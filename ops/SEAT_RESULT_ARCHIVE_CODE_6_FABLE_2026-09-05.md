# 席位结果 · AMEND-ARCHIVE-CODE-6-REVIEW-001（Fable，给建议，不裁定，不代签）

```ini
RECORD_TYPE=SEAT_RESULT            席位给建议；裁定与签字归 Aaron
REVIEW_ID=AMEND-ARCHIVE-CODE-6-REVIEW-001
SEAT=Fable 5.1，fresh top-level session，2026-09-05
ROLE=adversarial reviewer of a proposal（不是 A2，不是 Stage I，不解开任何 QROS 门）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder 会话；本项目任何先前席位
EFFORT=high
LANE=FULL（RECOVERY_ANCHOR §4 自陈，非本席位推断）
OUTCOME_EXPOSED=本席位自述 NONE —— 未打开任何 carries_outcome 条目；§0 披露一次 find，是否算触碰由 Aaron 裁
PREREG_SEALED=N/A
REVIEWED_SET_PIN=88035e415b4f33091a48aac8b5e591ac6209a5f1
HEAD_AT_REVIEW=2fbdc169f8b74130225a468abc86e977d75c4689
SCOPE=只读；发现即报告；未修复任何东西；未写入仓库（本文件在仓库之外）
```

标签约定：[复现] = 我在本机从磁盘或进程内测得；[推断] = 由复现事实推出、未直接执行；[自述] = 包 / 修订 / SEAT_RESULT 的说法，未验证。未标者为分析。

---

## 0. 席位资格披露（先于一切）

在读到 NEXT_HANDOFF §0.1 **之前**，我为定位两个相对路径运行过一次按文件名的 find（cwd 是 Desktop，不是仓库）：

```
cd /c/Users/Aaron/OneDrive/Desktop && find . -maxdepth 4 -type f \( -name "NEXT_HANDOFF.md" -o -name "REVIEW_PACKET_ARCHIVE_CODE_6_2026-09-05.md" \)
```

输出仅两行：那两个文件的路径。未读任何内容；未匹配任何其他文件名。

之后所有 cat / sed / grep 只作用于点名文件。pytest 只跑了包 §5 点名的两个测试文件（它们内部读 ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md、ops/R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md、ops/ND1_PROFILE_RATIFICATION.md、scripts/s0_real_run.py；内容未进入我的上下文，输出用 -q）。导入 supplement_chain 会触发 day_strata_pipeline 等模块的导入——执行了，没读。

那次 find 是否算一次「检索」，由 Aaron 裁。若裁为触碰，本文件作废。

## 1. 字节核对（全部 [复现]）

| 项 | 结果 |
|---|---|
| 包 d1c27bf8… 5692 B | 一致 |
| 交接 7917e90d… 5487 B | 一致 |
| 受审集 5 文件（e444fe58 / 053760ef / bda85429 / 133d4095 / 94c88528） | 全部一致，字节数一致 |
| ARTIFACTS_UNDER_REVIEW.json 6 条 sha256 | 与磁盘一致 |
| pin 88035e4 → HEAD 2fbdc16，限定到受审集的 diff | 5 个 reference 文件无改动；包与交接在 pin 后有改动（LOW-1） |
| 工作树（限定到我碰过的路径） | 干净；pytest 缓存已在 .gitignore |
| canonical block 7c63b3f4… | 三路一致：sed+sha256sum 独立重算 / builder 进程内摘要 / 测试 test_the_stated_hash_is_the_hash_of_the_block_beside_it（58 行 3143 B；文件无 CR） |
| ARCHIVE_CODES | 5 个，不含 archived_bytes_deleted |
| tests/test_n09_r3_design_facts.py | 21 passed |
| tests/test_a_proposal_states_the_hash_of_its_own_block.py | **1 failed, 11 passed**（HIGH-2） |

## 2. Critical / High

没有 Critical：现字节下代码一字未动、仍具名拒绝，批准动作本身不开任何门。

### HIGH-1 双码并发没有优先级规则 —— 块 §3 声称「must be impossible」的性质有一个洞

- [复现] supplement_chain.py 时刻 3 先取 archive_report（200 行），再独立取 after 并跑 run_c_build_3（201–205 行）；对 post.failure 的判断（208–231 行）**不看 report.status**。所以「report=archive_failed（分类器给出如 file_digest_mismatch）且 run_c_build_3 给出 archived_bytes_deleted」两者可以同时成立。今天两种情形都在 212–225 行具名拒绝，所以洞没暴露。
- [复现] A1 只有一个 archive_code 字段（contract 246–250 行）。
- [推断] 修订落地后，若这一行写的是分类器的码，块 §3 那层「只对 archived_bytes_deleted 生效」的映射永远不触发 → A1 → A2 合法 → 登记「本次拷贝已恢复」，而历史字节仍缺。这正是块 §3 要杜绝的事。
- 块 §1–§3 只讨论 report 说 archive_ok 的一种情形。「归档失败且失败处理误删邻居」这一情形没有理由被排除在外。

建议：块里加一条优先级（例如 archived_bytes_deleted 压倒分类器码；或 A1 同时登记两个码）。这是块的内容，须在 Aaron 哈希批准前定，不是接线时再定。run_c_build_3 是否真能在 archive_failed 下返回该码，我没读到该文件（§7 索要）；链路代码没有阻止它。

### HIGH-2 交付的验证守卫在本机默认环境下不能复现 —— 摘要本身是对的

- [复现] `python -m pytest tests/test_a_proposal_states_the_hash_of_its_own_block.py -q` → 1 failed / 11 passed。失败项 test_the_builder_reproduces_the_document_block_exactly，`AttributeError: 'NoneType' object has no attribute 'splitlines'`。
- [复现] 机制：本机 ACP=1252，builder 经默认 stdout 输出 `§` 为单字节 0xA7（抓到的原始字节 `b'1 \xa7'`）；测试以 `encoding="utf-8"` 严格解码子进程输出，解码失败发生在 communicate 的读线程（第一次运行出现的 PytestUnhandledThreadExceptionWarning 就是它），stdout 变 None。
- [复现] 设 PYTHONUTF8=1 或 PYTHONIOENCODING=utf-8 后 12 passed；此时原始字节为 `\xc2\xa7`。本 shell 两者均未设。
- [复现] 摘要不受影响：builder 在进程内对 UTF-8 编码后的字节算哈希（脚本 94–95 行），文档块是正确的 UTF-8，三路一致。

含义：修订 §1 说该测试「复核」了约定，包 §5 把它列为复现命令，但在 owner 机器的默认环境它抛异常而不是验证——「声称宽于证据」的又一例，出在验证工具而不是被验证的字节上。builder 要么没在默认环境跑过它，要么在一个不同的环境跑过而未注明。修法很小（builder 经 sys.stdout.buffer 写 UTF-8；或测试给子进程设 env；或块里不用非 ASCII 字符），不归我做。

附带 [复现]：包 §5 第 4 条 `python -c "from itsf.mc import ..."` 按字面运行 ModuleNotFoundError，须 PYTHONPATH=src；两个测试文件自己插入 src，所以只有这条裸命令失败。

### HIGH-3（分析，不是缺陷）§3-2 的「决定性」宽于它的机械依据

- [复现] router_of("archive_policy_a")="B"；gates_at(C_BUILD_3)=("archive_policy_a",)；plan_failure_event 对未声明的 gate 名拒绝（gate_outside_closed_enum）；test_routing_it_as_an_ordinary_gate_contradicts_policy_a 存在、通过、做的正是包所述。

所以在今天的规划器下，时刻 3 的任何 F2 都必须标 archive_policy_a，而它归 Router B——builder 的机械链条成立。但它证明的是 **在现有机制下 F2 是最差的落点**，不是「判 F2 就重建了被测试执行出的矛盾」：

- 那个测试执行的是 `archive_failed` 报告经 gate 名误路由；本案是 `archive_ok` 报告加附带损失，在 Policy A 的谓词（runner 874 行：`local_seal_ok AND archive_ok`）之外，也在该测试覆盖之外。
- 本案任何终态都要新接线（修订 §2 第三件自认未设计）。F2 接线要么加一个 gate 名（动 GATE_TABLE，另一个已批封闭枚举），要么加一个并列路由器（本仓已有先例：decide_evidence_write_failure，contract 479–502 行）。两者都不是「重建旧矛盾」。
- 反过来，现状也不是 R3 §5 那种「无人知道发生了什么」的 INDETERMINATE：run_c_build_3 精确知道少了哪些字节。已知的坏状态没有终态——这一点支持给它一个终态。

结论：乙的方向在更窄的论证上仍然成立（F2 机械上最差；A1+新码在「archive_ok 应包含不伤及既有归档」这一宽读法下自洽）。Aaron 决定时听到的那句「决定性」在措辞上强于它的机械内容。是否因此重开选项，归 Aaron。

## 3. 包 §3 四条逐条

### 一 widen 自述不变量是否比加成员更重

取决于该不变量出自何处，而块没有说。

- [复现] 块的 INVARIANT_BEFORE 引自 contract 131–141 行的代码注释，不是 §D.3.2 P4 的批准文本；修订 §0 的「逐字」其实是该英文注释的中译（译得忠实，但不是逐字）。
- 若 §D.3.2 P4 只批了「CLOSED + 五个名字」：widen 的是注释，随成员一起走同一手续即可；但块把注释抬成了「已批枚举的不变量」，标签不实。
- 若 §D.3.2 P4 确有生产者性质的文字：块改的是已批语义，应像 R4 测试要求的那样点名并作废被替换的那句。

建议：块里加一行 `INVARIANT_SOURCE=`（§D.3.2 P4 原句，或 "code comment only"）。

一个不换方向的备选：不 widen——ARCHIVE_CODES 保持为分类器的值域，archived_bytes_deleted 放进一个同法的并列封闭枚举（生产者 C_BUILD_3），A1/AX 的 archive_code 接受并集。改的是字段值域而不是枚举成员，同样是 R4 级，不一定更轻，但枚举不必「对自己说一句 EITHER/OR」。列为选项，不是推荐换。

### 二 见 HIGH-3。

### 三 映射层会不会变成第二份不变量实现

它只在一个地方有牙：A1 之后接受 A2 行的那一刻。

- [复现] A2 是手工追加的治理行（actor "main agent"，NUMBERED），运行时规划器从不规划 A2；plan_next_short_id 签名 `(from_short_id, *, outcome, commit_changed)` 看不到 archive_code——块 MECHANISM 这句准确。

所以「唯一出口 AX」实际是登记解析器上的一条按 A1 行 archive_code 取值的**条件边**规则。漂移风险真实存在于两处：解析器自己写死而不读 contract 的映射；将来的 A2 校验器另做一遍「这个 A1 可否恢复」。本仓的解法已有模板——数据在 contract + 一个访问器 + 唯一消费者 + 一个断言消费者读数据的测试（ROUTER_OF/router_of、CHECKPOINT_OF/gates_at）。

- [复现] FORBIDDEN_EDGES 是无条件二元组，表达不了条件边；这会是第三种边策略机制。可接受，但要声明。

建议：块里加 `CONSUMER=` 与 `GUARDED_BY=`，否则映射只是声明。

### 四 A2 校验器

**没读到，也不能自己找**：包让我「去读那个校验器」但没点名它，而 §0.1 禁止我找。

受审集内：A2 的七个必填字段只按名检查（PlannedEvent.__post_init__，runner 675–696 行）；没有任何代码计算或核验 source_and_archive_exact_inventory_match / per_file_sha256_match 的取值。所以就手边证据而言，上一席位的「条件推论」所条件的，是一个存在性本身未证的校验器。

另外，§3-4 的前提略有过度：即使某个校验器覆盖整个归档库，也不能让「S001 已恢复」对另一个 run 的丢失为真——校验器范围决定的是**机制**是否已存在，不是**规则**是否必要。若它已在解析器里实现，块 §3 的映射就是重复实现（正是第三条的漂移）。所以三、四是同一个问题，答案在同一个文件里。§7 索要。

## 4. 必答问

**Q1** 成立：一（有条件，见 §3 一）、三（作为要求而非反对）、四（作为索要）。想多了：二的「决定性」——结论可保，论证要缩。

**Q2 声称宽于证据的地方**

1. 块 §3 无保留地写「A2 asserts … for THIS run's copy」；修订 §4 自己标它是条件推论。批准的是块，不是 §4。[复现] 字段名里没有历史归档的槽位，所以推论有依据；但 "asserts for THIS run's copy" 是对字段名的解读，没有代码支撑。
2. runner 885–886 行仍写「The row cannot be written」；上一席位 Q1-A1 已指出、builder 已认，但只改了 A2 出口句。[复现] PlannedEvent 能构造 archive_code='definitely_not_a_code' 的 A1 与 AX——受审集内**没有任何行级成员校验**；今天挡住这个码的只有链路那一行 elif 与计数测试。
3. 修订 §1「由测试复核」——本机默认环境下不成立（HIGH-2）。
4. 包 §2「错了两次」——builder 当天自己的 SEAT_RESULT §4 列了四处，全是同一类。
5. 修订 §0「逐字」是译文。
6. 交接引用「包 §5 的必答五问（Q5…）」——包 §6 只有四问，没有 Q5；§5 是复现命令。

**Q3 未写出的后果**

1. 双码并发（HIGH-1）。
2. 后继 run 的基线：A1→AX→F3→T1 后，S002 的 archive_before 由调用方在**丢失之后**的归档上取（chain 148–153 行：before/after 是调用方提供），run_c_build_3 看不到再丢失，S002 可在历史损失未处置时到 P4。SEAT_RESULT §3.4 已点到「保留原始见证」，块里没有对应条件。建议作为该码 AX 裁定的附带条件：后继开跑前 aaron_ruling_doc 须记录处置或接受。
3. AX 必填 aaron_ruling_doc：Aaron 仍在环内。修订带来的是 A1 可被运行时立刻登记，不是自动化。
4. 接线大概率会重现 BD-5 形状的 diff（Router B 加第三个输入，或 Router C）。裁定之后这是合法的；审的人别把它当成被收回的排除法回潮。
5. AX / F3 / T1 是 NUMBERED 行。这是否触动任何曝光记账，我不能也不应推断；只标出来。
6. 块内 `STATUS=PROPOSED  (not approved; nothing implemented)`（修订 43 行）在哈希覆盖范围内。批准并实现之后，被批准的字节永久自述「未批准」；改这一行就换哈希。R3/R4 先例块是否把 STATUS 放在块内我没核（§7）。建议在 Aaron 哈希前把 STATUS 移出块，或在批准语里明写「所批哈希含一行 PROPOSED」。
7. INVARIANT_AFTER 没说 C_BUILD_3 的另外两个码（local_seal_absent / local_seal_mutated）为何不入枚举（它们走 Router B 的 local_seal_failed，chain 69–72 行）。写一句，免得枚举向「所有 C_BUILD_3 码」漂。
8. 命名刻意与 C_BUILD_3 的码同拼——好处 builder 说了；代价是两套词表从此共享一个名字，任何断言两者不交的测试会破。

**Q4 批准前必须弄清**

1. ARCHIVE_CODES 成员资格在行级到底由谁执行（解析器？还是只有计数测试）。这决定 §2 第一件是一行改动还是要动解析器，也决定「封闭」到底封在哪。
2. §D.3.2 P4 原文是否含生产者不变量（§3 一）。
3. 双码优先级（HIGH-1）。
4. A2 校验器是否存在、在哪、看什么（§3 四）。
5. STATUS 行在块内的处理（Q3-6）。
6. 后继基线条件（Q3-2）。
7. 验证守卫的编码问题修好、复现命令补 env 说明，再交给任何人「按 §5 复现」。

**Q5（按交接措辞：裁定落地前维持 fail-closed 是否安全）** 安全，三个附注。

- [复现] 拒绝在 Router B 上游（chain 212–225）；未知 C_BUILD_3 码同样拒绝（226–231）；Router B 对 archive_ok 返回 P4（我调用测得）——所以那一行 elif 是本案与静默 P4 之间**唯一**的东西；本构建无任何代码追加登记行；生产入口在此之前就拒绝（runner 1096–1169）；守卫测试钉着 5。
- 附注 (1) 拒绝发生在归档尝试之后，不撤销损失、不登记任何事（SEAT_RESULT §3.4 已说）。
- 附注 (2) 单行守卫——时刻 3 的任何重构都要保住它；我读的两个测试里没有「链路对该码具名拒绝」的断言，若仓内也没有，建议补一条（不归我写）。
- 附注 (3) 若真实 run 撞上，状态是「无事件」的悬空 P3，CR1 不适用（无崩溃），解开只能靠人工裁定——这正是本修订存在的理由，所以「安全维持」不等于「可以搁置」。

## 5. 建议（不是裁定）

现字节暂不建议 Aaron 哈希批准；先补：HIGH-1 优先级、INVARIANT_SOURCE、块 §3 措辞收敛或先读校验器、CONSUMER/GUARDED_BY、STATUS 出块、后继基线条件、守卫编码修复。这些都不改变乙的方向；它们让乙写得住。

Aaron 也可以选择按现字节批准并把以上作为实现条件——那是他的权衡。我只指出 HIGH-1 是块所声称性质本身的洞，不是实现细节。

若要用审计词汇：这是**建议层面的 HOLD**，不是裁定。本文件的任何 PASS/HOLD 都不等于 ①（何时读真实 Development 数据）的任何决定。

## 6. 低严重度

- LOW-1 交接文件不在 ARTIFACTS_UNDER_REVIEW.json（包称其「必须同行」，注册表规则要求 delivery 文档携带禁读清单——它正是载体）；pin 后 14 分钟在 2fbdc16（16:04）被改 21 行；文件头 UPDATED=2026-09-02 已过期。Aaron 给的哈希与磁盘一致，本次传输没问题；但冻结守卫测试保护不了它。
- LOW-2 交接「必答五问 / 包 §5」vs 包 §6 四问。
- LOW-3 包 §2 少算两处（按 builder 自己的记录）。
- LOW-4 「逐字」是译文。
- LOW-5 包 §5 第 4 条裸命令不可运行。
- LOW-6 test_every_ruled_archive_code_is_reachable_and_routes_to_a1 只覆盖 5 码中的 3 个（file_unreadable、file_digest_mismatch 未测），测试名比内容宽。不在本次范围，顺带记下。

## 7. 向 Aaron 索要（我不能自己找）

按精确路径给我、附 sha256，我复算后再开：

1. src/itsf/mc/supplement_registry.py —— 行级 archive_code 校验；A1→A2 边校验；「A2 校验器」若存在最可能在此。
2. src/itsf/mc/day_strata_pipeline.py（至少 run_c_build_3 与其 failure 类型）—— 产出该码的条件；能否与 archive_failed 并发。
3. src/itsf/s0/runinfra.py 中 archive_sealed_run 与 ArchiveReport —— 报告在既有字节被删时是否仍报 archive_ok（修订 §2 的前提）。
4. ops/DECISION_PACKET_N00_AND_ND1.md 的 §D.3.2 P4 与 A1 原句（摘录即可）—— §3 一。
5. R4 先例块（ops/R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md 的 BEGIN/END 之间）—— STATUS 是否在块内。
6. 若仓内已有「链路对 archived_bytes_deleted 具名拒绝」的测试，其路径。

这些都不在 carries_outcome 清单上；我仍按 §0.1 不自取。给了 1–3 我能关掉 §3 三、四与 HIGH-1 的 [推断] 标签；其余是块措辞问题，builder 一句话也能答。

## 8. 本文件的去处

本席位只读，未写入仓库。本文件位于仓库之外（Desktop），sha256 见交付消息。若要入仓，由 Aaron 或 builder 复制到 ops/ 并登记——与上一轮 SEAT_RESULT 的做法一致。
