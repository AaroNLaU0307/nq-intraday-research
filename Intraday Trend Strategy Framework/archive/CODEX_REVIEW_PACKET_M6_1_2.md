# CODEX_REVIEW_PACKET — M6.1.2（供 Codex 独立检查真实仓库）

- 审查对象：本 packet 所在 commit（`git log -1` 取；单一候选，自 ffb1647）
- 状态不变量：未 READY、未申授权、真实 S0 锁定、registry 未动、零真实
  研究数字（RealChain._ensure 全程未调）

## CLOSED（本轮，Opus 审计 18 新奇反例后闭合其全部 1 High＋7 Med）

| 类 | 内容 |
|---|---|
| 重算不读旗（N5 High） | 稳定性守恒由 validator **重算**（各分区轴 Σn==n_tp、LOYO n==total−by_year、删桶/充胀/全零/仅剩旗全拒）——自报 conservation_ok 不再被信任 |
| 深层校验（S1 前置） | A1-A12 叶级真实 producer 类型；20 族×{None/错类型/垃圾 dict}；day-universe 五不变量＋θ 嵌套单调（N1）；63 点 producer-derived 网格；oracle/theoretical 深结构 |
| 对账（N11/N16/N17） | A11 na_conservation 与 structural.na_table **数额对账**；序列块 ghost 日期/假 sum/假 mean 重算拒绝 |
| 封存记录类型（N2） | JSONL 逐字段叶类型（数字字符串"20000.0"/"1" 拒绝） |
| 空研究地板（N15/N13） | 零日 universe 永不封存；sizing rows 数==n_tp 恒等式 |
| infeasible（N6） | infeasible 点带 per_seed 选择即拒 |
| 全文件完整性（N18） | sealed_files manifest（sha256+bytes）覆盖渲染器全部产出（S0_REPORT.json 自排除、Stage-F 链封盖）；多余/未哈希文件拒绝 |
| admission（前轮） | formal_sealable 被消费：SEED_MANIFEST 今日扣留、HANDOFF_ADMISSION.json 披露、可封存则接纳双向证明 |
| 8 胞矩阵/轴锁/scanner | verify_handoff_conservation 冻结 8 胞枚举；θ/engine/scenario/seed 轴锁＋SEED_MANIFEST 交叉；scanner 父包 __init__ 入闭包（隔离仓变异证明） |
| 非法配置 | structural_problems 类型/不变量校验＋使用点复验：test_only/部分/结构非法注入均无法使 ready() 为真 |
| stats | n_boot 强制 int（10000.0 拒）；block_len 报告字段保 int、float 仅入 RNG 流；20260731 四入口全拒 |

## PARTIAL（如实，非生产完成）

- 方法单源：六字段（spread_cost/volatility_regime/fp_allocation/
  bootstrap_method/grid_policy/stability_population）无消费者，行为探针
  =None 且机器断言生产端必为 None；唯 event_na_mapping 有行为级探针。
- replay：PARTIAL_single_stratum_only（DR-B/F 未裁无真实层键）。
- DAY_STRATA/GRID_SAMPLES 未由渲染器构建；SEED_MANIFEST 被 admission
  扣留在封存集外。
- 配置可调用项仅保证 callable()（回调运行时抛错不预检，已文档化）。

## DECISION_REQUIRED（七项全份见 DECISION_REQUIRED_M6_1.md r3）

DR-1 spread＋IR-7；DR-2 vol 逐字（21 closes/20 returns 统一）；DR-3 FP
基准（unresolved_disagreement Fable B/Sol A）；DR-4 七分项；DR-5 K
（75,600 unique/604,800 evaluations；跨政策平台 CRN 按 MC §5 冻结移出
裁决面）；DR-6 event NA 词表；DR-7 stability 总体。
流程：本包过 Codex 后 Fable×Sol 对 DR-2/4/5/7 逐项 cross-critique，
再交 Aaron。

## 验证主张

pytest **926/0/0** == 地板 == 钉；扫描 CLEAN（import-closure 含父包
__init__＋未跟踪文件）；冻结哈希 7/7；diff-check 净；packet §0 12 行
哈希全当前。三轮 Sonnet（S1 177→S3r 207 report 测试；S2 86）＋主代理
接线；Opus 审计 18 反例（10 复跑全红＋18 新奇中 8 类缺口全闭）。
