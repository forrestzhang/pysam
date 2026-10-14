---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "`_collect` decodes captured stdout/stderr with the Windows ANSI code page — mojibake passes silently and binary can skip the `\"rb\"` fallback"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`parse_region` crashes with `IndexError` on single-coordinate region strings (`\"chr1:100\"`)"
  - id: IN-01
    severity: info
    disposition: open
    title: "`calmd` mapping appends an empty-string argv entry to the dispatch call"
  - id: IN-02
    severity: info
    disposition: open
    title: "dead imports/cimports"
  - id: IN-03
    severity: info
    disposition: open
    title: "`c_open2(os.devnull)` return value not checked"
  - id: CR-01
    severity: critical
    disposition: deferred
    title: "Win32 symbol gate reads implib beside `get_ext_fullpath`, but implib is emitted into source-tree `pysam/` — non-inplace builds crash"
  - id: CR-02
    severity: critical
    disposition: open
    title: "`save_stdout` redirect uses C `open()` without `O_BINARY` — text-mode fd silently corrupts BAM/BGZF written through it on Windows"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`.gitattributes` uses unconditional `text eol=lf` over whole vendored trees, and its comment misstates git semantics"
open: 6
total: 8
recorded: 2026-10-12T10:30:01.354Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| CR-01 | critical | deferred | triaged 2026-09-30 during UAT (user-delegated): verified first-hand — implib emitted cwd-relative to source-tree pysam/ (setup.py:546-554) while gate reads beside get_ext_fullpath (setup.py:405-410); paths agree on inplace (Phase 1-2 dev flow), diverge on non-inplace (pip install ., setup.py build, bdist_wheel → CalledProcessError). Deferred to Phase 3 entry (BUILD-02): first out-of-tree build phase; fix = derive implib path from os.path.dirname(get_ext_fullpath) (not in the current review) |
| CR-02 | critical | fixed | resolved by Phase 2 psam_open3/psam_wopen rewiring (dc40dd29): save_stdout fd now opened with _O_BINARY via _wopen — verified against generated pysam/libcutils.c:1448-1477 in the 2026-10-12 incremental re-review (not in the current review) |
| WR-03 | warning | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
