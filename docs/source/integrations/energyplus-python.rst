========================
EnergyPlus Python Plugin
========================

TMHP's EnergyPlus adapter exposes
:class:`~tmhp.AirSourceHeatPumpBoiler` as a
``PlantComponent:UserDefined`` surrogate. EnergyPlus still owns the
plant loop, timestep, load dispatch, and storage-tank objects; TMHP
answers each plant-solver call with a refrigerant-cycle-resolved steady
state through :meth:`~tmhp.AirSourceHeatPumpBoiler.analyze_steady`.

Use this path when you have an EnergyPlus model and want the heat pump
to be more physical than an empirical catalogue curve fit, without
moving the whole building simulation out of EnergyPlus.

Runtime contract
================

EnergyPlus Python Plugins run inside EnergyPlus's embedded CPython.
That means ``pyenergyplus`` comes from the EnergyPlus installation, not
from PyPI, and TMHP plus its native dependencies must be importable by
that embedded interpreter.

.. code-block:: text

   EnergyPlus plant solver
       -> PythonPlugin:SearchPaths
       -> tmhp.integrations.energyplus_plugin
       -> AirSourceHeatPumpBoiler.analyze_steady()

Practical setup:

1. Install TMHP into an environment compatible with the EnergyPlus
   embedded Python ABI.
2. Add that environment or package path with ``PythonPlugin:SearchPaths``.
3. Verify an import-only smoke plugin first. A wrong-ABI native wheel
   such as CoolProp can fail before the plant callback reaches useful
   logging.

IDF wiring
==========

The adapter expects one ``PlantComponent:UserDefined`` component and two
Python plugin managers:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - EnergyPlus object
     - TMHP binding
   * - ``PlantComponent:UserDefined``
     - Default name ``ASHPB_UserDefined`` unless ``TMHP_UD_NAME`` is set.
   * - Initialization program-calling manager
     - :class:`tmhp.integrations.energyplus_plugin.TmhpPlantInit`
       sizes the plant connection so EnergyPlus can dispatch load.
   * - Simulation program-calling manager
     - :class:`tmhp.integrations.energyplus_plugin.TmhpPlantSurrogate`
       reads loop boundary values, solves TMHP, and writes actuators.
   * - ``PythonPlugin:Variables``
     - Declare ``tmhp_E_cmp_J`` for timestep energy. Optionally declare
       ``tmhp_E_cmp_W`` for instantaneous compressor power.

Input / output boundary
=======================

The plugin reads only finite EnergyPlus boundary values before calling
TMHP. Invalid inputs are reported through ``issue_severe()``, the plant
component is driven to a safe off state, and the callback returns a
non-zero status instead of computing with bad values.

.. list-table::
   :header-rows: 1
   :widths: 26 30 44

   * - Direction
     - Field
     - Meaning
   * - EnergyPlus -> TMHP
     - Inlet temperature
     - Plant Connection 1 inlet water temperature.
   * - EnergyPlus -> TMHP
     - Inlet mass flow rate
     - Current loop-side flow available to the user-defined component.
   * - EnergyPlus -> TMHP
     - Inlet specific heat
     - Loop fluid heat capacity used to convert heat rate to outlet
       temperature.
   * - EnergyPlus -> TMHP
     - Load request
     - Positive heating load request for the plant component.
   * - EnergyPlus -> TMHP
     - Outdoor drybulb temperature
     - Source-side air temperature ``T0`` for the ASHPB cycle solve.
   * - TMHP -> EnergyPlus
     - Outlet temperature actuator
     - Inlet temperature plus delivered heat divided by ``m_dot * cp``,
       clamped inside the liquid-water property range.
   * - TMHP -> EnergyPlus
     - Mass-flow actuator
     - Requests design flow when load is present and EnergyPlus has not
       yet provided loop flow.
   * - TMHP -> EnergyPlus
     - ``tmhp_E_cmp_J``
     - Timestep compressor electricity in joules.
   * - TMHP -> EnergyPlus
     - ``tmhp_E_cmp_W``
     - Optional instantaneous compressor power in watts.

Configuration
=============

The adapter reads its configuration once at import from environment
variables:

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Variable
     - Meaning
   * - ``TMHP_ASHPB_REF``
     - Refrigerant name. Default ``R32``.
   * - ``TMHP_ASHPB_CAPACITY``
     - Nominal heat-pump capacity in watts. Default ``15000``.
   * - ``TMHP_UD_NAME``
     - ``PlantComponent:UserDefined`` object name. Default
       ``ASHPB_UserDefined``.
   * - ``TMHP_LOOP_DESIGN_VDOT``
     - Design loop volume flow in ``m3/s``. Default ``0.003``.
   * - ``TMHP_EPLUS_ECMP_ENERGY_GLOBAL``
     - Plugin global receiving timestep energy in joules. Default
       ``tmhp_E_cmp_J``.
   * - ``TMHP_EPLUS_ECMP_POWER_GLOBAL``
     - Optional plugin global receiving instantaneous power in watts.
       Default ``tmhp_E_cmp_W``.
   * - ``TMHP_PLUGIN_LOG``
     - Optional path for per-call and convergence-tally logging.

Why this uses ``analyze_steady()``
==================================

EnergyPlus is already the dynamic simulation environment. It owns the
plant loop iteration, the storage tank, and the timestep integration.
The plugin therefore asks TMHP for a steady component response:

.. code-block:: python

   result = hp.analyze_steady(
       T_tank_w=t_in,
       T0=t0,
       Q_ref_tank=q_target,
   )

The FMU adapter uses :meth:`~tmhp.AirSourceHeatPumpBoiler.step` instead
because the FMU owns its own dynamic state. Keeping those seams separate
prevents EnergyPlus tank state and FMU tank state from being mixed.

API reference
=============

The implementation API is documented at
:mod:`tmhp.integrations.energyplus_plugin`.
