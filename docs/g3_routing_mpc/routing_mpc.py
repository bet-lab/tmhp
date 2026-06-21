"""G3 — economic solar-routing MPC vs the myopic greedy router (reduced model).

The greedy router serves the tank whenever it is below setpoint and lets the
ground deplete (``docs/solar_routing``). Charging the *ground* instead pays off
later — a warmer borehole raises the heat-pump source temperature and the COP of
future operation (the affine map's ``a_src``) — so only a look-ahead controller
sees the value. :class:`~tmhp.solar_routing_mpc.SolarRoutingMPC` solves that
look-ahead exactly by dynamic programming over a lumped ground state with the
affine COP map (validated decision-relevant in ``docs/g2_decision_relevance``).

This experiment compares the DP plan against the myopic greedy baseline on the
MPC's internal model over a 5-day forecast with a time-of-use tariff. The
comparison is *exact and self-consistent* — both run on the same reduced model,
so the cost difference is attributable purely to the routing decision.

Full-plant closed-loop validation is deferred: the small 2×1 test field, pushed by
a 6 m² collector and frequent DHW draws, drives the CoolProp plant outside its
physical envelope (tank > 120 °C, source fluid < −100 °C), so a meaningful plant
comparison needs a properly-sized field and operating-envelope guards (next step,
toward a network-state MPC internal model that captures the depletion nonlinearity
the linear model misses).

Run::

    .venv/bin/python docs/g3_routing_mpc/routing_mpc.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tmhp.cop_map import AffineCOPMap
from tmhp.solar_routing_mpc import SolarRoutingMPC

HERE = Path(__file__).resolve().parent

DAYS = 5
N = DAYS * 24
DT = 3600.0
KWH = DT / 3.6e6
T_TANK_SET = 55.0

# Affine COP with a meaningful source sensitivity (ground charging raises COP).
COP = AffineCOPMap(np.array([4.6, 0.09, -0.045]), form="source_sink")


def _profiles():
    """Per-step tank heat demand [W], available solar heat [W], TOU price [-]."""
    duty = np.zeros(N)
    e_sol = np.zeros(N)
    price = np.ones(N)
    for d in range(DAYS):
        h = d * 24
        base = 1400.0  # standing loss the HP must cover every hour
        duty[h:h + 24] = base
        duty[h + np.array([6, 7, 18, 19, 20])] += 4200.0   # DHW draw heating
        e_sol[h + np.arange(8, 17)] = 2600.0               # daytime collector gain
        price[h + np.arange(8, 18)] = 1.4                  # daytime mid tariff (solar hours)
        price[h + np.arange(18, 23)] = 3.2                 # evening peak tariff (after solar)
    return duty, e_sol, price


def main() -> None:
    duty, e_sol, price = _profiles()
    mpc = SolarRoutingMPC(COP, c_ground_j_per_k=2.5e7, dt_s=DT, t_tank_set=T_TANK_SET)

    routes_dp, cost_dp, traj_dp = mpc.plan(t_bhe0=4.0, duty=duty, e_sol=e_sol, price=price)
    routes_gr, cost_gr, traj_gr = mpc.greedy(t_bhe0=4.0, duty=duty, e_sol=e_sol, price=price)

    # energy (price=1) for a transparent kWh figure alongside the priced cost
    _, e_dp, _ = mpc.plan(4.0, duty, e_sol)
    _, e_gr, _ = mpc.greedy(4.0, duty, e_sol)
    g_dp = sum(r == "ground" for r in routes_dp)
    g_gr = sum(r == "ground" for r in routes_gr)

    print(f"affine COP coeffs (a0,a_src,a_sink) = {COP.coeffs}")
    print(f"priced cost  : MPC={cost_dp:.1f} vs greedy={cost_gr:.1f}  ({100 * (1 - cost_dp / cost_gr):.1f}% less)")
    print(f"HP energy    : MPC={e_dp * KWH:.2f} kWh vs greedy={e_gr * KWH:.2f} kWh  "
          f"({100 * (1 - e_dp / e_gr):.1f}% less)")
    print(f"ground-routed: MPC={g_dp} steps vs greedy={g_gr};  "
          f"T_bhe end MPC={traj_dp[-1]:.1f} vs greedy={traj_gr[-1]:.1f} °C")

    _plot(traj_dp, traj_gr, routes_dp, routes_gr, e_sol, cost_dp, cost_gr)


def _plot(traj_dp, traj_gr, routes_dp, routes_gr, e_sol, cost_dp, cost_gr) -> None:
    import dartwork_mpl as dm
    import matplotlib.pyplot as plt

    dm.style.use("scientific")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 2.9), gridspec_kw={"wspace": 0.42})

    t = np.arange(N) / 24.0
    ax1.plot(t, traj_gr[:N], color="C3", lw=1.2, label=f"greedy (cost {cost_gr:.0f})")
    ax1.plot(t, traj_dp[:N], color="C2", lw=1.2, label=f"MPC (cost {cost_dp:.0f})")
    ax1.set_xlabel("time [days]", fontsize=dm.fs(-1))
    ax1.set_ylabel("ground temp $T_{bhe}$ [°C]", fontsize=dm.fs(-1))
    ax1.set_title("MPC banks solar -> warmer source", fontsize=dm.fs(-1))
    ax1.legend(fontsize=dm.fs(-3), frameon=False, loc="best")

    # routing per solar step: ground vs tank
    sol = e_sol > 0
    code = {"ground": 1, "tank": 0, "off": -1}
    rdp = np.array([code[r] for r in routes_dp])[sol]
    rgr = np.array([code[r] for r in routes_gr])[sol]
    xs = np.arange(rdp.size)
    ax2.step(xs, rgr, color="C3", lw=1.0, where="mid", label="greedy")
    ax2.step(xs, rdp, color="C2", lw=1.2, where="mid", label="MPC")
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["tank", "ground"], fontsize=dm.fs(-2))
    ax2.set_ylim(-0.4, 1.4)
    ax2.set_xlabel("solar step index", fontsize=dm.fs(-1))
    ax2.set_title("routing decision per solar step", fontsize=dm.fs(-1))
    ax2.legend(fontsize=dm.fs(-3), frameon=False, loc="center right")

    dm.simple_layout(fig, margin="2mm")
    dm.save_formats(fig, str(HERE / "fig1_routing_mpc"))
    print(f"saved {HERE / 'fig1_routing_mpc'}.pdf/.png")


if __name__ == "__main__":
    main()
