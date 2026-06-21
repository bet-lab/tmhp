"""Decision-relevance metrics for a COP (or any value) surrogate.

A control surrogate matters not by its pointwise error but by whether it preserves
the *decisions* a controller would make from it. These pure-NumPy helpers quantify
that: do the surrogate and the ground truth agree on which operating point is
better (ordering), and how much is lost when they disagree (regret)?

Used by ``docs/g2_decision_relevance`` to validate the affine COP map before it is
trusted inside an MPC (G3), but unit-agnostic — ``value`` can be COP, ``-cost``,
or any quantity a controller maximises.
"""

from __future__ import annotations

import numpy as np


def pairwise_ordering_agreement(value_true, value_pred, tol: float = 0.0):
    """Fraction of point pairs where surrogate and truth agree on which is better.

    For every unordered pair ``(i, j)``, the surrogate "agrees" if it ranks the two
    operating points the same way the ground truth does. Pairs whose true value gap
    is ``<= tol`` are treated as ties and excluded (a controller is indifferent
    there). Returns ``(agreement_fraction, n_pairs_considered)``.
    """
    t = np.asarray(value_true, dtype=float)
    p = np.asarray(value_pred, dtype=float)
    if t.shape != p.shape or t.ndim != 1:
        raise ValueError("value_true and value_pred must be 1-D arrays of equal length")
    iu, ju = np.triu_indices(t.size, k=1)
    dt = t[iu] - t[ju]
    dp = p[iu] - p[ju]
    keep = np.abs(dt) > tol
    if not keep.any():
        return 1.0, 0
    agree = np.sign(dt[keep]) == np.sign(dp[keep])
    return float(agree.mean()), int(keep.sum())


def disagreement_gaps(value_true, value_pred, tol: float = 0.0):
    """True value gaps ``|t_i - t_j|`` for the pairs the surrogate orders wrongly.

    Small gaps mean the surrogate only mis-ranks near-ties — cheap mistakes. The
    returned array is the regret-per-disagreement in true-value units.
    """
    t = np.asarray(value_true, dtype=float)
    p = np.asarray(value_pred, dtype=float)
    iu, ju = np.triu_indices(t.size, k=1)
    dt = t[iu] - t[ju]
    dp = p[iu] - p[ju]
    keep = np.abs(dt) > tol
    wrong = keep & (np.sign(dt) != np.sign(dp))
    return np.abs(dt[wrong])


def selection_regret(value_true, value_pred):
    """Regret from picking the argmax by the surrogate instead of the truth.

    A controller selects the operating point (timeslot, mode) the surrogate rates
    best; the regret is the true value it gives up versus the truly-best point::

        regret = max(value_true) - value_true[argmax(value_pred)]

    Zero when the surrogate's pick coincides with the true optimum. Returns a float
    in the units of ``value_true``.
    """
    t = np.asarray(value_true, dtype=float)
    p = np.asarray(value_pred, dtype=float)
    if t.shape != p.shape or t.ndim != 1:
        raise ValueError("value_true and value_pred must be 1-D arrays of equal length")
    return float(t.max() - t[int(np.argmax(p))])
