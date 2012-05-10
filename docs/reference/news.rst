:mod:`apps.ecidadania.news` --- News
====================================

:mod:`news.admin` --- Administration
------------------------------------

.. automodule:: apps.ecidadania.news.admin

.. autoclass:: PostAdmin(admin.ModelAdmin)
    :members:

:mod:`news.models` --- Data models
----------------------------------

.. automodule:: apps.ecidadania.news.models

.. autoclass:: Post(models.Model)
    :members:

:mod:`news.forms` --- Forms
---------------------------

.. automodule:: apps.ecidadania.news.forms

.. autoclass:: NewsForm(ModelForm)
    :members:

:mod:`news.views` --- Views
---------------------------

.. automodule:: apps.ecidadania.news.views

.. autoclass:: ViewPost(DetailView)
    :members:

.. autoclass:: AddPost(FormView)

.. autoclass:: EditPost(UpdateView)

.. autoclass:: DeletePost(DeleteView)
    :members:
