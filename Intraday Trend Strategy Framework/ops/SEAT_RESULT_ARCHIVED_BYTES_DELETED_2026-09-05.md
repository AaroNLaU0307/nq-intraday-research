＃ 席位结果验收 · DECISION-ARCHIVED-BYTES-DELETED-001

```ini
RECORD_TYPE=REVIEW_RESULT（builder 验收；席位给建议，裁定归 Aaron）
SEAT=GPT 6 ASTRA，fresh session（Aaron 指定；builder 原推荐 Codex Sol）
SEAT_SCOPE=字节核验 ＋ 静态源码核对。**未执行项目代码或 pytest**，
           因此席位明确声明不主张动态复现 —— 这个自陈边界是对的，我照抄不上调
BY=Opus 5，builder seat，2026-09-05
```

---

## 0. 结论先说：**席位是对的，我又错了一次，而且是同一种错**

席位的 High 是：包里「A2 是 A1 唯一出口，所以 O2 无出口」**是错的**。

**我复现了，它成立：**

```
A1 successors : ['A2', 'AX']
AX            : SUPPLEMENT_ARCHIVE_PERMANENTLY_FAILED     A1 -> AX -> F3
转移规划器     : A1 -> {"recovered": "A2", "permanent": "AX"}
```

**最难堪的是：我自己两步之前就测出过这一行，并且把它印在了同一份包的 §2 里
（`A1 -> A2, AX`），然后在 §4 写「A1 的唯一出口 A2」。**

> **同一份文档里，§2 的表和 §4 的结论互相矛盾，而我没看见。**

这和 BD-5 是同一个形状：**从一个记住的抽象推理，而不是去读手边那张已经量出来的表。**
上次的教训我写成了「要去查树」——**这次表就在同一份文件里，我还是没查。**

## 1. 席位其余发现，逐条验收

| # | 席位所指 | 我的复现 | 结论 |
|---|---|---|---|
| Q1-F2 | F2 规划器要求 `residue_path` 并填 `residue_preserved=YES`，所以 O1 的代价是「该 run 退役」而非「有效字节被丢弃」 | `plan_failure_event` 第 19 行确实填 `"residue_preserved": "YES"`，且缺 `residue_path` 时抛 `post_start_residue_path_required` | **成立。我把 O1 的代价写重了** |
| Q1-P4 | 包混淆了「本次拷贝 archive_ok」与「历史归档完好」；Router B 单独看到本地成功＋archive_ok 就返回 P4，历史保护来自上游拒绝 | 属实。`decide_after_seal` 只看 `report.status`；挡住它的是链路里那条具名拒绝 | **成立** |
| Q1-A1 | 「行在实现上绝对写不出来」超出三份文件能证明的范围 | 属实。我证明的是「该码不在 5 个枚举值内」，不是「完整登记校验链会拒」 | **成立，我的声称比证据宽** |
| Q1-CR1 | 无崩溃则不成立，悬空 P3 不能替代崩溃证据 | 一致 | 成立 |
| Q3 | **「P3 已经落地」未被独立证实** | **复现，而且比席位说的更强**：`supplement_runner` 头部逐字写着「The planner NEVER appends a registry row... Nothing in this module writes to `ops/TRIAL_REGISTRY.md`」。**当前构建里没有任何代码追加 P3** | **成立。我那句是无根据的断言** |
| Q3 | 事后补 F2 涉及执行者溯源：F2 是 `ACTOR_RUNNER`，CR1 是人工治理事件 | `plan_failure_event` 确实以 `sc.ACTOR_RUNNER` 构造 F2 | 成立 |
| Q4 | 漏列组合 `P3 → A1 → AX → F3` | 复现 | **成立，这是 High 的直接后果** |
| Q5 | O4 作为临时闸可保留，但不等于完整事故处置 | 一致 | 成立 |

**席位没有夸大自己的证据。** 它明确说了「没有执行 pytest，因此不声称动态复现」，
并把「A2 只校验本次拷贝」标为**条件推论而非已复现漏洞**。**这两处自我限制都是对的。**

## 2. 我已经改的（只改假陈述，不动裁定）

```
supplement_chain.py    ARCHIVED_BYTES_DELETED_HAS_NO_RULED_TERMINAL
                       删掉「A2 是唯一出口」，改为「A1 有两个出口：A2 与 AX」
supplement_chain.py    时刻 3 的注释同上
supplement_runner.py   decide_after_seal 的 BD-5 收回说明同上
```

**这是订正假陈述，不是裁定。** 代码行为一字未变，仍然具名拒绝。

## 3. 交给 Aaron 的四项

### 3.1 推荐选项 —— **O2′：A1 ＋ 新增一个 `archive_code`，并裁定该码的出口是 AX**

**决定性的机械理由（席位点到，我复现了）：**

```
ROUTER_OF = {"archive_policy_a": "B"}      —— 该 outcome 归 Router B，已裁
Router B 的词汇是 P4 / A1 / 拒绝的 seal    —— A1 在其中
F2 只能由 Router A（plan_failure_event）发出
=> 判 F2 就是把 archive_policy_a 路由回 Router A
=> 而 tests/test_n09_r3_design_facts.py 的
   test_routing_it_as_an_ordinary_gate_contradicts_policy_a
   **执行的正是这条路，并证明它与 Policy A 矛盾**
```

**O1 会重建一个已经被写成测试执行出来的缺陷。** 这不是权衡，这是回头踩坑。

而 A1 这一侧，**在我的错误被订正之后，代价比我原先写的小得多**：

```
A1 -> AX -> F3     退役路径，**不需要修订 A2**
AX 必填            supplement_id · archive_code · attempts_count · incident_id
                   aaron_ruling_doc · local_seal_sha256 · local_seal_immutable
                   —— 给定新码与你的 ruling doc，七项全部可填
```

**并且必须一并裁定：该码的出口只能是 AX，不能是 A2。**
否则「本次拷贝全部匹配」会被用来宣告「历史损失已解决」——
**那正是席位 Q2 指出的、真正的风险。** 这条裁定**不需要改 A2 的字段**。

**反方论据，我一并摆上：** O1 不需要任何枚举修订，且 residue 确实被保留。
**如果你认为「不动已批枚举」的价值高于「记录说真话」，O1 是可选的**——
但要接受两件事：Router 的矛盾，以及把一次成功封存记成失败 run。

### 3.2 对现有已批准枚举／状态机的影响

```
ARCHIVE_CODES        5 -> 6            <- **唯一的枚举改动**
EVENTS 表            不动
转移规划器            不动（A1 -> AX 已存在）
A2 的必填字段         不动
ROUTER_OF            不动
```

**一个尚未解决的实现问题，我现在就标出来:**
`classify_archive_report` 是从 `ArchiveReport` 的**结构**映射出码的，
而本缺陷不在 ArchiveReport 里（报告说 `archive_ok`）。
**所以新码不会来自那个分类器，只能来自 C_BUILD_3 的 outcome。**
这条接线怎么做，需要在裁定之后单独设计——**我不在裁定前预设它。**

### 3.3 是否需要 R4 级修改 —— **是**

扩充 `ARCHIVE_CODES` 是修改**已批准的封闭枚举**。按本仓 R4 先例，需要：

```
提案文档 -> 规范块 -> canonical sha256 -> 你绑定 EXACT_DOC_HEAD 的批准语
```

**不是一句 ratify 就够。** O1 则不需要 R4。

### 3.4 若保持 fail-closed：dangling P3 / CR1 的具体后果

**先更正我自己：** 我写过「P3 已经落地而没有后继」。**当前构建里没有任何代码追加 P3**
（planner 从不追加登记行）。所以：

```
今天的构建        不存在 dangling P3 —— 我那句是无根据的断言
真实授权运行之后   P3 会在开跑前被追加，届时悬空才是真的（条件成立）
阻断范围          per-ID，不是所有共用归档根的工作都被系统阻断
CR1 资格          **不自动获得** —— 需要真实的进程死亡及其证据，
                  「有个悬空事件」不等于「发生了崩溃」
事后补 F2         执行者溯源问题：F2 是 ACTOR_RUNNER 事件，
                  人工补记不能伪装成原进程发射
拒绝的时机        发生在归档尝试**之后**，它不撤销已经发生的损失
```

**席位的一条建议我认为该采纳:** 保留原始 before/after 见证与当时的 seal 哈希，
**避免日后用「缺失之后」的目录重建基线,把事故从检查条件里抹掉。**

## 4. 我在这一题上的错误清单

```
一  BD-5      把 Router B 的返回值集合当成状态机的后继集合   -> 已收回
二  本包 §4   说 A2 是 A1 唯一出口，而 §2 自己印着 A1 -> A2, AX
三  本包 §4   O4「P3 已经落地」——当前构建根本没有追加路径
四  本包 §3   「A1 行绝对写不出来」比证据宽
```

**二、三、四是同一份文档里的三处，全部是「声称比手边的证据宽」。**
**而第二条尤其应该被记住：证据不但在手边，它就印在同一份文件的两节之前。**
