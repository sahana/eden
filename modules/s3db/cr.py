# -*- coding: utf-8 -*-

""" Shelter (Camp) Registry, model

    @copyright: 2009-2013 (c) Sahana Software Foundation
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
           "cr_shelter_rheader",
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

class S3CampDataModel(S3Model):

    names = ["cr_shelter_type",
             "cr_shelter_service",
             "cr_shelter",
             "cr_shelter_status",
             ]

    # Define a function model() which takes no parameters (except self):
    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        messages = current.messages
        super_link = self.super_link
        NAME = T("Name")

        # -------------------------------------------------------------------------
        # Shelter types
        # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
        tablename = "cr_shelter_type"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   label = NAME,
                                   requires = IS_NOT_ONE_OF(db,
                                                           "%s.name" % tablename)),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_label_camp():
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

        configure(tablename,
                  deduplicate = self.cr_shelter_type_duplicate,
                  )

        represent = S3Represent(lookup=tablename)
        shelter_type_id = S3ReusableField("shelter_type_id", table,
                                          requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "cr_shelter_type.id",
                                                                  represent)),
                                          represent = represent,
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
                             Field("name", notnull=True,
                                   label = NAME,
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_label_camp():
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
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             super_link("pe_id", "pr_pentity"),
                             super_link("site_id", "org_site"),
                             #Field("code",
                             #      length=10,           # Mayon compatibility
                             #      notnull=True,
                             #      unique=True, label=T("Code")),
                             Field("name", notnull=True,
                                   length=64,            # Mayon compatibility
                                   requires = IS_NOT_EMPTY(),
                                   label = T("Shelter Name")
                                   ),
                             self.org_organisation_id(
                                widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
                             ),
                             shelter_type_id(),          # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
                             shelter_service_id(),       # e.g. medical, housing, food, ...
                             self.gis_location_id(),
                             Field("phone",
                                   label = T("Phone"),
                                   requires = IS_NULL_OR(s3_phone_requires)),
                             self.pr_person_id(label = T("Contact Person")),
                             Field("capacity_day", "integer",
                                   label = T("Capacity (Day)"),
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 999999)),
                                   represent=lambda v: \
                                                IS_INT_AMOUNT.represent(v),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Capacity (Day / Evacuation)"),
                                                                   T("Evacuation is short-term whilst storm passing e.g. 12 hours, hence people need less space."))),
                                   ),
                             Field("capacity_night", "integer",
                                   label = T("Capacity (Night)"),
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 999999)),
                                   represent=lambda v: \
                                                IS_INT_AMOUNT.represent(v),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Capacity (Night / Post-Impact)"),
                                                                   T("Post-impact shelterees are there for a longer time, so need more space to Sleep."))),
                                   ),
                             Field("population", "integer",
                                   label = T("Population"),
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 999999)),
                                   represent=lambda v: \
                                                IS_INT_AMOUNT.represent(v)
                                   ),
                             Field("status", "integer",
                                   requires = IS_NULL_OR(
                                                IS_IN_SET(cr_shelter_opts)
                                                ),
                                   represent = lambda opt: \
                                        cr_shelter_opts.get(opt, messages.UNKNOWN_OPT),
                                   label = T("Status")),
                             Field("source",
                                   readable = False,
                                   writable = False,
                                   label = T("Source")),
                             s3_comments(),
                             Field("obsolete", "boolean",
                                   label = T("Obsolete"),
                                   represent = lambda bool: \
                                     (bool and [T("Obsolete")] or [messages["NONE"]])[0],
                                   default = False,
                                   readable = False,
                                   writable = False),
                             *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_label_camp():
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

        # Search method
        cr_shelter_search = S3Search(
            advanced=(S3SearchSimpleWidget(
                        name="shelter_search_advanced",
                        label=T("Name or Organization"),
                        comment=T("To search for a shelter, enter any of the names of the shelter, or the organisation name or acronym, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all shelters."),
                        field=["name",
                               "code",
                               #"aka1",
                               #"aka2",
                               #"gov_uuid",
                               "organisation_id$name",
                               "organisation_id$acronym"
                               ]
                      ),
                      S3SearchOptionsWidget(
                            name="shelter_search_type",
                            label=T("Type"),
                            field="shelter_type_id"
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_L1",
                            field="location_id$L1",
                            location_level="L1",
                            cols = 3,
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_L2",
                            field="location_id$L2",
                            location_level="L2",
                            cols = 3,
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_L3",
                            field="location_id$L3",
                            location_level="L3",
                            cols = 3,
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_status",
                            label=T("Status"),
                            field="status",
                            options = cr_shelter_opts,
                          ),
                    ))

        report_fields = ["name",
                         "shelter_type_id",
                         #"organisation_id",
                         "location_id$L1",
                         "location_id$L2",
                         "location_id$L3",
                         "status",
                         "population",
                         ]

        configure(tablename,
                  super_entity=("org_site", "doc_entity", "pr_pentity"),
                  search_method=cr_shelter_search,
                  deduplicate = self.cr_shelter_duplicate,
                  report_options = Storage(
                        search=[
                          S3SearchOptionsWidget(
                            name="shelter_search_type",
                            label=T("Type"),
                            field="shelter_type_id"
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_L1",
                            field="location_id$L1",
                            location_level="L1",
                            cols = 3,
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_L2",
                            field="location_id$L2",
                            location_level="L2",
                            cols = 3,
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_L3",
                            field="location_id$L3",
                            location_level="L3",
                            cols = 3,
                          ),
                          S3SearchOptionsWidget(
                            name="shelter_search_status",
                            label=T("Status"),
                            field="status",
                            options = cr_shelter_opts,
                          ),
                        ],
                        rows=report_fields,
                        cols=report_fields,
                        fact=report_fields,
                        methods=["count", "list", "sum"],
                        defaults=Storage(rows="location_id$L2",
                                         cols="status",
                                         fact="name",
                                         aggregate="count")
                   ),
                   list_fields=["id",
                                "name",
                                "status",
                                "shelter_type_id",
                                #"shelter_service_id",
                                "capacity_day",
                                "capacity_night",
                                "population",
                                "location_id$addr_street",
                                "location_id$L1",
                                "location_id$L2",
                                "location_id$L3",
                                #"person_id",
                                ]
                   )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        shelter_id = S3ReusableField("shelter_id", table,
                                     requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "cr_shelter.id",
                                                              represent,
                                                              sort=True)),
                                     represent = represent,
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

        self.add_component("cr_shelter_status",
                           cr_shelter=dict(joinby="shelter_id",
                                           name="status"))

        # -------------------------------------------------------------------------
        # Shelter statuses
        # - a historical record of shelter status: opening/closing dates & populations
        #
        tablename = "cr_shelter_status"
        table = define_table(tablename,
                             shelter_id(ondelete = "CASCADE"),
                             s3_date(),
                             Field("status", "integer",
                                   requires = IS_NULL_OR(
                                                IS_IN_SET(cr_shelter_opts)
                                                ),
                                   represent = lambda opt: \
                                        cr_shelter_opts.get(opt, messages.UNKNOWN_OPT),
                                   label = T("Status")),
                             Field("population", "integer",
                                   label = T("Population"),
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 999999)),
                                   represent=lambda v: \
                                                IS_INT_AMOUNT.represent(v)
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_label_camp():
            ADD_SHELTER_STATUS = T("Add Camp Status")
            SHELTER_STATUS_LABEL = T("Camp Status")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_STATUS,
                title_display = T("Camp Status Details"),
                title_list = T("Camp Statuses"),
                title_update = T("Edit Camp Status"),
                title_search = T("Search Camp Statuses"),
                subtitle_create = T("Add New Camp Status"),
                label_list_button = T("List Camp Statuses"),
                label_create_button = ADD_SHELTER_STATUS,
                msg_record_created = T("Camp Status added"),
                msg_record_modified = T("Camp Status updated"),
                msg_record_deleted = T("Camp Status deleted"),
                msg_list_empty = T("No Camp Statuses currently registered"),
                name_nice = T("Camp Status"),
                name_nice_plural = T("Camp Statuses"))
        else:
            ADD_SHELTER_STATUS = T("Add Shelter Status")
            SHELTER_STATUS_LABEL = T("Shelter Status")
            crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_STATUS,
                title_display = T("Shelter Status Details"),
                title_list = T("Shelter Statuses"),
                title_update = T("Edit Shelter Status"),
                title_search = T("Search Shelter Statuses"),
                subtitle_create = T("Add New Shelter Status"),
                label_list_button = T("List Shelter Statuses"),
                label_create_button = ADD_SHELTER_STATUS,
                msg_record_created = T("Shelter Status added"),
                msg_record_modified = T("Shelter Status updated"),
                msg_record_deleted = T("Shelter Status deleted"),
                msg_list_empty = T("No Shelter Statuses currently registered"),
                name_nice = T("Shelter Status"),
                name_nice_plural = T("Shelter Statuses"))

        # Pass variables back to global scope (response.s3.*)
        return Storage(
                ADD_SHELTER = ADD_SHELTER,
                SHELTER_LABEL = SHELTER_LABEL,
            )

    # -----------------------------------------------------------------------------
    def defaults(self):
        #cr_shelter_id = S3ReusableField("shelter_id", "integer",
        #                                readable=False,
        #                                writable=False)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_onaccept(form):
        """
            After DB I/O
        """

        # @ToDo: Update/Create a cr_shelter_status record
        # Status & Population
        pass

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_status_onaccept(form):
        """
            After DB I/O
        """

        # @ToDo: Update the cr_shelter record
        # Status & Population
        pass

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_duplicate(item):
        """
            Shelter record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        if item.tablename == "cr_shelter":
            data = item.data
            #org = "organisation_id" in data and data.organisation_id
            address = "address" in data and data.address

            table = item.table
            query = (table.name == data.name)
            #if org:
            #    query = query & (table.organisation_id == org)
            if address:
                query = query & (table.address == address)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_type_duplicate(item):
        """
            Shelter Type record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        if item.tablename == "cr_shelter_type":
            table = item.table
            query = (table.name == item.data.name)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_service_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages["NONE"]

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
            return current.messages["NONE"]

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

# =============================================================================
def cr_shelter_rheader(r, tabs=[]):
    """ Resource Headers """

    rheader = None
    if r.representation == "html":

        tablename, record = s3_rheader_resource(r)
        if tablename == "cr_shelter" and record:
            T = current.T
            s3db = current.s3db
            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Status"), "status"),
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

    return rheader

# END =========================================================================

