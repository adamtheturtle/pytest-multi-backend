"""Reading the values of the plugin's command line options."""

from collections.abc import Iterable
from typing import TypeGuard

import pytest
from beartype import beartype


def _is_iterable(value: object, /) -> TypeGuard[Iterable[object]]:
    """Recognize a collection of pytest option values."""
    return isinstance(value, Iterable)


def option_strings(*, value: object) -> list[str]:
    """Return string values from a repeatable pytest setting."""
    return [str(object=item) for item in value] if _is_iterable(value) else []


@beartype
def option_values(*, config: pytest.Config, option_name: str) -> list[str]:
    """The values given to a repeatable option.

    Args:
        config: The configuration to read the option from.
        option_name: The option, with its leading dashes, whose values to
            give.

    Returns:
        Each value which was given to the option, in the order given.
    """
    name = option_name.lstrip("-").replace("-", "_")
    values: object = config.getoption(name=name)
    return option_strings(value=values)
