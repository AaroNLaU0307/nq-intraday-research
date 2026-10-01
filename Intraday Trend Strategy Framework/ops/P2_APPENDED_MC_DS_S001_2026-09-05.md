＃ P2 已追加 —— `MC-DS-S001` 的 `SUPPLEMENT_EXECUTION_AUTHORIZED` 行（第二次）

```ini
RECORD_TYPE=EXECUTION_EVIDENCE
AUTHORIZED_BY=Aaron，2026-09-05，逐字签署块（supplement_id / authorized_commit /
              output_root / actor 四项逐字给定；除 UTC 字段外不得改动）
EXECUTED_BY=Opus 5，builder seat
REGISTRY_COMMIT=a875740（registry 仓）
WITNESS=WITNESS_P2_APPENDED_2026-09-05.json（**补记，见 §3**）
```

---

## 1. 追加了什么

```
序号        15
时间戳      2026-09-05T09:43:26+00:00（签署/追加当时的真实 UTC）
commit      301de7bd8b2c7bdf02964e39a9729c39b4a5c691
actor       Aaron
note        [MC-DS-S001] START_MC_DS_S001_DAY_STRATA_SUPPLEMENT_EXECUTION
            supplement_id: MC-DS-S001;
            authorized_commit: 301de7bd8b2c7bdf02964e39a9729c39b4a5c691;
            output_root: C:\Users\Aaron\quant-data\itsf-runs
sha256      3ddbfb62… -> 27b4983f…
见证        WITNESS_P2_APPENDED_2026-09-05.json  sha256 7d4885b7…
```

**序号 15 是第二次被用。** 2026-08-31 的 P2（commit `89b514a3`）用过同一序号，
已无痕撤回，见 [`P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md`](P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md)。

事件数与字节数与那份见证**完全相同**（19 / 7273）——行形状一样、序号一样，
**只有 sha256 不同**。一个只比数量的检查在这里完全看不出差异。

## 2. 它解开了什么：13 道门里的 12 道

实测于 2026-09-05 晚，HEAD `5e7436c3`（不是引用之前的结论）：

```
g9_hard_blocker                  pass
second_copy_attested             pass
frozen_hashes                    pass
git_clean                        pass
supplement_id_pattern            pass
registry_chain_resolvable        pass
live_authorization_unique        pass   <- P2 翻的就是这一道
authorization_actor              pass
authorized_commit_matches_head   REFUSE
output_root_declared             pass
output_root_structure            pass
supplement_subtree_absent        pass
id_not_retired                   pass
```

就剩一道，而那一道拒的原因见 §4。

## 3. 我欠的：见证是补记的

`ops/REGISTRY_SYNC_FAILURE_MODEL.md` (1) 要求**每次追加后**写见证，
而 [`P1_APPENDED_MC_DS_S001_2026-08-31.md`](P1_APPENDED_MC_DS_S001_2026-08-31.md) 里已经写着
「见证不是可选的」。**我追加完没写。**

补记的见证**只能建立「从现在起」的防回滚基线**，不能证明追加当时的状态；
追加与补记之间的窗口只由 registry 仓自己的 commit `a875740` 覆盖。
这个局限已逐字写在见证的 `note` 里，而不是只写在这里。

见证根是 append-only，所以被撤回的那份 `WITNESS_P2_APPENDED_2026-08-31.json` 保留；
新见证的 `previous_witness` 按名字链到它，并逐字说明：本次追加实际是从
`3ddbfb62`（P1 状态）开始的，不是从 `e212ecf3` 开始的，跨这一链路做超集检查
会正确地报 `REGISTRY_ROLLBACK`，而原因就是那次已记录的撤回。

## 4. 这条 P2 现在不可行使

HEAD 已从 `301de7bd` 移到 `5e7436c3`（N09 prepare 修复），
所以 `authorized_commit_matches_head` 拒。

**这正是 P1 那份记录 §5 预先点名的顺序陷阱**：「P2 之后、真跑之前不得有任何提交」。
写下了，然后又踩了一次。

实测的重授权约束（不是推测）：

```
live_authorizations                = 1  (P2 #15 @ 301de7bd)
_g_live_authorization_unique       >1 拒绝（"at most one is legal"）
                                   所以直接再签一条会把链卡得更死
批准的重授权边                     P2 -> F1 -> P2S -> P2
                                   plan_next_short_id("F1", outcome="retry",
                                                      commit_changed=True) -> "P2S"
("F1","P2")                        在 FORBIDDEN_EDGES 里
                                   「changing commit without going through P2S」
另一条路                           P2 -> F3 -> T1 -> P2（退休 MC-DS-S001，换新 id）
registry_boundary                  **没有写入面**，所以每一条都是人工追加
```

**Aaron 2026-09-05 裁定：先冻结代码，之后再一次性处理旧 P2 的合法关闭/重授权并签最终 P2。**
**本文件不处理它，也没有动登记册。**
