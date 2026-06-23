============
Integrations
============

Optional adapters for coupling TMHP to building-energy simulators and
co-simulation masters. These modules are intentionally kept out of the
top-level package import path so the core package remains usable without the
adapter-specific runtimes.

For usage-first guides, model boundaries, and simulator wiring, see
:doc:`../../integrations/energyplus-python` and
:doc:`../../integrations/fmu`.

Install the FMI dependencies with the ``integrations`` extra:

.. code-block:: bash

   uv sync --extra integrations --locked

The EnergyPlus adapter is different: ``pyenergyplus`` is supplied by an
EnergyPlus installation and is not a PyPI dependency.

Interoperability contracts
==========================

FMI co-simulation uses FMI 2.0 through PythonFMU. The generated FMU is a
tool-coupling artifact: Python, TMHP, CoolProp, NumPy, and SciPy must be
available in the importing environment. The FMU model description is validated
with FMPy in CI; all output variables are listed in both ``Outputs`` and
``InitialUnknowns`` so importers can resolve the initial output dependency set.
The XML also declares units for power, temperature, DHW draw, and COP so
importers can perform basic unit checks. The slave rejects invalid importer
inputs (non-finite time/input values, non-positive communication step sizes, or
negative DHW draw) before advancing the internal ``step()`` state and exposes
``failure_reason="invalid_input"``.

EnergyPlus coupling uses the Python Plugin DataExchange API. The adapter first
resolves and validates all handles, then reads only finite boundary values
before calling ``analyze_steady()``. Invalid boundary data is reported through
``issue_severe()``, the plant actuator is driven to a safe off state, and the
plugin returns a non-zero status instead of silently computing with bad data.
Compressor electricity is exposed with explicit plugin-global units:
``tmhp_E_cmp_J`` receives timestep energy in joules by multiplying cycle power
in watts by EnergyPlus's fractional-hour ``system_time_step()``, while optional
``tmhp_E_cmp_W`` receives the instantaneous cycle power. Older IDFs that
declare only ``tmhp_E_cmp`` are still accepted; that legacy global is treated as
a joule sink.

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
