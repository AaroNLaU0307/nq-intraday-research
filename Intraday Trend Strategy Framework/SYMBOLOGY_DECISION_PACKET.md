# SYMBOLOGY_DECISION_PACKET（D5）

状态：**PENDING_AARON_AND_CHATGPT_APPROVAL**
发起：main agent（M4-T3，2026-07-29）；本包不改变任何冻结文件与 S0 锁定状态。

## 1. 问题

A1（NQ.v.0 continuous）的 instrument_id 是未映射整数，batch package 缺少
正式 symbology artifact；冻结文本要求"symbology 映射随数据归档"未被满足。
S0 的 F11（is_roll_transition / is_roll_window）与 F5（roll 日记 NA）依赖
roll 识别。须决定：补齐官方 mapping（Option A）还是以正式 Implementation
Resolution 限定用法（Option B）。

## 2. 对应冻结章节

- STUDY_0_PREREGISTRATION.md 行 30-32：is_roll_transition = continuous 映射
  实际切换的交易日；is_roll_window = 前后各 2 个 RTH 交易日；**"symbology
  映射随数据归档"**；"实证检查映射从不在同一 RTH session 内切换；禁止把
  roll jump 解释为 alpha"。
- 行 57（F5 gap 在 is_roll_transition 日记 NA）。
- purchase_plan A1 块（data_role: development_signal）。

## 3. 当前事实（main agent 本机核实，2026-07-29）

1. A1 官方 manifest.json **不含任何 symbology/definition 条目**——不是漏
   下载，是 job package 本来就没有（stype_in=continuous, stype_out=
   instrument_id, map_symbols=false 的 batch 不附带 symbology.json）。
2. A1 数据内 47 次 instrument_id transition：全部发生在 00:00 UTC 边界；
   无同一 RTH session 内切换；季度节奏与 2010-06→2021-12 的 47 个季度
   换月期完全一致（2010-06-13 首换 + Sep10..Dec21 共 46 次 = 47）。
   （证据：DATA_QA_ADDENDUM.md §8，qa_addendum_a1.json rolls 全表。）
3. commodity-carry 归档的 5,031 个逐日 definition.dbn.zst 已查 metadata：
   universe = 18 个商品 parent（CL/HO/RB/NG/GC/SI/HG/PL/PA/ZC/ZS/ZW/ZM/
   ZL/KE/LE/HE/GF），**不含 NQ**——本机零成本闭合 Option A 的路径不成立。
4. 免费官方路径存在：Databento `symbology.resolve` API（元数据端点，
   **不消耗数据额度、不产生美元费用**）可解析 NQ.v.0 → instrument_id 与
   NQ.v.0 → raw_symbol（合约代码）逐日区间映射，2010-06-06..2022-01-01。
   但它是联网获取，按项目规则须 Aaron 单独批准（需要临时注入 API key，
   一次会话即可，用后可撤销）。

## 4. Option A：补齐正式 symbology artifact（经免费 resolve 端点）

- Aaron 单独批准一次联网会话；`symbology.resolve` 两次调用
  （stype_out=instrument_id 与 raw_symbol），原始 JSON 响应归档至
  gate1/symbology/（raw + SHA-256 + URL/时间/参数 + 来源等级
  Level 1-vendor-official）。
- 机械验证三项：47 次 transition 与官方映射逐一吻合；同一 RTH session 内
  从不切换；47 次与季度换月一致。任何不吻合 = STOP 上交。
- instrument_id → 合约代码及有效日期映射表落地为机器可读 csv＋哈希。
- 花费：USD 0.00；网络访问 1 次；不触碰任何已冻结文件。

## 5. Option B：正式 Implementation Resolution（不补数据）

规则限定（写入 IMPLEMENTATION_RESOLUTIONS.md，编号顺延）：
- S0 只依赖 instrument_id **变化**生成 is_roll_transition / is_roll_window；
- 具体合约代码不进入 Alpha、标签、成本或判决的任何输入；
- transition 日 F5 按冻结规则记 NA；
- 未知合约身份不影响任何决策输入；
- 所有输出披露 symbology artifact 缺失；
- 未来若补齐 mapping，只能用于验证，不得改变 Primary 结果。

## 6. 影响方向

| 维度 | Option A | Option B |
|---|---|---|
| 样本 | 不变 | 不变 |
| Primary 算法 | 不变（mapping 仅验证/披露用） | 不变 |
| 判决 | 不变 | 不变 |
| 冻结符合度 | 完全恢复"映射随数据归档" | 以 IR 记录偏离并限权 |
| 风险 | 需一次联网＋key 注入 | roll 识别永远依赖单一推断源（id 变化），无独立官方对照 |

两案对 Primary 数字均为零影响；差别在证据完备性与"47 次 transition 是否
获得官方独立确认"。

## 7. main agent 推荐

**Option A（免费 resolve 变体）**。理由：零美元成本、一次性、把 F11/F5
的 roll 识别从"数据内推断"升级为"官方映射独立确认"，同时闭合冻结文本
的归档要求；Option B 保留为 Aaron 拒绝联网时的合规回退。
（按规则：main agent 不自行裁决，本推荐仅供 Aaron/ChatGPT 参考。）

## 8. 是否阻塞当前任务

不阻塞 SA-1/SA-2；不阻塞 SA-3 的机械运行（roll 计数两案同源）；
**阻塞 M4 收口与真实 S0 审批**（四项关闭条件之一）。

## 9. 涉及文件

- 新增（若 A）：gate1/symbology/**、机器可读映射 csv、evidence fragment；
- 新增（若 B）：IMPLEMENTATION_RESOLUTIONS.md 新条目；
- 两案均不改：冻结文件、loaders、guards、qa artifacts。

## 10. 需要 Aaron 批准的明确问题

1. 选 Option A 还是 Option B？
2. 若 A：是否批准一次 `symbology.resolve` 联网会话（USD 0.00，需临时
   API key，一次会话，key 用后撤销）？
