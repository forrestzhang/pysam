# pysam Windows 适配

## What This Is

让 pysam（Python 的 samtools/htslib C 库封装）能够在 Windows 上完整构建、通过全部测试，并由 CI 持续产出可分发的 Windows wheel。这是基于上游 pysam 代码库的棕地移植项目，先在 fork 上验证分发，最终目标为全功能对等。

## Core Value

Windows 用户能够 `pip install` 拿到 wheel 并正常使用 pysam 的全部功能（htslib API 绑定 + samtools/bcftools 命令封装），完整测试套件在 Windows 上通过。

## Requirements

### Validated

<!-- 从现有代码库推断的既有能力（详见 .planning/codebase/） -->

- ✓ htslib API 绑定（AlignmentFile/VariantFile/tabix 等 Cython 扩展模块）— existing
- ✓ samtools/bcftools 命令封装（`_pysam_dispatch`，经 `devtools/import.py` 正则重写嵌入）— existing
- ✓ Linux/macOS 上通过 autotools/make 构建 bundled htslib/samtools/bcftools — existing
- ✓ cibuildwheel 产出 Linux/macOS wheel（`ci.yaml`/`release.yaml`）— existing
- ✓ MinGW-w64 (MSYS2) 下从源码完整构建 pysam（含 bundled htslib/samtools/bcftools）— Phase 1（UCRT64 单命令 bootstrap，13 扩展 + 13 导入库，BUILD-03 符号门带牙齿，D-16 getopt 隔离，ubuntu/macos CI 零回归）
- ✓ Windows 可移植性加固 + 完整测试套件全绿 — Phase 2（libcport.pxd 单点平台映射清零 posix cimport；htslib 宽字符 open shim 使 CJK 路径可用；11 项字节保真回归测试防 text-mode 损坏；1027 passed / 15 skipped / 0 failed，TEST-02 对账零静默 skip；fork CI 19/19 全绿；上游 4 个已知失败中 1 个直接通过、3 个根因修复；PORT-01..04 + TEST-01/02）
- ✓ MSVC 构建系统就位（双工具链并存）— Phase 3（setup.py 两级分派：平台选源码 compiler_type 选 flags；预烘焙 win32/config.h.msvc + 52-TU 显式源码清单，MSVC 路径零 autotools；win32/msvc/ 集中 shim 层 + pthread/dirent/regex 实现；四棵 vendored 依赖树带 SHA-256 溯源；首次全量 MSVC 构建 27 轮迭代收敛；**双工具链同树全绿：MSVC 与 UCRT64 各 1028/15/0**；D-17 implib 修复双臂验证；D-20 模板 lockstep 机械证明；fork CI 19/19 SHA 钉扎；BUILD-02）
- ✓ Windows CI 与 wheel 分发上线 — Phase 4（ci.yaml 增量 windows job：MSVC 构建 + 实时符号门 + 全量 pytest，3.10–3.15 六 cell，25/25 全绿；win-wheels.yaml 流水线：cibuildwheel v4.3.1 → delvewheel `--ignore-existing` 修复 → 清洁机 smoke 门 → tag 门控发布；**线上 Release v0.24.1-win.2：6 个自包含 wheel（cp310–cp315），sha256 6/6 校验，无 vendor DLL、无 msvcrt.dll**；消费端从线上 URL 实证安装 + 全功能 smoke；CI 1032/16 与本地 1028/15 零未解释差异对账；CI-01/02/03）

### Active

<!-- 当前范围。正在构建的方向。 -->

（v1 里程碑 12/12 需求全部交付 —— 见 Validated。后续方向见 Out of Scope 与 ROADMAP v2 候选。）

### Out of Scope

- 上游 PyPI 官方包名分发 — 先 fork 渠道验证，上游化另行推动
- 32-bit Windows 支持 — 64-bit 优先，32-bit 无明确需求
- 修改 htslib/samtools/bcftools 上游源码本身的功能性行为 — 仅做可回馈上游的可移植性修补
- 非 Windows 平台的构建行为变更 — 现有 Linux/macOS 构建必须保持不回归

## Context

- pysam 是成熟的 Python/Cython 项目，捆绑 htslib/samtools/bcftools 源码树并通过 `devtools/import.py` 正则重写嵌入命令行工具代码。
- 关键阻塞点（详见 `.planning/codebase/CONCERNS.md`，含 10 项排序的 Windows 移植障碍）：
  - 构建系统全流程依赖 `sh configure` + `make` + `nm`（`setup.py`），GCC-only 编译选项（`-Wno-*`、`-Wl,-rpath,$ORIGIN`）
  - `pysam/libchtslib.pyx`、`pysam/libcutils.pyx`、`pysam/libctabix.pyx` 直接 cimport `posix.unistd`/`posix.fcntl`
  - `_pysam_dispatch` 中硬编码 `/dev/null`；`pysam/dynamic_libs.c` 使用 `dlopen`
  - `win32/` 下的 MSVC 时代 shim 头文件陈旧且未经测试（`setup.py:634` 分支标记 "untested"）
  - CI（`ci.yaml`/`release.yaml`）无任何 Windows runner；7 个测试文件含 POSIX shell 子进程调用
- 用户环境：Windows 11，Git Bash；开发分支 `win`。

## Constraints

- **Compatibility**: 现有 Linux/macOS 构建与测试不得回归 — 所有变更必须跨平台安全
- **Toolchain**: 先 MinGW-w64（MSYS2）后 MSVC，分阶段 — MinGW 最接近现有 GCC 流程，MSVC 是 Python 官方 wheel 生态原生路径
- **Feature parity**: 全功能对等 — samtools/bcftools 命令封装与 htslib API 绑定都要可用
- **Verification**: 完整测试套件在 Windows 上通过才算适配成功
- **Distribution**: wheel 先经 fork 渠道分发 — PyPI 官方名需要上游维护者配合

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 先 fork 分发 wheel，而非直接追求 PyPI 官方包 | PyPI 包名需上游配合；先在 fork 验证可降低协作不确定性 | — Pending |
| 中间工具链路线：MinGW/UCRT64 仅作开发验证工具，wheel 只发 MSVC | MinGW 是 htslib 官方验证的 Windows 路径、最快到达"测试全绿"；MSVC 是官方 wheel 生态原生路径；兼顾快速验证与单一发布产物 | — Pending |
| 全功能对等 + 完整测试套件作为成功标准 | 避免半移植状态难以界定"可用"；测试套件是客观验证依据 | — Pending |
| **D-16: getopt 族平台豁免（MinGW 隔离模型）** — libchtslib 不再导出 getopt 族（`--exclude-symbols`），各工具扩展持 mingwex 静态私有副本；BUILD-03 门控仅豁免封闭 7 符号集 {getopt, getopt_long, getopt_long_only, optarg, optind, opterr, optopt}，限 win32 路径 | D-10 前提被首次真实 UCRT64 构建证伪：getopt 族在静态 libmingwex.a 中，PE 数据导入缺口使共享设计必然多重定义；采用与 Windows 独立 samtools.exe/bcftools.exe 等价的隔离模型 | — Accepted（2026-09-18，plan 01-03 Task 1 人类裁决；UAT 2026-09-30 追认） |
| **D-17: CR-01 implib 发射路径分叉延后** — 非 inplace 构建（`pip install .` / `setup.py build` / `bdist_wheel`）下符号门探测 `build/lib.../pysam/*.dll.a` 而 implib 实际落源码树 → 未捕获 CalledProcessError；修法：发射路径从 `os.path.dirname(get_ext_fullpath(...))` 派生 | Phase 1/2 开发流全为 inplace（D-14），两路径一致不阻塞；Phase 3（BUILD-02 MSVC）为首个 out-of-tree 构建阶段，必须先行修复 | — Deferred（2026-09-30 UAT 裁决，01-REVIEW-DISPOSITION.md） |
| **D-18: libcport 单点平台映射（实证机制）** — `cdef extern from *` + `#ifdef _WIN32` C 预处理器切换（定长 psam_open2/3、强制 `_O_BINARY`、`psam_off_t` 64 位）；POSIX 分支纯恒等别名 | CONTEXT D2-01 的机制设想（Cython 3.1 plain-if + libc.msvcrt/libc.io）被实测证伪：环境为 Cython 3.3.0 且该 cimport 目标不存在；锁定属性（现在做开关、单点映射层）原样交付 | — Accepted（Phase 2，02-01 environment_contract 记录） |
| **D-19: conftest 平台分裂** — POSIX 分支逐字保留上游子进程 httpserver，win32 用线程版 | 线程版在 POSIX 下被 `_pysam_dispatch` 持 GIL 的 libcurl 传输饿死（fork CI run 38217865780 ubuntu 失败）；分裂后 CI 19/19 全绿 | — Accepted（Phase 2，d912a1df） |
| **D-20: Phase 3 输入 — dispatch setjmp 修复的双重缺口（WR-01/WR-05）** | samtools/bcftools.pysam.c 的 `_WIN32 __builtin_setjmp` 崩溃修复未同步进 import/pysam.c 模板（下次 import.py 运行会静默回退），且 GCC builtins 不兼容 MSVC/clang-cl；两项均记 02-REVIEW-DISPOSITION.md open，Phase 3（BUILD-02）必须处置 | — Accepted（Phase 3 关闭：模板 lockstep 机械证明 + `_MSC_VER` 编译器门控三文件 grep==1） |
| **D-21: MSVC 双工具链两级分派** | 平台（sysconfig mingw vs win-amd64）选模块图（源码/依赖来源），compiler_type 选 flags（UCRT64 mingw 臂原样，MSVC 臂 /DEF: + 晚到 /IMPLIB: + 零 -Wl）；UCRT64 路径字节不动的零回归形态贯穿 | — Accepted（Phase 3） |
| **D-22: MSVC 依赖闭包全 vendor** | MSYS2 头文件/库不跨工具链（zconf.h 含 unistd.h 实证）；zlib/bzip2/xz/musl-regex 四树 vendor 带 SHA-256 溯源（musl 无官方 checksum 显式标注）；pthread 用最小 Win32 CRITICAL_SECTION shim（14 函数有界面） | — Accepted（Phase 3） |
| **D-23: MSVC 跨模块数据绑定须在声明点 dllimport** | MSVC 链接器无 GNU ld 自动导入；/FI shim 无法赢过晚到的声明（最后声明定链接性）；hts_defs.h 消费者臂 `#elif _MSC_VER`，UCRT64 预处理输出逐字节不变 | — Accepted（Phase 3，LNK1181 修复中实证） |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-13 after Phase 4 (v1 milestone complete)*
