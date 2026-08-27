# registry 迁出 OneDrive —— 迁移设计与决裁包

```ini
REVIEW_ID=dec-registry-migration-2026-08-27
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=决裁席（adversarial decision seat）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被裁字节的作者；dec-four-owner-2026-08-27 的那个会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
DELEGATED=YES —— Aaron 2026-08-27「给我决策的部分一律让 fable 替我选择，我同意」
SUBAGENT_OR_WORKFLOW_BUDGET=0
STATUS=DESIGN_ONLY —— 本文件不迁移任何东西，不创建任何目录，不改任何路径
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_REGISTRY_MIGRATION.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 0. 一个发现，它改变了这件事的性质

`dec-four-owner-2026-08-27` 第 3 件 #4 裁了迁移**方向**：

> 在任何生产代码运行时追加能力被启用之前，canonical registry 写入面**必须迁出
> 主动同步树**（候选：`C:\Users\Aaron\quant-data\` 治理根之下）。

**但同一天 Aaron 批准的 CR1 语法块（`c251335f…`）里有两条硬依赖，逐字**：

```
CR1_REGISTRY_INTACT_PREIMAGE=the complete on-disk bytes of ops/TRIAL_REGISTRY.md, …
CR1_REGISTRY_INTACT_COLD_RECOMPUTE=the preimage is recoverable from git history of
  ops/TRIAL_REGISTRY.md at the commit preceding this row, and the witness file is
  append-only, so a cold reader can recompute both sides
```

**实测（builder 已核）**：

```
当前 ops/TRIAL_REGISTRY.md   在 OneDrive 内 = 是   在 git 仓内 = 是
候选 C:\Users\Aaron\quant-data\   在 OneDrive 内 = 否   是 git 仓 = 否
```

**迁出仓库 ＝ 迁出 git ＝ `COLD_RECOMPUTE` 那一句变成假的**，而它在一个**已批准的
canonical 块内**。

**所以这不是一次运维搬移，而是一次需要修订已批准字节的动作。** 这一点两份裁定都
没有察觉——第 3 件 #4 与 CR1 语法是同一天的两份产物。

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `4539484721aa308410ba03b096d4b9f2822b78a806248fba035206836fbc5e52` | `9237` | `ops/RULING_FABLE_FOUR_OWNER_2026-08-27.md` |
| `eb8b6567d99760ee7438e8105e08f48a0584e0798175a9a236a6be5bf73b96b0` | `37109` | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md`（含 CR1 语法块） |
| `3964c7b8227542bd78c1b7706493dbf16cbf86c30b824a5560bfa505eb174adc` | `11830` | `ops/ND1_PROFILE_RATIFICATION.md`（含 §9 的 R3 批准） |
| `8734c430534314e8c7592c998e43a0485b90c37b9b0fb9df5d5736200d979424` | `5448` | `ops/REGISTRY_SYNC_FAILURE_MODEL.md` |
| `fdb6f99a58180e1439749f6a1e2b9343fb83b7e59e42461b28ddffd56c7f0520` | `9185` | `src/itsf/mc/registry_boundary.py` |

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

## 3. 迁移面盘点（builder 实测，非估计）

`git grep TRIAL_REGISTRY -- src scripts tests` 命中 **61 处**，其中：

```
真正构造路径的  15 处
  生产 5 处   scripts/s0_real_run.py:40        REGISTRY = REPO / "ops" / "TRIAL_REGISTRY.md"
              src/itsf/mc/consumer.py:3242     Path("ops/TRIAL_REGISTRY.md")
              src/itsf/mc/day_strata_supplement.py:139
              src/itsf/mc/real_input.py:30
              src/itsf/mc/registry_boundary.py:50  REGISTRY_PATH = "ops/TRIAL_REGISTRY.md"
  测试 9 处   test_mc_supplement_integration.py ×4 · test_mc_supplement_paths_battery.py ×2
              test_mc_supplement_runner.py ×2 · 其余 1
  另 1 处     scripts/s0_real_run.py:113  CLEAN_GATE_ALLOWLIST_FILES
仅提及名字的    46 处
```

**一条 builder 必须如实说明的**：`registry_boundary.py:50` 的注释写着
「**The one governed path**」，且该模块自陈是**唯一被允许读它的模块**。
**但另外四处生产代码各自构造这条路径。** 那句注释描述的是意图，不是被机械保证的
事实——迁移要改的是 5 处，不是 1 处。

---

## 4. 三条候选路线，各自的代价都是实的

```
路线 A —— 目标位置本身做成 git 仓
  在 C:\Users\Aaron\quant-data\<something>\ 下 git init，registry 迁入。
  CR1 的 COLD_RECOMPUTE 逐字仍真（那句只说「git 历史」，没说是哪个仓）。
  代价：多一个仓要维护；两个仓的 HEAD 与 commit 绑定语义要各自说清
        （P2 绑的 40 位 commit 是哪个仓的？）；备份与同步策略要重定。

路线 B —— 走 §D.10.3 出 R4，修订 CR1 语法块
  把 COLD_RECOMPUTE 改写成不依赖 git 的形式（例如只依赖 append-only 见证链）。
  代价：改动一个**今天刚批准**的 canonical 块（c251335f…），R3 的批准哈希随之
        全部重算；Aaron 要再签一次。且「刚签完就改」本身值得警惕。

路线 C —— 不迁，改为在原地消除同步风险
  例如把 ops/TRIAL_REGISTRY.md 排除出 OneDrive 同步（OneDrive 支持按文件夹排除）。
  CR1 语法一字不改，git 历史仍在，5 处路径构造一处不动。
  代价：依赖 OneDrive 的排除设置持续生效——一个**仓外的、不受版本控制的**配置；
        它被无声改回就等于风险回归，而这正是 L-5 事故的形状。
```

**请裁：A、B、C 三选一。** 并回答：

1. **若 A**：P2 的 `authorized_commit_40hex` 绑的是哪个仓的 commit？两个仓的
   commit 如何在证据里被同时钉住？
2. **若 B**：「刚批准就修订」是否需要额外的门（例如必须由 fresh Sol 先确认原批准
   未被此修订实质削弱）？
3. **若 C**：如何**机械地**检出排除设置被改回？（builder 的观察：`registry_witness`
   的见证链能检出 registry 内容退化，但检不出「同步被重新打开」这个前置条件。）
4. **无论哪条**：`registry_boundary.py:50` 那句「the one governed path」与实际 5 处
   构造之间的落差，要不要在迁移之前先用机械守卫补上？

---

## 5. 迁移本身的不变量（无论选哪条路线都适用）

builder 提出，供裁定采纳或修改：

```
1. 字节恒等   迁移前后 registry 的 SHA-256 必须逐字节相同；不得借机规范化、
              不得改行尾、不得改编码。
2. 事件数不减 迁移后事件计数 >= 迁移前（append-only 的最低要求）。
3. 见证先行   迁移前先写一条见证（registry_witness），迁移后用它验证
              CR1_REGISTRY_INTACT_CRITERION 的「superset of the witness」成立。
4. 回滚可行   迁移后原路径保留一份逐字节副本至少一个完整工作周期，
              且回滚不需要任何新授权。
5. 单点收敛   5 处路径构造收敛到 registry_boundary.REGISTRY_PATH 一处，
              并由机械守卫钉住「生产包内不存在第二处构造」。
6. 冲突副本扫描 迁移前后各扫一次 OneDrive 冲突命名（`*-<机器名>*`），
              任一命中即 STOP 上报。
```

**第 5 条是 builder 建议在迁移之前单独落地的**——它今天就能做、与路线选择无关，
且它让后续无论选哪条路线都只改一处。

---

## 6. 常设禁令（对你同样在 force）

不读真实 Development 数据；不执行 supplement／MC／S0／strategy；不在
`C:\Users\Aaron\quant-data\` 下创建任何目录；不做写探针；不追加任何 registry／
exposure 事件；不写 `APPROVED`／`EFFECTIVE`／`RATIFIED` 值；不代签 P2、不代拟执行
语句；**不执行任何迁移**；不推送、不打标签、不 amend。

**READ_ONLY**：只裁不做，零文件修改。

**迁移的执行本身不可代裁**——`dec-four-owner-2026-08-27` 已把它列进
`STILL_AARON_ONLY` 第 ④ 项。本裁定只定路线与不变量。

---

## 7. 返回格式

```
ITEM=REGISTRY-MIGRATION
DELEGATED=YES
TRANSPORT_PRECHECK=PASS|STOP

FINDING_ACKNOWLEDGED=<CR1 语法块的 git 依赖与迁移方向相抵，你是否确认这个发现成立>
ITEM=路线
  RULING=A|B|C
  逐条回答 §4 的四问
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE
ITEM=迁移不变量
  RULING=<§5 六条采纳/修改/增补>
  第 5 条（单点收敛）是否应在路线落定之前先行落地

STRONGEST_OBJECTION=<对你自己裁定中最弱的那条>
STILL_AARON_ONLY=<你认定不可代裁的，至少含迁移的执行本身>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本裁定不释放任何 gate，不是研究授权，不是运行授权，不授权任何迁移。**
