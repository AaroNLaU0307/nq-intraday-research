# DECISION_PACKET_RUNTIME_SELFBLOCK

状态：PENDING_AARON（阻塞第一次真实 S0 的再尝试）
提出：main agent，2026-08-01，第一次真实 S0 尝试失败后
事件：attempts/S0-T001-A20260801T121730Z（incident INC-e6fe49ec63de）

## 0. 事实（Level 1-2，全部可机器复现）

1. Aaron 于 2026-08-01 发出逐字 §10 授权语句（commit
   `524c9ab94eea8cbf2e906f3016f63cffde86e2c5`）。RUN_AUTHORIZED 事件
   （registry 行 6）按流程追加，未建 commit。
2. 零参数入口启动。Stage A 前序门全过（含 git_clean——registry 白名单
   豁免如设计生效），至 `full_pytest` 门：pytest exit=1 → RunGateError →
   PRE_RUN_ATTEMPT_FAILURE 落册。**exposure 未消耗，S0-T001 完好**。
3. 复现：授权态下全套件 **1 failed / 508 passed**。唯一红测试：
   `tests/test_s0_runner.py::test_live_registry_today_has_no_authorization_event`
   （:506）——读取**真实** ops/TRIAL_REGISTRY.md 并断言
   `find_authorization_event` 返回空（docstring：“The real trial registry
   at this commit must NOT authorize a run.”）。
4. 全套件仅此一处读真实 registry（grep 证据：其余命中全为 tmp_path 合成
   fixture 与 git_clean 白名单测试）。

## 1. 根因：结构性自锁（不是普通测试缺陷）

两条各自正确的不变量在授权态相交为矛盾：

- 该测试钉死「本 commit 的真实 registry 无 RUN_AUTHORIZED 行」；
- Stage-A `run_authorized_event` 门要求「真实 registry **有**且仅有一行
  RUN_AUTHORIZED 且与 HEAD 一致」；
- Stage-A `full_pytest` 门在授权态运行全套件。

⇒ 授权语句一旦落册，`full_pytest` 必红，Stage A 必失败：**runner 在授权态
按构造不可运行**。SA-6..SA-13 全部七轮审计都在未授权态执行套件（509 全绿），
从未在授权态跑过一次——这正是第一次真实 Stage-A 执行才暴露的盲区，
与 SA-6 F-01（授权门可满足性）同类但方向相反：**运行可满足性**。

## 2. 连带锁死点（必须一并裁决，否则修完测试仍无法再授权）

`find_authorization_event` 对 >1 行 RUN_AUTHORIZED 一律拒绝
（`s0_real_run.py:190-192`，"exactly one is expected"）。行 6
（@524c9ab）已按 append-only 永不修改；修复测试必然产生新 commit X，
新授权需追加第二行 RUN_AUTHORIZED（@X）→ 解析器数到 2 行 → 拒绝。
**不改解析器则永远无法二次授权**——与 MR 仓库 D2-h1「被拒权威留下
持久声明楔死后续运行」同构。registry 规则本身已预设出路：
「勘误以新事件追加并引用被勘误事件」，缺的只是解析器对勘误事件的理解。

## 3. 选项

### P1（自锁测试）

- **A：删除该测试。** 解析器行为已由相邻合成 fixture 测试全覆盖
  （:497-503 空表拒绝、:515+ 精确语句接受、13 变体拒绝矩阵）；registry
  的状态治理本就属于 Stage-A 门与状态机，不属于 commit 属性。
- **B（推荐）：改为状态无关的结构有效性断言。** 真实 registry 必须
  可解析、RUN_AUTHORIZED 行数 ≤1（P2 落地后：存活行数 ≤1）、若存在则
  必须逐字含 §10 语句＋完整 40-hex。未授权态与授权态都通过，且仍能
  抓住「散文误匹配」「多行」「残缺语句」三类原始威胁。
- C：从 full_pytest 门排除该测试。**否决理由**：选择性 deselect 正是
  该门要防的静默禁音（SA-10 已验证 collected 地板语义）。

### P2（授权勘误机制）

- **A（推荐）：解析器承认 RUN_AUTHORIZATION_SUPERSEDED 事件。** 新事件行
  `RUN_AUTHORIZATION_SUPERSEDED`，note 必须引用被作废行号与其 commit；
  `find_authorization_event` 改为：候选 = 未被任何 supersede 行引用的
  RUN_AUTHORIZED 行；存活行仍要求恰好 1，语句校验不变。Stage-A
  `run_authorized_event` 门自动继承。新增测试：两行其一被 supersede→
  存活行通过；两行存活→仍拒绝；supersede 引用不存在的行→拒绝。
- B：不改解析器，把行 6 视为可覆盖。**否决理由**：违反 append-only
  永不修改；且丢失「授权曾发出、尝试曾失败」的治理事实。

### P3（顺带，不单独成项）

- 行 6＋PRE_RUN_ATTEMPT_FAILURE 行＋attempts/ 工件＋本决策包随修复
  commit 一并入库（失败尝试永久留档，registry 规则第 5 条）。
- MIN_COLLECTED_TESTS 按修复后精确计数重钉（P1-B 净零，P2-A 新增
  若干，以实测为准）。
- packet §0 入口哈希随 P2-A 重渲染（runner.py 不动）。

## 4. 推荐执行链（Aaron 批复后）

P1-B＋P2-A 实施（main agent，入口与测试均主代理专属面）→ 电池全绿
（含授权态回归：临时 fixture 模拟行 6+行 7 的 supersede 布局）→
新候选 commit X → 聚焦只读审计（范围=两处改动＋授权态全套件必须
509±N 全绿）→ ALL_CLOSED → registry 追加
RUN_AUTHORIZATION_SUPERSEDED（引用行 6，理由=自锁缺陷修复，commit X）
→ Aaron 新 §10 语句（commit X）→ 二次尝试。

## 5. 明确不做的事（除非 Aaron 另令）

- 不动行 6、不动失败事件行、不动 attempts/ 工件；
- 不在裁决前改任何 tracked 文件；
- 不将本次失败归因于数据或计算层——Stage C 从未进入，冻结方法区
  字节未动。
