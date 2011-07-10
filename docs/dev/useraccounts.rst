User accounts
=============

Th user account system in e-cidadania is abased on the django *auth* module and
in django-userprofile, created by James Bennet.

django-userprofile
------------------

*django-userprofile* provides the views and functions to extend the user data
model in django. Together with a module created for extending the data model everything
goes fine.

accounts
--------

The accounts module is our extended user data model. In it you can find all the
extra fields that are needed and will be added to *django-userprofile*.

