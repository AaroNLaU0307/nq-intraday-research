＃ §D.3.2 修订 —— pre-start 重授权直边 `P2 -> P2S`

```ini
AMENDMENT_ID=P2-TO-P2S-PRESTART
STATUS=APPROVED（Aaron 2026-09-05 逐条批准）并已实现
BY=Opus 5，builder seat，2026-09-05
SCOPE=只解决已机械确认的 pre-start authorization gap。
      **不视为全面 L6/QROS 重构**（Aaron 原话）。
      全面 workflow redesign 仍在 N09 完成之后、N10/N11 之前。
```

**不占 R 编号**，理由同 `AMENDMENT_ARCHIVE_CODE_6_2026-09-05.md`：本仓 `R<n>`
命名空间已被三个系列同时使用。

---

## 1. 缺口，机械确认

§D.3.2 把重授权写成 `F1 -> P2S -> P2`，前提是「commit 过期由一次失败的尝试发现」。

但 commit 也可以在**任何尝试之前**就过期：授权签了，必要的修复落地，HEAD 移动，
而什么都还没跑。实测当前 `MC-DS-S001` 正是这个状态：

```
第 15 行 P2 存在，live=1，绑定 301de7bd…
链里没有 P3            —— RUN_STARTED 从未发生
research freedom       —— 未消耗
A_PRECHECK 13 道门     —— 12 道 pass，唯一拒绝 authorized_commit_matches_head
```

**`F1` 描述不了这件事**：它的必填字段里有 `stage`、`gate_name`（两者都是
parser 校验的闭枚举）和 `attempts_dir`。那次尝试从未发生，所以这三个字段
只能靠**编造**填出来——而 A_PRECHECK 的拒绝根本不创建任何目录
（`make_run_directory` 在 B_DERIVE 之后才调用），`attempts_dir` 会指向一个
**执行流程永远不会使用**的目录。

从 P2 出发的合法后继只有 `P3 / F1 / F3`。所以在修订之前，这个状态**无路可走**。

## 2. 证据：它镜像的先例本来就是直边

创建这条规则的批准单元格逐字写着：

> `ND1_PRESTART_COMMIT_CHANGE_REAUTH` … `YES`（镜像 S0 两次
> `RUN_AUTHORIZATION_SUPERSEDED` 先例）

**实测真实登记册，那两次先例长这样：**

```
6   RUN_AUTHORIZED                 commit 524c9ab…
7   RUN_AUTHORIZATION_SUPERSEDED   supersedes_event_sequence: 6
8   READY_FOR_RUN_AUTHORIZATION
9   RUN_AUTHORIZED                 commit 08e7423…
10  RUN_AUTHORIZATION_SUPERSEDED   supersedes_event_sequence: 9
11  READY_FOR_RUN_AUTHORIZATION
```

**两次都是直接跨过去的，中间没有任何 failure 行。**
supplement lane 的转写给 P2S 加了一条**它自己引为先例的那条路径并不具备**的要求。

（三条 lane 实测对照：S0 lane 无转移表，只算 liveness；MC lane 与 supplement lane
都要求先有一条 attempt-failure。）

## 3. 改了什么 —— 三个源文件

```
supplement_contract.py    P2.successors    += "P2S"
                          P2S.predecessors += "P2"
supplement_registry.py    新增 PRESTART_COMMIT_CHANGE 常量
                          新增 _is_prestart_reauthorization()
                          _edge_code() 增加 event/started 参数
                          P3 处那条「必须走 F1 -> P2S」的拒绝消息补上直边
supplement_runner.py      plan_next_short_id：P2 增加 outcome
                          "prestart_reauthorize" -> "P2S"
```

`transition_allowed()` 是**从 EventSpec 派生**的，所以改两个元组就传播到 parser，
不需要同步任何手写表。`test_nd1_profile_r2.py` 钉的是 **P3** 的前驱，profile 字节未受影响。

## 4. 六个条件，以及每一条由谁执行

```
1  该 id 下不存在 P3 / RUN_STARTED    _is_prestart_reauthorization 的 `started`
2  旧 P2 未产生任何 consumption        **同一个 `started`** —— consumption 发生在
                                      P3（SUPPLEMENT_RUN_STARTED 就是取走名额的
                                      那一行）。这不是第二道检查，是同一个事实。
                                      如实写明，而不是假装有一个并不存在的字段
3  same_id_reauthorization = YES      predicate ＋ parser 的 _YES_FIELDS
4  superseded != successor commit     既有 p2s_successor_equals_superseded
5  reason_code=PRESTART_COMMIT_CHANGE predicate
6  supersedes_event_sequence 精确指向  既有 p2s_no_target_p2 /
   被替代的旧 P2                       p2s_target_not_live / p2s_commit_mismatch /
                                      p2s_supplement_id_mismatch
```

**六条里有四条本来就在执行。** `_resolve_supersedes` 在链遍历**之前**运行，
所以无论前驱是谁它们都成立。真正新增的只有 1/2 与 5，两者都从行和遍历状态**读出来**，
没有一处采信调用方的说法。

## 5. 它**不**打开什么

```
真实 attempt failure      仍走 F1（reason_code 不匹配即拒）
运行后的 commit 变化      P3 之后 `started` 为真，直边关闭
已有 P3                   p2s_after_p3，原样保留
已有 consumption          同上，同一个事实
其它 recovery 情形        仍走 F3 / A1 / A2 / AX / CR1，一律未动
p2s_without_preceding_f1  **保留**，只是不再拒绝满足本例外的那一种
十一条 P2S 拒绝码         数量与内容均未变
```

守卫方向已变异验证：把 reason_code 检查拿掉，一条本该被拒的链会被**放行**
（实测 `p2s_without_preceding_f1` -> `ADMITTED`）。

`tests/test_prestart_reauthorization.py`（16 条）里有一半是**反向**断言：
每一条原本守着旧路径的拒绝，都在新边上重新断言了一次。

## 6. 一个如实记录的测试缺陷

`prev == "P2"` 这一半**在链层面无法被违反**：要走到一个带合法 target 且没有 P3 的
P2S，可能的前驱只有 P2 和 F1。我最初写的 `test_p1_to_p2s_is_still_refused`
**通过的理由和它声称的不是同一个**——没有 P2 就没有 supersede target，
行在 `supersedes_event_sequence` 的字段检查上就死了，根本到不了 edge code。

已改成断言它**真正**产生的码，并在 docstring 里写明该条件改由 predicate 层证明。
「匹配不到任何东西的检查，和匹配到正确东西的检查，看起来一模一样」——本仓的老毛病。

## 7. 没有动的

```
AUTHORISED_SUPPLEMENT_ROWS   未预置任何尚未发生的事件（Aaron 明令）
真实 registry                 一个字节未动
F1 / F3 / T1 / recovery 语义  未动
backlog（含 C7）              未动
```
