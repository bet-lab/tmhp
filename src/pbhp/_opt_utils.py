"""Private helpers for SciPy OptimizeResult inspection.

`OptimizeResult.x` / `.fun` are typed `np.ndarray | float | None` in SciPy's
stubs, so plain `float(getattr(opt_result, "x", default))` blows up the static
type checker — and would raise `TypeError` at runtime if the optimiser
returned an empty/None result. These wrappers keep the call sites readable.
"""

from __future__ import annotations

__all__ = [
    "safe_float_attr",
]


def safe_float_attr(obj: object, name: str, default: float) -> float:
    """Read ``obj.name`` and coerce to ``float``, returning ``default`` if
    the attribute is missing, ``None``, or not numeric.

    Intended for ``OptimizeResult.x`` / ``OptimizeResult.fun`` where the
    optimiser may legitimately fail and leave the field unpopulated.
    """
    value = getattr(obj, name, None)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
