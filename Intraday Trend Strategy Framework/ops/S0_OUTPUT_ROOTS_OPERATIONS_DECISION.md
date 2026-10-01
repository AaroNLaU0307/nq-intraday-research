# S0_OUTPUT_ROOTS_OPERATIONS_DECISION（输出根运维决策记录，2026-08-14）

来源：`S0_OUTPUT_ROOTS_OPERATIONS_DECISION_PACKET`（Fable 只读勘察，
2026-08-13 交付聊天）→ Aaron 以具名提示词
`START_S0_OUTPUT_ROOTS_ATTESTATION_AFTER_PROMPT_AUDIT` 裁定并授权执行。
执行与证据全文见 `ops/OUTPUT_ROOTS_READINESS_CHECKLIST.md` 证明记录节。

## 1. 裁定（逐字，不再重议）

```
RUNS_ROOT=C:\Users\Aaron\quant-data\itsf-runs
ARCHIVE_ROOT=C:\Users\Aaron\quant-data\itsf-runs-archive
SAME_VOLUME_FOR_S0_T001=ACCEPTED_WITH_DISCLOSED_COMMON_MODE_RISK
ARCHIVE_ROLE=INTEGRITY_REVIEW_COPY_NOT_BACKUP
RETENTION=KEEP_RUN_AND_ARCHIVE_INDEFINITELY
EXTERNAL_BACKUP_BEFORE_ANY_FUTURE_DELETION=REQUIRED
EXTERNAL_BACKUP_BEFORE_FIRST_RUN=NOT_REQUIRED
ACL_POLICY=KEEP_CURRENT_INHERITED_ACL
```

裁定依据（勘察事实）：本机仅一个物理卷（C:，NTFS，Predator SSD GM7000
2TB，双源健康 OK）；两根不在任何同步客户端监控树内（客户端配置证据）；
每 run 证据量级 ~60MB，容量余量两个数量级以上。同卷共模风险
（单盘故障同时影响 run 与 archive 两份副本）已具名接受并在检查表披露；
补偿控制＝任何未来删除前强制异介质哈希核验备份。

## 2. 冻结覆盖口径（本轮统一措辞，具名裁定）

```
FROZEN_RUNTIME_CANONICAL_SET_COUNT=7
APPROVAL_PROVENANCE_ORIGINALS={gate1/G9_EVIDENCE_RESOLUTION.md,IR_APPROVAL_PACKET.md}
APPROVAL_PROVENANCE_BINDING=AUTHORIZED_COMMIT_PLUS_GIT_CLEAN
APPROVAL_PROVENANCE_IN_A12_DIRECT_HASH_SET=NO
```

说明：`guards.FROZEN_HASHES` 是**运行时正典 7 文件集**，不是（也不声称
是）`FREEZE_LOG.md` 全部历史登记行的覆盖清单。两份批准来源件不在 A12
直接哈希集内，其防篡改绑定机制＝真实运行授权锚定精确 commit ＋ Stage-A
强制 git-clean：授权后对树内任何文件的改动都会脏树/换 HEAD 而被门拒绝。
正式运行契约保持 7 项，不扩为 9；本轮零 guards/report/output_proof/生产
代码改动。

## 3. 已执行的外部状态变化（全部在具名授权内，无其他）

1. 创建空目录 `C:\Users\Aaron\quant-data\itsf-runs`；
2. 创建空目录 `C:\Users\Aaron\quant-data\itsf-runs-archive`；
3. 经 `runinfra.validate_output_roots_operational` 在两根内各写删一个
   探针文件（生产窄入口；探针后两根仍空）。

未执行：READY/RUN_AUTHORIZED/RUN_STARTED 追加、真实 S0、真实数据读取、
ACL 修改、外部备份复制、registry/exposure 修改、tag、策略 build。

## 4. 后续闸（每项需具名批准，本记录不构成其中任何一项）

Codex 运维终审 → Aaron 对精确 HEAD 追加 READY → Aaron 按 registry §10
格式对 S0-T001 发出精确 RUN_AUTHORIZED → 首次真实 S0。
