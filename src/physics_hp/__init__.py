"""Physics-Based Heat Pump Models — standalone package entry point.

When installed as a standalone package (``uv pip install -e .``),
import as::

    from physics_hp import AirSourceHeatPumpBoiler

When used as a git submodule of ``enex_analysis_engine``, the parent
imports directly from the submodule root (this ``src/physics_hp/``
package is NOT used in that case — it is only for standalone use).

The actual source ``.py`` files live at the submodule root
(``heat_pumps/*.py``), not inside this directory.  We add the submodule
root to ``sys.path`` so that all absolute imports resolve correctly.
"""

import os
import sys

# Add the submodule root (where the .py source files live) to sys.path
_submodule_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _submodule_root not in sys.path:
    sys.path.insert(0, _submodule_root)

# Re-export everything so ``from physics_hp import X`` works
from air_source_heat_pump import AirSourceHeatPump  # noqa: E402, F401
from air_source_heat_pump_boiler import AirSourceHeatPumpBoiler  # noqa: E402, F401
from ashpb_pv_ess import ASHPB_PV_ESS  # noqa: E402, F401
from ashpb_stc_preheat import ASHPB_STC_preheat  # noqa: E402, F401
from ashpb_stc_tank import ASHPB_STC_tank  # noqa: E402, F401
from calc_util import *  # noqa: E402, F401
from constants import *  # noqa: E402, F401
from dhw import *  # noqa: E402, F401
from dynamic_context import *  # noqa: E402, F401
from enex_functions import *  # noqa: E402, F401
from ground_source_heat_pump import GroundSourceHeatPump  # noqa: E402, F401
from ground_source_heat_pump_boiler import GroundSourceHeatPumpBoiler  # noqa: E402, F401
from gshpb_pv_ess import GSHPB_PV_ESS  # noqa: E402, F401
from gshpb_stc_preheat import GSHPB_STC_preheat  # noqa: E402, F401
from gshpb_stc_tank import GSHPB_STC_tank  # noqa: E402, F401
from heat_transfer import *  # noqa: E402, F401
from refrigerant import *  # noqa: E402, F401
from subsystems import *  # noqa: E402, F401
from thermodynamics import *  # noqa: E402, F401
from visualization import *  # noqa: E402, F401
from water_source_heat_pump_boiler import WaterSourceHeatPumpBoiler  # noqa: E402, F401
from weather import *  # noqa: E402, F401

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
