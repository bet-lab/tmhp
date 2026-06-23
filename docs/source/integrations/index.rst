============
Integrations
============

TMHP can stay inside a Python study, but it is also designed to sit
behind building-energy simulators and co-simulation masters. The
integration adapters are optional so the core heat-pump package stays
lightweight: import ``tmhp`` for native Python simulation, then opt into
the adapter that matches the external tool boundary.

Two adapter paths are currently supported:

.. grid:: 1 2 2 2
    :gutter: 3

    .. grid-item-card:: EnergyPlus Python Plugin
        :link: energyplus-python
        :link-type: doc

        Use TMHP as a ``PlantComponent:UserDefined`` surrogate. EnergyPlus
        owns the plant loop and tank state; TMHP answers each plant-solver
        call through ``analyze_steady()``.

    .. grid-item-card:: FMI 2.0 FMU
        :link: fmu
        :link-type: doc

        Export the ASHPB dynamic ``step()`` kernel as a co-simulation FMU
        with explicit input, output, unit, and diagnostic boundaries.

Integration boundary
====================

Both adapters use public model seams rather than private implementation
helpers. The EnergyPlus path is a steady plant-component surrogate because
EnergyPlus owns the loop dispatch and storage tank. The FMU path is a
dynamic co-simulation component because the FMU owns the ASHPB state and
advances it one communication step at a time.

.. raw:: html

   <style>
     .integration-graph-card {
       margin: 1.25em auto;
       border: 1px solid var(--sy-c-border, #e5e7eb);
       border-radius: 8px;
       background: var(--sy-c-bg, #fff);
       padding: 16px 18px;
       position: relative;
       max-width: 100%;
     }
     #tmhp-integration-boundary {
       width: 100%;
       height: 430px;
       min-height: 360px;
       border-radius: 6px;
     }
     .integration-graph-toolbar {
       position: absolute; top: 22px; right: 22px;
       display: flex; gap: 6px;
       background: rgba(255,255,255,0.9);
       border: 1px solid #e5e7eb; border-radius: 8px;
       padding: 4px; z-index: 5;
     }
     .integration-graph-toolbar button {
       background: transparent; border: 0;
       width: 28px; height: 28px;
       border-radius: 5px; cursor: pointer;
       color: #4b5563; font-size: 14px;
       font-family: inherit;
     }
     .integration-graph-toolbar button:hover {
       background: #f3f4f6; color: #1f2937;
     }
     #tmhp-integration-info {
       margin-top: 12px;
       background: linear-gradient(180deg, #0f1622 0%, #131a26 100%);
       color: #e6ecf5;
       padding: 14px 16px; border-radius: 8px;
       font-size: 13px; line-height: 1.55;
       border: 1px solid #1f2a3a;
       min-height: 4em;
     }
     #tmhp-integration-info .placeholder {
       color: #9aa7b8; font-style: italic;
     }
     #tmhp-integration-info .id {
       font-weight: 600; color: #c7d2fe; font-size: 14px;
     }
     #tmhp-integration-info .ty {
       font-size: 11px; padding: 1px 7px; border-radius: 999px;
       background: #1f2a3a; color: #9aa7b8; margin-left: 6px;
       vertical-align: 1px;
     }
     #tmhp-integration-info code {
       background: rgba(255,255,255,0.07); padding: 1px 6px;
       border-radius: 4px; font-size: 12px; color: #d1d5db;
     }
     #tmhp-integration-info .body { margin-top: 6px; }
     #tmhp-integration-info .apilink {
       display: inline-block; margin-top: 8px;
       color: #8b9eff; text-decoration: none; font-size: 12px;
     }
     #tmhp-integration-info .apilink:hover { text-decoration: underline; }
     .integration-graph-hint {
       color: #6b7280; font-size: 12px; margin-top: 8px;
     }
     .integration-graph-caption {
       text-align: center; font-style: italic;
       color: var(--sy-c-text-secondary, #6b7280);
       font-size: 0.92em; margin-top: 0.6em;
     }
     @media (max-width: 720px) {
       #tmhp-integration-boundary { height: 520px; }
       .integration-graph-toolbar { position: static; margin-bottom: 8px; }
     }
   </style>

   <div class="integration-graph-card">
     <div class="integration-graph-toolbar">
       <button id="tmhp-integration-fit" title="Fit to view">⤢</button>
       <button id="tmhp-integration-zoom-in" title="Zoom in">+</button>
       <button id="tmhp-integration-zoom-out" title="Zoom out">−</button>
     </div>
     <div id="tmhp-integration-boundary"></div>
     <div id="tmhp-integration-info">
       <span class="placeholder">Click a node to see the integration contract.</span>
     </div>
     <p class="integration-graph-hint">Topology is fixed · scroll-wheel to zoom · drag empty space to pan</p>
   </div>

   <p class="integration-graph-caption">
     TMHP integration data flow. EnergyPlus uses the steady seam; FMU
     co-simulation uses the dynamic seam.
   </p>

   <script src="../_static/js/lib/cytoscape.min.js"></script>
   <script>
   (function () {
     const container = document.getElementById("tmhp-integration-boundary");
     if (!container) return;
     if (typeof cytoscape === "undefined") {
       document.getElementById("tmhp-integration-info").innerHTML =
         '<span class="placeholder">Cytoscape did not load, so the integration graph cannot render.</span>';
       return;
     }

     const nodes = [
       {
         id: "EPLUS", type: "external", title: "EnergyPlus",
         sub: "Plant loop + Python Plugin",
         contract: "Owns the plant loop, timestep, dispatch request, and storage-tank state.",
         code: "PlantComponent:UserDefined + PythonPlugin:SearchPaths",
         api: "energyplus-python.html"
       },
       {
         id: "EPLUS_IO", type: "io", title: "EnergyPlus boundary",
         sub: "T_in · mdot · cp · load · T0",
         contract: "TMHP reads finite plant boundary values and writes outlet temperature, mass flow, and electricity globals.",
         code: "tmhp_E_cmp_J [J], optional tmhp_E_cmp_W [W]",
         api: "energyplus-python.html#input-output-boundary"
       },
       {
         id: "EPLUS_ADAPTER", type: "adapter", title: "EnergyPlus adapter",
         sub: "TmhpPlantSurrogate",
         contract: "Resolves DataExchange handles, guards invalid values, memoizes repeated plant-solver calls, and actuates the user-defined component.",
         code: "tmhp.integrations.energyplus_plugin",
         api: "../api/support/integrations.html#module-tmhp.integrations.energyplus_plugin"
       },
       {
         id: "STEADY", type: "seam", title: "analyze_steady()",
         sub: "steady plant seam",
         contract: "Answers one plant-solver request from inlet water temperature, outdoor temperature, and requested heat rate.",
         code: "AirSourceHeatPumpBoiler.analyze_steady(T_tank_w, T0, Q_ref_tank)",
         api: "../models/ashpb.html"
       },
       {
         id: "CORE", type: "core", title: "TMHP ASHPB core",
         sub: "CoolProp cycle solve",
         contract: "Solves refrigerant state points, heat exchangers, compressor work, COP, convergence, and failure_reason diagnostics.",
         code: "AirSourceHeatPumpBoiler + refrigerant/cycle helpers",
         api: "../concepts/cycle-architecture.html"
       },
       {
         id: "FMU_MASTER", type: "external", title: "FMI master",
         sub: "fmpy · OMSimulator · Dymola",
         contract: "Owns the co-simulation schedule and sets FMI input variables before each communication step.",
         code: "FMI 2.0 Co-Simulation importer",
         api: "fmu.html"
       },
       {
         id: "FMU_IO", type: "io", title: "FMU boundary",
         sub: "T0 · dhw_draw · T_sup_w",
         contract: "The importer sets outdoor, DHW draw, and mains-water inputs; the FMU returns power, heat, tank temperature, COP, and diagnostics.",
         code: "E_cmp, E_tot, Q_ref_tank, cop_sys, T_tank_w",
         api: "fmu.html#input-output-boundary"
       },
       {
         id: "FMU_ADAPTER", type: "adapter", title: "FMU adapter",
         sub: "TmhpAshpbSlave",
         contract: "Builds an FMI 2.0 model description, validates input scalars, owns the dynamic ASHPB state, and sanitizes FMI outputs.",
         code: "tmhp.integrations.fmu",
         api: "../api/support/integrations.html#module-tmhp.integrations.fmu"
       },
       {
         id: "STEP", type: "seam", title: "step()",
         sub: "dynamic state seam",
         contract: "Advances one ASHPB state over the FMI communication step using the same public dynamic kernel as native Python simulations.",
         code: "state, result = hp.step(state, inputs, step_size)",
         api: "../getting-started/first-dynamic-simulation.html"
       },
       {
         id: "OUTPUTS", type: "output", title: "Shared outputs",
         sub: "power · heat · COP · diagnostics",
         contract: "Both adapters preserve physical outputs and convergence diagnostics at the simulator boundary instead of hiding guard trips.",
         code: "converged, failure_reason, hp_is_on",
         api: "../concepts/failure-reason-semantics.html"
       }
     ];
     const edges = [
       { source: "EPLUS", target: "EPLUS_IO", label: "DataExchange API" },
       { source: "EPLUS_IO", target: "EPLUS_ADAPTER", label: "finite values" },
       { source: "EPLUS_ADAPTER", target: "STEADY", label: "calls" },
       { source: "STEADY", target: "CORE", label: "cycle solve" },
       { source: "CORE", target: "EPLUS_ADAPTER", label: "E_cmp, Q_ref, diagnostics" },
       { source: "EPLUS_ADAPTER", target: "OUTPUTS", label: "actuators + globals" },
       { source: "FMU_MASTER", target: "FMU_IO", label: "sets FMI inputs" },
       { source: "FMU_IO", target: "FMU_ADAPTER", label: "valid scalars" },
       { source: "FMU_ADAPTER", target: "STEP", label: "do_step" },
       { source: "STEP", target: "CORE", label: "state advance" },
       { source: "CORE", target: "FMU_ADAPTER", label: "step result" },
       { source: "FMU_ADAPTER", target: "OUTPUTS", label: "FMU outputs" }
     ];

     const palette = {
       external: { fill: "#fef3c7", border: "#d97706", text: "#78350f" },
       io:       { fill: "#dbeafe", border: "#2563eb", text: "#1e3a8a" },
       adapter:  { fill: "#eef2ff", border: "#6366f1", text: "#1e1b4b" },
       seam:     { fill: "#f5f3ff", border: "#8b5cf6", text: "#4c1d95" },
       core:     { fill: "#dcfce7", border: "#16a34a", text: "#14532d" },
       output:   { fill: "#f1f5f9", border: "#64748b", text: "#334155" }
     };

     const cy = cytoscape({
       container,
       elements: [
         ...nodes.map(n => ({ data: { ...n, label: n.title + "\n" + n.sub } })),
         ...edges.map(e => ({ data: e }))
       ],
       style: [
         { selector: "node", style: {
             "label": "data(label)", "text-wrap": "wrap",
             "text-valign": "center", "text-halign": "center",
             "font-size": 12, "font-weight": 600,
             "font-family": "-apple-system, BlinkMacSystemFont, Inter, sans-serif",
             "width": 166, "height": 64,
             "text-max-width": 148,
             "padding": "11px", "shape": "round-rectangle",
             "corner-radius": "10", "border-width": 1.5,
             "line-height": 1.35
         } },
         { selector: 'node[type = "external"]', style: {
             "background-color": palette.external.fill, "border-color": palette.external.border, "color": palette.external.text } },
         { selector: 'node[type = "io"]', style: {
             "background-color": palette.io.fill, "border-color": palette.io.border, "color": palette.io.text } },
         { selector: 'node[type = "adapter"]', style: {
             "background-color": palette.adapter.fill, "border-color": palette.adapter.border, "color": palette.adapter.text } },
         { selector: 'node[type = "seam"]', style: {
             "background-color": palette.seam.fill, "border-color": palette.seam.border, "color": palette.seam.text,
             "border-style": "dashed" } },
         { selector: 'node[type = "core"]', style: {
             "background-color": palette.core.fill, "border-color": palette.core.border, "color": palette.core.text,
             "border-width": 2.5 } },
         { selector: 'node[type = "output"]', style: {
             "background-color": palette.output.fill, "border-color": palette.output.border, "color": palette.output.text } },
         { selector: "edge", style: {
             "width": 1.5, "line-color": "#475569",
             "target-arrow-color": "#475569", "target-arrow-shape": "triangle",
             "arrow-scale": 1.05, "curve-style": "bezier",
             "label": "data(label)", "font-size": 10, "color": "#374151",
             "text-outline-color": "#fff", "text-outline-opacity": 1, "text-outline-width": 1.5
         } },
         { selector: "node:selected", style: { "border-width": 3 } },
         { selector: ".faded", style: { "opacity": 0.25 } }
       ],
       layout: { name: "preset", positions: {
         EPLUS: { x: 90, y: 95 }, EPLUS_IO: { x: 295, y: 95 },
         EPLUS_ADAPTER: { x: 500, y: 95 }, STEADY: { x: 700, y: 95 },
         CORE: { x: 900, y: 225 }, OUTPUTS: { x: 1090, y: 225 },
         FMU_MASTER: { x: 90, y: 355 }, FMU_IO: { x: 295, y: 355 },
         FMU_ADAPTER: { x: 500, y: 355 }, STEP: { x: 700, y: 355 }
       } },
       autoungrabify: true,
       minZoom: 0.1, maxZoom: 2.5
     });

     const info = document.getElementById("tmhp-integration-info");
     const placeholder = '<span class="placeholder">Click a node to see the integration contract.</span>';
     function escapeHtml(value) {
       return String(value)
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;");
     }
     function showNode(data) {
       info.innerHTML =
         '<span class="id">' + escapeHtml(data.title) + '</span>' +
         '<span class="ty">' + escapeHtml(data.type) + '</span>' +
         '<div class="body">' + escapeHtml(data.contract) + '</div>' +
         '<div class="body"><code>' + escapeHtml(data.code) + '</code></div>' +
         '<a class="apilink" href="' + escapeHtml(data.api) + '">Open related docs</a>';
     }
     cy.on("tap", "node", evt => {
       showNode(evt.target.data());
       cy.elements().addClass("faded");
       evt.target.closedNeighborhood().removeClass("faded");
     });
     cy.on("tap", evt => {
       if (evt.target === cy) {
         info.innerHTML = placeholder;
         cy.elements().removeClass("faded");
       }
     });

     let resizeTimer = null;
     function fitGraph() {
       cy.resize();
       cy.fit(undefined, 30);
     }
     document.getElementById("tmhp-integration-fit").addEventListener("click",
       fitGraph);
     document.getElementById("tmhp-integration-zoom-in").addEventListener("click",
       () => cy.zoom({ level: cy.zoom() * 1.25,
                       renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }));
     document.getElementById("tmhp-integration-zoom-out").addEventListener("click",
       () => cy.zoom({ level: cy.zoom() * 0.8,
                       renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }));
     window.addEventListener("resize", () => {
       window.clearTimeout(resizeTimer);
       resizeTimer = window.setTimeout(fitGraph, 80);
     });

     document.fonts && document.fonts.ready
       && document.fonts.ready.then(fitGraph);
     setTimeout(fitGraph, 0);
   })();
   </script>

Which path should I use?
========================

Use :doc:`energyplus-python` when EnergyPlus already owns the plant loop,
schedule, and tank objects, and you want TMHP to replace an empirical
heat-pump curve with a refrigerant-cycle-resolved answer.

Use :doc:`fmu` when an FMI master should own the co-simulation schedule
and TMHP should advance an ASHPB state across each communication step.
This path is best for tool-to-tool coupling and for comparing the same
dynamic kernel against native Python ``analyze_dynamic()`` runs.

.. toctree::
   :maxdepth: 1
   :hidden:

   energyplus-python
   fmu
