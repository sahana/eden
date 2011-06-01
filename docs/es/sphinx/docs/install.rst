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

Configuración
-------------

La plataforma e-cidadania viene casi lista para funcionar, no hay que tocar nada
salvo el fichero `settings.py` y la configuración específica de tu servidor web para
servir el contendio estático.

settings.py
...........

**Configurar la base de datos**::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db/sqlite.db',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }
    
Lo primero de todo será configurar la base de datos. Por defecto, e-cidadania
viene configurado para utilizxar una base de datos local de SQLite3, que puede
servirte para hacer pruebas de forma local si lo necesitas.

Un ejemplo de base de datos en un servidor compartido de DreamHost es este::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'ecidadania_database',
            'USER': 'databaseadmin',
            'PASSWORD': 'somepassword',
            'HOST': 'mysql.ecidadania.org',
            'PORT': '',
        }
    }

**Debug mode**

Debug mode comes activated by default, and in order to star using you e-cidadania
installation in production you'll need to deactivate it in `settings.py`::

    DEBUG = False
    
**Referencia de settings.py**

**DEBUG** (True, False)
    Por defecto el modo debug viene activado. Tras hacer tus pruebas, cámbialo
    a `False`.

**ACCOUNT_ACTIVATION_DAYS** (número)
    Esta variable especifica cuándos días tiene el usuario para activar su
    cuenta desde que recibe el correo de confirmación.

**GOOGLE_MAPS_API_KEY** (hash)
    Llave de la API de Google para poder utilizar la interfaz de mapas. Debes
    crearte una propia a pesar de que e-cidadania venga con una configurada,
    ya que sólo funcionará en el dominio que hayas especificado.

**EMAIL_HOST** (servidor)
    Servidor de correo desde el cual se enviarán los correos a los usuarios.
    
DEFAULT_FROM_EMAIL::

    Dirección por defecto desde la que se enviarán los correos si no se especifica
    otra.
