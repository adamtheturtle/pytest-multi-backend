"""Fixtures which run each test once per backend.

A "backend" is one way of running the system which the tests exercise.
A suite might run against a real remote service, an in-memory fake of
that service, and the same fake behind an HTTP server, and assert the
same things about each. That is how a fake is kept honest.

Backends are identified by members of any :class:`~enum.Enum`: the
member name gives the value which ``--skip-backend`` takes to deselect
it, and the member value gives the ID which ``pytest`` shows for it.
"""

import contextlib
import functools
from collections.abc import Callable, Generator, Sequence
from enum import Enum

import pytest

# ``pytest.fixture`` returns one of these, but ``pytest`` does not export
# the type.
# See https://github.com/pytest-dev/pytest/issues/14853.
from _pytest.fixtures import FixtureFunctionDefinition
from beartype import beartype

from pytest_multi_backend._options import option_values

SKIP_BACKEND_OPTION = "--skip-backend"


# Every backend which a fixture has been made for, keyed by the value
# which ``--skip-backend`` takes for it. Fixtures are made when the
# modules which define them are imported, which happens before
# collection finishes, so this is complete by the time the option is
# checked against it.
_REGISTERED_BACKENDS: dict[str, set[Enum]] = {}


@beartype
def _backend_parameter(*, value: Enum) -> Enum:
    """Type a backend value supplied by the pytest parameter API."""
    return value


@beartype
def backend_option_name(*, backend: Enum) -> str:
    """The value which ``--skip-backend`` takes to skip a backend.

    Args:
        backend: The backend to give the value for.

    Returns:
        The name of the backend's :class:`~enum.Enum` member, in lower
        case.
    """
    return backend.name.lower()


@beartype
def registered_backend_names() -> frozenset[str]:
    """The ``--skip-backend`` values of every backend with a fixture.

    Returns:
        The value which ``--skip-backend`` takes for each backend which
        :func:`backend_fixture` has been called with.
    """
    return frozenset(_REGISTERED_BACKENDS)


@beartype
def skipped_backend_names(*, config: pytest.Config) -> frozenset[str]:
    """The backends which ``--skip-backend`` was given.

    Args:
        config: The configuration to read the option from.

    Returns:
        Each value which was given to ``--skip-backend``.
    """
    return frozenset(
        option_values(config=config, option_name=SKIP_BACKEND_OPTION),
    )


@beartype
def _backend_ids(*, backends: Sequence[Enum]) -> list[str]:
    """The IDs which ``pytest`` shows for a set of backends.

    Args:
        backends: The backends to give IDs for.

    Returns:
        The ID to show for each given backend.
    """
    return [f"{backend.value!s}" for backend in backends]


@beartype
def backend_fixture(
    *,
    name: str,
    backends: Sequence[Enum],
    setup_for: Callable[..., Generator[None]],
) -> FixtureFunctionDefinition:
    """Make a fixture which runs each test once per backend.

    A test which uses the fixture runs once against each backend, with
    the backend's ID in the test's ID. Giving ``--skip-backend`` the
    :func:`backend_option_name` of a backend skips, rather than
    deselects, each test against that backend, so that a run which
    skips a backend still reports the tests which would have used it.

    Args:
        name: The name which tests use to request the fixture.
        backends: The backends to run each test against.
        setup_for: A generator function which is called with the keyword
            arguments ``backend`` and ``request``. It sets that backend
            up, yields once while the test runs, and then tears it down.
            Anything else it needs comes from
            :meth:`~pytest.FixtureRequest.getfixturevalue`, because a
            fixture made here requests no fixtures but ``request``.

    Returns:
        A fixture which yields the backend which the test is running
        against. Assign it to a module-level name in a ``conftest.py``
        or a plugin module for ``pytest`` to find it.
    """
    for backend in backends:
        option_name = backend_option_name(backend=backend)
        _REGISTERED_BACKENDS.setdefault(option_name, set()).add(backend)

    @pytest.fixture(
        name=name,
        params=backends,
        ids=_backend_ids(backends=backends),
    )
    def _fixture(
        *,
        request: pytest.FixtureRequest,
    ) -> Generator[Enum]:
        """Run a test against one backend.

        Yields:
            The backend which the test is running against.
        """
        backend = _backend_parameter(value=request.param)
        option_name = backend_option_name(backend=backend)
        if option_name in skipped_backend_names(config=request.config):
            reason = f"{SKIP_BACKEND_OPTION}={option_name} was given"
            pytest.skip(reason=reason)

        setup = functools.partial(setup_for, backend=backend, request=request)
        with contextlib.contextmanager(func=setup)():
            yield backend

    return _fixture
