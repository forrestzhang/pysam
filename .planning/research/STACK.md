# Stack Research

**Domain:** Porting pysam (Cython/C extensions wrapping bundled htslib/samtools/bcftools) to Windows with distributable wheels
**Researched:** 2026-09-17
**Confidence:** MEDIUM-HIGH (version facts verified against official pages fetched directly; toolchain strategy cross-checked across multiple ecosystem sources)

## Context

This research answers: what is the standard 2025-2026 toolchain for building Python C extensions with bundled autotools-based C libraries on Windows, for both MinGW-w64 (MSYS2) and MSVC? It builds on `.planning/codebase/STACK.md` and `CONCERNS.md` (existing build is autotools/make-driven, GCC-only flags, `posix.*` cimports, no Windows CI). Key facts that shape every recommendation below:

- htslib **officially documents MSYS2/MinGW-w64 as its Windows build path** (`./configure && make` inside the MSYS2 MinGW x64 shell). MSVC is unverified upstream, and the vcpkg htslib port is explicitly `!windows`. (HIGH — htslib INSTALL)
- MSYS2 ships a current `mingw-w64-ucrt-x86_64-htslib` **1.24-1** package (built 2026-07-13) with full deps: zlib, bzip2, xz, curl, openssl, libdeflate — proof that htslib's complete feature set (including libcurl remote access) compiles under MinGW-w64 right now. (HIGH — packages.msys2.org)
- python.org CPython (3.5+) links the **UCRT**. Only the MSYS2 **UCRT64** toolchain targets the same CRT, which makes fd/`FILE*`/`errno` passing between htslib and CPython safe. The legacy `mingw64` MSYS2 environment (msvcrt) must not be mixed with python.org Python. (MEDIUM — cross-checked: Python wiki, MSYS2 docs, Ziggit ABI discussion)
- cibuildwheel **4.2.1** (2026-09-05) is current; since 4.0.0 `delvewheel` is the **default Windows repair command**, so MinGW runtime DLLs get bundled automatically. delvewheel is at **1.13.1**. (HIGH — PyPI)
- Extension modules on Windows do **not** link `python3x.lib`; Python symbols resolve at import time. Therefore a UCRT64-gcc-built extension can load into python.org CPython, provided `libgcc_s_seh-1.dll` / `libwinpthread-1.dll` are bundled (delvewheel) or statically linked. This is not *officially* supported but is a known-working pattern; it is exactly the inverse of the `tiledb/m2w64-htslib` precedent (MinGW-built static htslib linked into MSVC extensions). (MEDIUM)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| MSYS2 (UCRT64 environment) | current (pacman rolling) | POSIX toolchain host for Phase 1 MinGW build | htslib's officially supported Windows path; `configure`+`make` keep the existing `setup.py` flow intact; UCRT64 matches python.org CPython's CRT |
| MinGW-w64 GCC (ucrt64 toolchain) | GCC 15.x (via `mingw-w64-ucrt-x86_64-toolchain`) | C compiler for all bundled C code in Phase 1 | Same compiler family/flags as the existing Linux/macOS GCC build — the `-Wno-*` and GNU-ism cleanup is minimal; GCC flags just work |
| Microsoft Visual C++ (MSVC) | Build Tools for Visual Studio 2022, toolset v143 (14.4x) | C compiler for Phase 2 MSVC build + all official `win_amd64` wheel expectations | The only compiler officially supported for CPython 3.5+ extensions; required for Python 3.13+ wheels; native `win_amd64` compatibility with zero runtime-DLL caveats |
| cibuildwheel | 4.2.1 | Wheel CI orchestration (Windows jobs added to existing `release.yaml`) | Standard across the ecosystem; Windows MSVC support out of the box; delvewheel repair is now the default |
| delvewheel | 1.13.1 | Bundle dependent DLLs into Windows wheels | The auditwheel/delocate equivalent for Windows; already invoked by default by cibuildwheel ≥4.0; handles `libgcc_s_seh-1.dll`/`libwinpthread-1.dll` for MinGW wheels |
| setuptools (existing) | >=59 (current ~80.x works) | Build backend | Keep — replacing the build backend is a separate effort and out of scope for the port |
| Cython | >=3,<4 (existing pin) | .pyx -> C | Unchanged; see Windows cimport pattern below |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `msys2/setup-msys2` GHA action | v2 | Install/cache MSYS2 + pacman packages on `windows-*` runners | All Phase 1 CI jobs; use `msystem: UCRT64`, `update: true`, `install:` for packages |
| `ilammy/msvc-dev-cmd` GHA action | v1 | Activate MSVC x64 toolset on the runner | All Phase 2 CI jobs — without it, `cl.exe`/`link.exe` are not on PATH and cibuildwheel fails |
| MSYS2 packages: `base-devel`, `mingw-w64-ucrt-x86_64-toolchain`, `-python`, `-cython`, `-zlib`, `-bzip2`, `-xz`, `-curl`, `-openssl`, `-libdeflate`, `-autotools` | current | Full MinGW build environment | Phase 1 only; mirrors what htslib's INSTALL documents |
| Pre-generated `config.h` (checked into `win32/`) | per htslib 1.24 | MSVC replacement for `./configure` | Phase 2 only — libusb `msvc/` and libopenmpt pattern; generate once under MSYS2 with `CC=cl ./configure`, then hand-curate |
| `zlib` (MSVC build) | 1.3.x | gzip/BGZF compression for MSVC path | Phase 2: build from source in `CIBW_BEFORE_ALL_WINDOWS` (h5py builds HDF5 the same way) or via vcpkg; MSYS2 path uses the pacman package |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Git Bash (existing) | Day-to-day dev shell | Fine for editing/running Python; the actual C build must run inside the MSYS2 UCRT64 shell (`ucrt64.exe`), not Git Bash — Git Bash's toolchain is not a MinGW GCC toolchain |
| MSYS2 UCRT64 shell | Authoritative Phase 1 build/test environment | `$MSYSTEM` must read `UCRT64`; verify with `gcc -dumpmachine` → `x86_64-w64-mingw32` |
| `windows-2022` GHA runner | CI image | `windows-2025` also available; 2022 is the stable default with VS 2022 preinstalled |
| Python.org CPython 3.10-3.14 | Wheel targets | 3.9 is EOL (Oct 2025); align Windows matrix with upstream's active support window (3.10+); cibuildwheel 4.2.1 covers cp3.9-cp3.15 |

## Installation

```bash
# Phase 1 — MSYS2 UCRT64 environment (one-time dev setup, inside ucrt64 shell)
pacman -Syu
pacman -S --needed \
  base-devel \
  mingw-w64-ucrt-x86_64-toolchain \
  mingw-w64-ucrt-x86_64-python \
  mingw-w64-ucrt-x86_64-cython \
  mingw-w64-ucrt-x86_64-zlib \
  mingw-w64-ucrt-x86_64-bzip2 \
  mingw-w64-ucrt-x86_64-xz \
  mingw-w64-ucrt-x86_64-curl \
  mingw-w64-ucrt-x86_64-openssl \
  mingw-w64-ucrt-x86_64-libdeflate \
  mingw-w64-ucrt-x86_64-autotools

# Phase 1 — build (MSYS2 python; keeps the existing autotools flow)
python -m pip install 'Cython>=3,<4' pytest
python setup.py build_ext --inplace   # configure/make run under the MSYS2 shell

# Phase 2 — MSVC (python.org python, "x64 Native Tools" prompt or GHA)
pip install build cython delvewheel
python -m build --wheel
```

```yaml
# GitHub Actions — Phase 1 (MinGW) job skeleton
- uses: msys2/setup-msys2@v2
  with:
    msystem: UCRT64
    update: true
    install: base-devel mingw-w64-ucrt-x86_64-toolchain mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-cython
- shell: msys2 {0}
  run: python -m pip install -e . && python -m pytest tests

# GitHub Actions — Phase 2 (MSVC) wheel job skeleton
- uses: ilammy/msvc-dev-cmd@v1
  with: { arch: x64 }
- uses: pypa/cibuildwheel@v3   # pin to installed cibuildwheel version
  env:
    CIBW_BUILD: "cp31{0,1,2,3,4}-win_amd64"
    CIBW_SKIP: "pp* *_i686"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Native `windows-*` GitHub runners | Cross-compiling MinGW→Windows from Linux (xwin + clang-cl) | Only if runner minutes become a constraint; the autotools flow needs a POSIX shell anyway, so cross-compile saves little and adds toolchain-debugging burden |
| Pre-generated `config.h` for MSVC | Run `./configure CC=cl` under MSYS2/Cygwin at build time | Acceptable to *generate* the header once during development; running it per-CI-build reintroduces the POSIX-tool dependency the pre-baked header exists to remove |
| Keep setuptools backend | Migrate to scikit-build-core + CMake (cyvcf2's choice) | Right long-term, wrong milestone: htslib has no upstream CMake/meson build, so you'd be writing and maintaining one — upstream-hostile per project constraints |
| MSYS2 UCRT64 gcc | conda `m2w64-gcc` toolchain (TileDB's approach) | If the fork ever distributes through conda; ties packaging to conda-forge conventions and complicates plain-pip wheels |
| Bundle runtime DLLs via delvewheel | Statically link `-static-libgcc -static-libstdc++ -static -lpthread` | Viable belt-and-suspenders for the MinGW wheel; delvewheel alone is the standard and keeps binary size down |
| h5py-style "build C deps in `CIBW_BEFORE_ALL`" | Ask users to install deps | Not applicable — htslib is bundled by design; but the *pattern* (scripted dep build in before-all, MSVC for the extension) is exactly what Phase 2 should copy from `h5py/ci/get_hdf5_win.py` |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| MSYS2 `MINGW64`/`mingw32` environment (msvcrt-based) | msvcrt CRT mixing with python.org CPython corrupts fd/`FILE*`/`errno` handling — the classic "works in MSYS2, crashes on python.org Python" failure | UCRT64 environment (both use UCRT) |
| 32-bit `win32` wheels / `setup-msys2` msystem MINGW32 | Out of project scope; MSVC also splits toolchains per-arch (x86 vs x64) doubling CI complexity | `win_amd64` only |
| vcpkg htslib port for the MSVC path | Marked `!windows` upstream; relying on it is a dead end | Pre-generated `config.h` + explicit htslib/htscodecs source lists compiled directly by setuptools |
| `win32/stdint.h` (2013-era shim) | Obsolete since MSVC 2010 which ships a conforming `<stdint.h>`; shadows the system header | Delete; use system `<stdint.h>` |
| Running htslib `./configure` per-build on MSVC runners | MSVC can't run configure natively; wrong feature-test answers even when it runs | Checked-in, hand-curated `win32/config.h` + `config_vars.h` per toolchain (one MinGW variant can still come from real configure) |
| distutils-era `mingw32` compiler defaults | Designed for the msvcrt era; `mingw32ccompiler` assumptions don't hold for UCRT64 gcc vs python.org Python | Explicit compiler selection in `setup.py` (CC/LDSHARED env or custom `build_ext`) pointing at `C:\msys64\ucrt64\bin\gcc.exe` |
| Writing a meson/CMake build for htslib | Upstream has neither; maintenance burden lands on this fork forever and conflicts with "no functional upstream changes" | Existing autotools (MinGW) / pre-generated headers + source lists (MSVC) |
| Replacing `posix.*` cimports with runtime `if sys.platform` checks in `.pyx` | Cython needs compile-time resolution of cimports | Platform `cimport` switch (see below) |

## Stack Patterns by Variant

**Phase 1 — MinGW-w64 (MSYS2):**
- Use the UCRT64 MSYS2 environment for the whole build and test loop (MSYS2's own Python first).
- Because htslib officially supports this path, pysam's existing `configure`+`make` orchestration in `setup.py` largely survives; the Windows work is plumbing (invoke under the MSYS2 shell, skip `nm`, guard `$ORIGIN` rpath) plus the `.pyx` POSIX cleanups (W2/W3/W9).
- For python.org-targeted wheels: compile with ucrt64 gcc against python.org headers (extensions don't link `python3x.lib`), bundle `libgcc_s_seh-1.dll`/`libwinpthread-1.dll` via delvewheel.
- Because: minimal build-system change (CONCERNS W1 mostly disappears), fastest path to a green test suite, validates all the Cython/POSIX fixes before MSVC is attempted.
- Top risk to spike early: setuptools on Windows assumes MSVC; wiring ucrt64 gcc as the compiler for a python.org-Python wheel build needs a custom `build_ext` step and is the least-documented part of this phase (MEDIUM confidence — pattern is proven but project-specific glue is required).

**Phase 2 — MSVC (distribution-grade):**
- Use Build Tools for Visual Studio 2022 (v143), `ilammy/msvc-dev-cmd` x64 activation, cibuildwheel on `windows-2022`.
- Compile htslib/htscodecs from explicit source lists in `setup.py` (replace `make lib-static`), driven by checked-in `win32/config.h` + `config_vars.h` generated once via MSYS2 `./configure CC=cl` then hand-curated (libusb/libopenmpt pattern).
- Replace `posix.*` cimports with a compile-time platform switch: Cython `IF UNAME_SYSNAME == "Windows"` is deprecated in Cython 3.1 — use plain Python-level `if` on a module constant combined with `compile_time_env`/`DEF`-style macros, mapping to `libc.msvcrt`/`libc.io` (`_open`, `_dup`, `_read`, `_close`, `_isatty`) (MEDIUM — Cython 3.1 deprecation detail).
- Bundle zlib (and optionally bzip2/xz/libdeflate) built from source in `CIBW_BEFORE_ALL_WINDOWS`, h5py-style; skip libcurl in the first MSVC iteration (W6 already recommends `--disable-libcurl` first).
- Because: MSVC is the only toolchain with official CPython support and the only one that yields wheels with zero runtime-DLL caveats; the pre-generated-header pattern is the established industry approach for autotools libs under MSVC.

**Cross-cutting:**
- Native runners, never cross-compile, in both phases. The build needs a POSIX shell for Phase 1 anyway; `msys2/setup-msys2` makes native MinGW CI trivial.
- `delvewheel` repair is on by default with cibuildwheel ≥4.0 — do not set a custom `repair-wheel-command` unless you need `--include` for `LoadLibrary`-loaded DLLs (relevant later if a Windows `dynamic_libs.c` variant lands for libcurl; W6).

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| cibuildwheel 4.2.1 | delvewheel ≥1.10 (bundled default), Python 3.9-3.15 | cibuildwheel itself requires Python ≥3.11 to run; builds cp3.9+ wheels. GitHub Action `pypa/cibuildwheel@v3` wraps cibuildwheel 3.x — pin action tag to the major of the pip-installed version you validate against |
| MSVC v143 (VS 2022) | CPython 3.9-3.15 wheels | Python 3.13+ is built with v143; use v143 for all versions to avoid two toolsets. Windows SDK 10/11 comes with the runner image |
| UCRT64 gcc 15.x | python.org CPython ≥3.9 | Both link UCRT; safe CRT mixing. Never pair msvcrt-built objects with python.org Python |
| Cython 3.x (<4) | existing `.pyx` sources | Cython 3.1 deprecates compile-time `IF` blocks — write new platform switches as plain Python `if` over compile-time constants (keep the existing `<4` pin) |
| htslib 1.24 (bundled) | MSYS2 ucrt64 packages 1.24-1 | Version parity confirmed in MSYS2 repo; MinGW build of the bundled tree is expected to work with htslib's documented MSYS2 flow |
| delvewheel 1.13.1 | Windows 7 SP1+ targets | UCRT is an OS component on Win10+ — do not bundle `ucrtbase.dll` |

## Sources

- [htslib INSTALL (develop)](https://github.com/samtools/htslib/blob/develop/INSTALL) — official MSYS2/MinGW build section; MSVC unverified (HIGH)
- [MSYS2 package: mingw-w64-ucrt-x86_64-htslib](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-htslib) — fetched: version 1.24-1, deps incl. curl/openssl/libdeflate, built 2026-07-13 (HIGH)
- [MSYS2.org](https://www.msys2.org/) / [MSYS2 docs: CI](https://www.msys2.org/docs/ci/) — UCRT64 as default env; setup-msys2 usage (HIGH)
- [msys2/setup-msys2 action](https://github.com/msys2/setup-msys2) — GHA integration, matrix example (HIGH)
- [cibuildwheel on PyPI](https://pypi.org/project/cibuildwheel/) — fetched: 4.2.1, Sep 5 2026; delvewheel default repair since 4.0.0; cp3.9-3.15 (HIGH)
- [cibuildwheel options docs](https://cibuildwheel.pypa.io/en/stable/options/) / [FAQ](https://cibuildwheel.pypa.io/en/stable/faq/) — MSVC arch handling, `CIBW_BEFORE_ALL` dep-build pattern (MEDIUM-HIGH)
- [delvewheel on PyPI](https://pypi.org/project/delvewheel/) — 1.13.1; `--include`/`--with-mangle` semantics (HIGH)
- [Cython install docs](https://cython.readthedocs.io/en/latest/src/quickstart/install.html) — MSVC as the officially tested Windows compiler (MEDIUM-HIGH)
- [Python Wiki: WindowsCompilers](https://wiki.python.org/moin/WindowsCompilers) — MinGW officially supported only up to 3.4; VS 2022 v143 for 3.13+ (MEDIUM)
- [Ziggit: GNU/MingW and MSVC C ABI compatibility](https://ziggit.dev/t/windows-gnu-mingw-and-msvc-binary-c-abi-compatibility-guarantees/6903) — UCRT↔UCRT mixing is safe; msvcrt mixing is not (MEDIUM)
- [Stack Overflow: autotools configure for MSVC](https://stackoverflow.com/questions/65555603/how-to-produce-a-configure-script-for-windows-with-autotools) — cross-compiled configure gives wrong feature-test answers for MSVC (MEDIUM)
- [libusb MinGW/MSVC config.h discussion](https://libusb-devel.narkive.com/33yao2v6/problem-compiling-with-mingw) — pre-generated `config.h` in `msvc/` precedent (MEDIUM)
- [libopenmpt FAQ](https://lib.openmpt.org/libopenmpt/faq/) — separate MSVC source package with pre-configured bundled deps precedent (MEDIUM)
- [h5py repo / HDFGroup issue #5026](https://github.com/HDFGroup/hdf5/issues/5026) — h5py builds HDF5 from source via `ci/get_hdf5_win.py` (CMake+MSVC) in CI (MEDIUM)
- [cyvcf2 repo](https://github.com/brentp/cyvcf2) / [install docs](https://brentp.github.io/cyvcf2/) — no Windows wheels; experimental MSYS2 external-htslib only; scikit-build-core+CMake backend (MEDIUM)
- [cyvcf2 issue #243](https://github.com/brentp/cyvcf2/issues/243) — bundled htslib is the Windows blocker for htslib-wrapping projects (MEDIUM)
- [tiledb m2w64-htslib (anaconda)](https://anaconda.org/tiledb/m2w64-htslib) / [TileDB-Inc/m2w64-htslib-build](https://github.com/TileDB-Inc/m2w64-htslib-build) — MinGW-built statically-linked htslib linked from MSVC builds; no libcurl (MEDIUM)
- [vcpkg htslib port](https://vcpkg.link/ports/htslib) — marked `!windows` (HIGH)
- [xwin: cross compiling Windows binaries from Linux](https://jake-shadle.github.io/xwin/) — clang-cl cross-compile option considered and rejected (MEDIUM)
- [MSYS2 python package](https://packages.msys2.org/package/mingw-w64-ucrt-x86_64-python) / [cython package](https://packages.msys2.org/package/mingw-w64-ucrt-x86_64-cython) — UCRT64 Python/Cython availability (HIGH)
- [scivision: GitHub Actions MSYS2 with Python](https://www.scivision.dev/github-actions-msys-python/) — mixing setup-python with MSYS2 toolchain via GITHUB_PATH (MEDIUM)
- [PyO3/maturin issue #2217](https://github.com/PyO3/maturin/issues/2217) — MinGW wheel vs python.org CPython failure mode (msvcrt) (MEDIUM)
- [SO: replacement for unistd.h on MSVC](https://stackoverflow.com/questions/341817/is-there-a-replacement-for-unistd-h-for-windows-visual-c) — `<io.h>`/`<process.h>` mappings for the MSVC shim work (MEDIUM)

---
*Stack research for: pysam Windows port (MinGW-w64 + MSVC toolchain selection)*
*Researched: 2026-09-17*
