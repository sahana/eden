# -*- coding: utf-8 -*-

""" Sahana Eden Organisation Model

    @author: Fran Boon <fran[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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

__all__ = ["S3OrganisationModel",
           "S3SiteModel",
           "S3RoomModel",
           "S3OfficeModel",
           "org_organisation_represent",
           "org_organisation_rheader",
           "org_site_represent",
           "org_office_rheader",
           ]

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from ..s3 import *

T = current.T
organisation_type_opts = {
    1:T("Government"),
    2:T("Embassy"),
    3:T("International NGO"),
    4:T("Donor"),               # Don't change this number without changing organisation_popup.html
    6:T("National NGO"),
    7:T("UN"),
    8:T("International Organization"),
    9:T("Military"),
    10:T("Private"),
    11:T("Intergovernmental Organization"),
    12:T("Institution"),
    13:T("Red Cross / Red Crescent")
    #12:"MINUSTAH"   Haiti-specific
}

# =============================================================================
class S3OrganisationModel(S3Model):

    names = ["org_sector",
             "org_sector_id",
             "org_subsector",
             "org_organisation",
             "org_organisation_id",
            ]

    def model(self):

        import copy

        T = current.T
        db = current.db
        gis = current.gis
        s3 = current.response.s3
        settings = current.deployment_settings

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        SELECT_LOCATION = messages.SELECT_LOCATION

        # ---------------------------------------------------------------------
        # Sector
        # (Cluster in UN-style terminology)
        #
        tablename = "org_sector"
        table = self.define_table(tablename,
                                  Field("abrv", length=64,
                                        notnull=True, unique=True,
                                        label=T("Abbreviation")),
                                  Field("name", length=128,
                                        notnull=True, unique=True,
                                        label=T("Name")),
                                  *s3.meta_fields())

        # CRUD strings
        if settings.get_ui_cluster():
            SECTOR = T("Cluster")
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Cluster"),
                title_display = T("Cluster Details"),
                title_list = T("List Clusters"),
                title_update = T("Edit Cluster"),
                title_search = T("Search Clusters"),
                subtitle_create = T("Add New Cluster"),
                subtitle_list = T("Clusters"),
                label_list_button = T("List Clusters"),
                label_create_button = T("Add New Cluster"),
                label_delete_button = T("Delete Cluster"),
                msg_record_created = T("Cluster added"),
                msg_record_modified = T("Cluster updated"),
                msg_record_deleted = T("Cluster deleted"),
                msg_list_empty = T("No Clusters currently registered"))
        else:
            SECTOR = T("Sector")
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Sector"),
                title_display = T("Sector Details"),
                title_list = T("List Sectors"),
                title_update = T("Edit Sector"),
                title_search = T("Search Sectors"),
                subtitle_create = T("Add New Sector"),
                subtitle_list = T("Sectors"),
                label_list_button = T("List Sectors"),
                label_create_button = T("Add New Sector"),
                label_delete_button = T("Delete Sector"),
                msg_record_created = T("Sector added"),
                msg_record_modified = T("Sector updated"),
                msg_record_deleted = T("Sector deleted"),
                msg_list_empty = T("No Sectors currently registered"))

        self.configure("org_sector", deduplicate=self.org_sector_deduplicate)

        sector_id = S3ReusableField("sector_id", "list:reference org_sector",
                                    sortby="abrv",
                                    requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                    "org_sector.id",
                                                                    "%(abrv)s",
                                                                    sort=True,
                                                                    multiple=True)),
                                    represent = self.org_sector_represent,
                                    label = SECTOR,
                                    ondelete = "RESTRICT")

        # =====================================================================
        # (Cluster) Subsector
        #
        tablename = "org_subsector"
        table = self.define_table(tablename,
                                  sector_id(),
                                  Field("abrv", length=64,
                                        notnull=True, unique=True,
                                        label=T("Abbreviation")),
                                  Field("name", length=128, label=T("Name")),
                                  *s3.meta_fields())

        # CRUD strings
        if settings.get_ui_cluster():
            SUBSECTOR = T("Cluster Subsector")
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Cluster Subsector"),
                title_display = T("Cluster Subsector Details"),
                title_list = T("List Cluster Subsectors"),
                title_update = T("Edit Cluster Subsector"),
                title_search = T("Search Cluster Subsectors"),
                subtitle_create = T("Add New Cluster Subsector"),
                subtitle_list = T("Cluster Subsectors"),
                label_list_button = T("List Cluster Subsectors"),
                label_create_button = T("Add Cluster Subsector"),
                label_delete_button = T("Delete Cluster Subsector"),
                msg_record_created = T("Cluster Subsector added"),
                msg_record_modified = T("Cluster Subsector updated"),
                msg_record_deleted = T("Cluster Subsector deleted"),
                msg_list_empty = T("No Cluster Subsectors currently registered"))
        else:
            SUBSECTOR = T("Subsector")
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Subsector"),
                title_display = T("Subsector Details"),
                title_list = T("List Subsectors"),
                title_update = T("Edit Subsector"),
                title_search = T("Search Subsectors"),
                subtitle_create = T("Add New Subsector"),
                subtitle_list = T("Subsectors"),
                label_list_button = T("List Subsectors"),
                label_create_button = T("Add Subsector"),
                label_delete_button = T("Delete Subsector"),
                msg_record_created = T("Subsector added"),
                msg_record_modified = T("Subsector updated"),
                msg_record_deleted = T("Subsector deleted"),
                msg_list_empty = T("No Subsectors currently registered"))

        subsector_id = S3ReusableField("subsector_id",
                                       db.org_subsector, sortby="abrv",
                                       requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                       "org_subsector.id",
                                                                       self.org_subsector_requires_represent,
                                                                       sort=True)),
                                       represent = self.org_subsector_represent,
                                       label = SUBSECTOR,
                                       #comment = Script to filter the sector_subsector drop down
                                       ondelete = "RESTRICT")

        self.configure("org_subsector", deduplicate=self.org_sector_deduplicate)
        self.add_component("org_subsector", org_sector="sector_id")

        # =============================================================================
        # Organisations
        #
        tablename = "org_organisation"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  #Field("privacy", "integer", default=0),
                                  #Field("archived", "boolean", default=False),
                                  Field("name", notnull=True, unique=True,
                                        length=128,           # Mayon Compatibility
                                        label = T("Name")),
                                  Field("acronym", length=8, label = T("Acronym"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Acronym"),
                                                                        T("Acronym of the organization's name, eg. IFRC.")))),
                                  Field("type", "integer", label = T("Type"),
                                        requires = IS_NULL_OR(IS_IN_SET(organisation_type_opts)),
                                        represent = lambda opt: \
                                            organisation_type_opts.get(opt, UNKNOWN_OPT)),
                                  sector_id(),
                                  #Field("registration", label=T("Registration")),    # Registration Number
                                  Field("region", label=T("Region")),
                                  Field("country", "string", length=2,
                                        label = T("Home Country"),
                                        requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                            lambda: gis.get_countries(key_type="code"),
                                            zero = SELECT_LOCATION)),
                                        represent = lambda code: \
                                            gis.get_country(code, key_type="code") or UNKNOWN_OPT),
                                  Field("website", label = T("Website"),
                                        requires = IS_NULL_OR(IS_URL()),
                                        represent = s3_url_represent),
                                  Field("twitter",                        # deprecated by contact component
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Twitter"),
                                                                        T("Twitter ID or #hashtag")))),
                                  Field("donation_phone", label = T("Donation Phone #"),
                                        requires = IS_NULL_OR(s3_phone_requires),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Donation Phone #"),
                                                                        T("Phone number to donate to this organization's relief efforts.")))),
                                  s3.comments(),
                                  #document_id(), # Better to have multiple Documents on a Tab
                                  *s3.meta_fields())

        # CRUD strings
        ADD_ORGANIZATION = T("Add Organization")
        LIST_ORGANIZATIONS = T("List Organizations")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ORGANIZATION,
            title_display = T("Organization Details"),
            title_list = LIST_ORGANIZATIONS,
            title_update = T("Edit Organization"),
            title_search = T("Search Organizations"),
            title_upload = T("Import Organizations"),
            subtitle_create = T("Add New Organization"),
            subtitle_list = T("Organizations"),
            label_list_button = LIST_ORGANIZATIONS,
            label_create_button = T("Add New Organization"),
            label_delete_button = T("Delete Organization"),
            msg_record_created = T("Organization added"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization deleted"),
            msg_list_empty = T("No Organizations currently registered"))

        organisation_popup_url = URL(c="org", f="organisation",
                                     args="create",
                                     vars=dict(format="popup"))

        organisation_comment = DIV(A(ADD_ORGANIZATION,
                                   _class="colorbox",
                                   _href=organisation_popup_url,
                                   _target="top",
                                   _title=ADD_ORGANIZATION),
                                 DIV(DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Organization"),
                                                           T("Enter some characters to bring up a list of possible matches")))))
                                                           # Replace with this one if using dropdowns & not autocompletes
                                                           #T("If you don't see the Organization in the list, you can add a new one by clicking link 'Add Organization'.")))))

        from_organisation_comment = copy.deepcopy(organisation_comment)
        from_organisation_comment[0]["_href"] = organisation_comment[0]["_href"].replace("popup", "popup&child=from_organisation_id")

        organisation_id = S3ReusableField("organisation_id",
                                          db.org_organisation, sortby="name",
                                          requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                          org_organisation_represent,
                                                                          orderby="org_organisation.name",
                                                                          sort=True)),
                                          represent = org_organisation_represent,
                                          label = T("Organization"),
                                          comment = organisation_comment,
                                          ondelete = "RESTRICT",
                                          # Comment this to use a Dropdown & not an Autocomplete
                                          widget = S3OrganisationAutocompleteWidget()
                                         )

        organisations_id = S3ReusableField("organisations_id",
                                           "list:reference org_organisation",
                                           sortby="name",
                                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                           "%(name)s",
                                                                           multiple=True,
                                                                           #filterby="acronym",
                                                                           #filter_opts=vol_orgs,
                                                                           orderby="org_organisation.name",
                                                                           sort=True)),
                                           represent = self.organisation_multi_represent,
                                           label = T("Organizations"),
                                           ondelete = "RESTRICT")

        # -----------------------------------------------------------------------------
        organisation_search = S3OrganisationSearch(
                # simple = (S3SearchSimpleWidget(
                    # name="org_search_text_simple",
                    # label = T("Search"),
                    # comment = T("Search for an Organization by name or acronym."),
                    # field = [ "name",
                              # "acronym",
                            # ]
                    # )
                # ),
                advanced = (S3SearchSimpleWidget(
                    name = "org_search_text_advanced",
                    label = T("Search"),
                    comment = T("Search for an Organization by name or acronym"),
                    field = [ "name",
                              "acronym",
                            ]
                    ),
                    S3SearchOptionsWidget(
                        name = "org_search_type",
                        label = T("Type"),
                        field = ["type"],
                        cols = 2
                    ),
                    S3SearchOptionsWidget(
                        name = "org_search_sector",
                        label = T("Sector"),
                        field = ["sector_id"],
                        represent = self.org_sector_represent,
                        cols = 3
                    ),
                    # Doesn't work on all versions of gluon/sqlhtml.py
                    S3SearchOptionsWidget(
                        name = "org_search_home_country",
                        label = T("Home Country"),
                        field = ["country"],
                        cols = 3
                    ),
                )
            )

        self.configure(tablename,
                       super_entity = "pr_pentity",
                       search_method=organisation_search,
                       deduplicate=self.organisation_deduplicate,
                       list_fields = ["id",
                                      "name",
                                      "acronym",
                                      "type",
                                      "sector_id",
                                      "country",
                                      "website"
                                    ])

        # Components

        # Staff
        self.add_component("hrm_human_resource",
                           org_organisation="organisation_id")

        # Projects
        if settings.get_project_drr():
            self.add_component("project_project",
                               org_organisation=Storage(
                                    link="project_organisation",
                                    joinby="organisation_id",
                                    key="project_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))
        else:
            self.add_component("project_project",
                               org_organisation="organisation_id")

        # Documents
        self.add_component("doc_document", org_organisation="organisation_id")
        self.add_component("doc_image", org_organisation="organisation_id")

        # Assets
        # @ToDo
        #self.add_component("asset_asset",
                           #org_organisation = "donated_by_id")

        # Requests
        #self.add_component("req_req",
                           #org_organisation = "donated_by_id")

        # -----------------------------------------------------------------------------
        # Enable this to allow migration of users between instances
        #self.add_component(db.auth_user,
        #                   org_organisation="organisation_id")

        # -----------------------------------------------------------------------------
        # Donors are a type of Organization
        #
        ADD_DONOR = T("Add Donor")
        ADD_DONOR_HELP = T("The Donor(s) for this project. Multiple values can be selected by holding down the 'Control' key.")
        donor_id = S3ReusableField("donor_id",
                                   "list:reference org_organisation",
                                   sortby="name",
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                   "%(name)s",
                                                                   multiple=True,
                                                                   filterby="type",
                                                                   filter_opts=[4])),
                                   represent = self.donor_represent,
                                   label = T("Funding Organization"),
                                   comment = DIV(A(ADD_DONOR,
                                                   _class="colorbox",
                                                   _href=URL(c="org", f="organisation",
                                                             args="create",
                                                             vars=dict(format="popup",
                                                                       child="donor_id")),
                                                   _target="top",
                                                   _title=ADD_DONOR),
                                                DIV( _class="tooltip",
                                                     _title="%s|%s" % (ADD_DONOR,
                                                                       ADD_DONOR_HELP))),
                                   ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                    org_sector_id = sector_id,
                    org_organisation_id = organisation_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_sector_represent(opt):
        """ Sector/Cluster representation for multiple=True options """

        db = current.db
        table = db.org_sector
        set = db(table.id > 0).select(table.id,
                                      table.abrv).as_dict()

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(set.get(o)["abrv"]) for o in opts]
            multiple = True
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(set.get(opt)["abrv"])
            multiple = False
        else:
            try:
                opt = int(opt)
            except:
                return current.messages.NONE
            else:
                opts = [opt]
                vals = str(set.get(opt)["abrv"])
                multiple = False

        if multiple:
            if len(opts) > 1:
                vals = ", ".join(vals)
            else:
                vals = len(vals) and vals[0] or ""
        return vals

    # -------------------------------------------------------------------------
    @staticmethod
    def org_sector_deduplicate(item):
        """ Import item de-duplication """

        if item.id:
            return
        if item.tablename in ("org_sector", "org_subsector"):
            db = current.db
            table = item.table
            abrv = item.data.get("abrv", None)
            name = item.data.get("name", None)
            if abrv:
                query = (table.abrv.lower() == abrv.lower())
            elif name:
                query = (table.name.lower() == name.lower())
            else:
                return
            duplicate = db(query).select(table.id,
                                         limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def org_subsector_represent(id):
        """ Subsector ID representation """

        db = current.db
        table = db.org_subsector
        query = (table.id == id)
        record = db(query).select(table.sector_id,
                                  table.abrv,
                                  limitby=(0, 1)).first()
        return org_subsector_requires_represent(record)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_subsector_requires_represent(record):
        """ Used to generate text for the Select """

        db = current.db
        table = db.org_sector
        NONE = current.messages.NONE

        if record:
            query = (table.id == record.sector_id)
            sector_record = db(query).select(table.abrv,
                                              limitby=(0, 1)).first()
            if sector_record:
                sector = sector_record.abrv
            else:
                sector = NONE
            return "%s:%s" % (sector, record.abrv)
        else:
            return NONE

    # -----------------------------------------------------------------------------
    @staticmethod
    def organisation_deduplicate(item):
        """
            Import item deduplication, match by name
            NB: usually, this is only needed to catch cases where the
                import item is misspelled (case mismatch), otherwise the
                org name is a primary key and matches automatically.
                However, if there's a spelling mistake, we would want to
                retain the original spelling *because* the name is a
                primary key.

            @param item: the S3ImportItem instance
        """

        if item.id:
            return
        if item.tablename == "org_organisation":
            db = current.db
            table = item.table
            name = "name" in item.data and item.data.name
            query = (table.name.lower() == name.lower())
            duplicate = db(query).select(table.id,
                                         table.name,
                                         limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                # Retain the correct spelling of the name
                item.data.name = duplicate.name
                item.method = item.METHOD.UPDATE

    # -----------------------------------------------------------------------------
    @staticmethod
    def organisation_multi_represent(opt):
        """
            Organisation representation
            for multiple=True options
        """

        db = current.db
        table = db.org_organisation
        NONE = current.messages.NONE

        query = (table.deleted == False)
        set = db(query).select(table.id,
                               table.name).as_dict()

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(set.get(o)["name"]) for o in opts]
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(set.get(opt)["name"])
        else:
            return NONE

        if len(opts) > 1:
            vals = ", ".join(vals)
        else:
            vals = len(vals) and vals[0] or ""
        return vals

    # -------------------------------------------------------------------------
    @staticmethod
    def donor_represent(donor_ids):
        """ Representation of donor record IDs """

        db = current.db
        table = db.org_organisation
        NONE = current.messages.NONE

        if not donor_ids:
            return NONE
        elif isinstance(donor_ids, (list, tuple)):
            query = (table.id.belongs(donor_ids))
            donors = db(query).select(table.name)
            return ", ".join([donor.name for donor in donors])
        else:
            query = (table.id == donor_ids)
            donor = db(query).select(table.name,
                                     limitby=(0, 1)).first()
            return donor and donor.name or NONE

# =============================================================================
class S3SiteModel(S3Model):


    names = ["org_site",
             "org_site_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3

        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        # =============================================================================
        # Site
        #
        # @ToDo: Rename as Facilities (ICS terminology)
        #
        # Site is a generic type for any facility (office, hospital, shelter,
        # warehouse, project site etc.) and serves the same purpose as pentity does for person
        # entity types:  It provides a common join key name across all types of
        # sites, with a unique value for each sites.  This allows other types that
        # are useful to any sort of site to have a common way to join to any of
        # them.  It's especially useful for component types.
        #
        org_site_types = auth.org_site_types

        tablename = "org_site"
        table = self.super_entity(tablename, "site_id", org_site_types,
                                  # @ToDo: Make Sites Trackable (Mobile Hospitals & Warehouses)
                                  #super_link("track_id", "sit_trackable"),
                                  #Field("code",
                                  #      length=10,           # Mayon compatibility
                                  #      notnull=True,
                                  #      unique=True,
                                  #      label=T("Code")),
                                  Field("name",
                                        length=64,           # Mayon compatibility
                                        notnull=True,
                                        #unique=True,
                                        label=T("Name")),
                                  location_id(),
                                  organisation_id(),
                                  *s3.ownerstamp())

        # -----------------------------------------------------------------------------
        site_id = self.super_link("site_id", "org_site",
                                  #writable = True,
                                  #readable = True,
                                  label = T("Facility"),
                                  default = auth.user.site_id if auth.is_logged_in() else None,
                                  represent = org_site_represent,
                                  # Comment these to use a Dropdown & not an Autocomplete
                                  widget = S3SiteAutocompleteWidget(),
                                  comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Facility"),
                                                                  T("Enter some characters to bring up a list of possible matches")))
                                )

        # Components

        # Human Resources
        self.add_component("hrm_human_resource",
                           org_site=self.super_key(table))

        # Documents
        self.add_component("doc_document",
                           org_site=self.super_key(table))
        self.add_component("doc_image",
                           org_site=self.super_key(table))

        # Inventory
        self.add_component("inv_inv_item",
                           org_site=self.super_key(table))
        self.add_component("inv_recv",
                           org_site=self.super_key(table))
        self.add_component("inv_send",
                           org_site=self.super_key(table))

        # Procurement Plans
        self.add_component("proc_plan",
                           org_site=self.super_key(table))

        # Requests
        self.add_component("req_req",
                           org_site=self.super_key(table))
        self.add_component("req_commit",
                           org_site=self.super_key(table))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                    org_site_id = site_id
                )

# =============================================================================
class S3RoomModel(S3Model):
    """
        Rooms are a location within a Site
        - used by Asset module
    """

    names = ["org_room",
             "org_room_id"
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        site_id = self.org_site_id


        # =============================================================================
        # Rooms (for Sites)
        # @ToDo: Validate to ensure that rooms are unique per facility
        #
        tablename = "org_room"
        table = self.define_table(tablename,
                                  site_id, # site_id
                                  Field("name", length=128, notnull=True),
                                  *s3.meta_fields())

        # CRUD strings
        ADD_ROOM = T("Add Room")
        LIST_ROOMS = T("List Rooms")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ROOM,
            title_display = T("Room Details"),
            title_list = LIST_ROOMS,
            title_update = T("Edit Room"),
            title_search = T("Search Rooms"),
            subtitle_create = T("Add New Room"),
            subtitle_list = T("Rooms"),
            label_list_button = LIST_ROOMS,
            label_create_button = ADD_ROOM,
            label_delete_button = T("Delete Room"),
            msg_record_created = T("Room added"),
            msg_record_modified = T("Room updated"),
            msg_record_deleted = T("Room deleted"),
            msg_list_empty = T("No Rooms currently registered"))

        room_comment = DIV(A(ADD_ROOM,
                             _class="colorbox",
                             _href=URL(c="org", f="room",
                                       args="create",
                                       vars=dict(format="popup")),
                             _target="top",
                             _title=ADD_ROOM),
                           DIV(_class="tooltip",
                               _title="%s|%s" % (ADD_ROOM,
                                                 T("Select a Room from the list or click 'Add Room'"))),
                           # Filters Room based on site
                           SCRIPT("""S3FilterFieldChange({
                                         'FilterField':   'site_id',
                                         'Field':         'room_id',
                                         'FieldPrefix':   'org',
                                         'FieldResource': 'room',
                                         });""")
                            )

        # Reusable field for other tables to reference
        room_id = S3ReusableField("room_id", db.org_room, sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                  "org_room.id",
                                                                  "%(name)s")),
                                  represent = self.org_room_represent,
                                  label = T("Room"),
                                  comment = room_comment,
                                  ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                    org_room_id = room_id,
                )

    # -----------------------------------------------------------------------------
    @staticmethod
    def org_room_represent(id):
        """ Represent a room in option fields or list views """

        NONE = current.messages.NONE

        if not id:
            return NONE

        db = current.db
        table = db.org_room

        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        if not record:
            return NONE

        return record.name

# =============================================================================
class S3OfficeModel(S3Model):

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        address_fields = s3.address_fields

        # =============================================================================
        # Offices
        #
        org_office_type_opts = {    # @ToDo: Migrate these to constants: s3.OFFICE_TYPE
            1:T("Headquarters"),
            2:T("Regional"),
            3:T("National"),
            4:T("Field"),
            5:T("Warehouse"),       # Don't change this number, as it affects the Inv module, KML Export stylesheet & OrgAuth
        }

        ADD_OFFICE = T("Add Office")
        office_comment = DIV(A(ADD_OFFICE,
                               _class="colorbox",
                               _href=URL(c="org", f="office",
                                         args="create",
                                         vars=dict(format="popup")),
                               _target="top",
                               _title=ADD_OFFICE),
                             DIV(_class="tooltip",
                                 _title="%s|%s" % (ADD_OFFICE,
                                                   T("If you don't see the Office in the list, you can add a new one by clicking link 'Add Office'."))))

        tablename = "org_office"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  self.super_link("site_id", "org_site"),
                                  Field("name", notnull=True,
                                        length=64,           # Mayon Compatibility
                                        label = T("Name")),
                                  Field("code",
                                        length=10,
                                        # Deployments that don't wants office codes can hide them
                                        #readable=False,
                                        #writable=False,
                                        # Mayon compatibility
                                        # @ToDo: Deployment Setting to add validator to make these unique
                                        #notnull=True,
                                        #unique=True,
                                        label=T("Code")),
                                  organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                  Field("type", "integer", label = T("Type"),
                                        requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts)),
                                        represent = lambda opt: \
                                          org_office_type_opts.get(opt, UNKNOWN_OPT)),
                                  Field("office_id", "reference org_office", # This form of hierarchy may not work on all Databases
                                        label = T("Parent Office"),
                                        represent = self.org_office_represent,
                                        comment = office_comment),
                                  location_id(),
                                  Field("phone1", label = T("Phone 1"),
                                        requires = IS_NULL_OR(s3_phone_requires)),
                                  Field("phone2", label = T("Phone 2"),
                                        requires = IS_NULL_OR(s3_phone_requires)),
                                  Field("email", label = T("Email"),
                                        requires = IS_NULL_OR(IS_EMAIL())),
                                  Field("fax", label = T("Fax"),
                                        requires = IS_NULL_OR(s3_phone_requires)),
                                  # @ToDo: Calculate automatically from org_staff (but still allow manual setting for a quickadd)
                                  #Field("international_staff", "integer",
                                  #      label = T("# of National Staff"),
                                  #      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                                  #Field("national_staff", "integer",
                                  #      label = T("# of International Staff"),
                                  #      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))),
                                  # @ToDo: Move to Fixed Assets
                                  #Field("number_of_vehicles", "integer",
                                  #      label = T("# of Vehicles"),
                                  #      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                                  #Field("vehicle_types", label = T("Vehicle Types")),
                                  #Field("equipment", label = T("Equipment")),
                                  Field("obsolete", "boolean",
                                        label = T("Obsolete"),
                                        represent = lambda bool: \
                                          (bool and [T("Obsolete")] or [NONE])[0],
                                        default = False),
                                  #document_id(),  # Better to have multiple Documents on a Tab
                                  s3.comments(),
                                  *(address_fields() + s3.meta_fields()))

        # Field settings
        table.office_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id",
                                                        "%(name)s",
                                                        filterby = "type",
                                                        filter_opts = [1, 2, 3, 4] # All bar '5' (Warehouse)
                                                        ))
        if not settings.get_gis_building_name():
            table.building_name.readable = False

        # CRUD strings
        LIST_OFFICES = T("List Offices")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_OFFICE,
            title_display = T("Office Details"),
            title_list = LIST_OFFICES,
            title_update = T("Edit Office"),
            title_search = T("Search Offices"),
            title_upload = T("Import Offices"),
            subtitle_create = T("Add New Office"),
            subtitle_list = T("Offices"),
            label_list_button = LIST_OFFICES,
            label_create_button = T("Add New Office"),
            label_delete_button = T("Delete Office"),
            msg_record_created = T("Office added"),
            msg_record_modified = T("Office updated"),
            msg_record_deleted = T("Office deleted"),
            msg_list_empty = T("No Offices currently registered"))

        # CRUD strings
        ADD_WH = T("Add Warehouse")
        LIST_WH = T("List Warehouses")
        warehouse_crud_strings = Storage(
            title_create = ADD_WH,
            title_display = T("Warehouse Details"),
            title_list = LIST_WH,
            title_update = T("Edit Warehouse"),
            title_search = T("Search Warehouses"),
            title_upload = T("Import Warehouses"),
            subtitle_create = T("Add New Warehouse"),
            subtitle_list = T("Warehouses"),
            label_list_button = LIST_WH,
            label_create_button = T("Add New Warehouse"),
            label_delete_button = T("Delete Warehouse"),
            msg_record_created = T("Warehouse added"),
            msg_record_modified = T("Warehouse updated"),
            msg_record_deleted = T("Warehouse deleted"),
            msg_list_empty = T("No Warehouses currently registered")
        )

        # Reusable field for other tables to reference
        office_id = S3ReusableField("office_id", db.org_office,
                        sortby="default/indexname",
                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id",
                                                        "%(name)s")),
                        represent = self.org_office_represent,
                        label = T("Office"),
                        comment = office_comment,
                        ondelete = "RESTRICT")

        # -----------------------------------------------------------------------------
        # Offices as component of Organisations
        self.add_component(table,
                           org_organisation="organisation_id")

        self.configure(tablename,
                       super_entity=("pr_pentity", "org_site"),
                       onvalidation=s3.address_onvalidation,
                       deduplicate=self.org_office_deduplicate,
                       list_fields=[ "id",
                                     "name",
                                     "organisation_id",   # Filtered in Component views
                                     "type",
                                     "L0",
                                     "L1",
                                     "L2",
                                     "L3",
                                     #"L4",
                                     "phone1",
                                     "email"
                                    ])

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                    org_office_type_opts = org_office_type_opts,
                    org_warehouse_crud_strings = warehouse_crud_strings,
                )

    # ---------------------------------------------------------------------
    @staticmethod
    def org_office_represent(id):
        """
            Represent an Office
        """

        NONE = current.messages.NONE
        if not id:
            return NONE

        db = current.db
        table = db.org_office
        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        if not record:
            return NONE

        return record.name

    # ---------------------------------------------------------------------
    @staticmethod
    def org_office_deduplicate(item):
        """
            Import item deduplication, match by name and location_id (if given)

            @param item: the S3ImportItem instance
        """

        db = current.db

        if item.id:
            return
        if item.tablename == "org_office":
            table = item.table
            name = "name" in item.data and item.data.name
            query = (table.name.lower() == name.lower())
            location_id = None
            if "location_id" in item.data:
                location_id = item.data.location_id
                # This doesn't find deleted records:
                query = query & (table.location_id == location_id)
            duplicate = db(query).select(table.id,
                                         limitby=(0, 1)).first()
            if duplicate is None and location_id:
                # Search for deleted offices with this name
                query = (table.name.lower() == name.lower()) & \
                        (table.deleted == True)
                row = db(query).select(table.id, table.deleted_fk,
                                       limitby=(0, 1)).first()
                if row:
                    fkeys = json.loads(row.deleted_fk)
                    if "location_id" in fkeys and \
                       str(fkeys["location_id"]) == str(location_id):
                        duplicate = row
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
def org_organisation_represent(id, showlink=False, acronym=True):
    """ Represent an Organisation in option fields or list views """

    db = current.db
    s3db = current.s3db
    NONE = current.messages.NONE

    if isinstance(id, Row):
        # Do not repeat the lookup if already done by IS_ONE_OF or RHeader
        org = id
    else:
        table = s3db.org_organisation
        query = (table.id == id)
        org = db(query).select(table.name,
                               table.acronym,
                               limitby = (0, 1)).first()
    if org:
        represent = org.name
        if acronym and org.acronym:
            represent = "%s (%s)" % (represent,
                                     org.acronym)
        if showlink:
            represent = A(represent,
                          _href = URL(c="org", f="organisation", args = [id]))
    else:
        represent = NONE

    return represent

# -----------------------------------------------------------------------------
def org_site_represent(id, default_label="[no label]", link = True):
    """ Represent a Facility in option fields or list views """

    db = current.db
    s3db = current.s3db
    site_str = current.messages.NONE

    stable = s3db.org_site

    if not id:
        return site_str

    if isinstance(id, Row) and "instance_type" in id:
        # Do not repeat the lookup if already done by IS_ONE_OF
        site = id
    else:
        site = db(stable._id == id).select(stable.instance_type,
                                           limitby=(0, 1)).first()
        if not site:
            return site_str

    instance_type = site.instance_type
    table = s3db[instance_type]
    try:
        table = db[instance_type]
    except:
        return site_str

    # All the current types of facility have a required "name" field that can
    # serve as their representation.
    query = (table.site_id == id)
    if instance_type == "org_office":
        record = db(query).select(table.id,
                                  table.type,
                                  table.name, limitby=(0, 1)).first()
    else:
        record = db(query).select(table.id,
                                  table.name, limitby=(0, 1)).first()

    instance_type_nice = stable.instance_type.represent(instance_type)

    try:
        if instance_type == "org_office" and record.type == 5:
             instance_type_nice = T("Warehouse")
    except:
        pass

    if record:
        site_str = "%s (%s)" % (record.name, instance_type_nice)
    else:
        # Since name is notnull for all types so far, this won't be reached.
        site_str = "[site %d] (%s)" % (id, instance_type_nice)

    if link and record:
        c, f = instance_type.split("_")
        site_str = A(site_str,
                     _href = URL(c=c, f=f,
                                 args = [record.id],
                                 extension = "" # removes the .aaData extension in paginated views!
                                 ))

    return site_str

# -----------------------------------------------------------------------------
def org_organisation_rheader(r, tabs=[]):
    """ Organization page headers """

    if r.representation == "html":

        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        T = current.T
        s3 = current.response.s3
        settings = current.deployment_settings

        # Tabs
        tabs = [(T("Basic Details"), None),
                (T("Staff & Volunteers"), "human_resource"),
                (T("Offices"), "office"),
                (T("Assessments"), "assess"),
                (T("Projects"), "project"),
                #(T("Tasks"), "task"),
               ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        organisation = r.record
        if organisation.sector_id:
            _sectors = s3.org_sector_represent(organisation.sector_id)
        else:
            _sectors = None

        try:
            _type = organisation_type_opts[organisation.type]
        except KeyError:
            _type = None

        table = r.table

        if settings.get_ui_cluster():
            sector_label = T("Cluster(s)")
        else:
            sector_label = T("Sector(s)")

        rheader = DIV(TABLE(
            TR(
                TH("%s: " % table.name.label),
                organisation.name,
                TH("%s: " % sector_label),
                _sectors),
            TR(
                #TH(A(T("Edit Organization"),
                #    _href=URL(r=request, c="org", f="organisation",
                              #args=[r.id, "update"],
                              #vars={"_next": _next})))
                TH("%s: " % table.type.label),
                _type,
                )
        ), rheader_tabs)

        return rheader

    return None

# -----------------------------------------------------------------------------
def org_office_rheader(r, tabs=[],
                       force_show_inv=False):

    """ Office/Warehouse page headers """

    if r.representation == "html":

        tablename, record = s3_rheader_resource(r)
        if tablename == "org_office" and record:
            office = record

            T = current.T
            db = current.db
            s3db = current.s3db
            s3 = current.response.s3
            settings = current.deployment_settings

            UNKNOWN_OPT = current.messages.UNKNOWN_OPT

            tabs = [(T("Basic Details"), None),
                    #(T("Contact Data"), "contact"),
                    (T("Staff"), "human_resource"),
                   ]
            try:
                tabs = tabs + s3.req_tabs(r)
            except:
                pass
            try:
                tabs = tabs + s3.inv_tabs(r, force_show_inv=force_show_inv)
            except:
                pass

            rheader_tabs = s3_rheader_tabs(r, tabs, check_active=False)

            table = s3db.org_organisation
            query = (table.id == office.organisation_id)
            organisation = db(query).select(table.name,
                                            limitby=(0, 1)).first()
            if organisation:
                org_name = organisation.name
            else:
                org_name = None

            table = s3db.org_office
            rheader = DIV(TABLE(
                          TR(
                             TH("%s: " % table.name.label),
                             office.name,
                             TH("%s: " % table.type.label),
                             s3.org_office_type_opts.get(office.type,
                                                         UNKNOWN_OPT),
                             ),
                          TR(
                             TH("%s: " % table.organisation_id.label),
                             org_name,
                             TH("%s: " % table.location_id.label),
                             s3db.gis_location_represent(office.location_id),
                             ),
                          TR(
                             TH("%s: " % table.email.label),
                             office.email,
                             TH("%s: " % table.phone1.label),
                             office.phone1,
                             ),
                          #TR(TH(A(T("Edit Office"),
                          #        _href=URL(c="org", f="office",
                          #                  args=[r.id, "update"],
                          #                  vars={"_next": _next})))
                          #   )
                              ),
                          rheader_tabs)

            if r.component and r.component.name == "req":
                # Inject the helptext script
                rheader.append(s3.req_helptext_script)
            return rheader

    return None

# END =========================================================================
