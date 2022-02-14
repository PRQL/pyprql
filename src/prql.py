import os
import sys
from dataclasses import dataclass
from typing import List, Union, Type, Any, Dict

import lark
import rich
from enforce_typing import enforce_types
from icecream import ic
from lark import Lark, ast_utils, Transformer, Token
from lark.tree import Tree

this_module = sys.modules[__name__]
script_path = os.path.dirname(__file__)


class _Ast(ast_utils.Ast):
    pass


class _Statement(_Ast):

    @enforce_types
    def replace_variables(self, s, start):
        for idx, v in enumerate(start.value_defs.fields):
            if str(v.name) == str(s):
                if isinstance(v, ValueDef):
                    return str(v.value_body)

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
                msg += f'{s} '

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
class Operator(_Statement):

    def get_op(self):
        return self.op

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} {self.op} {self.rhs}"


@dataclass
class Neq(Operator):
    lhs: Expression
    rhs: Expression = None
    op: str = '!='

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} != {self.rhs}"


@dataclass
class Eq(Operator):
    lhs: Expression
    rhs: Expression = None
    op: str = '='

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} = {self.rhs}"


@dataclass
class Diff(Operator):
    lhs: Expression
    rhs: Expression = None
    op: str = '-'


@dataclass
class Lt(_Statement):
    lhs: Expression
    rhs: Expression = None
    op: str = '<'

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} < {self.rhs}"


@dataclass
class Lte(_Statement):
    lhs: Expression
    rhs: Expression = None
    op: str = '<='

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} <= {self.rhs}"


@dataclass
class Sum(_Statement):
    lhs: Expression
    rhs: Expression = None
    op: str = '+'

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} + {self.rhs}"


@dataclass
class Gt(_Statement):
    lhs: Expression
    rhs: Expression = None
    op: str = '>'

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} > {self.rhs}"


@dataclass
class Gte(_Statement):
    lhs: Expression
    rhs: Expression = None
    op: str = '>='

    def __str__(self):
        if self.rhs is None:
            return f"{self.lhs}"
        else:
            return f"{self.lhs} >= {self.rhs}"


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
        return f'{self.name1}({self.name2}) as {self.name1}_{self.name2}'


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
        return f'{str(self.name)}'


@dataclass
class Take(_Statement):
    qty: str

    def __str__(self):
        return f'take: {self.qty}'


@dataclass
class Filter(_Statement, ast_utils.AsList):
    fields: List[str]
    name: str = "filter"

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
class FuncBody(_Statement, ast_utils.AsList):
    fields: List[str]


@dataclass
class FuncDef(_Statement):
    name: Name
    func_args: FuncArgs
    func_body: FuncBody = None


@dataclass
class FuncCall(_Statement):
    name: Name = None
    func_args: FuncArgs = None
    parm1: Any = None

    def __str__(self):
        return f'{self.name}({str(self.func_args)})'


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

    def __str__(self):
        return f'with {self.name} from {self._from.name}:\n\t{self._from}'


@dataclass
class Start(_Statement):
    # Corresponds to start in the grammar
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
def to_sql(prql: str) -> str:
    ast = parse(prql)
    return ast_to_sql(ast._from, ast).replace('   ', ' ').replace('  ', ' ')


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
    ops_list = ops
    ret = []
    if last_match:
        ops_list = list(reversed(ops))
    for op in ops_list:
        # print(type(op))
        if isinstance(op, class_type):
            if return_all:
                ret.append(op)
            else:
                return op
    return ret


@enforce_types
def alias(s: str, n: int = 1):
    return s + '_' + s[0:n]


def replace_tables_standalone(from_long, from_short, join_long, join_short, s) -> str:
    s = s.replace(f'{from_long}.', f'{from_short}.')
    if join_long:
        s = s.replace(f'{join_long}.', f'{join_short}.')
    return s


def wrap_replace_tables(from_long, from_short, join_long, join_short):
    def a(x):
        return replace_tables_standalone(from_long, from_short, join_long, join_short, x)

    return a


@enforce_types
def build_symbol_table(start: Start) -> Dict[str, _Ast]:
    table = {}
    for n in start.value_defs.fields:
        table[str(n.name)] = n
    for n in start.func_defs.fields:
        table[str(n.name)] = n

    return table


@enforce_types
def execute_function(f: FuncCall, symbol_table: Dict[str, _Ast]) -> str:
    print('EXECUTING ' + str(f.name))
    msg = 'NOT_FINISHED_YET --- '
    name = str(f.name)
    func_def: FuncDef = symbol_table[name]
    # Execute line by line the function
    for line in func_def.func_body.fields:
        # First just text replcaement ,
        if type(line) == str:
            args = {}
            vals = [f.parm1, f.func_args]
            for i in range(0, len(func_def.func_args.fields)):
                n = str(func_def.func_args.fields[i])
                args[n] = vals[i]
            msg = line.format(**args)

    return msg


# E
@enforce_types
def ast_to_sql(
        rule: Union[_Ast, lark.lexer.Token],
        start: Start,
        symbol_table: dict = None,
        verbose: bool = True):
    tree = start

    if not symbol_table:
        symbol_table = build_symbol_table(tree)

    if isinstance(rule, lark.lexer.Token):
        return str(rule)

    if isinstance(rule, From):
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
        order_by_str = ''
        limit_str = ''
        ###

        _from = rule
        _join = _from.get_join()

        from_long = str(_from.name)
        from_short = alias(from_long)
        join_long = ''
        join_short = ''
        if _join:
            join_long = str(_join.name)
            join_short = alias(join_long)
        replace_tables = wrap_replace_tables(from_long, from_short, join_long, join_short)

        from_str = from_long + ' ' + from_short

        ops = _from.get_pipes()
        selects = get_operation(ops.operations, Select, return_all=True)
        agg = get_operation(ops.operations, Aggregate)
        take = get_operation(ops.operations, Take)
        sort = get_operation(ops.operations, Sort)

        filters = get_operation(ops.operations, Filter, return_all=True)
        derives = get_operation(ops.operations, Derive, return_all=True)

        if verbose:
            rich.print(tree)

        for select in selects:
            select_str += replace_tables(str(select))

        join = _join
        if join:
            left_id = replace_tables(str(join.left_id))
            right_id = replace_tables(str(join.right_id))
            join_short = join_short

            # left_id = left_id.replace(from_long, '').replace(from_short, '')
            on_statement = str(from_short + "." + left_id).replace(from_short + "." + from_short + ".",
                                                                   from_short + ".")

            # right_id = right_id.replace(from_long, '').replace(from_short, '')
            right_side = str(join_short + "." + right_id).replace(join_short + "." + join_short + ".", join_short + ".")

            join_str = f'JOIN {join.name} {join_short} ON {on_statement} = {right_side}'

        if agg:

            if agg.group_by is not None:
                group_by_str = f'GROUP BY {replace_tables(str(agg.group_by))}'

            upper = len(agg.aggregate_body.statements)
            i = 0
            while i < upper:
                first = agg.aggregate_body.statements[i]
                if first is not None:
                    if isinstance(first, lark.lexer.Token):
                        name = first
                        i += 1
                        func_call = agg.aggregate_body.statements[i]

                        if isinstance(func_call, FuncCall):
                            if func_call.func_args is not None:
                                agg_str += f'{func_call} as {name},'
                        elif isinstance(func_call, str):
                            agg_str += f'{func_call} as {name},'
                        else:
                            raise Exception('Unknown type for aggregate body ')
                        # print('ASSIGNMENT! : ', first)
                    elif isinstance(first, FuncCall):
                        f = first
                        if f.func_args is not None:
                            agg_str += f'{str(f)} as {f.name}_{f.func_args},'
                    i += 1

            agg_str = replace_tables(agg_str)
            agg_str = agg_str.rstrip(',').lstrip(',')
        if take:
            limit_str = f'LIMIT {take.qty}'

        if filters:
            for filter in filters:
                if filter:
                    for f in filter.fields:
                        filter_str += ast_to_sql(f, start, symbol_table) + ' AND '
            filter_str = filter_str.rstrip(' AND ')

        if derives:
            for d in derives:
                for line in d.fields:
                    derives_str += f'{replace_tables(str(line.expression))} as {line.name} ,'
            derives_str = "," + derives_str.rstrip(",")

        if sort:
            order_by_str = f"ORDER BY {sort}"

        if not select_str and not agg_str:
            select_str = '*'
        elif not select_str and agg_str:
            select_str = ''
        elif not select_str and derives_str:
            select_str = '*'
        elif not select_str and derives_str:
            select_str = ''
        select_str = select_str.rstrip(',').lstrip(',')

        if select_str and agg_str:
            select_str += ','

        if not filter_str:
            filter_str = '1=1'
        if verbose:
            ic(select_str,
               agg_str,
               derives_str,
               from_str,
               join_str,
               filter_str,
               group_by_str,
               order_by_str,
               limit_str)
        sql = f'SELECT {select_str} {agg_str} {derives_str} FROM {from_str} {join_str} WHERE {filter_str} {group_by_str} {order_by_str} {limit_str}'
        # print(sql)
        if verbose:
            print(sql)
        return sql
    elif isinstance(rule, Expression):
        expr = rule
        msg = ''
        for s in expr.statements:
            msg += ast_to_sql(s, start, symbol_table)
        return msg
    elif isinstance(rule, Tree):
        print(f'TREE={tree.data}')
        tree = rule
        if tree.data == 'whole_line':
            return tree.children[0].replace('\n', '').replace('\r', '').rstrip('|')
        else:
            msg = str(f' {get_op_str(tree.data.value)} ').join([tree_to_str(c) for c in tree.children])
            return f'({msg})'
    elif isinstance(rule, Eq) or isinstance(rule, Gt) or isinstance(rule, Neq) \
            or isinstance(rule, Lt) or isinstance(rule, Gte) or isinstance(rule, Lte):
        # s.lhs = self.replace_variables(s.lhs, start)
        s = rule
        msg = ''
        operator = rule.op
        if s.lhs:
            msg += ast_to_sql(s.lhs, start, symbol_table)
        if s.rhs:
            msg += operator + ast_to_sql(s.rhs, start, symbol_table)
        return msg
    elif isinstance(rule, PipedCall):
        pipe: PipedCall = rule
        msg = ''
        pipe.func_body.parm1 = pipe.parm1
        msg += ast_to_sql(pipe.func_body, start, symbol_table)

        # msg = f'{pipe.func_body}({pipe.parm1})'
        return msg
    elif isinstance(rule, FuncCall):
        f = rule
        if f.parm1:
            v = ',' + ast_to_sql(f.parm1, start, symbol_table)
            msg = str(f.name) + f'({v})'
        if f.name in symbol_table:
            msg = execute_function(f, symbol_table)
        return msg
    elif isinstance(rule, Value):
        # Here is where we dp variable expansion and function execution .
        # If its a table or value, we generate the SQL.  If its a function, we execute it
        val = str(rule)
        if start.value_defs:
            for table in start.value_defs.fields:
                if table.name == val:
                    return "(" + ast_to_sql(table.value_body, start, symbol_table) + ")"

        return val
    else:
        raise Exception(f"No sql for {type(rule)}")
        # return str(rule)
