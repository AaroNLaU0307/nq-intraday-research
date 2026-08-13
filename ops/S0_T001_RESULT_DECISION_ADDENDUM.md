# S0_T001_RESULT_DECISION_ADDENDUM（揭盲结论追加式纠正，2026-08-14）

授权：具名提示词
`START_DR5_MC_CONSUMER_ENGINEERING_AFTER_S0_REVEAL_REVIEW_CORRECTION`。
本文件**追加**于既有揭盲备忘录（当轮聊天终报）与
`ops/S0_T001_RESULT_REVEAL_ATTESTATION.md` 之上，不重写不覆盖原文；
全部纠正针对**同一批已揭露结果的解释**，零新增研究关系暴露。
每项纠正均经 Fable 对封存报告机械复核后采纳（Level-1 验证）。

## 现势结论（取代原四层/推荐表述，冲突处以本表为准）

```
STATISTICAL_SIGNAL=NOT_TESTED
ORACLE_FEASIBILITY_CEILING=PASS
Q1_BASE_RATE=DELIVERED
Q1_Y_CONT_DISTRIBUTION=PARTIAL_NOT_REPORTED
Q2_ORACLE_FEASIBILITY=SUPPORTED
Q3_CHECKPOINT_0=INCONCLUSIVE_PENDING_MC
OVERALL_S0_VERDICT=INCONCLUSIVE_PENDING_MC
RECOMMENDATION=HOLD_FOR_SPECIFIC_MISSING_EVIDENCE
MISSING_EVIDENCE=DR5_MC_FP_ECONOMICS_AND_DEPLOYABLE_REGION
```

原备忘录的 `STATISTICAL_SIGNAL=PASS`（带 oracle 条件限定）按更诚实的
分类法改记：S0 不含任何事前信号检验，故该层为 **NOT_TESTED**；oracle
可行性天花板作为独立断言记 **PASS**。原
`RECOMMENDATION=PROCEED_TO_STRATEGY_SPEC` 撤回，改为
**HOLD_FOR_SPECIFIC_MISSING_EVIDENCE**：缺失证据＝DR-5 MC 的
FP 经济学与 deployable_region——这正是本轮工程构建其消费者的原因。

## 逐项撤回/限定

1. **撤回"S0 bootstrap 证据使 STOP 条件显得不太可能"一类任意方向的
   Checkpoint-0 推断**。S0 bootstrap 是 TP-oracle 口径（非选中日按零
   处理），不含 false-positive 损失、prop 路径经济性与平台失败状态；
   Checkpoint-0（预注册 §10.4）**尚未被任何证据检验**，其判定统计量
   （MC 认知层 prop_operating_EV 分布）尚不存在。
2. **撤回"Option C 共享 taxonomy 已由 2621 测试锁定"**。现存并经测试
   锁定的是 S0 的 funnel/NA/era 基础结构；两个 post-S0 候选共同使用、
   方向中性且互斥穷尽的 ON/touch/hold/recapture/double-touch taxonomy
   **尚未形成**，属策略规格阶段工作。
3. **撤回 sensitivity"≈1.3%、可忽略"表述**（跨总体除法：1520 条 stop
   记录的总体≠pooled TP-only 总体）。仅允许报告：

   ```
   SENSITIVITY_TOTAL_DELTA_USD=-760
   SENSITIVITY_E1_STOP_RECORDS=1520
   SENSITIVITY_DELTA_PER_STOP_USD=-0.50
   RELATIVE_PERCENTAGE=NOT_COMPARABLE
   MATERIALITY_CONCLUSION=NOT_ESTABLISHED
   ```

4. **更正收敛表述**：原"max-diff ≤ $0.20"系压缩取整所致失真。精确值
   （Fable 对封存字节复核，逐位一致）：

   ```
   MAX_BOOTSTRAP_ENDPOINT_SPREAD=0.20477498240675374
   ```

   （位于 theta_0.5|E1|Severe|block21 的 max_abs_ci_hi_diff。）
5. **限定稳定性口径**：full_eligible 人口块存在 **16 个有效的
   zero-direction 格（n=40，mean=0.0）**。正确表述为"**可比较的非零
   方向/时期格未观察到负均值**"，不得写"所有 subcells 均为正"。
6. 本纠正不增加研究关系暴露；exposure ledger 追加 quantity=0
   交叉引用行，累计保持 **1575**。
