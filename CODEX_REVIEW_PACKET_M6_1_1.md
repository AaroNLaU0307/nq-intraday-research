# CODEX_REVIEW_PACKET — M6.1.1（供 Codex 独立检查真实仓库）

- 审查对象：本 packet 所在 commit（`git log -1` 取；单一候选，自 4dcff169）
- 状态不变量：**未追加 READY、未申授权、真实 S0 锁定、registry 未动、
  零真实研究数字**（RealChain._ensure 全程未被调用，审计实证）

## CLOSED（本轮闭合，Opus 十项反例全红＋A-F 全过后再闭 1 Med＋4 Low）

| 项 | 内容 |
|---|---|
| 封存正式性 | S1：真实生产形状 fixture；θ 轴精确对；day_universe 守恒旗全 True 门；E1/E2×4 无条件矩阵；A1 structural 七键；governance 上下文交叉校验（expected_governance 必供、封存时独立二次派生）；manifest 注入后二次全量校验；sealed-file 八键集/三重计数/逐行字段集与 engine-scenario 一致性/日期唯一/日期集==TP∪FP（缺失/多余/替换均红） |
| 方法单源 | StudyConfig 只能经 derive_study_config 派生（__post_init__ 强制，直接构造同样拒绝——LOW-1）；pending 全部从 ResolvedS0Methods 结构化七字段派生；生产路径拒 test_only；MED-1 机器断言：resolved 字段无接线消费者即红（ruling+consumer+map 同 commit 强制） |
| handoff/守恒 | 冻结 F10 词表强制；θ 嵌套单调；TP/FP 对调红；run_meta 校验；replay 三工件重建实证；JSONL 无尾换行行数真 bug 修复；allocate 守恒 raise；空 strata 不可封存（LOW-3） |
| seed/RNG | resample_means/build_worlds 补守卫；四入口拒 20260731 与任意非冻结集（实证）；bare assert 治理门清除 |
| scanner | production_import_closure（ast 传递闭包）：mc/bootstrap 在内、account/orchestrator 在外；未跟踪文件入扫；E4 过时声明删除并如实重述；隔离仓变异实证 |
| E7 | 生产 builder 于 Stage C 内调用（计数器证零预计算）；真实 Stage-D integrity；Stage-B 拒绝零 exposure 无 RUN_STARTED 无 runs 目录；D/E 失败均无 COMPLETED；_expected_governance 独立性测试（LOW-2） |
| none_or_na | 正式 builder 移除；None 事件无裁决映射即显式 DR-M6-F raise |

## 仍待 Aaron 的 DECISION_REQUIRED（全份见 DECISION_REQUIRED_M6_1.md，M6.1.1-r2 修订）

DR-1 spread 归约＋IR-7 定稿（Sol=B 族/IR-7 i 主+ii 敏感，Fable 同）；
DR-2 vol 逐字子定义（21 closes、精确排期最后一分钟 bar close）；
DR-3 FP 分层基准（**unresolved_disagreement：Fable B / Sol A**）；
DR-4 bootstrap 七分项（D4.1-D4.7）；DR-5 网格 K（unique draws vs 全组合
evaluations 分列，θ 计入）；DR-6 event NA 词表（TEST_ONLY five_stratum
残留已披露）；DR-7=DR-M6-G stability 总体（荐双报）。四个 §10.1 扩展
record 字段授权核查=全有冻结出处（§8:148/§10.1:167/180），非扩展。

## 未接线骨架（如实披露，非声称已接）

- formal_sealable 三工件旗（day_strata/grid_samples/seed_manifest）：
  今日恒 False、无 Stage-E 消费者；DR-M6-E/F 闭后随契约条款接线。
- 六个结构化方法字段（除 event_na_mapping）今日无消费者——被 MED-1
  机器断言看守，裁决日必须同 commit 接线。
- DAY_STRATA/GRID_SAMPLES 未入封存文件集（SEED_MANIFEST 已入）；
  replay 测试为单层 fixture（DR-B/F 未裁前无真实层键，docstring 披露）。

## 验证主张（Codex 复算点）

pytest **782/0/0** == 地板 == 钉；扫描 CLEAN（import-closure＋未跟踪）；
冻结哈希 7/7；git diff --check 净；packet §0 哈希全部当前
（入口 b92d58fe/contracts 2638bb23/report 340a68b2/handoff f347f41e/
stability e7bca9fe）；Opus 审计末态字节同一实证。
