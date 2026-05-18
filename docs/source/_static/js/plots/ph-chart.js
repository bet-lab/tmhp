/**
 * ① Live P–h chart with refrigerant selector.
 *
 * Reads /docs/source/_static/data/refrigerants/<REF>.json (built by
 * scripts/data/gen_refrigerant_data.py) and renders:
 *   - saturation dome (closed area on a log-P / h axis)
 *   - the four cycle state points (1: comp in, 2: comp out, 3: cond out,
 *     4: throttle out) with connecting line segments
 *
 * The COP at the chosen (T_evap, T_cond) is shown in a side panel and
 * refreshes as the sliders move via bilinear interpolation on the
 * cycle_grid — no runtime CoolProp. We deliberately do not surface ṁ
 * or Q_cond: a P–h diagram describes the refrigerant cycle, not the
 * heat-pump system; those system-level outputs depend on a particular
 * compressor displacement / fan rating, which lives on the model pages.
 */
(function () {
  "use strict";
  const mount = document.getElementById("ph-chart-mount");
  if (!mount) return;
  const { tokens, loadJson, bilinear, staticDir } = window.tmhpPlot;

  const REFS = (mount.dataset.refrigerants || "R32").split(",");
  const DEFAULT_REF = mount.dataset.default || REFS[0];

  mount.classList.add("tmhp-plot-mount", "ph-chart");
  mount.innerHTML = `
    <div class="ph-chrome">
      <label>Refrigerant
        <select class="ph-ref">${REFS.map(r => `<option>${r}</option>`).join("")}</select>
      </label>
      <label>T_evap <output class="ph-t-evap-out"></output>
        <input type="range" class="ph-t-evap" min="-20" max="20" step="1">
      </label>
      <label>T_cond <output class="ph-t-cond-out"></output>
        <input type="range" class="ph-t-cond" min="25" max="65" step="1">
      </label>
    </div>
    <div class="ph-canvas-wrap">
      <svg class="ph-canvas" viewBox="0 0 720 420" preserveAspectRatio="xMidYMid meet"></svg>
      <aside class="ph-readout">
        <div class="metric"><span class="label">COP</span><span class="value" data-k="cop">—</span></div>
      </aside>
    </div>
  `;
  const sel = mount.querySelector(".ph-ref");
  const sliderEvap = mount.querySelector(".ph-t-evap");
  const sliderCond = mount.querySelector(".ph-t-cond");
  const outEvap = mount.querySelector(".ph-t-evap-out");
  const outCond = mount.querySelector(".ph-t-cond-out");
  const svg = mount.querySelector("svg.ph-canvas");
  const readout = mount.querySelector(".ph-readout");
  sel.value = DEFAULT_REF;
  sliderEvap.value = -5;
  sliderCond.value = 45;

  let payload = null;

  async function load(ref) {
    payload = await loadJson(`${staticDir()}/data/refrigerants/${ref}.json`);
    render();
  }

  function render() {
    if (!payload) return;
    const t = tokens();
    const dome = payload.saturation_dome;
    const grid = payload.cycle_grid;

    const margin = { top: 20, right: 20, bottom: 50, left: 60 };
    const W = 720, H = 420;
    const innerW = W - margin.left - margin.right;
    const innerH = H - margin.top - margin.bottom;

    const allH = dome.flatMap(d => [d.h_liq_kjkg, d.h_vap_kjkg]);
    const xExtent = [Math.min(...allH) - 20, Math.max(...allH) + 50];
    const pMin = Math.max(50, Math.min(...dome.map(d => d.P_kpa)) * 0.3);
    const pMax = Math.max(...dome.map(d => d.P_kpa)) * 1.2;

    const x  = d3.scaleLinear().domain(xExtent).range([0, innerW]);
    const yP = d3.scaleLog().domain([pMin, pMax]).range([innerH, 0]);

    svg.innerHTML = "";
    const root = d3.select(svg)
      .append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Axes
    root.append("g").attr("class", "axis")
        .attr("transform", `translate(0,${innerH})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.format(",.0f")))
      .append("text").attr("x", innerW / 2).attr("y", 40)
        .attr("text-anchor", "middle").attr("fill", t.muted)
        .text("Enthalpy h [kJ/kg]");
    root.append("g").attr("class", "axis")
        .call(d3.axisLeft(yP).ticks(6, ".0f"))
      .append("text")
        .attr("transform", "rotate(-90)").attr("x", -innerH / 2).attr("y", -42)
        .attr("text-anchor", "middle").attr("fill", t.muted)
        .text("Pressure P [kPa, log]");

    // Saturation dome: liq side + vap side, joined.
    const domePath = d3.line()
      .x(d => x(d.h)).y(d => yP(d.P))
      .curve(d3.curveCatmullRom);
    const liq = dome.map(d => ({ h: d.h_liq_kjkg, P: d.P_kpa }));
    const vap = dome.map(d => ({ h: d.h_vap_kjkg, P: d.P_kpa })).reverse();
    root.append("path")
      .attr("d", domePath([...liq, ...vap]))
      .attr("fill", t.accent3).attr("fill-opacity", 0.5)
      .attr("stroke", t.accent11).attr("stroke-width", 1.2);

    // Cycle 4 points at the chosen (T_evap, T_cond).
    const te = +sliderEvap.value, tc = +sliderCond.value;
    outEvap.textContent = `${te} °C`;
    outCond.textContent = `${tc} °C`;
    const xs = grid.t_evap_c, ys = grid.t_cond_c;

    function P_sat(T_target, side) {
      const tField = "T_c", pField = "P_kpa";
      const arr = dome;
      for (let i = 0; i < arr.length - 1; i++) {
        const a = arr[i], b = arr[i + 1];
        if (T_target >= a[tField] && T_target <= b[tField]) {
          const f = (T_target - a[tField]) / (b[tField] - a[tField]);
          return a[pField] + f * (b[pField] - a[pField]);
        }
      }
      return side === "evap" ? arr[0][pField] : arr[arr.length - 1][pField];
    }
    const P_evap = P_sat(te, "evap"), P_cond = P_sat(tc, "cond");

    function h_at(P, q) {
      let best = dome[0], bestErr = Math.abs(dome[0].P_kpa - P);
      for (const d of dome) {
        const e = Math.abs(d.P_kpa - P);
        if (e < bestErr) { best = d; bestErr = e; }
      }
      return q < 0.5 ? best.h_liq_kjkg : best.h_vap_kjkg;
    }
    const h1 = h_at(P_evap, 1);
    const h3 = h_at(P_cond, 0);
    const h4 = h3;
    const cop = bilinear(xs, ys, grid.cop, te, tc);

    // h2 follows from the COP: q_cond_per_kg = h1 - h4 + w_per_kg
    //                          w_per_kg     = q_cond_per_kg / cop
    // → solve: q_cond_pkg (cop - 1) = (h1 - h4) cop  →  q_cond_pkg = (h1-h4) cop / (cop-1)
    // and h2 = h3 + q_cond_pkg = h3 + (h1 - h4) * cop / (cop - 1).
    // Guarded against cop <= 1 so the chart doesn't NaN at extreme corners.
    const h2 = (cop && cop > 1.05)
      ? h3 + (h1 - h4) * cop / (cop - 1)
      : h1 + 30;   // visual fallback so the cycle still draws sensibly

    const cyclePoints = [
      { h: h1, P: P_evap, label: "1" },
      { h: h2, P: P_cond, label: "2" },
      { h: h3, P: P_cond, label: "3" },
      { h: h4, P: P_evap, label: "4" },
    ];
    const cycleClosed = [...cyclePoints, cyclePoints[0]];
    const cycleLine = d3.line().x(d => x(d.h)).y(d => yP(d.P));
    root.append("path")
      .attr("d", cycleLine(cycleClosed))
      .attr("fill", "none").attr("stroke", t.accent).attr("stroke-width", 1.8);

    root.selectAll(".pt").data(cyclePoints).enter().append("g")
      .attr("class", "pt")
      .attr("transform", d => `translate(${x(d.h)},${yP(d.P)})`)
      .call(g => {
        g.append("circle").attr("r", 4).attr("fill", t.accent);
        g.append("text").attr("x", 6).attr("y", -6).attr("fill", t.ink)
          .attr("font-size", 12).attr("font-weight", 600).text(d => d.label);
      });

    // Readout (COP only — see module docstring for why)
    readout.querySelector('[data-k="cop"]').textContent =
      cop ? cop.toFixed(2) : "—";
  }

  sel.addEventListener("change", () => load(sel.value));
  sliderEvap.addEventListener("input", render);
  sliderCond.addEventListener("input", render);

  load(DEFAULT_REF);
})();
