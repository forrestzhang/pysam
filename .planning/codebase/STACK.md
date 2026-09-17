---
last_mapped_commit: 4c8486b106f36b1e1e548da5d70038d60fb95498
last_mapped_at: 2026-09-17
---
# Technology Stack

**Analysis Date:** 2026-09-17

## Languages

**Primary:**

- Python >=3.9 — high-level API in `pysam/`, tests in `tests/`, build orchestration in `setup.py`
- Cython (`.pyx`/`.pxd`, Cython 3.x) — low-level HTSlib wrapper modules `pysam/libc*.pyx`
- C — bundled `htslib/`, `samtools/`, `bcftools/` sources, `pysam/htslib_util.c`, `pysam/dynamic_libs.c`, `win32/getopt.c`

**Secondary:**

- Shell (sh/bash) — `devtools/install-prerequisites.sh`, `devtools/check-platform.sh`
- reStructuredText — docs in `doc/`, `README.rst`, `INSTALL`
- YAML — `.github/workflows/ci.yaml`, `.github/workflows/release.yaml`

## Runtime

**Environment:**

- CPython 3.9 through 3.15 (CI tests `3.9`–`3.15-dev`; `pyproject.toml` declares `requires-python = ">=3.9"`)
- No third-party runtime dependencies — pysam is self-contained (the only Python dependency is Cython at build time)

**Package Manager:**

- pip (sdist/wheel via setuptools)
- Lockfile: none (no `requirements.txt` for runtime; `requirements-dev.txt` contains only `Cython>=3,<4`)

## Frameworks

**Core:**

- Cython 3 (`Cython>=3,<4`) — compiles `pysam/libc*.pyx` into C extensions
- HTSlib 1.24 (bundled, `htslib/`) — C library for SAM/BAM/CRAM/VCF/BCF
- samtools 1.24 (bundled, `samtools/`) and bcftools 1.24 (bundled, `bcftools/`) — vendored as C sources with `*.pysam.c` rewrite copies

**Testing:**

- pytest (config in `setup.cfg` `[tool:pytest]`, `addopts = -s -v`, `testpaths = pysam tests`)
- mypy (type checking, `.pyi` stubs shipped for all `libc*` modules)
- flake8 (style, config in `setup.cfg`)

**Build/Dev:**

- setuptools >=59.0 with legacy backend `setuptools.build_meta:__legacy__` (`pyproject.toml`)
- cibuildwheel (wheel builds, configured in `pyproject.toml` `[tool.cibuildwheel]` and `.github/workflows/release.yaml`)
- htslib autoconf `configure` + `make` invoked from `setup.py` during builds on POSIX

## Key Dependencies

**Critical:**

- Cython >=3,<4 — required to regenerate `pysam/libc*.c` from `.pyx` (sdist ships pre-generated C files via the `cythonize_sdist` command in `setup.py`)
- zlib (`libz`) — always linked; gzip/BGZF compression
- libbz2, liblzma (xz) — optional, enabled via htslib configure
- libcurl + OpenSSL/libcrypto — optional, enables remote HTTP/S3/GCS access
- libdeflate — optional on Linux; explicitly disabled on macOS wheel builds (`CIBW_ENVIRONMENT_MACOS: HTSLIB_CONFIGURE_OPTIONS="--without-libdeflate"`)

**Infrastructure:**

- htscodecs — bundled inside `htslib/htscodecs/` (CRAM codecs)
- lz4 — bundled at `samtools/lz4/lz4.c`
- None of the C libraries are Python packages; they are system libs discovered by `htslib/configure`

## Build System Detail (relevant to Windows porting)

**Entry points:**

- `pyproject.toml` — PEP 517 metadata; `build-system.requires = ["setuptools>=59.0", "Cython>=3,<4"]`
- `setup.py` — all build logic lives here (807 lines)

**C extension configuration:**

- 16 extension modules defined in the `modules` list in `setup.py` (lines ~699–755): `pysam.libchtslib`, `libcsamtools`, `libcbcftools`, `libcutils`, `libcalignedsegment`, `libcalignmentfile`, `libcsamfile`, `libctabix`, `libcfaidx`, `libcbcf`, `libcbgzf`, `libctabixproxies`, `libcvcf`
- Custom `CyExtension` (adds `init_func`/`prebuild_func` hooks) and `cy_build_ext` (customizes macOS install names, adds `-Wl,-rpath,$ORIGIN` on Linux, runs C99 probe, symbol-collision check via `nm`)

**HTSLIB link modes** (env var `HTSLIB_MODE`, default `shared`):

- `shared` (default) — build `libhts.a` from bundled `htslib/` via `make lib-static`, link its objects into `libchtslib`, other modules link against `libchtslib`
- `separate` — link `htslib/libhts.a` into every extension separately
- `external` — link against system-installed `libhts` via `HTSLIB_LIBRARY_DIR`/`HTSLIB_INCLUDE_DIR`
- Additional env vars: `HTSLIB_CONFIGURE_OPTIONS` (passed to `htslib/configure`; tries `--enable-libcurl` then falls back to `--disable-libcurl`), `PYSAM_PROFILE`, `PYSAM_FIX_CFLAGS`, `CIBUILDWHEEL` (adds `-g0`; on Linux + libcurl also enables `pysam/dynamic_libs.c` with `DYNAMIC_NETWORK_LIBS` to `dlopen` libcurl/libcrypto at runtime)

**Platform-specific handling in `setup.py`:**

- `IS_DARWIN` (line 46): `LDSHARED` tweak, `-dynamiclib`, `@rpath/@loader_path` install names
- Linux: `-Wl,-rpath,$ORIGIN` added to every extension (`setup.py` line 423)
- Windows branch (line 634, marked "untested"): adds `win32/` to include dirs and compiles `win32/getopt.c`; no configure/make step and no MSVC-specific flags anywhere — this is the main gap for a Windows port
- POSIX-only flags in `extra_compile_args` (lines 644–649): `-Wno-unused -Wno-strict-prototypes -Wno-sign-compare -Wno-error=declaration-after-statement` (GCC/clang only)

**Windows compatibility shims already present** (`win32/`):

- `win32/getopt.c`, `win32/getopt.h` — GNU getopt implementation
- `win32/unistd.h` — drop-in replacement mapping to `<io.h>`, defines `srandom`/`random`
- `win32/stdint.h` — portable stdint for old MSVC

**Generated files during build:**

- `pysam/config.py` (written by `setup.py` from `htslib/config.h`)
- `htslib/config.h`, `samtools/config.h`, `bcftools/config.h` (via autoconf or stubbed empty)
- `htslib/config_vars.h`, `samtools/samtools_config_vars.h` (`write_configvars_header`)

**Vendored C trees:** `htslib/`, `samtools/`, `bcftools/` are complete upstream source trees (not git submodules — no `.gitmodules`); `samtools/*.pysam.c` and `bcftools/*.pysam.c` are symbol-rewritten copies generated by `devtools/import.py`.

## Configuration

**Environment:**

- Build-time env vars (see above): `HTSLIB_MODE`, `HTSLIB_LIBRARY_DIR`, `HTSLIB_INCLUDE_DIR`, `HTSLIB_CONFIGURE_OPTIONS`, `CIBUILDWHEEL`, `PYSAM_PROFILE`, `PYSAM_FIX_CFLAGS`, `CC`/`CFLAGS`/`LDFLAGS`/`MAKE`
- No `.env` file; no runtime configuration file

**Build:**

- `pyproject.toml` — PEP 517 + cibuildwheel settings
- `setup.cfg` — `[bdist_wheel] universal = 0`, `[tool:pytest]`, `[flake8]`
- `MANIFEST.in` — sdist contents

## Platform Requirements

**Development:**

- POSIX toolchain: sh-compatible shell, autoconf-generated `htslib/configure`, GNU make, `nm`, C99 compiler (gcc/clang)
- Test-time: external `samtools`, `bcftools`, `tabix` binaries used by some tests (installed in CI; on Alpine/emulated platforms provided by `devtools/emulate-tools.py` symlinks)

**Production:**

- Classifiers list only `Operating System :: POSIX/Unix/MacOS` (`setup.py` lines 777–779) — no Windows classifier
- CI matrix (`.github/workflows/ci.yaml`): ubuntu-latest, macos-latest, plus FreeBSD 15.1 and NetBSD 11.0 via cross-platform-actions
- Wheel builds (`.github/workflows/release.yaml`): cibuildwheel on manylinux_2_28, musllinux_1_2, macOS (intel + arm); **no Windows wheel jobs**
- Published to PyPI via `pypa/gh-action-pypi-publish` (trusted publishing, `id-token: write`)

---

*Stack analysis: 2026-09-17*
