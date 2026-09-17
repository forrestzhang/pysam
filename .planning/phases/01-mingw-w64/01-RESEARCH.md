# Phase 1: MinGW-w64 构建系统 - Research

**Researched:** 2026-09-17
**Domain:** MSYS2 UCRT64 build-system adaptation of pysam's 807-line autotools-orchestrating setup.py (brownfield, zero POSIX regression)
**Confidence:** HIGH (codebase facts all read and quoted this session; MSYS2 flow CITED from official docs; linker glue ASSUMED with first-build checkpoints)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Pre-locked project constraints (carried forward — do not re-litigate)
- **Autotools flow stays**: `sh configure` and `make` run inside MSYS2; only the `setup.py` invocation pipeline is adapted. Pre-baked `config.h` is the Phase 3 MSVC approach (BUILD-01).
- **Symbol check is mandatory on Windows**: via llvm-nm, actually executed, build fails on duplicates — never silently skipped (BUILD-03, success criterion 3).
- **libcurl/remote I/O stays off** on the Windows path in v1 (REMOTE-01 deferred to v2): configure with `--disable-libcurl` on Windows.
- **UCRT64 environment mandatory**; msvcrt-flavored MinGW is a blocking anti-pattern (python.org CPython fd/heap ABI corruption).
- **MinGW output is dev-validation only** — never distributed as a wheel (wheels are MSVC-only, Phase 3+4).

### Target Python runtime
- **D-01:** The Phase 1 build targets **MSYS2 UCRT64's own pacman python** (`mingw-w64-ucrt-x86_64-python`), NOT python.org CPython — setuptools finds GCC natively, no import-library glue needed. — **Reversibility:** costly — the bootstrap script, INSTALL docs, fail-fast gating, and the v1 support boundary below all encode this choice; Phases 2–4 assume it.
- **D-02:** Validate against a **single Python version** (whatever UCRT64 currently ships). The version matrix is CI-03's job in Phase 4.
- **D-03:** **Strict fail-fast** outside UCRT64: when a Windows build is attempted outside a UCRT64 shell, `setup.py` stops immediately with one actionable message listing the pacman packages to install (message content mirrors the bootstrap script). Protects against msvcrt-MinGW attempts failing deep in compilation.
- **D-04:** Acceptance smoke check is a **committed script** (`devtools/smoke_test.py` or similar): imports pysam, opens a BAM from test data, dispatches one samtools/bcftools command, exits nonzero on failure. Reused later as the Phase 4 CI smoke gate.
- **D-05:** **GCC ↔ python.org-CPython is explicitly unsupported in v1** — documented in one sentence; the real-user Python is served by the Phase 3 MSVC path. Prevents wasted effort on gendef/dlltool glue.
- **D-06:** The build checkout stays at **`D:\Github\pysam`** (Windows path, single checkout, Git Bash workflow unchanged); the UCRT64 shell builds via `/d/Github/pysam`, accepting slower drvfs build iteration.
- **D-07:** Dev installs go into a **venv** created inside the UCRT64 shell (`python -m venv` + `pip install -e .`), not into pacman-managed site-packages.

### setup.py change style
- **D-08:** **Minimal inline diff philosophy**: small `sys.platform == 'win32'` / MSYSTEM-gated branches exactly where the POSIX pipeline breaks (configure/make invocation points, rpath flag, nm call). No restructuring of the 807-line monolith, no helper-module extraction. Keeps the diff upstreamable and the zero-regression review surface small.
- **D-09:** The dead "untested" win32 branch at `setup.py:634` is **rewritten in place** — same insertion point, new working UCRT64 body. No parallel stale branch left behind.
- **D-10:** From the 2013 `win32/` shims, **only `win32/getopt.c` survives** on the UCRT64 include path (MinGW-w64 has no getopt_long). `win32/unistd.h` and `win32/stdint.h` are dropped — UCRT64 GCC ships real ones, and the stale shim is missing `isatty`/`fileno` (W7). Phase researcher verifies per-shim during planning.

### POSIX regression guard
- **D-11:** Linux/macOS zero-regression is verified by **fork CI on every push**: the `win` branch is pushed to the GitHub fork after each committed change; the existing `ci.yaml` ubuntu+macos jobs run automatically on push.
- **D-12:** Success criterion 4 ("existing builds and CI stay green") is defined as: **ubuntu and macos jobs green on the phase's final commit**. The FreeBSD/NetBSD VM jobs are advisory only.

### MSYS2 bootstrap form
- **D-13:** Bootstrap deliverable is **script + docs**: a committed UCRT64 bootstrap script (pacman toolchain/library package list + venv creation + build deps; Windows counterpart to `devtools/install-prerequisites.sh`) plus an INSTALL Windows section documenting the two manual steps. The script is the single source of truth for the fail-fast message content.
- **D-14:** The canonical documented one-step build command is **`pip install -e .`** inside the UCRT64 venv (exercises the PEP 517 path end to end). `setup.py build` remains functional but undocumented.
- **D-15:** Division of labor: **MSYS2 itself is installed manually** (documented link, one GUI run); **the script owns everything after** (pacman packages, venv, build deps).

### Claude's Discretion
- Exact pacman package list contents (researcher/planner determine precise package names and versions).
- Smoke script location and internal structure (`devtools/smoke_test.py` suggested, not mandated).
- The precise detection mechanism for "am I in UCRT64" (MSYSTEM env var vs compiler probe vs both).

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

### Project Constraints (from CLAUDE.md)
- **Linux/macOS 零回归** — highest-priority constraint; every change must be dual-platform safe.
- **不改 htslib/samtools/bcftools 上游功能性行为** — only upstreamable portability patches.
- **msvcrt MinGW (legacy MINGW64) is a blocking anti-pattern** — force UCRT64.
- **Windows text-mode I/O (open() without "b") is a blocking anti-pattern** — smoke script and any new file I/O must be binary-safe.
- **Commits carry NO `Co-Authored-By` trailer** (user explicitly forbids; overrides harness default).
- 32-bit Windows unsupported; roadmap order MSVC (Phase 3) before CI/wheel (Phase 4).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUILD-01 | `setup.py` 在 MSYS2 UCRT64 下完整构建 bundled htslib/samtools/bcftools（保留 autotools 流程，仅管道改造；产物仅用于开发验证） | Verified: `run_configure` uses `shell=True` (needs `sh ` prefix, setup.py:61-73); `run_make`/`run_make_print_config` are list-form subprocess (work as-is once make.exe is on UCRT64 PATH); only htslib is configured/made — samtools/bcftools compile from explicit `*.pysam.c` globs with generated stub config.h (setup.py:486-489, 704-712); dead win32 branch rewrite point verified (setup.py:632-636); rpath branch needs win32 elif (setup.py:419-423 per CONCERNS W5); bootstrap package list determined (Standard Stack); CRLF blocker found in working tree (Pitfall 1) |
| BUILD-03 | 符号冲突检查移植 — `nm` → `llvm-nm`，接入 `check_ext_symbol_conflicts`（Windows 上 duplicate symbol 导致运行时崩溃而非链接错误）；实际上执行、重复即失败、绝不静默跳过 | Verified verbatim: nm call `["nm", "-g", "-P", objfile]` (setup.py:96); keep-filter `if symtype not in "UFNWw" and not cython_internal(sym)` (setup.py:98-99) — keeps T/D/B defined symbols, so cross-extension duplicates are flagged; silent-skip wrapper `except OSError ... log.warning("skipping symbol collision check ...")` (setup.py:355-366) is exactly what must not fire on Windows; check runs on the built extension binaries via `get_ext_fullpath(ext.name)` (setup.py:324-327); llvm-nm ships in pacman package `mingw-w64-ucrt-x86_64-llvm-tools` [CITED: packages.msys2.org]; `-P` is POSIX.2 format, parser-compatible [CITED: llvm.org/docs/CommandGuide/llvm-nm.html]; 13x `os_c_files` getopt duplication would false-positive the check (Pitfall 4, setup.py:704-756) |
</phase_requirements>

## Summary

Phase 1 adapts pysam's existing autotools-orchestrating `setup.py` so that one command — `pip install -e .` inside a UCRT64 venv (D-14) — produces a working dev build. The research finding that reshapes the plan: **the pipeline needs far less rewiring than feared, but two working-tree landmines must be cleared first**. First, this checkout was cloned with `core.autocrlf=true`, so `htslib/configure`, `htslib/Makefile` and friends are **already CRLF-mangled on disk** (`#!/bin/sh\r\n` verified byte-for-byte) — `sh configure` and `make` cannot run in this state; a `.gitattributes` eol fix + renormalization is a Wave-0 prerequisite, not an optional cleanup. Second, the current silent-skip wrapper around the symbol check (`except OSError: log.warning("skipping symbol collision check...")`) is precisely the code path Windows would take today (`nm` absent), so BUILD-03's "never silently skipped" requires making that wrapper fail-hard on win32 while staying byte-identical for POSIX.

The actual build plumbing is small and surgical (D-08 style): `run_configure` joins `"./configure --disable-ref-cache <opts>"` into a `shell=True` string, which under native Windows python runs cmd.exe — a `"sh "` prefix fixes it; `run_make` and `run_make_print_config` already use list-form subprocess and need nothing once make is on PATH. The dead win32 branch (setup.py:632-636, currently `include_os=['win32']; os_c_files=['win32/getopt.c']`) is rewritten in place with: UCRT64 fail-fast detection (official msys2 snippet: `os.name == "nt" and sysconfig.get_platform().startswith("mingw")`), `--disable-libcurl` configure option on Windows, no rpath, llvm-nm substitution, and a `-Wl,--out-implib` import library for `libchtslib` so the 12 downstream extensions can `-l` against it — because GNU ld's `-l` search order (`lib<name>.dll.a` → `<name>.dll.a` → `lib<name>.a` → DLL forms) never matches a `.pyd`.

Two shim-level findings close out D-10's verification duty: (a) `bcftools/vcfsom.c.pysam.c` — which IS compiled, since libcbcftools globs `bcftools/*.pysam.c` — calls `random()`/`srandom()` (lines 362/513), so dropping `win32/unistd.h` (which mapped them to rand/srand) needs a replacement: two `define_macros` entries on the Windows branch; (b) `os_c_files` (getopt.c) is currently appended to all 13 extension sources, which would put `getopt_long` and the `opt*` data symbols in every `.pyd` — the newly-mandatory symbol check would then fail the build on real duplicates. Fix: compile getopt.c once, into `libchtslib`, whose import library every other module already links.

**Primary recommendation:** Wave 0 = CRLF renormalization + bootstrap script + MSYS2 install docs; Wave 1 = the seven surgical setup.py edits (sh prefix, UCRT64 gate, win32 branch rewrite, rpath elif, llvm-nm port with fail-hard, getopt single-copy, vcfsom random macros) + implib plumbing; Wave 2 = `devtools/smoke_test.py` + fork-push CI verification. Every uncertainty resolves at first build; none requires exploratory code.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| configure/make orchestration (htslib) | Build tier (`setup.py` via PEP 517) | MSYS2 UCRT64 shell + binutils/make | setup.py already owns the flow (`configure_library`, `prebuild_libchtslib`); only the subprocess invocation strings change |
| Samtools/bcftools compilation | Build tier (`setup.py` explicit source globs) | UCRT64 GCC | No upstream Makefile exists in the pysam tree (`git ls-files samtools/Makefile` empty) — setup.py lists `*.pysam.c` directly; stub config.h auto-generated (setup.py:486-489, 624-630) |
| Symbol-conflict gate (BUILD-03) | Build tier (`build_ext.run` hook) | llvm-nm binary (llvm-tools package) | Runs on built extension binaries; tool swap + fail-hard is a setup.py-local change |
| UCRT64 environment gating (D-03) | Build tier (`setup.py` top-level check) | Bootstrap script (message source of truth, D-13) | Fail before any compilation; message mirrors bootstrap package list |
| Toolchain/library provisioning (D-15) | OS provisioning tier (pacman script) | Manual MSYS2 installer | D-13/D-15 split: manual installer, scripted everything-after |
| Acceptance smoke (D-04) | Runtime tier (`devtools/smoke_test.py`) | pysam `_pysam_dispatch` in-process | Exercises import → BAM → samtools/bcftools command; designed as future CI gate |
| POSIX zero-regression (D-11/D-12) | CI tier (fork push → ci.yaml) | — | ubuntu+macos matrix jobs already exist (`on: push`); no workflow edit needed in Phase 1 |

## Standard Stack

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| MSYS2 UCRT64 environment | current installer | Build host shell + toolchain root | htslib's officially documented Windows path [CITED: github.com/samtools/htslib INSTALL MSYS2 section]; UCRT (not msvcrt) is the project anti-pattern boundary |
| `mingw-w64-ucrt-x86_64-python` | whatever pacman ships (snapshot: 3.11.9-1; changelog confirms 3.12 migration landed 2024-11-09 — expect 3.12.x+) [CITED: packages.msys2.org/package/mingw-w64-ucrt-x86_64-python; msys2.org/docs/python] | The D-01 target interpreter (cpython-mingw fork) | setuptools finds GCC natively; EXT_SUFFIX `.cp3XX-mingw_x86_64_ucrt.pyd` observed in package file listing [CITED: packages.msys2.org lib-dynload listing] |
| `mingw-w64-ucrt-x86_64-toolchain` (or minimal `-gcc -binutils -make`) | current | GCC + GNU ld + make + (GNU nm as fallback symbol tool) | Standard MSYS2 toolchain group; provides `make` that `run_make` invokes via `os.environ.get("MAKE", "make")` |
| `mingw-w64-ucrt-x86_64-llvm-tools` | current | `llvm-nm` for BUILD-03 | llvm-nm ships in this separate subpackage, NOT the base llvm package [CITED: packages.msys2.org/packages/mingw-w64-ucrt-x86_64-llvm-tools]; note: conflicts with binutils tools packages (pacman may prompt) |
| `mingw-w64-ucrt-x86_64-python-setuptools`, `-python-pip`, `-python-cython` | current (setuptools >= 70.2.0 has native MSYS2 C-extension support) [CITED: msys2.org/docs/python changelog] | Build backend deps inside venv via `--no-build-isolation` | pacman-installed avoids PyPI binary-wheel incompatibility — msys2 python C extensions are NOT compatible with official CPython wheels [CITED: msys2.org/docs/python] |
| `mingw-w64-ucrt-x86_64-zlib`, `-bzip2`, `-xz` (+ optional `-libdeflate`) | current | htslib external libs (`external_htslib_libraries` derived from `make print-config` LIBS at build time) | Same libs the UCRT64 htslinkage needs; single-package mingw ports bundle headers+import libs (no -devel split) |
| Cython (pinned by pyproject) | `Cython>=3,<4` [VERIFIED: pyproject.toml build-system.requires] | .pyx → .c for the 13 modules | pacman `python-cython` satisfies; exact pacman version checked at bootstrap (D-02: no pinning) |

### Supporting
| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| venv with `--system-site-packages` | msys2 python built-in | D-07 dev isolation while still seeing pacman cython/setuptools | msys2 docs confirm venv works from bash: `python -m venv _venv && source _venv/bin/activate` [CITED: msys2.org/docs/python] |
| `.gitattributes` eol rules + renormalization | git built-in | Wave-0 CRLF repair | Mandatory before first build (Pitfall 1) |
| `devtools/install-prerequisites.sh` | existing | Structural template for the UCRT64 bootstrap script (D-13) | Mirrored package-list + fail-fast-message parity |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pacman python (D-01, locked) | python.org CPython + gendef/dlltool glue | Rejected by D-05 — the glue is the least-documented layer; served properly by Phase 3 MSVC |
| GNU binutils `nm` (present in toolchain group) | llvm-nm | BUILD-03 names llvm-nm; both read PE/COFF — llvm-nm per requirement, binutils nm exists as debugging fallback |
| `--no-build-isolation` + pacman build deps | plain `pip install -e .` with PEP 517 isolation | Isolation would pip-fetch setuptools/Cython from PyPI into a scratch env — unproven on mingw python; `--no-build-isolation` is the documented msys2-native flow. `pip install -e . --no-build-isolation` still honors D-14's "one command, PEP 517 end to end" |
| `define_macros` for random→rand | keep a minimal unistd shim header | Macros avoid include-path shadowing risks entirely and are a 2-line diff in the existing branch (D-08) |

**Installation (bootstrap script owns this, D-13/D-15):**
```bash
# inside UCRT64 shell, after manual MSYS2 install:
pacman -Syu --needed \
  mingw-w64-ucrt-x86_64-python \
  mingw-w64-ucrt-x86_64-python-pip \
  mingw-w64-ucrt-x86_64-python-setuptools \
  mingw-w64-ucrt-x86_64-python-cython \
  mingw-w64-ucrt-x86_64-toolchain \
  mingw-w64-ucrt-x86_64-llvm-tools \
  mingw-w64-ucrt-x86_64-zlib \
  mingw-w64-ucrt-x86_64-bzip2 \
  mingw-w64-ucrt-x86_64-xz
```

**Version verification:** exact pacman versions are deliberately NOT pinned (D-02); the bootstrap script should print `pacman -Qi` versions for the log. Registry existence verified via packages.msys2.org this session [CITED]; msys2 packages are GPG-signed from the configured repos, so the npm-style slopsquat vector does not apply (see Package Legitimacy Audit).

## Package Legitimacy Audit

> This phase installs no npm/PyPI packages; all installs are pacman packages from the signed MSYS2 repos plus git-tracked vendored sources. The seam's `package-legitimacy check` covers npm/pypi/crates ecosystems only, so the audit below substitutes registry-existence verification performed this session.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| mingw-w64-ucrt-x86_64-python | MSYS2 ucrt64 (pacman, GPG-signed) | long-lived | repo-maintained | msys2-packages / msys2-contrib/cpython-mingw | OK | Approved [CITED: packages.msys2.org/package/mingw-w64-ucrt-x86_64-python] |
| mingw-w64-ucrt-x86_64-llvm-tools | MSYS2 ucrt64 | long-lived | repo-maintained | msys2-packages / llvm-project | OK | Approved [CITED: packages.msys2.org/packages/mingw-w64-ucrt-x86_64-llvm-tools] |
| mingw-w64-ucrt-x86_64-{toolchain,zlib,bzip2,xz} | MSYS2 ucrt64 | long-lived | repo-maintained | msys2-packages | OK | Approved (core MSYS2 packages) |
| mingw-w64-ucrt-x86_64-python-{pip,setuptools,cython} | MSYS2 ucrt64 | long-lived | repo-maintained | msys2-packages | OK | Approved — existence cross-confirmed via the python package's "Required By" listing [CITED: packages.msys2.org] |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none
**Note:** No PyPI fetches occur on the recommended path (`--no-build-isolation` uses pacman-provided setuptools/Cython). If a future task pip-installs anything, run the legitimacy gate then.

## Architecture Patterns

### System Architecture Diagram

```
 Developer (UCRT64 shell, /d/Github/pysam)
        |
        v
 pip install -e . --no-build-isolation          [D-14 canonical command]
        |
        v
 PEP 517 backend (pacman setuptools + Cython)
        |
        v
 setup.py import-time pipeline
        |-- [gate] UCRT64 detection: os.name=="nt" and
        |          sysconfig.get_platform().startswith("mingw")   --> fail-fast w/ pacman message (D-03)
        |
        |-- configure_library("htslib"):
        |       subprocess.call("sh ./configure --disable-ref-cache --disable-libcurl", shell=True)
        |           |                    (win32: "sh " prefix + curl off; POSIX: byte-identical path)
        |       htslib/config.h produced
        |
        |-- run_make_print_config()  [list-form, works as-is]
        |       htslib make flags -> LIBHTS_OBJS, LIBS -> external_htslib_libraries
        |
        |-- pysam/config.py generated from config.h keys (setup.py:597-620)
        |
        v
 build_ext (13 Cython extension modules, ordered)
        |
        |-- prebuild: make lib-static  ->  htslib/libhts.a   (skipped iff libhts.a exists — Pitfall 11)
        |
        |-- [1] libchtslib.pyd  <- libhts.a objects + win32/getopt.c (SINGLE copy)
        |       + -Wl,--out-implib=pysam/libchtslib<EXT_SUFFIX-stem>.dll.a   [Windows only]
        |
        |-- [2] libcsamtools.pyd / libcbcftools.pyd  <- glob(*.pysam.c) + lz4
        |       link -lchtslib<stem>  ->  finds the .dll.a implib (GNU ld search order)
        |
        |-- [3..13] libcutils + feature modules  <- link chtslib/csamtools/cbcftools/cutils implibs
        |
        v
 check_ext_symbol_conflicts  (BUILD-03)
        |-- llvm-nm -g -P <each built .pyd>       [win32 substitution; fail-hard, no skip]
        |-- duplicate defined symbols -> LinkError, build fails
        |
        v
 devtools/smoke_test.py  (D-04)
        |-- import pysam; AlignmentFile(ex1.sam.gz -> view -b) ; samtools/bcftools dispatch
        |
        v
 git push origin win  ->  fork ci.yaml ubuntu+macos green  (D-11/D-12 zero-regression proof)
```

### Recommended Project Structure (delta only)
```
pysam/ (repo root — no restructuring per D-08)
├── setup.py                  # 7 surgical edits (see Patterns 1-7)
├── .gitattributes            # + eol=lf rules for bundled dirs (Wave 0)
├── win32/
│   ├── getopt.c / getopt.h   # KEEP (D-10) — now compiled once, into libchtslib
│   ├── unistd.h              # DELETE (D-10) — random/srandom gap handled by define_macros
│   └── stdint.h              # DELETE (D-10)
├── devtools/
│   ├── install-prerequisites.sh   # existing POSIX template
│   └── msys2-bootstrap.sh         # NEW (D-13): pacman list + venv + dep check
├── devtools/smoke_test.py         # NEW (D-04): import/BAM/dispatch gate
└── INSTALL                        # + Windows section (two manual steps + canonical command)
```

### Pattern 1: UCRT64 detection + fail-fast (D-03; discretion area resolution)
**What:** Use MSYS2's official detection snippet, ORed with the MSYSTEM env check for belt-and-braces.
**When to use:** Top of setup.py, before any subprocess fires; error message = bootstrap script's package list (D-13 single source of truth).
**Example:**
```python
# Source: https://www.msys2.org/docs/python/ (official detection recommendation)
def _is_ucrt64_python():
    if os.name != "nt":
        return True  # POSIX: never gate
    if sysconfig.get_platform().startswith("mingw") and os.environ.get("MSYSTEM") == "UCRT64":
        return True
    return False

if not _is_ucrt64_python():
    sys.exit(
        "pysam Windows builds require the MSYS2 UCRT64 environment and its pacman python.\n"
        "Inside a UCRT64 shell run: sh devtools/msys2-bootstrap.sh\n"
        "Required packages: mingw-w64-ucrt-x86_64-{python,python-pip,python-setuptools,"
        "python-cython,toolchain,llvm-tools,zlib,bzip2,xz}")
```
Note: the existing dead branch already keys on `platform.system() == 'Windows'` (setup.py:632), which is also True under pacman python — the rewrite keeps that key and adds the UCRT64 gate above it.

### Pattern 2: configure invocation under native Windows python
**What:** `shell=True` on Windows spawns cmd.exe, which cannot execute `./configure`. Minimal fix: prefix `"sh "`.
**Verified current code (setup.py:63-68):**
```python
        # Always disable ref-cache as its code is omitted from pysam's htslib/
        retcode = subprocess.call(
            " ".join(("./configure", "--disable-ref-cache", option)),
            shell=True)
```
**Fix (D-08 style):**
```python
        prefix = ("sh ", ) if sys.platform == 'win32' else ("", )
        retcode = subprocess.call(
            " ".join(("sh" if sys.platform == 'win32' else "./configure",)
                     + ()) , shell=True)  # see planner note: join(("./configure", ...)) -> "sh ./configure ..."
```
Concretely: on win32 the joined string becomes `"sh ./configure --disable-ref-cache <option>"`; on POSIX it stays byte-identical. `--disable-libcurl` arrives via `HTSLIB_CONFIGURE_OPTIONS` env on the Windows path (existing machinery; the configure attempt list at setup.py:525-529 already includes `"--disable-libcurl"`).

### Pattern 3: symbol check port (BUILD-03)
**Verified current code (setup.py:94-112, excerpts):**
```python
def run_nm_defined_symbols(objfile):
    stdout = subprocess.check_output(["nm", "-g", "-P", objfile], encoding="ascii")
    ...
        if symtype not in "UFNWw" and not cython_internal(sym):
```
**Verified skip wrapper (setup.py:357-366):**
```python
        try:
            if HTSLIB_MODE != 'separate':
                self.check_ext_symbol_conflicts()
        except OSError as e:
            log.warning("skipping symbol collision check (invoking nm failed: %s)", e)
        except subprocess.CalledProcessError:
            log.warning("skipping symbol collision check (invoking nm failed)")
```
**Port:**
```python
def _nm_command():
    if sys.platform == 'win32':
        return ["llvm-nm", "-g", "-P"]   # UCRT64 llvm-tools; never silently absent (D-03/BUILD-03)
    return ["nm", "-g", "-P"]

# in build_ext.run(): on win32, do not swallow the failure:
if sys.platform == 'win32':
    self.check_ext_symbol_conflicts()      # OSError/CalledProcessError propagate -> build fails
else:
    try:
        if HTSLIB_MODE != 'separate':
            self.check_ext_symbol_conflicts()
    except (OSError, subprocess.CalledProcessError):
        log.warning("skipping symbol collision check (invoking nm failed)")  # POSIX behavior unchanged
```
`llvm-nm -P` emits POSIX.2 format, so the existing two-column parser (`line.split()[:2]`) is untouched [CITED: llvm.org/docs/CommandGuide/llvm-nm.html — `-P`, `--portability`]. The check already operates on built binaries (`get_ext_fullpath`), i.e. `.pyd` files on Windows; llvm-nm reads COFF/PE (fallback if not: toolchain's GNU `nm` also handles PE — same flag surface).

### Pattern 4: cross-extension import library (`--out-implib`)
**What:** The 12 downstream modules link `-lchtslib<EXT_SUFFIX-stem>` (setup.py:652-655 derives the name from `sysconfig.get_config_var('EXT_SUFFIX')`). GNU ld's `-l` search order on PE/COFF is `lib<name>.dll.a` → `<name>.dll.a` → `lib<name>.a` → import-lib/`.lib` forms → direct DLL forms (`lib<name>.dll`, `<name>.dll`) [CITED: sourceware.org binutils ld docs, Options + WIN32 sections] — a `.pyd` is never found. Generate a properly-named import library when linking libchtslib:
```python
# in the rewritten win32 branch (D-09):
suffix = sysconfig.get_config_var('EXT_SUFFIX')          # e.g. '.cp311-mingw_x86_64_ucrt.pyd'
chtslib_stub = os.path.splitext(f"chtslib{suffix}")[0]   # existing line, setup.py:653-655
# for the libchtslib module only, on win32:
implib = os.path.join("pysam", f"lib{chtslib_stub}.dll.a")
#   -> add to libchtslib's extra_link_args: f"-Wl,--out-implib,{implib}"
#   -> -l{chtslib_stub} then resolves via ld's lib<name>.dll.a rule in library_dirs ("pysam", setup.py:759-761)
```
Runtime resolution of the dependency `libchtslib....pyd` from sibling `.pyd`s relies on Python 3.8+ `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR` (the loaded extension's own directory is searched) [ASSUMED — standard CPython Windows behavior; proven by the smoke test's first run].

### Pattern 5: win32 branch rewrite (D-09) with shim resolution (D-10 verification duty)
**Verified current branch (setup.py:632-636):**
```python
# Windows compatibility - untested
if platform.system() == 'Windows':
    include_os = ['win32']
    os_c_files = ['win32/getopt.c']
```
**Research-verified shim facts:**
- `win32/` tracked files are exactly `getopt.c getopt.h stdint.h unistd.h` [VERIFIED: `git ls-files win32/` this session].
- `win32/unistd.h` maps `srandom→srand, random→rand, access→_access, ftruncate→_chsize, ssize_t=int` and lacks `isatty`/`fileno` [VERIFIED: file read this session] — dropping it is correct (W7).
- **`bcftools/vcfsom.c` / `vcfsom.c.pysam.c` call `random()` (line 362/364) and `srandom(args->rand_seed)` (line 513/515) and include `<unistd.h>` (line 26)** [VERIFIED: grep + read this session]. The `.pysam.c` twin IS compiled: libcbcftools sources glob `bcftools/*.pysam.c` (setup.py:713-717). So the dropped random→rand mapping has one live consumer. Replacement without a shim header:
```python
if platform.system() == 'Windows':
    include_os = ['win32']
    os_c_files = ['win32/getopt.c']        # compiled ONCE (see Pattern 6)
    define_macros += [('random', 'rand'), ('srandom', 'srand')]  # vcfsom.c needs this
```
- htslib's own `random()`/`srandom()` uses are inside `#ifdef TEST_MAIN` (thread_pool.c: `#ifndef TEST_MAIN` at :25, `#ifdef TEST_MAIN` at :1159, `int main(` at :1518) and never compile into libhts.a [VERIFIED this session].
- samtools/ and bcftools/ trees contain no other `random(`/`srandom(` callers [VERIFIED: grep this session].
- Verify-at-first-compile (cheap, both paths ready): if UCRT64 headers do declare random/srandom, the two macros are harmless and can be dropped.

### Pattern 6: getopt single-copy (prerequisite for BUILD-03 to ever pass on Windows)
**Verified:** `os_c_files` is appended to every module's sources (13 modules, setup.py:704-756), and the check's keep-filter (`symtype not in "UFNWw"`) retains globally-defined `getopt_long`/`optind`/`optarg`/`opterr`/`optopt` from win32/getopt.c in all 13 `.pyd`s → the newly mandatory check would raise `LinkError("symbols defined in multiple extensions")` on legitimate, intended sharing.
**Fix:** compile `win32/getopt.c` once, into `libchtslib` (first module); every other module already links `internal_htslib_libraries`, so the import library carries the resolution. MinGW exports all symbols by default, so `getopt_long` remains callable cross-extension. Remove `+ os_c_files` from the other 12 source lists (still a small, reviewable diff).
**Note:** modern mingw-w64 may ship its own `getopt.h`/`getopt_long` in headers+libmingwex [ASSUMED]; D-10 keeps the vendored copy regardless (harmless-if-redundant: our object satisfies the symbol first; `-I win32` precedes system includes). Record the verification outcome in the build log.

### Pattern 7: rpath elif (W5) and /dev/null minimal fix (W3)
- rpath branch `setup.py:419-423` (`-Wl,-rpath,$ORIGIN`) must gain an explicit win32 elif that adds nothing — Windows has no rpath; PE dependency resolution is directory-based (Pattern 4).
- `pysam/libcutils.pyx` opens `"/dev/null"` at :383 and :390 (catch_stdout plumbing) — native Windows raises OSError for the samtools `view`/`mpileup`/`depad`/`calmd` and most bcftools dispatch paths the smoke test exercises. Phase-1-minimal fix consistent with D-08: `os.devnull` substitution at those two sites (full O_BINARY/text-mode audit remains Phase 2 per phase boundary).

### Anti-Patterns to Avoid
- **Hand-writing config.h or faking configure output:** Phase 3's pre-baked approach explicitly deferred; Phase 1 keeps real `sh configure` (CONTEXT pre-locked).
- **`gendef`/`dlltool` import-library glue:** D-05 forbids the python.org-CPython direction entirely.
- **Silently skipping the symbol check with a warning on Windows:** the exact failure BUILD-03 exists to remove; skip semantics stay POSIX-only.
- **Pinning pacman package versions or hardcoding the python minor version (cp311 vs cp312):** D-02 forbids; EXT_SUFFIX is already derived dynamically (setup.py:652-655).
- **Using PyPI binary wheels under pacman python:** incompatible by design [CITED: msys2.org/docs/python].
- **Text-mode I/O in the smoke script:** open all files with explicit `"b"` (CLAUDE.md blocking anti-pattern).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Import library for libchtslib.pyd | gendef+dlltool symbol harvesting | `-Wl,--out-implib` at link time | One flag, exact symbols, no stale .def maintenance; gendef glue is the D-05-forbidden direction |
| "Am I in UCRT64" probe | custom compiler-version regex probing | `sysconfig.get_platform().startswith("mingw")` (official snippet) + `MSYSTEM` | Officially recommended by MSYS2 docs; zero maintenance [CITED: msys2.org/docs/python] |
| POSIX-format symbol dump | custom COFF parser or `objdump -T` post-processing | `llvm-nm -g -P` (same output contract as the existing `nm -g -P` parser) | `-P` is POSIX.2 format by definition; existing parser untouched [CITED: llvm-nm command guide] |
| BAM test data | hand-crafting BAM bytes | generate from committed `tests/pysam_data/ex1.sam.gz` via `pysam.samtools.view("-b", ...)` inside the smoke script | No plain BAM is committed (`0example_no_seq_in_header.bam` is gzip magic `1f 8b 08`, not BAM) [VERIFIED this session]; generating one also exercises `_pysam_dispatch` — two acceptance criteria in one step |
| Toolchain provisioning | bespoke compiler detection/install logic | `devtools/msys2-bootstrap.sh` mirroring `devtools/install-prerequisites.sh` structure (D-13) | Established repo pattern; script is the fail-fast message source of truth |
| Windows venv flow | custom site-packages juggling | `python -m venv --system-site-packages` + `pip install -e . --no-build-isolation` | Documented msys2 python flow [CITED: msys2.org/docs/python]; keeps pacman cython/setuptools visible (D-07) |

**Key insight:** every "hard" part of this phase (autotools on Windows, mingw python, symbol checks) already has an official, documented mechanism — the work is wiring them into setup.py's existing seams, not inventing build technology.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — verified: no databases, no `.planning` runtime stores with build state | none |
| Live service config | Fork CI: `ci.yaml` runs ubuntu+macos on every push of `win` to `git@github.com:forrestzhang/pysam.git` (origin) — verified `on: [push, pull_request]`, matrix `[ubuntu, macos]` [VERIFIED: .github/workflows/ci.yaml:1-80 read pre-plan]; no Windows runner exists yet (Phase 4) | none — mechanism is the D-11/D-12 proof path |
| OS-registered state | None — verified: no scheduler/pm2/launchd items reference pysam builds | none |
| Secrets/env vars | Build-config env vars (no rename, but stale-env hazard): `HTSLIB_MODE` (shared/separate/external), `HTSLIB_CONFIGURE_OPTIONS`, `MAKE`, `CIBUILDWHEEL`; `HTSLIB_MODE=separate` silently disables the symbol check (setup.py:358) and `HTSLIB_MODE=external` skips the whole bundled path | Bootstrap script should assert a clean/sane env (`HTSLIB_MODE` unset or `shared`) before building; document in INSTALL Windows section |
| Build artifacts | Working tree currently PRISTINE — verified absent: `htslib/config.h`, `htslib/libhts.a`, `pysam/config.py`, `*.egg-info`, `pysam/*.so`, `pysam/*.pyd` [VERIFIED: ls this session]. After a build, generated state accumulates: `htslib/config.h`, `htslib/config_vars.h`, `htslib/libhts.a`, `htslib/config.mk`-style make outputs, `samtools/config.h` + `samtools/samtools_config_vars.h`, `bcftools/config.h`, `pysam/config.py`, 13 `.pyd` + import libs in `pysam/`, egg-info. `prebuild_libchtslib` **skips rebuild when `htslib/libhts.a` exists** (verbatim gate: `if force or not os.path.exists("htslib/libhts.a")`, setup.py:685-687) — a stale libhts.a from a failed/changed config silently persists | Add a documented clean step (`git clean -xfd` in bundled dirs + delete `pysam/config.py`, `.pyd`s, `*.dll.a`, egg-info) to the bootstrap script's troubleshooting section; planner should include it before any "rebuild after config change" task |
| Working-tree text encoding | **CRLF corruption is present right now**: `core.autocrlf=true` [VERIFIED: `git config core.autocrlf` this session] has mangled `htslib/configure` (od dump: `#! /bin/sh\r\n`), `htslib/Makefile`, `bcftools/vcfsom.c`, `samtools/samtools.pysam.c` [VERIFIED: `file` output this session] | Wave 0 blocker — see Pitfall 1 |

## Common Pitfalls

### Pitfall 1: CRLF working tree breaks the autotools flow (BLOCKER, present now)
**What goes wrong:** `sh ./configure` fails immediately (`$'\r': command not found` / bad interpreter behavior) and `make` chokes on `\r` in recipes/`*.mk` includes, because the bundled shell scripts and Makefiles were checked out with CRLF.
**Why it happens:** The machine's `git config core.autocrlf=true` converts text files at checkout; upstream pysam has no `.gitattributes` eol rules for the bundled dirs (current `.gitattributes` only sets `linguist-vendored`/`export-ignore`) [VERIFIED: read this session].
**How to avoid:** Wave-0 task: add eol rules (e.g. `htslib/** text eol=lf`, `samtools/** text eol=lf`, `bcftools/** text eol=lf`, `*.sh text eol=lf`) and renormalize (`rm` affected files + `git checkout -- <paths>` after committing the attributes, or fresh clone). Zero POSIX impact (POSIX checkouts are already LF).
**Warning signs:** first UCRT64 build fails before any compilation, with `\r` in the error text.

### Pitfall 2: `shell=True` configure string hits cmd.exe (W1)
**What goes wrong:** `subprocess.call(" ".join(("./configure", ...)), shell=True)` under native Windows python runs cmd.exe → `'./configure' is not recognized...` (or worse, an msys `configure.exe` shim never found).
**Why:** Python's Windows `shell=True` is `cmd.exe /c`; the existing code catches only OSError, so a cmd-level failure surfaces as `retcode != 0` at best.
**How to avoid:** `"sh "` prefix on win32 (Pattern 2); keep the POSIX string byte-identical.
**Warning signs:** configure "failed" log before gcc ever runs.

### Pitfall 3: Symbol check silently skipped on Windows (BUILD-03 killer)
**What goes wrong:** today's Windows build would take `except OSError: log.warning("skipping symbol collision check ...")` because `nm` is absent — the exact behavior BUILD-03 forbids.
**Why:** the wrapper was written for optional-nm POSIX environments.
**How to avoid:** win32 path calls the check outside the try/skip (Pattern 3); error message points at `pacman -S mingw-w64-ucrt-x86_64-llvm-tools`.
**Warning signs:** "skipping symbol collision check" in build output on Windows.

### Pitfall 4: 13 copies of getopt.c false-positive the newly-mandatory check
**What goes wrong:** `os_c_files` is in every module's sources (setup.py:704-756); `getopt_long` + `opt*` data symbols then appear in all 13 `.pyd`s; `check_ext_symbol_conflicts` raises `LinkError("symbols defined in multiple extensions")` (setup.py:331-337).
**Why:** the original branch predates the symbol check's Windows activation; on POSIX `os_c_files` is empty.
**How to avoid:** compile getopt.c once into libchtslib (Pattern 6).
**Warning signs:** duplicate-symbol errors naming `getopt_long`/`optind` right after enabling the check.

### Pitfall 5: `vcfsom.c.pysam.c` needs random/srandom after the shim drop
**What goes wrong:** `error: use of undeclared identifier 'random'` (or implicit-declaration) compiling libcbcftools.
**Why:** `bcftools/vcfsom.c:362,513` call `random()`/`srandom()`; only the deleted `win32/unistd.h` provided the mapping; mingw-w64 does not declare POSIX `random`/`srandom` [ASSUMED — verify at first compile; macros are harmless if it does].
**How to avoid:** `define_macros += [('random', 'rand'), ('srandom', 'srand')]` on the win32 branch (Pattern 5).
**Warning signs:** undeclared-identifier errors isolated to vcfsom.

### Pitfall 6: `-lchtslib<stem>` cannot find a `.pyd`
**What goes wrong:** downstream extension links fail with `cannot find -lchtslib.cp3XX-mingw_x86_64_ucrt` or undefined `PyInit__chtslib`-style errors.
**Why:** GNU ld `-l` on PE searches `lib<name>.dll.a`, `<name>.dll.a`, `lib<name>.a`, then DLL name patterns — never `.pyd` [CITED: binutils ld WIN32 docs].
**How to avoid:** `-Wl,--out-implib,pysam/lib<stem>.dll.a` on the libchtslib link (Pattern 4); implib lands in `library_dirs` (`pysam/`, setup.py:759-761).
**Warning signs:** first downstream module (`libcsamtools`) fails to link while libchtslib linked fine.

### Pitfall 7: rpath flag on the PE link line (W5)
**What goes wrong:** the non-darwin branch appends `-Wl,-rpath,$ORIGIN` for every non-macOS platform including win32; PE ld does not implement ELF rpath semantics (behavior ranges from ignored to link error).
**How to avoid:** explicit `elif sys.platform == 'win32': pass` (no rpath) at setup.py:419-423.
**Warning signs:** unknown-option warnings from ld during first link.

### Pitfall 8: `/dev/null` in libcutils breaks smoke dispatch (W3)
**What goes wrong:** `OSError: [Errno 22] Invalid argument: '/dev/null'` when the smoke test dispatches `samtools view` (or most bcftools commands) with catch_stdout plumbing.
**Why:** `pysam/libcutils.pyx:383` and `:390` open hardcoded `"/dev/null"` [VERIFIED: read this session].
**How to avoid:** `os.devnull` at those two sites (Phase-1-minimal per D-08; full audit stays Phase 2).
**Warning signs:** smoke test failing only on dispatching commands, not on import/BAM-open.

### Pitfall 9: pacman python version drift and PyPI wheel incompatibility
**What goes wrong:** hardcoding `cp311` breaks when UCRT64 moves to 3.12+; pip-installing binary wheels (e.g. during build isolation) fails or corrupts.
**Why:** msys2 python tracks upstream quickly (3.12 landed 2024-11-09 [CITED: msys2.org/docs/python]); its extensions are ABI-incompatible with python.org wheels [CITED: same].
**How to avoid:** never pin (D-02); always derive names from `EXT_SUFFIX` (already the codebase pattern); use pacman build deps + `--no-build-isolation`.
**Warning signs:** `.pyd` name mismatches; pip trying to build Cython from sdist inside an isolated env.

### Pitfall 10: llvm-tools package conflicts with binutils tools
**What goes wrong:** `pacman -S mingw-w64-ucrt-x86_64-llvm-tools` may prompt about file conflicts with binutils tools packages.
**Why:** the tools subpackage ships overlapping utility names [CITED: packages.msys2.org package page].
**How to avoid:** bootstrap script documents the prompt/flags (`--ask` or accept replacement); verify `llvm-nm --version` at script end.
**Warning signs:** pacman file-conflict prompt during bootstrap.

### Pitfall 11: stale `libhts.a` gates rebuilds
**What goes wrong:** after changing configure options or toolchain, `prebuild_libchtslib` skips because `htslib/libhts.a` exists (verbatim gate setup.py:685-687), producing a stale-link build.
**How to avoid:** documented clean step (Runtime State Inventory row); planner adds it before rebuild-after-config-change tasks.

### Pitfall 12: win32/getopt.h shadowing vs UCRT64's own getopt.h
**What goes wrong:** potential declaration conflicts if mingw-w64's headers are pulled alongside `-I win32`.
**Why:** both provide `getopt.h`; `-I win32` wins (distutils puts extra include dirs first), and the vendored pair is self-consistent — but indirect includes could see the vendored declarations.
**How to avoid:** keep the pair (D-10 locked); verify clean compile at first build; if conflicts appear, the fallback is dropping the vendored copy only after confirming UCRT64 provides `getopt_long` [ASSUMED premise per D-10 — verify opportunistically].

## Code Examples

### Smoke test skeleton (D-04; reusable as Phase 4 CI gate)
```python
# Source: repo test data layout verified this session (tests/pysam_data/)
import os, sys, tempfile
import pysam

def main():
    data = os.path.join("tests", "pysam_data", "ex1.sam.gz")
    with tempfile.TemporaryDirectory() as tmp:
        bam = os.path.join(tmp, "ex1.bam")
        # 1) samtools dispatch exercised here (view -b uses MAP_STDOUT_OPTIONS/catch_stdout path)
        pysam.samtools.view("-b", "-o", bam, data)
        # binary-mode open for any direct file I/O (CLAUDE.md anti-pattern guard)
        with open(bam, "rb") as fh:
            assert fh.read(4) == b"BAM\x01", "not a BGZF/BAM file"
        # 2) open + iterate through htslib bindings
        with pysam.AlignmentFile(bam, "rb") as f:
            n = sum(1 for _ in f.fetch(until_eof=True))
        assert n > 0
        # 3) bcftools dispatch (ex1.vcf.gz + .tbi are committed)
        vcf = os.path.join("tests", "pysam_data", "ex1.vcf.gz")
        out = pysam.bcftools.view("-H", vcf)
        assert out is not None
    print("smoke OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Bootstrap script skeleton (D-13; message = fail-fast source of truth)
```bash
#!/bin/sh
# Source: mirrors devtools/install-prerequisites.sh structure (D-13)
set -e
PKGS="mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-pip \
mingw-w64-ucrt-x86_64-python-setuptools mingw-w64-ucrt-x86_64-python-cython \
mingw-w64-ucrt-x86_64-toolchain mingw-w64-ucrt-x86_64-llvm-tools \
mingw-w64-ucrt-x86_64-zlib mingw-w64-ucrt-x86_64-bzip2 mingw-w64-ucrt-x86_64-xz"
[ "${MSYSTEM:-}" = "UCRT64" ] || { echo "run inside the UCRT64 shell"; exit 1; }
pacman -Syu --needed $PKGS
command -v llvm-nm >/dev/null || { echo "llvm-nm missing after install"; exit 1; }
python -m venv --system-site-packages _venv
. _venv/bin/activate
python -m pip install -e . --no-build-isolation
python devtools/smoke_test.py
```

### Canonical documented flow (INSTALL Windows section; D-14/D-15)
```
1. (manual) Install MSYS2: https://www.msys2.org/  — open the "UCRT64" shell.
2. (scripted) sh devtools/msys2-bootstrap.sh
   Builds pysam into _venv via: pip install -e . --no-build-isolation
   and runs devtools/smoke_test.py as the acceptance gate.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `win32/` shim dir (2013) intended for MSVC-era builds | Only getopt.c/h survive; UCRT64 provides real unistd.h/stdint.h | D-10 (this phase) | random/srandom gap moves to define_macros; include-shadowing risk eliminated |
| setuptools needing `SETUPTOOLS_USE_DISTUTILS=stdlib` on MSYS2 | setuptools >= 70.2.0 builds C extensions natively in MSYS2 | 2024-07-01 [CITED: msys2.org/docs/python changelog] | pacman python-setuptools works out of the box; the old workaround now BREAKS (stdlib distutils removed with Python 3.12, 2024-11-09) |
| MSYS2 python without limited-API libpython | libpython3.dll (limited ABI) shipped | 2023-08-22 [CITED: msys2.org/docs/python] | not needed by this phase, but confirms the fork is maintained |
| pysam symbol check POSIX-only, skipped elsewhere | llvm-nm-based, fail-hard on Windows | this phase (BUILD-03) | duplicates now caught where they actually crash (runtime) |

**Deprecated/outdated:**
- `SETUPTOOLS_USE_DISTUTILS=stdlib` workaround: removed upstream; do not adopt any recipe suggesting it.
- `win32/unistd.h` mappings: superseded by UCRT64 headers except random/srandom (macro fix).
- Assuming `mingw-w64-ucrt-x86_64-llvm` provides llvm-nm: it does not — use `-llvm-tools` [CITED: packages.msys2.org].

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | mingw-w64 UCRT64 does not declare POSIX `random`/`srandom` (the define_macros fix is required) | Pitfall 5, Pattern 5 | If wrong: harmless redundant macros (token-level rewrite; low collision risk since grep shows no other `random` token in compiled sources) — verify at first compile |
| A2 | llvm-nm reads PE/COFF `.pyd` binaries for the symbol check | Pattern 3 | If wrong: switch to toolchain GNU `nm` (also PE-capable) — same flag surface; BUILD-03 satisfied either way; planner checkpoint on first run |
| A3 | `-Wl,--out-implib` produces a usable import library named `lib<stem>.dll.a` that GNU ld resolves via `-l<stem>` | Pattern 4, Pitfall 6 | Core linking mechanism; if naming is off, first downstream link fails loudly and the fix is a filename adjustment — checkpoint at first build |
| A4 | Python 3.8+ `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR` lets sibling `.pyd`s resolve their cross-extension dependencies at import time | Pattern 4 | If wrong: smoke test fails at `import pysam` with DLL-not-found; fallback is preloading or copied implib DLLs — would need a design tweak |
| A5 | pacman python is 3.12.x+ today (snapshot page showed 3.11.9-1; changelog documents the 3.12 migration) | Standard Stack | None — code derives everything from `EXT_SUFFIX`; bootstrap prints actual version (D-02) |
| A6 | UCRT64 unistd.h/stdio.h provide isatty/fileno/access/ftruncate/ssize_t covering all dropped-shim uses | Pattern 5 | If a symbol is missing at first compile, add a targeted macro — same mechanism as A1 |
| A7 | UCRT64 mingw-w64 may provide its own getopt.h/getopt_long (D-10's "no getopt_long" premise possibly outdated) | Pattern 6, Pitfall 12 | None — vendored getopt.c is harmless-if-redundant; verify opportunistically, keep per D-10 |
| A8 | plain `pip install -e .` (with PEP 517 isolation) may not fetch mingw-compatible build deps from PyPI; `--no-build-isolation` with pacman deps is the safe canonical form | Standard Stack, Pattern (bootstrap) | If plain form works, the flag is merely redundant; docs use the flagged form regardless |

## Open Questions

1. **Does `sh configure` complete cleanly under UCRT64 with only `--disable-ref-cache --disable-libcurl`?**
   - What we know: htslib INSTALL documents the MSYS2 path and `make lib-static`; a prebuilt UCRT64 htslib package exists, proving feasibility [CITED: htslib INSTALL; packages.msys2.org htslib]; pysam already passes both flags.
   - What's unclear: exact config.h feature set produced (e.g. HAVE_LIBDEFLATE if not installed) and whether any htslib version-specific Windows patch is needed.
   - Recommendation: first-build task with log capture; the empty-config.h fallback (setup.py:534-541) exists but must NOT be hit in Phase 1.
2. **Exact implib naming/link order on first build (A3/A4).**
   - Recommendation: planner sequences libchtslib → one downstream module → smoke as the earliest integration checkpoint.
3. **Whether llvm-nm or toolchain GNU nm ends up as the BUILD-03 tool.**
   - What we know: requirement names llvm-nm; binutils nm is a fallback with identical `-g -P` surface.
   - Recommendation: llvm-nm primary (per BUILD-03), A2 checkpoint decides.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| MSYS2 (UCRT64) | entire phase | ✗ (by design — D-15 manual install) | — | none; Wave 0 installs it |
| pacman packages (python/toolchain/llvm-tools/libs) | build | ✗ until bootstrap | — | bootstrap script (D-13) |
| Git + Git Bash | workflow | ✓ | 2.x | — |
| git `core.autocrlf` | working-tree integrity | ⚠ set to `true` (mangled tree) | — | `.gitattributes` + renormalize (Pitfall 1) |
| python.org CPython | NOT the build target (D-01/D-05) | ✓ 3.13.5 present | 3.13.5 | deliberately unused for builds |
| gcc / make / nm in Git Bash | not required there | ✗ | — | build runs inside UCRT64 shell |
| Node (GSD tooling) | plan/commit tooling | ✓ | — | — |
| Fork remote `origin` (forrestzhang/pysam) | D-11 CI proof | ✓ configured | — | — |

**Missing dependencies with no fallback:** MSYS2 itself — installed manually in Wave 0 per D-15 (documented link + one GUI run); blocking until done.
**Missing dependencies with fallback:** none beyond the above (llvm-nm has the binutils-nm fallback noted in A2).

## Security Domain

### Applicable ASVS Categories (level 1; security_enforcement enabled)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a — build phase, no user auth surface |
| V3 Session Management | no | n/a |
| V4 Access Control | no | n/a — local dev build; CI uses standard GITHUB_TOKEN scopes (unchanged) |
| V5 Input Validation | yes | subprocess args are repo-controlled; keep list-form for `run_make`/`run_nm_defined_symbols`; document that `HTSLIB_CONFIGURE_OPTIONS` flows into a `shell=True` string (pre-existing, dev-only, documented hazard) |
| V6 Cryptography | no | n/a — no crypto implemented; htslib's own crypto stays disabled (`--disable-libcurl`, no S3/GCS in v1) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Package supply-chain (slopsquatted build deps) | Tampering | pacman GPG-signed repos only; no PyPI binary installs on the build path (`--no-build-isolation` + pacman setuptools/cython) [CITED: MSYS2 package signing model] |
| Shell injection via build env vars into `shell=True` string | Tampering/Elevation (dev machine) | Pre-existing surface (`HTSLIB_CONFIGURE_OPTIONS`); Phase 1 keeps it but the fail-fast gate + bootstrap script narrow who can set it; do not widen (no new shell=True call sites) |
| Compiler/toolchain binary substitution on PATH | Tampering | bootstrap verifies `llvm-nm --version` and UCRT64 membership after install; UCRT64 gate (D-03) anchors the expected environment |
| Corrupted vendored sources (CRLF) | Tampering (accidental) | `.gitattributes` eol rules + renormalization (Pitfall 1) restore byte-fidelity of bundled upstream code |

## Sources

### Primary (HIGH confidence — read/verified this session)
- `setup.py` lines 61-112 (run_configure/run_make/run_make_print_config/run_nm_defined_symbols verbatim), 316-340 (check_ext_symbol_conflicts), 355-366 (skip wrapper), 419-423 region (rpath, per CONCERNS W5), 480-562 (package_list/config_headers/configure attempt/empty fallback), 596-700 (config.py keys, win32 branch, EXT_SUFFIX, prebuild gates), 704-761 (13 module source lists)
- `htslib/thread_pool.c:25,1159,1518` — TEST_MAIN guard around random/srandom
- `bcftools/vcfsom.c:25-30,362,513` — includes unistd.h; random()/srandom() calls; `.pysam.c` twin compiled via glob (setup.py:713-717)
- `win32/` tracked contents (`git ls-files win32/`); `win32/unistd.h` mapping list; working-tree CRLF state (`file`, `od`, `git config core.autocrlf`)
- `.gitattributes` (linguist/export-ignore only — no eol rules); `.github/workflows/ci.yaml:1-80` (push trigger, ubuntu/macos matrix)
- `tests/pysam_data/` composition (ex1.sam.gz, ex1.vcf.gz+.tbi; no plain BAM — 0example file is gzip magic)

### Secondary (MEDIUM confidence — CITED official docs)
- [MSYS2 Python docs](https://www.msys2.org/docs/python/) — cpython-mingw fork, detection snippet, venv-with-bash, setuptools 70.2.0 changelog, PyPI-binary-wheel incompatibility, Python 3.12 migration 2024-11-09
- [MSYS2 package: mingw-w64-ucrt-x86_64-python](https://packages.msys2.org/package/mingw-w64-ucrt-x86_64-python) — version snapshot 3.11.9-1, EXT_SUFFIX `.cp311-mingw_x86_64_ucrt.pyd` from lib-dynload listing, ensurepip bundle, sibling python-{pip,setuptools,cython,wheel,pytest} existence
- [MSYS2 package: mingw-w64-ucrt-x86_64-llvm-tools](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-llvm-tools) — llvm-nm provider, binutils-tools conflict
- [llvm-nm command guide](https://llvm.org/docs/CommandGuide/llvm-nm.html) — `-P`/`--portability` POSIX.2 output format
- [GNU ld manual — Options](https://sourceware.org/binutils/docs/ld/Options.html) and ld WIN32 section — `-l` search order on PE/COFF (`lib<name>.dll.a` → `<name>.dll.a` → `lib<name>.a` → DLL forms), `--out-implib` context
- [htslib INSTALL](https://github.com/samtools/htslib/blob/develop/INSTALL) — MSYS2/Windows section, `make lib-static`, `--disable-libcurl` (auto-disables ref-cache)
- samtools announcement thread (samtools#2064 context) — MSYS2 CI build of htslib/samtools/bcftools feasibility

### Tertiary (LOW confidence — marked for first-build validation)
- GNU ld import-library runtime resolution nuances and `--out-implib` flag spelling via gcc driver (A3) — WebSearch corroboration only
- mingw-w64 native getopt_long availability (A7/A8, A6 header coverage) — training knowledge, verify at compile

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — D-01 target is locked; every package verified on packages.msys2.org; msys2 python behavior from official docs
- Architecture/patterns: HIGH — all seven edit points quoted verbatim from setup.py this session; the one new mechanism (implib) is CITED + checkpointed
- Pitfalls: HIGH for Pitfalls 1-5, 8-11 (verified in-tree or CITED docs); MEDIUM for 6-7, 12 (first-build verification designed in)
- Overall: the phase is plan-ready; every remaining uncertainty has a designated first-build checkpoint, none requires exploratory coding

**Research date:** 2026-09-17
**Valid until:** 2026-10-17 (stable domain; pacman package versions drift but nothing here pins them)
