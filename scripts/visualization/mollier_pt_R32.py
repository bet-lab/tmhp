"""Generate the R32 P-T cycle diagram embedded in the docs tutorial.

Counterpart to ``mollier_ph_R32.py``: same operating point, same
``analyze_steady`` result, same dependency footprint (CoolProp +
Matplotlib only). The diagram overlays the seven cycle nodes on top
of the R32 saturation curve in (T, P) coordinates.

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

mpl.rcParams["svg.hashsalt"] = "physics-hp.visualization.mollier-pt-r32"

mpl.rcParams["text.usetex"] = False
mpl.rcParams["mathtext.fontset"] = "stix"
mpl.rcParams["font.family"] = "STIXGeneral"


REF = "R32"
OUTPUT_PATH = Path("docs/source/_static/mollier_pt_R32.svg")

LABEL_TEX: dict[str, str] = {
    "1*": r"$1^{\star}$",
    "1":  r"$1$",
    "2":  r"$2$",
    "2*": r"$2^{\star}$",
    "3*": r"$3^{\star}$",
    "3":  r"$3$",
    "4":  r"$4$",
}
# Per-node label offsets (dx, dy) in points. The P-T plot has all
# isobaric segments collapsed to a single point per pressure level —
# 4 and 1* share the same P, T (evaporator); 2* and 3* share the same
# P near the condensing saturation line — so labels need careful
# horizontal staggering.
LABEL_OFFSET_PT: dict[str, tuple[int, int]] = {
    "1*": (-18, -12),
    "1":  (6, -4),
    "2":  (6, 4),
    "2*": (-18, 6),
    "3*": (6, 6),
    "3":  (6, -10),
    "4":  (-12, 4),
}


def _saturation_curve(refrigerant: str) -> tuple[np.ndarray, np.ndarray]:
    """R32 saturation curve in (T [°C], P [kPa]).

    Closed at the critical point so the curve terminates cleanly.
    """
    T_crit = CP.PropsSI("Tcrit", refrigerant)
    P_crit = CP.PropsSI("Pcrit", refrigerant) / 1_000  # kPa
    T_grid_K = np.linspace(220.0, T_crit - 0.05, 200)
    p_sat = np.array(
        [CP.PropsSI("P", "T", T, "Q", 0, refrigerant) for T in T_grid_K],
    ) / 1_000
    T_grid_C = T_grid_K - 273.15
    # Append the critical point so the curve ends at (Tcrit, Pcrit).
    T_grid_C = np.append(T_grid_C, T_crit - 273.15)
    p_sat = np.append(p_sat, P_crit)
    return T_grid_C, p_sat


def _cycle_points(result: dict[str, float]) -> dict[str, tuple[float, float]]:
    """Pull the seven (T [°C], P [kPa]) cycle points from analyze_steady()."""

    def tp(t_key: str, p_key: str) -> tuple[float, float]:
        return result[t_key], result[p_key] / 1_000

    return {
        "1*": tp("T_ref_evap_sat [°C]",   "P_ref_evap_sat [Pa]"),
        "1":  tp("T_ref_cmp_in [°C]",     "P_ref_cmp_in [Pa]"),
        "2":  tp("T_ref_cmp_out [°C]",    "P_ref_cmp_out [Pa]"),
        "2*": tp("T_ref_cond_sat_v [°C]", "P_ref_cond_sat_v [Pa]"),
        "3*": tp("T_ref_cond_sat_l [°C]", "P_ref_cond_sat_l [Pa]"),
        "3":  tp("T_ref_exp_in [°C]",     "P_ref_exp_in [Pa]"),
        "4":  tp("T_ref_exp_out [°C]",    "P_ref_exp_out [Pa]"),
    }


def main() -> None:
    ashpb = AirSourceHeatPumpBoiler(ref=REF)
    result = ashpb.analyze_steady(T_tank_w=55.0, T0=5.0, Q_ref_cond=8_000.0)
    # analyze_steady defaults to return_dict=True; narrow the union for
    # the rest of this script.
    assert isinstance(result, dict)

    T_sat, P_sat = _saturation_curve(REF)
    pts = _cycle_points(result)

    fig, ax = plt.subplots(figsize=(7.2, 5.0))

    ax.plot(T_sat, P_sat, color="#0c8599", lw=1.4, label="Saturation curve")

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

    for key, (x, y) in pts.items():
        ax.annotate(
            LABEL_TEX[key],
            (x, y),
            xytext=LABEL_OFFSET_PT[key],
            textcoords="offset points",
            fontsize=10,
            color="#212529",
        )

    ax.set_yscale("log")
    ax.set_xlabel(r"Temperature $T$ [$^{\circ}$C]")
    ax.set_ylabel(r"Pressure $P$ [kPa]")
    ax.set_title(
        r"$P$–$T$ diagram — $\mathrm{R32}$ cycle" "\n"
        r"$T_{\mathrm{tank}}=55\,^{\circ}\mathrm{C}$, "
        r"$T_{0}=5\,^{\circ}\mathrm{C}$, "
        r"$\dot{Q}_{\mathrm{cond}}=8\,\mathrm{kW}$"
    )
    ax.legend(loc="lower right", frameon=False)
    ax.grid(True, which="both", alpha=0.3)

    fig.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
