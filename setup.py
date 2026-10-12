#! /usr/bin/python

'''pysam --- a Python package for reading, manipulating, and writing
genomic data sets.

pysam is a lightweight wrapper of the HTSlib API and provides facilities
to read and write SAM/BAM/CRAM/VCF/BCF/BED/GFF/GTF/FASTA/FASTQ files
as well as access to the command-line functionality of samtools and bcftools.
The module supports compression and random access through indexing.

This module provides a low-level wrapper around HTSlib's C API using Cython
and a high-level API for convenient access to the data within standard genomic
file formats.
'''

import collections
import glob
import logging
import os
import platform
import re
import subprocess
import sys
import sysconfig
from contextlib import contextmanager
from setuptools import setup, Command
from setuptools.command.sdist import sdist
from setuptools.extension import Extension

try:
    from setuptools.errors import CompileError, LinkError
except ImportError:
    from distutils.errors import CompileError, LinkError

try:
    from Cython.Distutils import build_ext
except ImportError:
    from setuptools.command.build_ext import build_ext

try:
    import cython  # noqa
    HAVE_CYTHON = True
except ImportError:
    HAVE_CYTHON = False

IS_DARWIN = platform.system() == 'Darwin'

log = logging.getLogger('pysam')


# Official MSYS2 detection snippet (mingw sysconfig platform) plus an
# MSYSTEM belt-and-braces check. POSIX platforms are never gated.
def _is_ucrt64_python():
    if os.name != 'nt':
        return True
    return (sysconfig.get_platform().startswith("mingw")
            and os.environ.get("MSYSTEM") == "UCRT64")


# BUILD-02 (03-03): the second Windows toolchain. Any nt python that is
# not MSYS2/mingw (win-amd64 CPython -- python.org or conda builds)
# builds through MSVC: setuptools auto-locates cl.exe from the Visual
# Studio Build Tools with the C++ workload (2022 or later; never a
# VS-version path). The module graph below dispatches on this flag;
# compiler flags inside cy_build_ext dispatch on compiler_type instead
# (two-level dispatch: platform picks sources, compiler_type picks
# flags).
IS_MSVC_PYTHON = (os.name == 'nt'
                  and not sysconfig.get_platform().startswith("mingw"))


if not _is_ucrt64_python() and not IS_MSVC_PYTHON:
    # Strict fail-fast outside UCRT64: this message mirrors, package for
    # package, the PKGS list in devtools/msys2-bootstrap.sh.
    sys.exit(
        "pysam: Windows builds require the MSYS2 UCRT64 environment and its "
        "pacman python. Open the UCRT64 shell and run "
        "'sh devtools/msys2-bootstrap.sh' to provision it, then build inside "
        "a UCRT64 venv (see INSTALL, section 'Windows (MSYS2 UCRT64)'). "
        "Required pacman packages:\n"
        "  mingw-w64-ucrt-x86_64-python\n"
        "  mingw-w64-ucrt-x86_64-python-pip\n"
        "  mingw-w64-ucrt-x86_64-python-setuptools\n"
        "  mingw-w64-ucrt-x86_64-cython\n"
        "  mingw-w64-ucrt-x86_64-toolchain\n"
        "  mingw-w64-ucrt-x86_64-llvm-tools\n"
        "  mingw-w64-ucrt-x86_64-zlib\n"
        "  mingw-w64-ucrt-x86_64-bzip2\n"
        "  mingw-w64-ucrt-x86_64-xz\n")


if IS_MSVC_PYTHON:
    # MSVC-mode banner (no import-time exit: introspection such as
    # 'setup.py --name' must work). The prerequisite wording mirrors
    # devtools/msvc-build.md verbatim (D-03/D-13 single-source pattern).
    print("# pysam: MSVC build mode (win CPython + cl.exe via setuptools)")
    print("# pysam: MSVC builds require Visual Studio Build Tools with the")
    print("# pysam: C++ workload (2022 or later) - see devtools/msvc-build.md")


@contextmanager
def changedir(path):
    save_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(save_dir)


def run_configure(option):
    sys.stdout.flush()
    try:
        # Always disable ref-cache as its code is omitted from pysam's htslib/
        configure_cmd = " ".join(("./configure", "--disable-ref-cache", option))
        if sys.platform == 'win32':
            # Run the POSIX configure script through the MSYS2 sh. Spawn it
            # via ["sh", "-c", ...] rather than shell=True: shell=True goes
            # through cmd.exe, whose machine-global AutoRun hooks (e.g.
            # conda's) can break every cmd /c invocation on a developer
            # machine.
            retcode = subprocess.call(["sh", "-c", configure_cmd])
        else:
            retcode = subprocess.call(configure_cmd, shell=True)
        if retcode != 0:
            return False
        else:
            return True
    except OSError:
        return False


def run_make(targets):
    sys.stdout.flush()
    subprocess.check_call([os.environ.get("MAKE", "make")] + targets)


def run_make_print_config():
    stdout = subprocess.check_output([os.environ.get("MAKE", "make"), "-s", "print-config"], encoding="ascii")

    make_print_config = {}
    for line in stdout.splitlines():
        if "=" in line:
            row = line.split("=")
            if len(row) == 2:
                make_print_config.update(
                    {row[0].strip(): row[1].strip()})
    return make_print_config


# D-14: MinGW's getopt family lives in the STATIC libmingwex.a, so every
# extension that references getopt_long or the opt* variables links its own
# private copy. The D-10 premise ("MinGW has no getopt_long, so share the
# vendored win32/getopt.c through libchtslib's import library") is falsified:
# plain data references (optarg/optind) cannot resolve through a PE import
# library during archive scanning, so GNU ld pulls the mingwex member anyway
# and the shared design collides ("multiple definition of 'getopt'").
# The decided model mirrors separate samtools.exe / bcftools.exe on Windows:
# each extension keeps its own getopt copy (never exported), and the
# BUILD-03 gate exempts exactly this closed symbol set on win32. Every
# other duplicate symbol still fails the build.
WIN32_GETOPT_EXEMPT_SYMBOLS = frozenset([
    "getopt", "getopt_long", "getopt_long_only",
    "optarg", "optind", "opterr", "optopt",
])


def _nm_command():
    # BUILD-03: the symbol gate is mandatory on Windows. GNU binutils nm is
    # unavailable there, but llvm-nm ships with the UCRT64 llvm-tools
    # package; -P makes it emit the same POSIX.2 format the parser below
    # expects.
    if sys.platform == 'win32':
        return ["llvm-nm", "-g", "-P"]
    return ["nm", "-g", "-P"]


def run_nm_defined_symbols(objfile):
    stdout = subprocess.check_output(_nm_command() + [objfile], encoding="ascii")

    def cython_internal(sym):
        offset = 1 if sym.startswith("___") else 0  # Skip extra underscore on macOS
        return sym.startswith("__pyx_", offset) or sym.startswith("__Pyx_", offset)

    symbols = set()
    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) < 2:
            # archive member headers and blank lines (llvm-nm on a
            # .dll.a import library prints "<member>.o:" separators)
            continue
        (sym, symtype) = fields[:2]
        if symtype not in "UFNWw" and not cython_internal(sym):
            if IS_DARWIN:
                # On macOS, all symbols have a leading underscore
                symbols.add(sym.removeprefix("_"))
            else:
                # Ignore symbols such as _edata (present in all shared objects)
                if sym[0] not in "_$.@": symbols.add(sym)

    return symbols


def adjust_cflags(command, incdir="/usr/local/include"):
    if not truthy(os.environ.get("PYSAM_FIX_CFLAGS", "1")):
        return command, set()

    # Change -I/usr/system/dir options to use -isystem, so that system-installed HTSlib headers
    # don't override pysam's own in a shared/separate build, in which pysam's -I options come later.
    ISYSTEM = "changed system includes to use -isystem"

    # We don't use $CPPFLAGS, so if -Iincdir is listed there, ensure it also present in our options.
    need_incdir = f"-I{incdir}" in (sysconfig.get_config_var("CPPFLAGS") or "")
    ADDED = f"added {incdir} to search path"

    adjustments = set()

    if isinstance(command, str):
        if "-I/usr/" in command:
            command = command.replace("-I/usr/", "-isystem /usr/")
            adjustments.add(ISYSTEM)

        if need_incdir and incdir not in command:
            command = f"{command} -isystem {incdir}"
            adjustments.add(ADDED)

    elif isinstance(command, list):
        original_command = command
        command = []
        for word in original_command:
            if word.startswith("-I/usr/"):
                command.extend(["-isystem", word[2:]])
                adjustments.add(ISYSTEM)
            else:
                command.append(word)

        if need_incdir and incdir not in command and f"-I{incdir}" not in command:
            command.extend(["-isystem", incdir])
            adjustments.add(ADDED)

    return command, adjustments


# This function emulates the way distutils combines settings from sysconfig,
# environment variables, and the extension being built. It returns a dictionary
# representing the usual set of variables, suitable for writing to a generated
# file or for running configure (provided the returned LIBS is ignored).
def build_config_dict(ext):
    def env(var):
        return [os.environ[var]] if var in os.environ else []

    def sc(var):
        value = sysconfig.get_config_var(var)
        return [value] if value is not None else []

    def optionise(option, valuelist):
        def quote(s): return "'"+s+"'" if " " in s else s
        return list(quote(option+v) for v in valuelist)

    def kvtuples(pairlist):
        def appendoptvalue(t): return t[0] if t[1] is None else t[0]+"="+t[1]
        return map(appendoptvalue, pairlist)

    # For CC, select the first of these that is set
    cc = (env('CC') + sc('CC') + ['gcc'])[0]

    # distutils ignores sysconfig for CPPFLAGS
    cppflags = " ".join(env('CPPFLAGS') + optionise('-I', ext.include_dirs) +
                        optionise('-D', kvtuples(ext.define_macros)) +
                        optionise('-U', ext.undef_macros))

    cflags = " ".join(sc('CFLAGS') + env('CFLAGS') + sc('CCSHARED') +
                      ext.extra_compile_args)

    # distutils actually includes $CPPFLAGS here too, but that's weird and
    # unnecessary for us as we know the output LDFLAGS will be used correctly
    ldflags = " ".join(sc('LDFLAGS') + env('LDFLAGS') + env('CFLAGS') +
                       optionise('-L', ext.library_dirs) +
                       ext.extra_link_args)

    # ext.libraries is computed (incorporating $LIBS etc) during configure
    libs = " ".join(optionise('-l', ext.libraries))

    return {'CC': cc, 'CPPFLAGS': cppflags, 'CFLAGS': cflags,
            'LDFLAGS': ldflags, 'LIBS': libs}


def write_configvars_header(filename, ext, prefix):
    config = build_config_dict(ext)
    if prefix != 'HTS':
        config['HTSDIR'] = '(unused)'
        config['CURSES_LIB'] = '(unused)'

    log.info("creating %s for '%s' extension", filename, ext.name)
    with open(filename, "w") as outf:
        for var, value in config.items():
            # Escape backslashes for the C string literal: Windows paths
            # (D:\Github\pysam\vendor\xz\...) otherwise produce invalid
            # escape sequences -- "\x" + non-hex digit is a hard C2153
            # error under cl (03-04). POSIX paths carry no backslashes,
            # so this write is byte-identical there.
            outf.write(f'#define {prefix}_{var} "{value.replace("\\", "\\\\")}"\n')


@contextmanager
def set_compiler_envvars():
    tmp_vars = []
    for var in ['CC', 'CFLAGS', 'LDFLAGS']:
        if var in os.environ:
            if var == 'CFLAGS' and 'CCSHARED' in sysconfig.get_config_vars():
                os.environ[var] += ' ' + sysconfig.get_config_var('CCSHARED')
            print(f"# pysam: (env) {var}={os.environ[var]}")
        elif var in sysconfig.get_config_vars():
            value = sysconfig.get_config_var(var)
            if var == 'CFLAGS' and 'CCSHARED' in sysconfig.get_config_vars():
                value += ' ' + sysconfig.get_config_var('CCSHARED')
            if var == 'CFLAGS':
                value, adjustments = adjust_cflags(value)
                for adj in sorted(adjustments): print(f"# pysam: adjusted CFLAGS: {adj}")
            print(f"# pysam: (sysconfig) {var}={value}")
            os.environ[var] = value
            tmp_vars += [var]

    try:
        yield
    finally:
        for var in tmp_vars:
            del os.environ[var]


def truthy(s):
    if s.lower() in ["1", "true", "y", "yes"]: return True
    elif s.lower() in ["0", "false", "n", "no"]: return False
    else: return None


def format_macro_option(name, value):
    return f"-D{name}={value}" if value is not None else f"-D{name}"


def configure_library(library_dir, env_options=None, options=[]):

    configure_script = os.path.join(library_dir, "configure")

    on_rtd = os.environ.get("READTHEDOCS") == "True"
    # RTD has no bzip2 development libraries installed:
    if on_rtd:
        env_options = "--disable-bz2"

    if not os.path.exists(configure_script):
        raise ValueError(f"configure script {configure_script!r} does not exist")

    with changedir(library_dir), set_compiler_envvars():
        if env_options is not None:
            if run_configure(env_options):
                return env_options

        for option in options:
            if run_configure(option):
                return option

    return None


def global_cython_directives():
    directives = {}
    if truthy(os.environ.get("PYSAM_PROFILE", "0")): directives["profile"] = True
    return directives


def get_pysam_version():
    sys.path.insert(0, "pysam")
    import version
    return version.__version__


# Override sdist command to ensure Cythonized *.c files are included.
class cythonize_sdist(sdist):
    # Remove when setuptools (as installed on GH runners) has these options
    if not any(opt[0] == 'owner=' for opt in sdist.user_options):
        sdist.user_options.append(('owner=', 'u', 'Specify owner inside tar'))
    if not any(opt[0] == 'group=' for opt in sdist.user_options):
        sdist.user_options.append(('group=', 'g', 'Specify group inside tar'))

    def run(self):
        from Cython.Build import cythonize
        cythonize(self.distribution.ext_modules, force=True, compiler_directives=global_cython_directives())
        super().run()


# Override Cythonised build_ext command to customise macOS shared libraries.

class CyExtension(Extension):
    def __init__(self, *args, **kwargs):
        self._init_func = kwargs.pop("init_func", None)
        self._prebuild_func = kwargs.pop("prebuild_func", None)
        super().__init__(*args, **kwargs)

    def extend_includes(self, includes):
        self.include_dirs.extend(includes)

    def extend_macros(self, macros):
        self.define_macros.extend(macros)

    def extend_extra_objects(self, objs):
        self.extra_objects.extend(objs)


class cy_build_ext(build_ext):
    def initialize_options(self):
        super().initialize_options()
        self.cython_directives = global_cython_directives()

    def check_ext_symbol_conflicts(self):
        """Checks for symbols defined in multiple extension modules,
        which can lead to crashes due to incorrect functions being invoked.
        Avoid by adding an appropriate #define to import/pysam.h or in
        unusual cases adding another rewrite rule to devtools/import.py.

        D-14: on win32, exactly WIN32_GETOPT_EXEMPT_SYMBOLS may be
        duplicated (private per-module getopt copies — MinGW links the
        static libmingwex.a member into every extension that references
        it). The exemption is closed: any other duplicate still fails.
        """
        symbols = dict()
        for ext in self.distribution.ext_modules:
            objfile = self.get_ext_fullpath(ext.name)
            if sys.platform == 'win32':
                # The built .pyd files are stripped (distutils links with
                # -s), so their COFF symbol table is gone. Gate the module's
                # EXPORT surface instead by reading the import library
                # emitted beside it: cross-module binding can only happen
                # through exports, making this the exact PE analogue of the
                # POSIX gate reading .so dynamic symbols.
                # BUILD-02 (03-03): the MSVC arm emits .lib (llvm-nm parses
                # MSVC archives -- verified); MinGW keeps .dll.a.
                implib_ext = (
                    ".lib"
                    if getattr(self.compiler, "compiler_type", None) == "msvc"
                    else ".dll.a")
                objfile = os.path.splitext(objfile)[0] + implib_ext
            for sym in run_nm_defined_symbols(objfile):
                symbols.setdefault(sym, []).append(ext.name.lstrip('pysam.'))

        if sys.platform == 'win32' and not symbols:
            # Never pass vacuously: if the built artifacts yield no
            # parseable symbols, the gate saw nothing and must fail loudly.
            raise LinkError(
                "symbol gate read no symbols from the built binaries "
                "(llvm-nm produced no parseable output for the import "
                "libraries)")

        errors = 0
        for (sym, objs) in symbols.items():
            if (len(objs) > 1):
                if (sys.platform == 'win32'
                        and sym in WIN32_GETOPT_EXEMPT_SYMBOLS):
                    log.warning(
                        "duplicate symbol exempted on win32 (D-14): %s in %s",
                        sym, " ".join(objs))
                    continue
                log.error("conflicting symbol (%s): %s", " ".join(objs), sym)
                errors += 1

        if errors > 0: raise LinkError("symbols defined in multiple extensions")

    def c99_compile_args(self):
        """Determines whether any compiler flags are needed to ensure C99 compilation."""
        if getattr(self.compiler, "compiler_type", None) == "msvc":
            # BUILD-02 (03-03): skip the conftest_cstd.c probe under cl --
            # the probe source includes <unistd.h> and references optind,
            # which is unportable under MSVC, so every candidate flag
            # would fail and abort with "cannot compile C99". cl accepts
            # /std:c11 since VS2019 16.8; /utf-8 pins the source charset
            # (avoids C4819 on cp936 consoles). This mirrors how the
            # -Wno-* block below is gated away from Windows compilers.
            # (03-04: these flags are carried into the build by the
            # extra_compile_args.extend in the MSVC module-graph block --
            # MSVCCompiler has no compiler/compiler_so attributes, so the
            # set_executables plumbing here cannot deliver them; this arm
            # exists to SKIP the unportable probe.)
            log.info("msvc: skipping C99 probe; /std:c11 /utf-8 applied "
                     "via extra_compile_args (MSVC module-graph block)")
            return ["/std:c11", "/utf-8"]
        compiler = getattr(self.compiler, "compiler", "C compiler")
        if isinstance(compiler, list): compiler = compiler[0]
        log.info("checking for %s option to enable C99 features...", compiler)
        for flags in [None, ["-std=c99"], ["-std=gnu99"]]:
            try:
                self.compiler.compile(["pysam/conftest_cstd.c"], output_dir=self.build_temp, extra_preargs=flags)
                log.info("%s option to enable C99 features: %s", compiler, " ".join(flags) if flags else "none needed")
                return flags
            except CompileError:
                log.info("(ignoring errors from test probes)")

        log.error("%s cannot compile C99 source code", compiler)
        return None

    def run(self):
        if sys.platform == 'darwin':
            ldshared = os.environ.get('LDSHARED', sysconfig.get_config_var('LDSHARED'))
            os.environ['LDSHARED'] = ldshared.replace('-bundle', '')

        super().run()
        if sys.platform == 'win32':
            # BUILD-03: the symbol check is mandatory on Windows and is never
            # silently skipped — it runs outside the exception-swallowing
            # wrapper below, so a missing or failing llvm-nm aborts the build.
            if HTSLIB_MODE == 'separate':
                log.warning(
                    "symbol collision check not applicable: htslib is built "
                    "separately into each extension (HTSLIB_MODE=separate)")
            else:
                self.check_ext_symbol_conflicts()
        else:
            try:
                if HTSLIB_MODE != 'separate':
                    self.check_ext_symbol_conflicts()
            except OSError as e:
                log.warning("skipping symbol collision check (invoking nm failed: %s)", e)
            except subprocess.CalledProcessError:
                log.warning("skipping symbol collision check (invoking nm failed)")

    def build_extensions(self):
        c99_flags = self.c99_compile_args()
        if c99_flags:
            executables = {}
            for executable in ["compiler", "compiler_so"]:
                command = getattr(self.compiler, executable, None)
                if command:
                    if isinstance(command, list):  executables[executable] = command + c99_flags
                    elif isinstance(command, str): executables[executable] = f"{command} {' '.join(c99_flags)}"
            self.compiler.set_executables(**executables)

        executables = {}
        adjustments = set()
        for executable in ["compiler", "compiler_so"]:
            command = getattr(self.compiler, executable, None)
            new_command, adjs = adjust_cflags(command)
            if new_command != command:
                executables[executable] = new_command
                adjustments |= adjs
        if executables: self.compiler.set_executables(**executables)
        for adj in sorted(adjustments): print(f"checking compiler options... {adj}")

        super().build_extensions()

    def build_extension(self, ext):

        if isinstance(ext, CyExtension) and ext._init_func:
            ext._init_func(ext)

        if not self.inplace:
            ext.library_dirs.append(os.path.join(self.build_lib, "pysam"))

        if sys.platform == 'darwin':
            # The idea is to give shared libraries an install name of the form
            # `@rpath/<library-name.so>`, and to set the rpath equal to
            # @loader_path. This will allow Python packages to find the library
            # in the expected place, while still giving enough flexibility to
            # external applications to link against the library.
            relative_module_path = ext.name.replace(".", os.sep) + sysconfig.get_config_var('EXT_SUFFIX')
            library_path = os.path.join(
                "@rpath", os.path.basename(relative_module_path)
            )

            if not ext.extra_link_args:
                ext.extra_link_args = []
            ext.extra_link_args += ['-dynamiclib',
                                    '-rpath', '@loader_path',
                                    '-Wl,-headerpad_max_install_names',
                                    f'-Wl,-install_name,{library_path}',
                                    '-Wl,-x']
        elif sys.platform == 'win32':
            # PE binaries have no ELF rpath; only ensure the flag list exists.
            if not ext.extra_link_args:
                ext.extra_link_args = []
            mod = ext.name.rsplit('.', 1)[-1]
            if getattr(self.compiler, "compiler_type", None) == "msvc":
                # BUILD-02 (03-03) msvc arm: link.exe flags ONLY -- no GNU
                # -Wl flag may reach this arm (link.exe warns LNK4044 and
                # silently ignores them, hiding real misconfiguration).
                # The export surface comes from HTS_BUILDING_LIBRARY
                # dllexport (libchtslib-only compile define) plus the
                # supplementary /DEF: below (union export); link.exe has
                # no --export-all-symbols equivalent and needs neither.
                # D-17 (msvc arm): emit the import library beside the
                # built module via a LATE /IMPLIB: -- it overrides
                # distutils' builtin /IMPLIB (verified: last flag wins).
                # The symbol-gate probe reads exactly this path (.lib),
                # and consumer extensions resolve through
                # internal_htslib_libraries because the emitted stem
                # matches the existing module naming.
                implib = os.path.join(
                    os.path.dirname(self.get_ext_fullpath(ext.name)),
                    os.path.splitext(mod + suffix)[0] + ".lib")
                ext.extra_link_args.append("/IMPLIB:" + implib)
                # Supplementary exports. GNU ld's --export-all-symbols
                # (the mingw32 arm) exports every global symbol, so
                # cross-module consumers bind implicitly; link.exe
                # exports only dllexport annotations plus /DEF: entries.
                # libchtslib: htslib's HTSLIB_EXPORT machinery carries
                # the API (activated by the HTS_BUILDING_LIBRARY compile
                # define); the .def adds the un-annotated gaps and the
                # two htslib_util.c symbols the Cython extensions
                # reference (03-04). libcsamtools/libcbcftools: the
                # dispatch family consumed by libcutils (03-04). On all
                # three, consumer LNK2001 self-detects drift.
                _msvc_export_defs = {
                    "pysam.libchtslib": "chtslib_exports.def",
                    "pysam.libcsamtools": "samtools_exports.def",
                    "pysam.libcbcftools": "bcftools_exports.def",
                }
                if ext.name in _msvc_export_defs:
                    ext.extra_link_args.append(
                        "/DEF:" + os.path.abspath(
                            os.path.join("win32", _msvc_export_defs[ext.name])))
            else:
                # Emit an import library beside each built module so the other
                # extensions' -l flags resolve through library_dirs (GNU ld
                # searches for lib<name>.dll.a there). Module names already
                # carry the 'lib' prefix (libchtslib, libcsamtools, ...), so the
                # stub name is the module + EXT_SUFFIX stem + .dll.a — exactly
                # what '-l<name minus lib prefix>' expands to.
                # D-17: derive the implib path from the module's own output
                # directory so emission and the symbol-gate probe (which reads
                # get_ext_fullpath + ".dll.a") always target the same file,
                # inplace or not. The dirname is always on the -l search path:
                # common_options puts abspath("pysam") in every extension's
                # library_dirs, and build_extension appends build_lib/pysam
                # when not inplace.
                implib = os.path.join(
                    os.path.dirname(self.get_ext_fullpath(ext.name)),
                    os.path.splitext(mod + suffix)[0] + ".dll.a")
                # distutils hands the linker a .def file naming only PyInit_*,
                # which suppresses PE auto-export; later extensions resolve
                # dispatch/htslib symbols through this module's import library,
                # so export everything (the ELF default the POSIX build relies
                # on).
                ext.extra_link_args.append("-Wl,--export-all-symbols")
                # D-14: never export the getopt family. Each extension's copy
                # (vendored win32/getopt.c in libchtslib, or the static mingwex
                # member pulled into the tool extensions) stays private, so
                # siblings never bind across module boundaries. binutils' PE
                # linker delimits --exclude-symbols entries with ':'.
                ext.extra_link_args.append(
                    "-Wl,--exclude-symbols="
                    + ":".join(sorted(WIN32_GETOPT_EXEMPT_SYMBOLS)))
                ext.extra_link_args.append("-Wl,--out-implib," + implib)
        else:
            if not ext.extra_link_args:
                ext.extra_link_args = []

            ext.extra_link_args += ['-Wl,-rpath,$ORIGIN']

        if isinstance(ext, CyExtension) and ext._prebuild_func:
            ext._prebuild_func(ext, self.force)

        super().build_extension(ext)


class clean_ext(Command):
    description = "clean up Cython temporary files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        objs = glob.glob(os.path.join("pysam", "libc*.c"))
        if objs:
            log.info("removing 'pysam/libc*.c' (%s Cython objects)", len(objs))
        for obj in objs:
            os.remove(obj)

        headers = (glob.glob(os.path.join("htslib",   "*config*.h")) +
                   glob.glob(os.path.join("samtools", "*config*.h")) +
                   glob.glob(os.path.join("bcftools", "*config*.h")))
        if headers:
            log.info("removing '*/*config*.h' (%s generated headers)", len(headers))
        for header in headers:
            os.remove(header)

        objects = (glob.glob(os.path.join("htslib", "*.[oa]")) +
                   glob.glob(os.path.join("htslib", "cram", "*.o")) +
                   glob.glob(os.path.join("htslib", "htscodecs", "htscodecs", "*.o")))
        if objects:
            log.info("removing 'htslib/**/*.o' and libhts.a (%s objects)", len(objects))
        for obj in objects:
            os.remove(obj)


# How to link against HTSLIB
# shared:   build shared chtslib from builtin htslib code.
# external: use shared libhts.so compiled outside of
#           pysam
# separate: use included htslib and include in each extension
#           module. No dependencies between modules and works with
#           setup.py install, but wasteful in terms of memory and
#           compilation time. Fallback if shared module compilation
#           fails.

HTSLIB_MODE = os.environ.get("HTSLIB_MODE", "shared")
HTSLIB_LIBRARY_DIR = os.environ.get("HTSLIB_LIBRARY_DIR", None)
HTSLIB_INCLUDE_DIR = os.environ.get("HTSLIB_INCLUDE_DIR", None)
HTSLIB_CONFIGURE_OPTIONS = os.environ.get("HTSLIB_CONFIGURE_OPTIONS", None)
HTSLIB_SOURCE = None

# BUILD-02 (03-03): MSVC short-circuit constants. MSVC_LIBHTS_OBJS
# mirrors the LIBHTS_OBJS expansion of htslib/Makefile -- THE source of
# truth (count-checked at write time: 27 htslib core + 11 cram +
# 14 htscodecs = 52 TUs, the --disable-libcurl configuration parity).
# The .o names are what 'make print-config' would report; the MSVC
# module graph turns each into its .c source (03-03 Task 3). The
# compression and regex dependencies are vendored under vendor/ and
# enter as compiled sources there, so the only system -l residue is
# ws2_32 (sockets; UCRT64 links it too).
MSVC_LIBHTS_OBJS = [
    # htslib core (htslib/Makefile LIBHTS_OBJS, top-level entries)
    "kfunc.o", "kstring.o", "bcf_sr_sort.o", "bgzf.o", "errmod.o",
    "faidx.o", "header.o", "hfile.o", "hts.o", "hts_expr.o", "hts_os.o",
    "md5.o", "multipart.o", "probaln.o", "realn.o", "regidx.o",
    "region.o", "sam.o", "sam_mods.o", "simd.o", "synced_bcf_reader.o",
    "vcf_sweep.o", "tbx.o", "textutils.o", "thread_pool.o", "vcf.o",
    "vcfutils.o",
    # cram (htslib/Makefile LIBHTS_OBJS, cram/ entries)
    "cram/cram_codecs.o", "cram/cram_decode.o", "cram/cram_encode.o",
    "cram/cram_external.o", "cram/cram_index.o", "cram/cram_io.o",
    "cram/cram_stats.o", "cram/mFILE.o", "cram/open_trace_file.o",
    "cram/pooled_alloc.o", "cram/string_alloc.o",
    # htscodecs (htslib/Makefile $(HTSCODECS_OBJS) expansion)
    "htscodecs/htscodecs/arith_dynamic.o",
    "htscodecs/htscodecs/fqzcomp_qual.o",
    "htscodecs/htscodecs/htscodecs.o",
    "htscodecs/htscodecs/pack.o",
    "htscodecs/htscodecs/rANS_static4x16pr.o",
    "htscodecs/htscodecs/rANS_static32x16pr_avx2.o",
    "htscodecs/htscodecs/rANS_static32x16pr_avx512.o",
    "htscodecs/htscodecs/rANS_static32x16pr_sse4.o",
    "htscodecs/htscodecs/rANS_static32x16pr_neon.o",
    "htscodecs/htscodecs/rANS_static32x16pr.o",
    "htscodecs/htscodecs/rANS_static.o",
    "htscodecs/htscodecs/rle.o",
    "htscodecs/htscodecs/tokenise_name3.o",
    "htscodecs/htscodecs/utils.o",
]
MSVC_LIBHTS_LIBS = "ws2_32"

package_list = ['pysam',
                'pysam.include',
                'pysam.include.samtools',
                'pysam.include.bcftools']
package_dirs = {'pysam': 'pysam',
                'pysam.include.samtools': 'samtools',
                'pysam.include.bcftools': 'bcftools'}

# list of config files that will be automatically generated should
# they not already exist or be created by configure scripts in the
# subpackages.
config_headers = ["samtools/config.h",
                  "bcftools/config.h"]

# If cython is available, the pysam will be built using cython from
# the .pyx files. If no cython is available, the C-files included in the
# distribution will be used.
if HAVE_CYTHON:
    print(f"# pysam: Cython {cython.__version__} is available - using cythonize if necessary")
    source_pattern = "pysam/libc%s.pyx"
else:
    print("# pysam: no Cython available - using pre-compiled C")
    source_pattern = "pysam/libc%s.c"

# Exit if there are no pre-compiled files and no cython available
fn = source_pattern % "htslib"
if not os.path.exists(fn):
    raise ValueError(
        f"no Cython installed, but cannot find {fn}. "
        "Make sure that Cython is installed when building from the repository")

print(f"# pysam: htslib mode is {HTSLIB_MODE}")
print(f"# pysam: HTSLIB_CONFIGURE_OPTIONS={HTSLIB_CONFIGURE_OPTIONS}")
htslib_configure_options = None

define_macros = []
dynamic_files = []
extra_compile_args = []

if HTSLIB_MODE in ['shared', 'separate']:
    package_list += ['pysam.include.htslib',
                     'pysam.include.htslib.htslib']
    package_dirs.update({'pysam.include.htslib': 'htslib'})

    if IS_MSVC_PYTHON:
        # BUILD-02 (03-03): the MSVC arm never invokes autotools -- no
        # configure, no make print-config (cl.exe cannot run either).
        # htslib/config.h is deterministically rewritten from the
        # checked-in win32/config.h.msvc on EVERY run, so alternating
        # with UCRT64 builds is always safe (that path rewrites the same
        # file through real configure). The make options come from the
        # hard-coded MSVC mirror above instead of 'make print-config'.
        htslib_configure_options = "pre-baked win32/config.h.msvc"
        with open("win32/config.h.msvc") as inf, \
             open("htslib/config.h", "w") as outf:
            outf.write(inf.read())
        print("# pysam: htslib/config.h rewritten from win32/config.h.msvc")
        htslib_make_options = {
            "LIBHTS_OBJS": " ".join(MSVC_LIBHTS_OBJS),
            "LIBS": MSVC_LIBHTS_LIBS,
        }
    else:
        htslib_configure_options = configure_library(
            "htslib",
            HTSLIB_CONFIGURE_OPTIONS,
            ["--enable-libcurl",
             "--disable-libcurl"])

        with changedir("htslib"):
            htslib_make_options = run_make_print_config()

    HTSLIB_SOURCE = "builtin"
    print(f"# pysam: htslib configure options: {htslib_configure_options}")

    config_headers += ["htslib/config.h"]
    if htslib_configure_options is None:
        # create empty config.h file
        with open("htslib/config.h", "w") as outf:
            outf.write(
                "/* empty config.h created by pysam */\n")
            outf.write(
                "/* conservative compilation options */\n")

    for key, value in htslib_make_options.items():
        print(f"# pysam: htslib_config {key}={value}")

    external_htslib_libraries = ['z']
    if IS_MSVC_PYTHON:
        # BUILD-02 (03-03): the MSVC closure. The vendored zlib/bzip2/
        # liblzma/regex trees are compiled in as libchtslib sources (plan
        # 03-02), so the autotools '-l' harvest has no counterpart here;
        # the only system residue is ws2_32 (sockets; the UCRT64 build
        # links it too).
        external_htslib_libraries = ["ws2_32"]
    elif "LIBS" in htslib_make_options:
        external_htslib_libraries.extend(
            [re.sub("^-l", "", x) for x in htslib_make_options["LIBS"].split(" ") if x.strip()])

    for_redistribution = truthy(os.environ.get("CIBUILDWHEEL", "0"))

    if for_redistribution:
        extra_compile_args.append("-g0")  # Omit all debugging symbols

    if sys.platform == "linux" and "curl" in external_htslib_libraries and for_redistribution:
        dynamic_files.append("pysam/dynamic_libs.c")
        define_macros.append(("DYNAMIC_NETWORK_LIBS", None))
        # Filter out libraries that we will load dynamically at runtime
        external_htslib_libraries = [lib for lib in external_htslib_libraries if lib not in ("curl", "crypto")]

if HTSLIB_LIBRARY_DIR:
    # linking against a shared, externally installed htslib version,
    # no sources or built libhts.a required for htslib
    htslib_objects = []
    separate_htslib_objects = []
    chtslib_sources = []
    htslib_library_dirs = [HTSLIB_LIBRARY_DIR]
    htslib_include_dirs = [HTSLIB_INCLUDE_DIR]
    external_htslib_libraries = ['z', 'hts']
elif HTSLIB_MODE == 'separate':
    # add to each pysam component a separately compiled
    # htslib
    htslib_objects = ['htslib/libhts.a']
    separate_htslib_objects = ['htslib/libhts.a']
    htslib_library_dirs = []
    htslib_include_dirs = ['htslib']
elif HTSLIB_MODE == 'shared':
    # link each pysam component against the same
    # htslib built from sources included in the pysam
    # package.

    # Link with the object files rather than the final htslib/libhts.a, to ensure that
    # all object files are pulled into the link, even those not used by htslib itself.
    htslib_objects = [os.path.join("htslib", x)
                      for x in htslib_make_options["LIBHTS_OBJS"].split(" ")]
    separate_htslib_objects = []

    htslib_library_dirs = ["."]  # when using setup.py develop?
    htslib_include_dirs = ['htslib']
else:
    raise ValueError(f"unknown HTSLIB value {HTSLIB_MODE!r}")

if IS_MSVC_PYTHON and HTSLIB_MODE == 'shared':
    # BUILD-02 (03-03): no make-built libhts.a exists on the MSVC path --
    # every htslib TU is compiled by setuptools from libchtslib.sources
    # (the MSVC_LIBHTS_OBJS mirror turned into .c paths below).
    htslib_objects = []

# build config.py
with open(os.path.join("pysam", "config.py"), "w") as outf:
    outf.write(f'HTSLIB = "{HTSLIB_SOURCE}"\n')
    config_values = collections.defaultdict(int)

    if HTSLIB_SOURCE == "builtin":
        with open(os.path.join("htslib", "config.h")) as inf:
            for line in inf:
                if line.startswith("#define"):
                    key, value = re.match(
                        r"#define (\S+)\s+(\S+)", line).groups()
                    config_values[key] = value
            for key in ["ENABLE_GCS",
                        "ENABLE_PLUGINS",
                        "ENABLE_S3",
                        "HAVE_COMMONCRYPTO",
                        "HAVE_HMAC",
                        "HAVE_LIBBZ2",
                        "HAVE_LIBCURL",
                        "HAVE_LIBDEFLATE",
                        "HAVE_LIBLZMA",
                        "HAVE_MMAP"]:
                outf.write(f"{key} = {config_values[key]}\n")
                print(f"# pysam: config_option: {key}={config_values[key]}")

# create empty config.h files if they have not been created automatically
# or created by the user:
for fn in config_headers:
    if not os.path.exists(fn):
        with open(fn, "w") as outf:
            outf.write(
                "/* empty config.h created by pysam */\n")
            outf.write(
                "/* conservative compilation options */\n")

#######################################################
# Windows (MSYS2 UCRT64) compatibility
if platform.system() == 'Windows':
    include_os = ['win32']
    # The vendored getopt implementation is compiled into pysam.libchtslib
    # only. The old plan of sharing it with the other modules through the
    # import library was falsified by the first real UCRT64 build (PE data
    # references cannot resolve through an import library during archive
    # scanning, so every module pulled mingwex's own getopt anyway); per
    # D-14 the family is now excluded from every module's exports and the
    # tool extensions keep private mingwex copies. win32/getopt.c stays
    # for the upcoming MSVC path (no getopt there at all).
    # UCRT64 GCC ships real unistd.h/stdint.h — the stale
    # win32 shim headers were removed in favour of them (they lacked
    # isatty/fileno and risked header shadowing).
    os_c_files = ['win32/getopt.c']
    # bcftools/vcfsom.c calls random()/srandom() (lines 362 and 513) and the
    # dropped shim header used to provide this mapping; MSVCRT provides
    # rand()/srand(). Harmless if UCRT64 headers already declare the POSIX
    # names; verified at the first UCRT64 build.
    define_macros.extend([('random', 'rand'), ('srandom', 'srand')])
else:
    include_os = []
    os_c_files = []
    # for python 3.4, see for example
    # http://stackoverflow.com/questions/25587039/
    # error-compiling-rpy2-on-python3-4-due-to-werror-
    # declaration-after-statement
    extra_compile_args.extend([
        "-Wno-unused",
        "-Wno-strict-prototypes",
        "-Wno-sign-compare",
        "-Wno-error=declaration-after-statement",
    ])

#######################################################
# Windows (MSVC) module graph (BUILD-02, plan 03-03)
#
# The two-level dispatch, arm 1 (module graph): keyed on the sysconfig
# platform at module level. Arm 2 (compiler flags) lives inside
# cy_build_ext, keyed on self.compiler.compiler_type. Everything in
# this block is invisible to the mingw/POSIX graphs -- UCRT64
# byte-identity is the zero-regression red line.
msvc_include_extra = []
msvc_chtslib_sources = []
msvc_tool_private_sources = []
if IS_MSVC_PYTHON:
    # Include dirs: the shim dir plus the vendored trees' header paths,
    # copied verbatim from vendor/README.md (the single include source --
    # no MSYS2 header dir must ever appear on an MSVC compile line,
    # T-03-05).
    msvc_include_extra = [
        "win32/msvc",
        "vendor/zlib", "vendor/bzip2", "vendor/regex",
        "vendor/xz/src/liblzma/api", "vendor/xz/src/liblzma/common",
        "vendor/xz/src/liblzma/check", "vendor/xz/src/liblzma/lz",
        "vendor/xz/src/liblzma/lzma", "vendor/xz/src/liblzma/delta",
        "vendor/xz/src/liblzma/simple", "vendor/xz/src/liblzma/rangecoder",
        "vendor/xz/src/common",
    ]

    # Vendored dependency sources, compiled into libchtslib by the same
    # cl pass (sets per vendor/README.md: zlib 15 core TUs, bzip2 7
    # library TUs, xz liblzma tree + the two src/common support TUs,
    # musl regex 4 TUs -- regfree is defined inside regcomp.c).
    # xz exclusions (the autotools/cmake builds never put these in the
    # library): the *_small.c size-optimized CRC variants are the
    # HAVE_SMALL configuration -- our no-config route leaves HAVE_SMALL
    # unset, so crc32_fast.c/crc64_fast.c carry the tables via their
    # *_table_le.h headers, and the small files' runtime-initialized
    # lzma_crc32_table[1][256] definition collides with the const
    # [8][256] one (C2369/C2166, first full link, 03-04); the
    # *tablegen*.c / *_consts_gen.c files are standalone table-regen
    # tools (own main()), not library sources. stream_decoder_mt.c is
    # the multithreaded decoder: the no-config route leaves threading
    # off (mythread.h defines nothing without MYTHREAD_ENABLED; htslib
    # uses the single-threaded lzma_stream_decoder in the _st TU).
    _xz_tool_tus = ("crc32_small.c", "crc64_small.c",
                    "crc32_tablegen.c", "crc64_tablegen.c",
                    "crc_clmul_consts_gen.c", "fastpos_tablegen.c",
                    "price_tablegen.c", "stream_decoder_mt.c",
                    "stream_encoder_mt.c")
    msvc_vendor_sources = (
        sorted(glob.glob(os.path.join("vendor", "zlib", "*.c"))) +
        sorted(glob.glob(os.path.join("vendor", "bzip2", "*.c"))) +
        [s for s in sorted(glob.glob(os.path.join(
            "vendor", "xz", "src", "liblzma", "**", "*.c"),
            recursive=True))
         if os.path.basename(s) not in _xz_tool_tus] +
        [os.path.join("vendor", "xz", "src", "common", "tuklib_physmem.c"),
         os.path.join("vendor", "xz", "src", "common", "tuklib_cpucores.c")] +
        sorted(glob.glob(os.path.join("vendor", "regex", "*.c")))
    )

    # libchtslib's MSVC sources: the MSVC_LIBHTS_OBJS mirror as .c paths
    # plus the vendored closure plus the Win32 pthread implementation
    # (the shim layer's only compiled artifact).
    msvc_chtslib_sources = (
        [os.path.join("htslib", o[:-2] + ".c") for o in MSVC_LIBHTS_OBJS] +
        msvc_vendor_sources +
        [os.path.join("win32", "msvc", "pthread_win32.c")])

    # D-16 isolation analogue: each tool extension (the samtools and
    # bcftools mains live in libcsamtools/libcbcftools, and libcutils
    # wraps both dispatch families) compiles its own private getopt --
    # MinGW pulls the static libmingwex member per extension; MSVC has
    # no system getopt at all, so the vendored win32/getopt.c is the
    # copy. Never shared across modules, never exported.
    msvc_tool_private_sources = [os.path.join("win32", "getopt.c")]

    # Vendored-tree configuration macros (vendor/README.md recorded
    # sets): xz's full-feature static configuration and the musl regex
    # limits macros. Applied globally on the MSVC arm -- every other
    # consumer ignores them. The xz set is what autotools config.h
    # carries for a full build (the no-config route of 03-02's probe
    # covered only standalone TUs: without the HAVE_DECODER/ENCODER
    # feature keys filter_decoder.c's decoders[] array is EMPTY, and
    # cl ICEs on its zero-size ARRAY_SIZE -- C4034 then C1001, 03-04).
    # Deliberately NOT defined: HAVE_SMALL (excluded TUs),
    # HAVE_SYMBOL_VERSIONS_LINUX / HAVE_CRC_X86_ASM (ELF/GNU-as only),
    # HAVE_FUNC_ATTRIBUTE_CONSTRUCTOR / HAVE_VISIBILITY /
    # HAVE___BUILTIN_ASSUME_ALIGNED (GCC-isms), HAVE_USABLE_CLMUL (the
    # generic CRC fallback is the proven path under cl), HAVE_SMALL's
    # thread machinery (MYTHREAD_* stays off). musl's `hidden` macro is
    # NOT defined here either: a global -Dhidden= collides with htslib's
    # local variables named `hidden` (textutils.c:246); the qualifier is
    # instead dropped from vendor/regex/tre.h (compat edit 2, 03-04).
    _xz_feature_defines = [
        ("HAVE_DECODER_%s" % f, "1")
        for f in ("ARM", "ARM64", "ARMTHUMB", "DELTA", "IA64", "LZMA1",
                  "LZMA2", "POWERPC", "RISCV", "SPARC", "X86")
    ] + [
        ("HAVE_ENCODER_%s" % f, "1")
        for f in ("ARM", "ARM64", "ARMTHUMB", "DELTA", "IA64", "LZMA1",
                  "LZMA2", "POWERPC", "RISCV", "SPARC", "X86")
    ] + [
        ("HAVE_CHECK_CRC32", "1"), ("HAVE_CHECK_CRC64", "1"),
        ("HAVE_CHECK_SHA256", "1"), ("HAVE_LZIP_DECODER", "1"),
        ("HAVE_MF_HC3", "1"), ("HAVE_MF_HC4", "1"),
        ("HAVE_MF_BT2", "1"), ("HAVE_MF_BT3", "1"), ("HAVE_MF_BT4", "1"),
    ]
    define_macros.extend([
        ("HAVE_STDINT_H", "1"), ("HAVE_INTTYPES_H", "1"),
        ("HAVE_STDBOOL_H", "1"),
        ("RE_DUP_MAX", "255"), ("CHARCLASS_NAME_MAX", "14"),
    ] + _xz_feature_defines)

    # /FI force-includes the central compat header into every TU (the
    # mapping list must be global -- most call sites never include the
    # POSIX header that would canonically declare those names).
    extra_compile_args.append(
        "/FI" + os.path.abspath(os.path.join("win32", "msvc",
                                             "msvc_compat.h")))

    # cl dialect + source charset. These ride extra_compile_args because
    # cy_build_ext.c99_compile_args() applies its return value through
    # Compiler.set_executables('compiler'/'compiler_so') -- attributes
    # UnixCCompiler defines but MSVCCompiler does not, so that plumbing
    # is a verified no-op under cl (03-04, first full build). The
    # probe-skip arm of c99_compile_args stays: it still prevents the
    # unportable conftest_cstd.c probe from aborting the build.
    # /std:c11 matches every research/vendor probe command line; /utf-8
    # pins the source charset (cp936 consoles otherwise emit C4819).
    # /GL- disables distutils' whole-program optimization (/GL + link
    # /LTCG): the 14.50 backend hits a C1001 internal error during the
    # LTCG pass on filter_decoder.obj (LNK1000 BuildImage ICE follows);
    # upstream xz's own MSVC builds (CMake Release) never use /GL, so
    # this also matches the proven upstream configuration. /O2 stays.
    extra_compile_args.extend(["/std:c11", "/utf-8", "/GL-"])

suffix = sysconfig.get_config_var('EXT_SUFFIX')

internal_htslib_libraries = [
    os.path.splitext(f"chtslib{suffix}")[0],
    ]
internal_samtools_libraries = [
    os.path.splitext(f"csamtools{suffix}")[0],
    os.path.splitext(f"cbcftools{suffix}")[0],
    ]
internal_pysamutil_libraries = [
    os.path.splitext(f"cutils{suffix}")[0],
    ]

libraries_for_pysam_module = external_htslib_libraries + internal_htslib_libraries + internal_pysamutil_libraries

# Order of modules matters in order to make sure that dependencies are resolved.
# The structures of dependencies is as follows:
# libchtslib: htslib utility functions and htslib itself if builtin is set.
# libcsamtools: samtools code (builtin)
# libcbcftools: bcftools code (builtin)
# libcutils: General utility functions, depends on all of the above
# libcXXX (pysam module): depends on libchtslib and libcutils

# The list below uses the union of include_dirs and library_dirs for
# reasons of simplicity.


def prebuild_libchtslib(ext, force):
    if HTSLIB_MODE not in ['shared', 'separate']: return

    write_configvars_header("htslib/config_vars.h", ext, "HTS")

    if IS_MSVC_PYTHON:
        # BUILD-02 (03-03): no autotools anywhere on the MSVC path -- no
        # make-built libhts.a. config_vars.h is still written (hts.c:58
        # includes it); every htslib TU is compiled by setuptools from
        # libchtslib.sources with cl.
        return

    if force or not os.path.exists("htslib/libhts.a"):
        log.info("building 'libhts.a'")
        with changedir("htslib"):
            # TODO Eventually by running configure here, we can set these
            # extra flags for configure instead of hacking on ALL_CPPFLAGS.
            args = " ".join(ext.extra_compile_args)
            defines = " ".join([format_macro_option(*pair) for pair in ext.define_macros])
            run_make(["ALL_CPPFLAGS=-I. " + args + " " + defines + " $(CPPFLAGS)", "lib-static"])
    else:
        log.warning("skipping 'libhts.a' (already built)")


def prebuild_libcsamtools(ext, force):
    write_configvars_header("samtools/samtools_config_vars.h", ext, "SAMTOOLS")


modules = [
    # The vendored getopt implementation is compiled in this module only;
    # per D-14 it is excluded from every module's exports, and each tool
    # extension links its own private copy from MinGW's static libmingwex
    # (the same isolation as separate samtools.exe/bcftools.exe on
    # Windows). The symbol conflict check exempts exactly that closed
    # symbol set on win32.
    dict(name="pysam.libchtslib",
         prebuild_func=prebuild_libchtslib,
         sources=[source_pattern % "htslib", "pysam/htslib_util.c"] + dynamic_files + os_c_files + msvc_chtslib_sources,
         extra_objects=htslib_objects,
         libraries=external_htslib_libraries),
    dict(name="pysam.libcsamtools",
         prebuild_func=prebuild_libcsamtools,
         sources=[source_pattern % "samtools"] + glob.glob(os.path.join("samtools", "*.pysam.c")) +
         [os.path.join("samtools", "lz4", "lz4.c")] + msvc_tool_private_sources,
         extra_objects=separate_htslib_objects,
         libraries=external_htslib_libraries + internal_htslib_libraries),
    dict(name="pysam.libcbcftools",
         sources=[source_pattern % "bcftools"] + glob.glob(os.path.join("bcftools", "*.pysam.c")) + msvc_tool_private_sources,
         extra_objects=separate_htslib_objects,
         libraries=external_htslib_libraries + internal_htslib_libraries),
    dict(name="pysam.libcutils",
         sources=[source_pattern % "utils"] + msvc_tool_private_sources,
         extra_objects=separate_htslib_objects,
         libraries=external_htslib_libraries + internal_htslib_libraries + internal_samtools_libraries),
    dict(name="pysam.libcalignmentfile",
         sources=[source_pattern % "alignmentfile"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libcsamfile",
         sources=[source_pattern % "samfile"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libcalignedsegment",
         sources=[source_pattern % "alignedsegment"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libctabix",
         sources=[source_pattern % "tabix"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libcfaidx",
         sources=[source_pattern % "faidx"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libcbcf",
         sources=[source_pattern % "bcf"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libcbgzf",
         sources=[source_pattern % "bgzf"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libctabixproxies",
         sources=[source_pattern % "tabixproxies"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
    dict(name="pysam.libcvcf",
         sources=[source_pattern % "vcf"],
         extra_objects=separate_htslib_objects,
         libraries=libraries_for_pysam_module),
]

common_options = dict(
    language="c",
    extra_compile_args=extra_compile_args,
    define_macros=define_macros,
    # for out-of-tree compilation, use absolute paths
    library_dirs=[os.path.abspath(x) for x in ["pysam"] + htslib_library_dirs],
    include_dirs=[os.path.abspath(x) for x in ["pysam"] + htslib_include_dirs + \
                  ["samtools", "samtools/lz4", "bcftools", "."] + include_os + msvc_include_extra])

# add common options (in python >3.5, could use n = {**a, **b}
for module in modules:
    module.update(**common_options)

if IS_MSVC_PYTHON:
    # BUILD-02 (03-03): libchtslib-only compile define. Activates
    # hts_defs.h's HTSLIB_EXPORT -> __declspec(dllexport) machinery on
    # all annotated API (hts_expr.c:28 does the same in-file upstream);
    # consumers link the emitted import library instead. Must be a NEW
    # list -- define_macros is shared object identity across modules.
    for module in modules:
        if module["name"] == "pysam.libchtslib":
            module["define_macros"] = list(module["define_macros"]) + [
                ("HTS_BUILDING_LIBRARY", None)]

classifiers = """
Development Status :: 4 - Beta
Intended Audience :: Science/Research
Intended Audience :: Developers
Programming Language :: Python
Topic :: Software Development
Topic :: Scientific/Engineering
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

metadata = {
    'name': "pysam",
    'version': get_pysam_version(),
    'description': "Package for reading, manipulating, and writing genomic data",
    'long_description': __doc__,
    'long_description_content_type': "text/x-rst",
    'author': "Andreas Heger",
    'author_email': "andreas.heger@gmail.com",
    'license': "MIT",
    'platforms': ["POSIX", "UNIX", "MacOS"],
    'classifiers': [_f for _f in classifiers.split("\n") if _f],
    'url': "https://github.com/pysam-developers/pysam",
    'packages': package_list,
    'ext_modules': [CyExtension(**opts) for opts in modules],
    'cmdclass': {'build_ext': cy_build_ext, 'clean_ext': clean_ext, 'sdist': cythonize_sdist},
    'package_dir': package_dirs,
    'package_data': {'': ['*.pxd', '*.h', 'py.typed', '*.pyi'], },
    'exclude_package_data': {"pysam": ["dynamic_*.h", "version.h"]},
    'include_package_data': False,
    # do not pack in order to permit linking to csamtools.so
    'zip_safe': False,
}

if __name__ == '__main__':
    dist = setup(**metadata)
