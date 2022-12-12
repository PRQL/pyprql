"""A magic class for parsing PRQL in IPython or Jupyter."""
from typing import Dict

from IPython.core.magic import cell_magic, line_magic, magics_class, needs_local_scope
from IPython.core.magic_arguments import argument, magic_arguments
from prql_python import to_sql
from sql.magic import SqlMagic
from traitlets import Bool


@magics_class
class PRQLMagic(SqlMagic):
    """Perform PRQL magics.

    This is a thin wrapper around ``sql.SqlMagic``, the class that provides the
    ``%%sql`` magic. For full documentation on usage and features, please see their
    `docs <https://github.com/catherinedevlin/ipython-sql>`_.

    We override their defaults in two cases:

    1. autopandas is set to ``True``.
    1. displaycon is set to ``False``.

    Additionally, to work around some quirky behaviour, we also provide an ``autoview``
    option to indicate whether results should be printed to the window.

    Parameters
    ----------
    shell : InteractiveShell
        The current IPython shell instance. Since instantiation is handled by IPython,
        the user should never need to create this clas manually.
    """

    displaycon = Bool(False, config=True, help="Show connection string after execute")
    autopandas = Bool(
        True,
        config=True,
        help="Return Pandas DataFrames instead of regular result sets",
    )
    autoview = Bool(True, config=True, help="Display results")
    feedback = Bool(False, config=True, help="Print number of rows affected by DML")

    @needs_local_scope
    @line_magic("prql")
    @cell_magic("prql")
    @magic_arguments()
    @argument("line", default="", nargs="*", type=str, help="prql")
    @argument(
        "-l", "--connections", action="store_true", help="list active connections"
    )
    @argument("-x", "--close", type=str, help="close a session by name")
    @argument(
        "-c", "--creator", type=str, help="specify creator function for new connection"
    )
    @argument(
        "-s",
        "--section",
        type=str,
        help="section of dsn_file to be used for generating a connection string",
    )
    @argument(
        "-p",
        "--persist",
        action="store_true",
        help="create a table name in the database from the named DataFrame",
    )
    @argument(
        "--append",
        action="store_true",
        help="create, or append to, a table name in the database from the named DataFrame",
    )
    @argument(
        "-a",
        "--connection_arguments",
        type=str,
        help="specify dictionary of connection arguments to pass to SQL driver",
    )
    @argument("-f", "--file", type=str, help="Run SQL from file at this path")
    def prql(
        self, line: str = "", cell: str = "", local_ns: Dict | None = None
    ) -> None:
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

        Returns
        -------
        None
        """
        local_ns = local_ns or {}
        # If cell is occupied, it must be parsed to SQL
        if cell:
            cell = to_sql(cell)

        # TODO: evaluate whether this is required — it was here previously, but do we
        # need to do more than just super up to ipython-sql?
        # If cell is occupied and line is empty,
        # we artificially populate line to ensure a return value.
        # if cell and not line:
        #     line = "_ <<"

        result = super().execute(line=line, cell=cell, local_ns=local_ns)
        return result

        # TODO: evaluate whether this is required — it was here previously, but do we
        # need to do more than just super up to ipython-sql?
        # If results should be printed,
        # check line for the results name.
        # Default to `_`.
        # if self.autoview:
        #     if "<<" in line:
        #         print(local_ns[line.split()[0]])
        #     else:
        #         print(local_ns["_"])
        #         print(local_ns["_"])
