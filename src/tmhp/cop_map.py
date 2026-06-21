"""Affine COP surrogate of the first-principles heat-pump cycle.

A fast, smooth, low-dimensional approximation of the (expensive) CoolProp
vapour-compression COP, for use as an MPC-internal model — following the linear
COP predictor of Rastegarpour et al. (*Performance improvement of an air-to-water
heat pump through linear time-varying MPC with adaptive COP predictor*, Journal
of Process Control 2021, 99:69-78). Two affine forms are supported:

- ``"source_sink"`` (their COP1): ``COP = a0 + a_src·T_source + a_sink·T_sink``
- ``"source"``      (their COP2): ``COP = b0 + b_src·T_source``

where ``T_source`` is the evaporator-side (ground/air) temperature and
``T_sink`` the condenser-side (tank/supply) temperature [°C]. The coefficients
are fit by least squares to the ground-truth cycle
(:meth:`~tmhp.ground_source_heat_pump_boiler.GroundSourceHeatPumpBoiler.analyze_steady`)
over a temperature grid. The map is C-infinity smooth and O(1) to evaluate, so it
is suited to a receding-horizon QP/LTV-MPC. An optional first-order lag and an
online (recursive least squares / Kalman) update are left to the controller
layer; this module provides the static fit + evaluation.
"""

from __future__ import annotations

import numpy as np

_FORMS = ("source_sink", "source")


def _design(T_source: np.ndarray, T_sink: np.ndarray | None, form: str) -> np.ndarray:
    T_source = np.asarray(T_source, dtype=float)
    if form == "source":
        return np.column_stack([np.ones_like(T_source), T_source])
    if T_sink is None:
        raise ValueError("form 'source_sink' requires T_sink")
    T_sink = np.asarray(T_sink, dtype=float)
    return np.column_stack([np.ones_like(T_source), T_source, T_sink])


class AffineCOPMap:
    """Least-squares affine COP map fit to the CoolProp cycle."""

    def __init__(self, coeffs: np.ndarray, form: str = "source_sink") -> None:
        if form not in _FORMS:
            raise ValueError(f"form must be one of {_FORMS} — got {form!r}")
        self.coeffs = np.asarray(coeffs, dtype=float)
        self.form = form
        n = 2 if form == "source" else 3
        if self.coeffs.shape != (n,):
            raise ValueError(f"coeffs for form {form!r} must have shape ({n},) — got {self.coeffs.shape}")

    # ------------------------------------------------------------------
    @classmethod
    def fit(cls, T_source, T_sink, cop, form: str = "source_sink") -> AffineCOPMap:
        """Fit affine coefficients to scattered ``(T_source, T_sink) -> cop`` data."""
        cop = np.asarray(cop, dtype=float)
        X = _design(np.asarray(T_source, float), None if form == "source" else np.asarray(T_sink, float), form)
        coeffs, *_ = np.linalg.lstsq(X, cop, rcond=None)
        return cls(coeffs, form=form)

    @classmethod
    def from_gshpb(
        cls,
        gshpb,
        t_source_vals,
        t_sink_vals,
        *,
        Q_ref_tank: float = 8000.0,
        T0: float = 10.0,
        form: str = "source_sink",
    ) -> AffineCOPMap:
        """Generate a COP grid from the CoolProp cycle and fit the affine map.

        Runs ``gshpb.analyze_steady`` at each ``(T_source, T_sink)`` grid point;
        non-converged or non-physical points (``cop_sys <= 1`` or non-finite) are
        dropped before fitting.
        """
        src, snk, cops = [], [], []
        for ts in t_source_vals:
            for tk in t_sink_vals:
                r = gshpb.analyze_steady(T_tank_w=float(tk), T_source=float(ts), Q_ref_tank=Q_ref_tank, T0=T0)
                cop = float(r.get("cop_sys [-]", np.nan))
                if np.isfinite(cop) and cop > 1.0:
                    src.append(ts)
                    snk.append(tk)
                    cops.append(cop)
        if len(cops) < (2 if form == "source" else 3):
            raise RuntimeError("too few converged grid points to fit the COP map")
        return cls.fit(np.array(src), np.array(snk), np.array(cops), form=form)

    # ------------------------------------------------------------------
    def cop(self, T_source, T_sink=None):
        """Evaluate the affine COP (scalar or array)."""
        scalar = np.isscalar(T_source)
        Ts = np.atleast_1d(np.asarray(T_source, dtype=float))
        Tk = None if self.form == "source" else np.atleast_1d(np.asarray(T_sink, dtype=float))
        out = _design(Ts, Tk, self.form) @ self.coeffs
        return float(out[0]) if scalar else out

    def rmse(self, T_source, T_sink, cop_true) -> float:
        """Root-mean-square COP error against ground-truth samples."""
        pred = self.cop(T_source, T_sink if self.form == "source_sink" else None)
        return float(np.sqrt(np.mean((np.asarray(cop_true, float) - pred) ** 2)))
