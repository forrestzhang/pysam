---
status: testing
phase: 01-mingw-w64
source: [01-VERIFICATION.md]
started: 2026-09-30T03:10:00Z
updated: 2026-09-30T03:10:00Z
---

## Current Test

number: 1
name: Ratify prohibition P1 (libcurl/remote I/O off on the Windows build path)
expected: |
  Human accepts the LLM-judge verdict (all evidence verified first-hand by the verifier):
  devtools/msys2-bootstrap.sh exports HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl;
  INSTALL documents the v1 remote-I/O boundary; htslib/config.h carries '#undef HAVE_LIBCURL'.
awaiting: user response

## Tests

### 1. Ratify prohibition P1 (libcurl off)
expected: Human accepts the LLM-judge verdict: devtools/msys2-bootstrap.sh exports HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl; INSTALL documents the v1 boundary; htslib/config.h carries '#undef HAVE_LIBCURL'
result: [pending]

### 2. Ratify prohibition P2 (symbol gate strength, incl. D-16)
expected: Human accepts: win32 dispatch calls check_ext_symbol_conflicts outside the exception-swallowing wrapper (setup.py:457-474); vacuous-pass guard raises when llvm-nm yields nothing (setup.py:413-419); keep-filter unchanged; probe teeth=904 / honesty=0. NOTE the deviation from the plan's literal wording: single-copy getopt was falsified and replaced by the user-adjudicated D-16 model (private mingwex copies + --exclude-symbols + closed 7-symbol win32 exemption, setup.py:141-144) — confirm this is accepted as within the prohibition's intent.
result: [pending]

### 3. Ratify prohibition P3 (dev-only, no distribution artifacts)
expected: Human accepts: no dist/, no *.whl, no pysam-*.tar.gz anywhere in the tree (checked 2026-09-30, excluding _venv/.git).
result: [pending]

### 4. Triage CR-01 (open Critical in 01-REVIEW-DISPOSITION.md)
expected: A disposition decision (fix scheduling or explicit accept-and-defer). Does NOT block the Phase 1 goal: the phase's dev-verification flow is the editable/inplace build (pip install -e . --no-build-isolation, D-14), where implib emission path and gate read path agree — ROADMAP SC-1 is satisfied by the proven editable path. Non-inplace builds (pip install ., setup.py build, bdist_wheel) crash with an unhandled CalledProcessError and must be fixed before any out-of-tree build phase.
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
