.. Physics-Based Heat Pump Models documentation master file

==============================
Physics-Based Heat Pump Models
==============================

.. rst-class:: lead

   **First-principles dynamic models for air-source, ground-source, and
   water-source heat pump systems.**

``physics_hp`` solves the thermodynamic refrigerant cycle at every time
step using `CoolProp <http://www.coolprop.org>`_, so the same model
code applies across refrigerants and operating envelopes without
needing manufacturer-specific curve fits.

.. container:: hero-badges

   .. image:: https://img.shields.io/badge/python-3.10--3.13-3776ab?logo=python&logoColor=white
      :alt: Python 3.10 – 3.13
      :target: https://www.python.org/downloads/

   .. image:: https://img.shields.io/badge/license-MIT-success
      :alt: MIT License
      :target: https://github.com/bet-lab/physics-heatpump-models/blob/main/LICENSE

   .. image:: https://img.shields.io/badge/status-alpha-orange
      :alt: Development status — Alpha

   .. image:: https://img.shields.io/badge/refrigerant-CoolProp-6366f1
      :alt: Powered by CoolProp
      :target: http://www.coolprop.org

   .. image:: https://img.shields.io/badge/validated-Samsung%20EHS%20R32-iris
      :alt: Validated against Samsung EHS Mono HT Quiet R32

.. grid:: 2 2 4 4
   :gutter: 2
   :class-container: hero-cta

   .. grid-item::

      .. button-ref:: getting-started/installation
         :ref-type: doc
         :color: primary
         :expand:
         :outline:

         Install ⤓

   .. grid-item::

      .. button-ref:: getting-started/quickstart
         :ref-type: doc
         :color: primary
         :expand:

         Quick start →

   .. grid-item::

      .. button-ref:: validation/index
         :ref-type: doc
         :color: primary
         :expand:
         :outline:

         Validation ✓

   .. grid-item::

      .. button-link:: https://github.com/bet-lab/physics-heatpump-models
         :color: primary
         :expand:
         :outline:

         GitHub ↗

.. rubric:: Explore the docs

.. grid:: 1 2 2 3
    :gutter: 3
    :class-container: landing-cards

    .. grid-item-card:: :octicon:`rocket;1.4em;sd-mr-1` Getting Started
        :link: getting-started/index
        :link-type: doc
        :class-card: sd-shadow-sm

        Installation guide and your first simulation in minutes.

        +++

        :bdg-primary-line:`install` :bdg-primary-line:`quickstart` :bdg-primary-line:`first run`

    .. grid-item-card:: :octicon:`book;1.4em;sd-mr-1` Concepts
        :link: concepts/index
        :link-type: doc
        :class-card: sd-shadow-sm

        Why physics-based, how the cycle is assembled, and how to
        read the diagnostic flags every call returns.

        +++

        :bdg-primary-line:`theory` :bdg-primary-line:`architecture` :bdg-primary-line:`diagnostics`

    .. grid-item-card:: :octicon:`beaker;1.4em;sd-mr-1` Tutorials
        :link: tutorials/index
        :link-type: doc
        :class-card: sd-shadow-sm

        Focused walkthroughs: swap refrigerants, drive realistic
        schedules, compose subsystems.

        +++

        :bdg-primary-line:`R32` :bdg-primary-line:`R290` :bdg-primary-line:`PV+ESS` :bdg-primary-line:`STC`

    .. grid-item-card:: :octicon:`code;1.4em;sd-mr-1` API Reference
        :link: api/index
        :link-type: doc
        :class-card: sd-shadow-sm

        Complete API documentation for every model class and
        helper module.

        +++

        :bdg-primary-line:`ASHPB` :bdg-primary-line:`GSHPB` :bdg-primary-line:`WSHPB`

    .. grid-item-card:: :octicon:`check-circle;1.4em;sd-mr-1` Validation
        :link: validation/index
        :link-type: doc
        :class-card: sd-shadow-sm

        ASHPB benchmarked against 15 Samsung EHS catalogue
        operating points — parity plot, per-point table, and
        the reproducibility script.

        +++

        :bdg-success-line:`MAPE 11.8%` :bdg-primary-line:`15 points`

    .. grid-item-card:: :octicon:`graph;1.4em;sd-mr-1` Visualize
        :link: tutorials/visualize-the-cycle
        :link-type: doc
        :class-card: sd-shadow-sm

        Plot a solved refrigerant cycle on a P–h chart with only
        CoolProp and Matplotlib.

        +++

        :bdg-primary-line:`P–h` :bdg-primary-line:`Mollier`

.. rubric:: At a glance

.. grid:: 2 2 4 4
    :gutter: 2
    :class-container: stat-grid

    .. grid-item-card:: :octicon:`flame;1.2em` 5 system families
        :class-card: sd-text-center sd-shadow-none stat-card

        ASHPB · GSHPB · WSHPB · ASHP · GSHP

    .. grid-item-card:: :octicon:`stack;1.2em` 6 subsystem variants
        :class-card: sd-text-center sd-shadow-none stat-card

        STC preheat, stratified tank, PV + ESS

    .. grid-item-card:: :octicon:`zap;1.2em` Any CoolProp refrigerant
        :class-card: sd-text-center sd-shadow-none stat-card

        R32, R290, R410A, R134a, R744 …

    .. grid-item-card:: :octicon:`pulse;1.2em` Minute-resolution dynamic
        :class-card: sd-text-center sd-shadow-none stat-card

        Implicit ``fsolve`` per step, robust to large ``dt``

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

   GitHub Repository <https://github.com/bet-lab/physics-heatpump-models>
   enex_analysis_engine <https://github.com/bet-lab/enex_analysis_engine>
