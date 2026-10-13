# Roadmap: pysam Windows 适配

## Overview

从 `setup.py` 在 Windows 上一启动就报错（依赖 `sh configure`/`make`/`nm`）出发，先以 MSYS2 UCRT64/MinGW-w64 打通开发验证构建（预烘焙 `config.h` + 显式源码清单的 Pillow/h5py 模式），再做 Cython/POSIX 可移植性加固并让完整测试套件在 Windows 全绿（功能对等的客观证据）；随后将构建系统复刻到 MSVC 官方工具链，最后接入 GitHub Actions Windows CI 与 cibuildwheel，产出经 delvewheel 修复、清洁机冒烟测试把关的自包含 `win_amd64` wheel，经 fork 渠道（GitHub Releases）分发给 Windows 用户。MinGW 仅是开发验证工具，MSVC 才是发布产物工具链；全程 Linux/macOS 构建零回归。

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: MinGW-w64 构建系统** - MSYS2 UCRT64 下从源码完整构建 pysam（开发验证产物） (completed 2026-10-01)
- [x] **Phase 2: 可移植性加固与测试全绿** - POSIX 依赖清除 + 完整测试套件在 Windows 通过（对等证据） (completed 2026-10-12)
- [x] **Phase 3: MSVC 构建系统** - 预烘焙 config.h.msvc + 显式源码清单的官方级工具链 (completed 2026-10-13)
- [x] **Phase 4: Windows CI 与 wheel 分发** - CI 持续产出并分发自包含 win_amd64 wheel（fork 渠道） (completed 2026-10-13)

## Phase Details

### Phase 1: MinGW-w64 构建系统

**Goal**: 开发者在 MSYS2 UCRT64 下从源码一步构建 pysam（含 bundled htslib/htscodecs/samtools/bcftools），`import pysam` 在 Windows 开发机可用 — 一切后续工作的前提。
**Depends on**: Nothing (first phase)
**Requirements**: BUILD-01, BUILD-03
**Success Criteria** (what must be TRUE):

  1. 开发者在 MSYS2 UCRT64 环境执行构建（`pip install -e .` 或 setup.py build）即编译出全部 Cython 扩展与 bundled htslib/htscodecs/samtools/bcftools，全程不调用 `sh configure`/`make`/`nm`
  2. Windows 开发机上 `import pysam` 成功，能打开一个 BAM 文件并通过 `_pysam_dispatch` 运行一个 samtools/bcftools 命令
  3. `check_ext_symbol_conflicts` 在 Windows 上经 llvm-nm 实际运行，检出重复符号时使构建失败（不再静默跳过）
  4. 现有 Linux/macOS 构建与 CI 保持绿色（零回归）

**Plans:** 3/3 plans complete

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — 基础设施：CRLF 归一化 + UCRT64 bootstrap 脚本 + smoke 门 + INSTALL Windows 章节

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — setup.py 七处外科手术式编辑：UCRT64 门、sh 前缀、llvm-nm 符号门、win32 分支重写、implib、devnull

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — 首次 UCRT64 全量构建 + smoke/BUILD-03 实证 + fork CI 零回归收口

### Phase 2: 可移植性加固与测试全绿

**Goal**: 完整测试套件在 Windows 上通过，skip 数与 Linux 基线对账 — 功能对等的客观证据（PROJECT.md 成功标准）。
**Depends on**: Phase 1
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):

  1. 完整 pytest 套件在 Windows 全绿：7 个含 POSIX shell 调用的测试文件改写为进程内实现，make 测试数据生成有 Windows 替代，conftest spawn 安全
  2. 收集测试数与 Linux 基线完成对账，skip 差异在约定阈值内并记录在案（防 skip creep 冒充成功）
  3. Windows 上写出并回读的 BAM/BGZF 文件无 CRLF 损坏（全部文件 I/O 强制 `O_BINARY`/`"b"` 的审计关闭）
  4. `compile_test.py` 结构体大小断言按 LLP64 更新并通过（`long` 截断审计关闭）
  5. CJK 非 ASCII 文件名金丝雀测试通过

**Plans:** 4/4 plans complete

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — libcport 集中平台映射层：四处 posix cimport 收敛 + 两处 raw fd O_BINARY 修复 + D2-03 清单（PORT-01, PORT-02）

**Wave 2** *(blocked on Wave 1 completion — 共享构建目录的 rebuild 互斥)*

- [x] 02-02-PLAN.md — 审计三闭环：CJK 宽字符 shim（PORT-04）+ 字节级回归测试与 call-site 清单（PORT-02）+ LLP64 断言与 static asserts（PORT-03）

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03-PLAN.md — 测试基础设施：三个 Python 数据生成器 + conftest spawn 安全 + 收集期内 in-process 比较改写（TEST-01 阻塞项清除）

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-04-PLAN.md — 全量套件绿 + D2-07 四项已知失败 fix-first 处置 + TEST-02 对账与零回归收口（TEST-01, TEST-02）

### Phase 3: MSVC 构建系统

**Goal**: pysam 可用 MSVC（Build Tools for VS 2022）完整构建并通过全量测试 — 官方 wheel 生态的原生工具链就位。
**Depends on**: Phase 2
**Requirements**: BUILD-02
**Success Criteria** (what must be TRUE):

  1. MSVC 下 setup.py 分支（`compiler_type` 分派）基于预生成 `win32/config.h.msvc` + 显式源码清单完成全部扩展与 bundled 库编译，无任何 autotools 调用
  2. MSVC 构建产物上 `import pysam` 成功，且完整测试套件全绿
  3. 单一集中 MSVC shim 头文件覆盖 C99/VLA 缺口（无逐文件打地鼠）；按研究标志完成 clang-cl 回退路径评估

**Plans:** 5/5 plans complete

Plans:
**Wave 1** *(parallel — no file overlap)*

- [x] 03-01-PLAN.md — 携带约束闭环：D-17 implib 路径统一 + D-20 模板/双生文件锁步与编译器门 + VLA/[static] C99 修复 + WR-01 _collect UTF-8 解码（BUILD-02 前置）
- [x] 03-02-PLAN.md — vendor/ 依赖树：zlib/bzip2/xz/musl-regex 官方渠道采购 + SHA-256 溯源清单 + cl 编译探针工具

**Wave 2** *(blocked on 03-01 setup.py 顺序 + 03-02 vendor 就位)*

- [x] 03-03-PLAN.md — MSVC 构建基础：平台门重构 + win32/config.h.msvc 预烘焙 + win32/msvc/ 集中 shim 层 + 两级分派接线（显式源码清单、HTS_BUILDING_LIBRARY、/DEF:、/IMPLIB:、符号门 .lib）

**Wave 3** *(blocked on Wave 2)*

- [x] 03-04-PLAN.md — 首次全量 MSVC 构建（tracer）+ import/BAM/dispatch 冒烟 + out-of-tree D-17 实证 + UCRT64 零回归中间检查

**Wave 4** *(blocked on Wave 3)*

- [x] 03-05-PLAN.md — SC-2 全量套件在 MSVC 产物上全绿 + 1027/15 基线对账 + SC-3 clang-cl 评估决策记录 + 阶段零回归收口（fork CI）

### Phase 4: Windows CI 与 wheel 分发

**Goal**: CI 持续产出经清洁机冒烟测试把关的自包含 `win_amd64` wheel，经 fork 渠道发布 — Windows 用户 `pip install` 即可用。
**Depends on**: Phase 3
**Requirements**: CI-01, CI-02, CI-03
**Success Criteria** (what must be TRUE):

  1. GitHub Actions `windows-latest` runner 上手工 build+pytest job 全绿（先验证，再接入 cibuildwheel）
  2. cibuildwheel 产出 delvewheel 修复的自包含 `win_amd64` wheel，覆盖 Python 3.10–3.15 全矩阵（`python_requires` 对齐上游）
  3. 发布门槛生效：清洁 Windows 机器安装 wheel 并 import + 打开 BAM 的冒烟测试通过后才允许发布
  4. wheel 经 fork 渠道发布到 GitHub Releases，Windows 用户 pip 安装后 htslib API 绑定与 samtools/bcftools 命令分派全部可用

**Plans:** 3/3 plans complete

Plans:
**Wave 1**

- [x] 04-01-PLAN.md — ci.yaml 追加独立 `windows` direct job（3.10–3.15 全矩阵 build+pytest，符号门在 runner 上实跑）— 加法式零回归（CI-01, SC-1）

**Wave 2** *(blocked on 04-01 — SC-1 顺序：direct job 先绿，才接 cibuildwheel)*

- [x] 04-02-PLAN.md — win-wheels.yaml：cibuildwheel@v4.3.1 构建 cp310–cp315 → delvewheel `--ignore-existing` 修复 → CIBW smoke → 清洁机门 → fork Releases 发布 v0.24.1-win.1（含供应链 blocking checkpoint）（CI-02, CI-03, SC-2/3/4）

**Wave 3** *(blocked on 04-02)*

- [x] 04-03-PLAN.md — 消费者路径实证（Release URL 干净 venv 安装 + smoke）+ 04-CI-VALIDATION.md 对账记录（矩阵/完整性/CI-03 对齐/建议采纳登记）+ INSTALL wheel 章节 + 阶段零回归收口（CI-02, CI-03）

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

**Ordering rationale:**

- Build system first — 每个特性与每条测试都依赖可运行的构建（研究：依赖图根节点）。
- Portability/tests before MSVC — MinGW 移植先行迫使并验证全部平台抽象工作；先做 MSVC 会在更难的工具链上翻倍风险（研究：MSVC 排 MinGW 之后）。
- MSVC before CI/wheels — CI-02 明确要求 MSVC 产出的 wheel（PROJECT.md 决策：wheel 只发 MSVC），wheel 分发阶段必须在 MSVC 构建系统就位之后。
- Remote I/O（libcurl/S3/GCS）为 v2 差异化项（REMOTE-01），不在本路线图。

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. MinGW-w64 构建系统 | 3/3 | Complete    | 2026-10-01 |
| 2. 可移植性加固与测试全绿 | 4/4 | Complete    | 2026-10-12 |
| 3. MSVC 构建系统 | 5/5 | Complete    | 2026-10-13 |
| 4. Windows CI 与 wheel 分发 | 3/3 | Complete    | 2026-10-13 |

---
*Roadmap created: 2026-09-17*
