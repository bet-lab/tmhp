.. Thermodynamic Models for Heat Pumps documentation master file

===================================
Thermodynamic Models for Heat Pumps
===================================

A general-purpose, physics-based heat pump modeling library.

.. rst-class:: lead

   First-principles dynamic models for air-source, ground-source, and
   water-source heat pump systems.

``tmhp`` solves the thermodynamic refrigerant cycle at every time
step using `CoolProp <http://www.coolprop.org>`_, so the same model
code applies across refrigerants and operating envelopes without
needing manufacturer-specific curve fits.

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
   tutorials/index
   api/index
   validation/index

.. toctree::
   :maxdepth: 1
   :caption: Project Links
   :hidden:

   GitHub Repository <https://github.com/bet-lab/tmhp>
   Sister project — Energy-Exergy Analysis Engine <https://github.com/bet-lab/enex-analysis-engine>
