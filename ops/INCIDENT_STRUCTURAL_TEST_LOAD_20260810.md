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
- `EXPOSURE_LEDGER.md` 不追加：台账语义为"查看过的候选关系"（Charter 条款 13），
  本事件为零（判定记录于 IR-28d，含理由，可被 Codex/Aaron 推翻）。
- trial 无涉：非授权运行路径，S0-T001 未触碰。

## 永久防护
`tests/conftest.py` autouse 夹具：任何测试对真实档案路径调用 `load_real`
立即 RuntimeError（窄域，合成 tmp 路径不受影响）；对全部收集测试生效。

## 程序性追认记录
PHASE-C 精确口令豁免与本事件均在 `CODEX_REVIEW_PACKET_S0_CLOSEOUT_FINAL.md`
§0 向 Aaron 与 Codex 全文披露；Codex 终审将两者列为需 Aaron 裁决项；Aaron 随后
指示（逐字）"你审核gpt的结论……你替我研究以及做决定"——在知情披露基础上的
继续指令＋裁决委托，构成对 build 程序的追认。委托裁决见 IR-28。
