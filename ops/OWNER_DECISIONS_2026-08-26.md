# Aaron 本人裁定 —— 2026-08-26（采纳八项委托裁定）

```
RECORD_TYPE=OWNER_DECISION
DECIDED_BY=Aaron，本人
DELEGATED=NO —— 「采纳」这个动作是 Aaron 自己的；被采纳的八项内容是 Fable
          在他明示委托下作出的（DELEGATED=YES）。引用时两层都要带。
EFFECT=即时生效
TRANSCRIBED_BY=Opus 5 main agent（builder seat）—— 转录，非背书
BASIS=ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md
      SHA256 5116f7b03dabe6cc4a8a2357b02b4b30e3a9227d050e41d9c1f0943262ed7dd3
      （该哈希证明的是本次转录的字节；裁定经聊天送达，非磁盘交付）
```

---

## OD-2026-08-26-1 —— 委托 Fable 裁这八项

Aaron 原话：**「fable将会替我做选择，把这八项都交给fable」**（2026-08-26）。

```
DELEGATION_SCOPE=dec-eight-open-2026-08-26 的全部八项
DELEGATE=Fable 5，fresh top-level session
```

## OD-2026-08-26-2 —— 采纳八项裁定全文

Aaron 原话：**「你审核一下，就让fable推荐的做」**（2026-08-26，读过八项裁定之后）。

```
ADOPTED=ITEM 1..8 全部，逐字如 ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md §一
BUILDER_AUDIT=已做（同件 §二），全部引用 REPRODUCED；一处论证更正见下方 OD-…-4
```

**「采纳」在这里精确地意味着什么** —— 因为八项里**每一项**都自陈
`EXECUTION_UNLOCKED_BY_THIS_RULING=NO`：

- **实质选择**已定，不再重开。八项的 RULING 段即受裁文本。
- **执行**并未因采纳而全部解锁。凡裁定自己点名「欠某项 Aaron 具体动作」的，
  那个动作仍然欠着 —— 采纳裁定 ≠ 执行那个动作。
- **例外是第 4、5 项**：两者所欠的**仅**是「Aaron 决策记录 append」，而记录是
  转录 Aaron 的决定、由 builder 落盘。本记录即是。**故第 4、5 项自本记录起
  完成**，且两者本就是零改动裁定（「无执行动作存在」）。

## OD-2026-08-26-3 —— 逐项结算：什么完成了，什么还欠 Aaron

| # | 题 | 本记录之后的状态 | 还欠 Aaron 的**具体动作** |
|---|---|---|---|
| 1 | 全局 L6 exposure 句限缩 | 受裁：**改写措辞**（非裸限缩） | 对全局 `~/.claude/CLAUDE.md` L6 段的**修订授权**，并 append 改写句的逐字终稿。**过渡形继续**：临时生效，方向 fail-closed |
| 2 | D-2 S1(a) ＋注册表 carve-out | 受裁：**做**，carve-out 取外科形 | (i) path 字段编辑与文件迁移的**执行授权**；(ii) 确认 08-25「Sol 返回前不推进」hold 不覆盖本项。**过渡形继续**：(b)＋S2 |
| 3 | D-4 `_SAVE_DIR` 配置化 | 受裁：**下一个维护窗**，一轮 fresh Sol（High），B 按事件失效 | **开启维护窗**（qros-runtime 仓）。**过渡形继续**：B |
| 4 | actor 是否兼表执行者 | ✅ **完成** —— 是，复合 token，不加字段，双向绑定 | 无。零改动 |
| 5 | A1/F1/F2 的 actor | ✅ **完成** —— 保留，零修订；「观察者存活」为受裁切口 | 无。零改动 |
| 6 | P3 后硬崩溃 | 受裁：新增 CR1 事件＋bootstrap 悬链拒绝＋逐 incident 授权 | ND1 profile **R3 修订的 ratify**（走提案→fresh Sol→Aaron 三步）。**今日不阻塞任何事**：MC 生产路径不存在 |
| 7 | registry 留在 OneDrive 树？ | 受裁：**有边界地允许**，四条边界 | 决策记录（本件即是）；**另**：见证目录若需在 `C:\Users\Aaron\quant-data\` 下新建，须单独的**目录创建授权** |
| 8 | 租约回收自动化 | 受裁：**fail-closed，永远**；自动回收否决 | 无执行动作（租约尚不存在）。约束未来设计 |

**第 6 项特别声明**：`CR1` 是**工作名**，终名与字段归 profile 修订流程。
本记录不构成对 ND1 profile 的修订，也不授权任何人修订它。

## OD-2026-08-26-4 —— 一处经 builder 复核的论证更正（不改任何裁定）

第 7 项的**风险叙述**里有一句不成立：「半写行会死在六格解析上……fail-closed」。

**实测**：`parse_registry_events`（`scripts/s0_real_run.py:183-184`）对格数不符的行
是 **`continue` 而非 raise**，畸形行被静默丢弃；且 `ops/TRIAL_REGISTRY.md`
**被 clean gate 白名单豁免**（`:113`，用于 `:596`），registry 变脏不打红
`git_clean`。**所以截断末行的半写与静默回退可观测状态相同——致命通道是两条。**

**这不改第 7 项的裁定，反而加重其条件 (1)**：反回退见证比对
{sha256, 事件计数, 末行}，丢一行会让计数低于见证，同样被抓。**边界 (1) 是这两条
通道唯一的共同拦截点** —— 将来任何以「解析器会挡住半写」为由削减边界 (1) 的提议，
其前提是假的。

冲突副本那半句成立：`_clean_gate_exempt` 只豁免精确路径，冲突副本是另一个文件名的
未跟踪文件，会打红 `git_clean`。

## OD-2026-08-26-5 —— 仍然只有 Aaron 能做的（Fable 的 `STILL_AARON_ONLY`，加一条）

1. 上表所有「还欠」栏的执行授权。
2. 仓库整体是否迁出主动同步树（第 7 项的彻底形）。
3. 席位台账第 3 行的终分类（`PENDING_AARON`）、第 4 行 `NOT_EXPOSED` 分类值的存废、
   **以及新增的第 5 行**（本轮 Fable 的三次定位操作）。
4. GRAD pilot 排程及其与维护窗的先后（第 3 项条件 4 的两分支择一）。
5. **（builder 追加）** D-3 本身的去向：八项裁定**不解锁 D-3**。按 Fable 的
   `CROSS_ITEM_CONFLICTS`，重启 MC 需要按第 4/5/6/7/8 项**重写 D-3 提案并重走
   三步全程**。是否重启、何时重启，未裁。

## OD-2026-08-26-6 —— 未被采纳所改变的东西（免得日后误读）

- **D-3 的 HOLD 仍在**：条件 3 继续在 force —— fresh Sol PASS ＋ Aaron 授权之前，
  生产代码不得获得任何 registry 写能力。
- **N09 的 P2 仍不签**（OD-2026-08-25-1 未被本次触及）。
- **三条独立授权仍不得合并**（ND1）：目录创建 / 写探针 / 执行。第 7 项的见证目录
  正是「目录创建」那一条。
- `A2→B` 与 `I→J` 的 HOLD 未变；本轮不涉及任何 gate 释放。
