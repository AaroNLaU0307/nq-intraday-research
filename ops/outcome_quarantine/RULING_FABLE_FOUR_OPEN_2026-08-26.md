# 四项裁决 —— Fable 决裁席

```
RECORD_TYPE=RULING
DATE=2026-08-26
DECIDER=Fable 5（Xhigh；Aaron 常设指示下的决裁席）
BASIS=ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md
BASIS_SHA256=D9F37CAEC16B1A92FD8A2C1588E5394797DBF1F033CFBBEBBCD7BB33EAF34F94（8267 字节；移交未附哈希，由决裁席自钉）
MODE=READ_ONLY —— 本席未改动项目内任何文件；本件由 builder 逐字节转录入 ops/ 并复核哈希
```

**裁定 ≠ 解锁**（沿用包内声明）：各项执行锁逐条重申于文末。

---

## 〇、先行发现（按严重度）

**F1（HIGH，改变 D-2 的证据基础）**：`ops/REVIEWER_EXPOSURE_LOG.md` 第 2 行——2026-08-26 **第二个** Sol 席位在 packet 承载的 R2 复审中被烧，成因是**广域符号搜索带出隔离锚片段，席位并未打开该文件**；且禁区清单守卫只扫 `ops/*PROMPT*.md`，对 packet 载体「通过了，且什么也没保护」。决策包写「D-1 那次暴露是它的第一次兑现」——到裁决时刻兑现已是**两次**，第二次证明「别打开那个文件」类围栏**在原理上不够**。

**F2（HIGH，本包自身缺陷）**：包第 155 行让决裁席「形式沿用 `ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`」——该文件在 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome` 名单上（还原四类内容）。若我照办，**决裁席位就是第三个被烧的席位**。我先读注册表才避开，改用包内已写明的呈交字段形。这是同一形状的第四次实例，直接支撑 D-2 的加固条件 S2。

**F3（MEDIUM，归 Aaron）**：注册表把「cumulative exposure count」列为隔离还原类别，但该数值（1575）以「台账量纲」名义出现在**两份未登记文件**里：本决策包（第 33 行）与席位台账（第 21 行）。二者择一：把这两件入注册表（副作用：席位台账将对 blind 席位不可读，自败其用），或由 Aaron **限缩该类别定义**（例如「计数不携判定方向，不属 outcome」）。裁前按 fail-closed 处理：排 blind 席位时视两件为暴露相关。

**F4（MEDIUM，流程）**：本次移交违反常设工件传输规则——落盘但**未附 SHA256**；决裁席自行计算并钉入本件（见 BASIS_SHA256）。另：包未带规范路由头（轻微）。

**F5（披露，喂给 D-2）**：本席为核实 D-3 引用文本做了一次单模式定向 grep，命中 `ops/MC_TO_STRATEGY_MASTER_PLAN.md:62` 一行（边界第 4 条原文，经查不含注册表四类还原内容）。**连被明确警告过的席位做一次定向检索都会触到隔离件**——检索面危害的第五次演示。

**已复现 vs 自报**：已复现——注册表全文、席位台账、`tests/conftest.py:28-31` R5 守卫、`qros_runtime/packet.py:64` 硬编码、`plan_failure_event` 只规划不写（`src/itsf/mc/supplement_runner.py:648`）、s0 运行器自追加 RUN_STARTED 及其 never-re-read 纪律（代码注释 2568/2602/2999 一带）、恰一行不变量位置（`tests/test_exposure_ledger_migration.py:71`）、活跃提示词守卫位置（`tests/test_artifacts_under_review_are_frozen.py:223`）、偏离记录全文。仍属自报——213→211 实测数（偏离记录 §2 有文档化记录）、两行席位分类（席位自评，制度上不下调）。

---

## 一、裁决

### D-1

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

### D-2

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

### D-3

```
ITEM_ID=D-3
RULING=C（分开裁），且本裁定整体只是三步中的第一步（Fable 提案），非终裁。
  · P3：运行器自行追加（A 形），依「受托单写」限缩解释——边界第 4 条
    （ops/MC_TO_STRATEGY_MASTER_PLAN.md:62）的「主代理单写」读作「同一时刻恰一个写者，
    在主代理权限下，每次追加可追溯到主代理发起的动作」。运行器在 run 期间持显式写者
    租约、事件词表受限（仅获授类型）、schema 校验、追加后不再重读（s0_real_run.py 已
    工程化的快照纪律）。理由：P3 是暴露消耗点，记录必须与不可逆动作原子耦合；B 的人工
    介入窗口本身是风险。scripts/s0_real_run.py 的 RUN_STARTED 先例据此被规整为合规，
    不回溯拆除。
  · 失败事件：仅主代理追加（B 形）。plan_failure_event
    （src/itsf/mc/supplement_runner.py:648）保持只规划不写；运行器永不写自己的讣告——
    失败观察者必须在失败后存活，编排器做不到。缺失终止事件由下次 bootstrap fail-closed
    检出；该检出机制必须存在并有测试，若无则属本提案的建造义务。
CONDITIONS=
  1. 流程走满：本提案 → fresh Sol 批准 → Aaron 裁决（与 MC-REG-COLLISION-001 同形
    同工序；builder 的三步建议被采纳）。
  2. Sol 审查必须专门猎取：① 分快照读（MC-REG-COLLISION-001 的洞；代码已示 never-
    re-read 纪律，Sol 复核而非采信）；② 崩溃后陈旧租约；③ 并发 qros 调用竞争；
    ④ OneDrive 同步树内追加的原子性（仓在 OneDrive 下；L-5 正是 OneDrive 残渣类缺陷）。
  3. Sol PASS ＋ Aaron 授权之前，生产代码不得获得任何 registry 写能力。
FALSIFIER=任一观察到的双写者交错；或一次跨越 P3 的运行未留 registry 行且下次 bootstrap
  未标红 ⇒ 受托单写构造不安全，回落 B 并接受介入窗口（其缓解设计交 Sol，例如
  「预授权＋短时效启动令牌」把人工介入挪到 run 之前）。
COLLATERAL=动（仅经三步批准后）：src/itsf/mc/supplement_runner.py（新增租约化 P3 追加；
  plan_failure_event 不动）、tests/test_mc_supplement_runner.py、bootstrap 缺失终止
  事件检出＋测试、边界第 4 条限缩解释随 Aaron 决策记录附着（不改
  ops/MC_TO_STRATEGY_MASTER_PLAN.md:62 原文——它在隔离件内且 append-only）。
  不得动：scripts/s0_real_run.py 既有先例代码（规整非拆除）、registry/exposure 台账
  本体。
```

### D-4

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

---

## 二、决裁席暴露自评（按席位台账惯例，自评不下调）

- 经决策包与席位台账见到「cumulative exposure count」类别数值（1575）；经一次定向
  grep 见到隔离锚一行治理边界文本（不含四类还原内容）。
- **未见**：verdict token、endpoint spread value、zero-direction cell count、任何
  目标绩效数值。
- 按注册表现行类别定义，本席不再自证完全 outcome-blind；终分类随 F3 归 Aaron。本席
  本就不担任 Stage I（Stage I 属 Sol），实际成本为零，但入账原则一致——建议 Aaron
  授权在 ops/REVIEWER_EXPOSURE_LOG.md 补记第 3 行（builder 追加需该授权）。

## 三、执行锁重申

- **D-1**：裁 A 本身无动作；条件 1/2 属 builder 常权；条件 3（全局规则限缩解释）须
  Aaron 明示批准。
- **D-2**：拆锚、B 保留、S1(b)、S2 属 builder 可执行（受条件 5 的 hold 确认约束）；
  S1(a) 与注册表 carve-out 仅 Aaron。
- **D-3**：纯提案。任何执行须 fresh Sol PASS ＋ Aaron 裁决在先。
- **D-4**：运行时改动仅 Aaron 另开工作项；过渡 B 即刻生效（现状由「未裁」转「受裁
  批准」）。
- 本件由 builder 逐字节转录入项目 ops/（本席只读，不落仓）；转录后复核本件 SHA256。
