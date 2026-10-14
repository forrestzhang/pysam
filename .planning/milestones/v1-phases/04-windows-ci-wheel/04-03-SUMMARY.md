---
phase: 04-windows-ci-wheel
plan: 03
subsystem: infra
tags: [github-actions, wheels, sha256, consumer-verification, scope-audit, zero-regression]

requires:
  - phase: 04-02
    provides: Published fork Release v0.24.1-win.2 with six cp310-cp315 wheels (the distribution channel this plan's consumer proof exercises)
  - phase: 04-01
    provides: Six per-cell pytest counts from run 38296297134 (the CI-side baseline input for the reconciliation record)
provides:
  - Consumer-path proof on the live distribution channel: fresh venv, Release-URL pip install of the cp313 wheel, script-form smoke green, shadowing assert proven (import inside the venv's site-packages)
  - 04-CI-VALIDATION.md — the SHA-keyed CI evidence record (six windows cells, node-exact CI-vs-local reconciliation, six sha256s, delvewheel verdicts, clean-gate verdicts, CI-03 alignment, adopted-recommendation register Q1-Q5)
  - INSTALL Windows prebuilt-wheel section (fork Releases URL + pip-by-URL command + CPython 3.10-3.15 face)
  - Phase-exit zero-regression evidence: final-SHA CI run green on windows AND POSIX faces (run 38343462764, 25/25) + scope audit = exactly {ci.yaml, win-wheels.yaml, INSTALL} since 2ea68a19
affects: [milestone v4.3.1 close-out (gsd-complete-milestone), gsd-verify-work phase 04 audit]

actuals:
  tokens: 3300
  tasks: 2
  commits: 2
  plan_head_before: 4aa29be74b9da2715c886fda1cf911cb3a27b6b5
  plan_head_after: 1053e95f4c230dc62532b28195a57103b542790a

tech-stack:
  added: []
  patterns:
    - "Consumer-path verification = fresh venv + pip install by FULL Release URL (exercises the real channel) + script-form smoke + site-packages shadowing assert"
    "The shadowing assert must run in the script-form context (sys.path[0] = script dir): a python -c issued from the repo root puts cwd on sys.path and resolves to the source tree — the -c form is a false test of its own guard"

key-files:
  created: [.planning/phases/04-windows-ci-wheel/04-CI-VALIDATION.md]
  modified: [INSTALL]

key-decisions:
  - "Every Release URL and verify command in this plan was executed against tag v0.24.1-win.2, not the plan's literal v0.24.1-win.1: 04-02-SUMMARY (the plan's own read_first) records win.1's publish run failing before creating any Release and the Task 4 contingency re-tagging to win.2 as the published lineage"
  - "CI-vs-local count delta reconciled node-exactly (not arithmetically): 1032/16 = 1028/15 + 6 mypy-collected typechecking tests - 2 tty-gated testUsage units (TestSamtools + TestPysam, runner stdin is never a tty) + 1 upstream 3.11 skipif in the 3.11 cell"
  - "The shadowing guard is executed as a script file in TEMP (sys.path[0] = script dir, cwd = repo root) — the exact resolution context of devtools/smoke_test.py"

patterns-established:
  - "Evidence-record discipline for distribution claims: every count/verdict cites run ID, SHA, or tag; sha256s computed from a fresh gh release download of the published assets (an edited record stops matching the world)"

requirements-completed: [CI-02, CI-03]

coverage:
  - id: D1
    description: "Consumer-path proof on the published wheels: fresh venv, Release-URL install of the cp313 wheel, script-form smoke green, import proven inside the venv's site-packages"
    requirement: CI-02
    verification:
      - kind: integration
        ref: "pip install https://github.com/forrestzhang/pysam/releases/download/v0.24.1-win.2/pysam-0.24.1-cp313-cp313-win_amd64.whl into %TEMP%/gsd-uat-venv; devtools/smoke_test.py: 24 alignments, 44118 vcf lines, smoke OK; assert pysam.__file__ = %TEMP%/gsd-uat-venv/Lib/site-packages/pysam/__init__.py (re-run green end-to-end)"
        status: pass
    human_judgment: false
  - id: D2
    description: "04-CI-VALIDATION.md: six windows cell results, node-exact CI-vs-local reconciliation, six-wheel matrix with sha256s, clean-gate verdicts, CI-03 alignment, adopted-recommendation register Q1-Q5 — every verdict citing run ID/SHA/tag"
    requirement: CI-03
    verification:
      - kind: other
        ref: "file checks: sha256rows=8, sections=6, CI-03 mentions=2; gh release download v0.24.1-win.2 --pattern '*.whl' = 6 wheels, six sha256s recorded; delvewheel markers x6 from publish-run log (job 115086235074)"
        status: pass
    human_judgment: false
  - id: D3
    description: "INSTALL Windows prebuilt-wheel section: fork Releases URL, pip-by-URL install command (cp313 worked example), python.org CPython 3.10-3.15 requirement, self-containedness note"
    requirement: CI-02
    verification:
      - kind: other
        ref: "grep INSTALL: 'releases/download' count=1, '3.15' count=2"
        status: pass
    human_judgment: false
  - id: D4
    description: "Phase-exit zero-regression: final-SHA CI green on windows AND POSIX faces (run 38343462764 @ 1053e95f, 25/25 jobs: 6 windows + 19 pre-existing all success) + scope audit = exactly 3 source files since 2ea68a19"
    verification:
      - kind: integration
        ref: "gh run watch 38343462764 --exit-status (exit 0); windows_cells=6 conclusion sorted-unique=success; pre-existing 19/19 success; git diff --name-only 2ea68a19..HEAD minus .planning/ = .github/workflows/ci.yaml, .github/workflows/win-wheels.yaml, INSTALL (pyproject.toml/setup.py/devtools/vendor/win32 byte-identical)"
        status: pass
    human_judgment: false

duration: 27 min
completed: 2026-10-13
status: complete
---

# Phase 4 Plan 03: CI evidence close-out (CI-02/CI-03 + phase exit) Summary

**Consumer-path proof on the live Release (fresh venv installs the cp313 wheel by URL and passes smoke with the import proven inside site-packages), the SHA-keyed 04-CI-VALIDATION.md reconciliation record, the INSTALL consumer section, and a green final-SHA phase-exit gate with an exact 3-file scope audit**

## Performance

- **Duration:** 27 min
- **Started:** 2026-10-13T03:36:07Z
- **Completed:** 2026-10-13T04:03:22Z
- **Tasks:** 2
- **Files modified:** 2 (04-CI-VALIDATION.md new 85 lines; INSTALL +22/-2)

## Accomplishments

- **Consumer path proven on the real artifact** (the verification no CI job performed): a fresh venv (D:/miniconda3 CPython 3.13.5) pip-installed the cp313 wheel by its full Release URL — fetching the actually-published asset through DNS/TLS of the real channel — then `devtools/smoke_test.py` script-form passed (24 alignments, 44118 vcf lines, smoke OK) and the shadowing assert proved `pysam.__file__` inside that venv's site-packages (`%TEMP%\gsd-uat-venv\Lib\site-packages\pysam\__init__.py`)
- **Integrity record**: `gh release download v0.24.1-win.2 --pattern "*.whl"` delivered exactly six wheels (cp310-cp315, six expected filenames); six sha256s computed and recorded; delvewheel "no external dependencies are needed" x6 pulled first-hand from the publish run's build log (run 38332836356, job 115086235074, timestamped per wheel)
- **04-CI-VALIDATION.md written** (6 sections, 8 sha256 rows): six windows cell results SHA-pinned to run 38296297134 @ 207b6901; node-exact CI-vs-local reconciliation naming every count delta with mechanism; wheel matrix + import-table self-containedness note (no vendor DLLs, no msvcrt.dll); clean-gate verdicts + the consumer proof; CI-03 alignment (face 3.10-3.15 vs untouched requires-python >=3.9, cp39 exclusion rationale); adopted-recommendation register Q1-Q5
- **INSTALL documents the end-user path**: new "Windows (prebuilt wheel)" section — fork Releases URL, pip install by full Release URL (cp313 worked example from v0.24.1-win.2), python.org CPython 3.10-3.15 as the only requirement (VC runtime ships inside CPython; no MSYS2/toolchain for consumers)
- **Phase-exit zero-regression gate green**: FINAL_SHA `1053e95f` pushed; run [38343462764](https://github.com/forrestzhang/pysam/actions/runs/38343462764) — 25/25 jobs success (six windows cells + all 19 pre-existing POSIX/system/conda jobs); scope audit since phase base `2ea68a19`: exactly `.github/workflows/ci.yaml`, `.github/workflows/win-wheels.yaml`, `INSTALL` — pyproject.toml, setup.py, devtools/, vendor/, win32/ all byte-identical (the phase never touched build code)

## CI-vs-local reconciliation (summary of the record's section 2)

CI 1032/16 vs local 1028/15, node-exact: **+6 collected/passed** = the 6 typechecking tests that collect on CI (the windows job pip line installs mypy; local venvs module-skip 'mypy API not available'); **-2 passed/+2 node skips** = `TestSamtools::testUsage` + `TestPysam::testUsage`, both `skipif(not sys.stdin.isatty())` (samtools_test.py:275; runner stdin is never a tty, the local baseline session ran on one); **3.11 cell only**: +1 upstream skipif (`testIteratorOutOfScope`, crashes on CPython 3.11). Arithmetic: 1032 = 1028 + 6 - 2; 16 = 15 - 1 + 2; the common 13 node skips are the Phase-2/3 environment-shaped family recorded node-for-node in 03-SC2-RECONCILIATION §3. Zero unexplained differences.

## Task Commits

1. **Task 1: Consumer-path proof from the Release URL + 04-CI-VALIDATION.md** - `d16da6f3` (docs)
2. **Task 2: INSTALL Windows-wheel section + phase-exit zero-regression (scope audit + final-SHA CI)** - `1053e95f` (docs)

**Plan metadata:** (recorded below)

## Files Created/Modified

- `.planning/phases/04-windows-ci-wheel/04-CI-VALIDATION.md` - NEW (85 lines): the SHA-keyed evidence record for CI-01 matrix, wheel integrity, clean gates, CI-03 alignment, Q1-Q5 register
- `INSTALL` - new "Windows (prebuilt wheel)" consumer section before the MSYS2 dev section; MSYS2 section's stale "upcoming MSVC build path" cross-reference updated to point at the shipped wheel path

## Decisions Made

- All Release URLs executed against **v0.24.1-win.2** (the plan text carries v0.24.1-win.1 from before 04-02's publish): the plan's own read_first (04-02-SUMMARY) records win.1's release job failing before creating any Release and the pre-authorized re-tag; win.1 tag + failed run 38331012769 stay as the audit trail
- The shadowing assert runs as a **script file in TEMP** (sys.path[0] = script dir, cwd = repo root) — the exact resolution context the plan's action text describes for the smoke script; the plan's literal `python -c` verify form is self-defeating from the repo root (see Deviation 2)
- Delta reconciliation grounded in in-repo source before writing: counted typechecking_test.py's 6 tests, located the isatty skipif and the TestSamtools/TestPysam inheritance (TestBcftools commented out) — no count asserted without a mechanism

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan's Release URLs referenced the stale tag v0.24.1-win.1**
- **Found during:** Task 1 (precondition + verify commands)
- **Issue:** The plan was written against tag v0.24.1-win.1 before 04-02 executed; that tag's publish run failed at the release step before creating any Release (run 38331012769, `gh release create` without repo context), and 04-02's Task 4 contingency re-tagged to v0.24.1-win.2 as the published lineage — the win.1 asset URL the plan's verify commands use does not exist
- **Fix:** Substituted v0.24.1-win.2 in every URL, command, and the record (the plan's read_first, 04-02-SUMMARY, is the authority; it explicitly says win.2 is the published lineage and not to re-push win.1)
- **Files modified:** .planning/phases/04-windows-ci-wheel/04-CI-VALIDATION.md
- **Verification:** Live Release view (non-draft, 6 assets) + successful URL install + 6-wheel download with six sha256s
- **Committed in:** d16da6f3

**2. [Rule 1 - Bug] The plan's shadowing-assert verify command defeats its own guard**
- **Found during:** Task 1 (consumer-path verify)
- **Issue:** The verify's `python -c "import pysam; ... assert ..."` issued from the repo root puts `''` (cwd) at sys.path[0], so the import resolves to the source tree — observed `AssertionError: D:\Github\pysam\pysam\__init__.py` — the exact shadowing the guard exists to catch, induced by the invocation form itself (the `python -m`/`-c`-from-repo-root forms are false tests per 04-RESEARCH Pitfall 3)
- **Fix:** Executed the identical assert as a script file in TEMP (sys.path[0] = the script's directory, cwd = repo root) — the same resolution context as devtools/smoke_test.py; the fired `-c` form is retained in the record as evidence the guard has teeth
- **Files modified:** .planning/phases/04-windows-ci-wheel/04-CI-VALIDATION.md (section 4 shadowing-guard note)
- **Verification:** assert green with `pysam.__file__` inside `%TEMP%\gsd-uat-venv\Lib\site-packages`; full chain re-run green end-to-end
- **Committed in:** d16da6f3

**3. [Rule 1 - Bug] INSTALL's MSYS2 section contradicted the new wheel section**
- **Found during:** Task 2 (INSTALL edit)
- **Issue:** The pre-existing sentence "end-user Python support on Windows will be delivered by the upcoming MSVC build path" became false the moment the new section above it documents that shipped path
- **Fix:** Updated the cross-reference to "is delivered by the MSVC prebuilt-wheel path (see the section above)"
- **Files modified:** INSTALL
- **Verification:** grep gates still pass (releases/download=1, 3.15=2); diff is +22/-2 inside the in-scope file
- **Committed in:** 1053e95f

---

**Total deviations:** 3 auto-fixed (1 x Rule 3 blocking-tag substitution, 2 x Rule 1 correctness)
**Impact on plan:** All three were required for the plan's own acceptance criteria to be executable/consistent; no scope change — the phase still touches exactly the two workflows + INSTALL + .planning/.

## Issues Encountered

None beyond the deviations above. The final-SHA CI run needed no intervention (25/25 first try).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Phase 04 complete — the milestone's 4 phases are done.** CI-01/CI-02/CI-03 all evidenced: standing windows CI job, tag-gated wheel pipeline publishing delvewheel-repaired self-contained wheels to fork Releases, consumer path proven end-to-end, zero-regression closed at the final SHA
- Milestone v4.3.1 is ready for `/gsd-complete-milestone` (+ `/gsd-verify-work 04` if desired first); the CLAUDE.md "当前焦点" section predates this completion and will need a refresh at milestone close
- Future releases: push tag `v<version>-win.N`; the pipeline rebuilds, gates, and publishes autonomously

## Phase-Exit Evidence (FINAL_SHA-pinned)

- **FINAL_SHA:** `1053e95f4c230dc62532b28195a57103b542790a` (Task 2 commit; pushed as `4aa29be7..1053e95f win -> win`)
- **CI run:** [38343462764](https://github.com/forrestzhang/pysam/actions/runs/38343462764) — `gh run watch --exit-status` exit 0; windows_cells=6, conclusions sorted-unique = `success`; pre-existing jobs 19/19 `success`
- **Scope audit output** (`git diff --name-only 2ea68a19..HEAD | grep -v "^\.planning/"`):

```
.github/workflows/ci.yaml
.github/workflows/win-wheels.yaml
INSTALL
```

  source_files=3 (exact); protected paths (pyproject.toml, setup.py, devtools/, vendor/, win32/) — 0 files changed, byte-identical.

---

## Self-Check: PASSED

- 04-CI-VALIDATION.md, INSTALL, and this SUMMARY exist on disk
- Both task commits (d16da6f3, 1053e95f) are ancestors of HEAD
- evaluation-scope (commits-only, this branch): 2 commits resolved for 04-03
- All plan-level verification re-run green: consumer chain (URL install + script-form smoke + site-packages assert), 6-wheel download + six sha256s, record file checks (sha256rows=8, sections=6, CI-03=2), INSTALL greps, final-SHA CI verdict (25/25), scope audit (exactly 3 files)
