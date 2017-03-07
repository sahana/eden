# -*- coding: utf-8 -*-

""" Sahana Eden Social Tenure Domain Model
    http://stdm.gltn.net/

    @copyright: 2017 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3SocialTenureDomainModel",
           "stdm_rheader",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class S3SocialTenureDomainModel(S3Model):

    """ Details about which guided tours this Person has completed """

    names = ("stdm_tenure_role",
             "stdm_tenure_type",
             "stdm_tenure",
             "stdm_tenure_relationship",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Tenure Relationship Roles
        #
        # @ToDo: restrict these by Profile?
        #
        tablename = "stdm_tenure_role"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_ROLE = T("Create Role")
        crud_strings[tablename] = Storage(
            label_create = ADD_ROLE,
            title_display = T("Role"),
            title_list = T("Roles"),
            title_update = T("Edit Role"),
            label_list_button = T("List Roles"),
            label_delete_button = T("Delete Role"),
            msg_record_created = T("Role added"),
            msg_record_modified = T("Role updated"),
            msg_record_deleted = T("Role deleted"),
            msg_list_empty = T("No Roles currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        tenure_role_id = S3ReusableField("tenure_role_id", "reference %s" % tablename,
                                         requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "stdm_tenure_role.id",
                                                              represent,
                                                              sort=True)),
                                         represent=represent,
                                         label=T("Role"),
                                         ondelete="RESTRICT",
                                         comment = S3PopupLink(c = "stdm",
                                                               f = "tenure_role",
                                                               label = ADD_ROLE,
                                                               ),
                                         )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Tenure Types
        #
        tablename = "stdm_tenure_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Tenure Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Tenure Type"),
            title_list = T("Tenure Types"),
            title_update = T("Edit Tenure Type"),
            label_list_button = T("List Tenure Types"),
            label_delete_button = T("Delete Tenure Type"),
            msg_record_created = T("Tenure Type added"),
            msg_record_modified = T("Tenure Type updated"),
            msg_record_deleted = T("Tenure Type deleted"),
            msg_list_empty = T("No Tenure Types currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        tenure_type_id = S3ReusableField("tenure_type_id", "reference %s" % tablename,
                                         requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "stdm_tenure_type.id",
                                                              represent,
                                                              sort=True)),
                                         represent=represent,
                                         label=T("Tenure Type"),
                                         ondelete="RESTRICT",
                                         comment = S3PopupLink(c = "stdm",
                                                               f = "tenure_type",
                                                               label = ADD_TYPE,
                                                               ),
                                         )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Tenures
        #
        tablename = "stdm_tenure"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     self.gis_location_id(
                         widget = S3LocationSelector(catalog_layers = True,
                                                     points = True,
                                                     polygons = True,
                                                     ),
                     ),
                     tenure_type_id(),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Tenure"),
            title_display = T("Tenure"),
            title_list = T("Tenures"),
            title_update = T("Edit Tenure"),
            label_list_button = T("List Tenures"),
            label_delete_button = T("Delete Tenure"),
            msg_record_created = T("Tenure added"),
            msg_record_modified = T("Tenure updated"),
            msg_record_deleted = T("Tenure deleted"),
            msg_list_empty = T("No Tenures currently registered"))

        represent = S3Represent(lookup=tablename, fields=["location_id", "tenure_type_id"])
        tenure_id = S3ReusableField("tenure_id", "reference %s" % tablename,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "srdm_tenure.id",
                                                          represent,
                                                          sort=True)),
                                    represent=represent,
                                    label=T("Tenure"),
                                    ondelete="RESTRICT",
                                    )

        crud_form = S3SQLCustomForm("location_id",
                                    "tenure_type_id",
                                    S3SQLInlineComponent("tenure_relationship",
                                                         fields=["pe_id",
                                                                 "tenure_role_id",
                                                                 ],
                                                         ),
                                    "comments",
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  super_entity = "doc_entity",
                  )

        self.add_components(tablename,
                            stdm_tenure_relationship = "tenure_id",
                            )

        # ---------------------------------------------------------------------
        # Tenures <> Person Entities link
        #
        tablename = "stdm_tenure_relationship"
        define_table(tablename,
                     tenure_id(),
                     super_link("pe_id", "pr_pentity",
                                label = T("Party"),
                                readable = True,
                                writable = True,
                                represent = self.pr_pentity_represent,
                                sort = True,
                                empty = False,
                                ),
                     tenure_role_id(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        #crud_strings[tablename] = Storage(
        #    label_create = T("Add Tenure Relationship"),
        #    title_display = T("Tenure Relationship"),
        #    title_list = T("Tenure Relationships"),
        #    title_update = T("Edit Tenure Relationship"),
        #    label_list_button = T("List Tenure Relationships"),
        #    label_delete_button = T("Delete Tenure Relationship"),
        #    msg_record_created = T("Tenure Relationship added"),
        #    msg_record_modified = T("Tenure Relationship updated"),
        #    msg_record_deleted = T("Tenure Relationship deleted"),
        #    msg_list_empty = T("No Tenure Relationships currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def stdm_rheader(r):
    """ Resource Header for Social Tenure Domain Model """

    if r.representation != "html":
        return None

    s3db = current.s3db
    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "pr_person":

            tabs = ((T("Basic Details"), None),
                    (T("Identity"), "identity"),
                    (T("Address"), "address"),
                    (T("Contacts"), "contacts"),
                    (T("Groups"), "group_membership"),
                    (T("Tenures"), "tenure_relationship"),
                    )

            rheader_fields = (["first_name"],
                              ["middle_name"],
                              ["last_name"],
                              ["gender"],
                              ["date_of_birth"],
                              )

        elif tablename == "pr_group":

            tabs = ((T("Basic Details"), None),
                    (T("Address"), "address"),
                    (T("Contacts"), "contact"),
                    (T("Members"), "group_membership"),
                    (T("Tenures"), "tenure_relationship"),
                    )

            rheader_fields = [["name"],
                              ["comments"],
                              ]

        elif tablename == "gis_location":

            tabs = ((T("Basic Details"), None),
                    (T("Local Names"), "name"),
                    (T("Alternate Names"), "name_alt"),
                    (T("Key Value pairs"), "tag"),
                    )

            rheader_fields = [["name"],
                              ]

            if record.level:
                rheader_fields.append(["level"])
            else:
                tabs.append((T("Tenures"), "tenure"))

        elif tablename == "stdm_tenure":

            tabs = ((T("Basic Details"), None),
                    (T("Documents"), "document"),
                    )

            rheader_fields = (["location_id"],
                              ["tenure_type_id"],
                              )

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )

    return rheader

# END =========================================================================
