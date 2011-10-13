Instalación
===========

La instalación de e-cidadania es muy simple y se realiza de la misma manera que
cualquier otra plataforma django estándar.

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
como sistema de control de versiones, así que tendrás que instalarlo en tu ordenador.

    **Gitorious:** *(repositorio oficial)*::

        git clone git://gitorious.org/e-cidadania/mainline.git

    **GitHub** *(repositorio secundario)*::

        git clone git://github.com/oscarcp/e-cidadania.git

    **Repo.or.cz** *(espejo oficial)*::

        git clone git://repo.or.cz/e_cidadania.git

Requisitos
----------

- Python 2.5 o superior
- Apache, nginx, u otro servidor web con soporte CGI
- FastCGI, CGI, Passenger u otro CGI

**Dependencias**

- django 1.3
- PIL *(Python Imaging Library)*
- python-datetime *(versión 1.5)*
- django-tagging
- django-wysiwyg
- django-grappelli (para la administración)
- feedparser


Instalar dependencias
---------------------

Puedes instalar todas las dependencias automáticamente con este comando:

::

    # pip install -r requirements.txt

Si no dispones del programa *pip* también puedes instalar las dependencias a través
del programa *easy_install*.

