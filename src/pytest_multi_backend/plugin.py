"""The ``pytest`` plugin: the command line options and what they skip.

This is registered under the ``pytest11`` entry point, so ``pytest``
loads it whenever the package is installed.
"""

import pytest
from beartype import beartype

from pytest_multi_backend._backends import (
    SKIP_BACKEND_OPTION,
    registered_backend_names,
    skipped_backend_names,
)
from pytest_multi_backend._markers import SKIP_MARKER_OPTION, skip_marked_items


@beartype
def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the options which skip backends and markers.

    Args:
        parser: The parser to add the options to.
    """
    group = parser.getgroup(name="multi-backend")
    group.addoption(
        SKIP_BACKEND_OPTION,
        action="append",
        default=[],
        dest="skip_backend",
        metavar="BACKEND",
        help=(
            "Skip tests which run against BACKEND, the lower case name of "
            "a backend enum member. Give this once per backend to skip."
        ),
    )
    group.addoption(
        SKIP_MARKER_OPTION,
        action="append",
        default=[],
        dest="skip_marker",
        metavar="MARKER",
        help=(
            "Skip tests which carry the registered marker MARKER. Give "
            "this once per marker to skip."
        ),
    )


@beartype
def _check_skipped_backends(*, config: pytest.Config) -> None:
    """Fail if ``--skip-backend`` names a backend which has no fixture.

    Args:
        config: The configuration to read the option from.

    Raises:
        pytest.UsageError: A given backend is not one which
            :func:`~pytest_multi_backend.backend_fixture` was called
            with.
    """
    registered_names = registered_backend_names()
    unknown_names = skipped_backend_names(config=config) - registered_names
    if not unknown_names:
        return

    known_description = (
        ", ".join(sorted(registered_names))
        if registered_names
        else "none; no backend fixture has been made"
    )
    message = (
        f"{SKIP_BACKEND_OPTION} was given the unknown backend(s) "
        f"{', '.join(sorted(unknown_names))}. "
        f"Known backends: {known_description}."
    )
    raise pytest.UsageError(message)


@beartype
def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Check the skip options and apply the marker skips.

    Backend skips are applied by the fixtures themselves when they run.
    By now every module which makes a backend fixture has been imported,
    so the backends given to ``--skip-backend`` can be checked.

    Args:
        config: The configuration to read the options from.
        items: The collected tests.
    """
    _check_skipped_backends(config=config)
    skip_marked_items(config=config, items=items)
