Contas de usuario
=================

O módulo de contas de usuario baséase no módulo *auth* de django e na
aplicación *django-userprofile* creada por James Bennet.

Pode que para algunha instalación concreta de e-cidadania se precisen outros datos
do usuario que non teñan que ver co modelo de datos que trae e-cidadania por
defecto. Nese caso, pódense modificar os campos do perfil de usuario.

O fichero que contén o modelo de datos do perfil atópase en
`apps/accounts/models.py`. Todos os campos poden ser modificados salvo os de
idade e espazos.

.. note:: Recorda que tras modificar o modelo de datos da túa instalación deberás
          reconstruír a base de datos. Recomendamos que instales algunha aplicación
          para migración de esquemas de bases de datos como *django-evolution*

Os usuarios constan de dúas partes. Por unha está a conta de usuario creada
polo módulo *auth* de django e por outra está o obxecto *profile* que contén
todos os datos do perfil.

Os usuarios poden crearse sen o seu respectivo perfil, pero unha vez que se intente
crear un perfil haberá que enchelo enteiro e quedará asociado ao seu usuario de
por vida.

Perfís públicos
---------------

Os usuarios contan cunha parte pública do seu perfil, que mostrará os datos
que eles elixan facer públicos.

Os datos que elixan facerse públicos serán visibles para calquera persoa que
visite o perfil. Sexa usuario da plataforma ou non.

.. note:: Ten coidado coa información que amosas na rede.

.. warning:: Actualmente os datos do perfil público non son configurables polos
             usuarios. Espérase cambiar isto en e-cidadania 0.1.5.
             

