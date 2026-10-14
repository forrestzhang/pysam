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
and does not affect the result (the same stderr line appears in the ubuntu CI
logs on passing builds).

**Post-fix evidence** (`pytest tests/AlignmentFile_test.py -k "TestLogging or
testReadingFromFileWithoutIndex" -v`): `4 passed, 365 deselected in 0.16s`,
teardown clean, `log.txt` absent after the run.

## 2. Counts table — both platforms, same SHA (phase-final code commit `d912a1df`)

**Windows session (UCRT64, Python 3.14.7, default collection, tree at `d912a1df`):**

```
====================== 1027 passed, 15 skipped in 15.38s ======================
```

(captured verbatim from `_venv/bin/python.exe -m pytest`, exit code 0; the
`-rs` rerun of the same tree reported `1027 passed, 15 skipped in 15.22s`).
Collection: `1040 tests collected in 2.46s` (plus two module-level skip
placeholders — linking, typechecking — that execute as skip units, so pytest's
run accounting counts them among the 15 skipped).

**fork CI ubuntu job, direct matrix cell (ubuntu, 3.14) — same SHA `d912a1df`, run 38220111717:**

```
================= 1042 passed, 5 skipped, 2 warnings in 24.65s =================
```

(quoted verbatim from the job log; collection line `collected 1046 items / 1
skipped` — the `/1` is the linking module placeholder). Cell 3.14 chosen to
match the Windows session's Python 3.14.7; the other ubuntu cells report the
same shape (3.11 additionally skips one invalid-access test known to crash
there, `1041 passed, 6 skipped`).

**Node-level reconciliation (both sides enumerated, not estimated):** the
Windows collected-id set (1040) and the ubuntu executed-id set differ in
exactly one module — `tests/typechecking_test.py`, which collects 6 real tests
on ubuntu (mypy installed by ci.yaml) and one module-skip placeholder on
Windows (mypy absent from the UCRT64 venv): 1040 + 6 = 1046. Collection-drift
finding vs the research baseline: this phase itself added 12 test functions
(`tests/PortabilityRegression_test.py` ×11 — D2-08/D2-10 — plus
`test_compile_sizes_static_asserts` — D2-09), zero removed. Zero duplicate
node ids, zero deselected, every parseable Windows run id is a subset of the
collected ids; 52 `-v` status lines are absent from the Windows run log in
parseable form because dispatch fd-1 redirection swallows them mid-run (the
documented `-s` capture constraint) — the gate's failure modes
(deselection/duplication) are empirically excluded.

## 3. Skip-reason diff — Windows `-rs` listing vs ubuntu job (same SHA)

Every skip on either side, each individually named. Threshold per the chosen
mechanics: zero unexplained differences — met.

**Both platforms (identical reason):**

| Test | Reason | Evidence |
|---|---|---|
| `tests/linking_test.py` (module) | enable linking tests by setting PYSAM_LINKING_TESTS environment variable | opt-in env gate; not set in either environment (Windows `-rs` line `tests/linking_test.py:13`; ubuntu collection `/1 skipped`) |
| `tests/AlignmentFile_test.py::TestLargeCigar::test_reading_writing_cram` | fails on linux - https issue? | unconditional upstream skip; SKIPPED line present in both logs |
| `tests/StreamFiledescriptors_test.py::TestStream::test_samtools_processing` | test contains bug | unconditional upstream skip; SKIPPED line present in both logs |

**Windows-only skips (11 + 1 module — each links to an exemption entry in section 4):**

| Test | Reason | ubuntu status |
|---|---|---|
| `tests/AlignmentFile_test.py::TestRemoteFileHTTP::testView` | networking disabled (HAVE_LIBCURL=0) | PASSED |
| `tests/AlignmentFile_test.py::TestRemoteFileHTTP::testFetch` | networking disabled | PASSED |
| `tests/AlignmentFile_test.py::TestRemoteFileHTTP::testFetchAll` | networking disabled | PASSED |
| `tests/AlignmentFile_test.py::test_remote_GCS` | GCS networking disabled (ENABLE_GCS=0) | PASSED |
| `tests/AlignmentFile_test.py::test_remote_S3` | S3 networking disabled (ENABLE_S3=0) | PASSED |
| `tests/faidx_test.py::TestRemoteFile::test_fetch` | networking disabled | PASSED |
| `tests/faidx_test.py::TestRemoteFile::test_sequence_lengths_are_available` | networking disabled | PASSED |
| `tests/tabix_test.py::TestRemoteFileHTTP::testFetchAll[example]` | networking disabled | PASSED |
| `tests/tabix_test.py::TestRemoteFileHTTP::testFetchAll[example_comments]` | networking disabled | PASSED |
| `tests/tabix_test.py::TestRemoteFileHTTP::testHeader[example]` | networking disabled | PASSED |
| `tests/tabix_test.py::TestRemoteFileHTTP::testHeader[example_comments]` | networking disabled | PASSED |
| `tests/typechecking_test.py` (module; 6 real tests on ubuntu) | mypy API not available | PASSED (×6) |

**ubuntu-only skips (Windows runs these — explained, no action):**

| Test | Reason | Windows status |
|---|---|---|
| `tests/samtools_test.py::TestSamtools::testUsage` | skipping usage tests, stdin is not a tty | PASSED (UCRT64 session stdin is a tty) |
| `tests/samtools_test.py::TestPysam::testUsage` | skipping usage tests, stdin is not a tty | PASSED |

Arithmetic check: Windows 1027 passed = 1040 nodes − 13 node-level skips;
ubuntu 1042 passed = 1046 nodes − 4 node-level skips. All deltas accounted
for by the rows above.

## 4. D2-07 exemption list — Windows-only skips/xfails granted this phase

The four D2-07 checklist names were all resolved by pass/fix (section 1) — no
exemption was needed for any of them. The rows below are the Windows-only
skip surface named in section 3, each with its written cause, evidence
pointer, and decision date. Audit evidence: phase 02's whole diff
(`c3541873..HEAD`) added exactly one skip mark — the conditional
`@pytest.mark.skipif(NO_PYXIMPORT, reason="no pyximport")` (02-02, D2-09
gate) — removed none, and touched neither pre-existing unconditional skip.

| Test id | Cause (written) | Evidence | Date |
|---------|-----------------|----------|------|
| `tests/AlignmentFile_test.py::TestRemoteFileHTTP` (testView, testFetch, testFetchAll) | v1 pre-locked libcurl-disabled constraint (PROJECT decision: remote I/O deferred to v2); capability gate `skipif(not HAVE_LIBCURL)` present in upstream code, unchanged by this phase | Windows `-rs` lines `AlignmentFile_test.py:1389/1398/1411`; ubuntu job log: PASSED | 2026-10-12 |
| `tests/AlignmentFile_test.py::test_remote_GCS` / `test_remote_S3` | same v1 constraint (ENABLE_GCS/ENABLE_S3 both derive from libcurl plugins) | Windows `-rs` lines `1425/1434`; ubuntu: PASSED | 2026-10-12 |
| `tests/faidx_test.py::TestRemoteFile` (test_fetch, test_sequence_lengths_are_available) | same v1 constraint | Windows `-rs` lines `faidx_test.py:222/226`; ubuntu: PASSED | 2026-10-12 |
| `tests/tabix_test.py::TestRemoteFileHTTP` (testFetchAll, testHeader × 2 params) | same v1 constraint | Windows `-rs` lines `tabix_test.py:911/927` (SKIPPED [2] each); ubuntu: PASSED | 2026-10-12 |
| `tests/typechecking_test.py` (module) | mypy not installed in the UCRT64 dev venv — test-environment dependency difference, not a pysam platform limitation (the 6 tests exercise typestub annotations only) | Windows `-rs` line `typechecking_test.py:17 mypy API not available`; ci.yaml installs mypy on ubuntu | 2026-10-12 |

## 5. Zero-regression closure — fork CI on the phase-final code commit

- **First push of the phase (`16b05567`, run [38217865780](https://github.com/forrestzhang/pysam/actions/runs/38217865780)): FAILURE** — exactly one test failing on each of `direct (ubuntu, 3.13)`, `sdist (ubuntu, 3.14)`, `system (freebsd)`: `TestRemoteFileHTTP::testView`, `Connection timed out` on the httpserver URL; `conda (ubuntu, 3.13)` (libcurl disabled) green.
- **Root cause (found and fixed in this plan):** 02-03 had replaced the multiprocessing httpserver with a daemon-thread server on all platforms. `_pysam_dispatch` runs the samtools main with the GIL held (`samtools_dispatch` call in `pysam/libcutils.pyx`), so while the dispatch was blocked in libcurl waiting for the HTTP response, the in-process server thread could never run to answer — hence the timeout. The non-dispatch remote tests (libchtslib releases the GIL) passed, and a child-process server is immune — which is why upstream never saw this.
- **Fix (commit `d912a1df`):** `tests/conftest.py` platform-split — POSIX branch restores upstream's `_httpd` + fixture body verbatim (byte-identical tokens, guard-required indentation only); win32 keeps the spawn-safe threading variant (02-03 decision; all libcurl-gated remote tests skip on that build, so the GIL interaction is unreachable there).
- **Phase-final verdict (run [38220111717](https://github.com/forrestzhang/pysam/actions/runs/38220111717) on `d912a1df`): SUCCESS — all 19 jobs green**, including `direct (ubuntu, 3.9–3.15-dev)` ×7 cells, `direct (macos, 3.9–3.15-dev)` ×7 cells, `sdist (ubuntu/macOS, 3.14)`, `conda (ubuntu, 3.13)`, `system (freebsd/netbsd)` (BSD advisory per Phase 1 D-12 — also green). Zero-regression closed across all of phase 02 (`c3541873..d912a1df`).
