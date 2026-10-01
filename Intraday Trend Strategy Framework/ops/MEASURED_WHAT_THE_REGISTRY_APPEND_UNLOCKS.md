# registry 追加授权解开什么 —— 实测，不是推断

```ini
RECORD_TYPE=MEASUREMENT（不授权，不追加任何行）
BY=Opus 5，builder seat，2026-08-29
BASIS=A1 的教训：上一份授权我说它「解开一道门」，实测是零。这次先量。
METHOD=合成 registry 干跑，真实登记簿一个字节未动
HEAD=0c580ede6eb3cb82732cedcc26e35285a601ee11
```

## 1. 结果

十三道 A_PRECHECK 门在三种登记簿状态下的判定：

| 门 | 空（今天） | ＋P1 | ＋P1＋正确 P2 |
|---|---|---|---|
| g9_hard_blocker | PASS | PASS | PASS |
| second_copy_attested | PASS | PASS | PASS |
| frozen_hashes | PASS | PASS | PASS |
| git_clean | PASS | PASS | PASS |
| supplement_id_pattern | PASS | PASS | PASS |
| registry_chain_resolvable | PASS | PASS | PASS |
| **live_authorization_unique** | REFUSE | **REFUSE** | **PASS** |
| **authorization_actor** | REFUSE | **REFUSE** | **PASS** |
| **authorized_commit_matches_head** | REFUSE | **REFUSE** | **PASS** |
| **output_root_declared** | REFUSE | **REFUSE** | **PASS** |
| **output_root_structure** | REFUSE | **REFUSE** | **PASS** |
| supplement_subtree_absent | PASS | PASS | PASS |
| id_not_retired | PASS | PASS | PASS |

**追加 P1 改变的门数：0。** 五道门的翻转**全部**来自 P2 —— 那是 Aaron 的行。

这与 A1 是同一个形状，所以这次先量了再说。

## 2. 但 P1 不是没用 —— 它是**结构必需**，且已证

没有 P1，P2 在链上非法：

```
chain_does_not_start_at_proposal [MC-DS-S001, row #1]:
a chain starts at a proposal row (P1 or the T1 successor registration), not P2
```

P1→P2：链干净，`live_authorizations = 1`。
**所以 P1 的理由不是「解开门」，是「P2 没有它挂不上」。**

## 3. P1 不随提交作废，P2 会 —— 这条决定了「现在给还是等」

```
P1 必填字段  supplement_id · ir_basis · schema · non_authorization_disclaimer
             ^^ 没有 commit
P2 必填字段  supplement_id · authorized_commit_40hex · output_root ·
             verbatim_authorization_sentence
```

实测：P1 写在旧 commit、P2 写在新 commit —— 链**无 problem**，
`authorized_commit` 取的是 P2 那个。

**P1 放在那里不会腐烂。** 所以「等」的成本是零。

## 4. 就算 P1＋P2 都齐了，也还跑不动

```
A_PRECHECK   13/13 PASS
B_DERIVE      5/5 REFUSE   —— no supplement authority supplied
                              （要真实 Development 输入，在 assert_real_run_allowed 后面）
C_BUILD       5/5 REFUSE   —— "unreachable in this build"
                              （门还是桩；接线补丁已写好但**停放**，见
                               ops/PREPARED_C_BUILD_1_GATE_WIRING.md）
生产入口                     SupplementRunNotAuthorized（真实登记簿 0 条存活 P2）
```

## 5. builder 建议：**现在别给，等 fresh Sol 复审接线之后**

四条理由，每条都可复算：

1. **今天它解开零道门**（§1）。
2. **它不会腐烂**（§3），所以等的成本是零。
3. **裁定自己记的顺序就是这个** —— `OWNER_DECISIONS_2026-08-29.md` §3：
   ```
   builder 越过骨架，把 C_BUILD 五道门建成真的分类器
   fresh Sol  复审（D-3 条件 3 要求）
   Aaron   registry 追加授权 -> P1 -> P2 -> 真跑
   ```
   我没有任何实测证据支持偏离这个顺序。
4. **登记簿只追加、永久。** P1 携带 `schema: mc_day_strata_supplement.v1`。
   若接线复审改动了 schema，那行就成了陈述过时事实的永久行，
   撤销要走 F3＋T1 换代。**在它买不到任何东西的时候写下永久行，是纯粹的下行风险。**

**唯一会改变这个建议的事**：接线补丁落地并过 fresh Sol。那时 P1 才买到东西
（它让 P2 可以挂上，而 P2 让 A_PRECHECK 全开），且陈旧风险已被复审吃掉。

## 6. 到时候你要说的那句话（**现在不要说**）

形式跟着 P1 的必填字段走，不是我发明的：

> 授权主代理在 `ops/TRIAL_REGISTRY.md` 追加一行 `SUPPLEMENT_PROPOSED`（P1），
> supplement_id 为 `MC-DS-S001`，schema 为 `mc_day_strata_supplement.v1`，
> 且该行不构成执行授权。

再往后是 P2，那一句另有形制（含 §13.5 逐字句子头
`START_MC_DS_S001_DAY_STRATA_SUPPLEMENT_EXECUTION`），到时另备。

## 7. 复算方式

本件每个数字都由合成 registry 干跑得出，脚本形态见
`tests/test_what_the_registry_append_unlocks.py`（与本件同批提交），
真实 `ops/TRIAL_REGISTRY.md` 全程未被读写以外的方式触碰。
