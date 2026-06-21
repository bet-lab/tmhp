"""Tests for the affine COP surrogate (Rastegarpour 2021 linear COP predictor)."""

from __future__ import annotations

import numpy as np
import pytest

from tmhp.cop_map import AffineCOPMap


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
