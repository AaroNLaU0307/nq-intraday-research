# Aaron 手上仅剩的四件 —— 决裁包

```ini
DELIVERY_STATUS=RETURNED
REVIEW_ID=dec-four-owner-2026-08-27
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=决裁席（adversarial decision seat）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被裁字节的作者；执行授权签署人
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
DELEGATED=YES —— Aaron 2026-08-27「我手上的四件可以和 fable 商量提案，我会同意它推荐的方式去做」
SUBAGENT_OR_WORKFLOW_BUDGET=0
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_FOUR_OWNER_ITEMS.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 0. 处境：builder 侧的 DAG 已经见底

`ops/RECOVERY_ANCHOR.md` §4（outcome-clean）逐字：

> **执行段停在哪：** N09（MC-DS-S001 执行封存）需要 Aaron 的 P2 精确授权。
> N10 依赖 N09 的真实执行；N11 从未实现；N13 依赖 N11。**故 N12 之后不存在
> builder 可独立推进的 DAG 节点。**

**所以这四件不是待办清单，是唯一的通路。** 它们全部解决之前，这个项目不动。

**但第 4 件（P2）有一个 builder 已实测的排序约束，你必须先读 §4 再裁**，
否则你会推荐一个签了就作废的动作。

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `5f533347622156932fce5c35f11ffa2b089771eba0f2dd6157b7bb2f801a00ff` | `10185` | `ops/RULING_SOL_D3_HOLD_2026-08-26.md` |
| `a387aa5485512f84fcfcd9700201f9220c85cc7d01c9d8c6cb3d1b14e64dc2bc` | `5450` | `ops/P2_AUTHORIZATION_PREPARATION.md` |
| `de453448a8c007065850af2282f772edaa68c6a21e572f9bc767448f7c931fb7` | `15082` | `ops/N09_EXECUTION_PATH_DESIGN_R3.md` |
| `3964c7b8227542bd78c1b7706493dbf16cbf86c30b824a5560bfa505eb174adc` | `11830` | `ops/ND1_PROFILE_RATIFICATION.md` |

任一条不匹配 ⇒ STOP，不要自行判断差异是否无害。

---

## 2. 禁区 —— 本节必须随包

**Review Packet 没有承载禁区清单的字段。2026-08-26 就因为清单只写在提示词里、
而交付的是 packet，烧掉了第二个复审席位。**

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不 grep、不 rglob、不广域符号搜索、不「顺手看一眼」。** 需要哪个路径就列出来，
由工作会话提供逐字节内容。

**为什么是禁令而不是提醒**：已烧掉的三个席位里，**第二个从未打开过那份隔离文件**
——一次广域符号搜索把片段带了出来；第三个（决裁席）只做了**一次单模式定向 grep**，
同样触到了。

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
**读那个 json，把里面每一条路径当作关闭。** 尤其点名（以下全部为禁区）：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

它**既是 outcome-carrying，又是本项目的恢复锚**。

**许可起点**：`ops/RECOVERY_ANCHOR.md`（outcome-clean，永不隔离）。

**两条暴露轴不得合并**：研究轴那份**本身就在禁区名单上**；席位轴
`ops/REVIEWER_EXPOSURE_LOG.md` outcome-clean，可读。

---

## 3. 第 1 件 · P3 与失败事件的写者是谁

**这是 D-3 的核心，也是四件里唯一的真矛盾：两条都已批准的规则互相打架。**

```
已批准的 actor 表        A1／F1／F2 派给 main agent (mc_ds_runner)
全局边界 4               只有主代理写 registry
既有先例                 scripts/s0_real_run.py 在真实 S0 运行时自己追加了 RUN_STARTED
```

fresh Sol 对 D-3 的 HOLD 里给了一种读法（**它自己声明这只是一种解释，终裁归 Aaron**）：

> 运行器存活并捕获到的 A1/F1/F2 仍由运行器追加；硬崩溃后的检测／恢复由主代理负责，
> 并使用 Aaron 批准的独立恢复语义。

**请裁**：

1. 采不采纳上述窄读法。若不采纳，替代读法是什么。
2. 若采纳：**「运行器存活」这个条件由谁判定、用什么证据**？一个崩溃的进程无法自陈
   它崩溃了——这正是 CR1 存在的理由，但 CR1 的 actor 是 main agent。
3. 是否需要**独立的 executor provenance 字段**（D-3 的 `UNRESOLVED_FOR_AARON` 第 1 项
   问的就是「actor 是否同时表达实际执行者」）。

**builder 必须如实说明的**：这条裁完之前，`ops/N09_EXECUTION_PATH_DESIGN_R3.md` 的
`BUILD_SCOPE` 只能停在默认拒绝骨架——**执行路径的可建范围直接取决于本条**。

---

## 4. 第 2 件 · 目录创建授权的四要素 —— **先读这条的排序发现**

**Sol 在 N09 R2 的 HIGH #2 里点名**：R3 提案里那个「目录创建 token」的
**来源、actor、精确文本、commit/path 绑定、有效期**五项**全部未定义**。

实测事实（builder 已核）：

```
C:\Users\Aaron\quant-data\itsf-runs           存在
C:\Users\Aaron\quant-data\itsf-runs-archive   存在
两个根下的 supplements\ 子树                   都不存在
DIRECTORY_CREATION_AUTHORIZED=NO
§D.10.4: SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES
```

`supplement_subtree_absent` 是 A_PRECHECK 的 13 道门之一——**子树不存在时它拒绝，
且模块永不自己创建**。

**请裁**：这五个槽各自应当是什么形式。特别是：

1. **有效期**：绑 commit（随提交作废，与执行语句同形）还是绑事件（用掉即失效）？
2. **actor**：只有 Aaron，还是可委托给 main agent 在他授权后执行？
3. **精确文本**：需不需要像执行语句那样逐字入 registry 行？若需要，落在哪个事件上
   （现行词表里没有「目录创建」事件）？

---

## 5. 第 3 件 · D-3 的五项 `UNRESOLVED_FOR_AARON`

原文逐字（`ops/RULING_SOL_D3_HOLD_2026-08-26.md`）：

```
1. actor 是否同时表达实际执行者；若否，是否增加独立 executor provenance。
2. 保留 A1／F1／F2 的 runner actor，还是修订已批准 profile、planner 与生产先例。
3. P3 后硬崩溃应产生什么事件、由谁追加，以及恢复写入的授权条件。
4. registry 是否允许继续在主动同步的 OneDrive 树中作为 canonical 写入面。
5. 租约回收能否自动执行，还是必须 fail-closed 等待人工裁定。
```

**第 3 项现在有一半答案了**：R3 已批准，CR1（`SUPPLEMENT_RUN_CRASH_RESOLVED`）
已转录进生产代码——**「产生什么事件」已定，剩下的是「由谁追加」与「授权条件」**。

**第 4 项是这五项里最重的**：registry 目前就在 OneDrive 同步树里，而本项目
**存在一个真实缺陷（L-5，2026-08-10 裁定），其机制会让同步残渣撞上 exact-set 磁盘不变量并烧掉一次 trial —— 该机制尚未发生**（那正是 qros-runtime
第二维护窗存在的原因）。

**请逐项裁，并明说哪一项你认为不可代裁。**

---

## 6. 第 4 件 · N09 的 P2 —— **builder 的实测发现改变了这一项的性质**

Aaron 说「你找到后发给我，我会同意」。builder 找到了，**并发现今天签了也生效不了**。
完整记录在 `ops/P2_AUTHORIZATION_PREPARATION.md`（在送审集内）。摘要：

```
P2 必填四字段    supplement_id · authorized_commit_40hex · output_root ·
                 verbatim_authorization_sentence
P2 的前驱        P1 | P2S | T1
registry 现状    grep -c "MC-DS-S001" ops/TRIAL_REGISTRY.md  ->  0
```

**P2 今天追加不进去——它没有前驱可挂。** 需要先有 P1（`SUPPLEMENT_PROPOSED`，
actor = main agent），而追加 P1 需要 `REGISTRY_EVENT_APPEND_AUTHORIZED`（现为 `NO`）。

**更要紧的是已批准 profile 的这两行**：

```
EXECUTION_SENTENCE_ONE_RUN_ONLY=YES
EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE=YES
```

**一句话只管一次运行，且 commit 一动就作废。** 现在签一句绑定某 commit 的授权，
之后任何一次提交都会把它烧掉。

**请裁**：

1. P2 是否应当**排在最后**（builder 的建议顺序见 `P2_AUTHORIZATION_PREPARATION.md`
   §3）。若不是，正确顺序是什么。
2. **P1 由谁追加、在什么授权下追加**——它的 actor 是 main agent，但
   `REGISTRY_EVENT_APPEND_AUTHORIZED=NO` 且 D-3 条件 3 禁止生产代码获得 registry
   写能力。这两者之间有没有一条合法路径（例如主代理手工追加而非生产代码追加）？
3. 若上述路径存在，它与第 1 件的裁定是否**必须一致**（同一个「谁写 registry」问题
   的两个实例）。

**你不得代签 P2，也不得代拟 `verbatim_authorization_sentence`。** §D.10.4 要求
Aaron 本人的精确语句；由任何非 Aaron 的席位拟出，它就不再是那条规则要的东西。

---

## 7. 常设禁令（对你同样在 force）

不读真实 Development 数据；不执行 supplement／MC／S0／strategy；不在
`C:\Users\Aaron\quant-data\` 下创建任何目录；不做写探针；不追加任何 registry／
exposure 事件；不写 `APPROVED`／`EFFECTIVE`／`RATIFIED` 值；**不代签 P2、不代拟
执行语句**；不改样本／标签／NA 政策／成本／Primary／Oracle／feasibility／运行定义；
不推送、不打标签、不 amend；不裁 Stage I 与 discretionary Tier-1 之别；
不推断 LANE／STAGE。

**READ_ONLY**：只裁不做，零文件修改。

---

## 8. 返回格式

```
ITEM=FOUR-OWNER
DELEGATED=YES
TRANSPORT_PRECHECK=PASS|STOP

ITEM=第 1 件 P3/失败事件的写者
  RULING=<窄读法采纳与否；「运行器存活」由谁判定；要不要 executor provenance>
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE
ITEM=第 2 件 目录创建授权的四要素
  RULING=<五个槽各自的形式，含有效期与 actor>
  ...同上四栏
ITEM=第 3 件 D-3 五项
  RULING=<逐项，明标哪一项不可代裁>
  ...同上四栏
ITEM=第 4 件 P2 的排序与 P1 的追加路径
  RULING=<顺序；P1 由谁在什么授权下追加；与第 1 件是否必须一致>
  ...同上四栏

CROSS_ITEM_CONSISTENCY=<第 1 与第 4 件是同一问题的两个实例，你的两条裁定是否相容>
STRONGEST_OBJECTION=<对你自己四条裁定中最弱的那条>
STILL_AARON_ONLY=<你认定不可代裁的，至少含 P2 的签署与 verbatim 语句>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本裁定不释放任何 gate，不是研究授权，不是运行授权。**
