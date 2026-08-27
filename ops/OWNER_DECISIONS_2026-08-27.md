# Aaron 的裁定 —— 2026-08-27，DEFERRED_AFTER_MIGRATION §4 的八项

```ini
RECORD_TYPE=OWNER_DECISION_RECORD
REVIEW_ID=owner-decisions-2026-08-27
DELIVERY_STATUS=RETURNED
STATUS=IN_FORCE
DECIDED_BY=Aaron，2026-08-27
```

---

## 0. 授权文本与其精确范围

Aaron 的原话，逐字：

> 就按你推荐的全做就是了

**它授权的是 builder 在同一轮对话中逐条列出的推荐**，即下方 ④⑦⑧⑨⑩⑪ 六项。

**它没有授权 ①②③。** 理由记录在此，以免后来的读者把「全做」读成「全都批了」：

```
builder 在提出推荐时明确写道：①②③ 三条 builder 不接，
并请 Aaron「在 ①② 之间挑一个动作告诉我（或者说『先都不动』），其余按推荐执行」。
Aaron 未挑任何一条。因此 ①②③ 维持未授权。
```

**若要授权迁移，需要一句指名它的话。** ND1 把目录创建与迁移执行拆成两条不得合并的
授权，正是为了让「概括性同意」不能生效 —— 一句「全做」若能连迁移一起批掉，
那条拆分就白拆了。

**八项授权字段维持全部 NO。**

---

## 1. 逐条裁定

### ④ 是否因更正件重开路线选择 —— **不重开**

```
理由   迁移理由是实测事实（Desktop → OneDrive\Desktop 的文件夹重定向），
       它不因「trial 从未被烧过」这条更正而失效。
       重开要再烧一个决裁席位，而换不来新信息。
后果   路线 A ＋ GIT_ONLY 维持。
证伪   若出现一条与「桌面即 OneDrive」相抵的实测，路线重议。
```

### ⑤ 是否接受 GIT_ONLY 的残留风险 —— **无需新裁定**

`dec-s5-r4-2026-08-27` 已裁 `RULING=GIT_ONLY`（CONFIDENCE=HIGH），
Aaron 2026-08-27 采纳该裁定时即已作答。**本记录不重复批准，只记明它已被答过。**

残留风险原样在册（决裁席自陈：旧树内回滚介质从两种收窄到一种），
回退项 NEW_REPO_ONLY 仍然有效，随时可由 Aaron 取用。

### ⑥ R3 与 R4 的 ratify —— **现在无事可做**

```
R3   Aaron 已于 2026-08-27 签署（ND1 profile R3 ratification block）
R4   迁移执行完成之后才起草 —— 见 DEFERRED_AFTER_MIGRATION.md §2
     在 R4 ratify 之前，冻结令「禁止追加任何 CR1 行」持续在 force
```

### ⑦ 三处「从未存在」的存在性事实 —— **不在正确前提上重裁**

```
理由   决裁席当时是盲席、拿不到那些引用行，只能按 builder 的错误分类推理。
       现在字节已经把答案给出来了（三条全是提案，逐条证据见
       CORRECTION_CLASS_B_WERE_PROPOSALS_2026-08-27.md）。
       重问只是再花一个席位去确认磁盘上已经写着的东西。
残留   STRATEGY_COUNCIL_ROUND4_LOCK 的落盘仍等 Aaron 手上的 sealed proposal 原文
       —— 但这条 2026-08-25 的溯源审计就已提出，不是新问题，也不是重裁能解决的。
```

### ⑧ 「先有字节再引用」条款是否升入 QROS / 全局文件 —— **暂不升**

```
理由   QROS 是 FROZEN v2.0.1，修改它是大动作；
       一个项目一周的经验不足以作为修改冻结教条的证据基础。
现状   项目内已 IN FORCE（ops/CITATION_DISCIPLINE.md）
重议触发   第二个项目独立撞上同一形态的缺陷时，重新提出
```

### ⑨ 是否重制 D124 新版摘录 —— **不做**

目前无人需要。裁定已定其处置：一个字节都不改，警示放进递送它的文书。
若将来确有需要，那是一次**新的签发决定**，不是编辑。

### ⑩ 决裁席位的记忆接触是否影响其未来 Stage I 资格 —— **不影响**

```
依据   席位接触到的是文件名与治理标识（恢复锚名、N08 DROP、N00 保留、
       MC-REG-COLLISION-001 待批），无任何一类 outcome 内容的值：
       revealed verdict · cumulative exposure count · endpoint spread value ·
       zero-direction cell count · addendum feasibility assertion
       按项目自己的准则「文件名不是内容」，不构成 outcome 暴露。

如实记录一句   这是宽松的一边，且判断依据是席位自己的申报。
               若日后发现申报不完整，本条随之作废。
```

### ⑪ 模型多样性连续五席全为 Fable 5 —— **知悉，并立一条路由规则**

```
事实   dec-four-owner · dec-scope-boundary · dec-registry-migration ·
       dec-s5-r4 · dec-citations —— 五连，全部 Fable 5
性质   真实的独立性弱点。缓解（Sol 在环内做跨家族制衡）是真的但不完整：
       Sol 是验证席，不是决裁席

规则（自本记录起）
  高风险决策   Sol 先做 pre-seal 挑战 -> Fable 裁 -> Aaron 裁定
               （即 QROS 的 Stage A2 形态）
  低风险决策   Fable 单席即可
  两者都要求   裁定文书里写明「这是第 N 连同家族席位」

明确不采用的做法   把 Sol 变成决裁席 —— 那会毁掉它的验证独立性，
                   代价大于它买到的家族多样性
```

---

## 2. 一项 builder 实测发现，不是决策而是事实

**S8 的备份合同有一个未满足的硬件前提。**

```
不变量 10 要求   另一物理卷上的 bare 仓，或离线 bundle
实测（2026-08-27）
    Get-CimInstance Win32_LogicalDisk -> 只有 C:（DriveType=3，本地固定盘）
    无第二块固定盘 · 无可移动卷 · 无网络盘
```

**因此 ③（S8 备份目标仓的目录创建授权）今天不是「批不批」的问题，是硬件不具备。**
本发现已写进迁移方案 §4 的 S8 步骤，免得执行时才撞上。

**这不阻断 S0–S7**：备份合同是迁移完成后的持续义务，不是迁移的前置条件。
但它意味着**迁移完成后会有一段没有异卷备份的时间**，直到有第二块盘为止 ——
这一点应当在授权迁移时被知悉。

---

## 3. 仍然未授权的

```
① 新仓目录创建授权          NO
② 迁移执行授权              NO
③ S8 备份目标仓创建授权      NO（且硬件前提未满足）
八项授权字段                 全部 NO
```
