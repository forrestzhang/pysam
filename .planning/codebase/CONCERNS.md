---
last_mapped_commit: 4c8486b106f36b1e1e548da5d70038d60fb95498
last_mapped_at: 2026-09-17
---
# Codebase Concerns

**Analysis Date:** 2026-09-17

> **Context:** This audit was performed with the explicit goal of adapting pysam to build and run on Windows (MSVC / MinGW-w64). Windows-portability blockers are therefore listed first and in detail; general concerns follow.

## Windows Portability Blockers (Build)

### W1. Build system is hard-wired to autotools + GNU make

**Issue:** `setup.py` drives the bundled htslib exclusively through POSIX tooling. On Windows every one of these fails ungracefully.

- `run_configure()` (`setup.py:61-73`) executes `./configure --disable-ref-cache <option>` via `subprocess.call(..., shell=True)`. On Windows the script simply does not exist; `run_configure` catches only `OSError`, and on Windows `subprocess.call` returns a non-zero code instead, so every configure attempt "fails" and `configure_library()` (`setup.py:247-268`) returns `None`.
- `run_make_print_config()` (`setup.py:81-91`) invokes `make -s print-config` inside `htslib/`. It is called unconditionally at `setup.py:543-544` for `HTSLIB_MODE in ['shared', 'separate']`. On Windows `make` is absent → `FileNotFoundError` (an `OSError`) is raised **uncaught** at setup.py import time, aborting the entire build before any Windows fallback path can run.
- `prebuild_libchtslib()` (`setup.py:678-692`) calls `run_make(["ALL_CPPFLAGS=...", "lib-static"])` — another uncalled `make` invocation.
- `run_nm_defined_symbols()` (`setup.py:94-112`) shells out to `nm -g -P`. This one *is* handled: `cy_build_ext.run()` catches `OSError`/`CalledProcessError` and skips the symbol-conflict check with a warning (`setup.py:361-367`). It will silently do nothing on Windows.
- The `htscodecs` sub-library is built through htslib's own `htslib/htscodecs.mk` make fragment, so it inherits the same make dependency.

**Files:** `setup.py:61-91`, `setup.py:247-268`, `setup.py:543-552`, `setup.py:678-692`, `htslib/Makefile`, `htslib/configure`

**Impact:** No Windows build path exists at all; `python setup.py build` dies during setup.py module execution.

**Fix approach:** Add a Windows branch that (a) writes a pre-baked `htslib/config.h` (mingw-w64 or MSVC variant) instead of running `./configure`, (b) compiles the htslib/htscodecs source lists directly through setuptools `Extension` sources or `cl`/MinGW, and (c) skips `run_make_print_config` in favour of a hard-coded equivalent dict. The empty-`config.h` fallback at `setup.py:535-541` already hints at this pattern but is unreachable because `run_make_print_config` runs first.

### W2. Cython `posix.*` cimports in three core modules

**Issue:** Three `.pyx` modules cimport from Cython's `posix` package unconditionally:

- `pysam/libchtslib.pyx:10` — `from posix.unistd cimport dup`
- `pysam/libcutils.pyx:22-23` — `from posix.fcntl cimport open as c_open, O_WRONLY, O_CREAT, O_TRUNC` and `from posix.unistd cimport dup as c_dup, SEEK_SET, SEEK_CUR, SEEK_END, STDOUT_FILENO`
- `pysam/libctabix.pyx:62-63` — `from posix.fcntl cimport open as c_open, O_RDONLY` and `from posix.unistd cimport close, dup, read`

Cython's `posix` pxd declarations generate `#include <unistd.h>` / `#include <fcntl.h>` in the C output. MSVC has no `<unistd.h>`; the declaration signatures also target POSIX (e.g. `ssize_t read(...)`).

**Files:** `pysam/libchtslib.pyx:10`, `pysam/libcutils.pyx:22-23`, `pysam/libctabix.pyx:62-63`

**Impact:** Cythonization and/or C compilation fails on MSVC out of the box. MinGW-w64 works only because `win32/unistd.h` (a shim including `<io.h>`/`<getopt.h>` and mapping `access`→`_access`, `ftruncate`→`_chsize`, `random`→`rand`) is injected into `include_dirs` on Windows (`setup.py:632-639`).

**Fix approach:** Either (a) target MinGW-w64 only and keep the shim, extending `win32/unistd.h` with the missing `isatty`/`fileno` mappings (see W4), or (b) for MSVC, replace the `posix.*` cimports with `libc.msvcrt`/`libc.io` equivalents (`_open`, `_dup`, `_read`, `_close`) behind a `DEF`/`IF` compile-time platform switch in each `.pyx`.

### W3. Hardcoded `/dev/null` in the samtools/bcftools dispatcher

**Issue:** `_pysam_dispatch()` in `pysam/libcutils.pyx` opens the literal path `b"/dev/null"` twice:

- `pysam/libcutils.pyx:383` — `stdout_h = c_open(b"/dev/null", O_WRONLY)` after pushing a `-o <file>` output option
- `pysam/libcutils.pyx:390` — `stdout_h = c_open(b"/dev/null", O_WRONLY)` when `catch_stdout` is falsy

**Impact:** On Windows `open("/dev/null")` fails → `OSError_from_errno` is raised whenever a samtools/bcftools subcommand is dispatched without stdout capture.

**Fix approach:** Use `os.devnull` (already imported `os` at `pysam/libcutils.pyx:7`) wrapped in `force_bytes()`, e.g. `c_open(force_bytes(os.devnull), O_WRONLY)`.

### W4. Bundled samtools/bcftools C sources use POSIX tty/file APIs

**Issue:** The vendored (regex-rewritten) samtools/bcftools sources call `isatty(fileno(stdin))` at:

- `bcftools/consensus.c:1336` / `consensus.c.pysam.c:1338`
- `bcftools/csq.c:4063` / `csq.c.pysam.c:4065`
- `bcftools/reheader.c:727` / `reheader.c.pysam.c:729`
- `bcftools/vcfannotate.c:4054` / `vcfannotate.c.pysam.c:4056`
- `bcftools/vcfcall.c:1168` / `vcfcall.c.pysam.c:1170`

MSVC provides only `_isatty`/`_fileno`; MinGW provides the POSIX names. The `win32/unistd.h` shim does **not** map `isatty`/`fileno`.

**Files:** `bcftools/*.pysam.c`, `win32/unistd.h`

**Impact:** MSVC build fails at compile time for those translation units; even if it compiled, the stdin-tty detection used by several bcftools subcommands would misbehave.

**Fix approach:** Extend `win32/unistd.h` with `#define isatty _isatty` and `#define fileno _fileno` (guarded for MSVC only) or patch `devtools/import.py` to add these mappings when generating `.pysam.c` files.

### W5. GNU linker flag applied on all non-Darwin platforms

**Issue:** `cy_build_ext.build_extension()` appends `-Wl,-rpath,$ORIGIN` to `extra_link_args` for every non-Darwin platform (`setup.py:419-423`). The branch condition is `if sys.platform == 'darwin': ... else:`, so Windows is included.

**Impact:** MSVC `link.exe` rejects `-Wl,...` outright; even MinGW needs `$ORIGIN` (which stays literal inside a Python list — unlike in a shell, it is not expanded, so this happens to work on Linux but is fragile).

**Fix approach:** Add an explicit `elif sys.platform == 'win32':` branch that adds no rpath (DLL resolution on Windows relies on the loading directory anyway) and keep `$ORIGIN` only for Linux/POSIX. When adding Windows CI, quote/escape `$ORIGIN` review.

### W6. htslib configure fallbacks probe libcurl, unusable on Windows

**Issue:** `setup.py:525-529` tries `"--enable-libcurl"` then `"--disable-libcurl"` via `./configure`. The resulting `external_htslib_libraries` is parsed from `make print-config` output (`setup.py:543-552`), and dynamic libcurl/libcrypto loading (`pysam/dynamic_libs.c`, `pysam/dynamic_curl.h`, `pysam/dynamic_openssl.h`) is enabled only when `sys.platform == "linux" and for_redistribution` (`setup.py:559-563`).

**Files:** `setup.py:525-563`, `pysam/dynamic_libs.c`

**Impact:** Windows feature parity: no remote (http/S3/GCS) file support is possible through the current build logic even after a successful local build, because the dynamic-loading path (`dlopen`/`dlsym` via `dlfcn.h`, hardcoded `libcurl.so.4` and `libcrypto.so.{4,3,1.1}` sonames — `pysam/dynamic_libs.c:31,112-114`) is Linux-only by design. On Windows, htslib would need to link libcurl statically or via LoadLibrary with `.dll` names.

**Fix approach:** Decide explicitly: for a first Windows port, ship with `--disable-libcurl` (no remote URLs) and document it. Later, add a Windows variant of `dynamic_libs.c` using `LoadLibraryA`/`GetProcAddress` and `libcurl*.dll` names.

### W7. Stale, untested MSVC-era shims

**Issue:** The `win32/` directory dates from a 2013 MSVC 2008 effort (commits `09269db9`, `943142c6`, `5a7b2544`, `b0cf206d`, `6cd18113`; issue #190). `setup.py:633` literally comments `# Windows compatibility - untested`. Contents:

- `win32/unistd.h` — minimal shim, missing `isatty`, `fileno`, `sleep`, `getpid`.
- `win32/getopt.c`/`win32/getopt.h` — vendored getopt_long implementation, still needed by the bundled samtools/bcftools main loops (`samtools/samtools.pysam.c:1` includes `<getopt.h>`).
- `win32/stdint.h` — obsolete since MSVC 2010 (which ships a conforming `stdint.h`); including a 27 KB outdated copy risks shadowing the system header.

**Files:** `win32/`, `setup.py:632-649`, `samtools/samtools.pysam.c:1-3`, `bcftools/bcftools.pysam.c:1-3`

**Impact:** The shims have bit-rotted; nothing since ~2013 has validated them and the build machinery around them (configure/make) was added later, erasing the old code path entirely.

**Fix approach:** For MSVC drop `win32/stdint.h`; keep `win32/getopt.c`; expand `win32/unistd.h` or replace with per-file `_WIN32` guards. Prefer MinGW-w64 as the first-class Windows toolchain because GCC flags, `unistd.h`, and htslib's own MSYS2 support all align.

### W8. No Windows CI, no Windows wheels

**Issue:**

- `.github/workflows/ci.yaml:12` matrix is `os: [ubuntu, macos]` (plus FreeBSD/NetBSD VMs); no `windows` runner.
- `.github/workflows/release.yaml:17-21` builds wheels for `kind: [macos, many, musl]` only — **no `win` matrix entries**, so no Windows wheels are published to PyPI.
- `pyproject.toml:24-30` `[tool.cibuildwheel]` `before-all` runs the shell script `devtools/install-prerequisites.sh`, which is POSIX-only, and `before-build` runs `make -C htslib distclean` — both fail on a Windows runner.
- Packaging metadata declares no Windows support: `setup.py:777-780` classifiers `Operating System :: POSIX/Unix/MacOS`, `setup.py:791` `platforms: ["POSIX", "UNIX", "MacOS"]`.

**Files:** `.github/workflows/ci.yaml`, `.github/workflows/release.yaml`, `pyproject.toml`, `setup.py:770-791`, `devtools/install-prerequisites.sh`

**Impact:** Windows users must use WSL, MSYS2, or unofficial wheels; regressions for the (partial) Windows support are invisible.

**Fix approach:** After W1-W5 land, add `kind: win` + `arch` matrix rows with `CIBW_BUILD: cp3x-win_amd64` and a `CIBW_BEFORE_BUILD_WINDOWS`/before-all that invokes a Python-based prerequisite installer. Update classifiers/platforms.

### W9. POSIX-isms in the test suite

**Issue:** Many tests shell out to Unix tools or assume POSIX semantics:

- `tests/AlignmentFileFetchTestUtils.py:9,28,55` and `tests/PileupTestUtils.py:9,29,54` — `os.popen`/`os.system` pipelines using `samtools`, `wc`, `cut`, `awk`, and `2> /dev/null` / `> /dev/null` redirection (cmd.exe incompatible).
- `tests/AlignmentFile_bench.py:11` — `os.system("samtools view {} | wc -l > /dev/null")`.
- `tests/StreamFiledescriptors_test.py:46` — `subprocess.Popen('head -n200', ..., shell=True)`.
- `tests/linking_test.py:70` — `export LD_LIBRARY_PATH=...:$PATH` in a `bash -c` string.
- `tests/conftest.py:53` — `os.environ["REF_PATH"] = ":"`; htslib uses `;` as the path-list separator on Windows, so this override breaks reference lookups there.
- `tests/samtools_test.py:28` — checks `if retcode < 0` and prints "Child was terminated by signal" — POSIX-only signal exit semantics (Windows uses positive exit codes).

**Files:** `tests/AlignmentFileFetchTestUtils.py`, `tests/PileupTestUtils.py`, `tests/AlignmentFile_bench.py`, `tests/StreamFiledescriptors_test.py`, `tests/linking_test.py`, `tests/conftest.py`, `tests/samtools_test.py`

**Impact:** Even after a successful Windows build, a large fraction of the comparison tests cannot run unmodified.

**Fix approach:** Replace shell pipelines with `pysam.samtools.view(...)` invocations and pure-Python counting (the utilities already exist in `pysam/utils.py`). Parameterise the REF_PATH separator on `os.name`. Skip/replace `linking_test.py` with a `ctypes`-based load check on Windows.

### W10. `fdopen` in the C dispatch shim

**Issue:** `import/pysam.c` (template that becomes `samtools/samtools.pysam.c` and `bcftools/bcftools.pysam.c`) uses `fdopen(fd, "w")` at lines 19, 33. MSVC names this `_fdopen` (declared in `<stdio.h>` when legacy POSIX names are enabled).

**Files:** `import/pysam.c:19`, `import/pysam.c:33`

**Impact:** Compile warning/error under MSVC unless legacy names are on; MinGW unaffected.

**Fix approach:** `#ifdef _MSC_VER #define fdopen _fdopen` in `import/pysam.c` or the win32 shim.

## Tech Debt

**Monolithic build script (general):**

- Issue: `setup.py` (807 lines) mixes metadata, configure/make orchestration, compiler-flag surgery, macOS rpath handling, and config-header generation. It depends on the deprecated `python setup.py build/install` entry point (used in `.github/workflows/ci.yaml:44,212` and `pyproject.toml:22` legacy backend).
- Files: `setup.py`, `pyproject.toml:20-30`
- Impact: Any platform work (Windows included) must untangle this single file; PEP 517 front-ends get the legacy backend.
- Fix approach: Incrementally factor platform branches (`setup.py:632-649`, `setup.py:356-358`, `setup.py:401-423`) into helpers; consider moving htslib compilation to a static source list.

**Hardcoded shared-library sonames in dynamic loader:**

- Issue: `pysam/dynamic_libs.c` hardcodes `libcurl.so.4` (`line 31`) and `libcrypto.so.{4,3,1.1}` (`lines 112-114`); nothing probes for newer sonames.
- Files: `pysam/dynamic_libs.c`
- Impact: Will silently break on distros shipping libcurl.so.5 / libcrypto.so.4-only systems age out; error is only a runtime log.
- Fix approach: Iterate over a version list or use `ldconfig -p` at build time.

**sdist workarounds for setuptools:**

- Issue: `cythonize_sdist` manually injects `owner=`/`group=` sdist options because "setuptools (as installed on GH runners)" lacks them (`setup.py:284-289`).
- Files: `setup.py:284-294`
- Impact: Fragile against setuptools changes; build-time divergence between environments.
- Fix approach: Drop once minimum setuptools catches up; track with a comment/issue.

**Dead/obsolete files:**

- Issue: `pysam/VCF.py.obsolete` and `pysam/alternatives.py.obsolete` are kept in-tree; `MANIFEST.in:12` includes `KNOWN_BUGS`, which does not exist in the repo.
- Files: `pysam/VCF.py.obsolete`, `pysam/alternatives.py.obsolete`, `MANIFEST.in`
- Impact: Confuses new contributors and file-classification tooling.
- Fix approach: Delete `.obsolete` files and the `KNOWN_BUGS` include line.

**Symbol-conflict checking silently disabled on non-GNU platforms:**

- Issue: `check_ext_symbol_conflicts` depends on `nm -g -P`; failure is demoted to a warning (`setup.py:361-367`), so on Windows/macOS-BSD toolchains the check never runs.
- Files: `setup.py:320-337`, `setup.py:361-367`
- Impact: A real class of crash (duplicate non-static symbols across extension modules — the reason for the `#define`s in `import/pysam.h:63-73`) goes undetected.
- Fix approach: After a Windows port, replace `nm` with `dumpbin /symbols` (MSVC) or lld-compatible parsing.

**Source-rewriting pipeline fragility:**

- Issue: `devtools/import.py` regenerates `*.pysam.c` from upstream samtools/bcftools sources via regex substitutions (e.g. `devtools/import.py:90-102` rewriting `int main(`, `exit(`, `stdout`, `printf(`). Any upstream C source that trips these regexes introduces subtle runtime corruption.
- Files: `devtools/import.py`, `samtools/*.pysam.c`, `bcftools/*.pysam.c`
- Impact: Version bumps of bundled htslib/samtools/bcftools require manual verification of every rewrite; the regexes are not anchored and have already needed file-specific fixes (`devtools/import.py:106-120`).
- Fix approach: Keep the file-specific substitution table versioned per upstream release; add a post-import smoke test that dispatches each samtools subcommand.

## Known Bugs

**`StreamFiledescriptors_test.test_samtools_processing` hangs:**

- Symptoms: Test suite hangs when this test runs; marked `@pytest.mark.skip("test contains bug")`.
- Files: `tests/StreamFiledescriptors_test.py:63-84`
- Trigger: Running the skipped test.
- Workaround: Permanently skipped; indicates an unresolved interaction between fd-passing, htslib's stdout switching, and subprocess pipes — exactly the area that needs rework for Windows anyway (W2/W3).

**Crash on invalid accesses in pileup:**

- Symptoms: Segfault on Python 3.11 and NetBSD.
- Files: `tests/AlignmentFilePileup_test.py:178` (skip reason)
- Trigger: "exercises invalid accesses" test case.
- Workaround: Test skipped; underlying C-level bounds issue in `pysam/libcalignmentfile.pyx` pileup path presumed unresolved.

## Security Considerations

**`shell=True` with environment-controlled configure options:**

- Risk: `run_configure` joins `HTSLIB_CONFIGURE_OPTIONS` into a shell string (`setup.py:65-67`). In a build-farm scenario a crafted env var could inject shell commands.
- Files: `setup.py:61-73`
- Current mitigation: None; env var is trusted.
- Recommendations: Pass the option as a single argv element without `shell=True` (configure scripts accept `--opt=value` as one argument).

**Vendored C dependencies:**

- Risk: htslib/samtools/bcftools/htscodecs snapshots bundled in-tree inherit upstream CVEs until re-imported. The vendored `win32/getopt.c` (41 KB, from pwilson.net per `win32/unistd.h:11`) is an old third-party implementation — getopt parsers are a historic source of overflows.
- Files: `htslib/`, `samtools/`, `bcftools/`, `win32/getopt.c`
- Current mitigation: Versions tracked via `devtools/import.py`; `pysam/version.py` pins `__samtools_version__`.
- Recommendations: Document the bundled version map per release; consider replacing `win32/getopt.c` with a maintained implementation during the Windows port.

## Performance Bottlenecks

Not Windows-specific and moderate: builds re-run `./configure` for htslib on every invocation when `libhts.a` is missing, and the symbol-conflict check runs `nm` over every extension module serially (`setup.py:320-337`). Cythonization of the 14 `libc*.pyx` modules dominates sdist/build time; no caching layer beyond Cython's own. Runtime performance concerns were not flagged by this audit.

## Fragile Areas

**`_pysam_dispatch` stdout/stderr redirection:**

- Files: `pysam/libcutils.pyx:300-464`
- Why fragile: Coordinates Python `tempfile.mkstemp`, raw `c_open`, fd-level `samtools_set_stdout(fd)`, and C `fdopen` across two compiled codebases. Any fd leak (e.g. when `samtools_dispatch` longjmps — see `samtools/samtools.pysam.c:57` `jmp_buf`) leaks temp files. Hardcoded `/dev/null` (W3) lives here.
- Safe modification: Always pair `c_open` failures with `os.close(stdout_h)`; add a Windows abstraction for devnull; run the full `tests/samtools_test.py` suite after any change.

**Bundled-source import process:**

- Files: `devtools/import.py`, `import/pysam.h`, `import/pysam.c`
- Why fragile: See "Source-rewriting pipeline fragility" above; additionally `import/pysam.h:63-73` requires hand-maintained `#define` symbol prefixes for every colliding symbol between samtools and bcftools, discovered only at link/load time.
- Safe modification: Regenerate all `*.pysam.c` files via `python devtools/import.py` after touching the templates; rely on `check_ext_symbol_conflicts` (when `nm` is available).

**`pysam/config.py` generation:**

- Files: `setup.py:597-620`
- Why fragile: Regex-parses `htslib/config.h` at build time (`#define (\S+)\s+(\S+)`); assumes all `HAVE_*`/`ENABLE_*` keys exist, defaulting missing ones via `collections.defaultdict(int)` — silently reporting `0` for features that may actually be enabled.
- Safe modification: Verify against `htslib/config.h` contents when changing configure options.

## Scaling Limits

Not applicable in the server sense; pysam is a library. The relevant limit is htslib's `threads` model (per-file thread pools), which is platform-independent. Windows-specific scaling limits are unknown until W1-W8 land.

## Dependencies at Risk

**Cython 3.x pin:**

- Risk: `pyproject.toml:21` requires `Cython>=3,<4`; the `posix.*` cimports (W2) and `.pyi` stub generation depend on Cython's pxd layout, which Cython 4 may reorganise.
- Impact: Cython 4 release could break the build until cimports are updated.
- Migration plan: When Cython 4 lands, audit `pysam/libc*.pyx` cimports against the new pxd layout as part of the Windows `posix` cleanup (W2).

**setuptools legacy backend:**

- Risk: `pyproject.toml:22` uses `setuptools.build_meta:__legacy__` because `setup.py` still calls `setup()` under `if __name__ == '__main__'` (`setup.py:805-806`).
- Impact: Increasing divergence from modern PEP 517 behaviour; cibuildwheel already warns.
- Migration plan: Remove the `__main__` guard pattern / move metadata fully into `setup.cfg`/pyproject.

**Vendored getopt:**

- Risk: Ancient `win32/getopt.c` (see Security Considerations).
- Impact: Compiler warnings and potential parsing bugs for long options on Windows.
- Migration plan: Replace with a minimal maintained getopt_long or define `PYSAM_NO_GETOPT` paths — low priority since only build-time CLI parsing in bundled tools uses it.

## Missing Critical Features

**Windows wheels:**

- Problem: No PyPI wheels for Windows exist; `release.yaml` has no `win` build jobs (W8).
- Blocks: Windows adoption; forces users onto WSL/MSYS2/conda-forge. Note bioconda (the recommended channel in `INSTALL:9`) does not ship Windows binaries, so there is no supported Windows install path at all.

**Remote-file support on Windows:**

- Problem: libcurl/openssl dynamic loading is Linux-only (`setup.py:559-563`, `pysam/dynamic_libs.c`); htslib network (`s3://`, `gs://`, `http://`) is unavailable in any Windows build.
- Blocks: Parity with Linux/macOS wheels for cloud genomics workflows.

**Windows build documentation:**

- Problem: No mention of Windows anywhere in `INSTALL`, `README.rst`, or `doc/installation.rst` (only hit in whole `doc/` is a Sphinx favicon comment in `doc/conf.py:176`).
- Blocks: Contributors cannot discover the (partial) `win32/` support or its requirements.

## Test Coverage Gaps

**Windows CI coverage:**

- What's not tested: Everything. No Windows runner in `ci.yaml`; zero automated validation of the `win32/` shims since 2013.
- Files: `.github/workflows/ci.yaml`, `win32/`
- Risk: The Windows port described in W1-W10 has no safety net; regressions guaranteed without CI.
- Priority: High — add a `windows-latest` job as soon as the build succeeds once.

**Symbol-conflict detection on Windows:**

- What's not tested: `check_ext_symbol_conflicts` never runs where `nm` is missing (see Tech Debt).
- Files: `setup.py:320-367`
- Risk: Duplicate C symbols between `libcsamtools` and `libcbcftools` extensions cause wrong-function crashes that appear only at runtime.
- Priority: Medium.

**Dispatcher error paths without stdout capture:**

- What's not tested: The `/dev/null` branch of `_pysam_dispatch` (`pysam/libcutils.pyx:390`) — exercised only when callers pass `catch_stdout=False`; Windows failure of that branch (W3) would go unnoticed.
- Files: `pysam/libcutils.pyx:379-390`, `pysam/utils.py:59-103`
- Risk: `pysam.samtools.*` calls that stream to the real stdout break on Windows silently.
- Priority: High for the port.

**External-tool comparison tests:**

- What's not tested on Windows: All shell-pipeline-based fetch/pileup comparisons (W9) are unrunnable; equivalently the skipped `test_samtools_processing` fd test (`tests/StreamFiledescriptors_test.py:63`).
- Files: `tests/AlignmentFileFetchTestUtils.py`, `tests/PileupTestUtils.py`, `tests/StreamFiledescriptors_test.py`
- Risk: Core streaming behaviours lack any Windows-compatible test oracle.
- Priority: Medium — replace pipelines with in-process pysam equivalents.

---

*Concerns audit: 2026-09-17*
