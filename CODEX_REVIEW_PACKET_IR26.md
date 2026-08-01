# CODEX_REVIEW_PACKET — IR-26（供 Codex 独立检查真实仓库）

- 审查对象 commit：`6cb7eb718c903d119b7e51c7171e6db6f43aca67`
- 仓库：`Quant trade/Intraday Trend Strategy Framework/`（本地 git）
- 性质：第二次真实 S0 尝试 Stage-B 失败（INC-fa9234e0e541）的修复里程碑；
  exposure 未消耗，S0-T001 完好

## 变更面（全部 diff 均对 08e74235 基线）

| 文件 | 变更 |
|---|---|
| src/itsf/s0/context.py | `_prev_close_map` NA 条件删 vendor-degraded 子句（IR-26 规则 5/6）；isnan→isfinite（规则 7）；新 sidecar `prev_close_from_vendor_degraded`（S0Universe 字段＋per-day sidecar 键）；docstring 勘正 |
| scripts/s0_real_run.py | `structural_actuals_from` 缺失判定 key-membership→`is None`；地板 519→524；其余不动（含 `load_real_session_schedule` 完整 20 日标记集保留） |
| tests/test_s0_context.py | ＋4：degraded＋精确close→可用＋diagnostic；degraded＋close 缺失→NA；非 finite→NA；逐日 preflight 等价矩阵（七类案例） |
| tests/test_s0_runner.py | ＋1：actuals value-None 计缺失＋聚合 reason 守恒；地板钉 524 |
| ops/TRIAL_REGISTRY.md | ＋"+"失败行（runner 追加）＋行 10 supersede 行 9（STAGE_B_ANCHOR_SEMANTICS_FIX） |
| IMPLEMENTATION_RESOLUTIONS.md | IR-26 全文（八条语义＋实施边界＋验证记录） |
| S0_REAL_RUN_AUTHORIZATION_PACKET.md | §0 context/入口两行哈希再渲染 |
| attempts/S0-T001-A20260801T162047Z/ | 第二次尝试失败工件封存（含 Stage-A 授权快照） |

## 需要 Codex 独立验证的主张（按证据强度排序）

1. **真实数据 66 断言全符**：`RealChain` 实测 vs 锁定 json（9d6dd1c1）
   compare all_pass=True、零 missing/extra/mismatched；六个曾失配键现为
   18/2864/76/2806/17/18。
2. **逐日等价**：修复后 18 个 None 日与锁定 json
   `anchors.prev_rth_close.missing_dates` 逐日一致；diagnostic sidecar
   恰 6 日（=condition 标记但有 bar 的参照日之后继）。
3. **变异判定力**：重插标记子句→test_ir26_degraded_reference… 红；
   回退 key-membership→test_actuals_prev_close… 红。
4. **未越界**：dataset/labels/features/runner/runinfra/contracts/guards
   对 08e74235 字节不变（git diff 范围核对）；冻结方法文件 7/7 哈希过；
   `load_real_session_schedule` 未被收窄（Aaron 实施边界红线）。
5. **电池**：524/0 skipped、扫描 CLEAN、packet §0 12/12 哈希符。
6. **registry 链**：行 1-9 与"+"行字节不变（纯追加）；行 10 五字段
   精确引用行 9；生产解析器现返回 0 存活授权。

## 已知非阻塞背景

- P3 backlog：SA-14/15 六条观察（>40hex 截断、supersede 多字段组取首、
  非数字 seq 不可 supersede、合成 seq 89 碰撞余量、trial-ID 字面耦合、
  跨 trial 授权楔死——trial 2 前须裁决）＋SA-13 hook 新鲜度测试。
- 本 commit 之后流程：SA-16 只读审计（含隔离授权态 Stage A+B 可满足性
  探针，不入 Stage C）→ ALL_CLOSED → READY 事件 → Aaron 新 §10。
