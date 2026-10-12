# Vendored third-party C sources

This directory holds the compiler-neutral source trees the MSVC (cl.exe) build
path of plan 03-03/03-04 must compile from source. MSYS2-installed headers and
import libraries cannot be reused across toolchains (MSYS2's `zconf.h` includes
`unistd.h` and its import libs don't cross toolchains — 03-RESEARCH Pattern 4),
so BUILD-02's dependency closure is vendored in-tree. This also satisfies the
Phase-4 self-contained-wheel constraint. The UCRT64 path never references this
directory (it keeps linking the MSYS2 `-lz -lbz2 -llzma -lregex` packages).

## Provenance manifest

Extraction date: 2026-10-12 (all entries). Tarballs are NOT committed — only
extracted sources and license files (reviewable as diffs).

| Directory | Upstream project | Version | Origin URL | SHA-256 of tarball | License file | Cross-check status |
|-----------|------------------|---------|------------|--------------------|--------------|--------------------|
| vendor/zlib | zlib (Madler) | 1.3.2 | https://zlib.net/zlib-1.3.2.tar.gz | `bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16` | vendor/zlib/LICENSE | **cross-checked**: identical value published on https://www.zlib.net/ index page. (The zlib-announce 1.3.2 post links to zlib.net/GitHub without listing a hash; zlib.net's own index is the publication point that carried it.) |
| vendor/bzip2 | bzip2 (sourceware) | 1.0.8 | https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz | `ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269` | vendor/bzip2/LICENSE | **cross-checked on SHA-512**: publisher publishes SHA-512 only (https://sourceware.org/pub/bzip2/sha512.sum); computed SHA-512 matches the published line for 1.0.8 (`083f5e67...8a30b9f3`). SHA-256 above is our recorded value. |
| vendor/xz | XZ Utils (tukaani) | 5.8.4 | https://github.com/tukaani-project/xz/releases/download/v5.8.4/xz-5.8.4.tar.gz (linked as the official release artifact from https://tukaani.org/xz/) | `0014c7886930454fe8bd4228665b51af55eeae560ea135c9c4cd33f55b2591d9` | vendor/xz/COPYING (+ COPYING.0BSD, COPYING.GPLv2, COPYING.GPLv3, COPYING.LGPLv2.1) | **cross-checked**: identical value published as the release asset digest on the official tukaani-project/xz v5.8.4 release. |

Re-verification (offline, any machine): re-download the tarball from the origin
URL above, then `sha256sum <tarball>` and compare against vendor/HASHES.txt.

## Hygiene prune (what was removed and why)

Every tree was pruned to what a static cl compile of the library needs;
upstream license/copying files are always preserved. Removed:

- **zlib**: `CMakeLists.txt`, `BUILD.bazel`/`MODULE.bazel`, `configure`,
  `Makefile`/`Makefile.in`, `treebuild.xml`, `make_vms.com`, `zlib.3`/`.pdf`,
  `INDEX`, `FAQ`, `ChangeLog`, `doc/`, `test/`, `examples/`, `contrib/`, and
  the platform dirs `amiga/ msdos/ os400/ qnx/ watcom/ win32/` (the win32/ dir
  is zlib's own DLL project files, not needed — we compile the root .c set),
  `zconf.h.in` (configure template; the pristine pre-generated `zconf.h` is
  kept — its `unistd.h` probe is keyed on `HAVE_UNISTD_H`, which the MSVC path
  never defines).
- **bzip2**: the CLI `bzip2.c`/`bzip2recover.c`, shell wrappers
  (`bzgrep`/`bzdiff`/`bzmore` + man pages), XML/manual material, MSVC/DSP
  project files (`makefile.msc`, `*.dsp`, `libbz2.def`, `dlltest*`), test
  programs and data (`mk251.c`, `spewG.c`, `unzcrash.c`, `sample*`, `words*`).
  The bzip2 1.0.8 library is **7** TUs: blocksort.c bzlib.c compress.c
  crctable.c decompress.c huffman.c randtable.c (+ bzlib.h, bzlib_private.h).
- **xz**: autotools/cmake build machinery (`configure*`, `Makefile.*`,
  `CMakeLists.txt`, `cmake/`, `config.h.in`, `m4/`, `build-aux/`, `autogen.sh`),
  CLI trees (`src/xz`, `src/xzdec`, `src/lzmainfo`, `src/scripts`, `lib/`
  gnulib getopt), `tests/`, `po/`, `po4a/`, `debug/`, `doc/`, `doxygen/`,
  `dos/`, `extra/`, portability meta (`ABOUT-NLS`, `INSTALL*`, `PACKAGERS`),
  and the GNU-assembler files `src/liblzma/check/crc32_x86.S` +
  `crc64_x86.S` (cl cannot consume GAS syntax; the C/intrinsic fallbacks
  `crc32_fast.c`/`crc64_fast.c` cover MSVC).

Kept beyond the strict minimum:

- **xz** `src/common/`: `sysdefs.h`, `mythread.h`, `tuklib_common.h`,
  `tuklib_config.h`, `tuklib_integer.h`, `tuklib_cpucores.{c,h}`,
  `tuklib_physmem.{c,h}` — liblzma's `common/common.h` includes
  `"sysdefs.h" "mythread.h" "tuklib_integer.h"` directly and `hardware.c`
  uses the tuklib_physmem/cpucores TUs (both have native `_WIN32` arms).
  `tuklib_exit*`/`tuklib_progname*`/`tuklib_mbstr*` are CLI-only — pruned.
- **xz** `windows/` (6 files): in 5.8.4 this directory no longer ships a
  pre-provided `config.h`/MSVC project files — upstream moved MSVC builds to
  CMake (see windows/INSTALL-MSVC.txt). It is kept for its Windows-specific
  build/crt-mixing documentation (liblzma-crt-mixing.txt matters for Phase 4).

## MSVC configuration the 03-03 module graph consumes

- **zlib**: no configuration header exists. Compile the root `.c` set with
  `-I vendor/zlib`. (zlib.h/zconf.h are compiler-neutral.)
- **bzip2**: no configuration header exists. Compile the 7 library TUs with
  `-I vendor/bzip2`. Upstream `makefile.msc` proves cl compatibility.
- **xz/liblzma**: no `HAVE_CONFIG_H`. sysdefs.h falls back to direct header
  assumptions; MSVC needs `-DHAVE_STDINT_H=1 -DHAVE_INTTYPES_H=1` (MSVC ships
  both since VS2013). Include dirs:
  `-I vendor/xz/src/liblzma/api -I vendor/xz/src/liblzma/common
  -I vendor/xz/src/liblzma/check -I vendor/xz/src/liblzma/lz
  -I vendor/xz/src/liblzma/lzma -I vendor/xz/src/liblzma/delta
  -I vendor/xz/src/liblzma/simple -I vendor/xz/src/liblzma/rangecoder
  -I vendor/xz/src/common`.
  Threading is left at the default single-threaded build (no
  `MYTHREAD_VISTA`); htslib drives liblzma single-threaded through
  `lzma_stream_decoder`. Exact probe command lines proven in plan 03-02
  Task 3 are appended at the bottom of this file.
