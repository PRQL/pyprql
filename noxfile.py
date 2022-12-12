"""Nox session configuration."""
from typing import List

import nox
from nox.sessions import Session

PACKAGE: str = "pyprql"
LOCATIONS: List[str] = [
    PACKAGE,
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
    session.run_always("poetry", "install", external=True)
    args = session.posargs or LOCATIONS
    session.run("mypy", "--show-error-codes", *args)


@nox.session(python="3.10")
def security(session: Session) -> None:
    """Check security safety."""
    session.run_always("poetry", "install", external=True)
    session.run(
        "safety",
        "check",
        "--ignore=51668",
        "--ignore=51457",
        "--full-report",
    )


@nox.session(python=VERSIONS)
def tests(session: Session) -> None:
    """Run the test suite with pytest."""
    session.run_always("poetry", "install", external=True)
    args = session.posargs or []
    session.run("pytest", *args)


@nox.session(python="3.10")
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run_always("poetry", "install", external=True)
    session.run("sphinx-build", "docs", "docs/_build")
