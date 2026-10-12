# SC-3 — clang-cl Fallback Evaluation Decision Record

**Plan:** 03-05 · **Requirement:** BUILD-02 (ROADMAP Phase 3 SC-3: "按研究标志完成 clang-cl 回退路径评估") · **Deliverable:** the documented decision. No toolchain is installed for this evaluation and no plan depends on clang-cl.

## 1. Decision

**cl.exe-first. clang-cl is NOT adopted for this milestone.**

The MSVC build path ships on `cl.exe`/`link.exe` (VS Build Tools, toolset 14.50
verified on this machine), driven through setuptools' vswhere auto-detection
with zero environment setup. clang-cl is recorded below as the contingency
toolchain with a concrete activation path, to be invoked only if a future
bundled-tree bump reintroduces GCC-isms the shim layer cannot absorb.

## 2. Evidence

The decision rests on an empirically enumerated error surface, not folklore:

- **The error surface is two C99 constructs plus centralized name/header
  gaps — and both constructs are already fixed.** The research-phase
  enumeration (cl.exe compiled the real bundled sources file-by-file,
  `-Wvla` full-tree scan with positive control) found exactly **one VLA**
  in the entire bundled tree (`samtools/coverage.c:233`
  `double hist_data[hist_size]`, mirrored in `coverage.c.pysam.c:235`) and
  exactly **one C99 `[static N]` array-parameter qualifier**
  (`htslib/hts_internal.h:140`). Plan 03-01 closed both under
  `#if defined(_MSC_VER)` with `#else`-verbatim arms: the VLA is
  heap-allocated (malloc + free) on the MSVC arm, POSIX never sees a
  change; the qualifier is dropped (pure optimizer hint, the 03-03 .def
  belt-and-braces precedent). Name mapping (strcasecmp ×229 class,
  fdopen/fileno/isatty, ssize_t, O_* flags, S_* constants, 64-bit off_t)
  and the four missing headers (unistd.h/pthread.h/strings.h/sys/time.h)
  live in the centralized `win32/msvc/` shim layer (`msvc_compat.h` + four
  `__GNUC__`-forwarding drop-ins + `pthread_win32.c`).
- **The live cl 14.50 compile matrix covered the hard files** (research):
  `thread_pool.c`, `samtools.pysam.c`, `bcftools.pysam.c`, `rANS_static.c`
  (SIMD paths), `win32/getopt.c`, `samtools/lz4/lz4.c`, and four
  Cython-generated `libc*.c` TUs compiled clean under `/std:c11`.
- **The full build is green on cl.exe** (plan 03-04, this phase's
  substrate): `pip install -e . --no-build-isolation` under `_venv-msvc`
  compiles and links all 13 extensions + bundled
  htslib/htscodecs/samtools/bcftools + vendored zlib/bzip2/xz/regex
  through the BUILD-03 symbol gate (llvm-nm over the emitted `.lib`
  import libraries, 1313 symbol rows parsed), with zero C4013
  implicit-declaration residue over a fresh `setup.py build`; `import
  pysam` works and the smoke test round-trips BAM data and dispatches
  samtools/bcftools. Plan 03-05 (SC-2) then ran the complete
  default-collection suite on these artifacts: **1028 passed / 15 skipped
  / 0 failed** — reconciled node-for-node against the Phase-2 baseline
  with zero MSVC-only skips (`03-SC2-RECONCILIATION.md`).
- **The two-extension cross-link probe** (research, live on this machine):
  `/DEF:` + late `/IMPLIB:` + cross-`.pyd` symbol resolution + runtime
  call all work under link.exe — the export mechanism the plan predicted
  might need clang-cl's GNU compatibility does not need it.

**Why this supersedes the prior-art claims.** theAeon's 2025 MSVC pain list
(PR #1400 thread: "Cython extension sources contain POSIX-isms unusable
under MSVC", "MSVC cannot link GCC-produced .a files", name-mangling of
data-variable exports, "samtools coverage.c uses VLAs; MSVC does not
support VLA") and teepean's reply ("AFAIK clang-cl supports VLAs") were
recorded against older pysam/htslib trees and an MSVC-Python + GCC-built-
htslib mixing strategy — our pre-registered clang-cl fallback premise. For
the 1.24 tree the premise no longer holds: the VLA count is one (fixed),
the POSIX-ism storm is a finite centralized mapping (built), nothing links
GCC-produced `.a` files (each toolchain compiles the whole tree, vendors
included), and the data-export problem is solved by htslib's own
`HTSLIB_EXPORT` dllexport machinery plus the dllimport consumer arm
(03-04's `hts_defs.h` decision) — not by a different compiler. The
"needs clang-cl for VLAs" argument is moot when the only VLA is gone and
MSVC never sees it.

## 3. Contingency — activation path if a future bump reintroduces unshimmable GCC-isms

If a bundled htslib/samtools/bcftools bump expands the C99/GNU-ism surface
beyond the shim's class (see triggers below), clang-cl is the fallback:

1. **Install** (both routes are **blocking-human package installs** — a
   human must verify and approve them; the executor never auto-installs a
   toolchain):
   - the "C++ Clang tools for a single component" component inside Visual
     Studio Build Tools (Installer → Modify → Individual components), or
   - LLVM via winget (`winget install LLVM.LLVM`), which puts `clang-cl.exe`
     on PATH.
2. **Compiler semantics**: clang-cl accepts VLAs and GNU statement-expression
   extensions while targeting the MSVC ABI — it consumes MSVC headers,
   emits COFF objects, and links with link.exe against the same `/IMPLIB:`
   import-library machinery this phase already built. The per-source
   `#if defined(_MSC_VER)` guards and the centralized shim apply to
   clang-cl unchanged (`_MSC_VER` is defined by clang-cl in MS-compat mode).
3. **Build-path accommodation**: setup.py's two-level dispatch keys the
   module graph on `sysconfig.get_platform()` (win-amd64 → MSVC path) and
   the flags on `compiler.compiler_type` (`msvc`). clang-cl identifies as
   `compiler_type == 'msvc'` under distutils/setuptools when invoked as
   `clang-cl`, so the existing MSVC arm — source lists, `/FI` shim,
   `/DEF:` lists, late `/IMPLIB:`, symbol gate on `.lib` — is reused
   without structural change; only the compiler executable selection
   (e.g. `CL.exe=clang-cl` env or an explicit `--compiler` wrapper) and a
   re-audit of the warning surface differ.

## 4. Revisit triggers

Re-open this decision when a bundled-tree bump (or a vendored-dep bump)
introduces any of:

- **new VLAs** beyond a count the `#else`-verbatim heap-fix pattern can
  absorb economically (each VLA costs one guarded per-source edit; a
  diffuse return of stack-allocated variable arrays favors clang-cl's
  native support);
- **GNU statement expressions** (`({ ... })`), **nested functions**, or
  `__attribute__`-dependent control flow that cannot be expressed as a
  header-level mapping;
- any construct that would require editing more than a handful of bundled
  sources per bump (the single-place discipline's own threshold).

Until one of these fires, cl.exe remains the wheel toolchain (PROJECT.md
decision: wheels ship MSVC-only), and clang-cl stays a documented,
uninstalled contingency.
