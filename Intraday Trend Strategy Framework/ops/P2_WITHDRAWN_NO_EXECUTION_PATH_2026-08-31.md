＃ P2 已撤回 —— 这个 build 没有执行路径,而那是我错报的

```ini
RECORD_TYPE=EXECUTION_EVIDENCE ＋ builder 错误记录
DATE=2026-08-31
OUTCOME=P2 行已无痕撤回（未提交即还原）
RESEARCH_DEGREE_OF_FREEDOM=**未消耗** —— 什么都没跑，未读任何 Development 数据
AARON_DECISION=乙（撤回），见下
```

---

## 0. 事实,按发生顺序

```
1  Aaron 逐字回贴 P2 授权句（第二版；第一版是我呈错的块，见 §2）
2  builder 复验 HEAD == 89b514a、两仓干净、逐字匹配
3  追加 P2 行（序号 15），链解析 ('P1','P2')，live authorizations = 1
4  写见证（每次追加后的强制义务）
5  **实测生产入口** —— 拒绝信息变了，但不是「授权不够」：
       a live authorization row exists but this build carries no execution
       path — N04 ships DEFAULT-REFUSE and the ratification authorizes
       grammar, not execution
6  核实：run_supplement_production 的签名是 `-> NoReturn`，
   末尾是一条无条件 raise。**这个 build 里没有执行路径，按设计如此。**
7  停下来告诉 Aaron，未提交任何东西
8  Aaron 选「乙」：撤回
9  还原（未提交，无痕），实测回到 P1 状态
```

## 1. 撤回后的实测

```
registry sha256   3ddbfb626c3d1a0a…（== P1 追加后的状态）
chain short_ids   ('P1',)
live P2           0
SUPPLEMENT_EXECUTION_AUTHORIZED 行数   0
生产入口          回到「0 live … row(s)」
```

**见证 `WITNESS_P2_APPENDED_2026-08-31.json` 保留。**
见证根是 append-only，而它记录的是一个**确实存在过**的状态。
本文件即为它的去向记录 —— 不留悬空的哈希。

## 2. 我的两个错误,分开记

### 2.1 呈错了授权块（当场发现，未造成后果）

我照**合同** `supplement_contract.EVENTS["P2"].required_fields` 拟块，
而真正判它的是**解析器** `supplement_registry`，两者字段名不同：

```
合同     supplement_id · authorized_commit_40hex · output_root ·
         verbatim_authorization_sentence
解析器   supplement_id · authorized_commit · output_root
         且 note 必须以 START_MC_DS_S001_DAY_STRATA_SUPPLEMENT_EXECUTION 开头
```

第一块因此三处错。**拦住它的是我在内存里先跑了一遍** —— 而我本该在**呈块之前**就跑，
P1 那次刚学过这一课并写进记录。

**这两处字段名不一致本身是一个缺陷**（同一件事的两份声明，其中一份会走味），
记为待办。

### 2.2 **错报了剩余距离** —— 这一条更重要

我一路说「P2 → MC 真跑 → 策略 build」，把 P2 说成最后一道闸。

**它不是。P2 之后还有一整条执行路径，而它不存在。**

**这是可查的**：入口函数的签名就写着 `NoReturn`；C_BUILD_2 与 C_BUILD_3 的注释
写着「unreachable in this build」；我今天多次读过这个文件。
**我在告诉 Aaron「剩三步」之前，没有去查入口点自己会不会返回。**

## 3. 由此暴露的一个顺序死结（值得单独记住）

```
授权绑定 commit 89b514a，并写明「若 HEAD 移动，本授权失效」
让运行成为可能 = 写执行路径 = 提交代码 = HEAD 移动 = 授权失效
```

**按其字面，那份授权永远不可能被行使。**

**正确顺序是：先建执行路径，再授权。** 我把它做反了。
「授权绑 HEAD」这条约束本身是对的（它防的是「批了 A、跑了 B」），
错的是在没有可跑之物时就去索取它。

## 4. Aaron 的裁定

> 乙

（三选项：甲 = 保留 P2 行并提交；**乙 = 撤回**；丙 = 停下明天再说。）

**builder 曾建议乙，理由是可验证的**：一条永远不能被行使的 live 授权留在 registry 上，
会让后来读它的人以为运行被批准过 —— 而 `live_authorizations: 1`
在任何自动检查里都是「已授权」。**那是一条会误导的记录，而它当时还可以无痕撤回。**

## 5. 接下来真正要做的

```
建执行路径      N04 目前是 DEFAULT-REFUSE。这是工程工作，不需要新授权
                （Aaron 2026-08-29：「建代码不等于跑代码」）
建完之后        重走 P2：呈块 -> 逐字回贴 -> 追加 -> 实测门 -> 跑
不要再做的      在没有可跑之物时索取绑定 commit 的执行授权
```
