# Feature Research

**Domain:** Windows port of a scientific Python package with bundled C command-line tools (pysam: Cython/C extensions wrapping htslib/samtools/bcftools)
**Researched:** 2026-09-17
**Confidence:** MEDIUM (cross-checked web sources + HIGH-confidence codebase docs in `.planning/codebase/`)

## Feature Landscape

### Table Stakes (Users Expect These)

Features Windows users assume exist. Missing these = the port is not usable and users stay on WSL2/Docker.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `pip install` → working package from a wheel, no toolchain required | The #1 complaint across all pysam Windows issues (#575, #969, #1132, #1137) is that pip install fails; a port that still needs MSYS2 locally is not a port | HIGH | Requires full build-system replacement of `sh configure`/`make`/`nm` (concern W1) + cibuildwheel `win_amd64` jobs (W8); wheel must be self-contained |
| Core htslib API bindings: `AlignmentFile`, `AlignedSegment`, `VariantFile`, `TabixFile`, `FastaFile`, BGZF | This *is* pysam for most users — programmatic SAM/BAM/CRAM/VCF/BCF I/O. Linux parity without these is meaningless | HIGH | 12 Cython extension modules; blocked by `posix.*` cimports (W2) and extension link-order/rpath issues (W5) |
| samtools/bcftools command dispatch (`pysam.sort()`, `pysam.mpileup()`, `pysam.bcftools.*`) | PROJECT.md defines full feature parity as the goal; dispatch is half of pysam's surface | MEDIUM | Blocked by hardcoded `/dev/null` (W3) and POSIX fd APIs in `_pysam_dispatch` (W2); in-process dispatch works fine on Windows once stdio redirection is portable |
| Indexing: `.bai`/`.csi`/`.tbi` creation and region queries | Any real workflow (`fetch()`, `tabix`) needs indexes; htslib indexing is platform-independent C | LOW | Only blocked transitively by W2 (libctabix posix cimports) — no Windows-specific logic needed |
| CRAM read/write including htscodecs codecs | CRAM is standard in modern genomics; htscodecs is plain C, builds under MinGW | MEDIUM | External-reference lookup via `REF_PATH` works but uses `;` as path separator on Windows (test-suite fix needed, W9); reference-cache/configure nuances |
| Self-contained wheel (no external DLL/PATH dependencies) | Windows Python convention: wheels vendor everything; users will not install zlib/htscodecs separately | MEDIUM | Static-link zlib/htscodecs/libdeflate (and libgcc/libstdc++ if MinGW); MSYS2's own packages prove this is achievable |
| Full test suite passes on Windows | PROJECT.md success criterion; also the only objective parity evidence | HIGH | Requires rewriting POSIX-shell comparison tests (W9: `samtools view | wc`, `/dev/null` redirects, `REF_PATH` separator, signal exit codes) |
| Python version coverage matching upstream | Users on 3.10–3.13 each expect a wheel | LOW | Purely a CI matrix matter once one version builds |

### Differentiators (Competitive Advantage)

Features that set this port apart. Notably, **the competitive bar on Windows is essentially empty** — every comparable project has cut features here.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Remote I/O (`http(s)://`, S3, GCS via libcurl) on Windows | **No competitor ships this on Windows**: MSYS2's prebuilt m2w64-htslib explicitly lacks libcurl ("cannot be used with S3 or GCS"), cyvcf2 Windows is MSYS2-experimental without bundling, rust-htslib has no prebuilt Windows bindings. Full remote parity would be genuinely unique | HIGH | Current `pysam/dynamic_libs.c` is Linux-only (`dlopen`, hardcoded `libcurl.so.4` sonames); needs a Windows `LoadLibraryA`/`libcurl*.dll` variant or static link (concern W6) |
| MSVC-built wheels alongside MinGW-w64 | MSVC is the native toolchain of the official CPython wheel ecosystem (fewer runtime-DLL surprises, better debugging symbols, standard ABI expectations) | HIGH | Requires replacing `posix.*` cimports with `libc.msvcrt`/`libc.io` equivalents (W2 option b) and `_isatty`/`_fdopen`/`_fileno` mappings (W4, W10) |
| Dual-toolchain CI validation on a Windows runner | Continuous proof of no regressions — something upstream has never had and cyvcf2/rust-htslib lack | MEDIUM | Add `windows-latest` to ci.yaml + `win` matrix to release.yaml (W8) |
| libdeflate-accelerated BGZF/CRAM compression | Performance parity with Linux wheels (compression speed is user-visible on large BAMs) | LOW | htslib builds it when present; MSYS2 provides `mingw-w64-x86_64-libdeflate` |
| Full samtools/bcftools command surface, not a subset | Comparable projects that embed tools on Windows tend to trim; keeping 100% of subcommands makes the port a drop-in replacement | MEDIUM | The embedding mechanism (`*.pysam.c` regex rewrites) is platform-neutral; risk is per-subcommand POSIX leaks (isatty/fileno, W4) |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| 32-bit (win32) Windows wheels | "Complete coverage" instinct | No expressed demand in any pysam Windows issue; doubles CI/build matrix; 32-bit genomics workloads are RAM-bound anyway | 64-bit only (already Out of Scope in PROJECT.md) |
| Remote I/O in the first release | Feature-parity maximalism | `dynamic_libs.c` is Linux-only by design; adds libcurl+OpenSSL DLL vendoring, cert-path issues, and a large test surface on top of an already-large port | Ship v1 with `--disable-libcurl`, document clearly, add as differentiator milestone later |
| Publishing under the official PyPI `pysam` name immediately | User convenience | Requires upstream maintainer coordination; naming conflict risks fragmenting the ecosystem if done unilaterally | Fork channel (GitHub Releases) first; upstream separately (already decided in PROJECT.md) |
| Conda-forge/bioconda Windows package early | conda users are a large bioinformatics segment | Bioconda explicitly does not support Windows at all; a conda-forge recipe is a second packaging system to maintain before the pip wheel is proven | pip wheels first; evaluate conda-forge only after stable releases |
| Cygwin support | Legacy habit | Superseded by MSYS2 (which htslib officially recommends) and WSL2; Cygwin Python is a separate ecosystem | MSYS2 build host only, producing native wheels |
| Runtime reliance on system-installed htslib/DLLs (cyvcf2's `CYVCF2_HTSLIB_MODE=EXTERNAL` model) | Smaller wheels, "use the distro's htslib" | On Windows there is no system htslib; users must hand-build in MSYS2 — exactly the friction this port exists to remove | Bundle everything, statically (the pysam model, already the upstream design) |
| Building wheels that require MSYS2/Git Bash on the *user* machine | "Works on my machine" | A wheel that imports only when `C:\msys64\mingw64\bin` is on PATH is not distributable | CI-built, self-contained wheels |

## Feature Dependencies

```
[Build system port: pre-baked config.h + setuptools-driven htslib/htscodecs compile]
    └──requires──> [Self-contained win_amd64 wheel]
                       └──requires──> [CI: windows runner + cibuildwheel win jobs]
                                          └──requires──> [Test suite POSIX cleanup (W9)]
                                                             └──requires──> [Full test pass = parity definition]

[core API bindings (AlignmentFile/VariantFile/Tabix/Fasta)] ──requires──> [posix.* cimport cleanup (W2)]
[samtools/bcftools dispatch] ──requires──> [devnull/stdio portability (W2, W3, W10)]
[indexing / region queries] ──requires──> [core API bindings]

[MSVC wheels] ──requires──> [MinGW-w64 port learnings]
                                 └──requires──> [posix.* cimport cleanup (MSVC variant)]
[remote I/O (libcurl/S3/GCS)] ──requires──> [self-contained wheel] + [Windows dynamic loader rewrite (W6)]
    └──conflicts──> [v1 release scope]
```

### Dependency Notes

- **Self-contained wheel requires build-system port:** `setup.py` currently cannot execute on Windows at all (W1: `run_make_print_config` raises uncaught `FileNotFoundError` at import time). Everything downstream of a wheel depends on this.
- **Full test pass requires test-suite cleanup (W9):** comparison tests shell out to `samtools`/`wc`/`awk` with `>` redirects; these can never run on Windows, so "full test suite passes" is definitionally blocked until they are rewritten in-process.
- **MSVC wheels require the MinGW port first:** the MSVC-specific work (msvcrt cimports, `_isatty`/`_fdopen`) is additive on top of the platform-abstraction work the MinGW port forces; doing MSVC first would double the risk on the harder toolchain.
- **Remote I/O conflicts with v1 scope:** it is the single largest remaining feature after basic parity and the only one with no upstream-independent design precedent in this codebase (Linux-only `dynamic_libs.c`).

## MVP Definition

### Launch With (v1)

- [ ] Self-contained `win_amd64` wheel installable via pip from GitHub Releases (MinGW-w64 toolchain) — the entire product
- [ ] Core API bindings: AlignmentFile/AlignedSegment/VariantFile/TabixFile/FastaFile/BGZF — why users install pysam
- [ ] Full samtools/bcftools dispatch surface — parity requirement per PROJECT.md
- [ ] Indexing (BAI/CSI/TBI) and region queries — required by any real workflow
- [ ] CRAM read/write with bundled htscodecs — table stakes for modern genomics
- [ ] Full test suite passing on Windows CI runner — objective success criterion

### Add After Validation (v1.x)

- [ ] MSVC toolchain wheels — after MinGW pipeline is stable; trigger: users hit MinGW-runtime issues or demand official-style wheels
- [ ] Remote I/O via libcurl (http/S3/GCS) — trigger: parity milestone; needs Windows `dynamic_libs.c` rewrite
- [ ] libdeflate acceleration — trigger: trivial once MSYS2 dependency story is set; fold into v1 build if cheap
- [ ] Python version matrix expansion — trigger: first release feedback

### Future Consideration (v2+)

- [ ] Upstream PyPI name distribution — deferred pending upstream coordination (already Out of Scope)
- [ ] conda-forge Windows package — deferred until pip wheel is proven and stable
- [ ] 32-bit Windows — deferred indefinitely (no demand)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Self-contained pip wheel (MinGW) | HIGH | HIGH | P1 |
| Core htslib API bindings | HIGH | HIGH | P1 |
| samtools/bcftools dispatch | HIGH | MEDIUM | P1 |
| Indexing / region queries | HIGH | LOW | P1 |
| CRAM + htscodecs | HIGH | MEDIUM | P1 |
| Full test suite on Windows | HIGH | HIGH | P1 |
| CI Windows runner + release wheels | HIGH | MEDIUM | P1 |
| MSVC wheels | MEDIUM | HIGH | P2 |
| Remote I/O (libcurl/S3/GCS) | MEDIUM | HIGH | P2 |
| libdeflate | MEDIUM | LOW | P2 |
| 32-bit / conda / Cygwin | LOW | HIGH | P3 (reject) |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | cyvcf2 (brentp) | rust-htslib | MSYS2 packages (htslib/samtools) | Bioconda/conda-forge | Our Approach |
|---------|-----------------|-------------|----------------------------------|----------------------|--------------|
| Native Windows wheels | None — "experimental, MSYS2 only", user must build htslib first (`CYVCF2_HTSLIB_MODE=EXTERNAL`) | None — prebuilt bindings Mac/Linux only; Windows bindgen "untested" | N/A (C tools, not Python) — but ships native `.exe`s, proving the toolchain | Not available — Bioconda FAQ: "Windows is not supported" | CI-built self-contained `win_amd64` cibuildwheel wheels |
| Bundled vs external htslib | External (user-supplied) | Vendored via htslib-sys submodule | System pacman packages | N/A | Bundled in-tree sources (existing pysam design) |
| Remote I/O on Windows | Not available | Not available | Prebuilt m2w64-htslib explicitly **without** libcurl (no S3/GCS); source builds can enable it via `--enable-libcurl` | N/A | v1: disabled + documented; v1.x: Windows `LoadLibrary` loader |
| CRAM on Windows | Untested/unsupported | Requires full deps (bzip2/lzma), friction documented | Works (native samtools builds include CRAM) | N/A | Bundled htscodecs, enabled by default |
| Full command/tool surface | N/A (VCF only) | API-level only | Full samtools/bcftools exes | N/A | Full in-process dispatch, full test suite |
| CI on Windows | None | None | Yes — htslib runs "Windows/MinGW-W64 CI" on every develop commit (the strongest evidence MinGW parity is achievable) | N/A | Yes — windows-latest runner, release matrix |
| Install path for Windows users today | WSL2 / MSYS2 hand-build | WSL2 | pacman (tools only) | WSL2 / Docker | `pip install` from fork releases, then PyPI |

### How users consume Windows wheels (consumption model)

- **pip users** expect: `pip install <pkg>` (or a direct GitHub-release wheel URL / `--index-url`) resolving a `cp3x-cp3x-win_amd64` wheel, importing with zero extra steps. Windows wheel convention (unlike manylinux) permits and expects vendored DLLs — everything must be inside the wheel. There is no "system package manager" fallback on Windows; a wheel with PATH-dependent DLLs is considered broken.
- **conda users** on Windows pull from conda-forge/defaults, but **Bioconda — the recommended channel in pysam's INSTALL — does not support Windows at all** (Linux/macOS only; `conda install -c bioconda pysam` on Windows gives `PackagesNotFoundError`). So conda is not a viable primary channel for a v1 Windows port; pip is the only realistic route.
- **The status quo workaround** documented across issues and forums is WSL2 (occasionally Docker). Any native port competes with "free" WSL2, which sets the bar: the native experience must be at least as frictionless as `wsl && pip install pysam`.

### What "full feature parity" realistically means

Achievable on Windows with bundled sources: all htslib API bindings, all samtools/bcftools subcommands, BAM/SAM/CRAM/VCF/BCF/TABIX/FASTQ I/O, BAI/CSI/TBI indexing, bgzf+htscodecs compression, multithreading (htslib thread pools are platform-independent). The only genuine parity gap is remote file I/O (`http(s)://`, `s3://`, `gs://`), which is Linux-only in the current dynamic-loader design and which **every comparable project also lacks on Windows** — so shipping it disabled in v1 is parity with the ecosystem, not an embarrassment.

## Sources

- [pysam issue #575 — pysam does not install on windows (2017 meta-ticket)](https://github.com/pysam-developers/pysam/issues/575) — HIGH (primary repo)
- [pysam issue #969 — Unable to install PySam on windows](https://github.com/pysam-developers/pysam/issues/969) — HIGH
- [pysam issue #1137 — Unable to pip install pysam on Windows](https://github.com/pysam-developers/pysam/issues/1137) — HIGH
- [htslib INSTALL — Windows/MSYS2 section, configure flags for libcurl/S3/GCS](https://github.com/samtools/htslib/blob/develop/INSTALL) — HIGH (official docs)
- [htslib Windows/MinGW-W64 CI workflow](https://github.com/samtools/htslib/actions/workflows/windows-build.yml) — HIGH (proves MinGW parity is CI-maintained upstream)
- [MSYS2 package: mingw-w64-x86_64-samtools](https://packages.msys2.org/packages/mingw-w64-x86_64-samtools) — MEDIUM
- [m2w64-htslib — prebuilt Windows htslib explicitly without libcurl/S3/GCS](https://anaconda.org/tiledb/m2w64-htslib) — MEDIUM
- [Bioconda FAQ — "Windows is not supported"](https://bioconda.github.io/faqs.html) — HIGH
- [bioconda/pysam on Anaconda.org — platforms listed (no win-64)](https://anaconda.org/bioconda/pysam) — HIGH
- [cyvcf2 repo — Windows "experimental and only tested on MSYS2", EXTERNAL htslib mode, no Windows wheels](https://github.com/brentp/cyvcf2) — HIGH
- [rust-htslib README — prebuilt bindings Mac/Linux only, Windows bindgen untested](https://github.com/rust-bio/rust-htslib/blob/master/README.md) — HIGH
- [velocyto.py issue #161 — downstream project blocked by pysam on Windows](https://github.com/velocyto-team/velocyto.py/issues/161) — MEDIUM (evidence of downstream demand)
- Codebase docs: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md` (W1–W10) — HIGH (primary)

---
*Feature research for: Windows port of pysam (scientific Python package with bundled C CLI tools)*
*Researched: 2026-09-17*
