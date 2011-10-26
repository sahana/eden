:mod:`apps.news` --- News
=========================

:mod:`news.admin` --- Administration
------------------------------------

.. automodule:: e_cidadania.apps.news.admin

.. autoclass:: PostAdmin(admin.ModelAdmin)
    :members:

:mod:`news.models` --- Data models
----------------------------------

.. automodule:: e_cidadania.apps.news.models

.. autoclass:: Post(models.Model)
    :members:

:mod:`news.forms` --- Forms
---------------------------

.. automodule:: e_cidadania.apps.news.forms

.. autoclass:: NewsForm(ModelForm)
    :members:

:mod:`news.views` --- Views
---------------------------

.. automodule:: e_cidadania.apps.news.views

.. autoclass:: ViewPost(DetailView)
    :members:

.. autofunction:: add_post(request, space_name)

.. autofunction:: edit_post(request, space_name, post_id)

.. autoclass:: DeletePost(DeleteView)
    :members:
