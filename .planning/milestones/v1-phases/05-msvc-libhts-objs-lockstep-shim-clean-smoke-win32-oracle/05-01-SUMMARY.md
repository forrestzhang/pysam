---
phase: 05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle
plan: "01"
subsystem: infra
tags: [lockstep, msvc_libhts_objs, htslib-makefile, shim-sentinel, dirent, github-actions, workflow-dispatch, cibuildwheel, clean-smoke, test-oracle, pysam-api-readback, zero-regression]

requires:
  - phase: 03-msvc
    provides: MSVC_LIBHTS_OBJS 52-TU mirror + win32/msvc shim layer + dual-toolchain probe discipline this plan enforces and completes
  - phase: 04-windows-ci-wheel
    provides: win-wheels.yaml publish pipeline (clean_smoke job, dry-run tag discipline) parameterized here
  - phase: 02-portability-tests
    provides: samtools_test win32 comparison ladder + check_samtools_view_equal oracle strengthened here
provides:
  - devtools/check_libhts_objs_lockstep.py — standalone MSVC_LIBHTS_OBJS lockstep check with synthetic-drift self-test (teeth)
  - setup.py check_msvc_libhts_objs_lockstep comparator wired win32-guarded at the run_make_print_config site — every UCRT64 build now enforces the mirror against the Makefile truth
  - devtools/probe_symbol_check.py cwd-independent and toolchain-scoped (EXT_SUFFIX)
  - Five-drop-in shim_selftest sentinel (dirent.h included, struct dirent touched) + corrected forwarder-gate end-tags
  - Parameterized clean_smoke (workflow_dispatch smoke_python choice input -> SMOKE_PY -> derived SMOKE_CP glob), platform-suffixed CIBW test-command key, env-indirect msys2-location
  - TestUtils.check_api_readback_equal + win32-guarded samtools_test rung — the win32 oracle reads back through pysam.AlignmentFile (reader independent of the dispatch writer)
  - CI evidence: win-test.3 dry-run tag run 38369651968 and smoke_python=3.12 dispatch run 38369877795, both green; fork CI green on phase-final SHA 0e57840c
affects: [next milestone audit cycle (debt ledger starts clean), htslib upgrades (lockstep gate now fires), v2 CI hardening]

actuals:
  tokens: 6095    # chars/4 over the realized diff (24381 diff chars / 4; plan estimate 120000 — estimate was ~20x high, first calibration sample for this profile)
  tasks: 4
  commits: 5      # measured: git rev-list --count 74a9e906..HEAD

tech-stack:
  added: []
  patterns:
    - "ast-extraction enforcement reuse: the standalone devtools check exec-extracts setup.py's comparator + mirror verbatim (probe_symbol_check.py discipline) — the standalone verdict IS the build-time verdict"
    - "one-definition CI parameterization: choice-bounded workflow_dispatch input -> job-level env (with default-literal fallback) -> bash-derived GITHUB_ENV value; zero cp-tag literals in the job, zero template expressions in run blocks"
    - "API read-back oracle: compare dispatch-written files through a DIFFERENT code path (pysam.AlignmentFile reader) than the writer (samtools main behind dispatch), with @PG-header and MD/NM-tag tolerance mirroring the oracle it strengthens"

key-files:
  created:
    - devtools/check_libhts_objs_lockstep.py
  modified:
    - setup.py
    - devtools/probe_symbol_check.py
    - win32/msvc/shim_selftest.c
    - win32/msvc/pthread.h
    - win32/msvc/dirent.h
    - .github/workflows/win-wheels.yaml
    - tests/samtools_test.py
    - tests/TestUtils.py
    - tests/PortabilityRegression_test.py

key-decisions:
  - "Lockstep enforcement lives at the run_make_print_config site, win32-guarded: the MSVC arm itself never invokes autotools (BUILD-02), so the mirror is enforced at the one point where the Makefile truth is simultaneously available — every UCRT64 build; enforcement unconditional (libcurl-enabled local configure fails loudly with the parity hint)"
  - "Comparator raises LinkError (the BUILD-03 symbol gate's exception) with sorted add/drop diff + TU counts — the drift report is actionable without re-running make"
  - "probe_symbol_check.py glob scoped to the running interpreter's EXT_SUFFIX: both venvs' inplace artifacts (cp314 .dll.a / cp313 .lib) now permanently coexist in pysam/, so the UCRT64 teeth probe must select its own toolchain's set (Rule 1 fix; the plan's 'no other change' was insufficient)"
  - "clean_smoke reads one definition: workflow_dispatch choice input (fixed six-version vocabulary — no free-form value can reach the shell, T-05-02) with the default literal repeated once as the env fallback for tag-push runs"
  - "check_api_readback_equal compares header lines minus @PG and records minus MD/NM via dict_of_read + tag dict — tolerance parity with check_samtools_view_equal's -x MD -x NM / without_header semantics, but through the htslib BAM reader"

patterns-established:
  - "Lockstep gate pattern: single comparator function in setup.py, ast-extracted by devtools (never re-implemented), self-test proves teeth with synthetic drift from the REAL expansion"
  - "Pure-addition win32 rung insertion: new elif before the existing BAM rung; POSIX ladder textually untouched (proven by diff-gate against a pre-task pinned base SHA)"

requirements-completed: []   # debt-cleanup phase — no v1 requirement IDs (copied verbatim from PLAN frontmatter)

coverage:
  - id: D1
    description: "MSVC_LIBHTS_OBJS lockstep: comparator + UCRT64 build-path wiring + standalone self-test + probe cwd fix (05 items 1 + 5a)"
    verification:
      - kind: integration
        ref: "UCRT64 devtools/check_libhts_objs_lockstep.py --self-test -> exit 0 (mirror 52 TUs == parity expansion 52 TUs; synthetic drift raised LinkError)"
        status: pass
      - kind: integration
        ref: "UCRT64 MAKE=mingw32-make HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl setup.py --name -> exit 0, prints pysam, wired check executed; MSVC _venv-msvc setup.py --name -> exit 0 (arm untouched)"
        status: pass
      - kind: integration
        ref: "probe from /tmp via UCRT64 bash -> probe OK (cwd-independent, 13 modules)"
        status: pass
    human_judgment: false
  - id: D2
    description: "shim_selftest five-drop-in sentinel + stale forwarder-gate end-tags corrected (03 IN-01 + IN-02)"
    verification:
      - kind: integration
        ref: "msvc_compile_probe.py pthread_win32.c shim_selftest.c -I win32/msvc -I win32 -> 2 passed, 0 failed; UCRT64 gcc -fsyntax-only -I win32/msvc -> FORWARDER-OK"
        status: pass
      - kind: unit
        ref: "drop-in-includes=5; stale-tags=0 corrected-tag-files=2 (grep gates)"
        status: pass
    human_judgment: false
  - id: D3
    description: "clean_smoke parameterization + win-wheels comment/env hygiene (04 IN-01/IN-02/IN-03)"
    verification:
      - kind: unit
        ref: "structural gates: cp313-in-clean_smoke=0; run-interpolations=0 file-wide; CIBW_TEST_COMMAND_WINDOWS=1; default literals = exactly two (options vocabulary line excluded)"
        status: pass
      - kind: e2e
        ref: "win-test.3 tag run 38369651968: build_wheels+clean_smoke success, release skipped by tag guard"
        status: pass
      - kind: e2e
        ref: "dispatch run 38369877795 smoke_python=3.12: clean_smoke SMOKE_CP=cp312, installed pysam-0.24.1-cp312-cp312-win_amd64.whl, 148 cp312 log refs"
        status: pass
    human_judgment: false
  - id: D4
    description: "win32 samtools_test oracle: pysam API read-back comparator + rung (02 WR-02), TDD RED->GREEN, dual-toolchain green, POSIX ladder untouched"
    verification:
      - kind: unit
        ref: "TestWin32OracleReadback 4/4 (teeth: mutated mapq rejected; honesty: byte-copy/MD-NM-diff/PG-diff accepted); RED machine-validated RED_EVIDENCE_OK before GREEN"
        status: pass
      - kind: integration
        ref: "pytest samtools_test.py PortabilityRegression_test.py: UCRT64 31 passed; MSVC 31 passed"
        status: pass
      - kind: unit
        ref: "POSIX-untouched diff gate vs pinned base e960aba8: removed-ladder-lines=0"
        status: pass
      - kind: integration
        ref: "both smoke commands exit 0 (smoke OK x2); fork CI run 38370847255 on phase-final 0e57840c: success"
        status: pass
    human_judgment: false

duration: 62 min
completed: 2026-10-13
status: complete
plan_head_before: 74a9e906f45447f0120d6e6846cc3c4be17bbeb5
plan_head_after: 0e57840c164f169b6688421ceffdc843b5dbde7a
---

# Phase 05 Plan 01: Tech-Debt Cleanup Summary

**MSVC_LIBHTS_OBJS lockstep enforced on every UCRT64 build (comparator + ast-extracted standalone check with synthetic-drift teeth), shim sentinel completed to five drop-ins, clean_smoke parameterized end-to-end via one dispatch input, and the win32 samtools_test oracle now reads back through pysam.AlignmentFile — all proven against dual toolchains plus three green CI runs.**

## Performance

- **Duration:** 62 min
- **Started:** 2026-10-13T08:05:09Z
- **Completed:** 2026-10-13T09:07:27Z
- **Tasks:** 4/4
- **Files modified:** 10 (1 created, 9 modified)

## Accomplishments

- Debt item 1 (v1 audit IN-W2, highest value): `setup.py` gained `check_msvc_libhts_objs_lockstep` — set-compares the real `make print-config` LIBHTS_OBJS expansion against the 52-TU MSVC mirror and raises LinkError with a sorted add/drop diff, TU counts, and the parity-configuration hint. Wired win32-guarded at the print-config site (POSIX executes zero new code; the MSVC arm stays autotools-free per BUILD-02). The new `devtools/check_libhts_objs_lockstep.py` ast-extracts comparator + mirror from setup.py (single source of truth), recreates the parity configure, and its `--self-test` proves teeth by requiring a synthetic drifted expansion to raise. Verified live: 52/52 TUs lockstep OK under UCRT64.
- Debt item 2 (03 IN-01/IN-02): shim_selftest now includes all five drop-ins (`<dirent.h>` added; `struct dirent` touched by address, no filesystem call) and the two stale `#endif /* __GNUC__ */` tags in pthread.h/dirent.h now state the full `__GNUC__ && !_MSC_VER` condition. cl probe 2/0, UCRT64 forwarder OK.
- Debt item 3 + item 5 CI bits (04 IN-01/IN-02/IN-03): clean_smoke reads ONE definition — a choice-bounded `smoke_python` dispatch input (six versions, default '3.13') -> job env SMOKE_PY (same literal as fallback) -> bash-derived SMOKE_CP -> setup-python version, step name, and wheel-install glob. CIBW test command renamed to the platform-suffixed `CIBW_TEST_COMMAND_WINDOWS` with the false comment removed; msys2-location moved out of the run line via step env (zero template expressions in run blocks file-wide). Proven by two live runs: win-test.3 tag (default path, release correctly skipped) and a smoke_python=3.12 dispatch (cp312 wheel installed in the clean room).
- Debt item 4 (02 WR-02, the only warning-level residue): the win32 samtools_test BAM rung now compares both sides read back through `pysam.AlignmentFile` (`check_api_readback_equal`: header lines minus @PG, records via dict_of_read + tags minus MD/NM) instead of re-entering `_pysam_dispatch` via `pysam.samtools.view` — reader independent of writer, TDD RED→GREEN with machine-validated RED evidence. POSIX ladder textually untouched (diff gate: 0 removed lines vs pinned base).
- Item 5a (01 probe residue): probe_symbol_check.py anchored at REPO_ROOT and scoped to the running interpreter's EXT_SUFFIX — cwd-independent from /tmp and immune to the coexisting MSVC inplace artifacts.
- Zero-regression red line: dual-toolchain smoke (smoke OK ×2), dual-toolchain touched-test files (31 passed each), fork CI green on every phase SHA including the final 0e57840c.

## Artifacts This Phase Produces

| Artifact | What it is | Evidence |
|---|---|---|
| `devtools/check_libhts_objs_lockstep.py` (new) | Standalone lockstep check; ast-extracts setup.py's comparator + mirror; `--self-test` synthetic-drift teeth | UCRT64 self-test exit 0: mirror 52 == expansion 52, teeth OK |
| `setup.py` comparator + wiring site | `check_msvc_libhts_objs_lockstep` (LinkError with sorted diff + parity hint), win32-guarded call at the run_make_print_config site | UCRT64 `setup.py --name` exit 0 with wired check executed; MSVC arm exit 0 |
| Five-drop-in sentinel | `win32/msvc/shim_selftest.c` includes + touches all five drop-ins; corrected end-tags in pthread.h/dirent.h | cl probe 2 passed/0 failed; FORWARDER-OK; stale-tags=0 |
| Parameterized clean_smoke definition | `win-wheels.yaml`: smoke_python choice input -> SMOKE_PY -> derived SMOKE_CP glob; suffixed CIBW key; env-indirect msys2-location | Tag run 38369651968 success (release skipped); dispatch run 38369877795 success (SMOKE_CP=cp312, cp312 wheel installed) |
| `TestUtils.check_api_readback_equal` + win32 rung | API read-back comparator + one win32-guarded elif rung in samtools_test.py | OracleReadback 4/4; 31 passed on both toolchains; POSIX-untouched gate 0 |
| CI evidence runs | win-test.3 dry-run tag + workflow_dispatch smoke_python=3.12 | Run IDs 38369651968 / 38369877795, both `success`, release skipped by guard; fork CI 38370847255 success on 0e57840c |

**Closed finding IDs (for the next audit cycle):** 03 IN-W2 (integration warning — MSVC_LIBHTS_OBJS lockstep, 05 item 1), 03 IN-01, 03 IN-02 (05 item 2), 04 IN-01, 04 IN-02, 04 IN-03 (05 items 3+5), 02 WR-02 (05 item 4), 01 probe-path residue (05 item 5a).

## Task Commits

Each task was committed atomically:

1. **Task 1: MSVC_LIBHTS_OBJS lockstep — comparator, self-test teeth, wiring, probe cwd fix (tracer)** - `2d23a69b` (feat) — tracer gate re-ran all four verifies end-to-end green (V1–V4=0); expanded
2. **Task 2: shim_selftest dirent sentinel + stale gate-tag cleanup** - `13f50b6b` (fix)
3. **Task 3: clean_smoke parameterization + win-wheels comment/env hygiene** - `e960aba8` (fix) — live CI proofs: tag run 38369651968 + dispatch run 38369877795
4. **Task 4: win32 oracle read-back + phase closeout (tdd)** - `3895802d` (test, RED) + `0e57840c` (feat, GREEN) — no refactor needed (implementation minimal)

**Plan metadata:** committed after this SUMMARY (docs).

## Files Created/Modified

- `devtools/check_libhts_objs_lockstep.py` — NEW standalone lockstep check (parity configure + print-config + ast-extracted comparator + --self-test teeth)
- `setup.py` — comparator function after run_make_print_config; win32-guarded call at the print-config site (two hunks, nothing inside the IS_MSVC_PYTHON branch)
- `devtools/probe_symbol_check.py` — REPO_ROOT-anchored, EXT_SUFFIX-scoped module glob
- `win32/msvc/shim_selftest.c` — fifth drop-in include + struct dirent sentinel touch; header comment four→five
- `win32/msvc/pthread.h`, `win32/msvc/dirent.h` — corrected forwarder-gate end-tags
- `.github/workflows/win-wheels.yaml` — smoke_python input, SMOKE_PY/SMOKE_CP derivation, suffixed CIBW key, env-indirect msys2-location
- `tests/TestUtils.py` — check_api_readback_equal beside check_samtools_view_equal
- `tests/samtools_test.py` — one win32-guarded elif rung before the BAM rung; import extended (only removed lines in the diff)
- `tests/PortabilityRegression_test.py` — TestWin32OracleReadback (4 permanent tests)

## Decisions Made

- Lockstep at the print-config site (not the MSVC arm): BUILD-02 forbids autotools under MSVC, so the mirror is checked where the Makefile truth exists — every UCRT64 dev build; unconditional per the debt spec.
- Probe EXT_SUFFIX scoping (Rule 1): both venvs' inplace artifacts now coexist in `pysam/` (26 .pyd); the naive REPO_ROOT anchor alone still matched both toolchains' sets and broke the .dll.a lookup.
- Dispatch-run ref: the fork's default branch is master (no win-wheels.yaml), so `gh workflow run` required `--ref win` — the plan's literal command cannot work against this fork's layout.
- `str(header)` over `header.to_string()`: this pysam's AlignmentHeader has no `to_string` (caught in GREEN loop, one fix cycle).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] probe_symbol_check.py needed toolchain scoping beyond the REPO_ROOT anchor**
- **Found during:** Task 1 verify 4 (probe from /tmp)
- **Issue:** `pysam/` permanently holds BOTH venvs' inplace artifacts (13 cp314-mingw .pyd+.dll.a from UCRT64, 13 cp313-win_amd64 .pyd+.lib from MSVC). The anchored glob matched all 26 and the hardcoded `.dll.a` implib lookup failed on the first cp313 artifact — the probe would fail identically from the repo root, regardless of the cwd fix (pre-existing latent breakage since 03-04's inplace MSVC build).
- **Fix:** Scope the glob to the running interpreter's `sysconfig.get_config_var("EXT_SUFFIX")` — the probe judges the UCRT64 build's own artifact set; missing artifacts still fail loudly (>= 13 assertion).
- **Files modified:** devtools/probe_symbol_check.py
- **Verification:** PROBE-CWD-OK from /tmp (13 modules, probe OK line)
- **Committed in:** 2d23a69b

**2. [Rule 1 - Bug] AlignmentHeader has no to_string() in this pysam**
- **Found during:** Task 4 GREEN run (all four tests failed on a byte-copied pair)
- **Issue:** `inf.header.to_string()` raised AttributeError inside the comparator.
- **Fix:** `str(inf.header)` (same SAM text; verified API surface: as_dict/to_dict/str).
- **Files modified:** tests/TestUtils.py
- **Verification:** OracleReadback 4/4 green
- **Committed in:** 0e57840c (GREEN commit)

### Documented criterion deviations (verify-command drift / regex imprecision — no missing work)

**3. cl-probe verify command needed `-I win32`**
- **Found during:** Task 2 verify 1
- **Issue:** The plan transcribed 03-03's probe invocation (`-I win32/msvc` only); unistd.h gained `#include <getopt.h>` in 03-04 (d77beaef), which resolves via `win32/` in the real build include path. The literal command fails C1083 on getopt.h.
- **Resolution:** Ran with `-I win32/msvc -I win32` (real-build order); both TUs compile. The gcc forwarder verify also passes in the exact plan form (`-I win32/msvc` only) since gcc never reaches the getopt include.

**4. default-literal B-gate regex cannot match value-inline YAML**
- **Found during:** Task 3 structural gates
- **Issue:** `grep -cE "^\s+'3\.13'"` requires `'3.13'` directly after leading whitespace; conventional YAML (`default: '3.13'`, `${{ inputs.smoke_python || '3.13' }}`) never matches, so B==2 is unsatisfiable without contorting the YAML (value-on-own-line forms). Empirically confirmed.
- **Resolution:** Wrote conventional YAML; verified the stated intent instead — exactly two default literals (input default + env fallback; line count of `'3.13'` = 3 = one options-vocabulary entry + the two defaults; no third sync site). cp313-in-clean_smoke=0 gate passed as written.

**5. dispatch verify required `--ref win`**
- **Found during:** Task 3 live proof
- **Issue:** `gh workflow run win-wheels.yaml` without a ref targets the default branch (master), which has no win-wheels.yaml.
- **Resolution:** `gh workflow run win-wheels.yaml --ref win -f smoke_python=3.12` — the dispatch run executed the phase's workflow file.

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs), 3 documented criterion/verify-command deviations (plan-text drift vs tree/fork reality; no scope change)
**Impact on plan:** No scope creep. All must_haves truths hold; every acceptance criterion verified with evidence (two via intent-equivalent checks where the plan's literal grep/command was stale).

## TDD Gate Compliance

Task 4 (`tdd="true"`): RED commit `test(05-01):` 3895802d precedes GREEN commit `feat(05-01):` 0e57840c. RED evidence machine-validated (`gsd_run check tdd-red-evidence` → RED_EVIDENCE_OK, target_test_failed; JUnit: 4 tests, 4 failed, 0 passed; target `TestWin32OracleReadback`). Semantics: all four tests failed at import of the not-yet-existing comparator — the intended reason. No REFACTOR commit (implementation minimal). Evidence record kept at `.planning/tmp/tdd-red-05-01-task4.json` + `.planning/tmp/tdd-red-05-01-task4-junit.xml` (untracked). Plan-level TDD gate not active (plan `type: execute`, init `tdd_mode: false`).

## Issues Encountered

- MSYS2-native python passes `/tmp/...` paths to htslib verbatim (Windows C library) — transient debug runs need explicit `C:/msys64/tmp/...` forms; no product impact.
- All three CI runs (tag, dispatch, fork CI on final SHA) required ~25-35 min wall time; polled to terminal conclusions per the SHA/tag-pinned discipline, never judged from in-progress lists.

## Authentication Gates

None — gh CLI was already authenticated (forrestzhang); no auth gates hit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The v1 milestone-audit debt list is closed: items 1-4 (must) + item 5 sweep, with the zero-regression red line re-proven (dual-toolchain smoke, dual-toolchain touched tests, fork CI green on 0e57840c).
- The next audit cycle starts clean; the htslib-upgrade drift hazard (52-TU mirror) is now mechanically gated on every UCRT64 build.
- Not-processing list stands (upstream-inherited items, Y2038, WR-04 locale cell) — see 05-CONTEXT.md; v2 items (W1 wheel-per-version suite gate, remote I/O, PyPI name) remain deferred.

---
*Phase: 05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle*
*Completed: 2026-10-13*

## Self-Check: PASSED

All 10 key files exist on disk (1 created + 9 modified); all 5 task commits (2d23a69b, 13f50b6b, e960aba8, 3895802d, 0e57840c) are ancestors of HEAD; ledger recount confirms 5 commits between plan_head_before (74a9e906) and HEAD (0e57840c), matching frontmatter actuals.
