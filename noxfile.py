# -*- coding: utf-8 -*-
"""Nox session configuration."""
import os
from typing import Any, List

import nox
from nox.sessions import Session

PACKAGE: str = "pyprql"
LOCATIONS: List[str] = [
    PACKAGE,
    "tests",
    "noxfile.py",
]
VERSIONS: List[str] = [
    "3.7",
    "3.8",
    "3.9",
    "3.10",
]

nox.options.stop_on_first_error = False
nox.options.reuse_existing_virtualenvs = True


def constrained_install(session: Session, *args: str, **kwargs: Any) -> None:
    """Install packages with poetry version constraint."""
    session.run(
        "poetry",
        "export",
        "--dev",
        "--without-hashes",
        "--format=requirements.txt",
        "--output=requirements.txt",
        external=True,
    )
    session.install("--constraint=requirements.txt", *args, **kwargs)
    os.remove("requirements.txt")


@nox.session(python="3.8")
def form(session: Session) -> None:
    """Format code with isort and black."""
    args = session.posargs or LOCATIONS
    constrained_install(session, "isort", "black")
    session.run("isort", *args)
    session.run("black", *args)


@nox.session(python=VERSIONS)
def lint(session: Session) -> None:
    """Lint files with flake8."""
    args = session.posargs or LOCATIONS
    constrained_install(
        session,
        "flake8",
        "flake8-annotations",
        "flake8-docstrings",
        "flake8-pytest-style",
        "darglint",
    )
    session.run("flake8", *args)


@nox.session(python=VERSIONS)
def type(session: Session) -> None:
    """Type check files with mypy."""
    args = session.posargs or LOCATIONS
    constrained_install(session, "mypy")
    session.run("mypy", "--ignore-missing-imports", "--show-error-codes", *args)


@nox.session(python="3.10")
def security(session: Session) -> None:
    """Check security safety."""
    session.run(
        "poetry",
        "export",
        "--dev",
        "--without-hashes",
        "--format=requirements.txt",
        "--output=requirements.txt",
        external=True,
    )
    session.install("--constraint=requirements.txt", "safety")
    # the ignored flags are only relevant in python 3.7,
    # where numpy <1.22 is required
    session.run(
        "safety",
        "check",
        "--ignore=44717",
        "--ignore=44716",
        "--ignore=44715",
        "--file=requirements.txt",
        "--full-report",
    )
    os.remove("requirements.txt")


@nox.session(python=VERSIONS, reuse_venv=False)
def tests(session: Session) -> None:
    """Run the test suite with pytest."""
    args = session.posargs or []
    session.run("poetry", "install", "--no-dev", external=True)
    constrained_install(  # These are required for tests. Don't clutter w/ all dependencies!
        session,
        "coverage",
        "pytest",
        "pytest-clarity",
        "pytest-sugar",
        "pytest-xdist",
        "pytest-cov",
        "xdoctest",
    )
    session.run("pytest", *args)


@nox.session(python="3.10", reuse_venv=False)
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--no-dev", external=True)
    constrained_install(
        session,
        "sphinx",
        "sphinx-rtd-theme",
        "myst-parser",
        "pytest",
    )
    session.run("sphinx-build", "docs", "docs/_build")
