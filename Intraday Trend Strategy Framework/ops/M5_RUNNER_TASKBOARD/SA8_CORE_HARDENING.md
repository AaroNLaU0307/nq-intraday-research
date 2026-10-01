DISPATCH: Opus 5 / high（评分：时区/交易日语义＋NA 传播 =2）。
SUBAGENT TASK ID: M5-T4c / SA-8 — context/dataset 工程硬化（SA-6 修复）
ROLE: 核心装配层硬化工程师。与 SA-7 并行，文件集合零交集。

必读：ops/M5_RUNNER_TASKBOARD/SA6_AUDIT_FINDINGS.md；
IMPLEMENTATION_RESOLUTIONS.md（"报告治理修正"(1) 双报要求）；
src/itsf/contracts.py。

ALLOWED FILES: src/itsf/s0/context.py、src/itsf/s0/dataset.py、
tests/test_s0_context.py、tests/test_s0_dataset.py。
FORBIDDEN: 其余一切（含 runner/runinfra/s0_real_run/labels/features/
contracts/冻结件）。

修复清单（逐项闭环并配测试）：
- F-12 dataset 增 raw_category_membership_counts 产出结构（与
  f10_exclusive_counts 并列双报；断言 membership≥exclusive 逐类）。
- F-16 context 边界时区断言：输入 ts 必须 tz-aware 且 ET
  （America/New_York），否则抛 ValueError（fail-closed）＋测试
  （UTC 输入必须炸）。
- F-18 dataset 的 DEV_START/END 假保证：改为 build_s0_dataset 内真实
  范围断言（records 日期均在 [DEV_START, DEV_END_EXCL)）＋测试。
- F-28 labels_table 的 y6 列保 Int64（nullable int）而非 float64。
- F-29 重复分钟 fail-closed 扩展到 evening/pre-open 块＋测试。
- F-30 隔夜块含 NaN high/low：从静默丢块改为记 context NA 原因
  overnight_window_empty 附注计数（不发明新 approved 原因——用现有
  overnight_window_empty，附 sidecar 计数披露）＋测试。
- F-31 RollTransition.inside_official_interval=False 时 fail-closed
  抛错（与 preflight 断言语义一致）＋测试。
- F-21 增 test_roll_window_cannot_enter_oracle_paths（比照 Y6 隔离测试）。
- F-22 Y6 隔离测试扩展到 itsf.s0 下除 dataset 外全部模块。
- F-23 前视测试增强：roll/event 标志扰动＋同日 09:59 后 bar 扰动不改
  特征。
- 修 test_y6_no_date_or_index_tiebreak_in_source 的 `... or True` 半虚
  断言（改为真实源码检查）。

禁触方法决策区（等 Aaron 批复，行为不得改）：F-15（nansum）、F-17
（Y1/Y2/Y3 非方向日 NA）、F-25（L82 口径）。
禁 git commit；不读真实数据；测试全合成；pytest 全量只增不破（基线
347，SA-7 并行可能使总数漂移——只对自己文件负责）。
RETURN FORMAT：同 SA-7。
