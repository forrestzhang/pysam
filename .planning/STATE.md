---
gsd_state_version: "1.0"
milestone: v4.3.1
current_phase: 04
status: completed
stopped_at: Phase 04 complete — all phases complete
last_updated: "2026-10-13T06:51:56.080Z"
last_activity: 2026-10-13
last_activity_desc: Phase 04 complete
state_head: 0749da947b122e94a5d7ad098765235656bc0d17
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 15
  completed_plans: 15
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-12)

**Core value:** Windows 用户能够 `pip install` 拿到 wheel 并正常使用 pysam 的全部功能（htslib API 绑定 + samtools/bcftools 命令封装），完整测试套件在 Windows 上通过。
**Current focus:** Phase 04 — Windows CI 与 wheel 分发

## Current Position

Phase: 04
Plan: Not started
Status: All phases complete
Last activity: 2026-10-13 — Phase 04 complete

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 15
- Average duration: N/A
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | - | - |
| 02 | 4 | - | - |
| 03 | 5 | - | - |
| 04 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: N/A
- Trend: N/A

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 18 min | 3 tasks | 4 files |
| Phase 01 P02 | 24 min | 3 tasks | 4 files |
| Phase 01 P03 | 11d 18h (11.5d paused at gh-auth gate; ~6h active) | 3 tasks | 8 files |
| Phase 02 P01 | 27 min | 3 tasks | 6 files |
| Phase 02 P02 | 49 min | 3 tasks | 8 files |
| Phase 02 P03 | 54 min | 3 tasks | 12 files |
| Phase 02 P04 | 53 min | 3 tasks | 3 files |
| Phase 03 P01 | 28 min | 3 tasks | 9 files |
| Phase 03 P02 | 26 min | 3 tasks | 219 files |
| Phase 03 P03 | 26 min | 3 tasks | 12 files |
| Phase 03 P04 | 118 min | 3 tasks | 21 files |
| Phase 03 P05 | 68 min | 3 tasks | 10 files |
| Phase 04 P01 | 56 min | 2 tasks | 1 files |
| Phase 04 P02 | 88 min | 4 tasks | 1 files |
| Phase 04 P03 | 27 min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: MSVC 构建系统（Phase 3）置于 CI/wheel 分发（Phase 4）之前 — CI-02 要求 MSVC 产出的 wheel（PROJECT.md 决策"wheel 只发 MSVC"），wheel 阶段依赖 MSVC 构建系统就位。与研究建议序（CI/wheels → MSVC）不同，以需求文本与项目决策为准。
- [Phase 01]: Phase 1 Windows build targets MSYS2 UCRT64 pacman python; the bootstrap script's 9-package PKGS list is the single source of truth, mirrored verbatim by setup.py's UCRT64 fail-fast message (D-01/D-03/D-13). — One source prevents drift between the provisioning contract and the build gate; locked in plan 01-01 Task 1 and grep-verifiable (fixed-string count == 1).
- [Phase 01]: D-16 (user-adjudicated option-1, plan 01-03): getopt family excluded from libchtslib export surface via --exclude-symbols; private mingwex static copies per tool module; BUILD-03 win32 exemption CLOSED at 7 symbols {getopt, getopt_long, getopt_long_only, optarg, optind, opterr, optopt} — D-10 shared-copy premise falsified by the first real UCRT64 build
- [Phase 01]: Win32 symbol-gate evidence channel = .dll.a import libraries: distutils links with -s (strip) so .pyd has no readable symbol table; llvm-nm parses the PE archives (A2 verified); removing -s not authorized
- [Phase 01]: Plan 01-03 CI evidence via unauthenticated public REST API (same endpoint gh run view reads) when gh CLI is unauthenticated — standing substitute authorized by orchestrator (2026-09-30); ubuntu/macos blocking, BSD advisory (D-12)
- [Phase 02]: Plan 02-01: libcport uses cdef extern from * + #ifdef C-preprocessor switch (Cython 3.3.0 has no usable compile-time conditional; fixed-arity macros only; POSIX branch pure identity aliases).
- [Phase 02]: Plan 02-01: save_stdout byte proof runs on flagstat, not view - samtools view writes via htslib '-' to fd 1 on every platform so its save_stdout file is always empty; flagstat is the command that flows through the dispatch redirect fd.
- [Phase 02]: Plan 02-01: write-side CRLF corruption at libcutils save_stdout was masked in-process by CPython startup _fmode=_O_BINARY (fdopen FILE* layer); psam_open3's _O_BINARY makes the fd binary-by-flag (standalone-C probe proved CRT default corrupts). Read side (tabix_compress) was live-corrupt: 203->153 bytes, fixed.
- [Phase 02]: Plan 02-01: canonical UCRT64 rebuild requires both HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl and MAKE=mingw32-make (devtools/msys2-bootstrap.sh contract).
- [Phase 02]: Plan 02-02: PORT-04 needed wide-open shims at THREE layers, not one - hopen_fd (htslib), psam_wopen (libcport, covers tabix_compress/save_stdout), idx_stat_exists (hts.c index auto-discovery). Canary-first design found each; all use two-call MultiByteToWideChar, no MAX_PATH.
- [Phase 02]: Plan 02-02: htslib C-source edits require 'setup.py build_ext --inplace --force' - pip install -e . skips libhts.a rebuild when it exists and extensions do not relink on extra_object changes.
- [Phase 02]: Plan 02-02: pyximport on this env needs repo root appended to sys.path (PEP 660 editable hides pysam/*.pxd from Cython) and an absolute build_dir (relative .pyd paths fail the Windows loader).
- [Phase 02]: D2-06 Windows data generation: per-directory make_data.py generators behind make_data_files sys.platform dispatch (importlib file-location load, unique module name per directory); Makefiles stay the POSIX authority and the make line is byte-identical. Generator stdout must be taken from the dispatch RETURN value - raw=True only bypasses parsers; the collector returns str for text output and bytes only when the text-mode read raises UnicodeDecodeError (02-03).
- [Phase 02]: htslib fd_write Windows raise(SIGTERM)-on-broken-pipe kills the CPython host process (CPython sets SIGPIPE to SIG_IGN on POSIX so Linux never dies); pysam Windows port reports errno=EPIPE with an error return instead - identical error flow on every platform, POSIX block untouched (02-03).
- [Phase 02]: Dispatch exit interception (samtools_exit/bcftools_exit) crashes with STATUS_BAD_STACK (0xC0000028) under UCRT longjmp's RtlUnwindEx despite full .pdata coverage; _WIN32 builds use GCC __builtin_setjmp/__builtin_longjmp (direct register restore, no SEH unwind, setjmp and longjmp live in one TU); POSIX keeps standard setjmp/longjmp verbatim (02-03).
- [Phase 02]: samtools_test win32 oracle: redirect statements capture dispatch output to the target file; -o statements run with catch_stdout=False letting samtools' own output handling write the files; three-tier comparison ladder unchanged; POSIX keeps the external run_command oracle and fork CI ubuntu remains the external-binary coverage (D2-05 acknowledged weakening) (02-03).
- [Phase 02]: Plan 02-04: upstream #1274's four known failures reduce to one test-hygiene bug on our build - TestLogging check() leaked an open FileHandler (POSIX tolerates unlink-while-open; Windows WinError 32); fixed by closing the handler (POSIX no-op). testReadingFromFileWithoutIndex passes; zero exemptions needed for the checklist names.
- [Phase 02]: Plan 02-04: httpserver must be platform-split - _pysam_dispatch runs samtools mains with the GIL held, so 02-03's thread server starved during dispatch-blocked libcurl transfers (ubuntu TestRemoteFileHTTP::testView timeout); POSIX restored upstream's child-process server verbatim, win32 keeps the spawn-safe thread variant. v2 remote-I/O note: Windows needs the process server or a nogil dispatch once libcurl is enabled.
- [Phase 02]: Plan 02-04: TEST-02 baseline = fork CI direct (ubuntu, 3.14) on the phase-final code SHA; node-id set reconciliation (not count arithmetic) shows collection differs in exactly one module - typechecking (mypy on CI, absent from UCRT64 venv, documented as env-difference exemption). Windows collected 1040 = 1028 + phase's own 12 tests; run-vs-collect +2 = module-skip placeholders.
- [Phase 03]: 03-01: GCC-builtin dispatch gate implemented as a feature macro (<tool>_DISPATCH_GCC_BUILTIN_JMP) defined once per file under #if defined(_WIN32) && !defined(_MSC_VER) — three gate sites (jmpbuf type/dispatch/exit) but the grep gate requires exactly one condition occurrence per file; template regenerates both twins byte-identically (sed-verified)
- [Phase 03]: 03-01: coverage.c VLA kept verbatim in #else arm (zero-regression red line outranks the plan's grep==0 criterion, which contradicts its own #else-verbatim action text); MSVC arm heap-allocates under _MSC_VER — MSVC never sees a VLA
- [Phase 03]: 03-02: xz 5.8.4 consumes a no-config route (-DHAVE_STDINT_H/-DHAVE_INTTYPES_H/-DHAVE_STDBOOL_H) — its windows/ dir is docs-only in 5.8.4 (MSVC builds moved to CMake); the define set is the recorded configuration base for 03-03
- [Phase 03]: 03-02: musl regex internal-header fan-out neutralized by 2 glue adaptations (regex.h stddef/regoff_t; locale_impl.h LCTRANS_CUR identity shim) — 0 real musl-internal headers vendored, TRE fallback not triggered; define set hidden= + RE_DUP_MAX=255 + CHARCLASS_NAME_MAX=14
- [Phase 03]: 03-02: two genuine-MSVC-gap compat edits recorded in vendor/regex — regexec.c [restrict] array-param qualifier dropped (hts_internal.h [static] precedent); tre.h ALIGN (long)->(size_t) for win64 LLP64 (C4311 truncation)
- [Phase 03]: [Phase 03-04]: MSVC cross-module binding = HTSLIB_EXPORT dllimport consumer arm (hts_defs.h, _MSC_VER-gated) + /DEF lists + lib-prefixed internal names — link.exe has no auto-import for data (seq_nt16_*), and the /FI shim cannot win: MSVC takes the LAST declaration's linkage
- [Phase 03]: [Phase 03-04]: MSVC arm uses /GL- (distutils /GL+/LTCG ICEs the cl 14.50 backend on filter_decoder.c; upstream xz MSVC builds never use /GL) and /std:c11 /utf-8 via extra_compile_args — set_executables is a no-op under MSVCCompiler
- [Phase 03]: [Phase 03-04]: win32/msvc/msvc_compat.h closes _CRT_DECLARE_NONSTDC_NAMES (stdlib min/max macros collided with the trees' own functions; the open gate's off_t is 32-bit) — every legacy POSIX name now maps to an always-declared underscore spelling; the fd trio is declared, not mapped (macros mangled hFILE_backend->read member calls)
- [Phase 03]: [Phase 03-04]: xz consumes the full autotools-equivalent feature define set; the bare 3-define route left decoders[] empty (cl ICE) and the HAVE_SMALL/mt/tablegen TUs are excluded from the module graph; -Dhidden= dropped globally (tre.h compat edit 2)
- [Phase 03]: 03-05: MSVC suite green via root-cause fixes, not skips -- fd double-close (dup at lend sites), WR-01 binary-capture regression (strict-first decode), GNU-getopt optind reinit, C11 assert portability; 1028/15 both toolchains
- [Phase 03]: SC-3: cl.exe-first, clang-cl documented contingency only -- 1.24-tree error surface is 2 C99 sites + finite shim, both closed; premise of prior-art clang-cl-for-VLAs advice superseded
- [Phase 03]: CI syntax floor = oldest supported Python (3.9): PEP 701 f-string backslash killed py3.9-3.11 cells though 3.13/3.14 accept it; ast.parse(feature_version=(3,9)) as pre-push gate
- [Phase 04]: [Phase 04-01]: Windows CI test step globs build/lib.* via cygpath -m $GITHUB_WORKSPACE - Git Bash on runners does not expand globs against backslash-form Windows paths (raw $GITHUB_WORKSPACE echoed literally; ModuleNotFoundError at pytest collection).
- [Phase 04]: [Phase 04-01]: Windows CI pip prerequisites need --upgrade - python.org 3.10/3.11 hostpythons bundle setuptools 65.5.0 (pip no-ops without -U) and that generation detaches the process stdout stream during the MSVC build (logging errors; pytest dies at collection with 'underlying buffer has been detached'); 3.12+ bundle nothing and were green from the start. Locally reproduced with setuptools==65.5.0 vs 84.0.0.
- [Phase 04]: [Phase 04-01]: windows (3.11) cell's extra skip is upstream-owned hygiene (skipif testIteratorOutOfScope on CPython 3.11 'invalid accesses crash'), not a runner anomaly; all six cells 1031-1032 passed / 16-17 skipped, delta vs local 1028/15 reconciles in 04-CI-VALIDATION.md.
- [Phase 04]: [Phase 04-03]: All 04-03 Release URLs executed against v0.24.1-win.2, not the plan's literal win.1 - 04-02's publish run failed on win.1 before creating any Release and the Task 4 contingency re-tagged; 04-02-SUMMARY (the plan's read_first) is the authority; win.1 tag + failed run stay as audit trail.
- [Phase 04]: [Phase 04-03]: CI-vs-local delta reconciled node-exactly: 1032/16 = 1028/15 + 6 mypy-collected typechecking tests - 2 tty-gated testUsage units (runner stdin never a tty) + 1 upstream 3.11 skipif; zero unexplained differences.
- [Phase 04]: [Phase 04-03]: Wheel shadowing asserts must run in the script-form context (sys.path[0] = script dir) - python -c from the repo root puts cwd on sys.path and resolves to the source tree, a false test of its own guard.

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 3] CR-01：非 inplace 构建（`pip install .` / `bdist_wheel`）在 win32 符号门处未捕获 CalledProcessError（implib 发射路径 vs 读取路径分叉）— MSVC/wheel 阶段前必须修复（D-17，01-REVIEW-DISPOSITION.md deferred）。
- Phase 2 research flag: Cython 3.1 编译期平台开关惯用法 + `libc.msvcrt`/`libc.io` 精确映射待核实。
- Phase 3 research flag: clang-cl 回退路径与 MSVC C99 shim 范围（bundled 源码 VLA 清单）需决策 spike。

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-13T04:05:05.744Z
Stopped at: v1 milestone complete — all 4 phases verified
Resume file: None
