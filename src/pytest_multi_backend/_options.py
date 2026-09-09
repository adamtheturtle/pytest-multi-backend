"""Reading the values of the plugin's command line options."""

import pytest
from beartype import beartype


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
    return [str(object=value) for value in values or ()]
