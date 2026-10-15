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
| 5 | 技术债清理（用户裁决插入） | lockstep/shim 哨兵/clean_smoke/oracle 强化 |

v1 全部 5 phase 已完成（2026-10-13 归档）。详细 ROADMAP 见 `.planning/ROADMAP.md`。

## 已知研究缺口

无 — v1 三项研究缺口（UCRT64 build_ext 胶水、Cython 平台开关、clang-cl 回退评估）均已在对应 phase 内解决并记录于 `.planning/STATE.md` 决策日志。

## 当前焦点

**v1 里程碑（Windows 适配）已完成并归档（2026-10-13）**。5 个 phase 全部落地：UCRT64 开发构建、全套件双工具链全绿（1034/15/0）、MSVC 构建系统、Windows CI 6-cell 矩阵、Release v0.24.1-win.2 线上 6 wheel（cp310–cp315）。

下一步（二选一）：
- 启动 v2（候选：远程 I/O libcurl/S3/GCS、PyPI 官方名、wheel 逐版本全量门 — 见 `.planning/milestones/v1-MILESTONE-AUDIT.md` 残余节 + `RETROSPECTIVE.md`）
- 直接发新 wheel：推 `v<version>-win.N` tag 触发 win-wheels 流水线（里程碑 tag 勿含点，避免撞发布 glob）

## 环境

- 分支：`win`（基于 master `4c8486b1`），已推送 origin
- 开发机：Windows 11 + Git Bash
- 双工具链就位：MSYS2 UCRT64（venv `_venv/`，构建需 `MAKE=mingw32-make` + `HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl`）与 MSVC（venv `_venv-msvc/`）
- GitHub Actions：`ci.yaml` 含 6-cell Windows 矩阵（3.10–3.15，每 push 零回归门）；`win-wheels.yaml` 由 `v*.*-win.N` tag 触发产出 wheel
- 日常验证：`devtools/msys2-bootstrap.sh`（环境契约）；`devtools/check_libhts_objs_lockstep.py`（MSVC mirror lockstep）

## 上下文文档

- `.planning/PROJECT.md` — 项目定义、需求、决策日志、约束
- `.planning/ROADMAP.md` — v1 全部 5 phase 完成
- `.planning/milestones/` — v1 归档（含 v1-MILESTONE-AUDIT.md、v1-phases/）
- `.planning/RETROSPECTIVE.md` — v1 复盘与 v2 候选
- `.planning/research/SUMMARY.md` — 调研综合结论
- `.planning/codebase/CONCERNS.md` — 10 项排序的 Windows 移植障碍
