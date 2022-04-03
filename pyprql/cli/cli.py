# -*- coding: utf-8 -*-
"""The python command line interface of PRQL.

Attributes
----------
bindings : KeyBindings
    A container for key bindings.
this_files_path : str
    The Path to this file.
BOTTOM_TOOLBAR_TXT : str
    The text for the help bar of the CLI.
"""
import os
import sys
from typing import Dict, List, Optional, Tuple

import pygments
import rich
from enforce_typing import enforce_types
from prompt_toolkit import prompt
from prompt_toolkit.application import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_dict
from pygments.formatters.terminal import TerminalFormatter as Formatter
from pygments.lexers.sql import SqlLexer
from rich.table import Table
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import ResourceClosedError

import pyprql.lang.prql as prql
from pyprql import __version__ as pyprql_version
from pyprql.cli.PRQLCompleter import PRQLCompleter
from pyprql.cli.PRQLLexer import PRQLLexer
from pyprql.cli.PRQLStyle import PRQLStyle

bindings = KeyBindings()
this_files_path = os.path.abspath(os.path.dirname(__file__))
BOTTOM_TOOLBAR_TXT = prql.read_file("../assets/cli_bottom_toolbar.txt", this_files_path)


@bindings.add("c-l")
def clear_screen() -> None:
    """Create clear screen keybinding."""
    print(chr(27) + "[2j")
    print("\033c")
    print("\x1bc")


class CLI:
    """The command line interface object."""

    def __init__(self, connect_str: Optional[str] = "") -> None:
        """Instantiate a CLI object.

        Parameters
        ----------
        connect_str : str, default "chinook"
            The SQL alchemy connection string.

        Notes
        -----
            This additionally defines a number of default parameter values,
            generally used to control state of the connection and prompt.

            has_one_blank : bool, default False
            prompt_test : str, default "PRQL>"
            command : str, default ""
            sql_mode : bool, default False
        """
        self.has_one_blank = False
        self.prompt_text = "PRQL> "
        self.command = ""
        self.sql_mode = False
        self.connect_str = connect_str

        rich.print(
            "Connecting to [pale_turquoise1]{}[/pale_turquoise1]".format(connect_str)
        )
        self.engine = create_engine(connect_str)
        self.inspector = inspect(self.engine)

    @staticmethod
    def print_usage() -> None:
        """Prints the usage information for the CLI."""
        print(prql.read_file("../assets/cli_usage.txt", this_files_path))

    def bottom_toolbar(self) -> List[Tuple[str, str]]:
        """Create bottom toolbar for prql prompt.

        Returns
        -------
        List[Tuple[str, str]]
            An identifier and the desired display text wrapped in a list.
        """
        display_text = BOTTOM_TOOLBAR_TXT
        try:
            text = get_app().current_buffer.text
            display_text = prql.to_sql(text)
        except Exception:
            pass
        return [("class:bottom-toolbar", display_text)]

    def get_all_columns(self) -> Tuple[List[str], Dict[str, List[str]]]:
        """Retrive all columns in the database.

        Iterates over all tables to construct a dictionary of table:columns
        pairs, before condensing this into a single list of all columns to return.

        Returns
        -------
        Tuple[List[str], Dict[str, List[str]]
            A list of all column names in the database,
            and a dictionary mapping each table to its columns.
        """
        tables = self.inspector.get_table_names()
        columns = {}
        for table in tables:
            columns[table] = self.inspector.get_columns(table)
            columns[table] = [x["name"] for x in columns[table]]
            columns[table].sort()

        # This could be sum(columns.values(), [])
        column_names = []
        for col in columns.keys():
            for column in columns[col]:
                column_names.append(column)
        column_names = list(set(column_names))
        column_names.sort()
        return column_names, columns

    def execute_sql(self, sql: str) -> None:
        """Perform an SQL query.

        No value is returned, as ``rich.print`` is used to dumpt the results
        to the CLI.

        Parameters
        ----------
        sql : str
            The SQL query to be performed.
        """
        with self.engine.connect() as con:
            rs = con.execute(sql)
            columns = rs.keys()
            table = Table(show_header=True, header_style="bold sandy_brown")
            for column in columns:
                table.add_column(column, justify="left")

            try:
                for _row in rs:
                    row = list(_row)
                    table.add_row(*[str(x) for x in row])
            except ResourceClosedError:
                rich.print("")
            else:
                rich.print(table)

    def highlight_prql(self, text: str) -> str:
        """Provide highlighting for PRQL inputs.

        Uses a custom-defined PRQLLexer to highlight the prompt inputs.

        Parameters
        ----------
        text : str
            The inputs to be highlighted

        Returns
        -------
        str
            The highlighted inputs.
        """
        highlighted = pygments.highlight(text, PRQLLexer(), Formatter())
        return highlighted

    def highlight_sql(self, text: str) -> str:
        """Provide highlighting for SQL inputs.

        Uses a default Pygments SqlLexer to highlight the prompt inputs.

        Parameters
        ----------
        text : str
            The inputs to be highlighted

        Returns
        -------
        str
            The highlighted inputs.
        """
        highlighted = pygments.highlight(text, SqlLexer(), Formatter())
        return highlighted

    @enforce_types
    def handle_input(self, _user_input: str) -> None:
        """Process user input.

        Currently, uses if/elif/else logic to check possible inputs against
        actions to be taken for those inputs.

        Parameters
        ----------
        _user_input : str
            The input given by the user at the CLI.
        """
        user_input: str = _user_input.strip().rstrip(";")
        if user_input == "prql":
            self.sql_mode = False
            self.prompt_text = "PRQL> "
            return
        elif user_input == "exit":
            sys.exit(0)
        elif user_input == "examples":
            # That would likely increase maintainability
            rich.print(prql.read_file("../assets/examples.txt", this_files_path))
            return
        elif user_input == "?" or user_input == "help":
            rich.print("PyPRQL version: {}".format(pyprql_version))

            if self.sql_mode:
                rich.print(
                    prql.read_file("../assets/sql_mode_help.txt", this_files_path)
                )

            else:
                rich.print(
                    prql.read_file("../assets/prql_mode_help.txt", this_files_path)
                )
                self.prompt_text = "PRQL> "

            rich.print(
                "\nPRQL Syntax documentation is here https://github.com/max-sixty/prql\n"
            )

            return
        elif user_input == "sql":
            self.sql_mode = True
            self.prompt_text = "SQL> "
            return
        elif user_input == "show tables" or user_input == "\dt" or user_input == "ls":
            # tables = self.engine.list_tables()
            tables = self.inspector.get_table_names()
            table = Table(show_header=True, header_style="bold sandy_brown")
            table.add_column("Table Name", justify="left")
            for table_name in tables:
                table.add_row(table_name)
            rich.print(table)
            return
        elif user_input.startswith("show columns") or user_input.startswith("\d+"):
            key = "show columns"
            if key not in user_input:
                key = "\d+"
            table_name = user_input[key.__len__() + 1 :]
            print(table_name)
            # tables = self.engine.list_tables()
            columns = self.inspector.get_columns(table_name)
            rich.print(columns)
            return

        self.command += user_input + " "
        if self.sql_mode:
            if not user_input:

                self.has_one_blank = False
                sql = self.command
                if "SELECT" in sql and "LIMIT" not in sql:
                    sql += " LIMIT 25"

                self.prompt_text = "SQL> "
                self.execute_sql(sql)

            else:
                self.prompt_text = "....>"
        else:
            if not user_input:
                self.has_one_blank = False
                if self.command and self.command.strip().rstrip("") != "":
                    sql = prql.to_sql(self.command)
                    if "LIMIT" not in sql:
                        sql += " LIMIT 5"

                    print("SQL:\n\t" + self.highlight_sql(sql) + "\nResults:")
                    self.execute_sql(sql)
                    self.command = ""
                self.prompt_text = "PRQL> "

            else:
                self.prompt_text = "....>"

    def run(self) -> None:
        """Run the CLI.

        While there is no error,
        this function uses the prompt_toolkit ``prompt`` to handle
        completions, colouring, etc.
        If an error occurs while hanndling input,
        a message is printed to the terminal,
        but the CLI is *NOT* aborted,
        as this error is likely not critical.
        """
        prql_keywords = [
            "select",
            "from",
            "filter",
            "derive",
            "aggregate",
            "sort",
            "take",
            "order",
        ]
        while True:
            all_columns, columns_map = self.get_all_columns()
            user_input = prompt(
                self.prompt_text,
                history=FileHistory(".prql-history.txt"),
                auto_suggest=AutoSuggestFromHistory(),
                completer=PRQLCompleter(
                    self.inspector.get_table_names(),
                    all_columns,
                    columns_map,
                    prql_keywords,
                ),
                lexer=PygmentsLexer(PRQLLexer),
                style=style_from_pygments_dict(PRQLStyle.styles),
                bottom_toolbar=self.bottom_toolbar,
            )
            try:
                self.handle_input(user_input)
            except Exception as e:
                print(
                    f"Exception when handling the input: {e},{repr(e)}\nContinuing..."
                )
                self.command = ""
                self.prompt_text = "PRQL> "
                self.has_one_blank = False
