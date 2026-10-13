"""IN-W2 lockstep check: prove MSVC_LIBHTS_OBJS mirrors htslib/Makefile.

Reuses setup.py's REAL lockstep comparator (extracted verbatim via ast --
never re-implemented) against a live parity configuration of the bundled
htslib:

  1. Parity configure -- ./configure --disable-ref-cache
     --disable-libcurl (run_configure's exact argv) in htslib/.
  2. Real expansion -- `$(MAKE) -s print-config` (honoring the MAKE env
     var; UCRT64: mingw32-make), LIBHTS_OBJS parsed exactly like
     run_make_print_config.
  3. Verdict -- the extracted check_msvc_libhts_objs_lockstep() judges
     the expansion; exit 0 only on set-equality with the mirror.
  4. --self-test teeth -- a synthetic drift (one real token dropped, one
     phantom *.o added) built from the REAL expansion must make the
     comparator raise LinkError, and a duplicated mirror entry (05 WR-01
     copy-paste drift) must raise too; exit 0 only when the real state
     passes AND both synthetic corruptions raise (probe_symbol_check.py's
     teeth + honesty structure).

Side effects: the configure step mutates htslib/config.h and config.mk
exactly as every UCRT64 build does. The MSVC arm rewrites config.h from
win32/config.h.msvc on every run (the IS_MSVC_PYTHON branch of the
shared/separate arm in setup.py), so toolchain alternation stays safe.

Run under MSYS2 UCRT64 from the repository root:

  MAKE=mingw32-make _venv/bin/python.exe \
      devtools/check_libhts_objs_lockstep.py --self-test
"""

import ast
import os
import subprocess
import sys

try:
    from setuptools.errors import LinkError
except ImportError:
    from distutils.errors import LinkError

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP_PY = os.path.join(REPO_ROOT, "setup.py")
HTSLIB_DIR = os.path.join(REPO_ROOT, "htslib")
PARITY_CONFIGURE_CMD = "./configure --disable-ref-cache --disable-libcurl"


def _load_real_comparator():
    """ast-extract check_msvc_libhts_objs_lockstep and MSVC_LIBHTS_OBJS
    from setup.py and exec them into one namespace, so the verdict here
    IS the build-time verdict (single source of truth)."""
    with open(SETUP_PY, encoding="utf-8") as fh:
        source = fh.read()
    tree = ast.parse(source)
    namespace = {"LinkError": LinkError, "sys": sys}
    mirror = None
    for node in tree.body:
        if (isinstance(node, ast.FunctionDef)
                and node.name == "check_msvc_libhts_objs_lockstep"):
            exec(compile(ast.get_source_segment(source, node),
                         SETUP_PY, "exec"), namespace)
        if (isinstance(node, ast.Assign)
                and getattr(node.targets[0], "id", None)
                == "MSVC_LIBHTS_OBJS"):
            mirror = ast.literal_eval(node.value)
    if "check_msvc_libhts_objs_lockstep" not in namespace or mirror is None:
        raise RuntimeError("could not extract from setup.py: "
                           "check_msvc_libhts_objs_lockstep and/or "
                           "MSVC_LIBHTS_OBJS")
    namespace["MSVC_LIBHTS_OBJS"] = mirror
    return namespace["check_msvc_libhts_objs_lockstep"], mirror


def _run_parity_configure():
    """Recreate the wheel-parity configure state (run_configure's exact
    spawn shape: ["sh","-c",...] on win32, shell=True elsewhere)."""
    sys.stdout.flush()
    if sys.platform == "win32":
        retcode = subprocess.call(
            ["sh", "-c", PARITY_CONFIGURE_CMD], cwd=HTSLIB_DIR)
    else:
        retcode = subprocess.call(
            PARITY_CONFIGURE_CMD, shell=True, cwd=HTSLIB_DIR)
    if retcode != 0:
        print("FAIL: parity configure exited %d (%s)"
              % (retcode, PARITY_CONFIGURE_CMD))
        return False
    return True


def _make_print_config_libhts_objs():
    """LIBHTS_OBJS from `$(MAKE) -s print-config`, parsed exactly like
    run_make_print_config (key=value split, len==2 discipline)."""
    make = os.environ.get("MAKE", "make")
    stdout = subprocess.check_output(
        [make, "-s", "print-config"], cwd=HTSLIB_DIR, encoding="ascii")
    for line in stdout.splitlines():
        if "=" in line:
            row = line.split("=")
            if len(row) == 2 and row[0].strip() == "LIBHTS_OBJS":
                return row[1].strip()
    return None


def main():
    self_test = "--self-test" in sys.argv[1:]

    comparator, mirror = _load_real_comparator()
    print("mirror TUs: %d" % len(mirror))

    if not _run_parity_configure():
        return 1

    expansion = _make_print_config_libhts_objs()
    if not expansion:
        print("FAIL: make print-config produced no parseable "
              "LIBHTS_OBJS line")
        return 1
    make_objs = set(expansion.split())
    print("make LIBHTS_OBJS: %d TUs" % len(make_objs))

    # Real parity state must pass (the same verdict the wired build-time
    # check would give on every UCRT64 build).
    try:
        comparator(expansion)
    except LinkError as err:
        print("FAIL: real parity expansion diverges from the mirror:\n%s"
              % err)
        return 1
    print("lockstep OK: mirror == parity expansion (%d TUs)"
          % len(make_objs))

    if not self_test:
        return 0

    # Teeth: synthetic drift built from the REAL expansion (drop one
    # real token, add one phantom *.o) must make the comparator raise.
    tokens = sorted(make_objs)
    drifted = " ".join(tokens[1:] + ["zzz_lockstep_drift_probe.o"])
    try:
        comparator(drifted)
    except LinkError:
        print("teeth OK: synthetic drift raised LinkError (2-TU delta)")
    else:
        print("FAIL: comparator accepted a synthetic drifted expansion -- "
              "no teeth")
        return 1

    # Teeth (05 WR-01): a duplicated mirror entry (copy-paste drift in
    # MSVC_LIBHTS_OBJS itself) must make the comparator raise. The
    # comparator reads the mirror from the exec namespace it was compiled
    # into (its __globals__); duplicate one entry there, then restore.
    comparator.__globals__["MSVC_LIBHTS_OBJS"] = mirror + mirror[:1]
    try:
        comparator(expansion)
    except LinkError:
        print("teeth OK: duplicated mirror entry raised LinkError")
    else:
        print("FAIL: comparator accepted a duplicated mirror entry -- "
              "no teeth")
        return 1
    finally:
        comparator.__globals__["MSVC_LIBHTS_OBJS"] = mirror
    return 0


if __name__ == "__main__":
    sys.exit(main())
