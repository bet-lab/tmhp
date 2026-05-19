"""Pre-compute per-refrigerant thermodynamic data for the docs P–h chart.

Output (per refrigerant) is written to
``docs/source/_static/data/refrigerants/<REF>.json`` with three sections:

* ``saturation_dome``  ~80 points along (T_red → P, h_liq, h_vap)
* ``isotherms``        a handful of constant-T lines spanning [-30, +75 °C]
* ``cycle_grid``       a 21×21 grid of (T_evap, T_cond) → COP

The frontend renders the dome + cycle points by bilinear-interpolating on
the grid, so we don't need runtime CoolProp. COP is a property of the
refrigerant cycle alone; Q_cond and ṁ are system-level outputs and live
in the validation / timeseries payloads instead.
"""

from __future__ import annotations

import numpy as np
from CoolProp.CoolProp import PropsSI

from scripts.data._common import write_json

REFRIGERANTS: tuple[str, ...] = ("R32", "R290", "R134a", "R1234yf")

T_EVAP_RANGE_C = (-20.0, 20.0)
T_COND_RANGE_C = (25.0, 65.0)
GRID_N = 21

SUPERHEAT_K = 5.0
SUBCOOL_K = 3.0
ETA_ISEN = 0.70


def saturation_dome(refrigerant: str, n_points: int = 80) -> list[dict[str, float]]:
    """Return ~80 dome points sampled in reduced-temperature space."""
    t_min = PropsSI("T_triple", refrigerant) + 1.0
    t_crit = PropsSI("T_critical", refrigerant)
    fractions = np.concatenate([
        np.linspace(0.05, 0.85, int(n_points * 0.7)),
        np.linspace(0.85, 0.995, n_points - int(n_points * 0.7)),
    ])
    out: list[dict[str, float]] = []
    for f in fractions:
        T = t_min + f * (t_crit - t_min)
        try:
            P = PropsSI("P", "T", T, "Q", 0, refrigerant)
            h_liq = PropsSI("H", "T", T, "Q", 0, refrigerant) / 1000.0
            h_vap = PropsSI("H", "T", T, "Q", 1, refrigerant) / 1000.0
        except ValueError:
            continue
        out.append({
            "T_c": T - 273.15,
            "P_kpa": P / 1000.0,
            "h_liq_kjkg": h_liq,
            "h_vap_kjkg": h_vap,
        })
    out.sort(key=lambda d: d["P_kpa"])
    return out


def isotherm(refrigerant: str, T_c: float, n_points: int = 40) -> list[dict[str, float]]:
    """Return one isotherm line (P, h) sweeping h across the dome and beyond."""
    T = T_c + 273.15
    t_crit = PropsSI("T_critical", refrigerant)
    if t_crit > T:
        P_sat = PropsSI("P", "T", T, "Q", 0, refrigerant)
        P_range = np.geomspace(P_sat * 0.1, P_sat * 5.0, n_points)
    else:
        P_range = np.geomspace(1e5, 1e7, n_points)
    out: list[dict[str, float]] = []
    for P in P_range:
        try:
            h = PropsSI("H", "T", T, "P", P, refrigerant) / 1000.0
        except ValueError:
            continue
        out.append({"P_kpa": P / 1000.0, "h_kjkg": h})
    return out


def cycle_at(refrigerant: str, t_evap_c: float, t_cond_c: float) -> dict[str, float]:
    """Solve a simple isenthalpic-throttle cycle at one (T_evap, T_cond)."""
    T_evap = t_evap_c + 273.15
    T_cond = t_cond_c + 273.15
    T_suction = T_evap + SUPERHEAT_K
    T_subcooled = T_cond - SUBCOOL_K

    P_evap = PropsSI("P", "T", T_evap, "Q", 1, refrigerant)
    P_cond = PropsSI("P", "T", T_cond, "Q", 1, refrigerant)

    h_1 = PropsSI("H", "T", T_suction, "P", P_evap, refrigerant)
    s_1 = PropsSI("S", "T", T_suction, "P", P_evap, refrigerant)
    h_2s = PropsSI("H", "S", s_1, "P", P_cond, refrigerant)
    h_2 = h_1 + (h_2s - h_1) / ETA_ISEN
    h_3 = PropsSI("H", "T", T_subcooled, "P", P_cond, refrigerant)
    h_4 = h_3

    w_comp = h_2 - h_1
    q_cond = h_2 - h_3
    cop = q_cond / w_comp if w_comp > 0 else float("nan")

    return {
        "h_1": h_1 / 1000.0, "h_2": h_2 / 1000.0,
        "h_3": h_3 / 1000.0, "h_4": h_4 / 1000.0,
        "P_evap_kpa": P_evap / 1000.0,
        "P_cond_kpa": P_cond / 1000.0,
        "cop": cop,
    }


def cycle_grid(refrigerant: str) -> dict:
    t_evap = np.linspace(*T_EVAP_RANGE_C, GRID_N).tolist()
    t_cond = np.linspace(*T_COND_RANGE_C, GRID_N).tolist()
    cop: list[list[float | None]] = []
    skipped = 0
    for te in t_evap:
        row_cop: list[float | None] = []
        for tc in t_cond:
            try:
                row_cop.append(cycle_at(refrigerant, te, tc)["cop"])
            except ValueError:
                row_cop.append(None)
                skipped += 1
        cop.append(row_cop)
    if skipped:
        print(f"  [{refrigerant}] cycle_grid: {skipped} cells skipped (CoolProp ValueError — typically near dome edges)")
    return {
        "t_evap_c": t_evap,
        "t_cond_c": t_cond,
        "cop": cop,
    }


def build_refrigerant_payload(refrigerant: str) -> dict:
    return {
        "refrigerant": refrigerant,
        "superheat_k": SUPERHEAT_K,
        "subcool_k": SUBCOOL_K,
        "eta_isen": ETA_ISEN,
        "saturation_dome": saturation_dome(refrigerant),
        "isotherms": [
            {"T_c": T, "points": isotherm(refrigerant, T)}
            for T in (-20.0, 0.0, 20.0, 40.0, 60.0)
        ],
        "cycle_grid": cycle_grid(refrigerant),
    }


def main() -> None:
    for ref in REFRIGERANTS:
        write_json(f"refrigerants/{ref}.json", build_refrigerant_payload(ref))


if __name__ == "__main__":
    main()
