---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Windows longjmp fix not propagated to the `import/pysam.c` template — regeneration silently reverts it"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "win32 `check_statement` oracle is a tautology — both sides run the same dispatch"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`_compile_sizes` static asserts are swallowed by the blanket `except Exception` — a violated invariant skips instead of failing"
  - id: WR-04
    severity: warning
    disposition: open
    title: "PileupTestUtils oracle comments are false and two builders became token-identical"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "`_WIN32` branch uses GCC-only builtins — will not compile under the planned Phase 3 MSVC toolchain"
  - id: IN-01
    severity: info
    disposition: open
    title: "`psam_open2` + `O_CREAT` would create a mode-0 file on Windows"
  - id: IN-02
    severity: info
    disposition: open
    title: "\"long paths are never truncated\" comments overclaim for `_wopen`/`_wstat`"
  - id: IN-03
    severity: info
    disposition: open
    title: "`_build_httpd` duplicates `_httpd`'s classes verbatim"
  - id: IN-04
    severity: info
    disposition: open
    title: "`TestLogging.check` closes the handler only on the success path"
  - id: IN-05
    severity: info
    disposition: open
    title: "StreamFiledescriptors echo child re-emits CRLF on Windows"
  - id: IN-06
    severity: info
    disposition: open
    title: "tabix generator builds `example.gtf.gz.tbi`, which the Makefile does not list"
open: 8
total: 11
recorded: 2026-10-12T08:49:19.569Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | Phase 3 D-20 — see annotations below |
| WR-02 | warning | fixed | Phase 5 (0e57840c, 0c373d4b) — see annotations below |
| WR-03 | warning | open | partial: 03-05 fixed the assert form; swallow remains — see annotations below |
| WR-04 | warning | open | - |
| WR-05 | warning | fixed | Phase 3 D-20 — see annotations below |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.

## Stale-refresh annotations (2026-10-13, milestone closeout re-verification)

Rows re-triaged against the current tree by the phase-2 stale-refresh verifier.

- **WR-01 — fixed (Phase 3 D-20).** `import/pysam.c:59-75` now carries the Phase-2
  longjmp fix in the template itself, behind the D-20 compiler gate
  (`#if defined(_WIN32) && !defined(_MSC_VER)` → GCC builtins; MSVC/POSIX → standard
  `setjmp`/`longjmp`). Regeneration no longer reverts the fix. Verified by source
  inspection 2026-10-13.
- **WR-02 — fixed (Phase 5).** The win32 `check_statement` oracle no longer re-enters
  the same dispatch: `samtools_test.py:257-265` routes `.bam` comparisons through
  `TestUtils.check_api_readback_equal` (both sides read back via the htslib BAM reader
  behind `pysam.AlignmentFile` — a different code path from the samtools-main writer),
  with `@PG CL` dropped (0c373d4b) and 6 teeth tests in
  `tests/PortabilityRegression_test.py::TestWin32OracleReadback` pinning the rejection
  axes (mutated record, tag-only, header-only differences all rejected). All green on
  both toolchains in the 2026-10-13 re-verification runs (UCRT64 and MSVC each
  1034 passed / 15 skipped / 0 failed).
- **WR-03 — open (partially addressed).** 03-05 (f89add93) replaced the C11
  `_Static_assert` keyword form with the portable negative-array typedef form, removing
  the spurious-compile-failure mode (the asserts now compile and pass under BOTH UCRT64
  gcc and MSVC pyximport — verified 2026-10-13: zero `no pyximport` skips in either
  toolchain's suite run from a proper environment). The blanket `except Exception`
  swallow at `tests/compile_test.py:80-94` remains structural: observed first-hand in
  this re-verification — running pytest from a shell without gcc on PATH silently turns
  the three pyximport-gated tests into `no pyximport` skips (a real compile failure is
  indistinguishable from a missing toolchain). A violated width invariant would still
  skip rather than fail on such an environment. Residual risk, warning-level bookkeeping;
  does not affect any phase-2 must-have (in the sanctioned UCRT64/MSVC environments the
  asserts run and pass).
- **WR-05 — fixed (Phase 3 D-20).** The GCC-only `__builtin_setjmp/longjmp`
  (import/pysam.c:99,115) is now compiled only under
  `#if defined(_WIN32) && !defined(_MSC_VER)`; MSVC builds take the standard
  `setjmp`/`longjmp` path. The MSVC toolchain builds and the full suite is green on it
  (1034/15/0, this re-verification), which is the empirical closure WR-05 asked for.
- **WR-04 — still open.** Note: phase-3 commit f6cf3727 ("fix(03): WR-04 …") refers to
  Phase 3's own review numbering, not this row. No verified closure for the phase-2
  PileupTestUtils-comments finding (POSIX oracle unaffected; win32 comparisons now
  additionally covered by the WR-02 read-back oracle).
