# S0_REPORT_CONTENT_CONTRACT（DR-01 Option A；v1.1-draft，M6.1）

**v1.1 变更（Codex HOLD 第 2/3 项）**：①正式 payload 顶层键与本契约
**逐字同构**，权威键表 = `src/itsf/s0/report.py::FORMAL_SECTIONS`
（A1-A12 ＋ A2b `stability_views` 共 13 键，含 `oracle_daily` 复位）；
②新增 A2b：冻结 §2 稳定性视图（三时代/逐年/LOYO/多空必备；
vol_terciles 未裁时 status=unresolved ⇒ 拒封存）；③序列化强制严格
JSON（allow_nan=False、未知类型 raise、禁 default=str）；④validator
逐胞强制 n_boot==10000、block∈{5,21}、per_seed=={7,13,31}、
quoted_seed==7；⑤内部对象（dataset/DataFrame/记录实例）禁入正式
payload（envelope 分离，legacy structural 封存旁路移除）；⑥A9 记录
文件字段用冻结 §10.1 名（entry_timestamp/exit_timestamp）；A12 补
authorized_commit、engineering_seed 实值、七项冻结哈希、registry
sequence 快照。

地位：正式 S0 密封报告的**内容契约**。Stage E 渲染器产出的报告 payload
必须通过本契约的机器校验（`scripts/s0_real_run.py` 内契约校验门）才可
封存；缺任何必需节 = Stage E 失败（run_failure，编号已烧）。
本契约不含任何观测数字；它只规定**必须报告什么**。数字唯一出现地 =
封存后的 runs/<trial>/ 目录。

对应冻结出处逐节标注；契约本身为工程文档（可修订，修订须新 IR）。

## A. 必需顶层节（payload key → 冻结出处）

| # | key | 内容 | 出处 |
|---|---|---|---|
| A1 | structural | 漏斗/F10 双报/NA 表/锚点/标签可用性/eras/groups（现有结构层全保留） | §4/§5/IR-12..24 |
| A2 | oracle_daily | 每 θ∈{0.5,0.3} × engine∈{E1,E2} × scenario∈{Base,Conservative,Stress,Severe}：oracle 日逐日 USD P&L 序列（date 键控），era 分列＋pooled | §7 |
| A2b | stability_views | 冻结 §2 视图：三时代/逐年/LOYO/多空必备＋vol_terciles（未裁=unresolved⇒拒封存） | §2 |
| A3 | theoretical_oracle | 每 θ：TP 日 Base 场景理论 Oracle 逐日 USD 序列（经济上限，独立标注不可执行） | §7 |
| A4 | e2_worst_days | 每 θ × scenario：E2 日 P&L 的 P1/P5（era 分列＋pooled） | §7 表（强制） |
| A5 | sizing_outputs | §8 六字段逐日表（per engine × scenario）＋{$50,75,100,150} 描述性覆盖率 | §8/§10.1 |
| A6 | frequency | 每 θ：p、每年可交易日数、月均频率、（与 A8 联动的）F(q,r) | §10.5（强制） |
| A7 | bootstrap_ci | 每 θ × engine × scenario × {Primary 块5, Sensitivity 块21}：三 seed 各自 CI＋收敛指标＋quoted=seed 7（固定约定声明） | §9 |
| A8 | feasibility_grid | 附录 A 网格：每 (q,r) × 三 seed：realized/target q,r、infeasible 标记、日标记序列摘要、F 公式值；positive_EV/deployable 区域留 MC 填充位（S0 侧不判定） | 附录 A |
| A9 | mc_handoff_manifest | §10.1 原子记录清单：每 engine × scenario 记录数、序列化文件名与 sha256（记录本体存 runs/ 内独立文件，不嵌报告） | §10.1 |
| A10 | era_axis | 所有结果表的 era 轴声明：counterfactual_micro_execution 段禁止表述为真实 Micro 历史 | §6 |
| A11 | disclosures | untradeable 披露、NA 守恒复述、方法约定全披露（stream tag 派生、首 seed 引用约定、DR-M6-A 归约规则、DR-M6-B regime 定义——后两者裁决前 payload 标 PENDING 且 Stage E 拒绝封存） | §9/附录A/DR |
| A12 | governance | trial_id、authorized_commit、engineering_seed（出处戳记）、冻结哈希七项复述、registry 事件序号快照 | packet §0-5 |

## B. 机器校验规则

1. 必需 key 全存在且非空（A8 的 MC 填充位除外——必须存在且显式标
   `pending_mc`）；
2. A2/A4/A5/A7 的 θ×engine×scenario 覆盖矩阵完整（2×2×4；A7 另乘
   块长 2）；缺胞 = 拒绝；
3. A7 每胞必含 per_seed{7,13,31} 三组＋convergence＋quoted_seed==7；
4. A11 若含任何 PENDING 决策 → Stage E 拒绝封存（fail closed）；
5. A9 记录数守恒：records 数 == oracle 日数（TP）＋FP 日数，per
   engine × scenario；
6. 词汇守卫沿用：报告字符串不得进入日志（整文档封存唯一释放）。

## C. 版本

v1.1-draft（M6.1）：A2b 入 §A 表、封存规则见页首；v1.0-draft（M6）：结构定稿，待 DR-M6-A/B 裁决后升 v1.0 并入首个
可运行候选。修订走 IR 流程。
