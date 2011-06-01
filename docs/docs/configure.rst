Configuración
=============

e-cidadania se ha diseñado para evitar tanto al usuario como al administrador
el máximo trabajo posible, de forma que la configuración es muy sencilla.

Existen un número determinado de variables que hay que configurar, mientras
que el resto se configurarán automáticamente.

Todas las variables de configuración se encuentran en el fichero settings.py

Usuarios
--------

*AUTH_PROFILE_MODULE*
  El módulo que se va a utilizar para extender el modelo de usuario.

*ACCOUNT_ACTIVATION_DAYS*
  Número de días que se le permitirá al usuario para poder activar su cuenta tras
  registrarse.

*LOGIN_REDIRECT_URL*
  Dirección a la que será enviado el usuario tras un login correcto.

*GOOGLE_MAPS_API_KEY* **(no disponible)**
  Llave para la API de Google Maps, esta se va a utilizar para el
  geoposicionamiento en diversas zonas de la plataforma.

Correo electrónico
------------------

*EMAIL_HOST*
  Servidor de correo desde el que se van a enviar los emails a los usuarios.

*DEFAULT_FROM_EMAIL*
  Dirección de correo bajo la que se enviarán los correos a los usuarios.
  Por defecto: *accounts@cidadania.coop*

Administración y BDD
--------------------

*ADMINS*
  Lista de administradores del sitio. Esta parte es importante ya que cualquier
  error de la plataforma será enviado a las direcciones que se hayan escrito.

*DATABASES*
  Configuración de una o varias bases de datos de la plataforma. En un sistema
  concurrido recomendados dos bases de datos separadas en hosts que no sean
  el que almacena los datos.

Idioma
------

*TIME_ZONE*
  Zona horaria, si no sabes cuál es la tuya puedes consultarlo en `aqui`_

.. _aqui: http://www.worldtimezone.com/

*LANGUAGE_CODE*
  Código de idioma, habitualmente de dos letras (ES, EN, FR, etc.)

*LANGUAGES*
  Lista de idiomas admitidos en la plataforma. Si esta variable está vacía, se
  cargará con la lista por defecto de **todos** los idiomas soportados por Django.

