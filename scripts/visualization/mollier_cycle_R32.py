"""Two-panel R32 refrigerant-cycle diagram embedded in the docs tutorial.

Replaces the previous single-panel mollier_ph_R32.py / mollier_pt_R32.py
pair with one figure: panel (a) P-h, panel (b) T-h, sharing the same
seven cycle nodes returned by analyze_steady().

Uses only CoolProp and Matplotlib — both runtime dependencies of
``tmhp`` already — so it runs in any environment that can
``import tmhp``. No ``dartwork_mpl`` dependency.

Operating point picks a realistic DHW operating condition:
``T_tank_w = 60 °C``, ``T0 = 12 °C``, ``Q_ref_cond = 8 kW``.
"""

from __future__ import annotations

from pathlib import Path

import CoolProp.CoolProp as CP
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from tmhp import AirSourceHeatPumpBoiler

# Pin SVG clip-path IDs so re-running the script produces byte-identical
# output (matches the convention from samsung_ehs_parity.py).
mpl.rcParams["svg.hashsalt"] = "tmhp.visualization.mollier-cycle-r32"

# Use Matplotlib's built-in mathtext for LaTeX-style labels. No system
# TeX install required; the STIX fontset matches the body text of the
# Shibuya theme reasonably well.
mpl.rcParams["text.usetex"] = False
mpl.rcParams["mathtext.fontset"] = "stix"
mpl.rcParams["font.family"] = "STIXGeneral"

# Bump default font sizes so the figure stays legible at the size the
# Shibuya theme renders it (about 720 px wide). The previous defaults
# (10 pt) were noticeably smaller than the surrounding body text.
mpl.rcParams.update({
    "font.size":        13,
    "axes.labelsize":   14,
    "axes.titlesize":   14,
    "xtick.labelsize":  12,
    "ytick.labelsize":  12,
    "legend.fontsize":  12,
})


REF = "R32"
T_TANK_W = 60.0   # °C
T0       = 12.0   # °C
Q_COND   = 8_000  # W

OUTPUT_PATH = Path("docs/source/_static/mollier_cycle_R32.svg")

# Colours — match the body palette and the iris accent used elsewhere.
COLOR_LIQ      = "#4dabf7"   # sat. liquid (blue)
COLOR_VAP      = "#ff6b6b"   # sat. vapour (red)
COLOR_CYCLE    = "#212529"   # ref. cycle nodes + connector
COLOR_TANK_LWT = "#fa5252"   # tank water reference line
COLOR_AMBIENT  = "#fd7e14"   # outdoor air reference line


def _saturation_envelope_ph(refrigerant: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Liquid + vapour saturation curves on a P-h chart, in (kJ/kg, kPa)."""
    T_crit = CP.PropsSI("Tcrit", refrigerant)
    P_crit = CP.PropsSI("Pcrit", refrigerant) / 1_000  # kPa
    T_grid = np.linspace(220.0, T_crit - 0.05, 200)
    h_liq = np.array([CP.PropsSI("H", "T", T, "Q", 0, refrigerant) for T in T_grid]) / 1_000
    h_vap = np.array([CP.PropsSI("H", "T", T, "Q", 1, refrigerant) for T in T_grid]) / 1_000
    p_sat = np.array([CP.PropsSI("P", "T", T, "Q", 0, refrigerant) for T in T_grid]) / 1_000
    h_crit = 0.5 * (h_liq[-1] + h_vap[-1])
    return (
        np.append(h_liq, h_crit),
        np.append(h_vap, h_crit),
        np.append(p_sat, P_crit),
    )


def _saturation_envelope_th(refrigerant: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Liquid + vapour saturation curves on a T-h chart, in (kJ/kg, °C)."""
    T_crit = CP.PropsSI("Tcrit", refrigerant)
    T_grid_K = np.linspace(220.0, T_crit - 0.05, 200)
    h_liq = np.array([CP.PropsSI("H", "T", T, "Q", 0, refrigerant) for T in T_grid_K]) / 1_000
    h_vap = np.array([CP.PropsSI("H", "T", T, "Q", 1, refrigerant) for T in T_grid_K]) / 1_000
    T_C = T_grid_K - 273.15
    h_crit = 0.5 * (h_liq[-1] + h_vap[-1])
    return (
        np.append(h_liq, h_crit),
        np.append(h_vap, h_crit),
        np.append(T_C, T_crit - 273.15),
    )


def _cycle_nodes_ph(r: dict[str, float]) -> dict[str, tuple[float, float]]:
    """Pull seven (h [kJ/kg], P [kPa]) points from analyze_steady()."""

    def hp(h_key: str, p_key: str) -> tuple[float, float]:
        return r[h_key] / 1_000, r[p_key] / 1_000

    return {
        "1*": hp("h_ref_evap_sat [J/kg]",    "P_ref_evap_sat [Pa]"),
        "1":  hp("h_ref_cmp_in [J/kg]",      "P_ref_cmp_in [Pa]"),
        "2":  hp("h_ref_cmp_out [J/kg]",     "P_ref_cmp_out [Pa]"),
        "2*": hp("h_ref_cond_sat_v [J/kg]",  "P_ref_cond_sat_v [Pa]"),
        "3*": hp("h_ref_cond_sat_l [J/kg]",  "P_ref_cond_sat_l [Pa]"),
        "3":  hp("h_ref_exp_in [J/kg]",      "P_ref_exp_in [Pa]"),
        "4":  hp("h_ref_exp_out [J/kg]",     "P_ref_exp_out [Pa]"),
    }


def _cycle_nodes_th(r: dict[str, float]) -> dict[str, tuple[float, float]]:
    """Pull seven (h [kJ/kg], T [°C]) points from analyze_steady()."""

    def ht(h_key: str, t_key: str) -> tuple[float, float]:
        return r[h_key] / 1_000, r[t_key]

    return {
        "1*": ht("h_ref_evap_sat [J/kg]",    "T_ref_evap_sat [°C]"),
        "1":  ht("h_ref_cmp_in [J/kg]",      "T_ref_cmp_in [°C]"),
        "2":  ht("h_ref_cmp_out [J/kg]",     "T_ref_cmp_out [°C]"),
        "2*": ht("h_ref_cond_sat_v [J/kg]",  "T_ref_cond_sat_v [°C]"),
        "3*": ht("h_ref_cond_sat_l [J/kg]",  "T_ref_cond_sat_l [°C]"),
        "3":  ht("h_ref_exp_in [J/kg]",      "T_ref_exp_in [°C]"),
        "4":  ht("h_ref_exp_out [J/kg]",     "T_ref_exp_out [°C]"),
    }


# Map the library's internal 1/2/3/4 nodes to the labels readers expect.
NODE_LABEL: dict[str, str] = {
    "1": "cmp,in",
    "2": "cmp,out",
    "3": "exp,in",
    "4": "exp,out",
}
CYCLE_PATH = ["1*", "1", "2", "2*", "3*", "3", "4", "1*"]
CLOSED_NODES = ["1", "2", "3", "4"]            # cycle states (filled markers)
OPEN_NODES   = ["1*", "2*", "3*"]              # saturation intersections (hollow)


def _draw_envelope(ax, h_liq, h_vap, y_sat, label_units: str) -> None:
    """Common saturation-envelope plot on the given axes."""
    ax.plot(h_liq, y_sat, color=COLOR_LIQ, lw=1.6, label="Sat. liquid")
    ax.plot(h_vap, y_sat, color=COLOR_VAP, lw=1.6, label="Sat. vapor")


def _draw_cycle(ax, pts: dict[str, tuple[float, float]],
                label_offsets: dict[str, tuple[int, int]]) -> None:
    """Common cycle-path + node markers + labels on the given axes."""
    xs = [pts[k][0] for k in CYCLE_PATH]
    ys = [pts[k][1] for k in CYCLE_PATH]

    # Dashed connector first so markers sit on top.
    ax.plot(xs, ys, color=COLOR_CYCLE, lw=0.9, linestyle=(0, (2, 2)),
            zorder=2, label="Ref. cycle")

    # Saturation intersections — open circles, no label.
    for k in OPEN_NODES:
        x, y = pts[k]
        ax.plot(x, y, marker="o", markersize=7,
                markerfacecolor="white", markeredgecolor=COLOR_CYCLE,
                markeredgewidth=1.4, linestyle="None", zorder=3)

    # Cycle states — filled circles with text labels.
    for k in CLOSED_NODES:
        x, y = pts[k]
        ax.plot(x, y, marker="o", markersize=7,
                markerfacecolor=COLOR_CYCLE, markeredgecolor=COLOR_CYCLE,
                linestyle="None", zorder=3)
        dx, dy = label_offsets[k]
        ax.annotate(NODE_LABEL[k], (x, y),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=12, color=COLOR_CYCLE)


def _panel_letter(ax, letter: str) -> None:
    """Bold lowercase 'a' / 'b' panel label in the top-left corner."""
    ax.text(0.02, 0.97, letter,
            transform=ax.transAxes,
            fontsize=18, fontweight="bold",
            va="top", ha="left")


def main() -> None:
    ashpb = AirSourceHeatPumpBoiler(ref=REF)
    result = ashpb.analyze_steady(T_tank_w=T_TANK_W, T0=T0, Q_ref_cond=Q_COND)
    assert isinstance(result, dict)

    pts_ph = _cycle_nodes_ph(result)
    pts_th = _cycle_nodes_th(result)
    h_liq_ph, h_vap_ph, p_sat = _saturation_envelope_ph(REF)
    h_liq_th, h_vap_th, T_sat = _saturation_envelope_th(REF)

    fig, (ax_ph, ax_th) = plt.subplots(1, 2, figsize=(13.5, 5.4))

    # --- Panel (a): P-h --------------------------------------------------
    _draw_envelope(ax_ph, h_liq_ph, h_vap_ph, p_sat, "P [kPa]")
    _draw_cycle(ax_ph, pts_ph, label_offsets={
        "1": (8, -6), "2": (8, 4), "3": (-22, 8), "4": (-30, -14),
    })
    ax_ph.set_yscale("log")
    ax_ph.set_xlim(0, 700)
    ax_ph.set_ylim(1e2, 1e4)
    ax_ph.set_xlabel("Enthalpy [kJ/kg]")
    ax_ph.set_ylabel("Pressure [kPa]")
    ax_ph.legend(loc="upper left", frameon=False, ncol=3,
                 bbox_to_anchor=(0.08, 1.0))
    ax_ph.grid(True, which="both", alpha=0.25)
    _panel_letter(ax_ph, "a")

    # --- Panel (b): T-h --------------------------------------------------
    _draw_envelope(ax_th, h_liq_th, h_vap_th, T_sat, "T [°C]")
    _draw_cycle(ax_th, pts_th, label_offsets={
        "1": (8, -4), "2": (-50, 4), "3": (-30, 8), "4": (-32, -14),
    })

    # Operating-condition reference lines — leaving water temp + ambient air.
    ax_th.axhline(T_TANK_W, color=COLOR_TANK_LWT, lw=1.2,
                  linestyle=(0, (3, 3)), alpha=0.9)
    ax_th.text(15, T_TANK_W + 3, f"Tank water: {T_TANK_W:.1f}°C",
               color=COLOR_TANK_LWT, fontsize=11)
    ax_th.axhline(T0, color=COLOR_AMBIENT, lw=1.2,
                  linestyle=(0, (3, 3)), alpha=0.9)
    ax_th.text(15, T0 - 10, f"Outdoor air: {T0:.1f}°C",
               color=COLOR_AMBIENT, fontsize=11)

    ax_th.set_xlim(0, 700)
    ax_th.set_ylim(-20, 160)
    ax_th.set_xlabel("Enthalpy [kJ/kg]")
    ax_th.set_ylabel("Temperature [°C]")
    ax_th.legend(loc="upper left", frameon=False, ncol=3,
                 bbox_to_anchor=(0.08, 1.0))
    ax_th.grid(True, which="both", alpha=0.25)
    _panel_letter(ax_th, "b")

    fig.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
