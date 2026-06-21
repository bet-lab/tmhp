"""Tests for scripts/data/gen_refrigerant_data.py.

The module pre-computes vapour-compression cycle states for the client-side
SVG widget. Its public surface is :data:`REFRIGERANTS`,
:func:`build_saturation_curves`, and :func:`solve_cycle`; ``main`` sweeps the
full 8-parameter grid (too slow to exercise here). These tests cover the two
fast building blocks at the structural level.
"""

from __future__ import annotations

import CoolProp.CoolProp as CP
from scripts.data.gen_refrigerant_data import (
    REFRIGERANTS,
    build_saturation_curves,
    solve_cycle,
)


def test_supported_refrigerants():
    assert REFRIGERANTS == ["R410A", "R134a", "R32", "R290"]


def test_saturation_curves_shape_and_dome(monkeypatch):
    # Keep the dome sampling small so the test stays fast.
    monkeypatch.setattr(
        "scripts.data.gen_refrigerant_data.SAT_CURVE_POINTS", 50, raising=True
    )
    curves = build_saturation_curves("R32")
    expected_keys = {"T", "h_liq", "h_vap", "p_sat", "s_liq", "s_vap"}
    assert expected_keys <= curves.keys()

    n = len(curves["T"])
    assert n > 0
    assert all(len(curves[k]) == n for k in expected_keys)

    # Temperature axis is ascending and the vapour branch sits above the
    # liquid branch at every point below the critical point.
    assert curves["T"] == sorted(curves["T"])
    for h_l, h_v in zip(curves["h_liq"][:-1], curves["h_vap"][:-1], strict=True):
        assert h_l < h_v


def test_solve_cycle_returns_seven_points_for_reachable_point():
    t_crit_k = CP.PropsSI("Tcrit", "R32")
    t_min_k = CP.PropsSI("Tmin", "R32")
    # T_cond = 45 + 14000/2500 = 50.6 °C, well below R32 critical (~78 °C).
    pts = solve_cycle(
        refrigerant="R32",
        t_source_c=0.0,
        t_sink_c=45.0,
        dt_subcool=2.0,
        dt_superheat=3.0,
        q_cond_w=14000.0,
        ua_cond=2500.0,
        ua_evap=2000.0,
        t_crit_k=t_crit_k,
        t_min_k=t_min_k,
    )
    assert pts is not None
    assert len(pts) == 7
    for point in pts:
        assert len(point) == 4  # [h, T, P, s]


def test_solve_cycle_rejects_supercritical_condenser():
    t_crit_k = CP.PropsSI("Tcrit", "R32")
    t_min_k = CP.PropsSI("Tmin", "R32")
    # A huge condenser load with the same UA forces T_cond above the critical
    # point, which the solver must reject.
    pts = solve_cycle(
        refrigerant="R32",
        t_source_c=0.0,
        t_sink_c=45.0,
        dt_subcool=2.0,
        dt_superheat=3.0,
        q_cond_w=500000.0,
        ua_cond=2500.0,
        ua_evap=2000.0,
        t_crit_k=t_crit_k,
        t_min_k=t_min_k,
    )
    assert pts is None
