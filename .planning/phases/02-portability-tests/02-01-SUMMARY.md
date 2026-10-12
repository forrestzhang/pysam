---
phase: 02-portability-tests
plan: 01
subsystem: infra
tags: [cython, libcport, fd-io, o-binary, mingw-w64, ucrt64, posix-portability, off_t]

requires:
  - phase: 01-mingw-w64
    provides: UCRT64 editable build + devtools/smoke_test.py gate + os.devnull dispatch fix
provides:
  - pysam/libcport.pxd — single-point fd-I/O platform mapping (psam_dup/psam_open2/psam_open3/psam_read/psam_close, PSAM_O_*, PSAM_STDOUT_FILENO, 64-bit psam_off_t)
  - All four posix.* cimport sites eliminated (grep-clean across pysam/*.pyx and pysam/*.pxd)
  - Both live PORT-02 raw-fd text-mode corruptions closed with byte-level RED→GREEN proof
  - 02-PORT01-CHECKLIST.md — D2-03 acceptance artifact doubling as the Phase 3 MSVC inventory
affects: [02-02 audits, 02-03 test infra, 02-04 suite green, phase-3-msvc]

actuals:
  tokens: 4860        # chars/4 over the realized diff (19441 chars across 6 files)
  tasks: 3
  commits: 3          # MEASURED: git rev-list --count c3541873..HEAD
plan_head_before: c35418735dc015e3c6e19736fcc1195037d3b945
plan_head_after: 956421b086f3f0f373f84096a47b697c15ee1e31

tech-stack:
  added: []
  patterns:
    - "C-preprocessor platform switch via `cdef extern from *` verbatim C (no deprecated Cython compile-time conditionals; fixed-arity macros only)"
    - "Single choke point for fd-I/O platform mapping: consumers change cimport lines only (D2-04)"

key-files:
  created:
    - pysam/libcport.pxd
    - .planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md
  modified:
    - pysam/libcutils.pyx
    - pysam/libctabix.pyx
    - pysam/libchtslib.pyx
    - pysam/libchtslib.pxd

key-decisions:
  - "libcport uses `cdef extern from *` + #ifdef C-preprocessor switch (Cython 3.3.0 has no usable compile-time conditional; RESEARCH Pattern 1 verified on this toolchain)"
  - "save_stdout byte proof runs on flagstat, not view: samtools view writes via htslib '-' → fd 1 on every platform (upstream Linux included), so the save_stdout file is always empty for view; flagstat is the command whose output actually flows through the libcutils.pyx:359 redirect fd + fdopen FILE* (pysam's own testSaveStdout uses it)"
  - "Write-side corruption is masked in-process by CPython's startup `_fmode=_O_BINARY` (fdopen \"w\" FILE* inherits it); the fd-layer `_O_BINARY` in psam_open3 makes the fd binary-by-flag instead of binary-by-ambient-default (standalone-C probe proves the CRT default corrupts: 14 bytes hello\\r\\nworld\\r\\n)"
  - "Canonical rebuild requires both Phase 1 env vars: HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl and MAKE=mingw32-make (devtools/msys2-bootstrap.sh is the source of truth)"

patterns-established:
  - "libcport consumer rewiring: alias cimports (`psam_open2 as c_open2`) keep consumer diffs to cimport lines + arity-name call sites"
  - "Byte-level RED→GREEN probes through public API (tabix_compress round-trip; flagstat save_stdout) as PORT-02 evidence"

requirements-completed: [PORT-01, PORT-02]

coverage:
  - id: D1
    description: "Centralized libcport fd-I/O platform mapping; all four posix.* cimport sites eliminated (PORT-01, D2-01/D2-04)"
    requirement: PORT-01
    verification:
      - kind: other
        ref: "grep -rn 'from posix' pysam --include=*.pyx --include=*.pxd → rc=1 (zero matches)"
        status: pass
      - kind: other
        ref: "_venv/bin/python.exe -m pip install -e . --no-build-isolation (UCRT64, canonical env) → Successfully installed"
        status: pass
      - kind: other
        ref: "_venv/bin/python.exe devtools/smoke_test.py → 'smoke OK'"
        status: pass
    human_judgment: false
  - id: D2
    description: "save_stdout dispatch redirect binary-safe at the fd layer (PORT-02 write side): psam_open3 forces _O_BINARY and masks pmode"
    requirement: PORT-02
    verification:
      - kind: other
        ref: "flagstat save_stdout byte check: 460 bytes, no CRLF pair (public API; passes pre- and post-fix in-process because CPython _fmode masks the FILE layer — mechanism documented)"
        status: pass
      - kind: other
        ref: "grep -c 'psam_open3' pysam/libcutils.pyx → 1"
        status: pass
    human_judgment: false
  - id: D3
    description: "tabix_compress fd copy loop binary-safe end-to-end (PORT-02 read side — the live corruption)"
    requirement: PORT-02
    verification:
      - kind: other
        ref: "public-API round-trip: 203-byte payload with 50 CRLF pairs → RED 153 bytes (text-mode loss) → GREEN 203 bytes byte-identical"
        status: pass
    human_judgment: false
  - id: D4
    description: "D2-03 grep-clean checklist committed, consumable as the Phase 3 MSVC inventory"
    requirement: PORT-01
    verification:
      - kind: other
        ref: "test -f 02-PORT01-CHECKLIST.md && grep -c 'MSVC status' → 3; grep -c 'D2-' → 11; every row carries a runnable evidence command"
        status: pass
    human_judgment: false
  - id: D5
    description: "Zero POSIX regression: libcport POSIX branch is pure identity aliases, Linux/macOS behavior unchanged"
    verification:
      - kind: other
        ref: "source inspection: #else branch of pysam/libcport.pxd maps every name to the identical libc symbol; fork CI formal closure assigned to Plan 02-04 by the plan itself"
        status: pass
    human_judgment: true
    rationale: "Cross-platform behavioral proof requires the fork CI ubuntu/macos run on the pushed commits; this plan defers that formal closure to Plan 02-04 by design (local executor cannot run Linux CI)."

duration: 27 min
completed: 2026-10-12
status: complete
---

# Phase 2 Plan 1: libcport fd-I/O Platform Mapping Summary

**pysam/libcport.pxd centralized C-preprocessor fd-I/O mapping (Windows _dup/_open+_O_BINARY/pmode-mask, POSIX identity aliases) rewiring all four posix.* cimport sites, closing both live raw-fd text-mode corruptions with byte-level RED→GREEN proof, plus the D2-03 MSVC inventory**

## Performance

- **Duration:** 27 min
- **Started:** 2026-10-12T04:34:11Z
- **Completed:** 2026-10-12T05:00:48Z
- **Tasks:** 3
- **Files modified:** 6 (2 created, 4 rewired)

## Accomplishments
- `pysam/libcport.pxd`: one `cdef extern from *` block does the platform switch in the C preprocessor — Windows maps to CRT underscore variants with `_O_BINARY` forced and pmode masked to `_S_IREAD|_S_IWRITE`; POSIX branch is pure identity aliases (zero-regression); fixed-arity open forms only (no variadic macros — MSVC `/Zc:preprocessor` safe for Phase 3); `psam_off_t` is `long long` on Windows (closes the 32-bit `off_t` ABI gap against htslib's `_FILE_OFFSET_BITS 64` build), identity `off_t` on POSIX.
- All four posix cimport sites eliminated: `libcutils.pyx:25-30`, `libctabix.pyx:65-66`, `libchtslib.pyx:10`, `libchtslib.pxd:7` — recursive grep over `pysam/*.pyx`/`*.pxd` is clean (rc=1). SEEK_SET/CUR/END moved to `libc.stdio` (ISO-C).
- Live PORT-02 read-side corruption fixed with proof: `tabix_compress` 203-byte payload with 50 CRLF pairs read back **153 bytes** before (raw fd text mode), **203 bytes byte-identical** after.
- PORT-02 write side closed structurally at the fd layer (`psam_open3`); full causal chain documented (see Decisions).
- D2-03 checklist (`.planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md`): every POSIX-only symbol/path with disposition + runnable grep evidence; deferred rows cite D2-02/D2-03/D2-11/v2/W10/W4; MSVC status column pre-filled for Phase 3 (research A3: "mapped, unverified under MSVC").
- Post-change functional probes on the fresh build: smoke OK; tell/seek roundtrip through the new `psam_off_t`-typed `hseek`/`htell` signatures (24/24 records); flagstat save_stdout 460 bytes CRLF-free.

## Task Commits

1. **Task 1: Create pysam/libcport.pxd and rewire libcutils.pyx** - `dc40dd29` (feat)
2. **Task 2: Rewire libctabix.pyx, libchtslib.pyx, libchtslib.pxd** - `0b252e65` (feat; includes the libcport `nogil` Rule 1 fix)
3. **Task 3: D2-03 grep-clean checklist / MSVC inventory** - `956421b0` (docs)

## Files Created/Modified
- `pysam/libcport.pxd` - centralized fd-I/O platform mapping (D2-01/D2-04)
- `pysam/libcutils.pyx` - cimports rewired; save_stdout redirect + both devnull opens route through psam_open3/psam_open2
- `pysam/libctabix.pyx` - cimports rewired; tabix_compress copy loop now binary-safe
- `pysam/libchtslib.pyx` - dup → psam_dup alias
- `pysam/libchtslib.pxd` - off_t → 64-bit psam_off_t alias (hseek/htell signatures)
- `.planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md` - D2-03 acceptance artifact / Phase 3 MSVC inventory

## Decisions Made
- **Byte-proof command substitution (Rule 1):** the plan's save_stdout check used `samtools view`, but view writes through htslib's `"-"` → fd 1 on every platform (upstream Linux included) — its save_stdout file is always empty. The proof now runs on `flagstat`, the command whose output actually flows through the redirect fd + `fdopen` FILE* (what pysam's own `testSaveStdout` exercises). The view variant was also run and recorded: 0 bytes, no CRLF (matches POSIX behavior; the must_haves truth "no CRLF pair" holds).
- **Write-side mechanism pinned empirically:** raw `_open(O_RDONLY)` fds are TEXT mode even inside the python process (msvcrt setmode readback: 0x4000; os.open read 153/203 bytes) — `_fmode` only governs FILE* mode strings, and CPython sets `_fmode=_O_BINARY` at startup, which is why the flagstat write path was already clean in-process. A standalone-C probe of the exact :359 chain (default CRT) writes `hello\r\nworld\r\n` (14 bytes) — the corruption the `_O_BINARY` forcing now prevents at the fd layer, independent of ambient defaults.
- **Canonical rebuild env:** `HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl` **and** `MAKE=mingw32-make` are both required (Phase 1's msys2-bootstrap.sh contract); the plan's environment-contract shorthand omitted them.
- **Aliased cimports** (`psam_open2 as c_open2` etc.) per RESEARCH Code Examples, keeping consumer diffs minimal and satisfying the plan's `grep -c psam_open3 == 1` gate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] save_stdout byte-proof command unpassable as written**
- **Found during:** Task 1 (RED capture)
- **Issue:** The plan's verify used `pysam.samtools.view('-h', <sam>, save_stdout=<file>)` expecting nonzero bytes; view routes output through htslib `"-"` → fd 1 (console) on every platform, so the redirect file is always empty — the check cannot pass on Linux either.
- **Fix:** Byte proof runs on `pysam.samtools.flagstat(<sam>, save_stdout=<file>)` (the dispatch-redirect command); view variant still run and recorded (0 bytes, no CRLF).
- **Files modified:** none (verification substitution only; probe recorded in this SUMMARY)
- **Verification:** flagstat save_stdout = 460 bytes, `b"\r\n" not in data`, exit 0.
- **Committed in:** n/a (evidence recorded here and in the checklist)

**2. [Rule 1 - Bug] libcport function declarations missing `nogil`**
- **Found during:** Task 2 (first rebuild)
- **Issue:** `psam_read` is called inside `with nogil:` in the tabix copy loop; Cython rejected the call ("Calling gil-requiring function not allowed without gil") because the declarations lacked `nogil` (Cython's own posix.unistd declarations carry it).
- **Fix:** all five libcport function declarations marked `nogil`.
- **Files modified:** pysam/libcport.pxd
- **Verification:** rebuild green, smoke OK, tabix round-trip byte-clean.
- **Committed in:** 0b252e65

**3. [Rule 3 - Blocking] Rebuild failed without Phase 1 canonical env vars**
- **Found during:** Task 1 (first rebuild)
- **Issue:** `pip install -e .` failed twice — first `configure: error: libcurl library not found` (missing `HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl`), then `FileNotFoundError` spawning `make` (UCRT64 ships only `mingw32-make`, missing `MAKE=mingw32-make`).
- **Fix:** rebuild with both exports per devtools/msys2-bootstrap.sh (the Phase 1 D-14 contract).
- **Files modified:** none (environment invocation)
- **Verification:** "Successfully installed pysam-0.24.1".
- **Committed in:** n/a

**4. [Rule 1 - Documentation] Plan's Task 2 acceptance arithmetic slip**
- **Found during:** Task 2 verify
- **Issue:** Plan said the round-trip prints "in: 303 out: 303", but the verify snippet's payload `(b'AB\r\n' * 50) + b'END'` is 203 bytes.
- **Fix:** criterion satisfied with the snippet's real output `in: 203 out: 203` (the substantive gate — `back == payload` — passes).
- **Files modified:** none
- **Committed in:** n/a

---

**Total deviations:** 4 auto-fixed (2 Rule 1 bugs, 1 Rule 3 blocker, 1 Rule 1 doc correction)
**Impact on plan:** No scope change; the implementation itself matched the plan exactly. Deviations 1/4 are verification-command corrections with the plan's intent preserved; 2/3 were build-mechanics fixes required to execute at all.

## Issues Encountered
- The plan's must_haves truth #2 (view save_stdout CRLF-free) is satisfied but vacuously for `view` (empty file, identical on POSIX); the substantive write-side proof is the flagstat variant plus the standalone-C CRT probe — full causal chain in Decisions and the checklist.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for Plans 02-02 (PORT-02 audit closure: call-site checklist + permanent regression tests — this plan's byte probes are their templates), 02-03 (test infra), 02-04 (suite green + fork-CI zero-regression closure, which formally closes this plan's verification item 4).
- The fork CI run on these commits is the outstanding formal zero-regression evidence (assigned to Plan 02-04 by the plan itself; commits are local on `win` until push).
- Phase 3 can consume `.planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md` directly as its MSVC porting inventory.

## Self-Check: PASSED
- pysam/libcport.pxd — FOUND (dc40dd29 ancestor of HEAD)
- pysam/libcutils.pyx, pysam/libctabix.pyx, pysam/libchtslib.pyx, pysam/libchtslib.pxd — FOUND (0b252e65)
- .planning/phases/02-portability-tests/02-PORT01-CHECKLIST.md — FOUND (956421b0)
- commits dc40dd29, 0b252e65, 956421b0 all ancestors of HEAD — VERIFIED
- commits measured from ledger: 3 (git rev-list --count c3541873..HEAD)

---
*Phase: 02-portability-tests · Plan: 01*
*Completed: 2026-10-12*
