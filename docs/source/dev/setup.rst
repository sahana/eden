Setting up for Development
==========================

This page describes how you can set up a local Eden instance for
application development on your computer.

.. note::

   This guide assumes that you are working in a Linux environment (shell commands
   are for *bash*).

   If you are working with another operating system, you can still take this as a
   general guideline, but commands may be different, and additional installation
   steps could be required.

   You can use a docker container for development and testing. This is described
   :doc:`here <docker>`.

.. note::

   This guide further assumes that you have *Python* (version 3.11 or later)
   installed, and that you are familiar with the Python programming language.

   Additionally, you will need to have `git <https://git-scm.com/downloads>`_
   installed.

Prerequisites
-------------

Eden requires a couple of Python libraries - which you should install using
the packet manager of your OS (e.g. *apt* on Debian).

Alternatively, where no suitable package exists for your distribution, you
can use *pip* to install the library.

.. note::

   On newer OS versions, installation with *pip* is discouraged as the
   pip-installed packages could interfere with system dependencies. In
   this case, you may have to either use a virtual environment - or run
   pip with ``--break-system-packages``.

As a minimum, *lxml* and *dateutil* must be installed:

.. code-block:: bash

   sudo apt install python3-lxml python3-dateutil

The following are also required for normal operation:

.. code-block:: bash

   sudo apt install python3-requests python3-pyparsing
   sudo apt install python3-shapely python3-geopy
   sudo apt install python3-xlrd python3-xlwt python3-openpyxl
   sudo apt install python3-reportlab

.. note::

   Certain specialist functionality may require additional libraries (e.g.
   *python3-qrcode*). Check the system messages during the first run for
   such optional dependencies.

Installing web2py
-----------------

To install web2py, clone it directly from GitHub:

.. code-block:: bash

   git clone https://github.com/web2py/web2py.git ~/web2py

.. tip::
   You can of course choose any other target location than *~/web2py* for
   the clone - just remember to use the correct path in subsequent commands.

Change into the *web2py* directory, and reset the repository (including
all submodules) to the supported stable version (currently 3.3.3):

.. code-block:: bash

   cd ~/web2py
   git reset --hard 9005306
   git submodule update --init --recursive

.. note::

   Certain versions of web2py+PyDAL may need patching in order to work
   correctly. If a patch is required, it will be published alongside
   the latest Sahana Eden release on `GitHub <https://github.com/sahana/eden/releases>`_.

Installing Eden
---------------

To install Eden, clone it directly from GitHub:

.. code-block:: bash

   git clone --recursive https://github.com/sahana/eden.git ~/eden

.. tip::
   You can of course choose any other target location than *~/eden* for
   the clone - just remember to use the correct path in subsequent commands.

.. _entrance-docker-setup:

Configure Eden as a web2py application by adding a symbolic link
to the *eden* directory under *web2py/applications*:

.. code-block:: bash

   cd ~/web2py/applications
   ln -s ~/eden eden

The name of this symbolic link (*eden*) becomes the web2py application name,
and will later be used in URLs to access the application.

.. tip::
   You can also clone Eden into the *~/web2py/applications/eden*
   directory - then you will not need the symbolic link.

Configuring Eden
----------------

Before running Eden the first time, you need to create a configuration
file. To do so, copy the *000_config.py* template into Eden's *models* folder:

.. code-block:: bash

   cd ~/eden
   cp modules/templates/000_config.py models

Open the *~/eden/models/000_config.py* file in an editor and adjust any
settings as needed.

For development, you do not normally need to change anything, except
setting the following to *True* (or removing the line altogether):

.. code-block:: python
   :caption: Editing models/000_config.py

   FINISHED_EDITING_CONFIG_FILE = True

That said, it normally makes sense to also turn on *debug* mode for
development:

.. code-block:: python
   :caption: Editing models/000_config.py

   settings.base.debug = True

First run
---------

The first start of Eden will set up the database, creating all tables
and populating them with some data.

This is normally done by running the *noop.py* script in the web2py shell:

.. code-block:: bash

   cd ~/web2py
   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/noop.py

This will give a console output similar to this:

.. code-block:: bash
   :caption: Console output during first run

   WARNING:  S3Msg unresolved dependency: pyserial required for Serial port modem usage
   WARNING:  S3MSG unresolved dependency: sgmllib3k required for Feed import on Python 3.x

   *** FIRST RUN - SETTING UP DATABASE ***

   Setting Up System Roles...
   Setting Up Scheduler Tasks...
   Creating Database Tables (this can take a minute)...
   Database Tables Created. (7.41 sec)

   Please be patient whilst the database is populated...

   Importing default/base...
   Imports for default/base complete (1.88 sec)

   Importing default...
   Imports for default complete (1.61 sec)

   Importing default/users...
   Imports for default/users complete (0.05 sec)

   Updating database...
   Location Tree update completed (0.39 sec)
   Demographic Data aggregation completed (0.02 sec)

   Pre-populate complete (3.96 sec)

   Creating indexes...

   *** FIRST RUN COMPLETE ***

You can ignore the *WARNING* messages here about unresolved, optional dependencies.

Starting the server
-------------------

In a development environment, we normally use the built-in HTTP server (*Rocket*)
of web2py, which can be launched with:

.. code-block:: bash

   cd ~/web2py
   python web2py.py --no_gui -a [password]

Replace *[password]* here with a password of your choosing - this password is
needed to access web2py's application manager (e.g. to view error tickets).

Once the server is running, it will give you a localhost URL to access it:

.. code-block:: bash
   :caption: Console output of web2py after launch

   web2py Web Framework
   Created by Massimo Di Pierro, Copyright 2007-2026
   3.3.3-stable+timestamp.2026.04.28.08.03.04
   Database drivers available: sqlite3, psycopg2, imaplib, pymysql, pyodbc

   please visit:
         http://127.0.0.1:8000/
   use "kill -SIGTERM 9630" to shutdown the web2py server

Append the application name *eden* to the URL (http://127.0.0.1:8000/eden),
and open that address in your web browser to access Eden.

The first run will have installed two demo user accounts, namely:

  - `admin@example.com` (a user with the system administrator role)
  - `normaluser@example.com` (an unprivileged user account)

...each with the password `testing`. So you can login and explore the functionality.

Using PostgreSQL
----------------

*to be written*
