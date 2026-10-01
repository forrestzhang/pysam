---
phase: 01-mingw-w64
verified: 2026-09-30T03:05:00Z
status: passed
score: 15/15 must-haves verified
covered_files:
  - .planning/phases/01-mingw-w64/01-01-PLAN.md
  - .planning/phases/01-mingw-w64/01-02-PLAN.md
  - .planning/phases/01-mingw-w64/01-03-PLAN.md
  - .planning/phases/01-mingw-w64/01-01-SUMMARY.md
  - .planning/phases/01-mingw-w64/01-02-SUMMARY.md
  - .planning/phases/01-mingw-w64/01-03-SUMMARY.md
  - .gitattributes
  - devtools/msys2-bootstrap.sh
  - devtools/smoke_test.py
  - devtools/probe_symbol_check.py
  - INSTALL
  - setup.py
  - pysam/libcutils.pyx
  - win32/getopt.c
  - win32/getopt.h

covered_digest: "v2:sha256:2cd243e27cdafcfee9755b511586fe34a28b11a0e301e490881e430b24d07f6f"
behavior_unverified: 0
overrides_applied: 0
unverified_prohibition: "3 judgment-tier prohibitions carry NON-AUTHORITATIVE LLM-judge verdicts (all upheld) — human review recommended; see human_verification"
deferred:
  - truth: "CR-02: _pysam_dispatch save_stdout redirect opens via C open() without O_BINARY — text-mode fd can silently corrupt BAM/BGZF written through pysam.utils.dispatch(save_stdout=...) on Windows"
    addressed_in: "Phase 2"
    evidence: "ROADMAP Phase 2 Success Criterion 3: 'Windows 上写出并回读的 BAM/BGZF 文件无 CRLF 损坏（全部文件 I/O 强制 O_BINARY/\"b\" 的审计关闭）' and requirement PORT-02 (二进制模式审计). Review itself confirms the line is pre-existing upstream code and the Phase 1 smoke path does not traverse it."
human_verification:
  - test: "Confirm prohibition P1 (no libcurl/remote I/O on the Windows build path) is upheld"
    expected: "Human accepts the LLM-judge verdict: devtools/msys2-bootstrap.sh exports HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl; INSTALL documents the v1 boundary; htslib/config.h carries '#undef HAVE_LIBCURL'"
    why_human: "judgment-tier prohibition (PLAN 01-02 frontmatter, status unverified/flagged) — autonomous verify records a non-authoritative verdict only"
  - test: "Confirm prohibition P2 (symbol gate not weakened or silently bypassed on Windows) is upheld, including the D-16 deviation"
    expected: "Human accepts: win32 dispatch calls check_ext_symbol_conflicts outside the exception-swallowing wrapper (setup.py:457-474), a vacuous-pass guard raises when llvm-nm yields nothing (setup.py:413-419), and the keep-filter is unchanged. NOTE the deviation from the plan's literal wording: single-copy getopt was falsified and replaced by the user-adjudicated D-16 model (private mingwex copies + --exclude-symbols + closed 7-symbol win32 exemption, setup.py:141-144) — recorded as Key Decision D-16 in PROJECT.md"
    why_human: "judgment-tier prohibition; the D-16 exemption is a documented deviation from the prohibition's 'single-copy only' wording that only the adjudicating human can ratify"
  - test: "Confirm prohibition P3 (no wheel/sdist/distribution artifact from the UCRT64 path) is upheld"
    expected: "Human accepts: no dist/, no *.whl, no pysam-*.tar.gz anywhere in the tree (checked 2026-09-30, excluding _venv/.git)"
    why_human: "judgment-tier prohibition (PLAN 01-03 frontmatter, status unverified/flagged) — autonomous verify records a non-authoritative verdict only"
  - test: "Triage CR-01 in 01-REVIEW-DISPOSITION.md (open Critical): win32 symbol gate reads the implib beside get_ext_fullpath but the implib is emitted into source-tree pysam/ — non-inplace builds (pip install ., setup.py build, bdist_wheel) crash with an unhandled CalledProcessError"
    expected: "A disposition decision (fix scheduling or explicit accept-and-defer). Does NOT block the Phase 1 goal: the phase's dev-verification flow is the editable/inplace build (pip install -e . --no-build-isolation, D-14), where both paths agree — ROADMAP SC-1 is satisfied by the proven editable path. But non-inplace building must be fixed before any phase that builds out-of-tree"
    why_human: "open Critical in the code-review ledger; severity-vs-phase-scope tradeoff is a human scheduling decision"
---

# Phase 1: MinGW-w64 构建系统 Verification Report

**Phase Goal:** 开发者在 MSYS2 UCRT64 下从源码一步构建 pysam（含 bundled htslib/htscodecs/samtools/bcftools），`import pysam` 在 Windows 开发机可用 — 一切后续工作的前提。
**Verified:** 2026-09-30T03:05:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

Verification method: goal-backward, evidence-first. Per the project anti-pattern forbidding re-runs of the multi-hour build, the build itself is evidenced by on-disk artifacts + the captured clean-state bootstrap log + remote CI records; all loadable behaviors (probe, smoke, import, gate) were re-executed first-hand read-only on 2026-09-30 and passed.

### Observable Truths

ROADmap success criteria (R1-R4) plus plan-level must-haves (P-*), deduplicated.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| R1 | SC-1: one-command UCRT64 build compiles all 13 Cython extensions + bundled htslib/htscodecs/samtools/bcftools, no manual sh configure/make/nm | ✓ VERIFIED | 13 `pysam/libc*.cp314-mingw_x86_64_ucrt_gnu.pyd` + 13 `.dll.a` on disk (counted 2026-09-30); `htslib/config.h` real 6999-byte configure product; `pysam/config.py` HTSLIB=builtin; clean-state log `/c/msys64/tmp/pysam-bootstrap-run.log` contains `smoke OK` (the bootstrap ends with the smoke gate, so the full pipeline ran); configure/make/nm invoked only by setup.py itself (sh -c spawn, MAKE=mingw32-make, llvm-nm) |
| R2 | SC-2: `import pysam` works on Windows, opens a BAM, dispatches samtools+bcftools via `_pysam_dispatch` | ✓ VERIFIED | First-hand 2026-09-30: venv python `import pysam` → `0.24.1 builtin`; `devtools/smoke_test.py` exit 0 `smoke OK` (BAM generated via samtools dispatch, BGZF magic verified, 24 alignments read via AlignmentFile.fetch, bcftools view -H returned 44118 chars) |
| R3 | SC-3: `check_ext_symbol_conflicts` actually runs on Windows via llvm-nm, fails on duplicates, never silently skipped | ✓ VERIFIED | First-hand 2026-09-30: `devtools/probe_symbol_check.py` exit 0 — resolved tool `llvm-nm -g -P` (the real `_nm_command()` exec'd from setup.py source), teeth=904 (same binary judged as two extensions → duplicates detected), honesty=0 across 13 real binaries; bootstrap log grep `skipping symbol collision` = 0 hits; source: win32 dispatch outside exception wrapper (setup.py:457-474) + vacuous-pass guard (setup.py:413-419) + LinkError on any non-exempt duplicate |
| R4 | SC-4: Linux/macOS builds and CI stay green (zero regression) | ✓ VERIFIED | First-hand GitHub API 2026-09-30: run 35353108072 head_sha 0f326879 (phase-final source SHA) completed/success — 19/19 jobs success incl. 17/17 blocking ubuntu\|macos; run 36658641725 head_sha d7d3ba99 also success. Independent code review separately confirms every added platform branch is no-op or byte-identical on POSIX |
| P1a | CRLF Wave-0 blocker cleared (eol=lf contract, renormalized trees) | ✓ VERIFIED | `.gitattributes` five `text eol=lf` rules + preserved export-ignore/linguist lines; `git check-attr eol` → `eol: lf` on htslib/configure, htslib/Makefile, samtools/samtools.pysam.c, bcftools/vcfsom.c, bootstrap script; `git ls-files --eol` → `i/lf w/lf` |
| P1b | One committed script provisions the complete UCRT64 environment | ✓ VERIFIED | `devtools/msys2-bootstrap.sh`: 9-package single-line PKGS, MSYSTEM=UCRT64 gate, HTSLIB_MODE gate, pacman --needed, per-package version log, llvm-nm presence check, MAKE=mingw32-make, venv --system-site-packages, canonical build, smoke gate as final step; clean-state end-to-end log on disk |
| P1c | Smoke gate: nonzero on failure, binary-mode opens, magic assertion, both dispatches | ✓ VERIFIED (documented deviation) | Ran first-hand exit 0; single direct `open()` uses `"rb"`; step 2 asserts gzip/BGZF magic `1f 8b 08 04` + `BC` subfield (stronger than plan's raw `b"BAM\x01"` which only exists in the decompressed stream); input switched to headerful `test_mapped_unmapped.sam` + `catch_stdout=False` — both documented first-build lessons in 01-03-SUMMARY deviation #5 |
| P1d | INSTALL: two manual steps + bootstrap + canonical command + D-05 sentence | ✓ VERIFIED | INSTALL:91-128 'Windows (MSYS2 UCRT64)' section — two manual steps, `sh devtools/msys2-bootstrap.sh`, `pip install -e . --no-build-isolation`, python.org-GCC unsupported sentence, HTSLIB_MODE, --disable-libcurl boundary |
| P2a | Non-UCRT64 Windows python exits immediately with the 9-package message | ✓ VERIFIED | First-hand: `python setup.py --version` under the local non-UCRT64 python → exit 1, message names UCRT64, bootstrap script, and all nine packages (mirroring PKGS incl. the cython rename) |
| P2b | Symbol check via llvm-nm outside the exception-swallowing wrapper; POSIX skip-with-warning byte-identical | ✓ VERIFIED | setup.py:457-474: win32 calls the check directly (loud separate-mode warning only); POSIX try/except with both verbatim warning strings preserved |
| P2c | Getopt cannot false-positive the mandatory gate (module topology) | ✓ VERIFIED (D-16 model) | `win32/getopt.c` referenced by exactly one module dict (libchtslib, setup.py:860); falsified shared-export premise replaced by user-adjudicated D-16: `--exclude-symbols` on every module + private mingwex copies + closed 7-symbol win32 exemption (setup.py:141-144); probe honesty=0 with raw-before-exemption=0 first-hand |
| P2d | No ELF rpath on Windows link lines; import library resolves downstream -l flags | ✓ VERIFIED | setup.py:526-554 win32 elif adds no rpath, emits `-Wl,--out-implib,pysam/lib<stem>.dll.a` (EXT_SUFFIX-derived, no cp3xx literal); POSIX `-Wl,-rpath,$ORIGIN` else-branch unchanged (555-559); 13 implibs on disk; downstream modules linked and importable |
| P2e | Every setup.py change win32-gated; POSIX untouched | ✓ VERIFIED | Source inspection of all gates (`_is_ucrt64_python`, run_configure, `_nm_command`, run(), build_extension, platform.system() branch); independent code review confirms no POSIX behavior change; empirical CI 19/19 green |
| P2f | Hardcoded null-device byte paths replaced by os.devnull | ✓ VERIFIED | pysam/libcutils.pyx:383,390 `force_bytes(os.devnull)`; `grep /dev/null` = 0; only those 2 lines changed vs master (diff stat 4 +/-) |
| P3d | Teeth proven with real built binaries | ✓ VERIFIED | First-hand: probe teeth=904 on the largest real import library judged under two pseudo-names, using setup.py's actual extracted parser |

**Score:** 15/15 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | CR-02: `save_stdout` C `open()` without `O_BINARY` (text-mode fd corrupts BAM/BGZF written through `pysam.utils.dispatch(save_stdout=...)`) | Phase 2 | Phase 2 SC-3 '全部文件 I/O 强制 O_BINARY/"b" 的审计关闭' + PORT-02; pre-existing upstream line, not introduced by this phase; Phase 1 smoke path does not traverse it |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pysam/*.pyd` (13) | compiled UCRT64 extensions | ✓ VERIFIED | 13 on disk, all loadable (import + dispatch proven first-hand) |
| `pysam/*.dll.a` (13) | per-extension import libraries | ✓ VERIFIED | 13 on disk incl. libchtslib.cp314-...dll.a; gate + probe read them |
| `devtools/msys2-bootstrap.sh` | 9-package provisioning contract | ✓ VERIFIED | gsd verify.artifacts pass; content contract fully checked |
| `devtools/smoke_test.py` | acceptance gate | ✓ VERIFIED | gsd pass; ran first-hand exit 0 |
| `devtools/probe_symbol_check.py` | BUILD-03 teeth probe | ✓ VERIFIED | gsd pass; ran first-hand exit 0, exercises setup.py's real parser via ast-extraction |
| `setup.py` | seven win32-gated edits | ✓ VERIFIED | gsd pass; all edits confirmed in source (gate, sh -c configure, llvm-nm, fail-hard dispatch, win32 branch, implib/export-all/exclude-symbols, rpath elif) |
| `pysam/libcutils.pyx` | os.devnull fix | ✓ VERIFIED | gsd pass; 2 call sites |
| `.gitattributes` / `INSTALL` | eol contract / docs | ✓ VERIFIED | gsd pass; content verified |
| `win32/getopt.c` + `win32/getopt.h` | C23-hardened vendored getopt | ✓ VERIFIED | present, modified (explicit prototypes, getopt_long/long_only added); win32/unistd.h + win32/stdint.h deleted (confirmed absent) |

Note: `gsd_run query verify.artifacts` reports 01-03's two build-output artifact entries as "not found" because their PLAN paths are descriptive globs (`pysam/ (13 libc*.pyd ...)`), which the tool resolves literally. Manual Level 1-4 verification above supersedes: the actual artifacts exist, are substantive, wired, and data flows.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| bootstrap PKGS | setup.py gate message | verbatim 9-package mirror | ✓ WIRED | both read side-by-side; identical incl. cython rename; gate fired live with the full list |
| bootstrap | smoke gate | final script step | ✓ WIRED (gsd) | line 90 of the script; log shows smoke ran |
| bootstrap → venv → import | working pysam | D-07/D-14 chain | ✓ WIRED (gsd) | first-hand import + dispatch today |
| libchtslib implib | 12 downstream -l flags | GNU ld lib<name>.dll.a search | ✓ WIRED (manual) | source 526-554 + 13 implibs on disk + all modules linked/import; gsd tool false-negative (descriptive from-path) |
| `_nm_command` | parser | llvm-nm -P POSIX.2 contract | ✓ WIRED (manual) | setup.py:158; probe exec'd the real pair first-hand |
| smoke_test.py | `_pysam_dispatch` | samtools + bcftools dispatch | ✓ WIRED (gsd + live run) | both dispatch paths executed today |
| smoke_test.py | committed test data | repo-root-resolved inputs | ✓ WIRED (gsd) | tests/pysam_data inputs found and consumed |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Symbol-gate teeth + tool + honesty | `python devtools/probe_symbol_check.py` (UCRT64 venv) | exit 0; tool=llvm-nm -g -P; modules=13; teeth=904; honesty=0 | ✓ PASS |
| Smoke gate (SC-2 end-to-end) | `python devtools/smoke_test.py` (UCRT64 venv) | exit 0; 24 alignments; 44118-char bcftools output; `smoke OK` | ✓ PASS |
| import pysam + config | venv `python -c "import pysam; ..."` | `0.24.1 builtin` | ✓ PASS |
| UCRT64 fail-fast gate | `python setup.py --version` (non-UCRT64 python) | exit 1 + full 9-package message | ✓ PASS |
| CI zero-regression | GitHub API runs 35353108072 / 36658641725 | success / success; 19/19 jobs, 17/17 blocking | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BUILD-01 | 01-01, 01-02, 01-03 | UCRT64 dev build pipeline | ✓ SATISFIED | R1, R2, P1a-P1f, P2a, P2d-P2f; REQUIREMENTS.md marks Complete — consistent |
| BUILD-03 | 01-02, 01-03 | symbol-check port with teeth | ✓ SATISFIED | R3, P2b, P2c, P3d; REQUIREMENTS.md marks Complete — consistent |

Orphaned requirements: none — REQUIREMENTS.md traceability maps only BUILD-01/BUILD-03 to Phase 1; both are claimed by plans and verified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| setup.py | 824, 838 | `libcXXX` / `TODO Eventually by running configure` | ℹ️ Info | pre-existing upstream (verbatim on master); not phase-introduced — no debt-marker gate violation |
| win32/getopt.c | 266 | `XXX This is no good solution` | ℹ️ Info | pre-existing vendored FreeBSD getopt (on master); phase only added C23 prototypes |
| setup.py:409 vs 537-554 | — | implib lookup/emission path mismatch (CR-01) | ⚠️ Warning | non-inplace builds crash; does not affect the phase's editable dev-verification flow (gate paths agree for inplace); open in 01-REVIEW-DISPOSITION.md → human triage |
| devtools/probe_symbol_check.py | 107 | cwd-relative glob despite REPO_ROOT (WR-01) | ⚠️ Warning | probe must run from repo root (documented usage); open in ledger |
| devtools/msys2-bootstrap.sh | — | no cwd guard (WR-02) | ⚠️ Warning | run from elsewhere creates _venv in the wrong place; open in ledger |
| .gitattributes | 12-18 | bare `text` forces normalization; comment misstates semantics (WR-03) | ⚠️ Warning | no binary files in covered trees today; open in ledger |
| pysam/libcutils.pyx | 352 | save_stdout without O_BINARY (CR-02) | 📋 Deferred | Phase 2 PORT-02 scope (explicit SC-3 match); pre-existing upstream line |

No phase-introduced TBD/FIXME/XXX markers. No stubs: every artifact is substantive, wired, and (where dynamic) data-flowing.

### Human Verification Required

1. **Ratify prohibition P1 (libcurl off)** — LLM-judge verdict: upheld (bootstrap exports `--disable-libcurl`; `htslib/config.h` has `#undef HAVE_LIBCURL`; INSTALL documents the boundary). Judgment-tier prohibition: only a human can close it.
2. **Ratify prohibition P2 (gate strength) incl. D-16** — LLM-judge verdict: upheld (fail-hard dispatch, vacuous-pass guard, keep-filter unchanged; honesty=0). The single-copy wording was superseded by user-adjudicated D-16 (closed 7-symbol exemption); confirm this is accepted as within the prohibition's intent.
3. **Ratify prohibition P3 (dev-only, no distribution)** — LLM-judge verdict: upheld (no dist/, no .whl, no sdist anywhere).
4. **Triage CR-01 (open Critical)** — non-inplace win32 builds crash at the gate. Not goal-blocking (Phase 1 flow is the editable build; ROADMAP SC-1 is an "or"), but decide fix scheduling before any out-of-tree build phase.

### Gaps Summary

No failed truths, no missing/stub artifacts, no unwired links. All four ROADMAP success criteria are empirically verified — the first three re-proven first-hand on 2026-09-30 against the on-disk build (probe, smoke, import, gate), the fourth via first-hand CI API records on both the phase-final source SHA 0f326879 and the docs SHA d7d3ba99. The status is `human_needed` solely because the three PLAN judgment-tier prohibitions (flagged `unverified`) require explicit human ratification and CR-01 needs a triage decision — none can be silently absorbed into a pass. CR-02 is deferred to Phase 2 by explicit roadmap match.

Note for the orchestrator: local HEAD (dfc149f8, disposition-ledger docs commit) is one docs-only commit ahead of origin/win (d7d3ba99); CI has run green on both prior SHAs and the unpushed delta touches only `.planning/**`.

---

_Verified: 2026-09-30T03:05:00Z_
_Verifier: Claude (gsd-verifier)_
