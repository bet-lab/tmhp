"""Affine COP surrogate of the first-principles heat-pump cycle.

A fast, smooth, low-dimensional approximation of the (expensive) CoolProp
vapour-compression COP, for use as an MPC-internal model — following the linear
COP predictor of Rastegarpour et al. (*Performance improvement of an air-to-water
heat pump through linear time-varying MPC with adaptive COP predictor*, Journal
of Process Control 2021, 99:69-78). Two affine forms are supported:

- ``"source_sink"`` (their COP1): ``COP = a0 + a_src·T_source + a_sink·T_sink``
- ``"source"``      (their COP2): ``COP = b0 + b_src·T_source``

where ``T_source`` is the evaporator-side temperature and ``T_sink`` the
condenser-side temperature [°C]. The coefficients are fit by least squares to a
ground-truth COP grid; the map is C-infinity smooth and O(1) to evaluate, so it
is suited to a receding-horizon QP/LTV-MPC. An optional first-order lag and an
online (recursive least squares / Kalman) update are left to the controller
layer; this module provides the static fit + evaluation.

Heat source / heat sink are not fixed
-------------------------------------
The affine map is *agnostic* to which physical streams are the source and the
sink — it is parameterised purely by the two cycle-end temperatures. What the
"source" and "sink" denote depends on the unit and the operating mode, and is
filled in by a thin per-unit adapter, **not** by this module:

================  ===========================  ===========================
unit / mode       ``T_source`` (evaporator)    ``T_sink`` (condenser)
================  ===========================  ===========================
GSHP heating      ground / brine loop          tank water / supply
ASHP heating      outdoor air (the unit ``T0``) tank water / supply
A2A cooling       indoor / load air            outdoor air (heat reject)
================  ===========================  ===========================

In cooling the figure of merit is an EER and the source / sink roles swap
relative to heating, but the parameterisation is identical: a cooling adapter
simply feeds the (swapped) two temperatures into the same :meth:`from_grid`.
No core change is needed when the boiler-centric scope later grows to
air-to-air / air-to-water and to cooling — only a new adapter classmethod.

The generic fitting core is :meth:`from_grid` (takes any
``cop_fn(T_source, T_sink) -> cop``); :meth:`from_gshpb` and :meth:`from_ashpb`
are the ground- and air-source adapters that map the two abstract temperatures
onto each unit's ``analyze_steady`` signature.
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
    """Least-squares affine COP map fit to a ground-truth cycle.

    Heat-source/heat-sink agnostic: the map is fit and evaluated purely in terms
    of an evaporator-side ``T_source`` and a condenser-side ``T_sink``. Use
    :meth:`from_grid` with any ``cop_fn``, or the unit adapters
    :meth:`from_gshpb` / :meth:`from_ashpb`.
    """

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
    def from_grid(
        cls,
        cop_fn,
        t_source_vals,
        t_sink_vals,
        *,
        form: str = "source_sink",
        min_cop: float = 1.0,
    ) -> AffineCOPMap:
        """Fit the affine map from a generic COP function over a temperature grid.

        Heat-source/heat-sink agnostic core: ``cop_fn(T_source, T_sink) -> cop``
        is evaluated at every ``(T_source, T_sink)`` grid point (source outer,
        sink inner). A sample is kept only if its COP is finite and ``> min_cop``;
        ``cop_fn`` may also return ``None`` to signal a non-converged point. Any
        unit (GSHP, ASHP, future air-to-air / cooling) plugs in through its own
        ``cop_fn`` without touching this fit logic.
        """
        src, snk, cops = [], [], []
        for ts in t_source_vals:
            for tk in t_sink_vals:
                cop = cop_fn(ts, tk)
                if cop is not None and np.isfinite(cop) and cop > min_cop:
                    src.append(float(ts))
                    snk.append(float(tk))
                    cops.append(float(cop))
        if len(cops) < (2 if form == "source" else 3):
            raise RuntimeError("too few converged grid points to fit the COP map")
        return cls.fit(np.array(src), np.array(snk), np.array(cops), form=form)

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
        """Ground-source adapter: ``T_source`` = ground/brine loop, ``T_sink`` = tank water.

        Runs ``gshpb.analyze_steady`` at each grid point; non-converged or
        non-physical points (``cop_sys <= 1`` or non-finite) are dropped.
        """

        def _cop(ts: float, tk: float) -> float:
            r = gshpb.analyze_steady(T_tank_w=float(tk), T_source=float(ts), Q_ref_tank=Q_ref_tank, T0=T0)
            return float(r.get("cop_sys [-]", np.nan))

        return cls.from_grid(_cop, t_source_vals, t_sink_vals, form=form)

    @classmethod
    def from_ashpb(
        cls,
        ashpb,
        t_source_vals,
        t_sink_vals,
        *,
        Q_ref_tank: float = 8000.0,
        form: str = "source_sink",
    ) -> AffineCOPMap:
        """Air-source adapter: ``T_source`` = outdoor air (the unit's ``T0``), ``T_sink`` = tank water.

        Same affine map as :meth:`from_gshpb`, only the evaporator-side stream
        differs — here the source temperature is the ambient/outdoor air, fed to
        ``ashpb.analyze_steady`` as ``T0``. This is exactly the source/sink
        flexibility the affine form is designed to absorb.
        """

        def _cop(ts: float, tk: float) -> float:
            r = ashpb.analyze_steady(T_tank_w=float(tk), T0=float(ts), Q_ref_tank=Q_ref_tank)
            return float(r.get("cop_sys [-]", np.nan))

        return cls.from_grid(_cop, t_source_vals, t_sink_vals, form=form)

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
