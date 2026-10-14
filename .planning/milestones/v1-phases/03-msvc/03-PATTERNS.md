# Phase 3: MSVC 构建系统 - Pattern Map

**Mapped:** 2026-10-12
**Files analyzed:** 13 (new + modified)
**Analogs found:** 11 / 13 (2 have no in-tree analog; use 03-RESEARCH.md verified prototypes)

All analog paths verified git-tracked this session (`git ls-files` non-empty, 19/19). Line numbers refer to the current `win` branch working tree. Exception noted in-place: `htslib/config.h` is an **untracked** configure artifact (the live UCRT64 output) — it is the curation *base* for `win32/config.h.msvc`, read this session, but the durable analog is 03-RESEARCH.md's curation recipe.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `setup.py` (gate restructure + compiler_type=='msvc' branch + D-17 implib fix + c99 probe skip) | build config (setuptools) | n/a (build orchestration) | itself — win32 branch skeleton at :526-554, gate :53-77, c99 probe :435-449 | exact (self-referential edit) |
| `win32/config.h.msvc` (NEW) | config (pre-baked header) | n/a | `htslib/config.h` (live UCRT64 configure output — curation base, untracked working-tree artifact) + 03-RESEARCH.md "config.h.msvc curation recipe" | role-match (no tracked pre-baked config exists) |
| `win32/msvc/msvc_compat.h` + `unistd.h`/`strings.h`/`sys/time.h`/`pthread.h` (NEW) | shim headers | n/a (compile-time) | `pysam/libcport.pxd` `cdef extern from *` `#ifdef _WIN32` switch (same centralized-mapping design, Cython layer) + `win32/getopt.c` vendored-shim precedent in `win32/` | role-match |
| `win32/msvc/pthread_win32.c` (NEW) | shim implementation (C) | event-driven (threads/conds) | `win32/getopt.c` (drop-in POSIX-API implementation compiled as part of build) + 03-RESEARCH.md Pattern 4 bounded surface | role-match |
| `win32/chtslib_exports.def` (NEW) | config (linker exports) | n/a | 03-RESEARCH.md Pattern 3 verified `/DEF:xlink.def` probe (no in-tree .def) | prototype |
| `import/pysam.c` (D-20 template sync + `_MSC_VER` compiler gate) | code template | n/a (codegen source) | `samtools/samtools.pysam.c:84-105` (the existing `_WIN32 __builtin_setjmp` branch this template must absorb) | exact |
| `samtools/coverage.c:233` + `samtools/coverage.c.pysam.c:235` (VLA point fix) | C library code | transform (histogram) | Phase 2 `#ifdef`-guard + `#else`-verbatim idiom (02-PATTERNS.md "htslib C conditional-compilation guards", from `htslib/hfile.c:753-756, 792-794`) | exact idiom |
| `htslib/hts_internal.h:140` (`[static N]` point fix) | C header | n/a | same guard idiom | exact idiom |
| `htslib/hts_expr.c:37` / `htslib/sam.c:39` (regex → vendored) | C library code | request-response (filter eval) | no in-tree vendored dep; wire via `#ifdef` guard + `#else` verbatim include (same idiom), vendor dir supplies `regex.h` | prototype + idiom |
| `vendor/` zlib/bzip2/lzma/regex sources (NEW) | vendored library sources | streaming (codec) | no in-tree analog (supply-chain rule: official tarballs + recorded SHA-256, per 03-RESEARCH Security Domain); structure decided by planner (`vendor/` vs `win32/deps/`) | none |
| `pysam/conftest_cstd.c` (C99 probe rewrite/portability) | build probe source | n/a | itself — current :1-11 (the unistd.h+optind content that must become MSVC-safe or be skipped via `/std:c11`) | exact (self-referential) |
| `devtools/` MSVC rebuild-discipline doc/script (NEW) | dev tooling doc | n/a | `devtools/msys2-bootstrap.sh` (structure: gate → sanity → install → venv → canonical build → acceptance gate) | role-match |
| `pysam/libcport.pxd` (verification only; possible cl-compat tweak) | Cython declaration layer | n/a | itself — current :36-114 (research-verified cl-clean) | exact |

## Pattern Assignments

### `setup.py` (build config — the phase's main edit site)

**Analog:** itself (Phase 1 win32 skeleton, decision-ID comment style). All four edit sites verified this session:

**Edit site 1 — UCRT64 fail-fast gate (:53-77).** Current gate rejects the MSVC python outright (Pitfall 2). Restructure on `os.name == 'nt'`: `mingw*` platform → existing message verbatim; `win32`/`win-amd64` → MSVC path with its own actionable fail-fast naming "Visual Studio Build Tools with the C++ workload (2022 or later)" (never a VS-version path — Pitfall 1). Keep the comment style:
```python
# Official MSYS2 detection snippet (mingw sysconfig platform) plus an
# MSYSTEM belt-and-braces check. POSIX platforms are never gated.
def _is_ucrt64_python():
    if os.name != 'nt':
        return True
    return (sysconfig.get_platform().startswith("mingw")
            and os.environ.get("MSYSTEM") == "UCRT64")
```

**Edit site 2 — build_extension win32 branch (:526-554).** The GNU-ld flags here are unconditional today; they must become `compiler_type == 'mingw32'`-gated, with a parallel `'msvc'` arm (no `-Wl,*` at all; exports via `HTS_BUILDING_LIBRARY` + `/DEF:win32/chtslib_exports.def`; implib via late `/IMPLIB:`). Current code to split:
```python
        elif sys.platform == 'win32':
            # PE binaries have no ELF rpath; only ensure the flag list exists.
            if not ext.extra_link_args:
                ext.extra_link_args = []
            ...
            mod = ext.name.rsplit('.', 1)[-1]
            implib = os.path.join(
                "pysam",
                os.path.splitext(mod + suffix)[0] + ".dll.a")
            ext.extra_link_args.append("-Wl,--export-all-symbols")
            ext.extra_link_args.append(
                "-Wl,--exclude-symbols="
                + ":".join(sorted(WIN32_GETOPT_EXEMPT_SYMBOLS)))
            ext.extra_link_args.append("-Wl,--out-implib," + implib)
```
**D-17 fix (applies to BOTH arms):** the `"pysam"` literal above is the bug — out-of-tree, `get_ext_fullpath` points at `build\lib...\pysam\` while the implib lands in the source tree. Replace with the research-verified shape in both arms (`.dll.a`/mingw, `.lib`+`/IMPLIB:`/msvc):
```python
            implib = os.path.join(
                os.path.dirname(self.get_ext_fullpath(ext.name)),   # D-17
                os.path.splitext(mod + suffix)[0] + ".dll.a")
```
Why the dirname works: `common_options` (:915-922) puts `abspath("pysam")` in every extension's `library_dirs`, and `build_extension` appends `build_lib/pysam` when not inplace (:505-506) — the dirname is always one of those two.

**Edit site 3 — symbol-gate probe (:401-409).** Extension-selection is D-17's other half:
```python
            objfile = self.get_ext_fullpath(ext.name)
            if sys.platform == 'win32':
                objfile = os.path.splitext(objfile)[0] + ".dll.a"
```
→ `".lib" if compiler_type == 'msvc' else ".dll.a"` (llvm-nm parses MSVC .lib — research-verified). Keep the never-vacuous guard (:413-419) and D-14 exemption loop (:422-429) untouched (getopt isolation is per-tool-extension private copies under MSVC too — compile `win32/getopt.c` into each tool ext, D-16 analogue).

**Edit site 4 — c99 probe (:435-449).** `c99_compile_args()` compiles `pysam/conftest_cstd.c` which `#include <unistd.h>` and uses `optind` (verified content, see below) — fails under cl for every candidate. MSVC arm: skip the probe, return `["/std:c11"]` (+ `/utf-8` per Pitfall 7). The `-Wno-*` block (:796-801) already sits in the POSIX else-branch — mirror that gating for the new MSVC flags.

**Module-graph dispatch (module level).** Follow the existing top-level branches as the shape: the configure call (:661-675), `run_make_print_config` harvest (:679-688), and `htslib_objects` (:724-725) are the three autotools touchpoints the MSVC branch must short-circuit (write `htslib/config.h` from `win32/config.h.msvc`; hard-code the LIBHTS_OBJS-mirror dict; append htslib/htscodecs/cram/vendor sources to libchtslib). `pysam/config.py` generation (:734-756) regex-parses `#define` lines — unchanged by the MSVC file (same format). The `if platform.system() == 'Windows':` block (:770-791) is the precedent for where include-dirs/macros per-platform decisions live; its `win32/getopt.c stays for the upcoming MSVC path` comment (:777-779) already pre-registers this phase.

### `win32/config.h.msvc` (NEW — pre-baked htslib config)

**Analog:** live `htslib/config.h` (UCRT64 configure output, read in full by research; untracked working-tree artifact). No tracked pre-baked config exists in-tree — use 03-RESEARCH.md "config.h.msvc curation recipe" verbatim (Keep: HAVE_LIBZ/LIBBZ2/LIBLZMA/LZMA_H, inttypes/stdint/stdio/stdlib/string/sys_stat/sys_types headers, SIMD keys, PACKAGE_*, _FILE_OFFSET_BITS 64; Undef: HAVE_ATTRIBUTE_CONSTRUCTOR, HAVE_BUILTIN_CPU_SUPPORT_SSSE3, HAVE_DECL___CPUID_COUNT/__GET_CPUID_MAX, HAVE___BUILTIN_CLZ/__BUILTIN_PREFETCH, HAVE_CLOCK_GETTIME_CPUTIME, HAVE_GETPAGESIZE, HAVE_UNISTD_H, HAVE_STRINGS_H, HAVE_SYS_PARAM_H, _XOPEN_SOURCE, ENABLE_GCS/PLUGINS/S3, HAVE_LIBCURL). Deterministic rewrite into `htslib/config.h` every MSVC build (Pitfall 8 — alternation with UCRT64 is safe because both paths rewrite it).

### `win32/msvc/` shim layer (NEW — msvc_compat.h + 4 drop-in headers + pthread_win32.c)

**Analog A (design):** `pysam/libcport.pxd:36-99` — the project's own centralized `#ifdef _WIN32 / #else` platform-mapping switch. Copy its comment discipline (docstring explaining why the switch lives in exactly one place) and its macro-mapping shape:
```c
    #ifdef _WIN32
    ...
    #define psam_dup(fd)            _dup(fd)
    ...
    #else
    ...
    #define psam_dup(fd)            dup(fd)
    ...
    #endif
```
**Analog B (drop-in precedent):** `win32/getopt.c` — the surviving vendored POSIX-API shim in `win32/` (namespace-clean header guard `#ifndef _NO_PROTO`, compiled as an ordinary build source, license header preserved). New headers follow the research's `__GNUC__`-forwarder guard (include order puts `/I` dirs before system dirs for BOTH toolchains — the forwarder arm is what keeps UCRT64 builds byte-identical):
```c
#if defined(__GNUC__)
#include_next <unistd.h>
#else
/* MSVC body */
#endif
```
Content scope is fully enumerated in 03-RESEARCH.md Pattern 4 (the empirically verified gap table: ssize_t via `<BaseTsd>`, strcasecmp→_stricmp ×229, `PTHREAD_CREATE_JOINABLE`, `M_LN10` behind `_USE_MATH_DEFINES`, S_ISREG/S_ISDIR, gettimeofday/mkstemp/usleep bodies in pthread_win32.c). pthread surface is bounded: ~14 functions, CRITICAL_SECTION (natively recursive — thread_pool.c:755-758 requires it), CONDITION_VARIABLE (timedwait via gettimeofday→relative ms), INIT_ONCE, FlsAlloc; `pthread_kill` (thread_pool.c:1135) = no-op stub returning 0.

### `win32/chtslib_exports.def` (NEW — supplementary exports)

**Analog:** none in-tree; the shape is the research session's verified probe (`Extension("aclib", extra_link_args=["/DEF:xlink.def", "/IMPLIB:msvcdir\\aclib.lib"])` → cross-.pyd call returned 84). Keep it MINIMAL — only the enumerated un-annotated gaps (`hts_lib_shutdown`, `hts_free`, `hts_opt_add/apply/free`, `hts_parse_format`, `hts_parse_opt_list`); dllexport + /DEF union-export, drift self-detects as LNK2001 (research Anti-Pattern: do not hand-maintain a full .def). The export machinery itself is htslib's own, already tracked:
```c
// htslib/htslib/hts_defs.h:127-132
#if defined(_WIN32) || defined(__CYGWIN__)
#if defined(HTS_BUILDING_LIBRARY)
#define HTSLIB_EXPORT __declspec(dllexport)
#else
#define HTSLIB_EXPORT
#endif
```
(the MSVC branch merely adds `-DHTS_BUILDING_LIBRARY` to libchtslib's compile args; `htslib/hts_expr.c:28` already does this in-file).

### `import/pysam.c` (D-20 template sync + compiler gate)

**Analog:** `samtools/samtools.pysam.c:84-105` — the exact branch to absorb into the template. Current template (plain setjmp, no `_WIN32` arm) at `import/pysam.c:59-83`:
```c
static jmp_buf @pysam@_jmpbuf;
static int @pysam@_status = 0;

int @pysam@_dispatch(int argc, char *argv[])
{
  ...
  if (setjmp(@pysam@_jmpbuf) == 0)
    return @pysam@_main(argc, argv);
  else
    return @pysam@_status;
}

void @pysam@_exit(int status)
{
  @pysam@_status = status;
  longjmp(@pysam@_jmpbuf, 1);
}
```
Target form (from samtools.pysam.c:84-105), with the D-20(b) compiler gate — `_WIN32` alone is insufficient because `__builtin_*` compiles under cl via implicit-declaration warning and detonates at LINK:
```c
#if defined(_WIN32) && !defined(_MSC_VER)
  if (__builtin_setjmp(@pysam@_jmpbuf) == 0)
  ...
  __builtin_longjmp(@pysam@_jmpbuf, 1);
#else
  if (setjmp(@pysam@_jmpbuf) == 0)
  ...
  longjmp(@pysam@_jmpbuf, 1);
#endif
```
Apply the same gate shape to the existing generated `samtools.pysam.c`/`bcftools.pysam.c` (upgrade their bare `#ifdef _WIN32`). The generated twins must be edited in lockstep with the template (next `devtools/import.py` run would silently revert template-only fixes — research Anti-Pattern). While there: the W10 `fdopen` shim noted in 02-PORT01-CHECKLIST (line "open for Phase 3: add `fdopen`→`_fdopen` mapping") lands in the same template files via `#ifdef _MSC_VER` one-liner in the compat header.

### `samtools/coverage.c:233` + mirror (VLA point fix)

**Analog idiom:** Phase 2's `#ifdef`-guard + `#else`-verbatim form (02-PATTERNS.md, from `htslib/hfile.c`). The site (verified):
```c
    // Calculate histogram that contains percent covered
    double hist_data[hist_size];
```
Fix in BOTH files (`coverage.c:233` and `coverage.c.pysam.c:235`): heap-allocate under `#if defined(_MSC_VER)` (malloc `hist_size * sizeof(double)` + free; upstreamable-on-all-platforms variant is the planner's call). Only VLA in the tree (GCC `-Wvla` full scan, positive-control verified).

### `htslib/hts_internal.h:140` (`[static N]` point fix)

Same guard idiom (or plain keyword drop — it's a pure optimizer hint; either is upstreamable). Verified site:
```c
static inline int find_file_extension(const char *fn, char ext_out[static HTS_MAX_EXT_LEN])
```
Unblocks bgzf.c, hts.c, cram_io.c (all three error only here — research-verified).

### `htslib/hts_expr.c:37` / `htslib/sam.c:39` (POSIX regex wiring)

The unconditional `#include <regex.h>` (hts_expr.c:37, verified verbatim) resolves to the vendored `regex.h` via include dirs on the MSVC path — prefer that over editing these files; if a guard is needed, use the same `#ifdef` + `#else`-verbatim form. UCRT64 path must stay byte-identical (its `-lregex` already works).

### `pysam/conftest_cstd.c` (C99 probe)

Current content in full (verified — the `unistd.h` + `optind` is what breaks cl):
```c
#include <string.h>
#include <unistd.h>

// C++-style comment; for-decl; optind

int main(int argc, char **argv) {
    int sum = 0;
    for (int i = optind; i < argc; i++)
        sum += strlen(argv[i]);
    return sum;
}
```
Preferred fix is no file change at all: gate `c99_compile_args()` to skip under `compiler_type == 'msvc'` and force `/std:c11` (research Pattern 6). If the probe is kept portable instead, replace `unistd.h`+`optind` with ISO-C-only constructs — but do not let the probe run unmodified under cl ("cannot compile C99" abort, Pitfall 3).

### `devtools/` MSVC rebuild-discipline artifact (NEW)

**Analog:** `devtools/msys2-bootstrap.sh` — copy its structure point for point: header comment stating manual prerequisites + single-source-of-truth relationship to setup.py's fail-fast message (D-03/D-13 mirror), environment gate, sanity checks, venv creation, canonical build command, acceptance gate (`devtools/smoke_test.py` reuse), troubleshooting section (rebuild/clean incantations). MSVC content per research Pattern 7: no vcvars needed (setuptools `_get_vc_env`), one venv per toolchain (`_venv-msvc` from miniconda 3.13.5), `export PATH="/c/msys64/ucrt64/bin:$PATH"` for llvm-nm, `--inplace --force` after htslib C edits, config.h alternation note (Pitfall 8), gcc probes only inside the MSYS2 shell.

### `pysam/libcport.pxd` (verification-only)

Research-verified cl-clean as-is (`_open` family are UCRT standard functions; fixed-arity macros were designed for MSVC's preprocessor — see the file's own docstring, :32-33). No planned edits; treat any cl-compat tweak as a contingency. Do NOT restructure it in this phase.

## Shared Patterns

### Platform + compiler two-level gating
**Source:** `setup.py:53-77, 95-103, 526-554, 770-791`
**Apply to:** every setup.py edit this phase
Module graph keyed on `sysconfig.get_platform()` at top level (`mingw*` vs `win-amd64`); flags keyed on `self.compiler.compiler_type` inside `cy_build_ext` (`'msvc'` vs `'mingw32'` under the existing `sys.platform == 'win32'` arm). Every new branch carries a decision-ID comment (house style since Phase 1 — e.g. the D-14 comment block at setup.py:130-140).

### `#ifdef` guard + `#else` verbatim (zero-regression form)
**Source:** `samtools/samtools.pysam.c:84-105` (existing `_WIN32/#else` in-tree); `htslib/hfile.c:753-756, 72-794` (capability-guard variant)
**Apply to:** import/pysam.c, coverage.c ×2, hts_internal.h, any htslib touch
POSIX bytes never change; new arms add Windows behavior inside `#if`. GCC-builtin sites use `#if defined(_WIN32) && !defined(_MSC_VER)` (Pitfall 9 — implicit-declaration masks link bombs under cl).

### Template/generated lockstep
**Source:** `import/pysam.c` ↔ `samtools/samtools.pysam.c` / `bcftools/bcftools.pysam.c` (D-20)
**Apply to:** every `.pysam.c` edit
Any fix must land in the template AND both generated twins or the next `devtools/import.py` run silently reverts it.

### Fail-fast messages mirror the bootstrap script (D-03/D-13)
**Source:** `setup.py:60-77` ↔ `devtools/msys2-bootstrap.sh:19-23`
**Apply to:** the new MSVC gate message + MSVC devtools doc
One source of truth, quoted package-for-package; actionable next-step commands in the message body.

### Vendoring supply-chain rule
**Source:** 03-RESEARCH.md Security Domain (no in-tree precedent)
**Apply to:** vendor/ zlib/bzip2/lzma/regex
Official release channels only (zlib.net, sourceware.org, tukaani.org, musl), recorded SHA-256, committed reviewable sources, no network at build time, license files preserved in-tree (`win32/getopt.c`'s preserved LGPL header is the local precedent for keeping upstream license text).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `vendor/` (zlib/bzip2/lzma/regex sources) | vendored C library | streaming | No vendored third-party dep tree exists in-tree yet (win32/getopt.c is a two-file shim, not a dep); use official tarballs + research's supply-chain rule; directory layout (`vendor/` vs `win32/deps/`) is a planner decision |
| `win32/chtslib_exports.def` | linker export config | n/a | No .def file in-tree; use 03-RESEARCH.md Pattern 3's verified probe shape (`/DEF:` + late `/IMPLIB:`), keep minimal (un-annotated gaps only) |

## Metadata

**Analog search scope:** `setup.py` (7 targeted range reads), `import/pysam.c`, `samtools/*.pysam.c`, `samtools/coverage.c`, `htslib/` (hts_defs.h, hts_internal.h, hts_expr.c), `pysam/` (libcport.pxd, conftest_cstd.c), `win32/getopt.c`, `devtools/msys2-bootstrap.sh`, `.planning/phases/02-portability-tests/` (02-PATTERNS.md, 02-PORT01-CHECKLIST.md)
**Files scanned:** 15 direct reads + Phase 2 pattern-map inheritance
**Tracked-source gate:** all named analogs verified via `git ls-files` (19/19 non-empty); `htslib/config.h` explicitly identified as an untracked configure artifact and cited only as the (regenerable) curation base
**Pattern extraction date:** 2026-10-12
