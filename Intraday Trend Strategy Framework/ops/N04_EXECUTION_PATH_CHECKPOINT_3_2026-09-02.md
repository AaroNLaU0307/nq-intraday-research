＃ N04 执行路径 · 检查点 3 —— 机制全都在，缺的是编排

```ini
RECORD_TYPE=MEASUREMENT（不授权、不执行、不读 Development 数据）
BY=Opus 5，builder seat，2026-09-02
SCOPE=检查点 2 §6 的 ①②
BASE=8b28bf4（检查点 2）
```

---

## 0. 一句话结论，并且它订正了我自己昨天写的那条

检查点 2 §6 把剩余工程量写成：

```
①  seal / staging 机制（C_BUILD_2）      -> 建
②  archive + Router B 接线（C_BUILD_3）   -> 建
```

**两条都不准确。去测之后：**

```
①  机制早已完整存在。缺的只是把它的拒绝分类成 outcome 的一层包装
    -> 已建：day_strata_pipeline.run_c_build_2（＋门已接线）
②  不该接线。裁定明说 archive_policy_a 不得成为普通分类器，
    Router B 拥有它的 outcome —— 而 Router B、归档、C_BUILD_3
    判据三者都已存在
```

**没有一个机制是缺的。缺的是把它们串起来的编排器。**

---

## 1. 测出来的存量

```
seal_supplement_production   完整：从 authority 重导出、重建 payload、
                             内部已调用 resolve_partial 做暂存与 .partial 恢复
                             返回 (action, sha256)
resolve_partial              八轮审查的那一个，九种越界形式已拒
archive_sealed_run           itsf.s0.runinfra，产出 ArchiveReport
classify_archive_report      结构映射到封闭 ARCHIVE_CODES，总是可判
decide_after_seal            Router B，已实现：P4 / A1 / local_seal_failed
run_c_build_3                完整：本地 seal 不可变 ＋ 无归档字节被删
```

**我昨天说「①② 是唯一真正缺代码的部分」。那句话现在只剩四分之一为真** ——
缺的是 `run_c_build_2` 这一层包装，而它今天建好了。

## 2. 建了什么

```
src/itsf/mc/day_strata_pipeline.py   ＋ run_c_build_2 / SealStagingResult
src/itsf/mc/supplement_runner.py     _g_seal_staging_partial 接线为分类器
tests/test_run_c_build_2.py          9 条 ＋ 12 个子测试
tests/test_n09_checkpoint_assertions.py   更新那条已不再为真的断言
```

### 2.1 两个所有者，以及**提问的顺序**

一次 seal 拒绝，归门（Router A）或归 Router B——**BD-1 裁定有两个码根本不配门**。
所以 `run_c_build_2` 先问「**谁拥有它**」（`seal_failure_router`），再问「**哪道门**」
（`classify_seal_failure`）。

**反过来问会出事**：对一个 Router B 的码先问门，会抛 `ClassificationError`，
而一个把它吞掉的调用方，就让一个被裁定「无门」的码**意外获得了一道门**。
未登记的码从 `seal_failure_router` 大声抛出，失败关闭。

### 2.2 一个**故意保留**的陷阱，并且被执行而不是被警告

Router B 拥有拒绝时，没有任何门指名它——**于是五道 C_BUILD 门会在一次
根本没发生的封存上全绿**。

这是裁定本身的设计。应对方式不是藏起来，而是：

```
run_c_build_2 返回 local_seal_ok，与 outcome 并列
              -> 只读门的调用方，没有读到答案
test_a_router_b_refusal_leaves_the_gates_green   把这个陷阱跑一遍
```

**一个只被注释警告的陷阱，和一个不存在的陷阱，长得一模一样。**

### 2.3 尽量走真路径

干净封存与 seal 冲突两条都驱动**真实**生产封存器、写**真实**临时目录：
先封一次，改掉封存后的字节，再封一次 -> `supplement_seal_conflict`。
另有一条验证**它没有销毁任何字节**（`SILENT_DELETE_FORBIDDEN=YES`）。

只有 Router B 那两个码用桩——它们无法经公开工厂触发，而那里被测的是**路由**，
不是封存器。

## 2.4 整表随之变了

```
C_BUILD  5 道   4 PASS（给定干净 outcome）   1 无条件拒绝
                                             archive_policy_a —— 按裁定
────────────────────────────────────────────────────────────
        23 道  16 PASS   6 等 P2   1 归 Router B（永不经门）
```

## 2.5 四条守卫红了，而那正是它们存在的理由

改完之后全量套件有四条失败，**全部是钉住旧事实「两道门无条件拒绝」的测试**：

```
tests/test_supplement_build.py                 我昨天写的那两条
tests/test_the_c_build_1_wiring_landed.py      EXCLUDED 表
tests/test_day_strata_context.py               「两道存根仍是存根」
```

其中一条的原文写着：

> **「若其中之一悄悄变成分类器，理由就跟着丢了。」**

它没丢——`seal_staging_partial` 旧的排除理由是
「其措辞正被 Sol HOLD，且这条路径上从不封存」，而**后半句实际说的是
「缺分类器」而不是「缺机制」**。理由到期，排除随之取消，并逐字记进了测试。

`archive_policy_a` 的理由是**裁定**，不会到期——所以它留下。

**一次行为改动让四条守卫变红，比它们保持绿色更有价值。**

## 3. 下一段之前必须先解决的一个结构问题

```
run_stage_gates("C_BUILD", ctx)   按 GATE_TABLE 顺序跑全部五道
                                  -> 必然跑到 archive_policy_a
                                  -> 而它按裁定必须一直拒绝
```

**所以编排器不能按 stage 取门，必须按 checkpoint 取门。**

`CHECKPOINT_OF` 正是为此存在（三个时刻：写前 / 暂存中 / 归档后），
`checkpoint_of()` 已有，但**没有反向的 `gates_at(checkpoint)`**。
那是下一段的第一件事，且它有明确的消费者，不是投机添加。

## 4. 下一段：编排器

```
时刻 1  C_BUILD_1 三道门          （写之前）
时刻 2  run_c_build_2 -> 门        （暂存中，按构造会写 .partial）
时刻 3  archive_sealed_run
        -> run_c_build_3 判据
        -> decide_after_seal       （归档后，Router B，不经门）
```

**这是组合，不是新机制。** 完成后 `run_supplement_production` 才可能有返回值。

仍然不变：建代码不等于跑代码。真正创建 runs/archive 目录、以及签 P2，
每一次都需要你的精确授权。

## 5. 一条必须一并递上的残留

`ops/DELIVERY_C_BUILD_2_WORDING_AT_CAP_2026-08-30.md` §0 记着：
**第 8 轮之后那次修复，从未被任何独立席位看过。**

今天把 C_BUILD_2 接线，等于让执行路径**开始依赖**那次未经独立复审的修复。
残留没有变大，但它的**承重变了**。这条我不替你判定。
