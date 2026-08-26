# 恢复锚（outcome-clean）

> **任何会话从这里开始。** 本文件**不含任何揭盲结果**，永不进入
> `ops/OUTCOME_CARRYING_ARTIFACTS.json`，因此 outcome-blind 席位可以安全读它。
>
> 它取代主计划 §1 成为恢复入口。主计划
> （`ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md` —— **OFF-LIMITS**）仍是 DAG 与节点台账
> 的权威，但它是隔离件；需要其中事实时见 §0 与 §1。

```
ANCHOR_STATUS        = outcome-clean，永不隔离
SUPERSEDES           = 主计划 §1「恢复序」（该文件 OFF-LIMITS，见 §1）
RULED_BY             = D-2（Fable，2026-08-26，DELEGATED=YES），选项 C：拆锚 ＋ 保留围栏
WHY                  = 旧恢复序把每一个 outcome-blind 席位引向一份隔离件
```

---

## 0. 先判断你是谁

**你是 outcome-blind 复审席位吗？**（Stage I、A2、任何被要求保持 outcome 盲的角色）

- **是** → 只读本文件的 §1、§2、§5。**不得在本仓做任何检索**（不 grep、不
  rglob、不广域符号搜索）。需要的字节由工作会话经 Review Packet v1 的
  `PULL_PROTOCOL` 提供。理由见 §5。
- **否**（builder／owner／已暴露席位）→ 全文可读，§3 给出通往权威件的路径。

## 1. 禁区（读任何别的东西之前先读这条）

权威清单：**`ops/OUTCOME_CARRYING_ARTIFACTS.json`** 的 `carries_outcome`。
**里面每一条路径都当作关闭。**

本文件点名以下隔离件**仅为标记其为禁区**，不是引导你去读：

```
OFF-LIMITS   ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md      （DAG／节点台账的权威，但隔离）
OFF-LIMITS   ops/EXPOSURE_LEDGER.md                  （研究轴暴露台账）
OFF-LIMITS   EXPOSURE_LEDGER.md                      （仓根权威历史台账）
OFF-LIMITS   注册表列出的其余全部路径
```

需要主计划里的某项事实时：**列出你要的路径，请工作会话提供字节**，不要自己去开。

## 2. 两条暴露轴（永不混记）

```
研究轴  ops/EXPOSURE_LEDGER.md        —— 消耗研究自由度         【OFF-LIMITS】
席位轴  ops/REVIEWER_EXPOSURE_LOG.md  —— 复审席位被烧；不消耗自由度  【可读】
```

**烧掉一个席位不消耗研究自由度**，所以分账。要确认某个席位是否仍 blind，看
**席位轴**——它刻意保持 outcome-clean 且不隔离，就是为了能被读。

## 3. 恢复序（取代主计划 §1）

| 次序 | 读什么 | 状态 |
|---|---|---|
| 1 | **本文件** | outcome-clean |
| 2 | `ops/NEXT_HANDOFF.md` —— 下一份要交出去的东西，固定文件名 | outcome-clean |
| 3 | `qros status` / `qros check`（机械状态：lane、stage、seal、freshness） | outcome-clean |
| 4 | `ops/README.md` —— `ops/` 全量索引，标注了哪些隔离 | outcome-clean |
| 5 | `ops/TRIAL_REGISTRY.md` 尾部 —— 事件真相源，append-only | 未隔离 |
| 6 | `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md` 最高编号锚节 —— DAG／节点台账 | **【OFF-LIMITS，blind 席位不得读】** |

第 6 项**只对已暴露的 builder／owner 开放**。blind 席位需要其中事实时走 §0 的
`PULL_PROTOCOL`。

## 4. 现势位置（不含任何揭盲结果）

```
LANE   = FULL          STAGE  = C（工作会话自陈，非裁定）
L6     = OPERATIONAL；本仓注册为 ITSF-S0，状态文件 qros-state.yaml
```

**执行段停在哪：** N09（MC-DS-S001 执行封存）需要 Aaron 的 P2 精确授权。
N10 依赖 N09 的真实执行；N11 从未实现；N13 依赖 N11。**故 N12 之后不存在
builder 可独立推进的 DAG 节点。**

**另有三条独立授权，不得合并**（ND1 批准）：目录创建 / 写探针 / 执行。
`DIRECTORY_CREATION_AUTHORIZED=NO` 时，签了 P2 也不能创建
`supplements\` 子树。

**未决交给谁**：见 `ops/NEXT_HANDOFF.md`。

## 5. 为什么禁止 blind 席位检索

三个复审席位被触到，**只有一个是刻意打开文件的**：

- 第 1 个：按常规做状态定位，打开了旧恢复序指向的隔离锚。
- 第 2 个：**从未打开该文件**——一次广域符号搜索带出了片段。
- 第 3 个：**一次单模式定向 grep** 就触到了。

所以「别打开文件 X」这类围栏**在原理上不够**：只要隔离内容还在席位能检索到的
树里，任何检索都可能带出它。拆锚（本文件）去掉了**入口**这个源头；**禁止检索**
去掉了另一个。两者都要，因为席位烧毁不可逆，一次性不可逆危害不允许单层防线。

记录：`ops/REVIEWER_EXPOSURE_LOG.md`（可读）。

## 6. 本文件的约束（守卫钉着）

- 永不含注册表的四类还原内容 —— `tests/test_review_artifacts_are_outcome_clean.py`
- 永不进入 `carries_outcome` —— `tests/test_recovery_anchor_is_clean.py`
- 点名任何隔离路径时必须带 `OFF-LIMITS` 标记 —— 同上
- 主计划**只以 append 追加重定向横幅**，旧 §1 不删不改（D-2 条件 2）

## 7. 隔离子树（R5 迁移，2026-08-27 追加）

```
OFF-LIMITS   ops/outcome_quarantine/**        —— 该前缀下一切路径关闭
OFF-LIMITS   ops/EXPOSURE_LEDGER.md           —— 不在前缀下，逐字点名
OFF-LIMITS   EXPOSURE_LEDGER.md               —— 不在前缀下，逐字点名（仓根）
```

**注册表 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 仍是唯一权威。前缀是便利，不是
替代**——注册表 12 条里**有 2 条不在这个前缀下**（上面两份台账，R1 裁 A′ 留在
原地）。**只查前缀会漏掉它们。**

**迁移不使仓内检索变安全。** 子树仍在树里；`BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY`
**永久在 force，不是过渡措施**——不得以「已经归拢了」为由放松（R1 条件 2、R5 条件 4）。
