＃ P2 准备件 —— 你要签的那一行需要什么

```ini
RECORD_TYPE=PREPARATION（不是授权；本文件不追加任何行、不创建任何目录）
BY=Opus 5，builder seat，2026-08-31
STATUS=待 Aaron。P2 的 actor 必须是 Aaron，builder 不得代拟其内容
BASIS=P1 已追加（registry 仓 e53234e，序号 14）
```

---

## 1. 三件我说过要先量的，量完了

### 1.1 `output_root` 填哪一条 —— **不是 supplements 那一层**

门 `output_root_structure` 的判据是 `_norm(declared) == _norm(runs_root)`，
而 `supplements` 子层是 runner **自己拼**的：

```python
runs_parent = Path(runs_root) / SUPPLEMENTS_SUBDIR      # supplement_runner.py:214
runs_target = runs_parent / f"{supplement_id}_{utc_stamp}"
```

所以：

```
output_root  =  C:\Users\Aaron\quant-data\itsf-runs
```

**不是** `…\itsf-runs\supplements`。填后者会让该门拒绝 ——
**我原本会填错，因为「授权过的那两条路径」正是 supplements 那一层。**

### 1.2 运行目录谁建 —— 写入方，不需要额外的目录授权

生产路径里**没有任何 `mkdir`**（全 `src/itsf/mc/` 实测）。
`plan_supplement_paths` 只计算目标，且**目标已存在即拒绝**（`plan_target_exists`）。
真正创建它的是写入方，在落盘那一刻：

```
src/itsf/mc/day_strata_supplement.py:398   out.mkdir(parents=True, exist_ok=True)
```

两条父层 08-29 已授权、实测**都存在且为空**。

**但有一条我不替你判**：per-run 目录落在已授权的 supplements 之下，
而那次授权写着「用掉即失效」。**它算不算被 P2 的执行授权本身覆盖？**
我倾向算（P2 授权执行，执行会建它），**而这个判断对我有利**——
所以列在这里给你，不由我定。

### 1.3 `authorized_commit_40hex` 与那个顺序陷阱

门 `authorized_commit_matches_head` 要求 **P2 的 commit == 运行那一刻的 HEAD**。

```
你签下 commit X  ->  期间任何一次提交都会把 HEAD 移开 X  ->  该门拒绝
```

**所以从你签 P2 到真跑之间，我不会再提交任何东西。**
今天我提交了三十多次，这条不是理论上的风险。

**具体做法**：你说「准备 P2」时，我先停止一切提交，报出当时的 40 位 HEAD，
你把那个值写进授权句。中间若有任何东西非提交不可，我会先告诉你并重报 HEAD。

---

## 2. P2 的四个必填字段（来自 `supplement_contract.EVENTS["P2"]`，不是我记的）

```
supplement_id                    MC-DS-S001
authorized_commit_40hex          签署时报出的 40 位 HEAD
output_root                      C:\Users\Aaron\quant-data\itsf-runs
verbatim_authorization_sentence  你的原话，逐字入行
actor                            Aaron（**必须**；contract 硬约束）
```

## 3. 签下去之后会发生什么 —— 说清楚，因为这一步不可逆

```
五道门翻转    live_authorization_unique · authorization_actor ·
              authorized_commit_matches_head · output_root_declared ·
              output_root_structure
              （08-29 合成干跑实测；真跑时我会重测而不是引用）
然后          MC supplement 会真的读 Development 数据、真的落盘、真的归档
研究自由度    **被消耗一次，撤不回来**
```

**这是今天所有步骤里第一个真正不可逆的。** 迁移可以回滚（回滚窗口 ≥ 一个工作周期），
R4 是文档，P1 不解开任何门。**P2 不是。**

## 4. 我建议在你签之前先做的一件事（不需要授权）

```bash
python scripts/mc_ds_rehearsal.py
```

它把整条链走一遍并打印每一步：十三道 A_PRECHECK 门、五道 B_DERIVE 门、
C_BUILD 机制、以及**一次真跑会往登记簿里写的那一行**。
全合成输入，零治理写入（前后快照自校验）。

**它不是「真跑能过」的证据，而且永远不可能是** —— 生产路径正确地拒绝合成 authority，
所以 C_BUILD 那段是绕过门驱动的，报告里也这么写着。
**它的用处是让你在签字之前看见那条链长什么样。**

## 5. 我不会做的

```
不代拟 P2 的授权句       actor 必须是你；我可呈块（形制乙），但内容是你的话
不预填 commit            签署那一刻实测，且从那一刻起停止提交
不替你判 §1.2 那个问题    它对我有利
不动八项授权字段          仍全为 NO
```
