# M5_T1_T2_INTEGRATION_REPORT

重建式集成审计：两个因**月度消费上限**中止（账务事件，2026-07-31，均死于
"正写测试"节点）而未能提交正式 RETURN 的 subagent 交付记录。main agent
逐文件重建验收。真实 S0 未运行；无真实数据读取。

## 1. 变更清单（git name-status，0554a94..945938a）

```
A  DECISION_PACKET_S0CORE_Y6_DECILE.md   （main agent 补写）
A  src/itsf/s0/context.py                （SA-4）
A  src/itsf/s0/dataset.py                （SA-4）
M  src/itsf/s0/features.py               （SA-4，批准单点）
A  src/itsf/s0/runinfra.py               （SA-5）
A  tests/test_runinfra.py                （SA-5）
A  tests/test_s0_context.py              （SA-4）
A  tests/test_s0_dataset.py              （main agent 补写）
```
后续 IR-21 收口 commit（本报告所在）在此范围之外追加：dataset.py Y6 规则
定稿、test_s0_dataset.py 八项 IR-21 测试、IMPLEMENTATION_RESOLUTIONS.md、
本报告。

## 2. 文件 SHA-256（16 位前缀）与行数（IR-21 定稿后状态）

| 文件 | sha256 前缀 | 行数 |
|---|---|---|
| src/itsf/s0/context.py | f926ae40948c0acc | 837 |
| src/itsf/s0/dataset.py | 9e72e2a04b42d224* | 567 |
| src/itsf/s0/runinfra.py | 170fabb2ae758d1a | 716 |
| src/itsf/s0/features.py | a5e222f679731640 | 141 |
| tests/test_s0_context.py | f6d973d1c261041e | 611 |
| tests/test_s0_dataset.py | 16ebfc7dc2f8b485* | 272 |
| tests/test_runinfra.py | a036b034cd599e39 | 424 |

（* 标注文件在本 commit 内因 IR-21 与注释清理再次变更；最终哈希以本
commit 的 git blob 为准。）

## 3. 内容归属

- **SA-4 落盘**：context.py 全部（837 行）；dataset.py 主体（除 Y6 段）；
  features.py 单点；test_s0_context.py（608 行原稿）。
- **SA-5 落盘**：runinfra.py 全部；test_runinfra.py 全部（40 测试矩阵，
  实际已完整，含"绝不读 preflight 文件"的 monkeypatch 验证）。
- **main agent 补写/修复**：4 个机械测试缺陷（2 个星期索引、模块纯度
  MappingProxyType/import-del、自指字符串）；1 个设计期 fixture 缺陷
  （warm-up 期内断言 on_range 可算）；test_s0_dataset.py 全部（14→20
  测试，含方向语义分离硬测试与 IR-21 八项）；Y6 决策包补写；IR-21
  批复后的 assign_y6_deciles 重写（average-rank、禁 tie-break、
  n_year=1 极限披露）、convention 参数整体移除、Y6 NA 原因继承与
  赋值后 fail-closed 覆盖复检。

## 4. 禁改文件零改动证明

`git diff 0554a94..945938a -- labels.py oracle.py costs.py paths.py
contracts.py __init__.py` → **0 行**。IR-21 collision 亦未触碰上述文件
（本 commit 只改 dataset.py 与测试）。

## 5. features.py 单点性

范围内唯一 diff = `event_flag: str → str | None` ＋校验放行 None（IR-12/
18 的 F10=NA），含"这是唯一获批改动"的注释。无其他行变更（diff 全文
已在 945938a commit 前由 main agent 目验）。

## 6. context.py / dataset.py 纯计算证明

非注释行扫描 `open(|read_text|read_csv|to_csv|urllib|requests|
os.environ|getenv|print(|quant-data|load_real` → **零命中**。零文件
I/O、零网络、零环境变量、零真实 loader 调用、零 print。事件表/映射/
排期全部经注入参数（EventCalendar/RollInterval/SessionSchedule 均为
frozen dataclass，"INJECTED (no file access here)"）。

## 7. runinfra.py I/O 边界

全模块 `open(|write_text|write_bytes|to_csv|mkdir` 命中 4 处，函数归属
机器核对：line 386/404 → `append_manifest_record`（读尾部取 prev-hash
后追加——同一批准适配函数的职责）；line 831/832 →
`write_failure_report`。**恰好两个批准的窄 I/O 适配函数，无第三个
写路径**；不创建目录（mkdir 零命中）。

## 8. 未完成痕迹扫描

六个新文件扫 `TODO|FIXME|NotImplementedError|pytest.skip|xfail|PENDING`：
仅 dataset.py 残留 1 行 pre-IR-21 的 "PENDING decision packet" 注释
（本 commit 已清，Y6 已按 IR-21 定稿）＋ `pending_decisions` 机制字段
（合法治理机制，当前恒为空 tuple，测试断言之）。无任何 skip/xfail/
NotImplementedError/隐藏默认 policy。

## 9. 公式出处映射（Aaron 要求的九项）

| 项 | 实现处 | 冻结出处 |
|---|---|---|
| ADR14 | context.py（滚动，前 14 完整 RTH 日不含当日） | 行 49＋L44 完整日定义 |
| F4 参照集 | context.py F4_LOOKBACK_DAYS=60＋IR-20 basis（含半日市、早盘 30 根完整） | 行 56＋IR-20 |
| F5 前收盘 | context.py SessionSchedule.final-scheduled-bar＋vendor 不跳过 | 行 57＋IR-19 |
| F10 编码 | context.py EventCalendar（92 预定 statement 日；IR-13 后判冲突→None） | 行 62＋IR-12/13/18 |
| F11 roll | context.py RollInterval→首个有效 RTH session date；窗前后 2 日 | 行 30-32＋IR-16 |
| 隔夜窗 | context.py OVERNIGHT_START_MINUTE=18:00→09:30 | 行 43 |
| Y6 | dataset.assign_y6_deciles（average-rank decile；ties 同箱） | 行 91＋IR-21 |
| LOYO | dataset._groups（leave-one-year-out 分组结构） | 行 36 |
| 两时代轴 | context.MICRO_ERA_BOUNDARY=2019-05-06；dataset._era | 行 109-115 |

（features.py 内 F1-F9 公式注释逐条含 "frozen: S0 SS4 F<n>"，M1 期已
审计，本范围零改动。）

## 10. 无真实数据/无研究数字证明

- 两份测试文件自扫描断言不含真实归档路径（拼接式防自指）；
- 全部 338 测试运行于合成 fixture（生成器契约写在 test_s0_context.py
  文件头，每个 golden 数值附手算推导）；
- 本轮无任何 quant-data 读取（模块层面机器证明见 §6；测试层面见上）；
- 产生的数值均为合成 golden 值，无真实研究数字。

## Y6 前视信息说明（Aaron 特别检查点）

Y6 使用整年数据，对年内较早日期带有"未来标签信息"——**允许**，因其为
描述性标签；机器保证不回流：`test_y6_cannot_enter_oracle_or_candidate_
paths` 逐函数 inspect 检查 oracle/costs/paths/features 的签名与源码
（零 "y6" 引用），并断言 `oracle_candidate ≡ (d_open≠0 ∧ Y_cont 非 NA)`
与 Y6 无关。

## unresolved 与决策包清单

- DECISION_PACKET_S0CORE_Y6_DECILE.md → **已由 IR-21 裁决关闭**（修订版
  Option A：average-rank）；
- 无其他未决决策包；无 unresolved 事项。
- 机械边界披露：IR-21 公式在 n_year=1 时按极限 pr=0→decile 1（代码
  注释＋本报告披露）。

## 结论

SA-4/SA-5 中止交付经重建审计全部验收；main agent 补写部分归属明晰；
禁改文件零触碰；纯度/边界/痕迹三类扫描干净；IR-21 落档并以 8 项专项
测试固化。**未发现第二个决策包 → 满足 Aaron 定义的 M5-T3 启动条件。**
