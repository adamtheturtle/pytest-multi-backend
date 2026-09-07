"""Tests for ``--skip-marker``."""

import textwrap

import pytest

_TEST_FILE = textwrap.dedent(
    text='''\
    """Tests with and without a marker."""

    import pytest


    @pytest.mark.slow
    def test_marked() -> None:
        """Pass."""


    @pytest.mark.slow("with an argument")
    def test_marked_with_argument() -> None:
        """Pass."""


    def test_unmarked() -> None:
        """Pass."""
    ''',
)


def test_skip_marker(*, pytester: pytest.Pytester) -> None:
    """``--skip-marker`` skips, rather than deselects, each test which
    carries the marker.
    """
    pytester.makeini(
        source=textwrap.dedent(
            text="""\
            [pytest]
            markers =
                slow: a test which takes a long time
            """,
        ),
    )
    pytester.makepyfile(test_example=_TEST_FILE)

    result = pytester.runpytest("--skip-marker=slow", "--verbose", "-rs")

    result.assert_outcomes(passed=1, skipped=2)
    result.stdout.fnmatch_lines(
        lines2=[
            "*test_example.py::test_marked SKIPPED*",
            "*test_example.py::test_marked_with_argument SKIPPED*",
            "*test_example.py::test_unmarked PASSED*",
            "*--skip-marker=slow was given*",
        ],
    )


def test_marker_registered_with_arguments(
    *,
    pytester: pytest.Pytester,
) -> None:
    """A marker registered with an argument list is known by its name."""
    pytester.makeini(
        source=textwrap.dedent(
            text="""\
            [pytest]
            markers =
                slow(reason): a test which takes a long time
            """,
        ),
    )
    pytester.makepyfile(test_example=_TEST_FILE)

    result = pytester.runpytest("--skip-marker=slow")

    result.assert_outcomes(passed=1, skipped=2)


def test_skip_unregistered_marker(*, pytester: pytest.Pytester) -> None:
    """Giving ``--skip-marker`` a marker which is not registered is an
    error, so that a mistyped marker does not silently skip nothing.
    """
    pytester.makeini(
        source=textwrap.dedent(
            text="""\
            [pytest]
            markers =
                slow: a test which takes a long time
            """,
        ),
    )
    pytester.makepyfile(test_example=_TEST_FILE)

    result = pytester.runpytest("--skip-marker=slw", "--skip-marker=slow")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        lines2=[
            (
                "ERROR: --skip-marker was given the unregistered marker(s) "
                "slw. Register markers in the 'markers' setting."
            ),
        ],
    )
