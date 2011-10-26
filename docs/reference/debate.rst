:mod:`apps.debate` --- Debates
==============================

:mod:`debate.admin` --- Administration
--------------------------------------

.. automodule:: e_cidadania.apps.debate.admin

.. autoclass:: DebateAdmin(admin.ModelAdmin)
    :members:

.. autoclass:: NoteAdmin(admin.ModelAdmin)
    :members:
    
:mod:`debate.models` --- Data models
------------------------------------

.. automodule:: e_cidadania.apps.debate.models

.. autoclass:: Debate(models.Model)
    :members:

.. autoclass:: Note(models.Model)
    :members:

:mod:`debate.forms` --- Forms
-----------------------------

.. automodule:: e_cidadania.apps.debate.forms

.. autoclass:: DebateForm(ModelForm)
    :members:

.. autoclass:: NoteForm(ModelForm)
    :members:
    
:mod:`debate.views` --- Views
-----------------------------

.. automodule:: e_cidadania.apps.debate.views

.. autofunction:: add_new_debate(request, space_name)

.. autofunction:: get_debates(request)

.. autofunction:: create_note(request, space_name)

.. autofunction:: update_note(request, space_name)

.. autofunction:: delete_note(request, space_name)

.. autoclass:: ViewDebate(DetailView)
    :members:

.. autoclass:: ListDebates(ListView)
    :members:
