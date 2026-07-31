# DECISION PACKET — F4：NaN 成交量被静默当作 0（SA-6 F-15）

状态：PENDING_AARON_AND_CHATGPT_APPROVAL（来源：SA-6 对抗审计）

1. **问题**：context/preflight 用 `np.nansum` 求早盘成交量——若某日 30 根
   bar 齐全但 volume 含 NaN，得 `obs_volume=0.0`（貌似合法值而非 NA），
   且该日以 0 值进入 IR-20 参照集，污染其后至多 60 日的中位数分母。
2. **冻结章节**：行 56（F4）；行 45（算不出记 NA）；IR-20。
3. **事实**：与已批 preflight 同源（s0_input_preflight.py 同一写法）——
   属共享缺陷非新偏离；**当前真实 A1 数据无 NaN volume**（Data QA 七项
   全零），故对已批 preflight 数字零影响；这是面向未来数据修订的封口。
4. **Option A**：NaN volume → 记不批准 NA 原因立即 STOP（沿用
   NA_UNAPPROVED_F4_MEDIAN_ZERO 的 fail-closed 范式）；该日不入参照集。
5. **Option B**：维持 nansum 现状（依赖上游 QA 挡 NaN）。
6. **影响方向**：当前数据集下两案数值完全相同（无 NaN volume 存在）；
   A 案在未来脏数据下 fail-closed，B 案静默低估 F4。样本/Primary 不变。
7. **main agent 推荐**：**Option A**——与"清洗必须事件化、异常必须 STOP"
   的项目纪律同构；且因当前零影响，落地无重跑成本。
8. **阻塞**：不阻塞 M5 硬化；须在首次真实 S0 前批。
9. **涉及文件**：context.py、s0_input_preflight.py（同步修＋各一测试）。
10. **问题**：批 A 还是 B？
