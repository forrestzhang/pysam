# Phase 1: MinGW-w64 构建系统 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-17
**Phase:** 1-MinGW-w64 构建系统
**Areas discussed:** Target Python runtime, setup.py change style, POSIX regression guard, MSYS2 bootstrap form

---

## Target Python runtime

### Q1: Which CPython should the Phase 1 UCRT64 dev build target?

| Option | Description | Selected |
|--------|-------------|----------|
| MSYS2 python (Recommended) | pacman-installed GCC-built CPython native to UCRT64; setuptools finds gcc, libpython links via dll.a, no import-library glue; fastest to test-green; validates the C/Cython code, not the real-world install | ✓ |
| python.org CPython | MSVC-built CPython users actually have, invoked from UCRT64 shell; most realistic but GCC↔python.org linking is the least-documented glue (STACK MEDIUM), high risk for Phase 1 | |
| Both, staged | MSYS2 python first; python.org-CPython-under-UCRT64 as explicit stretch goal; adds a second validation environment to Phase 1's definition of done | |

**User's choice:** MSYS2 python
**Notes:** —

### Q2: How many Python versions should the Phase 1 dev build validate against?

| Option | Description | Selected |
|--------|-------------|----------|
| Single version (Recommended) | One pacman python (whatever UCRT64 ships); version matrix is CI-03's job in Phase 4 | ✓ |
| Small matrix (2 versions) | Validates Cython-3-generated C across ABI boundaries early; multiplies every debugging session | |

**User's choice:** Single version
**Notes:** —

### Q3: When someone runs the build on Windows but NOT inside a UCRT64 shell, what should happen?

| Option | Description | Selected |
|--------|-------------|----------|
| Strict fail-fast (Recommended) | setup.py detects non-UCRT64 Windows build and stops with one actionable message listing pacman packages; guards against msvcrt-MinGW silent-corruption class | ✓ |
| Best-effort | Attempt anywhere; let compiler/linker errors surface naturally; cryptic deep failures | |

**User's choice:** Strict fail-fast
**Notes:** —

### Q4: What form should the Phase 1 acceptance smoke check take?

| Option | Description | Selected |
|--------|-------------|----------|
| Committed script (Recommended) | devtools/smoke_test.py: import pysam, open a BAM, dispatch one command, nonzero exit on failure; reusable as Phase 4 CI smoke gate | ✓ |
| Manual one-liner | Interactive verification; zero maintenance but nothing reusable and no mechanical re-check | |

**User's choice:** Committed script
**Notes:** —

### Q5: How should the fork treat the GCC ↔ python.org-CPython combination?

| Option | Description | Selected |
|--------|-------------|----------|
| Mark unsupported (Recommended) | One-sentence doc note: unsupported in v1; real-user Python served by Phase 3 MSVC path; prevents gendef/dlltool rabbit hole | ✓ |
| Leave open for v2 | Note as open question next to MGW-01; keeps door open but leaves a tempting rabbit hole visible | |

**User's choice:** Mark unsupported
**Notes:** —

### Q6: Where should the build checkout live during Phase 1 development?

| Option | Description | Selected |
|--------|-------------|----------|
| Windows path (Recommended) | Keep D:\Github\pysam; UCRT64 shell builds via /d/Github/pysam; one checkout/branch, slower drvfs iteration | ✓ |
| MSYS2 home clone | Fastest configure/make on MSYS2-native FS; two checkouts to sync | |
| Decide later | No upfront commitment; leaves environment story ambiguous for docs | |

**User's choice:** Windows path
**Notes:** —

### Q7: How should pysam be installed into the MSYS2 python during development?

| Option | Description | Selected |
|--------|-------------|----------|
| venv (Recommended) | python -m venv in UCRT64 shell, pip install -e . into it; isolates from pacman-managed site-packages | ✓ |
| System/user install | One less step; pip-into-pacman-python is the combination MSYS2 docs warn about | |

**User's choice:** venv
**Notes:** —

---

## setup.py change style

### Q1: What diff philosophy should the Phase 1 Windows build changes follow in setup.py?

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal inline (Recommended) | Small sys.platform/MSYSTEM-gated branches exactly where the POSIX pipeline breaks; smallest upstreamable diff; no restructuring | ✓ |
| Helper module | Extract platform branching into setup_platform.py; cleaner but large moved-code diff, weaker upstreamability | |
| Refactor along the way | Inline branches + opportunistically factor existing darwin/linux branches; improves file but adds regression risk on untestable platforms | |

**User's choice:** Minimal inline
**Notes:** —

### Q2: What should happen to the existing dead Windows branch at setup.py:634?

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite in place (Recommended) | Replace the "untested" win32 branch with the working UCRT64 path at the same insertion point; diff localized where reviewers expect Windows handling | ✓ |
| Delete + fresh block | Pure deletion + new block; reads as a bigger change in review | |
| Keep alongside | Two Windows branches; stale one becomes a trap | |

**User's choice:** Rewrite in place
**Notes:** —

### Q3: Which of the 2013 win32/ shims should the UCRT64 build still use?

| Option | Description | Selected |
|--------|-------------|----------|
| getopt only (Recommended) | Keep win32/getopt.c (no getopt_long in MinGW-w64); drop win32/unistd.h + win32/stdint.h (UCRT64 GCC ships real ones); researcher verifies per-shim | ✓ |
| Keep all three | Zero decisions to revisit; stale unistd.h shadows MinGW-w64's real one, missing isatty/fileno (W7) | |
| Researcher decides | Inventory per-shim during planning; leaves include-path question unanswered in CONTEXT.md | |

**User's choice:** getopt only
**Notes:** —

---

## POSIX regression guard

### Q1: How should Linux/macOS zero-regression be verified during Phase 1 development?

| Option | Description | Selected |
|--------|-------------|----------|
| Fork CI per push (Recommended) | Push win branch to fork after each commit; existing ci.yaml ubuntu+macos jobs run automatically; real compiler + suite, zero new CI code | ✓ |
| Manual review only | Careful reading + platform gates; slips surface much later, entangled | |
| Phase-boundary runs | Trigger only before phase completion; regressions expensive to bisect | |

**User's choice:** Fork CI per push
**Notes:** —

### Q2: Which jobs define "existing Linux/macOS builds and CI stay green" for Phase 1 completion?

| Option | Description | Selected |
|--------|-------------|----------|
| ubuntu+macos green (Recommended) | ubuntu and macos jobs green on the phase's final commit; FreeBSD/NetBSD VM jobs advisory | ✓ |
| All jobs green | Includes cross-platform VM jobs; ties completion to third-party runner stability | |

**User's choice:** ubuntu+macos green
**Notes:** —

---

## MSYS2 bootstrap form

### Q1: What form should the MSYS2 UCRT64 environment bootstrap take?

| Option | Description | Selected |
|--------|-------------|----------|
| Script + docs (Recommended) | Committed UCRT64 bootstrap script (pacman list + venv) + INSTALL Windows section; script doubles as fail-fast message content | ✓ |
| Docs only | INSTALL lists packages by hand; every setup is manual copy-paste | |
| Fully automated | winget/choco + silent MSYS2 install; outlives usefulness for a set-up-once dev environment | |

**User's choice:** Script + docs
**Notes:** —

### Q2: Which command is the canonical documented "one-step build" for Phase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| pip install -e . (Recommended) | Exercises PEP 517 path end to end; matches modern dev workflow and future CI | ✓ |
| setup.py direct | Most direct, fewest moving parts; deprecated entry point, skips pyproject layer | |
| Both documented | Primary + troubleshooting fallback; dilutes the one-step claim | |

**User's choice:** pip install -e .
**Notes:** —

### Q3: Where is the line between manual setup and the bootstrap script?

| Option | Description | Selected |
|--------|-------------|----------|
| Manual + script (Recommended) | MSYS2 itself installed manually (documented link); script owns pacman packages, venv, build deps | ✓ |
| Script installs MSYS2 too | Fewer manual steps; brittle across MSYS2 releases | |

**User's choice:** Manual + script
**Notes:** —

---

## Claude's Discretion

- Exact pacman package list contents (names/versions) — researcher/planner
- Smoke script location and internal structure (`devtools/smoke_test.py` suggested, not mandated)
- Precise UCRT64 detection mechanism (MSYSTEM env var vs compiler probe vs both)

## Deferred Ideas

None — discussion stayed within phase scope.
