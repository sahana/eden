Persons and Groups - *pr*
=========================

This data model describes individual persons and groups of persons.

Database Structure
------------------

.. image:: pr.png
   :align: center

Description
-----------

=======================  ===========================  =========================================
Table                    Type                         Description
=======================  ===========================  =========================================
pr_address               Object Component             Addresses
pr_contact               Object Component             Contact information (Email, Phone, ...)
**pr_group**             Main Entity                  Groups of persons
pr_group_member_role     Taxonomy                     Role of the group member within the group
**pr_group_membership**  Relationship                 Group membership
pr_group_status          Taxonomy                     Status of the group
pr_group_tag             Key-Value                    Tags for groups
pr_identity              Component                    A person's identities (ID documents)
pr_image                 Object Component             Images (e.g. Photos)
pr_pentity               Object Table (Super-Entity)  All entities representing persons
**pr_person**             Main Entity                  Individual persons
pr_person_details        Subtable                     Additional fields for pr_person
pr_person_tag            Key-Value                    Tags for persons
pr_person_user           Link Table                   Link between a person and a user account
=======================  ===========================  =========================================
