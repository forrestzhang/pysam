---
gsd_state_version: "1.0"
current_phase: 03
current_phase_name: MSVC 构建系统
status: executing
stopped_at: Phase 02 complete, ready to plan Phase 3
last_updated: "2026-10-12T11:54:52.764Z"
last_activity: 2026-10-12
last_activity_desc: Phase 02 complete, transitioned to Phase 3
state_head: 47c4df2ff97a27601544495dcb31a8bd8e70e65f
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 12
  completed_plans: 7
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-12)

**Core value:** Windows 用户能够 `pip install` 拿到 wheel 并正常使用 pysam 的全部功能（htslib API 绑定 + samtools/bcftools 命令封装），完整测试套件在 Windows 上通过。
**Current focus:** Phase 3 — MSVC 构建系统

## Current Position

Phase: 03 (MSVC 构建系统) — READY TO EXECUTE
Plan: Not started
Status: Ready to execute
Last activity: 2026-10-12 — Phase 02 complete, transitioned to Phase 3

Progress: [█████░░░░░] 50%

## Performance Metrics

**Velocity:**

- Total plans completed: 7
- Average duration: N/A
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | - | - |
| 02 | 4 | - | - |

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

Last session: 2026-10-12T09:57:56.199Z
Stopped at: Phase 02 complete, ready to plan Phase 3
Resume file: None
