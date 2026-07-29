# IMPLEMENTATION RESOLUTIONS — B 类实现裁决登记（Addendum 候选）

> 定义：冻结规范存在歧义、且实现选择可能影响数值结果的裁决。
> 本文件不是冻结规范的同级依据；每项候选待 Aaron 批复后方可视为 Addendum 定案。
> A 类（规范唯一推出）裁决继续记录于 ADJUDICATIONS.md；C 类（冲突）= 立即停止，当前为零。

## 2026-07-28 登记（milestone 2 Phase 0 分类）

| ID | 内容 | 冻结章节 | 可能影响的输出 | 选择理由 |
|---|---|---|---|---|
| IR-1 (=R1) | breach 结算 = min(floor, 分钟 adverse 极值) − n×$1 | MC §2.2 | 爆仓后余额→重启费用→prop_operating_EV | 1 分钟 OHLC 下触发价不可观测；取更保守近似 |
| IR-2 (=R4) | max_favourable 极值口径 | S0 §10.1 | 仅描述性输出；不进判决统计量 | 与 adverse/Y4 对称 |
| IR-3 | Lucid payout "50% of profit" 基数 = 账户模拟盈利（balance−50000，gross 扣减后） | platform_params payouts.max_request | payout 金额与时点→EV | 与 scaling 基数一致；官方表措辞支持 |
| IR-4 | sizing anchor 含 $1.74 平台费 | MC §3 / S0 §8 | n 取整→EV（保守：anchor 大→n 小） | "incl cost" 的包含式读法 |
| IR-5 | Topstep credit 到期 age≥365 失效 | reset_policy.expires_after_days | 费用（保守：早失效→多付费） | 官方未定边界；防虚假 GO |
| IR-6 | 申请日损益不入任何 cycle；pass 撞 rebill 日仍计 $49 | payout_paths / subscription | 资格时点与费用（保守） | 官方只定义"不入下轮"；日粒度保守处理 |
| IR-7 | 场景 adverse slip 默认 = 该场景 per-side slip | S0 §6 | stop 成交价 | 暂用值；成本模型锁定前必须定稿（已有硬关卡） |
| IR-8 | Lucid 处理期 halt = 请求日＋后 2 个模板交易日 | MC §4.2 / payouts.processing "2 个工作日" | 交易日数→EV（保守：少交易） | 工作日≈模板交易日的近似 |
| IR-9 | Topstep API $29 计费自生命周期起（含 Combine 期） | billing_calendars topstep_api "from_activation" | 费用（保守：多计 1-3 期） | 自动化自 Combine 起即需 API |
| IR-10 | B2F 不消耗 6 次评估计数 | MC §4.3 failure_policy | 重启预算→EV | 冻结文本将 b2f 与 new_combine 列为不同 action；B2F 非 evaluation start |
| IR-11 | Y3 公式 = F9 在 [10:00,15:45) 类比；Y4/Y5 极值＋原始带符号 | S0 §5 | 仅描述性标签 | 唯一自然类比；见 ADJUDICATIONS 确认段 |

处置：以上全部为保守方向或仅描述性。批复方式：Aaron 逐条 accept/modify；
modify 项按两阶段流程形成正式 Addendum 并更新实现与测试。

## 批复定案（APPROVED_BY_AARON 2026-07-28，详见 IR_APPROVAL_PACKET.md）

- **A 类（纯实现解释）**：IR-2（diagnostic_only 标记＋静态测试）、IR-11。
- **diagnostic_only 附加条款**：IR-1（清算值不进任何判决输入；不变性测试固化——
  改变诊断清算值不得移动 prop_operating_EV 与 verdict）。
- **正式 Implementation Resolution Addendum（B 类）**：IR-1、IR-3、IR-4、IR-5、
  IR-6、IR-7（成本锁定硬条件维持）、IR-8、IR-9——冻结 tag 未动、历史未重写；
  影响 EV 的项在最终报告按方向披露（全部保守向）。
- **IR-10 = separate counters**：Primary 行为定案（B2F 不耗全局 6 次计数、每 XFA ≤2）；
  保守 sensitivity `b2f_consumes_attempt=True` 已实现并被机器强制限定为
  sensitivity-only（orchestrator 对 primary+consume 组合直接抛错）。
- 编号勘误：Aaron 批复第 3 条原文 "IR-4"，描述对应 IR-2；已按合理读法归位并明示。
本文件自此为已批复状态；后续新增 IR 以新条目追加。

---

## M4 批次（APPROVED_BY_AARON 2026-07-29，经 ChatGPT 评审；对应 DECISION_PACKETS_M4.md 与 SYMBOLOGY_DECISION_PACKET.md）

| ID | 内容 | 冻结章节 | 可能影响的输出 | 批复定案 |
|---|---|---|---|---|
| IR-12 (=D1) | 同日多事件：冻结 F10 单类别记 **NA**；当日不整日删除，仍进 Oracle 总体统计；multi-hot bool 与完整 event_types 保留在 **diagnostic sidecar**（不进 Primary/Oracle/成本/Checkpoint 判决）；报告全部多事件日（当前 19 天）；**禁止**发明 FOMC>NFP>CPI 等主观优先级；不得见标签/收益后改映射 | S0 行 62 / 行 45 NA 政策 | F10 特征 NA 计数＋sidecar | Aaron 新增 Option C（非原 A/B） |
| IR-13 (=D2+D2a) | F10=FOMC 只标**官方预定的 statement 发布日**（例会第二日，92 天）；两日会议第一天不标；非预定紧急行动（2019-10-11、2020-03-03/15/23）记 `unscheduled_fomc_action`，**仅 diagnostic**，不进冻结 F10；不得使用 10:00 时不可知的事后信息；(cancelled) 2020-03-17/18 不入表（未召开，事实判断） | S0 行 62 | FOMC 事件日集合＝92 | Option A＋限制 |
| IR-14 (=D3) | CPI/NFP 延期按**实际官方发布日**标注（as-released：2013-10-22 NFP、2013-10-30 CPI）；原定日期/延期公告/实际日期三者留在 source log；实际日期时间必须官方证据，不得第三方回填 | 无冻结解→本 IR 补 | 个别日期归类 | Option A |
| IR-15 (=D6 修订) | 路径特征口径：**先**应用冻结整日剔除（半日市/RTH 无成交/缺失>10%——vendor-degraded 超限日先排除，不计入保留数）；过资格日内部缺分钟按**时间排序实际存在 close 序列**差分；不造合成 bar、不 forward fill、不插值、不以邻 bar 替代精确锚点；精确锚点缺失→对应特征/标签记 NA，整日不删；opening path 与 PM path 受影响日分别报告 | S0 行 96 / 行 44-45 | F3/F8/path 类 NA 计数 | 修订版 Option A |
| IR-16 (=D5) | symbology Option A：main agent 亲自执行一次官方 `symbology.resolve`（USD 0.00 元数据端点；临时 key 仅经环境变量，禁入代码/日志/commit/报告；归档请求参数＋原始 JSON＋UTC 时间＋SHA-256；取 2010-06-06→2022-01-01(excl) NQ.v.0→instrument_id→raw_symbol；47 次 transition 逐一验证＋无同 RTH 内切换；任一不符 STOP 出新决策包；mapping 仅验证与披露，不得改 Primary；完成后撤销 key；Option B 仅在官方端点无法完整返回历史映射时经 Aaron 批准后回退） | S0 行 30-32 | F11/F5 roll 识别的独立官方确认 | Option A；**执行状态：2026-07-29 首跑 401（环境变量为已撤销旧 key，撤销纪律有效）；等待 Aaron 注入新临时 key 后重跑，验证结果将追加于 gate1/symbology/** |

- D4/D7 维持条件触发（SA-1 已另出 D4a：FOMC 2010-2015 发布时刻无官方记载，
  45 行哨兵值 NOT_ATTESTED_IN_OFFICIAL_SOURCE——待 Aaron/ChatGPT 批复，
  不阻塞事件日期本身）。
- SA-2 硬边界 commit a6bd012 经 Aaron 原则批准（Development [2010-06-06,
  2022-01-01)、IV fail-closed、整文件拒绝、边界不可参数化）。
