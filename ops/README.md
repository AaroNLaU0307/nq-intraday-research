# `ops/` 索引

**找要贴的东西？→ [`NEXT_HANDOFF.md`](NEXT_HANDOFF.md)。那个文件名永远不变。**

本目录有 50+ 份治理记录，**其中 47 份被别处引用**（22 份被代码／测试／状态文件
按路径硬引用）。**所以这里不搬家，只建索引**——移动一份被 `src/` 引用的文件会
直接弄断生产代码。哪些不能动，见最后一节。

---

## 0. QROS-CF 现势文件（2026-09-07 起；Aaron OD-CF-1 采纳，ITSF 专用）

| 文件 | 是什么 |
|---|---|
| [`RESEARCH_STATE.md`](RESEARCH_STATE.md) | **ITSF 阶段权威**（OD-CF-3）：十个问题一页答完；outcome-clean，永不隔离 |
| [`BACKLOG.md`](BACKLOG.md) | **唯一的 blocker 集（§1）＋非阻断 backlog（§2）＋已关闭项（§3）**；其余旧待办清单只剩指针横幅 |
| `tests/tiers.py`（仓内） | **测试分层图**：GOVERNANCE_FILES（C 层，不进运行门）、VALIDITY_FILES（A 层）；未列出的默认 B 层进门；本文件本身在受管执行身份内 |
| [`REVIEWER_CONTRACT.md`](REVIEWER_CONTRACT.md) | 复审契约：PASS / PASS_WITH_BACKLOG / HOLD，两轮预算，两种验证义务，污染协议（OD-CF-7） |
| [`VERIFICATION_BRIEF_TEMPLATE.md`](templates/VERIFICATION_BRIEF_TEMPLATE.md) | 验证简报模板（一页；匹配规则在派发前写死；pre-freeze / post-freeze 两集） |
| [`ATTESTATION_HEADER_TEMPLATE.md`](templates/ATTESTATION_HEADER_TEMPLATE.md) | 验证者 attestation 头部模板（独立性按维度陈述；冻结结果哈希） |
| [`DISPATCH_TEMPLATE.md`](templates/DISPATCH_TEMPLATE.md) | 派发模板（路由头＋目录／简报／规格哈希＋读规则） |
| [`QROS_CF_WINDOW_LOG_2026-09-07.md`](QROS_CF_WINDOW_LOG_2026-09-07.md) | 实施窗口（DEC-0006，I1–I7）的**唯一运行日志**：T-F17 估算、OD-CF-4 证明、各阶段结果 |
| [`ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md`](ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md) | **GPT-6 Astra P2 门禁复审 HOLD 的持久转录**（六条 BLOCKING F01–F06 + 两条非阻断 F07/F08）。原报告仅经聊天传递、从未落盘，故本文件即 F01–F06 的权威定义；与 `qros-cf-redesign/ASTRA_CHALLENGE_REPORT_2026-09-07_TRANSCRIPTION.md`（提案 v1 复审，编号无关）**不是同一份** |
| [`REVIEW_PACKET_QROS_CF_F01_F06_REREVIEW_2026-09-07.md`](REVIEW_PACKET_QROS_CF_F01_F06_REREVIEW_2026-09-07.md) | F01–F06 定向复审送审包（delivery）：受审集逐字节 sha256、修复提交 `f461f09`、退出判据；包自身的 sha256 由 `ARTIFACTS_UNDER_REVIEW.json` 承载（送审文档不能自钉） |
| [`REVIEW_PACKET_QROS_CF_F01_F06_FINAL_CERT_2026-09-07.md`](REVIEW_PACKET_QROS_CF_F01_F06_FINAL_CERT_2026-09-07.md) | F01/F02/F03/F05/F06 **最终认证**送审包（delivery，第 3 轮，Aaron 授权的业主例外——合同两轮预算已用尽）：第二轮修复提交 `0d15a62`、21 件受审集逐字节 sha256、F04 保持 CLOSED、F07/F08 非阻断。**§4 是 Aaron 点名的四个方向，本席位自测其中三条答案为「否」并写在包内**；包自身的 sha256 由 `ARTIFACTS_UNDER_REVIEW.json` 承载（送审文档不能自钉） |
| [`REVIEW_PACKET_QROS_CF_F06_OWNER_SEMANTICS_CLOSURE_2026-09-07.md`](REVIEW_PACKET_QROS_CF_F06_OWNER_SEMANTICS_CLOSURE_2026-09-07.md) | F06-OWNER-SEMANTICS 修复的**后续结案认证**包（delivery）。父谱系 `QROS-CF-F01-F06-FINAL-CERT-001` 已以 **HOLD** 完成并作为历史证据保留（**未改写为 PASS**）；本件另起 review id。结案范围：修复后的 F06 owner 语义 + 因父 HOLD 而搁置的 F01 / F02 / SANCTIONED_REAL_RUN_ENTRY / FLAG_PATH_BYPASS / F03 / F05（F04 仅保全） |
| [`DECISIONS.md`](DECISIONS.md) | **owner 决定与复审裁决的 append-only 台账**（QROS-CF v2 §10.1）。OD-CF-1..7 逐字转录在此；此后不再新建 OWNER_DECISIONS_* / RULING_* / SEAT_RESULT_* 文种 |

## 1. 现势入口（从这里开始）

| 文件 | 是什么 |
|---|---|
| [`RECOVERY_ANCHOR.md`](RECOVERY_ANCHOR.md) | **任何会话从这里开始**（D-2 拆锚，2026-08-26）。outcome-clean，永不隔离，blind 席位可安全读 |
| [`NEXT_HANDOFF.md`](NEXT_HANDOFF.md) | **下一份要交出去的东西**，固定文件名；同时是复审禁区清单的常驻载体 |
| `MC_TO_STRATEGY_MASTER_PLAN.md` | **OFF-LIMITS（outcome-carrying，不得打开）** · DAG、节点状态、租约、停止点的**权威**，§ 编号最高者为准。**恢复入口已于 §16 迁至 `RECOVERY_ANCHOR.md`**。**⚠ OFF-LIMITS —— outcome-carrying，blind 席位不得读**（此处刻意不给链接） |
| [`TRIAL_REGISTRY.md`](TRIAL_REGISTRY.md) | 事件真相源，append-only。S0／supplement／MC 三个生命周期共用一份 |
| [`DECISION_PACKET_REMAINING_FABLE.md`](DECISION_PACKET_REMAINING_FABLE.md) | **现在挂着的交付**——其余十项决定交 Fable，`dec-remaining-2026-08-26`。每项先答 `DELEGABLE`：Fable 上轮自己把多数划为 Aaron-only |
| [`PROMPT_ITEM6_SOL_REVIEW.md`](PROMPT_ITEM6_SOL_REVIEW.md) | **现在挂着的交付** —— ND1 R3 提案复核第二次交付，`rv-6cd8abb41a43-1ddf0617d52e`。第一次因缺 packet／哈希被判 REJECTED_INCOMPLETE（origin=BUILDER） |
| [`ARTIFACTS_UNDER_REVIEW.json`](ARTIFACTS_UNDER_REVIEW.json) | 谁手上正拿着什么；空表是常态 |
| [`OUTCOME_CARRYING_ARTIFACTS.json`](OUTCOME_CARRYING_ARTIFACTS.json) | **隔离名单**。给复审席位之前必读 |

## 2. 现势未决

| 文件 | 是什么 |
|---|---|
| [`RULING_SOL_C_BUILD_2_R5_HOLD_2026-08-30.md`](RULING_SOL_C_BUILD_2_R5_HOLD_2026-08-30.md) | **第 5 轮 HOLD，`SPECIFICATION_VERDICT=FAIL`＋`ENGINEERING_QUALITY_VERDICT=FAIL`**。三个 HIGH 各自 10/10 全绿。**它让我看见的不是四个缺陷，是五轮共同的错**：我一直用 AST 检查器去证明一个**运行期属性**，而满足任何形状却违反语义的表达式集合是无穷的。**换了仪器**：`test_resolve_partial_observed_behaviour.py` 包住真实文件调用、驱动真实函数、对观测到的动作断言 —— 三个 HIGH 各被点名抓住 |
| [`RULING_SOL_C_BUILD_2_R6_HOLD_2026-08-30.md`](RULING_SOL_C_BUILD_2_R6_HOLD_2026-08-30.md) | **第 6 轮 HOLD，两个 HIGH 全部复现**。观测器只包了四个名字（`_saved` 从未被填充），`builtins.open` / `os.open` / `shutil.*` 全部不可见 —— **而提示词 §4 写着我已经修了它，那句话在字节里是假的**。第二条：「每个已声明出口都触达」的 `reached` 是**手打集合**，不是执行轨迹。**根因是同一个错下沉一层**：R3–R5 枚举语法形状，R6 枚举拦截点，两者的违规集合都无穷。闭合方式 = **不观测操作，观测状态**（目录逐字节快照 diff，对机制闭合） |
| [`PROMPT_C_BUILD_2_WORDING_SOL_ROUND7.md`](PROMPT_C_BUILD_2_WORDING_SOL_ROUND7.md) | 第 7 轮送审包。**仪器换的是种类不是紧度**：不观测操作，观测状态（目录逐字节快照 diff，digest 多重集包含）。**新纪律**：每条声称旁挂一条可跑的命令，没命令的标 `[意见]` —— 因为第 6 轮 §4 有一句「已修」在字节里是假的。该纪律在发行前就抓到了我自己写错的一条命令 |
| [`RULING_SOL_C_BUILD_2_R7_HOLD_2026-08-30.md`](RULING_SOL_C_BUILD_2_R7_HOLD_2026-08-30.md) | **第 7 轮 HOLD，三个 HIGH 全部复现全部闭合**。① 出口覆盖仍是名字级 —— **`DECLARED_EXITS` 正上方的注释写着「A list, never a set」，我读过它、在它下面写了文件、然后照样折叠**；现在路径身份是(名字, 出口行, helper raise 行)，两侧导出，12/12 唯一。② NTFS 备用数据流不在快照里 —— 走 `FindFirstStreamW` **枚举而非收窄声称**。③ **`out_dir` 声称被证伪，是生产缺陷**：`../escaped.json` 直接写到父目录，`_require_plain_name` 已补，快照根上移一层。另记 5 条 claim/command 不一致（含「23/23」实为 22）与**检索边界违例的成因是我**——我要求席位守一条我自己的测试代码违反的边界 |
| [`PROMPT_C_BUILD_2_WORDING_SOL_ROUND8.md`](PROMPT_C_BUILD_2_WORDING_SOL_ROUND8.md) | **第 8 轮 = 上限轮**（Aaron OD-1）。残留一律标 `ACCEPTED_BY_CAP` —— **到期是停止迭代，不是残留已闭合**。§4 只要能改变结论的发现，§5 请他检查我有没有把真残留写窄 |
| [`OFF_LIMITS_COMPANION_R8.md`](OFF_LIMITS_COMPANION_R8.md) | 第 8 轮随包禁区清单。**更正了第 7 轮那次边界违例**：逐条列出内部会枚举 `ops/` 的九个治理测试，写明跑它们不算违例 —— 边界约束的是席位主动发起的检索，不是被审代码自己的行为 |
| [`RULING_SOL_C_BUILD_2_R8_HOLD_2026-08-30.md`](RULING_SOL_C_BUILD_2_R8_HOLD_2026-08-30.md) | **上限轮 HOLD。同一个折叠第三次，只是又小一号**：R7 的 `(名字, 出口行, helper raise 行)` 标识的是**出口位点**不是路径，两条汇合的控制流共用一个身份，删掉一条场景仍全绿。**根因在 walker**——`ast.If` 之后的语句只用「进 if 之前」的 guards 走一次。**选择修而不是只收窄措辞**：walker 在落空分支处分叉剩余语句，12 条声明变 17 条（无新代码路径），身份改为**路径行集合＋唯一匹配**，席位的原案变异被点名。另：席位更正了我一条**把弱点写得比事实宽**的归因（提前绑定会让因果测试变红，非静默绕过），实测确认他对。**修复未经任何独立席位复审 —— 这一条必须写给 Aaron** |
| [`DELIVERY_C_BUILD_2_WORDING_AT_CAP_2026-08-30.md`](DELIVERY_C_BUILD_2_WORDING_AT_CAP_2026-08-30.md) | **上限交付，等 Aaron 一句话**。§0 是唯一需要他决定的事：**第 8 轮之后的 walker 修复没有被任何独立席位看过**——变异证红 ≠ 被独立复审过。甲收下／**乙为修复解开一轮（我推荐）**／丙推迟。另附八轮结论改变项、`ACCEPTED_BY_CAP` 残留表、以及我自己八轮错误的形状归类 |
| [`OFF_LIMITS_COMPANION_R7.md`](OFF_LIMITS_COMPANION_R7.md) | 第 7 轮随包禁区清单（D-2：Review Packet 不得自带禁区清单，须由随包件承载并同行）|
| [`OWNER_DECISIONS_2026-08-30.md`](OWNER_DECISIONS_2026-08-30.md) | **OD-1：Aaron 裁定措辞复审上限 8 轮**，到 8 轮按当时最好的方式发出，不开第 9 轮。上限由 `tests/test_the_review_round_cap_is_respected.py` **从本文件读出**而非写死；并强制第 8 轮把仍站着的残留标 `ACCEPTED_BY_CAP` 而非 `ACCEPTED` —— **到期是停止迭代，不是残留已闭合** |
| [`MIGRATION_ROUTE_A_COMPLETED_2026-08-31.md`](MIGRATION_ROUTE_A_COMPLETED_2026-08-31.md) | **迁移 Route A S0–S7 完成，S7 PASS**。O0/O1/N0/N1 与 SHA0 全在案，F4 双向核对通过。**计划外发现两件**：`core.autocrlf` 会在将来某次 clone 静默改写字节（已加 `.gitattributes`）；**单一构造守卫从不走 `tests/`**，于是三处读墓碑的测试**平凡通过**——绿着，守的东西已经不在了。R4 的证伪器已真做一次冷读，**未触发** | 
| [`R4_PROPOSAL_CR1_REPOSITORY_ANCHORING_2026-08-31.md`](R4_PROPOSAL_CR1_REPOSITORY_ANCHORING_2026-08-31.md) | **R4 提案，待 Sol 复审 → Aaron 批**。仓锚定改两处且只有两处；**锚点是 commit 对不是路径**（路径是机器局部的，移动不留记录）。起草时看清一件原文没给的信息：**「git history」迁移后是两段，分界是 N1**——N1 之前的 CR1 行前像在框架仓，之后的在 registry 仓，两段都没被重写。证伪器已真跑一次冷读，**未触发**。§4 有一个**我判断对自己有利、因此请 Sol 独立复核**的问题 |
| [`PROMPT_R4_CR1_ANCHORING_SOL.md`](PROMPT_R4_CR1_ANCHORING_SOL.md) | R4 送审包（`r4-cr1-anchoring`，**不受措辞八轮上限约束**，那条绑的是另一族提示词）。§1 要求 Sol **自己重跑证伪器**而不是采信我；随包件为此**特许他读 registry 仓与见证根**——不给读就只能采信我，而那正是本次复审要避免的。§5 是我判给自己的一个「澄清 vs 新判据」问题，明写它对我有利、因此不该由我定 |
| [`OFF_LIMITS_COMPANION_R4.md`](OFF_LIMITS_COMPANION_R4.md) | R4 随包禁区清单。含**本轮特许**：registry 仓与见证根可读（判据就是跨仓冷读），并写明 registry 不是 outcome-carrying 件——**若在里面读到像绩效的东西，那是事故** |
| [`RULING_SOL_R4_HOLD_2026-08-31.md`](RULING_SOL_R4_HOLD_2026-08-31.md) | **R4 HOLD，四条阻断全部复现**。① **我把「发现」和「验证」混为一谈**——commit hash 只能在已定位的 object DB 里确认身份，**是路径在做发现**，而我用一句加粗否定句否掉了真正承重的那一半。② 我判给自己的「澄清」判错了：是**仓选择判据**，且「INTACT-looking」用词也错（墓碑 0 事件 vs 见证 17，按未改判据它**并不 INTACT**）。③ **提案漏了原块 8 个字段，根本不构成可哈希、可批准的块**。④ 分界该是 strictly after N1。另：**为防陈旧数字而造的守卫自己算错了**（parametrize 数成 1），已改为失败关闭 |
| [`R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md`](R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md) | **R4 v2，待复审**。四条阻断逐条处理：锚点分成**发现 vs 验证**并把「仓移动即找不到」留成明写残留（不解决它）；那句话按**仓选择判据**重写并删掉错用词；**完整块 18 行、机械生成、15/17 逐字保留**；分界改 strictly after N1。新哈希 `6e62fd2d…` 由复算出 `c251335f…` 的同一段代码算出，并从成文文件里回哈希核对。§4 把「收窄主张算不算扩权」这个**对我有利的判断**原样交给下一席位 |
| [`PROMPT_R4_V2_FORK_SOL.md`](PROMPT_R4_V2_FORK_SOL.md) | **单问复审包**（`r4-v2-fork`，OD-6）。只裁一件事：**收窄主张算不算在 R4 内自行扩权**。v1 四条阻断里的另外三条已由常驻守卫机械核对，请核对而非重推。包里逐字写着**范围窄是预算决定不是封口**，并留 `OUT_OF_SCOPE_FINDINGS` 字段——一份「只问一个问题」的包若被用来把审查席引开，它就在做本项目反复要避免的事 |
| [`OFF_LIMITS_COMPANION_R4V2.md`](OFF_LIMITS_COMPANION_R4V2.md) | 单问复审的随包禁区清单。仍特许读 registry 仓与见证根——那个分岔的核心就是「冷读者能不能只凭字节找到并确认那个仓」，不给读就只能采信 builder |
| [`RULING_SOL_R4_FORK_2026-08-31.md`](RULING_SOL_R4_FORK_2026-08-31.md) | **分岔裁「甲」**：收窄主张不算扩权。理由的形状我自己没想清楚——**「用一条已被裁定存在的边」和「另立一条新边」不是一回事**。席位还主动给出**反对自己裁断的最强论点**（「桥仍只引用 S4」是不精确简写，发现步骤实际读了墓碑），并说明为何不足以改判。两条范围外发现均已修：登记册对 delivery 说了一句关于它自己的假话；一个未关闭句柄。**裁断不批准 v2、不释放冻结令** |
| [`APPROVAL_R4_CR1_GRAMMAR_2026-08-31.md`](APPROVAL_R4_CR1_GRAMMAR_2026-08-31.md) | **R4 已批准，生效**。`6e62fd2d…` 取代 `c251335f…`，作废理由「所指重绑定，判据未变」——**而「判据未变」是机械可验的**（15/17 行逐字保留，守卫逐行比对）。记录前复测四项，含**被作废的哈希仍能由同一口径复算出来**——算不出就说明「作废旧值换新值」这件事本身无从成立。**冻结令已解除，且解除不等于追加**：CR1 行数实测仍为 0，生产入口仍拒绝。旧值所在的两份历史记录**一个字节都不改** |
| [`P1_DRAFT_MC_DS_S001_2026-08-31.md`](P1_DRAFT_MC_DS_S001_2026-08-31.md) | **P1 草案，等 Aaron 一句「追加它」**（registry 追加在 builder 禁止清单内）。开篇就摆 08-29 的实测结论：**追加 P1 改变的门数是 0**，五道门的翻转全部来自 P2。**序号与 commit 不预填**——两者在追加那一刻才为真。并预先点出一个顺序陷阱：**P2 之后、真跑之前不能有任何提交**，否则 HEAD 移开授权的 commit |
| [`P1_APPENDED_MC_DS_S001_2026-08-31.md`](P1_APPENDED_MC_DS_S001_2026-08-31.md) | **P1 已追加**（registry 仓 `e53234e`，序号 14）。**实测确认它解开了零道门**——拒绝点与拒绝信息一字未变。**第一次尝试是坏的**：我把决策包的 `NOTE_SHAPE` 散文当成 note 字面内容照抄，而真实文法是 `;` 分隔的 `key: value`——链整体拒绝。坏行未进历史已还原，**但它的见证保留**（见证根 append-only，它记的是确实短暂存在过的状态）。**教训是顺序**：先追加后解析，第二次才改成先在内存里试通过再碰文件 |
| [`P2_PREPARATION_MC_DS_S001_2026-08-31.md`](P2_PREPARATION_MC_DS_S001_2026-08-31.md) | **P2 准备件，待 Aaron**。三件已实测：`output_root` 是 `itsf-runs` **而不是 supplements 那一层**（后者是 runner 自己拼的——**我原本会填错**，因为被授权过的恰是 supplements）；运行目录由写入方在落盘时建，不需额外目录授权；以及**签 P2 到真跑之间不得有任何提交**。**P2 是今天第一个真正不可逆的步骤** —— 迁移可回滚、R4 是文档、P1 解开零道门 |
| [`P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md`](P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md) | **P2 已无痕撤回；研究自由度未消耗**。追加后实测发现拒绝信息变了，但不是缺授权——**`run_supplement_production` 的签名是 `NoReturn`，这个 build 没有执行路径**。**我一路把 P2 说成最后一道闸，那是错报**，而入口函数的签名就写着答案。由此暴露一个顺序死结：**授权绑 commit，而让运行成为可能就要提交代码、HEAD 移动、授权失效**——正确顺序是先建执行路径再授权，我做反了 |
| [`AMENDMENT_P2_TO_P2S_PRESTART_2026-09-05.md`](AMENDMENT_P2_TO_P2S_PRESTART_2026-09-05.md) | **§D.3.2 已批准修订：pre-start 重授权直边 `P2 -> P2S`**。缺口：commit 可以在**任何尝试之前**就过期，而 `F1` 描述不了——它要 `stage`/`gate_name`（闭枚举）和一个执行根本不会用的 `attempts_dir`。**决定性证据：它声称镜像的 S0 先例（真实登记册 6→7、9→10 行）两次都是直边，中间没有 failure 行**。六个条件里四个本来就在执行；`p2s_without_preceding_f1` 保留，只对不满足本例外的情形继续拒绝。内含一条如实记录的测试缺陷：我写的一条测试**通过的理由和它声称的不是同一个** |
| [`P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md`](P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md) | **独立 verifier 的 P5 证明，判 FAIL**。它的 sha256 `cc733337…` **写在登记册第 22 行（F2v）的 detail 里**，所以这份文件是链上引用的权威证据。结论：2842 天里 **8 天**的分层标签与 S0-T001 当初所用不同，headline draw 在封存标签下 0/1008 复现、还原那 8 个标签后 1008/1008。**它推翻了我作为 builder 封存的产物** |
| [`F2V_CANDIDATE_MC_DS_S001_2026-09-06.md`](F2V_CANDIDATE_MC_DS_S001_2026-09-06.md) | verifier 给出的 F2v 候选行与内存预检，已被真实的第 22 行取代。保留为过程证据：**无 sha256 绑定**，不入仓也不会破坏可验证性 |
| [`P2S_AND_REAUTH_MC_DS_S001_2026-09-05.md`](P2S_AND_REAUTH_MC_DS_S001_2026-09-05.md) | **P2S(16) + 重授权 P2(17) 已追加，N09 首跑**。P2→P2S 直边的第一次实际使用——**没有制造 F1，也没有建 attempts_dir**。两份见证都是**追加后立即**写的；追加前先断言字节等于上一步验证过的状态，写完断言是纯追加；中间态（0 条 live）**事先在内存里验过合法**。N09 停在 `bundle_manifest_coverage`，**零副作用**（未建目录、未读 Development 数据）——两个已批准模块对 `REGISTRY_AFTER_RUN_STARTED.json` 的分类矛盾。修好后**越过它，停在下一条同族的**：`record_schema_violation`，封存记录用 `entry_timestamp/exit_timestamp`，`TradePathRecord` 用 `entry_ts/exit_ts`（19 vs 19，17 个相同）。第二条未碰 |
| [`P2_APPENDED_MC_DS_S001_2026-09-05.md`](P2_APPENDED_MC_DS_S001_2026-09-05.md) | **第二条 P2 已追加**（registry 仓 `a875740`，序号 15 第二次被用）。实测它翻了 `live_authorization_unique`，**13 道门只剩 `authorized_commit_matches_head` 在拒**。两件如实记录：① **见证是补记的**——只能建「从现在起」的防回滚基线，证不了追加当时；② **又踩了 P1 记录 §5 已经点名的顺序陷阱**（P2 之后又提交，HEAD 移走，授权失效）。并记下实测的重授权约束：直接再签一条会变 2 live 被拒，合法边是 `P2 -> F1 -> P2S -> P2` |
| [`P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md`](P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md) | **P5 独立验证 attestation（fresh fable verifier，2026-09-06）**。blind-first：所有独立重算先落盘再读 P4。P4 七项 claim 全部复现；`rederivation_reproduced=YES`；**`headline_replay_identity=FAIL`**——2842 日中 8 日的 stratum 与 S0-T001 实际分层不同（5 日 vol T2/T3、3 日 event FOMC/none，后者是 IR-13 非计划 FOMC 日），把这 8 个标签还原后 3024 条 headline 行与全部 K=200 digest 逐字节复现。结论走 F2v。sha256 `cc733337…`，字节不得改动 |
| [`F2V_CANDIDATE_MC_DS_S001_2026-09-06.md`](F2V_CANDIDATE_MC_DS_S001_2026-09-06.md) | seq 22 `SUPPLEMENT_VERIFICATION_FAILED` 候选行与 memory-only preflight 记录（已由 Aaron 签署追加，registry 仓 `78a2586c`，见证 `WITNESS_F2V_APPENDED_2026-09-05.json`）。actor `fresh fable verifier` 的机械推导见验证席位报告 |
| [`OWNER_DECISIONS_2026-09-06.md`](OWNER_DECISIONS_2026-09-06.md) | **OD-1：Aaron 裁定 MC-DS-S001 F3 retirement**——supersedes seq 22、superseded_commit `3df1656f…`、reason `POST_START_FAILURE`、incident `INC-96578a2997e9`、successor `MC-DS-S002`（同日修正，原 NONE——parser 实测 NONE 会永久堵死 T1 lineage；S002 由 F3 预绑定为唯一 successor，后续须经 T1，禁止 fresh P1 绕过）；ID_REUSE=FORBIDDEN；本步不执行 T1、不改 S002 代码、不动 sealed/archive/attestation。seq 23 F3 行的 actor 引用本文件 OD-1 |
| [`F3_CANDIDATE_MC_DS_S001_2026-09-06.md`](F3_CANDIDATE_MC_DS_S001_2026-09-06.md) | seq 23 `SUPPLEMENT_SUPERSEDED` 候选行（memory-only preflight，0 problems）。**未追加**，等 Aaron 最终签署；commit 列须为追加时 framework HEAD |
| [`N04_EXECUTION_PATH_CHECKPOINT_1_2026-08-31.md`](N04_EXECUTION_PATH_CHECKPOINT_1_2026-08-31.md) | **第一个分段检查点：18 道门的实测位置**。A_PRECHECK 8/13 通过、B_DERIVE 4/5 通过（**对生产形态输入**），**没有一道因为「代码没建好」而拒绝**——全部在等 P2 携带的那个 commit。设计上「装配接收、从不生产」，该声称按源码/按签名/按行为证了三遍。另记三个「静默匹配不到」的错，其中一个差点让我报出「有冻结文件被改动」 |
| [`N04_EXECUTION_PATH_CHECKPOINT_2_2026-09-01.md`](N04_EXECUTION_PATH_CHECKPOINT_2_2026-09-01.md) | **第二个分段检查点：23 道门的完整实测表**。15 PASS / 6 等 P2 / **2 无条件拒绝**。本段的实质发现：C_BUILD 那五道不是同一种东西——三道分类器挂上 outcome 即通过，`seal_staging_partial` 与 `archive_policy_a` 直接 `_fail`、**根本不读 outcome**，任何输入都不能让它们通过。用探雷器对象把两组门**测**开，而不是读注释。顺手订正了一处生产字节里「写时为真、读时已假」的拒绝消息，并记下 `write_text` 在 Windows 上静默改写整个文件的坑 |
| [`N04_EXECUTION_PATH_CHECKPOINT_3_2026-09-02.md`](N04_EXECUTION_PATH_CHECKPOINT_3_2026-09-02.md) | **第三个分段检查点：机制全都在，缺的是编排**。订正检查点 2 §6——① seal/staging 机制早已完整（`seal_supplement_production` 内部已调 `resolve_partial`），缺的只是分类包装 `run_c_build_2`，已建并接线；② `archive_policy_a` **不该接线**，裁定给 Router B，而归档、Router B、C_BUILD_3 判据三者都已存在。另记一个结构问题：`run_stage_gates` 按 stage 跑必然撞上那道恒拒的门，**编排器必须按 checkpoint 取门**；以及一条承重变了的残留（第 8 轮后的修复从未独立复审） |
| [`N04_EXECUTION_PATH_CHECKPOINT_4_2026-09-02.md`](N04_EXECUTION_PATH_CHECKPOINT_4_2026-09-02.md) | **第四个分段检查点：链路跑通到 P4**。三个时刻组合完成（`supplement_chain`），在真封存器＋真临时目录上到达 `P4`；新增 `gates_at`，分区断言为精确 3+1+1，未知 checkpoint 抛异常而非返回空元组。`run_supplement_production` 那句「carries no execution path」**已为假并订正**——真正的缺口是 dataset 侧输入（要读 Development 数据，被门挡着），不是缺路径。另：组合暴露出 `_declared_digest` 不认真实 `SupplementProduct`（docstring 比实现宽＋覆盖缺口），已修并补真工厂测试；**并留下一条欠 Aaron 的裁定**——`archived_bytes_deleted` 无既有终态，链路具名拒绝而不发明 |
| [`RULING_SOL_C_BUILD_2_R4_HOLD_2026-08-30.md`](RULING_SOL_C_BUILD_2_R4_HOLD_2026-08-30.md) | **第 4 轮 HOLD，四条全部成立、全部复现**。两个 HIGH 在合同 12/12 全绿下通过：① 同形路径被 set 去重＋溯源是函数级不是路径级；② 删除动作作为**值**被调用，名字黑名单看不见。MEDIUM：64-hex 只认小写；**`REVIEWED_SET_UNCHANGED_SINCE` 是错误自报**。**根因我上一轮自己列出过却没去修** —— 列出弱点不等于处理弱点。已改为路径敏感有序列表＋封闭调用世界＋range 声称机械核实 |
| [`FINDINGS_SOL_R3_REPRODUCED_2026-08-30.md`](FINDINGS_SOL_R3_REPRODUCED_2026-08-30.md) | **两条 HOLD 发现的复现证据**。含一件比结论更值得记的事：**第一次复现是错的**（全红），因为我的变异守在测试会触发的条件上；Sol 的守在测试从不触发的条件上。停在第一次就会写下「无法复现」而缺陷仍在 |
| [`DECISION_PACKET_FOUR_OPEN_2026-08-29.md`](DECISION_PACKET_FOUR_OPEN_2026-08-29.md) | **四件待裁的决裁包**（已由 Fable 顾问级答复，见 `RULING_FABLE_FOUR_OPEN_2026-08-30.md`）。**第 2 件已撤回** —— 它是一件 owner 已裁事项，我当未决送出去了 |
| [`RULING_SOL_C_BUILD_2_R3_HOLD_2026-08-30.md`](RULING_SOL_C_BUILD_2_R3_HOLD_2026-08-30.md) | **第 3 轮 fresh Sol 判 HOLD，逐字转录**。HIGH：C_BUILD_2 路径覆盖不是失败闭合（新增路径 59/59 仍绿）；MEDIUM：批准守卫的探测域是单文件＋字段正则却声称「每份批准」。**两条均已复现在先、修复在后**（`test_resolve_partial_path_contract.py` ＋ 探测域改为哈希）。`UNRESOLVED_FOR_AARON`：`SIGNABLE_RATIFICATION_ROUTES=1` 要不要成为权威不变量 |
| [`RULING_FABLE_FOUR_OPEN_2026-08-30.md`](RULING_FABLE_FOUR_OPEN_2026-08-30.md) | **Fable 四件裁定，顾问级**（builder spawn 的子代理，对 builder 不独立）。第 1 件用数据流推翻了我的 BD-4；**第 2 件抓到我把一件 owner 已裁事项当未决送裁**；第 3 件采纳＋两条硬化；第 4 件正确让渡给 Aaron |
| [`HOW_TO_SEND_THE_SOL_ROUND3_REVIEW.md`](HOW_TO_SEND_THE_SOL_ROUND3_REVIEW.md) | **给 Aaron 的操作单**：第 3 轮复审的提示词早已 ISSUED，可能从没真发出去。含可直接粘的开场段、`MUST_NOT_BE` 清单、返回后我要做的四步。**2026-08-29 复查：十份参考件自 pin `d34ce7c` 起全部未动，可以原样发** |
| [`REHEARSAL_SAMPLE_2026-08-29.md`](REHEARSAL_SAMPLE_2026-08-29.md) | **整条链第一次端到端走通的样本输出**（全合成输入，零治理写入，`day_strata_dryrun`）。两条路径：事件旗标缺失 → 生产者拒绝；旗标齐全 → builder 在 authority 分区拒绝。**首次走通就抓到一个真缺陷**：`run_c_build` 把所有 builder 异常都记成 `row_schema_blind`，而 builder 也校验 authority —— 于是 B_DERIVE 的 custody 缺陷被记到 C_BUILD 的行模式门下。已订正 |
| [`MEASURED_WHAT_THE_REGISTRY_APPEND_UNLOCKS.md`](MEASURED_WHAT_THE_REGISTRY_APPEND_UNLOCKS.md) | **registry 追加授权的实测**（合成 registry 干跑，真实登记簿未动）。**结论：追加 P1 解开的门数是 0**，五道门的翻转全部来自 P2；但 P1 是**结构必需**（没有它 `chain_does_not_start_at_proposal`）。**P1 不随提交作废，P2 会** —— 所以等的成本是零。**builder 建议：现在别给**，等接线过 fresh Sol 之后，理由四条可复算，数字全部由 `tests/test_what_the_registry_append_unlocks.py` 产出 |
| [`PREPARED_C_BUILD_1_GATE_WIRING.md`](PREPARED_C_BUILD_1_GATE_WIRING.md) | **已写好、待落地的 C_BUILD_1 三门接线**（补丁 106 行同名 `.patch`）。阻塞原因不是缺授权 —— Aaron 08-29 明确批了「把五道门建成真的分类器」；阻塞的是 `supplement_runner.py` 此刻被 fresh Sol 持有（C_BUILD_2 措辞第 3 轮，仍未返回），改它会让那一轮席位白烧。**含一条自我订正**：该文件从来不在 `FROZEN_HASHES` 里，我按一条过期记忆少干了活 |
| [`WAITING_ON_AARON.md`](WAITING_ON_AARON.md) | **等 Aaron 一句话的完整清单**，大白话，每条附 builder 推荐。A1 目录授权（`quant-data` 下两条逐字路径）· A2/A3 迁移 ①②（必须分两句）· A4 迁移 ③（**建议别给**：本机单卷，给了也执行不了）· B1 MATERIALITY · B2 真实数据运行授权（**唯一不可逆的一条，现在不该批**）。另列 builder 已自行接手、不再等他的四项 |
| [`DECISION_PACKET_FOUR_OPEN_2026-08-26.md`](DECISION_PACKET_FOUR_OPEN_2026-08-26.md) | 四项待裁。Fable 已裁，但**裁决工件不在盘上**——见下一行 |
| [`RULING_FABLE_FOUR_OPEN_2026-08-26.md`](outcome_quarantine/RULING_FABLE_FOUR_OPEN_2026-08-26.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · **Fable 对 D-1..D-4 的裁决全文**，逐字节转录，SHA256 `90CC7110…749B86` 已复核 **⚠ outcome-carrying**（自身携带累计 exposure 计数，转录同时已隔离） |
| [`FINDINGS_FABLE_FOUR_OPEN_TRANSPORT_STOP.md`](FINDINGS_FABLE_FOUR_OPEN_TRANSPORT_STOP.md) | **传输 STOP**：四项裁决未转录未执行；另含两条已复核的 builder 自身缺陷（指令指向隔离件；隔离值扩散进 10 份未登记文件，其中 3 份是测试） |
| [`PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md`](PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md) | **第 3 项交付物**：`_SAVE_DIR` 配置化设计 ＋ **范围发现**——同一缺陷在 `header.py:201` 还有第二处，D-4 未点名 |
| [`PREP_ITEM2_QUARANTINE_MIGRATION.md`](PREP_ITEM2_QUARANTINE_MIGRATION.md) | **第 2 项交付物**：迁移可行性实测（生产代码零路径引用）＋计划。**发现裁定未区分仓根台账**，三选一待 Aaron |
| [`PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md`](PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md) | **第 6＋8 项交付物**：ND1 profile R3 修订提案（三步之第一步）。含 builder 实测的**第二个缺口**——闭合检查生产零调用，悬空 P3 今天会过 A_PRECHECK |
| [`PREP_ITEM1_L6_EXPOSURE_TEXT.md`](PREP_ITEM1_L6_EXPOSURE_TEXT.md) | **第 1 项交付物**：全局 L6 exposure 句的逐字终稿，可整段替换。**未落地**——全局文件写入需 Aaron 单独授权 |
| [`REGISTRY_SYNC_FAILURE_MODEL.md`](REGISTRY_SYNC_FAILURE_MODEL.md) | **第 7 项边界 (3)(4)**：registry 在同步树内的故障模型与恢复程序。含 builder 复核出的第二条致命通道（裁定文本少算的那条） |
| [`D124_RULINGS_CLEAN_EXTRACT.md`](D124_RULINGS_CLEAN_EXTRACT.md) | **D-1／D-2／D-4 裁决的 outcome-clean 逐字副本**（原件是隔离件）＋ builder 已落地部分的对照。三项未决部分即八项待裁的前三项 |
| [`D3_REGISTRY_WRITER_PROPOSAL.md`](D3_REGISTRY_WRITER_PROPOSAL.md) | **D-3 提案**：谁向 registry 追加 P3 与失败事件。待 fresh Sol 批准 → Aaron 终裁。outcome-clean（裁决全文是隔离件，故另立可读副本）。**§2.5–2.7 是 builder 实测**：已批准的 ND1 actor 表把 A1／F1／F2 都判给运行器，与提案「失败事件仅主代理」相抵三行 |
| [`N09_EXECUTION_PATH_DESIGN_R2.md`](N09_EXECUTION_PATH_DESIGN_R2.md) | N09 执行路径设计 R2 —— **Sol 判 HOLD**，R3 待 Fable 裁定后再写 |
| [`N08_SCOPE_UNRESOLVED.md`](N08_SCOPE_UNRESOLVED.md) | N08 范围无法重建的实测记录（节点已由 Aaron 裁 DROP） |
| [`PENDING_ANCHOR_UPDATES.md`](PENDING_ANCHOR_UPDATES.md) | 已并入主计划 §15.1，**保留为历史，勿再并一次** |

## 3. 裁定与决策（authority）

| 文件 | 是什么 |
|---|---|
| [`BUILDER_DECISIONS_2026-08-29.md`](BUILDER_DECISIONS_2026-08-29.md) | **builder 自裁，不是 owner 裁定**（依 Aaron 2026-08-29「很多决定不需要问我」的工程分工，与 `OWNER_DECISIONS_*` 严格分开）。**BD-1** 两个未决封印码不归门、归路由器 B —— 套用已被测试执行的 `archive_policy_a` 先例，而非新原则；`GATE_TABLE` 是已批准封闭枚举，加门属 R4 级，挑一个不合适的门会把缺陷记到没人裁定过的名下。**BD-2** qros 席位台账：建，但只向前记，历史标 UNKNOWN 不回填。**BD-3** qros 倒转默认：采纳 |
| [`BUILDER_DECISIONS_2026-09-02.md`](BUILDER_DECISIONS_2026-09-02.md) | **BD-2：`archived_bytes_deleted` 的终态是 A1**。由封闭答案空间的排除法得到（P4 被 Policy A 排除，「被拒的 seal」被「seal 活着」排除），而 A1 是**非终态陷阱**、挡住完成——这一点是排除法在此处足够的原因。实现用 `decide_after_seal(post_archive_ok=)` 把检查点的判定**告诉**路由器，而不是合成一份失败报告去骗过 `classify_archive_report`。**并记下我自己的两个错**：先把这条越级递给了 Aaron，随后被要求转给 Fable 裁决——而 Fable 可顾问不可代签 |
| [`REVIEW_RESULT_ENG_SAFETY_2026-09-02.md`](REVIEW_RESULT_ENG_SAFETY_2026-09-02.md) | **ENG-SAFETY-PRE-REAL-DATA-001 = HOLD**，Aaron 亲任席位。四条发现**全部由 builder 逐条复现、无一采信自述**：H1 链路不绑定 out_dir/runs_dir（真归档下 P4+archive_ok 而 seal 不在归档里）、H2 无 gate-first 组合路径、M1 `retry_permitted` 被当作封存成功、**M2 推翻 BD-5 并致其收回**（P3 后继是四个不是三个；A1 行写不出来；A2 治不了）。另记我的两个缺陷：包在席位持有期间被我改写四版；以及我加宽守卫时用子串匹配造成假阳性，据此差点改坏一份治理记录 |
| [`REPAIR_ENG_SAFETY_HOLD_2026-09-02.md`](REPAIR_ENG_SAFETY_HOLD_2026-09-02.md) | **HOLD 的三条工程缺陷已修，每条先复现再修**。H1 链路改为只收 `PlannedPaths`——绑定规则来自**已批规划器**而非我发明；顺带挖出两个缺陷（C_BUILD_1 的「必须为空」一直在查错的目录；那条拒绝以裸异常逃出）。M1 `retry_permitted` 不再算封存成功。H2 新增 `run_supplement_gate_first`（A_PRECHECK→B_DERIVE→运行目录→C_BUILD），**建它不打开执行**，因为 A_PRECHECK 今天就拒绝；无人拥有的 mkdir 现在有主且默认拒绝。另有一条测试被改写——它原先把 H1 钉成了预期行为 |
| [`SEAT_RECORD_ENG_SAFETY_PRE_REAL_DATA_2026-09-02.md`](SEAT_RECORD_ENG_SAFETY_PRE_REAL_DATA_2026-09-02.md) | **席位记录本体，逐字节转录**（sha256 `6001eeea…`，源文件按哈希定位而非按路径猜，转录后三方一致）。语义未改、未做换行规范化——规范化会改变字节 |
| [`DECISION_PACKET_ARCHIVED_BYTES_DELETED_2026-09-02.md`](DECISION_PACKET_ARCHIVED_BYTES_DELETED_2026-09-02.md) | **最小决策包，outcome-clean**：`archived_bytes_deleted` 在已批状态机里的合法处理。四个后继逐一对照（P4 被 Policy A 排除；A1 的行**写不出来**；F2 语义存疑——把成功封存记成失败 run；CR1 无崩溃可言），四个方案与影响。**关键观察：维持 fail-closed 不是中性的**——它在链上留下 dangling P3，而 CR1 正是为此存在。**席位分析并建议，Aaron 裁** |
| [`SEAT_RESULT_ARCHIVED_BYTES_DELETED_2026-09-05.md`](SEAT_RESULT_ARCHIVED_BYTES_DELETED_2026-09-05.md) | **席位结果验收 —— 席位对，builder 又错了一次**。High 成立：包称「A2 是 A1 唯一出口」为假，`A1 -> AX -> F3` 存在，**而同一份包的 §2 自己就印着 `A1 -> A2, AX`**。另查出三处「声称宽于证据」，其中「P3 已经落地」在当前构建里**根本没有追加路径**。含交给 Aaron 的四项：**推荐 O2′（A1＋新码，出口裁为 AX，不改 A2）**，理由是判 F2 会重建一个已被测试执行出来的 Router 矛盾；枚举只动 ARCHIVE_CODES 一处；**需要 R4**；以及 fail-closed 的真实后果（含我那句无根据的 dangling P3 更正）|
| [`AMENDMENT_ARCHIVE_CODE_6_2026-09-05.md`](AMENDMENT_ARCHIVE_CODE_6_2026-09-05.md) | **待批准修订：`ARCHIVE_CODES` 5→6**（Aaron 2026-09-05 选「乙」后起草）。`CANONICAL_SHA256=7c63b3f4…`，块由 `scripts/archive_code_6_block_builder.py` **生成而非手抄**，哈希由测试按已批约定复核并做过变异检验。**§0 是我在他决定前没说清楚的一件事**：枚举自述「每个码都对应 ArchiveReport 的一个结构状态」，而新码不满足，**所以修订同时要改这条自述不变量**——「乙」比我告诉他的贵一点。仍为 `STATUS=PROPOSED`，代码一字未动，守卫断言枚举仍是 5 个 |
| [`REVIEW_PACKET_ARCHIVE_CODE_6_2026-09-05.md`](REVIEW_PACKET_ARCHIVE_CODE_6_2026-09-05.md) | **ARCHIVE-CODE-6 提案的对抗性送审包**（Fable，给建议不裁定）。§2 逐条列出 **builder 在本题已错两次**，请席位以此为基准怀疑度；§3 四条按我自己把握从低到高排，最低那条是「widen 一条已批枚举的自述不变量是否比加一个成员更重」；并请席位**去读 A2 的实际恢复校验器**——上一席位明说那是它未复现的条件推论，而本提案 §3 建立在其上 |
| [`COMPLETION_AND_SIMPLIFICATION_PLAN_2026-09-05.md`](COMPLETION_AND_SIMPLIFICATION_PLAN_2026-09-05.md) | **复杂度收缩审计与最短路径**（Aaron 2026-09-05 改变目标后）。量出来的诊断：**8-29 以来 ops 改动 191 次 vs src 44 次**，测试体量其实健康（大文件全是 S0 研究测试）——**问题在流程产出不在测试**。**关键发现：归档 supplements 子树是空的，所以 `archived_bytes_deleted` 在第一次真实运行中结构上不可达**，那条修订与在飞的 Fable 复审都不挡首跑。A 类只剩三条（两条是 Aaron 的授权 + 一段接线）；D 类列出六种要停的习惯，并区分「真正保护研究有效性的 QROS 规则」与「我叠加的执行习惯」。**唯一卡住的是我不知道 N10/N11/N13 是什么** —— 内容在隔离的主计划里 |
| [`PUBLIC_RELEASE_INVENTORY_2026-09-05.md`](PUBLIC_RELEASE_INVENTORY_2026-09-05.md) | **公开发布分类，只分类不删除**。量出来的关键数字：**A 类 55 个文件 = 3529 条测试**（6分24秒），B 类 77 个文件 = 1477 条（36 秒）——**70% 的测试是研究保护，只占 42% 的文件**，所以公开仓不是精简版。C 类几乎全在 `ops/` 里，而 `ops/` 整个不进公开仓，**所以 C 类对公开发布几乎无影响**。含建议的公开目录结构：**README 是最重要的文件**，治理压成一页而不是一个目录 |
| [`SEAT_RESULT_ARCHIVE_CODE_6_FABLE_2026-09-05.md`](SEAT_RESULT_ARCHIVE_CODE_6_FABLE_2026-09-05.md) | **Fable 席位结果,逐字节转录**（`877b3c2c…`，18491 bytes）。建议层面 HOLD，方向不变。两条 High builder 均已复现：**双码并发无优先级**（真洞，归 backlog——首跑结构上不可达）、**哈希守卫在默认环境下不通过**（cp1252 vs 严格 UTF-8，复现性缺陷，已修）。另纠正 builder 一处过宽论证：那条 Router 矛盾测试执行的是 `archive_failed` 误路由，本案是 `archive_ok` 加附带损失，**在 Policy A 谓词之外**——F2 仍是最差落点，但论证要缩 |
| [`BACKUP_STATUS_2026-09-02.md`](BACKUP_STATUS_2026-09-02.md) | **`CURRENT_BACKUP_AVAILABLE=NO`** —— 不是目录不见，是**整个盘符不存在**。历史 flag 断言的是「2026-07-28 验证过」，不是「此刻可达」，而 `assert_real_run_allowed` 只查 flag 在不在。恢复的四步最小动作，以及**有不读 payload 的认证方法**（现有工具只哈希不解码，研究轴不动一格）|
| [`PREFLIGHT_BEFORE_REAL_DATA_2026-09-02.md`](PREFLIGHT_BEFORE_REAL_DATA_2026-09-02.md) | **真实数据前的最终边界，按 Aaron 的七项逐条回答**。HEAD `bbae823e…`，4997 全绿；合成 bars 除归档外全程不打桩跑到 **P4**。**§0 是一条安全相关的自我更正**：我先前说「被 assert_real_run_allowed 挡着」，执行后发现**那道门是开的**——真正拦住的是「没有 live P2」与「代码库里没有任何地方配置 job_dir」。两个 blocker（①job_dir / ③P2）、五条 residual、①与 P2 的精确授权形状、以及本阶段被守卫拦下的三次 |
| [`REVIEW_PACKET_PRE_REAL_DATA_2026-09-02.md`](REVIEW_PACKET_PRE_REAL_DATA_2026-09-02.md) | **真实数据前的 outcome-blind 工程安全送审包**（由 Aaron 派发，我不得自行调用席位）。12 条禁读清单机器生成；四块受审面按承重排序（R1 未独立复审的修复 / 编排层 / 输入装配层 / loader 边界）；**我自己报告的四条弱点请席位核实而非采信**；明写不满足 A2 也不满足 Stage I |
| [`PREFLIGHT_1_DEVELOPMENT_INPUT_2026-09-02.md`](PREFLIGHT_1_DEVELOPMENT_INPUT_2026-09-02.md) | **① 授权 preflight**。只读检视，未调用 `load_real`、未开任何 .dbn.zst。**两个候选 job_dir，manifest 逐字节相同，差别在认证**：A 在 attestation 的 primary_root 下，B 在 OneDrive 同步树内且不在 attestation 里——而 `_check_role` **区分不了两者**。生效 manifest 是官方 `manifest.json`（`_local_manifest.json` 无 files 映射）；139 个数据文件全部有 expected sha256 且覆盖无缺口；文件集为**全部 139 个**（`full_development_expost` 要求全窗口）。新 residual：attestation 的 `E:\quant-data` 备份卷**当前不存在** |
| [`OWNER_DECISIONS_2026-08-26.md`](OWNER_DECISIONS_2026-08-26.md) | **Aaron 采纳八项**＋逐项结算表（哪几项完成了、其余还欠他哪个具体动作） |
| [`OWNER_DECISIONS_2026-08-25.md`](OWNER_DECISIONS_2026-08-25.md) | **Aaron 本人**四项裁定，`DELEGATED=NO` |
| [`DELEGATED_RULINGS_2026-08-24.md`](DELEGATED_RULINGS_2026-08-24.md) | N06 终态 ＋ N-D2/N-D3 共 32 项，Sol 委托裁定 `DELEGATED=YES` |
| [`RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md`](RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md) | MC-REG-COLLISION-001 批准（C2 被整条替换） |
| [`RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md`](RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md) | 上一条的 Fable 提案 |
| [`RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`](outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · N-D2/N-D3 的 Fable 提案 **⚠ outcome-carrying** |
| [`ND1_PROFILE_RATIFICATION.md`](ND1_PROFILE_RATIFICATION.md) | N-D1 profile 批准。**目录创建／写探针／执行是三次独立授权** |
| [`DECISION_PACKET_N00_AND_ND1.md`](DECISION_PACKET_N00_AND_ND1.md) | N00 与 N-D1 决策包，含 `N00_MISSING_AUTHORITY_CHECKLIST` 与 §D.3.4 |
| [`DECISION_PACKET_ND2_ND3.md`](outcome_quarantine/DECISION_PACKET_ND2_ND3.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · N-D2/N-D3 合并决策包 **⚠ outcome-carrying** |
| [`ND2_ND3_RULING_REVIEW_FINDINGS.md`](outcome_quarantine/ND2_ND3_RULING_REVIEW_FINDINGS.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · 对上一条裁定的复核发现 **⚠ outcome-carrying** |
| [`DECISION_MC_REGISTRY_COLLISION.md`](DECISION_MC_REGISTRY_COLLISION.md) | 两份已批准工件相抵的记录；末尾 STATUS 段为收口 |
| [`S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md`](S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md) | L-5 输出根运维决策 |

## 4. 交给别的席位的提示词（历史）

> **要贴的那份永远在 [`NEXT_HANDOFF.md`](NEXT_HANDOFF.md)。** 下面是已用过的。

| 文件 | 交给谁 / 结果 |
|---|---|
| [`PROMPT_C_BUILD_2_WORDING_SOL_ROUND6.md`](PROMPT_C_BUILD_2_WORDING_SOL_ROUND6.md) | **第 6 轮，`PREPARED_NOT_ISSUED`**。§1.1 摆出五轮同一形状的证据，§1.2 说明换仪器，§3 请它**攻击观测器本身**（`os.open`／`shutil`／子进程绕过、场景集完整性、计数不等于因果） |
| [`OFF_LIMITS_COMPANION_R6.md`](OFF_LIMITS_COMPANION_R6.md) | 第 6 轮的禁区伴随件 |
| [`OFF_LIMITS_COMPANION_R5.md`](OFF_LIMITS_COMPANION_R5.md) | **第 5 轮的禁区伴随件**，随提示词一同交付。D-2 裁定要求它独立存在：第二个席位被烧时，禁区清单写在提示词里而交付载体是 Review Packet，**清单没跟过去**。含可执行的检索边界与「工具落盘请报路径、不要打开」 |
| [`PROMPT_C_BUILD_2_WORDING_SOL_ROUND5.md`](PROMPT_C_BUILD_2_WORDING_SOL_ROUND5.md) | **第 5 轮，`PREPARED_NOT_ISSUED`**。§1.1 记着本轮最该记的一条：**第 4 轮的两个根因，我在第 4 轮 §4 里自己列出过，然后没去修** —— 列出弱点不等于处理弱点。所以 §4 改成「要么已修、要么明确接受并写明代价」，不再是「可能错的地方」清单 |
| [`PROMPT_C_BUILD_2_WORDING_SOL_ROUND4.md`](PROMPT_C_BUILD_2_WORDING_SOL_ROUND4.md) | **第 4 轮，`PREPARED_NOT_ISSUED`**，等 Aaron 发。第 3 轮两条 HOLD 发现已修，含**我用 Sol 自己的反对意见攻击我的修复**的记录 —— 机制在发出前两次抓到我（合同只枚举函数体；`_preserve` 有两个调用点我只声明了一个）。§0 是**可执行的检索边界**，不是散文 —— 上一轮席位的曝光事故成因就是它 |
| [`PROMPT_EIGHT_OPEN_FABLE.md`](PROMPT_EIGHT_OPEN_FABLE.md) | Fable 决裁席，八项，**已全部裁定并经 Aaron 采纳**；席位自评未烧 |
| [`PROMPT_D3_SOL_REVIEW.md`](PROMPT_D3_SOL_REVIEW.md) | Sol，D-3 复核，**已返回 HOLD**，席位未烧 |
| [`N09_EXECUTION_PATH_A2_SOL_PROMPT.md`](N09_EXECUTION_PATH_A2_SOL_PROMPT.md) | Sol，两次 TRANSPORT_STOP 后被 Review Packet 取代 |
| [`MC_REG_COLLISION_SOL_RATIFICATION_PROMPT.md`](MC_REG_COLLISION_SOL_RATIFICATION_PROMPT.md) | Sol，已 RATIFIED_AS_MODIFIED |
| [`MC_REGISTRY_COLLISION_FABLE_PROMPT.md`](MC_REGISTRY_COLLISION_FABLE_PROMPT.md) | Fable，已出提案 |
| [`ND2_ND3_FABLE_DECISION_PROMPT.md`](outcome_quarantine/ND2_ND3_FABLE_DECISION_PROMPT.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · Fable，32 项 **⚠ outcome-carrying** |
| [`N06_DISPOSITION_AND_ND2_ND3_RATIFICATION_SOL_PROMPT.md`](N06_DISPOSITION_AND_ND2_ND3_RATIFICATION_SOL_PROMPT.md) | Sol，N06 终态＋32 项批准 |
| [`N06_ROUND2_SOL_PROMPT.md`](N06_ROUND2_SOL_PROMPT.md) · [`N06_ROUND3_SOL_PROMPT.md`](N06_ROUND3_SOL_PROMPT.md) · [`N06_ROUND4_SOL_PROMPT.md`](N06_ROUND4_SOL_PROMPT.md) | N06 二/三/四轮 |
| [`N06_REVIEW_HANDOFF.md`](N06_REVIEW_HANDOFF.md) | N06 首轮交接 |

## 5. 复审结果与证据

| 文件 | 是什么 |
|---|---|
| [`RULING_FABLE_REMAINING_2026-08-26.md`](RULING_FABLE_REMAINING_2026-08-26.md) | **其余十项裁定全文**（R1–R10，逐字）＋ builder 审核。R4／R6／R7 判 `DELEGABLE=NO`，仍等 Aaron；两条机械条件已跑，均成立 |
| [`RULING_FABLE_EIGHT_OPEN_2026-08-26.md`](RULING_FABLE_EIGHT_OPEN_2026-08-26.md) | **八项裁定全文**（逐字）＋ builder 逐条复现审核；含一处经复核的论证更正 |
| [`RULING_SOL_D3_HOLD_2026-08-26.md`](RULING_SOL_D3_HOLD_2026-08-26.md) | **D-3 复核结果 = HOLD**（4 High／1 Medium，五项留给 Aaron）＋ builder 逐条复现记录。outcome-clean |
| [`RULING_SOL_N09_R2_HOLD_2026-08-26.md`](RULING_SOL_N09_R2_HOLD_2026-08-26.md) | **N09 执行路径设计 R2 复审结果 = HOLD**（3 High／1 Medium，四条全部经 builder 复现）＋裁定原文逐字转录。**此前该轮裁定只存在于聊天里**，2026-08-27 落盘。outcome-clean |
| [`DECISION_PACKET_ITEM6_OPEN_FABLE.md`](DECISION_PACKET_ITEM6_OPEN_FABLE.md) | **第 6 项三个开放项的决裁包**（R-A 禁边 ZERO/FULL · R-B profile 行绑语法块的构造 · R-C 悬空 P3 的拒绝范围）。**R3 的 ratify 明确排除在外，仍是 `STILL_AARON_ONLY`。** 自带禁区清单与盲席检索禁令。outcome-clean |
| [`RULING_FABLE_ITEM6_OPEN_2026-08-27.md`](RULING_FABLE_ITEM6_OPEN_2026-08-27.md) | **第 6 项三项开放项的裁定（生效）**：R-A=FULL · R-B=接受构造＋三条 CONDITIONS（已全部执行）· R-C=PER_ID_ONLY。**R3 的 ratify 仍 `STILL_AARON_ONLY`。** outcome-clean |
| [`P2_AUTHORIZATION_PREPARATION.md`](P2_AUTHORIZATION_PREPARATION.md) | **N09 的 P2 要什么，以及为什么今天签了也生效不了**——四必填字段、四条实测阻断（无前驱／registry 追加未授权／目录创建未授权／执行路径仍是拒绝骨架）、正确顺序。**不签、不代填。** outcome-clean |
| [`DECISION_PACKET_FOUR_OWNER_ITEMS.md`](DECISION_PACKET_FOUR_OWNER_ITEMS.md) | **Aaron 仅剩四件的决裁包**（P3 写者 · 目录创建四要素 · D-3 五项 · P2 排序与 P1 路径）。自带禁区清单。**P2 的签署与 verbatim 语句明令不可代裁。** outcome-clean |
| [`RULING_FABLE_FOUR_OWNER_2026-08-27.md`](RULING_FABLE_FOUR_OWNER_2026-08-27.md) | **四件的裁定（生效）**：executor provenance 成文化（不加新字段）· 目录创建五槽 · D-3 五项逐项 · P2 排最后＋P1 走主代理手工。**含两条独立性披露与一条 STRONGEST_OBJECTION。** outcome-clean |
| [`RULING_FABLE_SCOPE_AND_MIGRATION_2026-08-27.md`](RULING_FABLE_SCOPE_AND_MIGRATION_2026-08-27.md) | **两份边界裁定（生效）**：R3 骨架＝NARROW · `save_dir` 合同＝BOTH · 迁移路线＝A ＋ 十条不变量。**含 builder 对八条可证伪断言的逐条复现，以及三件两份裁定都没有的发现。** 模型同源性三连与机制来源两条披露留给 Aaron。outcome-clean |
| [`DECISION_PACKET_SCOPE_AND_BOUNDARY.md`](DECISION_PACKET_SCOPE_AND_BOUNDARY.md) | **两个边界问题的决裁包**：R3 骨架可建到哪（NARROW/WIDE，裁定收尾句与 R3 §6 给了两个边界）· `save_dir` 合同的边界（LEXICAL_ONLY/RENDER_TIME/BOTH，三轮 HOLD 同一缺陷类）。跨 ITSF 与 qros-runtime 两仓。outcome-clean |
| [`DECISION_PACKET_REGISTRY_MIGRATION.md`](DECISION_PACKET_REGISTRY_MIGRATION.md) | **registry 迁出 OneDrive 的设计与决裁包**。**头号发现：刚批准的 CR1 语法块（`c251335f…`）依赖 `ops/TRIAL_REGISTRY.md` 的 git 历史，而迁出仓库＝迁出 git——迁移方向与它相抵。** 三条路线 ＋ 六条不变量 ＋ 15 处路径构造盘点。`STATUS=DESIGN_ONLY`。outcome-clean |
| [`REGISTRY_MIGRATION_PLAN_ROUTE_A.md`](REGISTRY_MIGRATION_PLAN_ROUTE_A.md) | **路线 A 迁移方案 R2**（fresh Sol 判 HOLD 后修订）：新增 FENCE 静默期＋双向核对、S4 采纳复审席拓扑、S8 改成可执行备份合同。**S5 悬置——裁定给的副本文件名撞边界 (2)，整个方案今天不可执行。** `STATUS=PLAN_ONLY`。outcome-clean |
| [`CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md`](CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md) | **builder 自纠**：把 L-5 缺陷的**机制**（「会烧掉一次 trial」）写成了**已发生的事故**。实测 registry 里 `BURNED/ABORTED/VOID` 为 0。**两份裁定拒绝路线 C 的力度部分来自这句错话。** 另附 OneDrive 同步休眠的实测。outcome-clean |
| [`DECISION_PACKET_S5_AND_R4.md`](DECISION_PACKET_S5_AND_R4.md) | **复审席退回的两件**：S5 回滚副本的形式（**裁定给的文件名撞边界 (2)，缺陷在裁定里**）· CR1「所指已移」要不要走 R4（复审席比决裁席严，builder 倾向复审席）。另请它复核 builder 已修的五条。outcome-clean |
| [`ERRATUM_TO_MIGRATION_PLAN_REVIEW.md`](ERRATUM_TO_MIGRATION_PLAN_REVIEW.md) | **致正在飞的那轮迁移方案复审的勘误**——送审版含 builder 写错的一句；明说不必 STOP，并让复审席自选「纳入本轮」或「另计」。附改后新哈希。outcome-clean |
| [`DECISION_PACKET_A_COVERAGE_CANNOT_BE_PRESERVED.md`](DECISION_PACKET_A_COVERAGE_CANNOT_BE_PRESERVED.md) | **【已撤回 2026-08-29】** 原称「(a) 的覆盖保全在现 CONDITIONS 下无法满足」——整个前提是 builder 造出来的缺陷，已实测推翻（§14）。全文保留为误判记录。原文： —— 复审席 HIGH ②：缩窄违规类不能同时叫覆盖保全。三条出路各自越权（放宽判据 / 重开 B / 解除机制零改动），builder 一条都不能自己选。推荐重开 B，并写明这意味着 §12 大部分工作不进生产。outcome-clean |
| [`INCIDENT_BUILDER_GREPPED_A_QUARANTINED_FILE_20260829.md`](INCIDENT_BUILDER_GREPPED_A_QUARANTINED_FILE_20260829.md) | **事故：builder 对隔离件跑了一次内容检索**（跨 ops/ 的枚举没有先剔除隔离子树）。只返回一个计数，无 outcome 内容 —— **但那是模式恰好够窄，是运气不是纪律**。与恢复锚 §5 记的第 3 个被烧席位是同一个动作。outcome-clean |
| [`SUPPLEMENTS_SUBTREE_GRANT_PREPARATION.md`](SUPPLEMENTS_SUBTREE_GRANT_PREPARATION.md) | **`supplements\` 子树目录创建授权的准备件**（不是授权）。父层两条路径今天就确定、可签；**但第二层 `<id>_<UTC>` 与「封闭清单不得含通配符」正面相抵** —— 三条出路各自的代价已列，builder 倾向乙（运行时刻再签）但不代选。outcome-clean |
| [`OWNER_DECISIONS_2026-08-29.md`](OWNER_DECISIONS_2026-08-29.md) | **Aaron 裁定 D-3 的五项**（actor 保持绑定 · 崩溃恢复归主代理且每次单授权 · OneDrive 有界封套＋绊线 · 租约回收 fail-closed）。**六项全部采纳 builder 推荐**（含追加两问：P3 归运行器 · 运行目录乙案）。记录形式本身是证据。**§7 的设计侧两项全解除** —— builder 现在可以越过 DEFAULT_REFUSE_SCAFFOLD_ONLY；运行侧仍缺目录创建与 P2 两条授权。outcome-clean |
| [`MIGRATION_AUTHORIZATION_PREPARATION.md`](MIGRATION_AUTHORIZATION_PREPARATION.md) | **迁移 ①②③ 的授权准备件**（不是授权）。①的封闭路径清单一条、五个槽逐条、②应知悉的三件、**③今天给了也执行不了（实测本机只有 C: 一个卷）**。并说明为什么「这个你可以直接做了」在治理上批不掉迁移。outcome-clean |
| [`FINDINGS_DOLLAR_ANCHOR_SWEEP_2026-08-29.md`](FINDINGS_DOLLAR_ANCHOR_SWEEP_2026-08-29.md) | **已有的 `$` 锚定守卫只扫七个模式，另有五个从没被扫过**，五个全接受尾随换行（三个校验 SHA-256）。修法是**让清单从源码导出**而不是再手列一张；行解析器须逐条声明豁免。**这是生产改动**，与本周措辞侧的机制零改动不同。outcome-clean |
| [`FINDINGS_REFUSAL_COVERAGE_SCAN_2026-08-29.md`](FINDINGS_REFUSAL_COVERAGE_SCAN_2026-08-29.md) | **扫全部 290 个失败码找无人执行的拒绝**。**第一次口径错了 19 倍**（按完整串查，而 `pytest.raises(match=)` 是 re.search）—— costs.py 差点被写成「6/6 未覆盖」的重大发现。真实结果 3 条，已补测试。方法错误一并记录。outcome-clean |
| [`FINDINGS_EXHAUSTIVE_EXIT_SCAN_2026-08-29.md`](FINDINGS_EXHAUSTIVE_EXIT_SCAN_2026-08-29.md) | **从 AST 穷举 resolve_partial 的出口，找到第五条分歧类出口**（`supplement_post_promotion_verify`，唯一不留具名残留的一条，且重试静默成功）。**并量了推论那一半**：它不是缺陷，是未来执行路径的一项未被记录的义务 —— 记事件的组件今天还不存在。不改任何字节（冻结中）。outcome-clean |
| [`SELF_REPORT_AUDIT_2026-08-29.md`](SELF_REPORT_AUDIT_2026-08-29.md) | **builder 自陈审计** —— 把 R3 里更早会话留下的九条「实测」断言逐条重量：八条逐字符合，一条（§10.1）是陈旧时态非假。**明写方法边界：它抓不到 §12.5 那种散文里的偷换。**第 2 轮复审的伴随件，不在受审集内（R3 冻结中）。outcome-clean |
| [`PROMPT_C_BUILD_2_WORDING_SOL_ROUND3.md`](PROMPT_C_BUILD_2_WORDING_SOL_ROUND3.md) | **措辞复审第 3 轮**。第 2 轮四条 finding 全部先复现后修，其中一条带出更大的洞：**我只锚了三份批准里的第一份，而当时三份都在**。主攻击面：请对我给出的每一个「锚」先问它锚在几份东西的第几份上。outcome-clean |
| [`PROMPT_C_BUILD_2_WORDING_SOL_ROUND2.md`](PROMPT_C_BUILD_2_WORDING_SOL_ROUND2.md) | **措辞复审第 2 轮**。第 1 轮五条 finding 四条已闭合，第五条是 builder 发明的缺陷已撤回（§14）。**主攻击面是 builder 自陈的可复核性** —— 上一轮席位在我供的假前提上做了正确推理，所以这一轮请它把每句「实测……」当作待证。outcome-clean |
| [`PROMPT_C_BUILD_2_WORDING_SOL_REVIEW.md`](PROMPT_C_BUILD_2_WORDING_SOL_REVIEW.md) | **C_BUILD_2 新措辞的 fresh Sol 复审提示词**——裁定 B 的 CONDITIONS 所要求的那一道。**开篇告知：决裁席自陈已限定措辞形态，独立性相应折减。**六个攻击面，含 builder 三条自纠（§12.5–12.7：(a) 声称宽于检出、(b) 扫描面只有一个函数体、(c) 路线两条而实测四条）。outcome-clean |
| [`PROMPT_MIGRATION_PLAN_SOL_REVIEW.md`](PROMPT_MIGRATION_PLAN_SOL_REVIEW.md) | **迁移方案的 fresh Sol 复审提示词**——六个攻击面，含决裁席自陈的最弱处（「所指已移」治理缓解 vs R4）。**开篇告知：裁路线的席位对本方案设计有实质贡献、已自陈失格，跨家族独立审查由本轮恢复。** outcome-clean |
| [`DIRECTORY_CREATION_GRANTS.md`](DIRECTORY_CREATION_GRANTS.md) | **目录创建授权的 append-only 记录件**（第 2 件裁定所要求，由 builder 建）。**今天为空，`GRANTS_RECORDED=0`；建立本件不授权任何创建。** outcome-clean |
| [`FINDINGS_DANGLING_CITATIONS_2026-08-27.md`](FINDINGS_DANGLING_CITATIONS_2026-08-27.md) | **实测：`ops/*.md` 94 份里 15 处路径引用不可达，11 处是真问题。** 8 处指向已移入隔离区的文件——**这 8 个对象全部在 `carries_outcome` 表上**；另 3 处在 git 全历史中从未增删（名单在该文件 §3.B，此处刻意不复述——写出文件名本身就是给出一个指向）。**危害不是找不到，是找不到之后读者会搜索**——烧掉第二、三席的正是这个动作。builder 一条引用都没改，理由见 §4。outcome-clean |
| [`DECISION_PACKET_CITATION_REMEDIATION.md`](DECISION_PACKET_CITATION_REMEDIATION.md) | **上述 11 处如何处理的决裁包**：8 处陈旧引用走 REPOINT／MARK_ONLY／PER_DOCUMENT · 3 处「从未存在」是本该存在还是引用本身错。**争议焦点 `D124_RULINGS_CLEAN_EXTRACT.md` 是刻意做成 outcome-clean 的摘录，把它的引用指进隔离区与其存在目的相反**——同一处改动在不同文档里有相反的正确答案，故不由 builder 自选。outcome-clean |
| [`FINDINGS_PENDING_UNFREEZE_2026-08-27.md`](FINDINGS_PENDING_UNFREEZE_2026-08-27.md) | **等解冻才能落地的小发现**：2 处跨仓 `.py` 引用缺仓限定符，其中一处所在文档已随 `dec-s5-r4` 冻结、应扩写的守卫已随 `dec-citations` 冻结。**冻结正常工作，代价是这条得等。**明写「本件不得被用作绕过冻结的通道」。outcome-clean |
| [`RULING_FABLE_S5_AND_R4_2026-08-27.md`](RULING_FABLE_S5_AND_R4_2026-08-27.md) | **决裁席裁定（Aaron 已采纳）**：第 1 件 **GIT_ONLY**，且明说是对不变量 4 的**修订**——改名副本作废，逐字节保留由旧仓 O0 的 blob ＋ 新仓核证副本共同承担，**工作区不留第二份可读副本**；四条强制条件（S0 增 O0==工作区==SHA0 核证 · 回滚改字节级取回 · 墓碑不减 · 边界 (2) 不搭车但仍是真实运行前置）。第 2 件 **必须 R4**，且须一并处理 `PREIMAGE` 的仓锚定（一次性仓锚定，两处相对它解析）；R4 在迁移执行后起草，其前**禁止追加任何 CR1 行**。builder 五条修复全部判「修对了」。自陈最弱处：GIT_ONLY 把旧树内回滚介质从两种收窄到一种。**模型多样性第四连，Aaron 应知悉后追认。** outcome-clean |
| [`RULING_FABLE_CITATIONS_2026-08-27.md`](RULING_FABLE_CITATIONS_2026-08-27.md) | **决裁席裁定（Aaron 已采纳）**：8 处陈旧引用统一 **MARK_ONLY**（具名标记、**不给路径**——REPOINT 是把搜索邀请函换成带地址的登门邀请函）；`D124` 摘录**一个字节不改**（无法核验的逐字转录，任何编辑与篡改不可区分），警示改放进递送文书。四条执行条件 C1–C4，其中 **C2「可变性纪律高于本裁定」**：受保护字节一律走 addendum，残余悬空是预期结果不是修复失败。3 处「从未存在」就地标注 OPEN 并全部升 Aaron 裁存在性（`STRATEGY_COUNCIL_ROUND4_LOCK` 最重——一份溯源审计压在它上面）。「先有字节再引用」升为项目纪律条款，例外须在写入当时声明。outcome-clean |
| [`CORRECTION_CLASS_B_WERE_PROPOSALS_2026-08-27.md`](CORRECTION_CLASS_B_WERE_PROPOSALS_2026-08-27.md) | **builder 自纠，且作废了裁定第 2 件的前提**：三条被我分类为「从未存在的凭空引用」的路径，逐条读引用行后**全部是提案**——一个是被否决选项 R1 的假设文件（`RULING=R2`），一个是已在册恢复路径的落盘目标（**2026-08-25 的溯源审计早已穷尽搜索并记录**，我的扫描器命中了那一行却没读它），一个字面写着「是否新建……工程建议：建」。**机械的一半我量了，意图的一半我直接断言了——就在同一份论证「意图不可机械判定」的文档里。**第 1 件（MARK_ONLY／D124）不受影响；问 3 的纪律条款反被加强。outcome-clean |
| [`CITATION_DISCIPLINE.md`](CITATION_DISCIPLINE.md) | **IN FORCE（裁定问 3，Aaron 已采纳）**：新增路径引用时被引字节必须已存在；唯一例外是**在写下的当时**声明其为提案并登入 `_KNOWN` 附提案出处。两类在磁盘上同形、事后不可机械分辨，**但写入那一刻意图只有作者知道且声明成本为零**。当天即被实测证成：三条未声明的提案两天后被误分类，白烧一个决裁席位。附落地检查清单与覆盖边界（正则只认正斜杠 `ops/…`，与 C1 裸文件名标记是同一把剑的两面）。outcome-clean |
| [`DEFERRED_AFTER_MIGRATION.md`](DEFERRED_AFTER_MIGRATION.md) | **IN FORCE**：裁定推到迁移之后的两件，加一条现在就生效的冻结令 —— **R4 ratify 之前禁止追加任何 CR1 行**（把「本就不会」升为「明令不得」：前者依赖三个条件同时成立，任一解除就没人记得它靠的是巧合）。R4 须一并处理 `PREIMAGE` 的仓锚定，不止改一行；桥的形式由 R4 提案定而非裁定定（决裁席避免成为设计贡献者）。边界 (2) 接入立为独立事项，**但「不落地不许跑消耗 trial 的真实运行」不因此松动**。附 Aaron-only 十一项去重清单，含模型多样性已连续五席全为 Fable。outcome-clean |
| [`OWNER_DECISIONS_2026-08-27.md`](OWNER_DECISIONS_2026-08-27.md) | **Aaron 2026-08-27 对 DEFERRED §4 八项的裁定**：不重开路线 · 不重裁引用第 2 件 · 条款暂不升 QROS（FROZEN v2.0.1，一个项目一周的经验不足以改冻结教条）· 不重制 D124 · 席位记忆接触不烧 Stage I 资格（如实记明这是宽松的一边）· **模型多样性五连立路由规则**：高风险决策 Sol 先 pre-seal 挑战再由 Fable 裁，明确不采用「把 Sol 变成决裁席」。**§0 明写「就按你推荐的全做」不构成迁移授权** —— ①②③ 维持 NO。另含实测发现：**本机只有 C: 一个卷，S8 异卷备份的硬件前提未满足**。outcome-clean |
| [`DECISION_PACKET_C_BUILD_2_HOOK.md`](DECISION_PACKET_C_BUILD_2_HOOK.md) | **C_BUILD_2 的断言观测不到 —— 决裁包**。R3 §1 说那三条「都是文件系统事实」，而实测 `resolve_partial` 是 stage→verify→promote 一体的：**「FINAL 缺席 ＋ .partial 在场」只存在于调用内部，而它不提供让门在那一刻运行的钩子。** 今天潜伏（门是默认拒绝的桩、整条路径从未运行）。二选一：A 把门接进 staging 内部（断言逐字保留，代价是在原子操作中间开可观测点）· B 重述断言为调用后可观测的形态（机制不动，代价是改一段被复审过的文本）。**明令不得给出机制草案** —— 前一决裁席自陈「设计贡献即丧失未来复审独立性」。附申报：这是连续第 6 个同家族席位。outcome-clean |
| [`RULING_FABLE_C_BUILD_2_HOOK_2026-08-28.md`](RULING_FABLE_C_BUILD_2_HOOK_2026-08-28.md) | **决裁席裁定 B**（重述断言，不动机制）。三条核心理由：A 会把默认拒绝的门变成**残留制造机**（每次调用都在 staging 中途被打断）· A 违反 R3 自己的门学说（门是分类器不是校验器）· **中途观测点不提供任何调用前拿不到的信息，而调用前拒绝能在任何 `.partial` 落盘之前拦住**。给了「不弱于」的五条判据。另抓 builder 两处事实错误：**连席计数被低估**（包写第 6，实为第 10）· **BRANCH_C/E 标签归属矛盾**（它未读批准原文而让渡，builder 读了并核正）。自陈最弱处：B 以「变异证红纪律持续被执行」为前提，而该前提没有机械守卫。outcome-clean |
| [`R3_CROSS_FIELD_RECHECK_2026-08-27.md`](R3_CROSS_FIELD_RECHECK_2026-08-27.md) | **§7 路线的 builder 步骤**：R3 的 C1–C10 跨字段检查重跑（7 PASS／3 不适用／0 FAIL）＋ CR1 双向边闭合 ＋ 两个 canonical SHA-256。**批准未发生，`PROFILE_STATUS=PROPOSED_NOT_EFFECTIVE`。** outcome-clean |
| [`N09_EXECUTION_PATH_DESIGN_R3.md`](N09_EXECUTION_PATH_DESIGN_R3.md) | **N09 执行路径设计 R3**——回应 R2 的 HOLD：三个 checkpoint 各自的副作用断言、冻结的 A1/F2/indeterminate 矩阵、钉死的 structural-only 调用图、precheck 证据规则。`BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`，`STATUS=NOTHING_IMPLEMENTED`。outcome-clean |
| [`A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md`](A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md) | N09 首轮：席位暴露 ＋ 非正式 REDESIGN |
| [`N09_EXECUTION_PATH_DESIGN.md`](N09_EXECUTION_PATH_DESIGN.md) | R1（已被 R2 取代，正文保留原样） |
| [`N06_HOLD_RED_PROOF.md`](N06_HOLD_RED_PROOF.md) | N06 四个 High 的红证 |
| [`N06_HOLD_REPAIR_EVIDENCE.md`](N06_HOLD_REPAIR_EVIDENCE.md) · [`N06_ROUND2_HOLD_REPAIR_EVIDENCE.md`](N06_ROUND2_HOLD_REPAIR_EVIDENCE.md) · [`N06_ROUND3_HOLD_REPAIR_EVIDENCE.md`](N06_ROUND3_HOLD_REPAIR_EVIDENCE.md) | 各轮修复证据 |
| [`MC_FACTORY_BOUNDARY_STAGE_I.md`](outcome_quarantine/MC_FACTORY_BOUNDARY_STAGE_I.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · factory boundary 的 Stage I 记录 **⚠ outcome-carrying** |
| [`ND1_ENGINEERING_EVIDENCE_PACKET.md`](ND1_ENGINEERING_EVIDENCE_PACKET.md) | N-D1 工程证据 |
| [`N00_N08_PROVENANCE_AUDIT_2026-08-25.md`](N00_N08_PROVENANCE_AUDIT_2026-08-25.md) | N00／N08 只读 provenance 审计 |

## 6. 事故记录（每一份都换来了一条机械守卫）

| 文件 | 换来了什么 |
|---|---|
| [`INCIDENT_TRANSPORTED_ARTIFACT_MUTATED_20260824.md`](INCIDENT_TRANSPORTED_ARTIFACT_MUTATED_20260824.md) | 冻结登记表 |
| [`INCIDENT_TRANSPORT_HEAD_PIN_20260825.md`](INCIDENT_TRANSPORT_HEAD_PIN_20260825.md) | 不会过期的 `REVIEWED_SET_UNCHANGED_SINCE` |
| [`INCIDENT_TRANSPORT_PIN_DERIVATION_20260825.md`](INCIDENT_TRANSPORT_PIN_DERIVATION_20260825.md) | 钉子从 git 派生，不手打；含「声明本身靠粘贴传递」的补记 |
| [`INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md`](INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md) | 送审集 outcome-clean 检查 |
| [`INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md`](INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md) | 结构性测试载荷事故（历史） |
| [`REVIEWER_EXPOSURE_LOG.md`](REVIEWER_EXPOSURE_LOG.md) | **复审席位暴露台账**（已烧两个席位）。与研究 exposure 是两条轴 |

## 7. 台账与登记表（append-only，行只增不改）

| 文件 | 是什么 |
|---|---|
| [`TRIAL_REGISTRY.md`](TRIAL_REGISTRY.md) | 事件真相源 |
| [`EXPOSURE_LEDGER.md`](EXPOSURE_LEDGER.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · §10.1 合规承载件，逐行转录仓根权威台账 **⚠ outcome-carrying** |
| [`REVIEWER_EXPOSURE_LOG.md`](REVIEWER_EXPOSURE_LOG.md) | 席位暴露，**不是**研究 exposure |
| [`FEASIBILITY_ERRATA_REGISTER.md`](FEASIBILITY_ERRATA_REGISTER.md) | feasibility 历史文档勘误 |
| [`OUTPUT_ROOTS_READINESS_CHECKLIST.md`](OUTPUT_ROOTS_READINESS_CHECKLIST.md) | 输出根就绪证明记录 |

## 8. 规范、证明与其他

| 文件 | 是什么 |
|---|---|
| [`MC_DR5_BUILD_PACKET.md`](outcome_quarantine/MC_DR5_BUILD_PACKET.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · MC/DR-5 build packet，含 §13.5 的 P2 授权模板 **⚠ outcome-carrying** |
| [`MC_DR5_CONSUMER_SOURCE_MATRIX.md`](MC_DR5_CONSUMER_SOURCE_MATRIX.md) | consumer 的来源矩阵 |
| [`MC_COST_PROBE_FINDINGS.md`](MC_COST_PROBE_FINDINGS.md) | N16 单位成本实测 |
| [`RUNTIME_DEVIATION_PACKET_SAVE_DIR.md`](RUNTIME_DEVIATION_PACKET_SAVE_DIR.md) | 对 qros-runtime 硬编码 `_SAVE_DIR` 的偏离记录 |
| [`QROS_FIRST_RUN_2026-08-24.md`](QROS_FIRST_RUN_2026-08-24.md) | 本项目首次接入 L6 runtime |
| [`S0_T001_POST_RUN_ATTESTATION.md`](S0_T001_POST_RUN_ATTESTATION.md) | S0-T001 盲式收口 attestation（哈希被代码 pin） |
| [`S0_T001_RESULT_DECISION_ADDENDUM.md`](outcome_quarantine/S0_T001_RESULT_DECISION_ADDENDUM.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · S0 结果裁决 addendum **⚠ outcome-carrying** |
| [`S0_T001_RESULT_REVEAL_ATTESTATION.md`](outcome_quarantine/S0_T001_RESULT_REVEAL_ATTESTATION.md) | **OFF-LIMITS（outcome-carrying，不得打开）** · 揭盲 attestation **⚠ outcome-carrying** |

| [`MIGRATION_R5_QUARANTINE_SUBTREE_2026-08-27.md`](MIGRATION_R5_QUARANTINE_SUBTREE_2026-08-27.md) | **R5 迁移执行记录**：10 迁 2 留、三处条件偏离、以及我把一份活跃复审弄失效的记录 |

## 8.5 隔离子树 `outcome_quarantine/`（R5 迁移，2026-08-27）

**该前缀下一切路径关闭。** 权威判据仍是
[`OUTCOME_CARRYING_ARTIFACTS.json`](OUTCOME_CARRYING_ARTIFACTS.json)——
**前缀是便利，不是替代**：注册表 12 条里有 **2 条不在这个前缀下**（两份
`EXPOSURE_LEDGER.md` —— **OFF-LIMITS，outcome-carrying，不得打开** ——
R1 裁 A′ 留在原地）。只查前缀会漏掉它们。

下面逐条列出**只是为了标记它们是禁区**，不是引导你去读。
**以下每一条都是 OFF-LIMITS（outcome-carrying，不得打开）：**

```
outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md          DAG／节点台账（旧恢复入口）
outcome_quarantine/RULING_FABLE_FOUR_OPEN_2026-08-26.md   D-1..D-4 裁决全文
outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
outcome_quarantine/ND2_ND3_FABLE_DECISION_PROMPT.md
outcome_quarantine/ND2_ND3_RULING_REVIEW_FINDINGS.md
outcome_quarantine/DECISION_PACKET_ND2_ND3.md
outcome_quarantine/MC_DR5_BUILD_PACKET.md
outcome_quarantine/MC_FACTORY_BOUNDARY_STAGE_I.md
outcome_quarantine/S0_T001_RESULT_DECISION_ADDENDUM.md
outcome_quarantine/S0_T001_RESULT_REVEAL_ATTESTATION.md
```

## 8.6 子任务板里的三份（扩大索引守卫后才发现从未入索引）

**共 13 份，全部此前不在索引里** —— 不是因为被排除，而是因为守卫只 glob 顶层
`ops/*.md`。R5 迁移逼着把守卫扩到 `ops/**/*.md`，才把它们照出来。

**`ops/M4_TASKBOARD/`**

| 文件 | 是什么 |
|---|---|
| `TASKBOARD.md` | M4 任务板 |
| `SA1_F10_CALENDAR.md` | SA1 F-10 日历 |
| `SA2_DEV_BOUNDARY.md` | SA2 Development 边界 |
| `SA3_S0_INPUT_PREFLIGHT.md` | SA3 S0 输入 preflight |

**`ops/M5_RUNNER_TASKBOARD/`**

| 文件 | 是什么 |
|---|---|
| `TASKBOARD.md` | M5 runner 任务板 |
| `M5_T0_INTERFACE_AUDIT.md` | T0 接口审计 |
| `SA4_S0_CORE.md` · `SA5_RUN_INFRA.md` | S0 核心／运行基础设施 |
| `SA6_AUDIT_FINDINGS.md` | SA6 审计发现 |
| `SA7_RUNNER_HARDENING.md` · `SA8_CORE_HARDENING.md` | runner／核心加固 |
| `SA9_IR22_23_24.md` | IR-22／23／24 |

**`ops/M6_TASKBOARD/`**

| 文件 | 是什么 |
|---|---|
| `M6_DESIGN.md` | M6 设计 |

## 9. 非 md

`packets/`（Review Packet v1，`ops/` 而非 runtime 默认的 `runs/`，原因见
`RUNTIME_DEVIATION_PACKET_SAVE_DIR.md`）· `M4_TASKBOARD/` · `M5_RUNNER_TASKBOARD/` ·
`M6_TASKBOARD/` · `S0_T001_REVEAL_EXPOSURE_MANIFEST.jsonl` ·
`SECOND_COPY_ATTESTED.flag` · `physical_copy_attestation.json` ·
`mc_cost_probe_2026-08-24.json`

---

## 10. 不能动的（移动 = 弄断生产代码或测试）

被 `src/`、`tests/`、`scripts/`、`qros-state.yaml` 或 `ops/*.json` **按路径**
引用，共 22 份。这里只列文件名以说明「不能移动」，**不是让你去开**；要读哪一份
先查 `OUTCOME_CARRYING_ARTIFACTS.json`。
**下表含隔离件，一律按 OFF-LIMITS 对待：**

```
TRIAL_REGISTRY.md                    EXPOSURE_LEDGER.md
MC_TO_STRATEGY_MASTER_PLAN.md        DECISION_PACKET_N00_AND_ND1.md
ND1_PROFILE_RATIFICATION.md          S0_T001_POST_RUN_ATTESTATION.md
S0_T001_RESULT_DECISION_ADDENDUM.md  S0_T001_RESULT_REVEAL_ATTESTATION.md
OUTPUT_ROOTS_READINESS_CHECKLIST.md  S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md
FEASIBILITY_ERRATA_REGISTER.md       DECISION_MC_REGISTRY_COLLISION.md
DELEGATED_RULINGS_2026-08-24.md      MC_DR5_BUILD_PACKET.md
MC_FACTORY_BOUNDARY_STAGE_I.md       DECISION_PACKET_ND2_ND3.md
ND2_ND3_FABLE_DECISION_PROMPT.md     ND2_ND3_RULING_REVIEW_FINDINGS.md
RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md
A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md
INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md
```

另有 25 份被其他 md 引用——移动它们只会留下断链，收益为零。

**本索引由 `tests/test_ops_index_is_complete.py` 机械守着**：`ops/` 下每新增
一份 `.md`，不写进本文件就会红。索引会烂掉，除非有东西盯着它。
