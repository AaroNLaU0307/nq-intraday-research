# 等解冻才能落地的小发现

```ini
REVIEW_ID=findings-pending-unfreeze-2026-08-27
DELIVERY_STATUS=RETURNED
```

**为什么单独一份文件**：这几条本应写进
`ops/FINDINGS_DANGLING_CITATIONS_2026-08-27.md` 或
`tests/test_cited_records_exist.py`，但那两份已随 `dec-citations-2026-08-27`
登记冻结，`ops/CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md` 已随
`dec-s5-r4-2026-08-27` 冻结。**冻结正在正常工作，代价就是这条得等。**
不写进聊天记录 —— 本项目 2026-08-26 刚为「只存在于聊天里的裁定」付过一次代价。

---

## F-1 · 跨仓 `.py` 引用没有仓限定符（2 处）

实测：`ops/*.md` 里 49 处 `tests|src|scripts/*.py` 引用，2 处在本仓不可解析。

```
<tests>/test_save_dir_configuration.py  <- CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md
<tests>/fakes.py                        <- PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md
```

**上面两行的 `<tests>` 是刻意写坏的**：本文件是这个问题的**记录**，
若按原样写出路径，守卫会把这份记录本身算作两条活的悬空引用 ——
记录一个缺陷不应当再制造一份同样的缺陷。

**两者都不是缺失文件**：它们是 qros-runtime 仓的路径，写在 ITSF 文档里时省掉了
仓名。**危害与陈旧引用同形，只是轻得多**：读者在本仓解析不到 → 搜索。

**~~未修，且刻意不做分别处理~~** —— 该判断建立在「两处都是真缺陷」之上，
而实测只有一处是（见下）。原文保留，因为它是当时的如实状态。

### 已完成，2026-08-28

```
1. 仓限定符   CORRECTION 那处**本来就带着** qros-runtime/ —— 原先判它悬空是
              builder 的探测器误报：正则匹配了 `qros-runtime/tests/...` 的中段。
              PREP_ITEM3 那处是真的缺，已补。
2. 守卫扩展   tests/test_cited_records_exist.py 增加 .py 引用扫描，
              正则前置零宽断言，不再匹配路径中段。
3. 分类形状   跨仓引用不走 dec-citations 的 MARK_ONLY —— 那条裁的是隔离件，
              而跨仓引用的正确形式就是补上仓名，不需要新分类。
```

**一条值得记的**：第 1 条里那个「悬空引用」有一半是我的探测器造出来的。
**在把一份记录判成缺陷之前，先确认探测器没有在制造它。**

### 原待办（解冻后）

```
1. 两处补上仓限定符（如 `qros-runtime/tests/test_save_dir_configuration.py`）。
2. tests/test_cited_records_exist.py 增加对 tests|src|scripts/*.py 引用的扫描，
   并为跨仓引用定一个可证伪的分类（候选：CROSS_REPO_QUALIFIED —— 判据是
   路径以某个已知姊妹仓名开头）。
3. 若 dec-citations 的裁定给出了 §3 的分类判据，2 应与之保持同一形状。
```

---

## 记录纪律

**本文件本身不得被用作绕过冻结的通道。** 它只记录「发现了什么、为什么现在不能
落地」，不含任何对已冻结文件的替代实现。上面每一条待办都要在原文件解冻后回到
原文件里去做，而不是留在这里长成第二份真相。
