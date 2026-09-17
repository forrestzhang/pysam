# Architecture Research

**Domain:** Brownfield port of a Cython/C-extension Python package (pysam) with vendored autotools C libraries (htslib/samtools/bcftools) to Windows, producing distributable wheels
**Researched:** 2026-09-17
**Confidence:** MEDIUM (web corroborated by HIGH-confidence local codebase analysis in `.planning/codebase/`)

## Standard Architecture

Windows builds of C-extension packages with bundled autotools C libraries converge on one shape: **the autotools layer is short-circuited entirely on Windows; setuptools drives C compilation directly from explicit source lists against a pre-baked `config.h`.** Three established variants exist for replacing `configure`:

| Variant | Who uses it | Verdict for pysam |
|---------|-------------|-------------------|
| **Pre-baked per-toolchain `config.h` + static source list in setup.py** | Pillow (vendored libjpeg-turbo/zlib compiled from source lists with feature probes), htslib's own `LIBHTS_OBJS`-style object enumeration | **Recommended.** Maps directly onto pysam's existing `HTSLIB_MODE=shared` machinery, which already enumerates htslib objects and parses `config.h` into `pysam/config.py` |
| **Download prebuilt dep binaries, link statically** | lxml (`--static-deps` downloads prebuilt libxml2/libxslt and links statically) | Good for *external* deps (zlib) on Windows; not applicable to htslib itself, which is vendored and patched |
| **Convert library build to meson/cmake** | nanobind/meson-python ecosystem, community trend | Correct long-term direction but a big-bang rewrite of `setup.py`'s build orchestration; out of scope for this milestone |

**Explicitly rejected:** running MSYS2 autotools (`sh configure && make`) as the Windows build path inside CI. MSYS2 is the right *dev environment* and is the standard route for upstream htslib/samtools/bcftools Windows binaries (samtools issue #2064 documents a MSYS2 GitHub Actions workflow compiling all three tools into a wheel; bioconda uses `m2w64` compilers), but building wheels through a nested MSYS2 shell inside cibuildwheel adds a fragile second toolchain layer. Use MSYS2 locally to *discover* the correct flags, then bake them into setup.py.

### System Overview

```text
Windows build architecture (target state)

┌─────────────────────────────────────────────────────────────────────┐
│  PEP 517 front-end (pip / cibuildwheel on windows-latest)            │
│  Legacy setuptools backend → setup.py                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ imports
┌──────────────────────────────▼──────────────────────────────────────┐
│  Build orchestration layer (setup.py — single file, 3 platform       │
│  branches, POSIX path byte-identical to today)                       │
│                                                                      │
│  ┌─────────────────────┐  ┌───────────────────────────────────────┐ │
│  │ POSIX branch         │  │ Windows branch (NEW)                  │ │
│  │ sh configure && make │  │ 1. write pre-baked htslib/config.h    │ │
│  │ (unchanged)          │  │    (mingw variant first, msvc later)  │ │
│  └─────────────────────┘  │ 2. compile htslib+htscodecs from      │ │
│                           │    explicit source lists (mirrors       │ │
│                           │    LIBHTS_OBJS) into libchtslib.pyd     │ │
│                           │ 3. hard-coded print-config dict         │ │
│                           │ 4. cross-extension links via .lib/.dll.a│ │
│                           │    import libraries                     │ │
│                           └───────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ compiler_type dispatch
┌──────────────────────────────┴──────────────────────────────────────┐
│  Toolchain layer                                                     │
│  Phase 1: MinGW-w64 (compiler_type == 'mingw32')                     │
│           -DMS_WIN64, -static-libgcc, static winpthread, win32/ shims│
│  Phase 2: MSVC (compiler_type == 'msvc', needs ilammy/msvc-dev-cmd   │
│           in CI; -DMS_WIN64 not needed; _fdopen/_isatty/_fileno)     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ produces
┌──────────────────────────────▼──────────────────────────────────────┐
│  Runtime artifact layer                                              │
│  pysam/*.pyd — self-contained extensions, htslib + zlib statically   │
│  linked in; NO external DLL dependencies (Python 3.8+ safe DLL       │
│  loading makes this a hard requirement, not a nicety)                │
│  If external DLLs ever added (libcurl): delvewheel repair or         │
│  os.add_dll_directory() in pysam/__init__.py BEFORE libc imports     │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `setup.py` Windows branch | Replace `run_configure`/`run_make_print_config`/`prebuild_libchtslib` with: pre-baked config writer, source-list compiler, config dict | New functions alongside existing POSIX ones; selected by `sys.platform == 'win32'` at the same decision points used today |
| Pre-baked `config.h` generator | Emit `htslib/config.h` + `config_vars.h` for MinGW-w64 (then MSVC) | Python function writing the header; MinGW variant derived from an actual MSYS2 `./configure` run, checked into `win32/` as template |
| htslib source-list builder | Enumerate htslib + htscodecs + cram C files (the `LIBHTS_OBJS` equivalent) as `Extension` sources | Mirror the existing `LIBHTS_OBJS` parsing in `setup.py`; htscodecs list taken from `htslib/htscodecs.mk` transcribed to Python |
| Dual-toolchain `build_ext` subclass | Apply MinGW-only flags (`-DMS_WIN64`, `-static-libgcc`, static winpthread) vs MSVC flags, keyed on `self.compiler.compiler_type` | Canonical pattern per Cython docs; keeps one setup.py portable across unix/mingw32/msvc with no platform config files |
| Cross-extension link coordinator | Replace `-Wl,-rpath,$ORIGIN` (Linux) / install_name (macOS) with Windows import-library linking: feature modules link the `.lib`/`.dll.a` import libraries of `libchtslib`/`libcutils` | `extra_link_args` pointing at built import libs; **required** — see "Cross-extension linking is non-negotiable" below |
| Symbol-conflict checker (Windows) | Replace `nm -g -P` with `dumpbin /symbols` (MSVC) or `llvm-nm`/`objdump` (MinGW) so `check_ext_symbol_conflicts` runs on Windows | Same post-link check, new parser; today it silently skips (CONCERNS W1/tech debt) |
| Dispatch portability shim | `/dev/null` → `os.devnull`; `posix.*` cimports → `libc.msvcrt`/`libc.io` or MinGW-compatible `cdef extern` | Per CONCERNS W2/W3; shared by both toolchains |
| Wheel repair (conditional) | Vendor + mangle DLLs, patch `__init__.py` with `os.add_dll_directory` | delvewheel via `CIBW_REPAIR_WHEEL_COMMAND_WINDOWS`; ideally never needed if linking stays fully static |

## Recommended Project Structure

The port adds Windows machinery without disturbing existing layout:

```
pysam/
├── setup.py                  # + Windows branch functions (config writer, source lists,
│                             #   toolchain-dispatching build_ext); POSIX path untouched
├── win32/
│   ├── config.h.mingw        # NEW: pre-baked htslib config.h template (from real MSYS2 configure)
│   ├── config.h.msvc         # NEW: later phase
│   ├── unistd.h              # EXTEND: isatty/fileno/sleep/getpid mappings (CONCERNS W4/W7)
│   ├── getopt.c / getopt.h   # keep (still needed by bundled tools)
│   └── stdint.h              # DELETE: obsolete since MSVC 2010, risks shadowing system header
├── htslib/                   # untouched; config.h written by setup.py at build time
├── .github/workflows/
│   ├── ci.yaml               # + windows-latest matrix row (post-build-success)
│   └── release.yaml          # + kind: win, CIBW_BEFORE_BUILD_WINDOWS, delvewheel repair
└── pyproject.toml            # + [tool.cibuildwheel] windows overrides; keep POSIX hooks as-is
```

### Structure Rationale

- **Config templates live in `win32/`, not generated at build time:** configure probing on the target machine is exactly what Windows cannot do reliably. One checked-in template per toolchain, regenerated deliberately from a real configure run when the bundled htslib version changes.
- **No new build files (no meson/cmake):** the milestone constraint is zero regression on Linux/macOS; everything rides through the existing setuptools entry point.
- **`win32/` grows rather than a parallel `build-windows.py`:** the codebase map already designates `win32/` as the Windows-shim location and `setup.py:634-639` as the wiring point; extending existing seams beats inventing new ones.

## Architectural Patterns

### Pattern 1: Toolchain dispatch via `compiler.compiler_type`

**What:** Subclass `build_ext`; in `build_extensions()`, branch on `self.compiler.compiler_type` (`'unix'` / `'mingw32'` / `'msvc'`) to apply toolchain-specific compile/link flags. Platform-level concerns (source lists, config writer selection) branch on `sys.platform` earlier, at module-graph assembly time.
**When to use:** Always — this is the intended setuptools mechanism (`cygwinccompiler.py` / `_msvccompiler.py` exist precisely for this), and it is the only dual-toolchain approach that requires no Windows-only config files and cannot break POSIX builds.
**Trade-offs:** The `compiler_type` is only known at build time, not at setup.py parse time — so the *module graph* (which sources exist) must be platform-branched, while *flags* must be compiler-branched. Mixing these two levels is the main confusion hazard.

**Example:**
```python
class cy_build_ext(build_ext):
    def build_extensions(self):
        ct = self.compiler.compiler_type
        for ext in self.extensions:
            if ct == 'mingw32':
                ext.extra_compile_args += ['-DMS_WIN64', '-O2']
                ext.extra_link_args += ['-static-libgcc', '-static-libstdc++',
                                        '-Wl,-Bstatic,--whole-archive', '-lwinpthread',
                                        '-Wl,--no-whole-archive']
            elif ct == 'msvc':
                ext.extra_compile_args += ['/O2', '/wd4267']
            # 'unix': nothing — existing POSIX flags already applied elsewhere
        super().build_extensions()
```

### Pattern 2: Static-everything linking for wheels

**What:** All C dependencies (htslib objects, htscodecs, zlib, and optionally bzip2/lzma) are compiled into the extension modules directly; no external DLLs ship in the wheel.
**When to use:** First Windows port and all wheel builds. Python 3.8+ DLL resolution (bpo-36085) searches only system directories, the loading module's own directory, and `os.add_dll_directory()` entries — PATH and CWD no longer count. Static linking reduces this to a non-problem.
**Trade-offs:** Larger `.pyd` files and no independent security patching of zlib — acceptable for a fork-distributed wheel. pysam's existing `dynamic_libs.c` (dlopen of `libcurl.so.4`, Linux-only by design per CONCERNS W6) should simply stay disabled on Windows: ship `--disable-libcurl` semantics (no `http://`/`s3://`) in phase 1; a Windows variant using `LoadLibraryA`/`GetProcAddress` against `libcurl*.dll` is a later enhancement, and even then static linking libcurl is safer than runtime loading.

### Pattern 3: Cross-extension linking via import libraries (the Windows rpath replacement)

**What:** pysam's Linux/macOS build relies on `-Wl,-rpath,$ORIGIN` so feature modules resolve htslib/cutils symbols from sibling `.so` files. Windows has no rpath. The equivalent: when `libchtslib.pyd` is linked, the toolchain emits an import library (`libchtslib.lib` for MSVC, `libchtslib.dll.a` for MinGW); feature modules add that import lib to `extra_link_args`/`libraries`.
**When to use:** Mandatory for `HTSLIB_MODE=shared` semantics on Windows — and shared semantics ARE mandatory: feature modules cimport htslib types from `libchtslib.pxd` and share `htsFile*` pointers with it. The `separate` mode (static `libhts.a` per module) would give each `.pyd` its own htslib copy and break struct/file-handle sharing across module boundaries.
**Trade-offs:** Adds build-order sensitivity (chtslib import lib must exist before feature modules link — setuptools' topological handling of inter-extension deps is weak, so pysam's existing fixed extension ordering at `setup.py:666-672` must be enforced explicitly, e.g. by building in two passes). This is the single most under-appreciated structural difference between the POSIX and Windows builds.

### Pattern 4: Phased port — build, then runtime, then CI, then second toolchain

**What:** Sequence the port in four strictly ordered stages, each independently verifiable: (A) build system produces an importable `pysam` on a dev machine; (B) full test suite passes on Windows; (C) CI produces and tests wheels on `windows-latest` via cibuildwheel; (D) MSVC toolchain support alongside MinGW.
**When to use:** Always for brownfield ports; each stage has different failure modes and tooling (respectively: compiler/config, POSIX-ism cleanup, packaging/CI, ABI diversification).
**Trade-offs:** Defers MSVC — but MSVC and MinGW share ~80% of the work (source lists, config.h structure, Cython fixes, dispatch shims), and MSVC adds its own surface (`_fdopen`/`_isatty`/`_fileno` naming, no `unistd.h` at all, stale `win32/` shims per CONCERNS W7/W10, `ilammy/msvc-dev-cmd` in CI). Cython `.pyx` fixes should be written toolchain-neutrally (portable `libc` cimports or `DEF`-gated blocks) so phase D is mostly build wiring, not source changes.

## Data Flow

### Build-time flow (Windows)

```
pip wheel .
    │
    ▼
setup.py module execution
    │ sys.platform == 'win32' branch (NEW; POSIX branch untouched)
    ▼
write_config_header('mingw') ──► htslib/config.h + config_vars.h   (was: sh configure)
    │
    ▼
assemble module graph: 12 CyExtension definitions, htslib sources inlined
into libchtslib sources list (mirrors LIBHTS_OBJS + htscodecs list)
    │
    ▼
cy_build_ext.build_extensions()
    │ compiler_type == 'mingw32' → MinGW flags; 'msvc' → MSVC flags
    ▼
link pass 1: libchtslib.pyd  +  libchtslib.dll.a (import lib emitted)
    │
    ▼
link pass 2: libcsamtools/libcbcftools/libcutils against libchtslib import lib;
feature modules against libchtslib + libcutils import libs
    │
    ▼
check_ext_symbol_conflicts via llvm-nm/dumpbin (was: nm; previously skipped on Windows)
    │
    ▼
parse pre-baked config dict ──► pysam/config.py   (was: regex-parse htslib/config.h)
```

### Runtime DLL-resolution flow (import pysam)

```
import pysam
    │
    ▼
pysam/__init__.py
    │ (only if external DLLs ever ship: os.add_dll_directory(<pkg dir>) — must run
    │  BEFORE any libc* import; ideally unnecessary under Pattern 2)
    ▼
import pysam.libchtslib  (.pyd loaded by full path; dependencies = system DLLs only,
    │                      because everything else is statically linked inside)
    ▼
import remaining libc* modules in fixed order (chtslib first — existing invariant)
```

### Key Data Flows

1. **Configure knowledge flow (one-time, developer-run):** real MSYS2 `./configure` in `htslib/` → harvested `config.h` → transcribed to `win32/config.h.mingw` template → written verbatim by setup.py on every Windows build. Same future path for MSVC.
2. **Symbol-contract flow:** `import/pysam.h` renames + `check_ext_symbol_conflicts` enforcement — unchanged in intent on Windows, only the symbol-reading tool changes (`nm` → `llvm-nm`/`dumpbin`). The check must NOT stay silently disabled on Windows (today it is, per CONCERNS W1), because duplicate non-static symbols across `.pyd` files cause wrong-function crashes at runtime, not link errors.
3. **Interop flow (unchanged):** Cython `.pxd` cimports form the same DAG rooted at `libchtslib`/`libcutils`; Windows changes how symbols resolve at link/load time, not the module dependency graph.

## Build Order Implications (for roadmap phasing)

| Order | Component | Depends on | Why |
|-------|-----------|------------|-----|
| 1 | `win32/config.h.mingw` + setup.py config-writer branch | Nothing (needs one MSYS2 configure run to harvest) | Unblocks everything; replaces the two uncaught `make`/`configure` calls that abort setup.py import (CONCERNS W1) |
| 2 | htslib/htscodecs source-list builder | 1 | libchtslib cannot compile without both config.h and the source enumeration |
| 3 | Dual-toolchain `build_ext` + cross-extension import-lib linking (Pattern 1+3) | 2 | All 12 modules; enforces two-pass link ordering (chtslib → tools/utils → features) |
| 4 | Cython portability fixes (`posix.*` cimports, `/dev/null`, `isatty`/`fileno`) | Can proceed in parallel with 1–3 (different files) | Blocks only module *compilation*, not build orchestration; toolchain-neutral fixes keep phase D cheap |
| 5 | Runtime/test pass: dispatch shims, test-suite POSIX-ism cleanup (CONCERNS W3/W9), symbol-check via llvm-nm | 3+4 | Success criterion per PROJECT.md: full test suite green |
| 6 | CI + wheels: `windows-latest` matrix, `CIBW_BEFORE_BUILD_WINDOWS`, delvewheel repair slot, GitHub Releases fork channel | 5 | cibuildwheel tests each wheel in an isolated venv; only meaningful once tests pass |
| 7 | MSVC toolchain (second config template, `ilammy/msvc-dev-cmd`, `_fdopen`/`_isatty`/`_fileno` mapping, `win32/` shim modernization) | 6 (MinGW wheels shipping) | Shared 80% with MinGW; standalone ABI verification needed |

## Scaling Considerations

Library-scale, not service-scale; "scaling" here means matrix breadth (Python versions × toolchains × arches).

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 toolchain, 1 Python, dev machine | Everything above; manual MSYS2 environment |
| 2 toolchains (MinGW+MSVC), 4–5 CPython versions, CI matrix | Config templates per toolchain; cibuildwheel `CIBW_BUILD` pins; wheel-test per build |
| Python-version coverage parity with upstream + ARM64 Windows | ARM64 needs its own MinGW/MSVC config template and CI runner (`windows-11-arm`); consider meson/cmake conversion if setup.py branches become unmaintainable |

### Scaling Priorities

1. **First bottleneck:** setup.py's growing platform-branch complexity — mitigated by keeping each Windows function small and POSIX-path-pure; the moment flags leak across branches, regressions on Linux/macOS follow.
2. **Second bottleneck:** per-toolchain config.h drift when bundled htslib is re-imported via `devtools/import.py` — mitigated by a `devtools/` check script asserting `win32/config.h.*` templates still match what configure would produce (or at minimum, documenting the harvest procedure).

## Anti-Patterns

### Anti-Pattern 1: Running MSYS2 autotools as the CI wheel-build path

**What people do:** Install MSYS2 in CI, run `sh configure && make` inside it, and wrap the artifacts into wheels.
**Why it's wrong:** Two nested toolchain layers (MSYS2 shell + Python's compiler selection), opaque flag harvesting, and cibuildwheel integration hacks. It works for producing upstream samtools *binaries* (samtools #2064) but fights the PEP 517 build model that wheels require.
**Do this instead:** Use MSYS2 once, locally, to harvest `config.h` and flags into checked-in templates (Pattern 2 of configure replacement); let setuptools compile the sources natively.

### Anti-Pattern 2: Keeping the symbol-collision check disabled on Windows

**What people do:** Let `check_ext_symbol_conflicts` keep silently skipping because `nm` is absent (current behavior, CONCERNS W1).
**Why it's wrong:** On Windows, duplicate non-static symbols across `.pyd` modules don't fail the link — they cause subtle wrong-function crashes at runtime, exactly the failure class the check exists to catch.
**Do this instead:** Port the checker to `llvm-nm` (MinGW) / `dumpbin /symbols` (MSVC) in the same phase as the build-system port, before the test suite relies on it.

### Anti-Pattern 3: Per-toolchain `#ifdef` sprawl in Cython sources

**What people do:** Fix each `posix.*` cimport with a tangle of `IF UNAME_SYSNAME == 'Windows'` blocks per call site.
**Why it's wrong:** Three modules (`libchtslib`, `libcutils`, `libctabix`) already cimport posix APIs; duplicated inline gating is unmaintainable and doubles again for MSVC differences.
**Do this instead:** Centralize: one small `pysam/libcport.pxd` (or extend `win32/` shims for the MinGW path) providing portable declarations, with the platform switch in exactly one place per function family.

### Anti-Pattern 4: Shipping external DLLs next to the .pyd without a loading strategy

**What people do:** Drop `zlib.dll`/`libcurl.dll` into the package directory and assume they'll be found.
**Why it's wrong:** Python 3.8+ removed PATH/CWD from DLL resolution; the package dir is searched only for the loaded module's own directory, and same-named DLL collisions across packages have *unspecified* search order (Autodesk maya-usd #2859).
**Do this instead:** Statically link everything possible (Pattern 2). If a DLL must ship, repair with delvewheel (mangles names, patches `__init__.py` with `os.add_dll_directory` before extension imports) or add the directory explicitly at the top of `pysam/__init__.py` before any `libc*` import.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| MSYS2 (dev-time only) | `pacman -S mingw-w64-x86_64-toolchain`; run real `./configure` to harvest config | Never in the wheel CI path |
| cibuildwheel | `[tool.cibuildwheel]` windows overrides: `CIBW_BEFORE_BUILD_WINDOWS` (config writer check / dep fetch), `CIBW_REPAIR_WHEEL_COMMAND_WINDOWS` (delvewheel slot), `test-command = pytest {project}/tests` | POSIX `before-all`/`before-build` hooks must be overridden, not replaced, for Windows (current hooks run shell scripts, CONCERNS W8) |
| GitHub Releases (fork channel) | Separate upload job, trusted publishing later | Per PROJECT.md distribution constraint |
| vcpkg (optional, phase D or zlib sourcing) | `CIBW_ENVIRONMENT_WINDOWS` passing INCLUDE/LIB | Only if building zlib/libcurl from source becomes necessary; simplest phase-1 path is vendoring zlib sources like Pillow does |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| setup.py POSIX branch ↔ Windows branch | None — mutually exclusive at `sys.platform` decision points | The hard invariant: POSIX branch files/functions untouched |
| libchtslib ↔ feature modules (.pyd ↔ .pyd) | Import-library linking at build; Cython cimport contract unchanged | Build order: chtslib import lib must precede feature-module links (Pattern 3) |
| libcutils ↔ libcsamtools/libcbcftools | Same import-lib mechanism | `_pysam_dispatch` fd plumbing is the fragile seam (CONCERNS "Fragile Areas"); all `/dev/null`/fd fixes concentrate here |
| pysam/__init__.py ↔ OS loader | `os.add_dll_directory` (conditional) before star imports | Insertion point exists today; keep it a no-op when statically linked |
| devtools/import.py ↔ win32/ config templates | Manual, documented harvest procedure | Version bumps of bundled htslib must regenerate templates |

## Sources

- [Cython docs — Appendix: Installing MinGW on Windows (compiler_type dispatch pattern)](https://cython.readthedocs.io/en/latest/src/tutorial/appendix.html)
- [Cython issue #4470 — Make MinGW work on Windows](https://github.com/cython/cython/issues/4470)
- [Python docs — os.add_dll_directory / Windows DLL resolution (bpo-36085 behavior)](https://docs.python.org/3/library/os.html)
- [delvewheel — Self-contained Python wheels for Windows](https://github.com/adang1345/delvewheel)
- [delvewheel issue #47 — patching DLLs beyond .pyd](https://github.com/adang1345/delvewheel/issues/47)
- [Autodesk maya-usd #2859 — AddDllDirectory search order unspecified](https://github.com/Autodesk/maya-usd/issues/2859)
- [confluent-kafka-python Windows build system (CIBW_REPAIR_WHEEL_COMMAND with delvewheel)](https://deepwiki.com/confluentinc/confluent-kafka-python/7.2-windows-build-system)
- [Apache Arrow #45278 — delvewheel for msvcp140 mangling](https://github.com/apache/arrow/issues/45278)
- [pypa/cibuildwheel](https://github.com/pypa/cibuildwheel) and [cibuildwheel docs](https://cibuildwheel.readthedocs.io/en/stable/)
- [coin-or/CyLP cibuildwheel workflow (vendored C-library reference implementation)](https://github.com/coin-or/python-mip/discussions/262)
- [iscinumpy — Overview of cibuildwheel](https://iscinumpy.dev/post/overview-of-cibuildwheel/)
- [lxml — building from source with --static-deps (prebuilt deps + static linking)](https://lxml.de/build.html)
- [Pillow #4960 (source-list/feature-probe build model)](https://github.com/python-pillow/Pillow/issues/4960)
- [pypa/pip #11633 — psycopg2 on MSYS2 (hand-maintained config.h pain)](https://github.com/pypa/pip/issues/11633)
- [samtools #2064 — MSYS2 GitHub Actions build of htslib/samtools/bcftools into a wheel](https://github.com/samtools/samtools/issues/2064)
- [conda-forge maintainer knowledge base (m2w64 compiler matrices)](https://conda-forge.org/docs/maintainer/knowledge_base/)
- [pysam #1132, #1137, #1320 — no official Windows support / build failures](https://github.com/pysam-developers/pysam/issues/1132)
- [nanobind — building extensions with Meson (meson/cmake alternative direction)](https://nanobind.readthedocs.io/en/latest/meson.html)

Confidence: web-derived claims MEDIUM (secondary sources, no primary verification of every tool claim); local codebase claims HIGH (from `.planning/codebase/` audit). Prior-art note: no successful public pysam Windows port exists — this architecture synthesizes from sibling-package patterns, not from a pysam-specific blueprint.

---
*Architecture research for: pysam Windows port — build-system architecture dimension*
*Researched: 2026-09-17*
