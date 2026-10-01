DISPATCH: 建议模型 = Claude Sonnet 5（claude-sonnet-5），effort = high。
理由：接口已由 main agent 完全定稿、11 条测试逐条具名，歧义度低，属
"照规格实现"型任务；guard 代码正确性由测试矩阵＋main agent 集成审查
双重兜底。不需要浏览器。可与 SA-1 并行。

SUBAGENT TASK ID: M4-T2 / SA-2
TASK NAME: Development 数据硬边界修复＋数据角色强类型化
ROLE: 数据治理工程师（fail-closed 纪律）
OBJECTIVE: 把 Development loader 的错误上界 2025-07-01 修正为冻结边界
2022-01-01(exclusive)，用强类型枚举固化数据角色，使 IV 段数据在任何路径下
都无法被加载，并按指定的八条边界测试全部落地。

项目背景（自包含）：
- 仓库：C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\
- 冻结事实（STUDY_0_PREREGISTRATION.md 行 24-26；purchase_plan.yaml A1 块）：
  Development = NQ.v.0 ohlcv-1m，2010-06-06 → 2022-01-01(excl)；
  Internal Validation = 2022-01-01 → 2025-07-01(excl)，不采购、不上机、
  S0 不得访问；Execution Cost Calibration = MNQ bbo-1s 2025-01-01 →
  2025-04-01(excl)，只出 spread 表。
- 已确认 bug：src/itsf/data/dbn_loader.py:29 `DEV_END_EXCLUSIVE = "2025-07-01"`，
  其注释错误援引 purchase_plan A1（实为 IV 段终点）。本地 A1 归档只含
  2010-06..2021-12 文件，故此 bug 尚未造成实际越界读取，但边界必须硬化。

REQUIRED READING:
- STUDY_0_PREREGISTRATION.md 行 24-32（数据角色表）
- purchase_plan.yaml 中 A1/A2/A3 的 data_role 与窗口块
- PROJECT_CHARTER.md 数据角色隔离条款
- src/itsf/data/dbn_loader.py、src/itsf/data/cost_calibration_loader.py、
  src/itsf/data/manifests.py、src/itsf/data/validation.py 全文
- tests/test_loader.py 全文（现有 guard/role/boundary 测试的写法与 fixture）
- ops/M4_TASKBOARD/TASKBOARD.md 中 SA-2 接口定义

ALLOWED FILES:
- src/itsf/data/roles.py（新建）
- src/itsf/data/dbn_loader.py
- src/itsf/data/cost_calibration_loader.py（仅接入 DataRole 枚举所需的最小改动）
- tests/test_dev_boundary.py（新建）
- tests/test_loader.py（仅修正 :263 处测错误边界的用例＋必要追加）

FORBIDDEN FILES:
- 所有冻结文件（PROJECT_CHARTER.md、STUDY_0_PREREGISTRATION.md、
  purchase_plan.yaml、MC_METHOD_SPEC.md、gate1/platform_params.yaml）；
  FREEZE_LOG.md；git tag/历史；src/itsf/guards.py；src/itsf/mc/**；
  scripts/**（含 render_qa_addendum.py——其中 :384 的错误描述由 main agent
  走 Addendum 勘误流程，你不要动）；DATA_QA_REPORT.md；DATA_QA_ADDENDUM.md；
  qa_addendum_*.json；spread_cost_table.csv；ops/**。

INPUTS: 上述现有代码与冻结文本。
OUTPUTS: 修改后的 loader/roles/tests；全部测试绿。

INTERFACES（main agent 已定稿，照此实现，不得自行更改）:
```python
# src/itsf/data/roles.py —— 文件头注释必须逐条引用冻结出处
from enum import Enum

class DataRole(str, Enum):
    DEVELOPMENT_SIGNAL = "development_signal"
    EXECUTION_COST_CALIBRATION = "execution_cost_calibration"
    INTERNAL_VALIDATION_SIGNAL = "internal_validation_signal"  # 永不可加载

ROLE_WINDOWS = {  # (start_inclusive, end_exclusive) — ISO 日期字符串
    DataRole.DEVELOPMENT_SIGNAL: ("2010-06-06", "2022-01-01"),
    DataRole.EXECUTION_COST_CALIBRATION: ("2025-01-01", "2025-04-01"),
}
# INTERNAL_VALIDATION_SIGNAL 故意不在 ROLE_WINDOWS：任何加载尝试必须
# 在窗口查询处直接 RoleError（fail-closed，而非 KeyError 泄漏）。
```
- DevelopmentSignalLoader / CostCalibrationLoader 对外签名不变
  （load_real(filename, source_format) / build_spread_table_*）。
- 边界为模块级冻结常量，禁止通过构造参数、方法参数、环境变量、
  monkeypatch 之外的任何运行时手段放宽；构造器不得新增边界参数。
- 角色判定改为：job_dir 路径必须包含本 loader 的 DataRole.value 且不得
  包含其他任何 DataRole.value（防 "development_signal/../internal_validation"
  之类混合路径）；不匹配一律 RoleError。
- 时间戳边界检查保持"先 guard、再角色、再 manifest、再解码、再范围"的
  fail-closed 顺序；范围检查为整文件判定：min < start 或 max >= end 一律
  ValidationError 整文件拒绝，禁止截断或过滤行。

IMPLEMENTATION REQUIREMENTS:
1. dbn_loader.py：DEV_END_EXCLUSIVE 改为取自 roles.ROLE_WINDOWS；修正错误
   注释（正确出处：预注册 §1 行 24 + purchase_plan A1 end 2022-01-01）。
2. cost_calibration_loader.py：ROLE_DIRNAME 字符串改为 DataRole 枚举来源；
   行为不变；MNQ launch 边界检查保留。
3. 不改 guards、不改任何公共 API 名称；Alpha 隔离测试
   （test_alpha_cannot_obtain_raw_bbo 等）必须保持通过。
4. 修 tests/test_loader.py:263：该用例现在用 2025-07-01 测上界，改为
   2022-01-01 拒绝＋2021-12-31 允许两个方向都测。

REQUIRED TESTS（tests/test_dev_boundary.py，具名落地以下全部）:
1. 2010-06-06 当日数据允许；
2. 2021-12-31 当日数据允许；
3. 2022-01-01 当日数据拒绝（ValidationError，整文件）；
4. 2025 年时间戳文件拒绝；
5. manifest hash 正确但目录角色错误 → RoleError（hash 对不豁免角色）；
6. 文件名/目录伪装成 development_signal 但内部时间戳进入 IV → 整文件拒绝；
7. 跨边界单文件（部分 2021-12、部分 2022-01）→ 整文件拒绝，断言输出中
   不存在任何被"截断保留"的行；
8. synthetic 入口（load_synthetic）保持可测且同样受范围检查约束；
9. 构造器/方法不存在任何可放宽边界的参数（用 inspect.signature 断言）；
10. INTERNAL_VALIDATION_SIGNAL 任何加载路径 RoleError；
11. development 目录传给 CostCalibrationLoader、cost 目录传给
    DevelopmentSignalLoader 均拒绝。
全套跑 `python -m pytest tests -q`，基线 174 全绿之上只增不破。

EVIDENCE REQUIREMENTS: 返回中附 pytest 末行输出；列出每个修改文件的
diff 概要；确认三处 2025-07-01 引用中你只处理了 loader 与 tests 两处
（scripts/render_qa_addendum.py:384 留给 main agent）。

STOP CONDITIONS（满足任一立即停止上交）:
- 发现冻结规范与代码存在本任务范围之外的其他边界冲突（明确要求：停止
  上交，不得顺手修）；
- 遇到方法歧义；需要修改共享接口（含对 INTERFACES 一节的任何偏离）；
- 需要改变冻结规则；官方证据冲突；超出文件所有权；
- 发现可能影响 Primary 的未批准选择。

禁止：
- 创建其他 subagent；修改冻结文件；创建最终 commit（工作区变更可以，
  集成 commit 归 main agent）；运行真实 S0（测试只用合成 fixture，不得
  读取 C:\Users\Aaron\quant-data 下任何真实文件）；输出策略数字。

RETURN FORMAT:
- files_read:
- files_modified:
- tests_run:
- test_results:（pytest 末行原文）
- evidence_added:
- unresolved:
- decisions_required:
- frozen_files_untouched: true/false
- real_s0_not_run: true/false
