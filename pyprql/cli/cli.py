# -*- coding: utf-8 -*-
"""The python command line interface of PRQL.

Attributes
----------
bindings : KeyBindings
    A container for key bindings.
this_files_path : str
    The Path to this file.
"""
import os
import sys
from typing import Dict, Iterable, List, Optional, Tuple

import pygments
import rich
from enforce_typing import enforce_types
from prompt_toolkit import prompt
from prompt_toolkit.application import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_dict
from pygments.formatters.terminal import TerminalFormatter as Formatter
from pygments.lexers.sql import SqlLexer
from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Token,
    Whitespace,
)
from rich.table import Table
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import ResourceClosedError

import pyprql.lang.prql as prql
from pyprql import __version__ as pyprql_version
from pyprql.cli.PRQLLexer import PRQLLexer

bindings = KeyBindings()
this_files_path = os.path.abspath(os.path.dirname(__file__))
BOTTOM_TOOLBAR_TXT = prql.read_file("../assets/cli_bottom_toolbar.txt", this_files_path)


def bottom_toolbar() -> List[Tuple[str, str]]:
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


@bindings.add("c-l")
def clear_screen() -> None:
    """Create clear screen keybinding."""
    print(chr(27) + "[2j")
    print("\033c")
    print("\x1bc")


class PRQLStyle(Style):
    """Pygments version of the "native" vim theme.

    Inherits from pygments ``Style``,
    overriding values to create our colour scheme.
    The various style attributes are self-descriptive,
    and thoroughly documented on the `pygments`_ page.

    .. _pygments: https://pygments.org/docs/styledevelopment/
    """

    background_color = "#202020"
    highlight_color = "#404040"
    line_number_color = "#aaaaaa"
    background_color = "#202020"
    highlight_color = "#404040"
    line_number_color = "#aaaaaa"

    styles = {
        Token: "#d0d0d0",
        Whitespace: "#666666",
        Comment: "italic #999999",
        Comment.Preproc: "noitalic bold #cd2828",
        Comment.Special: "noitalic bold #e50808 bg:#520000",
        Keyword: "bold #6ab825",
        Keyword.Pseudo: "nobold",
        Operator.Word: "bold #6ab825",
        String: "#ed9d13",
        String.Other: "#ffa500",
        Number: "#3677a9",
        Name.Builtin: "#24909d",
        Name.Variable: "#40ffff",
        Name.Constant: "#40ffff",
        Name.Class: "underline #447fcf",
        Name.Function: "#447fcf",
        Name.Namespace: "underline #447fcf",
        Name.Exception: "#bbbbbb",
        Name.Tag: "bold #6ab825",
        Name.Attribute: "#bbbbbb",
        Name.Decorator: "#ffa500",
        Generic.Heading: "bold #ffffff",
        Generic.Subheading: "underline #ffffff",
        Generic.Deleted: "#d22323",
        Generic.Inserted: "#589819",
        Generic.Error: "#d22323",
        Generic.Emph: "italic",
        Generic.Strong: "bold",
        Generic.Prompt: "#aaaaaa",
        Generic.Output: "#cccccc",
        Generic.Traceback: "#d22323",
        Error: "bg:#e3d2d2 #a61717",
    }


class PRQLCompleter(Completer):
    """Prompt_toolkit completion engine for PyPRQL CLI."""

    @enforce_types
    def __init__(
        self,
        table_names: List[str],
        column_names: List[str],
        column_map: Dict[str, List[str]],
        prql_keywords: List[str],
    ) -> None:
        """Initialise a completer instance.

        This provides some of the root completion material.
        Inherits from  prompt_toolkit's ``Completer`` class,
        and overrides methods to achieve desired functionality.

        Parameters
        ----------
        table_names : List[str]
            List of available tables.
        column_names : List[str]
            List of available columns.
        column_map : Dict[str, List[str]]
            A column-to-table map.
        prql_keywords : List[str]
            list of PRQL keywords.
        """
        self.table_names = table_names
        self.column_names = column_names
        self.column_map = column_map
        self.prql_keywords = prql_keywords

        self.prev_word: Optional[str] = None
        self.previous_selection: Optional[List[str]] = None

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Retrieve completion options.

        Parameters
        ----------
        document : Document
            Implements all text operations/querying.
        complete_event : CompleteEvent
            Event that called the Completer.
            Unused in current implementation, but required to match signature.

        Yields
        ------
        Completion
            The completion object.
        """
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        completion_operators = ["[", "+", ",", ":"]
        possible_matches = {
            "from": self.table_names,
            "join": self.table_names,
            "columns": self.table_names,
            "select": self.column_names,
            " ": self.column_names,
            "sort": self.column_names,
            "sum": self.column_names,
            "avg": self.column_names,
            "min": self.column_names,
            "max": self.column_names,
            "count": self.column_names,
            "filter": self.column_names,
            "exit": [""],
        }
        matches_that_need_prev_word = {
            "show": ["tables", "columns", "connection"],
            "side:": ["left", "inner", "right", "outer"],
            "order:": ["asc", "desc"],
            "by:": self.column_names,
        }
        # print(word_before_cursor)
        for op in completion_operators:
            possible_matches[op] = self.column_names

        # This delays the completions until they hit space, or a completion operator
        if word_before_cursor in possible_matches:
            selection = possible_matches[word_before_cursor]
            selection = [f"{x}" for x in selection]
            self.previous_selection = selection
            # This can be reworked to a if not in operator. No pass required.
            if (
                word_before_cursor == "from"
                or word_before_cursor == "join"
                or word_before_cursor == "sort"
                or word_before_cursor == "select"
                or word_before_cursor == "columns"
                or word_before_cursor == "show"
                or word_before_cursor == ","
                or word_before_cursor == "["
                or word_before_cursor == "filter"
            ):
                pass
            else:
                for m in selection:
                    yield Completion(m, start_position=-len(word_before_cursor))
        elif word_before_cursor in matches_that_need_prev_word:
            selection = matches_that_need_prev_word[word_before_cursor]
            #            selection = [f"{x}" for x in selection]
            for m in selection:
                yield Completion(m, start_position=0)
        # If its an operator
        elif (
            len(word_before_cursor) >= 1
            and word_before_cursor[-1] in completion_operators
        ):
            selection = possible_matches[word_before_cursor[-1]]
            self.previous_selection = selection
        # If its a period, then we assume the first word was a table
        elif len(word_before_cursor) >= 1 and word_before_cursor[-1] == ".":
            table = word_before_cursor[:-1]
            if table in self.column_map:
                selection = self.column_map[table]
                self.previous_selection = selection
                for m in selection:
                    yield Completion(m, start_position=0)
        # This goes back to the first if, this is the delayed completion finally completing
        elif self.previous_selection:
            selection = [
                x for x in self.previous_selection if x.find(word_before_cursor) != -1
            ]
            self.previous_selection = selection

            for m in selection:
                yield Completion(m, start_position=-len(word_before_cursor))

        # This is supposed to complete keywords, but its tromping all over the other completions
        # else:
        #     completer = FuzzyWordCompleter(self.prql_keywords)
        #     for m in completer.get_completions(document, complete_event):
        #         yield m


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
        elif user_input == "show tables" or user_input == "\dt":
            # tables = self.engine.list_tables()
            tables = self.inspector.get_table_names()
            table = Table(show_header=True, header_style="bold sandy_brown")
            table.add_column("Table Name", justify="left")
            for table_name in tables:
                table.add_row(table_name)
            rich.print(table)
            return
        elif user_input.startswith("show columns") or user_input == "\d+":
            table_name = user_input["show columns ".__len__() :]
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
                bottom_toolbar=bottom_toolbar,
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


def print_usage() -> None:
    """Prints the usage information for the CLI."""
    print(prql.read_file("../assets/cli_usage.txt", this_files_path))


def main(params: Optional[List[str]] = None) -> None:
    """Serve the CLI entrypoint.

    If ``params`` is left as it's default ``None``,
    then ``params`` is set to ``sys.argv``.
    If no parameters are passed,
    then the help message is printed.
    Otherwise,
    a prompt is activated until a keyboard interrupt.

    Parameters
    ----------
    params : Optional[List[str]], default None
        The parameters passed to the CLI.
    """
    if params is None:
        params = sys.argv
    try:
        if len(params) > 1:
            cli = CLI(params[1])
            cli.run()
        else:
            print_usage()
            sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
