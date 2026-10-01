# OUTPUT ROOTS READINESS CHECKLIST（真实运行前运维证明；R5 具名委托建立）

机器可查项（已由 Stage-A `output_roots_operational` 门强制，曝光前 fail-closed）：
- [x] 两根存在且为真实目录（门不创建缺失根——创建=操作者显式动作）
- [x] 非 symlink/junction/reparse point
- [x] 可写（探针文件创建+删除）
- [x] runs-root 卷剩余容量 ≥ 1 GiB（`runinfra.OUTPUT_ROOTS_MIN_FREE_BYTES`，
      量级依据：K=200 全证据合成实测 ~60MB/run，两个数量级余量）

人工/操作者项（本清单不构成运行授权）：
- [x] `C:\Users\Aaron\quant-data\itsf-runs` 与 `…\itsf-runs-archive` 已由
      操作者创建
- [x] 两根均不在任何云同步（OneDrive/Dropbox/Drive/Sync 客户端）监控树内
      ——用各客户端的文件夹清单核对，不以路径名推断
- [x] 卷与路径隔离策略确认：两根互不包含（门已强制）；是否要求不同物理卷
      由 Aaron 裁定并在此记录
- [x] 备份/保留策略与 archive 目录的关系已确认（archive 是复核副本，非备份）
- [x] 磁盘健康/SMART 无警告

## 证明记录（S0-T001 首次真实运行前 attestation，2026-08-14）

授权与签署方式：具名提示词
`START_S0_OUTPUT_ROOTS_ATTESTATION_AFTER_PROMPT_AUDIT`（Aaron，2026-08-14）。
该提示词逐字授权本轮全部外部状态变化（仅建两空目录＋仅经生产窄校验入口
探针＋文档持久化），并具名作出下列运维裁定。本记录不构成 READY 或任何
真实运行授权。

**创建事实**：
- 创建时刻：`2026-08-13T16:01:53Z`（UTC；本地 2026-08-14 00:01:53 +08:00）
- 执行身份：`desktop-b7vtgf0\aaron`（父目录继承 FullControl，未提权）
- 路径（resolve 后绝对路径与裁定值逐字相同）：
  - runs：`C:\Users\Aaron\quant-data\itsf-runs`
  - archive：`C:\Users\Aaron\quant-data\itsf-runs-archive`
- 卷/文件系统：C:（唯一物理卷），NTFS，Healthy；创建后剩余
  1,252,809,990,144 bytes（≈1166.8 GB ≫ 1 GiB 地板）
- Owner/ACL：owner=`DESKTOP-B7VTGF0\Aaron`；两根各 4 条**继承** ACE、
  0 条显式 ACE（含自父目录传播的 `CodexSandboxUsers: ReadAndExecute`）。
  裁定 `ACL_POLICY=KEEP_CURRENT_INHERITED_ACL`——本轮零 ACL 修改。

**窄运维验证（仅生产入口，未触任何真实研究入口）**：
- `runinfra.validate_output_roots`（结构门：绝对性/与 repo 树互斥/两根
  互斥/per-run 路径严格属于 runs-root）＝ **PASS**
- `runinfra.validate_output_roots_operational`（存在/真实目录/非 reparse/
  探针写删/容量地板）＝ **PASS**；两根探针创建并删除成功
- 探针后两根均为空（0 子项）；repo 内 `runs/` 不存在

**同步核验（客户端自身配置证据，非路径推断）**：
- OneDrive Personal 实际挂载点（registry `UserFolder`）＝
  `C:\Users\Aaron\OneDrive`——两根在其外；FileCoAuth 账户无挂载
- Dropbox/Google Drive(FS)/iCloud/MEGA/Box：无安装或配置痕迹
  （info.json/registry/程序目录逐一为否）
- 运行中同步进程仅 `OneDrive.Sync.Service`
- 结论：**SYNC_ATTESTATION=PASS**

**磁盘健康（双源）**：
- `MSFT_PhysicalDisk`：Predator SSD GM7000 2TB，HealthStatus=Healthy，
  OperationalStatus=OK
- `Win32_DiskDrive`：Status=OK
- SMART predict-failure WMI 类不可用（NVMe 常见），已披露，不影响判定
- 结论：**DISK_HEALTH_ATTESTATION=PASS**

**具名运维裁定（来源＝上述具名提示词，逐字）**：

```
SAME_VOLUME_FOR_S0_T001=ACCEPTED_WITH_DISCLOSED_COMMON_MODE_RISK
ARCHIVE_ROLE=INTEGRITY_REVIEW_COPY_NOT_BACKUP
RETENTION=KEEP_RUN_AND_ARCHIVE_INDEFINITELY
EXTERNAL_BACKUP_BEFORE_ANY_FUTURE_DELETION=REQUIRED
EXTERNAL_BACKUP_BEFORE_FIRST_RUN=NOT_REQUIRED
ACL_POLICY=KEEP_CURRENT_INHERITED_ACL
```

同卷共模风险已具名接受并披露：runs 与 archive 同处唯一物理卷 C:，单盘
故障将同时影响两份副本；archive 是完整性复核副本而非备份；两份封存永久
保留，任何未来删除前必须先完成异介质哈希核验备份。

签署：Aaron（经具名提示词 `START_S0_OUTPUT_ROOTS_ATTESTATION_AFTER_PROMPT_AUDIT`）  日期：2026-08-14
