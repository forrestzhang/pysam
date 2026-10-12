---
schema_version: 1
open_count: 4
waived_count: 0
fixed_count: 0
total_count: 4
last_updated: 2026-10-12T15:37:07.100Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 03 | deviation | samtools/coverage.c | 236 | VLA kept verbatim inside #else arm per zero-regression prohibition; plan grep==0 criterion conflicts with #else-verbatim action text (heap form + free under _MSC_VER guard present) | open |  | 2026-10-12T12:24:23.035Z |  |
| 2 | 03 | deviation | pysam/libcutils.c |  | Regenerated libcutils.c is untracked by repo policy (.gitignore pysam/libc*.c); plan asked to commit it - fix is carried by tracked pysam/libcutils.pyx | open |  | 2026-10-12T12:24:23.503Z |  |
| 3 | 03 | deviation | .planning/phases/03-msvc/03-04-SUMMARY.md |  | Task 3 audit grep=1 textual hit is 03-03's moved run_make_print_config wrapper line; semantic audit shows zero new process-spawning calls; documented in 03-04-SUMMARY deviation #12 | open |  | 2026-10-12T15:36:59.225Z |  |
| 4 | 03 | deviation | .planning/phases/03-msvc/03-04-SUMMARY.md |  | 03-04 commits also touched hts_defs.h htslib_util.h and bcftools sources beyond the plan-enumerated confinement (dllimport header-sites and MSVC-rejected constructs; no macro-layer fix exists); POSIX arms verbatim; documented in 03-04-SUMMARY deviation #13 | open |  | 2026-10-12T15:37:07.100Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "03",
    "file": "samtools/coverage.c",
    "line": 236,
    "description": "VLA kept verbatim inside #else arm per zero-regression prohibition; plan grep==0 criterion conflicts with #else-verbatim action text (heap form + free under _MSC_VER guard present)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-12T12:24:23.035Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "03",
    "file": "pysam/libcutils.c",
    "line": null,
    "description": "Regenerated libcutils.c is untracked by repo policy (.gitignore pysam/libc*.c); plan asked to commit it - fix is carried by tracked pysam/libcutils.pyx",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-12T12:24:23.503Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 3,
    "kind": "deviation",
    "phase": "03",
    "file": ".planning/phases/03-msvc/03-04-SUMMARY.md",
    "line": null,
    "description": "Task 3 audit grep=1 textual hit is 03-03's moved run_make_print_config wrapper line; semantic audit shows zero new process-spawning calls; documented in 03-04-SUMMARY deviation #12",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-12T15:36:59.225Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 4,
    "kind": "deviation",
    "phase": "03",
    "file": ".planning/phases/03-msvc/03-04-SUMMARY.md",
    "line": null,
    "description": "03-04 commits also touched hts_defs.h htslib_util.h and bcftools sources beyond the plan-enumerated confinement (dllimport header-sites and MSVC-rejected constructs; no macro-layer fix exists); POSIX arms verbatim; documented in 03-04-SUMMARY deviation #13",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-12T15:37:07.100Z",
    "resolved_at": null,
    "milestone": null
  }
]
````
