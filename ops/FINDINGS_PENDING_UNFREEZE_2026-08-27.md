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
tests/test_save_dir_configuration.py  <- CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md
                                         【已冻结：dec-s5-r4-2026-08-27】
tests/fakes.py                        <- PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md
                                         【未冻结】
```

**两者都不是缺失文件**：它们是 qros-runtime 仓的路径，写在 ITSF 文档里时省掉了
仓名。**危害与陈旧引用同形，只是轻得多**：读者在本仓解析不到 → 搜索。

**未修，且刻意不做分别处理**：只修未冻结的那一份，会让同一份文档集里两处相同
缺陷用两种写法，比两处都不改更糟。

### 待办（解冻后）

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
