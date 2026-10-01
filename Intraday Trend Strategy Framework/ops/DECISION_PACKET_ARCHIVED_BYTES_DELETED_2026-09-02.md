＃ 最小决策包 —— `archived_bytes_deleted` 的合法处理

```ini
PACKET_TYPE=DECISION_ANALYSIS（outcome-clean；不含任何揭盲结果、绩效值或曝光计数）
REVIEW_ID=DECISION-ARCHIVED-BYTES-DELETED-001
DELIVERY_STATUS=RETURNED
COMPANION=ops/NEXT_HANDOFF.md（禁读清单载体，必须同行）
PREPARED_BY=Opus 5，builder seat
FOR=fresh 独立席位 —— **分析并建议**
DECIDED_BY=Aaron
```

---

## 0. 受审集 —— **先逐字节核对，再开工**

对下表每一行重算 sha256 并比对。**不符即 STOP 并报告。**
聊天里贴过来的字节永远不是真相来源；请从磁盘读。

| sha256 | bytes | 路径 | 角色 |
|---|---|---|---|
| `284af0a8baa995b895a2d631fd1dd046e997bf1873e3f7466a753cd84ee0b14e` | `15728` | `src/itsf/mc/supplement_chain.py` | reference |
| `bda85429e1aab979ce033d4aafae04241b935514452e58d49e4b534c2a519e54` | `33867` | `src/itsf/mc/supplement_contract.py` | reference |
| `43b09701513930263e44378259f389662525eb44f79ded66921468bd7d99dd76` | `55502` | `src/itsf/mc/supplement_runner.py` | reference |

本包自身的 sha256 记录在 `ops/ARTIFACTS_UNDER_REVIEW.json`
（一份文档无法钉住自己的哈希）。

## 0. 席位做什么，不做什么

**席位分析并给建议；裁定归 Aaron。**

理由有二，且都是 Aaron 自己的规矩：**席位可顾问不可代签**；而本题的出路之一是
**修改一个已批准的封闭枚举（R4 级动作）**，那更不是席位能定的。

**上一次这条被 builder 自裁（BD-5）并且裁错了。** 教训不是「该交给席位裁」，
而是「该给席位看、由 Aaron 裁」。

**本包不授权写入、不授权执行、不授权创建任何目录。**
**不得读取任何 outcome-carrying 件**（清单见 `ops/OUTCOME_CARRYING_ARTIFACTS.json`），
**不得读取任何 Development payload**。

## 1. 现象（机械描述，无结果内容）

```
run_c_build_3 在归档尝试之后做两条重算：
  (a) 本地 seal 不可变    重算 sha256 == 封存时记录值
  (b) 无任何已归档字节被删除
archived_bytes_deleted = (a) 成立、(b) 不成立
  —— 本次的 seal 活着，而**更早**已在归档里的字节没了
```

**为什么这个组合可达：** `archive_sealed_run` 只校验它**刚做的那份拷贝**，
从不看更早归档的字节。所以它的报告可以是 `archive_ok`，而 (b) 同时被违反。

## 2. 已批状态机的约束（全部机械读出，未加解释）

```
P3 的后继        P4 · A1 · F2 · CR1        （四个）
P4 -> F2v, P5    A1 -> A2, AX              F2 -> F3      CR1 -> F3
终态             P5（成功） · F3（失败）
非终态陷阱       A1 · AX · CR1

Policy A         P4_SUPPLEMENT_SEALED_REQUIRES = local_seal_ok AND archive_ok
ARCHIVE_CODES    inventory_unavailable · file_unreadable · file_digest_mismatch
                 set_equality_refused · set_equality_unreached      （封闭，5 个）

必填字段
  A1   supplement_id · local_seal_sha256 · archive_code · incident_id
       local_seal_immutable · archive_root_attempted
  F2   supplement_id · stage · error_class · incident_id
       residue_path · residue_preserved
  CR1  supplement_id · dangling_event · incident_id · crash_evidence_summary
       recovery_authorization_doc · registry_intact_verification
       registry_witness_ref
  A2   supplement_id · recovery_authorization_doc
       source_and_archive_exact_inventory_match · per_file_sha256_match
       n_files · local_seal_sha256_unchanged · incident_id
```

## 3. 四个后继逐一对照

| 后继 | 字段可填？ | 语义是否成立 | 备注 |
|---|---|---|---|
| **P4** | 可填 | **否** | Policy A 要 `archive_ok`，而 (b) 刚被违反 |
| **A1** | **否** | 近 | `archive_code` 必填，而本码不在 5 个之内 —— **行写不出来** |
| **F2** | 可填 | **存疑** | 六个字段都填得出，但 F2 是「supplement run 失败」，而本次 **seal 成功了** |
| **CR1** | **否** | 否 | 要 `crash_evidence_summary` 与 `dangling_event`，**并没有崩溃** |

## 4. 可选方案与影响

```
O1  判 F2 -> F3（终态失败）
    可行     六个字段都可填
    代价     把一次**成功的封存**记成失败的 run。seal 是真的、可验证的，
             而 F3 之后是 T1；这条路把有效证据丢在一个失败终态里

O2  判 A1，并**扩充 ARCHIVE_CODES** 新增一个码
    可行     需要修改**已批准的封闭枚举** —— R4 级动作，非 builder、非席位
    语义     最贴近：归档侧确实不 ok，而本地 seal 确实活着
    遗留     即便如此，A1 的唯一出口 A2 只断言**本次 run 拷贝**的一致性
             （inventory match / per-file sha256 / local seal unchanged）
             —— **它治不了「更早归档的字节被删」**，所以 A1 会成为一个
                没有出口的陷阱，除非 A2 也一并修订

O3  判 CR1
    不可行   无崩溃、无 dangling_event，两个必填字段只能靠编造

O4  维持现状：具名拒绝，不落任何终态（今日代码即此）
    可行     fail-closed，不新增任何隐含语义
    **但它不是中性的**：P3 已经落地而没有后继，
    登记链上留下一个 **dangling P3**。而 CR1 的存在理由正是解决
    `dangling_event` —— 它需要 Aaron 的 `recovery_authorization_doc`。
    换言之，O4 把问题推给一次**人工的 CR1**，而不是消掉问题
```

## 5. 请席位回答

```
Q1  §3 的对照有没有错？特别是 F2 的「语义存疑」——把一次成功封存记成失败 run，
    是不是比我写的更可接受、或更不可接受？
Q2  O2 的遗留是否致命：A1 无出口，是否意味着 O2 必须与 A2 的修订绑定？
Q3  O4 的 dangling P3 会带来什么我没看到的后果？
Q4  有没有第五个我没列出的合法处理方式？
Q5  在裁定落地之前，维持 O4（fail-closed）是否安全？
```

**请给建议与理由，不要给裁定。** Critical/High 放最前，
并区分「你复现的事实」与「本包自述的内容」。

## 6. 复现命令（只读）

```
python -m pytest tests/test_mc_supplement_runner.py -q
python -m pytest tests/test_supplement_chain.py -q
python -c "from itsf.mc import supplement_contract as sc; print(sc.ARCHIVE_CODES)"
```

## 7. 背景（可读，均 outcome-clean）

```
ops/REVIEW_RESULT_ENG_SAFETY_2026-09-02.md   §2 M2 —— 反驳 BD-5 的那三条
ops/BUILDER_DECISIONS_2026-09-02.md          BD-5 原文与收回横幅
ops/REPAIR_ENG_SAFETY_HOLD_2026-09-02.md     §5 为什么这条没修
```
