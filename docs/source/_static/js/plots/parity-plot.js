/**
 * ② Interactive parity plot — Samsung EHS catalogue (15 points, R32).
 *
 * Mirrors the style of scripts/validation/samsung_ehs_parity.py
 * (the Python figure that produces validation_parity.svg):
 *   - axes are COP_target vs COP_pred, locked to [1, 8] square
 *   - ±20 % band (light gray) and ±10 % band (light blue) behind
 *   - dotted y = x reference
 *   - white-edged scatter with the case id annotated next to each dot
 *   - inline MAE / MAPE in the upper-left
 *   - subtle grid + lower-right legend
 *
 * Reads /_static/data/validation-points.json. Hovering a dot fires a
 * 'tmhp:parity-selected' CustomEvent (consumed by ④ validation-table);
 * clicking pins the selection. Listens for 'tmhp:table-selected' to
 * highlight the matching dot when the table dispatches.
 */
(function () {
  "use strict";
  const mount = document.getElementById("parity-plot-mount");
  if (!mount) return;
  if (!window.tmhpPlot) {
    console.warn("parity-plot: tmhpPlot helpers missing — load _plot-common.js first");
    return;
  }
  const { tokens, loadJson, staticDir } = window.tmhpPlot;

  // OpenColor tokens used by the Python figure (see scripts/visualization/_dmpl_common.py).
  const BAND20 = "#dee2e6";  // oc.gray3
  const BAND10 = "#a5d8ff";  // oc.blue2

  mount.classList.add("tmhp-plot-mount", "parity-plot");
  mount.innerHTML = `
    <svg class="parity-canvas" viewBox="0 0 520 520" preserveAspectRatio="xMidYMid meet"></svg>
  `;
  const svg = mount.querySelector("svg.parity-canvas");

  (async () => {
    const points = await loadJson(`${staticDir()}/data/validation-points.json`);
    const t = tokens();

    const W = 520, H = 520;
    const margin = { top: 30, right: 20, bottom: 50, left: 60 };
    const iw = W - margin.left - margin.right;
    const ih = H - margin.top - margin.bottom;

    // Fixed [1, 8] domain matches the Python figure (paper's COP range).
    const lo = 1.0, hi = 8.0;
    const x = d3.scaleLinear().domain([lo, hi]).range([0, iw]);
    const y = d3.scaleLinear().domain([lo, hi]).range([ih, 0]);

    // MAE / MAPE on COP — matches the Python figure's inline text.
    const targets = points.map(p => p.cop_cat);
    const preds   = points.map(p => p.cop_mod);
    const absErr  = preds.map((v, i) => Math.abs(v - targets[i]));
    const mae  = absErr.reduce((s, v) => s + v, 0) / absErr.length;
    const mape = absErr.reduce((s, v, i) => s + v / targets[i], 0) / absErr.length * 100;

    const svgSel = d3.select(svg);
    const root = svgSel.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // ±20 % and ±10 % error bands (drawn first, sit behind everything).
    const NB = 60;
    const lineXs = d3.range(NB).map(i => lo + (hi - lo) * i / (NB - 1));
    const band = (frac) => d3.area()
      .x(d => x(d))
      .y0(d => y(d * (1 - frac)))
      .y1(d => y(d * (1 + frac)));
    root.append("path").attr("d", band(0.20)(lineXs))
      .attr("fill", BAND20).attr("fill-opacity", 0.55).attr("stroke", "none");
    root.append("path").attr("d", band(0.10)(lineXs))
      .attr("fill", BAND10).attr("fill-opacity", 0.45).attr("stroke", "none");

    // Subtle grid (alpha-25 lines, behind the diagonal).
    root.append("g").attr("class", "axis grid")
      .attr("transform", `translate(0,${ih})`)
      .call(d3.axisBottom(x).ticks(8).tickSize(-ih).tickFormat(""))
      .selectAll("line").attr("stroke", t.hairline).attr("stroke-opacity", 0.6);
    root.append("g").attr("class", "axis grid")
      .call(d3.axisLeft(y).ticks(8).tickSize(-iw).tickFormat(""))
      .selectAll("line").attr("stroke", t.hairline).attr("stroke-opacity", 0.6);

    // y = x reference (dotted, muted).
    root.append("line")
      .attr("x1", x(lo)).attr("y1", y(lo))
      .attr("x2", x(hi)).attr("y2", y(hi))
      .attr("stroke", t.muted).attr("stroke-width", 1)
      .attr("stroke-dasharray", "2 3");

    // Axes (drawn after the grid so tick labels sit on top).
    root.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${ih})`)
      .call(d3.axisBottom(x).ticks(8).tickFormat(d3.format(".1f")))
      .append("text").attr("x", iw / 2).attr("y", 40)
      .attr("text-anchor", "middle").attr("fill", t.muted)
      .text("Target COP [-]");
    root.append("g").attr("class", "axis")
      .call(d3.axisLeft(y).ticks(8).tickFormat(d3.format(".1f")))
      .append("text")
      .attr("transform", "rotate(-90)").attr("x", -ih / 2).attr("y", -42)
      .attr("text-anchor", "middle").attr("fill", t.muted)
      .text("Predicted COP [-]");

    let selectedId = null;

    // Scatter — white-edged dots, accent fill.
    const groups = root.selectAll("g.pt").data(points).enter().append("g")
      .attr("class", "pt")
      .attr("transform", d => `translate(${x(d.cop_cat)},${y(d.cop_mod)})`)
      .style("cursor", "pointer");

    groups.append("circle")
      .attr("r", 5).attr("fill", t.accent)
      .attr("stroke", "#fff").attr("stroke-width", 1.2);

    // Case id annotation, offset (3, -3) — matches the Python figure.
    groups.append("text")
      .attr("x", 6).attr("y", -4).attr("fill", t.ink)
      .attr("font-size", 11).attr("font-weight", 500)
      .text(d => d.case_id);

    // Inline MAE / MAPE in the upper-left (transform (0.04, 0.04) of axes).
    root.append("text").attr("class", "parity-stats")
      .attr("x", 8).attr("y", 14)
      .attr("fill", t.ink).attr("font-size", 12)
      .style("font-variant-numeric", "tabular-nums")
      .text(`MAE  = ${mae.toFixed(2)}`);
    root.append("text").attr("class", "parity-stats")
      .attr("x", 8).attr("y", 30)
      .attr("fill", t.ink).attr("font-size", 12)
      .style("font-variant-numeric", "tabular-nums")
      .text(`MAPE = ${mape.toFixed(1)} %`);

    // Lower-right legend.
    const legend = root.append("g")
      .attr("transform", `translate(${iw - 110},${ih - 50})`);
    legend.append("rect").attr("width", 14).attr("height", 14).attr("y", 0)
      .attr("fill", BAND20).attr("fill-opacity", 0.55);
    legend.append("text").attr("x", 20).attr("y", 11)
      .attr("fill", t.muted).attr("font-size", 11).text("±20 % error");
    legend.append("rect").attr("width", 14).attr("height", 14).attr("y", 22)
      .attr("fill", BAND10).attr("fill-opacity", 0.45);
    legend.append("text").attr("x", 20).attr("y", 33)
      .attr("fill", t.muted).attr("font-size", 11).text("±10 % error");

    function applySelection() {
      groups.select("circle")
        .attr("fill", d => d.case_id === selectedId ? t.amber : t.accent);
    }

    groups
      .on("click", (_e, d) => {
        selectedId = d.case_id;
        applySelection();
        window.dispatchEvent(new CustomEvent("tmhp:parity-selected",
          { detail: { case_id: d.case_id } }));
      });

    window.addEventListener("tmhp:table-selected", (e) => {
      selectedId = e.detail.case_id;
      applySelection();
    });
  })();
})();
