# N06 第三轮 HOLD 修复证据（2026-08-24）

```
PACKET_TYPE=N06_ROUND3_HOLD_REPAIR_EVIDENCE
STATUS=REPAIR_CANDIDATE_AWAITING_FOURTH_FRESH_SOL
REVIEWED_HEAD=2a7374fc069274eeab2b090f5be84520efda5868（第三轮判 HOLD）
REPAIR_HEAD=ea610e728386705fa1793051f29e5aaf7d0e2e5a
PRODUCED_BY=Opus 5 main agent（builder seat）—— 自陈，不是验收
N06_FINAL_PASS=NO
AARON_RULING=改设计（2026-08-24，对主计划 §3 边界 10 的具名裁定）
```

---

## 1. 阻断 finding：敌意标量子类穿过深度冻结

### 1.1 缺陷

`_freeze_value` 用 `isinstance(value, _FREEZABLE_SCALARS)` 判定标量，
**isinstance 接受子类**，随后**按引用原样返回**。于是所谓"惰性快照"里
仍然坐着攻击者的比较行为。

```python
class LyingDigest(str):
    def __eq__(self, other): return True
    def __ne__(self, other): return False
```

放进 `rows_digest`，`supplement_production.py:343` 的
`payload["rows_digest"] != canonical_rows_digest(rows)` 问的是**它自己**，
而 `json` 编码写出的是底层真值。

### 1.2 本会话独立复现（未采信第三轮的数字）

修复前的树上，只用公开 `__new__` ＋ `object.__setattr__`：

```
EXACT_PRODUCT_TYPE=True
SEAL_RETURNED=True
DECLARED_ROWS_DIGEST=0000000000000000000000000000000000000000000000000000000000000000
ACTUAL_ROWS_DIGEST=792d1297a4c08a039472504298ebce7bf9db2a4241b98e8eeb0b6f730863dd8f
DECLARED_MATCH=False
```

`ACTUAL_ROWS_DIGEST` 与第三轮报告的**逐位相同**。封印正常返回，字节已进暂存。

### 1.3 为什么这一轮改设计，不是再打补丁

| 轮 | High | 被信任而未重新推导的东西 |
|---|---|---|
| 1 | N03→N04 接缝是反的 | authority 对象 |
| 2 | check 与 use 未绑定同一快照 | payload 被读四次 |
| 3 | 快照里的标量是敌意对象 | 快照里的 `rows_digest` |

同一个形状：**调用方给的值，参与了一次决定要不要写的比较**。三次补丁各自
正确，对手三次从同一扇门的另一个位置进来。主计划 §3 边界 10 要求同类反复
即停并上交，Aaron 裁定**改设计**。

### 1.4 修复

1. **封印重建自己要写的东西**。`_rebuild_from_rows` 从 authority 派生
   day universe 与 binding，用 rows 重建 payload，`canonical_supplement_bytes`
   序列化**重建结果**。伪造的 `rows_digest` 没有对象可以撒谎——不存在一个
   声明值供它冒充。
2. **receipt 对着重建结果再验一次**。因此 receipt 只可能描述**真正写出的
   字节**。
3. **冻结只收精确内建标量**，子类一律拒绝而非强转——`str(v)` 会调用攻击者
   自己的 `__str__`，那是同一个缺陷下移一层。

### 1.5 写电池时发现的第二处，无人到达过

`freeze_payload` 顶层内联了自己那份更弱的规则 `{str(k): _freeze_value(v)}`：
**嵌套 mapping 严格，顶层却用 `str(k)` 调用键子类的 `__str__`**。一个 `str`
子类做的键可以干净封存。三轮审查都没走到这里。**这是我的洞**，由本轮新写的
键攻击测到，现已收敛为一条规则一个地方（`freeze_payload` 委托 `_freeze_value`）。

### 1.6 拒绝顺序刻意保持不变

receipt 仍**先**对着 declared 验一次（手工装配的产物照旧在最前面以自己的
名字失败），`production_day_set_drift`、`production_rows_digest_drift`、
`production_forbidden_row_field` 全部保住原位。重建**之前**加了一道形状闸，
因为重建会静默丢掉多余的顶层键，没有这道闸那个键会以 receipt mismatch 的
名义出现，而不是它自己的名字。

### 1.7 变异证明（三处都承重）

```
type(value) in _FREEZABLE_SCALARS  →  isinstance(...)      → 4 failed
canonical_supplement_bytes(rebuilt) → (declared)           → 1 failed
键的 type(key) is not str          →  取消                 → 1 failed
还原                                                        → 81 passed
```

---

## 2. 我必须收回的一句话（第二次收回，同一句）

第二轮已经证伪"重新推导才是真正的边界"，但**只在证据包里改了一处**。
handoff 的 `KNOWN_ASSUMPTIONS` 和 battery 的 F1/F2 残留条目**仍立着原话**，
而那恰是审查者最先读到的两份。三处只改一处，不叫收回。

第三轮同时指出这句话还错了第二层：攻击只用**公开**的 `__new__` 与
`object.__setattr__`，"模块私有不是安全边界"根本不是这里的问题。

F1/F2 现记为它实际的样子——**不是良性残留，是这次封存违规的组成部分**。

---

## 3. 第三轮独立确认（非采信）

六份工件 SHA-256 6/6 逐字匹配；HEAD `2a7374f` 工作树全程干净；
`git diff --check` exit 0；collect 3970 与双 pin 一致；全套件 3970 passed；
定向生产边界 64 passed；frozen hashes 7/7；registry / exposure / attestation
三个哈希匹配；S0-T001 run/archive 14/14 逐文件相等；两个 `supplements\`
子树不存在；registry 零 `SUPPLEMENT_` 行；`final_candidate_scans.py` 如实
报 `SCANS=FAIL (3)`、未冒称 CLEAN；R2 为 51 行、`a3d40b7c…`、仅指定 2 删 4 增；
runtime serializer 对 handoff 自报的 26-path 快照复算得 `517c2ef2…`，并**明确
未把它自己算出的 27-path `21314dc8…` 冒充成候选 packet digest**；十个 pattern
均拒 `\n`/`\r\n`；`.python-version=3.13`，实跑 3.13.14。

---

## 4. 本轮机械结果

```
battery            74 → 81（说谎摘要／说谎标量×3 字段／说谎键／
                            重建字节属性／改名守卫）
full suite         3977 passed / 0 failed（371.10s）
dual floor pin     3970 → 3977
git diff --check   exit 0
scans              SCANS=FAIL (3)，仍是 atoms.py 三个既有 false positive
registry           ee9da33f（不变）
exposure           382182bf（不变）
attestation        d839b965（不变）
S0-T001            14 文件 run==archive
supplements 子树    两个均不存在
SUPPLEMENT_ 行数    0
```

---

## 5. 禁止状态（全部仍为 NO）

```
REAL_DATA_READ=NO            REVEALED_OUTCOME_READ_BY_BUILDER=NO
SUPPLEMENT_EXECUTED=NO       MC_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO    REGISTRY_EVENTS_APPENDED=NO
EXPOSURE_EVENTS_APPENDED=NO  REAL_DIRECTORIES_CREATED=NO
QROS_STATE_YAML_CREATED=NO   STAGE_I_VS_TIER1_DECIDED=NO
LANE_STAGE_INFERRED=NO       N-D2_STARTED=NO   N09_STARTED=NO
PUSHED=NO                    TAGGED=NO
```

全部攻击**未**写入任何 governed root：`resolve_partial` 被替换以在内存中捕获
intended bytes，两个 `supplements\` 子树在测试前后均不存在。

---

## 6. 下一步

第四个 fresh top-level Sol 会话做 round-4 exact-tree 验收，且

```
MUST_NOT_BE=BUILDER_OF_THIS_WORK,REPAIRER_OF_THIS_FINDING,
            FIRST_N06_REVIEW_SESSION,SECOND_N06_REVIEW_SESSION,
            THIRD_N06_REVIEW_SESSION
```

提示词见 `ops/N06_ROUND4_SOL_PROMPT.md`。

**若第四轮仍出 High**：按 §3 边界 10，不再自动修复——上交 Aaron，
并把"supplement 生产路径是否应当整体重新设计"作为独立议题提出。
