# Project Research Summary

**Project:** pysam Windows port — MinGW-w64 (MSYS2) first, MSVC second, distributable `win_amd64` wheels
**Domain:** Brownfield port of a Cython/C-extension scientific Python package with bundled autotools C libraries (htslib/samtools/bcftools) to Windows
**Researched:** 2026-09-17
**Confidence:** MEDIUM-HIGH

## Executive Summary

This is a Windows port of pysam, a Cython/C-extension package that bundles htslib, samtools, and bcftools and today builds only on POSIX via autotools/make. No successful public pysam Windows port exists, and every comparable project (cyvcf2, rust-htslib, MSYS2 htslib packages) has cut features or shipped nothing on Windows — the competitive bar is empty, and full parity including a self-contained `pip install`-able wheel is achievable. The recommended approach, consistent across all four research files, is a two-toolchain strategy: **Phase 1 with MSYS2 UCRT64/MinGW-w64** (htslib's officially supported Windows path, minimal build-system change, fastest route to a green test suite), then **Phase 2 with MSVC** (the only toolchain with official CPython extension support and the only way to wheels with zero runtime-DLL caveats).

The central architectural decision is to short-circuit autotools entirely on Windows: setuptools drives C compilation directly from explicit source lists against a **pre-baked per-toolchain `config.h`** checked into `win32/` (the Pillow/libusb pattern), with MSYS2 used once, locally, to harvest the correct flags — never as a CI wheel-build path. Cross-extension linking replaces `$ORIGIN` rpath with import libraries and a two-pass link order. The top risks are well-characterized: CRT mismatch (must use the UCRT64 toolchain, never msvcrt-vintage MinGW), silent binary-mode corruption of BAM/BGZF output through text-mode fds (highest-severity silent-corruption risk), LLP64 `long` truncation, and wheels that work on the build machine but fail on clean machines (mitigated by delvewheel plus a clean-machine smoke test as the release gate). Remote I/O (libcurl/S3/GCS) is deliberately deferred — every competitor lacks it on Windows too.

## Key Findings

### Recommended Stack

From [STACK.md](STACK.md) (MEDIUM-HIGH confidence; version facts verified against official pages). The stack is deliberately conservative: keep setuptools and the existing `setup.py` orchestration, add Windows branches; do not migrate build backends or write a meson/CMake build for htslib.

**Core technologies:**
- **MSYS2 (UCRT64 environment) + MinGW-w64 GCC 15.x**: Phase 1 build host and compiler — htslib's officially documented Windows path; UCRT64 matches python.org CPython's CRT, making fd/FILE* passing safe.
- **MSVC (Build Tools for VS 2022, v143)**: Phase 2 compiler — only officially supported CPython extension toolchain; required for Python 3.13+ and for zero-caveat `win_amd64` wheels.
- **cibuildwheel 4.2.1**: wheel CI orchestration — delvewheel repair is the default Windows repair command since 4.0.0.
- **delvewheel 1.13.1**: bundles MinGW runtime DLLs (`libgcc_s_seh-1.dll`, `libwinpthread-1.dll`) into wheels.
- **Pre-generated `config.h`** checked into `win32/` (per toolchain): MSVC replacement for `./configure`, generated once via `CC=cl ./configure` under MSYS2 then hand-curated.
- **GitHub Actions helpers**: `msys2/setup-msys2@v2` (Phase 1), `ilammy/msvc-dev-cmd@v1` (Phase 2).

Hard constraints: never mix the msvcrt-vintage `MINGW64` MSYS2 environment with python.org Python; `win_amd64` only; Python 3.10+ matrix (3.9 EOL); Cython 3.x with plain-if compile-time platform switches (Cython 3.1 deprecates `IF UNAME_SYSNAME`).

### Expected Features

From [FEATURES.md](FEATURES.md) (MEDIUM confidence, codebase docs HIGH). v1 must deliver a self-contained pip wheel with the full core API surface — the single P1 theme is "real parity, not a subset," because every competitor shipped a subset and the user complaints driving this project are about install friction, not missing APIs.

**Must have (table stakes, all P1):**
- Self-contained `win_amd64` pip wheel (no toolchain, no PATH dependencies) — the entire product
- Core htslib bindings: AlignmentFile, AlignedSegment, VariantFile, TabixFile, FastaFile, BGZF
- Full samtools/bcftools in-process command dispatch
- Indexing (BAI/CSI/TBI) and region queries
- CRAM read/write with bundled htscodecs
- Full test suite passing on a Windows CI runner (the objective parity evidence)

**Should have (P2, after validation):**
- MSVC toolchain wheels — after MinGW pipeline is stable
- Remote I/O via libcurl (http/S3/GCS) — needs a Windows `dynamic_libs.c` rewrite; **unique on Windows** if shipped
- libdeflate acceleration — cheap once the MSYS2 dep story exists

**Defer (v2+ / rejected):**
- Remote I/O in v1 (ship `--disable-libcurl`, document), 32-bit wheels, conda-forge early, Cygwin, PyPI name without upstream coordination

### Architecture Approach

From [ARCHITECTURE.md](ARCHITECTURE.md) (MEDIUM). The standard shape for this class of port: **the autotools layer is short-circuited on Windows; setuptools compiles htslib/htscodecs from explicit source lists against pre-baked `config.h`**. One `setup.py` with three platform branches (POSIX byte-identical to today), toolchain dispatch via a `build_ext` subclass keyed on `compiler.compiler_type`, static-everything linking (Python 3.8+ DLL resolution rules make self-containment a hard requirement), and cross-extension linking via import libraries (`libchtslib.dll.a`/`.lib`) replacing `$ORIGIN` rpath, with a two-pass link order (chtslib to tools/utils to features).

**Major components:**
1. `setup.py` Windows branch — config writer, source-list builder, hard-coded config dict (replaces `sh configure`/`make`/`nm`)
2. `win32/config.h.{mingw,msvc}` templates — one per toolchain, harvested from a real MSYS2 configure run
3. Dual-toolchain `cy_build_ext` + cross-extension link coordinator
4. Ported `check_ext_symbol_conflicts` (`llvm-nm`/`dumpbin` instead of `nm`) — currently silently skipped on Windows
5. Centralized portability shim (extend `win32/unistd.h`; one `libcport.pxd` for Cython `posix.*` replacements)

Phasing per architecture research: build, then runtime/tests, then CI/wheels, then second toolchain.

### Critical Pitfalls

From [PITFALLS.md](PITFALLS.md) (HIGH confidence on CRT/ABI/DLL findings). Twelve pitfalls with a phase mapping; the five that should shape roadmap gates:

1. **CRT mismatch** — heap corruption and fd failures on end-user machines only; use UCRT64 toolchain exclusively, verify with `objdump -p *.pyd | grep msvcrt` in CI (must be empty), never mix objects across toolchains.
2. **fd/stdout divergence + text-mode default** — `fopen` without `O_BINARY` corrupts BAM/BGZF output silently (LF becomes CRLF); `/dev/null` becomes `os.devnull`; audit every `open`/`fopen` site for binary mode during the POSIX-cleanup pass.
3. **LLP64 (long = 32-bit)** — silent pointer/offset truncation; `compile_test.py` struct-size assertions localize every occurrence; update expected sizes for LLP64 rather than skipping.
4. **Non-self-contained wheels (DLL load failed on clean machines)** — delvewheel repair plus a clean-runner install/import/BAM-open smoke test as the release gate; `--strip` for MinGW name-mangling; include GCC runtime license texts.
5. **POSIX test-suite semantics** — shell pipelines, signal exit codes, `REF_PATH` colon-vs-semicolon, spawn-mode multiprocessing; rewrite shell oracles in-process and track skip counts against Linux to prevent skip creep masquerading as success.

Also notable: non-ASCII filenames break under ANSI path handling (add a CJK canary test early; full wide-API fix later), MAX_PATH (use short CI workdirs), and MSVC C99 non-compliance (VLA whack-a-mole — one central shim header, consider clang-cl as an intermediate).

## Implications for Roadmap

Based on research, suggested phase structure (aligned with ARCHITECTURE.md's seven-step build order and PITFALLS.md's phase mapping):

### Phase 1: Windows build system — pre-baked config + MinGW source-list compile
**Rationale:** `setup.py` currently aborts at import on Windows (uncaught `FileNotFoundError` from `make`); nothing downstream exists until this works. Everything here unblocks everything else.
**Delivers:** `win32/config.h.mingw` template (harvested from one real MSYS2 configure run), setup.py Windows branch (config writer, htslib/htscodecs source-list builder, `cy_build_ext` with MinGW flags), two-pass import-library linking, importable `pysam` on a dev machine.
**Uses:** MSYS2 UCRT64 + MinGW-w64 GCC 15.x, existing setuptools backend, `compiler_type` dispatch pattern.
**Avoids:** Anti-patterns "running MSYS2 autotools as the CI path" and "reusing the untested `setup.py:633` MSVC branch."
**Research flag:** likely needs `/gsd-plan-phase --research-phase 1` — the custom `build_ext` wiring of ucrt64 gcc for python.org-Python wheel builds is the least-documented part (STACK MEDIUM confidence).

### Phase 2: Cython/POSIX portability + first full test pass (MinGW)
**Rationale:** Architecture build-order steps 4-5 — parallelizable with Phase 1 in planning but gated on it for verification. The success criterion per PROJECT.md lives here.
**Delivers:** Centralized `posix.*` cimport cleanup (one `libcport.pxd`, not per-call-site `IF` blocks — Cython 3.1 deprecation noted), `/dev/null` to `os.devnull`, binary-mode (`O_BINARY`/`b`) audit, LLP64 `long` audit with `compile_test.py` sizes updated, test-suite POSIX-ism cleanup (in-process oracles, `os.pathsep` for `REF_PATH`, spawn-safe conftest), full test suite green on MSYS2.
**Avoids:** Pitfalls 2 (binary-mode corruption), 8 (fd semantics), 10 (POSIX test semantics), 6 canary test (CJK filename).
**Research flag:** `/gsd-plan-phase --research-phase 2` — the exact `libc.msvcrt`/`libc.io` mapping and Cython 3.1 compile-time-constant idiom deserve verification against current Cython docs.

### Phase 3: Windows CI + distributable wheels (MinGW)
**Rationale:** Only meaningful once tests pass (cibuildwheel tests each wheel in isolation); Pitfall 11 says get one plain `windows-latest` job green before cibuildwheel.
**Delivers:** `windows-latest` CI job, cibuildwheel `win_amd64` jobs with `CIBW_*_WINDOWS` platform-suffixed overrides, delvewheel repair, clean-machine smoke test as release gate, GitHub Releases fork channel.
**Avoids:** Pitfalls 1 (UCRT audit in CI), 5 (clean-machine gate), 7 (short workdir), 11 (POSIX-only cibuildwheel config).
**Research flag:** standard cibuildwheel patterns — skip research-phase unless the MinGW-python.org-Python wheel build from Phase 1 remains unproven.

### Phase 4: MSVC toolchain
**Rationale:** Deferred until MinGW wheels ship (FEATURES P2; architecture step 7) — shares ~80% of the work and forces no re-design if Phases 1-2 kept fixes toolchain-neutral.
**Delivers:** `win32/config.h.msvc`, MSVC shim header (central `unistd.h` replacements, `/FI` forced include), `ilammy/msvc-dev-cmd` CI, `dumpbin`-based symbol check, official-grade wheels.
**Avoids:** Pitfalls 1 (same-generation MSVC), 3 (no whack-a-mole — one shim; clang-cl fallback), 4 (per-toolchain dependency closure).
**Research flag:** `/gsd-plan-phase --research-phase 4` — clang-cl intermediate step and the Schannel-vs-OpenSSL question (if remote I/O advances) need a decision spike.

### Phase 5 (later): Remote I/O parity (libcurl/S3/GCS)
**Rationale:** Explicitly out of v1 scope (conflicts per FEATURES dependency graph); unique-on-Windows differentiator.
**Delivers:** Windows `dynamic_libs.c` variant (`LoadLibraryA`/`GetProcAddress`) or static libcurl with Schannel; vendored DLL handling via delvewheel `--add-dll`.
**Avoids:** Pitfall 9 (phase deliberately; `HAVE_LIBCURL=0` + skip-gated networking tests until then).
**Research flag:** `/gsd-plan-phase --research-phase 5` — no upstream-independent design precedent in the codebase.

### Phase Ordering Rationale

- Build system first because every feature and every test depends on a wheel-capable build (FEATURES dependency graph root).
- Portability fixes before CI because "full test suite passes" is the only objective parity evidence and it is definitionally blocked until shell-oracle tests are rewritten.
- MSVC after MinGW because the MinGW port forces and validates all the platform-abstraction work; doing MSVC first doubles risk on the harder toolchain (FEATURES dependency note).
- Remote I/O last because it is the largest remaining feature, the only one with no codebase precedent, and parity-with-ecosystem (everyone lacks it) rather than parity-with-Linux is the correct v1 bar.

### Research Flags

Needs research during planning:
- **Phase 1:** custom `build_ext` to wire ucrt64 gcc against python.org CPython headers (least-documented glue; STACK MEDIUM confidence).
- **Phase 2:** Cython 3.1 compile-time platform-switch idiom + exact `libc.msvcrt`/`libc.io` mappings.
- **Phase 4:** clang-cl as MSVC-phase fallback; MSVC C99 shim scope (VLA inventory in bundled sources).
- **Phase 5:** Windows dynamic loader design for libcurl.

Standard patterns (skip research-phase):
- **Phase 3:** cibuildwheel + delvewheel + GHA Windows runners are exhaustively documented; patterns settled.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Version facts verified against official pages (cibuildwheel 4.2.1, delvewheel 1.13.1, MSYS2 htslib 1.24-1); toolchain strategy cross-checked across multiple ecosystem sources |
| Features | MEDIUM | Cross-checked web sources + HIGH-confidence codebase docs (`.planning/codebase/`); competitive analysis solid, no pysam-specific prior art exists |
| Architecture | MEDIUM | Web corroborated by HIGH-confidence local codebase audit; synthesizes sibling-package patterns (Pillow, lxml, h5py, libusb) — no pysam Windows blueprint exists anywhere |
| Pitfalls | HIGH | CRT/ABI/LLP64/delvewheel findings corroborated by multiple independent authoritative sources (Steve Dower, Matthew Brett, cppreference); MEDIUM on drifting cibuildwheel image specifics |

**Overall confidence:** MEDIUM-HIGH. The stack and pitfalls rest on verified, multi-source facts; the architecture is a well-grounded synthesis of established patterns rather than a proven pysam-specific recipe.

### Gaps to Address

- **MinGW to python.org-CPython wheel glue:** pattern is proven ecosystem-wide but project-specific `setup.py` work is unverified — spike early in Phase 1.
- **Volume of MSVC C99 incompatibilities in bundled sources:** unknown until first compile; the shim design should be sized in Phase 1 (design during MinGW, per Pitfall 3) with a clang-cl escape hatch.
- **Symbol-prefix staleness:** 2013-era `#define` prefixes in `import/pysam.h` are surely stale for current upstream sources; the ported symbol check must run before release.
- **config.h drift on htslib re-import:** no automation exists to detect baked-template drift; add a devtools check script.
- **Non-ASCII path strategy:** documented-limitation vs UTF-8-to-wide shim is a Phase 2/4 decision the research leaves open.
- **Collected-test-count parity target:** the acceptable skip-count delta vs Linux needs defining during test-port planning.

## Sources

### Primary (HIGH confidence)
- [htslib INSTALL](https://github.com/samtools/htslib/blob/develop/INSTALL) — official MSYS2/MinGW Windows path; MSVC unverified
- [MSYS2 package: mingw-w64-ucrt-x86_64-htslib](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-htslib) — htslib 1.24-1 builds on UCRT64 with full deps
- [cibuildwheel on PyPI](https://pypi.org/project/cibuildwheel/) / [options docs](https://cibuildwheel.pypa.io/en/stable/options/) — 4.2.1, delvewheel default since 4.0.0
- [delvewheel on PyPI](https://pypi.org/project/delvewheel/) — 1.13.1
- [Steve Dower: Building Extensions for Python 3.5](https://stevedower.id.au/blog/building-for-python-3-5) — CRT/UCRT authoritative
- [Matthew Brett: Python compiled with MinGW-w64](https://matthew-brett.github.io/pydogue/mingw_python.html)
- [cppreference: C compiler support](https://cppreference.net/c/99.html) — MSVC C99/C11 feature matrix
- [Bioconda FAQ](https://bioconda.github.io/faqs.html) — "Windows is not supported"
- [pysam issues #575, #969, #1132, #1137](https://github.com/pysam-developers/pysam/issues/575) — Windows install demand
- Codebase docs: `.planning/codebase/STACK.md`, `ARCHITECTURE.md`, `CONCERNS.md` (W1-W10), `TESTING.md`

### Secondary (MEDIUM confidence)
- [Cython docs — MinGW appendix](https://cython.readthedocs.io/en/latest/src/tutorial/appendix.html) — compiler_type dispatch pattern
- [vcpkg htslib port](https://vcpkg.link/ports/htslib) — marked `!windows`
- [tiledb m2w64-htslib](https://github.com/TileDB-Inc/m2w64-htslib-build) — MinGW htslib linked into MSVC builds (inverse pattern)
- [h5py HDF5 Windows CI build](https://github.com/HDFGroup/hdf5/issues/5026) — CIBW_BEFORE_ALL dep-build pattern
- [samtools #2064](https://github.com/samtools/samtools/issues/2064) — MSYS2 GHA build of htslib/samtools/bcftools
- [cyvcf2](https://github.com/brentp/cyvcf2) / [rust-htslib](https://github.com/rust-bio/rust-htslib) — competitor feature cuts on Windows
- [Ziggit: GNU/MinGW and MSVC ABI compatibility](https://ziggit.dev/t/windows-gnu-mingw-and-msvc-binary-c-abi-compatibility-guarantees/6903) — UCRT mixing rules
- [PVS-Studio: 64-bit porting / LLP64](https://pvs-studio.com/en/blog/posts/cpp/1036/) — `long` truncation class
- [Fortran Discourse: MSYS2 + cibuildwheel pattern](https://fortran-lang.discourse.group/t/python-wheels-on-github-actions-using-fortran-f2py-numpy-meson-and-cibuildwheel/5609) — CIBW_ENVIRONMENT_WINDOWS injection
- [MSDN: fopen/_wfopen](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/fopen-wfopen) — wide-path recipe

### Tertiary (LOW confidence)
- [Stack Overflow: autotools configure for MSVC](https://stackoverflow.com/questions/65555603/how-to-produce-a-configure-script-for-windows-with-autotools) — cross-configure gives wrong feature answers
- [GitCode: Cython + Windows Unicode](https://blog.gitcode.com/6c518dfd0b78d705f72f17197bb0eabe.html) — `PyUnicode_AsWideCharString` for Python 3.12
- [meshpy #150](https://github.com/inducer/meshpy/issues/150) — non-self-contained MinGW wheel failure mode

---
*Research completed: 2026-09-17*
*Ready for roadmap: yes*
