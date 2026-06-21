"""Online COP adaptation — RLS tracking of a drifting cycle + first-order lag.

A static `AffineCOPMap` is fit once and never moves. Real equipment drifts:
compressor fouling, refrigerant-charge loss, and ageing slowly lower the COP a
fixed map cannot follow. `OnlineCOPMap` adapts its coefficients by recursive
least squares with a forgetting factor, so the predictor tracks the drift.

Two demonstrations:
  A. A slowly degrading COP relation (offset and source-slope both decay). The
     static map's error grows; the RLS-adapted map stays accurate.
  B. The first-order lag smoothing a noisy per-step COP signal.

The drift here is synthetic but physically motivated (fouling/ageing), since the
CoolProp steady cycle has no time-dependent degradation — that is exactly the gap
the online update fills relative to the offline fit.

Run::

    .venv/bin/python docs/cop_map/online_adaptation.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tmhp.cop_map import AffineCOPMap, OnlineCOPMap

HERE = Path(__file__).resolve().parent

# Reproducible pseudo-random operating points / noise (Math.random is unavailable
# in workflow scripts, but this is a plain script — a seeded Generator is fine).
RNG = np.random.default_rng(0)
N = 600
DT = 60.0  # s between samples


def _true_coeffs(t_frac):
    """Ground-truth affine coeffs drifting with normalised time t_frac in [0, 1]."""
    a0 = 4.5 - 1.2 * t_frac        # offset decays (fouling)
    a_src = 0.13 - 0.04 * t_frac   # source sensitivity decays
    a_sink = -0.06                 # sink sensitivity steady
    return np.array([a0, a_src, a_sink])


def main() -> None:
    # operating points wander over the feasible envelope
    ts = 5.0 + 6.0 * np.sin(np.linspace(0, 12 * np.pi, N)) + RNG.normal(0, 1.0, N)
    tk = 50.0 + 5.0 * np.cos(np.linspace(0, 7 * np.pi, N)) + RNG.normal(0, 0.6, N)

    static = AffineCOPMap(_true_coeffs(0.0))           # fit at t=0, frozen
    online = OnlineCOPMap(_true_coeffs(0.0), lam=0.985, tau_s=180.0)

    err_static = np.empty(N)
    err_online = np.empty(N)
    cop_true = np.empty(N)
    cop_meas = np.empty(N)
    cop_lag = np.empty(N)
    for k in range(N):
        c = _true_coeffs(k / (N - 1))
        x = np.array([1.0, ts[k], tk[k]])
        true = float(x @ c)
        meas = true + RNG.normal(0, 0.05)              # measurement noise
        cop_true[k] = true
        cop_meas[k] = meas

        err_static[k] = static.cop(ts[k], tk[k]) - true
        cop_lag[k] = online.filtered_predict(ts[k], tk[k], DT)
        err_online[k] = online.predict(ts[k], tk[k]) - true
        online.update(ts[k], tk[k], meas)              # adapt to the plant

    rms_s = float(np.sqrt(np.mean(err_static[N // 2:] ** 2)))
    rms_o = float(np.sqrt(np.mean(err_online[N // 2:] ** 2)))
    print(f"second-half prediction RMSE  static={rms_s:.3f}  online(RLS)={rms_o:.3f}  "
          f"-> {rms_s / max(rms_o, 1e-9):.1f}x better")
    _plot(ts, tk, err_static, err_online, cop_true, cop_meas, cop_lag, rms_s, rms_o)


def _plot(ts, tk, err_static, err_online, cop_true, cop_meas, cop_lag, rms_s, rms_o) -> None:
    import dartwork_mpl as dm
    import matplotlib.pyplot as plt

    dm.style.use("scientific")
    n = len(err_static)
    t = np.arange(n) * DT / 3600.0  # hours

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 2.9), gridspec_kw={"wspace": 0.32})

    ax1.axhline(0.0, color="0.7", lw=0.6)
    ax1.plot(t, err_static, color="C3", lw=0.9, label=f"static (RMSE {rms_s:.2f})")
    ax1.plot(t, err_online, color="C2", lw=0.9, label=f"online RLS (RMSE {rms_o:.2f})")
    ax1.set_xlabel("time [h]", fontsize=dm.fs(-1))
    ax1.set_ylabel("COP prediction error [-]", fontsize=dm.fs(-1))
    ax1.set_title("tracking a drifting cycle", fontsize=dm.fs(-1))
    ax1.legend(fontsize=dm.fs(-3), frameon=False, loc="lower left")

    seg = slice(0, 120)  # zoom in to show the lag smoothing the noisy signal
    ax2.plot(t[seg], cop_meas[seg], color="0.6", lw=0.6, label="measured (noisy)")
    ax2.plot(t[seg], cop_lag[seg], color="C0", lw=1.2, label="first-order lag")
    ax2.plot(t[seg], cop_true[seg], color="k", lw=0.8, ls="--", label="true")
    ax2.set_xlabel("time [h]", fontsize=dm.fs(-1))
    ax2.set_ylabel("COP [-]", fontsize=dm.fs(-1))
    ax2.set_title("first-order lag smoothing", fontsize=dm.fs(-1))
    ax2.legend(fontsize=dm.fs(-3), frameon=False, loc="best")

    dm.simple_layout(fig, margin="2mm")
    dm.save_formats(fig, str(HERE / "fig2_online_adaptation"))
    print(f"saved {HERE / 'fig2_online_adaptation'}.pdf/.png")


if __name__ == "__main__":
    main()
