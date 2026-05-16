"""Generate the R32 P-h cycle diagram embedded in the docs tutorial.

Uses only CoolProp and Matplotlib — both runtime dependencies of
``physics_hp`` already — so it can run on any environment that can
``import physics_hp``. No ``dartwork_mpl`` dependency.

Operating point matches the ASHPB quickstart example:
``T_tank_w = 55 °C``, ``T0 = 5 °C``, ``Q_ref_cond = 8 kW``.
"""

from __future__ import annotations

from pathlib import Path

import CoolProp.CoolProp as CP
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from physics_hp import AirSourceHeatPumpBoiler

# Pin SVG clip-path IDs so re-running the script produces byte-identical
# output (matches the convention from samsung_ehs_parity.py).
mpl.rcParams["svg.hashsalt"] = "physics-hp.visualization.mollier-ph-r32"


REF = "R32"
OUTPUT_PATH = Path("docs/source/_static/mollier_ph_R32.svg")


def _saturation_envelope(refrigerant: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Liquid + vapour saturation curves on a P-h chart, in (kJ/kg, kPa)."""
    T_crit = CP.PropsSI("Tcrit", refrigerant)
    T_grid = np.linspace(220.0, T_crit - 0.5, 200)
    h_liq = np.array([CP.PropsSI("H", "T", T, "Q", 0, refrigerant) for T in T_grid]) / 1_000
    h_vap = np.array([CP.PropsSI("H", "T", T, "Q", 1, refrigerant) for T in T_grid]) / 1_000
    p_sat = np.array([CP.PropsSI("P", "T", T, "Q", 0, refrigerant) for T in T_grid]) / 1_000
    return h_liq, h_vap, p_sat


def _cycle_points(result: dict[str, float]) -> dict[str, tuple[float, float]]:
    """Pull the seven (h, P) cycle points from analyze_steady() output."""

    def hp(h_key: str, p_key: str) -> tuple[float, float]:
        return result[h_key] / 1_000, result[p_key] / 1_000

    return {
        "1*": hp("h_ref_evap_sat [J/kg]", "P_ref_evap_sat [Pa]"),
        "1":  hp("h_ref_cmp_in [J/kg]",   "P_ref_cmp_in [Pa]"),
        "2":  hp("h_ref_cmp_out [J/kg]",  "P_ref_cmp_out [Pa]"),
        "2*": hp("h_ref_cond_sat_v [J/kg]", "P_ref_cond_sat_v [Pa]"),
        "3*": hp("h_ref_cond_sat_l [J/kg]", "P_ref_cond_sat_l [Pa]"),
        "3":  hp("h_ref_exp_in [J/kg]",   "P_ref_exp_in [Pa]"),
        "4":  hp("h_ref_exp_out [J/kg]",  "P_ref_exp_out [Pa]"),
    }


def main() -> None:
    ashpb = AirSourceHeatPumpBoiler(ref=REF)
    result = ashpb.analyze_steady(T_tank_w=55.0, T0=5.0, Q_ref_cond=8_000.0)

    h_liq, h_vap, p_sat = _saturation_envelope(REF)
    pts = _cycle_points(result)

    fig, ax = plt.subplots(figsize=(7.2, 5.0))

    ax.plot(h_liq, p_sat, color="#1c7ed6", lw=1.3, label="Saturated liquid")
    ax.plot(h_vap, p_sat, color="#e03131", lw=1.3, label="Saturated vapor")

    path = ["1*", "1", "2", "2*", "3*", "3", "4", "1*"]
    xs = [pts[p][0] for p in path]
    ys = [pts[p][1] for p in path]
    ax.plot(
        xs, ys,
        color="#212529",
        lw=1.1,
        marker="o",
        markersize=4.5,
        markerfacecolor="#212529",
        label="Refrigerant cycle",
    )

    for label, (x, y) in pts.items():
        ax.annotate(
            label,
            (x, y),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
            color="#212529",
        )

    ax.set_yscale("log")
    ax.set_xlabel("Enthalpy [kJ/kg]")
    ax.set_ylabel("Pressure [kPa]")
    ax.set_title(
        f"P–h diagram — {REF} cycle\n"
        f"T_tank = 55 °C, T_0 = 5 °C, Q_cond = 8 kW"
    )
    ax.legend(loc="lower right", frameon=False)
    ax.grid(True, which="both", alpha=0.3)

    fig.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
