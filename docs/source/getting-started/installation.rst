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

- `CoolProp <http://www.coolprop.org>`_ — refrigerant thermodynamic
  properties (REFPROP-grade EOS).
- `NumPy <https://numpy.org>`_ + `SciPy <https://scipy.org>`_ —
  numerical computation and ``fsolve`` for cycle closure.
- `pandas <https://pandas.pydata.org>`_ — per-timestep result frames.
- `Matplotlib <https://matplotlib.org>`_ — plotting primitives.
- `pvlib <https://pvlib-python.readthedocs.io>`_ — solar irradiance
  and PV power for the STC / PV subsystems.
- `pygfunction <https://github.com/MassimoCimmino/pygfunction>`_ —
  g-function borehole heat exchanger model.
- `tqdm <https://tqdm.github.io>`_ — progress bars on long
  ``analyze_dynamic`` runs.
- `dartwork-mpl <https://github.com/dartworklabs/dartwork-mpl>`_ —
  thin matplotlib styling layer used by
  :doc:`../api/support/visualization`. Pulled from the upstream Git
  repo via ``[tool.uv.sources]`` since there is no PyPI release; you
  do not need to install it separately.

Development dependencies (``--group dev``)
==========================================

Run the same checks CI runs on every PR:

- `ruff <https://docs.astral.sh/ruff>`_ — lint
  (``uv run ruff check src/physics_hp tests``).
- `mypy <https://mypy.readthedocs.io>`_ — static type checking
  (``uv run mypy src/physics_hp``).
- `pytest <https://docs.pytest.org>`_ +
  `pytest-cov <https://pytest-cov.readthedocs.io>`_ — unit tests and
  coverage (``uv run pytest --cov=physics_hp``).

Documentation dependencies (``--group docs``)
=============================================

The Sphinx build pulls in:

- `Sphinx <https://www.sphinx-doc.org>`_ +
  `Shibuya theme <https://shibuya.lepture.com>`_ — base toolchain.
- `sphinx-autodoc-typehints
  <https://github.com/tox-dev/sphinx-autodoc-typehints>`_,
  `sphinx-design <https://sphinx-design.readthedocs.io>`_,
  `sphinx-copybutton <https://sphinx-copybutton.readthedocs.io>`_,
  `MyST-Parser <https://myst-parser.readthedocs.io>`_,
  `sphinx-click <https://sphinx-click.readthedocs.io>`_,
  `linkify-it-py <https://github.com/tsutsu3/linkify-it-py>`_ —
  authoring helpers (typehints, grids/cards/tabs, copy button,
  Markdown, CLI docs, link autodetection).
- `sphinxcontrib-mermaid
  <https://github.com/mgaitan/sphinxcontrib-mermaid>`_,
  `sphinx-togglebutton <https://sphinx-togglebutton.readthedocs.io>`_,
  `sphinxext-opengraph <https://github.com/sphinx-doc/sphinxext-opengraph>`_,
  `sphinx-notfound-page <https://sphinx-notfound-page.readthedocs.io>`_,
  `sphinx-sitemap <https://sphinx-sitemap.readthedocs.io>`_,
  `sphinx-last-updated-by-git
  <https://github.com/mgeier/sphinx-last-updated-by-git>`_ —
  UX/UI layer (Mermaid diagrams, collapsibles, social cards, 404,
  sitemap, per-page Last-updated footer).

Building the docs locally
=========================

After ``uv sync --group docs --locked``:

.. code-block:: bash

   cd docs
   uv run make html

The rendered HTML lands in ``docs/build/html``. CI builds the same target
with ``sphinx-build -W --keep-going``, so any new warning fails the
documentation job.
