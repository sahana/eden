Installation
============

e-cidadania installation is very simple and is done almost in the same as any
other django platforms.

Requirements
------------

- Apache, nginx, or any other web server with CGI suppport
- FastCGI, CGI, Passenger or other CGI.

**Dependencies**

- Python 2.7 or later (not 3.x series)
- django 1.4
- PIL *(Python Imaging Library)*
- python-datetime *(version 1.5)*
- django-tagging
- django-grappelli
- feedparser
- pyyaml

You can install all the required dependencies automatically with this command:

::

    # pip install -r requirements.txt

Downloading platform
--------------------

Official download page
......................

.. note:: The download section in the official website is not available yet.

The are several ways to download e-cidadania. The most simple of them is going to
the `downloads <http://ecidadania.org/downloads>`_ page in the website and download
the latest stable or development versions, ready to use.

GitHub packages
...............

Other way of downloading it is through the Github downloads page, which
autogenerates a .zip and .tar.gz files based on the repository tags. You can
find it in:

::

    https://github.com/cidadania/e-cidadania/tags

From repository
...............

See :ref:`dev-version`

Stable version
..............

You can find the latest stable version in the download page in ecidadania.org::

    http://ecidadania.org/en/downloads

.. _dev-version:

Development version
...................

Development version is available through various places. We use `GIT <http://git-scm.com/>`_
as version control system, so you will have to install it in your computer.

    **GitHub** *(official repository)*::

        git clone git://github.com/cidadania/e-cidadania.git

    **Gitorious:** *(secondary repository)*::

        git clone git://gitorious.org/e-cidadania/mainline.git

    **Repo.or.cz** *(official mirror)*::

        git clone git://repo.or.cz/e_cidadania.git
        

Installing
----------

There is no proper installation process in e-cidadania, you just need to copy
the *src/* directory to the folder where you want it to be, and after that
configure in your CGI server how to execute it.

In the case you want to do some testing of the e-cidadania platform before getting
into proper deployment, you just hace to copy the *src/* directory and execute
the following commands inside it since e-cidadania comes by default configured
in a development environment.::

    ./manage.py syncdb # This will create all the database objects
    
    ./manage.py collectstatic # This will copy all the static content to *static/*
    
    ./manage.py runserver

This last command will execute the development server in the port 8000 of your
machine, so you just need to type **localhost:8000" inside a web browser.

Now you can continue to :doc:`configuration`
