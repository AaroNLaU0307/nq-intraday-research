# OUTPUT ROOTS READINESS CHECKLIST（真实运行前运维证明；R5 具名委托建立）

机器可查项（已由 Stage-A `output_roots_operational` 门强制，曝光前 fail-closed）：
- [ ] 两根存在且为真实目录（门不创建缺失根——创建=操作者显式动作）
- [ ] 非 symlink/junction/reparse point
- [ ] 可写（探针文件创建+删除）
- [ ] runs-root 卷剩余容量 ≥ 1 GiB（`runinfra.OUTPUT_ROOTS_MIN_FREE_BYTES`，
      量级依据：K=200 全证据合成实测 ~60MB/run，两个数量级余量）

人工/操作者项（Aaron 签署后方可视为 READY 的运维前提；本清单不构成运行授权）：
- [ ] `C:\Users\Aaron\quant-data\itsf-runs` 与 `…\itsf-runs-archive` 已由
      操作者创建
- [ ] 两根均不在任何云同步（OneDrive/Dropbox/Drive/Sync 客户端）监控树内
      ——用各客户端的文件夹清单核对，不以路径名推断
- [ ] 卷与路径隔离策略确认：两根互不包含（门已强制）；是否要求不同物理卷
      由 Aaron 裁定并在此记录
- [ ] 备份/保留策略与 archive 目录的关系已确认（archive 是复核副本，非备份）
- [ ] 磁盘健康/SMART 无警告

签署：________（Aaron）  日期：________
