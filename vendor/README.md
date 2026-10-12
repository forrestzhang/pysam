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
| vendor/regex | musl libc (regex subset) | 1.2.6 | https://musl.libc.org/releases/musl-1.2.6.tar.gz | `d585fd3b613c66151fc3249e8ed44f77020cb5e6c1e635a616d3f9f82460512a` | vendor/regex/COPYRIGHT (MIT) | **NOT cross-checked — no upstream checksum published** (musl publishes only a GPG signature; no sha256/md5 file exists on musl.libc.org). Hash recorded from the official-URL download at extraction time; flagged per T-03-04, never silently trusted. |

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
  assumptions; MSVC needs `-DHAVE_STDINT_H=1 -DHAVE_INTTYPES_H=1
  -DHAVE_STDBOOL_H=1` (MSVC ships all three; without HAVE_STDBOOL_H the
  fallback `typedef unsigned char _Bool` collides with the C11 builtin).
  Include dirs:
  `-I vendor/xz/src/liblzma/api -I vendor/xz/src/liblzma/common
  -I vendor/xz/src/liblzma/check -I vendor/xz/src/liblzma/lz
  -I vendor/xz/src/liblzma/lzma -I vendor/xz/src/liblzma/delta
  -I vendor/xz/src/liblzma/simple -I vendor/xz/src/liblzma/rangecoder
  -I vendor/xz/src/common`.
  Threading is left at the default single-threaded build (no
  `MYTHREAD_VISTA`); htslib drives liblzma single-threaded through
  `lzma_stream_decoder`. Exact probe command lines proven in plan 03-02
  Task 3 are appended at the bottom of this file.

## vendor/regex (musl-derived POSIX regex)

Per 03-RESEARCH Q2/A3 (adopted): the MSVC path vendors musl 1.2.6's
regcomp/regexec implementation (MIT) because htslib's filter expressions
(`hts_expr.c:37`, `sam.c:39` — unconditional `#include <regex.h>`) need real
POSIX BRE/ERE semantics (`REG_EXTENDED`, `REG_NOSUB`, `regerror` strings) that
MSVC has no native provider for. TRE (LGPL, what htslib-msvc pulls via vcpkg)
remains the documented fallback if filter tests disagree in plan 03-05.

Files and their provenance state:

| File | State |
|------|-------|
| regcomp.c, regerror.c, tre-mem.c, COPYRIGHT | **byte-identical** to musl 1.2.6 (`src/regex/*`, top-level `COPYRIGHT`) |
| regexec.c | **one compat edit** — `pmatch[restrict]` array-parameter qualifier dropped (see below) |
| tre.h | **one compat edit** — ALIGN macro's `(long)` casts widened to `(size_t)` (see below) |
| regex.h | **adapted** — the only header adaptation; see below |
| locale_impl.h | **vendored shim** (not upstream content) — see below |

MSVC compile defines (recorded for plan 03-03): `-D hidden= -D RE_DUP_MAX=255
-D CHARCLASS_NAME_MAX=14` — `hidden` is musl's visibility macro (used on 3
declarations in tre.h; empty is correct for a static compile), and
RE_DUP_MAX/CHARCLASS_NAME_MAX live in musl's `include/limits.h` extensions
(values from musl 1.2.6 limits.h lines 85/81; a cross-check of all 112 musl
limits.h macros against the vendored TUs shows no other missing ones).

- `regfree` is *not* a separate TU in musl 1.2.6: it is defined inside
  `regcomp.c` (regfree coverage therefore present in-TU). `tre-mem.c` is the
  fourth required TU (`regcomp.c` calls the `tre_mem_*` allocator 37 times).
  `fnmatch.c`/`glob.c` in the same upstream directory are unrelated APIs and
  were not vendored.

- **regex.h adaptation** (upstream `include/regex.h` includes the
  musl-internal `<features.h>` + `<bits/alltypes.h>`, the latter generated
  per-arch at musl build time): replaced by `#include <stddef.h>` (size_t) +
  `typedef long regoff_t;` — exactly musl's x86_64 definition
  (`TYPEDEF _Addr regoff_t`, `_Addr` = `long`). Everything below the
  adaptation marker is byte-identical to upstream.

- **regexec.c compat edit** (genuine MSVC compiler gap, 03-02 Task 3): the
  `regexec` definition used the C99/C11 array-parameter qualifier
  `regmatch_t pmatch[restrict]` — the same MSVC-rejected construct class as
  htslib/hts_internal.h's `[static N]` (dropped in 03-01). Changed to the
  empty-bracket form `pmatch[]`, which decays to the same `regmatch_t *`
  as regex.h's prototype. Pure aliasing hint; no semantic change.

- **tre.h compat edit** (genuine MSVC/LLP64 gap, 03-02 Task 3): the ALIGN
  macro cast pointers to `long` — 32-bit on win64, so the casts truncated
  64-bit heap pointers (C4311). Widened to `(size_t)` (64-bit on both
  musl's LP64 target and win64; on musl size_t == unsigned long, so the
  arithmetic there is unchanged). Same modulo math otherwise.

- **locale_impl.h shim**: upstream `regerror.c` includes musl's internal
  `locale_impl.h` solely for `LCTRANS_CUR(s)`, whose default C-locale
  behavior upstream is the identity function (the weak `__lctrans_impl`
  dummy in `src/locale/__lctrans.c` returns its argument unchanged). The
  shim defines `LCTRANS_CUR(msg) (msg)` and nothing else. It exists instead
  of vendoring the real header because the real one chains into `libc.h` +
  `pthread_impl.h` and the musl TLS runtime (`__pthread_self()->locale`) —
  unbuildable outside musl. Total musl-internal glue neutralized: 2 glue
  points, 0 real internal headers vendored, 0 upstream logic changes; the
  TRE fallback (LGPL implications) was therefore not triggered.

The four TUs contain no GNU extensions and no VLAs (scanned: `__attribute__`,
`__thread`, `weak_alias`, `__builtin`, `__asm__`, `__GNUC__`, variable-length
arrays — all zero hits; the one external musl macro they reference is
`hidden`, neutralized by the empty define above). Compile with
`-I vendor/regex -D hidden= -D RE_DUP_MAX=255 -D CHARCLASS_NAME_MAX=14`.
Known-benign MSVC warnings (surfaced by the probe, /W3): C4005 NDEBUG
redefinition (tre.h defines NDEBUG that distutils' default /DNDEBUG already
provides — cosmetic) and one C4267 size_t-to-int narrowing in tre-mem.c
(upstream's int-typed block accounting; sizes are small).

The UCRT64 path is NOT touched by this tree — it keeps linking the MSYS2
`-lregex` package; `vendor/regex/` exists for the MSVC module graph only.

## Proven cl-compile probe command lines (03-02 Task 3)

Run from the repo root with the MSVC-compatible interpreter
(`D:/miniconda3/python.exe`); setuptools auto-locates cl.exe (VS 2026
BuildTools 18.4.1, toolset 14.50 was used). All lines exit 0 — every listed
TU compiles clean under `/nologo /std:c11 /W3 /we4013 /utf-8`. Plan 03-03's
include wiring should copy these verbatim.

Four-tree representative set (the plan's acceptance run):

    D:/miniconda3/python.exe devtools/msvc_compile_probe.py \
      vendor/zlib/inflate.c vendor/bzip2/decompress.c vendor/regex/regcomp.c \
      vendor/xz/src/liblzma/common/common.c \
      -I vendor/zlib -I vendor/bzip2 -I vendor/regex -I vendor/xz/src/liblzma/api \
      -I vendor/xz/src/liblzma/common -I vendor/xz/src/liblzma/check -I vendor/xz/src/liblzma/lz \
      -I vendor/xz/src/liblzma/lzma -I vendor/xz/src/liblzma/delta -I vendor/xz/src/liblzma/simple \
      -I vendor/xz/src/liblzma/rangecoder -I vendor/xz/src/common \
      -D HAVE_STDINT_H=1 -D HAVE_INTTYPES_H=1 -D HAVE_STDBOOL_H=1 \
      -D hidden= -D RE_DUP_MAX=255 -D CHARCLASS_NAME_MAX=14

Full regex subset (all four TUs):

    D:/miniconda3/python.exe devtools/msvc_compile_probe.py \
      vendor/regex/regcomp.c vendor/regex/regexec.c vendor/regex/regerror.c vendor/regex/tre-mem.c \
      -I vendor/regex -D hidden= -D RE_DUP_MAX=255 -D CHARCLASS_NAME_MAX=14

xz decoder TU (stream_decoder.c, the `lzma_stream_decoder` entry htslib uses):

    D:/miniconda3/python.exe devtools/msvc_compile_probe.py \
      vendor/xz/src/liblzma/common/common.c vendor/xz/src/liblzma/common/stream_decoder.c \
      -I vendor/xz/src/liblzma/api -I vendor/xz/src/liblzma/common -I vendor/xz/src/liblzma/check \
      -I vendor/xz/src/liblzma/lz -I vendor/xz/src/liblzma/lzma -I vendor/xz/src/liblzma/delta \
      -I vendor/xz/src/liblzma/simple -I vendor/xz/src/liblzma/rangecoder -I vendor/xz/src/common \
      -D HAVE_STDINT_H=1 -D HAVE_INTTYPES_H=1 -D HAVE_STDBOOL_H=1
