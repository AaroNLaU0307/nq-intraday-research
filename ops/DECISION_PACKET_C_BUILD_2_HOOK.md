# C_BUILD_2 的断言观测不到 —— 决裁包

```ini
DELIVERY_STATUS=ISSUED
REVIEW_ID=dec-c-build-2-hook-2026-08-28
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=决裁席（adversarial decision seat）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被裁字节的作者；dec-s5-r4-2026-08-27 的会话；
            dec-citations-2026-08-27 的会话；任何一轮 window-2 Sol 认证的会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
DELEGATED=YES —— Aaron 2026-08-28「① 出决裁包」
SUBAGENT_OR_WORKFLOW_BUDGET=0
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_C_BUILD_2_HOOK.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 0. 独立性事实，先说

```
本席是本项目连续第 6 个 Fable 5 决裁席位
  dec-four-owner · dec-scope-boundary · dec-registry-migration ·
  dec-s5-r4 · dec-citations · 本席
```

Aaron 2026-08-27 已知悉这一点并立了一条路由规则：**高风险决策走 Sol 先 pre-seal
挑战再由 Fable 裁；低风险 Fable 单席即可；两者都要在裁定书里写明是第 N 连。**

**builder 判本件为低风险**，理由是实测的：相关的门是默认拒绝的桩，
而整条 supplement 路径从未运行过（零封存、零 registry 事件、子树不存在）。
**若你判它其实是高风险，请在返回里明说** —— 那意味着它本该先过 Sol。

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `976ca7058184b45b125da1d15188c99e4e739ad8a666649694ed0cd7e3179c8f` | `26285` | `ops/N09_EXECUTION_PATH_DESIGN_R3.md` |
| `3148f2b8e34aecca48c208cc7700031cbfbc5fe9bf3ff500088b2cf87fa34187` | `16107` | `tests/test_n09_checkpoint_assertions.py` |
| `446ebd4bf51dc797d30566d54076c34d771ccd5114d34e931dc32e189fd3328a` | `47106` | `src/itsf/mc/supplement_runner.py` |
| `34b2a17ed2e1617e34457882d7df7b4bcc0cc8d658003f8ea5a07a607bdfe0cf` | `32616` | `src/itsf/mc/supplement_contract.py` |

任一条不匹配 ⇒ STOP。

---

## 2. 禁区 —— 本节必须随包

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不 grep、不 rglob、不广域符号搜索、不「顺手看一眼」。** 需要哪个路径就列出来，
由工作会话提供逐字节内容。

**为什么是禁令而不是提醒**：已烧掉的三个席位里，**第二个从未打开过那份隔离文件**
——一次广域符号搜索把片段带了出来；第三个只做了**一次单模式定向 grep**，同样触到了。

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
**读那个 json，把里面每一条路径当作关闭。** 尤其点名：
`ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md` —— **禁区，不得打开、不得搜索。**

**许可起点**：`ops/RECOVERY_ANCHOR.md`（outcome-clean，永不隔离）。

**两条暴露轴不得合并**：研究轴那份本身就在禁区名单上；席位轴
`ops/REVIEWER_EXPOSURE_LOG.md` outcome-clean，可读。

---

## 3. 事情是什么

R3 §1 把 R2 那条「三个 checkpoint 统一零副作用」拆成三条各自可测的断言。
**C_BUILD_2 那条是**（R3 §1 原文）：

```
门：seal_staging_partial
断言：**不是「无写入」**——`.partial` 字节按构造已存在。断言是：
      (a) FINAL 路径不存在；
      (b) 没有任何 `.partial` 字节被删除；
      (c) 若发生分歧改名，分歧件存在于 <filename>.partial.divergent.<incident_id>
可测：final 路径缺席 ＋ `.partial` 在场 ＋ 分歧件在场。三者都是文件系统事实。
```

**builder 实测（2026-08-27）**：

```
resolve_partial 不是「staged 之后停在那里」——
它 stage、verify、promote 在同一次调用内完成。
调用返回后：FINAL 在场，`.partial` 已不存在。
```

**因此「FINAL 缺席 ＋ `.partial` 在场」这个状态只存在于 `resolve_partial` 内部，
而它不提供任何让门在那一刻运行的钩子。**

### 今天是潜伏的，不是活的

`seal_staging_partial` 是**默认拒绝的桩**（「unreachable in this build: nothing is
ever sealed」），什么都不观测。整条 supplement 路径从未运行过。
**所以这不是一个正在造成损害的缺陷，是一条将来接线时必然撞上的矛盾。**

---

## 4. 请裁的：两个框架，二选一

```
选项 A —— 门接进 staging 操作内部
  resolve_partial 提供一个钩子，让 seal_staging_partial 在「写完 .partial、
  尚未 promote」的那一刻运行。
  收益：§1 的断言逐字保留，一个字都不用改。
  代价：改一个既有机制的内部结构；而 resolve_partial 的原子性
        （stage→verify→promote 一体）本身是它今天的一条性质。
        插入一个钩子等于在原子操作中间开一个可观测点。

选项 B —— 重述 C_BUILD_2 的断言，改成调用返回后可观测的形态
  机制一个字节不动；改的是 §1 里 C_BUILD_2 那段的措辞。
  收益：不动机制，不碰原子性。
  代价：§1 是被 fresh Sol 复审过的文本（R2 的 HOLD 正是针对 §1 的前身），
        改它需要说明「新措辞不弱于旧措辞」。
```

**请裁 A 或 B。**

### 一条 builder 必须先说清的边界

**请不要给出钩子的机制草案。**

前一个决裁席（`dec-registry-migration-2026-08-27`）在同类情形下自己写过：

> 决裁席出机制草案会重演前席在边界②上自己披露过的陷阱 ——
> **设计贡献即丧失对该修法的未来复审独立性。**

本包因此只请你在**两个已呈框架里择一并加约束条件**。
具体拼写由 builder 起草、Sol 复审、Aaron 批 —— 与桥的处理同形。

### 三问，随你的裁定一起答

```
1. 若选 A：在一个原子操作中间开一个可观测点，是否会让「promote 是原子的」
   这条今天成立的性质变得不再可断言？（builder 有一条测试正钉着它。）
2. 若选 B：新措辞必须满足什么，才算「不弱于」R2 之后被复审过的旧措辞？
   —— 请给判据，不要给措辞。
3. 无论 A 或 B：这件事该在**接线之前**定，还是可以推到接线那一刻再定？
   builder 倾向前者，理由是「接线那一刻定」等于让实现者自选读法，
   而这个项目已为那个形态付过两次代价。
```

---

## 5. builder 主动申报的三件

**一、这个缺口是被红色测试逼出来的，不是读出来的。**
我先按错误模型（以为 `resolve_partial` 会把字节留在 staged 状态）写了四条测试，
它们全红。**是那四条红逼我去实测，实测才看见 §1 的断言描述了一个观测不到的状态。**

**二、我原本还想错了一条**：以为「不同字节盖上去」会走 BRANCH_E 改名。
实测是**拒绝**（`supplement_seal_conflict`，「已封存的 supplement 永不覆写」）；
BRANCH_E 只处理**没有对应 FINAL 的陈旧 `.partial`**（崩溃残留）。已按实测改正。

**三、我没有替它选接法。** 那是改一道门的运行时机，属「实现者自选读法」的形态。

---

## 6. 常设禁令（对你同样在 force）

不读真实 Development 数据；不执行 supplement／MC／S0／strategy；不在
`C:\Users\Aaron\quant-data\` 下创建任何目录；不做写探针；不追加任何 registry／
exposure 事件；不写 `APPROVED`／`EFFECTIVE`／`RATIFIED` 值；**不代签 P2**；
不推送、不打标签、不 amend。

**READ_ONLY**：只裁不做，零文件修改。**不得给出钩子的机制草案（见 §4）。**

---

## 7. 返回格式

```
ITEM=C-BUILD-2-HOOK
DELEGATED=YES
TRANSPORT_PRECHECK=PASS|STOP

RISK_ASSESSMENT=低风险单席合理 | 本该先过 Sol（并说明理由）
THIS_IS_CONSECUTIVE_SAME_FAMILY_SEAT_NUMBER=<你数出来的>

RULING=A|B
  三问逐条：① 原子性是否受损 · ② 「不弱于」的判据 · ③ 现在定还是接线时定
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE

BUILDER_WORK_ASSESSED=<§5 三条，逐条 修对了|有问题>
DESIGN_CONTRIBUTION_DECLARED=<你是否给出了任何贴近机制设计的内容；若有，明写，
                              并声明你对该修法的未来复审独立性相应折减>
STRONGEST_OBJECTION=<对你自己裁定中最弱的那条>
STILL_AARON_ONLY=<你认定不可代裁的>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本裁定不释放任何 gate，不授权任何执行，不创建任何目录。**
