Model Loader *s3db*
===================

The **s3db** model loader provides access to database tables and
other named objects defined in dynamically loaded models.

The model loader can be accessed through :doc:`current </reference/current>`:

.. code-block:: python
   :emphasize-lines: 3

   from gluon import current

   s3db = current.s3db

Accessing Tables and Objects
----------------------------

A table or other object defined in a dynamically loaded data model
can be accessed by name either as attribute or as key of *current.s3db*:

.. code-block:: python
   :caption: Example: accessing the org_organisation table using attribute-pattern

   table = s3db.org_organisation

.. code-block:: python
   :caption: Example: accessing the org_organisation table using key-pattern

   tablename = "org_organisation"
   table = s3db[tablename]

Either pattern will raise an *AttributeError* if the table or object is
not defined, e.g. when the module is disabled.

Both access methods build on the lower-level *table()* method:

.. function:: s3db.table(tablename, default=None, db_only=False)

   Access a named object (usually a Table instance) defined in a
   dynamically loaded model.

   :param str tablename: the name of the table (or object)
   :param default: the default to return if the table (or object) is not defined
   :param bool db_only: return only Table instances, not other objects with the
                        given name

.. note::
   If an *Exception* instance is passed as default, it will be raised
   rather than returned.

Table Settings
--------------

Table settings are used to configure entity-specific behaviors, e.g. forms,
list fields, CRUD callbacks and access rules. The following functions can be
used to manage table settings:

.. function:: s3db.configure(tablename, **attr)

   Add or modify table settings.

   :param str tablename: the name of the table
   :param attr: table settings as key-value pairs

.. code-block:: python
   :caption: Example: configuring table settings

   s3db.configure("org_organisation",
                  insertable = False,
                  list_fields = ["name", "acronym", "website"],
                  )

.. function:: s3db.get_config(tablename, key, default=None)

   Inspect table settings.

   :param str tablename: the name of the table
   :param str key: the settings-key
   :param default: the default value if setting is not defined for the table
   :returns: the current value of the setting, or default

.. code-block:: python
   :caption: Example: inspecting table settings

   if s3db.get_config("org_organisation", "insertable", True):
       # ...
   else:
       # ...

.. function:: s3db.clear_config(tablename, *keys)

   Remove table settings.

   :param str tablename: the name of the table
   :param keys: the keys for the settings to remove

.. code-block:: python
   :caption: Example: removing table settings

   s3db.clear_config("org_organisation", "list_fields")

.. warning::

   If *clear_config* is called without keys, **all** settings for the table
   will be removed!

Declaring Components
--------------------

The *add_components* method can be used to declare :doc:`components </extend/models/basics>`.

.. function:: s3db.add_components(tablename, **links)

   Declare components for a table.

   :param str tablename:  the name of the table
   :param links: component links

.. code-block:: python
   :caption: Example: declaring components

   s3db.add_components("org_organisation",

                       # A 1:n component with foreign key
                       org_office = "organisation_id",

                       # A 1:n component with foreign key, single entry
                       org_facility = {"joinby": "organisation_id",
                                       "multiple": False,
                                       },

                       # A m:n component with link table
                       project_project = {"link": "project_organisation",
                                          "joinby": "organisation_id",
                                          "key": "project_id",
                                          },
                       )

URL Method Handlers
-------------------

.. function:: s3db.set_method(tablename, component=None, method=None, action=None)

   Configure a URL method for a table, or a component in the context of the table

   :param str tablename: the name of the table
   :param str component: component alias
   :param str method: name of the method (to use in URLs)
   :param action: function or other callable to invoke for this method,
                  receives the CRUDRequest instance and controller keyword
                  parameters as arguments

.. code-block:: python
   :caption: Example: defining and configuring a handler for a URL method for a table
   :emphasize-lines: 11

   def check_in_func(r, **attr):
       """ Handler for check_in method """

       # Produce some output...

       # Return output to view
       return {}

   # Configure check_in_func as handler for the "check_in" method
   # (i.e. for URLs like /eden/pr/person/5/check_in):
   s3db.set_method("pr_person", method="check_in", action=check_in_func)

.. tip::

   If a S3Method class is specified as action, it will be instantiated
   when the method is called (lazy instantiation).

.. function:: s3db.get_method(tablename, component=None, method=None)

   Get the handler for a URL method for a table, or a component in the context
   of the table

   :param str tablename: the name of the table
   :param str component: component alias
   :param str method: name of the method
   :returns: the handler configured for the method (or None)

CRUD Callbacks
--------------

.. Topics to cover:
   - onvalidation
   - onaccept

*to be written*
