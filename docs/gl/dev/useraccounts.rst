Cuentas de usuario
==================

El módulo de cuentas de usuario se basa en el módulo *auth* de django y en la
aplicación *django-userprofile* creada por James Bennet.

Puede que para alguna instalación concreta de e-cidadania se necesiten otros datos
del usuario que no tengan que ver con el modelo de datos que trae e-cidadania por
defecto. En ese caso, se puede modificar los campos del perfil de usuario.

El fichero que contiene el modelo de datos del perfil se encuentra en
`apps/accounts/models.py`. Todos los campos pueden ser modificados salvo los de
edad y espacios.

.. note:: Recuerda que tras modificar el modelo de datos de tu instalación deberás
          reconstruir la base de datos. Recomendamos que instales alguna aplicación
          para migración de esquemas de bases de datos como *django-evolution*

Los usuarios constan de dos partes. Por una está la cuenta de usuario creada
por el módulo *auth* de django y por otra está el objeto *profile* que contiene
todos los datos del perfil.

Los usuarios pueden crearse sin su respectivo perfil, pero una vez que se intente
crear un perfil habrá que rellenarlo entero y quedará asociado a su usuario de
por vida.

Perfiles públicos
-----------------

Los usuarios cuentan con una parte pública de su perfil, que mostrará los datos
que ellos elijan hacer públicos.

Los datos que elijan hacerse públicos serán visibles para cualquier persona que
visite el perfil. Sea usuario de la plataforma o no.

.. note:: Ten cuidado con la información que muestras en la red.

.. warning:: Actualmente los datos del perfil pýblico no son configurables por los
             usuarios. Se espera cambiar esto en e-cidadania 0.1.5.
             

