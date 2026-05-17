=============
API Reference
=============

Complete API documentation for the ``tmhp`` package, organized by
module group. Each card below links to a sub-section that documents the
classes and functions in that group.

Models
======

System-level heat pump models. Each model couples a refrigerant cycle to a
source side (air, ground, water) and a sink side (DHW tank, building load,
hybrid PV / STC / ESS configurations).

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: Air-source heat pump boilers
        :link: models/ashpb
        :link-type: doc

        ASHPB core model plus three composed variants:
        STC preheat, STC stratified tank, PV + ESS.

    .. grid-item-card:: Ground-source heat pump boilers
        :link: models/gshpb
        :link-type: doc

        GSHPB core model with g-function borehole, plus
        STC preheat, STC stratified tank, PV + ESS variants.

    .. grid-item-card:: Water-source heat pump boiler
        :link: models/wshpb
        :link-type: doc

        Dynamic WSHPB model.

    .. grid-item-card:: Space-conditioning heat pumps
        :link: models/space-conditioning
        :link-type: doc

        Air-source and ground-source heat pumps for
        building heating and cooling loads.

Support modules
===============

Lower-level building blocks used by the system models above.

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: Refrigerant & thermodynamics
        :link: support/refrigerant-thermo
        :link-type: doc

        CoolProp state-point helpers, cycle analysis, and
        COP correlations.

    .. grid-item-card:: Heat transfer & exchangers
        :link: support/heat-transfer
        :link-type: doc

        ε-NTU heat exchanger model, air-side fan and
        heat-exchanger calculations, and borehole g-function.

    .. grid-item-card:: Demand & weather
        :link: support/demand-weather
        :link-type: doc

        Outdoor air temperature utilities and domestic hot
        water demand profiles.

    .. grid-item-card:: Subsystems
        :link: support/subsystems
        :link-type: doc

        Solar thermal collector, photovoltaic system,
        energy storage system, and UV treatment.

    .. grid-item-card:: Simulation helpers
        :link: support/simulation
        :link-type: doc

        Per-step dynamic context, energy / exergy helpers,
        and stdout summary tables.

    .. grid-item-card:: Visualization
        :link: support/visualization
        :link-type: doc

        Plotting facade and Mollier (T-h / P-h / T-s)
        diagrams.

    .. grid-item-card:: Utilities & constants
        :link: support/utilities
        :link-type: doc

        Unit-conversion helpers and physical constants.

.. toctree::
    :maxdepth: 2
    :hidden:

    models/index
    support/index
