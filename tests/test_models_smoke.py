"""Smoke tests — exercise each public model's analyze_steady() once.

These tests catch wide classes of regressions (NameError, AttributeError,
KeyError, sign convention flips) that the pure-import tests cannot.
They use single representative operating points; they are not validation
against external data.
"""

from physics_hp import (
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


def test_gshpb_analyze_steady():
    gshpb = GroundSourceHeatPumpBoiler(ref="R32")
    result = gshpb.analyze_steady(
        T_tank_w=55.0, T_source=12.0, Q_ref_cond=8_000.0, T0=15.0
    )
    assert isinstance(result, dict)
    assert result["E_cmp [W]"] > 0
    assert result["cop_sys [-]"] > 1.0


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


def test_ashp_heating_analyze_steady():
    # Use a UA / fan-flow combination large enough to converge — too-small UA
    # makes the inner HX optimisation bottom out and return off-mode.
    ashp = AirSourceHeatPump(
        ref="R32",
        UA_evap_design=3000.0,
        UA_cond_design=3000.0,
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
