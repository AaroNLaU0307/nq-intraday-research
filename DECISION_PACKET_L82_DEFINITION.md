# DECISION PACKET — L82 零方向类的判定基准（SA-6 F-25）

状态：PENDING_AARON_AND_CHATGPT_APPROVAL（来源：SA-6 对抗审计）

1. **问题**：冻结 L82 以 `ret_open30 == 0` 定义零方向日；现实现（dataset
   与已批 preflight 同口径）以"双锚点存在且 C0959==O0930"判定——差异仅
   出现在"锚点相等**且** ADR14 不可用"的日子：原文口径下 ret_open30 为
   NA（非 0），现口径判为 L82。
2. **冻结章节**：行 82；行 45。
3. **事实**（SA-6 实证）：当前输入集上 26 个 L82 日 ∩ 14 个 warm-up 日
   = **∅**——两种口径完全重合，零数值差；优先级规则目前只写在 docstring。
4. **Option A**：维持现口径（锚点相等即 L82，不论 ADR），以 IR 固化：
   "价格事实（开收相等）优先于归一化可用性"。
5. **Option B**：改为字面口径（ret_open30==0 才 L82；warm-up 期锚点相等
   日归 direction_undeterminable_na）。
6. **影响方向**：当前数据零差异；未来若出现"warm-up 期开收相等日"，
   A 案计入 L82 频率统计、B 案计入 undeterminable。仅分类归属，样本、
   Y_cont、判决不变。
7. **main agent 推荐**：**Option A＋IR 固化**——"市场开收相等"是价格
   事实，不因归一化分母缺席而改性；且与已批 preflight 连续。
8. **阻塞**：不阻塞；须在首次真实 S0 前批（分类进正式频率表）。
9. **涉及文件**：仅 IR 记录＋一个 runtime 披露计数器（防未来数据修订
   静默重分类）＋docstring 升格引用 IR。
10. **问题**：批 A（IR 固化现口径）还是 B（改字面口径）？
