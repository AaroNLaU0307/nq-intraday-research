＃ 送审包 —— QROS-CF F01–F06 修复的**定向复审**

```ini
PACKET_TYPE=TARGETED_RE_REVIEW_OF_A_REPAIR（不是 A2，不是 Stage I，不解开任何 QROS 门）
REVIEW_ID=QROS-CF-F01-F06-REREVIEW-001
DELIVERY_STATUS=RETURNED
RETURNED_VERDICT=HOLD —— F04 CLOSED;F01/F02/F03/F05/F06 STILL_BLOCKING（GPT-6 Astra，fresh session，2026-09-07）
RETURNED_NOTE=本轮复审已归还,故按 test_artifacts_under_review_are_frozen 的指示从 ARTIFACTS_UNDER_REVIEW.json 撤销登记。第二轮修复见 tests/test_qros_cf_astra_round2.py。**归还不是通过**;最终认证由 Aaron 派发
COMPANION=ops/NEXT_HANDOFF.md（禁读清单载体，**必须同行**;已登记在 §0.3 与 ARTIFACTS_UNDER_REVIEW.json,强制件必须被钉住）
PREPARED_BY=Claude Opus 5，repair-builder seat —— **本席位写了被审的修复,不得自审通过**
FOR=GPT-6 Astra，fresh session —— 定向复审，仅 F01–F06
DECIDED_BY=Aaron —— **席位不裁定,也不代签**
REPAIR_COMMIT=f461f098a407ffc87dd0e2187c14ee4f4f00d1fd
HOLD_OF_RECORD=ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md
THREAT_VOCABULARY=ops/REVIEWER_CONTRACT.md（T1–T6）
REVIEWED_SET_UNCHANGED_SINCE=（由 ops/ARTIFACTS_UNDER_REVIEW.json 的 `unchanged_since` 承载，git 派生,不在本文键入）
THIS_PACKET_SHA256=（**不在此文件内**。送审文档无法自钉:把自身 hash 写进正文会产生新提交,新提交又改变 hash——2026-08-29 实测无不动点,见 tests/the_delivery_cannot_pin_itself。本包的 sha256 由 ops/ARTIFACTS_UNDER_REVIEW.json 中 `is_the_delivery_document: true` 那一条承载,并由 test_every_artifact_under_review_still_hashes_to_what_was_sent 每次运行核对。）
```

---

## 0. 受审集 —— **先逐字节核对,再开工**

对下表每一行重算 sha256 并比对。**不符即 STOP 并报告。**
聊天里贴过来的字节永远不是真相来源;请从磁盘读。

仓库文件另给 `repair commit` 与该提交处的字节 sha256。**git commit id 不能替代
声明的 sha256**:提交 id 证明历史,sha256 证明你手上这些字节。本席位已核对
worktree 字节与 `f461f09` 处的 blob 字节逐一相同(14/14),你应独立复核。

### 0.1 修复产物(role = reference,均在 `f461f098a407ffc87dd0e2187c14ee4f4f00d1fd`)

| sha256 | bytes | 路径 | 与哪条 finding 相关 |
|---|---|---|---|
| `e8e36d385cc9977791f5119c9ba54fb64bb97d34b03227af590ac8590cc49229` | `29311` | `src/itsf/execution_identity.py` | **F01**（`bytecode_report`）· **F02**（`startup_report`）· 两者接入 `seam_recheck` |
| `c06f10b8395b19e2d79943bb3c42794a3cac5652d51a78323a2022e30ea29354` | `25045` | `src/itsf/mc/registry_boundary.py` | **F06**（单次决策读 · `_compare_and_append` · `_AppendLock`） |
| `99cd38d5f41f6fc9733957311d95399b83713fed7784aa055136e890d5a8159a` | `10157` | `src/itsf/mc/owner_control.py` | **F05**（`owner_intent_lines` 意图扫描） |
| `e41093307a6d015849fc68aef59b562df762ef6aea1d85508ab2dfff31265be7` | `6126` | `src/itsf/data/manifests.py` | **F03**（`load_authorized_manifest`）· **F04**（`read_verified_bytes`） |
| `04e79418337ccad178fd74d37cc25f5a44033ef69cab41dc0a5124f2ba6fcdf9` | `12724` | `src/itsf/mc/production_inputs.py` | **F03/F04**（受管 `condition.json` 读取点） |

### 0.2 结算回归(role = reference,同一提交)

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `6e130251fa62fdc690d2467de26f54df99d5dd2dec6e44c219b2d3074ecbcfd3` | `26969` | `tests/test_qros_cf_astra_repairs.py` | **F01–F06 的结算测试**,40 条:每条 finding 的反例 + 其正向路径 |
| `7bc5b32182ef05b0e816d12cbe63b9779a96c6db50e4981f2aa510f4714026e0` | `24714` | `tests/test_execution_identity.py` | T-F01;seam 夹具注入两个新 report,使每条仍因自己命名的理由拒绝 |
| `c9435e9202f7ec6151b91fce32ec02e6cacc3b78d213fad7d2b2d6f019c58e42` | `25544` | `tests/test_n09_scaffold_criteria.py` | 元守卫:P3 seam 写入集合(已加严,见 §3) |
| `9c262c405fcced24d575719adb5d5693224095766f36a59d85516b94244a8576` | `12010` | `tests/test_registry_path_single_construction.py` | 元守卫:registry 路径构造登记 |
| `985569a7cbe92db4a6a81a1e47233efc0270d9dabbab9dd7312350d8886d38d3` | `9728` | `tests/test_every_identity_pattern_is_swept.py` | 元守卫:`LINE_PARSERS` 声明(意图扫描为何不得锚定) |

### 0.3 权威定义与参考(role = reference)

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| 见 `ARTIFACTS_UNDER_REVIEW.json` | — | `ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md` | **F01–F06 的权威定义**。原报告仅经聊天传递、从未落盘,本文件是该缺口的补救,并逐字说明它转录的是 Aaron 的派发陈述、不是 Astra 报告原文 |
| `14e2d84defc6a77e408bba37806246d220e1bd2ee5af836a730843443d87d72a` | `5985` | `ops/REVIEWER_CONTRACT.md` | **T1–T6 威胁定义**与判决词表(PASS / PASS_WITH_BACKLOG / HOLD),两轮预算,污染协议 |
| `7a0fd26969f68e1a4ac2de6167b03ebbb6c83368e1f6998dec93422485ab187a` | `11381` | `ops/BACKLOG.md` | F07/F08 作为 **B-22 / B-23** 的落点;唯一 blocker 集合 |
| `5c9af31df771eb9c36ff8100b881b5efd17f4e69a2e80e5a42e76cec1961540d` | `6084` | `ops/RECOVERY_ANCHOR.md` | **允许的 outcome-clean 入口点** |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | `2563` | `ops/OUTCOME_CARRYING_ARTIFACTS.json` | **隔离登记册**（quarantine register） |
| `8bd3668c887f812de07a9763ffb37cc5cbee92c0a5d14d4911e98748f8965598` | `5770` | `ops/NEXT_HANDOFF.md` | **强制同行件**（本包 `COMPANION`,禁读清单载体）。第一版声明它"必须同行"却没有把它登记进在审集——**Astra 据此正确 STOP**:强制件未被钉住,与缺失同罪。现已登记 |

转录件的 sha256 未写在本包正文内,原因与本包自身相同:它与本包在同一批提交中
落盘,把它的 hash 写进正文再提交会改变本包 hash。它由
`ops/ARTIFACTS_UNDER_REVIEW.json` 承载并每次运行核对——**该 JSON 是唯一权威
的在审清单**。

---

## 1. 禁读清单与入口(D-2,必须随每个交付载体同行)

- **隔离登记册**:`ops/OUTCOME_CARRYING_ARTIFACTS.json`。其上列出的任何路径都不得读取。
- **盲席位不得检索仓库**:`BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY`。本次是定向复审而非盲审,但检索仍限于 §0 表内路径及其直接依赖;不得漫游 `ops/`。
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

这些文件携带 S0-T001 的**结果**。本次复审只关心执行安全与数据身份,不需要任何
结果数字;读到它们会烧掉一个可用于未来独立验证的席位。

---

## 2. 范围 —— 只有 F01–F06

退出判据**只有**六条 BLOCKING finding。原文见 §0.3 的转录件,不在此处重写——
把它们改写成新表述会造成新的 finding 谱系,那正是本次要避免的。

```
F01  bytecode / source execution        T1
F02  startup / import hook              T1
F03  authorized manifest authority      T3
F04  verify-consume same bytes          T3
F05  malformed owner-control fail-open  T5
F06  owner-hold / P3 serialization race T5
```

**F07 / F08 在范围之外**,已作为 B-22 / B-23 记入 backlog。Aaron 的指示:两者
都不能产生未授权的 STARTED——F07 拒绝一个**合法**启动,F08 **关闭**授权。不得
以它们阻挡本次退出。

不在范围内、且不得在本轮重开的:架构、N10/N11/N13、任何真实运行、
F01–F06 之外的新缺陷搜寻(若发现,记为新 finding 交 Aaron,不并入本轮退出判据)。

---

## 3. 修复者自报的证据 —— **请当作待验证的声明,不是结论**

本席位写了被审代码,因此以下每一条都应被独立复核。§0.2 的结算文件是它们的
可执行形式。

| id | 修复的机制 | 结算方式 | 引入的拒绝码 |
|---|---|---|---|
| F01 | 不信任预存缓存:要求 `-B` + 私有 `sys.pycache_prefix` + 受管源在该前缀下零缓存文件 | 篡改的 timestamp-valid 缓存在该条件下被忽略,授权源语义(`960`)执行;不满足条件时 seam 在 P3 前拒绝 | `seam_bytecode_cache_readable` |
| F02 | 只约束真正在启动时执行的面:可执行 `.pth`(按实机普查固定两个必需项)+ `sitecustomize`/`usercustomize` | 合成可执行 `.pth` → 拒绝;纯数据 `.pth` → 不拒绝(它不执行,拒绝它就是变相全机 hash) | `seam_startup_surface_unpinned` |
| F03 | 受管路径只认官方 `manifest.json`;新增独立入口而非加开关 | 授权清单不变 + 冲突本地清单 + 替换 `condition.json` → 拒绝 | `ManifestError`（未新增码） |
| F04 | 读一次、验这批字节、消费同一批 | 验证后替换 → 消费到的仍是被验证的字节;验证前替换 → 摘要拒绝 | `ManifestError`（未新增码） |
| F05 | 在通用丢弃之前对原始文本做 owner-control 意图扫描;凡带 token 却未产出合法行者一律拒绝 | 缺尾管线 / reason 内多管线 / 单元格数不对 / actor 畸形 → 全部拒绝,且 registry 字节不变、无 P3 | `owner_control_row_unreadable` · `p3_owner_control_row_unreadable` |
| F06 | 一次读决策,同一版本被追加;`O_EXCL` 锁内 compare-and-swap | 在 Astra 复现的边界确定性插入 hold:hold 先 → 拒绝且不写 P3 字节、hold 保留;append 先 → P3 落账,后到的 hold 排在其后 | `p3_registry_changed_under_decision` · `p3_append_lock_unavailable` |

**一个被实现后否决的方向**,请一并检视是否同意该判断:F01 的"校验缓存内容"
路线先被实现,而它不成立——`marshal.dumps` 对等价 code object 不是字节稳定的
(interning 顺序),结构化摘要需要已废弃的 `co_lnotab`,两者都在无人改动的文件上
报错(68 个可信缓存中分别 3 个与 7 个)。会误拒的门比没有门更糟,故改用可判定的
启动条件机制。若你认为内容校验仍应存在,这是一条应当提出的 finding。

**四处元守卫被要求交代并已交代,无一被削弱**:意图扫描在 `LINE_PARSERS` 内声明
理由(它必须匹配行解析器拒绝的行,锚定即失效);P3 seam 写入守卫现覆盖两个 seam
函数加锁,并**加严**为"恰好一处 registry 字节写入、在 CAS 内、`append_run_started`
内零写入、锁内零写入、CAS 只能被 seam 调用";构造登记册增加本文件的六处读取;
seam 夹具注入两个新 report。

---

## 4. 请你做的事

1. 逐行重算 §0 的 sha256;不符即 STOP。
2. 以 §0.3 的转录件为 F01–F06 的定义,**独立复现每条原始反例**——不要以本包的
   复现记录代替你自己的。
3. 判断每条修复是否恢复了被声明的不变量,以及是否引入新的失败面。
4. 用 `ops/REVIEWER_CONTRACT.md` 的词表给出判决:`PASS` / `PASS_WITH_BACKLOG` /
   `HOLD`。BLOCKING finding 须点名恰好一个威胁(T1–T6)、一条具体失败路径、
   及其证据类别。
5. 区分**你复现的事实**与**本席位自报的测量**。后者在 §3 与转录件 §3 已标记。

不要修改任何文件。不要执行 `qros`。不要追加任何 registry 事件。

---

## 5. 本包不做的事

不接受、不裁定、不关闭任何 finding。F01–F06 在一个新的独立席位另有结论之前
保持 BLOCKING,而那个结论由 Aaron 派发与记录——不由写了这份修复的席位给出。
