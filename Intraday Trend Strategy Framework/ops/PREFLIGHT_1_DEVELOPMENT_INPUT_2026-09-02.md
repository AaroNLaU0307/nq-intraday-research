＃ ① DEVELOPMENT INPUT AUTHORIZATION PREFLIGHT

```ini
RECORD_TYPE=PREFLIGHT（不授权、未调用 load_real、未读任何 payload）
BY=Opus 5，builder seat，2026-09-02
MEASURED_AT=0cefc1503858ecf3b1dc5c90ec8bb3de9b1daa97
本次做了什么：只读的目录检视与 manifest 元数据读取。
            139 个 .dbn.zst 一个都没有打开。
```

---

## 1. Review 结果 —— **尚无结果，且不该由我给**

我是写了 R1–R4 全部内容的 builder。你的规矩：**独立性在会话不在模型**，
且 producing session 不得是同一交付物的唯一认证者。所以：

```
我能做的   备包 -> ops/REVIEW_PACKET_PRE_REAL_DATA_2026-09-02.md（已备好）
我不能做的 自行调用 Fable/Sol，或自己出 verdict
待你做的   派发该包；席位返回后把 verdict 给我
```

**这一格是空的，我不会用自评把它填上。**

包内已含：机器生成的 12 条禁读清单、四块受审面按承重排序、
**我自己报告的四条弱点（请席位核实而非采信）**、只读复现命令、四个必答问题。

**并已写明：本次复审不满足 A2、也不满足 Stage I，不解开任何 QROS 门。**

## 2. 候选 job_dir —— **有两个，我不替你选**

```
候选 A  C:\Users\Aaron\quant-data\databento-archive\intraday-trend\development_signal\GLBX-20260727-DL3BEBCHJA
候选 B  C:\Users\Aaron\OneDrive\Desktop\CV\quant-data\databento-archive\intraday-trend\development_signal\GLBX-20260727-DL3BEBCHJA
```

**两者的 job id 相同，manifest 逐字节相同**（`manifest.json` 与
`_local_manifest.json` 的 sha256 两边一致），文件数同为 143。

### 2.1 机械证据：A 与 B 的差别在**认证**，不在内容

`ops/physical_copy_attestation.json`（由 `ops/SECOND_COPY_ATTESTED.flag` 指向）逐字写着：

```
primary_root : C:\Users\Aaron\quant-data
backup_root  : E:\quant-data
verified_at  : 2026-07-28T16:04:43Z
all_raw_sha256_match : True     20304 <-> 20304 files
```

```
候选 A  == primary_root 之下                     -> 被 attestation 覆盖
候选 B  既不是 primary_root，也不是 backup_root   -> **不在 attestation 里**
E:\quant-data  实测**当前不存在**（该卷未挂载）   -> 备份副本现在不可达
```

**候选 B 位于 OneDrive 同步树内。** 它的内容今天与 A 一致，
但它受同步影响，且没有任何 attestation 覆盖它。

### 2.2 一条必须一起报的弱点

**`_check_role` 区分不了这两者。** 它只要求路径含 `development_signal`
且不含其他 role 标记 —— A 和 B **都会通过**。

所以「用哪一个」是一个**真实的、有后果的选择**，守卫不会替你把关。
按你的第 3 条，我把两个都列出来，不自行选择。

**我的建议（仅建议）：A。** 唯一理由是机械的：它是 attestation 覆盖的 primary。

## 3. filename 与 source_format

```
source_format  "dbn"          —— load_real 的默认值，且这批文件是 .dbn.zst
filename       load_real 一次只接受**一个** filename
```

**将来实际会读取的精确文件集合：该 job_dir 下全部 139 个 `.dbn.zst`。**

不是子集，理由是机械的、可引用的：

```
冻结数据角色表（src/itsf/data/roles.py:9，引自 S0 preregistration 行 24-26）
  Development | NQ.v.0 ohlcv-1m | 2010-06-06 -> 2022-01-01(excl)
_local_manifest.json 逐字吻合
  start 2010-06-06   end 2022-01-01   data_file_count 139
已裁定的 tercile 参照
  RULED_VOL_TERCILE_REFERENCE = full_development_expost
  -> 波动率 tercile 必须在**完整 Development 样本**上界定，
     所以 universe 必须覆盖全窗口，不能只取封存日
```

文件名形如 `glbx-mdp3-YYYYMMDD-YYYYMMDD.ohlcv-1m.dbn.zst`，逐月：

```
首   glbx-mdp3-20100606-20100630.ohlcv-1m.dbn.zst
末   glbx-mdp3-20211201-20211231.ohlcv-1m.dbn.zst
```

**末月是 2021-12，与「2022-01-01 不含」严格一致。**

## 4. manifest path 与 expected sha256

```
生效的 manifest   <job_dir>\manifest.json          （官方 Databento 格式）
                  sha256 d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8

**不是** _local_manifest.json —— 它存在，但**没有 `files` 映射**，
所以 load_manifest 按其优先级规则落到官方 manifest.json。
这一点是执行 load_manifest 得到的，不是读代码猜的。
```

机械核对（用**生产的** `manifests.load_manifest`，非我自写的解析）：

```
manifest 条目          141   （139 数据 + condition.json + metadata.json）
磁盘文件               143   （141 + manifest.json + _local_manifest.json）
数据文件不在 manifest  0
manifest 条目不在磁盘  0
```

两个端点的 expected sha256（取自 manifest，**未对文件做任何哈希**）：

```
glbx-mdp3-20100606-20100630.ohlcv-1m.dbn.zst
  9c66e285bc9afc08948365e0f5be1884ade1a56e635cf636e25e29a2df2e4c36
glbx-mdp3-20211201-20211231.ohlcv-1m.dbn.zst
  6a3f17c8e1f7474aaa4ab122d69087350f99d07ba86f6946079e3b51074c074d
```

全部 139 条 expected sha256 已在 manifest 内；**我没有重算任何一个**——
重算就要读 payload。`verify_file_against_manifest` 会在真正读取时逐文件比对。

## 5. 是否仍有阻断 ① 的 High/Medium engineering finding

**我不能回答「没有」，只能回答我知道的部分：**

```
我已知的、阻断 ① 的                无
我已知的、不阻断 ① 但需一起过审    R1（未独立复审的修复）
                                    R2（UNMAPPED_SEAL_CODES 7 条）
                                    §2.2（role 检查区分不了 primary 与副本）
                                    §6（E: 备份卷当前不存在）
```

**但「有没有 High/Medium」正是复审要回答的问题（包内 Q3）。**
在席位返回之前，这一格只能是「builder 未发现，未经独立确认」。

## 6. 一条本次新发现的 residual

```
attestation 里的 backup_root = E:\quant-data  实测不存在
-> 「第二份物理副本」当前**不可达**
-> ops/SECOND_COPY_ATTESTED.flag 仍然存在，因而 assert_real_run_allowed 仍然通过
```

**flag 断言的是 2026-07-28 当时验证过，不是「此刻仍然可达」。**
这与迁移时记下的 S8（跨卷备份不可满足，只有一个卷）是同一件事的两面。
是否要在读真实数据前恢复第二份副本，**是你的决定，不是我的**。

## 7. 我在本次没有做的事

```
未调用 DevelopmentSignalLoader.load_real
未打开任何 .dbn.zst
未对任何数据文件计算哈希
未创建任何目录、未写任何真实输出
未修改 job_dir 下任何字节
```

本次只做了：目录列举、读 `_local_manifest.json` 与 `manifest.json`
（均为元数据）、读 `ops/physical_copy_attestation.json`、执行生产的
`manifests.load_manifest` 做覆盖核对。

## 8. 顺序（按你 2026-09-02 的安排）

```
1  你派发 ops/REVIEW_PACKET_PRE_REAL_DATA_2026-09-02.md
2  席位返回 verdict -> 给我
3  你在 A / B 之间选一个，并给出 ① 的封闭授权语
4  我接线、跑全套、冻结最终 HEAD 并当场读给你
5  然后才进入新的 live P2
```
