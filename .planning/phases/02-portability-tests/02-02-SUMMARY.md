---
phase: 02-portability-tests
plan: 02
subsystem: portability
tags: [windows, portability, cjk-paths, wide-char, wopen, o-binary, binary-mode, llp64, static-assert, htslib, regression-tests, port-02, port-03, port-04]

requires:
  - phase: 02-portability-tests plan 01
    provides: pysam/libcport.pxd centralized fd-I/O mapping (psam_open2/3, psam_off_t) and the canonical UCRT64 rebuild contract
provides:
  - PORT-04 fix at the C open layer — htslib hopen_fd UTF-8→UTF-16 _wopen shim, libcport psam_wopen, hts_idx_check_local wide stat probes (all _WIN32-guarded, two-call MultiByteToWideChar, no MAX_PATH)
  - tests/PortabilityRegression_test.py — permanent suite: TestCJKPathCanary (D2-10) + TestBinaryMode (D2-08), 11 tests
  - PORT-03 closure — EXPECTED_SIZES per-platform table (no skips) + _Static_assert pyximport module proving hts_pos_t/psam_off_t == 8 at C compile time
  - 02-PORT02-AUDIT.md — D2-08 one-time binary-mode call-site checklist, zero unguarded sites
affects: [02-03 test infra, 02-04 suite green + fork-CI closure, phase-3-msvc]

actuals:
  tokens: 8040       # chars/4 over the realized diff (32159 chars, 8 files)
  tasks: 3
  commits: 3         # MEASURED: git rev-list --count bf3653bc..HEAD
plan_head_before: bf3653bc972b6f882dcb7e08390a3de6f1dedffc
plan_head_after: 100389f1

tech-stack:
  added: []
  patterns:
    - "Wide-char open shim: two-call MultiByteToWideChar (length query, then convert) into a malloc'd buffer + _wopen/_wstat — never a fixed MAX_PATH buffer; POSIX branch kept verbatim behind #else"
    - "Byte-level canary-first RED→GREEN discipline through public API surfaces to catch audit gaps (three separate narrow-open layers were found this way)"

key-files:
  created:
    - tests/PortabilityRegression_test.py
    - tests/_compile_sizes.pyx
    - tests/_compile_sizes.pyxbld
    - .planning/phases/02-portability-tests/02-PORT02-AUDIT.md
  modified:
    - htslib/hfile.c
    - htslib/hts.c
    - pysam/libcport.pxd
    - tests/compile_test.py

key-decisions:
  - "PORT-04 required widening THREE narrow-open layers, not one: hopen_fd (htslib), psam_open2/3 (libcport — tabix_compress/save_stdout paths bypass htslib), and hts_idx_check_local's stat probes (auto index discovery). The canary found each in sequence; all use the same two-call MultiByteToWideChar pattern at the single-point-of-mapping layers."
  - "htslib C-source rebuild discipline: `pip install -e .` does NOT recompile htslib objects when only htslib .c files change (prebuild_libchtslib skips when libhts.a exists and extensions don't relink on extra_object mtime) — `setup.py build_ext --inplace --force` is the working rebuild for htslib-touching edits."
  - "pyximport in this environment needs (a) the repo root appended to sys.path (PEP 660 editable installs import pysam through a MetaPathFinder invisible to Cython's file-based .pxd search) and (b) an absolute build_dir (ntpath.expanduser ignores HOME; with USERPROFILE absent under an MSYS2 login shell the default '~/.pyxbld' is relative, and a relative .pyd path cannot be loaded on Windows)."
  - "nt struct sizes equal the posix literals for all seven TestBinaryCompatibility objects — explained by struct composition (PyObject header + pointers + int/int64_t/bint; no C `long` field anywhere in the hierarchy), recorded beside the EXPECTED_SIZES table."

patterns-established:
  - "TestBinaryMode assertions are platform-neutral by construction (no-CRLF, byte-identity, BGZF magic) so they double as POSIX no-regression sentinels"
  - "Wide-char conversion helper shape (wlen query → malloc → convert → use → free on all paths → errno mapping) — copy for any future narrow-API call site"

requirements-completed: [PORT-02, PORT-03, PORT-04]

coverage:
  - id: D1
    description: "PORT-04 closed at the C open layer: CJK-path read+write, .bai/.csi/.tbi build+auto-discovery, tabix fetch, VariantFile roundtrip, dispatch command (D2-10 core surface)"
    requirement: PORT-04
    verification:
      - kind: other
        ref: "RED: AlignmentFile write+read under 数据目录 failed FileNotFoundError pre-patch (narrow open, ACP 936) — probe output recorded in SUMMARY"
        status: pass
      - kind: other
        ref: "GREEN: _venv/bin/python.exe -m pytest tests/PortabilityRegression_test.py -k CJK → 5 passed"
        status: pass
      - kind: other
        ref: "sed -n '/static hFILE \\*hopen_fd/,/^}/p' htslib/hfile.c | grep -c _wopen → 2; narrow open() verbatim in #else (diff inspected)"
        status: pass
    human_judgment: false
  - id: D2
    description: "PORT-02 closure: permanent byte-level regression tests for every public file-path writer + committed one-time call-site checklist with zero unguarded sites (D2-08)"
    requirement: PORT-02
    verification:
      - kind: other
        ref: "_venv/bin/python.exe -m pytest tests/PortabilityRegression_test.py → 11 passed (6 TestBinaryMode: SAM LF-only, dispatch save_stdout LF-only incl. flagstat non-empty variant, tabix_compress byte-faithful on 50-CRLF payload, BAM BGZF magic + roundtrip, VCF/BCF roundtrip, double-compress determinism)"
        status: pass
      - kind: other
        ref: "grep -c 'def test_' tests/PortabilityRegression_test.py → 11; grep -c psam_open 02-PORT02-AUDIT.md → 7; no skip marks"
        status: pass
    human_judgment: false
  - id: D3
    description: "PORT-03 closure: LLP64-localized struct assertions (EXPECTED_SIZES table, no skips, POSIX literals unchanged) + C-level static asserts on hts_pos_t/long long/psam_off_t widths (D2-09)"
    requirement: PORT-03
    verification:
      - kind: other
        ref: "direct pyximport invocation builds tests/_compile_sizes (compilation IS the assertion) and check() is True → 'static asserts passed'"
        status: pass
      - kind: other
        ref: "grep -c _Static_assert tests/_compile_sizes.pyx → 4 (3 asserts + docstring mention); grep -c EXPECTED_SIZES tests/compile_test.py → 4; posix table values present (7 matches)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Zero POSIX regression: hfile.c/hts.c diffs confined to #if defined(_WIN32) guards with narrow paths byte-identical; libcport #else branch untouched"
    verification:
      - kind: other
        ref: "git diff bf3653bc -- htslib/hfile.c: zero deletions outside the moved open() line (now in #else verbatim); hts.c idx_stat_exists #else keeps plain stat(); smoke OK post-rebuild"
        status: pass
    human_judgment: true
    rationale: "Formal cross-platform proof is the fork CI ubuntu/macos run on the pushed commits; local executor cannot run Linux CI. Assigned to Plan 02-04 by the phase plan (commits are local on `win` until push)."

duration: 49 min
completed: 2026-10-12
status: complete
---

# Phase 2 Plan 2: PORT-02/03/04 Audit Closure Summary

**UTF-8→UTF-16 wide-open shims at three C layers (htslib hopen_fd, libcport opens, hts_idx_check_local stat probes) closing the CJK-path canary with byte-level regression suite (11 tests) plus LLP64-localized struct assertions and compile-time _Static_asserts**

## Performance

- **Duration:** 49 min
- **Started:** 2026-10-12T05:09:21Z
- **Completed:** 2026-10-12T05:58:28Z
- **Tasks:** 3
- **Files modified:** 8 (4 created, 4 modified)

## Accomplishments
- **PORT-04 (Task 1, tracer):** `htslib/hfile.c hopen_fd` gained a `_WIN32` block converting the UTF-8 filename via two-call `MultiByteToWideChar` into a malloc'd `wchar_t` buffer and opening with `_wopen`; the narrow `open()` call is preserved verbatim in `#else`; no MAX_PATH constant anywhere. RED evidence captured pre-patch: BAM write+read under a CJK tmp dir failed `FileNotFoundError` (UTF-8 bytes read as ACP-936 mojibake). Post-patch: 5/5 canary tests pass.
- **PORT-02 (Task 2):** `tests/PortabilityRegression_test.py::TestBinaryMode` — six byte-level tests (SAM LF-only, dispatch save_stdout LF-only with the flagstat substantive variant, tabix_compress byte-faithful over a 50-CRLF payload, BAM BGZF magic + roundtrip, VCF/BCF roundtrip, double-compress determinism via `checkBinaryEqual`/`checkGZBinaryEqual`); `02-PORT02-AUDIT.md` enumerates every raw open site with evidence and records zero unguarded sites.
- **PORT-03 (Task 3):** `tests/compile_test.py` `EXPECTED_SIZES` per-platform table consulted by all three `TestBinaryCompatibility` methods (posix entries byte-identical to the old literals; nt values measured and struct-composition-explained); `tests/_compile_sizes.pyx` carries three `_Static_assert` width gates (`hts_pos_t == 8`, `long long >= 8`, `psam_off_t == 8` via the libcport cimport) proven by direct pyximport compilation ("static asserts passed").
- Tracer feedback gate re-ran all Task 1 verify commands end-to-end post-commit (auto mode) — all green before expansion tasks started.

## Task Commits

1. **Task 1: hopen_fd wide-char shim + CJK path canary** - `51a6f00f` (feat; includes the two Rule-2 wide-open extensions in libcport/hts.c)
2. **Task 2: D2-08 byte-fidelity suite + call-site audit** - `8005d8c4` (test)
3. **Task 3: D2-09 LLP64-localized assertions + _Static_assert module** - `100389f1` (test)

**Plan metadata:** this commit (docs)

## Files Created/Modified
- `htslib/hfile.c` - hopen_fd _WIN32 _wopen conversion path (+32 lines, zero POSIX deletions)
- `htslib/hts.c` - `idx_stat_exists()` wide stat probe replacing 10 existence checks in `hts_idx_check_local`
- `pysam/libcport.pxd` - `psam_wopen()` (wide, `_O_BINARY`-forced, pmode-masked) behind `psam_open2/psam_open3`
- `tests/PortabilityRegression_test.py` - TestCJKPathCanary (5) + TestBinaryMode (6)
- `tests/compile_test.py` - EXPECTED_SIZES table, `_compile_sizes` import + test, artifact cleanup, pyximport hardening
- `tests/_compile_sizes.pyx` / `.pyxbld` - compile-time width gates + pyximport build hook (htslib include dir from file location)
- `.planning/phases/02-portability-tests/02-PORT02-AUDIT.md` - D2-08 one-time checklist

## Decisions Made
See key-decisions in frontmatter. Additional: the unused-function warning from `psam_wopen` in modules that cimport libcport without opening files is suppressed with a `__GNUC__`-guarded `PSAM_UNUSED` attribute (MSVC-clean forward path for Phase 3).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] libcport narrow opens unreachable for non-ACP paths**
- **Found during:** Task 1 (canary GREEN run)
- **Issue:** `tabix_index` on a CJK path failed at `tabix_compress`'s input open — 02-01's `psam_open2/3` mapped to narrow `_open`, which has the same ACP-936 defect the plan fixed only in htslib. The plan's canary surface (tabix fetch) is unreachable without it.
- **Fix:** `psam_wopen()` in libcport's `_WIN32` branch (same two-call pattern, `_O_BINARY` + pmode masking preserved); POSIX macros untouched.
- **Files modified:** pysam/libcport.pxd
- **Verification:** `test_cjk_vcf_tabix_index_and_fetch` passes (tabix_index → .tbi → TabixFile fetch returns both records).
- **Committed in:** 51a6f00f

**2. [Rule 2 - Missing Critical] index auto-discovery used narrow stat probes**
- **Found during:** Task 1 (canary GREEN run)
- **Issue:** `.bai`/`.csi`/`.tbi` existed but `fetch()` raised "fetch called on bamfile without index" — `hts_idx_check_local` probes candidates with narrow `stat()` (ACP-interpreted), so auto-discovery never finds them on non-ACP paths (explicit `index_filename` worked, proving the read path itself was fine).
- **Fix:** `idx_stat_exists()` helper (`_wstat` on the UTF-16 name under `_WIN32`, plain `stat()` verbatim under `#else`) replacing all 10 existence probes in that function; the probes never consumed `struct stat` beyond existence, so the replacement is behavior-identical on POSIX.
- **Files modified:** htslib/hts.c
- **Verification:** `test_cjk_bam_indexes_bai_and_csi` fetches 2 records via auto-discovered `.bai`.
- **Committed in:** 51a6f00f

**3. [Rule 3 - Blocking] editable rebuild does not recompile htslib objects**
- **Found during:** Task 1 (first rebuild)
- **Issue:** `pip install -e .` reported success but `htslib/hfile.o` stayed months stale — `prebuild_libchtslib` skips `make` when `libhts.a` exists and distutils does not relink extensions whose `extra_objects` changed, so an htslib C-source edit silently never reaches the .pyds.
- **Fix:** `_venv/bin/python.exe setup.py build_ext --inplace --force` (with `HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl MAKE=mingw32-make`) — make then rebuilds exactly the stale objects (hfile.o/hts.o) and all extensions relink.
- **Files modified:** none (build invocation; documented in SUMMARY + key-decisions for future plans)
- **Verification:** hfile.o/hts.o/libhts.a/.pyd mtimes refreshed; canary flipped green.
- **Committed in:** n/a (process)

**4. [Rule 3 - Blocking] pyximport could not resolve pysam/*.pxd under PEP 660 editable install**
- **Found during:** Task 3 (first direct pyximport verify)
- **Issue:** Cython compile error `'pysam/libcport.pxd' not found` — the editable install imports pysam through a MetaPathFinder, which Cython's file-based .pxd search cannot see (also latent for upstream's `_compile_test.pyx`).
- **Fix:** append the repo root to `sys.path` before `pyximport.install()` in compile_test.py (appended, not inserted, so a `PYTHONPATH=build` CI tree keeps module precedence).
- **Files modified:** tests/compile_test.py
- **Verification:** cython compiles; "static asserts passed".
- **Committed in:** 100389f1

**5. [Rule 3 - Blocking] pyximport default build dir relative under MSYS2 login shell**
- **Found during:** Task 3 (DLL load failure)
- **Issue:** `ntpath.expanduser('~')` ignores `HOME` and this shell chain lacks `USERPROFILE`/`HOMEPATH`, so pyximport built into a *relative* `./~/.pyxbld/` inside the repo — and a relative `.pyd` path cannot be loaded by the Windows extension loader (`LOAD_WITH_ALTERED_SEARCH_PATH` resolves relative names against the application dir). Loading the same artifact by absolute path worked, isolating the cause.
- **Fix:** `pyximport.install(build_in_temp=False, build_dir=os.path.join(tempfile.gettempdir(), "pysam-pyxbld"))`.
- **Files modified:** tests/compile_test.py
- **Verification:** fresh clean run prints "static asserts passed"; no stray `~` directory in the repo.
- **Committed in:** 100389f1

---

**Total deviations:** 5 auto-fixed (2 Rule 2 missing-critical, 3 Rule 3 blocking)
**Impact on plan:** Deviations 1-2 were the substantive discovery of this plan: the canary-first design did its job, forcing PORT-04's fix down to every narrow-open layer the D2-10 surface actually touches. Deviations 3-5 are build/environment mechanics required to execute and verify at all. No scope creep; every fix is `_WIN32`-guarded or test-infrastructure-local with POSIX behavior preserved verbatim.

## Issues Encountered
- Routine in-task test fixes (part of the task commits, not deviations): dispatch `view -H` returns bytes (decoded in-test), `TabixFile.fetch` returns str (marker typed per result), and the VCF→BCF double-write needed the source records captured into a list (single-pass iterator exhaustion).
- The `psam_wopen` unused-function warning in cimport-only consumers (libchtslib) was silenced with `PSAM_UNUSED` to keep the build warning-clean.
- `tempfile.mkstemp` binary-by-construction assumption (A5) continues to hold empirically — the dispatch save_stdout byte test passes through that machinery.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: same-class-extension | pysam/libcport.pxd, htslib/hts.c | Two additional untrusted-length C-string handling sites (psam_wopen, idx_stat_exists) beyond the plan's T-02-03 register entry (hfile.c). Both apply the identical mitigation: two-call length pattern, dynamically sized buffer, free on all paths, errno-mapped failures falling through to existing error handling. |

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for Plans 02-03 (test infra/generators) and 02-04 (suite green + fork-CI zero-regression closure, which formally closes this plan's D4/verification item 4).
- The `setup.py build_ext --inplace --force` rebuild contract applies to any future htslib C-source edit (02-03/02-04 touch .pyx/.py only, so the plain editable rebuild remains sufficient there).
- compile_test.py's full pytest run is deferred to 02-04 by the plan itself (setUpModule needs 02-03's Python data generators); the static-assert module is verified by direct pyximport now.
- Known limitation recorded (outside D2-10 core surface): `FastaFile`/faidx auto-discovery would need the same wide-stat treatment if non-ASCII FASTA paths become a requirement (v1 scope does not include it; the audit doc notes the pattern to copy).

## Self-Check: PASSED
- tests/PortabilityRegression_test.py, tests/_compile_sizes.pyx, tests/_compile_sizes.pyxbld, 02-PORT02-AUDIT.md — FOUND on disk
- htslib/hfile.c, htslib/hts.c, pysam/libcport.pxd, tests/compile_test.py — modified and committed
- commits 51a6f00f, 8005d8c4, 100389f1 all ancestors of HEAD — VERIFIED
- commits measured from ledger: 3 (git rev-list --count bf3653bc..HEAD)

---
*Phase: 02-portability-tests · Plan: 02*
*Completed: 2026-10-12*
