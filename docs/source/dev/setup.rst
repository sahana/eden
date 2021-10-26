Setting up for Development
==========================

This page describes how you can set up a local Sahana Eden instance for
application development on your computer.

.. note::

   This guide assumes that you are working in a Linux environment (shell commands
   are for *bash*).

   If you are working with another operating system, you can still take this as a
   general guideline, but commands may be different, and additional installation
   steps could be required.

.. note::

   This guide further assumes that you have *Python* (version 3.6 or later)
   installed, which comes bundled with the *pip* package installer - and that
   you are familiar with the Python programming language.

   Additionally, you will need to have `git <https://git-scm.com/downloads>`_
   installed.

Prerequisites
-------------

Sahana Eden requires a couple of Python libraries, which can be installed
with the *pip* installer.

As a minimum, *lxml* and *python-dateutil* must be installed:

.. code-block:: bash

   sudo pip install lxml python-dateutil

The following are also required for normal operation:

.. code-block:: bash

   sudo pip install pyparsing requests xlrd xlwt openpyxl reportlab shapely geopy

Some specialist functionality may require additional libraries, e.g.:

.. code-block:: bash

   sudo pip install qrcode docx-mailmerge

.. tip::

   The above commands use `sudo pip` to install the libraries globally.
   If you want to install them only in your home directory, you can
   omit `sudo`.

Installing web2py
-----------------

To install web2py, clone it directly from GitHub:

.. code-block:: bash

   git clone --recursive https://github.com/web2py/web2py.git ~/web2py

.. tip::
   You can of course choose any other target location than *~/web2py* for
   the clone - just remember to use the correct path in subsequent commands.

Change into the *web2py* directory, and reset the repository (including
all submodules) to the supported stable version (currently 2.21.2):

.. code-block:: bash

   cd ~/web2py
   git reset --hard 3190585
   git submodule update --recursive

Installing Sahana Eden
----------------------

To install Sahana Eden, clone it directly from GitHub:

.. code-block:: bash

   git clone --recursive https://github.com/sahana/eden.git ~/eden

.. tip::
   You can of course choose any other target location than *~/eden* for
   the clone - just remember to use the correct path in subsequent commands.

Configure Sahana Eden as a web2py application by adding a symbolic link
to the *eden* directory under *web2py/applications*:

.. code-block:: bash

   cd ~/web2py/applications
   ln -s ~/eden eden

The name of this symbolic link (*eden*) becomes the web2py application name,
and will later be used in URLs to access the application.

.. tip::
   You can also clone Sahana Eden into the *~/web2py/applications/eden*
   directory - then you will not need the symbolic link.

Configuring Sahana Eden
-----------------------

Before running Sahana Eden the first time, you need to create a configuration
file. To do so, copy the *000_config.py* template into Sahana Eden's *models* folder:

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

The first start of Sahana Eden will set up the database, creating all tables
and populating them with some data.

This is normally done by running the *noop.py* script in the web2py shell:

.. code-block:: bash

   cd ~/web2py
   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/noop.py

This will give a console output similar to this:

.. code-block:: bash
   :caption: Console output during first run

   WARNING:  S3Msg unresolved dependency: pyserial required for Serial port modem usage
   WARNING:  Setup unresolved dependency: ansible required for Setup Module
   WARNING: Error when loading optional dependency: google-api-python-client
   WARNING: Error when loading optional dependency: translate-toolkit

   *** FIRST RUN - SETTING UP DATABASE ***

   Setting Up System Roles...
   Setting Up Scheduler Tasks...
   Creating Database Tables (this can take a minute)...
   Database Tables Created. (3.74 sec)

   Please be patient whilst the database is populated...

   Importing default/base...
   Imports for default/base complete (1.99 sec)

   Importing default...
   Imports for default complete (5.20 sec)

   Importing default/users...
   Imports for default/users complete (0.04 sec)

   Updating database...
   Location Tree update completed (0.63 sec)
   Demographic Data aggregation completed (0.01 sec)

   Pre-populate complete (7.90 sec)

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
   Created by Massimo Di Pierro, Copyright 2007-2021
   Version 2.21.1-stable+timestamp.2020.11.27.18.21.43
   Database drivers available: sqlite3, MySQLdb, psycopg2, imaplib, pymysql, pyodbc

   please visit:
           http://127.0.0.1:8000/
   use "kill -SIGTERM 8455" to shutdown the web2py server

Append the application name *eden* to the URL (http://127.0.0.1:8000/eden),
and open that address in your web browser to access Sahana Eden.

The first run will have installed two demo user accounts, namely:

  - `admin@example.com` (a user with the system administrator role)
  - `normaluser@example.com` (an unprivileged user account)

...each with the password `testing`. So you can login and explore the functionality.

Using PostgreSQL
----------------

*to be written*
