---
phase: 05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle
fixed_at: 2026-10-13T09:48:04Z
review_path: .planning/phases/05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle/05-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 5: Code Review Fix Report

**Fixed at:** 2026-10-13T09:48:04Z
**Source review:** .planning/phases/05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope (critical_warning): 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### WR-01: Lockstep comparator is blind to duplicate entries in MSVC_LIBHTS_OBJS

**Files modified:** `setup.py`, `devtools/check_libhts_objs_lockstep.py`
**Commit:** efe5a2b0
**Applied fix:** Added a length/uniqueness check on `MSVC_LIBHTS_OBJS` before the set comparison in `check_msvc_libhts_objs_lockstep` (`setup.py`): `len(set(MSVC_LIBHTS_OBJS)) != len(MSVC_LIBHTS_OBJS)` now raises `LinkError("MSVC_LIBHTS_OBJS contains duplicate entries: ...")` naming the duplicated entries. Comparator docstring updated ("Any add, remove, or duplicate divergence"). Because the devtool ast-extracts the comparator verbatim, it inherits the check; the `--self-test` was extended (trivially additive, as authorized) with a duplicate-mirror teeth case: one mirror entry is duplicated in the comparator's exec-namespace globals, the comparator must raise, and the mirror is restored in a `finally`. The pre-existing synthetic-drift (add/remove) self-test case is unchanged and still passes. Verified standalone before commit: clean mirror passes, duplicated mirror raises naming `kfunc.o`, drifted expansion still raises.

### WR-02: check_api_readback_equal strips entire @PG lines, not just the CL field that carries the per-side filename

**Files modified:** `tests/TestUtils.py`
**Commit:** 0c373d4b
**Applied fix:** Added module-level helper `_drop_pg_cl(line)`: non-@PG lines pass through unchanged; @PG lines are rewritten with only the `CL:` field removed (`"\t".join(f for f in line.split("\t") if not f.startswith("CL:"))`). `check_api_readback_equal` now maps both header line lists through `_drop_pg_cl` instead of dropping every `@PG` line; docstring updated to "header text lines with the @PG CL field dropped". Caller audit re-confirmed before editing: the only production caller remains `tests/samtools_test.py:265` inside the `elif sys.platform == 'win32' and s.endswith(".bam")` rung — the POSIX ladder (`check_samtools_view_equal` rung) is untouched. Functionally probed before commit: CL-only @PG difference still accepted (no new false positive; existing `test_pg_header_difference_accepted` stays green), @PG PN divergence now rejected, one-side-dropped @PG record now rejected.

### WR-03: Oracle teeth tests do not pin the tag-comparison and header-comparison rejection axes

**Files modified:** `tests/PortabilityRegression_test.py`
**Commit:** 7b0c4256
**Applied fix:** Added `test_tag_difference_rejected` (RG: grp1 vs grp2 — tag-only difference, no record-field change) and `test_header_difference_rejected` (default ORACLE_HEADER vs SQ LN 1000 vs 2000 — header-only difference, identical records) to `TestWin32OracleReadback`, placed after `test_mutated_record_rejected`, using the same local-import style as the four existing tests (IN-05's top-level-import cleanup is out of scope for this run). TDD shape confirmed: both tests pass against the current comparator (class run: 6/6 green) — no comparator gap was exposed, so no comparator change was needed.

## Verification

All verification ran in the **main checkout** (`workflow.use_worktrees=false` — no isolated worktree was created; numbers are reproducible from this tree):

- UCRT64 lockstep self-test: `MAKE=mingw32-make _venv/bin/python.exe devtools/check_libhts_objs_lockstep.py --self-test` — exit 0; output: `mirror TUs: 52`, `lockstep OK: mirror == parity expansion (52 TUs)`, `teeth OK: synthetic drift raised LinkError (2-TU delta)`, `teeth OK: duplicated mirror entry raised LinkError` (new).
- UCRT64 `setup.py --name`: exit 0, prints `pysam` (also exercises the wired build-time comparator — no LinkError).
- UCRT64 pytest: `_venv/bin/python.exe -m pytest tests/PortabilityRegression_test.py tests/samtools_test.py -q` — 33 passed (was 31; +2 from WR-03 tests).
- MSVC pytest: `D:/Github/pysam/_venv-msvc/Scripts/python.exe -m pytest tests/PortabilityRegression_test.py tests/samtools_test.py -q` — 33 passed.
- MSVC `setup.py --name`: exit 0, prints `pysam`.

## Out-of-Scope Findings (open advisory)

The five Info findings (IN-01..IN-05) were excluded per `fix_scope: critical_warning` and remain open advisory items:

- **IN-01** — `setup.py:866-868`: hard `htslib_make_options["LIBHTS_OBJS"]` index adds a bare-`KeyError` surface in `HTSLIB_MODE=separate` on win32.
- **IN-02** — `devtools/check_libhts_objs_lockstep.py:74-101`: devtool re-implements the print-config parse and skips `set_compiler_envvars` while claiming parity fidelity.
- **IN-03** — `tests/TestUtils.py:159-164`: tag dict comparison blind to SAM type changes (`i:5` vs `f:5.0`).
- **IN-04** — `.github/workflows/win-wheels.yaml:16,96`: clean_smoke default Python literal defined twice, can drift.
- **IN-05** — `tests/PortabilityRegression_test.py`: redundant per-test local imports of `check_api_readback_equal`.

---

_Fixed: 2026-10-13T09:48:04Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
