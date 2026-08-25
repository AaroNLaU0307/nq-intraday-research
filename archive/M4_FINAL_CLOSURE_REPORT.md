# M4 FINAL CLOSURE REPORT

状态：M4 收口完成，**真实 S0 仍锁定**，等待 Aaron 对本报告的明确批准。
本报告只含结构计数、布尔、原因分类与治理事实；无任何策略/Oracle/收益/
EV/MC/判决数字。

## 1. 批准决策落档与实施（Aaron 2026-07-29 终批）

- **IR-18**（F10 多事件作用域，Option A）：IR-13 过滤后判定冲突；Primary
  F10 NA = 9 天；19 天原始结构保留 diagnostic sidecar；10 个单类别日按其
  唯一类别编码；IR-12 表述已修订（19 = raw diagnostic count）。
- **IR-19**（D7 前日 RTH 收盘，修订版 Option B）：前日 = 紧邻上一**实际
  CME RTH session**（独立于资格漏斗）；常规日 15:59 bar close；半日市取
  最后**排期** RTH bar close＋sidecar 标记；排期收盘 bar 缺失→NA；
  vendor-degraded 前日不得跳过→NA；禁一切填充/替代。
- **IR-20**（F4 参照集，Option A 精确化）：前 60 个实际 RTH 交易日且
  早盘 30 根完整（含半日市、含 warm-up 日；不要求下游资格）。
- 报告治理修正两条（F10 双报＋互斥断言；commit 元数据四字段方案）均已
  实施于 scripts/s0_input_preflight.py 与两份输出。

## 2. Preflight 重跑结果（全部机械生成）

漏斗不变：2989 → −20 → 2969 → −85 → 2884 → −2 → **2882** → −14 → **2868**
（守恒＋互斥七项检查全 True；与 DATA_QA_ADDENDUM 十项交叉核对全符）。

**IR-19 生效对比**（旧 → 新）：
- prev_rth_close 缺失：**73 → 18**
  - 58 个半日市案例恢复（sidecar `prev_close_from_early_close_day` = 58）
  - 12 个半日市的最后排期 bar 本身缺失（薄交易时代无成交分钟）→ 按规则
    NA，未回退到"最后存在 bar"
  - 3 个 vendor-degraded 零 bar 日的后继日（2014-06-16、2014-09-26、
    2015-01-02）从旧实现的"跳过取值"改为 **NA**（不跳过规则）
  - 2 个 vendor 部分缺失前日（2020-03-02、2020-07-01 的前日）＋样本首日
    维持 NA
- F5：NA 132 → **76**（= 18 锚点 + 47 roll + 11 warm-up 非重叠计数）；
  可构建 2750 → **2806**。
  注：Aaron 批复中"预计 ≈62 NA"为估算；机械结果 76 的差额正是上述
  12＋3 个 fail-closed 案例——按"缺失即 NA、不得回退"的批复本义执行。

**F10 双报（人口 = 2882）**：
- raw membership（重叠）：CPI 137 / NFP 134 / FOMC 92
- **最终互斥**：CPI 128 + NFP 134 + FOMC 83 + none 2528 + NA_multi_event 9
  = **2882**（断言 True；9 个冲突日全为 CPI×FOMC 组合）

特征覆盖（可构建/NA）：F1 2868/14 · F2 2868/14 · F3 2882/0 · F4 2823/59 ·
F5 2806/76 · F6 2881/1 · F7 2868/14 · F8 2856/26 · F9 2882/0 ·
F10 2873/9 · F11 2882/0。

**commit 元数据（四字段方案，报告与 JSON 同源）**：
input_commit = report_rendered_from_head = `c557c3b…`（重跑时 HEAD）；
subagent_integration_commit = `a8faf31…`；post_integration_fix_commit =
`c557c3b…`。本收口 commit 不自引用。

## 3. SA-1 七项只读安全审计（scripts/m4_sa1_security_audit.py）

**ALL_PASS**：
1. Git 无 key/cookie/浏览器 profile/请求头 secret（152 个证据文件扫描零命中）；
2. 140/140 原始件 SHA-256 重算与 registry fragment 吻合；
3. SOURCE_LOG/fragment/csv 链无断点（468 行 source_id 全解析）；
4. 多事件日按 IR-12+IR-18（9 primary NA / 19 sidecar / 分区守恒）；
5. multi-hot 仅存 diagnostic sidecar，冻结 F10 单类别；
6. 4 个非预定 FOMC 行动仅诊断，冻结 FOMC = 92；
7. 停摆延期按实际官方发布日（2013-10-22 NFP / 2013-10-30 CPI）。

## 4. Key 收口状态（按批复：不做 API 探测）

- 仓库 tracked 文件 secret 扫描（db- 模式）：**零命中** ✅
- 证据/符号学 artifact 扫描：**零命中** ✅
- `DATABENTO_API_KEY` Machine 域：**ABSENT** ✅
- `DATABENTO_API_KEY` User 域：**仍 PRESENT** ⚠ —— 待 Aaron 删除
- Aaron 后台撤销声明：**尚未收到** ⚠ —— 待 Aaron 确认
（两项 OPEN ITEM 均为 Aaron 亲手动作；main agent 不代作、不以 401 探测
"证明"撤销。）

## 5. 流程控制事故留档（Aaron 要求如实保留）

2026-07-29，commit `ae9b19c`（integration_commit 盖章）在测试套件红时被
提交：同一条命令输出中 `1 failed, 231 passed` 未被 main agent 目视捕获。
失败测试为 SA-3 将 integration_commit 冻结为 null 的生命周期断言；已以
`c557c3b` 修复（接受 null | 40-hex 两种合法状态）。整改：自此里程碑提交
一律以机器退出码为硬闸（pytest/seal/结构断言/冻结哈希任一非零则 commit
物理不可达）；本收口 commit 即按该纪律执行。未重写历史。

## 6. 收口时机械校验（退出码硬闸链输出见 commit 记录）

- pytest 全量：**234 passed**
- seal_check（mc-freeze 六项）：PASS
- verify_freeze_hashes（s0-freeze）：ALL_VERIFIED
- guards.verify_frozen_hashes()（七项规范）：OK
- pyyaml 结构断言：OK
- SA-1 七项审计：ALL_PASS

## 7. M4 四项工作最终状态

| 项 | 状态 |
|---|---|
| F10 官方事件日历 | **关闭**（468 事件、140 Level-1 件、IR-17/18 落地） |
| Development 硬边界 | **关闭**（roles.py 单一真源、13 边界测试） |
| symbology 治理 | **关闭**（官方映射 47/47 验证、IR-16） |
| S0_INPUT_PREFLIGHT | **关闭**（IR-18/19/20 实施、双报＋断言、234 测试） |

## 8. 等待 Aaron

1. 撤销临时 Databento key（后台）＋删除 User 域环境变量，并回复确认；
2. 审阅本报告；
3. 若批准 → 明确回复后才进入"第一次真实 S0"的启动决策。
   在此之前禁止运行真实 S0、Oracle、收益、EV、MC、Checkpoint 0。
