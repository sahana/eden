Guía de estilo
==============

A guía de estilo establece unha serie de normas a seguir cando se programa en
e-cidadania. Estas normas son *inquebrantables*. A guía de estilo segue moi
preto o documento `PEP8`_, con algunhas excepcións que veñen da guía de
estilo interna de `Pocoo`_.

.. _PEP8: http://www.python.org/dev/peps/pep-0008
.. _Pocoo: http://www.pocoo.org//internal/styleguide/

Python
------

**Imports**
    Todos os imports deben estar situados na cabeceira do arquivo, por debaixo
    do comentario de cabeceira. Os imports de módulos python deben preceder a todos
    os demais, e as librarías externas ou módulos de terceiras partes deben preceder
    aos das aplicacións.

    *Exemplo*::

        import os
        import sys

        from extlib import function

        from myapp.module import function

**Ancho de liña (columnas)**
    O código debe ser sempre de 80 columnas de ancho, permítese un par de columnas
    extra en casos de necesidade.

**Declaracións longas**
    Se unha liña de código non cabe en 80 columnas, intenta reducilo declarando
    variables previamente. Se aínda non encaixa, podes dividir as liñas da
    seguinte forma:

    *Sentencias con parénteses*::

        website = models.URLField(_('Website'), verify_exists=True,
                                  max_length=200, null=True, blank=True,
                                  help_text=_('The URL will be checked'))

    *Declaracións*::

        this_is_a_very_long(function_call, 'with many parameters') \
            .that_returns_an_object_with_an_attribute

        MyModel.query.filter(MyModel.scalar > 120) \
                     .order_by(MyModel.name.desc()) \
                     .limit(10)

    *Listas, tuplas e diccionarios*::

        items = [
            'this is the first', 'set of items', 'with more items',
            'to come in this line', 'like this'
        ]

        dict = {
            ('mobile': phone),
            ('car': key),
            ('another': thing),
        }

**Sangría**
    A sangría debe ser **sempre** de 4 espazos por nivel. Non se permite o
    uso de tabulacións para sangrar.

**Liñas en branco**
    Cada función e clase debe estar separado por dúas liñas en branco. O
    código dentro dunha clase ou método debe estar separado por unha liña en
    branco.

    *Exemplo*::

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
    O código HTML non ten límite de columnas, pero debe estar sangrado de forma
    que se poida localizar rapidamente cada elemento no documento. O estilo
    de sangrado precede ao resultado interpretado no navegador.

**Sangría**
    O código X/HTML debe estar sangrado con 4 espazos por nivel igual que
    o código python, sen excepcións.
    
    .. note:: Poida que haxa código antigo que siga a anterior norma de sangría
              que establecía dos espazos por nivel. Se ves algún arquivo así
              agradeceríamos que nos enviases un parche para solucionalo.

CSS
---

**Sangría**
    A sangría é de 4 espazos, igual que no código python.

    *Exemplo*::

        body {
            background: #FAFAFA;
	        padding: 0;
	        margin: 0;
	        font-family: Verdana, "Lucida Sans", Arial;
	        font-size: 1em;
	        color: #000;
	        cursor: default;
        }

**Cores**
    As cores deben ser escritos sempre en hexadecimal. Permítese utilizar
    abreviaturas de tres díxitos.

**Tamaño de fonte**
    O tamaño de fonte debe estar especificado sempre en **em's** salvo que
    sexa un requisito da presentación.


JavaScript
----------

Ao código javascript aplícanselle as mesmas normas que ao código python.
