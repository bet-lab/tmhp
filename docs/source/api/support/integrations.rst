============
Integrations
============

Optional adapters for coupling ``tmhp`` to building-energy simulators and
co-simulation masters. These modules are intentionally kept out of the
top-level ``tmhp`` import path so the core package remains usable without the
adapter-specific runtimes.

Install the FMI dependencies with the ``integrations`` extra:

.. code-block:: bash

   uv sync --extra integrations --locked

The EnergyPlus adapter is different: ``pyenergyplus`` is supplied by an
EnergyPlus installation and is not a PyPI dependency.

Adapter package
===============

.. automodule:: tmhp.integrations
    :members:
    :undoc-members:
    :show-inheritance:

FMI co-simulation
=================

.. automodule:: tmhp.integrations.fmu
    :members:
    :undoc-members:
    :show-inheritance:

EnergyPlus Python Plugin
========================

.. automodule:: tmhp.integrations.energyplus_plugin
    :members:
    :undoc-members:
    :show-inheritance:
