# S0_REAL_RUN_AUTHORIZATION_PACKET

```
status: PENDING_AARON_APPROVAL
real_s0: REAL_S0_NOT_AUTHORIZED
drafted_at_utc: 2026-07-31
drafted_by: main agent (solo; no subagent, no workflow, no real data read)
```

本包只授权**首次真实 S0**。批准本包 ≠ 运行授权；运行只能由 §10 的精确
授权语句触发。

## 1. 运行代码版本

- 起草时 Git HEAD（全 hash）：`541571f4c0f55eadf19f9edfda1688e98f5deffd`
- 起草时工作区：CLEAN（git status --porcelain 空）
- **本次运行允许使用的唯一 commit**：由 Aaron 在 §10 授权语句中指名的
  完整 hash。诚实前提：真实 S0 runner 尚未实现（当前
  `run_real_study()` 为 NotImplementedError 挡板）；流程为
  本包批准 → runner 实现与审查 → 全部硬门通过 → Aaron 指名该 commit。
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
- 日期资格：Preflight 定稿漏斗（2989→2969→2884→2882→2868）＋冻结三类
  剔除；NA 政策 = 行 45（非剔除日不删，特征 NA 计数）。
- F10：IR-12/13/14/17/18（互斥分区 128/134/83/2528/9）；F4：IR-20；
  F5：IR-19（前一实际 session；半日市取排期收盘 bar）；F11：IR-16 映射
  仅验证披露。
- random seed：`20260731`（仅用于预注册规定的 bootstrap CI；S0 主计算
  确定性，无其他随机源）。
- **runner 必须零命令行参数**：不接受任何可覆盖冻结 Primary 配置的
  运行时输入（inspect 级测试固化）。

## 6. 输出目录

- 模板：`runs/S0-T001_<UTCyyyymmddTHHMMSSZ>/`——运行时创建，**此前必须
  不存在**（存在即 STOP）；本包不创建任何目录。
- 禁止覆盖任何既有输出；临时文件、日志、结构结果、最终报告全部归入
  该目录；目录创建后立即登记内容 hash manifest 并随阶段追加；
  失败或中止时目录整体保留，禁止删除。

## 7. 运行阶段与信息释放顺序

| Stage | 内容 | 信息释放 |
|---|---|---|
| A | 运行前机械检查（§9 全部硬门） | 仅 pass/fail |
| B | 数据加载与结构验证（对 Preflight 计数逐项一致） | 仅结构计数 |
| C | S0 计算（Oracle/标签/引擎） | **零释放** |
| D | 结果完整性验证（行数、NA 守恒、无 NaN 泄漏） | 仅 pass/fail |
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
一致；11. 输出目录此前不存在；12. S0-T001 已在 TRIAL_REGISTRY 登记且
状态为 APPROVED（由 Aaron 批准动作翻转）；13. Aaron 已给出 §10 精确
授权语句。全链以机器退出码为闸。

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
