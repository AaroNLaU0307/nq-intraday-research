# 穷举 `resolve_partial` 的出口，找到第五个 —— 以及它为什么**不是**缺陷

```ini
RECORD_TYPE=FINDINGS_PENDING_UNFREEZE
DATE=2026-08-29
FOUND_BY=builder（工作会话）
METHOD=从源码 AST 穷举所有 return/raise，而不是「测我想到的情形」
STATUS=**不改任何字节** —— supplement_runner.py 与 R3 都在 c-build-2-wording-r3
       的冻结登记册里，复审席持有中
```

## 0. 方法，以及它为什么值得单说

今晚在姊妹仓 `qros-runtime` 找到第七、第八实例，用的都是同一招：
**不去测我想到的形状，而是穷举整个域**（十七种词法形状全被拒 → 逐个扫 128 个 ASCII 码位 → 0x7f）。

**把同一招用回这里**：§12.7 说 `resolve_partial` 有「四条分歧结局」，
那是我**想**出来的。从源码 AST 穷举它的每一个 `return` 与 `raise`：

```
return  already_sealed
raise   supplement_seal_conflict
return  retry_permitted                     （branch C）
raise   supplement_partial_verify           （branch E）
raise   supplement_post_promotion_verify    <- 我从未测过这一条
return  promote
合计 6 个出口
_preserve 另有 2 个：divergent_partial_exists（raise）· 返回新名
_divergent_name 另有 1 个：incident_id_malformed
```

## 1. 第五条分歧类出口的实测

`supplement_post_promotion_verify` —— `os.replace` 之后复读 FINAL 与 intended 不符。
**它的处境与其余四条都不同：`.partial` 已被 `os.replace` 消耗掉了。**

```
码             supplement_post_promotion_verify
目录           ['f.json']
FINAL 在场      是
.partial 还在   否（已被 replace 消耗）
留下分歧件      **否**
```

**而重试会静默成功：**

```
第一次调用（瞬时故障）   raise supplement_post_promotion_verify
第二次调用（故障消失）   already_sealed · byte-identical
之后磁盘上                没有任何东西记得曾经失败过
```

## 2. 为什么它**不是** `resolve_partial` 的缺陷

**这一条我特意把推论那一半也量了** —— §12.5 的教训就是「量对一半、推错一半」。

事故本该记在 **registry**（F 系列事件），不是记在文件系统。所以问题是：
**这个失败码会不会被记成事件？**

```
plan_failure_event 的签名   (failure: GateFailure, *, supplement_id, incident_id,
                            has_p3, attempts_dir="", residue_path="")
resolve_partial 里是否调用它  **否**（源码实测）
```

`resolve_partial` 只是抛 `SupplementRunnerError`；**记什么事件由调用方决定**。
而调用方是执行路径 —— 它今天是 `BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`，
**五道门无条件拒绝，生产中没有任何东西调用 `resolve_partial`。**

**所以「这次失败有没有被记录」在今天的代码里根本无法回答**，
因为要回答它的那个组件还不存在。

## 3. 那么它是什么：一项**未被记录的义务**

```
未来的执行路径必须：
  在 resolve_partial 抛出 supplement_post_promotion_verify 时，
  规划并追加一条失败事件 —— 因为文件系统这一侧不留任何痕迹，
  registry 是唯一能记住它的地方。

今天没有任何文档记着这项义务。
```

**这就是本件的全部主张。** 我没有把它写成缺陷，也没有改任何字节。

## 4. 顺带：§12.1 (c) 的枚举与这一条的关系

(c) 现在列四条分歧结局。**这是第五条**，且它与其余四条有一个结构差异：
其余四条都把字节留在一个**可追溯的名字**下（`.partial` 或
`.partial.divergent.<incident_id>`），**这一条留在 `f.json` 这个普通名字下**，
与一个正常封存件在名字上不可区分。

**是否应当进 (c) 的枚举，是设计问题，归 Aaron 与决裁席**，不归本件。
我倾向「应当进，且应当明写它是唯一不留具名残留的那一条」——
**但那要改 §12，而 §12 正被复审席持有。**

## 5. 解冻后要做的（清单）

```
一、把这项义务写进 N09 执行路径设计的「越过骨架需要什么」一节
    —— 那一节现在整节归 Aaron，builder 不代填，所以只提出、不填写
二、给 supplement_post_promotion_verify 补一条行为测试
    （今天全仓只有两处提到它，都在 docstring 里，没有一条测试跑到它）
三、§12.1 (c) 是否收纳第五条，等 Aaron / 决裁席
```

## 6. 本件不做什么

不改 `supplement_runner.py` 一个字节（冻结中）；不改 §12；不改 §15；
不追加任何 registry／exposure 行；不主张任何缺陷。
