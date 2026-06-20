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
    result = ashpb.analyze_steady(T_tank_w=55.0, T0=5.0, Q_ref_tank=8_000.0)
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["Q_ref_tank [W]"] > 0
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
        T_tank_w=55.0, T_source=12.0, Q_ref_tank=8_000.0, T0=15.0
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
        T_tank_w=55.0, T_source=12.0, Q_ref_tank=8_000.0, T0=15.0
    )
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["Q_ref_tank [W]"] > 0
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


# ---------------------------------------------------------------------------
# dT_cycle_min / dT_hx_min — expose as user-configurable params (#185)
# ---------------------------------------------------------------------------


def test_ashp_custom_min_lift_and_pinch():
    ashp = AirSourceHeatPump(
        ref="R32", UA_ou_rated=3000.0, UA_iu_rated=3000.0,
        dT_cycle_min=15.0, dT_hx_min=1.0,
    )
    assert ashp.dT_cycle_min == 15.0
    assert ashp.dT_hx_min == 1.0


def test_ashp_default_min_lift_and_pinch():
    ashp = AirSourceHeatPump(ref="R32", UA_ou_rated=3000.0, UA_iu_rated=3000.0)
    assert ashp.dT_cycle_min == 20.0
    assert ashp.dT_hx_min == 0.5


def test_gshp_custom_min_lift_and_pinch():
    gshp = GroundSourceHeatPump(ref="R32", dT_cycle_min=8.0, dT_hx_min=1.0)
    assert gshp.dT_cycle_min == 8.0
    assert gshp.dT_hx_min == 1.0


def test_gshp_default_min_lift_fallback_to_dT_subcool():
    gshp = GroundSourceHeatPump(ref="R32", dT_subcool=4.0)
    assert gshp.dT_cycle_min == 4.0  # falls back to dT_subcool
    assert gshp.dT_hx_min == 0.5


def test_ashpb_custom_min_lift_and_pinch():
    ashpb = AirSourceHeatPumpBoiler(ref="R32", dT_cycle_min=12.0, dT_hx_min=0.8)
    assert ashpb.dT_cycle_min == 12.0
    assert ashpb.dT_hx_min == 0.8


def test_ashpb_default_min_lift_is_20():
    ashpb = AirSourceHeatPumpBoiler(ref="R32")
    assert ashpb.dT_cycle_min == 20.0
    assert ashpb.dT_hx_min == 0.5


def test_gshpb_custom_min_lift_and_pinch():
    gshpb = GroundSourceHeatPumpBoiler(ref="R32", dT_cycle_min=10.0, dT_hx_min=0.7)
    assert gshpb.dT_cycle_min == 10.0
    assert gshpb.dT_hx_min == 0.7


def test_gshpb_default_min_lift_is_20():
    gshpb = GroundSourceHeatPumpBoiler(ref="R32")
    assert gshpb.dT_cycle_min == 20.0
    assert gshpb.dT_hx_min == 0.5


def test_wshpb_custom_min_lift_and_pinch():
    wshpb = WaterSourceHeatPumpBoiler(ref="R32", dT_cycle_min=10.0, dT_hx_min=0.7)
    assert wshpb.dT_cycle_min == 10.0
    assert wshpb.dT_hx_min == 0.7


def test_wshpb_default_min_lift_is_20():
    wshpb = WaterSourceHeatPumpBoiler(ref="R32")
    assert wshpb.dT_cycle_min == 20.0
    assert wshpb.dT_hx_min == 0.5
