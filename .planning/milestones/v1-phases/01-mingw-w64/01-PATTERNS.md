# Phase 1: MinGW-w64 构建系统 - Pattern Map

**Mapped:** 2026-09-17
**Files analyzed:** 7 (5 modified/created, 2 deleted)
**Analogs found:** 7 / 7 (mostly self-analog: this phase extends pysam's own build system)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `setup.py` (modify, 7 surgical edits) | config/build-orchestrator | batch (build pipeline) | `setup.py` itself (self-extend: darwin branches, symbol check) | exact (self) |
| `devtools/msys2-bootstrap.sh` (new) | script (env provisioning) | batch | `devtools/install-prerequisites.sh` | exact (role+style) |
| `devtools/smoke_test.py` (new) | utility/test gate | request-response (in-process dispatch) | `devtools/import.py` (standalone-script style); RESEARCH.md skeleton | partial |
| `INSTALL` (modify) | docs | — | `INSTALL` itself (RST section style) | exact (self) |
| `.gitattributes` (modify) | config | — | `.gitattributes` itself (append eol rules) | exact (self) |
| `pysam/libcutils.pyx` (modify, /dev/null → os.devnull) | Cython module | file-I/O | itself (lines 383, 390) | exact (self) |
| `win32/unistd.h`, `win32/stdint.h` (delete) | shim headers | — | n/a — deletion per D-10 | n/a |

## Pattern Assignments

### `setup.py` — 7 surgical edits (D-08 minimal inline style)

**Analog:** `setup.py` itself. All edit points verified verbatim in RESEARCH.md; planner should quote these lines in plan actions.

**Existing platform-branch style to extend (setup.py:46, 401-423):** small `sys.platform == 'darwin'` inline branches — the win32 branches follow the same shape.

**Edit 1 — UCRT64 fail-fast gate (D-03), top of file before any subprocess:**
```python
# Official MSYS2 detection snippet + MSYSTEM belt-and-braces
def _is_ucrt64_python():
    if os.name != "nt":
        return True  # POSIX: never gate
    return (sysconfig.get_platform().startswith("mingw")
            and os.environ.get("MSYSTEM") == "UCRT64")
# if not -> sys.exit(message == bootstrap script's package list, D-13 single source of truth)
```

**Edit 2 — sh prefix on configure (setup.py:63-68 current):**
```python
retcode = subprocess.call(
    " ".join(("./configure", "--disable-ref-cache", option)),
    shell=True)
```
Fix: on win32 the joined string becomes `"sh ./configure ..."`; POSIX path byte-identical. `--disable-libcurl` arrives via `HTSLIB_CONFIGURE_OPTIONS` env (existing machinery; setup.py:525-529 attempt list already includes it). Do NOT add new `shell=True` call sites (Security Domain).

**Edit 3 — symbol check port (BUILD-03), setup.py:94-112 + 355-366:**
```python
# current nm call: ["nm", "-g", "-P", objfile]  (setup.py:96)
# current silent-skip wrapper (setup.py:357-366):
try:
    if HTSLIB_MODE != 'separate':
        self.check_ext_symbol_conflicts()
except OSError as e:
    log.warning("skipping symbol collision check (invoking nm failed: %s)", e)
```
Port: `_nm_command()` returns `["llvm-nm", "-g", "-P"]` on win32; on win32 call the check OUTSIDE the try/skip so OSError/CalledProcessError propagate (fail-hard); POSIX branch keeps the try/skip byte-identical. Keep-filter (`symtype not in "UFNWw"`) and parser untouched — llvm-nm `-P` emits POSIX.2 format.

**Edit 4 — rpath elif (setup.py:419-423, W5):** add explicit `elif sys.platform == 'win32': pass` — no rpath on PE.

**Edit 5 — win32 branch rewrite in place (D-09, setup.py:632-636 current):**
```python
# Windows compatibility - untested
if platform.system() == 'Windows':
    include_os = ['win32']
    os_c_files = ['win32/getopt.c']
```
Rewrite keeps the key, adds `define_macros += [('random', 'rand'), ('srandom', 'srand')]` (vcfsom.c:362,513 consumers) and implib plumbing.

**Edit 6 — implib for libchtslib (Pattern 4):** `extra_link_args += [f"-Wl,--out-implib,pysam/lib{chtslib_stub}.dll.a"]` on the libchtslib module only; `chtslib_stub` already derived from EXT_SUFFIX at setup.py:652-655 (never pin version). `library_dirs` already contains `pysam/` (setup.py:759-761).

**Edit 7 — getopt single-copy (Pattern 6):** keep `win32/getopt.c` only in libchtslib's sources; remove `+ os_c_files` from the other 12 source lists (setup.py:704-756) — otherwise the now-mandatory symbol check fails on 13x `getopt_long`/`opt*` duplicates.

**Also verify keeps working:** `pysam/config.py` generation from `htslib/config.h` (setup.py:597-620); `prebuild_libchtslib` gate (setup.py:678-692, skips if `htslib/libhts.a` exists — Pitfall 11, document clean step).

### `devtools/msys2-bootstrap.sh` (new)

**Analog:** `devtools/install-prerequisites.sh` (lines 1-48 read in full).

**Structure to mirror:**
```sh
#!/bin/sh -e          # <- same shebang with -e, no set -euo pipefail ceremony
# platform gate first (analog: the dnf/yum/apk/... if-chain opens with detection)
# ... package install via the native package manager ...
# ... post-install verification ...
```
Content per RESEARCH skeleton: UCRT64 `MSYSTEM` gate → `pacman -Syu --needed $PKGS` (the 9 packages from Standard Stack) → `command -v llvm-nm` check → `python -m venv --system-site-packages _venv` → `pip install -e . --no-build-isolation` → `python devtools/smoke_test.py`. **The `PKGS` list is verbatim the fail-fast message content in setup.py (D-03 + D-13 single source of truth).** Document the llvm-tools/binutils pacman file-conflict prompt (Pitfall 10) and a clean/troubleshooting step (`git clean -xfd` in bundled dirs; delete `pysam/config.py`, `.pyd`, `*.dll.a`, egg-info — Pitfall 11).

### `devtools/smoke_test.py` (new, D-04)

**Analog:** no direct devtools test script exists; use RESEARCH.md "Smoke test skeleton" (already repo-verified against `tests/pysam_data/`: `ex1.sam.gz`, `ex1.vcf.gz` + `.tbi`; no plain BAM committed — generate one via `pysam.samtools.view("-b", ...)`). Standalone-script style (argv/sys.exit, no pytest) matches `devtools/import.py`. Hard requirements: explicit `"b"` on every direct `open()` (CLAUDE.md blocking anti-pattern); assert BAM magic `b"BAM\x01"`; exercise `_pysam_dispatch` via `pysam.bcftools.view` so Pitfall 8's `/dev/null` path is covered; exit nonzero on failure; designed as Phase 4 CI gate.

### `INSTALL` (modify)

**Analog:** itself. RST with `===` section underlines and `::` literal blocks (lines 1-50 read). Add a "Windows (MSYS2 UCRT64)" section after existing install sections: (1) manual MSYS2 install link + open UCRT64 shell (D-15); (2) `sh devtools/msys2-bootstrap.sh`. Document canonical command `pip install -e . --no-build-isolation` (D-14 — never document bare `setup.py build`); one sentence: GCC + python.org CPython unsupported in v1 (D-05); `HTSLIB_MODE` must be unset or `shared`.

### `.gitattributes` (modify)

**Analog:** itself (11 lines, read in full — currently only `export-ignore`/`linguist-vendored`, no eol rules). Append: `htslib/** text eol=lf`, `samtools/** text eol=lf`, `bcftools/** text eol=lf`, `*.sh text eol=lf`, `*.pyx text eol=lf` (or equivalent minimal set). Wave-0 blocker: working tree is CRLF-mangled right now (`core.autocrlf=true`; `htslib/configure` has `#! /bin/sh\r\n` byte-verified) — renormalize after committing attributes.

### `pysam/libcutils.pyx` (modify)

**Analog:** itself, lines 383 and 390 — hardcoded `open("/dev/null", ...)` in catch_stdout plumbing. Phase-1-minimal fix per D-08: substitute `os.devnull` at exactly those two sites; full O_BINARY/text-mode audit is Phase 2 (out of scope).

## Shared Patterns

### Platform gating (D-08 style)
**Source:** `setup.py:46, 401-423` (darwin inline branches)
**Apply to:** every setup.py edit — small `sys.platform == 'win32'` / MSYSTEM-gated inline branches at the exact break point; no restructuring, no helper modules; POSIX paths byte-identical.

### Env-var configuration surface
**Source:** `HTSLIB_MODE` / `HTSLIB_CONFIGURE_OPTIONS` / `MAKE` machinery in `setup.py`
**Apply to:** Windows options (`--disable-libcurl`) ride existing env vars; do not invent new config files or new env vars.

### Fail-fast + single source of truth
**Source:** D-03 + D-13
**Apply to:** setup.py gate message ≡ bootstrap script `PKGS` list ≡ INSTALL docs. Never silent-skip on Windows (symbol check; BUILD-03).

### Binary-safe I/O
**Source:** CLAUDE.md anti-pattern table; `win32/unistd.h` dropped-mapping lesson
**Apply to:** smoke_test.py all `open(..., "b")`; libcutils `/dev/null` fix; text-mode audit deferred to Phase 2.

### No-version-pinning
**Source:** `setup.py:652-655` (EXT_SUFFIX-derived names)
**Apply to:** never hardcode cp311/cp312; derive all artifact names from `sysconfig.get_config_var('EXT_SUFFIX')` (Pitfall 9, D-02).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `devtools/smoke_test.py` | test gate | in-process dispatch | No existing smoke/CI-gate script in repo; use RESEARCH.md verified skeleton + `tests/pysam_data/` layout |

## Metadata

**Analog search scope:** `setup.py`, `devtools/`, `win32/`, root (`INSTALL`, `.gitattributes`), `tests/pysam_data/` composition (via RESEARCH.md session verification)
**Files scanned:** 6 read in full or in part this session; all setup.py line references pre-verified verbatim in 01-RESEARCH.md
**Pattern extraction date:** 2026-09-17
