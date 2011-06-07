Instalación
===========

La instalación de e-cidadania es muy sencilla y se cumple exactamente igual que
cualquier otra plataforma Django.

Requisitos
----------

- Apache, nginx, o cualquier otro servidor web que soporte CGI
- FastCGI, CGI, Passenger u otro intérprete CGI

**Dependencias**

- django 1.3
- PIL *(Python Imaging Library)*
- python-datetime *(versión 1.5)*
- django-tagging
- django-wysiwyg
- django-grappelli (para la administración)

Puedes instalar todas las dependiencias de forma automática mediante el siguiente comando:

::

    # pip install -r requirements.txt

Descargar la plataforma
-----------------------

Hay diversas formas de descargar e-cidadania. La más sencilla de ellas es
acceder a la página de `Descargas <http://ecidadania.org/downloads>`_ de la web y bajarte la última versión
estable, o la de desarrollo, ya empaquetadas y listas para usar.

Versión estable
...............

Podrás encontrar la últiva versión estable en la página de descargas de ecidadania.org::

    http://ecidadania.org/downloads


Versión de desarrollo
.....................

La versión de desarrollo está disponible desde diversos lugares. Utilizamos `GIT <http://git-scm.com/>`_ como sistema de control de versiones, así que necesitarás tenerlo instalado en tu ordenador.

    **Gitorious:** *(repositorio oficial)*::
    
        git clone git://gitorious.org/e-cidadania/mainline.git

    **GitHub** *(repositorio secundario)*::
    
        git clone git://github.com/oscarcp/e-cidadania.git
    
    **Repo.or.cz** *(mirror oficial)*::
    
        git clone git://repo.or.cz/e_cidadania.git

Instalación con Apache 2
------------------------

Esta sección está en desarrollo.

Instalación con nginx + FastCGI
-------------------------------

.. note:: La instalación mediante FastCGI debería servir para otros servidores web ya que FastCGI es el que se encarga de e-cidadania, y el servidor sólo del contenido estático.

La instalación con nginx y FastCGI...

Esta sección está en desarrollo.
