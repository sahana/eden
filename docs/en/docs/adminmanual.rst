Administration manual
=====================

This is a small introductory manual to teach you about how to use e-cidadania
without messing everything up :).

User registration
-----------------

.. note:: This section is obsolete.

User registration in version `0.1 alpha` is done manually due to the lack of
a secure authentication mechanism, except the electronic certificate, that is
not too much extended.

Anyway, e-cidadania has from the start a basic automated registration system, that
the administrator will have to activate when he considers removing the comment symbol
(sharp).

*apps/userprofile/urls/en.py:107*::

   # url(r'^register/$', register, name='signup'),

If the platform is well set up, the registration system should take care of
everything.

Permissions
-----------

Permissions in e-cidadania are inherited directly from the django auth system.
This way we have group based permissions and user based permissions. For the first
release is enough, but **it would be extremely recommended to not use the platform
yet, if security if your priority**.

e-cidadania 0.2 will have a row-level permission system, more detailed and secure
than the current ones.

Groups
------

Groups are a massive way to give permissions to people. In this version groups will
be a way to group people inside the spaces, except that for any reason you'll have
to give them another permission for a specific task.

Spaces
------

Spaces are where partivipative processes take place.

Modules
-------

e-cidadania is a modular platform. Even its basic features (news, documents,
spaces, proposals) are modules that can be replaced at any moment without affecting
the general application structure.

Moderation
..........

Moderation tasks inside the platform are very simple. Every module has three basic
tasks which are: creation, editing and deletion.

**Creation**
  Depending on the moderation grade that you have been given, you can add simple
  content or more complex. The highest moderation leves have a very high detail
  grade when adding content.

**Editing**
  The editing task is similar to creation, it will return a formulary with the
  current data based on your permission level.

**Deletion**
  Usually in forums a moderator can delete user entries. In e-cidadania that is
  not the objective. User generated content must be preserved, it only can be
  deleted by platform administrators.

Frequent errors
---------------

The most frequest errors are due to the server or a bad administrator management
in the groups/permission case.

