---
phase: 02-portability-tests
plan: 03
subsystem: testing
tags: [windows, test-infrastructure, data-generators, in-process-oracle, threading-httpserver, ref-path, epipe, longjmp, d2-05, d2-06, test-01]

requires:
  - phase: 02-portability-tests plan 01
    provides: canonical UCRT64 rebuild contract + smoke gate
  - phase: 02-portability-tests plan 02
    provides: binary-safe fd I/O (psam_open/tabix_compress) and wide-char opens the generators rely on
provides:
  - tests/{pysam_data,tabix_data,cbcf_data}/make_data.py — Python generators mirroring every Makefile rule via pysam dispatch/tabix_compress/stdlib gzip (D2-06)
  - TestUtils.make_data_files sys.platform=='win32' dispatch (importlib file-location load; POSIX make line byte-identical)
  - spawn-safe threading httpserver fixture + REF_PATH=os.pathsep conftest
  - In-process comparison rewrites for PileupTestUtils pipe family, samtools_test, StreamFiledescriptors, TestSAMFromStringIO (D2-05)
  - Two Windows C-layer portability fixes — htslib fd_write EPIPE (was raise(SIGTERM)), dispatch exit interception (UCRT longjmp STATUS_BAD_STACK → GCC builtins)
affects: [02-04 suite green + D2-07 triage + fork-CI closure, phase-3-msvc, phase-4-ci]

actuals:
  tokens: 8055       # chars/4 over the realized diff (32221 chars, 12 files)
  tasks: 3
  commits: 5         # MEASURED: git rev-list --count ca81c2e2..HEAD
plan_head_before: ca81c2e204c56abab29aadcac243bc30f261302
plan_head_after: 7f22519d1842757f9eccb2311780a49fa235ca62

tech-stack:
  added: []
  patterns:
    - "Per-directory Python data generators behind make_data_files platform dispatch — Makefile stays the POSIX spec, generator mirrors it rule-for-rule with decision-ID comments"
    - "Dispatch stdout normalisation: raw=True only bypasses parsers; the collector returns str for text output and bytes only when text-mode read raises UnicodeDecodeError — encode via _as_bytes helper"
    - "Windows dispatch exit interception via GCC __builtin_setjmp/__builtin_longjmp (no SEH unwind) — UCRT longjmp's RtlUnwindEx raises STATUS_BAD_STACK over this module's GCC frames"

key-files:
  created:
    - tests/pysam_data/make_data.py
    - tests/tabix_data/make_data.py
    - tests/cbcf_data/make_data.py
  modified:
    - tests/TestUtils.py
    - tests/conftest.py
    - tests/PileupTestUtils.py
    - tests/samtools_test.py
    - tests/StreamFiledescriptors_test.py
    - tests/AlignmentFile_test.py
    - htslib/hfile.c
    - samtools/samtools.pysam.c
    - bcftools/bcftools.pysam.c

key-decisions:
  - "Generators capture dispatch stdout via the RETURN VALUE (catch_stdout=True + raw=True + _as_bytes), never save_stdout — the return path is the proven byte-faithful one; dispatch 'raw' only bypasses parsers and does not force bytes"
  - "with_md.bam is written directly from calmd's captured BAM stdout (POSIX reaches the same records through the with_md.sam.gz→with_md.sam→view -bo chain; consumers read them, nothing byte-compares the pair)"
  - "htslib fd_write's Windows raise(SIGTERM)-on-broken-pipe kills the CPython host (CPython sets SIGPIPE to SIG_IGN on POSIX, so POSIX never dies); patch reports errno EPIPE instead — identical error flow on every platform, POSIX block untouched"
  - "samtools/bcftools dispatch exit interception crashes with STATUS_BAD_STACK (0xC0000028) under UCRT longjmp's RtlUnwindEx despite full .pdata coverage; _WIN32 branch switches to GCC __builtin_setjmp/__builtin_longjmp (direct register restore, no unwind), POSIX keeps setjmp/longjmp verbatim"
  - "samtools_test win32 branch: redirect statements capture dispatch output to the target file; -o statements run with catch_stdout=False letting samtools' own output handling write files — the three-tier comparison ladder runs unchanged"

patterns-established:
  - "make-rule-to-dispatch mapping table (view -bo/index/calmd/mpileup/faidx, tabix_compress, tabix_index presets, bcftools view/index) reusable for any future fixture"
  - "sys.executable -c inline consumer as the cross-platform pipe-drainer replacing POSIX text utilities in tests"

requirements-completed: [TEST-01]

coverage:
  - id: D1
    description: "make_data_files win32 dispatch + pysam_data generator: full fixture set from committed inputs, idempotent via all.stamp, POSIX make line byte-identical (D2-06)"
    requirement: TEST-01
    verification:
      - kind: integration
        ref: "UCRT64: rm all.stamp → make_data_files(BAM_DATADIR) → 'generated'; ex1.bam fetch(until_eof)==3270; artifacts-ok (truncated/corrupt/empty/ex3.cram/pileup/stamp); second run 'idempotent-ok'"
        status: pass
      - kind: other
        ref: "git diff tests/TestUtils.py — make invocation line unchanged (added branch only); git ls-files --error-unmatch tests/pysam_data/make_data.py (force-added)"
        status: pass
    human_judgment: false
  - id: D2
    description: "tabix_data + cbcf_data generators (tabix presets, bcftools view/index chains) — compile_test.py, the module blocked on all three dirs, passes"
    requirement: TEST-01
    verification:
      - kind: integration
        ref: "UCRT64: _venv/bin/python.exe -m pytest tests/compile_test.py → 6 passed (setUpModule exercises all three generators)"
        status: pass
      - kind: other
        ref: "git ls-files --error-unmatch tests/tabix_data/make_data.py tests/cbcf_data/make_data.py; both contain def generate, no subprocess"
        status: pass
    human_judgment: false
  - id: D3
    description: "Spawn-safe conftest: threading httpserver (QuietHTTPServer classes and ('localhost', 0) bind verbatim) + REF_PATH=os.pathsep; zero multiprocessing references"
    requirement: TEST-01
    verification:
      - kind: integration
        ref: "direct probe: _build_httpd + daemon thread served tests/pysam_data/ex1.fa byte-identical (3281 bytes) over localhost, clean shutdown; pytest faidx -k selection → 2 passed (remote pair libcurl-skipped by pre-existing gates)"
        status: pass
      - kind: other
        ref: "grep -c multiprocessing tests/conftest.py → 0; os.pathsep → 2; bind line ('localhost', 0) intact"
        status: pass
    human_judgment: false
  - id: D4
    description: "In-process comparison rewrites: four collected PileupTestUtils builders, samtools_test check_version/check_statement, StreamFiledescriptors sys.executable consumer, TestSAMFromStringIO dispatch (D2-05)"
    requirement: TEST-01
    verification:
      - kind: integration
        ref: "UCRT64: pytest tests/AlignmentFilePileup_test.py → 32 passed; tests/samtools_test.py → 15 passed; TestStream/TestSAMFromStringIO selection → 20 passed 1 skipped (pre-existing skip)"
        status: pass
      - kind: other
        ref: "grep gates: samtoolspysam|samtools.mpileup=9 (>=5), shutil.which=2 (>=1), 'head -n200'=0; no new pytest.mark.skip in the task diff"
        status: pass
    human_judgment: false
  - id: D5
    description: "Two Windows C-layer portability fixes required by the rewrites: fd_write EPIPE reporting (was raise(SIGTERM) killing the interpreter) and dispatch exit interception (was STATUS_BAD_STACK crash)"
    requirement: TEST-01
    verification:
      - kind: other
        ref: "VEH probe captured 0xC0000028 at ntdll+0x1D3DF pre-fix; post-fix all 16 usage() probes rc=0 incl. depth/flagstat/stats/idxstats/reheader; concurrent pipe probe EXIT=0 with reader=198, clean writer close"
        status: pass
      - kind: integration
        ref: "tests/StreamFiledescriptors_test.py::TestStream::test_text_processing PASSED (real subprocess fd pipe, EPIPE-tolerant writer, read==198)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Zero POSIX regression: Makefiles untouched, TestUtils else-branch byte-identical, samtools_test POSIX run_command oracle verbatim; hfile.c/pysam.c changes confined to _WIN32 guards"
    verification:
      - kind: other
        ref: "git diff ca81c2e2..HEAD — no Makefile under tests/*/ touched; all C edits inside #ifdef _WIN32 with #else carrying the original lines verbatim"
        status: pass
    human_judgment: true
    rationale: "Formal proof is the fork CI ubuntu/macos run on the pushed commits; local executor cannot run Linux CI. Assigned to Plan 02-04 by the phase plan (commits local on 'win' until push)."

duration: 54 min
completed: 2026-10-12
status: complete
---

# Phase 2 Plan 3: Test Infrastructure Windows Port Summary

**Platform-dispatched Python data generators (three Makefile-mirroring make_data.py modules behind make_data_files), spawn-safe threading conftest with os.pathsep REF_PATH, in-process comparison rewrites for every collected shell-out test, plus two Windows C-layer fixes — htslib raise(SIGTERM)-on-EPIPE and UCRT longjmp STATUS_BAD_STACK in dispatch exit interception**

## Performance

- **Duration:** 54 min
- **Started:** 2026-10-12T06:04:49Z
- **Completed:** 2026-10-12T06:58:49Z
- **Tasks:** 3
- **Files modified:** 12 (3 created, 9 modified)

## Accomplishments
- **Generators (D2-06):** `tests/pysam_data/make_data.py` mirrors every Makefile rule — ex1.bam via `-t ex1.fa.fai` from headerless ex1.sam.gz (3270 records), CRAM via `-T ex1.fa` (which also supplies the @SQ dictionary for headerless input — empirically confirmed), calmd stdout capture for with_md, empty.bam as a zero-record AlignmentFile write from ex2.sam's @-lines, pure-Python truncate/corrupt rules, bgzip-vs-plain-gzip fidelity (fa.gz via tabix_compress, fq.gz via stdlib gzip), all.stamp idempotency. `tabix_data` (bgzip + tabix presets bed/gff/sam/vcf) and `cbcf_data` (bgzip + .tbi + .csi + view -O b + .bcf.csi per *.vcf, example_empty excluded like the Makefile filter) follow the same pattern. No subprocess, no shell, no network; committed inputs read-only; force-added past the whole-dir gitignore.
- **conftest:** threading httpserver (daemon `serve_forever` thread, no child process, no pipe handshake; QuietHTTPServer/QuietRequestHandler classes and the `("localhost", 0)` ephemeral bind kept verbatim; teardown `shutdown()` + `server_close()` in try/finally) and `REF_PATH = os.pathsep` (matches `HTS_PATH_SEPARATOR_CHAR ';'` on `_WIN32`, hts.h:44-51).
- **In-process rewrites (D2-05):** four collected PileupTestUtils builders now parse `pysam.samtools.mpileup` dispatch output with their original column/type semantics (bench-only pipe/shell builders untouched per D2-11); samtools_test gates check_version on `shutil.which` and produces win32-side targets via the same dispatch method (redirect→capture-to-file, -o→catch_stdout=False) with the POSIX `run_command` oracle verbatim; StreamFiledescriptors drains the pipe with a `sys.executable -c` 200-line consumer (list form, no shell; `read == 198` and EPIPE-tolerant writer intact); TestSAMFromStringIO uses `pysam.samtools.view`.
- **Two Windows C-layer root-cause fixes** (the tests cannot pass without them, see Deviations 5-6): htslib `fd_write` reported EPIPE instead of raising SIGTERM, and dispatch exit interception switched to GCC builtins under `_WIN32`.
- Final combined run of all touched modules plus regressions: **422 passed, 7 skipped (all pre-existing env gates), 3 errors — exactly the D2-07 TestLogging trio** (teardown errors), recorded for 02-04. `TestIO::testReadingFromFileWithoutIndex` — the fourth #1274 known failure — **passes** on this build (correct data generation was what it needed).

## Task Commits

1. **Task 1: make_data_files win32 dispatch + pysam_data generator (tracer)** - `089d31b1` (feat)
   - tracer-gate Rule 1 fix: `c338039b` (tabix_compress force=True — the gate's re-run caught the overwrite failure)
2. **Task 2: tabix/cbcf generators + spawn-safe conftest** - `1957e33f` (feat)
3. **Task 3: in-process comparison rewrites** - `6c059cc2` (fix: hfile.c + both .pysam.c dispatch files) + `7f22519d` (test: four test files)

**Plan metadata:** this commit (docs)

## Files Created/Modified
- `tests/pysam_data/make_data.py` / `tests/tabix_data/make_data.py` / `tests/cbcf_data/make_data.py` - generate(directory) mirroring each Makefile (D2-06)
- `tests/TestUtils.py` - win32 branch (importlib file-location load) before any make invocation; POSIX line untouched
- `tests/conftest.py` - threading httpserver + REF_PATH=os.pathsep
- `tests/PileupTestUtils.py` - four samtoolspipe builders → mpileup-dispatch parsers
- `tests/samtools_test.py` - shutil.which-gated check_version; platform-guarded check_statement
- `tests/StreamFiledescriptors_test.py` - sys.executable pipe consumer
- `tests/AlignmentFile_test.py` - TestSAMFromStringIO in-process
- `htslib/hfile.c` - fd_write _WIN32 block: errno=EPIPE instead of raise(SIGTERM)
- `samtools/samtools.pysam.c` / `bcftools/bcftools.pysam.c` - _WIN32 __builtin_setjmp/__builtin_longjmp exit interception

## Decisions Made
See key-decisions in frontmatter. Additional in-flight findings:
- Dispatch `raw=True` does NOT force bytes — it only bypasses output parsers; the collector (`_collect` in libcutils.pyx) returns str when the text-mode read succeeds and bytes only on UnicodeDecodeError (binary output). Generators normalise through `_as_bytes`.
- `pysam.bcftools` is not imported by `import pysam` (only `pysam.samtools` is star-imported); the cbcf generator imports the submodule explicitly, matching tests/samtools_test.py's own import.
- BGZF block-boundary flagged assumption (research Open Question 3) RESOLVED: ex2_truncated.bam and ex2_corrupt.bam consumers are read-based — AlignmentFile_test.py:1195-1227 expects IOError during iteration on both; verified on the generated files (both raise as required). tabix_compress re-compression is acceptable.
- The httpserver-consuming pysam tests (faidx/AlignmentFile/tabix remote tests) are all libcurl-gated (HAVE_LIBCURL=0) and skip on this build by design (v1: libcurl disabled); the threading server itself is proven byte-faithful over HTTP by a direct stdlib-urllib probe against the same `_build_httpd` the fixture uses.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] dispatch raw=True returned str for view -h / mpileup output**
- **Found during:** Task 1 (first generation run)
- **Issue:** Generator wrote dispatch output to gzip binary handles; `TypeError: a bytes-like object is required` — raw=True only bypasses parsers, the collector decodes text output to str.
- **Fix:** `_as_bytes()` helper (str→utf-8 encode, bytes passthrough) at all three capture sites.
- **Files modified:** tests/pysam_data/make_data.py
- **Verification:** full generation run green; ex2.sam.gz/ex1.pileup.gz/with_md.bam all readable.
- **Committed in:** 089d31b1

**2. [Rule 1 - Bug] tabix_compress refused to overwrite existing targets (retry path broken)**
- **Found during:** Task 1 tracer feedback gate (the gate did its job — the initial verify passed only because artifacts did not yet exist)
- **Issue:** Deleting all.stamp while artifacts remain (the retry/refresh path) raised `IOError: already exists, use *force*` for ex2_corrupt.bam/ex1.fa.gz; make rules always overwrite targets.
- **Fix:** `force=True` on both tabix_compress calls.
- **Files modified:** tests/pysam_data/make_data.py
- **Verification:** full tracer verify suite re-run end-to-end: generated / reads: 3270 / artifacts-ok / idempotent-ok.
- **Committed in:** c338039b

**3. [Rule 3 - Blocking] pysam.bcftools not reachable via `import pysam`**
- **Found during:** Task 2 (first cbcf generation)
- **Issue:** `AttributeError: module 'pysam' has no attribute 'bcftools'` — the bcftools dispatch submodule needs explicit import.
- **Fix:** `import pysam.bcftools` in cbcf_data/make_data.py (mirrors tests/samtools_test.py:12).
- **Files modified:** tests/cbcf_data/make_data.py
- **Verification:** both dirs generate; compile_test.py 6 passed.
- **Committed in:** 1957e33f

**4. [Rule 1 - Literal gate] conftest comment contained the word "multiprocessing"**
- **Found during:** Task 2 verify
- **Issue:** The plan's gate is `grep -c "multiprocessing" == 0`; the rewrite's explanatory comment tripped it (no actual usage remained).
- **Fix:** Comment reworded to "child-process start method".
- **Files modified:** tests/conftest.py
- **Verification:** grep count 0; threading/os.pathsep/bind-line gates all pass.
- **Committed in:** 1957e33f

**5. [Rule 1 - Bug] htslib fd_write raise(SIGTERM) killed the interpreter on broken-pipe writes**
- **Found during:** Task 3 (TestStream::test_text_processing died with exit 3, no traceback)
- **Issue:** hfile.c's _WIN32 fd_write block raises SIGTERM to emulate SIGPIPE's default action; CPython (which sets SIGPIPE to SIG_IGN on POSIX, so Linux never dies here) has no SIGTERM handler — the whole pytest process terminated (CRT abort exit 3) the moment the pipe consumer exited and the SAM writer flushed into a broken pipe.
- **Fix:** Under _WIN32, set `errno = EPIPE` and return the error — the exact POSIX write(2) failure mode — so callers see the same IOError/EPIPE flow on every platform. POSIX block untouched.
- **Files modified:** htslib/hfile.c
- **Verification:** concurrent pipe probe EXIT=0 (reader 198 records, writer thread catches EPIPE, clean close); test_text_processing passes; smoke OK; PortabilityRegression 11 passed.
- **Committed in:** 6c059cc2

**6. [Rule 1 - Bug] dispatch exit interception crashed with STATUS_BAD_STACK under UCRT longjmp**
- **Found during:** Task 3 (samtools_test TestSamtools::testUsage died 0xC0000028)
- **Issue:** usage() of depth/flagstat/stats/idxstats/reheader (every command whose usage path calls samtools_exit) crashed the interpreter: UCRT longjmp unwinds via RtlUnwindEx, which raised STATUS_BAD_STACK (captured by a vectored exception handler at ntdll+0x1D3DF) walking this module's GCC-compiled frames — despite .pdata covering 100% of .text (verified). The setjmp/longjmp pair lives in one translation unit, so GCC's `__builtin_setjmp`/`__builtin_longjmp` (direct register restore, no SEH unwind) is a safe replacement.
- **Fix:** `_WIN32` branches in samtools.pysam.c and bcftools.pysam.c use the builtins with a `void *jmpbuf[5]` buffer; POSIX keeps standard setjmp/longjmp verbatim.
- **Files modified:** samtools/samtools.pysam.c, bcftools/bcftools.pysam.c
- **Verification:** all 16 usage() subprocess probes rc=0 (five previously crashing); samtools_test.py 15 passed.
- **Committed in:** 6c059cc2

---

**Total deviations:** 6 auto-fixed (5 Rule 1 bugs, 1 Rule 3 blocker)
**Impact on plan:** Deviations 1-4 were test-infrastructure mechanics. Deviations 5-6 are the substantive porting work Task 3's action text authorizes ("root-caused and fixed here") — two Windows-only C-layer defects in the dispatch/htslib seam that no amount of Python-side rewriting could bypass; both are `#ifdef _WIN32`-guarded with the POSIX lines preserved verbatim. No scope creep.

## Issues Encountered
- My own win32 samtools-side capture logic initially inverted the flag (`catch_stdout=not redirect`) — redirect statements printed to real stdout and returned None; corrected to `catch_stdout=redirect` before commit (probe showed byte-identical 553335-byte outputs both sides; never landed broken).
- The UCRT64 login shell has no git on PATH — git-based verify commands run from the outer Git Bash shell.
- Residual platform failures (documented for 02-04 per D2-07, zero silent skips): TestLogging::testFail1/testNoFail1/testNoFail2 — teardown ERROR with `[E::bgzf_read] Read block operation failed with error 4 after 0 of 4 bytes` in the session log (combined run `/tmp/pv4.log` equivalent: 422 passed / 7 pre-existing env skips / these 3 errors). The fourth #1274 known failure, TestIO::testReadingFromFileWithoutIndex, PASSES on this build.
- All 7 skips in the combined run are pre-existing platform/env gates (test_samtools_processing "test contains bug", 3 libcurl HTTP tests, GCS, S3, large-cigar CRAM) — none added by this task.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: behavior-change-windows-only | htslib/hfile.c, samtools/samtools.pysam.c, bcftools/bcftools.pysam.c | Two _WIN32-only behavior changes in the C layer (EPIPE reporting instead of a raised SIGTERM; register-restore longjmp instead of SEH-unwinding longjmp). Both are net reductions of abrupt-termination behavior inside an embedded interpreter; no new input surface, no shell, no network. T-02-06's "rewrite is itself the mitigation" applies. |

## Known Stubs

None — no placeholder data, no unwired consumers, no unrun verifies.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for Plan 02-04: whole-suite green drive. The D2-07 reproduce-first triage has evidence waiting (TestLogging trio with bgzf_read error 4); the suite's data generation, collection, and comparison machinery now all work on Windows.
- Fork CI ubuntu/macos on the pushed commits remains the formal POSIX zero-regression closure (assigned to 02-04 by the phase plan).
- Rebuild contract reminder: htslib/.pysam.c C edits require `HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl MAKE=mingw32-make _venv/bin/python.exe setup.py build_ext --inplace --force`.

## Self-Check: PASSED
- tests/pysam_data/make_data.py, tests/tabix_data/make_data.py, tests/cbcf_data/make_data.py — FOUND on disk
- tests/TestUtils.py, tests/conftest.py, tests/PileupTestUtils.py, tests/samtools_test.py, tests/StreamFiledescriptors_test.py, tests/AlignmentFile_test.py — FOUND, committed
- htslib/hfile.c, samtools/samtools.pysam.c, bcftools/bcftools.pysam.c — FOUND, committed
- commits 089d31b1, c338039b, 1957e33f, 6c059cc2, 7f22519d all ancestors of HEAD — VERIFIED below
- commits measured from ledger: 5 (git rev-list --count ca81c2e2..HEAD)

---
*Phase: 02-portability-tests · Plan: 03*
*Completed: 2026-10-12*

<!-- self-check appended post-commit: all 12 files FOUND on disk; commits 089d31b1 c338039b 1957e33f 6c059cc2 7f22519d 6358b5e4 all ancestors of HEAD; ledger count 5 == frontmatter commits -->
