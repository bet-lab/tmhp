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
html_baseurl = "https://bet-lab.github.io/physics-heatpump-models/"

html_theme_options = {
    "github_url": "https://github.com/bet-lab/physics-heatpump-models",
    "nav_links": [
        {"title": "Getting Started", "url": "getting-started/index"},
        {"title": "API Reference", "url": "api/index"},
    ],
}

# -- Autodoc ------------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

autodoc_mock_imports = ["dartwork_mpl", "dartwork-mpl", "pvlib", "pygfunction"]

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
