---
phase: 01-mingw-w64
verified: 2026-10-13T10:25:32Z
status: passed
score: 15/15 must-haves verified
covered_files:
  - .gitattributes
  - .planning/phases/01-mingw-w64/01-01-PLAN.md
  - .planning/phases/01-mingw-w64/01-01-SUMMARY.md
  - .planning/phases/01-mingw-w64/01-02-PLAN.md
  - .planning/phases/01-mingw-w64/01-02-SUMMARY.md
  - .planning/phases/01-mingw-w64/01-03-PLAN.md
  - .planning/phases/01-mingw-w64/01-03-SUMMARY.md
  - INSTALL
  - devtools/msys2-bootstrap.sh
  - devtools/probe_symbol_check.py
  - devtools/smoke_test.py
  - pysam/libcport.pxd
  - pysam/libcutils.pyx
  - setup.py
  - win32/getopt.c
  - win32/getopt.h
covered_digest: "v3:sha256:90f42dff770c6e2438bfda126d40ed8b90d5d304ff29cc4893d1defa423e4cb8"
behavior_unverified: 0
overrides_applied: 0
unverified_prohibition: "3 judgment-tier prohibitions re-checked first-hand on the current tree (all upheld); human ratification on record — 01-UAT.md complete 2026-09-30, 4/4 pass (user-delegated to orchestrator)"
re_verification:
  previous_status: passed
  previous_score: 15/15
  gaps_closed:
    - "CR-01 (implib emission vs read path mismatch on non-inplace builds): closed by Phase 3 commit 08e2526a (D-17) — emission (setup.py:679-681) and gate read (setup.py:474-488) now both derive from get_ext_fullpath; verified in current source"
  gaps_remaining: []
  regressions: []
---

# Phase 1: MinGW-w64 构建系统 Verification Report

**Phase Goal:** 开发者在 MSYS2 UCRT64 下从源码一步构建 pysam（含 bundled htslib/htscodecs/samtools/bcftools），`import pysam` 在 Windows 开发机可用 — 一切后续工作的前提。
**Verified:** 2026-10-13T10:25:32Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH (#4682, milestone closeout): prior verification passed 2026-10-12; Phases 3/5 afterwards modified covered sources (`setup.py`: MSVC platform gate + module graph + D-17 implib derivation + phase-5 lockstep comparator; `pysam/libcutils.pyx`: WR-01 `_collect` binary-read/UTF-8 fixes; `devtools/probe_symbol_check.py`: REPO_ROOT anchoring + EXT_SUFFIX scoping; `INSTALL`: phase-4 prebuilt-wheel section). Same 15-truth must-have set, fresh first-hand evidence against the CURRENT tree (HEAD 6adf94e2, all milestone work included), fresh fingerprint.

## Refresh Scope (what changed since the prior fingerprint)

`git log --since=2026-10-12` over the covered set shows exactly these source commits: `08e2526a` (D-17: MinGW implib emission from get_ext_fullpath dirname — **closes deferred CR-01**), `14cedd97`/`dfa47c25`/`f6cf3727` (libcutils `_collect` binary read + strict-UTF-8 decode with raw-bytes fallback — **fixes prior anti-pattern warning WR-01**), `e177844a`/`465adb7e`/`fc471ae3`/`f44e42b6`/`61fc11b8`/`860dd867`/`0e6adfd7`/`a6d928fa`/`fd6f7510` (Phase 3 MSVC arm + portability fixes, all nt/MSVC-gated per 03-VERIFICATION.md), `1053e95f` (INSTALL prebuilt-wheel docs section), `2d23a69b`/`efe5a2b0` (Phase 5 MSVC_LIBHTS_OBJS lockstep comparator adjacent to the symbol gate + probe cwd fix). Every Phase-1 contract element was re-verified to survive the delta; behavioral proofs re-run first-hand today.

## Goal Achievement

### Observable Truths

Same 15-truth set as the ratified prior verifications (ROADMAP SC R1-R4 + plan-level P-truths), each re-verified against the CURRENT tree.

| # | Truth | Status | Evidence (current tree, 2026-10-13) |
|---|-------|--------|----------|
| R1 | SC-1: one-command UCRT64 build compiles all 13 Cython extensions + bundled htslib/htscodecs/samtools/bcftools, no manual sh configure/make/nm | ✓ VERIFIED | 13 `pysam/libc*.cp314-mingw_x86_64_ucrt_gnu.pyd` + 13 `.dll.a` on disk, built TODAY (libhts.a 2026-10-13 01:15 local, the phase-5-close full rebuild through this phase's own setup.py pipeline); `htslib/config.h` real 6999-byte configure product (2026-10-13); `pysam/config.py` HTSLIB=builtin; configure spawned only via setup.py `["sh","-c",...]` (setup.py:116-124), make via `os.environ.get("MAKE")` (setup.py:135/139), nm via `_nm_command()` (setup.py:211-218) |
| R2 | SC-2: `import pysam` works on Windows, opens a BAM, dispatches samtools+bcftools via `_pysam_dispatch` | ✓ VERIFIED | First-hand today (UCRT64 contract): import → `0.24.1 builtin 0`; `devtools/smoke_test.py` exit 0 `smoke OK` — BAM generated via samtools dispatch (catch_stdout=False), BGZF magic `1f 8b 08 04` + `BC` subfield asserted, 24 alignments via AlignmentFile.fetch, bcftools view -H returned 44118 lines |
| R3 | SC-3: `check_ext_symbol_conflicts` actually runs on Windows via llvm-nm, fails on duplicates, never silently skipped | ✓ VERIFIED | First-hand today: `devtools/probe_symbol_check.py` exit 0 — resolved tool `llvm-nm -g -P` (ast-extracted real `_nm_command`), modules=13, teeth=904 (same binary judged as two extensions → duplicates detected), honesty=0 across 13 real binaries (raw before D-14 exemption: 0); source re-confirmed: win32 bare-call dispatch outside exception wrapper (setup.py:552-561), vacuous-pass LinkError guard (setup.py:492-498), D-16 closed 7-symbol exemption intact (setup.py:205-208); bootstrap log still shows 0 silent-skip warnings |
| R4 | SC-4: Linux/macOS builds and CI stay green (zero regression) | ✓ VERIFIED | First-hand gh today: run 38380672667 head_sha 965760f1 (latest source SHA; the 3 commits to HEAD 6adf94e2 are .planning docs-only) completed/success — 17/17 blocking ubuntu/macos jobs success; suite evidence on this tree independently green (03-05-SUMMARY: UCRT64 full suite 1028 passed/15 skipped/0 failed after full rebuild on the phase-final tree) |
| P1a | CRLF Wave-0 blocker cleared (eol=lf contract, renormalized trees) | ✓ VERIFIED | `.gitattributes` five `text eol=lf` rules + preserved export-ignore/linguist lines (re-read today); `git check-attr eol` → `eol: lf` on htslib/configure, htslib/Makefile, htslib/htscodecs_bundled.mk, samtools/samtools.pysam.c, bcftools/vcfsom.c, bootstrap script, libcutils.pyx; `git ls-files --eol` → `i/lf w/lf` |
| P1b | One committed script provisions the complete UCRT64 environment | ✓ VERIFIED | `devtools/msys2-bootstrap.sh` re-read in full today: 9-package single-line PKGS (with the ratified cython rename), MSYSTEM=UCRT64 gate (27-32), HTSLIB_MODE gate (37-44), pacman --needed (53), per-package version log (56-58), llvm-nm presence check (60-65), MAKE=mingw32-make (69-70), HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl export (74-75), venv --system-site-packages (80-81), canonical `pip install -e . --no-build-isolation` (86), smoke gate as final step (90), troubleshooting (92-100) |
| P1c | Smoke gate: nonzero on failure, binary-mode opens, magic assertion, both dispatches | ✓ VERIFIED (documented deviation) | Ran first-hand today exit 0; single direct `open()` uses `"rb"` (smoke_test.py:55); asserts gzip/BGZF magic `1f 8b 08 04` + `BC` subfield (stronger than plan's raw `b"BAM\x01"`, which only exists in the decompressed stream); headerful `test_mapped_unmapped.sam` + `catch_stdout=False` — documented first-build deviations (01-03-SUMMARY #5), unchanged since ratification |
| P1d | INSTALL: two manual steps + bootstrap + canonical command + D-05 sentence | ✓ VERIFIED | INSTALL 'Windows (MSYS2 UCRT64)' section re-read today — two manual steps, `sh devtools/msys2-bootstrap.sh` literal block, `pip install -e . --no-build-isolation`, python.org-GCC unsupported sentence, HTSLIB_MODE, --disable-libcurl boundary; phase-4's adjacent 'Windows (prebuilt wheel)' section does not alter this contract |
| P2a | Non-UCRT64 Windows python exits immediately with the 9-package message | ✓ VERIFIED (documented deviation) | First-hand today: UCRT64 venv python (mingw platform) under MSYSTEM=MINGW64 → `setup.py --version` exit 1 with the verbatim nine-package message naming UCRT64 + the bootstrap script (programmatic content+order match vs PKGS = True) — wrong-env fail-fast semantics preserved. Documented deviation: Phase 3's BUILD-02 restructured the gate so win-amd64 CPython (python.org/conda) enters MSVC mode with a banner instead of exiting (setup.py:68-98) — verified in 03-VERIFICATION.md; the mingw-but-not-UCRT64 rejection that this truth guards against still fires |
| P2b | Symbol check via llvm-nm outside the exception-swallowing wrapper; POSIX skip-with-warning byte-identical | ✓ VERIFIED | setup.py:552-561: win32 calls `check_ext_symbol_conflicts()` directly (loud separate-mode warning only); POSIX try/except (563-569) with both verbatim warning strings; probe exec'd the real resolver first-hand today |
| P2c | Getopt cannot false-positive the mandatory gate | ✓ VERIFIED (D-16 model) | `WIN32_GETOPT_EXEMPT_SYMBOLS` = exactly 7 closed symbols (getopt/getopt_long/getopt_long_only/optarg/optind/opterr/optopt, setup.py:205-208); `--exclude-symbols` on every win32 module + private copies (setup.py:687-695); `os_c_files = ['win32/getopt.c']` in the win32 branch (setup.py:1007), concatenated into the libchtslib dict ONLY (setup.py:1247 — sole os_c_files use in module dicts); probe honesty=0 raw=0 first-hand today (zero exemption hits); D-16 ratification on record (01-UAT.md test 2 pass) |
| P2d | No ELF rpath on Windows link lines; import library resolves downstream -l flags | ✓ VERIFIED | setup.py:621-624 win32 elif adds no rpath; POSIX `-Wl,-rpath,$ORIGIN` else-branch unchanged (697-701); MinGW implib now emitted beside get_ext_fullpath via D-17 derivation (679-696) — CR-01 closed; 13 fresh `.dll.a` implibs on disk; all 13 UCRT64 modules linked and imported first-hand today |
| P2e | Every setup.py change win32-gated; POSIX untouched | ✓ VERIFIED | All phase-1 gates re-confirmed (`_is_ucrt64_python`, sh -c configure, `_nm_command`, rpath elif, build_extension arms); Phase 3's additions are nt/MSVC-gated (`IS_MSVC_PYTHON` requires os.name=='nt', compiler_type msvc arms) — no POSIX path touched; empirical CI 17/17 blocking jobs green on current source SHA; Phase 5's lockstep comparator (setup.py:151-191) runs only in the MSVC path |
| P2f | Hardcoded null-device byte paths replaced by os.devnull | ✓ VERIFIED | pysam/libcutils.pyx `os.devnull` ×2 (lines 390, 397, via `psam_open2`), `/dev/null` ×0 — PRESERVED through Phase 3's `_collect` rewiring (14cedd97/dfa47c25) |
| P3d | Teeth proven with real built binaries | ✓ VERIFIED | First-hand today: probe teeth=904 on the largest real import library judged under two pseudo-names, using setup.py's actual ast-extracted parser (now REPO_ROOT-anchored and EXT_SUFFIX-scoped per phase-5 fix — no MSVC/UCRT64 cross-contamination) |

**Score:** 15/15 truths verified (0 present, behavior-unverified)

### Deferred Items

None remaining. The single previously-deferred item (CR-01: non-inplace win32 builds crash at the symbol gate) is CLOSED by Phase 3 commit `08e2526a` (D-17): implib emission (setup.py:679-681) and the gate's read path (setup.py:474-488) both derive from `get_ext_fullpath`, verified in current source. Previously-deferred CR-02 was closed by Phase 2 (prior report). Note: 01-REVIEW-DISPOSITION.md still lists CR-01 as `deferred` and WR-01 as `open` — both are superseded by the Phase 3 fixes (08e2526a; 14cedd97+dfa47c25, `_collect` binary read + strict UTF-8 decode verified at libcutils.pyx:450-476); ledger annotation is bookkeeping only, not a phase gap.

### Advisory (New Scope, Unevidenced)

None. The stale-refresh delta was inspected commit-by-commit (git log over the covered set since 2026-10-12); every delta is Phase 3/5 in-contract work verified in those phases' own reports, and each Phase-1 contract element touching a changed file was re-proven first-hand today (spot-check table below).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pysam/libc*.cp314-mingw_x86_64_ucrt_gnu.pyd` (13) | compiled UCRT64 extensions | ✓ VERIFIED | 13 on disk, built today (2026-10-13 01:15 local, phase-5-close rebuild); import + both dispatches proven first-hand today |
| `pysam/*.dll.a` (13) | per-extension import libraries | ✓ VERIFIED | 13 on disk incl. libchtslib.cp314-...dll.a; gate + probe read them (probe exit 0 today, teeth=904/honesty=0) |
| `devtools/msys2-bootstrap.sh` | 9-package provisioning contract | ✓ VERIFIED | content contract fully re-checked today (see P1b) |
| `devtools/smoke_test.py` | acceptance gate | ✓ VERIFIED | re-read; ran first-hand today exit 0 |
| `devtools/probe_symbol_check.py` | BUILD-03 teeth probe | ✓ VERIFIED | re-read (phase-5 cwd/EXT_SUFFIX fix in place); ran first-hand today exit 0 |
| `setup.py` | win32-gated build pipeline (phase-1 edits) | ✓ VERIFIED | all phase-1 edits re-confirmed in current source amid the phase-3/5 additions |
| `pysam/libcutils.pyx` | os.devnull fix (now via psam_open2) | ✓ VERIFIED | 2 call sites, 0 hardcoded literals; WR-01 decode fix verified adjacent |
| `pysam/libcport.pxd` | fd-I/O platform mapping | ✓ VERIFIED | present (4827 bytes), unchanged since the 2026-10-12 refresh |
| `.gitattributes` / `INSTALL` | eol contract / docs | ✓ VERIFIED | re-read; content re-verified |
| `win32/getopt.c` + `win32/getopt.h` | C23-hardened vendored getopt | ✓ VERIFIED | present (phase-3 optind-reset fix 860dd867 is MSVC-arm-only); win32/unistd.h + win32/stdint.h confirmed absent (deletions hold) |

Note: `gsd_run query verify.artifacts` retains the known false-negative on 01-03's two descriptive-glob artifact paths (same as both prior verifications); manual Level 1-4 verification supersedes — all artifacts exist, are substantive, wired, and loadable.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| bootstrap PKGS | setup.py gate message | verbatim 9-package mirror | ✓ WIRED | programmatic compare today: lists identical in content AND order; gate fired live today with the full list under MSYSTEM=MINGW64 |
| bootstrap | smoke gate | final script step | ✓ WIRED | line 90 of the script; smoke re-run today exit 0 |
| bootstrap → venv → import | working pysam | D-07/D-14 chain | ✓ WIRED | first-hand import + dispatch today |
| libchtslib implib | 12 downstream -l flags | GNU ld lib<name>.dll.a search | ✓ WIRED | emission source 679-696 + 13 fresh implibs on disk + all 13 modules linked/imported today; D-17 made emission/read path-derivation consistent |
| `_nm_command` | parser | llvm-nm -P POSIX.2 contract | ✓ WIRED | setup.py:211-218/221-244; probe exec'd the real pair first-hand today |
| smoke_test.py | `_pysam_dispatch` | samtools + bcftools dispatch | ✓ WIRED | both dispatch paths executed today (24 alignments; 44118 vcf lines) |
| smoke_test.py | committed test data | repo-root-resolved inputs | ✓ WIRED | tests/pysam_data inputs found and consumed today |
| libcutils.pyx | libcport.pxd | psam_open2/psam_open3 cimports | ✓ WIRED | libcutils.pyx:26; binary-forced opens preserved |

### Behavioral Spot-Checks

All commands run first-hand 2026-10-13 against the CURRENT tree (HEAD 6adf94e2) and today's build, under the UCRT64 contract (`C:/msys64/usr/bin/env MSYSTEM=UCRT64 CHERE_INVOKING=1 C:/msys64/usr/bin/bash.exe -lc 'cd D:/Github/pysam && MAKE=mingw32-make _venv/bin/python.exe ...'`).

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| import pysam + config | UCRT64 venv python `-c "import pysam, pysam.config; ..."` | `0.24.1 builtin 0` | ✓ PASS |
| Smoke gate (SC-2 end-to-end) | `_venv/bin/python.exe devtools/smoke_test.py` | exit 0; 24 alignments; 44118-line bcftools output; `smoke OK` | ✓ PASS |
| Symbol-gate teeth + tool + honesty | `_venv/bin/python.exe devtools/probe_symbol_check.py` | exit 0; tool=llvm-nm -g -P; modules=13; teeth=904; honesty=0 (raw 0) | ✓ PASS |
| UCRT64 fail-fast gate (wrong-env) | UCRT64 venv python `setup.py --version` under MSYSTEM=MINGW64 | exit 1 + full 9-package message naming the bootstrap script | ✓ PASS |
| CI zero-regression | `gh run view 38380672667` (source SHA 965760f1) | completed/success; 17/17 blocking ubuntu/macos jobs success; HEAD delta docs-only | ✓ PASS |
| Distribution prohibition | `find` for `*.whl`/`pysam-*.tar.gz`/`dist/` (excluding venvs/.git) | 0 wheels, 0 sdists, no dist/ | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| `devtools/probe_symbol_check.py` | UCRT64 venv python (probe contract) | exit 0; `probe OK: tool=llvm-nm -g -P teeth=904 honesty=0` | PASS |
| `devtools/smoke_test.py` | UCRT64 venv python | exit 0; `smoke OK` | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BUILD-01 | 01-01, 01-02, 01-03 | UCRT64 dev build pipeline | ✓ SATISFIED | R1, R2, P1a-P1d, P2a, P2d-P2f re-verified on current tree; REQUIREMENTS.md marks Complete — consistent |
| BUILD-03 | 01-02, 01-03 | symbol-check port with teeth | ✓ SATISFIED | R3, P2b, P2c, P3d re-verified first-hand today; REQUIREMENTS.md marks Complete — consistent |

Orphaned requirements: none — REQUIREMENTS.md traceability maps only BUILD-01/BUILD-03 to Phase 1; both are claimed by plans and re-verified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| setup.py | 1204 | `libcXXX` naming comment | ℹ️ Info | pre-existing upstream (verbatim at master:672); not phase-introduced |
| setup.py | 1225 | `TODO Eventually by running configure here...` | ℹ️ Info | pre-existing upstream (verbatim at master:686); warning-level marker, not phase-introduced |
| win32/getopt.c | 266 | `XXX This is no good solution` | ℹ️ Info | pre-existing vendored FreeBSD getopt (on master); phase only added C23 prototypes |
| pysam/libcutils.pyx | 450-476 | WR-01 `_collect` code-page decode mojibake | ℹ️ Info (FIXED) | prior warning now resolved by Phase 3 (binary read + strict UTF-8 decode with raw-bytes fallback); disposition ledger row not yet annotated — bookkeeping only |
| pysam/libcutils.pyx | — | WR-02 `parse_region` IndexError on `"chr1:100"` | ⚠️ Warning | inherited upstream behavior; advisory; does not touch any Phase 1 must-have |
| .gitattributes | 12-18 | bare `text` forces normalization; comment semantics (WR-03) | ⚠️ Warning | carried from prior verification; no binary files in covered trees today; advisory |

No phase-introduced TBD/FIXME/XXX debt markers (all three matches above are pre-existing upstream, verified against master). No stubs: every artifact is substantive, wired, and (where dynamic) data-flowing. Prohibition re-checks on the current tree: P1 libcurl off (`htslib/config.h:108 /* #undef HAVE_LIBCURL */` from the 2026-10-13 configure state + `pysam/config.py HAVE_LIBCURL=0` + bootstrap export + INSTALL boundary), P2 gate strength (fail-hard dispatch + vacuous-pass guard + probe honesty=0 live), P3 no distribution artifacts (0 `.whl`, 0 sdist, no `dist/`, excluding venvs/.git) — all upheld; human ratification on record (01-UAT.md complete, 4/4 pass).

### Human Verification Required

None. Infrastructure/foundation phase (build system) with no user-facing elements; all four prior UAT items were closed 2026-09-30 (01-UAT.md complete, 4/4 pass, user-delegated to orchestrator with first-hand re-verification). Every behavior-dependent truth has first-hand behavioral evidence from today (spot-check table above); the stale-refresh delta (Phases 3/5, all in-contract) was re-proven against each touched Phase-1 must-have and introduces no new human-only checks.

### Gaps Summary

No failed truths, no missing/stub artifacts, no unwired links, no regressions from the stale-refresh trigger. The Phase 3/5 delta over the covered set PRESERVED every Phase 1 must-have it touched: the platform gate keeps UCRT64 wrong-env fail-fast semantics (re-proven live: mingw python outside UCRT64 exits 1 with the verbatim nine-package message) while admitting MSVC per BUILD-02; the symbol gate keeps its D-16 closed 7-symbol exemption (probe raw=0 — not even exemption hits) with Phase 5's lockstep comparator added only in the MSVC path; the D-17 implib derivation closed the previously-deferred CR-01 in source; `_collect`'s WR-01 decode fix landed without touching the os.devnull contract (×2 preserved, 0 literals). All four ROADMAP success criteria re-proven first-hand on the current tree: R1 via today's build artifacts through the phase's own one-command pipeline, R2 via live import + smoke run, R3 via live probe (teeth=904, honesty=0), R4 via first-hand CI records on the current source SHA (17/17 blocking green, HEAD delta docs-only). Later phases' verified states (02-VERIFICATION 23/23, 03-VERIFICATION with UCRT64 suite 1028/15/0 after full rebuild, 05-VERIFICATION) all rest on this phase's build system and are consistent with it.

Note for the orchestrator: local HEAD 6adf94e2 is 3 docs-only commits (.planning/**) ahead of CI-verified source SHA 965760f1. Bookkeeping: 01-REVIEW-DISPOSITION.md rows CR-01 (`deferred`) and WR-01 (`open`) are superseded by the Phase 3 fixes and may be annotated at milestone close.

---

_Verified: 2026-10-13T10:25:32Z_
_Verifier: Claude (gsd-verifier)_
