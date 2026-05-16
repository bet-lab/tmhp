========
Concepts
========

Background reading for ``physics_hp``. These pages cover *why* the
library is built the way it is — what physics-based cycle solving buys
you, how the model pieces fit together, and how to interpret the
diagnostic fields that come back from a steady-state call.

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: Why physics-based?
        :link: why-physics-based
        :link-type: doc

        Trade-offs versus empirical curve-fit models — what you give
        up, what you gain, and where the compute goes.

    .. grid-item-card:: Cycle architecture
        :link: cycle-architecture
        :link-type: doc

        How source side, refrigerant cycle, and sink side connect,
        and how the same core cycle is reused across every system
        model.

    .. grid-item-card:: ``failure_reason`` semantics
        :link: failure-reason-semantics
        :link-type: doc

        The four diagnostic values returned by ``analyze_steady``
        and how to branch on them.

    .. grid-item-card:: Refrigerants and CoolProp
        :link: refrigerant-and-coolprop
        :link-type: doc

        Subcritical vs supercritical operation, why CoolProp is the
        backing dependency, and how to swap refrigerants safely.

.. toctree::
    :maxdepth: 1
    :hidden:

    why-physics-based
    cycle-architecture
    failure-reason-semantics
    refrigerant-and-coolprop
