:mod:`apps.proposals` --- Proposals
===================================

:mod:`proposals.admin` --- Administration
-----------------------------------------

.. automodule:: e_cidadania.apps.proposals.admin

.. autoclass:: ProposalAdmin(admin.ModelAdmin)
    :members:

:mod:`proposals.models` --- Data models
---------------------------------------

.. automodule:: e_cidadania.apps.proposals.models

.. autoclass:: BaseClass(models.Model)
    :members:

.. autoclass:: Category(BaseClass)
    :members:

.. autoclass:: Proposal(models.Model)
    :members:

:mod:`proposals.forms` --- Forms
--------------------------------

.. automodule:: e_cidadania.apps.proposals.forms

.. autoclass:: ProposalForm(ModelForm)
    :members:

:mod:`proposals.views` --- Views
--------------------------------

.. automodule:: e_cidadania.apps.proposals.views    

.. autoclass:: ListProposals(ListView)
    :members:

.. autoclass:: ViewProposal(DetailView)
    :members:
    
.. autoclass:: DeleteProposal(DeleteView)
    :members:
    
.. autofunction:: add_proposal(request, space_name)
    
.. autofunction:: edit_proposal(request, space_name, prop_id)
