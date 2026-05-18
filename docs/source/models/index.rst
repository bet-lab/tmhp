======
Models
======

System-level heat pump models — the classes you instantiate directly.
Each page below is a 1-stop reference for one model family: how it
plugs the shared refrigerant cycle into a specific source / sink
pairing, what the system-specific mechanics look like, how to compose
subsystems (STC, PV + ESS) on top, and the full API reference.

ASHPB is the most commonly used model and the one Getting Started
walks you through. The remaining pages mirror the same template so
moving between source families feels uniform.

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: Air-source heat pump boiler
        :link: ashpb
        :link-type: doc

        ASHPB core + STC preheat, STC stratified tank, PV + ESS
        composed variants. The default first stop.

    .. grid-item-card:: Ground-source heat pump boiler
        :link: gshpb
        :link-type: doc

        GSHPB core with g-function borehole, plus the same three
        composed variants as ASHPB.

    .. grid-item-card:: Water-source heat pump boiler
        :link: wshpb
        :link-type: doc

        WSHPB with a prescribed water-loop inlet temperature.

    .. grid-item-card:: Air-source heat pump (space conditioning)
        :link: ashp
        :link-type: doc

        ASHP for building heating / cooling load instead of DHW.

    .. grid-item-card:: Ground-source heat pump (space conditioning)
        :link: gshp
        :link-type: doc

        GSHP for building heating / cooling load instead of DHW.

.. toctree::
    :maxdepth: 1
    :hidden:

    ashpb
    gshpb
    wshpb
    ashp
    gshp
