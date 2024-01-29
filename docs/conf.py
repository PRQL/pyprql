"""Sphinx configuration."""

import os
import sys

import sphinx_rtd_theme  # noqa: F401

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../pyprql/"))

project = "pyprql"
author = "PRQL Crew"
copyright = "2022"
version = "0.4.1"
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "myst_parser",
]
exclude_patterns = ["archive/**"]

napoleon_google_docstrings = False
napoleon_numpy_docstrings = True
napoleon_use_param = False

html_theme = "sphinx_rtd_theme"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_heading_anchors = 2
myst_enable_extensions = [
    "html_admonition",
    "colon_fence",
]
