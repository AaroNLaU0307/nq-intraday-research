# TRIAL REGISTRY（append-only；不得重置、删除或重新编号；失败 trial 永久保留）

| trial_id | type | exposure_seq | status | authorized_commit | opened_utc | closed_utc | outcome |
|---|---|---|---|---|---|---|---|
| S0-T001 | FIRST_REAL_S0_FULL_DEVELOPMENT_RUN | 1 | **PENDING_AARON_APPROVAL** | （待 Aaron 授权语句指名） | — | — | — |

规则：状态只能由 Aaron 的批准动作从 PENDING_AARON_APPROVAL 翻转为
APPROVED（授权语句见 S0_REAL_RUN_AUTHORIZATION_PACKET.md §10）；运行
开始时填 opened_utc；无论成功失败均填 closed_utc 与 outcome；任何行
一经写入不得修改语义（勘误以新行追加并互相引用）。
