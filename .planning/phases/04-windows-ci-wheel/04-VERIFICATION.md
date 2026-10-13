---
phase: 04-windows-ci-wheel
verified: 2026-10-13T06:48:31Z
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
covered_digest: "v3:sha256:08e484440414f1bd24711385c0b5c4a6d1f89859dc2bca3fe1d6d6eb52cbc0e2"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 4: Windows CI 与 wheel 分发 Verification Report

**Phase Goal:** CI 持续产出经清洁机冒烟测试把关的自包含 `win_amd64` wheel，经 fork 渠道发布 — Windows 用户 `pip install` 即可用。
**Verified:** 2026-10-13T06:48:31Z
**Status:** passed
**Re-verification:** No — initial verification

**Verification method note:** this phase's deliverables are CI pipelines and a published distribution channel, so the decisive evidence is LIVE external state (GitHub Actions runs, the fork Release, the distribution URL), not file presence. Every SUMMARY claim below was re-checked against the live GitHub state via `gh`, and the consumer path was independently re-executed by the verifier from the live Release URL. The final phase of the milestone was verified with full rigor.

## Goal Achievement

### Observable Truths

Merged from ROADMAP SC-1..SC-4 (the contract) plus PLAN frontmatter truths, deduplicated (roadmap wording kept where plans restate an SC).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC-1: `windows-latest` 手工 build+pytest job 全绿（3.10–3.15） | ✓ VERIFIED | ci.yaml `windows` job (lines 221-267): windows-latest, shell bash, matrix 3.10-3.15, MSVC build + PYTHONPATH pytest. LIVE: run 38296297134 @ 207b6901 = conclusion success, 25/25 jobs, 0 non-success; final-SHA run 38343462764 @ 1053e95f = success 25/25; WR-02-fix SHA run 38346109919 @ 0cdffee9 = success 25/25 (all three re-checked via gh by verifier) |
| 2 | SC-2: cibuildwheel + delvewheel 自包含 win_amd64 wheel，3.10–3.15 全矩阵 | ✓ VERIFIED | win-wheels.yaml: cibuildwheel@v4.3.1, CIBW_BUILD "cp310-* … cp315-*", delvewheel repair --ignore-existing. LIVE: Release v0.24.1-win.2 holds exactly 6 assets cp310-cp315, all win_amd64; verifier downloaded all 6 — sha256s match 04-CI-VALIDATION.md §3 byte-for-byte; delvewheel "no external dependencies are needed" appears exactly 6x in publish run 38332836356 build_wheels log (verifier-grep); verifier's own import-table audit of the cp313 wheel: 13 .pyd, 0 bundled .dll, 0 msvcrt.dll imports |
| 3 | SC-3: 清洁机冒烟测试作为发布门槛（gate pass 才允许发布） | ✓ VERIFIED | win-wheels.yaml: `clean_smoke` job (fresh venv, interpreter-filtered wheel install dist/*-cp313-cp313-win_amd64.whl, SCRIPT-form smoke — never `python -m`); `release` job has `needs: clean_smoke`. LIVE: clean_smoke success on runs 38328253612, 38329297031, 38332836356; publish run's release job ran strictly after gate success (platform-enforced `needs:` ordering) |
| 4 | SC-4: fork Releases 发布，pip 安装后 htslib API 绑定与 samtools/bcftools 命令分派全部可用 | ✓ VERIFIED | LIVE Release v0.24.1-win.2: non-draft (isDraft=false), 6 assets. Verifier independently re-executed the consumer path: fresh venv → `pip install <live Release URL cp313 wheel>` → devtools/smoke_test.py script-form → "24 alignments read / 44118 vcf lines / smoke OK" (exercises AlignmentFile fetch = htslib API; samtools view -b + bcftools view -H = command dispatch) → shadowing assert as script file: `pysam.__file__` inside the venv's site-packages. Full-suite functional parity additionally carried by the 6 green direct-job cells (truth 1) |
| 5 | BUILD-03 符号门在 runner 上真实执行 — llvm-nm 经 msys2/setup-msys2 供给，缺失即硬失败，从未被 patch 跳过 (04-01) | ✓ VERIFIED | ci.yaml windows job + win-wheels.yaml both provision `mingw-w64-ucrt-x86_64-llvm-tools` (release:false) and GITHUB_PATH-append. setup.py:509-518: on win32 `check_ext_symbol_conflicts()` runs OUTSIDE the exception-swallowing wrapper (the try/except OSError/CalledProcessError skip exists only on the POSIX else-branch, lines 519-526) — a missing/failing llvm-nm aborts the build on Windows by code structure. Fail-open scan: 0 `continue-on-error` in either workflow |
| 6 | 零回归：所有 pre-existing ci.yaml job 字节不变（纯加法） | ✓ VERIFIED | `git diff 2ea68a19..HEAD -- ci.yaml` deleted lines = 0 (pure addition); LIVE: 19 pre-existing jobs success in all three checked runs (25/25 = 6 windows + 19 pre-existing, 0 non-success each) |
| 7 | 六个 per-cell pytest 计数来自真实 run log（非编造） | ✓ VERIFIED | 04-01-SUMMARY table present. Disconfirmation check: verifier pulled the windows (3.13) job log (job 114968083996) from run 38296297134 — verbatim line "1032 passed, 16 skipped in 18.87s" matches the recorded table exactly (count and duration) |
| 8 | pyproject.toml POSIX cibuildwheel hooks 字节不变 | ✓ VERIFIED | `git diff 2ea68a19..HEAD -- pyproject.toml setup.py devtools/ vendor/ win32/ .github/workflows/release.yaml` = empty (protected-file gate) |
| 9 | Dry-run tag 绝不发布；publish 路径从 PR 不可达 (04-02) | ✓ VERIFIED | win-wheels.yaml triggers: `push.tags [v[0-9]+.*, win-test*]` + workflow_dispatch only — no branch/pull_request triggers; release job `if: startsWith(github.ref, 'refs/tags/v')` excludes win-test*. LIVE empirical proof: runs 38328253612 (win-test.1) and 38329297031 (win-test.2) both show release conclusion = skipped while build+clean ran green |
| 10 | 04-CI-VALIDATION.md 存在且证据 SHA-pinned、与真实世界一致 | ✓ VERIFIED | File read: 6 sections, 8 sha256 rows, CI-03 alignment section, Q1-Q5 adopted-recommendation register, node-exact CI-vs-local reconciliation (1032/16 = 1028/15 +6 mypy −2 tty +1 upstream-3.11); every verdict cites run ID/SHA/tag. World-match: all 6 sha256s re-verified against fresh `gh release download` (6/6 identical); run-log count line re-verified (truth 7); publish-run delvewheel markers re-verified (truth 2) |
| 11 | INSTALL 记录 Windows 预编译 wheel 安装路径 | ✓ VERIFIED | INSTALL lines 91-109: "Windows (prebuilt wheel)" section — fork Releases URL, full-URL pip install command (cp313 worked example from v0.24.1-win.2), python.org CPython 3.10–3.15 as the only requirement, self-containedness note. The URL it documents is the one the verifier installed from successfully |
| 12 | 阶段源码范围 = 恰好 3 个文件 + final-SHA CI 双面全绿 (04-03) | ✓ VERIFIED | `git diff --name-only 2ea68a19..HEAD` minus .planning/ = exactly {.github/workflows/ci.yaml, .github/workflows/win-wheels.yaml, INSTALL}; final-SHA run 38343462764 @ 1053e95f = 25/25 success (LIVE re-check) — build code untouched |

**Score:** 12/12 truths verified (0 present, behavior-unverified)

No deferred items — Phase 4 is the final phase of the milestone (nothing later to defer to).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.github/workflows/ci.yaml` | Additive `windows` job, 6-version matrix, symbol gate live | ✓ VERIFIED | Present at HEAD; substantive (windows job + all pre-existing jobs intact); wired — three live 25/25 green runs verified |
| `.github/workflows/win-wheels.yaml` | build_wheels → clean_smoke → release chain | ✓ VERIFIED | Present at HEAD (incl. WR-02 idempotency fallback at 0cdffee9); substantive; wired — 4 live runs verified with expected verdicts incl. release skipped on dry runs |
| `INSTALL` | Windows prebuilt-wheel consumer section | ✓ VERIFIED | Lines 91-109; URL + pip command + 3.10-3.15 face; the documented URL proven live by verifier install |
| `.planning/.../04-CI-VALIDATION.md` | SHA-keyed evidence record | ✓ VERIFIED | 6 sections, 8 sha256 rows; contents cross-checked against live Release and run logs — no fabrication detected |
| Six wheels at Release v0.24.1-win.2 | cp310-cp315 win_amd64, non-draft | ✓ VERIFIED | LIVE: 6 assets, isDraft=false, all six CPython tags present; 6/6 sha256 match the record |
| 04-01/02/03-SUMMARY.md | Run URLs, counts, commits | ✓ VERIFIED | All run IDs/conclusions/shas re-checked live; every checked claim matched |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| tag push | win-wheels.yaml | `on.push.tags` + dispatch only | ✓ WIRED | No branch/PR trigger exists in the file; empirically: branch pushes fired only CI (e.g. 0cdffee9), tags fired win-wheels |
| build_wheels | clean_smoke | `needs:` + same-run download-artifact (nameless, merge-multiple) | ✓ WIRED | Provenance rule holds: no run-id/URL inputs anywhere in the release/clean jobs |
| clean_smoke | release | `needs: clean_smoke` + `if: refs/tags/v` | ✓ WIRED | Publish run 38332836356: all three success in dependency order; dry runs: release skipped |
| windows-latest runner | llvm-nm → MSVC build → pytest | setup-msys2 → GITHUB_PATH append → `python setup.py build` → PYTHONPATH(cygpath) pytest | ✓ WIRED | Full chain in ci.yaml windows job; green across all checked runs |
| Release URL | fresh venv install → script-form smoke → site-packages | pip by full URL; `devtools/smoke_test.py`; script-file assert | ✓ WIRED | Verifier re-executed the whole link live: INSTALL-OK → smoke OK → SHADOW-ASSERT-OK |

### Data-Flow Trace (Level 4)

Workflow artifacts, not UI data; the flowing "data" is the wheels themselves.

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| win-wheels.yaml | `wheelhouse/*.whl` → artifact → `dist/*.whl` → Release assets | cibuildwheel build (run 38332836356) | Yes — the released assets' sha256s (verifier-computed from fresh download) match the record keyed to that run | ✓ FLOWING |
| ci.yaml windows job | `build/lib.win-amd64-cpython-*` via PYTHONPATH | real `python setup.py build` output | Yes — pytest collected 1047 items per cell (a broken PYTHONPATH failed collection in run 38291397314, proving the path is load-bearing) | ✓ FLOWING |
| 04-CI-VALIDATION.md | counts / sha256s / verdicts | live run logs + `gh release download` | Yes — re-derived by verifier: pytest line, 6 sha256s, delvewheel markers all match | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Consumer: URL install + script smoke + shadowing assert (SC-4) | fresh venv → pip install live Release URL → smoke_test.py → TEMP assert-script | INSTALL-OK; 24 alignments / 44118 vcf lines / smoke OK; pysam.\_\_file\_\_ inside venv site-packages | ✓ PASS |
| Release live state | `gh release view v0.24.1-win.2` | non-draft, 6 assets cp310-cp315 | ✓ PASS |
| Wheel integrity vs record | `gh release download` + sha256sum | 6/6 digests identical to 04-CI-VALIDATION.md §3 | ✓ PASS |
| CLAUDE.md wheel anti-pattern (msvcrt.dll) | unzip cp313 wheel, scan 13 .pyd import tables | 0 bundled .dll, 0 msvcrt.dll imports | ✓ PASS |
| CI verdicts (3 SHAs) | `gh run view` 38296297134 / 38343462764 / 38346109919 | all success, 25 jobs, 0 non-success | ✓ PASS |
| Pipeline verdicts (4 runs) | `gh run view` 38328253612 / 38329297031 / 38332836356 / 38331012769 | dry: release skipped; publish: 3/3 success; win.1: release failure (audit trail as recorded) | ✓ PASS |
| Evidence authenticity (fabrication check) | grep run 38296297134 job-114968083996 log; grep publish-run build log | "1032 passed, 16 skipped in 18.87s" verbatim match; delvewheel marker x6 | ✓ PASS |
| YAML validity | miniconda yaml.safe_load both workflows | both-yaml-ok | ✓ PASS |
| WR-01 state | `gh api .../actions/workflows` | "Publish wheels" (release.yaml, id 360107850) = disabled_manually, user-approved, reversible | ✓ PASS |
| Zero-regression gates | git diff vs 2ea68a19; grep continue-on-error | scope = exactly 3 files; ci.yaml 0 deleted lines; 0 fail-open constructs; protected files byte-identical | ✓ PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` declared by the plans; this phase's probes were the live CI runs and Release checks above (Step 7b table).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CI-01 | 04-01 | windows-latest runner（先手工 build+pytest job，验证后接入 cibuildwheel） | ✓ SATISFIED | Truths 1, 5, 6: hand job green 3.10-3.15; cibuildwheel integration verified in truth 2 |
| CI-02 | 04-02, 04-03 | MSVC 自包含 win_amd64 wheel + delvewheel 修复 + 清洁机冒烟发布门槛 + fork Releases 分发 | ✓ SATISFIED | Truths 2, 3, 4: live Release with 6 self-contained wheels (no msvcrt.dll, no vendor DLLs); clean-machine gate wired and empirically gating publish; consumer path re-executed live |
| CI-03 | 04-02, 04-03 | wheel 覆盖 3.10–3.15（以 python_requires 为准） | ✓ SATISFIED | Truth 2 + 04-CI-VALIDATION §5: 6 wheels cp310-cp315 on the live Release; requires-python >=3.9 untouched (documented alignment — cp310+ tags never select on 3.9, no incompatible offer) |

Orphaned requirements: none — REQUIREMENTS.md maps exactly CI-01/CI-02/CI-03 to Phase 4; all three are claimed by plans and verified. (All 13 v1 requirements now complete per REQUIREMENTS.md.)

### Decision Coverage

`check.decision-coverage-verify`: skipped — "No trackable decisions in CONTEXT.md." (04-CONTEXT.md has no `<decisions>` block; non-blocking gate).

### Test Quality Audit

Not applicable in the classic per-test sense — this phase adds no test files; its assertion surfaces are CI verdicts and the smoke gate. Noted for the record: the two assertion surfaces (Q1 decision) are both active — full pytest suite (1032 passed/16 skipped per cell) in the direct job, per-wheel smoke + clean-room consumer gate in the wheel pipeline; zero exemptions granted to reach green (04-CI-VALIDATION §1), and the CI-vs-local count delta is reconciled node-exactly with in-repo mechanisms (mypy collection, tty-gated skips, upstream 3.11 skipif).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers; no continue-on-error; no empty implementations; no placeholder text in the three phase files | - | - |

### Info Observations (non-blocking, for the record)

1. **HEAD differs from the Release-producing SHA (expected, accepted).** The released wheels' provenance run is 38332836356 @ ddaa9b68; post-release, commit 0cdffee9 added the WR-02 re-run resilience fallback (`gh release create … || gh release upload --clobber`) to win-wheels.yaml. Same-run-artifact provenance (T-04-06) is preserved in the fallback; CI green at that SHA (run 38346109919, 25/25, verifier-checked). The fallback branch itself is unexercised (no re-run has occurred) — it is a code-review hardening, not a plan must-have, so it creates no gap.
2. **WR-01 resolved by user-approved workflow disable.** The pre-existing "Publish wheels" (release.yaml) workflow on the fork is `disabled_manually` (id 360107850, verifier-checked live) — stops Windows v-tags collaterally firing the doomed PyPI publish; reversible. This avoided editing release.yaml, which would have breached the phase scope gate.
3. **04-02 prohibition wording is internally inconsistent** ("no new third-party actions beyond msys2/setup-msys2@v2") with the same plan's truth requiring pypa/cibuildwheel@v4.3.1. The only coherent reading — no release-publishing actions; publishing via the preinstalled gh CLI — is what the code does; cibuildwheel activation was explicitly user-approved at the Task 1 blocking supply-chain checkpoint (recorded in 04-02-SUMMARY). No action needed.
4. **IN-01..IN-03 code-review info findings remain open** as advisory backlog (04-REVIEW-DISPOSITION) — comment-level and hardening items, explicitly out of the fix scope; none affects the phase truths.

### Human Verification Required

N/A — infrastructure/CI phase with no user-facing UI elements. All acceptance criteria were verified programmatically against live external state (CI run conclusions, Release assets, sha256 digests, run-log lines) plus verifier-executed reproduction of the consumer path (the phase goal's literal user action — pip install from the distribution channel — was performed and passed). No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths: every behavioral claim (green cells, gate ordering, dry-run suppression, consumer install) has live or verifier-re-executed evidence.

### Gaps Summary

None. All 12 merged must-have truths verified against the live codebase and GitHub state; all artifacts present, substantive, and wired; all key links proven both structurally and empirically; zero-regression gates green (scope exactly 3 files, pure-addition ci.yaml, protected files byte-identical, fail-open scans clean); the evidence record matches the world (sha256s, run-log counts, delvewheel markers all re-derived and identical). The milestone's distribution story — CI continuously producing clean-machine-gated self-contained win_amd64 wheels, published via the fork channel, pip-installable — is achieved and live at https://github.com/forrestzhang/pysam/releases/tag/v0.24.1-win.2.

---

_Verified: 2026-10-13T06:48:31Z_
_Verifier: Claude (gsd-verifier)_
