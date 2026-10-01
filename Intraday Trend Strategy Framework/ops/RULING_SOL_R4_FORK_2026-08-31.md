＃ R4 v2 单问裁断 —— fresh Sol：**甲**

```ini
REVIEW_ID=r4-v2-fork
RETURNED=2026-08-31
FORK_RULING=甲 —— 收窄主张**不算**在 R4 内自行扩权
TRANSPORT_PRECHECK=PASS
MECHANISED_THREE_CONFIRMED=YES
BOUNDARY_INDEPENDENTLY_TESTED=YES
OUT_OF_SCOPE_FINDINGS=2（均非阻断，均已修）
SEAT_STATUS=BLIND；REGISTRY_REPO_READ=YES；OUTCOME_EXPOSED=NONE
```

**本裁断只回答分岔。** 席位逐字写明：**不批准 v2、不释放冻结令、
不授权 CR1 追加或任何写入。**

---

## 1. 裁断的理由，逐字转录要点

> 控制性证伪器并非「发现任何定位脆弱性即触发」，而是
> 「**S4 不足迫使桥引入 S4 之外的新钉法**」才触发。
>
> v2 没有新增仓身份钉法：DISCOVERY 使用**迁移时已经存在的**墓碑定位符，
> VERIFICATION 使用 S4 的 N1/O0/O1 交叉互钉；它撤回「仓移动后仍可发现」
> 的过宽承诺，并将该情形明确保留为未关闭残留。
>
> 因此这是**把主张缩回现有事实**，不是在 R4 内自行扩权。
> 「移动时必须更新墓碑」是**维护现有发现边**的条件，不是新增身份锚。

**这条区分我自己没有想清楚**：我一直把问题看成「路径够不够格当锚」，
而它真正的形状是「**用一条已经被裁定存在的边，和另立一条新边，不是一回事**」。

## 2. 席位给出了**反对自己裁断的最强论点**

> `STRONGEST_OBJECTION`：「桥仍只引用 S4」作为简写并不精确，
> 因为发现步骤实际读取了墓碑；但原裁定的精确禁令是**不得另立新钉法**，
> 而不是不得使用已经裁定并存在的迁移字节。该反对不足以改判乙。

**这一条值得单独记。** 一个只给结论不给反面的裁断，价值低得多 ——
它让读者无法判断结论有多稳。本席位主动交出了推翻自己的最好材料，
并说明为何不足以推翻。

**我在 v2 里写的「桥仍只引用 S4」确实是不精确的简写**，
按他的口径应写成「桥只使用 S4 已裁定的钉法与迁移已产生的字节，不另立新钉法」。

## 3. 他独立复核的三件，全部与我一致

```
机械化三条    9/9 · 7/7 · 11/11 全绿（其运行时无 pytest 前端，
              改走各模块自带 unittest 入口，跑的是同一批断言）
哈希          重算 6e62fd2d… / 3384 字节，与提案声称一致
变异          进程内单字段变异 -> 预期的 3 个失败、0 error
分界          框架仓查 N1 exit 128 · registry 仓 exit 0
              N1 父提交无该文件 · N1 首次携带 6697 字节/37 行且 SHA0 匹配
              N1 时点 CR1 事件行数 0 · O0 blob 同 SHA0 · O1/N1 互钉成立
```

## 4. 两条范围外发现 —— 都成立，都已修

### ① 登记册对 delivery 说了一句关于它自己的假话

`unchanged_since` 对 delivery 写的是参考集的 pin，
**而该 pin 之后有 3 个提交碰过 delivery**（实测：`c087570`、`56ca240`、`5455ffc`）。

**这不是无害的冗余：它是一条治理记录在断言一件假事。**

**处置**（并说明为什么选便宜的那条）：

```
理想修法   把 unchanged_since 对 delivery 设为不适用，并让所有读者跳过它
实际修法   保留字段（schema 兼容），新增 unchanged_since_applies_to_this_entry=false
           与理由说明，使记录**自陈**该值不适用于它
为什么     unchanged_since 被四处当成必填字符串；在 R4 在途时做 schema 迁移
           会连带风险打到正在护着 R4 的运输守卫。**这是一次明写的取舍，
           不是没看见** —— 更好的那条记为待办
```

### ② `test_registry_absence_refuses.py` 的未关闭句柄

`io.open(...).read()` 未关。已改 `with`。
现在该组测试在 `-W error::ResourceWarning` 下也全绿 ——
**不是「警告消失了」，是把警告升级成错误后仍然通过。**

## 5. 我在修这两条时又犯了一次

修 ② 的时候，`test_registry_absence_refuses.py` **还在冻结登记册里**，
而我直接改了它。冻结守卫立刻变红。

规程本仓自己写着：**verdict returns → clear the register → then repair**。
裁断已返回，清册即可 —— 但我是被守卫提醒才想起顺序的，不是自己记得的。
**同一族顺序错误，今日第五次。**

## 6. 接下来

```
R4 v2      分岔已裁「甲」-> 可送 Aaron 批准（§D.10.3：id + sha256 + 精确 doc HEAD）
           R4_CANONICAL_SHA256 = 6e62fd2dc349468fd3bd1fdd8c5f2ef20b5b4cfade215eba07609107ca0f5233
冻结令     仍在 force —— 席位明确本裁断不释放它
批准之后   解冻 -> P1 -> P2 -> MC 真跑 -> 策略 build
```
