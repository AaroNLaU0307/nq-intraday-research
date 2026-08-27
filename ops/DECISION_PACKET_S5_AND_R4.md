# 两件复审席退回来的 —— 决裁包

```ini
DELIVERY_STATUS=RETURNED
REVIEW_ID=dec-s5-r4-2026-08-27
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=决裁席（adversarial decision seat）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被裁字节的作者；dec-registry-migration-2026-08-27 的那个会话；
            迁移方案复审的那个 Sol 会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
DELEGATED=YES —— Aaron 2026-08-27「给我决策的部分一律让 fable 替我选择，我同意」
SUBAGENT_OR_WORKFLOW_BUDGET=0
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_S5_AND_R4.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 0. 处境：一份裁定里有缺陷，而 builder 不该自己绕过去

fresh Sol 复审迁移方案，判 **HOLD**，八条 finding。**builder 修了五条，两条退回。**

**退回的第一条，其缺陷在裁定里而不在方案里**：

```
dec-registry-migration-2026-08-27 不变量 4（修改条）原文：
  副本用改名形式（如 ops/TRIAL_REGISTRY.pre-migration.<date>.md）保留
```

**这个文件名必然命中故障模型边界 (2) 的非精确 `TRIAL_REGISTRY*` 拒绝模式**
——与 OneDrive 冲突副本不可区分。builder 实测：

```
fnmatch('TRIAL_REGISTRY.pre-migration.2026-08-27.md', 'TRIAL_REGISTRY*')  True
且不等于精确名 'TRIAL_REGISTRY.md'                                        True
```

复审席的 `STRONGEST_OBJECTION` 因此是：**方案的成功路径自身不可达**——S7 再扫时
必然 STOP；若临时豁免，又会未经设计地削弱冲突副本检测。

**builder 不自选一个新文件名。** 那是「实现者自行挑一种读法」，与第六轮 HOLD 的
Finding 1 同形，且这次要挑的是**已生效裁定的读法**。

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `228103a46c51dbbb1004572e6a07d2c45a3767fb4e547702f4fe6c905a281b8f` | `15514` | `ops/REGISTRY_MIGRATION_PLAN_ROUTE_A.md`（R2，含 §0 修订说明） |
| `8734c430534314e8c7592c998e43a0485b90c37b9b0fb9df5d5736200d979424` | `5448` | `ops/REGISTRY_SYNC_FAILURE_MODEL.md`（含边界 (2)） |
| `a62030d72113a3c16a8190449fc42f2623c38bdd254c8de6a40a697e1ff86538` | `7645` | `ops/RULING_FABLE_SCOPE_AND_MIGRATION_2026-08-27.md` |
| `eb8b6567d99760ee7438e8105e08f48a0584e0798175a9a236a6be5bf73b96b0` | `37109` | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md`（含已批准 CR1 语法块） |
| `fd3cd89ad03e60a5606730b5d3447a67ea04e36916afeb20033ea7e08e989771` | `5111` | `ops/CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md` |

任一条不匹配 ⇒ STOP。

---

## 2. 禁区 —— 本节必须随包

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不 grep、不 rglob、不广域符号搜索、不「顺手看一眼」。** 需要哪个路径就列出来，
由工作会话提供逐字节内容。

**为什么是禁令而不是提醒**：已烧掉的三个席位里，**第二个从未打开过那份隔离文件**
——一次广域符号搜索把片段带了出来；第三个只做了**一次单模式定向 grep**，同样触到了。

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
**读那个 json，把里面每一条路径当作关闭。** 尤其点名（以下全部为禁区）：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

**许可起点**：`ops/RECOVERY_ANCHOR.md`（outcome-clean，永不隔离）。

**两条暴露轴不得合并**：研究轴那份本身就在禁区名单上；席位轴
`ops/REVIEWER_EXPOSURE_LOG.md` outcome-clean，可读。

---

## 3. 第 1 件 · S5 的回滚副本要以什么形式存在

**约束（三条同时成立才算解）**：

```
C1  与迁移前 registry 逐字节相同（不变量 1、4）
C2  不得命中 ops/ 下 TRIAL_REGISTRY* 的非精确名（边界 (2)）
C3  不得被任何读者误当成 canonical registry
    —— 裁定改不变量 4 的理由正是「留在原路径的陈旧真 registry 是最危险的形态」
```

```
选项 RENAME_OUT —— 副本改名且移出 TRIAL_REGISTRY* 前缀
  例如 ops/migration-2026-08-27/registry-snapshot-pre-migration.md
  满足 C1C2C3。代价：ops/ 下多一棵一次性子树；且它仍是一份可读的真 registry
  字节，C3 靠命名与位置而非机制。

选项 GIT_ONLY —— 不留任何磁盘副本，回滚用旧仓 git 历史
  git checkout <O0> -- ops/TRIAL_REGISTRY.md
  满足 C1C2C3 且 C3 是机制性的（磁盘上根本没有第二份）。回滚不需新授权。
  代价：**与裁定不变量 4「逐字节副本保留」的字面相抵**——需要决裁席明说这是
  修订而不是解释。且它把回滚能力完全押在旧仓 git 历史上。

选项 NEW_REPO_ONLY —— 副本只放在新仓，旧仓只留墓碑
  满足 C1C2C3。代价：迁移失败时回滚要跨仓取字节；且新仓刚建、备份合同尚未就位。
```

**请裁三选一**，并回答：

1. **不变量 4 的「逐字节副本保留」是否被 git 历史满足**？旧仓的历史里本就有那份
   字节，且旧仓不得重写历史。若满足，GIT_ONLY 就不是与裁定相抵而是它的更强形式。
2. **墓碑本身现在可行**——builder 已按复审席 finding 5 在 `registry_boundary`
   加了具名标记 `REGISTRY_MOVED_NOT_A_REGISTRY`，墓碑被点名拒绝（变异证红）。
   **请判这个机制是否足以承担 C3**，还是副本的位置仍须承担一部分。
3. **边界 (2) 今天「代码已写、未接入」**（失败模型 §3 表）。S7 的扫描是手工步骤。
   **请判**：本次是否应顺带把它接入，还是接入属另一件事、不搭这次的车。

---

## 4. 第 2 件 · CR1 的「所指已移」要不要走 R4

**决裁席（`dec-registry-migration`）裁的是治理缓解**：

> Aaron 的批准文本必须显式指名新仓为 `COLD_RECOMPUTE` 的所指，使所指变更经过
> 他之手而非默认发生。

**并自陈这是它最弱的一处**：

> 这是**字面为真、所指已移**——`c251335f…` 批准时「git 历史」的默认所指显然是
> ITSF 仓，A 把所指换成了一个批准时不存在的仓。怀疑者可以正当地说：这种哈希稳定、
> 语义漂移的读法，恰恰应该走 R4 让 Aaron 重新签，而我为了省一次签字选了不签。
> ……若认为这不够、仍须 R4，我不反对。

**fresh Sol 复审判得更严**：

> 治理缓解不够，**必须走 §D.10.3 的 R4**。已封存 CR1 块没有 registry 仓身份；
> 仅凭外部批准文本把「git history」的所指从 ITSF 仓改成新仓，是**未绑定进
> canonical 字节的语义变更**。R4 应明确跨仓历史桥及新仓所指并重新绑定批准。

**builder 的立场（非裁定）**：**倾向复审席**。理由是本项目自己反复付过的代价——
「声称已机械化、实则从未有过」（§D.11.3 事件）与「批准语义靠 prose 而非字节承载」
是同一形态，而 R4 正是把语义重新绑进字节的那条既定路线。

**请裁**：治理缓解够，还是必须 R4。若 R4：

1. R4 是否只改 `COLD_RECOMPUTE` 一行，还是须一并处理 `PREIMAGE` 的路径绑定？
2. 复审席要求 R4「明确跨仓历史桥」——桥的形式由谁定，本裁定还是 R4 提案？
3. 「刚批准就修订」是否需要额外的门（前一份裁定给过一个备案答案：fresh Sol 先出具
   「修订未实质削弱原批准」的正面结论；R4 批准块须显式引用被作废的 `c251335f…`）？

---

## 5. builder 已修的五条，供你判是否修对了

```
finding 5  墓碑 ≠ 缺失 —— 具名标记点名拒绝；刻意不扩成「拒绝一切不可解析的」
           （截断归见证，混进来会把真事故藏在路径错误后面）        变异证红 2
finding 6  守卫扩到 scripts/；s0_real_run.py 两处构造具名登记计数   变异证红 1
finding 2  FENCE —— 见证防回退不防分叉；SHA0 在 S0 记录、S6 前重测、
           S7 核对改双向
S4 拓扑    采纳复审席给的 N1→O0 / O1(parent=O0)→N1，删掉自相矛盾的「回填/amend」
S8         从一句要求改成可执行合同（卷核证／仅快进／禁 force/delete／
           周期／fsck／恢复演练／目标仓的创建需另一条授权）
```

**其中 finding 2 那条 builder 认为最深**：见证证的是「不低于」，而 S3 之后的追加
使计数**变高**，超集判据照过——**它防回退，不防分叉**。这一点方案原版没有。

---

## 6. 常设禁令（对你同样在 force）

不读真实 Development 数据；不执行 supplement／MC／S0／strategy；不在
`C:\Users\Aaron\quant-data\` 下创建任何目录；不做写探针；不追加任何 registry／
exposure 事件；不写 `APPROVED`／`EFFECTIVE`／`RATIFIED` 值；**不代签 P2、不代拟
执行语句**；**不执行任何迁移**；不推送、不打标签、不 amend。

**READ_ONLY**：只裁不做，零文件修改。

---

## 7. 返回格式

```
ITEM=S5-AND-R4
DELEGATED=YES
TRANSPORT_PRECHECK=PASS|STOP

DEFECT_IN_YOUR_PREDECESSOR_ACKNOWLEDGED=<不变量 4 给的文件名撞边界 (2)，你是否确认>

ITEM=第 1 件 S5 回滚副本的形式
  RULING=RENAME_OUT|GIT_ONLY|NEW_REPO_ONLY
  三问逐条：git 历史算不算「逐字节副本」· 墓碑机制能否承担 C3 ·
           边界 (2) 要不要顺带接入
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE
ITEM=第 2 件 CR1 所指已移
  RULING=治理缓解足够|必须 R4
  若 R4：三问逐条
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE

BUILDER_REPAIRS_ASSESSED=<§5 五条，逐条 修对了|有问题>
STRONGEST_OBJECTION=<对你自己两条裁定中最弱的那条>
STILL_AARON_ONLY=<你认定不可代裁的>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本裁定不释放任何 gate，不授权任何迁移，不创建任何目录。**
