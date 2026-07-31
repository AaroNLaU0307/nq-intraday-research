# DECISION PACKET — S0CORE / Y6：年内十分位的装桶规则

状态：PENDING_AARON_AND_CHATGPT_APPROVAL
来源：M5-T1 / SA-4 在实现中标记（spend-limit 终止前已在代码中按 pending
参数设计防护；包文件由 main agent 补写）。

## 1. 问题

冻结行 91：`Y6 cont_decile = Y_cont 在 Development 分年内十分位（描述）`。
"十分位"的**装桶规则**冻结文本未唯一确定：等频排名装桶还是分位数边界
装桶，并列值与不能整除时的处理不同。

## 2. 冻结章节

行 86-91 标签表（Y6 行，用途栏 = 描述）；行 45 NA 政策。

## 3. 事实

- dataset.assign_y6_deciles 已实现两种约定，由显式参数选择，默认
  `None` = 不装桶＋pending 记录（不静默选择）：
  - `rank_equal_count_1_10`：年内非 NA Y_cont 等频排名装桶，并列以
    trade_date 打破（完全确定性）；
  - `quantile_edges_1_10`：numpy 线性插值的 10%..90% 分位边界装桶，
    并列值同桶。
- Y_cont 为 NA 的日子两种约定下都保持 Y6 = None。
- 两约定均已被确定性与边界测试覆盖（test_s0_dataset.py）。

## 4. Option A：rank_equal_count_1_10

每桶数量最均衡；并列打破规则显式且确定；每年首尾桶必非空。

## 5. Option B：quantile_edges_1_10

与"十分位数"的统计学直觉更贴近；并列值不会被拆进不同桶；但偏态年份
可能出现空桶/桶大小失衡。

## 6. 影响方向

Y6 是**纯描述性标签**（冻结用途栏），不进入 Oracle 判据、成本、样本
资格或任何判决。两案对 Primary 影响均为零；差别只在描述表的分组语义。

## 7. main agent 推荐

**Option A（rank_equal_count_1_10）**：确定性完备（并列打破规则显式），
跨年可比性最好（每桶数量恒定），审计重放零歧义。仅供参考，裁决在
Aaron/ChatGPT。

## 8. 是否阻塞

不阻塞 runner 实现与集成（默认 pending 安全）；阻塞真实 S0 报告中
Y6 列的最终定稿——须在授权真实 S0 前批复。

## 9. 涉及文件

src/itsf/s0/dataset.py（assign_y6_deciles，两案均已实现，批复后由
main agent 在 runner 配置中指名）；S0_REAL_RUN_AUTHORIZATION_PACKET §5。

## 10. 需 Aaron 批准的明确问题

Y6 装桶采用 A（等频排名）还是 B（分位边界）？
