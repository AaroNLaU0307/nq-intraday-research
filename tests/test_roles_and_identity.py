"""TASKS 14 and 15 -- the data-role boundary and prospective run identity."""
from __future__ import annotations

import pytest

from r1.errors import AuthorityError, RoleError, SealIdentityError
from r1.roles import (FORBIDDEN_ROLES, R1_AUTHORIZED_ROLES, DataRole,
                      check_role, resolve_window)
from r1.run_identity import (assert_event_set_frozen, build_run_identity,
                             environment_identity)


# ---------------------------------------------------------------- roles
def test_only_development_signal_and_cost_calibration_are_authorized():
    assert R1_AUTHORIZED_ROLES == {DataRole.DEVELOPMENT_SIGNAL,
                                   DataRole.EXECUTION_COST_CALIBRATION}
    assert FORBIDDEN_ROLES == {DataRole.INTERNAL_VALIDATION_SIGNAL,
                               DataRole.PHYSICAL_LOCKBOX}


def test_development_window_matches_the_sealed_grant():
    assert resolve_window(DataRole.DEVELOPMENT_SIGNAL) == ("2010-06-06",
                                                           "2022-01-01")


def test_internal_validation_is_refused_with_the_reason():
    with pytest.raises(RoleError, match="NOT GRANTED"):
        check_role(DataRole.INTERNAL_VALIDATION_SIGNAL)
    with pytest.raises(RoleError, match="hypothesis death"):
        resolve_window("internal_validation_signal")


def test_lockbox_is_refused():
    with pytest.raises(RoleError):
        check_role(DataRole.PHYSICAL_LOCKBOX)


def test_unknown_role_fails_closed():
    with pytest.raises(RoleError, match="unknown data role"):
        check_role("final_evaluation")
    with pytest.raises(RoleError):
        check_role("")


def test_forbidden_roles_have_no_window_entry():
    from r1.roles import ROLE_WINDOWS
    for role in FORBIDDEN_ROLES:
        assert role not in ROLE_WINDOWS


# ---------------------------------------------------------------- identity
def _identity(contract, **kw):
    base = dict(run_label="synthetic-s2", code_commit="0" * 40,
                data_manifest_sha256="1" * 64, event_universe_digest="2" * 64)
    base.update(kw)
    return build_run_identity(contract, **base)


def test_run_identity_binds_everything_required(contract):
    ident = _identity(contract)
    p = ident.payload()
    for field in ("content_commit", "seal_attestation_commit", "prereg_sha256",
                  "manifest_sha256", "event_calendar_sha256",
                  "data_manifest_sha256", "event_universe_digest",
                  "code_commit", "environment", "cost_scenarios",
                  "bootstrap_seeds", "trial_registry_sha256",
                  "sample_formal_trial_ordinal"):
        assert p[field], field
    assert p["k"] == 1
    assert p["n_structural"] == 252
    assert p["cost_scenarios"]["Base"]["round_turn_usd"] == pytest.approx(3.99)
    assert len(ident.digest()) == 64


def test_identity_is_not_a_real_run_without_authorization(contract):
    assert _identity(contract).is_real_run is False
    assert _identity(contract).trial_consumed is False
    real = _identity(contract,
                     s3_authorization="S3_RUN_AUTHORIZED_BY_AARON:2026-xx")
    assert real.is_real_run is True
    assert real.trial_consumed is False       # consumed at RUN_STARTED, not here


def test_malformed_authorization_is_refused(contract):
    with pytest.raises(AuthorityError, match="malformed"):
        _identity(contract, s3_authorization="nope")


def test_digest_changes_when_any_bound_field_changes(contract):
    a = _identity(contract).digest()
    b = _identity(contract, code_commit="f" * 40).digest()
    c = _identity(contract, event_universe_digest="3" * 64).digest()
    assert len({a, b, c}) == 3


def test_l6_binding_refuses_a_moved_event_set(contract):
    ident = _identity(contract)
    assert_event_set_frozen(ident, "2" * 64)
    with pytest.raises(SealIdentityError, match="outcome-dependent"):
        assert_event_set_frozen(ident, "9" * 64)


def test_environment_identity_is_recorded():
    env = environment_identity()
    assert env["python"] and env["platform"]
    assert "numpy" in env
