# -*- coding: utf-8 -*-

""" Shelter (Camp) Registry, model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3CampDataModel",
           "cr_shelter_rheader"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from eden.layouts import S3AddResourceLink

class S3CampDataModel(S3Model):

    names = ["cr_shelter_type",
             "cr_shelter_service",
             "cr_shelter",
             ]

    # Define a function model() which takes no parameters (except self):
    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        messages = current.messages

        # -------------------------------------------------------------------------
        # Shelter types
        # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
        tablename = "cr_shelter_type"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   requires = IS_NOT_ONE_OF(db,
                                                           "%s.name" % tablename)),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_camp():
            ADD_SHELTER_TYPE = T("Add Camp Type")
            SHELTER_TYPE_LABEL = T("Camp Type")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_TYPE,
                title_display = T("Camp Type Details"),
                title_list = T("Camp Types"),
                title_update = T("Edit Camp Type"),
                title_search = T("Search Camp Types"),
                subtitle_create = T("Add New Camp Type"),
                label_list_button = T("List Camp Types"),
                label_create_button = ADD_SHELTER_TYPE,
                msg_record_created = T("Camp Type added"),
                msg_record_modified = T("Camp Type updated"),
                msg_record_deleted = T("Camp Type deleted"),
                msg_list_empty = T("No Camp Types currently registered"),
                name_nice = T("Camp"),
                name_nice_plural = T("Camps"))
        else:
            ADD_SHELTER_TYPE = T("Add Shelter Type")
            SHELTER_TYPE_LABEL = T("Shelter Type")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_TYPE,
                title_display = T("Shelter Type Details"),
                title_list = T("Shelter Types"),
                title_update = T("Edit Shelter Type"),
                title_search = T("Search Shelter Types"),
                subtitle_create = T("Add New Shelter Type"),
                label_list_button = T("List Shelter Types"),
                label_create_button = ADD_SHELTER_TYPE,
                msg_record_created = T("Shelter Type added"),
                msg_record_modified = T("Shelter Type updated"),
                msg_record_deleted = T("Shelter Type deleted"),
                msg_list_empty = T("No Shelter Types currently registered"),
                name_nice = T("Shelter"),
                name_nice_plural = T("Shelters"))

        shelter_type_id = S3ReusableField("shelter_type_id", table,
                                          requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "cr_shelter_type.id",
                                                                  self.cr_shelter_type_represent)),
                                          represent = self.cr_shelter_type_represent,
                                          comment=S3AddResourceLink(c="cr",
                                                                    f="shelter_type",
                                                                    label=ADD_SHELTER_TYPE),
                                          ondelete = "RESTRICT",
                                          label = SHELTER_TYPE_LABEL)

        # -------------------------------------------------------------------------
        # Shelter services
        # e.g. medical, housing, food, ...
        tablename = "cr_shelter_service"
        table = define_table(tablename,
                             Field("name", notnull=True),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_camp():
            ADD_SHELTER_SERVICE = T("Add Camp Service")
            SHELTER_SERVICE_LABEL = T("Camp Service")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_SERVICE,
                title_display = T("Camp Service Details"),
                title_list = T("Camp Services"),
                title_update = T("Edit Camp Service"),
                title_search = T("Search Camp Services"),
                subtitle_create = T("Add New Camp Service"),
                label_list_button = T("List Camp Services"),
                label_create_button = ADD_SHELTER_SERVICE,
                msg_record_created = T("Camp Service added"),
                msg_record_modified = T("Camp Service updated"),
                msg_record_deleted = T("Camp Service deleted"),
                msg_list_empty = T("No Camp Services currently registered"),
                name_nice = T("Camp Service"),
                name_nice_plural = T("Camp Services"))
        else:
            ADD_SHELTER_SERVICE = T("Add Shelter Service")
            SHELTER_SERVICE_LABEL = T("Shelter Service")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_SERVICE,
                title_display = T("Shelter Service Details"),
                title_list = T("Shelter Services"),
                title_update = T("Edit Shelter Service"),
                title_search = T("Search Shelter Services"),
                subtitle_create = T("Add New Shelter Service"),
                label_list_button = T("List Shelter Services"),
                label_create_button = ADD_SHELTER_SERVICE,
                msg_record_created = T("Shelter Service added"),
                msg_record_modified = T("Shelter Service updated"),
                msg_record_deleted = T("Shelter Service deleted"),
                msg_list_empty = T("No Shelter Services currently registered"),
                name_nice = T("Shelter Service"),
                name_nice_plural = T("Shelter Services"))

        shelter_service_id = S3ReusableField("shelter_service_id",
                                             "list:reference cr_shelter_service",
                                             sortby="name",
                                             requires = IS_NULL_OR(
                                                            IS_ONE_OF(db,
                                                                      "cr_shelter_service.id",
                                                                      self.cr_shelter_service_represent,
                                                                      multiple=True)),
                                             represent = self.cr_shelter_service_multirepresent,
                                             label = SHELTER_SERVICE_LABEL,
                                             comment = S3AddResourceLink(c="cr",
                                                                         f="shelter_service",
                                                                         label=ADD_SHELTER_SERVICE),
                                             ondelete = "RESTRICT",
                                             #widget = SQLFORM.widgets.checkboxes.widget
                                             )

        # -------------------------------------------------------------------------
        cr_shelter_opts = {
            1 : T("Closed"),
            2 : T("Open")
        }

        tablename = "cr_shelter"
        table = db.define_table(tablename,
                                self.super_link("site_id", "org_site"),
                                #Field("code",
                                #      length=10,           # Mayon compatibility
                                #      notnull=True,
                                #      unique=True, label=T("Code")),
                                Field("name", notnull=True,
                                      length=64,            # Mayon compatibility
                                      requires = IS_NOT_EMPTY(),
                                      label = T("Shelter Name")),
                                organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile=True)),
                                shelter_type_id(),          # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
                                shelter_service_id(),       # e.g. medical, housing, food, ...
                                location_id(),
                                Field("phone", label = T("Phone"),
                                      requires = IS_NULL_OR(s3_phone_requires)),
                                person_id(label = T("Contact Person")),
                                Field("capacity", "integer",
                                      label = T("Capacity (Max Persons)"),
                                      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                      represent=lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                                Field("population", "integer",
                                      label = T("Population"),
                                      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                      represent=lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                                Field("status", "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(cr_shelter_opts)),
                                      represent = lambda opt: \
                                        cr_shelter_opts.get(opt, messages.UNKNOWN_OPT),
                                      label = T("Status")),
                                Field("source",
                                      label = T("Source")),
                                s3_comments(),
                                Field("obsolete", "boolean",
                                   label = T("Obsolete"),
                                   represent = lambda bool: \
                                     (bool and [T("Obsolete")] or [messages.NONE])[0],
                                   default = False,
                                   readable = False,
                                   writable = False),
                                *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_camp():
            ADD_SHELTER = T("Add Camp")
            SHELTER_LABEL = T("Camp")
            SHELTER_HELP = T("The Camp this Request is from")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER,
                title_display = T("Camp Details"),
                title_list = T("Camps"),
                title_update = T("Edit Camp"),
                title_search = T("Search Camps"),
                subtitle_create = T("Add New Camp"),
                label_list_button = T("List Camps"),
                label_create_button = ADD_SHELTER,
                msg_record_created = T("Camp added"),
                msg_record_modified = T("Camp updated"),
                msg_record_deleted = T("Camp deleted"),
                msg_list_empty = T("No Camps currently registered"),
                name_nice = T("Camp"),
                name_nice_plural = T("Camps"))

        else:
            ADD_SHELTER = T("Add Shelter")
            SHELTER_LABEL = T("Shelter")
            SHELTER_HELP = T("The Shelter this Request is from")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER,
                title_display = T("Shelter Details"),
                title_list = T("Shelters"),
                title_update = T("Edit Shelter"),
                title_search = T("Search Shelters"),
                subtitle_create = T("Add New Shelter"),
                label_list_button = T("List Shelters"),
                label_create_button = ADD_SHELTER,
                msg_record_created = T("Shelter added"),
                msg_record_modified = T("Shelter updated"),
                msg_record_deleted = T("Shelter deleted"),
                msg_list_empty = T("No Shelters currently registered"),
                name_nice = T("Shelter"),
                name_nice_plural = T("Shelters"))

        # Reusable field
        shelter_id = S3ReusableField("shelter_id", table,
                                     requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "cr_shelter.id",
                                                              self.cr_shelter_represent,
                                                              sort=True)),
                                     represent = self.cr_shelter_represent,
                                     ondelete = "RESTRICT",
                                     comment=S3AddResourceLink(c="cr",
                                                               f="shelter",
                                                               label=ADD_SHELTER,
                                                               title=SHELTER_LABEL,
                                                               tooltip="%s (%s)." % (SHELTER_HELP,
                                                                                    T("optional"))),
                                     label = SHELTER_LABEL,
                                     widget = S3AutocompleteWidget("cr", "shelter")
                                     )

        # Add Shelters as component of Services, Types as a simple way
        # to get reports showing shelters per type, etc.
        self.add_component(tablename,
                            cr_shelter_type="shelter_type_id")
                            # @todo: can't use a list:reference type for a
                            # component link => use a link table instead!
                            #cr_shelter_service="shelter_service_id")

        self.configure(tablename,
                        super_entity="org_site",
                        # Update the Address Fields
                        #onvalidation=s3_address_onvalidation,
                        list_fields=["id",
                                     "name",
                                     "status",
                                     "shelter_type_id",
                                     "shelter_service_id",
                                     "capacity",
                                     "population",
                                     "location_id$addr_street",
                                     "location_id$L1",
                                     "location_id$L2",
                                     "location_id$L3",
                                     "person_id",
                                    ])

        # Pass variables back to global scope (response.s3.*)
        return Storage(
                ADD_SHELTER = ADD_SHELTER,
                SHELTER_LABEL = SHELTER_LABEL
            )

    # -----------------------------------------------------------------------------
    def defaults(self):
        shelter_id = S3ReusableField("shelter_id", "integer",
                                      readable=False,
                                      writable=False)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.cr_shelter
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.cr_shelter_type
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_service_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.cr_shelter_service
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -----------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_service_multirepresent(shelter_service_ids):
        """
        """
        if not shelter_service_ids:
            return current.messages.NONE

        db = current.db
        table = db.cr_shelter_service
        if isinstance(shelter_service_ids, (list, tuple)):
            query = (table.id.belongs(shelter_service_ids))
            shelter_services = db(query).select(table.name)
            return ", ".join([s.name for s in shelter_services])
        else:
            query = (table.id == shelter_service_ids)
            shelter_service = db(query).select(table.name,
                                               limitby=(0, 1)).first()
            try:
                return shelter_service.name
            except:
                return current.messages.UNKNOWN_OPT

# -----------------------------------------------------------------------------
def cr_shelter_rheader(r, tabs=[]):
    """ Resource Headers """

    rheader = None
    if r.representation == "html":

        T = current.T
        s3db = current.s3db
        tablename, record = s3_rheader_resource(r)

        if tablename == "cr_shelter" and record:
            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("People"), "presence"),
                        (T("Staff"), "human_resource"),
                        (T("Assign Staff"), "human_resource_site"),
                    ]
                if current.deployment_settings.has_module("assess"):
                    tabs.append((T("Assessments"), "rat"))

                try:
                    tabs = tabs + s3db.req_tabs(r)
                except:
                    pass
                try:
                    tabs = tabs + s3db.inv_tabs(r)
                except:
                    pass

            rheader_tabs = s3_rheader_tabs(r, tabs)

            if r.name == "shelter":
                location = s3db.gis_location_represent(record.location_id)

                rheader = DIV(TABLE(
                                    TR(
                                        TH("%s: " % T("Name")), record.name
                                      ),
                                    TR(
                                        TH("%s: " % T("Location")), location
                                      ),
                                    ),
                              rheader_tabs)
            else:
                rheader = DIV(TABLE(
                                    TR(
                                        TH("%s: " % T("Name")), record.name
                                      ),
                                    ),
                              rheader_tabs)

            #if r.component and r.component.name == "req":
                # Inject the helptext script
            #    rheader.append(response.s3.req_helptext_script)

        elif tablename == "cr_shelter_type" and record:

            tabs = [(T("Basic Details"), None),
                    (current.response.s3.crud_strings["cr_shelter"].subtitle_list,
                     "shelter")]
            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader = DIV(rheader_tabs)

    return rheader

# END =========================================================================

