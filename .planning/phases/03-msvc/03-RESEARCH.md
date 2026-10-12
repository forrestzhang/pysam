# Phase 3: MSVC 构建系统 - Research

**Researched:** 2026-10-12
**Domain:** MSVC (cl.exe/link.exe) build path for pysam's Cython extensions + bundled htslib/htscodecs/samtools/bcftools — pre-baked config.h, explicit source lists, Win32 shim layer, cross-extension import-library linking, BUILD-03 symbol gate on MSVC artifacts
**Confidence:** HIGH (every toolchain claim below was **empirically probed on this machine this session**: cl.exe compiled the real bundled sources; a full two-extension cross-.pyd link+import+call probe succeeded; llvm-nm parsed MSVC artifacts; setuptools' MSVC auto-detection was exercised end-to-end. Remaining unknowns are enumerated in the Assumptions Log)

## Summary (摘要)

本机 MSVC 环境与项目文档假设有一个重大出入、若干已消除的风险和一个新发现的依赖。**(1) 环境实况**：本机装的是 **Visual Studio 2026 Build Tools 18.4.1**（非 ROADMAP 文本所说的 "VS 2022"），带两个 MSVC toolset（14.44.35207 = v143 系、14.50.35717 = v145，setuptools 默认选 14.50，`_MSC_VER=1950`）和 Windows SDK 10.0.26100.0/10.0.22621.0；**没有 python.org CPython、没有 py launcher、没有 clang-cl**，可用解释器是 Miniconda 3.13.5（`win-amd64`）。决定性实验证明：**setuptools 78.1.1 在 Miniconda Python 上从普通 Git Bash（零 vcvars）自动定位 VS2026 Build Tools 并完整编译+链接+import 一个 C 扩展** — Phase 3 可以在本机直接执行 SC-2，Build Tools 安装不成为计划任务。**(2) MSVC 错误面已用 cl.exe 对真实 bundled 源码逐文件枚举完毕**，比预想小得多：整个 bundled 树（含 .pysam.c）只有 **1 处 VLA**（`coverage.c:233` 的 `double hist_data[hist_size]`，镜像 `coverage.c.pysam.c:235`）、**1 处 C99 `[static N]` 形参**（`hts_internal.h:140`）、缺 4 个头文件（unistd.h/pthread.h/strings.h/sys/time.h）+ 一组名字映射（strcasecmp×229 等）+ `ssize_t`/`gettimeofday`/`mkstemp`/`PTHREAD_CREATE_JOINABLE` 补齐。Cython 生成的全部 4 个代表 .c（含 libcport 内联 C）在 cl 下零错误。**(3) 新发现**：htslib `hts_expr.c:37`/`sam.c:39` 无条件使用 POSIX `<regex.h>`（`regcomp/regexec`，UCRT64 构建的 `LIBS = -lregex -llzma -lbz2 -lws2_32 -lz`），MSVC 无 regex.h → 需 vendor 一个 POSIX regex 实现（htslib-msvc 用 vcpkg 装 TRE）；zlib/bzip2/lzma 在 MSVC 下必须从源码 vendor（MSYS2 的 zconf.h 自己 include unistd.h，不可复用——实证）。**(4) 跨扩展导出问题已实证解决**：htslib 自带 `HTSLIB_EXPORT __declspec(dllexport)` 机制（`hts_defs.h:127-132`），编译 htslib 源时定义 `HTS_BUILDING_LIBRARY` 即导出全部注解 API，无需生成 .def；补充实验证明 MSVC link 下 `/DEF:`、后置 `/IMPLIB:` 覆盖 builtin、跨 .pyd 符号解析 + 运行时调用全部可行（`auser.pong()` 经 aclib.pyd 的 `shared_func` 返回 84）。

**Primary recommendation:** setup.py 采用**两级分派**（模块图按 `sysconfig.get_platform()` 在顶层分支：mingw→UCRT64 路径原样、win-amd64→MSVC 新路径；flags 按 `compiler.compiler_type` 在 build_ext 内分支），MSVC 分支 = 写 `win32/config.h.msvc`（从当前 UCRT64 config.h 手工固化，undef 全部 GCC-builtin 键）+ 显式源码清单（LIBHTS_OBJS 镜像 + htscodecs 14 个 + cram 11 个 + vendor 的 zlib/bzip2/lzma/regex）+ `win32/msvc/` shim 目录（unistd.h/pthread.h/strings.h/sys/time.h 四个 drop-in + `/FI` 中央 compat 头 + pthread Win32 实现）+ `HTS_BUILDING_LIBRARY` 导出 + `/IMPLIB:` 定向发射（D-17 修法在两个工具链上统一）。D-17（implib 路径）与 D-20（import/pysam.c 模板同步 + `_MSC_VER` 编译器门）作为前置任务先行。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Carried constraints (prior decisions — binding on this phase)
- **D-17（Phase 1 CR-01，deferred → 本 phase 必须先行修复）**: 非 inplace 构建下符号门探测 `build/lib.../pysam/*.dll.a` 而 implib 实际落源码树 pysam/ → CalledProcessError；修法 = 发射路径从 `os.path.dirname(get_ext_fullpath(...))` 派生。本 phase（BUILD-02）是首个 out-of-tree 构建阶段，不修则 MSVC 路径构建必炸。
- **D-20 / WR-01+WR-05（Phase 2 评审遗留 → 本 phase 处置）**: (a) samtools/bcftools.pysam.c 的 `_WIN32 __builtin_setjmp/__builtin_longjmp` 崩溃修复未同步进 `import/pysam.c` 模板 — 任何 `devtools/import.py` 运行前必须先同步模板，否则静默回退崩溃修复；(b) GCC builtins 不存在于 MSVC/clang-cl — `_WIN32` 门控不够，需编译器门控（`#if defined(_WIN32) && !defined(_MSC_VER)` 形态或等价）。
- **新 WR-01（01-REVIEW 2026-10-12，open）**: `pysam/libcutils.pyx` `_collect` 以 ANSI 代码页解码捕获的 stdout/stderr — cp936 机器上 UTF-8 输出变 mojibake 且无异常；MSVC 路径同样受影响。属本 phase 可顺手处置项（在 MSVC 构建全绿的语义下验证）。

### Pre-registered approach (research + ROADMAP SC-1/SC-3) — design baseline
- 预烘焙 `win32/config.h.msvc`（Pillow/libusb 模式：MSYS2 一次 configure 采集后手工固化）+ 显式源码清单驱动 setuptools 编译 —— 短路 autotools，与 UCRT64 路径（保留真实 configure）并存于同一 setup.py，按 `compiler_type` 分派。
- 单一集中 MSVC shim 头文件（扩展 `win32/` 而非逐文件打地鼠）；VLA 清单 = bundled 源码中 VLA 使用点盘点（research 标志：htslib 上游有 MSVC 移植先例 refresh-bio-sandbox/htslib-msvc；samtools coverage.c 已知用 VLA）。
- clang-cl 回退路径评估（SC-3 要求）：teepean 指出 clang-cl 支持 VLA — 评估为 MSVC cl.exe 不可行时的回退，非首选。

### Claude's Discretion
All implementation choices are at Claude's discretion — infrastructure phase (autonomous smart-discuss). Use ROADMAP phase goal, success criteria, REQUIREMENTS.md BUILD-02, pre-registered research, and the carried constraints above to guide decisions.

### Reusable Assets (from 03-CONTEXT)
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

### Deferred Ideas (OUT OF SCOPE)
None — infrastructure path; no grey-area discussion held. (Phase boundary: Windows CI runners/wheel 分发 = Phase 4、远程 I/O = v2、PyPI 官方包名 = future.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUILD-02 | MSVC 构建系统 — 预生成 `win32/config.h` + 显式源码清单（Pillow/h5py 模式），产出官方级构建 | Complete empirical groundwork: toolchain verified on-machine (VS2026 BT 18.4.1, cl 14.50, setuptools auto-detect); full MSVC error surface enumerated by compiling real sources; config.h.msvc curation recipe derived from the in-tree UCRT64 config.h; explicit source-list scale measured (54 LIBHTS_OBJS + 14 htscodecs + 11 cram + vendored deps); cross-extension export/link mechanism verified end-to-end (`HTS_BUILDING_LIBRARY` + `/IMPLIB:`) |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Toolchain selection (UCRT64 vs MSVC path) | setup.py top level, keyed on `sysconfig.get_platform()` | `compiler.compiler_type` (flags only) | The module graph (which sources exist) differs per toolchain and is assembled at setup.py import time; compiler_type is only known at build_ext time — the two-level split is the setuptools-canonical pattern (ARCHITECTURE.md Pattern 1). On win-amd64 CPython, msvc is the only supported compiler (D-05 rules out GCC), so platform ⇒ toolchain deterministically |
| htslib feature configuration | Pre-baked `win32/config.h.msvc` (checked in) | harvest procedure doc | configure cannot run under cl; Pillow/libusb pattern pre-registered |
| C compilation of bundled libs | setuptools `Extension.sources` (explicit lists) | — | replaces `make lib-static`; mirrors LIBHTS_OBJS |
| Cross-extension symbol resolution | MSVC import libraries (`.lib`) via `HTS_BUILDING_LIBRARY` dllexport + `/IMPLIB:` redirect | supplementary `/DEF:` for un-annotated gaps | verified live this session; GNU ld's `--export-all-symbols` has no MSVC equivalent |
| Symbol gate (BUILD-03) | llvm-nm (from MSYS2 ucrt64, on PATH) over emitted `.lib` | dumpbin (fallback, parser差异) | llvm-nm parses MSVC .lib archives — verified live; .pyd has no symbol table under both toolchains |
| MSVC POSIX/C99 gap coverage | `win32/msvc/` shim directory + `/FI` central compat header | 4 source patches (VLA, [static], D-20 ×2 files) | bounded, empirically enumerated surface; force-include needed because `strcasecmp` etc. appear in files that don't include strings.h |
| pthread API for htslib/samtools | Win32 implementation shim (CRITICAL_SECTION/CONDITION_VARIABLE/INIT_ONCE/FlsAlloc) or vendored pthreads4w | — | thread_pool.c has zero `_WIN32` handling; recursive mutex required (CRITICAL_SECTION is re-entrant) |
| POSIX regex for hts_expr/sam filters | vendored regex implementation (musl regex / TRE-class) | — | new dependency discovered this session; no config guard in hts_expr.c:37 / sam.c:39 |
| zlib/bzip2/lzma under MSVC | vendored from official sources, compiled by the same cl pass | (disable-in-config alternative documented) | MSYS2 headers are GCC-configured (zconf.h includes unistd.h — verified) and MSYS2 import libs don't cross toolchains (PITFALLS Pitfall 4) |
| MSVC build invocation discipline | plain shell + python (setuptools runs vcvars internally) | `vcvars64.bat` wrapper if raw cl needed | verified: zero-env build works from Git Bash |

## Standard Stack

### Core

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Visual Studio Build Tools | **18.4.1** ("VS 生成工具 2026", channel VisualStudio.18.Release) | cl.exe/link.exe/lib.exe toolchain | Installed on this machine [VERIFIED: vswhere.exe -all -products '*' output this session — `installationVersion: "18.4.11612.150"`, `productId: "Microsoft.VisualStudio.Product.BuildTools"`, path `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools`]. NOTE: ROADMAP/STACK text says "VS 2022"; the machine reality is VS 2026 — the design must not hard-code a VS-version path (let setuptools locate it) |
| MSVC toolset | **14.50.35717** (default; `_MSC_VER=1950`) + 14.44.35207 also installed | C compilation | [VERIFIED: `ls .../VC/Tools/MSVC/` + setuptools picked 14.50 in live build]. ABI-compatible with CPython 3.13 (C-extension ABI is stable across MSVC generations via vcruntime140.dll) |
| Windows SDK | 10.0.26100.0 (used) + 10.0.22621.0 | UCRT + Win32 headers/libs | [VERIFIED: SDK Include dirs listed + live cl command line] |
| CPython (MSVC runtime) | **Miniconda 3.13.5** (`D:\miniconda3\python.exe`, `win-amd64`) | MSVC-path build+test interpreter | The only MSVC-compatible CPython on this machine [VERIFIED: `py -0p` empty, no `%LOCALAPPDATA%\Programs\Python`, WindowsApps python is the Store redirector stub]. Standard CPython ABI — setuptools treats it as native win-amd64 |
| setuptools | 78.1.1 (miniconda) | build backend; MSVC auto-detection | [VERIFIED: live build auto-located cl.exe with no vcvars, no env setup] |
| Cython | >=3,<4 (existing pin; install into `_venv-msvc`) | .pyx → C | Phase 2 verified Cython 3.3.0 output compiles under cl (see Code Examples); committed `pysam/libc*.c` are the primary artifacts |
| llvm-nm | UCRT64 `mingw-w64-ucrt-x86_64-llvm-tools` (already installed) | BUILD-03 symbol gate on MSVC `.lib` | [VERIFIED: parsed MSVC-produced `probe.cp313-win_amd64.lib`, symbols listed incl. `PyInit_probe T`] |

### Supporting (vendored C sources — new to tree)

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| zlib | **1.3.2** (current stable, 2026-02-17) | BGZF/gzip — mandatory (htslib hard-depends) | always; vendor from zlib.net official tarball [VERIFIED: zlib.net + madler/zlib releases + zlib-announce, sha256 published] |
| bzip2 | 1.0.8+ | CRAM bzip2 codec — parity with UCRT64 build (`HAVE_LIBBZ2 1`) | recommended for SC-2 parity (see Open Questions Q1) [ASSUMED: current version to pin at execution] |
| liblzma (xz) | 5.8.x | CRAM lzma codec — parity (`HAVE_LIBLZMA 1`) | recommended for SC-2 parity (Q1) [ASSUMED] |
| POSIX regex | musl-regex class implementation | htslib filter expressions (`hts_expr.c`, `sam.c` filter API) | mandatory — MSVC has no regex.h; UCRT64 build links `-lregex` [VERIFIED: `make print-config` LIBS line this session] (Q2 for choice) |
| pthreads4w | 3.x | alternative to hand-rolled Win32 pthread shim | only if planner picks it over the minimal shim (Q3) [ASSUMED] |

**Installation:**
```bash
# No pip packages installed by this phase (pytest/Cython already available/venv-install).
# MSVC build venv (one-time):
D:/miniconda3/python.exe -m venv D:/Github/pysam/_venv-msvc
D:/Github/pysam/_venv-msvc/Scripts/python.exe -m pip install "Cython>=3,<4" pytest
# Vendored C sources are committed to-tree (win32/deps/ or vendor/) from official
# release tarballs with recorded hashes — supply-chain rule, see Security Domain.
# MSVC builds need llvm-nm on PATH for the symbol gate:
export PATH="/c/msys64/ucrt64/bin:$PATH"
```

**Version verification:** toolset/SDK/Python versions above were all verified by direct execution this session (vswhere, cl banner `_MSC_VER=1950` via built probe module, live setuptools command lines). zlib version verified against zlib.net and GitHub releases this session. bzip2/xz/pthreads4w current versions not yet pinned — planner pins at execution from official sources [ASSUMED].

## Package Legitimacy Audit

> This phase installs **no registry packages** (no PyPI/npm/crates dependencies). New third-party code enters as **vendored C source trees** (zlib/bzip2/xz/regex[/pthreads4w]) — governed by the vendoring supply-chain rule in Security Domain, not by the registry gate.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none — no registry installs) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
MSVC build flow (Phase 3 target state; UCRT64 flow unchanged on the left)

  pip install / setup.py build_ext  (Miniconda CPython, any shell; setuptools
        │                            internally locates VS Build Tools — verified)
        ▼
  setup.py module level ────────── sysconfig.get_platform() ──────────┐
  ├─ mingw*  → UCRT64 path (sh configure + make + mingw ld implibs)   │ unchanged
  └─ win-amd64 → MSVC path:                                          ◀─ new
        1. write htslib/config.h  ◀── win32/config.h.msvc (checked in,
           curated from UCRT64 configure output; deterministic rewrite
           per build — alternation with UCRT64 builds is safe)
        2. htslib_make_options = hard-coded dict (LIBHTS_OBJS mirror
           + LIBS = vendored lib names)   [replaces make print-config]
        3. module graph: libchtslib.sources += htslib *.c (54) +
           htscodecs (14) + cram (11) + vendored zlib/bz2/lzma/regex +
           shim .c (pthread impl); tool exts += win32/getopt.c (private
           copies, D-16 isolation); NO make, NO configure
        4. build_ext (compiler_type == 'msvc'):
           /std:c11, /FI win32/msvc/msvc_compat.h, include win32/msvc
           libchtslib: -DHTS_BUILDING_LIBRARY → __declspec(dllexport)
                      on all HTSLIB_EXPORT-annotated API (hts_defs.h)
                      + supplementary /DEF: for un-annotated gaps
                      + late /IMPLIB:<dir on library_dirs>  (D-17 shape)
           consumers: link chtslib<EXT-stem>.lib (name matches /IMPLIB
                      emission — verified by cross-link probe)
        5. BUILD-03 gate: llvm-nm -g -P over each emitted .lib
           (extension .dll.a → .lib under msvc; gate code path unchanged
            otherwise; llvm-nm from MSYS2 ucrt64 on PATH)
        6. pysam/config.py regex-parse of htslib/config.h — unchanged
           (same #define format)

  Runtime: import pysam → libc* .pyd load; MSVC .pyd depends only on
  system CRT (vcruntime140.dll — ships with CPython) — no MinGW DLLs.
```

### Recommended Project Structure (delta only)

```
win32/
├── getopt.c / getopt.h          # existing — compiled per tool extension under MSVC
├── config.h.msvc                # NEW — pre-baked htslib config.h (curated)
├── chtslib_exports.def          # NEW — supplementary exports (un-annotated gaps only)
└── msvc/                        # NEW — the single centralized MSVC shim layer
    ├── msvc_compat.h            #   /FI force-include: ssize_t (BaseTsd),
    │                            #   strcasecmp→_stricmp, strncasecmp→_strnicmp,
    │                            #   STDIN/STDOUT/STDERR_FILENO, fdopen→_fdopen,
    │                            #   isatty/fileno, _USE_MATH_DEFINES,
    │                            #   WIN32_LEAN_AND_MEAN, S_ISREG/S_ISDIR
    ├── unistd.h                 #   drop-in (MSVC body; #include_next under __GNUC__)
    ├── strings.h                #   drop-in macros
    ├── sys/time.h               #   drop-in: timeval + gettimeofday decl
    ├── pthread.h                #   drop-in declarations for the bounded surface
    └── pthread_win32.c          #   implementation: CRITICAL_SECTION (recursive!),
                                 #   CONDITION_VARIABLE, INIT_ONCE, FlsAlloc,
                                 #   CreateThread/WaitForSingleObject, gettimeofday,
                                 #   mkstemp (_mktemp_s + _O_BINARY|_O_EXCL open)
vendor/ (or win32/deps/)         # NEW — zlib 1.3.2, bzip2, xz/liblzma, regex
setup.py                         # two-level dispatch + MSVC branch (surgical, win32-gated)
```

### Pattern 1: Two-level toolchain dispatch (module graph vs flags)

**What:** At setup.py import time, branch on `sysconfig.get_platform().startswith("mingw")` vs `win-amd64` to select source lists and the configure-vs-config.h.msvc path. Inside `cy_build_ext`, branch on `self.compiler.compiler_type` (`'msvc'` vs `'mingw32'`) for compile/link flags.

**When to use:** always — this is ARCHITECTURE.md Pattern 1; the current setup.py already has the win32 `sys.platform` branches, this phase adds the compiler_type sub-branch inside them.

**Verified facts feeding this pattern:**
- `MSVCCompiler().initialize(); compiler_type` → `'msvc'`, cc → `...14.50.35717\bin\HostX86\x64\cl.exe` [VERIFIED: executed on miniconda python this session]
- `sysconfig.get_platform()` on miniconda → `'win-amd64'` [VERIFIED: executed]
- On win-amd64 CPython the default compiler is msvc (no `--compiler` flag needed; D-05 excludes GCC)

**Current code that MUST become compiler-gated** — the `sys.platform == 'win32'` branch in `build_extension` applies GNU-ld flags unconditionally [VERIFIED: setup.py:526-554, read this session]:
```python
        elif sys.platform == 'win32':
            # PE binaries have no ELF rpath; only ensure the flag list exists.
            if not ext.extra_link_args:
                ext.extra_link_args = []
            ...
            ext.extra_link_args.append("-Wl,--export-all-symbols")
            ...
            ext.extra_link_args.append(
                "-Wl,--exclude-symbols="
                + ":".join(sorted(WIN32_GETOPT_EXEMPT_SYMBOLS)))
            ext.extra_link_args.append("-Wl,--out-implib," + implib)
```
Under MSVC these become: no `-Wl,*` flags at all (link.exe ignores-with-warning); exports come from `HTS_BUILDING_LIBRARY` + supplementary `/DEF:`; implib comes from a late `/IMPLIB:` override (verified last-wins, see Pattern 3).

### Pattern 2: D-17 implib emission discipline (both toolchains, one shape)

**What:** Derive the implib path from the module's own output path so emission and gate-probe read the same file, inplace or not.

**Current bug** [VERIFIED: setup.py:401-409 (gate probe) and setup.py:536-539 (emission), read this session — quoted verbatim]:
```python
        # gate probe (check_ext_symbol_conflicts):
        for ext in self.distribution.ext_modules:
            objfile = self.get_ext_fullpath(ext.name)
            if sys.platform == 'win32':
                objfile = os.path.splitext(objfile)[0] + ".dll.a"
```
```python
            # emission (build_extension):
            mod = ext.name.rsplit('.', 1)[-1]
            implib = os.path.join(
                "pysam",
                os.path.splitext(mod + suffix)[0] + ".dll.a")
```
`get_ext_fullpath` returns `build\lib.<plat>-<tag>\pysam\libchtslib*.pyd` when not inplace, while the emission path `"pysam/..."` is cwd-relative (source tree) → the gate's llvm-nm call raises CalledProcessError (file not found) on any out-of-tree build (`pip install .`, `bdist_wheel`).

**Fix shape (MinGW):**
```python
            implib = os.path.join(
                os.path.dirname(self.get_ext_fullpath(ext.name)),
                os.path.splitext(mod + suffix)[0] + ".dll.a")
```
**Fix shape (MSVC):** same dirname derivation, `.lib` extension, emitted via a late `/IMPLIB:` in extra_link_args; gate reads `os.path.splitext(get_ext_fullpath(name))[0] + (".lib" if <msvc> else ".dll.a")`.

**Why the directory works:** `common_options` already puts `abspath("pysam")` in every extension's `library_dirs` (setup.py:920) and `build_extension` appends `build_lib/pysam` for non-inplace (setup.py:505-506) — `get_ext_fullpath`'s dirname is always one of those two, so `-lchtslib<stem>` / `chtslib<stem>.lib` resolution finds the emitted implib.

### Pattern 3: Cross-extension linking under MSVC (VERIFIED END-TO-END this session)

**What:** libchtslib.pyd exports the htslib API via htslib's own dllexport machinery; consumers link its import library.

**Evidence chain:**
1. htslib has the machinery [VERIFIED: htslib/htslib/hts_defs.h:127-132, read this session]:
```c
#if defined(_WIN32) || defined(__CYGWIN__)
#if defined(HTS_BUILDING_LIBRARY)
#define HTSLIB_EXPORT __declspec(dllexport)
#else
#define HTSLIB_EXPORT
#endif
```
   and `hts_expr.c:28` already uses `#define HTS_BUILDING_LIBRARY // Enables HTSLIB_EXPORT, see htslib/hts_defs.h`.
2. Annotation coverage: 447 `HTSLIB_EXPORT` annotations across hts.h(78)/sam.h(123)/bgzf.h(30)/hfile.h(23)/cram.h(81)/tbx.h(16)/vcf.h(96) [VERIFIED: grep counts this session]. Gaps exist (`hts_lib_shutdown`, `hts_free`, `hts_opt_add/apply/free`, `hts_parse_format`, `hts_parse_opt_list` in hts.h lack the annotation — grep this session) → supplementary `/DEF:win32/chtslib_exports.def` adds them; dllexport + /DEF combine (union of exports). A missing export surfaces loudly as consumer-side LNK2001, so drift is self-detecting.
3. Two-extension live probe (built with miniconda python + cl 14.50 this session): `aclib` (defines `shared_func`, linked with `/DEF:xlink.def` + late `/IMPLIB:msvcdir\aclib.lib` via `extra_link_args`) and `auser` (`libraries=["aclib"]`, `library_dirs=["msvcdir"]`, calls `shared_func`): both built, both imported, `auser.pong()` returned **84** (2× shared_func's 42) — i.e. a cross-.pyd call through the import table works. The late `/IMPLIB:` **overrode** distutils' builtin `/IMPLIB:build\temp\...` (the .lib landed in msvcdir/ — verified by `ls`).
4. Data symbols: grep found **zero** `HTSLIB_EXPORT extern` data in htslib headers, and the dispatch data (`samtools_stdout/stderr/stdout_fn`) has no consumer outside libcsamtools itself (grep of pysam/*.c + *.pyx this session: only samtools/samtools.pysam.h declares them) — so no cross-module dllimport annotations are needed. getopt data (optarg/optind) stays per-extension-private (compile win32/getopt.c into each tool extension — MSVC analogue of D-16 isolation).
5. MSVC .pyd carries no COFF symbol table ("no symbols" — llvm-nm this session), same as MinGW's stripped .pyd → the BUILD-03 gate reads the **import library** on both toolchains; llvm-nm parses MSVC .lib archives [VERIFIED: `PyInit_probe T` listed from probe .lib].

### Pattern 4: The single centralized MSVC shim (empirically scoped)

**What:** `win32/msvc/` drop-in headers + `/FI` central compat header + one pthread implementation .c — added to include dirs ONLY in a way that cannot shadow MinGW's real headers (UCRT64 builds must stay byte-identical).

**The empirically enumerated surface** (all from cl.exe probes on the real sources this session):

| Gap class | Concrete items (verbatim from errors/greps) | Shim answer |
|---|---|---|
| missing headers | `<unistd.h>` (64 .pysam.c files + htslib core), `<pthread.h>` (thread_pool_internal.h:45, bgzf.c:35, hfile.c:35, cram_structs.h:49, htscodecs rANS_static.c:60 / rANS_static4x16pr.c:61 / utils.c:44, samtools bam_sort/bam_consensus), `<strings.h>` (hts.c:32), `<sys/time.h>` (thread_pool.c:36) | drop-in headers in win32/msvc/ (on include path for MSVC branch only; `#include_next` guard for GCC) |
| POSIX names | `strcasecmp`×229 / `strncasecmp`×176 in .pysam.c (+30/+5 htslib proper), `isatty`×34 / `fileno`×26 / `STDIN_FILENO`×14 / `fdopen`×5, `random/srandom` (already macro'd at setup.py:788) | macros in /FI msvc_compat.h (must be global — many call sites don't include strings.h) |
| types | `ssize_t` (bgzf.c:388, hfile_internal.h:69 …) | `typedef SSIZE_T ssize_t;` via `<BaseTsd.h>` in /FI header (htslib-msvc's os_specific.h uses exactly this) |
| functions | `gettimeofday` (thread_pool.c:234,976,986; vcfconcat/vcfgtcheck .pysam.c), `mkstemp` (bam_reheader.c:479, bcftools/extsort.c:154 + mirrors), `usleep` | shim functions in pthread_win32.c / msvc_compat layer |
| pthread constants | `PTHREAD_CREATE_JOINABLE` (bam_sort.c.pysam.c:3169 error C2065) | pthread.h drop-in |
| math constants | `M_LN10` (errmod.c:96) — UCRT gates them behind `_USE_MATH_DEFINES` [VERIFIED: corecrt_math_defines.h:27] | `#define _USE_MATH_DEFINES` in /FI header |
| stat macros | `S_ISREG/S_ISDIR` (htslib-msvc defines these for MSVC) | /FI header (verify need during build) |

**pthread implementation surface (bounded, from grep counts this session):** `pthread_mutex_lock`×123 / `unlock`×171 / `init`×11 / `destroy`×14 (+`mutexattr_init/settype/destroy` — **recursive mutex required**, thread_pool.c:755-758 verbatim `pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);` → CRITICAL_SECTION is natively re-entrant), `pthread_cond_signal`×24 / `wait`×7 / `timedwait`×3 (absolute-time deadlines computed via gettimeofday — convert to relative ms) / `broadcast`×6 / `init`×7 / `destroy`×9, `pthread_create`×9 / `join`×9 / `exit`×8 / `self`×1 / `kill`×1 (thread_pool.c:1135 `pthread_kill(p->t[i].tid, SIGINT)` — teardown path; no-op stub returning 0 is the pragmatic mapping), `pthread_once`×3 (INIT_ONCE), TLS `pthread_key_create/getspecific/setspecific` (FlsAlloc family). `thread_pool.c` compiled CLEAN under cl with a declarations-only stub of exactly this surface [VERIFIED this session] — i.e. compilation needs only the header; only the ~14 functions need real bodies.

**Probe-verified clean compiles under cl /std=c11** (with stub headers): `thread_pool.c`, `samtools.pysam.c`, `bcftools.pysam.c`, `rANS_static.c` (SIMD code + current config.h — MSVC's immintrin.h covers AVX2/SSE4 paths), `win32/getopt.c`, `samtools/lz4/lz4.c`, `pysam/libcbgzf.c`, `pysam/libcutils.c`, `pysam/libchtslib.c`, `pysam/libctabix.c` (the last four = Cython-generated C + libcport inline C, zero errors).

### Pattern 5: Source patches (the ONLY C edits beyond the shim)

All use the established `#ifdef`-guard + `#else`-verbatim pattern:

1. **VLA fix** — exactly one VLA exists in the entire bundled tree (GCC `-Wvla` full scan, positive-control verified): [VERIFIED: samtools/coverage.c:233]
```c
    // Calculate histogram that contains percent covered
    double hist_data[hist_size];
```
   mirror at `samtools/coverage.c.pysam.c:235` [VERIFIED: same -Wvla warning]. Fix: heap-allocate (`malloc(hist_size * sizeof(double))` + free) — upstreamable on all platforms, or `#if defined(_MSC_VER)` guarded; apply to BOTH files.
2. **C99 `[static N]` fix** — exactly one site: [VERIFIED: htslib/hts_internal.h:140]
```c
static inline int find_file_extension(const char *fn, char ext_out[static HTS_MAX_EXT_LEN])
```
   Fix: drop the `static` keyword inside the brackets (pure optimizer hint; callers unchanged). Unblocks bgzf.c, hts.c, cram_io.c (all three error only here — verified).
3. **D-20 template sync + compiler gate** — `import/pysam.c` (template) currently has NO `_WIN32` branch [VERIFIED: import/pysam.c:59-83 verbatim:
```c
static jmp_buf @pysam@_jmpbuf;
static int @pysam@_status = 0;

int @pysam@_dispatch(int argc, char *argv[])
{
  ...
  if (setjmp(@pysam@_jmpbuf) == 0)
```
   while `samtools/samtools.pysam.c:84-101` has:
```c
#ifdef _WIN32
  if (__builtin_setjmp(samtools_jmpbuf) == 0)
  ...
  __builtin_longjmp(samtools_jmpbuf, 1);
```
   Fix: (a) sync the `_WIN32` branch into the template; (b) change the gate to `#if defined(_WIN32) && !defined(_MSC_VER)` for the GCC-builtins branch, plain `setjmp/longjmp` under MSVC (MSVC longjmp in MSVC-compiled TUs is the supported path — the Phase-2 STATUS_BAD_STACK crash was UCRT longjmp walking GCC frames). **Mechanism verified:** `__builtin_setjmp` under cl compiles only because C implicit-declaration degrades to a warning — it would fail at LINK (unresolved external), which is exactly the silent-failure class D-20(b) predicts.
4. **Optional WR-01** (`libcutils.pyx _collect` cp936 mojibake) — opportunistic, per CONTEXT.

### Pattern 6: c99 probe and compile flags under MSVC

- `c99_compile_args()` compiles `pysam/conftest_cstd.c` [VERIFIED content this session] which includes `<unistd.h>` and uses `optind` — under MSVC this probe fails for ALL candidate flag values (`None`, `-std=c99`, `-std=gnu99`), ending in "cannot compile C99". MSVC branch: skip the probe, unconditionally use `/std:c11` (all probes this session used it; cl accepts it since VS2019 16.8).
- Flag translation: GCC `-Wno-*` warning flags are already win32-gated OFF (setup.py:796-801, POSIX else-branch). `-fPIC`/`-fvisibility` never reach the MSVC branch. Recommend adding `/utf-8` (source charset; avoids C4819 warnings on cp936 machines — observed this session on non-ASCII probe files) and `/W1` noise control per preference.

### Pattern 7: MSVC rebuild discipline (the UCRT64 contract's analogue)

- **No vcvars needed**: setuptools' `_get_vc_env` runs vcvars internally — a live build from plain Git Bash (zero env) worked [VERIFIED]. Raw cl probes (if ever needed) use the verified `vcvars64.bat`-wrapper pattern: `cmd //c "...vcvars64.bat && cl ..."` (a plain `cmd //c` with inline quotes fails path resolution — use a .bat wrapper).
- **One venv per toolchain**: `_venv` (UCRT64 3.14.7) vs NEW `_venv-msvc` (miniconda 3.13.5). Build products separate naturally: `build/temp.mingw_x86_64_ucrt_gnu-cpython-314/` (exists) vs `build/temp.win-amd64-cpython-313/`, EXT_SUFFIXes `*.cp314-mingw*.pyd` vs `*.cp313-win_amd64.pyd`.
- **config.h alternation is safe**: UCRT64 runs re-execute configure (rewrites htslib/config.h) on every setup.py run; the MSVC branch deterministically rewrites it from `win32/config.h.msvc` every build. Switching toolchains = one full rebuild of the affected tree.
- **htslib C edits** require `setup.py build_ext --inplace --force` (Phase-2 lesson — extensions don't relink on source changes automatically).
- **llvm-nm on PATH**: `export PATH="/c/msys64/ucrt64/bin:$PATH"` before MSVC builds (the gate calls plain `llvm-nm`).
- **gcc probes must run inside the UCRT64 shell** (`MSYSTEM=UCRT64 CHERE_INVOKING=1 /c/msys64/usr/bin/bash.exe -lc '...'`) — outside it gcc fails *silently* (exit 1, no diagnostics; re-verified this session when the first -Wvla scan produced a false-negative all-clear).

### Anti-Patterns to Avoid

- **Passing `-Wl,*` flags to link.exe** — GNU-ld flags in the current win32 branch must be compiler-gated; link.exe at best warns (LNK4044) and ignores them, hiding real misconfiguration.
- **Reusing MSYS2-built headers/libs for the MSVC path** — MSYS2's `zconf.h` itself includes `<unistd.h>` (verified: hts.c probe died inside zconf.h:490) and MSYS2 import libs don't cross toolchains (PITFALLS Pitfall 4). Vendor compiler-neutral sources instead.
- **Editing generated `.pysam.c` without syncing `import/pysam.c`** — the D-20 lesson; every .pysam.c edit must land in the template too (next `devtools/import.py` run would silently revert it).
- **Running gcc-based probes/verification outside the MSYS2 shell** — silent false negatives (seen twice this session).
- **Hand-maintaining a full export .def for libchtslib** — htslib's HTSLIB_EXPORT annotations already do this; only a small supplementary .def for the enumerated un-annotated functions (drift on htslib bumps is caught by consumer LNK2001).
- **Believing cl's "clean compile" for undeclared functions** — implicit-declaration is a warning at /W1; `__builtin_setjmp` compiles and fails at link. Compile probes should use `/we4013` (treat C4013 as error) when verifying MSVC readiness of generated code.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| zlib/bzip2/lzma compression | — | vendor official sources | battle-tested; MSVC-clean (zlib officially supports MSVC) |
| POSIX regex | custom pattern matcher | vendored musl-regex/TRE-class implementation | regcomp/regexec semantics (REG_EXTENDED\|REG_NOSUB, error strings) are subtle; htslib filters depend on POSIX semantics |
| BGZF/htslib anything | — | existing bundled tree | unchanged |
| Symbol table parsing | custom PE parser | llvm-nm (verified on MSVC .lib) | already the BUILD-03 tool |
| gettimeofday / mkstemp / usleep | — | shim functions in the win32/msvc layer | 10-20 lines each, standard Win32 idioms (GetSystemTimeAsFileTime; _mktemp_s + _O_BINARY\|_O_EXCL) |
| pthread on Win32 | full pthreads clone | EITHER minimal shim over CRITICAL_SECTION/CONDITION_VARIABLE/INIT_ONCE/FlsAlloc (14 functions, bounded surface — recommended) OR vendored pthreads4w | the surface is enumerated and small; pthreads4w brings cancellation/signal machinery we never use, plus a license file to manage. Flagged as planner decision Q3 |

**Key insight:** every genuinely hard part of this phase (export mechanism, implib discipline, symbol gate, config curation) was de-risked by a live probe this session; what remains is assembly.

## Common Pitfalls

### Pitfall 1: VS version assumptions baked into paths/docs
**What goes wrong:** hard-coding `Visual Studio\2022\BuildTools` paths or "VS 2022" in docs breaks on this machine (VS 2026 / `18\BuildTools`).
**Why:** roadmap text predates the machine state.
**How to avoid:** never reference VS paths in code — setuptools' auto-detection (vswhere-based) is the only supported locator (verified working). Docs should say "Visual Studio Build Tools with the C++ workload (2022 or later)".
**Warning signs:** LNK/msbuild "toolset not found".

### Pitfall 2: The UCRT64 fail-fast gate rejects the MSVC python
**What goes wrong:** running setup.py under miniconda python today exits immediately: the gate `if not _is_ucrt64_python(): sys.exit(...)` [VERIFIED: setup.py:60-77] fires because `sysconfig.get_platform()` is `win-amd64`, not `mingw*`.
**How to avoid:** first MSVC task restructures the gate: on `os.name == 'nt'`, `mingw*` platform → UCRT64 path (unchanged message); `win32`/`win-amd64` platform → MSVC path with its own fail-fast (actionable message naming the Build Tools + C++ workload requirement, mirroring the D-03/D-13 one-source-of-truth pattern).

### Pitfall 3: c99 probe aborts MSVC builds
Covered in Pattern 6 — the probe source itself is unportable; skip-and-force `/std:c11` under msvc.

### Pitfall 4: out-of-tree build explodes at the symbol gate (D-17)
Covered in Pattern 2 — must be fixed BEFORE any `pip install .`/`bdist_wheel` attempt; SC-2's test run should be executed against an out-of-tree install at least once to exercise it.

### Pitfall 5: implicit-declaration masks link-time bombs
Covered in Anti-Patterns (`/we4013` for verification compiles; the D-20 `__builtin_setjmp` case compiles cleanly at /W1).

### Pitfall 6: config.h GCC-flavored keys leak into the MSVC build
**What goes wrong:** naive reuse of the UCRT64 `htslib/config.h` keeps e.g. `#define HAVE___BUILTIN_CLZ 1`, `HAVE_ATTRIBUTE_CONSTRUCTOR 1`, `HAVE_CLOCK_GETTIME_CPUTIME 1`, `HAVE_GETPAGESIZE 1`, `HAVE_UNISTD_H 1`, `HAVE_STRINGS_H 1`, `HAVE_SYS_PARAM_H 1`, `_XOPEN_SOURCE 700` [VERIFIED: current htslib/config.h read in full this session — those exact keys are set].
**Why it matters:** any `#ifdef` guarded on them selects GCC-only code paths.
**How to avoid:** the curation recipe in State of the Art below (probes this session showed the main htslib files compile clean even WITH the GCC keys — the Makefile-only keys are inert for code — but the undef pass is cheap insurance and matches htslib-msvc's precedent).

### Pitfall 7: cp936 codepage noise (C4819) and mojibake
Non-ASCII bytes in sources trigger C4819 on this machine (seen on probe files). Add `/utf-8` to MSVC compile flags; keep bundled sources ASCII-only (they are).

### Pitfall 8: same-checkout toolchain alternation surprises
The shared `htslib/config.h` flips content between toolchains (real configure output vs config.h.msvc). Symptom if forgotten: stale-configure features (e.g. `HAVE_LIBBZ2` mismatch) in `pysam/config.py`. The discipline (Pattern 7) makes each build rewrite it deterministically.

### Pitfall 9: `__builtin_*` gating with `_WIN32` only (D-20b)
The exact hazard: GCC builtins keyed on `_WIN32` compile under MSVC via implicit declaration and detonate at link. Gate on `defined(_WIN32) && !defined(_MSC_VER)` (or the inverse for the MSVC branch) everywhere builtins appear.

## Code Examples

### MSVC implib emission + gate path (D-17 fix, MSVC arm)
```python
# build_extension, win32 branch, compiler_type == 'msvc':
mod = ext.name.rsplit('.', 1)[-1]
implib = os.path.join(
    os.path.dirname(self.get_ext_fullpath(ext.name)),      # D-17
    os.path.splitext(mod + suffix)[0] + ".lib")
ext.extra_link_args.append("/IMPLIB:" + implib)             # late flag overrides builtin — verified
# gate (check_ext_symbol_conflicts):
ext_impl = ".lib" if <is_msvc> else ".dll.a"
objfile = os.path.splitext(self.get_ext_fullpath(ext.name))[0] + ext_impl
```

### Verified cross-link probe (the shape libchtslib/consumers will use)
```python
# Source: this session's xlink probe — built, linked, imported, called (pong → 84)
Extension("aclib", sources=["aclib.c"],
          extra_link_args=["/DEF:xlink.def", "/IMPLIB:msvcdir\\aclib.lib"]),
Extension("auser", sources=["auser.c"], libraries=["aclib"], library_dirs=["msvcdir"]),
```

### Shim skeleton (drop-in unistd.h that cannot shadow MinGW's real one)
```c
/* win32/msvc/unistd.h — MSVC body; GCC forwarders keep UCRT64 builds on the
   system header (include order: /I dirs precede system dirs for BOTH
   toolchains, so the __GNUC__ arm must forward, not redefine). */
#if defined(__GNUC__)
#include_next <unistd.h>
#else
#include <io.h>
#include <process.h>
#include <stdlib.h>
#define isatty  _isatty
#define fdopen  _fdopen
/* read/write/close map to _read/_write/_close — see libcport precedent */
#endif
```

### config.h.msvc curation recipe (from the live UCRT64 config.h)
```
Base:  current htslib/config.h (UCRT64 configure output, read in full this session)
Keep:  HAVE_LIBZ 1, HAVE_LIBBZ2 1, HAVE_LIBLZMA 1, HAVE_LZMA_H 1 (per Q1),
       HAVE_INTTYPES_H/STDINT_H/STDIO_H/STDLIB_H/STRING_H/SYS_STAT_H/SYS_TYPES_H 1,
       SIMD keys (HAVE_AVX2/AVX512/POPCNT/SSE4_1/SSSE3 1 — rANS_static.c compiled
       clean under cl with these set; htslib-msvc keeps them too),
       HAVE_ATTRIBUTE_TARGET_SSSE3 → undef (GCC attribute),
       PACKAGE_* block, _FILE_OFFSET_BITS 64 (inert on MSVC, harmless)
Undef: HAVE_ATTRIBUTE_CONSTRUCTOR, HAVE_BUILTIN_CPU_SUPPORT_SSSE3,
       HAVE_DECL___CPUID_COUNT, HAVE_DECL___GET_CPUID_MAX, HAVE___BUILTIN_CLZ,
       HAVE___BUILTIN_PREFETCH, HAVE_CLOCK_GETTIME_CPUTIME, HAVE_GETPAGESIZE,
       HAVE_UNISTD_H, HAVE_STRINGS_H, HAVE_SYS_PARAM_H, _XOPEN_SOURCE,
       ENABLE_GCS/PLUGINS/S3 + HAVE_LIBCURL (already undef — v1 remote deferral)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "Build Tools for VS 2022" (ROADMAP text) | VS 2026 BuildTools 18.4.1 on this machine; toolsets v143(14.44)+v145(14.50); setuptools auto-detects regardless | VS 2026 GA (2026) | no code change if no paths hard-coded; Phase 4 CI runners (windows-latest) ship their own VS — toolset pinning is a Phase 4 concern |
| MSVC C99 pain folklore (theAeon 2025 list: VLA everywhere, strcasecmp storms) | htslib/samtools 1.24 tree: exactly 1 VLA + 1 `[static]` + name mapping; Cython 3.3 output + libcport are cl-clean | upstream evolution + Phase 1/2 groundwork | MSVC phase is assembly, not archaeology |
| distutils msvc / `msvc-dev-cmd`-style env setup | setuptools 78 `_get_vc_env` runs vcvars internally; zero-env builds work from any shell | setuptools ≥~74 lineage | rebuild discipline is just "run python" |
| GNU ld `--export-all-symbols` (UCRT64 path) | `HTS_BUILDING_LIBRARY` dllexport + supplementary /DEF | — (htslib's own mechanism) | no .def generation pipeline needed |
| vcpkg for MSVC deps (htslib-msvc's route) | vendored in-tree sources (self-contained wheel constraint) | project decision | one-time vendoring work vs external toolchain dependency |

**Deprecated/outdated:**
- `win32/unistd.h`/`win32/stdint.h` (2013-era) — already dropped by Phase 1 D-10; do NOT resurrect the old copies; the new shim lives in `win32/msvc/` with GCC forwarders.
- htslib-msvc's vcpkg/pthreads/TRE dependency list — reference only (different distribution model); our equivalents are vendored.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Miniconda CPython 3.13.5 is an acceptable SC-2 runtime (no python.org CPython install needed for Phase 3) | Environment | If planner/user insist on python.org CPython: a winget install task + blocking-human gate enters the plan; technical risk low either way (both are win-amd64 MSVC-ABI CPython) |
| A2 | bzip2 + liblzma should be vendored (full parity with UCRT64 feature set) rather than disabled in config.h.msvc | Stack | If disabled: smaller phase, but CRAM codec parity gap vs the 1027-green baseline; any test asserting bz2/lzma CRAM would need exemption (D2-07 discipline) |
| A3 | musl-regex-class vendored implementation satisfies hts_expr/sam filter semantics (REG_EXTENDED, REG_NOSUB, regerror strings) | Don't Hand-Roll | Regex behavioral edge cases could surface as filter-test failures; TRE-class (what htslib-msvc uses via vcpkg) is the fallback |
| A4 | Minimal hand-rolled Win32 pthread shim (14 functions) is preferable to vendoring pthreads4w | Patterns | Condvar-timedwait and once-init are the subtle spots; if review flags risk, pthreads4w vendoring is the drop-in alternative (its header API matches) |
| A5 | `HTS_BUILDING_LIBRARY` export coverage + small supplementary .def suffices for every cross-module symbol pysam actually references | Pattern 3 | Uncovered symbols fail loudly (LNK2001) during the first full MSVC link — self-detecting, cost is iteration not risk |
| A6 | `bam_consensus.c.pysam.c` (not individually probed) has the same pthread surface as bam_sort.c.pysam.c (PTHREAD_CREATE_JOINABLE-class constants) | Patterns | Extra shim constant; trivial |
| A7 | MSVC-built .pyd runtime deps are only vcruntime140.dll + system DLLs (true for static-vendored deps) | Architecture | delvewheel/clean-machine audit is Phase 4's gate anyway (CI-02) |
| A8 | bzip2 1.0.8+ / xz 5.8.x are the current versions to vendor (not pinned this session) | Stack | Pin at execution from sourceware.org/tukaani.org official releases |
| A9 | The Phase-2 test infrastructure (Python data generators, in-process oracles, conftest os.pathsep, threading httpserver) is keyed on `sys.platform == 'win32'` and therefore works unchanged under the miniconda/MSVC env | Requirements map | If any piece is MSYSTEM-keyed instead, it needs a guard relaxation — discovered at first suite run; 02-RESEARCH indicates sys.platform keying |
| A10 | MSVC toolset 14.50-built extensions are ABI-safe for the CPython 3.13 they were built against (local validation) — toolset unification with python.org-built CPython wheels is a Phase 4 CI concern | Environment | None for Phase 3 SC-2; Phase 4 may pin v143 on runners |

## Open Questions

1. **bzip2/lzma: vendor for parity, or disable for scope?** (A2)
   - What we know: UCRT64 baseline has both enabled (`LIBS = -lregex -llzma -lbz2 -lws2_32 -lz` — verified this session); htslib degrades gracefully without them; vendoring adds ~50 TUs of well-trodden MSVC-portable code.
   - Recommendation: vendor both (SC-2 says "完整测试套件全绿" on MSVC products — feature parity is the safest reading). Planner may descope with documented exemptions if build time balloons.
2. **Which regex implementation to vendor** (A3): musl's regex.c (MIT, single-file, POSIX BRE/ERE) vs TRE (what htslib-msvc uses, via vcpkg). Recommendation: musl regex first (single file, permissive license); fall back to TRE if filter tests disagree.
3. **pthread shim: minimal Win32 implementation vs vendored pthreads4w** (A4). Recommendation: minimal shim (bounded surface, no extra license file, no cancellation machinery); planner checkpoint if preferred otherwise.
4. **Does SC-2 need to run on python.org CPython too, or is miniconda sufficient?** (A1) Recommendation: miniconda sufficient for Phase 3; python.org CPython enters at Phase 4 (CI runners provide it; cibuildwheel downloads per-version).
5. **clang-cl fallback (SC-3) — resolved by evidence:** cl.exe 14.50 compiles everything except the enumerated 2 C99 sites + shim gaps; the only VLA is trivially heap-fixable. The "clang-cl needed for VLAs" premise (from theAeon/teepean 2025) no longer holds for the 1.24 tree. Deliverable for SC-3 = the decision note (cl.exe-first; clang-cl documented as contingency, installable via VS "C++ Clang tools" component or winget LLVM if a future htslib bump reintroduces unshimmable GCC-isms — both are blocking-human package installs).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| VS Build Tools (C++ workload) | everything | ✓ | 18.4.1, toolsets 14.44+14.50, SDK 10.0.26100.0/10.0.22621.0 | — (hard requirement; verified working) |
| CPython win-amd64 | build+test | ✓ | Miniconda 3.13.5 (D:\miniconda3) | python.org CPython via winget (not installed; would be a blocking-human gate) |
| setuptools MSVC detection | build | ✓ | 78.1.1 (verified auto-detect, zero env) | — |
| Cython | .pyx→C | ✓ via venv install | >=3,<4 (3.3.0 verified cl-clean in Phase 2 + this session) | committed .c files (cython not strictly required) |
| pytest | SC-2 suite | ✓ via venv install | (any current) | — |
| llvm-nm | BUILD-03 gate | ✓ (PATH prepend `/c/msys64/ucrt64/bin`) | UCRT64 llvm-tools | dumpbin parser (not needed — llvm-nm verified on .lib) |
| zlib source | BGZF | ✗ (not vendored yet) | 1.3.2 to vendor | — |
| bzip2 / xz source | CRAM codecs | ✗ (not vendored yet) | A8 | disable-in-config (Q1) |
| POSIX regex source | hts filters | ✗ (not vendored yet) | Q2 | — |
| clang-cl | SC-3 fallback eval | ✗ (not installed anywhere) | — | not needed (Q5 resolution) |
| winget | contingency installs | ✓ | — | — |

**Missing dependencies with no fallback:** none blocking — the three vendored source trees are plan tasks (downloads from official release channels, recorded hashes).
**Missing dependencies with fallback:** clang-cl (contingency only); python.org CPython (miniconda stands in).

## Security Domain

`security_enforcement: true`, ASVS level 1. The phase adds a build path; it introduces **no new runtime input surfaces** (same test corpus, same local files). New considerations:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | none |
| V3 Session Management | no | none |
| V4 Access Control | no | none |
| V5 Input Validation | no | no new inputs (vendored code consumes committed/compressed genomics data only) |
| V6 Cryptography | no | none (no crypto deps in v1 — libcurl/openssl deferred) |
| V10 Malicious Code | watch item | vendored source provenance: zlib/bzip2/xz/regex MUST come from official release channels (zlib.net, sourceware.org, tukaani.org, musl/gitlab) with recorded SHA-256 (zlib 1.3.2 sha256 published — see Sources); no network at build time; same review standard for the pthread shim (it runs at build/test time only) |

### Known Threat Patterns for this phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Vendored-source supply chain | Tampering | official-channel tarballs + recorded hashes + committed (reviewable) diffs only |
| Binary mixing across toolchains (MSYS2 libs into MSVC build) | Tampering | per-toolchain dependency closure (Pitfall 4 discipline); MSVC job never references MSYS2 import libs |
| Build-time code execution via shim/prebuild code | Tampering | shim code is committed, reviewed C; no network/shell in the MSVC branch (no `shell=True` additions — the MSVC path removes subprocess calls relative to the autotools path) |

## Sources

### Primary (HIGH confidence — executed/read this session)
- **Live MSVC builds/probes (this machine, this session):** trivial extension build+import (`_MSC_VER=1950`); VLA rejection (C2057/C2466/C2133); two-extension cross-link probe (`/DEF:` + late `/IMPLIB:` override + cross-.pyd call → 84); llvm-nm on MSVC .lib and .pyd; cl compile matrix over hts.c/bgzf.c/hfile.c/thread_pool.c/cram_io.c/rANS_static.c/samtools.pysam.c/bcftools.pysam.c/bam_sort.c.pysam.c/coverage.c.pysam.c/libcbgzf.c/libcutils.c/libchtslib.c/libctabix.c/getopt.c/lz4.c
- **vswhere.exe** `-all -products '*'` — VS 18.4.1 BuildTools inventory, toolsets, SDKs
- `setup.py` (full read) — gate (53-77), configure/print-config calls (661-688), htslib_objects (724-725), random→rand (788), include/os (770-788), implib emission (526-554), gate probe (401-433), internal lib naming (805-820), prebuild hooks (830-848)
- `htslib/config.h` (full read — curation base), `htslib/Makefile:203+` (LIBHTS_OBJS), `make print-config` live output (`LIBS = -lregex -llzma -lbz2 -lws2_32 -lz`)
- `samtools/coverage.c:220-300` (VLA), `htslib/hts_internal.h:125-155` ([static]), `import/pysam.c` (full read), `samtools/samtools.pysam.c:1-120` (setjmp gate), `htslib/htslib/hts_defs.h:127-139` (HTSLIB_EXPORT), `htslib/thread_pool.c:30-48,755-758,1135`, `htslib/hts_expr.c:28-44`, `sam.c:39` regex sites, `pysam/conftest_cstd.c`
- `win32/getopt.c` — cl-clean
- **GCC -Wvla full-tree scan** (inside UCRT64 shell, positive-control verified): exactly 2 warnings (coverage.c:233 + .pysam.c:235)

### Secondary (MEDIUM confidence — fetched official docs/reference repos)
- [zlib.net](http://www.zlib.net/) / [madler/zlib releases](https://github.com/madler/zlib/releases) / [zlib-announce 1.3.2](https://madler.net/pipermail/zlib-announce_madler.net/2026/000016.html) — zlib 1.3.2 current (2026-02-17), CVE fixes, sha256
- [refresh-bio-sandbox/htslib-msvc](https://github.com/refresh-bio-sandbox/htslib-msvc) (archive-1.18: `README.msvc.md`, `os/os_specific.h`, `config.h` fetched raw) — vcpkg dependency list, force-include shim pattern (ssize_t/STDIN_FILENO/S_ISREG), HTS_STATIC static-link choice, SIMD keys kept under MSVC
- Prior project research consumed as canonical refs: `.planning/research/STACK.md`, `ARCHITECTURE.md` (pre-registered MSVC design), `UPSTREAM-PRS.md` (theAeon pain list, htslib-msvc pointer), `PITFALLS.md` (Pitfalls 1/3/4/12)

### Tertiary (LOW confidence — planner pins at execution)
- bzip2/xz current release versions (A8); pthreads4w current release (A4 alternative); musl regex extraction details (A3)

## Metadata

**Confidence breakdown:**
- Environment reality (toolchain/interpreter availability + auto-detection): **HIGH** — every claim from live execution
- MSVC error surface / shim scope / source patches: **HIGH** — cl.exe compiled the actual sources; -Wvla scan positive-control verified
- Cross-extension linking + symbol gate design: **HIGH** — end-to-end probe succeeded on this machine
- config.h.msvc curation: **HIGH** on the recipe (base file read in full), **MEDIUM** on completeness (only ~10 of ~90 htslib files individually probed; the rest validated by the clean-compile pattern of their siblings + full-build discovery)
- Vendored dep choices (bz2/lzma/regex/pthread): **MEDIUM** — decisions A2/A3/A4 with clear fallbacks
- clang-cl fallback (SC-3): **HIGH** that it is not needed for feasibility (cl path proven); the contingency note is procedural

**Research date:** 2026-10-12
**Valid until:** 2026-11-12 (toolchain-state facts are machine-anchored; re-verify if VS/BuildTools or the bundled htslib tree changes)
