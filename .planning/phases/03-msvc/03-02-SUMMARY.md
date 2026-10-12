---
phase: 03-msvc
plan: "02"
subsystem: infra
tags: [vendoring, zlib, bzip2, xz, liblzma, musl, posix-regex, msvc, cl-exe, sha256, supply-chain, compile-probe, provenance]

requires:
  - phase: 03-msvc/01
    provides: MSVC compiler-gate idiom + C99 site closures (03-02's compat edits reuse the same drop-the-qualifier precedent as hts_internal.h)
provides:
  - vendor/zlib 1.3.2, vendor/bzip2 1.0.8, vendor/xz 5.8.4 (liblzma) — MSVC-closable source trees, hygiene-pruned, licenses preserved
  - vendor/regex — musl 1.2.6 POSIX regex subset (regcomp/regexec/regerror/tre-mem + tre.h + adapted regex.h + locale_impl.h shim), MIT
  - vendor/HASHES.txt + vendor/README.md — per-source SHA-256 provenance with cross-check status and offline re-verification command
  - devtools/msvc_compile_probe.py — reusable cl.exe compile-only probe (setuptools auto-locate, /W3 /we4013, verbatim cl output, PASS/FAIL, codepage-safe)
  - Proven MSVC include/define sets for every tree, recorded in vendor/README.md for plan 03-03 copy-verbatim reuse
affects: [03-03 MSVC build branch, 03-04 MSVC shim layer, 03-05 suite/close, Phase 4 CI/wheel (self-contained closure)]

actuals:
  tokens: 725270   # chars/4 over the realized diff (2901081 diff chars / 4) — dominated by vendored upstream sources (219 files, 75971 inserted lines); the estimate (28000) was sized for authored files only
  tasks: 3
  commits: 3       # measured: git rev-list --count 49a17096..HEAD

tech-stack:
  added:
    - "zlib 1.3.2 (vendored from zlib.net)"
    - "bzip2 1.0.8 (vendored from sourceware.org)"
    - "xz/liblzma 5.8.4 (vendored from tukaani.org official release)"
    - "musl 1.2.6 regex subset (vendored from musl.libc.org)"
  patterns:
    - "vendor-tree provenance contract: HASHES.txt sha256-per-tarball + README cross-check-status column; uncross-checkable sources explicitly flagged, never silently trusted (T-03-04)"
    - "cl-compile probe discipline: /W3 /we4013 so implicit declarations are errors, fd-level capture of cl output, codepage-safe (GBK-console) reporting"

key-files:
  created:
    - vendor/zlib/**
    - vendor/bzip2/**
    - vendor/xz/**
    - vendor/regex/**
    - vendor/HASHES.txt
    - vendor/README.md
    - vendor/.gitattributes
    - devtools/msvc_compile_probe.py
  modified: []

key-decisions:
  - "xz 5.8.4 consumes a no-config route: -DHAVE_STDINT_H=1 -DHAVE_INTTYPES_H=1 -DHAVE_STDBOOL_H=1 (its windows/ dir no longer ships a pre-provided config.h — upstream moved MSVC builds to CMake; documented in vendor/README.md)"
  - "musl regex internal-header fan-out neutralized by 2 glue adaptations (regex.h features.h/alltypes.h -> stddef.h + typedef long regoff_t; locale_impl.h shim defining LCTRANS_CUR as identity) instead of vendoring musl runtime internals — 0 real internal headers vendored, TRE fallback not triggered"
  - "Two genuine-MSVC-gap compat edits recorded in-tree: regexec.c [restrict] array-param qualifier dropped (same class as hts_internal.h [static], 03-01 precedent); tre.h ALIGN (long)->(size_t) because long is 32-bit on win64 (C4311 pointer truncation)"
  - "regex define set: hidden= (musl visibility macro) + RE_DUP_MAX=255 + CHARCLASS_NAME_MAX=14 (musl limits.h extensions; cross-checked all 112 musl limits macros against the TUs — no others missing)"

patterns-established:
  - "Vendoring supply-chain rule operationalized: official-channel tarball + publisher-checksum cross-check where published (zlib.net index, sourceware sha512.sum, GitHub release asset digest) + explicit not-cross-checkable flag (musl)"
  - "Compile-probe-early: every vendored tree proven cl-compilable before the build-integration plan touches it; probe command lines live in vendor/README.md"

requirements-completed: [BUILD-02]  # copied verbatim from PLAN frontmatter (shared ID — ready-ids gate holds it until all phase-03 plans finish)

coverage:
  - id: D1
    description: "vendor/{zlib,bzip2,xz} committed from official releases with SHA-256 provenance cross-checked against publisher values, licenses preserved, zero archives/binaries tracked"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "test -f gates over zlib/inflate.c zlib/zconf.h bzip2/bzlib.c bzip2/LICENSE xz/.../common.c + git ls-files archive scan == 0"
        status: pass
      - kind: manual_procedural
        ref: "sha256 cross-checks at download time: zlib.net index == bb329a0a...119d16; sourceware sha512.sum line == computed SHA-512 for bzip2 1.0.8; GitHub v5.8.4 asset digest == 0014c788...591d9"
        status: pass
    human_judgment: false
  - id: D2
    description: "vendor/regex: musl 1.2.6 POSIX regex subset with MIT COPYRIGHT, regerror/regfree coverage, provenance recorded (uncross-checkable status flagged per T-03-04)"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "regcomp.c/regexec.c/regerror.c/tre-mem.c/tre.h byte-identical vs tarball (cmp); regfree at regcomp.c:2907, regerror at regerror.c:30; HASHES musl row present"
        status: pass
      - kind: unit
        ref: "all four TUs PASS under cl probe with the recorded define set (4 passed, 0 failed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "devtools/msvc_compile_probe.py + MSVC-cleanliness proof: four-tree acceptance run exits 0; failure paths proven (broken.c FAIL exit 1, implicit-decl C4013 FAIL exit 1, clean.c PASS exit 0)"
    requirement: BUILD-02
    verification:
      - kind: integration
        ref: "D:/miniconda3/python.exe devtools/msvc_compile_probe.py zlib/inflate.c bzip2/decompress.c regex/regcomp.c xz/.../common.c + recorded includes/defines -> 4 PASS, exit 0 (re-run in final sweep)"
        status: pass
      - kind: unit
        ref: "failure-path matrix: genuine error -> FAIL exit 1; /we4013 promotes implicit declaration (C4013) to error -> FAIL exit 1; clean TU -> PASS exit 0"
        status: pass
      - kind: unit
        ref: "grep -c 'PASS|FAIL' devtools/msvc_compile_probe.py == 3 (reporting strings present)"
        status: pass
    human_judgment: false

duration: 26 min
completed: 2026-10-12
status: complete
plan_head_before: 49a170969429e8df920201d3490133d80a6b9ff2
plan_head_after: 258e6b54019670424afae62ef4e4af72229a1c4e
---

# Phase 03 Plan 02: Vendor trees (zlib/bzip2/xz + musl regex), SHA-256 manifest, cl-compile probe proof Summary

**Four MSVC-closable dependency trees vendored from official releases with publisher-cross-checked SHA-256 provenance (zlib 1.3.2, bzip2 1.0.8, xz 5.8.4, musl 1.2.6 regex subset), each proven cl.exe-compilable via a reusable /we4013-disciplined compile probe before the build-integration plan touches them.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-10-12T12:28:40Z
- **Completed:** 2026-10-12T12:55:17Z
- **Tasks:** 3/3
- **Files:** 219 created (vendor/ 218 + devtools/msvc_compile_probe.py)

## Accomplishments

- BUILD-02's MSVC dependency closure is in-tree: zlib (BGZF hard dep), bzip2 + xz/liblzma (CRAM codec parity with the 1027-green UCRT64 baseline, research Q1/A2), and a POSIX regex (hts_expr.c:37 / sam.c:39 unconditional consumers, research Q2/A3). Every tree hygiene-pruned to static-compile sources with upstream license files preserved; no tarballs, no binaries, no build products tracked.
- Provenance is re-verifiable offline: vendor/HASHES.txt carries one sha256 line per source tarball; vendor/README.md records origin URL + license path + cross-check status per tree — zlib cross-checked against zlib.net's index page, bzip2 cross-checked on SHA-512 against sourceware's sha512.sum, xz cross-checked against the official release asset digest, musl explicitly flagged "not published upstream" (only a GPG signature exists) per T-03-04.
- All four trees proven MSVC-clean under cl 14.50 (VS 2026 BuildTools, setuptools auto-located from plain Git Bash): the plan's four-TU acceptance probe exits 0, plus the full 4-TU regex set and xz's stream_decoder.c decoder TU. The exact working command lines are recorded in vendor/README.md for plan 03-03 to copy verbatim.
- devtools/msvc_compile_probe.py: compile-only cl.exe checker with the /we4013 discipline (implicit declarations are errors, not silent link-time bombs), fd-level verbatim capture of cl diagnostics, codepage-safe reporting (GBK consoles), and proven failure-path exit codes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Vendor zlib + bzip2 + xz with recorded provenance** - `d7e3c3ed` (feat) — 210 files
2. **Task 2: Vendor musl 1.2.6 POSIX regex subset** - `40dba8de` (feat) — 10 files
3. **Task 3: cl compile probe tool + MSVC-cleanliness proof** - `258e6b54` (feat) — probe + 2 recorded compat edits + README probe lines

## Files Created/Modified

- `vendor/zlib/` — 15 core TUs + 11 headers + LICENSE + README (1.3.2)
- `vendor/bzip2/` — 7 library TUs + bzlib.h + bzlib_private.h + LICENSE (1.0.8)
- `vendor/xz/` — src/liblzma/** (84 .c + 64 .h, .S asm excluded) + 9 src/common support files + windows/ docs + COPYING family (5.8.4)
- `vendor/regex/` — regcomp/regexec/regerror/tre-mem + tre.h (1 compat edit) + adapted regex.h + locale_impl.h shim + COPYRIGHT (musl 1.2.6)
- `vendor/HASHES.txt`, `vendor/README.md`, `vendor/.gitattributes` — provenance manifest + LF/linguist rules
- `devtools/msvc_compile_probe.py` — reusable MSVC compile probe

## Decisions Made

- xz MSVC configuration = no-config route with three defines (HAVE_STDINT_H/HAVE_INTTYPES_H/HAVE_STDBOOL_H); 5.8.4's windows/ is documentation-only (upstream moved MSVC builds to CMake), so there is no pre-provided config.h to consume — the define set is the recorded configuration base for 03-03.
- musl regex: 2 glue adaptations (regex.h header-machinery replacement; locale_impl.h identity shim) instead of vendoring musl internals — the real locale_impl.h chains into pthread TLS runtime, unbuildable outside musl; musl's own weak-alias default makes LCTRANS_CUR the identity function. Fan-out stayed at 0 real internal headers, so the plan's TRE-fallback trigger (~3+ headers) never fired.
- The two in-tree compat edits (regexec.c `[restrict]` drop; tre.h ALIGN `(long)`→`(size_t)`) are genuine MSVC/LLP64 compiler gaps, recorded with in-code comments and README entries, in the same pattern as 03-01's hts_internal.h qualifier drop.
- bzip2's library recorded as 7 TUs (upstream 1.0.8 fact); the plan's "eight" counted the CLI bzip2.c which is not library code and stays pruned.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Probe missed setuptools 78's relocated CompileError class**
- **Found during:** Task 3 (first probe run)
- **Issue:** setuptools 78's MSVC compiler raises `setuptools._distutils.compilers.C.errors.CompileError`, a different class from `setuptools._distutils.errors.CompileError`; the except-clause missed it, the fd-captured cl diagnostics were lost, and the traceback escaped
- **Fix:** `_import_distutils()` now collects every CompileError/DistutilsPlatformError variant present across both layouts and the except-clauses use the tuple
- **Files modified:** devtools/msvc_compile_probe.py
- **Verification:** all four regex TUs report clean PASS/FAIL with verbatim cl output; failure-path matrix green
- **Committed in:** 258e6b54

**2. [Rule 1 - Bug] Probe report crashed on GBK consoles**
- **Found during:** Task 3 (regcomp.c FAIL output)
- **Issue:** cl emits codepage-localized diagnostics (cp936 here); decoding as UTF-8 produced U+FFFD that Python's gbk stdout refused to print (UnicodeEncodeError mid-report)
- **Fix:** layered decode (utf-8 -> mbcs -> utf-8/replace) + `reconfigure(errors="replace")` on stdout/stderr
- **Files modified:** devtools/msvc_compile_probe.py
- **Verification:** full GBK diagnostic text prints verbatim on this cp936 machine
- **Committed in:** 258e6b54

### Documented plan-text vs upstream-reality divergences (no missing work)

**3. zlib checksum publication point**: plan said the SHA-256 is "published in the zlib-announce post"; the 1.3.2 announce post links out without any hash. The value IS published on zlib.net's index page — cross-check performed against that official publisher page (exact match).

**4. xz windows/ pre-provided config**: plan expected "its pre-provided config for MSVC builds" in windows/; xz 5.8.4's windows/ ships install docs only. The MSVC path consumes the recorded no-config define set instead (README documents this and points at windows/INSTALL-MSVC.txt).

**5. bzip2 "eight library .c files"**: the 1.0.8 library is 7 TUs; the eighth .c in the plan's count is the CLI tool (pruned as planned). Documented in vendor/README.md.

**6. musl internal-header fan-out**: plan's fallback trigger ("exceeds ~3 extra headers → switch to TRE") was written for real internal headers; the actual fan-out was 2 glue includes neutralized by a 6-line shim + a 3-line header adaptation, 0 real headers vendored — TRE (LGPL) not triggered, rationale recorded in README.

---

**Total deviations:** 2 auto-fixed (Rule 1 bugs, both in the probe tool itself), 4 documented plan-text divergences (upstream-reality checks, no scope change)
**Impact on plan:** No scope creep. All must_haves truths hold; UCRT64 path untouched (vendor/ referenced only by the future MSVC module graph; zero shared-file edits outside vendor/ + devtools/).

## Issues Encountered

None beyond the deviations above — every gate passed on the consolidated final sweep (file presence, archive scan, hash-line counts, README row counts, probe exit 0).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 03-03 can wire the four vendor trees into the MSVC module graph: include dirs + define sets + the exact probe command lines are recorded in vendor/README.md; the trees are proven cl-clean so the first integration failure class is wiring, not sources.
- The known-benign warnings (regex C4005 NDEBUG, tre-mem.c C4267) are documented in README — 03-03 should not chase them.
- musl regex behavioral validation (filter tests) lands with 03-05's suite run; TRE remains the documented fallback if filter tests disagree.

## Self-Check: PASSED

All 8 key created files/dirs exist on disk (vendor trees + manifest files + probe); all 3 task commits (d7e3c3ed, 40dba8de, 258e6b54) are ancestors of HEAD; ledger recount confirms 3 commits between plan_head_before (49a17096) and HEAD, matching frontmatter actuals.

---
*Phase: 03-msvc*
*Completed: 2026-10-12*
