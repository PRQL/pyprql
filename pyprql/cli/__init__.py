"""The command line interface implementation for pyprql."""
import sys
import warnings
from typing import List, Optional

from pyprql.cli.cli import CLI

warnings.warn(
    """
Currently the pyprql CLI is unfortunately deprecated, since the original creators are no
longer active. It was a valiant effort, and of the first things that was built on top of
PRQL. But it's a big project that requires work to keep it current.

If anyone would be interested in taking it over, please feel free to start contributing,
and we can un-deprecate it.
""",
    DeprecationWarning,
)


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
