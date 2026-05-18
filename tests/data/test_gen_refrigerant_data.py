"""Tests for scripts/data/gen_refrigerant_data.py."""

from __future__ import annotations

import json
import pytest

from scripts.data.gen_refrigerant_data import (
    REFRIGERANTS,
    build_refrigerant_payload,
)


def test_supported_refrigerants():
    assert REFRIGERANTS == ("R32", "R290", "R134a", "R1234yf")


@pytest.mark.parametrize("ref", ["R32", "R290", "R134a", "R1234yf"])
def test_payload_top_level_shape(ref):
    payload = build_refrigerant_payload(ref)
    assert payload["refrigerant"] == ref
    assert {"saturation_dome", "isotherms", "cycle_grid"} <= payload.keys()


def test_saturation_dome_is_monotonic_in_pressure():
    payload = build_refrigerant_payload("R32")
    dome = payload["saturation_dome"]
    pressures_kpa = [pt["P_kpa"] for pt in dome]
    assert pressures_kpa == sorted(pressures_kpa), "dome must be sorted by P"


def test_saturation_dome_h_liquid_lt_h_vapor():
    payload = build_refrigerant_payload("R32")
    for pt in payload["saturation_dome"]:
        assert pt["h_liq_kjkg"] < pt["h_vap_kjkg"], pt


def test_cycle_grid_shape():
    payload = build_refrigerant_payload("R32")
    grid = payload["cycle_grid"]
    assert "t_evap_c" in grid and "t_cond_c" in grid
    assert "cop" in grid and "m_dot_kgs" in grid
    assert "q_cond_kw" in grid
    n_evap = len(grid["t_evap_c"])
    n_cond = len(grid["t_cond_c"])
    assert len(grid["cop"]) == n_evap
    assert len(grid["cop"][0]) == n_cond


def test_writes_per_refrigerant_files(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.data._common.DATA_DIR", tmp_path)
    from scripts.data.gen_refrigerant_data import main
    main()
    for ref in REFRIGERANTS:
        out = tmp_path / "refrigerants" / f"{ref}.json"
        assert out.exists(), out
        payload = json.loads(out.read_text())
        assert payload["refrigerant"] == ref
