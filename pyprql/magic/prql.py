"""A magic class for parsing PRQL in IPython or Jupyter."""
from __future__ import annotations

from IPython.core.magic import cell_magic, line_magic, magics_class, needs_local_scope
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from prql_python import compile, CompileOptions
from sql.magic import SqlMagic
from sql.parse import parse
from traitlets import Bool, Unicode
import re


@magics_class
class PrqlMagic(SqlMagic):
    """Perform PRQL magics.

    This is a thin wrapper around ``sql.SqlMagic``, the class that provides the
    ``%%sql`` magic. For full documentation on usage and features, please see their
    `docs <https://jupysql.readthedocs.io/en/latest/quick-start.html>`_.

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
    autopolars = Bool(
        False,
        config=True,
        help="Return Polars DataFrames instead of regular result sets",
    )
    autoview = Bool(True, config=True, help="Display results")
    feedback = Bool(False, config=True, help="Print number of rows affected by DML")
    target = Unicode("sql.any", config=True, help="Compile target of prql-compiler")
    dryrun = Bool(False, config=True, help="Only print the compiled SQL")

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
        "-n",
        "--no-index",
        action="store_true",
        help="Do not store Data Frame index when persisting",
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
    @argument("-f", "--file", type=str, help="Run PRQL from file at this path")
    def prql(
        self, line: str = "", cell: str = "", local_ns: dict | None = None
    ) -> None:
        """Create the PRQL magic.

        Returns
        -------
            None
        """
        local_ns = local_ns or {}
        self.args = parse_argstring(self.execute, line)
        line_prql = parse(" ".join(self.args.line), self.execute)["sql"]
        if line_prql and not self.args.persist and not self.args.append:
            cell = line_prql + "\n" + cell
            _escaped_prql = re.escape(line_prql)
            _pattern = re.sub(r"\\\s", r"\\s+", _escaped_prql)
            line = re.sub(_pattern, "", line)
        if self.args.file:
            with open(self.args.file, "r") as infile:
                cell = infile.read()
            line = re.sub(r"(\-f|\-\-file)\s+" + self.args.file, "", line)
        # If cell is occupied, parsed to SQL
        if cell:
            cell = compile(
                cell,
                CompileOptions(target=self.target, format=True, signature_comment=True),
            )
        if self.dryrun:
            print(cell)
            return None
        result = super().execute(line=line, cell=cell, local_ns=local_ns)
        return result
