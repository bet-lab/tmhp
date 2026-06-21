"""Decision-relevance metrics for a control surrogate (pure NumPy, no cycle)."""

from __future__ import annotations

import numpy as np
import pytest

from tmhp.surrogate_eval import (
    disagreement_gaps,
    pairwise_ordering_agreement,
    selection_regret,
)


def test_perfect_surrogate_agrees_everywhere():
    t = np.array([1.0, 2.0, 3.0, 4.0])
    p = 0.5 * t + 10.0  # monotone transform preserves all orderings
    agree, n = pairwise_ordering_agreement(t, p)
    assert agree == 1.0
    assert n == 6  # C(4,2)
    assert disagreement_gaps(t, p).size == 0
    assert selection_regret(t, p) == 0.0


def test_single_flip_is_detected():
    t = np.array([1.0, 2.0, 3.0])
    p = np.array([1.0, 3.0, 2.0])  # swaps the order of the top two
    agree, n = pairwise_ordering_agreement(t, p)
    assert n == 3
    assert agree == pytest.approx(2 / 3)
    gaps = disagreement_gaps(t, p)
    assert gaps.size == 1
    assert gaps[0] == pytest.approx(1.0)  # |3 - 2|


def test_tol_excludes_near_ties():
    t = np.array([1.0, 1.0005, 5.0])
    p = np.array([1.0005, 1.0, 5.0])  # mis-ranks the near-tie only
    agree_no_tol, _ = pairwise_ordering_agreement(t, p, tol=0.0)
    agree_tol, n_tol = pairwise_ordering_agreement(t, p, tol=0.01)
    assert agree_no_tol < 1.0       # the near-tie counts as a disagreement
    assert agree_tol == 1.0         # ...but is excluded under tol
    assert n_tol == 2               # only the two clear pairs remain


def test_selection_regret_picks_surrogate_argmax():
    value_true = np.array([5.0, 4.8, 4.0])     # slot 0 is truly best
    value_pred = np.array([4.7, 5.0, 4.1])     # surrogate prefers slot 1
    # regret = best true (5.0) - true value of the surrogate's pick (4.8)
    assert selection_regret(value_true, value_pred) == pytest.approx(0.2)


def test_shape_validation():
    with pytest.raises(ValueError):
        pairwise_ordering_agreement(np.array([1.0, 2.0]), np.array([1.0]))
    with pytest.raises(ValueError):
        selection_regret(np.zeros((2, 2)), np.zeros((2, 2)))
