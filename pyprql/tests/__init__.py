from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import IPython


def run_sql(ip_session: "IPython.core.interactiveshell.InteractiveShell", statements):
    if isinstance(statements, str):
        statements = [statements]
    for statement in statements:
        result = ip_session.run_line_magic("sql", f"sqlite:// {statement}")
    return result  # returns only last result


def run_prql(ip_session: "IPython.core.interactiveshell.InteractiveShell", statements):
    if isinstance(statements, str):
        statements = [statements]
    for statement in statements:
        result = ip_session.run_line_magic("prql", f"sqlite:// {statement}")
    return result  # returns only last result
