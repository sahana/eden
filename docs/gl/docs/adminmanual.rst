Manual de administración
========================

Este manual ensinarache como manexar e-cidadania para que non te perdas nada de 
nada :).

Concretamente trata a parte do administrador do sitio sen meterse en detalles
técnicos innecesarios. Se en algún momento necesitas detalles técnicos é preferible
que leas o manual de desenvolvemento, no cal está todo especificado.

Estrutura do panel de administración
------------------------------------

|Admin-es|_

.. |Admin-es| image:: ../../images/admin/admin_es_mini.png
.. _Admin-es: http://postimage.org/image/z7b8s72c/full/

A páxina principal do panel de administración divídese en tres grandes zonas:

 1. Esta zona contén todas as aplicacións da plataforma. Desde aquí poderás
    engadir, editar ou eliminar calquera elemento da base de datos.
    
    .. note:: Pode que aparezan tamén outras aplicacións de terceiros, como
              django-evolution ou similares, que son para a xestión de certos
              aspectos técnicos da plataforma.
              
 2. Esta zona contén o que chamamos *widgets*. Neles pódese amosar case
    calquera tipo de información.
    
    Normalmente eses widgets veñen configurados por defecto. Se queres cambiar
    o seu contido basta con que edites o arquivo **dashboard.py** que hai na
    raíz da aplicación, pero ollo, non cho recomendamos se non sabes o que
    estás facendo. Se aínda así queres facelo, mira o `manual de django-grappelli <http://django-grappelli.readthedocs.org/en/latest/dashboard_api.html>`_.
    
 3. Esta é a zona de rexistro. Aquí amosarase toda a actividade recente que
    ocorrese na plataforma.

Rexistro de usuarios
--------------------

Os usuarios teñen dúas formas de rexistrarse:

* **A través do proceso participativo presencial** Anótanse para participar no
  proceso, e vólcanse os seus datos na base de datos de e-cidadania.
  
  Neste caso terás que crear o seu usuario dende *"Usuarios"* e logo o perfil
  correspondente dende *"User profiles"*

* **Rexistrándose eles mesmos** Esta é a forma máis rápida pero tamén menos
  conveniente. Con este rexistro o usuario non terá ningún dos seus datos persoais
  na base de datos, nin pertencerá a ningún proceso participativo salvo que se
  lle permita. Da mesma maneira, só poderá visualizar os procesos participativos
  abertos, pero non poderá participar a menos que se lle inclúa no grupo.

.. note:: Este comportamento é susceptible de cambiar nun futuro.

Por defecto e-cidadania ten o rexistro de usuarios activado cando se instala.
Para desactivalo terás que comentar unha liña de código no seguinte arquivo:

::

    apps/userprofile/urls/en.py:107
        # url(r'^register/$', register, name='signup'),


Permisos
--------

.. note:: En e-cidadania 0.2 actualizarase a permisos por fila, que permiten
          un nivel moito máis detallado de permisos.

Os permisos en e-cidadania están herdados directamente do sistema de autenticación
de django. De esa maneira xa dispoñemos de permisos baseados en grupo ou individuais.

 * **Por grupo** O ideal é xestionar os usuarios a través de grupos. Pódese
   facer accedendo ao panel de administración dende o menú que hai arriba á
   dereita, ao lado do nome de usuario.

   Unha vez no panel de administración basta con que fagamos clic no botón que
   hai ao lado de *"Grupos"* que pon *" + Engadir"* e aí teremos opción a configurar
   os nosos grupos.

   Como poderás observar, temos dous paneis de permisos e un campo para escribir o
   nome. Basta con que pases os permisos que queiras para ese grupo ao panel da
   dereita (mediante as frechas que hai entre os dous paneles) e logo lle poñas
   un nome ao grupo.

   Para gardar fai clic abaixo á dereita onde pon *"Gardar"*.

 * **Individuais** Pode que nalgún momento queiras que alguén teña unha serie
   de permisos en concreto que non encaixan en ningún dos grupos que creaches.
   Nese caso é mellor darlle os permisos ao usuario en si en vez de crear un
   grupo para el só.

   Para iso debes editar ao usuario facendo clic en *"Usuarios"* e seleccionando o
   que queiras editar. Mostraránseche unha serie de datos do usuario como os grupos
   aos que pertence, data de rexistro, etc. O que nos interesa son os paneis
   de permisos.

   Funcionan exactamente igual que os de grupo. Basta con que o configures e gardes
   os cambios para aplicar os permisos ao usuario.

Espazos
-------

Os espazos son zonas separadas nas cales teñen lugar os procesos participativos.
Cada espazo pode configurarse a medida das necesidades do proceso e non poderá
participar ningún usuario que non fose "admitido".

A creación de espazos corresponde ao administrador da plataforma, por medidas
de seguridade.

.. note:: Esta sección está sen terminar.


Módulos
-------

e-cidadania é unha plataforma totalmente modular, incluso as características máis
básicas como noticias, repositorio de documentos, espazos, sistema de propostas, etc.
son módulos que poden ser modificados ou substituídos sen afectar á estrutura
da plataforma.

Moderación
----------

As tarefas de moderación dentro da plataforma son moi sinxelas. Cada módulo ou
aplicación ten tres tarefas básicas: crear, editar e eliminar.

**Crear**
  Dependendo do grao de moderación que teñas, poderás engadir contido de
  distintos tipos. Os niveis de moderación máis altos permiten crear practicamente
  calquera cousa e cun elevado grao de detalle.

**Editar**
  A tarefa de edición é similar á de creación, coa diferencia de que se che
  devolverá un formaluario cos datos do obxecto que esteas editando.
  
  O contido xerado polos usuarios debe ser preservado, só pode ser
  eliminado polos administradores do sitio.
  
**Eliminar**
  Normalmente nun foro, un moderador pode eliminar o contido dun usuario.
  En e-cidadania ese non é o obxectivo. Todo o contido xerado polos usuarios
  debe preservarse e só poderá ser eliminado polos administradores do sitio ou
  baixo petición do propio usuario.

Erros frecuentes
----------------

Lista de erros máis frecuentes á hora de administrar.
