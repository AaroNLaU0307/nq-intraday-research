＃ 送审包 —— 真实数据前的 outcome-blind 工程安全复审

```ini
PACKET_TYPE=ENGINEERING_SAFETY_REVIEW（不是 A2，不是 Stage I，不解开任何 QROS 门）
REVIEW_ID=ENG-SAFETY-PRE-REAL-DATA-001
DELIVERY_STATUS=ISSUED
COMPANION=ops/NEXT_HANDOFF.md（禁读清单的载体；必须与本包一同交付）
PREPARED_BY=Opus 5，builder seat
DISPATCHED_BY=Aaron（我不得自行调用任何审阅席位）
MEASURED_AT=0cefc1503858ecf3b1dc5c90ec8bb3de9b1daa97
SCOPE=工程安全 / 边界 / fail-closed 行为 / 现存 residual
OUT_OF_SCOPE=研究结论、样本、成本、Primary 指标、promotion/falsified
ROUNDS=一轮。不开无限复审循环（Aaron 2026-09-02）
```

---

## 0. 受审集 —— **先逐字节核对，再开工**

标准动作：对下表每一行 `sha256 <路径>`，重算并比对。**不符即 STOP 并报告，不要继续。**
聊天里贴过来的字节永远不是真相来源；请从磁盘读。

| sha256 | bytes | 路径 | 角色 |
|---|---|---|---|
| `c34a9d13368eb4106d432c0b77ce25f7fd8e56f43642e5d1dee4f20e46c6d41a` | `6148` | `src/itsf/data/dbn_loader.py` | reference |
| `6ec6345734e97f2f9d718da8caade481b8f23827870299b6c2334fc046970000` | `2934` | `src/itsf/guards.py` | reference |
| `f0078a653a6b2f46980e62142780a1ef3913e8b6bd4d9748d0cdf99b54ec77ee` | `21391` | `src/itsf/mc/day_strata_classify.py` | reference |
| `4f181e5938b7e83b8837b93195e8ec1834b32a1ca160b5af2ce8c0a19387c8b7` | `8560` | `src/itsf/mc/supplement_chain.py` | reference |
| `bda85429e1aab979ce033d4aafae04241b935514452e58d49e4b534c2a519e54` | `33867` | `src/itsf/mc/supplement_contract.py` | reference |
| `d15611ce834f228069521e48c248a1936e2804a9894d1ca2c5c38c2e48f8290a` | `4853` | `src/itsf/mc/supplement_inputs.py` | reference |
| `6d3d48fe3013b797d1205f92aed93c207166919cb2f79e17f08eb018940097fb` | `55988` | `src/itsf/mc/supplement_runner.py` | reference |

本包自身的 sha256 记录在 `ops/ARTIFACTS_UNDER_REVIEW.json`
（一份文档无法钉住自己的哈希）。禁读清单在 `ops/NEXT_HANDOFF.md`，
**必须与本包一同交付**。

## 0. 给审阅席位的三条硬约束

```
一  不得读取任何 outcome-carrying artifact —— 清单在 §1，逐字，无通配符
二  不得读取任何真实 Development payload
    （139 个 .dbn.zst 一个都不读；manifest 元数据可读）
三  只读。发现即报告，不修复。
    本包不授权写入、不授权执行、不授权创建任何目录
```

**本次复审通过不等于 ① 被批准。** ① 只有 Aaron 能批。
**也不满足 A2 或 Stage I** —— `qros status` 现为两者皆 `NOT_SATISFIED`，本包不改变这一点。

## 1. 禁读清单

【OFF-LIMITS】以下 %d 条为 outcome-carrying，**一律禁读**（由 ops/OUTCOME_CARRYING_ARTIFACTS.json 机器生成，非手抄）：

```
EXPOSURE_LEDGER.md
ops/EXPOSURE_LEDGER.md
ops/outcome_quarantine/DECISION_PACKET_ND2_ND3.md
ops/outcome_quarantine/MC_DR5_BUILD_PACKET.md
ops/outcome_quarantine/MC_FACTORY_BOUNDARY_STAGE_I.md
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
ops/outcome_quarantine/ND2_ND3_FABLE_DECISION_PROMPT.md
ops/outcome_quarantine/ND2_ND3_RULING_REVIEW_FINDINGS.md
ops/outcome_quarantine/RULING_FABLE_FOUR_OPEN_2026-08-26.md
ops/outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
ops/outcome_quarantine/S0_T001_RESULT_DECISION_ADDENDUM.md
ops/outcome_quarantine/S0_T001_RESULT_REVEAL_ATTESTATION.md
```

## 2. 请审的四块，按承重排序

```
R1  第 8 轮之后对 resolve_partial 的修复，从未被任何独立席位看过
    —— 本阶段它的承重增加了两层：C_BUILD_2 门接线，
       且被接进一条能跑到 P4 的链路
    文件 src/itsf/mc/supplement_runner.py
         resolve_partial / _preserve / _require_plain_name
    背景 ops/DELIVERY_C_BUILD_2_WORDING_AT_CAP_2026-08-30.md §0

R2  编排层 src/itsf/mc/supplement_chain.py
    —— 按 checkpoint 取门而非按 stage（gates_at）；Router B 的两个入口；
       BD-5 的 post_archive_ok 语义

R3  输入装配层 src/itsf/mc/supplement_inputs.py
    —— structural-only 边界（第一版用 iter_day_contexts，被守卫拒绝）；
       已裁定方法从 contracts 读取而非写成字面量

R4  loader 边界 src/itsf/data/dbn_loader.py
    —— 自我更正：assert_real_run_allowed **今天是通过的**。
       请特别审：真正阻止真实读取的是什么，以及它是否足够
```

## 3. 我自己报告的四条弱点 —— **请核实，不要只采信**

```
一  assert_real_run_allowed 不阻止直接调用 load_real。
    保护来自「补充路径上没有代码调用它」＋「没有任何地方配置 job_dir」
    -> 这是否是可接受的保护形态？

二  _check_role 无法区分 attested primary 与未证副本。
    实测两条路径都会通过 role 检查（见 ① preflight §3 的两个候选）

三  UNMAPPED_SEAL_CODES 7 条仍无门（BD-6），全部大声拒绝、无一可静默取得门名

四  BD-5「archived_bytes_deleted -> A1」由封闭枚举的排除法得到。
    **请攻击这个论证**：答案空间真的封闭吗？A1 真的是非终态吗？
```

## 4. 复现命令（全部只读）

```
python -m pytest -q                                   期望 4997 passed
python -m pytest tests/test_supplement_chain.py -q
python -m pytest tests/test_day_strata_classification.py -q
python -m pytest tests/test_n09_scaffold_criteria.py -q
python -m pytest tests/test_supplement_inputs.py -q
```

## 5. 请席位回答的四问

```
Q1  R1 的修复在其新承重下是否安全？
    —— 问的不是「代码好不好」，是「够不够」
Q2  §3 的四条弱点，哪些是 High/Medium，哪些可接受？
Q3  是否存在**阻断 ①**（即：命名一个 job_dir）的工程发现？
Q4  除上述之外，还有哪个高风险面**未被审到**？
```

**verdict 请给 PASS / HOLD，Critical/High 放最前，并区分「复现的事实」与「自述的证据」。**
