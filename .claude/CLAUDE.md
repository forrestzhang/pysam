# pysam Windows 适配 — 项目指令

棕地移植项目：让 pysam（Python 的 samtools/htslib C 库封装）在 Windows 上完整构建、通过全部测试，并由 CI 持续产出可分发的 Windows wheel。

## Core Value

Windows 用户能够 `pip install` 拿到 wheel 并正常使用 pysam 的全部功能（htslib API 绑定 + samtools/bcftools 命令封装），完整测试套件在 Windows 上通过。

## 关键决策（硬约束）

1. **中间工具链路线**：MinGW/UCRT64 仅作开发验证工具（最快到达"测试全绿"），wheel 只发 MSVC（官方 wheel 生态原生路径，单一发布产物）。
2. **fork 分发优先**：先在 fork 的 GitHub Releases 验证 wheel 分发；PyPI 官方包名需要上游维护者配合，单独推动。
3. **全功能对等 + 完整测试套件 = 成功标准**。半移植状态不接受 — 测试套件是客观验证依据。
4. **远程 I/O 延期至 v2**：`libcurl` / S3 / GCS 在 Windows 无任何竞品实现，不在本里程碑范围。
5. **路线图顺序：MSVC 早于 CI/wheel**。Phase 3（MSVC 构建系统）必须在 Phase 4（CI + wheel 分发）之前完成，因 CI-02 要求 MSVC 产出的 wheel。

## 跨平台硬约束

- **Linux/macOS 零回归** — 任何 Windows 移植改动必须双平台安全。这是 PROJECT.md 最高优先级约束。
- **不改 htslib/samtools/bcftools 上游功能性行为** — 仅做可回馈上游的可移植性修补。
- **32-bit Windows 不支持** — 64-bit 优先。

## 反模式（必须避免）

| 反模式 | 严重度 | 后果 | 预防 |
|--------|--------|------|------|
| **msvcrt 版 MinGW**（legacy MINGW64 而非 UCRT64） | blocking | 与 python.org CPython fd/堆 ABI 不兼容，静默损坏 | 强制 UCRT64；wheel 审计时拒绝 `msvcrt.dll` 导入 |
| **Windows 文本模式 I/O**（`open()` 不加 `"b"`，C 端不开 `O_BINARY`） | blocking | BAM/BGZF 的 `\n` 被静默翻译为 `\r\n`，二进制数据损坏 | PORT-02 阶段做字节比对审计；Cython `open` 必须显式 `"b"`，C 端 `open()` 必须 `_O_BINARY` |
| **commit 带 `Co-Authored-By` trailer** | advisory | 用户明确禁止 | 所有提交用纯消息体；存放在记忆中 |

## 路线图

| Phase | 名称 | 核心需求 |
|-------|------|----------|
| 1 | MinGW-w64 构建系统 | BUILD-01, BUILD-03 |
| 2 | 可移植性加固与测试全绿 | PORT-01~04, TEST-01, TEST-02 |
| 3 | MSVC 构建系统 | BUILD-02 |
| 4 | Windows CI 与 wheel 分发 | CI-01, CI-02, CI-03 |

13 项 v1 需求已 100% 覆盖。详细 ROADMAP 见 `.planning/ROADMAP.md`。

## 已知研究缺口（plan-phase 时启动 research-phase）

- **Phase 1**: UCRT64 GCC ↔ python.org CPython 头文件的自定义 `build_ext` 胶水 — 文档最少层（STACK 置信度 MEDIUM）。
- **Phase 2**: Cython 3.1 编译期平台开关惯用法；`libc.msvcrt` / `libc.io` 精确映射待核实。
- **Phase 3**: clang-cl 回退路径与 MSVC C99 shim 范围（bundled 源码 VLA 清单）需决策 spike。

## 当前焦点

**Phase 1 — MinGW-w64 构建系统**。下一步 `/gsd-discuss-phase 1`（收集 vision/边界）或直接 `/gsd-plan-phase 1`（yolo 模式）。

## 环境

- 分支：`win`（基于 master `4c8486b1`）
- 开发机：Windows 11 + Git Bash
- MSYS2 UCRT64 尚未安装（Phase 1 前置条件）
- GitHub Actions 现有 `ci.yaml` / `release.yaml` 无 Windows runner

## 上下文文档

- `.planning/PROJECT.md` — 项目定义、需求、决策日志、约束
- `.planning/REQUIREMENTS.md` — 13 项 v1 需求
- `.planning/ROADMAP.md` — 4 phase 详细规划
- `.planning/research/SUMMARY.md` — 调研综合结论
- `.planning/codebase/CONCERNS.md` — 10 项排序的 Windows 移植障碍
