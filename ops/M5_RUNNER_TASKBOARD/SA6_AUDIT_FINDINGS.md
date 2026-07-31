# SA-6 对抗审计结果（只读；基线 f67d3bb；347 tests 复跑通过）

files_modified: none（前后 git status 均空）。real_s0_not_run: true。
公式忠实性抽查 **18/18 FAITHFUL，零静默偏离**；无前视 PASS（仅两项冻结
本身规定的披露例外：is_roll_window 前 2 日、L44 资格用全日数据）；
NA 归因 PASS（构造不出 L82 与 undeterminable 合并路径）但有一条静默吞
NA 路径（F-15）；**exposure / leak / override 三项 FAIL**。

## CRITICAL

- **F-01** s0_real_run.py g_authorized：`"RUN_AUTHORIZED" in 全文` 被
  registry 的**规则散文**满足（实测 7 门中 6 门当下已过，仅剩 HEAD 子串
  一层）；门 13（精确语句）未实现。修法：解析事件表，要求 event 列
  恰为 RUN_AUTHORIZED、note 含逐字 §10 语句、命名 40 位 hash 与 HEAD
  全等。
- **F-02** compute 占位符在**原子转换之后**抛错→若 A/B 全过将烧掉
  S0-T001 与 exposure 而零产出。修法：占位挪为 Stage-B 门
  `stage_c_wiring_activated`（PRE_RUN 失败）。

## HIGH

- **F-03** 授权流程不可满足（追加事件脏树/换 HEAD 无限回归；.gitignore
  不含 attempts|runs|registry→同 commit 只能尝试一次，违 §3 重试语义）。
  修法：clean 检查白名单化＋授权凭据独立工件。
- **F-04** 日志守卫**完全未接线**（validate_log_event 零非测试调用方；
  且 runner 现有消息全都过不了白名单——接上就全崩）。修法：消息改
  schema 化＋包装注入 logger。
- **F-05** 失败路径未过滤：原始异常文本进 RUN_FAILURE 报告与**入 git 的
  registry**。修法：失败文本过守卫或降为错误类＋不透明 incident id。
- **F-06** runinfra 四大机件（manifest 链/verify/NA 守恒/断言比对）
  **零非测试调用方**——§5/§6/§7 义务在真实 runner 里全是死代码。
- **F-07** 13 门只实现 7：缺 seal_check、structure assertions、精确语句；
  LOCKED 缺 A1 manifest（d8d1edc7）、raw_file_set（08fca11b）、
  preflight json（5c0ae2d7）→ 断言文件本身未被 hash 锁。
- **F-08** runs 目录带秒级时间戳→"必须不存在"检查形同虚设；RUN_STARTED
  追加失败留**无标记孤儿目录**。修法：HALF_TRANSITION 标记＋按 trial id
  扫描 runs/。
- **F-09** 环境覆盖：PYTEST_ADDOPTS 可缩 pytest 门；GIT_DIR 族可骗
  clean/HEAD 门。修法：子进程洗净 env＋断言收集数。
- **F-10** Stage A/B 门抛异常未包裹→裸 traceback，无失败报告无 registry
  事件（正是 §8 要防的路径）。
- **F-11** authorized_commit 填 HEAD 而非语句解析值（契约语义违背）。

## MEDIUM（工程）

- **F-13** check_na_conservation 的 approved_reasons 可被调用方覆盖；
  reported_total_na 可省略→半检查。修法：删参数＋必填。
- **F-14** preflight json 与 contracts 词表/形状不一致（5 个词不同、
  funnel 10 键 vs 5 数、adr14 字段多出）→ 比对器需翻译层（现缺）。
- **F-16** context 边界无时区断言（UTC 输入静默平移窗口）。
- **F-18** dataset 的 DEV_START/END 导入后未用（假保证）。
- **F-19** 冻结常数为运行时可重绑模块全局；pin 测试在别的进程。修法：
  Stage-A 门在 runner 自身解释器内复核常数。
- **F-20** 守卫数字白名单弱（records=任意整数；文件名可夹带
  base_rate_0_63；词表缺 theta/base_rate/adr/rvol/gap/retrace/funnel）。

## MEDIUM（方法决策→已出包）

- **F-15** NaN volume 经 np.nansum 变 0.0（非 NA！）且 0 值日可进 IR-20
  参照集污染中位数——与已批 preflight 同源缺陷。
  → DECISION_PACKET_F4_NAN_VOLUME.md
- **F-17** d_open==0 日 Y1/Y2/Y3 被强制 NA，但冻结 L87-89 三者不依赖
  方向（白丢 14 warm-up 日 Y2/Y3 与 26 零方向日 Y1/Y2/Y3 的描述值）。
  → DECISION_PACKET_Y123_NONDIRECTIONAL.md
- **F-25** L82 类以"双锚点存在且相等"而非冻结原文 `ret_open30==0` 定义
  （当前输入集上二者重合=∅交集，实证无差；但优先级规则只活在
  docstring）。→ DECISION_PACKET_L82_DEFINITION.md
- **F-12** f10 双报缺 raw membership 结构（已批治理要求，工程补齐项）。

## LOW/NOTE（择要）

F-21 roll_window 缺 Oracle 隔离测试；F-22 Y6 隔离测试未来模块盲区；
F-23 前视测试未覆盖 roll/event/同日盘后；F-26 verify_chain 不要求每
阶段有 seal＋corrupt tail 抛错类型；F-27 exc_type 从 detail 解析可伪装；
F-28 labels_table decile 变 float64；F-29 重复分钟检查仅 RTH；F-30 隔夜
块 NaN 静默丢块；F-31 inside_official_interval 不 gate；F-32 IR-16 与
L30-32 需最终包一句 reconciliation；F-33 行数列为非空行口径（哈希全对）；
F-34 runner 未调 assert_real_run_allowed（双实现漂移险）。

## 测试有效性抽查

方向分离/IR-19 不跳过/Y6 ties 等关键测试**真的能抓错**；但
test_y6_no_date_or_index_tiebreak_in_source 第二断言 `... or True` 半虚；
守卫 40 测试单元有效但无一断言 runner 接线；零参测试不查 env 读取。
