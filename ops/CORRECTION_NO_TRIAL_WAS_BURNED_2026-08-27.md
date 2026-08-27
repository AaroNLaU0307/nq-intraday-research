# 更正：没有 trial 被烧掉过，也没有 OneDrive 在同步

```
RECORD_TYPE=CORRECTION
BY=Opus 5，builder seat，2026-08-27
TRIGGER=Aaron 2026-08-27「我电脑的 One Drive 我其实没同步过」
SCOPE=builder 在多份文档中把一个缺陷的**机制**写成了**已发生的事故**
AFFECTS=dec-four-owner-2026-08-27 第 3 件 #4 · dec-registry-migration-2026-08-27
        · 正在进行中的迁移方案 fresh Sol 复审
```

**这份更正是 builder 的自纠。** 两份裁定都部分建立在一个我写进决裁包的、被夸大的
前提上，而正在飞的那轮复审里也有它。

---

## 1. 我一直在说的话，与记录实际说的话

**我写的（至少四处）**：

> 本项目**已经**因云同步残渣撞上 exact-set 磁盘不变量**烧掉过一次 trial**。

**记录实际说的**（`ops/D124_RULINGS_CLEAN_EXTRACT.md:111`，逐字）：

> 为**真实缺陷**（L-5）建立、经**真实事故**（R5）加固的回归守卫

**两件不同的事，我合成了一件。**

「烧掉一次 trial」的出处是 `ops/D3_REGISTRY_WRITER_PROPOSAL.md` §2.4，逐字：

> L-5 缺陷正是 OneDrive 残渣类（同步产生的 `desktop.ini`／`*.tmp` **会让**
> M6.1.7 的 exact-set 磁盘不变量判为封存拒绝、烧掉一次 trial）

**用的是「会让」。那是机制描述，不是事件记录。**

---

## 2. 实测（不采信任何转述）

```
ops/TRIAL_REGISTRY.md 中 BURNED / ABORTED / VOID 事件数    0
S0-T001 的实际结局                                          Stage C entry ->
                                                            S0 report sealed
```

**没有任何 trial 被烧掉过。** 唯一一次真实运行消耗了一次 exposure seq 并成功封存。

**准确的表述应当是**：

```
L-5   真实缺陷，2026-08-10 裁定：受治理的输出根必须在仓树之外
R5    真实事故，把 <repo>/runs 加进监视表
机制  同步残渣会让 exact-set 判为封存拒绝，从而烧掉一次 trial —— 尚未发生
```

---

## 3. Aaron 的说法有实证支持

```
仓内文件属性              Archive 而已 —— 无 Offline、无 ReparsePoint、
                          无 RecallOnDataAccess
全仓 OneDrive 冲突副本    0
主客户端 OneDrive.exe     未运行（仅 OneDrive.Sync.Service）
最后登录                  2026-01-06 UTC，将近八个月前
```

真被 OneDrive 接管的文件会带重解析点或离线标记，**仓内文件没有**。

### 但要说清楚它**不是**什么

```
账户仍配置着              UserFolder=C:\Users\Aaron\OneDrive，带邮箱
C:\Users\Aaron\OneDrive   ReadOnly, Directory, Archive, ReparsePoint
…\OneDrive\Desktop        ReadOnly, Directory, ReparsePoint
```

**目录结构确实是 OneDrive 的，同步是休眠而不是不存在。** 一次登录或启动客户端就会
把这棵树纳入管理。风险的准确形状是「一步之遥」，不是「不可能」。

---

## 4. 这动摇了什么、没动摇什么

### 动摇的

**Fable 拒路线 C 的理由之一被削弱了。** 它写：

> 我为了不让迁移成本挡住 P1→P2 链条，对一个**已经兑现过的风险**给了过轻的处置。

**那个风险没有兑现过，而「已经兑现过」这个说法是从我的决裁包里来的。**

同理，`dec-four-owner` 第 3 件 #4「现相容忍」的自陈弱点，其分量也随之改变。

### 没有动摇的

- **L-5 缺陷是真的**，且已由 Aaron 于 2026-08-10 裁定。
- **失败模型的通道 A／B 分析仍然成立**——它们从来就是分析，不是事故报告；
  §0 写的是「registry **住在**一棵被主动同步的树里」，那是前提陈述。
- **配置是活的、只是休眠**——`REGISTRY_SYNC_FAILURE_MODEL.md` §6「迁出同步树是
  结构性关死那个窗口的唯一办法」不因休眠而变假。
- **`Desktop` 被已知文件夹重定向到 OneDrive 是实测事实**，与同步是否活跃无关。

**所以迁移的理由仍在，紧迫性下降。** 这两件事必须分开说，而我此前把它们绑在一起了。

---

## 5. 已改的与刻意不改的

**已改（builder 自己写的断言）**：

```
ops/DECISION_PACKET_FOUR_OWNER_ITEMS.md
ops/DIRECTORY_CREATION_GRANTS.md
ops/REGISTRY_MIGRATION_PLAN_ROUTE_A.md
qros-runtime/tests/test_save_dir_configuration.py（docstring）
```

**刻意不改**：`ops/RULING_FABLE_FOUR_OWNER_2026-08-27.md` 的两处
——**那是决裁席原话的逐字转录**。转录不得因转录者事后发现前提有误而被改写；
本更正在该文件末尾**追加**指向，原文一字不动。

---

## 6. 必须让谁知道

```
1. 正在进行中的迁移方案 fresh Sol 复审  —— 送审文件里就有这句夸大
2. dec-four-owner 与 dec-registry-migration 两个决裁席 —— 若它们要重估
3. Aaron —— 路线选择可能因此不同（C 被拒的理由之一削弱了）
```

**builder 不代 Aaron 判要不要重开路线选择。** 但他应当知道：**两份裁定拒绝路线 C
的力度，部分来自一句我写错的话。**
