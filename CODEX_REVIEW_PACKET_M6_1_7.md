# CODEX_REVIEW_PACKET_M6_1_7（字节保真 ＋ 磁盘发布判定 ＋ 治理快照单源，供 Codex 独立复审）

- **baseline（父 commit）**：`185e47f7e95c5d0cca4b44257c5b32c99790ef83`（M6.1.6）
- **本审查对象**：`UNCOMMITTED_WORKTREE_SNAPSHOT`（**未提交**的工作树；
  本里程碑**无任何 commit**）。故本文件通篇**不使用**「本 commit」字样——
  没有 commit 可指。

  > **【M6.1.8 事实更正，2026-08-09，`FABLE_MEASURED`】上面两行在写下时为真，
  > 现已过期。** 本文件所描述的工作树其后**已落为候选 commit
  > `bdc060cefa0eac4351c9c7bc82784e2527391943`**（父 `185e47f7`）。
  > 因此本文件通篇的「当前工作树」「未提交」应读作**该 commit 的字节**。
  > 原文保留不删——这是 M6.1.7 在其自身时点上的诚实记录，且当时确实
  > 无 commit 可指；此处只加时点标注，不改写历史。
  > 凡本文件中带时刻限定的观测值（尤以 §8.7 的 `git status --porcelain`
  > 计数与源文件哈希为甚）**均按同一条纪律作废**：读者须对
  > `bdc060ce` 的字节重新复算，不得转录。
- **授权状态（registry 词汇原文）**：`REAL_S0_NOT_AUTHORIZED`。
  不追加 READY、不申请授权、不建 tag、**不追加任何 registry 事件**、
  **不新铸任何研究 DR 编号**。`runs/` 仍不存在，S0-T001 未消耗。
- **本轮闭合的是四个**具名对象（§1 逐条分述），**不是** F-1／F-2 中的
  任何一个整体（§2）。
- **本文件的一条结构性坦白，放在最前**：本轮最重的发现（§1.3）是一条
  **潜在的真实运行期缺陷**，不是整洁度问题。它会把一个**错误的**
  `registry_sequence_snapshot` 写进封存报告，而且**两侧对照会一致地
  同意那个错值**。它至今未被发现，是因为合成测试从不向真实 registry
  追加 `RUN_STARTED`。

---

# ⛔ H-1 —— 真实运行 READINESS 的具名阻断项（**致 Aaron 与 Codex；不阻断本次 commit**）

> **本节独立于四条闭合，放在最前，因为它不该被埋进任何 findings 表格。**
> 它**不是** M6.1.7 引入的，**不在** M6.1.7 的四条闭合范围内，
> **因此正确地不阻断本次提交**。
> 但它会在**第一次越过 `prepare` 的运行上确定性地发生**，
> 并且是在 M6.1.7 的每一条机制都已经通过之后才发生——**烧掉 S0-T001**。
>
> > **【M6.1.8 表述更正，2026-08-09，`FABLE_MEASURED`】上一句的触发条件写窄了、
> > 因而写错了。** 过 `prepare` 是**必要不充分**条件。精确表述为：
> > **任何成功抵达 Stage-E artifact recording、且未先因其他原因失败的运行
> > 都会触发。** 该行必须先通过 `render_report` 与 `post_write_verify`
> > 才可能到达 `_record_artifacts`，故「越过 `prepare` 即必然」不成立。
> > 本节稍后关于「必须在第一次真实 S0 之前被处置」的诉求，同受下方注记更新。
> > **H-1 已在 M6.1.8 修复**（日志行改用不透明序号，
> > 词表与工件名均未动）——详见 `CODEX_REVIEW_PACKET_M6_1_8.md` §1。

**症状**：生产的 guarded logger 会在 **Stage F** 烧掉 trial ——
**在一次已经完全通过验证的封存之后**。

**机制（S3 逐环独立核实，非转录）**：

| # | 环节 | 字节位置 / 实测 |
|---|---|---|
| 1 | Stage E 为**每个**工件记一行 `file={name} sha256={hex}` | `src/itsf/s0/runner.py:519`（在 `_record_artifacts` 内） |
| 2 | `runinfra._FORBIDDEN_VOCAB_RE`（`runinfra.py:503-506`）命中该名 | 词表 36 项，其中含**小写** `'e1'` / `'e2'`；正则带 `re.IGNORECASE`，故命中 `MC_HANDOFF_E1_Base.jsonl` 中的 `E1`。**S3 实跑 `validate_log_event` → `LogLeakError`** |
| 3 | 命中范围 | **10 项 `sealed_files` 中恰 8 项**（8 份 `MC_HANDOFF_<E1\|E2>_*.jsonl`）。`S0_REPORT.md`、`HANDOFF_ADMISSION.json` 不命中（S3 逐名实测） |
| 4 | `_safe_log` 把 `LogLeakError` **吞进** `self._log_errors` | `runner.py:294-300` |
| 5 | **Stage E 结束时没有任何东西检查 `_log_errors`** | 检查点只有 `:551`（Stage A）、`:569`（Stage B）、`:682`（Stage C）、`:790`（Stage F）——**Stage D／E 之间没有** |
| 6 | Stage F 的检查随后开火 | `runner.py:790-792` → `_fail_run(RunStage.F_SEALED, …, "log_guard", …)` |

**S3 独立复现（合成运行；真实 `S0Runner` ＋ 生产工件名 ＋ 生产 guarded logger
＝ `tests/test_s0_runner.py:143-149` 的 `guarded_logger`，即
`scripts/s0_real_run.py` F-04 注入的同一个包装；未读真实数据，未碰真实 registry）**：

```
--- PRODUCTION guarded logger ---
  ok=False  terminal=RunStage.F_SEALED  exposure_consumed=True
  failed_gate='log_guard'
  registry events=['RUN_STARTED', 'FAILED']
  stages_completed=('A_PRECHECK','B_LOAD_VALIDATE','C_COMPUTE','D_INTEGRITY','E_REPORT')

--- plain logger (control) ---
  ok=True   terminal=RunStage.F_SEALED  exposure_consumed=True
  registry events=['RUN_STARTED', 'COMPLETED']
  stages_completed=(… ,'E_REPORT','F_SEALED')
```

**`stages_completed` 里有 `E_REPORT`——这是本条最重的一个字。**
它意味着写后磁盘证明**已经通过**、清单链**已经封好**、
M6.1.7 的四条闭合**全部生效并全部成功**，
然后 trial 被一条**日志行**杀死。同一接线换成朴素 logger 即抵达 `COMPLETED`。

**出处与范围（严格限定，不夸大）**：

- **基线即存在**：同一行日志在 `185e47f7` 的 `src/itsf/s0/runner.py:396`
  逐字相同（S3 对基线字节核实）。**M6.1.7 没有引入它。**
- **不在本轮范围内**：它与四条闭合（字节保真／磁盘判定／快照单源／
  通用性回退）无一相交。**故它正确地不阻断本次 commit。**
- **但它今天之所以看不见，与其余一切同墙**：`_approved_injectables()`
  （`scripts/s0_real_run.py:1141-1148`）返回 `None`，生产在 `prepare` 处
  即 fail closed。**H-1 与磁盘验证器一样，都还没在真实路径上跑过。**
  区别在于：磁盘验证器**可能**通过，H-1 **必定**开火。

**S3 的严重度措辞（不软化，也不越权）**：这是一条
**REAL-RUN READINESS BLOCKER**，**不是**一条 M6.1.7 缺陷。
它的代价是**在一次成功的封存之后烧掉首个真实 trial**，
而恢复需要 registry 上的一次 supersession ＋ Aaron 重发 §10 语句
——即它的成本不是「重跑一次」。
**S3 不提出修法，也不修改任何 `.py`**：日志词表与 Stage-E／F 的检查点位置
都在本车道 lease 之外。**本条唯一的诉求是：它必须在第一次真实 S0 之前被处置，
且该处置需要 Aaron／Codex 的决定，而不是一次静默的工程改动。**

> **【M6.1.8 状态更新，2026-08-09，`FABLE_MEASURED`】本条诉求已履行。**
> Aaron 以 M6.1.8 执行提示词明确授权处置 H-1，并**明令**：不得放宽
> `_FORBIDDEN_VOCAB`、不得白名单 `e1`／`e2`、不得改工件名、manifest 须保留
> 真名／真摘要／原顺序。修法为**只改日志行**，改用不透明序号
> `file=artifact_NNNN sha256=…`。故这**不是**一次静默工程改动——
> 它是一次被明确授权、且带有硬约束的处置。
> 结论定性见 `CODEX_REVIEW_PACKET_M6_1_8.md` §1.3：
> **守卫在此处的拒绝是假阳性**，工件名是冻结契约 engine×scenario 矩阵
> 定死的运行不变常量，零数据派生信息；本轮做的是**尊重词表的规避**，
> 不是修补真实泄漏。词表对结构性常量过宽一事，**仍具名延后**。

---

## 0. 验收门实测

**证据级别声明（逐行标注，不设跨行统一标准）**：

| 标注 | 含义 |
|---|---|
| `S3_MEASURED` | 本文件作者（只读治理车道 S3）于 2026-08-09 在**当前未提交工作树字节**上自行实测／复算，非转录 |
| `S3_DERIVED` | S3 由源码结构推导（无真实运行可测，理由随条给出） |
| `MAIN_AGENT_MEASURED` | **主代理**在最终树上实测并交回；**S3 未复跑该项**，故按其真实出处署名，不冒领 |
| `REVIEWER_MEASURED` | **独立只读复核员**实测；S3 未复跑，同样按其真实出处署名 |
| `CODEX_NOT_RERUN` | Codex 未独立复跑；复审时应视为待验证的自报数据 |

| 门 | 结果 | 标注 |
|---|---|---|
| **`python -m pytest -q`（全量，修复轮后的最终树）** | **2205 passed / 0 failed / 0 skipped**，275.60s | **`MAIN_AGENT_MEASURED`**`; CODEX_NOT_RERUN` |
| `python -m pytest -q`（全量，**修复轮之前**的树） | **2204 passed / 0 failed** | **`REVIEWER_MEASURED`** |
| collect 重算（最终树） | **2205** | `S3_MEASURED` |
| collected == `MIN_COLLECTED_TESTS` | **2205 == 2205**；**双钉**：`scripts/s0_real_run.py:47` 与 `tests/test_s0_runner.py:894`（`assert mod.MIN_COLLECTED_TESTS == 2205`）。门本身是 `<` 的**下限**（`:518`），不是等式 | `S3_MEASURED`（逐行核对） |
| `pytest` 三份改动测试 ＋ `test_s0_evidence.py`（S3 于**修复轮前**收口重跑） | **698 passed / 0 failed**，170.39s，exit 0（＝ 374 ＋ 324） | `S3_MEASURED; CODEX_NOT_RERUN` |
| 其中 `tests/test_s0_evidence.py` | **324 passed / 0 failed**，与 M6.1.4-R2／M6.1.6 同值（F-2 面未动的字节佐证，另见 §5） | `S3_MEASURED` |
| 独立复核判定 | **`M6_1_7_REVIEW=PASS`**，无 in-scope High／Medium | **`REVIEWER_MEASURED`**（见 §9） |
| `pytest tests --collect-only`（baseline `185e47f7`，`git archive` 导出到隔离目录后复跑） | **2146 collected** | `S3_MEASURED` |
| `git status --porcelain` 改动集 | **10 行 ＝ 9 modified ＋ 1 untracked**，**在本次测量的那一刻**（3 源 ＋ 3 测试 ＋ 3 份 S3 治理文档 ＋ 本文件 untracked）。**该数字把测量者自己也算在内**：本文件与另三份治理文档都在改动集里，故它每被本车道写一次就会变一次——按 §8.7 的同一条纪律，它是**带时刻限定的观测值，不是稳定事实**（复核员 L-8） | `S3_MEASURED` |
| `git diff --check` | 净（exit 0） | `S3_MEASURED` |
| `ops/TRIAL_REGISTRY.md` sha256 | `de63b3d690c5c4be1def67aff9e0302138e9910df5b9a89acb1db57697b0b440`（＝基线，未修改） | `S3_MEASURED` |
| `EXPOSURE_LEDGER.md` sha256 | `394813431d879555b7504d2501c40123368d67a517359e056692eb6b0f6bc9e6`（＝基线，未修改） | `S3_MEASURED` |
| `runs/` | 不存在 | `S3_MEASURED` |
| 真实数据 | 零读取；未运行真实 S0；S0-T001 未消耗 | `S3_MEASURED` |

> **两个全量数字都是真的，且各自属于不同的树**：
> **2204 = 修复轮之前**（复核员实测），**2205 = 修复轮之后**（主代理实测，
> 差额即新增的 L-4 行为测试）。**不得把它们写成同一次运行的两种说法。**
>
> **署名边界（不得抹平）**：两个全量 `pytest -q` 结果**均非 S3 所跑**，
> 故分别署 `MAIN_AGENT_MEASURED` 与 `REVIEWER_MEASURED`。
> S3 在其工作期间**曾拒绝**书写「2146 → 2204 全绿」——当时
> `tests/test_s0_runner.py` 仍在被编辑，一次全量跑测的是移动靶，
> S3 没有跑过它。**该拒绝在此保留记录，且不因他人事后跑出结果而追认为
> S3 的实测。** 一个数字的价值取决于谁在什么字节上量的，这条区分本身
> 就是本 packet 的内容之一。
>
> **S3 独立复核了这些结果中可静态复核的侧面**：
> collect 重算为 **2205**，`MIN_COLLECTED_TESTS` 双钉同为 **2205**
> （`scripts/s0_real_run.py:47` ＋ `tests/test_s0_runner.py:894`，逐行核对）。
> **两个全量运行的通过／失败数本身，S3 均未复核。**

**生产源哈希（sha256 前 16 位，当前工作树实测，`S3_MEASURED`）**：

```
scripts/s0_real_run.py      131b0dd11422ca3d        # 本轮改动（M6.1.6 值 937c96bf6b15d26b）
src/itsf/s0/runner.py       b44306f8f1202e80        # 本轮改动（M6.1.6 值 0c1e5cbb9861f8da）
src/itsf/s0/output_proof.py b43c05243bd9b886        # 本轮改动（M6.1.6 值 1f045ed5fb75480a）
src/itsf/contracts.py       d72a9b05dbf481a4        # 未动
src/itsf/s0/report.py       52d050bb6f1095e9        # 未动
src/itsf/s0/handoff.py      a1f2c0a1ac77f96d        # 未动
src/itsf/s0/evidence.py     676fbcd1ae0ac2a9        # 未动
```

---

## 1. 本轮闭合的四个对象

### 1.1 Stage E **字节保真** —— CLOSED（缺陷已由 S3 独立复算）

**缺陷（对 baseline `185e47f7` 的字节实测，不是转述）**

- `src/itsf/s0/runner.py:558`（baseline）：`path.write_text(content, encoding="utf-8")`
  ——**没有** `newline=`。Windows 上以**文本模式**打开，`\n` 被转译为 `\r\n`。
- `src/itsf/s0/runner.py:559`（baseline）：`written.append((name, path.read_bytes()))`
  ——进入 runner 自有哈希链的是**磁盘字节**。
- `scripts/s0_real_run.py:1050-1057`（baseline）：
  `mc_handoff_manifest.sealed_files[<name>]` 的 `sha256` 与 `bytes` 取自
  `body.encode("utf-8")` ——**内存字节**（LF）。

→ **一个工件、一个封存输出内部、两个互相矛盾的自陈。**

**S3 本机实测探针（`S3_MEASURED`，Python 3.13.14 / Windows 11）**：

```
write_text('a\nb\nc', encoding='utf-8')  ->  磁盘 b'a\r\nb\r\nc'
  sha256(disk)[:16] = d37a6c0b581046ee     len(disk) = 7
  sha256(mem )[:16] = ea7fb08b7a2dc461     len(mem ) = 5
write_bytes(b'a\nb\nc')                  ->  磁盘 b'a\nb\nc'（逐位相同）
json.dumps(..., sort_keys=True)（无 indent） ->  单行，正文内无裸 LF（相同）
```

**规模复算（10 项 `sealed_files`，全集 11 项）**

`sealed_files` 的成员由 `scripts/s0_real_run.py:982-1057` 唯一决定，S3 逐项复算：

| # | 工件 | 序列化 | 正文含裸 `\n`？ | baseline 下声明是否等于磁盘 |
|---|---|---|---|---|
| 1 | `HANDOFF_ADMISSION.json` | `handoff.dumps_canonical` ＝ `json.dumps(..., allow_nan=False, sort_keys=True)`，**无 `indent`**，单行 | 否 | **是** |
| 2-9 | `MC_HANDOFF_<E1\|E2>_<Base\|Conservative\|Stress\|Severe>.jsonl`（**8** 项） | `"\n".join(...)` 逐记录 | 是 | **否** |
| 10 | `S0_REPORT.md` | `"\n".join([...])`（字面量列表） | 是（**5** 个） | **否** |

→ **9 / 10 不匹配。与主代理告知的数字一致。**

`SEED_MANIFEST.json` 不在其中：`build_seed_manifest()` 在
`src/itsf/s0/handoff.py:2235` 显式置 `artifact["formal_sealable"] = False`，
经 `_partition_admission` 被 **WITHHELD**，从不进入 `files`。
`S0_REPORT.json` 自排除（`self_excluded`），故 10 ＋ 1 ＝ 11。
「8 项 JSONL」另有一处**独立**佐证，不依赖 S3 对渲染循环的阅读：
`src/itsf/s0/report.py:2627-2628` 的 `validate_sealed_files` 硬性要求
manifest 的 file-KEY 集合**恰为** `{E1,E2} × {Base,Conservative,Stress,Severe}`
＝ 8 键。

**S3 追加的两条精确化（主代理未提及，属对给定数字的补强，非否证）**

1. **错的不止 `sha256`，`bytes` 也错。** 每条 `sealed_files` 条目声明**两个**
   事实。S3 用 baseline 的 `S0_REPORT.md` 字面量正文实测：内存 **425** 字节，
   磁盘 **430** 字节（正文 5 个 LF，每个 +1）。即 9 个工件的**字节数声明**
   同样为假，偏移量恰为该工件的 LF 计数。本轮新的磁盘证明**两个字段都查**
   （`output_proof.py:726-772`，每工件三次计数化检查：存在／字节数／摘要）。
2. **「9/10」在结构上依赖「每份 JSONL 至少 2 条记录」。** 正文是
   `"\n".join(...)`：0 或 1 条记录时正文无裸 LF，该项会「匹配」。
   记录逐**可构造日**生成（`src/itsf/s0/study.py:605-617`，`for day, inp in usable`），
   真实 S0 数据集下每（engine, scenario）为数千条，故该退化情形在真实运行中
   不可达。**`S0_REPORT.md` 一项则无条件成立**（字面量列表，恒含 5 个 LF）。
   本 packet 把 9/10 记为 **`S3_DERIVED`（真实运行下确定成立）**，
   而非 `S3_MEASURED`——**因为没有真实运行可测，而伪造一次不是选项。**

**Stage F 为何抓不到**：Stage F 校验 runner 自有的清单链，其**两侧都由
磁盘导出**（链入参来自 `read_bytes()`，复核也从磁盘读，`runner.py:781`）。
两个 disk-derived 侧当然自洽；`sealed_files` 的内存侧不在那条链的比较范围内。
Stage-E 的既有 `rep.validate_sealed_files(files, formal)`（`s0_real_run.py:1072`）
同样看不见：它的入参 `files` 是 `Mapping[str, str]`，**一个内存映射**。

**修法与其一条可验证后果**：`runner.py:719-728` ——
`data = content.encode("utf-8")` 编码**恰好一次**，该 `bytes` 值被
`write_bytes` 原样落盘（二进制模式，无换行转译）、被 `_record_artifacts`
直接哈希入链、并被交给验证接缝。路径上**不再有任何 re-read 取摘要**的动作，
故「同一工件两个摘要」在构造上不可能。
**顺带的强化，值得复审员单独确认**：修前 Stage F 的两侧同源，是一次
**同义反复**；修后链侧是内存 `bytes`、Stage F 侧是 `Path.read_bytes()`，
Stage F **首次成为对写入路径的真实交叉检验**。

**须显式声明的后果**：该修法**改变真实运行的封存字节**——修后每个含换行的
工件（含 `indent=1` 的 `S0_REPORT.json`，见 `report.py:919-922`）在磁盘上为
LF。因 `runs/` 不存在、S0-T001 未消耗，**没有任何既有封存工件因此失效**。

### 1.2 发布判定**改从磁盘取得** —— CLOSED

**M6.1.6 的判定对象是一个 `dict`。** 生产调用为
`prove_governance(ctx, sealed_artifacts=files)`（baseline `s0_real_run.py:1092-1093`），
读的是 `files["S0_REPORT.json"]` 这个**内存字符串**。故其 CLOSED 的精确含义是
**「渲染器打算封存的内容是对的」**——一个关于**尚未落盘的映射**的主张。
§1.1 的度量正是这一读法的代价：在那个判定说「通过」的同时，磁盘上 10 个工件
里有 9 个与其自陈不符。

**本轮的结构性改动（源码核实，不是承诺）**

- `sealed_artifacts=` **成为毒丸**：`output_proof.py:946-953`——传入即
  `ProofRefused`，旧调用点**响亮失败**而不是继续悄悄意味着更弱的那件事。
- 生产改传 `report_path=<run_dir>/S0_REPORT.json`（`s0_real_run.py:2440-2444`）。
- `GovernanceProof.__post_init__`（`output_proof.py:821-830`）拒绝任何
  `actual_source != "file"`。**故「存在一个 `GovernanceProof`」与「磁盘字节
  被检查过」是同一句话**——这是类型层的强制，不是文档承诺。
- 内存检查**降级留存**为 `screen_governance_draft`（`:1012`），返回
  `DraftScreen`：**无 `ok` 字段**，`ok` **属性**抛 `ProofRefused`（`:861`），
  `__bool__` 抛 `TypeError`（`:870`）。照抄惯用 `if not result.ok:` 的调用者
  会在**接错线的那一行**拿到异常。
- **新增第二条轴（Q2）**：每条声明的 `sealed_files` 条目的 `sha256` 与 `bytes`
  对 `Path.read_bytes()` 逐条比对；且声明的文件集合必须**恰好等于**运行目录
  里实际存在的集合（保留 `S0_REPORT.json` 自排除，基础设施文件名由调用方
  **显式声明**，无宽容默认值——`_validated_infrastructure`，`:880-906`）。
- **F-c（期望域塌缩）在这条新轴上是从另一侧设防的**：`disk_checks_required`
  确实由 manifest（被守护对象）定尺寸，但文件**全集来自 `Path.iterdir()`**，
  故清空 `sealed_files` 不会清空域，而是把磁盘上每个工件都变成
  `disk_extra_file` 问题（且空 `sealed_files` 本身即 `manifest_missing`）。
  **这一点请复审员单独确认**（§8.3）。

### 1.3 治理数据改从**曝光前快照**取得 —— CLOSED（**本轮最重的一条**）

**这不是整洁度问题，是一条潜在的真实运行期缺陷。**

**缺陷（baseline 源码 ＋ S3 对 registry 字节实测）**

- baseline `RealChain.compute()`（`s0_real_run.py:2423-2431`）内：
  `text = REGISTRY.read_text(...)`，`"registry_sequence_snapshot": len(parse_registry_events(text))`。
- 那次读发生在 `_atomic_run_start` 追加本次运行**自己的** `RUN_STARTED` 行**之后**
  （`runner.py:648-659`：exposure 在此消耗，`compute` 在 `:676` 才被调用）。
- 追加的行是 `append_registry_event_line`（`runner.py:806-807`）产生的
  `| + | utc | event | commit | actor | note |` ——**六格表行**，
  而 `parse_registry_events`（`s0_real_run.py:151-183`）**正是按六格表行计数**。
- **S3 实测**：当前 `ops/TRIAL_REGISTRY.md`（sha256 `de63b3d6…b440`）解析出
  **13** 条事件（seq 1..11 ＋ 两条 `+` PRE_RUN_ATTEMPT_FAILURE）。
  真实运行进入 Stage C 后即为 **14**。
  → 封存的 `registry_sequence_snapshot` 会是 **N＋1 ＝ 14**，
  而「授权时的 registry」是 **13**。

**它为什么一直没被发现（这是本条的要害）**

`_expected_governance()`（baseline `s0_real_run.py:2183` 起）**在封存时又读了一次
registry**，而生产渲染入口 `render_report_with_governance_proof(result)`
（baseline `:2318`）调用 `render_s0_report(result, governance_context=ctx)` 时
**不传** `expected_governance=`，于是 `s0_real_run.py:913` 的默认分支触发。
**契约检查的两侧一起漂移，在 14 上握手言和。** 合成测试同样抓不到：
它们从不向一个真实 registry 追加 `RUN_STARTED`。
**这与 §1.1 是同一个形状**——检查与其期望取自同一个正在移动的源，
就看不见那个源在动。

**修法（源码核实）**

- prepared 对象新增 `snapshot`（`s0_real_run.py:2301` `__slots__` 加一项，
  `:2303-2306` 构造），
  由 `make_snapshot_control` 闭包持有的 **Stage-A 快照**传入
  （`prepare_for_run`，`:2641-2654`），**不是**在 `prepare` 内再读一次
  registry——「一个事实两个来源」正是本里程碑两条缺陷的共同成因。
  因为取自该闭包，`pre_exposure_recheck` 的「registry 自授权以来逐字节未变」
  证明**恰好适用于本次运行将要封存的那个值**。
- `compute` 只从快照取治理数据（`:2570-2582`），并在注释里立下
  「本行以下不再读 `REGISTRY`」的约束；冻结哈希 re-hash 仍**故意保持实时**
  （那是另一个事实，且有 `guards.FROZEN_HASHES` 作独立权威可比对）。
- `_expected_governance(snapshot)`（`:2194-2230`）**只从快照取 SEQUENCE**，
  **仍从实时 registry 字节重读 authorized COMMIT**，两者不一致即 `raise`。
  **这一点是本修法里最需要被看懂的一处**：若两侧都改从快照取，比较就会
  **变成空洞的**——那正是 `evidence.py` 硬编码 compared-count 的老毛病。
  保留 COMMIT 的独立字节观测，是为了让这条比较继续有内容。

**测试侧的钉子（S3 核实在场）**：`tests/test_m6_chain.py:924-940`
（`test_m617_expected_governance_takes_the_sequence_from_the_snapshot`）
断言 `gov["registry_sequence_snapshot"] == live_count - 1` **且**
`!= live_count`——即把「＋1 bug」本身钉成红线；`:99` 的合成快照
`"registry_sequence_snapshot": 13` 与 S3 对真实 registry 的实测计数一致。

### 1.4 `if not prepared` 回退为 `if prepared is None` —— CLOSED（**是对 M6.1.6 的更正**）

M6.1.6 在其唯一允许的修复轮内把 `is None` 改成 `not prepared`
（其 §3 第 2 条，标注 `M6.1.6 review A1-1`）。**该修改是错的，本轮撤销**
（`runner.py:627-646`），两条理由都是结构性的：

1. `not prepared` 会在 **runner 的门内**执行**应用方控制**的
   `__bool__` / `__len__`。**门内跑外来代码**正是本项目已两度付出代价的
   那一类；一个 `__bool__` 抛异常的对象会从治理检查内部掀翻整个生命周期。
2. 它破坏了该组件的**通用性**。`S0Runner` 是通用生命周期机：
   「有没有产出一个对象」是它的问题，「那个对象**有没有意义**」是应用的问题。
   falsy 的 prepared 对象（空元组／空映射／0）是合法的，原样转交 `compute`。

**证明方式（不是自陈）**：`tests/test_s0_runner.py:1834-1859` 参数化了
`[0, 0.0, "", (), {}, [], frozenset(), …]` 全部原样穿透且**同一性不变**
（`assert seen[0] is falsy`）；`:1864-1890` 另构造一个 `__bool__` 抛异常的
对象，证明 runner **从不读取其真值**——并且该证明覆盖**三个**转交点
（`compute`、渲染器、写后验证器：`:2117` 的
`test_post_write_verifier_receives_a_falsy_prepared_object_too`）。

**附带（同一条设计规则的第三面）**：`render_report` 现为两参
`(result, prepared)`，**无 arity shim**，由
`tests/test_s0_runner.py:2284-2291` 逐字钉住源码
（`assert "d.render_report(result, prepared)" in source` 且
`assert "d.render_report(result)" not in source`）。
理由不是风格：`RunnerDeps` 在 `prepare_compute()` 运行**之前**就已构造完毕，
故单参渲染器**只能**在渲染时自行去重新推导本次运行的授权身份——
而那个来源已经被本次运行自己的 `RUN_STARTED` 追加移动过了。
**那就是 §1.3 的缺陷形状**。单参渲染器现在响亮失败
（`TypeError` → Stage-E run failure），不被可选参数悄悄容纳。

---

## 2. 本轮**未**闭合的（分辨率必须保持，不得合并陈述）

> 下列各条是**不同的对象**。把其中任意两条写成同一件事，
> 就是本项目已多次付出代价的那类过度声明。

| 对象 | 本轮状态 | 依据 |
|---|---|---|
| Stage E 字节保真 | **CLOSED** | §1.1 |
| 发布判定的磁盘化（`governance.*` ＋ `sealed_files` 两轴） | **CLOSED** | §1.2 |
| 治理数据的曝光前单源 | **CLOSED** | §1.3 |
| 通用性回退（`prepared is None`／两参渲染器） | **CLOSED** | §1.4 |
| **F-1 整体** | **PARTIAL** | §2.1 |
| **F-2 整体** | **PARTIAL**，本轮**无变化** | §2.2 |

### 2.1 F-1 整体 —— PARTIAL（原因具名，S3 对当前字节复核）

prepared 对象 `_PreparedExecutionInput`（`scripts/s0_real_run.py:2250-2309`）
**仍不是**完全物化的执行计划：

1. `config.regime_of` / `config.vol_axis_of` **仍是 CALLABLES**
   （`src/itsf/contracts.py:449-450`，注释即 `Callable[[date_str], str]`）。
   行为不可快照——`__closure__` cells／`__code__`／`__globals__` 均可重绑。
   **物化这两个 callable 需要 DR-2 的已裁词表**，其中 `vol_na` 第四层的处理
   **明确未裁**。
2. `methods.spread_cost.adverse_slippage_ticks` **仍是 `MappingProxyType`**
   （`src/itsf/contracts.py:214-219`），即其作者可能仍持有后备 dict 的**活视图**。
   **冻结 tick 取值需要一条本里程碑不得作出的裁决**（与 E-6 同一面）。

**必须防止的一处误读，本轮显式排除**：本轮新增的
`prepared.snapshot` **也是** `MappingProxyType`，但它**不是**上面那条 PARTIAL。
它包的是 `prepare` 内部当场取的**私有副本**（`s0_real_run.py:2539` `snap = dict(snapshot)`），
**无第三方持有其后备 dict**，故它是**真正物化的**。
钉子：`tests/test_m6_chain.py:2406-2414`
（`test_m617_prepared_carries_an_immutable_pre_exposure_snapshot`）。

**因此**：本轮关闭的是**生命周期与字节**的洞，**不是** F-1 架构要求的
「完全物化的执行计划」。F-1 整体维持 `PARTIAL + ENGINEERING_REQUIRED`。

### 2.2 F-2 整体 —— PARTIAL，本轮**无变化**

本轮**没有**触碰叶／token 证据系统。**该主张有字节证据，不是自陈**：

- `src/itsf/s0/evidence.py` 现值 `676fbcd1ae0ac2a9`，与 M6.1.4-R2／M6.1.6
  收口值**逐位相同**（S3 复算）；
- `src/itsf/s0/dataset.py`（`8e12d35043c0110d`）与 `src/itsf/s0/context.py`
  （`e022cd1a012a0dd8`）**根本不在本工作树的改动集内**；
- `tests/test_s0_evidence.py` 亦不在改动集内。

叶／token 证据系统的分类**维持 M6.1.6 所定的 LEGACY DIAGNOSTIC**，
**不是** release certificate。本轮的磁盘证明**不替代**、也**不缩小**
F-2 的未闭合面：它证的是「封存集的字节等于其自陈」，
不是「那些字节**说的内容**对」——后者是
`report.validate_sealed_files` 的问题，`output_proof` 的模块文档明写此界。

---

## 3. 对 M6.1.6 历史记录的更正（**已在原文件就地批注，未删除其主张**）

M6.1.6 宣布了**两条** CLOSED。本轮把它们**双双**标为
**历史性临时（HISTORICALLY PROVISIONAL）且随后被 M6.1.7 REOPENED**。
更正**以批注方式落在 `CODEX_REVIEW_PACKET_M6_1_6.md` 原文旁**，
**原主张一字未删**——本项目不重写历史，只保证读者不会带着一个错误的
「CLOSED 是什么意思」离开。

| M6.1.6 的 CLOSED | 本轮判定 | 理由 |
|---|---|---|
| §1.2 治理 **OUTPUT-PROOF 切片** | **REOPENED → 由 M6.1.7 §1.2 以更强形态重新闭合** | 其判定对象是**内存 `dict`**。在它说「通过」的同时，磁盘上 10 个封存工件里 **9 个**的 `sha256` 与 `bytes` 皆与自陈不符（§1.1）。**旧的 CLOSED 不是错的陈述，而是一句比读者以为的弱得多的陈述。** |
| §1.1 prepared **LIFECYCLE 接缝** | **PARTIALLY REOPENED**：其 config 生命周期部分**成立**；其 fail-closed 措辞与覆盖范围**已被更正** | (a) 其 `if not prepared` 一条被 M6.1.7 §1.4 判为**错误并撤销**；(b) 更实质：该接缝**没有**把**曝光前 registry 快照**纳入 prepared 对象，故 `compute` 仍在 `RUN_STARTED` **之后**重读 registry，`registry_sequence_snapshot` 仍会封存 **N＋1**（§1.3）。**「生命周期接缝已闭合」当时读起来比其实际覆盖面宽。** |

另有两条 M6.1.6 自陈的登记项，本轮状态更新（同样就地批注）：

- M6.1.6 §4「DEFERRED —— CRLF 转译造成同一工件两个摘要」：
  **本轮已闭合**（§1.1）。M6.1.6 对该缺陷的登记**是准确的**，
  且其「必须在任何真实 S0 授权之前处置」的判断**已被本轮兑现**。
- M6.1.6 §5.2「未接线的 `governance_context` 是 SKIP，不是 fail-closed」：
  **部分仍然成立**。`s0_real_run.py:1100` 仍是 `if governance_context is not None:`
  ——**PRE-WRITE 屏（screen）**未接线仍是静默跳过。
  但**发布判定**已变为 fail-closed：`post_write_verify` 未接线在
  **曝光前**即拒绝（`runner.py:615-621`），与 `prepare_compute` /
  `pre_exposure_recheck` 同例。**M6.1.6 登记的那条「同一轮内两条接缝答案相反」
  因此缩小到了「屏 vs 判定」，而不是消失。**

---

## 4. 本轮必须披露的限度（**不予掩盖**）

### 4.1 `sealed_files` 的声明**未被绑定到报告之外的任何权威**

Q2 证明的是 **声明 == 磁盘**，**不是** 声明 == 渲染器本意。
一个同时改写工件与 `S0_REPORT.json` 内对应 manifest 条目的篡改者，
会得到一对**自洽**的东西，**Q2 单独无法把它与诚实的一对区分开**。
能抓住它的是：(a) Q1——其期望侧从不来自报告，只要篡改触及 `governance.*`；
(b) Stage-F 的 append-only 链（`manifest.jsonl`，写入时即由 runner 哈希），
只要篡改不触及 `governance.*`。
本模块是那一对里的**一条轴，不是替代品**。
`sealed_files` 无任何字段把它绑到报告之外，且**无授权新增此类字段**，
故每一次跑过该轴的证明都**显式披露**
`governance_proof_partial:sealed_file_declaration_not_bound_to_an_external_authority`
（`output_proof.py:302-303`；测试 `test_the_sealed_set_partial_disappears_when_that_axis_did_not_run`），
不让 `ok=True` 被读成更强的主张。

### 4.2 写后验证**必然在曝光边界之后**——一次磁盘封存拒绝会**烧掉 trial**

**磁盘字节**的验证需要磁盘上已有字节，故必然在写之后，
也就是在 `RUN_STARTED` 之后。**因此一次拒绝是
Stage-E RUN failure：trial id 已消耗，收不回来。**
这是被明确接受的取舍，也是拒绝路径上**什么都不删除**的原因
（工件、失败报告、封存的 incident 明细全部保留待裁）。
**本 packet 不把这条写成「已缓解」。** 它是本设计的成本。

> **【措辞更正 —— 复核员 L-3，S3 接受】** 本节原写
> 「**只有接线**可以在曝光前被检查」。**那是过强的说法，已更正。**
> 准确的划分是：**磁盘字节**的验证确实不可能前移，
> 但**期望侧整个是曝光前可算的**——`SourceContext` 的每一项
> （授权快照、`guards.FROZEN_HASHES` 权威、冻结文件的磁盘重哈希、
> engineering-seed 出处戳记）在 `RUN_STARTED` 之前就已完全确定。
> **两者被打包进同一个后置动作，是实现选择，不是逻辑必然。**
> 其后果具体而不抽象：**一个在曝光边界之前就已被完全决定的缺陷
> （例如一个结构上不可用的 context），今天仍然要烧掉一个 trial 才会被说出来。**
> 本轮不重排该时序（超出四条闭合的范围），但**不再用「只有接线可查」
> 这句话把它说成必然**。

**与 §9.2 第 2 条合读**：若 `seal_check` 门（位于禁读路径下，复核员与 S3
均无法验证）**不**覆盖冻结文件的字节级篡改，则该输入也落入本条，
**L-3 对它的严重度相应上升**。

### 4.3 治理证明结果在封存字节里**仍无留痕**

M6.1.6 §5.2 登记过：`proof.partial` 被算出后随即丢弃，未写入任何工件。
**本轮仍然如此**——`post_write_verify` 只把摘要放进返回的 detail 字符串
（`s0_real_run.py:2450-2453`），而 detail 只在**失败**路径进入
`RUN_FAILURE_REPORT`。成功运行的封存字节里，**「本次做过磁盘证明、
且它自陈了若干缺口」这一事实无从查证**。扩展已冻结的报告 schema
需要一条本里程碑不得作出的裁决，故此处**披露而非静默补齐**。

### 4.4 本轮**新发现**的残留：字节保真只覆盖**渲染器工件** —— **四处：两处已闭，两处具名延期**

**S3 在核对时发现，不在指派清单上；主代理随后闭合了其 lease 内的那一半。
两半的处置不同，此处分开陈述，不合并成一句「已处理」。**

Stage E 的写路径已全面 `write_bytes`，`runner.py:323`／`:465`
（`INCIDENT_*.md`／`HALF_TRANSITION.md`）亦已加 `newline="\n"`。
**S3 最初枚举了三处，那个枚举不完整**——复核员发现了第四处（L-2）。
**四处**的现状如下（S3 于最终树逐处重新核对字节）：

| # | 位置 | 工件 | 状态 |
|---|---|---|---|
| 1 | `scripts/s0_real_run.py:2647-2651`（`post_run_started_hook`） | `REGISTRY_AFTER_RUN_STARTED.json`（`indent=1`，多行） | **已闭合**——现为 `encoding="utf-8", newline="\n"` |
| 2 | `scripts/s0_real_run.py:2639-2641`（`make_snapshot_control` 的 Stage-A 门） | **`AUTHORIZATION_SNAPSHOT.json`**（`indent=1`，多行）——**S3 原枚举遗漏，复核员 L-2 补出** | **已闭合**——现为 `encoding="utf-8", newline="\n"`。它落在 **attempt 目录**、从不落在运行目录，故对封存集无影响 |
| 3 | `src/itsf/s0/runinfra.py:1089` | `RUN_FAILURE_REPORT.md` / `PRE_RUN_ATTEMPT_FAILURE.md` | **OPEN，具名延期** |
| 4 | `src/itsf/s0/runinfra.py:1090-1093` | 同名 `.json`（`indent=2`，多行） | **OPEN，具名延期** |

**如实记录 S3 自身的一处不完整**：§4.4 原写「三处」。那是一次**枚举**，
而枚举正是最容易漏项的证据形态——S3 当时按 `runner.py` / `runinfra.py`
两个文件搜索写路径，`make_snapshot_control` 的那一处在
`scripts/s0_real_run.py` 内、且写的是 attempt 目录，未被覆盖。
**这条更正归复核员。**

**已闭合的那一处，其理由必须原样记录，因为它不是缺陷修复**：
`REGISTRY_AFTER_RUN_STARTED.json` **从未进入 `sealed_files`，
因此从来没有过「一个工件两个摘要」的缺陷**。改它的理由是
**「运行目录的字节是被决定的」这条规则不应带一个读者必须记住的例外**。
S3 复核了其安全性：全库检索显示**没有任何测试钉住该文件的字节或哈希**
——`tests/test_s0_runner.py:1508` 经 `read_text("utf-8")` 读取（通用换行，
对行尾不敏感），`tests/test_s0_output_proof.py:94` 只用到其**文件名**。

**OPEN 的两处（＃3／＃4，同一个函数）是 DELIBERATELY DEFERRED，
不是疏漏，也不是已闭合。**
理由（主代理判断，S3 复核其事实基础并登记）：

1. **`src/itsf/s0/runinfra.py` 在 M6.1.7 的每一条 lease 之外。**
   在收口时扩大改动面，其风险**大于**该残留本身。
   S3 复核：该文件 sha256 为 `b6cd12d3158ba2a7…`，
   **与授权包环境锁内的值逐位相同**，即本里程碑确实一字节未动。
2. **它不可能与磁盘证明相互作用。** 这两个工件**只在失败路径写出**，
   而磁盘证明跑在**成功路径**上、且在 Stage E 完成之前——
   两者在时序上不相交，故它不会把一个未声明文件放进运行目录、
   也就不会触发 §4.2 的「烧掉 trial」面。

**登记口径**：`RUN_FAILURE_REPORT.{md,json}` 的字节**仍依赖运行所在平台**。
这是一条 **OPEN、具名、经理由的延期项**，
**不得**在后续文档中被读作「M6.1.7 已把字节保真做全」。

---

## 5. 行尾一致性 —— **披露式观察，本轮不作机械改写**

三份历史文档的字节被测试与既有评审包引用，**本轮一个字节都不动**。
但主代理给出的「三份 CRLF-heavy 文件」这一描述**经 S3 实测不成立**，
在此更正（这正是本项目要求逐数复算的理由）：

| 文件 | CRLF 行 | 纯 LF 行 | 字节 | 实况 |
|---|---|---|---|---|
| `M6_1_4_LEAF_LINEAGE_MATRIX.md` | **748** | 0 | 48,618 | **确为全 CRLF** |
| `PHASE_D_COUNTEREXAMPLE_EVIDENCE.md` | **0** | 123 | 12,343 | **全 LF——描述有误** |
| `B0_SOURCE_LINEAGE_MATRIX.md` | **0** | 441 | 87,934 | **全 LF——描述有误** |

**全库实测**（**59** 份：45 份根目录 `*.md` ＋ 14 份 `ops/**/*.md`；
**S3 首次测得 58，是因为当时本文件尚未落盘——一个把自己算漏了的计数，
按 L-8 同一原则更正并披露**）：**恰有 4 份**含 CRLF，
且**没有一份是混合行尾**：

```
DATA_QA_ADDENDUM.md            CRLF=464   LF_only=0
DATA_QA_REPORT.md              CRLF=18    LF_only=0
M6_1_4_LEAF_LINEAGE_MATRIX.md  CRLF=748   LF_only=0
S0_INPUT_PREFLIGHT_REPORT.md   CRLF=202   LF_only=0
```

`.gitattributes` 为 `* -text`（S3 实读），即 **git 不做任何行尾归一化**——
上述字节就是仓库字节，也是 checkout 后的字节。
`S0_INPUT_PREFLIGHT_REPORT.md` 的 sha256 被授权包 §0 环境锁钉住
（`ea287f85638c0afdac…`，S3 复算一致），**更不可改写**。

**`M6_1_4_LEAF_LINEAGE_MATRIX.md` 的非惰性（S3 逐行复验，§9 块原样保留）**：

- `tests/test_s0_evidence.py:2371-2372` 把该文件路径钉为 `_MATRIX_PATH`；
- `:2373` `_FENCE = "```" + "leafregistry"`；
- `:2381` `text.index(_FENCE)` 取**第一处**围栏标记——故在 §9 **之前**任何位置
  出现该标记字面量都会把解析窗口挪到错误位置；
- `:2388` 断言每行**恰 6 列**（tab 分隔）；
- `:2418-2419` `test_the_matrix_declares_exactly_121_leaf_rows`。

**S3 独立复算该块**：文件中该围栏字面量**出现 1 次**；块内非空行
**121** 行；观测到的列数集合**恰为 `{6}`**。**与测试所断言的一致，
该块本轮一字节未改。**
**落盘后复验**：`tests/test_s0_evidence.py` **324 passed / 0 failed**
（S3 于本车道全部编辑完成后重跑），该文件 sha256 `50ca849834bb3f28…`
与 baseline 逐位相同。
（附注：解析器用 `read_text(encoding="utf-8")`，Python 文本模式做通用换行
归一，故该文件的 CRLF 对**该解析器**无害；不可改写的理由是**哈希引用**，
不是解析器。）

---

## 6. 文件／车道（lease）地图

| 文件 | 车道 | 本轮状态 |
|---|---|---|
| `src/itsf/s0/runner.py` | 工程（S1） | modified（字节保真、写后验证接缝、`is None` 回退、两参渲染） |
| `src/itsf/s0/output_proof.py` | 工程 | modified（磁盘判定、毒丸、`DraftScreen`、Q2 封存集轴） |
| `scripts/s0_real_run.py` | 工程 | modified（快照单源、屏／判定分离、`prepare_for_run` 接线） |
| `tests/test_s0_runner.py` | 工程（S1，**S3 阅读期间仍在编辑**） | modified |
| `tests/test_s0_output_proof.py` | 工程 | modified |
| `tests/test_m6_chain.py` | 工程 | modified |
| **`CODEX_REVIEW_PACKET_M6_1_7.md`** | **治理（S3）** | **本轮新建** |
| **`CODEX_REVIEW_PACKET_M6_1_6.md`** | **治理（S3）** | **本轮批注**（§3；不删除任何原主张） |
| **`S0_REAL_RUN_AUTHORIZATION_PACKET.md`** | **治理（S3）** | **本轮更新** §0 环境锁 ＋ HEAD／commit 距离／工作树事实 |
| **`DECISION_REQUIRED_READY_SUPERSESSION.md`** | **治理（S3）** | **本轮新增 §5.2**（队列长度不变 ＋ 两条陈旧事实更正） |
| `ops/TRIAL_REGISTRY.md` / `EXPOSURE_LEDGER.md` / `runs/` / 冻结件 | — | **未触碰**（哈希复算逐位不变） |
| `M6_1_4_LEAF_LINEAGE_MATRIX.md` / `PHASE_D_COUNTEREXAMPLE_EVIDENCE.md` / `B0_SOURCE_LINEAGE_MATRIX.md` | — | **未触碰**（§5） |

---

## 7. 测试计数移动

| 量 | baseline `185e47f7` | 当前工作树（修复轮后） | Δ |
|---|---|---|---|
| `pytest tests --collect-only` 全量 | **2146** | **2205** | **+59** |
| `tests/test_s0_runner.py` | 110 | 132 | +22 |
| `tests/test_s0_output_proof.py` | 34 | 60 | +26 |
| `tests/test_m6_chain.py` | 172 | **183** | **+11** |
| 三文件合计 | 316 | **375** | **+59** |
| `MIN_COLLECTED_TESTS` | 2146 | **2205** | **+59** |

修复轮把 `test_m6_chain.py` 由 182 加到 **183**——新增的一条就是 §1.3 的
行为证据（L-4，见 §9.3）。三文件 Δ 之和仍**恰等于**全量 Δ，
即新增测试**全部**落在这三个文件内，其余 26 份测试文件计数未动。

**测法（`S3_MEASURED`）**：baseline 侧用 `git archive 185e47f7` 导出到隔离目录后
在同一解释器下 `--collect-only`，**不是**读转录数字。

**一条如实记录的时序事实（不隐去）**：S3 在本轮**第一次**复算时测到
`MIN_COLLECTED_TESTS` 仍为 **2146**，而实测 collected 为 2204——
即该「套件是否被静音」探测器当时有 **58 个测试的松弛量**。
S3 在收口前**重新复算**（本车道对所引每一个数字在最后重读一次的既定纪律），
测到工程车道已把它上调到 2204；修复轮后再次复算为 **2205**，
测试双钉同步为 2205。
**该观察因此已被处置，本 packet 不将其列为待办**；
记录在此，是因为**「我第一次看到的值」与「我落笔时的值」不同**，
而本项目要求这类差异被说出来，而不是被悄悄抹平成一致。

---

## 8. Codex 复审入口 —— **请在这几处用力**

> 以下每条都给出「若我错了，你会在哪一行看见」。

**8.1 §1.3 的比较是否真的没有变空洞。**
`_expected_governance(snapshot)`（`s0_real_run.py:2194-2230`）从快照取 SEQUENCE、
从实时 registry 字节重读 COMMIT。请核：这条比较在**什么条件下会退化成
「快照 vs 快照」**？特别地——`snapshot is None` 的分支（`:2211-2212`）仍走
`len(parse_registry_events(text))`，其存在理由是「非运行调用方（渲染器直测）」。
**请确认生产路径不可能落入该分支**（S3 已核实 `:2414` 恒传
`prepared.snapshot`，且 `render_report_with_governance_proof` 以
`type(prepared) is not _PreparedExecutionInput` 硬拒）；
若能构造出一条落入 `None` 分支的生产路径，本轮 §1.3 的闭合即不成立。

**8.2 写后验证拒绝会烧 trial（§4.2）——这是设计还是应被推翻的取舍？**
S3 认为不可避免（磁盘字节无法在成为磁盘字节之前被验证），但这是一条
**要求 Codex 给立场**的治理判断，不是工程细节。相关：本轮把接线检查放在
曝光前（`runner.py:615-621`），把验证放在 `_record_artifacts` **之前**
（`:748` 早于 `:764`），使未经证明的工件不会进入 append-only 链——
请核对这个顺序是否真的成立。

**8.3 Q2 的域是否真的来自目录而非 manifest。**
`_verify_sealed_set`（`output_proof.py:726-772`）的 `disk_checks_required`
＝ `3 * len(declared)`，**由 manifest 定尺寸**；作者宣称另一侧
（`Path.iterdir()` 的 extra-file 检查）补上了这个洞。
**请独立构造「清空 `sealed_files`」这一变异**，确认它产出的是
`manifest_missing` ＋ 满目录的 `disk_extra_file`，而**不是**一次
`disk_checks_required == 0` 的静默通过。（`ok` 另要求
`disk_required > 0`，见 `:995-997`——请确认这条不能被绕过。）

**8.4 `infrastructure_files` 的生产声明只有两项，而模块文档列了四个名字。**
生产传 `("manifest.jsonl", "REGISTRY_AFTER_RUN_STARTED.json")`
（`s0_real_run.py:2443-2444`），模块文档（`output_proof.py:129-134`）另提
`HALF_TRANSITION.md` 与 `INCIDENT_*.md`。S3 循代码认为成功路径上后两者不存在
（Stage C/D 失败即中止，Stage E 不会跑到），故不会误报 extra；
**但这是 S3 的推理，不是实测**，且**误报的代价是烧掉 trial**（§4.2）。
另注：`INCIDENT_*.md` 是**通配名**，即使声明也无法用一个字面名覆盖。
请把这条当作「运行目录里出现任何一个未声明文件即 = 一次被烧掉的 trial」
的风险面来审。

**8.5 §1.1 的 9/10 是 `S3_DERIVED` 而非 `S3_MEASURED`；
并且——磁盘封存验证器至今从未在真实路径上执行过一次。**

S3 实测了转译机制、`S0_REPORT.md` 的 425→430 字节偏移、以及
`sealed_files` 的成员构成；**未**实测真实运行下 8 份 JSONL 的记录数
（无真实运行可测，且伪造一次不是选项）。若复审员认为该数字必须为
`MEASURED` 方可采信，请指明可接受的替代取证方式。

**同一段证据缺口，还有更重的一面，在此与 9/10 并列陈述**：
生产今日在 `prepare` 处即 fail closed——`_approved_injectables()`
（`scripts/s0_real_run.py:1141-1148`）**返回 `None`**，这是刻意的姿态。
**因此 §1.2 的写后磁盘验证器虽然已接线（且未接线会在曝光前拒绝），
但它从未在一条真实路径上跑过。**
它的**全部**证据都来自合成边界：合成的运行目录、合成的
`S0_REPORT.json`、合成的 `sealed_files`。
**这不推翻 §1.2 的结构性主张**（毒丸、`actual_source == "file"` 强制、
`DraftScreen` 不可当验收——这些是类型与控制流层面的事实，不依赖执行），
**但它确实意味着**：本 packet 里凡是形如「磁盘证明会抓住 X」的句子，
其证据级别都是**合成的**，不是运行过的。
第一次真实 S0 将同时是这个验证器的第一次真实执行——
而按 §4.2，它那一次的拒绝会烧掉 trial。**请把这两条一起审。**

**8.8 `_expected_governance` 在 Stage E 仍读 registry —— 这是有意为之，
但它贴着本里程碑指令的字面边界，主代理明确要求被推敲，S3 转达其原话要点。**

指令是「`compute` 的治理数据只从 prepared 快照构建，`RUN_STARTED` 之后
不得重读 registry」。**`compute` 严格合规**，且由 AST 钉死：
`tests/test_m6_chain.py:2428-2444`
（`test_m617_compute_never_reads_the_registry_after_run_started`）断言
`REGISTRY` 不在其 `ast.Name` 集合内、`parse_registry_events` 与
`find_authorization_event` 均不在其 `ast.Call` 集合内，
并正向断言 `"prepared.snapshot" in src`。**S3 已逐行核实该测试在场且如上。**

**但 `_expected_governance(snapshot)`（`s0_real_run.py:2194-2230`）
在 Stage E 仍然读 registry**——**故意的**，用途是重新推导 authorized
COMMIT 并在其与快照不一致时拒绝封存。

**【L-6：对主代理原理由的更正，明说是更正】**
主代理原先给的理由是「若不重读，五个治理键里**有两个**会变成自己跟自己比」。
**复核员重新度量后证明该数字过于乐观，主代理已接受并已改写源码 docstring。**
S3 逐键复算，确认复核员的数字：

| 治理键 | actual（`compute`）来源 | expected（`_expected_governance`）来源 | 是否空洞 |
|---|---|---|---|
| `trial_id` | `TRIAL_ID` 模块常量 | **同一个**常量 | **空洞** |
| `engineering_seed` | `ENGINEERING_SEED` 常量 | **同一个**常量 | **空洞** |
| `frozen_hashes` | `dict(_g.FROZEN_HASHES)` | **同一个**进程内对象 | **空洞** |
| `registry_sequence_snapshot` | `snap["event_sequence"]` | **同一个**快照 | **空洞（M6.1.7 之后才变成这样）** |
| `authorized_commit` | `snap["authorized_commit"]` | **实时 registry 字节重读** | **唯一非空洞** |

→ **五个里已经有四个是空洞的；重读只保住了一个。** 不是两个。

**因此该重读的真正价值不在「保住比较内容」，而在那个 `raise` 本身**：
它是一个 **RUN 中途重新授权的检测器**，而且是**唯一**的一个。
`pre_exposure_recheck` 在结构上覆盖不了它——它跑在 `RUN_STARTED` **之前**
（`_atomic_run_start` 内），此后到封存之间的窗口无人看守。
**故 §8.8 原先提出的「把 commit 稳定性检查搬到 `pre_exposure_recheck` 一侧」
这个备选方案会严格地丢失检测能力，不是等价搬移。**
另需明确：`find_authorization_event`（`scripts/s0_real_run.py:293-311`）
只认 **`RUN_AUTHORIZED`** 行，而本次运行自己追加的是 **`RUN_STARTED`** 行，
**故这条检测器不会被本次运行自己触发**（S3 核实其实现）。

**请复审员／Codex 回答的问题（主代理自陈不是合适的裁决方）**：
在「四空洞 ＋ 一检测器」这一被更正后的图景下，这条线仍然划得对吗？
**S3 立场**：S3 复核了全部事实基础（AST 测试在场、`compute` 确实不读
registry、`_expected_governance` 确实读、四／一的空洞划分、
`RUN_STARTED ≠ RUN_AUTHORIZED`），**但不对这条线本身表态**——
它是治理设计取舍，不是可由只读车道复算的事实。
**如实记录**：在这一条上，**复核员为该代码给出的理由比主代理原先给的更强**。

> **【M6.1.8 更新：本项已由 Aaron 裁定，不再是开放问题，2026-08-09】**
> 裁定权威＝**Aaron 的 M6.1.8 执行提示词 D.4**（非 Fable、非 Codex、
> 非任何只读车道）。所定表述为：
> **「曝光后不得从实时 registry 获取研究执行输入；允许只读、只否决的
> 授权新鲜度检查。」**
> 按此，`_expected_governance` 的那次重读**合规**——它不向执行提供任何输入，
> 只在 commit 与运行前快照不一致时**否决**封存。**代码维持原样。**
> 上面那句「请复审员／Codex 回答的问题」现应读作：请 Codex 复核**代码是否
> 确实符合该已裁定的不变量**，而**不是**重新裁决这条线本身。
> 详见 `CODEX_REVIEW_PACKET_M6_1_8.md` §4。

**8.6 §3 的两条 REOPENED 是否措辞得当。**
S3 的判断是：M6.1.6 的两条 CLOSED **不是假陈述**，而是**比读者会以为的弱得多的
陈述**。若 Codex 认为其中任一应记为**误报的 CLOSED**（更重的定性），
请明说——S3 不自行升格。

**8.7 本 packet 引用的工程侧字节在 S3 工作期间移动了四次，这本身是一条数据。**
`scripts/s0_real_run.py` 在 S3 的同一次会话内被观测到**四个**取值
（S3 逐次实测）：`9565c930` → `a86515c0` → `ef03cc3a` → **`131b0dd1`**；
`MIN_COLLECTED_TESTS` 由 2146 → 2204 → **2205**；
第四处文本模式写（L-2）、L-4 行为测试、以及两处 `newline="\n"`
都是在这期间陆续落地的。
本 packet 的所有哈希与行号**已在最终收口时逐一重读**（见 §0 与 §6），
但**该重读没有、也不可能给出「此后不再变」的保证**——
**这条警告同样适用于向 S3 转达数值的任何一方：主代理与复核员都不例外。**
本轮的实际做法是：**凡他人交回的数值，S3 一律不转录，一律自行重测**
（本节这串取值就是这样得到的）。
**请复审员以 M6.1.7 形成 commit 后的字节为准重新复算**，
并把本 packet 的 §0／§6／§7 三处数字当作**需要被重新确认的自报数据**。

---

## 9. 独立只读复核结果（`M6_1_7_REVIEW=PASS`）

**判定：`M6_1_7_REVIEW=PASS`，无 in-scope High／Medium。**
唯一的 High（**H-1**）为 **out-of-scope ＋ pre-existing at baseline**，
已提到本文件最前（见顶部专节），不阻断本次 commit。

### 9.1 正面结果 —— **按其被建立的强度陈述**

- **十一项验收项全部 OK，且是对真实 `S0Runner` 执行**得出的，
  不是读代码得出的。
- **九个变异，每一个都至少被一个测试杀死。** 其中两个值得单列：
  - 把 `write_bytes` 改回 `write_text` —— **6 个测试**同时红；
  - 把 `prepared is None` 改回 `not prepared` —— **10 个测试**同时红。

> **为什么本 packet 给变异证据比给断言数更多篇幅**：断言数只说明
> 「写了多少检查」，变异存活率说明「这些检查**抓得住什么**」。
> 本项目已经吃过一次「结构上不可能失败的检查」
> （`evidence.py` 的硬编码 compared-count，见 §1.2 F-b）。
> **九个变异九个被杀，是本轮质量证据里最重的一条，
> 比 2205 passed 更重。**

### 9.2 复核员**无法**验证的三件事 —— 记为 **PASS 的边界**，不是工作的缺口

1. **真实运行下的 9/10 计数。** 机制、`S0_REPORT.md` 的 425→430 偏移、
   `sealed_files` 的成员构成**均已确认**；**计数本身**维持 `S3_DERIVED`
   （§1.1、§8.5）。
2. **`seal_check` 门的行为无法确定。** 该工具位于
   `C:\Users\Aaron\quant-data` 之下，**复核员被禁止读取该路径**
   （S3 同样受此禁令，本轮从未读取）。**因此「一次冻结文件的字节级篡改
   是否会在曝光前被抓住」是未定的**；若 `seal_check` 不覆盖该输入，
   **L-3 对该输入的严重度上升**。
3. **`prepare` 之后、真实数据路径上的任何行为。**
   生产今日在 `prepare` 处 fail closed（`_approved_injectables()` 返回
   `None`），故磁盘验证器、H-1、以及本 packet 中一切「运行时会怎样」的
   陈述，其证据级别都是**合成的**。

### 9.3 其余 Lows —— **已披露、在范围内、未修**（逐条含理由）

| # | 内容 | 为何未修 |
|---|---|---|
| **L-1** | `render_s0_report` 的 `expected_governance=None` 回退分支（`s0_real_run.py:913`）仍返回 **N＋1** 值 | **生产不可达**：唯一调用方恒传快照（`:2414`），且对非 `_PreparedExecutionInput` 的 prepared 硬拒。**且即便到达也是 fail-closed**：结果是一次契约违规 ＋ 烧掉的 trial，**绝不会是一次错误的封存**。改动它会扩大范围而不改变任何可达行为 |
| **L-3** | 期望侧**整个**可在曝光前算出，却在写后才验证——故一个**在边界之前就已完全确定**的缺陷仍会烧掉 trial | 重排验证时序超出本轮四条闭合。**但本 packet 的措辞须软化**：§4.2 原写「只有接线可以在曝光前被检查」，这是**过强**的说法。准确的说法是：**磁盘字节**的验证必然在写后，但**期望侧**并不是；两者被打包在同一个后置动作里，是实现选择，不是逻辑必然 |
| **L-5** | `runs/` 位于**正在同步的 OneDrive 树内**。磁盘证明要求运行目录内容**恰好等于**声明集，故**任何**未声明条目——`desktop.ini`、`*.tmp`、同步器建的子目录——都是 `disk_extra_file` → **烧掉 trial** | **这需要 Aaron 的一条裁决，不是工程改动**：要么把 `runs/` 移出同步树，要么裁定一份同步器工件白名单（而白名单本身会削弱「恰好等于」这条不变式）。**在第一次真实 S0 之前必须处置**，与 H-1 同列 |
| **L-7** | `render_report` 无**曝光前**的 arity 探针：单参渲染器要到 Stage E 才 `TypeError`，届时 trial 已烧 | **两方立场并存，本 packet 不作解决**。主代理：无 shim 是刻意的，探针会诱使人以为 arity 已被处理；复核员：这是**设计偏好**而非缺陷，但其本人会**反向决定**（加一个纯读签名的 pre-exposure 探针，不调用渲染器）。**两条都记录，不裁决** |

**L-2（第四处文本模式写）与 L-4（`compute` 缺行为证据）已在修复轮闭合**，
分别见 §4.4 与 §1.3／§7。

**L-4 的性质值得单说**：复核员指出 §1.3 的 `compute` 侧当时**只有一个 AST
测试**在钉——把 registry 读回去，**只有那一个测试会死**，因为**没有任何东西
断言 `compute` 实际盖了什么章**。修复轮新增
`test_m617_compute_stamps_the_snapshot_sequence_not_the_live_registry`
（`tests/test_m6_chain.py:2537`）：它把 `mod.REGISTRY` 换成
`read_text`／`read_bytes`／`open` **全部抛异常**的对象——即读取变成**不可能**
而非「不该」——再断言封存的 `registry_sequence_snapshot` 等于快照值。
**C3 因此同时具备结构证据（AST）与行为证据（stamp），不再是单点。**

---

## 10. Aaron 裁决队列 —— **本里程碑新增零项**

**S3 已对 `DECISION_REQUIRED_READY_SUPERSESSION.md` §5.1 的
「待 Aaron 裁决的完整集合恰为两组」逐条复验，该陈述在 M6.1.7 后
**仍然成立**：**

1. **DR-1 … DR-8**（八个方法家族，`DECISION_REQUIRED_M6_1.md`；DR-8 ＝ DR-M6-H）；
2. **READY supersession**（Option A/B/C，该文件本身）。

**没有第三组。M6.1.7 向该「方法裁决」队列增加了 0 项。**

> **但这句话必须带一条限定，否则它会误导。**
> 「队列」在本项目里指的是**方法家族裁决**（DR-1…DR-8）＋ READY supersession。
> M6.1.7 确实没有向它加任何一项。**然而本轮产生了两条
> REAL-RUN READINESS 的处置项，它们不是方法裁决，却同样必须在
> 第一次真实 S0 之前被解决**：
>
> - **H-1**（见本文件最前）——**基线即存在，M6.1.7 范围外**，
>   故它**不是** M6.1.7 新增的任何东西；
> - **L-5**（`runs/` 位于同步中的 OneDrive 树内，§9.3）——**这一条不同：
>   它是 §1.2 的 Q2「声明集必须恰好等于运行目录实际内容」这条新不变式的
>   直接后果。基线没有这条检查，所以基线没有这个问题。**
>   **不把它算作 M6.1.7 的产物是不诚实的。**
>
> **S3 不裁定这两条是否构成「第三组」**——那是队列口径问题，
> 归 Aaron／Codex。S3 的职责是保证它们**被说出来**，
> 而不是被「队列长度不变」这句真话遮住。
本轮未新铸任何研究 DR 编号，未追加任何 registry 事件，
未触碰 EV-11／标签语义／方法裁决面（`dataset.py`、`context.py`、
`contracts.py`、`evidence.py` 的字节本轮**未改动**，见 §2.2）。

**D-4 的本轮登记：`DEFERRED_NOT_REQUESTED_FOR_M6.1.7`。**

- 含义：D-4（EV-11 五布尔 → 标签集 reducer 的冻结）**本里程碑既未推进、
  也未请求裁决**。它**不因本轮而进入队列**。
- **S3 明确不写的一件事**：本 packet **不主张** D-4「挂在 DR-1…DR-8 的某条伞下」。
  理由是实测——`CODEX_REVIEW_PACKET_M6_1_4.md:224` 把 D-4 标为
  「（DR 伞下·工程受阻）」，却**从未指名是哪一条 DR**；同一行又写
  「二选一，**均需 Aaron 一句裁决**」。**「挂在某伞下」与「需要 Aaron 一句裁决」
  这两句话不能同时为真而不指名那把伞。** S3 无权指定，也不猜测，
  故把 D-4 记为**本轮不请求**，把该措辞张力**原样交给 Codex／Aaron**。
- 与之相符的一处旧文：`DECISION_REQUIRED_READY_SUPERSESSION.md` §5.1 写
  「D-4 仍挂在既有 DR 伞下」——**同样未指名**。本轮在该文件新增的 §5.2
  只确认**队列长度不变**，**不复制**那句未指名的归属主张。

---

## 11. 本轮红线自查（本车道声明）

- **未修改**任何 `.py`、`ops/TRIAL_REGISTRY.md`、`EXPOSURE_LEDGER.md`、
  `runs/`、或任何 `guards.FROZEN_HASHES` 冻结件。
  **证据**：编辑前后逐一复算，registry `de63b3d6…b440`、
  exposure `39481343…bc9e6` 逐位不变；三份被改动的生产源
  （`131b0dd1…` / `b44306f8…` / `b43c0524…`，**修复轮后的最终重读值**）
  与三份测试文件的哈希（`710fdcf4…` / `eb1e753e…` / `256e14df…`）
  **由工程车道产生，S3 只读取，未写入**。
  `src/itsf/s0/runinfra.py` 仍为 `b6cd12d3…`（＝环境锁值，本里程碑一字节未动，
  即 §4.4 的延期项确实被延期了）。
- **未触碰** `M6_1_4_LEAF_LINEAGE_MATRIX.md`、`PHASE_D_COUNTEREXAMPLE_EVIDENCE.md`、
  `B0_SOURCE_LINEAGE_MATRIX.md` 三份文件的任何字节（§5）。
- **未读取** `C:\Users\Aaron\quant-data`；**未运行**真实 S0；
  未追加 registry 事件；未追加 READY 行；未建 tag；未提出任何授权请求。
  `real_s0_authorization: REAL_S0_NOT_AUTHORIZED` 原样保持。
- 本车道所有 markdown 写入均为 **LF**（落盘后逐文件复算行尾确认）。
- `git diff --check` 在本车道的编辑后仍为净（exit 0）。
