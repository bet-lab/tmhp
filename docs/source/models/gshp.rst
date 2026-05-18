===================================================
Ground-source heat pump (GSHP — space conditioning)
===================================================

GSHP conditions a building zone, drawing or rejecting heat through
the same g-function borehole heat exchanger as GSHPB.

Overview
========

The class is :class:`tmhp.GroundSourceHeatPump`. Use it when the heat
pump's job is space conditioning rather than DHW production.

Base usage
==========

.. code-block:: python

   from tmhp import GroundSourceHeatPump

   gshp = GroundSourceHeatPump(
       ref="R410A",
       N_1=1, N_2=1,
       H_b=150.0,
   )

   # See API reference below for the full constructor and
   # analyze_steady / analyze_dynamic signatures.

Source-side mechanics
=====================

Same g-function-based borehole as :doc:`gshpb`. See that page for the
detailed mechanic and the g-function figure.

Sink-side mechanics
===================

A zone temperature / load proxy stands in for the building, as in
:doc:`ashp`.

API reference
=============

.. automodule:: tmhp.ground_source_heat_pump
    :members:
    :undoc-members:
    :show-inheritance:
