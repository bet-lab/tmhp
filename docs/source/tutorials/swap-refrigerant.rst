==================
Swap refrigerants
==================

The refrigerant is a constructor argument on every model in
``physics_hp``. Changing it requires no recalibration and no
manufacturer data — pick any name CoolProp recognises and the
library re-solves the cycle from first principles.

This tutorial sweeps four common refrigerants at a single fixed
operating point and tabulates the resulting COP.

Sweep
=====

.. code-block:: python

   import pandas as pd

   from physics_hp import AirSourceHeatPumpBoiler

   T_tank_w   = 55.0   # °C
   T0         = 5.0    # °C
   Q_ref_cond = 8_000  # W

   refrigerants = ["R32", "R290", "R410A", "R134a"]

   rows = []
   for ref in refrigerants:
       ashpb = AirSourceHeatPumpBoiler(ref=ref)
       r = ashpb.analyze_steady(
           T_tank_w=T_tank_w,
           T0=T0,
           Q_ref_cond=Q_ref_cond,
       )
       rows.append({
           "ref": ref,
           "cop_ref [-]": r["cop_ref [-]"],
           "cop_sys [-]": r["cop_sys [-]"],
           "E_cmp [kW]": r["E_cmp [W]"] / 1_000,
           "T_evap_sat [°C]": r["T_ref_evap_sat [°C]"],
           "T_cond_sat [°C]": r["T_ref_cond_sat_v [°C]"],
           "failure_reason": r["failure_reason"],
       })

   df = pd.DataFrame(rows)
   print(df.to_string(index=False))

The output is a four-row DataFrame — same operating point, same
code path, four refrigerants. Compressor power, saturation
temperatures, and COP all move together with the refrigerant's
EOS.

Reading the result
==================

A few things to look for:

- ``failure_reason`` — should be ``none`` for all four at
  this operating point. If a refrigerant trips
  ``cycle_invalid`` or ``hx_not_converged``, see
  :doc:`../concepts/failure-reason-semantics`.
- **``cop_ref`` vs ``cop_sys``** — ``cop_ref`` is the cycle COP
  (condenser duty divided by compressor work). ``cop_sys`` also
  charges auxiliary power (fan, pumps) and is the figure that
  matches catalogue datasheets.
- **Saturation temperatures** — the evaporating temperature was
  found by the internal minimiser. Refrigerants with steeper
  saturation curves end up at different ``T_evap_sat`` even when
  the heat exchangers are identical.

Picking a refrigerant
=====================

The library doesn't decide for you. Each refrigerant trades off
COP, safety class, and environmental impact differently. Tabs
below summarise the four common picks at a glance.

.. tab-set::

    .. tab-item:: R32
        :sync: r32

        **Difluoromethane** · single-component HFC

        :bdg-success:`A2L low-flammability` :bdg-warning:`GWP ≈ 675`
        :bdg-info:`T_crit ≈ 78 °C`

        Default in this library — solid COP across the DHW
        envelope and the refrigerant Samsung used for the
        validation unit. Subcritical condensation up to about
        70 °C LWT.

    .. tab-item:: R290
        :sync: r290

        **Propane** · natural refrigerant

        :bdg-danger:`A3 flammable` :bdg-success:`GWP ≈ 3`
        :bdg-info:`T_crit ≈ 97 °C`

        Highest COP and lowest GWP of the four. Safety-charge
        limits constrain residential applications, but propane
        is the EU-friendly long-term pick.

    .. tab-item:: R410A
        :sync: r410a

        **R32 / R125 zeotropic blend** · legacy HFC

        :bdg-success:`A1 non-flammable` :bdg-danger:`GWP ≈ 2088`
        :bdg-info:`T_crit ≈ 72 °C`

        The blend most existing residential heat pumps were
        designed for. Strong precedent and tooling, but being
        phased out under F-gas regulation.

    .. tab-item:: R134a
        :sync: r134a

        **1,1,1,2-Tetrafluoroethane** · single-component HFC

        :bdg-success:`A1 non-flammable` :bdg-danger:`GWP ≈ 1430`
        :bdg-info:`T_crit ≈ 101 °C`

        High critical temperature makes it well-suited to
        high-LWT industrial heat-pump applications, but GWP and
        regulatory pressure limit residential use.

Screening criteria
------------------

Use the sweep above as a screening step against the constraints
that actually matter for your application:

- **Operating-point COP** — what this tutorial reports.
- **Flammability class** — A1 (R134a, R410A) → A2L (R32) → A3 (R290).
- **GWP** — R134a > R410A > R32 > R290 ≈ R744.
- **Critical temperature** — for transcritical CO₂ (R744), see
  :doc:`../concepts/refrigerant-and-coolprop`.

Once a candidate refrigerant is chosen, re-run a full annual
simulation with realistic schedules — see
:doc:`realistic-dynamic-simulation`.
