|project|
=========

Run one ``pytest`` suite against several interchangeable backends
------------------------------------------------------------------

.. code-block:: console

   $ pip install pytest-multi-backend

This requires Python |minimum-python-version|\+.

A "backend" is one way of running the system which the tests exercise.
A suite might run against a real remote service, an in-memory fake of that service, and the same fake behind an HTTP server, and assert the same things about each.
That is how a fake is kept honest.

See :doc:`usage` for how to make a fixture which runs each test once per backend, and :doc:`api-reference` for the details.

Reference
---------

.. toctree::
   :maxdepth: 3

   installation
   usage
   api-reference
   contributing

.. toctree::
   :hidden:

   unreleased
   changelog
   release-process
