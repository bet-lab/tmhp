"""Affine COP surrogate across heat source / heat sink configurations.

The affine map (Rastegarpour 2021) is parameterised purely by an evaporator-side
``T_source`` and a condenser-side ``T_sink`` — it does not care *which physical
stream* is the source. This experiment fits the same affine form against two
different units whose source stream is entirely different:

  - GSHP : source = ground / brine loop temperature  (``from_gshpb``)
  - ASHP : source = outdoor-air temperature          (``from_ashpb``)

For each unit we sweep the CoolProp cycle over a (source, sink) grid, fit the
affine map, and report how well the C-infinity affine surrogate tracks the
expensive ground-truth COP. The point is *generality*: one fitting core
(:meth:`AffineCOPMap.from_grid`) absorbs a moving heat source / heat sink behind
a thin per-unit adapter, which is what an MPC needs when the same controller
serves air-to-water today and air-to-air / cooling later.

Run::

    OMP_NUM_THREADS=2 .venv/bin/python docs/cop_map/compare_hp_cop_maps.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tmhp import AirSourceHeatPumpBoiler, GroundSourceHeatPumpBoiler
from tmhp.cop_map import AffineCOPMap

HERE = Path(__file__).resolve().parent

Q_REF = 6000.0  # condenser target heat rate [W]

# Source-stream temperatures differ by unit; sink (tank water) is shared.
GSHP_SRC = [-2.0, 2.0, 6.0, 10.0, 14.0]   # ground / brine loop [°C]
ASHP_SRC = [-10.0, -5.0, 0.0, 5.0, 10.0]  # outdoor air [°C]
SINK = [35.0, 40.0, 45.0, 50.0]           # tank water [°C]


def sweep(cop_fn, src_vals, sink_vals):
    """Return converged (src, sink, cop) ground-truth samples over the grid."""
    src, snk, cop = [], [], []
    for ts in src_vals:
        for tk in sink_vals:
            c = cop_fn(ts, tk)
            if c is not None and np.isfinite(c) and c > 1.0:
                src.append(ts)
                snk.append(tk)
                cop.append(c)
    return np.array(src), np.array(snk), np.array(cop)


def main() -> None:
    gshpb = GroundSourceHeatPumpBoiler(ref="R32", dt_s=3600.0, t_max_s=200 * 3600)
    ashpb = AirSourceHeatPumpBoiler(ref="R32")

    def gshp_cop(ts, tk):
        r = gshpb.analyze_steady(T_tank_w=float(tk), T_source=float(ts), Q_ref_tank=Q_REF, T0=10.0)
        return float(r.get("cop_sys [-]", np.nan))

    def ashp_cop(ts, tk):
        r = ashpb.analyze_steady(T_tank_w=float(tk), T0=float(ts), Q_ref_tank=Q_REF)
        return float(r.get("cop_sys [-]", np.nan))

    units = []
    for name, cop_fn, src_vals in (
        ("GSHP (source = ground)", gshp_cop, GSHP_SRC),
        ("ASHP (source = outdoor air)", ashp_cop, ASHP_SRC),
    ):
        gx, sx, cx = sweep(cop_fn, src_vals, SINK)
        m = AffineCOPMap.fit(gx, sx, cx, form="source_sink")
        rmse = m.rmse(gx, sx, cx)
        maxerr = float(np.max(np.abs(cx - m.cop(gx, sx))))
        units.append((name, cop_fn, src_vals, gx, sx, cx, m, rmse, maxerr))
        print(f"{name}: n={len(cx)}  coeffs(a0,a_src,a_sink)={m.coeffs.round(4)}  "
              f"RMSE={rmse:.3f}  max|err|={maxerr:.3f}")

    _plot(units)


def _plot(units) -> None:
    import dartwork_mpl as dm
    import matplotlib.pyplot as plt

    dm.style.use("scientific")
    colors = ["C0", "C1", "C2", "C3"]

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for ax, (name, _cop_fn, src_vals, gx, sx, cx, m, rmse, maxerr) in zip(axes, units, strict=True):
        src_line = np.linspace(min(src_vals), max(src_vals), 60)
        for tk, col in zip(SINK, colors, strict=False):
            # ground-truth markers
            mask = np.isclose(sx, tk)
            if mask.any():
                ax.scatter(gx[mask], cx[mask], s=14, color=col, zorder=3,
                           label=f"CoolProp, sink {tk:.0f}°C")
            # affine surrogate line
            ax.plot(src_line, m.cop(src_line, np.full_like(src_line, tk)),
                    color=col, lw=1.0, zorder=2)
        ax.set_xlabel("source temperature [°C]", fontsize=dm.fs(-1))
        ax.set_ylabel("system COP [-]", fontsize=dm.fs(-1))
        ax.set_title(f"{name}\nRMSE={rmse:.3f}, max|err|={maxerr:.3f}", fontsize=dm.fs(-1))
        ax.legend(fontsize=dm.fs(-3), frameon=False, loc="best", ncol=1)

    dm.simple_layout(fig, margin="2mm")
    dm.save_formats(fig, str(HERE / "fig1_cop_source_sink"))
    print(f"saved {HERE / 'fig1_cop_source_sink'}.pdf/.png")


if __name__ == "__main__":
    main()
