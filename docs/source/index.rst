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

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: 🚀 Getting Started
        :link: getting-started/index
        :link-type: doc

        Installation guide and your first simulation in minutes.

    .. grid-item-card:: 📚 Concepts
        :link: concepts/index
        :link-type: doc

        Why physics-based, how the cycle is assembled, and how to
        read the diagnostic flags every call returns.

    .. grid-item-card:: 🧪 Tutorials
        :link: tutorials/index
        :link-type: doc

        Focused walkthroughs: swap refrigerants, drive realistic
        schedules, compose subsystems.

    .. grid-item-card:: 🔧 API Reference
        :link: api/index
        :link-type: doc

        Complete API documentation for every model class and
        helper module.

    .. grid-item-card:: 🎯 Validation
        :link: validation/index
        :link-type: doc

        ASHPB benchmarked against 15 Samsung EHS catalogue
        operating points — parity plot, per-point table, and
        the reproducibility script.

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
