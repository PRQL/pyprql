import os
import sys
from dataclasses import dataclass
from typing import List, Union, Type

from enforce_typing import enforce_types
from lark import Lark, ast_utils, Transformer, Token
from lark.tree import Tree

import prql

this_module = sys.modules[__name__]
script_path = os.path.dirname(__file__)


class _Ast(ast_utils.Ast):
    pass


class _Statement(_Ast):
    pass


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
class Expression(_Ast, ast_utils.AsList):
    # Corresponds to expression in the grammar
    statements: List[_Statement]

    def __str__(self):
        msg = ''
        for s in self.statements:
            if isinstance(s, Tree):
                msg += tree_to_str(s).replace("\n", ",")
            else:
                msg += f' | {s} '  # str(s)

        return msg


@dataclass
class SetVar(_Statement):
    # Corresponds to set_var in the grammar
    name: str
    value: Value


@dataclass
class Join(_Statement):
    # Corresponds to join in the grammar
    name: Name
    value: Name
    right_id: Name = None

    def __str__(self):
        return f"join: {self.name} on {self.value} {' = ' + self.right_id.name if self.right_id else ''}"


@dataclass()
class SelectFields(_Ast, ast_utils.AsList):
    fields: List[Name]

    def __str__(self):
        return [str(x) for x in self.fields]


@dataclass
class Select(_Statement):
    # Corresponds to select in the grammar
    fields: SelectFields

    def __str__(self):
        return ",".join([str(f) for f in self.fields.fields])


@dataclass
class DeriveLine(_Statement):
    name: str
    expression: Expression


@dataclass
class GroupBy(_Ast, ast_utils.AsList):
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
class AggregateBody(_Ast, ast_utils.AsList):
    statements: List[NamePair]

    def __str__(self):
        return f'{[str(s) for s in self.statements]}'


@dataclass
class Aggregate(_Statement):
    group_by: GroupBy
    aggregate_body: AggregateBody

    def __str__(self):
        return f'aggregate: \n\t\taggregates: {self.aggregate_body}\n\t\tgroup_by: {self.group_by}'


@dataclass
class Derive(_Ast, ast_utils.AsList):
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


def get_op_str(op):
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


@dataclass
class Filter(_Ast, ast_utils.AsList):
    fields: List[str]

    def to_sql(self):
        msg = ''
        for idx, f in enumerate(self.fields):
            msg += f'\n\t\t{tree_to_str(f)}'
        return msg.replace("\n", "").replace("\r", "").replace("\t", "")

    # def __str__(self):
    #     ret = 'filter:\n\t\t'
    #     for idx, f in enumerate(self.fields):
    #         if isinstance(f, Expression):
    #             op_tree = f.statements[0]
    #             ret += f'{tree_to_str(op_tree)}\n\t\t'
    #
    #         else:
    #             ret += f'filter: {f},{type(f)}'
    #     return ret[0:-3]  # cut out the last newline

    def __str__(self):
        msg = 'filter:'
        for idx, f in enumerate(self.fields):
            msg += f'\n\t\t{tree_to_str(f)}'
        return msg


@dataclass
class Query(_Ast, ast_utils.AsList):
    operations: List[_Statement]


@dataclass
class From(_Statement):
    # Corresponds to from in the grammar
    name: str
    query: Query = None
    join: Join = None

    def __init__(self, name, query=None, join=None):
        # This is dumb as shit but I cant figure out how to tell lark to use named parameters and the join is optional :shrug:
        self.name = name
        if isinstance(query, Query):
            self.query = query
        if isinstance(join, Query):
            self.query = join
        if isinstance(query, Join):
            self.join = query
        if isinstance(join, Join):
            self.join = join

    def get_query(self):
        return self.query

    def get_join(self):
        return self.join

    def __str__(self):

        ret = ''
        ret += f'from {self.name}\n'
        join = self.get_join()
        if join is not None:
            ret += f'\t{join}\n'
        for op in self.get_query().operations:
            ret += f'\t{str(op)}\n'
        return ret


@dataclass
class Cte(_Statement):
    name: Name
    _from: From

    def __str__(self):
        return f'with {self.name} from {self._from.name}:\n\t{self._from}'


@dataclass
class Start(_Statement):
    # Corresponds to start in the grammar
    cte: Cte = None
    _from: From = None

    def __init__(self, cte=None, _from=None):
        self.cte = cte
        # So ghetto here, see From for why
        if isinstance(_from, From):
            self._from = _from
        if isinstance(cte, From):
            self._from = cte
        if isinstance(_from, Cte):
            self.cte = _from
        if isinstance(cte, Cte):
            self.cte = cte

        if not isinstance(self.cte, Cte):
            self.cte = None

    def get_from(self):
        return self._from

    def get_cte(self):
        return self.cte


class ToAst(Transformer):

    def STRING(self, s):
        # Remove quotation marks
        return s[1:-1]


@enforce_types
def read_file(filename: str, path: str = script_path) -> str:
    with open(path + filename, "r") as f:
        x = f.read()
    return x


@enforce_types
def parse(text: str) -> Start:
    parser = Lark(read_file('/../resource/prql.lark'), start="start", parser="lalr", transformer=ToAst())
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
def tree_to_str(tree: Union[Tree, Token, _Ast]) -> str:
    if isinstance(tree, Tree):
        # print(f'TREE={tree.data}')
        if tree.data == 'whole_line':
            return tree.children[0].replace('\n', '').replace('\r', '')
        else:
            msg = str(f' {get_op_str(tree.data.value)} ').join([tree_to_str(c) for c in tree.children])
            return f'({msg})'
    else:
        return str(tree)


def get_operation(ops: List[_Statement], class_type: Type[_Statement], last_match: bool = False,
                  return_all: bool = False) -> List[_Statement]:
    l = ops
    ret = []
    if last_match:
        l = list(reversed(ops))
    for op in l:
        # print(type(op))
        if isinstance(op, class_type):
            if return_all:
                ret += op
            else:
                return op
    return ret


def replace_with_short_version(s, from_long, from_short, join_long, join_short):
    s = s.replace(f'{from_long}.', f'{from_short}.')
    s = s.replace(f'{join_long}.', f'{join_short}.')
    return s


@enforce_types
def tree_to_sql(tree: Start) -> str:
    # return tree_to_str(tree)
    # ret = str(tree)
    # return ret
    # first get the select fields
    _from = tree.get_from()
    from_str = f'{_from.name}'
    from_short = from_str[0:3]
    from_str += f' {from_short}'
    ops = _from.get_query()
    select = get_operation(ops.operations, prql.Select)
    select_str = str(select)
    join = _from.get_join()
    join_from_str = ''
    join_str = ''
    if join:
        join_short = f'{str(join.name)[0:3]}'
        join_str = f'INNER JOIN {join.name} ON {from_short}.{join.value} = {join_short}.{join.right_id}'
        join_from_str = f',{join.name} {join_short}'
        select_str = replace_with_short_version(select_str, str(_from.name), from_short, str(join.name), join_short)

    agg = get_operation(ops.operations, prql.Aggregate)
    group_by_str = ''
    agg_str = ''
    limit_str = ''
    take = get_operation(ops.operations, prql.Take)
    if take:
        limit_str = f'LIMIT {take.qty}'
    if agg:
        group_by_str = f'GROUP BY {agg.group_by}'
        group_by_str = replace_with_short_version(group_by_str, str(_from.name), from_short, str(join.name), join_short)

        # rich.print(agg)
        for i in range(0, len(agg.aggregate_body.statements), 2):
            name = agg.aggregate_body.statements[i]
            query = agg.aggregate_body.statements[i + 1]
            agg_str += f", {query} as {name}"
        # agg_str = f", {agg_str}"
        agg_str = replace_with_short_version(agg_str, str(_from.name), from_short, str(join.name), join_short)

    filter = get_operation(ops.operations, prql.Filter)
    filter_str = ''
    if filter:
        clause = filter.to_sql()
        clause = replace_with_short_version(clause, str(_from.name), from_short, str(join.name), join_short)
        filter_str = f'WHERE {clause}'

    sort = get_operation(ops.operations, prql.Sort, last_match=True)
    order_by = ''
    if sort:
        order_by = f'ORDER BY {str(tree_to_str(sort.name))}'
        order_by = replace_with_short_version(order_by, str(_from.name), from_short, str(join.name), join_short)

    derives = get_operation(ops.operations, prql.Derive, return_all=True)
    derives_str = ''
    if derives:
        derives_str = f'{derives}'

    if select_str is None or select_str == 'None':
        select_str = '*'
    sql = f'SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_from_str} {join_str} {filter_str} {group_by_str} {order_by} {limit_str}'
    print(sql)
    return sql
