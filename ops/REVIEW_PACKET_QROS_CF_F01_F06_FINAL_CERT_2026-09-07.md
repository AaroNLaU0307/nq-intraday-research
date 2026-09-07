＃ 送审包 —— QROS-CF F01/F02/F03/F05/F06 最终认证（PRE-CERT 修复后重发）

```ini
PACKET_TYPE=FINAL_CERTIFICATION_OF_A_REPAIR（沿用既有 Review Packet 件种,不是新件种;不是 A2,不是 Stage I,不解开任何 QROS 门）
REVIEW_ID=QROS-CF-F01-F06-FINAL-CERT-001
DELIVERY_STATUS=ISSUED
REISSUE=YES（第 2 次）—— 本次因 **Astra 在实质认证前的传输停止**：入口/写者清单需要更多源文件的字节。**这不是一条 finding,不是新的一轮,不是新 id**。前一次重发的原因是 —— **同一 REVIEW_ID 重发,不是新的复审谱系**。首版打包完成后从未派发;打包过程中机械测出三条残留,Aaron 授权了一次 PRE-CERT 定界修复,修复改动了首版钉住的字节,故撤回并按同一 id 重发。**没有任何席位看过任何一版**
PRE_CERT_REPAIR_COMMIT=81c0d22ab9df7bfc5f99224bd1e89af0fd7178af
SECOND_ROUND_REPAIR_COMMIT=0d15a62e7611049ee2095e52d3d55d2037d698a5
FIRST_ROUND_REPAIR_COMMIT=f461f098a407ffc87dd0e2187c14ee4f4f00d1fd
HEAD=81c0d22ab9df7bfc5f99224bd1e89af0fd7178af
ISSUE_LINEAGE=同一条 F01–F06 谱系。**轮次未被重置**:PRE-CERT 修复不是一轮复审,它没有派发过任何席位
ROUND_BUDGET=**合同预算之外**。ops/REVIEWER_CONTRACT.md 第 23 行为「每条 issue 谱系两轮」,已用尽;本轮由 Aaron 明确授权为一次业主例外。详见 §2.1
COMPANION=ops/NEXT_HANDOFF.md（禁读清单载体,**必须同行**;已按 sha256 钉在 §0.5 与 ARTIFACTS_UNDER_REVIEW.json）
PREPARED_BY=Claude Opus 5，repair-builder seat —— **本席位写了被审的修复,不得自审通过**
FOR=GPT-6 Astra，fresh session —— 最终认证，仅 F01/F02/F03/F05/F06
DECIDED_BY=Aaron —— **席位给判决,不代签;本包不裁定**
HOLD_OF_RECORD=ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md
THREAT_VOCABULARY=ops/REVIEWER_CONTRACT.md（T1–T6）
REVIEWED_SET_UNCHANGED_SINCE=（由 ops/ARTIFACTS_UNDER_REVIEW.json 的 `unchanged_since` 承载,git 派生,不在本文键入）
THIS_PACKET_SHA256=（**不在此文件内**。送审文档无法自钉;由 ops/ARTIFACTS_UNDER_REVIEW.json 中 `is_the_delivery_document: true` 那一条承载）
```

---

## 先读这一段 —— 首版承认的三条「否」,本轮已修;请核这三条修复

首版打包时,本席位把 Aaron 点的四个方向各机械测了一遍,**其中三个答案是「否」**。
Aaron 随后授权了一次**定界的 PRE-CERT 修复**（不是一轮复审,没有派发任何席位）。
本版的受审对象就是那次修复。

```
方向 1  可执行 .pth 的内容是否在它执行之前被约束      首版: 否   本版: 是（改为「阻止执行」）
方向 2  启动钩子能否在 attestation 之前碰受管模块并隐藏  首版: 能   本版: 不能（无钩子可运行）
方向 3  是否每个受认可的真实运行入口都被受信启动约束    首版: 否   本版: 是（单一真实运行门）
方向 4  三个写者是否共享同一序列化原语直到物理写入      首版: 文件写入是  本版: 未变,并新增动态证明
```

**方向 4 没有改成「直到 git 提交」**,这是 Aaron 的明确指示:registry 在另一个仓,
科学与安全的不变量是**顺序与落盘字节**,不是 git 历史的形态。本版只补了证明。

§4 逐条给出机制、命令与我的测量。**每一条都是本席位自己的测量,请独立复核。**

---

## 0. 受审集 —— **先逐字节核对,再开工**

对下表每一行重算 sha256 并比对。**不符即 STOP 并报告。**
聊天里贴过来的字节永远不是真相来源;请从磁盘读。

工作树在 `81c0d22ab9df7bfc5f99224bd1e89af0fd7178af` 处干净。

### 0.1 本轮修复产物(role = reference)

| sha256 | bytes | 路径 | 与哪条相关 |
|---|---|---|---|
| `d4cedff56a0711e3dcdf7680b2c11d77c15ce03156a8d817ef2872a4f9dd861d` | `44099` | `src/itsf/execution_identity.py` | **F01/F02**（`assert_governed_launch` 新增只读 `sys.flags.no_site` 事实；`LaunchAttestation.no_site`；`classify_startup_artifact`；`LAUNCH_FLAGS_REQUIRED` 由 `-B` 改为 `-S -B`——**这条是对第二轮结论的更正**） |
| `f51f166ad4fc18db8a8cd12201dcfd3adf1e86e670bf2a6ec490a8f21437714b` | `10328` | `scripts/run_governed.py` | **受信启动边界，本轮重写为两个进程**：父进程 `-S -E -B` 按字节核验启动面并在不符时**拒绝启动子进程**；子进程 `-S -B` + 私有前缀 + 显式 site 目录 |
| `45373b43985f99747ce42f603fc09a0b3ab03f079645658b5a10bf6f680bb6f2` | `209` | `scripts/run_governed.cmd` | **新增**：让父进程本身在 `-S` 下启动的入口 |
| `2e850c8dd099a7b7c6dae87a14c4dfc23dbef240b489d7a27f73b8fc66ce3e61` | `6022` | `src/itsf/guards.py` | **R3**：`assert_trusted_launch` + 在单一真实运行门内以生产默认旗标为条件要求它 |
| `dcf34cc27cbc4295af6690a2dccf7c328b9573a4f9c16c7d7357520cd5d24fac` | `34487` | `src/itsf/mc/registry_boundary.py` | **F06**（`append_owner_hold` / `append_owner_release` 与 P3 共用 `_AppendLock` 与 compare-and-swap）；**本轮未改动** |
| `e7f6b65cf82fe7f0fcd97e9762f64d7f1df3b0ff5c7b1b9dda4bb6a28638eef9` | `13579` | `src/itsf/mc/owner_control.py` | **F05**（族系路由）；**本轮未改动** |
| `eb6e499e4348f2a43138aaf24fa33cedda035b01d445b39a1d3e39ad44c9a17d` | `8050` | `src/itsf/data/manifests.py` | **F03/F04**；**本轮未改动** |
| `474a5c83f90ab4f13f698fc118564bbace3f8153d2faf245c54edf583963d4fc` | `13439` | `src/itsf/mc/production_inputs.py` | **F03/F04**；**本轮未改动** |

### 0.2 真实运行入口(role = reference,方向 3)

| sha256 | bytes | 路径 | 为什么在集内 |
|---|---|---|---|
| `9ba7ad59ed012112e700aac59451ec729660ca3fa25a3d89a9bf5ef74784b166` | `67929` | `src/itsf/mc/supplement_runner.py` | `seam_recheck` 在生产侧唯一的调用点；并经 `assert_real_run_allowed` 以生产默认旗标受本轮的受信启动要求约束。**本轮未改动** |
| `f51d19a8e1768d4223a44145d79213d012a132d1933e9184662c786f7dd16ebc` | `161254` | `scripts/s0_real_run.py` | S0 真实运行入口。其 `g_real_run_allowed` 走 `guards.assert_real_run_allowed()`，所以本轮的要求覆盖它，且拒绝会成为一次**失败的 GateCheck**。**本轮未改动** |

### 0.3 结算回归与元守卫(role = reference)

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `ba78db2015fa18d361308031ebaf40896d8dbe90c6a02b27e1da022021e233ce` | `26730` | `tests/test_qros_cf_pre_cert.py` | **本轮结算测试，30 条**：启动顺序、R1/R2/R3 的原样复现与关闭、入口清单、F06 动态写入证明、F03/F04/F05 保全 |
| `3e678becc47bc37df7eb3132bd64bd41a9836f32580fd32aa7720cc3ac08a8e6` | `38785` | `tests/test_qros_cf_astra_round2.py` | 第二轮结算测试。`_Flags` 增补 `no_site`；**`-S` 的结论被倒转并写明理由** |
| `2e800045bf09eb3e40636efeca7491eae6d0e57ffb6a515ab3b47f7c4b6b0f37` | `28383` | `tests/test_qros_cf_astra_repairs.py` | 第一轮结算测试；本轮未改动 |
| `31bb95295ebf21f228fa62417b70d700a1fb451104dcdfd0e3bd137056b962f6` | `25270` | `tests/test_execution_identity.py` | T-F01；本轮未改动 |
| `bc1c1668aa0a44360d5807cf5bf329dd4684d6182d20c9d6b6be015045399180` | `27994` | `tests/test_n09_scaffold_criteria.py` | 元守卫：写者集合。本轮把「拒绝须点名阻断者」一条改为**先注入 launch 事实**，以便断言仍落在授权层 |
| `2466c2e92a219182aa1183546c3414272f1a64c84a0a4ee552db1c4196da813c` | `12968` | `tests/test_registry_path_single_construction.py` | 元守卫：路径构造登记 |
| `985569a7cbe92db4a6a81a1e47233efc0270d9dabbab9dd7312350d8886d38d3` | `9728` | `tests/test_every_identity_pattern_is_swept.py` | 元守卫；本轮未改动 |

### 0.4 因本轮而改动的既有测试 —— **请特别检查是否有测试被削弱**

本轮把八条断言了「授权层拒绝」的测试改为**先注入 launch 事实再断言**,
因为受信启动的拒绝现在更早到达。**这正是最容易偷偷削弱检查的地方**:
把匹配放宽到接受任何消息,等于删掉了检查而不是移动它。请逐条核对。

| sha256 | bytes | 路径 | 本轮改了什么 |
|---|---|---|---|
| `85aae1bcb6cd494a13e099452e3d49ecc5e9bfd3b1b5d5f08fe10fa3141d2c50` | `31800` | `tests/test_mc_consumer.py` | 两条改为注入 launch 事实；**新增一条直接断言外层拒绝** |
| `100a1b22a84c7da1bac7a372fda4d2784ecf82208dae4f78d733e2c6e61a1f83` | `36197` | `tests/test_mc_supplement_integration.py` | 一条改为注入 launch 事实 |
| `4ddba05a6e334af77b68c55f51db0f3f898f50ea2b0c7178b1f8119006a921d6` | `39363` | `tests/test_mc_supplement_runner.py` | 两条：门的旗标语义改为注入；生产入口的**首个拒绝已前移**并如实改写 |
| `6b0d2d88218b4bc241b630267e743476bc4bd1e4f9a4129cfc0d4b38a1561871` | `6276` | `tests/test_supplement_prepare_boundary.py` | 一条改为注入；**新增一条直接断言外层拒绝** |
| `6ab114630876d365f53b24c8f96dfcd693a96279e9d28ccbaa3051af3f8d8999` | `9389` | `tests/test_what_the_registry_append_unlocks.py` | 一条改为注入 launch 事实 |

### 0.5 权威定义、谱系与随包件(role = reference)

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `c55d8f5675243519bc102f6ac9181e8276b4f867dff1e77881710713928806f9` | `7754` | `ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md` | **F01–F06 的权威定义** |
| `8abdc702fe2e608717e97906053138a8f7f863f87da19a4826f9d51c3d600602` | `12245` | `ops/REVIEW_PACKET_QROS_CF_F01_F06_REREVIEW_2026-09-07.md` | 第 2 轮送审包（已 RETURNED）。谱系记录；其 §0 的 hash 是**当时**的字节 |
| `14e2d84defc6a77e408bba37806246d220e1bd2ee5af836a730843443d87d72a` | `5985` | `ops/REVIEWER_CONTRACT.md` | **T1–T6**、判决词表、证据类别、轮次预算 |
| `7a0fd26969f68e1a4ac2de6167b03ebbb6c83368e1f6998dec93422485ab187a` | `11381` | `ops/BACKLOG.md` | F07/F08 作为 B-22 / B-23 |
| `5c9af31df771eb9c36ff8100b881b5efd17f4e69a2e80e5a42e76cec1961540d` | `6084` | `ops/RECOVERY_ANCHOR.md` | **允许的 outcome-clean 定位入口** |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | `2563` | `ops/OUTCOME_CARRYING_ARTIFACTS.json` | **隔离登记册**（12 条） |
| `1cdd2dce3b33796e75f3dedfcac720704166f5d7a1bc93f2bde54a6f51de4c79` | `7424` | `ops/NEXT_HANDOFF.md` | **强制同行件**，禁读清单载体；本轮未改动 |

---

## 0.6 本次因入口/写者清单而新钉的源文件

Astra 在实质认证前停在传输环节:入口/写者清单需要这些源文件的字节,而它们
未被钉住。**这是一次传输停止,不是一条 finding。** 同一 `REVIEW_ID` 重发。

| sha256 | bytes | 路径 | 为什么被钉(它让哪个判断可决) |
|---|---|---|---|
| `66d746d83e76fcfc2145820e5262025bf27ad50538d671dbbbeca80600d393bd` | `4658` | `scripts/run_data_qa.py` | SANCTIONED_REAL_RUN_ENTRY (`__main__`) |
| `9d0e6134d814b869482a3ed8bffe77afa5119158ed4d4afa9146832dcda834d5` | `11135` | `scripts/qa_addendum_a1.py` | SANCTIONED_REAL_RUN_ENTRY (`__main__`) |
| `faf6ee467ffb18b04070b71719016587b1f0ddb00a77c901b144877e66aca12f` | `2428` | `scripts/qa_addendum_a2.py` | SANCTIONED_REAL_RUN_ENTRY (`__main__`) |
| `21512097b688bade80eb185d39ace0413dd7d2a1cbc7e54818afa1ce26e9f512` | `67832` | `scripts/s0_input_preflight.py` | SANCTIONED_REAL_RUN_ENTRY (`__main__`) |
| `e37bd5c2cd434568b16645f4a36970b2f2df5aeff02aaf8bee3e39cf7670b6d7` | `165998` | `src/itsf/mc/consumer.py` | SANCTIONED_REAL_RUN_ENTRY `run_real_mc` |
| `b07827067ed68033f1b21834f680546ef7f2c99629fb71c78deab62fdc76ea2a` | `4649` | `src/itsf/mc/real_input.py` | TWO SANCTIONED entries: `prepare_real_mc_input`, `prepare_supplement_mc_input` |
| `c34a9d13368eb4106d432c0b77ce25f7fd8e56f43642e5d1dee4f20e46c6d41a` | `6148` | `src/itsf/data/dbn_loader.py` | the flag-path seam: `load_real` calls the gate with the loader's OWN flags, so a temp-flag construction reaches real bytes without the launch proof. **This is the FLAG-PATH_BYPASS the reviewer must judge** |
| `f0035e1d5e2f3ca5b8c6189dcb6196970ddc79263cbf4dca008ff253a4d94d4b` | `11560` | `src/itsf/data/cost_calibration_loader.py` | same flag-path seam, three call sites |
| `817419cd5910fd352bf291c8c74d6e4723cc6afefcd1a1f5fe3cb1326bd88e34` | `10894` | `src/itsf/mc/mc_contract.py` | `RUN_ID_RE` — one of F05's two authoritative families |
| `e93a75e44c72d77d19abf72c7cd0d923d4b719ddd1e19e34f6924c19fbc0e24f` | `34389` | `src/itsf/mc/supplement_contract.py` | `SUPPLEMENT_ID_PATTERN` — F05's other family; sequence/row grammar |
| `ff4ba0f66aee5625e4ee1d53d915bfc3e78cf31c110dd0cf6bd85d579e2042b5` | `72459` | `src/itsf/mc/supplement_registry.py` | the shared row parser F05 routes through, and the GLOBAL sequence rule F06's derived sequence reuses |
| `499224b94113f47333fc2d2e8f2d3bcf6b24bc803a699d7419f51a716e1b3ede` | `13331` | `src/itsf/mc/registry_integrity.py` | calls `assert_no_owner_hold` with an MC-family id — why F05 routes BOTH families |
| `774cd76f927effa4560e699f4243269d833b34f09dbd8fff800044fe39d9b652` | `37130` | `src/itsf/mc/supplement_authority.py` | the authorization layer the relocated refusal assertions land on |
| `e0be5ae9771029d8c3e96a7d06f41808f15f28902d4e8739c33350df575bd8ee` | `78591` | `src/itsf/s0/runner.py` | **contains `append_registry_event_line`, a SUPPORTED_REGISTRY_WRITER that does NOT share the serialization primitive.** Load-bearing for F06 writer completeness |
| `888d639194578b8d22d93e4d61ab87d2cb8860d00759bfc1994f5b27c4f3b276` | `90687` | `src/itsf/s0/runinfra.py` | S0 run infrastructure; its writers were candidates under the writer rule and are classified NON-registry in the inventory |
| `97d50740d938cb40eccab6595e6ba7284c493e9a662e311ddce31700f294a002` | `64677` | `src/itsf/contracts.py` | `RunConfig` / `TrialState` / ruled roots the S0 entry constructs |
| `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `0` | `src/itsf/__init__.py` | **0 bytes, and that is the measured fact `BOOTSTRAP_IMPORT_CLOSURE` rests on**: importing `itsf.execution_identity` pulls in exactly two governed modules. F01's pre-import proof depends on it |
| `67a91c9ede5a8a53bceccafb39102cd5ce083cb2ca4cbf087aa56360bbe89c71` | `7231` | `tests/conftest.py` | test collection/fixtures Astra will execute |
| `d441aad613d6f1138a67d166434084f4d8792a2a23eb40091325fd33a102a136` | `5347` | `tests/tiers.py` | the tier map defining the A+B suite Astra will run |
| `27a4d763fc7c58b498a50d8b738d4846fdc5b8a4ce7d818e3167e2934e6c5db6` | `9312` | `src/itsf/mc/account.py` | **本席位追加(超出 19 件清单)**：SANCTIONED_ENTRY completeness. The stated discovery rule classifies `run_real_study` as a SANCTIONED_REAL_RUN_ENTRY (it calls the gate on the production defaults), and it is in NEITHER the 19-file list NOR the previous builder inventory. The reviewer cannot decide entry completeness without its bytes. |
| `272a804505b5ba51acc4ac62ca5c044a616213d770672f3330205352c8232088` | `24144` | `src/itsf/mc/orchestrator.py` | **本席位追加(超出 19 件清单)**：SANCTIONED_ENTRY completeness. Same rule, same omission: `run_real_lifecycle` calls the gate on the production defaults and was absent from both lists. |

**没有做整仓递归钉定。** 每一行都对应下面清单里一个具体判断;
被 Python 顺带 import 的模块、标准库与第三方包内部**不因为被 import 就成为受审件**。

---

## 4.5 SUPPORTED_ENTRY_WRITER_INVENTORY —— 在冻结 HEAD 上机械导出

**导出方式,可复核。** 工作树在 `3bc415e41ec606ee5b47d331f30a5a57af0c9328` 处干净,故对工作树做 AST 即等于对
冻结 HEAD 做 AST。两条规则,逐条施加,不抄任何先前的 builder 报告:

```
规则 E（候选真实运行入口）
  scripts/ 下带 `if __name__ == "__main__"` 的文件,
  或 src/itsf/ 下调用 assert_real_run_allowed 的函数。
  当它以**生产默认旗标**到达该门时(无参调用、传 G9_FLAG/SECOND_COPY_FLAG、
  或构造未覆盖旗标的 DevelopmentSignalLoader)即 SANCTIONED_REAL_RUN_ENTRY,
  因为那正是 assert_trusted_launch 触发的那个调用。

规则 W（候选 registry 写者）
  src/ 或 scripts/ 下函数体含写调用(write_bytes/write_text/write/writelines)
  或以追加模式 open,且满足其一:
    (a) 位于拥有受管 registry 路径的模块;
    (b) 文本中出现 TRIAL_REGISTRY.md;
    (c) 调用共享原语 _compare_and_append;
    (d) 函数名或参数名含 "registry"。
  条 (d) 是**本轮补上的**:第一版规则只按路径字面量匹配,因而漏掉了一个把
  registry 路径当**参数**接收的真实写者——见下表 `append_registry_event_line`。
```

**允许你自己重跑这两条规则。** 对 `src/` 与 `scripts/` 做 AST 扫描是被明确许可的:
它只读项目源码,**不触及 `ops/`**,因此不可能命中任何隔离件。不要把扫描扩到 `ops/`。

### 4.5.1 真实运行入口

| 路径 | 入口符号 | 分类 | 发现依据 | 受信启动 | 共享序列化 | 该文件 sha256 |
|---|---|---|---|---|---|---|
| `scripts/s0_real_run.py` | `__main__` | **SANCTIONED_REAL_RUN_ENTRY** | scripts/ + `__main__`; gate on production defaults | YES | n/a | `f51d19a8e1768d4223a44145d79213d012a132d1933e9184662c786f7dd16ebc` |
| `scripts/run_data_qa.py` | `__main__` | **SANCTIONED_REAL_RUN_ENTRY** | scripts/ + `__main__`; gate on production defaults | YES | n/a | `66d746d83e76fcfc2145820e5262025bf27ad50538d671dbbbeca80600d393bd` |
| `scripts/qa_addendum_a1.py` | `__main__` | **SANCTIONED_REAL_RUN_ENTRY** | scripts/ + `__main__`; gate on defaults + default-flag loader | YES | n/a | `9d0e6134d814b869482a3ed8bffe77afa5119158ed4d4afa9146832dcda834d5` |
| `scripts/qa_addendum_a2.py` | `__main__` | **SANCTIONED_REAL_RUN_ENTRY** | scripts/ + `__main__`; gate on production defaults | YES | n/a | `faf6ee467ffb18b04070b71719016587b1f0ddb00a77c901b144877e66aca12f` |
| `scripts/s0_input_preflight.py` | `__main__` | **SANCTIONED_REAL_RUN_ENTRY** | scripts/ + `__main__`; default-flag `DevelopmentSignalLoader` | YES (through the loader) | n/a | `21512097b688bade80eb185d39ace0413dd7d2a1cbc7e54818afa1ce26e9f512` |
| `src/itsf/mc/consumer.py` | `run_real_mc` | **SANCTIONED_REAL_RUN_ENTRY** | src/ function; gate with `G9_FLAG, SECOND_COPY_FLAG` | YES | n/a | `e37bd5c2cd434568b16645f4a36970b2f2df5aeff02aaf8bee3e39cf7670b6d7` |
| `src/itsf/mc/real_input.py` | `prepare_real_mc_input` | **SANCTIONED_REAL_RUN_ENTRY** | src/ function; gate on defaults | YES | n/a | `b07827067ed68033f1b21834f680546ef7f2c99629fb71c78deab62fdc76ea2a` |
| `src/itsf/mc/real_input.py` | `prepare_supplement_mc_input` | **SANCTIONED_REAL_RUN_ENTRY** | src/ function; gate on defaults | YES | n/a | `b07827067ed68033f1b21834f680546ef7f2c99629fb71c78deab62fdc76ea2a` |
| `src/itsf/mc/supplement_runner.py` | `run_supplement_production` | **SANCTIONED_REAL_RUN_ENTRY** | src/ function; gate on defaults; also the sole `seam_recheck` caller | YES (gate + seam) | via `append_run_started` | `9ba7ad59ed012112e700aac59451ec729660ca3fa25a3d89a9bf5ef74784b166` |
| `src/itsf/mc/account.py` | `run_real_study` | **SANCTIONED_REAL_RUN_ENTRY** | src/ function; gate on defaults. **ABSENT from the 19-file list and from the previous builder inventory** | YES | n/a | `27a4d763fc7c58b498a50d8b738d4846fdc5b8a4ce7d818e3167e2934e6c5db6` |
| `src/itsf/mc/orchestrator.py` | `run_real_lifecycle` | **SANCTIONED_REAL_RUN_ENTRY** | src/ function; gate on defaults. **ABSENT from both lists** | YES | n/a | `272a804505b5ba51acc4ac62ca5c044a616213d770672f3330205352c8232088` |
| `scripts/run_governed.py` | `main / run_parent / run_child` | **INTERNAL_ONLY** | scripts/ + `__main__`; performs no run — it IS the boundary | IT IS THE MECHANISM | n/a | `f51f166ad4fc18db8a8cd12201dcfd3adf1e86e670bf2a6ec490a8f21437714b` |
| `src/itsf/data/dbn_loader.py` | `load_real` | **INTERNAL_ONLY** | src/ function calling the gate with the LOADER'S OWN flags, not the production defaults | NO — flag-path seam, see §4.5 | n/a | `c34a9d13368eb4106d432c0b77ce25f7fd8e56f43642e5d1dee4f20e46c6d41a` |
| `src/itsf/data/cost_calibration_loader.py` | `build_spread_table_real, _qa_crossed_forensics, _qa_ts_phase_census` | **INTERNAL_ONLY** | same flag-path seam, three sites | NO — flag-path seam, see §4.5 | n/a | `f0035e1d5e2f3ca5b8c6189dcb6196970ddc79263cbf4dca008ff253a4d94d4b` |
| `scripts/render_qa_addendum.py` | `__main__` | **NON_REAL** | `__main__`; no gate on defaults, no loader — its real-data names are docstrings | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `scripts/mc_ds_rehearsal.py` | `__main__` | **NON_REAL** | `__main__`; no gate, no loader | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `scripts/archive_code_6_block_builder.py` | `__main__` | **NON_REAL** | `__main__`; no gate, no loader | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `scripts/build_verifier_dir.py` | `__main__` | **NON_REAL** | `__main__`; no gate, no loader | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `scripts/fetch_symbology_d5.py` | `__main__` | **NON_REAL** | `__main__`; no gate, no loader | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `scripts/final_candidate_scans.py` | `__main__` | **NON_REAL** | `__main__`; no gate, no loader | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `scripts/mc_cost_probe.py` | `__main__` | **NON_REAL** | `__main__`; no gate, no loader | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `scripts/physical_copy_verify.py` | `__main__` | **NON_REAL** | `__main__`; no gate, no loader | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |

### 4.5.2 registry 写者

| 路径 | 符号 | 分类 | 发现依据 | 受信启动 | 共享序列化 | 该文件 sha256 |
|---|---|---|---|---|---|---|
| `src/itsf/mc/registry_boundary.py` | `_compare_and_append` | **SUPPORTED_REGISTRY_WRITER** | owns the governed path; the ONE physical `write_bytes` | n/a (called after the seam) | **IT IS THE PRIMITIVE** — lock + CAS | `dcf34cc27cbc4295af6690a2dccf7c328b9573a4f9c16c7d7357520cd5d24fac` |
| `src/itsf/mc/registry_boundary.py` | `append_run_started` | **SUPPORTED_REGISTRY_WRITER** | exported appender in `__all__` | YES — `seam_recheck` requires the attestation | YES | `dcf34cc27cbc4295af6690a2dccf7c328b9573a4f9c16c7d7357520cd5d24fac` |
| `src/itsf/mc/registry_boundary.py` | `append_owner_hold` | **SUPPORTED_REGISTRY_WRITER** | exported appender in `__all__` | NO — owner control is Aaron's path and is not gated on a governed launch | YES | `dcf34cc27cbc4295af6690a2dccf7c328b9573a4f9c16c7d7357520cd5d24fac` |
| `src/itsf/mc/registry_boundary.py` | `append_owner_release` | **SUPPORTED_REGISTRY_WRITER** | exported appender in `__all__` | NO — same reason | YES | `dcf34cc27cbc4295af6690a2dccf7c328b9573a4f9c16c7d7357520cd5d24fac` |
| `src/itsf/s0/runner.py` | `append_registry_event_line` | **SUPPORTED_REGISTRY_WRITER** | **opens the path in APPEND MODE and writes a row; the path arrives as a PARAMETER**, so a rule keyed on the path literal misses it. Called at `scripts/s0_real_run.py:3174` with that script's `REGISTRY` constant | YES, indirectly — its only caller is a SANCTIONED entry whose gate now requires the attestation | **NO — plain `open('a')` + `write`, no lock, no compare-and-swap** | `e0be5ae9771029d8c3e96a7d06f41808f15f28902d4e8739c33350df575bd8ee` |
| `src/itsf/s0/registry_witness.py` | `append_witness` | **NON_REAL** | append mode, but `witness_path` — writes WITNESS files, not the registry | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |
| `src/itsf/s0/runinfra.py` | `append_manifest_record, write_failure_report, archive_sealed_run, validate_output_roots_operational` | **NON_REAL** | write calls in a module that mentions the registry path in prose; every target is a run-directory artifact | n/a | n/a | `888d639194578b8d22d93e4d61ab87d2cb8860d00759bfc1994f5b27c4f3b276` |
| `src/itsf/mc/supplement_runner.py` | `resolve_partial` | **NON_REAL** | writes `out_dir / filename`, a run output | n/a | n/a | `9ba7ad59ed012112e700aac59451ec729660ca3fa25a3d89a9bf5ef74784b166` |
| `src/itsf/mc/day_strata_supplement.py` | `seal_supplement_test_only` | **NON_REAL** | writes the sealed supplement artifact in `out_dir` | n/a | n/a | 未钉(该分类按 §4.5 的规则可自行复核) |

### 4.5.3 这份清单查出的两件事 —— **请当作待验证的声明**

**① 两个 SANCTIONED 入口在两份清单里都缺失。** `mc/account.py::run_real_study`
与 `mc/orchestrator.py::run_real_lifecycle` 都以生产默认旗标调用那道门,
既不在 19 件清单里,也不在本席位上一版的入口清单里。两者已在 §0.6 补钉。
上一版的入口清单只枚举了 `scripts/*.py` 的 `__main__` 加三个模块入口——
**那是一份不完整的清单,而我当时称它「机械枚举」**。

**② 有一个受支持的 registry 写者不共享序列化原语。**
`s0/runner.py::append_registry_event_line` 以 `open('a')` 直接追加,没有锁、
没有 compare-and-swap,其唯一调用点 `scripts/s0_real_run.py:3174` 传入的正是
受管 registry。本席位上一版把 F06 表述为「三个受支持写者共享同一原语」——
**那句话对 `registry_boundary` 的三个 appender 成立,对「每个受支持的 registry
写者」不成立**,这与第 2 轮「机制化强制」那次是同一形态。

**本轮是 transport-only,故两者都没有被修。** ① 只是补钉字节;② 是一条
**尚未修复的事实**,交给你判断它是否构成 BLOCKING、以及归 T5 还是别处。
不要因为我先说出来就替我打折。

---

## 1. 禁读清单与入口(必须随每个交付载体同行)

- **隔离登记册**:`ops/OUTCOME_CARRYING_ARTIFACTS.json`。其上列出的任何路径都不得读取。
- **不得漫游仓库**:检索限于 §0 表内路径及其直接依赖。
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

这些文件携带 S0-T001 的**结果**。本轮只关心执行安全与数据身份,不需要任何结果数字。
**其中 `MC_TO_STRATEGY_MASTER_PLAN.md` 既 outcome-carrying、又曾是项目的「恢复锚点」**
——一个正常定位状态的审阅者会正面撞上去,2026-08-25 已有一个 fresh 席位这样被烧掉。
用 `RECOVERY_ANCHOR.md` 定位。

seat 轴台账 `ops/REVIEWER_EXPOSURE_LOG.md` 存在但**不在受审集内、也不必核对**;
本轮那一行在你归还之后才追加。研究轴台账禁读(已在上表)。

---

## 2. 范围

```
F01  bytecode / source execution        T1   待认证
F02  startup / import hook              T1   待认证
F03  authorized manifest authority      T3   待认证（本轮未改动其字节）
F04  verify-consume same bytes          T3   **CLOSED —— 你在第 2 轮关闭,本轮不重开**
F05  malformed owner-control fail-open  T5   待认证（本轮未改动其字节）
F06  owner-hold / P3 serialization race T5   待认证（本轮未改动其字节,只加证明）
```

**F04 保持 CLOSED**;若本轮改动使其失效,那本身是一条 finding
（`tests/test_qros_cf_pre_cert.py` 重新驱动了它的对抗性用例）。

**F07 / F08 在范围之外**,已作为 **B-22 / B-23** 记入 `ops/BACKLOG.md`;
两者都不能产生未授权的 STARTED,**不得以它们阻挡本轮退出**。

不在范围、且不得在本轮重开的:架构、N10/N11/N13、任何真实运行、
研究结论/样本/成本/Primary 指标/promotion-falsified。

### 2.1 轮次 —— 本轮在合同预算之外,且**未被重置**

```
第 1 轮  P2 门禁复审          -> HOLD,六条 BLOCKING(F01–F06)
第 2 轮  定向复审(第一轮修复) -> HOLD,F04 CLOSED,五条 STILL_BLOCKING
         ↓ 第二轮修复 0d15a62
         ↓ 打包最终认证 -> 本席位自测出三条残留 -> Aaron 授权 PRE-CERT 修复 81c0d22
         ↓ **这一步没有派发任何席位,因此不是一轮**
第 3 轮  本次               -> 预算已用尽,**Aaron 明确授权的一次业主例外**
```

写在这里是因为:**你完全有理由在自己发现合同被突破时 STOP**,而让你自己去发现
则是本席位的失职。**这是本谱系的最后一轮。**

### 2.2 基准怀疑度

本席位在这条谱系上已经错了三次,而且是同一形态——**声称宽于事实**:

```
第 1 轮修复  五条修复各自通过了我写的结算测试,你仍在其中五条上复现了反例
第 2 轮修复  我写「机制化强制」,而它对 P3 seam 成立、对每个真实运行入口不成立
第 2 轮测量  我写「-S 不能用」,而真相是「-S 单用不能,-S 加显式 site 目录可以」
```

第三条尤其值得你注意:**它是一条被我写进测试、钉成结论的错误测量**,
本轮已倒转并写明理由。请假设同类错误还在。

---

## 3. 本轮修复的机制 —— 待验证的声明

### 3.1 R1 + R2：一个时序漏洞,改为「阻止」而非「事后检查」

`.pth` 的 `import` 行在 site 初始化时执行,**早于项目任何一行代码**。
所以「先执行、后校验」在原理上不足;而 R2 证明了事后的 `sys.modules` 普查
可以被「导入 → 变造 → 删除子模块条目」清扫干净——留下的正好是被允许的 closure。

**关闭方式是 `-S`**:在它之下没有任何 `.pth` 行被执行,`site` 从未被导入,
`sitecustomize` / `usercustomize` 也从未被导入。没有钩子可以运行,
也就没有东西需要被普查发现。`assert_governed_launch` 现在要求只读的
`sys.flags.no_site`,且**该拒绝被排在 `sys.modules` 普查之前**
（测试断言了这个顺序:带钩子的进程不得被它能击败的检查来评判）。

### 3.2 R3：单一真实运行门

`assert_real_run_allowed` 本来就是唯一的真实运行门,被八个生产入口以
**生产默认旗标**调用。要求放在那里,一处覆盖全部,并覆盖将来没人记得接线的新入口。
条件（两个生产 attestation 路径）与**它不覆盖什么**都写在 docstring 里:
一个传入临时旗标却指向真实 job 目录的调用者仍会读到真实字节——那是旗标参数
既有的测试接缝,早于本轮,本轮既未扩大也未关闭它。

### 3.3 F06：只补证明,不加 git 提交要求

三个受支持的写者被**真实驱动**并计数,证明它们都经由同一个序列化原语到达
那一次物理写入;另有一条守卫断言没有 git 提交被引入追加路径。

---

## 4. 四个方向 —— 本版的答案与证据

**每条都是本席位自己的测量,证据类别 SELF-REPORTED,请独立复核。**

### 方向 1 —— 可执行 `.pth` 的内容是否在它**执行之前**被约束? **是**

两层,顺序重要:

```
父进程（-S -E -B,只用 stdlib）
  按字节核验每个可执行启动面 -> 不符即 REFUSING TO LAUNCH,子进程根本不启动
子进程（-S -B,私有前缀,显式 site 目录）
  -S 之下没有任何 .pth 被执行 —— 不是「检查过了」,是「没有运行过」
```

请特别检视:父进程自己也在 `-S` 下,所以它自身启动时也没有 `.pth` 执行。
**未声称的部分**:任何链条最外层的那个进程,在它能运行一行代码时,自己的
解释器启动已经完成。本边界给出的是「运行受管语义的那个进程里没有启动面执行」,
不是全机哈希。

### 方向 2 —— 启动钩子能否在 attestation 之前碰受管模块并隐藏? **不能**

原攻击仍在测试里**原样复现**（导入 → 变造 `OWNER_ACTOR` → 删除 `itsf.mc.*`
→ 只剩 closure）,以证明**普查确实可被击败**——这正是不再依赖普查的理由。
在 `-S` 之下没有钩子可以运行,故该攻击无法转化为一次有效的受管启动。

### 方向 3 —— 每个受认可的真实运行入口都被约束? **是**

`tests/test_qros_cf_pre_cert.py` 里有一份**机械枚举的入口清单**
（`scripts/*.py` 全部带 `__main__` 者,逐个分类),新脚本未分类即红。
五个 SANCTIONED 入口全部绑定到那一个门;其中三个以直接执行验证了**失败关闭**。

`scripts/s0_real_run.py` **故意不在测试里直接执行**:执行一个真实运行入口
正是被阻止的那件事本身。它的绑定以静态方式证明,门的行为以动态方式证明。

### 方向 4 —— 共享序列化原语直到物理写入? **是（到物理写入）**

三个写者被真实驱动并计数为 3;物理写入与相等性再读都在锁内。
**registry 在另一个仓,追加路径里没有 git 提交,本轮也没有加**——按 Aaron 的指示,
不变量是顺序与落盘字节。若你认为提交顺序也须由同一原语覆盖,那是一条应当提出的
finding,而不是本轮偷偷加进去的要求。

---

## 5. 请你做的事

1. 逐行重算 §0 的 sha256;不符即 STOP 并报告。
2. 以 §0.5 的转录件为 F01–F06 的定义,**独立复现每条原始反例**。
3. **逐条核对 §0.4**:八条被改动的既有测试,是否有任何一条被削弱。
4. **§4 四条逐条明确作答**,并说明你的答案是 REPRODUCED 还是 REASONED。
5. 用 `ops/REVIEWER_CONTRACT.md` 的词表给出判决:`PASS` / `PASS_WITH_BACKLOG` /
   `HOLD`。每条 BLOCKING 须点名恰好一个威胁(T1–T6)、一条具体失败路径、
   及其证据类别(REPRODUCED / REASONED / SELF-REPORTED)。
6. 区分**你复现的事实**与**本席位自报的测量**。

不要修改任何文件。不要执行 `qros`。不要追加任何 registry 事件。不要写入仓库。

---

## 6. 本包不做的事

不接受、不裁定、不关闭任何 finding。F01/F02/F03/F05/F06 在一个新的独立席位
另有结论之前保持 BLOCKING,而那个结论由 Aaron 派发与记录——不由写了这份修复的
席位给出。
