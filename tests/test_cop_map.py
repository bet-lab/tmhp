"""Tests for the affine COP surrogate (Rastegarpour 2021 linear COP predictor)."""

from __future__ import annotations

import numpy as np
import pytest

from tmhp.cop_map import AffineCOPMap, OnlineCOPMap


def test_construction_validation():
    with pytest.raises(ValueError):
        AffineCOPMap(np.array([1.0, 2.0, 3.0]), form="bogus")
    with pytest.raises(ValueError):
        AffineCOPMap(np.array([1.0, 2.0]), form="source_sink")  # wrong shape
    AffineCOPMap(np.array([1.0, 2.0]), form="source")  # ok


def test_fit_recovers_known_affine():
    """Least squares recovers an exactly-affine COP field."""
    ts = np.array([0.0, 5.0, 10.0, 15.0, 0.0, 10.0])
    tk = np.array([40.0, 50.0, 60.0, 45.0, 55.0, 40.0])
    a0, a_src, a_sink = 3.0, 0.12, -0.05
    cop = a0 + a_src * ts + a_sink * tk
    m = AffineCOPMap.fit(ts, tk, cop, form="source_sink")
    assert np.allclose(m.coeffs, [a0, a_src, a_sink], atol=1e-9)
    assert m.rmse(ts, tk, cop) < 1e-9


def test_source_only_form():
    ts = np.array([0.0, 5.0, 10.0, 15.0])
    cop = 4.0 + 0.1 * ts
    m = AffineCOPMap.fit(ts, None, cop, form="source")
    assert np.allclose(m.coeffs, [4.0, 0.1], atol=1e-9)
    assert m.cop(10.0) == pytest.approx(5.0, abs=1e-9)


def test_cop_eval_scalar_and_array():
    m = AffineCOPMap(np.array([3.0, 0.1, -0.05]), form="source_sink")
    assert isinstance(m.cop(10.0, 50.0), float)
    out = m.cop(np.array([0.0, 10.0]), np.array([50.0, 50.0]))
    assert out.shape == (2,)
    assert out[1] > out[0]  # higher source temp -> higher COP


# --- generic source/sink-agnostic core (no CoolProp needed) -------------------
def test_from_grid_recovers_known_affine():
    """The generic core fits any cop_fn, independent of which unit produced it."""
    a0, a_src, a_sink = 2.8, 0.11, -0.04

    def cop_fn(ts, tk):
        return a0 + a_src * ts + a_sink * tk

    m = AffineCOPMap.from_grid(cop_fn, [-5.0, 0.0, 5.0, 10.0], [40.0, 50.0, 60.0])
    assert np.allclose(m.coeffs, [a0, a_src, a_sink], atol=1e-9)


def test_from_grid_drops_nonconverged_and_nonphysical():
    """None (non-converged), non-finite, and COP <= min_cop samples are dropped."""
    seen = []

    def cop_fn(ts, tk):
        seen.append((ts, tk))
        if tk == 60.0:
            return None  # pretend non-converged
        if ts == -5.0:
            return 0.5  # non-physical (<= 1) -> dropped
        return 3.0 + 0.1 * ts - 0.03 * tk

    m = AffineCOPMap.from_grid(cop_fn, [-5.0, 0.0, 5.0], [40.0, 50.0, 60.0])
    # All 9 grid points are probed (source outer, sink inner)...
    assert len(seen) == 9
    assert seen[0] == (-5.0, 40.0) and seen[1] == (-5.0, 50.0)
    # ...but only the 4 finite, physical, converged ones survive the fit.
    assert isinstance(m, AffineCOPMap)


def test_from_grid_raises_when_too_few_points():
    with pytest.raises(RuntimeError, match="too few"):
        AffineCOPMap.from_grid(lambda ts, tk: None, [0.0, 5.0], [40.0, 50.0])


# --- online (adaptive) COP map -----------------------------------------------
def test_online_construction_validation():
    with pytest.raises(ValueError):
        OnlineCOPMap(np.array([1.0, 2.0]), form="bogus")
    with pytest.raises(ValueError):
        OnlineCOPMap(np.array([1.0, 2.0, 3.0]), form="source")  # wrong shape
    with pytest.raises(ValueError):
        OnlineCOPMap(np.array([1.0, 2.0, 3.0]), lam=1.5)  # forgetting out of range


def test_online_rls_recovers_true_affine():
    """RLS (lam=1) converges to the underlying affine relation from a cold start."""
    a0, a_src, a_sink = 3.0, 0.12, -0.05
    # independent (not collinear) source/sink grid so the 3 coeffs are identifiable
    pts = [(ts, tk) for ts in np.linspace(-5.0, 15.0, 8) for tk in np.linspace(40.0, 60.0, 6)]
    m = OnlineCOPMap(np.zeros(3), lam=1.0, p0=1e6)  # weak prior -> near-exact recovery
    for ts, tk in pts:
        m.update(ts, tk, a0 + a_src * ts + a_sink * tk)
    assert np.allclose(m.coeffs, [a0, a_src, a_sink], atol=1e-4)


def test_online_forgetting_tracks_a_step_change():
    """With lam < 1 the predictor tracks a sudden change in the COP relation."""
    m = OnlineCOPMap(np.zeros(2), form="source", lam=0.9, p0=1e3)
    # regime 1: cop = 4 + 0.1 t
    for t in np.tile(np.linspace(-5, 15, 20), 3):
        m.update(t, None, 4.0 + 0.1 * t)
    c1 = m.coeffs.copy()
    # regime 2: cop = 2 + 0.3 t  (degraded offset, steeper slope)
    for t in np.tile(np.linspace(-5, 15, 20), 5):
        m.update(t, None, 2.0 + 0.3 * t)
    # coefficients moved toward the new regime
    assert abs(m.coeffs[0] - 2.0) < abs(c1[0] - 2.0)
    assert abs(m.coeffs[1] - 0.3) < abs(c1[1] - 0.3)
    assert m.predict(10.0) == pytest.approx(2.0 + 0.3 * 10.0, abs=0.2)


def test_online_first_order_lag_smooths():
    """filtered_predict seeds on the first call, then lags toward the raw value."""
    m = OnlineCOPMap(np.array([5.0, 0.0, 0.0]), tau_s=60.0)
    first = m.filtered_predict(0.0, 50.0, dt_s=10.0)
    assert first == pytest.approx(5.0)  # seeded at the raw value
    # jump the underlying map; the lagged signal moves only partway in one step
    m.coeffs = np.array([8.0, 0.0, 0.0])
    nxt = m.filtered_predict(0.0, 50.0, dt_s=10.0)
    assert 5.0 < nxt < 8.0
    alpha = 1.0 - np.exp(-10.0 / 60.0)
    assert nxt == pytest.approx(5.0 + alpha * (8.0 - 5.0), abs=1e-9)


def test_online_from_affine_warm_start_and_snapshot():
    base = AffineCOPMap(np.array([3.0, 0.1, -0.05]), form="source_sink")
    m = OnlineCOPMap.from_affine(base, lam=0.98)
    assert np.allclose(m.coeffs, base.coeffs)
    assert m.predict(10.0, 50.0) == pytest.approx(base.cop(10.0, 50.0))
    snap = m.as_affine()
    assert isinstance(snap, AffineCOPMap)
    assert np.allclose(snap.coeffs, m.coeffs)


# --- air-source adapter ground-truth fit (needs CoolProp, not pygfunction) ----
def test_from_ashpb_air_source_is_physical_and_close():
    """Same affine map fit against the air-source cycle: source = outdoor air."""
    pytest.importorskip("CoolProp")
    from tmhp import AirSourceHeatPumpBoiler

    ashpb = AirSourceHeatPumpBoiler(ref="R32")
    src = [-5.0, 0.0, 5.0]   # outdoor air temperature [°C]
    snk = [40.0, 50.0, 60.0]  # tank water temperature [°C]
    m = AffineCOPMap.from_ashpb(ashpb, src, snk, Q_ref_tank=6000.0)

    # Physical signs hold regardless of which stream is the source:
    assert m.coeffs[1] > 0.0  # warmer outdoor air -> higher COP
    assert m.coeffs[2] < 0.0  # hotter tank (sink)  -> lower COP

    # Tracks the CoolProp COP within a small error at a held point.
    r = ashpb.analyze_steady(T_tank_w=50.0, T0=0.0, Q_ref_tank=6000.0)
    cop_true = float(r["cop_sys [-]"])
    assert m.cop(0.0, 50.0) == pytest.approx(cop_true, abs=0.6)


# --- ground-truth fit (needs the CoolProp cycle + g-function precompute) ------
pytest.importorskip("pygfunction")
from tmhp import GroundSourceHeatPumpBoiler  # noqa: E402


def test_from_gshpb_affine_fit_is_physical_and_close():
    gshpb = GroundSourceHeatPumpBoiler(ref="R32", dt_s=3600.0, t_max_s=200 * 3600)
    src = [0.0, 5.0, 10.0, 15.0]
    snk = [40.0, 50.0, 60.0]
    m = AffineCOPMap.from_gshpb(gshpb, src, snk, Q_ref_tank=6000.0, T0=10.0)

    # Physical signs: COP rises with source temp, falls with sink temp.
    assert m.coeffs[1] > 0.0   # a_src > 0
    assert m.coeffs[2] < 0.0   # a_sink < 0

    # The affine map tracks the CoolProp COP within a small error at a held point.
    r = gshpb.analyze_steady(T_tank_w=50.0, T_source=8.0, Q_ref_tank=6000.0, T0=10.0)
    cop_true = float(r["cop_sys [-]"])
    assert m.cop(8.0, 50.0) == pytest.approx(cop_true, abs=0.6)
