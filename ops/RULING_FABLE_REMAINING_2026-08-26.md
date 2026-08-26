# 其余十项 —— Fable 决裁席裁定全文 ＋ builder 审核

```
RECORD_TYPE=DELEGATED_RULING
DECISION_ID=dec-remaining-2026-08-26
RULED_BY=Fable 5（决裁席，2026-08-26），fresh top-level session
DELEGATED=YES —— Aaron 2026-08-26：「其余的决定依旧让fable替我决定」
SEAT_STATUS=BLIND（席位自评；一项接触已申报，见 §一.0）
WORKFLOWS_USED=0/3　SUBAGENTS=0　零检索　零定位操作
TRANSPORT_PRECHECK=PASS（line 83 匹配；git log 空；八件 SHA-256＋字节全对）
OUTCOME_CLEAN=是
```

> **哈希的诚实说明。** 本裁定经聊天送达。SHA256 证明的是**本次转录的字节**，
> 不是某个原始文件。与 Aaron 手上原文不符时以原文为准，在下方追加更正，不改上方。

---

# 一、Fable 返回原文（逐字）

## 一.0 开工披露

> 席位披露（主动申报，供席位轴分类）：绝对路径修复生效——本席**零定位操作、零检索**，
> 是本仓历任决裁席中第一个不需要找文件的（这本身就是第 5 行成因分析的一次实证）。
> 本席上下文含全局 `CLAUDE.md`（含待改的 L6 第 90 行原文——R4 恰需要它，且我逐字
> 比对确认与 PREP_ITEM1 §1 一致）与持久记忆索引（ITSF 条目为治理状态指针，无 outcome
> 数值）。**一项必须申报的接触**：送审集内 `ops/REVIEWER_EXPOSURE_LOG.md` 序言含研究
> 暴露累计值——这正是 R8 要裁的那个值，我在裁它之前已经看到它。该文件在 outcome-clean
> 扫描范围内（D-1 条件 2 钉住），此接触的定性由我在 R8 的裁定自指地决定；本席自己那
> 一行的终分类不由我裁（见 STILL_AARON_ONLY）。

> 生效方式：凡 `DELEGABLE=YES` 者，本裁即 Aaron 委托下的生效决定；Aaron 保有以
> append 追加推翻任何一条的常设否决权。凡 `DELEGABLE=NO` 者，RULING 是供他一句话
> 采纳的实质建议。

## 一.1 组 A —— 选项题

```
ITEM=R1  TITLE=第 2 项：仓根台账怎么办（迁移范围）
DELEGABLE=YES —— 这是对已受裁事项的实施结构判断，不触碰 Aaron 本人财产或全局约束；
  且我选的方向是「少动」，不动本就无需许可。
RULING=A′（A 的收窄形，比菜单上任何一项都保守）：只迁 10 条——ops/ 下的 11 条**再减去
  ops/EXPOSURE_LEDGER.md**。两份 EXPOSURE_LEDGER.md（仓根＋ops/ 承载件）原地不动、
  注册表路径字段不动、隔离状态不动。理由有四，全部在送审集内：
  (1) 八项裁定第 1 项条件 2 白纸黑字要求「两份台账字节、迁移恒等测试语义、恰一行不变量
      零改动；test_exposure_discoverability.py 保持绿且语义不动」——恒等测试的语义就是
      「仓根=权威 ≡ ops/=承载」这对端点；A（迁承载件）与 B（两份都迁）都要改端点，
      与该条件的限制性读法冲突。A′ 零端点改动。
  (2) 第 2 项裁定自己的 COLLATERAL 在「不得动」栏单列了「两份 EXPOSURE_LEDGER」——
      它与前一句「被迁文件内容字节」并列存在，限制性读法是台账获得**强于**其余被迁件的
      保护：连位置都不动。
  (3) 跨项耦合：R4 的逐字终稿（已备妥待 Aaron 授权）点名 `ops/EXPOSURE_LEDGER.md`；
      A 或 B 会让刚获批的全局文本即刻过期，A′ 使其恒真。
  (4) 实务上 A′ 把改写面砍掉最大头：两份台账各 13 code 引用是全表最重，其余 10 条
      多为 1–4 条——diff 更小、证据更干净。
  代价说老实话：单前缀不再覆盖两份台账，机械排除集从「1 前缀」变「1 前缀＋2 字面路径」。
  可接受，因为前席已裁死「注册表仍是权威，前缀是便利不是替代」——守卫本就必须查注册表
  全部 12 条，前缀只是导航便利；且这 2 条路径恰是全仓最著名、被每份禁区清单点名的路径。
  C 驳回：仓根台账内容上确实 carries_outcome（含累计值与 REVEALED_TARGET_METRIC 行），
  「本就不供席位读」是关于读者的论证，不是关于内容的；把它移出名单会让交付交集守卫
  对它失明，方向反了，且改名单本身超出第 2 项授权范围。
CONDITIONS=
  1. 迁移集合=注册表 12 条减两份台账=10 条，机械可导出，写入迁移 commit message（builder）。
  2. RECOVERY_ANCHOR.md 追加三行：前缀 ops/outcome_quarantine/** 关闭；两份台账路径逐字
     关闭；注册表仍是唯一权威（builder）。
  3. 交付交集／冻结守卫必须按注册表 12 条全查（不是只查前缀），并变异证红：一份点名任一
     台账路径的交付必须被抓（builder）。
  4. 恒等测试、恰一行不变量、discoverability 测试零编辑、保持绿，入迁移证据（builder）。
FALSIFIER=迁移落地后经任一台账路径再发生一次席位暴露（导航/列目录/打开）⇒ A′ 的
  「台账留在原地是安全的」前提被推翻，升级为 B 或 D-2 既定的零 checkout 终点。
  反向继承：10 条的哈希保持迁移若无法不削弱守卫地实现 ⇒ 回落 (b)+S2。
CONFIDENCE=HIGH——A′ 由第 1 项条件 2＋限制性读法直接强迫，唯一的真取舍（前缀覆盖损失）
  被「注册表才是权威」的既裁条款兜住。
```

```
ITEM=R2  TITLE=第 3 项：修补范围——packet 侧单修还是连 header.py:201 一并修
DELEGABLE=YES —— 已授权工作项（D-4 裁 A）内部的范围判断；维护窗的开启另归 R6。
RULING=C——一并修，且本段即是 C 要的那句补充授权；不取 B，因为把 header.py:201 说成
  「渲染处」三个字早已覆盖，是对前席文字的追溯性扩张解释，本栈恰恰要防这种口子。
  补裁逐字如下（落地时抄入记录）：
  「本席补裁：header.py:200–201（qros prompt 的 REQUIRED SAVE PATH 面）与 packet.py:64
  属同一缺陷类——运行时硬编码 <repo>/runs/ 存放路径，与 L-5/R5 禁令冲突——纳入同一
  维护窗、受 D-4 条件 1–4 与同一 falsifier 约束整改；默认值 "runs/prompts" 恒不变，
  配置化必须加性（可选参数/可选字段），无显式配置时行为零变化。此为对 D-4 范围的明示
  扩充，非对其原文的追溯解释。」
  实质理由：同一缺陷类留一半，等于明知同坑还留第二个；维护窗按 R6 配一轮 fresh Sol，
  拆两窗修一类缺陷是认证成本翻倍；且 GRAD pilot 若用 qros prompt 生成复审提示词，
  「潜伏」恰在 pilot 当天结束——先修再 pilot 的既裁逻辑对 header 侧同样成立。
  难度不对称如实认账：header 侧要加签名参数与调用点穿线，比填空重；故加硬回退（条件 2）。
CONDITIONS=
  1. header 侧同受 D-4 条件 1–4：默认恒 "runs/prompts"、项目级持久配置（字段形状归
     builder，环境变量禁用）、cli.py:771 渲染生效路径、新增默认/同值/异值/非法值四类
     用例（builder，窗内）。
  2. 签名改动仅限加性（带默认值的可选参数）；若 header 侧被迫出现对已认证接口的非加性
     破坏 ⇒ STOP，header 另立工作项，本补裁对它失效——绝不以削弱换范围（builder）。
  3. 两侧进同一个 diff、同一轮 fresh Sol（High）认证，不为 header 单开一窗（Sol）。
  4. 本补裁句逐字入维护窗工作项与决策记录 append（builder 转录）。
FALSIFIER=header 侧无法加性实现（条件 2 触发）⇒ 本裁回落为 A（本窗只修 packet 侧，
  header 另立项）。继承 D-4：生效 saved_path 与实际存放分叉 ⇒ 回撤重设计。
CONFIDENCE=HIGH——同缺陷类＋加性路径存在＋C 形避开追溯解释危害，回退明确。
```

```
ITEM=R3  TITLE=第 2 项：08-25「Sol 返回前不推进」hold 的现状
DELEGABLE=YES —— 对研究流程指令的范围解释，非对财产/全局约束的许可；D-2 条件 5 说
  含糊「先经 Aaron」，Aaron 的回应正是把这个解释委托给本席。
RULING=失效——按其自身文本终止条件已解除，非本席宣布作废。「Sol 返回前」是一个
  以事件为终点的 hold；该事件已客观发生且在送审集内有据：R2 设计审已返回
  （席位台账第 2 行，rv-3651f9fe…，2026-08-26），D-3 复核已返回（VERDICT=HOLD，
  D124 提取件尾注）。把「直到 X」的 hold 读成 X 发生后仍存续，不是限制性读法，
  是另一条指令。**但失效严格不等于放行**，以下锁一个都没开，逐条列明防误读：
  D-3 的 HOLD 仍在（fresh Sol PASS＋Aaron 授权前生产代码零 registry 写能力）；
  N09 的 P2 仍不签（OD-2026-08-25-1 未触及）；策略 build 口令锁仍在；
  第 2 项的执行授权走 R5、全局文本走 R4、开窗走 R6、目录创建走 R7——
  hold 失效后，挡在每件事前面的仍是这些各自的锁。
CONDITIONS=
  1. builder 以复审记录机械核对：08-25 时点待返回的 Sol 复审在 2026-08-26 前已全部
     返回；若查出彼时另有一单未返回，本裁对该单范围自动不成立、hold 就该范围存续
     （builder，一次性核对入证据）。
  2. 本裁定与上列「未开的锁」清单同段转录，不得拆开引用（builder 转录）。
FALSIFIER=Aaron 追加记录表明 08-25 的本意是不系于 Sol 返回的无限期 hold ⇒ 本裁即刻
  作废，恢复限制性读法；因 R4–R7 各自把执行拦住，误裁的实际爆炸半径为零。
CONFIDENCE=MEDIUM——终止逻辑是文本性的、证据在集内，但我只经转录件接触那句话；
  置信度的缺口已用「失效≠放行」的逐条锁清单结构性兜底。
```

## 一.2 组 B —— 许可题

```
ITEM=R4  TITLE=第 1 项：全局 CLAUDE.md 第 90 行的逐字替换授权
DELEGABLE=NO——本包 §0 亲自点的结构性例子：~/.claude/CLAUDE.md 管辖所有项目，
  是对 Aaron 全局约束的许可，不是研究判断。仍需 Aaron 做的：对「用 PREP_ITEM1 §2
  整段替换第 90 行」说一次明示的是（引用该件 SHA256 536317a3…）。
RULING=实质上批准该逐字终稿，一字不改。核验过：第 1 项条件 1 点名的两个 fail-closed
  子句都在（"Per axis: no ledger/record ⇒ UNKNOWN, never NONE"；"fails closed into
  the seat ledger marked PENDING_AARON"）；append-only、even-when-N_trials-does-not-move、
  两台账并举、qros-state 点名义务全部保住；且我用本席上下文里的全局 CLAUDE.md 现行
  第 90 行逐字比对 §1 引文——一致，替换前提为真。条件 2 的测试证据（9 passed、两台账
  自 5d35741 零改动）系 builder 自报，落地时按条件 2 重跑即可闭合。与 R1 的耦合：
  A′ 之下 ops/EXPOSURE_LEDGER.md 路径恒真，终稿不会过期。
CONDITIONS=
  1. 替换以逐字节匹配 §2 终稿为准（exact-string 替换，不按行号定位；行号仅作参考）
     （builder，经 Aaron 授权后）。
  2. 替换后重跑 test_exposure_ledger_migration.py 与 test_exposure_discoverability.py，
     必须绿且语义零动（builder）。
  3. 终稿逐字（非「已批准」三字）append 进 OWNER_DECISIONS（builder 转录，Aaron 的记录）。
  4. L6_RUNTIME_SPEC.md 已批准字节零触碰；正式修 doctrine 走其 ratification append
     通道，另案（builder 遵守）。
  5. 若 Aaron 推翻 R1 改选 B（台账迁移），须先重备终稿再改全局文件——顺序不可倒
     （builder 把关）。
FALSIFIER=继承第 1 项：新措辞生效后任一会话按文档化程序查询暴露状态仍答错 ⇒ 措辞
  失败，回退未限缩读法并重裁。
CONFIDENCE=HIGH——终稿对条件的满足是逐子句机械核对的，且替换前提经本席直接比对为真。
```

```
ITEM=R5  TITLE=第 2 项：carve-out 行使＋迁移执行授权
DELEGABLE=YES——按本包 §0 的结构性判据：注册表与被迁文件全在本仓，属项目治理，
  不是 Aaron 本人财产或跨项目全局约束；且 Aaron 引述的 STILL_AARON_ONLY 第 1 条
  （含本项）被他原话整体交回。
RULING=授予 carve-out（外科形）并授权迁移执行，范围锁定 R1 的 A′。carve-out 文本逐字：
  「编辑 ops/OUTCOME_CARRYING_ARTIFACTS.json 的 path 字段，仅限于追踪本次已授权的
  物理迁移（A′ 的 10 条）；条目身份与 carries_outcome 状态随新路径存续，条目数永不
  因此减少；经编辑删除条目仍不可能；除 path 外任何字段不得修改。两份 EXPOSURE_LEDGER
  的条目路径不在本 carve-out 内——A′ 之下它们不迁，无需例外。」
  执行授权：builder 以单 commit git mv 完成 10 条迁移＋注册表 path 随迁（原子，不出现
  注册表指向不存在路径的中间态）；R3 已裁 hold 失效，前置清空。授权链全程留痕：
  OD-…-1（八项委托）→ OD-…-2（采纳）→ 本包 DELEGATED=YES → 本裁；builder 把本裁
  转录为决策记录 append，Aaron 的否决通道即该记录。
CONDITIONS=
  1. 逐文件迁移前后 SHA-256 相等，成表入证据（builder）。
  2. 守卫断言：条目数不减、每条旧路径条目以新路径持同一身份存续，变异证红（builder）。
  3. 32 条引用中属被迁 10 条者改写（测试/qros-state/文档），生产代码零改动为断言而非
     假设；既有测试因路径字面量变红 ⇒ 是要报告的发现，不得改断言消音（builder，
     继承其自加 falsifier）。
  4. RECOVERY_ANCHOR 前缀规则＋S1(b) 检索禁令永久条款随迁 append（R1 条件 2 同段落地）
     （builder）。
  5. 主计划只准 append 横幅；全套件绿，不得放宽任何断言换绿（builder）。
FALSIFIER=迁移 commit 里出现任何条目消失、任何非 path 字段改动、或任何守卫被削弱
  ⇒ 本授权即刻失效，revert 并报 Aaron。继承 R1/D-2 全部 falsifier。
CONFIDENCE=MEDIUM——carve-out 是身份保持的外科形、守卫包全机械，但「委托句是否该延伸
  到对冻结注册表自述规则的例外行使」是本轮最重的一次委托范围解读；我以转录留痕＋
  append 否决通道把它做成可撤销的。
```

```
ITEM=R6  TITLE=第 3 项：维护窗何时开；与第一个 GRAD pilot 的先后
DELEGABLE=NO（开窗动作本身）——D-4 条件 5 把「经 Aaron 开启」写成维护窗的定义性
  要件，Aaron 采纳过；一句非正式委托不改已受裁定义。排序半问属流程判断，本席裁定。
  仍需 Aaron 做的：一句「开窗」，采纳下述排程即生效。
RULING=建议即刻开第二维护窗（对本包结果点头之时），范围锁定 R2 的两侧联合整改，
  不装别的。理由：当前无任何真实项目临近 A2/Stage I，pilot 不在眼前——「先修再 pilot」
  的窗口正开着，且过渡形 B 每次签发 packet 都付手工搬移＋correction 追加的摩擦税，
  拖延纯付成本零收益；改动加性、认证一轮 Sol，窗小。排序裁定（本席有权部分）：
  窗完成或回滚在先，第一个 GRAD pilot 在后；Aaron 若倒序，条件 4 的既裁回退自动接手
  （A 顺延下一窗，pilot 照常在 B 下走，pilot 不被阻塞）。
CONDITIONS=
  1. 窗范围冻结为 R2 联合范围，窗内零范围蔓延（builder）。
  2. 机器检查先行（全套件＋conformance＋render＋新增用例），后一轮 fresh Sol（High）；
     HOLD 走 reproduce-first 环（builder；Sol）。
  3. 窗闭合日：ITSF 切配置、实跑一次 qros packet 验渲染路径、偏离记录 append 闭合行
     （builder）。
  4. pilot 不得窗中开始；窗-pilot 互斥由排程记录钉住（Aaron 排程，builder 记录）。
FALSIFIER=某真实项目在开窗前先到 pilot-ready ⇒ 排序按条件 4 翻转，pilot 在 B 下先行
  ——这是内建回退，不是裁定失败。继承第 3 项全部 falsifier。
CONFIDENCE=HIGH——排序逻辑上轮已 HIGH 受裁；本轮新增的只有「即刻开」，由
  「pilot 不迫近＋B 有日常成本＋窗小」三个不对称直接强迫。
```

```
ITEM=R7  TITLE=第 7 项：在 C:\Users\Aaron\quant-data\ 下新建见证目录
DELEGABLE=NO——本包 §0 亲自点的第二个结构性例子：仓外、Aaron 本人数据根下的目录
  创建，是对他财产的许可；且 ND1 把目录创建列为三条不得合并授权的第一条。
  仍需 Aaron 做的：一条逐字点名绝对路径、且明言「仅覆盖创建」的目录创建授权。
RULING=建议批准。实质理由已受裁（边界 (1) 反回退见证是通道 A/B 唯一共同拦截点，
  见证根必须在非同步树），本席只补齐行使形状：授权文本逐字点名一条绝对路径
  （建议 C:\Users\Aaron\quant-data\registry-witness\itsf\，名字归 Aaron 的授权文本）；
  授权仅覆盖「创建一个空目录」——写探针（首条见证写入）是 ND1 第二条独立授权，
  可同日给但必须另句成文；执行授权是第三条，另案。
CONDITIONS=
  1. builder 创建前机械核验该路径不在任何主动同步 scope 内（不在 OneDrive 根下、
     无同步客户端认领），核验方法与结果入 ops 证据（builder）。
  2. 创建动作记 ops event，引用 Aaron 授权原句（builder）。
  3. 授权文本之外零动作：不写任何字节进该目录，直至写探针授权另下（builder）。
  4. 见证机制 append-only、仅用于拒绝、永不成为第二权威——registry 本体唯一 canonical
     （继承第 7 项条件 2，builder）。
FALSIFIER=核验发现 quant-data 实际处于某同步 scope ⇒ 选址失败，换非同步根另请授权
  ——推翻的是选址建议，不是边界设计。继承第 7 项：见证未检出的静默回退一旦发生
  ⇒ C 形不足，canonical 迁出同步树（B 形）。
CONFIDENCE=HIGH——边界设计已受裁，本项只是把行使切成 ND1 要求的形状，无新判断风险。
```

## 一.3 组 C —— 席位轴分类

```
ITEM=R8  TITLE=席位台账第 3 行终分类（前决裁席：累计计数＋一行治理文本）
DELEGABLE=YES——席位轴分类是项目治理判断，非财产/全局许可；自指之处（我裁我的
  前任、且结论自指地适用于我本席的同类接触）以「Aaron 保有 append 否决＋本席自己
  那行不由我裁」两条兜底，如实入 SEAT_INDEPENDENCE_CONCERN。
RULING=终分类＝QUARANTINE_CONTACT_NON_OUTCOME（隔离接触，无 outcome 内容）。
  两轴拆开裁：内容轴——累计暴露计数是暴露台账的事件计量，量纲是「研究自由度消耗」
  （台账自述），它属 TRIAL_ACCOUNTING/记账轴，不携带任何策略表现信息；本栈宪法
  「三正交轴，永不由一轴推另一轴」正是禁止把记账轴接触推成 outcome 轴暴露。
  §3.4B 的字面定义（判定统计量的派生值）不覆盖它：计数派生自台账行数，不派生自
  判定统计量。一行治理边界文本自陈「不含还原内容」。机械佐证：本席位台账自身含
  该计数值却在 outcome-clean 扫描范围内且过扫——项目自己的已批准机器早已
  把「计数≠outcome 内容」编进扫描器（受条件 2 核验约束）。纪律轴——接触了隔离
  字节是事实，记录存续、成因已修（clean extract 制度），不因内容干净而抹掉。
  后果栏：outcome-blind 资格按内容轴不烧；该会话已结束，实际效力是先例——
  记账轴数值的接触记「隔离接触」，不记「outcome 暴露」。
CONDITIONS=
  1. 以 append 更正行落地（引用第 3 行，不改原行），注明「delegated Fable seat,
     dec-remaining-2026-08-26；Aaron may override by append」（builder）。
  2. builder 机械核验 outcome-clean 扫描器对 REVIEWER_EXPOSURE_LOG.md 无逐文件豁免；
     若有豁免，本裁的机械佐证失效，该行回到 PENDING_AARON 并报 Aaron（builder）。
  3. 裁定依据句（记账轴≠outcome 轴，轴间不得互推）逐字入更正行，杜绝逐事件重开
     （builder）。
FALSIFIER=任何证据表明累计计数经归一化规则可反演出目标绩效信息 ⇒ 分类翻转为
  outcome 暴露、第 3 行席位追溯记烧、且本席（看过同一值）的席位自评同步作废。
CONFIDENCE=MEDIUM——轴分离论证有宪法与扫描器双重支撑，但扫描器无豁免这一前提
  在送审集内不可证，故以条件 2 把它做成 fail-closed。
```

```
ITEM=R9  TITLE=第 4 行：NOT_EXPOSED 值该不该存在于暴露台账
DELEGABLE=YES——台账词表的治理判断，仓内、非许可。
RULING=保留该值与该行，附范围规则。doctrine 论证：L6 禁的是**由无记录推出 NONE**；
  一条有据可查的阴性记录恰是其对立面——它是合法宣称「干净」的唯一通道。没有第 4 行
  这类行，未来排席者对任何席位的既往只剩 UNKNOWN，缓解措施永远无法被证明起过作用；
  本栈的负证据传统（falsified 的果断记录、KB 负证据审计）同理适用于席位轴。
  防语义漂移的范围规则：NOT_EXPOSED 行仅许可用于「在 blind-mandate 下完成的一次
  具体复审」的逐单认证（引用 review_id），不得用作例行会话点名册；台账主题由此
  明确为「席位暴露状态事件」，阳性（烧）与认证阴性（活）同为状态事件。
CONDITIONS=
  1. 以 append 在台账尾部加词表节（不动既有任何行）：REVEALED_TARGET_METRIC /
     TARGET_METRIC / QUARANTINE_CONTACT_NON_OUTCOME / NOT_EXPOSED / PENDING_AARON
     （过渡态），各一行定义＋NOT_EXPOSED 的逐单认证范围规则；新值首用前须经裁定
     （Aaron 或受委托席）（builder）。
  2. 第 4 行本身不动，无需更正行——其 classification 值经本裁转为合法（builder 零动作）。
FALSIFIER=NOT_EXPOSED 行开始为无 blind-mandate 复审的会话追加（点名册漂移）⇒
  范围规则失败，阴性认证拆出独立 roster 文件、台账回归纯暴露事件。
CONFIDENCE=HIGH——「无记录⇒UNKNOWN」与「有据阴性记录」在逻辑上互补而非冲突，
  唯一实险（语义漂移）已被范围规则机械化。
```

```
ITEM=R10  TITLE=第 5 行终分类（前决裁席约束前三次仅文件名定位，零内容）
DELEGABLE=YES——同 R8；血缘自指（该席是本席的直接前任、同模型族）如实申报，
  兜底同 R8。
RULING=终分类＝NOT_EXPOSED（注：pre-constraint、filename-only、zero content；
  成因为 builder 交付缺陷，已修——本席零定位操作即是修复生效的实证）。与第 3 行
  先例的一致性：第 3 行有隔离字节接触（一行文本＋一个计数值）故得隔离接触类；
  第 5 行零隔离字节——返回的两个文件名均不在注册表上（近失如实记录：注册表上确有
  一件名含 PROMPT 的隔离件 ops/ND2_ND3_FABLE_DECISION_PROMPT.md，但其名不以 PROMPT
  起头，锚定 glob 未命中——这证明修复的必要，不改变本次零命中的事实）。激励面是
  本裁的第二只脚：该席未被问及即主动申报，台账末行自己写着「瞒报才是不可逆损失」
  ——对诚实申报的零内容操作若给出烧毁邻近的标签，是在训练未来席位不申报。
  自评从严、终裁从实：干净就是干净。
CONDITIONS=
  1. 以 append 更正行落地，同 R8 条件 1 的委托标注（builder）。
  2. builder 机械复核：在当时 commit 下 ops\PROMPT* 所返回的文件名集合恰为申报的
     两个、且无一在注册表上；核验入更正行（builder）。
FALSIFIER=任何证据表明三次操作之一实际返回过内容（非仅名）、或彼时有隔离件匹配
  该模式 ⇒ 重分类，且第 5 行成因分析重开。
CONFIDENCE=HIGH——零内容是三方一致的事实（席位自陈＋builder 复核＋台账转录），
  分类只需先例一致性与激励一致性，两者同向。
```

## 一.4 跨项与席位陈述（逐字）

```
CROSS_ITEM_CONFLICTS=十项无矛盾，三处耦合已显式接线：(1) R1 的 A′ 是 R4 终稿恒真的
  前提——若 Aaron 推翻 R1 改 B，R4 条件 5 强制先重备终稿再动全局文件（这是本轮发现的
  一条真耦合：菜单上的 A 与 B 都会让刚批的全局文本过期，A′ 消解之）；(2) R3 的失效
  裁定是 R5 执行授权的前置，二者绑定——推翻 R3 必须连带冻结 R5；(3) R2 的联合范围
  即 R6 的窗范围，一处改动两处同步。R8/R9/R10 构成单调一致的词表（内容严重度：
  零内容<记账轴值<outcome 片段<判定统计量）。十项合计不解锁 D-3、不签 P2、不动
  口令锁、不释放任何 gate——与 OD-2026-08-26-6 逐条相容。
SEAT_INDEPENDENCE_CONCERN=三层如实报：(a) 我在裁「我自己模型族的前席划为 Aaron-only
  的东西能否委托给我」，并且答了七个 YES——无法自证这不是同族自利；结构缓解是每个
  YES 都留了 Aaron 的 append 否决通道且执行全部过 builder 的机械条件。(b) R8 的裁定
  自指地决定了本席自己对同一计数值的接触定性——我把「本席那一行的终分类」明示让出
  （见 STILL_AARON_ONLY 第 5 条）以切断循环。(c) R1 的 A′ 不在 builder 菜单上，
  无对抗席复核过它；我以「严格少动于 A」为其安全论证，但它终究是本席的独创。
STILL_AARON_ONLY=
  1. R4 的行使：全局 CLAUDE.md 第 90 行替换的那一次明示授权。
  2. R6 的开窗动作本身（定义性要件）；以及真到 pilot-ready 时，启动 GRAD pilot 的
     决定——pilot 消耗真实研究面，我只裁了它与窗的相对顺序。
  3. R7 的目录创建授权，及其后各自独立的写探针授权与执行授权（ND1 三条不得合并）。
  4. 仓库整体是否迁出主动同步树（第 7 项彻底形，本轮未触）。
  5. 本席自己的席位轴终分类（builder 将按惯例把本席披露转录为新行；该行终分类不由
     本席的 R8/R10 先例自动决定，归 Aaron）。
  6. D-3 的去向（OD-2026-08-26-5 第 5 条，不在本十项内）。
  7. 对本裁定全文的否决——每一条 YES 都是可被他一行 append 推翻的。
STRONGEST_OBJECTION_TO_MY_OWN_RULINGS=最强一条打在 R3+R5 的合取：同一个受委托席位
  先解释掉所有者的 hold、再行使被释放的许可——这正是本栈到处设防的自我升格形状，
  哪怕每一步都有 Aaron 的委托原话背书；若 Aaron 对 R3 有一丝不适，正确动作是连 R5
  一起冻结，而不是只改 R3。次强打在 R1：A′ 放弃了单前缀的完全覆盖，若未来某守卫
  只查前缀忘了查注册表，两份台账就是它的盲区——条件 3 的变异证红是唯一防线，
  它必须真的红过。第三：R8 依赖「扫描器无逐文件豁免」这一集内不可证前提，条件 2
  若查出豁免，R8 连同本席自评的干净度一起降级。
SEAT_STATUS=BLIND（自评）——零检索、零定位操作、零隔离件打开；唯一申报项是送审集内
  席位台账序言携带的累计计数值，其定性按本席 R8 的裁定为记账轴接触、
  非 outcome 内容——此自评的循环性已如实标注，本席那一行的终分类归 Aaron。
INDEPENDENCE_STATEMENT=按维度：
  · 会话：全新顶层窗口；非八项裁定席、非四项裁定席、非本仓任何工作会话的延续；
    前席内容仅经送审集内的转录件到达本席。上下文含全局 CLAUDE.md（R4 恰用它做了
    一次有利的直接核验）与记忆索引（ITSF 条目为治理指针，无 outcome 数值），如实报。
  · 隔离件：零打开。本仓内除本 packet 与表列八路径外零文件访问；未开 RECOVERY_ANCHOR
    （无需要）；OUTCOME_CARRYING_ARTIFACTS.json 本体未开（12 条以送审件转述为据，
    条目级事实凡承重处均已挂机械核验条件）。
  · 检索：零。git log 与哈希重算均为 packet §2 明示指令、精确路径、无 glob 无 grep。
  · 数据与运行：零真实数据、零 run、零 registry/台账追加、零文件写入；
    workflow 0/3，subagent 0。
  · 与前席关系：同模型族，不同会话；本轮对前席产物既有继承（R2 沿 D-4 条件）也有
    越出菜单的修正（R1 A′）与其留白的收束（R8/R10），每处判断的依据是集内字节，
    不是席位权威。
```

---

# 二、builder 审核

## 2.1 两条机械条件都已跑，都成立

Fable 把两条断言做成了 fail-closed 条件，要求 builder 核验。**都跑了：**

| 条件 | 核验 | 结果 |
|---|---|---|
| **R8 条件 2**：扫描器对 `ops/REVIEWER_EXPOSURE_LOG.md` 有无逐文件豁免 | `_SELF` 仅两项（`INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md`、扫描器自身），**席位台账不在其中**；在 `rglob("*.md")` 范围内；实扫干净 | **无豁免 ⇒ R8 机械佐证成立，不降级** |
| **R10 条件 2**：当时 `ops/PROMPT*` 返回什么、有无在注册表上 | 在 `6fe14a7` 下实测恰为 `ops/PROMPT_D3_SOL_REVIEW.md` 与 `ops/PROMPT_EIGHT_OPEN_FABLE.md` 两个，**均不在隔离名单上** | **与席位申报逐字吻合 ⇒ `NOT_EXPOSED` 成立** |

**Fable 那条近失也属实**：`ops/ND2_ND3_FABLE_DECISION_PROMPT.md` 确在隔离名单上、
名含 `PROMPT`，但**不以 `PROMPT` 起头**，锚定 glob 未命中。**运气成分是真的。**

## 2.2 R3 条件 1 的核对

Fable 要求核对「08-25 时点待返回的 Sol 复审在 08-26 前已全部返回」。
席位台账与 packet 记录显示：R2 设计审（`rv-3651f9fe…`）**已返回 HOLD**；
D-3 复核（`rv-f4207865a116…`）**已返回 HOLD**。**未发现彼时另有未返回的单。**
故 R3「hold 按自身终止条件解除」成立。

**Fable 要求「失效≠放行」清单与裁定同段引用，不得拆开** —— 已在 §一.1 R3 内。

## 2.3 R1 的 A′ 是菜单外的新选项，我复核了它的第 (1) 条理由

A′ 依据的核心是「八项裁定第 1 项条件 2 要求两份台账零改动」。**该条件原文属实**
（见 `ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md` §一.1 ITEM=1 CONDITIONS 第 2 条）。
Fable 自己也把 A′ 标为「无对抗席复核过」的独创（`SEAT_INDEPENDENCE_CONCERN` (c)）。

**builder 的观察**：A′ 确实严格弱于 A（迁得更少），所以它引入的**新**风险面只有
一条——单前缀不再覆盖两份台账。Fable 的条件 3 用「守卫必须按注册表 12 条全查 ＋
变异证红」把它兜住，而那正是 `tests/test_delivery_names_no_quarantined_path.py`
**现有的做法**（它读注册表，不读前缀）。**所以条件 3 不是新建，是保持现状。**

## 2.4 尚未执行的部分

R1／R2／R5 的落地动作（迁移、运行时整改、carve-out 行使）**均未开始**。
R4／R6／R7 三条 `DELEGABLE=NO`，等 Aaron 各一句话。
本席（Fable）自己的席位轴新行由 builder 转录，**终分类归 Aaron**（其
`STILL_AARON_ONLY` 第 5 条）。
