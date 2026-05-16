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

``--locked`` tells ``uv`` to respect the committed ``uv.lock`` and
fail rather than silently re-resolving versions. This is the same
contract CI uses, so your local install matches what we test.

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

What's installed
================

The runtime install pulls in `CoolProp <http://www.coolprop.org>`_
for refrigerant thermodynamics, NumPy / SciPy for numerical work,
pandas for per-timestep result frames, and Matplotlib for plotting,
plus a few smaller libraries for the PV and ground-loop subsystems.
The full, version-pinned list lives in ``pyproject.toml`` and
``uv.lock``.

Running the dev checks
======================

After ``uv sync --group dev --locked``, the three commands CI runs
on every PR are:

.. code-block:: bash

   uv run ruff check src/physics_hp tests
   uv run mypy src/physics_hp
   uv run pytest --cov=physics_hp

Building the docs locally
=========================

After ``uv sync --group docs --locked``:

.. code-block:: bash

   cd docs
   uv run make html

The rendered HTML lands in ``docs/build/html``. CI builds the same
target with ``sphinx-build -W --keep-going``, so any new warning
fails the documentation job.
