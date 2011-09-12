Instalación
===========

La instalación de e-cidadania es muy simple y se realiza de la misma manera que
cualquier otra plataforma django estándar.

Requisitos
----------

- Apache, nginx, or any other web server with CGI suppport
- FastCGI, CGI, Passenger or other CGI.

**Dependencias**

- django 1.3
- PIL *(Python Imaging Library)*
- python-datetime *(versión 1.5)*
- django-tagging
- django-wysiwyg
- django-grappelli (para la administración)
- feedparser

Puedes instalar todas las dependencias automáticamente con este comando:

::

    # pip install -r requirements.txt

Descargar la plataforma
-----------------------

.. note:: La sección de descargas de la web oficial todavía no está disponible.

Existen numerosas formas de descargar e-cidadania. La más sencilla de todas es
ir a le sección `descargas <http://ecidadania.org/downloads>`_ de la web y bajarse
la última versión estable o de desarrollo, listas para utilizar.

Versión estable
...............

Puedes encontrar la última versión estable en la página de descargas de ecidadania.org::

    http://ecidadania.org/downloads


Versión de desarrollo
.....................

La versión de desarrollo está disponible desde varios sitios. Utilizamos `GIT <http://git-scm.com/>`_
como sistema de control de versiones, asó que tendrás que instalarlo en tu ordenador.

    **Gitorious:** *(repositorio oficial)*::

        git clone git://gitorious.org/e-cidadania/mainline.git

    **GitHub** *(repositorio secundario)*::

        git clone git://github.com/oscarcp/e-cidadania.git

    **Repo.or.cz** *(espejo oficial)*::

        git clone git://repo.or.cz/e_cidadania.git

Instalando con Apache 2
-----------------------

Esta sección está en desarrollo.

Instalando con nginx + FastCGI
-------------------------------

.. note:: The installtion through FastCGI should work for other web servers since
          FastCGI is the one who handles e-cidadania, and the server only serves
          the static content.

The installation with nginx and FastCGI...

This section is in development.

Now you can continue to "Configuration".

Instalación en DreamHost
------------------------

Esta sección está en desarrollo, pero se puede consultar el manual en http://blog.oscarcp.com
