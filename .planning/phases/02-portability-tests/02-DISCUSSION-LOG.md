# Phase 2: 可移植性加固与测试全绿 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-12
**Phase:** 2-可移植性加固与测试全绿
**Areas discussed:** POSIX 清理深度, 测试移植策略, 审计证据形态

---

## Session preamble

User invoked `/gsd-discuss-phase 1`, but STATE.md showed Phase 1 already complete (3/3 plans, UAT passed, 2026-10-01; CLAUDE.md's "current focus" section is stale). User was asked which phase to actually discuss and chose **Phase 2**.

---

## POSIX 清理深度

**Q1: posix.* cimport（W2，三个模块）的清理时机与方式？**

| Option | Description | Selected |
|--------|-------------|----------|
| 现在做平台开关 | 本 phase 就在三个 .pyx 做编译期平台开关，一次性服务 MinGW+MSVC，PORT-01 彻底关闭 | ✓ |
| 最小修补，延迟到 Phase 3 | 只修 UCRT64 真实阻塞项，posix.* cimport 留给 MSVC 时再条件化 | |
| 先 spike 后动手 | 平台开关代码现在做，先出 MSVC 映射研究笔记验证可行性 | |

**Q2: W3 硬编码 b"/dev/null" 怎么修？**

| Option | Description | Selected |
|--------|-------------|----------|
| 平台条件常量 | sys.platform 检查选 b"NUL" vs b"/dev/null"，不动 fd 重定向结构 | ✓ |
| 结构性消除 | 重构消除 null 设备依赖；可能碰 jmp_buf 清理路径（W10 风险区） | |
| os.devnull 传入 | Python 层算好路径传入 Cython 层 | |

**Q3: PORT-01 验收口径？**

| Option | Description | Selected |
|--------|-------------|----------|
| grep-clean 清单审计 | grep 全部 POSIX-only 符号，每项守卫内或已消除，清单落 phase 文档 | ✓ |
| 功能性验收 | 测试全绿即视为完成，无审计文档 | |
| 审计+自动守卫 | 清单 + CI 守卫脚本每次 push 自动 grep | |

**Q4: 平台开关的代码组织？**

| Option | Description | Selected |
|--------|-------------|----------|
| 集中 libcport.pxd | 统一映射层，内部按平台指向 posix.* 或 libc.msvcrt/libc.io | ✓ |
| 各文件内联开关 | 每个 .pyx 内直接 IF/ELSE，无新文件但映射重复三遍 | |

---

## 测试移植策略

**Q1: 7 个 shell 测试文件：外部 samtools 命令对比怎么处理？**

| Option | Description | Selected |
|--------|-------------|----------|
| 纯进程内对比 | 改用 pysam 自己 dispatch 或纯 Python 读回比对，无外部可执行依赖 | ✓ |
| 保留外部命令对比 | #1274 路线：pacman 装 samtools/bcftools 继续 subprocess 对比 | |
| 进程内主 + 可选外部 | 主 suite 进程内，-m external 可选子集 | |

**Q2: make 测试数据生成的 Windows 替代？**

| Option | Description | Selected |
|--------|-------------|----------|
| Python 重写 | 生成逻辑改为 Python 脚本调 pysam API，make_data_files() 按平台分派 | ✓ |
| 继续用 make | MSYS2 环境里有 make，零改动但绑死 MSYS2 | |
| 预生成提交 | 产物直接进仓库，最稳但仓库变大 | |

**Q3: conftest HTTP server 的 Windows 安全化？**

| Option | Description | Selected |
|--------|-------------|----------|
| threading 重写 | http.server + threading 进程内线程，消除 fork/spawn 语义差异 | ✓ |
| multiprocessing spawn 安全化 | 显式 spawn 上下文 + if __name__ 守卫 | |
| 第三方插件 | pytest-httpserver 等替代自建 | |

**Q4: 上游 #1274 已知 4 个失败测试的处理策略？**

| Option | Description | Selected |
|--------|-------------|----------|
| 先修后豁 | 根因优先，确属平台行为差异才 skip+理由进豁免清单，零静默 skip | ✓ |
| 遇错即跳 | skipif win32 + TODO，全绿速度优先 | |
| 对齐上游 xfail | 同款失败直接 xfail(strict=False) | |

---

## 审计证据形态

**Q1: PORT-02 二进制模式审计的证据形态？**

| Option | Description | Selected |
|--------|-------------|----------|
| 清单+永久回归测试 | 一次性 grep 清单 + 字节级回归测试进常规 suite | ✓ |
| 仅一次性清单 | 人工审计落档，不加永久测试 | |
| C 层强制断言 | 包装宏强制二进制，代码即证据 | |

**Q2: PORT-03 LLP64 审计的实现方式？**

| Option | Description | Selected |
|--------|-------------|----------|
| 断言更新+static assert | compile_test.py 按 LLP64 更新 + C 层编译期 static assert | ✓ |
| 仅更新 compile_test | 最小改动满足字面要求 | |
| 全量 long API 审计 | grep 所有 long/int 混用点逐一核对 | |

**Q3: PORT-04 CJK 金丝雀覆盖范围？**

| Option | Description | Selected |
|--------|-------------|----------|
| 核心面金丝雀 | CJK 路径读写+index+tabix+dispatch roundtrip | ✓ |
| 最小 roundtrip | 只测 open/read/write 一个测试 | |
| 全矩阵覆盖 | CJK+音标+emoji+空格+嵌套目录 × 全 API | |

**Q4: TEST-01"全绿"的套件范围？**

| Option | Description | Selected |
|--------|-------------|----------|
| 默认 collection | testpaths=pysam tests，不含 bench，对齐上游 CI 语义 | ✓ |
| 含 bench 文件 | bench 也要求通过 | |
| collection 含 collect 检查 | bench 能被 collect 不报错即可 | |

---

## Claude's Discretion

- `libcport.pxd` 文件名与内部布局（pxd-only vs pxd+pxi）
- TEST-02 对账机制细节（Linux 基线来源、对比产物格式、skip 差异阈值）
- Cython 3.1 平台开关惯用法细节与 libc.msvcrt/libc.io 精确映射（研究缺口，researcher 验证）
- D2-07 之外的豁免测试具体清单（执行中发现并附理由追加）
- Python 数据生成器与 POSIX Makefile 的代码共享程度

## Deferred Ideas

- TEST-02 基线/阈值深设计（讨论中被取消选择，留给 planner/researcher 在 D2-07 纪律内裁量）
- bench 文件 Windows 移植（D2-11 排除出"全绿"；Phase 4 CI 需要性能信号时再议）
- 远程 I/O 测试的启用（v2，libcurl 延期决策）
