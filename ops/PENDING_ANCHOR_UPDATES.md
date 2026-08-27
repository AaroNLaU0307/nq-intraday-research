> **已并入，2026-08-25。** 下列五项已全部写进
> `MC_TO_STRATEGY_MASTER_PLAN.md`（已隔离，见 ops/OUTCOME_CARRYING_ARTIFACTS.json；不得打开） §15.1。本文件保留为历史记录，
> **不要再并入一次**；解冻条件（登记表清空）当时已满足。

# 待并入主计划恢复锚的内容（§15）

```
WHY_PENDING=MC_TO_STRATEGY_MASTER_PLAN.md（已隔离，见 ops/OUTCOME_CARRYING_ARTIFACTS.json；不得打开） 目前登记在
            ops/ARTIFACTS_UNDER_REVIEW.json，审查期间不可改动。
UNFREEZE_WHEN=Sol 的委托裁定返回，条目从登记表移除之后。
```

审查一返回就要写进 §15 的：

1. **INC-TRANSPORT-20260824** —— 交付中的工件被 builder 改动导致一次委托裁定
   作废；处置与新增的机械守卫见
   `ops/INCIDENT_TRANSPORTED_ARTIFACT_MUTATED_20260824.md`。
2. **N16 单位成本实测** —— `ops/MC_COST_PROBE_FINDINGS.md`：
   0.0114 sec/path @504 天；一次 BE（16 Primary cell）1.1 h；18 BE = 19 h；
   ＋θ0.3 通道 ×2 ≈ 1.6 天。**custody（15–42 h）比模拟（19 h）还贵。**
   §14.4 里「总时长给不出小时数」那句可以更新，但**下界性质与 E3 的必要性不变**。
3. **F1/F2 定性收窄** —— 全伪造 (prepared, authority) 对**被接受**，但
   `bundle_table_digest` 不在 sealed binding 键集内，谎言到不了字节。
   故为**验证违规而非封存违规**：`verify_supplement_authority` 可被自洽虚构满足。
   钉在 `tests/test_mc_supplement_coercion_census.py`。
4. **强制转换登记表** —— `tests/test_mc_supplement_coercion_census.py` 用 AST
   登记摘要／身份派生函数内的每一处 `str()`/`int()`；每条 KNOWN 条目都写明
   其防御是**顺序性的而非构造性的**。
5. **测试地板** 3980 → 3985。
