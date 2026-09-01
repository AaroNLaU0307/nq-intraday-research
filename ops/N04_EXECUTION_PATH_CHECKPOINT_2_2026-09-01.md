＃ N04 执行路径 · 检查点 2 —— 二十三道门的完整实测表

```ini
RECORD_TYPE=MEASUREMENT（不授权、不执行、不读 Development 数据）
BY=Opus 5，builder seat，2026-09-01
SCOPE=C_BUILD（5 道）＋ 与检查点 1 的十八道合并成整表
BASE=11f0273b2696270fdaa02ab04185b09bcbf40cf6（检查点 1）
```

---

## 0. 一句话结论

**距离不是二十三道门。是两道门，加一条 live 的 P2。**

其余二十一道要么已经通过，要么只在等 P2 携带的那个 commit。

---

## 1. 整表

```
A_PRECHECK  13 道    8 PASS    5 等 P2
B_DERIVE     5 道    4 PASS    1 等 P2 携带的 commit（门对，夹具旧）
C_BUILD      5 道    3 PASS    2 无条件拒绝  ← 本段新测出的
                     （给定一个干净 outcome 时）
────────────────────────────────────────────
            23 道   15 PASS    6 等 P2    2 缺机制
```

## 2. 本段的实质发现：**那五道门不是同一种东西**

检查点 1 的标题是「没有一道门因为缺代码而拒绝」。**把它直接延伸到二十三道会是错的。**

```
分类器（C_BUILD_1，3 道）   row_schema_blind · day_set_exact ·
                            rows_digest_recompute
                            —— 经 _classify_c_build_1 读 outcome，
                               挂上 outcome 后即通过

无条件拒绝（2 道）          seal_staging_partial（C_BUILD_2）
                            archive_policy_a（C_BUILD_3）
                            —— 直接 _fail，**根本不读 outcome**
                               任何输入都不能让它们通过
```

它们各自的理由，逐字来自生产字节：

```
seal_staging_partial   "unreachable in this build: nothing is ever sealed"
archive_policy_a       "unreachable in this build: nothing is ever archived,
                        and Router B owns this gate's outcome (ROUTER_OF)
                        — see decide_after_seal"
```

**「拒绝」一个词，底下是两种完全不同的处境，而只有一种能靠挂上 outcome 解决。**

`archive_policy_a` 尤其不能简单接线：把它当普通门路由，refusal 会经 Router A 走到 F2，
而已批的 `ND1_ARCHIVE_FAILURE_POLICY=A` 要求 A1。**这个矛盾是被测出来的**，
不是推测（`test_routing_it_as_an_ordinary_gate_contradicts_policy_a`）。

## 3. 这个发现是**测**出来的，不是读注释读来的

注释确实写了这件事。但注释是一种声称——**这个仓库有五轮审查栽在
「写的时候为真、读的时候已假」的注释上**。所以用了探雷器：

```python
class _Tripwire:
    def __getattr__(self, name):
        raise AssertionError("the gate read .%s off the outcome" % name)
```

把它当 outcome 挂上去：

```
两道无条件门     照常拒绝，探雷器没响   -> 它们确实从不看 outcome
三道分类器       探雷器响在 .belongs_to  -> 它们确实要看
```

**两半都要测。** 只测前一半的话，探雷器有可能对谁都没响——那就什么也没证明。

## 4. 顺手修的一处生产字节

`seal_staging_partial` 的拒绝消息里写着「and the C_BUILD_2 wording is out for review」。
而**正上方的注释刚刚宣告这句话不再为真**（八轮已闭合、OD-1 封顶、已交付）。

**注释被修了，它旁边真正发出去的字符串没有。** 同一个缺陷形状，在同一个函数里，
距离十七行。

```
改前  "nothing is ever sealed (and the C_BUILD_2 wording is out for review)"
改后  "nothing is ever sealed; the C_BUILD_2 wording closed at cap on
       2026-08-30 and is NOT what makes this unreachable"
```

先查了没有测试钉住那个短语；`nothing is ever sealed` 被 n09 钉着，原样保留。
**行为不变，只有真假变了。**

### 4.1 修它的过程里，我用的工具静默改了整个文件

`Path.write_text` 在 Windows 上按 universal newlines 写出——**我只想改三行，
它把每一行的换行都换成了 CRLF**。全量套件里那条 `test_our_own_python_sources_are_lf`
抓住了它。

**这是同一族的第四个：一次只该动三行的写入，静默地动了每一行，而 diff 在
`git diff` 里看起来仍然只有三行**（因为 autocrlf）。修好后逐字核了 diff，
确认确实只有那三行。

以后在这个仓里改生产字节：读 `read_bytes` / 写 `write_bytes`，不用 `write_text`。

## 5. 建了什么

```
src/itsf/mc/supplement_build.py    装配 C_BUILD 上下文并逐道报告
tests/test_supplement_build.py     11 条
```

同一条分割线，第三次：**装配接收，从不生产。** `run_c_build` 由调用方带着它自己的
输入去跑，本模块永不代劳。仍是三重证明（AST 无 producer 调用 / `outcome` 无默认值 /
治理目录逐字节不变）。

### 5.1 写的过程中我自己犯了那个形状

```python
if outcome.failure is not None:      # <- 条件式断言
    self.assertIn(...)
```

**一条从不触发的条件断言，和一条断言了正确东西的，长得一模一样。**
去测了：该输入恒以 `vol_day_invented` 在 `day_set_exact` 拒绝。改成无条件断言。

另外把两处 `getattr(failure, "stage", "?")` 改成直接读字段——
**字段被改名时应该抛异常，而不是渲染成一个问号继续往下走。**

## 6. 下一步不是「再建一段」，而是一个要你定的岔口

```
要让 run_supplement_production 能返回，缺的是
  ①  seal / staging 机制（C_BUILD_2）
  ②  archive + Router B 接线（C_BUILD_3，且不得当普通门接）
  ③  一条 live 的 P2 —— 且必须在 ①② 之后签，否则重蹈
      ops/P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md 记的那个顺序错误
```

**①② 是真正的剩余工程量，也是唯一真正「缺代码」的部分。**
