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
| IR-16 (=D5) | symbology Option A：main agent 亲自执行一次官方 `symbology.resolve`（USD 0.00 元数据端点；临时 key 仅经环境变量，禁入代码/日志/commit/报告；归档请求参数＋原始 JSON＋UTC 时间＋SHA-256；取 2010-06-06→2022-01-01(excl) NQ.v.0→instrument_id→raw_symbol；47 次 transition 逐一验证＋无同 RTH 内切换；任一不符 STOP 出新决策包；mapping 仅验证与披露，不得改 Primary；完成后撤销 key；Option B 仅在官方端点无法完整返回历史映射时经 Aaron 批准后回退） | S0 行 30-32 | F11/F5 roll 识别的独立官方确认 | Option A；**执行完成（2026-07-29）**：首跑 401 记录为 AUTH_FAILED_NOT_RESOLVED（Aaron 勘误：401 仅证明未获授权，不能唯一归因）；新 key 注入后两跳执行成功（API 事实：GLBX.MDP3 上 continuous→raw_symbol 不受支持=HTTP 422，改为受支持的 continuous→instrument_id→raw_symbol 两跳，批复语义不变）；48 区间、47/47 transition 全符、同 RTH 切换数 0、季月链 NQM0→NQZ1 无断点；发现并正确处理 CME instrument_id 跨年复用（id 10016 曾载 22 个产品→时间感知联接）；证据归档 gate1/symbology/（原始 JSON×2＋SHA-256＋验证报告＋mapping csv）；密钥模式扫描零命中 |

| IR-17 (=D4a) | FOMC 2010-2015 共 45 行官方存档无精确发布时刻：日期继续用官方证据；`official_release_time_et` 记 NA（空）；新增列 `release_time_status = official_time_unavailable_in_archived_source`；**禁止**以 00:00/12:30/14:00/14:15 或任何"典型时间"替代；禁止新闻/第三方日历/历史惯例回填；日期级 F10 仍编码为 FOMC；时间级诊断不得使用这些行（除非显式标记未知）；不因时间未知而整日删除或 F10 变 NA；每行保留官方 source ID＋hash。其余行的 status 取值（main agent 机械补全，纯披露）：`official_time_recorded`（有官方时刻）/`not_applicable_no_statement`（无声明的 FOMC 条目行）。**Primary effect = none；sample effect = none；diagnostic time coverage reduced**。已实施：f10_extraction.py＋csv 重生成（sha256 5e92ad00…bb5e8c，468 行 9 列）＋专项测试（205 全绿） | 任务书证据条款 | 仅诊断时刻覆盖 | APPROVED_BY_AARON 2026-07-29 |

- D4/D7 维持条件触发（D4a 已批并落档为 IR-17，见上）。

### Preflight 批次（APPROVED_BY_AARON 2026-07-29，经 ChatGPT 评审；对应三个 DECISION_PACKET_PREFLIGHT_*）

| ID | 内容 | 冻结章节 | 可能影响的输出 | 批复定案 |
|---|---|---|---|---|
| IR-18 (=F10 多事件作用域) | 先应用 IR-13 事件资格过滤 → 映射冻结 F10 类别 → 再判多类别冲突。**Primary F10 多事件 NA = 9 天**；原表 19 个多事件日完整保留 diagnostic sidecar（raw_multi_event_sidecar_days=19）；被 IR-13 排除 FOMC 身份的 10 天按剩余唯一类别编码 CPI/NFP；禁止发明优先级。**IR-12 表述修订**：其"当前 19 天"指 raw diagnostic multi-event count，非最终 Primary 冲突集（后者=9） | 行 62 / IR-12×IR-13 | F10 NA 集合 | Option A |
| IR-19 (=D7 前日 RTH 收盘) | 前日 = 紧邻上一个**实际 CME RTH session**，不依赖资格漏斗；常规日锚点=15:59 bar close；scheduled early-close 日=最后一根官方排期 RTH bar close（是锚点本身非替代）＋sidecar `prev_close_from_early_close_day=true`；**禁止**泛化为"最后一根存在 bar"；排期收盘 bar 本身缺失→NA；vendor-degraded 前日（2 天）→NA；样本首日→NA；禁止跳过不合格前日向前找 eligible day；禁止 forward fill/插值/邻 bar 替代 | 行 57 / 行 41-45 | F5 覆盖（NA 由重跑机械生成，不手写） | 修订版 Option B |
| IR-20 (=F4 参照集) | 参照集 = 严格早于当日的最近 60 个**实际 CME RTH 交易日**，每个参照日须有完整 30 根 09:30-09:59 bar；**含** scheduled early-close 日、早盘完整的下午缺口日、ADR14 warm-up 日；**不要求**整体 S0 资格或 ADR14 资格；**排除** zero-bar 日与早盘窗口不完整日 | 行 56 / 行 44-45 | F4 覆盖 | Option A（精确化） |

| IR-21 (=Y6 装桶) | **修订版 Option A（APPROVED_BY_AARON 2026-07-31）**：按 calendar year 独立；排名总体=该年 Y_cont 非 NA 的 Development 日（L82 零方向/方向不可判/ADR warm-up 等一律 Y6=NA 且**继承** y_cont 底层 NA 原因，不造新原因）；ascending（decile 1=最低）；**ties 用 average rank，相同 Y_cont 必得相同 Y6，禁止日期/行序/index/rank(method="first") 拆并列**；percentile_rank=(average_rank−1)/(n_year−1)；decile=clip(1+floor(10·pr),1,10)；并列致箱不均或空箱允许并如实披露；机械边界：n_year=1 时按公式极限 pr=0→decile 1（披露）；**use_restriction 机器保证**：仅描述性，不进 feature/Oracle/Primary/样本资格/成本/候选筛选/trial 选择；convention 运行时参数整体移除（唯一规则，无可选项） | 行 91 / 行 45 | 仅描述性标签 | 修订版 Option A；8 项专项测试（跨年独立/min1 max10/ties 同箱/行序不变/NA 传播继承/不完整年/Oracle 路径隔离/无 tie-break 源扫描） |

### SA-6 方法决策批次（APPROVED_BY_AARON 2026-08-01）

| ID | 内容 | 冻结章节 | 批复定案 |
|---|---|---|---|
| IR-22 (=F4 非有限 volume) | 任一必需 09:30-09:59 volume 为 NaN/非有限 → classification=**INPUT_DATA_DEFECT**，**Stage B 立即 STOP**（非可继续运行的日级 NA）；当日不入 F4 参照集；不得继续产出该 trial 任何研究结果；**禁 np.nansum**——先断言窗口全 finite 再普通 sum；context.py 与 s0_input_preflight.py 同步修复同测试。当前 A1 零 NaN → 现有结构数字不变 | 行 56/45 | 修正语义版 Option A |
| IR-23 (=Y1/Y2/Y3 独立计算) | **删除**任何 "d_open==0 → 整行标签 NA" 早退；每标签只按自身必要输入判可算：Y1{O1000,C1544,ADR14}、Y2{O1000,C1544,PM close path}、Y3{C1544,PM high,PM low}；Y1/Y2/Y3 **不得**因 zero_direction/undeterminable 本身 NA；warm-up 日 Y1 NA 但 Y2/Y3 可算；Y_cont/Y4/Y5 继续依赖方向；Y6 继续依赖 Y_cont；覆盖数字重跑机械生成不得手写。labels.py **限定语义解锁**（仅此改动，非任意重构） | 行 86-91/45 | Option A＋逐标签独立 |
| IR-24 (=L82 判定) | **Option B（冻结字面）**：仅当 ret_open30 **可计算且 exactly zero** 才属 L82（需 O0930/C0959/ADR14 全可用且 finite）；ADR 缺失/非有限/为零或锚点缺失 → **不属 L82**，归 direction_undeterminable_na 等批准原因；新增 diagnostic `opening_numerator_zero_ret_open30_undefined`（分子为 0 但标准化回报不可定义的计数披露）；当前输入两口径零差异，但**此后不得用锚点相等替代 ret_open30 定义**（main agent 原推荐 A 被否——不得以"价格事实"新政策覆盖冻结字面） | 行 82 | Option B |

**Y6 文字勘误（同批）**：n_year=1 → decile=1 是 **explicit singleton-year
convention**，不得称"公式极限"（0/0 无唯一极限）。

**IR-16 reconciliation（SA-6 F-32，Aaron 2026-08-02 批准关闭）**：冻结
L30-32 以 symbology 映射**定义** F11/is_roll_transition；IR-16 的"仅验证
与披露"限定的是**具体合约代码（raw_symbol）身份**——roll 识别本身来自
instrument_id 变化（数据内在事实），官方映射用于独立验证该识别并披露
合约身份，绝不反向修改 F5/F11 的 Primary 语义。两者不矛盾：映射 csv 在
LOCKED 输入中是因为它是**验证输入**，不是特征取值来源。

**报告治理修正（同批 Aaron 批复）**：(1) F10 必须双报 raw category membership counts 与
final mutually-exclusive F10 counts，并断言 CPI+NFP+FOMC+none+NA_multi_event == 结构合格日数；
(2) commit 元数据统一为 input_commit / subagent_integration_commit / post_integration_fix_commit /
report_rendered_from_head 四字段（报告与 JSON 同源，禁自引用最终 commit）；
(3) 里程碑提交一律以机器退出码为硬闸（pytest/seal 红则 commit 物理不可达）——
ae9b19c 红测试提交事故如实留档于 M4_FINAL_CLOSURE_REPORT。
- SA-2 硬边界 commit a6bd012 经 Aaron 原则批准（Development [2010-06-06,
  2022-01-01)、IV fail-closed、整文件拒绝、边界不可参数化）。

### IR-25 运行可满足性修复（APPROVED_BY_AARON 2026-08-01，DECISION_PACKET_RUNTIME_SELFBLOCK）

背景：第一次真实 S0 尝试（attempts/S0-T001-A20260801T121730Z，incident
INC-e6fe49ec63de）在 Stage-A `full_pytest` 门失败。根因＝结构性自锁：
`test_live_registry_today_has_no_authorization_event` 钉死真实 registry
的未授权态，而 Stage-A 在授权态运行全套件 → 授权后必红（508/1）。
连带锁死：解析器拒绝 >1 行 RUN_AUTHORIZED，行 6 append-only 永存 →
不改解析器无法二次授权。exposure 未消耗，S0-T001 完好。

| 项 | 批复定案 |
|---|---|
| P1（自锁测试） | **Option B（状态无关化）**：删除"真实 registry 必无 RUN_AUTHORIZED"断言；改为——真实 registry 必须可完整解析；未被 supersede 的合法 RUN_AUTHORIZED ≤1；若存在必须严格满足 §10 完整语句＋trial_id＋40 位 commit；**pytest 通过与否不得依赖真实 registry 当前是未授权态还是授权态** |
| P2（授权作废机制） | **Option A**：新事件类型 `RUN_AUTHORIZATION_SUPERSEDED`，note 必含 trial_id、supersedes_event_sequence、superseded_commit、reason_code、incident_id 五字段（机器可解析，缺一即整链 fail-closed）。**有效授权集合 = 全部格式合法 RUN_AUTHORIZED − 被格式合法 supersede 精确引用者**；存活数 0=未授权、1=继续验证 commit==HEAD、>1=fail-closed |
| 解析器细则 | 格式非法的 RUN_AUTHORIZED 行**永不静默忽略**（整链 fail-closed）；RUN_AUTHORIZED 行 commit 单元格必须与语句 commit 完全相等（fixture 7）；围栏代码块内的行是文档非事件（fixture 4）；supersede 引用不存在/前向引用/重复引用/trial 或 commit 不一致 → 一律 fail-closed（fixtures 10-13） |
| 十三项夹具测试 | 无授权／一条合法／散文提及／围栏引用／错 trial／短 hash／cell-语句不一致／两条存活／合法 supersede 后归零（＋9b：旧废新立授权新 commit）／引用不存在／前向引用／重复 supersede／引用不一致——全部生产解析器直测 |
| 双状态可满足性（§四） | 全套 pytest 在布局 A（零存活授权）与布局 B（恰一条存活、commit==该布局 HEAD）均须通过；授权态测试必须走生产解析器与生产同构 registry 字节，禁 mock 直返成功。套件内唯一读真实 registry 的测试已状态无关化（grep 证据），布局 B 由生产字节＋追加合法行的 fixture 直测（含 RealChain.authorization_snapshot 全链） |
| 本次失败处置（§三） | 行 6（RUN_AUTHORIZED @524c9ab）、"+"失败事件行、attempts/ 全部工件、incident 一律保留不改；追加行 7 `RUN_AUTHORIZATION_SUPERSEDED` 精确引用行 6（reason_code=RUNTIME_SELFBLOCK_FIX, incident_id=INC-e6fe49ec63de）；全部随修复 commit 入库 |
| 收口序（§五） | IR 落档 → 修复 → 全量电池（含冻结 hash/扫描/Stage-A 合成测试）→ 新修复 commit → Opus 只读审计（重点=运行可满足性）→ 全 CLOSED 后追加新 READY_FOR_RUN_AUTHORIZATION → **停等 Aaron 对新 HEAD 重发 §10**。不得自动再授权或运行；S0-T001 未消耗，仍为首次真实 trial |

**IR-25 勘误（SA-14 审计，2026-08-01）**：§四行中"套件内唯一读真实
registry 的测试已状态无关化"陈述**不实**——实际有两个测试读真实
registry（结构测试＋双状态测试），且双状态测试本身在授权态构成第二个
自锁（对真实字节直接追加探针授权行→2 行存活→fail-closed→套件红，
与 INC-e6fe49ec63de 同门同样式）。SA-14 已在隔离副本端到端验证修复
（布局 B 先 supersede 存活集再追加探针行）：双布局 519 全绿、模拟
13 门 Stage A 全过（COMPLETE 13/13）。修复仅动测试文件，收集数不变。
SA-14 另留三条非阻塞观察（>40-hex 截断接受、supersede note 多字段组
仅取首、非数字 seq 的 RUN_AUTHORIZED 行将永久不可 supersede）——
记入 P3 backlog，不在授权前扩测试面。
