=====================
FMI 2.0 FMU export
=====================

TMHP's FMU adapter wraps
:class:`~tmhp.AirSourceHeatPumpBoiler` as an FMI 2.0 co-simulation
component. The FMI master owns the communication schedule; the FMU owns
the ASHPB dynamic state and advances it through
:meth:`~tmhp.AirSourceHeatPumpBoiler.step` at each ``do_step`` call.

Use this path when TMHP needs to participate in a tool-level
co-simulation workflow, or when a non-Python master should drive a
cycle-resolved ASHPB component with explicit FMI variables.

Install the optional FMU tooling
================================

The core TMHP package does not install PythonFMU or FMPy. Add the
``integrations`` extra when building or smoke-testing the FMU:

.. code-block:: bash

   uv sync --extra integrations --locked

This installs:

- ``pythonfmu`` for building the FMI 2.0 co-simulation FMU.
- ``fmpy`` for model-description validation and local smoke simulation.

Build and simulate
==================

Build from the repository root:

.. code-block:: bash

   uv run pythonfmu build -f src/tmhp/integrations/fmu.py .

PythonFMU writes ``TmhpAshpbSlave.fmu`` into the current output
directory. A local smoke test can then validate and simulate the FMU
through FMPy:

.. code-block:: python

   from fmpy import simulate_fmu
   from fmpy.validation import validate_fmu

   assert validate_fmu("TmhpAshpbSlave.fmu") == []

   result = simulate_fmu(
       "TmhpAshpbSlave.fmu",
       stop_time=3600.0,
       output=[
           "E_cmp",
           "E_tot",
           "Q_ref_tank",
           "cop_sys",
           "T_tank_w",
           "converged",
           "failure_reason",
       ],
   )

Runtime contract
================

The FMU is a tool-coupling artifact, not a hermetic binary. The
importing environment must provide a compatible Python runtime plus
TMHP, CoolProp, NumPy, SciPy, and the other native dependencies for the
target operating system, architecture, and Python ABI.

The adapter intentionally targets FMI 2.0 co-simulation only:

- TMHP exposes no continuous state derivatives for FMI model exchange.
- The ASHPB state is advanced in one pass for each communication step.
- Save-state and rollback support are outside the current adapter scope.
- FMI outputs are sanitized so NaN or infinity does not cross the
  importer boundary.

Input / output boundary
=======================

The FMU declares units in ``modelDescription.xml`` for power,
temperature, volume flow, and dimensionless COP. Outputs are also listed
in ``ModelStructure/InitialUnknowns`` so importers can resolve the
initial dependency set.

.. list-table::
   :header-rows: 1
   :widths: 22 26 52

   * - Causality
     - Variable
     - Meaning
   * - Parameter
     - ``ref``
     - Refrigerant name. Default ``R32``.
   * - Parameter
     - ``hp_capacity``
     - Nominal heat-pump capacity in watts.
   * - Parameter
     - ``T_tank_w_init``
     - Initial tank-water temperature in degrees Celsius.
   * - Parameter
     - ``T_sur``
     - Surrounding temperature for tank losses in degrees Celsius.
   * - Input
     - ``T0``
     - Outdoor or dead-state air temperature in degrees Celsius.
   * - Input
     - ``dhw_draw``
     - Service-water draw-off in ``m3/s``.
   * - Input
     - ``T_sup_w``
     - Mains make-up water temperature in degrees Celsius.
   * - Output
     - ``E_cmp``
     - Compressor electric power in watts.
   * - Output
     - ``E_tot``
     - Total system electric power in watts.
   * - Output
     - ``Q_ref_tank``
     - Refrigerant-to-tank heat transfer in watts.
   * - Output
     - ``cop_sys``
     - System COP including auxiliary loads.
   * - Output
     - ``T_tank_w``
     - Updated tank-water temperature in degrees Celsius.
   * - Output
     - ``hp_is_on``
     - Whether the heat pump is active for this step.
   * - Output
     - ``converged``
     - Whether the TMHP cycle solve accepted the step result.
   * - Output
     - ``failure_reason``
     - Step-level diagnostic reason, or ``none``.

Invalid importer inputs
=======================

Before advancing the internal state, the slave rejects non-finite time
or input values, non-positive communication step sizes, and negative
``dhw_draw``. In that case ``do_step`` returns ``False`` and the
diagnostic outputs are set to:

.. code-block:: text

   hp_is_on = false
   converged = false
   failure_reason = "invalid_input"

The state is not advanced for that rejected step.

Relationship to native Python simulation
========================================

The FMU path is intentionally aligned with native dynamic simulation:
each ``do_step`` call maps to one public
:meth:`~tmhp.AirSourceHeatPumpBoiler.step` call. For smoke testing,
compare FMU outputs against a native ``analyze_dynamic()`` run over the
same schedule, especially ``E_cmp``, ``E_tot``, ``Q_ref_tank``,
``cop_sys``, and ``T_tank_w``.

API reference
=============

The implementation API is documented at :mod:`tmhp.integrations.fmu`.
