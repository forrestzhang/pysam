---
phase: 02-portability-tests
verified: 2026-10-13T10:40:26Z
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
covered_digest: "v3:sha256:4b5adc55a4f230ac2ebbd66de6e972b1e99163031e5538f0ecde5ed293c9a3b0"
behavior_unverified: 0
overrides_applied: 0
coincidental_reliance_items:
  - truth: "pysam.samtools.view('-h', <sam>, save_stdout=<file>) writes a file whose raw bytes contain no CRLF pair (02-01 truth #2)"
    reason: undeclared-precondition
    harden: "Carried forward unchanged from the initial verification: the view variant holds vacuously (view routes output through htslib '-' -> fd 1 on every platform, so the save_stdout file is empty — 0 bytes, no CRLF); the substantive write path is separately proven by the flagstat variant (non-empty, CRLF-free) asserted in TestBinaryMode::test_dispatch_save_stdout_is_lf_only, which passed in both of this re-verification's full-suite runs."
re_verification:
  previous_status: passed
  previous_score: 23/23
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 2: 可移植性加固与测试全绿 (Portability & Suite Green) Verification Report

**Phase Goal:** 完整测试套件在 Windows 上通过，skip 数与 Linux 基线对账 — 功能对等的客观证据（PROJECT.md 成功标准）。(Full pytest suite passes on Windows, skip count reconciled against the Linux baseline — objective evidence of functional parity.)
**Verified:** 2026-10-13T10:40:26Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH (#4682, milestone closeout). Initial verification passed 23/23 on 2026-10-12 (phase-final SHA `d912a1df`); later phases 3/5 then modified five covered sources. All 23 truths were re-verified from scratch against the CURRENT tree (HEAD `6adf94e2`), with fresh behavioral evidence — not a quick regression pass.

## Goal Achievement

The phase goal is behavioral. This re-verification independently re-executed the behavior on the current tree, on BOTH Windows toolchains:

- **UCRT64 full suite (verifier's own run, from the phase's sanctioned MSYS2 UCRT64 shell):** `1034 passed, 15 skipped in 25.34s`, pytest exit 0 (`_venv/bin/python.exe -m pytest -q -rs`).
- **MSVC full suite (verifier's own run):** `1034 passed, 15 skipped in 29.38s`, pytest exit 0 (`_venv-msvc/Scripts/python.exe -m pytest -q -rs`).
- **Skip reconciliation (verifier's own `-rs` listings, both toolchains):** the skip set is IDENTICAL to the phase's 15-skip inventory and classification in `02-TEST02-RECONCILIATION.md` — 3 both-platform (linking env gate, large-cigar CRAM, samtools_processing upstream bug) + 11 pre-locked v1 libcurl capability gates + 1 mypy-env module gate. Zero silent skips, zero skip drift.
- **Fork CI on the current source tree (verifier's own API pull):** run 38380672667 on `965760f1` — the tree containing ALL post-phase source changes (the two later HEAD commits `160ef327`/`6adf94e2` touch only `.planning/` docs, verified by `git show --stat`): conclusion `success`, every job green — ubuntu direct 3.9–3.15-dev + conda + sdist, macos 3.9–3.15-dev + sdist, windows 3.10–3.15, BSD advisory. POSIX zero-regression holds at HEAD.
- **Count drift vs the phase's own baseline, fully reconciled:** 1027→1034 passed = exactly +7 later-phase test additions — 1× `TestDispatchOutputEncoding::test_cjk_header_comment_roundtrip` (03-01, WR-01 fix evidence) + 6× `TestWin32OracleReadback` teeth tests (05-01, 02-WR-02 closure evidence). Skips unchanged at 15 (same instances, same reasons). The phase-5 close-run figure of 1028/15 predates the 6 teeth-test commits; nothing was removed, no test regressed. The reconciliation doc's historical record (1027/15 on `d912a1df`, byte-matched against live CI in the initial verification) remains accurate for its commit and is unchanged since (`61125c2a`).

### Stale-Refresh Diff Audit (what later phases changed in covered files)

`git diff d912a1df..HEAD` over the covered surface touches exactly 5 files, all reviewed hunk-by-hunk:

| File | Change | Phase-2 impact |
| ---- | ------ | -------------- |
| `pysam/libcutils.pyx` (+30/-10) | `_collect`: binary read + strict-first UTF-8 decode, raw-bytes fallback (03-01/03-05, WR-01) | Outside the redirect choke point (`:360` `c_open3`) and devnull sites (`:390/:397`) — untouched, re-verified by grep |
| `tests/PortabilityRegression_test.py` (+145) | Adds `TestDispatchOutputEncoding` + `TestWin32OracleReadback` (6 teeth tests) | Additive; all pre-existing canary/binary-mode methods present and green |
| `tests/TestUtils.py` (+46) | Adds `check_api_readback_equal` + `_drop_pg_cl` (05, WR-02) | Additive; make_data_files win32/POSIX branches byte-unchanged |
| `tests/_compile_sizes.pyx` (+17/-6) | `_Static_assert` → portable negative-array typedef form (03-05) | Same invariants asserted (`sizeof(hts_pos_t)==8`, `sizeof(psam_off_t)==8`); now compiles under BOTH toolchains — proven by zero `no pyximport` skips in both suite runs |
| `tests/samtools_test.py` (+11/-1) | win32 `.bam` comparisons route through `check_api_readback_equal` (05, WR-02) | STRENGTHENS the no-tautology prohibition: win32 oracle now reads back through a different code path than the writer; POSIX ladder unchanged |

All other covered files (libcport.pxd, libchtslib.pyx/pxd, libctabix.pyx, hfile.c, hts.c, conftest.py, PileupTestUtils.py, compile_test.py, AlignmentFile_test.py, StreamFiledescriptors_test.py, 3× make_data.py, both .pysam.c) are byte-identical to the phase-final state.

### Observable Truths

Same 23 merged truths as the initial verification (ROADMAP SCs + four PLAN frontmatters). All re-verified against the current tree; behavioral truths re-proven by this verifier's own runs.

| # | Truth | Status | Evidence (2026-10-13 tree) |
| --- | --- | --- | --- |
| 1 | No .pyx/.pxd under pysam/ cimports Cython posix modules (grep-clean) | ✓ VERIFIED | Verifier grep `from posix` over pysam/*.pyx,*.pxd → rc=1, zero matches |
| 2 | `view('-h', …, save_stdout=…)` file contains no CRLF pair; redirect choke point binary-safe | ✓ VERIFIED (coincidental-reliance) | `c_open3` (=psam_open3) at `pysam/libcutils.pyx:360` intact; `test_dispatch_save_stdout_is_lf_only` (both variants) passed in both full-suite runs. See coincidental_reliance_items |
| 3 | `tabix_compress` copies CRLF-laden payload byte-for-byte | ✓ VERIFIED | `test_tabix_compress_is_byte_faithful` passed in both full-suite runs; copy loop via psam_open2 (libctabix.pyx unchanged since phase-final) |
| 4 | import pysam succeeds; smoke_test prints "smoke OK" in UCRT64 | ✓ VERIFIED | Verifier ran `_venv/bin/python.exe devtools/smoke_test.py` → `smoke OK`, exit 0 |
| 5 | Both dispatch stdout-null sites in libcutils.pyx use os.devnull | ✓ VERIFIED | `pysam/libcutils.pyx:390,397` — `c_open2(force_bytes(os.devnull), O_WRONLY)` × 2 |
| 6 | POSIX branch of every libcport mapping is an identity alias | ✓ VERIFIED | `pysam/libcport.pxd` #else branch: identity macros + `typedef off_t psam_off_t` (file byte-identical to phase-final); 0 `__VA_ARGS__`/Cython-IF; ubuntu+macos CI green on current tree (run 38380672667) |
| 7 | BAM/CRAM/VCF under CJK dir+file names read AND write on Windows | ✓ VERIFIED | 5 TestCJKPathCanary tests green in BOTH toolchain suite runs (UCRT64 and MSVC) |
| 8 | CJK canary covers AlignmentFile+VariantFile write/read, .bai/.csi/.tbi, tabix fetch, dispatch | ✓ VERIFIED | `tests/PortabilityRegression_test.py:76-131` — all five surfaces present; green |
| 9 | Permanent byte-level regression tests live in the regular suite | ✓ VERIFIED | TestBinaryMode 6 methods green in both full-suite runs; collected by default testpaths |
| 10 | compile_test per-platform struct assertions + static-assert module proves sizeof(hts_pos_t)==8 / psam_off_t==8 | ✓ VERIFIED | `EXPECTED_SIZES` posix+nt table (compile_test.py:41-66); portable typedef asserts (03-05 form) at `_compile_sizes.pyx:25-31`; **proven live on BOTH toolchains**: zero `no pyximport` skips in the UCRT64-shell run AND the MSVC run (the pyximport build compiled and `test_compile_sizes_static_asserts` passed in both) |
| 11 | PORT-02 one-time call-site checklist committed | ✓ VERIFIED | `02-PORT02-AUDIT.md` present in phase dir |
| 12 | hfile.c POSIX behavior untouched outside #if defined(_WIN32); fork CI green | ✓ VERIFIED | hfile.c byte-identical to phase-final (empty diff d912a1df..HEAD); _wopen shim + verbatim narrow open #else confirmed; CI green |
| 13 | make_data_files() on win32 generates all three data dirs via Python generators | ✓ VERIFIED | Wiring: TestUtils win32 importlib branch before make (re-inspected); generators unchanged since phase-final; behavioral proof: every data consumer in both 1034-test suite runs green on freshly gated data dirs |
| 14 | POSIX branch keeps exact subprocess make invocation; Makefiles untouched | ✓ VERIFIED | `subprocess.check_output([make, '-C', directory], …)` verbatim in else-branch; Makefiles outside the covered diff (untouched) |
| 15 | conftest starts HTTP fixture as daemon threading.Thread on win32; REF_PATH=os.pathsep | ✓ VERIFIED | conftest.py:62 platform-split, :81-91 win32 daemon thread, :112 `os.environ["REF_PATH"] = os.pathsep`; file unchanged since phase-final; httpserver-dependent tests green |
| 16 | Previously-external-samtools tests compare via pysam dispatch in-process on win32 | ✓ VERIFIED (strengthened) | PileupTestUtils D2-05 win32 dispatch branch; samtools_test check_statement win32 branch (`:196`, `catch_stdout=False` :352) — and since Phase 5 the `.bam` oracle additionally reads back through the API (`check_api_readback_equal`, `:257-265`): two-sided structure now uses a DIFFERENT code path on win32 |
| 17 | StreamFiledescriptors keeps real subprocess+fd pipe via sys.executable; read == 198 | ✓ VERIFIED | File unchanged since phase-final; `Popen([sys.executable, "-c", …])` :52-53, `assert read == 198` :72; green in both suite runs |
| 18 | Generated data files land only in gitignored dirs; generators force-added | ✓ VERIFIED | `git ls-files` over the 3 data dirs: 112 files, exactly 3 .py (the generators); `git diff --name-only d912a1df..HEAD` over the dirs → empty (prohibition deterministically confirmed at HEAD) |
| 19 | Full default pytest collection exits 0 on Windows — zero failures | ✓ VERIFIED (behavioral) | Verifier's own runs at HEAD: UCRT64 `1034 passed, 15 skipped in 25.34s` exit 0; MSVC `1034 passed, 15 skipped in 29.38s` exit 0 |
| 20 | Every Windows-only skip individually named with written reason in committed exemption list | ✓ VERIFIED | Verifier's own `-rs` listings reconcile 1:1 against 02-TEST02-RECONCILIATION.md §3-4 — same 15 instances on both toolchains: 3 both-platform + 11 libcurl gates + 1 mypy module gate |
| 21 | The 4 upstream-known failures each received root-cause work; each ends fixed or documented | ✓ VERIFIED | Verifier re-ran the named selection: `4 passed, 365 deselected`, exit 0; no `log.txt` after run |
| 22 | TEST-02 reconciliation artifact records both-platform counts on same commit with -rs reasons | ✓ VERIFIED | Doc unchanged since `61125c2a` (its historical record was byte-verified against live CI in the initial verification); current-tree skip classification unchanged — the same 15 skips, same reasons, on both toolchains |
| 23 | Fork CI ubuntu and macos green on the phase-final commit (zero-regression closure) | ✓ VERIFIED (behavioral) | Historical: run 38220111717 on `d912a1df` green (initial verification). Current: run 38380672667 on `965760f1` (all source changes; later commits docs-only) — all ubuntu/macos/windows jobs success |

**Score:** 23/23 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pysam/libcport.pxd` | Single-point fd-I/O platform mapping, _O_BINARY inside Windows branch, no variadic macros, no Cython IF | ✓ VERIFIED | Byte-identical to phase-final; identity POSIX branch re-inspected; consumed by libcutils/libctabix/libchtslib |
| `.planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md` | D2-03 grep-clean inventory with MSVC status column | ✓ VERIFIED | Present; MSVC column now backed by a green MSVC toolchain (Phase 3/5) |
| `htslib/hfile.c` (hopen_fd) | _WIN32 _wopen shim, two-call MultiByteToWideChar, POSIX narrow open verbatim | ✓ VERIFIED | Byte-identical to phase-final; shim re-inspected |
| `tests/PortabilityRegression_test.py` | CJK canary + binary-mode tests, checkBinaryEqual used | ✓ VERIFIED | Now 18 methods (11 phase-2 + 7 later-phase additions); all green both toolchains |
| `tests/_compile_sizes.pyx` + `.pyxbld` | C-level static asserts via pyximport | ✓ VERIFIED | Portable typedef form (03-05); compiled+passed on BOTH toolchains in this verification |
| `tests/{pysam,tabix,cbcf}_data/make_data.py` | generate(directory) via pysam dispatch only | ✓ VERIFIED | Unchanged since phase-final; `def generate` in all 3; consumers green |
| `tests/conftest.py` | spawn-safe win32 httpserver + REF_PATH=os.pathsep | ✓ VERIFIED | Unchanged since phase-final; branch structure re-inspected |
| `02-PORT02-AUDIT.md` | One-time binary-mode call-site audit | ✓ VERIFIED | Present, unchanged |
| `02-TEST02-RECONCILIATION.md` | Counts table + skip diff + exemption list | ✓ VERIFIED | Present, unchanged; classification still matches live behavior at HEAD |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `pysam/libcutils.pyx` | `pysam/libcport.pxd` | cimports + 3 call sites (redirect + 2× devnull) | ✓ WIRED | :26 cimport, :360 c_open3, :390/:397 c_open2 (re-grepped at HEAD) |
| `pysam/libchtslib.pxd` | `pysam/libcport.pxd` | `cimport psam_off_t as off_t` | ✓ WIRED | Unchanged since phase-final |
| `pysam/libctabix.pyx`, `pysam/libchtslib.pyx` | `pysam/libcport.pxd` | aliased cimports | ✓ WIRED | Unchanged since phase-final |
| `tests/PortabilityRegression_test.py` | `htslib/hfile.c hopen_fd` | CJK canary through encode_filename → hopen → hopen_fd | ✓ WIRED | 5 canary tests green on both toolchains |
| `tests/_compile_sizes.pyx` | `pysam/libcport.pxd` | `cimport psam_off_t` + width assert | ✓ WIRED | :13 cimport, :29-31 typedef assert; compiled green on both toolchains |
| `tests/TestUtils.py make_data_files` | `tests/*/make_data.py` | win32 importlib branch before make | ✓ WIRED | Re-inspected at HEAD; exercised by both suite runs |
| `tests/samtools_test.py check_statement` | pysam dispatch (win32) / external binary (POSIX) | catch_stdout=False; since 05: API read-back oracle for .bam | ✓ WIRED | :196/:257-265 win32; :221+ POSIX ladder unchanged |
| `02-TEST02-RECONCILIATION.md` | fork CI ubuntu job on same SHA | verbatim log capture | ✓ WIRED | Historical capture verified in initial verification; current-tree skips match the classification exactly |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| Suite-green claim (UCRT64) | 1034 passed / 15 skipped | Verifier's own pytest execution | Yes | ✓ FLOWING |
| Suite-green claim (MSVC) | 1034 passed / 15 skipped | Verifier's own pytest execution | Yes | ✓ FLOWING |
| Skip inventory | 15 SKIPPED rows ×2 toolchains | Verifier's own `-rs` runs | Yes | ✓ FLOWING |
| Linux/POSIX baseline | all ubuntu+macos jobs green | Live GitHub Actions API (run 38380672667) | Yes | ✓ FLOWING |
| CJK canary | BAM/VCF/tbi under CJK paths | Real filesystem round-trips through _wopen | Yes | ✓ FLOWING |
| Count-drift accounting | +7 tests = 1 (03-01) + 6 (05-01) | git diff + test-method enumeration | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full suite green, UCRT64 (sanctioned shell) | `MSYSTEM=UCRT64 …bash -lc '_venv/bin/python.exe -m pytest -q -rs'` | `1034 passed, 15 skipped in 25.34s`, exit 0 | ✓ PASS |
| Full suite green, MSVC | `_venv-msvc/Scripts/python.exe -m pytest -q -rs` | `1034 passed, 15 skipped in 29.38s`, exit 0 | ✓ PASS |
| Static asserts compile+pass on both toolchains | (no `no pyximport` skips in either run) | 0 such skips in both runs | ✓ PASS |
| Skip reasons match exemption inventory | `-rs` listings ×2 | 15/15 rows match reconciliation doc | ✓ PASS |
| Smoke gate | `_venv/bin/python.exe devtools/smoke_test.py` | `smoke OK`, exit 0 | ✓ PASS |
| Four upstream-known failures by name | `pytest tests/AlignmentFile_test.py -k "TestLogging or testReadingFromFileWithoutIndex"` | `4 passed, 365 deselected`, no log.txt | ✓ PASS |
| POSIX zero-regression at HEAD | `gh run view 38380672667 --json jobs` | every ubuntu/macos/windows job success | ✓ PASS |

Note on environment sensitivity (not a gap): a diagnostic Git Bash run (gcc not on PATH) produced 3 extra `no pyximport` skips — the pyximport runtime C build needs the compiler toolchain, exactly per the phase's UCRT64-shell environment contract. From the sanctioned shell the three tests compile and pass. This is also first-hand confirmation that review finding WR-03's blanket-except swallow remains structural (annotated in 02-REVIEW-DISPOSITION.md).

### Probe Execution

No `scripts/*/tests/probe-*.sh` declared by the plans or present in the repo — N/A for this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| PORT-01 | 02-01 | POSIX 依赖清除 | ✓ SATISFIED | Truth #1 (grep-clean at HEAD), #5, #6 |
| PORT-02 | 02-01, 02-02 | 二进制模式审计 | ✓ SATISFIED | Truths #2, #3, #9, #11; both suite runs green with byte-fidelity tests |
| PORT-03 | 02-02 | LLP64 类型审计 | ✓ SATISFIED | Truth #10 — EXPECTED_SIZES + portable static asserts proven on BOTH toolchains |
| PORT-04 | 02-02 | 非 ASCII 路径适配 | ✓ SATISFIED | Truths #7, #8 — canary green on both toolchains |
| TEST-01 | 02-03, 02-04 | 测试全绿 | ✓ SATISFIED | Truths #13-#17, #19-#21; 1034/15/0 ×2 toolchains at HEAD |
| TEST-02 | 02-04 | 测试数对账 | ✓ SATISFIED | Truths #20, #22, #23; 15-skip classification identical, drift fully accounted |

**Orphaned requirements:** none — REQUIREMENTS.md maps exactly PORT-01..04 + TEST-01/02 to Phase 2 (all marked Complete); all six appear in plan frontmatter and all six are satisfied at HEAD.

### Prohibitions (judgment-tier, ADR-550 D4)

| Prohibition | Verdict | Evidence (current tree) |
| ----------- | ------- | ---------------------- |
| 02-03: MUST NOT rewrite comparisons into tautologies (POSIX keeps external-binary oracle; two-sided structure on ≥1 platform) | HELD (source-verified, strengthened) | POSIX else-branch keeps `run_command` external oracle (unchanged); PileupTestUtils compares Cython pileup vs samtools-main mpileup; since Phase 5 the win32 `.bam` oracle reads back through `pysam.AlignmentFile` — a different code path than the writer — with 6 teeth tests proving mutations are rejected (all green both toolchains) |
| 02-03: MUST NOT commit generated test-data artifacts | HELD (deterministic) | `git diff --name-only d912a1df..HEAD` over the three data dirs is empty; 112 tracked files, exactly 3 .py generators |
| 02-04: MUST NOT present model-recalled counts as measured evidence | HELD (deterministic) | Every count in this report is from the verifier's own 2026-10-13 runs or a live CI API pull; the doc's historical quotes were byte-verified against live CI in the initial verification |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| htslib/hfile.c | 113 | `// FIXME For now, clamp input buffer sizes…` | ℹ️ Info (pre-existing upstream) | Unchanged since phase-final; verbatim upstream |
| tests/samtools_test.py | 75-97 | several `TODO:` comments in the statement list | ℹ️ Info (pre-existing upstream) | 7 TODOs present verbatim in `master`; outside every phase-2 and later-phase hunk |

No phase-introduced or later-phase-introduced debt markers in the covered surface; no stubs; no unwired consumers; skip inventory unchanged.

### Review-Disposition Bookkeeping (stale-refresh annotations)

`02-REVIEW-DISPOSITION.md` re-triaged against the current tree (this verifier, source evidence for each): WR-01 → **fixed** (Phase 3 D-20 compiler gate now in `import/pysam.c:59-75`, regeneration-safe); WR-02 → **fixed** (Phase 5 API read-back oracle + 6 teeth tests); WR-05 → **fixed** (D-20 gate `#if defined(_WIN32) && !defined(_MSC_VER)`; MSVC toolchain green); WR-03 → **still open** (03-05 fixed the assert-form portability failure mode — asserts now compile on both toolchains — but the blanket-except swallow remains structural, observed first-hand during this verification); WR-04 + IN-01..06 remain open (info/warning-level bookkeeping, none affects a phase must-have).

### Human Verification Required

N/A — same as the initial verification: infrastructure/test-infrastructure phase, all acceptance criteria programmatically verified, and every behavior-dependent truth received direct fresh behavioral evidence in this re-verification (two full-suite runs, smoke, named tests, live CI API pull). No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths.

### Gaps Summary

None. The stale-refresh hypothesis (later phases broke a covered truth) is falsified: of the 5 files later phases touched in the covered surface, every change is additive or strengthening (UTF-8 decode in `_collect` away from the phase's choke points; a win32 oracle that reads back through a different code path; portable static asserts), and the phase's goal state is stronger than at phase close — the full suite is green on BOTH Windows toolchains (UCRT64 and MSVC each 1034 passed / 15 skipped / 0 failed at HEAD), the 15-skip inventory matches the committed reconciliation classification exactly, the +7 test-count drift is fully accounted for by named later-phase additions, and fork CI is green on every ubuntu/macos/windows job for the current source tree.

---

_Verified: 2026-10-13T10:40:26Z_
_Verifier: Claude (gsd-verifier)_
