# Physics-Based Heat Pump Models

**First-principles dynamic models for air-source, ground-source, and water-source heat pump boiler systems**

A Python library that provides physics-based dynamic models for heat pump systems used in domestic hot water (DHW) and building heating applications. Unlike conventional empirical curve-fit approaches, this library solves the thermodynamic refrigerant cycle at every time step using CoolProp, enabling system evaluation across a broad range of refrigerants and operating conditions without proprietary manufacturer data.

> **Repository**: [bet-lab/physics-heatpump-models](https://github.com/bet-lab/physics-heatpump-models)
> **Part of**: [enex_analysis_engine](https://github.com/bet-lab/enex_analysis_engine) ecosystem (git submodule)

---

## Why Physics-Based Models?

Conventional building energy simulators (EnergyPlus, TRNSYS, etc.) rely on manufacturer-specific curve fits that:
- Are limited to the operating range of the original test data
- Cannot be adapted to alternative refrigerants
- Do not expose the thermodynamic state of the refrigerant loop

This library solves these limitations by directly computing:

| Property | Method |
|---|---|
| Refrigerant state points | CoolProp thermodynamic library |
| Compressor work | Isentropic + volumetric efficiency model |
| Condenser heat transfer | ε-NTU method |
| Evaporator heat transfer | ε-NTU method with fan model |
| Optimal evaporating temperature | Internal minimization of compressor power |

---

## Models Included

### Air-Source Heat Pump Boiler (ASHPB)

| Class | Description |
|---|---|
| `AirSourceHeatPumpBoiler` | Full dynamic ASHPB model: refrigerant cycle + storage tank |
| `ASHPB_STC_preheat` | ASHPB with solar thermal collector (STC) preheat |
| `ASHPB_STC_tank` | ASHPB + STC with stratified tank |
| `ASHPB_PV_ESS` | ASHPB + PV + Energy Storage System |

### Ground-Source Heat Pump Boiler (GSHPB)

| Class | Description |
|---|---|
| `GroundSourceHeatPumpBoiler` | Full dynamic GSHPB model with g-function borehole model |
| `GSHPB_STC_preheat` | GSHPB with STC preheat |
| `GSHPB_STC_tank` | GSHPB + STC with stratified tank |
| `GSHPB_PV_ESS` | GSHPB + PV + Energy Storage System |

### Water-Source Heat Pump Boiler (WSHPB)

| Class | Description |
|---|---|
| `WaterSourceHeatPumpBoiler` | Dynamic WSHPB model |

### Heat Pump (Space Conditioning)

| Class | Description |
|---|---|
| `AirSourceHeatPump` | ASHP in heating/cooling mode |
| `GroundSourceHeatPump` | GSHP in heating/cooling mode |

### Support Modules

| Module | Description |
|---|---|
| `refrigerant.py` | Refrigerant thermodynamic state functions (via CoolProp) |
| `thermodynamics.py` | Cycle analysis: COP, compression ratio, isentropic efficiency |
| `heat_transfer.py` | ε-NTU heat exchanger calculations |
| `weather.py` | Outdoor air temperature and weather data utilities |
| `dhw.py` | Domestic hot water demand profiles |
| `visualization.py` | Mollier diagram and performance plotting |
| `calc_util.py` | Unit conversion constants |
| `constants.py` | Physical constants |

---

## Quick Start

### As part of `enex_analysis_engine` (recommended)

```python
from enex_analysis import AirSourceHeatPumpBoiler

# Initialize model with R32 refrigerant
ashpb = AirSourceHeatPumpBoiler(ref="R32")

# Run a steady-state operating point:
#   tank water at 55 °C, outdoor air at 5 °C, target condenser heat 8 kW
result = ashpb.analyze_steady(T_tank_w=55.0, T0=5.0, Q_ref_cond=8_000.0)

print(f"COP (refrigerant)  : {result['cop_ref [-]']:.2f}")
print(f"COP (system)       : {result['cop_sys [-]']:.2f}")
print(f"Heating capacity   : {result['Q_ref_cond [W]'] / 1e3:.2f} kW")
print(f"Compressor power   : {result['E_cmp [W]'] / 1e3:.2f} kW")
print(f"Evap sat. temp.    : {result['T_ref_evap_sat [°C]']:.1f} °C")
print(f"Cond sat. temp.    : {result['T_ref_cond_sat_v [°C]']:.1f} °C")
```

For a full time-stepping simulation use `analyze_dynamic(...)` instead — it takes
a weather/load DataFrame and returns a per-step DataFrame of the same keys.

### As a standalone package

```bash
git clone https://github.com/bet-lab/physics-heatpump-models.git
cd physics-heatpump-models
uv sync
```

```python
from physics_hp import AirSourceHeatPumpBoiler
```

---

## Validation

The `AirSourceHeatPumpBoiler` model has been validated against commercial catalogue data (Samsung EHS 14 kW) across **15 operating points** spanning LWT 40/50/65°C and outdoor temperatures −10 to 30°C:

| Metric | Value |
|---|---|
| Mean Absolute Error (MAE) | 0.354 |
| Mean Absolute Percentage Error (MAPE) | 10.09% |

See the associated paper: *"Thermodynamic Modeling of Refrigerant Cycle in an Air-Source Heat Pump Boiler and Validation against Commercial Catalogue Data"* (KJACR, 2025).

---

## Installation

### Requirements

- Python >= 3.10
- `uv` package manager

### From source

```bash
# Clone with submodule (when using as part of enex_analysis_engine)
git submodule update --init --recursive

# Or clone standalone
git clone https://github.com/bet-lab/physics-heatpump-models.git
cd physics-heatpump-models
uv sync
```

---

## Documentation

- **[📚 Online Documentation](https://bet-lab.github.io/physics-heatpump-models/)**: Full API reference (Sphinx-generated)
- **[enex_analysis_engine docs](https://bet-lab.github.io/enex_analysis_engine/)**: Parent library documentation

---

## Project Structure

```
physics-heatpump-models/
├── src/
│   └── physics_hp/                       # Importable package (`from physics_hp import ...`)
│       ├── __init__.py                   # Re-exports the public model classes
│       ├── air_source_heat_pump.py       # ASHP (space conditioning)
│       ├── air_source_heat_pump_boiler.py  # ASHPB core model
│       ├── ashpb_stc_preheat.py          # ASHPB + STC preheat
│       ├── ashpb_stc_tank.py             # ASHPB + STC with stratified tank
│       ├── ashpb_pv_ess.py               # ASHPB + PV + ESS
│       ├── ground_source_heat_pump.py    # GSHP (space conditioning)
│       ├── ground_source_heat_pump_boiler.py  # GSHPB core model
│       ├── gshpb_stc_preheat.py
│       ├── gshpb_stc_tank.py
│       ├── gshpb_pv_ess.py
│       ├── water_source_heat_pump_boiler.py   # WSHPB core model
│       ├── refrigerant.py                # CoolProp state-point helpers
│       ├── thermodynamics.py             # Cycle analysis (COP, exergy, …)
│       ├── heat_transfer.py              # ε-NTU heat exchanger calcs
│       ├── hx_fan.py                     # Fan / heat-exchanger air-side model
│       ├── g_function.py                 # Borehole g-function (pygfunction)
│       ├── weather.py                    # Outdoor / weather utilities
│       ├── dhw.py                        # DHW demand profiles
│       ├── cop.py                        # COP correlations
│       ├── enex_functions.py             # Energy / exergy helpers
│       ├── dynamic_context.py            # Per-step simulation state
│       ├── subsystems.py                 # Subsystem composition helpers
│       ├── simulation_summary.py         # Stdout summary tables
│       ├── visualization.py              # Facade for Mollier plots
│       ├── mollier_diagram.py            # T-h / P-h / T-s plots (optional dep)
│       ├── uv_treatment.py
│       ├── calc_util.py                  # Unit-conversion constants
│       └── constants.py                  # Physical constants
├── docs/                                 # Sphinx documentation
│   ├── Makefile
│   ├── make.bat
│   └── source/
│       ├── conf.py
│       ├── index.rst
│       ├── getting-started/
│       └── api/
├── tests/                                # Unit / smoke tests
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Related Repositories

- [`enex_analysis_engine`](https://github.com/bet-lab/enex_analysis_engine): Parent energy-exergy analysis library (uses this as a submodule)

---

## License

MIT License © 2025 betlab (Habin Jo, Wonjun Choi)
