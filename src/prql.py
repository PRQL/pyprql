import os
import sys
from dataclasses import dataclass
from math import ceil
from typing import List, Union, Type, Any

import rich
from enforce_typing import enforce_types
from icecream import ic
from lark import Lark, ast_utils, Transformer, Token
from lark.tree import Tree

this_module = sys.modules[__name__]
script_path = os.path.dirname(__file__)


class _Ast(ast_utils.Ast):
    pass


@enforce_types
def get_leaf(start, name):
    assert (isinstance(start, Start))
    start.value_defs


class _Statement(_Ast):

    @enforce_types
    def replace_variables(self, s, start):
        for idx, v in enumerate(start.value_defs.fields):
            if str(v.name) == str(s):
                if isinstance(v, ValueDef):
                    return str(v.value_body)
            # print(f'f-->{v}')
        # print('here')

        # print(f'replacing {type(start)}')

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
        msg = ''
        for s in self.statements:
            if isinstance(s, Tree):
                msg += tree_to_str(s).replace("\n", ",")
            else:
                msg += f'{s} '  # str(s)

        return msg


@dataclass
class PipedCall(_Statement):
    parm1: Name
    func_body: Tree


@dataclass
class Join(_Statement):
    name: Name
    left_id: Name
    right_id: Name = None

    def __str__(self):
        return f"join: {self.name} on {self.left_id} {' = ' + self.right_id.name if self.right_id else ''}"


@dataclass()
class SelectFields(_Statement, ast_utils.AsList):
    fields: List[Name]

    def __str__(self):
        return [str(x) for x in self.fields]


@dataclass
class Select(_Statement):
    fields: SelectFields

    def __str__(self):
        return ",".join([str(f) for f in self.fields.fields])


@dataclass
class DeriveLine(_Statement):
    name: str
    expression: Expression


@dataclass
class Eq(_Statement):
    lhs: Expression
    rhs: Expression = None

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} = {self.rhs}"


@dataclass
class GroupBy(_Statement, ast_utils.AsList):
    fields: List[str]

    def __str__(self):
        return ",".join([str(f) for f in self.fields])


@dataclass
class NamePair(_Statement):
    name1: str = "count"
    name2: str = "all"

    def __str__(self):
        return f'{self.name1} {self.name2}'


@dataclass
class AggregateBody(_Statement, ast_utils.AsList):
    statements: List[NamePair]

    def __str__(self):
        return f'{[str(s) for s in self.statements]}'


@dataclass
class Aggregate(_Statement):
    group_by: GroupBy
    aggregate_body: AggregateBody = None

    def __init__(self, group_by, aggregate_body=None):
        self.group_by = group_by
        self.aggregate_body = aggregate_body
        if self.aggregate_body is None:
            self.aggregate_body = self.group_by
            self.group_by = None

    def __str__(self):
        return f'aggregate: \n\t\taggregates: {self.aggregate_body}\n\t\tgroup_by: {self.group_by}'


@dataclass
class Derive(_Statement, ast_utils.AsList):
    fields: List[DeriveLine]

    def __str__(self):
        ret = 'derive:'
        for f in self.fields:
            ret += '\n\t\t' + str(f)
        return ret


@dataclass
class DeriveLine(_Statement):
    name: str
    expression: Expression

    def __str__(self):
        return f'{self.name}={str(self.expression)}'


@dataclass
class Sort(_Statement):
    name: Name

    def __str__(self):
        return f'sort: {str(self.name)}'


@dataclass
class Take(_Statement):
    qty: str

    def __str__(self):
        return f'take: {self.qty}'


@dataclass
class Filter(_Statement, ast_utils.AsList):
    fields: List[str]
    name: str = "filter"

    def to_sql(self):
        msg = ''
        for idx, f in enumerate(self.fields):
            msg += f'\n\t\t{tree_to_str(f)}'
        return msg.replace("\n", "").replace("\r", "").replace("\t", "")

    def __str__(self):
        msg = 'filter:'
        for idx, f in enumerate(self.fields):
            msg += f'\n\t\t{tree_to_str(f)}'
        return msg


@dataclass
class Pipes(_Statement, ast_utils.AsList):
    operations: List[_Statement]


@dataclass
class From(_Statement):
    name: str
    pipes: Pipes = None
    join: Join = None

    def __init__(self, name, pipes=None, join=None):
        self.name = name
        values = [pipes, join]

        self.pipes = self.assign_field(Pipes, values)
        self.join = self.assign_field(Join, values)

    def get_pipes(self):
        return self.pipes

    def get_join(self):
        return self.join

    def __str__(self):

        ret = ''
        ret += f'from {self.name}\n'
        join = self.get_join()
        if join is not None:
            ret += f'\t{join}\n'
        for op in self.get_pipes().operations:
            ret += f'\t{str(op)}\n'
        return ret


@dataclass
class FuncArgs(_Statement, ast_utils.AsList):
    fields: List[str] = None

    def __str__(self):
        return ",".join([str(x) for x in {self.fields}])


@dataclass
class FuncDef(_Statement):
    name: Name
    func_args: FuncArgs


@dataclass
class ValueDefs(_Statement, ast_utils.AsList):
    fields: List[str]


@dataclass
class ValueDef(_Statement):
    name: Name
    value_body: From


@dataclass
class FuncBody(_Statement, ast_utils.AsList):
    fields: List[str]


@dataclass
class WithDef(_Statement):
    name: Name
    _from: From

    def __str__(self):
        return f'with {self.name} from {self._from.name}:\n\t{self._from}'


@dataclass
class Start(_Statement):
    # Corresponds to start in the grammar
    with_def: WithDef = None
    _from: From = None
    value_defs: ValueDef = None
    func_def: FuncDef = None

    def __init__(self, with_def=None, _from=None, value_def=None, func_def=None):
        values = [with_def, _from, value_def, func_def]
        self.with_def = self.assign_field(WithDef, values)
        self._from = self.assign_field(From, values)
        self.value_defs = self.assign_field(ValueDefs, values)
        self.func_def = self.assign_field(FuncDef, values)

    def get_from(self):
        return self._from

    def get_cte(self):
        return self.with_def


class ToAst(Transformer):

    def STRING(self, s):
        # Remove quotation marks
        return s[1:-1]

    def FSTRING(self, s):
        return s[2:-1]

    def ESCAPED_STRING(self, s):
        return s[1:-1].replace('\\"', '"').replace("\\'", "'")

    def NEWLINE(self, s):
        return s


@enforce_types
def read_file(filename: str, path: str = script_path) -> str:
    with open(path + filename, "r") as f:
        x = f.read()
    return x


@enforce_types
def get_op_str(op: str) -> str:
    if op == 'gt':
        return '>'
    elif op == 'lt':
        return '<'
    elif op == 'eq':
        return '='
    elif op == 'neq':
        return '!='
    elif op == 'gte':
        return '>='
    elif op == 'sum':
        return '+'
    elif op == 'diff':
        return '-'
    elif op == 'product':
        return '*'
    elif op == 'division':
        return '/'
    elif op == 'lte':
        return '<='
    else:
        return str(op)


@enforce_types
def parse(_text: str) -> Start:
    text = _text + '\n'
    parser = Lark(read_file('/../resources/prql.lark'), start="start", parser="lalr", transformer=ToAst())
    tree = parser.parse(text)
    transformer = ast_utils.create_transformer(this_module, ToAst())
    return transformer.transform(tree)


@enforce_types
def pretty_print(start: Start, do_print: bool = True) -> str:
    # rich.print(start)
    ret = ''
    _from = start.get_from()
    table = start.get_cte()
    if table:
        ret += str(table) + "\n"
    ret += str(_from)
    if do_print:
        print(ret)
    return ret


@enforce_types
def tree_to_str(tree: Union[Tree, Token, _Ast, str]) -> str:
    if isinstance(tree, Tree):
        # print(f'TREE={tree.data}')
        if tree.data == 'whole_line':
            return tree.children[0].replace('\n', '').replace('\r', '').rstrip('|')
        else:
            msg = str(f' {get_op_str(tree.data.value)} ').join([tree_to_str(c) for c in tree.children])
            return f'({msg})'
    else:
        return str(tree)


@enforce_types
def get_operation(ops: List[_Statement],
                  class_type: Type[_Statement],
                  last_match: bool = False,
                  return_all: bool = False) -> List[_Statement]:
    l = ops
    ret = []
    if last_match:
        l = list(reversed(ops))
    for op in l:
        # print(type(op))
        if isinstance(op, class_type):
            if return_all:
                ret.append(op)
            else:
                return op
    return ret


def shorten(s, n=4):
    l = len(s)
    c = ceil(l / n)
    return s[0:l:c]


def replace_tables_standalone(from_long, from_short, join_long, join_short, s) -> str:
    s = s.replace(f'{from_long}.', f'{from_short}.')
    if join_long:
        s = s.replace(f'{join_long}.', f'{join_short}.')
    return s


def wrap_replace_tables(from_long, from_short, join_long, join_short):
    def a(x):
        return replace_tables_standalone(from_long, from_short, join_long, join_short, x)

    return a


def tree_to_sql(rule, start):
    tree = start
    verbose = True
    print(f"INSGANCE={type(rule)},{rule}")
    if isinstance(rule, From):
        _from = rule
        _join = _from.get_join()

        from_long = str(_from.name)
        from_short = shorten(from_long)
        join_long = ''
        join_short = ''
        if _join:
            join_long = str(_join.name)
            join_short = shorten(join_long)
        replace_tables = wrap_replace_tables(from_long, from_short, join_long, join_short)
        # The SQL template is in the form
        # SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {order_by} {limit_str}'

        # We will be creating these strings to form the final SQL,
        # We will do it in order so that we can reference them
        select_str = ''
        agg_str = ''
        derives_str = ''
        from_str = ''
        join_str = ''
        filter_str = ''
        group_by_str = ''
        order_by = ''
        limit_str = ''
        ###

        from_str = from_long + ' ' + from_short

        ops = _from.get_pipes()
        selects = get_operation(ops.operations, Select, return_all=True)
        agg = get_operation(ops.operations, Aggregate)
        take = get_operation(ops.operations, Take)
        filters = get_operation(ops.operations, Filter, return_all=True)
        derives = get_operation(ops.operations, Derive, return_all=True)

        if verbose:
            rich.print(tree)
            ic(selects, agg, take, filters, derives)

        for select in selects:
            select_str += replace_tables(str(select))

        join = _join
        if join:
            left_id = replace_tables(str(join.left_id))
            right_id = replace_tables(str(join.right_id))
            join_short = join_short

            # left_id = left_id.replace(from_long, '').replace(from_short, '')
            on_statement = from_short + "." + left_id

            # right_id = right_id.replace(from_long, '').replace(from_short, '')
            right_side = join_short + "." + right_id

            join_str = f'JOIN {join.name} {join_short} ON {on_statement} = {right_side}'

        if agg:

            if agg.group_by is not None:
                group_by_str = f'GROUP BY {replace_tables(str(agg.group_by))}'

            for i in range(0, len(agg.aggregate_body.statements), 2):
                name = agg.aggregate_body.statements[i]
                if i + 1 < len(agg.aggregate_body.statements):
                    pipes = agg.aggregate_body.statements[i + 1]
                    agg_str += f", {pipes} as {name}"
                else:
                    agg_str += f", {name}"
            agg_str = replace_tables(agg_str)
            agg_str = agg_str.rstrip(',').lstrip(',')
        if take:
            limit_str = f'LIMIT {take.qty}'

        if filters:

            for filter in filters:
                if filter:
                    for f in filter.fields:
                        filter_str += tree_to_sql(f, start) + ' AND '
            filter_str = filter_str.rstrip(' AND ')

        if derives:

            for d in derives:
                for line in d.fields:
                    derives_str += f'{replace_tables(str(line.expression))} as {line.name} ,'
            derives_str = "," + derives_str.rstrip(",")

        if not select_str and not agg_str:
            select_str = '*'
        elif not select_str and agg_str:
            select_str = ''
        elif not select_str and derives_str:
            select_str = '*'
        elif not select_str and derives_str:
            select_str = ''
        select_str = select_str.rstrip(',').lstrip(',')
        if not filter_str:
            filter_str = '1=1'

        sql = f'SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {order_by} {limit_str}'
        # print(sql)
        return sql
    elif isinstance(rule, Expression):
        expr = rule
        msg = ''
        for s in expr.statements:
            msg += tree_to_sql(s, start)
        return msg
    elif isinstance(rule, Tree):
        raise Exception("Not implemented")
    elif isinstance(rule, Eq):
        # s.lhs = self.replace_variables(s.lhs, start)
        s = rule
        msg = ''
        if s.lhs:
            msg += tree_to_sql(s.lhs, start)
        if s.rhs:
            msg += ' = ' + tree_to_sql(s.rhs, start)
        return msg
    elif isinstance(rule, Value):
        # Here is where we dp variable expansion and function execution .
        # If its a table or value, we generate the SQL.  If its a function, we execute it
        val = str(rule)
        for table in start.value_defs.fields:
            if table.name == val:
                return "(" + tree_to_sql(table.value_body, start) + ")"

        return val
    else:
        raise Exception(f"No sql for {type(rule)}")
        # return str(rule)
