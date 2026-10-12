---
phase: 03-msvc
plan: "01"
subsystem: infra
tags: [msvc, mingw, setup.py, implib, setjmp, vla, c99, cython, utf-8, dispatch]

requires:
  - phase: 02-portability-tests
    provides: UCRT64 green baseline (1027 tests), #ifdef-guard + #else-verbatim idiom, dispatch setjmp crash fix in generated twins
provides:
  - D-17 fix — setup.py implib emission derived from get_ext_fullpath dirname (out-of-tree builds pass the BUILD-03 symbol gate)
  - D-20 closure — import/pysam.c template carries the Windows dispatch branch with compiler gating; regenerates both twins byte-identically
  - Compiler gate form for GCC builtins — defined(_WIN32) && !defined(_MSC_VER), once per file via a feature macro
  - C99 site closure — coverage.c VLA heap-allocated under _MSC_VER (both files), hts_internal.h array-parameter qualifier dropped
  - WR-01 closure — _collect binary read + UTF-8-with-replacement decode; TestDispatchOutputEncoding permanent regression test
affects: [03-02 vendoring, 03-03 MSVC build branch, 03-05 suite/close]

actuals:
  tokens: 3400   # chars/4 over the realized diff (13506 diff chars / 4)
  tasks: 3
  commits: 4     # measured: git rev-list --count e53be051..HEAD

tech-stack:
  added: []
  patterns:
    - "single-occurrence compiler gate: one #if defines <tool>_DISPATCH_GCC_BUILTIN_JMP, three #ifdef sites test it (satisfies count==1 grep gates while gating type+dispatch+exit)"
    - "template lockstep proof: sed 's/@pysam@/<tool>/g' import/pysam.c must diff clean against each twin"

key-files:
  created: []
  modified:
    - setup.py
    - import/pysam.c
    - samtools/samtools.pysam.c
    - bcftools/bcftools.pysam.c
    - samtools/coverage.c
    - samtools/coverage.c.pysam.c
    - htslib/hts_internal.h
    - pysam/libcutils.pyx
    - tests/PortabilityRegression_test.py

key-decisions:
  - "Compiler gate via feature macro (one #if defined(_WIN32) && !defined(_MSC_VER) per file defining <tool>_DISPATCH_GCC_BUILTIN_JMP) because each twin needs the gate at three sites (jmpbuf type, dispatch, exit) while the plan's grep gate demands exactly one occurrence of the condition string"
  - "VLA kept verbatim inside the #else arm (zero-regression red line wins over the plan's grep==0 criterion, which contradicts its own #else-verbatim action text); MSVC never sees the VLA — heap form + free sit under #if defined(_MSC_VER)"
  - "decode_bytes called positionally (encoding=None, 'replace') — Cython cdef helpers reject keyword-only calls in this file"

patterns-established:
  - "grep-gate-friendly compiler gating: define the gate macro once, test it with #ifdef at every site"
  - "lockstep verification: simulate devtools/import.py regeneration with sed and diff before committing template edits"

requirements-completed: [BUILD-02]  # copied verbatim from PLAN frontmatter (shared ID — ready-ids gate will hold it until all phase-03 plans finish)

coverage:
  - id: D1
    description: "D-17: out-of-tree UCRT64 builds emit import libraries beside the built modules and pass the BUILD-03 symbol gate"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "MSYSTEM=UCRT64 setup.py build (fresh) -> exit=0, 13 *.dll.a in build/lib.mingw*/pysam/ incl libchtslib, gate clean (no CalledProcessError)"
        status: pass
      - kind: integration
        ref: "tracer gate re-run of the same build -> exit=0"
        status: pass
    human_judgment: false
  - id: D2
    description: "D-20: dispatch setjmp branch synced into import/pysam.c template and compiler-gated in both twins (MSVC compiles the plain-setjmp arm)"
    requirement: BUILD-02
    verification:
      - kind: unit
        ref: "grep 'defined(_WIN32) && !defined(_MSC_VER)' count == 1 in import/pysam.c, samtools/samtools.pysam.c, bcftools/bcftools.pysam.c"
        status: pass
      - kind: integration
        ref: "sed s/@pysam@/samtools|bcftools/g template vs twin -> diff clean (regeneration reproduces twins byte-identically)"
        status: pass
      - kind: integration
        ref: "UCRT64 build_ext --inplace --force + devtools/smoke_test.py -> exit=0 (GCC builtin arm still executes)"
        status: pass
    human_judgment: false
  - id: D3
    description: "C99 surface closed for MSVC: coverage histogram heap-allocated under _MSC_VER in both files; hts_internal.h array-parameter qualifier dropped"
    requirement: BUILD-02
    verification:
      - kind: unit
        ref: "malloc(hist_size * sizeof(double)) + free(hist_data) present under #if defined(_MSC_VER) in coverage.c and coverage.c.pysam.c; VLA declaration sits only inside the #else arm"
        status: pass
      - kind: unit
        ref: "grep '\\[static ' htslib/hts_internal.h == 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "WR-01: dispatch-captured stdout decodes UTF-8 with replacement on every interpreter locale (binary read, no locale codec, no text-mode newline translation); permanent regression test in the suite"
    requirement: BUILD-02
    verification:
      - kind: unit
        ref: "tests/PortabilityRegression_test.py#TestDispatchOutputEncoding::test_cjk_header_comment_roundtrip (TDD: RED under cp936 -> GREEN after fix; full file 12 passed)"
        status: pass
      - kind: unit
        ref: "grep 'open(fn, \"rb\")' pysam/libcutils.pyx == 1; grep UnicodeDecodeError == 0"
        status: pass
    human_judgment: false

duration: 28 min
completed: 2026-10-12
status: complete
plan_head_before: e53be05180145e4856cb27ed3a5e861bf95c67b2
plan_head_after: 14cedd97d3cf0783ba2dca22d37d8c16891c819e
---

# Phase 03 Plan 01: Carried Fixes — D-17 implib, D-20 dispatch gate, C99 sites, WR-01 capture decode Summary

**Out-of-tree builds pass the symbol gate via dirname-derived implib emission; dispatch setjmp arms compiler-gated GCC-vs-MSVC with a template that regenerates both twins byte-identically; the tree's only VLA and [static] sites closed for MSVC; dispatch capture now binary-read + UTF-8-replace decoded with a permanent CJK regression test.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-10-12T11:56:51Z
- **Completed:** 2026-10-12T12:24:23Z
- **Tasks:** 3/3
- **Files modified:** 9

## Accomplishments

- D-17 closed: fresh non-inplace UCRT64 build (setup.py build) exits 0 end-to-end through the symbol gate; 13 import libraries emitted into build/lib.mingw_x86_64_ucrt_gnu-cpython-314/pysam/ (libchtslib included) — the emission and gate-probe paths now agree in both inplace and out-of-tree layouts.
- D-20 closed: import/pysam.c template now carries the Phase-2 Windows dispatch branch; all three files gate GCC __builtin_setjmp/__builtin_longjmp (and the void*[5] jmpbuf type) on a single `#if defined(_WIN32) && !defined(_MSC_VER)` feature-macro definition per file, so MSVC compiles the plain setjmp/longjmp arm instead of linking unresolved builtins. Verified: regeneration (sed @pysam@ substitution, devtools/import.py's exact transform) reproduces both twins byte-for-byte.
- BUILD-02 C99 surface closed: coverage.c + coverage.c.pysam.c histogram heap-allocated under `#if defined(_MSC_VER)` with free() on the single exit path (POSIX VLA bytes untouched); htslib/hts_internal.h `find_file_extension` array bound kept plain (qualifier dropped, documented exception).
- WR-01 closed TDD-style: `_collect` reads the capture file in binary mode and decodes via `decode_bytes` with replacement — locale-independent, never raises, no text-mode newline translation. RED under the cp936-default UCRT64 interpreter validated by the tdd-red-evidence classifier (RED_EVIDENCE_OK, JUnit XML); failing-direction miniconda probe recorded (unequal string, no exception); GREEN on UCRT64.

## Task Commits

Each task was committed atomically:

1. **Task 1: D-17 implib emission (tracer)** - `08e2526a` (fix) — tracer gate re-ran verify end-to-end, green; expanded
2. **Task 2: D-20 template lockstep + compiler gate; VLA + qualifier fixes** - `d3e77161` (fix)
3. **Task 3: WR-01 _collect binary+UTF-8 (tdd)** - `5adcb0cc` (test, RED) + `14cedd97` (feat, GREEN) — no refactor needed

## Files Created/Modified

- `setup.py` — implib path derived from get_ext_fullpath dirname (win32 branch only)
- `import/pysam.c` — Windows dispatch branch + compiler gate (template)
- `samtools/samtools.pysam.c`, `bcftools/bcftools.pysam.c` — bare _WIN32 guards upgraded to compiler gate
- `samtools/coverage.c`, `samtools/coverage.c.pysam.c` — histogram heap form under _MSC_VER
- `htslib/hts_internal.h` — array-parameter qualifier dropped
- `pysam/libcutils.pyx` — _collect binary read + UTF-8 replace decode
- `tests/PortabilityRegression_test.py` — TestDispatchOutputEncoding (permanent)

## Decisions Made

- Compiler gate implemented as a feature macro (`<tool>_DISPATCH_GCC_BUILTIN_JMP`) defined by one `#if defined(_WIN32) && !defined(_MSC_VER)` per file: the gate is needed at three sites (jmpbuf type, dispatch body, exit body) but the plan's grep gate requires exactly one occurrence of the condition string per file.
- Lockstep proven mechanically: sed-substituted template diffs clean against both twins (import.py's only transform is the @pysam@ substitution, confirmed by reading devtools/import.py:132-134).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Cython rejected keyword call to cdef helper**
- **Found during:** Task 3 (GREEN implementation)
- **Issue:** `decode_bytes(inf.read(), errors='replace')` failed cythonization — "C function call is missing argument 'encoding'" (cdef helpers in this file are called positionally by convention)
- **Fix:** `decode_bytes(inf.read(), None, 'replace')` (None selects TEXT_ENCODING = utf-8)
- **Files modified:** pysam/libcutils.pyx
- **Verification:** rebuild + targeted test green
- **Committed in:** 14cedd97

### Documented criterion deviations (plan-internal conflicts)

**2. VLA grep criterion (== 0) unsatisfiable together with the #else-verbatim requirement**
- **Found during:** Task 2 acceptance sweep
- **Issue:** The plan's action text and prohibitions require the original stack-array declaration kept verbatim in the #else arm (zero-regression red line, CLAUDE.md highest-priority constraint), but the verify's `grep -c "double hist_data\[hist_size\]" == 0` pattern matches that verbatim #else line. The two cannot both hold; removing the VLA everywhere would change POSIX-compiled bytes, which the plan's own must_haves prohibit (only the hts_internal qualifier drop is an authorized exception).
- **Resolution:** Kept the guarded form — VLA verbatim in #else, malloc+free under `#if defined(_MSC_VER)` in both files. The criterion's intent (MSVC never sees a VLA) is proven by guard context: the declaration sits directly inside the #else arm at coverage.c:233-238. Criterion recorded as FAIL-as-written with rationale rather than silently satisfied by breaking the red line.
- **Committed in:** d3e77161

**3. "regenerated pysam/libcutils.c committed" conflicts with repo .gitignore policy**
- **Found during:** Task 3 acceptance sweep
- **Issue:** The plan requires committing the regenerated Cython C, but `.gitignore:35` excludes `pysam/libc*.c` — no generated libc*.c is version-controlled in this fork (git ls-files confirms 0 tracked).
- **Resolution:** The .c was regenerated (mtime newer than .pyx; behavior change proves the extension carries the fix) but stays untracked per repo policy — force-adding a gitignored 25k-line generated file would be a repo-policy change, not this plan's call. Fix is carried by the tracked .pyx.
- **Committed in:** 14cedd97 (pyx only)

---

**Total deviations:** 1 auto-fixed (Rule 1 bug), 2 documented criterion conflicts (both plan-internal, zero-regression/red-line precedence applied)
**Impact on plan:** No scope creep. All four carried constraints (D-17, D-20a, D-20b, WR-01) are closed with committed evidence; the two conflicts are checkable-text mismatches, not missing work.

## TDD Gate Compliance

Task 3 (`tdd="true"`): RED commit `test(03-01):` 5adcb0cc precedes GREEN commit `feat(03-01):` 14cedd97. RED evidence machine-validated (`gsd_run check tdd-red-evidence` → RED_EVIDENCE_OK, JUnit XML report, target test `TestDispatchOutputEncoding#test_cjk_header_comment_roundtrip` failed on the planned assertion). Semantic assessment: failed for the intended reason — under the cp936-default interpreter _collect's text-mode read hit its decode-error fallback and returned raw bytes (locale-dependent capture path). No REFACTOR commit (implementation minimal). Evidence record kept at `.planning/tmp/tdd-red-03-01-task3.json` (untracked).

## Issues Encountered

- The WR-01 RED manifested as a bytes return (the decode-error fallback firing) rather than the plan's predicted mojibake str: the test's CJK string is not cp936-decodable, so the text-mode read raised and the fallback returned bytes. Same defect class (locale-dependent capture decode); the plan-mandated miniconda one-shot probe additionally recorded the pure-mojibake facet (`roundtrip equal: False`, `raised: nothing` under cp936).
- Plan-level TDD gate not active (`workflow.tdd_mode: false`, init JSON `tdd_mode: false`); per-task TDD followed per the task's tdd="true" attribute, including RED evidence classification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- D-17/D-20/C99/WR-01 all closed — plans 03-02 (vendoring) and 03-03 (MSVC build branch) can proceed; 03-03's first MSVC compile will exercise the plain-setjmp arm and the _MSC_VER heap form added here.
- Inplace + out-of-tree UCRT64 builds green; smoke green; full portability file 12/12 green. Fork CI ubuntu/macos verification rides the push (phase-level check in plan 03-05).

---
*Phase: 03-msvc*
*Completed: 2026-10-12*

## Self-Check: PASSED

All 9 modified key files exist on disk; all 4 task commits (08e2526a, d3e77161, 5adcb0cc, 14cedd97) are ancestors of HEAD; ledger recount confirms 4 commits between plan_head_before and HEAD, matching frontmatter actuals.
