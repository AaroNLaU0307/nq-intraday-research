# CODEX_REVIEW_PACKET_M6_1_8（H-1 日志自锁修复 ＋ Strategy Council 交接，供 Codex 独立复审）

- **父 commit（baseline）**：`bdc060cefa0eac4351c9c7bc82784e2527391943`（M6.1.7）
- **本审查对象**：**包含本文件的那个 commit**。本文件**不写自己的 SHA**——
  文档在被提交之前无法知道自己所在 commit 的哈希，任何写在这里的值都只能是
  上一轮的值或凭空捏造的值。实际新 HEAD 见本轮终端汇报。
- **授权状态**：`REAL_S0_NOT_AUTHORIZED`。不追加 READY、不申请授权、不建 tag、
  **不追加任何 registry 事件**、**不新铸任何研究 DR 编号**。
  `runs/` 不存在，S0-T001 未消耗。
- **本轮范围极窄**：只闭合 H-1 一项，并做交接文档更正。**未**重新展开
  evidence、leaf、schema、report architecture 或任何方法实现。

## 0. 证据分级（本轮只有两级，均非 Codex 复跑）

| 级别 | 含义 |
|---|---|
| `FABLE_MEASURED` | 主代理（Fable）在**最终树**上亲自执行所得 |
| `OPUS_REVIEWED` | 独立 Opus 车道（S1／S2）在其自身运行中实测所得，主代理复核采信 |

**本轮没有任何一项证据来自 Codex 全量复跑。** 凡下文数字，Codex 应视为
待复算的声明，而非既成事实。

| 事实 | 值 | 级别 |
|---|---|---|
| 全套件 | **2220 passed / 0 failed / 0 skipped**，388.62s | `FABLE_MEASURED` |
| `--collect-only` | **2220** | `FABLE_MEASURED` |
| `MIN_COLLECTED_TESTS` | **2220**，双钉于 `scripts/s0_real_run.py:47` 与 `tests/test_s0_runner.py:895` | `FABLE_MEASURED` |
| `tests/test_s0_runner.py` | 132 → **147** | `OPUS_REVIEWED` |
| 变异（日志改回真名） | **7 个测试失败** | `OPUS_REVIEWED` |
| `ops/TRIAL_REGISTRY.md` | `de63b3d690c5c4be…b440`（＝基线，未改动；13 条事件） | `FABLE_MEASURED` |
| `EXPOSURE_LEDGER.md` | `394813431d879555…bc9e6`（＝基线，未改动） | `FABLE_MEASURED` |
| `runs/` | 不存在 | `FABLE_MEASURED` |
| `git rev-list --count 6cb7eb71..bdc060ce` | **9** | `FABLE_MEASURED` |

## 1. H-1 —— 缺陷、修复、以及一句必须说清的话

### 1.1 缺陷（在 `bdc060ce` 上独立复现，两个车道各自复现一次）

Stage E 每写一个工件就记一行 `file={真实文件名} sha256={digest}`。
`runinfra._FORBIDDEN_VOCAB_RE` 以 `re.IGNORECASE` 匹配 `e1`／`e2`，
而 10 个正式封存工件里有 **8 个**文件名含之
（`MC_HANDOFF_{E1,E2}_{Base,Conservative,Stress,Severe}.jsonl`；
`S0_REPORT.md` 与 `HANDOFF_ADMISSION.json` 不含，可通过）。
`_safe_log` 把抛出的 `LogLeakError` 吞进 `self._log_errors`，
而 `_log_errors` 的检查点只在 Stage A／B／C／F——**D 与 F 之间没有**。

实测终态（真实 `S0Runner` ＋ 正式工件名 ＋ 生产守卫 logger）：

```
ok=False  terminal_stage=F_SEALED  failed_gate='log_guard'
exposure_consumed=True  stages_completed=(A,B,C,D,E_REPORT)
events=['RUN_STARTED','FAILED']  len(_log_errors)==8
manifest 已完整写入全部 10 条记录
```

**精确触发条件**：**任何成功抵达 Stage-E artifact recording、且未先因其他
原因失败的运行都会触发。** 不得表述为「越过 `prepare` 就必然触发」——
过 `prepare` 是必要不充分条件。（此为对主代理上一轮口头表述的更正。）

严重性：封存全部正确完成、磁盘证明通过、哈希链写好之后，运行才被一行日志
杀死，且 exposure 已消耗。恢复代价＝registry supersession ＋ Aaron 新 §10 语句。

### 1.2 修复

只改**日志行**：`file=artifact_0001 sha256=<digest>`。
`artifact_log_id(position) = f"artifact_{position:04d}"`，
**只由固定写入顺序的序号决定**，不编码 engine／scenario／theta／成本／结果。
`digest` 只计算一次，manifest 记录与日志行共用，二者不可能分叉。

- **未**放宽 `_FORBIDDEN_VOCAB`，**未**白名单 `e1`／`e2`，**未**改任何工件名。
- manifest 保留**真实文件名、真实摘要、原有顺序**。
- 磁盘字节、哈希链、正式报告内容**全部未变**。
- `_log_errors` 检查点移到 `_record_artifacts` 之后（`runner.py:903`），
  使日志缺陷归属 Stage E 而非 Stage F。

**归属改进不是修复本身。** 两个检查点都在 exposure 之后，所以移动检查点
只改变失败**在哪里被报告**，不改变**是否烧 trial**。真正的修复是日志行本身。

### 1.3 必须说清楚的一句：这是假阳性，不是真泄漏

正式工件名是**冻结契约的 engine×scenario 矩阵定死的运行不变常量**——
每次运行完全相同，不含任何数据派生信息。守卫（SA-6 F-04）的目的是拦截
**Stage-C 派生值**（日期、计数、价格）进入日志。因此：

> 本轮做的是**尊重一个本车道无权编辑的守卫词表的规避**，
> **不是**对一处真实泄漏的修补。工件名从来不危险。

同理，不透明编号由固定且公开的写入顺序导出，**与它替换掉的文件名信息等价**。
这没有问题——恰恰因为那些名字本就零信息——但也因此
**不得把不透明 ID 辩护成「隐藏了什么」**，它只是词表兼容措施。

**deferred（本轮不处理，交 Aaron／Codex）**：`_FORBIDDEN_VOCAB` 对结构性
常量过宽。修正词表需要一次裁决，本轮无权也无必要做。

### 1.4 验收证据

| 项 | 结果 | 级别 |
|---|---|---|
| 10 个正式工件名在新日志形态下全部通过生产守卫 | PASS | `OPUS_REVIEWED` |
| 真实 `S0Runner` ＋ 正式工件名 ＋ 合成输入，A→F 抵达 `COMPLETED` | PASS（两种 logger 参数化） | `OPUS_REVIEWED` |
| 所有工件日志行只含不透明 ID 与 sha256 | PASS | `OPUS_REVIEWED` |
| manifest 仍含全部真名、摘要与顺序 | **逐字节证明**：取 `git show bdc060ce:src/itsf/s0/runner.py` 的修复前 runner 与修复后 runner 在**相同合成输入**上各跑一遍，`manifest.jsonl` 两侧 3687 字节、sha256 同为 `3ccd7a048214d897…`，10 个工件全部逐字节相同 | `OPUS_REVIEWED` |
| 变异：日志改回真名 | **7 个测试失败** | `OPUS_REVIEWED` |
| 成功运行末态 `_log_errors` 为空 | PASS | `OPUS_REVIEWED` |
| 未接线关键回调仍在曝光前拒绝 | PASS（三参数化） | `OPUS_REVIEWED` |
| **完备性钉**：该日志点是唯一带变量负载的日志点（**修复前**树中为 `runner.py:519`，**修复后**树中为 `runner.py:632-633`；S2 指出原文未标明所指为哪棵树） | AST 机器核验：15 个 `_safe_log` 点全部锁定，**恰有 1 个**的插值超出 `{RunStage.<X>.value, stage.value}`，且其插值集合 ⊆ `{artifact_log_id(position), digest}`，`name` 不在其中 | `OPUS_REVIEWED` |

**完备性钉是本轮加的，不在原任务书里。** 理由：只修一处而别处仍泄漏
不算修复；把「唯一泄漏点」变成机器可核验的断言，才使完整性可检查而非可声称。
主代理另已独立确认：其余 15 处日志全为 `stage=<枚举> status=<start|end|fail|pass>`，
`_fail_run` 也只发 `status=fail`，原始文本按 F-05 进密封 `INCIDENT_*.md`
而不入日志——故 `post_write_verify` 那些含 `sealed_files[MC_HANDOFF_E1_…]`
的失败详情**不会**触发同一守卫。

**一处诚实注记（S1 提出，主代理采纳）**：测试**不能**断言
`"e1" not in message`——`e1` 会作为普通十六进制子串出现在 sha256 中
（实测：`MC_HANDOFF_E1_Base.jsonl` 的摘要中，`e1` 出现在片段 `ce13` 内部；
**S2 更正**：先前引用的 15 字符片段 `…804629e6b9a219e` 本身**并不含** `e1`，
结论为真但所引证据不成立，此处改为指出真实出现位置），
这正是生产守卫使用词边界正则而非子串匹配的原因。
测试改为断言标识符 token 内无 `e1`／`e2`（大小写不敏感），
并对**每一行**跑守卫自身的正则。这比朴素断言更强。

**一处行为变化（已钉测试）**：检查点位于
`_stages_done.append(RunStage.E_REPORT.value)` 之前，故 Stage-E 日志缺陷
现在报告的 `stages_completed` **不含** `E_REPORT`（此前走 Stage-F 路径时
会把它报为已完成）。这是正确归属。检查点之后仍有一行
`stage=E_REPORT status=end`，是固定字面量（完备性钉已证），
且仍被 Stage-F 检查点覆盖。

### 1.5 S2 只读复核查出的三条延后观察（本轮不修，如实记录）

**(a) 生产实际写 11 行 `file=`，不是 10 行。** 测试夹具 `OFFICIAL_SEALED_ARTIFACTS`
钉的是 **10** 个名字，那是 `sealed_files` 的计数（`S0_REPORT.json` 自排除）；
但 `render_s0_report` 实际返回 **11** 个工件，runner 因而写 11 行日志
（若 `SEED_MANIFEST.json` 将来获准入则为 12——`handoff.py:2242`
`formal_sealable = not problems`，准入不是永久字面量）。
S2 已实测**守卫安全性无缺口**：`S0_REPORT.json` 与 `SEED_MANIFEST.json`
**均能通过守卫**，故修复对真实的 11／12 工件集**同样完整**。
但由此**限定了 §1.3 的「信息等价」说法**：序号→名字的映射，
**只在准入候选集稳定时才稳定**；若 `SEED_MANIFEST.json` 转为准入，
序号 9／10 的所指会改变。**当前没有任何东西钉住写入顺序。** 延后。

**(b) 完备性钉的盲区，已实测而非推测。** S2 在 scratchpad 副本上注入三种
重新引入真实文件名的写法，并复跑该钉子：

| 注入形式 | 完备性钉 | 行为级 H-1 测试 |
|---|---|---|
| `_alias = self._safe_log; _alias(...)` | **通过（盲）** | 抓到 |
| `self._d.log(...)`（绕过 `_safe_log`） | **通过（盲）** | 抓到 |
| `getattr(self, "_safe_log")(...)` | **通过（盲）** | 抓到（5 个测试红） |

即：**钉子只认 `self._safe_log(...)` 这一句法形态，且只走 `runner.py`。**
别名、`getattr`、`partial`、直接 `self._d.log(...)`，以及
`scripts/s0_real_run.py`／`runinfra.py`／`output_proof.py`／`report.py`
里的任何日志路径，它都看不见。**真正的防线是行为级测试**——三种注入
全部被行为测试抓到。当前残余风险实测为零（`self._d.log(` 全库仅出现一次，
就在 `_safe_log` 内部；`guarded_log` 只在 `s0_real_run.py` 一处接线；
`runinfra.py` 内无 `print`／`logging`），但**钉子并不检查这些事实**，
将来若把 `guarded_log` 接到别处，它不会察觉。延后。
（另：`s0_real_run.py` 末尾的 `print(f"terminal: stage=… ok=… …")`
是**不经守卫**的 stdout，只含结构性值，本轮未动。）

**(c) 字节不变性证明法的边界。** manifest 字节完全决定其全部字段且不含时间戳，
故**保序的语义漂移在 manifest 内部已被字节同一性排除**，不是「未观察到」。
它**不能**排除的是：其一，本夹具之外的输入（重名、空 `written`、
超过 9999 个工件、真实 11 工件渲染输出）；其二，**新增的 Stage-E 检查点**
——它在顺利路径上是空操作，因而对顺利路径的字节比对**不可见**
（§1.4 已自行披露该行为变化，S2 复现了分歧：修复前＋拒绝型 logger →
终态 `F_SEALED` 且 `stages_completed` 含 `E_REPORT`；修复后 → 终态
`E_REPORT` 且不含。两侧 `exposure_consumed` 均为 `True`，故「烧 trial」
的结论不变）。

## 2. L-5 —— 只做运行前处置说明，本轮不实施

```
L5_STATUS=OPERATIONS_REQUIRED_BEFORE_REAL_S0
RECOMMENDATION=DEDICATED_LOCAL_NON_SYNCED_RUN_ROOT
BLOCKS_STRATEGY_COUNCIL=NO
BLOCKS_REAL_RUN=YES
```

**成因**：M6.1.7 §1.2 新引入的「声明集必须精确等于运行目录内容」不变量，
使运行目录内**任何**未声明条目都判 `disk_extra_file` → 拒绝封存 → 烧 trial。
而 `RUNS_ROOT = REPO/"runs"` 位于**正在同步的 OneDrive 树**内，
`desktop.ini`、`*.tmp`、`.~lock*`、乃至一个空子目录都会触发。
**基线没有该检查，故基线没有该问题——L-5 是本里程碑系列产生的，不是既有缺陷。**

**本轮明确未做**（逐条对应原任务书 C 项禁止事项）：

- 未增加任何 OneDrive 文件白名单；
- 未忽略任何未知目录条目；
- 未弱化 exact-set 磁盘证明；
- 未擅自把输出改到仓库外路径。

**未来需 Aaron 明确批准的输出根变更（本轮只列，不实施）**：

1. 把 `RUNS_ROOT` 从 `REPO/"runs"` 改到一个**本地、不受云同步**的路径；
2. 该路径须在 `RunConfig` 中显式声明并进入环境锁，否则换根本身会成为
   一个未受治理的自由度；
3. 换根后 `attempts/` 是否同步迁移，需一并裁决（两者当前同根）；
4. 换根会使运行工件**不再随仓库版本化**，取证与归档流程须相应调整——
   这是治理后果，不是纯工程细节。

**它是否构成第三个裁决队列组，仍未裁决**（与 D-4 同样悬置）。
本文件不代为裁决。

## 3. 交接文档事实更正（本轮已做）

| 更正项 | 原状 | 现状 |
|---|---|---|
| M6.1.7 的提交状态 | 三份文档均写「M6.1.7 无任何 commit／未提交工作树」 | M6.1.7 已是 commit `bdc060ce`；三份文档**加时点注记，原文保留不删** |
| commit 距离 | 8 | **9**（`6cb7eb71..bdc060ce`），带码候选里程碑 **7** |
| H-1 表述 | 「跑过 `prepare` 就必然触发」 | 「任何成功抵达 Stage-E artifact recording、且未先因其他原因失败的运行都会触发」 |
| 生命周期不变量 | 主代理曾把它表述为「曝光后不得重读 registry」 | **「曝光后不得从实时 registry 获取研究执行输入；允许只读、只否决的授权新鲜度检查」**——见 §4 |

## 4. 生命周期不变量的精确表述，及它对 §8.8 的裁定

M6.1.7 packet §8.8 曾把一个问题升级：`_expected_governance` 在 Stage-E
仍读一次实时 registry 以复核 authorized commit，这是否违反
「`RUN_STARTED` 后不再读 registry」？

**该问题已由 Aaron 裁定。裁定权威＝Aaron 的 M6.1.8 执行提示词 D.4**——
不是 Fable，不是 Codex，不是任何只读车道。原文所定表述如下。

> **曝光后不得从实时 registry 获取研究执行输入；允许只读、只否决的
> 授权新鲜度检查。**

按此表述，`_expected_governance` 的那次重读**合规**：它不向执行提供任何
输入，只在 commit 与运行前快照不一致时**否决**封存。M6.1.7 复核员 L-6
另已查明其真实价值——它是**运行中途改授权的探测器**，且是唯一的一个
（`pre_exposure_recheck` 在 `RUN_STARTED` 之前跑，结构上覆盖不到）。
**代码维持原样，§8.8 不再是开放项。**

## 5. 仍为 PARTIAL 的项 —— 本轮不得借机宣称整体闭合

- **F-1 = PARTIAL**。prepared 对象仍以 **callable** 形式携带 `regime_of`／
  `vol_axis_of`，并持有一个**活的方法表 `MappingProxyType`**。物化需要
  DR-2 的 `vol_na` 裁决与一个 ticks 取值裁决。M6.1.8 **完全未触及** F-1。
- **F-2 = PARTIAL**。叶／token 证据系统仍为 **legacy diagnostic**，不是发布证书。
  M6.1.8 **完全未触及** F-2。
- `sealed_files` 声明**未绑定到报告之外的任何权威**：磁盘证明确立的是
  *声明==磁盘*，不是 *声明==渲染器本意*。
- 磁盘校验器与本轮的 H-1 修复**都从未在真实路径上执行过**——生产今天在
  `prepare` 即 fail-closed（`_approved_injectables()` 返回 `None`），
  全部证据为**合成级**。第一次真实 S0 将同时是它们的第一次真实执行。
- `runinfra.py` 的 `RUN_FAILURE_REPORT.{md,json}` 写入仍为文本模式
  （M6.1.7 已具名延后；本轮范围外，未动）。

## 6. 车道与文件归属

| 文件 | 车道 |
|---|---|
| `src/itsf/s0/runner.py`、`tests/test_s0_runner.py`（除双钉值） | **S1**（独占） |
| `MIN_COLLECTED_TESTS` 双钉值 | 主代理 |
| `scripts/s0_real_run.py` | 主代理（本轮仅改双钉值一行） |
| 本文件、`CODEX_REVIEW_PACKET_M6_1_7.md`、`S0_REAL_RUN_AUTHORIZATION_PACKET.md`、`DECISION_REQUIRED_READY_SUPERSESSION.md` | 主代理（S2 只读核查） |
| `runinfra.py`、`report.py`、方法层全部文件 | **未触碰** |

## 7. 给 Codex 的复核重点

1. **§1.3 的定性是否成立**——工件名是否真为运行不变常量？若否，则本轮的
   「假阳性」定性错误，修复方向也应改变。
2. **完备性钉是否真的完备**——AST 走查只覆盖 `self._safe_log(...)` 的
   f-string 字面量形式。若存在其他日志路径（非 f-string、间接调用、
   或 `runinfra` 内部自行发日志），钉子看不见。
3. **manifest 字节不变性的证明方法**——用修复前后两个 runner 跑相同输入比字节，
   是否足以排除「顺序相同但内容语义改变」？
4. **归属检查点的位置**是否引入了新的失败模式（`stages_completed` 语义变化）。
5. **L-5 的严重性判定**：`BLOCKS_REAL_RUN=YES` 是否过强或过弱。
6. **§4 的不变量已由 Aaron 裁定（D.4），不在复核范围内。** 请 Codex 复核的是
   **代码是否确实符合该不变量**——特别是：除 `_expected_governance` 的
   commit 复核外，曝光后是否还有任何路径从实时 registry 取得会进入研究
   计算的输入。若有，则是违规，须报出。

## 7.1 「工程闸」这个判定说的是什么，不说什么

`ENGINEERING_GATE_FOR_STRATEGY_COUNCIL=PASS` 是本轮新出现的令牌，
故在此明确其外延，避免被读成比实际更强的东西：

**它只断言一件事**：截至本候选，**没有已知的、在范围内的工程缺陷阻挡
Strategy Council 开始方法讨论**。依据是——M6.1.7 的四条磁盘封存闭合
（独立复核 PASS，九项变异全被杀死）＋本轮 H-1 闭合（七项变异杀死）＋
全套件 2220 全绿＋registry／exposure／`runs/` 三项未动。

**它明确不断言**：

- **不**断言 `REAL_RUN_READY`——该值仍为 `NO`，且 **L-5 仍以
  `BLOCKS_REAL_RUN=YES` 挡在真实运行之前**；
- **不**断言 F-1／F-2 已闭合——两者**均仍为 PARTIAL**（见 §5）；
- **不**断言这些机制在真实路径上可用——生产今天在 `prepare` 即
  fail-closed，全部证据为**合成级**；
- **不**解除 `STRATEGY_COUNCIL` 的锁定。

**`STRATEGY_COUNCIL` 在本会话内仍为 `LOCKED`，本轮未改变这一点。**
先前 packet（`M6_1_4` §、`M6_1_6` §0）把 `STRATEGY_COUNCIL=LOCKED`
作为不变量携带；本轮的状态行改用工程闸令牌，是**任务书指定的汇报格式变更**，
**不是**对该锁的解除。二者并存且不冲突：工程闸 PASS ＝ 工程侧不再阻挡；
锁仍在 ＝ 本会话不开始方法讨论，须待 Codex 复核后在新会话启动。

## 8. 状态行

```
M6_1_8_H1=PASS
M6_1_7_DISK_SEAL=PASS
ENGINEERING_GATE_FOR_STRATEGY_COUNCIL=PASS
F1_OVERALL=PARTIAL
F2_OVERALL=PARTIAL
L5=OPERATIONS_REQUIRED_BEFORE_REAL_S0
REAL_RUN_READY=NO
REAL_S0_AUTHORIZED=NO
REGISTRY_CHANGED=NO
EXPOSURE_CHANGED=NO
```
