# ND1 R3 修订提案复核 —— fresh Sol（**第六次交付**）

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

**REVIEW_ID=rv-c257c88e8228-ccd9f84da420**（gate=`TIER1_DISCRETIONARY`）

> **本文件必须从磁盘读取（read it from disk）。绝对路径：**
> `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_ITEM6_SOL_REVIEW.md`
> **line 115 of it must read** `REVIEWED_SET_UNCHANGED_SINCE=…`。
> 行号或内容对不上 ⇒ 你手里是旧副本，**STOP**。

---

## 0. **前四次的经过 —— 第四次是真正的复审，判 HOLD**

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

**第四次交付被真正审了，判 `HOLD`（传输 PASS），四条 findings 全部经 builder 复现
并已在提案 v2 中处理。** 其中 **HIGH 1 是决定性的**：前一版 R3 声明 `CR1→F3` 却没
把 CR1 加进 F3 的 predecessors，**而提案自己还把 F3 列进「不动」清单**——与
`test_mc_supplement_integration.py:208` 的双向对称不变量直接冲突。已修，
**R3 哈希因此从 `d26cbc3e…` 变为 `12105e98…`**。

**HIGH 2 推翻了我自己的一句结论。** 我曾写「悬空 P3 今天会通过 A_PRECHECK」并把它
当作发现来讲。实测：`(P1,P2,P3)` 的 `live_authorizations = 0`（P3 消费掉了那条
live P2），`_g_live_authorization_unique` 会拒。**完整的 A_PRECHECK 确实会拒，
我那句是假的**，已在提案 §一.2 公开更正。

**第三次交付根本没被审。** builder 执行了一次**另行授权的**隔离件迁移，而那次
迁移必须改的注册表 `ops/OUTCOME_CARRYING_ARTIFACTS.json` **正是第三次交付冻结
送审集里的一件**。改它 ⇒ 送审集当场失效。冻结守卫打红并点名了它。

```
ops/OUTCOME_CARRYING_ARTIFACTS.json: sent 6bcafa9c… to fresh Sol（第三次交付），
now a61c125b…
```

**这不是工件有缺陷，是 builder 让两条各自获授权的工作线撞在了同一个文件上。**

**本次（第四次）交付**：`ops/ND1_PROFILE_RATIFICATION.md` 在冻结集内；提案已按
§7 重写为「R3 canonical 正文 ＋ 其 SHA-256」，并带出两处**升级**（§二.2）；
钉子重新派生于迁移之后。

> **给你的一条提醒**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `path` 字段在
> 迁移中变过——十条隔离路径现在住在 `ops/outcome_quarantine/` 下，**两份
> `EXPOSURE_LEDGER.md`（**OFF-LIMITS**）仍在原地**。**注册表始终是权威，前缀不是**：
> 只按前缀判断会漏掉那两条。

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
REVIEWED_SET_UNCHANGED_SINCE=f4f00a57635f5b3218dd297ed6c0e3d08226d9c1
```

**语义**：该 commit **之后**没有任何 commit 触碰过下表任一送审路径。它不是当前
分支头，也不该等于当前分支头——提交本提示与登记本会推动分支头，而那些提交都不碰
下表路径。**这一条命令是允许的**（范围核对，不是检索）：

```bash
git log --oneline f4f00a57635f5b3218dd297ed6c0e3d08226d9c1..HEAD -- ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md ops/ND1_PROFILE_RATIFICATION.md ops/DECISION_PACKET_N00_AND_ND1.md src/itsf/mc/supplement_contract.py src/itsf/mc/supplement_runner.py src/itsf/mc/supplement_registry.py ops/OUTCOME_CARRYING_ARTIFACTS.json tests/test_mc_supplement_registry.py tests/test_mc_supplement_runner.py tests/test_mc_supplement_integration.py tests/test_registry_boundary.py tests/test_nd1_profile_revision_chain.py
```

**必须为空。** 非空 ⇒ 工件在你手里动了 ⇒ STOP。

| SHA-256 | 字节 | 路径 | 为什么给你 |
|---|---|---|---|
| `731cb2ff060c7e8ad3e3b032220640fdfed57c5d06537515ba722e0d1eb9b7a5` | 29623 | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md` | 被复核的提案（已在 §7 路径上） |
| `cf2c3cb2bdb79b34498c2a7ebc53344c70ef89f0686466a010ce62431541d05e` | 8277 | `ops/ND1_PROFILE_RATIFICATION.md` | 权威基线 —— §8 是 R2 批准记录，§7 是修订路径 |
| `da64a3d68454e6f129287412f200ea51309ee85daad9d9bdb7465d9765e47991` | 86999 | `ops/DECISION_PACKET_N00_AND_ND1.md` | R2 canonical 正文所在；其第 1 行自陈不含已批准值 |
| `c6d5b46f71404044d3e0d2ce770bfda2f4eaa88b3448e397d035b3ec8aff7298` | 20014 | `src/itsf/mc/supplement_contract.py` | EVENTS／TRAPS／FORBIDDEN_EDGES —— 批准后的转录物 |
| `3cb698aef52dcc14ee0987e585ee5b46705a3046e7e53ea42d3db69e001cf746` | 45975 | `src/itsf/mc/supplement_runner.py` | assert_chain_closed:739、A_PRECHECK 门:279、748-749 |
| `e8dd4942645e0d127ff7d388be79ea0fd180a7adf2f0905f60bcf6eaa1f5dfb2` | 65735 | `src/itsf/mc/supplement_registry.py` | 链解析；ChainResolution.closed:245 |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | 2563 | `ops/OUTCOME_CARRYING_ARTIFACTS.json` | 隔离名单权威。**其 path 字段刚因迁移变过**，见 §0 |
| `5737f5141c57fd687a737b9af4b48e97b16c0f6c2b1f1ccd045340d463957eba` | 48061 | `tests/test_mc_supplement_registry.py` | 链解析／trap／forbidden edges |
| `3dc719db3f34e8a60a0f71fb5b1c6f31e8a9bf32f655063b3c2d2aa9f4ab7d13` | 36141 | `tests/test_mc_supplement_runner.py` | assert_chain_closed／A_PRECHECK |
| `f6b0ff3bd0280f814209aee87f970ff24b235e8e3bce1b2a9944f140b5f70a9b` | 27139 | `tests/test_mc_supplement_integration.py` | **逐行比对 R1/R2 并断言差异恰为四行** —— R3 须同形 |
| `4ae818b6699386df3a5d1d27d32765207f1f1ba15a831f13ef2d9ee2267037b8` | 13738 | `tests/test_registry_boundary.py` | C2 边界 |
| `a35269b2c8d4bd119bbf7872808065793bae43f1e79934de7e9f4ade7da4f2f8` | 11817 | `tests/test_nd1_profile_revision_chain.py` | **本轮新建** —— Finding 4 的答复：profile 修订链的机械保障 |
| `5ccd54979d977e2cc975a4a3a875a96cab43fd5cd68b92550dea23511e46217f` | 15688 | `ops/packets/rv-c257c88e8228-ccd9f84da420.packet` | Review Packet v1 本体（**不冻结**，见表下说明） |

**逐个重算并比对。** packet 内的 `GENERATED_BLOCK_SHA256` 亦请重算——
前像是**字段行本身**（不含章节标题与空行），见 `packet.py:1154` 的 `_render`。

> **表有 13 行，但冻结的是前 12 行。最后一行是 packet 本体，它不在冻结集里，
> 也不该在。** packet 由本次交付创建，**必然晚于钉子**——这是固定点问题：
> packet 记录分支头，而提交 packet 会推动分支头，所以它永远无法在「已包含自己」
> 的树上被钉住。
>
> **所以上面那条 `git log` 只列前 12 条，请照抄，不要把 packet 加进去。**
> 把 packet 加进去会得到一条非空结果（创建它的那个 commit），那不是工件被动过。
> **packet 只按哈希核，不按范围核。**
>
> **packet 的 `FILE_MANIFEST=EMPTY` 是刻意的。** `SCOPE_BASE` 取 HEAD——若取迁移之前的 base，那十个刚被移动的隔离件会作为 rename 全部进 manifest，**机械地把隔离路径摆到你面前，没有任何人手打过它们**。送审范围由下表十一个哈希界定，不由 diff 界定。

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
REVIEW_ID=rv-c257c88e8228-ccd9f84da420
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
