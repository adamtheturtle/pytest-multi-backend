|Build Status| |PyPI|

pytest-multi-backend
====================

.. contents::
   :local:

Run one ``pytest`` suite against several interchangeable backends.

A "backend" is one way of running the system which the tests exercise.
A suite might run against a real remote service, an in-memory fake of that service, and the same fake behind an HTTP server, and assert the same things about each.
That is how a fake is kept honest.

Installation
------------

.. code-block:: shell

    pip install pytest-multi-backend

This requires Python |minimum-python-version|\+.

Usage
-----

Backends are the members of an ``Enum``.
The member name, in lower case, is what ``--skip-backend`` takes to skip the backend.
The member value is the ID which ``pytest`` shows for it.

``backend_fixture`` makes a fixture which runs each test which uses it once per backend.
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
    ) -> Generator[None, None, None]:
        """Set a backend up, yield while the test runs, then tear it down.

        Anything else the setup needs comes from
        ``request.getfixturevalue``.
        """
        if backend is Backend.FAKE:
            # Start the fake here.
            yield
            # Stop the fake here.
            return
        # Prepare the real service here.
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

Skipping backends
~~~~~~~~~~~~~~~~~

Give ``--skip-backend`` the lower case name of a backend to skip every test against it.
Give it once per backend to skip.

.. code-block:: console

   $ pytest --skip-backend=real

Tests against a skipped backend are skipped, not deselected, so a run which skips a backend still reports the tests which would have used it.
The setup function is not called for a skipped backend.
Giving a name which no fixture has a backend for is an error, so a mistyped name does not silently run tests against a backend you meant to avoid.

Skipping marked tests
~~~~~~~~~~~~~~~~~~~~~

Give ``--skip-marker`` the name of a registered marker to skip every test which carries it.
Give it once per marker to skip.

.. code-block:: console

   $ pytest --skip-marker=requires_docker

Unlike ``-m "not requires_docker"``, this skips rather than deselects, so the skipped tests are still reported.
The marker must be registered in the ``markers`` setting, as ``--strict-markers`` requires, and giving an unregistered marker is an error.

Full documentation
------------------

See the `full documentation <https://adamtheturtle.github.io/pytest-multi-backend/>`__.

.. |Build Status| image:: https://github.com/adamtheturtle/pytest-multi-backend/actions/workflows/test.yml/badge.svg?branch=main
   :target: https://github.com/adamtheturtle/pytest-multi-backend/actions
.. |PyPI| image:: https://badge.fury.io/py/pytest-multi-backend.svg
    :target: https://badge.fury.io/py/pytest-multi-backend
.. |minimum-python-version| replace:: 3.11
