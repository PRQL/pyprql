# -*- coding: utf-8 -*-
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, Union

import lark
import rich
from enforce_typing import enforce_types
from icecream import ic
from lark import Lark, Token, Transformer, ast_utils

this_module = sys.modules[__name__]
script_path = os.path.dirname(__file__)


class _Ast(ast_utils.Ast):
    pass


class _Statement(_Ast):
    @enforce_types
    def assign_field(self, clazz: Type, values: List[Any]):
        for v in values:
            if isinstance(v, clazz):
                return v


@dataclass
class Value(_Ast):
    value: str

    def __str__(self):
        return str(self.value)


@dataclass
class Name(_Ast, ast_utils.AsList):
    name: List[str]

    def __str__(self):
        return ".".join([str(x) for x in self.name])


@dataclass
class Expression(_Statement, ast_utils.AsList):
    statements: List[_Statement]

    def __str__(self):
        msg = ""
        for s in self.statements:
            msg += f"{s}"

        return msg


class _JoinType(_Ast):

    def __str__(self):
        return "JOIN"


@dataclass
class InnerJoin(_JoinType):

    def __str__(self):
        return "INNER JOIN"


@dataclass
class LeftJoin(_JoinType):

    def __str__(self):
        return "LEFT JOIN"


@dataclass
class RightJoin(_JoinType):

    def __str__(self):
        return "RIGHT JOIN"


@dataclass
class OuterJoin(_JoinType):

    def __str__(self):
        return "OUTER JOIN"


@dataclass
class JoinType(_JoinType):
    join_type: _JoinType

    def __str__(self):
        if self.join_type is None:
            return "JOIN"
        else:
            return str(self.join_type)


@dataclass
class Join(_Statement):
    name: Name
    join_type: Optional[_JoinType] = None
    left_id: Optional[Name] = None  # Has to have a default argument now
    right_id: Optional[Name] = None

    def __init__(self, name: Name, join_type: Optional[_JoinType] = None, left_id: Name = None,
                 right_id: Optional[Name] = None):
        self.name = name
        self.join_type = join_type

        if isinstance(self.name, JoinType):
            temp = self.join_type
            self.join_type = self.name
            self.name = temp

        if isinstance(self.join_type, Name):
            # Now we need to shift everything , since join_type is now our left_id

            temp = left_id
            self.left_id = self.join_type
            self.right_id = temp
            self.join_type = None
        else:
            self.left_id = left_id
            self.right_id = right_id

        # self.left_id = left_id
        # self.right_id = right_id


@dataclass
class SelectField(_Statement):
    name: Name
    cast_type: Optional[Name] = None

    def __str__(self):
        if self.cast_type is not None:
            return f"CAST({self.name} as {self.cast_type})"
        return str(self.name)


@dataclass()
class SelectFields(_Statement, ast_utils.AsList):
    fields: List[SelectField]

    def __str__(self):
        return [str(x) for x in self.fields]


@dataclass()
class PipeBody(_Statement):
    body: str

    def __str__(self):
        return str(self.body)


@dataclass
class Select(_Statement):
    fields: SelectFields

    def __str__(self):
        return ",".join([str(f) for f in self.fields.fields])


@dataclass
class DeriveBody(_Statement):
    val: Union[str, Expression]

    def __str__(self):
        return str(self.val)


@dataclass
class Operator(_Statement):
    op: Token

    def __str__(self):
        return self.op.value


@dataclass
class GroupBy(_Statement, ast_utils.AsList):
    fields: List[str]

    def __str__(self):
        return ",".join([str(f) for f in self.fields])


@dataclass
class AggregateBody(_Statement, ast_utils.AsList):
    statements: List[_Statement]

    def __str__(self):
        return f"{[str(s) for s in self.statements]}"


@dataclass
class Aggregate(_Statement):
    group_by: GroupBy
    aggregate_body: Optional[AggregateBody] = None

    def __init__(self, group_by, aggregate_body=None):
        values = [group_by, aggregate_body]
        self.aggregate_body = self.assign_field(AggregateBody, values)
        self.group_by = self.assign_field(GroupBy, values)


@dataclass
class DeriveLine(_Statement):
    name: str
    expression: Expression

    def __str__(self):
        return f"{str(self.expression)}"


@dataclass
class Derive(_Statement, ast_utils.AsList):
    fields: List[DeriveLine]


class _Direction(_Statement):
    pass


@dataclass
class Direction(_Statement):
    direction: Optional[_Direction] = None

    def __str__(self):
        return str(self.direction)


@dataclass
class Ascending(_Direction):
    direction = "ASC"

    def __str__(self):
        return self.direction


@dataclass
class Descending(_Direction):
    direction = "DESC"

    def __str__(self):
        return self.direction


@dataclass
class Sort(_Statement):
    name: Name
    direction: Optional[Direction] = None

    def __str__(self):
        return (
                f'{str(self.name)} {self.direction if self.direction is not None else ""}'
        )


@dataclass
class Take(_Statement):
    qty: str
    offset: str = Optional[str]

    def __str__(self):
        sql = f"LIMIT {self.qty}"
        if (
                self.offset is not None
                and self.offset
                and isinstance(self.offset, lark.lexer.Token)
        ):
            sql += f" OFFSET {self.offset} "
        return sql


@dataclass
class Filter(_Statement, ast_utils.AsList):
    fields: List[str]
    name: str = "filter"


@dataclass
class FilterLine(_Statement):
    val: Any = None

    def __str__(self):
        return str(self.val)


@dataclass
class Pipes(_Statement, ast_utils.AsList):
    operations: List[_Statement]


@dataclass
class From(_Statement):
    name: str
    pipes: Pipes = None

    def __init__(self, name, pipes=None, join=None):
        self.name = name
        values = [pipes, join]

        self.pipes = self.assign_field(Pipes, values)
        self.join = self.assign_field(Join, values)

    def get_pipes(self):
        return self.pipes


@dataclass
class FuncArgs(_Statement, ast_utils.AsList):
    fields: List[str] = None

    def __str__(self):
        return ",".join([str(x) for x in self.fields])


@dataclass
class FuncBody(_Statement, ast_utils.AsList):
    fields: List[str]


@dataclass
class FuncDef(_Statement):
    name: Name
    func_args: FuncArgs
    func_body: FuncBody = None

    def __init__(self, name, func_args=None, func_body=None):
        self.name = name
        values = [func_args, func_body]
        self.func_args = self.assign_field(FuncArgs, values)
        self.func_body = self.assign_field(FuncBody, values)


@dataclass
class FuncCall(_Statement):
    name: Name = None
    parm1: Any = None
    parm2: Any = None
    parm3: Any = None


@dataclass
class PipedCall(_Statement):
    parm1: Name
    func_body: FuncCall


@dataclass
class ValueDef(_Statement):
    name: Name
    value_body: From


@dataclass
class ValueDefs(_Statement, ast_utils.AsList):
    fields: List[ValueDef]


@dataclass
class FuncDefs(_Statement, ast_utils.AsList):
    fields: List[FuncDef]


@dataclass
class WithDef(_Statement):
    name: Name
    _from: From


# The top level definition that holds all other definitions
@dataclass
class Root(_Statement):
    with_def: WithDef = None
    _from: From = None
    value_defs: ValueDefs = None
    func_defs: FuncDefs = None

    def __init__(self, with_def=None, _from=None, value_def=None, func_def=None):
        values = [with_def, _from, value_def, func_def]
        self.with_def = self.assign_field(WithDef, values)
        self._from = self.assign_field(From, values)
        self.value_defs = self.assign_field(ValueDefs, values)
        self.func_defs = self.assign_field(FuncDefs, values)

    def get_from(self):
        return self._from

    def get_cte(self):
        return self.with_def


# This is a helper class, its not actually parsed
@dataclass
class NameValuePair(_Ast):
    name: str
    value: str

    def __str__(self):
        return f"({self.value})"


class ToAst(Transformer):
    def STRING(self, s):
        # Remove quotation marks
        return s  # s[1:-1]

    def SSTRING(self, s):
        return s[2:-1]

    def ESCAPED_STRING(self, s):
        return s  # s.replace('\\"', '"').replace("\\'", "'")

    def NEWLINE(self, s):
        return s


@enforce_types
def read_file(filename: str, path: str = script_path) -> str:
    with open(path + filename, "r") as f:
        x = f.read()
    return x


@enforce_types
def get_func_str(func: Optional[str]) -> str:
    if func == "average":
        return "avg"
    return func


@enforce_types
def parse(_text: str) -> Root:
    text = _text + "\n"
    parser = Lark(
            read_file("/../resources/prql.lark"),
            start="root",
            parser="lalr",
            transformer=ToAst(),
    )
    tree = parser.parse(text)
    transformer = ast_utils.create_transformer(this_module, ToAst())
    return transformer.transform(tree)


@enforce_types
def to_sql(prql: str, verbose: bool = False) -> str:
    ast = parse(prql)
    stdlib = parse(read_file("/../resources/stdlib.prql"))
    return (
            ast_to_sql(ast._from, [ast, stdlib], verbose=verbose).replace("   ", " ").replace("  ", " ")
    )


@enforce_types
def pretty_print(root: Root) -> None:
    rich.print(root)


@enforce_types
def get_operation(
        ops: List[_Statement],
        class_type: Type[_Statement],
        last_match: bool = False,
        return_all: bool = False,
        before: Type = None,
        after: Type = None,
) -> Union[List, _Statement]:
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
def alias(s: str, n: int = 1):
    return s + "_" + s[0:n]


def replace_all_tables_standalone(
        from_long: str, from_short: str, join_long: List, join_short: List, s: str
):
    s = s.replace(f"{from_long}.", f"{from_short}.")
    if join_long and len(join_long) > 0:
        for i in range(len(join_long)):
            s = s.replace(f"{join_long[i]}.", f"{join_short[i]}.")
        # s = s.replace(f'{join_long}.', f'{join_short}.')
    return s


def wrap_replace_all_tables(from_long, from_short, join_long, join_short):
    def inner(x):
        return replace_all_tables_standalone(
                from_long, from_short, join_long, join_short, x
        )

    return inner


def replace_tables_standalone(from_long, from_short, join_long, join_short, s) -> str:
    s = s.replace(f"{from_long}.", f"{from_short}.")
    if join_long:
        s = s.replace(f"{join_long}.", f"{join_short}.")
    return s


def wrap_replace_tables(from_long, from_short, join_long, join_short):
    def inner(x):
        return replace_tables_standalone(
                from_long, from_short, join_long, join_short, x
        )

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
        if root._from.get_pipes():
            derives = get_operation(
                    root._from.get_pipes().operations, Derive, return_all=True
            )
            for d in derives:
                for line in d.fields:
                    table[str(line.name)].append(
                            NameValuePair(str(line.name), line.expression)
                    )
    return table


class PRQLException(Exception):
    pass


@enforce_types
def replace_variables(_param: Any, symbol_table: Dict[str, List[_Ast]]) -> str:
    param: str = str(_param)
    if param in symbol_table:
        if not symbol_table[param]:
            return _param
        if isinstance(symbol_table[param][0], NameValuePair):
            if isinstance(symbol_table[param][0].value, Expression):
                msg = ""
                exp: Expression = symbol_table[param][0].value
                for s in exp.statements:
                    msg += str(replace_variables(str(s), symbol_table))

                return msg
            if isinstance(symbol_table[param][0].value, DeriveBody):
                msg = ""
                exp: Expression = symbol_table[param][0].value.val
                for s in exp.statements:
                    msg += str(replace_variables(str(s), symbol_table))

                return msg
            else:
                return symbol_table[param][0].value
        else:
            return str(symbol_table[param][0])
    else:
        return _param


@enforce_types
def execute_function(
        f: FuncCall, roots: Union[Root, List], symbol_table: Dict[str, List[_Ast]]
) -> str:
    msg = ""
    name = str(f.name)
    func_defs: List[FuncDef] = symbol_table[name]
    func_def: FuncDef = None
    # Execute line by line the function
    if len(func_defs) == 1:
        func_def = func_defs[0]
    else:
        # Now we match the parameter count against a list of functions and take the first one
        func_call_parm_count = get_function_parm_count(f)

        for defintion in func_defs:
            if get_function_parm_count(defintion) == func_call_parm_count:
                func_def = defintion
                break

    try:
        if func_def:
            for line in func_def.func_body.fields:
                if isinstance(line, PipeBody):
                    line = line.body
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
                        for i in range(0, len(func_def.func_args.fields)):
                            n = str(func_def.func_args.fields[i])
                            args[n] = vals[i]
                        msg = line.format(**args)
                    else:
                        msg = line
    except Exception as e:
        msg = repr(e)
        if "KeyError" in msg:
            msg = f"Function {name} had an error executing , full error: {msg}"
        raise PRQLException(msg)
    return msg


@enforce_types
def is_empty(a: Any) -> bool:
    if a is not None and a != "None" and a != "none" and a != "":
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
            parm_count = len(f.func_args.fields)
    return parm_count


@enforce_types
def safe_to_sql(
        rule: Any,
        roots: Union[
            Root, List
        ],  # a Root or a list of roots, all share the same symbol table
        symbol_table: Dict[str, List[_Ast]] = None,
        verbose: bool = False,
):
    if isinstance(rule, str):
        return rule
    elif isinstance(rule, Token) or isinstance(rule, Name):
        return str(rule)
    elif isinstance(rule, _Ast):
        return ast_to_sql(rule, roots, symbol_table, verbose)


@enforce_types
def ast_to_sql(
        rule: Union[_Ast, Token],
        roots: Union[
            Root, List
        ],  # a Root or a list of roots, all share the same symbol table
        symbol_table: Dict[str, List[_Ast]] = None,
        verbose: bool = True,
):
    if isinstance(roots, Root):
        root = roots
    else:
        root = roots[0]

    if not symbol_table:
        symbol_table = build_symbol_table([roots] if isinstance(roots, Root) else roots)
        if verbose:
            ic(symbol_table)

    if isinstance(rule, Token):
        return str(rule)

    if isinstance(rule, From):
        # The SQL template is in the form
        # SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {order_by} {limit_str}'

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
        ops = _from.get_pipes()
        joins = get_operation(ops.operations, Join, return_all=True)
        agg = get_operation(ops.operations, Aggregate)
        take = get_operation(ops.operations, Take, last_match=True)
        sort = get_operation(ops.operations, Sort, last_match=True)

        filters = get_operation(
                ops.operations, Filter, return_all=True, before=Aggregate
        )
        wheres_from_derives = get_operation(
                ops.operations, Derive, return_all=True, before=Aggregate
        )
        havings = get_operation(
                ops.operations, Filter, return_all=True, after=Aggregate
        )
        selects = get_operation(ops.operations, Select, return_all=True)

        from_long = str(_from.name)
        from_short = alias(from_long)

        from_str = f"`{from_long}`" + " " + from_short
        all_join_longs = []
        all_join_shorts = []
        for join in joins:
            if join:
                join_long = str(join.name)
                join_short = alias(join_long)

                all_join_shorts.append(join_short)
                all_join_longs.append(join_long)

        replace_all_tables = wrap_replace_all_tables(
                from_long, from_short, all_join_longs, all_join_shorts
        )

        if verbose:
            rich.print(roots)

        for join in joins:
            if join:
                join_long = str(join.name)
                join_short = alias(join_long)

                left_id = replace_all_tables(str(join.left_id))
                right_id = replace_all_tables(str(join.right_id))
                if right_id is None or right_id == "None":
                    right_id = left_id

                # left_id = left_id.replace(from_long, '').replace(from_short, '')

                if left_id.find(".") == -1:
                    left_side = str(from_short + "." + left_id).replace(
                            from_short + "." + from_short + ".", from_short + "."
                    )
                else:
                    left_side = str(left_id).replace(
                            from_short + "." + from_short + ".", from_short + "."
                    )

                # right_id = right_id.replace(from_long, '').replace(from_short, '')
                if right_id.find(".") == -1:
                    right_side = replace_all_tables(
                            str(join_long + "." + right_id).replace(
                                    join_short + "." + join_short + ".", join_short + "."
                            )
                    )
                else:
                    right_side = replace_all_tables(
                            str(right_id).replace(
                                    join_short + "." + join_short + ".", join_short + "."
                            )
                    )

                join_type = "JOIN"
                if join.join_type is not None:
                    join_type = str(join.join_type)
                join_str += replace_all_tables(
                        f"{join_type} {join.name} {join_short} ON {left_side} = {right_side} "
                )

        if selects:
            for select in selects:
                select_str += replace_all_tables(str(select))

        if agg:

            if agg.group_by is not None:
                group_by_str = f"GROUP BY {replace_all_tables(str(agg.group_by))}"

            if havings is not None and len(havings) > 0:
                havings_str = "HAVING "
                for filter in havings:
                    if filter:
                        for func_call in filter.fields:
                            if func_call.val is not None:
                                havings_str += (
                                        ast_to_sql(
                                                func_call.val, roots, symbol_table, verbose
                                        )
                                        + " AND "
                                )
                havings_str = havings_str.rstrip(" AND ")

            upper = len(agg.aggregate_body.statements)
            i = 0
            while i < upper:
                line = agg.aggregate_body.statements[i]
                if line is not None:
                    if isinstance(line, lark.lexer.Token):
                        name = line
                        i += 1
                        func_call = agg.aggregate_body.statements[i]

                        if isinstance(func_call, FuncCall):
                            agg_str += f"{ast_to_sql(func_call, roots, symbol_table, verbose)} as {name},"
                        elif isinstance(func_call, str):
                            agg_str += f"{func_call} as {name},"
                        elif isinstance(func_call, PipeBody):
                            if isinstance(func_call.body, PipedCall) or isinstance(
                                    func_call.body, FuncCall
                            ):
                                agg_str += f"{ast_to_sql(func_call.body, roots, symbol_table, verbose)} as {name},"
                            else:
                                agg_str += f"{func_call} as {name},"

                        elif isinstance(func_call, PipedCall):
                            agg_str += f"{ast_to_sql(func_call, roots, symbol_table, verbose)} as {name},"
                        else:
                            raise PRQLException(
                                    f"Unknown type for aggregate body {type(line)}, {str(line)}"
                            )
                    elif isinstance(line, FuncCall):
                        func_call = line
                        if func_call.func_args is not None:
                            agg_str += f"{str(func_call)} as {func_call.name}_{func_call.func_args},"
                        else:
                            agg_str += f"{str(func_call)},"
                    elif isinstance(line, PipedCall):
                        piped = line
                        # piped.func_body.parm1 = replace_variables(str(piped.parm1), symbol_table)
                        # piped.func_body.func_args = replace_variables(str(piped.func_args), symbol_table)
                        agg_str += f"{ast_to_sql(piped.func_body, roots, symbol_table, verbose)} as {piped.parm1}_{piped.func_body.name},"
                    elif isinstance(line, str):
                        agg_str += f"{line},"
                    elif isinstance(line, PipeBody):
                        agg_str += (
                                ast_to_sql(
                                        line.body,
                                        roots,
                                        symbol_table=symbol_table,
                                        verbose=verbose,
                                )
                                + ","
                        )
                    else:
                        raise PRQLException(
                                f"Unknown type for aggregate body {type(line)}, {str(line)}"
                        )
                i += 1

            agg_str = replace_all_tables(agg_str)
            agg_str = agg_str.rstrip(",").lstrip(",")
        if take:
            limit_str = str(take)

        if filters:
            for filter in filters:
                if filter:
                    for func_call in filter.fields:
                        if func_call.val is not None:
                            filter_str += (
                                    replace_all_tables(
                                            ast_to_sql(
                                                    func_call.val, roots, symbol_table, verbose
                                            )
                                    )
                                    + " AND "
                            )
            filter_str = filter_str.rstrip(" AND ")

        if wheres_from_derives:
            for d in wheres_from_derives:
                for line in d.fields:
                    derives_str += f"{replace_all_tables(ast_to_sql(line.expression, roots, symbol_table, verbose))} as {line.name} ,"
            derives_str = "," + derives_str.rstrip(",")

        if sort:
            order_by_str = f"ORDER BY {sort}"

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
                    msg += ast_to_sql(fields, roots, symbol_table, verbose)
                else:
                    msg += ast_to_sql(fields, roots, symbol_table, verbose)
            else:
                msg += ast_to_sql(fields, roots, symbol_table, verbose)
            # else:
            #     raise PRQLException(f'Unknown type for expression {type(fields)}, {str(fields)}')
            i += 1
        return msg
    elif isinstance(rule, PipedCall):
        pipe: PipedCall = rule
        msg = ""
        if pipe.parm1 is not None:
            # Now we have to shift all the function all arguments , annoying

            pipe.func_body.parm3 = pipe.func_body.parm2
            pipe.func_body.parm2 = pipe.func_body.parm1
            pipe.func_body.parm1 = pipe.parm1

        msg += ast_to_sql(pipe.func_body, roots, symbol_table, verbose)

        return msg
    elif isinstance(rule, FuncCall):
        func_call: FuncCall = rule
        if str(func_call.name) in symbol_table:
            msg = execute_function(func_call, roots, symbol_table)
        else:
            raise PRQLException(f"Unknown function {func_call.name}")
        return msg
    elif isinstance(rule, Value):

        val = str(rule)
        if root.value_defs:
            for table in root.value_defs.fields:
                if table.name == val:
                    return (
                            "("
                            + ast_to_sql(table.value_body, roots, symbol_table, verbose)
                            + ")"
                    )
        if val in symbol_table:
            replacement = symbol_table[val][0]
            if not isinstance(replacement, FuncDef):
                return str(replacement)

        return val
    elif isinstance(rule, Operator):
        return str(rule)
    elif isinstance(rule, Name):
        return str(rule)
    elif isinstance(rule, FilterLine):
        return ast_to_sql(rule.val, roots, symbol_table, verbose)
    elif isinstance(rule, DeriveBody):
        return ast_to_sql(rule.val, roots, symbol_table, verbose)
    else:
        raise Exception(f"No sql for {type(rule)}")
