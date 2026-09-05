＃ 送审包 —— ARCHIVE-CODE-6 修订提案的对抗性复审

```ini
PACKET_TYPE=ADVERSARIAL_REVIEW_OF_A_PROPOSAL（不是 A2，不是 Stage I，不解开任何 QROS 门）
REVIEW_ID=AMEND-ARCHIVE-CODE-6-REVIEW-001
DELIVERY_STATUS=RETURNED
COMPANION=ops/NEXT_HANDOFF.md（禁读清单载体，必须同行）
PREPARED_BY=Opus 5，builder seat
FOR=Fable，fresh session —— **对抗性审查，给建议**
DECIDED_BY=Aaron —— **席位不裁定，也不代签**
REVIEWED_SET_UNCHANGED_SINCE=88035e415b4f33091a48aac8b5e591ac6209a5f1
```

---

## 0. 受审集 —— **先逐字节核对，再开工**

对下表每一行重算 sha256 并比对。**不符即 STOP 并报告。**
聊天里贴过来的字节永远不是真相来源；请从磁盘读。

| sha256 | bytes | 路径 |
|---|---|---|
| `e444fe5870751be8ef3feff57b38ad8da88fc6758067470e82d98195c084738b` | `7165` | `ops/AMENDMENT_ARCHIVE_CODE_6_2026-09-05.md` |
| `053760ef10eec62236815215ab712638d2737a0602bea5dd99bda27f5ce60e87` | `5187` | `scripts/archive_code_6_block_builder.py` |
| `bda85429e1aab979ce033d4aafae04241b935514452e58d49e4b534c2a519e54` | `33867` | `src/itsf/mc/supplement_contract.py` |
| `133d40956672359c166b57e0957118ac923ebfd356aab0891dda6b87225f03a8` | `55911` | `src/itsf/mc/supplement_runner.py` |
| `94c885289f8ac6331b68ede5ee6ba712b63b275a660248346f28f220f6dccae2` | `15980` | `src/itsf/mc/supplement_chain.py` |

本包自身的 sha256 记录在 `ops/ARTIFACTS_UNDER_REVIEW.json`。

## 0.1 禁读 —— **权威清单在哪**

【OFF-LIMITS】outcome-carrying 的权威清单是
`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`（12 条，机器可读）。
**逐字清单与那个结构性陷阱在 `ops/NEXT_HANDOFF.md`，它必须与本包一同交付。**

**以那个 JSON 为准，不要凭记忆，也不要凭本包。** 清单会变，文档不会跟着变——
这正是本节只给指针、不给副本的原因。

## 1. 这次审什么

**一份待批准的修订提案**：给已批准的封闭枚举 `ARCHIVE_CODES` 增加第六个成员。

背景一句话：补充跑完之后，本地封存文件成功写出，
而**归档动作毁掉了更早已在归档里的字节**。这个组合目前没有合法终态，
代码对它具名拒绝。提案要给它一个。

**这个场景从未发生过，也不可能已经发生**——真实运行一次都没跑过。
**这是在给一个假想故障提前定规则。**

## 2. builder 在这道题上已经错了两次 —— **请把这当成基准怀疑度**

```
一  BD-5：判 A1，理由是「Router B 的答案空间封闭，排除法只剩 A1」
    错在把**函数的返回值集合**当成**状态机的后继集合**。已收回
二  决策包：写「A2 是 A1 唯一出口」
    错。A1 -> AX -> F3 存在。**而同一份包的 §2 自己就印着 A1 -> A2, AX**
```

**两次都是「声称宽于手边的证据」。第二次证据就在同一份文件里。**

## 3. 请攻击的四条，按我自己的把握从低到高

```
一  §0 那条自述：新码不满足枚举的自述不变量，所以修订同时要 widen 它。
    **这是我在 Aaron 决定之后才发现的** —— 我给他的成本描述当时是不完整的。
    问：widen 一条已批准枚举的自述不变量，是否比「加一个成员」更重？
        它是否需要比本提案更高规格的程序？

二  「判 F2 会重建一个已写成测试的 Router 矛盾」——我把这条当成决定性论据。
    机械依据：ROUTER_OF 把 archive_policy_a 给 Router B；F2 只能由 Router A 发出；
    tests/test_n09_r3_design_facts.py 的
    test_routing_it_as_an_ordinary_gate_contradicts_policy_a 执行了这条矛盾。
    问：这条论据真的决定性吗？有没有一种读法让 F2 仍然合法？

三  「该码唯一出口是 AX」这条约束，我提议用一层映射表达
    （不动封闭枚举，与 CHECKPOINT_OF / ROUTER_OF 同法）。
    问：这层映射会不会变成第二份不变量实现，与将来的 A2 校验器漂移？

四  上一个席位说「A2 只校验本次拷贝」是**条件推论，它没读到实际的恢复校验器**。
    本提案第 3 节建立在该推论上。
    问：请去读那个校验器。**若它其实也覆盖历史归档，第 3 节的必要性会下降。**
```

## 4. 我明确没有做的

```
未实现任何东西      ARCHIVE_CODES 仍是 5 个，守卫断言这一点
未设计接线          新码从 C_BUILD_3 outcome 来还是别处，未定
未占 R 编号          该命名空间已被三个系列同时使用，留给 Aaron
```

## 5. 复现命令（只读）

```
python scripts/archive_code_6_block_builder.py
python -m pytest tests/test_a_proposal_states_the_hash_of_its_own_block.py -q
python -m pytest tests/test_n09_r3_design_facts.py -q
python -c "from itsf.mc import supplement_contract as sc; print(len(sc.ARCHIVE_CODES), sc.ARCHIVE_CODES)"
```

## 6. 请回答

```
Q1  §3 四条，哪些成立、哪些是我想多了？
Q2  这份提案本身有没有「声称宽于证据」的地方？—— 我有前科，请当作大概率存在
Q3  批准它会引入什么我没写出来的后果？
Q4  在批准之前，还有什么必须先弄清楚？
```

**请给建议与理由，不要给裁定，也不要代 Aaron 签字。**
Critical/High 放最前，并区分「你复现的事实」与「本包自述的内容」。

## 7. 预算（Aaron 的规矩）

```
一波，最多 3 个 workflow，范围互不重叠；本题窄，1 个通常够
默认总预算 3，硬上限 6（超出需 Aaron 明批）
子 workflow 不得再生 workflow
只读起步：发现即报告，**不修复**
```
