Guía de estilo
==============

La guía de estilo establece una serie de parámetros a seguir a la hora de programar código para e-cidadania. Estas normas son inquebrantables. La guía de estilo sigue bastante fielmente el `PEP8`_, con algunas excepciones que vienen de la guía de estilo interna de `Pocoo`_.

.. _PEP8: http://www.python.org/dev/peps/pep-0008
.. _Pocoo: http://www.pocoo.org//internal/styleguide/

Python
------

**Imports**
    Todos los imports deben estar situados en la cabecera del fichero, por debajo de la cabecera de comentarios. Los imports de módulos de sistema o de python deben preceder a los demás, y los de las librerías externas deben preceder a los de la aplicación.

    *Ejemplo*::

        import os
        import sys

        from extlib import function

        from myapp.module import function

**Ancho de línea**
    El código debe de ser de 80 columnas de ancho como máximo salvo en los casos de las plantillas.

**Declacariones largas**
    Si una línea de código no cabe en 80 columnas, intenta reducirla declarando variables previamente. Si aún así no se puede se deben dividir de las siguientes formas:

    *Parentesis*::

        website = models.URLField(_('Website'), verify_exists=True,
                                  max_length=200, null=True, blank=True,
                                  help_text=_('The URL will be checked'))

    *Declaraciones*::

        this_is_a_very_long(function_call, 'with many parameters') \
            .that_returns_an_object_with_an_attribute

        MyModel.query.filter(MyModel.scalar > 120) \
                     .order_by(MyModel.name.desc()) \
                     .limit(10)

    *Listas, tuplas y diccionarios*::

        items = [
            'this is the first', 'set of items', 'with more items',
            'to come in this line', 'like this'
        ]

        dict = {
            ('mobile': phone),
            ('car': key),
            ('another': thing),
        }

**Indentación**
    La indentación debe ser de 4 espacios por nivel, sin excepciones. No se pueden utilizar tabulaciones para marcar los niveles de indentación.

**Líneas en blanco**
    Todas las funciones y clases deben estar separadas por dos líneas en blanco. El código dentro de una clase o método por una línea en blanco.

    *Ejemplo*::

        class ListDocs(ListView):

            """
            List all documents stored whithin a space.
            """
            paginate_by = 25
            context_object_name = 'document_list'

            def get_queryset(self):
                place = get_object_or_404(Space, url=self.kwargs['space_name'])
                objects = Document.objects.all().filter(space=place.id).order_by('pub_date')
                return objects

            def get_context_data(self, **kwargs):
                context = super(ListDocs, self).get_context_data(**kwargs)
                context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
                return context


        def whatever(args):

            """
            A comment.
            """
            this_is_something = 0


HTML
----

**Columnas**
    El código HTML no tiene límite de columnas, pero debe estar indentado de forma que se pueda localizar rápidamente cualquier elemento del documento. La disposición indentada en el desarrollo prevalece sobre el resultado renderizado de la aplicación.

**Indentación**
    El código X/HTML debe estar indentado con 2 espacios, sin excepción.

CSS
---

**Indentación**
    La indentación será de 4 espacios, siempre, igual que el código Python.

    *Ejemplo*::

        body {
            background: #FAFAFA;
	    padding: 0;
	    margin: 0;
	    font-family: Verdana, "Lucida Sans", Arial;
	    font-size: 1em;
	    color: #000;
	    cursor: default;
        }

**Colores**
    Los colores siempre deberán estar escritos en su código hexadecimal. Se permiten las abreviaturas de tres dígitos.

**Tamaños de letra**
    Los tamaños de letra deben ser declarados siempre en **em's** y salvo una excepción muy casual no se deben declarar en píxels.


JavaScript
----------

Estilo de código JavaScript.