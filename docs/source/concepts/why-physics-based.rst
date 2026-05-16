==================
Why physics-based?
==================

Most building-energy simulators model a heat pump as an empirical
curve fit: a polynomial in (outdoor temperature, leaving-water
temperature) calibrated against the manufacturer's test points. That
approach is cheap and accurate *inside the calibration envelope*, but
it carries three structural limitations that this library is built
to remove.

The three structural limits of curve fits
==========================================

.. list-table::
    :header-rows: 1
    :widths: 30 35 35

    * -
      - Curve-fit models
      - ``physics_hp``
    * - **Operating range**
      - Tied to the manufacturer's test points; extrapolation is
        unreliable.
      - Predictive across the full refrigerant envelope — limited by
        the EOS, not by training data.
    * - **Refrigerant**
      - Baked into the fitted coefficients. Changing R410A → R290
        requires a new dataset.
      - The refrigerant is a constructor argument
        (``ref="R290"``). Anything CoolProp supports works.
    * - **State visibility**
      - Cycle state is hidden behind the fit. You see COP; you
        don't see why.
      - Every cycle node (compressor in/out, expander in/out,
        evaporator / condenser saturation) is in the result frame
        at every step.

What gets solved at every time step
====================================

Each call to ``analyze_steady`` or each step of ``analyze_dynamic``
solves a closed refrigerant cycle coupled to the surrounding
system. The condenser duty is the target; the evaporating
temperature is found by internally minimising compressor power, so
the cycle closes physically rather than via fitted coefficients.

.. list-table::
    :header-rows: 1
    :widths: 35 65

    * - Sub-model
      - Method
    * - Refrigerant state points
      - `CoolProp <http://www.coolprop.org>`_ (REFPROP-grade EOS).
    * - Compressor work
      - Isentropic + volumetric + mechanical efficiency.
    * - Condenser / evaporator
      - ε-NTU heat exchanger model.
    * - Outdoor unit fan
      - ASHRAE 90.1-style VSD power curve, air-side ε-NTU.
    * - Borehole (GSHP)
      - g-function via
        `pygfunction <https://github.com/MassimoCimmino/pygfunction>`_.
    * - PV / solar thermal
      - `pvlib <https://pvlib-python.readthedocs.io>`_-driven
        irradiance and power.
    * - Cycle closure
      - Internal minimisation → optimal evaporating temperature.

The same core cycle is reused across every system model — what
changes is the source side (air / ground / water) and the sink
side (DHW tank, building load, or hybrid PV / STC / ESS).

The compute trade-off
=====================

Solving an EOS state at every cycle node is more expensive than
evaluating a polynomial. In practice this lands around a few
hundred steps per second on a single core for a vanilla ASHPB —
fast enough that a year-long minute-resolution run is hours, not
minutes. If that's too slow for your use case, a fitted surrogate
is the right escape hatch; this library is calibrated against
commercial catalogue data well enough that the surrogate can be
trained against ``physics_hp`` itself rather than against new
bench data.
