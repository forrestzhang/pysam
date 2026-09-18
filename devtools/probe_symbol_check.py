"""BUILD-03 teeth probe: prove the symbol-conflict gate detects duplicates.

Reuses setup.py's REAL llvm-nm tool resolution and defined-symbol parser
(extracted verbatim via ast -- never re-implemented) against the built
UCRT64 artifacts:

  1. Tool evidence -- the extracted `_nm_command()` resolves to the
     llvm-nm triple in the UCRT64 environment, without depending on any
     log-echo behavior.
  2. Teeth -- judging the SAME binary under two pseudo-extension names
     must report duplicates (the build-time gate would raise LinkError;
     zero teeth means llvm-nm produced nothing parseable, which is a
     failed A2 checkpoint, not a pass).
  3. Honesty -- judging the 13+ real distinct binaries must report zero
     duplicates, independently re-validating the build-time gate,
     including its D-14 closed getopt exemption on win32.

Strip note (first-build finding): the built .pyd files carry no COFF
symbol table (distutils links with -s), so the parser is fed the
unstripped .dll.a import libraries emitted beside them -- the export
surface, which is the only thing cross-module binding can reach and the
exact analogue of the POSIX gate reading .so dynamic symbols.

Exit 0 only when all three assertions hold; nonzero otherwise.
"""

import ast
import glob
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP_PY = os.path.join(REPO_ROOT, "setup.py")

EXPECTED_NM_COMMAND = ["llvm-nm", "-g", "-P"]
EXPECTED_MODULES = 13


def _load_real_parser():
    """ast-extract the real gate pieces from setup.py and exec them.

    `_nm_command` and `run_nm_defined_symbols` must come from the same
    extraction (the parser calls the resolver), plus the D-14 exemption
    set. `frozenset([...])` is a Call node, so take its list argument.
    """
    with open(SETUP_PY, encoding="utf-8") as fh:
        source = fh.read()
    tree = ast.parse(source)
    namespace = {
        "subprocess": subprocess,
        "IS_DARWIN": False,
        "sys": sys,
    }
    exempt = None
    for node in tree.body:
        if (isinstance(node, ast.FunctionDef)
                and node.name in ("_nm_command", "run_nm_defined_symbols")):
            exec(compile(ast.get_source_segment(source, node),
                         SETUP_PY, "exec"), namespace)
        if (isinstance(node, ast.Assign)
                and getattr(node.targets[0], "id", None)
                == "WIN32_GETOPT_EXEMPT_SYMBOLS"):
            value = node.value
            exempt = ast.literal_eval(
                value.args[0] if isinstance(value, ast.Call) else value)
    missing = {"_nm_command", "run_nm_defined_symbols"} - set(namespace)
    if missing or exempt is None:
        raise RuntimeError(
            "could not extract from setup.py: %s" % sorted(missing
            | ({"WIN32_GETOPT_EXEMPT_SYMBOLS"} if exempt is None else set())))
    return namespace["_nm_command"], namespace["run_nm_defined_symbols"], \
        frozenset(exempt)


def duplicate_count(modules, nm_defined, exempt):
    """Re-state of the gate's duplicate rule (check_ext_symbol_conflicts).

    Counts defined symbols claimed by more than one module, honoring the
    D-14 closed exemption on win32 exactly like the build-time gate.
    """
    symbols = {}
    for name, path in modules:
        for sym in nm_defined(path):
            symbols.setdefault(sym, []).append(name)

    raw = sum(1 for owners in symbols.values() if len(owners) > 1)
    hard = raw
    if sys.platform == "win32":
        hard = sum(
            1 for sym, owners in symbols.items()
            if len(owners) > 1 and sym not in exempt)
    return raw, hard


def main():
    nm_command, nm_defined, exempt = _load_real_parser()

    # 1. Tool evidence: the real build-time tool resolution.
    resolved = nm_command()
    print("resolved nm command: %s" % " ".join(resolved))
    if resolved != EXPECTED_NM_COMMAND:
        print("FAIL: expected %r" % (EXPECTED_NM_COMMAND,))
        return 1

    # Strip note (A2 record): the built .pyd carry no COFF symbol table.
    modules = sorted(glob.glob(os.path.join("pysam", "libc*.pyd")))
    if len(modules) < EXPECTED_MODULES:
        print("FAIL: expected >= %d built modules, found %d"
              % (EXPECTED_MODULES, len(modules)))
        return 1
    print("built modules: %d" % len(modules))

    implibs = []
    for pyd in modules:
        implib = os.path.splitext(pyd)[0] + ".dll.a"
        if not os.path.exists(implib):
            print("FAIL: missing import library for %s" % pyd)
            return 1
        implibs.append((os.path.basename(os.path.splitext(pyd)[0]), implib))

    # 2. Teeth: the same binary judged as two extensions must collide.
    # Judge the largest module so the teeth count reflects a real export
    # surface, not a two-symbol feature stub.
    teeth_module = max(implibs, key=lambda m: os.path.getsize(m[1]))
    teeth_pair = [("pseudo-extension-a", teeth_module[1]),
                  ("pseudo-extension-b", teeth_module[1])]
    teeth_raw, teeth_hard = duplicate_count(teeth_pair, nm_defined, exempt)
    print("teeth count (same binary as two extensions): %d" % teeth_hard)
    if teeth_hard <= 0:
        print("FAIL: parser detected no duplicates -- llvm-nm output was "
              "empty or unparseable (failed A2 checkpoint, not a pass)")
        return 1

    # 3. Honesty: the 13+ real distinct binaries must be duplicate-free.
    honest_raw, honest_hard = duplicate_count(implibs, nm_defined, exempt)
    print("real-binaries duplicate count: %d (raw before D-14 exemption: %d)"
          % (honest_hard, honest_raw))
    if honest_hard != 0:
        print("FAIL: real binaries carry non-exempt duplicate symbols")
        return 1

    print("probe OK: tool=%s teeth=%d honesty=0"
          % (" ".join(resolved), teeth_hard))
    return 0


if __name__ == "__main__":
    sys.exit(main())
