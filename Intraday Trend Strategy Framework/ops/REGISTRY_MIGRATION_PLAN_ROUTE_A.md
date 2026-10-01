# registry 迁移方案 —— 路线 A（待 fresh Sol 审 ＋ Aaron 亲批）

```ini
RECORD_TYPE=MIGRATION_PLAN
REVISION=R3（2026-08-27，决裁席裁 GIT_ONLY 之后；Aaron 已采纳该裁定）
STATUS=PLAN_ONLY —— 本文件不迁移、不创建任何目录、不 git init、不改任何路径
BY=Opus 5，builder seat，2026-08-27
BASIS=dec-registry-migration-2026-08-27（路线 A ＋ 十条不变量），Aaron 已采纳
CHAIN=本方案包 → fresh Sol 审 → Aaron 亲批并执行
AUTHORIZATIONS_STILL_NO=八项全部；DIRECTORY_CREATION_AUTHORIZED=NO 尤其相关
```

**执行本方案需要两条 Aaron 的独立授权**（ND1 明令不得合并）：新仓目录的创建、
迁移动作本身。**本文件不构成、不请求、也不预设其中任何一条。**

---

## 0. 这一版是被 HOLD 之后的修订 —— 先读这节

fresh Sol 复审判 **HOLD**，八条 finding。**它最强的一条是致命的**：

> **成功路径自身不可达。** S5 创建 `ops/TRIAL_REGISTRY.pre-migration.2026-08-27.md`，
> 它必然匹配故障模型边界 (2) 的非精确 `TRIAL_REGISTRY*` 拒绝模式；S7 再扫时必然命中。
> 若临时豁免，又会未经设计地削弱冲突副本检测。

**builder 复现属实**，`fnmatch('TRIAL_REGISTRY.pre-migration.2026-08-27.md',
'TRIAL_REGISTRY*')` 为真且不等于精确名。

### 三条 builder 不修，因为不该由 builder 修

| finding | 为什么不由 builder 处置 |
|---|---|
| **S5 文件名撞边界 (2)** | **那个文件名是裁定原文给的例子**（不变量 4 修改条：「副本用改名形式（如 `ops/TRIAL_REGISTRY.pre-migration.<date>.md>`）」）。复审席找到的是**裁定里的缺陷**。builder 自选一个新名把它绕过去，正是「实现者自行挑一种读法」的形态——第六轮 HOLD 的 Finding 1 同形 |
| **R4 是必须的** | 复审席判得比决裁席严：「仅凭外部批准文本把『git history』的所指从 ITSF 仓改成新仓，是未绑定进 canonical 字节的语义变更」。**builder 认为它对**，但推翻决裁席的裁定归 Aaron |
| **`RegistrySnapshot` 是接口改动** | 它逐条给了理由（必填字段破坏三参数构造；默认字段仍改 equality／repr／asdict／模式匹配；且 snapshot 哈希的是工作区字节而 HEAD 未必含那些字节）。**builder 接受**，但这改变了裁定 Q1 的实施形态 |

### 已修的两条（代码层，各自变异证红）

```
finding 5  墓碑 ≠ 缺失 —— registry_boundary 加具名标记识别，墓碑点名拒绝
           刻意不扩成「拒绝一切不可解析的」：截断归见证，混进来会把真事故藏起来
finding 6  S6「只改一处」未覆盖写者 —— 守卫扩到 scripts/，
           s0_real_run.py 的两处构造具名登记并计数
```

**下面 §4 的执行序按其余三条（fencing／S4 拓扑／备份合同）重写。**

---

## 0bis. R3 —— 决裁席裁了 S5，且明说是**修订**而不是解释

`dec-s5-r4-2026-08-27`，Aaron 2026-08-27 采纳。逐字要点：

```
RULING=GIT_ONLY
```

> **并明说：这是对不变量 4 修改条的修订，不是解释。** 原修改条给出的形式
> （改名副本 `ops/TRIAL_REGISTRY.pre-migration.<date>.md`）**作废**，因为它与边界 (2)
> 按构造相撞。

### 不变量 4，修订后的全文（本方案自此按此执行）

```
逐字节副本保留由两者共同承担：
  (i)  旧仓 git 历史中 O0 所含的 registry blob
       —— 自动保留、内容寻址、历史不可重写
  (ii) 新仓中经 == SHA0 核证的那一份
不在任何工作区创建第二份可读副本。
回滚 = 从 O0 做字节级取回并核 == SHA0，不需要任何新授权。
```

**决裁席给的理由，记在这里以免下一个读者以为是 builder 的选择**：三个选项下旧仓
git 历史**都**保留着迁移前字节 —— O0 提交里的 blob 就是那份字节的逐字节副本，
内容寻址钉死，历史重写被常设禁令封死。**保留与否从来不是选择题**；真正的选择只是
「要不要**再**造一份工作区可读副本」。原裁定改不变量 4 的理由是「陈旧真 registry
是最危险的形态」，而那条理由本身就反对**任何**可读陈旧副本 —— RENAME_OUT 只是
把危险换了个地址。

### 四条强制条件（缺一即非本裁定）

```
C1  S0 增加一项核证：git show <O0>:ops/TRIAL_REGISTRY.md 的字节
    == 工作区字节 == SHA0。不等 ⇒ 存在未提交追加 ⇒ 边界 (3) 已被破坏 ⇒ STOP
C2  回滚步骤重写为字节级取回（不得信任裸 git checkout）；取回后重算 sha256
    必须 == SHA0；§7 须随之重写；回滚窗口 ≥ 一个完整工作周期不变
C3  墓碑要求一字不减
C4  边界 (2) 本次不接入；接入立为独立事项，且仍是真实运行的前置条件
```

**C1 为什么必要**（决裁席原话要点）：registry 被 clean gate 白名单豁免，
**历史副本与磁盘副本可能不一致而不打红** —— 不核这一条，GIT_ONLY 的前提就是
未经验证的。

### 决裁席自陈的最弱处，原样记录

> GIT_ONLY 把旧仓侧的第一线回滚押在 **OneDrive 树内的 git 对象库**上 —— 恰是本次
> 迁移不信任的那棵树，而 OneDrive 弄坏 `.git` 松散对象是真实存在的故障形态。
> …… GIT_ONLY 把旧树内回滚介质从两种收窄到一种。Aaron 若对此残留风险另有权衡，
> 回退项是 NEW_REPO_ONLY。

**FALSIFIER**：若 C1 的核证失败且不可归因于可修复的未提交追加，GIT_ONLY 前提坍塌，
**回退项是 NEW_REPO_ONLY，不是 RENAME_OUT**（文件名撞边界的缺陷与此无关，仍然成立）。

---

## 1. 为什么要迁 —— 一句话与一个环境事实

registry 是 append-only 的事件真相源，而它今天在一棵 **OneDrive 树**里。

**同步是休眠的，不是活跃的**（Aaron 2026-08-27 指出，builder 实测证实）：仓内
文件属性只有 `Archive`，无 `Offline`／`ReparsePoint`／`RecallOnDataAccess`；
全仓零个冲突副本；主客户端 `OneDrive.exe` 未运行；最后登录 2026-01-06。
**但账户仍配置着，OneDrive 根与其下 `Desktop` 都是重解析点——一次登录就会把
这棵树纳入管理。风险是「一步之遥」，不是「不可能」。**
L-5 是**真实缺陷**（2026-08-10 裁定），其机制**会**让同步残渣撞上 exact-set
磁盘不变量并烧掉一次 trial。**更正：至今没有 trial 被烧掉过**，registry 里
`BURNED/ABORTED/VOID` 事件数为 0——builder 此前把机制写成了已发生的事故，
见 `ops/CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md`。

**一个 builder 实测的环境事实，说明这不是「有人把仓放错了地方」**：

```
HKCU\...\User Shell Folders
  Desktop  -> C:\Users\Aaron\OneDrive\Desktop        ← 已知文件夹重定向
  Personal -> C:\Users\Aaron\OneDrive\Documents
OneDrive.Sync.Service 运行中（注意：这是服务组件，不是同步客户端本身）
```

**这台机器上的桌面就是 OneDrive。** 任何放在桌面下的仓都落在 OneDrive 树里，
与放置者的选择无关——所以「注意别放进去」不是可行的缓解。**这一条不因同步休眠
而变假**：休眠可以结束，重定向不会。

`ops/REGISTRY_SYNC_FAILURE_MODEL.md` §6 早已写明：**迁出同步树是结构性关死那个
窗口的唯一办法。**

---

## 2. 迁前状态（builder 实测，2026-08-27）

```
路径        ops/TRIAL_REGISTRY.md
sha256      ee9da33fdbb47725dc036243adc76d7d9ba69ff06df0df443b09103f897353d6
字节        6697
表格行数    17
行尾        LF only
末行        | + | 2026-08-13T17:04:32+00:00 | COMPLETED | 876c1b7 |
            main agent (s0_real_run) | [S0-T001] S0 report sealed
```

**这三元组（sha256 / 行数 / 末行）就是不变量 1、2、7 要交叉互钉的东西。**
执行时必须重测——上表是方案期的值，不是执行期的值。

---

## 3. 目的地与环境核证（不变量 9，builder 实测）

**提议路径**：

```
C:\Users\Aaron\quant-data\itsf-registry\        ← 新 git 仓的根
C:\Users\Aaron\quant-data\itsf-registry\ops\TRIAL_REGISTRY.md   ← 相对路径不变
```

**相对路径保持 `ops/TRIAL_REGISTRY.md` 是刻意的**：已批准 CR1 语法块的
`CR1_REGISTRY_INTACT_PREIMAGE` 与 `COLD_RECOMPUTE` 都逐字点名这个相对路径。
保持它，那两句在新仓里逐字仍真。

**环境核证结果**：

```
C:\Users\Aaron\quant-data
  存在              是
  在 OneDrive 内    否
  realpath          C:\Users\Aaron\quant-data（与自身相同 ⇒ 非重解析点）
  在被重定向的已知文件夹下  否（Desktop/Personal 都指向 OneDrive；此路径不在其下）
  现有子项          commodity-carry · databento-archive · itsf-runs ·
                    itsf-runs-archive · registry-witness · review · tools
```

**`itsf-registry` 今天不存在**——这正是需要目录创建授权的那一个。

> **执行期必须重测**，不得采信本节：同步代理与重定向都是可变配置。
> 裁定的不变量 9 要求「机械核证新根不在任何主动同步／重定向之下，
> 不止 builder 已测的那两项」。

---

## 4. 执行步骤 —— R2，按复审席的三条重写

**三处改动**（其余保留）：

```
新增 FENCE   S0 与 S6 之间没有任何 registry 追加，且这一条是被验证的、不是被声明的
S4 改        采纳复审席给的拓扑，删掉 R1 里那句自相矛盾的「回填/amend」
S8 改        备份从「一句要求」变成一份可执行合同
S5 已裁      GIT_ONLY（R3）—— 只留墓碑，不留任何可读副本；见 §0bis
```

### FENCE —— 复审席 finding 2 的正面对象

它说的是：S3 之后旧仓的追加可在 S6 静默丢失，而 S7 对旧 S1 见证**仍可能通过**
（见证只证「不低于」，追加使计数变高，超集判据照过）。

**builder 复核成立**，且这正是见证设计的边界：**它防回退，不防分叉。**

```
F1  宣告静默期：S0 起至 S7 结束，任何 registry 追加一律 STOP
    —— 追加今天全部是主代理手工（八项授权全 NO），所以静默期靠纪律可达
F2  S0 记录 SHA0 = 旧 registry 的 sha256
F3  S6 切换之前重测旧 registry：sha256 必须仍等于 SHA0
       不等 ⇒ 静默期被破坏 ⇒ STOP，全部回滚，不得「把新的行补进新仓」
F4  S7 的见证核对改为双向：既要「新仓 ⊇ S1 见证」，也要「新仓 == SHA0」
       —— 单向超集判据放得过分叉，这是复审席点出的漏洞
```

### 执行序（R3：S5 已裁，方案恢复可执行）

```
S0  前置核证                                     不变量 9 · 6 · F2 · **C1**
    · 重测环境全部项（复审席与 builder 的实测不一致过一次，见 §3 注）
    · 扫两侧 TRIAL_REGISTRY* 非精确名；任一命中 ⇒ STOP
    · 记录 SHA0 / 行数 / 末行
    · **C1（R3 强制）**：记下 O0 = 当前 HEAD；核
        git show <O0>:ops/TRIAL_REGISTRY.md  的字节 == 工作区字节 == SHA0
      三者必须逐字节相等。**不等 ⇒ 存在未提交追加 ⇒ 边界 (3) 已被破坏 ⇒ STOP。**
      理由：registry 被 clean gate 白名单豁免，历史副本与磁盘副本可以不一致
      而不打红；GIT_ONLY 把回滚押在历史副本上，因此这一条是它的前提而非附加检查
    · 取字节须 binary-safe（见 §7 同一注意事项）
    · 宣告静默期开始（F1）

S1  见证先行                                     不变量 3
    · 手工写一条见证 {sha256, 事件计数, 末行} 到已授权的见证根下
    · 该路径在 registry 仓之外（不变量 9 后半），
      任何单条 git 操作动不到两者

S2  新仓 git init ＋ 首 commit（不含 registry）    不变量 7 · 10
    · 需要 Aaron 的目录创建授权（封闭清单：itsf-registry 一条）
    · 记下新仓首 commit = N0

S3  移字节                                       不变量 1 · 2
    · 逐字节复制到 <新仓>/ops/TRIAL_REGISTRY.md
    · 重算 sha256 必须 == SHA0；行数不减；不规范化、不改行尾编码

S4  两仓交叉互钉（拓扑由复审席给定）              不变量 7
    · N1 = 新仓首个含 registry 的 commit，message 记录：
        { O0 = 旧仓迁移前 HEAD, SHA0, 行数, 末行, 两仓定位符 }
    · O1 = 旧仓迁移 commit（parent = O0，内容含 S5 ＋ S6），message 记录 N1
    · 顺序固定：N1 → O0，然后 O1(parent=O0) → N1
    · R1 里那句「回填/amend」已删 —— 它与同节的「无需 amend」自相矛盾，
      而 S4 当时旧仓迁移 commit 尚不存在，根本无可钉
    · 单边失败恢复：N1 已成而 O1 未成 ⇒ 新仓保留、旧仓不动、STOP 上报；
      不得为凑对称去 amend 任何一侧

S5  旧路径处置                                   不变量 4（R3 修订版）· C3
    · **只留墓碑，不留任何可读副本**（GIT_ONLY）
    · 旧精确路径 ops/TRIAL_REGISTRY.md 写入墓碑，含具名标记
      REGISTRY_MOVED_NOT_A_REGISTRY 与新仓定位符
    · registry_boundary 已按该标记点名拒绝（finding 5，变异证红）
    · **不创建改名副本** —— 原裁定给的那个文件名已由 R3 作废；
      不另选新名（那正是「实现者自选读法」）
    · C3：墓碑要求一字不减
    · 逐字节副本此刻由 O0 的 blob 与新仓那份共同承担，二者都已在 S0/S3 核过

S6  路径切换                                     不变量 5 · 8 · F3
    · 先执行 F3：旧 registry 的 sha256 仍 == SHA0，否则 STOP
    · registry_boundary 的常量指向新仓（冻结精确串，禁环境变量覆盖）
    · scripts/s0_real_run.py 的两处登记构造同改
      （finding 6：它们在守卫的登记表里，不是被遗漏的）

S7  后置核证                                     F4
    · 全量套件绿
    · 双向：新仓 ⊇ S1 见证，且新仓 == SHA0
    · 再扫两侧冲突副本
    · 静默期在此结束

S8  备份合同（不是一句要求）                      不变量 10
    · 目标：另一物理卷上的 bare 仓，或离线 bundle
    · 目标卷须先核证：非同步、非重解析点、与源不同物理卷
    · 策略：仅快进推送；禁止 force、禁止 delete、
      禁止任何文件级同步复制
    · 周期：每次 registry 追加后一次；保留 ≥ 一个完整工作周期
    · 完整性：定期 git fsck；恢复演练至少一次并留证据
    · 目标仓的创建同样需要独立的目录创建授权 —— 不在本方案已请求之列
```

**S8 的硬件前提今天未满足（builder 实测 2026-08-27）。**

```
Get-CimInstance Win32_LogicalDisk  ->  只有 C:（DriveType=3，本地固定盘）
无第二块固定盘 · 无可移动卷 · 无网络盘
```

不变量 10 要求「另一物理卷上的 bare 仓，或离线 bundle」，而本机只有一个卷。
**因此 S8 今天无法完成，与授权与否无关。**

**这不阻断 S0–S7**：备份合同是迁移完成后的持续义务，不是迁移的前置条件。
**但它意味着迁移完成后会有一段没有异卷备份的时间**，直到有第二块盘为止 ——
授权迁移时应当知悉这一点。见 `ops/OWNER_DECISIONS_2026-08-27.md` §2。

**R3 之后方案恢复可执行**，但**执行仍被两条 Aaron 的独立授权挡住**（新仓目录创建、
迁移动作本身），八项授权字段今天全部为 NO。**「可执行」指的是方案自身不再自相矛盾，
不是指今天可以动手。**

**另附 C4 的边界条件，以免它被读成放松**：边界 (2) 本次不接入，但失败模型 §0 的
「边界不落地不许再跑消耗 trial 的真实运行」**不因本裁定松动** —— 接入不搭车
≠ 可以无限期不接。该事项已单列，见 `ops/DEFERRED_AFTER_MIGRATION.md`。

## 5. 不变量 5 与 8 已经先行落地

裁定明裁不变量 5「先行」，且它路线无关。**已完成并提交**：

```
不变量 5  四处路径构造收敛到 registry_boundary 一处
          守卫 tests/test_registry_path_single_construction.py
          变异证红 3 条（含裁定 Q4 点名的「第二处伪造构造必须打红」）
不变量 8  registry 文件缺失改为 BoundaryError 拒绝
          守卫 tests/test_registry_absence_refuses.py
          变异证红 3 条
```

**执行时顺带发现两件，两份裁定都没有**：

1. **不变量 8 单独修是空修。** 四处生产站点每一处都带同一个
   `read_text(...) if exists() else ""`，完全绕过边界。5 与 8 是同一个修法。
2. **`consumer.py` 用的是相对路径** `Path("ops/TRIAL_REGISTRY.md")`
   ——只在进程恰好从仓根启动时才解析得对。收敛顺带修掉了。

---

## 6. 三件本方案自己不能解决、须复审席判的

### ① 两仓的 commit 语义（裁定 Q1 已裁，但实施仍有一处未定）

裁定：`authorized_commit_40hex` 继续且**只绑 ITSF 代码仓的 commit**，一字不改；
registry 仓的钉法走证据层——凡今日记录 `registry_sha256` 之处随行加记 registry
仓当时的 40 位 HEAD 作**旁证**，sha256 仍是主判据。

**未定的一处**：`RegistrySnapshot` 今天不带 registry 仓的 HEAD 字段。加它是**改动
一个已认证接口**吗？还是纯加性？**builder 不自判**。

### ② 「所指已移」—— 裁定自己标的弱点

`c251335f…` 批准时「git 历史」的默认所指显然是 ITSF 仓；路线 A 把所指换成一个
**批准时不存在的仓**。裁定的缓解是治理性的：

> **Aaron 的批准文本必须显式指名新仓为 `COLD_RECOMPUTE` 的所指**，使所指变更
> 经过他之手而非默认发生。

**请判这条缓解够不够**，还是仍须走 §D.10.3 出 R4 重签 CR1 语法块。裁定自己说
「若认为不够仍须 R4，我不反对，那是更保守的同向裁定」。

### ③ 边界 (3) 的提交纪律在新仓下如何续存

`REGISTRY_SYNC_FAILURE_MODEL.md` 边界 (3) 要求「registry 追加与 `git commit` 属
**同一操作步骤**」、仲裁顺序「git 历史 > 见证 > 工作区」。

**新仓下这条逐字仍可执行**（它没说是哪个仓），但**它现在跨了两个仓**：一次治理
追加要在新仓 commit，而相关的代码状态在旧仓。**请判是否需要为此定一条跨仓的
提交纪律**，还是边界 (3) 原文已足。

---

## 7. 回滚

**R3 改写（条件 C2）。** 原文依赖那个已作废的改名副本，因而整节重写。

```
触发   S0–S7 任一步失败，或后置核证任一项不成立
动作   1. 撤销 S6 的常量改动（registry_boundary 与 s0_real_run.py 两处）
       2. 从 O0 做**字节级取回**到 ops/TRIAL_REGISTRY.md
       3. 重算 sha256，必须 == SHA0
       4. 删除墓碑
授权   不需要任何新授权（不变量 4 R3 修订版明定）
不做   不清理、不重试、不「先修一下再说」——失败即 STOP 上报
```

### 第 2 步为什么不能用裸 `git checkout`

**决裁席条件 C2 逐字**：不得信任裸 `git checkout` —— **Windows 上 autocrlf 与
`.gitattributes` 可在检出时改写 LF-only 文件**。registry 是 LF-only 且其 sha256
是治理判据，一次静默的行尾改写就会让取回的字节 != SHA0，而**看起来一切正常**。

取回必须 binary-safe，取回后**必须**重算 sha256 并核 `== SHA0`。

```
不等 ⇒ STOP 上报，不得「先修一下再说」
```

这一条与 S0 的 C1 是同一个前提的两端：C1 证明 O0 里那份字节**当时**等于 SHA0，
本步证明取回**之后**仍然等于 SHA0。两端都不核，GIT_ONLY 就只是一句主张。

### 回滚窗口 ≥ 一个完整工作周期（不变）

期间新仓那份与 O0 里那份**都在**，而旧精确路径上是墓碑而非陈旧真 registry
——这正是 GIT_ONLY 比 RENAME_OUT 强的地方：**磁盘上根本没有第二份可读 registry**，
C3「不得被任何读者误当成 canonical」由机制承担，而不是靠命名与位置。

---

## 8. 请 fresh Sol 重点看的

1. **§4 的步骤序有没有一步能让 registry 在某个时刻既不在旧处也不在新处**，
   或两处都是「真的」而无法判定哪个权威。
2. **S4 的交叉互钉是否真的闭合**——builder 用「新仓记旧仓迁移前 HEAD、旧仓记新仓
   commit」来避开循环依赖，请判冷读者两侧是否都拿得到 `COLD_RECOMPUTE` 需要的东西。
3. **§6 三问**，尤其 ② 的「所指已移」够不够。
4. **不变量 10 的备份形态**：git push 到另一物理卷的 bare 仓，是否真与本次事故形状
   正交，还是引入了新的通道。
5. **本方案有没有默认了任何一条尚未授权的东西**——builder 的自查是没有，
   但这正是应当由别人查的。

---

## 9. 边界

本文件不迁移任何东西、不创建任何目录、不 `git init`、不改任何路径常量、
不追加任何 registry 或 exposure 行、不请求任何授权。

**八个授权字段仍全部为 `NO`。** 迁移的执行是
`dec-four-owner-2026-08-27` §8 第 ④ 项，`STILL_AARON_ONLY`。
