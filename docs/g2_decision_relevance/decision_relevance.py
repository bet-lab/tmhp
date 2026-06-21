"""G2 — is the affine COP surrogate *decision-relevant* vs the full cycle?

Before an MPC (G3) is allowed to optimise against the cheap affine COP map instead
of the expensive CoolProp cycle, we must check the surrogate preserves the
*decisions* the controller would make — not just its pointwise COP. Two tests on a
library of real GSHP operating points:

  A. Pairwise ordering: for every pair of operating points, do surrogate and cycle
     agree on which has the higher COP? Disagreements are characterised by the true
     COP gap they carry (cheap if the gap is small).
  B. Selection regret: a controller picks the operating point (timeslot / tank
     state) the surrogate rates best; the regret is the true COP it gives up vs the
     truly-best point. Aggregated over many random decision instances.

If agreement is high and regret is negligible, the affine map is decision-adequate
and G3 can trust it in the loop.

Run::

    OMP_NUM_THREADS=2 .venv/bin/python docs/g2_decision_relevance/decision_relevance.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tmhp import GroundSourceHeatPumpBoiler
from tmhp.cop_map import AffineCOPMap
from tmhp.surrogate_eval import (
    disagreement_gaps,
    pairwise_ordering_agreement,
    selection_regret,
)

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(0)

N_POINTS = 160     # random operating points (cycle evaluations)
N_INSTANCES = 4000  # random selection-decision instances
M_CANDIDATES = 6   # candidate operating points per decision
Q_REF = 6000.0
TOL = 0.02         # COP ties below this are controller-indifferent


def main() -> None:
    gshpb = GroundSourceHeatPumpBoiler(ref="R32", dt_s=3600.0, t_max_s=200 * 3600)

    # offline surrogate: coarse grid fit (what G3 would carry)
    surrogate = AffineCOPMap.from_gshpb(
        gshpb, [-2.0, 4.0, 10.0, 14.0], [38.0, 44.0, 50.0], Q_ref_tank=Q_REF, T0=10.0
    )

    # library of random operating points with their true (cycle) COP
    ts = RNG.uniform(-2.0, 14.0, N_POINTS)
    tk = RNG.uniform(38.0, 52.0, N_POINTS)
    cop_true, cop_surr = [], []
    for s, k in zip(ts, tk, strict=True):
        r = gshpb.analyze_steady(T_tank_w=float(k), T_source=float(s), Q_ref_tank=Q_REF, T0=10.0)
        c = float(r.get("cop_sys [-]", np.nan))
        if np.isfinite(c) and c > 1.0:
            cop_true.append(c)
            cop_surr.append(surrogate.cop(s, k))
    cop_true = np.array(cop_true)
    cop_surr = np.array(cop_surr)
    n = cop_true.size

    # A. pairwise ordering agreement
    agree, n_pairs = pairwise_ordering_agreement(cop_true, cop_surr, tol=TOL)
    gaps = disagreement_gaps(cop_true, cop_surr, tol=TOL)
    print(f"A. ordering agreement = {agree * 100:.1f}% over {n_pairs} pairs "
          f"({n} points); disagreements n={gaps.size}, "
          f"mean gap={gaps.mean() if gaps.size else 0:.3f}, max gap={gaps.max() if gaps.size else 0:.3f} COP")

    # B. selection regret over random M-candidate decision instances
    regrets = np.empty(N_INSTANCES)
    for i in range(N_INSTANCES):
        idx = RNG.choice(n, size=M_CANDIDATES, replace=False)
        regrets[i] = selection_regret(cop_true[idx], cop_surr[idx])
    pct = 100.0 * regrets / cop_true.mean()
    print(f"B. selection regret over {N_INSTANCES} instances (M={M_CANDIDATES}): "
          f"mean={regrets.mean():.4f} ({pct.mean():.2f}%), "
          f"95th={np.percentile(regrets, 95):.3f} ({np.percentile(pct, 95):.2f}%), "
          f"zero-regret picks={100.0 * (regrets < 1e-9).mean():.1f}%")

    _plot(cop_true, cop_surr, gaps, regrets, pct, agree)


def _plot(cop_true, cop_surr, gaps, regrets, pct, agree) -> None:
    import dartwork_mpl as dm
    import matplotlib.pyplot as plt

    dm.style.use("scientific")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 2.9), gridspec_kw={"wspace": 0.32})

    lo = min(cop_true.min(), cop_surr.min())
    hi = max(cop_true.max(), cop_surr.max())
    ax1.plot([lo, hi], [lo, hi], color="0.6", lw=0.8, ls="--", label="1:1")
    ax1.scatter(cop_true, cop_surr, s=10, color="C2", alpha=0.8)
    ax1.set_xlabel("true COP (CoolProp cycle) [-]", fontsize=dm.fs(-1))
    ax1.set_ylabel("surrogate COP (affine) [-]", fontsize=dm.fs(-1))
    ax1.set_title(f"ranking preserved — agreement {agree * 100:.1f}%", fontsize=dm.fs(-1))
    ax1.legend(fontsize=dm.fs(-3), frameon=False, loc="upper left")

    ax2.hist(pct, bins=40, color="C0", edgecolor="white", lw=0.3)
    ax2.axvline(pct.mean(), color="C3", lw=1.0, label=f"mean {pct.mean():.2f}%")
    ax2.set_xlabel("selection regret [% of COP]", fontsize=dm.fs(-1))
    ax2.set_ylabel("decision instances", fontsize=dm.fs(-1))
    ax2.set_title("regret of trusting the surrogate", fontsize=dm.fs(-1))
    ax2.legend(fontsize=dm.fs(-3), frameon=False, loc="upper right")

    dm.simple_layout(fig, margin="2mm")
    dm.save_formats(fig, str(HERE / "fig1_decision_relevance"))
    print(f"saved {HERE / 'fig1_decision_relevance'}.pdf/.png")


if __name__ == "__main__":
    main()
