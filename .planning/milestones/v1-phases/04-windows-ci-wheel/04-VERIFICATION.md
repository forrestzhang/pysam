---
phase: 04-windows-ci-wheel
verified: 2026-10-13T11:06:04Z
status: passed
score: 12/12 must-haves verified
covered_files:
  - .github/workflows/ci.yaml
  - .github/workflows/win-wheels.yaml
  - .planning/phases/04-windows-ci-wheel/04-01-PLAN.md
  - .planning/phases/04-windows-ci-wheel/04-01-SUMMARY.md
  - .planning/phases/04-windows-ci-wheel/04-02-PLAN.md
  - .planning/phases/04-windows-ci-wheel/04-02-SUMMARY.md
  - .planning/phases/04-windows-ci-wheel/04-03-PLAN.md
  - .planning/phases/04-windows-ci-wheel/04-03-SUMMARY.md
  - INSTALL
covered_digest: "v3:sha256:e7a89b6809e2035846fbad74e4845b9397c3bfab655d3984acc517bb160e44a0"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 12/12
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 4: Windows CI 与 wheel 分发 Verification Report

**Phase Goal:** CI 持续产出经清洁机冒烟测试把关的自包含 `win_amd64` wheel，经 fork 渠道发布 — Windows 用户 `pip install` 即可用。
**Verified:** 2026-10-13T11:06:04Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH (#4682) for milestone closeout. Prior pass 12/12 at 2026-10-13T06:48:31Z; afterwards Phase-5 commit `e960aba8` (fix(05-01): parameterize clean_smoke Python + win-wheels comment/env hygiene) touched a covered source (`win-wheels.yaml`). This pass re-verifies every truth against the CURRENT tree (HEAD `6adf94e2`) with fresh live evidence and a fresh fingerprint.

**Verification method note:** deliverables are CI pipelines plus a published distribution channel, so the decisive evidence is LIVE external state (GitHub Actions runs, the fork Release, the distribution URL), not file presence. Every check below was re-executed against the current tree and live GitHub state on this pass, including full re-execution of the consumer path (fresh venv → live Release URL install → script-form smoke → shadowing assert).

## Stale-Refresh Scope (what changed since the prior pass)

`git log --since=2026-10-13T06:48:31Z` over covered files shows exactly one commit: `e960aba8`, all changes inside `.github/workflows/win-wheels.yaml` (Phase-5 debt item: clean_smoke Python de-hardcoding). `ci.yaml` and `INSTALL` are untouched since the prior pass. Phase-5 commits `2d23a69b`/`13f50b6b`/`efe5a2b0` additionally touched `setup.py`, `devtools/`, `win32/`, `tests/` — outside phase-4's covered set except where noted under truths 5/8/12 below (each reconciled against Phase-5's declared ROADMAP scope, the same reconciliation pattern as the phase-2 refresh).

## Goal Achievement

### Observable Truths

Merged from ROADMAP SC-1..SC-4 (the contract) plus PLAN frontmatter truths, deduplicated (roadmap wording kept where plans restate an SC). Identical truth set to the prior pass.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC-1: `windows-latest` 手工 build+pytest job 全绿（3.10–3.15） | ✓ VERIFIED | ci.yaml windows job (lines 221-267) unchanged since phase-4: windows-latest, shell bash, matrix 3.10-3.15, MSVC build + PYTHONPATH(cygpath) pytest. LIVE refresh: fork CI run 38380672667 @ 965760f1 = conclusion success, 25/25 jobs, 0 non-success (verifier re-pulled full jobs table: 6 windows cells + 19 pre-existing all success) |
| 2 | SC-2: cibuildwheel + delvewheel 自包含 win_amd64 wheel，3.10–3.15 全矩阵 | ✓ VERIFIED | win-wheels.yaml at HEAD: cibuildwheel@v4.3.1, CIBW_BUILD "cp310-* … cp315-*", delvewheel repair --ignore-existing. LIVE: Release v0.24.1-win.2 holds exactly 6 assets cp310-cp315, all win_amd64, isDraft=false (re-checked this pass); verifier re-downloaded the cp313 asset — sha256 `5fe4cbe2…a1e84d` byte-identical to 04-CI-VALIDATION.md §3; delvewheel "no external dependencies are needed" x6 in current-SHA build log (run 38369651968, verifier-grep). msvcrt/no-vendor-DLL import-table audit carries via byte-identity of the unchanged asset |
| 3 | SC-3: 清洁机冒烟测试作为发布门槛（gate pass 才允许发布） | ✓ VERIFIED | win-wheels.yaml at HEAD: `clean_smoke` job — fresh venv, interpreter-filtered install now Phase-5-parameterized (choice-bounded SMOKE_PY input → derived SMOKE_CP glob; zero hardcoded cp-tag in the job), script-form smoke; `release` has `needs: clean_smoke`. LIVE at current SHA e960aba8: win-test.3 run 38369651968 = build_wheels success, clean_smoke success (installed cp313 wheel, log line verbatim), release skipped; dispatch run 38369877795 (smoke_python=3.12) = clean_smoke success installing `dist/pysam-0.24.1-cp312-cp312-win_amd64.whl` (log line verbatim) — both parameterization paths proven green |
| 4 | SC-4: fork Releases 发布，pip 安装后 htslib API 绑定与 samtools/bcftools 命令分派全部可用 | ✓ VERIFIED | LIVE Release v0.24.1-win.2: non-draft, 6 assets (re-checked). Verifier re-executed the consumer path THIS pass: fresh venv (D:/miniconda3 CPython 3.13) → `pip install <live Release URL cp313 wheel>` → INSTALL-OK → devtools/smoke_test.py script-form → "24 alignments read / 44118 vcf lines / smoke OK" (AlignmentFile fetch = htslib API; samtools view -b + bcftools view -H = command dispatch) → shadowing assert as a TEMP script file: `pysam.__file__` inside the venv's site-packages, SHADOW-ASSERT-OK. Full-suite functional parity carried by the 6 green direct-job cells (truth 1) |
| 5 | BUILD-03 符号门在 runner 上真实执行 — llvm-nm 经 msys2/setup-msys2 供给，缺失即硬失败，从未被 patch 跳过 (04-01) | ✓ VERIFIED | Both workflows at HEAD provision `mingw-w64-ucrt-x86_64-llvm-tools` (release:false) + GITHUB_PATH append (win-wheels now env-indirect via MSYS2_LOCATION — zero ${{ }} in run:). setup.py at HEAD (post-Phase-5 edits): win32 branch calls `check_ext_symbol_conflicts()` bare (line 561) — the try/except OSError/CalledProcessError swallow exists only on the POSIX else-branch; a missing/failing llvm-nm aborts the Windows build. Empirical: current-SHA run 38369651968's six builds all passed through the gate. Fail-open scan: 0 `continue-on-error` in either workflow |
| 6 | 零回归：所有 pre-existing ci.yaml job 字节不变（纯加法） | ✓ VERIFIED | `git diff 2ea68a19..HEAD -- ci.yaml` deleted lines = 0 (still pure addition at CURRENT HEAD — Phase 5 did not touch ci.yaml); LIVE run 38380672667: 19 pre-existing jobs success (25/25 = 6 windows + 19 pre-existing, 0 non-success) |
| 7 | 六个 per-cell pytest 计数来自真实 run log（非编造） | ✓ VERIFIED | 04-01-SUMMARY table keyed to immutable run 38296297134 @ 207b6901 (windows 3.13 cell verbatim-matched "1032 passed, 16 skipped in 18.87s" at phase-4 verification; the run log is frozen history). Refresh drift check: windows (3.13) at 965760f1 now reads "1038 passed, 16 skipped in 26.98s" (verifier-grepped run 38380672667) = 1032 + 6, fully attributed to Phase-5's lockstep teeth tests (tests/PortabilityRegression_test.py, commit 2d23a69b) — named later-phase additions, same reconciliation as the phase-2 refresh; zero unexplained delta |
| 8 | pyproject.toml POSIX cibuildwheel hooks 字节不变 | ✓ VERIFIED | Phase-4 boundary: `git diff 2ea68a19..0cdffee9 -- pyproject.toml setup.py devtools/ vendor/ win32/ .github/workflows/release.yaml` = 0 lines. At CURRENT HEAD, pyproject.toml itself remains byte-identical (absent from the 2ea68a19..HEAD diff); the other protected paths changed only via Phase-5 commits 2d23a69b/13f50b6b/efe5a2b0 (lockstep/shim-sentinel work — Phase-5 ROADMAP scope), never phase-4 commits |
| 9 | Dry-run tag 绝不发布；publish 路径从 PR 不可达 (04-02) | ✓ VERIFIED | win-wheels.yaml triggers at HEAD: `push.tags [v[0-9]+.*, win-test*]` + `workflow_dispatch` only — no branch/pull_request triggers; release job `if: startsWith(github.ref, 'refs/tags/v')` excludes win-test* and dispatch refs. LIVE at current SHA: win-test.3 run 38369651968 release = skipped; dispatch run 38369877795 release = skipped — both with build+clean green |
| 10 | 04-CI-VALIDATION.md 存在且证据 SHA-pinned、与真实世界一致 | ✓ VERIFIED | File re-checked: 6 sections, 8 sha256 rows, CI-03 alignment section, Q1-Q5 register; every verdict cites run ID/SHA/tag. World-match re-derived this pass: cp313 sha256 from a fresh `gh release download` identical to the record; delvewheel markers re-derived at the current SHA (truth 2); run-log count line re-derived (truth 7) |
| 11 | INSTALL 记录 Windows 预编译 wheel 安装路径 | ✓ VERIFIED | INSTALL unchanged since phase-4: "Windows (prebuilt wheel)" section at line 91 — fork Releases URL, full-URL pip install command (cp313 worked example), python.org CPython 3.10–3.15 requirement, self-containedness note (relurl=1, v315=2 grep gates green). The documented URL is the one the verifier installed from successfully THIS pass |
| 12 | 阶段源码范围 = 恰好 3 个文件 + final-SHA CI 双面全绿 (04-03) | ✓ VERIFIED | Phase-scoped audit: `git diff --name-only 2ea68a19..0cdffee9` (phase-4 source end) minus .planning/ = exactly {.github/workflows/ci.yaml, .github/workflows/win-wheels.yaml, INSTALL} — build code untouched by phase-4. Final phase-4 CI runs 38343462764 @ 1053e95f and 38346109919 @ 0cdffee9 both 25/25 (verified at phase time). At CURRENT HEAD the same diff additionally lists 8 files — every one from Phase-5 commits (2d23a69b/13f50b6b/efe5a2b0/e960aba8: setup.py, devtools/check_libhts_objs_lockstep.py, devtools/probe_symbol_check.py, win32/msvc/{dirent.h,pthread.h,shim_selftest.c}, tests/{PortabilityRegression_test.py,TestUtils.py,samtools_test.py}) matching Phase-5's ROADMAP goal verbatim — documented later-phase work, not a phase-4 scope breach; current-tree CI green at 965760f1 (truth 1) |

**Score:** 12/12 truths verified (0 present, behavior-unverified)

No deferred items — Phase 4 truths are all met (phase-scoped where later phases legitimately appended work); Phase 5 is complete in the same milestone, nothing outstanding.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.github/workflows/ci.yaml` | Additive `windows` job, 6-version matrix, symbol gate live | ✓ VERIFIED | Unchanged since phase-4 (deleted_lines=0 vs 2ea68a19 at HEAD); live 25/25 green run 38380672667 |
| `.github/workflows/win-wheels.yaml` | build_wheels → clean_smoke → release chain | ✓ VERIFIED | Present at HEAD with Phase-5 parameterization (SMOKE_PY/SMOKE_CP) + WR-02 idempotent publish fallback; substantive; wired — live runs 38369651968 (tag) and 38369877795 (dispatch) both build+clean green, release correctly suppressed |
| `INSTALL` | Windows prebuilt-wheel consumer section | ✓ VERIFIED | Unchanged since phase-4; grep gates green; documented URL re-proven live by verifier install this pass |
| `.planning/.../04-CI-VALIDATION.md` | SHA-keyed evidence record | ✓ VERIFIED | 6 sections, 8 sha256 rows; cp313 digest re-derived live = identical |
| Six wheels at Release v0.24.1-win.2 | cp310-cp315 win_amd64, non-draft | ✓ VERIFIED | LIVE re-check: 6 assets, isDraft=false, all six CPython tags present; cp313 asset byte-identical to record |
| 04-01/02/03-SUMMARY.md | Run URLs, counts, commits | ✓ VERIFIED | Present; recorded run IDs re-checked live where re-pulled this pass (38369651968, 38369877795, 38380672667 — every checked claim matched) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| tag push | win-wheels.yaml | `on.push.tags` + dispatch only | ✓ WIRED | No branch/PR trigger exists at HEAD; empirically re-proven: win-test.3 tag fired the pipeline, dispatch fired it, branch pushes fire only CI |
| build_wheels | clean_smoke | `needs:` + same-run download-artifact (nameless, merge-multiple) | ✓ WIRED | Provenance rule holds at HEAD: no run-id/URL inputs anywhere in the release/clean jobs |
| clean_smoke | release | `needs: clean_smoke` + `if: refs/tags/v` | ✓ WIRED | Live at current SHA: release skipped on win-test.3 and dispatch while build+clean green; publish run 38332836356 (historical) 3/3 success in dependency order |
| windows-latest runner | llvm-nm → MSVC build → pytest | setup-msys2 → GITHUB_PATH append → `python setup.py build` → PYTHONPATH(cygpath) pytest | ✓ WIRED | Full chain intact in ci.yaml at HEAD; green across all checked runs incl. 38380672667 |
| Release URL | fresh venv install → script-form smoke → site-packages | pip by full URL; `devtools/smoke_test.py`; script-file assert | ✓ WIRED | Verifier re-executed the whole link live THIS pass: INSTALL-OK → smoke OK → SHADOW-ASSERT-OK |

### Data-Flow Trace (Level 4)

Workflow artifacts; the flowing "data" is the wheels themselves.

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| win-wheels.yaml | `wheelhouse/*.whl` → artifact → `dist/*.whl` → Release assets | cibuildwheel build | Yes — released cp313 asset's sha256 (verifier-computed from fresh download this pass) matches the record keyed to the publish run; delvewheel marker x6 re-derived at current SHA | ✓ FLOWING |
| ci.yaml windows job | `build/lib.win-amd64-cpython-*` via PYTHONPATH | real `python setup.py build` output | Yes — pytest per cell green at 965760f1 with count line verbatim in the run log | ✓ FLOWING |
| clean_smoke gate | SMOKE_PY input → SMOKE_CP → `dist/*-${SMOKE_CP}-…whl` install | Phase-5 parameterization | Yes — both paths log the exact expected wheel file being installed (cp312 on dispatch, cp313 on tag default) | ✓ FLOWING |
| 04-CI-VALIDATION.md | counts / sha256s / verdicts | live run logs + `gh release download` | Yes — cp313 digest re-derived identical this pass; count-line and delvewheel markers re-derived | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Consumer: URL install + script smoke + shadowing assert (SC-4) | fresh venv → pip install live Release URL → smoke_test.py → TEMP assert-script | INSTALL-OK; 24 alignments / 44118 vcf lines / smoke OK; pysam.\_\_file\_\_ inside venv site-packages | ✓ PASS |
| Release live state | `gh release view v0.24.1-win.2` | non-draft, 6 assets cp310-cp315 | ✓ PASS |
| Wheel integrity vs record (cp313) | `gh release download --pattern *cp313*` + sha256sum | `5fe4cbe2…a1e84d` identical to 04-CI-VALIDATION.md §3 | ✓ PASS |
| Current-SHA pipeline (dry run) | `gh run view 38369651968` (win-test.3 @ e960aba8) | build_wheels success, clean_smoke success (cp313 install line verbatim), release skipped | ✓ PASS |
| Parameterized gate (dispatch 3.12) | `gh run view 38369877795` log grep | clean_smoke installed `dist/pysam-0.24.1-cp312-cp312-win_amd64.whl`, gate green | ✓ PASS |
| Self-containedness at current SHA | grep "no external dependencies are needed" in run 38369651968 build log | marker present x6 (one per wheel) | ✓ PASS |
| CI verdicts (current) | `gh run view 38380672667` @ 965760f1 | success, 25 jobs, 0 non-success | ✓ PASS |
| Evidence authenticity (count drift) | grep windows (3.13) summary in 38380672667 | "1038 passed, 16 skipped" = phase-time 1032 + 6 Phase-5 teeth tests (named commits) | ✓ PASS |
| YAML validity | miniconda yaml.safe_load both workflows | both-yaml-ok | ✓ PASS |
| WR-01 state | `gh api .../actions/workflows` | "Publish wheels" (release.yaml) = disabled_manually; CI + Windows wheels active | ✓ PASS |
| Injection-surface discipline | inspect run: blocks in win-wheels.yaml at HEAD | zero ${{ }} inside run: lines (MSYS2_LOCATION/SMOKE_* env-indirect; TAG/GITHUB_SHA/GH_REPO env) | ✓ PASS |
| Zero-regression gates | git diff vs 2ea68a19 (boundary + HEAD); grep continue-on-error | phase-4 scope exactly 3 files; ci.yaml 0 deleted lines at HEAD; pyproject.toml byte-identical at HEAD; 0 fail-open constructs | ✓ PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` declared by the plans; this phase's probes were the live CI runs and Release checks above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CI-01 | 04-01 | windows-latest runner（先手工 build+pytest job，验证后接入 cibuildwheel） | ✓ SATISFIED | Truths 1, 5, 6 re-verified against current tree + live run 38380672667 |
| CI-02 | 04-02, 04-03 | MSVC 自包含 win_amd64 wheel + delvewheel 修复 + 清洁机冒烟发布门槛 + fork Releases 分发 | ✓ SATISFIED | Truths 2, 3, 4 — live Release unchanged (byte-identical digest re-proven); gate wired and empirically gating at the current workflow SHA; consumer path re-executed live this pass |
| CI-03 | 04-02, 04-03 | wheel 覆盖 3.10–3.15（以 python_requires 为准） | ✓ SATISFIED | Truth 2 + 04-CI-VALIDATION §5: 6 wheels cp310-cp315 on the live Release; requires-python >=3.9 untouched (pyproject.toml byte-identical at HEAD) |

Orphaned requirements: none — REQUIREMENTS.md maps exactly CI-01/CI-02/CI-03 to Phase 4; all three are claimed by plans and re-verified. (All 13 v1 requirements complete per REQUIREMENTS.md.)

### Decision Coverage

`check.decision-coverage-verify`: skipped — "no trackable decisions" (04-CONTEXT.md has no `<decisions>` block; non-blocking gate).

### Test Quality Audit

Not applicable in the classic per-test sense — this phase adds no test files; its assertion surfaces are CI verdicts and the smoke gate. Both surfaces re-proven active this pass: full pytest suite green per windows cell (1038 passed/16 skipped at 965760f1, delta from phase-time 1032 node-attributed to Phase-5's 6 lockstep teeth tests), per-wheel smoke + clean-room consumer gate green on both parameterization paths at the current workflow SHA.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers, zero placeholder text across ci.yaml / win-wheels.yaml / INSTALL; zero fail-open constructs; `CIBW_ENVIRONMENT: ""` is the documented deliberate POSIX-leak override, not a stub | - | - |

### Advisory (New Scope, Unevidenced)

Re-verification ran; no new-scope findings raised — the only covered-file change since the prior pass (`e960aba8`, win-wheels.yaml) was itself verified live at its own SHA (runs 38369651968 / 38369877795).

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| (none) | - | - | - |

### Info Observations (non-blocking, for the record)

1. **Phase-5 parameterization refinements inside win-wheels.yaml (accepted as later-phase work).** Three changes to the covered file since phase-4 close: (a) clean_smoke Python is now the choice-bounded `smoke_python` dispatch input with `SMOKE_PY`/derived `SMOKE_CP` env indirection (replaces the hardcoded cp313 glob — the single-definition debt item); (b) `CIBW_TEST_COMMAND` → platform-suffixed `CIBW_TEST_COMMAND_WINDOWS` (same semantics in this Windows-only workflow); (c) msys2-location reaches the PATH-append step via `MSYS2_LOCATION` env instead of inline `${{ }}`. All three PRESERVE or strengthen the phase-4 truths: script-form smoke unchanged, provenance rules unchanged, injection surface reduced to zero template expressions in run blocks. Proven live at the current SHA on both trigger paths.
2. **WR-02 idempotency fallback unexercised but structurally sound.** `gh release create … || gh release upload --clobber` (landed pre-refresh at 0cdffee9) preserves same-run-artifact provenance in both branches; no re-run has occurred, so the fallback branch remains unexercised — hardening, not a must-have.
3. **WR-01 still in force.** "Publish wheels" (release.yaml, id 360107850) = `disabled_manually` (re-checked live this pass) — user-approved, reversible; CI and Windows wheels workflows `active`.
4. **Truth 12 wording is phase-scoped by necessity after Phase 5.** The "exactly 3 files since 2ea68a19" claim holds verbatim at the phase-4 boundary (2ea68a19..0cdffee9); at HEAD the diff legitimately includes Phase-5's 8 files, every one from Phase-5-tagged commits matching Phase-5's ROADMAP goal. Recorded here so the next reader of the diff is not surprised.
5. **04-02 prohibition wording inconsistency (carried from prior pass, unchanged).** "no new third-party actions beyond msys2/setup-msys2@v2" vs the same plan's cibuildwheel truth — the only coherent reading (no release-publishing actions; publishing via preinstalled gh CLI) is what the code does; cibuildwheel activation was user-approved at the Task 1 blocking checkpoint.

### Human Verification Required

N/A — infrastructure/CI phase with no user-facing UI elements; auto-pass UAT scoping applies. All acceptance criteria were re-verified programmatically against the current tree and live external state, including verifier re-execution of the phase goal's literal user action (pip install from the distribution channel into a fresh venv + functional smoke). No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths: every behavioral claim (green cells, gate ordering, dry-run suppression, parameterized gate, consumer install) has live or verifier-re-executed evidence from this pass.

### Gaps Summary

None. All 12 must-have truths re-verified against the CURRENT tree and live GitHub state: the standing windows CI job is green (25/25 at a near-HEAD SHA), the wheel pipeline's current (Phase-5-parameterized) shape is proven live on both trigger paths with publish correctly suppressed off v-tags, the live Release is unchanged and byte-integrity-re-proven, and the consumer path was independently re-executed this pass (INSTALL-OK → smoke OK → SHADOW-ASSERT-OK). Zero-regression gates hold (ci.yaml pure addition at HEAD, pyproject.toml byte-identical, fail-open scans clean, phase-4 scope exactly 3 files at its boundary); the only covered-source change since the prior pass is Phase-5's win-wheels.yaml parameterization, itself live-proven at its own SHA. The milestone's distribution story — CI continuously producing clean-machine-gated self-contained win_amd64 wheels, published via the fork channel, pip-installable — remains achieved and live at https://github.com/forrestzhang/pysam/releases/tag/v0.24.1-win.2.

---

_Verified: 2026-10-13T11:06:04Z_
_Verifier: Claude (gsd-verifier)_
