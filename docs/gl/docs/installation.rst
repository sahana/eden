Instalación
===========

A instalación de e-cidadania é moi simple e realízase da mesma maneira que
calquera outra plataforma django estándar.

Descargar a plataforma
----------------------

.. note:: A sección de descargas da web oficial aínda non está dispoñible.

Existen numerosas formas de descargar e-cidadania. A máis sinxela de todas é
ir á sección `descargas <http://ecidadania.org/downloads>`_ da web e baixarse
a última versión estable ou de desenvolvemento, listas para utilizar.

Versión estable
...............

Podes encontrar a última versión estable na páxina de descargas de ecidadania.org::

    http://ecidadania.org/downloads


Versión de desenvolvemento
..........................

A versión de desenvolvemento está dispoñible dende varios sitios. Utilizamos `GIT <http://git-scm.com/>`_
como sistema de control de versións, así que terás que instalalo no teu ordenador.

    **Gitorious:** *(repositorio oficial)*::

        git clone git://gitorious.org/e-cidadania/mainline.git

    **GitHub** *(repositorio secundario)*::

        git clone git://github.com/oscarcp/e-cidadania.git

    **Repo.or.cz** *(espello oficial)*::

        git clone git://repo.or.cz/e_cidadania.git

Requisitos
----------

- Python 2.5 o superior
- Apache, nginx, ou outro servidor web con soporte CGI
- FastCGI, CGI, Passenger ou outro CGI

**Dependencias**

- django 1.3
- PIL *(Python Imaging Library)*
- python-datetime *(versión 1.5)*
- django-tagging
- django-wysiwyg
- django-grappelli (para a administración)
- feedparser


Instalar dependencias
---------------------

Podes instalar todas as dependencias automaticamente con este comando:

::

    # pip install -r requirements.txt

Se non dispós do programa *pip* tamén podes instalar as dependencias a través
do programa *easy_install*.

