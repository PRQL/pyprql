# -*- coding: utf-8 -*-
"""The Python implementation of PRQL.

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
"""
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Type, Union

# For Python 3.7
try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal  # type: ignore

import lark
import rich
from enforce_typing import enforce_types
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
    pass


@dataclass
class Value(_Ast):
    value: str

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Name(_Ast, ast_utils.AsList):
    name: List[str]

    def __str__(self) -> str:
        return ".".join([str(x) for x in self.name])


@dataclass
class Expression(_Ast, ast_utils.AsList):
    statements: List[_Ast]

    def __str__(self) -> str:
        msg = ""
        for s in self.statements:
            msg += f"{s}"

        return msg


@dataclass
class BinaryExpression(_Ast):
    left: _Ast
    right: Optional[_Ast] = None
    operator: Optional[str] = None  # This will be overridden

    def __str__(self) -> str:
        if self.right is not None:
            return f"{self.left} {self.operator} {self.right}"
        else:
            return f"{self.left}"


@dataclass
class ExpressionLt(BinaryExpression):
    operator: str = "<"


@dataclass
class ExpressionAdd(BinaryExpression):
    operator: str = "+"


@dataclass
class ExpressionSub(BinaryExpression):
    operator: str = "-"


@dataclass
class ExpressionMul(BinaryExpression):
    operator: str = "*"


# Unfortunately we have to recreate the expression based on the parsing when creating the sql.
# So we need to know if the original had parentheses or not, they will all inherit from this class.
class ParensExpression(BinaryExpression):
    pass


@dataclass
class ExpressionAddParens(ParensExpression):
    operator: str = "+"


@dataclass
class ExpressionSubParens(ParensExpression):
    operator: str = "-"


@dataclass
class ExpressionMulParens(ParensExpression):
    operator: str = "*"


@dataclass
class ExpressionDivParens(ParensExpression):
    operator: str = "/"


@dataclass
class ExpressionDiv(BinaryExpression):
    operator: str = "/"


@dataclass
class ExpressionGt(BinaryExpression):
    operator: str = ">"


@dataclass
class ExpressionEq(BinaryExpression):
    operator: str = "="


@dataclass
class _JoinType(_Ast):
    def __str__(self) -> str:
        return "JOIN"


@dataclass
class InnerJoin(_JoinType):
    def __str__(self) -> Literal["INNER JOIN"]:
        return "INNER JOIN"


@dataclass
class LeftJoin(_JoinType):
    def __str__(self) -> Literal["LEFT JOIN"]:
        return "LEFT JOIN"


@dataclass
class RightJoin(_JoinType):
    def __str__(self) -> Literal["RIGHT JOIN"]:
        return "RIGHT JOIN"


@dataclass
class OuterJoin(_JoinType):
    def __str__(self) -> Literal["OUTER JOIN"]:
        return "OUTER JOIN"


@dataclass
class JoinType(_JoinType):
    join_type: _JoinType

    def __str__(self) -> str:
        if self.join_type is None:
            return "JOIN"
        else:
            return str(self.join_type)


@dataclass
class Alias(_Ast):
    name: str

    def __str__(self) -> str:
        return self.name


# These extra join_types here are to allow for those to be in any position in the parsing rule
@dataclass
class Join(_Ast):
    join_type: Optional[_JoinType] = None
    alias: Optional[Alias] = None
    name: Optional[Name] = None
    join_type_2: Optional[_JoinType] = None
    left_id: Optional[Name] = None
    right_id: Optional[Name] = None
    join_type_3: Optional[_JoinType] = None

    def get_join_type(self) -> Optional[_JoinType]:
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
    pass


@dataclass
class Csv(_FileType):
    def __str__(self) -> Literal["csv"]:
        return "csv"


@dataclass
class FileType(_FileType):
    file_type: _FileType

    def __str__(self) -> str:
        return str(self.file_type)


@dataclass
class To(_Ast):
    file_type: _FileType
    name: Name

    def get_file_type(self) -> _FileType:
        return self.file_type


@dataclass
class SelectField(_Ast):
    name: Name
    cast_type: Optional[Name] = None

    def __str__(self) -> str:
        if self.cast_type is not None:
            return f"CAST({self.name} as {self.cast_type})"
        return str(self.name)


@dataclass()
class SelectFields(_Ast, ast_utils.AsList):
    fields: List[SelectField]

    def __str__(self) -> str:
        return ",".join([str(x) for x in self.fields])


@dataclass()
class SortField(_Ast):
    name: Name

    def __str__(self) -> str:
        return str(self.name)


@dataclass()
class SortFields(_Ast, ast_utils.AsList):
    fields: List[SortField]

    def __str__(self) -> str:
        return ",".join([str(x) for x in self.fields])


@dataclass()
class PipeBody(_Ast):
    body: str

    def __str__(self) -> str:
        return str(self.body)


@dataclass
class Select(_Ast):
    fields: SelectFields

    def __str__(self) -> str:
        return ",".join([str(f) for f in self.fields.fields])


@dataclass
class DeriveBody(_Ast):
    val: Union[str, _Ast]

    def __str__(self) -> str:
        return str(self.val)


@dataclass
class Operator(_Ast):
    op: Token

    def __str__(self) -> str:
        return self.op.value


@dataclass
class GroupBy(_Ast, ast_utils.AsList):
    fields: List[str]

    def __str__(self) -> str:
        return ",".join([str(f) for f in self.fields])


@dataclass
class AggregateBody(_Ast, ast_utils.AsList):
    statements: List[_Ast]

    def __str__(self) -> str:
        return f"{[str(s) for s in self.statements]}"


@dataclass
class Aggregate(_Ast):
    group_by: Optional[GroupBy] = None
    aggregate_body: Optional[AggregateBody] = None


@dataclass
class DeriveLine(_Ast):
    name: str
    expression: Expression

    def __str__(self) -> str:
        return str(self.expression)


@dataclass
class Derive(_Ast, ast_utils.AsList):
    fields: List[DeriveLine]


class _Direction(_Ast):
    pass


@dataclass
class Direction(_Ast):
    direction: Optional[_Direction] = None

    def __str__(self) -> str:
        return str(self.direction)


@dataclass
class Ascending(_Direction):
    direction = "ASC"

    def __str__(self) -> str:
        return self.direction


@dataclass
class Descending(_Direction):
    direction = "DESC"

    def __str__(self) -> str:
        return self.direction


@dataclass
class Sort(_Ast):
    direction1: Optional[Direction] = None
    fields: Optional[SortFields] = None
    direction2: Optional[Direction] = None

    def get_direction(self) -> Optional[Direction]:
        ret = None
        if self.direction1 is not None:
            ret = self.direction1
        elif self.direction2 is not None:
            ret = self.direction2
        return ret

    def __str__(self) -> str:
        direction = self.get_direction()
        ret = f"{str(self.fields)}"
        if direction is not None:
            ret = f"{ret} {str(direction)}"
        return ret


@dataclass
class Take(_Ast):
    qty: str
    offset: Optional[str] = None

    def __str__(self) -> str:
        sql = f"LIMIT {self.qty}"
        if (
            self.offset is not None
            and self.offset
            and isinstance(self.offset, lark.lexer.Token)
        ):
            sql += f" OFFSET {self.offset} "
        return sql


@dataclass
class Filter(_Ast, ast_utils.AsList):
    fields: List[str]
    name: str = "filter"


@dataclass
class FilterLine(_Ast):
    val: Any = None

    def __str__(self) -> str:
        return str(self.val)


@dataclass
class Pipes(_Ast, ast_utils.AsList):
    operations: List[_Ast]


@dataclass
class From(_Ast):
    alias: Optional[Alias] = None
    name: Optional[Name] = None
    pipes: Optional[Pipes] = None


@dataclass
class FuncArgs(_Ast, ast_utils.AsList):
    fields: Optional[List] = None

    def __str__(self) -> str:
        return ",".join([str(x) for x in self.fields])


@dataclass
class FuncBody(_Ast, ast_utils.AsList):
    fields: List[str]


@dataclass
class FuncDef(_Ast):
    name: Name
    func_args: Optional[FuncArgs] = None
    func_body: Optional[FuncBody] = None


@dataclass
class FuncCall(_Ast):
    name: Optional[Name] = None
    parm1: Any = None
    parm2: Any = None
    parm3: Any = None


@dataclass
class PipedCall(_Ast):
    parm1: Name
    func_body: FuncCall


@dataclass
class ValueDef(_Ast):
    name: Name
    value_body: From


@dataclass
class ValueDefs(_Ast, ast_utils.AsList):
    fields: List[ValueDef]


@dataclass
class FuncDefs(_Ast, ast_utils.AsList):
    fields: List[FuncDef]


@dataclass
class WithDef(_Ast):
    name: Name
    _from: From


# The top level definition that holds all other definitions
class Root(_Ast):
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
        return self._from

    def get_cte(self) -> Optional[WithDef]:
        return self.with_def

    @enforce_types
    def assign_field(self, clazz: Type, values: List[Any]) -> Optional[Type]:
        for v in values:
            if isinstance(v, clazz):
                return v
        # Explicit statement of prior implicit behaviour to silence MyPy
        return None


# This is a helper class, its not actually parsed
@dataclass
class NameValuePair(_Ast):
    name: str
    value: _Ast

    def __str__(self) -> str:
        return f"{self.value}"


class ToAst(Transformer):
    def STRING(self, s: str) -> str:
        # Remove quotation marks
        return s  # s[1:-1]

    def SSTRING(self, s: str) -> str:
        return s[2:-1]

    def ESCAPED_STRING(self, s: str) -> str:
        return s  # s.replace('\\"', '"').replace("\\'", "'")

    def NEWLINE(self, s: str) -> str:
        return s


@enforce_types
def read_file(filename: str, path: str = script_path) -> str:
    with open(path + os.sep + filename, "r") as f:
        x = f.read()
    return x


@enforce_types
def parse(_text: str, verbose: bool = False) -> Root:
    global GLOBAL_PARSER
    global GLOBAL_TRANSFORMER
    text = _text + "\n"
    if GLOBAL_PARSER is None:
        GLOBAL_PARSER = Lark(
            read_file("prql.lark"),
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


@enforce_types
def to_sql(prql: str, verbose: bool = False) -> str:
    global STDLIB_AST
    ast = parse(prql, verbose)
    if verbose:
        rich.print(ast.get_from())
    if STDLIB_AST is None:
        STDLIB_AST = parse(read_file("stdlib.prql"))
    return (
        ast_to_sql(ast.get_from(), [ast, STDLIB_AST], verbose=verbose)
        .replace("   ", " ")
        .replace("  ", " ")
    )


@enforce_types
def pretty_print(root: Root) -> None:
    rich.print(root)


@enforce_types
def get_operation(
    ops: List[_Ast],
    class_type: Type[_Ast],
    last_match: bool = False,
    return_all: bool = False,
    before: Type = None,
    after: Type = None,
) -> Union[List, _Ast]:
    ops_list = ops
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


@enforce_types
def _generate_alias(s: str, n: int = 1) -> str:
    return s + "_" + s[0:n]


@enforce_types
def replace_all_tables(
    from_long: str, from_short: str, join_long: List[str], join_short: List[str], s: str
) -> str:
    s = s.replace(f"{from_long}.", f"{from_short}.")
    if join_long and len(join_long) > 0:
        for i in range(len(join_long)):
            s = s.replace(f"{join_long[i]}.", f"{join_short[i]}.")
    return s


@enforce_types
def wrap_replace_all_tables(
    from_long: str, from_short: str, join_long: List[str], join_short: List[str]
) -> Callable[[str], str]:
    def inner(x: str) -> str:
        return replace_all_tables(from_long, from_short, join_long, join_short, x)

    return inner


@enforce_types
def build_symbol_table(roots: List[Root]) -> Dict[str, List[_Ast]]:
    table = defaultdict(list)
    for _root in roots:
        root: Root = _root
        for n in root.value_defs.fields:
            table[str(n.name)].append(n)
        for n in root.func_defs.fields:
            table[str(n.name)].append(n)
        if root.get_from().pipes:
            derives = get_operation(
                root.get_from().pipes.operations, Derive, return_all=True
            )
            for d in derives:
                for line in d.fields:
                    table[str(line.name)].append(
                        NameValuePair(str(line.name), line.expression)
                    )
    return table


class PRQLException(Exception):
    pass


def _replace_variables(ast: _Ast, symbol_table: Dict[str, List[_Ast]]) -> str:
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


@enforce_types
def replace_variables(_param: Any, symbol_table: Dict[str, List[_Ast]]) -> str:
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


@enforce_types
def execute_function(
    f: FuncCall,
    roots: Union[Root, List],
    symbol_table: Dict[str, List[_Ast]],
) -> str:
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


@enforce_types
def is_empty(a: Any) -> bool:
    if a is not None and a:
        return False
    return True


@enforce_types
def get_function_parm_count(f: Union[FuncCall, FuncDef]) -> int:
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


@enforce_types
def safe_to_sql(
    rule: Any,
    roots: Union[Root, List],
    symbol_table: Optional[Dict] = None,  # Dict[str, List[_Ast]]
    verbose: bool = False,
) -> Optional[str]:
    # Return must be Optional[str] as no else clause is provided.
    # In python, this makes the check non-exhaustive, so the implicit None
    # return is a possibility.
    if isinstance(rule, str):
        return rule
    elif isinstance(rule, Token) or isinstance(rule, Name):
        return str(rule)
    elif isinstance(rule, _Ast):
        return ast_to_sql(rule, roots, symbol_table, None, verbose)
    # I've added the else clause explicitly to quiet mypy.
    # This is just an explicit statement of previous behaviour.
    else:
        return None


@enforce_types
def safe_get_alias(join: Union[Join, From], join_long: str) -> str:
    if join.alias is not None:
        join_short = str(join.alias)
    else:
        join_short = _generate_alias(join_long)
    return join_short


def build_replace_tables(root: Root) -> Callable:
    all_join_longs = []
    all_join_shorts = []
    _from = root.get_from()
    from_long = str(_from.name)
    from_short = safe_get_alias(_from, from_long)
    joins: List[Join] = get_operation(_from.pipes.operations, Join, return_all=True)

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


@enforce_types
def ast_to_sql(
    rule: Union[_Ast, Token],
    roots: Union[Root, List],
    symbol_table: Optional[Dict] = None,  # Optional[Dict[str, List[_Ast]]]
    replace_tables: Optional[Callable] = None,
    verbose: bool = True,
) -> str:
    # Renaming it here silences the static analysis warnings below for replace_tables being None
    replace_tables_func: Callable = replace_tables  # type: ignore[assignment]

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
        # The SQL template is in the form
        # sql = f"SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {havings_str} {order_by_str} {limit_str}"
        # We will be creating these strings to form the final SQL,
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
        ###

        _from = rule
        from_long = ""
        from_short = ""
        ops = _from.pipes
        joins: List[Join] = get_operation(ops.operations, Join, return_all=True)
        agg: Aggregate = get_operation(ops.operations, Aggregate)
        take: Take = get_operation(ops.operations, Take, last_match=True)
        sort: Sort = get_operation(ops.operations, Sort)

        filters = get_operation(
            ops.operations, Filter, return_all=True, before=Aggregate
        )
        wheres_from_derives = get_operation(ops.operations, Derive, return_all=True)
        havings = get_operation(
            ops.operations, Filter, return_all=True, after=Aggregate
        )
        selects = get_operation(ops.operations, Select, return_all=True)

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

        if havings:
            havings_str = "HAVING "
            for filter in havings:
                if filter:
                    for func in filter.fields:
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
        sql = f"SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {havings_str} {order_by_str} {limit_str}"
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
