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

**Windows session (UCRT64, Python 3.14.7, default collection, phase-final working tree):**

```
====================== 1027 passed, 15 skipped in 15.22s ======================
```

(captured verbatim from `_venv/bin/python.exe -m pytest -rs`, exit code 0; the
first plain run of the same tree reported `1027 passed, 15 skipped in 16.30s`).
Collection count: `1040 tests collected in 2.46s`.

Collection-drift finding (investigated per plan): research baseline was 1028;
this phase itself added 12 test functions (`tests/PortabilityRegression_test.py`
×11 — D2-08/D2-10 regression suite — plus `test_compile_sizes_static_asserts`
in `tests/compile_test.py` — D2-09), zero removed: 1028 + 12 = 1040. Zero
duplicate node ids, zero deselected; every parseable run id is a subset of the
collected ids. Observed anomaly, investigated and recorded: the run summary
counts 1042 executions (1027 passed + 15 skipped) against 1040 collected; 52
`-v` status lines are absent from the run log in parseable form because
dispatch fd-1 redirection swallows them mid-run (the documented `-s` capture
constraint) — deselection and duplication, the gate's failure modes, are both
empirically excluded.

**fork CI ubuntu job (same commit SHA):** *(populated in Task 3 from the job
log on the phase-final SHA — quoted verbatim, never model-recalled)*

## 3. Skip-reason diff — Windows `-rs` listing vs ubuntu job

Windows `-rs` listing, complete (15 skips, each with its printed reason):

| Site (as printed) | Reason (as printed) | Class |
|---|---|---|
| `tests/linking_test.py:13` | enable linking tests by setting PYSAM_LINKING_TESTS environment variable | env gate (opt-in on both platforms) |
| `tests/typechecking_test.py:17` | mypy API not available | env gate (dependency absent) |
| `tests/AlignmentFile_test.py:1389` | networking disabled | libcurl-gated remote I/O (v1 pre-locked) |
| `tests/AlignmentFile_test.py:1398` | networking disabled | libcurl-gated remote I/O |
| `tests/AlignmentFile_test.py:1411` | networking disabled | libcurl-gated remote I/O |
| `tests/AlignmentFile_test.py:1425` | GCS networking disabled | libcurl-gated remote I/O |
| `tests/AlignmentFile_test.py:1434` | S3 networking disabled | libcurl-gated remote I/O |
| `tests/AlignmentFile_test.py:2066` | fails on linux - https issue? | unconditional upstream skip, both platforms |
| `tests/StreamFiledescriptors_test.py:74` | test contains bug | unconditional upstream skip, both platforms |
| `tests/faidx_test.py:222` | networking disabled | libcurl-gated remote I/O |
| `tests/faidx_test.py:226` | networking disabled | libcurl-gated remote I/O |
| `tests/tabix_test.py:911` ×2 | networking disabled | libcurl-gated remote I/O (parametrized pair) |
| `tests/tabix_test.py:927` ×2 | networking disabled | libcurl-gated remote I/O (parametrized pair) |

*(ubuntu-side diff of these rows against the job log is completed in Task 3;
every row must end as "both platforms (identical reason)" or gain an exemption
entry below.)*

## 4. D2-07 exemption list — Windows-only skips/xfails granted this phase

**Zero exemptions granted.** The four D2-07 checklist names were all resolved
by pass/fix (section 1). All 15 skips in the Windows run belong to pre-existing
classes present on both platforms (unconditional upstream skips, opt-in env
gates) or to the v1 pre-locked libcurl-disabled constraint (remote-I/O skipif
sites — expected Windows skips per CONTEXT). Audit evidence: phase 02's whole
diff (`c3541873..HEAD`) added exactly one skip mark — the conditional
`@pytest.mark.skipif(NO_PYXIMPORT, reason="no pyximport")` (02-02, D2-09
gate) — removed none, and touched neither pre-existing unconditional skip
(`AlignmentFile_test.py` "fails on linux", `StreamFiledescriptors_test.py`
"test contains bug", both present verbatim at the phase-start commit).

| Test id | Cause (written) | Evidence | Date |
|---------|-----------------|----------|------|
| *(none — zero Windows-only skips exist beyond the pre-existing/pre-locked classes)* | | | |

