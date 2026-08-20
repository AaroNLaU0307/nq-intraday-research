# N06 HOLD — 修复前红证与修复后对照（2026-08-21）

```
RECORD_TYPE=RED_PROOF_AND_REPAIR_PROOF
PRE_REPAIR_HEAD=617f7c33d20051fd991d74afa7c76716720e385d
MEASURED_BY=Opus 5 main agent (builder seat)
NOT_A_VERIFICATION=YES（builder 自陈；N06 Stage I 属 fresh Sol）
```

> 每一条都驱动**公共/稳定边界**——一个 gate callable、一个 builder、一个
> parser——**不检查私有函数调用次数**。同一支脚本在修复前后各跑一次，
> 所以「新测试会杀死旧行为」是可复算的事实，不是断言。

---

## 1. 对照表

| # | 探针（公共边界） | 修复前 `617f7c3` | 修复后 |
|---|---|---|---|
| P1 | 手工 `FakeAuthority` 走完整 `B_DERIVE` | **ALL B_DERIVE GATES PASSED** | 拒于 `custody_authority_production` |
| P2 | 按真实 `SupplementAuthority` 字段形状的对象走 `B_DERIVE` | **拒于 `source_bundle_digest`** | 拒于 `custody_authority_production`（类型不符） |
| P2b | 真实 authority 的 digest 字段名 | `authority_digest, bundle_table_digest, day_universe_digest, method_digest` | 同（未变） |
| P2c | gate 实际读取的属性（AST） | `file_sha256_digest` | `bundle_table_digest` |
| P3 | 手工 `(expected_day_set, binding)` 经 hermetic core | **BUILT AND SEALED**（sha `f4de1c34…`） | 仍可（该 core 现已更名 `_test_only`，见 P3c） |
| P3b | 接收 authority 的生产 build API | **ABSENT** | present（`supplement_production`） |
| P3c | 手工 payload 能否进入**生产** seal | n/a（当时不存在生产 seal） | 拒于 `production_not_factory_built` |
| P4 | P2 的 `output_root` ≠ 实际 `runs_root` | **ACCEPTED** | 拒于 `output_root_structure` |
| P4b | P2 的 `output_root` 为相对路径 | **ACCEPTED** | 拒于 `output_root_structure` |
| P5 | 历史最高序号 13 之后使用 **14** | ACCEPTED | ACCEPTED（正确的下一个值） |
| P5b | 13 之后直接使用 **99** | **ACCEPTED** | 拒于 `supplement_seq_not_next_value` |

### P2 的意义（最严重的一条）

修复前的接缝是**反的**：手工伪造对象通过全部 `B_DERIVE`，而**真实**
authority 被拒——因为 gate 读 `file_sha256_digest`，而真实 authority 暴露的是
`bundle_table_digest`。伪造进、真品出。修复后 `B_DERIVE` 检查**类型**，并且
每个下游 gate 从**同源 prepared input 重新计算**，而不是读取对象自述。

### P3 / P3c 的读法

P3 修复后仍显示 "BUILT AND SEALED"，这是**预期且正确**的：那是
`build_day_strata_supplement_test_only` / `seal_supplement_test_only`——刻意
保留、刻意改名的 hermetic 测试核心。决定性的一条是 **P3c**：同一份手工
payload 送进**生产** seal 被拒于 `production_not_factory_built`，因为
`ProductionReceipt` 是 `init=False` 且只能由生产 builder 铸造。

---

## 2. R1 的两处结构矛盾（第 6 项；工程侧无法自行裁定）

```
P3_PREDECESSOR:
  contract = P2                 （§D.3.2 P3 那一行）
  diagram  = P2 | F1            （§D.3.3，且 F1 自己的后继表含 P3）

P3_SUCCESSOR:
  contract = P4 | F2            （§D.3.2 P3 那一行）
  diagram  = P4 | A1 | F2       （§D.3.3，且 A1 自己的前置表写 P3）
```

两处都是「两份陈述对一份遗漏」。当前工程树实现图与邻接合同的读法
（`pred=('P2','F1') succ=('P4','A1','F2')`），**该读法尚未被任何已批准的
profile 逐字覆盖**——这正是 `ND1_RECOMMENDED_PROFILE_R2`（决策包 §D.11）
存在的原因，也是本轮把它交给 Aaron 而不是自行认定的原因。

```
P6_RESOLVED_BY_ENGINEERING=NO
P6_REQUIRES=AARON_RATIFICATION_OF_ND1_RECOMMENDED_PROFILE_R2
```

---

## 3. 另一条独立的旧行为对照（`.partial`，第 N04 轮已记录，此处复列）

```
branch C（前次崩溃遗留的 divergent partial）
  OLD  supplement_partial_residue；residue_still_blocking_path=True
  NEW  retry_permitted；evidence_preserved=True；路径解除阻塞
branch E（本次写入后 re-read 不符）
  OLD  supplement_partial_verify；bytes_on_disk=[]        ← 被 unlink
  NEW  supplement_partial_verify；保留为 …partial.divergent.INC-…
```

---

## 4. 本记录不构成的东西

```
THIS_IS_NOT_A_STAGE_I_VERIFICATION=YES
THIS_IS_NOT_AN_AUTHORIZATION=YES
SUPPLEMENT_EXECUTED=NO / MC_EXECUTED=NO / REAL_DATA_READ=NO
```
