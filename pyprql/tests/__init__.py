import IPython


def run_sql(ip_session: IPython.core.interactiveshell.InteractiveShell, statements):
    if isinstance(statements, str):
        statements = [statements]
    for statement in statements:
        result = ip_session.run_line_magic("sql", "sqlite:// %s" % statement)
    return result  # returns only last result


def run_prql(ip_session: IPython.core.interactiveshell.InteractiveShell, statements):
    if isinstance(statements, str):
        statements = [statements]
    for statement in statements:
        result = ip_session.run_line_magic("prql", "sqlite:// %s" % statement)
    return result  # returns only last result
