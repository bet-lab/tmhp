"""G3 (closed loop) — receding-horizon routing under model-plant mismatch.

G3 found the controller's linear lumped-ground model *under-estimates* the
depletion: the real ground gets cold faster than the model predicts. An open-loop
plan, computed once on that optimistic model, therefore over-commits to the tank
and is surprised when the source depletes. Receding-horizon control closes the
loop: every step it measures the true ground temperature and re-plans, so state
feedback corrects for the model error the open-loop plan cannot see.

This experiment runs a plant whose ground capacitance is smaller (depletes faster)
than the controller's model, with a *perfect input forecast* so the only error is
the dynamics model. It compares greedy, open-loop MPC and receding-horizon MPC.

Run::

    .venv/bin/python docs/g3_routing_mpc/receding_horizon.py
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
T_TANK_SET = 55.0
COP = AffineCOPMap(np.array([4.6, 0.09, -0.045]), form="source_sink")

C_MODEL = 4.0e7  # capacitance the controller believes (optimistic — slow depletion)
C_PLANT = 1.5e7  # the real ground is smaller -> depletes faster than modelled


def _profiles():
    duty = np.zeros(N)
    e_sol = np.zeros(N)
    price = np.ones(N)
    for d in range(DAYS):
        h = d * 24
        duty[h:h + 24] = 1400.0
        duty[h + np.array([6, 7, 18, 19, 20])] += 4200.0
        e_sol[h + np.arange(8, 17)] = 2600.0
        price[h + np.arange(8, 18)] = 1.4
        price[h + np.arange(18, 23)] = 3.2
    return duty, e_sol, price


def _plant_stage(m, t, duty, e_sol, route, c_plant):
    sol_tank = e_sol if route == "tank" else 0.0
    sol_grnd = e_sol if route == "ground" else 0.0
    h_tank = max(0.0, duty - sol_tank)
    cop = max(m.cop_floor, float(m.cop.cop(t, m.t_tank_set)))
    e_hp = h_tank / cop
    q_net = sol_grnd - (h_tank - e_hp)
    return e_hp, t + m.dt * q_net / c_plant


def _closed_loop(m, t0, duty, e_sol, price, mode):
    t = t0
    cost = 0.0
    traj = [t0]
    routes_open = None if mode == "receding" else m.plan(t0, duty, e_sol, price)[0]
    for k in range(N):
        if mode == "greedy":
            route = m.greedy(t, duty[k:k + 1], e_sol[k:k + 1], price[k:k + 1])[0][0]
        elif mode == "receding":
            route = m.step(t, duty[k:], e_sol[k:], price[k:])
        else:
            route = routes_open[k]
        e_hp, t = _plant_stage(m, t, float(duty[k]), float(e_sol[k]), route, C_PLANT)
        cost += float(price[k]) * e_hp
        traj.append(t)
    return cost, np.array(traj)


def main() -> None:
    duty, e_sol, price = _profiles()
    m = SolarRoutingMPC(COP, c_ground_j_per_k=C_MODEL, dt_s=DT, t_tank_set=T_TANK_SET)

    out = {mode: _closed_loop(m, 4.0, duty, e_sol, price, mode)
           for mode in ("greedy", "open-loop", "receding")}
    base = out["greedy"][0]
    for mode, (cost, traj) in out.items():
        print(f"{mode:10s}: cost={cost:.0f}  ({100 * (1 - cost / base):+.1f}% vs greedy)  T_bhe end={traj[-1]:.1f}")
    print(f"receding recovers {out['open-loop'][0] - out['receding'][0]:.0f} cost over open-loop "
          f"({100 * (out['open-loop'][0] - out['receding'][0]) / out['open-loop'][0]:.1f}% of open-loop)")
    _plot(out)


def _plot(out) -> None:
    import dartwork_mpl as dm
    import matplotlib.pyplot as plt

    dm.style.use("scientific")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 2.9), gridspec_kw={"wspace": 0.34})

    t = np.arange(N) / 24.0
    cmap = {"greedy": "C3", "open-loop": "C1", "receding": "C2"}
    for mode, (_, traj) in out.items():
        ax1.plot(t, traj[:N], color=cmap[mode], lw=1.1, label=mode)
    ax1.set_xlabel("time [days]", fontsize=dm.fs(-1))
    ax1.set_ylabel("ground temp $T_{bhe}$ [°C]", fontsize=dm.fs(-1))
    ax1.set_title("closed-loop ground (plant depletes faster than model)", fontsize=dm.fs(-2))
    ax1.legend(fontsize=dm.fs(-3), frameon=False, loc="best")

    modes = list(out.keys())
    costs = [out[mname][0] for mname in modes]
    ax2.bar(np.arange(len(modes)), costs, color=[cmap[mname] for mname in modes], width=0.6)
    ax2.set_xticks(np.arange(len(modes)))
    ax2.set_xticklabels(modes, fontsize=dm.fs(-2))
    ax2.set_ylabel("closed-loop cost [-]", fontsize=dm.fs(-1))
    ax2.set_title("cost under model-plant mismatch", fontsize=dm.fs(-1))
    ax2.set_ylim(min(costs) * 0.95, max(costs) * 1.02)

    dm.simple_layout(fig, margin="2mm")
    dm.save_formats(fig, str(HERE / "fig2_receding_horizon"))
    print(f"saved {HERE / 'fig2_receding_horizon'}.pdf/.png")


if __name__ == "__main__":
    main()
