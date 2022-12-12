"""IPython/Jupyter magic for pyprql.

Examples
--------
A single function is defined herein. It should not be used directly by the user. Rather,
any users should load the magic using the IPython line magic, like below:

    In [1]: %load_ext pyprql.magic

"""
from IPython import InteractiveShell

from .prql import PRQLMagic


def load_ipython_extension(ipython: InteractiveShell) -> None:
    """Load the ``pyprql.magic`` extension.

    This function is called automatically by ``IPython`` when the magic is loaded using
    ``%load_ext``.

    Parameters
    ----------
    ipython: InteractiveShell
        The current IPython instance.
    """
    ipython.register_magics(PRQLMagic)
