# `archive/` —— 历史治理件

移到这里的**只有一类文件**：经机械扫描确认**全仓 511 个受版本控制文件中无人
引用**的历史件。它们没有被删除，`git mv` 保留了完整历史。

```
MOVED   2026-08-26
FROM    仓库根
METHOD  对全部 511 个受控文本文件做逐名检索，零命中才移动
```

**判据是「无人引用」，不是「看起来旧」。** 同一批候选里原本有三份
（`DECISION_PACKET_F4_NAN_VOLUME.md`、`DECISION_PACKET_L82_DEFINITION.md`、
`DECISION_PACKET_Y123_NONDIRECTIONAL.md`）也像是历史件，但扫描发现
`ops/M5_RUNNER_TASKBOARD/SA6_AUDIT_FINDINGS.md` 仍在引用它们——**留在原处未动**。
第一次窄扫描（只看 py/md/json/yaml）漏掉了那个子目录；扩到全部受控文件才抓到。

## 移动了什么

| 文件 | 是什么 |
|---|---|
| `CODEX_REVIEW_PACKET_M6.md` · `_M6_1.md` · `_M6_1_1.md` · `_M6_1_2.md` | M6 阶段的 Codex 复审包。**注意：`M6_1_4/6/7/8` 与 `S0_CLOSEOUT_FINAL` 仍被引用，留在仓根** |
| `DECISION_PACKET_PREFLIGHT_D7_PREV_RTH_CLOSE.md` | preflight D7 决策包 |
| `DECISION_PACKET_PREFLIGHT_F10_MULTIEVENT_SCOPE.md` | preflight F10 多事件范围 |
| `DECISION_PACKET_RUNTIME_SELFBLOCK.md` | runtime 自锁决策包 |
| `DECISION_PACKET_VENDOR_DEGRADED_ANCHOR.md` | vendor 降级锚决策包 |
| `HANDOFF_TO_CODEX.md` | 早期的「统一项目交接入口」。**已被 `ops/MC_TO_STRATEGY_MASTER_PLAN.md` 取代为唯一恢复锚**，故成为孤件 |
| `M4_FINAL_CLOSURE_REPORT.md` | M4 收口报告 |
| `ULTRACODE_EXPERIMENT_REPORT.md` | ultracode 实验报告 |

## 需要其中某份时

它们仍在版本控制内，路径只是多了 `archive/`。历史用 `git log --follow` 可以
穿过这次移动。

## 没有移动的

- `ops/` 下**一份都没动**。52 份里 47 份被引用（22 份被代码／测试／状态文件按
  路径硬引用），移动会直接弄断生产代码。`ops/` 改为建索引：见
  [`../ops/README.md`](../ops/README.md)。
- 仓根其余 37 份 `.md` 全部仍被引用或仍在现势使用。
