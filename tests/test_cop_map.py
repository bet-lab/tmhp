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
