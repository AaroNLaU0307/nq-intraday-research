# Aaron 本人裁定 —— 2026-08-25（四项）

```
RECORD_TYPE=OWNER_DECISION
DECIDED_BY=Aaron，本人
DELEGATED=NO —— 这四项是 Aaron 自己的判断，不是委托裁定。引用时不得与
          2026-08-24 那批（Sol 在具名委托下裁定，DELEGATED=YES）混记。
EFFECT=即时生效
TRANSCRIBED_BY=Opus 5 main agent（builder seat）—— 转录，非背书
HEAD_AT_TRANSCRIPTION=167045f7…（转录不改 HEAD；本记录落盘会改）
BASIS=ops/N00_N08_PROVENANCE_AUDIT_2026-08-25.md
      （SHA256 F5A8F3B7A683127D9536C02D4BB5C4C0A0E12755A106176A45F9B1646C03B2CA）
```

---

## OD-2026-08-25-1 —— N09 暂不签发

```
N09_P2_SIGNED=NO
REASON=执行路径尚未存在；签发会绑定一个必然过期的 commit
RESUME_CONDITION=执行路径完成 AND HEAD 稳定在待审 commit 上
```

Aaron 原话：「先不签 N09……等执行路径完成、HEAD 稳定后再让我签 P2。」

**为什么这是对的，机械依据**：`_g_authorized_commit_matches_head`
（`supplement_runner.py:312`）要求授权 commit **等于运行时 HEAD**。而两个生产
入口今天都无条件拒绝——`day_strata_supplement.authorize_supplement` 与
`supplement_runner.run_supplement_production` 末行的 raise 都没有条件分支，
`GateContext` 在全仓只有测试构造过。所以今天签 P2 既不解锁执行，又保证以后要
走一次 P2S。

**三个值仍然有效，只有 commit 会随 HEAD 变**：

```
supplement_id = MC-DS-S001            （supplement_contract.py:51 与
                                       day_strata_supplement.py:50 互证）
output_root   = C:\Users\Aaron\quant-data\itsf-runs
                                      （L-5 裁定 2026-08-10；RunConfig 默认值
                                       即裁定值；S0-T001 封存路径经验证实；
                                       _g_output_root_structure 机械绑死——
                                       别的值过不了门）
authorized_commit = <签发当时的 HEAD，40 位全长>
```

---

## OD-2026-08-25-2 —— N08 废弃

```
N08=DROPPED
DAG_EFFECT=§4 表中 N08 行标记为 DROPPED，保留不删除（append-only 纪律：
           删掉它，后人就看不见它存在过以及为何废弃）
```

Aaron 原话：「N08 按审计结果 DROP。」

**依据（审计已机械核实）**：全仓仅主计划 §4 一行定义它；其来源链
（Fable V1/V1.1/V1.2、Codex 综合稿 `OPUS5_MC_TO_STRATEGY_V1`）从未入库，
故「9/12 簇」抄自只存在于聊天的文档；git history、全部 ops/ 与仓根 md、
`Quant trade\` 下 14 个仓，全部零命中；**DAG 全表扫描：零下游依赖**；表自身
写着 `数据面=none／权限=工程`，故不承担 preregistration／exposure／authority／
provenance／candidate-selection 中任何一项。

**随裁定一起冻结的一句话**：若日后仍要做一次广域逻辑审计，那是**一次新的范围
裁定**，必须以新名义登记，**不得写成「恢复了 N08」**。审计里那条未采用的线索
（一份未复核的 agent 记忆笔记列了九个簇名，树对其中任何一个零命中）保留在
审计记录 §1.4，供 Aaron 日后若认得出处时使用——它不是 authority。

---

## OD-2026-08-25-3 —— N00 保留，且不阻断 N09→N17

```
N00=KEEP_UNRESOLVED
BLOCKS_N09_TO_N17=NO
BLOCKS_CANDIDATE_SPECIFIC_BUILD=YES（N18-C 与 N18-I）
```

Aaron 原话：「N00 保留但不阻断当前 N09→N17。」

**这不是对审计的推翻，是对审计发现的确认。** DAG 全表扫描：以 N00 为前置的
节点恰两个，`N18-C` 与 `N18-I`；N09…N17 之中无一以它为前置。§11.4 的效力
不变——五项不齐，即使 N17=GO 也不得开始任何 candidate-specific strategy build。

**未解决项仍是同一件**：Round-4 sealed proposal 原文是否还在 Aaron 手上。
在 → 走 `DECISION_PACKET_N00_AND_ND1.md` §D.1.3 的补交路径。不在 → 才轮到
`FORMALLY_LOST`，而宣告丢失**本身不解锁任何东西**，另需一次独立裁定授权
**新的**候选定义程序（新 authority，明确不是 Round-4 的恢复）。

---

## OD-2026-08-25-4 —— 走 fresh Sol 独立裁定，且在其返回前不推进

```
MC-REG-COLLISION-001=AWAITING_FRESH_SOL_RATIFICATION
BUILDER_ADVANCE_BEFORE_SOL_RETURNS=NO
```

Aaron 原话：「按你的建议继续走 fresh Sol 独立裁定……Sol 回来后再继续推进。」

提示词：`ops/MC_REG_COLLISION_SOL_RATIFICATION_PROMPT.md`。六份工件已登记于
`ops/ARTIFACTS_UNDER_REVIEW.json`（review_id
`MC-REG-COLLISION-001-RATIFICATION`），Sol 交回前 builder 不得改动其字节。

**「在 Sol 返回前不推进」是按字面执行的**：本轮不动执行路径、不动 N13、不动
任何被冻结的工件。本记录与 §4/§15 的 N08 状态更新是**转录 Aaron 已作出的
裁定**，不是推进。

---

## 生效后的节点状态增量

```
N08：BLOCKED/SCOPE_UNRESOLVED → DROPPED（Aaron 本人，DELEGATED=NO）
N00：BLOCKED → KEEP_UNRESOLVED；阻断面澄清为仅 N18-C／N18-I
N09：等待 Aaron 的 P2 —— 但前置补一条：执行路径须先存在
MC-REG-COLLISION-001：Fable 提案已落盘，待 fresh Sol
```
