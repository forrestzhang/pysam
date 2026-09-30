---
phase: 01-mingw-w64
plan: 03
subsystem: build-system
tags: [windows, msys2, ucrt64, first-build, symbol-gate, llvm-nm, import-library, ci]
requires:
  - {phase: 01-01, provides: "bootstrap script (PKGS contract) + smoke gate + eol=lf working tree"}
  - {phase: 01-02, provides: "setup.py win32 pipeline (fail-fast gate, sh configure, llvm-nm gate, implib link flag)"}
provides:
  - "Empirical end-to-end proof: one command (sh devtools/msys2-bootstrap.sh) builds all 13 Cython extensions + bundled htslib/samtools/bcftools from a clean slate on real UCRT64 hardware (ROADMAP criteria 1-2)"
  - "BUILD-03 proven, not just implemented: gate ran on win32, cannot silently skip, teeth=904 / honesty=0 evidenced via committed devtools/probe_symbol_check.py exercising setup.py's real llvm-nm parser"
  - "D-16 getopt isolation model landed and evidenced (libchtslib export surface excludes getopt family; closed 7-symbol win32 gate exemption; 13 modules / 1624 defined symbols / 0 duplicates / 0 exemption hits)"
  - "Research checkpoints A1/A3/OQ1/A4 resolved positive; A2 resolved WITH RESERVATION (gate reads .dll.a import libraries because distutils -s strips .pyd)"
  - "POSIX zero-regression closed: fork CI run 35353108072 green 19/19 on phase-final SHA 0f326879 (17/17 blocking ubuntu/macos jobs success, D-12)"
affects: ["phase-02-portability", "phase-03-msvc", "phase-04-ci-wheels"]
actuals:
  tokens: 10700
  tasks: 3
  commits: 12
plan_head_before: 6164f6fbb10b6473724ad757d4c4eb20881c1cc5
tech-stack:
  added:
    - "MSYS2 UCRT64 toolchain proven on hardware: GCC 14+/C23, mingw32-make, llvm-nm reading PE/COFF import-library archives"
    - "devtools/probe_symbol_check.py — teeth probe that ast-extracts and execs setup.py's real _nm_command + run_nm_defined_symbols"
  patterns:
    - "Symbol gating on stripped-module platforms reads the -Wl,--out-implib import library, not the final image (distutils links with -s)"
    - "Cross-module C symbol isolation via --exclude-symbols + per-module private static copies (D-16), with a CLOSED platform exemption list"
    - "CI verdict read via unauthenticated public REST API when gh auth is unavailable (ubuntu/macos blocking, BSD advisory, D-12)"
key-files:
  created:
    - "devtools/probe_symbol_check.py"
    - ".planning/phases/01-mingw-w64/01-03-SUMMARY.md"
    - ".planning/phases/01-mingw-w64/01-03-USER-SETUP.md"
  modified:
    - "setup.py"
    - "devtools/smoke_test.py"
    - "devtools/msys2-bootstrap.sh"
    - "win32/getopt.c"
    - "win32/getopt.h"
    - ".planning/PROJECT.md"
    - ".planning/phases/01-mingw-w64/01-CONTEXT.md"
key-decisions:
  - "D-16 (user-adjudicated option-1): getopt family removed from libchtslib's export surface via --exclude-symbols; each tool extension keeps its private mingwex static copy; BUILD-03 gate exempts exactly 7 symbols {getopt, getopt_long, getopt_long_only, optarg, optind, opterr, optopt} on win32 only — list is CLOSED"
  - "Gate/probe evidence channel on win32 = the .dll.a import libraries: distutils links with -s (strip) so .pyd has no readable symbol table; user did not authorize removing -s (A2 reservation)"
  - "PKGS mirror sync: python-cython renamed to cython (upstream MSYS2 package rename, D-13)"
  - "configure spawned via [\"sh\",\"-c\",...] directly + MAKE=mingw32-make exported: cmd.exe AutoRun/conda_hook poisons every shell=True subprocess on this machine; UCRT64's make package only ships mingw32-make.exe"
  - "Task 1 precondition (MSYS2 install) resolved via user-authorized automated install at C:\\msys64 (official installer, --noconfirm first-update)"
patterns-established:
  - "First-build checkpoint discipline: every research assumption (A1-A4, OQ1) adjudicated against captured evidence in the bootstrap log and on-disk artifacts, never assumed"
  - "Fix-forward D-08 style inside the build loop: one surgical win32-gated lesson per commit, message = what the first build taught"
requirements-completed: [BUILD-01, BUILD-03]
coverage:
  - id: D1
    description: "One-command clean-slate UCRT64 build: bootstrap script runs pacman (idempotent) -> venv -> full 13-extension build -> smoke gate, end to end (BUILD-01, ROADMAP criterion 1-2)"
    requirement: BUILD-01
    verification:
      - {kind: command, ref: "grep -c 'smoke OK' C:\\msys64\\tmp\\pysam-bootstrap-run.log -> 1 (clean-state acceptance run)", status: pass}
      - {kind: command, ref: "UCRT64 venv python -c 'import pysam; print(pysam.__version__, pysam.config.HTSLIB)' -> '0.24.1 builtin' (re-run 2026-09-30)", status: pass}
      - {kind: command, ref: "ls pysam/*.pyd | wc -l -> 13; ls pysam/*.dll.a | wc -l -> 13; libchtslib.cp314-mingw_x86_64_ucrt_gnu.dll.a present (re-counted 2026-09-30)", status: pass}
      - {kind: command, ref: "htslib/config.h is a real 6999-byte configure product; empty-config fallback (setup.py:535-541) never hit (OQ1)", status: pass}
    human_judgment: false
  - id: D2
    description: "BUILD-03 proven on win32: symbol gate ran with the ported tool, did not skip, and detects duplicates (ROADMAP criterion 3)"
    requirement: BUILD-03
    verification:
      - {kind: command, ref: "grep -c 'skipping symbol collision check' bootstrap-run.log -> 0 (no silent skip on any execution path)", status: pass}
      - {kind: command, ref: "direct llvm-nm -g -P on built .dll.a set -> 930 non-empty POSIX.2 lines (A2)", status: pass}
      - {kind: command, ref: "python devtools/probe_symbol_check.py (re-run 2026-09-30) -> exit 0, resolved nm command 'llvm-nm -g -P', built modules 13, teeth=904, honesty=0", status: pass}
    human_judgment: false
  - id: D3
    description: "D-16 getopt isolation model: libchtslib export surface excludes getopt family, per-module private copies, closed 7-symbol win32 exemption in the gate"
    requirement: BUILD-03
    verification:
      - {kind: command, ref: "setup.py:142-143 closed exemption set {getopt, getopt_long, getopt_long_only, optarg, optind, opterr, optopt} (re-inspected 2026-09-30)", status: pass}
      - {kind: command, ref: "probe honesty path: 13 modules / 1624 defined symbols / 0 duplicates / 0 exemption hits ('raw before D-14 exemption: 0')", status: pass}
    human_judgment: false
  - id: D4
    description: "POSIX zero-regression: fork CI green on the phase-final source SHA 0f326879 (D-12, ROADMAP criterion 4)"
    verification:
      - {kind: command, ref: "GET api.github.com/repos/forrestzhang/pysam/actions/runs/35353108072 -> head_sha 0f326879fb35e38728b71d506ec93ced52dbb416, status completed, conclusion success (re-fetched first-hand 2026-09-30)", status: pass}
      - {kind: command, ref: "GET .../runs/35353108072/jobs -> 19/19 success; blocking set (17 ubuntu|macos jobs incl. direct 3.9-3.15-dev, conda 3.13, sdist) all success; BSD VM jobs (netbsd 11.0, freebsd 15.1) advisory, also success", status: pass}
    human_judgment: false
  - id: D5
    description: "Distribution prohibition upheld: no wheel, sdist, or any distributable artifact built from the UCRT64 path (T-01-10)"
    verification:
      - {kind: command, ref: "ls dist/ -> absent; no *.whl or *.tar.gz anywhere in the tree (checked 2026-09-30)", status: pass}
    human_judgment: false
duration: 11d 18h wall (approx 6h active across two sessions; 11.5d paused at gh-auth gate)
completed: 2026-09-30
status: complete
---

# Phase 1 Plan 03: UCRT64 End-to-End Proof Summary

**UCRT64 end-to-end build proven on real hardware: one bootstrap command compiles all 13 extensions plus bundled htslib/samtools/bcftools from a clean slate, BUILD-03 evidenced with teeth (teeth=904 / honesty=0 via llvm-nm on import libraries), D-16 getopt isolation landed, and fork CI green 19/19 on the phase-final SHA — Phase 01's four empirical ROADMAP criteria all closed.**

## Performance

- **Duration:** 11d 18h wall clock (2026-09-18 ~08:30Z → 2026-09-30 ~02:30Z), of which ~6h active execution across two sessions and 11.5 days a deliberate pause at the gh-auth gate (see Authentication Gates)
- **Started:** 2026-09-18 (session 1; first production commit 4c7f83d4 at 10:48:07Z)
- **Paused:** 2026-09-18T14:20:41Z (checkpoint:human-action, gh CLI unauthenticated) — wip commit a8a417b9 preserved the pause state
- **Resumed/Completed:** 2026-09-30 (continuation executor; CI verified via the orchestrator-authorized public REST API channel)
- **Tasks:** 3/3 (all auto; Task 3 finished by continuation close-out)
- **Files:** 8 production (1 added, 7 modified; 319 insertions / 36 deletions vs plan head 6164f6fb) + close-out docs/hygiene (SUMMARY, USER-SETUP, STATE, ROADMAP, REQUIREMENTS, .gitignore, 2 pause-artifact deletions)

## Accomplishments

- **One-command clean-slate build (criterion 1):** `sh devtools/msys2-bootstrap.sh` executed end-to-end from a cleaned tree (git-cleaned bundled trees, deleted config.py/*.pyd/*.dll.a/egg-info) — pacman idempotent, `_venv` created (CPython 3.14.7), `pip install -e . --no-build-isolation` compiled all 13 extensions + bundled htslib/htscodecs/samtools/bcftools, smoke gate passed: `smoke OK` in the captured log (`C:\msys64\tmp\pysam-bootstrap-run.log`).
- **Working pysam from Python (criterion 2):** `import pysam` prints `0.24.1 builtin`; generated BAM opens with positive alignment count via samtools dispatch; bcftools dispatch returns data through `_pysam_dispatch` (D-04).
- **BUILD-03 triple proof (criterion 3):** (1) no-skip grep over the always-captured bootstrap log = 0 hits; (2) direct `llvm-nm -g -P` on the built import libraries emits 930 POSIX.2 lines; (3) committed `devtools/probe_symbol_check.py` — which ast-extracts and execs setup.py's real `_nm_command` + `run_nm_defined_symbols` — asserts the resolved tool is the llvm-nm triple, flags teeth=904 duplicates when one binary is judged as two extensions, and reports honesty=0 duplicates across the 13 real binaries.
- **D-16 landed and evidenced:** getopt family excluded from libchtslib's export surface (`--exclude-symbols`), private mingwex static copies per tool module, closed 7-symbol win32 gate exemption — 13 modules / 1624 defined symbols / 0 duplicates / 0 exemption hits.
- **POSIX zero-regression (criterion 4):** fork CI run 35353108072 on the phase-final SHA 0f326879 — conclusion success, 19/19 jobs green, every blocking ubuntu/macos job (direct 3.9/3.10/3.11/3.12/3.13/3.15-dev, conda 3.13, sdist) success; BSD VM jobs advisory and green.

## Research Checkpoint Adjudications (first-build assumptions)

| Checkpoint | Verdict | Evidence |
|------------|---------|----------|
| **A1** random/srand macros | **Resolved: REQUIRED** | With `('random','rand')` / `('srandom','srand')` define_macros the full tree (incl. bcftools/vcfsom.c:362/513) compiles clean under GCC 14+/C23; without them vcfsom fails to link |
| **A3** implib naming | **Resolved: PRODUCED** | All 13 import libraries emitted, e.g. `pysam/libchtslib.cp314-mingw_x86_64_ucrt_gnu.dll.a` — lib-prefixed stub names resolving the 12 downstream `-l` flags. First attempt doubled the prefix (`liblib*`) because the EXT_SUFFIX stem already starts with "lib"; fixed in a50e71a4 |
| **OQ1** configure really runs | **Resolved: YES** | `sh configure` executed via `["sh","-c",...]` direct spawn under `--disable-ref-cache --disable-libcurl`; `htslib/config.h` is a real 6999-byte configure product; `HTSLIB=builtin`; the empty-config fallback (setup.py:535-541) was never hit |
| **A4** sibling DLL resolution | **Resolved: YES** | `import pysam` loads libchtslib.pyd and the 12 downstream modules resolve sibling DLLs via the loader's own-directory search — no PATH dependency; smoke dispatch proves the loaded set is the just-built one |
| **A2** llvm-nm on PE | **Resolved: YES, WITH RESERVATION** | llvm-nm parses the PE/COFF import-library archives (930 lines on the .dll.a set). Reservation: distutils links extensions with `-s` (strip), so `.pyd` files carry no readable symbol table — the gate and probe read the `.dll.a` import libraries instead. The user explicitly did NOT authorize removing `-s`; the import-library channel is the standing evidence path for win32 gating (Phase 2/3 tooling must respect this) |

## Task Commits

Production commits (Task 1: 9, Task 2: 2), each an atomic first-build lesson:

| # | Task | Commit | Message (what the first build taught) |
|---|------|--------|----------------------------------------|
| 1 | 1 | `4c7f83d4` | build(01): rename python-cython to cython in PKGS list (D-13 mirror sync) |
| 2 | 1 | `87437211` | build(01): spawn configure via sh directly, export MAKE=mingw32-make (cmd AutoRun poisoning) |
| 3 | 1 | `61b2d26a` | build(01): make win32/getopt shims compile under C23 (GCC 14+) — explicit prototypes |
| 4 | 1 | `7e4e676f` | build(01): emit import libraries for every win32 extension (--out-implib) |
| 5 | 1 | `a50e71a4` | build(01): fix doubled lib prefix in implib stub name (liblib* bug) |
| 6 | 1 | `055a9ddb` | build(01): export all symbols from win32 extension modules (def file only exports PyInit_*) |
| 7 | 1 | `461a5bb5` | build(01): add getopt_long/getopt_long_only to win32 getopt shim |
| 8 | 1 | `c7bd2adf` | build(01): exempt getopt family from cross-module gate on win32 (D-16) |
| 9 | 1 | `5a8e2fee` | build(01): fix smoke gate for the real UCRT64 dispatch behavior |
| 10 | 2 | `11d84800` | build(01): gate the win32 export surface via import libraries (strip workaround) |
| 11 | 2 | `0f326879` | build(01): add symbol-conflict teeth probe — phase-final source SHA |

Task 3 pushed 0f326879 to `origin/win` (phase-final source commit) and closed on green CI; its close-out artifacts are the docs commits that follow this SUMMARY. Pause bookkeeping: `a8a417b9` (wip: pause artifacts, kept in history, artifacts removed at close-out).

**Plan metadata:** this SUMMARY + state/docs updates + pause-artifact removal + .gitignore hygiene, committed as `docs(01-03)` after this file (see git log).

## CI Evidence (D-12)

- **Run:** 35353108072 (workflow "CI", run #3) on head_sha `0f326879fb35e38728b71d506ec93ced52dbb416`, completed 2026-09-18T14:06:00Z, **conclusion: success**.
- **Jobs:** 19/19 green. Blocking set (judgment rule: ubuntu|macos only): 17/17 success — direct builds 3.9/3.10/3.11/3.12/3.13/3.15-dev on ubuntu and macos, conda 3.13, sdist builds. Advisory (ignored by the rule, also green): netbsd 11.0 (3.14), freebsd 15.1 (3.12).
- **Evidence channel:** unauthenticated public REST API (`api.github.com/repos/forrestzhang/pysam/actions/runs/...`) — the same endpoint `gh run view` reads; re-fetched first-hand by the continuation executor on 2026-09-30 (run-level + per-job conclusions).
- Closing docs-only commits pushed after this SUMMARY touch only `.planning/**` and `.gitignore`; D-12's basis is the source-final SHA 0f326879. The docs-head CI run verdict is recorded in the plan completion report.

## Decisions Made

- **D-16 (user-adjudicated, option-1):** getopt family leaves libchtslib's export surface (`--exclude-symbols`); tool extensions hold private mingwex static copies; gate exemption closed at 7 symbols, win32-only. Rationale: getopt lives in static libmingwex.a and PE data symbols (optarg/optind) cannot resolve through import libraries at archive-scan time — any shared-export model double-defines. Recorded in PROJECT.md Key Decisions.
- **Evidence channel for a stripped-module platform:** gate/probe read `.dll.a` import libraries (distutils `-s`); removing `-s` was not authorized.
- **gh-auth substitute:** public REST API as the authorized CI evidence channel (standing pattern from plan 01-02, re-authorized by the orchestrator for this continuation).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] MSYS2 package rename broke the bootstrap PKGS list**
- **Found during:** Task 1 (first bootstrap run)
- **Issue:** `python-cython` no longer exists in the UCRT64 repo (upstream renamed to `cython`)
- **Fix:** PKGS list updated to `cython`; setup.py fail-fast message mirrors it (D-13 single-source contract preserved)
- **Files modified:** devtools/msys2-bootstrap.sh, setup.py
- **Verification:** bootstrap ran to completion; fixed-string grep of the 9-package list still == 1
- **Committed in:** 4c7f83d4

**2. [Rule 3 - Blocking] cmd.exe AutoRun/conda_hook poisons every shell=True subprocess**
- **Found during:** Task 1 (configure stage)
- **Issue:** configure invoked through cmd failed; UCRT64 make package ships only mingw32-make.exe
- **Fix:** configure spawned via `["sh","-c",...]` directly; bootstrap exports `MAKE=mingw32-make`
- **Files modified:** setup.py, devtools/msys2-bootstrap.sh
- **Verification:** htslib/config.h produced by a real configure run (OQ1)
- **Committed in:** 87437211

**3. [Rule 1 - Bug] C23 hard errors in win32 getopt shims**
- **Found during:** Task 1 (first compile of win32/getopt.c)
- **Issue:** GCC 14+ defaults to C23; K&R prototype-less declarations and implicit function declarations are hard errors
- **Fix:** explicit prototypes throughout the shim; getopt_long/getopt_long_only added (needed by samtools/bcftools mains)
- **Files modified:** win32/getopt.c, win32/getopt.h
- **Verification:** full clean compile
- **Committed in:** 61b2d26a, 461a5bb5

**4. [Rule 2 - Missing critical] distutils def-file exports only PyInit_\***
- **Found during:** Task 1 (link stage)
- **Issue:** downstream `-lchtslib`-style flags found no symbols — def-file linking hides everything except the module init
- **Fix:** `--export-all-symbols` on win32 extensions + `-Wl,--out-implib,pysam/lib<stem>.dll.a` per extension; corrected the doubled `liblib*` prefix (EXT_SUFFIX stem already begins with "lib")
- **Files modified:** setup.py
- **Verification:** 13 import libraries on disk; downstream links resolve; probe honesty=0
- **Committed in:** 7e4e676f, a50e71a4, 055a9ddb

**5. [Rule 1 - Bug] smoke gate assumptions vs real UCRT64 dispatch behavior**
- **Found during:** Task 2 (first smoke run)
- **Issue:** smoke steps asserted dispatch behaviors that differ on the real build
- **Fix:** gate aligned with actual `_pysam_dispatch` behavior on win32
- **Files modified:** devtools/smoke_test.py
- **Verification:** smoke exits 0 printing `smoke OK`; same result inside the clean-state bootstrap run
- **Committed in:** 5a8e2fee

**6. [Rule 1 - Design adjustment] gate/probe read .dll.a because distutils strips .pyd**
- **Found during:** Task 2 (BUILD-03 evidence)
- **Issue:** `.pyd` files have no readable symbol table (link flag `-s`); the plan's "built binaries" evidence channel seemed blocked
- **Fix:** gate dispatch and probe target the per-extension import libraries (llvm-nm parses PE archives — A2 verified); `-s` removal not pursued (not authorized)
- **Files modified:** setup.py, devtools/probe_symbol_check.py
- **Verification:** teeth=904 / honesty=0 / resolved tool = llvm-nm triple
- **Committed in:** 11d84800, 0f326879

### Architectural (user decision)

**7. [Rule 4 - Architectural] D-16 getopt export model**
- **Found during:** Task 1 (cross-module symbol conflicts on first full link)
- **Issue:** D-10's premise (win32/getopt.c single copy shareable) was falsified — PE data symbols cannot resolve through import libraries at archive-scan time; every shared-export variant double-defines getopt
- **Fix (user adjudicated option-1 at a blocking checkpoint):** `--exclude-symbols` on libchtslib + private copies per tool module + closed 7-symbol win32 gate exemption
- **Files modified:** setup.py, win32/getopt.c, win32/getopt.h, .planning/PROJECT.md, 01-CONTEXT.md
- **Verification:** 13 modules / 1624 symbols / 0 duplicates / 0 exemption hits; CI green
- **Committed in:** c7bd2adf (+ shim prep in 461a5bb5)

### Execution-history deviation (pause/resume)

**8. Task 3 step 3 paused 11.5 days at a gh-auth gate.** The plan prescribed `gh run watch/view`; gh CLI was unauthenticated, so the original executor correctly returned a `checkpoint:human-action` (never skipping CI verification) and committed pause artifacts (a8a417b9). The orchestrator later authorized the public REST API as the equivalent evidence channel and dispatched this continuation executor, which re-fetched run-level and per-job conclusions first-hand (results above) and completed the close-out without a rebuild.

---

**Total deviations:** 8 (6 auto-fixed: 3x Rule 1, 1x Rule 2, 2x Rule 3; 1 Rule 4 user-adjudicated; 1 pause/resume history). **Impact:** all resolved within the plan's fix-forward budget (no stage exceeded two failed rebuild attempts); final state is the clean-slate acceptance build with every criterion evidenced.

## Authentication Gates

- **gh CLI unauthenticated (Task 3 step 3):** original executor surfaced `checkpoint:human-action` per protocol; run 35353108072 completed remotely during the pause. Resumed 2026-09-30: the orchestrator authorized the unauthenticated public REST API (the same endpoint `gh run view` reads) as the evidence channel — first-hand run-level + per-job conclusions fetched, no human step required. `gh auth login` remains available for future phases but is no longer a blocker for CI verification.

## Issues Encountered

- **MSYS2 install precondition (Task 1):** machine had no MSYS2 (precondition unmet). Surfaced as blocking-human; the user authorized automated install (official installer, default `C:\msys64`, `--noconfirm` first-update). Installed and verified by the clean-state bootstrap run. STATE.md's stale blocker entry removed at close-out.
- **12-day wall-clock gap** between execution sessions (process pause, not technical): all remote state (origin/win, CI) persisted; disk artifacts re-verified at resume before any close-out action; no rebuild performed.

## User Setup Required

MSYS2 UCRT64 — **already satisfied** (installed at `C:\msys64`; verified by the clean-state bootstrap run). Details and evidence: `01-03-USER-SETUP.md`. No other external configuration required.

## Known Stubs

None. No stub, placeholder, or unwired data path was introduced by this plan.

## Next Phase Readiness

- Phase 01's four empirical ROADMAP criteria are closed on captured evidence; phase close-out chain (post-merge gate, code review, verify_phase_goal, roadmap phase.complete) is the orchestrator's next step.
- Phase 02 (portability hardening + tests-green) starts from a proven baseline: dev build, smoke gate, symbol gate with teeth, and POSIX CI are all live.
- Standing constraints carried forward: win32 symbol-gate evidence reads `.dll.a` (A2 reservation); D-16 exemption list CLOSED at 7 symbols; UCRT64 toolchain quirks (C23 prototypes mandatory, `mingw32-make`, cmd AutoRun poisoning) documented in the bootstrap script's troubleshooting section.

## Self-Check: PASSED

- Files: `devtools/probe_symbol_check.py` (committed, 0f326879), `01-03-SUMMARY.md`, `01-03-USER-SETUP.md` present in `.planning/phases/01-mingw-w64/`.
- Commits: 4c7f83d4, 87437211, 61b2d26a, 7e4e676f, a50e71a4, 055a9ddb, 461a5bb5, c7bd2adf, 5a8e2fee, 11d84800, 0f326879, a8a417b9 all found in `git log`.
- `git rev-list --count 6164f6fb..HEAD` = 12 matching frontmatter `commits: 12` (11 production + 1 pause-wip; close-out docs commits follow this file by design).
- origin/win == 0f326879 (phase-final source SHA); CI on it: success, 19/19.

---
*Phase: 01-mingw-w64*
*Completed: 2026-09-30*
