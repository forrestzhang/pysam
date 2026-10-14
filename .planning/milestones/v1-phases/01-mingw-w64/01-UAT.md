---
status: complete
phase: 01-mingw-w64
source: [01-VERIFICATION.md]
started: 2026-09-30T03:10:00Z
updated: 2026-09-30T03:45:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Ratify prohibition P1 (libcurl off)
expected: Human accepts the LLM-judge verdict: devtools/msys2-bootstrap.sh exports HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl; INSTALL documents the v1 boundary; htslib/config.h carries '#undef HAVE_LIBCURL'
result: pass
note: user delegated check to orchestrator; re-verified first-hand 2026-09-30: bootstrap:74-75 exports --disable-libcurl; INSTALL:122-124 documents v1 remote-I/O boundary; htslib/config.h:108 '#undef HAVE_LIBCURL' (real 6999-byte configure product); setup.py:664 is the recognized-options whitelist not an enablement; setup.py:751 only reflects config.h into Python constants; install-prerequisites.sh is the Linux apt path, out of scope

### 2. Ratify prohibition P2 (symbol gate strength, incl. D-16)
expected: Human accepts: win32 dispatch calls check_ext_symbol_conflicts outside the exception-swallowing wrapper (setup.py:457-474); vacuous-pass guard raises when llvm-nm yields nothing (setup.py:413-419); keep-filter unchanged; probe teeth=904 / honesty=0. NOTE the deviation from the plan's literal wording: single-copy getopt was falsified and replaced by the user-adjudicated D-16 model (private mingwex copies + --exclude-symbols + closed 7-symbol win32 exemption, setup.py:141-144) — confirm this is accepted as within the prohibition's intent.
result: pass
note: user delegated check to orchestrator; re-verified first-hand 2026-09-30: win32 dispatch bare-calls the gate (no try/except) while POSIX keeps the wrapper; vacuous-pass guard raises on empty symbol set; diff vs upstream 4c8486b1 shows only additive win32 branches (.dll.a read / guard / closed exemption), error core unchanged; WIN32_GETOPT_EXEMPT_SYMBOLS = exactly 7 symbols; live probe rerun exit 0 (13 modules, teeth=904, honesty=0, exemption hits 0). Footnote: exemption log text labels the decision D-14 while PROJECT.md records D-16 — naming artifact only

### 3. Ratify prohibition P3 (dev-only, no distribution artifacts)
expected: Human accepts: no dist/, no *.whl, no pysam-*.tar.gz anywhere in the tree (checked 2026-09-30, excluding _venv/.git).
result: pass
note: user delegated check to orchestrator; re-verified first-hand 2026-09-30: find over tree (excl. _venv/.git) → 0 *.whl, 0 *.tar.gz; no dist/ directory; git ls-files tracks no wheel/tarball/dist path

### 4. Triage CR-01 (open Critical in 01-REVIEW-DISPOSITION.md)
expected: A disposition decision (fix scheduling or explicit accept-and-defer). Does NOT block the Phase 1 goal: the phase's dev-verification flow is the editable/inplace build (pip install -e . --no-build-isolation, D-14), where implib emission path and gate read path agree — ROADMAP SC-1 is satisfied by the proven editable path. Non-inplace builds (pip install ., setup.py build, bdist_wheel) crash with an unhandled CalledProcessError and must be fixed before any out-of-tree build phase.
result: pass
note: user delegated check to orchestrator; verified first-hand 2026-09-30 (emission cwd-relative setup.py:546-554 vs gate get_ext_fullpath read; agree on inplace, diverge on non-inplace). DISPOSITION: deferred to Phase 3 entry (BUILD-02 MSVC — first out-of-tree build phase); recorded in 01-REVIEW-DISPOSITION.md (open 8→7); fix direction: derive implib path from os.path.dirname(get_ext_fullpath)

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
