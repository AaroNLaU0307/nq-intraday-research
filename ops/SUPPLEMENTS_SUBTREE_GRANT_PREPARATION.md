# `supplements\` 子树的目录创建授权 —— 准备件（不是授权）

```ini
RECORD_TYPE=PREPARATION（不签、不代填、不创建任何目录）
BY=Opus 5，builder seat，2026-08-29
BASIS=N09 §7 第 2 项；DIRECTORY_CREATION_GRANTS.md §1 的五个槽
STATUS=NOTHING_AUTHORIZED —— DIRECTORY_CREATION_AUTHORIZED 仍为 NO
```

## 1. 封闭路径清单 —— 父层，两条，今天就确定

```
C:\Users\Aaron\quant-data\itsf-runs\supplements
C:\Users\Aaron\quant-data\itsf-runs-archive\supplements
```

**实测 2026-08-29**：两个治理根都存在；**两个 `supplements` 子树都不存在**。
决裁的 CONDITIONS 明写它们在授权执行前必须继续保持不存在——**保持中**。

无通配符，无变量，两条路径逐字确定。**这一份可以今天签。**

## 2. 但还有第二层，而它与授权形制相抵 —— 这一条必须先裁

`plan_supplement_paths`（`supplement_runner.py:209-213`）产出的真实目标是：

```
<runs_root>\supplements\<supplement_id>_<UTC>
<archive_root>\supplements\<supplement_id>_<UTC>
```

目录名由已批准值 `ND1_SUPPLEMENT_DIRECTORY_NAME=2_ID_UNDERSCORE_UTC` 规定，
**`<UTC>` 是运行时刻的 `YYYYMMDDTHHMMSSZ`**。

而 `DIRECTORY_CREATION_GRANTS.md` §1 的形制要求：

```
精确文本   必须逐字，且含**封闭枚举的绝对路径清单** —— **不得含通配符**
有效期     绑事件：用掉即失效。一份授权 ＝ 一次创建动作 ＝ 恰好那个封闭清单
```

**运行时刻的 UTC 在签授权时不可能知道。** 所以这两条不可能被同一份封闭清单覆盖。

### 三条出路，各自的代价（builder 不代选）

```
甲  P2 覆盖运行时目录创建
    执行授权本身就绑 supplement_id + 40hex commit + output_root，
    由它蕴含「在 output_root 下按已批准命名规则创建本次运行的目录」。
    得：不需要你在运行时刻在场。
    失：ND1 明令目录创建与执行是两条**不得合并**的授权 ——
        这条出路正面抵触那条明令。**builder 认为它走不通，但不代裁。**

乙  运行时刻再签一份
    执行前 builder 把实际 UTC 查实、呈交封闭清单，你当场签。
    得：完全符合现有形制。
    失：你必须在运行那一刻在场。

丙  修订命名规则
    把 <UTC> 从目录名里去掉，或改成签授权时可确定的东西。
    得：一份授权覆盖到底。
    失：ND1_SUPPLEMENT_DIRECTORY_NAME 是**已批准值**，改它要走修正案，
        而 A2 永久 HOLD 使修正案没有可满足的前置门。
```

**builder 的意见（非裁定）**：倾向 **乙**。甲正面抵触 ND1 的不得合并明令；
丙要动已批准值。乙只花你运行那一刻的几分钟，且完全在现有形制内。

## 3. 五个槽 —— 父层这一份要什么

| 槽 | 要求（`DIRECTORY_CREATION_GRANTS.md` §1） | 我能确认的 |
|---|---|---|
| 来源 | Aaron 具名消息中的**主动逐字发送**；「好」「批准」二字不够 | —— 只能是你 |
| actor | 授权只能是 Aaron；执行可委托主代理**手工** | 我可执行 |
| 精确文本 | 逐字，含封闭枚举绝对路径清单，**不得含通配符** | §1 两条 |
| 绑定 | **绑路径，不绑 commit** | —— |
| 有效期 | **绑事件：用掉即失效** | —— |

**builder 不呈交待你回贴的句子块**：决裁席对「呈交＋回贴」这个形制自陈置信度
MEDIUM，并建议从严者胜；目录创建改变文件系统状态且不可无痕撤销。**句子请你亲笔。**

## 4. 执行时的 fail-closed（决裁明列，我会照做）

```
清单中任一路径已存在      -> STOP 上报，不得以「反正目标态一样」继续
门后快照出现清单外字节     -> 判失败，全部上报，**不得清理后重试**
门前门后 exact-set 快照    -> 追加进 DIRECTORY_CREATION_GRANTS.md §4 台账
```

## 5. 本件不做什么

不授权任何目录创建；不创建任何目录；不呈交授权句子块；
不选择 §2 的三条出路；不追加任何 registry／exposure 行。
`DIRECTORY_CREATION_AUTHORIZED` 仍为 `NO`。
