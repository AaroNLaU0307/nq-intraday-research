# CODEX_REVIEW_PACKET_M6_1_6（生命周期接缝 ＋ 治理输出证明，供 Codex 独立复审）

- **baseline（父 commit）**：`1e188b54ace011bb4c2ab7356f775af6d32aab37`（M6.1.3，Codex 判 HOLD）
- **本审查对象**：`UNCOMMITTED_WORKTREE_SNAPSHOT`（**未提交**的工作树：
  `git status --porcelain` 共 **21** 条，父 commit 即上述 baseline）。HOLD 期间
  **不使用** `THIS_COMMIT`／「本 commit」字样——没有 commit 可指。
- **本轮闭合的是两个**具名接缝，**不是** F-1／F-2 中的任何一个整体（§2 逐条分述）。
- **授权状态（registry 词汇原文）**：`REAL_S0_NOT_AUTHORIZED`。
  `REAL_RUN_READY=NO`、`STRATEGY_COUNCIL=LOCKED`（不变）。
  不追加 READY、不申请授权、不建 tag、**不追加任何 registry 事件**、
  **不新铸任何研究 DR 编号**。

---

## 0. 验收门实测

**证据级别声明（逐行标注，不设跨行统一标准）**：

| 标注 | 含义 |
|---|---|
| `FABLE/OPUS_REPORTED` | 本工程会话（主代理＋工程车道）本机实测 |
| `S3_RERUN` | 本文件作者（只读治理车道 S3）于 2026-08-09 在同一未提交工作树字节上**自行复跑**，非转录 |
| `CODEX_NOT_RERUN` | Codex 未独立复跑；复审时应视为待验证的自报数据 |

| 门 | 结果 | 标注 |
|---|---|---|
| `pytest -q -rs` | **2146 passed / 0 failed / 0 skipped**（S3 复跑同值，400.21s，exit 0） | `FABLE/OPUS_REPORTED; S3_RERUN; CODEX_NOT_RERUN` |
| collected == `MIN_COLLECTED_TESTS` | 2146 == 2146；**双钉**：`scripts/s0_real_run.py:47`（`MIN_COLLECTED_TESTS = 2146`）与 `tests/test_s0_runner.py:867`（`assert mod.MIN_COLLECTED_TESTS == 2146`） | `S3_RERUN`（逐文件核对） |
| `guards.verify_frozen_hashes()` | `FROZEN=OK`，`FROZEN_HASHES` 共 **7** 项 | `S3_RERUN` |
| `scripts/final_candidate_scans.py` | `SCANS=CLEAN`，exit 0 | `S3_RERUN` |
| `git diff --check` | 净（exit 0） | `S3_RERUN` |
| `ops/TRIAL_REGISTRY.md` sha256 | `de63b3d690c5c4be1def67aff9e0302138e9910df5b9a89acb1db57697b0b440`（＝基线，未修改） | `S3_RERUN` |
| `EXPOSURE_LEDGER.md` sha256 | `394813431d879555b7504d2501c40123368d67a517359e056692eb6b0f6bc9e6`（＝基线，未修改） | `S3_RERUN` |
| `runs/` | 不存在 | `S3_RERUN` |
| 工作树条目数 | **21 → 22** —— 工程车道收口时为 **21** 条；S3 治理车道**新增本文件一个 untracked 条目**后为 **22** 条（`git status --porcelain` 计数，S3 实测）。**已改动文件集合不变**：11 modified（4 源 ＋ 4 测试 ＋ 2 治理文档 ＋ 1 脚本）＋ 11 untracked | `S3_RERUN` |
| 真实数据 | 零读取；未运行真实 S0；S0-T001 未消耗 | `FABLE/OPUS_REPORTED` |

**「0 skipped」的性质（与前序 packet 同，不得升格）**：那是**本环境本次运行的
观测值**，不是结构保证——`tests/test_preflight.py` 内仍有条件性 `pytest.skip`，
preflight 工件缺失时会触发。

**生产源哈希（sha256 前 16 位，本轮工作树实测，`S3_RERUN`）**：

```
scripts/s0_real_run.py    937c96bf6b15d26b        # 本轮改动
src/itsf/s0/runner.py     0c1e5cbb9861f8da        # 本轮改动
src/itsf/s0/output_proof.py 1f045ed5fb75480a      # 本轮新增（未入授权包环境锁，见 §7）
src/itsf/contracts.py     d72a9b05dbf481a4
src/itsf/s0/report.py     52d050bb6f1095e9
src/itsf/s0/handoff.py    a1f2c0a1ac77f96d
src/itsf/s0/evidence.py   676fbcd1ae0ac2a9
```

---

## 1. 本轮闭合的两个接缝（**只此两条**）

### 1.1 prepared **LIFECYCLE 接缝** —— CLOSED

生命周期新序（`src/itsf/s0/runner.py:37-40`，实施在 `:434-523`）：

```
Stage B（结构校验，pre-exposure）
  -> prepare_compute()                 （新增；仍在 pre-exposure）
  -> 最终 pre-exposure registry 复查    （_atomic_run_start 内）
  -> RUN_STARTED                        （exposure 在此消耗）
  -> compute(prepared)                  （Stage C）
```

**fail-closed 两侧均已接线（源码核实）**：

- `prepare_compute` **未接线**（`d.prepare_compute is None`，`runner.py:473-478`）
  → Stage B `prepare_compute` 门失败，**不**默默跳过。措辞照搬其自身先例：
  「mirrors the pre-exposure registry recheck at `_atomic_run_start`」。
- prepare 返回**任何 falsy 值**（`if not prepared`，`runner.py:485-492`）→ 同样失败。
  该行注释点名 `M6.1.6 review A1-1`，即它是本轮复核意见的落地（见 §3）。

**它修的是什么（对旧字节实测，不是转述）**：baseline `1e188b5` 的
`scripts/s0_real_run.py` 中，`ready()`（:1379）调用 `resolved_study_config()`
（:1388）后**只返回 bool＋字符串、丢弃 cfg**；`compute()`（:1463）在
RUN_STARTED **之后**再次调用 `resolved_study_config()`（:1466）。因此一次
config 拒绝会**烧掉 trial**（exposure 已消耗）。新序把解析前移到 exposure 之前，
Stage C 只消费被交付的 prepared 对象（`s0_real_run.py:2411-2415` 另有 AST 测试
钉住「Stage C 以下不得再触碰任何 config 源」）。

### 1.2 治理 **OUTPUT-PROOF 切片**（`governance.*` **仅此五键**）—— CLOSED

`src/itsf/s0/output_proof.py`，单一公开可调用 `prove_governance`。

- **跑在最后**，对**最终 `S0_REPORT.json`**（`FINAL_REPORT_NAME` 硬编码，
  不是参数，故无法被指向 evidence 镜像或注入前草稿；工件图内无该键即
  `ProofRefused`，绝不当作通过）。
  **精确限定（S3 逐行核实，务必与 §4 合读）**：`prove_governance` 有两种
  取证方式（`output_proof.py:487-550`），**生产走的是前者**——
  `sealed_artifacts=files`（`s0_real_run.py:1092-1093`）取
  `sealed_artifacts["S0_REPORT.json"]` 这个**内存字符串**（`:529`）；
  另一条 `report_path=` 分支才走 `Path.read_bytes()`（`:546`）。
  **因此本切片证明的是「渲染器打算封存的内容」，而不是「磁盘上最终躺着
  的字节」**——那正是 §4 的裂缝所在的一侧。
- **expected 侧来自 pre-run 的独立 context**（`SourceContext`：pre-run
  authorization snapshot ＋ `guards.FROZEN_HASHES` 权威 ＋ 其独立的磁盘观测
  ＋ 已批准的 engineering-seed 出处戳记），**从不读取 report／formal／evidence 镜像**。
- **比较次数是派生的，不是硬码**：`comparisons_performed` 由比较循环自增，
  `ok` 要求 `problems == ()` **且** `comparisons_performed == comparisons_required`，
  后者由遍历 expected 树得出。跳过的比较不能通过。
- expected 键域为 `CONTRACT_GOVERNANCE_KEYS`（内容契约的字面转写）＋
  `sorted(context.frozen_hash_authority)`，**不由被守护对象定尺寸**——这是
  `evidence.py:2052-2054` 那类「域塌缩」的显式反向设计。

**范围限定（必须与 §1.1 分开读）**：本切片证明的是 `governance.*` 五键，
**不是**报告整体，**不是** F-1，**不是** F-2。

---

## 2. 本轮**未**闭合的（分辨率必须保持，不得合并陈述）

> 下列四条是**四个不同的对象**。把其中任意两条写成同一件事，就是本项目
> 已两度付出代价的那类过度声明。

| 对象 | 本轮状态 | 依据 |
|---|---|---|
| prepared **LIFECYCLE 接缝** | **CLOSED** | §1.1 |
| 治理 **OUTPUT-PROOF 切片**（`governance.*` 仅） | **CLOSED** | §1.2 |
| **F-1 整体** | **PARTIAL** | 见下 |
| **F-2 整体** | **PARTIAL**，本轮**无变化** | 见下 |

### 2.1 F-1 整体 —— PARTIAL（原因具名，源码核实）

prepared 对象 `_PreparedExecutionInput`（`scripts/s0_real_run.py:2210-2250`）
**不是**完全物化的执行计划：

1. `config.regime_of` / `config.vol_axis_of` **仍是 CALLABLES**
   （`src/itsf/contracts.py:449-450`，注释即 `Callable[[date_str], str]`）。
   行为不可快照——`__closure__` cells／`__code__`／`__globals__` 均可重绑。
   **物化这两个 callable 需要 DR-2 的已裁词表**，其中 `vol_na` 第四层的
   处理**明确未裁**（`DECISION_REQUIRED_M6_1.md:93-98`：vol_na 独立层、不入
   任何三分位、不删日；`B0_SOURCE_LINEAGE_MATRIX.md` L078/L079 同标 DR-2）。
2. `methods.spread_cost.adverse_slippage_ticks` **仍是 `MappingProxyType`**，
   即其作者可能仍持有后备 dict 的**活视图**。**冻结 tick 取值需要一条本
   里程碑不得作出的裁决**（与 E-6 同一面：int-vs-float 与 `-0.0` 的 tick
   **值**分歧，今日到不了任何封存字节，但也没有被冻结）。

**因此**：`prepare_compute` 关闭的是**生命周期**的洞，**不是** F-1 架构要求的
「完全物化的执行计划」。F-1 整体维持 `PARTIAL + ENGINEERING_REQUIRED`。

### 2.2 F-2 整体 —— PARTIAL，本轮**无变化**

本轮**没有**触碰叶／token 证据系统。`output_proof.py` 的模块文档明写
「deliberately does NOT extend (or read) the leaf/token evidence system」。

**该主张有字节证据，不是自陈**（S3 复算）：

- `src/itsf/s0/evidence.py` 现值 `676fbcd1ae0ac2a9`，与 M6.1.4-R2 收口值
  **逐位相同**（见 `CODEX_REVIEW_PACKET_M6_1_4.md` §0 的生产源哈希行）；
- `tests/test_s0_evidence.py` 仍为 **324 passed / 0 failed / 0 skipped**，
  与 R2 轮同值（§10.3「电池 —— PASS」）；
- `src/itsf/s0/dataset.py` 与 `src/itsf/s0/context.py` **根本不在本工作树的
  改动集内**（`git status --porcelain` 无此二行），即 EV-11 与 preflight
  比对两侧的语义**与 baseline `1e188b5` 逐字节相同**。

**分类变更（本轮唯一的 F-2 相关动作，属文档层）**：叶／token 证据系统
**重新归类为 LEGACY DIAGNOSTIC**，**不是** release certificate。
理由是 M6.1.4-R2 复核员 R2 的实测（`CODEX_REVIEW_PACKET_M6_1_4.md` §10.1-10.4）：
在诚实基线 `hard=0` / 121/121 叶 complete / 8,178 token 全等的情况下，
F1／B1／B2／B3 四类篡改产出**逐字节相同**的封存输出。一个在四类篡改下
不变的信号，可以作为诊断，**不能**作为发布凭证。该重分类**不缩小**
F-2 的未闭合面，也不替代 §10.5 的六条闭合要求。

### 2.3 EV-11 —— 本轮**语义未触碰**

`dataset.py` 的标签依赖语义、EV-11 的两条专属 PARTIAL、以及
`M6.1.4 packet` 的 **D-4**（EV-11 五布尔→标签集 reducer 的冻结）
本轮**一律未改动**。**故 M6.1.6 不产生任何新的 Aaron 裁决请求。**
D-4 仍挂在既有 DR 伞下，队列长度不变（见 `DECISION_REQUIRED_READY_SUPERSESSION.md` §5）。

---

## 3. 独立复核（本轮）

| 项 | 值 |
|---|---|
| 判定 | **`M6_1_6_REVIEW=PASS`** |
| 轴数 | 4 |
| 发现 | **6 Low**；**0 High／0 Medium** |
| **轴 4（research boundary）** | **零发现** |

**在唯一允许的修复轮内落地的两条 Low（源码核实其在场）**：

1. 敌意 Mapping 的 `SourceContext` 校验 —— `src/itsf/s0/output_proof.py:209-227`，
   注释 `M6.1.6 review A3-1`。修法是**先物化再校验被物化的副本**
   （`snap = dict(snap_in)`，其后每一次读取都读该副本），
   以杜绝「`.get()` 与 `__getitem__` 不一致的 Mapping 通过校验、随后交出
   **不同**取值作为 expectation」这一「validate X, use Y」类。
2. falsy prepared 对象 —— `src/itsf/s0/runner.py:485-492`，注释
   `M6.1.6 review A1-1`：**任何** falsy 返回都是拒绝，不只是 `None`。

**其余 4 条 Low 记为设计注记，本轮不改。**

> **必须原样保留的限定**：**上述两条修复没有被独立复核员重新复核。**
> 复核员在其判定之后未再开跑；本 packet 对这两条的全部证据是
> `FABLE/OPUS_REPORTED` ＋ 本车道的源码在场核实。按本项目
> 「修复轮自判闭合不构成闭合」的既定规则，它们**不计入**任何 CLOSED 主张。

---

## 4. DEFERRED —— 已核实、**本轮未修**：CRLF 转译造成同一工件两个摘要

**严重度按原样记录，不软化。**

**机制（本车道在本机独立复算，不是转述）**：

- `src/itsf/s0/runner.py:558` 写工件：`path.write_text(content, encoding="utf-8")`
  ——**没有** `newline=""`。Windows 上 `\n` 被转译为 `\r\n`。
- 紧接着 `:559` `written.append((name, path.read_bytes()))` ——进入 runner
  自有哈希链的是**磁盘字节**。
- 而 `scripts/s0_real_run.py:1050-1057` 写进 `S0_REPORT.json` 的
  `mc_handoff_manifest.sealed_files[<name>].sha256`，是
  `hashlib.sha256(body.encode("utf-8"))` ——**内存字节**（LF）。

**本机实测（`S3_RERUN`）**：`write_text('a\nb\nc', encoding='utf-8')` 后
磁盘为 `b'a\r\nb\r\nc'`，摘要与内存摘要不等；无换行的正文则相等。

**规模（复核员测得 9/10；本车道由构造独立复现同一数字）**：
`sealed_files` 共 **10** 项（`S0_REPORT.json` 自排除，全集 11）：

| 工件 | 序列化 | 含 `\n`？ | 摘要是否匹配磁盘 |
|---|---|---|---|
| `MC_HANDOFF_<E1\|E2>_<Base\|Conservative\|Stress\|Severe>.jsonl`（**8** 项＝2 引擎×4 情景） | JSONL，逐行 | 是 | **否** |
| `S0_REPORT.md` | `"\n".join([...])` | 是 | **否** |
| `HANDOFF_ADMISSION.json` | `handoff.dumps_canonical` ＝ `json.dumps(..., sort_keys=True)`，**无 indent**，单行 | 否 | 是 |

→ **9 / 10 不匹配**。

**为什么这是治理级而非风格级问题**：**一个工件、一个封存输出内部、两个摘要。**
一个是 runner 哈希链记录的**磁盘**摘要，一个是 `S0_REPORT.json` 自称的
**内存**摘要，二者对同一 `MC_HANDOFF_*.jsonl` 给出不同的 64 位十六进制串。

**为什么 Stage F 抓不到**：Stage F 校验的是 runner 自有的清单链，其**两侧
都由磁盘导出**（`_record_artifacts` 的入参来自 `read_bytes`，复核也从磁盘读）。
两个 disk-derived 侧当然自洽；`sealed_files` 的内存侧**不在**那条链的比较范围内。

**本轮治理证明**也**站在内存一侧**（S3 追加核实，非复核员所报）：生产调用
是 `prove_governance(ctx, sealed_artifacts=files)`（`s0_real_run.py:1092-1093`），
读的是 `files["S0_REPORT.json"]` 这个**内存字符串**（`output_proof.py:529`），
**不是**磁盘字节；模块另有的 `report_path=` 分支（`:546` `Path.read_bytes()`）
**生产未使用**。因此 §1.2 的 CLOSED 应精确读作
**「渲染器打算封存的 `governance.*` 五键是对的」**，
**不是**「磁盘上最终躺着的那份是对的」。

**未修的原因与边界**：修法（`newline=""`，或改用 `write_bytes`）会改变
封存字节，属本轮范围外；本 packet 只如实登记。**它不推翻本轮的两条
CLOSED**（生命周期接缝完全在 exposure 之前、与落盘无关；治理证明在其
自陈的内存作用域内成立），但它**收窄** §1.2 的可读性，且**必须**在任何
真实 S0 授权之前处置。

---

## 5. 治理证明自身的限度（**本轮不予掩盖的三／二条**）

### 5.1 证明自陈的 3 条 PARTIAL（schema **未**扩展）

`output_proof._partial_coverage`（`:355-368`）**派生**而非手写这三条：

1. 没有任何字段把报告绑定到 registry **字节**——`governance.*` 无
   `registry_sha256`。
2. 没有任何字段把报告绑定到 **§10 授权语句**——无
   `exact_authorization_text_sha256`。
3. `registry_sequence_snapshot` 是一个 **COUNT**（`len(parse_registry_events(text))`）。
   **故一次保持事件条数不变的 registry 编辑，对本切片不可见。**

模块**没有权限**扩展已冻结的报告 schema，也**没有**去扩展；缺口以 PARTIAL
披露而非静默补齐。

### 5.2 本轮唯一**不遵循自身先例**的接缝（如实登记）

- **证明结果在封存输出中不留痕**：`prove_governance` 的三条 PARTIAL 披露
  被计算出来**随即丢弃**——`scripts/s0_real_run.py:1090-1096` 只用
  `proof.ok` 抛异常，`proof.partial` **不写入** `files` 的任何工件。
  于是「本次运行做过治理证明、且它自陈了三条缺口」这一事实，
  **在封存字节里无从查证**。
- **未接线的 `governance_context` 是 SKIP，不是 fail-closed**：
  `s0_real_run.py:1090` 为 `if governance_context is not None:`。
  生产路径确实接线（`:2337`）且有测试钉住，模块文档也给了理由
  （不给 context 就无法从被验对象自造 expectation，故「跳过而非伪造」）。
  **但这与本轮另一条接缝的处置相反**：`prepare_compute` 未接线是
  **FAIL**（§1.1）。**同一轮内两条接缝对「未接线」给出相反答案，
  这是本轮唯一不遵循自身先例之处，在此登记，不自行裁决。**

---

## 6. 治理／文档事实更正（本车道本轮的主体工作）

> 本节更正的是**文档**，不是代码、不是 registry、不是 exposure。
> 每条均先复算后书写；复算方法与行号一并给出，便于 Codex 独立复验。

### 6.1 更正一 —— 撤销「EV-11／preflight **全然未获批准**」这一框架

**此前的框架为过度声明。** 存在一条**外部治理链**（逐条对字节复算）：

| 环节 | 字节位置 | 内容 |
|---|---|---|
| **IR-22（APPROVED_BY_AARON 2026-08-01）** | `IMPLEMENTATION_RESOLUTIONS.md:70` | 明令「**context.py 与 s0_input_preflight.py 同步修复同测试**」——即 preflight 脚本被当作**共同维护的实现**，不是野生工件 |
| **IR-26（APPROVED_BY_AARON 2026-08-01，Aaron E5）** | `IMPLEMENTATION_RESOLUTIONS.md:123-` | 其等价性（B 条）与结构结果（C 条）**以 preflight 的逐日判定表为比对基准**，收口于「全 **66** 断言 all_pass=True 零失配」 |
| **registry 行 11** | `ops/TRIAL_REGISTRY.md:33` | `READY_FOR_RUN_AUTHORIZATION` 记录「Stage B 5/5 全过（含 **preflight_assertions_match 66/66**）」 |

**接线实况（源码复算）**：`S0_INPUT_PREFLIGHT.json` 经
`runinfra.translate_preflight_assertions`（`:772-860`）翻译成扁平 expected 集，
由 `runinfra.compare_preflight_assertions`（`:888-942`）**单向、逐项**比对
runner 独立算出的 actual；门为 `scripts/s0_real_run.py:683`
`GateCheck("preflight_assertions_match", …)`。比较集内**包含**
`label.<Y_cont|Y1..Y5>.{available,unavailable}` 共 12 键。

**结论**：**把 preflight 的结构性计数用作 expected 断言，是获治理授权的。**

**同时披露的 DOCUMENTATION-LAYER CONFLICT（不自行解决）**：

| 出处 | 字面 |
|---|---|
| `S0_INPUT_PREFLIGHT.json` 的 `"approval"` 字段 | `"AWAITING_AARON_APPROVAL"` |
| `S0_INPUT_PREFLIGHT_REPORT.md:5` | `approval: AWAITING_AARON_APPROVAL` |
| `src/itsf/s0/dataset.py:667-668`（docstring） | 「identical to the **approved** preflight's `label_anchor_availability`」 |
| `src/itsf/s0/context.py:73`（module docstring） | 「Semantics are kept identical to the **APPROVED** `scripts/s0_input_preflight.py`」 |

即：**工件自带的 approval 字段说「待批」，两处源码 docstring 说「已批」，
而外部 IR/registry 链授权的是「用其计数作为期望值」。**
本车道**将其定性为 DOCUMENTATION-LAYER CONFLICT**，
**不修改 registry，不修改源码，不自行裁决**。

> **本条不得被读作 D-4 已闭。** 授权的对象是**用计数作比较**；
> **不是**把 EV-11 的五个 per-day 布尔→标签集 **reducer** 冻结为研究语义。
> IR-23 的枚举确为部分（`IMPLEMENTATION_RESOLUTIONS.md:71` 只列
> Y1/Y2/Y3，Y_cont/Y4/Y5 仅称「继续依赖方向」）。
> M6.1.4-R2 复核员 R2 对该围栏的判定（「reducer 未被推导；
> `dataset.py:688-695` 未冻结 ＋ IR-23 仅部分列举」）**继续成立**。

### 6.2 更正二 —— **撤回**`_LABEL_DEPS` 与 `ok`「互斥／内容不同」的主张（该主张为假）

**逐格复算（本车道自行执行，非采信）**：

`_LABEL_DEPS`（`src/itsf/s0/dataset.py:151-159`）四列为
`(O1000, C1544, ADR14, d_open)`；`ok`（`src/itsf/s0/dataset.py:688-695`）
在同四轴上的取值如下：

| 标签 | `_LABEL_DEPS`(O,C,ADR,dir) | `ok` 在同四轴上 | 同轴一致？ | `ok` 另需 |
|---|---|---|---|---|
| `y_cont` | T T T T | `o1000 and c1544 and adr_ok and dir_ok` → T T T T | **是** | — |
| `y1` | T T T F | `o1000 and c1544 and adr_ok` → T T T F | **是** | — |
| `y2_de_pm` | T T F F | `o1000 and c1544 and pm_ok` → T T F F | **是** | `pm_ok` |
| `y3_close_pos_pm` | F T F F | `c1544 and pm_ok` → F T F F | **是** | `pm_ok` |
| `y4_mfe` | T F T T | `o1000 and pm_ok and adr_ok and dir_ok` → T F T T | **是** | `pm_ok` |
| `y5_mae` | T F T T | 同上 → T F T T | **是** | `pm_ok` |

**六个标签、四条轴，全部一致。** 唯一差别是 `ok` 另需 `pm_ok`，
而 `_LABEL_DEPS` **根本没有 PM 列**。

**正确表述**：`_LABEL_DEPS` 是 `ok` 在五条依赖轴中**四条上的 PROJECTION**；
在该投影所表示的每一条轴上，两者一致。**这不是矛盾，也不是需要 Aaron
裁决的事项。**

**据此**：此前拟建的台账行 **`NEW-LABELDEPS-CONFLICT` 予以 WITHDRAWN**。
（**如实记录**：本车道全库检索 `NEW-LABELDEPS-CONFLICT` 字面**零命中**——
该行从未落到仓库字节，故撤回是**纯文档性**的，无行需删除。
真正落在字节里的是 `M6_1_4_LEAF_LINEAGE_MATRIX.md:124-127` 那段
「**内部矛盾**」散文，已在该文件内就地更正。）

### 6.3 更正三 —— 不得主张 dataset 归约器与 preflight 归约器「字节相同或语义相同」

前序车道曾断言「`ok` 在六个标签上与 preflight 的 `required_anchors` **精确**
一致」。**由于同一车道在 §6.2 上判断有误，该同一性主张按 UNVERIFIED 处理。**
本车道进一步**实测到三处谓词级差异**，因此该主张不仅未经核实，且在**谓词
形态上已被反证**：

| # | preflight（`scripts/s0_input_preflight.py:1123-1143`） | dataset（`src/itsf/s0/dataset.py:683-695`） |
|---|---|---|
| 1 | `pm_ok = not np.all(np.isnan(pm_h))` —— PM **high** 至少一根非 NaN | `pm_ok = s.pm_present > 0` —— PM 窗口内**bar 行数**计数（`context.py:449` `pm_present=int(pm.sum())`，`pm` 是**分钟掩码**，即行存在性，非取值有限性） |
| 2 | **Y2 用另一个谓词**：`np.sum(~np.isnan(pm_c)) > 0` —— PM **close** | Y2 复用同一个 `s.pm_present > 0` |
| 3 | `d_ok = not(isnan(o930) or isnan(c959)) and c959 != o930` —— 直接锚点判定 | `dir_ok = (r.direction_status == DIRECTION_DIRECTIONAL)` —— 经 IR-24 链派生（`dataset.py:296-317`），ret_open30 不可定义时归 `direction_undeterminable_na` |

（另：`a_ok = d in adr_ok` 对 `universe.adr14[d] is not None`，来源不同。）

**可以陈述的等价范围（KNOWN EQUIVALENCE SCOPE）**：

- **轴集层面一致**：若把 preflight 的 `PM high` / `PM low` / `PM close path`
  合并读作单一「PM 轴」，则六个标签的**必需轴集合**两侧一致。
- **数值层面**：仅有**经验一致**——registry 行 11 记录的是在 A1 数据上
  `preflight_assertions_match 66/66`。**那是一次观测，不是结构等价证明。**

**工程一致性风险（ENGINEERING CONFORMANCE RISK，具名登记）**：该门是
compare-only 的**生产阻断门**（失败即 Stage B STOP，见 registry 第 `+` 行
2026-08-01 的 `INC-fa9234e0e541`）。expected 与 actual 由**两份形态不同的
实现**产生，其一致性今日**只有经验证据**。任一侧的 PM／direction 谓词
被独立修改，都可能在真实 S0 上把一次结构性差异表现为一次运行期 STOP。
**IR-22 已经预见到这一点**（明令两侧「同步修复同测试」）；本条是对该命令
在**当前字节**上仍需持续遵守的登记，**不是**新裁决请求。

**顺带登记（本车道不拥有该文件，不修改）**：`dataset.py:667-668` 的
docstring 自称与 preflight「identical」。按本节，该词在**谓词层面**过强。

### 6.4 更正四 —— `M6_1_4_LEAF_LINEAGE_MATRIX.md` 标为 `PROVISIONAL / REJECTED AS TRUTH SOURCE`

已在该文件顶部落标。要点：

- **被拒的是**其 **§1／§4 散文**与其 **`authority` 列**——不得作为源码事实引用。
  依据：`CODEX_REVIEW_PACKET_M6_1_4.md` §10.4 第 4／5／6 条（R2 实测证伪）。
- **它并非惰性文件（如实披露）**：`tests/test_s0_evidence.py:2372` 把该文件
  路径钉为 `_MATRIX_PATH`，解析其 **§9** 的机器可读围栏块
  （**6 列**、**121 行**，本车道复算一致）并与 `evidence.LEAF_REGISTRY`
  **双向**比对（`test_leaf_registry_matches_the_lineage_matrix_document`、
  `test_the_matrix_declares_exactly_121_leaf_rows`）。**§9 块因此保持原样，
  一个字节未改。**
- **本轮实测到的一处解析器脆弱性（新发现，见 §7.2）**：该解析器用
  `text.index(_FENCE)` 取**第一处**围栏标记，故在 §9 **之前**任何位置
  出现该标记字面量（例如在散文里引用它）都会把解析窗口挪到错误位置，
  两个测试同时红。本车道在落标时误触发过一次并当场回退——
  **文档编辑可以打断代码测试**，这是本文件「非惰性」的具体后果。
- **`authority` 列为何被单列**：`LeafSpec` 确有 `authority` 字段
  （`src/itsf/s0/evidence.py:1997`），但 §9 的机器可读块**只有 6 列**且
  **不含 authority**——即该列**两个方向都没有被钉住**，与 §10.4 第 3 条
  闭合要求所指为同一件事。

---

## 7. 本轮新发现的文档漂移（不在指派清单上，如实登记）

**授权包 `S0_REAL_RUN_AUTHORIZATION_PACKET.md` §0 环境锁的逐行时效表已被
本轮改动追过**（本车道对当前工作树字节逐行复算）：

| 行 | 表中标注 | 本轮实况 |
|---|---|---|
| `src/itsf/s0/runner.py` | 属「其余 10 行……逐项一致」 | **已失效**：锁内 `772790cd9572446a`，现值 `0c1e5cbb9861f8da`（本轮 S1 改动） |
| `scripts/s0_real_run.py` | 已标 `STALE`（仍正确） | 但其「现值」注记应更新：`5ea7b7f11e84577c` → `937c96bf6b15d26b` |
| `src/itsf/s0/output_proof.py` | **不在锁内** | 本轮**新增的生产源**，环境锁未收录（现值 `1f045ed5fb75480a`） |
| 其余 9 行 ＋ `requirements_lock` | 一致 | 复算一致，维持 |

已在授权包内就地更新该表。**「不得对本块整体加『全部陈旧』笼统标注」这一
既有约束继续成立**——本轮仍有 9 行为真。

---

## 8. Codex 复审入口

1. **§0 门 → §1 两条 CLOSED → §2 四对象分辨率表**（重点核对是否有把
   接缝级闭合读成 F-1／F-2 级闭合之处）。
2. **§4** —— 本轮最重的一条**未修**项。建议独立复跑本文件给出的
   `write_text` 探针，并核对 `runner.py:558-559` 与
   `s0_real_run.py:1050-1057` 两段。**另请特别核对 §4 末段**：治理证明
   在生产路径上读的是**内存字符串**而非磁盘字节
   （`s0_real_run.py:1092-1093` → `output_proof.py:529`），
   这是 S3 追加发现、**不在复核员所报之列**的一条限定。
3. **§5.2** —— 同一轮内两条接缝对「未接线」给出相反答案，请给立场。
4. **§6.1／§6.3** —— 治理链存在与谓词不同一，两件事必须同时成立地被接受；
   若 Codex 认为 §6.1 已足以关闭 D-4，请明确说明（本车道**未**如此主张）。
5. **§3 的限定**：本轮两条修复**未经独立复核**，不得计入 CLOSED。
6. 若接受工程面：**DR-1…DR-8 与 READY supersession 仍是 Aaron 队列中
   仅有的两组裁决项**；本里程碑**未新增第三组**。
   Strategy Council 在 Codex 工程裁定通过前保持关闭。

---

## 9. 本轮红线自查（本车道声明）

- 未修改任何源文件、测试文件、`ops/TRIAL_REGISTRY.md`、`EXPOSURE_LEDGER.md`、
  或任何 `guards.FROZEN_HASHES` 冻结件。**证据**：本车道编辑前后逐一复算，
  7 个生产源（`s0_real_run 937c96bf6b15d26b` · `contracts d72a9b05dbf481a4` ·
  `handoff a1f2c0a1ac77f96d` · `report 52d050bb6f1095e9` ·
  `runner 0c1e5cbb9861f8da` · `evidence 676fbcd1ae0ac2a9` ·
  `output_proof 1f045ed5fb75480a`）、7 个测试文件、registry
  （`de63b3d6…`）与 exposure（`39481343…`）**哈希全部逐位不变**。
- 本车道触碰的**唯一**一个被测试消费的文件是
  `M6_1_4_LEAF_LINEAGE_MATRIX.md`；其 **§9 机器可读块一字节未改**，
  `tests/test_s0_evidence.py` 全 **324 passed / 0 failed** 复验通过。
- 未提交、未建 tag、未追加 registry 事件、未新铸研究 DR 编号。
- 未运行真实 S0、未读取真实数据、S0-T001 未消耗。
- `git diff --check` 在本车道的编辑后仍为净。
