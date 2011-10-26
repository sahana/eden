.. e-cidadania documentation master file, created by
   sphinx-quickstart on Mon Jan  3 11:34:17 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

e-cidadania documentation
=========================

**e-cidadania** es una plataforma de e-democracia hecha con software abierto
para la participación ciudadana. Las características clave son: un sistema de
propuestas, un revolucionario sistema de debate ordenado, repositorio de documentos,
informes autogenerados y perfiles avanzaqdos de usuario entre otras cosas como
geolocalización y mensajería.

Esta plataforma está basada en el framework `django <http://www.djangoproject.com>`_ 
y algunas librerías externas.

|Models|_

.. |Models| image:: images/models.png
.. _Models: http://postimage.org/image/z7b8s72c/full/

.. warning:: e-cidadania está en desarrollo, y por ello algunos componentes pueden
             variar sus carcaterísticas, especialmente los modelos de datos y
             esta documentación.


Instalación y configuración
---------------------------

.. toctree::
    :maxdepth: 2

    docs/installation
    docs/configuration
    docs/deployment
    
Manuales
--------

.. toctree::
    :maxdepth: 3
    
    docs/usermanual
    docs/adminmanual

Apariencia / Temas
------------------

.. toctree::
    :maxdepth: 2

    theming/themes

Desarrollo
----------

.. toctree::
    :maxdepth: 2

    dev/styleguide
    dev/useraccounts
    dev/modules
    dev/documenting
    dev/i18n

Referencia (inglés)
-------------------

.. toctree::
    :maxdepth: 2

    reference/calendar
    reference/debate
    reference/spaces
    reference/proposals
    reference/news

Colofón
=======

Conseguir ayuda
---------------

- Prueba a mirar en el `PUF <http://app.ecidadania.org/faq>`_ (Preguntas de Uso Frecuente).
- Listas de correo de e-cidadania

  * ecidadania-users@freelists.org
  * ecidadania-dev@freelists.org
  * ecidadania-es@freelists.org

- Archiva un informe de error en el `bug tracker <http://dev.ecidadania.org>`_.

.. toctree::
    :maxdepth: 1
    
    authors
