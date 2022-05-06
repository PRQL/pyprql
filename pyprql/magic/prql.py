# -*- coding: utf-8 -*-
"""A magic class for parsing PRQL in IPython or Jupyter."""
from typing import Any, Dict

from IPython import InteractiveShell
from IPython.core.magic import cell_magic, line_magic, magics_class, needs_local_scope
from prql_python import to_sql
from sql.magic import SqlMagic


@magics_class
class PRQLMagic(SqlMagic):
    """Perform PRQL magics.

    This is a thin wrapper around ``sql.SqlMagic``,
    the class that provides the ``%%sql`` magic.
    For full documentation on usage and features,
    please see their docs_.

    .. _docs: https://github.com/catherinedevlin/ipython-sql

    Parameters
    ----------
    shell : InteractiveShell
        The current IPython shell instance.
        Since instantiation is handled by IPython,
        the user should never need to create this clas manually.
    """

    def __init__(self, shell: InteractiveShell):
        super().__init__(shell)

    @needs_local_scope
    @line_magic
    @cell_magic
    def prql(self, line: str = "", cell: str = "", local_ns: Dict = {}) -> Any:
        """Create the PRQL magic.

        If used as a line magic,
        then the line is assumed to be PRQL and parsed to SQL.
        If used as a cell magic,
        then the line is passed untouched,
        but the cell contents are parsed to SQL.
        Then,
        the parameters are passed to ``sql.SqlMagic.execute``.

        Parameters
        ----------
        line : str
            The magic's line contents.
        cell : str
            The magic's cell contents.
        local_ns : Dict
            The variables local to the running IPython shell.

        Returns
        -------
        Any
            Depending on the arguments passed,
            this could be one of several items,
            such as a ``sqlalchemy`` connection or a ``pandas`` dataframe.
        """
        if line != "":
            # Assume line magic doesn't take arguments
            line = to_sql(line)
        if cell != "":
            # If a cell magic, always convert to prql
            cell = to_sql(cell)
        super().execute(line=line, cell=cell, local_ns=local_ns)
