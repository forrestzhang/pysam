# Pitfalls Research

**Domain:** Porting a POSIX-first scientific Python C-extension package (pysam: Cython extensions wrapping bundled htslib/samtools/bcftools) to Windows with distributable wheels — dual toolchain (MinGW-w64/MSYS2 first, MSVC second)
**Researched:** 2026-09-17
**Confidence:** HIGH (CRT/ABI/LLP64/delvewheel findings corroborated by multiple independent sources; MEDIUM on current cibuildwheel image specifics, which drift)

> Scope note: pysam-specific blockers are already catalogued in `.planning/codebase/CONCERNS.md` (W1–W10). This file covers the *general class* of mistakes projects like this make when adding Windows support, keyed to those blockers where relevant.

## Critical Pitfalls

### Pitfall 1: CRT (C Runtime) mismatch between the extension and CPython

**What goes wrong:**
Random heap corruption, `free()` crashes, "file not found" for fds opened in the extension, and stdout/stderr interleaving — typically appearing only on end-user machines, not the build machine. With two toolchains in play (the project's explicit plan), the worst variant: a MinGW-built `.pyd` loaded into an MSVC-built CPython, where `free()` in one CRT releases memory allocated by another → undefined behavior.

**Why it happens:**
Windows has no system C library. CPython 3.5+ links the **Universal CRT (UCRT)** + `vcruntime140.dll`. Classic MinGW-w64 links the ancient `msvcrt.dll` (MSVC 6-era), which lacks most C99 and is ABI-incompatible with UCRT. CRT state (heaps, fd tables, locale, stdio buffers) is per-DLL: an fd opened under one CRT may not exist in the other's table, and memory must be freed by the same side that allocated it.

**How to avoid:**
- For MSVC wheels: build with the same MSVC generation as the CPython being targeted (cibuildwheel handles this via `distutils`/`setuptools` toolchain detection — don't override `CC`).
- For MinGW-w64 wheels: **must use a UCRT-targeted toolchain** (`mingw-w64-ucrt-x86_64-*` MSYS2 packages / `--with-default-msvcrt=ucrt`), never the msvcrt-vintage `mingw-w64-x86_64-gcc` if the produced `.pyd` mixes with anything UCRT. Verify with `objdump -p foo.pyd | grep DLL` — the only CRT DLLs listed should be `api-ms-win-*.dll` / `vcruntime140.dll`, never `msvcrt.dll`.
- Never pass `FILE*`, fds, or heap pointers across a module boundary that uses a different CRT. Inside pysam, the bundled htslib and the Cython extensions are compiled in the same toolchain pass — keep it that way; don't link a prebuilt MinGW `libhts.a` into an MSVC build or vice versa.

**Warning signs:**
- `objdump -p *.pyd | grep -i msvcrt` returning hits in a "MinGW wheel".
- Crashes in `free()`/`realloc()` inside `MSVCR*.dll` or `ucrtbase.dll` in user crash dumps while the build machine works fine.
- Weird "file not found" when reading fd 1/2 redirected output.

**Phase to address:**
MSVC toolchain phase (and MinGW wheel phase for the UCRT check). Add an automated wheel audit step that fails if `msvcrt.dll` appears in any vendored/built binary's import table.

---

### Pitfall 2: LLP64 data model — `long` is 32-bit on Windows x64

**What goes wrong:**
Silent truncation of pointers stored in `long`, wrong struct layouts, wrong `printf` formats, and incorrectly sized Cython `long` fields. pysam's own `tests/compile_test.py` asserts exact `__sizeof__` values (120/24/72/80/96/32) — any Cython struct containing a C `long` will have a different size on Windows x64 than on Linux, and these tests encode LP64 assumptions.

**Why it happens:**
Linux/macOS are LP64 (`long` = 8 bytes on 64-bit); Windows is LLP64 (`long` = 4 bytes; only `long long` and pointers are 8). Code that "works everywhere" on POSIX because `long == pointer` breaks silently on Windows — no compile error, just a truncated value or wrong offset. Classic instances: `(LONG)pointer` casts, `%lu` for `size_t` (works on LP64, wrong on LLP64 — use `%zu`), `long` used as an index/offset into large files (>2GB BAM offsets!).

**How to avoid:**
- Audit bundled htslib/samtools and Cython `.pyx` for `long` used where a pointer or file offset is meant; replace with `int64_t`/`off_t`/`ptrdiff_t`/`uintptr_t`. htslib is mostly clean here (uses `hpos_t`/`int64_t`), but the pysam Cython layer has `long` fields.
- Run the struct-size tests (`compile_test.py`) early on Windows and update the expected sizes for LLP64 rather than skipping the test — the size diff localizes every C-`long`-in-struct occurrence.
- Grep for `%ld`/`%lu` in format strings touching 64-bit values.

**Warning signs:**
- `compile_test.py` size mismatches on Windows.
- Failures only on files >2GB.
- Cython code declaring `cdef long` for htslib positions.

**Phase to address:**
MinGW build phase (first time the code compiles under LLP64). Bake a `grep -rn "cdef long"` and `%l[du]` audit into that phase's checklist.

---

### Pitfall 3: Treating MSVC C99 non-compliance as a per-error whack-a-mole

**What goes wrong:**
The MSVC phase drowns in hundreds of compile errors/warnings from bundled htslib/samtools/bcftools (which require C99 — upstream literally fails on GCC without `-std=gnu99`): variable-length arrays (VLAs — **never supported by MSVC, ever**), `restrict` qualifiers, missing `unistd.h`/`strings.h`, `ssize_t`, POSIX names (`fdopen`, `strdup`, `isatty`, `fileno`, `ftruncate`, `random`). Fixing each ad hoc with scattered `#define`s produces an unmaintainable diff that breaks on every upstream re-import via `devtools/import.py`.

**Why it happens:**
MSVC only reached usable C99 *library* support in VS 2015 and C11/C17 in VS 2019 16.8; VLAs remain unsupported by design. Developers porting GCC code underestimate the volume and respond file-by-file instead of building one systematic compatibility layer.

**How to avoid:**
- One central shim header (extend the existing `win32/unistd.h` pattern, but make it MSVC-first and complete): `isatty→_isatty`, `fileno→_fileno`, `fdopen→_fdopen`, `ftruncate→_chsize`, `sleep→Sleep`, `ssize_t→SSIZE_T/ptrdiff_t`, plus a forced include (`/FI`) of the shim via `extra_compile_args` so vendored sources don't need editing.
- Where the shim cannot help (true VLAs), prefer patching upstream in a *reusable, upstreamable* way (fixed-size buffer or heap alloc) over local hacks — the project constraint requires only upstream-acceptable portability patches.
- Consider **clang-cl** (LLVM with MSVC ABI) as an intermediate step: full C99/C11 support, links against UCRT, produces MSVC-compatible objects — dramatically lowers the MSVC-phase risk while keeping ABI compatibility with official CPython.

**Warning signs:**
- Compile error count growing across phases; fixes scattered in vendored `.pysam.c` files (which are *regenerated* by `devtools/import.py` — edits there are lost).
- A growing pile of `#ifdef _WIN32` in Cython `.pyx` files that duplicates what a shim could do centrally.

**Phase to address:**
MSVC phase — but design the shim during the MinGW phase (MinGW needs `unistd.h` too; the difference is only MSVC's missing names, W4/W10). Never edit `*.pysam.c` directly; patch `devtools/import.py` templates or the shim.

---

### Pitfall 4: Import libraries and object files don't cross toolchains

**What goes wrong:**
Link errors like `undefined reference to ...` or `cannot open file .lib` when mixing MinGW-produced `.a`/`.dll.a` import libs with MSVC `link.exe` (or vice versa). Both are COFF, but MinGW import libraries and MSVC import libraries are not interchangeable; static archives produced by `ar` vs `lib.exe` often won't link across.

**Why it happens:**
The dual-toolchain plan invites "reuse the MinGW-built htslib from the MSVC build" (or shipping both in one wheel). Toolchains differ in symbol decoration, `__declspec(dllimport)` handling, and archive member formats.

**How to avoid:**
Each toolchain builds the full dependency closure itself: bundled htslib/htscodecs/samtools/bcftools compiled from source per toolchain. Never mix objects/archives across toolchains. For DLLs that must be shared (e.g. a libcurl DLL), obtain per-toolchain import libs (MSVC: link directly against `libcurl.lib`; MinGW: generate with `gendef` + `dlltool` or use `libcurl.dll.a` from MSYS2 — and accept that only one toolchain variant ships per wheel).

**Warning signs:**
`LINK : fatal error LNK1181` / `undefined reference to '__imp_...'` when switching toolchains.

**Phase to address:**
MSVC phase (MinGW phase builds everything itself already). Enforce in CI: the MSVC job never references `win32/` MinGW artifacts.

---

### Pitfall 5: Wheels that work on the build machine but fail on clean machines ("DLL load failed")

**What goes wrong:**
`ImportError: DLL load failed while importing libchtslib` on user machines. MinGW-built `.pyd` files depend on `libgcc_s_seh-1.dll`, `libstdc++-6.dll`, `libwinpthread-1.dll` — none of which exist on a stock Windows box. MSVC-built wheels can fail similarly if built against a non-default runtime or if dependency DLLs (zlib, libcurl) aren't vendored.

**Why it happens:**
`delvewheel` (cibuildwheel's default Windows repair tool) reads DLL import tables, but: (a) MSYS2-built binaries may place runtime deps outside the searched PATH; (b) dependencies loaded via `LoadLibrary`/`ctypes` (pysam's `dynamic_libs.c` does exactly this for libcurl/libcrypto) are invisible to repair tools; (c) MinGW DLLs with debug-overlay sections break name-mangling unless stripped first.

**How to avoid:**
- Always run `delvewheel repair` (cibuildwheel does by default) **plus** verify on a clean VM/machine before publishing — the project's `release.yaml` should add an install-from-release-asset smoke test job.
- For MinGW wheels: `delvewheel repair --strip` (GNU strip must be on PATH) so name-mangling of libgcc/libwinpthread succeeds; otherwise `--no-mangle` risks DLL hell between packages.
- Add `--add-dll` for anything loaded dynamically (`libcurl`, `libcrypto` if that path is implemented).
- License compliance when vendoring: GCC runtime DLLs are GPL **with GCC Runtime Library Exception** (OK to ship, no copyleft of pysam); MinGW-w64 runtime is permissive — include `COPYING.MinGW-w64-runtime.txt`. Document the bundled-DLL map per release (also flagged in CONCERNS.md security section).

**Warning signs:**
- `objdump -p foo.pyd | grep "DLL Name"` listing DLLs not present in the wheel's `.libs` directory.
- All tests passing in CI but bug reports from users on clean machines.

**Phase to address:**
Windows CI/wheel phase. A clean-machine smoke test (install wheel in a bare `windows-latest` runner with no MSYS2, import pysam, run a BAM open) is the acceptance gate for wheel publication.

---

### Pitfall 6: ANSI path handling silently breaks non-ASCII filenames

**What goes wrong:**
htslib takes `char*` paths and calls `fopen`. On Windows, ANSI `fopen` interprets bytes in the *current system codepage* (on many machines, not UTF-8). Files with Chinese/Japanese/etc. names fail to open or open the wrong file. pysam users on non-English Windows (the user's own environment is Windows 11 China) will hit this immediately.

**Why it happens:**
Windows filenames are natively UTF-16; only the `W` APIs (`CreateFileW`, `_wfopen`) are codepage-independent. Code ported from POSIX assumes byte-paths-are-fine (Linux uses UTF-8 bytes). Python itself hands paths to extensions as `str` (filesystem encoding utf-8 on Windows) — if pysam encodes to bytes and calls ANSI APIs, non-ASCII chars corrupt.

**How to avoid:**
- At the Cython boundary, convert Python path objects with `PyUnicode_AsWideCharString()` (not the removed `PyUnicode_AsUnicode`) and call the wide APIs on Windows (`_wfopen`, `CreateFileW`, `_wopen`), or route through htslib's own `hopen`/fd-based entry points by opening the file in Python and passing an fd/handle.
- Realistically for pysam: pysam already passes paths into htslib as bytes. Options: (a) accept documented limitation for phase 1, (b) add a small `fopen`→`_wfopen` macro layer for `_WIN32` that converts UTF-8 bytes to UTF-16 via `MultiByteToWideChar(CP_UTF8, ...)` — htslib paths are internally UTF-8-ish on POSIX, so a UTF-8→wide shim is faithful.
- Add a test with a non-ASCII filename early; it's a cheap canary.

**Warning signs:**
Bug reports about files "not found" that exist; tests passing on an English-locale CI runner only.

**Phase to address:**
Test-suite port phase (add the canary test), full fix in the polish/feature-parity phase. Note Python 3.12+ removes `PyUnicode_AsUnicode` — use `PyUnicode_AsWideCharString` + `PyMem_Free`.

---

### Pitfall 7: MAX_PATH (260 chars) truncation on temp dirs and deep paths

**What goes wrong:**
File operations fail with `ENOENT`/path-not-found once paths exceed ~260 chars. pytest temp dirs under CI working directories, deeply nested BAM folder structures, and cloud-synced home dirs easily exceed this. Unicode paths count **characters**, not bytes — non-ASCII names hit the limit sooner.

**Why it happens:**
Legacy ANSI APIs cap at `MAX_PATH`. Long-path support requires either the `\\?\` prefix (absolute, backslash-only, no `.`/`..`) with the `W` APIs, or the opt-in registry/`manifest` setting (Windows 10 1607+, off by default).

**How to avoid:**
- Keep CI working directories short (e.g. `C:\b` instead of the default `D:\a\pysam\pysam\` double-nested GHA path) — the single highest-ROI fix.
- Use wide APIs (see Pitfall 6) and prepend `\\?\` when length approaches the limit.
- Don't "fix" by silently truncating paths; surface the error.

**Warning signs:**
Intermittent `ENOENT` in CI only; tests that pass locally fail on GHA.

**Phase to address:**
Windows CI phase (short workdir) and the same wide-API work as Pitfall 6.

---

### Pitfall 8: fd/stdout semantics divergence — `/dev/null`, fd passing, and binary mode

**What goes wrong:**
Three converging failure modes in exactly the fragile area CONCERNS.md flags (`_pysam_dispatch`, `libcutils.pyx`):
1. Hardcoded `/dev/null` (W3) doesn't exist on Windows.
2. File descriptors opened in C land and consumed by another CRT or Python layer get different fd numbering semantics on Windows (fds are valid but CRT-per-DLL, see Pitfall 1; also `_get_osfhandle` translation needed for HANDLE-level APIs).
3. **Text-mode default**: on Windows, `fopen`/`_open` without `O_BINARY`/`"b"` performs CRLF translation — writing binary BAM/BGZF data through a text-mode fd **corrupts the output** (`\n` → `\r\n`). POSIX has no such mode.

**Why it happens:**
POSIX assumes fds are process-global and files are byte streams. Windows makes both assumptions false. The Cython `posix.*` cimports (W2) generate POSIX-signature calls that happen to link under MinGW but hide the binary-mode issue entirely.

**How to avoid:**
- `os.devnull` instead of literal `/dev/null` (one-line fix, CONCERNS.md W3 already prescribes it).
- Every `open`/`fopen`/`c_open` in the ported paths must specify `O_BINARY` / `"wb"` — audit `_pysam_dispatch` (`libcutils.pyx:300-464`), the `import/pysam.c` fdopen sites, and htslib calls that receive fds. This is the highest-severity *silent corruption* risk in the whole port.
- For fd passing between Python and C, use `_open_osfhandle`/`_get_osfhandle` explicitly and stay within one CRT.
- Note `_pysam_dispatch`'s longjmp-based error path already leaks temp files on POSIX (CONCERNS.md); on Windows add cleanup in a `finally`-equivalent C guard.

**Warning signs:**
BAM/BCF outputs from `pysam.samtools.*` that differ byte-wise from real samtools output (`checkBinaryEqual` failures), especially sizes growing by the number of `\n`s. Tests passing when output goes to a pipe but failing when written to a file (or vice versa).

**Phase to address:**
POSIX-dependency cleanup phase (W2/W3) — the binary-mode audit is part of the same pass.

---

### Pitfall 9: libcurl/OpenSSL dependency handling on Windows (remote-file parity gap)

**What goes wrong:**
Feature-parity gap: `s3://`, `gs://`, `http://` URLs don't work on Windows. Current pysam gates dynamic loading on `sys.platform == "linux"` with hardcoded sonames (`libcurl.so.4`, `libcrypto.so.*`) via `dlopen` — none of which exists on Windows. Naive attempts to "just enable libcurl" then hit: htslib's configure probes mis-detecting curl, OpenSSL vs native Schannel backend choice, and DLL-loading failures on clean machines.

**Why it happens:**
Windows has no soname concept; htslib's Windows support expects either static linking or explicit `LoadLibrary("libcurl*.dll")`; the auto-configure machinery (W1/W6) that wires this up on POSIX doesn't exist in the new Windows build path.

**How to avoid:**
- **Phase it deliberately:** ship Windows wheels with libcurl disabled (`HAVE_LIBCURL=0`) and networking tests skip-gated — the tests already follow `getattr(pysam.config, "HAVE_LIBCURL", 0)` idiom (TESTING.md). Document the gap.
- Later: add a Windows branch of `dynamic_libs.c` using `LoadLibraryA`/`GetProcAddress` against a list of `libcurl-*.dll` / `libcrypto-*.dll` names, or link libcurl statically with the Schannel backend (`-DUSE_SSL=SCHANNEL`... upstream curl builds) to avoid shipping OpenSSL at all.
- Whichever way: the DLL must be vendored into the wheel (Pitfall 5) or the feature dies on clean machines.

**Warning signs:**
Tests gating on `HAVE_LIBCURL` unexpectedly running (config.h parsing silently defaulting to 0 — CONCERNS.md flags `collections.defaultdict(int)` behavior); wheel size ballooning from vendored OpenSSL.

**Phase to address:**
Explicitly out of the first build/test/CI phases; its own later phase. Do not let "remote files don't work" block MinGW/MSVC parity on local files.

---

### Pitfall 10: Port the tests assuming POSIX process/shell semantics

**What goes wrong:**
Even with a perfect build, the suite fails wholesale: shell pipelines (`samtools ... | awk`, `2> /dev/null`), `head -n200` via `shell=True`, signal-based exit code checks (`retcode < 0`), `errno.EPIPE`, `LD_LIBRARY_PATH` exports, `REF_PATH` separator `:` (htslib uses `;` on Windows), and `multiprocessing` fixtures that fork on POSIX but *spawn* on Windows (re-importing the test module in the child — import-time side effects explode).

**Why it happens:**
POSIX shell semantics don't exist on Windows; `cmd.exe` doesn't do `2>` pipes the same way, negative return codes don't exist (exit codes are positive; "killed by signal" is unrepresentable), and spawn-mode multiprocessing requires import-safety.

**How to avoid:**
- Replace shell pipelines with in-process equivalents: `pysam.samtools.view(...)` plus pure-Python counting — TESTING.md already notes `tests/TestUtils.py` helpers exist for this. Where a real external `samtools` is needed as oracle, gate on `shutil.which("samtools")` and skip.
- Parameterize the `REF_PATH` separator on `os.name` (`;` vs `:`) — one line, but invisible until CRAM reference lookups fail on Windows.
- Make `conftest.py` spawn-safe (it mostly is — verify the `multiprocessing.Process` http-server fixture pickles cleanly under spawn).
- Test data generation Makefiles (`tests/pysam_data/Makefile`) need a Python fallback or pre-generated artifacts committed for Windows CI.
- Follow the suite's existing platform-skip idiom (`@pytest.mark.skipif(sys.platform ...)`).

**Warning signs:**
Massive test failures clustered in `AlignmentFileFetchTestUtils`/`PileupTestUtils`/`samtools_test.py`; tests hanging (spawn deadlock) rather than failing.

**Phase to address:**
Test-suite port phase, immediately after first successful build.

---

### Pitfall 11: CI pitfalls — POSIX-only cibuildwheel config, shell mismatch, and MSYS2 setup cost

**What goes wrong:**
The existing `pyproject.toml` cibuildwheel config runs a POSIX `before-all` script and `make -C htslib distclean` (W8) — both fail instantly on a Windows runner. Further traps: running builds inside `shell: msys2 {0}` while cibuildwheel invokes its own `cmd` subprocesses (PATH mixing causes "gcc not found" or MSVC confusion); `msys2/setup-msys2` adding several minutes per job; MSVC jobs needing `msvc-dev-cmd` (or let setuptools auto-detect); 32-bit never needed (already out of scope).

**Why it happens:**
cibuildwheel's Windows builds run in the build-frontend's environment (Python's own MSVC toolchain for native builds); MSYS2 only provides the compiler for the MinGW variant and must be injected carefully via `CIBW_ENVIRONMENT_WINDOWS` (e.g. `CC/CXX`) with `path-type: inherit`, as in the documented Fortran/fpm pattern.

**How to avoid:**
- Use `CIBW_BEFORE_ALL_WINDOWS` / `CIBW_BEFORE_BUILD_WINDOWS` (platform-suffixed vars) — the POSIX `before-all` stays for Linux/macOS untouched (cross-platform-safety constraint).
- Keep the MinGW job's Python interpreter the standard CPython (MSYS2's own Python is a different beast); MSYS2 supplies only gcc/binutils.
- Cache MSYS2 (`cache: true` on setup-msys2) and matrix over Python versions in one job to amortize setup.
- For MSVC jobs, don't fight toolchain detection unless necessary; pin `CIBW_BUILD: cp3x-win_amd64`.
- First milestone: a plain `windows-latest` job that builds and runs pytest before attempting cibuildwheel at all.

**Warning signs:**
Green Linux CI while Windows jobs fail at the `before-all` step; builds finding the wrong `gcc` (MSYS2 vs none); 10+ minute Windows job setup times.

**Phase to address:**
Windows CI phase. Add one manual `windows-latest` build job *before* cibuildwheel integration.

---

### Pitfall 12: Symbol conflicts between extension modules go undetected without `nm`

**What goes wrong:**
Duplicate non-static C symbols across the samtools/bcftools-derived extension modules (`libcsamtools`, `libcbcftools`, and the 14 `libc*.pyx` modules) cause "wrong function called" crashes at runtime. On POSIX this is caught by `check_ext_symbol_conflicts` (`nm -g -P`); on Windows the check degrades to a warning and never runs (CONCERNS.md, Tech Debt). The 2013-era `#define` prefixes in `import/pysam.h:63-73` are the manual mitigation and are surely stale for current upstream sources.

**Why it happens:**
Bundled samtools/bcftools were never designed to be linked into one process; `devtools/import.py` regex-rewrites and hand-maintained symbol prefixes are the only barrier. Windows linker behaves differently (MSVC links happily where GNU ld might complain, and DLL boundary hides duplicates until a call jumps wrong).

**How to avoid:**
- Port the check: `dumpbin /symbols` (MSVC) or `llvm-nm` (works on both toolchains, parses MSVC and MinGW objects) driven by the existing Python check code.
- Re-run it after every `devtools/import.py` regeneration of `*.pysam.c`.
- Prefer `static` + identical-helper refactoring where upstreamable.

**Warning signs:**
Crash inside a samtools subcommand that works in the standalone binary; wrong output from one `pysam.samtools.*` call only.

**Phase to address:**
MSVC phase (and wheel QA for MinGW). Cheap to add with `llvm-nm`.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep stale `win32/` shims as-is and patch around them | No new files; build "works" under MinGW quickly | 2013-era `unistd.h` missing `isatty`/`fileno`/`sleep`/`getpid`; `stdint.h` shadows the system header under modern MSVC | Never for MSVC; acceptable as MinGW-only stopgap behind `sys.platform == 'win32'` guard, with a rewrite ticket |
| Ship Windows wheels with `--disable-libcurl` | Unblocks everything else; no DLL vendoring/licensing questions | Documented feature gap vs Linux/macOS wheels | Explicitly acceptable for first fork releases; must be documented in README + config flags |
| Skip tests that shell out instead of rewriting them | Green CI fastest | Windows coverage silently diverges; regressions invisible | Acceptable for a milestone boundary if each skip cites a CONCERNS.md item and a rewrite ticket exists |
| `-static-libgcc -static-libstdc++` to avoid delvewheel | Fewer DLLs to vendor | Known unreliable for DLLs (not EXEs); can cause duplicate `_Unwind_Resume` symbols across modules | Only with the wheel-audit check (Pitfall 5) verifying no unwanted dynamic deps remain; prefer delvewheel repair |
| Pre-baked `config.h` per toolchain | Removes configure/make entirely on Windows | Must be regenerated when bundled htslib version bumps; drift silently disables features (defaultdict(int) → 0) | Acceptable and recommended — but add a build-time check that every `HAVE_*`/`ENABLE_*` key in `pysam/config.py` exists in the baked header |
| Reuse the untested `setup.py:633` MSVC branch | "It's already there" | Comment literally says "untested"; assumes MSVC 2008-era layout | Never — treat as archaeology, write the Windows branch fresh |
| Commit pre-generated test data for Windows | Removes make dependency in tests | Data can drift from Makefiles | Acceptable if a CI check regenerates on Linux and byte-compares |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| htslib `configure` on Windows | Trying to run `./configure` under MSYS2 and hoping paths/config translate | Write pre-baked `htslib/config.h` per toolchain (CONCERNS W1); MSYS2 configure output doesn't match what `setup.py`'s regex parsers expect |
| MSYS2 `pacman` deps (zlib/bzip2/xz/libdeflate) | Linking MSYS2 `*.dll.a` import libs into MSVC builds, or mixing `/mingw64` and `/usr` trees | Per-toolchain dependency closure (Pitfall 4); MSYS2 deps only in MinGW wheel; MSVC uses vcpkg or bundled sources |
| libcurl backend | Vendoring OpenSSL on Windows for htslib https | Prefer Schannel (Windows native TLS) when building/bundling curl, or defer entirely (Pitfall 9) |
| `delvewheel` | Assuming it catches everything | It reads import tables only; `--add-dll` for `LoadLibrary`-loaded deps; verify on clean machine |
| GitHub Actions Windows images | Assuming `make`/`gcc` exist | `windows-latest` has MSVC + Python but no MSYS2/gcc by default; install explicitly; MSYS2 setup adds minutes (cache it) |
| REF_PATH / env-list separators | Copying `REF_PATH=":"` from conftest | `os.pathsep` (`;` on Windows); htslib honors it (CONCERNS W9) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| MSYS2 install per CI job | Windows job setup dominates build time (~minutes) | `cache: true` on setup-msys2; one job matrices all Python versions | Any CI run |
| Re-running htslib configure on every build | Slow local iteration | Baked config.h + incremental build; keep `libhts` objects stable | Developer inner loop |
| Serial `nm` symbol-conflict check | Slow builds (existing on POSIX) | Run once per wheel job, not per extension; use llvm-nm parallel | Build time only |
| Test data generation via make | Slow/no-op on Windows | Pre-generated data artifacts + Linux-side byte-compare check | Windows CI job duration |
| Long GHA working directories | MAX_PATH flakiness (Pitfall 7) | Short workdir (`C:\b`) | Always on Windows CI |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| `shell=True` with `HTSLIB_CONFIGURE_OPTIONS` (existing, CONCERNS.md) | Env-var shell injection in build farms | Pass as single argv element, no shell |
| Vendoring DLLs from unofficial download sites into wheels | Supply-chain compromise; users run unsigned binaries | Only MSYS2-official / vcpkg / self-built DLLs; pin versions; record hashes |
| Shipping ancient `win32/getopt.c` | Historic overflow-prone parser | Replace with maintained implementation or limit to build-time use (CONCERNS security section) |
| GPL anxiety blocking MinGW runtime vendoring | Over-reaction | GCC Runtime Library Exception explicitly permits shipping libgcc/libstdc++; include license texts (Pitfall 5) |
| OpenSSL vendoring | CVE inheritance + export/attribution requirements | Prefer Schannel backend; if OpenSSL, track CVEs and version-pin per release |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Publishing wheels tested only on the build machine | "DLL load failed" for every user | Clean-machine smoke test as release gate (Pitfall 5) |
| pip falling back to sdist on Windows | Users get a source build that fails (no configure/make) | Ensure the fork's PyPI/index only exposes Windows wheels for supported Pythons; make sdist Windows-build failure fast and explicit |
| Silent feature loss (remote URLs) with no error message | Confusion why `s3://` works on Linux | Clear runtime message: "remote file support not available in this build" tied to `pysam.config.HAVE_LIBCURL` |
| Error messages quoting POSIX paths (`/dev/null`) | Users can't act on errors | Platform-correct paths in messages; `os.devnull` |
| No Windows docs | Users don't know wheel exists or limitations | Windows section in INSTALL/README listing supported Pythons, limitations (remote files, non-ASCII paths until fixed), and issue-reporting channel |

## "Looks Done But Isn't" Checklist

- [ ] **Build passes:** Often only means compile+link on the dev machine — verify `objdump -p *.pyd` shows no `msvcrt.dll` (UCRT check) and no unvendored DLL deps.
- [ ] **Import works:** `import pysam` only exercises module init — run one read, one write, one `pysam.samtools.view` call, and byte-compare output against real samtools.
- [ ] **Binary-mode audit:** Grep all ported `open`/`fopen`/`c_open` sites for `O_BINARY`/`"b"` — text-mode fds corrupt BAM/BGZF silently.
- [ ] **Tests green on Windows:** Check *how many were skipped/collected* vs Linux — a 60% skip rate masquerades as success; diff the collected-test counts per phase.
- [ ] **Wheel installs clean:** Install the wheel (not the build tree) on a runner with no MSYS2/gcc and run the smoke test — CI's build tree hides DLL resolution via PATH.
- [ ] **Non-ASCII filename test:** A single canary test with a CJK filename catches the whole ANSI-path pitfall class.
- [ ] **Fork regressions:** Linux/macOS CI still green and `release.yaml` unchanged for POSIX wheels — cross-platform safety is a stated constraint.
- [ ] **Symbol-conflict check:** Confirm `llvm-nm`-based check ran on Windows artifacts at least once per `devtools/import.py` regeneration.
- [ ] **config.h drift:** After any htslib version bump, diff baked `config.h` against configure-generated output on Linux.
- [ ] **License files:** Vendored DLL licenses (GCC runtime exception text, MinGW-w64 COPYING) present in the wheel metadata.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| CRT mismatch shipped in a wheel | MEDIUM | Rebuild affected toolchain variant with correct runtime; yank/retag release; no user data loss but reputation hit |
| Text-mode corruption of outputs | LOW (if caught) | Binary-mode fix is mechanical; re-run byte-compare tests to confirm |
| LLP64 truncation bugs | MEDIUM | Usually localized by struct-size tests; fix field types, re-audit `%l` formats |
| DLL-load failures reported by users | LOW | Identify missing DLL via `Dependencies`-style tool; add to delvewheel invocation; re-release |
| Test-suite skip creep | MEDIUM | Re-enable by replacing shell oracles with in-process equivalents; track in dedicated milestone item |
| MSVC phase stalls on C99 errors | LOW if planned | Switch that phase to clang-cl as intermediate; keeps ABI, restores C99/C11 |
| MSYS2/CI config rot | LOW | Iterate on one manual windows-latest job before cibuildwheel; keep POSIX jobs untouched |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. CRT mismatch (incl. UCRT check) | MinGW wheel phase (UCRT toolchain selection); MSVC phase | `objdump -p` audit step in CI; clean-machine smoke test |
| 2. LLP64 | First MinGW build phase | `compile_test.py` size assertions updated + passing on Windows |
| 3. MSVC C99 whack-a-mole | MSVC phase (shim designed earlier) | Central shim header exists; zero edits inside `*.pysam.c`; compile-error count trend per milestone |
| 4. Cross-toolchain import libs | MSVC phase | MSVC job builds bundled libs from source; no MinGW artifacts in MSVC job workspace |
| 5. Non-self-contained wheels | Windows CI/wheel phase | delvewheel + clean-runner install test gates release |
| 6. Non-ASCII paths | Test port phase (canary) / parity phase (full fix) | CJK-filename test in suite |
| 7. MAX_PATH | Windows CI phase | Short CI workdir; long-path test case |
| 8. Binary-mode/fd semantics | POSIX-dependency cleanup phase (W2/W3) | Byte-compare tests (`checkBinaryEqual`) pass for file outputs, not just pipes |
| 9. libcurl parity | Dedicated later phase | `HAVE_LIBCURL=0` documented; networking tests skip-gated; later: clean-machine remote-URL test |
| 10. POSIX test semantics | Test-suite port phase | Collected-test count parity with Linux within agreed delta; zero hangs |
| 11. CI config pitfalls | Windows CI phase | One green `windows-latest` job before cibuildwheel; POSIX matrix untouched |
| 12. Symbol conflicts | MSVC phase + wheel QA | llvm-nm check wired into existing `check_ext_symbol_conflicts` |

## Sources

- [Why do Python extension modules need to be compiled with MSVC on Windows? (Stack Overflow)](https://stackoverflow.com/questions/56210402/why-do-python-extension-modules-need-to-be-compiled-with-msvc-on-windows) — HIGH
- [Steve Dower: Building Extensions for Python 3.5](https://stevedower.id.au/blog/building-for-python-3-5) — HIGH (CRT/UCRT authoritative)
- [Matthew Brett: Notes on Python compiled with MinGW-w64](https://matthew-brett.github.io/pydagogue/mingw_python.html) — HIGH
- [Ziggit: Windows GNU/MinGW and MSVC binary C ABI compatibility](https://ziggit.dev/t/windows-gnu-mingw-and-msvc-binary-c-abi-compatibility-guarantees/6903) — MEDIUM
- [mingw-users: stdcall/cdecl mix and MSVC compatibility](https://mingw-users.narkive.com/m6SiZHc1/stdcall-cdecl-mix-and-msvc-compatibility) — MEDIUM
- [samtools/htslib issue #1523: C99 required](https://github.com/samtools/htslib/issues/1523) — HIGH
- [cppreference: C compiler support](https://cppreference.net/c/99.html) — HIGH (MSVC feature matrix)
- [perldoc perlhacktips: VLAs not supported by any MSVC](https://perldoc.perl.org/perlhacktips) — HIGH
- [PVS-Studio: 64-bit porting issues / LONG, LONG_PTR](https://pvs-studio.com/en/blog/posts/cpp/1036/) — HIGH (LLP64)
- [GCC bug #103635: size_t/uintptr_t on w64](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103635) — MEDIUM
- [LLVM commit: ssize_t definition on Windows](https://lists.llvm.org/pipermail/llvm-commits/Week-of-Mon-20130701/179890.html) — MEDIUM
- [delvewheel (adang1345/delvewheel)](https://github.com/adang1345/delvewheel) — HIGH
- [meshpy #150: wheels not self-contained (MinGW runtime DLLs)](https://github.com/inducer/meshpy/issues/150) — HIGH
- [Stack Overflow: eliminating MinGW DLL dependencies](https://stackoverflow.com/questions/62156534/eliminate-dependency-on-mingw-specific-dlls-when-compiling-dynamic-library) — MEDIUM (static-link pitfalls)
- [SO: statically/dynamically linked mingw-w64 runtime licensing](https://opensource.stackexchange.com/questions/9047/can-i-use-statically-or-dynamically-linked-mingw-w64-runtime-libraries-for-com) — MEDIUM
- [Fortran Discourse: Python wheels on GHA using MSYS2 + cibuildwheel](https://fortran-lang.discourse.group/t/python-wheels-on-github-actions-using-fortran-f2py-numpy-meson-and-cibuildwheel/5609) — HIGH (working CIBW_ENVIRONMENT_WINDOWS pattern)
- [cibuildwheel docs](https://cibuildwheel.pypa.io/en/stable/faq/) — HIGH (platform-suffixed before-all/build vars, delvewheel default)
- [MSDN: fopen/_wfopen](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/fopen-wfopen) — HIGH (wide-path recipe)
- [mergeall fixlongpaths.py](http://learning-python.com/mergeall-products/unzipped/fixlongpaths.py) — MEDIUM (MAX_PATH subtleties: 259 vs 247, `\\?\` rules)
- [SDL discourse: Unicode path handling](https://discourse.libsdl.org/t/file-path-and-unicode-characters-sdl-dropfile-event/24764) — MEDIUM
- [GitCode: Cython + Windows Unicode (PyUnicode_AsWideCharString for 3.12)](https://blog.gitcode.com/6c518dfd0b78d705f72f17197bb0eabe.html) — MEDIUM
- Domain-internal sources: `.planning/codebase/CONCERNS.md` (W1–W10), `.planning/codebase/TESTING.md` — HIGH (repo-specific facts)

---
*Pitfalls research for: pysam Windows port (MinGW-w64 + MSVC, distributable wheels)*
*Researched: 2026-09-17*
