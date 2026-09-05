＃ 第二份物理副本 —— 当前状态

```ini
RECORD_TYPE=MEASUREMENT（只读；未拷贝、未认证、未创建任何目录）
BY=Opus 5，builder seat，2026-09-02
```

---

## 1. 明确状态

```
CURRENT_BACKUP_AVAILABLE = NO
```

**不是「目录不见了」，是整个盘符不存在。**

```
attestation 记的 backup_root   E:\quant-data
ls /e/                          No such file or directory   <- 盘符本身没有
ls /e/quant-data                No such file or directory
```

## 2. 历史 flag **不是**「现在仍有第二份副本」的证据

```
ops/SECOND_COPY_ATTESTED.flag     存在
  attested: 2026-07-29
  三方核验 all_raw_sha256_match=true，20304 <-> 20304 文件，10207 条清单条目
ops/physical_copy_attestation.json
  primary_root  C:\Users\Aaron\quant-data      <- 今天仍在
  backup_root   E:\quant-data                  <- 今天不存在
  verified_at_utc 2026-07-28T16:04:43Z
```

**那个 flag 断言的是「2026-07-28 那天验证过」，不是「此刻可达」。**
它是一条**历史事实**，而且仍然为真——真的是当时验证过。
把它读成现状，是把「曾经」当成「现在」。

**而 `assert_real_run_allowed` 只检查 flag 是否存在**，
所以那道门今天照样通过——**它测的是历史证明存在，不是副本可达**。
这一点已在 preflight §0 记过，此处是它的第二个后果。

## 3. 恢复它的最小动作

```
一  接一个**第二个物理卷**（盘符不必是 E:；工具接受任意 backup_root 参数）
二  把 C:\Users\Aaron\quant-data 整树拷过去    20304 个文件
三  跑 scripts/physical_copy_verify.py <backup_root>
    -> 产出 attestation **草稿**
四  Aaron 审阅草稿后，才由 Aaron 决定 flag 的处置
```

**第四步不是我能做的，工具也不做**：脚本头部逐字写着
「It NEVER creates ops/SECOND_COPY_ATTESTED.flag —— 最后那一下只在
Aaron 审阅 attestation 之后发生（frozen instruction: no self-certification）」。

**第二步属于你保留的第六类**（quant-data 目录/写入），我不擅自动手。

## 4. 有没有不读 Development payload 的恢复／认证方法

**有，而且现有工具就是。**

```
scripts/physical_copy_verify.py 做的全部事情
  collect(root)                 遍历、逐文件 sha256_file（分块读原始字节）
  official_manifest_hashes()    读官方 manifest.json 里记录的 sha256
  三方比对                       primary <-> 官方清单 <-> backup
```

**它从不解码 DBN，不构造 universe，不计算任何特征或标签。**
拷贝与哈希会**读到字节**，但不解释字节——**不产生任何 outcome 暴露**，
研究轴不动一格。

> 「读 Development payload」在本项目里指的是**把它当数据用**。
> 复制与校验不是那件事，正如 `_check_role` 之外的守卫也不管它。

**所以：恢复副本这件事本身，可以在 ① 被批准之前完成，且不消耗任何研究自由度。**
它是否要先做，是你的决定。

## 5. 一条建议（仅建议）

`ops/SECOND_COPY_ATTESTED.flag` 今天让 `assert_real_run_allowed` 通过，
而它证明的事情（2026-07-28 验证过）与它被当作的事情（现在有第二份副本）
**不是同一件**。

**在真正跑真实数据之前，这两者应当重新一致**——要么恢复副本并重新认证，
要么明确记录「知道当前无副本仍然继续」。

**我不替你选，也没有改动那个 flag。**
