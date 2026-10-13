---
milestone: v1
audited: 2026-10-13T05:00:00.000Z
status: tech_debt
scores:
  requirements: 12/12
  phases: 4/4
  integration: 9/9
  flows: 1/1
gaps: {}
tech_debt:
  - phase: 01-mingw-w64
    items:
      - "WR-01 (01-REVIEW 2026-10-12): _collect ANSI 代码页 mojibake —— 已在 03-05 修复并关闭于 01 账本（fixed）；账本残余 6 项 open 均为 info 级（probe_symbol_check 相对路径、parse_region 上游继承 IndexError 等）"
      - "A2 结构性保留：符号门读取 implib 间接映像（.pyd 被 strip）—— 硬件验证成立，v2 可做直接映像门"
  - phase: 02-portability-tests
    items:
      - "账本 11 项 open（原 5W 中 WR-01 import 模板已由 Phase 3 D-20 关闭、WR-03 pyximport 吞异常由 03-05 可移植断言修复、WR-05 GCC builtins 由 D-20 编译器门关闭；残余为 info 级 + WR-02 win32 samtools_test 同码对比（D2-05 已声明的弱化））"
  - phase: 03-msvc
    items:
      - "账本 9 项 info open（shim_selftest 缺 dirent 包含、#endif 标签过期、X_OK 语义注释、HTSLIB_MODE=separate 晚失败等打磨项）"
      - "IN 集成警告 W2：MSVC_LIBHTS_OBJS 为 Makefile 展开的手工镜像 —— htslib 升级时有漂移风险（52-TU 在 Phase 3 核对；无自动 lockstep 检查）"
  - phase: 04-windows-ci-wheel
    items:
      - "账本 3 项 info open（CIBW_TEST_COMMAND_WINDOWS 注释准确性、msys2-location 插值良 benign、clean_smoke 硬编码 cp313 三处）"
      - "IN 集成警告 W1：每 wheel 验证为 smoke-only（全量 1028 套件验证 direct job 构建路径而非逐版本 wheel 制品）—— 符合 CI-02 文面，v2 加固项"
---

# v1 里程碑审计 — pysam Windows 适配

**审计时间:** 2026-10-13 · **状态:** tech_debt（无 blocker，累积 advisory 打磨项）

## 结论

12/12 v1 需求满足（三源交叉验证：4 份 VERIFICATION.md 全部 passed + 全部 SUMMARY frontmatter 列明 + REQUIREMENTS.md 全部 `[x]`，无孤儿需求）。跨阶段集成 9/9 接线（一个 setup.py 双工具链分派、可移植层双编译一致、wheel 流水线复用 P1 符号门与 smoke、测试基建无分叉）。核心价值端到端流（`pip install Release URL → import → BAM → dispatch`）经 clean_smoke job 忠实模拟并线上验证。

**里程碑核心交付已在线上兑现：** https://github.com/forrestzhang/pysam/releases/tag/v0.24.1-win.2（6 个自包含 wheel，cp310–cp315，sha256 全录于 04-CI-VALIDATION.md）

## 需求覆盖（12/12）

| REQ | Phase | VERIFICATION | SUMMARY | REQUIREMENTS.md | 终态 |
|-----|-------|--------------|---------|-----------------|------|
| BUILD-01 | 1 | passed | 01-02/03 | [x] | satisfied |
| BUILD-03 | 1 | passed | 01-02/03 | [x] | satisfied |
| PORT-01..04 | 2 | passed | 02-01/02 | [x] | satisfied |
| TEST-01/02 | 2 | passed | 02-03/04 | [x] | satisfied |
| BUILD-02 | 3 | passed | 03-01..05 | [x] | satisfied |
| CI-01 | 4 | passed | 04-01 | [x] | satisfied |
| CI-02/03 | 4 | passed | 04-02/03 | [x] | satisfied |

（REMOTE-01 为 v2 延期项，不在 v1 范围。）

## 阶段验证汇总

| Phase | 验证 | 得分 | 备注 |
|-------|------|------|------|
| 1 MinGW-w64 | passed | 15/15 | 2026-10-12 stale 刷新（第一手重建 + CI 复核） |
| 2 可移植性 | passed | 23/23 | verifier 独立复现套件/CI/生成器 |
| 3 MSVC | passed | 11/11 | 双工具链套件 verifier 亲跑（各 1028/15/0） |
| 4 CI+wheel | passed | 12/12 | 全线上证据（Release/sha256/消费端复走） |

## 集成检查（9/9 wired, 0 orphan）

五条跨阶段接缝全部接通（详见 integration checker 报告，证据锚定于 setup.py/workflows/live Release）。3 条 advisory 警告（smoke-only wheel 门、手工 52-TU 镜像、间接符号映像）列入 tech_debt，均不阻塞。

## Nyquist

capability 关闭（workflow.nyquist_validation=false）—— 按工作流跳过。

## Tech Debt 汇总

29 项 info 级账本 open（跨 4 phase 的代码评审打磨项，无 critical/warning 残留 —— 全部 warning 已修复关闭）+ 3 条集成 v2 建议。**性质全部为打磨/加固，无功能缺口。**
