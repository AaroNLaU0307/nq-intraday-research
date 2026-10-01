＃ 复审结果 · ENG-SAFETY-PRE-REAL-DATA-001 —— **HOLD**

```ini
RECORD_TYPE=REVIEW_RESULT（builder 的验收记录，不是席位记录本身）
SEAT=Aaron 亲自以审阅席位执行
VERDICT=HOLD
REVIEWED=包字节 d21c552e… @ HEAD c18ef15
SEAT_RECORD=scratchpad 文件，sha256 6001eeea68d02d50ebbd2f32185bbec19370337527c96034ef0a9814b92532a4
BY=Opus 5，builder seat，2026-09-02
```

---

## 0. 席位审的是哪一版 —— **认定 `d21c552e…`**

包在席位持有期间被我改写了四版（`d21c552e → c7d9fbec → 0cb52697 → 522b435f`）。
**那是我的缺陷（席位记为 M4）**：冻结之后不得再动交付件。

**认定席位审的是它开工时核对过的 `d21c552e…`**，其后三版全部是我为满足治理守卫
所做的元数据补齐（哈希表、REVIEW_ID、DELIVERY_STATUS、禁读清单加标记），
**没有一版改动 §2 的受审面或 §3 的自述弱点**。七个受审源文件在始末两次核对中
sha256 未变——这一点席位与登记册一致。

> **教训，写在最前：冻结、送出、然后不许再碰。** 我把「补齐治理元数据」
> 当成了无害动作，而它让席位手里的字节与磁盘上的不一致。

## 1. 席位记录本身尚未落仓

席位给了 sha256（`6001eeea…`）但记录仍在 scratchpad。
**按运输规则，聊天里的摘要不是真相来源。** 本文件是**我的验收记录**，
不是席位记录的替代品；席位记录需要 Aaron 提供路径后抄入 `ops/`，
届时核对该 sha256。

## 2. 四条发现 —— **全部由我逐条复现，无一采信自述**

### H1 链路从不把 `out_dir` 与 `runs_dir` 绑定 —— **复现**

用**真实** `archive_sealed_run` 驱动，`out=tmp/seal`、`runs=tmp/runs`（存在但空）：

```
verdict         P4
archive_status  archive_ok
seal 落在       out_dir/DAY_STRATA_SUPPLEMENT.json
归档树          ['runs']        <- 拷进去的是一个空目录
SEAL IN ARCHIVE False
```

**Policy A 的「P4 需要 archive_ok」被满足了，而被封存的补充根本没进归档。**
第二份拷贝在代码里没有被保证。席位还指出：我自己的
`test_it_creates_no_directory_of_its_own` 正是在 P4 之后断言 runs 不存在——
**那条测试把这个缺陷钉成了预期行为。**

### H2 不存在 gate-first 的组合路径 —— **复现（按构造）**

```
run_supplement_production   无条件 raise，从不调用链路
precheck / derive / build   只是报告器，不构成执行路径
run_supplement_chain        只跑 C_BUILD 三个时刻的门
                            -> 18 道 A_PRECHECK/B_DERIVE 一道没过就能到 P4
<id>_<UTC> 的 mkdir         无人拥有
out_dir 不存在时            裸 FileNotFoundError 逃出，不是具名拒绝
```

**与 `P2_WITHDRAWN_NO_EXECUTION_PATH` 同形**：我又一次把「组件齐了」
当成了「路径通了」。

### M1 `retry_permitted` 被当作封存成功 —— **复现（按构造）**

`resolve_partial` 可返回 `retry_permitted`（第 1054 行），
而 `run_c_build_2` 第 315 行在非异常路径上**无条件**回 `local_seal_ok=True`。
于是链路先做**真实归档 I/O**，`run_c_build_3` 才发现 seal 不存在，
Router B 事后才说 `local_seal_failed`。**顺序错了。**

### M2 BD-5 的排除法不封闭 —— **复现，且已导致 BD-5 收回**

```
以 P3 为前驱的事件   ['A1', 'CR1', 'F2', 'P4']    <- 四个，不是三个
A1 必填              archive_code
ARCHIVE_CODES        5 个，不含 archived_bytes_deleted
A2（A1 唯一出口）     只断言**本次 run 拷贝**的 inventory/sha256 相等
```

**我把「Router B 函数的返回值集合」当成了「已批状态机的后继集合」。**
F2 与 CR1 从未进入我的排除。**详见 §3。**

### M3 / M4

M3 三条我在 preflight 里已自报（门是开的、`E:` 不存在、manifest 优先级），
席位判为可接受。**M4 是 §0 那条,我的缺陷。**

## 3. BD-5 收回

**收回。** 三条腿全断：空间不封闭、A1 行写不出来、A1 的出口治不了这个缺陷。

```
decide_after_seal   post_archive_ok 参数已移除，恢复已批签名
supplement_chain    archived_bytes_deleted 重新**具名拒绝**
测试                原先钉 A1 的两条改为钉**反驳本身**：
                    P3 后继必须是 ['A1','CR1','F2','P4']
                    archived_bytes_deleted 必须不在 ARCHIVE_CODES
                    decide_after_seal 必须没有 post_archive_ok 参数
```

**为什么不改判成别的终态：** 现在给它命名需要在四个后继里裁定，
或者修改一个**已批的封闭枚举**（R4 级动作）。**两者都不是 builder 能做的。**

> BD-5 的「这条不占 Aaron 六类保留项、所以归 builder」这一半仍然成立。
> **但『可以由我决定』不等于『可以由我决定错』。**

## 4. 我处置了什么，没处置什么

```
已处置  BD-5 收回（Aaron 明确指派）
        seat 台账第 16 行补全 SEAT_STATUS，verdict 记 HOLD
        冻结登记册撤下（复审已返回），包标 RETURNED
未处置  H1 / H2 / M1 —— **修复是独立阶段，需要 Aaron 单独授权**
```

## 5. 加宽守卫的副产品，以及我因此犯的第五个错

加宽「在飞交付物」判定后，它报出 `ops/HOW_TO_SEND_THE_SOL_ROUND3_REVIEW.md`
也是 ISSUED。**我据此改了那份文件——而那是错的**：那里的
`DELIVERY_STATUS=ISSUED` 是在**描述另一份文件**的状态，不是自我声明。

**假阳性是我的检查造成的**：我用了子串匹配，而既有的 `_STATUS` 一直是行首锚定的。
已撤回对该文件的改动，并把我的检查改成同样锚定。

**一个我为了抓「守卫比声称窄」而写的检查，自己比声称宽。**
