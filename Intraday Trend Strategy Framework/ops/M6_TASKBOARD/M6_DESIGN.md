# M6 设计 — 完整 S0 生产链（Codex HOLD → DR-01/02 Option A）

状态：ACTIVE（AUTONOMOUS_MILESTONE_MODE）。目标＝单一里程碑候选 commit
＋CODEX_REVIEW_PACKET；不追加 READY、不授权、不运行真实 S0。

## 0. 差距矩阵（M6-recon 结论）

| 冻结要求 | 现状 | 缺口 |
|---|---|---|
| §7 双 Oracle（θ 0.5 主/0.3 副全报） | oracle.py 逐日函数完备 | 无日集选择/编排层 |
| E1/E2 × 四成本场景 §10.1 原子记录 | paths.build_record 完备 | 无全样本生成器 |
| §6 场景参数（Base/Cons/Stress/Severe） | costs.build_scenarios 完备 | 三标量来源未锁（DR-M6-A） |
| §8 整数仓位逐日输出＋覆盖率 | sizing_anchor_usd 存在 | realized/cost_pct_of_R/覆盖率未编排 |
| §9 bootstrap（块5/10k/{7,13,31}/百分位95CI；副块21） | mc/bootstrap.py 有索引器 | S0 级 CI 层不存在 |
| 附录 A（D_TP/D_FP＋(q,r) 网格分层均匀抽样） | 无 | 全缺；volatility_regime 未定义（DR-M6-B） |
| 频率输出（p/年可交易日/月频/F(q,r)） | dataset._frequency_cell 部分 | 需并入正式报告 |
| era 双轴分列 | ds.eras 存在 | 需贯穿所有结果表 |
| 正式报告内容契约（DR-01） | render_s0_report 仅结构层 | 契约文档＋机器校验＋渲染器全缺 |
| DR-02 seeds | RunConfig.seed=20260731 注释"bootstrap only" | 违 §9；须改名隔离＋{7,13,31} 接线 |

## 1. 架构（模块边界＝agent 边界，零文件交集）

```
dataset(ds) + universe + bars_by_date
   │
   ├─ scripts 入口（main agent）：spread_cost_table.csv → 三标量
   │    （归约规则 = DR-M6-A 参数注入，PENDING_AARON）→ costs.build_scenarios
   │
   ├─ s0/study.py（SA-17）：oracle 日集（θ×era×engine×scenario）→
   │    TradePathRecord 全集＋theoretical oracle＋§8 逐日输出＋
   │    D_TP/D_FP＋E2 最差日 P1/P5＋频率块
   │
   ├─ s0/stats.py（SA-18）：S0 级 stationary bootstrap CI
   │    （块5主/块21副、10k、master seeds {7,13,31} 逐一跑＋合并规则、
   │     百分位 95% CI、三 seed 收敛检查）
   │
   ├─ s0/gridmix.py（SA-18）：附录 A 网格
   │    （分层 year×volatility_regime×event_flag——regime 映射参数注入
   │     PENDING_AARON；floor/round_half_up/比例再分配/infeasible 标记/
   │     realized q,r/日标记序列/F(q,r)）
   │
   └─ 入口 render_s0_report（main agent）：REPORT_CONTENT_CONTRACT
        机器校验后封存
```

## 2. 开放方法决策（升级类型 1，随里程碑收口一并交 Aaron）

- **DR-M6-A**：spread_cost_table（逐分钟 slot 行）→ (median, P90, P95)
  三标量的归约规则。候选：A=RTH 全时段 slot 分位数聚合（QA 报告口径：
  slot-median 的 median/quantile）；B=交易窗 10:00–15:44 slot 聚合；
  C=n_obs 加权池化分位（需回 BBO 重算，违 §1 隔离——预否）。
  机制先行：三标量作为 build_scenarios 显式入参，锁定规则后由入口注入。
- **DR-M6-B**：附录 A 分层键 `volatility_regime` 冻结文本用而未定义。
  候选：A=按年内 ADR14 三分位（低/中/高）；B=按全样本 ADR14 三分位；
  C=F4 rvol 口径。机制先行：gridmix 接受 date→regime 映射参数。

## 3. DR-02 落地（main agent）

- contracts.py：新增 `RESEARCH_BOOTSTRAP_SEEDS = (7, 13, 31)`（frozen:
  S0 §9/附录A/MC §(b)）；`RunConfig.seed` 改名
  `engineering_seed`（注释：run-infra 专用，禁入研究路径）。
- 隔离证明测试：研究模块（study/stats/gridmix/oracle/paths/costs）源码
  与调用图中不得出现 engineering_seed/20260731；stats/gridmix 的 RNG
  只能由 RESEARCH_BOOTSTRAP_SEEDS 派生。
- packet §5 seed 条目重渲染（20260731 → 工程 seed 定位）。

## 4. 收敛与合并规则（工程约定，报告全披露）

- §9 Primary CI：三个 master seed 各自跑满 10,000 次→三组 CI；
  **报告全部三组＋收敛检查**（MC §(b) 口径：判定类别一致；S0 层=
  CI 端点最大绝对差披露）；正式引用值=seed 7 组（约定，非选择性：
  固定第一 seed，禁止择优）。
- 网格点子流派生：`np.random.default_rng([master, GRID_STREAM_TAG,
  q_mil, r_mil])`（SeedSequence spawn 数组式，确定性、与顺序无关）。
- bootstrap 子流同理 `[master, BOOT_STREAM_TAG, block_len]`。

## 5. 验收（M6-close 门槛）

合成 e2e：合成市场→全链（study→stats→gridmix→report contract 校验）
全绿；变异验收≥3（改 seeds→红；D_TP/D_FP 混层→红；契约缺节→红）；
全电池＋扫描；单一候选 commit＋CODEX_REVIEW_PACKET_M6。
