Installation
============

e-cidadnaia installation is very simple and is the same as any other django
platform.

Requirements
------------

- Apache, nginx, or any other web server with CGI suppport
- FastCGI, CGI, Passenger or other CGI.

**Dependencies**

- django 1.3
- PIL *(Python Imaging Library)*
- python-datetime *(versión 1.5)*
- django-tagging
- django-wysiwyg
- django-grappelli (para la administración)

You can install all the required dependencies automatically with this command:

::

    # pip install -r requirements.txt

Downloading platform
--------------------

The are several ways to download e-cidadania. The most simple of them is going to
the `downloads <http://ecidadania.org/downloads>`_ page in the website and download
the latest stable versions, or development, ready to use.

Stable version
...............

You can find the latest stable version in the download page in ecidadania.org::

    http://ecidadania.org/downloads


Development version
...................

Development version is available through various places. We use `GIT <http://git-scm.com/>`_
as control version system, so you will have to install it in your computer.

    **Gitorious:** *(official repository)*::

        git clone git://gitorious.org/e-cidadania/mainline.git

    **GitHub** *(secondary repository)*::

        git clone git://github.com/oscarcp/e-cidadania.git

    **Repo.or.cz** *(official mirror)*::

        git clone git://repo.or.cz/e_cidadania.git

Installing with Apache 2
------------------------

Esta sección está en desarrollo.

Installing with nginx + FastCGI
-------------------------------

.. note:: The installtion through FastCGI should work for other web servers since
          FastCGI is the one who handles e-cidadania, and the server only serves
          the static content.

The installation with nginx and FastCGI...

This section is in development.

