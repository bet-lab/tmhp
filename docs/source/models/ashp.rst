================================================
Air-source heat pump (ASHP — space conditioning)
================================================

ASHP conditions a building zone (heating + cooling) rather than
charging a DHW tank. The refrigerant cycle and outdoor-coil source
side are shared with ASHPB; what differs is the load side — a zone
energy balance instead of a tank.

Overview
========

The class is :class:`tmhp.AirSourceHeatPump`. Use it when the heat
pump's job is space conditioning rather than DHW production.

Base usage
==========

.. code-block:: python

   from tmhp import AirSourceHeatPump

   ashp = AirSourceHeatPump(ref="R32")

   # See API reference below for the full constructor and
   # analyze_steady / analyze_dynamic signatures.

Source-side mechanics
=====================

Identical to ASHPB — outdoor coil with variable-speed fan, ε-NTU
air-side heat exchanger.

Sink-side mechanics
===================

A zone temperature / load proxy stands in for the building. The
heat pump's condenser duty serves whatever space-heating or
cooling load the caller supplies; there is no tank energy balance.

API reference
=============

.. automodule:: tmhp.air_source_heat_pump
    :members:
    :undoc-members:
    :show-inheritance:
