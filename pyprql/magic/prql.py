# -*- coding: utf-8 -*-
"""A magic class for parsing PRQL in IPython or Jupyter."""
from typing import Any, Dict

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
    please see their docs_.

    .. _docs: https://github.com/catherinedevlin/ipython-sql

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

    def __init__(self, shell: InteractiveShell):
        super().__init__(shell)

    @needs_local_scope
    @line_magic
    @cell_magic
    def prql(self, line: str = "", cell: str = "", local_ns: Dict = {}) -> Any:
        """Create the PRQL magic.

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
        # Assume line will only take arguments
        # So cell will always need to be parsed
        if cell != "":
            cell = to_sql(cell)
        super().execute(line=line, cell=cell, local_ns=local_ns)
