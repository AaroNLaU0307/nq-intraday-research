# ND1 R3 修订提案复核 —— fresh Sol（**第三次交付**）

```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=reviewer（profile 修订提案复核，三步之第二步）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；artifact author；writer；gate releaser；上一次判 REJECTED_INCOMPLETE 的那个会话的延续
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A（本件不动 preregistration）
```

**REVIEW_ID=rv-2469d0cff91a-31fed17a5401**（gate=`TIER1_DISCRETIONARY`）

> **本文件必须从磁盘读取（read it from disk）。绝对路径：**
> `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_ITEM6_SOL_REVIEW.md`
> **line 88 of it must read** `REVIEWED_SET_UNCHANGED_SINCE=…`。
> 行号或内容对不上 ⇒ 你手里是旧副本，**STOP**。

---

## 0. **前两次交付都被判 `REJECTED_INCOMPLETE`，两次都判得对**

前一个 fresh Sol 会话的裁定，逐字：

```
VERDICT: REJECTED_INCOMPLETE
REJECTION_ORIGIN_CLASS: BUILDER
REJECTION_CAUSE_CLASS: SOURCE_CONTENT
STRONGEST_OBJECTION: No Review Packet v1 or declared SHA-256 for the proposal
was supplied. ... Per the L6 artifact-transport rule, substantive review must
stop here.
```

**成因全在 builder。** 我把一份裸文件递了过去，没有 packet、没有声明哈希——
而同一条传输规则我在本项目里已经执行过两轮。那一席**在开工前停下是正确的**。

**它自算的提案哈希 `7557AD42…60D5D`，我复算逐字节一致**——文件本身没问题，
缺的是它外面的传输。

**第二次交付补齐了 packet 与冻结集，仍被判 `REJECTED_INCOMPLETE`**，
`ORIGIN=BUILDER`／`CAUSE=SOURCE_CONTENT`，理由逐字：

```
送审材料未提供当前 R2 批准记录的完整、哈希钉定字节，无法建立拟议 R3 修订
所依赖的权威基线。DECISION_PACKET_N00_AND_ND1.md 明示"本文件不含任何已批准值"、
NOTHING_HEREIN_IS_APPROVED=YES ... supplement_contract.py 指向真正的批准记录
ops/ND1_PROFILE_RATIFICATION.md，但该文件不在送审集内。
```

**又对了，而且这一次的后果更大。** 追下去发现：R2 **确实已批准**
（`ND1_PROFILE_RATIFICATION.md` §8，Aaron 逐字「批准 R2」），我只是**引错了出处**；
但**同一份文件的 §7 写死了修订路径**，而**前一版提案没走那条路**——它提的是
「批准后改代码」，可代码是批准之后的**转录**，不是批准的**对象**。

**本次交付**：`ops/ND1_PROFILE_RATIFICATION.md` 已入冻结集；提案已按 §7 重写为
「R3 canonical 正文 ＋ 其 SHA-256」；并带出两处**升级**（§二.2），是照规矩做才
浮出来的。

## 1. 开工之前：你可能被烧掉

本仓已烧掉三个复审席位，**其中两个从未刻意打开过任何文件**（一个死于广域符号
搜索，一个死于单模式定向 grep）。所以：

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不得在本仓做任何检索。** 只打开 §2 表里逐条列出的路径。需要别的字节：
**列出路径，回给工作会话**，由它经 `PULL_PROTOCOL` 供给。

**禁区权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`（12 条）。
每一条都当作关闭。** 点名两条，只为标记禁区、不是指路：

```
OFF-LIMITS   ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md   （DAG／节点台账；旧恢复入口）
OFF-LIMITS   ops/EXPOSURE_LEDGER.md              （研究轴台账）
```

**允许的 outcome-clean 入口：`ops/RECOVERY_ANCHOR.md`。**

## 2. 传输核对（先做，不通过就 STOP）

```
REVIEWED_SET_UNCHANGED_SINCE=025c771b9d9f083df5893c64af68d6b95ee4a55d
```

**语义**：该 commit **之后**没有任何 commit 触碰过下表任一送审路径。它不是当前
分支头，也不该等于当前分支头——提交本提示与登记本会推动分支头，而那些提交都不碰
下表路径。**这一条命令是允许的**（范围核对，不是检索）：

```bash
git log --oneline 025c771b9d9f083df5893c64af68d6b95ee4a55d..HEAD -- ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md ops/ND1_PROFILE_RATIFICATION.md ops/DECISION_PACKET_N00_AND_ND1.md src/itsf/mc/supplement_contract.py src/itsf/mc/supplement_runner.py src/itsf/mc/supplement_registry.py ops/OUTCOME_CARRYING_ARTIFACTS.json tests/test_mc_supplement_registry.py tests/test_mc_supplement_runner.py tests/test_mc_supplement_integration.py tests/test_registry_boundary.py
```

**必须为空。** 非空 ⇒ 工件在你手里动了 ⇒ STOP。

| SHA-256 | 字节 | 路径 | 为什么给你 |
|---|---|---|---|
| `24093464e03f499a59a7f89558156f9e8555d2bb19a1227ae8626c46b1547384` | 19774 | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md` | 被复核的提案（已重写到 §7 路径上） |
| `cf2c3cb2bdb79b34498c2a7ebc53344c70ef89f0686466a010ce62431541d05e` | 8277 | `ops/ND1_PROFILE_RATIFICATION.md` | **上次缺的权威基线** —— §8 是 R2 的批准记录，§7 是修订路径 |
| `da64a3d68454e6f129287412f200ea51309ee85daad9d9bdb7465d9765e47991` | 86999 | `ops/DECISION_PACKET_N00_AND_ND1.md` | R2 canonical 正文所在（1613–1665 行）；其第 1 行自陈不含已批准值 |
| `c6d5b46f71404044d3e0d2ce770bfda2f4eaa88b3448e397d035b3ec8aff7298` | 20014 | `src/itsf/mc/supplement_contract.py` | EVENTS／TRAPS／FORBIDDEN_EDGES —— 批准后的转录物 |
| `3cb698aef52dcc14ee0987e585ee5b46705a3046e7e53ea42d3db69e001cf746` | 45975 | `src/itsf/mc/supplement_runner.py` | assert_chain_closed:739、A_PRECHECK 门:279、748-749 写死提示 |
| `e8dd4942645e0d127ff7d388be79ea0fd180a7adf2f0905f60bcf6eaa1f5dfb2` | 65735 | `src/itsf/mc/supplement_registry.py` | 链解析；ChainResolution.closed:245 |
| `6bcafa9cb7aec7e386cef2311e709c4ebfdafac73db1ce549ed25c91bf0a105b` | 2373 | `ops/OUTCOME_CARRYING_ARTIFACTS.json` | 隔离名单权威 |
| `5737f5141c57fd687a737b9af4b48e97b16c0f6c2b1f1ccd045340d463957eba` | 48061 | `tests/test_mc_supplement_registry.py` | 链解析／trap／forbidden edges |
| `3dc719db3f34e8a60a0f71fb5b1c6f31e8a9bf32f655063b3c2d2aa9f4ab7d13` | 36141 | `tests/test_mc_supplement_runner.py` | assert_chain_closed／A_PRECHECK |
| `f6b0ff3bd0280f814209aee87f970ff24b235e8e3bce1b2a9944f140b5f70a9b` | 27139 | `tests/test_mc_supplement_integration.py` | **逐行比对 R1/R2 并断言差异恰为四行** —— R3 须同形 |
| `4ae818b6699386df3a5d1d27d32765207f1f1ba15a831f13ef2d9ee2267037b8` | 13738 | `tests/test_registry_boundary.py` | C2 边界 |
| `3f03814fa97b4e7b30ada72397a2ccc6d804f015910af57df20b5f61e4b6e313` | 16525 | `ops/packets/rv-2469d0cff91a-31fed17a5401.packet` | Review Packet v1 本体（**不冻结**，见表下说明） |

**逐个重算并比对。** packet 内的 `GENERATED_BLOCK_SHA256` 亦请重算——
前像是**字段行本身**（不含章节标题与空行），见 `packet.py:1154` 的 `_render`。

> **表有 12 行，但冻结的是前 11 行。最后一行是 packet 本体，它不在冻结集里，
> 也不该在。** packet 由本次交付创建，**必然晚于钉子**——这是固定点问题：
> packet 记录分支头，而提交 packet 会推动分支头，所以它永远无法在「已包含自己」
> 的树上被钉住。
>
> **所以上面那条 `git log` 只列前 11 条，请照抄，不要把 packet 加进去。**
> 把 packet 加进去会得到一条非空结果（创建它的那个 commit），那不是工件被动过。
> **packet 只按哈希核，不按范围核。**

## 3. 你要复核什么

**读 `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md` 全文。** 它含：两个缺口
（词表缺口 ＋ 接线缺口）、提议的 `CR1` 事件规格、trap 与 forbidden-edge 改动、
`ABANDONED` 门谓词、租约纪律（第 8 项）、建造义务、以及**一处 builder 的自我更正**。

**本提示不复述提案**——复述会产生两份互相漂移的副本。

### 请优先看 §四.A

**那一节的第一版是错的，我在动手实施前实测推翻了它，更正逐字保留在原处。**
错的版本说「把 `assert_chain_closed` 接到 A_PRECHECK 上，最小改动」。实测：

```
('P1','P2')  -> 拒绝: chain_not_closed: P2
```

而 `('P1','P2')` 正是任何合法运行**开跑之前**的状态——接上去会拒掉每一次正当运行。

**请把 §四.A 当作最可能还藏着错的一节。** 其中 `P4` 与 `F2` 两栏我明说定不了。

## 4. 三条你不能替任何人做的事

1. **PASS 不修改任何已批准工件。** 本件是三步之第二步；`EVENTS` 表在 Aaron
   ratify 之前一字不改。
2. **不要替 Aaron 决定**。凡你认为该由所有者定的，写进 `UNRESOLVED_FOR_AARON`。
3. **只读。** 不改文件、不打补丁、不追加任何 registry／台账事件、不签发授权、
   不在 `C:\Users\Aaron\quant-data\` 下创建目录、不读真实数据、不执行任何 run。

## 5. 返回格式

```
ITEM=6+8
REVIEW_ID=rv-2469d0cff91a-31fed17a5401
TRANSPORT_PRECHECK=PASS|STOP（逐个哈希 ＋ 上面那条 git log 为空 ＋ 重算 packet 生成块）
VERDICT=PASS | HOLD | REJECTED_INCOMPLETE
STRONGEST_OBJECTION=<即使 PASS 也要写出最强的反对>
FINDINGS=<逐条，带文件与符号>
逐一作答：
  ① CR1 规格（字段／actor／predecessors／successors／terminal／incident_required）
  ② CR1 该不该进 NON_TERMINAL_TRAPS（builder 的推断，非裁定）
  ③ 两条 FORBIDDEN_EDGES 是否必要
  ④ ABANDONED 谓词，**含 P4 与 F2 两栏**（builder 明说定不了）
  ⑤ predecessors=("P3",) 是否过窄
  ⑥ 第 8 项租约纪律（不改 profile，只约束未来设计）
UNRESOLVED_FOR_AARON=<你与 builder 都不得替他决定的部分>
INDEPENDENCE_STATEMENT=<按维度：会话、工件作者身份、模型多样性、经验独立性、设计贡献>
SEAT_STATUS=BLIND|EXPOSED（读过隔离件或检索命中隔离内容就是 EXPOSED，如实报）
```

`SEAT_STATUS` 请务必如实——**烧掉席位不消耗研究自由度**，两条轴分开记账
（`ops/REVIEWER_EXPOSURE_LOG.md` 记席位轴，可读）。瞒报才是不可逆损失。
