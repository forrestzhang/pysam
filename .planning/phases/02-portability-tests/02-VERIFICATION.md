---
phase: 02-portability-tests
verified: 2026-10-12T10:09:53Z
status: passed
score: 23/23 must-haves verified
covered_files:
  - .planning/phases/02-portability-tests/02-01-PLAN.md
  - .planning/phases/02-portability-tests/02-01-SUMMARY.md
  - .planning/phases/02-portability-tests/02-02-PLAN.md
  - .planning/phases/02-portability-tests/02-02-SUMMARY.md
  - .planning/phases/02-portability-tests/02-03-PLAN.md
  - .planning/phases/02-portability-tests/02-03-SUMMARY.md
  - .planning/phases/02-portability-tests/02-04-PLAN.md
  - .planning/phases/02-portability-tests/02-04-SUMMARY.md
  - .planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md
  - .planning/phases/02-portability-tests/02-PORT02-AUDIT.md
  - .planning/phases/02-portability-tests/02-TEST02-RECONCILIATION.md
  - bcftools/bcftools.pysam.c
  - htslib/hfile.c
  - htslib/hts.c
  - pysam/libchtslib.pxd
  - pysam/libchtslib.pyx
  - pysam/libcport.pxd
  - pysam/libctabix.pyx
  - pysam/libcutils.pyx
  - samtools/samtools.pysam.c
  - tests/AlignmentFile_test.py
  - tests/PileupTestUtils.py
  - tests/PortabilityRegression_test.py
  - tests/StreamFiledescriptors_test.py
  - tests/TestUtils.py
  - tests/_compile_sizes.pyx
  - tests/_compile_sizes.pyxbld
  - tests/cbcf_data/make_data.py
  - tests/compile_test.py
  - tests/conftest.py
  - tests/pysam_data/make_data.py
  - tests/samtools_test.py
  - tests/tabix_data/make_data.py
covered_digest: "v3:sha256:2083b0ae05c804d2b64ca5ec277fcc4aba7c0e9bc39d7981fa178814d0e13944"
behavior_unverified: 0
overrides_applied: 0
coincidental_reliance_items:
  - truth: "pysam.samtools.view('-h', <sam>, save_stdout=<file>) writes a file whose raw bytes contain no CRLF pair (02-01 truth #2)"
    reason: undeclared-precondition
    harden: "The view variant of this truth holds vacuously: view routes output through htslib '-' -> fd 1 on every platform, so the save_stdout file is always empty (0 bytes, no CRLF) — a routing property of upstream htslib, not something this phase's artifacts enforce. Already hardened in-suite: TestBinaryMode::test_dispatch_save_stdout_is_lf_only additionally asserts the flagstat variant with NON-EMPTY output (460+ bytes, CRLF-free), which is the command whose bytes actually flow through the psam_open3 redirect fd. No further action needed; recorded so the vacuous reading is never mistaken for the proof."
---

# Phase 2: 可移植性加固与测试全绿 (Portability & Suite Green) Verification Report

**Phase Goal:** 完整测试套件在 Windows 上通过，skip 数与 Linux 基线对账 — 功能对等的客观证据（PROJECT.md 成功标准）。(Full pytest suite passes on Windows, skip count reconciled against the Linux baseline — objective evidence of functional parity.)
**Verified:** 2026-10-12T10:09:53Z
**Status:** passed
**Re-verification:** No — initial verification (a prior verifier dispatch was interrupted before writing any report; this is the first VERIFICATION.md for the phase)

## Goal Achievement

The phase goal is behavioral, and it was verified by **independently re-executing the behavior**, not by trusting SUMMARY claims:

- **Full default collection, UCRT64, verifier's own run:** `1027 passed, 15 skipped in 22.30s`, pytest exit 0 (`_venv/bin/python.exe -m pytest`).
- **Skip reconciliation, verifier's own `-rs` run:** all 15 skips enumerated; every one matches a written-cause row in `02-TEST02-RECONCILIATION.md` (3 both-platform + 12 Windows-only: 11 pre-locked v1 libcurl capability gates + 1 mypy-env module gate). Zero silent skips.
- **Linux baseline, verifier's own API pull:** fork CI run 38220111717, head SHA `d912a1dfa9923e470ee6bb9617e1f5f15dfd9e18`, conclusion `success`, **19/19 jobs green** (ubuntu + macos direct 3.9–3.15-dev, sdist, conda, BSD advisory). The `direct (ubuntu, 3.14)` pytest line extracted from the live log — `1042 passed, 5 skipped, 2 warnings in 24.65s` — **matches the reconciliation doc's quoted baseline byte-for-byte**, including duration.

### Observable Truths

Merged from ROADMAP success criteria (5) + the four PLAN frontmatters (23 truths total after merging restatements; roadmap SCs map onto truths #13–#23 below).

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | No .pyx/.pxd under pysam/ cimports Cython posix modules (grep-clean) | ✓ VERIFIED | Verifier grep `grep -rn "from posix" pysam --include=*.pyx --include=*.pxd` → rc=1, zero matches |
| 2 | `view('-h', …, save_stdout=…)` file contains no CRLF pair; redirect choke point binary-safe | ✓ VERIFIED (coincidental-reliance) | `psam_open3` (aliased c_open3) at the redirect (`pysam/libcutils.pyx:360`); permanent test `test_dispatch_save_stdout_is_lf_only` asserts BOTH view (0-byte) and flagstat (non-empty, CRLF-free) variants — passed in verifier's suite run. See coincidental_reliance_items for the vacuous view reading |
| 3 | `tabix_compress` copies CRLF-laden payload byte-for-byte | ✓ VERIFIED | `test_tabix_compress_is_byte_faithful` (50 CRLF pairs round-trip identical) passed in verifier's run; copy loop reads via psam_open2 (`pysam/libctabix.pyx:65,835`) |
| 4 | import pysam succeeds; smoke_test prints "smoke OK" in UCRT64 | ✓ VERIFIED | Verifier ran `_venv/bin/python.exe devtools/smoke_test.py` → `smoke OK` |
| 5 | Both dispatch stdout-null sites in libcutils.pyx use os.devnull | ✓ VERIFIED | `pysam/libcutils.pyx:390,397` — `c_open2(force_bytes(os.devnull), O_WRONLY)` × 2 |
| 6 | POSIX branch of every libcport mapping is an identity alias (Linux/macOS source- and behavior-identical) | ✓ VERIFIED | `pysam/libcport.pxd:85-99` #else branch: dup/open/read/close/STDOUT_FILENO/O_* all identity macros, `typedef off_t psam_off_t`; behaviorally gated by fork CI ubuntu+macos 19/19 green on `d912a1df` |
| 7 | BAM/CRAM/VCF under CJK dir+file names read AND write on Windows (ACP 936) | ✓ VERIFIED | 5 TestCJKPathCanary tests passed in verifier's suite run and in verifier's dedicated `-v` run (11/11 in 0.26s) |
| 8 | CJK canary covers AlignmentFile+VariantFile write/read, .bai/.csi/.tbi build, tabix fetch, one dispatch command | ✓ VERIFIED | `tests/PortabilityRegression_test.py:69-134` — all five surfaces present as separate test methods |
| 9 | Permanent byte-level regression tests live in the regular suite (SAM LF-only, save_stdout LF-only, tabix_compress byte-faithful, BAM/VCF round-trip) | ✓ VERIFIED | `tests/PortabilityRegression_test.py` collected by default testpaths (setup.cfg `testpaths = pysam tests`); all 11 methods passed in verifier's full-suite run |
| 10 | compile_test.py struct assertions per-platform (not skipped) + static-assert module proves sizeof(hts_pos_t)==8 and sizeof(psam_off_t)==8 | ✓ VERIFIED | `EXPECTED_SIZES` table (`tests/compile_test.py:41-66`, posix+nt); `_Static_assert` ×3 incl. hts_pos_t and psam_off_t (`tests/_compile_sizes.pyx:18-21`); `test_compile_sizes_static_asserts` passed in verifier's suite run (pyximport available — not skipped) |
| 11 | PORT-02 one-time call-site checklist committed | ✓ VERIFIED | `02-PORT02-AUDIT.md`: 5 grep commands + per-site table; "Zero unguarded sites remain." conclusion |
| 12 | hfile.c POSIX behavior untouched outside #if defined(_WIN32); fork CI green | ✓ VERIFIED | `hopen_fd` narrow `open()` verbatim in #else; `fd_write` EPIPE mapping inside `#ifdef _WIN32` (hfile.c:578-594); CI 19/19 green |
| 13 | make_data_files() on win32 generates all three data dirs via Python generators — no make, no external binaries | ✓ VERIFIED (behavioral) | Verifier copied ONLY committed inputs to a fresh temp dir and ran `make_data_files()` there: ex1.bam = exactly 3270 fetchable records, all special artifacts + all.stamp produced, second call idempotent. Generators contain no subprocess/os.system/Popen (grep: docstring mentions only) |
| 14 | POSIX branch keeps exact subprocess make invocation; Makefiles untouched | ✓ VERIFIED | `tests/TestUtils.py` else-branch keeps `subprocess.check_output([make, '-C', directory], …)`; `git diff master...win -- tests/*/Makefile` (×3) → empty |
| 15 | conftest starts HTTP fixture as daemon threading.Thread on Windows and sets REF_PATH to os.pathsep | ✓ VERIFIED | `tests/conftest.py:60-100`: win32 branch = `_build_httpd` + `threading.Thread(…, daemon=True)`; `REF_PATH = os.pathsep` (:112). NOTE intentional in-phase evolution: 02-04 platform-split the fixture — POSIX restored upstream's child-process server token-identically (root cause: GIL-holding dispatch starves a thread server during libcurl calls; ubuntu CI had failed). Windows-side spawn safety (the truth's intent) holds; win32 branch has no multiprocessing |
| 16 | Previously-external-samtools collected tests compare via pysam dispatch in-process on Windows | ✓ VERIFIED | 4 PileupTestUtils builders rewritten to `pysam.samtools.mpileup` parsers (original column semantics); samtools_test check_statement win32 branch (`:196-217`); TestSAMFromStringIO uses `pysam.samtools.view` (`AlignmentFile_test.py:258`). Remaining subprocess builders (`build_pileup_with_samtoolspipe`, `build_query_positions_with_samtoolspipe`) consumed only by `*_bench.py` (outside default collection, D2-11) |
| 17 | StreamFiledescriptors keeps real subprocess+fd pipe, consumes via sys.executable, read == 198 | ✓ VERIFIED | `tests/StreamFiledescriptors_test.py:52-72`: `Popen([sys.executable, "-c", …])` list form, no shell; `assert read == 198` (:72); test passed in verifier's suite run |
| 18 | Generated data files land only in gitignored dirs; generator modules force-added | ✓ VERIFIED | `git ls-files` lists all 3 `make_data.py`; `git diff c3541873..d912a1df --name-status -- tests/pysam_data tests/tabix_data tests/cbcf_data` → ONLY the 3 make_data.py additions (prohibition P-0203-2 deterministically confirmed) |
| 19 | Full default pytest collection exits 0 on Windows in UCRT64 — zero failures | ✓ VERIFIED (behavioral) | Verifier's own run: `1027 passed, 15 skipped in 22.30s`, PYTEST_EXIT=0 |
| 20 | Every Windows-only skip individually named with written reason in committed exemption list | ✓ VERIFIED | Verifier's own `-rs` listing (15 rows) reconciles 1:1 against 02-TEST02-RECONCILIATION.md sections 3-4: 3 both-platform (linking module, large-cigar CRAM, samtools_processing), 11 libcurl gates, 1 mypy module gate — each with cause+evidence+date |
| 21 | The 4 upstream-known failures each received root-cause work; each ends fixed or documented | ✓ VERIFIED | Reconciliation §1 triage table; verifier re-ran the named selection: `4 passed, 365 deselected in 0.19s`, `log.txt` absent after run. TestLogging root cause = unclosed FileHandler (fix at `AlignmentFile_test.py:1774-1775`); testReadingFromFileWithoutIndex passes |
| 22 | TEST-02 reconciliation artifact records both-platform counts on same commit with -rs reasons and every skip difference explained | ✓ VERIFIED | `02-TEST02-RECONCILIATION.md` §2-4 complete; Windows `1027 passed, 15 skipped` (verifier reproduced exactly); ubuntu `1042 passed, 5 skipped, 2 warnings in 24.65s` — verifier pulled the live CI log and confirmed byte-identical quote; node-level diff = exactly one module (typechecking) |
| 23 | Fork CI ubuntu and macos green on the phase-final commit | ✓ VERIFIED (behavioral) | `gh run view 38220111717`: status completed, conclusion success, head `d912a1dfa992…`, 19/19 jobs success incl. direct ubuntu 3.9–3.15-dev and macos cells |

**Score:** 23/23 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pysam/libcport.pxd` | Single-point fd-I/O platform mapping, `_O_BINARY` forced inside Windows branch, no variadic macros, no Cython IF | ✓ VERIFIED | 115 lines; all psam_* identifiers; verifier grep: 0 `__VA_ARGS__`/Cython-IF; wired by 4 consumers (libcutils/libctabix/libchtslib.pyx/libchtslib.pxd) |
| `.planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md` | D2-03 grep-clean inventory with MSVC status column | ✓ VERIFIED | 16-row inventory + libcport contract table; "MSVC status" ×3, D2- citations ×11; deferred rows cite D2-02/D2-03/D2-11/W10/W4/v2 |
| `htslib/hfile.c` (hopen_fd) | _WIN32 `_wopen` shim, two-call MultiByteToWideChar, POSIX narrow open verbatim | ✓ VERIFIED | Source inspected; no MAX_PATH; malloc'd buffer freed on all paths; #else keeps `open()` verbatim |
| `tests/PortabilityRegression_test.py` | TestCJKPathCanary + TestBinaryMode, checkBinaryEqual used | ✓ VERIFIED | 11 test methods; imports checkBinaryEqual/checkGZBinaryEqual from TestUtils; collected and green |
| `tests/_compile_sizes.pyx` + `.pyxbld` | C-level static asserts via pyximport | ✓ VERIFIED | 3 `_Static_assert` lines; compiled green inside suite run; .pyxbld computes include_dirs from file location |
| `tests/{pysam,tabix,cbcf}_data/make_data.py` | generate(directory) mirroring Makefiles via pysam dispatch only | ✓ VERIFIED | `def generate` in all 3; no subprocess; behaviorally proven in verifier's temp-dir regeneration (3270 records, idempotent) |
| `tests/conftest.py` | spawn-safe Windows httpserver + REF_PATH=os.pathsep | ✓ VERIFIED | win32 threading branch; POSIX branch upstream-verbatim; os.pathsep present |
| `02-PORT02-AUDIT.md` | One-time binary-mode call-site audit | ✓ VERIFIED | Grep commands + full site table; zero unguarded sites |
| `02-TEST02-RECONCILIATION.md` | Counts table + skip diff + exemption list | ✓ VERIFIED | All three sections; counts cross-verified against live CI log and verifier's own runs |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `pysam/libcutils.pyx` | `pysam/libcport.pxd` | cimports + 3 call sites (psam_open3 redirect, 2× psam_open2 devnull) | ✓ WIRED | libcutils.pyx:25-29, 360, 390, 397 |
| `pysam/libchtslib.pxd` | `pysam/libcport.pxd` | `cimport psam_off_t as off_t` | ✓ WIRED | libchtslib.pxd:7 |
| `pysam/libctabix.pyx`, `pysam/libchtslib.pyx` | `pysam/libcport.pxd` | aliased cimports | ✓ WIRED | libctabix.pyx:65-66; libchtslib.pyx:10 |
| `tests/PortabilityRegression_test.py` | `htslib/hfile.c hopen_fd` | CJK canary through encode_filename → hopen → hopen_fd | ✓ WIRED | 5 canary tests green through the _wopen path (plus libcport psam_wopen + hts.c _wstat probes — the two Rule-2 extensions) |
| `tests/_compile_sizes.pyx` | `pysam/libcport.pxd` | `from pysam.libcport cimport psam_off_t` + width static assert | ✓ WIRED | _compile_sizes.pyx:13,20-21; compiled green in suite |
| `tests/TestUtils.py make_data_files` | `tests/*/make_data.py` | `sys.platform == 'win32'` importlib branch before make | ✓ WIRED | TestUtils.py:160-176; behaviorally exercised in temp-dir run |
| `tests/samtools_test.py check_statement` | pysam dispatch (win32) / external binary (POSIX) | catch_stdout=False for -o statements; run_command kept on POSIX | ✓ WIRED | samtools_test.py:196-221; POSIX oracle verbatim at :221 |
| `02-TEST02-RECONCILIATION.md` | fork CI ubuntu job on same SHA | verbatim log capture | ✓ WIRED | Verifier re-pulled run 38220111717 log; quoted line byte-identical |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| Suite-green claim | 1027 passed / 15 skipped | Verifier's own pytest execution | Yes | ✓ FLOWING |
| Linux baseline counts | 1042 passed / 5 skipped | Live GitHub Actions log (`gh run view --log`) | Yes | ✓ FLOWING |
| Skip inventory | 15 SKIPPED rows | Verifier's own `-rs` run | Yes | ✓ FLOWING |
| Generator outputs | ex1.bam (3270 records) + 5 special artifacts | pysam dispatch calls in make_data.generate (temp-dir re-run) | Yes | ✓ FLOWING |
| CJK canary | BAM/VCF/tbi under CJK paths | Real filesystem round-trips through _wopen | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full default collection green | `_venv/bin/python.exe -m pytest` (UCRT64) | `1027 passed, 15 skipped in 22.30s`, exit 0 | ✓ PASS |
| Skip reasons enumerated | `_venv/bin/python.exe -m pytest -rs` | 15 SKIPPED rows; all match exemption inventory | ✓ PASS |
| Portability regression suite | `pytest tests/PortabilityRegression_test.py -v` | 11 passed in 0.26s (CJK + binary mode) | ✓ PASS |
| Smoke gate | `_venv/bin/python.exe devtools/smoke_test.py` | `smoke OK` | ✓ PASS |
| Data generation (fresh dir, committed inputs only) | `make_data_files(<temp copy>)` | 3270 records; artifacts + stamp; idempotent on 2nd call | ✓ PASS |
| Four upstream-known failures by name | `pytest tests/AlignmentFile_test.py -k "TestLogging or testReadingFromFileWithoutIndex"` | `4 passed, 365 deselected`, log.txt absent | ✓ PASS |
| Collection count | `pytest --collect-only -q` | `1040 tests collected` (matches doc: 1028 baseline + 12 phase-added) | ✓ PASS |
| Fork CI on phase-final SHA | `gh run view 38220111717` | success, head d912a1df, 19/19 jobs | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` declared by the plans or present in the repo — N/A for this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| PORT-01 | 02-01 | POSIX 依赖清除 (posix cimports, /dev/null, fork/signal) | ✓ SATISFIED | Truths #1, #5, #6; checklist committed |
| PORT-02 | 02-01, 02-02 | 二进制模式审计 (O_BINARY forced; CRLF corruption eliminated) | ✓ SATISFIED | Truths #2, #3, #9, #11; libcport forcing + permanent tests |
| PORT-03 | 02-02 | LLP64 类型审计 | ✓ SATISFIED | Truth #10; EXPECTED_SIZES + static asserts green |
| PORT-04 | 02-02 | 非 ASCII 路径适配 (wide-char shim + CJK canary) | ✓ SATISFIED | Truths #7, #8; three narrow-open layers widened (_wopen hfile.c, psam_wopen libcport, _wstat hts.c) |
| TEST-01 | 02-03, 02-04 | 测试全绿 | ✓ SATISFIED | Truths #13-#17, #19-#21; verifier's own 1027/15/0 run |
| TEST-02 | 02-04 | 测试数对账 (skip parity vs Linux baseline) | ✓ SATISFIED | Truths #20, #22, #23; reconciliation doc cross-verified against live CI |

**Orphaned requirements:** none — REQUIREMENTS.md maps exactly PORT-01..04 + TEST-01/02 to Phase 2; all six appear in plan frontmatter and all six are satisfied.

### Prohibitions (judgment-tier, ADR-550 D4)

| Prohibition | Verdict | Evidence |
| ----------- | ------- | -------- |
| 02-03: MUST NOT rewrite comparisons into tautologies (two-sided structure on ≥1 platform; POSIX keeps external-binary oracle) | HELD (source-verified) | `samtools_test.py:218-221` POSIX else-branch keeps `run_command` external oracle; PileupTestUtils compares the Cython pileup engine against samtools-main mpileup output (two code paths). The win32 same-dispatch two-sided structure is exactly what the plan's own action text authorized; external-oracle coverage retained on Linux CI (ubuntu jobs exercise it, green) |
| 02-03: MUST NOT commit generated test-data artifacts (only generators force-added) | HELD (deterministic) | Phase diff in the three data dirs adds exactly 3 `make_data.py` files; all other tracked files pre-existing upstream inputs |
| 02-04: MUST NOT present model-recalled counts as measured evidence | HELD (deterministic) | Both quoted summary lines reproduced by the verifier from independent sources: Windows line by re-running the suite (counts identical), ubuntu line byte-matched against the live CI log (incl. `24.65s` duration) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| htslib/hfile.c | 113 | `// FIXME For now, clamp input buffer sizes…` | ℹ️ Info (pre-existing) | Present verbatim in upstream master at the same line; NOT added by this phase (diff shows no +FIXME). No action |

No phase-introduced debt markers, no stubs, no unwired consumers, no new unconditional skips (phase diff added exactly one conditional `skipif(NO_PYXIMPORT)`).

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/PortabilityRegression_test.py | PORT-02/04 | 11 | 0 | 0 | Value (byte equality, magic bytes, exact counts) | OK |
| tests/compile_test.py | PORT-03 | all | 0 (env has pyximport; skipif dormant) | 0 | Value (exact sizes; compile-time asserts) | OK |
| tests/samtools_test.py | TEST-01 | 15 | 0 in verifier run (tty-gated testUsage passed) | 0 (POSIX keeps external oracle) | Behavioral (three-tier compare ladder) | OK |

- **Disabled tests on requirements:** 0 (only environmental skipifs; none fired in the verifier's session except the documented 15 suite skips)
- **Circular patterns:** 0 — TEST-02's baseline values come from the EXTERNAL ubuntu CI oracle, independently reproduced by this verifier (provenance: VALID)
- **Insufficient assertions:** 0

### Decision Coverage

`check.decision-coverage-verify`: 11/11 trackable CONTEXT.md decisions honored by shipped artifacts; zero not_honored.

### Human Verification Required

N/A — Infrastructure/test-infrastructure phase with no user-facing elements. All acceptance criteria are verifiable programmatically, and every behavior-dependent truth received direct behavioral evidence in this verification (verifier-executed suite, generators, smoke, named tests, and live CI API pull). No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths exist.

### Advisory Notes (non-blocking, for the record)

1. **Coincidental reliance (truth #2, view variant):** see `coincidental_reliance_items` — the view save_stdout file is empty on every platform (htslib `-` routing), so that variant of the truth is vacuously true; the substantive write path is separately proven by the flagstat variant asserted in the permanent test.
2. **Open code-review findings** (`02-REVIEW.md` / `02-REVIEW-DISPOSITION.md`: 0 critical / 5 warning / 6 info, all disposition `open`): none breaks a phase must-have or the goal. Notable forward-looking items: WR-01 (longjmp fix not in the `import/pysam.c` template — regeneration would revert it), WR-03 (static-assert failure would surface as a pyximport skip via upstream's blanket except — in this environment pyximport works and the asserts ran), WR-05 (GCC-only `__builtin_setjmp/longjmp` will need an MSVC branch — Phase 3 scope, flagged in the checklist's MSVC column). These are recorded for Phase 3 triage; they do not affect Phase 2's MinGW/UCRT64 deliverable.
3. **Documentation evolution inside the phase:** 02-03's unconditional thread-httpserver truth was superseded by 02-04's platform-split (POSIX restored upstream-verbatim after the GIL-starvation CI regression). Final state satisfies both intents: Windows spawn safety AND POSIX zero-regression (CI-proven). Recorded here so the truth-wording difference is not read as a gap.

### Gaps Summary

None. All 23 merged must-have truths verified, all artifacts present/substantive/wired with real data flowing, all key links connected, all three prohibitions held, requirements PORT-01..04 + TEST-01/02 satisfied, decision coverage 11/11, and the phase goal itself (full Windows suite green + skip reconciliation against the Linux baseline) independently reproduced by this verifier: **1027 passed / 15 skipped / 0 failed on Windows** vs **1042 passed / 5 skipped on ubuntu** on the same phase-final SHA `d912a1df`, with every difference individually named, and fork CI green on all 19 jobs.

---

_Verified: 2026-10-12T10:09:53Z_
_Verifier: Claude (gsd-verifier)_
