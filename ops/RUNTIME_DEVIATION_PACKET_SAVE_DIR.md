# 运行时偏离：packet 不存 `<repo>/runs/packets`

```
RECORD_TYPE=RUNTIME_CONFORMANCE_DEVIATION
DATE=2026-08-26
DEVIATES_FROM=qros-runtime `packet._SAVE_DIR = "runs/packets"`（硬编码，不可配置）
DEVIATION=packet 存于 `ops/packets/`
STATUS=已生效并入账（PACKET_ISSUANCE correction `pr-rv3651f9fe0b68-002`）
```

## 1. 冲突

**运行时侧**：`qros packet` 输出 `REQUIRED SAVE PATH: runs/packets/<review_id>.packet`。
`_SAVE_DIR` 是 `qros_runtime/packet.py:64` 的硬编码常量，**没有配置项**。

**项目侧**：`<repo>/runs` **不得存在**。这不是偏好：

- 它编码的是 L-5 历史缺陷——`RUNS_ROOT = REPO / "runs"` 曾把运行输出写进被
  OneDrive 同步的仓库树，而 M6.1.7 的 exact-set 磁盘不变量会把任何同步残渣
  （`desktop.ini`／`*.tmp`）判成封存拒绝、烧掉一次 trial。
- 约十处断言依赖它，含 `tests/conftest.py` 的 **suite-wide autouse fixture**
  （F4.1 一致性守卫）。
- 该路径是**在一次事故之后**才加进监视表的：conftest 原文——
  「R5 incident guard: `<repo>/runs` joined the watch list after a fixture
  mkdir briefly created it (empty; removed; disclosed in the packet)」。

**同一个名字，两种含义**：运行时的 `runs/` 装的是治理 packet，项目的 `runs/`
指的是运行输出根。名字撞了，语义无关。

## 2. 实测

为存 packet 建了 `runs/packets/` 之后：

```
tests/test_s0_runner.py   211 passed / 2 failed
  test_attempts_dir_inside_repo_tree_is_never_created_by_the_refusal
  test_root_gate_refusal_writes_nothing_even_to_a_valid_looking_attempts_dir
把 runs/ 移走后同一文件   213 passed / 0 failed
```

两条都断言 `assert not (REPO / "runs").exists()`。**目录存在即失败，与内容无关。**

## 3. 为什么项目侧胜出

优先级格（`~/.claude/CLAUDE.md`）：

> 不可推翻的不变量 > 已封存研究契约 > 项目指令 > **QROS** > 该文件 > 模型默认

`<repo>/runs` 的禁令是项目指令层的、且是 evidence-critical 回归守卫；运行时的
`_SAVE_DIR` 是 QROS 层的一个实现常量。**格上项目侧更高。**

反向做法——为了迁就一个硬编码常量而改动那些回归测试——等于削弱一条为真实缺陷
建立、并在一次真实事故后加固的守卫。不做。

## 4. 处置

- packet 移至 `ops/packets/rv-3651f9fe0b68-da56aecb6991.packet`，**字节未变**
  （sha256 `74fbcea0…` 不变）。
- `<repo>/runs` 已删除，不复存在。
- `qros-state.yaml` 中**追加**一条同 `review_id` 的 correction
  （`pr-rv3651f9fe0b68-002`，`corrects: pr-rv3651f9fe0b68-001`）记录新
  `saved_path`。**没有就地改写**——L6 禁止 in-place completion。
- 验证器复核：`packet-record integrity: no rejection`。

## 5. 给复审者的一句

packet 正文里那行 `REQUIRED SAVE PATH: runs/packets/...` 是运行时生成的，
**已不是它的实际位置**。权威位置是 `qros-state.yaml` 里生效的那条 PACKET_ISSUANCE
的 `saved_path`；packet 的完整性由该记录中的 sha256 钉住，与目录无关。

## 6. 留给 Aaron 的

这是一次**对 operational 运行时的偏离**，不是 bug 修复。两条可能的长期处置，
**都不是我能定的**：

- **A** —— 在 qros-runtime 里把 `_SAVE_DIR` 变成可配置项。那要改一个已认证的
  运行时（902 测试 ＋ 22 conformance ＋ 25 render-checks），代价不小。
- **B** —— 维持本记录这样的按项目偏离。便宜，但每个新项目都要各自发现一次。

在裁定前，本项目按 B 运行。
