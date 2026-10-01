# CODEX_REVIEW_PACKET — M6 完整生产链（供 Codex 独立检查真实仓库）

- 审查对象 commit：`08fca9bd47837489e7a84fcc4107f2fc7ce807b4`
- 基线（Codex HOLD 裁定时）：`4c5e7979d6808e426a819f8315ee9bf4d0e73255`
- 性质：DR-01/DR-02 Option A 落地；单一里程碑候选；**未追加 READY、
  未授权、真实 S0 仍锁、registry 本 commit 未动**

## 变更面（14 文件，+3593/−17）

| 面 | 内容 |
|---|---|
| DR-02 | contracts.RESEARCH_BOOTSTRAP_SEEDS=(7,13,31) 单一真源；RunConfig.seed→engineering_seed（仅出处戳记）；进程内冻结常量门双钉；packet §5 重渲染 |
| 研究模块（新） | s0/study.py（确定性 study 层，33 测试）；s0/stats.py（三 seed 平稳 bootstrap CI，块5/21、10k、百分位95、收敛＋首 seed 引用约定）；s0/gridmix.py（附录 A 网格：floor/ROUND_HALF_UP/最大余数分层均匀抽样/缺额再分配/infeasible/realized vs target/F(q,r)/反排序不变性） |
| 入口编排（主代理） | make_day_inputs（OR 极值仅取 OBS 窗）；build_full_study_result（契约 A1-A12 payload）；validate_report_contract（§B 机器校验）；render_s0_report 全链分发（MC_HANDOFF JSONL＋sha256 manifest；契约违规拒封存） |
| fail-closed | PENDING_METHOD_DECISIONS（DR-M6-A/B/C）→ chain.ready=False（Stage B 拦截，不烧号）＋compute 双保险 raise；合成 e2e 以注入参数走通全链（21 测试） |
| 契约/设计 | S0_REPORT_CONTENT_CONTRACT.md v1.0-draft；ops/M6_TASKBOARD/M6_DESIGN.md |

## 需 Codex 独立验证的主张

1. **电池**：pytest 612/612、0 skipped；地板=收集数=钉=612；
   guards.verify_frozen_hashes 过；final_candidate_scans CLEAN。
2. **DR-02 隔离**：六个研究模块源码零 `20260731`/`engineering_seed`、
   import 行零 RunConfig；study/oracle/paths/costs 零 RNG；
   stats/gridmix 的 seeds 默认值就是 contracts 常量对象（变异守卫）。
3. **冻结忠实**（抽样重点）：paths.build_record 对 §10.1 双数组/截断/
   adverse 规则逐条；gridmix 取整两陷阱（floor 浮点、banker's）；
   stats 分位法与三 seed 独立流；study 的 θ 边界（==θ 属 TP）、
   守恒恒等式、E2 P1/P5 强制块。
4. **fail-closed**：真实 ready() 现返回 False 且含 DR-M6 字样；
   compute 在数据装载前 raise；contract 校验对 pending payload 拒绝
   （双向测试在 test_m6_chain.py）。
5. **范围**：runner.py/runinfra.py/dataset.py/labels.py/features.py/
   context.py/guards.py 对基线字节不变（唯 contracts/入口/测试/新模块/
   包 §0 两行哈希变动）；registry 与 HANDOFF 未动。

## 开放方法决策（升级中，Aaron 待裁）

- **DR-M6-A**：spread_cost_table（逐分钟 slot）→ (median,P90,P95) 三标
  量归约规则（QA 口径 RTH slot 聚合 vs 交易窗聚合 vs 池化——池化预否，
  违 §1 隔离）。
- **DR-M6-B**：附录 A 分层键 volatility_regime 冻结文本用而未定义
  （年内 ADR14 三分位 / 全样本三分位 / F4 rvol 口径）。
- **DR-M6-C**（SA-18 发现）：冻结"缺额按其余层再分配"规则在自池比例
  分配下不可达；仅当 FP 抽样须复制 TP 层构成时才有触发点——FP 分配
  基准需裁决。
- 次级披露（非决策）：S0 层三 seed 收敛无数值容差（仅披露端点最大差）；
  realized_precision 空胞=None；infeasible 胞报告形态。

裁决落地路径：三项 DR → IR-27 → 入口注入真实参数＋compute 接
build_full_study_result → 契约升 v1.0 → 聚焦审计 → READY → §10。
