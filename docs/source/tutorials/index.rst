=========
Tutorials
=========

Focused, end-to-end walkthroughs that pick up where Getting Started
leaves off. Each tutorial is self-contained — copy the snippet, change
one or two values, and you have a working starting point.

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: Swap refrigerants
        :link: swap-refrigerant
        :link-type: doc

        Sweep R32, R290, R410A, R134a at one operating point and
        compare COP — no recalibration required.

    .. grid-item-card:: Realistic dynamic simulation
        :link: realistic-dynamic-simulation
        :link-type: doc

        Extend the 24-hour Getting Started example with a real DHW
        draw profile, a sinusoidal outdoor schedule, and CSV output.

    .. grid-item-card:: Compose subsystems
        :link: compose-subsystems
        :link-type: doc

        Wire a ``SolarThermalCollector`` onto ``ASHPB_STC_preheat`` and
        feed irradiance schedules into ``analyze_dynamic``.

    .. grid-item-card:: Visualize the thermodynamic cycle
        :link: visualize-the-cycle
        :link-type: doc

        Plot a solved refrigerant cycle on a pressure–enthalpy
        chart using only CoolProp and Matplotlib.

.. toctree::
    :maxdepth: 1
    :hidden:

    swap-refrigerant
    realistic-dynamic-simulation
    compose-subsystems
    visualize-the-cycle
