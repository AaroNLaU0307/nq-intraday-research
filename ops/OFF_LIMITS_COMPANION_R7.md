＃ 禁区清单 · 第 7 轮随包件

```ini
REVIEW_ID=c-build-2-wording-r7
COMPANION_OF=ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND7.md
```

**为什么单独一份**：Review Packet 不得携带禁区清单本身（D-2），
但清单必须随包travel。两份一起读。

## 永不打开

```
ops/outcome_quarantine/**              整个子树，不得打开、不得搜索、不得列目录
ops/EXPOSURE_LEDGER.md                 研究轴台账
EXPOSURE_LEDGER.md                     仓根那一份
ops/OUTCOME_CARRYING_ARTIFACTS.json    其 carries_outcome 下列出的全部路径
```

逐条点名只为**标记禁区**，不是引导你去读。

## 禁止的检索动作

```
仓根范围的 grep / rglob / find
ops/ 全目录枚举
```

## 允许的检索根

```
src/
tests/
提示词 §2 表中逐条列名的 ops 文件
```

## 席位

```
SEAT_STATUS 必须报 BLIND
FORBIDDEN_PATHS_OPENED 必须报 NONE，若非 NONE 则逐条列出并立即停
SOURCE_WRITES 必须报 NONE —— 本轮为只读复审，不修任何源码或测试
PERSISTED_SEARCH_OUTPUT 必须报 NONE
```

进程内变异（在内存里改、跑、不落盘）不算 `SOURCE_WRITES`，
第 6 轮即如此进行，是被鼓励的做法。
