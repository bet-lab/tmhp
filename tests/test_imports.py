"""Smoke tests — verify that core classes can be imported and instantiated."""

import sys
import os

# Add repo root to path (flat-layout: source files live at root)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_import_ashpb():
    """AirSourceHeatPumpBoiler should be importable."""
    from air_source_heat_pump_boiler import AirSourceHeatPumpBoiler  # noqa: F401

    assert AirSourceHeatPumpBoiler is not None


def test_import_gshpb():
    """GroundSourceHeatPumpBoiler should be importable."""
    from ground_source_heat_pump_boiler import GroundSourceHeatPumpBoiler  # noqa: F401

    assert GroundSourceHeatPumpBoiler is not None


def test_import_wshpb():
    """WaterSourceHeatPumpBoiler should be importable."""
    from water_source_heat_pump_boiler import WaterSourceHeatPumpBoiler  # noqa: F401

    assert WaterSourceHeatPumpBoiler is not None


def test_calc_util_constants():
    """Unit conversion constants should be importable."""
    from calc_util import C2K, K2C, W2kW  # noqa: F401

    assert C2K(0) == 273.15
    assert K2C(273.15) == 0.0
    assert W2kW(1000) == 1.0
