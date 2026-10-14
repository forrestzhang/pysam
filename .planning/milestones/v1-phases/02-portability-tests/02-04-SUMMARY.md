---
phase: 02-portability-tests
plan: 04
subsystem: testing
tags: [windows, suite-green, test-reconciliation, skip-parity, fork-ci, zero-regression, d2-07, test-01, test-02]

requires:
  - phase: 02-portability-tests plan 01
    provides: libcport fd-I/O mapping + canonical UCRT64 rebuild contract
  - phase: 02-portability-tests plan 02
    provides: binary/CJK/LLP64 regression suite (11 tests) feeding the collected count
  - phase: 02-portability-tests plan 03
    provides: Python data generators, spawn-safe conftest, in-process comparison rewrites
provides:
  - Full default-collection suite green on Windows — 1027 passed / 15 skipped / 0 failed, exit 0 (TEST-01 closed)
  - D2-07 triage record for all four upstream-known failures — one passes, three fixed by a one-line test-hygiene fix (unclosed FileHandler), zero exemptions needed for them
  - 02-TEST02-RECONCILIATION.md — counts table (Windows vs fork CI ubuntu on one SHA), individually-named skip diff, written-cause exemption list (TEST-02 closed)
  - Zero-regression closure for all of phase 02 — fork CI run 38220111717 green on all 19 jobs after root-causing and fixing the 02-03 httpserver regression
affects: [phase-3-msvc, phase-4-ci, v2-remote-io]

actuals:
  tokens: 3954      # chars/4 over the realized diff (15815 chars, 3 files)
  tasks: 3
  commits: 4        # MEASURED: git rev-list --count 35808573..61125c2a
plan_head_before: 3580857362ade7b842817e8addf24a254bf2f9dc
plan_head_after: 61125c2a97e56a83fead338e6d9ab67f19b02902

tech-stack:
  added: []
  patterns:
    - "POSIX-identical-outside-guards applies to test fixtures too: platform-split conftest restores upstream blocks verbatim (token-identical, guard indentation only)"
    - "TEST-02 reconciliation mechanics: node-id set diff (collect-only vs CI-log extraction) instead of count arithmetic alone — catches exactly which module differs"

key-files:
  created:
    - .planning/phases/02-portability-tests/02-TEST02-RECONCILIATION.md
  modified:
    - tests/AlignmentFile_test.py
    - tests/conftest.py

key-decisions:
  - "TestLogging trio root cause was test hygiene, not platform behavior: check() leaked an open FileHandler; POSIX tolerates unlink-while-open so upstream never saw it. Fixed by closing/removing the handler (POSIX no-op) - no exemption granted (D2-07 fix-first order paid off)."
  - "testReadingFromFileWithoutIndex passes on this build - 02-03's data generation was all it needed; upstream #1274's four failures reduce to one hygiene bug on our toolchain."
  - "httpserver must be platform-split: _pysam_dispatch runs samtools mains with the GIL held, so an in-process thread server starves while a dispatch call blocks in libcurl (ubuntu TestRemoteFileHTTP::testView connection timeout). POSIX restores upstream's child-process server verbatim; win32 keeps the spawn-safe thread variant where all libcurl-gated tests skip."
  - "TEST-02 baseline cell = direct (ubuntu, 3.14) on the phase-final code SHA (matches Windows Python 3.14.7); node-level reconciliation shows collection differs in exactly one module (typechecking: mypy present on CI, absent from the UCRT64 venv)."
  - "Windows 1040-collected = research 1028 + this phase's own 12 added tests; run-vs-collect +2 = the two module-level skip placeholders (linking, typechecking), resolving the run-accounting anomaly."

patterns-established:
  - "Reproduce-first triage table (per-name outcome before any fix/skip decision) as the D2-07 evidence shape"
  - "Skip-diff table with three buckets: both-platform, Windows-only (exemption-linked), baseline-only (Windows runs more) - zero unexplained differences as the threshold"

requirements-completed: [TEST-01, TEST-02]

coverage:
  - id: D1
    description: "D2-07 triage of the four upstream-known failures: reproduce-first baseline recorded, TestLogging trio fixed at root (unclosed FileHandler), testReadingFromFileWithoutIndex passes"
    requirement: TEST-01
    verification:
      - kind: integration
        ref: "UCRT64: pytest tests/AlignmentFile_test.py -k 'TestLogging or testReadingFromFileWithoutIndex' -v → '4 passed, 365 deselected in 0.16s', teardown clean, log.txt absent"
        status: pass
      - kind: other
        ref: "Pre-fix reproduction captured: 4 passed + 3 teardown ERRORs (PermissionError WinError 32 on os.unlink('log.txt')) - recorded in 02-TEST02-RECONCILIATION.md section 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Full default collection green on Windows with bounded, documented skips (D2-11 perimeter; no deselection, no new unconditional skips)"
    requirement: TEST-01
    verification:
      - kind: integration
        ref: "UCRT64: _venv/bin/python.exe -m pytest → '1027 passed, 15 skipped in 15.38s' exit 0; -rs rerun '1027 passed, 15 skipped in 15.45s' exit 0 (final tree)"
        status: pass
      - kind: other
        ref: "collect-only 1040 (drift = phase's own +12 tests, enumerated); git diff c3541873..HEAD: one reasoned skipif added, zero removed, zero unconditional"
        status: pass
    human_judgment: false
  - id: D3
    description: "TEST-02 reconciliation artifact: verbatim counts from both platforms on SHA d912a1df, every skip difference individually named, written-cause exemption list"
    requirement: TEST-02
    verification:
      - kind: other
        ref: "02-TEST02-RECONCILIATION.md gates: collected|passed count=12 (≥2), ubuntu mentions=20 (≥1), legacy-count=0; -rs run green while listing reasons"
        status: pass
    human_judgment: false
  - id: D4
    description: "Zero-regression closure for phase 02: fork CI ubuntu and macos green on the phase-final code commit"
    verification:
      - kind: other
        ref: "gh: run 38220111717 on d912a1df → conclusion success, all 19 jobs success (direct ubuntu/macos 3.9-3.15-dev, sdist, conda, BSD advisory-green); regression run 38217865780 root-caused and fixed first"
        status: pass
    human_judgment: false

duration: 53 min
completed: 2026-10-12
status: complete
---

# Phase 2 Plan 4: Suite Green + TEST-02 Reconciliation Summary

**Windows suite fully green under default collection (1027 passed / 15 skipped / 0 failed) with the four upstream-known failures resolved by one test-hygiene root-cause fix, a node-exact TEST-02 reconciliation against fork CI ubuntu on the same SHA, and phase-wide zero-regression closed after root-causing the 02-03 thread-httpserver CI regression (GIL-holding dispatch starves an in-process server)**

## Performance

- **Duration:** 53 min (start 2026-10-12T07:12:25Z, end 2026-10-12T08:05:48Z)
- **Tasks:** 3
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- **D2-07 triage (Task 1):** reproduce-first baseline: `testReadingFromFileWithoutIndex` PASSES; the TestLogging trio's bodies pass but teardown ERRORs with `PermissionError: [WinError 32]` — `check()` never closed its `logging.FileHandler('log.txt')`, and Windows cannot unlink an open file (POSIX can, which is why upstream is blind to the leak). Fixed by close+removeHandler after the pileup (POSIX no-op). Zero exemptions needed for any of the four names.
- **Suite green (Task 2):** first full default-collection drive was already green — `1027 passed, 15 skipped in 16.30s`, exit 0. All 15 skips are pre-existing classes (11 libcurl capability gates, 2 unconditional upstream skips, 2 module env gates); zero Windows-only silent skips. Collection count 1040 = research baseline 1028 + this phase's own 12 added tests (enumerated); the run-vs-collect +2 anomaly was root-caused to the two module-skip placeholders in pytest's run accounting, and deselection/duplication were empirically excluded (subset + uniq checks).
- **TEST-02 + zero-regression (Task 3):** pushed the phase (30 commits); first CI run failed exactly one test on ubuntu/sdist/freebsd — `TestRemoteFileHTTP::testView` connection timeout. Root cause: 02-03's thread httpserver starves because `_pysam_dispatch` holds the GIL through the whole samtools main (incl. the libcurl transfer); upstream's child-process server is immune. Fix: platform-split conftest — POSIX branch restored token-identical to upstream, win32 keeps the thread variant (unreachable GIL interaction there — all libcurl-gated tests skip). Re-push: **all 19 jobs green** (run 38220111717). Reconciliation doc committed with verbatim counts from both platforms on SHA `d912a1df`: Windows `1027 passed, 15 skipped` vs ubuntu direct 3.14 `1042 passed, 5 skipped`, node-level diff = exactly one module (typechecking: mypy on CI, absent in the UCRT64 venv).

## Task Commits

1. **Task 1: reproduce + triage + fix the 4 upstream-known failures** - `e4dc435c` (fix: TestLogging handler close + reconciliation doc started)
2. **Task 2: full-suite green + skip audit** - `16b05567` (test: doc grown with counts/skip inventory/audit evidence)
3. **Task 3: TEST-02 reconciliation + zero-regression closure** - `d912a1df` (fix: conftest platform-split CI regression fix) + `61125c2a` (docs: reconciliation artifact finalized)

**Plan metadata:** this commit (docs)

## Files Created/Modified
- `tests/AlignmentFile_test.py` - TestLogging.check() closes its FileHandler (win32 unlink requirement, POSIX no-op)
- `tests/conftest.py` - httpserver platform-split: POSIX = upstream child-process server verbatim; win32 = spawn-safe thread server (02-03)
- `.planning/phases/02-portability-tests/02-TEST02-RECONCILIATION.md` - triage baseline, counts table, skip diff, exemption list, zero-regression record

## Decisions Made
See key-decisions in frontmatter. Additional: TEST-02 baseline cell chosen as direct (ubuntu, 3.14) to match the Windows session's Python 3.14.7; ubuntu 3.11's extra skip (one invalid-access test known to crash on 3.11) noted in the doc but not part of the baseline pair.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 02-03's thread httpserver broke fork CI ubuntu (regression within the phase)**
- **Found during:** Task 3 (first CI push, run 38217865780: direct ubuntu 3.13 + sdist ubuntu 3.14 + freebsd each failed exactly `TestRemoteFileHTTP::testView` — connection timeout)
- **Issue:** `_pysam_dispatch` calls `samtools_dispatch` with the GIL held (`pysam/libcutils.pyx`, no nogil), so while the dispatch blocks in libcurl awaiting the HTTP response, an in-process daemon-thread server can never run to answer. The non-dispatch remote tests passed (libchtslib releases the GIL) and `conda` ubuntu (libcurl disabled) was green, isolating the dispatch+thread interaction.
- **Fix:** platform-split `tests/conftest.py` — POSIX branch restores upstream's `_httpd` and fixture body verbatim (token-identical; only guard-required indentation differs); win32 keeps 02-03's threading variant (spawn safety) where every libcurl-gated remote test skips, making the GIL interaction unreachable.
- **Files modified:** tests/conftest.py
- **Verification:** Windows full suite green after the split (1027 passed / 15 skipped, exit 0); re-push run 38220111717 green on all 19 jobs (ubuntu+macos blocking, BSD advisory-green).
- **Committed in:** d912a1df

---

**Total deviations:** 1 auto-fixed (1 Rule 1 regression fix inside the phase's own changes)
**Impact on plan:** The regression fix was Task 3's own mandate ("root-cause the regression before committing the artifact") executed to completion; the red line (every 02-xx change POSIX-identical outside win32 guards) is restored and now enforced by a green CI. No scope creep.

## Issues Encountered
- pytest run-vs-collect accounting anomaly (1042 run units vs 1040 collected on Windows) — investigated to resolution: the 2 module-level skip placeholders (linking, typechecking) count as run units; 52 further `-v` status lines are swallowed by dispatch fd-1 redirection (the documented `-s` constraint) — evidence recorded in the reconciliation doc.
- The `[E::bgzf_read] ... error 4` stderr line seen around TestSanityChecking/TestLogging runs also appears in the ubuntu CI logs on passing builds — expected htslib error-path noise from intentionally-truncated fixtures, not a failure signal.
- mypy is not installed in the UCRT64 dev venv, so `tests/typechecking_test.py` module-skips on Windows while running 6 tests on CI — documented as an environment-difference exemption row (test-env dependency, not a platform limitation).

## Authentication Gates
None — `gh` was already authenticated (forrestzhang); git push over SSH worked first try.

## Known Stubs
None — no placeholder data, no unwired consumers, no unrun verifies.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 2 complete: all six requirements (PORT-01..04, TEST-01, TEST-02) closed with objective evidence; suite green on Windows and fork CI green on the phase-final code SHA `d912a1df`.
- For Phase 3 (MSVC): the D2-03 checklist doubles as the porting inventory; nothing in 02-04 adds MSVC surface.
- For v2 (remote I/O): when libcurl is enabled on Windows, the thread-httpserver/dispatch GIL interaction becomes live — either run the server in a child process on Windows too, or add nogil around the samtools/bcftools dispatch call (recorded in the conftest comment and the reconciliation doc).

## Self-Check: PASSED
- .planning/phases/02-portability-tests/02-TEST02-RECONCILIATION.md — FOUND on disk
- tests/AlignmentFile_test.py, tests/conftest.py — FOUND, committed
- commits e4dc435c, 16b05567, d912a1df, 61125c2a — all ancestors of HEAD, VERIFIED
- commits measured from ledger: 4 (git rev-list --count 35808573..61125c2a)
- final suite on current tree: 1027 passed / 15 skipped / exit 0; log.txt absent (clean teardown)

---
*Phase: 02-portability-tests · Plan: 04*
*Completed: 2026-10-12*
