# -*- coding: utf-8 -*-
"""Sphinx configuration."""
import os
import sys

import sphinx_rtd_theme  # noqa: F401

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../pyprql/"))

project = "PyPRQL"
author = "Charlie Sando"
copyright = "2022, Charlie Sando"
version = "0.4.1"
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "myst_parser",
]

napoleon_google_docstrings = False
napoleon_numpy_docstrings = True
napoleon_use_param = False

html_theme = "sphinx_rtd_theme"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_heading_anchors = 2
