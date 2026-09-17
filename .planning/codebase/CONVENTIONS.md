---
last_mapped_commit: 4c8486b106f36b1e1e548da5d70038d60fb95498
last_mapped_at: 2026-09-17
---
# Coding Conventions

**Analysis Date:** 2026-09-17

## Naming Patterns

**Files (Python tests):**

- Test modules are named `<Component>_test.py` (suffix style): `tests/AlignmentFile_test.py`, `tests/VariantFile_test.py`, `tests/samtools_test.py`, `tests/tabix_test.py`.
- Benchmark modules use `_bench.py` suffix: `tests/AlignedSegment_bench.py`, `tests/AlignmentFile_bench.py`, `tests/tabix_bench.py`.
- Shared test helpers use `CamelCase.py` (no `_test` suffix, so pytest does not collect them): `tests/TestUtils.py`, `tests/PileupTestUtils.py`, `tests/AlignmentFileFetchTestUtils.py`, `tests/VariantFileFetchTestUtils.py`.
- Cython modules in `pysam/` follow the `lib<component>.pyx` / `lib<component>.pxd` / `lib<component>.pyi` triplet pattern: `pysam/libchtslib.pyx`, `pysam/libcalignmentfile.pyx`, `pysam/libcbcf.pyx`.

**Files (Cython):**

- `.pyx` implementation, `.pxd` declarations, `.pyi` type stubs are kept adjacent with identical basenames.
- C support files are lowercase with underscores: `pysam/htslib_util.c`, `pysam/dynamic_libs.c`.

**Functions:**

- Python test methods historically use mixedCase (`testARqname`, `testFetchAll`), newer code uses snake_case (`test_remote_S3`, `test_fetch_with_region_is_equivalent`). Match the surrounding class.
- Helper functions are snake_case: `check_binary_equal` would be; existing helpers are `checkBinaryEqual`, `checkGZBinaryEqual`, `force_str`, `force_bytes`, `make_data_files` (mixed legacy styles — keep the existing name when editing, use snake_case for new code).

**Classes:**

- Test classes use `Test` prefix: `class TestBAMFromFetch:` in `tests/AlignmentFile_test.py`, `class TestSamtools:` in `tests/samtools_test.py`.
- Exception classes use CamelCase: `pysam.SamtoolsError` in `pysam/utils.py`.

**Variables:**

- snake_case throughout (`tests/TestUtils.py`: `BAM_DATADIR`, `TABIX_DATADIR` are module-level constants in ALL_CAPS).
- Module-level data directory constants are ALL_CAPS: `BAM_DATADIR`, `TABIX_DATADIR`, `CBCF_DATADIR`, `LINKDIR` in `tests/TestUtils.py`.

## Code Style

**Formatting:**

- No automated formatter (no black/ruff config). Style is hand-maintained.
- flake8 is the lint authority. Config in `setup.cfg`:
  - `max-line-length = 120`
  - `max-complexity = 23`
  - Ignored: E124, E128, E203, E221, E272, E701, E741, F405
  - Per-file: `__init__.py: F401,F403` (star imports allowed in `__init__.py`); `tests/typechecking_test.py: F821,F841`; `tests/*.py: B007,F841`
- 4-space indent, single quotes in older code, double quotes common in newer code — not enforced.

**Linting:**

- Run flake8 with `setup.cfg` config. There is no lint gate in CI (`ci.yaml` does not run flake8), so lint compliance is best-effort.

**Type Checking:**

- mypy is installed in CI and exercised through `tests/typechecking_test.py` (which invokes `mypy.api` programmatically and skips at module level if mypy is unavailable: `pytest.skip('mypy API not available', allow_module_level=True)`).
- Stub files (`.pyi`) are maintained by hand alongside each `.pyx`: `pysam/libcalignedsegment.pyi`, `pysam/libchtslib.pyi`, etc.
- Runtime type introspection tests live in `tests/typechecking_test.py` (uses `typing.TYPE_CHECKING` and inspects dispatcher types).
- There is no `mypy.ini`/`[mypy]` section; checks rely on defaults plus per-file flake8 ignores.

## Import Organization

**Order (observed in `tests/samtools_test.py`, `tests/AlignmentFile_test.py`):**

1. Standard library (`os`, `sys`, `subprocess`, `warnings`, `glob`)
2. Third-party (`pytest`)
3. `pysam` and `pysam.samtools` / `pysam.bcftools`
4. Test helpers via `from TestUtils import ...` — note: tests run with the `tests/` directory on `sys.path` (pytest rootdir behavior plus `testpaths = pysam tests` in `setup.cfg`), so helpers are imported as top-level modules (`import TestUtils`, `from TestUtils import BAM_DATADIR`), NOT `from tests.TestUtils import ...`.

**Path Aliases:**

- None. No `src/` layout; `pysam/` is imported directly from the repo root (CI sets `PYTHONPATH=$GITHUB_WORKSPACE/build/lib.*` after `python setup.py build`).

**Star imports:**

- Permitted and idiomatic in `pysam/__init__.py`, which re-exports the full public API from all `lib*.pyx` modules via `from pysam.libchtslib import *` etc., combined into a single `__all__` tuple (`pysam/__init__.py`).
- Star imports from `pysam.libc*` are accepted practice for consumers too (`from pysam import *`).

## Error Handling

**Patterns:**

- Exception-based, never return codes. Custom exception `pysam.SamtoolsError` (defined in `pysam/utils.py`) is raised when samtools/bcftools exits non-zero; test pattern: `with pytest.raises(pysam.SamtoolsError): pysam.samtools.view("nonexistent.bam")` (`tests/samtools_test.py`).
- `IOError` (aliased to `OSError` on py3) used for missing input files: `with pytest.raises(IOError): pysam.samtools.index("exdoesntexist.bam")` (`tests/samtools_test.py`).
- Cython layer raises Python exceptions via `raise ValueError(...)`, `raise OSError(errno, message)` etc. inside `.pyx` files; do not return error codes across the Cython boundary.
- EAFP style throughout: `try: return s.decode('ascii') except AttributeError: return s` (`tests/TestUtils.py` `force_str`/`force_bytes`).

**Assertions in tests:**

- Plain `assert` statements (pytest rewrites them). No `unittest.TestCase` (no `self.assertEqual`), though `setup_method`/`teardown_method`/`setUpModule` xunit-style hooks are used alongside pytest fixtures.

## Logging

**Framework:** `logging` module in library code (`tests/AlignmentFile_test.py` imports `logging`; `pysam/` dispatcher code collects stderr into `self.stderr` lists).

**Patterns:**

- The `PysamDispatcher` class in `pysam/utils.py` captures subprocess stderr per-call into `self.stderr` rather than printing.
- Tests use `print()` freely because pytest runs with `-s` (stdout capture disabled — see `setup.cfg` addopts), which is required because `pysam.dispatch` manipulates file descriptors 1/2.

## Comments

**When to Comment:**

- Comment blocks explain *why*, frequently citing external issues: `# Work around actions/runner-images#14568` (`tests/conftest.py`), `# Necessary until we build libhts.a out-of-tree from within build_temp` (`pyproject.toml`).
- Disabled tests keep an explanatory comment: `# TODO: fixmate behaviour changed in 1.21` (`tests/samtools_test.py`), `# test contains bug` (`tests/StreamFiledescriptors_test.py`).
- Module/class docstrings are prevalent and reStructuredText-style (`:class:`pysam.SamtoolsError``).

**Docstrings:**

- Triple-single-quote `'''...'''` docstrings are the dominant style in tests (`tests/TestUtils.py`) and `pysam/utils.py`, though double quotes also appear.

## Function Design

**Size:** Test methods are short; module-level helper functions in `tests/TestUtils.py` are kept small and single-purpose.

**Parameters:** Keyword args used for optional behavior (`check_samtools_view_equal(filename1, filename2, without_header=False)`). Dispatcher methods take `*args: str, **kwargs`.

**Return Values:** Helpers return booleans for comparisons (`checkBinaryEqual`) or lists (`slurp_file`). Dispatcher calls return `str`/`bytes`/`list` depending on parser (tested in `TestReturnType`, `tests/samtools_test.py`).

## Module Design

**Exports:**

- `pysam/__init__.py` aggregates `__all__` from every compiled sub-module; each `lib*.pyx` defines its own `__all__`.
- `pysam/config.py` (generated by `setup.py`) exposes build-time feature flags (`HAVE_LIBCURL`, `ENABLE_GCS`, `ENABLE_S3`, `HAVE_LIBBZ2`, etc.). Tests gate on these with `getattr(pysam.config, "HAVE_LIBCURL", 0)` — always use `getattr` with a default of `0` because the attribute may be absent in some build configurations.

**Barrel Files:**

- `pysam/__init__.py` is the single barrel for the public API. `tests/` has no barrel; helpers imported by explicit module name.

## Platform-Specific Conventions (Windows-port relevant)

- **Build-time platform handling lives in `setup.py`**, not in the Python package:
  - `IS_DARWIN = platform.system() == 'Darwin'` (line 46)
  - `if sys.platform == 'darwin':` blocks (lines 356, 401)
  - `if sys.platform == "linux" and "curl" in external_htslib_libraries and for_redistribution:` (line 559)
  - **Windows branch (marked "untested", line 633-636):** `if platform.system() == 'Windows': include_os = ['win32']; os_c_files = ['win32/getopt.c']` — MSVC does not get the `-Wno-*` GCC flags that POSIX builds receive (lines 644-649).
- **Shim headers for Windows** live in `win32/`: `win32/getopt.c`, `win32/getopt.h`, `win32/stdint.h`, `win32/unistd.h`.
- **No Windows handling exists anywhere in `pysam/` Python/Cython code or in `tests/`** — there are zero `sys.platform == 'win32'` checks in the test suite.
- Existing platform skips in tests use this idiom: `@pytest.mark.skipif(sys.platform.startswith("netbsd"), reason="exercises invalid accesses, crashing on NetBSD")` (`tests/AlignmentFilePileup_test.py`) and `@pytest.mark.skipif(sys.version_info[:2] == (3, 11) or ...)` — follow this pattern for Windows skips, preferring `sys.platform.startswith("win")` or feature detection over `os.name`.
- Tests frequently shell out to POSIX tools (`head`, `awk`, `samtools mpileup ... 2> /dev/null`) via `subprocess.Popen(..., shell=True)` or `os.system` — see `tests/StreamFiledescriptors_test.py`, `tests/PileupTestUtils.py`, `tests/AlignmentFileFetchTestUtils.py`, `tests/samtools_test.py`. These will need guarding or replacement for Windows.
- `tests/pysam_data/Makefile`, `tests/tabix_data/Makefile`, `tests/cbcf_data/Makefile` generate test data using `samtools`, `gzip`, and shell pipes; generation is orchestrated by `make_data_files()` in `tests/TestUtils.py` which invokes `$MAKE -C <directory>` with a lock directory (`all.lock`) and an `all.stamp` sentinel.

---

*Convention analysis: 2026-09-17*
