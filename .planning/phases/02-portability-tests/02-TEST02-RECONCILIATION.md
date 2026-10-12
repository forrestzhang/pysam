# TEST-02 Reconciliation — Windows session vs fork CI ubuntu baseline

**Plan:** 02-04 · **Policy:** D2-07 (fix first, exempt only with cause; zero silent skips) · **Baseline source:** fork CI ubuntu job on the same commit SHA (upstream #1274's older-version log is NOT used anywhere — different pysam version; its digit count is deliberately not quoted here).

## 1. D2-07 triage baseline — the four upstream-known failures

Reproduce-first order (run by name, `-v`, UCRT64 session, Python 3.14.7, before any fix/skip/exempt decision):

| Test | Reproduced outcome (pre-fix) | Disposition |
|------|------------------------------|-------------|
| `TestIO::testReadingFromFileWithoutIndex` | PASSED (correct data generation was all it needed — 02-03 finding confirmed) | **passes — no work** |
| `TestLogging::testFail1` | test body PASSED; teardown ERROR `PermissionError: [WinError 32]` on `os.unlink('log.txt')` | **fixed** — see below |
| `TestLogging::testNoFail1` | same teardown ERROR | **fixed** — see below |
| `TestLogging::testNoFail2` | same teardown ERROR | **fixed** — see below |

**TestLogging root cause (fix-first, not an exemption):** `check()` created a
`logging.FileHandler('log.txt')` and never closed it. POSIX allows unlinking an
open file (the inode lives on), so upstream never noticed the leak; Windows
cannot delete a file held open by any handle — hence WinError 32 in
`teardown_method`. The fix closes and removes the handler after the pileup —
a strict hygiene improvement and a behavioral no-op on POSIX (handler lifetime
is otherwise invisible to the assertions). No `.pyx` change was needed; the
C-level stderr noise (`[E::bgzf_read] ... error 4` on `ex9_fail.bam` pileup)
belongs to the expected htslib error path the test intentionally exercises
and does not affect the result.

**Post-fix evidence** (`pytest tests/AlignmentFile_test.py -k "TestLogging or
testReadingFromFileWithoutIndex" -v`): `4 passed, 365 deselected in 0.16s`,
teardown clean, `log.txt` absent after the run.

## 2. Counts table — both platforms, same SHA

*(populated in Task 3 — the Windows line comes from Task 2's captured summary; the ubuntu line from the fork CI job log on the phase-final SHA; both quoted verbatim from captured output, never model-recalled)*

## 3. Skip-reason diff — Windows `-rs` listing vs ubuntu job

*(populated in Task 3 — every line is "both platforms (identical reason)" or "Windows-only: <test> — <written cause>" linking to the exemption entry below; threshold: zero unexplained differences)*

## 4. D2-07 exemption list — Windows-only skips/xfails granted this phase

**Zero exemptions granted so far.** Every Windows-only skip observed to date is
pre-existing on both platforms or libcurl-gated per the v1 pre-locked
constraint (remote-I/O skipif sites, linking environment gate, tty-gated usage
tests, `test_samtools_processing`). Any skip discovered in Task 2's full-suite
drive that is NOT in those pre-existing classes will be added here with test
id, written cause, evidence pointer, and decision date — or fixed instead.

| Test id | Cause (written) | Evidence | Date |
|---------|-----------------|----------|------|
| *(none — the four D2-07 checklist names above were all resolved by pass/fix)* | | | |
