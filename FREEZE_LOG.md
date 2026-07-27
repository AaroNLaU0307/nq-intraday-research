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
| — | PROJECT_CHARTER.md | v1.2-r2 | （Commit B 时填写） | — | 待 Aaron 复核 |
| — | STUDY_0_PREREGISTRATION.md | v0.2 | （Commit B 时填写） | — | 待 Aaron 复核 |
| — | purchase_plan.yaml | PP-2026-07-27-A rev2 | （Commit C 时填写） | — | 待冻结后批准 |

## IV_ACCESS_LOG（Internal Validation 访问台账）

```yaml
预算: 1 次（总额）
预定用途: 完全冻结后的 H1 首次内部验证
Study 0: 不得访问
规则: IV 验证失败 = 假设死亡（转入知识库），不是迭代燃料；
      任何额外访问需求必须以预注册增补形式申请，并声明独立性已退化
```

| # | 日期 | 假设 | 目的 | 结论 | 剩余预算 |
|---|---|---|---|---|---|
| — | — | — | — | — | 1 |
