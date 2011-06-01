Manual de administración
========================

Este es un pequeño manual introductorio que va a enseñarte a utilizar e-cidadania
de forma correcta.

Registro de usuarios
--------------------

El registro de usuarios en la versión `v0.1 alpha` se realiza de forma manual,
debiado a que no hay ningún mecanismo seguro de autentificación, salvo el DNI-e
que está poco extendido.

De todas formas, e-cidadania cuenta desde el principio con un sistema de registro
automático de usuarios que el administrador podrá activar cuando lo crea conveniente
quitando la marca de comentario (almohadilla).

*apps/userprofile/urls/en.py:107*::

   # url(r'^register/$', register, name='signup'),

Si la plataforma está correctamente configurada el sistema de registro ya se
debería encargar de todo.

Permisos
--------

Los permisos en e-cidadania se heredan directamente del sistema de django. De
esa manera tenemos permisos por usuario y por grupo. Para esta primera versión
de e-cidadanía es suficiente, pero **sería extremadamente recomendable que
no utilizases la aplicación si la seguridad es tu prioridad**.

e-cidadania 0.2 contará con un sistema de permisos por fila, mucho más detallados
y seguros que los permisos actuales.

Grupos
------

Los grupos son una forma masiva de otorgar permisos a grupos de gente. En esta
versión los grupos van a ser una forma de agrupar a la gente por espacios y
otorgarles permisos en esos espacios determinados, salvo que por algún motivo
se le otorgue un permiso diferente por alguna tarea que deba hacer.

Espacios
--------

Los espacios son lugares donde se realizan procesos participativos.

Módulos
-------

e-cidadania es una plataforma modular. Incluso sus características básicas
(noticias, documentos, espacios) son meros módulos que pueden ser sustituídos
en el momento que se preciso sin afectar a la estructura general de la aplicación.

Moderación
..........

Las tareas de moderación de la plataforma son muy sencillas. Cada módulo consta
de tres tareas básicas, que son: creación, edición y borrado.

**Creación**
  Dependiendo del grado de moderación que se te haya otorgado podrás agregar
  contenidos sencillos o más complejos. Los mayores niveles de moderación
  tienen un grado elevadísimo de detalle a la hora de agregar contenido.

**Edición**
  La tarea de edición es similar a la de creación, se presentará un formulario
  en base a las credenciales de las que disponga el moderador.

**Borrado**
  Por norma general en foros un moderador puede borrar las entradas de los
  usuarios. En e-cidadania ese no es el objetivo. Todo lo que diga la gente
  debe preservarse salvo que incurra en alguna falta grave. Sólo los moderadores
  de mayor nivel pueden borrar las entradas.

Errores frecuentes
------------------

Los errores más frecuentes son debidos al servidor o a una mala gestión del
administrador en cuanto a los permisos y/o grupos.
