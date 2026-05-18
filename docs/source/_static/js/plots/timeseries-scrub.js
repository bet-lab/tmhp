/**
 * ③ 24-hour timeseries scrub.
 *
 * Reads /_static/data/timeseries-24h.json (built by
 * scripts/data/gen_timeseries_data.py). Three stacked subplots share
 * the time axis; a vertical cursor + side-card show the row at the
 * pointer position.
 */
(function () {
  "use strict";
  const mount = document.getElementById("ts-scrub-mount");
  if (!mount) return;
  if (!window.tmhpPlot) {
    console.warn("timeseries-scrub: tmhpPlot helpers missing — load _plot-common.js first");
    return;
  }
  const { tokens, loadJson, staticDir } = window.tmhpPlot;

  mount.classList.add("tmhp-plot-mount", "ts-scrub");
  mount.innerHTML = `
    <div class="ts-wrap">
      <svg class="ts-canvas" viewBox="0 0 780 460" preserveAspectRatio="xMidYMid meet"></svg>
      <aside class="ts-readout">
        <div class="head">Scrub to pin a time</div>
        <dl></dl>
      </aside>
    </div>
  `;
  const svg = mount.querySelector("svg.ts-canvas");
  const headEl = mount.querySelector(".ts-readout .head");
  const dlEl = mount.querySelector(".ts-readout dl");

  (async () => {
    const payload = await loadJson(`${staticDir()}/data/timeseries-24h.json`);
    const data = payload.series;
    const t = tokens();

    const W = 780, H = 460;
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const innerW = W - margin.left - margin.right;
    const innerH = H - margin.top - margin.bottom;
    const rowH = innerH / 3;

    const x = d3.scaleLinear()
      .domain([data[0].t_min, data[data.length - 1].t_min])
      .range([0, innerW]);

    const seriesDefs = [
      { key: "t_amb_c",   label: "T_amb [°C]",  color: t.amber },
      { key: "q_heat_kw", label: "Q_heat [kW]", color: t.accent },
      { key: "cop",       label: "COP [-]",     color: t.green },
    ];

    const root = d3.select(svg).append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    seriesDefs.forEach((s, i) => {
      const yExt = d3.extent(data, d => d[s.key]).map(v => v ?? 0);
      const pad = (yExt[1] - yExt[0]) * 0.1 || 1;
      const y = d3.scaleLinear()
        .domain([yExt[0] - pad, yExt[1] + pad])
        .range([(i + 1) * rowH - 4, i * rowH + 4]);

      root.append("g").attr("class", "axis")
        .call(d3.axisLeft(y).ticks(3));
      root.append("text").attr("x", 4).attr("y", i * rowH + 14)
        .attr("fill", t.muted).attr("font-size", 11).text(s.label);

      const line = d3.line()
        .defined(d => d[s.key] !== null && d[s.key] !== undefined)
        .x(d => x(d.t_min)).y(d => y(d[s.key]));
      root.append("path").datum(data)
        .attr("d", line)
        .attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 1.5);
    });

    // Shared x-axis at the bottom (hours).
    root.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x)
        .ticks(8)
        .tickFormat(m => `${String(Math.floor(m / 60)).padStart(2, "0")}:00`));

    // Cursor overlay
    const cursor = root.append("line")
      .attr("y1", 0).attr("y2", innerH)
      .attr("stroke", t.ink).attr("stroke-width", 1)
      .style("display", "none");

    const bisect = d3.bisector(d => d.t_min).left;

    function update(mouseX) {
      const tMin = x.invert(mouseX);
      const idx = Math.max(0, Math.min(data.length - 1, bisect(data, tMin)));
      const row = data[idx];
      cursor.attr("x1", x(row.t_min)).attr("x2", x(row.t_min)).style("display", null);
      const hh = String(Math.floor(row.t_min / 60)).padStart(2, "0");
      const mm = String(row.t_min % 60).padStart(2, "0");
      headEl.textContent = `${hh}:${mm}`;
      const rows = [
        ["T_amb",  row.t_amb_c   != null ? row.t_amb_c.toFixed(1)   + " °C" : "—"],
        ["Q_heat", row.q_heat_kw != null ? row.q_heat_kw.toFixed(2) + " kW" : "—"],
        ["COP",    row.cop       != null ? row.cop.toFixed(2)               : "—"],
        ["P_cmp",  row.p_cmp_kw  != null ? row.p_cmp_kw.toFixed(2)  + " kW" : "—"],
        ["T_tank", row.t_tank_c  != null ? row.t_tank_c.toFixed(1)  + " °C" : "—"],
      ];
      dlEl.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }

    root.append("rect")
      .attr("width", innerW).attr("height", innerH)
      .attr("fill", "transparent")
      .on("mousemove", (event) => {
        const [mx] = d3.pointer(event);
        update(mx);
      })
      .on("mouseleave", () => {
        cursor.style("display", "none");
        headEl.textContent = "Scrub to pin a time";
        dlEl.innerHTML = "";
      });
  })();
})();
