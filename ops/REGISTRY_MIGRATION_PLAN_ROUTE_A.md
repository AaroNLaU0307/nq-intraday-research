# registry 迁移方案 —— 路线 A（待 fresh Sol 审 ＋ Aaron 亲批）

```ini
RECORD_TYPE=MIGRATION_PLAN
STATUS=PLAN_ONLY —— 本文件不迁移、不创建任何目录、不 git init、不改任何路径
BY=Opus 5，builder seat，2026-08-27
BASIS=dec-registry-migration-2026-08-27（路线 A ＋ 十条不变量），Aaron 已采纳
CHAIN=本方案包 → fresh Sol 审 → Aaron 亲批并执行
AUTHORIZATIONS_STILL_NO=八项全部；DIRECTORY_CREATION_AUTHORIZED=NO 尤其相关
```

**执行本方案需要两条 Aaron 的独立授权**（ND1 明令不得合并）：新仓目录的创建、
迁移动作本身。**本文件不构成、不请求、也不预设其中任何一条。**

---

## 1. 为什么要迁 —— 一句话与一个环境事实

registry 是 append-only 的事件真相源，而它今天在**主动同步的 OneDrive 树**里。
本项目**已经因云同步残渣撞上 exact-set 磁盘不变量烧掉过一次 trial**（L-5）。

**一个 builder 实测的环境事实，说明这不是「有人把仓放错了地方」**：

```
HKCU\...\User Shell Folders
  Desktop  -> C:\Users\Aaron\OneDrive\Desktop        ← 已知文件夹重定向
  Personal -> C:\Users\Aaron\OneDrive\Documents
OneDrive.Sync.Service 运行中
```

**这台机器上的桌面就是 OneDrive。** 任何放在桌面下的仓都在同步树里，与放置者的
选择无关——所以「注意别放进去」不是可行的缓解，迁出才是。

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

## 4. 执行步骤（每一步对应一条或多条不变量）

**顺序不可重排。** 每一步的失败处置一律是 STOP 上报，**不得清理后重试**（不变量
FALSIFIER）。

```
S0  前置核证                                     不变量 9 · 6
    · 重测 §3 的环境核证全部项目
    · 扫 ops/ 下 TRIAL_REGISTRY* 的非精确名（OneDrive 冲突副本形态）
    · 扫目的地一侧同样命名（裁定把第 6 条扩到了目的地）
    · 任一命中 ⇒ STOP

S1  见证先行                                     不变量 3
    · 按 registry_witness 格式手工写一条见证：{sha256, 事件计数, 末行}
    · 见证放在 registry git 仓之外的兄弟路径（不变量 9 后半）
      提议：C:\Users\Aaron\quant-data\registry-witness\itsf\  ← 已授权创建、今为空
    · 目的：任何单条 git 操作（reset/checkout）都不可能同时动到两者

S2  新仓 git init 并做首 commit                  不变量 7 · 10
    · 需要 Aaron 的目录创建授权（封闭清单：itsf-registry 一条）
    · git init 后先做一个不含 registry 的首 commit（README/.gitignore）
    · 记下新仓首 commit 的 40hex

S3  移字节                                       不变量 1 · 2
    · 逐字节复制到 <新仓>/ops/TRIAL_REGISTRY.md
    · 立刻重算 sha256 与行数：必须与 S0 重测值逐字节相同、行数不减
    · 不得借机规范化、不得改行尾、不得改编码

S4  两仓交叉互钉                                 不变量 7
    · 新仓：首个含 registry 的 commit，message 记录
      { 旧仓迁移 commit 的 40hex（S5 之后回填，或先留占位再 amend——见下）,
        registry 的 sha256 / 行数 / 末行 }
    · 旧仓：迁移 commit 记录新仓首个含 registry 的 commit 40hex ＋ 同一组三元组
    · 循环依赖的处置：新仓先记三元组与旧仓 HEAD（迁移前），
      旧仓迁移 commit 记新仓的 commit —— 单向即可闭合，不需要 amend

S5  旧路径处置                                   不变量 4（裁定修改后的形式）
    · 原路径 ops/TRIAL_REGISTRY.md 放一个**故意不合六格语法**的墓碑文件，
      指明新位置
    · 逐字节副本改名保留：ops/TRIAL_REGISTRY.pre-migration.2026-08-27.md
    · 保留 ≥ 一个完整工作周期；回滚不需要任何新授权

S6  路径切换                                     不变量 5（已先行落地）
    · registry_boundary 的常量指向新仓的绝对路径（不变量 8：冻结精确串，
      禁止环境变量或配置文件覆盖）
    · 因不变量 5 已落地，这里只改一处

S7  后置核证
    · 全量套件绿
    · CR1_REGISTRY_INTACT_CRITERION 的「superset of the witness」对 S1 的见证成立
    · 再扫一次冲突副本（两侧）

S8  备份形态                                     不变量 10
    · 新仓 push 到另一物理卷上的 bare 仓，或定期 bundle
    · **禁止对新根做任何文件级同步复制**——那是把通道 A 原样请回来
    · 在真实运行恢复之前必须就位
```

---

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

```
触发   S0–S7 任一步失败，或后置核证任一项不成立
动作   把 ops/TRIAL_REGISTRY.pre-migration.2026-08-27.md 改回原名，
       撤销 S6 的常量改动，删除墓碑
授权   不需要任何新授权（不变量 4 明定）
不做   不清理、不重试、不「先修一下再说」——失败即 STOP 上报
```

**回滚窗口 ≥ 一个完整工作周期。** 期间新旧两份都在，且旧的**不在原精确路径上**
——裁定改这一条的理由是：一份留在原路径的陈旧真 registry 是最危险的形态，任何
漏改的读者会**成功地**读到旧事件集。

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
