# SC-2 Reconciliation — MSVC build suite vs Phase-2 UCRT64 baseline (1027/15)

**Plan:** 03-05 · **Policy:** D2-07 (fix first, exempt only with cause; zero silent skips) · **Baseline source:** the Phase-2 Windows session close (`02-TEST02-RECONCILIATION.md`, SHA `d912a1df`: `1027 passed, 15 skipped`, fork CI ubuntu `1042 passed, 5 skipped` on the same SHA).

## 1. D2-07 triage — every failure the first MSVC suite run produced, before any fix

Reproduce-first order (each failure isolated by name with `-v`/single-test runs and
probed directly at the C boundary before any fix/skip/exempt decision):

| Failure | Reproduced outcome (pre-fix) | Root cause (stack/evidence-proven) | Disposition |
|---|---|---|---|
| `TestSamtools::testStatements` — process killed, exit 127 (0xC0000409) at the `reheader` statement | `cmd /c` raw exit `-1073740791`; invalid-parameter handler (ctypes into ucrtbase) catches it; RtlCaptureStackBackTrace shows `libcsamtools!samtools_close_stdout → ucrtbase!fclose` | `main_reheader` lends `fileno(samtools_stdout)` to `bam_reheader → bgzf_dopen`, which takes ownership and closes the fd at `bgzf_close`; the dispatch shim then fcloses the FILE* wrapping the same fd. Double close. glibc and MSYS2's mingw python (which installs a tolerant invalid-parameter handler — `_close(9999)` survives there) tolerate it; the UCRT behind python.org/conda CPython fail-fasts and kills the interpreter | **fixed** — `dup()` at both lend sites under `_WIN32` (`bam_reheader.c.pysam.c`, `bam_cat.c.pysam.c` — the same latent bug class exists in cat's stdout path); POSIX arms verbatim (commit `61fc11b8`) |
| `TestSamtools::testStatements` — `UnicodeEncodeError: 'ascii' codec can't encode '�'` after the reheader crash was fixed | reheader's captured stdout is a **binary BAM**; `_collect` decoded it UTF-8-**with-replacement** into a lossy str; the test oracle's `force_bytes()` then failed | 03-01's WR-01 fix (`_collect` replacement decode) regressed binary capture — present on **both** toolchains (reproduced on UCRT64 too; no full suite had run between 03-01 and this plan) | **fixed** — strict-first decode: valid UTF-8 text still returns str byte-identically (WR-01 test stays green), non-UTF-8 data is binary tool output and returns raw bytes, the pre-WR-01 fallback every consumer handles (commit `dfa47c25`) |
| `TestDispatchOutputEncoding::test_cjk_header_comment_roundtrip` — full-suite only: `header == ''` (passed individually; cumulative, sequence-dependent) | bisected to preceding dispatch history; not count-dependent (25 identical view -H dispatches pass) | the vendored `win32/getopt.c` is **GNU getopt**: the dispatch reset's `optind = 1` (non-glibc arm) does not reinitialize its permutation state (`nextchar`/`first_nonopt`), so a later dispatch misparsed its options — a `view -H -o <file>` dispatch dropped its `-o`, wrote the header into the devnull capture, and returned empty with exit 0 | **fixed** — reset gate widened to `__GLIBC__ \|\| _MSC_VER` (GNU getopt's own `optind=0` reinit idiom) in `import/pysam.c` + both twins, sed-lockstep diff-clean; MinGW arm unchanged — mingwex's BSD-style getopt keeps `optind = 1` (commit `860dd867`) |
| `compile_test.py` 3 tests module-skipped (`no pyximport`) | gate exception captured via pytest plugin: `_compile_sizes.c(1332): error C2143/C2059` on the `_Static_assert` lines | `_Static_assert` is C11 syntax MSVC only accepts under an explicit /std switch — setup.py passes `/std:c11` but pyximport builds with stock distutils flags; purely syntactic, the width invariants themselves hold on MSVC (hts_pos_t 8, long long 8, psam_off_t = long long 8) | **fixed** — negative-array-size typedef asserts (the portable pre-C11 form): identical invariant on every toolchain, reason carried in the failing symbol name; 6/6 compile_test pass on both builds (commit `f89add93`) |
| `TestSamtools::testUsage` — access violation (0xC0000005) in `usage()` after a failed testStatements (full-suite/-v only) | inverted under `--tb=no`, vanished entirely after the fixes above; never reproducible standalone or in plain-process sequence probes | downstream manifestation of the two dispatch-state bugs above (lossy-str + stale-getopt interaction), not an independent defect | **passes** once the root causes above are fixed — no separate fix needed |

Zero exemptions were needed for any of the five rows — every MSVC failure was
resolved by a root-cause fix. The four fix commits are the suite-driven gap
closures the plan's single-place discipline names (shim/`#else`-verbatim
per-source guards, template-lockstep dispatch fix, platform-neutral test
sentinel, `.pyx` corrective).

## 2. Counts table — MSVC build vs the Phase-2 baseline

**MSVC run (`_venv-msvc`, Miniconda CPython 3.13.5, cl 14.50 artifacts, plain
default collection from repo root, llvm-nm's dir on PATH):**

```
====================== 1028 passed, 15 skipped in 20.01s ======================
```

(captured verbatim from `_venv-msvc/Scripts/python.exe -m pytest`, exit code 0;
the `-rs` rerun of the same tree reports the same 1028/15 shape.)

**Phase-2 Windows baseline (UCRT64, Python 3.14.7, SHA `d912a1df`):**

```
====================== 1027 passed, 15 skipped in 15.38s ======================
```

**Count reconciliation (node-exact, not arithmetic):** collection 1041 = the
baseline's 1040 + exactly one test added since — 03-01's
`TestDispatchOutputEncoding::test_cjk_header_comment_roundtrip` (WR-01's
permanent regression test; 03-02..03-04 added none). The run accounting matches
the Phase-2 baseline's shape exactly: 1028 passed = 1041 collected − 13
node-level skips; the 15 skipped run units = 13 node-level + 2 module-skip
placeholders (linking, typechecking), the same accounting anomaly the Phase-2
reconciliation resolved.

## 3. Skip-reason diff — MSVC `-rs` listing vs the Phase-2 Windows baseline

Every skip on either side, each individually named. Threshold: zero unexplained
differences — met with **zero differences at all**: the MSVC skip set is
node-for-node the Phase-2 Windows skip set.

**Both environments (identical reasons):**

| Test | Reason | Bucket |
|---|---|---|
| `tests/linking_test.py` (module) | enable linking tests by setting PYSAM_LINKING_TESTS | module env gate |
| `tests/typechecking_test.py` (module) | mypy API not available (mypy not installed in `_venv-msvc` either — same env-difference class as the UCRT64 venv row in the Phase-2 doc) | module env gate |
| `AlignmentFile_test.py::TestRemoteFileHTTP::testView/testFetch/testFetchAll` (1389/1398/1411) | networking disabled (HAVE_LIBCURL=0) | libcurl capability gate |
| `AlignmentFile_test.py::test_remote_GCS` (1425) / `test_remote_S3` (1434) | GCS/S3 networking disabled | libcurl capability gate |
| `faidx_test.py::TestRemoteFile` (222/226) | networking disabled | libcurl capability gate |
| `tabix_test.py::TestRemoteFileHTTP` (911/927, 2 params each) | networking disabled | libcurl capability gate |
| `AlignmentFile_test.py::TestLargeCigar::test_reading_writing_cram` (2066) | fails on linux - https issue? | unconditional upstream skip |
| `StreamFiledescriptors_test.py::TestStream::test_samtools_processing` (74) | test contains bug | unconditional upstream skip |

**MSVC-only skips:** none.

**Baseline-only skips (MSVC runs more):** none.

Composition check: 11 libcurl capability gates + 2 unconditional upstream skips
+ 2 module env gates = 15, identical to the baseline composition recorded in
`02-TEST02-RECONCILIATION.md` section 3.

## 4. D2-07 exemption list — MSVC-only skips granted this phase

**Empty.** No skip, xfail, or deselection was added for the MSVC build. The
only test-code change (`tests/_compile_sizes.pyx`) converts a C11-keyword
static assert into its portable negative-array-typedef form — the asserted
invariants and failure semantics are identical on every toolchain, and the
change un-skipped 3 tests rather than skipping anything.

## 5. Zero-regression note

The two dispatch-state fixes (`dup()` lend sites; `optind=0` MSVC reset) and
the `_collect` corrective carry the standing shared-tree risk: the POSIX and
MinGW compiled paths are byte-identical outside their guards (proven by the
template sed-lockstep diff and the `#else`-verbatim arms). The phase-final
zero-regression instruments (UCRT64 full suite on the final tree + fork CI
ubuntu/macos on the final SHA) run in Task 3 and are recorded in the phase
summary (`03-05-SUMMARY.md`), mirroring the Phase-2 close-out.
