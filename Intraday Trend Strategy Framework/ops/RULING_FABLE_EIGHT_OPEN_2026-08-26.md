# 八项待裁 —— Fable 决裁席裁定全文 ＋ builder 审核

```
RECORD_TYPE=DELEGATED_RULING
DECISION_ID=dec-eight-open-2026-08-26
RULED_BY=Fable 5（决裁席，2026-08-26），fresh top-level session
DELEGATED=YES —— Aaron 2026-08-26 明示：「fable将会替我做选择，把这八项都交给fable」
ADOPTED_BY_AARON=YES —— 2026-08-26：「你审核一下，就让fable推荐的做」
SEAT_STATUS=BLIND（席位自评；边界事实见 §一.0，终分类归 Aaron）
WORKFLOWS_USED=0/3
OUTCOME_CLEAN=是（机械扫描；本件永不进入 carries_outcome）
```

> **来源与哈希的诚实说明。** 本裁定**经聊天送达**，不是以磁盘文件交付的。按常设
> 传输规则「聊天携带的字节永远不是真相源」，本件记录的 SHA256 证明的是**本次转录
> 的字节**，不是某个原始文件。若与 Aaron 手上的原文不符，以原文为准并在本件下方
> 追加更正，**不改上方**。

---

# 一、Fable 返回原文（逐字）

## 一.0 开工前的席位披露（Fable 主动申报）

> 开工前如实披露（供席位轴分类）：为定位本提示文件（我的工作目录是 Desktop，不在
> 仓内），我在读到本提示的约束之前做了三次定位操作：① 一次全仓文件名 glob 搜
> `PROMPT_EIGHT_OPEN_FABLE.md`（超时，零返回）；② 列出 `Quant trade\` 顶层目录名；
> ③ 列出 `ops\PROMPT*` 文件名（返回两个文件名，其中含 `PROMPT_D3_SOL_REVIEW.md`）。
> 全部只触文件名，未读任何文件内容，未命中任何隔离内容。读到禁令后零检索。
> 自评 `SEAT_STATUS=BLIND`，边界事实如上，终分类按惯例归 Aaron。

**传输核对**：本件 line 71 freshness marker 匹配；`git log ce378c8..HEAD -- <十路径>`
为空；十件 SHA-256 与字节数逐一全部匹配。**PASS**。

**Fable 自陈亲验的代码事实**：actor 表五行 P3/P4/A1/F1/F2 = `main agent
(mc_ds_runner)`（`supplement_contract.py:238-276`）；`plan_failure_event` 硬编码
ACTOR_RUNNER（`supplement_runner.py:663,671`）；S0 运行器在 P3 后存活时自写 `FAILED`
（`runner.py:725`）；recheck→mkdir→append 三步分离（`runner.py:766-774`）；writer 为
无锁 `open("a")`（`runner.py:1388-1396`），docstring 自称 MAIN-AGENT owned 而调用点
actor 写 `main agent (s0_real_run)`（`s0_real_run.py:3136-3139`）；
`REGISTRY = REPO/ops/TRIAL_REGISTRY.md` 在 OneDrive 树内（`s0_real_run.py:40`）；
`run_supplement_production` 默认拒绝（`supplement_runner.py:935`）；never-re-read 靠
prepared object 结构＋注释＋一条局部 AST 钉（`s0_real_run.py:2986-3004`）。
**另一条 Fable 自己发现的图上事实**：F3 的 predecessors 不含 P3
（`supplement_contract.py:286`），所以悬空 P3 链在现行词表下根本无法合法闭合——
硬崩溃状态机不是「不完善」，是**结构性缺失**。

## 一.1 八项裁定（逐字）

```
ITEM=1  TITLE=全局 L6「append every exposure event」限缩到研究轴——批准/驳回/改写？
RULING=改写措辞（方向上批准限缩，但不以裸限缩形式落地）。两轴量纲不同已被本送审集
  机械证实（迁移恒等测试＋恰一行不变量＋席位烧毁不耗研究自由度三重错）。裸限缩的风险
  是被读成「席位事件可以不记」；改写形保住 L6 的 fail-closed 内核。建议句（终稿归落地时）：
  「Exposure：研究轴暴露事件逐条 append 到项目 ops/EXPOSURE_LEDGER.md（append-only），
  即使 N_trials 不动也要记；复审席位轴暴露事件逐条 append 到项目
  ops/REVIEWER_EXPOSURE_LOG.md（append-only），席位烧毁不消耗研究自由度、不入研究台账。
  两轴分账：任一轴无记录 ⇒ 该轴 UNKNOWN，绝不为 NONE；无法归轴的事件 fail-closed 记入
  席位台账并标 PENDING_AARON（先例：席位台账第 3 行）。qros-state.yaml 的
  outcome_exposure.scope 必须同时点名两份台账。」
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：Aaron 对全局常设文件（~/.claude/CLAUDE.md L6 段）修订的明示授权，以决策记录
  append 形式（L6 权威文本若要正式修，走其 ratification 记录的 append 通道）。批准前
  过渡形＝前席已裁的「临时生效」：席位台账＋discoverability 守卫已保证 no-record⇒UNKNOWN
  不被触发，方向 fail-closed。
CONDITIONS=
  1. 落地文本必须保住「任一轴无记录⇒该轴 UNKNOWN」与「不可归轴⇒席位台账+PENDING_AARON」
     两个 fail-closed 子句，不得只落限缩半句（Aaron 决策记录+落地者）。
  2. 两份台账字节、迁移恒等测试语义、恰一行不变量零改动；
     tests/test_exposure_discoverability.py 保持绿且语义不动（builder 核验）。
  3. 决策记录记录改写后句子的逐字终稿，不是「已批准」三个字（Aaron）。
FALSIFIER=新措辞生效后任一会话按文档化程序查询暴露状态仍答错（席位台账有行却自陈 NONE，
  或一次研究轴暴露因被读成「只记席位」而漏账）⇒ 措辞失败，回退未限缩读法并重裁。
COLLATERAL=动：全局 CLAUDE.md L6 exposure 句（经授权后）、L6 owner-decisions 记录
  （append）、qros-state.yaml scope 措辞。不得动：两份 EXPOSURE_LEDGER.md、
  ops/REVIEWER_EXPOSURE_LOG.md 既有行、tests/test_exposure_ledger_migration.py 不变量、
  L6_RUNTIME_SPEC.md 已批准字节。
CONFIDENCE=HIGH——轴分离由送审集内三条机械不变量直接强迫，唯一自由度是措辞，而两轴
  fail-closed 措辞严格安全于裸批准与驳回两个备选。
```

```
ITEM=2  TITLE=D-2 S1(a) 迁移 carries_outcome 至单一隔离子树＋注册表 carve-out——做/不做/(b)单独成立？
RULING=做 S1(a)，carve-out 以外科形授予——但对它买到什么说老实话：三个席位死于三条
  不同通道（导航引路、广域符号搜索、定向 grep），每次缓解都是对上一条通道的追认；物理
  归拢是零 checkout 之外唯一与通道无关的缓解，且换来一条可机械排除的单前缀
  （ops/outcome_quarantine/**）替代必须保持同步的 12 路径清单。它买到的是导航安全与
  机械可排除性；**它不使仓内裸检索变安全**（子树仍在树内），所以 S1(b) 检索禁令永久
  在 force，不是过渡措施。carve-out 外科形：允许编辑 path 字段以追踪物理迁移；条目
  身份与 carries_outcome 状态永存；经编辑删除条目仍不可能。第 4 行（四件缓解就位后
  首个未烧席位）不足以证明 (b) 单独够用——三烧一活不是统计证据，且第 4 席是 packet
  喂给的 PULL 席，现行栈未经受过自行定位型席位的考验（我本席的定位披露就是这个形状
  的活例）。席位烧毁一次性不可逆，不允许单层防线——前席此理由我独立复核后认可，
  依据是证据，不是它的席位。
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：Aaron 对 (i) 注册表 path 字段编辑（carve-out 的行使）与文件迁移的明示执行授权；
  (ii) 确认 08-25「Sol 返回前不推进」hold 不覆盖本项或已随 Sol 返回失效（D-2 条件 5，
  含糊取限制性读法）。过渡形＝现状 (b)＋S2，第 4 行显示其在运转。
CONDITIONS=
  1. carve-out 文本（Aaron 记录）：path 编辑=追踪迁移，条目永不因此离开；守卫测试断言
     迁移 commit 前后条目数不减、每条旧路径的条目以新路径持同一注册身份存续（builder）。
  2. 迁移逐文件字节保持（SHA-256 前后一致），单 commit 完成；主计划只准 append 横幅
     （builder）。
  3. 全仓引用清点由已暴露的 builder 执行；隔离交集守卫与冻结守卫改指新前缀，并对漏迁
     残留证红（变异测试，沿 test_delivery_names_no_quarantined_path 先例）（builder）。
  4. RECOVERY_ANCHOR.md 追加一行前缀规则：ops/outcome_quarantine/ 下一切路径关闭；
     注册表仍是权威，前缀是便利不是替代（builder）。
  5. S1(b) 检索禁令在迁移后永久保留，明写不许因迁移而放松（builder 落地，Aaron 记录）。
FALSIFIER=迁移落地后再发生一次经导航/列目录的席位暴露 ⇒ S1(a) 未达目的，按 D-2 既定
  终点升级零 checkout 复审。反向：若哈希保持迁移无法不削弱任何守卫地实现 ⇒ 回落
  (b)+S2 单独成立，绝不以削弱守卫为代价（继承 D-2 反向条款）。
COLLATERAL=动（经授权后）：12 条 carries_outcome 路径物理位置、
  ops/OUTCOME_CARRYING_ARTIFACTS.json path 字段、两条守卫测试、ops/RECOVERY_ANCHOR.md
  （append）、全仓旧路径引用。不得动：被迁文件内容字节、注册表条目数与隔离状态、
  主计划既有字节、两份 EXPOSURE_LEDGER、席位台账既有行。
CONFIDENCE=MEDIUM——方向证据充分（F1/F5 证明检索通道真实），但「仓内迁移相对 (b) 的
  增益是否值得触碰永久隔离语义」是真判断题；我按不可逆损害的纵深原则取了做，
  并把「它不使检索变安全」写死进条件以防止其被高估。
```

```
ITEM=3  TITLE=D-4 运行时工作项：_SAVE_DIR 配置化何时做、认证深度、过渡形 B 维持多久？
RULING=时点：下一个 Aaron 开启的维护窗，并以「先于第一个 GRAD pilot 完成」为目标排序——
  理由：pilot 恰恰要签发 packet，每次签发都踩偏离的手工搬移＋correction 追加，pilot 中
  误建 <repo>/runs 会当场打红两条 R5 守卫、污染 pilot 本身；先修再 pilot 的风险小于带伤
  pilot。认证深度：机器检查先行（全套 923+ 测试、22 conformance、25 render-checks＋
  条件 4 新增覆盖），然后一轮 fresh Sol 认证（High）——不取零轮（M15-1 零轮先例是
  零生产实例缺陷；本项动的是每次复审都要过手的 packet 渲染语义），不取多轮（改动加性、
  默认值不变、falsifier 明确）；Sol HOLD 则按既有 repair-loop 先例走。B 维持到 A 落地
  且 conformance 通过之日为止——按事件失效，不按日历；A 落地当日 ITSF 切换配置并向
  偏离记录 append 一行闭合。
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：Aaron 开启维护窗（D-4 条件 5 的定义性要求）。开窗前过渡形＝B（已受裁批准，
  继续有效）。
CONDITIONS=
  1. 实现严格按 D-4 条件 1-4：默认恒 "runs/packets"、项目级持久配置（注册表条目或
     qros-state.yaml 字段）、环境变量禁用、REQUIRED SAVE PATH 渲染生效路径、
     conformance/render 增配置路径用例（builder，窗内）。
  2. 一轮 fresh Sol 认证（High）过 diff＋证据；HOLD 走 reproduce-first 修复环
     （Sol；Aaron 终裁）。
  3. A 落地日：ITSF 配置指向 ops/packets，实跑一次 `qros packet` 验证渲染路径，
     RUNTIME_DEVIATION_PACKET_SAVE_DIR.md append 闭合行（builder）。
  4. 排序保护：pilot 不得在窗中途开始——窗完成或回滚后才开 pilot；若 Aaron 先开
     pilot，则 A 顺延至下一窗、pilot 照常在 B 下进行（pilot 不被本项阻塞）（Aaron 排程）。
FALSIFIER=配置化后任一项目出现生效 saved_path 与实际存放分叉 ⇒ 回撤配置项重设计
  （继承 D-4 falsifier）；或窗内改动需要**削弱**（而非扩展）任何既有测试/守卫 ⇒ STOP，
  按 D-4 反向条款处理。
COLLATERAL=动（开窗后，qros-runtime 仓）：qros_runtime/packet.py:64 _SAVE_DIR 及渲染处、
  conformance/render 覆盖、注册流程说明；ITSF 侧配置字段与偏离记录（append）。不得动：
  tests/conftest.py R5 守卫、test_s0_runner 两条 runs 断言、<repo>/runs 禁令、
  既有 PACKET_ISSUANCE 记录。
CONFIDENCE=HIGH——A 本身已裁，剩余三问都有明确的不对称性（pilot 摩擦>窗风险；
  packet 渲染语义值一轮 Sol；B 按事件失效不留悬空），且条件 4 给了排序失败的安全回退。
```

```
ITEM=4  TITLE=actor 是否同时表达实际执行者；若否，是否增加独立 executor provenance？
RULING=是——已批准 actor 字串本就是复合的「权限 (工具)」token，同时表达两者，故不增
  executor 字段、不改六格行契约。四个独立数据点全在送审集内：表内 `main agent
  (mc_ds_runner)`、planner 硬编码、S0 调用点 `main agent (s0_real_run)`、writer
  docstring「MAIN-AGENT owned」与调用点的分工。括号外=权限归属（主代理），括号内=
  执行追加的工具。**本解释双向绑定，这是它的牙齿**：字串点名执行者，则执行者必须
  与字串相符——主代理代写却标 runner 是契约违规，不是标注弹性。这与 Sol ⑤ 的窄解释
  同向，并把它落成可测试的不变量。不新增字段的理由：ROW_CELLS 六格契约被既有 parser
  与测试钉死，改 schema 触及已批准语法；note 字段可携带附带 provenance 无需改约；
  且 provenance 字段解决不了 Sol 指出的任何安全问题（带 PID 戳的无锁 writer 仍是
  无锁 writer）。
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：仅 Aaron 决策记录 append（记录本解释逐字）。无执行动作存在。
CONDITIONS=
  1. 解释逐字入 Aaron 决策记录，杜绝重复争论（Aaron）。
  2. 未来 MC 执行路径落地时，增加测试断言：每条被追加行的括号内工具名 == 实际执行
     追加的注册入口名（builder，届时）。
FALSIFIER=出现一个正当治理需求，要求两个不同进程合法地以同一工具名写行（如恢复代理
  补完运行器的行）⇒ 复合读法不敷用，重开 executor 字段议题。注：第 6 项的恢复事件
  用独立事件类型＋main agent actor，特意避开了这个冲突。
COLLATERAL=动：决策记录（append）；届时新增一致性测试。不得动：supplement_contract.py
  的 ROW_CELLS 与 EVENTS 表、plan_failure_event、s0_real_run.py 先例代码。
CONFIDENCE=HIGH——四个数据点同向且全部经我亲验；备选（加字段）代价实、收益空。
```

```
ITEM=5  TITLE=保留 A1/F1/F2 的 runner actor，还是修订已批准 profile/planner/生产先例？
RULING=保留，零修订。已批准表的切口是「观察者是否存活」：运行器存活捕获的失败
  （A1/F1/F2）归运行器，运行器已死后才发生的（A2/AX/F3）归主代理——原则自洽、已实现、
  且被 S0 先例逐字印证（runner.py:725 的 FAILED 正是存活运行器在异常路径里写的讣告；
  门失败≠进程死亡）。**前一个 Fable 提案的失败事件半边（「运行器永不写自己的讣告」）
  在此被明确否决：Sol 是对的**，那句话只对硬崩溃成立，而硬崩溃是第 6 项。提案的 P3
  半边存活，但其存活理由是它与已批准表本就一致，不是提案的新贡献。plan_failure_event
  的 ACTOR_RUNNER 硬编码维持；S0 先例本就合规，无须「规整」动作。
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：仅 Aaron 决策记录 append（记录「观察者存活」切口为受裁原则）。本项是零改动裁定，
  无执行动作存在。
CONDITIONS=
  1. 「观察者存活」切口入决策记录（Aaron）。
FALSIFIER=出现真实的捕获型失败案例，其中运行器虽存活却不能安全追加（失败恰恰发生在
  registry 写路径本身）且不能按 S0 的 HALF_TRANSITION 标记＋bootstrap 检出模式处理
  ⇒ 该失败类需要主代理后备事件，重开本项。
COLLATERAL=动：决策记录（append）。不得动：ND1 profile、EVENTS 表、plan_failure_event、
  S0 先例代码。
CONFIDENCE=HIGH——文本与代码双重直接证据；Sol 与 builder 独立同向；我的同意给的是
  证据，不是任何席位。
```

```
ITEM=6  TITLE=P3 后硬崩溃应产生什么事件、由谁追加、恢复写入的授权条件？
RULING=采纳 Sol 窄解释并给出具体形。四条：
  (1) 崩溃时刻按定义零事件（无存活写者）；链尾悬在 P3。
  (2) 检测 fail-closed 于每次 bootstrap：链尾为 P3 且无后继 ⇒ 拒绝该 supplement_id
      的一切新工作，并拒绝 MC 生产入口整体，直至裁定。悬空 A1 不需要新机制——A1 的
      后继 A2/AX 本就是 main agent 事件，现行词表已可闭合。
  (3) 裁定事件：**新增一个 ratified 事件**（工作名 CR1 / SUPPLEMENT_RUN_CRASH_RESOLVED，
      终名归 profile 修订），NUMBERED（治理动作，同 A2/AX），actor=main agent（按第 4
      项，主代理确为执行者），incident_required=YES，required_fields ⊇ {supplement_id,
      dangling_event, incident_id, crash_evidence_summary, recovery_authorization_doc,
      registry_intact_verification}，predecessors={P3}，successors={F3}；并入
      FORBIDDEN_EDGES：(CR1,P4)、(CR1,P5)——崩溃裁定永不复活运行。走 A1→A2/AX→F3 的
      trap 模式先例。**为什么必须新增而不是复用**：我亲验 F3 的 predecessors 不含 P3
      （supplement_contract.py:286），悬空 P3 在现行图上无合法闭合路径；复用 F2 则
      违反第 4/5 项的 executor 绑定。缺口是结构性的，Sol 发现 3 成立。
  (4) 恢复写入的授权条件：逐事件、逐 incident 的 Aaron 明示授权，记录于行内
      recovery_authorization_doc 所指文档（复用 A2 的字段模式）。恢复写入永不自动
      ——与第 8 项同一纪律。
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：ND1 profile 的 R3 修订须 Aaron ratify（已批准工件，常设规则）；建议修订案与第 8
  项捆绑走「提案→fresh Sol→Aaron」三步（MC-REG-COLLISION-001 先例）。过渡形＝现状：
  MC 生产路径不存在（run_supplement_production 默认拒绝），无物可崩，本缺口今日不
  阻塞任何事；但它是未来 MC 执行路径落地的**前置条件**，列入 D-3 重启时的建造义务。
CONDITIONS=
  1. 悬空 P3 的 bootstrap 拒绝必须先于任何 MC 生产执行路径落地，且经变异测试证红
     （builder，届时）。
  2. 修订案复用 A2 的 recovery_authorization_doc 字段模式（修订起草者）。
  3. 任何形式的自动恢复均禁止（连接第 8 项）。
FALSIFIER=真实事故显示悬空 P3 拒绝以裁定无法快速解除的方式楔死整个 registry（阻塞
  无关 supplement_id）——D2 h1 楔死先例证明此形状真实存在 ⇒ 拒绝范围（per-id vs 全局）
  需重设计；我有意取偏楔死的一侧（per-id + MC 入口整体 fail-closed），此偏向可由
  Aaron 回调。
COLLATERAL=动（经三步流程后）：ND1 profile（R3 修订）、supplement_contract/_runner 对应
  实现与测试、bootstrap 悬链拒绝＋测试。不得动：既有事件语义、TERMINAL_SHORT_IDS/
  NON_TERMINAL_TRAPS 既有语义、F2/F3 既有行、S0 先例。
CONFIDENCE=HIGH（架构层：新事件＋fail-closed bootstrap＋逐事件授权）——缺口经我亲验
  为图上结构事实，形状严格沿用已 ratified 的 trap 先例；字段与命名细节归修订流程。
```

```
ITEM=7  TITLE=registry 是否允许继续在主动同步的 OneDrive 树中作为 canonical 写入面？
RULING=有边界地允许（Sol 备选 C 形），不迁出仓。**先说清最坏场景**：OneDrive 冲突
  解决可能把 canonical 文件静默回退到追加前版本、把追加挪进冲突副本——回退后的文件
  格式完好，fail-closed 解析抓不住它，链会授权第二次运行 ⇒ 双重暴露。这是本项唯一
  真正致命的通道（半写行会死在六格解析上，冲突副本文件会死在 git_clean 脏路径上，
  均 fail-closed）。不迁出仓的理由：registry 的 git 追踪是承重属性（git_clean 白名单、
  链解析、哈希入账、恒等迁移测试全部钉在仓内路径上），迁出制造双真相源，代价大于
  收益。边界四条（作为下一次真实运行之前的先决条件）：
  (1) 反回退见证：沿 post_run_started_hook 既有先例扩展——每次 registry 追加后把
      {sha256, 事件计数, 末行} 见证写到**非同步的 ruled 治理根**下（append-only）；
      每次 bootstrap 与 pre-exposure recheck 增加比对：registry 事件集不是最近见证的
      超集 ⇒「registry 回退」拒绝，STOP。
  (2) 冲突副本显式检测：bootstrap 对 ops/ 下 TRIAL_REGISTRY 冲突副本命名模式 glob，
      命中即拒绝（把 git_clean 的顺带覆盖变成点名守卫）。
  (3) 提交纪律：registry 追加与 git commit 作为一个操作步骤，最小化未提交窗口，
      git 历史作仲裁。
  (4) 文档化故障模型与恢复程序：检出回退/冲突 ⇒ STOP，据见证＋git 历史＋冲突副本
      裁定，修复写入按第 6 项纪律逐 incident 经 Aaron。
  两份 EXPOSURE_LEDGER 同处同步树，同一环境属性——建议同等见证待遇，此为建议非裁定
  （超出本项问句范围）。把仓整体迁出主动同步（L-5 的彻底形）仍向 Aaron 开放，
  本裁不预设。
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：Aaron 决策记录 append（记录「有边界允许」及四条边界）；条件 (1)(2)(3) 属 builder
  常权（新增 fail-closed 守卫，不削弱任何不变量），但见证目录若需在
  C:\Users\Aaron\quant-data\ 下新建，须按 ND1 先例走单独的目录创建授权
  （SEPARATE_DIRECTORY_CREATION_AUTHORIZATION）。本裁不解锁任何运行。
CONDITIONS=
  1. 四条边界全部落地并测试证红，先于下一次消耗 trial 的真实运行（builder；目录创建
     授权归 Aaron）。
  2. 见证机制自身 append-only、在非同步根、不成为第二权威——registry 本体仍是唯一
     canonical，见证只用于拒绝（builder）。
  3. 故障模型文档写明「检出即 STOP、修复须逐 incident 授权」，入 ops/（builder）。
FALSIFIER=发生一次见证机制未检出的静默回退（事后经 git 分叉或冲突副本发现）⇒ C 形
  不足，canonical 写入面必须迁出同步树（B 形），git 代价不再是抗辩理由。
COLLATERAL=动（记录在先，builder 常权）：bootstrap/recheck 守卫、见证写入（非同步根）、
  冲突副本 glob、故障模型文档。不得动：ops/TRIAL_REGISTRY.md 本体、两份
  EXPOSURE_LEDGER、registry 的仓内 git 追踪属性。
CONFIDENCE=MEDIUM——边界设计全部用既有先例件搭成、方向 fail-closed，但 OneDrive 冲突
  行为终究是无人对抗性测过的环境属性；我在用「检测」换「git 追踪」，残余的
  检出前窗口是真实的（见 STRONGEST_OBJECTION）。
```

```
ITEM=8  TITLE=租约回收能否自动执行，还是必须 fail-closed 等待人工裁定？
RULING=fail-closed，永远；自动回收否决。判据是不对称性：错误回收（双写者）损坏的
  是 append-only 治理账与暴露记账，不可逆；楔死的运行损失的是时间，可逆。PID/时钟型
  自动回收正是 Sol 列为未定义的失效面，在 Windows+OneDrive 语义下无法定义到本仓
  要求的确定性。栈内一切先例同向：P2 授权、HALF_TRANSITION 裁定、非终态 trap，
  全部 fail-closed 等所有者。回收动作本身=一次恢复写入，按第 6 项纪律逐 incident
  经 Aaron 授权。附一条防腐条款：fail-closed 不得沦为 fail-silent——租约设计（届时）
  必须让楔死的租约在每次 bootstrap 大声可见（点名持有者、时长、裁定程序），且裁定
  程序文档化到一行决策即可解除的程度；否则楔死会催生绕行文化，而绕行文化才是
  不变量真正的死法。
EXECUTION_UNLOCKED_BY_THIS_RULING=NO
  欠：无执行动作存在（租约本身尚不存在，§2.1 实测零命中）。本裁约束未来租约设计，
  随第 6 项修订案一并入记录。
CONDITIONS=
  1. 未来租约设计遵守：回收=恢复写入=逐 incident 授权；楔死状态 bootstrap 可见；
     裁定程序一行化（届时 builder＋修订流程）。
FALSIFIER=运营证据显示反复楔死（一个季度 ≥3 次陈旧租约裁定）且每次裁定同形零信息
  ⇒ 可重开一条**窄**自动路径（仅当持有者自己的持久崩溃标记——第 6 项的——证明其
  已死时），但该重开归 Aaron。
COLLATERAL=动：无。不得动：一切。
CONFIDENCE=HIGH——不对称性论证是决定性的，且与栈内全部既有先例同向。
```

## 一.2 跨项与席位陈述（逐字）

```
CROSS_ITEM_CONFLICTS=无矛盾。校验过的接缝：4（executor 绑定）与 6（主代理追加 CR1）
  一致——CR1 的 actor 与执行者同为主代理；5（观察者存活切口）与 6（死后归主代理）
  是同一原则的两半；6 与 8 共用「恢复写入=逐 incident 授权」纪律；7 的见证在非同步
  根，与 2 的隔离子树、3 的 runs/ 禁令零交集；1 的两轴分账与 7 的 registry 边界
  分属不同台账。八项合起来不解锁 D-3：HOLD 条件 3 继续在 force——生产代码在
  fresh Sol PASS＋Aaron 授权前不得获得任何 registry 写能力；重启 MC 需要按 4/5/6/7/8
  的裁定重写 D-3 提案并重走三步全程。
SEAT_INDEPENDENCE_CONCERN=我认为本席在第 4-8 项上给出了独立判断，依据：每一条裁定
  引用的是送审集内我亲眼复现的字节（含一条 Sol 与 builder 都没点名的图上事实——
  F3 predecessors 不含 P3），没有一条引用前席位的权威；且我在第 5 项明确否决了
  前一个 Fable 提案的失败事件半边，并写明「Sol 是对的」。结构性残余（同族裁同族）
  无法自证归零，如实报此，终判归 Aaron。
STILL_AARON_ONLY=
  1. 全部执行授权：第 1 项全局文本修订、第 2 项 carve-out 行使＋hold 范围确认、
     第 3 项维护窗开启、第 6 项 profile R3 修订 ratify、各项决策记录 append。
  2. 仓库整体是否迁出主动同步树（第 7 项的彻底形）。
  3. 席位台账第 3 行的终分类（PENDING_AARON）与第 4 行 NOT_EXPOSED 分类值的存废
     ——不在八项内，仍归 Aaron。
  4. GRAD pilot 排程及其与维护窗的先后（第 3 项条件 4 的两分支择一）。
  5. 本席开工前定位披露的席位轴分类（先例：第 3 行一行治理文本得 PENDING_AARON；
     本席仅文件名、零内容，我自评 BLIND，分类权不在我）。
STRONGEST_OBJECTION_TO_MY_OWN_RULINGS=最强的一条打在第 7 项：静默回退丢失 P3 追加
  的双重暴露窗口，我的见证机制只能在「下一次 bootstrap」检出，检出前窗口真实存在；
  B 形（canonical 迁出同步树）结构性关死该窗口，我以 git 追踪承重为由拒绝了它——
  若 Aaron 把双重暴露风险计为绝对不可接受，第 7 项应当被推翻为 B。次强打在第 2 项：
  仓内迁移不使检索变安全，S1(a) 的实际增益比字面小，(b) 单独成立是可敬的对立面。
SEAT_STATUS=BLIND（自评）——未打开任何隔离件；仅有的三次检索发生在读到本提示约束
  之前、为定位本提示本身、全部只返回文件名且零内容命中（逐字披露见文首）；读到
  禁令后零检索。边界事实全部如实在案，终分类归 Aaron。瞒报才是不可逆损失，故披露
  从宽、自评从严。
INDEPENDENCE_STATEMENT=按维度：
  · 会话独立性：新顶层会话，非 D-3 提案 Fable 会话的延续，非本仓任何工作会话的延续；
    本会话上下文含全局 CLAUDE.md 与持久记忆索引（其中有 ITSF 项目条目——治理状态
    指针，不含任何 outcome 数值与 D-3 提案内容），如实披露。
  · 隔离件：零打开。本仓内除本提示与表列十路径外零文件打开（含未开 RECOVERY_ANCHOR
    ——无需要）。
  · 检索：三次定位操作（文首逐字披露，均在读约束前、均仅文件名）；此后零检索。
  · 与 D-3 提案作者的关系：同模型族（Fable 5），不同会话；本轮否决了其提案的一半。
  · 数据与运行：零真实数据读取、零运行执行、零 registry/台账追加、零文件修改；
    workflow 用量 0/3。
```

**Fable 给工作会话的转录指引（逐字）**：本席只读不落仓。请将本裁定逐字节转录入项目
`ops/`（建议名 `ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md`），转录后重算并记录
SHA-256，机械扫描确认 outcome-clean 后再入登记；文首的席位披露段请一并转录，供
Aaron 作席位轴分类。八项中每一处 `EXECUTION_UNLOCKED=NO` 所欠的授权均已逐项点名——
在 Aaron 逐条 append 之前，一切维持各自写明的过渡形。

---

# 二、builder 审核 —— 逐条复现，不采信

`REPRODUCED` ＝ 我自己打开代码看到了同一事实。

## 2.1 全部引用属实，含 Fable 自己发现的那一条

| Fable 的断言 | 我的复核 | 结果 |
|---|---|---|
| F3 的 predecessors 不含 P3 | `supplement_contract.py:282-287`：F3 predecessors ＝ `("P1","P2","F1","F2","F2v","AX")`。**确无 P3。** 且 P3 的合法后继 `("P4","A1","F2")` 全为 `ACTOR_RUNNER` | **REPRODUCED** |
| actor 表五行 | 与我出包前实测一致 | **REPRODUCED** |
| `plan_failure_event` 硬编码 ACTOR_RUNNER | `supplement_runner.py:663,671` | **REPRODUCED** |
| `runner.py:725` 存活时自写 FAILED | 异常路径内，注释 `trial permanently consumed` | **REPRODUCED** |
| `runner.py:766-774` 三步分离 | recheck → mkdir → append | **REPRODUCED** |
| `runner.py:1388-1396` 无锁 writer ＋ docstring 冲突 | docstring 首句 `MAIN-AGENT owned`；`s0_real_run.py:3139` actor 写 `main agent (s0_real_run)` | **REPRODUCED** |
| `REGISTRY` 在 OneDrive 树内 | `s0_real_run.py:40` = `REPO/"ops"/"TRIAL_REGISTRY.md"` | **REPRODUCED** |
| `run_supplement_production` 默认拒绝 | `supplement_runner.py:935` gate-first | **REPRODUCED** |
| never-re-read 有「**局部** AST 钉」 | `s0_real_run.py:2989` 的 AST 钉覆盖的是 `resolved_study_config()` 等**配置**再解析，**不覆盖 REGISTRY 再读**（后者只有 `:3001` 的注释）。Fable 写「局部」是准确的 | **REPRODUCED** |
| Fable 点名的结构名真实存在 | `FORBIDDEN_EDGES`／`ROW_CELLS`／`TERMINAL_SHORT_IDS`／`NON_TERMINAL_TRAPS`／A2 的 `recovery_authorization_doc` 在 `supplement_contract.py` 中全部实有 —— **没有杜撰名字** | **REPRODUCED** |

## 2.2 一处需要更正的论证 —— **第 7 项的风险叙述少算了一条通道**

**Fable 写**：「半写行会死在六格解析上，冲突副本文件会死在 git_clean 脏路径上，
均 fail-closed」，并据此断定静默回退是「本项**唯一**真正致命的通道」。

**实测这半句不成立**：

- `parse_registry_events`（`s0_real_run.py:183-184`）对格数不符的行是
  **`continue`，不是 raise** —— 畸形行被**静默丢弃**。
- 且 `ops/TRIAL_REGISTRY.md` **被 clean gate 白名单豁免**
  （`s0_real_run.py:113`，用于 `:596` 的 `_clean_gate_exempt`）——registry 变脏
  **不会**打红 `git_clean`。

**后果**：一次把末行截断的半写，其可观测状态与静默回退**完全相同**——事件不见了，
文件格式完好，门全过。**所以致命通道是两条，不是一条。**

**但这不推翻裁定，反而加重条件 (1) 的分量**：反回退见证比对 {sha256, 事件计数,
末行}，**丢一行会让计数低于见证 ⇒ 同样被抓**。也就是说 Fable 的**药**覆盖了它
**病理描述**漏掉的那条通道。

**记在这里的原因**：将来若有人以「反正解析器会挡住半写」为由削减边界 (1)，那个前提
是假的。**边界 (1) 是这两条通道唯一的共同拦截点。**

**冲突副本那半句成立**：`_clean_gate_exempt` 只豁免精确路径
`ops/TRIAL_REGISTRY.md`；冲突副本是另一个文件名的未跟踪文件，会打红 git_clean。

## 2.3 我自己的流程缺陷，直接造成了 Fable 的三次定位检索

Fable 老实申报：为找到提示词文件，它在读到检索禁令**之前**做了三次文件名操作。

**成因是我的**：提示词与 `NEXT_HANDOFF.md` 里给的都是**仓相对路径**
（`ops/PROMPT_EIGHT_OPEN_FABLE.md`），而决裁席的工作目录在 `Desktop`，**不在仓内**。
**一个必须先被找到才能读到「不许找」的文件，本身就是设计缺陷。**

三次操作只触文件名、零内容命中，代价这次为零。**但它正是第 2、3 席位被烧的同一
形状**——检索先于约束。已修：交付说明改带**绝对路径**，见
`ops/NEXT_HANDOFF.md`「交付前 builder 必须做的」新增条目。

## 2.4 与 Sol 的关系

第 5 项**明确否决**了前一个 Fable 提案的失败事件半边，并写明「Sol 是对的」——
这与我出包前的独立实测（提案 §2.5–2.7）同向。第 6 项采纳 Sol 的窄解释并补上了
Sol 与我都没点名的图上缺口。**同族护短的具体证据未出现**；结构性残余按 Fable
自陈保留，终判归 Aaron。
