About Templates
===============

Global Config
-------------

Many features and behaviors of Sahana Eden can be controlled by settings.

These settings are stored in a global *S3Config* instance - which is accessible
through :doc:`current </reference/current>` as *current.deployment_settings*.

.. code-block:: python

   from gluon import current

   settings = current.deployment_settings

.. note::
   In the models and controllers context, *current.deployment_settings* is
   accessible simply as *settings*.

Deployment Settings
-------------------

*S3Config* comes with meaningful defaults where possible.

However, some settings will need to be adjusted to configure the application
for a particular system environment - or to enable, disable, configure,
customize or extend features in the specific context of the deployment.

This configuration happens in a machine-specific configuration file:

   **models/000_config.py**

.. note::

   *models/000_config.py is not part of the code base, and must be created
   before the application can be started. An annotated example can be found
   in the *modules/templates* directory.

The configuration file is a Python script that is executed for every request cycle:

.. code-block:: python
   :caption: models/000_config.py (partial example)
   :emphasize-lines: 11,36

   # -*- coding: utf-8 -*-

   """
       Machine-specific settings
   """

   # Remove this line when this file is ready for 1st run
   FINISHED_EDITING_CONFIG_FILE = True

   # Select the Template
   settings.base.template = "MYAPP"

   # Database settings
   settings.database.db_type = "postgres"
   #settings.database.host = "localhost"
   #settings.database.port = 3306
   settings.database.database = "myapp"
   #settings.database.username = "eden"
   #settings.database.password = "password"

   # Do we have a spatial DB available?
   settings.gis.spatialdb = True

   settings.base.migrate = True
   #settings.base.fake_migrate = True

   settings.base.debug = True
   #settings.log.level = "WARNING"
   #settings.log.console = False
   #settings.log.logfile = None
   #settings.log.caller_info = True

   # =============================================================================
   # Import the settings from the Template
   #
   settings.import_template()

   # =============================================================================
   # Over-rides to the Template may be done here
   #
   # After 1st_run, set this for Production
   #settings.base.prepopulate = 0

   # =============================================================================
   VERSION = 1

   # END =========================================================================

Templates
---------

Deployment configurations use configuration **templates**, which provide
pre-configured settings, customizations and extensions suitable for a concrete
deployment scenario. The example above highlights how these templates are applied.

.. important::
   Implementing configuration **templates** is the primary strategy to build
   applications with Sahana Eden.

Templates are Python packages located in the *modules/templates* directory:

.. image:: template_location.png
   :align: center

Each template package must contain a module *config.py* which defines
a *config*-function :

.. code-block:: python
   :caption: modules/templates/MYAPP/config.py

   def config(settings):

       T = current.T

       settings.base.system_name = T("My Application")
       settings.base.system_name_short = T("MyApp")

       ...

This *config* function is called from *models/000_config.py* (i.e. for every
request cycle) with the *current.deployment_settings* instance as parameter,
so that it can modify the global settings as needed.

.. note::
   The template directory must also contain an *__init__.py* file (which can
   be empty) in order to become a Python package!

Cascading Templates
-------------------

It is possible for a deployment configuration to apply multiple templates
in a cascade, so that they complement each other:

.. code-block:: python
   :caption: Cascading templates (in models/000_config.py)

   # Select the Template
   settings.base.template = ("locations.DE", "MYAPP")

This is useful to separate e.g. locale-specific settings from use-case
configurations, so that both can be reused independently across multiple
deployments.
