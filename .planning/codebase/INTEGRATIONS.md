---
last_mapped_commit: 4c8486b106f36b1e1e548da5d70038d60fb95498
last_mapped_at: 2026-09-17
---
# External Integrations

**Analysis Date:** 2026-09-17

pysam is a scientific file-format library, not a networked application. Its "integrations" are (a) optional system C libraries linked into the bundled htslib, and (b) subprocess dispatch to external command-line tools. There are no databases, auth providers, webhooks, or SaaS APIs.

## APIs & External Services

**Remote genomic data protocols (via htslib, optional at build time):**

- HTTP/HTTPS remote file access — htslib `hfile_libcurl.c`, enabled when built `--enable-libcurl`
- Amazon S3 — htslib `hfile_s3.c`, requires libcurl + HMAC (OpenSSL/CommonCrypto)
- Google Cloud Storage — htslib `hfile_gcs.c`, requires libcurl
  - SDK/Client: none (pure C in bundled htslib)
  - Auth/config: reads htslib's standard env vars (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`, `GCS_OAUTH_TOKEN`, `HTS_S3_HOST`, etc.); not wrapped or documented by pysam itself
  - Build detection: feature flags recorded in `pysam/config.py` (`ENABLE_S3`, `ENABLE_GCS`, `HAVE_LIBCURL`, `HAVE_HMAC`, `HAVE_COMMONCRYPTO`, ...)

**Runtime dynamic loading (Linux wheel builds only):**

- `pysam/dynamic_libs.c` + `pysam/dynamic_curl.h` + `pysam/dynamic_openssl.h` — when `CIBUILDWHEEL=1` and htslib was configured with libcurl, libcurl and libcrypto are NOT linked; they are `dlopen`ed at runtime (`libcurl.so.4`, libssl) so wheels don't hard-depend on them. `DYNAMIC_NETWORK_LIBS` macro gates this. This path is POSIX-only (`dlopen`/`dlsym`) and would need a Windows equivalent (`LoadLibrary`/`GetProcAddress`) in a Windows port.

## Data Storage

**Databases:** None — no SQL/NoSQL clients anywhere in the codebase.

**File formats (local I/O, the actual domain):**

- SAM/BAM/CRAM (alignment) — via bundled htslib
- VCF/BCF (variants) — via bundled htslib + bcftools code
- FASTA/FASTQ (`.fai` indexing) — via bundled htslib
- BED/GFF/GTF/tabix-indexed text — via bundled htslib
- BGZF-compressed streams
- All compression through zlib; optional bzip2 and xz/lzma support via `libbz2`/`liblzma`

**File Storage:** Local filesystem only. Remote access only through the htslib protocols above.

**Caching:** None at the pysam level (htslib has internal reference-cache machinery, disabled by pysam: `setup.py` runs `./configure --disable-ref-cache`).

## Authentication & Identity

**Auth Provider:** None — no user accounts, sessions, or tokens. Cloud-object-store credentials are passed through to htslib's C code via environment variables (see above); pysam does not handle them in Python.

## External Processes (subprocess integration)

**samtools / bcftools command emulation:**

- `pysam/utils.py` — `PysamDispatcher` class invokes the compiled-in samtools/bcftools C `main()` functions from Python (`pysam.samtools`, `pysam.bcftools` module-level callables)
- `devtools/emulate-tools.py` — Python script that can be symlinked as `samtools`, `bcftools`, `bgzip`, or `tabix` to emulate those CLIs (used on Alpine/BSD CI where the real binaries aren't packaged)
- Tests shell out to real `samtools`, `bcftools`, `tabix` binaries where available (installed via `devtools/install-prerequisites.sh` in CI)

**Build-time subprocess calls (`setup.py`):**

- `htslib/configure`, `make` (incl. `make -s print-config`, `make lib-static`), `nm` (symbol-collision check between extensions)

## Monitoring & Observability

**Error Tracking:** None — no Sentry/rollbar/etc.

**Logs:** Python `logging` in `setup.py` only; htslib emits to `stderr` at the C level (suppressible via `pysam.set_verbosity()`).

## CI/CD & Deployment

**Hosting:** PyPI (trusted publishing via OIDC, `pypa/gh-action-pypi-publish@release/v1`) and conda/bioconda (recipe external to this repo).

**CI Pipeline:** GitHub Actions

- `.github/workflows/ci.yaml` — push/PR matrix: Ubuntu + macOS x Python 3.9–3.15-dev; FreeBSD/NetBSD jobs via `cross-platform-actions/action@v1`; sdist build-and-test job; conda job (`devtools/environment-dev.yaml`)
- `.github/workflows/release.yaml` — cibuildwheel matrix: manylinux_2_28, musllinux_1_2, macOS (intel `macos-15-intel` / arm `macos-latest`), cp39–cp315, CIBW_ARCHS=native; no Windows targets
- `pyproject.toml [tool.cibuildwheel]` — `before-all = devtools/install-prerequisites.sh ...`, `before-build = make -C htslib distclean`, `test-command = pytest {project}/tests`

## Environment Configuration

**Required env vars:** None at runtime.

**Build-time env vars** (all optional, consumed in `setup.py`):

- `HTSLIB_MODE` — `shared` (default) | `separate` | `external`
- `HTSLIB_LIBRARY_DIR`, `HTSLIB_INCLUDE_DIR` — for external mode
- `HTSLIB_CONFIGURE_OPTIONS` — extra flags for `htslib/configure` (e.g. `--without-libdeflate` on macOS CI)
- `CIBUILDWHEEL` — set by cibuildwheel; triggers `-g0` and dynamic libcurl loading
- `PYSAM_PROFILE` — enables Cython profiling directives
- `PYSAM_FIX_CFLAGS` — controls `-isystem` rewriting (default on)
- `READTHEDOCS` — special-cased to pass `--disable-bz2` to configure
- Standard compiler vars: `CC`, `CFLAGS`, `LDFLAGS`, `CPPFLAGS`, `MAKE`

**Secrets location:** None in-repo. PyPI publishing uses OIDC (`id-token: write`), no stored tokens. Cloud-storage credentials are never handled by this codebase.

## Webhooks & Callbacks

**Incoming:** None.

**Outgoing:** None. No HTTP client code exists at the Python level.

---

*Integration audit: 2026-09-17*
