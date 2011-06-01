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

Piedes instalar todas las dependiencias de forma automática mediante el siguiente comando:

::

    # pip install -r requirements.txt

.. warning:: Esta sección no está terminada!

Descargar la plataforma
-----------------------

Hay diversas formas de descargar e-cidadania. La más sencilla de ellas es
acceder a la página de `Descargas`_ de la web y bajarte la última versión
estable, o la de desarrollo, ya empaquetadas y listas para usar.

.. _Descargas: http://ecidadania.org/downloads

Versión estable
...............

Podrás encontrar la últiva versión estable en la página de descargas de ecidadania.org::

    http://ecidadania.org/downloads


Versión de desarrollo
.....................

La versión de desarrollo está disponible desde diversos lugares:

**Gitorious:** *(repositorio oficial)*::
    
    git clone git://gitorious.org/e-cidadania/mainline.git

**GitHub** *(repositorio secundario)*::
    
    git clone git://github.com/oscarcp/e-cidadania.git
    
**Repo.or.cz** *(mirror oficial)*::
    
    git clone git://repo.or.cz/e_cidadania.git

Y con eso ya tendriamos una copia del programa. Suponemos que si sabes
manejar git, no necesitarás más ayuda, pero en cualquier caso puedes
consultarnos en las listas de correo :-)