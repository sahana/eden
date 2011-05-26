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

.. warning:: Esta sección no está terminada!

Descargar la plataforma
-----------------------

Hay diversas formas de descargar e-cidadania. La más sencilla de ellas es
acceder a la página de `Descargas`_ de la web y bajarte la última versión
estable, o la de desarrollo, ya empaquetadas y listas para usar.

.. _Descargas: http://ecidadania.org/downloads

**Versión estable**::

    http://ecidadania.org/downloads

Sin embargo, puede que quieras probar la ultimísima versión del programa
en cuyo caso tendrás que descargarte el código fuente del repositorio git que
se encuentra en gitorious:

**Versión de desarrollo**::

    git clone git://gitorious.org/e-cidadania/mainline.git

Y con eso ya tendriamos una copia del programa. Suponemos que si sabes
manejar git, no necesitarás más ayuda, pero en cualquier caso puedes
consultarnos en las listas de correo :-)

Preparar el entorno
-------------------

e-cidadania no necesita de una configuracuión extremadamente compleja,
aunque actualmente tiene que ser realizada a meno y puede llevar algo de
tiempo.

Pruebas
-------
