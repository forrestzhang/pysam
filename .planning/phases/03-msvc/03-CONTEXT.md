# Phase 3: MSVC 构建系统 - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — infrastructure phase)

<domain>
## Phase Boundary

pysam 可用 MSVC（Build Tools for VS 2022）完整构建并通过全量测试 — 官方 wheel 生态的原生工具链就位。MSVC 下 setup.py 分支（`compiler_type` 分派）基于预生成 `win32/config.h.msvc` + 显式源码清单完成全部扩展与 bundled 库编译，无任何 autotools 调用；MSVC 构建产物上 `import pysam` 成功且完整测试套件全绿；单一集中 MSVC shim 头文件覆盖 C99/VLA 缺口；按研究标志完成 clang-cl 回退路径评估（BUILD-02）。

NOT in this phase: Windows CI runners/wheel 分发（Phase 4）、远程 I/O（v2）、PyPI 官方包名。

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — infrastructure phase (autonomous smart-discuss). Use ROADMAP phase goal, success criteria, REQUIREMENTS.md BUILD-02, pre-registered research, and the carried constraints below to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

### Carried constraints (prior decisions — binding on this phase)
- **D-17（Phase 1 CR-01，deferred → 本 phase 必须先行修复）**: 非 inplace 构建下符号门探测 `build/lib.../pysam/*.dll.a` 而 implib 实际落源码树 pysam/ → CalledProcessError；修法 = 发射路径从 `os.path.dirname(get_ext_fullpath(...))` 派生。本 phase（BUILD-02）是首个 out-of-tree 构建阶段，不修则 MSVC 路径构建必炸。
- **D-20 / WR-01+WR-05（Phase 2 评审遗留 → 本 phase 处置）**: (a) samtools/bcftools.pysam.c 的 `_WIN32 __builtin_setjmp/__builtin_longjmp` 崩溃修复未同步进 `import/pysam.c` 模板 — 任何 `devtools/import.py` 运行前必须先同步模板，否则静默回退崩溃修复；(b) GCC builtins 不存在于 MSVC/clang-cl — `_WIN32` 门控不够，需编译器门控（`#if defined(_WIN32) && !defined(_MSC_VER)` 形态或等价）。
- **新 WR-01（01-REVIEW 2026-10-12，open）**: `pysam/libcutils.pyx` `_collect` 以 ANSI 代码页解码捕获的 stdout/stderr — cp936 机器上 UTF-8 输出变 mojibake 且无异常；MSVC 路径同样受影响。属本 phase 可顺手处置项（在 MSVC 构建全绿的语义下验证）。

### Pre-registered approach (research + ROADMAP SC-1/SC-3)
- 预烘焙 `win32/config.h.msvc`（Pillow/libusb 模式：MSYS2 一次 configure 采集后手工固化）+ 显式源码清单驱动 setuptools 编译 —— 短路 autotools，与 UCRT64 路径（保留真实 configure）并存于同一 setup.py，按 `compiler_type` 分派。
- 单一集中 MSVC shim 头文件（扩展 `win32/` 而非逐文件打地鼠）；VLA 清单 = bundled 源码中 VLA 使用点盘点（research 标志：htslib 上游有 MSVC 移植先例 refresh-bio-sandbox/htslib-msvc；samtools coverage.c 已知用 VLA）。
- clang-cl 回退路径评估（SC-3 要求）：teepean 指出 clang-cl 支持 VLA — 评估为 MSVC cl.exe 不可行时的回退，非首选。

### Reusable Assets
- Phase 1/2 已建立的：setup.py 平台分派骨架（`sys.platform == 'win32'` 门 + 决策 ID 注释）、llvm-nm 符号门（BUILD-03，win32 豁免闭集 D-16）、`devtools/msys2-bootstrap.sh` 结构、UCRT64 rebuild 纪律（`HTSLIB_CONFIGURE_OPTIONS=--disable-libcurl` + `MAKE=mingw32-make`；htslib C 改动需 `setup.py build_ext --inplace --force`）
- `pysam/libcport.pxd` 单点平台映射（D-18）— POSIX 恒等、Windows `_WIN32` 分支；MSVC 编译该文件时 `_WIN32` 分支同样激活（需验证 `_wopen` 族在 MSVC 可用 — 均为 UCRT 标准函数，预期兼容）
- Phase 2 的 1027-test 绿基线 = MSVC 路径的验收对照（同套件须在 MSVC 产物上全绿）

### Established Patterns
- 所有 C 改动 `#ifdef` 守卫 + `#else` 原文保留（零回归红线的既定形态；02-04 CI 全绿证明该形态有效）
- fork CI ubuntu/macos 每 push 验证（MSVC 分支改动不得触碰 POSIX 路径字节）

### Integration Points
- `setup.py` build_ext 编译器分派点（`compiler.compiler_type`）、configure 短路点（`HTSLIB_MODE` 机制）、符号门调用点（llvm-nm → MSVC 下 dumpbin 或 llvm-nm 仍可用）
- `win32/` 目录（getopt.c/h 幸存 shim；config.h.msvc 与 shim 头文件落此）
- `.planning/research/STACK.md`/`ARCHITECTURE.md` 的 MSVC 段（预注册设计）、`UPSTREAM-PRS.md`（theAeon MSVC 实证痛点清单 + htslib-msvc 参考）

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase; carried constraints above are the binding inputs.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure path; no grey-area discussion held.

</deferred>
