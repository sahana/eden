Generando la documentación
==========================

La documentación de e-cidadania se genera a través del programa sphinx (1.1) en
tres idiomas por defecto, que son:

- Inglés
- Español
- Gallego

La estructura actual de la documentación es::

    docs/
        en/
        es/
        gl/
        reference/
        build/
        dev/ *
        docs/ *
        theming/ *
        index.rst *
        authors.rst *

Las carpetas `en`, `es` y `gl` contienen la documentación para sus
respectivos idiomas. La carpeta `reference` contiene la documentación que se
genera automáticamente a partir de los comentarios de código, que serán
siempre en inglés y por lo tanto estará enlazado a todos los idiomas para
tener únicamente una copia y no tener que actualizar las tres de cada vez.

Lo mismo sucede para los últimos archivos y carpetas. Por motivos de
compatibilidad hemos dejado la estructura "típica" de un proyecto de sphinx,
que sólo son enlaces a la documentación en inglés. Esto nos permite publicar
la documentación en sistios como *`Read The Docs <http://readthedocs.org>`_*
que utilizan la estructura estándar para analizar la documentación.

La documentación se estructura en tres grandes categorías::

    dev/     -- Relacionado con desarrollo o administración (instalación, configuración, puesta en marcha, etc.)
    docs/    -- Documentación habitual (manual de usuario, de administrador, etc.)
    theming/ -- Tutoriales sobre temas, índice de apariencias de e-cidadania, etc.

La documentación está estructurada de forma que sea lo más automática posible. Los
tres idiomas se generan de una sentada al ejecutar `make html`.

Una vez realizado ese comando la documentación quedará distribuída de la siguiente
forma::

    build/
        doctrees/
        html/
            es/
            en/
            gl/
        latex/
            es/
            en/
            gl/

Las carpetas `es`, `en` y `gl` contienen la documentación en sus respectivos
idiomas. La carpeta `doctrees` sólo sirve de referencia para generar los documentos.

Como puedes ver, hay dos formatos de documentación: `latex` y `html`.
e-cidadania tiene tres tipos de formato soportados oficialmente para la
documentación: html, latex y pdf (generado a través de pdflatex y guardado
en la carpeta `latex`).

.. note:: Tal como hemos diseñado el sistema multiidioma debería permitir
          generar cualquiera de los formatos permitidos por sphinx (como
          epub, manpages, htmlhelp, etc.) pero no lo garantizamos.

De la misma forma que se pueden generar todos los idiomas de una vez,
también se pueden generar por separado ejecutando el mismo comando *make*
pero dentro de la carpeta del idioma.

Normas lingúisticas
-------------------

 * Siempre tratar de tú al lector, nunca de usted.
 * Siempre que una palabra tenga un equivalente en castellano, usar el equivalente
   aunque sea más común el anglicismo.
   
.. note:: Esta sección está sin terminar.

Palabras difusas
----------------

.. note:: Esta sección está en constante cambio.

+-----------+----------+
| Inglés    | Español  |
+===========+==========+
| Click     | Clic     |
+-----------+----------+
| Delete    | Eliminar |
+-----------+----------+
| Widget    |          |
+-----------+----------+
| Dashboard |          |
+-----------+----------+
| File      | Archivo  |
+-----------+----------+
