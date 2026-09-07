"""Run one test suite against several interchangeable backends."""

from pytest_multi_backend._backends import (
    SKIP_BACKEND_OPTION,
    backend_fixture,
    backend_option_name,
)
from pytest_multi_backend._markers import SKIP_MARKER_OPTION

__all__ = [
    "SKIP_BACKEND_OPTION",
    "SKIP_MARKER_OPTION",
    "backend_fixture",
    "backend_option_name",
]
