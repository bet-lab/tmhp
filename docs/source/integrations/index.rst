============
Integrations
============

TMHP can stay inside a Python study, but it is also designed to sit
behind building-energy simulators and co-simulation masters. The
integration adapters are optional so the core heat-pump package stays
lightweight: import ``tmhp`` for native Python simulation, then opt into
the adapter that matches the external tool boundary.

The selling point is model reuse. TMHP keeps the cycle-resolved heat
pump model in one place, while external tools keep doing what they are
already good at: EnergyPlus owns whole-building loads and plant dispatch,
Modelica tools own equation-based HVAC and controls, and FMI masters own
tool-to-tool scheduling.

What integrations enable
========================

.. grid:: 1 2 2 3
    :gutter: 3

    .. grid-item-card:: Keep EnergyPlus as the building model

        Replace an empirical plant component with a TMHP steady
        refrigerant-cycle solve while EnergyPlus still owns the IDF,
        schedules, plant loop, and reporting.

    .. grid-item-card:: Export the heat pump as a reusable FMU

        Package the dynamic ASHPB ``step()`` kernel behind FMI variables
        so a co-simulation master can set weather and DHW draw inputs and
        read power, heat, COP, tank temperature, and diagnostics.

    .. grid-item-card:: Connect to other simulation ecosystems

        Use the same TMHP model in Python smoke tests, Modelica-based
        plant and controls studies, Simulink controller workflows, or
        composite FMU co-simulation.

Two adapter paths are currently supported:

.. grid:: 1 2 2 2
    :gutter: 3

    .. grid-item-card:: EnergyPlus Python Plugin
        :link: energyplus-python
        :link-type: doc

        Use TMHP as a ``PlantComponent:UserDefined`` surrogate. EnergyPlus
        owns the plant loop and tank state; TMHP answers each plant-solver
        call through ``analyze_steady()``.

    .. grid-item-card:: FMI FMU
        :link: fmu
        :link-type: doc

        Export the ASHPB dynamic ``step()`` kernel as a co-simulation FMU
        with explicit input, output, unit, and diagnostic boundaries.
        TMHP provides separate FMI 2.0 and FMI 3.0 artifacts.

Integration vocabulary
======================

EnergyPlus is a whole-building energy simulation program. Its Python
Plugin interface lets EnergyPlus call user-defined Python classes at
specific simulation calling points; the official Input Output Reference
describes a plugin as a class derived from ``EnergyPlusPlugin`` whose
overridden methods determine when EnergyPlus calls user code
(`EnergyPlus Python Plugin documentation
<https://bigladdersoftware.com/epx/docs/9-3/input-output-reference/group-python-plugins.html>`_).
TMHP uses that mechanism to answer a plant-component request without
moving the building model out of EnergyPlus.

FMI, the Functional Mock-up Interface, is a Modelica Association standard
for exchanging dynamic models. The current specification defines an FMU
as a ZIP archive plus API for XML metadata, binaries, and source code; it
also distinguishes Co-Simulation, Model Exchange, and Scheduled
Execution interface types (`FMI specification
<https://fmi-standard.org/docs/main/>`_). TMHP exports Co-Simulation
FMUs: the importing tool sets scalar inputs, calls ``do_step``, then
reads scalar outputs.

FMI 3.0 is managed as a separate major version rather than as an FMU file
that automatically contains FMI 2.0. The FMI 3.0.2 specification frames
compatibility within the same major version and adds features such as
Scheduled Execution, clocks, early return, event mode, and intermediate
update (`FMI 3.0.2 specification
<https://fmi-standard.org/docs/3.0.2/>`_). TMHP therefore provides
separate FMI 2.0 and FMI 3.0 adapters over the same ASHPB ``step()``
kernel.

The reason this matters is reach. The FMI project maintains a tools page
covering hundreds of FMI-capable tools (`FMI tools
<https://fmi-standard.org/tools/>`_), and a 2025 project note reported
250 listed tools with 178 Co-Simulation importers and 133
Co-Simulation exporters (`FMI tools milestone
<https://fmi-standard.org/news/2025-07-14-fmi-supported-by-250-tools/>`_).
Actual compatibility still depends on the importer and on the Python
runtime required by TMHP's current PythonFMU-based package, but the
interface is deliberately the standard FMI boundary rather than a
TMHP-specific socket or file protocol.

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
       padding: 18px 20px;
       position: relative;
       width: 100%;
       max-width: 1120px;
     }
     #tmhp-integration-boundary {
       width: 100%;
       height: 500px;
       min-height: 460px;
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
     .integration-graph-legend {
       display: flex; gap: 8px; flex-wrap: wrap;
       margin: 2px 110px 10px 0;
       color: #475569; font-size: 12px;
     }
     .integration-graph-legend span {
       display: inline-flex; align-items: center; gap: 5px;
       white-space: nowrap;
     }
     .integration-graph-legend i {
       display: inline-block; width: 10px; height: 10px;
       border-radius: 3px; border: 1px solid currentColor;
     }
     @media (max-width: 720px) {
       #tmhp-integration-boundary { height: 680px; }
       .integration-graph-toolbar { position: static; margin-bottom: 8px; }
       .integration-graph-legend { margin-right: 0; }
       .integration-graph-card {
         width: 100%;
         max-width: 100%;
       }
     }
   </style>

   <div class="integration-graph-card">
     <div class="integration-graph-toolbar">
       <button id="tmhp-integration-fit" title="Fit to view">⤢</button>
       <button id="tmhp-integration-zoom-in" title="Zoom in">+</button>
       <button id="tmhp-integration-zoom-out" title="Zoom out">−</button>
     </div>
     <div class="integration-graph-legend" aria-label="Diagram legend">
       <span><i style="background:#fef3c7;color:#d97706"></i>External tool</span>
       <span><i style="background:#eef2ff;color:#6366f1"></i>Adapter</span>
       <span><i style="background:#f5f3ff;color:#8b5cf6"></i>Public TMHP API</span>
       <span><i style="background:#dcfce7;color:#16a34a"></i>Cycle core</span>
     </div>
     <div id="tmhp-integration-boundary"></div>
     <div id="tmhp-integration-info">
       <span class="placeholder">Click a node to see the integration contract.</span>
     </div>
     <p class="integration-graph-hint">Topology is fixed · scroll-wheel to zoom · drag empty space to pan</p>
   </div>

   <p class="integration-graph-caption">
     TMHP integration data flow. Both paths move left to right: external
     simulator inputs enter TMHP, the cycle core solves, then each adapter
     publishes outputs back to its host tool.
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

     const desktopPositions = {
       EPLUS: { x: 120, y: 180 },
       EPLUS_ADAPTER: { x: 340, y: 180 },
       STEADY: { x: 560, y: 180 },
       CORE: { x: 660, y: 310 },
       EPLUS_OUT: { x: 940, y: 180 },
       FMU_MASTER: { x: 120, y: 440 },
       FMU_ADAPTER: { x: 340, y: 440 },
       STEP: { x: 560, y: 440 },
       FMU_OUT: { x: 940, y: 440 }
     };
     const mobilePositions = {
       EPLUS: { x: 115, y: 90 },
       EPLUS_ADAPTER: { x: 115, y: 225 },
       STEADY: { x: 115, y: 360 },
       CORE: { x: 255, y: 440 },
       EPLUS_OUT: { x: 415, y: 360 },
       FMU_MASTER: { x: 115, y: 600 },
       FMU_ADAPTER: { x: 115, y: 735 },
       STEP: { x: 275, y: 735 },
       FMU_OUT: { x: 415, y: 600 }
     };

     const nodes = [
       {
         id: "EPLUS", type: "external", title: "EnergyPlus",
         sub: "Plant loop + Python Plugin",
         contract: "Owns the plant loop, timestep, dispatch request, and storage-tank state.",
         code: "PlantComponent:UserDefined + PythonPlugin:SearchPaths",
         api: "energyplus-python.html"
       },
       {
         id: "EPLUS_ADAPTER", type: "adapter", title: "EnergyPlus adapter",
         sub: "T_in · mdot · cp · load · T0",
         contract: "TmhpPlantSurrogate resolves DataExchange handles, guards invalid boundary values, memoizes repeated plant-solver calls, and actuates the user-defined component.",
         code: "tmhp.integrations.energyplus_plugin",
         api: "../api/support/integrations.html#module-tmhp.integrations.energyplus_plugin"
       },
       {
         id: "STEADY", type: "seam", title: "analyze_steady()",
         sub: "steady public API",
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
         id: "EPLUS_OUT", type: "output", title: "EnergyPlus outputs",
         sub: "actuators + plugin globals",
         contract: "Writes outlet temperature, mass-flow request, timestep compressor energy, optional compressor power, and severe diagnostics back to EnergyPlus.",
         code: "outlet temperature actuator, tmhp_E_cmp_J, tmhp_E_cmp_W",
         api: "energyplus-python.html#input-output-boundary"
       },
       {
         id: "FMU_MASTER", type: "external", title: "FMI master",
         sub: "fmpy · OMSimulator · Dymola",
         contract: "Owns the co-simulation schedule and sets FMI input variables before each communication step.",
         code: "FMI 2.0/3.0 Co-Simulation importer",
         api: "fmu.html"
       },
       {
         id: "FMU_ADAPTER", type: "adapter", title: "FMU adapter",
         sub: "T0 · dhw_draw · T_sup_w",
         contract: "TmhpAshpbSlave and TmhpAshpbFmi3Slave build FMI model descriptions, validate input scalars, own the dynamic ASHPB state, and sanitize outputs.",
         code: "tmhp.integrations.fmu / fmu3",
         api: "../api/support/integrations.html#module-tmhp.integrations.fmu"
       },
       {
         id: "STEP", type: "seam", title: "step()",
         sub: "dynamic public API",
         contract: "Advances one ASHPB state over the FMI communication step using the same public dynamic kernel as native Python simulations.",
         code: "state, result = hp.step(state, inputs, step_size)",
         api: "../getting-started/first-dynamic-simulation.html"
       },
       {
         id: "FMU_OUT", type: "output", title: "FMU outputs",
         sub: "power · heat · state · diagnostics",
         contract: "Publishes FMI output variables for power, heat, tank temperature, COP, convergence, on/off state, and failure_reason.",
         code: "E_cmp, E_tot, Q_ref_tank, cop_sys, T_tank_w, converged",
         api: "fmu.html#input-output-boundary"
       }
     ];
     const edges = [
       { source: "EPLUS", target: "EPLUS_ADAPTER" },
       { source: "EPLUS_ADAPTER", target: "STEADY" },
       { source: "STEADY", target: "CORE" },
       { source: "CORE", target: "EPLUS_OUT" },
       { source: "FMU_MASTER", target: "FMU_ADAPTER" },
       { source: "FMU_ADAPTER", target: "STEP" },
       { source: "STEP", target: "CORE" },
       { source: "CORE", target: "FMU_OUT" }
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
             "width": 176, "height": 76,
             "text-max-width": 156,
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
             "border-width": 2.5, "width": 198, "height": 100,
             "text-max-width": 174 } },
         { selector: 'node[type = "output"]', style: {
             "background-color": palette.output.fill, "border-color": palette.output.border, "color": palette.output.text,
             "width": 190, "height": 82, "text-max-width": 168 } },
         { selector: "edge", style: {
             "width": 2, "line-color": "#475569",
             "target-arrow-color": "#475569", "target-arrow-shape": "triangle",
             "arrow-scale": 1.05, "curve-style": "straight"
         } },
         { selector: "node:selected", style: { "border-width": 3 } },
         { selector: ".faded", style: { "opacity": 0.25 } }
       ],
       layout: {
         name: "preset",
         positions: container.clientWidth < 560 ? mobilePositions : desktopPositions
       },
       autoungrabify: true,
       minZoom: 0.1, maxZoom: 2.5
     });

     function applyNodeScale() {
       const compact = container.clientWidth < 560;
       cy.nodes().style({
         width: compact ? 132 : 176,
         height: compact ? 68 : 76,
         "font-size": compact ? 11 : 12,
         "text-max-width": compact ? 116 : 156
       });
       cy.nodes('[type = "core"]').style({
         width: compact ? 150 : 198,
         height: compact ? 84 : 100,
         "text-max-width": compact ? 132 : 174
       });
       cy.nodes('[type = "output"]').style({
         width: compact ? 138 : 190,
         height: compact ? 72 : 82,
         "text-max-width": compact ? 120 : 168
       });
     }
     applyNodeScale();

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
     let compactLayout = container.clientWidth < 560;
     function applyResponsiveLayout() {
       const shouldCompact = container.clientWidth < 560;
       applyNodeScale();
       if (shouldCompact !== compactLayout) {
         compactLayout = shouldCompact;
         cy.layout({
           name: "preset",
           positions: compactLayout ? mobilePositions : desktopPositions,
           animate: false
         }).run();
       }
     }
     function fitGraph() {
       cy.resize();
       applyResponsiveLayout();
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

Examples of FMU host workflows
==============================

.. list-table::
   :header-rows: 1
   :widths: 28 34 38

   * - Host ecosystem
     - Why it matters
     - Example use with TMHP
   * - `Modelica Buildings Library
       <https://simulationresearch.lbl.gov/modelica/>`_
     - LBNL's Buildings library provides dynamic models for building,
       district-energy, HVAC, storage, and control systems, and its
       project materials explicitly cover Spawn/EnergyPlus coupling.
     - Use a Modelica plant and controls model around a TMHP heat-pump
       FMU, or compare TMHP against a Modelica heat-pump model in a
       district-energy study.
   * - `Spawn of EnergyPlus
       <https://www.energy.gov/cmei/buildings/articles/spawn-energyplus-spawn>`_
       and `EnergyPlusToFMU
       <https://simulationresearch.lbl.gov/fmu/EnergyPlus/export/>`_
     - Spawn combines EnergyPlus loads/envelope with Modelica controls
       through FMI-based co-simulation; EnergyPlusToFMU exports
       EnergyPlus as an FMU for co-simulation.
     - Co-simulate an EnergyPlus envelope FMU with a TMHP heat-pump FMU
       and a supervisory controller, keeping each domain in the tool that
       models it best.
   * - `OpenModelica / OMSimulator
       <https://openmodelica.org/doc/OpenModelicaUsersGuide/v1.12.0/omsimulator.html>`_
       and `Dymola
       <https://www.3ds.com/products/catia/dymola/export-capabilities-interfacing-other-software>`_
     - Modelica tools can import/export FMUs and build composite
       co-simulation models that mix Modelica and non-Modelica
       submodels.
     - Put TMHP's cycle-resolved ASHPB next to Modelica hydronic loops,
       tanks, district plants, or controllers.
   * - `FMPy <https://github.com/CATIA-Systems/FMPy>`_
     - FMPy is a Python library and GUI for inspecting and simulating
       FMUs across FMI major versions, including Co-Simulation FMUs.
     - Run local smoke tests, parameter sweeps, notebooks, and regression
       comparisons between FMU output and native TMHP Python output.
   * - `Simulink FMU block
       <https://www.mathworks.com/help/simulink/ref_extras/fmu.html>`_
     - Simulink can import FMUs and run Co-Simulation FMUs as external
       components in controller-oriented models.
     - Couple TMHP to controller prototypes or hardware-in-the-loop style
       experiments while keeping the heat-pump physics in the FMU.

.. toctree::
   :maxdepth: 1
   :hidden:

   energyplus-python
   fmu
