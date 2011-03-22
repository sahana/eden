Generando documentación y traducciones
======================================

La documentación de e-cidadania se genera en tres idiomas por defecto, que son:

- Inglés
- Español
- Gallego


Herramientas
------------

Para poder ayudar con la documentación o con las traducciones deberás tener
isntalado en tu sistema las siguientes herramientas:

- Sphinx
- Gettext
- Django

Documentación
-------------

Traducciones
------------

Para la traducción se pueden utilizar mayoritariamente dos herramientas:

- django-rosetta
- gettext

Ambas formas de traducción son sencillas gracias al *middleware* de Django.

Traduciendo con rosetta
.......................

Para traducir con rosetta es necesario tener una cuenta en el sistema y
pertenecer al grupo **'translators'**. Una vez hecho eso, el resto es sencillo.

Basta con acceder a la `URL de traducción`_ y lo primero que se verá será una
lista de los idiomas disponibles para traducir.

.. _URL de traducción: http://ecidadania.org/rosetta 

.. image:: ../images/rosetta1.png
    :align: center

Basta con hacer clic en el componente que se desee traducir y comenzar la
traducción (se realiza desde el inglés al resto de idiomas). Si te encuentras
atascado puedes utilizar la opción "Sugerir" que consultará la base de datos
de Google Translate y te dará el resultado que el crea correcto.

.. warning:: Nunca te fies del resultado del botón "sugerir" ya que en muchas ocasiones
   es incorrecto.

Traduciendo con gettext (a mano)
................................

Gettext es una herramienta de sobra conocida por todos los traductores del mundo. 
Es un estándar. Gracias al *middleware* de traducción que trae django de serie
nuestro trabajao con gettext va a ser mínimo, tan sólo nos limitaremos a editar
los ficheros .po del códgo fuente.

.. image:: ../images/gettext1.png
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
