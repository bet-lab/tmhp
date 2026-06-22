"""Characterization + contract tests for the BHE ground-coupling abstraction.

The default :class:`AggregateGFunctionCoupler` must reproduce the legacy inline
temporal superposition *byte-for-byte*, and the GSHPB integration must keep
producing the same BHE temperatures after delegating to the coupler. This is the
"self-only" regression gate for the G1 ground-coupling refactor.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest

# The default g-function precompute requires pygfunction; skip gracefully where
# it is unavailable (e.g. a minimal CI image) rather than failing.
pytest.importorskip("pygfunction")

from tmhp import GroundSourceHeatPumpBoiler  # noqa: E402
from tmhp.ground_coupling import AggregateGFunctionCoupler, GroundCoupler  # noqa: E402


def _gshpb() -> GroundSourceHeatPumpBoiler:
    return GroundSourceHeatPumpBoiler(
        ref="R32",
        N_1=2,
        N_2=1,
        H_b=100.0,
        dt_s=3600.0,
        t_max_s=200 * 3600,
    )


def _legacy_dT_sequence(
    g_interp: Callable[[np.ndarray], np.ndarray],
    time_arr: np.ndarray,
    q_seq: np.ndarray,
    tol: float = 1e-6,
) -> np.ndarray:
    """Verbatim replica of the legacy ``_compute_bhe_superposition`` dT loop.

    Serves as the independent oracle: the refactored coupler must match this
    sequence exactly for any load history.
    """
    pulses = np.zeros(len(q_seq))
    q_old = 0.0
    out = []
    for n, q in enumerate(q_seq):
        if abs(q - q_old) > tol:
            pulses[n] = q - q_old
            q_old = q
        idx = np.flatnonzero(pulses[: n + 1])
        if len(idx) > 0:
            dQ = pulses[idx]
            tau = np.maximum(time_arr[n] - time_arr[idx], 1e-6)
            out.append(float(np.dot(dQ, g_interp(tau))))
        else:
            out.append(0.0)
    return np.array(out)


@pytest.fixture(scope="module")
def gshpb() -> GroundSourceHeatPumpBoiler:
    return _gshpb()


def test_default_coupler_satisfies_protocol(gshpb):
    assert isinstance(gshpb._ground_coupler, AggregateGFunctionCoupler)
    assert isinstance(gshpb._ground_coupler, GroundCoupler)


def test_aggregate_coupler_byte_identical_to_legacy(gshpb):
    """The default coupler reproduces the legacy pulse-superposition exactly."""
    g = gshpb._gfunc_interp
    time_arr = np.arange(0, 100) * 3600.0
    rng = np.random.default_rng(0)
    # A load history with many on/off transitions exercises the pulse logic.
    q_seq = np.where(rng.random(100) < 0.5, 0.0, 40.0)

    ref = _legacy_dT_sequence(g, time_arr, q_seq)

    coupler = AggregateGFunctionCoupler(g)
    coupler.reset(len(q_seq), time_arr)
    got = np.array([coupler.wall_temperature_rise(n, time_arr, float(q)) for n, q in enumerate(q_seq)])
    assert np.array_equal(got, ref)


def test_injected_coupler_overrides_default():
    """A user-supplied coupler must replace the default backend."""
    seen: dict[str, int] = {}

    class _Spy:
        def reset(self, n_steps: int, time_arr: np.ndarray) -> None:
            seen["reset"] = n_steps

        def wall_temperature_rise(
            self,
            n: int,
            time_arr: np.ndarray,
            q_unit: float,
        ) -> float:
            return 0.0

    spy = _Spy()
    gshpb = GroundSourceHeatPumpBoiler(ref="R32", ground_coupler=spy)
    assert gshpb._ground_coupler is spy


# Golden captured from the pre-refactor inline implementation (config _gshpb();
# tN=16; DHW draws at steps 3,4,9,10; T_init=56°C; T0=15°C).
_GOLDEN = {
    "T_bhe [°C]": [
        16.0,
        16.0,
        16.0,
        16.0,
        15.999999996376145,
        2.9541246554140894,
        -4.247081881858133,
        2.4215236506163222,
        6.62973208801127,
        8.831490508103252,
        10.19053786741571,
        1.4724205372596337,
        5.17325806341926,
        7.9792640000650294,
        9.495330534883667,
        10.47963549792732,
    ],
    "T_bhe_f [°C]": [
        16.0,
        16.0,
        16.0,
        16.0,
        -53.522146250986765,
        -57.30029848497861,
        -4.247081881858151,
        2.4215236506163365,
        6.629732088011281,
        8.83149050810323,
        -41.19981525209076,
        1.4724205372596089,
        5.173258063419269,
        7.9792640000650294,
        9.495330534883692,
        10.479635497927347,
    ],
    "T_bhe_f_in [°C]": [
        16.0,
        16.0,
        16.0,
        16.0,
        -66.03450503224639,
        -68.14468406835698,
        -4.247081881858151,
        2.4215236506163365,
        6.629732088011281,
        8.83149050810323,
        -50.44887574339111,
        1.4724205372596089,
        5.173258063419269,
        7.9792640000650294,
        9.495330534883692,
        10.479635497927347,
    ],
    "T_bhe_f_out [°C]": [
        16.0,
        16.0,
        16.0,
        16.0,
        -41.009787469727144,
        -46.45591290160024,
        -4.247081881858151,
        2.4215236506163365,
        6.629732088011281,
        8.83149050810323,
        -31.950754760790403,
        1.4724205372596089,
        5.173258063419269,
        7.9792640000650294,
        9.495330534883692,
        10.479635497927347,
    ],
}


def test_analyze_dynamic_bhe_matches_golden():
    """End-to-end: the refactored plant reproduces the captured BHE outputs."""
    tN = 16
    dhw = np.zeros(tN)
    dhw[[3, 4, 9, 10]] = 6.0e-5
    T0 = np.full(tN, 15.0)

    gshpb = _gshpb()
    df = gshpb.analyze_dynamic(
        simulation_period_sec=tN * 3600.0,
        dt_s=3600.0,
        T_tank_w_init_C=56.0,
        dhw_usage_schedule=dhw,
        T0_schedule=T0,
    )

    for col, golden in _GOLDEN.items():
        assert col in df.columns
        np.testing.assert_allclose(df[col].to_numpy(), np.array(golden), rtol=0.0, atol=1e-12)
