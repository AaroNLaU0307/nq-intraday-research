"""Frozen data-role enum and role time windows (main-agent-authored interface;
M4-T2 / SA-2 implementation — this file's contract must not be altered by any
subagent; any perceived need to do so is a STOP CONDITION, not a judgment call).

Frozen citations for every value below (Level 1/2 evidence; do not re-derive):

  - STUDY_0_PREREGISTRATION.md (S0 v0.6, FROZEN, tag s0-freeze-v1), 行 24-26,
    数据角色表:
      Development                | NQ.v.0 ohlcv-1m  | 2010-06-06 -> 2022-01-01(excl)
      Internal Validation (IV)   | NQ.v.0 ohlcv-1m  | 2022-01-01 -> 2025-07-01(excl)
        -- "现在不采购、不存在于本机"；S0 全程不得访问。
      Execution Cost Calibration | MNQ.v.0 bbo-1s   | 2025-01-01 -> 2025-04-01(excl)

  - purchase_plan.yaml (PP-2026-07-27-A rev4, frozen_pending_approval):
      item A1  data_role: development_signal            start 2010-06-06  end 2022-01-01 (exclusive)
      item A2  data_role: execution_cost_calibration     start 2025-01-01  end 2025-04-01 (exclusive)
      future_items_not_in_this_approval item A3
               data_role: internal_validation_signal     2022-01-01 -> 2025-07-01
               status: not_approved_in_current_plan ("此前 IV 数据不得存在于本机")

  - PROJECT_CHARTER.md 冻结条款 14 (数据角色隔离): Development / Internal
    Validation / Execution Cost Calibration / Physical Lockbox 必须具有独立
    目录、读取边界和用途；成本校准数据不得用于 Alpha 特征或收益分析。

INTERNAL_VALIDATION_SIGNAL 故意不在 ROLE_WINDOWS 内: that data role is not
purchased, does not exist on this machine, and S0 must never access it. Any
loader code path that would need its window must fail closed as RoleError
(a deliberate, named exception), never leak a bare KeyError that could be
mistaken for an ordinary lookup bug.
"""
from __future__ import annotations

from enum import Enum


class DataRole(str, Enum):
    DEVELOPMENT_SIGNAL = "development_signal"
    EXECUTION_COST_CALIBRATION = "execution_cost_calibration"
    INTERNAL_VALIDATION_SIGNAL = "internal_validation_signal"  # 永不可加载


ROLE_WINDOWS = {  # (start_inclusive, end_exclusive) — ISO 日期字符串
    DataRole.DEVELOPMENT_SIGNAL: ("2010-06-06", "2022-01-01"),
    DataRole.EXECUTION_COST_CALIBRATION: ("2025-01-01", "2025-04-01"),
}
# INTERNAL_VALIDATION_SIGNAL 故意不在 ROLE_WINDOWS：任何加载尝试必须
# 在窗口查询处直接 RoleError（fail-closed，而非 KeyError 泄漏）。
