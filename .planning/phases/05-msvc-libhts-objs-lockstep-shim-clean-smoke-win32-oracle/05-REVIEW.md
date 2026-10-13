---
phase: 05-msvc-libhts-objs-lockstep-shim-clean-smoke-win32-oracle
reviewed: 2026-10-13T09:33:53Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - .github/workflows/win-wheels.yaml
  - devtools/check_libhts_objs_lockstep.py
  - devtools/probe_symbol_check.py
  - setup.py
  - tests/PortabilityRegression_test.py
  - tests/TestUtils.py
  - tests/samtools_test.py
  - win32/msvc/dirent.h
  - win32/msvc/pthread.h
  - win32/msvc/shim_selftest.c
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-13T09:33:53Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Review of the debt-cleanup changes since `e36dbd42` across the lockstep comparator, its ast-extraction self-test tool, the shim cosmetics, the clean_smoke parameterization, the win32 read-back oracle, and the probe filter.

Verification performed (not just reading — the claims were executed):

- **Lockstep mirror is factually correct.** The 52-entry `MSVC_LIBHTS_OBJS` list was cross-checked against `htslib/Makefile` (`LIBHTS_OBJS` top-level + cram entries + `HTSCODECS_SOURCES` in `htscodecs_bundled.mk` + `NONCONFIGURE_OBJS=` blanking in the `--disable-libcurl` config): 27 + 11 + 14 = 52 TUs, set-equal to the mirror. The ast extraction (`_load_real_comparator`) was run and works; the comparator was fed the real expansion (PASS) and a phantom token (raises `LinkError`) — teeth confirmed.
- **Wiring is correct and regression-free.** The check sits in the non-MSVC branch and is gated `sys.platform == 'win32'`, i.e. exactly the UCRT64 dev build; Linux/macOS never reach it; the MSVC arm (`IS_MSVC_PYTHON`) remains autotools-free and never self-compares its own mirror. The unconditional-failure-on-libcurl-configure behavior is documented intent in the comment.
- **Oracle tests pass and the comparator is semantically sound.** All 4 `TestWin32OracleReadback` tests pass; the comparator was additionally probed: tag-only (non-MD/NM), header-only (@SQ LN), and record-count differences are all correctly rejected. MD/NM exclusion is symmetric on both sides and mirrors `check_samtools_view_equal`'s `-x MD -x NM` (parity by design; accepted). The win32 elif rung is purely additive for the POSIX ladder (POSIX evaluation of the condition is unchanged).
- **Workflow is injection-safe and the guards are intact.** `smoke_python` is a `choice` input bounded to the six built versions — no free-form value can reach a shell line; all `run:` blocks remain free of `${{ }}` interpolation (env-indirect `SMOKE_PY`/`SMOKE_CP`/`MSYS2_LOCATION`/`TAG`); the release job's `if: startsWith(github.ref, 'refs/tags/v')` guard is untouched; the `CIBW_TEST_COMMAND` → `CIBW_TEST_COMMAND_WINDOWS` correction is accurate (cibuildwheel documents per-platform test-command overrides, consistent with the sibling `_WINDOWS` keys already used in this file). The `SMOKE_CP` bash expansion (`${SMOKE_PY/./}` → `cp313`) and the install glob `dist/*-${SMOKE_CP}-${SMOKE_CP}-win_amd64.whl` reproduce the previous literal exactly.
- **Shim changes are cosmetic-plus.** `dirent.h`/`pthread.h` end-tags are comment-only edits that now match the actual `defined(__GNUC__) && !defined(_MSC_VER)` guard; the `shim_selftest.c` dirent sentinel is a compile-level address-taken type probe that works under both the forwarder arm and the MSVC drop-in, and the "all five drop-in headers" claim matches the directory (dirent, pthread, strings, unistd, sys/time).
- **Probe filter is correct.** The `REPO_ROOT` anchor plus `sysconfig.get_config_var("EXT_SUFFIX")` scoping selects exactly the running interpreter's toolchain artifacts; a wrong-interpreter run fails loudly (missing `.dll.a`), never silently mis-verdicts.

No blockers. Three warnings: the comparator cannot detect duplicate mirror entries; the oracle's @PG tolerance strips whole lines where the documented rationale only covers the CL field; and the new teeth tests do not pin the tag- and header-rejection axes they were written to protect.

## Warnings

### WR-01: Lockstep comparator is blind to duplicate entries in MSVC_LIBHTS_OBJS

**File:** `setup.py:163-165`
**Issue:** The comparator reduces the mirror to a set (`set(MSVC_LIBHTS_OBJS)`) before comparing, so a hand-maintained duplicate entry (copy-paste drift — exactly the drift class this gate exists to catch) passes set-equality silently. The MSVC module graph at `setup.py:1079` (`[os.path.join("htslib", o[:-2] + ".c") for o in MSVC_LIBHTS_OBJS]`) would then compile the same TU twice, surfacing as a confusing MSVC link failure (or a duplicate-object warning) far from the root cause, and the standalone devtool reports "lockstep OK" because it re-uses the same comparator. Currently the list is clean (verified: 52 entries, 52 unique), but the gate's own comment says it exists so mirror drift "can never silently strand the hand-maintained MSVC module graph" — this drift class does exactly that.
**Fix:** Assert uniqueness before the set comparison:

```python
mirror_objs = set(MSVC_LIBHTS_OBJS)
if len(mirror_objs) != len(MSVC_LIBHTS_OBJS):
    dupes = sorted(o for o in mirror_objs
                   if MSVC_LIBHTS_OBJS.count(o) > 1)
    raise LinkError(
        "MSVC_LIBHTS_OBJS contains duplicate entries: %s"
        % " ".join(dupes))
```

### WR-02: check_api_readback_equal strips entire @PG lines, not just the CL field that carries the per-side filename

**File:** `tests/TestUtils.py:148-152`
**Issue:** The docstring justifies @PG exclusion solely by "the CL field embeds the per-side output filename", but the implementation drops every line starting with `@PG`. Consequences: a win32 samtools_test pair where one side dropped its @PG record entirely, wrote a corrupt/truncated @PG, or diverged in PN/ID/PP passes the oracle as "equal". Since both sides run the same command against the same input with only the output-name substituted, filtering just the CL field would keep the gate strictly stronger with no added false positives.
**Fix:**

```python
def _drop_pg_cl(line):
    if not line.startswith("@PG"):
        return line
    return "\t".join(f for f in line.split("\t")
                     if not f.startswith("CL:"))

header1 = [_drop_pg_cl(line) for line in str(inf1.header).splitlines()]
```

### WR-03: Oracle teeth tests do not pin the tag-comparison and header-comparison rejection axes

**File:** `tests/PortabilityRegression_test.py:325-370`
**Issue:** The four tests cover exactly one rejection axis (record field mutation via mapq). Deleting the tags block (`TestUtils.py:159-164`) or the header block (`TestUtils.py:148-153`) from the comparator leaves all four tests green — verified by probing the comparator directly: it does reject tag-only (`RG: grp1` vs `RG: grp2`) and header-only (`SQ LN 1000` vs 2000) differences today, but no test would notice if that regressed. For a phase whose deliverable is "teeth tests (RED)", the tag and header axes of the oracle are currently unguarded.
**Fix:** Add the two rejection tests (both pass against the current comparator):

```python
def test_tag_difference_rejected(self, tmp_path):
    from TestUtils import check_api_readback_equal
    bam_a = _write_oracle_bam(os.path.join(str(tmp_path), "a.bam"),
                              tags=[("RG", "grp1")])
    bam_b = _write_oracle_bam(os.path.join(str(tmp_path), "b.bam"),
                              tags=[("RG", "grp2")])
    assert not check_api_readback_equal(bam_a, bam_b)

def test_header_difference_rejected(self, tmp_path):
    from TestUtils import check_api_readback_equal
    h2 = {"HD": {"VN": "1.6", "SO": "coordinate"},
          "SQ": [{"SN": "chr1", "LN": 2000}]}
    bam_a = _write_oracle_bam(os.path.join(str(tmp_path), "a.bam"))
    bam_b = _write_oracle_bam(os.path.join(str(tmp_path), "b.bam"),
                              header=h2)
    assert not check_api_readback_equal(bam_a, bam_b)
```

## Info

### IN-01: Lockstep wiring adds a new KeyError surface in HTSLIB_MODE=separate on win32

**File:** `setup.py:866-868`
**Issue:** `htslib_make_options["LIBHTS_OBJS"]` is a hard index. In `shared` mode the key was already required later (`setup.py:932`, pre-existing), but `separate` mode never needed it until now. If `make -s print-config` output ever lacks a parseable LIBHTS_OBJS line, the failure is a bare `KeyError` traceback instead of an actionable gate message. Practical risk is low (the vendored Makefile unconditionally echoes it, and the expansion cannot contain `=`), but the new dependency deserves a clean failure.
**Fix:** `expansion = htslib_make_options.get("LIBHTS_OBJS")` and raise an explicit `LinkError("make print-config produced no LIBHTS_OBJS line")` when `None`.

### IN-02: devtool re-implements the print-config parse and skips set_compiler_envvars while claiming parity fidelity

**File:** `devtools/check_libhts_objs_lockstep.py:74-101`
**Issue:** The module's "never re-implemented / single source of truth" claim is true for the comparator but not for the parse: `_make_print_config_libhts_objs` duplicates `run_make_print_config`'s splitting discipline, so a future parse change in setup.py silently diverges the tool (it could have ast-extracted `run_make_print_config` the same way, seeding the namespace with `subprocess`). Also, `_run_parity_configure` reproduces "run_configure's exact argv" but not `configure_library`'s `set_compiler_envvars()` context (CC/CFLAGS/LDFLAGS exported from sysconfig). Verdict-equivalent in practice — LIBHTS_OBJS membership depends only on NONCONFIGURE_OBJS/libcurl and bundled-vs-external htscodecs, none of which CC/CFLAGS flip — but worth a docstring qualifier so the parity claim is not over-read.
**Fix:** Extract `run_make_print_config` via the same ast mechanism (or note the deliberate parse duplication), and mention in the docstring that configure runs without setup.py's compiler env exports.

### IN-03: Tag dict comparison is blind to SAM type changes (i:5 vs f:5.0)

**File:** `tests/TestUtils.py:159-164`
**Issue:** Converting tags to `{k: v}` dicts and comparing with `==` makes an integer 5 and a float 5.0 for the same tag key compare equal, so a tag-serialization bug that changes the BAM type code passes the oracle. The old text-based comparator (`check_samtools_view_equal` compares `NM:i:0`-style text) would have caught it. Marginal practical risk, but a real detection regression on this axis.
**Fix:** Compare the type code too, e.g. `{k: (type(v).__name__, v) for ...}` or keep tag order and compare `(read1.tags or [])` lists after filtering.

### IN-04: clean_smoke default Python is defined twice and can drift

**File:** `.github/workflows/win-wheels.yaml:16,96`
**Issue:** The `'3.13'` literal exists both as the workflow_dispatch input default and as the tag-push fallback in `SMOKE_PY: ${{ inputs.smoke_python || '3.13' }}`. The comment explains why the fallback exists, but nothing keeps the two literals in sync: bumping the input default without the fallback (or vice versa) silently makes tag-push smoke tests run a different Python than dispatch runs. Not a publish-safety issue (both must be one of the six built versions), but a maintenance trap in the publish pipeline.
**Fix:** A step-level `SMOKE_PY: ${{ inputs.smoke_python || env.DEFAULT_SMOKE_PY }}` shape, or a single comment-anchored literal pair with a TODO to keep in sync; simplest is to note both lines in the same comment block.

### IN-05: Redundant per-test local imports in the new oracle tests

**File:** `tests/PortabilityRegression_test.py:327,337,346,359` (and `import shutil` at 336)
**Issue:** `from TestUtils import check_api_readback_equal` is repeated inside all four test functions although the module already imports `TestUtils` at top (`PortabilityRegression_test.py:23`). Harmless, but four copies invite copy-paste drift and imply a dependency isolation that the module-level import already breaks.
**Fix:** Move `check_api_readback_equal` into the top-level `from TestUtils import ...` line and drop the local imports.

---

_Reviewed: 2026-10-13T09:33:53Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
