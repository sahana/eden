Desarrollo
==========

Guía de estilo
--------------

La guía de estilo establece una serie de parámetros a seguir a la hora de programar código para e-cidadania. Estas normas son inquebrantables. La guía de estilo sigue bastante fielmente el `PEP8`_, con algunas excepciones que vienen de la guía de estilo interna de `Pocoo`_.

.. _PEP8: http://www.python.org/dev/peps/pep-0008
.. _Pocoo: http://www.pocoo.org//internal/styleguide/

Python
......

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
....

**Columnas**
    El código HTML no tiene límite de columnas, pero debe estar indentado de forma que se pueda localizar rápidamente cualquier elemento del documento. La disposición indentada en el desarrollo prevalece sobre el resultado renderizado de la aplicación.

**Indentación**
    El código X/HTML debe estar indentado con 2 espacios, sin excepción.

CSS
...

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
..........

Estilo de código JavaScript.

Cuentas de usuario
------------------

El sistema de cuentas de usuario en e-cidadania está basado en el módulo *auth*
de django, así como en django-registration y django-profile, creados por James
Bennet.

Campos de datos
...............

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
..............

*django-userprofile* se encarga de proveeder las vistas y funciones para extender
el modelo de datos de usuario en django. Junto a un módulo creado para extender
el modelo de datos todo va perfecto.

accounts
........

El módulo accounts es nuestro modelo extendido de usuario. En él se encuentran
todos los campos extra de usuario que se necesitan y que serán incorporados de
forma transparente a *django-userprofile*.


Módulos base
------------

Propuestas
..........

El sistema de propuestas consta de varios elementos muy similares al ya
archiconocido sistema de preguntas de *Stack Overflow*.

Aunque es similar, tiene grandes diferencias que hacen que sea único en
lo referente a la aplicación.

Debates
.......

Noticias
........

Espacios
........

Páginas estáticas
.................


Generando documentación y traducciones
--------------------------------------

La documentación de e-cidadania se genera en tres idiomas por defecto, que son:

- Inglés
- Español
- Gallego


Herramientas
............

Para poder ayudar con la documentación o con las traducciones deberás tener
isntalado en tu sistema las siguientes herramientas:

- Sphinx
- Gettext
- Django

Documentación
.............

Traducciones
............

Para la traducción se pueden utilizar mayoritariamente dos herramientas:

- django-rosetta
- gettext

Ambas formas de traducción son sencillas gracias al *middleware* de Django.

Traduciendo con rosetta
,,,,,,,,,,,,,,,,,,,,,,,

Para traducir con rosetta es necesario tener una cuenta en el sistema y
pertenecer al grupo **'translators'**. Una vez hecho eso, el resto es sencillo.

Basta con acceder a la `URL de traducción`_ y lo primero que se verá será una
lista de los idiomas disponibles para traducir.

.. _URL de traducción: http://ecidadania.org/rosetta 

.. image:: images/rosetta1.png
    :align: center

Basta con hacer clic en el componente que se desee traducir y comenzar la
traducción (se realiza desde el inglés al resto de idiomas). Si te encuentras
atascado puedes utilizar la opción "Sugerir" que consultará la base de datos
de Google Translate y te dará el resultado que el crea correcto.

.. warning:: Nunca te fies del resultado del botón "sugerir" ya que en muchas ocasiones
   es incorrecto.

Traduciendo con gettext
,,,,,,,,,,,,,,,,,,,,,,,

Gettext es una herramienta de sobra conocida por todos los traductores del mundo. 
Es un estándar. Gracias al *middleware* de traducción que trae django de serie
nuestro trabajao con gettext va a ser mínimo, tan sólo nos limitaremos a editar
los ficheros .po del códgo fuente.

.. image:: images/gettext1.png
    :align: center
    
En vez de realizar una traducción global, hemos optado por diseñar una traducción
esecífica para cada parte de la plataforma, de forma que las traducciones se
perpetuen aunque los módulos se muevan.

La localización de las cadenas de texto habitualmente es en un directorio llamado
**locale** dentro del módulo. Dentro del mismo, se encuentran directorios con
el código de país (en, es, us, gl, fr, etc.) y dentro de éste, se encuentran los
ficheros PO y MO.

Para traducir, debes editar el fichero PO, que es un fichero de texto plano ya
hecho para ser posteriormente tratado.

El fichero MO es la traducción compilada a lenguaje máquina para que la plataforma
pueda utilziarlo posteriormente.

.. warning:: Establecer un método de trabajo para traductores y explicarlo aqui.
