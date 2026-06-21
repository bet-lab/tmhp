"""Finite-horizon DP solar-routing MPC vs the myopic greedy baseline."""

from __future__ import annotations

import numpy as np
import pytest

from tmhp.cop_map import AffineCOPMap
from tmhp.solar_routing_mpc import SolarRoutingMPC

# COP rises with ground temp (a_src>0) — the reason ground charging pays off later.
COP = AffineCOPMap(np.array([4.0, 0.10, -0.05]), form="source_sink")


def _mpc(**kw):
    base = dict(c_ground_j_per_k=1.0e7, dt_s=3600.0, t_tank_set=50.0)
    base.update(kw)
    return SolarRoutingMPC(COP, **base)


def test_requires_source_sink_map():
    with pytest.raises(ValueError):
        SolarRoutingMPC(AffineCOPMap(np.array([4.0, 0.1]), form="source"),
                        c_ground_j_per_k=1e7, dt_s=3600.0, t_tank_set=50.0)


def test_plan_returns_valid_schedule():
    m = _mpc()
    H = 12
    duty = np.full(H, 3000.0)
    e_sol = np.where(np.arange(H) % 2 == 0, 2000.0, 0.0)
    routes, cost, traj = m.plan(t_bhe0=5.0, duty=duty, e_sol=e_sol)
    assert len(routes) == H
    assert set(routes) <= {"ground", "tank", "off"}
    assert traj.size == H + 1
    assert np.isfinite(cost)


def test_dp_is_never_worse_than_greedy():
    """DP is the optimal finite-horizon plan, so it never costs more than greedy."""
    m = _mpc()
    rng = np.random.default_rng(1)
    for _ in range(8):
        H = 16
        duty = rng.uniform(0.0, 4000.0, H)
        e_sol = rng.uniform(0.0, 3000.0, H) * (rng.random(H) > 0.4)
        _, c_dp, _ = m.plan(5.0, duty, e_sol)
        _, c_gr, _ = m.greedy(5.0, duty, e_sol)
        assert c_dp <= c_gr + 1e-6


def test_no_solar_makes_routing_irrelevant():
    m = _mpc()
    duty = np.full(10, 2500.0)
    e_sol = np.zeros(10)
    _, c_dp, _ = m.plan(0.0, duty, e_sol)
    _, c_gr, _ = m.greedy(0.0, duty, e_sol)
    assert c_dp == pytest.approx(c_gr)  # nothing to route -> identical cost


def test_lookahead_banks_solar_into_the_ground():
    """When early solar coincides with no tank demand, look-ahead charges the ground.

    Greedy wastes that solar (tank routing does nothing when duty=0) and lets the
    ground stay cold; the DP banks it, so later high-demand steps run at a higher
    COP and the DP plan is strictly cheaper.
    """
    m = _mpc()
    # early steps: strong solar, no tank demand; later steps: high demand, no solar
    duty = np.array([0, 0, 0, 0, 0, 0, 5000, 5000, 5000, 5000, 5000, 5000.0])
    e_sol = np.array([3000, 3000, 3000, 3000, 3000, 3000, 0, 0, 0, 0, 0, 0.0])
    routes_dp, c_dp, traj_dp = m.plan(0.0, duty, e_sol)
    routes_gr, c_gr, traj_gr = m.greedy(0.0, duty, e_sol)
    assert "ground" in routes_dp           # DP banks the early surplus
    assert c_dp < c_gr                      # and it pays off later
    assert traj_dp[6] > traj_gr[6]          # ground warmer when demand arrives
