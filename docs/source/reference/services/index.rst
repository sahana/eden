Services
========

Services are thread-local global singleton objects, instantiated during
the *models* run.

They can be accessed through :doc:`current </reference/current>` , e.g.:

.. code-block:: python

   from gluon import current

   s3db = current.s3db

This section describes the services, and their most relevant functions.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Model Loader (s3db) <s3db>
   Authorization (auth) <auth>
   Mapping (gis) <gis>
   Messaging (msg) <msg>
   XML Codec (xml) <xml>
