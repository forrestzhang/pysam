# Phase 2: 可移植性加固与测试全绿 - Research

**Researched:** 2026-10-12
**Domain:** POSIX-dependency elimination in pysam's Cython layer (platform-switch idiom + libc mapping), Windows test-suite porting (in-process comparators, Python data generators, spawn-safe conftest), binary-mode/LLP64/CJK-path audit closure
**Confidence:** HIGH (all codebase claims read and quoted this session; all Cython/libc idioms **compiled and executed** on the actual UCRT64 + Cython 3.3.0 toolchain; remaining unknowns are the 4 upstream failures' root causes, explicitly logged as in-phase work per D2-07)

## Summary (摘要)

本阶段的技术核心是三件事：(1) 把 4 处 `posix.*` cimport 收敛到一个集中映射层（`libcport`），用 **C 预处理器 + `cdef extern from *`** 的惯用法实现 — 这是 Cython 官方认可的唯一不依赖已弃用 `IF`/`DEF` 的编译期平台开关，本会话已在真实工具链上编译、链接、运行验证通过；(2) 测试套件的 POSIX 外壳依赖比 W9 估计的更小也更集中 — 两个 `*FetchTestUtils.py` 只被 bench 文件引用（D2-11 已排除），真正的收集期内阻塞是 `PileupTestUtils`、`samtools_test` 的外部 samtools oracle、`StreamFiledescriptors` 的 `head` 管道、`conftest` 的 REF_PATH 分隔符 + multiprocessing，以及 `make_data_files`（已在真机复现 FileNotFoundError）；(3) 三个审计各有实锤：`off_t` 在 Windows 上是 32-bit 而 htslib 按 `_FILE_OFFSET_BITS 64` 编译成 64-bit（真实 ABI 缺口）；`libcutils.pyx:352` 与 `libctabix.pyx:832` 的 raw `c_open` 缺 `O_BINARY`（本会话实证 300 字节读成 250 字节）；CJK 路径在 ACP=936 的机器上必然失败（pysam 全部经 `os.fsencode` 产 UTF-8 字节，而 htslib 的窄字符 `open` 按 ANSI 解释，htslib 无任何宽字符支持）。

两个项目文档里的研究缺口假设被**证伪**：安装的 Cython 是 **3.3.0**（非 3.1），且 **`libc.msvcrt` 与 `libc.io` 两个 cimport 目标根本不存在**于 Cython 3.3.0 的 Includes（`ls` + `find` 实证）— 映射必须在项目自有的 pxd/C header 里手写。另外发现 W2 清单漏了第 4 处 cimport：`pysam/libchtslib.pxd:7` 的 `from posix.types cimport off_t`。Phase 1 已顺手修掉了 W3（`/dev/null` → `os.devnull`，见 `libcutils.pyx:383,390` 现状引用），D2-02 实际上是"已完成"状态，规划时应按验证关闭处理。

**Primary recommendation:** 建 `pysam/libcport.pxd`（`cdef extern from *` 内联 C 映射到 `_dup/_open/_read/_close` + `_O_*` 常量，Windows 侧强制 `| _O_BINARY` 并把 pmode 掩码为 `_S_IREAD|_S_IWRITE`）+ 可选的 `off_t` 64-bit 平台 typedef；三个 .pyx 只改 cimport 行。测试侧：`make_data_files` 加 Windows 分支调 Python 生成器（复用 `check_samtools_view_equal` 已有的 in-process 模式），`PileupTestUtils`/`samtools_test`/`StreamFiledescriptors`/`testSAMFromStringIO` 改写为 in-process 对比，conftest 改 `os.pathsep` + threading HTTP server，最后跑全量套件对 4 个上游失败做 root-cause-first 处置。

<user_constraints>
## User Constraints (from CONTEXT.md)

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

### Deferred Ideas (OUT OF SCOPE)
- TEST-02 baseline/threshold deep-design (where Linux baseline numbers come from, exact skip-diff threshold) — deselected from discussion; planner/researcher discretion within D2-07 discipline.
- Bench-file (`*_bench.py`) Windows porting — excluded from "green" (D2-11); revisit only if Phase 4 CI wants perf signals.
- Remote-I/O tests beyond documented skips — v2 scope (libcurl deferred).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PORT-01 | POSIX 依赖清除 — `posix.unistd`/`posix.fcntl` cimport、硬编码 `/dev/null`、fork/signal 等 POSIX-only 路径全部消除或条件化 | Complete symbol inventory (4 cimport sites incl. the W2-missed `libchtslib.pxd:7`); verified libcport idiom; W3 already fixed by Phase 1 (needs only verification closure); fork/signal grep = zero hits in Cython layer |
| PORT-02 | 二进制模式审计 — 所有文件 I/O 强制 `O_BINARY`/`"b"`，防止 `\r\n` 翻译静默损坏 BAM/BGZF | Two live bugs found (`libcutils.pyx:352`, `libctabix.pyx:832`); htslib layer already O_BINARY-safe (hfile.c:766-793); corruption reproduced empirically (300→250 bytes); regression-test building blocks (`checkBinaryEqual`) confirmed Windows-safe |
| PORT-03 | LLP64 类型审计 — `long` 截断与类型宽度检查（用 `compile_test.py` 做本地化工具，而非跳过） | Real off_t ABI gap found (32-bit Cython decl vs 64-bit htslib build, include-order evidence); compile_test.py current assertions read; static-assert delivery mechanism identified (pyximport + `cdef extern from *`) |
| PORT-04 | 非 ASCII 路径适配 — 宽字符 API shim + CJK 文件名金丝雀测试 | Full causal chain verified: `os.fsencode`→UTF-8 bytes vs msvcrt narrow `open`→ACP 936; htslib has zero wide-char code; fix point = `hopen_fd`/hfile.c; canary surface mapped (all file modules funnel through `encode_filename`) |
| TEST-01 | 测试全绿 — 完整测试套件在 Windows 通过（含 POSIX shell 调用移植、make 数据生成替代、spawn 安全 conftest） | Corrected W9 inventory (FetchTestUtils = bench-only); exact blocker list with file:line; make_data_files failure reproduced; in-process comparator pattern already exists in TestUtils; 1028 tests collect cleanly today |
| TEST-02 | 测试数对账 — 收集数与 Linux 基线 skip-parity 对账 | 1028 Windows collection count established; expected skip-delta surface quantified (5 libcurl gates / 3 files); #1274's 958 is NOT comparable (older pysam) — fork CI ubuntu job recommended as baseline source |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Platform-mapped fd I/O symbols (dup/open/read/close, O_* flags) | Cython/C seam (`pysam/libcport.pxd` + inline C) | C preprocessor | The mapping is a *compile-time C* concern (Cython maintainer guidance: platform adaptation "should be handled at C compile time"); Cython-level `IF` is deprecated |
| Binary-mode enforcement on raw fd opens | libcport layer (Windows `| _O_BINARY`) | htslib (already does it: hfile.c) | Single choke point beats per-call-site auditing; htslib layer already safe, the two raw `c_open` sites are the residual |
| off_t width consistency | libcport typedef | Phase 3 MSVC config | The pxd must publish the width htslib was *compiled* with (64-bit via `_FILE_OFFSET_BITS 64`), not the header default |
| CJK/wide-char filename open | htslib C layer (`hopen_fd` patch) | pysam `encode_filename` (already UTF-8) | Only the C open layer can call `_wopen`; the Python side already produces UTF-8 per PEP 529 |
| Test comparison oracle | in-process pysam dispatch | pure-Python read-back | External samtools/bcftools do not exist in the env (verified); `check_samtools_view_equal` already demonstrates the pattern |
| Test-data generation | Python generators behind `make_data_files()` | POSIX Makefile (unchanged, authoritative on POSIX) | D2-06 locked; platform dispatch point already exists (TestUtils.make_data_files) |
| Spawn safety / REF_PATH | conftest.py | — | Session fixture + report header are the only cross-cutting test-config points |
| Linux baseline numbers | fork CI (ubuntu job) | — | Zero-setup, already runs on every push (D-11); upstream #1274's log is a different pysam version |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Cython | **3.3.0** (installed, system-site-packages; `pyproject.toml` pins `Cython>=3,<4`) | Compile .pyx → C | Already the project's compiler; version **verified by import this session** — note: project docs assumed "3.1"; the installed reality is 3.3.0 |
| pytest | **9.1.1** (installed into `_venv` during this research) | Test runner | Suite's existing runner; `setup.cfg [tool:pytest]` config |
| CPython (UCRT64 pacman) | **3.14.7** | Runtime | Phase 1 D-01 lock |
| GCC (UCRT64) | 16.2.0 | C compilation | Phase 1 environment |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pysam.samtools.*` / `pysam.bcftools.*` dispatch | in-tree (`_pysam_dispatch`) | In-process test oracle + data generator | Every rewrite of external-samtools comparisons (D2-05/D2-06) |
| `pysam.tabix_compress` / `pysam.tabix_index` | `pysam/libctabix.pyx:802/857` | BGZF compression + tabix indexing in Python generators | tabix_data/cbcf_data generation |
| stdlib `gzip`/`shutil`/`tempfile`/`threading`/`http.server` | stdlib | Generator + conftest rewrites | everywhere; no new deps allowed |
| `checkBinaryEqual`/`checkGZBinaryEqual` | `tests/TestUtils.py:54-92` | Byte-equality regression assertions (D2-08) | Already pure-Python, Windows-safe |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `cdef extern from *` inline-C mapping | `IF UNAME_SYSNAME` blocks | IF still **works** in 3.3.0 (verified) but emits a deprecation warning and is officially slated for removal; new code must not adopt it [CITED: cython migration guide] |
| `cdef extern from *` inline-C mapping | separate `pysam/libcport.h` C header + plain `cdef extern from "libcport.h"` | Cleaner diffs/reviewability, shareable with C shims (Phase 3 `import/pysam.c` fdopen); costs one extra file. **Both verified-equivalent mechanically** — planner latitude per D2-04 |
| Python data generators | pacman `samtools`/`tabix`/`bcftools`/`make` binaries | Explicitly rejected by D2-05/D2-06; also empirically NONE of these are installed today |
| threading HTTP server in conftest | keep multiprocessing | spawn works on Windows but re-imports conftest in child (slow, fragile under pytest); threading is strictly simpler for a localhost fixture |

**Installation:**
```bash
# nothing new to install — phase works with the existing editable install.
# pytest was installed into the venv during this research (was missing):
/d/Github/pysam/_venv/bin/python.exe -m pip install pytest   # done: pytest 9.1.1
```

**Version verification:** All versions above verified by direct execution in the UCRT64 venv this session (`Cython.__version__`, `pytest.__version__`, `sys.version`, `gcc --version`).

## Package Legitimacy Audit

> This phase installs **no new runtime packages**. The only installation performed was `pytest` into the dev venv (test-only dependency, required by `pyproject.toml test-requires`).

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pytest | PyPI | ~20 yrs | ~30M/mo | github.com/pytest-dev/pytest | OK | Approved (already a project test-requires) |
| Cython | PyPI | ~15 yrs | ~15M/mo | github.com/cython/cython | OK | Approved (existing pinned build dep) |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*No package discovered via WebSearch or training data is recommended by this research — the recommended "stack" is project-internal code plus stdlib.*

## Architecture Patterns

### System Architecture Diagram

```text
Phase 2 change map (arrows = "rewires to")

  .pyx consumers                      centralized mapping layer                C layer
  ┌──────────────────────────┐        ┌────────────────────────────┐      ┌──────────────────────────┐
  │ pysam/libchtslib.pyx:10  │        │ pysam/libcport.pxd         │      │ #ifdef _WIN32            │
  │   dup                    │───────▶│  publishes:                │─────▶│   #include <io.h>        │
  │ pysam/libcutils.pyx:22-23│ cimport│   psam_dup/psam_open2/3/   │      │   #include <fcntl.h>     │
  │   c_open,O_*,c_dup,      │  only  │   psam_read/psam_close,    │      │   psam_dup → _dup        │
  │   SEEK_*, STDOUT_FILENO  │        │   PSAM_O_RDONLY/...,       │      │   psam_open → _open      │
  │ pysam/libctabix.pyx:62-63│        │   PSAM_STDOUT_FILENO,      │      │   flags |= _O_BINARY     │
  │   c_open,O_RDONLY,       │        │   psam_off_t (64-bit win)  │      │ #else                    │
  │   close,dup,read         │        │ (cdef extern from * +      │      │   #include <unistd.h>    │
  │ pysam/libchtslib.pxd:7   │        │  inline C, or libcport.h)  │      │   #include <fcntl.h>     │
  │   off_t (posix.types)    │        └────────────────────────────┘      │   psam_* → POSIX names   │
  └──────────────────────────┘                                            └──────────────────────────┘
        ▲ no IF / no DEF anywhere — switch lives in C preprocessor
        │
        │ (htslib C layer untouched except:)
        ├────────────▶ hfile.c hopen_fd ──(PORT-04 patch)──▶ _wopen via MultiByteToWideChar(CP_UTF8)

  Test layer
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │ setUpModule() ──▶ make_data_files(dir) ──┬─ POSIX: subprocess [make -C dir] (unchanged)│
  │                                          └─ win32:  Python generators (new)            │
  │                                               pysam.samtools.view/index/calmd/mpileup/  │
  │                                               faidx + pysam.bcftools.view/index +      │
  │                                               tabix_compress/tabix_index + gzip/BGZF    │
  │ comparators: check_samtools_view_equal (already in-process) ◀── rewritten PileupTest-  │
  │ Utils / samtools_test / StreamFiledescriptors / testSAMFromStringIO wire in here       │
  │ conftest: httpserver (multiprocessing → threading); REF_PATH ":" → os.pathsep          │
  └───────────────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (delta only)

```
pysam/
├── libcport.pxd          # NEW — centralized fd-I/O mapping (D2-04). pxd-only via inline C,
│                         #   or pxd + libcport.h if planner prefers a real header
├── libcutils.pyx         # cimport lines 22-23 → libcport; :352 add O_BINARY-equivalent flags
├── libctabix.pyx         # cimport lines 62-63 → libcport (:832 read loop becomes binary)
├── libchtslib.pyx        # cimport line 10 → libcport
└── libchtslib.pxd        # line 7 off_t → libcport's psam_off_t (64-bit on win)
tests/
├── conftest.py           # threading httpserver; REF_PATH = os.pathsep
├── TestUtils.py          # make_data_files(): win32 branch → Python generators
├── pysam_data/           # NEW generator module (e.g. make_data.py) — Makefile untouched
├── tabix_data/           # NEW generator (tabix_compress/tabix_index based)
├── cbcf_data/            # NEW generator (bcftools dispatch based)
├── PileupTestUtils.py    # samtoolsshell builders → in-process equivalents
├── samtools_test.py      # run_command/get_version/check_version/check_statement → in-process
├── StreamFiledescriptors_test.py  # head -n200 → sys.executable pipe consumer
└── compile_test.py       # LLP64-size assertions per-platform + static-assert pyx module
```

### Pattern 1: libcport via `cdef extern from *` + C preprocessor (VERIFIED END-TO-END)

**What:** One pxd declares portable `psam_*` names; the inline C block does the platform mapping with `#ifdef`. Consumers change only their cimport lines (`from pysam.libcport cimport psam_dup as dup`).

**When to use:** D2-01/D2-04 — replaces all four `posix.*` cimport sites.

**Why this and not `IF`:** `IF` is deprecated ("The 'IF' statement is deprecated and will be removed in a future Cython version. Consider using runtime conditions or C macros instead") — that exact warning text was reproduced by compiling an `IF` module on our Cython 3.3.0 this session. The official migration guide's sanctioned replacement for platform-specific adaptation is C shims "defined in verbatim C code"; the Cython lead maintainer states it "should be handled at C compile time" [CITED: github.com/cython/cython/issues/4310]. A plain `if UNAME_SYSNAME == "Windows":` **does not compile** ("undeclared name not builtin: UNAME_SYSNAME" — reproduced this session): `UNAME_*` names live only in the IF/DEF compile-time scope (verified in `Cython/Compiler/Scanning.py:89-93`: `names = ('UNAME_SYSNAME', 'UNAME_NODENAME', 'UNAME_RELEASE', 'UNAME_VERSION', 'UNAME_MACHINE')`). The discuss-note phrase "Cython 3.1 plain-if idiom" does not correspond to any working mechanism — treat D2-01's *intent* (compile-time switch, no runtime cost) as locked and this pattern as its implementation.

**Verified prototype (compiled with Cython 3.3.0, linked with UCRT64 gcc 16.2.0, imported and executed: `dup ok: True`):**

```cython
# Source: verified live this session on Cython 3.3.0 / UCRT64; shape follows
# https://cython.readthedocs.io/en/latest/src/userguide/migrating_to_cy30.html (verbatim C shims)
cdef extern from *:
    """
    #ifdef _WIN32
    #include <fcntl.h>
    #include <io.h>
    #define psam_dup _dup
    #define psam_open(path, flags, ...) _open(path, flags, ##__VA_ARGS__)
    #define psam_read _read
    #define psam_close _close
    #define PSAM_STDOUT_FILENO 1
    #else
    #include <fcntl.h>
    #include <unistd.h>
    #define psam_dup dup
    #define psam_open open
    #define psam_read read
    #define psam_close close
    #define PSAM_STDOUT_FILENO STDOUT_FILENO
    #endif
    """
    int psam_dup(int fd)
    int psam_read(int fd, void *buf, size_t count)   # C return int on win / ssize_t on POSIX — declare Py_ssize_t in pxd if you prefer; implicit widening is safe
    int psam_close(int fd)
    int PSAM_STDOUT_FILENO
```

**Variadic-macro caveat (found during verification):** the `##__VA_ARGS__` comma-stripping used above is a GNU extension; MSVC's legacy preprocessor tolerates empty variadics but the conforming `/Zc:preprocessor` mode does not. Since the call sites are fixed-arity today (2-arg at `libctabix.pyx:832`, `libcutils.pyx:383,390`; 3-arg at `libcutils.pyx:352`), the **safer shape is two fixed-arity exports**: `psam_open2(path, flags)` and `psam_open3(path, flags, mode)` — avoids variadic macros entirely and is MSVC-proof for Phase 3. Planner latitude.

**Binary-mode enforcement built in (PORT-02):** on Windows the mapping should force binary — either `#define psam_open2(p,f) _open(p, (f) | _O_BINARY)` or an enum-or at call sites via published `PSAM_O_BINARY`. Empirical proof this matters (this session, UCRT64): a file with 50 `\r\n` pairs written as 300 bytes reads back as **250 bytes** through `_open(path, _O_RDONLY)` (text mode) and **300 bytes** with `_O_BINARY`. `_O_RDONLY` is `0x0000` and `_O_BINARY` is `0x8000` on this toolchain [VERIFIED: /c/msys64/ucrt64/include/fcntl.h:12,20] — plain `O_RDONLY` carries no binary bit.

**pmode masking (forward-compat):** MS docs state `_open`'s `pmode` accepts only `_S_IREAD|_S_IWRITE` combinations; other values "generate an assertion in Debug mode and invoke the invalid parameter handler" [CITED: learn.microsoft.com _open]. pysam passes `0o666` (= 0x1B6, extra bits beyond 0x180). Release UCRT empirically accepts `0o666` (verified: `_open` returned a valid fd), but masking in the Windows mapping (`mode & 0x180`) is cheap insurance for MSVC/debug CRT in Phase 3.

### Pattern 2: off_t width must follow htslib's compile, not the header default (PORT-03)

**What:** publish a platform-typed `psam_off_t` from libcport and use it in `libchtslib.pxd` signatures.

**Evidence chain (all read this session):**
- `htslib/config.h:218`: `#define _FILE_OFFSET_BITS 64` — htslib objects are compiled with LFS.
- Probe compiled on UCRT64: plain `sizeof(off_t)` = **4**; with `#define _FILE_OFFSET_BITS 64` before includes = **8**.
- Generated `pysam/libchtslib.c`: `#include <sys/types.h>` at line **1370** precedes `#include "htslib/hts.h"` at line **1376** — so the Cython TU sees the 32-bit `off_t` while htslib's compiled functions use 64-bit.
- `Cython/Includes/posix/types.pxd:23` declares `ctypedef long off_t` — `long` is 32-bit on LLP64 Windows (and this is the declaration the pxd currently cimports at `libchtslib.pxd:7`).

**Consequence today:** value truncation (not frame corruption) on `hseek`/`htell`/`bgzf_utell`/`cram_*` offsets above 2 GiB; invisible to the current test corpus (small files), which is exactly why it belongs in PORT-03 rather than being dismissed. On Linux LP64 both declarations are 8-byte, so a fix is zero-regression-safe.

**Fix shape:** in libcport's inline C — `#ifdef _WIN32 typedef long long psam_off_t; #else typedef off_t psam_off_t; #endif` (mingw's `_off64_t` is `long long`-compatible; the caller-side conversions then match htslib's 64-bit ABI). Verify with the D2-09 static asserts.

### Pattern 3: In-process comparison oracle (D2-05)

**What:** all external-`samtools`/`bcftools` oracle calls become `pysam.samtools.*`/`pysam.bcftools.*` dispatch calls.

**Already-existing proof point** — `tests/TestUtils.py:106-107`:
```python
    lines1 = pysam.samtools.view(*(args + [filename1]))
    lines2 = pysam.samtools.view(*(args + [filename2]))
```
`check_samtools_view_equal` has been in-process all along; W9's fear that it shells out is outdated. The rewrites extend this same pattern. **Weakening to acknowledge in the plan:** when both sides of a comparison become pysam dispatch, the oracle no longer catches bundled-samtools-vs-upstream-samtools drift — the fork-CI ubuntu job (which installs external samtools and runs the original comparisons) becomes the place that still exercises the external oracle on POSIX, which is precisely how zero-regression + oracle coverage are both preserved.

### Pattern 4: Python test-data generators behind make_data_files (D2-06)

**What:** `make_data_files()` gains a win32 branch that calls per-directory Python generators; Makefiles and the POSIX branch remain byte-for-byte untouched.

**Verified dispatch surface for the generators:**

| Makefile operation (POSIX) | Python replacement | Notes |
|---|---|---|
| `samtools view -bo out.bam in.sam` | `pysam.samtools.view("-b", "-o", out, "-t"?, in)` / `AlignmentFile` write loop | mirrors `%.bam: %.sam` rule |
| `samtools index x.bam` / `index -c` | `pysam.samtools.index(...)` | .bai / .csi |
| `samtools view -C -T ex1.fa` | `pysam.samtools.view("-C", "-T", ...)` | CRAM |
| `samtools calmd` | `pysam.samtools.calmd(...)` | `with_md.bam` |
| `samtools mpileup \| gzip` | `pysam.samtools.mpileup(...)` + `gzip` module | `ex1.pileup.gz` |
| `samtools faidx` | `pysam.samtools.faidx(...)` | .fai/.gzi |
| `bgzip < in > out` | `pysam.tabix_compress(in, out)` (`libctabix.pyx:802`) | note: its raw read loop is PORT-02 item #2 |
| `tabix -f -p vcf/bed/gff/sam` | `pysam.tabix_index(fn, preset=...)` (`libctabix.pyx:857`) | .tbi |
| `bcftools view -O b` / `bcftools index -f` | `pysam.bcftools.view("-O","b",...)` / `pysam.bcftools.index(...)` | .bcf / .csi |
| `gunzip` / `gzip` | stdlib `gzip`/`shutil` | |
| `dd bs=$(($(wc -c < ex2.bam)-512))` | pure-Python `open(rb); truncate(len-512)` | `ex2_truncated.bam` |
| `(bgzip -d < in; printf '\37\0\0\0\1\0\0\0') \| bgzip` | read BAM via `BGZFile`/gzip → append 8 bytes `b'\x1f\0\0\0\x01\0\0\0'` → re-BGZF | `ex2_corrupt.bam` |
| `grep "^@" \| samtools view -bo - -` | filter header lines in Python, write empty BAM via `AlignmentFile(header_from=...)` | `empty.bam` |
| `$(shell samtools view '-?')` NO_PG probe | pass `"--no-PG"` unconditionally in generators (bundled samtools supports it) | keeps generated headers deterministic |

**Committed inputs (generators read these, never regenerate them):** `pysam_data`: `ex1.sam.gz`, `ex1.fa`, `ex1.bed`, `ex1.vcf.gz(+.tbi)`, `ex10.sam`, `ex3-8.sam`, `ex9_fail.sam`, `ex9_nofail.sam`, `ex_spliced.sam`, `example_*.sam` (git ls-files verified); `tabix_data`: `example.bed`, `*.gz` inputs; `cbcf_data`: `*.vcf` inputs.

### Pattern 5: conftest spawn-safety + REF_PATH (read fully this session)

`tests/conftest.py:35-45` — `multiprocessing.Pipe(duplex=False)` + `multiprocessing.Process(target=_httpd, ...)`. On Windows the default start method is spawn; `_httpd` is module-level so pickling by reference *should* work, but the child re-imports conftest under pytest's import machinery — slow and fragile. Threading rewrite is a strict simplification (server is a daemon `serve_forever` loop; no CPU-shared state).

`tests/conftest.py:53` — `os.environ["REF_PATH"] = ":"`. htslib's separator is compile-time platform-switched — `htslib/htslib/hts.h:44-51`:
```c
// Separator used to split HTS_PATH (for plugins); REF_PATH (cram references)
#if defined(_WIN32) || defined(__MSYS__)
#define HTS_PATH_SEPARATOR_CHAR ';'
...
#else
#define HTS_PATH_SEPARATOR_CHAR ':'
```
so on Windows `":"` is a single bogus entry, not "empty element list". Fix: `os.environ["REF_PATH"] = os.pathsep` (Python's os.pathsep is `;` on Windows — matches HTS_PATH_SEPARATOR on `_WIN32`). This only matters once CRAM tests run (they need generated .cram + ref files) — currently unreachable because data generation fails first.

### Anti-Patterns to Avoid

- **Writing new `IF UNAME_SYSNAME` blocks** — deprecated, warns on every build, removal scheduled; the inline-C mapping replaces it at zero runtime cost.
- **Fixing O_BINARY per call-site by hand-spelling `_O_BINARY` in .pyx files** — spreads platform conditionals across consumers; the flag belongs inside libcport's Windows mapping (single point, D2-04's locked property).
- **Making the Linux `make` path call the Python generators** — D2-06 requires the Makefiles stay authoritative on POSIX unless byte-identity is proven; don't "unify" by weakening the POSIX side.
- **`check_version` keeping its external-binary probe** — `samtools_test.py:137-152` calls `get_version(self.executable)` in an **autouse** fixture; with no external samtools on Windows it raises (Popen+shell on a missing binary yields garbage stderr → `ValueError("could not get version...")`), poisoning every TestSamtools test. Gate or rewrite it, don't leave it.
- **Silent skips to make the suite green** — D2-07's exemption-list discipline; every new skip needs a written reason in the phase doc.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| BGZF compression in generators | custom gzip framing | `pysam.tabix_compress` / `BGZFile` | BGZF block structure, EOF marker, index compatibility are already correct in-tree |
| SAM/BAM/CRAM conversion in generators | hand-writing BAM records | `pysam.samtools.view` dispatch | the dispatch exercises the same bundled samtools the tests compare against |
| Line-count / column-extract oracles (wc/cut/awk) | subprocess shims | Python iteration over `pysam.samtools.view(...)` output | `AlignmentFileFetchTestUtils`' `*_with_pysam` builders already show the shape |
| The `head -n200` pipe consumer | cmd.exe tricks | `subprocess.Popen([sys.executable, "-c", ...])` reading 200 lines | keeps a *real* subprocess + fd pipe (the test's purpose: fd-based streaming) with zero external tool |
| UTF-8→UTF-16 filename conversion in Python | encoding gymnastics before `open()` | one C-level `_wopen` mapping in hfile.c | Python already hands over correct UTF-8 bytes (`os.fsencode`); only the C side misinterprets them |

**Key insight:** every piece of machinery this phase needs (in-process dispatch oracle, byte-compare helpers, idempotent data-gen entry point, BGZF writer) already exists in-tree; the phase is rewiring, not invention.

## Common Pitfalls

### Pitfall 1: Text-mode raw `open()` silently corrupts binary reads
**What goes wrong:** `\r\n` → `\n` translation on read (and `\n` → `\r\n` on write) at the CRT fd layer.
**Why it happens:** Windows CRT defaults narrow-char `open()` to text mode; `_O_RDONLY` is `0x0000` so it carries no binary bit.
**How to avoid:** route every raw fd open through libcport which ORs `_O_BINARY` (`0x8000`) on Windows.
**Warning signs / proof (this session):** 300-byte file with 50 CRLF pairs → `_open(O_RDONLY)` read **250** bytes, `_O_BINARY` read 300. Live sites: `libctabix.pyx:832` (`fd_src = c_open(fn, O_RDONLY)` — the tabix_compress copy loop) and `libcutils.pyx:352` (`c_open(stdout_f_bytes, O_WRONLY|O_CREAT|O_TRUNC, 0o666)` — the `save_stdout` dispatch path). tempfile.mkstemp fds are already binary (Python adds O_BINARY on Windows), so the mkstemp-based dispatch paths are safe; only these two raw `c_open` sites + htslib (already safe) complete the audit.

### Pitfall 2: Stale compiled artifacts after editing .pyx (brownfield rebuild discipline)
**What goes wrong:** editing `libcutils.pyx` etc. shows no effect, or the suite tests old code.
**Why it happens:** the editable install's built `.pyd`s and the checked-in generated `.c` files don't auto-refresh from a `setup.py build` you didn't run.
**How to avoid:** after each libcport-touching commit, `pip install -e .` (or `python setup.py build_ext --inplace`) **inside the UCRT64 shell**, then `devtools/smoke_test.py` before the suite. The generated `.c` files are committed by this repo's workflow (they exist in `pysam/` today) — keep regenerating them, they are part of the diff.

### Pitfall 3: Running pytest from Git Bash instead of the UCRT64 shell
**What goes wrong:** gcc inside pyximport/compile_test fails with `cannot execute 'cc1'` (reproduced this session when a build was attempted from Git Bash).
**Why it happens:** MSYS2 gcc resolves its internal subprograms via the shell environment; Git Bash has a different `/usr`.
**How to avoid:** all Phase 2 commands run via `MSYSTEM=UCRT64 CHERE_INVOKING=1 /c/msys64/usr/bin/bash.exe -lc '...'` (the Phase 1 environment contract D-01).

### Pitfall 4: comparing collection counts across pysam versions (TEST-02)
**What goes wrong:** "958 vs 1028" looks like 70 missing tests.
**Why it happens:** upstream #1274's 958 was an older pysam; this fork collects **1028** on Windows today (verified: `1028 tests collected in 2.46s`, zero collection errors).
**How to avoid:** baseline = the fork CI **ubuntu job on the same commit** (`PYTHONPATH=build pytest` per ci.yaml), compared per test-session summary line (collected/passed/failed/skipped) with `-rs` skip reasons attached. Artifact: a small reconciliation table committed to the phase dir.

### Pitfall 5: bench files dragging POSIX utils into scope
**What goes wrong:** "fixing" `AlignmentFileFetchTestUtils`/`VariantFileFetchTestUtils`/bench shell pipelines that pytest never collects.
**Why it happens:** pytest's default `python_files` (`test_*.py`, `*_test.py`) does not match `*_bench.py` — the shell-heavy utils are imported **only** by bench files (verified by grep: consumers are `AlignmentFileFetch_bench.py`, `AlignmentFilePileup_bench.py`, `VariantFile_bench.py` — plus `AlignmentFilePileup_test.py` importing `PileupTestUtils`, which IS collected).
**How to avoid:** scope TEST-01 to the collected set; note the bench utils in the D2-03/D2-11 documentation as deliberately out of scope.

### Pitfall 6: `check_version`/`get_version` external-binary probes
Covered in Anti-Patterns — autouse fixture + missing binary = whole-class failure that looks like a portability bug but is an environment assumption. Rewrite as `pysam.__samtools_version__` self-check or gate behind `shutil.which`.

## Code Examples

### libcport consumer rewiring (exact current lines → new lines)

Current (verbatim, `pysam/libcutils.pyx:22-23`):
```cython
from posix.fcntl cimport open as c_open, O_WRONLY, O_CREAT, O_TRUNC
from posix.unistd cimport dup as c_dup, SEEK_SET, SEEK_CUR, SEEK_END, STDOUT_FILENO
```
New:
```cython
from pysam.libcport cimport psam_open2 as c_open2, psam_open3 as c_open3
from pysam.libcport cimport PSAM_O_WRONLY as O_WRONLY, PSAM_O_CREAT as O_CREAT, PSAM_O_TRUNC as O_TRUNC
from pysam.libcport cimport psam_dup as c_dup, PSAM_STDOUT_FILENO as STDOUT_FILENO
from libc.stdio cimport SEEK_SET, SEEK_CUR, SEEK_END   # C-standard (stdio.h); Cython libc.stdio declares SEEK_SET (Includes/libc/stdio.pxd:44)
```
(The `SEEK_*` switch to `libc.stdio` is a strict improvement: they are ISO-C stdio.h constants on every platform including MSVC, removing three POSIX cimports for free.)

Current (verbatim, `pysam/libctabix.pyx:62-63`):
```cython
from posix.fcntl cimport open as c_open, O_RDONLY
from posix.unistd cimport close, dup, read
```
Current (verbatim, `pysam/libchtslib.pyx:10`):
```cython
from posix.unistd cimport dup
```
Current (verbatim, `pysam/libchtslib.pxd:7`):
```cython
from posix.types cimport off_t
```
New for all four: analogous `from pysam.libcport cimport ...` lines; `off_t` → `psam_off_t` (Pattern 2). Line 111-112 of libchtslib.pxd then read `psam_off_t hseek(hFILE *fp, psam_off_t offset, int whence)` etc.

### conftest fixes (current verbatim, `tests/conftest.py:35-45,53`)
```python
@pytest.fixture(scope="session")
def httpserver():
    rconn, wconn = multiprocessing.Pipe(duplex=False)
    process = multiprocessing.Process(target=_httpd, args=[wconn, Path(__file__).parent], name="httpd", daemon=True)
    ...
os.environ["REF_PATH"] = ":"
```
New shape:
```python
@pytest.fixture(scope="session")
def httpserver():
    # threading rewrite: same _httpd body minus the Pipe handshake —
    # start QuietHTTPServer in a daemon thread, read server.server_port directly
os.environ["REF_PATH"] = os.pathsep   # ';' on win32 == HTS_PATH_SEPARATOR (hts.h:46)
```

### make_data_files win32 branch (current verbatim, `tests/TestUtils.py:168,181`)
```python
    make = os.environ.get('MAKE', 'make')
    ...
        subprocess.check_output([make, '-C', directory], stderr=subprocess.STDOUT, encoding='ascii')
```
New shape:
```python
    if sys.platform == 'win32':
        from make_data import generate           # tests/<datadir>/make_data.py
        generate(directory)
    else:
        subprocess.check_output([make, '-C', directory], ...)
```
(The current code's `except CalledProcessError` does NOT catch the Windows `FileNotFoundError` from the missing `make` — reproduced this session; the win32 branch must sit *before* make is ever invoked.)

### D2-09 static asserts via pyximport (compile_test.py already installs pyximport)
```cython
# tests/_compile_sizes.pyx — compiled by existing pyximport machinery in compile_test.py
cdef extern from *:
    """
    #include "htslib/hts.h"
    _Static_assert(sizeof(hts_pos_t) == 8, "hts_pos_t must be 64-bit");
    _Static_assert(sizeof(long long) >= 8, "64-bit scalar expected on LLP64");
    """
def check():
    return True
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `IF UNAME_SYSNAME` / `DEF` conditional compilation | C preprocessor via `cdef extern from *` verbatim C (or C shim header); runtime conditions for Python-level branching | Deprecated Cython 3.0 (2023); still functional with warning in 3.3.0 | New platform switches must be C-level; pysam's four cimport sites get one centralized C-level switch |
| `from posix.unistd/fcntl/types cimport ...` | project-local portable pxd (libcport) publishing `_`-prefixed CRT names on Windows | this phase | `libc.msvcrt` was assumed available — falsified: Cython 3.3.0 ships no `libc/msvcrt.pxd` and never shipped `libc.io` (directory listing verified) |
| Windows ANSI (ACP) file APIs in Python | UTF-8 filesystem encoding, `*W` APIs | Python 3.6, PEP 529 | pysam's UTF-8 bytes are correct; the residual mismatch is C-side narrow `open` — htslib needs the `_wopen` shim (PORT-04) |

**Deprecated/outdated:**
- `IF`/`DEF`: deprecated; "It will not be removed in Cython 3.1, but continue to be available for another couple of release series" [CITED: github.com/cython/cython/issues/4310] — no urgency to purge from third-party code, but do not add.
- Project-doc assumption "`libc.msvcrt`/`libc.io` 精确映射": falsified for Cython 3.3.0 — neither exists as a cimport target; hand-declare in libcport.
- W3 (`/dev/null`): already fixed in Phase 1 — current code (verbatim, `libcutils.pyx:383` and `:390`): `stdout_h = c_open(force_bytes(os.devnull), O_WRONLY)`. D2-02 should close via verification + regression coverage, not re-implementation (and note `os.devnull` is `"NUL"` on Windows — the platform-conditional constant the decision asked for, arrived at via stdlib).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TestLogging ×3 failures root cause — hypotheses: (a) C-level stderr/fd state vs Python FileHandler interplay during pileup; (b) different htslib warning behavior on Windows for `ex9_fail.bam`; (c) generation-corrupted ex9 data on the contributor's machine. No htslib→Python logging bridge exists (grep of `htslib_util.c`/`libchtslib.pyx` empty), so the FileHandler itself is likely incidental. | Known failures | Wasted fix time; mitigated by D2-07's reproduce-first protocol |
| A2 | `testReadingFromFileWithoutIndex` failure — hypotheses: exception-type mismatch (pysam raises IOError/OSError instead of ValueError when index missing on Windows), or `until_eof` count off due to data generation. Test body read (`AlignmentFile_test.py:604-611`): expects `ValueError` then 3270 reads. | Known failures | Same — in-phase reproduction decides |
| A3 | MSVC forward-compat of the libcport mapping (underscore names, `sys/types.h` off_t) — cited from Microsoft docs and mingw headers, but never compiled with MSVC in this session | libcport design | Phase 3 discovery; design already minimizes exposure (fixed-arity, masked pmode, C-preprocessor switch) |
| A4 | Python maps Windows `ERROR_BROKEN_PIPE` to `errno.EPIPE` so `StreamFiledescriptors_test.py:25`'s check is cross-platform | Pitfalls | If wrong: minor test-local fix |
| A5 | `tempfile.mkstemp` fds are binary-mode on Windows (Python adds O_BINARY in `_bin_openflags`) | PORT-02 audit | If wrong: dispatch temp paths corrupt; would surface immediately in D2-08 regression tests |
| A6 | Upstream #1274's 958-test count is from an older pysam and unusable as our baseline — fork CI ubuntu job used instead | TEST-02 | If wrong: only affects baseline choice, not green-ness |
| A7 | PORT-04 fix shape = UTF-8→UTF-16 conversion at `hopen_fd` (MultiByteToWideChar + `_wopen`) in htslib hfile.c | PORT-04 | Alternative shapes (e.g. `SetConsoleOutputCP`-style ACP override, app manifest UTF-8) exist but are process-global and worse; validate the patch compiles/passes the canary in-phase |
| A8 | `#1274`'s environment had external samtools installed for data generation (their Makefile path) — our D2-06 generators make this irrelevant either way | Test porting | None |

## Open Questions (RESOLVED)

All four questions are resolved by the phase plan set (02-01..02-04); per-question resolutions below point at the adopting plan task.

1. **TestLogging ×3 + testReadingFromFileWithoutIndex actual failure modes on OUR build**
   - What we know: test bodies fully read; environment differs from #1274 (Python 3.14.7 vs 3.11, our toolchain, our data generation).
   - What's unclear: whether they even reproduce here.
   - Recommendation: plan an explicit early "reproduce & triage" task for the 4 names before any skip/exempt decisions (D2-07 order).
   - **Resolution:** adopted — 02-04 Task 1 is the reproduce-first triage task (all four names run with -v before any fix/skip/exempt decision; the recorded baseline decides the disposition).

2. **TEST-02 threshold mechanics** (planner discretion per deferred idea)
   - What we know: Windows collects 1028; expected skip-delta = libcurl-gated tests (5 skipif sites across AlignmentFile/faidx/tabix tests) + any D2-07 exemptions; hard skips (`test_reading_writing_cram`, `test_samtools_processing`, linking env-gate, tty-gated usage tests) exist on BOTH platforms → zero delta.
   - Recommendation: artifact = per-session `{collected, passed, failed, skipped}` + `-rs` reasons table, Windows vs fork-CI-ubuntu on same commit; threshold = "every skip difference individually named with a reason" (stricter and simpler than a numeric budget).
   - **Resolution:** adopted verbatim — 02-04 Task 3 fixes these mechanics (baseline = fork CI ubuntu job on the phase-final SHA; threshold = zero unexplained skip differences).

3. **Generator byte-fidelity for `ex2_corrupt.bam` / `ex2_truncated.bam`**
   - What we know: POSIX rules use bgzip/dd/printf pipelines; Python equivalents exist but BGZF block boundaries of `pysam.tabix_compress` vs `bgzip` binary may differ (tests consuming these files read them, not byte-compare them — check consumers during implementation).
   - **Resolution:** carried as a flagged assumption of 02-03 Task 1 — consumers are read-based, so block-boundary drift is acceptable; consumers are verified in-phase and the result recorded in the SUMMARY.

4. **Whether `libchtslib.pxd`'s `off_t`→`psam_off_t` rename ripples into other pxd consumers**
   - What we know: `grep off_t` in `.pxd` shows signatures only in `libchtslib.pxd`; `.pyx` files don't cimport off_t directly.
   - Recommendation: keep `libcport` exporting the name `off_t` (aliased) so consumer diffs stay one-line.
   - **Resolution:** adopted — 02-01 Task 2 rewires via `cimport psam_off_t as off_t` (the alias keeps the consumer diff one-line; the grep evidence shows no other pxd consumer to ripple into).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| UCRT64 shell (MSYSTEM=UCRT64) | everything | ✓ | MSYS2 at C:/msys64 | — (hard requirement, D-01) |
| pacman python + `_venv` (system-site-packages) | runtime | ✓ | 3.14.7 | — |
| Cython | rebuilds | ✓ | 3.3.0 | — |
| gcc | rebuilds, pyximport | ✓ | 16.2.0 (UCRT64) | — |
| pytest | TEST-01/02 | ✓ (installed during this research; **was missing**) | 9.1.1 | — |
| external `samtools`/`bcftools`/`tabix` | nothing (D2-05 forbids) | ✗ (not installed — desired state) | — | in-process dispatch |
| `make` (POSIX) | POSIX data-gen branch only | ✗ on Windows (verified) | — | Python generators (D2-06) |
| `mingw32-make` | not used by design | ✓ | ucrt64 package | — (unused) |
| llvm-nm symbol gate | rebuild parity (Phase 1 D-16) | ✓ (per Phase 1) | — | — |
| editable pysam install | suite under test | ✓ | 0.24.1 (`import pysam` verified) | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** `make` + external toolchain on Windows — by design, replaced by D2-06 generators and D2-05 in-process comparators.

## Security Domain

`security_enforcement: true`, ASVS level 1. Phase 2 is a porting/testing phase on a local dev toolchain; no new external input surfaces are introduced.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | none (no auth surface) |
| V3 Session Management | no | none |
| V4 Access Control | no | none (local test files only) |
| V5 Input Validation | marginally | test data generators consume committed fixture files only; no untrusted input paths added. conftest HTTP server binds localhost ephemeral port only (existing design, preserved in threading rewrite) |
| V6 Cryptography | no | none |
| V10 Malicious Code | watch item | D2-06 generators + libcport inline C are new code executing at build/test time — keep them free of network calls and shell execution (they replace shell execution, reducing the existing `shell=True` surface: `samtools_test.py:25,36` and the utils' `os.popen/os.system` disappear — a net security improvement) |

### Known Threat Patterns for this phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `shell=True` subprocess with format-string commands (existing) | Tampering/Elevation | D2-05 rewrite removes them entirely (list-form / in-process); keep zero shell interpolation in new code |
| Inline C in pxd (`cdef extern from *`) executing at build time | Tampering | same review standards as any C diff; no network/filesystem side effects in the mapping block |
| Test HTTP server exposure | Information Disclosure | bind `("localhost", 0)` (existing `QuietHTTPServer` design — keep verbatim in threading rewrite) |

## Sources

### Primary (HIGH confidence — read or executed this session)
- `pysam/libcutils.pyx:22-23,140-144,352,383-390` — posix cimports, encode_filename, raw c_open sites (quoted verbatim above)
- `pysam/libctabix.pyx:62-63,802,832-852,857,1035` — cimports, tabix_compress/index, read loop
- `pysam/libchtslib.pyx:10,110,567` and `pysam/libchtslib.pxd:7,111-112` — dup usage, off_t declarations
- `pysam/libcbcf.pyx:144-145,4927` — VariantFile funnels through encode_filename
- `tests/TestUtils.py` (full read), `tests/conftest.py` (full read), `tests/samtools_test.py:22-44,114,137-260`, `tests/StreamFiledescriptors_test.py` (full read), `tests/linking_test.py` (full read), `tests/compile_test.py` (full read), `tests/_compile_test.pyx`, `tests/AlignmentFile_test.py:254-264,604-611,1746-1787`
- `tests/pysam_data/Makefile`, `tests/tabix_data/Makefile`, `tests/cbcf_data/Makefile` (full reads)
- `htslib/htslib/hts.h:44-51`, `htslib/config.h:218`, `htslib/hfile.c:30-50,530-600,755-798` (O_BINARY enforcement), `htslib/htslib/hts.h:798-802` (hts_pos_t)
- Cython 3.3.0 compiler internals: `Cython/Compiler/Parsing.py:2544-2559` (IF/DEF deprecation warnings verbatim), `Cython/Compiler/Scanning.py:89-93` (compile-time env names); `Cython/Includes/libc/` + `Cython/Includes/posix/` listings (no msvcrt.pxd, no libc/io; fcntl.pxd/unistd.pxd/types.pxd contents)
- `/c/msys64/ucrt64/include/io.h:105-124,172` (`_close/_dup/_isatty/_read/_open` declarations), `/c/msys64/ucrt64/include/fcntl.h:12-39` (`_O_RDONLY 0x0000`, `_O_WRONLY 0x0001`, `_O_CREAT 0x0100`, `_O_TRUNC 0x0200`, `_O_TEXT 0x4000`, `_O_BINARY 0x8000`, `O_WRONLY _O_WRONLY`, `O_CREAT _O_CREAT` …)
- Generated `pysam/libchtslib.c:1370-1376` (include order), generated `pysam/*.c` presence
- Empirical builds/runs this session: IF module (works+warns), plain-if module (fails: "undeclared name not builtin: UNAME_SYSNAME"), extern-from-star dup module (**works, `dup ok: True`**), text-vs-binary read probe (**250 vs 300 bytes**), `_open` pmode probe (0o666 accepted on release UCRT), off_t probes (**4 / 8 bytes**), pytest collection (**1028 tests**), make_data_files probe (**FileNotFoundError**), `GetACP()=936`, `sys.getfilesystemencoding()='utf-8'`

### Secondary (MEDIUM confidence — official docs fetched)
- [Cython — Migrating from Cython 0.29 to 3.0](https://cython.readthedocs.io/en/latest/src/userguide/migrating_to_cy30.html) — IF/DEF deprecation + sanctioned replacements (verbatim C shims, runtime conditions)
- [cython/cython#4310](https://github.com/cython/cython/issues/4310) — removal plan, "handled at C compile time", not removed in 3.1
- [PEP 529](https://peps.python.org/pep-0529/) — Windows UTF-8 filesystem encoding, `*W` APIs, legacy opt-out
- [Microsoft Learn — _open/_wopen](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/open-wopen) — signatures, `_O_*` constants, pmode validation rules, `_wopen` wide variant

### Tertiary (LOW confidence)
- History of `libc.msvcrt.pxd` removal from Cython (searched; no authoritative page found — irrelevant to the decision since present-absence is verified)
- Upstream #1274's exact environment details beyond its PR description (from `.planning/research/UPSTREAM-PRS.md`, previously verified)

## Metadata

**Confidence breakdown:**
- libcport idiom + libc mappings: **HIGH** — compiled and executed on the exact target toolchain; header values quoted
- Test-porting inventory: **HIGH** — every blocker file read; collection and failure modes reproduced live
- PORT-02/03/04 audit findings: **HIGH** — each backed by a reproduced experiment or quoted source line
- 4 known-failure root causes: **LOW→in-phase** — hypotheses only (A1/A2); D2-07 protocol handles the uncertainty
- TEST-02 mechanics: **MEDIUM** — counts verified; threshold choice is planner discretion

**Research date:** 2026-10-12
**Valid until:** 2026-11-12 (stable, codebase-anchored; re-verify only if htslib/Cython versions move)
