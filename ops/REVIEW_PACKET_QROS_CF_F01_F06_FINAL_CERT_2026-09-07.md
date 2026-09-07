＃ 送审包 —— QROS-CF F01/F02/F03/F05/F06 第二轮修复的**最终认证**

```ini
PACKET_TYPE=FINAL_CERTIFICATION_OF_A_REPAIR（沿用既有 Review Packet 件种,不是新件种;不是 A2,不是 Stage I,不解开任何 QROS 门）
REVIEW_ID=QROS-CF-F01-F06-FINAL-CERT-001
DELIVERY_STATUS=RETURNED
WITHDRAWN_BEFORE_DISPATCH=YES —— **本包从未派发,没有任何席位看过这些字节**。「RETURNED」是词表里表示「不在外面」的那个记号,不表示有过一轮复审
WITHDRAWN_REASON=打包过程中机械测出三条残留(R1/R2/R3),Aaron 授权了一次 PRE-CERT 定界修复;修复改动了本表钉住的字节,故先撤回再以**同一 REVIEW_ID** 重发
ISSUE_LINEAGE=同一条 F01–F06 谱系的第 3 轮（前两轮:P2 门禁复审 HOLD → 定向复审 HOLD）
ROUND_BUDGET=**合同预算之外**。ops/REVIEWER_CONTRACT.md 第 23 行为「每条 issue 谱系两轮」,已用尽;本轮由 Aaron 明确授权为一次业主例外。详见 §2.1
COMPANION=ops/NEXT_HANDOFF.md（禁读清单载体,**必须同行**;已按 sha256 钉在 §0.4 与 ARTIFACTS_UNDER_REVIEW.json）
PREPARED_BY=Claude Opus 5，repair-builder seat —— **本席位写了被审的修复,不得自审通过**
FOR=GPT-6 Astra，fresh session —— 最终认证，仅 F01/F02/F03/F05/F06
DECIDED_BY=Aaron —— **席位给判决,不代签;本包不裁定**
REPAIR_COMMIT=0d15a62e7611049ee2095e52d3d55d2037d698a5（第二轮）
PRIOR_REPAIR_COMMIT=f461f098a407ffc87dd0e2187c14ee4f4f00d1fd（第一轮,已被你上一轮判为不足）
HEAD=0d15a62e7611049ee2095e52d3d55d2037d698a5
HOLD_OF_RECORD=ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md
PRIOR_ROUND_PACKET=ops/REVIEW_PACKET_QROS_CF_F01_F06_REREVIEW_2026-09-07.md（DELIVERY_STATUS=RETURNED,谱系记录）
THREAT_VOCABULARY=ops/REVIEWER_CONTRACT.md（T1–T6）
REVIEWED_SET_UNCHANGED_SINCE=（由 ops/ARTIFACTS_UNDER_REVIEW.json 的 `unchanged_since` 承载,git 派生,不在本文键入）
THIS_PACKET_SHA256=（**不在此文件内**。送审文档无法自钉:把自身 hash 写进正文会产生新提交,新提交又改变 hash——2026-08-29 实测无不动点,见 tests/test_the_delivery_cannot_pin_itself.py。本包的 sha256 由 ops/ARTIFACTS_UNDER_REVIEW.json 中 `is_the_delivery_document: true` 那一条承载,并由 test_every_artifact_under_review_still_hashes_to_what_was_sent 每次运行核对。）
```

---

## 先读这一段 —— 本包最重要的内容不是「请验收修复」

Aaron 给本轮点了四个方向(§4)。本席位在打包前把四个方向各自机械测了一遍,
**其中三个,我自己测出来的答案是「否」**:

```
方向 1  可执行 .pth 的内容是否在它执行之前被约束     -> 否
方向 2  启动钩子能否在 attestation 之前碰受管模块并隐藏 -> 能
方向 3  是否每个受认可的真实运行入口都必须过 run_governed.py -> 否
方向 4  三个写者是否共享同一序列化原语「直到物理提交」 -> 文件写入是,提交不是
```

四条的测量、命令与我的判断写在 §4,**每条都标了它是我自己的测量,请独立复核**。

本轮的修复是真的修了被点名的五条 finding(§3),但**它没有覆盖 §4 的四个方向**——
那四个方向问的是比原 finding 更强的性质。Aaron 的本轮指令是**只做传输、不再修复**,
所以我把差距写出来交给你,而不是趁机再改一版字节。

如果你认为这四条中的任何一条足以构成 BLOCKING,那就是 BLOCKING;
**不要因为我先承认了就替我打折。**

---

## 0. 受审集 —— **先逐字节核对,再开工**

对下表每一行重算 sha256 并比对。**不符即 STOP 并报告。**
聊天里贴过来的字节永远不是真相来源;请从磁盘读。

`git commit id 不能替代声明的 sha256`:提交 id 证明历史,sha256 证明你手上
这些字节。工作树在 `0d15a62` 处干净(`git status --porcelain` 为空)。

### 0.1 修复产物(role = reference)

| sha256 | bytes | 路径 | 与哪条 finding 相关 |
|---|---|---|---|
| `426042211ace13777792fc911148a7ee81ab8abace756384ef35867d06820898` | `39484` | `src/itsf/execution_identity.py` | **F01**（`assert_governed_launch`、`LaunchAttestation`、`BOOTSTRAP_IMPORT_CLOSURE`）· **F02**（`EXPECTED_EXECUTABLE_PTH` 变为 name→sha256 映射、`startup_report`）· 两者接入 `seam_recheck` |
| `315bdf4e02340f465ef3cfad6270f7ed00ad5afcc76653e460ec40f038c281a3` | `4521` | `scripts/run_governed.py` | **F01/F02 新增**:受信启动边界。以 `-B` + 私有 `PYTHONPYCACHEPREFIX` 重启自身,在受管导入之前取 attestation |
| `dcf34cc27cbc4295af6690a2dccf7c328b9573a4f9c16c7d7357520cd5d24fac` | `34487` | `src/itsf/mc/registry_boundary.py` | **F06**（`_append_owner_row` + `append_owner_hold` / `append_owner_release`,与 P3 共用 `_AppendLock` 与 compare-and-swap;`_next_global_sequence`） |
| `e7f6b65cf82fe7f0fcd97e9762f64d7f1df3b0ff5c7b1b9dda4bb6a28638eef9` | `13579` | `src/itsf/mc/owner_control.py` | **F05**（`RUN_ID_FAMILIES` / `canonical_run_id_family`;`_SCOPE_RE` 只捕获不评级;查询侧同扫） |
| `eb6e499e4348f2a43138aaf24fa33cedda035b01d445b39a1d3e39ad44c9a17d` | `8050` | `src/itsf/data/manifests.py` | **F03**（权威归目录:官方清单存在时本地清单是拒绝而非降级）· **F04 已 CLOSED,其不变量在此保持** |
| `474a5c83f90ab4f13f698fc118564bbace3f8153d2faf245c54edf583963d4fc` | `13439` | `src/itsf/mc/production_inputs.py` | **F03**（`_manifest_data_files` 直接点名授权入口）· **F04 保持** |

### 0.2 真实运行入口(role = reference,**为方向 3 而入集**)

| sha256 | bytes | 路径 | 为什么在集内 |
|---|---|---|---|
| `9ba7ad59ed012112e700aac59451ec729660ca3fa25a3d89a9bf5ef74784b166` | `67929` | `src/itsf/mc/supplement_runner.py` | `seam_recheck` 在生产侧**唯一**的调用点(第 1384 行);本轮未改动此文件 |
| `f51d19a8e1768d4223a44145d79213d012a132d1933e9184662c786f7dd16ebc` | `161254` | `scripts/s0_real_run.py` | S0 真实运行入口脚本。**方向 3 的关键证据在此**;本轮未改动。文件很大,方向 3 只需其启动/入口面,不需通读 |

### 0.3 结算回归与元守卫(role = reference)

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `4ad08b01ef335854d707c9318a8de1d99e0f336f7afdf53d03b3da831ad44397` | `37341` | `tests/test_qros_cf_astra_round2.py` | **第二轮结算测试**,50 条:五条 finding 各自的反例 + 正向路径 |
| `2e800045bf09eb3e40636efeca7491eae6d0e57ffb6a515ab3b47f7c4b6b0f37` | `28383` | `tests/test_qros_cf_astra_repairs.py` | 第一轮结算测试。**其中两条曾把缺陷钉成不变量,本轮已重写并写明原因**,见 §3.3 |
| `31bb95295ebf21f228fa62417b70d700a1fb451104dcdfd0e3bd137056b962f6` | `25270` | `tests/test_execution_identity.py` | T-F01;seam 夹具新增注入 `launch` |
| `9a2c076eb5b38ced1d82069e4c5f4a77febd34c0aa963d96517aba736ad8b879` | `27226` | `tests/test_n09_scaffold_criteria.py` | **方向 4 的元守卫**:registry 写者集合与「导出写者不得把事件当参数」 |
| `8ff909d935b13be37eac969349c4ebbf16d9165aecc778b26043ece97393ae05` | `12646` | `tests/test_registry_path_single_construction.py` | 元守卫:registry 路径构造登记 |
| `985569a7cbe92db4a6a81a1e47233efc0270d9dabbab9dd7312350d8886d38d3` | `9728` | `tests/test_every_identity_pattern_is_swept.py` | 元守卫:`LINE_PARSERS` 声明(F05 的意图扫描为何不得锚定);本轮未改动 |

### 0.4 权威定义、谱系与随包件(role = reference)

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `c55d8f5675243519bc102f6ac9181e8276b4f867dff1e77881710713928806f9` | `7754` | `ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md` | **F01–F06 的权威定义**。原报告仅经聊天传递、从未落盘;该文件逐字说明它转录的是 Aaron 的派发陈述、不是 Astra 报告原文 |
| `8abdc702fe2e608717e97906053138a8f7f863f87da19a4826f9d51c3d600602` | `12245` | `ops/REVIEW_PACKET_QROS_CF_F01_F06_REREVIEW_2026-09-07.md` | **第 2 轮送审包**（已 RETURNED）。谱系记录:第一轮修复自报了什么、你判了什么。其 §0 表内的 hash 是**当时**的字节,现已改变——那是历史,不是错误 |
| `14e2d84defc6a77e408bba37806246d220e1bd2ee5af836a730843443d87d72a` | `5985` | `ops/REVIEWER_CONTRACT.md` | **T1–T6 威胁定义**、判决词表（PASS / PASS_WITH_BACKLOG / HOLD）、证据类别、轮次预算 |
| `7a0fd26969f68e1a4ac2de6167b03ebbb6c83368e1f6998dec93422485ab187a` | `11381` | `ops/BACKLOG.md` | F07/F08 作为 **B-22 / B-23** 的落点 |
| `5c9af31df771eb9c36ff8100b881b5efd17f4e69a2e80e5a42e76cec1961540d` | `6084` | `ops/RECOVERY_ANCHOR.md` | **允许的 outcome-clean 定位入口** |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | `2563` | `ops/OUTCOME_CARRYING_ARTIFACTS.json` | **隔离登记册**（quarantine register,机器可读,12 条） |
| `1cdd2dce3b33796e75f3dedfcac720704166f5d7a1bc93f2bde54a6f51de4c79` | `7424` | `ops/NEXT_HANDOFF.md` | **强制同行件**（本包 `COMPANION`,禁读清单载体）。第 2 轮曾声明它必须同行却未钉住——**你据此正确 STOP**;本轮它与本包在同一提交中落盘,上表 hash 即其最终字节 |

---

## 1. 禁读清单与入口(必须随每个交付载体同行)

- **隔离登记册**:`ops/OUTCOME_CARRYING_ARTIFACTS.json`。其上列出的任何路径都不得读取。
- **不得漫游仓库**:检索限于 §0 表内路径及其直接依赖。本次是定向认证而非盲审,
  但一次意外命中就烧掉这个席位,而烧席位不消耗研究自由度、却让本轮作废。
- **允许的 outcome-clean 入口点**:`ops/RECOVERY_ANCHOR.md`。
- 逐名点出的隔离锚点。【OFF-LIMITS】—— 下列每一条都是 outcome-carrying,**不得读取**:

【OFF-LIMITS】以下 12 条全部禁读(outcome-carrying)

```
EXPOSURE_LEDGER.md
ops/EXPOSURE_LEDGER.md
ops/outcome_quarantine/DECISION_PACKET_ND2_ND3.md
ops/outcome_quarantine/MC_DR5_BUILD_PACKET.md
ops/outcome_quarantine/MC_FACTORY_BOUNDARY_STAGE_I.md
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
ops/outcome_quarantine/ND2_ND3_FABLE_DECISION_PROMPT.md
ops/outcome_quarantine/ND2_ND3_RULING_REVIEW_FINDINGS.md
ops/outcome_quarantine/RULING_FABLE_FOUR_OPEN_2026-08-26.md
ops/outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
ops/outcome_quarantine/S0_T001_RESULT_DECISION_ADDENDUM.md
ops/outcome_quarantine/S0_T001_RESULT_REVEAL_ATTESTATION.md
```

这些文件携带 S0-T001 的**结果**。本轮只关心执行安全与数据身份,不需要任何
结果数字。**其中 `MC_TO_STRATEGY_MASTER_PLAN.md` 既 outcome-carrying、又曾是
项目的「恢复锚点」**——一个正常定位状态的审阅者会正面撞上去,2026-08-25 已有
一个 fresh 席位这样被烧掉。用 `RECOVERY_ANCHOR.md` 定位。

seat 轴台账 `ops/REVIEWER_EXPOSURE_LOG.md` 存在但**不在受审集内、也不必核对**;
本轮那一行在你归还之后才追加。研究轴台账禁读(已在上表)。

---

## 2. 范围

退出判据是余下五条 BLOCKING finding。原文定义见 §0.4 的转录件,不在此处重写——
改写成新表述会造成新的 finding 谱系。

```
F01  bytecode / source execution        T1   STILL_BLOCKING(第 2 轮)
F02  startup / import hook              T1   STILL_BLOCKING(第 2 轮)
F03  authorized manifest authority      T3   STILL_BLOCKING(第 2 轮)
F04  verify-consume same bytes          T3   **CLOSED —— 你在第 2 轮关闭,本轮不重开**
F05  malformed owner-control fail-open  T5   STILL_BLOCKING(第 2 轮)
F06  owner-hold / P3 serialization race T5   STILL_BLOCKING(第 2 轮)
```

**F04 保持 CLOSED。** 本轮改动了它所在的两个文件(`manifests.py`、
`production_inputs.py`),所以其不变量——「按 hash 验过的字节就是被消费的字节」——
在 `tests/test_qros_cf_astra_round2.py::test_F04_PRESERVED_...` 中被重新驱动。
若你发现本轮改动使 F04 失效,那本身是一条 finding。

**F07 / F08 在范围之外**,已作为 **B-22 / B-23** 记入 `ops/BACKLOG.md`。
Aaron 的指示:两者都不能产生未授权的 STARTED——F07 拒绝一个**合法**启动,
F08 **关闭**授权。**不得以它们阻挡本轮退出。**

不在范围、且不得在本轮重开的:架构、N10/N11/N13、任何真实运行、
研究结论/样本/成本/Primary 指标/promotion-falsified。
F01–F06 之外若发现新缺陷,记为新 finding 交 Aaron,不并入本轮退出判据。

### 2.1 轮次 —— 本轮在合同预算之外

`ops/REVIEWER_CONTRACT.md` 第 23 行:**每条 issue 谱系两轮**,跨改名、阶段与
新行连续计数。这条谱系的账:

```
第 1 轮  P2 门禁复审          -> HOLD,六条 BLOCKING(F01–F06)
第 2 轮  定向复审(第一轮修复) -> HOLD,F04 CLOSED,五条 STILL_BLOCKING
第 3 轮  本轮                 -> 预算已用尽,**Aaron 明确授权的一次业主例外**
```

写在这里是因为:**你完全有理由在自己发现合同被突破时 STOP**,而让你自己去发现
则是本席位的失职。这不是请求豁免——是把事实交给你和 Aaron。

**这是本谱系的最后一轮。** Aaron 的指示:若本轮仍为 HOLD,回到 Aaron,
不再有第四轮,也不再有 builder 的自动修复循环。

---

## 3. 第二轮修复的机制 —— **请当作待验证的声明,不是结论**

本席位写了被审代码。§0.3 的结算文件是以下每一条的可执行形式。
五条 finding 的反例都在**已修复过一次的树**(`33f2384`)上重新复现过,
然后才写这一轮的修复。

### 3.1 两个机制承载五条

| id | 第 1 轮留下的窟窿(你的原话所指) | 第 2 轮的机制 | 引入的拒绝码 |
|---|---|---|---|
| **F01** | 证明是一次**事后普查**:攻击者让伪造缓存执行完再删掉,普查就是干净的;而且读的是**可写的** `sys.dont_write_bytecode` 镜像 | 证明移到**受管导入之前**:`sys.flags.dont_write_bytecode`(只读 structseq,实测赋值抛 `AttributeError`)+ 私有前缀下零缓存 + `sys.modules` 内除 `itsf`/`itsf.execution_identity` 外无受管模块 | `launch_bytecode_writing_enabled` · `launch_pycache_prefix_unset` · `launch_pycache_prefix_absent` · `launch_pycache_prefix_not_empty` · `launch_governed_modules_already_imported` · `seam_launch_not_attested` |
| **F02** | 信任按**文件名**:允许名下装任意可执行内容即通过 | 钉**字节**:`EXPECTED_EXECUTABLE_PTH` 改为 name→sha256 映射,允许名而字节不符与未登记名同样拒绝 | `seam_startup_surface_unpinned`（沿用） |
| **F03** | 只有**一个**调用者被改到授权入口;四个生产调用点仍走偏好本地清单的入口 | 权威归**目录**:官方清单存在时本地清单是**拒绝**而非降级,一处改动同时关闭全部调用点(含未来新增) | `ManifestError`（未新增码） |
| **F05** | 畸形行已拒绝,但**合法解析**却 scope 非规范(`[MC-DS-S004-]`)的行仍然「适用于零个对象」 | scope 只经**拥有该文法的模块**路由(`SUPPLEMENT_ID_PATTERN` / `RUN_ID_RE` 两个族系),非规范即拒绝;**查询侧同扫** | `owner_control_scope_unrecognized` · `owner_control_query_run_id_unrecognized` |
| **F06** | 锁只有**一个参与者**:owner control 根本没有受认可的追加路径,hold 靠临时改文件落账,不取锁、不读 decided 快照 | 补上缺的另一半:`append_owner_hold` / `append_owner_release` 走**同一个** `_AppendLock` + compare-and-swap;序列号由 `_next_global_sequence` 派生而非手键 | `owner_append_*`（8 条,见 `registry_boundary.py`） |

### 3.2 一个被实现后否决的方向(第 1 轮已报,此处重申结论)

F01 的「校验缓存内容」路线先被实现而不成立:`marshal.dumps` 对等价 code object
不是字节稳定的(interning 顺序),结构化摘要需要已废弃的 `co_lnotab`,两者都在
无人改动的文件上误报(68 个可信缓存中分别 3 个与 7 个)。会误拒的门比没有门更糟。

**本轮新增的同类测量,请一并检视是否同意**:`-S`(以及蕴含它的 `-I`)会**从构造上
关闭 F02**,因为 `.pth` 根本不被处理——但实测 `import pandas` 在其下直接失败,
即用一个启动面换掉整个被钉环境。`-E` 会让解释器忽略 `PYTHONPYCACHEPREFIX`,
使前缀静默未设、仓库自己的 `__pycache__` 重新可读。所以最小兼容启动语义是
**只有** `-B` + `PYTHONPYCACHEPREFIX`。若你认为该取舍有误,这是一条应当提出的 finding。

### 3.3 两条测试曾把缺陷钉成不变量(本席位的缺陷,已重写)

第 1 轮的 `test_F03_the_legacy_loader_still_prefers_local_for_fixtures` 断言
「两者都存在时本地清单胜出」,并把它称为夹具需求。**那条偏好正是 F03 的替换通道**——
一条把修复前行为钉成不变量的测试。已重写并在测试内写明原因;其中真正承重的
半边(只有本地清单的夹具目录仍可用)保留并断言。另一条是 `.pth` 集合/映射断言。

### 3.4 元守卫的变动,无一被削弱

`test_n09_scaffold_criteria` 的写者集合从一个追加者扩到两个,**并且是作为 seam 的
成员而非例外**:CAS 仍然只能被 seam 调用。该守卫还抓到了本席位第一版
`append_owner_control_row(token, ...)`——它禁止导出写者把事件当参数
（「a general registry writer wearing a narrow name」)。**处置是改代码去迎合守卫,
不是放宽守卫**:拆成两个各自只命名一个事件的窄入口,私有 `_append_owner_row`
承载 token,守卫的规则从只查一个写者扩到查全部三个。

### 3.5 测试结果(本席位自报)

```
全套    5354 passed · 1 xfailed · 0 failed   （提交后重跑,HEAD 0d15a62）
xfail   B-20 见证归档命名缺陷,与本轮无关,未变动;无新增 xfail
工作树  git status --porcelain 为空
```

---

## 4. 四个方向 —— **Aaron 点名,本席位已各测一遍,三个答案是「否」**

以下每一条都是**本席位自己的测量**,证据类别为 SELF-REPORTED,
**请独立复核**。我给出命令与结论,不给出判决。

### 方向 1 —— 可执行 `.pth` 的内容是否在它**执行之前**被约束?

**我的答案:否。** `.pth` 在解释器启动、`site` 初始化时执行,**早于本项目任何一行
代码**;`startup_report()` 的字节校验发生在 `seam_recheck` 处,也就是**它已经执行
之后**。第 2 轮把「按名信任」换成「按字节信任」,这确实关闭了「允许名装任意内容
仍报 pinned」的反例——但它把 F02 从「名不可信」修到了「字节可验」,**没有**修到
「执行前受约束」。

可以想到的闭合方式是在**父进程**里做:`scripts/run_governed.py` 本来就要重启一次
子进程,在重启**之前**校验 `.pth` 字节,不符就不启动。**现在没有这么做**,
而 Aaron 本轮的指令是只做传输、不再修复,所以我没有加。

请判断:这是否构成 BLOCKING,以及威胁归 T1 还是别处。

### 方向 2 —— 启动钩子能否在受信启动 attestation 之前碰受管模块,并**隐藏**这件事?

**我的答案:能,而且我测出来了。** attestation 的第三条事实是
「`sys.modules` 内除 `BOOTSTRAP_IMPORT_CLOSURE` 外没有受管模块」。一个在启动时
执行的钩子可以先 `import itsf.mc.owner_control`,再把它从 `sys.modules` 里删掉:

```
实测(本席位,进程内):
  导入后再删除的:  itsf.mc, itsf.mc.mc_contract, itsf.mc.owner_control,
                   itsf.mc.supplement_contract, itsf.mc.supplement_registry
  删除后仍可见的:  itsf          <- 正是 closure 允许的集合
  => assert_governed_launch() 会通过
```

也就是说 attestation 的第三条事实**可以被清扫掉**,而被伪造缓存执行过的副作用
(打过的猴子补丁、改过的模块属性)不会随 `sys.modules` 条目一起消失。
`sys.modules` 是**当前状态**,而第三条事实想证明的是**历史**——这与第 1 轮
F01 被你打破的形态是同一个,只是换了一层。

我没有把这条写进 §3 的「已修」,因为它没修。请判断其严重性。

### 方向 3 —— 是否**每个**受认可的真实运行入口都必须过 `scripts/run_governed.py`?

**我的答案:否。**

```
实测(grep,本席位):
  scripts/s0_real_run.py  中 seam_recheck / assert_governed_launch /
                          execution_identity 的出现次数:0
  生产侧 seam_recheck 调用点:仅 src/itsf/mc/supplement_runner.py:1384
```

所以 attestation 只强制覆盖 **P3 seam 那一条路径**(MC-DS 补充运行)。
`scripts/s0_real_run.py` 是 S0 真实运行入口,它不经过 seam,也不经过 attestation;
一个从它启动的真实运行不会因为缺少 attestation 而拒绝。

§3 里我写「机制化强制而非事后检查」——**那句话对 P3 seam 成立,对「每个真实运行
入口」不成立**。这正是本项目反复出现的形态「声称宽于事实」,而这次是我自己。
请核对并判断。

### 方向 4 —— 每个受支持的 `OWNER_HOLD` / `OWNER_RELEASE` / `STARTED` 写者是否共享
同一序列化原语,**直到物理提交**?

**我的答案:文件写入是,物理提交不是。**

仓内三个写者(`append_run_started`、`append_owner_hold`、`append_owner_release`)
确实都经 `_append_owner_row` / 直接走 `_AppendLock` + compare-and-swap,
`test_n09_scaffold_criteria` 机械断言「模块内恰好一处 registry 字节写入,在 CAS 内,
CAS 只能被这三者调用」。**到文件写入为止,答案是「是」。**

但 registry 不在本仓:

```
REGISTRY_REPO_ROOT = C:\Users\Aaron\quant-data\itsf-registry
本仓                = ...\Intraday Trend Strategy Framework   (不同仓)
生产追加路径中执行 git commit 的地方:无
```

追加只写文件;把它**提交**是之后另一次动作,发生在锁之外、另一个仓里,由人或
其他工具完成。所以「直到物理提交」这一段没有被同一原语覆盖:两次追加可以正确
序列化,而它们的提交顺序不由这把锁决定。

请判断这是否落在 F06 的范围内,还是一条应当单列的新 finding。

---

## 5. 请你做的事

1. 逐行重算 §0 的 sha256;不符即 STOP 并报告。
2. 以 §0.4 的转录件为 F01–F06 的定义,**独立复现每条原始反例**——不要以本包的
   复现记录代替你自己的。
3. 判断第二轮的每条修复是否恢复了被声明的不变量,以及是否引入新的失败面。
4. **§4 四条逐条明确作答**,并说明你的答案是 REPRODUCED 还是 REASONED。
   我的答案是 SELF-REPORTED,不能作为你的证据。
5. 用 `ops/REVIEWER_CONTRACT.md` 的词表给出判决:`PASS` / `PASS_WITH_BACKLOG` /
   `HOLD`。每条 BLOCKING 须点名恰好一个威胁(T1–T6)、一条具体失败路径、
   及其证据类别(REPRODUCED / REASONED / SELF-REPORTED)。
6. 区分**你复现的事实**与**本席位自报的测量**。后者集中在 §3 与 §4。

不要修改任何文件。不要执行 `qros`。不要追加任何 registry 事件。不要写入仓库。

---

## 6. 本包不做的事

不接受、不裁定、不关闭任何 finding。F01/F02/F03/F05/F06 在一个新的独立席位
另有结论之前保持 BLOCKING,而那个结论由 Aaron 派发与记录——不由写了这份修复的
席位给出。**本包也不主张 §4 的四条已被处理**:三条我自己测出的答案是「否」,
它们写在这里是为了交给你,不是为了先行结案。
