Configuración
=============

La plataforma e-cidadania viene casi lista para funcionar tan pronto la
descargues, pero aún te queda editar el archivo `settings.py`.

Base de datos (BDD)
-------------------

**Configurando la base de datos**::

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
    
Lo primero de todo es configurar la base de datos. Por defecto e-cidadania viene
configurado para utilizar una base de datos local de tipo SQLite 3, que te puede
resultar útil para realizar pruebas antes de poner la plataforma en producción,
pero que deberás cambiar tan pronto como termines las pruebas.

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

Modo Debug
----------

El modo debug viene activado por defecto y se recomienda encarecidamente
desactivarlo para comenzar a utilizar e-cidadania en producción. Para ello
hay que desactivarlo en el fichero `settings.py`::

    DEBUG = False

Perfiles de usuario
-------------------

*ACCOUNT_ACTIVATION_DAYS* (número)

    Esta variable especifica cuándos días tiene el usuario para activar su
    cuenta desde que recibe el correo de confirmación.

*GOOGLE_MAPS_API_KEY* (hash)

    Llave de la API de Google para poder utilizar la interfaz de mapas. Debes
    crearte una propia a pesar de que e-cidadania venga con una configurada,
    ya que sólo funcionará en el dominio que hayas especificado.

Correo electrónico
------------------

*ADMINS* (lista)

    Lista de adminsitradores y cuentas de correo para la notificación
    de errores del servidor. Sólo funciona si DEBUG = False
    
*EMAIL_HOST* (servidor)

    Servidor de correo desde el cual se enviarán los correos a los usuarios.
    
*DEFAULT_FROM_EMAIL*

    Dirección por defecto desde la que se enviarán los correos si no se especifica
    otra.

Idioma
------

*LANGUAGE_CODE* (código de idioma)

    Idioma con el cual funcionará django por defecto.

Plugins
-------

.. note:: Esta sección está sin redactar.

