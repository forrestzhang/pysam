#!/usr/bin/env python
"""MSVC compile probe (plan 03-02).

Compiles individual C translation units with the MSVC compiler that
setuptools auto-locates -- no vcvars/environment setup is needed because
setuptools runs the Visual Studio environment discovery internally
(03-RESEARCH Pattern 6/7, verified from plain Git Bash). Compile only,
never link: the goal is an early-warning MSVC-cleanliness check over
vendored trees (vendor/, plan 03-02) and, later, bundled sources
(plans 03-03/03-04) before the build integration depends on them.

Usage:
    python devtools/msvc_compile_probe.py SOURCE... [-I DIR]... [-D NAME[=VAL]]...

One PASS/FAIL line is printed per source. The compiler's own output is
surfaced verbatim on failure (and warning lines are echoed on success, so
nothing passes silently). Compilation uses /W3 and /we4013 so an implicit
function declaration (C4013) is an ERROR, not a warning that would compile
"clean" and detonate at link time (03-RESEARCH Anti-Patterns: cl's clean
compile for undeclared functions is a trap; the D-20 __builtin_setjmp case
is exactly this class).

Exit status: 0 if every source compiled, 1 if any failed, 2 on
initialization/usage errors.
"""

import argparse
import atexit
import os
import shutil
import sys
import tempfile

PROBE_COMPILE_FLAGS = ["/nologo", "/std:c11", "/W3", "/we4013", "/utf-8"]


def _decode_tool_output(raw):
    """cl.exe diagnostics follow the console codepage (cp936 on this
    machine's Chinese locale, UTF-8 elsewhere). Try UTF-8, then the ANSI
    codepage ('mbcs'), then a lossy fallback -- the report must never
    crash on encoding (observed: UnicodeEncodeError 'gbk' at print time)."""
    for encoding in ("utf-8", "mbcs"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


def _import_distutils():
    """Import the compiler factory and error classes.

    setuptools >= ~74 restructured distutils: the MSVC compiler lives in
    setuptools._distutils.compilers.C.msvc and raises CompileError from
    setuptools._distutils.compilers.C.errors -- a DIFFERENT class from the
    legacy setuptools._distutils.errors.CompileError. Collect every variant
    present so the except-clauses match regardless of layout. Falls back to
    the stdlib distutils shim on older interpreters.
    """
    candidates = [
        "setuptools._distutils",
        "distutils",
    ]
    new_compiler = None
    for mod_path in candidates:
        try:
            mod = __import__(mod_path + ".ccompiler", fromlist=["new_compiler"])
            new_compiler = getattr(mod, "new_compiler")
            break
        except (ImportError, AttributeError):
            continue
    if new_compiler is None:
        raise ImportError("no distutils/setuptools ccompiler module found")


    error_specs = [
        ("setuptools._distutils.compilers.C.errors", "CompileError"),
        ("setuptools._distutils.errors", "CompileError"),
        ("distutils.compilers.C.errors", "CompileError"),
        ("distutils.errors", "CompileError"),
        ("setuptools._distutils.errors", "DistutilsPlatformError"),
        ("distutils.errors", "DistutilsPlatformError"),
    ]
    compile_errors = []
    platform_errors = []
    seen = set()
    for mod_path, name in error_specs:
        try:
            mod = __import__(mod_path, fromlist=[name])
            cls = getattr(mod, name)
        except (ImportError, AttributeError):
            continue
        key = (mod_path, name, cls)
        if key in seen:
            continue
        seen.add(key)
        if name == "CompileError":
            if cls not in compile_errors:
                compile_errors.append(cls)
        else:
            if cls not in platform_errors:
                platform_errors.append(cls)

    class _Errors:
        pass

    errors = _Errors()
    errors.new_compiler = new_compiler
    errors.CompileError = tuple(compile_errors) or (Exception,)
    errors.DistutilsPlatformError = tuple(platform_errors) or (Exception,)
    return errors


def make_msvc_compiler():
    """Instantiate and initialize the MSVC compiler object.

    MSVCCompiler.initialize() performs the vcvars-equivalent environment
    discovery (vswhere -> toolset -> Windows SDK) and raises
    DistutilsPlatformError with an actionable message when no Visual Studio
    C++ build tools are installed.
    """
    errors = _import_distutils()
    try:
        compiler = errors.new_compiler(compiler="msvc", force=1)
        compiler.initialize()
    except errors.DistutilsPlatformError as exc:
        print("ERROR: could not initialize the MSVC compiler: %s" % exc,
              file=sys.stderr)
        print("Install Visual Studio Build Tools with the 'Desktop "
              "development with C++' workload (2022 or later), then rerun.",
              file=sys.stderr)
        sys.exit(2)
    return compiler


def compile_one(compiler, source, out_dir, include_dirs, macros,
                extra_preargs, compile_errors):
    """Compile a single TU with the child process's stdout/stderr captured
    at the file-descriptor level (cl.exe writes diagnostics to stdout, and
    distutils lets the child inherit the parent's fds -- a Python-level
    sys.stderr redirect alone would miss it).

    compile_errors is a tuple of every CompileError class variant the
    installed setuptools/distutils may raise (see _import_distutils).

    Returns (ok, captured_text).
    """
    sys.stdout.flush()
    sys.stderr.flush()
    capture = tempfile.TemporaryFile(mode="w+b")
    capture_fd = capture.fileno()
    saved_out = os.dup(1)
    saved_err = os.dup(2)
    try:
        os.dup2(capture_fd, 1)
        os.dup2(capture_fd, 2)
        ok = True
        try:
            compiler.compile([source], output_dir=out_dir,
                             include_dirs=include_dirs, macros=macros,
                             extra_preargs=list(extra_preargs))
        except compile_errors:
            ok = False
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os.dup2(saved_out, 1)
        os.dup2(saved_err, 2)
        os.close(saved_out)
        os.close(saved_err)
    capture.seek(0)
    text = _decode_tool_output(capture.read())
    capture.close()
    return ok, text


def parse_define(raw):
    """-D NAME, -DNAME, -D NAME=VAL, -DNAME=VAL -> distutils macro tuple."""
    if "=" in raw:
        name, value = raw.split("=", 1)
        return (name, value)
    return (raw, None)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compile-only MSVC probe for individual C sources "
                    "(setuptools auto-locates cl.exe; no vcvars needed).")
    parser.add_argument("sources", nargs="+", metavar="SOURCE",
                        help="C source file(s) to compile (no linking)")
    parser.add_argument("-I", "--include", action="append", default=[],
                        metavar="DIR", dest="include_dirs",
                        help="include directory (repeatable)")
    parser.add_argument("-D", "--define", action="append", default=[],
                        metavar="NAME[=VAL]", dest="defines",
                        help="preprocessor define (repeatable)")
    args = parser.parse_args(argv)

    # The report must survive any console codepage (cp936 consoles cannot
    # encode every diagnostic byte; printing must degrade, never crash).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

    sources = []
    for src in args.sources:
        path = os.path.abspath(src)
        if not os.path.isfile(path):
            print("ERROR: source not found: %s" % src, file=sys.stderr)
            return 2
        sources.append(path)
    include_dirs = [os.path.abspath(d) for d in args.include_dirs]
    macros = [parse_define(d) for d in args.defines]

    errors = _import_distutils()
    compiler = make_msvc_compiler()
    out_dir = tempfile.mkdtemp(prefix="msvc_compile_probe-")
    atexit.register(shutil.rmtree, out_dir, ignore_errors=True)

    print("probe: cl.exe = %s" % getattr(compiler, "cc", "<unknown>"))
    print("probe: flags  = %s" % " ".join(PROBE_COMPILE_FLAGS))

    failures = 0
    for source in sources:
        ok, text = compile_one(compiler, source, out_dir, include_dirs,
                               macros, PROBE_COMPILE_FLAGS, errors.CompileError)
        if ok:
            print("PASS %s" % source)
            for line in text.splitlines():
                if "warning" in line.lower():
                    print("     %s" % line)
        else:
            failures += 1
            print("FAIL %s" % source)
            if text.strip():
                print("     --- cl output (verbatim) ---")
                for line in text.rstrip().splitlines():
                    print("     %s" % line)

    total = len(sources)
    print("probe: %d passed, %d failed (of %d)" % (total - failures, failures, total))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
