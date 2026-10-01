# CODEX_REVIEW_PACKET — M6.1（供 Codex 独立检查真实仓库）

- 审查对象：本 packet 所在 commit（`git log -1` 取；单一候选，自 08fca9b）
- 性质：Codex HOLD 十项的 Track-E 工程修复＋Track-D 六项决策包；
  **未追加 READY、未申授权、真实 S0 锁定、registry 未动、合成链通过
  ≠ 真实生产链可运行（五项方法未裁，Stage B fail-closed）**

## Track E 交付（Opus 工作树审计后 1 轮修复闭合）
E1 ResolvedS0Methods 单源＋resolved_study_config 共享谓词（全字段
non-None 仍 fail-closed 至派生接线落地）；E2/E3 report.py 13 键
FORMAL_SECTIONS＋严格 JSON＋R1-R10＋O2 补 A2 矩阵与记录守恒＋封存后
manifest 再验证（O5 call-site 测试钉线）；**O1 已闭：legacy structural
封存旁路删除（无 study 即拒），旧 e2e 反转为拒绝断言**；E4 stability
四轴＋vol 未裁拒封存；E5 seed 硬化（公共 API 拒非冻结 seeds、mc 单源）；
E6 handoff UNRESOLVED 哨兵；E7 S0Runner A→F 合成 e2e 双向；扫描器纳
未跟踪文件；O3 packet §0 补 report/stability/handoff 三行哈希；O7
pending_decisions 必填。

## Opus 审计遗留（接受披露，非阻塞）
O4（Med）：五个已裁字段暂无注入点——防线=派生分支未实现即 fail-closed；
裁决落地日须按"每字段一消费者＋机器断言"接线（记入 DECISION_REQUIRED
执行清单）。O6/O8（Low）：严格 JSON 双冗余网与新模块纯度参数化未钉
（_clean 主防线已变异钉死）。审计其余全 CLOSED（含四组变异、方法泄漏
狩猎零命中、E7 真实性）。

## 验证主张
pytest 732/0/0＝地板＝钉；扫描 CLEAN（含未跟踪盲区修复，隔离仓验证）；
冻结哈希 OK；git diff --check 干净；工作树离场 clean。

## Track D
DECISION_REQUIRED_M6_1.md 六项（DR-3 = unresolved_disagreement
Fable B vs Sol A）；M6_HOLD_RESPONSE.md 已按 Aaron §二勘正三处。
