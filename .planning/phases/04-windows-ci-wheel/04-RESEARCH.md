# Phase 4: Windows CI 与 wheel 分发 - Research

**Researched:** 2026-10-13
**Domain:** GitHub Actions Windows CI + cibuildwheel/delvewheel wheel 打包分发
**Confidence:** HIGH（核心链路经本地端到端实证：cibuildwheel 构建 → delvewheel 修复 → 清洁 venv 安装 → smoke 全绿）

## Summary

本次研究的核心是用**本地端到端探针**替代推测：在隔离环境（`%TEMP%\gsd-cibw-venv`，cibuildwheel 4.2.1 = release.yaml 现行 pin）跑了一次 `cp313-win_amd64` 本地 cibuildwheel 构建。结果链条完整：MSVC 路径在 `pip wheel` 式非 inplace 构建下**一次通过**（含强制符号门，CR-01/D-17 遗留疑虑就此关闭——探针 exit 0，implib 正确发射到 `build/lib.win-amd64-cpython-313/pysam/*.lib`）；产出的 wheel（`pysam-0.24.1-cp313-cp313-win_amd64.whl`，3.0 MB，13 个 .pyd，**零 DLL 文件**）；delvewheel 修复在 `--ignore-existing` 下通过（"no external dependencies are needed"，1.13.1 与 1.13.2 双版本验证）；清洁 venv `pip install` + `python devtools/smoke_test.py` **全绿**（import 解析到 site-packages、samtools view 生成 BAM、AlignmentFile 读回 24 条、bcftools view 44118 行）。

两个实证发现直接决定 CI-02 形态：**(1)** pyproject.toml 的 POSIX cibuildwheel 钩子在 Windows 原样执行并立即失败（`install-prerequisites.sh` 在 cmd.exe 下 0.02 秒报错），必须用 `CIBW_BEFORE_ALL_WINDOWS` / `CIBW_BEFORE_BUILD_WINDOWS` / `CIBW_REPAIR_WHEEL_COMMAND_WINDOWS` 环境变量覆盖——且 `test-command` 没有平台后缀变体，Windows 专属测试命令只能在独立 workflow 里用 `CIBW_TEST_COMMAND` 覆盖；**(2)** delvewheel 默认修复在 pysam 的跨模块 .pyd 导入（libcutils→libcsamtools/libcbcftools，各消费者→libchtslib）上必然崩溃 `FileNotFoundError: Unable to find library: libchtslib.cp313-win_amd64.pyd`——根因是 delvewheel 源码只在传 `--ignore-existing` 时才构建 wheel 内文件 casemap（`_wheel_repair.py`: `if ignore_existing: ... else: None`），修复命令必须加该标志。全部 13 个 .pyd 的导入表实证：外部依赖仅 `python313.dll`、`VCRUNTIME140.dll`、UCRT `api-ms-win-crt-*`、`KERNEL32.dll`、`WS2_32.dll`——无 vendor DLL（全静态达成）、无 `msvcrt.dll`（反模式审计通过）、无 `vcruntime140_1.dll`。

runner 侧关键事实：`windows-latest` 自 2026 年 6 月起已是 Windows Server 2025 + **Visual Studio 2026** 镜像（与本机 VS 2026 BuildTools 18.4.1/toolset 14.50 同代——本地探针对 runner 保真度高）；Python 3.15.0 final 已于 2026-10-09 发布，setup-python 直接用 `'3.15'`；符号门需要 `llvm-nm`，runner 上用 `msys2/setup-msys2@v2`（`release: false` 复用镜像自带 C:\msys64）装 `mingw-w64-ucrt-x86_64-llvm-tools` 再 `GITHUB_PATH` 注入。

**Primary recommendation:** ci.yaml 新增**独立** `windows` direct job（不动既有 `direct` job，加法式零回归）；新建独立 Windows wheel workflow（cibuildwheel@v4.3.1 + 三项 CIBW_WINDOWS 覆盖 + `--ignore-existing` 修复命令 + CIBW_TEST_COMMAND=smoke），job 链 build → artifact → 清洁安装 smoke 门 → `gh release create`（job 级 `permissions: contents: write`），fork tag 建议 `v0.24.1-win.1` 形态。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

CONTEXT.md 无锁定决策（infrastructure phase，autonomous smart-discuss 生成）。以下 carried context 为绑定输入（节选自 04-CONTEXT.md `## Existing Code Insights`）：

- **MSVC 构建就位（Phase 3）**：setup.py 两级分派；MSVC 路径零 autotools（预烘焙 config.h.msvc + 52-TU 显式清单）；win32/msvc/ shim + 四棵 vendor 树；双工具链同树全绿（各 1028/15/0）。CI 的 build+pytest job 应走 MSVC 路径（决策 1：wheel 只发 MSVC）。
- **上游调研（UPSTREAM-PRS.md）**：jmarshall 明示 delvewheel 修复的 wheel 可接受；上游 PR #1400 的 setup-python+cygpath+msys2 CI 配方是 UCRT64 验证参考（但 wheel 路线是 MSVC + cibuildwheel，不依赖 MSYS2）。
- **预注册研究（STACK.md）**：cibuildwheel 4.2.1（delvewheel 自 4.0.0 为 Windows 默认修复命令）、delvewheel 1.13.1、msys2/setup-msys2@v2；pyproject.toml 已有 cibuildwheel 配置（test-requires pytest）。
- **发布门槛形态（ROADMAP SC-3）**：清洁 Windows 机器安装 wheel + import + 打开 BAM 冒烟通过才允许发布 —— devtools/smoke_test.py（D-04）即为此设计，可复用为清洁机门。
- **fork 渠道**：origin = forrestzhang/pysam；Releases 发布用 gh CLI（已授权 REST 代用先例 D-12）。
- **CI 纪律（既有）**：ci.yaml ubuntu/macos 每 push 零回归门；BSD advisory；gh 未认证时 REST 代用（D-12）。

### Claude's Discretion

All implementation choices are at Claude's discretion — infrastructure phase (autonomous smart-discuss). Use ROADMAP success criteria, REQUIREMENTS.md CI-01/02/03, pre-registered research, and carried context above.

### Deferred Ideas (OUT OF SCOPE)

None — infrastructure path; no grey-area discussion held.（PyPI 官方包名、远程 I/O、32-bit 均不在本 phase，见 REQUIREMENTS.md Out of Scope。）
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CI-01 | Windows CI — GitHub Actions 增加 `windows-latest` runner（先手工 build+pytest job，验证后接入 cibuildwheel） | ci.yaml 独立 windows job 蓝图（Pattern 1）：shell: bash、llvm-nm 供给步骤、`python setup.py build` 自动走 MSVC 臂（IS_MSVC_PYTHON 对 win-amd64 CPython 自动触发）、PYTHONPATH 指向 build/lib.win-amd64-*；本地冷构建 ~7 分钟/版本实测 |
| CI-02 | wheel 分发 — MSVC 产出自包含 `win_amd64` wheel，delvewheel 修复 + 清洁机安装冒烟测试作为发布门槛，经 fork 渠道（GitHub Releases）分发 | 本地端到端实证链：cibuildwheel cp313 构建 exit 0 → delvewheel `--ignore-existing` 修复 → 清洁 venv 安装 + smoke_test.py 全绿；13 个 .pyd 导入表证明自包含；GitHub Releases 发布 job 蓝图（Pattern 3/4） |
| CI-03 | Python 版本对齐 — wheel 覆盖上游支持面（3.10–3.15，以 `python_requires` 为准） | in-tree `requires-python = ">=3.9"`（pyproject.toml:8）；cibuildwheel 4.2.1 `--print-build-identifiers` 实测 cp310–cp315-win_amd64 全部可选（cp39/cp314t/cp315t 亦在但按 CI-03 取 3.10–3.15）；setup-python `'3.15'` 已是 stable（3.15.0 final 2026-10-09） |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| 每 push Windows 构建验证（build+pytest） | GitHub Actions ci.yaml（windows direct job） | — | 零回归纪律要求每 push 门；本地 Phase 3 已证 MSVC 构建可复现，CI 只是把它搬上 runner |
| 多版本 wheel 生产 | 新 Windows wheel workflow（cibuildwheel） | pyproject.toml（钩子来源，需 env 覆盖） | cibuildwheel 负责 nuget CPython 安装、隔离构建、修复、测试；pyproject 保持 POSIX 纯净 |
| wheel 修复（delvewheel） | cibuildwheel 内置修复步骤（CIBW_REPAIR_WHEEL_COMMAND_WINDOWS 覆盖） | — | 自包含性由"全静态 vendor + VC runtime 由 CPython 提供"达成；delvewheel 是验证器而非 DLL 打包器 |
| 发布门槛（清洁机冒烟） | 独立 smoke job（artifact 下载 + 全新 venv 安装） | cibuildwheel 内建 test 步骤（轻量 smoke） | "清洁机"语义 = 与构建 job 无共享状态的消费者 job；SC-3 的字面要求 |
| fork 渠道发布 | release job（gh release create，GITHUB_TOKEN） | artifactname.py 命名约定 | Releases 是 fork 分发的既定渠道；权限最小化在 job 级声明 |
| 测试数据（BAM/VCF）供给 | job 内 checkout 的 tests/pysam_data | — | smoke_test.py 从脚本位置解析 repo root（smoke_test.py:29-30），checkout 即得；wheel 本身不含测试数据 |

## Standard Stack

### Core

| Library/Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cibuildwheel | **4.2.1**（release.yaml 现行 pin）/ 最新 **4.3.1**（2026-10-10） | Windows wheel 构建编排（nuget CPython + 隔离构建 + delvewheel + 测试） | pypa 官方工具；上游 release.yaml 已 pin `pypa/cibuildwheel@v4.2.1`（release.yaml:35）；4.3.1 将 CPython 3.15 更新到 final（4.2.1 锁 rc2）。本地探针在 4.2.1 完整跑通 [VERIFIED: 本地探针 2026-10-13] |
| delvewheel | 1.13.1（cibuildwheel 4.2.1 constraints pin）/ 1.13.2 | wheel 修复与自包含性验证 | cibuildwheel ≥4.0 的 Windows 默认修复命令（探针日志实证默认命令 `delvewheel repair -w {dest_dir} -v {wheel}` + 自动安装 delvewheel 1.13.1）；`--ignore-existing` 是跨模块 .pyd 导入的必需标志（1.13.1/1.13.2 双验证）[VERIFIED: 本地探针 + delvewheel 源码阅读 2026-10-13] |
| `msys2/setup-msys2` GHA action | v2 | runner 上供给 `llvm-nm`（符号门必需） | 预注册 STACK.md 选项；`release: false` 复用镜像自带 C:\msys64，`install: mingw-w64-ucrt-x86_64-llvm-tools`（与本地开发环境同包）[CITED: github.com/msys2/setup-msys2 README] |
| gh CLI | runner 预装 | fork Releases 发布（`gh release create`） | [ASSUMED]（runner 镜像标准组件，未在本会话对照镜像清单核实；本地 gh 已认证 forrestzhang 账号——探针期间 `gh auth status` 实证） |

### Supporting

| Library/Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| actions/checkout@v7, actions/setup-python@v7, actions/upload-artifact@v7, actions/download-artifact@v8 | 既有 in-repo pins | workflow 步骤 | 沿用 ci.yaml/release.yaml 既有版本族，保持仓库一致性 [VERIFIED: .github/workflows/ci.yaml:17,22,73 / release.yaml:104] |
| `devtools/smoke_test.py` | 既有（Phase 1 D-04） | 清洁机门载体 + cibuildwheel 测试命令 | 88 行独立脚本，4 步验证（dispatch 生成 BAM / BGZF magic / htslib 读回 / bcftools dispatch），退出码非零即失败 [VERIFIED: devtools/smoke_test.py 全文阅读] |
| `devtools/artifactname.py` | 既有 | wheel artifact 命名（`wheels-win_amd64-AMD64-310-...-315`） | release.yaml:53 既有用法 `devtools/artifactname.py wheelhouse/*.whl >> $GITHUB_ENV` |
| pytest | 既有（test-requires） | direct job 全量测试 | ci.yaml direct job 模式 `PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*) pytest` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| 独立 Windows wheel workflow | 在 release.yaml `build_wheels` matrix 加 `kind: win` | 共用触发器更省文件，但 release.yaml 的 POSIX job 读同一 pyproject 钩子配置，Windows env 覆盖与 `case()` runner 表达式纠缠会抬高零回归风险；独立文件是纯加法。**推荐独立 workflow** |
| cibuildwheel@v4.3.1 | @v4.2.1（与上游 release.yaml 一致） | 4.3.1 才用 3.15.0 final 构建 cp315（4.2.1 锁 3.15.0rc2；ABI 自 rc 已冻结，风险低但不洁）。**fork 的 Windows job 推荐 4.3.1**；上游 POSIX job 的 4.2.1 pin 不动 |
| CIBW_TEST_COMMAND=smoke_test.py | CIBW_TEST_COMMAND=`pytest {project}/tests`（上游默认） | 全量套件 ×6 版本更强但更慢且存在 {project} cwd 源码树遮蔽疑虑（repo 内 pysam/ 目录含 inplace .pyd 时 import 可能命中源码树）；smoke 是 wheel 语境下最保真的最小门。**推荐 smoke**，全量测试由 ci.yaml direct windows job 承担（不同断言面：direct 验证源码树构建，cibuildwheel 验证 wheel 产物） |
| msys2/setup-msys2 供 llvm-nm | choco install llvm / VS Clang 组件路径直取 | choco 重（数百 MB）；VS Clang 路径随镜像漂移。setup-msys2+pacman 与本地开发完全同源（同一 llvm-nm 构建）。**推荐 setup-msys2** |
| gh release create | softprops/action-gh-release 等 action | 第三方 action 引入供应链面；gh CLI 是 GitHub 官方且 release.yaml 生态已在用 gh（D-12 REST 代用先例）。**推荐 gh CLI** |

**Installation:**

```bash
# 本地复现探针（全部隔离，不污染 _venv-msvc）：
D:/miniconda3/python.exe -m venv "$TEMP/gsd-cibw-venv"
"$TEMP/gsd-cibw-venv/Scripts/python.exe" -m pip install cibuildwheel==4.2.1
export PATH="/c/msys64/ucrt64/bin:$PATH"   # llvm-nm（符号门）
# 见 Code Examples 的完整 env 组合
```

CI 侧不需要安装：workflow 用 `pypa/cibuildwheel@vX.Y.Z` action，delvewheel 由 cibuildwheel constraints 自动装入构建 venv [VERIFIED: 探针日志 "Downloading delvewheel-1.13.1"]。

**Version verification（本会话实测）:** cibuildwheel 4.2.1 安装成功且 `pip index versions` 显示最新 4.3.1；delvewheel 本地装 1.13.2、另建 venv 装并以 1.13.1 复验修复成功 [VERIFIED: pip registry + 实跑]。

## Package Legitimacy Audit

> Protocol 输出（`package-legitimacy check --ecosystem pypi`）对三者均判 **SUS**，但 reasons 均为 `too-new`（键于*最新版*发布日期：cibuildwheel 4.3.1 发布于 2026-10-10、delvewheel 1.13.2 发布于 2026-10-09，即昨天）与 `unknown-downloads`（seam 未取到下载量）。这是"最新版刚发布"造成的假阳性，非包本身可疑——两者分别是 pypa 官方工具与 cibuildwheel 官方默认依赖，且上游 pysam release.yaml 已 pin cibuildwheel@v4.2.1（in-repo 权威引用）。处置：保留 + 严格 pin，首个 workflow 上线时 human-verify 一次即可。

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| cibuildwheel | PyPI | 首发约 2018；最新版昨日 | seam 未取到 | github.com/pypa/cibuildwheel | SUS（too-new on latest release） | Approved with pin — 上游 release.yaml:35 已 pin @v4.2.1；fork job pin @v4.3.1 |
| delvewheel | PyPI | 首发约 2021；最新版昨日 | seam 未取到 | github.com/adang1345/delvewheel | SUS（too-new on latest release） | Approved — 经 cibuildwheel constraints 间接安装（1.13.1），不经手直装 |
| pytest | PyPI | 首发约 2009 | seam 未取到 | github.com/pytest-dev/pytest | SUS（unknown-downloads） | Approved — 仓库既有 test-requires，无新增 |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** 上述三者（原因均为最新版发布日期/下载数据缺失的假阳性；无 SLOP；无新增直装依赖——本 phase 零 Python 依赖变更）

## Architecture Patterns

### System Architecture Diagram

```text
                      ┌────────────────────────────────────────────┐
                      │  push 到 win 分支（每 push 触发）            │
                      └──────────────┬─────────────────────────────┘
                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ci.yaml（既有，仅追加 job）                                            │
│                                                                      │
│  [direct: ubuntu/macos ×7]  ←── 零回归门（不动）                       │
│  [system: BSD] [sdist] [conda]      ←── advisory（不动）              │
│  [windows: NEW ──────────────────────────────────────────────────]   │
│   checkout → setup-python(3.10..3.15) → setup-msys2(llvm-tools)      │
│     → GITHUB_PATH += C:\msys64\ucrt64\bin        (llvm-nm)           │
│     → python setup.py build   ──自动──▶  MSVC 臂                      │
│        (IS_MSVC_PYTHON: win-amd64 CPython 即触发)                     │
│        (符号门: llvm-nm 读 build/lib.win-amd64-*/pysam/*.lib)         │
│     → PYTHONPATH=build/lib.win-amd64-* pytest   (1028/15 基线)        │
└──────────────────────────┬───────────────────────────────────────────┘
                           │  CI-01 绿 → 才允许接入（SC-1 顺序约束）
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│ win-wheels.yaml（新 workflow；tag v* / release/* / manual 触发）        │
│                                                                      │
│  build_wheels ──▶ cibuildwheel(cp310..cp315-win_amd64)               │
│     env: CIBW_BEFORE_ALL_WINDOWS / BEFORE_BUILD_WINDOWS = no-op      │
│          CIBW_REPAIR_WHEEL_COMMAND_WINDOWS = delvewheel              │
│              repair --ignore-existing -w {dest_dir} -v {wheel}       │
│          CIBW_TEST_COMMAND = python {project}/devtools/smoke_test.py │
│     ──▶ upload-artifact(wheels-win_amd64-...)                         │
│                           │                                          │
│  clean_smoke（needs build）                                          │
│     download-artifact → setup-python(3.13) → python -m venv tmp      │
│     → venv pip install *.whl → venv python devtools/smoke_test.py    │
│     （SC-3 发布门槛：全新 job/venv，非 editable，import 命中 wheel）    │
│                           │                                          │
│  release（needs clean_smoke；permissions: contents: write）           │
│     gh release create <tag> wheels/*.whl --generate-notes            │
└──────────────────────────┬───────────────────────────────────────────┘
                           ▼
        Windows 用户: pip install https://github.com/forrestzhang/pysam/
                      releases/download/<tag>/pysam-...-win_amd64.whl
        （VCRUNTIME140.dll/UCRT 由 CPython 自带 —— 导入表实证无其他外部依赖）
```

### Recommended Project Structure

```text
.github/workflows/
├── ci.yaml            # + 独立 windows job（不动 direct/system/sdist/conda）
└── win-wheels.yaml    # 新：cibuildwheel + 清洁 smoke 门 + Releases 发布
pyproject.toml         # 不改（Windows 覆盖全部走 workflow env —— POSIX 零回归）
devtools/
├── smoke_test.py      # 既有，双职：cibuildwheel 测试命令 + 清洁机门
└── artifactname.py    # 既有，artifact 命名
```

### Pattern 1: ci.yaml 独立 windows direct job（加法式零回归）

**What:** 在 ci.yaml 追加一个与 `direct` 平行的 `windows` job，而不是往 `direct` 的 `os:` matrix 里塞 windows。
**When to use:** CI-01 落地时。
**Why:** `direct` 的既有步骤按 `runner.os == 'Linux'/'macOS'` 守卫、默认 shell 是 pwsh（windows cell 会挂）、`PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*)` 是 bash 语法——改动共享步骤会波及既有 ubuntu/macos cells，违反零回归最高约束。独立 job 是纯加法。
**Example:** 见 Code Examples 1。

### Pattern 2: Windows cibuildwheel 覆盖全部走 workflow env（pyproject 不动）

**What:** `CIBW_BEFORE_ALL_WINDOWS`、`CIBW_BEFORE_BUILD_WINDOWS`、`CIBW_REPAIR_WHEEL_COMMAND_WINDOWS`、`CIBW_TEST_COMMAND` 在 win-wheels.yaml 的 env 里设置；pyproject.toml 的 `[tool.cibuildwheel]`（POSIX 钩子）一个字不改。
**When to use:** CI-02 的 cibuildwheel job。
**Why:** (a) release.yaml 的 macos/linux wheel job 读同一 pyproject 配置——改它就是把 Windows 语义泄漏进 POSIX 发布路径；(b) 探针实证平台后缀 env 能精确覆盖（probe1 日志：before-build 被覆盖而 before-all 未覆盖时，只有前者变化）。
**关键陷阱:** `test-command` **没有** `CIBW_TEST_COMMAND_WINDOWS` 平台变体——Windows 专属测试命令只能靠独立 workflow 的 env 覆盖（本方案天然满足）。[VERIFIED: 探针 "Build options" 输出 + cibuildwheel options 文档]

### Pattern 3: 清洁机门 = 独立消费 job（SC-3 语义）

**What:** `clean_smoke` job 与构建 job 无任何共享状态：download-artifact 取 wheel → 全新 setup-python → 全新 venv → `pip install <wheel文件>` → `python devtools/smoke_test.py`（脚本形式调用）。
**When to use:** 发布门槛。
**Why:** "清洁 Windows 机器"的可 CI 化语义 = 不继承构建环境的 PATH/venv/构建产物。本地已实证该调用形态 import 命中 site-packages（`pysam from: ...\gsd-cleanroom\Lib\site-packages\pysam\__init__.py`）而非源码树——因为脚本形式调用时 `sys.path[0]` 是脚本目录 devtools/，repo root 不入 path；**必须避免 `python -m` 形式调用**（`-m` 会把 cwd 即 repo root 放进 sys.path，遮蔽 wheel）。[VERIFIED: 本地清洁 venv 实证 2026-10-13]

### Pattern 4: fork Releases 发布（最小权限）

**What:** release job 级声明 `permissions: contents: write`（workflow 顶层保持最小），`gh release create "$TAG" --generate-notes` + `GH_TOKEN: ${{ github.token }}`；tag 用 fork 专属形态 `v0.24.1-win.1`（匹配 release.yaml 既有触发 glob `v[0-9]+.*`；fork remote 现无任何 v0.2x tag，无碰撞——`git ls-remote --tags origin` 仅见 `0.2`/`0.2_release`/`v0.1.1`/`v0.1.2`）。[VERIFIED: git ls-remote 2026-10-13]
**When to use:** CI-02 的发布步骤。
**Why:** GITHUB_TOKEN 默认权限不足以建 release（403 "Resource not accessible by integration"）；job 级声明实现最小授权 [CITED: 多个 workflow 实例与 issue]。tag 名经 env 间接传入 run: 块防 `github.ref` 注入。

### Anti-Patterns to Avoid

- **改 pyproject.toml 的 cibuildwheel 段适配 Windows**：泄漏进 POSIX wheel 流程（零回归红线）。用 workflow env 平台后缀覆盖。
- **`python -m devtools.smoke_test` 形式跑清洁门**：cwd=repo root 进 sys.path，源码树（含 inplace .pyd）遮蔽 wheel，测试无效。用 `python devtools/smoke_test.py` 脚本形式。
- **在 cibuildwheel 里跑 `pytest {project}/tests` 当 Windows wheel 门**（不经处理直接沿用上游默认）：源码树遮蔽疑虑 + 6 版本×全量耗时；smoke 已足够作 wheel 产物门，全量归 direct job。
- **`shell: msys2 {0}` 里跑 cibuildwheel**（PITFALLS.md W11）：cibuildwheel 自己起 cmd 子进程，PATH 混用引发 gcc/MSVC 混淆。MSYS2 只装包不进 shell。
- **手写 DLL 打包/`os.add_dll_directory` 补丁替代 delvewheel**：wheel 已实证零外部 DLL 依赖，不需要；delvewheel 留作持续验证器。
- **commit 带 `Co-Authored-By` trailer**（CLAUDE.md 反模式）。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 多版本 CPython 安装 + 隔离构建 + 产物收集 | per-version setup-python × pip wheel × 手动收集 | cibuildwheel | nuget CPython 安装、build 隔离、delvewheel、测试编排全是它的职责 [VERIFIED: 探针全程] |
| DLL 依赖分析与 vendoring | 手拷 DLL 进 wheel + 改 `__init__.py` | delvewheel（`--ignore-existing`） | PE 导入表解析、mangle、补丁逻辑边界极多；且本项目实况是"零外部依赖"，delvewheel 是免费的自包含性证明器 |
| runner 上 llvm-nm 供给 | 手下载 LLVM zip/解压/PATH | msys2/setup-msys2@v2 + `release: false` + GITHUB_PATH | 与本地开发同源同版本；镜像自带 MSYS2 复用零下载 |
| MSVC 环境激活 | vcvars/msvc-dev-cmd 步骤 | 什么都不做（setuptools `_get_vc_env` 自动定位） | Phase 3 已证"零 MSVC 环境的 Git Bash 是 canonical 调用"（msvc-build.md:26-29）；STACK.md 的 ilammy/msvc-dev-cmd 建议被 Phase 3 事实取代 |
| artifact 命名 | 拼字符串 | devtools/artifactname.py | release.yaml:53 既有约定，跨 job 一致 |
| 清洁机冒烟脚本 | 新写 CI 专用测试 | devtools/smoke_test.py | D-04 即为此设计；本地已实证 wheel 语境可用 |

**Key insight:** Phase 1–3 已把全部构建智能沉进 setup.py（MSVC 臂零 autotools、符号门、/DEF 导出）；Phase 4 是纯编排层——任何"为 CI 改构建代码"的冲动都应该先怀疑是 Phase 3 遗留缺陷（探针证明没有：MSVC 臂在 cibuildwheel 构建隔离下零改动通过）。

## Runtime State Inventory

> 本 phase 非重命名/重构/迁移 phase（additive CI 基建），按协议略。唯一相关运行态：本地探针产物全部落在 `%TEMP%`（gsd-cibw-venv / gsd-cibw-wheelhouse / whl-bin / dv-out* / gsd-cleanroom）与 repo 的 gitignored `build/` 目录，工作树验证干净（`git status --porcelain` 仅既有 `.planning/tmp/`）。无需迁移。

## Common Pitfalls

### Pitfall 1: POSIX cibuildwheel 钩子在 Windows 原样执行（已实证）

**What goes wrong:** pyproject.toml 的 `before-all = "{project}/devtools/install-prerequisites.sh ..."` 与 `before-build = "make -C {project}/htslib distclean"` 在 windows cibuildwheel 下经 cmd.exe 执行，前者 0.02 秒失败（`'.' 不是内部或外部命令`）。[VERIFIED: 本地探针第一次运行实失败输出]
**Why it happens:** cibuildwheel 的钩子是跨平台的；平台专属覆盖不写就全局生效。
**How to avoid:** `CIBW_BEFORE_ALL_WINDOWS` 与 `CIBW_BEFORE_BUILD_WINDOWS` 设为显式 no-op（如 `echo ...`）。MSVC 臂零 autotools，distclean 本就无意义（setup.py:800-812 每次运行重写 config.h）。
**Warning signs:** Windows cibuildwheel job 在 before-all 秒挂 + cmd 乱码报错。

### Pitfall 2: delvewheel 默认修复遇跨模块 .pyd 导入崩溃（已实证 + 已解）

**What goes wrong:** `FileNotFoundError: Unable to find library: libchtslib.cp313-win_amd64.pyd`。pysam 消费者 .pyd 经 Phase 3 implib 绑定导入兄弟 .pyd；delvewheel 默认只搜 PATH（casemap 仅在 `--ignore-existing` 时构建——1.13.1/1.13.2 源码同构）。[VERIFIED: 探针失败 + `_wheel_repair.py` 源码 + 双版本修复实验]
**How to avoid:** `CIBW_REPAIR_WHEEL_COMMAND_WINDOWS: delvewheel repair --ignore-existing -w {dest_dir} -v {wheel}`。两个版本实测输出 `no external dependencies are needed`。
**Warning signs:** 修复步骤 FileNotFoundError 且库名以 `.pyd` 结尾。

### Pitfall 3: 源码树遮蔽 wheel 测试

**What goes wrong:** 从 repo root 以会加入 cwd 的方式（`python -m`）跑测试时，`import pysam` 命中源码树（含 inplace 构建的 .pyd）而非已装 wheel——清洁门变成假测试。
**How to avoid:** 脚本形式 `python devtools/smoke_test.py`（sys.path[0]=脚本目录）；本地清洁 venv 实证 import 命中 site-packages。
**Warning signs:** 测试通过得可疑地顺利 / `pysam.__file__` 指向 repo。

### Pitfall 4: 符号门需要 llvm-nm 且 win32 上不允许静默跳过

**What goes wrong:** `_nm_command()` win32 返回 `["llvm-nm", "-g", "-P"]`（setup.py:173-174）；runner 默认 PATH 无 llvm-nm → 构建在符号门以 CalledProcessError 终止（win32 分支在异常吞噬包装之外，setup.py:509-518——这是设计）。[VERIFIED: setup.py 阅读]
**How to avoid:** setup-msys2（`release: false`，`install: mingw-w64-ucrt-x86_64-llvm-tools`）→ `"${{ steps.msys2.outputs.msys2-location }}\ucrt64\bin" >> $GITHUB_PATH`。cibuildwheel/构建子进程继承父 env，无需 CIBW_ENVIRONMENT。
**Warning signs:** 构建日志止于 llvm-nm 调用。

### Pitfall 5: windows-latest 镜像漂移（VS2026 切换已发生）

**What goes wrong:** 2026-06 起 windows-latest = Windows Server 2025 + **VS 2026**（toolset v145 + v143 back-compat）；旧假说"VS 2022 稳定默认"过时。本地是 VS 2026 BuildTools 18.4.1（toolsets 14.44+14.50，msvc-build.md:19-20），探针实际用 14.50.35717 编译——与 runner 同代，保真度高。[CITED: actions/runner-images issue #14017；VERIFIED: 探针日志 cl.exe 路径含 `Visual Studio\18\BuildTools\...\14.50.35717`]
**How to avoid:** 接受 windows-latest（与本地同代）；CI-01 direct job 是 runner 工具链漂移的检测器——它先绿才谈 wheel。
**Warning signs:** 仅 runner 上出现的 cl ICE（本地无）——此时考虑 pin `windows-2025` 具体镜像标签排查。

### Pitfall 6: pwsh 默认 shell × bash 语法

**What goes wrong:** windows job 的 run 步骤默认 pwsh；`PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*)` 这类 bash 语法直接挂；构建产物目录名也不同（`build/lib.win-amd64-cpython-313` vs `build/lib.linux-x86_64-cpython-313`）。
**How to avoid:** windows job `defaults: run: shell: bash`（runner 预装 Git Bash [ASSUMED——镜像标准组件，首跑即证]），或每步显式 `shell: bash`。

### Pitfall 7: python_requires 与矩阵面的语义差

**What goes wrong:** in-tree `requires-python = ">=3.9"`（pyproject.toml:8）允许 3.9，但 CI-03/ROADMAP 锁定 Windows wheel 面 = 3.10–3.15（3.9 已 EOL）。不构建 cp39 wheel 不违反元数据（cp310+ wheel 在 3.9 解释器上因 tag 不匹配不被选中），但若有人期望"以 python_requires 为准=含 3.9"会产生分歧。
**How to avoid:** 按 CI-03 文本取 cp310–cp315；不改 `requires-python`（改了才真正影响 POSIX 发布）。cibuildwheel 实测四版本标识符全在。遗留选择见 Open Questions Q4。
**Warning signs:** 评审时有人把"python_requires 对齐上游"读成"矩阵含 3.9"。

### Pitfall 8: GITHUB_TOKEN 权限与 tag 注入

**What goes wrong:** `gh release create` 403（默认 token 无 contents:write）；`run: gh release create ${{ github.ref_name }}` 形式存在 tag 名 shell 注入面。
**How to avoid:** release job 级 `permissions: contents: write`；tag 名经 `env: TAG: ${{ github.ref_name }}` 间接引用 [CITED: GitHub Actions 权限文档/社区实例]。既有两 workflow 顶层 `permissions: {}` 纪律（ci.yaml:5, release.yaml:10）延续到新文件。

### Pitfall 9: 浪费在"为 CI 改 setup.py"上

**What goes wrong:** 把 runner 差异误判为构建代码缺陷去动 setup.py，波及双工具链。
**How to avoid:** 探针已证 MSVC 臂在 cibuildwheel 构建隔离（最新 setuptools/Cython 解析）下零改动全链路通过。runner 上的任何失败先怀疑环境供给（llvm-nm、镜像），再怀疑代码。

## Code Examples

### Example 1: ci.yaml 独立 windows direct job（CI-01）

```yaml
# Source: 基于 ci.yaml 既有 direct job 结构 + 探针实证的 MSVC 构建事实
  windows:
    runs-on: windows-latest
    defaults:
      run:
        shell: bash          # pwsh 默认会挂 bash 语法（Pitfall 6）
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13', '3.14', '3.15']
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python-version }}
      - name: Provision llvm-nm for the BUILD-03 symbol gate
        uses: msys2/setup-msys2@v2
        id: msys2
        with:
          msystem: UCRT64
          release: false                       # 复用镜像自带 C:\msys64
          update: false
          install: mingw-w64-ucrt-x86_64-llvm-tools
      - run: echo "${{ steps.msys2.outputs.msys2-location }}\ucrt64\bin" >> "$GITHUB_PATH"
      - run: pip install Cython mypy pytest setuptools
      - run: python setup.py build             # win-amd64 CPython → 自动 MSVC 臂
      - run: PYTHONPATH=$(echo $GITHUB_WORKSPACE/build/lib.*) pytest
```

### Example 2: win-wheels.yaml 构建核心 env（CI-02，探针原样验证过的组合）

```yaml
# Source: 本地探针两次运行的实证 env 组合（2026-10-13，cibuildwheel 4.2.1）
      - name: Build wheels
        uses: pypa/cibuildwheel@v4.3.1
        env:
          CIBW_BUILD: "cp310-* cp311-* cp312-* cp313-* cp314-* cp315-*"
          CIBW_ARCHS: AMD64
          # 三项 Windows 覆盖（Pitfall 1/2）；pyproject POSIX 钩子保持原样
          CIBW_BEFORE_ALL_WINDOWS: "echo no before-all on Windows (MSVC path self-contained)"
          CIBW_BEFORE_BUILD_WINDOWS: "echo skipping make distclean (MSVC path has no autotools artifacts)"
          CIBW_REPAIR_WHEEL_COMMAND_WINDOWS: "delvewheel repair --ignore-existing -w {dest_dir} -v {wheel}"
          # test-command 无平台后缀变体 —— 独立 workflow 内整单覆盖（Pitfall 2/Pattern 2）
          CIBW_TEST_COMMAND: "python {project}/devtools/smoke_test.py"
          CIBW_ENVIRONMENT: ""                 # 显式置空，防 POSIX 段污染
          CIBW_BUILD_VERBOSITY: "1"
```

### Example 3: 清洁机门 job（SC-3）+ 发布 job（Pattern 4）

```yaml
# Source: 本地清洁 venv 实证的调用形态（gsd-cleanroom 实跑 smoke OK）
  clean_smoke:
    needs: build_wheels
    runs-on: windows-latest
    defaults: { run: { shell: bash } }
    steps:
      - uses: actions/checkout@v7
        with: { persist-credentials: false }
      - uses: actions/setup-python@v7
        with: { python-version: '3.13' }
      - uses: actions/download-artifact@v8
        with: { name: wheels-win_amd64, path: dist }   # artifactname.py 命名
      - run: python -m venv "$RUNNER_TEMP/cleanroom"
      - run: "$RUNNER_TEMP/cleanroom/Scripts/python.exe" -m pip install dist/*.whl
      - run: "$RUNNER_TEMP/cleanroom/Scripts/python.exe" devtools/smoke_test.py
        # 脚本形式调用 —— sys.path[0]=devtools/，import 命中已装 wheel（Pitfall 3）

  release:
    needs: clean_smoke          # 发布门槛：清洁机冒烟通过才允许发布
    runs-on: ubuntu-latest
    permissions:
      contents: write           # job 级最小授权（Pitfall 8）
    steps:
      - uses: actions/download-artifact@v8
        with: { name: wheels-win_amd64, path: dist, merge-multiple: true }
      - run: gh release create "$TAG" dist/*.whl --generate-notes --target "$GITHUB_SHA"
        env:
          GH_TOKEN: ${{ github.token }}
          TAG: ${{ github.ref_name }}   # env 间接引用防注入
```

### Example 4: 探针实证记录（可信度锚点）

```text
# Source: 本地探针输出（2026-10-13，D:/Github/pysam，VS 2026 BuildTools toolset 14.50.35717）
Successfully built pysam-0.24.1-cp313-cp313-win_amd64.whl      # ~7 min 冷构建（含 nuget CPython 3.13.15 下载）
FileNotFoundError: Unable to find library: libchtslib.cp313-win_amd64.pyd   # 默认修复（修前）
no external dependencies are needed                            # delvewheel repair --ignore-existing（修后，1.13.1+1.13.2 双验证）
wheel copied to ...pysam-0.24.1-cp313-cp313-win_amd64.whl
[smoke] 1/4 samtools view -b ... / 2/4 verify BGZF magic bytes / 3/4 ... 24 alignments read / 4/4 ... 44118 vcf lines
smoke OK                                                       # 清洁 venv（gsd-cleanroom）安装后
pysam from: C:\Users\forre\AppData\Local\Temp\gsd-cleanroom\Lib\site-packages\pysam\__init__.py
# 全部 13 个 .pyd 导入表（llvm-objdump -p，外部 DLL 仅）：python313.dll / VCRUNTIME140.dll /
#   api-ms-win-crt-*.dll / KERNEL32.dll / WS2_32.dll（libchtslib 独有）—— 无 vendor DLL，无 msvcrt.dll
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手动 `pip install delvewheel` + 自写 CIBW_REPAIR 命令 | cibuildwheel ≥4.0 默认 `delvewheel repair -w {dest_dir} -v {wheel}` | 2025（4.0.0） | 只需在默认命令上加 `--ignore-existing` |
| STACK.md 建议 `ilammy/msvc-dev-cmd` 激活 MSVC | setuptools `_get_vc_env` 自动定位（vswhere），零环境步骤 | Phase 3 实证（2026-10） | CI 少一个步骤、少一个第三方 action |
| windows-latest = VS 2022 | windows-latest = Windows Server 2025 + VS 2026 | 2026-06（runner-images #14017） | 与本地 VS 2026 同代；旧文档/记忆里的 VS2022 假说过时 |
| setup-python `'3.15-dev'` / allow-prereleases | `'3.15'` 直取 stable | 2026-10-09（3.15.0 final + actions/python-versions 收录） | Windows 矩阵直接写 `'3.15'`；ci.yaml 既有 POSIX cells 的 `'3.15-dev'` 不必动（dev 串自动解析到 final） |
| cibuildwheel 4.2.1（CPython 3.15.0rc2 pin） | 4.3.1（2026-10-10，3.15.0 final） | 2026-10-10 | fork Windows job 用 4.3.1 得到干净 final 构建 |

**Deprecated/outdated:**
- `ilammy/msvc-dev-cmd` 依赖假说（本项目语境）——被 Phase 3"零 MSVC 环境构建"事实取代。
- "windows-2022 是稳定默认"（STACK.md）——已被镜像迁移取代。

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | windows runner 预装 Git Bash 且 `shell: bash` 可用 | Pattern 1 / Pitfall 6 | 低（镜像长期标准组件；CI-01 job 首跑即证） |
| A2 | gh CLI 预装于 windows/ubuntu runner | Standard Stack / Pattern 4 | 低（同上；D-12 REST 代用是既有回退路径） |
| A3 | runner 冷构建耗时 ~7–15 分钟/Python 版本（本地 4 核 ~7 min 实测外推） | CI-01 / 摘要 | 低——只影响 job 时长预估；6 版本串行 30–90 分钟在 release 触发下可接受 |
| A4 | fork tag 形态 `v0.24.1-win.1`（`git ls-remote` 证 fork remote 无 v0.2x tag 无碰撞，但命名本身是提案） | Pattern 4 / Open Q2 | 低——执行期 human 确认一次 |
| A5 | conda 版 CPython 亦自带 VCRUNTIME140.dll（清洁门按 python.org CPython 设计，conda 非门内承诺） | 自包含性结论 | 极低——wheel 的消费者基线是 python.org CPython；conda 用户若遇缺 DLL 属上游生态问题 |
| A6 | cp310–cp314 各版本将复现 cp313 探针结果（仅 cp313 实建） | CI-02 | 低——cpython 版本间构建差异极小（同一 setup.py 臂）；CI 矩阵本身就是验证 |

## Open Questions (RESOLVED)

1. **cibuildwheel 内建测试的强度（smoke vs 全量 pytest）**
   - What we know: 全量套件 Windows ~快（Phase 2/3 本地常态跑）；smoke 已实证 wheel 语境可用；`pytest {project}/tests` 在 {project} cwd 有源码树遮蔽疑虑（本地 repo 内有 inplace .pyd；runner 的 checkout 无 .pyd——inplace 产物不进 git——所以 runner 上 pytest 实际测的是 wheel，疑虑仅存在于本地复现场景）。
   - What's unclear: 6 版本 × 全量的 runner 耗时。
   - Recommendation: 先 smoke（本方案）；direct windows job 全绿后可作为后续增强把 CIBW_TEST_COMMAND 升级为 pytest。
2. **fork tag 命名**
   - What we know: fork remote 现无 v0.2x tag；release.yaml 触发 glob `v[0-9]+.*`。
   - Recommendation: `v0.24.1-win.1`（版本-win.序号）；执行期确认。
3. **cibuildwheel action 版本（fork Windows job pin @v4.3.1 vs 与上游一致的 @v4.2.1）**
   - What we know: 4.3.1 才含 3.15.0 final（4.2.1 是 rc2；ABI 已冻结，功能等价）。
   - Recommendation: fork 独立 workflow pin @v4.3.1；上游 POSIX job 不动。
4. **cp39 wheel 是否补建（超出 CI-03 文本，回应 Pitfall 7 的另一读法）**
   - Recommendation: 不建（3.9 EOL、CI-03 锁 3.10–3.15）；若用户在执行期要求补齐再加一个 CIBW_BUILD cell 即可，成本 ~10 分钟 CI。
5. **direct windows job 矩阵宽度（6 版本 vs 子集）**
   - What we know: 上游 direct 对每 OS 跑全版本；本地 MSVC 构建每版本 ~7–15 min。
   - Recommendation: 6 版本全矩阵（与 CI-03 面一致，parallel job 无墙钟惩罚）。

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| VS Build Tools（C++ workload） | MSVC 构建（CI-01/02） | ✓ 本地 | VS 2026 BuildTools 18.4.1，toolsets 14.44+14.50（msvc-build.md:19-20；探针实际用 14.50.35717） | runner 自带 VS 2026（同代） |
| cibuildwheel | wheel 构建 | ✓ 本地（隔离 venv） | 4.2.1（= release.yaml pin）；最新 4.3.1 | `python -m cibuildwheel` / action |
| delvewheel | wheel 修复 | ✓（cibuildwheel constraints 自动装 1.13.1；本地 1.13.1/1.13.2 双验） | 1.13.1/1.13.2 | — |
| llvm-nm（UCRT64 llvm-tools） | 符号门 | ✓ 本地 /c/msys64/ucrt64/bin | LLVM（GNU nm 兼容版） | runner: setup-msys2 `release: false`（镜像自带 C:\msys64） |
| gh CLI | Releases 发布 | ✓ 本地（forrestzhang 已认证） | — | runner 预装 [ASSUMED A2]；本地未认证时 REST 代用（D-12） |
| actions/setup-python `'3.15'` | CI-03 矩阵上界 | ✓ | 3.15.0 stable（2026-10-09 收录） | `'3.15-dev'` 亦可（ci.yaml 既有形态） |
| GitHub Actions windows-latest | 全部 Windows job | ✓（远程） | Windows Server 2025 + VS 2026（2026-06 起） | pin `windows-2025` 具体标签 |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none（A1/A2 为低风险假设，首跑自证）

## Security Domain

> `security_enforcement: true`（ASVS level 1）。本 phase 是 CI/分发基建，无应用面（V2–V6 用户面类别不适用）；安全面集中在 CI 供应链与发布完整性。

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no（无用户认证面；GITHUB_TOKEN 机器身份） | — |
| V3 Session Management | no | — |
| V4 Access Control | yes（CI 授权） | job 级 `permissions:` 最小声明（contents: write 仅 release job；其余 `permissions: {}` 延续 ci.yaml:5 纪律） |
| V5 Input Validation | yes（workflow 输入） | tag/ref 名经 env 间接引用进 run: 块（防 `${{ }}` 注入）；checkout `persist-credentials: false`（既有惯例） |
| V6 Cryptography | no（不引入密码学） | artifact SHA256 由 cibuildwheel 输出（可留档） |

### Known Threat Patterns for CI/CD supply chain

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| 第三方 action 供应链（typosquat/劫持） | Tampering / Elevation | 只用既有版本族（actions@v7 系、pypa/cibuildwheel、msys2/setup-msys2@v2）+ 大版本 pin；不引入新第三方 action |
| `${{ github.ref }}` 直接内插 run: | Injection / Tampering | env 间接引用（Example 3） |
| GITHUB_TOKEN 过权 | Elevation | workflow 顶层最小 + release job 单独提权 |
| 恶意 PR 改 workflow 自发布 | Tampering | wheel 发布触发限 tag/release 分支（继承 release.yaml 模式）；push 触发的 job 只跑测试不发布 |
| wheel 篡改/来源不实 | Repudiation | cibuildwheel 打印 SHA256；GitHub Releases 提供 tag 关联审计轨迹 |
| 下载产物执行（research 阶段纪律） | Tampering | 本探针全程未执行任何下载包的构建产物（隔离 venv + 既有 setup.py 代码路径） |

## Sources

### Primary (HIGH confidence)

- 本地端到端探针（2026-10-13，cibuildwheel 4.2.1 + delvewheel 1.13.1/1.13.2 + VS 2026 14.50.35717，D:/Github/pysam）——全部结论的实证锚点
- 仓库源码阅读：pyproject.toml、setup.py（IS_MSVC_PYTHON/符号门/implib//DEF）、.github/workflows/ci.yaml、release.yaml、devtools/smoke_test.py、devtools/msvc-build.md、devtools/artifactname.py、devtools/msys2-bootstrap.sh
- delvewheel 1.13.1/1.13.2 源码（`_wheel_repair.py` casemap 分支、`_dll_utils.py` find_library/get_all_needed）+ `--help` 实跑
- cibuildwheel changelog（cibuildwheel.pypa.io/en/stable/changelog/）——4.2.1/4.3.0/4.3.1 变更
- msys2/setup-msys2 README（github.com/msys2/setup-msys2）——inputs 与 release:false 行为

### Secondary (MEDIUM confidence)

- actions/runner-images issue #14017 + GitHub changelog 2026-05-14——windows-latest → VS2026（2026-06）
- python.org downloads（3.15.0 final，2026-10-09）+ actions/python-versions 收录报道
- gh release create 权限模式（社区 workflow 实例：contents:write + GH_TOKEN）
- 项目预注册研究 .planning/research/{STACK,PITFALLS,ARCHITECTURE}.md（W8/W11 陷阱在本次探针中被实证确认）

### Tertiary (LOW confidence)

- A1/A2（runner 预装 Git Bash/gh CLI）——常识级假设，首跑自证

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH —— cibuildwheel/delvewheel 全链路本地实跑；msys2 action 与 runner 镜像为官方文档级
- Architecture: HIGH —— 三个 workflow 的每一步都对应本地已验证的调用形态；唯一未实跑的是 GitHub Actions 本身（执行期首次验证）
- Pitfalls: HIGH —— Pitfall 1/2 为实证失败+实证修复；3/4 源码级；5/8 官方文档级

**Research date:** 2026-10-13
**Valid until:** 2026-11-13（runner 镜像与 cibuildwheel 4.x 为慢漂移面；30 天后建议复核 windows-latest 镜像与 cibuildwheel 最新版）
