"""Reading the values of the plugin's command line options."""

from typing import TypeGuard

import pytest
from beartype import beartype
from beartype.door import TypeHint


@beartype
def _is_string_list(value: object) -> TypeGuard[list[str]]:
    """Whether a value is a list which contains only strings.

    Args:
        value: The value to check.

    Returns:
        Whether the value is a list of strings.
    """
    return TypeHint(hint=list[str]).is_bearable(obj=value)


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
    values = config.getoption(name=option_name.lstrip("-").replace("-", "_"))
    if not _is_string_list(value=values):  # pragma: no cover
        message = f"pytest gave a non-list value for {option_name}: {values!r}"
        raise TypeError(message)
    return values
