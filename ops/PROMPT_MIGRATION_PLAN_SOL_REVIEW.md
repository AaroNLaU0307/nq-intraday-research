# registry 迁移方案（路线 A）—— fresh Sol 复审

```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=reviewer（迁移方案复审）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；方案作者；任何一个 Fable 决裁席会话；migration executor
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_MIGRATION_PLAN_SOL_REVIEW.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 0. 你在审什么，以及链条位置

`dec-registry-migration-2026-08-27` 定了路线（A）与十条不变量，并明写：

> **具体迁移方案须单独出包、经 fresh Sol 审后由 Aaron 亲批——迁移的执行不可代裁。**

```
方案包（已出，本轮送审）→ 【你】→ Aaron 亲批并执行
```

**你审的是方案，不是路线。** 路线 A 已由决裁席裁定、Aaron 采纳。若你认为路线本身
错了，写进 `UNRESOLVED_FOR_AARON`，不要改裁。

### 必须先告知你的两条独立性事实

1. **裁定路线 A 的决裁席自陈**：它对该迁移方案有实质设计贡献（路线 ＋ 十条不变量），
   **因此对本方案的后续独立验证席位失格**。它自己写：「跨家族多样性由后续 fresh Sol
   方案复核恢复」——**那就是你**。
2. **三份相关裁定全部出自同一模型家族（Fable）**，其中一份还收窄了另一份的措辞。
   **本链条至今没有跨家族的独立审查。**

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `fc9b5a81e206ed3187da3ee2789e5a5addd401862afaa47f7177a4878a9f8c7c` | 10941 | `ops/REGISTRY_MIGRATION_PLAN_ROUTE_A.md` |
| `8734c430534314e8c7592c998e43a0485b90c37b9b0fb9df5d5736200d979424` | 5448 | `ops/REGISTRY_SYNC_FAILURE_MODEL.md` |
| `a62030d72113a3c16a8190449fc42f2623c38bdd254c8de6a40a697e1ff86538` | 7645 | `ops/RULING_FABLE_SCOPE_AND_MIGRATION_2026-08-27.md` |
| `963446b1725630b78c1744730f203fbe930f9f92adf178bee3b8ca47ecd1055d` | 10557 | `src/itsf/mc/registry_boundary.py` |
| `eb8b6567d99760ee7438e8105e08f48a0584e0798175a9a236a6be5bf73b96b0` | 37109 | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md`（含已批准 CR1 语法块） |

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

## 3. 方案要点（细节以送审文件为准，本节只为定位）

```
目的地   C:\Users\Aaron\quant-data\itsf-registry\   ← 新 git 仓根（今天不存在）
         其内相对路径保持 ops/TRIAL_REGISTRY.md     ← 刻意，见下
步骤     S0 前置核证 · S1 见证先行 · S2 git init ＋ 首 commit · S3 移字节
         S4 两仓交叉互钉 · S5 旧路径墓碑＋改名副本 · S6 路径切换
         S7 后置核证 · S8 备份形态
已先行   不变量 5（路径构造收敛到一处）· 不变量 8（缺失即拒），均已落地并变异证红
```

**相对路径保持不变的理由**：已批准 CR1 语法块（`c251335f…`）的
`CR1_REGISTRY_INTACT_PREIMAGE` 与 `CR1_REGISTRY_INTACT_COLD_RECOMPUTE`
**逐字点名 `ops/TRIAL_REGISTRY.md`**。保持它，那两句在新仓里逐字仍真。

---

## 4. 请重点打的六件

### ① 有没有一个时刻，registry 既不在旧处也不在新处

或者更糟：**两处都是「真的」而无法判定哪个权威**。请逐步走 S0–S8，找那个窗口。

### ② S4 的交叉互钉是否真的闭合

builder 用「新仓记旧仓**迁移前** HEAD ＋ 三元组；旧仓迁移 commit 记新仓 commit」
来避开循环依赖。**请判冷读者从两侧是否都拿得到 `COLD_RECOMPUTE` 需要的东西**
——迁移前的行与迁移后的行都要。

### ③ 「所指已移」够不够 —— 这是决裁席自陈的最弱处

`c251335f…` 批准时「git 历史」的默认所指显然是 ITSF 仓；路线 A 把所指换成一个
**批准时不存在的仓**。裁定的缓解是治理性的（Aaron 的批准文本须显式指名新仓）。

**决裁席自己说**：

> 怀疑者可以正当地说：这种哈希稳定、语义漂移的读法，恰恰应该走 R4 让 Aaron
> 重新签，而我为了省一次签字选了不签。……若认为这不够、仍须 R4，我不反对。

**请判**：治理缓解够，还是必须走 §D.10.3 出 R4 重签 CR1 语法块。

### ④ 边界 (3) 跨了两个仓之后还成不成立

`REGISTRY_SYNC_FAILURE_MODEL.md` 边界 (3)：「registry 追加与 `git commit` 属
**同一操作步骤**」、仲裁顺序「git 历史 > 见证 > 工作区」。

新仓下这条逐字仍可执行，**但一次治理追加现在要在新仓 commit，而相关代码状态在旧仓**。
请判是否需要一条跨仓的提交纪律，还是原文已足。

### ⑤ `RegistrySnapshot` 加一个 registry 仓 HEAD 字段，是加性还是接口改动

裁定要求「凡记录 `registry_sha256` 之处随行加记 registry 仓 HEAD 作旁证」。
`RegistrySnapshot` 今天不带该字段。**builder 不自判**。

### ⑥ 不变量 10 的备份形态

git push 到另一物理卷的 bare 仓 —— **是否真与本次事故形状正交**，还是引入了新通道？
裁定禁止对新根做任何文件级同步复制，理由是「那是把通道 A 原样请回来」。

---

## 5. 一件 builder 主动报告的

方案里那条环境事实是实测的，**它改变了这件事的框架**：

```
HKCU\...\User Shell Folders
  Desktop  -> C:\Users\Aaron\OneDrive\Desktop
  Personal -> C:\Users\Aaron\OneDrive\Documents
OneDrive.Sync.Service 运行中
```

**这台机器上的桌面就是 OneDrive。** 任何放在桌面下的仓都在同步树里，与放置者的
选择无关——所以「注意别放进去」从来不是可行的缓解。

**请自行复核该注册表读数**，不要采信本段。

---

## 6. 只读

- **不执行任何一步**：不创建目录、不 `git init`、不移动任何字节、不改任何常量。
- **不代 Aaron 批准**：迁移的执行是 `STILL_AARON_ONLY`。
- 其余常设禁令：不读真实 Development 数据；不执行 supplement／MC／S0／strategy；
  不做写探针；不追加任何 registry／exposure 事件；不写 `APPROVED`／`RATIFIED` 值；
  不推送、不打标签、不 amend。

---

## 7. 返回格式

```
ITEM=REGISTRY-MIGRATION-PLAN
TRANSPORT_PRECHECK=PASS|STOP
VERDICT=PASS | HOLD
逐条作答：① 有无「两不在／两都真」窗口 · ② 交叉互钉是否闭合 ·
         ③ 所指已移够不够（治理缓解 vs R4）· ④ 边界 (3) 跨仓 ·
         ⑤ RegistrySnapshot 字段的加性判定 · ⑥ 备份形态是否正交
UNDECLARED_ASSUMPTIONS=<方案默认了哪些尚未授权的东西；builder 自查为无>
STRONGEST_OBJECTION=<即使 PASS 也要写>
FINDINGS=<逐条，带文件与步骤号>
UNRESOLVED_FOR_AARON=<你与 builder 都不得替他决定的；至少含迁移的执行本身>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本复审不释放任何 gate，不授权任何迁移，不创建任何目录。**
