Authentication and Authorisation *auth*
=======================================

Global authentication/authorisation service, accessible through **current.auth**.

.. code-block:: python

   from gluon import current

   auth = current.auth

User Status and Roles
---------------------

.. function:: auth.s3_logged_in()

   Check whether the user is logged in; attempts a HTTP Basic Auth login if not.

   :returns bool: whether the user is logged in or not

.. function:: auth.s3_has_role(role, for_pe=None, include_admin=True)

   Check whether the user has a certain role.

   :param str|int role: the UID/ID of the role
   :param int for_pe: the *pe_id* of a realm entity
   :param bool include_admin: return True for ADMIN even if role is not explicitly assigned

   :returns bool: whether the user has the role (for the realm)

.. TODO explain for_pe options

Access Permissions
------------------

Access methods:

===========  ==========================
Method Name  Meaning
===========  ==========================
create       create new records
read         read records
update       update existing records
delete       delete records
review       review unapproved records
approve      approve records
===========  ==========================

.. function:: auth.s3_has_permission(method, table, record_id=None, c=None, f=None):

    Check whether the current user has permission to perform an action
    in the given context.

    :param str method: the access method
    :param str|Table table: the table
    :param int record_id: the record ID
    :param str c: the controller name (if not specified, current.request.controller will be used)
    :param str f: the function name (if not specified, current.request.function will be used)

    :returns bool: whether the intended action is permitted

.. TODO auth.s3_accessible_query
