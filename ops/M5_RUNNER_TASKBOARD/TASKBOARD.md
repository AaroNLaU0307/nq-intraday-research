# M5 任务板 — S0 Runner 实现（PENDING_AARON）

状态：任务板与提示词已备，**无 subagent 已启动，无真实 S0 运行**。
基线：授权包治理框架已批（PACKET_DRAFTED），八条修订已落。派工模式：
手动受控（Aaron 逐个回复"启动SA-X"）。

## 里程碑目标

实现首次真实 S0 的 runner 全链（纯函数计算库＋运行基础设施＋入口状态
机），通过审计后重渲染最终授权包至 READY_FOR_RUN_AUTHORIZATION。
本里程碑**不运行**真实 S0/Oracle/收益/EV/MC/Checkpoint 0；全部开发与
测试只用合成 fixture。

## 任务清单

| Task | 名称 | 执行者 | 状态 |
|---|---|---|---|
| M5-T0 | 共享接口定稿＋现状审计（见 M5_T0_INTERFACE_AUDIT.md） | main agent | **完成**（PACKET_APPROVED 事件已录；contracts 扩展已落；纠正初版"新建"错误——features/labels/oracle/costs/paths 均有历史实现，REPLACE_PROHIBITED） |
| M5-T1 | S0 计算**缺口补齐**（context.py＋dataset.py 新建；五个既有模块 KEEP） | **SA-4** | 待 Aaron 启动 |
| M5-T2 | 运行基础设施 runinfra.py（真实新建） | **SA-5** | 待 Aaron 启动 |
| M5-T3 | runner 入口＋Stage A-F 状态机＋13 硬门＋attempts→runs 原子转换＋registry 事件 | main agent（保留） | 阻塞于 T1+T2 集成 |
| M5-T4 | 只读对抗审计 | **SA-6**（建议，提示词届时出） | 阻塞于 T3 |
| M5-T5 | 最终授权包重渲染（环境锁定七件套）→ READY_FOR_RUN_AUTHORIZATION | main agent（保留） | 最后 |

建议 subagent 数量：**2**（SA-4 ∥ SA-5，文件所有权不相交）＋1 个审计
（SA-6，集成后另出提示词）。

## 派工模型与 effort 建议

| SA | 模型 | effort | 并行 |
|---|---|---|---|
| SA-4 核心计算 | Claude Opus 5 | high | 可与 SA-5 并行 |
| SA-5 运行基础设施 | Claude Sonnet 5 | high | 可与 SA-4 并行 |
| SA-6 审计 | Claude Opus 5 | xhigh | 集成后单独跑 |

## 文件所有权

| 任务 | 允许 | 禁止 |
|---|---|---|
| SA-4 | `src/itsf/s0/context.py`、`src/itsf/s0/dataset.py`（新建）；`features.py` 仅限 F10-NA 校验单点（M5_T0 审计明示）；`tests/test_s0_context.py`、`tests/test_s0_dataset.py`（新建） | `labels.py`/`oracle.py`/`costs.py`/`paths.py`（READ-ONLY，REPLACE_PROHIBITED）、`__init__.py`、`src/itsf/contracts.py`、冻结文件、`src/itsf/data/**`、`guards.py`、`src/itsf/mc/**`、`scripts/**`、registry、授权包、SA-5 文件、既有测试文件（只增不改原则下新测试独立命名） |
| SA-5 | `src/itsf/s0/runinfra.py`（新建）；`tests/test_runinfra.py`（新建） | 同上＋SA-4 文件 |
| main | `scripts/s0_real_run.py`、`src/itsf/contracts.py`（包顶层，共享接口唯一维护者）、`src/itsf/s0/__init__.py`（包级导出）、`ops/TRIAL_REGISTRY.md` 事件追加、环境锁定七件套采集、授权包重渲染、集成 commit | — |

## 依赖与并行

SA-4 ∥ SA-5（零文件交集）→ main agent 审查集成（T3）→ SA-6 审计 →
T5 重渲染。SA-4/5 均不得读取 C:\Users\Aaron\quant-data 任何真实文件。

## main agent 保留职责

runner 入口与 Stage A-F 状态机；TRIAL_REGISTRY 状态转换（事件追加只能
由 main agent 执行）；共享 contracts/config（src/itsf/contracts.py 由
main agent 先行定稿，两个 SA 依赖其类型签名）；冻结规范最终解释；
SA 成果审查、unresolved 裁决、全量测试、seal/structure/frozen-hash、
git diff 审计、集成 commit；最终包重渲染与环境锁定。

## 必读冻结章节（提示词内已列）

预注册行 41-45（约定/剔除/NA）、49-63（ADR14/F1-F11）、75-96
（MVE/retrace/路径/标签公式）、86-91（标签表）、130-145（Oracle 判据
θ、E1/E2 定义）、236（频率输出）；IR-1..20 全部；授权包 §5/§7。

## 潜在决策点（预计需 Aaron＋ChatGPT，SA-4 遇到即 STOP 出包）

| 候选 | 内容 |
|---|---|
| D-EXEC | executable Oracle 的成交假设细节若预注册 §6 未唯一确定（entry/exit 的 bar 内成交价与 slip 叠加次序） |
| D-BOOT | bootstrap CI 规格若冻结文本未唯一确定（块长/重采样单位/CI 类型） |
| D-E1FILL | E1 止损在 bar 内 gap-through 时的成交价约定若与 IR-1（MC 层近似）之间需要 S0 层独立解释 |
| D-Y23 | Y2/Y3 公式实现细节若行 86-91 存在读法分歧（IR-11 已解 Y3 一部分） |

## 验收基线

全量 pytest（当前 234）只增不破；每个新模块有合成 golden 测试
（手算可验的小 fixture）；无前视断言（特征只用 ≤ 当日数据）机器化；
runner 相关全部代码零命令行参数覆盖能力；Stage C 词汇守卫测试在。
