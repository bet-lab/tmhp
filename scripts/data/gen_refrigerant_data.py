"""Pre-compute a multi-dimensional grid of vapour-compression cycle states.

This generator sweeps an 8-parameter grid (refrigerant, source/sink
temperatures, subcool, superheat, condenser load, and the two heat-exchanger
``UA`` values), runs a damped fixed-point solver to establish the dynamic
evaporating temperature, and serialises every reachable cycle state to a single
compact JSON asset consumed by the client-side SVG widget.

The condensing temperature is fixed directly by the load and condenser ``UA``::

    T_cond = T_sink + Q_cond / UA_cond

The evaporating temperature is coupled to the cycle through the evaporator duty
and is solved iteratively::

    Q_evap = m_ref (h1 - h4)          (cycle energy balance)
    T_evap = T_source - Q_evap / UA_evap

Combinations that are physically unreachable (e.g. ``T_cond`` above the
refrigerant critical temperature, or a non-converging / inverted cycle) are
omitted from the output; the widget renders an "unavailable" notice for those.

Output
------
``docs/source/_static/widgets/cycle_data.json`` — a single JSON file with:

* ``meta``        — grid metadata, point ordering, units
* ``params``      — axis values for each parameter
* ``limits``      — per-refrigerant diagram axis limits (from ``REF_LIMITS``)
* ``saturation``  — per-refrigerant saturation dome curves
* ``states``      — dict of ``"i0_i1_..._i7" -> [[h,T,P,s], ...]`` (7 points)
"""

from __future__ import annotations

import json
import os

import CoolProp.CoolProp as CP
import numpy as np
from tqdm import tqdm

import tmhp.calc_util as cu
from tmhp.mollier_diagram import REF_LIMITS
from tmhp.refrigerant import calc_ref_state

# ── Parameter grid ──────────────────────────────────────────────────────────
REFRIGERANTS = ["R410A", "R134a", "R32", "R290"]
T_SOURCES_C = [-15.0, -5.0, 5.0, 15.0]
T_SINKS_C = [30.0, 45.0, 60.0]
DT_SUBCOOL_K = [0.0, 3.0, 6.0]
DT_SUPERHEAT_K = [0.0, 4.0, 8.0]
Q_COND_W = [4000.0, 8000.0, 12000.0]
UA_COND_WK = [300.0, 600.0, 900.0]
UA_EVAP_WK = [300.0, 600.0, 900.0]

ETA_CMP_ISEN = 0.70
SAT_CURVE_POINTS = 10000

# Ordered axis lists; the per-state key encodes the index into each axis.
PARAM_AXES = [
    ("refrigerant", REFRIGERANTS),
    ("T_source", T_SOURCES_C),
    ("T_sink", T_SINKS_C),
    ("dT_subcool", DT_SUBCOOL_K),
    ("dT_superheat", DT_SUPERHEAT_K),
    ("Q_cond", Q_COND_W),
    ("UA_cond", UA_COND_WK),
    ("UA_evap", UA_EVAP_WK),
]

# Display-unit accessors: (h [kJ/kg], T [°C], P [kPa], s [kJ/(kg·K)]).
_POINT_SPEC = [
    ("1s", "h_ref_evap_sat [J/kg]", "T_ref_evap_sat [°C]", "P_ref_evap_sat [Pa]", "s_ref_evap_sat [J/(kg·K)]"),
    ("1", "h_ref_cmp_in [J/kg]", "T_ref_cmp_in [°C]", "P_ref_cmp_in [Pa]", "s_ref_cmp_in [J/(kg·K)]"),
    ("2", "h_ref_cmp_out [J/kg]", "T_ref_cmp_out [°C]", "P_ref_cmp_out [Pa]", "s_ref_cmp_out [J/(kg·K)]"),
    ("2s", "h_ref_cond_sat_v [J/kg]", "T_ref_cond_sat_v [°C]", "P_ref_cond_sat_v [Pa]", "s_ref_cond_sat_v [J/(kg·K)]"),
    ("3s", "h_ref_cond_sat_l [J/kg]", "T_ref_cond_sat_l [°C]", "P_ref_cond_sat_l [Pa]", "s_ref_cond_sat_l [J/(kg·K)]"),
    ("3", "h_ref_exp_in [J/kg]", "T_ref_exp_in [°C]", "P_ref_exp_in [Pa]", "s_ref_exp_in [J/(kg·K)]"),
    ("4", "h_ref_exp_out [J/kg]", "T_ref_exp_out [°C]", "P_ref_exp_out [Pa]", "s_ref_exp_out [J/(kg·K)]"),
]


def build_saturation_curves(refrigerant: str) -> dict[str, list[float]]:
    """Return down-sampled saturation dome curves in display units."""
    t_min = CP.PropsSI("Tmin", refrigerant)
    t_crit = CP.PropsSI("Tcrit", refrigerant)
    temps_k = np.linspace(t_min + 1.0, t_crit - 0.5, SAT_CURVE_POINTS)

    temp_c, h_liq, h_vap, p_sat, s_liq, s_vap = [], [], [], [], [], []
    for t_k in temps_k:
        temp_c.append(round(cu.K2C(t_k), 1))
        h_liq.append(round(CP.PropsSI("H", "T", t_k, "Q", 0, refrigerant) * cu.J2kJ, 1))
        h_vap.append(round(CP.PropsSI("H", "T", t_k, "Q", 1, refrigerant) * cu.J2kJ, 1))
        p_sat.append(round(CP.PropsSI("P", "T", t_k, "Q", 0, refrigerant) * cu.Pa2kPa, 1))
        s_liq.append(round(CP.PropsSI("S", "T", t_k, "Q", 0, refrigerant) * cu.J2kJ, 3))
        s_vap.append(round(CP.PropsSI("S", "T", t_k, "Q", 1, refrigerant) * cu.J2kJ, 3))

    return {"T": temp_c, "h_liq": h_liq, "h_vap": h_vap, "p_sat": p_sat, "s_liq": s_liq, "s_vap": s_vap}


def solve_cycle(
    refrigerant: str,
    t_source_c: float,
    t_sink_c: float,
    dt_subcool: float,
    dt_superheat: float,
    q_cond_w: float,
    ua_cond: float,
    ua_evap: float,
    t_crit_k: float,
    t_min_k: float,
) -> list[list[float]] | None:
    """Solve one cycle; return its 7 packed state points or ``None`` if invalid.

    Each point is ``[h (kJ/kg), T (°C), P (kPa), s (kJ/(kg·K))]`` in the order
    given by :data:`_POINT_SPEC`.
    """
    t_cond_c = t_sink_c + q_cond_w / ua_cond
    t_cond_k = cu.C2K(t_cond_c)
    # The condenser must operate below the critical point (with a small margin)
    # for the two-phase saturation states to exist.
    if t_cond_k > t_crit_k - 1.0:
        return None

    # Damped fixed-point iteration on the evaporating temperature.
    t_evap_c = t_source_c - q_cond_w / ua_evap  # conservative initial guess
    res = None
    converged = False
    for _ in range(60):
        t_evap_k = cu.C2K(t_evap_c)
        if t_evap_k <= t_min_k + 1.0 or t_evap_k >= t_cond_k - 0.5:
            return None

        res = calc_ref_state(
            T_evap_K=t_evap_k,
            T_cond_K=t_cond_k,
            refrigerant=refrigerant,
            eta_cmp_isen=ETA_CMP_ISEN,
            mode="heating",
            dT_superheat=dt_superheat,
            dT_subcool=dt_subcool,
            is_active=True,
        )

        h1 = res["h_ref_cmp_in [J/kg]"]
        h2 = res["h_ref_cmp_out [J/kg]"]
        h3 = res["h_ref_exp_in [J/kg]"]
        h4 = res["h_ref_exp_out [J/kg]"]
        if any(np.isnan(v) for v in (h1, h2, h3, h4)) or np.isnan(res["T_ref_cmp_out_K"]):
            return None

        delta_cond = h2 - h3
        if delta_cond <= 0.0:
            return None

        m_ref = q_cond_w / delta_cond
        q_evap = m_ref * (h1 - h4)
        if q_evap <= 0.0:
            return None

        t_evap_new_c = t_source_c - q_evap / ua_evap
        if abs(t_evap_new_c - t_evap_c) < 1e-3:
            t_evap_c = t_evap_new_c
            converged = True
            break
        t_evap_c = 0.5 * t_evap_c + 0.5 * t_evap_new_c  # under-relaxation

    if not converged or res is None:
        return None

    # Final recompute at the converged evaporating temperature.
    t_evap_k = cu.C2K(t_evap_c)
    if t_evap_k <= t_min_k + 1.0 or t_evap_k >= t_cond_k - 0.5:
        return None
    res = calc_ref_state(
        T_evap_K=t_evap_k,
        T_cond_K=t_cond_k,
        refrigerant=refrigerant,
        eta_cmp_isen=ETA_CMP_ISEN,
        mode="heating",
        dT_superheat=dt_superheat,
        dT_subcool=dt_subcool,
        is_active=True,
    )

    pts = []
    for _name, h_key, t_key, p_key, s_key in _POINT_SPEC:
        h_val = res[h_key]
        t_val = res[t_key]
        p_val = res[p_key]
        s_val = res[s_key]
        if any(np.isnan(v) for v in (h_val, t_val, p_val, s_val)):
            return None
        pts.append([
            round(h_val * cu.J2kJ, 1),
            round(t_val, 1),
            round(p_val * cu.Pa2kPa, 1),
            round(s_val * cu.J2kJ, 3),
        ])

    return pts


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(repo_root, "docs", "source", "_static", "widgets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cycle_data.json")

    saturation = {ref: build_saturation_curves(ref) for ref in REFRIGERANTS}

    crit = {ref: CP.PropsSI("Tcrit", ref) for ref in REFRIGERANTS}
    tmin = {ref: CP.PropsSI("Tmin", ref) for ref in REFRIGERANTS}

    states: dict[str, list[list[float]]] = {}
    total = int(np.prod([len(axis) for _, axis in PARAM_AXES]))

    with tqdm(total=total, desc="Solving cycle grid") as pbar:
        for i0, ref in enumerate(REFRIGERANTS):
            for i1, t_source in enumerate(T_SOURCES_C):
                for i2, t_sink in enumerate(T_SINKS_C):
                    for i3, dt_sub in enumerate(DT_SUBCOOL_K):
                        for i4, dt_sup in enumerate(DT_SUPERHEAT_K):
                            for i5, q_cond in enumerate(Q_COND_W):
                                for i6, ua_cond in enumerate(UA_COND_WK):
                                    for i7, ua_evap in enumerate(UA_EVAP_WK):
                                        packed = solve_cycle(
                                            ref, t_source, t_sink, dt_sub, dt_sup,
                                            q_cond, ua_cond, ua_evap,
                                            crit[ref], tmin[ref],
                                        )
                                        if packed is not None:
                                            key = f"{i0}_{i1}_{i2}_{i3}_{i4}_{i5}_{i6}_{i7}"
                                            states[key] = packed
                                        pbar.update(1)

    data = {
        "meta": {
            "eta_cmp_isen": ETA_CMP_ISEN,
            "point_order": [name for name, *_ in _POINT_SPEC],
            "point_labels": {
                "1s": "1'", "1": "1", "2": "2", "2s": "2'", "3s": "3'", "3": "3", "4": "4",
            },
            "value_order": ["h", "T", "P", "s"],
            "units": {"h": "kJ/kg", "T": "°C", "P": "kPa", "s": "kJ/(kg·K)"},
            "state_format": "states[key] is a list of 7 points; each point is [h, T, P, s]",
            "key_axes": [name for name, _ in PARAM_AXES],
            "n_valid": len(states),
            "n_total": total,
        },
        "params": {name: axis for name, axis in PARAM_AXES},
        "limits": REF_LIMITS,
        "saturation": saturation,
        "states": states,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Wrote {out_path}")
    print(f"Valid states: {len(states)} / {total}  ({100 * len(states) / total:.1f}%)")
    print(f"File size: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
