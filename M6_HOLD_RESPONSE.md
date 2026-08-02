# M6 HOLD 逐项回应（Fable → Codex/Sol，经 Aaron）

对象 commit：`08fca9bd47837489e7a84fcc4107f2fc7ce807b4`。
本文件零 S0 结果引用；方法域项一律只交立场与决策包，不落新定义。
状态标记：accepted_revision / rejected_revision / unresolved_disagreement。

## 1. resolved 态 ready/compute 不一致 — **accepted_revision**（fact_error［我方］＋engineering_gap）

Codex 正确：pending 清空后 `ready()` 返回 True 而 `compute()` 仍无条件
raise——Stage B 放行、Stage C 爆炸＝**烧号**。这是 resolved 态的第三类
自锁，性质与前两次事故同源（我在 fail-closed 姿态上只做了一半）。
修复计划（工程，不触方法）：
- 单一 `resolved_params()` provider：三项裁决落地后返回
  (spread_scalars, regime_of, fp_basis)；未落地返回 None；
- `ready()` 与 `compute()` 共用同一 provider——ready 的判定即
  compute 的前置条件（探测同一对象，不再各表）；
- compute 接 `build_full_study_result(ds, self._bars, **provider())`；
- resolved 态 e2e：monkeypatch 清空 pendings＋注入合成 provider，断言
  `ready()==True ⇒ compute() 成功` 且走完 render（合成市场，永不触
  真实档案）；再加不变量测试：ready ok 时 compute 禁止抛 wiring 类错。

## 2. 契约四缺口 — **accepted_revision**（engineering_gap ×4）

- **绕过**：渲染器对无 "study" 的 payload 走 legacy 路径直接封存＝契约
  可绕过。修复：Stage E 封存路径删除 legacy 分支——无 "study" 即拒。
- **oracle_daily→study 漂移**：契约 A 键名与 payload 顶层键不一一对应
  （A2 oracle_daily 等实际藏在 study.per_theta 内）。修复：payload 顶层
  按契约 A 键逐一铺开，validator 按 A 键矩阵字面校验（doc↔code 同构）。
- **A12 缺失**：governance 块缺 authorized_commit、engineering_seed
  实值、冻结哈希七项复述、registry 快照。修复：补全并入 validator。
- **default=str ＋ n_boot=40 可封存**：json 序列化改严格 encoder（未知
  类型 raise，不静默字符串化）；validator 逐胞强制
  `n_boot == 10000`（FROZEN_N_BOOT）与块长 ∈ {5,21}。

## 3. 冻结 §2 稳定性视图缺席 — **accepted_revision**（engineering_gap；定义已冻结无歧义）

§2 原文强制：时代切片 **2010–2013 / 2014–2017 / 2018–2021**、按年表格、
leave-one-year-out、**多空分开**、20 日实现波动率三分位。完整映射：

| §2 轴 | study 落点 | 契约节 | validator |
|---|---|---|---|
| 三时代 | oracle_daily/频率聚合按 ds.groups.stability_epochs 切片 | A2b.stability_views.epochs | 3 胞全存在 |
| 按年（强制） | 同上 by_year | A2b.by_year | 年数=样本年数 |
| LOYO | 同上 leave_one_year_out | A2b.loyo | 同上 |
| 多空 | 按 d_open ∈ {+1,−1} 分列（study 已存方向，纯切片） | A2b.by_direction | 2 胞 |
| 20 日实现波动率三分位 | 待第 5 项裁决后接入（分层键与 §2 轴同源） | A2b.vol_terciles | 3 胞＋NA 层 |

前四轴定义完备可径行实施；第五轴阻塞于第 5 项的子定义裁决。

## 4. DR-M6-A 重定义＋IR-7 定稿 — **accepted_revision（重定标）**（method_risk → Aaron 裁决包 DR-M6-A-v2）

承认原 DR-M6-A 定义不完整：须先定"逐分钟表如何成为每笔 entry/exit/
stop 的成本"，再谈标量归约。三机制精确化：
- **A（全 RTH slot 聚合）**：场景三标量 = RTH 570-959 slot 的
  median/P90/P95 聚合；每笔成本用场景常量（与冻结 §6 成交公式的
  "场景单一 spread_points"形状一致；QA 已发布同口径）。
- **B（交易窗聚合）**：同 A 但窗=600-944（entry/exit/stop 只发生在此
  窗；代表性更贴执行时段）。
- **C（fill-minute lookup）**：每笔按成交分钟查 slot 行取该场景分位。
  **我方警示**：冻结 §6 成交公式以场景常量 spread_points 定义
  entry/timed/stop fill；C 使 spread 变为分钟函数，改变冻结公式的参数
  形状——除非 Codex/Aaron 判定"时段中位"本意即逐分钟，否则 C 疑似
  越冻结字面。推荐 **B**（窗口与执行一致、保持场景常量形状）；A 为
  次选（与 QA 披露同源）。
- **IR-7 定稿草案**（同包合并裁决）：adverse_slippage_ticks 从"暂用=
  该场景 per-side"定稿为：Option i）维持 per-side 同值（现状转正）；
  Option ii）per-side＋1 tick（stop 成交更不利的保守层）。机制两者皆
  已支持（build_scenarios 的 override map）；推荐 ii（stop 场景的
  adverse 本性）。**只交 Aaron 定稿，不自落。**

## 5. DR-M6-B 撤回 — **accepted_revision（撤回原案）**（fact_error［我方］）

Codex 正确：冻结 §2 已含 **"20 日实现波动率三分位"**——我原提的
ADR14/F4 三选项与冻结文本冲突，**全部撤回**。替代案 DR-M6-B-v2
（Aaron 裁决包，逐字子定义）：
- trailing window：**严格早于 d 的最近 20 个实际 RTH 交易日**（提案）；
- return basis：RTH 官方收盘 close-to-close **简单收益**（提案；log 为
  备选）；
- lag：窗口终点 = d−1（无前视，与 F4/ADR 同款先例）；
- tercile reference：**全 Development 非 NA 分布一次性定界**（提案；
  备选=逐年定界，与"year×regime"轴正交性更强，两案并呈）；
- NA：不足 20 个先行观测或成分收盘缺失 → 该日 vol_na 层**单列**
  （不并入任何三分位、不剔除日，附录 A 分层含第四层 vol_na）。

## 6. DR-M6-C 机制论证 — **accepted_revision（荐 B，Aaron 裁）**（method_risk）

机制：真实分类器的 FP 与其 TP 源自相同特征空间区域——FP 层构成
**跟随 TP 构成**（B）模拟"层内混淆"的分类器；FP 按自身池构成（A）
等价于"分类器的错误与无条件非延续总体同分布"这一更弱假设。冻结
文本设"缺额再分配"规则而 A 下该规则不可达（SA-18 证明），立法意图
指向 B。若裁 B：**权重来源 = 该网格点实际选出的 TP 层构成**（逐点、
逐 seed）；**缺额守恒** = FP 总数 n_fp 不变，缺额按其余层 FP 可用量
比例再分配（冻结字面直接适用），并披露 realized FP 构成与 TP 构成的
逐层偏离。推荐 **B**。

## 7. Primary bootstrap 抽样总体 — **accepted_revision（采 Codex 读法，Aaron 裁）**（method_risk → DR-M6-D）

Codex 挑战成立：现接线只对 D_TP 子序列抽块——"期望块长 5 **交易日**"
的单位在冻结文本里是交易日；对 TP 子序列而言 5 个相邻元素可横跨数周，
依赖结构失真，且交易频率的不确定性被冻结在点值。**接受修订方向**：
Primary bootstrap 作用于**完整 Development 交易日序列**（非 oracle 日
P&L=0），块=连续交易日；统计量=全日均值（联合捕获频率×盈亏不确定
性，与 MC 月度 EV 直接同构）。诚实对价：统计量含义从"每 oracle 日
均值"变为"每交易日均值"，契约 A7 的口径说明须同步。反例检索：无——
我未找到支持 TP-子序列读法的冻结文字。**Aaron 裁决后落 IR。**

## 8. 附录 A K 次重复＋事件分层 — 两部分

- **事件层 "none_or_na" 合并 = fact_error［我方］，accepted_revision
  （工程径行修复）**：F10=NA（multi-event）依 IR-12/18 是独立类，与
  "none" 合并违已批词表。修复：事件层 = {CPI, NFP, FOMC, none,
  NA_multi_event} 精确词表（非新方法，系词表 conformance）。
- **K 政策 = method_risk → Aaron 裁决包 DR-M6-E**：冻结文本每
  (seed,q,r) 未定重复数；现实现=每 seed 单次抽取（3 draws/点）。提案:
  K=200/seed/点，repeat stream = `[master, GRID_TAG, q_mil, r_mil, k]`
  （SeedSequence 数组，确定性）；收敛 = K 与 2K 的 realized 统计量
  离散度对比（容差数值同包裁决）；跨 K 离散度全报告。

## 9. RNG API 硬化 — **accepted_revision**（engineering_gap ×4）

- `bootstrap_mean_ci`/`build_grid` 的 master_seeds 形参可被覆盖：改为
  校验 `master_seeds == contracts.RESEARCH_BOOTSTRAP_SEEDS` 不符即
  raise（保留形参仅为显式性）；
- mc/bootstrap.py:27 本地 `MASTER_SEEDS=(7,13,31)` 重复常量：改
  import contracts 单源＋一致性测试；
- grid seeds 未验证：同第一条统一校验；
- governance 块补 engineering_seed **实值**（见第 2 项 A12 修复）。

## 10. MC 交接可重建性 — **accepted_revision**（engineering_gap；内容锚定第 5/6/8 项裁决）

确认缺口：TradePathRecord（冻结 §10.1 schema，**不增字段**）不含
label/stratum——MC 无法仅凭 JSONL 重建 K 次 TP/FP 分层抽样。修复
设计：封存交接扩展为四件套（全部入 manifest＋sha256）：
1. MC_HANDOFF_<eng>_<scn>.jsonl（现有，§10.1 原子记录）；
2. **DAY_STRATA.json**：date → {era, year, event_flag（精确词表）,
   vol_tercile（第 5 项裁决后）, tp_fp_class per θ}——全部由冻结定义
   ＋已裁 IR 派生，属封存输出的一部分（非运行期泄漏）；
3. **GRID_SAMPLES.json**：gridmix 的逐点逐 seed（裁后逐 K）日标记
   序列＋realized 值＋stream 派生参数全披露；
4. SEED_MANIFEST：seeds、stream tags、K 政策、派生公式文本。
MC 侧凭 2+3+4 可完全重建或独立重放抽样。

## 汇总

| 项 | 标记 | 分类 |
|---|---|---|
| 1 | accepted_revision | fact_error（我方）＋engineering_gap |
| 2 | accepted_revision | engineering_gap |
| 3 | accepted_revision | engineering_gap（定义已冻结） |
| 4 | accepted_revision（重定标） | method_risk → DR-M6-A-v2＋IR-7 定稿包 |
| 5 | accepted_revision（撤回原案） | fact_error（我方）→ DR-M6-B-v2 |
| 6 | accepted_revision（荐 B） | method_risk → DR-M6-C |
| 7 | accepted_revision（采 Codex 读法） | method_risk → DR-M6-D |
| 8 | 事件层：accepted（工程）；K：method_risk → DR-M6-E |  |
| 9 | accepted_revision | engineering_gap |
| 10 | accepted_revision | engineering_gap（锚定 5/6/8 裁决） |

零 rejected_revision、零 unresolved_disagreement。工程批
（1/2/3 前四轴/8 事件层/9/10 骨架）待 Codex 确认本回应后作为 M6.1
实施；五个方法包（A-v2＋IR-7、B-v2、C、D、E）全部只等 Aaron 裁决。
真实 S0 保持锁定；本轮零代码改动、零真实数据读取。
