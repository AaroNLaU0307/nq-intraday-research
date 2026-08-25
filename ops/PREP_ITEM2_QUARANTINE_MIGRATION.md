# 第 2 项交付物 —— 隔离子树迁移的可行性实测与计划

```
RECORD_TYPE=PREPARED_ARTIFACT
ITEM=2（dec-eight-open-2026-08-26）：D-2 的 S1(a) ＋注册表 carve-out
STATUS=可行性已实测，计划已写，**未执行**
RULED=Fable 5，2026-08-26，`DELEGATED=YES`（做 S1(a)，carve-out 取外科形）；
      Aaron 已采纳（OD-2026-08-26-2）
NEEDS=(i) Aaron 的 carve-out 文本 ＋ 迁移执行授权
      (ii) 确认 08-25「Sol 返回前不推进」hold 不覆盖本项（D-2 条件 5：含糊取限制性读法）
OUTCOME_CLEAN=是
```

> **为什么先量再动。** Fable 的反向条款写死了：「若哈希保持迁移无法**不削弱任何
> 守卫**地实现 ⇒ 回落 (b)+S2 单独成立，**绝不以削弱守卫为代价**」。所以准备阶段
> 的第一件事是测可行性，不是写脚本。

---

## 1. 实测：12 条隔离路径被谁按路径引用

全仓 `git ls-files` 扫描（`.py/.json/.yaml/.md/...`），按引用者分类：

```
代码/配置引用总计            44
  其中注册表自身的自指        12   ← 正是 carve-out 的标的，必然要改
  其余                       32
生产代码（src/ 非测试）的路径引用   0
```

**「0」这一条最重要，且与索引 §10 的旧说法不同。** 唯一命中 `src/` 的是
`src/itsf/mc/supplement_runner.py:24`，而那一行**在模块 docstring 里**（散文
「…or `EXPOSURE_LEDGER.md`.」），不是路径引用。

所以那 32 条分布是：**测试文件 ＋ `qros-state.yaml` ＋ `ops/*.json` ＋ 文档**。

### 逐条（code / docs）

| 路径 | code | docs |
|---|---|---|
| `EXPOSURE_LEDGER.md`（**仓根**） | 13 | 37 |
| `ops/EXPOSURE_LEDGER.md` | 13 | 37 |
| `ops/MC_TO_STRATEGY_MASTER_PLAN.md` | 4 | 17 |
| `ops/MC_FACTORY_BOUNDARY_STAGE_I.md` | 2 | 3 |
| `ops/ND2_ND3_FABLE_DECISION_PROMPT.md` | 2 | 4 |
| `ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md` | 2 | 10 |
| `ops/S0_T001_RESULT_DECISION_ADDENDUM.md` | 2 | 8 |
| `ops/S0_T001_RESULT_REVEAL_ATTESTATION.md` | 2 | 5 |
| `ops/DECISION_PACKET_ND2_ND3.md` · `ops/MC_DR5_BUILD_PACKET.md` · `ops/ND2_ND3_RULING_REVIEW_FINDINGS.md` · `ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md` | 各 1（仅注册表自指） | 6 / 5 / 6 / 6 |

## 2. **一个裁定没有区分、但必须区分的例外**

**`EXPOSURE_LEDGER.md` 在仓根，不在 `ops/` 下。**

裁定说「将 `carries_outcome` **全部路径**迁入单一显名隔离子树（如
`ops/outcome_quarantine/`）」。照字面执行，会把**仓根的权威历史台账搬进
`ops/` 里**——那不是换个路径，是改变「仓根台账」这个身份本身。而且：

- `tests/test_exposure_ledger_migration.py` 强制仓根件与 `ops/` 承载件**逐行
  恒等**。那条测试存在的前提就是「仓根那份是权威、ops 那份是承载」。
- `qros-state.yaml:285` 把 `ops/EXPOSURE_LEDGER.md` 声明为运行时的
  `exposure_record` 输入路径（可随迁改写，属 DECLARED 分区）。

**builder 不替任何人裁这一条。** 三种读法都成立：

- **(A)** 只迁 `ops/` 下的 11 条，仓根件原地不动、另作标记；
- **(B)** 两份都迁，并同步改写恒等测试的两端路径（测试语义不变、仅端点改名）；
- **(C)** 仓根件根本不该在隔离名单上（它是权威历史台账，本就不供任何席位读）
  —— 这一条会改变名单本身，**远超第 2 项范围**。

**这是需要 Aaron（或 Fable 补裁）回答的第一个问题。**

## 3. 迁移计划（Aaron 授权后执行）

**前置**：先答 §2 的三选一。以下按 **(A)** 写，改选 (B) 只是多两条路径。

1. **单 commit**，`git mv` 逐文件——`git mv` 保证内容字节不变，迁移前后逐文件
   SHA-256 比对入证据（Fable 条件 2）。
2. `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `path` 字段随迁。**条目数不减、
   每条以新路径持同一注册身份存续**——新增守卫断言之（Fable 条件 1）。
3. 32 条非自指引用逐条改写：**测试 ＋ `qros-state.yaml` ＋ 文档**。生产代码零改动。
4. 守卫改指单前缀 `ops/outcome_quarantine/**`，并**对漏迁残留证红**
   （变异测试，沿 `tests/test_delivery_names_no_quarantined_path.py` 先例）。
5. `ops/RECOVERY_ANCHOR.md` **追加**一行前缀规则：该前缀下一切路径关闭；
   **注册表仍是权威，前缀是便利不是替代**（Fable 条件 4）。
6. `ops/MC_TO_STRATEGY_MASTER_PLAN.md` **只准 append 横幅**，既有字节不动。
7. 全套件必须绿，且**不得靠放宽任何断言换绿**。

## 4. 它买到什么、不买到什么（Fable 原话，必须随迁移一起记住）

**买到**：导航安全，以及**一条可机械排除的单前缀**替代必须保持同步的 12 路径清单。

**不买到**：**它不使仓内裸检索变安全**——子树仍在树内。所以
`BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY` **永久在 force，不是过渡措施**。
第 5 条条件就是把这句话写死进恢复锚，防止日后有人以「已经归拢了」为由放松检索禁令。

## 5. FALSIFIER（继承 Fable，加一条）

- 迁移落地后再发生一次**经导航／列目录**的席位暴露 ⇒ S1(a) 未达目的，
  按 D-2 既定终点升级零 checkout 复审。
- 反向：若哈希保持迁移无法在不削弱任何守卫的前提下实现 ⇒ 回落 (b)+S2 单独成立。
- **（builder 追加）** 若 §3 第 3 步的引用改写导致任何**既有**测试变红，
  说明存在依赖旧路径字面量的断言——**那是要报告的发现，不得靠改断言消音**。

## 6. 待 Aaron 的两件（外加 §2 的三选一）

1. **carve-out 文本**：path 编辑＝追踪迁移，条目永不因此离开注册表；经编辑删除
   条目仍不可能。
2. **hold 范围确认**：08-25「Sol 返回前不推进」是否覆盖本项。Sol 已返回，
   但 D-2 条件 5 要求**含糊取限制性读法**，所以由你确认，我不自行判定失效。
3. **§2 的仓根台账三选一**（A / B / C）。
