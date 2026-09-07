＃ 封闭范围机械结案检查 —— QROS-CF 最终定界修复

```ini
PACKET_TYPE=CLOSED_SCOPE_MECHANICAL_CLOSURE_CHECK（沿用既有 Review Packet 件种；**不是**广域认证包，不邀请全仓发现）
REVIEW_ID=QROS-CF-FINAL-CLOSURE-CHECK-001
PARENT_REVIEW_ID=QROS-CF-F06-OWNER-SEMANTICS-CLOSURE-001
PARENT_RESULT=**HOLD** —— GPT-5.6 Sol XHigh substantive closure review。**I1/I2 NOT SAFE TO ACTIVATE**。记录保持原样，**未改写为 PASS**
DESIGN_AUTHORITY=ops/FABLE_DESIGN_REVIEW_QROS_CF_FINAL_2026-09-07_TRANSCRIPTION.md（`ONE_BOUNDED_FINAL_REPAIR_IS_JUSTIFIED` / `NO FURTHER DESIGN REVIEW REQUIRED`）
DELIVERY_STATUS=ISSUED
ADJUDICATION_SCOPE=**仅** A1 A2 A3 A4 A5 A6 B1 B2 B3 B4 S。范围外的观察进 BACKLOG，除非它给出当前阶段某条 T1–T6 的直接失败路径并因此推翻上述某条固定不变量
VERDICT_SHAPE=**恰好一个** PASS 或 HOLD。PASS 仅当 A1–A6 全 PASS、B1–B4 全 PASS、S PASS、且传输/工件身份有效
AFTER_HOLD=QROS-CF **延期 / 不激活**。**HOLD 之后没有自动的下一轮修复**
REPAIR_COMMIT=d063834bea5c0011cc4da503c2225e36f172bff7
HEAD=d063834bea5c0011cc4da503c2225e36f172bff7
PRE_REPAIR_BASELINE=7c641ba（ANTI-DECORATIVE 伴随断言从此提交取修复前形态）
PREPARED_BY=Claude Opus 5，repair-builder seat —— **本席位写了被检查的修复，不得自审通过**
DECIDED_BY=Aaron
COMPANION=ops/NEXT_HANDOFF.md（禁读清单载体，**必须同行**）
THIS_PACKET_SHA256=（不在本文件内；由 ops/ARTIFACTS_UNDER_REVIEW.json 中 `is_the_delivery_document: true` 那一条承载）
```

---

## 0. 这份包故意是窄的

上一轮以 HOLD 归还，并把剩余失败收敛为**两个**根阻断族。Aaron 据 Fable 的
**仅设计**复审授权了**一次**定界修复。自动的「修复 → 广域复审」循环已终止。

**本件只请你裁 A1–A6 / B1–B4 / S。** 不要把它当作又一次全仓审计——
那正是这次要停下来的东西。

---

## 1. 两个根阻断的修复前复现（本席位实测）

### 1.1 Root A —— 信任根位置

```
① 父进程在子进程构造之前导入受管项目模块
   run_parent -> _startup_surfaces_are_trusted -> from itsf import execution_identity
   run_parent -> _child_environment            -> from itsf import execution_identity
② 未加旗标的直接形式启动的是普通解释器
   no_site 0 · isolated 0 · safe_path False · dont_write_bytecode 0 · ignore_env 0
③ -B 不阻止**读取**一个 timestamp-valid 的 .pyc
   实测：伪造缓存在 -B 之下照样执行
```

### 1.2 Root B —— 起动路径完整性

```
scratch registry： RUN_AUTHORIZED → OWNER_HOLD
generic serialized_append(raw RUN_STARTED bytes) → **提交成功**
提交顺序：['RUN_AUTHORIZED', 'OWNER_HOLD', 'RUN_STARTED']
而 serialized_start_append 对同一 start **正确拒绝**（start_refused_owner_hold_in_force）
公开面暴露 validate= —— 调用方可控的旁路
```

**未触碰真实受管 registry。**

---

## 2. 自举信任假设 —— 显式声明，不在运行中自证

```
trusted bootstrap boundary =
    OS 进程创建
  + 在加固旗标下选定的 Python 可执行文件 / 标准库启动（旗标在进程创建时固定、只读）
  + 被显式调用的 launcher 源码字节
```

该边界之后的一切被检查；之前的一切不被检查，本修复也不假装检查。
**没有**全机哈希、可执行文件签名、launcher 签名设施、溯源框架、信任台账。
**信任递归止于上面这条假设**，这句话同时写在 `scripts/run_governed.py` 顶部与
设计转录件里。

受认可形式：`python -I -S -B scripts/run_governed.py <module>[:<callable>]`；
`.cmd` 是同一形式的固定拼写。未加旗标的形式**失败关闭且不 re-exec**。

---

## 3. 受检集 —— 先逐字节核对，再开工

**只钉了证明 A1–A6 / B1–B4 / S 所必需的文件。** 工作树在 `d063834bea5c0011cc4da503c2225e36f172bff7` 处干净。

### 3.1 Root A

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `5afbe36984edb33bd13785c03748d566fac167c17b0c721f277e916fd4777d5d` | `11432` | `scripts/run_governed.py` | **Root A**：父进程仅用标准库直到子进程构造；无 self-re-exec；未加旗标即失败关闭；子进程 `-I -S -B -X pycache_prefix=`；site 目录与 `src` 只**追加**。**自举信任假设写在本文件顶部** |
| `ab608b467bc4ef328ef97b3de2dd57aa47d36af127d11add87f521ab9d78208e` | `265` | `scripts/run_governed.cmd` | 受认可加固形式的固定拼写 |
| `d4cedff56a0711e3dcdf7680b2c11d77c15ce03156a8d817ef2872a4f9dd861d` | `44099` | `src/itsf/execution_identity.py` | A2/A4/A6 的参照：`BOOTSTRAP_IMPORT_CLOSURE`、`HOSTILE_ENV_VARS`（A6 钉定 launcher 本地副本与它相等）、`assert_governed_launch`。**本轮未改动** |

### 3.2 Root B

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `a52275e5ced95a26c57be734250cc069206f0a87b4b8b535dafd5534f04220e3` | `45500` | `src/itsf/mc/registry_boundary.py` | **Root B**：`_physical_serialized_write` 私有化；`serialized_append` 用权威解析器分类并**拒绝任何 start-equivalent 行**；`serialized_start_append` 要求恰好一行 start 并执行 owner 决定；公开面不存在调用方可控旁路 |

### 3.3 结案检查本体与随根因更新的既有测试

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `efc86a39d31322c6b6be44b8e2075d2aec62a460794aee28082a2644d251073f` | `27203` | `tests/test_qros_cf_final_closure.py` | **A1–A6 / B1–B4 本体，46 条**。每条新守卫都带一条 ANTI-DECORATIVE 伴随断言：把 `7c641ba` 的**修复前形态**从 git 取出，喂给该守卫自己的规则，证明它会红 |
| `64e3614fa436f2088d3b273f7868e96c2ea7acc9c5dfc81bd58f49fb38dd1738` | `28957` | `tests/test_qros_cf_pre_cert.py` | F01/F02 既有结算测试（本轮随根因更新） |
| `38e195e06983d6c6e103765d871a1983016d6ef9d31fe551f5da6d6d868aa104` | `27354` | `tests/test_qros_cf_f06_owner_semantics.py` | F06 owner 语义（本轮随根因更新） |
| `44860568707ffe1c28e2b589ab3f651c6de6e01714f4935719caab8efee774c8` | `24036` | `tests/test_qros_cf_f06_writer_completeness.py` | F06 写者完整性。**本轮修正了两处我自己的规则缺陷**：clause (a) 曾匹配**docstring**、以及「到达原语」必须含两个公开入口 |
| `e1012050781c32c7b533198fc3973712a0d3ce47e2193659ce986c42a1a9ed2e` | `33063` | `tests/test_n09_scaffold_criteria.py` | 写者集合元守卫（SEAM 扩至私有写入） |
| `de0948b7b24f1fa9933e04d2b2cbb32b4a786b06df66ad09a3e1b39cc9222f70` | `30300` | `tests/test_qros_cf_astra_repairs.py` | 第一轮结算测试（随物理写入位置更新） |
| `3dec5c600ad90cb11b13c8c94ce626116b2440b0a0b1323599bcf19309085b7b` | `40526` | `tests/test_qros_cf_astra_round2.py` | 第二轮结算测试（随启动形式更新） |

### 3.4 授权依据、谱系与随包件

| sha256 | bytes | 路径 | 作用 |
|---|---|---|---|
| `897d5f78ad1a359e49468bae33023e78fb8e46dea426010c9817af4d54593818` | `5630` | `ops/FABLE_DESIGN_REVIEW_QROS_CF_FINAL_2026-09-07_TRANSCRIPTION.md` | **本轮修复的授权依据**：`ONE_BOUNDED_FINAL_REPAIR_IS_JUSTIFIED` / `NO FURTHER DESIGN REVIEW REQUIRED`，含自举信任假设与结构性 API 条件 |
| `1df3ff235e3b472a6bcfad6b2b35b9a863d60aaab6a4ce3c2a2e3f25cdaef75d` | `19321` | `ops/REVIEW_PACKET_QROS_CF_F06_OWNER_SEMANTICS_CLOSURE_2026-09-07.md` | **上一轮的 HOLD，历史证据**（`RETURNED_VERDICT=HOLD`，`I1/I2 NOT SAFE TO ACTIVATE`）。**未被改写为 PASS** |
| `14e2d84defc6a77e408bba37806246d220e1bd2ee5af836a730843443d87d72a` | `5985` | `ops/REVIEWER_CONTRACT.md` | T1–T6 与 PASS / HOLD 词表 |
| `5c9af31df771eb9c36ff8100b881b5efd17f4e69a2e80e5a42e76cec1961540d` | `6084` | `ops/RECOVERY_ANCHOR.md` | 允许的 outcome-clean 定位入口 |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | `2563` | `ops/OUTCOME_CARRYING_ARTIFACTS.json` | 隔离登记册（12 条） |
| `8d6e8d177689ed088969937bbf08e5d5d640d905daea735c050fef42413f0010` | `7607` | `ops/NEXT_HANDOFF.md` | **强制同行件**，禁读清单载体 |

---

## 4. 禁读清单与入口

- **隔离登记册**：`ops/OUTCOME_CARRYING_ARTIFACTS.json`，其上任何路径都不得读取。
- **允许的 outcome-clean 入口**：`ops/RECOVERY_ANCHOR.md`。
- 检索限于 §3 表内路径及其直接依赖。**对 `src/` 与 `scripts/` 做 AST 扫描是被
  明确许可的**（只读项目源码，不触及 `ops/`）；**不要**扩到 `ops/`。

【OFF-LIMITS】以下 12 条全部禁读（outcome-carrying）

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

`MC_TO_STRATEGY_MASTER_PLAN.md` 既 outcome-carrying、又曾是项目的「恢复锚点」，
一个正常定位状态的审阅者会正面撞上去；2026-08-25 已有一个 fresh 席位如此被烧掉。
用 `RECOVERY_ANCHOR.md` 定位。

---

## 5. 固定结案判据

请对每一条给出 PASS 或 HOLD，然后给**一个**总判决。

```
A1  父自举路径在子进程构造前导入零个项目模块；
    且自举 stdlib 路径不能被受管 scripts/src 树遮蔽
A2  加固启动带**分相位**证据：父相位无受管导入；子相位在条件建立后方可导入
A3  未加旗标的调用：拒绝、非零退出、无受管子进程、目标未执行
A4  受管树内放入 timestamp-valid 的伪造 execution_identity 缓存后，
    加固启动不受其控制；子进程在所需条件下启动且私有缓存边界成立
A5  合成 site 目录内可执行启动面的改动，不能在子进程条件建立前影响其执行；
    对**已改动的被钉启动面**，既有拒绝行为仍然正确
A6  父进程本地环境控制元组（若重复）与权威 HOSTILE_ENV_VARS 相等；
    且 attestation 之前 stdlib 解析先于受管 src/scripts
B1  对**每个**现行 start token 与权威解析器支持的每种拼法，
    generic serialized_append 一律**拒绝**（有无 HOLD 皆然）；字节不变；无残锁
B2  合法**非起动**事件仍可经 serialized_append 提交，
    包括在 GLOBAL HOLD 生效、而现行语义允许它们时
B3  serialized_start_append 对非起动行 / 多行 / 畸形行**拒绝**；
    合法 start 形态**提交**；可适用未释放 HOLD 之下**拒绝**
B4  机械边界证明：唯一物理写入点；两个公开入口都汇聚于它；
    generic 入口无法经调用方可控旗标/回调启用 start 语义；
    start 入口必然提供 start 语义决定；受支持调用者被机械登记；
    修复前的 raw-start-through-generic 形态会让该守卫红
S   受影响的定向套件 → A+B → 全套；0 failed（既有 B-20 历史 xfail 可保持）
    并核 F03 / F04 / F05 / F06 保全、FLAG_PATH_BYPASS 处置未被扩大、
    真实 registry 未变、无实时 registry 事件写入、工作树干净
```

---

## 6. 本席位自报的结果 —— **请当作待验证的声明**

```
A1–A6 / B1–B4   46 条，全 PASS（tests/test_qros_cf_final_closure.py）
S               定向 178 passed · A+B 5253 passed · 全套 5473 passed / 1 xfailed / 0 failed
xfail           仅既有 B-20 历史条目，未变
```

**ANTI-DECORATIVE 已逐条执行**：每条新守卫都有一条伴随断言，把 `7c641ba` 的
修复前形态从 git 取出、喂给该守卫自己的规则、并证明它会红。
这一步查出了**我自己规则里的两个缺陷**：clause (a) 曾匹配 **docstring**
（守卫读散文而非代码，本项目反复中招的形态）；以及「到达原语」必须包含两个公开
入口，否则 Root B 让跨模块写者改为委托的那一刻，它就从「本文件存在的理由」
变成了不可见。两者都已修，登记表内无不可达行。

---

## 7. 基准怀疑度

本席位在这条谱系上已经错过五次，形态相同——**声称宽于事实**：

```
第 1 轮修复  五条修复各自通过我写的结算测试，你仍复现了五条反例
第 2 轮修复  我写「机制化强制」，而它对 P3 seam 成立、对每个真实运行入口不成立
第 2 轮测量  我写「-S 不能用」，真相是「-S 单用不能，加显式 site 目录可以」
F06 第 1 次  我写「三个受支持写者共享同一原语」，而第四个在序列化之外
F06 第 2 次  我为关闭上一条 F06 缺陷而写的测试，把**下一条**缺陷断言成了正确行为
```

**请假设同类错误还在。** 若 §6 的任何一条自报与你的复现不符，那就是 HOLD。

---

## 8. 本件不做的事

不接受、不裁定、不关闭范围之外的任何 finding。**上一轮及之前所有 HOLD 记录
保持原样，不因本件而变成 PASS。** I1/I2 是否可激活由 Aaron 裁定。
若本件判 HOLD，QROS-CF 延期 / 不激活，**之后没有自动的下一轮修复**。
