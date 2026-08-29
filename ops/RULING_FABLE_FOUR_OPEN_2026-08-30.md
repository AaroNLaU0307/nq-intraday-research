＃ 四件待裁 —— Fable 决裁席的答复（**顾问级**）

```ini
RECORD_TYPE=ADJUDICATION_OUTCOME
REVIEW_ID=dec-four-open-2026-08-29
SEAT=Fable 5
INDEPENDENCE=**NOT_INDEPENDENT** —— builder spawn 的子代理。
             QROS：独立性活在会话里不在模型里；subagent 对其 spawner 不独立。
             因此以下四条是**顾问级结论**，不是独立裁决。
DELEGATED_BY=Aaron 2026-08-30「其余的问题如果你拿不定决定或者裁决，
             交给 fable 也行，让它替我做裁决」
PACKET=ops/DECISION_PACKET_FOUR_OPEN_2026-08-29.md
PACKET_SHA256=63dd2b29acbb648b6c81bde9a0d14a849a6a19db6d8fc0c711babc1598d4e55f
             （席位复算一致）
SEAT_EXPOSURE=ops/REVIEWER_EXPOSURE_LOG.md 第 5 行（PENDING_AARON，席位自评）
```

**采纳前 builder 逐条复现。凡可开源码核实的都核实了，结果见每条的「builder 复核」。**

---

## 第 1 件 `production_payload_unsupported_type` —— 裁定：**乙，且必须限定作用域**

映射为 `("C_BUILD", "row_schema_blind")`，**仅限 `classify_builder_failure` 一侧**；
`classify_seal_failure` 一侧维持大声拒绝。

### 席位的理由（其中一条是决定性的）

`build_supplement_from_authority` 内该码的**唯一**抛出源是
`supplement_production.py:280` 的 `rows = _freeze_value(list(day_rows))`，
发生在载荷组装之前；`binding` 由 :268 从 authority 推导后
**不经 `_freeze_value`** 直接传入。**所以在 builder 分类器的辖域里，
触发源只能是行。**

### builder 复核 —— **成立**

逐字读 :266-282：`_freeze_value` 只作用在 `list(day_rows)` 上；
`expected_day_set, binding = _sa.supplement_build_inputs(...)` 之后
`binding=binding` 直接进 `build_day_strata_supplement_test_only`，中间无冻结。
作用域切分的另一半也成立：`freeze_payload`（:187-220）委托给 `_freeze_value`
并作用于**整个载荷含 binding**，故封印侧确实混源。

### 它指出我错在哪 —— 我接受全部三条

1. **「从严的一边也是对的一边」在这里不成立。** `ClassificationError` 全仓无人接住，
   真跑时会穿透 `run_c_build`，于是**一次完整性缺陷恰好成为登记簿唯一记不到的
   缺陷类别**。fail-closed 管的是动作（写、封存、晋升），不是拒绝记录一次已发生的失败。
   **我在包里自己写了「这一条我没有反驳」，那个让步是决定性的，我却仍选了从严。**
2. **我把「拿不定」当成了事实状态，而那只是没做数据流分析的状态。** 我把 :280
   （builder，纯行）与 :378/:391（seal，混源）两个抛出面糊成一个问题，
   于是制造出一个本不存在的不可判定。
3. **「`row_schema_blind` 只管四个结构行字段」被我自己维护的已裁表反驳** ——
   `vol_mapping_shape`、`vol_vocabulary_drift` 等形状与词表码都不是「四字段的值」，
   却早已在该门名下。

### 已执行

`STAGE_GATE_OF_BUILDER_CODE` 新增该映射并附数据流理由；
`UNMAPPED_BUILDER_CODES` 清空但**机制保留**（下一个无门码仍落在那里）；
另按席位第 4 点订正了 `day_strata_pipeline.py` 里一句已成假的注释
（「unmapped code 不是 run failure」—— 真实数据帧的 numpy 标量泄漏就是）。

---

## 第 2 件 运行时目录授权形制 —— 裁定：**不重裁，此问已由 owner 裁过**

`ops/OWNER_DECISIONS_2026-08-29.md` §5 逐字裁了**乙**，§6 写「形制已定（乙）」。

### builder 复核 —— **成立，这是我的流程缺陷**

见 `ops/DIRECTORY_CREATION_GRANTS.md` 末尾 `订正-ALREADY-RULED-2026-08-30`。
最坏形态：**一个 builder spawn 的子席位静默覆盖 owner 裁定**。它没有发生，
是因为席位认出并拒绝重裁 —— **那是它的功劳，不是流程的功劳**。

席位另外逐字核了 ND1 文本（`DECISION_PACKET_N00_AND_ND1.md:1112`
「目录创建、写探针、执行是三次独立授权，不得合并」），裁掉了我那条自疑：
「三次**独立授权**」封死的是授权身份的合并，不是句子排版，**甲确实走不通**。

已机械化：`tests/test_no_settled_question_is_sent_to_adjudication.py`。
它**管不了语义重叠**，只强制「核对这一步必须发生并留痕」—— 局限写在文件里。

---

## 第 3 件 席位跨两仓 —— 裁定：**采 builder 倾向，加两条硬化**

两仓各记各自仓内的那次消耗、`cause` 互指。理由：席位轴是**逐项目 fail-closed** 的，
「单一台账＋另一边放指针」会让一根轴的状态依赖项目外字节。

**两条硬化（builder 需照办）**：

1. 两仓的行必须携带**逐字相同的席位标识**（session／review_id），
   使任何跨仓 join 能按**席位**去重 —— 现在靠习惯，应立为规则。
2. `cause` 互指必须**双向、同时**落笔。单边先记、另一边「回头补」会重现假 `NONE`，
   而 08-28 更正案已经证明「回头补」会变成永久缺口。

**builder 状态：接受，两条硬化待执行**（qros 侧目前尚无席位行，无 join 可做；
下一条跨仓席位出现时同时落笔）。

---

## 第 4 件 研究轴指针行 —— 裁定：**归 Aaron，本席明确不裁**

并直答包问：它**落入**「研究轴记账」类 —— 不是因为指针行是暴露事件，
而是因为**任何实现都必须修订研究轴记录的已批准结构**
（`tests/test_exposure_ledger_migration.py` 钉着逐行恒等与已批准闭集词表）。

**顾问意见：建议 Aaron 裁「不加」。** 指针行要买的可发现性已被
`qros-state.yaml` ＋机械测试满足；「两轴永不合并」是常备明令，指针行是一次软合并；
为零信息增益去修订全部机械守卫，纯下行。

**builder 状态：不动，等 Aaron。**

---

## 席位的总结，逐字保留

> 四件里 builder 的实体倾向三对一空（第 1 件方向对但理由错、作用域没切；
> 第 2 件结论与 owner 已裁重合；第 3 件对但缺硬化；第 4 件正确让渡）。
> 真正的缺陷都在**记录层**：一个被自己未做的数据流分析撑起来的「不可判定」，
> 和一次把 owner 已裁事项当未决送裁。两者同形：**未经核对的陈述与真实事实并排，
> 读起来一样。**
