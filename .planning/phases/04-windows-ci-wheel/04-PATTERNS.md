# Phase 4: Windows CI 与 wheel 分发 - Pattern Map

**Mapped:** 2026-10-13
**Files analyzed:** 3 (2 workflows + 1 optional validation record; pyproject.toml explicitly NOT modified)
**Analogs found:** 3 / 3 (all analog paths verified git-tracked via `git ls-files`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.github/workflows/ci.yaml` (add `windows` job) | config (CI workflow) | batch (build+test matrix) | `.github/workflows/ci.yaml` `direct` job (lines 8–77) | exact (same file, sibling job) |
| `.github/workflows/win-wheels.yaml` (NEW) | config (CI workflow) | batch → artifact → request-response (publish) | `.github/workflows/release.yaml` (whole file) + `ci.yaml` job conventions | exact for both halves |
| `.planning/phases/04-windows-ci-wheel/04-CI-VALIDATION.md` (or similar; if planner wants a matrix verification record) | doc (reconciliation record) | transform (evidence log) | `.planning/phases/03-msvc/03-SC2-RECONCILIATION.md` | role-match |
| `pyproject.toml` | config | — | **DO NOT MODIFY** (research Pattern 2; POSIX hooks must stay pristine) | n/a |
| `devtools/smoke_test.py`, `devtools/artifactname.py` | existing assets | — | reused verbatim, no edits | n/a |

## Pattern Assignments

### `.github/workflows/ci.yaml` `windows` job (config, batch)

**Analog:** same file — `direct` job (lines 8–77) for step conventions; `conda` job (lines 183–193) for the `defaults: run: shell:` precedent.

**Job skeleton + checkout convention** (copy from lines 8–24; `conda` job's job-level defaults at 190–192):
```yaml
  direct:
    runs-on: ${{ matrix.os }}-latest
    strategy:
      matrix:
        os: [ubuntu, macos]
        python-version: ['3.9', '3.10', '3.11', '3.12', '3.13', '3.14', '3.15-dev']

    steps:
      - name: Checkout pysam
        uses: actions/checkout@v7
        with:
          persist-credentials: false

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python-version }}
```
Note the step-naming style (`Checkout pysam`, `Set up Python ...`, `Install prerequisite Python libraries`) — keep it in the new job. Copy `persist-credentials: false` verbatim.

**Pip prerequisites + build + test invocation** (lines 26–27, 40–44, 57–59):
```yaml
      - name: Install prerequisite Python libraries
        run:  pip install Cython mypy pytest setuptools
      ...
        run:  python setup.py build
      ...
      - name: Run tests
        run: |
          PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*) pytest
```
This is the exact call chain the Windows job replicates (bash syntax — hence `shell: bash` default per RESEARCH Pitfall 6; `conda` job already shows the `defaults: run: shell: bash -el {0}` precedent at lines 190–192, so a job-level shell default is in-house style). Windows deltas: `runs-on: windows-latest`, matrix `['3.10'..'3.15']`, no OS-conditional prerequisite steps (MSVC path needs none), plus setup-msys2 for llvm-nm — the only step with NO in-repo analog; use RESEARCH Example 1 verbatim (msys2/setup-msys2@v2, `release: false`, `install: mingw-w64-ucrt-x86_64-llvm-tools`, GITHUB_PATH append). Build products land in `build/lib.win-amd64-cpython-*` — the `build/lib.*` glob already covers it.

**Anti-pattern guard:** do NOT insert windows into the existing `direct` `os:` matrix — its steps are guarded on `runner.os == 'Linux'/'macOS'` and assume POSIX shells. New standalone job = additive zero regression (RESEARCH Pattern 1).

**Top-level permissions discipline** (line 5): `permissions: {}` — leave untouched; new test-only jobs inherit it.

---

### `.github/workflows/win-wheels.yaml` (NEW; config, batch → artifact → publish)

**Analog:** `.github/workflows/release.yaml` (whole file, 118 lines).

**Trigger + permissions skeleton** (lines 3–10):
```yaml
on:
  push:
    branches:
      - release/*
    tags:
      - v[0-9]+.*

permissions: {}
```
Keep `permissions: {}` at workflow top (release job gets a job-level elevation instead — see below). Fork tag `v0.24.1-win.N` matches the existing `v[0-9]+.*` glob, so the trigger block can be copied verbatim (add `workflow_dispatch` if manual runs wanted).

**cibuildwheel step + CIBW env shape** (lines 34–50):
```yaml
      - name: Build wheels
        uses: pypa/cibuildwheel@v4.2.1
        env:
          CIBW_BUILD: ${{ matrix.build }}
          CIBW_SKIP:  ${{ case(matrix.kind == 'many', '*-musllinux_*', '*-manylinux_*') }}

          CIBW_BUILD_VERBOSITY: 1
          ...
          CIBW_ARCHS: native
```
Copy this step skeleton but pin `pypa/cibuildwheel@v4.3.1` for the fork Windows job (RESEARCH: 3.15.0 final). Do NOT copy the `case()` runner expressions or the POSIX matrix. Replace env with RESEARCH Example 2 verbatim (probe-validated combination):
```yaml
          CIBW_BUILD: "cp310-* cp311-* cp312-* cp313-* cp314-* cp315-*"
          CIBW_ARCHS: AMD64
          CIBW_BEFORE_ALL_WINDOWS: "echo no before-all on Windows (MSVC path self-contained)"
          CIBW_BEFORE_BUILD_WINDOWS: "echo skipping make distclean (MSVC path has no autotools artifacts)"
          CIBW_REPAIR_WHEEL_COMMAND_WINDOWS: "delvewheel repair --ignore-existing -w {dest_dir} -v {wheel}"
          CIBW_TEST_COMMAND: "python {project}/devtools/smoke_test.py"
          CIBW_ENVIRONMENT: ""
          CIBW_BUILD_VERBOSITY: "1"
```
The `--ignore-existing` flag is load-bearing (RESEARCH Pitfall 2, empirically verified). cibuildwheel itself needs llvm-nm too (symbol gate runs inside the isolated build) — reuse the same setup-msys2 + GITHUB_PATH step from the ci.yaml windows job.

**Artifact naming + upload convention** (lines 52–59):
```yaml
      - name: Check wheelhouse
        run:  devtools/artifactname.py wheelhouse/*.whl >> $GITHUB_ENV

      - name: Upload artifacts
        uses: actions/upload-artifact@v7
        with:
          name: ${{ env.artifactname }}
          path: wheelhouse/*.whl
```
Copy verbatim — `devtools/artifactname.py` yields `wheels-win_amd64-AMD64-310-...-315` (D:/Github/pysam/devtools/artifactname.py:25). Downstream jobs reference this exact name.

**Job-chain + download-artifact shape** (lines 94–107):
```yaml
  upload_pypi:
    needs: [build_wheels, build_sdist]
    runs-on: ubuntu-latest
    ...
    steps:
      - name: Get artifacts
        uses: actions/download-artifact@v8
        with:
          merge-multiple: true
          path: dist
```
This is the `needs:` + download pattern for the `clean_smoke` and `release` jobs. `clean_smoke` body = RESEARCH Example 3 verbatim (download → fresh venv → `pip install dist/*.whl` → `python devtools/smoke_test.py` — script-form invocation only, never `python -m`, per RESEARCH Pitfall 3).

**Permissions elevation + publishing step** (lines 97–100, the job-level `permissions:` precedent):
```yaml
    permissions:
      id-token: write  # Needed to upload to PyPI
```
This is the in-repo precedent for job-scoped permission elevation — the new `release` job does the same with `contents: write`, then `gh release create "$TAG" dist/*.whl --generate-notes --target "$GITHUB_SHA"` with `GH_TOKEN: ${{ github.token }}` and `TAG: ${{ github.ref_name }}` passed via `env:` (indirect reference prevents `${{ }}` injection; RESEARCH Pitfall 8). Release job runs on ubuntu-latest; it needs no checkout (artifact-only, like `upload_pypi`).

**smoke_test.py call contract** (D:/Github/pysam/devtools/smoke_test.py): resolves repo root from script location (lines 28–30) so a checkout of `tests/pysam_data` must exist in the clean_smoke job — hence that job checks out the repo. Exits nonzero on failure (lines 81–87); no args.

---

### `.planning/phases/04-windows-ci-wheel/04-CI-VALIDATION.md` (optional doc, transform)

**Analog:** `.planning/phases/03-msvc/03-SC2-RECONCILIATION.md` (also `02-TEST02-RECONCILIATION.md`).

Structure to copy: title naming the criterion + baseline source with SHA; numbered triage table (per-failure: reproduced outcome / root cause with evidence / disposition); verbatim captured counts block; node-exact reconciliation prose. Apply to the CI matrix first-run evidence: per-Python-version pass/skip counts vs the local 1028/15 baseline, any runner-only failures with root-cause dispositions.

---

## Shared Patterns

### Permissions discipline
**Source:** `.github/workflows/ci.yaml:5`, `.github/workflows/release.yaml:10,99-100`
**Apply to:** all new/modified workflow files.
```yaml
permissions: {}          # workflow top level — stays minimal everywhere
permissions:
  contents: write        # release job ONLY, job-scoped
```

### checkout/setup-python/action version family
**Source:** `.github/workflows/ci.yaml:17,22,73` / `release.yaml:24-27,104`
**Apply to:** every step in both workflows.
```yaml
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - uses: actions/setup-python@v7
```
Use `actions/download-artifact@v8` (matches release.yaml:104), `actions/upload-artifact@v7` (release.yaml:56), `pypa/cibuildwheel@v4.3.1` (fork Windows job only), `msys2/setup-msys2@v2`. No new third-party actions.

### Build + test invocation (Windows MSVC path)
**Source:** `devtools/msvc-build.md:85-92` (canonical invocation, verified in Phase 3)
**Apply to:** ci.yaml windows job.
```bash
export PATH="/c/msys64/ucrt64/bin:$PATH"   # CI equivalent: GITHUB_PATH append
python setup.py build                      # win-amd64 CPython auto-selects MSVC arm
PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*) pytest
```
No vcvars, no MSVC environment step — setuptools `_get_vc_env` self-locates (msvc-build.md:26-29). The symbol gate hard-fails without llvm-nm on PATH (by design, setup.py:509-518); never patch setup.py to skip it.

## No Analog Found

| Item | Reason | Fallback |
|------|--------|----------|
| `msys2/setup-msys2@v2` step (llvm-nm provisioning) | No in-repo use of this action | RESEARCH Example 1 verbatim (inputs: `msystem: UCRT64`, `release: false`, `update: false`, `install: mingw-w64-ucrt-x86_64-llvm-tools`) |
| `gh release create` publishing step | In-repo publishing uses `pypa/gh-action-pypi-publish`, not gh CLI | RESEARCH Example 3 verbatim (job-level `contents: write`, env-indirect TAG, GH_TOKEN) |
| delvewheel repair / CIBW_*_WINDOWS overrides | No in-repo Windows cibuildwheel config (by design — pyproject stays POSIX-pure) | RESEARCH Example 2 verbatim (probe-validated) |

## Metadata

**Analog search scope:** `.github/workflows/`, `devtools/`, `pyproject.toml`, `.planning/phases/*/` (reconciliation docs)
**Tracked-source gate:** all named analogs pass `git ls-files -- <path>` (verified 2026-10-13)
**Pattern extraction date:** 2026-10-13
