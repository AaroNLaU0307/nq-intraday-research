# 委托裁定记录 — N06 终态 ＋ N-D2/N-D3 批准（2026-08-24）

```
RECORD_TYPE=DELEGATED_RULING
DECIDED_BY=Codex GPT-5.6 Sol，fresh top-level session（第五个）
AUTHORITY=Aaron 2026-08-24 具名批次委托
DELEGATED=YES —— 这是委托裁定，不是 Aaron 本人的判断
EFFECT=生效（Sol 明示「立即生效」；Aaron 已确认收到）
TRANSCRIBED_BY=Opus 5 main agent（builder/architect seat）—— 转录，非背书
REVIEWED_HEAD=b2616b835918623cb0708ea2245c35f8891b5efe（与本地 HEAD 一致，已核）
```

> **provenance 一句话，务必随裁定传播**：本终态与这 32 项由 Sol 在 Aaron 的
> 具名委托下裁定生效。凡在 N17 或任何对外记录中引用，必须带 `DELEGATED=YES`，
> 不得写成 Aaron 本人的判断。

---

## 1. N06 终态

```
N06_FINAL=ACCEPTED_WITH_DISCLOSED_RESIDUAL
第五轮 N06 审查=不再进行
DAG 效力=就 §4/§13.5 而言，本终态取代「N06 PASS」并满足进入 N-D2 的依赖
不表示=F1/F2 已被消除
N09=在下述缓解机械落实并验证前继续封锁；本裁定不授权任何真实运行
```

### 1.1 N17 的 F1/F2 披露措辞（逐字，Sol 裁定）

> F1/F2（残留，Python exact-type capability bypass）：同一 Python 进程内的
> 调用者可用公开的 `__new__` 与 `object.__setattr__` 构造精确类型且彼此自洽的
> `PreparedMCInput`／`SupplementAuthority`，使 `verify_supplement_authority`
> 返回成功。因此，「authority 验证通过」只能证明这一对对象内部自洽，**不能
> 单独证明其描述了真实的 14 文件 bundle**。已测的完全伪造对象对中，伪造的
> `bundle_table_digest` 不在 sealed binding 键集内，也未进入任何封存字节；故
> 该已复现残留是**验证违规，不是已复现的封存字节违规**。但凡把验证成功进一步
> 当作真实 bundle 来源或完整性的证据，该推断均不成立。

### 1.2 N09 强制缓解（工程侧的硬前置，归 builder 实现）

在任何 N09 真实执行前：

1. 独立 precheck **直接从受治理路径读取真实 bundle 字节**，逐文件重算完整
   14 文件 SHA-256 表，与冻结 manifest／代码钉定 attestation 逐项匹配；
2. 该门的输入**必须是路径与实际字节**，不能是 `PreparedMCInput` /
   `SupplementAuthority` 的对象自报值；
3. 重算表及总摘要进入运行证据；任一不匹配必须在 `STARTED` 前拒绝；
4. **任何文档、门或审计不得把 `verify_supplement_authority=PASS` 单独作为
   真实 bundle provenance**；
5. 须有至少一个机械测试：**对象对自洽但磁盘 bundle 不匹配时拒绝**。

---

## 2. N-D2 ＋ N-D3：`RATIFIED_WITH_MODIFICATIONS`

基底 = Fable 提案 SHA256 `E9745EAD…11519380`。

```
RATIFIED_UNCHANGED   M1, M3–M15, D2, O1, O2, O4, G2–G7
RATIFIED_AS_MODIFIED M2, D1, O3, E1, E2, E3, G1, G8
```

### 2.1 八项修订（要点；措辞以 Sol 原文为准）

| 项 | 修订 |
|---|---|
| **M2** | 数值 **5.0 日/月不变**，定性改为「本轮从零设定的保守门槛」；不得再称由平台算术导出或零自由参数。O3/N17 必须点名 M2=5.0 属揭盲后设定。 |
| **D1** | 结论与谓词不变；**删除**「E2 组合本就不可 GO」整句。保留的充分理由仅为 `over_budget` 只进 consumer metric、不进 verdict 或 feasibility 门。 |
| **O3** | 采纳阈值修正并追加精确 provenance：M1/M3/M2=5.0 三者均为**从零设定**，由 Fable 提出、Sol 在 Aaron 具名委托下裁定生效，**是委托裁定不是 Aaron 本人判断**。 |
| **E1** | 结论不变；**删除**「比 5% 小 12 个数量级」。若量化只能写「1.7×10⁻¹² 相对 0.05 约低 **10.47** 个数量级」；`$25` 绝对容差在没有给定尺度时不得与相对误差比数量级。 |
| **E2＋E3** | 采纳聚合绊线。280 min 与 2 GB **按每次独立物理调用**判断；E3 基础档与 2B 档分别应用，不把两跑合计当单跑。N16 前冻结每个计划调用的校准预计 `T_i`，`T_budget=ΣT_i`；已完成/失败/retry 实耗为 `A`，未启动计划量为 `R`。每次调用后与下次调用前：`A+R > 2×T_budget` 或任一调用 >280 min 或峰值 RSS >2 GB → **立即 fail-closed、暂停、重开 E2**。 |
| **M12** | 确认 YES 值得。α 是异质边界兜底类，块长 21 是唯一冻结的时间依赖敏感性轴。代价约为主通道认知层 9 → 18 base-equivalent；由 E2/E3 绊线约束。**不构成运行授权。** |
| **G1** | **删除授权句中的 alpha/beta 结果哈希。** 固定文法改为：`启动第一次真实MC，授权run_id: MC-R001，使用commit: <40位小写hex>，分支政策: PRECOMPUTE_BOTH_BLIND_SEAL_AFTER_COMPLETION，smoke: SMOKE-001=PASS`。commit 绑定生成代码/schema/两分支预计算政策/smoke；**结果哈希只能由运行后事件绑定**。 |
| **G8** | READY 前 reviewed HEAD 必须含 α/β **生成代码、schema、validator、盲封/manifest 逻辑及 SMOKE-001 PASS 记录**；**不得**要求尚未运行时就存在结果 payload 或结果 SHA-256。实际 payload 由同一授权 commit 运行产生，依 G7 于 `MC_RUN_COMPLETED` 后、揭盲前分别追加 `MC_BRANCH_SEALED` 登记实际 hash 与 byte_length。 |

### 2.2 Sol 独立发现、我漏掉的一条

**G1/G8 与 M14/G7 存在不可同时满足的时序矛盾**：分支 payload 与其哈希**只能
在运行之后产生**，却被要求预先出现在 reviewed HEAD 与授权句里。这不是措辞
瑕疵，是**逻辑上无法执行**。

我做验收时逐条核了八条承重事实断言，却**没有检查这 32 项之间的时序可满足性**。
Fable 的附录一列了 17 条依赖，我按它给的清单核，没有自己找它没列的那条。

### 2.3 附录一 17 条依赖的处置

全部保留，两处变更：第 14 条——G1/G8 改为**预运行绑定代码/政策**，G7 在运行
完成后绑定实际分支哈希，**三者现可同时满足**；第 16 条——O3 清单同步加入 M2
定性与委托裁定 provenance。第 17 条不变：**§2.2 仍归 Aaron**，本会话不裁
addendum 效力，N17 在 Aaron 裁前不得称该义务完成。

---

## 3. Sol 自己复现的 vs 采信的（逐字保留其区分）

**自己复现**：八条承重断言全部直接核实（FREEZE_LOG 2026-07-28、S0 §9 块长
5/21、`consumer.py:1441`、`gate2_cost_guard`、`GridRepeatPolicy.max_doublings=2`、
`k_per_seed=200`、附录 A 两 region、θ 0.5/0.3）；定向治理测试 24 passed；
四轮攻击＋完全伪造对象对＋工件冻结守卫定向集 90 passed；独立算得 E1 比值
10.4685 个数量级、M12 约 18 base-equivalent。

**未复核的 builder 自陈**：完整 3980 套件全绿、全仓负搜索的绝对完备性。

**其 596 passed / 3 failed**：三项失败源于运行在 Python 3.12（`/` 与
`/quant-data/...` 被判为绝对路径），本仓测试钉 3.13 的相反语义。**本地已核**：
3.13.14 下 `isabs('/')=False`、`isabs('/quant-data/itsf-runs')=False`，版本钉在
`tests/test_mc_supplement_paths_battery.py:416`。诊断成立，与四轮 High 及
F1/F2 无关。**但它暴露了一个真残留，另案记录。**

---

## 4. 一个我造成的、代价明确的后果

Sol 在独立性声明里写：

> 两份必读钉定工件自身复述了聚合结果及与 feasibility 相关的结果分类；虽然
> 禁读源文件均未打开、这些信息也未用于理由，本会话仍须记
> `OUTCOME_EXPOSED=TARGET_METRIC`，**已不具备 outcome-blind 的未来 Stage I 资格**。

那两份工件是我写的。**我把复述 outcome 的内容放进了必读工件，因此烧掉了一个
Stage I 席位。** 这与 EXPOSURE_LEDGER 白名单泄漏同一类错误——我的交付文档
携带复述 outcome 的内容，而我在写的时候没把它当成暴露面。

代价具体：runtime 的 GRAD-* 需要一个真实 Stage I pilot，**这个 Sol 会话不能
再当**；任何读过这两份工件的后续 Sol 会话同样作废。

处置见 `ops/INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md`。

---

## 5. 本裁定未做的事（Sol 自陈，已核）

```
未授权真实运行  ／ 未追加 registry 或 exposure 事件
未创建治理目录  ／ 未处理 N00 五份 Round-4 文档
未修改仓库任何文件（工作树在其审查前后均 clean）
```

`OUTCOME_EXPOSED=TARGET_METRIC`（其自陈，见 §4）。
