---
phase: 01-mingw-w64
plan: 02
subsystem: build-system
tags: [windows, msys2, ucrt64, setup-py, symbol-check, llvm-nm]
requires: [{phase: 01-01, provides: "bootstrap PKGS list (fail-fast message source of truth), smoke gate, eol contract"}]
provides:
  - "setup.py UCRT64 fail-fast gate (_is_ucrt64_python) naming the nine pacman packages + bootstrap script (D-03)"
  - "sh-prefixed configure on win32; win32 rpath elif (no ELF rpath on PE) — POSIX paths unchanged"
  - "BUILD-03 port: llvm-nm -g -P symbol gate on win32, fail-hard dispatch outside the exception-swallowing wrapper"
  - "Working win32 module topology: getopt compiled into pysam.libchtslib only, import library -Wl,--out-implib for the 12 downstream -l stubs, random/srandom macros"
  - "os.devnull in _pysam_dispatch stdout plumbing (Pitfall 8)"
  - "Stale shims win32/unistd.h, win32/stdint.h deleted (D-10)"
affects: ["01-03", "phase-02-portability"]
actuals:
  tokens: 8400
  tasks: 3
  commits: 3
plan_head_before: cc712670861f40c92fe6158cb1924992fe89e78b
tech-stack:
  added:
    - "llvm-nm (UCRT64 llvm-tools) as the Windows symbol-gate tool, POSIX.2 -P format"
    - "PE import library emission via -Wl,--out-implib for inter-module linking"
  patterns:
    - "win32-gated surgical branches (D-08): sys.platform/os.name/platform.system() inline tests, POSIX behavior byte-identical"
    - "EXT_SUFFIX-derived artifact names, never hardcoded cp3xx (D-02)"
key-files:
  created: []
  modified:
    - "setup.py"
    - "pysam/libcutils.pyx"
  deleted:
    - "win32/unistd.h"
    - "win32/stdint.h"
key-decisions:
  - "Gate detection = sysconfig.get_platform().startswith('mingw') AND MSYSTEM==UCRT64 on os.name=='nt' only (official MSYS2 snippet + belt-and-braces); POSIX returns True and is never gated"
  - "Symbol-gate fail-hard on win32 via dispatch restructure (if win32: call outside try; else: keep POSIX try/skip); separate-mode exemption is a loud explicit warning, never silent"
  - "random/srandom mapping moved from the deleted unistd.h shim into win32 define_macros, with vcfsom.c:362/513 named as live consumers"
  - "gh CLI was unauthenticated at CI-watch time; used the unauthenticated GitHub REST API against the public fork instead of surfacing a human-action checkpoint — same evidence, zero human steps (golden rule: automate everything automatable)"
patterns-established:
  - "Fork CI verdict read via REST API jobs list when gh auth is unavailable (ubuntu/macos blocking, FreeBSD/NetBSD advisory, D-12)"
requirements-completed: [BUILD-01, BUILD-03]
coverage:
  - id: D1
    description: "UCRT64 fail-fast gate: non-UCRT64 Windows python exits nonzero naming the nine pacman packages + sh devtools/msys2-bootstrap.sh (D-03)"
    requirement: BUILD-01
    verification:
      - {kind: command, ref: "python setup.py --version >/dev/null 2>&1 -> exit=1 under miniconda (non-UCRT64) python", status: pass}
      - {kind: command, ref: "gate output lists all 9 mingw-w64-ucrt-x86_64-* packages and msys2-bootstrap.sh (grep -o count=9, bootstrap grep=1)", status: pass}
      - {kind: command, ref: "POSIX not gated: _is_ucrt64_python() returns True when os.name != 'nt'; fork CI ubuntu/macos green proves no POSIX exit", status: pass}
    human_judgment: false
  - id: D2
    description: "sh-prefixed configure on win32 + win32 rpath elif; POSIX branches unchanged (Pitfalls 2/7)"
    requirement: BUILD-01
    verification:
      - {kind: command, ref: "grep -c \"elif sys.platform == 'win32':\" setup.py -> 1; POSIX else still appends -Wl,-rpath,$ORIGIN (diff-inspected)", status: pass}
      - {kind: command, ref: "git diff master hunk review: run_configure win32 gate is the only invocation change; no new shell=True call sites", status: pass}
    human_judgment: false
  - id: D3
    description: "BUILD-03 symbol gate port: _nm_command llvm-nm on win32, fail-hard dispatch, separate-mode loud exemption"
    requirement: BUILD-03
    verification:
      - {kind: command, ref: "grep -c 'llvm-nm' setup.py -> 3; parser body untouched (diff-inspected)", status: pass}
      - {kind: command, ref: "git diff master: win32 branch calls check_ext_symbol_conflicts outside try; POSIX try/except with two warnings preserved verbatim", status: pass}
    human_judgment: false
  - id: D4
    description: "win32 module topology: getopt single-copy in pysam.libchtslib, out-implib link flag, random/srandom macros, untested comment dropped (D-09)"
    requirement: BUILD-03
    verification:
      - {kind: command, ref: "grep -c 'win32/getopt.c' setup.py -> exactly 1; grep -c 'out-implib' -> 1; grep -cF \"('srandom', 'srand')\" -> 1", status: pass}
      - {kind: command, ref: "grep -n os_c_files -> 3 hits (win32 assign, POSIX assign, single libchtslib use); implib stub derived from EXT_SUFFIX suffix var (no cp3xx literal)", status: pass}
    human_judgment: false
  - id: D5
    description: "Stale shim deletion win32/unistd.h + win32/stdint.h, getopt pair retained (D-10)"
    requirement: BUILD-01
    verification:
      - {kind: command, ref: "test ! -f win32/unistd.h && test ! -f win32/stdint.h && test -f win32/getopt.c && test -f win32/getopt.h -> shims=0", status: pass}
      - {kind: command, ref: "shim content read pre-deletion: unistd.h carried the srandom/random defines now in define_macros; stdint.h was a 3rd-party pstdint", status: pass}
    human_judgment: false
  - id: D6
    description: "os.devnull in _pysam_dispatch stdout plumbing (Pitfall 8), POSIX behavior-preserving"
    requirement: BUILD-01
    verification:
      - {kind: command, ref: "grep -c 'os.devnull' pysam/libcutils.pyx -> exactly 2; grep -c '/dev/null' -> 0; only those 2 lines changed (diff-inspected)", status: pass}
    human_judgment: false
  - id: D7
    description: "Zero-regression: plan head 14398d74 pushed to fork; ubuntu + macos jobs green (D-11/D-12)"
    requirement: BUILD-01
    verification:
      - {kind: command, ref: "GitHub API run 35297346867 head_sha=14398d742826b57ac6b26d3dad28f58e6207d1b4, conclusion=success; all 17 ubuntu/macos jobs success (netbsd/freebsd also green, advisory)", status: pass}
      - {kind: command, ref: "git diff master hunk-by-hunk review: every setup.py hunk win32-gated or POSIX-no-op (os_c_files==[] on POSIX; _nm_command returns identical list; os.devnull=='/dev/null')", status: pass}
    human_judgment: false
duration: 24min
completed: 2026-09-18
status: complete
---

# Phase 1 Plan 02: UCRT64 Build Pipeline in setup.py Summary

**setup.py re-plumbed for MSYS2 UCRT64 with seven win32-gated surgical edits — fail-fast gate naming the nine pacman packages, sh-prefixed configure, llvm-nm fail-hard symbol gate (BUILD-03), single-copy getopt + import-library topology, rpath elif — plus the os.devnull dispatch fix and stale shim deletion; fork CI green on ubuntu+macos at 14398d74.**

## Performance

- **Duration:** 24 min (started 2026-09-18T01:49Z, completed 2026-09-18T02:14Z)
- **Tasks:** 3/3 (all auto)
- **Files:** 4 (2 modified, 2 deleted); 106 insertions / 850 deletions vs plan head
- **CI:** run 35297346867 on fork `forrestzhang/pysam` branch `win` — success (17 ubuntu/macos jobs green; netbsd/freebsd advisory, also green)

## Accomplishments

- **UCRT64 fail-fast gate (D-03):** `_is_ucrt64_python()` (mingw sysconfig platform AND `MSYSTEM==UCRT64`, POSIX never gated) exits with one actionable message listing the nine pacman packages verbatim from `devtools/msys2-bootstrap.sh` PKGS and pointing at the bootstrap script. Verified live: the local miniconda python exits 1 with the full package list.
- **Invocation hazards fixed (Pitfalls 2/7):** `run_configure` prepends `sh ` on win32 only (cmd.exe would otherwise try to run the POSIX configure script); `build_extension` gained an explicit win32 elif that adds no rpath flag (PE has no ELF rpath) — the POSIX `-Wl,-rpath,$ORIGIN` else branch is unchanged.
- **BUILD-03 symbol gate port:** `_nm_command()` returns `["llvm-nm", "-g", "-P"]` on win32; on win32 `cy_build_ext.run` calls `check_ext_symbol_conflicts()` outside the exception-swallowing wrapper (missing/broken llvm-nm aborts the build; never silently skipped); `HTSLIB_MODE=separate` on win32 is a loud explicit warning+skip; the POSIX try/skip with its two warnings is preserved verbatim.
- **Win32 module topology (D-09, Pitfalls 4/6):** dead "untested" branch rewritten in place — `include_os=['win32']`, `win32/getopt.c` compiled into pysam.libchtslib only (twelve other dicts lost `+ os_c_files`), `('random','rand')`/`('srandom','srand')` macros for bcftools/vcfsom.c:362/513, and pysam.libchtslib emits `-Wl,--out-implib,pysam/lib<EXT_SUFFIX-stem>.dll.a` so the downstream `-l` flags resolve via GNU ld's lib<name>.dll.a search in library_dirs.
- **Shim cleanup (D-10):** `win32/unistd.h` (whose srandom/random defines moved into define_macros) and third-party `win32/stdint.h` deleted; `win32/getopt.c/.h` retained.
- **Null-device portability (Pitfall 8):** both `c_open(b"/dev/null", O_WRONLY)` sites in `_pysam_dispatch` now use `force_bytes(os.devnull)` (`nul` on Windows, `/dev/null` on POSIX — behavior-preserving).
- **Zero-regression proof (D-11/D-12):** hunk-by-hunk `git diff master` review (every hunk win32-gated or POSIX-no-op) + fork CI: all ubuntu/macos jobs success on the pushed head.

## Task Commits

| Task | Name | Type | Commit |
| ---- | ---- | ---- | ------ |
| 1 | UCRT64 gate, sh-prefixed configure, win32 rpath branch | build | f251f204 |
| 2 | Port symbol gate to llvm-nm, rewrite win32 branch, drop stale shims | build | ed76cbac |
| 3 | os.devnull in _pysam_dispatch stdout paths (+ push, CI watch) | build | 14398d74 |

## Files Created/Modified

- `setup.py` (modified) — all seven edits: gate, `_nm_command`, fail-hard dispatch, win32 branch rewrite, getopt single-copy, implib flag, rpath elif
- `pysam/libcutils.pyx` (modified) — two `force_bytes(os.devnull)` call sites (383/390)
- `win32/unistd.h`, `win32/stdint.h` (deleted) — stale shims, D-10

## Decisions Made

- **Gate detection:** official MSYS2 snippet (`sysconfig.get_platform().startswith("mingw")`) plus the `MSYSTEM==UCRT64` belt-and-braces, applied only when `os.name == 'nt'`.
- **Fail-hard dispatch shape:** `if sys.platform == 'win32':` direct call / loud separate-mode warning, `else:` POSIX try/skip — restructuring confined to `cy_build_ext.run`, warning strings byte-identical.
- **Macro source of truth:** the random/srandom mapping now lives in the win32 branch of setup.py (the deleted shim previously provided it); harmless if UCRT64 headers declare the POSIX names — first live build (plan 01-03) will confirm.
- **CI watch automation:** gh was unauthenticated; used the unauthenticated GitHub REST API on the public fork (run + jobs endpoints) instead of pausing for `gh auth login` — same D-12 evidence, no human step required.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task 2 commit initially missing setup.py**
- **Found during:** Task 2 commit
- **Issue:** `git add setup.py win32/unistd.h win32/stdint.h` failed as a whole (a pathspec listing an already-`git rm`'d file matches nothing in the worktree, and `git add` is all-or-nothing across pathspecs), so commit 70ca437e landed with only the deletions while its message claimed the setup.py edits.
- **Fix:** staged setup.py and amended the not-yet-pushed commit (now ed76cbac), restoring the intended atomic per-task commit.
- **Files modified:** commit content only (setup.py included)
- **Verification:** `git show --stat HEAD` shows setup.py + both deletions in ed76cbac
- **Commit:** ed76cbac

**Total deviations:** 1 auto-fixed (staging mechanics). **Impact:** zero — final history is atomic per task; nothing pushed between the faulty and fixed states.

## Issues Encountered

- `gh` CLI is not authenticated on this machine (plan anticipated a human-action gate). Resolved without human input via the public REST API; `gh auth login` remains available for future phases.
- The live UCRT64 build itself (configure/make/llvm-nm execution) is intentionally plan 01-03's scope, gated on the manual MSYS2 install (D-15); this plan proves the source-level contract and POSIX CI only.

## User Setup Required

None for this plan. (MSYS2 UCRT64 install remains the pre-01-03 manual step documented in INSTALL.)

## Next Phase Readiness

- Ready for 01-03: the seven-edit pipeline is internally consistent (gate message ≡ bootstrap PKGS; implib name ≡ downstream `-l` stubs; getopt single-copy keeps the mandatory symbol check free of legitimate duplicates) and POSIX CI is green on the fork.
- BUILD-01/BUILD-03 completion depends on 01-03's live build proof (shared-ID gate: REQUIREMENTS.md checkboxes stay open until the build runs).

## Self-Check: PASSED

setup.py, pysam/libcutils.pyx present with the edits; win32/unistd.h and win32/stdint.h absent; commits f251f204, ed76cbac, 14398d74 found in history; `git rev-list --count cc712670..HEAD` = 3 matching frontmatter `commits: 3`.
