"""Reuse the CATALOGUE constant from samsung_ehs_parity and emit
docs/source/_static/data/validation-points.json with the same 15 points,
each evaluated by ASHPB so the docs widget reads off pre-computed numbers
instead of re-running the simulation in the browser.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
from samsung_ehs_parity import CATALOGUE  # noqa: E402

from tmhp import AirSourceHeatPumpBoiler  # noqa: E402

from scripts.data._common import write_json


def build_validation_points() -> list[dict]:
    ashpb = AirSourceHeatPumpBoiler(ref="R32")
    out: list[dict] = []
    for op in CATALOGUE:
        result = ashpb.analyze_steady(
            T_tank_w=op.t_tank_c, T0=op.t0_c, Q_ref_cond=op.q_cond_kw * 1000.0,
        )
        out.append({
            "case_id": op.id,
            "refrigerant": "R32",
            "t_source_c": op.t0_c,
            "t_sink_c": op.lwt_c,
            "t_tank_c": op.t_tank_c,
            "q_cat_kw": op.q_cond_kw,
            "q_mod_kw": result["Q_ref_cond [W]"] / 1000.0,
            "cop_cat": op.target_cop,
            "cop_mod": result["cop_sys [-]"],
            "failure_reason": result.get("failure_reason", "none"),
        })
    return out


def main() -> None:
    write_json("validation-points.json", build_validation_points())


if __name__ == "__main__":
    main()
