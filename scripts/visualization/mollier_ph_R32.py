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

# Use Matplotlib's built-in mathtext for LaTeX-style labels. No system
# TeX install required; the STIX fontset matches the body text of the
# Shibuya theme reasonably well.
mpl.rcParams["text.usetex"] = False
mpl.rcParams["mathtext.fontset"] = "stix"
mpl.rcParams["font.family"] = "STIXGeneral"


REF = "R32"
OUTPUT_PATH = Path("docs/source/_static/mollier_ph_R32.svg")

# Per-node label offsets (dx, dy) in points. Tuned so the superheat /
# subcool pairs (1 next to 1*, 3 next to 3*) don't collide.
LABEL_TEX: dict[str, str] = {
    "1*": r"$1^{\star}$",
    "1":  r"$1$",
    "2":  r"$2$",
    "2*": r"$2^{\star}$",
    "3*": r"$3^{\star}$",
    "3":  r"$3$",
    "4":  r"$4$",
}
LABEL_OFFSET_PH: dict[str, tuple[int, int]] = {
    "1*": (-14, -12),
    "1":  (6, 4),
    "2":  (6, 4),
    "2*": (6, -12),
    "3*": (6, 6),
    "3":  (-14, -12),
    "4":  (-12, -12),
}


def _saturation_envelope(refrigerant: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Liquid + vapour saturation curves on a P-h chart, in (kJ/kg, kPa).

    The curves are explicitly closed at the critical point so the dome
    is a single connected boundary rather than two dangling arcs.
    """
    T_crit = CP.PropsSI("Tcrit", refrigerant)
    P_crit = CP.PropsSI("Pcrit", refrigerant) / 1_000  # kPa
    # Stop a hair short of Tcrit; CoolProp gets unstable right at the
    # critical isotherm.
    T_grid = np.linspace(220.0, T_crit - 0.05, 200)
    h_liq = np.array([CP.PropsSI("H", "T", T, "Q", 0, refrigerant) for T in T_grid]) / 1_000
    h_vap = np.array([CP.PropsSI("H", "T", T, "Q", 1, refrigerant) for T in T_grid]) / 1_000
    p_sat = np.array([CP.PropsSI("P", "T", T, "Q", 0, refrigerant) for T in T_grid]) / 1_000

    # Critical-point closure: at Tcrit the two saturation enthalpies
    # collapse onto a single point. Use the average of the last two
    # sampled values as a numerically stable proxy for h_crit.
    h_crit = 0.5 * (h_liq[-1] + h_vap[-1])
    h_liq = np.append(h_liq, h_crit)
    h_vap = np.append(h_vap, h_crit)
    p_sat = np.append(p_sat, P_crit)
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
    # analyze_steady defaults to return_dict=True; narrow the union for
    # the rest of this script.
    assert isinstance(result, dict)

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

    for key, (x, y) in pts.items():
        ax.annotate(
            LABEL_TEX[key],
            (x, y),
            xytext=LABEL_OFFSET_PH[key],
            textcoords="offset points",
            fontsize=10,
            color="#212529",
        )

    ax.set_yscale("log")
    ax.set_xlabel(r"Enthalpy $h$ [kJ/kg]")
    ax.set_ylabel(r"Pressure $P$ [kPa]")
    ax.set_title(
        r"$P$–$h$ diagram — $\mathrm{R32}$ cycle" "\n"
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
