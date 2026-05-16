"""Reproduce the parity plot from the KJACR 2026 (in press) validation paper.

Compares predictions from `AirSourceHeatPumpBoiler` against the 15 catalogue
operating points of the Samsung EHS Mono HT Quiet R32 14 kW unit, then writes a
publication-quality SVG figure to ``docs/source/_static/validation_parity.svg``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from physics_hp import AirSourceHeatPumpBoiler

# Pin clip-path IDs so re-running the script produces byte-identical SVG.
mpl.rcParams["svg.hashsalt"] = "physics-hp.validation.samsung-ehs-parity"


@dataclass(frozen=True)
class OperatingPoint:
    """One row of Samsung EHS catalogue Table 1."""

    id: int
    lwt_c: float
    t0_c: float
    q_cond_kw: float
    target_cop: float

    @property
    def t_tank_c(self) -> float:
        # Paper section 3: LWT - 2.5 K for LWT <= 60, LWT - 5 K for LWT > 60.
        if self.lwt_c <= 60.0:
            return self.lwt_c - 2.5
        return self.lwt_c - 5.0


CATALOGUE: tuple[OperatingPoint, ...] = (
    OperatingPoint(1, 40, -10, 13.45, 2.30),
    OperatingPoint(2, 40, 2, 12.42, 3.04),
    OperatingPoint(3, 40, 12, 14.65, 5.07),
    OperatingPoint(4, 40, 20, 15.69, 6.48),
    OperatingPoint(5, 40, 30, 16.98, 7.68),
    OperatingPoint(6, 50, -10, 13.89, 2.00),
    OperatingPoint(7, 50, 2, 13.27, 2.56),
    OperatingPoint(8, 50, 12, 14.76, 3.86),
    OperatingPoint(9, 50, 20, 15.97, 4.78),
    OperatingPoint(10, 50, 30, 17.48, 5.95),
    OperatingPoint(11, 65, -10, 13.96, 1.83),
    OperatingPoint(12, 65, 2, 13.59, 2.27),
    OperatingPoint(13, 65, 12, 15.55, 3.22),
    OperatingPoint(14, 65, 20, 16.76, 3.83),
    OperatingPoint(15, 65, 30, 18.27, 4.72),
)


def build_model() -> AirSourceHeatPumpBoiler:
    """Configure ASHPB with the parameter set from the paper's Table 2."""
    # Scroll compressor with clearance C = 0.035, k = 1.18 (R32).
    def eta_vol(pi: float) -> float:
        return float(1.0 - 0.035 * (pi ** (1.0 / 1.18) - 1.0))

    # Reference isentropic efficiency 0.90, decay 0.02 per unit pressure ratio.
    def eta_isen(pi: float) -> float:
        return 0.90 - 0.02 * pi

    # Combined motor + inverter efficiency, quadratic vs. rev/s (= Hz).
    def eta_mech(_pi: float, rps: float) -> float:
        return 0.90 - 6.25e-5 * (rps - 60.0) ** 2

    return AirSourceHeatPumpBoiler(
        ref="R32",
        V_disp_cmp=33.0e-6,
        eta_cmp_isen=eta_isen,
        eta_cmp_vol=eta_vol,
        eta_cmp_mech=eta_mech,
        dT_superheat=5.0,
        dT_subcool=5.0,
        UA_cond_design=2500.0,
        UA_evap_design=2000.0,
        n_evap=0.65,
        dV_ou_fan_a_design=1.5,
        dP_ou_fan_design=60.0,
        eta_ou_fan_design=0.6,
    )


def run_validation() -> list[tuple[OperatingPoint, float]]:
    model = build_model()
    rows: list[tuple[OperatingPoint, float]] = []
    for op in CATALOGUE:
        result = model.analyze_steady(
            T_tank_w=op.t_tank_c,
            T0=op.t0_c,
            Q_ref_cond=op.q_cond_kw * 1000.0,
            return_dict=True,
        )
        assert isinstance(result, dict)
        cop = float(result["cop_sys [-]"])
        rows.append((op, cop))
    return rows


def plot_parity(rows: list[tuple[OperatingPoint, float]], out_path: Path) -> None:
    target = np.array([op.target_cop for op, _ in rows])
    pred = np.array([cop for _, cop in rows])

    abs_err = np.abs(pred - target)
    mae = float(abs_err.mean())
    mape = float((abs_err / target).mean() * 100.0)

    lo, hi = 1.0, 8.0
    line = np.linspace(lo, hi, 200)

    fig, ax = plt.subplots(figsize=(6.0, 6.0))
    # ±20% and ±10% bands.
    ax.fill_between(line, 0.80 * line, 1.20 * line, color="#d6d6d6", alpha=0.55,
                    label="±20% Error", linewidth=0)
    ax.fill_between(line, 0.90 * line, 1.10 * line, color="#9ec8e8", alpha=0.55,
                    label="±10% Error", linewidth=0)
    ax.plot(line, line, linestyle=":", color="#3b4a5a", linewidth=1.2)

    ax.scatter(target, pred, s=42, color="#1f2a36", zorder=4, edgecolor="white",
               linewidth=0.6)
    for (op, cop) in rows:
        ax.annotate(str(op.id), (op.target_cop, cop),
                    textcoords="offset points", xytext=(6, -6), fontsize=8.5,
                    color="#1f2a36")

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Target COP")
    ax.set_ylabel("Predicted COP")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25, linewidth=0.6)
    ax.legend(loc="lower right", frameon=False, fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    # Pin the SVG metadata date so re-runs of this script produce
    # byte-identical output (avoids noisy diffs on regeneration).
    fig.savefig(
        out_path,
        format="svg",
        bbox_inches="tight",
        metadata={"Date": None},
    )
    plt.close(fig)

    print(f"MAE  = {mae:.3f}")
    print(f"MAPE = {mape:.2f}%")
    print(f"SVG  = {out_path}")


def render_markdown_table(rows: list[tuple[OperatingPoint, float]]) -> str:
    """Render a Markdown results table suitable for the README.

    Column headers use GitHub-flavored LaTeX (``$...$``) so the rendered table
    matches the symbols used in the paper and in the supporting modules.
    """
    target = np.array([op.target_cop for op, _ in rows])
    pred = np.array([cop for _, cop in rows])
    abs_err = np.abs(pred - target)
    pct_err = abs_err / target * 100.0
    mae = float(abs_err.mean())
    mape = float(pct_err.mean())

    header = (
        "| ID "
        "| $T_{\\mathrm{LWT}}$ [°C] "
        "| $T_0$ [°C] "
        "| $\\dot{Q}_{\\mathrm{cond}}$ [kW] "
        "| $\\mathrm{COP}_{\\mathrm{target}}$ "
        "| $\\mathrm{COP}_{\\mathrm{pred}}$ "
        "| AE "
        "| APE |\n"
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
    )

    def _fmt_t0(t: float) -> str:
        # Typographic minus so the column reads cleanly when rendered.
        return f"−{abs(t):.0f}" if t < 0 else f"{t:.0f}"

    body_lines = [
        (
            f"| {op.id} | {op.lwt_c:.0f} | {_fmt_t0(op.t0_c)} | {op.q_cond_kw:.2f} | "
            f"{op.target_cop:.2f} | {cop:.2f} | {ae:.2f} | {pe:.1f} % |"
        )
        for (op, cop), ae, pe in zip(rows, abs_err, pct_err, strict=True)
    ]
    footer = f"| | | | | | **Mean** | **{mae:.2f}** | **{mape:.1f} %** |"
    return "\n".join([header, *body_lines, footer])


def main() -> None:
    rows = run_validation()
    out = Path(__file__).resolve().parents[2] / "docs" / "source" / "_static" / "validation_parity.svg"
    plot_parity(rows, out)
    print()
    print("Markdown table (paste into README):")
    print(render_markdown_table(rows))


if __name__ == "__main__":
    main()
