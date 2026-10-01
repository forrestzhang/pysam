---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: deferred
    title: "Win32 symbol gate reads implib beside `get_ext_fullpath`, but implib is emitted into source-tree `pysam/` — non-inplace builds crash"
  - id: CR-02
    severity: critical
    disposition: open
    title: "`save_stdout` redirect uses C `open()` without `O_BINARY` — text-mode fd silently corrupts BAM/BGZF written through it on Windows"
  - id: WR-01
    severity: warning
    disposition: open
    title: "`probe_symbol_check.py` computes `REPO_ROOT` but globs with a cwd-relative path"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`msys2-bootstrap.sh` silently depends on being run from the repo root"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`.gitattributes` uses unconditional `text eol=lf` over whole vendored trees, and its comment misstates git semantics"
  - id: IN-01
    severity: info
    disposition: open
    title: "Smoke test log mislabels a character count as a line count"
  - id: IN-02
    severity: info
    disposition: open
    title: "Probe re-states the gate's duplicate rule instead of extracting it"
  - id: IN-03
    severity: info
    disposition: open
    title: "`random`/`srandom` `-D` remap is redundant with htslib's own `hts_os.h` remap (benign today)"
open: 7
total: 8
recorded: 2026-09-30T02:49:52.784Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | deferred | triaged 2026-09-30 during UAT (user-delegated): verified first-hand — implib emitted cwd-relative to source-tree pysam/ (setup.py:546-554) while gate reads beside get_ext_fullpath (setup.py:405-410); paths agree on inplace (Phase 1-2 dev flow), diverge on non-inplace (pip install ., setup.py build, bdist_wheel → CalledProcessError). Deferred to Phase 3 entry (BUILD-02): first out-of-tree build phase; fix = derive implib path from os.path.dirname(get_ext_fullpath) |
| CR-02 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
