Guía de estilo
==============

La guía de estilo establece una serie de normas a seguir cuando se programa en
e-cidadania. Estas normas son *inquebrantables*. La guía de estilo sigue muy
de cerca el documento `PEP8`_, con algunas excepciones que vienen de la guía de
estilo interna de `Pocoo`_.

.. _PEP8: http://www.python.org/dev/peps/pep-0008
.. _Pocoo: http://www.pocoo.org//internal/styleguide/

Python
------

**Imports**
    Todos los imports deben estar situados en la cabecera del archivo, por debajo
    del comentario de cabecera. Los imports de módulos python deben preceder a todos
    los demás, y las librerías externas o módulos de terceras partes deben preceder
    a los de las aplicacion.

    *Ejemplo*::

        import os
        import sys

        from extlib import function

        from myapp.module import function

**Ancho de línea (columnas)**
    El código debe ser siempre de 80 columnas de ancho, se permite un par de columnas
    extra en casos de necesidad.

**Declaraciones largas**
    Si una línea de código no cabe en 80 columnas, intenta reducirlo declarando
    variables previamente. Si todavía no encaja, puedes dividir las lineas de la
    siguiente forma:

    *Sentencias con paréntesis*::

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
    La indentación debe ser **siempre** de 4 espacios por nivel. No se permite el
    uso de tabulaciones para indentar.

**Líneas en blanco**
    Cada función y clase debe de estar separado por dos líneas en blanco. El
    código dentro de una clase o método debe de estar separado por una línea en
    blanco.

    *Ejemplo*::

        class ListDocs(ListView):
            ----blank line----
            """
            List all documents stored whithin a space.
            """
            paginate_by = 25
            context_object_name = 'document_list'
            ----blank line----
            def get_queryset(self):
                place = get_object_or_404(Space, url=self.kwargs['space_name'])
                objects = Document.objects.all().filter(space=place.id).order_by('pub_date')
                return objects
            ----blank line----
            def get_context_data(self, **kwargs):
                context = super(ListDocs, self).get_context_data(**kwargs)
                context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
                return context
        ----blank line----
        ----blank line----
        def whatever(args):
            ----blank line----
            """
            A comment.
            """
            this_is_something = 0


HTML
----

**Columnas**
    El código HTML no tiene límite de columnas, pero debe estar indentado de forma
    que se pueda localizar rápidamente cada elemento en el documento. El estilo
    de indentación precede al resultado renderizado en el navegador.

**Indentación**
    El código X/HTML debe de estar indentado con 4 espacios por nivel igual que
    el código python, sin excepciones.
    
    .. note:: Puede que haya código antiguo que siga la anterior norma de indentación
              que establecía dos espacios por nivel. Si ves algún archivo así
              agradeceríamos que nos enviases un parche para solucionarlo.

CSS
---

**Indentación**
    La indentación es de 4 espacios, igual que en el código python.

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
    Los colores deben ser escritos siempre en hexadecimal. Se permite utilizar
    abreviaturas de tres dígitos.

**Tamaño de fuente**
    El tamaño de fuente debe estar especificado siempre en **em's** salvo que
    sea un requisito de la presentación.


JavaScript
----------

Al código javascript se le aplican las mismas normas que al código python.
