:mod:`apps.spaces` --- Spaces/Processes
=======================================

:mod:`spaces.admin` --- Administration
--------------------------------------

.. automodule:: e_cidadania.apps.spaces.admin

.. autoclass:: EntityAdmin(admin.ModelAdmin)
    :members:

.. autoclass:: EntityInline(admin.TabularInline)
    :members:

.. autoclass:: SpaceAdmin(admin.ModelAdmin)
    :members:
    
.. autoclass:: DocumentAdmin(admin.ModelAdmin)
    :members:
    
.. autoclass:: MeetingAdmin(admin.ModelAdmin)
    :members:

:mod:`spaces.models` --- Data models
------------------------------------

.. automodule:: e_cidadania.apps.spaces.models

.. autoclass:: Space(models.Model)
    :members:

.. autoclass:: Entity(models.Model)
    :members:

.. autoclass:: Document(models.Model)
    :members:

.. autoclass:: MeetingType(models.Model)
    :members:

.. autoclass:: Meeting(models.Model)
    :members:
    
:mod:`spaces.forms` --- Forms
-----------------------------

.. automodule:: e_cidadania.apps.spaces.forms

.. autoclass:: SpaceForm(ModelForm)
    :members:

.. autoclass:: DocForm(ModelForm)
    :members:
    
.. autoclass:: MeetingForm(ModelForm)
    :members:

:mod:`EntityFormSet` --- modelformset_factory

:mod:`spaces.views` --- Views
---------------------------------

.. automodule:: e_cidadania.apps.spaces.views    
 
General spaces views
....................

.. autoclass:: ListPosts(ListView)
    :members:

Spaces views
............

.. autoclass:: GoToSpace(RedirectView)
    :members:

.. autoclass:: ListSpaces(ListView)
    :members:

.. autoclass:: ViewSpaceIndex(DetailView)
    :members:
    
.. autoclass:: DeleteSpace(DeleteView)
    :members:

.. autofunction:: edit_space(request, space_name)

.. autofunction:: create_space(request)

Document views
..............

.. autoclass:: ListDocs(ListView)
    :members:

.. autoclass:: DeleteDocument(DeleteView)
    :members:

.. autofunction:: add_doc(request, space_name)

.. autofunction:: edit_doc(request, space_name, doc_id)


Meeting views
.............

.. autoclass:: ListMeetings(ListView)
    :members:

.. autoclass:: ViewMeeting(DetailView)
    :members:

.. autoclass:: DeleteMeeting(DeleteView)
    :members:
    
.. autofunction:: add_meeting(request, space_name)

.. autofunction:: edit_meeting(request, space_name, meeting_id)

