Configuración
=============

A plataforma e-cidadania vén case lista para funcionar tan axiña a
descargues, pero aínda che queda editar o arquivo `settings.py` e algúns pasos máis.

Base de datos (BDD)
-------------------

**Configurando a base de datos**::

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
    
O primeiro de todo é configurar a base de datos. Por defecto e-cidadania vén
configurado para utilizar unha base de datos local de tipo SQLite 3, que che pode
resultar útil para realizar probas antes de poñer a plataforma en produción,
pero que deberás cambiar tan axiña como remates as probas.

Un exemplo de base de datos nun servidor compartido de DreamHost é iste::

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

O modo debug vén activado por defecto e recoméndase encarecidamente
desactivalo para comezar a utilizar e-cidadania en produción. Para isto
hai que desactivalo no ficheiro `settings.py`::

    DEBUG = False

Perfís de usuario
-----------------

*ACCOUNT_ACTIVATION_DAYS* (número)

    Esta variable especifica cantos días ten o usuario para activar a súa
    conta dende que recibe o correo de confirmación.

*GOOGLE_MAPS_API_KEY* (hash)

    Chave da API de Google para poder utilizar a interface de mapas. Débeste
    crear unha propia a pesar de que e-cidadania veña con unha configurada,
    xa que só funcionará no dominio que houberas especificado.

Correo electrónico
------------------

*ADMINS* (lista)

    Lista de administradores e contas de correo para a notificación
    de erros do servidor. Só funciona se DEBUG = False
    
*EMAIL_HOST* (servidor)

    Servidor de correo dende o cal se enviarán os correos aos usuarios.
    
*DEFAULT_FROM_EMAIL*

    Enderezo por defecto dende a que se enviarán os correos se non se especifica
    outra.

Idioma
------

*LANGUAGE_CODE* (código de idioma)

    Idioma co cal funcionará django por defecto.

Despois de settings.py
----------------------

Despois de configurar e-cidadania ao teu gusto, terás que executar unha serie
de comandos para que todo estea en orde.

*Crear a BDD*

    Para crear a base de datos co primeiro usuario de administración executamos
    dende a raíz do proxecto::
    
    ./manage.py syncdb
    
    Creará as táboas da base de datos e posteriormente preguntaranos se queremos
    crear un usuario de administración. Elixiremos a opción que máis nos conveña
    e seguiremos.
    
    En principio con isto é suficiente. Se por algún motivo queres meter un conxunto
    de datos previos, deberás facelo a través dos métodos que Django ofrece,
    pero iso cae fóra deste manual.

*Recoller ficheiros estáticos*

    e-cidadania vén configurado para servir os ficheiros estáticos tanto en
    desenvolvemento como en produción, pero neste último hai que *recollelos* e
    xuntalos nun directorio.
    
    Ese directorio vén predeterminado como "static", e os ficheiros estáticos
    propios de e-cidadania están almacenados en "static_files". Para *recoller*
    os ficheiros debes executar o comando::
    
    ./manage.py collectstatic
    
    Tras executalo podes borrar o directorio *static_files* se queres, aínda que
    recomendamos mantelo por se algún día necesitas executar o servidor de
    desenvolvemento.
    
Plugins
-------

.. note:: e-cidadania aínda non soporta plugins, pero farao nun futuro.

