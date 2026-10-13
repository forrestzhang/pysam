---
phase: 04-windows-ci-wheel
reviewed: 2026-10-13T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - .github/workflows/ci.yaml
  - .github/workflows/win-wheels.yaml
  - INSTALL
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-13
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed the three changed files (`git diff 2ea68a19..HEAD` scope-audited to exactly these three). Cross-referenced `pyproject.toml`'s `[tool.cibuildwheel]` section, `devtools/artifactname.py`, `devtools/smoke_test.py`, `setup.py`'s llvm-nm symbol gate, the pre-existing `release.yaml`, and the pinned `cibuildwheel==4.3.1` source. Verified factual claims against the live GitHub Release (`gh release view v0.24.1-win.2` on `forrestzhang/pysam`) and live workflow runs (`gh run list`).

**Scope integrity confirmed:** ci.yaml is purely additive — 49 insertions, 0 deletions vs `2ea68a19`; all four pre-existing jobs byte-identical. `release.yaml`, `devtools/`, and `pyproject.toml` unchanged since base.

**Security posture of win-wheels.yaml verified sound against the threat register (all checkable from the YAML and live runs):**

- T-04-04 PASS: workflow-level `permissions: {}` (line 12); `contents: write` appears only on the release job (lines 125-126) — the sole elevation in the file. Upload/download-artifact work under this scheme (proven by the pre-existing ci.yaml jobs and the recorded green runs).
- T-04-07 PASS: triggers are tag pushes (`v[0-9]+.*`, `win-test*`) + `workflow_dispatch` only (lines 5-10); no `pull_request`/branch-push entry point. Both tag patterns empirically fire (runs on `win-test.1`, `win-test.2`, `v0.24.1-win.2` all present). `workflow_dispatch` requires collaborator write access; even a dispatch on a branch ref cannot publish because of the release `if`-guard.
- T-04-05 PASS (core claim): the tag reaches the release script exclusively via `env: TAG: ${{ github.ref_name }}` and is referenced as `"$TAG"` inside double quotes (lines 140-143) — no re-evaluation of variable contents, no inline `github.ref_name` in any run script.
- T-04-06 PASS: release consumes only same-run artifacts (`actions/download-artifact@v8` with no `name`, no `run-id`, no URL), chained `needs: clean_smoke`; the run's single artifact (`wheels-win-amd64-310-311-312-313-314-315`, produced by `devtools/artifactname.py`) makes the nameless merge-download claim in the comments true. Six wheels published to the live Release match the CIBW_BUILD face exactly.
- Secrets: `GITHUB_TOKEN` (`github.token`) only; no other secrets referenced; `persist-credentials: false` on all three checkouts. Action set stays within the approved family (checkout@v7, setup-python@v7, setup-msys2@v2, cibuildwheel@v4.3.1, upload-artifact@v7, download-artifact@v8).
- ci.yaml windows job: llvm-nm PATH provisioning matches how `setup.py:_nm_command()` invokes `["llvm-nm", "-g", "-P"]` on win32 during `python setup.py build` (subprocess inherits runner PATH via GITHUB_PATH append); cygpath glob handling is correct Git Bash practice; matrix `3.10`–`3.15` proven green (run 38296297134, 25/25 jobs).
- cibuildwheel override mechanics verified from the pinned 4.3.1 source: platform-suffixed env vars (`CIBW_BEFORE_ALL_WINDOWS` etc.) take precedence over pyproject's generic POSIX `before-all`/`before-build` in the OptionsReader cascade, so the neutralizing `echo` overrides are effective; `CIBW_ENVIRONMENT: ""` cannot strip PATH (that option only adds vars).
- INSTALL factual accuracy verified live: the Release URL form, the example URL for cp313, and the "3.10--3.15" version claim all match the live Release assets on `forrestzhang/pysam` (confirmed via `gh release view`); `git remote` confirms the fork URL.

No BLOCKER/Critical findings. Two operational robustness warnings (one empirically observed on live runs) and three informational accuracy items.

## Critical Issues

None.

## Warnings

### WR-01: Windows release tags collaterally fire the pre-existing PyPI workflow, which always fails on the fork

**File:** `.github/workflows/win-wheels.yaml:6-9`
**Issue:** The publish-tag pattern `v[0-9]+.*` is identical to the pre-existing `release.yaml` ("Publish wheels") tag trigger. Every Windows release tag therefore also starts the full upstream POSIX wheel matrix (macos/many/musl, 18 build cells) followed by a PyPI publish attempt that cannot succeed on this fork. Verified on live runs: "Publish wheels" completed `failure` on both `v0.24.1-win.1` and `v0.24.1-win.2` (fired 2026-10-13T01:12Z and 01:35Z alongside the successful "Windows wheels" runs). Cost: hours of wasted runner compute per release tag plus a red-X run attached to every release — degrades robustness and muddies the provenance signal the phase is trying to establish.
**Fix:** Cheapest in-scope mitigation: disable the "Publish wheels" workflow on the fork via the Actions UI (Settings → Actions → disable `release.yaml`), so no code change and the "release.yaml untouched" scope claim holds. Alternative: adopt a non-colliding Windows tag convention (e.g. `win-v…`) and update the trigger pattern, the `if: startsWith(github.ref, 'refs/tags/v')` guard, and INSTALL together — a breaking change against the already-published `v0.24.1-win.2` naming. Do NOT "fix" by editing release.yaml here: that violates the phase's own scope-audit gate (04-03 T-04-10).

### WR-02: Release step is not idempotent on workflow re-run

**File:** `.github/workflows/win-wheels.yaml:137-146`
**Issue:** `gh release create "$TAG" …` fails hard once the release already exists. If a run fails transiently after release creation (e.g., partial asset upload), re-running the workflow — the standard recovery gesture — can never succeed until someone manually deletes the release. Provenance stays correct either way (assets are always same-run), this is purely a recovery-path robustness gap on the publish step.
**Fix:**
```yaml
      - name: Publish
        run: |
          gh release create "$TAG" dist/*.whl --generate-notes --target "$GITHUB_SHA" \
            || gh release upload "$TAG" dist/*.whl --clobber
        env:
          GH_TOKEN: ${{ github.token }}
          TAG: ${{ github.ref_name }}
          GH_REPO: ${{ github.repository }}
```
The `upload --clobber` fallback still consumes only same-run artifacts, preserving the T-04-06 provenance chain.

## Info

### IN-01: Comment claims test-command has no platform-suffix variant — cibuildwheel 4.3.1 has one

**File:** `.github/workflows/win-wheels.yaml:56-58`
**Issue:** The comment "test-command has NO platform-suffix variant, so the override is whole-order in this Windows-only workflow" is mechanically wrong: `cibuildwheel/options.py` in 4.3.1 builds `CIBW_TEST_COMMAND_WINDOWS` for every option unless explicitly disabled, so a platform-suffixed override does exist. The chosen generic `CIBW_TEST_COMMAND` env var still wins over pyproject's generic `test-command` in the resolution cascade (verified from the pinned version's `OptionsReader.get`), so behavior is correct — this is comment accuracy only, but the comment is the documented justification for the override strategy and would mislead a future maintainer.
**Fix:** Reword to: "pyproject's test-command is generic (no [tool.cibuildwheel.windows] section), so a generic CIBW_TEST_COMMAND env override fully replaces it; a suffixed variant (CIBW_TEST_COMMAND_WINDOWS) also exists."

### IN-02: Threat-register claim "no ${{ }} interpolation inside any run: block" does not hold file-wide

**File:** `.github/workflows/win-wheels.yaml:41` (also `.github/workflows/ci.yaml:251`)
**Issue:** T-04-05's mitigation as recorded in 04-02-PLAN.md states "no ${{ }} interpolation inside any run: block". Line 41 interpolates `${{ steps.msys2.outputs.msys2-location }}` directly into a run script (as does ci.yaml's twin step). The value is a runner filesystem path emitted by the official setup-msys2 action — not attacker-controlled, and a compromised action could execute arbitrary code in-job regardless — so there is no exploitable injection here. But the documented security property is overstated; the release-run-block claim specifically is true. For uniformity with the TAG pattern, the step could also use env indirection.
**Fix:** Either amend the plan text to scope the claim to the release job's run block, or convert the step: add `env: MSYS2_LOC: ${{ steps.msys2.outputs.msys2-location }}` and use `run: echo "$MSYS2_LOC\\ucrt64\\bin" >> "$GITHUB_PATH"`.

### IN-03: clean_smoke hardcodes the 3.13/cp313 pairing in three places that must stay in sync

**File:** `.github/workflows/win-wheels.yaml:88-91, 109`
**Issue:** The clean-room gate pins `python-version: '3.13'` and the wheel glob `dist/*-cp313-cp313-win_amd64.whl` independently. The single-version clean-room design is fine (per-wheel smoke already runs inside cibuildwheel via `CIBW_TEST_COMMAND`, so every built version is smoke-tested; the consumer gate samples one), and desynchronization fails loudly (glob no-match → pip error), but a future matrix edit that drops 3.13 breaks the gate for a non-obvious reason.
**Fix:** Derive one from the other, e.g. define `env: GATE_PY: '3.13'` at job level and use `python-version: ${{ env.GATE_PY }}` with `dist/*-cp${GATE_PY/./}-cp${GATE_PY/./}-win_amd64.whl` (or simply a comment stating the three lines are one unit).

---

_Reviewed: 2026-10-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
