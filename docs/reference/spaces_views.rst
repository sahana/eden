:mod:`spaces.views` --- Space-related views
===========================================

.. automodule:: e_cidadania.apps.spaces.views    
 
General spaces views
--------------------

.. autoclass:: ListPosts(ListView)

Spaces views
---------------------

.. autoclass:: GoToSpace(RedirectView)

.. autoclass:: ListSpaces(ListView)

.. autoclass:: ViewSpaceIndex(DetailView)

.. autoclass:: DeleteSpace(DeleteView)

.. autofunction:: edit_space(request, space_name)

.. autofunction:: create_space(request)

Document views
-----------------------

.. autoclass:: ListDocs(ListView)

.. autoclass:: DeleteDocument(DeleteView)

.. autofunction:: add_doc(request, space_name)

.. autofunction:: edit_doc(request, space_name, doc_id)


Meeting views
-------------

.. autoclass:: ListMeetings(ListView)

.. autoclass:: ViewMeeting(DetailView)

.. autoclass:: DeleteMeeting(DeleteView)

.. autofunction:: add_meeting(request, space_name)

.. autofunction:: edit_meeting(request, space_name, meeting_id)

