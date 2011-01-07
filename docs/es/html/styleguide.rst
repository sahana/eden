Guía de estilo de desarrollo
============================

La guía de estilo establece una serie de parámetros a seguir a la hora de programar código para e-cidadania. Estas normas son inquebrantables.

Python
------

**Imports**

- Todos los imports deben estar situados en la cabecera del fichero, por debajo de la cabecera de comentarios.
- Los imports de módulos de sistema o de python deben preceder a los demás, y los de las librerías externas deben preceder a los de la aplicación.

*Ejemplo*::

    import os
    import sys

    from extlib import function

    from myapp.module import function

**Columnas**

El código debe de ser de 80 columnas de ancho como máximo salvo en los casos de las plantillas de estilo.

Si una línea de código no cabe en 80 columnas, intenta reducirla declarando variables previamente. Si aún así no se puede y la línea tiene paréntensis, debe dividirse por ese lugar.

*Ejemplo*::

    website = models.URLField(_('Website'), verify_exists=True,
                              max_length=200, null=True, blank=True,
                              help_text=_('The URL will be checked'))

**Indentación**

La indentación debe ser de 4 espacios por nivel. No se pueden utilizar tabulaciones para marcar los niveles de indentación.

HTML
----

**Columnas**

El código HTML no tiene límite de columnas, pero debe estar indentado de forma que se pueda localizar rápidamente cualquier elemento del documento. La disposición indentada en el desarrollo prevalece sobre el resultado renderizado de la aplicación.

CSS
---

Estilo de hojas CSS.

JavaScript
----------

Estilo de hojas JavaScript.
