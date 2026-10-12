---
phase: 03
review: 03-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "VLA-to-heap port of `print_hist` never checks `malloc` failure"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Drop-in headers' `__GNUC__` forwarder gate diverges from `msvc_compat.h`'s `_MSC_VER` gate — breaks the documented clang-cl fallback"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`X_OK` mapped to `6` — contradicts both POSIX and its own comment"
  - id: WR-04
    severity: warning
    disposition: open
    title: "`_collect` UTF-8 rework changes dispatch return type on non-UTF-8-locale POSIX interpreters; in-code comment overclaims \"identical bytes either way\""
  - id: IN-01
    severity: info
    disposition: open
    title: "Stray double semicolons in the `_MSC_VER` arms of `abuf.c`"
  - id: IN-02
    severity: info
    disposition: open
    title: "`opendir`/`readdir` errno mapping is coarse"
  - id: IN-03
    severity: info
    disposition: open
    title: "`gettimeofday` `tv_sec` is 32-bit `long` — year-2038 truncation"
  - id: IN-04
    severity: info
    disposition: open
    title: "`pthread_cond_timedwait` with negative `tv_sec` waits ~49 days instead of timing out"
  - id: IN-05
    severity: info
    disposition: open
    title: "vendor/README.md's \"proven\" probe section still instructs copying `-D hidden=` lines the final design rejected"
  - id: IN-06
    severity: info
    disposition: open
    title: "Test docstring describes the superseded \"replacement\" decode; implementation is strict-first with bytes fallback"
  - id: IN-07
    severity: info
    disposition: open
    title: "`config.h.msvc` SIMD keys are inert for the dedicated AVX2/AVX512 codec TUs under cl"
  - id: IN-08
    severity: info
    disposition: open
    title: "`HTSLIB_MODE=separate` with an MSVC interpreter fails late and confusingly"
  - id: IN-09
    severity: info
    disposition: open
    title: "msvc-build.md states \"win-amd64 CPython 3.13+\" as the prerequisite"
open: 13
total: 13
recorded: 2026-10-12T17:08:39.877Z
---

# Phase 03: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |
| IN-08 | info | open | - |
| IN-09 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
