＃ P2S ＋ 重授权 P2 已追加，N09 首跑停在一个新 blocker

```ini
RECORD_TYPE=EXECUTION_EVIDENCE
AUTHORIZED_BY=Aaron，2026-09-05，逐字确认两行内容后签署
EXECUTED_BY=Opus 5，builder seat
REGISTRY_COMMITS=ba8c244（seq 16 P2S）· ffb15ae（seq 17 P2）
WITNESSES=WITNESS_P2S_APPENDED_2026-09-05.json（sha256 0a8bf526…）
          WITNESS_P2_REAUTHORIZED_2026-09-05.json（sha256 aeecb85e…）
          两份都是**追加后立即**写的，不是补记的
```

---

## 1. 追加了什么

```
seq 16  SUPPLEMENT_EXECUTION_AUTHORIZATION_SUPERSEDED   actor Aaron
        supersedes_event_sequence: 15
        superseded_authorized_commit: 301de7bd8b2c7bdf02964e39a9729c39b4a5c691
        reason_code: PRESTART_COMMIT_CHANGE
        incident_id: INC-79851de94465
        successor_authorized_commit: 74acf282b9a2c96ac093ad44294a31b1083cd7c2
        same_id_reauthorization: YES
        sha256  27b4983f… -> 0229418f…

seq 17  SUPPLEMENT_EXECUTION_AUTHORIZED                 actor Aaron
        authorized_commit: 74acf282b9a2c96ac093ad44294a31b1083cd7c2
        output_root: C:\Users\Aaron\quant-data\itsf-runs
        sha256  0229418f… -> 8d538da2…
```

这是 [`AMENDMENT_P2_TO_P2S_PRESTART_2026-09-05.md`](AMENDMENT_P2_TO_P2S_PRESTART_2026-09-05.md)
批准的直边第一次实际使用：**没有制造任何 F1**，也没有创建任何
`attempts_dir`。

## 2. 追加纪律

每次追加前先断言登记册字节**等于上一步验证／见证过的那个状态**，写完断言是
**纯追加**（`after == before + row`）。

追加过程中登记册会短暂处于 `P1, P2, P2S`、**0 条 live 授权**的中间态。
这个状态在内存里**事先验过**是合法的——没有先验就写，等于赌它合法。

两份见证都核对过：记录的 sha256 等于当时的登记册、记录的末行确实在文件里、
事件数复算一致、无 OneDrive 冲突副本。

## 3. 追加后实测

```
chain.problem            ''
short_ids                ('P1', 'P2', 'P2S', 'P2')
seq 15                   已 superseded（不再 live）
live authorizations      1（seq 17）
live commit              74acf282b9a2c96ac093ad44294a31b1083cd7c2
P3 / RUN_STARTED         不存在
consumption              无
```

## 4. N09 首跑：1 秒内停在 `bundle_manifest_coverage`

```
运行 incident   INC-9b6a83e22429（与 P2S 的 INC 分开）
停止点          MCInputError: bundle_manifest_coverage
                REGISTRY_AFTER_RUN_STARTED.json: no well-formed manifest digest
副作用          **零** —— 两个 supplements 子树仍为空，未创建任何目录，
                未读一根 Development 数据（它停在 prepare 里，比数据获取还早）
```

**这不是数据损坏，是两个已批准模块对同一个文件的分类矛盾**：
`s0/output_proof.py` 把 `REGISTRY_AFTER_RUN_STARTED.json` 归为
`infrastructure_files`（运行基础设施写入、渲染器未产出、**因此必须不得出现在
`sealed_files` 里**），而 MC consumer 的覆盖检查只排除 `manifest.jsonl`。

Aaron 当日裁定按「对齐已批准的 S0 文件分类」处理，只改 MC consumer 的谓词，
不动任何已封存字节、不补 manifest entry。修复与三项前置核实见
`consumer.S0_INFRASTRUCTURE_FILES` 与
`tests/test_infrastructure_file_manifest_exemption.py`。

## 5. 修复后：越过了那一条，停在**下一条**

```
MCInputError: record_schema_violation
  MC_HANDOFF_E1_Base.jsonl:0 field set != TradePathRecord(19)
```

实测（**只读字段名，不读任何值**）：

```
双方都是 19 个字段，17 个相同
封存记录里有、TradePathRecord 里没有   entry_timestamp, exit_timestamp
TradePathRecord 里有、封存记录里没有   entry_ts, exit_ts
```

**同一族的第二个实例**：两个已批准组件对同一份封存数据的字段命名不一致，
而合成夹具一直用的是 consumer 那一套名字，所以从未暴露。

**未处理。** 它改变的是 consumer 如何解读已封存的研究数据，归 Aaron 裁。

## 6. 没有动的

```
S0-T001 已封存字节        一个字节未改
manifest.jsonl            未补任何 entry
真实 registry             本轮修复期间未再动
record_schema 那一条       未碰
governance packet/review  未新增
```
