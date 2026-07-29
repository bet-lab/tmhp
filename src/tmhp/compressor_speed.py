"""Compressor speed-envelope guard (capacity based).

A variable-speed compressor can only deliver duties inside the band spanned by
its speed range. Below ``rps_min`` the machine still turns at ``rps_min``; it
does not stop modulating and it does not fail. Asking such a machine for less
than that minimum is therefore an ordinary operating situation -- a real
inverter unit answers it by running at its floor and cycling on/off -- not a
numerical failure.

The speed search itself is a one-dimensional root find on

    residual(rps) = Q_delivered(rps) - Q_request

which is monotonically increasing in ``rps``. When the requested duty lies
outside the deliverable band the residual keeps the same sign across the whole
interval, so a bracketing solver such as :func:`scipy.optimize.brentq` has no
root to find and raises. That exception means *the solution is outside the
interval*, which is a statement about the machine, not about the solver.

:func:`solve_compressor_speed` separates the two cases. Out-of-band requests are
**clamped** onto the nearest speed bound and reported as converged, tagged with
:data:`CAPACITY_CLAMPED_MIN` / :data:`CAPACITY_CLAMPED_MAX` so callers can tell
that the delivered duty differs from the requested one. Only a genuine solver
breakdown inside a valid bracket is reported as non-converged.

This mirrors the floor/ceiling split already used for the pressure-ratio
envelope in :mod:`tmhp.compressor_envelope`, and is shared by every heat-pump
model that solves for compressor speed so the semantics stay consistent.
"""

from __future__ import annotations

from collections.abc import Callable

from scipy.optimize import brentq

__all__ = [
    "solve_compressor_speed",
    "default_displacement",
    "CAPACITY_CLAMPED_MIN",
    "CAPACITY_CLAMPED_MAX",
    "DISPLACEMENT_PER_W",
]

#: Clamp code: request below the duty deliverable at ``rps_min``.
CAPACITY_CLAMPED_MIN = "min"
#: Clamp code: request above the duty deliverable at ``rps_max``.
CAPACITY_CLAMPED_MAX = "max"

#: Swept displacement per watt of nominal heating capacity [m^3/rev per W].
#:
#: Taken from the Panasonic Aquarea WH-MXC09J3E8 (R32, 9 kW nominal,
#: 42.0 cm^3/rev): ``42.0e-6 / 9000``. Catalogue displacements for the 9-16 kW
#: air-to-water range sit within roughly a factor of two of this figure, so it
#: is a defensible placeholder for a machine whose displacement the caller has
#: not specified.
#:
#: Displacement and ``rps_min`` jointly fix the lowest duty a machine can
#: deliver: an oversized displacement makes the minimum capacity a large
#: fraction of nameplate, which shows up as a machine that cannot modulate.
#: Sizing the default from the nominal capacity keeps the two consistent.
DISPLACEMENT_PER_W = 42.0e-6 / 9000.0


def default_displacement(hp_capacity: float) -> float:
    """Swept compressor displacement [m^3/rev] implied by a nominal capacity."""
    return hp_capacity * DISPLACEMENT_PER_W


def solve_compressor_speed(
    residual: Callable[[float], float],
    rps_min: float,
    rps_max: float,
) -> tuple[float, bool, str | None]:
    """Solve for the compressor speed that meets a requested duty.

    Parameters
    ----------
    residual
        ``residual(rps) = Q_delivered(rps) - Q_request`` [W]. Must be
        monotonically increasing in ``rps``.
    rps_min, rps_max
        Compressor speed search bounds [rev/s].

    Returns
    -------
    tuple[float, bool, str | None]
        ``(rps, converged, capacity_clamped)``.

        ``capacity_clamped`` is :data:`CAPACITY_CLAMPED_MIN` when the request
        was below the duty available at ``rps_min`` (the machine delivers more
        than asked), :data:`CAPACITY_CLAMPED_MAX` when it was above the duty
        available at ``rps_max`` (the machine delivers less than asked), and
        ``None`` when the request was met exactly. ``converged`` is ``False``
        only when the request lies inside the deliverable band yet the root
        find still failed, which indicates a numerical problem.
    """
    res_min = residual(rps_min)
    if res_min > 0.0:
        return rps_min, True, CAPACITY_CLAMPED_MIN
    if res_min == 0.0:
        return rps_min, True, None

    res_max = residual(rps_max)
    if res_max < 0.0:
        return rps_max, True, CAPACITY_CLAMPED_MAX
    if res_max == 0.0:
        return rps_max, True, None

    try:
        return brentq(residual, rps_min, rps_max), True, None
    except ValueError:
        # The residual changes sign across the interval, so a root exists and
        # the solver should have found it. Report the failure honestly.
        rps = rps_min if abs(res_min) < abs(res_max) else rps_max
        return rps, False, None
