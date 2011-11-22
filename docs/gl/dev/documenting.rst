Xerando a documentación
=======================

A documentación de e-cidadania xérase a través do programa sphinx (1.1) en
tres idiomas por defecto, que son:

- Inglés
- Español
- Galego

A documentación está estruturada de forma que sexa o máis automática posible. Os
tres idiomas xéranse dunha sentada ao executar `make html`.

Unha vez realizado ese comando a documentación quedará distribuída da seguinte
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

As carpetas `es`, `en` e `gl` conteñen a documentación nos seus respectivos
idiomas. A carpeta `reference` só existe na raíz da documentación e replícase
nos outros idiomas (a referencia debe ser sempre en inglés e é
autoxerada dende os comentarios de código).

Por motivos de compatibilidade (por exemplo coa plataforma *Read The Docs*) unha
copia da documentación en inglés mantense na raíz, iso dará unha solución
en caso de que utilicemos algunha ferramenta que busque a documentación no
directorio por defecto. 


Normas lingüísticas
-------------------

 * Sempre tratar de ti ao lector, nunca de vostede.
 * Sempre que unha palabra teña un equivalente en castelán, usar o equivalente
   aínda que sexa máis común o anglicismo.
   
.. note:: Esta sección está sen terminar.

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
