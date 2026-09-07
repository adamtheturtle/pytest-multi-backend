"""Skip tests which carry a marker, via a command line option."""

import pytest
from beartype import beartype

from pytest_multi_backend._options import option_values

SKIP_MARKER_OPTION = "--skip-marker"


@beartype
def skipped_marker_names(*, config: pytest.Config) -> frozenset[str]:
    """The markers which ``--skip-marker`` was given.

    Args:
        config: The configuration to read the option from.

    Returns:
        Each value which was given to ``--skip-marker``.
    """
    return frozenset(
        option_values(config=config, option_name=SKIP_MARKER_OPTION),
    )


@beartype
def registered_marker_names(*, config: pytest.Config) -> frozenset[str]:
    """The markers which the project has registered.

    Args:
        config: The configuration to read the ``markers`` setting from.

    Returns:
        The name of each marker registered in the ``markers`` setting,
        whether in a configuration file or by a plugin. A registration
        looks like ``name: description`` or ``name(args): description``.
    """
    lines: list[str] = config.getini(name="markers")
    names: set[str] = set()
    for line in lines:
        (name_and_args, _, _) = line.partition(":")
        (marker_name, _, _) = name_and_args.partition("(")
        names.add(marker_name.strip())
    return frozenset(names)


@beartype
def skip_marked_items(
    *,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip each test which carries a marker given to ``--skip-marker``.

    Args:
        config: The configuration to read the option from.
        items: The collected tests.

    Raises:
        pytest.UsageError: A given marker is not registered.
    """
    skipped_markers = skipped_marker_names(config=config)
    unknown_markers = skipped_markers - registered_marker_names(config=config)
    if unknown_markers:
        message = (
            f"{SKIP_MARKER_OPTION} was given the unregistered marker(s) "
            f"{', '.join(sorted(unknown_markers))}. Register markers in "
            "the 'markers' setting."
        )
        raise pytest.UsageError(message)

    for marker_name in sorted(skipped_markers):
        skip_marker = pytest.mark.skip(
            reason=f"{SKIP_MARKER_OPTION}={marker_name} was given",
        )
        for item in items:
            if item.get_closest_marker(name=marker_name) is not None:
                item.add_marker(marker=skip_marker)
