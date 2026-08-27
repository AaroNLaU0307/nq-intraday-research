# 勘误 —— 致正在复审迁移方案的 fresh Sol

```
RECORD_TYPE=ERRATUM
TO=正在执行 ops/PROMPT_MIGRATION_PLAN_SOL_REVIEW.md 的那个会话
FROM=Opus 5，builder seat，2026-08-27
ISSUED_AFTER=送审之后、裁定返回之前
```

**你手上那份送审文件里有一句 builder 写错的话。** 它不影响传输核对——**你不必
STOP，也不必重做哈希核对**：勘误的是内容的一个前提，不是被审字节的完整性。

**你可以选择**：把它纳入本轮，或在裁定里声明「本轮基于送审版本，勘误另计」。
**两种都是正当的**，请明说你选了哪种。

---

## 1. 错在哪

送审的 `ops/REGISTRY_MIGRATION_PLAN_ROUTE_A.md` §1 原文（你读到的版本）：

> 本项目**已经因云同步残渣撞上 exact-set 磁盘不变量烧掉过一次 trial**（L-5）。

**这是错的。** 记录（`ops/D124_RULINGS_CLEAN_EXTRACT.md:111`，逐字）区分两件事：

> 为**真实缺陷**（L-5）建立、经**真实事故**（R5）加固的回归守卫

「烧掉一次 trial」的出处是 `ops/D3_REGISTRY_WRITER_PROPOSAL.md` §2.4，逐字：

> L-5 缺陷正是 OneDrive 残渣类（……**会让** M6.1.7 的 exact-set 磁盘不变量判为
> 封存拒绝、烧掉一次 trial）

**「会让」。那是机制描述，不是事件记录。**

**builder 实测**：

```
ops/TRIAL_REGISTRY.md 中 BURNED / ABORTED / VOID 事件数    0
S0-T001 的实际结局                                          成功封存
```

**没有任何 trial 被烧掉过。**

---

## 2. 第二处：OneDrive 实际处于休眠

送审版 §1 与 §3 把同步描述成活跃的。**Aaron 2026-08-27 指出它从未真正同步过，
builder 实测证实**：

```
仓内文件属性              Archive 而已 —— 无 Offline / ReparsePoint /
                          RecallOnDataAccess（被 OneDrive 接管的文件会有）
全仓冲突副本命名          0
主客户端 OneDrive.exe     未运行（仅 OneDrive.Sync.Service，服务组件）
最后登录                  2026-01-06 UTC
```

**但不是「不存在」**：账户仍配置着，OneDrive 根与其下 `Desktop` 都是重解析点。
**一次登录就把这棵树纳入管理。**

---

## 3. 这改变了什么，没改变什么

### 改变的 —— 且它触及你正在审的那条链

`dec-registry-migration-2026-08-27` 拒绝路线 C 的理由之一，逐字：

> 我为了不让迁移成本挡住 P1→P2 链条，对一个**已经兑现过的风险**给了过轻的处置。

**那个风险没有兑现过，而「已经兑现过」这个说法是从 builder 的决裁包里来的。**

**所以拒 C 的力度弱了一截。** 你若认为路线选择应当重开，写进
`UNRESOLVED_FOR_AARON`——**但仍不要改裁**，路线由决裁席裁、Aaron 已采纳。

### 没有改变的

- **L-5 缺陷是真的**，2026-08-10 由 Aaron 裁定。
- **失败模型的通道 A／B 分析从来就是分析**，不是事故报告；§0 写的是 registry
  「**住在**」一棵被同步的树里，那是前提陈述。
- **`Desktop` 被已知文件夹重定向进 OneDrive 是实测事实**，与同步是否活跃无关
  ——休眠可以结束，重定向不会。
- **迁移的理由仍在，紧迫性下降。** builder 此前把这两件捆在一起说，是错的。

---

## 4. 已改的版本

```
ops/REGISTRY_MIGRATION_PLAN_ROUTE_A.md   已改，新 sha256 见下
   0ed30133d06922089571aa1861fc7fa6ba23420e1f115687700666c09f6cf121   11787 字节
```

**若你选择纳入本轮**，请对新字节重做哈希核对再继续；
**若你选择另计**，请在裁定里逐字声明你基于的是送审版本。

完整自纠记录：`ops/CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md`
（sha256 `fd3cd89ad03e60a5606730b5d3447a67ea04e36916afeb20033ea7e08e989771`，5111 字节）。

---

## 5. 一件 builder 要说明的

**这条勘误是 builder 自己查出来的，不是被谁发现的。** 触发是 Aaron 说了一句
「我电脑的 OneDrive 其实没同步过」——builder 去核那句话，顺带发现自己一直在把
一个缺陷的机制当成已发生的事故写。

**这不是替自己表功，是给你一个判断依据**：本方案里其余的「实测」标注，是否也
需要你重新验一遍。**builder 的建议是：需要。**
