# Phase 01 Plan 03: User Setup — MSYS2 UCRT64

**Status: SATISFIED (verified 2026-09-18, re-verified 2026-09-30) — no action required.**

## Requirement (from PLAN frontmatter `user_setup`)

- **Service:** MSYS2 UCRT64 — build host for the Phase 1 dev build (D-15 split: MSYS2 itself is
  installed manually once; the committed `devtools/msys2-bootstrap.sh` owns everything after).
- **Manual step:** Install MSYS2 from https://www.msys2.org/ (default root `C:\msys64`) and
  complete the first-update flow in the UCRT64 shell before executing this plan.

## Evidence it is satisfied

- MSYS2 installed at the default root **C:\msys64** (user authorized automated install at the
  Task 1 blocking-human precondition checkpoint; official installer, `--noconfirm` first update).
- `msys2-runtime 3.6.10-4`; 9 UCRT64 packages provisioned through the TUNA mirror; UCRT64 venv
  (`_venv`) running CPython 3.14.7.
- First-update flow completed: the clean-state acceptance run of
  `sh devtools/msys2-bootstrap.sh` executed end-to-end on 2026-09-18 (pacman idempotent →
  venv → `pip install -e . --no-build-isolation` full build → smoke gate), ending with
  `smoke OK` in the captured log (`C:\msys64\tmp\pysam-bootstrap-run.log`).
- Re-verified 2026-09-30 (plan close-out): 13 `pysam/*.pyd` + 13 `pysam/*.dll.a` on disk;
  `import pysam` in the UCRT64 venv prints `0.24.1 builtin`.

## Notes for future plans

- A second MSYS2 install is NOT needed for Phase 02+ — the environment persists at `C:\msys64`;
  re-running `sh devtools/msys2-bootstrap.sh` is idempotent if packages drift.
- `gh auth login` (GitHub CLI) remains unauthenticated on this machine; CI verification uses the
  public REST API channel (same endpoint `gh run view` reads) — authorized standing substitute.
