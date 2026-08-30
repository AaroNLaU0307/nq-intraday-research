＃ R4 v2 —— **单问复审**：收窄主张算不算在 R4 内自行扩权

```ini
REVIEW_ID=r4-v2-fork
DELIVERY_STATUS=RETURNED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（单一问题裁断）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；ops/RULING_FABLE_S5_AND_R4_2026-08-27 的决裁席（Fable 5）；
            **review r4-cr1-anchoring 的那个会话**（它给了 v1 的 HOLD）；
            迁移方案 Route A 的前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
SCOPE=NARROW —— 见 §1，并读 §1 末尾那段
```

**READ THIS PROMPT FROM DISK, not from a paste.**
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_R4_V2_FORK_SOL.md`

框架仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
registry 仓根：`C:\Users\Aaron\quant-data\itsf-registry`（**本轮许可读**）

禁区清单随包交付：`ops/OFF_LIMITS_COMPANION_R4V2.md`，请一并读。

**权威登记册**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
点名它是为了让你**有东西可以对照** —— 只拿到交付件却无从核对任何路径，
本身就是 D-2 那次烧掉席位的形状。随包件点名不算：席位可能只拿到这一份。

---

## 1. 只问一个问题 —— 但这不是封口

**唯一要你裁的：**

> 上一席位判 v1 的锚点主张**触发了证伪器**（须回决裁层重裁）。
> v2 的回应不是解决那个问题，而是**收窄主张**：
> 承认「路径做发现、commit 对做验证」，并把「仓被移动即找不到」
> 写成明白的、未关闭的残留。
>
> **这样的收窄，算不算「在 R4 内自行扩权」？**

```
甲  不算 —— 桥仍只引用 S4，没有引入任何新钉法，只是把主张缩到事实内
乙  算   —— v2 作废，桥回决裁层
```

**builder 倾向甲，并明说甲对 builder 有利**（不必回决裁层）。
builder 上一次自己判「澄清 vs 新判据」判偏了，偏向也对自己有利，
**所以这一次不自己判**。

### 范围窄是预算决定，**不是封口**

Aaron 2026-08-31（OD-6）裁定只问这一条，理由是 v1 四条阻断里的**另外三条
现在都由常驻守卫机械核对**（见 §3）。

**但如果你在别处看到东西，照说。** 一份「只问一个问题」的包若被用来
把审查席引开，那它就是在做本项目反复要避免的事。
`OUT_OF_SCOPE_FINDINGS` 字段就是留给这个的。

---

## 2. 回答这个问题需要的最小事实

**v1 为什么被判触发**（上一席位实测，builder 已复现）：

```
框架仓 object DB 里查 N1   ->  不存在
registry 仓里查 N1         ->  存在
```

`commit hash` 只能在**已经被定位的** object database 里确认身份，
**它不能发现仓在哪**。v1 却写了一句加粗的
「A FILESYSTEM PATH IS NOT THE ANCHOR」——**否掉了真正承重的那一半**。

**v2 改成什么**（逐字在 `ops/R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md` §1 的块里）：

```
DISCOVERY     墓碑所述位置是找到它的**唯一**手段；机器局部；
              仓被移动而墓碑未更新 => 冷读者找不到。
              **本语法不关闭这条**，并把「移动 registry 仓」定为
              必须同时更新墓碑的受治理动作
VERIFICATION  找到之后，由 S4 交叉互钉确认是不是那个仓
```

**裁定原文的证伪器**（`ops/RULING_FABLE_S5_AND_R4_2026-08-27`，在受审集内）：

> 若 R4 起草时发现 S4 交叉互钉不足以让冷读者单凭字节完成跨仓解析
> （**即桥必须引入 S4 之外的新钉法**），本裁定「桥引用 S4 即可」的前提即被证伪，
> 桥的设计须回到决裁层重裁而非在 R4 内自行扩权。

**问题的实质**：括号里那句把触发条件绑在「**必须引入新钉法**」上。
v2 没有引入任何钉法，它把主张缩小了。**这算不算触发？**

---

## 3. 另外三条阻断：**已机械化，请核对而不是重推**

```
核验  python -m pytest tests/test_a_proposal_states_the_hash_of_its_own_block.py -q
预期  9 passed
```

该文件的检查顺序是刻意的：

```
一  先证明口径复算得出**已批准的** c251335f…
    —— 不成立则此处用的哈希方法不是批准时那个，其余数字全错
二  提案声称的 R4_CANONICAL_SHA256 == 它自己携带的块的哈希
三  「未改字段」**逐行比对 R3**（v1 死在复述上：手抄漏了 8 个字段）
```

变异证红：块里改一个字段值 -> 三条同时红。

```
核验  python -m pytest tests/test_registry_path_single_construction.py -q
预期  7 passed
核验  python -m pytest tests/test_registry_absence_refuses.py -q
预期  11 passed
```

**分界（strictly after N1）是可实测的**，请自行确认而非采信：

```
N1 的父提交里取 ops/TRIAL_REGISTRY.md   ->  不存在（N1 才首次加入）
迁移当时 registry 里的 CR1 行数          ->  0（N1 搬文件，不写行）
```

---

## 4. 受审集

```
REVIEWED_SET_UNCHANGED_SINCE=2a783111f8780762fa6c34b6b8bd7b8953e7e6b7
```

| sha256 | bytes | 路径 |
|---|---|---|
| `10190d54f595485c45afc6837e64edb228fdb50444834e5b0000e294ce42c672` | 8499 | `ops/R4_PROPOSAL_V2_CR1_REPOSITORY_ANCHORING_2026-08-31.md` |
| `5a30398b8d6dbd35bc702362e458d6c10c135d3c692082d1c71819136db400c5` | 15702 | `ops/RULING_FABLE_S5_AND_R4_2026-08-27.md` |
| `7ea86474ce886dffa80d9540037e93f657e1603bcda20d26aa6512a10553cfa7` | 6332 | `ops/RULING_SOL_R4_HOLD_2026-08-31.md` |
| `9f1269f1c8e8e88767d14d87ed36169240729e806d253bfd01b1e13dab4e2cec` | 8866 | `ops/R4_PROPOSAL_CR1_REPOSITORY_ANCHORING_2026-08-31.md` |
| `fdb18eb71273a4eb8a08adbda885f5f66531292bb8c1be2a4aa4f35063a747e1` | 3690 | `ops/MIGRATION_ROUTE_A_COMPLETED_2026-08-31.md` |
| `eb8b6567d99760ee7438e8105e08f48a0584e0798175a9a236a6be5bf73b96b0` | 37109 | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md` |
| `bf96a2861f64d0b5251696f01dd130d983e57cd4da815ade6ed4cef6ff25a0ae` | 2608 | `ops/TRIAL_REGISTRY.md` |
| `d8e4342c5f4408def1f0abd0f96a99d6a84fc6c148ea09e0a13e6df0a55153f5` | 5444 | `scripts/r4v2_block_builder.py` |
| `516290cc4a5f3a544fe0ebb3cc4f0fc4776386cfa07abb854f246f0d9e865d7c` | 5795 | `tests/test_a_proposal_states_the_hash_of_its_own_block.py` |
| `f1820fdeed2b991177bcc31762ae94ab3c7fc6dbcacc11ef9d81ca3e2dd78f08` | 11504 | `tests/test_registry_path_single_construction.py` |
| `a54eea0d2bf03d46a19959ed4d041e1671f70b162727609e7274de84dc5a6057` | 7665 | `tests/test_registry_absence_refuses.py` |
| `591979df11d766748362bf62663ffebf3a4285a53205b61784492195274a4112` | 2489 | `ops/OFF_LIMITS_COMPANION_R4V2.md` |

**delivery**：`ops/PROMPT_R4_V2_FORK_SOL.md`，字节见 `ops/ARTIFACTS_UNDER_REVIEW.json`。

**`ops/TRIAL_REGISTRY.md` 在集内的是墓碑，不是 registry** —— 它是桥的第一跳。
真 registry 在另一个仓。

**v1 也在集内**（`R4_PROPOSAL_CR1_...`，无 V2 字样），因为你要判的是
「v1 → v2 的这次收窄」，两份都得看得见。

**核对你读的是当前文件**：line 137 of it must read
`REVIEWED_SET_UNCHANGED_SINCE` 那一行。对不上 ⇒ **STOP**，回磁盘重读。

---

## 5. 交付要求

```
FORK_RULING=                  甲|乙 —— 收窄主张算不算在 R4 内自行扩权
REASONING=                    一段就够，但要能被 Aaron 直接读懂
MECHANISED_THREE_CONFIRMED=   YES|NO —— §3 三条核验跑过了吗？数字对得上吗？
BOUNDARY_INDEPENDENTLY_TESTED= YES|NO —— strictly after N1，你自己测了吗？
OUT_OF_SCOPE_FINDINGS=        范围外看到的东西，照说
SEAT_STATUS= / FORBIDDEN_PATHS_OPENED= / SOURCE_WRITES= / PERSISTED_SEARCH_OUTPUT=
REGISTRY_REPO_READ=           YES|NO
```

**判「乙」是完全可以的结果。** v2 作废、桥回决裁层，
比一个没人独立判过的、对 builder 有利的读法被默认采纳要好。
