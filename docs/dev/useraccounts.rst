Cuentas de usuario
==================

El sistema de cuentas de usuario en e-cidadania está basado en el módulo *auth*
de django, así como en django-registration y django-profile, creados por James
Bennet.

Campos de datos
---------------

Las cuentas de usuario contienen los siguientes campos:

**username** *(CharField, 200 caracteres)*
   Este campo contiene el nombre de usuario. Es accesible como user.username

**firstname** *(CharField, 50 caracteres)*
   Este campo contiene el nombre *real* del usuario.

**surname** *(CharField, 200 caracteres)*
   Este campo contiene los apellidos *reales* del usuario.

**gender** *(Choice)*
   Lista de elecciones de género. Opciones válidas: F (Female) y M (Male)

**birthdate** *(DateField)*
   Fecha de nacimiento del usuario. Utilizada para calcular la edad.

**province** *(CharField, 50 caracteres)*
   Provincia de residencia del usuario.

**municipality** *(CharField, 50 caracteres)*
   Municipio o ciudad de residencia del usuario.

**address** *(CharField)*
   Dirección de residencia (calle) del usuario.

**address_number** *(CharField, 3 caracteres)*
   Número del edificio de residencia.

**address_floor** *(CharField, 3 caracteres)*
   Piso

**address_letter** *(CharField, 2 caracteres)*
   Letra del piso de residencia

**phone** *(CharField, 9 caracteres)*
   Teléfono de contacto del usuario.

**phone_alt** *(CharField, 9 caracteres)*
   Teléfono secundario de contacto

django-profile
--------------

*django-userprofile* se encarga de proveeder las vistas y funciones para extender
el modelo de datos de usuario en django. Junto a un módulo creado para extender
el modelo de datos todo va perfecto.

accounts
--------

El módulo accounts es nuestro modelo extendido de usuario. En él se encuentran
todos los campos extra de usuario que se necesitan y que serán incorporados de
forma transparente a *django-userprofile*.