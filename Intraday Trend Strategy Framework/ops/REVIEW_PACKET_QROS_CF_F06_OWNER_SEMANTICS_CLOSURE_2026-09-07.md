＃ 送审包 —— F06 OWNER-SEMANTICS 修复的**后续结案认证**

```ini
PACKET_TYPE=FOLLOW_UP_CLOSURE_CERTIFICATION（沿用既有 Review Packet 件种,不是新件种;不是 A2,不是 Stage I,不解开任何 QROS 门）
REVIEW_ID=QROS-CF-F06-OWNER-SEMANTICS-CLOSURE-001
PARENT_REVIEW_ID=QROS-CF-F01-F06-FINAL-CERT-001
PARENT_RESULT=**HOLD** —— 已完成的最终认证。**I1/I2 NOT SAFE TO ACTIVATE**。确认阻断项 `F06-OWNER-SEMANTICS = STILL_BLOCKING`
PARENT_RECORD_INTACT=YES —— `ops/REVIEW_PACKET_QROS_CF_F01_F06_FINAL_CERT_2026-09-07.md` 保留为历史证据,**未被改写为 PASS**;其 `RETURNED_VERDICT` 就是那次 HOLD
DELIVERY_STATUS=RETURNED
RETURNED_VERDICT=**HOLD** —— GPT-5.6 Sol XHigh substantive closure review。**I1/I2 NOT SAFE TO ACTIVATE**。剩余失败被收敛为两个根阻断族：TRUSTED-LAUNCH TRUST-ROOT PLACEMENT 与 F06 START-PATH COMPLETENESS
RETURNED_NOTE=本记录是**历史证据**，不得被改写为 PASS。Aaron 据此授权了**一次**定界的最终修复（设计依据：ops/FABLE_DESIGN_REVIEW_QROS_CF_FINAL_2026-09-07_TRANSCRIPTION.md）；后续只做一次**封闭范围**的机械结案检查（A1-A6 / B1-B4 / S）
THIS_IS_NOT_THE_OLD_CERTIFICATION_CONTINUING=正确。父认证已完成并给出 HOLD;本件是**另一个 review id** 下的后续结案认证
F06_OWNER_SEMANTICS_REPAIR_COMMIT=d28ced1f2573e9b396f0cb9ed0e319de1b76c869
HEAD=d28ced1f2573e9b396f0cb9ed0e319de1b76c869
PREPARED_BY=Claude Opus 5，repair-builder seat —— **本席位写了被审的修复,不得自审通过**
FOR=GPT-6 Astra，fresh session
DECIDED_BY=Aaron —— **席位给判决,不代签**
COMPANION=ops/NEXT_HANDOFF.md（禁读清单载体,**必须同行**,已按 sha256 钉住）
HOLD_OF_RECORD=ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md
THREAT_VOCABULARY=ops/REVIEWER_CONTRACT.md（T1–T6）
THIS_PACKET_SHA256=（**不在此文件内**;由 ops/ARTIFACTS_UNDER_REVIEW.json 中 `is_the_delivery_document: true` 那一条承载）
```

---

## 0. 本次要结案的问题 —— 两组,不是一组

父认证以 HOLD 收尾,因此当时**没有必要**再往下处理其余各项。本件要把两件事一起结掉:

```
① 修复后的 F06 OWNER SEMANTICS   —— 独立验证(本轮修复的对象)
② 因父 HOLD 而搁置的处置        —— F01 · F02 · SANCTIONED_REAL_RUN_ENTRY
                                   · FLAG_PATH_BYPASS · F03 · F05
F04                              —— 仅保全;除非回归,不重开
```

**F04 保持 CLOSED。** 若本轮改动使其失效,那本身是一条 finding。

---

## 1. 确认失败的原样复现,与修复

### 1.1 复现(修复前,逐步驱动)

```
1. 最终 owner/control 检查通过   （S0 侧即 pre-exposure recheck: registry == Stage-A 快照）
2. 可适用且未释放的 OWNER_HOLD 落账
3. 进行中的转换追加 RUN_STARTED
4. 转换成功返回
提交顺序实测: ['RUN_AUTHORIZED', 'OWNER_HOLD', 'RUN_STARTED']
```

### 1.2 两个成因,都成立

```
① S0 start 路径**根本没有任何 owner-control 检查** —— 实测:对
   scripts/s0_real_run.py 与 src/itsf/s0/ 搜 owner_control / active_holds /
   assert_no_owner_hold,零命中;且它以 decided=None 追加,因此没有东西能察觉
② supplement 路径**确实检查了**,但读的是**进锁之前**的字节。它的
   compare-and-swap 使其在**效果上**安全 —— 而「因为另一个机制恰好接住了所以安全」
   不是合同要求的东西
```

### 1.3 修复(定界,靠复用)

```
serialized_append(target, addition, *, decided=None, validate=None)
    锁内、读后、写前调用 validate(now) —— now 就是将被提交的那批字节
serialized_start_append(target, addition, *, run_id, decided=None)
    把「可适用 hold」判断作为 validate 传入
两条 start 路径都经它提交
```

同一把 `_AppendLock`、同一次物理写入、同一批解析器、同一套规范文法、同一套适用性逻辑。
**没有第二把锁、第二个 registry、第二本 owner 台账、每写一次 git 提交的规则、
平行状态机、新的治理子系统。**

**owner 判断排在过期快照比较之前**（已断言）:两者都会触发时,操作者应当被告知
「有人叫停了你」,而不是「文件恰好动了」。

### 1.4 非 start 事件**没有**被卷进来

`START_EQUIVALENT_TOKENS = (SUPPLEMENT_RUN_STARTED, RUN_STARTED, MC_RUN_STARTED)`。
最后一个今天没有写者,列进来是为了让将来的写者**继承**这条拒绝而不是需要记得它。
`**TOKEN**` 与带空格的拼法解析为同一答案（行文法允许粗体,躲在星号后面的 start
正是这套分类要挡的东西）。

**通用有序追加保持原语义**:用例 I 在**一条生效的 GLOBAL hold 之下**证明非 start
事件仍然提交成功——把 start 拒绝施加到每一个 registry 事件上会是另一件事,而且是错的。

### 1.5 一个必须交代的边界

S0 的 trial id `S0-T001` **不是**规范族系,而 `[S0-T001]` 作为 **scope** 会被
`parse_owner_rows` 拒绝（F05）。所以对一个 S0 trial 而言,**能适用的 hold 全集就是
GLOBAL 那些**,GLOBAL-only 的回答没有丢掉任何**存在的**能力。

若要支持 scoped S0 hold,那是规范 run-id 文法的扩展、是关于 F05 的决定,
**不属于本次定界修复**。这一点写成了断言,而不是留作假设。

---

## 2. 受审集 —— 先逐字节核对,再开工

对下表每一行重算 sha256 并比对。**不符即 STOP 并报告。** 工作树在 `d28ced1f2573e9b396f0cb9ed0e319de1b76c869` 处干净。

**只钉了对上述结案问题有实质语义依赖的文件。** 没有做整仓递归钉定;
被顺带 import 的模块、标准库与第三方内部不因被 import 而成为受审件。

### 2.1 ① F06 OWNER SEMANTICS

| sha256 | bytes | 路径 | 与哪个结案问题相关 |
|---|---|---|---|
| `942fd1511c0dd2be04e4574303f7d753c9e2234f29b877c8614186ed4d024eb6` | `41459` | `src/itsf/mc/registry_boundary.py` | **F06 修复的核心**：`serialized_append` 新增 `validate` 回调（锁内、写前、对将被提交的字节执行）；`serialized_start_append` 把「可适用 hold」判断作为该回调传入；`START_EQUIVALENT_TOKENS` / `is_start_equivalent` |
| `29941d3d5306cb1a3e8951f662068c91e2beed49a3fcb44f47785a8ce72317bc` | `16235` | `src/itsf/mc/owner_control.py` | **F06**：`holds_applicable_to_start` / `assert_no_hold_blocks_start`；`_live_holds` 抽出以免两处适用性答案漂移。**`active_holds` 未改**——它对非规范查询 id 的拒绝是 F05 的查询侧扫描，原样保留 |
| `c9c43a00582c262eb95cd53cb1094285aa0af4b62f53512806fa69dd8c2adfe3` | `80658` | `src/itsf/s0/runner.py` | **F06**：`append_registry_event_line` 现按事件分派——start-equivalent 走start 入口，其余走通用序列化入口；`_atomic_run_start` 是真实 S0 转换 |
| `f51d19a8e1768d4223a44145d79213d012a132d1933e9184662c786f7dd16ebc` | `161254` | `scripts/s0_real_run.py` | 把受管 REGISTRY 传给上面那个写者的调用点（第 3174 行）。**本轮未改动** |
| `9ba7ad59ed012112e700aac59451ec729660ca3fa25a3d89a9bf5ef74784b166` | `67929` | `src/itsf/mc/supplement_runner.py` | supplement 侧的 start 入口；`seam_recheck` 唯一生产调用点。**本轮未改动** |
| `e05f0a21098733f014bd6a7e2bd02a0a42a29a9e7e53155425ef47c5cb3dd594` | `27084` | `tests/test_qros_cf_f06_owner_semantics.py` | **F06 结算测试，25 条**：确认失败的原样复现（C）、A–J 十组确定性顺序、真实 S0Runner 转换端到端、以及 start 语义完整性守卫 |
| `46ac08768185bf92a7a1ce7ec27e965c1beb155dd738c0de84279d15a1a0b011` | `21477` | `tests/test_qros_cf_f06_writer_completeness.py` | 写者完整性（跨模块）。**其中两条曾把本次缺陷断言为正确行为，已倒转并写明理由**——请特别核这两条 |
| `e93a75e44c72d77d19abf72c7cd0d923d4b719ddd1e19e34f6924c19fbc0e24f` | `34389` | `src/itsf/mc/supplement_contract.py` | F05/F06：supplement 族系与行/序列文法 |
| `817419cd5910fd352bf291c8c74d6e4723cc6afefcd1a1f5fe3cb1326bd88e34` | `10894` | `src/itsf/mc/mc_contract.py` | F05/F06：MC 族系 `RUN_ID_RE` |
| `ff4ba0f66aee5625e4ee1d53d915bfc3e78cf31c110dd0cf6bd85d579e2042b5` | `72459` | `src/itsf/mc/supplement_registry.py` | 共享行解析器与 GLOBAL 序列规则 |
| `499224b94113f47333fc2d2e8f2d3bcf6b24bc803a699d7419f51a716e1b3ede` | `13331` | `src/itsf/mc/registry_integrity.py` | 以 MC 族系 id 调用 owner 检查的地方 |
| `774cd76f927effa4560e699f4243269d833b34f09dbd8fff800044fe39d9b652` | `37130` | `src/itsf/mc/supplement_authority.py` | 授权层 |

### 2.2 ② F01 / F02 与受信启动

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `d4cedff56a0711e3dcdf7680b2c11d77c15ce03156a8d817ef2872a4f9dd861d` | `44099` | `src/itsf/execution_identity.py` | **F01/F02**：只读 `sys.flags.no_site` 事实、`LaunchAttestation`、启动面按字节钉定、`classify_startup_artifact` |
| `f51f166ad4fc18db8a8cd12201dcfd3adf1e86e670bf2a6ec490a8f21437714b` | `10328` | `scripts/run_governed.py` | **F01/F02**：两进程受信启动边界 |
| `45373b43985f99747ce42f603fc09a0b3ab03f079645658b5a10bf6f680bb6f2` | `209` | `scripts/run_governed.cmd` | 让父进程本身在 `-S` 下启动 |
| `311eefa4141629bbf302221ed5af3b6fcaf077be6542262d459c73a82620209c` | `27206` | `tests/test_qros_cf_pre_cert.py` | F01/F02/R3 的结算测试，30 条 |
| `31bb95295ebf21f228fa62417b70d700a1fb451104dcdfd0e3bd137056b962f6` | `25270` | `tests/test_execution_identity.py` | T-F01 |

### 2.3 ② SANCTIONED_REAL_RUN_ENTRY 与 FLAG_PATH_BYPASS

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `2e850c8dd099a7b7c6dae87a14c4dfc23dbef240b489d7a27f73b8fc66ce3e61` | `6022` | `src/itsf/guards.py` | **SANCTIONED_ENTRY**：`assert_trusted_launch`，在单一真实运行门内以生产默认旗标为条件要求。**FLAG_PATH_BYPASS 的条件与它不覆盖什么都写在 docstring** |
| `c34a9d13368eb4106d432c0b77ce25f7fd8e56f43642e5d1dee4f20e46c6d41a` | `6148` | `src/itsf/data/dbn_loader.py` | **FLAG_PATH_BYPASS 的关键证据**：`load_real` 以 loader 自己的旗标调用那道门 |
| `f0035e1d5e2f3ca5b8c6189dcb6196970ddc79263cbf4dca008ff253a4d94d4b` | `11560` | `src/itsf/data/cost_calibration_loader.py` | 同一旗标接缝，三处 |
| `27a4d763fc7c58b498a50d8b738d4846fdc5b8a4ce7d818e3167e2934e6c5db6` | `9312` | `src/itsf/mc/account.py` | SANCTIONED 入口 `run_real_study`——**两份清单都缺过它** |
| `272a804505b5ba51acc4ac62ca5c044a616213d770672f3330205352c8232088` | `24144` | `src/itsf/mc/orchestrator.py` | SANCTIONED 入口 `run_real_lifecycle`——同上 |
| `e37bd5c2cd434568b16645f4a36970b2f2df5aeff02aaf8bee3e39cf7670b6d7` | `165998` | `src/itsf/mc/consumer.py` | SANCTIONED 入口 `run_real_mc` |
| `b07827067ed68033f1b21834f680546ef7f2c99629fb71c78deab62fdc76ea2a` | `4649` | `src/itsf/mc/real_input.py` | 两个 SANCTIONED 入口 |
| `66d746d83e76fcfc2145820e5262025bf27ad50538d671dbbbeca80600d393bd` | `4658` | `scripts/run_data_qa.py` | SANCTIONED 入口 |
| `9d0e6134d814b869482a3ed8bffe77afa5119158ed4d4afa9146832dcda834d5` | `11135` | `scripts/qa_addendum_a1.py` | SANCTIONED 入口 |
| `faf6ee467ffb18b04070b71719016587b1f0ddb00a77c901b144877e66aca12f` | `2428` | `scripts/qa_addendum_a2.py` | SANCTIONED 入口 |
| `21512097b688bade80eb185d39ace0413dd7d2a1cbc7e54818afa1ce26e9f512` | `67832` | `scripts/s0_input_preflight.py` | SANCTIONED 入口（默认旗标 loader） |

### 2.4 ② F03 / F05（F04 仅保全）

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `eb6e499e4348f2a43138aaf24fa33cedda035b01d445b39a1d3e39ad44c9a17d` | `8050` | `src/itsf/data/manifests.py` | **F03**（权威归目录）· **F04** 不变量 |
| `474a5c83f90ab4f13f698fc118564bbace3f8153d2faf245c54edf583963d4fc` | `13439` | `src/itsf/mc/production_inputs.py` | **F03/F04** 的受管读取点 |
| `58b0bf6ffda1ff53088091d31ec9e88b468f8846f8763d65ef74011c6fada800` | `29976` | `tests/test_qros_cf_astra_repairs.py` | 第一轮结算测试（F03/F04/F05） |
| `78bbfd4c96e585a654ff444bb0ae440bb0d9270ec14b86d664ae8b347d6a7c28` | `40040` | `tests/test_qros_cf_astra_round2.py` | 第二轮结算测试（F03/F05） |

### 2.5 元守卫与支撑

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `6080c6e9d163e96c945c43636f07a40f31f1e8c0b6ab129a2c1abdd31a52a337` | `32391` | `tests/test_n09_scaffold_criteria.py` | 写者集合元守卫。本轮 SEAM 扩到含 `serialized_start_append` |
| `0555b361354ee0ebdadb904f84d91509eabea2571d41896321f8dc99d3966033` | `13709` | `tests/test_registry_path_single_construction.py` | 路径构造登记 |
| `985569a7cbe92db4a6a81a1e47233efc0270d9dabbab9dd7312350d8886d38d3` | `9728` | `tests/test_every_identity_pattern_is_swept.py` | F05 意图扫描声明 |
| `67a91c9ede5a8a53bceccafb39102cd5ce083cb2ca4cbf087aa56360bbe89c71` | `7231` | `tests/conftest.py` | 测试收集与夹具 |
| `d441aad613d6f1138a67d166434084f4d8792a2a23eb40091325fd33a102a136` | `5347` | `tests/tiers.py` | A+B 层映射 |
| `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `0` | `src/itsf/__init__.py` | **0 字节**——`BOOTSTRAP_IMPORT_CLOSURE` 依赖的实测事实 |
| `97d50740d938cb40eccab6595e6ba7284c493e9a662e311ddce31700f294a002` | `64677` | `src/itsf/contracts.py` | `RunConfig` / `TrialState` / 受裁定根 |
| `888d639194578b8d22d93e4d61ab87d2cb8860d00759bfc1994f5b27c4f3b276` | `90687` | `src/itsf/s0/runinfra.py` | S0 运行基础设施（写者规则的候选，已分类为非 registry） |

### 2.6 因先前各轮而改动的既有测试 —— **请特别检查是否被削弱**

| sha256 | bytes | 路径 | 本轮/前轮改了什么 |
|---|---|---|---|
| `85aae1bcb6cd494a13e099452e3d49ecc5e9bfd3b1b5d5f08fe10fa3141d2c50` | `31800` | `tests/test_mc_consumer.py` | 受信启动拒绝前移后注入 launch 事实 |
| `100a1b22a84c7da1bac7a372fda4d2784ecf82208dae4f78d733e2c6e61a1f83` | `36197` | `tests/test_mc_supplement_integration.py` | 同上 |
| `4ddba05a6e334af77b68c55f51db0f3f898f50ea2b0c7178b1f8119006a921d6` | `39363` | `tests/test_mc_supplement_runner.py` | 同上 + 首个拒绝前移 |
| `6b0d2d88218b4bc241b630267e743476bc4bd1e4f9a4129cfc0d4b38a1561871` | `6276` | `tests/test_supplement_prepare_boundary.py` | 同上 + 新增外层拒绝断言 |
| `6ab114630876d365f53b24c8f96dfcd693a96279e9d28ccbaa3051af3f8d8999` | `9389` | `tests/test_what_the_registry_append_unlocks.py` | 同上 |

### 2.7 权威定义与谱系

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `c55d8f5675243519bc102f6ac9181e8276b4f867dff1e77881710713928806f9` | `7754` | `ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md` | **F01–F06 的权威定义** |
| `70a5a88add2ea19d1cc5526f11c2ceb767447258f999d56cd2a2361d83b1b010` | `40235` | `ops/REVIEW_PACKET_QROS_CF_F01_F06_FINAL_CERT_2026-09-07.md` | **父谱系的最终认证包，已 RETURNED，verdict=HOLD**。**这是历史证据，未被改写为 PASS**；其 §0 的 hash 是当时的字节 |
| `8abdc702fe2e608717e97906053138a8f7f863f87da19a4826f9d51c3d600602` | `12245` | `ops/REVIEW_PACKET_QROS_CF_F01_F06_REREVIEW_2026-09-07.md` | 第 2 轮送审包 |
| `14e2d84defc6a77e408bba37806246d220e1bd2ee5af836a730843443d87d72a` | `5985` | `ops/REVIEWER_CONTRACT.md` | T1–T6、判决词表、证据类别 |
| `7a0fd26969f68e1a4ac2de6167b03ebbb6c83368e1f6998dec93422485ab187a` | `11381` | `ops/BACKLOG.md` | F07/F08 = B-22 / B-23 |
| `5c9af31df771eb9c36ff8100b881b5efd17f4e69a2e80e5a42e76cec1961540d` | `6084` | `ops/RECOVERY_ANCHOR.md` | 允许的 outcome-clean 定位入口 |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | `2563` | `ops/OUTCOME_CARRYING_ARTIFACTS.json` | 隔离登记册（12 条） |
| `5200e6dd9d28663235b586d1fc7d9752db3d175accf55dd32c20c8b10b98cb59` | `7536` | `ops/NEXT_HANDOFF.md` | **强制同行件**，禁读清单载体 |

---

## 3. 禁读清单与入口

- **隔离登记册**:`ops/OUTCOME_CARRYING_ARTIFACTS.json`,其上任何路径都不得读取。
- **允许的 outcome-clean 入口**:`ops/RECOVERY_ANCHOR.md`。
- 检索限于 §2 表内路径及其直接依赖。**对 `src/` 与 `scripts/` 做 AST 扫描是被
  明确许可的**（只读项目源码,不触及 `ops/`,因此不可能命中隔离件）;**不要**把
  扫描扩到 `ops/`。

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

其中 `MC_TO_STRATEGY_MASTER_PLAN.md` 既 outcome-carrying、又曾是项目的「恢复锚点」,
一个正常定位状态的审阅者会正面撞上去;2026-08-25 已有一个 fresh 席位这样被烧掉。
用 `RECOVERY_ANCHOR.md` 定位。

seat 轴台账存在但**不在受审集内、也不必核对**;本轮那一行在你归还之后才追加。

---

## 4. 基准怀疑度 —— 本席位在这条谱系上错过四次,形态相同

```
第 1 轮修复  五条修复各自通过我写的结算测试,你仍复现了五条反例
第 2 轮修复  我写「机制化强制」,而它对 P3 seam 成立、对每个真实运行入口不成立
第 2 轮测量  我写「-S 不能用」,真相是「-S 单用不能,加显式 site 目录可以」
本轮之前     我写「三个受支持写者共享同一原语」,而第四个受支持写者在序列化之外
```

**而本轮还多一种**:我为关闭上一条 F06 缺陷而写的测试文件,**把本次这条缺陷
断言成了正确行为**（说 S0 追加应当排在 hold 之后）。只检查你修好的那一半的测试,
会心平气和地为你没修的那一半背书。两条已倒转并写明理由,列在 §2.1。

**请假设同类错误还在。**

---

## 5. 请你做的事

1. 逐行重算 §2 的 sha256;不符即 STOP。
2. **独立复现 §1.1 的确认失败**,再验证修复后它不可能发生。
3. 逐条核对 §2.6 与 §2.1 里那两条被倒转的测试,**判断有无测试被削弱**。
4. 对 §0 的两组问题分别给出结论;`F04` 只需保全判断。
5. 用 `ops/REVIEWER_CONTRACT.md` 的词表给出判决:`PASS` / `PASS_WITH_BACKLOG` /
   `HOLD`。每条 BLOCKING 须点名恰好一个威胁(T1–T6)、一条具体失败路径、
   及其证据类别(REPRODUCED / REASONED / SELF-REPORTED)。
6. 区分**你复现的事实**与**本席位自报的测量**。

不要修改任何文件。不要执行 `qros`。不要追加任何 registry 事件。不要写入仓库。

---

## 6. 本包不做的事

不接受、不裁定、不关闭任何 finding。**父认证的 HOLD 记录保持原样,不因本件而变成
PASS。** I1/I2 是否可以激活由 Aaron 裁定,不由写了这份修复的席位给出。
