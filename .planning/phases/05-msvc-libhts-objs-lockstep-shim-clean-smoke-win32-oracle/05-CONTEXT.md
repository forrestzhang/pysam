# Phase 5: 技术债清理 - Context

**Gathered:** 2026-10-13
**Status:** Ready for planning
**Mode:** Auto-generated (milestone-audit debt cleanup — user-directed)

<domain>
## Phase Boundary

清理 v1 里程碑审计（.planning/v1-MILESTONE-AUDIT.md，status: tech_debt）记录的打磨项 —— 全部为 advisory 级，无功能缺口。范围以用户裁决"先清理债务"为准：处理审计 debt 清单中的实质项，注释级微项可顺手处理但不求全。

NOT in this phase: v2 功能项（远程 I/O、PyPI 官方包名）、wheel 逐版本全量套件门（v2 加固建议 W1 记录在案）。

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices at Claude's discretion — debt-cleanup phase. The audit's debt list below is the binding input set.

</decisions>

<code_context>
## Existing Code Insights

### Debt list (from v1-MILESTONE-AUDIT + disposition ledgers — prioritized)

**实质项（用户裁决的清理对象）：**
1. **MSVC_LIBHTS_OBJS 自动 lockstep 检查**（集成警告 W2，最高价值）：setup.py:716-728 的 52-TU 手工镜像 vs htslib/Makefile 展开 —— 加一个机械检查（开发期脚本或 setup.py 自检：MSVC 分支构建前比对 mirror 与 `make print-config` 的 LIBHTS_OBJS 展开，不一致即 fail），消除 htslib 升级漂移风险。参照 D-20 模板 lockstep 的 sed-diff 证明形态。
2. **shim_selftest 哨兵补全**（03-REVIEW IN-01）：win32/msvc/shim_selftest.c 缺 dirent.h 包含（五个 drop-in 只哨兵四个）+ pthread.h/dirent.h 的过期 `#endif /* __GNUC__ */` 标签（IN-02）。
3. **clean_smoke 去硬编码**（04-REVIEW IN-03）：win-wheels.yaml 三处硬编码 3.13/cp313 —— 参数化（workflow input 或 env，默认 cp313）。
4. **win32 samtools_test oracle 强化**（02-REVIEW WR-02，唯一 warning 级残留）：win32 侧 check_statement 两边同走 dispatch 的同码对比（D2-05 已声明弱化）—— 强化方向：win32 对比侧改用 pysam API 读回比对（AlignmentFile/VCF 读回 vs 期望文件），恢复独立性而不引入外部二进制依赖；POSIX 分支不动。

**注释级微项（顺手处理）：**
5. 02-REVIEW IN 项中仍然有效的：probe_symbol_check.py REPO_ROOT 相对路径（01-REVIEW WR 残留）；X_OK 注释已在 WR-03 修复；CIBW_TEST_COMMAND_WINDOWS 注释更正（04-REVIEW IN-01）；msys2-location 插值改 env 间接（04-REVIEW IN-02，benign）。

**不处理（明确记录）：** parse_region 上游继承 IndexError（上游代码，回馈上游而非 fork 私改）；calmd 空串等上游项；Y2038 gettimeofday（与 winsock 结构体对齐，改动风险大于收益）；WR-04 CI 非 UTF-8 locale cell（v2 CI 加固）。

### Constraints (binding)
- 零回归红线全程适用：POSIX/UCRT64 路径字节不动；每项改动过双工具链 smoke + 既有测试；fork CI 全绿。
- 改动全部限定在既有文件 + 至多一个新 devtools 检查脚本；无新依赖。
- NO Co-Authored-By trailers。

### Reusable Assets
- D-20 lockstep 的 sed-diff 机械证明形态（03-01 已建立）
- devtools/probe_symbol_check.py、msvc_compile_probe.py 的探针脚本模式
- 02-PATTERNS 的 check_samtools_view_equal 进程内 oracle 形态（item 4 参照）

</code_context>

<specifics>
## Specific Ideas

Debt list 即规格（上文 1-5 项，1-4 为必做，5 为顺手）。

</specifics>

<deferred>
## Deferred Ideas

v2 项（W1 wheel 逐版本套件门、远程 I/O、PyPI 官方名）—— 见 v1-MILESTONE-AUDIT 与 PROJECT.md Out of Scope。

</deferred>
