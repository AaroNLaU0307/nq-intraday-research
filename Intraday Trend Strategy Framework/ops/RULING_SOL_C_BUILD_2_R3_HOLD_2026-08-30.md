＃ 第 3 轮 C_BUILD_2 措辞复审 —— fresh Sol，VERDICT=HOLD

```ini
RECORD_TYPE=REVIEW_OUTCOME（逐字转录，非摘要）
REVIEW_ID=c-build-2-wording-r3
RETURNED=2026-08-30（由 Aaron 转贴）
VERDICT=HOLD
WORDING_MAY_GO_TO_AARON=NO
SEAT=Codex GPT-5.6 Sol，fresh top-level session
SEAT_STATUS=BLIND（席位自陈：OUTCOME_EXPOSED=NONE，未打开／搜索／枚举任何禁区工件）
TRANSPORT_PRECHECK=PASS
```

**本轮不释放任何 gate，不构成 Aaron 的批准。**

## 逐字转录

```
REVIEW_ID=c-build-2-wording-r3
TRANSPORT_PRECHECK=PASS
VERDICT=HOLD
WORDING_MAY_GO_TO_AARON=NO

SECOND_STALE_ANCHOR=YES。所谓 “every sealed FINAL” 和“四条分歧结局”仍是手工枚举的现有路径子集；没有机制证明 resolve_partial 的返回/异常路径集合已经闭合。

APPROVAL_GUARD_ASSESSMENT=
1. 对 ND1_PROFILE_RATIFICATION.md 内新增的唯一 APPROVED_*SHA256 声明，守卫确实失败闭合；内存追加新声明后，8 条中精确 1 条变红。
   但它没有闭合“所有批准”，只闭合“该文件内符合该字段语法的批准”。加入携带 profile id、SHA-256、doc HEAD 的散文式批准后，8/8 仍绿。
   SIGNABLE_RATIFICATION_ROUTES=1 若是权威、冻结且机械强制的治理不变量，可以补足这个边界；当前受审集只给出 builder 自报，未钉住该不变量，因此不足以支持无条件 PASS。
2. R3 原像位于文件名含 PROPOSAL 的文件中，本身不是问题。批准由 commit/path/span/SHA-256 与后续 ratification record 建立；R3 与 CR1 原像均独立重算匹配。
3. 有范围取代的推理成立：R2 只改 P3，R3 只改 P3/F3；三个 profile 原像中的 C_BUILD_2 锚定字段逐字一致。更准确的依据应是“所有已登记 profile 原像均受守卫”，而不是单独声称 R1 继续管辖。

CLASSIFICATION_OF_A=分类改为“被钉住的机制性质”是正确的；调用后文件系统状态不能证明比较发生过。但现有 pin 没有闭合新增控制流路径，因此分类正确、证据不足。

PINNED_MECHANISM_OVERUSE=类别本身未被滥用；裁定 B 明确允许机制性质承重，门仍可作为调用结局/异常分类器。滥用发生在把开放世界的手工路径枚举称为“已钉住”。当前分类域与检测域没有机械闭合，因此门学说尚非名存实亡，但不足以承重。

CRITERION_1_NOW_MET=NO：
(a) NO——新增“写出 FINAL、不读取、直接返回 already_sealed”的路径后，59/59 仍绿。
(b) NO——新增经 getattr(...,"unlink") 删除 .partial 的路径后，59/59 仍绿。
(c) NO——同一变异返回 retry_permitted，却无残留、无 preserved_as，59/59 仍绿。

CONDITIONS_MET=
1 MET——采用追加/超越形态，旧文本保留。
2 NOT_MET——判据 (1) 覆盖保全 NO；(2) 证伪保全 NO；(3) 不得回并 YES；(4) 锚定保全仅条件成立，故 NO；(5) 缺口出清 YES。
3 NOT_MET——本轮为 HOLD，且无 Aaron 批准。
4 MET——裁定记录 commit 之后 supplement_runner.py、supplement_contract.py 零提交/零 diff；GATE_TABLE 与 CHECKPOINT_OF 保持不变。
5 MET——test_c_build_2s_state_is_not_observable_to_a_caller 保留并通过。

HISTORICAL_FACTS_LOAD_BEARING=对本次 HOLD 均不承重。历史全仓搜索已由四份批准原像的精确重建替代；历史变异结果不能推翻本轮的新鲜反例；上一轮 delivery 旧字节不影响当前传输预检。未来若申请 PASS，应提供当前字节上可复跑的闭合变异证据，而不是依赖历史自报。

UNVERIFIABLE_SELF_REPORTS=SIGNABLE_RATIFICATION_ROUTES=1；此前各条历史变异运行结果；此前全仓搜索完整性；旧 delivery 字节；builder 隔离事故只返回计数及“红套件中提交”的历史细节。它们均未被用来形成本次 HOLD。

NEW_DIVERGENCE_SHAPES=
1. 在原函数 docstring 后新增未读取 FINAL 的 already_sealed 早退；其余原函数体不动。
2. 新增经由值调用 unlink 的残留删除路径，并返回既有 retry_permitted 动作。
3. 批准以散文携带 id/hash/doc HEAD，但不采用 APPROVED_*SHA256= 字段。
三者均绕过对应现有守卫。

STRONGEST_OBJECTION=这些测试再次把“我列出的现有路径”当成“所有可能路径”。直接在原函数 AST 中新增违规路径后，两种变异各自仍然 59/59 全绿；这正是第二个“锚在子集上”的锚。

FINDINGS=
HIGH（高置信）——C_BUILD_2 的路径/结局覆盖不是失败闭合。证据位置：
tests/test_every_sealed_final_was_read_back.py:83-134；
tests/test_c_build_2_wording_coverage.py:45-106；
tests/test_n09_checkpoint_assertions.py:123-236,262-388；
src/itsf/mc/supplement_runner.py:834-840。
纯内存、原函数 AST 插入变异分别证明未校验 FINAL 与静默删除残留都可在 59/59 绿灯下发生。最小修复方向是建立机器可检查的封闭返回/异常路径合同，并要求每个新增路径显式承担 (a)/(b)/(c) 的证据；不可只把本轮两个反例追加成新用例。

MEDIUM（高置信）——批准守卫的发现域由单文件＋字段命名正则定义，却被表述为“每份批准”。证据位置：
tests/test_every_approval_is_accounted_for.py:180-202；
ops/N09_EXECUTION_PATH_DESIGN_R3.md:1254-1256。
规范字段新批准会红，但散文式批准令 8/8 仍绿。需要机械钉住唯一有效批准路线，或把守卫声明缩窄到其实际检测域。

SCOPE_CREEP=NO
UNRESOLVED_FOR_AARON=是否把“批准仅在 ND1_PROFILE_RATIFICATION.md 中以强制 APPROVED_*SHA256 字段追加后才生效”确认为权威治理不变量；若确认，仍需机械钉住。无论该项如何决定，HIGH 路径闭合缺陷都须先修并重新送 fresh review。
SEAT_STATUS=BLIND
INDEPENDENCE_STATEMENT=会话：全新顶级会话，非第 1/2 轮；作者身份：非受审字节作者；实现/修复：完全独立，只读，零磁盘修改；设计贡献：无，仅提出反例与验收方向；模型多样性：相对 Opus builder 与 Fable 决裁席存在，相对前两轮 Sol 仅有会话独立、无模型家族多样性；经验/样本：OUTCOME_EXPOSED=NONE，未打开、搜索或列举任何禁区工件。
```

执行证据（席位自陈）：当前五文件标准库套件 `59/59` 通过；两个原函数 AST 违规变异也分别
`59/59` 通过。十份受审路径最终工作树状态为空，未修改任何文件。

## builder 的处置

**接受，两条都接受，且不辩解。** 处理见
`ops/FINDINGS_SOL_R3_REPRODUCED_2026-08-30.md`（逐条复现在先，采信在后）。

一条对 builder 有利的事实，如实记下而不当作抵消：**CONDITIONS_MET 第 4 条 MET**
—— 裁定记录 commit 之后 `supplement_runner.py` 与 `supplement_contract.py`
零提交、零 diff。冻结登记册在整个 08-29 通宵里挡住了一次真实的越界
（见 `ops/PREPARED_C_BUILD_1_GATE_WIRING.md`）。
