/**
 * ② Interactive parity plot (15-point Samsung EHS catalogue).
 *
 * Reads /_static/data/validation-points.json (built by
 * scripts/data/gen_validation_data.py). Renders a scatter of Q_mod vs
 * Q_cat with the y = x reference line. Hovering a point pins a side
 * card with the case fields; clicking a point dispatches a CustomEvent
 * 'tmhp:parity-selected' that ④ (validation-table) listens for to
 * highlight the matching row.
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

  mount.classList.add("tmhp-plot-mount", "parity-plot");
  mount.innerHTML = `
    <div class="parity-wrap">
      <svg class="parity-canvas" viewBox="0 0 600 460" preserveAspectRatio="xMidYMid meet"></svg>
      <aside class="parity-readout">
        <div class="empty">Hover or click a point to see the case</div>
      </aside>
    </div>
  `;
  const svg = mount.querySelector("svg.parity-canvas");
  const card = mount.querySelector(".parity-readout");

  (async () => {
    const points = await loadJson(`${staticDir()}/data/validation-points.json`);
    const t = tokens();
    const margin = { top: 30, right: 20, bottom: 50, left: 60 };
    const W = 600, H = 460;
    const iw = W - margin.left - margin.right;
    const ih = H - margin.top - margin.bottom;
    const qs = points.flatMap(p => [p.q_cat_kw, p.q_mod_kw]);
    const lo = Math.floor(Math.min(...qs) - 1);
    const hi = Math.ceil(Math.max(...qs) + 1);

    const x = d3.scaleLinear().domain([lo, hi]).range([0, iw]);
    const y = d3.scaleLinear().domain([lo, hi]).range([ih, 0]);

    const root = d3.select(svg).append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    root.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${ih})`)
      .call(d3.axisBottom(x).ticks(6))
      .append("text").attr("x", iw / 2).attr("y", 40)
      .attr("text-anchor", "middle").attr("fill", t.muted)
      .text("Catalogue Q [kW]");
    root.append("g").attr("class", "axis")
      .call(d3.axisLeft(y).ticks(6))
      .append("text")
      .attr("transform", "rotate(-90)").attr("x", -ih / 2).attr("y", -42)
      .attr("text-anchor", "middle").attr("fill", t.muted)
      .text("Model Q [kW]");

    root.append("line")
      .attr("x1", x(lo)).attr("y1", y(lo))
      .attr("x2", x(hi)).attr("y2", y(hi))
      .attr("stroke", t.muted).attr("stroke-dasharray", "4 4");

    let selectedId = null;

    const dots = root.selectAll("circle.pt")
      .data(points).enter()
      .append("circle").attr("class", "pt")
      .attr("cx", d => x(d.q_cat_kw))
      .attr("cy", d => y(d.q_mod_kw))
      .attr("r", 5).attr("fill", t.accent)
      .attr("stroke", "#fff").attr("stroke-width", 1.2)
      .style("cursor", "pointer");

    function show(d) {
      const dpct = ((d.q_mod_kw - d.q_cat_kw) / d.q_cat_kw) * 100;
      const sign = dpct >= 0 ? "+" : "";
      const cls = Math.abs(dpct) < 5 ? "ok" : "warn";
      card.innerHTML = `
        <div class="head">Case ${d.case_id} · ${d.refrigerant}</div>
        <dl>
          <dt>T_source / T_sink</dt><dd>${d.t_source_c} / ${d.t_sink_c} °C</dd>
          <dt>Q_cat</dt><dd>${d.q_cat_kw.toFixed(2)} kW</dd>
          <dt>Q_mod</dt><dd>${d.q_mod_kw.toFixed(2)} kW</dd>
          <dt>COP_cat / COP_mod</dt><dd>${d.cop_cat.toFixed(2)} / ${d.cop_mod.toFixed(2)}</dd>
        </dl>
        <div class="delta ${cls}">${sign}${dpct.toFixed(1)} %</div>
      `;
    }

    dots
      .on("mouseenter", (_e, d) => show(d))
      .on("mouseleave", () => {
        if (selectedId !== null) {
          const sel = points.find(p => p.case_id === selectedId);
          if (sel) show(sel);
        } else {
          card.innerHTML = '<div class="empty">Hover or click a point to see the case</div>';
        }
      })
      .on("click", (_e, d) => {
        selectedId = d.case_id;
        dots.attr("fill", p => p.case_id === selectedId ? t.amber : t.accent);
        window.dispatchEvent(new CustomEvent("tmhp:parity-selected",
          { detail: { case_id: d.case_id } }));
      });

    // Listen for selection from ④ (table → plot, lands in Task 9).
    window.addEventListener("tmhp:table-selected", (e) => {
      selectedId = e.detail.case_id;
      dots.attr("fill", p => p.case_id === selectedId ? t.amber : t.accent);
      const sel = points.find(p => p.case_id === selectedId);
      if (sel) show(sel);
    });
  })();
})();
