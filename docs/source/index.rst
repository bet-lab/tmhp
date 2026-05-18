.. Thermodynamic Models for Heat Pumps documentation master file

===================================
Thermodynamic Models for Heat Pumps
===================================

A physics-based Python library for heat pump simulation.

.. rst-class:: lead

   First-principles dynamic models for air-source, ground-source, and
   water-source heat pumps — covering DHW, space heating, and space
   cooling.

``tmhp`` solves the closed refrigerant cycle at every time step using
`CoolProp <http://www.coolprop.org>`_ as the equation-of-state
backend. The same model code applies across refrigerants and
operating envelopes, with no manufacturer-specific curve fits and no
per-unit recalibration.

.. container:: hero-badges

   .. image:: https://img.shields.io/badge/python-3.10--3.13-3776ab?logo=python&logoColor=white
      :alt: Python 3.10 – 3.13
      :target: https://www.python.org/downloads/

   .. image:: https://img.shields.io/badge/license-MIT-success
      :alt: MIT License
      :target: https://github.com/bet-lab/tmhp/blob/main/LICENSE

   .. image:: https://img.shields.io/badge/status-alpha-orange
      :alt: Development status — Alpha

.. container:: hero-cta

   :doc:`Install <getting-started/installation>`
   :doc:`Quick start <getting-started/quickstart>`
   :doc:`Validation <validation/index>`
   `GitHub <https://github.com/bet-lab/tmhp>`_

.. raw:: html

   <div id="hero-motion-root" class="hero">
     <div class="hero-stats">
       <div class="hero-stat"><span class="hero-metric" data-target="15">0</span>
         <span class="hero-stat-label">benchmark points</span></div>
       <div class="hero-stat"><span class="hero-metric" data-target="5">0</span>
         <span class="hero-stat-label">model families</span></div>
       <div class="hero-stat"><span class="hero-metric" data-target="0">0</span>
         <span class="hero-stat-label">fitted curves</span></div>
     </div>
     <svg class="hero-sketch" viewBox="0 0 300 140" aria-hidden="true">
       <path d="M 20 110 Q 30 70 70 55 Q 110 40 150 40 Q 190 40 220 55 Q 250 70 260 110"
             fill="#edf2fe" stroke="#3a5bc7" stroke-width="1"/>
       <path d="M 40 90 L 40 50 L 210 50 L 210 90 Z"
             fill="none" stroke="#3e63dd" stroke-width="2"/>
     </svg>
   </div>
   <script src="_static/js/widgets/hero-motion.js" defer></script>

.. grid:: 1 2 2 3
    :gutter: 3
    :class-container: landing-cards

    .. grid-item-card:: Getting Started
        :link: getting-started/index
        :link-type: doc

        Install with ``uv``, run your first steady-state, then
        drive a 24-hour dynamic simulation.

    .. grid-item-card:: Concepts
        :link: concepts/index
        :link-type: doc

        Why first-principles, how the cycle is assembled, and
        how to read the diagnostic flags every call returns.

    .. grid-item-card:: Models
        :link: models/index
        :link-type: doc

        ASHPB / GSHPB / WSHPB plus the space-conditioning ASHP /
        GSHP — each one a 1-stop page with source-side mechanics,
        composed subsystem variants, and API reference.

    .. grid-item-card:: Tutorials
        :link: tutorials/index
        :link-type: doc

        Focused walkthroughs — swap refrigerants, drive realistic
        schedules, compose PV / STC / ESS subsystems.

    .. grid-item-card:: API Reference
        :link: api/index
        :link-type: doc

        Every model, support module, and helper exposed by the
        ``tmhp`` package, with full type signatures.

    .. grid-item-card:: Validation
        :link: validation/index
        :link-type: doc

        ASHPB benchmarked against 15 Samsung EHS catalogue
        points — parity plot, per-point table, reproducibility.

    .. grid-item-card:: Visualize
        :link: tutorials/visualize-the-cycle
        :link-type: doc

        Plot a solved refrigerant cycle on a P–h chart using
        only CoolProp and Matplotlib.

.. toctree::
   :maxdepth: 2
   :caption: Documentation
   :hidden:

   getting-started/index
   concepts/index
   models/index
   tutorials/index
   api/index
   validation/index

.. toctree::
   :maxdepth: 1
   :caption: Project Links
   :hidden:

   GitHub Repository <https://github.com/bet-lab/tmhp>
   Sister project — Energy-Exergy Analysis Engine <https://github.com/bet-lab/enex-analysis-engine>
