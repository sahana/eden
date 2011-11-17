Generando la documentación
==========================

La documentación de e-cidadania se genera a través del programa sphinx (1.1) en
tres idiomas por defecto, que son:

- Inglés
- Español
- Gallego

La documentación está estructurada de forma que sea lo más automática posible. Los
tres idiomas se generan de una sentada al ejecutar `make html`.

Una vez realizado ese comando la documentación quedará distribuída de la siguiente
forma::

    docs/
        en/
        es/
        gl/
        reference/
        dev/
        docs/
        theming/
        index.rst

Las carpetas `es`, `en` y `gl` contienen la documentación en sus respectivos
idiomas. La carpeta `reference` sólo existe en la raíz de la documentación y se
replica en los otros idiomas (la referencia debe ser siempre en inglés y es
autogenerada desde los comentarios de código).

Por motivos de compatibilidad (por ejemplo con la plataforma *Read The Docs*) una
copia de la documentación en inglés se mantiene en la raíz, eso dará una solución
en caso de que utilicemos alguna herramienta que busque la documentación en el
directorio por defecto. 


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
