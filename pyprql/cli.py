import os
import sys
from typing import Dict, List

import prql
import pygments
import rich
from enforce_typing import enforce_types
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_dict
from PRQLLexer import PRQLLexer
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

bindings = KeyBindings()
this_files_path = os.path.abspath(os.path.dirname(__file__))


@bindings.add("c-l")
def clear_screen(event):
    print(chr(27) + "[2j")
    print("\033c")
    print("\x1bc")


# Shortlist material ,pastie, trac, native, paraiso-dark, dracula

# PRQLStyle = style_from_pygments_cls(get_style_by_name('prql'))
class PRQLStyle(Style):
    """
    Pygments version of the "native" vim theme.
    """

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
    @enforce_types
    def __init__(
        self,
        table_names: List[str],
        column_names: List[str],
        column_map: Dict,
        prql_keywords: List[str],
    ):
        self.table_names = table_names
        self.column_names = column_names
        self.column_map = column_map
        self.prql_keywords = prql_keywords

        self.prev_word = None
        self.previous_selection = None

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        completion_operators = ["[", "+", ",", ":"]
        possible_matches = {
            "from": self.table_names,
            "join": self.table_names,
            "columns": self.table_names,
            "select": self.column_names,
            " ": self.column_names,
            "sort": self.column_names,
            "filter": self.column_names,
            "show": ["tables", "columns", "connection"],
            "exit": None,
        }
        for op in completion_operators:
            possible_matches[op] = self.column_names

        # This delays the completions until they hit space, or a completion operator
        if word_before_cursor in possible_matches:
            selection = possible_matches[word_before_cursor]
            selection = [f"{x}" for x in selection]
            self.previous_selection = selection
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
    def __init__(self, connect_str: str = "chinook"):
        self.has_one_blank = False
        self.prompt_text = "PRQL> "
        self.command = ""
        self.sql_mode = False
        self.connect_str = connect_str
        if connect_str == "chinook":
            connect_str = f"sqlite:///{this_files_path}/../resources/chinook.db"
        elif connect_str == "factbook":
            connect_str = f"sqlite:///{this_files_path}/../resources/factbook.db"

        rich.print(
            "Connecting to [pale_turquoise1]{}[/pale_turquoise1]".format(connect_str)
        )
        self.engine = create_engine(connect_str)
        self.inspector = inspect(self.engine)

    def get_all_columns(self):
        tables = self.inspector.get_table_names()
        columns = {}
        for table in tables:
            columns[table] = self.inspector.get_columns(table)
            columns[table] = [x["name"] for x in columns[table]]
            columns[table].sort()

        column_names = []
        for col in columns.keys():
            for column in columns[col]:
                column_names.append(column)
        column_names = list(set(column_names))
        column_names.sort()
        return column_names, columns

    def execute_sql(self, sql):
        with self.engine.connect() as con:
            rs = con.execute(sql)
            columns = rs.keys()
            table = Table(show_header=True, header_style="bold sandy_brown")
            for column in columns:
                table.add_column(column, justify="left")

            for _row in rs:
                row = list(_row)
                table.add_row(*[str(x) for x in row])

            rich.print(table)

    def highlight_prql(self, text):

        highlighted = pygments.highlight(text, PRQLLexer(), Formatter())
        return highlighted

    def highlight_sql(self, text):
        highlighted = pygments.highlight(text, SqlLexer(), Formatter())
        return highlighted

    @enforce_types
    def handle_input(self, _user_input: str) -> None:

        user_input: str = _user_input.strip().rstrip(";")
        if user_input == "prql":
            self.sql_mode = False
            self.prompt_text = "PRQL> "
            return
        elif user_input == "examples":
            rich.print(
                """
            [pale_turquoise1]SQL  : SELECT * from employees[/pale_turquoise1]
            [sandy_brown]PRQL : from employees[/sandy_brown]
            
            [pale_turquoise1]SQL  : SELECT name, salary from employees WHERE salary > 100000[/pale_turquoise1]
            [sandy_brown]PRQL : from employees | select \[name,salary] | filter salary > 100000[/sandy_brown]
                          
            """
            )
            return
        elif user_input == "?" or user_input == "help":

            if self.sql_mode:
                rich.print(
                    "\tCommand [cornflower_blue bold]show tables[/cornflower_blue bold]: To show all tables in the database.\n"
                    + "\tCommand [cornflower_blue bold]show columns ${table}[/cornflower_blue bold]: To show all columns in a table.\n"
                )

            else:
                rich.print(
                    "\tCommand [cornflower_blue bold]show tables[/cornflower_blue bold]: To show all tables in the database.\n"
                    + "\tCommand [cornflower_blue bold]show columns ${table}[/cornflower_blue bold]: To show all columns in a table.\n"
                )

                rich.print(
                    "\tCommand [cornflower_blue bold]sql[/cornflower_blue bold]: Switch to SQL mode"
                )
                rich.print(
                    "\tCommand [cornflower_blue bold]prql[/cornflower_blue bold]: Switch to PRQL mode"
                )
                rich.print(
                    "\tCommand [cornflower_blue bold]<enter>[/cornflower_blue bold]: Hit enter twice to execute your query"
                )
                rich.print(
                    "\n\tCommand [cornflower_blue bold]examples[/cornflower_blue bold]: Displays sql-to-prql examples for reference"
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
        elif user_input == "show tables":
            # tables = self.engine.list_tables()
            tables = self.inspector.get_table_names()
            table = Table(show_header=True, header_style="bold sandy_brown")
            table.add_column("Table Name", justify="left")
            for table_name in tables:
                table.add_row(table_name)
            rich.print(table)
            return
        elif user_input.startswith("show columns"):
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
                if "LIMIT" not in sql:
                    sql += " LIMIT 5"

                print("\t" + self.highlight_sql(sql))
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

                    rich.print("[pale_green3 bold]SQL:[/pale_green3 bold]")
                    print("\t" + self.highlight_sql(sql))
                    rich.print(
                        "[medium_turquoise bold]Results:[/medium_turquoise bold]"
                    )
                    self.execute_sql(sql)
                    self.command = ""
                self.prompt_text = "PRQL> "

            else:
                self.prompt_text = "....>"

    def run(self):
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


def print_usage():
    print(
        """
    Usage:
        python cli.py connection_string"""
    )

    print(
        """
    Examples:
        python cli.py 'sqlite:///file.db'
        python cli.py 'postgresql://user:password@localhost:5432/database'
        python cli.py 'postgresql+psycopg2://user:password@localhost:5432/database'
        python cli.py 'mysql://scott:tiger@localhost/foo'
        """
    )

    print(
        """
    Test Database:
        python cli.py chinook
        python cli.py factbook
        
    """
    )

    print(
        """
    Notes:
        The connection string syntax is detailed here https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
        To install database drivers, see https://docs.sqlalchemy.org/en/13/dialects/index.html
        
        Mysql      : pip install mysqlclient
        Postgresql : pip install psycopg2-binary
        MariaDB    : pip install mariadb
        Oracle     : pip install cx_oracle
        SQLite     : <built-in>
    """
    )


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            cli = CLI(sys.argv[1])
            cli.run()
        else:
            print_usage()
            sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
