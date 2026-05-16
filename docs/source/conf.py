# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the src directory to sys.path so autodoc can find the physics_hp package.
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, src_path)

# -- Project information -------------------------------------------------------

project = "Physics-Based Heat Pump Models"
copyright = "2025, betlab"
author = "Habin Jo, Wonjun Choi"
release = "0.1.0"

# -- General configuration -----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
    "myst_parser",
    "sphinx.ext.githubpages",
]

autosummary_generate = True
autosummary_generate_overwrite = False

templates_path = ["_templates"]
exclude_patterns = ["_build", "build", "Thumbs.db", ".DS_Store"]

suppress_warnings = ["myst.xref_missing"]

# -- MyST-parser extensions ---------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# -- HTML output ---------------------------------------------------------------

html_theme = "shibuya"
html_title = "Physics-Based Heat Pump Models"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
html_baseurl = "https://bet-lab.github.io/physics-heatpump-models/"

# Hide the per-page "Show Source" link — the GitHub icon already gives readers
# a path to the repo, and the in-tree .rst files aren't a useful artifact.
html_show_sourcelink = False
html_copy_source = False

html_theme_options = {
    # Cool blue accent fits a thermodynamics / refrigerant-cycle library and
    # keeps headings, links, and the active-nav indicator on one consistent hue.
    "accent_color": "iris",
    "github_url": "https://github.com/bet-lab/physics-heatpump-models",
    # Expand top-level toctree captions in the sidebar by default so the four
    # planned sections (Getting Started, Concepts, Tutorials, API, Validation)
    # are visible without the reader hunting for them.
    "globaltoc_expand_depth": 1,
    "nav_links": [
        {"title": "Getting Started", "url": "getting-started/index"},
        {"title": "Concepts", "url": "concepts/index"},
        {"title": "API Reference", "url": "api/index"},
    ],
    # Social-card image shown when the docs are linked on GitHub, Slack, etc.
    "og_image_url": (
        "https://bet-lab.github.io/physics-heatpump-models/"
        "_static/system_schematic.png"
    ),
}

# -- Autodoc ------------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

autodoc_mock_imports = ["dartwork_mpl"]

# -- Napoleon -----------------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_param = True
napoleon_use_rtype = True

# -- Type hints ---------------------------------------------------------------

typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True
