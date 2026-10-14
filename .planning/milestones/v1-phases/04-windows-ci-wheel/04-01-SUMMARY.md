---
phase: 04-windows-ci-wheel
plan: 01
subsystem: infra
tags: [github-actions, windows-ci, msvc, llvm-nm, pytest, setuptools]

requires:
  - phase: 03-msvc
    provides: MSVC build arm in setup.py (pre-baked config.h.msvc, /DEF exports, BUILD-03 symbol gate via llvm-nm)
provides:
  - Additive `windows` job in ci.yaml building pysam via the MSVC arm on windows-latest and running the full pytest suite across Python 3.10-3.15
  - SHA-pinned per-cell pytest pass/skip counts as the CI-side baseline input for 04-CI-VALIDATION.md (plan 04-03)
affects: [04-02 (win-wheels workflow gated on CI-01 green), 04-03 (CI matrix validation record)]

actuals:
  tokens: 3100
  tasks: 2
  commits: 4

tech-stack:
  added: [msys2/setup-msys2@v2 (release:false, mingw-w64-ucrt-x86_64-llvm-tools)]
  patterns:
    - "Additive standalone windows job with job-level shell: bash default (never insert into the direct os-matrix)"
    - "Git Bash on runners cannot glob-expand backslash-form $GITHUB_WORKSPACE - cygpath -m converts before globbing"
    - "python.org 3.10/3.11 hostpythons bundle setuptools 65.5.0; unpinned pip install no-ops and that generation detaches process stdout - windows CI cells need pip install --upgrade"

key-files:
  created: []
  modified: [.github/workflows/ci.yaml]

key-decisions:
  - "Windows job test step uses cygpath -m on $GITHUB_WORKSPACE before the build/lib.* glob - Git Bash does not expand globs against backslash-form Windows paths"
  - "Windows job pip line uses --upgrade: bundled setuptools 65.5.0 (python.org 3.10/3.11) detaches the process stdout stream during the MSVC build and kills pytest at collection; 3.12+ cells already resolve a current setuptools"
  - "3.11 cell's extra skip (testIteratorOutOfScope) is upstream-owned test hygiene (skipif on CPython 3.11), not a runner anomaly"

requirements-completed: [CI-01]

coverage:
  - id: D1
    description: "Additive windows-latest CI job: MSVC-arm build with live BUILD-03 symbol gate plus full pytest suite, green across Python 3.10-3.15 on every push"
    requirement: CI-01
    verification:
      - kind: integration
        ref: "gh run watch 38296297134 (SHA 207b6901): windows (3.10..3.15) all success"
        status: pass
    human_judgment: false
  - id: D2
    description: "Zero-regression: all 19 pre-existing ci.yaml jobs green in the same run, diff vs phase base 2ea68a19 is pure addition (0 deleted lines), no fail-open constructs"
    requirement: CI-01
    verification:
      - kind: integration
        ref: "gh run view 38296297134 --json jobs: non_success_count=0; git diff 2ea68a19..HEAD ci.yaml: deleted_lines=0; grep continue-on-error: 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Six per-cell pytest pass/skip counts captured from run logs as the CI-side baseline for 04-CI-VALIDATION.md"
    requirement: CI-01
    verification:
      - kind: other
        ref: "run 38296297134 job logs, pytest summary lines per windows cell (see table below)"
        status: pass
    human_judgment: false

duration: 56 min
completed: 2026-10-12
status: complete
---

# Phase 4 Plan 01: Windows CI job (CI-01) Summary

**Additive windows-latest CI job building pysam through the Phase-3 MSVC arm (llvm-nm symbol gate live) and passing the full pytest suite on Python 3.10-3.15, with all 19 pre-existing jobs green in the same runs**

## Performance

- **Duration:** 56 min
- **Started:** 2026-10-12T18:29:53Z
- **Completed:** 2026-10-12T19:26:16Z
- **Tasks:** 2
- **Files modified:** 1 (.github/workflows/ci.yaml, +49/-0 vs phase base)

## Accomplishments

- `windows` job appended to ci.yaml after `conda`: windows-latest, job-level `shell: bash`, setup-msys2 (release:false) provisioning llvm-nm for the BUILD-03 symbol gate, `python setup.py build` auto-selecting the MSVC arm, full pytest via PYTHONPATH to `build/lib.win-amd64-cpython-*`
- Tracer cell (3.13) green end-to-end at ec1dc63a (run [38292937597](https://github.com/forrestzhang/pysam/actions/runs/38292937597)) after one fix: Git Bash cannot glob-expand the backslash form of `$GITHUB_WORKSPACE`; the test step now runs `cygpath -m` first
- Full 3.10-3.15 matrix green at 207b6901 (run [38296297134](https://github.com/forrestzhang/pysam/actions/runs/38296297134)) after one fix: `pip install --upgrade` for prerequisites, because bundled setuptools 65.5.0 (python.org 3.10/3.11) detaches the process stdout stream mid-build
- Zero-regression closed: same-run green for all 19 pre-existing jobs (14 direct, 2 sdist, 2 system, 1 conda), pure-addition diff gate vs phase base 2ea68a19 (deleted_lines=0), fail-open scan clean (0 `continue-on-error`)

## CI Evidence (SHA-pinned)

| Run | SHA | Verdict | Notes |
|-----|-----|---------|-------|
| [38291397314](https://github.com/forrestzhang/pysam/actions/runs/38291397314) | f0ff49a2 | windows (3.13) red | Build + symbol gate green; pytest collection failed - PYTHONPATH glob (fixed in ec1dc63a) |
| [38292937597](https://github.com/forrestzhang/pysam/actions/runs/38292937597) | ec1dc63a | all 20 jobs green | Tracer cell: windows (3.13) 1032 passed, 16 skipped in 18.40s |
| [38294145577](https://github.com/forrestzhang/pysam/actions/runs/38294145577) | 05d50278 | windows (3.11) red | Build green; pytest died at collection - setuptools 65.5.0 stdout detach (fixed in 207b6901); 5 sibling cells cancelled by fail-fast |
| [38296297134](https://github.com/forrestzhang/pysam/actions/runs/38296297134) | 207b6901 | all 25 jobs green | Final: 6/6 windows cells + 19/19 pre-existing jobs |

The pushes carried 16 previously-unpushed Phase-3/Phase-4-planning commits (verified POSIX-inert by the Phase-3 verifier); the ubuntu/macos direct cells green in the same runs close that loop.

## Per-cell pytest counts (from run 38296297134 logs - input for 04-CI-VALIDATION.md)

| Cell | Collected | Passed | Skipped | Duration |
|------|-----------|--------|---------|----------|
| windows (3.10) | 1047 items / 1 skipped | 1032 | 16 | 27.73s |
| windows (3.11) | 1047 items / 1 skipped | 1031 | 17 | 35.26s |
| windows (3.12) | 1047 items / 1 skipped | 1032 | 16 | 35.19s |
| windows (3.13) | 1047 items / 1 skipped | 1032 | 16 | 18.87s |
| windows (3.14) | 1047 items / 1 skipped | 1032 | 16 | 39.08s |
| windows (3.15) | 1047 items / 1 skipped | 1032 | 16 (+2 warnings) | 32.21s |

Cell-only deviation triage (plan requirement): windows (3.11) has one extra skip - `tests/AlignmentFilePileup_test.py::TestPileupObjects::testIteratorOutOfScope`, upstream-owned `@pytest.mark.skipif(sys.version_info[:2] == (3, 11) ...)` ("exercises invalid accesses, which crashes on Python 3.11 and NetBSD"). Benign by design; not a runner anomaly. Skip family across all cells matches the Phase-2/3 environment-shaped set (remote-I/O networking deferred to v2, no-external-samtools usage, stream fds, large-cigar CRAM). CI shows 1032/16 vs the local 1028/15 baseline - the delta reconciles in 04-CI-VALIDATION.md (04-03); likely source is the CI-only mypy presence (typechecking collection) and platform skip-set edges.

## Task Commits

1. **Task 1: Additive `windows` job - cp313 tracer cell green end-to-end** - `f0ff49a2` (feat)
   - fix follow-up: `ec1dc63a` - cygpath -m glob fix for the test step
2. **Task 2: Widen to the 3.10-3.15 matrix - all six cells green + zero-regression close** - `05d50278` (feat)
   - fix follow-up: `207b6901` - pip install --upgrade for the setuptools detach fix

**Plan metadata:** (recorded below)

## Files Created/Modified

- `.github/workflows/ci.yaml` - additive `windows` job (49 inserted lines vs phase base 2ea68a19; 0 deleted): runs-on windows-latest, shell: bash default, 3.10-3.15 matrix, setup-msys2 llvm-tools + GITHUB_PATH append, MSVC build, PYTHONPATH pytest

## Decisions Made

- Test-step glob runs through `cygpath -m "$GITHUB_WORKSPACE"` (Windows-native forward-slash path) - Git Bash does not expand `D:\a\.../build/lib.*`; verified locally in Git Bash and confirmed on the runner
- Prerequisite pip line uses `--upgrade` in the windows job: setup-python's 3.11 hostpython is python.org 3.11.9 bundling setuptools 65.5.0, and `pip install setuptools` without `-U` leaves it in place; that setuptools generation's build stack detaches the process stdout TextIOWrapper (locally reproduced: 3 `--- Logging error ---` / `ValueError: underlying buffer has been detached` with 65.5.0, zero with 84.0.0). 3.12+ hostpythons bundle no setuptools, which is why the 3.13 tracer cell was green from the start
- No setup.py changes were made at any point (Pitfall 9 discipline held): both reds were environment-provisioning facts, proven by local reproduction before touching ci.yaml

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test-step PYTHONPATH glob did not expand on the runner**
- **Found during:** Task 1 (tracer red, run 38291397314)
- **Issue:** `PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*) pytest` - Git Bash does not glob-expand the backslash form of `$GITHUB_WORKSPACE`, so PYTHONPATH received a literal nonexistent path; all 16 test modules failed collection with `ModuleNotFoundError: No module named 'pysam'`
- **Fix:** `PYTHONPATH=$(echo $(cygpath -m "$GITHUB_WORKSPACE")/build/lib.*) pytest` in the windows job only (direct job's line untouched)
- **Files modified:** .github/workflows/ci.yaml
- **Verification:** Local Git Bash glob test (4 path forms); local import of the MSVC-built tree through the resulting PYTHONPATH; runner green at ec1dc63a (1032/16)
- **Committed in:** ec1dc63a

**2. [Rule 1 - Bug] Bundled setuptools 65.5.0 detached the process stdout stream**
- **Found during:** Task 2 (windows (3.11) red, run 38294145577)
- **Issue:** python.org 3.11.9 bundles setuptools 65.5.0; the unpinned prerequisite install no-ops there, and that setuptools generation detaches stdout during the MSVC build (`--- Logging error ---` at the C99-probe log.info) - pytest then dies at collection finish writing its summary (`ValueError: underlying buffer has been detached`). Build step itself stayed green, masking the corruption until pytest
- **Fix:** `pip install --upgrade Cython mypy pytest setuptools` in the windows job (with an explanatory comment); all six cells now run the same current setuptools family
- **Files modified:** .github/workflows/ci.yaml
- **Verification:** Local reproduction with a conda py311 env: setuptools==65.5.0 build shows 3 identical logging errors, setuptools 84.0.0 shows zero; runner all-25-jobs green at 207b6901
- **Committed in:** 207b6901

---

**Total deviations:** 2 auto-fixed (2 x Rule 1 bug, both in the plan's own additive job)
**Impact on plan:** Both fixes required for CI-01 to be green at all; neither touched any pre-existing ci.yaml job or setup.py. Pure-addition gate still passes (0 deleted lines vs 2ea68a19).

## Issues Encountered

None beyond the two deviations above (both root-caused with local reproduction before fixing, per the plan's reproduce-first triage discipline).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CI-01 / ROADMAP SC-1 closed: the windows job is the standing zero-regression detector for Windows on every push, and the prerequisite SC-1 gate for plan 04-02 (win-wheels cibuildwheel workflow) is satisfied
- Per-cell counts above are the CI-side input for 04-CI-VALIDATION.md (04-03); the CI-vs-local count delta (1032/16 vs 1028/15) awaits reconciliation there
- Research A1 confirmed (runner Git Bash + shell: bash works); A3 refined (cold build ~1.5-2 min on the current windows-latest generation, well under the 7-15 min estimate)

---
*Phase: 04-windows-ci-wheel*
*Completed: 2026-10-12*

## Self-Check: PASSED

- 04-01-SUMMARY.md and .github/workflows/ci.yaml exist on disk
- All 4 task commits (f0ff49a2, ec1dc63a, 05d50278, 207b6901) are ancestors of HEAD
- evaluation-scope (commits-only, this branch): 4 commits
- All plan-level verification commands re-run and green: YAML parse gate, SHA-pinned run jobs table (25/25 success at 207b6901), pure-addition gate (deleted_lines=0 vs 2ea68a19), fail-open scan (0)
