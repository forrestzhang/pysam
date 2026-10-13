# Retrospective

## Milestone: v1 — Windows 适配

**Shipped:** 2026-10-13 · **Phases:** 5 | **Plans:** 16 | **Tasks:** 48

### What Was Built
UCRT64 开发构建链（Phase 1）→ 全套件 Windows 全绿 + 可移植层（Phase 2, 1027→1034/15/0）→ MSVC 并行工具链（Phase 3, 双工具链同绿）→ CI + 线上 Release v0.24.1-win.2 六 wheel（Phase 4）→ 债务清理含 52-TU 机器 lockstep（Phase 5）。

### What Worked
- 实证先行：每个 phase 的 researcher 在真机编译/运行探针（Cython 3.3.0 证伪、cibuildwheel 本地全链路、VS 2026 实况）——plan 建立在事实上而非文档传说
- #ifdef + #else 原文的守卫形态贯穿全程，零回归红线从未破（fork CI 每 push 验证）
- SHA 钉扎 CI 判定纪律 + "绝不以进行中列表下结论"
- TDD 牙齿测试（WR-01 解码、win32 oracle 6 轴）与机械 lockstep 证明（D-20 sed-diff、D-25 lockstep self-test）

### What Was Inefficient
- stale-refresh 跑了三轮（phase 2 后、milestone close 前 ×2 轮）——指纹保鲜与迭代的固有张力，里程碑收口前的集中刷新是必要成本
- 计划中的 verify 命令两轮零匹配 grep 退出码问题（round-1 checker 均抓出）——planner 对"零期望"命令的退出语义是反复出现的盲点

### Key Lessons
- MSYS2 头文件/库绝不跨工具链（zconf.h 含 unistd.h 实证）→ vendor 是唯一干净解
- MSVC 无 GNU ld 自动导入：跨模块数据绑定必须声明点 dllimport（D-23）
- delvewheel 默认修复在跨模块 .pyd 上必崩（casemap 缺 --ignore-existing 时）——本地端到端探针在进 CI 前抓住了它
- 线程 httpserver × 持 GIL 的 dispatch 在 POSIX 上互相饿死（D-19）——测试基建的平台分裂是必要而非洁癖

### Cost Observations
- 模型组合：opus 规划 + sonnet 执行/研究/验证 + haiku 检查
- 16 plans 全 autonomous 除一个 blocking-human 供应链门（用户裁决）+ 一个 WR-01 workflow 禁用裁决
