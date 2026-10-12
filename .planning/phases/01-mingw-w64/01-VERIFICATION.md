---
phase: 01-mingw-w64
verified: 2026-10-12T10:38:11Z
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
covered_digest: "v3:sha256:3444dc932c6a2c0882258864f6ca93fd5d54ba825072855cab8a9674e3f1ad3a"
behavior_unverified: 0
overrides_applied: 0
unverified_prohibition: "3 judgment-tier prohibitions re-checked first-hand on the current tree (all upheld); human ratification on record — 01-UAT.md complete 2026-09-30, 4/4 pass (user-delegated to orchestrator)"
re_verification:
  previous_status: passed
  previous_score: 15/15
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "CR-01: win32 symbol gate reads the implib beside get_ext_fullpath but the implib is emitted into source-tree pysam/ — non-inplace builds (pip install ., setup.py build, bdist_wheel) crash with an unhandled CalledProcessError"
    addressed_in: "Phase 3"
    evidence: "Disposition ledger 01-REVIEW-DISPOSITION.md: CR-01 triaged 2026-09-30 during UAT (user-delegated), deferred to Phase 3 entry (BUILD-02 MSVC — first out-of-tree build phase); fix direction recorded (derive implib path from os.path.dirname(get_ext_fullpath)). Not goal-blocking: the Phase 1 dev-verification flow is the editable/inplace build where both paths agree."
---

# Phase 1: MinGW-w64 构建系统 Verification Report

**Phase Goal:** 开发者在 MSYS2 UCRT64 下从源码一步构建 pysam（含 bundled htslib/htscodecs/samtools/bcftools），`import pysam` 在 Windows 开发机可用 — 一切后续工作的前提。
**Verified:** 2026-10-12T10:38:11Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH (#4682): prior verification passed 2026-09-30; covered source `pysam/libcutils.pyx` was afterwards modified by Phase 2 (commit dc40dd29, libcport fd-I/O rewiring). Same must-have set, fresh evidence against the current tree, fresh fingerprint.

## Refresh Scope (what changed since the prior fingerprint)

`git log` over the prior covered set since 2026-09-30 shows exactly ONE source commit: `dc40dd29 feat(02-01): add libcport fd-I/O platform mapping; rewire libcutils` (pysam/libcport.pxd new, pysam/libcutils.pyx rewired; posix.fcntl/unistd cimports → libcport mappings, `c_open` split into `psam_open2`/`psam_open3` with `_O_BINARY` forced on Windows). Everything else in the covered set is byte-identical to the verified state. This refresh re-proves the phase goal on the post-Phase-2 tree; `pysam/libcport.pxd` is added to the covered set (the changed file's new dependency). An incremental code re-review of the delta exists (01-REVIEW.md, 2026-10-12: 0 critical, 2 warnings, 3 info) and the disposition ledger was updated.

## Goal Achievement

### Observable Truths

Same 15-truth set as the ratified prior verification (ROADMAP SC R1-R4 + plan-level P-truths), each re-verified against the CURRENT tree.

| # | Truth | Status | Evidence (current tree, 2026-10-12) |
|---|-------|--------|----------|
| R1 | SC-1: one-command UCRT64 build compiles all 13 Cython extensions + bundled htslib/htscodecs/samtools/bcftools, no manual sh configure/make/nm | ✓ VERIFIED | 13 `pysam/libc*.cp314-mingw_x86_64_ucrt_gnu.pyd` + 13 `.dll.a` on disk, freshly built TODAY 14:49-14:51 (Phase 2's final in-place rebuild — through this phase's own setup.py pipeline); `htslib/config.h` real 6999-byte configure product (Oct 12); `pysam/config.py` HTSLIB=builtin; configure spawned only via setup.py `sh -c` (setup.py:94-103), make via `os.environ.get("MAKE")` (setup.py:114/118, MAKE=mingw32-make from bootstrap), nm via `_nm_command()` |
| R2 | SC-2: `import pysam` works on Windows, opens a BAM, dispatches samtools+bcftools via `_pysam_dispatch` | ✓ VERIFIED | First-hand today: `_venv` python `import pysam` → `0.24.1`; `devtools/smoke_test.py` exit 0 `smoke OK` — BAM generated via samtools dispatch (catch_stdout=False), BGZF magic `1f 8b 08 04` + `BC` subfield verified, 24 alignments via AlignmentFile.fetch, bcftools view -H returned 44118 chars |
| R3 | SC-3: `check_ext_symbol_conflicts` actually runs on Windows via llvm-nm, fails on duplicates, never silently skipped | ✓ VERIFIED | First-hand today: `devtools/probe_symbol_check.py` exit 0 — resolved tool `llvm-nm -g -P` (the real `_nm_command()` from setup.py source), teeth=904 (same binary judged as two extensions → duplicates detected), honesty=0 across 13 real binaries; source re-confirmed: win32 bare-call dispatch outside exception wrapper (setup.py:456-466), vacuous-pass LinkError guard (setup.py:413-419), D-16 closed 7-symbol exemption intact (setup.py:141-144) |
| R4 | SC-4: Linux/macOS builds and CI stay green (zero regression) | ✓ VERIFIED | First-hand gh API today: run 38221882337 head_sha 3404a4d0 (latest source SHA; the 8 commits up to HEAD are .planning docs-only) completed/success — 19/19 jobs success incl. 17/17 blocking ubuntu/macos; Phase 2 suite evidence independently green (02-VERIFICATION.md: verifier-run `1027 passed, 15 skipped, 0 failed` on this tree); incremental re-review confirms POSIX names are identity mappings in libcport.pxd |
| P1a | CRLF Wave-0 blocker cleared (eol=lf contract, renormalized trees) | ✓ VERIFIED | `.gitattributes` five `text eol=lf` rules + preserved export-ignore/linguist lines (re-read today); `git check-attr eol` → `eol: lf` on htslib/configure, htslib/Makefile, htslib/htscodecs.mk, samtools/samtools.pysam.c, bcftools/vcfsom.c, bootstrap script; `git ls-files --eol` → `i/lf w/lf` |
| P1b | One committed script provisions the complete UCRT64 environment | ✓ VERIFIED | `devtools/msys2-bootstrap.sh` re-read in full today: 9-package single-line PKGS (with the ratified cython rename), MSYSTEM=UCRT64 gate (27-32), HTSLIB_MODE gate (37-44), pacman --needed (53), per-package version log (56-58), llvm-nm presence check (60-65), MAKE=mingw32-make (69-70), HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl export (74-75), venv --system-site-packages (80-81), canonical `pip install -e . --no-build-isolation` (86), smoke gate as final step (90), troubleshooting (92-100) |
| P1c | Smoke gate: nonzero on failure, binary-mode opens, magic assertion, both dispatches | ✓ VERIFIED (documented deviation) | Ran first-hand today exit 0; single direct `open()` uses `"rb"` (smoke_test.py:55); asserts gzip/BGZF magic `1f 8b 08 04` + `BC` subfield (stronger than plan's raw `b"BAM\x01"`, which only exists in the decompressed stream); headerful `test_mapped_unmapped.sam` + `catch_stdout=False` — documented first-build deviations (01-03-SUMMARY #5), unchanged since ratification |
| P1d | INSTALL: two manual steps + bootstrap + canonical command + D-05 sentence | ✓ VERIFIED | INSTALL:91-124 'Windows (MSYS2 UCRT64)' section re-read today — two manual steps, `sh devtools/msys2-bootstrap.sh` literal block, `pip install -e . --no-build-isolation`, python.org-GCC unsupported sentence, HTSLIB_MODE, --disable-libcurl boundary |
| P2a | Non-UCRT64 Windows python exits immediately with the 9-package message | ✓ VERIFIED | First-hand today: `python setup.py --version` under non-UCRT64 python → exit 1, message names UCRT64, the bootstrap script, and all nine packages (grep count 9, programmatic order-match vs PKGS = True) |
| P2b | Symbol check via llvm-nm outside the exception-swallowing wrapper; POSIX skip-with-warning byte-identical | ✓ VERIFIED | setup.py:456-466: win32 calls `check_ext_symbol_conflicts()` directly (loud separate-mode warning only); POSIX try/except with both verbatim warning strings preserved in the else-branch |
| P2c | Getopt cannot false-positive the mandatory gate | ✓ VERIFIED (D-16 model) | `WIN32_GETOPT_EXEMPT_SYMBOLS` = exactly 7 closed symbols (getopt/getopt_long/getopt_long_only/optarg/optind/opterr/optopt, setup.py:141-144); `--exclude-symbols` on every module + private copies (setup.py:538-552); `os_c_files = ['win32/getopt.c']` in the win32 branch (setup.py:783); probe honesty=0 first-hand today; D-16 ratification on record (01-UAT.md test 2 pass) |
| P2d | No ELF rpath on Windows link lines; import library resolves downstream -l flags | ✓ VERIFIED | setup.py:527-555 win32 elif adds no rpath, emits `-Wl,--out-implib,pysam/lib<stem>.dll.a` (EXT_SUFFIX-derived); POSIX `-Wl,-rpath,$ORIGIN` else-branch unchanged; 13 implibs on disk (fresh today); all 13 downstream modules linked and imported first-hand today |
| P2e | Every setup.py change win32-gated; POSIX untouched | ✓ VERIFIED | All gates re-confirmed in source (`_is_ucrt64_python`, sh -c configure, `_nm_command`, run(), build_extension elif); empirical CI 19/19 green on current source SHA; incremental re-review: libcport POSIX branch is pure identity aliases |
| P2f | Hardcoded null-device byte paths replaced by os.devnull | ✓ VERIFIED | pysam/libcutils.pyx `os.devnull` ×2, `/dev/null` ×0 — PRESERVED through Phase 2's rewiring (the two devnull sites now route via `psam_open2`, dc40dd29) |
| P3d | Teeth proven with real built binaries | ✓ VERIFIED | First-hand today: probe teeth=904 on the largest real import library judged under two pseudo-names, using setup.py's actual extracted parser |

**Score:** 15/15 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | CR-01: non-inplace win32 builds crash at the symbol gate (implib emission path vs read path) | Phase 3 | 01-REVIEW-DISPOSITION.md: triaged 2026-09-30 during UAT (user-delegated), deferred to Phase 3 entry (BUILD-02 — first out-of-tree build phase); not goal-blocking (Phase 1-2 dev flow is the editable/inplace build where paths agree) |

Previously-deferred CR-02 (save_stdout without O_BINARY) is CLOSED: resolved by Phase 2's dc40dd29 (`psam_open3` → `_wopen(..., flags | _O_BINARY, ...)`), verified against generated `pysam/libcutils.c` in the 2026-10-12 incremental re-review; disposition ledger row updated to `fixed`.

### Advisory (New Scope, Unevidenced)

None — every new-scope finding from the incremental re-review (WR-01 `_collect` ANSI-codepage decode mojibake, WR-02 inherited upstream `parse_region` IndexError, IN-01..03) is evidenced in 01-REVIEW.md and tracked with open dispositions in 01-REVIEW-DISPOSITION.md; none touches a Phase 1 must-have.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pysam/*.pyd` (13) | compiled UCRT64 extensions | ✓ VERIFIED | 13 on disk, built today 14:49-14:51; import + both dispatches proven first-hand today |
| `pysam/*.dll.a` (13) | per-extension import libraries | ✓ VERIFIED | 13 on disk incl. libchtslib.cp314-...dll.a; gate + probe read them (probe exit 0 today) |
| `devtools/msys2-bootstrap.sh` | 9-package provisioning contract | ✓ VERIFIED | gsd verify.artifacts 4/4 pass (plan 01); content contract fully re-checked |
| `devtools/smoke_test.py` | acceptance gate | ✓ VERIFIED | gsd pass; ran first-hand today exit 0 |
| `devtools/probe_symbol_check.py` | BUILD-03 teeth probe | ✓ VERIFIED | gsd pass (plan 03); ran first-hand today exit 0 |
| `setup.py` | seven win32-gated edits | ✓ VERIFIED | gsd pass (plan 02); all edits re-confirmed in current source |
| `pysam/libcutils.pyx` | os.devnull fix (now via psam_open2) | ✓ VERIFIED | gsd pass; 2 call sites, 0 hardcoded literals |
| `.gitattributes` / `INSTALL` | eol contract / docs | ✓ VERIFIED | gsd pass (plan 01); content re-verified |
| `win32/getopt.c` + `win32/getopt.h` | C23-hardened vendored getopt | ✓ VERIFIED | present; win32/unistd.h + win32/stdint.h confirmed absent (deletions hold) |
| `pysam/libcport.pxd` (new in covered set) | Phase 2 fd-I/O platform mapping under the changed covered file | ✓ VERIFIED | exists (4827 bytes); Windows branch forces `_O_BINARY`, POSIX branch identity aliases (incremental re-review verified against generated C) |

Note: `gsd_run query verify.artifacts` reports 01-03's two build-output artifact entries as "not found" because their PLAN paths are descriptive globs (`pysam/ (13 libc*.pyd ...)`), which the tool resolves literally — same known false-negative as the prior verification. Manual Level 1-4 verification supersedes: the artifacts exist (13/13 counted today), are substantive, wired, and loadable.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| bootstrap PKGS | setup.py gate message | verbatim 9-package mirror | ✓ WIRED | programmatic compare today: lists identical in content AND order (incl. ratified cython rename); gate fired live with the full list |
| bootstrap | smoke gate | final script step | ✓ WIRED (gsd) | line 90 of the script; smoke re-run today |
| bootstrap → venv → import | working pysam | D-07/D-14 chain | ✓ WIRED (gsd) | first-hand import + dispatch today |
| libchtslib implib | 12 downstream -l flags | GNU ld lib<name>.dll.a search | ✓ WIRED (manual) | source 527-555 + 13 fresh implibs on disk + all 13 modules linked/imported today; gsd tool false-negative (descriptive from-path) |
| `_nm_command` | parser | llvm-nm -P POSIX.2 contract | ✓ WIRED (manual) | setup.py:146-152; probe exec'd the real pair first-hand today |
| smoke_test.py | `_pysam_dispatch` | samtools + bcftools dispatch | ✓ WIRED (gsd + live run) | both dispatch paths executed today |
| smoke_test.py | committed test data | repo-root-resolved inputs | ✓ WIRED (gsd) | tests/pysam_data inputs found and consumed today |
| libcutils.pyx | libcport.pxd | psam_open2/psam_open3 cimports (new since refresh) | ✓ WIRED | dc40dd29 rewiring; binary-forced opens verified in generated C |

### Behavioral Spot-Checks

All commands run first-hand 2026-10-12 against the CURRENT tree and today's build.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Symbol-gate teeth + tool + honesty | `_venv/bin/python.exe devtools/probe_symbol_check.py` (UCRT64) | exit 0; tool=llvm-nm -g -P; modules=13; teeth=904; honesty=0 | ✓ PASS |
| Smoke gate (SC-2 end-to-end) | `_venv/bin/python.exe devtools/smoke_test.py` (UCRT64) | exit 0; 24 alignments; 44118-char bcftools output; `smoke OK` | ✓ PASS |
| import pysam + config | `_venv/bin/python.exe -c "import pysam; ..."` (UCRT64) | `0.24.1`, libchtslib import OK | ✓ PASS |
| UCRT64 fail-fast gate | `python setup.py --version` (non-UCRT64 python) | exit 1 + full 9-package message | ✓ PASS |
| CI zero-regression | `gh run view 38221882337` (source SHA 3404a4d0) | completed/success; 19/19 jobs, 17/17 blocking ubuntu/macos | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| `devtools/probe_symbol_check.py` | `bash`-invoked via UCRT64 venv python | exit 0; `probe OK: tool=llvm-nm -g -P teeth=904 honesty=0` | PASS |
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
| setup.py | 824 | `libcXXX` naming comment | ℹ️ Info | pre-existing upstream (verbatim on master); not phase-introduced |
| win32/getopt.c | 266 | `XXX This is no good solution` | ℹ️ Info | pre-existing vendored FreeBSD getopt (on master); phase only added C23 prototypes |
| pysam/libcutils.pyx | — | WR-01: `_collect` decodes captured stdout/stderr with the Windows ANSI code page (mojibake risk) | ⚠️ Warning | NEW since Phase 2's rewiring context; evidenced in 01-REVIEW.md (2026-10-12), open in disposition ledger; advisory — does not touch any Phase 1 must-have (smoke/dispatch paths byte-clean today) |
| pysam/libcutils.pyx | — | WR-02: `parse_region` IndexError on `"chr1:100"` | ⚠️ Warning | inherited upstream behavior; open in ledger; advisory |
| .gitattributes | 12-18 | bare `text` forces normalization; comment misstates semantics (WR-03) | ⚠️ Warning | carried from prior verification; no binary files in covered trees today; open in ledger |
| setup.py | 405-410 vs 546-554 | implib lookup/emission path mismatch (CR-01) | 📋 Deferred | triaged 2026-09-30 (user-delegated), deferred to Phase 3 entry; does not affect the editable dev-verification flow |

No phase-introduced TBD/FIXME/XXX debt markers (the two matches above are pre-existing upstream comments). No stubs: every artifact is substantive, wired, and (where dynamic) data-flowing. Prohibition re-checks on the current tree: P1 libcurl off (`htslib/config.h:108 /* #undef HAVE_LIBCURL */` from TODAY's configure run + bootstrap export + INSTALL boundary), P2 gate strength (fail-hard dispatch + vacuous-pass guard + probe honesty=0 live), P3 no distribution artifacts (0 `.whl`, 0 `pysam-*.tar.gz`, no `dist/`, excluding _venv/.git) — all upheld; human ratification on record (01-UAT.md complete, 4/4 pass).

### Human Verification Required

None. The four items from the initial verification (P1/P2/P3 prohibition ratification, CR-01 triage) were all closed by UAT on 2026-09-30 (01-UAT.md: complete, 4/4 pass, user-delegated to orchestrator with first-hand re-verification). The current-tree refresh introduces no new human-only checks: every behavior-dependent truth has first-hand behavioral evidence from today (spot-check table above), and the only covered-file change was machine-re-reviewed with its findings tracked in the disposition ledger.

### Gaps Summary

No failed truths, no missing/stub artifacts, no unwired links, no regressions from the stale-refresh trigger. The one covered-file change since the ratified verification (dc40dd29, pysam/libcutils.pyx → libcport rewiring) PRESERVED every Phase 1 must-have touching that file (P2f: os.devnull ×2, zero `/dev/null` literals; R2 dispatch plumbing: smoke exit 0 today) and additionally closed the previously-deferred CR-02 (save_stdout now binary-forced via psam_open3/_wopen). All four ROADMAP success criteria re-proven first-hand on the current tree: R1 via today's fresh build artifacts produced through the phase's own one-command pipeline, R2 via live import + smoke run, R3 via live probe (teeth=904, honesty=0), R4 via first-hand CI records on the current source SHA (19/19 green, HEAD delta docs-only). Phase 2's independently verified state (02-VERIFICATION.md passed 23/23, suite 1027/15/0) rests on this phase's build system and is consistent with it.

Note for the orchestrator: local HEAD 7e8b404a is 8 docs-only commits (.planning/**) ahead of CI-verified source SHA 3404a4d0.

---

_Verified: 2026-10-12T10:38:11Z_
_Verifier: Claude (gsd-verifier)_
