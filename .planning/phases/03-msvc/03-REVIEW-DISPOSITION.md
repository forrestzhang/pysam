---
phase: 03
review: 03-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: open
    title: "`shim_selftest.c` probes four of the five drop-in headers — `dirent.h` is not exercised"
  - id: IN-02
    severity: info
    disposition: open
    title: "Stale `#endif /* __GNUC__ */` end comments after the WR-02 gate rename"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "VLA-to-heap port of `print_hist` never checks `malloc` failure"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Drop-in headers' `__GNUC__` forwarder gate diverges from `msvc_compat.h`'s `_MSC_VER` gate"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`X_OK` mapped to `6` — contradicts both POSIX and its own comment"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "`_collect` UTF-8 rework changes dispatch return type on non-UTF-8-locale POSIX interpreters; in-code comment overclaims"
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
open: 9
total: 13
recorded: 2026-10-12T17:33:35.468Z
---

# Phase 03: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| WR-01 | warning | fixed | 03-REVIEW-FIX.md iter1 (not in the current review) |
| WR-02 | warning | fixed | 03-REVIEW-FIX.md iter1 (not in the current review) |
| WR-03 | warning | fixed | 03-REVIEW-FIX.md iter1 (not in the current review) |
| WR-04 | warning | fixed | 03-REVIEW-FIX.md iter1 (not in the current review) |
| IN-03 | info | open | - (not in the current review) |
| IN-04 | info | open | - (not in the current review) |
| IN-05 | info | open | - (not in the current review) |
| IN-06 | info | open | - (not in the current review) |
| IN-07 | info | open | - (not in the current review) |
| IN-08 | info | open | - (not in the current review) |
| IN-09 | info | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
