---
phase: 05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle
verified: 2026-10-13T10:12:00Z
status: passed
score: 5/5 must-haves verified
covered_files: [".github/workflows/win-wheels.yaml", ".planning/phases/05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle/05-01-PLAN.md", ".planning/phases/05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle/05-01-SUMMARY.md", "devtools/check_libhts_objs_lockstep.py", "devtools/probe_symbol_check.py", "setup.py", "tests/PortabilityRegression_test.py", "tests/TestUtils.py", "tests/samtools_test.py", "win32/msvc/dirent.h", "win32/msvc/pthread.h", "win32/msvc/shim_selftest.c"]
covered_digest: "v3:sha256:996a7d08825ab1758e1a65ef0bb9e842dbcde1b9a2f267e809b53dae20b94962"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 05: Tech-Debt Cleanup Verification Report

**Phase Goal:** 清理 v1 里程碑审计记录的打磨项（技术债清理 phase，无新需求；05-CONTEXT debt items 1-4 为必做规格）
**Verified:** 2026-10-13T10:12:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

All five roadmap Success Criteria map 1:1 to the PLAN's five must-have truths. Every
behavior-dependent truth was exercised live by this verifier (not inferred from
presence): the lockstep self-test and both toolchain pytest/smoke batteries were
re-run in this verification session, and the CI evidence was audited via `gh` run
records.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Lockstep: any add/remove/duplicate divergence between MSVC_LIBHTS_OBJS mirror and htslib/Makefile expansion fails UCRT64 build with actionable diff; standalone devtools check, same verdict via ast-extraction; teeth proven by synthetic-drift self-test | ✓ VERIFIED | Comparator `setup.py:151-191` (set-compare + WR-01 duplicate gate + sorted add/drop diff + TU counts + parity hint, raises LinkError); wired win32-guarded at `setup.py:877-879` in the non-MSVC branch after `run_make_print_config()`; MSVC arm (`setup.py:843-859`) autotools-free and check-free. **Live**: UCRT64 `--self-test` exit 0 — mirror 52 == parity expansion 52, synthetic drift raised LinkError, duplicated mirror entry raised LinkError (WR-01 teeth); UCRT64 `setup.py --name` exit 0 (wired path executes); MSVC `setup.py --name` exit 0. Script ast-extracts comparator+mirror verbatim (`_load_real_comparator`) — never re-implements |
| 2 | shim_selftest covers all five drop-ins under BOTH cl and UCRT64 gcc; stale end-tags state full condition | ✓ VERIFIED | `shim_selftest.c:14-19` five drop-in includes (dirent.h added), `struct dirent` sentinel touch (lines 32-38, address taken, no fs call); `pthread.h:126` + `dirent.h:41` both `#endif /* __GNUC__ && !_MSC_VER */`. **Live**: cl probe "2 passed, 0 failed"; UCRT64 `gcc -fsyntax-only` FORWARDER-OK; gates re-run: drop-in-includes=5, stale-tags=0, corrected-tag-files=2 |
| 3 | clean_smoke Python version defined in exactly one place (dispatch input, default 3.13) with derived cp-tag glob; no cp313 literal in job; no ${{ }} in run blocks; suffixed CIBW key; proven by tag run AND non-default dispatch | ✓ VERIFIED | `win-wheels.yaml`: choice input (six versions, default '3.13') → job env `SMOKE_PY` (fallback literal for tag runs) → bash-derived `SMOKE_CP` → setup-python + install glob `dist/*-${SMOKE_CP}-${SMOKE_CP}-win_amd64.whl`; `CIBW_TEST_COMMAND_WINDOWS`; msys2-location env-indirect. Gates re-run: cp313-in-clean_smoke=0, run-interpolations=0 (file-wide), suffixed-key=1; `'3.13'` literals = 3 (options vocabulary + 2 defaults — intent of the plan's unsatisfiable B-regex, SUMMARY deviation #4). **Live (audited via gh)**: tag run 38369651968 (branch win-test.3) conclusion success — build_wheels success, clean_smoke success, release skipped by guard; dispatch run 38369877795 (event workflow_dispatch) conclusion success with SMOKE_CP=cp312 derivation + cp312 install glob in job log |
| 4 | win32 BAM rung reads back through pysam.AlignmentFile (no dispatch re-entry); comparator teeth proven by synthetic mutation tests; POSIX ladder textually unchanged | ✓ VERIFIED | `TestUtils.check_api_readback_equal` (lines 144-176): both sides via AlignmentFile rb, header lines minus @PG CL field only (WR-02 `_drop_pg_cl`), records pairwise via `dict_of_read` + `zip_longest`, tags minus MD/NM; win32-guarded elif rung at `samtools_test.py:257-265` inserted before the untouched POSIX BAM rung. **Live**: phase diff gate re-run — only removed line in samtools_test.py is the extended TestUtils import (pure addition); 6 teeth tests (mutated record, tag-only, header-only rejected; byte-copy, MD/NM-only, PG-CL-only accepted) green on BOTH toolchains inside the 33/33 runs; full samtools_test green on both (strengthened rung live on win32 accepts dispatch pairs) |
| 5 | Zero regression: dual-toolchain smoke; touched test files green on both toolchains; fork CI green on phase-final SHA | ✓ VERIFIED | **Live (this verifier)**: smoke OK ×2 (UCRT64 + MSVC); `pytest samtools_test.py PortabilityRegression_test.py` = 33 passed ×2 (matches post-review count: 31 + 2 WR-03 teeth); probe from /tmp cwd = "probe OK: teeth=904". **CI (audited via gh)**: run 38370847255 on phase code-final SHA 0e57840c = success; run 38374832794 on 8073676e = success; all 12 recent win-branch runs green. See Advisory for the unpushed post-review commits |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Advisory (New Scope, Unevidenced)

Initial verification — frontmatter advisory list not applicable. Two informational
notes for the orchestrator (neither blocks; neither is a must-have failure):

1. **Post-review fix commits are unpushed.** `origin/win` is at 8073676e; local HEAD
   965760f1 is 6 commits ahead (efe5a2b0 setup.py WR-01, 0c373d4b TestUtils WR-02,
   7b0c4256 teeth tests WR-03, + 3 docs). No fork-CI evidence can exist for them yet.
   This verifier re-ran the full Windows battery on the current tree (self-test incl.
   WR-01 duplicate teeth; 33/33 ×2 incl. WR-02/WR-03 tests; smokes ×2), and the
   unpushed code diff is confined to the win32-guarded comparator internals and
   additive tests (POSIX paths textually unchanged — verified by diff). Action:
   after the orchestrator bundles and pushes, confirm CI green on the new HEAD before
   milestone close.
2. **Open info findings IN-01..IN-05** (05-REVIEW-DISPOSITION) remain open by design —
   ledger items for the next audit cycle, not phase gaps. IN-01 (KeyError surface in
   HTSLIB_MODE=separate on win32) is the most substantive: the wiring indexes
   `htslib_make_options["LIBHTS_OBJS"]`, which would KeyError if print-config ever
   omitted the key.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `devtools/check_libhts_objs_lockstep.py` | NEW standalone lockstep check + self-test teeth | ✓ VERIFIED | 169 lines; ast-extracts comparator+mirror; parity configure + print-config; dual teeth (drift + duplicate). Live exit 0 |
| `setup.py` | comparator + win32-guarded wiring at print-config site | ✓ VERIFIED | Two hunks (151-191, 870-879); nothing inside IS_MSVC_PYTHON branch — confirmed by diff-confinement analysis |
| `win32/msvc/shim_selftest.c`, `pthread.h`, `dirent.h` | five-drop-in sentinel + corrected tags | ✓ VERIFIED | Compiles under cl (2/0) and UCRT64 gcc; grep gates pass |
| `.github/workflows/win-wheels.yaml` | parameterized clean_smoke + comment/env fixes | ✓ VERIFIED | Structural gates pass; two live CI runs green |
| `tests/samtools_test.py`, `TestUtils.py`, `PortabilityRegression_test.py` | API read-back oracle + rung + teeth tests | ✓ VERIFIED | 33/33 both toolchains; pure-addition ladder diff |
| `devtools/probe_symbol_check.py` | REPO_ROOT-anchored, EXT_SUFFIX-scoped glob | ✓ VERIFIED | Live from /tmp: "probe OK: teeth=904" |

Tool note: `verify.artifacts`/`verify.key-links` returned NO_INPUT — this PLAN's
must_haves use bare string lists, not the tool's object shape. Manual three-level
verification (exists / substantive / wired) above is authoritative.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| setup.py comparator | devtools ast-extraction | `_load_real_comparator` exec-extracts function + mirror verbatim | ✓ WIRED | Single source of truth; script contains no re-implementation of the rule |
| UCRT64 build path (print-config site) | lockstep enforcement | win32-guarded call, `setup.py:877-879` | ✓ WIRED | Live: UCRT64 `setup.py --name` exit 0 executes the check; MSVC arm stays autotools-free (exit 0, no configure output) |
| smoke_python input | setup-python → SMOKE_CP → install glob | job env + GITHUB_ENV derivation | ✓ WIRED | One definition, zero sync sites; dispatch run log shows cp312 glob installing cp312 wheel |
| win32 BAM rung | TestUtils.check_api_readback_equal | import + assert at `samtools_test.py:265` | ✓ WIRED | Reader path (AlignmentFile) independent of writer (dispatch); exercised by both toolchain suite runs |

### Data-Flow Trace (Level 4)

Not applicable — no rendered dynamic-data artifacts this phase (build scripts, C
headers, workflow YAML, test comparators). Every value trace terminates in a real
source: lockstep verdict ← live `make print-config` expansion (52 TUs, re-generated
this session); SMOKE_CP ← dispatch input (proven in run log); oracle comparisons ←
real BAM bytes read back through AlignmentFile.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Lockstep self-test (real parity + drift teeth + duplicate teeth) | UCRT64 `check_libhts_objs_lockstep.py --self-test` | exit 0: mirror 52 == expansion 52; both teeth raised LinkError | ✓ PASS |
| Wired check executes in build path | UCRT64 `MAKE=mingw32-make setup.py --name` | exit 0, prints `pysam` | ✓ PASS |
| MSVC short-circuit arm untouched | `_venv-msvc` `setup.py --name` | exit 0, prints `pysam`, no configure output | ✓ PASS |
| cl compiles both shim TUs | `msvc_compile_probe.py ... -I win32/msvc -I win32` | 2 passed, 0 failed | ✓ PASS |
| UCRT64 forwarder arm | `gcc -fsyntax-only -I win32/msvc shim_selftest.c` | FORWARDER-OK | ✓ PASS |
| Oracle teeth tests + touched suites (UCRT64) | `pytest samtools_test.py PortabilityRegression_test.py -q` | 33 passed in 2.87s | ✓ PASS |
| Oracle teeth tests + touched suites (MSVC) | same, `_venv-msvc` | 33 passed in 2.94s | ✓ PASS |
| Smoke (UCRT64 / MSVC) | `devtools/smoke_test.py` ×2 | smoke OK ×2 | ✓ PASS |
| Probe cwd independence | from `/tmp`, UCRT64 | "probe OK: tool=llvm-nm -g -P teeth=904 honesty=0" | ✓ PASS |
| Tag-run CI evidence | `gh run view 38369651968` | success; release skipped by tag guard | ✓ PASS |
| Dispatch CI evidence (non-default input) | `gh run view 38369877795` + clean_smoke job log | success; SMOKE_CP=cp312 derivation + cp312 install | ✓ PASS |
| Fork CI on phase-final SHA | `gh run list --branch win` | 38370847255 on 0e57840c success; all recent runs success | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` conventional probes exist; phase verification is the
devtools/self-test/CI battery above, all executed directly (see Behavioral
Spot-Checks).

### Requirements Coverage

Phase declares `requirements: []` (debt-cleanup — 13/13 v1 requirements already
satisfied in phases 1-4 per v1-MILESTONE-AUDIT). REQUIREMENTS.md maps no IDs to
phase 5 — no orphans. Not applicable by design.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| setup.py | 1225 | Pre-existing upstream `TODO` (outside both phase hunks) | ℹ️ Info | Not phase-introduced; upstream residue |
| tests/samtools_test.py | 75-105, 293 | Pre-existing upstream `TODO` comments (outside phase hunks) | ℹ️ Info | Not phase-introduced; upstream residue |

No TBD/FIXME/XXX anywhere in phase-touched files; no new debt markers; no stub
patterns (all values flow to real sources). The phase's own hunks are marker-free.

### Human Verification Required

None. All truths verified by direct behavioral execution or auditable external run
records; no visual/UI/UX surface in this phase.

### Gaps Summary

No gaps. All five roadmap success criteria (lockstep gate with teeth, five-drop-in
sentinel + corrected tags, single-definition clean_smoke proven by two live CI runs,
independent win32 read-back oracle with teeth, zero regression) verified against the
actual codebase with first-hand behavioral evidence on both Windows toolchains. The
post-summary review round (WR-01/02/03) is fixed in the verified tree and its fixes
were exercised by this verification's runs. Two informational advisories recorded
above (unpushed post-review commits pending CI evidence at push time; five open info
findings ledgered for the next audit cycle).

---

_Verified: 2026-10-13T10:12:00Z_
_Verifier: Claude (gsd-verifier)_
