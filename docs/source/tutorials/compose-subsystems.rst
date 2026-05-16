==================
Compose subsystems
==================

Solar thermal collectors, photovoltaic systems, and energy
storage are not modelled as separate top-level classes — they
plug into an existing heat-pump model. This tutorial walks
through the simplest such composition: ``ASHPB_STC_preheat``,
where a ``SolarThermalCollector`` heats the cold mains water
before it reaches the DHW tank.

The two pieces
==============

The :class:`~physics_hp.subsystems.SolarThermalCollector` is a
pure physics engine — given irradiance, ambient temperature, and
flow, it returns collector outlet temperature and absorbed heat.
It carries no simulation state.

:class:`~physics_hp.ashpb_stc_preheat.ASHPB_STC_preheat` extends
``AirSourceHeatPumpBoiler`` and owns the orchestration: when the
collector is warmer than the mains supply, it overrides the
tank-inlet temperature so the heat pump sees pre-heated water.

Putting them together
=====================

.. code-block:: python

   import numpy as np

   from physics_hp import ASHPB_STC_preheat
   from physics_hp.subsystems import SolarThermalCollector

   # Collector geometry. SolarThermalCollector is a dataclass — all
   # parameters have sensible defaults; override only what differs.
   stc = SolarThermalCollector(
       A_stc=4.0,             # 4 m² collector area
       stc_tilt=35.0,         # tilt angle from horizontal
       stc_azimuth=180.0,     # due south
   )

   model = ASHPB_STC_preheat(
       stc=stc,
       ref="R32",
   )

Driving it with irradiance
==========================

``analyze_dynamic`` accepts irradiance schedules in addition to
the outdoor-temperature and DHW schedules used in
:doc:`realistic-dynamic-simulation`. The two channels are
direct-normal (``I_DN_schedule``) and diffuse-horizontal
(``I_dH_schedule``) — both in W/m² per step.

.. code-block:: python

   dt_s                  = 60
   n_steps               = 24 * 3600 // dt_s
   minute_of_day         = np.arange(n_steps)
   hour_of_day           = minute_of_day / 60.0

   # Crude clear-sky irradiance: bell from 06:00 to 18:00, peak 800 W/m².
   day_window = (hour_of_day >= 6.0) & (hour_of_day <= 18.0)
   sun_shape  = np.sin(np.pi * (hour_of_day - 6.0) / 12.0)
   I_DN       = np.where(day_window, 800.0 * sun_shape, 0.0)
   I_dH       = np.where(day_window, 100.0 * sun_shape, 0.0)

   T0         = np.full(n_steps, 5.0)
   dhw        = np.zeros(n_steps)

   df = model.analyze_dynamic(
       simulation_period_sec = n_steps * dt_s,
       dt_s                  = dt_s,
       T_tank_w_init_C       = 50.0,
       dhw_usage_schedule    = dhw,
       T0_schedule           = T0,
       I_DN_schedule         = I_DN,
       I_dH_schedule         = I_dH,
   )

The STC is activated automatically inside its preheat window
(default 06:00–18:00). When the collector outlet beats the mains
supply, the result frame's tank-inlet temperature reflects the
boost.

Reading the contribution
========================

.. code-block:: python

   # Compare against a base case with the same operating conditions
   # but no solar — drive `AirSourceHeatPumpBoiler` with the same
   # schedules and difference the compressor energy.

   from physics_hp import AirSourceHeatPumpBoiler

   base = AirSourceHeatPumpBoiler(ref="R32").analyze_dynamic(
       simulation_period_sec = n_steps * dt_s,
       dt_s                  = dt_s,
       T_tank_w_init_C       = 50.0,
       dhw_usage_schedule    = dhw,
       T0_schedule           = T0,
   )

   def daily_kwh(s, dt_s=dt_s):
       return float(s.sum()) * dt_s / 3.6e6

   print(f"Base compressor energy : {daily_kwh(base['E_cmp [W]']):.2f} kWh")
   print(f"With STC preheat       : {daily_kwh(df['E_cmp [W]']):.2f} kWh")
   print(f"Saving                 : {daily_kwh(base['E_cmp [W]']) - daily_kwh(df['E_cmp [W]']):.2f} kWh")

The saving is whatever the STC pushed into the tank as preheat,
minus the small pump electricity cost the STC subsystem reports
in its own columns.

Other compositions
==================

Three other subsystems compose against ASHPB / GSHPB the same
way:

- :class:`~physics_hp.ashpb_stc_tank.ASHPB_STC_tank` — STC charges
  the top node of a stratified storage tank instead of the
  mains feed.
- :class:`~physics_hp.ashpb_pv_ess.ASHPB_PV_ESS` — photovoltaic
  generation + ESS supplies compressor and auxiliary loads
  before drawing grid power.
- The :class:`~physics_hp.gshpb_stc_preheat.GSHPB_STC_preheat`,
  :class:`~physics_hp.gshpb_stc_tank.GSHPB_STC_tank`, and
  :class:`~physics_hp.gshpb_pv_ess.GSHPB_PV_ESS` mirrors on the
  ground-source side.

The constructor pattern is the same in every case: instantiate
the subsystem, hand it to the composed model, pass the
appropriate schedules to ``analyze_dynamic``.
