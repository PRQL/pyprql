# -*- coding: utf-8 -*-
"""Prompt_toolkit completion engine for PyPRQL CLI."""
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from enforce_typing import enforce_types
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document


def log_to_file(s):
    with open('output.txt', 'a') as f:
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
        # We're only interested in everything after the dot
        if '.' in word_before_cursor and not word_before_cursor.endswith('.'):
            word_before_cursor = word_before_cursor.split('.')[-1]

        # Same with the colon
        if ':' in word_before_cursor and not word_before_cursor.endswith(':'):
            word_before_cursor = word_before_cursor.split(':')[-1]

        log_to_file(word_before_cursor)

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
        builtin_matches = {
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
        elif word_before_cursor in builtin_matches:
            selection = builtin_matches[word_before_cursor]
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
                    yield Completion(str(m), start_position=0)
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
