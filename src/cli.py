import os
import sys

import pygments
import rich
from enforce_typing import enforce_types
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.formatters.terminal import TerminalFormatter as Formatter
from pygments.lexers.sql import SqlLexer
from rich.table import Table
from sqlalchemy import create_engine, inspect

import prql
from PRQLLexer import PRQLLexer

script_path = os.path.abspath(os.path.dirname(__file__))


class PRQLCompleter(Completer):

    def __init__(self, table_names, column_names, column_map):
        self.table_names = table_names
        self.column_names = column_names
        self.column_map = column_map

        self.prev_word = None
        self.previous_selection = None

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        selection = []

        possible_matches = {
            'from': self.table_names,
            'join': self.table_names,
            'columns': self.table_names,
            '[': self.column_names,
            '+': self.column_names,
            ' ': self.column_names,

            'sort': self.column_names,
            'show': ['tables', 'columns', 'connection'],
            'exit': None
        }
        # print(word_before_cursor)
        if word_before_cursor in possible_matches:
            selection = possible_matches[word_before_cursor]
            selection = [f'{x}' for x in selection]
            self.previous_selection = selection
            if word_before_cursor == 'from' or word_before_cursor == 'join' or word_before_cursor == 'sort' or \
                    word_before_cursor == 'columns' or word_before_cursor == 'show':
                pass
            else:
                for m in selection:
                    yield Completion(m, start_position=-len(word_before_cursor))

        elif len(word_before_cursor) >= 1 and word_before_cursor[-1] in ['[', '+']:
            selection = possible_matches[word_before_cursor[-1]]
            # selection = [f'{word_before_cursor} {x}' for x in selection]
            self.previous_selection = selection
            # for m in selection:
            #     yield Completion(m, start_position=-len(word_before_cursor))
        elif len(word_before_cursor) >= 1 and word_before_cursor[-1] == '.':
            table = word_before_cursor[:-1]
            if table in self.column_map:
                selection = self.column_map[table]
                self.previous_selection = selection
                for m in selection:
                    yield Completion(m, start_position=0)
        elif self.previous_selection:
            selection = [x for x in self.previous_selection if x.find(word_before_cursor) != -1]
            self.previous_selection = selection

            for m in selection:
                yield Completion(m, start_position=-len(word_before_cursor))


def stringify(row):
    return [str(x) for x in row]


class CLI:

    def __init__(self, connect_str: str = 'sqlite:///../resources/chinook.db'):
        self.has_one_blank = False
        self.prompt_text = 'PRQL> '
        self.command = ''
        self.sql_mode = False
        self.connect_str = connect_str
        if connect_str == 'chinook':
            print(script_path)
            connect_str = f'sqlite:///{script_path}/../resources/chinook.db'
        print('Connecting to {}'.format(connect_str))
        self.engine = create_engine(connect_str)
        self.inspector = inspect(self.engine)

    def get_all_columns(self):
        tables = self.inspector.get_table_names()
        columns = {}
        for table in tables:
            columns[table] = self.inspector.get_columns(table)
            columns[table] = [x['name'] for x in columns[table]]
            columns[table].sort()
        # print('HERE!!')
        # print(columns)
        column_names = []
        for col in columns.keys():
            # print(col)
            for column in columns[col]:
                column_names.append(column)
        column_names = list(set(column_names))
        column_names.sort()
        return column_names, columns

    # def get_completer(self):
    #     table_names = set(self.inspector.get_table_names())
    #
    #     completer = NestedCompleter.from_nested_dict()
    #     return completer

    def execute_sql(self, sql):
        with self.engine.connect() as con:
            rs = con.execute(sql)
            columns = rs.keys()
            table = Table(show_header=True, header_style="bold sandy_brown")
            for column in columns:
                table.add_column(column, justify='left')

            for _row in rs:
                row = list(_row)
                table.add_row(*stringify(row))

            rich.print(table)

    def highlight_prql(self, text):

        highlighted = pygments.highlight(text, PRQLLexer(), Formatter())
        return highlighted

    def highlight_sql(self, text):
        highlighted = pygments.highlight(text, SqlLexer(), Formatter())
        return highlighted

    @enforce_types
    def handle_input(self, _user_input: str) -> None:

        user_input: str = _user_input.strip().rstrip(';')
        if user_input == 'prql':
            self.sql_mode = False
            self.prompt_text = 'PRQL> '
            return
        elif user_input == '?' or user_input == 'help':
            if self.sql_mode:
                rich.print(
                    '\tCommand [cornflower_blue bold]show tables[/cornflower_blue bold]: To show all tables in the database.\n' +
                    '\tCommand [cornflower_blue bold]show columns ${table}[/cornflower_blue bold]: To show all columns in a table.\n')

            else:
                rich.print(
                    '\tCommand [cornflower_blue bold]show tables[/cornflower_blue bold]: To show all tables in the database.\n' +
                    '\tCommand [cornflower_blue bold]show columns ${table}[/cornflower_blue bold]: To show all columns in a table.\n')

                rich.print('\tCommand [cornflower_blue bold]sql[/cornflower_blue bold]: Switch to SQL mode')
                rich.print('\tCommand [cornflower_blue bold]prql[/cornflower_blue bold]: Switch to PRQL mode')
                rich.print(
                    '\tCommand [cornflower_blue bold]<enter>[/cornflower_blue bold]: Hit enter twice to execute your query')
                self.prompt_text = 'PRQL> '
            return
        elif user_input == 'sql':
            self.sql_mode = True
            self.prompt_text = 'SQL> '
            return
        elif user_input == 'show tables':
            # tables = self.engine.list_tables()
            tables = self.inspector.get_table_names()
            table = Table(show_header=True, header_style="bold sandy_brown")
            table.add_column("Table Name", justify='left')
            for table_name in tables:
                table.add_row(table_name)
            rich.print(table)
            return
        elif user_input.startswith('show columns'):
            table_name = user_input['show columns '.__len__():]
            # tables = self.engine.list_tables()
            columns = self.inspector.get_columns(table_name)
            rich.print(columns)
            return

        self.command += user_input + ' '
        if self.sql_mode:
            if not user_input:
                if self.has_one_blank:
                    self.has_one_blank = False
                    sql = self.command
                    if 'LIMIT' not in sql:
                        sql += ' LIMIT 5'

                    print('\t' + self.highlight_sql(sql))
                    self.prompt_text = 'SQL> '
                    self.execute_sql(sql)
                else:
                    self.prompt_text = '<enter to execute>'
                    self.has_one_blank = True
            else:
                self.prompt_text = '....>'
        else:
            if not user_input:
                # if self.has_one_blank:
                self.has_one_blank = False
                if self.command and self.command.strip().rstrip('') != '':
                    # rich.print('[pale_green3 bold]PRQL:[/pale_green3 bold]')
                    # print('\t' + self.highlight_prql(self.command).strip())
                    sql = prql.to_sql(self.command)
                    if 'LIMIT' not in sql:
                        sql += ' LIMIT 5'

                    rich.print('[pale_green3 bold]SQL:[/pale_green3 bold]')
                    print('\t' + self.highlight_sql(sql))
                    rich.print('[medium_turquoise bold]Results:[/medium_turquoise bold]')
                    self.execute_sql(sql)
                    self.command = ''
                self.prompt_text = 'PRQL> '
                # else:
                #     self.prompt_text = '<enter to execute>'
                #     self.has_one_blank = True
            else:
                self.prompt_text = '....>'
        # rich.print(user_input)

    def run(self):
        # PRQLKeywords = ['select', 'from', 'filter', 'derive', 'aggregate', 'sort', 'take', 'order']
        while True:
            all_columns, columns_map = self.get_all_columns()
            user_input = prompt(self.prompt_text,
                                history=FileHistory('.prql-history.txt'),
                                auto_suggest=AutoSuggestFromHistory(),
                                completer=PRQLCompleter(self.inspector.get_table_names(), all_columns, columns_map),
                                lexer=PygmentsLexer(PRQLLexer),
                                )
            try:
                self.handle_input(user_input)
            except Exception as e:
                print(f'Exception when handling the input: {e},{repr(e)}\nContinuing...')
                self.command = ''
                self.prompt_text = 'PRQL> '
                self.has_one_blank = False


def print_usage():
    rich.print('''
    [bold sandy_brown]Usage[/bold sandy_brown]:
        python cli.py connection_string''')

    rich.print('''
    [bold green]Examples[/bold green]:
        python cli.py 'sqlite:///file.db'
        python cli.py 'postgresql://user:password@localhost:5432/database'
        python cli.py 'postgresql+psycopg2://user:password@localhost:5432/database'
        python cli.py 'mysql://scott:tiger@localhost/foo''')

    rich.print('''
    [bold cornflower_blue]Try It[/bold cornflower_blue ]
        python cli.py 'chinook'
    ''')

    print('''Notes:
        The connection string syntax is detailed here https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
    ''')


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            cli = CLI(sys.argv[1])
            cli.run()
        else:
            print_usage()
            sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
