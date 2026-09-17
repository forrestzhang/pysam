---
last_mapped_commit: 4c8486b106f36b1e1e548da5d70038d60fb95498
last_mapped_at: 2026-09-17
---
<!-- refreshed: 2026-09-17 -->

# Architecture

**Analysis Date:** 2026-09-17

## System Overview

pysam is a Python/Cython package wrapping the HTSlib C library plus the samtools
and bcftools command-line toolkits. Everything compiles into a set of C extension
modules under the `pysam` package; there is no server, no IPC, no daemon — a
single-process library architecture.

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                      Python API Layer (pure Python)                        │
│  `pysam/__init__.py`  `pysam/utils.py`  `pysam/samtools.py`  `pysam/...`   │
│  (re-exports all libc* modules; PysamDispatcher; Pileup helpers)           │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │ imports (star imports, cimports)
┌───────────────────────────────▼───────────────────────────────────────────┐
│                 Cython Extension Modules (pysam/libc*.pyx → .so/.pyd)      │
├──────────────┬──────────────┬──────────────┬───────────────┬───────────────┤
│ libchtslib   │ libcsamtools │ libcbcftools │ libcutils     │ libc* feature │
│ (htslib API  │ (patched     │ (patched     │ (dispatch to  │ modules:      │
│  wrapper +   │ samtools C   │ bcftools C   │ samtools/     │ alignmentfile,│
│  bundled     │ sources      │ sources      │ bcftools main │ alignedsegment│
│  htslib objs)│ *.pysam.c)   │ *.pysam.c)   │ + helpers)    │ bcf, tabix,   │
│              │              │              │               │ faidx, bgzf,  │
│              │              │              │               │ vcf, samfile… │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬───────┴───────┬───────┘
       │              │              │               │               │
       ▼              ▼              ▼               ▼               ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    Bundled C Sources (vendored upstreams)                  │
│  `htslib/` (incl. `htslib/cram/`, `htslib/htscodecs/`, `htslib/os/`)      │
│  `samtools/` (incl. `samtools/*.pysam.c` — patched for embedding)          │
│  `bcftools/` (incl. `bcftools/*.pysam.c` — patched for embedding)          │
└───────────────────────────────────────────────────────────────────────────┘
```

Build orchestration lives entirely in `setup.py` (806 lines), invoked via
`pyproject.toml`'s legacy setuptools backend.

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Build orchestrator | configure/make htslib, defines 12 extension modules, C99 probing, symbol-collision checks | `setup.py` |
| Upstream importer | copies upstream htslib/samtools/bcftools releases in and rewrites them as embeddable `*.pysam.c` | `devtools/import.py` |
| Output-redirection shim template | `@pysam@_`-prefixed FILE redirection API injected into vendored samtools/bcftools | `import/pysam.h`, `import/pysam.c` |
| htslib wrapper | Cython bindings for htslib structs (htsFile, bam_hdr_t, tbx_t, faidx_t, BGZF…) | `pysam/libchtslib.pyx` (+ `.pxd`) |
| samtools embedding | Compiled patched samtools C code; exports `samtools_dispatch()` etc. | `pysam/libcsamtools.pyx` (2-line stub), `samtools/*.pysam.c` |
| bcftools embedding | Compiled patched bcftools C code; exports `bcftools_dispatch()` etc. | `pysam/libcbcftools.pyx` (2-line stub), `bcftools/*.pysam.c` |
| Dispatch/utilities | `_pysam_dispatch()` runs samtools/bcftools main() in-process with stdout/stderr redirected to temp files | `pysam/libcutils.pyx` |
| Python facade | `PysamDispatcher` callables (`pysam.sort(...)`, `pysam.mpileup(...)`), `SamtoolsError` | `pysam/utils.py`, `pysam/samtools.py`, `pysam/bcftools.py` |
| Feature modules | High-level Pythonic APIs: AlignmentFile, AlignedSegment, VariantFile, TabixFile, FastaFile | `pysam/libcalignmentfile.pyx`, `pysam/libcalignedsegment.pyx`, `pysam/libcbcf.pyx`, `pysam/libctabix.pyx`, `pysam/libcfaidx.pyx` |
| Package init | Star-imports all libc* modules, aggregates `__all__`, `get_include()`/`get_libraries()` | `pysam/__init__.py` |

## Pattern Overview

**Overall:** Monolithic C-extension architecture with a "vendored + patched C
toolkit embedding" pattern. Two distinct binding strategies coexist:

1. **API binding** — Cython `.pyx` files declare htslib's C API in `.pxd` files
   and wrap them in Python classes (AlignmentFile, AlignedSegment, …).
2. **Whole-program embedding** — the entire samtools and bcftools C codebases are
   compiled into `libcsamtools` / `libcbcftools` extension modules with their
   `main()` renamed and their stdio redirected, then invoked in-process via a
   dispatch function.

**Key Characteristics:**

- Every public C symbol is namespaced. `import/pysam.h` (template, `@pysam@`
  placeholder) rewrites colliding symbols (`main_consensus`, `error`, etc.) via
  `#define`s; `devtools/import.py` rewrites `int main(` → `int samtools_main(`,
  `stderr` → `samtools_stderr`, `exit(` → `samtools_exit(` etc. in the vendored
  sources at import time.
- Extension modules link against each other in a fixed dependency order (see
  Layers); `setup.py` line 666 documents the chain.
- htslib can be built three ways controlled by `HTSLIB_MODE` env var:
  `shared` (default, one `libchtslib` extension holding htslib objects),
  `separate` (each module links `htslib/libhts.a` statically),
  `external` (link against system-installed libhts).

## Layers

**Python facade layer:**

- Purpose: user-facing API, command emulation, error types
- Location: `pysam/__init__.py`, `pysam/utils.py`, `pysam/samtools.py`, `pysam/bcftools.py`, `pysam/Pileup.py`
- Contains: pure Python; no C
- Depends on: all libc* extension modules
- Used by: end users, test suite (`tests/`)

**Cython binding layer:**

- Purpose: Python classes wrapping htslib data structures; cross-module cimports
- Location: `pysam/*.pyx` / `pysam/*.pxd` (one pair per feature)
- Contains: `cdef extern` declarations in `.pxd`, implementations in `.pyx`
- Depends on: `libchtslib` (cimported via `pysam/libchtslib.pxd`), `libcutils` helpers
- Used by: Python facade layer

**Embedded toolkit layer:**

- Purpose: samtools/bcftools executables as linkable code
- Location: `samtools/*.pysam.c`, `bcftools/*.pysam.c`, generated headers `samtools/samtools.pysam.h`, `bcftools/bcftools.pysam.h`
- Contains: full upstream C sources with mechanical rewrites (main→dispatch, stdio→FILE* redirection)
- Depends on: htslib headers/objects
- Used by: `libcsamtools`, `libcbcftools` extension builds

**Vendored htslib layer:**

- Purpose: upstream htslib C library shipped in-tree
- Location: `htslib/`, public headers `htslib/htslib/*.h`, CRAM codec `htslib/cram/`, compression codecs `htslib/htscodecs/`, OS shims `htslib/os/`
- Contains: unmodified upstream C + autotools (`configure`, `Makefile`)
- Depends on: zlib (required), bzip2/lzma/libcurl/libdeflate (optional via configure)
- Used by: everything; built by `setup.py` via `make lib-static`

**Build layer:**

- Purpose: configure htslib, write `config.h`/`config_vars.h`, assemble extension definitions
- Location: `setup.py`, `pyproject.toml`, `devtools/`, `win32/`
- Contains: setuptools `cy_build_ext` subclass, `CyExtension` (prebuild hooks), env-var-driven config

## Data Flow

### Read path (e.g., `pysam.AlignmentFile("x.bam")`)

1. User calls `pysam.AlignmentFile` — resolved via star import in `pysam/__init__.py:18` to `pysam/libcalignmentfile.pyx`
2. `libcalignmentfile.pyx` cimports htslib API from `pysam/libchtslib.pxd`; calls `hts_open()` / `sam_hdr_read()` in the bundled htslib compiled into `libchtslib`
3. Iteration calls `sam_read1()`; records materialized as `AlignedSegment` (defined in `pysam/libcalignedsegment.pyx`)
4. Index-based random access uses `sam_index_load3()` (`pysam/libcalignmentfile.pyx:1013`)

### Command emulation path (e.g., `pysam.sort("-o", "out.bam", "in.bam")`)

1. `pysam/samtools.py:50` — `sort = PysamDispatcher('samtools', 'sort')`
2. `PysamDispatcher.__call__` → `_pysam_dispatch()` in `pysam/libcutils.pyx:303`
3. `_pysam_dispatch` creates temp files, optionally rewrites args to use explicit `-o` output options (`MAP_STDOUT_OPTIONS` at `libcutils.pyx:361`), opens `/dev/null` for stdout when capturing
4. Calls `samtools_set_stdout/_set_stderr()` then `samtools_dispatch()` — the renamed `main()` of the patched samtools code compiled into `libcsamtools` (`pysam/libcsamtools.pxd`)
5. Return code + captured stderr/stdout read back from temp files; nonzero exit raises `SamtoolsError` (`pysam/utils.py:83`)

### Build path

1. `pip install .` → `pyproject.toml` legacy backend → `setup.py`
2. `setup.py:525` runs `htslib/configure` (`configure_library`), then `make -s print-config` to harvest flags
3. `setup.py:588` (HTSLIB_MODE=shared) links the htslib *object files* listed in `LIBHTS_OBJS` into `libchtslib`; `prebuild_libchtslib` (`setup.py:678`) runs `make lib-static` first
4. `config.h` is parsed into generated `pysam/config.py` (`setup.py:598`) so Python can inspect feature flags (`HAVE_LIBCURL`, `HAVE_MMAP`, …)
5. After linking, `cy_build_ext.check_ext_symbol_conflicts` (`setup.py:320`) runs `nm` on every extension and fails the build if any non-Cython symbol is defined in more than one module

### Vendoring path (developer-facing)

1. `python devtools/import.py samtools /path/to/samtools-X.Y` (`devtools/import.py:137`)
2. Copies upstream files (excluding test/misc dirs per `EXCLUDE` map), then `_update_pysam_files` rewrites each `.c` into `.pysam.c` with the stdio/main redirections and stamps versions into `pysam/version.py`, `pysam/version.h`, `README.rst`, `doc/index.rst`

**State Management:**

- No global mutable state at the Python level. At C level, the patched samtools/bcftools keep module-scope `FILE *samtools_stdout` etc. (`samtools/samtools.pysam.c`, generated from `import/pysam.c`).
- `_pysam_dispatch` is not thread-safe with respect to those global FILE handles (single dispatch at a time per process is assumed).

## Key Abstractions

**PysamDispatcher:**

- Purpose: turn every samtools/bcftools subcommand into a Python callable
- Examples: `pysam/samtools.py`, `pysam/bcftools.py`
- Pattern: one-liner instantiations `PysamDispatcher('samtools', '<cmd>')`; optional stdout parsers matched by flag combinations

**Cython module pair (.pyx/.pxd):**

- Purpose: each feature gets a `libc<name>.pyx` implementation and a `libc<name>.pxd` declaration file so other modules can `cimport` it
- Examples: `pysam/libchtslib.pyx`+`pysam/libchtslib.pxd`, `pysam/libcutils.pyx`+`pysam/libcutils.pxd`
- Pattern: `.pxd` holds `cdef extern from "<header>"` blocks; `.pyx` holds `cdef class` wrappers; companion `.pyi` stubs for type checking

**Patched C embedding (`*.pysam.c`):**

- Purpose: compile whole CLI programs into extension modules
- Examples: `samtools/bamtk.c.pysam.c` (the renamed main dispatcher), `bcftools/main.c.pysam.c`
- Pattern: mechanical regex rewriting by `devtools/import.py::_update_pysam_files` (lines 76–135); shim header `import/pysam.h` provides `@pysam@_dispatch`, `@pysam@_set_stdout`, `@pysam@_exit` etc.

**Extension dependency chain:**

- Purpose: control link order (documented at `setup.py:666-672`)
- Chain: `libchtslib` (htslib) → `libcsamtools`/`libcbcftools` (tools, link chtslib) → `libcutils` (links chtslib + csamtools + cbcftools) → feature modules (link chtslib + cutils)

## Entry Points

**Build entry point:**

- Location: `setup.py`
- Triggers: pip install, `python setup.py build`
- Responsibilities: htslib configure/make, module graph, compiler flag munging, symbol collision check

**Library entry point:**

- Location: `pysam/__init__.py`
- Triggers: `import pysam`
- Responsibilities: import order of libc* modules (chtslib first so symbols resolve), aggregate `__all__`

**Command entry point (in-process):**

- Location: `samtools_dispatch()` in `libcsamtools`, `bcftools_dispatch()` in `libcbcftools`
- Triggers: any `PysamDispatcher` call
- Responsibilities: run renamed `main(argc, argv)` with redirected stdio

**Upstream import entry point:**

- Location: `devtools/import.py`
- Triggers: manual developer run when updating bundled htslib/samtools/bcftools versions
- Responsibilities: copy + rewrite + version stamping

## Architectural Constraints

- **Threading:** CPython GIL-bound; htslib calls release the GIL where marked. No worker threads inside pysam itself. `_pysam_dispatch` mutates process-global C `FILE*` handles — not safe for concurrent dispatches.
- **Global state:** `samtools_stdout`/`samtools_stderr`/`bcftools_stdout` etc. in the generated `*.pysam.c` files; Cython module-level `ERROR_HANDLER` in `pysam/libcutils.pyx:102`.
- **Symbol uniqueness:** every extension must define disjoint global symbols; enforced post-link by `check_ext_symbol_conflicts` (`setup.py:320`). Adding a vendored file that exports a new colliding symbol breaks the build by design.
- **Link-time interdependence:** feature modules link against `libchtslib`/`libcutils` shared objects; on ELF/macOS this uses `-Wl,-rpath,$ORIGIN` (`setup.py:423`); macOS uses `@rpath/@loader_path` install names (`setup.py:401-418`). Windows has no equivalent handling.
- **POSIX assumption:** Cython sources cimport from `posix.unistd` and `posix.fcntl` (`pysam/libchtslib.pyx:10`, `pysam/libctabix.pyx:62-63`, `pysam/libcutils.pyx:22-23`), which do not exist on Windows MSVC. `_pysam_dispatch` opens literal `/dev/null` (`pysam/libcutils.pyx:~385`). `setup.py` invokes `sh configure`, `make`, and `nm` (lines 61–112).
- **Circular imports:** none at Python level; Cython cimports form a DAG rooted at `libchtslib`/`libcutils`.

## Anti-Patterns

### Hard-coded POSIX paths and APIs in dispatch code

**What happens:** `_pysam_dispatch` in `pysam/libcutils.pyx` opens `b"/dev/null"` and cimports `posix.fcntl.open`, `posix.unistd.dup/SEEK_SET/STDOUT_FILENO`; `libctabix.pyx` and `libchtslib.pyx` also cimport `posix.unistd`.
**Why it's wrong:** none of these compile on MSVC; Cython's `posix` package is POSIX-only. This blocks the Windows port directly.
**Do this instead:** gate with `DEF UNAME_SYSNAME == 'Windows'`/runtime `sys.platform` checks, use `os.devnull`, and replace `posix.*` cimports with small `cdef extern` blocks or Cython's portable `libc` modules (see `win32/unistd.h` shim already present for the C side).

### Regex-based C source rewriting as the embedding mechanism

**What happens:** `devtools/import.py::_update_pysam_files` rewrites upstream C files with ~15 regexes (`stderr` → `samtools_stderr`, ` printf(` → `fprintf(samtools_stdout,`, …) plus per-file special cases.
**Why it's wrong:** fragile against upstream code changes; any new upstream stdio pattern silently leaks through and writes to the real process stdout/stderr.
**Do this instead:** when adding vendored files, run the importer and grep the generated `.pysam.c` for un-redirected `printf`/`stderr`/`exit(`; extend `SPECIFIC_SUBSTITUTIONS` for new patterns.

### Symbol-collision whack-a-mole

**What happens:** same-named global functions across samtools/bcftools/glbc (`main_consensus`, `error`, `read_file_list`, …) are `#define`-renamed in `import/pysam.h:63-73` and occasionally rewritten via rules in `devtools/import.py`.
**Why it's wrong:** upstream renames/adds functions silently reintroduce collisions; caught only by the post-link `nm` check (skipped if `nm` is missing — e.g., on Windows).
**Do this instead:** keep `import/pysam.h` exhaustive; treat a `check_ext_symbol_conflicts` failure as a signal to add a `#define`, not to weaken the check.

## Error Handling

**Strategy:** C-level return codes converted to Python exceptions at the binding boundary.

**Patterns:**

- htslib errno captured and wrapped: `OSError_from_errno()` in `pysam/libcutils.pyx:192`
- Dispatch failures: nonzero exit status → `SamtoolsError` with captured stdout/stderr attached (`pysam/utils.py:83`)
- Region/argument validation: plain `ValueError`/`IOError` raised in Python before C calls (`pysam/libcutils.pyx:243` in `parse_region`)

## Cross-Cutting Concerns

**Logging:** htslib's `hts_log` C facility, severity controllable via the binding layer; no Python logging framework.
**Validation:** input validation at Python layer (`parse_region`, `_pysam_dispatch` argument pre-checks); C layers assume validated input.
**Authentication:** none in pysam itself; remote access (S3/GCS) delegated to htslib's libcurl code paths configured at htslib configure time.

---

*Architecture analysis: 2026-09-17*
