# -*- coding: utf-8 -*-
"""A Pygments RegexLexer for the PyPRQL CLI.

Attributes
----------
__all__ : List[str]
    List of available lexers.
"""
from typing import List

from pygments.lexer import RegexLexer, include, words
from pygments.token import Comment, Keyword, Name, Number, Punctuation, String, Text

__all__: List[str] = ["PRQLLexer"]


class PRQLLexer(RegexLexer):
    """
    For PRQL.

    .. versionadded:: 1
    """

    name = "PRQL"
    aliases = ["prql"]
    filenames = ["*.prql"]
    mimetypes = ["text/x-prql"]

    validName = r"[a-z_][a-zA-Z0-9_\']*"

    specialName = r"^main "

    builtinOps = (
        "'",
        ".",
        "?",
        ":",
        "|",
        "`",
        ">=",
        ">",
        "=",
        "==",
        "+",
        "+=",
        "<=",
        "<",
        "!=",
        "*",
        "/",
        "-",
        "-=",
        "%",
        "\\",
    )

    reservedWords = words(
        (
            "select",
            "from",
            "filter",
            "derive",
            "aggregate",
            "sort",
            "take",
            "order",
            "by",
            "asc",
            "desc",
            "join",
            "order",
            "side",
        ),
        suffix=r"\b",
    )

    tokens = {
        "root": [
            # Comments
            (r"\{-", Comment.Multiline, "comment"),
            (r"--.*", Comment.Single),
            # Whitespace
            (r"\s+", Text),
            # Strings
            (r'"', String, "doublequote"),
            # Modules
            (r"^\s*module\s*", Keyword.Namespace, "imports"),
            # Imports
            (r"^\s*import\s*", Keyword.Namespace, "imports"),
            # Shaders
            (r"\[glsl\|.*", Name.Entity, "shader"),
            # Keywords
            (reservedWords, Keyword.Reserved),
            # Types
            (r"[A-Z][a-zA-Z0-9_]*", Keyword.Type),
            # Main
            (specialName, Keyword.Reserved),
            # Prefix Operators
            (words((builtinOps), prefix=r"\(", suffix=r"\)"), Name.Function),
            # Infix Operators
            (words(builtinOps), Name.Function),
            # Numbers
            include("numbers"),
            # Variable Names
            (validName, Name.Variable),
            # Parens
            (r"[,()\[\]{}]", Punctuation),
        ],
        "comment": [
            (r"-(?!\})", Comment.Multiline),
            (r"\{-", Comment.Multiline, "comment"),
            (r"[^-}]", Comment.Multiline),
            (r"-\}", Comment.Multiline, "#pop"),
        ],
        "doublequote": [
            (r"\\u[0-9a-fA-F]{4}", String.Escape),
            (r'\\[nrfvb\\"]', String.Escape),
            (r'[^"]', String),
            (r'"', String, "#pop"),
        ],
        "imports": [
            (r"\w+(\.\w+)*", Name.Class, "#pop"),
        ],
        "numbers": [
            (r"_?\d+\.(?=\d+)", Number.Float),
            (r"_?\d+", Number.Integer),
        ],
        "shader": [
            (r"\|(?!\])", Name.Entity),
            (r"\|\]", Name.Entity, "#pop"),
            (r".*\n", Name.Entity),
        ],
    }
