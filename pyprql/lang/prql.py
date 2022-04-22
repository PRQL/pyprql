# -*- coding: utf-8 -*-
"""The Python implementation of PRQL.

Each class in this module directly correcponds to a structure
within the PRQL grammar.
Thus, for each class,
its initialisation parameters correcpond directly to those
tokens the parser expects to find.

Those interested in the actual EBNF-based grammar file should see
`here <https://github.com/prql/PyPrql/blob/main/pyprql/lang/prql.lark>`_.

Attributes
----------
this_module : ModuleType
    The calling module.
script_path : str
    The path to the calling script.
STDLIB_AST : Optional[Root]
    Cache used for long running processes.
GLOBAL_PARSER : Optional[Lark]
    Cache used for long running processes.
GLOBAL_TRANSFORMER : Optional[Transformer]
    Cache used for long running processes.
T : TypeVar
    A type bar with ``bound=_Ast``
"""
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, overload

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import lark
import rich
from icecream import ic
from lark import Lark, Token, Transformer, ast_utils

# Used for lark magic and prql.lark file loading
this_module: ModuleType = sys.modules[__name__]
script_path: str = os.path.dirname(__file__)

# We cache these for longer running processes
STDLIB_AST: Optional["Root"] = None
GLOBAL_PARSER: Optional[Lark] = None
GLOBAL_TRANSFORMER: Optional[Transformer] = None


class _Ast(ast_utils.Ast):
    """An ``ast_utils.Ast`` object."""

    pass


# Represent any type that is derived from _Ast
# Used when input and output need same type.
T = TypeVar("T", bound=_Ast)


@dataclass
class Value(_Ast):
    """A Lark value.

    Parameters
    ----------
    value : str
        The parsed value.
    """

    value: str

    def __str__(self) -> str:
        """Produce the string representation.

        Returns
        -------
        str
            The string representation of the value.

        """
        return str(self.value)


@dataclass
class Name(_Ast, ast_utils.AsList):
    """A Lark Name.

    This is a custom representation that expects
    ``NAME (. NAME)*``.

    Parameters
    ----------
    name : List[str]
    """

    name: List[str]

    def __str__(self) -> str:
        """Produce the string representation.

        Returns
        -------
        str
            The string representation of the name.

        """
        return ".".join([str(x) for x in self.name])


@dataclass
class JinjaMacro(_Ast):
    macro: str

    def __str__(self) -> str:
        return str(self.macro)


@dataclass
class Relation(_Ast):
    relation: Union[str, JinjaMacro]

    def __str__(self) -> str:
        if isinstance(self.relation, JinjaMacro):
            return str(self.relation)
        return "`" + self.relation + "`"


@dataclass
class Expression(_Ast, ast_utils.AsList):
    """A Lark expression.

    Parameters
    ----------
    statements : List[_Ast]
        The objects comprising the statement.
    """

    statements: List[_Ast]

    def __str__(self) -> str:
        """Produce the string representation.

        Returns
        -------
        str
            The string representation of the expression.
        """
        msg = ""
        for s in self.statements:
            msg += f"{s}"

        return msg


@dataclass
class BinaryExpression(_Ast):
    """A binary expression.

    These are normally arithmetic operators,
    like ``+``.

    Parameters
    ----------
    left : _Ast
        Statement on the left of the operator.
    right : Optional[_Ast]
        Statement on the right of the operator.
    operator : Optional[str]
        The operation to perform.
    """

    left: _Ast
    right: Optional[_Ast] = None
    operator: Optional[str] = None  # This will be overridden

    def __str__(self) -> str:
        """Produce the string representation.

        Returns
        -------
        str
            The string representation of the expression.
        """
        if self.right is not None:
            return f"{self.left} {self.operator} {self.right}"
        else:
            return f"{self.left}"


@dataclass
class ExpressionLt(BinaryExpression):
    """Less than operator.

    Parameters
    ----------
    operator : Literal["<"]
    """

    operator: Literal["<"] = "<"


@dataclass
class ExpressionGt(BinaryExpression):
    """Greater than operator.

    Parameters
    ----------
    operator : Literal[">"]
    """

    operator: Literal[">"] = ">"


@dataclass
class ExpressionAdd(BinaryExpression):
    """Addition operator.

    Parameters
    ----------
    operator : Literal["+"]
    """

    operator: Literal["+"] = "+"


@dataclass
class ExpressionSub(BinaryExpression):
    """Subtraction operator.

    Parameters
    ----------
    operator : Literal["-"]
    """

    operator: Literal["-"] = "-"


@dataclass
class ExpressionMul(BinaryExpression):
    """Multiplication operator.

    Parameters
    ----------
    operator : Literal["*"]
    """

    operator: Literal["*"] = "*"


@dataclass
class ExpressionDiv(BinaryExpression):
    """Division operator.

    Parameters
    ----------
    operator : Literal["/"]
    """

    operator: Literal["/"] = "/"


@dataclass
class ExpressionEq(BinaryExpression):
    """Equality operator.

    Parameters
    ----------
    operator : Literal["="]
    """

    operator: Literal["="] = "="


class ParensExpression(BinaryExpression):
    """A parenthetical expression.

    Due to limitations in the parsing,
    we have to know whether the original expression had parentheses.
    To achieve this,
    those binary expressions within parentheses inherit from this class.
    """

    pass


@dataclass
class ExpressionAddParens(ParensExpression):
    """Addition operator within parentheses.

    Parameters
    ----------
    operator : Literal["+"]
    """

    operator: Literal["+"] = "+"


@dataclass
class ExpressionSubParens(ParensExpression):
    """Subtraction operator within parentheses.

    Parameters
    ----------
    operator : Literal["-"]
    """

    operator: Literal["-"] = "-"


@dataclass
class ExpressionMulParens(ParensExpression):
    """Multiplication operator within parentheses.

    Parameters
    ----------
    operator : Literal["*"]
    """

    operator: Literal["*"] = "*"


@dataclass
class ExpressionDivParens(ParensExpression):
    """Division operator within parentheses.

    Parameters
    ----------
    operator : Literal["/"]
    """

    operator: Literal["/"] = "/"


@dataclass
class _JoinType(_Ast):
    """The root join type.

    Note
    ----
    This (``_JoinType``) differs from ``JoinType``.
    The latter defines the join type in the ``Join`` statement for grammar parsing.
    The former (this class) provides a parent class for the varion types of joins.
    """

    def __str__(self) -> str:
        """Produce the string representation of the join.

        Returns
        -------
        str
            The type of join.

        """
        return "JOIN"


@dataclass
class InnerJoin(_JoinType):
    """An inner join."""

    def __str__(self) -> Literal["INNER JOIN"]:
        """Produce the string representation of the join.

        Returns
        -------
        Literal["INNER JOIN"]
        """
        return "INNER JOIN"


@dataclass
class LeftJoin(_JoinType):
    """A left join."""

    def __str__(self) -> Literal["LEFT JOIN"]:
        """Produce the string representation of the join.

        Returns
        -------
        Literal["LEFT JOIN"]
        """
        return "LEFT JOIN"


@dataclass
class RightJoin(_JoinType):
    """A right join."""

    def __str__(self) -> Literal["RIGHT JOIN"]:
        """Produce the string representation of the join.

        Returns
        -------
        Literal["RIGHT JOIN"]
        """
        return "RIGHT JOIN"


@dataclass
class OuterJoin(_JoinType):
    """An outer join."""

    def __str__(self) -> Literal["OUTER JOIN"]:
        """Produce the string representation of the join.

        Returns
        -------
        Literal["OUTER JOIN"]

        """
        return "OUTER JOIN"


@dataclass
class JoinType(_JoinType):
    """The join type token.

    Note
    ----
    This (``JoinType``) differs from ``_JoinType``.
    The former (this class) defines the join type in the ``Join`` statement for grammar parsing.
    The latter provides a parent class for the varion types of joins.
    """

    join_type: _JoinType

    def __str__(self) -> str:
        """Produce the string representation of the join.

        Returns
        -------
        str
            The join type.
        """
        if self.join_type is None:
            return "JOIN"
        else:
            return str(self.join_type)


@dataclass
class Alias(_Ast):
    """A table alias.

    Parameters
    ----------
    name : str
        The table alias.
    """

    name: str

    def __str__(self) -> str:
        """Produce the string representation of the alias.

        Returns
        -------
        str
            The table alias.
        """
        return self.name


# These extra join_types here are to allow for those to be in any position in the parsing rule
@dataclass
class Join(_Ast):
    """The join statement.

    Note
    ----
    The multiple ``join_type`` parameters allow for the parameter to occur anywhere
    and still parse correctly.

    Warning
    -------
    Only one ``join_type`` will be parsed,
    with preference given to the earliest occurring.

    Parameters
    ----------
    join_type : Optional[_JoinType]
        The type of join to perform.
    alias : Optional[Alias]
        Table alias for the joined table.
    join_type_2 : Optional[_JoinType]
        The type of join to perform.
    left_id : Optional[Name]
        Id to join on from left table.
    right_id : Optional[Name]
        Id to join on from right table.
    join_type_3 : Optional[_JoinType]
        The type of join to perform.
    """

    join_type: Optional[_JoinType]
    alias: Optional[Alias]
    name: Relation
    join_type_2: Optional[_JoinType] = None
    left_id: Optional[Name] = None
    right_id: Optional[Name] = None
    join_type_3: Optional[_JoinType] = None

    def get_join_type(self) -> Optional[_JoinType]:
        """Return join type.

        Only one ``join_type`` will be parsed,
        with preference given to the earliest occurring.

        Returns
        -------
        Optional[_JoinType]
            The join type, if pressent.
        """
        if self.join_type is not None:
            return self.join_type
        elif self.join_type_2 is not None:
            return self.join_type_2
        elif self.join_type_3 is not None:
            return self.join_type_3
        else:
            return None


@dataclass
class _FileType(_Ast):
    """The file type parent class.

    Note
    ----
    This (``_FileType``) differs from ``FileType``.
    The latter represents the FileType token for grammar parsing,
    while the former (this class) represents the parent file type.
    """

    pass


@dataclass
class Csv(_FileType):
    """The CSV file type."""

    def __str__(self) -> Literal["csv"]:
        """Produce the string representation of the filetype.

        Returns
        -------
        Literal["csv"]
            The file type.
        """
        return "csv"


@dataclass
class Tsv(_FileType):
    """The TSV file type."""

    def __str__(self) -> Literal["tsv"]:
        """Produce the string representation of the filetype.

        Returns
        -------
        Literal["tsv"]
            The file type.
        """
        return "tsv"


@dataclass
class FileType(_FileType):
    """The file type token.

    Note
    ----
    This (``FileType``) differs from ``_FileType``.
    The latter represents the parent file type class,
    while the former (this class) represents the FileType Token.

    Parameters
    ----------
    file_type : _FileType
        The parsed file type.
    """

    file_type: _FileType

    def __str__(self) -> str:
        """Produce the string representation of the filetype.

        Returns
        -------
        str
            The file type.
        """
        return str(self.file_type)


@dataclass
class To(_Ast):
    """The ``to`` token.

    Parameters
    ----------
    file_type : _FileType
        The file_type to save as.
    name : Name
        The out file name.
    """

    file_type: _FileType
    name: Name

    def __str__(self) -> str:
        """Produce the string representation of the ``to`` statement.

        Returns
        -------
        str
            The file type.
        """
        return f"TO {self.file_type} {self.name}"

    def get_file_type(self) -> _FileType:
        """Return the file_type.

        Returns
        -------
        _FileType
            The out file type of the ``to`` statement.
        """
        return self.file_type


@dataclass
class SelectField(_Ast):
    """A single field from a select statement.

    Parameters
    ----------
    alias : Optional[Alias]
        The alias for the column in the select.
    name : Name
        The column to be selected.
    cast_type : Optional[Name]
        Whether the column should be cast as a new name.
    """

    alias: Optional[Alias]
    name: Name
    cast_type: Optional[Name] = None

    def __str__(self) -> str:
        """Retuan a string representation of the field.

        Returns
        -------
        str
            The SelectFiled representation.
        """
        result = str(self.name)

        if self.cast_type is not None:
            result = f"CAST({result} as {self.cast_type})"

        if self.alias is not None:
            result += f" as {self.alias}"

        return result


@dataclass()
class SelectFields(_Ast, ast_utils.AsList):
    """Multiple SelectField's.

    Parameters
    ----------
    fields : List[SelectField]
        Multiple fields from the same statement.
    """

    fields: List[SelectField]

    def __str__(self) -> str:
        """Retuan a string representation of the field.

        Returns
        -------
        str
            The SelectFiled representation.
        """
        return ",".join([str(x) for x in self.fields])


@dataclass()
class SortField(_Ast):
    """Field from a ``sort`` statement.

    Parameters
    ----------
    name : Name
        The column to sort by.
    """

    name: Name

    def __str__(self) -> str:
        """Retuan a string representation of the field.

        Returns
        -------
        str
            The SortFiled representation.
        """
        return str(self.name)


@dataclass()
class SortFields(_Ast, ast_utils.AsList):
    """Multiple fields from the same ``Sort`` statement.

    Parameters
    ----------
    fields : List[SortField]
        Multiple SortFields
    """

    fields: List[SortField]

    def __str__(self) -> str:
        """Retuan a string representation of the field.

        Returns
        -------
        str
            The SortFiled representation.
        """
        return ",".join([str(x) for x in self.fields])


@dataclass()
class PipeBody(_Ast):
    """The body of a statement in a Pipe.

    Parameters
    ----------
    body : str
        The pipe body statement.
    """

    body: str

    def __str__(self) -> str:
        """Retuan a string representation of the body.

        Returns
        -------
        str
            The PipeBody representation.
        """
        return str(self.body)


@dataclass
class Select(_Ast):
    """The ``Select`` Statement.

    Parameters
    ----------
    fields : SelectFields
        Any fields of the statement.
    """

    fields: SelectFields

    def __str__(self) -> str:
        """Retuan a string representation of the ``Select`` statement.

        Returns
        -------
        str
            The Select statement representation.
        """
        return ",".join([str(f) for f in self.fields.fields])


@dataclass
class DeriveBody(_Ast):
    """The body of a ``Derive`` statement.

    Parameters
    ----------
    val : Union[str, _Ast]
        Either a string or a ``BinaryExpression``.
    """

    val: Union[str, _Ast]

    def __str__(self) -> str:
        """Retuan a string representation.

        Returns
        -------
        str
            The DeriveBody statement representation.
        """
        return str(self.val)


@dataclass
class Operator(_Ast):
    """Operators indicating common manipulations.

    Examples include all the common boolean and arithmetic operations.

    Parameters
    ----------
    op : Token
        The operator symbol.
    """

    op: Token

    def __str__(self) -> str:
        """Retuan a string representation.

        Returns
        -------
        str
            The Operator statement representation.
        """
        return self.op.value


@dataclass
class GroupBy(_Ast, ast_utils.AsList):
    """The columns to group by in an ``Aggregate`` statement.

    Parameters
    ----------
    fields : List[str]
        Columns to group by.
    """

    fields: List[str]

    def __str__(self) -> str:
        """Retuan a string representation.

        Returns
        -------
        str
            The GroupBy token representation.
        """
        return ",".join([str(f) for f in self.fields])


@dataclass
class AggregateBody(_Ast, ast_utils.AsList):
    """The manipulations performed in the ``Aggregate`` statement.

    These are normally of the form ``NAME : PipeBody``.

    Parameters
    ----------
    statements : List[_Ast]
        All manipulations performed.
    """

    statements: List[_Ast]

    def __str__(self) -> str:
        """Retuan a string representation.

        Returns
        -------
        str
            The AggregateBody token representation.
        """
        return f"{[str(s) for s in self.statements]}"


@dataclass
class Aggregate(_Ast):
    """The ``Aggregate`` statement.

    Parameters
    ----------
    group_by : Optional[GroupBy]
        Columns to group by.
    aggregate_body : Optional[AggregateBody]
        Operations to perform.
    """

    group_by: Optional[GroupBy] = None
    aggregate_body: Optional[AggregateBody] = None


@dataclass
class DeriveLine(_Ast):
    """Any line of a ``derive`` statement.

    Parameters
    ----------
    name : str
        Name of the column to be created.
    expression : Expression
        How it is to be created.
    """

    name: str
    expression: Expression

    def __str__(self) -> str:
        """Retuan a string representation.

        Returns
        -------
        str
            The DeriveLine token representation.
        """
        return str(self.expression)


@dataclass
class Derive(_Ast, ast_utils.AsList):
    """The ``derive`` statement.

    Parameters
    ----------
    fields : List[DeriveLine]
        The lines of the derive statement.
    """

    fields: List[DeriveLine]


class _Direction(_Ast):
    """The parent direction class.

    This differs from ``Direction``.
    That class represents the actual token for parsing,
    while this class serves as the parent class for all possible directions.
    """

    pass


@dataclass
class Direction(_Ast):
    """The direction token.

    This differs from ``_Direction``.
    That class represents parent class for all possible directions,
    while this class serves as the actual token for parsing.

    Parameters
    ----------
    direction : Optional[_Direction]
        The sort order.
    """

    direction: Optional[_Direction] = None

    def __str__(self) -> str:
        """Return a string representation.

        Returns
        -------
        str
            The sort order.
        """
        return str(self.direction)


@dataclass
class Ascending(_Direction):
    """Ascending sort.

    Parameters
    ----------
    direction : Literal["ASC"]
        The sort direction.
    """

    direction: Literal["ASC"] = "ASC"

    def __str__(self) -> Literal["ASC"]:
        """Return a string representation.

        Returns
        -------
        Literal["ASC"]
            The sort order.
        """
        return self.direction


@dataclass
class Descending(_Direction):
    """Descending sort.

    Parameters
    ----------
    direction : Literal["DESC"]
        The sort direction.
    """

    direction: Literal["DESC"] = "DESC"

    def __str__(self) -> Literal["DESC"]:
        """Return a string representation.

        Returns
        -------
        Literal["DESC"]
            The sort order.
        """
        return self.direction


@dataclass
class Sort(_Ast):
    """The ``sort`` statement.

    Note
    ----
    Multiple direction parameters allow the parser to detect direction
    anywhere in the clause.

    Warning
    -------
    If multiple directions are provided,
    then the first will be parsed.

    Parameters
    ----------
    direction1 : Optional[Direction]
        The sort order.
    fields : Optional[SortFields]
        The columns to sort by.
    direction2 : Optional[Direction]
        The sort order.
    """

    direction1: Optional[Direction] = None
    fields: Optional[SortFields] = None
    direction2: Optional[Direction] = None

    def get_direction(self) -> Optional[Direction]:
        """Return the sort direction..

        All comments about field preference from the main class
        are still relevant here.

        Returns
        -------
        Optional[Direction]
            The sort direction.
        """
        ret = None
        if self.direction1 is not None:
            ret = self.direction1
        elif self.direction2 is not None:
            ret = self.direction2
        return ret

    def __str__(self) -> str:
        """Return a string representation..

        Returns
        -------
        str
            The string representation of the sort statement.
        """
        direction = self.get_direction()
        ret = f"{str(self.fields)}"
        if direction is not None:
            ret = f"{ret} {str(direction)}"
        return ret


@dataclass
class Take(_Ast):
    """The ``take`` statement.

    Parameters
    ----------
    qty : str
        How many rows to take.
    offset : str
        How many rows to skip from the start.
    """

    qty: str
    offset: Optional[str] = None

    def __str__(self) -> str:
        """Return a string representation.

        Returns
        -------
        str
            the string representation of the take statement.
        """
        sql = f"LIMIT {self.qty}"
        if (
            self.offset is not None
            and self.offset
            and isinstance(self.offset, lark.lexer.Token)
        ):
            sql += f" OFFSET {self.offset} "
        return sql


# TODO: clarify filter documentation
@dataclass
class FilterLine(_Ast):
    """The ``FilterLine`` token.

    Parameters
    ----------
    val : _Ast
        Usually a BinaryExpression, SSTRING
    """

    val: Optional[_Ast] = None

    def __str__(self) -> str:
        """Return a string representation.

        Returns
        -------
        str
            The string representation of the take statement.
        """
        return str(self.val)


@dataclass
class Filter(_Ast, ast_utils.AsList):
    """The ``filter`` statement.

    Parameters
    ----------
    fields : List[FilterLine]
        The fields to filter by.
    name : str
    """

    fields: List[FilterLine]
    name: str = "filter"


@dataclass
class Pipes(_Ast, ast_utils.AsList):
    """A collection of ``Pipes``.

    These form the core of the parser and can be:
    join, select, derive, filter, sort, take, aggregate, or to.

    Parameters
    ----------
    operations : List[_Ast]
        The operations performed in the query.
    """

    operations: List[_Ast]


@dataclass
class From(_Ast):
    """The ``From`` statement.

    In addition to including the ``from`` statement that specifies a table,
    this also includes any alias for that table,
    as well as all resultant pipes.

    Parameters
    ----------
    alias : Optional[Alias]
        An alias for the queried table.
    name : Optional[Name]
        The name of the queried table.
    pipes : Optional[Pipes]
        All operations, other than from, in the query.
    """

    alias: Optional[Alias]
    name: Relation
    pipes: Optional[Pipes] = None


@dataclass
class FuncArgs(_Ast, ast_utils.AsList):
    """The arguments passed to a function.

    Parameters
    ----------
    fields : Optional[List]
        Name of arguments.
    """

    fields: Optional[List] = None

    def __str__(self) -> str:
        """Return a string representation.

        Returns
        -------
        str
            The string representation of the take statement.
        """
        if self.fields is None:
            return ""
        else:
            return ",".join([str(x) for x in self.fields])


@dataclass
class FuncBody(_Ast, ast_utils.AsList):
    """A series of expressions defining the function's function.

    Parameters
    ----------
    fields : List[str]
        The expressions defining the function.
    """

    fields: List[str]


@dataclass
class FuncDef(_Ast):
    """The full function definition.

    Parameters
    ----------
    name : Name
        The function's name.
    func_args : Optional[FuncArgs]
        The function's arguments.
    func_body : Optional[FuncBody]
        The expressions defining the function.
    """

    name: Name
    func_args: Optional[FuncArgs] = None
    func_body: Optional[FuncBody] = None


# TODO: The lark definition includes 4 params?
# TODO: Make more robust to variable parameter number?
@dataclass
class FuncCall(_Ast):
    """A function call.

    Currently,
    the number of parameters is specified in the parser.
    This simplifies the parsing grammar,
    at the expense of a upper limit for parameter number.

    Parameters
    ----------
    name : Optional[Name]
        The name of the function
    param1 : Any
    param2 : Any
    param3 : Any
    """

    name: Optional[Name] = None
    parm1: Any = None
    parm2: Any = None
    parm3: Any = None


# TODO: clarify PipedCall purpose
@dataclass
class PipedCall(_Ast):
    """A chained function call that allows functions to be piped to each other.

    Parameters
    ----------
    param1: Name
        The thing to be piped.
    func_body : FuncCall
        A function call.
    """

    parm1: Name
    func_body: FuncCall


@dataclass
class ValueDef(_Ast):
    """Assign the result of a query to a value.

    Parameters
    ----------
    name : Name
        The name of the value.
    value_body : From
        The query producing the value.
    """

    name: Name
    value_body: From


@dataclass
class ValueDefs(_Ast, ast_utils.AsList):
    """Multiple ``ValueDef``.

    Used to construct the root token.

    Parameters
    ----------
    fields : List[ValueDef]
        A list of ValueDef's.
    """

    fields: List[ValueDef]


@dataclass
class FuncDefs(_Ast, ast_utils.AsList):
    """Multiple ``FuncDef``.

    Used to construct the root token.

    Parameters
    ----------
    fields : List[FuncDef]
        A list of FuncDef's.
    """

    fields: List[FuncDef]


@dataclass
class WithDef(_Ast):
    """A Common Table Expression (CTE) using ``with``.

    Used to construct the root token.

    Parameters
    ----------
    name : Name
        The CTE name.
    _from : From
        The query producing the CTE.
    """

    name: Name
    _from: From


class Root(_Ast):
    """The top level definition that holds all other definitions.

    Of the form: ``(with_def)* value_defs func_defs from``

    To increase the flexibility of the language and ease some parsing difficulties,
    the ``assign_field`` method is used during initialisation.
    This assures that each clause is only assigned iff a clause of the apropriate type
    is present among the inputs.

    Parameters
    ----------
    with_def : Optional[WithDef]
        Any CTEs in the query.
    _from : Optional[From]
        The main ``from`` statement.
    value_def : Optional[ValueDefs]
        Any ``value`` assignments in the query.
    func_def : Optional[FuncDefs]
        Any functions defined in the query.
    """

    def __init__(
        self,
        with_def: Optional[WithDef] = None,
        _from: Optional[From] = None,
        value_def: Optional[ValueDefs] = None,
        func_def: Optional[FuncDefs] = None,
    ) -> None:
        values = [with_def, _from, value_def, func_def]
        self.with_def = self.assign_field(WithDef, values)
        self._from = self.assign_field(From, values)
        self.value_defs = self.assign_field(ValueDefs, values)
        self.func_defs = self.assign_field(FuncDefs, values)

    def get_from(self) -> Optional[From]:
        """Returns the main ``from`` statement in the query.

        Returns
        -------
        Optional[From]
            The ``from`` statement, if present.
        """
        return self._from

    # TODO: lark allows for multiple withs, this does not?
    def get_cte(self) -> Optional[WithDef]:
        """Returns the CTE in the query.

        Returns
        -------
        Optional[WithDef]

        """
        return self.with_def

    T = TypeVar("T", bound=_Ast)

    def assign_field(self, clazz: Type[T], values: List[Any]) -> Optional[T]:
        """Initialise a field, by first checking if a token if present among inputs.

        Parameters
        ----------
        clazz : Type[T]
            The type of token to search for.
        values : List[Any]
            All inputs to the class.

        Returns
        -------
        Optional[T]
            The first instance of type ``clazz`` among ``values``.
        """
        for v in values:
            if isinstance(v, clazz):
                return v
        return None


@dataclass
class NameValuePair(_Ast):
    """A name-value pair.

    This is a helper class.
    It is **not** parsed by Lark.

    Parameters
    ----------
    name : str
        The name of a token.
    value : _Ast
        A language token.
    """

    name: str
    value: _Ast

    def __str__(self) -> str:
        """Return a string representation.

        Returns
        -------
        str
            The representation of the name-value pair.
        """
        return f"{self.value}"


# TODO: is this class used at all?
class ToAst(Transformer):
    """Various methods for parsing strings to their apropriate AST values."""

    # TODO: should this method remove quotes or not?
    # The comment says it should, but then no slicing occurs.
    def STRING(self, s: str) -> str:
        """Return the string, with quotes removed.

        Parameters
        ----------
        s : str
            The string to return.

        Returns
        -------
        str
            ``s``, but without quotes?
        """
        # Remove quotation marks
        return s  # s[1:-1]

    def SSTRING(self, s: str) -> str:
        """Pass a string as SQL.

        This is any string of the form s"text".
        Upon return,
        the leading s and the quotes are dropped,
        returning the raw SQL contained there in.

        Parameters
        ----------
        s : str
            The s-string to clean.

        Returns
        -------
        str
            The s-string with the s and quotes removed.
        """
        return s[2:-1]

    # TODO: should this method remove slashes or not?
    def ESCAPED_STRING(self, s: str) -> str:
        """Parse an escaped string.

        This removes any leading escapes to preserve the passed quote marks.

        Parameters
        ----------
        s : str
            A string where the quotes have been escaped.

        Returns
        -------
        str
            The string with escapes removed but quotes kept.
        """
        return s  # s.replace('\\"', '"').replace("\\'", "'")

    # TODO: This is the same as ESCAPED_STRING and STRING?
    def NEWLINE(self, s: str) -> str:
        """Handle new lines in the string.

        Parameters
        ----------
        s : str
            A string containing new lines.

        Returns
        -------
        str
            The string with the new lines correctly processed.
        """
        return s


# TODO: perhaps a bit more natural to handle this with pathlib.Path?
def read_file(filename: str, path: str = script_path) -> str:
    """Read a file and return its contents.

    Parameters
    ----------
    filename : str
        The file to read.
    path : str
        Default : the run path of the script.
        The root folder.

    Returns
    -------
    str
        The contents of the file.
    """
    with open(path + os.sep + filename, "r") as f:
        x = f.read()
    return x


def parse(_text: str, verbose: bool = False, dbt: bool = False) -> Root:
    """Parse a PRQL string to SQL, and return the Root.

    Parameters
    ----------
    _text : str
        The query string to parse.
    verbose : bool
        Whether or not to print verbose information.
    dbt : bool
        Whether or not to enable dbt-style parsing.

    Returns
    -------
    Root
        The Root structure.
    """
    global GLOBAL_PARSER
    global GLOBAL_TRANSFORMER
    text = _text + "\n"
    if GLOBAL_PARSER is None:
        grammar = read_file("prql.lark")
        # TODO: change to dbt check
        if dbt:
            grammar += read_file("dbt.lark")

        GLOBAL_PARSER = Lark(
            grammar,
            start="root",
            parser="lalr",
            transformer=ToAst(),
        )
    tree = GLOBAL_PARSER.parse(text)
    if verbose:
        rich.print(tree)
    if GLOBAL_TRANSFORMER is None:
        GLOBAL_TRANSFORMER = ast_utils.create_transformer(this_module, ToAst())
    return GLOBAL_TRANSFORMER.transform(tree)


def to_sql(prql: str, verbose: bool = False, dbt: bool = False) -> str:
    """Convert a query to SQL.

    First,
    convert a given query to the AST ``Root``.
    Then,
    convert the ``Root`` token to raw SQL.

    Parameters
    ----------
    prql : str
        The PRQL query to parse
    verbose : bool
        Whether or not to print verbose information.
    dbt : bool
        Whether or not to enable dbt-style parsing.

    Returns
    -------
    str
        The raw SQL.
    """
    global STDLIB_AST
    ast = parse(prql, verbose, dbt)
    if verbose:
        rich.print(ast.get_from())
    if STDLIB_AST is None:
        STDLIB_AST = parse(read_file("stdlib.prql"))
    return (
        ast_to_sql(ast.get_from(), [ast, STDLIB_AST], verbose=verbose)
        .replace("   ", " ")
        .replace("  ", " ")
    )


def pretty_print(root: Root) -> None:
    """Print pretty things.

    A thin wrapper around ``rich.print``.

    Parameters
    ----------
    root : Root
        The ``Root`` token.
        Generated by ``parse``.
    """
    rich.print(root)


# Most basic call - returns first instance.
@overload
def get_operation(
    *,
    ops: List[_Ast],
    class_type: Type[T],
) -> T:
    ...


# Most basic call - returns all instances.
@overload
def get_operation(
    *,
    ops: List[_Ast],
    class_type: Type[T],
    return_all: Literal[True],
) -> List[T]:
    ...


# Return last instance.
@overload
def get_operation(
    *,
    ops: List[_Ast],
    class_type: Type[T],
    last_match: Literal[True],
) -> T:
    ...


# Return all instances before a specified type.
@overload
def get_operation(
    *,
    ops: List[_Ast],
    class_type: Type[T],
    return_all: Literal[True],
    before: Type[_Ast],
) -> List[T]:
    ...


# Return all instances after a specified type.
@overload
def get_operation(
    *,
    ops: List[_Ast],
    class_type: Type[T],
    return_all: Literal[True],
    after: Type[_Ast],
) -> List[T]:
    ...


def get_operation(
    *,
    ops: List[_Ast],
    class_type: Type[T],
    return_all: Optional[bool] = None,
    last_match: Optional[bool] = None,
    before: Optional[Type[_Ast]] = None,
    after: Optional[Type[_Ast]] = None,
) -> Union[List[T], T]:
    """Return operations of a specific type.

    Given a list of operations,
    return those of a given class.
    The remaining boolean parameters allow control over number returned
    and where amongst the list they occur.

    In order to specify the whether the return value is a singleton or a list,
    we must abuse some overloaded signatures.
    In order to achieve this,
    the signature requires kwargs only.

    Note
    ----
    ``T`` is a TypeVar with ``bound=_Ast``.
    This allows us to specify that the returned list or item must be of the type specified
    while simultaneously allowing it to be any element of the grammar.

    Parameters
    ----------
    ops : List[_Ast]
        A list of operations.
    class_type : Type[T]
        The operation type to return.
        See ``Note`` on ``T``.
    return_all : bool
        Return all occurences of the operation.
    last_match : bool
        Return the last occurence of the operation.
    before : Type
        Return only those occurences before an operation of this type.
    after : Type
        Return only those occurences after an operation of this type.

    Returns
    -------
    Union[List[T], T]
        If ``return_all``, then ``List[T]``.
        If not ``return_all``, then ``T``.

    Raises
    ------
    PRQLException
        If both ``after`` and ``before`` are specified,
        or if either ``after`` or ``before`` is specified without ``return_all``.
    """
    ops_list = ops
    if return_all is None:
        return_all = False
    if last_match is None:
        last_match = False
    ret = []
    is_before = True
    is_after = False
    if after is not None and before is not None:
        raise PRQLException("Cannot specify both before and after in get_operation")
    if before is not None or after is not None:
        if not return_all:
            raise PRQLException("Cannot specify before or after without return_all")
    if last_match:
        ops_list = list(reversed(ops))
    for op in ops_list:
        # print(type(op))
        if isinstance(op, class_type):
            if return_all:

                if before is not None:
                    if is_before:
                        ret.append(op)
                elif before is None and after is None:
                    ret.append(op)
                elif after is not None:
                    if is_after:
                        ret.append(op)

            else:
                return op
        if before is not None:
            if isinstance(op, before):
                is_before = False
        if after is not None:
            if isinstance(op, after):
                is_after = True
    return ret


def _generate_alias(s: str, n: int = 1) -> str:
    """Generate an alias for a given string.

    This alias will be the given string,
    an underscore,
    and the firt ``n`` characters of the string.

    Parameters
    ----------
    s : str
        The name from which an alias will be created.
    n : int
        The number of characters to use.

    Returns
    -------
    str
        The aliased string.
    """
    alias = s + "_" + s[0:n]

    for c in "}{][)(,\"' ":
        alias = alias.replace(c, "")
    return alias


def replace_all_tables(
    from_long: str, from_short: str, join_long: List[str], join_short: List[str], s: str
) -> str:
    """Replace all table names with their apropriate aliases.

    ``join_long`` and ``join_short`` are paired.
    That is,
    the i-th else of join_long will be replaced with the i-th element of join_short.

    Parameters
    ----------
    from_long : str
        The full table name.
    from_short : str
        The aliased (short) table name.
    join_long : List[str]
        A list of full names to be replaced.
    join_short : List[str]
        The short versions with which to replace ``join_long``.
    s : str
        The string in which the replacement will occur.

    Returns
    -------
    str

    """
    s = s.replace(f"{from_long}.", f"{from_short}.")
    if join_long and len(join_long) > 0:
        for i in range(len(join_long)):
            s = s.replace(f"{join_long[i]}.", f"{join_short[i]}.")
    return s


# TODO: I've left the auto generated docstring, as I'm not sure what the function is used for.
def wrap_replace_all_tables(
    from_long: str, from_short: str, join_long: List[str], join_short: List[str]
) -> Callable[[str], str]:
    """Wrap ``replace_all_tables``.

    Creates a callable of ``replace_all_tables`` where all parameters are already supplied
    except for ``s``, the string on which the function will operate.

    Parameters
    ----------
    from_long : str
        The full table name.
    from_short : str
        The aliased (short) table name.
    join_long : List[str]
        A list of full names to be replaced.
    join_short : List[str]
        The short versions with which to replace ``join_long``.

    Returns
    -------
    Callable[[str], str]
        An instance of ``replace_all_tables`` that need only be passed ``s``
    """

    def inner(x: str) -> str:
        return replace_all_tables(from_long, from_short, join_long, join_short, x)

    return inner


def build_symbol_table(roots: List[Root]) -> Dict[str, List[_Ast]]:
    """Build a symbol table from the ``Root`` instance.

    Given a list of ``Roots``,
    create a hashmap/dictionary of all their fields.
    This allows easy access to all fields in a set of ``Roots``.

    Parameters
    ----------
    roots : List[Root]
        A list of ``Root`` tokens.

    Returns
    -------
    Dict[str, List[_Ast]]
        All fields in those tokens.
    """
    table = defaultdict(list)
    for _root in roots:
        root: Root = _root
        for n in root.value_defs.fields:
            table[str(n.name)].append(n)
        for n in root.func_defs.fields:
            table[str(n.name)].append(n)
        if root.get_from().pipes:
            derives = get_operation(
                ops=root.get_from().pipes.operations, class_type=Derive, return_all=True
            )
            for d in derives:
                for line in d.fields:
                    table[str(line.name)].append(
                        NameValuePair(str(line.name), line.expression)
                    )
    return table


class PRQLException(Exception):
    """A basic exception for PRQL related errors."""

    pass


# TODO: I've left the auto generated docstring, as I'm not sure what the function is used for.
def _replace_variables(ast: _Ast, symbol_table: Dict[str, List[_Ast]]) -> str:
    """_replace_variables.

    Parameters
    ----------
    ast : _Ast
        ast
    symbol_table : Dict[str, List[_Ast]]
        symbol_table

    Returns
    -------
    str
        The new string.
    """
    if isinstance(ast, Expression):
        msg = ""
        exp: Expression = ast
        for s in exp.statements:
            msg += str(replace_variables(str(s), symbol_table))
        return msg
    elif isinstance(ast, DeriveBody):
        msg = _replace_variables(ast.val, symbol_table)  # type: ignore [arg-type]
        return msg
    elif isinstance(ast, BinaryExpression):
        msg = ""
        if ast.left is not None:
            msg = _replace_variables(ast.left, symbol_table)
        if ast.right is not None:
            msg += ast.operator + _replace_variables(ast.right, symbol_table)

        return msg
    else:
        key = str(ast)
        if key in symbol_table:
            return str(symbol_table[key][0])
        else:
            return str(ast)


def replace_variables(_param: Any, symbol_table: Dict[str, List[_Ast]]) -> str:
    """Parses a symbol_table to expand all references to a variable.

    Parameters
    ----------
    _param : Any
        A parameter to search for.
    symbol_table : Dict[str, List[_Ast]]
        The hashmap/dictionary for a ``Root`` structure.

    Returns
    -------
    str
        The replaced string.

    Raises
    ------
    PRQLException
        If a symbol type is unknown.
    """
    param_str: str = str(_param)

    if param_str in symbol_table:
        if not symbol_table[param_str]:
            return _param
        if isinstance(symbol_table[param_str][0], NameValuePair):
            nvp: NameValuePair = symbol_table[param_str][0]
            msg = _replace_variables(nvp.value, symbol_table)
            if msg is None:
                return str(nvp.value)
            else:
                return msg
        else:
            raise PRQLException(
                f"Unkown type in symbol table , for {type(symbol_table[param_str][0])} "
            )
            # return str(symbol_table[param_str][0])
    else:
        return _param


def execute_function(
    f: FuncCall,
    roots: Union[Root, List],
    symbol_table: Dict[str, List[_Ast]],
) -> str:
    """Execute a passed PRQL function.

    Parameters
    ----------
    f : FuncCall
        The called function.
    roots : Union[Root, List]
        The ``Root`` instance containing that function.
    symbol_table : Dict[str, List[_Ast]]
        The symbol table for that ``Root`` instance.

    Returns
    -------
    str
        The results of the called function.

    Raises
    ------
    PRQLException
        If a text-based function has more than one statement.
    """
    msg = ""
    name = str(f.name)
    func_defs: List[FuncDef] = symbol_table[name]
    func_def: Optional[FuncDef] = None

    if len(func_defs) == 1:
        func_def = func_defs[0]
    else:
        # This is if we have multiple functions with the same name
        # We then match against the argument count

        func_call_parm_count = get_function_parm_count(f)

        for defintion in func_defs:
            if get_function_parm_count(defintion) == func_call_parm_count:
                func_def = defintion
                break

    # try:
    if func_def:
        for line in func_def.func_body.fields:
            if isinstance(line, PipeBody):
                line = line.body
            if isinstance(line, Expression):
                exp: Expression = line
                if len(exp.statements) != 1:
                    raise PRQLException(
                        "Currently only single statement functions that are text based are supported"
                    )
                else:
                    line = str(exp.statements[0])
            if type(line) == str:
                args = {}

                vals = [
                    safe_to_sql(
                        replace_variables(f.parm1, symbol_table),
                        roots,
                        symbol_table,
                    ),
                    safe_to_sql(
                        replace_variables(f.parm2, symbol_table),
                        roots,
                        symbol_table,
                    ),
                    safe_to_sql(
                        replace_variables(f.parm3, symbol_table),
                        roots,
                        symbol_table,
                    ),
                ]

                if func_def.func_args is not None:
                    for i in range(0, len(func_def.func_args.fields)):  # type: ignore[arg-type]
                        n = str(func_def.func_args.fields[i])  # type: ignore[index]
                        args[n] = vals[i]
                    msg = line.format(**args)
                else:
                    msg = line
    # except Exception as e:
    #     msg = repr(e)
    #     if "KeyError" in msg:
    #         msg = f"Function {name} had an error executing , full error: {msg}"
    #     raise PRQLException(msg)
    return msg


def is_empty(a: Any) -> bool:
    """Check if an object is empty.

    Effectively,
    check that ``a`` is not ``None`` and that ``a`` is truthy.

    Parameters
    ----------
    a : Any
        The object to check.

    Returns
    -------
    bool
        Whether or not the object is empty.
    """
    if a is not None and a:
        return False
    return True


def get_function_parm_count(f: Union[FuncCall, FuncDef]) -> int:
    """Return the number of parameters in a function.

    Parameters
    ----------
    f : Union[FuncCall, FuncDef]
        Either a called function or a function definition.

    Returns
    -------
    int
        The number of parameters in the passed function.
    """
    parm_count = 0
    if isinstance(f, FuncCall):
        if not is_empty(f.parm1):
            parm_count += 1
        if not is_empty(f.parm2):
            parm_count += 1
        if not is_empty(f.parm3):
            parm_count += 1
    elif isinstance(f, FuncDef):
        if f.func_args is not None:
            parm_count = len(f.func_args.fields)  # type: ignore[arg-type]
    return parm_count


def safe_to_sql(
    rule: Any,
    roots: Union[Root, List],
    symbol_table: Optional[Dict[str, List[_Ast]]] = None,
    verbose: bool = False,
) -> Optional[str]:
    """Safely convert a rule to SQL.

    This checks the input type of ``rule``,
    and correctly converts it to SQL using the apropriate method.

    Parameters
    ----------
    rule : Any
        rule
    roots : Union[Root, List]
        roots
    symbol_table : Optional[Dict[str, List[_Ast]]]
        symbol_table
    verbose : bool
        verbose

    Returns
    -------
    Optional[str]
        The string representation of the SQL.
    """
    if isinstance(rule, str):
        return rule
    elif isinstance(rule, Token) or isinstance(rule, Name):
        return str(rule)
    elif isinstance(rule, _Ast):
        return ast_to_sql(rule, roots, symbol_table, None, verbose)
    else:
        return None


def safe_get_alias(join: Union[Join, From], join_long: str) -> str:
    """Safely create an alias for a table.

    If the passed ``Join`` or ``From`` has an alias property,
    then the string representation of that is returned.
    If not,
    then the ``_generate_alias`` function is used to create one.

    Parameters
    ----------
    join : Union[Join, From]
        The statement to check for an alias.
    join_long : str
        The string to use for alias generation,
        if ``join.alias`` is None.

    Returns
    -------
    str
        The created alias.
    """
    if join.alias is not None:
        join_short = str(join.alias)
    else:
        join_short = _generate_alias(join_long)
    return join_short


def build_replace_tables(root: Root) -> Callable[[str], str]:
    """Build the correct ``replace_tables`` calls for a given ``Root``.

    Essentially,
    this programatically calls ``build_replace_tables`` to build the correct ``replace_tables`` call,
    based on the various statements present in ``root``.

    Parameters
    ----------
    root : Root
        The ``Root`` object from a PRQL query.

    Returns
    -------
    Callable[[str], str]
        The constructed call of ``replace_tables``.
        This needs only be passed the string to operate on.
    """
    all_join_longs = []
    all_join_shorts = []
    from_long = ""
    from_short = ""
    _from = root.get_from()
    joins: List[Join] = []

    if _from is not None:
        from_long = str(_from.name)
        from_short = safe_get_alias(_from, from_long)
        if _from.pipes is not None:
            joins = get_operation(
                ops=_from.pipes.operations, class_type=Join, return_all=True
            )

    for join in joins:
        if join:
            join_long = str(join.name)
            join_short = safe_get_alias(join, join_long)

            all_join_shorts.append(join_short)
            all_join_longs.append(join_long)

    replace_tables = wrap_replace_all_tables(
        from_long, from_short, all_join_longs, all_join_shorts
    )
    return replace_tables


def ast_to_sql(
    rule: Union[_Ast, Token],
    roots: Union[Root, List],
    symbol_table: Optional[Dict[str, List[_Ast]]] = None,
    replace_tables: Optional[Callable[[str], str]] = None,
    verbose: bool = True,
) -> str:
    """Construct the SQL from a given Ast.

    The SQL template is in the form
    ``sql = f"SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {havings_str} {order_by_str} {limit_str} {to_str}``.
    We will be creating these strings to form the final SQL
    by checking for the presence, absence, and order of various statements.

    Parameters
    ----------
    rule : Union[_Ast, Token]
        The rule to parse.
    roots : Union[Root, List]
        Either a ``Root`` object, or a list thereof.
    symbol_table : Optional[Dict[str, List[_Ast]]]
        The hashmap/dictionary of the statements present in ``Roots``.
    replace_tables : Optional[Callable[[str], str]]
        The function to use for handling table aliases.
    verbose : bool
        Whether to print verbose output.

    Returns
    -------
    str
        The generated SQL query.

    Raises
    ------
    PRQLException
        If function or statement type is unknown.
    """
    # Renaming it here silences the static analysis warnings below for replace_tables being None
    replace_tables_func: Callable[[str], str] = replace_tables  # type: ignore[assignment]

    if isinstance(roots, Root):
        root = roots
    else:
        root = roots[0]

    if symbol_table is None:
        symbol_table = build_symbol_table([roots] if isinstance(roots, Root) else roots)

    if replace_tables_func is None:
        replace_tables_func: Callable = build_replace_tables(root)  # type: ignore[no-redef]

    if isinstance(rule, Token):
        return str(rule)

    if isinstance(rule, From):
        select_str = ""
        agg_str = ""
        derives_str = ""
        from_str = ""
        join_str = ""
        filter_str = ""
        group_by_str = ""
        havings_str = ""
        order_by_str = ""
        limit_str = ""
        to_str = ""
        ###

        _from = rule
        from_long = ""
        from_short = ""
        ops = _from.pipes
        joins: List[Join] = get_operation(
            ops=ops.operations, class_type=Join, return_all=True
        )
        agg: Aggregate = get_operation(ops=ops.operations, class_type=Aggregate)
        take: Take = get_operation(ops=ops.operations, class_type=Take, last_match=True)
        sort: Sort = get_operation(ops=ops.operations, class_type=Sort)

        filters = get_operation(
            ops=ops.operations, class_type=Filter, return_all=True, before=Aggregate
        )
        wheres_from_derives = get_operation(
            ops=ops.operations, class_type=Derive, return_all=True
        )
        havings = get_operation(
            ops=ops.operations, class_type=Filter, return_all=True, after=Aggregate
        )
        selects = get_operation(ops=ops.operations, class_type=Select, return_all=True)
        tos = get_operation(ops=ops.operations, class_type=To, last_match=True)

        from_long = str(_from.name)
        from_short = safe_get_alias(_from, from_long)

        from_str = f"`{from_long}`" + " " + from_short

        for join in joins:
            if join:
                join_long = str(join.name)
                join_short = safe_get_alias(join, join_long)

                left_id = replace_tables_func(str(join.left_id))
                right_id = replace_tables_func(str(join.right_id))

                if right_id is None or right_id == "None":
                    right_id = left_id

                if left_id.find(".") == -1:
                    left_side = str(from_short + "." + left_id).replace(
                        from_short + "." + from_short + ".", from_short + "."
                    )
                else:
                    left_side = str(left_id).replace(
                        from_short + "." + from_short + ".", from_short + "."
                    )

                if right_id.find(".") == -1:
                    right_side = replace_tables_func(
                        str(join_long + "." + right_id).replace(
                            join_short + "." + join_short + ".", join_short + "."
                        )
                    )
                else:
                    right_side = replace_tables_func(
                        str(right_id).replace(
                            join_short + "." + join_short + ".", join_short + "."
                        )
                    )

                join_type = join.get_join_type()
                if join_type is None:
                    join_type_str = "JOIN"
                else:
                    join_type_str = str(join.get_join_type())

                join_str += replace_tables_func(
                    f"{join_type_str} {join.name} {join_short} ON {left_side} = {right_side} "
                )

        if selects:
            for select in selects:
                select_str += replace_tables_func(str(select))

        if tos:
            # Tos is generated with `last_match=True`, so will always be single instance.
            # Additionally, __str__method is defined for simplicity.
            to_str += str(tos)

        if havings:
            havings_str = "HAVING "
            for f in havings:
                if f is not None:
                    for func in f.fields:
                        if func.val is not None:
                            havings_str += (
                                ast_to_sql(
                                    rule=func.val,
                                    roots=roots,
                                    symbol_table=symbol_table,
                                    replace_tables=replace_tables,
                                    verbose=verbose,
                                )
                                + " AND "
                            )
            havings_str = havings_str.rstrip(" AND ")

        if agg:

            if agg.group_by is not None:
                group_by_str = f"GROUP BY {replace_tables_func(str(agg.group_by))}"

            upper = len(agg.aggregate_body.statements)
            i = 0
            while i < upper:
                line = agg.aggregate_body.statements[i]
                if line is not None:
                    if isinstance(line, lark.lexer.Token):
                        name = line
                        i += 1
                        function_call = agg.aggregate_body.statements[i]

                        if isinstance(function_call, FuncCall):
                            agg_str += f"{ast_to_sql(function_call, roots, symbol_table, replace_tables, verbose)} as {name},"
                        elif isinstance(function_call, str):
                            agg_str += f"{function_call} as {name},"
                        elif isinstance(function_call, PipeBody):
                            if isinstance(function_call.body, PipedCall) or isinstance(
                                function_call.body, FuncCall
                            ):
                                agg_str += f"{ast_to_sql(function_call.body, roots, symbol_table, replace_tables, verbose)} as {name},"
                            else:
                                agg_str += f"{function_call} as {name},"

                        elif isinstance(function_call, PipedCall):
                            agg_str += f"{ast_to_sql(function_call, roots, symbol_table, replace_tables, verbose)} as {name},"
                        else:
                            raise PRQLException(
                                f"Unknown type for aggregate body {type(line)}, {str(line)}"
                            )
                    elif isinstance(line, FuncCall):
                        function_call = line
                        if function_call.func_args is not None:
                            agg_str += f"{str(function_call)} as {function_call.name}_{function_call.func_args},"
                        else:
                            agg_str += f"{str(function_call)},"
                    elif isinstance(line, PipedCall):
                        piped = line
                        # piped.func_body.parm1 = replace_variables(str(piped.parm1), symbol_table)
                        # piped.func_body.func_args = replace_variables(str(piped.func_args), symbol_table)
                        agg_str += f"{ast_to_sql(piped.func_body, roots, symbol_table, replace_tables, verbose)} as {piped.parm1}_{piped.func_body.name},"
                    elif isinstance(line, str):
                        agg_str += f"{line},"
                    elif isinstance(line, PipeBody):
                        agg_str += (
                            ast_to_sql(
                                line.body,
                                roots,
                                symbol_table=symbol_table,
                                replace_tables=replace_tables,
                                verbose=verbose,
                            )
                            + ","
                        )
                    else:
                        raise PRQLException(
                            f"Unknown type for aggregate body {type(line)}, {str(line)}"
                        )
                i += 1

            agg_str = replace_tables_func(agg_str)
            agg_str = agg_str.rstrip(",").lstrip(",")
        if take:
            limit_str = str(take)

        if filters:
            for filter in filters:
                if filter:
                    for function_call in filter.fields:
                        if function_call.val is not None:
                            filter_str += (
                                replace_tables_func(
                                    ast_to_sql(
                                        function_call.val,
                                        roots,
                                        symbol_table,
                                        replace_tables,
                                        verbose,
                                    )
                                )
                                + " AND "
                            )
            filter_str = filter_str.rstrip(" AND ")

        if wheres_from_derives:
            for d in wheres_from_derives:
                for line in d.fields:
                    derives_str += f"{replace_tables_func(ast_to_sql(line.expression, roots, symbol_table, replace_tables, verbose))} as {line.name} ,"
            derives_str = "," + derives_str.rstrip(",")

        if sort:
            order_by_str = f"ORDER BY {replace_tables_func(str(sort))}"

        if not select_str and not agg_str:
            select_str = "*"
        elif not select_str and agg_str:
            select_str = ""
        elif not select_str and derives_str:
            select_str = "*"
        elif not select_str and derives_str:
            select_str = ""
        select_str = select_str.rstrip(",").lstrip(",")

        if select_str and agg_str:
            select_str += ","

        if not filter_str:
            filter_str = "1=1"
        if verbose:
            ic(
                select_str,
                agg_str,
                derives_str,
                from_str,
                join_str,
                filter_str,
                group_by_str,
                havings_str,
                order_by_str,
                limit_str,
            )
        sql = f"SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {havings_str} {order_by_str} {limit_str} {to_str}"
        if verbose:
            print("\t" + sql)
        return sql
    elif isinstance(rule, BinaryExpression):
        left = replace_variables(
            ast_to_sql(rule.left, roots, symbol_table, replace_tables, verbose),
            symbol_table,
        )
        if rule.right:
            left += rule.operator + replace_variables(
                ast_to_sql(rule.right, roots, symbol_table, replace_tables, verbose),
                symbol_table,
            )
        if isinstance(rule, ParensExpression):
            return "(" + left + ")"
        else:
            return left
    elif isinstance(rule, Expression):
        expr = rule
        msg = ""
        upper = len(expr.statements)
        i = 0
        while i < upper:
            fields = expr.statements[i]
            if isinstance(fields, PipedCall):
                if i + 1 < upper and isinstance(expr.statements[i + 1], Token):
                    fields.func_args = expr.statements[i + 1]
                    i += 1
                    # msg += ast_to_sql(fields, roots, symbol_table, verbose)
                    if i + 1 < upper and isinstance(expr.statements[i + 1], Token):
                        fields.parm2 = expr.statements[i + 1]
                        i += 1
                    msg += ast_to_sql(
                        fields, roots, symbol_table, replace_tables, verbose
                    )
                else:
                    msg += ast_to_sql(
                        fields, roots, symbol_table, replace_tables, verbose
                    )
            else:
                msg += ast_to_sql(fields, roots, symbol_table, replace_tables, verbose)
            # else:
            #     raise PRQLException(f'Unknown type for expression {type(fields)}, {str(fields)}')
            i += 1
        return msg
    elif isinstance(rule, PipedCall):
        pipe: PipedCall = rule
        msg = ""
        if pipe.parm1 is not None:
            # Now we shift all the function arguments

            pipe.func_body.parm3 = pipe.func_body.parm2
            pipe.func_body.parm2 = pipe.func_body.parm1
            pipe.func_body.parm1 = pipe.parm1

        msg += ast_to_sql(pipe.func_body, roots, symbol_table, replace_tables, verbose)

        return msg
    elif isinstance(rule, FuncCall):
        function_call: FuncCall = rule  # type: ignore [no-redef]
        if str(function_call.name) in symbol_table:
            msg = execute_function(function_call, roots, symbol_table)
        else:
            raise PRQLException(f"Unknown function {function_call.name}")
        return msg
    elif isinstance(rule, Value):

        val = str(rule)
        if root.value_defs:
            for table in root.value_defs.fields:
                if table.name == val:
                    return (
                        "("
                        + ast_to_sql(
                            table.value_body,
                            roots,
                            symbol_table,
                            replace_tables,
                            verbose,
                        )
                        + ")"
                    )
        # TODO , should we use replace_variables here ?
        if val in symbol_table:
            replacement = symbol_table[val][0]  # type: ignore [index]
            if not isinstance(replacement, FuncDef):
                return str(replacement)

        return val
    elif isinstance(rule, Operator):
        return str(rule)
    elif isinstance(rule, Name):
        return str(rule)
    elif isinstance(rule, FilterLine):
        return ast_to_sql(rule.val, roots, symbol_table, replace_tables, verbose)
    elif isinstance(rule, DeriveBody):
        return ast_to_sql(rule.val, roots, symbol_table, replace_tables, verbose)
    else:
        raise PRQLException(f"No sql for {type(rule)}")
