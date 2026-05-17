"""24-hour dynamic simulation timeseries for the ASHPB.

Runs a one-day ``analyze_dynamic`` with a realistic synthetic DHW
profile (morning + evening peaks) and a sinusoidal outdoor temperature.
Plots three stacked panels sharing the same time axis:

    a) tank water temperature with set-point bounds
    b) condenser heat rate and compressor electrical power
    c) instantaneous and running system COP

This is the canonical "what does a dynamic run produce?" figure for
the getting-started page.
"""

from __future__ import annotations

import sys
from pathlib import Path

import dartwork_mpl as dm
import matplotlib.pyplot as plt
import numpy as np

from tmhp import AirSourceHeatPumpBoiler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _dmpl_common import COLORS, apply_style, finalize, static_path  # noqa: E402

SIM_HOURS = 24
DT_S      = 60       # 1-minute step
N_STEPS   = SIM_HOURS * 3600 // DT_S
T_INIT_C  = 50.0     # start mid-band so the heat-up transient is short


def _dhw_profile(n: int) -> np.ndarray:
    """Synthetic DHW draw profile [m³/s] over a 24 h horizon."""
    t_h = np.arange(n) * DT_S / 3600.0
    # Two gaussian-shaped peaks: 07:00 shower, 20:00 dishes/shower.
    def peak(center_h: float, sigma_h: float, peak_lpm: float) -> np.ndarray:
        m3s_peak = peak_lpm / 60_000.0
        return m3s_peak * np.exp(-0.5 * ((t_h - center_h) / sigma_h) ** 2)
    return peak(7.0, 0.35, 12.0) + peak(20.0, 0.55, 8.0)


def _ambient_profile(n: int) -> np.ndarray:
    """Sinusoidal outdoor air [°C] — min at 06:00, max at 15:00."""
    t_h = np.arange(n) * DT_S / 3600.0
    return 7.0 + 6.0 * np.sin((t_h - 9.0) * np.pi / 12.0)


def main() -> None:
    apply_style("report", hashsalt="tmhp.visualization.dynamic-24h")

    ashpb = AirSourceHeatPumpBoiler(ref="R32")

    dhw = _dhw_profile(N_STEPS)
    t0  = _ambient_profile(N_STEPS)

    df = ashpb.analyze_dynamic(
        simulation_period_sec=SIM_HOURS * 3600,
        dt_s=DT_S,
        T_tank_w_init_C=T_INIT_C,
        dhw_usage_schedule=dhw,
        T0_schedule=t0,
    )

    t_h = np.arange(len(df)) * DT_S / 3600.0
    q_cond_kw = df["Q_ref_cond [W]"].to_numpy() / 1_000.0
    e_cmp_kw  = df["E_cmp [W]"].to_numpy() / 1_000.0
    t_tank    = df["T_tank_w [°C]"].to_numpy()

    # Running COP: cumulative Q_cond / cumulative E_cmp. Suppress the very
    # first samples where the denominator is zero or near-zero.
    cum_q = np.cumsum(q_cond_kw) * (DT_S / 3600.0)  # kWh
    cum_e = np.cumsum(e_cmp_kw)  * (DT_S / 3600.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        cop_running = np.where(cum_e > 0.05, cum_q / cum_e, np.nan)
    cop_inst = df["cop_sys [-]"].to_numpy()

    fig, (ax_t, ax_p, ax_c) = plt.subplots(
        3, 1,
        figsize=dm.figsize("15cm", "portrait"),
        sharex=True,
    )

    # --- (a) tank temperature ------------------------------------------
    ax_t.plot(t_h, t_tank, color=COLORS["hot"], linewidth=dm.lw(1),
              label="$T_{\\mathrm{tank,w}}$")
    ax_t.axhline(ashpb.T_tank_w_upper_bound, color=COLORS["muted"],
                 linewidth=dm.lw(0), linestyle=(0, (3, 3)))
    ax_t.axhline(ashpb.T_tank_w_lower_bound, color=COLORS["muted"],
                 linewidth=dm.lw(0), linestyle=(0, (3, 3)))
    ax_t.text(0.5, ashpb.T_tank_w_upper_bound + 0.5,
              f"upper {ashpb.T_tank_w_upper_bound:.0f} °C",
              color=COLORS["muted"], fontsize=dm.fs(-2))
    ax_t.text(0.5, ashpb.T_tank_w_lower_bound - 2.5,
              f"lower {ashpb.T_tank_w_lower_bound:.0f} °C",
              color=COLORS["muted"], fontsize=dm.fs(-2))
    ax_t.set_ylabel("Tank [°C]")
    ax_t.set_title("(a) Tank water temperature", loc="left",
                   fontsize=dm.fs(0))

    # --- (b) heat + power ---------------------------------------------
    ax_p.plot(t_h, q_cond_kw, color=COLORS["hot"],  linewidth=dm.lw(0),
              label="$\\dot Q_{\\mathrm{cond}}$")
    ax_p.plot(t_h, e_cmp_kw,  color=COLORS["accent"], linewidth=dm.lw(0),
              label="$E_{\\mathrm{cmp}}$")
    ax_p.fill_between(t_h, 0, q_cond_kw, color=COLORS["hot"], alpha=0.18,
                      linewidth=0)
    ax_p.fill_between(t_h, 0, e_cmp_kw, color=COLORS["accent"], alpha=0.22,
                      linewidth=0)
    ax_p.set_ylabel("Power [kW]")
    ax_p.legend(loc="upper right", frameon=False, ncol=2,
                fontsize=dm.fs(-1))
    ax_p.set_title("(b) Condenser heat & compressor power", loc="left",
                   fontsize=dm.fs(0))

    # --- (c) COP -------------------------------------------------------
    ax_c.plot(t_h, cop_inst, color=COLORS["accent2"], linewidth=dm.lw(-1),
              alpha=0.5, label="instantaneous")
    ax_c.plot(t_h, cop_running, color=COLORS["accent"], linewidth=dm.lw(1),
              label="running mean")
    ax_c.set_ylabel("$\\mathrm{COP}_{\\mathrm{sys}}$ [-]")
    ax_c.set_xlabel("Time of day [h]")
    ax_c.set_xlim(0, SIM_HOURS)
    ax_c.set_xticks(np.arange(0, SIM_HOURS + 1, 3))
    ax_c.legend(loc="upper right", frameon=False, ncol=2,
                fontsize=dm.fs(-1))
    ax_c.set_title("(c) System COP", loc="left", fontsize=dm.fs(0))

    for ax in (ax_t, ax_p, ax_c):
        ax.grid(True, alpha=0.25, linewidth=dm.lw(-2))

    out = static_path("dynamic_24h_timeseries.svg").with_suffix("")
    finalize(fig, out, margin="3%")
    plt.close(fig)
    print(f"wrote {out}.svg")


if __name__ == "__main__":
    main()
