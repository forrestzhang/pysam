---
last_mapped_commit: 4c8486b106f36b1e1e548da5d70038d60fb95498
last_mapped_at: 2026-09-17
---
# Testing Patterns

**Analysis Date:** 2026-09-17

## Test Framework

**Runner:**

- pytest (version unpinned; installed via `pip install ... pytest` in CI and via `test-requires = ["pytest"]` in `pyproject.toml`'s cibuildwheel config).
- Config: `setup.cfg` `[tool:pytest]`:
  - `addopts = -s -v` — **`-s` (no stdout capture) is mandatory**: it conflicts with `pysam.dispatch`, which redirects file descriptors 1 and 2. Never run tests with capture enabled.
  - `testpaths = pysam tests` — the `pysam` path also collects any tests inside the package.
- Benchmarks: `pytest-benchmark` is used by `*_bench.py` files (e.g. `tests/AlignedSegment_bench.py` uses the `benchmark` fixture); it is not installed in CI and these files are effectively optional.

**Assertion Library:**

- Plain pytest `assert` (rewrite-enabled). No unittest assertions.

**Run Commands:**

```bash
pytest                        # from repo root (uses setup.cfg testpaths)
pytest tests/AlignmentFile_test.py   # single module
pytest tests/AlignmentFile_test.py::TestBAMFromFetch::testARqname  # single test
PYTHONPATH=build/lib.<plat> pytest   # CI pattern after `python setup.py build`
```

## Test File Organization

**Location:**

- All tests live in `tests/` at repo root. They are NOT co-located with `pysam/` package code (except whatever pytest collects under `testpaths = pysam tests`).
- Helpers are importable as top-level modules because pytest inserts the test dir into `sys.path` (no `tests/__init__.py`; rootdir-based conftest). Imports look like `from TestUtils import checkBinaryEqual, BAM_DATADIR` (`tests/AlignmentFile_test.py:22-23`).

**Naming:**

- `<Subject>_test.py` for test modules: `tests/AlignmentFile_test.py`, `tests/VariantFile_test.py`, `tests/VariantRecord_test.py`, `tests/AlignmentFileHeader_test.py`, `tests/AlignmentFilePileup_test.py`, `tests/AlignedSegment_test.py`, `tests/faidx_test.py`, `tests/tabix_test.py`, `tests/tabixproxies_test.py`, `tests/samtools_test.py`, `tests/typechecking_test.py`, `tests/compile_test.py`, `tests/StreamFiledescriptors_test.py`, `tests/linking_test.py`.
- `*_bench.py` for benchmarks (not run in CI): `tests/AlignedSegment_bench.py`, `tests/AlignmentFile_bench.py`, `tests/AlignmentFilePileup_bench.py`, `tests/AlignmentFileFetch_bench.py`, `tests/VariantFile_bench.py`, `tests/faidx_bench.py`, `tests/libcutils_bench.py`, `tests/tabix_bench.py`.
- `*TestUtils.py` / `TestUtils.py` for shared helpers (non-collected): `tests/TestUtils.py`, `tests/PileupTestUtils.py`, `tests/AlignmentFileFetchTestUtils.py`, `tests/VariantFileFetchTestUtils.py`.
- `conftest.py` at `tests/conftest.py` (session-scoped HTTP server fixture + `pytest_report_header` hook).

**Data directories:**

- `tests/pysam_data/` — BAM/SAM/CRAM/FA inputs; generated artifacts built by `tests/pysam_data/Makefile`.
- `tests/tabix_data/` — tabix-indexed files; `tests/tabix_data/Makefile`.
- `tests/cbcf_data/` — VCF/BCF files; `tests/cbcf_data/Makefile`.
- `tests/linker_tests/` — external-linking test fixtures (used via `LINKDIR` in `tests/TestUtils.py`).

## Test Structure

**Suite Organization:**

- Class-based grouping with `setup_method`/`teardown_method` (xunit style) and/or pytest fixtures — both coexist. Example from `tests/AlignmentFile_test.py:42-55`:

```python
class TestBAMFromFetch:
    def setup_method(self):
        self.samfile = pysam.AlignmentFile(os.path.join(BAM_DATADIR, "ex3.bam"), "rb")
        self.reads = list(self.samfile.fetch())

    def teardown_method(self):
        self.samfile.close()

    def testARqname(self):
        assert self.reads[0].query_name == "read_28833_29006_6945"
```

- Module-level data preparation via `def setUpModule(): make_data_files(BAM_DATADIR)` — required in any test module that reads generated `.bam`/`.cram` files (see `tests/AlignmentFile_test.py:26-27`, `tests/samtools_test.py:18-19`, `tests/compile_test.py:17-20`).

**Fixture-based setup** (newer style, `tests/samtools_test.py:135-161`):

```python
@pytest.fixture(autouse=True)
def setup_method(self, tmp_path):
    self.workdir = str(tmp_path)
    ...
    yield
    # teardown
```

**Patterns:**

- Setup: lazily build test data with `make_data_files(DATADIR)` (idempotent — uses `all.stamp` sentinel and `all.lock` lockdir in `tests/TestUtils.py:164-185`); copy inputs into `tmp_path` when the test mutates them.
- Teardown: `tmp_path`/`monkeypatch` fixtures auto-clean; manual cleanup via `os.unlink` globbing for voluminous samtools outputs (`tests/samtools_test.py:157-161`).
- Assertions: direct equality plus helper comparators `checkBinaryEqual`, `checkGZBinaryEqual`, `check_samtools_view_equal` (`tests/TestUtils.py:54-128`).

## Mocking

**Framework:** pytest built-ins only (`monkeypatch`, `tmp_path`). `unittest.mock` is NOT used anywhere in the suite.

**Patterns:**

```python
def test_remote_S3(httpserver, monkeypatch, tmp_path):
    monkeypatch.setenv("HTS_S3_HOST", httpserver)
    monkeypatch.setenv("HTS_S3_ADDRESS_STYLE", "path")
    monkeypatch.chdir(tmp_path)
```

(`tests/AlignmentFile_test.py:1434-1437`, `tests/tabix_test.py:911-912`)

**What to Mock:**

- Environment variables (`HTS_S3_HOST`, etc.) via `monkeypatch.setenv`.
- Working directory via `monkeypatch.chdir(tmp_path)`.
- Remote/network access via the session-scoped `httpserver` fixture (localhost HTTP server spawned with `multiprocessing` in `tests/conftest.py:35-45`); tests monkeypatch htslib's remote endpoints to point at it.

**What NOT to Mock:**

- pysam/HTSlib internals — tests are integration-heavy: they run real samtools/bcftools commands and compare binary output against pysam dispatchers (`tests/samtools_test.py` `check_statement` runs both `samtools` and `pysam.samtools.<cmd>` then byte-compares).

## Fixtures and Factories

**Test Data:**

- Static small files committed under `tests/pysam_data/`, `tests/tabix_data/`, `tests/cbcf_data/`.
- Derived files (BAM/CRAM/BAI/CSI) are generated at test time by make, not committed: each data dir has a `Makefile` whose `all` target produces an `all.stamp` file; `make_data_files()` in `tests/TestUtils.py` runs `make -C <dir>` (respects `$MAKE` env var, e.g. `gmake` on BSD — see `ci.yaml` `system` job env `MAKE: "gmake"`).
- Generation requires the `samtools` binary on PATH; CI installs it (`sudo apt-get install samtools bcftools tabix` / `brew install samtools bcftools`).

**Session fixtures (`tests/conftest.py`):**

- `httpserver` — yields `"host:port"` of a localhost HTTP server serving the `tests/` directory. Used for libcurl/GCS/S3 remote-file tests.
- `pytest_report_header` sets `os.environ["REF_PATH"] = ":"` globally to disable external reference lookups during CRAM tests.

## Coverage

**Requirements:** None enforced. No coverage measurement in CI.

**View Coverage:**

```bash
pytest --cov=pysam --cov-report=term-missing   # works locally; not part of CI
```

## Test Types

**Unit Tests:**

- Object-level tests of `AlignedSegment`, header manipulation, pileup columns (`tests/AlignedSegment_test.py`, `tests/AlignmentFileHeader_test.py`).

**Integration Tests (dominant style):**

- Round-trip comparisons of pysam output against real samtools/bcftools output (`tests/samtools_test.py` class `TestSamtools`; subclass `TestPysam` reuses the whole suite against the legacy `pysam.<cmd>` API — pattern: override `module = pysam` to re-parameterize a test class).
- Remote-protocol tests gated on build config (`tests/AlignmentFile_test.py:1382,1424,1433`; `tests/faidx_test.py:218`; `tests/tabix_test.py:905`):

```python
@pytest.mark.skipif(not getattr(pysam.config, "HAVE_LIBCURL", 0), reason="networking disabled")
```

  Always use `getattr(pysam.config, "FLAG", 0)` — flags include `HAVE_LIBCURL`, `ENABLE_GCS`, `ENABLE_S3`, `HAVE_LIBBZ2`, `HAVE_LIBLZMA`, `HAVE_LIBDEFLATE`, `HAVE_MMAP` (written by `setup.py` from `htslib/config.h`).

**Binary-layout tests:**

- `tests/compile_test.py` `TestBinaryCompatibility` asserts exact `__sizeof__` values (120/24/72/80/96/32) and is skipped off known architectures:

```python
@pytest.mark.skipif(platform.machine() not in ('aarch64', 'arm64', 'AMD64', 'x86_64'),
                    reason="different scalar sizes")
```

**Type-checking tests:**

- `tests/typechecking_test.py` runs `mypy.api` programmatically against generated snippets; module-level skip if mypy missing (`pytest.skip(..., allow_module_level=True)`). `pyximport` compile tests in `tests/compile_test.py` skip similarly when compilation fails at import time (`NO_PYXIMPORT`).

**Linking tests:**

- `tests/linking_test.py` is opt-in via `PYSAM_LINKING_TESTS` env var (module-level skip otherwise) and requires the separate `linker_tests/` tree.

**E2E Tests:** Not used.

## Platform-Specific Skips and Windows-Relevant Findings

**Existing platform skips (the idiom to follow):**

- `@pytest.mark.skipif(sys.platform.startswith("netbsd"), reason="exercises invalid accesses, crashing on NetBSD")` — `tests/AlignmentFilePileup_test.py:298`
- `@pytest.mark.skipif(sys.version_info[:2] == (3, 11) or sys.platform.startswith("netbsd"), ...)` — `tests/AlignmentFilePileup_test.py:177`
- `@pytest.mark.skipif(platform.machine() not in (...))` — `tests/compile_test.py:57`
- `@pytest.mark.skipif(not sys.stdin.isatty(), ...)` — `tests/samtools_test.py:242`

**No Windows skips exist.** `grep` for `win32|windows|_WIN32|msvc` across `tests/` and `pysam/` returns zero hits. The only Windows handling is the untested build branch in `setup.py:633-636` (adds `win32/getopt.c`, `win32/` include dir) and the shim headers `win32/getopt.c`, `win32/getopt.h`, `win32/stdint.h`, `win32/unistd.h`.

**Windows-blockers present in the test suite:**

1. POSIX shell subprocess calls with `shell=True` using external tools — will fail on Windows:
   - `subprocess.Popen('head -n200', shell=True)` — `tests/StreamFiledescriptors_test.py:46`
   - `os.system("samtools mpileup {} 2> /dev/null | awk ...")` — `tests/PileupTestUtils.py:29,54`
   - `subprocess.call(cmd, shell=True)` with samtools statements — `tests/samtools_test.py:25`
2. `errno.EPIPE` handling — `tests/StreamFiledescriptors_test.py:25` (Windows has no SIGPIPE/EPIPE semantics in the same way).
3. Data generation Makefiles (`tests/pysam_data/Makefile` etc.) use `samtools`, `gzip`, shell pipes, and `$(shell ...)` — require make + POSIX shell (consider pre-generating data or a Python fallback for Windows).
4. Multiprocessing start method: `tests/conftest.py` spawns the HTTP server with `multiprocessing.Process` — on Windows the default start method is `spawn`, so the fixture must be import-safe (it currently is, being module-level in conftest) and pickling of `_httpd` across spawn needs verification.

**CI configuration (`.github/workflows/ci.yaml`):**

- Jobs: `direct` (matrix: ubuntu/macos x CPython 3.9-3.15-dev; `python setup.py build`; `PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*) pytest`), `system` (FreeBSD 15.1 / NetBSD 11.0 via cross-platform-actions, `MAKE=gmake`, `PYSAM_FIX_CFLAGS=1`), `sdist`, `conda` (ubuntu, `HTSLIB_CONFIGURE_OPTIONS="--disable-libcurl"`).
- External samtools/bcftools/tabix binaries are installed on runners and several tests compare against them — a Windows job must either install them or skip those tests.
- **No Windows runner anywhere in CI.** `release.yaml` builds wheels for macOS (arm/intel) and manylinux/musllinux x86_64/aarch64 only; cibuildwheel config in `pyproject.toml` has no `CIBW_WINDOWS` settings.
- Tests are run from the built tree in CI (`PYTHONPATH=build/lib.*`), not from an installed wheel (the sdist job installs then runs `pytest`).

## Common Patterns

**Error testing:**

```python
def testFailingSamtools(self):
    with pytest.raises(pysam.SamtoolsError):
        pysam.samtools.view("nonexistent.bam")

def testEmptyIndex(self):
    with pytest.raises(IOError):
        pysam.samtools.index("exdoesntexist.bam")
```

(`tests/samtools_test.py:278-284, 264-266`)

**Conditional module-level skip:**

```python
NO_PYXIMPORT = False
try:
    import pyximport
    pyximport.install(build_in_temp=False)
    import _compile_test
except Exception:
    NO_PYXIMPORT = True

@pytest.mark.skipif(NO_PYXIMPORT, reason="no pyximport")
```

(`tests/compile_test.py:23-47`)

**Reusable test class via inheritance:**

```python
class TestPysam(TestSamtools):
    module = pysam
```

(`tests/samtools_test.py:332-339` — changes only the module under test)

**Temp-file discipline:**

- Always use pytest's `tmp_path` fixture for writable outputs; never write into `tests/pysam_data/` (it is shared, generated, and possibly read-only). Copy inputs there first (`shutil.copy(os.path.join(BAM_DATADIR, f), ...)` in `tests/samtools_test.py:148-149`).

---

*Testing analysis: 2026-09-17*
