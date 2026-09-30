---
phase: 01-mingw-w64
reviewed: 2026-09-30T02:46:32Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - .gitattributes
  - .gitignore
  - INSTALL
  - devtools/msys2-bootstrap.sh
  - devtools/probe_symbol_check.py
  - devtools/smoke_test.py
  - pysam/libcutils.pyx
  - setup.py
  - win32/getopt.c
  - win32/getopt.h
findings:
  critical: 2
  warning: 3
  info: 3
  total: 8
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-09-30T02:46:32Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Reviewed the Phase 01 MinGW-w64/UCRT64 build-system port: the setup.py win32
link/gate additions (`--export-all-symbols`, `--out-implib`, `--exclude-symbols`,
the llvm-nm symbol gate and its D-14 getopt exemption), the UCRT64 bootstrap and
acceptance scripts, the `os.devnull` fix in `_pysam_dispatch`, and the vendored
getopt C23/header hardening. Cross-file checks were performed against
`pysam/utils.py` (public `dispatch` API), the installed setuptools
`build_ext.get_ext_fullpath`, bundled htslib's O_BINARY handling
(`htslib/hfile.c:766,792`), htslib's own `random`/`srandom` remap
(`htslib/htslib/hts_os.h:74-78`), and git tracking/ignore state of the
in-tree build artifacts.

Intentional decisions (UCRT64-only gating, import-library-based symbol gate,
closed 7-symbol getopt exemption, `sh -c` configure, `MAKE=mingw32-make`,
editable-install-first workflow) were treated as designed and are not reported.

**Positive result:** no Linux/macOS regressions were found. Every platform
branch added in this phase (`_is_ucrt64_python`, `run_configure`,
`_nm_command`, `run()`, `build_extension`, the `os_c_files` restructuring,
the `os.devnull` substitution) is either no-op or byte-identical on POSIX.
The `os.devnull` change is a strict improvement (POSIX value identical,
`"nul"` now correct on Windows).

**Key concerns:** two Critical findings. (1) The win32 symbol gate looks up
each import library beside `get_ext_fullpath()`, but the implib is always
emitted relative to the source-tree `pysam/` directory — these two paths agree
only for inplace/editable builds, so any non-inplace build (`pip install .`,
`python setup.py build`, `bdist_wheel`) on Windows crashes with an unhandled
`CalledProcessError` from the mandatory gate. (2) `_pysam_dispatch`'s
`save_stdout` path opens the redirect target via C `open()` without
`O_BINARY` — on Windows this is a text-mode fd, and every `\n` a tool writes
through it (BGZF/BAM bytes included) is silently translated to `\r\n`,
exactly the project's blocking text-mode-I/O anti-pattern, reachable from the
public `pysam.utils.dispatch(..., save_stdout=...)` API.

## Critical Issues

### CR-01: Win32 symbol gate reads implib beside `get_ext_fullpath`, but implib is emitted into source-tree `pysam/` — non-inplace builds crash

**File:** `setup.py:409` (lookup), `setup.py:537-554` (emission), `setup.py:457-466` (uncaught failure)
**Issue:** `build_extension` emits the import library via a path relative to
the setup.py cwd:

```python
mod = ext.name.rsplit('.', 1)[-1]
implib = os.path.join("pysam", os.path.splitext(mod + suffix)[0] + ".dll.a")
ext.extra_link_args.append("-Wl,--out-implib," + implib)
```

so it always lands at `<repo>/pysam/libchtslib.<ext-suffix>.dll.a` (verified
present in the working tree). But `check_ext_symbol_conflicts` derives its
lookup from the extension's *build output* path:

```python
objfile = self.get_ext_fullpath(ext.name)
if sys.platform == 'win32':
    objfile = os.path.splitext(objfile)[0] + ".dll.a"
```

For inplace/editable builds (`pip install -e .`) `get_ext_fullpath` returns
`pysam/libchtslib.*.pyd` and the two agree — the tested path works. For any
non-inplace build, setuptools' `get_ext_fullpath` returns
`os.path.join(self.build_lib, "pysam", filename)` (verified in the installed
`setuptools/_distutils/command/build_ext.py:711-716`), so the gate probes
`build/lib/pysam/libchtslib.*.dll.a`, which never exists. `llvm-nm` then exits
nonzero, `subprocess.check_output` raises `CalledProcessError`, and because
the win32 gate deliberately runs outside the exception-swallowing wrapper in
`run()` (setup.py:457-466), the exception propagates and aborts the build with
a raw traceback. Consequence: `pip install .`, `python setup.py build`, and
`bdist_wheel` all hard-crash on the supported UCRT64 platform; only the
editable install path passes. (Sibling *linking* is unaffected — the implib is
found through the absolute `pysam` entry in `library_dirs` — so the failure is
silent until the gate step.)
**Fix:** derive both the emission path and the gate path from the same source.
Easiest is to emit beside the extension's actual output location:

```python
# build_extension, win32 branch
mod = ext.name.rsplit('.', 1)[-1]
out_path = self.get_ext_fullpath(ext.name)          # build_lib or inplace
implib = os.path.join(
    os.path.dirname(out_path),
    os.path.splitext(mod + suffix)[0] + ".dll.a")
ext.extra_link_args.append("-Wl,--out-implib," + implib)
```

`build_extension` already appends `os.path.join(self.build_lib, "pysam")` to
`library_dirs` for non-inplace builds (setup.py:505-506), so sibling `-l`
resolution keeps working in both layouts. Alternatively keep emission as-is
and make the gate mirror the emission construction (`os.path.join("pysam", ...)`)
— but then the gate remains cwd-dependent; the `get_ext_fullpath`-based fix is
safer. Worth adding one non-inplace `python setup.py build` run to the Phase 01
verification or the Phase 4 CI matrix to pin this behavior.

### CR-02: `save_stdout` redirect uses C `open()` without `O_BINARY` — text-mode fd silently corrupts BAM/BGZF written through it on Windows

**File:** `pysam/libcutils.pyx:352`
**Issue:** In `_pysam_dispatch`:

```cython
stdout_h = c_open(stdout_f_bytes, O_WRONLY|O_CREAT|O_TRUNC, 0o666)
```

`c_open` is the raw C `open()` (from `posix.fcntl`). On MSVCRT/UCRT, when
neither `_O_BINARY` nor `_O_TEXT` is passed, the fd defaults to *text* mode:
every `\n` byte written through it is translated to `\r\n`. This branch is
reachable from the public dispatcher API — `pysam/utils.py:76` forwards
`save_stdout=` — so on Windows, e.g.
`pysam.samtools.view("-b", "in.sam", save_stdout="out.bam")` writes its BGZF
output through a text-mode fd and produces a corrupted file (every LF in the
gzip stream becomes CRLF; the file fails the exact magic/parse checks the
phase's own smoke test enforces). Even for text output (SAM/VCF), the saved
bytes get CRLF endings, diverging from POSIX behavior. This is precisely the
project's blocking anti-pattern ("C 端 `open()` 必须 `_O_BINARY`"). Note this
line is pre-existing upstream code, not introduced by this phase — but the
phase both touched the adjacent `c_open` call sites and made Windows a
supported platform, so the hazard is now live. The smoke test does not cover
`save_stdout` (it uses `catch_stdout=False` + the tool's own `-o`, which is
why it passes). POSIX is unaffected (no O_BINARY concept), so the fix is
zero-regression.
**Fix:** OR in a binary flag that is 0 on POSIX, keeping Linux/macOS builds
byte-identical:

```cython
cdef extern from *:
    """
    #ifdef O_BINARY
    #define PYSAM_O_BINARY O_BINARY
    #else
    #define PYSAM_O_BINARY 0
    #endif
    """
    int PYSAM_O_BINARY
```

then

```cython
stdout_h = c_open(stdout_f_bytes,
                  O_WRONLY|O_CREAT|O_TRUNC|PYSAM_O_BINARY, 0o666)
```

(Cython's `posix.fcntl.pxd` does not declare `O_BINARY`, hence the literal
block.) The two `os.devnull` opens at lines 383/390 can take the same flag
for consistency — writes there are discarded, so they are not corrupted
today, only inconsistent. Add a `save_stdout` binary round-trip case
(generate BAM via `save_stdout`, read it back with `AlignmentFile`) to the
smoke gate so this path stays covered.

## Warnings

### WR-01: `probe_symbol_check.py` computes `REPO_ROOT` but globs with a cwd-relative path

**File:** `devtools/probe_symbol_check.py:33,107`
**Issue:** `REPO_ROOT` is derived from `__file__` (line 33) and used only for
`SETUP_PY`; the module glob at line 107 is
`glob.glob(os.path.join("pysam", "libc*.pyd"))` — relative to the current
working directory. Invoking the probe from any directory other than the repo
root (e.g. `python D:/Github/pysam/devtools/probe_symbol_check.py` from `~`)
yields the misleading failure `FAIL: expected >= 13 built modules, found 0`
even on a fully built tree. The sibling `smoke_test.py` resolves the repo root
precisely to avoid this class of failure (lines 27-29).
**Fix:**
```python
modules = sorted(glob.glob(os.path.join(REPO_ROOT, "pysam", "libc*.pyd")))
```

### WR-02: `msys2-bootstrap.sh` silently depends on being run from the repo root

**File:** `devtools/msys2-bootstrap.sh:80-90`
**Issue:** The script's MSYSTEM and `HTSLIB_MODE` gates are explicit, but it
never checks the working directory. `python -m venv ... _venv`,
`. _venv/bin/activate`, `pip install -e .`, and
`python devtools/smoke_test.py` are all cwd-relative. Run from any other
directory, the script creates `_venv` in the wrong place, then
`pip install -e .` fails against a non-package cwd — a confusing failure mode
for the single documented entry point (INSTALL step 2).
**Fix:** Anchor to the script location at the top:
```sh
cd "$(dirname "$0")/.." || exit 1
```

### WR-03: `.gitattributes` uses unconditional `text eol=lf` over whole vendored trees, and its comment misstates git semantics

**File:** `.gitattributes:12-18`
**Issue:** The comment claims "Binaries inside these trees are untouched
(bare `text` = git auto-detection)", but the attributes actually written are
`htslib/** text eol=lf` (etc.). Setting the `text` attribute to a plain value
(bare `text`, with or without `eol=lf`) *forces* text handling — checkin
CRLF→LF normalization is applied to every matching file with no binary
detection; auto-detection only happens with `text=auto` or with no attribute
at all. I verified the currently tracked `htslib/`, `samtools/`, `bcftools/`
trees contain no binary files, so there is no corruption today — but any
binary file added under those globs in the future (test fixture, image,
bundled blob) would be silently LF-"normalized" on `git add`, corrupting it.
**Fix:** Use auto-detection plus forced-LF checkout, which matches the stated
intent:
```
htslib/**                   text=auto eol=lf
samtools/**                 text=auto eol=lf
bcftools/**                 text=auto eol=lf
```
and correct the comment. (`*.sh` / `*.pyx` are safe as-is — those extensions
are text by construction.)

## Info

### IN-01: Smoke test log mislabels a character count as a line count

**File:** `devtools/smoke_test.py:75`
**Issue:** `print("[smoke]     %d vcf lines" % len(output))` — `output` is the
captured stdout string; `len(output)` is the total character count, not the
number of VCF data lines. The assertion (`len(output) > 0`) is fine; only the
log message is wrong, which matters because this script is designed to make CI
failure logs self-explanatory.
**Fix:** `print("[smoke]     %d vcf lines" % len(output.splitlines()))`
(or reword to "bytes/chars").

### IN-02: Probe re-states the gate's duplicate rule instead of extracting it

**File:** `devtools/probe_symbol_check.py:76-93`
**Issue:** `_load_real_parser` carefully extracts `_nm_command` and
`run_nm_defined_symbols` verbatim from setup.py "never re-implemented", but
`duplicate_count` then re-implements the duplicate/exemption rule by hand. If
the gate rule in `check_ext_symbol_conflicts` changes (e.g. the exemption set
becomes conditional), the probe can pass while the build-time gate behaves
differently. The docstring acknowledges this; it is a drift risk, not a bug.
**Fix:** Consider extracting `WIN32_GETOPT_EXEMPT_SYMBOLS` consumers' logic
too, or add a comment in setup.py at the exemption site pointing at the probe
so the two are updated together.

### IN-03: `random`/`srandom` `-D` remap is redundant with htslib's own `hts_os.h` remap (benign today)

**File:** `setup.py:788`
**Issue:** `define_macros.extend([('random', 'rand'), ('srandom', 'srand')])`
duplicates `htslib/htslib/hts_os.h:74-78`, which already does
`#define srandom srand` / `#define random rand` under `#ifdef _WIN32`. The two
definitions are token-identical, so the C standard permits the redefinition
without diagnostics, and I confirmed no bare `random`/`srandom` identifier
exists in samtools/bcftools/pysam sources outside strings/comments and the
intended call sites (`bcftools/vcfsom.c:362,513`). Noting it because the
setup.py comment ("Harmless if UCRT64 headers already declare the POSIX
names") is only accidentally true: if a future UCRT64 `stdlib.h` declared
`random()`, the object-like macro would rewrite that declaration into a
conflicting `rand()` declaration and break the compile.
**Fix:** Optional: drop the `-D` pair and rely on `hts_os.h`, or leave as
belt-and-braces with the fragility noted in the comment.

---

_Reviewed: 2026-09-30T02:46:32Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
