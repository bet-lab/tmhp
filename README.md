# Physics-Based Heat Pump Models

**First-principles dynamic models for air-source, ground-source, and water-source heat pump boiler systems**

A Python library that provides physics-based dynamic models for heat pump systems used in domestic hot water (DHW) and building heating applications. Unlike conventional empirical curve-fit approaches, this library solves the thermodynamic refrigerant cycle at every time step using CoolProp, enabling system evaluation across a broad range of refrigerants and operating conditions without proprietary manufacturer data.

> **Repository**: [bet-lab/physics_hp_models](https://github.com/bet-lab/physics_hp_models)
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
ashpb = AirSourceHeatPumpBoiler(refrigerant="R32")

# Set operating conditions
ashpb.T_amb = -10       # Outdoor temperature [°C]
ashpb.T_w_tank = 65     # Target LWT [°C]

# Run one time step
result = ashpb.step(dt=60)  # 60-second step

print(f"COP: {result.COP:.2f}")
print(f"Heating capacity: {result.Q_cond:.2f} kW")
```

### As a standalone package

```bash
git clone https://github.com/bet-lab/physics_hp_models.git
cd physics_hp_models
uv sync
```

```python
import sys
sys.path.insert(0, ".")  # Add repo root to path
from air_source_heat_pump_boiler import AirSourceHeatPumpBoiler
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
git clone https://github.com/bet-lab/physics_hp_models.git
cd physics_hp_models
uv sync
```

---

## Documentation

- **[📚 Online Documentation](https://bet-lab.github.io/physics_hp_models/)**: Full API reference (Sphinx-generated)
- **[enex_analysis_engine docs](https://bet-lab.github.io/enex_analysis_engine/)**: Parent library documentation

---

## Project Structure

```
physics_hp_models/
├── src/
│   └── physics_hp/
│       └── __init__.py       # Standalone package entry point
├── docs/                     # Sphinx documentation
│   ├── Makefile
│   ├── make.bat
│   └── source/
│       ├── conf.py
│       ├── index.rst
│       ├── getting-started/
│       └── api/
├── tests/                    # Unit tests
├── air_source_heat_pump_boiler.py   # Core ASHPB model
├── ground_source_heat_pump_boiler.py
├── water_source_heat_pump_boiler.py
├── refrigerant.py
├── thermodynamics.py
├── heat_transfer.py
├── weather.py
├── dhw.py
├── visualization.py
├── calc_util.py
├── constants.py
├── pyproject.toml
└── README.md
```

---

## Related Repositories

- [`enex_analysis_engine`](https://github.com/bet-lab/enex_analysis_engine): Parent energy-exergy analysis library (uses this as a submodule)

---

## License

MIT License © 2025 betlab (Habin Jo, Wonjun Choi)
