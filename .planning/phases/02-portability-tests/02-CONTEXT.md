# Phase 2: 可移植性加固与测试全绿 - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning

<domain>
## Phase Boundary

The full pytest suite (default collection: `testpaths = pysam tests` per `setup.cfg`, bench files excluded) passes green on Windows in the MSYS2 UCRT64 environment (runtime locked by Phase 1 D-01: pacman python, single version). All POSIX-only dependencies in the Cython/library layer are eliminated or platform-gated with a grep-clean audit as closure evidence. Binary-mode I/O, LLP64 widths, and CJK non-ASCII paths each carry permanent regression protection. Requirements covered: PORT-01, PORT-02, PORT-03, PORT-04, TEST-01, TEST-02 (TEST-02 reconciliation mechanics left to planner/researcher discretion — only the "fix-first, then exempt" policy and the exemption-list discipline were user-decided, see D2-07).

NOT in this phase: MSVC toolchain (Phase 3), Windows CI runners and wheels (Phase 4), remote I/O / libcurl enablement (v2), Python version matrix (Phase 4), bench-file porting (excluded from "green" by D2-11).

</domain>

<decisions>
## Implementation Decisions

### Pre-locked project constraints (carried forward — do not re-litigate)
- **Runtime = MSYS2 UCRT64 pacman python, single version** (Phase 1 D-01/D-02). All Phase 2 testing happens in this environment.
- **Zero POSIX regression**: fork CI on every push stays green (Phase 1 D-11/D-12).
- **`devtools/smoke_test.py`** exists from Phase 1 (D-04) and may be reused/extended for quick pre-suite checks.
- **getopt exemption closed set** (Phase 1 D-16) — BUILD-03 symbol-gate behavior is settled; not re-opened here.
- **libcurl stays disabled** on the Windows path in v1 — remote-I/O tests are expected Windows skips, subject to D2-07's no-silent-skip discipline.

### POSIX cleanup depth (PORT-01)
- **D2-01:** The three `posix.*` cimport modules (`pysam/libchtslib.pyx`, `pysam/libcutils.pyx`, `pysam/libctabix.pyx`) are converted to compile-time platform switches **in this phase** (Cython 3.1 plain-if idiom + `libc.msvcrt`/`libc.io` mappings), not deferred to Phase 3. One pass serves MinGW now and MSVC later; PORT-01 closes fully. — **Reversibility:** costly — the switch shape (cimport surface consumed by three modules) becomes the contract `libcport.pxd` (D2-04) publishes; undoing means re-touching every consumer.
- **D2-04:** Platform-switch code organization = **one centralized mapping layer** (`pysam/libcport.pxd` or equivalent) that publishes `dup`/`open`/`close`/`read` etc. and internally targets `posix.*` or `libc.msvcrt`/`libc.io` per platform. The three `.pyx` files change only their cimport lines. Matches the pre-registered architecture in `.planning/research/ARCHITECTURE.md` ("one `libcport.pxd` for Cython `posix.*` replacements"). Exact filename is researcher/planner latitude; the single-point-of-mapping property is the locked part.
- **D2-02:** W3's hardcoded `b"/dev/null"` in `pysam/libcutils.pyx` is fixed with a **platform-conditional constant** (`b"NUL"` vs `b"/dev/null"`); the fd-redirection structure around it stays untouched (W10/`fdopen` territory is deliberately not restructured in this phase).
- **D2-03:** PORT-01 acceptance = **grep-clean checklist audit**: enumerate every POSIX-only symbol/path (posix.* cimports, unistd-only functions, `/dev/null`, fork/signal, POSIX path separators) across Cython + shim layers; each entry is either platform-guarded or eliminated; the checklist lands in the phase documentation and doubles as the Phase 3 MSVC inventory.

### Test porting strategy (TEST-01)
- **D2-05:** The ~7 test files with POSIX shell calls are rewritten to **pure in-process comparisons** — `check_samtools_view_equal`-style helpers call pysam's own dispatch (or pure-Python read-back) instead of invoking an external `samtools` executable. No pacman `samtools`/`bcftools` dependency enters the test environment (diverges deliberately from upstream PR #1274's approach).
- **D2-06:** Test-data generation (`tests/pysam_data/`, `tests/tabix_data/`, `tests/cbcf_data/` Makefiles) is **rewritten in Python** — generators call pysam's own APIs to produce `.bam`/`.cram`/`.bcf` etc.; `make_data_files()` dispatches by platform. The Makefiles remain authoritative on POSIX (zero regression) unless the planner finds a single-source form that keeps the Linux path byte-identical.
- **D2-07:** Known-failure policy = **fix first, exempt only with cause**. Upstream #1274's four same-environment failures (`TestLogging::testFail1/testNoFail1/testNoFail2`, `TestIO::testReadingFromFileWithoutIndex`) enter as an expected-failures checklist; each gets root-cause work first; only genuine platform-behavior differences may become skips, each with a written reason in an exemption list. Zero silent skips.
- **D2-11:** "Green" = **default pytest collection** (`setup.cfg` `testpaths = pysam tests`), bench files (`*_bench.py`) excluded — matches upstream CI semantics; the known bench `samtoolsshell` path breakage does not block this phase.

### Audit evidence shape (PORT-02/03/04)
- **D2-08:** PORT-02 produces both a **one-time grep checklist** (every `open`/`c_open`/`fopen` call site verified for `O_BINARY`/`"b"`) **and permanent byte-level regression tests** (Windows write BAM/BGZF/SAM → read back → `checkBinaryEqual`) that live in the regular suite — any future text-mode regression fails CI, not just the audit.
- **D2-09:** PORT-03 = `tests/compile_test.py` struct-size assertions updated for LLP64 **plus** a small set of C-level `static assert`s (compile-time verification of critical type widths like `hts_pos_t`/`off_t` class types). No exhaustive `long`-API sweep.
- **D2-10:** PORT-04 CJK canary covers the **core surface**: CJK-path `AlignmentFile`/`VariantFile` read + write + index (`.bai`/`.csi`/`.tbi`) + tabix query + one dispatch command, round-tripped via tmp directories. Not a full unicode matrix.

### Claude's Discretion
- Exact `libcport.pxd` file name, internal layout, and whether the mapping is pxd-only or pxd+pxi.
- TEST-02 reconciliation mechanics: where the Linux baseline numbers come from (local run vs upstream CI), the comparison artifact format, and the skip-diff threshold — only D2-07's fix-first policy and written-reason exemption discipline are locked.
- The Cython 3.1 platform-switch idiom details (`IF` deprecation handling, exact `libc` module mappings to verify) — pre-registered as a research gap; researcher validates.
- Which specific tests beyond #1274's list need exemptions (discovered during execution, added with reasons).
- Whether Python data generators share code with the POSIX Makefile inputs or fully replace them on Windows only.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition and requirements
- `.planning/PROJECT.md` — Core value, zero-regression constraint, upstreamable-patches-only rule
- `.planning/REQUIREMENTS.md` — PORT-01..04, TEST-01, TEST-02 definitions (this phase's six requirements)
- `.planning/ROADMAP.md` — Phase 2 goal + success criteria 1–5
- `.claude/CLAUDE.md` — Anti-patterns table (text-mode I/O is the blocking one for PORT-02); note its "current focus" section is stale (still says Phase 1)

### Codebase maps (this phase's territories)
- `.planning/codebase/TESTING.md` — Suite structure, `make_data_files` idempotent pattern, `checkBinaryEqual` helpers, conftest HTTP fixture, `-s` capture constraint
- `.planning/codebase/CONCERNS.md` — W2 (posix.* cimports, three modules + line numbers), W3 (/dev/null), W4 (bundled C tty APIs), W9 (test-suite POSIX-isms incl. the 7 shell-test files), W10 (fdopen/jmp_buf risk zone)

### Prior phase and research
- `.planning/phases/01-mingw-w64/01-CONTEXT.md` — D-01..D-16 carried decisions (esp. D-01 runtime, D-04 smoke script, D-16 getopt set)
- `.planning/research/UPSTREAM-PRS.md` — Upstream #1274/#1400 field report: 958-test baseline, the 4 known failures (D2-07 checklist), samtoolsshell bench breakage, maintainer stance
- `.planning/research/ARCHITECTURE.md` — Pre-registered `libcport.pxd` centralized-shim design (D2-04 implements this)
- `.planning/research/SUMMARY.md` — Research flags: Cython 3.1 platform-switch idiom + `libc.msvcrt`/`libc.io` exact mappings still to validate (Phase 2 flag)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/TestUtils.py` `checkBinaryEqual`/`checkGZBinaryEqual`/`make_data_files` (idempotent via `all.stamp`/`all.lock`) — the extension points for D2-06 platform dispatch and D2-08 regression tests
- `devtools/smoke_test.py` (Phase 1) — quick import+BAM+dispatch check; cheap pre-suite sanity during porting iterations
- `pysam/libcutils.pyx` dispatch machinery (`_pysam_dispatch`) — the in-process comparator D2-05 rewires tests toward; already exercises bundled samtools/bcftools mains

### Established Patterns
- `setUpModule(): make_data_files(DATADIR)` module-level data prep — D2-06 generators plug in behind this existing call, no test-file churn
- Class-based xunit + fixture mix; `monkeypatch`/`tmp_path` built-ins only (no unittest.mock) — new tests should stay in this idiom
- `-s` (no capture) is mandatory in `setup.cfg` addopts — conflicts with `pysam.dispatch` fd redirection; never run with capture

### Integration Points
- `pysam/libchtslib.pyx:10`, `pysam/libcutils.pyx:22-23`, `pysam/libctabix.pyx:62-63` — the three cimport sites D2-01/D2-04 replace
- `pysam/libcutils.pyx` `_pysam_dispatch` — the two `b"/dev/null"` opens (W3, D2-02)
- `tests/conftest.py:35-45` — multiprocessing HTTP server fixture → threading rewrite (D2-07-adjacent spawn safety)
- `tests/compile_test.py` — PORT-03 LLP64 assertion updates (D2-09)
- `setup.cfg` `[tool:pytest]` — testpaths define the D2-11 "green" perimeter

</code_context>

<specifics>
## Specific Ideas

- Upstream #1274's test log is the concrete expected-failure checklist for D2-07 — use its four failures verbatim as the starting exemption candidates.
- The D2-03 grep-clean checklist should be structured so Phase 3 can consume it directly as the MSVC porting inventory (symbol → guard location → MSVC status column).
- D2-08's regression tests should write via every public writer that touches a file path (AlignmentFile/VariantFile/BGZFWriter at minimum), not just one representative.

</specifics>

<deferred>
## Deferred Ideas

- TEST-02 baseline/threshold deep-design (where Linux baseline numbers come from, exact skip-diff threshold) — deselected from discussion; planner/researcher discretion within D2-07 discipline.
- Bench-file (`*_bench.py`) Windows porting — excluded from "green" (D2-11); revisit only if Phase 4 CI wants perf signals.
- Remote-I/O tests beyond documented skips — v2 scope (libcurl deferred).

</deferred>

---

*Phase: 2-可移植性加固与测试全绿*
*Context gathered: 2026-10-12*
