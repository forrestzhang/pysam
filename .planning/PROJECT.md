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

### Active

<!-- 当前范围。正在构建的方向。 -->

- [ ] MinGW-w64 (MSYS2) 下从源码完整构建 pysam（含 bundled htslib/samtools/bcftools）
- [ ] 消除 Python/Cython 层的 POSIX-only 依赖（`posix.unistd`/`posix.fcntl` cimport、硬编码 `/dev/null`、shell 子进程调用）
- [ ] Windows 下完整测试套件通过（含移植测试中的 POSIX shell 调用与测试数据生成流程）
- [ ] CI（GitHub Actions）增加 Windows runner，产出并分发 wheel（先 fork 渠道：GitHub Releases）
- [ ] MSVC 工具链支持（第二阶段，与 MinGW-w64 并列产出 wheel）
- [ ] Python 版本覆盖面对齐上游当前支持面

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
| **D-16: getopt 族平台豁免（MinGW 隔离模型）** — libchtslib 不再导出 getopt 族（`--exclude-symbols`），各工具扩展持 mingwex 静态私有副本；BUILD-03 门控仅豁免封闭 7 符号集 {getopt, getopt_long, getopt_long_only, optarg, optind, opterr, optopt}，限 win32 路径 | D-10 前提被首次真实 UCRT64 构建证伪：getopt 族在静态 libmingwex.a 中，PE 数据导入缺口使共享设计必然多重定义；采用与 Windows 独立 samtools.exe/bcftools.exe 等价的隔离模型 | — Accepted（2026-09-18，plan 01-03 Task 1 人类裁决） |

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
*Last updated: 2026-09-17 after initialization*
