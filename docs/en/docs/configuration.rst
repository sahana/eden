Configuration
=============

The e-cidadania platform is almost ready-to-use adter unpacking, but you will have
to edit the `settings.py` file.

Database
--------

**Configuring the database**::

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
    
First of all will be to set up the database. By default e-cidadania is set up to
use a local SQLite3 database, which will be useful if Lo primero de todo será configurar la base de datos. Por defecto, e-cidadania
viene configurado para utilizar una base de datos local SQLite3, que puede
servirte para hacer pruebas si lo necesitas pero no se debe utilizar bajo ningún
concepto en producción.

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

Debug mode
----------

Debug mode comes activated by default and is strongly recommended to deactivate it
to start using e-cidadania in production. To do it you need to deactivate it in
the `settings.py` file::

    DEBUG = False

User profiles
-------------

*ACCOUNT_ACTIVATION_DAYS* (number)

    This variable specifies how many days the user has to activate the user account
    since he receibes the confirmation e-mail.

*GOOGLE_MAPS_API_KEY* (hash)

    Google API key to use the maps interface. You shall create your own API key even
    if e-cidadania comes with one of his own. That's because the API is domain
    dependant.

E-mail
------

*ADMINS* (list)

    Administrators and e-mail adresses list for the server error notifications. It
    only works if DEBUG = False
    
*EMAIL_HOST* (server)

    Mail server from which e-mails will be sent to the users.
    
*DEFAULT_FROM_EMAIL*

    Default e-mail address from which the mails will be sent it other is not
    specified.

Language
--------

*LANGUAGE_CODE* (language code)

    Default language for the django installation.

Plugins
-------

.. note:: This section is still on development.

