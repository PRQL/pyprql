# -*- coding: utf-8 -*-
"""The command line interface implementation for PyPRQL."""
import sys
from typing import List, Optional

from pyprql.cli.cli import CLI


def main(params: Optional[List[str]] = None) -> None:
    """Serve the CLI entrypoint.

    If ``params`` is left as it's default ``None``,
    then ``params`` is set to ``sys.argv``.
    If no parameters are passed,
    then the help message is printed.
    Otherwise,
    a prompt is activated until a keyboard interrupt.

    Parameters
    ----------
    params : Optional[List[str]], default None
        The parameters passed to the CLI.
    """
    if params is None:
        params = sys.argv
    try:
        if len(params) > 1:
            cli = CLI(params[1])
            cli.run()
        else:
            CLI.print_usage()
            sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
