---
phase: 03-msvc
plan: "04"
subsystem: infra
tags: [msvc, cl-exe, link-exe, dllimport, implib, def-exports, lzma, zlib-win, nonstdc-gate, build-iteration]

requires:
  - phase: 03-msvc/01
    provides: D-17 dirname implib shape + compiler-gate idiom this plan's link layer consumes
  - phase: 03-msvc/02
    provides: vendor trees + probe discipline (xz feature-define gap discovered and closed here)
  - phase: 03-msvc/03
    provides: the wired MSVC machine (module graph, shim layer, /DEF + /IMPLIB machinery, _venv-msvc) driven to green here
provides:
  - Full green MSVC build: pip install -e . under _venv-msvc compiles + links all 13 extensions + bundled htslib/htscodecs/samtools/bcftools + vendored deps, symbol gate green, zero C4013 residue
  - import + smoke green on MSVC artifacts (BAM write/read round-trip, samtools + bcftools dispatch)
  - Out-of-tree MSVC build (setup.py build) green through the D-17 /IMPLIB: path with the gate reading the emitted .lib set — Phase 4's bdist_wheel shape proven
  - Complete win32/msvc/ POSIX mapping layer (non-stdc gate closed; every legacy name maps to an always-declared underscore spelling)
  - Cross-module binding under MSVC: HTSLIB_EXPORT dllimport consumer arm + three /DEF lists + exact-name internal libraries
  - Zero-regression control re-proven: full UCRT64 rebuild + smoke green on the phase-final tree after config.h alternation back
affects: [03-05 suite/close (MSVC artifacts for the 1027-test suite run), Phase 4 CI/wheel (out-of-tree shape proven)]

actuals:
  tokens: 12239   # chars/4 over the realized diff (48957 diff chars / 4; estimate was 50000)
  tasks: 3
  commits: 7      # measured: git rev-list --count e307350b..HEAD

tech-stack:
  added: []
  patterns:
    - "MSVC cross-module binding: annotated API exports via HTS_BUILDING_LIBRARY dllexport; consumers see dllimport through hts_defs.h's consumer arm; un-annotated families ride /DEF: lists; data symbols REQUIRE the dllimport declaration site (no linker auto-import)"
    - "non-stdc names gate closure: _CRT_DECLARE_NONSTDC_NAMES=0 in the /FI header plus explicit fixed-arity underscore mappings — deterministic declarations, no reliance on UCRT legacy spellings except the fd trio (declared against the still-exported legacy symbols)"
    - "fd trio declared-not-mapped: function-like read/write/close macros mangle member calls (hFILE_backend->read); plain declarations bind the UCRT legacy exports"
    - "off_t defined at _lseeki64 width (the UCRT's open-gate off_t is 32-bit long — hFILE offsets would truncate >2GiB)"

key-files:
  created:
    - win32/msvc/dirent.h
    - win32/samtools_exports.def
    - win32/bcftools_exports.def
  modified:
    - setup.py
    - win32/msvc/msvc_compat.h
    - win32/msvc/unistd.h
    - win32/msvc/pthread_win32.c
    - win32/chtslib_exports.def
    - htslib/htslib/hts_defs.h
    - pysam/htslib_util.h
    - vendor/regex/tre.h
    - vendor/README.md
    - devtools/msvc-build.md
    - bcftools/abuf.c + abuf.c.pysam.c
    - bcftools/hex.h
    - bcftools/variantkey.h
    - bcftools/version.c + version.c.pysam.c
    - bcftools/vcfgtcheck.c + vcfgtcheck.c.pysam.c

key-decisions:
  - "dllimport belongs at the header declaration site, not the /FI shim: MSVC takes the LAST declaration's linkage (verified live), so only hts_defs.h's own consumer arm can make consumers see dllimport — the plan's \".def closes data gaps\" assumption is falsified on MSVC (link.exe has no auto-import)"
  - "internal library names carry the module lib- prefix on the MSVC arm (link.exe opens .lib arguments literally; GNU ld's -l double NAME/libNAME search is what made the unprefixed spelling work on MinGW)"
  - "/GL- on the MSVC arm: distutils' /GL+/LTCG makes the cl 14.50 backend ICE on filter_decoder.c (C1001/LNK1000); upstream xz MSVC builds never use /GL; /O2 stays"
  - "xz consumes the full autotools-equivalent feature define set (decoders/encoders/checks/matchers/lzip); the bare three-define no-config route left filter_decoder.c's decoders[] empty, which cl ICEs on"
  - "off_t and min/max forced the non-stdc gate decision: closing _CRT_DECLARE_NONSTDC_NAMES kills stdlib's min/max macros (stats_isize/edlib define same-named functions) and the 32-bit off_t; everything the trees need then maps explicitly"
  - "MSVC-path compile flags ride extra_compile_args: c99_compile_args' set_executables plumbing is a no-op under MSVCCompiler (no compiler/compiler_so attributes); its probe-skip arm stays"

patterns-established:
  - "iteration discipline held: every compile gap landed in win32/msvc/ (shim), setup.py (module graph/flags), or /DEF lists; the only per-source edits are constructs no macro layer can fix (void* arithmetic, [static N], stray ;;), each guarded with #else-verbatim or a pure qualifier drop per the 03-01 precedent"
  - "C4013 authority: pip's editable build hides compiler output on success — the zero-implicit-declaration proof must come from a direct setup.py build whose warnings stream to the log"

requirements-completed: [BUILD-02]  # copied verbatim from PLAN frontmatter (shared ID — ready-ids gate holds it until all phase-03 plans finish)

coverage:
  - id: D1
    description: "Editable MSVC build green end-to-end: pip install -e . --no-build-isolation under _venv-msvc (llvm-nm on PATH) builds all 13 extensions through the symbol gate; smoke_test.py green on the MSVC artifacts"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "pip install -e . --no-build-isolation -> build-exit=0 (fresh full compile in pip's throwaway temp); devtools/smoke_test.py -> smoke OK, smoke-exit=0 (BAM generate + BGZF magic + 24 alignments read + 44118 vcf lines)"
        status: pass
      - kind: unit
        ref: "grep -c 'warning C4013' /tmp/msvc-oot.log == 0 over a full fresh setup.py build with visible compiler output (the authoritative instrument; pip swallows output on success)"
        status: pass
      - kind: integration
        ref: "gate-ran evidence: standalone llvm-nm -g -P sweep over the 13 emitted .libs -> 1313 parsed symbol rows (libchtslib 1241); never-vacuous guard structurally fires on zero"
        status: pass
    human_judgment: false
  - id: D2
    description: "Out-of-tree MSVC build (the D-17 /IMPLIB: wheel-path shape): setup.py build green, gate reads the emitted .lib set in build/lib.win-amd64*/pysam/"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "setup.py build -> exit=0; 13 .lib files in build/lib.win-amd64-cpython-313/pysam/; llvm-nm -g -P libchtslib...lib lists 1241 symbol rows; PyInit_libcalignedsegment T listed from an extension lib; zero CalledProcessError / gate-read-no-symbols"
        status: pass
    human_judgment: false
  - id: D3
    description: "UCRT64 zero-regression control on the phase-current tree + MSVC-path process-surface audit"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "MSYSTEM=UCRT64 pip install -e . (full rebuild after config.h alternation back to configure output; GCC-flavored keys restored) + smoke_test.py -> ucrt64-final-exit=0, smoke OK"
        status: pass
      - kind: manual_procedural
        ref: "semantic subprocess audit vs e53be051: run_make_print_config 2->2, run_configure 3->3, run_make 2->2, subprocess refs 7->7; zero added lines introduce subprocess/run_configure/run_make/run_nm calls (textual grep=1 is the moved wrapper line, -/+ pair in one hunk — documented criterion deviation)"
        status: pass
    human_judgment: false

duration: 118 min
completed: 2026-10-12
status: complete
plan_head_before: e307350bbaffc7f07adfb70ce25d6a2c4bfcda29
plan_head_after: 684b0912c263e46d8b074bb367d11dcab8ee296f
---

# Phase 03 Plan 04: First Full MSVC Build — Tracer, Out-of-Tree, Zero-Regression Summary

**The wired MSVC machine driven to a full green build through 27 logged iterations: 13 extensions + bundled htslib/htscodecs/samtools/bcftools + vendored deps compile and link under cl 14.50, import, round-trip a BAM, and dispatch samtools/bcftools — with the out-of-tree (wheel-path) build green through the D-17 gate on .lib and the UCRT64 control re-proven on the same tree.**

## Performance

- **Duration:** 118 min
- **Started:** 2026-10-12T13:35:53Z
- **Completed:** 2026-10-12T15:33:33Z
- **Tasks:** 3/3
- **Files modified:** 21
- **Build iterations:** 27 logged compile/link cycles (iter1-iter26 inplace + out-of-tree rerun)

## Accomplishments

- BUILD-02's core deliverable exists: `pip install -e . --no-build-isolation` under `_venv-msvc` (plain Git Bash, setuptools-located cl, llvm-nm on PATH) completes a fresh full build of every extension through the BUILD-03 symbol gate; `import pysam` works; `devtools/smoke_test.py` passes all four steps on the MSVC artifacts (BGZF magic verified byte-level, 24 alignments read back, both dispatch families exercised).
- The out-of-tree shape Phase 4 needs is proven: `setup.py build` (non-inplace) is green, emits all 13 import libraries into `build/lib.win-amd64-cpython-313/pysam/`, the gate reads them (1241 symbol rows in libchtslib's), and `PyInit_*` entries list through llvm-nm.
- The centralized shim layer grew to the complete POSIX surface the full ~200-TU compile actually exercises — including the three structurally hard pieces the plan could not pre-enumerate: the UCRT non-stdc names gate (closed, with every legacy name mapped to an always-declared underscore spelling), a 64-bit off_t (the open gate's spelling is 32-bit and would truncate hFILE offsets), and cross-module dllimport binding for htslib data symbols.
- Zero-regression held: after all MSVC-path changes, the full UCRT64 editable rebuild re-executed real configure (config.h alternation verified by restored GCC-flavored keys) and passed the smoke — dual-green on one checkout; the MSVC path adds zero process-spawning calls (semantic audit vs the phase-plan commit).

## Task Commits

Each task was committed atomically; Task 1's gap closures landed as they were proven (plan's "commit gap closures as they land"):

1. **Task 1: End-to-end MSVC build + import + dispatch smoke (tracer)** — 7 gap-closure commits: `0aa95885` (shim POSIX closure: R_OK/S_*/fixed-arity io mappings, dirent.h drop-in + impl, nanosleep), `ecc0e849` (export-surface closure: 3 .def files), `fc471ae3` (module-graph corrections: /std:c11+/utf-8+/GL- via extra_compile_args, config_vars.h backslash escape, xz TU exclusions + feature defines, tre.h compat edit 2), `d77beaef` (non-stdc gate closure + complete POSIX io mapping), `f44e42b6` (dllimport consumer arm + exact implib names), `fd6f7510` (MSVC-rejected C constructs in bcftools), `684b0912` (fd trio declared-not-mapped fix)
2. **Task 2: Out-of-tree MSVC build — D-17 /IMPLIB: path + gate on .lib** — no file changes (verification-only; the fixes it surfaced were folded into the commits above)
3. **Task 3: UCRT64 zero-regression control + subprocess audit** — no file changes (both verifications green)

## Files Created/Modified

- `win32/msvc/msvc_compat.h` — non-stdc gate closure, complete underscore mappings (access/chmod/getcwd/mktemp/strdup/lseek/rmdir/ftruncate/getpid/popen/pclose/mkdir/strtok_r/setmode/stat->_stat64/O_* flags), R_OK/F_OK/W_OK/X_OK + S_* constants, 64-bit off_t, SSIZE_MAX/PATH_MAX, NOMINMAX, fd-trio declarations (not macros — member-mangling lesson), nanosleep declaration
- `win32/msvc/dirent.h` (new) + `pthread_win32.c` — dirent drop-in over FindFirstFileA + nanosleep implementation
- `win32/msvc/unistd.h` — vendored getopt.h include (MinGW-parity declarations)
- `win32/chtslib_exports.def` — 31 exports: 7 plan-enumerated + htslib data (DATA keyword) + zlib/regex/shim families + htslib_util symbols
- `win32/samtools_exports.def` / `win32/bcftools_exports.def` (new) — the dispatch families libcutils binds
- `htslib/htslib/hts_defs.h` — HTSLIB_EXPORT consumer arm = dllimport under _MSC_VER (MinGW arm empty, byte-identical)
- `pysam/htslib_util.h` — guarded dllimport for pysam_seq_comp_table
- `setup.py` — /std:c11+/utf-8+/GL- via extra_compile_args (set_executables is a no-op under MSVCCompiler), config_vars.h C-string backslash escape, xz TU exclusion set + feature defines, -Dhidden= removed, internal library names lib-prefixed on the MSVC arm, /DEF wiring for the two tool modules
- `vendor/regex/tre.h` — compat edit 2 (three `hidden` qualifiers dropped; provenance rows updated in vendor/README.md)
- `devtools/msvc-build.md` — flags discipline + export-def drift alarm documented
- bcftools sources (guarded or qualifier-only): abuf ×2 (void*→uint8_t* under _MSC_VER), hex.h + variantkey.h + version.c ×2 ([static N] drops), vcfgtcheck ×2 (stray ;;)

## Decisions Made

- dllimport at the header declaration site (hts_defs.h consumer arm) — the /FI shim cannot win (MSVC takes the last declaration's linkage; verified live with the cl probe)
- fd trio as declarations against UCRT legacy exports (macros mangled `hFILE_backend->read(...)` member calls — the macro approach is structurally wrong for names used as struct members)
- /GL- despite /O2: the LTCG backend ICE is deterministic on filter_decoder.c; matching upstream xz's MSVC configuration is the safest variant
- Keep the c99 probe-skip arm (prevents the unportable probe abort) while carrying the actual flags on extra_compile_args

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] /std:c11 /utf-8 never reached the cl command line**
- **Found during:** Task 1 (iteration 1 — flags absent from the echoed failing command)
- **Issue:** 03-03 applied c99_compile_args' return through `Compiler.set_executables('compiler'/'compiler_so')` — attributes UnixCCompiler defines but MSVCCompiler does not; the plumbing is a verified no-op under cl
- **Fix:** Flags ride `extra_compile_args` in the MSVC module-graph block (later joined by /GL-); the probe-skip arm stays
- **Verification:** `/std:c11 /utf-8` visible in every echoed command line from iteration 2 on
- **Committed in:** fc471ae3

**2. [Rule 1 - Bug] config_vars.h generated invalid C string escapes**
- **Found during:** Task 1 (iteration 4 — C2153 on hts.c:159)
- **Issue:** Windows paths in the generated `#define HTS_CPPFLAGS "...vendor\xz\src..."` contain `\x` + non-hex digit — a hard C2153 under cl
- **Fix:** write_configvars_header escapes backslashes; POSIX paths carry none, output byte-identical there
- **Verification:** hts.c compiles; full builds green
- **Committed in:** fc471ae3

**3. [Rule 3 - Blocking] MSVC LTCG internal compiler error**
- **Found during:** Task 1 (iteration 8 — C1001 UTC p2 on filter_decoder.obj, then LNK1000 IMAGE::BuildImage)
- **Issue:** distutils' default /GL + link /LTCG crashes the cl 14.50 backend
- **Fix:** `/GL-` on the MSVC arm (matches upstream xz CMake Release, which never uses /GL; /O2 stays)
- **Verification:** All 13 extensions link clean from iteration 9 on
- **Committed in:** fc471ae3

**4. [Rule 3 - Blocking] xz module graph: empty decoders[] array ICE + variant/tool TUs in the glob**
- **Found during:** Task 1 (iterations 5-7 and 10)
- **Issue:** The recursive liblzma glob included the HAVE_SMALL CRC variants (table collision C2369), the standalone tablegen tools, and both mt codecs; and the bare three-define route left `decoders[]` empty (C4034 then C1001)
- **Fix:** Exclusion tuple (7 tool/small TUs) + the full feature define set (11 decoders + 11 encoders + checks + match finders + lzip); documented in vendor/README.md
- **Verification:** vendor tree compiles + libchtslib links
- **Committed in:** fc471ae3

**5. [Rule 3 - Blocking] global -Dhidden= collided with htslib locals**
- **Found during:** Task 1 (iteration 5 — textutils.c:246 `int hidden`)
- **Issue:** The musl regex visibility macro, defined globally on the MSVC arm, wiped every `hidden` identifier in htslib
- **Fix:** Qualifier dropped from tre.h's three declarations (compat edit 2, provenance updated); the define is gone
- **Verification:** textutils.c + regex TUs compile together
- **Committed in:** fc471ae3

**6. [Rule 2 - Missing Critical] cross-module export surface beyond the plan's enumeration**
- **Found during:** Task 1 (link phase, LNK2001-driven)
- **Issue:** link.exe exports only dllexport + /DEF entries (GNU ld's --export-all-symbols had covered: the dispatch families, htslib's un-annotated data, the zlib API, the regex API, the shim surface, htslib_util's symbols)
- **Fix:** samtools_exports.def + bcftools_exports.def (new) + chtslib_exports.def expanded to 31 entries; /DEF wired for the tool modules
- **Verification:** every consumer links; LNK2001 remains the drift alarm
- **Committed in:** ecc0e849, f44e42b6

**7. [Rule 3 - Blocking] consumer data references cannot bind through .def DATA exports**
- **Found during:** Task 1 (iteration 19 — seq_nt16_* LNK2001 persisted after the .def listed them)
- **Issue:** MSVC has no linker auto-import (GNU ld rewrites direct data refs through __imp_); the plan's ".def closes export gaps" mechanism is physically insufficient for data symbols. Verified additionally: a /FI-side dllimport declaration cannot win (MSVC takes the last declaration's linkage — cl probe PASS with C4273, linkage unchanged)
- **Fix:** hts_defs.h HTSLIB_EXPORT consumer arm = dllimport under _MSC_VER (annotated data + all 447 functions); guarded dllimport for pysam_seq_comp_table in pysam/htslib_util.h; MinGW arms byte-identical
- **Verification:** libcsamtools + all API modules link
- **Committed in:** f44e42b6

**8. [Rule 3 - Blocking] link.exe could not resolve the internal libraries (LNK1181)**
- **Found during:** Task 1 (iteration 16)
- **Issue:** Consumers requested `chtslib<suffix>.lib`; the emitted implib is `libchtslib<suffix>.lib`. GNU ld's -l searches both NAME and libNAME — link.exe opens the argument literally
- **Fix:** internal_*_libraries carry the module lib- prefix on the MSVC arm (emission, gate probe, and consumer names now match end to end)
- **Verification:** all consumer links resolve
- **Committed in:** f44e42b6

**9. [Rule 2 - Missing Critical] stdlib min/max macros vs the trees' own functions + 32-bit off_t**
- **Found during:** Task 1 (iterations 13-15)
- **Issue:** UCRT stdlib.h defines min()/max() macros under _CRT_INTERNAL_NONSTDC_NAMES; stats_isize.c/edlib.c define same-named static functions (C2059). The same open gate gives sys/types.h's off_t as 32-bit `long` — hFILE.offset/hseek/htell would truncate >2GiB
- **Fix:** Close the non-stdc names gate (_CRT_DECLARE_NONSTDC_NAMES=0 in the /FI header) and map every legacy name the trees use to always-declared underscore spellings; define off_t at the _lseeki64 width; stat->_stat64 object-like macro (struct tag + call, 64-bit st_size); NOMINMAX for windows.h's pair
- **Verification:** all TUs compile; MSVC build's hFILE offsets are 64-bit
- **Committed in:** d77beaef

**10. [Rule 1 - Bug] fd-trio macros mangled struct member calls**
- **Found during:** Task 2 (first fresh out-of-tree compile — C2039 `_read` not a member of hFILE_backend)
- **Issue:** The compat-level `read/write/close/open` function-like macros expanded `backend->read(...)` member calls; the earlier inplace tree had pre-macro objects masking it
- **Fix:** fd trio declared (UCRT legacy spellings still export — the link proves it), not mapped; setmode stays a macro (no member collisions)
- **Verification:** hfile.c compiles fresh; both build shapes green
- **Committed in:** 684b0912

**11. [Rule 3 - Blocking] MSVC-rejected C constructs in bcftools sources**
- **Found during:** Task 1 (iterations 22-25)
- **Issue:** void* pointer arithmetic in abuf.c (GNU extension), four `[static N]` array-parameter qualifiers (hex.h, variantkey.h ×2, version.c), a stray `;;` struct member terminator (vcfgtcheck.c) — none fixable at any macro/header layer
- **Fix:** guarded uint8_t* under _MSC_VER with #else verbatim (abuf struct fields + local src/dst pointers); qualifier drops per the hts_internal.h precedent; the stray `;` removed. Every site edited in source + twin lockstep
- **Verification:** libcbcftools compiles and links; POSIX arms verbatim (UCRT64 rebuild green)
- **Committed in:** fd6f7510

### Documented plan-text vs MSVC-reality divergences (no missing work)

**12. Task 3's subprocess audit grep (== 0) flags the moved autotools wrapper line**
- The `+ htslib_make_options = run_make_print_config()` hit is 03-03's re-gating of the pre-existing unconditional call into the non-MSVC else arm — its `-` twin sits in the same diff hunk. Semantic audit: call-site counts unchanged (run_make_print_config 2→2, run_configure 3→3, run_make 2→2, subprocess refs 7→7); zero added lines introduce a process-spawning call. Recorded as criterion-as-written FAIL with rationale rather than gaming the grep (the 03-01 VLA-grep precedent).

**13. Task 1 acceptance "gap-closure commits confined to win32/msvc/*, exports.def, config.h.msvc, vendor/**, setup.py"**
- Also touched (all Rule 3 necessities, documented above): htslib/htslib/hts_defs.h + pysam/htslib_util.h (dllimport header-sites — no other layer can carry them), bcftools ×8 (MSVC-rejected constructs — no macro fix exists), devtools/msvc-build.md + vendor/README.md (documentation of the new discipline). Every shared-file edit keeps POSIX arms verbatim; the UCRT64 control is the enforcement proof.

---

**Total deviations:** 11 auto-fixed (2 Rule 1 bugs, 2 Rule 2 missing-critical, 7 Rule 3 blocking), 2 documented criterion divergences (both plan-text vs MSVC/linker reality; zero scope creep)
**Impact on plan:** All must_haves truths hold — the single happy path works end-to-end, every gap closure lives in the centralized artifacts (the three structurally-impossible classes are guarded per-source edits with POSIX bytes verbatim), and the UCRT64 control stayed green.

## Issues Encountered

- pip's editable build hides compiler output on success (setuptools captures subprocess output and re-emits only on failure) — an early "green" pip verify had a structurally vacuous C4013 count and stale-artifact imports; discovered when the first fresh out-of-tree compile failed on the fd-macro bug the inplace tree had masked. Resolution: clean-tree rebuilds for every authoritative check + setup.py build as the C4013 instrument.
- The UCRT64 link phase emits LNK4286 warnings (lzma_* imported by htslib TUs against the vendored definitions) — cosmetic dllimport/dllexport mixing inside one module from xz's api headers; links clean; not chased.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all paths are real implementations; the deferred-validation simplifications remain the three 03-03 documented ones (joined value_ptr 32-bit, recursive default mutex, musl-regex behavior at suite time — plan 03-05).

## Next Phase Readiness

- Plan 03-05 can run the 1027-test suite against the MSVC artifacts (the editable install under _venv-msvc is the import target; rebuild discipline in devtools/msvc-build.md).
- The out-of-tree build shape is proven for Phase 4's bdist_wheel; A7's clean-machine DLL closure audit is Phase 4's CI-02 gate as planned.
- Fork CI ubuntu/macos green-check rides plan 03-05's phase close on the final SHA.

## Self-Check: PASSED

All 3 created files exist on disk (win32/msvc/dirent.h, win32/samtools_exports.def, win32/bcftools_exports.def); all 7 task commits (0aa95885, ecc0e849, fc471ae3, d77beaef, f44e42b6, fd6f7510, 684b0912) are ancestors of HEAD; ledger recount confirms 7 commits between plan_head_before (e307350b) and HEAD, matching frontmatter actuals.

---
*Phase: 03-msvc*
*Completed: 2026-10-12*
