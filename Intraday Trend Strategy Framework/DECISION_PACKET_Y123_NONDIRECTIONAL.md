# DECISION PACKET — Y1/Y2/Y3 在非方向日被强制 NA（SA-6 F-17）

状态：PENDING_AARON_AND_CHATGPT_APPROVAL（来源：SA-6 对抗审计）

1. **问题**：labels.py 在 d_open==0 时返回全空标签（M1 期"main-agent
   instruction"），但冻结 L87-89 的 Y1=(C1544−O1000)/ADR14、Y2=de_pm、
   Y3=close_pos_pm **不依赖方向**；L45 说 NA 只给"算不出"的量。
2. **冻结章节**：行 86-91（标签表）；行 45（NA 政策）；行 82（L82 单列
   计数）。
3. **事实**（SA-6 实测口径）：现实现白丢 26 个零方向日的 Y1/Y2/Y3 与
   14 个 ADR warm-up 日的 Y2/Y3（后二者连 ADR14 都不需要）。Y_cont/Y4/
   Y5 依赖 d_open，非方向日 NA 正确。已在 label_anchor_availability 中
   披露但无 IR 记录。
4. **Option A**：非方向日照冻结公式计算 Y1/Y2/Y3（Y2/Y3 在 ADR warm-up
   日也算，因不需 ADR14）；Y_cont/Y4/Y5 维持 NA（reason 分别为
   zero_direction_day_l82 / direction_undeterminable_na）。
5. **Option B**：维持现状（全 NA），以 IR 形式把"非方向日整行标签 NA"
   固化为口径。
6. **影响方向**：仅描述性标签覆盖（Y1-Y3 是描述用途，冻结明示不进
   Oracle 方向）；样本、Y_cont、判决不变。A 案 +40 天描述覆盖且更贴
   冻结字面；B 案实现更简单但需 IR 背书其偏离。
7. **main agent 推荐**：**Option A**（冻结字面即如此；"NA 只给算不出的
   量"是已批准原则）。需改 labels.py（REPLACE_PROHIBITED 解锁须你明示
   批准该单点）＋dataset 归因逻辑＋测试。
8. **阻塞**：不阻塞硬化；须在首次真实 S0 前批（影响正式报告的描述表）。
9. **涉及文件**：labels.py（单点）、dataset.py、test_labels/test_s0_dataset。
10. **问题**：批 A（含 labels.py 单点解锁）还是 B（出 IR 固化现状）？
