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
       padding: 16px 18px;
       position: relative;
       max-width: 100%;
     }
     #tmhp-integration-boundary {
       width: 100%;
       height: 320px;
       border: 1px solid #e2e8f0;
       border-radius: 6px;
       background:
         linear-gradient(90deg, rgba(148, 163, 184, 0.10) 1px, transparent 1px),
         linear-gradient(180deg, rgba(148, 163, 184, 0.10) 1px, transparent 1px),
         #fbfdff;
       background-size: 40px 40px, 40px 40px, auto;
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
     .integration-graph-legend {
       display: flex; gap: 8px; flex-wrap: wrap;
       margin: 2px 110px 12px 0;
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
       text-align: center;
       font-style: italic;
       color: var(--sy-c-text-secondary, #6b7280);
       font-size: 0.92em;
       margin-top: 0.6em;
     }
     @media (max-width: 820px) {
       .integration-graph-toolbar {
         position: static;
         margin-bottom: 8px;
       }
       .integration-graph-legend {
         margin-right: 0;
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
       <span><i style="background:#e8f1ff;color:#2563eb"></i>Boundary variables</span>
       <span><i style="background:#f5f3ff;color:#8b5cf6"></i>Public TMHP API</span>
       <span><i style="background:#dcfce7;color:#16a34a"></i>Shared core</span>
     </div>
     <div id="tmhp-integration-boundary"></div>
     <div id="tmhp-integration-info">
       <span class="placeholder">Click a node to see the integration contract.</span>
     </div>
     <p class="integration-graph-hint">Topology is fixed · scroll-wheel to zoom · drag empty space to pan</p>
   </div>

   <p class="integration-graph-caption">
     TMHP integration data flow. EnergyPlus and FMI hosts pass boundary
     variables through public TMHP seams; the shared heat-pump core solves
     once behind those seams and returns heat, power, COP, and state values.
   </p>

   <script src="../_static/js/lib/cytoscape.min.js"></script>
   <script>
   (function () {
     const el = document.getElementById("tmhp-integration-boundary");
     if (!el || typeof cytoscape === "undefined") return;

     const cy = cytoscape({
       container: el,
       autoungrabify: true,
       boxSelectionEnabled: false,
       layout: { name: "preset", fit: false },
       elements: [
         { data: { id: "hostGroup", label: "External host tools", type: "group" }, classes: "group hostGroup" },
         { data: { id: "contractGroup", label: "Adapter Contracts", type: "group" }, classes: "group contractGroup" },
         { data: {
             id: "ep", parent: "hostGroup", label: "EnergyPlus\nplant loop",
             title: "EnergyPlus plant loop", type: "external",
             contract: "Owns the plant loop, timestep, dispatch request, and storage-tank state.",
             code: "PlantComponent:UserDefined + PythonPlugin:SearchPaths",
             api: "energyplus-python.html"
           }, classes: "host steady", position: { x: 76, y: 112 } },
         { data: {
             id: "fm", parent: "hostGroup", label: "FMI master\nFMPy / OMS",
             title: "FMI master", type: "external",
             contract: "Owns the co-simulation schedule and sets FMI input variables before each communication step.",
             code: "FMI 2.0/3.0 Co-Simulation importer",
             api: "fmu.html"
           }, classes: "host dynamic", position: { x: 76, y: 232 } },
         { data: {
             id: "eb", parent: "contractGroup", label: "Plant boundary\nT_in, mdot\nload, T0",
             title: "Plant boundary", type: "boundary",
             contract: "The EnergyPlus adapter maps plant-loop state into the steady TMHP request boundary.",
             code: "T_in, mdot, load, T0",
             api: "energyplus-python.html#input-output-boundary"
           }, classes: "boundary steady", position: { x: 240, y: 112 } },
         { data: {
             id: "fb", parent: "contractGroup", label: "FMU variables\nT0, draw\nT_sup",
             title: "FMU variables", type: "boundary",
             contract: "The FMU adapter exposes weather, draw, and supply-temperature variables to the importing FMI master.",
             code: "T0, dhw_draw, T_sup_w",
             api: "fmu.html#input-output-boundary"
           }, classes: "boundary dynamic", position: { x: 240, y: 232 } },
         { data: {
             id: "es", parent: "contractGroup", label: "steady seam\nanalyze_steady()",
             title: "analyze_steady()", type: "seam",
             contract: "Answers one plant-solver request without advancing a TMHP-owned dynamic state.",
             code: "AirSourceHeatPumpBoiler.analyze_steady(...)",
             api: "../models/ashpb.html"
           }, classes: "seam steady", position: { x: 365, y: 112 } },
         { data: {
             id: "fs", parent: "contractGroup", label: "dynamic seam\nstep()",
             title: "step()", type: "seam",
             contract: "Advances one communication step for a dynamic TMHP-owned state.",
             code: "state, result = hp.step(state, inputs, step_size)",
             api: "../getting-started/first-dynamic-simulation.html"
           }, classes: "seam dynamic", position: { x: 365, y: 232 } },
         { data: {
             id: "core", label: "TMHP shared\nheat pump\ncore",
             title: "TMHP shared heat-pump core", type: "core",
             contract: "Keeps the heat-pump model implementation behind stable public seams, so future heat-pump families can reuse the same integration boundary.",
             code: "heat-pump model + refrigerant/cycle helpers",
             api: "../concepts/cycle-architecture.html"
           }, classes: "core", position: { x: 500, y: 172 } },
         { data: {
             id: "out", label: "Returned values\nheat, power\nCOP, state",
             title: "Returned values", type: "output",
             contract: "Returns adapter-specific outputs to the host: EnergyPlus actuators/globals or FMI output variables.",
             code: "heat, power, COP, state, diagnostics",
             api: "fmu.html#input-output-boundary"
           }, classes: "output", position: { x: 650, y: 172 } },
         { data: { source: "ep", target: "eb" }, classes: "steady" },
         { data: { source: "fm", target: "fb" }, classes: "dynamic" },
         { data: { source: "eb", target: "es" }, classes: "steady" },
         { data: { source: "fb", target: "fs" }, classes: "dynamic" },
         { data: { source: "es", target: "core" }, classes: "steady corelink" },
         { data: { source: "fs", target: "core" }, classes: "dynamic corelink" },
         { data: { source: "core", target: "out" }, classes: "return" }
       ],
       style: [
         {
           selector: "node",
           style: {
             "shape": "round-rectangle",
             "width": 112,
             "height": 58,
             "background-color": "#f8fafc",
             "border-width": 0.7,
             "border-color": "#94a3b8",
             "label": "data(label)",
             "font-family": "Inter Variable, system-ui, sans-serif",
             "font-size": 10.8,
             "font-weight": 650,
             "line-height": 1.2,
             "text-wrap": "wrap",
             "text-max-width": 98,
             "text-valign": "center",
             "text-halign": "center",
             "color": "#172033",
             "shadow-blur": 8,
             "shadow-color": "#0f172a",
             "shadow-opacity": 0.08,
             "shadow-offset-x": 0,
             "shadow-offset-y": 2,
             "overlay-opacity": 0
           }
         },
         {
           selector: ".group",
           style: {
             "shape": "round-rectangle",
             "background-color": "#fffde1",
             "background-opacity": 0.72,
             "border-color": "#a6a821",
             "border-width": 0.65,
             "padding": 22,
             "compound-sizing-wrt-labels": "include",
             "label": "data(label)",
             "text-valign": "top",
             "text-halign": "center",
             "text-margin-y": 10,
             "text-wrap": "none",
             "text-max-width": 180,
             "text-background-color": "#fbfdff",
             "text-background-opacity": 0.96,
             "text-background-padding": 3,
             "text-background-shape": "roundrectangle",
             "font-size": 11.5,
             "font-weight": 700,
             "color": "#334155",
             "shadow-opacity": 0
           }
         },
         { selector: ".hostGroup", style: { "padding": 22 } },
         { selector: ".contractGroup", style: { "padding": 22 } },
         { selector: ".host", style: { "background-color": "#fff7d6", "border-color": "#d97706", "color": "#7c2d12" } },
         { selector: ".boundary", style: { "background-color": "#e8f1ff", "border-color": "#2563eb", "color": "#1e3a8a", "font-family": "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace", "font-size": 10.2, "text-max-width": 100 } },
         { selector: ".seam", style: { "background-color": "#f4f0ff", "border-color": "#7c3aed", "color": "#4c1d95", "border-style": "dashed", "font-family": "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace", "font-size": 10.2, "text-max-width": 100 } },
         { selector: ".core", style: { "shape": "ellipse", "background-color": "#dcfce7", "border-color": "#16a34a", "border-width": 1.1, "color": "#166534", "width": 98, "height": 98, "font-size": 10.8, "font-weight": 650, "text-max-width": 82, "shadow-opacity": 0.12 } },
         { selector: ".output", style: { "background-color": "#f1f5f9", "border-color": "#64748b", "color": "#334155", "font-size": 10.6, "text-max-width": 98 } },
         {
           selector: "edge",
           style: {
             "curve-style": "straight",
             "width": 1.45,
             "line-color": "#2f343b",
             "target-arrow-color": "#2f343b",
             "target-arrow-shape": "triangle",
             "arrow-scale": 0.78,
             "overlay-opacity": 0
           }
         },
         { selector: "edge.steady", style: { "line-color": "#9a3412", "target-arrow-color": "#9a3412", "opacity": 0.86 } },
         { selector: "edge.dynamic", style: { "line-color": "#2f343b", "target-arrow-color": "#2f343b", "opacity": 0.82 } },
         { selector: "edge.corelink", style: { "curve-style": "taxi", "taxi-direction": "rightward", "taxi-turn": "62%", "taxi-turn-min-distance": 18, "taxi-radius": 0, "width": 1.8, "opacity": 0.9 } },
         { selector: "edge.return", style: { "width": 1.8, "line-color": "#2f343b", "target-arrow-color": "#2f343b", "opacity": 0.9 } },
         { selector: "node:selected", style: { "border-width": 1.5 } },
         { selector: ".faded", style: { "opacity": 0.25 } }
       ],
       minZoom: 0.4,
       maxZoom: 2.5,
       wheelSensitivity: 0.2
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
       if (evt.target.data("type") === "group") return;
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

     function fit() {
       cy.fit(cy.elements(), 20);
       cy.center();
     }
     document.getElementById("tmhp-integration-fit").addEventListener("click", fit);
     document.getElementById("tmhp-integration-zoom-in").addEventListener("click",
       () => cy.zoom({ level: cy.zoom() * 1.25,
                       renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }));
     document.getElementById("tmhp-integration-zoom-out").addEventListener("click",
       () => cy.zoom({ level: cy.zoom() * 0.8,
                       renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }));
     fit();
     window.addEventListener("resize", function () {
       window.clearTimeout(el._tmhpResizeTimer);
       el._tmhpResizeTimer = window.setTimeout(fit, 90);
     });
     if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
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
