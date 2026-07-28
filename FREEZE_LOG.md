# FREEZE LOG — 冻结登记簿

## 两阶段冻结流程（消除自引用循环）

1. **Freeze Commit A**：仅包含被冻结文档本身（PROJECT_CHARTER.md、STUDY_0_PREREGISTRATION.md）；
   打 annotated tag（如 `s0-freeze-v1`）。
2. **Registry Commit B**：计算 Commit A 内目标文件的 SHA-256，连同 Commit A 的 hash
   写入本文件后提交。**冻结锚定对象是 Commit A，不是 Commit B。**
3. **Purchase Approval Commit C**：Aaron 填写 purchase_plan.yaml 批准字段
   （含 approved_*_sha256）后单独提交。执行脚本核对哈希一致方可运行。

冻结后正文不可编辑；变更以增补条目（S0.x、Charter v1.3…）追加。
参数更新（如 platform_fee 由规则引擎快照替换占位值）须在此登记，注明"参数更新"。

## 冻结登记表

| 日期 | 文件 | 版本 | SHA-256 | Freeze Commit A | 备注 |
|---|---|---|---|---|---|
| 2026-07-27 | PROJECT_CHARTER.md | v1.2-r2 | 5176320fb54a30e5e5dcc7f1ee96b828e7d38f727a573e8bd152ca3ff4299327 | 89e2505928342d131c8f6eff93369bcc46f909b4 | FROZEN（tag s0-freeze-v1） |
| 2026-07-27 | STUDY_0_PREREGISTRATION.md | v0.6 | 6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132 | 89e2505928342d131c8f6eff93369bcc46f909b4 | FROZEN（tag s0-freeze-v1） |
| 2026-07-27 | purchase_plan.yaml | PP-2026-07-27-A rev4 | 02edbc2cb8481089ecf7b30156fd86eb3cf524112e3f97d253f94acc60c39e6c | 89e2505928342d131c8f6eff93369bcc46f909b4 | FROZEN（tag s0-freeze-v1）；批准记录另见 purchase_approval.yaml |
| 2026-07-28 | MC_METHOD_SPEC.md | v0.6 | a6de4a286eaff5ab7487298593f590cbee845afa1939ad4ea675ec219cf29608 | 5d1ec10 (tag mc-freeze-v1) | FROZEN；GPT 最终机械确认后批准 |
| 2026-07-28 | gate1/platform_params.yaml | v0.6 | 65bfdd9e90ba891fac9cde0389387255ea0a10225b23f8a5aead75d5b8a19740 | 5d1ec10 (tag mc-freeze-v1) | FROZEN |
| 2026-07-28 | gate1/evidence_registry.yaml | — | c14d576ba2076f8f08cb4f8bef16fc5a99c881071baed303f9d8a73964a6b35c | 5d1ec10 (tag mc-freeze-v1) | FROZEN（证据 bundle） |
| 2026-07-28 | gate1/snapshots/2026-07-28/snapshot_manifest_v5.json | v5 | 5b6083b5ee61db9c44b119fae3bfdb2c0c039b9c53f5d7c67a74c69f6d4e0434 | 5d1ec10 (tag mc-freeze-v1) | FROZEN（证据 bundle） |
| 2026-07-28 | gate1/G9_EVIDENCE_RESOLUTION.md | MC1.1-G9 | 2aa7e146f38f582504619ca9dc2ad9fb425fef07b61fb3d2d26e9f0cdf48b1ac | f932714 | Evidence Resolution Addendum：CME $0.35/side VERIFIED（Case A，Primary 不变，仅解除 G9） |
| 2026-07-28 | gate1/platform_params.yaml | v0.6+MC1.1 | 702b983baba88d833ebf7122d358beaf9feb946c99c2e85aad41ecee2863d9ff | f932714 | PROVISIONAL→VERIFIED、hard_run_blocker→false；at-freeze 版本 65bfdd9e… 仍锚定于 mc-freeze-v1 |
| 2026-07-28 | gate1/evidence_registry.yaml | +CME 证据 | 8ec318088ebedc9a3e3ce65bedf743b8a7741bfaa97481e841dc1802cb66a198 | f932714 | 追加 CME PDF/XLS＋addendum 文档条目；at-freeze 版本 c14d576b… 仍锚定于 mc-freeze-v1 |
| — | purchase_approval.yaml | — | （Commit C 时填写） | 不适用 | Aaron 批准时提交 |

哈希计算方法：对 Commit A（89e2505）的 git blob 做字节级 SHA-256（python hashlib，
subprocess 捕获 `git cat-file blob` 原始字节），并与工作区 Get-FileHash 交叉验证一致
（`.gitattributes * -text` 保证两者字节相同）。机械检查：Commit A 变更集仅触及三份
冻结文件（status 翻转）；purchase_approval.yaml 未进入 Commit A。

## IV_ACCESS_LOG（Internal Validation 访问台账）

```yaml
预算: 1 次（总额）
预定用途: 完全冻结后的 H1 首次内部验证
Study 0: 不得访问
数据状态: IV 段现在不采购、不存在于本机；H1 冻结 commit 后按 A3 独立批准采购
规则: IV 验证失败 = 假设死亡（转入知识库），不是迭代燃料；
      任何额外访问需求必须以预注册增补形式申请，并声明独立性已退化
无效运行判定:
  - 运行在任何结果产生前因纯技术错误中止 → 不消耗 IV 访问
  - 任何 IV 结果/统计/图表已生成或被查看后才发现实现或数据错误 →
    该次访问计入预算，IV 视为已污染；不得用修复后的 IV 迭代 H1；
    下一次独立确认只能使用 Physical Lockbox 或新市场数据
```

## 判决封存顺序（Checkpoint 0，v0.5 修正依赖顺序）

```
冻结 S0 规范与采购计划（Commit A，tag s0-freeze-v1；含 .gitattributes 随同提交）
→ 冻结 Gate 1 官方规则/费率快照
→ 冻结引用这些快照 hash 的 MC_METHOD_SPEC（tag mc-freeze-v1）
→ 运行 S0 与 MC
→ 合并判决
MC_METHOD_SPEC 冻结前，禁止运行产出任何可读的 S0 数字报告。
```

| # | 日期 | 假设 | 目的 | 结论 | 剩余预算 |
|---|---|---|---|---|---|
| — | — | — | — | — | 1 |
