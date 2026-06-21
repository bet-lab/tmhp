"""Finite-horizon economic MPC for the solar-routing decision.

The greedy router (:func:`~tmhp.gshpb_stc_routed.default_solar_router`) is myopic:
it serves the tank whenever it is below setpoint and lets the ground deplete
(``docs/solar_routing``). The economic value of charging the *ground* instead is
deferred — a warmer borehole raises the heat-pump source temperature and therefore
the COP of *future* operation (the affine map's ``a_src`` quantifies this) — so a
controller has to look ahead to see it.

This module solves that look-ahead exactly by dynamic programming over a lumped
ground-temperature state, using the affine COP map (validated decision-relevant in
``docs/g2_decision_relevance``) as the cost model. The decision each step is the
exclusive route ``ground``/``tank``/``off``; greedy is the horizon-1 special case.
The resulting schedule is injectable into the full plant
(:class:`~tmhp.gshpb_stc_routed.GSHPB_STC_routed`) through its ``solar_router``.

Reduced internal model (per step ``k``)
---------------------------------------
- ``COP_k = cop_map.cop(T_bhe_k, T_tank_set)`` (floored just above 1).
- tank heat the HP must supply: ``H_k = max(0, duty_k − [E_sol_k if route==tank])``.
- HP electricity: ``E_k = H_k / COP_k``; ground extraction ``Q_ext_k = H_k − E_k``.
- ground update: ``T_bhe_{k+1} = T_bhe_k + dt·([E_sol_k if route==ground] − Q_ext_k)/C_g``.
- stage cost: ``price_k · E_k`` (energy if price is flat).

This is the affine-LTV cost the program's MPC layer is built on; the ground state
makes routing a genuine sequential decision (charging accumulates), which is why
DP — not a per-step rule — is needed to value it.
"""

from __future__ import annotations

import numpy as np

from .cop_map import AffineCOPMap

_ROUTES = ("ground", "tank", "off")


class SolarRoutingMPC:
    """Look-ahead solar router via finite-horizon dynamic programming.

    Parameters
    ----------
    cop_map : AffineCOPMap
        COP cost model (source = ground temp, sink = tank setpoint).
    c_ground_j_per_k : float
        Lumped ground thermal capacitance [J/K] for the reduced state.
    dt_s : float
        Step length [s].
    t_tank_set : float
        Tank/condenser setpoint [°C] held fixed over the horizon.
    n_grid : int
        Number of discretised ground-temperature levels in the DP.
    cop_floor : float
        Lower clamp on COP to keep electricity finite.
    """

    def __init__(
        self,
        cop_map: AffineCOPMap,
        *,
        c_ground_j_per_k: float,
        dt_s: float,
        t_tank_set: float,
        n_grid: int = 121,
        cop_floor: float = 1.05,
    ) -> None:
        if cop_map.form != "source_sink":
            raise ValueError("SolarRoutingMPC needs a 'source_sink' COP map (source=ground, sink=tank)")
        self.cop = cop_map
        self.c_g = float(c_ground_j_per_k)
        self.dt = float(dt_s)
        self.t_tank_set = float(t_tank_set)
        self.n_grid = int(n_grid)
        self.cop_floor = float(cop_floor)

    # ------------------------------------------------------------------
    def _cop_at(self, t_bhe: np.ndarray) -> np.ndarray:
        cop = self.cop.cop(t_bhe, np.full_like(t_bhe, self.t_tank_set))
        return np.asarray(np.maximum(self.cop_floor, cop), dtype=float)

    def _stage(self, t_bhe: np.ndarray, duty: float, e_sol: float, route: str):
        """Vectorised stage cost + next ground temp for one route over a state grid."""
        sol_tank = e_sol if route == "tank" else 0.0
        sol_grnd = e_sol if route == "ground" else 0.0
        h_tank = np.maximum(0.0, duty - sol_tank)          # HP heat to tank [W]
        cop = self._cop_at(t_bhe)
        e_hp = h_tank / cop                                 # HP electricity [W]
        q_ext = h_tank - e_hp                               # ground extraction [W]
        q_net = sol_grnd - q_ext                            # net ground heat [W]
        t_next = t_bhe + self.dt * q_net / self.c_g
        return e_hp, t_next

    def plan(self, t_bhe0: float, duty, e_sol, price=None):
        """Optimal routing schedule by backward DP. Returns ``(routes, cost, traj)``.

        ``duty`` / ``e_sol`` are per-step arrays [W] (tank heat demand and available
        solar heat); ``price`` is a per-step weight (default flat = energy). Returns
        the route per step, the predicted electricity cost, and the ground-temp
        trajectory under the optimal plan.
        """
        duty = np.asarray(duty, dtype=float)
        e_sol = np.asarray(e_sol, dtype=float)
        H = duty.size
        price = np.ones(H) if price is None else np.asarray(price, dtype=float)

        # State grid spans the reachable ground-temperature range with margin.
        lo = min(t_bhe0, -60.0)
        hi = max(t_bhe0, 30.0)
        grid = np.linspace(lo, hi, self.n_grid)

        # Backward value iteration: J[k] = cost-to-go on the grid; A[k] = best route idx.
        J = np.zeros(self.n_grid)
        best_route = np.full((H, self.n_grid), -1, dtype=int)
        for k in range(H - 1, -1, -1):
            cand = np.full((len(_ROUTES), self.n_grid), np.inf)
            for ri, route in enumerate(_ROUTES):
                e_hp, t_next = self._stage(grid, float(duty[k]), float(e_sol[k]), route)
                # 'off'/'tank' are pointless without solar to place; allow but never cheaper.
                jto = np.interp(t_next, grid, J)            # cost-to-go after transition
                cand[ri] = price[k] * e_hp + jto
            best = np.argmin(cand, axis=0)
            best_route[k] = best
            J = np.take_along_axis(cand, best[None, :], axis=0)[0]

        # Forward roll-out from the true initial state.
        routes, traj = [], [t_bhe0]
        t = t_bhe0
        cost = 0.0
        for k in range(H):
            gi = int(np.argmin(np.abs(grid - t)))
            ri = int(best_route[k, gi])
            route = _ROUTES[ri]
            e_hp, t_next_arr = self._stage(np.array([t]), float(duty[k]), float(e_sol[k]), route)
            cost += float(price[k]) * float(e_hp[0])
            t = float(t_next_arr[0])
            routes.append(route)
            traj.append(t)
        return routes, cost, np.array(traj)

    def step(self, t_bhe_now: float, duty, e_sol, price=None) -> str:
        """Receding-horizon control move: the optimal *first* route from now.

        Call once per control step with the *current* measured ground temperature
        and the forecast for the remaining horizon. Re-planning each step lets the
        controller correct for forecast error and plant-model mismatch — the value
        of receding-horizon over committing to a single open-loop plan.
        """
        routes, _, _ = self.plan(t_bhe_now, duty, e_sol, price)
        return str(routes[0])

    def greedy(self, t_bhe0: float, duty, e_sol, price=None):
        """Myopic horizon-1 baseline (route minimising the immediate stage cost).

        Tie-break toward the tank, matching the deployed greedy default's bias.
        Returns ``(routes, cost, traj)`` in the same form as :meth:`plan`.
        """
        duty = np.asarray(duty, dtype=float)
        e_sol = np.asarray(e_sol, dtype=float)
        H = duty.size
        price = np.ones(H) if price is None else np.asarray(price, dtype=float)
        routes, traj = [], [t_bhe0]
        t = t_bhe0
        cost = 0.0
        order = ("tank", "ground", "off")  # tank-first tie-break
        for k in range(H):
            best_c, best_route, best_next = np.inf, "off", t
            for route in order:
                e_hp, t_next = self._stage(np.array([t]), float(duty[k]), float(e_sol[k]), route)
                c = float(price[k]) * float(e_hp[0])
                if c < best_c - 1e-12:
                    best_c, best_route, best_next = c, route, float(t_next[0])
            cost += best_c
            t = best_next
            routes.append(best_route)
            traj.append(t)
        return routes, cost, np.array(traj)
