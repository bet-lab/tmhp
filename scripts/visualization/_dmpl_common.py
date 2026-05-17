"""Shared dartwork-mpl bootstrap for ``scripts/visualization/`` figures.

Every docs figure goes through this module so the typography, colour
palette, and on-disk paths stay consistent across the documentation. The
public surface is intentionally tiny: ``apply_style``, ``static_path``,
``finalize`` (layout + save), and ``COLORS``.
"""

from __future__ import annotations

from pathlib import Path

import dartwork_mpl as dm
import matplotlib as mpl
from matplotlib.figure import Figure

# Uniform buffer around the axes. ``margin=0`` (the dartwork default) snaps
# labels flush against the figure edge, which clips axis-edge tick labels on
# narrow figures — 2 % leaves room for the ``"-10"`` / ``"160"`` extremes
# without wasting headroom.
DEFAULT_MARGIN = "2%"


def finalize(fig: Figure, out_stem: Path, *, margin: str | float = DEFAULT_MARGIN,
             formats: tuple[str, ...] = ("svg",)) -> None:
    """Apply the standard layout buffer and save through ``dm.save_formats``.

    ``out_stem`` is a path without extension (``dm.save_formats`` appends
    them itself). ``margin`` is forwarded to ``dm.simple_layout`` — pass a
    smaller value (e.g. ``"1%"``) for ultra-tight gallery thumbnails.
    """
    dm.simple_layout(fig, margin=margin)
    dm.save_formats(fig, str(out_stem), formats=formats)


def apply_style(preset: str = "report", *, hashsalt: str | None = None) -> None:
    """Activate a dartwork-mpl composite preset for figure scripts.

    ``preset`` defaults to ``"report"`` (larger body-text-matching type,
    looser ticks), which reads better when embedded inside the Shibuya
    theme. Use ``"scientific"`` for tighter publication figures.
    ``hashsalt`` pins matplotlib's SVG clip-path IDs so re-running a
    script produces byte-identical output — pass a unique string per
    figure.
    """
    dm.style.use(preset)
    if hashsalt is not None:
        mpl.rcParams["svg.hashsalt"] = hashsalt


def static_path(name: str) -> Path:
    """Resolve ``docs/source/_static/<name>`` relative to the repo root."""
    repo_root = Path(__file__).resolve().parents[2]
    out = repo_root / "docs" / "source" / "_static" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


# Named tokens used across the docs figures. Keeping them here means every
# figure shares the same accent, refrigerant phase colours, and dim grey,
# which makes the gallery read as a single design system instead of seven
# unrelated plots.
COLORS = {
    "accent":   "oc.indigo6",   # primary line / scatter
    "accent2":  "oc.violet5",   # secondary series
    "warm":     "oc.orange6",   # ambient air / warm-side process
    "cool":     "oc.blue5",     # sat. liquid / cold-side process
    "hot":      "oc.red5",      # sat. vapour / discharge
    "ink":      "oc.gray8",     # node markers, axis ink
    "muted":    "oc.gray5",     # grids, secondary annotations
    "band20":   "oc.gray3",     # ±20 % band
    "band10":   "oc.blue2",     # ±10 % band
    "ess":      "oc.teal6",     # ESS / storage series
    "pv":       "oc.yellow6",   # PV irradiance / generation
    "load":     "oc.grape6",    # load / demand
}
