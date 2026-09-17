# Requirements: pysam Windows 适配

**Defined:** 2026-09-17
**Core Value:** Windows 用户能够 `pip install` 拿到 wheel 并正常使用 pysam 的全部功能（htslib API 绑定 + samtools/bcftools 命令封装），完整测试套件在 Windows 上通过。

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### 构建系统 (Build)

- [ ] **BUILD-01**: MinGW/UCRT64 开发构建 — `setup.py` 在 MSYS2 UCRT64 环境下完整构建 bundled htslib/samtools/bcftools（保留 autotools 流程，仅管道改造；产物仅用于开发验证，不分发）
- [ ] **BUILD-02**: MSVC 构建系统 — 预生成 `win32/config.h` + 显式源码清单（Pillow/h5py 模式），产出官方级构建
- [ ] **BUILD-03**: 符号冲突检查移植 — `nm` → `llvm-nm`/`dumpbin`，接入 `check_ext_symbol_conflicts`（Windows 上 duplicate symbol 导致运行时崩溃而非链接错误）

### 代码可移植性 (Portability)

- [ ] **PORT-01**: POSIX 依赖清除 — `posix.unistd`/`posix.fcntl` cimport、硬编码 `/dev/null`、fork/signal 等 POSIX-only 路径全部消除或条件化
- [ ] **PORT-02**: 二进制模式审计 — 所有文件 I/O 强制 `O_BINARY`/`"b"`，防止 `\r\n` 翻译静默损坏 BAM/BGZF
- [ ] **PORT-03**: LLP64 类型审计 — `long` 截断与类型宽度检查（用 `compile_test.py` 做本地化工具，而非跳过）
- [ ] **PORT-04**: 非 ASCII 路径适配 — 宽字符 API shim + CJK 文件名金丝雀测试

### 测试 (Testing)

- [ ] **TEST-01**: 测试全绿 — 完整测试套件在 Windows 通过（含 7 个测试文件的 POSIX shell 调用移植、make 测试数据生成的 Windows 替代、spawn 安全 conftest）
- [ ] **TEST-02**: 测试数对账 — 收集的测试数与 Linux 基线 skip-parity 对账，作为客观指标

### CI 与分发 (CI & Distribution)

- [ ] **CI-01**: Windows CI — GitHub Actions 增加 `windows-latest` runner（先手工 build+pytest job，验证后接入 cibuildwheel）
- [ ] **CI-02**: wheel 分发 — MSVC 产出自包含 `win_amd64` wheel，delvewheel 修复 + 清洁机安装冒烟测试作为发布门槛，经 fork 渠道（GitHub Releases）分发
- [ ] **CI-03**: Python 版本对齐 — wheel 覆盖上游支持面（3.10–3.15，以 `python_requires` 为准）

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### 差异化能力

- **REMOTE-01**: 远程 I/O 对等（libcurl/S3/GCS）— 所有竞品在 Windows 均无此能力，属 v1.x 差异化项；Windows 动态加载器设计需专项调研
- **MGW-01**: MinGW wheel 分发 — MinGW 当前仅作开发验证工具

### 上游化

- **UPSTR-01**: PyPI 官方包名分发 — 需上游维护者协作，fork 验证后另行推动

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| 32-bit Windows 支持 | 64-bit 优先，无明确需求 |
| Conda 打包 | Bioconda 不支持 Windows，pip wheel 已覆盖 |
| Cygwin 支持 | 已被 MSYS2 取代，无维护价值 |
| 用户侧外部 htslib 依赖 | 自包含 wheel 是核心交付物 |
| htslib/samtools/bcftools 功能性行为修改 | 仅做可回馈上游的可移植性修补 |
| Linux/macOS 构建行为变更 | 现有构建必须零回归 |
| 重写 meson/CMake 构建 | 上游无此构建系统，且违反不改上游行为的约束；Pillow/lxml 式预烘焙 config.h 模式已足够 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUILD-01 | TBD | Pending |
| BUILD-02 | TBD | Pending |
| BUILD-03 | TBD | Pending |
| PORT-01 | TBD | Pending |
| PORT-02 | TBD | Pending |
| PORT-03 | TBD | Pending |
| PORT-04 | TBD | Pending |
| TEST-01 | TBD | Pending |
| TEST-02 | TBD | Pending |
| CI-01 | TBD | Pending |
| CI-02 | TBD | Pending |
| CI-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 0
- Unmapped: 13 ⚠️（等待路线图创建）

---
*Requirements defined: 2026-09-17*
*Last updated: 2026-09-17 after initial definition*
