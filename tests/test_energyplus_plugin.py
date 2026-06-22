"""P2 EnergyPlus Python Plugin adapter tests (#165) — PlantComponent:UserDefined.

The plugin classes import ``pyenergyplus`` (bundled in an EnergyPlus install,
not pip-installable) and a full check needs EnergyPlus running the embedded
interpreter — that end-to-end co-simulation is exercised outside CI. Here we
anchor correctness to the public ``analyze_steady()`` seam (#165 P0), which is
exactly what the plugin calls, so the contract the adapter depends on is tested
dependency-light; the plugin-class structure is checked only when
``pyenergyplus`` is importable.
"""

from __future__ import annotations

import pytest

from tmhp import AirSourceHeatPumpBoiler

# Keys the plugin reads back from analyze_steady (must stay unit-suffixed).
_REQUIRED_KEYS = ("E_cmp [W]", "Q_ref_tank [W]", "cop_ref [-]", "cop_sys [-]")
CP_WATER = 4181.0  # J/(kg·K)
TOUT_MAX_REF = 95.0  # mirror the plugin's outlet clamp; fails if it drifts


class _FakeExchange:
    def __init__(self, values):
        self.values = values
        self.actuators = {}
        self.globals = {}

    def api_data_fully_ready(self, state):
        return True

    def get_internal_variable_value(self, state, handle):
        return self.values[handle]

    def get_variable_value(self, state, handle):
        return self.values[handle]

    def set_actuator_value(self, state, handle, value):
        self.actuators[handle] = value

    def set_global_value(self, state, handle, value):
        self.globals[handle] = value

    def system_time_step(self, state):
        return 0.25


class _FakeApi:
    def __init__(self, values):
        self.exchange = _FakeExchange(values)


def _steady():
    hp = AirSourceHeatPumpBoiler(ref="R32", hp_capacity=15000.0)
    return hp.analyze_steady(T_tank_w=54.0, T0=7.0, Q_ref_tank=10000.0)


def test_analyze_steady_contract_keys():
    """The adapter reads unit-suffixed keys plus bare converged/failure_reason."""
    res = _steady()
    for k in _REQUIRED_KEYS:
        assert k in res, f"missing key {k!r}"
    for k in ("converged", "failure_reason"):
        assert k in res, f"missing bare key {k!r}"


def test_analyze_steady_converges_and_powers_in_watts():
    res = _steady()
    assert res["converged"] and res["failure_reason"] == "none"
    e_cmp = res["E_cmp [W]"]
    q = res["Q_ref_tank [W]"]
    assert 500.0 < e_cmp < 15000.0, f"E_cmp out of plausible W range: {e_cmp}"
    assert 1000.0 < q < 20000.0, f"Q out of plausible W range: {q}"


def test_plugin_derived_formulas_are_unit_consistent():
    """Reproduce the two derivations the plugin performs from analyze_steady:
    cop_ref == Q/E_cmp, and the loop outlet rise dT = Q/(mdot*cp) is a small
    °C increment (the EnergyPlus <-> tmhp boundary contract)."""
    res = _steady()
    q, e_cmp = res["Q_ref_tank [W]"], res["E_cmp [W]"]
    assert abs(res["cop_ref [-]"] - q / e_cmp) < 1e-6
    m_dot = 0.003 * 1000.0  # design loop flow [kg/s]
    dt = q / (m_dot * CP_WATER)
    assert 0.1 < dt < 10.0, f"outlet dT not a small °C rise: {dt}"
    assert 54.0 + dt < TOUT_MAX_REF


def test_surrogate_uses_usable_diagnostic_cycle_numbers(monkeypatch):
    """EnergyPlus should use positive cycle outputs even when diagnostics warn."""
    from tmhp.integrations.energyplus_plugin import (
        LOOP_DESIGN_VDOT,
        RHO_WATER,
        TmhpPlantSurrogate,
    )

    plant = TmhpPlantSurrogate()
    plant._requested = True
    plant._need = False
    plant._tally_every = 10_000
    plant.h = {
        "t_in": 1,
        "mdot": 2,
        "cp": 3,
        "load": 4,
        "t_out_act": 5,
        "mdot_act": 6,
        "t0": 7,
        "e_cmp": 8,
    }
    monkeypatch.setattr(
        plant,
        "_solve",
        lambda t_in, t0, q_target: {
            "converged": False,
            "failure_reason": "hx_not_converged",
            "Q_ref_tank [W]": 6000.0,
            "E_cmp [W]": 2000.0,
        },
    )
    plant.api = _FakeApi({1: 50.0, 2: 0.0, 3: CP_WATER, 4: 8000.0, 7: 7.0})

    assert plant.on_user_defined_component_model(object()) == 0

    ex = plant.api.exchange
    assert ex.actuators[5] > 50.0
    assert ex.actuators[6] == pytest.approx(LOOP_DESIGN_VDOT * RHO_WATER)
    assert ex.globals[8] == pytest.approx(2000.0 * 3600.0 * 0.25)


def test_surrogate_zeroes_true_off_mode_cycle_outputs(monkeypatch):
    """Off-mode placeholders must not heat the EnergyPlus loop."""
    from tmhp.integrations.energyplus_plugin import TmhpPlantSurrogate

    plant = TmhpPlantSurrogate()
    plant._requested = True
    plant._need = False
    plant._tally_every = 10_000
    plant.h = {
        "t_in": 1,
        "mdot": 2,
        "cp": 3,
        "load": 4,
        "t_out_act": 5,
        "mdot_act": 6,
        "t0": 7,
        "e_cmp": 8,
    }
    monkeypatch.setattr(
        plant,
        "_solve",
        lambda t_in, t0, q_target: {
            "converged": False,
            "failure_reason": "cycle_invalid",
            "Q_ref_tank [W]": 0.0,
            "E_cmp [W]": 0.0,
        },
    )
    plant.api = _FakeApi({1: 50.0, 2: 0.0, 3: CP_WATER, 4: 8000.0, 7: 7.0})

    assert plant.on_user_defined_component_model(object()) == 0

    ex = plant.api.exchange
    assert ex.actuators[5] == 50.0
    assert ex.globals[8] == 0.0


def test_plugin_classes_when_energyplus_available():
    """When pyenergyplus is importable, the two managers are EnergyPlusPlugins
    exposing the user-defined-component callback."""
    pytest.importorskip("pyenergyplus")
    from pyenergyplus.plugin import EnergyPlusPlugin

    from tmhp.integrations.energyplus_plugin import TmhpPlantInit, TmhpPlantSurrogate

    for cls in (TmhpPlantInit, TmhpPlantSurrogate):
        assert issubclass(cls, EnergyPlusPlugin)
        assert hasattr(cls, "on_user_defined_component_model")
