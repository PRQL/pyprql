# -*- coding: utf-8 -*-
"""Prompt_toolkit completion engine for PyPRQL CLI."""
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from enforce_typing import enforce_types
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from pyprql.lang import prql


def _debug_log_to_file(s):
    with open('.prql_cli_debug_output.txt', 'a') as f:
        f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        f.write(":" + s)
        f.write('\n')


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

        self.last_good_table_aliases = {}

    def parse_prql(self, text: str) -> Optional[prql.Root]:
        ast = prql.parse(text)
        return ast

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
        _debug_log_to_file(word_before_cursor)

        table_aliases = self.get_table_aliases(str(document.text))
        if table_aliases is not None:
            self.last_good_table_aliases = table_aliases
            _debug_log_to_file('last_good_table_aliases=' + str(table_aliases))

        # We're only interested in everything after the dot
        if '.' in word_before_cursor and not word_before_cursor.endswith('.'):
            word_before_cursor = word_before_cursor.split('.')[-1]

        # Same with the colon
        if ':' in word_before_cursor and not word_before_cursor.endswith(':'):
            word_before_cursor = word_before_cursor.split(':')[-1]

        completion_operators = ["[", "+", ","]
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
        builtin_matches = {
            "show": ["tables", "columns", "connection"],
            "side:": ["left", "inner", "right", "outer"],
            "order:": ["asc", "desc"],
            "by:": self.column_names,
        }
        aliases = {}

        for alias in self.last_good_table_aliases.keys():
            aliases[alias] = self.column_map[self.last_good_table_aliases[alias]]
        # print(word_before_cursor)
        for op in completion_operators:
            possible_matches[op] = self.column_names

        # This delays the completions until they hit space, or a completion operator
        if word_before_cursor in possible_matches:
            _debug_log_to_file('possible_matches')
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
        elif len(word_before_cursor) == 0 or word_before_cursor[-1] == " " or word_before_cursor[-1] == "\t" or \
                word_before_cursor[-1] == "\n":
            # self.previous_selection = []
            _debug_log_to_file('null')
            return None
        elif word_before_cursor in builtin_matches:
            _debug_log_to_file('builtin_matches')

            selection = builtin_matches[word_before_cursor]
            self.previous_selection = selection
            for m in selection:
                yield Completion(m, start_position=0)
        # If its an operator
        elif (
                len(word_before_cursor) >= 1
                and word_before_cursor[-1] in completion_operators
        ):
            _debug_log_to_file('completion_operators')

            selection = possible_matches[word_before_cursor[-1]]
            self.previous_selection = selection
        # If its a period, then we assume the first word was a table
        elif len(word_before_cursor) >= 1 and word_before_cursor[-1] == ".":
            _debug_log_to_file('period')

            table = word_before_cursor[:-1]
            _debug_log_to_file('table=' + table)
            _debug_log_to_file('aliases=' + str(self.last_good_table_aliases.keys()))

            if table in self.last_good_table_aliases.keys():
                table = self.last_good_table_aliases[table]
            if table in self.column_map:
                selection = self.column_map[table]
                self.previous_selection = selection
                for m in selection:
                    yield Completion(str(m), start_position=0)
        elif len(word_before_cursor) >= 1 and word_before_cursor[-1] == ":":
            _debug_log_to_file('colon')

            selection = self.column_map.keys()
            self.previous_selection = selection
            for m in selection:
                yield Completion(str(m), start_position=0)
        # This goes back to the first if, this is the delayed completion finally completing
        elif self.previous_selection:
            _debug_log_to_file('previous_selection')

            # They have selected something, so just clear it out
            selection = [
                x for x in self.previous_selection if x.find(word_before_cursor) != -1
            ]
            self.previous_selection = selection

            for m in selection:
                yield Completion(m, start_position=-len(word_before_cursor))

    @enforce_types
    def get_table_aliases(self, full_text: str) -> Optional[Dict]:
        try:
            ret = {}
            root = self.parse_prql(full_text)
            joins = prql.get_operation(root.get_from().pipes.operations, class_type=prql.Join, return_all=True)
            # print('joins=' +str(joins))
            for join in joins:
                if join.alias is not None:
                    ret[str(join.alias)] = str(join.name)
            return ret
        except Exception as e:
            # print(e)
            return None
