"""Prompt_toolkit completion engine for pyprql CLI."""
from typing import Dict, Iterable, List, Optional

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document


class PRQLCompleter(Completer):
    """Prompt_toolkit completion engine for pyprql CLI.

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

    def __init__(
        self,
        table_names: List[str],
        column_names: List[str],
        column_map: Dict[str, List[str]],
        prql_keywords: List[str],
    ) -> None:
        self.table_names = table_names
        self.column_names = column_names
        self.column_map = column_map
        self.prql_keywords = prql_keywords

        self.prev_word: Optional[str] = None
        self.previous_selection: Optional[List[str]] = None

        self.last_good_table_aliases: Dict[str, str] = {}

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:  # noqa: DAR201
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
        # _debug_log_to_file('wbc:' + word_before_cursor)
        working_column_names = self.column_names
        # _debug_log_to_file('wcn:' + str(working_column_names))
        # If we have a from_table, then set the column names to just that table
        # from_table = self.get_from_table(str(document.text))
        # if from_table is not None:
        #     working_column_names = self.column_map.get(from_table, [])
        #
        # table_aliases = self.get_table_aliases(str(document.text))
        # if table_aliases is not None and table_aliases:
        #     self.last_good_table_aliases = table_aliases
        # _debug_log_to_file('last_good_table_aliases=' + str(table_aliases))

        # We're only interested in everything after the dot
        if "." in word_before_cursor and not word_before_cursor.endswith("."):
            word_before_cursor = word_before_cursor.split(".")[-1]

        # Same with the colon
        if ":" in word_before_cursor and not word_before_cursor.endswith(":"):
            word_before_cursor = word_before_cursor.split(":")[-1]

        completion_operators = ["[", "+", ","]
        possible_matches = {
            "from": self.table_names,
            "join": self.table_names,
            "\\d+": self.table_names,
            "columns": self.table_names,
            "select": working_column_names,
            " ": working_column_names,
            "sort": working_column_names,
            "sum": working_column_names,
            "avg": working_column_names,
            "min": working_column_names,
            "max": working_column_names,
            "count": working_column_names,
            "filter": working_column_names,
            "exit": [""],
        }
        builtin_matches = {
            "show": ["tables", "columns", "connection"],
            "side:": ["left", "inner", "right", "outer"],
            "order:": ["asc", "desc"],
            "by:": working_column_names,
        }
        aliases = {}

        try:
            for alias in self.last_good_table_aliases.keys():
                aliases[alias] = self.column_map[self.last_good_table_aliases[alias]]
        except KeyError:
            pass

        for op in completion_operators:
            possible_matches[op] = working_column_names

        # This delays the completions until they hit space,
        # it feels weird when the completion comes up when you're still at the keyword
        if word_before_cursor in possible_matches:
            # _debug_log_to_file('possible_matches')
            selection = possible_matches[word_before_cursor]
            selection = [f"{x}" for x in selection]
            self.previous_selection = selection
            # This can be reworked to a if not in operator. No pass required.
            if word_before_cursor not in possible_matches.keys():
                for m in selection:
                    yield Completion(m, start_position=-len(word_before_cursor))
        elif (
            len(word_before_cursor) == 0
            or word_before_cursor[-1] == " "
            or word_before_cursor[-1] == "\t"
            or word_before_cursor[-1] == "\n"
        ):
            # _debug_log_to_file('null')
            return None
        elif word_before_cursor in builtin_matches:
            # _debug_log_to_file('builtin_matches')

            selection = builtin_matches[word_before_cursor]
            self.previous_selection = selection
            for m in selection:
                yield Completion(m, start_position=0)
        # If its an operator
        elif (
            len(word_before_cursor) >= 1
            and word_before_cursor[-1] in completion_operators
        ):
            # _debug_log_to_file('completion_operators')

            selection = possible_matches[word_before_cursor[-1]]
            self.previous_selection = selection
        # If its a period, then we assume the first word was a table
        elif len(word_before_cursor) >= 1 and word_before_cursor[-1] == ".":
            # _debug_log_to_file('period')

            table = word_before_cursor[:-1]
            # _debug_log_to_file('table=' + table)
            # _debug_log_to_file('aliases=' + str(self.last_good_table_aliases.keys()))

            if table in self.last_good_table_aliases.keys():
                table = self.last_good_table_aliases[table]
            if table in self.column_map:
                selection = self.column_map[table]
                self.previous_selection = selection
                for m in selection:
                    yield Completion(str(m), start_position=0)
        elif len(word_before_cursor) >= 1 and word_before_cursor[-1] == ":":
            # _debug_log_to_file('colon')

            selection = list(self.column_map.keys())  # type: ignore
            self.previous_selection = selection
            for m in selection:
                yield Completion(str(m), start_position=0)
        # This goes back to the first if, this is the delayed completion finally completing
        elif self.previous_selection:
            # _debug_log_to_file('previous_selection')

            selection = [
                x for x in self.previous_selection if x.find(word_before_cursor) != -1
            ]
            self.previous_selection = selection

            for m in selection:
                yield Completion(m, start_position=-len(word_before_cursor))
