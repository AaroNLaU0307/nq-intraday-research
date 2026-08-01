# S0_REAL_RUN_AUTHORIZATION_PACKET

```
status: PENDING_AARON_APPROVAL
real_s0: REAL_S0_NOT_AUTHORIZED
drafted_at_utc: 2026-07-31
drafted_by: main agent (solo; no subagent, no workflow, no real data read)
```

本包只授权**首次真实 S0**。批准本包 ≠ 运行授权；运行只能由 §10 的精确
授权语句触发。

## 0. Trial 治理状态机（Aaron 2026-07-31 修订批复）

```
PACKET_DRAFTED → PACKET_APPROVED → RUNNER_IMPLEMENTED
→ READY_FOR_RUN_AUTHORIZATION → RUN_AUTHORIZED → RUNNING
→ COMPLETED / FAILED
```

- 当前位置：**PACKET_DRAFTED**（治理框架已获 Aaron 批准，最终包待
  runner 落地后重渲染再批）。
- `PACKET_APPROVED` 与 `RUN_AUTHORIZED` 是**不同状态**，前者绝不自动
  推进为后者；每次状态变化以事件追加进 ops/TRIAL_REGISTRY.md
  （UTC 时间＋commit＋actor＋原因），既有记录永不修改。
- **最终环境锁（M5-T5 重渲染，2026-08-02 实值；SA-11 修复落地后
  entrypoint/runner 两行已再渲染；authorized_commit 除外
  ——见 §1 防自引用定案）**：
  ```
  runner_entrypoint: scripts/s0_real_run.py  (zero CLI args; env-clean gate)
  runner_source_sha256:
    scripts/s0_real_run.py:  2f0e2a1ad57099f10263ee18f7b0584d7661183b...
    src/itsf/s0/runner.py:   772790cd9572446a...
    src/itsf/s0/runinfra.py: b6cd12d3158ba2a7...
    src/itsf/s0/context.py:  a20e959767191932...
    src/itsf/s0/dataset.py:  8e12d35043c0110d...
    src/itsf/s0/labels.py:   964af7725061ad5d...
    src/itsf/s0/features.py: a5e222f679731640...
    src/itsf/contracts.py:   80868657b68901d4...
    src/itsf/guards.py:      6ec6345734e97f2f...
  requirements_lock: ops/requirements.lock.txt
    sha256 f87799f6d24d3788b8b7b41b7f81d3b01cb2da8070294eba56bada69bbcc16a0
  python: 3.13.14 | pandas 2.3.3 | numpy 2.5.0 | databento 0.81.0
  pandas-market-calendars 5.4.0 | tzdata 2026.3
  os: Windows-11-10.0.26200-SP0 | machine tz irrelevant (all logic ET via
  zoneinfo; context enforces tz-aware ET at the choke point)
  preflight (M5-T5 rerun, IR-22/23/24, IR-24 divergence==0 evidenced):
    S0_INPUT_PREFLIGHT.json  9d6dd1c15602f6188e0b85754118dd51eb81b65c...
    S0_INPUT_PREFLIGHT_REPORT.md  ea287f85638c0afdac6d5d0dd9bbfbc85f1c...
  zero-override proof: 13-gate roster incl. parent_env_clean +
    frozen_constants_in_process; hermetic child env; no CLI args
    (pinned by tests/test_s0_runner.py)
  ```
  重渲染后的状态上限为 `READY_FOR_RUN_AUTHORIZATION`（须 final-readiness
  审计全 CLOSED），仍须 Aaron 发 §10 精确语句才进入 `RUN_AUTHORIZED`。

## 1. 运行代码版本

- 起草时 Git HEAD（全 hash）：`541571f4c0f55eadf19f9edfda1688e98f5deffd`
- 起草时工作区：CLEAN（git status --porcelain 空）
- **本次运行允许使用的唯一 commit**（Aaron 2026-08-02 §四防自引用定案）：
  ```
  authorized_commit_source: exact_section_10_runtime_authorization_event
  authorized_commit: TO_BE_SUPPLIED_BY_AARON
  runtime_requirement: authorized_commit == git_HEAD
  ```
  tracked 授权包**永不**嵌入自身最终 commit hash（含自身 hash 的文件无法
  稳定得到自己的 commit hash）；真正的 commit 只由 Aaron 的 §10 精确语句
  提供，并由 registry 事件解析器结构化验证（event 单元格恰为
  RUN_AUTHORIZED＋逐字语句＋40 位 hash == HEAD）。
  历史注记：runner 已实现（M5-T1..T4），Stage C 为真实链，占位符全除。
- 运行前 HEAD 若与授权语句中的 hash 不一致，**授权自动失效**，必须重新
  申请；工作区必须 CLEAN。

## 2. 冻结与治理状态

| 项 | 引用 |
|---|---|
| s0-freeze-v1 | tag → commit `89e2505928342d131c8f6eff93369bcc46f909b4`（Charter v1.2-r2、S0 预注册 v0.6、purchase_plan rev4） |
| mc-freeze-v1 | tag → commit `5d1ec10ee3ff66cf9bd9c432458d3367dea42da6`（MC_METHOD_SPEC v0.6、platform_params v0.6、registry、manifest_v5） |
| G9 resolution | commit `f932714725dbbc769f9c33deaccd468d1b6d6985`（CME 费表官方证据，Case A，$1.74 不变） |
| M4 最终收口 | commit `d036837ccdb5b0c29b4cff740eb528b6129f02a3`；key attestation commit `541571f4c0f55eadf19f9edfda1688e98f5deffd` |
| IR-1..IR-20 | 全部 APPROVED_BY_AARON（IMPLEMENTATION_RESOLUTIONS.md）；对 S0 直接适用：IR-2/11（描述性口径）、IR-4（sizing 含 $1.74）、IR-7（场景 slip）、IR-12..14（F10）、IR-15（路径）、IR-16（symbology 仅验证披露）、IR-17（发布时刻 NA）、IR-18..20（F10 冲突/前收盘/F4 参照集） |
| 运行前重验 | seal_check、structure assertions、guards 七项冻结哈希必须在运行当刻重新通过（§9 硬门），本包记录不替代运行时检查 |

## 3. 正式 trial 登记（ops/TRIAL_REGISTRY.md 同步建立）

```
trial_id: S0-T001
trial_type: FIRST_REAL_S0_FULL_DEVELOPMENT_RUN
researcher_exposure_ledger_seq: 1        # 首笔真实结果暴露
is_first_real_s0: true
```

**本 trial 将暴露的结果**（一次性、不可逆的 researcher exposure）：
双 Oracle（theoretical/executable）天花板统计；Y_cont 分布与延续基础率
p（θ 主 0.5/副 0.3）；E1/E2 引擎产出（含强制最差日 P1/P5）；按年表与
leave-one-year-out 分组；proxy/actual-micro 两时代轴分列；频率输出
（年可交易日数、Oracle 月均频率）；全部 NA 与剔除计数表。
**不暴露**：MC、EV、GO/STOP、Checkpoint 0（另行授权）。
trial 开始后不得重置、删除或重新编号；失败运行同样入册永久保留。

**trial 正式开始与 exposure 边界（Aaron 2026-07-31 修订批复）**：
- Stage A 或 Stage B 失败：记录 `PRE_RUN_ATTEMPT_FAILURE` 事件，保留
  失败日志与 artifact；**不消耗** researcher exposure ledger；**不**强制
  改用 S0-T002；再次尝试前须 Aaron 重新确认机械问题已关闭。
  （理由：A/B 阶段未计算、未暴露任何 Oracle 结果。）
- Stage A/B 全部通过、即将进入 Stage C 的瞬间：原子追加 `RUN_STARTED`
  事件，S0-T001 进入 RUNNING，exposure ledger 序号 1 **正式消耗**。
- Stage C 及以后失败：S0-T001 永久占用，记录 RUN_FAILURE_REPORT，
  修复后必须申请 S0-T002。
- **任何中间结果一旦被读取或展示，一律视为 Stage C exposure 已发生**，
  无论程序处于哪个阶段。
- **措辞修正（SA-10 N1，Aaron 2026-08-02 批准）**：Stage B 会在内存中
  完整构建数据集（IR-22 的 Stage-B STOP 语义要求如此），但**只释放结构
  计数，绝不释放任何研究数值**；A/B 失败不消耗 exposure 的依据是
  "未释放"，而非"未计算"。
- **Registry 授权快照控制（SA-10 N5 补偿控制，Aaron 2026-08-02 §三）**：
  Stage A 在授权门通过后结构化解析最后一个合法 RUN_AUTHORIZED 事件并
  写入 attempt 目录 `AUTHORIZATION_SNAPSHOT.json`（registry_sha256／
  event_sequence／trial_id／authorized_commit／精确语句 sha256）；
  进入原子 RUN_STARTED 转换前**再次核验 registry 未变**（防事件插入）；
  追加后把新 registry hash 记入 runs 目录。

## 4. 输入数据锁定（运行时逐项重验，不符即 STOP）

| 输入 | 锁定值 |
|---|---|
| A1 job | `GLBX-20260727-DL3BEBCHJA`，root `C:\Users\Aaron\quant-data\databento-archive\intraday-trend\development_signal\`，139 个 dbn.zst |
| A1 官方 manifest.json SHA-256 | `d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8` |
| A1 raw 文件哈希 | 全部 139 文件经 loader 逐文件对 manifest 验证（fail-closed，attestation 三方核对 all_raw_sha256_match=true） |
| F10 事件表 SHA-256 | `5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c`（IR-17 版，468 行 9 列） |
| symbology mapping SHA-256 | `85a32d44994b51e004e0c322510527aae18b70e1fadc70437e754253a2ac1850`（48 区间，47/47 验证） |
| spread_cost_table.csv SHA-256 | `b6d6984ff7c364f9a57514d7583685956f6b080ec02027ee8401f38f6d9509bf`（唯一允许的成本侧输入） |
| physical-copy attestation SHA-256 | `51ce415c6e2c06eb363d8061b9543c13d1b9ff11dfecbd9ec2312e3c66212813` |
| **raw_file_set_sha256**（集合摘要） | `08fca11b7a9aea1f96f740409c099696e48907a408f409dfbadd82c5ac584298` = SHA256(sorted(relative_path\|size\|file_sha256))，覆盖全部 139 个 A1 dbn.zst；总文件数 139，总字节 58,711,328。一次性验证集合无缺失/新增/改名/替换（成员 hash 取自三方核对过的官方 manifest） |
| Data QA / Preflight 对应 commit | QA `4ab40c5`＋Addendum `ac2979f`；Preflight 重跑 `d036837`（json SHA-256 `5c0ae2d7bc007cd8196d2bca796c1bf2f36e0d2c35ef4ac354d0f1d187614bbf`） |

**硬禁止**：访问 IV（2022-01-01 起任何 NQ 数据，roles.py 机器强制）；
读取 raw A2 BBO（只许上表 derived spread table）；触碰 Physical Lockbox。

## 5. 运行配置锁定

- 全部 Primary 参数唯一来源：STUDY_0_PREREGISTRATION.md（s0-freeze-v1）
  ＋ gate1/platform_params.yaml（mc-freeze-v1）＋已批 IR；代码不得内嵌
  与冻结文本不同的常数。
- 成本口径：S0 统一平台费 $1.74 RT（G9 Case A）＋ 2025Q1 spread 表四档
  场景（proxy 假设按预注册 §7 分时代披露）；场景 adverse slip 按 IR-7。
- Oracle：双路径定义（theoretical / executable）照预注册 §5-6；方向恒
  = d_open；E1（OR 对侧止损/15:45 退出）、E2（无止损 15:45 定时退出）。
- 日期资格：按冻结规则（三类剔除＋批准漏斗顺序）由 runner **独立重新
  计算**；NA 政策 = 行 45。F10：IR-12/13/14/17/18；F4：IR-20；F5：IR-19；
  F11：IR-16 映射仅验证披露。
- **expected_preflight_assertions（只作运行断言，禁作算法配置——Aaron
  2026-07-31 修订批复）**：漏斗 2989→2969→2884→2882→2868；F10 最终互斥
  128/134/83/2528/9；其余 Preflight 结构计数。runner 必须按冻结原始规则
  独立计算后与这些观测值**比对**（不符即 STOP）；禁止把这些数字用作
  样本选择、事件归类或特征取值的输入常数。
- random seed：`20260731`（仅用于预注册规定的 bootstrap CI；S0 主计算
  确定性，无其他随机源）。
- **runner 必须零命令行参数**：不接受任何可覆盖冻结 Primary 配置的
  运行时输入（inspect 级测试固化）。

## 6. 输出目录

- **双目录语义（Aaron 2026-07-31 修订批复）**：
  - Stage A/B 使用独立 pre-run attempt 目录
    `attempts/S0-T001-A<sequence>_<UTC>/`——只含机械日志与
    PRE_RUN_ATTEMPT_FAILURE 报告，**不含任何研究结果**；机械失败保留
    该目录，不消耗 exposure，不换 trial 编号；
  - Stage A/B 全部通过后才**原子创建**正式目录
    `runs/S0-T001_<UTCyyyymmddTHHMMSSZ>/`——创建正式目录与追加
    `RUN_STARTED` 事件必须属于同一受控转换，随后进入 Stage C 并消耗
    exposure ledger 序号 1；
  - 正式目录运行前**必须不存在**（存在即 STOP）；本包不创建任何目录。
- 禁止覆盖任何既有输出；临时文件、日志、结构结果、最终报告全部归入
  该目录；失败或中止时目录整体保留，禁止删除。
- **hash manifest 非自引用设计（Aaron 2026-07-31 修订批复）**：
  ```
  manifest_format: jsonl_hash_chain（append-only）
  manifest_self_excluded: true          # manifest 不对自身求 hash
  each_record: {stage, relative_path, file_sha256, previous_record_hash}
  ```
  临时未关闭文件不得进入 final manifest；每阶段结束写入 stage seal
  记录；失败目录同样保留完整 hash chain。

## 7. 运行阶段与信息释放顺序

| Stage | 内容 | 信息释放 |
|---|---|---|
| A | 运行前机械检查（§9 全部硬门） | 仅 pass/fail |
| B | 数据加载与结构验证（对 Preflight 计数逐项一致） | 仅结构计数 |
| C | S0 计算（Oracle/标签/引擎） | **零释放**（含日志，见下） |
| D | 结果完整性验证（行数＋**NA 守恒**） | 仅 pass/fail |

- **Stage C 日志防泄漏（机器强制）**：控制台与日志只允许阶段状态、
  心跳、文件 hash、非研究性的完成/失败状态；机器禁止输出 Oracle、
  标签、E1/E2、年度结果、频率、分布或任何局部研究数字——以日志词汇
  与 schema 守卫测试固化。
- **NA 完整性（取代"无 NaN"粗判——Aaron 2026-07-31 修订批复）**：
  预期 NA 必须与批准的 feature/label/anchor NA 原因表**逐项守恒**
  （允许原因显式枚举：F5 roll 日/IR-19 锚点缺失、F10 多事件、ADR14 与
  F4 warm-up、L82 零方向、锚点缺失等）；任何未登记原因产生的 NA/NaN
  立即 STOP；不得以 dropna、填充或隐式类型转换消除异常。
| E | 生成正式 S0 报告（封存入 trial 目录，含哈希） | 报告整体交付 |
| F | S0 报告封存后，MC 才可另行申请授权 | — |

中途不得向 Aaron 展示零散结果、日志数字或局部指标；不得因看到任何
中间结果而修改代码、配置或样本（预注册反窥视条款）。

## 8. 失败处理

hash 不符 / schema 不符 / 日期计数与 Preflight 不符 / 配置漂移 /
异常退出 / 任一测试失败 → **立即停止**。不得自动修复；不得静默重跑；
不得更换 seed；不得删除失败输出。生成 RUN_FAILURE_REPORT（含失败点、
已释放信息清单、目录 hash 状态）入 trial 目录并登记 TRIAL_REGISTRY。
修复后是否允许新开 trial（S0-T002）由 Aaron 再次批准；S0-T001 编号
永久占用。

## 9. 运行前硬门（全部满足才可进入 Stage B，缺一即 STOP）

1. git status clean；2. HEAD == 授权语句中的 commit；3. 全量 pytest 通过；
4. seal_check 通过；5. structure assertions 通过；6. guards 七项冻结哈希
通过；7. M4_KEY_CLOSURE_ATTESTATION.md 存在；8. gate1/G9_RESOLVED.flag
存在；9. ops/SECOND_COPY_ATTESTED.flag 存在；10. §4 全部输入 hash 逐项
一致；11. 输出目录此前不存在；12. TRIAL_REGISTRY 事件链
显示 S0-T001 处于 **RUN_AUTHORIZED** 状态（§0 状态机；由 Aaron 的 §10
精确语句触发追加，PACKET_APPROVED 不构成此门）；13. Aaron 已给出 §10
精确授权语句。全链以机器退出码为闸。

## 10. 唯一有效授权语句

只有 Aaron 回复以下**精确文本**（替换尖括号内容）后才允许运行：

```
启动第一次真实S0，授权trial_id: S0-T001，使用commit: <完整commit hash>
```

"开始"、"可以跑"、"继续"或任何其他表述**均不构成授权**。

## 11. 明确排除

本授权包只覆盖首次真实 S0（S0-T001）。**不**自动授权：MC、Checkpoint 0、
IV 访问或采购、Physical Lockbox、任何参数修改、第二次及以后 trial、
对本包所锁 hash 的任何替换。上述每一项都需要独立申请与 Aaron 独立批准。
