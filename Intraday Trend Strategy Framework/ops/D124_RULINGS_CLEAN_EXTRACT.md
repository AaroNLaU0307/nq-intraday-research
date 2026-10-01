# D-1／D-2／D-4 裁决 —— outcome-clean 可读副本

```
RECORD_TYPE=RULING_EXTRACT
SOURCE=ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md（**OFF-LIMITS，隔离件**）
RULED_BY=Fable 5（决裁席，2026-08-26），`DELEGATED=YES`
EXTRACT_IS=逐字。D-1／D-2／D-4 三节全文 ＋ §三执行锁全文。
EXTRACT_IS_NOT=删节。未取的是 §〇（先行发现）与 §二（决裁席暴露自评）；
               **§二里带着一个被隔离的数值，那正是原件被隔离的原因。**
               D-3 一节另有单独副本 ops/D3_REGISTRY_WRITER_PROPOSAL.md。
OUTCOME_CLEAN=是（机械扫描；本件永不进入 carries_outcome）
```

> **为什么要有这份副本。** 原件**是隔离件** —— 它自身复述了一个被隔离的数值，
> 转录时即登记。任何 outcome-blind 席位不得打开它，而 D-1／D-2／D-4 的裁决本身
> 不含任何还原内容。所以取出来，经同一台扫描器验证干净。

---

## D-1

```
ITEM_ID=D-1
RULING=A（不补行）。席位暴露与研究暴露是两条轴：ops/EXPOSURE_LEDGER.md 的量纲是研究
  自由度消耗，席位烧毁不消耗研究自由度；同轴记录会凭空制造一次「研究者暴露于目标统计
  量」，而指针行提供的只是可发现性、不是信息——可发现性能在不触碰 append-only 台账、
  不修订已批准不变量的前提下机械达成。L6「无账即 UNKNOWN」已由席位台账满足。
  本裁覆盖第 1、2 行及未来同类席位事件作为一个类，不逐事件重开。
CONDITIONS=
  1. 双向可发现性必须机械化，不靠口口相传：qros-state.yaml 的 outcome_exposure.scope
     同时点名两份台账（研究轴 ops/EXPOSURE_LEDGER.md；席位轴
     ops/REVIEWER_EXPOSURE_LOG.md），并新增守卫测试断言任何声明项目暴露状态的活动
     工件两者并举。此为 builder 常权（是测试与自报字段，不是 exposure 事件追加）。
  2. builder 核实 ops/REVIEWER_EXPOSURE_LOG.md 确在
     tests/test_review_artifacts_are_outcome_clean.py 扫描范围内；不在则纳入。
  3. 本裁隐含对全局 L6 规则「append every exposure event to ops/EXPOSURE_LEDGER.md」
     的限缩解释：该句 scope 限于研究者/统计暴露轴。此解释触及全局常设规则，须 Aaron
     明示批准并录入决策记录；批准前本裁临时生效（方向 fail-closed：席位台账已保证
     no-record⇒UNKNOWN 不被触发）。
FALSIFIER=任一会话按文档化程序（qros bootstrap ＋ scope 点名）查询暴露状态仍得出错误
  答案——烧掉的席位被排为 outcome-blind Stage I，或某会话在席位台账有相反行时自陈
  OUTCOME_EXPOSED=NONE。观察到任一次 ⇒ 本裁翻转为 B。
COLLATERAL=动：qros-state.yaml（declared scope 措辞）、新增/扩展守卫测试、Aaron 决策
  记录。不得动：两份 EXPOSURE_LEDGER.md、tests/test_exposure_ledger_migration.py:71
  恰一行不变量、逐行恒等迁移测试语义、ops/REVIEWER_EXPOSURE_LOG.md 既有行。
```

**builder 已落地的部分**：条件 1 = `tests/test_exposure_discoverability.py`；
条件 2 = 已核实并由该文件的
`test_the_seat_ledger_is_inside_the_outcome_clean_scan` 钉住。
**条件 3 未落地** —— 它就是本次八项里的第一项。

## D-2

```
ITEM_ID=D-2
RULING=C（A 拆锚 ＋ B 保留），并附加两条包内未列、但 F1/F2/F5 证据强迫的结构性条件：
  S1 检索面隔离——F1 证明只要隔离内容仍在 blind 席位会检索到的树里，任何广域检索都
     可能带出它；F5 证明定向检索同样触到。两个 prong：
     (a) 将 carries_outcome 全部路径迁入单一显名隔离子树（如 ops/outcome_quarantine/），
         注册表路径字段随迁——此 prong 因注册表自述「entry 永不因编辑本文件而离开」
         需 Aaron 对「路径迁移≠条目离开」作明示 carve-out，Aaron 拒绝则 S1 以 (b)
         单独成立；
     (b) outcome-blind 席位的操作规则禁止自主仓内检索：字节仅经 Review Packet v1
         PULL_PROTOCOL 由工作会话供给。立即可实施，零文件迁移。
  S2 缓解必须随载体走——禁区清单机械附着于**每一种**复审交付载体，不只 *PROMPT*.md：
     新增守卫断言每次 PACKET_ISSUANCE/复审移交都有禁区清单附件入记录，守卫扫描范围
     相应扩展。（F1 第 2 行的直接根因；F2 是同形第四例。）
  不选纯 PULL-only（不拆锚）：它不覆盖按恢复序自行定位的会话，且 F1 表明 packet 承载
  的复审中席位照样检索。拆锚去除源头，围栏与隔离作纵深——一次性不可逆危害（席位烧毁
  不可逆）不允许单层防线。
CONDITIONS=
  1. 新锚 outcome-clean 且永不入 carries_outcome；守卫测试断言其不含注册表四类还原
     内容、不在未标 OFF-LIMITS 的情况下指向任何 carries_outcome 路径。
  2. 主计划仅以 append 追加重定向横幅（保 append-only）：旧 §1 恢复序不删不改，由横幅
     宣告被取代；横幅本身不得新增任何还原类内容。
  3. S1(b)＋S2 落地并写入席位操作规则之前，不得再排任何 outcome-blind 席位；
     Stage I GRAD pilot 排席前，拆锚（A）与 S1(b) 必须已生效。
  4. tests/test_artifacts_under_review_are_frozen.py:223 的守卫语义更新：新锚为许可
     起点，注册表成员仍为禁区。
  5. 若 Aaron 08-25「Sol 返回前不推进」hold 的范围覆盖本项，先经 Aaron；含糊取限制性
     读法。
FALSIFIER=全部落地后再发生一次经检索或导航的席位暴露 ⇒ 源头隔离＋围栏整体失败，唯余
  「零 checkout 复审」（blind 席位无任何仓访问，字节全部外部供给），D-2 重开。反向：若
  S1(a) 在 append-only/注册表约束下无法不削弱守卫地实现，则回落 A＋B＋S1(b)＋S2——
  绝不以削弱守卫为代价。
COLLATERAL=动：ops/MC_TO_STRATEGY_MASTER_PLAN.md（仅 append 横幅；builder 已暴露，可
  执行）、新建 outcome-clean 恢复锚文件（命名归 builder）、
  tests/test_artifacts_under_review_are_frozen.py:223、
  tests/test_review_artifacts_are_outcome_clean.py（增锚清洁用例）、S2 新守卫、
  （仅经 Aaron carve-out）ops/OUTCOME_CARRYING_ARTIFACTS.json 路径字段、指向旧恢复序
  的一切引用（builder 执行时全仓 grep 清点）。不得动：主计划既有章节字节、注册表永久
  隔离语义、两份 EXPOSURE_LEDGER、席位台账既有行。
```

**builder 已落地的部分**：拆锚 = `ops/RECOVERY_ANCHOR.md`；条件 1 =
`tests/test_recovery_anchor_is_clean.py`；条件 2 = 主计划只追加了横幅，旧 §1
字节未动（同文件 `test_the_master_plan_carries_the_redirect_banner` 钉住）；
条件 4 = 已更新；S1(b) 检索禁令 = 写入 `ops/NEXT_HANDOFF.md` 与
`ops/RECOVERY_ANCHOR.md`；S2 = `tests/test_artifacts_under_review_are_frozen.py`
的 `test_every_packet_issuance_has_the_off_limits_carrier` **另加**
`tests/test_delivery_names_no_quarantined_path.py`（后者首跑就抓出载体自身丢了
OFF-LIMITS 标记，已变异证红）。
**S1(a) 与注册表 carve-out 未落地** —— 本次八项里的第二项。

## D-4

```
ITEM_ID=D-4
RULING=A（改运行时，_SAVE_DIR 可配置），过渡期 B 明示批准为受裁标准形，C 驳回——为迁就
  一个实现常量削弱为真实缺陷（L-5）建立、经真实事故（R5）加固的回归守卫，方向是反的，
  与 builder 立场一致；优先级格上项目守卫也高于 QROS 层实现常量。
CONDITIONS=
  1. 改动加性且向后兼容：默认值恒为 "runs/packets"，无显式配置时认证行为零变化。
  2. 配置面为项目级持久配置（注册表条目或 qros-state.yaml 字段），禁用环境变量——
     环境变量会话易失且审计不可见。
  3. packet 正文渲染的 REQUIRED SAVE PATH 行必须渲染生效路径（偏离记录 §5 的陈旧行
     危害不得复制到配置化之后）。
  4. conformance / render-check 套件增配置路径覆盖用例。
  5. 经 Aaron 开启的维护窗执行；认证深度归 Aaron（先例：第一维护窗零 Sol 轮）。
  6. A 落地前：「偏离记录＋同 review_id correction 追加」为受批准的过渡标准形；危害
     写入注册流程/运行时残差登记（注册表在认证仓之外，无需认证轮），新项目不再各自
     重踩。
FALSIFIER=配置化后任一项目出现 PACKET_ISSUANCE 生效 saved_path 与实际存放位置分叉
  （双真相源）⇒ 设计错误——saved_path 保持唯一权威，配置只导向写入器；观察到即回撤
  配置项重设计。
COLLATERAL=动（Aaron 另开 qros-runtime 工作项）：qros_runtime/packet.py:64 _SAVE_DIR
  及 REQUIRED SAVE PATH 渲染处、运行时测试与 conformance、注册流程说明；A 落地时
  ops/RUNTIME_DEVIATION_PACKET_SAVE_DIR.md 追加一行闭合。不得动：
  tests/conftest.py:28-31 R5 守卫、test_s0_runner 两条 runs 断言（明确再确认）、
  <repo>/runs 禁令本身。
```

**builder 已落地的部分**：过渡形 B 已在用 —— packet 存 `ops/packets/`，偏离记录
`ops/RUNTIME_DEVIATION_PACKET_SAVE_DIR.md`，`PACKET_ISSUANCE` 里以同 review_id
correction 追加。**运行时改动未做** —— 本次八项里的第三项。

---

## 原件 §三「执行锁重申」（逐字）

```
- **D-1**：裁 A 本身无动作；条件 1/2 属 builder 常权；条件 3（全局规则限缩解释）须
  Aaron 明示批准。
- **D-2**：拆锚、B 保留、S1(b)、S2 属 builder 可执行（受条件 5 的 hold 确认约束）；
  S1(a) 与注册表 carve-out 仅 Aaron。
- **D-3**：纯提案。任何执行须 fresh Sol PASS ＋ Aaron 裁决在先。
- **D-4**：运行时改动仅 Aaron 另开工作项；过渡 B 即刻生效（现状由「未裁」转「受裁
  批准」）。
- 本件由 builder 逐字节转录入项目 ops/（本席只读，不落仓）；转录后复核本件 SHA256。
```

**D-3 的那一条已经走完前半段**：fresh Sol 已复核，`VERDICT=HOLD`
（`ops/RULING_SOL_D3_HOLD_2026-08-26.md`）。**不是 PASS**，所以执行锁未开。
