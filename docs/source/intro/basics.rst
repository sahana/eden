Basic Concepts
==============

This page explains the basic concepts, structure and operations of Sahana Eden, and
introduces the fundamental terminology used throughout this documentation.

Client and Server
-----------------

Sahana Eden is a **web application**, which means it is run as a **server** program
and is accessed remotely by **client** programs connected over the network.

.. image:: client_server.png
   :align: center

Most of the time, the client program will be a **web browser** - but it could
also be a mobile app, or another type of program accessing web services. Many
clients can be connected to the server at the same time.

Client and server communicate using the **HTTP** protocol, in which the client
sends a **request** to the server, the server processes the request and
produces a **response** (e.g. a HTML page) that is sent back to the client,
and then the client processes the response (e.g. by rendering the HTML page
on the screen).

.. note::

   Responding to HTTP requests is Sahana Eden's fundamental mode of operation.

Web2Py and PyDAL
----------------

Sahana Eden builds on the **web2py** web application framework, which consists
of three basic components: a *HTTP server*, the *application runner* and various
libraries, and a *database abstraction layer*.

.. image:: web2py_stack.png
   :align: center

The **HTTP server** (also commonly called "web server") manages client connections.
Web2py comes with a built-in HTTP server (*Rocket*), but production environments
typically deploy a separate front-end HTTP server (e.g. *nginx*) that connects
to web2py through a WSGI plugin or service (e.g. *uWSGI*).

.. image:: web2py_stack_prod.png
   :align: center

The **application runner** (*gluon*) decodes the HTTP request, then calls certain
Python functions in the Sahana Eden application with the request data as input, and
from their output renders the HTTP response. Additionally, *gluon* provides a number
of libraries to generate interactive web contents and process user input.

The **database abstraction layer** (*PyDAL*) provides a generic interface to
the database, as well as a mapping between Python objects and the tables
and records in the database (*ORM, object-relational mapping*). For production
environments, the preferred database back-end is PostgreSQL with the
PostGIS extension, but SQLite and MariaDB/MySQL are also supported.

Application Structure
---------------------

Web2py applications like Sahana Eden implement the MVC (model-view-controller)
application model, meaning that the application code is separated in:

  - **models** defining the data(base) structure,
  - **views** implementing the user interface,
  - **controllers** implementing the logic connecting models and views

This is somewhat reflected by the directory layout of Sahana Eden:

.. image:: directory_layout.png
   :align: center

.. note::

   This directory layout can be somewhat misleading about where certain
   functionality can be found in the code:

   The *controllers* directory contains Python scripts implementing the logic
   of the application. In Sahana Eden, these controllers delegate much of that
   logic to **core** modules.

   The *models* directory contains Python scripts to configure the application
   and define the database structure. In Sahana Eden, the former is largely delegated
   to configuration **templates**, and the latter is reduced to the instantiation
   of a model loader, which then loads the actual data models from **s3db** modules
   if and when they are actually needed.

The Request Cycle
-----------------

Sahana Eden runs in cycles triggered by incoming HTTP requests.

.. image:: request_cycle.png
   :align: center

When an HTTP request is received, web2py parses and translates it into a global
**request** object.

   For instance, the request URI is translated like::

      https://www.example.com/[application]/[controller]/[function]/[args]?[vars]

   ...and its elements stored as properties of the *request* object
   (e.g. *request.controller* and *request.function*). These values determine
   which function of the application is to be executed.

Web2py also generates a global **response** object, which can be written to
in order to set parameters for the eventual HTTP response.

Web2py then runs the Sahana Eden application:

  1. executes all scripts in the *models/* directory in lexical (ASCII) order.

  2. executes the script in the *controllers/* directory that corresponds
     to *request.controller*, and then calls the function defined by that
     script that corresponds to *request.function*.

     E.g. if *request.controller* is "org" and *request.function* is "organisation",
     then the *controllers/org.py* script will be executed, and then the
     *organisation()* function defined in that script will be invoked.

  3. takes the output of the function call to compile the view template
     configured as *response.view*.

These three steps are commonly referred to as the *request cycle*.
