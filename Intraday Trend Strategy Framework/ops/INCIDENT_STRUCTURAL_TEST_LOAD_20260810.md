# INCIDENT — 测试进程结构性加载真实 Development 档案（2026-08-10）

## 事实
S0-closeout 集成中段，`RealChain.prepare` 接入 F-1 快照物化后（配置自此可解析），
两次未打 hermetic 补丁的 `tests/test_m6_chain.py` 运行越过旧 Stage-B 拒绝点，经
`RealChain._ensure → DevelopmentSignalLoader.load_real` 对
`C:\Users\Aaron\quant-data\databento-archive\intraday-trend\development_signal\`
发起**结构性 bar 加载**。两次均由主代理发现并 taskkill 终止（进程内存分别
~1.1GB / ~687MB；持续数分钟）。

## 定性
- 结构性加载（bar 解码入内存）；**无任何 Oracle/收益/标签/EV 数值被计算完成、
  查看或打印**（两次运行均止于进度点＋2 个失败字母，未达断言输出）。
- `EXPOSURE_LEDGER.md` 处置 = **pending Aaron**：Fable proposal = 不追加
  （台账语义为"查看过的候选关系"，Charter 条款 13，本事件为零；理由在
  IR-28d）。Aaron 明示批准前不构成定案。
- trial 无涉：非授权运行路径，S0-T001 未触碰。

## 永久防护
`tests/conftest.py` autouse 夹具：任何测试对真实档案路径调用 `load_real`
立即 RuntimeError（窄域，合成 tmp 路径不受影响）；对全部收集测试生效。

## 程序性记录（口令豁免 = pending Aaron）
PHASE-C 精确口令豁免与本事件均在 `CODEX_REVIEW_PACKET_S0_CLOSEOUT_FINAL.md`
§0 向 Aaron 与 Codex 全文披露；Codex 终审将两者列为需 Aaron 裁决项；Aaron 随后
指示（逐字）"你审核gpt的结论……你替我研究以及做决定"——该继续指令与委托已逐字入档；**豁免与追认是否成立由 Aaron 明示裁定
（pending），不以推断代替**。相关提案见 IR-28（全部
PENDING_AARON_RATIFICATION）。
