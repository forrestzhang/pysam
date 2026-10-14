# CI Matrix Validation — windows cells and wheel matrix vs the Phase-2/3 local baselines (1028/15)

**Plan:** 04-03 · **Evidence policy:** every count and verdict below cites its run ID, commit SHA, or release tag — nothing from memory. **Baseline sources:** `03-SC2-RECONCILIATION.md` (local MSVC suite, `_venv-msvc` Miniconda CPython 3.13.5: `1028 passed, 15 skipped`, collection 1041) and `02-TEST02-RECONCILIATION.md` (Phase-2 UCRT64, Python 3.14.7, SHA `d912a1df`: `1027 passed, 15 skipped`).

## 1. Direct-job matrix evidence — the six windows cells (ci.yaml `windows` job, CI-01)

Final matrix run: [38296297134](https://github.com/forrestzhang/pysam/actions/runs/38296297134) @ SHA `207b6901` — 25/25 jobs success (6 windows cells + 19 pre-existing jobs). Per-cell pytest summary lines captured verbatim from that run's job logs:

| Cell | Collected | Passed | Skipped | Duration |
|------|-----------|--------|---------|----------|
| windows (3.10) | 1047 items / 1 skipped | 1032 | 16 | 27.73s |
| windows (3.11) | 1047 items / 1 skipped | 1031 | 17 | 35.26s |
| windows (3.12) | 1047 items / 1 skipped | 1032 | 16 | 35.19s |
| windows (3.13) | 1047 items / 1 skipped | 1032 | 16 | 18.87s |
| windows (3.14) | 1047 items / 1 skipped | 1032 | 16 | 39.08s |
| windows (3.15) | 1047 items / 1 skipped | 1032 | 16 (+2 warnings) | 32.21s |

Cell-only deviation triage (numbered, 03-SC2 shape; every row names reproduce/root-cause evidence and a disposition):

| # | Cell-only deviation | Root-cause evidence | Disposition |
|---|---|---|---|
| 1 | windows (3.11) carries one extra skip vs sibling cells: `tests/AlignmentFilePileup_test.py::TestPileupObjects::testIteratorOutOfScope` | Upstream-owned conditional, `@pytest.mark.skipif(sys.version_info[:2] == (3, 11) or sys.platform.startswith("netbsd"), reason="exercises invalid accesses, which crashes on Python 3.11 and NetBSD")` (`tests/AlignmentFilePileup_test.py:177`) — fires on the 3.11 interpreter only, by design | **benign — upstream test hygiene**, not a runner anomaly; no action |
| 2 | Two reds during bring-up (not present in the final matrix): pytest collection died at the PYTHONPATH glob (run [38291397314](https://github.com/forrestzhang/pysam/actions/runs/38291397314) @ `f0ff49a2`) and at setuptools 65.5.0 stdout detach on 3.10/3.11 hostpythons (run [38294145577](https://github.com/forrestzhang/pysam/actions/runs/38294145577) @ `05d50278`) | Environment-provisioning facts root-caused with local reproduction before any fix (`cygpath -m` glob expansion; `pip install --upgrade` for the bundled-setuptools detach), both fixed inside the additive windows job only — recorded in `04-01-SUMMARY.md` with commits `ec1dc63a` / `207b6901` | **already fixed and recorded** (04-01); no setup.py change at any point |

Zero exemptions (skips, xfails, deselections) were granted to reach these counts; the skip family is reconciled node-for-node in section 2.

## 2. CI-vs-local count reconciliation (node-exact, not arithmetic)

Verbatim captured counts:

```
CI runner, run 38296297134 @ 207b6901 (python.org interpreters, windows-latest):
  1032 passed, 16 skipped  (3.10/3.12/3.13/3.14/3.15)
  1031 passed, 17 skipped  (3.11)
  collection: 1047 items / 1 skipped

Local MSVC baseline, 03-SC2-RECONCILIATION (_venv-msvc, Miniconda CPython 3.13.5):
  1028 passed, 15 skipped in 20.01s
  collection: 1041
```

Every delta named, each with its mechanism (all grounded in the in-repo source):

1. **+6 collected items / −1 module placeholder — the mypy module.** `tests/typechecking_test.py` holds exactly 6 tests (counted in-repo) and module-skips with `pytest.skip('mypy API not available', allow_module_level=True)` (`tests/typechecking_test.py:17`) when mypy is absent — the case in `_venv-msvc` and the Phase-2 UCRT64 venv (same env-difference class the Phase-2/3 reconciliations recorded). The windows job's prerequisite line installs mypy (`pip install --upgrade Cython mypy pytest setuptools`, ci.yaml windows job), so all 6 collect and pass on CI.
2. **−2 passed / +2 node skips — the tty-gated usage tests.** `TestSamtools::testUsage` and `TestPysam::testUsage` both carry `@pytest.mark.skipif(not sys.stdin.isatty(), reason="skipping usage tests, stdin is not a tty")` (`tests/samtools_test.py:275`; `TestPysam` inherits the decorated method — `class TestPysam(TestSamtools)`, line 365; the `TestBcftools` subclass is commented out in-tree, so exactly two units exist). A runner's stdin is never a tty, so both units skip on every CI cell; the local baseline session ran on a tty, so both ran and passed there.
3. **3.11 only — upstream skipif.** The extra unit in the 3.11 cell is triage row 1 of section 1 (`testIteratorOutOfScope`, upstream-owned).

Arithmetic (node-exact): passed `1032 = 1028 + 6 − 2`; skipped `16 = 15 − 1 + 2`; items `1047 = 1041 + 6`; the 3.11 cell adds exactly the upstream skip (`1031/17`). The common node-skip set is the Phase-2/3 environment-shaped family recorded node-for-node in `03-SC2-RECONCILIATION.md` §3 — 11 libcurl capability gates (remote I/O deferred to v2) + 2 unconditional upstream skips (large-cigar CRAM, `test_samtools_processing` "test contains bug") = 13 — plus the `linking_test.py` module env gate present on both sides (`PYSAM_LINKING_TESTS` unset). No unexplained difference remains.

## 3. Wheel matrix and integrity — Release v0.24.1-win.2

Publish run: [38332836356](https://github.com/forrestzhang/pysam/actions/runs/38332836356) @ SHA `ddaa9b68` (tag `v0.24.1-win.2`) — build_wheels / clean_smoke / release all success. The delvewheel self-containedness marker appears once per wheel in that run's build log (job 115086235074): "Successfully built pysam-0.24.1-cp3XX-…" followed by "no external dependencies are needed" at 01:42:41 (cp310), 01:45:32 (cp311), 01:48:40 (cp312), 01:51:42 (cp313), 01:54:51 (cp314), 01:57:57 (cp315) — six of six. sha256s computed by this task (2026-10-13) from `gh release download v0.24.1-win.2 --pattern "*.whl"` into a clean TEMP dir — six files, exactly the six expected names:

| CPython | Wheel | sha256 | Size (bytes) | delvewheel verdict (run 38332836356) |
|---------|-------|--------|--------------|--------------------------------------|
| 3.10 | pysam-0.24.1-cp310-cp310-win_amd64.whl | sha256 `10859a94a98e5b34c71923b18549d0293fd4abc4a4cfc9d1285d58a60d918433` | 2981805 | no external dependencies are needed |
| 3.11 | pysam-0.24.1-cp311-cp311-win_amd64.whl | sha256 `ad54ba2239ed0a8d11ad1aef85a18991b5c792d6056cfe8930a1456a738c1ca5` | 2981025 | no external dependencies are needed |
| 3.12 | pysam-0.24.1-cp312-cp312-win_amd64.whl | sha256 `851d34df42fb073dbe43112e65163c0147dd4a2a476e654179cf0cb06f50daa7` | 2975075 | no external dependencies are needed |
| 3.13 | pysam-0.24.1-cp313-cp313-win_amd64.whl | sha256 `5fe4cbe2593bd01c4daff8dbb809c37b5a7791d6b2df19167474e3cd79a1e84d` | 2968381 | no external dependencies are needed |
| 3.14 | pysam-0.24.1-cp314-cp314-win_amd64.whl | sha256 `7caca0f023eb08800319458bdeb832a3ab3d770893bc8dece86615ecae0e0e14` | 3047605 | no external dependencies are needed |
| 3.15 | pysam-0.24.1-cp315-cp315-win_amd64.whl | sha256 `670a0c0f5a7b89622ab961a92f4e92bd41d0db9469d83a690484c77b46c532b1` | 3045285 | no external dependencies are needed |

**Import-table self-containedness** (04-RESEARCH Example 4 probe, `llvm-objdump -p` over all 13 `.pyd` files of the cp313 wheel): the only external DLL imports are `python3XX.dll`, `VCRUNTIME140.dll`, UCRT `api-ms-win-crt-*.dll`, `KERNEL32.dll`, and `WS2_32.dll` (libchtslib only) — all shipped with or provided by the OS alongside any CPython distribution. **No vendor DLL** (all vendor trees link statically), **no `msvcrt.dll`** (CLAUDE.md wheel anti-pattern audit passes), no `vcruntime140_1.dll`. The delvewheel marker above is the same verdict re-asserted per wheel at publish time.

## 4. Clean-machine gate (SC-3) and consumer-path proof from the distribution channel (SC-4)

- **CI clean-machine gate** (`clean_smoke` job — separate consumer job, fresh venv, wheel install from same-run artifact, script-form smoke): success on run [38329297031](https://github.com/forrestzhang/pysam/actions/runs/38329297031) (win-test.2, @ `3b26df3b`, job "clean_smoke") and on run [38332836356](https://github.com/forrestzhang/pysam/actions/runs/38332836356) (v0.24.1-win.2, @ `ddaa9b68`, job 115091894999) — the release job ran strictly after the gate passed in the same run.
- **Consumer-path proof from the live Release URL** (this task, 2026-10-13; the verification no CI job performed — a real consumer outside every build environment): fresh venv from `D:/miniconda3/python.exe` (CPython 3.13.5) under `%TEMP%\gsd-uat-venv`; `pip install` of the cp313 wheel by its full Release URL (`https://github.com/forrestzhang/pysam/releases/download/v0.24.1-win.2/pysam-0.24.1-cp313-cp313-win_amd64.whl`) — fetching the actually-published asset exercises DNS/TLS/auth-free download of the real distribution channel. Result: install OK; `devtools/smoke_test.py` run SCRIPT-FORM from the repo root printed `24 alignments read` / `44118 vcf lines` / `smoke OK` (exit 0); shadowing assert: `pysam.__file__ = C:\Users\forre\AppData\Local\Temp\gsd-uat-venv\Lib\site-packages\pysam\__init__.py` — inside the fresh venv's site-packages, not the source tree.
- **Shadowing-guard note:** the guard has teeth, and the proof context matters — a `python -c` invocation issued from the repo root puts `''` (cwd) at `sys.path[0]` and DOES resolve `import pysam` to the checkout (`D:\Github\pysam\pysam\__init__.py`; observed). The proof above uses the script form (`sys.path[0]` = the script's directory, repo root never on `sys.path`), which is exactly the resolution context of `devtools/smoke_test.py` — the `python -m` / `-c`-from-repo-root forms are false tests (04-RESEARCH Pitfall 3).

## 5. CI-03 alignment — wheel face 3.10–3.15 vs in-tree `requires-python >=3.9`

- **Matrix face (what we build and publish):** CPython 3.10–3.15, six wheels — `CIBW_BUILD: "cp310-* cp311-* cp312-* cp313-* cp314-* cp315-*"` in `.github/workflows/win-wheels.yaml`; evidenced by the six rows of section 3 and the artifact name `wheels-win-amd64-310-311-312-313-314-315` (run 38329297031).
- **In-tree metadata (unchanged):** `requires-python = ">=3.9"` (`pyproject.toml:8`) — byte-identical since phase base `2ea68a19` (phase scope audit; touching it would alter POSIX sdist/wheel publishing semantics, which is outside this phase and prohibited by the plan).
- **The documented reading (04-RESEARCH Pitfall 7):** the two statements do not conflict. `requires-python` describes interpreter compatibility of the distribution metadata; the wheel face is what cibuildwheel builds. A `cp310`-and-later wheel tag never selects on a 3.9 interpreter (pip refuses on tag mismatch), so a 3.9 user is never offered an incompatible wheel — they fall back to the sdist, exactly as before this fork existed. CI-03 locks the Windows wheel face at 3.10–3.15, so no cp39 wheel is built deliberately: **Python 3.9 is EOL (2025-10) and CI-03's face is 3.10–3.15**; if a cp39 wheel were ever wanted it is one added `CIBW_BUILD` cell.

## 6. Adopted-recommendation register — research open questions Q1–Q5 (04-RESEARCH, all resolved by plans 04-01/04-02)

| Q | Research recommendation | Adopted disposition | Validating evidence |
|---|---|---|---|
| Q1 | cibuildwheel test = smoke; full pytest suite stays in the ci.yaml direct job (two assertion surfaces: source-tree build vs wheel artifact) | Adopted verbatim: `CIBW_TEST_COMMAND` = script-form smoke in win-wheels.yaml; full suite in the ci.yaml `windows` job | Run [38296297134](https://github.com/forrestzhang/pysam/actions/runs/38296297134) (full suite ×6 cells, section 1) + run [38332836356](https://github.com/forrestzhang/pysam/actions/runs/38332836356) (per-wheel smoke inside cibuildwheel + separate clean_smoke gate) |
| Q2 | fork tag form `v0.24.1-win.1` | Tag FORM adopted (`v<version>-win.N`); the published lineage is **v0.24.1-win.2** — win.1's release job failed before creating any Release (run [38331012769](https://github.com/forrestzhang/pysam/actions/runs/38331012769), `gh release create` without repo context), and plan 04-02 Task 4's contingency pre-authorized re-tagging rather than re-using the failed tag name; the win.1 tag + failed run remain as the audit trail | Release [v0.24.1-win.2](https://github.com/forrestzhang/pysam/releases/tag/v0.24.1-win.2) (non-draft, 6 assets — section 3); GH_REPO fix commit `ddaa9b68` |
| Q3 | cibuildwheel@v4.3.1 for the fork Windows job; upstream release.yaml 4.2.1 pin untouched | Adopted verbatim (4.3.1 carries CPython 3.15.0 final; the upstream POSIX pin is out of scope and byte-identical since `2ea68a19`) | Publish run log "Successfully built cibuildwheel" then six cp310–cp315 wheels incl. the 3.15.0-final build (section 3 timestamps); scope audit shows release.yaml untouched |
| Q4 | no cp39 wheel | Adopted (section 5 rationale) | Release asset list: exactly cp310–cp315, no cp39 (section 3) |
| Q5 | direct windows job = six-version full matrix | Adopted verbatim (`['3.10'..'3.15']` in ci.yaml windows job) | Run [38296297134](https://github.com/forrestzhang/pysam/actions/runs/38296297134): six windows cells + 19 pre-existing jobs, 25/25 success |
