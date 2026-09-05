＃ Owner 裁定 —— 2026-09-06

```
DECIDER=Aaron（本人）
DELEGATED=NO
RECORDED_BY=fresh fable verifier（本轮 MC-DS-S001 P5 独立验证席位），逐字转录他的原话；provenance 为本席位所记，标明
```

---

## OD-1 MC-DS-S001 F3 retirement

### 原话

> 我现在正式作出并授权记录以下 Aaron owner decision：
>
> OD-1 — MC-DS-S001 F3 retirement
>
> DECIDER = Aaron
> DELEGATED = NO
>
> 我裁定：
>
> - supersedes_event_sequence = 22
> - superseded_supplement_id = MC-DS-S001
> - superseded_commit = 3df1656f105b9314235bd28957336a7dec4bde05
> - reason_code = POST_START_FAILURE
> - incident_id = INC-96578a2997e9
> - successor_supplement_id = NONE
>
> 依据：
> seq 22 `SUPPLEMENT_VERIFICATION_FAILED` 已由 fresh independent verifier
> 确认 `headline_replay_identity = FAIL`，因此当前 supplement 必须退休。
>
> 我确认：
> - MC-DS-S001 ID_REUSE = FORBIDDEN；
> - 当前没有注册 successor supplement；
> - 不创建 MC-DS-S002；
> - 不开始 T1；
> - 不修改或删除 sealed supplement；
> - 不修改或删除 archive；
> - 不修改 verifier attestation；
> - 不开始 N10/N11。

### 修正原话（Aaron，2026-09-06，同日；只改 successor 一项）

> 根据你刚刚机械测出的不可逆 parser 语义，我修正 OD-1 中唯一一项 owner ruling：
> `successor_supplement_id = MC-DS-S002`
> 不再使用 `NONE`。
> 理由：
> 本次 retirement 的后续计划是让修正后的 supplement 作为 `MC-DS-S001` 的正式 successor，通过现有 T1 路径登记 lineage，而不是创建一个与 S001 无正式关系的 fresh P1。
> 我明确接受该选择的合同后果：
>
> * `MC-DS-S001` 在 F3 后永久 retired，ID reuse forbidden；
> * `MC-DS-S002` 被 F3 预先绑定为唯一 successor；
> * 后续必须通过 T1 将 `MC-DS-S002` 注册为 S001 的 successor；
> * `MC-DS-S002` 不允许绕过 T1 直接使用 fresh P1；
> * 当前这一步只绑定 successor id，不执行 T1、不修改 S002 代码、不开始 repair。

Aaron 接受该选择会要求后续使用 T1 注册 MC-DS-S002，且禁止 MC-DS-S002 以 fresh P1 绕过 successor lineage。

机械依据（本席位实测，memory-only）：parser 要求 T1 的 predecessor F3 必须点名该 T1 的 id；
F3 写 `NONE` 则日后任何 `T1(MC-DS-S002, predecessor=MC-DS-S001)` 被拒（`t1_predecessor_f3_names_other_successor`），
而 F3 行终态且不可修正；F3 写 `MC-DS-S002` 则 T1 被接受、fresh P1(MC-DS-S002) 被拒（`f3_successor_not_registered_by_t1`）。

### 裁定

```
EVENT                      F3  SUPPLEMENT_SUPERSEDED（NUMBERED，seq 23）
supersedes_event_sequence  22
superseded_supplement_id   MC-DS-S001
superseded_commit          3df1656f105b9314235bd28957336a7dec4bde05   （绑定 seq 22 行的 commit 列）
reason_code                POST_START_FAILURE
incident_id                INC-96578a2997e9
successor_supplement_id    MC-DS-S002   （同日修正；原裁定 NONE，见「修正原话」）
ACTOR                      main agent（Aaron 批复 OWNER_DECISIONS_2026-09-06.md OD-1）
COMMIT 列                  追加时的 framework HEAD（40-hex；本文件提交后重新取得）
ID_REUSE                   FORBIDDEN —— MC-DS-S001 永久报废；MC-DS-S002 由本 F3 预先绑定为唯一 successor，后续必须经 T1 登记 lineage 并重走完整 P2；禁止以 fresh P1 绕过
NOT_DONE_BY_THIS_DECISION  本步只绑定 successor id；不执行 T1；不修改 S002 代码；不开始 repair；不改动 sealed supplement / archive / verifier attestation；不开始 N10/N11
```

### Provenance（本席位所记）

```
触发事件      registry seq 22  SUPPLEMENT_VERIFICATION_FAILED（2026-09-05T18:06:16+00:00，actor fresh fable verifier）
              failure_code headline_replay_mismatch；sealed artifact NOT deleted；supersession required
registry      C:\Users\Aaron\quant-data\itsf-registry  ops/TRIAL_REGISTRY.md
              sha256 0a52352c1c2bb0978e0f5107630274c7617457b3a7efb5810883a5cce6598ffb（11031 bytes，48 行，28 事件）
              repo HEAD 78a2586c3f073d73ff349ed3c0e2351ecff4db6e
witness       registry-witness/itsf/WITNESS_F2V_APPENDED_2026-09-05.json
              sha256 36bf855a2e3c718463b4c68192e80a83107bf47a6d8b8b580c785a69fe60c126
attestation   ops/P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md
              sha256 cc733337ed4fb39c994e11f188f49f20e2239870bbb0d82e645bc974d1c8053a
sealed        DAY_STRATA_SUPPLEMENT.json（MC-DS-S001_20260905T170810Z）
              sha256 f2ecbb9c77d3f2d7d2b555f50cadb6bcafdc979bdcfa4ac5a985e3cf33b9a911；archive 副本字节相同
incident_id   itsf.s0.runner.make_incident_id 生成，parts（"|" 连接）：
              MC-DS-S001 | F3 | SUPPLEMENT_SUPERSEDED | supersedes_event_sequence=22 |
              SUPPLEMENT_VERIFICATION_FAILED | headline_replay_mismatch |
              registry_sha256_after_f2v=0a52352c1c2bb0978e0f5107630274c7617457b3a7efb5810883a5cce6598ffb
preflight     ops/F3_PREFLIGHT_MC_DS_S001_2026-09-06.json（memory-only，0 problems；以本文件提交后的 HEAD 重跑一次）
```

本文件只记录 Aaron 的裁定与其 provenance；不构成对 seq 23 的追加，追加由 Aaron 最终签署。
