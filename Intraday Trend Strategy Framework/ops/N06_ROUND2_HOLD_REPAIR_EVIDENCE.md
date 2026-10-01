# N06 第二轮 HOLD 修复证据（2026-08-23）

```
PACKET_TYPE=N06_ROUND2_HOLD_REPAIR_EVIDENCE
STATUS=REPAIR_CANDIDATE_AWAITING_THIRD_FRESH_SOL
REVIEWED_HEAD=17904bf6aef2b11f898e05a7351123af614e6cfd（第二轮判 HOLD）
REPAIR_STARTED_FROM=3d8a4e2727861a8943a19bcc6bafcef7faf0aa33
PRODUCED_BY=Opus 5 main agent (builder seat) — 自陈，不是验收
N06_FINAL_PASS=NO
```

---

## 1. 阻断 finding：check 与 use 未绑定同一快照（TOCTOU）

### 1.1 缺陷

`seal_supplement_production` 多次读取 caller 控制的 `product.payload`：
receipt 分量复算一次、day-set 一次、rows-digest 一次、blind schema 一次、
最终 `canonical_supplement_bytes` 再一次。

无需读取任何模块私有即可利用：`SupplementProduct.__new__` ＋
`object.__setattr__` 可把一个**状态型 Mapping** 装进去，绕过
`__post_init__` 的 `MappingProxyType(dict(...))` 浅拷贝，且**类型仍然精确**，
因此 exact-type 守卫看不见它。

### 1.2 第二轮 Sol 的实测

```
SEAL_RETURNED=YES
ROWS_READS=4
FORBIDDEN_PNL_SERIALIZED=True
DECLARED_ROWS_DIGEST_MATCH=False
SEALED_SHA_MATCH=True
```

### 1.3 本会话独立复现（未采信对方数字）

在修复前的树上跑新写的回归攻击：

```
test_z_a_stateful_payload_...  Failed: DID NOT RAISE SupplementProductionError
test_z_the_seal_reads_the_payload_exactly_once
    AssertionError: the seal read the caller's rows 2 times
```

即：封印**正常返回**，禁止字段进入了字节。

### 1.4 修复

新增 `freeze_payload()`：在 seal 入口**一次性**把 caller 的 mapping 深度冻结
成惰性副本（`Mapping → MappingProxyType`、`list/tuple → tuple`、标量原样、
其余类型拒绝 `production_payload_unsupported_type`），此后
**receipt 分量复算、binding、day-set、rows-digest、blind schema 与最终
canonical serialization 全部只消费这一份快照**，caller 的对象不再被读第二次。

`verify_production_receipt` 拆成 `_product_receipt`（类型与 receipt 在场）
＋ `_verify_receipt_against(snapshot, …)`，使 seal 能与它共用同一快照。

### 1.5 验收按第二轮指定的**析取**，不是"一律拒绝"

要求为：状态型 mapping 最终只能得到两种结果之一——写入前拒绝，或封存一份
无禁止字段且 `rows_digest` 与其自身 rows 一致的稳定快照。两条分支都有断言，
并由 flip 点选择走哪条：

```
flip_after=3（晚翻转） → 冻结取到干净视图 → 封存稳定快照（分支 b）
flip_after=0（立即翻转）→ 冻结取到带毒视图 → blind guarantee 拒绝（分支 a）
```

第二条存在的理由：否则第一条会**因为错误的原因**通过——必须证明冻结取的是
真实视图，而不是总能碰巧拿到干净的那一份。

### 1.6 一个我自己犯的测试错误，一并记下

回归攻击的第一版只覆写了 `__getitem__`。而 `freeze_payload` 经由
`items()` 读取，所以毒药根本没触发，测试**通过了但什么也没测**。改为同时
覆写 `items()`，攻击真实读取路径之后才成立。

### 1.7 变异证明（修复是承重的）

```
把 `payload = freeze_payload(product.payload)` 改回 `payload = product.payload`
  → 2 failed（test_z_the_freeze_takes_the_real_view…、
              test_z_the_seal_reads_the_payload_exactly_once）
还原
  → 74 passed
```

---

## 2. 我必须收回的一句话

上一轮证据包把 F1/F2（`__new__` 可绕过 capability）定性为：

> "真正成立的安全论证是：起作用的边界是**重新推导**，不是 capability——
> 每个被篡改的事实都在各自专属的码上被拒，因此 `__new__` 伪造只能复述真相。"

**这句话是错的，而且是我写的。** 重新推导只有在**推导所依据的字节与最终
使用的字节是同一份**时才成立；当时它们不是。缺陷不在 capability，在
check 与 use 未绑定同一快照。

`ops/N06_HOLD_REPAIR_EVIDENCE.md` §3 第 1 条已就地划掉并附更正，不是删除。
F1/F2 残留本身仍成立，但**不得**再用"重新推导足以兜底"为其背书。

---

## 3. 非阻断（Low）：与树不符的陈述

```
supplement_contract.py 头部        仍称 R1 为生效 profile     → 改为 R2（2026-08-23 批准）
provenance battery 头部            仍把 F7b/F4b 列为开放残留  → 标注为同轮已修的历史
supplement_production.py 头部      指向不存在的测试文件        → 指向真实的 provenance battery
```

---

## 4. 第二轮独立确认的四条（上一轮修复闭合成立）

由第二轮 Sol 各自重算，非采信：R2 为 51 行、`a3d40b7c…`、相对 R1 仅
PROFILE_ID/P3 四处变动且与代码一致；scope digest 独立枚举 24 blob 经 runtime
serializer 得 `e833ef7b…`；10 个校验 pattern 均拒绝 `\n`/`\r\n`，registry 两处
`(.*)$` 系提取器、原定性成立；`.python-version` 与 battery 断言一致。

---

## 5. 禁止状态（全部仍为 NO）

```
REAL_DATA_READ=NO ／ SUPPLEMENT_EXECUTED=NO ／ MC_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO ／ REGISTRY_EVENTS_APPENDED=NO
EXPOSURE_EVENTS_APPENDED=NO ／ REAL_DIRECTORIES_CREATED=NO
QROS_STATE_YAML_CREATED=NO ／ STAGE_I_VS_TIER1_DECIDED=NO
LANE_STAGE_INFERRED=NO ／ N-D2_STARTED=NO ／ N09_STARTED=NO
PUSHED=NO ／ TAGGED=NO
```

回归攻击**未**写入任何 governed root：`resolve_partial` 被替换以在内存中
捕获 intended bytes，两个 `supplements\` 子树在测试前后均不存在。

---

## 6. 下一步

第三个 fresh top-level Sol 会话做 round-3 exact-tree 验收，且

```
MUST_NOT_BE=BUILDER_OF_THIS_WORK,REPAIRER_OF_THIS_FINDING,
            FIRST_N06_REVIEW_SESSION,SECOND_N06_REVIEW_SESSION
```

提示词见 `ops/N06_ROUND3_SOL_PROMPT.md`。
