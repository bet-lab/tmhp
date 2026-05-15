"""Physics-Based Heat Pump Models (physics_hp).

A standalone Python library providing first-principles physics-based models
for air-source, ground-source, and water-source heat pump systems.

When installed as a standalone package (``pip install physics-hp-models``),
import as::

    from physics_hp import AirSourceHeatPumpBoiler

When used as a git submodule of ``enex_analysis_engine``, the parent package
imports directly from the submodule root (backward-compatible path).

Modules
-------
- :mod:`physics_hp.air_source_heat_pump_boiler` — Dynamic ASHPB model
- :mod:`physics_hp.ground_source_heat_pump_boiler` — Dynamic GSHPB model
- :mod:`physics_hp.water_source_heat_pump_boiler` — WSHPB model
- :mod:`physics_hp.refrigerant` — Thermodynamic refrigerant state functions
- :mod:`physics_hp.thermodynamics` — Cycle analysis utilities
- :mod:`physics_hp.heat_transfer` — ε-NTU heat exchanger methods
"""

import sys
import os

# Allow importing the flat-layout modules from the repo root.
# When installed via pyproject.toml with packages=["src/physics_hp"],
# this file lives at <root>/src/physics_hp/__init__.py.
# The actual source files live at <root>/ (repo root = submodule root).
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from air_source_heat_pump import AirSourceHeatPump  # noqa: E402
from air_source_heat_pump_boiler import AirSourceHeatPumpBoiler  # noqa: E402
from ashpb_pv_ess import ASHPB_PV_ESS  # noqa: E402
from ashpb_stc_preheat import ASHPB_STC_preheat  # noqa: E402
from ashpb_stc_tank import ASHPB_STC_tank  # noqa: E402
from calc_util import *  # noqa: F401, E402
from constants import *  # noqa: F401, E402
from dhw import *  # noqa: F401, E402
from dynamic_context import *  # noqa: F401, E402
from enex_functions import *  # noqa: F401, E402
from ground_source_heat_pump import GroundSourceHeatPump  # noqa: E402
from ground_source_heat_pump_boiler import GroundSourceHeatPumpBoiler  # noqa: E402
from gshpb_pv_ess import GSHPB_PV_ESS  # noqa: E402
from gshpb_stc_preheat import GSHPB_STC_preheat  # noqa: E402
from gshpb_stc_tank import GSHPB_STC_tank  # noqa: E402
from heat_transfer import *  # noqa: F401, E402
from refrigerant import *  # noqa: F401, E402
from subsystems import *  # noqa: F401, E402
from thermodynamics import *  # noqa: F401, E402
from visualization import *  # noqa: F401, E402
from water_source_heat_pump_boiler import WaterSourceHeatPumpBoiler  # noqa: E402
from weather import *  # noqa: F401, E402

__all__ = [
    "AirSourceHeatPump",
    "AirSourceHeatPumpBoiler",
    "ASHPB_PV_ESS",
    "ASHPB_STC_preheat",
    "ASHPB_STC_tank",
    "GroundSourceHeatPump",
    "GroundSourceHeatPumpBoiler",
    "GSHPB_PV_ESS",
    "GSHPB_STC_preheat",
    "GSHPB_STC_tank",
    "WaterSourceHeatPumpBoiler",
]
