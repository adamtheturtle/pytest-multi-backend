Usage
=====

Making a backend fixture
------------------------

Backends are the members of an :class:`~enum.Enum`.
The member name, in lower case, is what ``--skip-backend`` takes to skip the backend.
The member value is the ID which ``pytest`` shows for it.

:func:`~pytest_multi_backend.backend_fixture` makes a fixture which runs each test which uses it once per backend.
Assign the fixture to a module-level name in a ``conftest.py`` for ``pytest`` to find it.

.. code-block:: python

    """Run each test against the real service and against a fake."""

    from collections.abc import Generator
    from enum import Enum

    import pytest

    from pytest_multi_backend import backend_fixture


    class Backend(Enum):
        """The ways of running the service under test."""

        REAL = "Real service"
        FAKE = "In memory fake"


    def _setup_backend(
        *,
        backend: Backend,
        request: pytest.FixtureRequest,
    ) -> Generator[None]:
        """Set a backend up, yield while the test runs, then tear it down.

        Anything else the setup needs comes from
        ``request.getfixturevalue``.
        """
        monkeypatch = request.getfixturevalue(argname="monkeypatch")
        if backend is Backend.FAKE:
            # Start the fake here, and point the code under test at it.
            monkeypatch.setenv(name="SERVICE_URL", value="http://localhost:8080")
            yield
            # Stop the fake here.
            return
        monkeypatch.setenv(name="SERVICE_URL", value="https://example.com")
        yield


    fixture_backend = backend_fixture(
        name="backend",
        backends=list(Backend),
        setup_for=_setup_backend,
    )

A test which requests the fixture runs once per backend, and gets the backend it is running against:

.. code-block:: python

    """A test which runs against each backend."""

    from enum import Enum


    def test_something(backend: Enum) -> None:
        """Assert the same thing about every backend."""
        assert backend.value

Several fixtures can share an :class:`~enum.Enum`.
A suite might have one fixture for every backend, used by tests which verify a fake against the real service, and another for the fakes alone, used by tests which need to control the state of the service.

Skipping backends
-----------------

Give ``--skip-backend`` the lower case name of a backend to skip every test against it.
Give it once per backend to skip.

.. code-block:: console

   $ pytest --skip-backend=real

Tests against a skipped backend are skipped, not deselected, so a run which skips a backend still reports the tests which would have used it.
The setup function is not called for a skipped backend.
Giving a name which no fixture has a backend for is an error, so a mistyped name does not silently run tests against a backend you meant to avoid.

Skipping marked tests
---------------------

Give ``--skip-marker`` the name of a registered marker to skip every test which carries it.
Give it once per marker to skip.

.. code-block:: console

   $ pytest --skip-marker=requires_docker

Unlike ``-m "not requires_docker"``, this skips rather than deselects, so the skipped tests are still reported.
The marker must be registered in the ``markers`` setting, as ``--strict-markers`` requires, and giving an unregistered marker is an error.
