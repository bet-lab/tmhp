"""Daily energy balance for the ASHPB_PV_ESS scenario.

Runs a one-day dynamic simulation with a representative clear-day
irradiance profile and a moderate DHW draw, then renders two side-by-
side panels:

  (a) timeseries — PV generation, ESS state-of-charge proxy
      (cumulative net energy in/out), and HP electrical load.
  (b) stacked-bar daily energy ledger — kWh of PV that went directly
      to HP load, that charged the ESS, that was dumped; plus how much
      of the HP load came from PV, from ESS discharge, and from grid
      import.

The second panel is what makes the design tradeoff readable: a small
ESS dumps a lot of midday PV; a small PV system pulls in a lot of grid.
"""

from __future__ import annotations

import sys
from pathlib import Path

import dartwork_mpl as dm
import matplotlib.pyplot as plt
import numpy as np

from tmhp import ASHPB_PV_ESS
from tmhp.subsystems import EnergyStorageSystem, PhotovoltaicSystem

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _dmpl_common import COLORS, apply_style, finalize, static_path  # noqa: E402

SIM_HOURS = 24
DT_S = 60
N_STEPS = SIM_HOURS * 3600 // DT_S


def _dhw_profile(n: int) -> np.ndarray:
    t_h = np.arange(n) * DT_S / 3600.0
    def peak(c, sigma, lpm):
        return (lpm / 60_000.0) * np.exp(-0.5 * ((t_h - c) / sigma) ** 2)
    return peak(7.0, 0.35, 12.0) + peak(20.0, 0.55, 8.0)


def _t0_profile(n: int) -> np.ndarray:
    t_h = np.arange(n) * DT_S / 3600.0
    return 8.0 + 7.0 * np.sin((t_h - 9.0) * np.pi / 12.0)


def _clearsky_irradiance(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Cosine clearsky profile peaking at solar noon. Returns (I_DN, I_dH)."""
    t_h = np.arange(n) * DT_S / 3600.0
    day_factor = np.clip(np.sin((t_h - 6.0) * np.pi / 12.0), 0.0, 1.0)
    i_dn = 800.0 * day_factor
    i_dh = 150.0 * day_factor
    return i_dn, i_dh


def main() -> None:
    apply_style("report", hashsalt="tmhp.visualization.pv-ess-energy-balance")

    pv = PhotovoltaicSystem()
    ess = EnergyStorageSystem()
    model = ASHPB_PV_ESS(pv=pv, ess=ess, ref="R32")

    dhw = _dhw_profile(N_STEPS)
    t0  = _t0_profile(N_STEPS)
    i_dn, i_dh = _clearsky_irradiance(N_STEPS)

    df = model.analyze_dynamic(
        simulation_period_sec=SIM_HOURS * 3600,
        dt_s=DT_S,
        T_tank_w_init_C=50.0,
        dhw_usage_schedule=dhw,
        T0_schedule=t0,
        I_DN_schedule=i_dn,
        I_dH_schedule=i_dh,
    )

    t_h = np.arange(len(df)) * DT_S / 3600.0
    e_pv   = df["E_pv_out [W]"].to_numpy() / 1_000.0
    e_hp   = df["E_cmp [W]"].to_numpy() / 1_000.0
    e_grid = df["E_grid_import [W]"].to_numpy() / 1_000.0
    e_chg  = df["E_ess_chg [W]"].to_numpy() / 1_000.0
    e_dis  = df["E_ess_dis [W]"].to_numpy() / 1_000.0

    # Daily energy ledger (kWh) by integrating power over the day.
    dt_h = DT_S / 3600.0
    kwh_pv   = float(e_pv.sum()   * dt_h)
    kwh_grid = float(e_grid.sum() * dt_h)
    kwh_dis  = float(e_dis.sum()  * dt_h)
    kwh_chg  = float(e_chg.sum()  * dt_h)
    kwh_hp   = float(e_hp.sum()   * dt_h)
    # The dump column is implicit: PV that wasn't used directly and
    # couldn't be absorbed by the ESS. By energy balance:
    #   PV = direct-to-HP + ESS charge + dump
    # With direct-to-HP estimated as min(PV, HP load) per step.
    direct = np.minimum(e_pv, e_hp)
    kwh_direct = float(direct.sum() * dt_h)
    kwh_dump   = max(0.0, kwh_pv - kwh_direct - kwh_chg)

    fig, (ax_t, ax_b) = plt.subplots(
        1, 2,
        figsize=dm.figsize("17cm", 6 / 12),
        gridspec_kw={"width_ratios": [3, 2]},
    )

    # --- (a) timeseries ------------------------------------------------
    ax_t.plot(t_h, e_pv,   color=COLORS["pv"],     linewidth=dm.lw(1),
              label="PV generation")
    ax_t.plot(t_h, e_hp,   color=COLORS["load"],   linewidth=dm.lw(0),
              label="HP electrical load")
    ax_t.plot(t_h, e_grid, color=COLORS["accent"], linewidth=dm.lw(0),
              linestyle=(0, (3, 3)), label="Grid import")
    ax_t.fill_between(t_h, 0, e_pv, color=COLORS["pv"], alpha=0.20, linewidth=0)
    ax_t.set_xlabel("Time of day [h]")
    ax_t.set_ylabel("Power [kW]")
    ax_t.set_xlim(0, SIM_HOURS)
    ax_t.set_xticks(np.arange(0, SIM_HOURS + 1, 3))
    ax_t.set_title("(a) Daily power timeseries", loc="left", fontsize=dm.fs(0))
    ax_t.grid(True, alpha=0.25, linewidth=dm.lw(-2))
    ax_t.legend(loc="upper left", frameon=False, fontsize=dm.fs(-1))

    # --- (b) stacked ledger -------------------------------------------
    # Two bars: PV destinations vs. HP-load sources.
    x_labels = ["PV destinations", "HP-load sources"]
    x = np.arange(len(x_labels))
    width = 0.55

    # PV destinations stack
    bottom_pv = 0.0
    ax_b.bar(x[0], kwh_direct, width=width, bottom=bottom_pv,
             color=COLORS["pv"], label="PV to HP (direct)")
    bottom_pv += kwh_direct
    ax_b.bar(x[0], kwh_chg, width=width, bottom=bottom_pv,
             color=COLORS["ess"], label="PV to ESS")
    bottom_pv += kwh_chg
    ax_b.bar(x[0], kwh_dump, width=width, bottom=bottom_pv,
             color=COLORS["muted"], label="PV to dump")

    # HP-load sources stack
    bottom_hp = 0.0
    ax_b.bar(x[1], kwh_direct, width=width, bottom=bottom_hp,
             color=COLORS["pv"])
    bottom_hp += kwh_direct
    ax_b.bar(x[1], kwh_dis, width=width, bottom=bottom_hp,
             color=COLORS["ess"], label="ESS to HP")
    bottom_hp += kwh_dis
    ax_b.bar(x[1], kwh_grid, width=width, bottom=bottom_hp,
             color=COLORS["accent"], label="Grid to HP")

    ax_b.set_xticks(x)
    ax_b.set_xticklabels(x_labels, fontsize=dm.fs(-1))
    ax_b.set_ylabel("Daily energy [kWh]")
    ax_b.set_title("(b) Daily energy ledger", loc="left", fontsize=dm.fs(0))
    ax_b.grid(True, alpha=0.25, linewidth=dm.lw(-2), axis="y")
    ax_b.legend(loc="upper left", frameon=False, fontsize=dm.fs(-2))

    # Totals annotation
    ax_b.text(
        x[0], bottom_pv + 0.2,
        f"{kwh_pv:.1f} kWh",
        ha="center", va="bottom",
        fontsize=dm.fs(-1), color=COLORS["ink"],
    )
    ax_b.text(
        x[1], bottom_hp + 0.2,
        f"{kwh_hp:.1f} kWh",
        ha="center", va="bottom",
        fontsize=dm.fs(-1), color=COLORS["ink"],
    )

    out = static_path("pv_ess_energy_balance.svg").with_suffix("")
    # mt bumped to 8% because the wide-aspect (6/12) canvas leaves
    # ``simple_layout`` undercounting the headroom needed by the
    # ``set_title(loc="left")`` text — the union bbox it measures
    # converges before the ``_left_title`` artist's final position is
    # accounted for, so the title overshoots the canvas top at 3%.
    finalize(fig, out, margin="3%", mt="8%")
    plt.close(fig)
    print(f"wrote {out}.svg")


if __name__ == "__main__":
    main()
