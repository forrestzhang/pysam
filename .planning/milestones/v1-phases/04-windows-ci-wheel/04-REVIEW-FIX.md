---
phase: 04-windows-ci-wheel
fixed_at: 2026-10-13T04:36:15Z
review_path: .planning/phases/04-windows-ci-wheel/04-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 1
skipped: 1
status: partial
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-10-13T04:36:15Z
**Source review:** .planning/phases/04-windows-ci-wheel/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 2 (WR-01, WR-02 — Critical/Warning tier per fix_scope; Info findings IN-01..IN-03 out of scope)
- Fixed: 1
- Skipped: 1

## Fixed Issues

### WR-02: Release step is not idempotent on workflow re-run

**Files modified:** `.github/workflows/win-wheels.yaml`
**Commit:** 0cdffee9 (`fix(04): make gh release create idempotent on re-run`, pushed to `origin/win` as `1053e95f..0cdffee9`)
**Applied fix:** The `Publish` step's `run:` was converted to a multi-line script: `gh release create "$TAG" dist/*.whl --generate-notes --target "$GITHUB_SHA" || gh release upload "$TAG" dist/*.whl --clobber`. If the release already exists (transient failure after creation), the re-run clobbers the release assets with the same-run downloaded wheels instead of failing hard. Provenance chain preserved: the fallback still consumes only same-run artifacts (`actions/download-artifact@v8`, no `run-id`/URL), so T-04-06 still holds. The existing T-04-05 comment (env indirection for `TAG`) and the `GH_REPO` comment were kept — the tag still never appears inline in the run script; a note documenting the re-run-safe fallback (WR-02) was added to the comment. `env:` block unchanged (`GH_TOKEN`, `TAG`, `GH_REPO`).

## Skipped Issues

### WR-01: Windows release tags collaterally fire the pre-existing PyPI workflow, which always fails on the fork

**File:** `.github/workflows/win-wheels.yaml:6-9`
**Reason:** not fixed in this pass — escalated to user decision by orchestrator. Repo-wide workflow disable on a pre-existing workflow requires explicit owner decision — orchestrator surfaced to user. (No workflow was disabled and no code was changed for this finding in this pass; the review's own note that editing `release.yaml` would violate the phase scope-audit gate T-04-10 also stands.)
**Original issue:** The publish-tag pattern `v[0-9]+.*` is identical to the pre-existing `release.yaml` ("Publish wheels") tag trigger, so every Windows release tag also starts the 18-cell upstream POSIX wheel matrix plus a doomed PyPI publish attempt on the fork (observed `failure` on `v0.24.1-win.1` and `v0.24.1-win.2`).

## Verification

- **YAML parse gate:** `python -c "import yaml; yaml.safe_load(open('.github/workflows/win-wheels.yaml', encoding='utf-8'))"` — PASS. Ran in the **main checkout** (`workflow.use_worktrees=false`, so this fixer edited/committed directly in the main checkout; no isolated worktree was created).
- **Commit hygiene:** single-line pure message, no Co-Authored-By trailer (per project rule).
- **Standing CI verdict (SHA-pinned):** pushed `0cdffee9242e0c75050961f1100b28264385da24` to `origin/win`; the standing `CI` workflow (ci.yaml) run `38346109919` for exactly that SHA concluded **success**. Only the CI workflow fired for this SHA, as expected — `win-wheels` triggers on tag pushes/manual dispatch only, so a branch push cannot fire the publish path (T-04-07 intact).
- Tier-1 re-read of the modified step confirmed the fix text is present and surrounding steps/env are intact; diff was scoped to the `Publish` step only (4 lines -> 8 lines, comments included).

---

_Fixed: 2026-10-13T04:36:15Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
