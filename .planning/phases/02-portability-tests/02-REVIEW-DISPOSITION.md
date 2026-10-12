---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Windows longjmp fix not propagated to the `import/pysam.c` template — regeneration silently reverts it"
  - id: WR-02
    severity: warning
    disposition: open
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
    disposition: open
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
open: 11
total: 11
recorded: 2026-10-12T08:49:19.569Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
