# Upstream Windows PRs & Issues — Field Report

**Project:** pysam Windows port
**Researched:** 2026-10-09 (live review of pysam-developers/pysam via `gh`)
**Confidence:** HIGH — direct quotes from maintainers and merged-diff inspection; test numbers from the contributor's own logs

## TL;DR

Two open upstream PRs implement a MinGW/MSYS2 route to building pysam on Windows, and one of them (#1400) contains a **working CI recipe for exactly our least-documented Phase 1 glue: UCRT64 GCC driving python.org CPython**. Neither PR builds wheels or touches packaging; both carry hacks we must not copy verbatim. Crucially, maintainer jmarshall stated on record that upstream will likely only ever merge an **MSYS2-based approach** and explicitly named **delvewheel** as an acceptable way to ship the resulting wheels — which puts measurable tension on our Decision 1 ("wheels are MSVC-only"). Re-evaluate that decision during discuss-phase before Phase 4 planning.

## Inventory

| Item | State | Relevance |
|---|---|---|
| PR #1274 "MinGW version of pysam" (teepean, 2024-03) | open, stalled | 958-test local baseline on UCRT64; setup.py link structure to borrow |
| PR #1400 "MinGW support" (theAeon, 2026-03) | open, "needs work" | python.org-CPython-under-msys2 CI glue; supersedes #1274 nominally |
| PR #964 "[WIP] build pysam on Windows" (fo40225, 2020) | open, abandoned | MSVC+MinGW hybrid hack; requires hand-editing Anaconda's `distutils/cygwinccompiler.py`; do not use |
| Issues #575, #624, #969, #1137, #1320, #1336, #1005 | open | User demand, no solutions ("how to install on Windows") |
| Issue #1375 | closed | jmarshall: "See PR #1274 for efforts towards adding support"; recommends VM/WSL meanwhile |
| Issue #983 (win32/getopt missing from sdist) | closed | Historical; confirms `win32/getopt.c` packaging pitfalls |

## PR #1274 — MinGW version of pysam

<https://github.com/pysam-developers/pysam/pull/1274> — teepean, 2024-03-28; last updated 2025-03-20. Files: `setup.py` (+232/−100), `.github/workflows/ci.yaml` (+152/−156).

### Environment

MSYS2 **UCRT64 with MSYS2's own CPython** (`C:/msys64/ucrt64/bin/python.exe`, 3.11.8, from `mingw-w64-ucrt-x86_64-python`). **Not** python.org CPython — a wheel from this setup targets the MSYS2 Python ecosystem, not the standard Windows install base. This is the gap our Phase 1 exists to close; see #1400 for the bridge.

### Test baseline (Phase 2 / TEST-01 input)

958 tests collected, all run types (filename/fileobject/StringIO/fetch, BAM/SAM/CRAM):

- **FAILED (4):** `TestIO::testReadingFromFileWithoutIndex`, `TestLogging::testFail1`, `TestLogging::testNoFail1`, `TestLogging::testNoFail2`
- **SKIPPED:** `testIteratorOutOfScope` (invalid-access test, crashes on 3.11 everywhere), `TestLargeCigar::test_reading_writing_cram` ("fails on linux — https issue?"), `StreamTest::test_samtools_processing` ("test contains bug")
- **Remote I/O PASSED** under UCRT64: `TestRemoteFileFTP`, `TestRemoteFileHTTP` (mingw curl DLLs just work). We still defer remote I/O per Decision 4 — this only means the UCRT64 dev environment won't hide curl problems from us.
- Bench suite: samtoolsshell variants fail with "The system cannot find the path specified" (subprocess/PATH translation issue — expect this class of failure in PORT work).

### setup.py mechanics (the borrowable parts)

- `run_configure`: under `MSYSTEM ∈ {MINGW32, MINGW64, UCRT64, CLANG*}` invoke `sh ./configure` instead of `./configure`
- Windows link structure via `extra_objects` (bypassing `-l` name resolution):
  - `htslib/libhts.a` (still built `lib-static`)
  - MSYS2 import libs by absolute path: `{msys2_root}/{msystem}/lib/lib{lib}.a` for `deflate.dll, z.dll, bz2.dll, crypto.dll, lzma.dll, regex.dll, tre.dll, intl.dll, iconv.dll, curl.dll` + `ws2_32` handled specially
- Cross-extension linking by exact filename: `:libchtslib{EXT_SUFFIX}` (`:` prefix = link this file, don't library-search) — replaces our `$ORIGIN` rpath mechanism
- `-Wl,--export-all-symbols` on libchtslib/libcsamtools/libcbcftools so downstream extensions can resolve their symbols; `-shared` in `extra_link_args`
- `find_msys2_root()` parses `df -a` for the line ending in ` /` to locate the MSYS2 install root
- `run_nm_defined_symbols`: skips symbol filtering when `platform.system() == 'Windows'` and not MSYS (nm not available on native Windows)

### Hacks NOT to copy (anti-patterns, confirmed present in diff)

1. **Symbol-conflict check commented out** — `errors += 1` → `#errors += 1` in `check_ext_symbol_conflicts`. Silently tolerates the exact duplicate-symbol class our port must surface and resolve properly (see CONCERNS W-items on nm/ld symbol checking).
2. Inconsistent lib naming in `external_htslib_libraries` — mixes `'z'`/`'crypto'` (bare) with `'z.dll'`/`'crypto.dll'`; works only by accident of MSYS2's `libz.dll.a`/`libz.a` dual presence.
3. `df -a` root detection — fragile; prefer `cygpath -m /` or `MSYSTEM_PREFIX` (PR #1400's approach is closer).
4. Duplicated `modules = [...]` blocks (full Windows/non-Windows copies) — violates our zero-regression-by-review-ability preference; keep single list + platform-keyed deltas.

## PR #1400 — MinGW support (the Phase 1 glue answer)

<https://github.com/pysam-developers/pysam/pull/1400> — theAeon (Andrew Robbins), 2026-03-24, no comments/no updates since. Body: "Supersedes #1274. Needs some work to fix warnings and ci." Files: `setup.py` (+278/−93), `setup.cfg` (+3), `ci.yaml` (+35). Diff based on current master (Python 3.8–3.14 matrix).

### The CI glue (highest-value artifact for us)

```yaml
- uses: actions/setup-python@v5
  id: setup-python
  with: { python-version: '${{ matrix.python-version }}' }

- uses: msys2/setup-msys2@v2
  with:
    msystem: ucrt64
    install: >-
      base-devel mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-make
      mingw-w64-ucrt-x86_64-pkgconf mingw-w64-ucrt-x86_64-curl
      mingw-w64-ucrt-x86_64-libdeflate mingw-w64-ucrt-x86_64-bzip2
      mingw-w64-ucrt-x86_64-zlib mingw-w64-ucrt-x86_64-xz
      mingw-w64-ucrt-x86_64-openssl mingw-w64-ucrt-x86_64-libsystre
      mingw-w64-ucrt-x86_64-libiconv

- name: Build (Windows)
  shell: msys2 {0}
  run: sh -c '$(cygpath "${{ steps.setup-python.outputs.python-path }}") setup.py build'
```

This is the documented-nowhere recipe our STACK.md rated MEDIUM confidence: **run the UCRT64 shell, but invoke python.org's interpreter via `cygpath`-converted absolute path**, so GCC compiles against python.org headers/libraries. Note it does *not* need `mingw-w64-ucrt-x86_64-python` (unlike #1274) — the MSYS2 side provides only the toolchain and C libraries.

It pairs with `setup.cfg`:

```ini
[build_ext]
compiler = mingw32
```

### Other mechanics differing from #1274

- htslib built via `lib-shared` (not `lib-static`); links `htslib/hts-3.lib` import library
- Internal cross-extension refs by build-output path: `build/lib.<platform>-<cache_tag>/pysam/libchtslib{EXT_SUFFIX}` — self-locating, no `:` prefix needed
- `libraries_for_pysam_module = []` on Windows; all deps folded into each module's `extra_objects`

### Known flaws (why "needs work" — and our zero-regression red line)

1. **`[build_ext] compiler = mingw32` is unconditional in shared `setup.cfg`** — would force the mingw32 compiler selection on Linux/macOS checkouts; a cross-platform regression of exactly the kind our project forbids. If we adopt the mechanism, it must be injected per-invocation (`setup.py build --compiler=mingw32` or env) or platform-gated, never committed globally.
2. Unfinished artifacts: `sys.platform == "win32"` branch with broken indentation, "Example continues..." comments, `htslib_make_options` reduced to `{'LIBHTS_OBJS': ''}`.
3. No test results published; no maintainer feedback yet (submitted ~7 months before this review, zero activity).

## Maintainer stance (strategic input for Decision 1 & 2)

From PR #1274 comments, 2025-03-18 — jmarshall (pysam/htslib maintainer):

> "Most likely I will only be interested in merging an **MSYS2-based approach** such as @teepean's. What you're describing for MSVC support is **too invasive for a niche platform**."

> "AIUI MSYS2 produces native executables without unusual dependencies. If this is the case, **or if pysam uses delvewheel when building wheels**, this is irrelevant."

And on the stalled PR, 2024-04-10:

> "Please add a Windows build to the job matrix in ci.yaml so that we can see this build in operation." — (contributor couldn't; PR stalled. Our CI-01 deliverable is exactly this ask.)

**Implications:**

- Upstream's merge ceiling is the MSYS2 route. Our Phase 3 (MSVC build system) will likely remain fork-only, permanently. Price it in: upstreamable-portability-patches framing applies to Phases 1–2, not 3.
- jmarshall explicitly blesses **UCRT64-built wheels repaired with delvewheel** as a legitimate shipping form. Combined with Decision 2 (fork GitHub Releases first), a credible alternative to "MSVC-only wheels" exists: UCRT64 + delvewheel wheels could ship *earlier* (Phase 1 toolchain all the way through Phase 4 CI), with MSVC as a later hardening milestone. **Decision 1 should be re-examined in discuss-phase before Phase 4 planning** — this file is the evidence.
- Caveat on the quote: a UCRT64 wheel embeds `libgcc_s_seh-1.dll`/`libwinpthread-1.dll` + htslib's dep DLLs via delvewheel; CRT itself is UCRT (ships with Windows 10+). ABI-safe for python.org CPython as long as no fd/FILE* cross boundaries with different CRTs — our existing constraint analysis stands.

## MSVC empirical pain list (Phase 3 / BUILD-02 input)

theAeon's field notes from attempting MSVC-Python + GCC-built htslib (same PR thread, 2025-03-18) — independently corroborates our CONCERNS inventory:

- Cython extension sources contain POSIX-isms unusable under MSVC
- **MSVC cannot link GCC-produced `.a` files** → needs GNUToMS-style conversion or htslib built to produce `.lib` (htslib makefile's `build-shared`/`lib-shared` path already emits one)
- `strcasecmp`→`_stricmp`, `STDIN_FILENO`→`_fileno(stdin)` mapping needed (matches our `libc` mapping research flag)
- htslib **data-variable exports get name-mangled** under MSVC (symbol decoration) — beyond function-level issues
- **samtools `coverage.c` uses VLAs; MSVC does not support VLA** — teepean's reply: "AFAIK clang-cl supports VLAs" → reinforces our pre-registered clang-cl fallback (ROADMAP Phase 3 spike)
- Existing MSVC port of htslib exists as reference: <https://github.com/refresh-bio-sandbox/htslib-msvc> (refresh-bio-sandbox, develop branch)

## Mapping to our roadmap

| Phase | Take from upstream | Guard against |
|---|---|---|
| 1 (MinGW build) | #1400's setup-python+cygpath+msys2 CI glue; #1274's `sh ./configure`, `extra_objects` link layout, `:`-prefixed internal libs, `--export-all-symbols` | global `setup.cfg` compiler override; MSYS2-python-only assumption |
| 2 (portability, tests green) | #1274's 958-test baseline & known-failure list as TEST-01 acceptance comparator; samtoolsshell PATH failures as expected PORT work items | commented-out symbol-conflict check — must instead make `nm`/`llvm-nm` work or port the checker |
| 3 (MSVC) | theAeon pain list as spike checklist; htslib-msvc repo reference; `lib-shared` `.lib` emission | assuming MSVC upstreamability (jmarshall: no) |
| 4 (CI + wheels) | jmarshall's delvewheel remark; his "add Windows to ci.yaml" ask as the CI-01 shape | shipping before the Decision-1 re-evaluation happens |

## Sources

- PR #1274: <https://github.com/pysam-developers/pysam/pull/1274> (diff + full comment thread reviewed 2026-10-09)
- PR #1400: <https://github.com/pysam-developers/pysam/pull/1400> (diff reviewed)
- PR #964: <https://github.com/pysam-developers/pysam/pull/964>
- Issue #1375 closure: <https://github.com/pysam-developers/pysam/issues/1375>
- refresh-bio-sandbox/htslib-msvc: <https://github.com/refresh-bio-sandbox/htslib-msvc>
- Related internal docs: `STACK.md` (Phase 1 glue MEDIUM flag), `ARCHITECTURE.md` (short-circuit autotools, cross-extension linking), `.planning/codebase/CONCERNS.md` (nm/ld checking, VLA, libc mappings)
