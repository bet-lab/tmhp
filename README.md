<div align="center">

# physics-heatpump-models

**A general-purpose, physics-based heat pump modeling library**

*Refrigerant-agnostic · operating-condition-agnostic · first-principles from the cycle up*

[![Python](https://img.shields.io/badge/python-≥3.10-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Docs](https://img.shields.io/badge/docs-online-blue.svg)](https://bet-lab.github.io/physics-heatpump-models/)
[![CoolProp](https://img.shields.io/badge/powered%20by-CoolProp-orange.svg)](http://www.coolprop.org)

[**Documentation**](https://bet-lab.github.io/physics-heatpump-models/) ·
[**Repository**](https://github.com/bet-lab/physics-heatpump-models) ·
[**Sister project**](https://github.com/bet-lab/enex_analysis_engine)

</div>

---

## Overview

`physics-heatpump-models` is a Python library for simulating air-source, ground-source, and water-source heat pump systems — for domestic hot water (DHW), space heating, and space cooling.

Unlike conventional simulators that rely on manufacturer-specific curve fits, this library **solves the thermodynamic refrigerant cycle at every time step**. The result is a single, unified modeling framework that produces reasonably accurate results across a wide range of refrigerants and operating conditions, without requiring proprietary catalogue data for every new configuration.

> **In one line:** a refrigerant-agnostic, condition-agnostic heat pump model — one library, many systems.

---

## Why physics-based?

Empirical curve-fit models (typical in EnergyPlus, TRNSYS, and most BES tools) carry structural limitations:

| Curve-fit models | This library |
|---|---|
| Tied to the operating range of the original test data | Predictive across the full refrigerant envelope |
| Refrigerant is baked into the coefficients | Any CoolProp-supported refrigerant, swappable at runtime |
| Refrigerant state is hidden | Full thermodynamic state at every cycle node |
| Requires re-fitting for every new unit | One model class, parameterized by geometry & components |

The trade-off is a few extra parameters and a slightly more expensive time step — in exchange for a model you can **trust outside its calibration range**.

---

## How it works

Each time step solves a closed refrigerant cycle coupled to the surrounding system (tank, building, ground loop, etc.). The condenser duty is the target, and the evaporating temperature is found by internally minimizing compressor power, so the cycle closes physically rather than via fitted coefficients.

| Sub-model | Method |
|---|---|
| Refrigerant state points | [CoolProp](http://www.coolprop.org) (REFPROP-grade EOS) |
| Compressor work | Isentropic + volumetric + mechanical efficiency |
| Condenser / evaporator | ε-NTU heat exchanger model |
| Outdoor unit fan | ASHRAE 90.1-style VSD power curve, air-side ε-NTU |
| Borehole (GSHP) | g-function via [pygfunction](https://github.com/MassimoCimmino/pygfunction) |
| PV / solar thermal | [pvlib](https://pvlib-python.readthedocs.io)-driven irradiance & power |
| Cycle closure | Internal minimization → optimal evaporating temperature |

The same core cycle is reused across every system model — what changes is the **source-side** (air / ground / water) and the **sink-side** (DHW tank, building load, hybrid PV / STC / ESS configurations).

---

## Installation

Requires Python ≥ 3.10 and the [`uv`](https://github.com/astral-sh/uv) package manager.

```bash
git clone https://github.com/bet-lab/physics-heatpump-models.git
cd physics-heatpump-models
uv sync
```

Optional dev / docs tooling is exposed via [PEP 735](https://peps.python.org/pep-0735/) dependency groups:

```bash
uv sync --group dev      # pytest, mypy, ruff
uv sync --group docs     # sphinx + theme
```

---

## Quick start

### Steady-state operating point

```python
from physics_hp import AirSourceHeatPumpBoiler

# Build a model — refrigerant is just a parameter (default: R134a)
ashpb = AirSourceHeatPumpBoiler(ref="R32")

# Steady state: tank at 55 °C, ambient at 5 °C, target condenser duty 8 kW
result = ashpb.analyze_steady(
    T_tank_w=55.0,
    T0=5.0,
    Q_ref_cond=8_000.0,
)

print(f"COP (refrigerant) : {result['cop_ref [-]']:.2f}")
print(f"COP (system)      : {result['cop_sys [-]']:.2f}")
print(f"Heating capacity  : {result['Q_ref_cond [W]'] / 1e3:.2f} kW")
print(f"Compressor power  : {result['E_cmp [W]'] / 1e3:.2f} kW")
print(f"Evap sat. temp.   : {result['T_ref_evap_sat [°C]']:.1f} °C")
print(f"Cond sat. temp.   : {result['T_ref_cond_sat_v [°C]']:.1f} °C")
```

Swap the refrigerant — no recalibration required:

```python
ashpb_r290 = AirSourceHeatPumpBoiler(ref="R290")    # propane
ashpb_r744 = AirSourceHeatPumpBoiler(ref="R744")    # CO₂
ashpb_r410 = AirSourceHeatPumpBoiler(ref="R410A")
```

### Time-stepping dynamic simulation

```python
import numpy as np
from physics_hp import AirSourceHeatPumpBoiler

ashpb = AirSourceHeatPumpBoiler(ref="R32")

simulation_period_sec = 24 * 3600
dt_s                  = 60
n_steps               = simulation_period_sec // dt_s

dhw_usage_schedule = np.zeros(n_steps)            # m³/s per step
T0_schedule        = np.full(n_steps, 5.0)        # outdoor °C per step

df = ashpb.analyze_dynamic(
    simulation_period_sec = simulation_period_sec,
    dt_s                  = dt_s,
    T_tank_w_init_C       = 50.0,
    dhw_usage_schedule    = dhw_usage_schedule,
    T0_schedule           = T0_schedule,
)

# df is a pandas DataFrame with the same keys as analyze_steady, per time step.
```

---

## Models

<details open>
<summary><b>Air-source heat pump boilers (ASHPB)</b></summary>

| Class | Description |
|---|---|
| `AirSourceHeatPumpBoiler` | Core ASHPB — refrigerant cycle + storage tank |
| `ASHPB_STC_preheat` | + Solar thermal collector preheat |
| `ASHPB_STC_tank` | + STC with stratified tank |
| `ASHPB_PV_ESS` | + PV + Energy Storage System |

</details>

<details open>
<summary><b>Ground-source heat pump boilers (GSHPB)</b></summary>

| Class | Description |
|---|---|
| `GroundSourceHeatPumpBoiler` | Core GSHPB with g-function borehole model |
| `GSHPB_STC_preheat` | + STC preheat |
| `GSHPB_STC_tank` | + STC with stratified tank |
| `GSHPB_PV_ESS` | + PV + Energy Storage System |

</details>

<details open>
<summary><b>Water-source heat pump boiler (WSHPB)</b></summary>

| Class | Description |
|---|---|
| `WaterSourceHeatPumpBoiler` | Dynamic WSHPB model |

</details>

<details open>
<summary><b>Space-conditioning heat pumps</b></summary>

| Class | Description |
|---|---|
| `AirSourceHeatPump` | ASHP — heating & cooling |
| `GroundSourceHeatPump` | GSHP — heating & cooling |

</details>

<details>
<summary><b>Supporting modules</b></summary>

| Module | Purpose |
|---|---|
| `refrigerant.py` | CoolProp state-point helpers |
| `thermodynamics.py` | Cycle analysis — COP, compression ratio, isentropic efficiency |
| `heat_transfer.py` | ε-NTU heat exchanger calculations |
| `hx_fan.py` | Air-side fan & heat-exchanger model |
| `g_function.py` | Borehole g-function (pygfunction) |
| `weather.py` | Outdoor air temperature & weather utilities |
| `dhw.py` | Domestic hot water demand profiles |
| `cop.py` | COP correlations |
| `enex_functions.py` | Energy / exergy helpers |
| `dynamic_context.py` | Per-step simulation state |
| `subsystems.py` | Subsystem composition (STC / PV / UV) |
| `simulation_summary.py` | Stdout summary tables |
| `visualization.py` | Plotting facade |
| `mollier_diagram.py` | T-h / P-h / T-s plots |
| `uv_treatment.py` | UV treatment subsystem |
| `calc_util.py` | Unit conversions |
| `constants.py` | Physical constants |

</details>

---

## Validation

The `AirSourceHeatPumpBoiler` model was validated against commercial catalogue data (**Samsung EHS 14 kW**) across **15 operating points** spanning LWT 40 / 50 / 65 °C and outdoor air temperatures from −10 to 30 °C.

<div align="center">

| Metric | Value |
|:---:|:---:|
| **MAE** | 0.354 |
| **MAPE** | 10.09 % |

</div>

This accuracy is achieved **without unit-specific calibration** — the same code path applies to any CoolProp refrigerant and any operating envelope the cycle can physically close in.

> 📄 *"Thermodynamic Modeling of Refrigerant Cycle in an Air-Source Heat Pump Boiler and Validation against Commercial Catalogue Data"*, KJACR (2025).

---

## Documentation

- 📚 **[Full API reference](https://bet-lab.github.io/physics-heatpump-models/)** — Sphinx-generated docs
- 🔗 **[enex_analysis_engine](https://bet-lab.github.io/enex_analysis_engine/)** — sister energy / exergy analysis library, maintained in parallel

---

## Project layout

```text
physics-heatpump-models/
├── src/physics_hp/                # Importable package
│   ├── __init__.py                # Public re-exports
│   │
│   ├── air_source_heat_pump.py            # ASHP (space conditioning)
│   ├── air_source_heat_pump_boiler.py     # ASHPB core
│   ├── ashpb_stc_preheat.py
│   ├── ashpb_stc_tank.py
│   ├── ashpb_pv_ess.py
│   │
│   ├── ground_source_heat_pump.py         # GSHP (space conditioning)
│   ├── ground_source_heat_pump_boiler.py  # GSHPB core
│   ├── gshpb_stc_preheat.py
│   ├── gshpb_stc_tank.py
│   ├── gshpb_pv_ess.py
│   │
│   ├── water_source_heat_pump_boiler.py   # WSHPB core
│   │
│   ├── refrigerant.py             # CoolProp helpers
│   ├── thermodynamics.py          # Cycle analysis
│   ├── heat_transfer.py           # ε-NTU
│   ├── hx_fan.py                  # Air-side fan & heat-exchanger model
│   ├── g_function.py              # Borehole g-function
│   ├── weather.py
│   ├── dhw.py
│   ├── cop.py
│   ├── enex_functions.py
│   ├── dynamic_context.py
│   ├── subsystems.py
│   ├── simulation_summary.py
│   ├── visualization.py
│   ├── mollier_diagram.py
│   ├── uv_treatment.py
│   ├── calc_util.py
│   └── constants.py
│
├── docs/                          # Sphinx documentation
├── tests/                         # Unit / smoke tests
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Related work

- [`enex_analysis_engine`](https://github.com/bet-lab/enex_analysis_engine) — sister energy / exergy analysis library, maintained in parallel (not currently consumed as a submodule)

---

## License

MIT License © 2025 **betlab** — Habin Jo, Wonjun Choi
