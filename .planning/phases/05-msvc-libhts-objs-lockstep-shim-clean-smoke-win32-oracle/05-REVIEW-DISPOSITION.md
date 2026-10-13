---
phase: 05
review: 05-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Lockstep comparator is blind to duplicate entries in MSVC_LIBHTS_OBJS"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "check_api_readback_equal strips entire @PG lines, not just the CL field that carries the per-side filename"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "Oracle teeth tests do not pin the tag-comparison and header-comparison rejection axes"
  - id: IN-01
    severity: info
    disposition: open
    title: "Lockstep wiring adds a new KeyError surface in HTSLIB_MODE=separate on win32"
  - id: IN-02
    severity: info
    disposition: open
    title: "devtool re-implements the print-config parse and skips set_compiler_envvars while claiming parity fidelity"
  - id: IN-03
    severity: info
    disposition: open
    title: "Tag dict comparison is blind to SAM type changes (i:5 vs f:5.0)"
  - id: IN-04
    severity: info
    disposition: open
    title: "clean_smoke default Python is defined twice and can drift"
  - id: IN-05
    severity: info
    disposition: open
    title: "Redundant per-test local imports in the new oracle tests"
open: 5
total: 8
recorded: 2026-10-13T09:49:29.028Z
---

# Phase 05: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 05-REVIEW-FIX.md iter1 |
| WR-02 | warning | fixed | 05-REVIEW-FIX.md iter1 |
| WR-03 | warning | fixed | 05-REVIEW-FIX.md iter1 |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |

Dispositions: `open`, `fixed`, `skipped`, `deferred`.
