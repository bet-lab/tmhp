"""Smoke tests — exercise each public model's analyze_steady() once.

These tests catch wide classes of regressions (NameError, AttributeError,
KeyError, sign convention flips) that the pure-import tests cannot.
They use single representative operating points; they are not validation
against external data.
"""

import warnings

from tmhp import (
    AirSourceHeatPump,
    AirSourceHeatPumpBoiler,
    GroundSourceHeatPump,
    GroundSourceHeatPumpBoiler,
    WaterSourceHeatPumpBoiler,
)


def test_ashpb_analyze_steady():
    ashpb = AirSourceHeatPumpBoiler(ref="R32")
    result = ashpb.analyze_steady(T_tank_w=55.0, T0=5.0, Q_ref_cond=8_000.0)
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["Q_ref_cond [W]"] > 0
    assert result["cop_sys [-]"] > 1.0
    # failure_reason is a diagnostic, not a pass/fail gate — it may say
    # "hx_not_converged" or "optimizer_failed" even when the returned
    # numbers (E_cmp, COP) are usable. Just assert it surfaces.
    assert result["failure_reason"] in {
        "none",
        "hx_not_converged",
        "optimizer_failed",
    }


def test_gshpb_analyze_steady():
    gshpb = GroundSourceHeatPumpBoiler(ref="R32")
    result = gshpb.analyze_steady(
        T_tank_w=55.0, T_source=12.0, Q_ref_cond=8_000.0, T0=15.0
    )
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["cop_sys [-]"] > 1.0
    # failure_reason is a diagnostic, not a pass/fail gate — it may say
    # "hx_not_converged" or "optimizer_failed" even when the returned
    # numbers (E_cmp, COP) are usable. Just assert it surfaces.
    assert result["failure_reason"] in {
        "none",
        "hx_not_converged",
        "optimizer_failed",
    }


def test_wshpb_analyze_steady():
    wshpb = WaterSourceHeatPumpBoiler(ref="R32")
    result = wshpb.analyze_steady(
        T_tank_w=55.0, T_source=12.0, Q_ref_cond=8_000.0, T0=15.0
    )
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["Q_ref_cond [W]"] > 0
    assert result["cop_ref [-]"] > 1.0
    assert result["cop_sys [-]"] > 1.0
    # failure_reason is a diagnostic, not a pass/fail gate — it may say
    # "hx_not_converged" or "optimizer_failed" even when the returned
    # numbers (E_cmp, COP) are usable. Just assert it surfaces.
    assert result["failure_reason"] in {
        "none",
        "hx_not_converged",
        "optimizer_failed",
    }


def test_ashp_heating_analyze_steady():
    # Use a UA / fan-flow combination large enough to converge — too-small UA
    # makes the inner HX optimisation bottom out and return off-mode.
    ashp = AirSourceHeatPump(
        ref="R32",
        UA_iu_rated=3000.0,
        UA_ou_rated=3000.0,
        dV_iu_fan_a_design=0.8,
        dV_ou_fan_a_design=0.8,
        A_cross_iu=0.5,
        A_cross_ou=0.5,
    )
    result = ashp.analyze_steady(
        Q_r_iu=-5_000.0, T0=5.0, T_a_room=20.0, verbose=False
    )
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["cop_sys [-]"] > 1.0
    # failure_reason is a diagnostic, not a pass/fail gate — it may say
    # "hx_not_converged" or "optimizer_failed" even when the returned
    # numbers (E_cmp, COP) are usable. Just assert it surfaces.
    assert result["failure_reason"] in {
        "none",
        "hx_not_converged",
        "optimizer_failed",
    }


def test_gshp_heating_analyze_steady():
    gshp = GroundSourceHeatPump(
        ref="R32",
        UA_evap_design=2000.0,
        UA_cond_design=2000.0,
        dV_iu_fan_a_design=0.5,
        A_cross_iu=0.5,
    )
    result = gshp.analyze_steady(Q_r_iu=-3_000.0, T0=5.0, T_a_room=20.0)
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["cop_sys [-]"] > 1.0
    # failure_reason is a diagnostic, not a pass/fail gate — it may say
    # "hx_not_converged" or "optimizer_failed" even when the returned
    # numbers (E_cmp, COP) are usable. Just assert it surfaces.
    assert result["failure_reason"] in {
        "none",
        "hx_not_converged",
        "optimizer_failed",
    }


def test_ashp_off_mode_failure_reason_is_diagnostic():
    # Deliberately tiny UA so the inner HX optimisation cannot converge.
    # The model is expected to fall back to off-mode AND surface a
    # specific failure_reason so callers can branch on it.
    ashp = AirSourceHeatPump(
        ref="R32",
        UA_iu_rated=2000.0,
        UA_ou_rated=2000.0,
        dV_iu_fan_a_design=0.5,
        dV_ou_fan_a_design=0.5,
        A_cross_iu=0.5,
        A_cross_ou=0.5,
    )
    result = ashp.analyze_steady(
        Q_r_iu=-3_000.0, T0=5.0, T_a_room=20.0, verbose=False
    )
    assert isinstance(result, dict)
    assert result["mode"] == "off"
    assert result["converged"] is False
    assert result["failure_reason"] in {
        "cycle_invalid",
        "hx_not_converged",
        "optimizer_failed",
    }


def test_ashp_deprecated_params_emit_warning():
    """Deprecated UA_cond_rated/UA_evap_rated/n_cond/n_evap must emit DeprecationWarning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        AirSourceHeatPump(
            ref="R32",
            UA_cond_rated=3000.0,
            UA_evap_rated=2500.0,
            n_cond=0.6,
            n_evap=0.6,
        )
    dep_messages = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
    assert any("UA_cond_rated" in m or "UA_evap_rated" in m for m in dep_messages), (
        "Expected DeprecationWarning for UA_cond_rated/UA_evap_rated"
    )
    assert any("n_cond" in m or "n_evap" in m for m in dep_messages), (
        "Expected DeprecationWarning for n_cond/n_evap"
    )


def test_ashp_oldest_deprecated_design_params_emit_warning():
    """Two-hop compat: UA_cond_design/UA_evap_design must also emit DeprecationWarning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        AirSourceHeatPump(
            ref="R32",
            UA_cond_design=3000.0,
            UA_evap_design=2500.0,
        )
    dep_messages = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
    assert any("UA_cond_rated" in m or "UA_evap_rated" in m for m in dep_messages), (
        "Expected DeprecationWarning for two-hop UA_cond_design path"
    )
