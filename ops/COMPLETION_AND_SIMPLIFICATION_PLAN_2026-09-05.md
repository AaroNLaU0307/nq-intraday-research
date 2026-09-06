> **2026-09-07 · QROS-CF (DEC-0001):** this list is no longer a source of blockers or pending items. Everything in it was triaged into `ops/BACKLOG.md` (blocker set §1, backlog §2, closed items §3); the current stage is `ops/RESEARCH_STATE.md`. Kept unchanged below as history.

＃ QUANT PROJECT COMPLETION / SIMPLIFICATION PLAN

```ini
RECORD_TYPE=PLAN（不改代码、不读真实数据、不签 P2、不解开任何门）
BY=Opus 5，builder seat，2026-09-05
BASIS=Aaron 2026-09-05：FINISH THE QUANT RESEARCH WITH THE MINIMUM
      GOVERNANCE NECESSARY FOR CORRECTNESS
PRIORITY=correct research > reproducibility > essential safety
         > finishing the project > framework perfection
```

> **这份文件本身是一个矛盾:用一份新文档回答「文档太多」。**
> 所以它取代下一批本来会被写出来的东西——检查点记录、修复记录、
> 席位结果、复审结果各一份。**以后一段用一份运行日志,不是五份。**

---

## 0. 诊断 —— 量出来的,不是印象

```
2026-08-29 以来的提交
  src/ 改动    44 次
  ops/ 改动   191 次          <- 4.3 : 1
  ops 文档共 159 份，本周被触及 165 次

测试
  132 个文件，其中治理/元测试 31 个（23%），贡献 316 条
  最大的五个文件全部是 S0 研究测试（test_s0_runner 4569 行等）
```

**结论一:测试不是问题。** 体量集中在 S0 研究测试上,那是真正保护研究性质的东西,
**一条都不该删。**

**结论二:问题在流程产出。** 每推进一步工程 → 发现一个缺陷 → 写一份决策包 →
开一次复审 → 写一份席位记录 → 写一份验收记录 → 再加几条守卫。
**四点三比一就是这个循环的量度。**

**我是这个循环的主要制造者。** 本节会话我建了报告器、编排器、装配层、
`gates_at`、封存码四桶、两份决策包、两份送审包、更正横幅、守卫的守卫——
**其中真正修掉缺陷的只有三条**(H1 归档绑定、M1 `retry_permitted`、
`_declared_digest` 不认真实产品)。

---

## 1. 一个让一大块塌掉的事实

```
归档的 supplements 子树     0 个文件
_archived_bytes_lost(before, after)  只报「before 有、after 没了」
第一次真实运行 before = 空
=> archived_bytes_deleted **在第一次真实运行中结构上不可达**
```

**所以:ARCHIVE-CODE-6 修订、正在 Fable 手里的那次复审、
以及围绕它的整条决策链,一条都不挡第一次真实运行。**

它要到**第二次** supplement 运行(归档里已经有东西之后)才可能触发。

**Fable 那轮已经派出去了,让它跑完不花额外成本**——但它的结论
**不应该 gate 任何东西**。

---

## A. MUST FIX BEFORE REAL RUN

**只有三条,其中两条是你的。**

```
A1  ① job_dir 授权                                    -> Aaron
    候选 A 有机械证据（attestation 的 primary_root 之下）
    需要：逐字路径 + 文件名 + source_format

A2  把 dataset 侧输入接进 run_supplement_production    -> builder，约一段工作
    今天入口在「拿不到 universe/vol_method/flag_by_date」处拒绝
    ① 批准后这是纯接线，无新机制

A3  ③ live P2，绑定 A2 完成后的稳定 HEAD              -> Aaron
```

**H1/M1 已修;gate-first 路径已建;链路已从合成 bars 跑到 P4。**

### A2 的实测范围 —— **比我先前说的「一段接线」大,并且第四项是 blocker**

```
① bars_by_date        139 个 DBN 经 load_real            直接，databento 0.81 已装
② EventCalendar       gate1/f10_event_calendar/f10_events.csv
                      冻结、在仓内、列名与 EventCalendar 精确对应   直接
③ SessionSchedule     pandas_market_calendars CME_Equity
                      （生产先例 consumer.py:811）
                      vendor_degraded_dates 可来自 job 目录的 condition.json   要建
④ roll_intervals      **已解决 2026-09-05**（首次真实 Development 读取，Aaron 授权内）
                      来源：DBN metadata 的官方 continuous->instrument_id 映射
                      139 文件 -> 186 个逐文件区间 -> 合并 48 -> **47 个换月点**
                      零缺口/重叠；按月 3:11 6:12 9:12 12:12（完美季度）
                      **未用任何价格推断**；`df["symbol"]` 实测恒为 'NQ.v.0'
                      （连续符号，跨换月也不变），所以符号推导本就不可行
                      实现 src/itsf/data/symbology.py（纯函数与 I/O 分开）
                      测试 tests/test_symbology_rolls.py（10 条，**不读真实数据**）
```

**为什么 ④ 是 blocker 而不是 residual:**

```
_straddles_roll(older, newer, roll_transition_dates)
    return any(older < t <= newer for t in roll_transition_dates)
若为空 -> 永远 False -> r1_drop_and_extend 永不丢弃任何 return
-> vol20 跨合约换月计算，把价格跳空当成真实收益
-> 污染 terciles -> 污染 vol 分层 -> 污染补充的每一行
NQ.v.0 是连续前月序列，12 年约 48 次换月
```

**它命中过滤条件第一条(影响研究正确性),所以它曾阻塞 N09 —— 现已解除。**

**候选来源(未验证,需要一个决定):** DBN store 自带 symbology,
`_postprocess_static` 已经在读 `df["symbol"]`,所以换月点**可能可从 bars 自身导出**
(symbol 变化处)。`RollInterval` 的 docstring 称其为「官方 symbology 映射的一行
(IR-16, verify/disclose only)」——**若 DBN 内的 symbology 就是那份官方映射,导出是正确的;
若「官方」另有所指,那就要另找来源。这一条我不自己判。**


---

## B. MUST FIX BEFORE FINAL RESEARCH CONCLUSION

```
B1  N10 / N11 / N13 的实现                            <- **我不知道它们是什么**
    N11 从未实现；N13 依赖 N11；N10 依赖 N09 的真实执行
    内容在隔离的主计划里。**见 §5,这是唯一卡住这份计划的东西**

B2  archived_bytes_deleted 的裁定
    第二次真实 supplement 运行之前必须落地（那时归档非空）
    **不是第一次运行的 blocker**

B3  reveal / 结论阶段的暴露记账
    研究轴台账必须记全 —— 这条保护研究有效性，不可省
```

---

## C. SAFE TO DEFER / BACKLOG

```
C1  E: 第二份物理副本
    **重要重新评估**：这批数据 **$14.30 可重新购买**（purchase_plan A1）。
    「不可替代的证据」这个框架是错的。丢失风险是钱和时间，不是研究有效性。
    -> 记 backlog。真跑之前**不必**恢复

C2  UNMAPPED_SEAL_CODES 七条          全部失败关闭，无一能静默取得门名
C3  ARCHIVE-CODE-6 修订                见 §1，第一次运行不可达
C4  R1（第 8 轮后的修复未独立复审）     已经被你亲自审过一轮（H1/M1 就是那轮出的）
C5  P2 契约字段名与解析器不一致         已按解析器为准，记录在案
C6  S8 跨卷备份                        同 C1
C7  authorized_commit_matches_head      **不在早期拒绝块里**（早期只查 live 计数）。
    提前到早期拒绝块                    所以一条过期授权会先读完 3.8M 根 Development
                                        数据、再读封存的 S0 bundle，然后才在
                                        A_PRECHECK 拒。**不影响正确性**——门照拒，
                                        什么都没写。只是白烧一次全量读取。
                                        Aaron 2026-09-05：进 backlog，本轮不为性能
                                        动 gate ordering
```

---

## D. REMOVE OR STOP EXPANDING

**这一类是本计划的重点。**

```
D1  为「失败关闭的工程边缘状态」写决策包并开复审
    -> 停。失败关闭 + backlog 一行足够
    -> 本周两份决策包（archived_bytes_deleted、ARCHIVE-CODE-6）都属此类

D2  每一段工作产出多份 ops 记录（检查点/修复/席位结果/验收各一份）
    -> 停。一段一份运行日志

D3  为「保护提案格式」的守卫（自哈希、更正横幅、块生成器的测试）
    -> 只在真正要批准一份提案时才需要。不是常设

D4  冻结登记册 + 哈希表 + 伴随件的全套仪式，用于每一次复审
    -> 只用于**可能改变结论或安全性**的复审。工程问答不需要

D5  为理论上可能、但当前 critical path 不会触发的状态新增状态机层
    -> 停。§1 的 archived_bytes_deleted 就是活例

D6  守卫的守卫
    -> 现有的保留（它们已经抓到过真缺陷），**不再新增**
```

---

## 2. 最短 critical path

```
现在 ──> ① job_dir 授权（你）
      └─> A2 接线（我，约一段）
      └─> 跑全量、冻结 HEAD
      └─> ③ live P2（你）
      └─> **N09 第一次真实运行** ── 真实 supplement 封存
      └─> N10（依赖 N09 的真实执行）
      └─> N11 最小实现          <- 内容未知，见 §5
      └─> N13（MC 接线）
      └─> reveal / 决策（你）
      └─> candidate strategy build
      └─> validation
      └─> 最终研究结论
```

**从今天到 N09 真实运行:两个你的授权 + 我一段接线。** 没有别的。

---

## 3. 哪些 QROS 规则会阻碍收缩 —— 区分真伪

### 3.1 真正保护研究有效性,**不能动**

```
outcome-blind 席位纪律          席位烧毁不可逆，且已发生三次
两根曝光轴永不合并               研究自由度的记账是研究有效性本身
不得自证同一交付物               producing session 不能是唯一认证者
你保留的六类                     成本/Primary/样本切分/何时动真实数据/
                                promotion-falsified/quant-data 建目录
数据边界失败关闭                 role 隔离、manifest 校验、look-ahead
```

### 3.2 我们过去人为选择的工程治理偏好,**可以放松**

```
每次复审都要冻结登记册 + 哈希表 + 伴随件      -> 只用于结论/安全相关
每个工程边缘状态都要一份决策包                 -> 失败关闭 + backlog
L6 Review Packet 形式用于工程问答              -> 直接问，直接答
每段工作多份 ops 记录                          -> 一份运行日志
提案格式守卫常设                               -> 用时才建
「还能更严谨」就继续加层                        -> 你的停止规则已经写死了这条
```

**注意:3.2 里没有一条来自 QROS 文本本身。** 它们是**我在执行 QROS 时叠加的习惯**,
其中好几条是我这周为了修上一个缺陷而临时发明、然后变成了常例的。

---

## 4. 新增 test / guard / rule 之前的一句话检验

**照你给的写死:**

> **不加它,会不会让当前研究结果错误、不可复现、产生数据泄漏,或无法安全运行?**
> **否 -> 不加,记 backlog。**

我加一条自查,因为我这周犯的正是这个:

> **它保护的是研究,还是保护另一个守卫?**
> **后者 -> 不加。**

---

## 5. **唯一卡住这份计划的东西**

**我不知道 N10 / N11 / N13 是什么。** 依赖关系我从 outcome-clean 的恢复锚点读到了,
但它们各自要做什么,写在**隔离的主计划**里
(`ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`，**OFF-LIMITS**)。

```
按恢复锚点 §0，**我作为 builder 有权读它**
但读它会在研究轴上记一次暴露事件
我不会为了排进度自己去开 —— 那是你的决定
```

**两条出路,你选一条:**

```
甲  你授权我读主计划，把 N10/N11/N13 摸清楚，然后把 §2 的路径补成实际工作量
    代价：研究轴记一次暴露事件（项目已声明 TARGET_METRIC/HISTORICAL_CUMULATIVE，
          所以这不是新种类的暴露，但仍是一次事件，要入账）

乙  你直接告诉我这三个节点大致要做什么，我照着估
    代价：无
```

**在你选之前,§2 的后半段只有依赖关系,没有工作量估计。**
**我不会假装我知道。**
