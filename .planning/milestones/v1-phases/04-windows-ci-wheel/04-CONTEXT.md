# Phase 4: Windows CI 与 wheel 分发 - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — infrastructure phase)

<domain>
## Phase Boundary

CI 持续产出经清洁机冒烟测试把关的自包含 `win_amd64` wheel，经 fork 渠道发布 — Windows 用户 `pip install` 即可用。(CI-01: GitHub Actions windows-latest 手工 build+pytest job 全绿，验证后接入 cibuildwheel；CI-02: cibuildwheel 产出 delvewheel 修复的自包含 wheel，清洁机安装冒烟为发布门槛，fork GitHub Releases 分发；CI-03: Python 3.10–3.15 全矩阵覆盖，python_requires 对齐上游。)

NOT in this phase: PyPI 官方包名（上游配合，另行推动）、远程 I/O（v2）、32-bit（不支持）。

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — infrastructure phase (autonomous smart-discuss). Use ROADMAP success criteria, REQUIREMENTS.md CI-01/02/03, pre-registered research, and carried context below.

</decisions>

<code_context>
## Existing Code Insights

### Carried context (binding facts from prior phases)
- **MSVC 构建就位（Phase 3）**：setup.py 两级分派；MSVC 路径零 autotools（预烘焙 config.h.msvc + 52-TU 显式清单）；win32/msvc/ shim + 四棵 vendor 树；双工具链同树全绿（各 1028/15/0）。CI 的 build+pytest job 应走 MSVC 路径（决策 1：wheel 只发 MSVC）。
- **上游调研（UPSTREAM-PRS.md）**：jmarshall 明示 delvewheel 修复的 wheel 可接受；上游 PR #1400 的 setup-python+cygpath+msys2 CI 配方是 UCRT64 验证参考（但 wheel 路线是 MSVC + cibuildwheel，不依赖 MSYS2）。
- **预注册研究（STACK.md）**：cibuildwheel 4.2.1（delvewheel 自 4.0.0 为 Windows 默认修复命令）、delvewheel 1.13.1、msys2/setup-msys2@v2；pyproject.toml 已有 cibuildwheel 配置（test-requires pytest）。
- **发布门槛形态（ROADMAP SC-3）**：清洁 Windows 机器安装 wheel + import + 打开 BAM 冒烟通过才允许发布 —— devtools/smoke_test.py（D-04）即为此设计，可复用为清洁机门。
- **fork 渠道**：origin = forrestzhang/pysam；Releases 发布用 gh CLI（已授权 REST 代用先例 D-12）。
- **CI 纪律（既有）**：ci.yaml ubuntu/macos 每 push 零回归门；BSD advisory；gh 未认证时 REST 代用（D-12）。

### Reusable Assets
- `devtools/smoke_test.py`（Phase 1 D-04，清洁机门的既定载体）
- `pyproject.toml` cibuildwheel 配置骨架、`ci.yaml`/`release.yaml` 既有 workflow 结构
- `devtools/msvc-build.md`（MSVC 构建纪律文档 —— CI job 的构建步骤蓝本）
- Phase 2/3 的对账文档形态（02-TEST02-RECONCILIATION.md）作 CI 矩阵验证记录模板

### Integration Points
- `.github/workflows/ci.yaml`（Windows job 接入点）+ 新 wheel workflow（cibuildwheel + delvewheel + 清洁机门 + Releases）
- `pyproject.toml`（CIBW_* 配置扩展：win_amd64 matrix、before-build、test-command）
- MSVC 构建的 CI 可行性注意：runner 上 VS Build Tools 预装（windows-latest 自带）；vendor 树已在 repo（无需网络下载依赖 —— 03-02 已 vendor，但注意 CI 的 checkout 即含 vendor/）

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure path; carried context above is the binding input set.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure path; no grey-area discussion held.

</deferred>
