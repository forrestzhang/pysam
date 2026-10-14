---
phase: 03-msvc
plan: "05"
subsystem: infra
tags: [msvc, suite-green, reconciliation, d2-07, ucrt-fail-fast, double-close, wr-01, getopt-reinit, static-assert, clang-cl, sc-3, zero-regression, fork-ci]

requires:
  - phase: 03-msvc/04
    provides: the green MSVC editable build + inplace artifacts this suite run exercises
  - phase: 02-portability-tests
    provides: the 1027/15 objective baseline and the reconciliation instrument shape (02-TEST02-RECONCILIATION.md)
provides:
  - SC-2 closed — full default-collection suite green on the MSVC build (1028 passed / 15 skipped / 0 failed, exit 0), reconciled node-for-node against the Phase-2 baseline with zero MSVC-only skips
  - Four suite-driven root-cause fixes (UCRT fail-fast double-close; WR-01 binary-capture regression; GNU-getopt stale optind; C11 _Static_assert under pyximport) — the first two latent on BOTH toolchains
  - SC-3 closed — clang-cl fallback decision record (cl.exe-first; contingency installs named blocking-human)
  - Phase-03 zero-regression closed — UCRT64 full suite 1028/15 on the phase-final tree + fork CI all 19 jobs green on the phase-final SHA (run 38278346280)
  - BUILD-02 acceptance evidence complete across all five phase-03 plans
affects: [Phase 4 CI/wheel (MSVC artifacts proven suite-green; py<3.12 CI syntax lesson), v2 remote-I/O]

actuals:
  tokens: 6600   # chars/4 over the realized diff (26413 diff chars; estimate was 35000)
  tasks: 3
  commits: 7     # measured: git rev-list --count 77144e60..HEAD

tech-stack:
  added: []
  patterns:
    - "UCRT invalid-parameter fail-fast forensics: ctypes _set_invalid_parameter_handler + RtlCaptureStackBackTrace + dbghelp resolves faulting RVA -> IAT slot when no debugger exists (0xC0000409 = release-CRT _invalid_parameter_noinfo)"
    - "fd-ownership discipline for captured-stdout lending: any dispatch command handing fileno(FILE*) to an ownership-taking API must lend a dup() — the UCRT kills the process on the lender's later fclose (double close)"
    - "per-toolchain getopt identity matters for the dispatch reset: the vendored win32/getopt.c is GNU getopt (optind=0 reinit idiom), mingwex's is BSD-style (optind=1) — the reset gate is keyed on the implementation, not the platform"

key-files:
  created:
    - .planning/phases/03-msvc/03-SC2-RECONCILIATION.md
    - .planning/phases/03-msvc/03-CLANGCL-EVAL.md
  modified:
    - samtools/bam_reheader.c.pysam.c
    - samtools/bam_cat.c.pysam.c
    - pysam/libcutils.pyx
    - import/pysam.c
    - samtools/samtools.pysam.c
    - bcftools/bcftools.pysam.c
    - tests/_compile_sizes.pyx
    - setup.py

key-decisions:
  - "reheader/cat fd lend fixed with dup() at the lend sites under _WIN32 (#else verbatim) rather than defensive fclose anywhere: bgzf_dopen's ownership contract is legitimate; the lender keeping its own descriptor is the root-cause fix (upstreamable)"
  - "_collect decode is strict-first, not replacement-always: valid UTF-8 text returns str byte-identically (WR-01 intact), non-UTF-8 data is binary tool output and returns raw bytes — 03-01's replacement-always form was a latent both-toolchain suite regression that only surfaced now because no full suite ran between 03-01 and this plan"
  - "dispatch optind reset keyed to __GLIBC__ || _MSC_VER (GNU getopt reinit idiom) — the MSVC build's getopt is the vendored GNU copy, not mingwex's; MinGW arm unchanged"
  - "_compile_sizes asserts converted to negative-array-size typedefs (portable pre-C11 static assert) instead of passing /std:c11 through pyximport: platform-neutral sentinel form, keeps the assertion identical everywhere, and un-skips the 3 tests rather than widening the skip"

patterns-established:
  - "reproduce-first with C-level evidence before fixing: single-name pytest reproduction, raw ERRORLEVEL via cmd /v:on, ctypes IPH + stack walk for fail-fast faults — every MSVC suite failure got a stack-proven root cause, zero reflexive skips (D2-07)"
  - "CI syntax floor is the oldest supported Python (3.9): local interpreters 3.13/3.14 accept PEP 701 f-strings that kill CI — ast.parse(feature_version=(3,9)) is the cheap pre-push gate"

requirements-completed: [BUILD-02]

coverage:
  - id: D1
    description: "SC-2: full default-collection suite green on the MSVC build with node-exact count reconciliation against the Phase-2 1027/15 baseline (plus this phase's single added test) and an empty exemption list"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "_venv-msvc/Scripts/python.exe -m pytest -> '1028 passed, 15 skipped in 20.01s', exit 0 (re-run in final sweep: 1028/15 exit 0)"
        status: pass
      - kind: other
        ref: "03-SC2-RECONCILIATION.md: counts table vs baseline, five-failure triage table (all root-caused, zero exemptions), skip diff with zero MSVC-only and zero baseline-only rows; grep '1027|baseline' count 9"
        status: pass
    human_judgment: false
  - id: D2
    description: "SC-3: clang-cl fallback evaluation decision record — cl.exe-first decision, evidence-based supersedence of the prior-art premise, contingency path with blocking-human install gates, revisit triggers"
    requirement: BUILD-02
    verification:
      - kind: other
        ref: "03-CLANGCL-EVAL.md: 17 clang-cl references, all four section headings (Decision/Evidence/Contingency/Revisit), cites 03-04 build evidence + the 03-05 suite run, contingency installs marked blocking-human"
        status: pass
    human_judgment: false
  - id: D3
    description: "Phase-03 zero-regression close-out: UCRT64 full suite green on the phase-final tree and fork CI blocking jobs green on the phase-final SHA"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "MSYSTEM=UCRT64 _venv/bin/python.exe -m pytest -> '1028 passed, 15 skipped in 15.07s', exit=0 (after full rebuild on the phase-final tree)"
        status: pass
      - kind: other
        ref: "gh run 38278346280 (head_sha 0e6adfd7b148bf6f712855927645204518f5b9e5 == recorded PHASE_SHA): conclusion success, 19/19 jobs green — ubuntu direct 3.9-3.15-dev x7, macos direct x7, sdist x2, conda, freebsd+netbsd advisory-green; first push b3b479a7 failed macos 3.11 (py<3.12 f-string), root-caused and fixed before close"
        status: pass
    human_judgment: false

duration: 68 min
completed: 2026-10-12
status: complete
plan_head_before: 77144e60602ef3e0d42b95a413acbdd653c72e2a
plan_head_after: 0e6adfd7b148bf6f712855927645204518f5b9e5
---

# Phase 03 Plan 05: SC-2 Suite Green + Reconciliation, SC-3 clang-cl Decision, Phase Close-Out Summary

**The full 1028-test suite green on the MSVC-built artifacts with every count reconciled node-for-node against the Phase-2 baseline and zero exemptions — after four stack-proven root-cause fixes (a UCRT fail-fast fd double-close, a both-toolchain WR-01 binary-capture regression, stale GNU-getopt state, and a C11 assert under pyximport) — plus the SC-3 cl.exe-first decision record and the phase-close zero-regression gate (UCRT64 1028/15 + fork CI 19/19 on the final SHA).**

## Performance

- **Duration:** 68 min
- **Started:** 2026-10-12T15:39:54Z
- **Completed:** 2026-10-12T16:48:06Z
- **Tasks:** 3/3
- **Files modified:** 10 (2 created, 8 modified)
- **First-suite failures root-caused:** 5 (all fixed, zero exemptions)

## Accomplishments

- **SC-2 closed with objective parity evidence:** the complete default-collection suite runs green on the MSVC build — `1028 passed, 15 skipped, 0 failed`, exit 0, verbatim — and the skip set is node-for-node the Phase-2 Windows baseline's (11 libcurl capability gates + 2 unconditional upstream skips + 2 module env gates; the passed delta is exactly 03-01's one added WR-01 test). The reconciliation artifact mirrors the 02-TEST02 shape: triage table, counts table, three-bucket skip diff (zero MSVC-only, zero baseline-only), empty exemption list.
- **Every first-run failure got a stack-proven root cause, not a skip:** the reheader process-kill was traced via a ctypes invalid-parameter handler + RtlCaptureStackBackTrace + objdump/IAT resolution to `samtools_close_stdout → fclose` on an fd `bgzf_dopen` had already closed (glibc and MSYS2's python tolerate the double close; conda CPython's UCRT fail-fasts — a latent upstream bug exposed by the MSVC runtime). The cumulative empty-output failure was bisected to the vendored GNU getopt's reinit idiom. Full narratives in `03-SC2-RECONCILIATION.md` section 1.
- **Two latent BOTH-toolchain regressions caught and fixed:** 03-01's WR-01 `_collect` replacement-decode destroyed binary captured output (reheader's BAM) on UCRT64 and MSVC alike — no full suite had run between 03-01 and this plan; the strict-first decode + raw-bytes fallback restores the pre-WR-01 binary contract while keeping WR-01's text guarantee (its regression test stays green on both builds).
- **SC-3 discharged as a documented decision:** cl.exe-first; the "clang-cl needed for VLAs" prior-art premise (theAeon 2025 pain list, teepean's reply) is superseded by the 1.24-tree evidence — one VLA (heap-fixed), one qualifier (dropped), a finite centralized name/header shim, and a fully green cl.exe build+suite. Contingency (VS "C++ Clang tools" component / winget LLVM, both named blocking-human) rides the existing `compiler_type == 'msvc'` arm without structural change.
- **Phase-03 zero-regression closed:** UCRT64 full suite 1028/15 exit 0 on the phase-final tree (fresh rebuild), and fork CI run [38278346280](https://github.com/forrestzhang/pysam/actions/runs/38278346280) — matched by `head_sha == 0e6adfd7` — green on all 19 jobs (ubuntu/macos direct 3.9–3.15-dev blocking, sdist, conda, BSD advisory-green). The first push exposed one more latent defect (an f-string backslash legal only on py≥3.12 — 03-04's wave had never been CI'd); root-caused and fixed before close.

## Task Commits

Each task's gap closures landed as they were proven (03-04 pattern):

1. **Task 1: Full suite on MSVC + count reconciliation** — `61fc11b8` (dup() lend-site fix), `dfa47c25` (_collect strict-decode + bytes fallback), `860dd867` (optind=0 MSVC reset, template+twins lockstep), `f89add93` (portable typedef static asserts), `67485b88` (SC-2 reconciliation artifact)
2. **Task 2: clang-cl decision record** — `b3b479a7` (03-CLANGCL-EVAL.md)
3. **Task 3: Zero-regression close-out** — `0e6adfd7` (py<3.12 f-string fix; the SHA the green CI verdict is keyed to)

## Files Created/Modified

- `.planning/phases/03-msvc/03-SC2-RECONCILIATION.md` (new) — counts + triage + skip diff + empty exemption list
- `.planning/phases/03-msvc/03-CLANGCL-EVAL.md` (new) — SC-3 decision record
- `samtools/bam_reheader.c.pysam.c`, `samtools/bam_cat.c.pysam.c` — dup() at the two fileno(samtools_stdout) lend sites (#else verbatim)
- `pysam/libcutils.pyx` — _collect strict-first UTF-8 decode with raw-bytes fallback for binary capture
- `import/pysam.c` + `samtools/samtools.pysam.c` + `bcftools/bcftools.pysam.c` — optind reset gate `__GLIBC__ || _MSC_VER` (sed-lockstep diff-clean)
- `tests/_compile_sizes.pyx` — negative-array typedef asserts (portable form; un-skips 3 tests on MSVC)
- `setup.py` — config-vars backslash escape moved out of the f-string expression (py<3.12 CI)

## Decisions Made

See key-decisions in frontmatter. Additional: the phase-final SHA is `0e6adfd7` (the CI-verdict key); the pre-fix SHA `b3b479a7`'s failed run (38277045819) is preserved in the reconciliation narrative as the evidence that caught the f-string defect.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] UCRT fail-fast on the reheader dispatch (process killed, exit 0xC0000409)**
- **Found during:** Task 1 (first full-suite run)
- **Issue:** `main_reheader`/`bam_cat` lend `fileno(samtools_stdout)` to `bgzf_dopen`, which owns+ closes the fd; the dispatch shim's later `fclose` on the FILE* wrapping the same fd is a double close the UCRT (behind conda CPython, which installs no invalid-parameter handler) treats as fatal
- **Fix:** `dup()` at both lend sites under `_WIN32`, `#else` verbatim; POSIX arms untouched
- **Verification:** stack proof at fault + reheader probes green + full suite green
- **Committed in:** 61fc11b8

**2. [Rule 1 - Bug] 03-01's WR-01 fix regressed binary captured output (both toolchains)**
- **Found during:** Task 1 (testStatements UnicodeEncodeError after fix 1)
- **Issue:** `_collect`'s replacement-always decode lossy-converted reheader's BAM (binary) to U+FFFD str; the oracle's `force_bytes` failed — reproduced on UCRT64 too (latent since 03-01; no full suite had run)
- **Fix:** strict-first decode; non-UTF-8 data returns raw bytes (pre-WR-01 contract); valid UTF-8 text unchanged (WR-01 test green both builds)
- **Verification:** TestSamtools + WR-01 test green on both builds; full suites green
- **Committed in:** dfa47c25

**3. [Rule 1 - Bug] Stale GNU-getopt state made later dispatches misparse options (full-suite-only, cumulative)**
- **Found during:** Task 1 (WR-01 test returned empty output with exit 0 after preceding dispatch history)
- **Issue:** the dispatch reset's non-glibc arm (`optind = 1`) does not reinitialize the vendored GNU getopt's permutation state; a later `view -H -o` dispatch dropped its `-o` and wrote the header into the devnull capture
- **Fix:** reset gate widened to `__GLIBC__ || _MSC_VER` (GNU `optind=0` reinit idiom) in the template + both twins; MinGW (mingwex BSD getopt) unchanged; sed-lockstep diff-clean
- **Verification:** previously failing combination green; full suite green; testUsage access-violation (downstream manifestation) gone
- **Committed in:** 860dd867

**4. [Rule 3 - Blocking] `_Static_assert` in _compile_sizes un-compilable under pyximport's stock MSVC flags (3 tests module-skipped)**
- **Found during:** Task 1 (skip reconciliation: 18 skips vs baseline 15)
- **Issue:** C11 keyword MSVC only accepts under an explicit /std switch — setup.py passes /std:c11, pyximport does not; the width invariants themselves hold on MSVC
- **Fix:** negative-array-size typedef asserts (portable pre-C11 form) — identical invariant on every toolchain; un-skips the 3 tests
- **Verification:** compile_test 6/6 on both builds; suite back to the 15-skip baseline shape
- **Committed in:** f89add93

**5. [Rule 1 - Bug] py<3.12 SyntaxError in setup.py (fork CI macos/ubuntu 3.9–3.11 cells)**
- **Found during:** Task 3 (first CI push, run 38277045819 — the 03-04 wave's first CI exposure)
- **Issue:** 03-04's config-vars backslash escape put `"\\"` inside an f-string expression — legal only since Python 3.12 (PEP 701); both local interpreters (3.13/3.14) accepted it
- **Fix:** escaped value computed in a plain statement; py3.9-grammar parse verified; both toolchains' `setup.py --name` green
- **Verification:** re-push run 38278346280 all 19 jobs green at the fix SHA
- **Committed in:** 0e6adfd7

---

**Total deviations:** 5 auto-fixed (4 Rule 1 bugs, 1 Rule 3 blocking) — all suite-driven gap closures within the plan's own fix classes
**Impact on plan:** No scope creep. All must_haves truths hold: the suite is green on MSVC artifacts with every difference named and caused (zero exemptions), the clang-cl decision record exists with the contingency path, and both zero-regression instruments are green on the phase-final state. Two of the five fixes (WR-01 regression, f-string) were latent defects from earlier plans that this plan's instruments were designed to catch.

## Issues Encountered

- No debugger exists on this machine (no cdb/windbg, no PDBs) — the fail-fast fault was localized with ctypes-installed invalid-parameter/VEH handlers + stack walking + objdump/IAT resolution; the technique is recorded in frontmatter patterns for future use.
- The crash behaviors were highly environment-sensitive (bash-vs-cmd, -v-vs---tb=no, pytest-vs-plain) — resolved by treating each reproduction as evidence and fixing root causes rather than chasing the sensitivity; every sensitivity disappeared after the root-cause fixes.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None — all paths are real implementations. The three 03-03 documented simplifications (joined value_ptr 32-bit, recursive default mutex, musl-regex behavior) were watched at suite time as instructed: the full green suite on MSVC is the empirical evidence none of them affects any suite test.

## Next Phase Readiness

- Phase 03 complete: BUILD-02 fully evidenced across all five plans (carried fixes → vendoring → build foundation → full green build → suite green + reconciliation + decision record + zero-regression close).
- Phase 4 (Windows CI + wheel 分发) can proceed: the MSVC artifacts are suite-green, the out-of-tree/wheel-path build shape was proven in 03-04, and the py<3.12 f-string lesson is recorded (CI builds 3.9+).
- Fork CI green on the phase-final SHA `0e6adfd7` — the standing per-push gate continues into Phase 4.

## Self-Check: PASSED

All 11 created/modified key files exist on disk (both artifacts, the SUMMARY, and all 8 code files); all 7 task commits (61fc11b8, dfa47c25, 860dd867, f89add93, 67485b88, b3b479a7, 0e6adfd7) are ancestors of HEAD; ledger recount confirms 7 commits between plan_head_before (77144e60) and HEAD, matching frontmatter actuals; the CI verdict run (38278346280) head_sha equals plan_head_after (0e6adfd7).

---
*Phase: 03-msvc*
*Completed: 2026-10-12*
