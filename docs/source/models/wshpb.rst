=====================================
Water-source heat pump boiler (WSHPB)
=====================================

Source side is a water loop with a prescribed inlet temperature;
sink side is the same DHW tank used by ASHPB / GSHPB.

Overview
========

The class is :class:`tmhp.WaterSourceHeatPumpBoiler`. Unlike GSHPB,
WSHPB takes the source-side inlet temperature as a schedule input
rather than computing it from a borehole field — useful when the
water loop is driven by an external simulation or measurement.

Base usage
==========

.. code-block:: python

   from tmhp import WaterSourceHeatPumpBoiler

   wshpb = WaterSourceHeatPumpBoiler(ref="R134a")

   result = wshpb.analyze_steady(
       T_tank_w=55.0,
       T_source=15.0,     # water-loop inlet [°C]
       Q_ref_cond=8_000,
   )

Source-side mechanics
=====================

A single ε-NTU heat exchanger between the refrigerant evaporator
and the source-side water loop. No borehole transient — the loop
inlet temperature is whatever the user supplies.

Sink-side mechanics
===================

Same DHW tank as ASHPB / GSHPB.

API reference
=============

.. automodule:: tmhp.water_source_heat_pump_boiler
    :members:
    :undoc-members:
    :show-inheritance:
