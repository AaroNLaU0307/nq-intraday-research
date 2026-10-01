＃ R4 批准记录 —— CR1 语法块的仓锚定

```ini
RECORD_TYPE=APPROVAL（生效）
APPROVED_BY=Aaron，本人，逐字回贴 builder 呈块（形制乙，OD-4）
APPROVED_AT=2026-08-31
ROUTE=§D.10.3（id ＋ sha256 ＋ 精确 doc HEAD），未加新门类
```

## 1. 批准文本，逐字

> 批准 R4 —— CR1 语法块的仓锚定修订。
>
> ```
> R4_AMENDMENT_ID=ND1_CR1_GRAMMAR_R4
> R4_CANONICAL_SHA256=6e62fd2dc349468fd3bd1fdd8c5f2ef20b5b4cfade215eba07609107ca0f5233
> R4_PROPOSAL_DOC=ops/R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md
> R4_PROPOSAL_DOC_SHA256=10190d54f595485c45afc6837e64edb228fdb50444834e5b0000e294ce42c672
> EXACT_DOC_HEAD=4dd34e85d97e3c754333407e6c568980f6040678
>
> VOIDS=c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483
> VOIDING_REASON=所指重绑定，判据未变。
> ```
>
> 本批准解除「R4 ratify 之前禁止追加任何 CR1 行」的冻结令。
>
> 本批准不授权：MC 执行、supplement 执行、策略 build、真实数据读取、
> 目录创建、写探针、registry／exposure 事件追加、归档重试。
> 每一次执行仍需我单独的、绑定完整 40 位 commit 的精确授权语句。

## 2. 记录前的复测 —— 批准绑的是字节，不是我的记忆

```
R4_CANONICAL_SHA256 复算            == 6e62fd2d…      ✅
提案文件 sha256                      == 10190d54…      ✅
EXACT_DOC_HEAD 处的字节 == 盘上字节                    ✅
被作废的 c251335f… 仍可由同一口径复算出来               ✅
```

**最后一条是刻意测的**：若那个口径已经算不出被作废的哈希，
说明这里用的哈希方法不是当初批准时那个，**「作废旧值、换上新值」这件事本身就无从成立**。

## 3. 生效内容

```
ND1_CR1_GRAMMAR_R4  生效     canonical sha256 = 6e62fd2d…（18 行）
ND1_CR1_GRAMMAR_R3  作废     c251335f…
作废理由            所指重绑定，判据未变
```

**「判据未变」是机械可验的，不是形容词**：
`tests/test_a_proposal_states_the_hash_of_its_own_block.py` 逐行比对 R3 与 R4，
15/17 行逐字保留，改动恰为 `PREIMAGE` 与 `COLD_RECOMPUTE`，新增恰为 `ANCHOR`。
一个 fresh Sol 席位独立确认：`REVISION_WEAKENS_ORIGINAL=NO`，
`CRITERION=EXACTLY_UNCHANGED`，`UNRESOLVED_TOCTOU=EXACTLY_UNCHANGED`。

## 4. 绑定如何更新 —— **不改任何已批准／已返回的历史记录**

```
承载旧值的记录   ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md 的 CR1_GRAMMAR_SHA256
                 ops/DECISION_PACKET_ITEM6_OPEN_FABLE.md 的 RECOMMENDED_CR1_GRAMMAR_SHA256
处置             **两份都不动**。它们是历史记录，记的是当时为真的事。
                 就地改一个已批准的哈希，等于让记录说它当时说的不是它说的话。
新绑定的权威     **本文件**。R4 生效之后，CR1 语法的 canonical 值是 6e62fd2d…
```

## 5. 冻结令 —— 已解除，且**解除不等于追加**

```
冻结令           「R4 ratify 之前禁止追加任何 CR1 行」-> 已解除
解除后的实测      registry 里 CR1 行数 = 0
```

**解冻只是把「明令不得」降回「本就不会」**：
八项授权仍全为 NO，真实运行仍被边界前置封锁，CR1 本就无法合法触发。

## 6. 批准之后**仍然不被授权**的（逐字来自 D.10.4，非 builder 添加）

```
MC 执行 · supplement 执行 · 策略 build · 真实数据读取 ·
目录创建 · 写探针 · registry／exposure 事件追加 · 归档重试
```

**每一次执行仍需 Aaron 单独的、绑定完整 40 位 commit 的精确授权语句。**

## 7. 仍然未关闭的残留，明写

```
仓被移动    若 registry 仓移动而墓碑未更新，冷读者无法发现它。
            R4 不关闭这条，只把「移动 registry 仓」定为
            必须同时更新墓碑的受治理动作
TOCTOU      读与追加之间的临界区仍未关闭，仍无 lease。R4 逐字未动它
S8 备份     异卷备份仍未满足 —— 本机只有 C:
```
