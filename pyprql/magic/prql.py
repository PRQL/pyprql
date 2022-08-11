# -*- coding: utf-8 -*-
"""A magic class for parsing PRQL in IPython or Jupyter."""
from typing import Dict

from IPython import InteractiveShell
from IPython.core.magic import cell_magic, line_magic, magics_class, needs_local_scope
from prql_python import to_sql
from sql.magic import SqlMagic
from traitlets import Bool


@magics_class
class PRQLMagic(SqlMagic):
    """Perform PRQL magics.

    This is a thin wrapper around ``sql.SqlMagic``,
    the class that provides the ``%%sql`` magic.
    For full documentation on usage and features,
    please see their `docs <https://github.com/catherinedevlin/ipython-sql>`_.

    We override their defaults in two cases:

    1. autopandas is set to ``True``.
    1. displaycon is set to ``False``.

    Additionally,
    to work around some quirky behaviour,
    we also provide an ``autoview`` option to indicate
    whether results should be printed to the window.

    Parameters
    ----------
    shell : InteractiveShell
        The current IPython shell instance.
        Since instantiation is handled by IPython,
        the user should never need to create this clas manually.
    """

    displaycon = Bool(False, config=True, help="Show connection string after execute")
    autopandas = Bool(
        True,
        config=True,
        help="Return Pandas DataFrames instead of regular result sets",
    )
    autoview = Bool(True, config=True, help="Display results")

    def __init__(self, shell: InteractiveShell) -> None:
        super().__init__(shell)

    @needs_local_scope
    @line_magic
    @cell_magic
    def prql(self, line: str = "", cell: str = "", local_ns: Dict = {}) -> None:
        """Create the PRQL magic.

        To handle parsing to PRQL,
        there is one limitation relative to the `original <https://github.com/catherinedevlin/ipython-sql>`_
        ``%%sql`` magic. Namely,
        line magics can only be used to pass connection strings and arguments.
        To figure out whether the ``line`` argument contained PRQL or not
        required heavy parsing followed by recosntruction of the input to pass
        on to the ``%sql`` magic we are wrapping.

        Parameters
        ----------
        line : str
            The magic's line contents.
        cell : str
            The magic's cell contents.
        local_ns : Dict
            The variables local to the running IPython shell.
        """
        # If cell is occupied, it must be parsed to SQL
        if cell:
            cell = to_sql(cell)

        # If cell is occupied and line is empty,
        # we artificially populate line to ensure a return value.
        if cell and not line:
            line = "_ <<"

        super().execute(line=line, cell=cell, local_ns=local_ns)

        # If results should be printed,
        # check line for the results name.
        # Default to `_`.
        if self.autoview:
            if "<<" in line:
                print(local_ns[line.split()[0]])
            else:
                print(local_ns["_"])
