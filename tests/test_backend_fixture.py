"""Tests for ``backend_fixture`` and ``--skip-backend``."""

import textwrap

import pytest

# A ``conftest.py`` which makes a fixture for two backends, and logs
# what each backend's setup and teardown does to a file which the test
# outside ``pytester`` can read.
_CONFTEST = textwrap.dedent(
    text='''\
    """Fixtures for two backends."""

    from collections.abc import Generator
    from enum import Enum
    from pathlib import Path

    import pytest

    from pytest_multi_backend import backend_fixture


    class Backend(Enum):
        """Backends for tests."""

        REAL = "Real service"
        FAKE = "In memory fake"


    def _log(*, request: pytest.FixtureRequest, message: str) -> None:
        """Append a line to the log file in the test directory."""
        log = Path(request.config.rootpath) / "log.txt"
        with log.open(mode="a", encoding="utf-8") as log_file:
            log_file.write(message + "\\n")


    def _setup(
        *,
        backend: Backend,
        request: pytest.FixtureRequest,
    ) -> Generator[None]:
        """Set a backend up, and log the steps."""
        _log(request=request, message=f"setup {backend.name}")
        yield
        _log(request=request, message=f"teardown {backend.name}")


    fixture_backend = backend_fixture(
        name="backend",
        backends=list(Backend),
        setup_for=_setup,
    )
    ''',
)

_TEST_FILE = textwrap.dedent(
    text='''\
    """A test which runs against each backend."""

    from enum import Enum
    from pathlib import Path

    import pytest


    def test_backend(
        backend: Enum,
        request: pytest.FixtureRequest,
    ) -> None:
        """Log the backend which the test is running against."""
        log = Path(request.config.rootpath) / "log.txt"
        with log.open(mode="a", encoding="utf-8") as log_file:
            log_file.write(f"test {backend.name}\\n")
    ''',
)


def test_runs_once_per_backend(*, pytester: pytest.Pytester) -> None:
    """Each test runs once per backend.

    The fixture yields the backend, the backend is set up before the
    test and torn down after it, and the backend's value is the ID
    which ``pytest`` shows.
    """
    pytester.makeconftest(source=_CONFTEST)
    pytester.makepyfile(test_example=_TEST_FILE)

    result = pytester.runpytest("--verbose")

    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        lines2=[
            "*test_example.py::test_backend[[]Real service[]] PASSED*",
            "*test_example.py::test_backend[[]In memory fake[]] PASSED*",
        ],
    )
    log = pytester.path / "log.txt"
    assert log.read_text(encoding="utf-8").splitlines() == [
        "setup REAL",
        "test REAL",
        "teardown REAL",
        "setup FAKE",
        "test FAKE",
        "teardown FAKE",
    ]


def test_skip_backend(*, pytester: pytest.Pytester) -> None:
    """``--skip-backend`` skips, rather than deselects, the tests against
    the backend, and the backend is not set up for them.
    """
    pytester.makeconftest(source=_CONFTEST)
    pytester.makepyfile(test_example=_TEST_FILE)

    result = pytester.runpytest("--skip-backend=real", "--verbose", "-rs")

    result.assert_outcomes(passed=1, skipped=1)
    result.stdout.fnmatch_lines(
        lines2=[
            "*test_example.py::test_backend[[]Real service[]] SKIPPED*",
            "*test_example.py::test_backend[[]In memory fake[]] PASSED*",
            "*--skip-backend=real was given*",
        ],
    )
    log = pytester.path / "log.txt"
    assert log.read_text(encoding="utf-8").splitlines() == [
        "setup FAKE",
        "test FAKE",
        "teardown FAKE",
    ]


def test_skip_multiple_backends(*, pytester: pytest.Pytester) -> None:
    """``--skip-backend`` can be given once per backend to skip."""
    pytester.makeconftest(source=_CONFTEST)
    pytester.makepyfile(test_example=_TEST_FILE)

    result = pytester.runpytest(
        "--skip-backend=real",
        "--skip-backend=fake",
    )

    result.assert_outcomes(skipped=2)
    assert not (pytester.path / "log.txt").exists()


def test_skip_unknown_backend(*, pytester: pytest.Pytester) -> None:
    """Giving ``--skip-backend`` a backend which no fixture was made for
    is an error which names the known backends.

    This runs ``pytest`` in a subprocess so that the known backends
    are only those of this test's fixtures.
    """
    pytester.makeconftest(source=_CONFTEST)
    pytester.makepyfile(test_example=_TEST_FILE)

    result = pytester.runpytest_subprocess("--skip-backend=nonexistent")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        lines2=[
            (
                "ERROR: --skip-backend was given the unknown backend(s) "
                "nonexistent. Known backends: fake, real."
            ),
        ],
    )


def test_skip_backend_without_fixtures(*, pytester: pytest.Pytester) -> None:
    """Giving ``--skip-backend`` when no backend fixture has been made
    is an error which says so.

    This runs ``pytest`` in a subprocess so that no other test's
    fixtures are known.
    """
    pytester.makepyfile(
        test_example=textwrap.dedent(
            text='''\
            """A test which uses no backend."""


            def test_nothing() -> None:
                """Pass."""
            ''',
        ),
    )

    result = pytester.runpytest_subprocess("--skip-backend=real")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        lines2=[
            (
                "ERROR: --skip-backend was given the unknown backend(s) "
                "real. Known backends: none; no backend fixture has been "
                "made."
            ),
        ],
    )


def test_setup_uses_other_fixtures(*, pytester: pytest.Pytester) -> None:
    """The setup function can use other fixtures through ``request``."""
    pytester.makeconftest(
        source=textwrap.dedent(
            text='''\
            """A backend fixture whose setup uses another fixture."""

            from collections.abc import Generator
            from enum import Enum

            import pytest

            from pytest_multi_backend import backend_fixture


            class Backend(Enum):
                """Backends for tests."""

                ONLY = "The only backend"


            @pytest.fixture(name="greeting")
            def fixture_greeting() -> str:
                """A fixture which the backend setup uses."""
                return "hello"


            def _setup(
                *,
                backend: Backend,
                request: pytest.FixtureRequest,
            ) -> Generator[None]:
                """Set the backend up with the value of another fixture."""
                greeting = request.getfixturevalue(argname="greeting")
                message = f"{greeting} {backend.name}"
                request.config.stash[GREETING_KEY] = message
                yield


            GREETING_KEY = pytest.StashKey[str]()

            fixture_backend = backend_fixture(
                name="backend",
                backends=[Backend.ONLY],
                setup_for=_setup,
            )
            ''',
        ),
    )
    pytester.makepyfile(
        test_example=textwrap.dedent(
            text='''\
            """A test which checks what the backend setup did."""

            from enum import Enum

            import pytest

            from conftest import GREETING_KEY


            def test_setup_ran(
                backend: Enum,
                request: pytest.FixtureRequest,
            ) -> None:
                """The setup function used the other fixture."""
                assert backend.name == "ONLY"
                assert request.config.stash[GREETING_KEY] == "hello ONLY"
            ''',
        ),
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)


def test_shared_backend_names(*, pytester: pytest.Pytester) -> None:
    """A backend name given to ``--skip-backend`` skips that backend for
    every fixture which has a backend of that name.
    """
    pytester.makeconftest(
        source=textwrap.dedent(
            text='''\
            """Two fixtures with a backend in common."""

            from collections.abc import Generator
            from enum import Enum

            import pytest

            from pytest_multi_backend import backend_fixture


            class Backend(Enum):
                """Backends for tests."""

                REAL = "Real service"
                FAKE = "In memory fake"


            def _setup(
                *,
                backend: Backend,
                request: pytest.FixtureRequest,
            ) -> Generator[None]:
                """Set nothing up."""
                del backend
                del request
                yield


            fixture_verify_fake = backend_fixture(
                name="verify_fake",
                backends=list(Backend),
                setup_for=_setup,
            )

            fixture_fake_only = backend_fixture(
                name="fake_only",
                backends=[Backend.FAKE],
                setup_for=_setup,
            )
            ''',
        ),
    )
    pytester.makepyfile(
        test_example=textwrap.dedent(
            text='''\
            """Tests which use each fixture."""

            from enum import Enum


            def test_verify_fake(verify_fake: Enum) -> None:
                """Use the fixture with both backends."""
                del verify_fake


            def test_fake_only(fake_only: Enum) -> None:
                """Use the fixture with one backend."""
                del fake_only
            ''',
        ),
    )

    result = pytester.runpytest("--skip-backend=fake", "--verbose")

    result.assert_outcomes(passed=1, skipped=2)
    result.stdout.fnmatch_lines(
        lines2=[
            "*test_verify_fake[[]Real service[]] PASSED*",
            "*test_verify_fake[[]In memory fake[]] SKIPPED*",
            "*test_fake_only[[]In memory fake[]] SKIPPED*",
        ],
    )


def test_help(*, pytester: pytest.Pytester) -> None:
    """The options are documented in ``--help``."""
    result = pytester.runpytest("--help")

    result.stdout.fnmatch_lines(
        lines2=[
            "multi-backend:",
            "*--skip-backend=BACKEND*",
            "*--skip-marker=MARKER*",
        ],
    )
