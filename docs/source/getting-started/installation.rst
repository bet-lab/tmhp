============
Installation
============

Requirements
============

- Python **3.10 – 3.13**
- `uv <https://docs.astral.sh/uv/>`_ package manager

Clone and install
=================

.. code-block:: bash

   git clone https://github.com/bet-lab/physics-heatpump-models.git
   cd physics-heatpump-models
   uv sync --locked

``--locked`` makes ``uv`` honor the committed ``uv.lock`` and fail rather
than silently re-resolving versions, which is the same contract CI uses.

Optional dependency groups
==========================

Development and documentation tooling are exposed as `PEP 735
<https://peps.python.org/pep-0735/>`_ dependency groups so they don't
pollute the runtime install.

.. code-block:: bash

   # Runtime only — what most users want
   uv sync --locked

   # + ruff, mypy, pytest, pytest-cov
   uv sync --group dev --locked

   # + sphinx, shibuya theme, MyST, sphinx-design, etc.
   uv sync --group docs --locked

   # Everything at once (mirrors the docs CI job)
   uv sync --all-groups --locked

Runtime dependencies
====================

The runtime install pulls in:

- **CoolProp** — refrigerant thermodynamic properties (REFPROP-grade EOS).
- **NumPy / SciPy** — numerical computation and ``fsolve`` for cycle closure.
- **Pandas** — per-timestep result frames.
- **Matplotlib** — visualization backend.
- **pvlib** — solar irradiance and PV power for STC / PV subsystems.
- **pygfunction** — g-function borehole heat exchanger model.

Building the docs locally
=========================

After ``uv sync --group docs --locked``:

.. code-block:: bash

   cd docs
   uv run make html

The rendered HTML lands in ``docs/build/html``. CI builds the same target
with ``sphinx-build -W --keep-going``, so any new warning fails the
documentation job.
