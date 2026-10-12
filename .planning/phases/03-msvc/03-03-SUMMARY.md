---
phase: 03-msvc
plan: "03"
subsystem: infra
tags: [msvc, cl-exe, setup.py, config-h, shim, pthread, win32, implib, def, exports, two-level-dispatch]

requires:
  - phase: 03-msvc/01
    provides: D-17 dirname implib shape (both arms), D-20 compiler gate, C99 site closures 03-03's shim and dispatch build on
  - phase: 03-msvc/02
    provides: vendor/{zlib,bzip2,xz,regex} cl-proven trees + devtools/msvc_compile_probe.py + recorded include/define sets wired verbatim here
provides:
  - setup.py two-level dispatch — win-amd64 MSVC module-graph arm (gate, pre-baked config rewrite, hard-coded 52-TU LIBHTS_OBJS mirror, vendored+shim source assembly) with the UCRT64 path byte-identical
  - win32/config.h.msvc — curated pre-baked htslib configuration (deterministic per-run rewrite)
  - win32/msvc/ shim layer — msvc_compat.h (/FI) + 4 __GNUC__-forwarding drop-ins + pthread_win32.c Win32 implementation + shim_selftest.c dual-toolchain sentinel
  - win32/chtslib_exports.def — supplementary seven-symbol export list
  - build_ext compiler_type-msvc arm (late /IMPLIB: D-17 shape, /DEF:) + symbol-gate .lib/.dll.a split + c99 probe /std:c11 skip
  - _venv-msvc (untracked environment) + devtools/msvc-build.md rebuild-discipline doc
affects: [03-04 MSVC build integration (the machine this plan wires), 03-05 suite/close, Phase 4 CI/wheel]

actuals:
  tokens: 14447   # chars/4 over the authored diff (57790 diff chars / 4; estimate was 45000)
  tasks: 3
  commits: 3      # measured: git rev-list --count 5867f01a..HEAD

tech-stack:
  added: []
  patterns:
    - "two-level toolchain dispatch: sysconfig platform selects the module graph at setup.py module level, compiler.compiler_type selects flags inside build_ext"
    - "__GNUC__ include_next forwarder arm in every drop-in shim header + a dual-toolchain selftest TU (cl probe AND gcc -fsyntax-only) as the UCRT64 byte-identity sentinel"
    - "pre-baked config.h pattern (Pillow/libusb): checked-in win32/config.h.msvc deterministically rewritten over htslib/config.h every MSVC run (alternation-safe with UCRT64 configure)"
    - "static-initializable pthread primitives: INIT_ONCE member inside pthread_mutex_t gives PTHREAD_MUTEX_INITIALIZER a race-free lazy CRITICAL_SECTION init"

key-files:
  created:
    - win32/config.h.msvc
    - win32/chtslib_exports.def
    - win32/msvc/msvc_compat.h
    - win32/msvc/unistd.h
    - win32/msvc/strings.h
    - win32/msvc/sys/time.h
    - win32/msvc/pthread.h
    - win32/msvc/pthread_win32.c
    - win32/msvc/shim_selftest.c
    - devtools/msvc-build.md
  modified:
    - setup.py
    - .gitignore

key-decisions:
  - "Gate restructure keeps the UCRT64 fail-fast message byte-identical and adds a non-exiting MSVC banner (introspection must work); fail-fast for missing Build Tools is setuptools' own compile-time error, documented in msvc-build.md (D-03/D-13 lockstep)"
  - "LIBHTS_OBJS mirror is the 52-entry print-config expansion (27 core + 11 cram + 14 htscodecs), programmatically count-checked IDENTICAL against htslib/Makefile at write time; hfile_libcurl.o absent = --disable-libcurl parity"
  - "Shim surface extended beyond the plan-enumerated list to the empirically required families (pthread_attr_*, pthread_equal, PTHREAD_MUTEX_INITIALIZER/PTHREAD_ONCE_INIT static init) — without them the first 03-04 link fails"
  - "mutex substrate: CRITICAL_SECTION + embedded INIT_ONCE (lazy init) so PTHREAD_MUTEX_INITIALIZER works; default mutex type is recursive (substrate semantics, documented deviation)"
  - "The seven .def symbols are HTSLIB_EXPORT-annotated in the htslib 1.24 tree (research enumeration was stale); the .def still lists them per plan — dllexport + /DEF union-export is idempotent, keeping belt-and-braces coverage"

patterns-established:
  - "compiler_type msvc arm: zero GNU -Wl flags; exports via dllexport + /DEF, import library via late /IMPLIB: at the D-17 dirname (.lib), gate probe split .lib/.dll.a"
  - "vendor wiring copied verbatim from vendor/README.md's proven cl probe lines (single include/define source of truth)"

requirements-completed: [BUILD-02]  # copied verbatim from PLAN frontmatter (shared ID — ready-ids gate holds it until all phase-03 plans finish)

coverage:
  - id: D1
    description: "win-amd64 CPython passes the restructured setup.py gate (no UCRT64 message, no import-time exit) and completes module-level assembly with htslib/config.h deterministically rewritten from the curated win32/config.h.msvc; c99 probe skipped under cl (/std:c11 /utf-8)"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "D:/miniconda3/python.exe setup.py --name -> prints pysam, exit=0, MSVC banner, no UCRT64 message (re-run in final sweep)"
        status: pass
      - kind: unit
        ref: "grep HAVE_LIBBZ2 1 htslib/config.h == 1; grep HAVE___BUILTIN_CLZ htslib/config.h win32/config.h.msvc == 0/0; 17-key exclusion sweep over config.h.msvc all absent"
        status: pass
      - kind: unit
        ref: "UCRT64 control: MSYSTEM=UCRT64 _venv/bin/python.exe setup.py --name exit=0 after every task (real configure path intact)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Centralized win32/msvc/ shim layer: /FI compat header, four __GNUC__-forwarding drop-ins, Win32 pthread implementation (recursive CRITICAL_SECTION, condvar timedwait conversion, INIT_ONCE, FlsAlloc TLS, binary+exclusive mkstemp, no-op pthread_kill), dual-toolchain shim_selftest sentinel, seven-symbol supplementary exports.def"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "devtools/msvc_compile_probe.py pthread_win32.c shim_selftest.c -I win32/msvc -> 2 PASS, 0 FAIL (re-run in final sweep)"
        status: pass
      - kind: integration
        ref: "UCRT64 gcc -fsyntax-only -I win32/msvc shim_selftest.c -> FORWARDER-OK (forwarder arm; no MinGW header shadowed)"
        status: pass
      - kind: unit
        ref: "grep -c EXPORTS win32/chtslib_exports.def == 1; the seven enumerated symbols exactly"
        status: pass
    human_judgment: false
  - id: D3
    description: "MSVC module graph and build_ext arm fully wired: vendored+shim+htslib source assembly on libchtslib, HTS_BUILDING_LIBRARY (libchtslib-only), /FI + vendor include/define sets verbatim, prebuild autotools early-return, late /IMPLIB: at the D-17 dirname with .lib, /DEF: on libchtslib, gate-probe .lib/.dll.a split, _venv-msvc provisioned"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "PATH=/c/msys64/ucrt64/bin:$PATH _venv-msvc/Scripts/python.exe setup.py --name -> exit=0 (module graph assembles; final sweep)"
        status: pass
      - kind: unit
        ref: "grep HTS_BUILDING_LIBRARY //DEF: //IMPLIB: setup.py == 2/2/2; -Wl flags inside the msvc arm == 0 (diff-scoped); mingw arm verbatim in else"
        status: pass
      - kind: unit
        ref: "_venv-msvc python -c 'import Cython, pytest' -> VENV-OK"
        status: pass
      - kind: integration
        ref: "UCRT64 setup.py --name exit=0 after all MSVC additions (zero-regression control)"
        status: pass
    human_judgment: false

duration: 26 min
completed: 2026-10-12
status: complete
plan_head_before: 5867f01abcdf70a85c3e524f439a751c43aa5749
plan_head_after: 465adb7e15e1cb3e46587a7da6f05015c8ae970b
---

# Phase 03 Plan 03: MSVC Build Foundation Summary

**setup.py's Windows gate restructured into a two-level dispatch (win-amd64 -> MSVC module graph with pre-baked config.h.msvc, 52-TU htslib mirror, vendored+shim source closure; compiler_type -> link/compile flags with late /IMPLIB: D-17 shape, /DEF: union exports, .lib symbol gate) plus a centralized win32/msvc/ shim layer proven harmless to UCRT64 by a dual-toolchain sentinel.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-10-12T13:00:12Z
- **Completed:** 2026-10-12T13:26:50Z
- **Tasks:** 3/3
- **Files:** 12 authored (10 created, 2 modified)

## Accomplishments

- The miniconda interpreter now passes setup.py's gate into a real MSVC mode (banner, no import-time exit) and completes module-level assembly: htslib/config.h is deterministically rewritten from the checked-in curated win32/config.h.msvc every run, configure and make print-config never execute, and the hard-coded htslib_make_options carries a LIBHTS_OBJS mirror programmatically count-checked identical (52/52) to the htslib/Makefile print-config expansion.
- The MSVC POSIX/C99 gap is covered by one centralized shim layer: msvc_compat.h (force-included; _MSC_VER-guarded so UCRT64 sees an empty file) mapping the POSIX name storm (strcasecmp x229 class, fdopen, isatty, fileno, ssize_t, STDIN_FILENO, S_ISREG/S_ISDIR), four drop-in headers each with a __GNUC__ include_next forwarder arm, and a Win32 pthread implementation over CRITICAL_SECTION (natively recursive; INIT_ONCE-lazy static initializer), CONDITION_VARIABLE (absolute-to-relative timedwait), INIT_ONCE, FlsAlloc, plus gettimeofday/mkstemp(_O_BINARY|_O_EXCL)/usleep. shim_selftest.c is the permanent dual-toolchain sentinel — cl probe PASS and gcc -fsyntax-only PASS.
- The build_ext machinery is toolchain-split: the msvc arm emits a late /IMPLIB: at the D-17 dirname with .lib extension (overriding distutils' builtin — research-verified last-wins), /DEF:win32/chtslib_exports.def on libchtslib, zero GNU -Wl flags; the mingw32 arm is verbatim in the else. The symbol gate probes .lib under msvc / .dll.a under mingw32. HTS_BUILDING_LIBRARY is defined on libchtslib only, activating htslib's 447 HTSLIB_EXPORT dllexport annotations for cross-extension linking.
- _venv-msvc provisioned (Cython 3.3.0 + pytest + setuptools) and devtools/msvc-build.md mirrors msys2-bootstrap.sh's structure (prerequisites, zero-env builds, llvm-nm PATH, config.h alternation, --inplace --force discipline, zero-regression control) with fail-fast wording in D-03/D-13 lockstep with the setup.py banner.

## Task Commits

Each task was committed atomically:

1. **Task 1: Platform gate restructure + config.h.msvc + deterministic rewrite + c99 probe skip (tracer)** - `e177844a` (feat) — tracer gate re-ran verify end-to-end green; expanded
2. **Task 2: win32/msvc/ shim layer + shim_selftest + exports.def** - `9f1d7d7d` (feat)
3. **Task 3: MSVC module graph + build_ext msvc arm + gate .lib + _venv-msvc** - `465adb7e` (feat)

## Files Created/Modified

- `setup.py` — gate restructure + MSVC banner; MSVC arm of the HTSLIB_MODE shared branch (config.h.msvc rewrite, hard-coded 52-TU mirror dict, ws2_32 residue); MSVC module-graph block (vendor globs, /FI, defines, getopt private copies); prebuild early return; compiler_type split in build_extension and the symbol gate; c99 probe /std:c11 skip
- `win32/config.h.msvc` — curated pre-baked htslib config (compression libs, ISO headers, SIMD keys, PACKAGE_*, _FILE_OFFSET_BITS; every GCC-flavored probe key absent)
- `win32/msvc/{msvc_compat.h, unistd.h, strings.h, sys/time.h, pthread.h, pthread_win32.c, shim_selftest.c}` — the shim layer
- `win32/chtslib_exports.def` — the seven supplementary exports
- `devtools/msvc-build.md` — MSVC rebuild-discipline doc
- `.gitignore` — `_venv-msvc/`

## Decisions Made

- MSVC mode prints a banner instead of failing fast at import (introspection like `setup.py --name` must work); the actionable Build-Tools prerequisite lives in the banner text and msvc-build.md, mirrored verbatim (D-03/D-13).
- The htslib_objects override is scoped to `IS_MSVC_PYTHON and HTSLIB_MODE == 'shared'` — the documented Windows-supported mode — leaving the separate/external graphs untouched.
- HTS_BUILDING_LIBRARY appended to a NEW list per module (define_macros is shared object identity across modules — appending in place would leak the define to all 13 extensions).
- win32/getopt.c keeps its existing libchtslib slot on all Windows builds (zero-diff of the shared path) AND gains private copies in the three tool extensions on MSVC (D-16 isolation analogue; no system getopt exists under MSVC).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Block comment closed early by `*/` inside comment prose**
- **Found during:** Task 2 (first cl probe run)
- **Issue:** pthread.h's header comment contained `pthread_attr_*/pthread_equal`; the `*/` terminated the comment block mid-line, so the rest of the prose parsed as C code (winnt.h error cascade)
- **Fix:** Reworded to "the pthread_attr and pthread_equal families"; scanned all shim files for other mid-line `*/` hazards (none)
- **Files modified:** win32/msvc/pthread.h
- **Verification:** cl probe 2 PASS / 0 FAIL
- **Committed in:** 9f1d7d7d

**2. [Rule 2 - Missing Critical] Shim surface extended beyond the plan-enumerated list**
- **Found during:** Task 2 read_first (thread_pool.c/bam_sort inspection)
- **Issue:** The plan's bounded surface omitted families the tree actually uses: pthread_attr_{init,destroy,getstacksize,setstacksize,setdetachstate} (thread_pool.c:729-808; bam_sort.c.pysam.c:3162-3169), pthread_equal (thread_pool.c:63), static PTHREAD_MUTEX_INITIALIZER/PTHREAD_ONCE_INIT (hfile.c:1018, htscodecs utils.c:76, rANS_static4x16pr.c:858 — the latter two are inside the 52-TU mirror), pthread_key_delete, pthread_condattr_*
- **Fix:** Header declares the union (bounded by direct grep of every pthread reference in htslib/samtools/bcftools); INIT_ONCE-member mutex design makes the static initializers real
- **Files modified:** win32/msvc/pthread.h, win32/msvc/pthread_win32.c
- **Verification:** cl probe PASS over both shim TUs; surface covers every pthread_* token found in the trees
- **Committed in:** 9f1d7d7d

**3. [Rule 3 - Blocking] _venv-msvc lacked setuptools**
- **Found during:** Task 3 (first venv setup.py run)
- **Issue:** Python 3.12+ venvs no longer preinstall setuptools; setup.py imports it at module level
- **Fix:** `pip install setuptools` into _venv-msvc; devtools/msvc-build.md's install line updated with the rationale
- **Files modified:** devtools/msvc-build.md
- **Verification:** _venv-msvc setup.py --name exit 0; VENV-OK
- **Committed in:** 465adb7e

**4. [Rule 2 - Missing Critical] _CRT_SECURE_NO_WARNINGS in msvc_compat.h**
- **Found during:** Task 2 (cl probe C4996 on _open)
- **Issue:** The UCRT flags POSIX-spelled CRT entry points (_open, _mktemp_s, ...) deprecated; the MSVC path uses them intentionally and /W3 noise would drown real diagnostics across ~170 TUs in 03-04
- **Fix:** Defined centrally in the /FI header (project-standard suppression, no behavior change)
- **Files modified:** win32/msvc/msvc_compat.h
- **Verification:** cl probe re-run clean (C4996 gone)
- **Committed in:** 9f1d7d7d

### Documented plan-text vs tree-reality divergences (no missing work)

**5. The seven ".def gap symbols" are HTSLIB_EXPORT-annotated in the htslib 1.24 tree** (research enumeration was stale). The .def still lists exactly the seven per the plan and its verify — dllexport + /DEF union-export is idempotent, so the belt-and-braces purpose is served and drift on future htslib bumps still self-detects as LNK2001.

**6. HAVE_X86INTRIN_H omitted from config.h.msvc beyond the recipe's named exclusion list** — it is a GCC-header probe key (sam_internal.h:104 / simd.c:37 gate the SIMD nibble2base path on it together with HAVE_ATTRIBUTE_CONSTRUCTOR, which IS excluded); absence selects htslib's scalar fallback, the correct MSVC curation. Also omitted STDC_HEADERS (immaterial per config.h.in's own comment, not in the Keep list).

**7. Plan said "bzip2 eight-file set"; the library is 7 TUs** (03-02's documented upstream fact — the eighth .c is the pruned CLI). The glob picks up the 7.

---

**Total deviations:** 4 auto-fixed (1 bug, 2 missing-critical, 1 blocking), 3 documented divergences (research/plan-text vs tree reality; no scope change)
**Impact on plan:** No scope creep. All must_haves truths hold; the UCRT64 control stayed green after every task.

## Issues Encountered

- Task 1's restructure initially left the original `run_make_print_config` block in place alongside the moved one (double execution / MSVC crash); caught while re-reading the assembled branch before any verify run and removed — the else arm runs it exactly once, preserving the original print ordering.

## User Setup Required

None - no external service configuration required. (_venv-msvc already created by Task 3; Visual Studio Build Tools with the C++ workload is a pre-existing machine prerequisite, documented in devtools/msvc-build.md.)

## Next Phase Readiness

- The MSVC build machine is fully wired and introspectable: plan 03-04 can drive `setup.py build_ext --inplace` under _venv-msvc to a full build; the first failure class there is per-TU compile integration (e.g. remaining implicit-declaration gaps), not wiring.
- Zero-regression control green at module level after every task; full UCRT64 rebuild re-proof and fork CI ride plan 03-05's phase close (per plan).
- Known accepted simplifications for 03-04/03-05 to watch: pthread joined value_ptr carries 32 bits (no bundled consumer joins a value); default mutex type is recursive; musl-regex behavioral validation lands with the suite run (TRE is the documented fallback).

## Self-Check: PASSED

All 10 created files exist on disk; all 3 task commits (e177844a, 9f1d7d7d, 465adb7e) are ancestors of HEAD; ledger recount confirms 3 commits between plan_head_before (5867f01a) and HEAD, matching frontmatter actuals.

---
*Phase: 03-msvc*
*Completed: 2026-10-12*
