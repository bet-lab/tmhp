"""Smoke tests — verify that core classes can be imported and instantiated."""

import sys
import os

# Add repo root to path (flat-layout: source files live at src/physics_hp)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


def test_import_ashpb():
    from physics_hp.air_source_heat_pump_boiler import AirSourceHeatPumpBoiler
    assert AirSourceHeatPumpBoiler is not None


def test_import_gshpb():
    from physics_hp.ground_source_heat_pump_boiler import GroundSourceHeatPumpBoiler
    assert GroundSourceHeatPumpBoiler is not None


def test_calc_util_constants():
    from physics_hp.calc_util import C2K, K2C, W2kW
    assert C2K(0) == 273.15
    assert K2C(273.15) == 0.0
    assert W2kW(1000) == 1.0
