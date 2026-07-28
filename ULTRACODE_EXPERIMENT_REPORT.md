# ULTRACODE_EXPERIMENT_REPORT — 2026-07-28 受控实验（一次性授权）

```yaml
ultracode_auto_orchestration_enabled: false   # 本轮结束，恢复受控手动派工模式
```

## 实际编排

**创建 subagent 数：7**（计划 7 = 实际 7；未为"充分利用多代理"加量；
用户建议清单中的"数据读取与schema QA"被合并进主 agent 脚手架并推迟——
禁真实数据约束下 loader 无法有意义测试）。

| Agent | 任务 | 产出 | 测试 |
|---|---|---|---|
| calendar | Session/DST/假日/ADR14/roll | calendar.py | 17 通过 |
| features-labels | F1–F11＋标签（冻结公式） | features.py, labels.py | 18 通过 |
| costs-oracle-paths | signed-d 成交/双Oracle/E1-E2/双路径 | costs.py, oracle.py, paths.py | 27 通过 |
| lucid-platform | LucidFlex 全生命周期状态机 | lucid.py | 14 通过 |
| topstep-platform | Combine→XFA＋订阅/Credit 引擎 | topstep.py | 16 通过 |
| mc-engine | bootstrap/sizing/判定表 | bootstrap.py, account.py, verdict.py | 31 通过 |
| spec-audit | 只读规范符合性审计 | 13 findings（1高/6中/6低） | — |

**主 agent 预置**（派工前冻结接口）：contracts.py、guards.py（冻结哈希自检＋双 flag
运行门）、base.py、conftest.py、包结构。**主 agent 集成**：R1–R4 四项代码修复、
6 处测试断言按裁决更新、全量 123/123 通过、ADJUDICATIONS.md、本报告、commit。

## 实验观测（按授权要求逐项）

- **递归派发**：无（prompt 明令禁止，未发生）。
- **重复探索/冲突修改**：文件所有权互斥执行到位——零同文件冲突、零重复模块。
  出现 **1 处并行设计裂缝**（audit M5）：mc-engine 针对 Protocol 鸭子类型写通用循环，
  平台 agent 各自实现自含 Lifecycle——两半接口不咬合＋breach 约定三处分叉。
  已裁决（R1/R5）。另 1 处良性：mc-engine 因所有权清单没有 test_account.py，
  把 sizing 测试放进 test_bootstrap.py（有注释）。
- **无效工作**：无成块废弃；无整体驳回。
- **主 agent 驳回/重做**：4 项审计确认的代码缺陷由主 agent 修复（含 1 项高危：
  全局 40 手上限错切 Topstep 的 50）；6 处测试期望按裁决改写；集成中主 agent
  自己算错 2 个期望值（对 helper 路径构造的假设错误），当轮修正——如实记录。
- **subagent 规范阅读**：每个 agent 的 spec_sections_read 已在 workflow 结果存档
  （journal.jsonl）；实现 agent 各读 4–9 个章节，audit 读全部三份冻结文件＋全部代码。
- **遥测（系统提供的真实值）**：subagent 总 tokens = 726,205；工具调用 = 120；
  墙钟 = 18 分 38 秒；agent 全部成功（7/7，0 错误 0 空结果）。
  主 agent 侧协调消耗的精确 token/context 数：**不可获得**；费用美元数：**不可获得**。
- **审计 agent 附注**：系统提示其安全分类器当轮不可用；主 agent 已逐条人工核验其
  findings（全部与代码实况相符）并确认其只读（git status 干净、冻结哈希完好）。

## 定性效率判断

- **Token**：726k subagent tokens 产出 14 个源文件＋123 个测试。单 main-agent 顺序
  实现同等内容的 token 消耗大概率**显著更低**（免去 6 份规范重复阅读、7 份 schema
  回报、审计重读全部代码）；粗略方向判断为 2–4 倍开销，不给精确倍数（不可测）。
- **墙钟**：18.6 分钟并行完成 6 模块——顺序实现无法接近；这是本轮最大真实收益。
- **质量**：unresolved 上交纪律（16 项真问题全部停下上交而非擅自发挥）＋独立审计
  （抓到 1 个真高危 bug＋breach 约定三处分叉）的价值高；但并行也**制造**了那个
  接口裂缝——顺序实现不会发生 M5。净质量收益主要来自 audit agent，而非并行本身。
- **协调开销**：主 agent 在 prompt 撰写、结果消化、裁决与返工上的上下文占用可观
  （不可精确计量）；7-agent 规模已接近单轮可舒适协调的上限。

## 下轮分工建议（恢复受控模式后）

保留：**spec-audit 独立审计**（性价比最高，建议成为每个里程碑的固定关卡）；
平台状态机按平台各一 agent（隔离效果好）。
合并：calendar＋features（接口天然衔接，拆开收益小）。
改顺序：mc-engine/orchestrator 必须在平台接口定稿**之后**派发（本轮 M5 的根因）；
business-layer orchestrator 由主 agent 亲自写或单独一个 agent 顺序做。
取消：专职 data-loader agent 直至真实数据阶段解封。

## 下一里程碑（受控模式）

1. business-layer orchestrator（Lifecycle 驱动＋synthetic 日历＋failure/attempt 政策）；
2. G9 解除（CME 费表浏览器渲染快照）＋ Aaron 第二物理副本 → 双 flag 落地；
3. 真实数据 loader（内置 assert_real_run_allowed，R6）；
4. S0 运行 → MC → Checkpoint 0。
