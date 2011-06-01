Configuración
=============

La plataforma e-cidadania viene casi lista para funcionar, no hay que tocar nada
salvo el fichero `settings.py` y la configuración específica de tu servidor web para
servir el contendio estático.

settings.py
-----------

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

**Modo Debug**

El modo debug viene activado por defecto y se recomienda encarecidamente
desactivarlo para comenzar a utilizar e-cidadania en producción. Para ello
hay que desactivarlo en el fichero `settings.py`::

    DEBUG = False

**Otras opciones de settings.py**

*ACCOUNT_ACTIVATION_DAYS* (número)
    Esta variable especifica cuándos días tiene el usuario para activar su
    cuenta desde que recibe el correo de confirmación.

*GOOGLE_MAPS_API_KEY* (hash)
    Llave de la API de Google para poder utilizar la interfaz de mapas. Debes
    crearte una propia a pesar de que e-cidadania venga con una configurada,
    ya que sólo funcionará en el dominio que hayas especificado.

*EMAIL_HOST* (servidor)
    Servidor de correo desde el cual se enviarán los correos a los usuarios.
    
*DEFAULT_FROM_EMAIL*
    Dirección por defecto desde la que se enviarán los correos si no se especifica
    otra.