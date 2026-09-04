# Builder 裁定 —— 2026-09-02

BASIS=Aaron 2026-08-29「很多决定不需要问我」——工程判断归 builder，
Aaron 保留六类：成本 / Primary 指标 / 样本切分 / 何时动真实数据 /
promotion-falsified / quant-data 建目录。

**这份文件不是 owner 裁定。** 与 `ops/OWNER_DECISIONS_*.md` 严格分开。
每一条都写明**为什么它是工程判断而不是研究判断**。

---

## BD-2 `archived_bytes_deleted` 的终态：**A1**

### 起因，以及我先犯的错

`ops/N04_EXECUTION_PATH_CHECKPOINT_4_2026-09-02.md` §2 把这一条写成
**「欠 Aaron 一条裁定」**。

**那是越级。** 它不碰成本、不碰 Primary、不碰样本切分、不动真实数据、
不产生 promotion/falsified、不建 quant-data 目录——**六类一条都不沾**。
它只回答「这个失败被记成哪个终态」，和 BD-1 是同一种问题。

Aaron 随后说「你不能决定就交给 Fable 裁决」。**这两件都不成立：**
一是这条本来就该我定；二是他自己的规矩写着
**「Fable 可顾问不可代签——它是我调用的」**，所以我既不该把裁决权转给 Fable，
也不该由我去调用它。

### 结论

```
run_c_build_3 报 archived_bytes_deleted
  且 local seal 存活
  -> decide_after_seal(local_seal_ok=True, report, post_archive_ok=False)
  -> A1
```

### 为什么 A1 不是发明，而是**排除法**

路由器 B 的答案空间是**封闭的**：`P4 / A1 / 被拒的 seal`。

```
P4                 Policy A：P4 需要 local_seal_ok AND archive_ok
                   而 R3 §1 的 C_BUILD_3 判据(b)「无任何已归档字节被删除」
                   刚刚被违反 -> 不是 ok -> 排除
被拒的 seal        seal 活着。这正是本码与 local_seal_absent /
                   local_seal_mutated 的**全部区别** -> 排除
────────────────────────────────────────────────
剩下               A1
```

**三取其二被排除，A1 是已批枚举剩下的那个，不是 builder 偏好的那个。**

### 为什么「排除法」在这里是足够的

单靠排除法**不够**——除非 A1 本身不是「放行」。它不是：

> A1 是**非终态陷阱**（`NON_TERMINAL_TRAPS`），`P5` 在一次显式的 `A2`
> 之前不可达。

所以把「证据被毁」判成 A1 **挡住了完成**，而不是把它挥手放过。
**如果 A1 意味着「继续」，上面的排除就不足以支撑这条裁定，我会把它递上去。**

### 为什么需要一个新参数，而不是造一份报告

`archive_sealed_run` 只校验它**刚做的那份拷贝**，从不看更早归档的字节。
所以它的报告可以说 `archive_ok`，而检查点说归档毁了证据。

`classify_archive_report` 按设计拒绝一份 `archive_ok` 的报告
（抛 `archive_ok_has_no_code`）。**要绕过它只有两条路：**

```
甲  合成一份「失败」的报告喂给它     —— 为了拿到一个结论而伪造证据
乙  把检查点的判定作为参数告诉路由器 —— decide_after_seal(post_archive_ok=)
```

**选乙。** 甲是这个项目最不该出现的一种动作。

参数默认 `True`，所以每一个既有调用方行为不变，且这一点被签名测试钉住。
另外钉住：`local_seal_ok=False` **压过**检查点的判定——seal 没活下来时，
结论仍是「nothing was sealed」。

### 边界：BD-2 只定了**一个**码

C_BUILD_3 将来新增的码**仍然失败关闭**——链路抛
`no ruled verdict covers <code>`，与 BD-1 对封印码的要求一致。
**一条被裁定的码，不给后来的码开门。**

---

## 与 BD-2 一起交回的两件事（**不是**我能定的）

```
①  何时动真实数据        Aaron 保留的六类之一
③  签一条 live P2        消耗研究自由度，只有 Aaron 能签
```

这两件**不能转给 Fable**：Fable 可顾问不可代签，且由 Aaron 调用。
若 Aaron 要 Fable 的**意见**（而非签字），我可以备送审包，由他发起。
