---
phase: 04-windows-ci-wheel
plan: 02
subsystem: infra
tags: [cibuildwheel, delvewheel, github-actions, wheels, windows, gh-release]

requires:
  - phase: 04-01
    provides: Green additive windows CI job on every push (SC-1 ordering gate; its cygpath/setuptools fixes keep the branch green while this plan iterated)
provides:
  - win-wheels.yaml pipeline turning a tag push into six delvewheel-repaired self-contained win_amd64 wheels (build_wheels -> clean_smoke -> release)
  - Six published wheels at fork Release v0.24.1-win.2 (cp310-cp315, non-draft, verified asset list) - the pip-installable distribution channel
  - Dry-run evidence on win-test.1 / win-test.2 tags including release-suppression proof (the if-guard skipped on non-v tags)
affects: [04-03 (CI matrix validation record; consumer-path verification and sha256s run against Release v0.24.1-win.2)]

actuals:
  tokens: 1600
  tasks: 4
  commits: 3
  plan_head_before: 1a3bcf855f240e89230b203acd61c4baf2fd44ca
  plan_head_after: ddaa9b6871ece958463fc7f7eae538b5fccf0c08

tech-stack:
  added: [pypa/cibuildwheel@v4.3.1, delvewheel 1.13.x (constraints-installed), gh release create via preinstalled gh CLI]
  patterns:
    - "Windows cibuildwheel semantics live exclusively in workflow env (CIBW_*_WINDOWS overrides); pyproject.toml POSIX hooks stay byte-identical"
    - "delvewheel repair --ignore-existing is load-bearing for cross-module .pyd imports (default repair crashes FileNotFoundError)"
    - "Clean-machine gate = nameless same-run artifact download + fresh venv + interpreter-filtered wheel install + script-form smoke (never python -m)"
    - "Publish job needs repo context without a checkout: GH_REPO env (gh shells out to git otherwise)"

key-files:
  created: [.github/workflows/win-wheels.yaml]
  modified: []

key-decisions:
  - "Publish tag is v0.24.1-win.2 (not the planned v0.24.1-win.1): the first publish attempt failed at the release step (gh lacked repo context in the checkout-less job) and the plan's Task 4 contingency explicitly directs re-tagging rather than re-using a tag name whose run already failed"
  - "release job gets repository context via GH_REPO env instead of a checkout step - keeps the job artifact-only (provenance) and preserves env-indirection discipline"
  - "Check wheelhouse invokes python devtools/artifactname.py explicitly (release.yaml's bare script form relies on a python3 shebang resolution Git Bash cannot guarantee on windows-latest)"

patterns-established:
  - "Tag-gated publish pipeline: on.push.tags + workflow_dispatch only; the release job's if: startsWith(refs/tags/v) makes dry-run tags structurally unable to publish"
  - "Per-run provenance chain: clean_smoke and release consume only same-run artifacts via nameless merge-multiple download-artifact"

requirements-completed: [CI-02, CI-03]

coverage:
  - id: D1
    description: "win-wheels.yaml: build_wheels -> clean_smoke -> release chain, tag-push + dispatch triggers only, publish unreachable from PRs"
    requirement: CI-02
    verification:
      - kind: integration
        ref: "run 38328253612 (win-test.1): build_wheels success, clean_smoke success, release skipped; YAML parse gate yaml-ok"
        status: pass
    human_judgment: false
  - id: D2
    description: "Six delvewheel-repaired self-contained win_amd64 wheels (cp310-cp315) through cibuildwheel@v4.3.1 with the three CIBW_*_WINDOWS overrides"
    requirement: CI-03
    verification:
      - kind: integration
        ref: "run 38329297031 (win-test.2): artifact wheels-win-amd64-310-311-312-313-314-315 downloaded, 6/6 wheels, per-tag grep 1 each; delvewheel 'no external dependencies are needed' x6"
        status: pass
    human_judgment: false
  - id: D3
    description: "SC-3 clean-machine publish gate: separate consumer job (fresh venv, cp313-filtered wheel install, script-form smoke) that release strictly needs"
    requirement: CI-02
    verification:
      - kind: integration
        ref: "clean_smoke success on runs 38328253612, 38329297031, 38332836356; smoke log shows wheel-resolved import path (24 alignments, 44118 vcf lines)"
        status: pass
    human_judgment: false
  - id: D4
    description: "SC-4 fork Release with all six wheels published strictly after the clean-machine gate passed in the same run"
    requirement: CI-02
    verification:
      - kind: integration
        ref: "run 38332836356 (v0.24.1-win.2): all three jobs success; gh release view: isDraft=false, 6 assets, cp310-cp315 each present"
        status: pass
    human_judgment: false

duration: 88 min
completed: 2026-10-13
status: complete
---

# Phase 4 Plan 02: Windows wheel pipeline (CI-02 + CI-03 production) Summary

**win-wheels.yaml pipeline publishing six delvewheel-repaired self-contained win_amd64 wheels (cp310-cp315) to fork Release v0.24.1-win.2 through a clean-machine smoke gate**

## Performance

- **Duration:** 88 min
- **Started:** 2026-10-13T00:31:33Z
- **Completed:** 2026-10-13T02:00:30Z
- **Tasks:** 4
- **Files modified:** 1 (.github/workflows/win-wheels.yaml, +146/-0 new file)

## Checkpoint Resolution (Task 1)

Task 1 (`checkpoint:human-verify`, `gate="blocking-human"` — supply-chain approval for cibuildwheel@v4.3.1 + delvewheel activation and the fork release tag) was resolved before this executor run: the orchestrator surfaced the full checkpoint panel and the user approved on 2026-10-12 with 「批准，按计划」. Verdict recorded: **approved-as-planned** (cibuildwheel@v4.3.1 + delvewheel activation AND the fork tag including the eventual public Release). Tasks 2-4 executed exactly as written under that approval; no re-verification was performed by this executor.

## Accomplishments

- `.github/workflows/win-wheels.yaml` created: `build_wheels` (windows-latest, bash default, timeout 240, setup-msys2 llvm-nm provisioning for the BUILD-03 symbol gate, cibuildwheel@v4.3.1 with the probe-validated CIBW env) -> `clean_smoke` (SC-3 clean-room consumer gate) -> `release` (job-scoped `contents: write`, env-indirect TAG, v-tag if-guard)
- Tracer dry run green end-to-end on tag win-test.1: cp313 wheel built, delvewheel-repaired with the ignore-existing flag ("no external dependencies are needed"), per-wheel smoke inside cibuildwheel, then installed and smoke-verified in a clean-room venv — release correctly skipped
- Full CI-03 matrix green on win-test.2: six wheels (cp310-cp315) verified from the downloaded artifact contents, not the log; delvewheel self-containedness marker present for all six
- Published: fork Release [v0.24.1-win.2](https://github.com/forrestzhang/pysam/releases/tag/v0.24.1-win.2) — non-draft, exactly 6 assets, every CPython tag present, created strictly after the clean-machine gate passed in the same run
- Protected files byte-identical throughout: `git diff 2ea68a19..HEAD -- pyproject.toml devtools/smoke_test.py devtools/artifactname.py` is empty at every task SHA

## CI Evidence (SHA-pinned)

| Run | Tag / SHA | Verdict | Notes |
|-----|-----------|---------|-------|
| [38328253612](https://github.com/forrestzhang/pysam/actions/runs/38328253612) | win-test.1 @ 28de00a1 | build success, clean success, release **skipped** | Tracer dry run; cp313 wheel in 2m54s; delvewheel marker x1 |
| [38329297031](https://github.com/forrestzhang/pysam/actions/runs/38329297031) | win-test.2 @ 3b26df3b | build success, clean success, release **skipped** | Six-wheel matrix; artifact `wheels-win-amd64-310-311-312-313-314-315` (2.95 MB/cp313); delvewheel marker x6 |
| [38331012769](https://github.com/forrestzhang/pysam/actions/runs/38331012769) | v0.24.1-win.1 @ 3b26df3b | release **failure** | Build+clean green; `gh release create` died: "failed to run git: fatal: not a git repository" — no Release created (see Deviation 1) |
| [38332836356](https://github.com/forrestzhang/pysam/actions/runs/38332836356) | v0.24.1-win.2 @ ddaa9b68 | all three jobs **success** | Publish run after the GH_REPO fix; delvewheel marker x6; Release created with 6 assets |

Standing ci.yaml gate (every branch push of this plan): 38328248844, 38329287491, 38332831159 — each 25/25 jobs success.

## Published Release (SC-4)

**URL:** https://github.com/forrestzhang/pysam/releases/tag/v0.24.1-win.2 (isDraft=false, 6 assets)

```
pysam-0.24.1-cp310-cp310-win_amd64.whl
pysam-0.24.1-cp311-cp311-win_amd64.whl
pysam-0.24.1-cp312-cp312-win_amd64.whl
pysam-0.24.1-cp313-cp313-win_amd64.whl
pysam-0.24.1-cp314-cp314-win_amd64.whl
pysam-0.24.1-cp315-cp315-win_amd64.whl
```

Artifact name at win-test.2: `wheels-win-amd64-310-311-312-313-314-315`. sha256s and the consumer-path (pip install from the Release URL on a clean machine) are recorded by plan 04-03.

## Task Commits

1. **Task 2: win-wheels.yaml cp313 tracer dry run — pipeline proven, publish suppressed** - `28de00a1` (feat)
2. **Task 3: widen matrix to cp310-cp315 — six wheels through build + clean gate** - `3b26df3b` (feat)
3. **Task 4: publish — GH_REPO fix + tag v0.24.1-win.2, six assets verified** - `ddaa9b68` (fix)

**Plan metadata:** (recorded below)

## Files Created/Modified

- `.github/workflows/win-wheels.yaml` - NEW (143 lines + 3): the whole CI-02 pipeline. Trigger: `on.push.tags [v[0-9]+.*, win-test*]` + `workflow_dispatch` only. Jobs: `build_wheels` (cibuildwheel@v4.3.1, CIBW_BUILD "cp310-* cp311-* cp312-* cp313-* cp314-* cp315-*", CIBW_ARCHS AMD64, the three CIBW_*_WINDOWS overrides, CIBW_TEST_COMMAND smoke, CIBW_ENVIRONMENT ""), `clean_smoke` (nameless merge-multiple same-run download, fresh venv, `dist/*-cp313-cp313-win_amd64.whl` install, script-form smoke), `release` (if v-tag, job-scoped contents:write, `gh release create` with GH_TOKEN/TAG/GH_REPO env indirection)

## Decisions Made

- Publish tag moved v0.24.1-win.1 -> v0.24.1-win.2 after the failed first publish: the plan's Task 4 contingency pre-authorizes exactly this ("a failed run leaves no release; never re-push [the failed tag]") — the win.1 tag and its failed run remain on the fork as the audit trail
- `GH_REPO: ${{ github.repository }}` supplies gh's repo context in the checkout-less release job (gh shells out to git otherwise); env form chosen over a `--repo` flag to keep `run:` free of any interpolation beyond env references
- `Check wheelhouse` uses `python devtools/artifactname.py ...` (explicit interpreter) rather than release.yaml's bare `devtools/artifactname.py` — the shebang form needs `python3` resolution through Git Bash which windows-latest does not guarantee; explicit `python` is the same shape with a deterministic interpreter

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] gh release create failed without repository context in the checkout-less release job**
- **Found during:** Task 4 (publish run 38331012769, release job failure)
- **Issue:** The release job is artifact-only by design (like release.yaml's upload_pypi — no checkout). `gh release create` shells out to `git` to determine the repository when no repo context is set, and died with `failed to run git: fatal: not a git repository (or any of the parent directories): .git` before creating anything. The plan had anticipated a different failure mode (403 permissions); the job-scoped `contents: write` elevation worked as designed
- **Fix:** Added `GH_REPO: ${{ github.repository }}` to the publish step's env block — supplies repo context without adding a checkout step (preserves the artifact-only provenance shape) and without inline `${{ }}` in the run script
- **Files modified:** .github/workflows/win-wheels.yaml
- **Verification:** Re-tagged v0.24.1-win.2 per the plan's Task 4 contingency; run 38332836356 release job success; Release non-draft with 6 assets
- **Committed in:** ddaa9b68

---

**Total deviations:** 1 auto-fixed (1 x Rule 1 bug, in this plan's own new workflow)
**Impact on plan:** Required for SC-4 at all; no pre-existing file touched (pure addition + 3 lines inside the new file). Protected-file gate still passes.

## Issues Encountered

- Transient local network outage at session start (DNS/TLS to github.com failing, gh keyring auth error) — self-recovered within minutes before any operation depended on it; no impact on execution
- The publish run's six-wheel build took ~20 min (vs 40-90 min budgeted) — the current windows-latest generation builds each CPython version in ~2-3 min; timeout-minutes 240 retains headroom for image drift

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CI-02/CI-03 production complete; ROADMAP SC-2/SC-3/SC-4 live. 04-03 (CI matrix validation + 04-CI-VALIDATION.md) has: the published Release URL for consumer-path verification, per-run wheel evidence, and the CI-vs-local count delta from 04-01 to reconcile
- The v0.24.1-win.1 tag with its failed run stays on the fork as the audit trail (do not delete/re-push; win.2 is the published lineage)
- Future releases: push tag `v<version>-win.N`; the pipeline rebuilds, gates, and publishes autonomously

---
*Phase: 04-windows-ci-wheel*
*Completed: 2026-10-13*

## Self-Check: PASSED

- 04-02-SUMMARY.md and .github/workflows/win-wheels.yaml exist on disk
- All 3 task commits (28de00a1, 3b26df3b, ddaa9b68) are ancestors of HEAD
- evaluation-scope (commits-only, this branch): resolves with commits on this branch
- All plan-level verification re-run and green: YAML parse gate; win-test.1 jobs table (build success / clean success / release skipped); win-test.2 artifact contents (6 wheels, cp310-cp315 each 1); v0.24.1-win.2 all-jobs-success + Release non-draft 6 assets; protected-file diff empty at final SHA; ci.yaml standing gate 25/25 on every push
