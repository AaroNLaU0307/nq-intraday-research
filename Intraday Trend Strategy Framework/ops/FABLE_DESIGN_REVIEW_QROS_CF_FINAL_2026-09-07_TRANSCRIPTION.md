＃ Fable 5.1 — QROS-CF 最终定界修复的**仅设计复审** — TRANSCRIPTION

```ini
RECORD_TYPE        = TRANSCRIPTION of a chat-carried design-only review result
                     (precedent: ops/ASTRA_P2_GATE_REVIEW_HOLD_F01_F06_2026-09-07_TRANSCRIPTION.md,
                     which was created for exactly this gap)
REVIEW_ID          = FABLE-QROS-CF-FINAL-DESIGN-001
SEAT               = Fable 5.1 —— design-only review（不审字节,不给实现认证）
TRANSCRIBED_BY     = Claude Opus 5，the repair-builder seat，2026-09-07
SOURCE             = Aaron 的派发消息，2026-09-07
DECISION           = **ONE_BOUNDED_FINAL_REPAIR_IS_JUSTIFIED**
                     **NO FURTHER DESIGN REVIEW REQUIRED**
WHAT_THE_HASH_CERTIFIES = 下面这些设计陈述,如 Aaron 所述;**不是** Fable 报告的原始字节
                     ——那些字节从未作为文件存在于本仓库
EDITS              = 对设计陈述本身零编辑。标注为 BUILDER'S ADDITION 的段落是本席位所加
```

## 0. 为什么存在这份文件

标准的工件传输规则要求:跨会话传递的工件必须以文件形式落盘并记录 SHA256,
**聊天携带的字节永远不是真相来源**。Fable 的这次设计复审只经由 Aaron 的派发
消息到达修复席位,因此**本文件是该设计决定的持久定义,仓库里此前没有别的。**

两条限制,免得后来的读者过度解读:

1. **这不是 Fable 的完整报告。** Aaron 的消息以设计方向的形式陈述了结论与
   约束;Fable 自己的推理、度量与措辞未被传输,此处也不重建。若 Fable 会话中
   存在更长的原件,以那份为准,本件是它的摘要。
2. **这是仅设计复审,不是实现认证。** Fable 没有审过修复后的字节。实现是否
   成立,由后续的**封闭范围机械结案检查**判定,而那不是本件。

## 1. 设计决定

```
ONE_BOUNDED_FINAL_REPAIR_IS_JUSTIFIED
NO FURTHER DESIGN REVIEW REQUIRED
```

自动的「修复 → 广域复审 → 修复 → 广域复审」循环**终止**。本轮之后只做一次
封闭范围的机械结案检查;其 PASS 关闭 QROS-CF 治理窗口,HOLD 则 QROS-CF
**延期/不激活**,之后**没有**自动的下一轮修复。

## 2. Root A —— 受信启动的信任根位置

信任根必须移到**项目受管 Python 语义之外**。目标设计:

```
OS 进程创建
→ 以已固定的加固旗标启动 Python 解释器
→ 父进程执行 launcher 源码,不导入任何项目模块
→ 父进程构造受管子进程
→ 子进程的信任条件建立
→ 受管项目导入只在此之后发生
```

受认可的加固形式在概念上是 `python -I -S -B scripts/run_governed.py ...`;
`-I` 提供 `-E -s -P`。`.cmd` 只是同一形式的固定拼写。
未加旗标的 `python scripts/run_governed.py ...` **不再是受认可的生产启动形式**:
它必须失败关闭,并且**不得**通过 re-exec「自我升级」。

### 2.1 关键的信任根条件

不得引入递归的信任问题。修复必须显式定义并机械保持这条自举信任假设:

```
trusted bootstrap boundary =
    OS 进程创建
  + 在加固旗标下选定的 Python 可执行文件 / 标准库启动
  + 被显式调用的 launcher 源码字节
```

launcher **不得**在该边界建立所需解释器条件之前执行受管的项目导入语义,
也**不得**试图在自己已经运行之后证明自己的可信性。禁止:全机哈希、
Python 可执行文件签名、launcher 签名设施、另一套溯源框架、另一本信任台账。
**信任递归止于上面那条声明的假设。**

## 3. Root B —— F06 起动路径完整性

不变量必须下移到**权威的最低变更层**。期望的公开语义:

```
serialized_append(...)        = 仅通用的**非起动**registry 变更
serialized_start_append(...)  = start-equivalent 变更，必须执行最终的
                                owner-control 起动语义
```

通用公开 API 必须**在结构上无法**提交 start-equivalent 事件字节。

### 3.1 关键的 API 条件

不得用另一个隐藏的旁路参数替换当前的旁路。**不得**出现
`allow_start=True` / `skip_validation=True` / `validate=None` / `unsafe=True`
或任何等效的、调用方可控的开关,使工作流代码得以经通用 API 提交起动语义。
所需性质是**结构性**的,并且在这条区分之下不得存在任何受支持的公开/裸路由。

复用现有的 `registry_boundary`、共享解析器、共享事件规范化、既有 `_AppendLock`
与既有物理写入边界。**不得**新建 registry 或状态权威。

## 4. 起动事件词表

不得发明新的事件语义。复用当前权威的事件解析器/规范化与既有
`START_EQUIVALENT_TOKENS`;保持 plain / padded / 既有受支持格式化拼法的现有处理;
不引入无关的大小写折叠或新 token。

## 5. 封闭范围结案判据（Fable 划定的范围）

结案检查**仅限** `A1–A6`、`B1–B4`、`S`。它**不是**另一次开放式的仓库审计。
范围之外的观察进 BACKLOG,除非它给出当前阶段某条 T1–T6 的直接失败路径、
并因此推翻上述某条固定结案不变量。

## 6. 本件不做的事 —— BUILDER'S ADDITION

本件不接受、不裁定、不关闭任何 finding,也不认证任何实现。
**它只是把一次仅设计复审的决定落盘。** 修复后的字节是否成立,
由后续那一次封闭范围机械结案检查给出 PASS 或 HOLD,而那由 Aaron 派发。
之前所有的 HOLD / 已归还认证记录保持原样,**不得被改写为 PASS**。
