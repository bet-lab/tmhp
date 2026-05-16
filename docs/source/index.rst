.. Physics-Based Heat Pump Models documentation master file

==============================
Physics-Based Heat Pump Models
==============================

.. rst-class:: lead

   First-principles dynamic models for air-source, ground-source, and
   water-source heat pump systems.

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

.. grid:: 2 2 4 4
   :gutter: 2
   :class-container: hero-cta

   .. grid-item::

      .. button-ref:: getting-started/installation
         :ref-type: doc
         :color: secondary
         :expand:
         :outline:

         Install

   .. grid-item::

      .. button-ref:: getting-started/quickstart
         :ref-type: doc
         :color: secondary
         :expand:
         :outline:

         Quick start

   .. grid-item::

      .. button-ref:: validation/index
         :ref-type: doc
         :color: secondary
         :expand:
         :outline:

         Validation

   .. grid-item::

      .. button-link:: https://github.com/bet-lab/physics-heatpump-models
         :color: secondary
         :expand:
         :outline:

         GitHub

.. grid:: 1 2 2 3
    :gutter: 3
    :class-container: landing-cards

    .. grid-item-card:: Getting Started
        :link: getting-started/index
        :link-type: doc

        Installation guide and your first simulation in minutes.

    .. grid-item-card:: Concepts
        :link: concepts/index
        :link-type: doc

        Why physics-based, how the cycle is assembled, and how to
        read the diagnostic flags every call returns.

    .. grid-item-card:: Tutorials
        :link: tutorials/index
        :link-type: doc

        Focused walkthroughs: swap refrigerants, drive realistic
        schedules, compose subsystems.

    .. grid-item-card:: API Reference
        :link: api/index
        :link-type: doc

        Complete API documentation for every model class and
        helper module.

    .. grid-item-card:: Validation
        :link: validation/index
        :link-type: doc

        ASHPB benchmarked against 15 Samsung EHS catalogue
        operating points — parity plot, per-point table, and
        the reproducibility script.

    .. grid-item-card:: Visualize
        :link: tutorials/visualize-the-cycle
        :link-type: doc

        Plot a solved refrigerant cycle on a P–h chart with only
        CoolProp and Matplotlib.

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
