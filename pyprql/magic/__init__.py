# -*- coding: utf-8 -*-
"""PRQL magic wrapping ipython-sql."""
from IPython import get_ipython

from .prql import PRQLMagic

get_ipython().register_magics(PRQLMagic)
