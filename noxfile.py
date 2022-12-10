"""Nox session configuration."""
from typing import List

import nox
from nox.sessions import Session

PACKAGE: str = "pyprql"
LOCATIONS: List[str] = [
    PACKAGE,
    "tests",
    "noxfile.py",
]
VERSIONS: List[str] = [
    "3.8",
    "3.9",
    "3.10",
]

nox.options.stop_on_first_error = False
nox.options.reuse_existing_virtualenvs = True


@nox.session(python=VERSIONS)
def type(session: Session) -> None:
    """Type check files with mypy."""
    args = session.posargs or LOCATIONS
    # TODO: move these to configs
    session.run("mypy", "--ignore-missing-imports", "--show-error-codes", *args)


@nox.session(python="3.10")
def security(session: Session) -> None:
    """Check security safety."""
    session.run(
        "safety",
        "check",
        "--ignore=44717",
        "--ignore=44716",
        "--ignore=44715",
        "--ignore=51457",
        "--file=requirements.txt",
        "--full-report",
    )


@nox.session(python=VERSIONS)
def tests(session: Session) -> None:
    """Run the test suite with pytest."""
    args = session.posargs or []
    session.run("pytest", *args)


@nox.session(python="3.10")
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run("sphinx-build", "docs", "docs/_build")
