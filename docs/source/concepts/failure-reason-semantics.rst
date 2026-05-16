============================
``failure_reason`` semantics
============================

Every ``analyze_steady`` result carries a ``"failure_reason"`` key.
It's a diagnostic *report* — independent from whether the result
dict contains usable cycle numbers — and lets callers branch on
*why* a step looks the way it does without having to inspect cycle
internals.

The four values
===============

.. list-table::
    :header-rows: 1
    :widths: 25 35 40

    * - Value
      - Means
      - Result dict carries cycle numbers?
    * - ``"none"``
      - Cycle closed and the SciPy optimiser converged.
      - Yes — trust ``E_cmp``, ``Q_ref_*``, ``cop_*``.
    * - ``"hx_not_converged"``
      - HX residual exceeded tolerance, but the cycle itself
        produced a state.
      - Yes — numbers are usable but should be treated as
        approximate. ``converged == False``.
    * - ``"optimizer_failed"``
      - SciPy couldn't satisfy its own success criteria, even
        though the cycle returned a state.
      - Yes — numbers exist, but the evaporating-temperature
        choice is not provably optimal.
    * - ``"cycle_invalid"``
      - The cycle itself was infeasible at the requested
        operating point. The model falls back to off-mode
        (``E_cmp = 0``, ``Q_ref_cond = 0``).
      - No — only off-mode placeholders.

How to branch on it
===================

The safest pattern depends on which question you're asking.

**"Is this step physically meaningful?"** Use the cycle output
directly. Off-mode rows have ``E_cmp [W] == 0``:

.. code-block:: python

   ok = df["E_cmp [W]"] > 0

This is robust across all four ``failure_reason`` values and is
also the recommended check inside ``analyze_dynamic``, where
``failure_reason`` is per-step.

**"Did the model warn me about anything?"** Look at
``failure_reason`` directly:

.. code-block:: python

   from collections import Counter

   print(Counter(df["failure_reason"]))
   # e.g. Counter({'none': 1392, 'hx_not_converged': 47, 'cycle_invalid': 1})

**"Is this row trustworthy for a metric I care about?"** Combine
the converged flag with the failure reason:

.. code-block:: python

   trustworthy = (df["converged"]) & (df["failure_reason"] == "none")

What triggers each value
========================

These are implementation details and may shift between releases —
treat the four values themselves as the stable contract, not the
mechanism.

- **``"cycle_invalid"``** — ``_calc_state`` raised, or returned a
  non-dict, at the requested ``T_tank_w`` / ``T0`` / ``Q_ref_cond``.
  Usually a sign the requested duty is unreachable for the given
  geometry; consider increasing the design ε-NTU or fan flow.
- **``"hx_not_converged"``** — HX residual didn't drop below
  tolerance inside the inner iteration. Result is still usable;
  treat ``converged`` as the truth on this.
- **``"optimizer_failed"``** — the outer SciPy optimiser exited
  with ``success == False``. The cycle still has a state at the
  optimiser's best ``dT_ref_evap``, just not a provably optimal
  one.
- **``"none"``** — everything converged.

Off-mode fallback
=================

When ``failure_reason == "cycle_invalid"``, the steady-state path
emits a ``RuntimeWarning`` and substitutes an off-mode result:
``hp_is_on = False``, all power and duty fields zeroed. This keeps
``analyze_dynamic`` rows aligned (one row per step, regardless of
feasibility) so the resulting DataFrame is safe to vectorise over.

Where this is defined in the code
=================================

The diagnostic flag is set inside ``analyze_steady`` for the five
core models. See the docstrings under:

- :doc:`../api/models/ashpb`
- :doc:`../api/models/gshpb`
- :doc:`../api/models/wshpb`
- :doc:`../api/models/space-conditioning`
