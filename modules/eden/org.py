# -*- coding: utf-8 -*-

""" Sahana Eden Organisation Model

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

__all__ = ["S3OrganisationModel",
           "S3OrganisationVirtualFields",
           "S3OrganisationSummaryModel",
           "S3OrganisationTypeTagModel",
           "S3SiteModel",
           "S3FacilityModel",
           "org_facility_rheader",
           "S3RoomModel",
           "S3OfficeModel",
           "S3OfficeSummaryModel",
           "S3OfficeTypeTagModel",
           "org_organisation_logo",
           "org_root_organisation",
           "org_organisation_requires",
           "org_organisation_represent",
           "org_site_represent",
           "org_rheader",
           "org_organisation_controller",
           "org_office_controller",
           ]

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage

from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class S3OrganisationModel(S3Model):
    """
        Organisations & their Sectors
    """

    names = ["org_sector",
             "org_sector_id",
             "org_multi_sector_id",
             "org_sector_opts",
             #"org_subsector",
             "org_organisation_type",
             "org_organisation_type_id",
             "org_organisation",
             "org_organisation_id",
             "org_organisation_branch",
             "org_organisation_user",
             ]

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis
        messages = current.messages
        settings = current.deployment_settings

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        NONE = messages.NONE
        ORGANISATION = messages.ORGANISATION

        location = current.session.s3.location_filter
        if location:
            filterby = "location_id"
            filter_opts = (location, None)
        else:
            filterby = None
            filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Sector
        # (Cluster in UN-style terminology)
        #
        tablename = "org_sector"
        table = define_table(tablename,
                             Field("name", length=128,
                                   notnull=True,
                                   label=T("Name")),
                             Field("abrv", length=64,
                                   notnull=True,
                                   label=T("Abbreviation")),
                             self.gis_location_id(
                                    widget=S3LocationAutocompleteWidget(),
                                    requires=IS_EMPTY_OR(IS_LOCATION())
                                ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_cluster():
            SECTOR = T("Cluster")
            ADD_SECTOR = T("Add Cluster")
            help = T("If you don't see the Cluster in the list, you can add a new one by clicking link 'Add Cluster'.")
            crud_strings[tablename] = Storage(
                title_create=ADD_SECTOR,
                title_display=T("Cluster Details"),
                title_list=T("Clusters"),
                title_update=T("Edit Cluster"),
                title_search=T("Search Clusters"),
                subtitle_create=T("Add New Cluster"),
                label_list_button=T("List Clusters"),
                label_create_button=T("Add New Cluster"),
                label_delete_button=T("Delete Cluster"),
                msg_record_created=T("Cluster added"),
                msg_record_modified=T("Cluster updated"),
                msg_record_deleted=T("Cluster deleted"),
                msg_list_empty=T("No Clusters currently registered"))
        else:
            SECTOR = T("Sector")
            ADD_SECTOR = T("Add Sector")
            help = T("If you don't see the Sector in the list, you can add a new one by clicking link 'Add Sector'.")
            crud_strings[tablename] = Storage(
                title_create=ADD_SECTOR,
                title_display=T("Sector Details"),
                title_list=T("Sectors"),
                title_update=T("Edit Sector"),
                title_search=T("Search Sectors"),
                subtitle_create=T("Add New Sector"),
                label_list_button=T("List Sectors"),
                label_create_button=T("Add New Sector"),
                label_delete_button=T("Delete Sector"),
                msg_record_created=T("Sector added"),
                msg_record_modified=T("Sector updated"),
                msg_record_deleted=T("Sector deleted"),
                msg_list_empty=T("No Sectors currently registered"))

        configure("org_sector", deduplicate=self.org_sector_duplicate)

        sector_comment = S3AddResourceLink(c="org", f="sector",
                                           label=ADD_SECTOR,
                                           title=SECTOR,
                                           tooltip=help)

        sector_id = S3ReusableField("sector_id", "reference org_sector",
                                    sortby="abrv",
                                    requires=IS_NULL_OR(
                                                IS_ONE_OF(db, "org_sector.id",
                                                          self.org_sector_represent,
                                                          sort=True,
                                                          filterby=filterby,
                                                          filter_opts=filter_opts,
                                                          )
                                                        ),
                                    represent=self.org_sector_multirepresent,
                                    comment=sector_comment,
                                    label=SECTOR,
                                    ondelete="SET NULL")

        multi_sector_id = S3ReusableField("multi_sector_id", "list:reference org_sector",
                                    sortby="abrv",
                                    requires=IS_NULL_OR(
                                                IS_ONE_OF(db, "org_sector.id",
                                                          self.org_sector_represent,
                                                          sort=True,
                                                          filterby=filterby,
                                                          filter_opts=filter_opts,
                                                          multiple=True
                                                          )
                                                        ),
                                    represent=self.org_sector_multirepresent,
                                    comment=sector_comment,
                                    label=SECTOR,
                                    ondelete="SET NULL")

        # =====================================================================
        # (Cluster) Subsector
        #
        # tablename = "org_subsector"
        # table = define_table(tablename,
                             # sector_id(),
                             # Field("name", length=128,
                             #       label=T("Name")),
                             # Field("abrv", length=64,
                                   # notnull=True, unique=True,
                                   # label=T("Abbreviation")),
                             # *s3_meta_fields())

        ##CRUD strings
        # if settings.get_ui_cluster():
            # SUBSECTOR = T("Cluster Subsector")
            # crud_strings[tablename] = Storage(
                # title_create = T("Add Cluster Subsector"),
                # title_display = T("Cluster Subsector Details"),
                # title_list = T("Cluster Subsectors"),
                # title_update = T("Edit Cluster Subsector"),
                # title_search = T("Search Cluster Subsectors"),
                # subtitle_create = T("Add New Cluster Subsector"),
                # label_list_button = T("List Cluster Subsectors"),
                # label_create_button = T("Add Cluster Subsector"),
                # label_delete_button = T("Delete Cluster Subsector"),
                # msg_record_created = T("Cluster Subsector added"),
                # msg_record_modified = T("Cluster Subsector updated"),
                # msg_record_deleted = T("Cluster Subsector deleted"),
                # msg_list_empty = T("No Cluster Subsectors currently registered"))
        # else:
            # SUBSECTOR = T("Subsector")
            # crud_strings[tablename] = Storage(
                # title_create = T("Add Subsector"),
                # title_display = T("Subsector Details"),
                # title_list = T("Subsectors"),
                # title_update = T("Edit Subsector"),
                # title_search = T("Search Subsectors"),
                # subtitle_create = T("Add New Subsector"),
                # label_list_button = T("List Subsectors"),
                # label_create_button = T("Add Subsector"),
                # label_delete_button = T("Delete Subsector"),
                # msg_record_created = T("Subsector added"),
                # msg_record_modified = T("Subsector updated"),
                # msg_record_deleted = T("Subsector deleted"),
                # msg_list_empty = T("No Subsectors currently registered"))

        # subsector_id = S3ReusableField("subsector_id", table,
                                       # sortby="abrv",
                                       # requires = IS_NULL_OR(
                                                        # IS_ONE_OF(db, "org_subsector.id",
                                                                  # self.org_subsector_represent,
                                                                  # sort=True)),
                                       # represent = self.org_subsector_represent,
                                       # label = SUBSECTOR,
                                       ##comment = Script to filter the sector_subsector drop down
                                       # ondelete = "SET NULL")

        # configure("org_subsector", deduplicate=self.org_sector_duplicate)
        # add_component("org_subsector", org_sector="sector_id")

        # ---------------------------------------------------------------------
        # Organisation Types
        #
        tablename = "org_organisation_type"
        table = define_table(tablename,
                             Field("name", length=128,
                                   notnull=True, unique=True,
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            title_create=T("Add Organization Type"),
            title_display=T("Organization Type Details"),
            title_list=T("Organization Types"),
            title_update=T("Edit Organization Type"),
            title_search=T("Search Organization Types"),
            subtitle_create=T("Add New Organization Type"),
            label_list_button=T("List Organization Types"),
            label_create_button=T("Add New Organization Type"),
            label_delete_button=T("Delete Organization Type"),
            msg_record_created=T("Organization Type added"),
            msg_record_modified=T("Organization Type updated"),
            msg_record_deleted=T("Organization Type deleted"),
            msg_list_empty=T("No Organization Types currently registered"))

        organisation_type_id = S3ReusableField("organisation_type_id", table,
                                sortby="name",
                                requires=IS_NULL_OR(
                                            IS_ONE_OF(db, "org_organisation_type.id",
                                                      self.org_organisation_type_represent,
                                                      sort=True
                                                      )),
                                represent=self.org_organisation_type_represent,
                                label=T("Organization Type"),
                                comment=S3AddResourceLink(c="org",
                                            f="organisation_type",
                                            label=T("Add Organization Type"),
                                            title=T("Organization Type"),
                                            tooltip=T("If you don't see the Type in the list, you can add a new one by clicking link 'Add Organization Type'.")),
                                ondelete="SET NULL")

        configure(tablename,
                  deduplicate=self.organisation_type_duplicate,
                  )

        # Tags as component of Organisation Types
        add_component("org_organisation_type_tag",
                      org_organisation_type=dict(joinby="organisation_type_id",
                                                 name="tag"))

        # ---------------------------------------------------------------------
        # Organisations
        # http://xmlns.com/foaf/0.1/Organisation
        #
        tablename = "org_organisation"
        table = define_table(tablename,
                             self.super_link("pe_id", "pr_pentity"),
                             #Field("privacy", "integer", default=0),
                             #Field("archived", "boolean", default=False),
                             Field("name", notnull=True, unique=True,
                                   length=128, # Mayon Compatibility
                                   label=T("Name")),
                             # http://hxl.humanitarianresponse.info/#abbreviation
                             Field("acronym", length=16,
                                   label=T("Acronym"),
                                   represent=lambda val: val or "",
                                   comment=DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Acronym"),
                                                                   T("Acronym of the organization's name, eg. IFRC.")))),
                             organisation_type_id(#readable = False,
                                                  #writable = False,
                                                  ),
                             multi_sector_id(#readable = False,
                                             #writable = False,
                                             ),
                             #Field("registration", label=T("Registration")),    # Registration Number
                             Field("region",
                                   label=T("Region"),
                                   #readable = False,
                                   #writable = False,
                                   represent=lambda v: v or NONE,
                                   ),
                             Field("country", "string", length=2,
                                   label=T("Home Country"),
                                   #readable = False,
                                   #writable = False,
                                   requires=IS_NULL_OR(IS_IN_SET_LAZY(
                                        lambda: gis.get_countries(key_type="code"),
                                                                  zero=messages.SELECT_LOCATION)),
                                   represent=lambda code: \
                                        gis.get_country(code, key_type="code") or messages.UNKNOWN_OPT),
                             Field("phone",
                                   label=T("Phone #"),
                                   #readable = False,
                                   #writable = False,
                                   requires=IS_NULL_OR(s3_phone_requires),
                                   represent=lambda v: v or NONE
                                   ),
                             # http://hxl.humanitarianresponse.info/#organisationHomepage
                             Field("website",
                                   label=T("Website"),
                                   requires=IS_NULL_OR(IS_URL()),
                                   represent=s3_url_represent),
                             Field("year", "integer",
                                   label=T("Year"),
                                   #readable = False,
                                   #writable = False,
                                   requires=IS_NULL_OR(IS_INT_IN_RANGE(1850, 2100)),
                                   represent=lambda v: v or NONE,
                                   comment=DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Year"),
                                                                   T("Year that the organization was founded"))),
                                   ),
                             # @ToDo: Deprecate with Contact component
                             Field("twitter",
                                   #readable = False,
                                   #writable = False,
                                   represent=lambda v: v or NONE,
                                   comment=DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Twitter"),
                                                                   T("Twitter ID or #hashtag")))),
                             Field("donation_phone",
                                   label=T("Donation Phone #"),
                                   #readable = False,
                                   #writable = False,
                                   requires=IS_NULL_OR(s3_phone_requires),
                                   represent=lambda v: v or NONE,
                                   comment=DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Donation Phone #"),
                                                                   T("Phone number to donate to this organization's relief efforts.")))),
                             Field("logo", "upload",
                                   label=T("Logo"),
                                   requires=[IS_EMPTY_OR(IS_IMAGE(maxsize=(400, 400),
                                                                    error_message=T("Upload an image file (png or jpeg), max. 400x400 pixels!"))),
                                               IS_EMPTY_OR(IS_UPLOAD_FILENAME())],
                                   represent=self.doc_image_represent,
                                   comment=DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Logo"),
                                                                   T("Logo of the organization. This should be a png or jpeg file and it should be no larger than 400x400")))
                                  ),
                             s3_comments(),
                             #document_id(), # Better to have multiple Documents on a Tab
                             * s3_meta_fields())

        table.virtualfields.append(S3OrganisationVirtualFields())

        # CRUD strings
        ADD_ORGANIZATION = T("Add Organization")
        crud_strings[tablename] = Storage(
            title_create=ADD_ORGANIZATION,
            title_display=T("Organization Details"),
            title_list=T("Organizations"),
            title_update=T("Edit Organization"),
            title_search=T("Search Organizations"),
            title_upload=T("Import Organizations"),
            subtitle_create=T("Add New Organization"),
            label_list_button=T("List Organizations"),
            label_create_button=T("Add New Organization"),
            label_delete_button=T("Delete Organization"),
            msg_record_created=T("Organization added"),
            msg_record_modified=T("Organization updated"),
            msg_record_deleted=T("Organization deleted"),
            msg_list_empty=T("No Organizations currently registered"))

        # @ToDo: Deployment_setting
        organisation_dropdown_not_ac = False
        if organisation_dropdown_not_ac:
            help = T("If you don't see the Organization in the list, you can add a new one by clicking link 'Add Organization'.")
            widget = None
        else:
            help = T("Enter some characters to bring up a list of possible matches")
            widget = S3OrganisationAutocompleteWidget()

        organisation_comment = S3AddResourceLink(c="org",
                                                 f="organisation",
                                                 label=ADD_ORGANIZATION,
                                                 title=ORGANISATION,
                                                 tooltip=help)

        from_organisation_comment = S3AddResourceLink(c="org",
                                                      f="organisation",
                                                      vars=dict(child="from_organisation_id"),
                                                      label=ADD_ORGANIZATION,
                                                      title=ORGANISATION,
                                                      tooltip=help)

        auth = current.auth
        organisation_id = S3ReusableField("organisation_id", table,
                                          sortby="name",
                                          default = auth.user.organisation_id if auth.is_logged_in() else None,
                                          requires=org_organisation_requires(),
                                          represent=org_organisation_represent,
                                          label=ORGANISATION,
                                          comment=organisation_comment,
                                          ondelete="RESTRICT",
                                          widget = None #SQLFORM.widgets.options.widget,
                                         )

        organisations_id = S3ReusableField("organisations_id",
                                           "list:reference org_organisation",
                                           sortby="name",
                                           requires=IS_NULL_OR(
                                                        IS_ONE_OF(db, "org_organisation.id",
                                                                  org_organisation_represent,
                                                                  multiple=True,
                                                                  #filterby="acronym",
                                                                  #filter_opts=vol_orgs,
                                                                  orderby="org_organisation.name",
                                                                  sort=True)),
                                           represent=self.organisation_multi_represent,
                                           label=T("Organizations"),
                                           ondelete="SET NULL")

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
                advanced=(S3SearchSimpleWidget(
                    name="org_search_text_advanced",
                    label=T("Search"),
                    comment=T("Search for an Organization by name or acronym"),
                    field=[ "name",
                              "acronym",
                              "parent.name",
                              "parent.acronym",
                            ]
                    ),
                    S3SearchOptionsWidget(
                        name="org_search_type",
                        label=T("Type"),
                        field="organisation_type_id",
                        cols=2
                    ),
                    S3SearchOptionsWidget(
                        name="org_search_sector",
                        label=SECTOR,
                        field="multi_sector_id",
                        options=self.org_sector_opts,
                        cols=3
                    ),
                    # Doesn't work on all versions of gluon/sqlhtml.py
                    S3SearchOptionsWidget(
                        name="org_search_home_country",
                        label=T("Home Country"),
                        field="country",
                        cols=3
                    ),
                )
            )

        utablename = current.auth.settings.table_user_name
        configure(tablename,
                  onaccept=self.org_organisation_onaccept,
                  ondelete=self.org_organisation_ondelete,
                  super_entity="pr_pentity",
                  referenced_by=[(utablename, "organisation_id")],
                  search_method=organisation_search,
                  deduplicate=self.organisation_duplicate,
                  list_fields=["id",
                                 "name",
                                 "acronym",
                                 "organisation_type_id",
                                 "multi_sector_id",
                                 "country",
                                 "website"
                                ])

        # Components

        # Sites
        add_component("org_site",
                      org_organisation="organisation_id")

        # Offices
        add_component("org_office",
                      org_organisation="organisation_id")

        # Warehouses
        add_component("inv_warehouse",
                      org_organisation="organisation_id")

        # Catalogs
        add_component("supply_catalog",
                      org_organisation="organisation_id")

        # Facilities
        add_component("org_facility",
                      org_organisation="organisation_id")

        # Staff
        add_component("hrm_human_resource",
                      org_organisation="organisation_id")

        # Members
        add_component("member_membership",
                      org_organisation="organisation_id")

        # Projects
        if settings.get_project_mode_3w():
            add_component("project_project",
                          org_organisation=Storage(
                                    link="project_organisation",
                                    joinby="organisation_id",
                                    key="project_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))
        else:
            add_component("project_project",
                          org_organisation="organisation_id")

        # Organisation Summary data
        if settings.get_org_summary():
            add_component("org_organisation_summary",
                          org_organisation=dict(name="summary",
                                                joinby="organisation_id"))

        # Assets
        add_component("asset_asset",
                      org_organisation="organisation_id")

        # Documents
        add_component("doc_document", org_organisation="organisation_id")
        add_component("doc_image", org_organisation="organisation_id")

        # Branches
        add_component("org_organisation",
                      org_organisation=Storage(
                                    name="branch",
                                    link="org_organisation_branch",
                                    joinby="organisation_id",
                                    key="branch_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

        # For imports
        add_component("org_organisation",
                      org_organisation=Storage(
                                    name="parent",
                                    link="org_organisation_branch",
                                    joinby="branch_id",
                                    key="organisation_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

        # Assets
        # @ToDo
        #add_component("asset_asset",
                      #org_organisation = "donated_by_id")

        # Requests
        #add_component("req_req",
                       #org_organisation = "donated_by_id")

        # -----------------------------------------------------------------------------
        # Enable this to allow migration of users between instances
        #add_component(db.auth_user,
        #              org_organisation="organisation_id")

        # -----------------------------------------------------------------------------
        # Donors are a type of Organization
        #
        # ADD_DONOR = T("Add Donor")
        # ADD_DONOR_HELP = T("The Donor(s) for this project. Multiple values can be selected by holding down the 'Control' key.")
        # donor_id = S3ReusableField("donor_id", "list:reference org_organisation",
                                   # sortby="name",
                                   # requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                   # org_organisation_represent,
                                                                   # multiple=True,
                                                                   # filterby="type",
                                                                   # filter_opts=[4])),
                                   # represent = self.donor_represent,
                                   # label = T("Funding Organization"),
                                   # comment=S3AddResourceLink(c="org",
                                                             # f="organisation",
                                                             # vars=dict(child="donor_id"),
                                                             # label=ADD_DONOR,
                                                             # tooltip=ADD_DONOR_HELP),
                                   # ondelete = "SET NULL")


        # ---------------------------------------------------------------------
        # Organisation Branches
        #
        tablename = "org_organisation_branch"
        table = define_table(tablename,
                             organisation_id(ondelete="CASCADE"),
                             organisation_id("branch_id",
                                             label=T("Branch"),
                                             ondelete="CASCADE"),
                             *s3_meta_fields())

        # CRUD strings
        ADD_BRANCH = T("Add Branch Organization")
        crud_strings[tablename] = Storage(
            title_create=ADD_BRANCH,
            title_display=T("Branch Organization Details"),
            title_list=T("Branch Organizations"),
            title_update=T("Edit Branch Organization"),
            title_search=T("Search Branch Organizations"),
            title_upload=T("Import Branch Organizations"),
            subtitle_create=T("Add New Branch Organization"),
            label_list_button=T("List Branch Organizations"),
            label_create_button=T("Add New Branch"),
            label_delete_button=T("Delete Branch"),
            msg_record_created=T("Branch Organization added"),
            msg_record_modified=T("Branch Organization updated"),
            msg_record_deleted=T("Branch Organization deleted"),
            msg_list_empty=T("No Branch Organizations currently registered"))

        configure(tablename,
                  deduplicate=self.org_branch_duplicate,
                  onaccept=self.org_branch_onaccept,
                  onvalidation=self.org_branch_onvalidation,
                  ondelete=self.org_branch_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Organisation <-> User
        #
        utable = current.auth.settings.table_user
        tablename = "org_organisation_user"
        table = define_table(tablename,
                             Field("user_id", utable),
                             organisation_id(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    org_sector_id=sector_id,
                    org_multi_sector_id=multi_sector_id,
                    org_sector_opts=self.org_sector_opts,
                    org_sector_represent = self.org_sector_represent,
                    org_organisation_type_id=organisation_type_id,
                    org_organisation_id=organisation_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_onaccept(form):
        """
            If a logo was uploaded then create the extra versions.
            Process injected fields
        """

        newfilename = form.vars.logo_newfilename
        if newfilename:
            s3db = current.s3db
            image = form.request_vars.logo
            s3db.pr_image_resize(image.file,
                                 newfilename,
                                 image.filename,
                                 (None, 60),
                                 )
            s3db.pr_image_modify(image.file,
                                 newfilename,
                                 image.filename,
                                 (None, 60),
                                 "bmp",
                                 )

        # Process Injected Fields
        if not current.deployment_settings.get_org_summary():
            return

        db = current.db
        vars = current.request.post_vars
        id = vars.id
        table = current.s3db.org_organisation_summary
        query = (table.organisation_id == id)
        existing = db(query).select(table.id,
                                    limitby=(0, 1)).first()
        if "national_staff" in vars:
            national_staff = vars.national_staff
        else:
            national_staff = None
        if "international_staff" in vars:
            international_staff = vars.international_staff
        else:
            international_staff = None

        if existing:
            db(query).update(national_staff=national_staff,
                             international_staff=international_staff
                             )
        elif national_staff or international_staff:
            table.insert(organisation_id=id,
                         national_staff=national_staff,
                         international_staff=international_staff
                         )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_ondelete(row):
        """
        """

        db = current.db
        table = db.org_organisation
        query = (table.id == row.get("id"))
        deleted_row = db(query).select(table.logo,
                                       limitby=(0, 1)).first()
        current.s3db.pr_image_delete_all(deleted_row.logo)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_sector_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.org_sector
        r = db(table.id == id).select(table.name,
                                      limitby=(0, 1)).first()
        try:
            return current.T(r.name)
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def org_sector_multirepresent(opt):
        """ Sector/Cluster representation for multiple=True options """

        if not opt:
            return current.messages.NONE

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
    def org_sector_opts():
        """
            Provide the options for Sector search filters
        """

        db = current.db
        table = db.org_sector
        location = current.session.s3.location_filter
        if location:
            query = (table.deleted == False) & \
                    (table.location_id == location)
        else:
            query = (table.deleted == False)

        opts = db(query).select(table.id,
                                table.name,
                                orderby=table.name)
        od = OrderedDict()
        for opt in opts:
            od[opt.id] = current.T(opt.name)
        return od

    # -------------------------------------------------------------------------
    @staticmethod
    def org_sector_duplicate(item):
        """ Import item de-duplication """

        if item.tablename in ("org_sector", "org_subsector"):
            table = item.table
            abrv = item.data.get("abrv", None)
            name = item.data.get("name", None)
            if abrv:
                query = (table.abrv.lower() == abrv.lower())
            elif name:
                query = (table.name.lower() == name.lower())
            else:
                return
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def org_subsector_represent(id, row=None):
        """ Subsector ID representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.org_subsector
        r = db(table.id == id).select(table.name,
                                      table.sector_id,
                                      limitby=(0, 1)).first()
        try:
            sector = db(query).select(table.abrv,
                                      limitby=(0, 1)).first()
            if sector:
                return "%s: %s" % (sector.abrv, current.T(r.name))
            else:
                return current.T(r.name)
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def organisation_type_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "org_organisation_type":
            table = item.table
            name = item.data.get("name", None)
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.org_organisation_type
        r = db(table.id == id).select(table.name,
                                      limitby=(0, 1)).first()
        try:
            return current.T(r.name)
        except:
            return current.messages.UNKNOWN_OPT

    # -----------------------------------------------------------------------------
    @staticmethod
    def organisation_duplicate(item):
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

        if item.tablename == "org_organisation":
            table = item.table
            name = "name" in item.data and item.data.name
            if name:
                query = (table.name.lower() == name.lower())
                duplicate = current.db(query).select(table.id,
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
        set = db(table.deleted == False).select(table.id,
                                                table.name).as_dict()

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(set.get(o)["name"]) for o in opts]
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(set.get(opt)["name"])
        else:
            return current.messages.NONE

        if len(opts) > 1:
            vals = ", ".join(vals)
        else:
            vals = len(vals) and vals[0] or ""
        return vals

    # -------------------------------------------------------------------------
    @staticmethod
    def donor_represent(donor_ids):
        """ Representation of donor record IDs """

        if not donor_ids:
            return current.messages.NONE

        db = current.db
        table = db.org_organisation

        if isinstance(donor_ids, (list, tuple)):
            query = (table.id.belongs(donor_ids))
            donors = db(query).select(table.name)
            return ", ".join([donor.name for donor in donors])
        else:
            query = (table.id == donor_ids)
            donor = db(query).select(table.name,
                                     limitby=(0, 1)).first()
            try:
                return donor.name
            except:
                return current.messages.UNKNOWN_OPT

    # -----------------------------------------------------------------------------
    @staticmethod
    def org_branch_duplicate(item):
        """
            An Organisation can only be a branch of one Organisation
        """

        if item.tablename == "org_organisation_branch":
            table = item.table
            branch_id = "branch_id" in item.data and item.data.branch_id
            if branch_id:
                query = (table.branch_id == branch_id)
                duplicate = current.db(query).select(table.id,
                                                     limitby=(0, 1)).first()
                if duplicate:
                    item.id = duplicate.id
                    item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def org_branch_onvalidation(form):
        """
            Prevent an Organisation from being a Branch of itself
            - this is for interactive forms, imports are caught in .xsl
        """

        vars = form.request_vars
        if vars and \
           vars.branch_id and \
           int(vars.branch_id) == int(vars.organisation_id):
            error = current.T("Cannot make an Organisation a branch of itself!")
            form.errors["branch_id"] = error
            current.response.error = error

    # -------------------------------------------------------------------------
    @staticmethod
    def org_branch_onaccept(form):
        """
            Remove any duplicate memberships and update affiliations
        """

        id = form.vars.id
        db = current.db
        table = db.org_organisation_branch
        record = db(table.id == id).select(table.branch_id,
                                           table.organisation_id,
                                           table.deleted,
                                           table.deleted_fk,
                                           limitby=(0, 1)).first()
        try:
            branch_id = record.branch_id
            organisation_id = record.organisation_id
            if branch_id and organisation_id and not record.deleted:
                query = (table.branch_id == branch_id) & \
                        (table.organisation_id == organisation_id) & \
                        (table.id != id) & \
                        (table.deleted != True)
                deleted_fk = {"branch_id": branch_id,
                              "organisation_id": organisation_id}
                db(query).update(deleted=True,
                                 branch_id=None,
                                 organisation_id=None,
                                 deleted_fk=json.dumps(deleted_fk))
            current.s3db.pr_update_affiliations(table, record)
        except:
            return

    # -------------------------------------------------------------------------
    @staticmethod
    def org_branch_ondelete(row):
        """
            Update affiliations
        """

        db = current.db
        table = db.org_organisation_branch
        record = db(table.id == row.id).select(table.branch_id,
                                               table.deleted,
                                               table.deleted_fk,
                                               limitby=(0, 1)).first()
        if record:
            current.s3db.pr_update_affiliations(table, record)
        return
# =============================================================================
class S3OrganisationVirtualFields:
    """ Virtual fields for the org_organisation table """

    def address(self):
        """ Fetch the address of an office """

        db = current.db
        s3db = current.s3db
        otable = s3db.org_office
        gtable = db.gis_location
        if hasattr(self, "org_organisation") and \
           "id" in self.org_organisation:
            query = (otable.deleted != True) & \
                    (otable.organisation_id == self.org_organisation.id) & \
                    (otable.location_id == gtable.id)
            row = db(query).select(gtable.id,
                                   limitby=(0, 1)).first()
        else:
            row = None

        if row:
            return s3db.gis_location_represent(row.id)
        else:
            return None


# =============================================================================
class S3OrganisationSummaryModel(S3Model):
    """
        Organisation Summary fields visible when settings.org.summary = True
    """

    names = ["org_organisation_summary"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Summary data
        #
        tablename = "org_organisation_summary"
        table = self.define_table(tablename,
                                  self.org_organisation_id(ondelete="CASCADE"),
                                  Field("national_staff", "integer", # national is a reserved word in Postgres
                                        requires=IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                        label=T("# of National Staff")),
                                  Field("international_staff", "integer",
                                        requires=IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                        label=T("# of International Staff")),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

# =============================================================================
class S3OrganisationTypeTagModel(S3Model):
    """
        Organisation Type Tags
    """

    names = ["org_organisation_type_tag"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Local Names
        #
        # ---------------------------------------------------------------------
        # Organisation Type Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems, such as:
        #   * HXL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "org_organisation_type_tag"
        table = self.define_table(tablename,
                                  self.org_organisation_type_id(),
                                  # key is a reserved word in MySQL
                                  Field("tag", label=T("Key")),
                                  Field("value", label=T("Value")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

# =============================================================================
class S3SiteModel(S3Model):
    """
        Site Super-Entity
    """

    names = ["org_site",
             "org_site_requires",
             "org_site_id",
             ]

    def model(self):

        T = current.T
        auth = current.auth

        # =====================================================================
        # Site / Facility (ICS terminology)
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
                                  Field("code",
                                        length=10, # Mayon compatibility
                                        writable=False,
                                        label=T("Code")),
                                  Field("name",
                                        length=64, # Mayon compatibility
                                        notnull=True,
                                        #unique=True,
                                        label=T("Name")),
                                  self.gis_location_id(),
                                  self.org_organisation_id(),
                                  Field("obsolete", "boolean",
                                        label=T("Obsolete"),
                                        represent=lambda bool: \
                                          (bool and [T("Obsolete")] or
                                           [current.messages.NONE])[0],
                                        default=False,
                                        readable=False,
                                        writable=False),
                                  *s3_ownerstamp())

        # ---------------------------------------------------------------------
        org_site_label = current.deployment_settings.get_org_site_label()
        site_id = self.super_link("site_id", "org_site",
                                  #writable = True,
                                  #readable = True,
                                  label=org_site_label,
                                  default=auth.user.site_id if auth.is_logged_in() else None,
                                  represent=org_site_represent,
                                  orderby="org_site.name",
                                  sort=True,
                                  # Comment these to use a Dropdown & not an Autocomplete
                                  widget=S3SiteAutocompleteWidget(),
                                  comment=DIV(_class="tooltip",
                                                _title="%s|%s" % (org_site_label,
                                                                  T("Enter some characters to bring up a list of possible matches")))
                                  )

        # Components
        add_component = self.add_component

        # Human Resources
        # - direct component (suitable for Create/List)
        add_component("hrm_human_resource",
                      org_site="site_id")
        # - via link table (suitable for Assign)
        add_component("hrm_human_resource_site",
                      org_site="site_id")

        # Documents
        add_component("doc_document",
                      org_site="site_id")
        add_component("doc_image",
                      org_site="site_id")

        # Inventory
        add_component("inv_inv_item",
                      org_site="site_id")
        add_component("inv_recv",
                      org_site="site_id")
        add_component("inv_send",
                      org_site="site_id")

        # Assets
        add_component("asset_asset",
                      org_site="site_id")

        # Procurement Plans
        add_component("proc_plan",
                      org_site="site_id")

        # Requests
        add_component("req_req",
                      org_site="site_id")
        add_component("req_commit",
                      org_site="site_id")

        self.configure(tablename,
                       onaccept=self.org_site_onaccept,
                       list_fields=["id",
                                     "code",
                                     "instance_type",
                                     "name",
                                     "organistion_id",
                                     "location_id"]
                       )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    org_site_id=site_id
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_site_onaccept(form):
        """
            Create the code from the name
        """
        name = form.vars.name
        if not name:
            return
        code_len = current.deployment_settings.get_org_site_code_len()
        temp_code = name[:code_len].upper()
        db = current.db
        site_table = db.org_site
        query = (site_table.code == temp_code)
        row = db(query).select(site_table.id,
                               limitby=(0, 1)).first()
        if row:
            code = temp_code
            temp_code = None
            wildcard_bit = 1
            length = len(code)
            max_wc_bit = pow(2, length)
            while not temp_code and wildcard_bit < max_wc_bit:
                wildcard_posn = []
                for w in range(length):
                    if wildcard_bit & pow(2, w):
                        wildcard_posn.append(length - (1 + w))
                wildcard_bit += 1
                code_list = S3SiteModel.getCodeList(code, wildcard_posn)
                temp_code = S3SiteModel.returnUniqueCode(code, wildcard_posn, code_list)
        if temp_code:
            db(site_table.site_id == form.vars.site_id).update(code=temp_code)

    # -------------------------------------------------------------------------
    @staticmethod
    def getCodeList(code, wildcard_posn=[]):
        """
        """
        temp_code = ""
        # Inject the wildcard charater in the right positions
        for posn in range(len(code)):
            if posn in wildcard_posn:
                temp_code += "%"
            else:
                temp_code += code[posn]
        # Now set up the db call
        db = current.db
        site_table = db.org_site
        query = site_table.code.like(temp_code)
        rows = db(query).select(site_table.id,
                                        site_table.code)
        # Extract the rows on the database to provide a list of used codes
        codeList = []
        for record in rows:
            codeList.append(record.code)
        return codeList

    # -------------------------------------------------------------------------
    @staticmethod
    def returnUniqueCode(code, wildcard_posn=[], code_list=[]):
        """
        """
        # Select the replacement letters with numbers first and then
        # followed by the letters in least commonly used order
        replacement_char = "1234567890ZQJXKVBWPYGUMCFLDHSIRNOATE"
        rep_posn = [0] * len(wildcard_posn)
        finished = False
        while (not finished):
            # Find the next code to try
            temp_code = ""
            r = 0
            for posn in range(len(code)):
                if posn in wildcard_posn:
                    temp_code += replacement_char[rep_posn[r]]
                    r += 1
                else:
                    temp_code += code[posn]
            if temp_code not in code_list:
                return temp_code
            # set up the next rep_posn
            p = 0
            while (p < len(wildcard_posn)):
                if rep_posn[p] == 35: # the maximum number of replacement characters
                    rep_posn[p] = 0
                    p += 1
                else:
                    rep_posn[p] = rep_posn[p] + 1
                    break
            # if no new permutation of replacement characters has been found
            if p == len(wildcard_posn):
                return None

# =============================================================================
class S3FacilityModel(S3Model):
    """
        Generic Site
    """

    names = ["org_facility_type",
             "org_facility",
             ]

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Facility Types (generic)
        #
        tablename = "org_facility_type"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields()
                             )

        # CRUD strings
        ADD_FAC = T("Add Facility Type")
        crud_strings[tablename] = Storage(
            title_create=ADD_FAC,
            title_display=T("Facility Type Details"),
            title_list=T("Facility Types"),
            title_update=T("Edit Facility Type"),
            title_search=T("Search Facility Types"),
            title_upload=T("Import Facility Types"),
            subtitle_create=T("Add New Facility Type"),
            label_list_button=T("List Facility Types"),
            label_create_button=T("Add New Facility Type"),
            label_delete_button=T("Delete Facility Type"),
            msg_record_created=T("Facility Type added"),
            msg_record_modified=T("Facility Type updated"),
            msg_record_deleted=T("Facility Type deleted"),
            msg_list_empty=T("No Facility Types currently registered"))

        configure(tablename,
                  deduplicate=self.org_facility_type_duplicate,
                  )

        # ---------------------------------------------------------------------
        # Facilities (generic)
        #
        tablename = "org_facility"
        table = define_table(tablename,
                             self.super_link("site_id", "org_site"),
                             Field("name", notnull=True,
                                   length=64, # Mayon Compatibility
                                   label=T("Name")),
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
                             Field("facility_type_id", "list:reference org_facility_type",
                                   requires=IS_NULL_OR(
                                                IS_ONE_OF(db, "org_facility_type.id",
                                                          self.org_facility_type_represent,
                                                          sort=True,
                                                          multiple=True)),
                                   represent=self.org_facility_type_multirepresent,
                                   comment=S3AddResourceLink(c="org",
                                                               f="facility_type",
                                                               label=ADD_FAC,
                                                               tooltip=T("Select a Facility Type from the list or click 'Add Facility Type'")),
                                   label=T("Type")),
                             self.org_organisation_id(widget=S3OrganisationAutocompleteWidget(
                                default_from_profile=True)),
                             self.gis_location_id(),
                             Field("obsolete", "boolean",
                                   label=T("Obsolete"),
                                   represent=lambda bool: \
                                     (bool and [T("Obsolete")] or [current.messages.NONE])[0],
                                   default=False,
                                   readable=False,
                                   writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_FAC = T("Add Facility")
        crud_strings[tablename] = Storage(
            title_create=ADD_FAC,
            title_display=T("Facility Details"),
            title_list=T("Facilities"),
            title_update=T("Edit Facility"),
            title_search=T("Search Facilities"),
            title_upload=T("Import Facilities"),
            subtitle_create=T("Add New Facility"),
            label_list_button=T("List Facilities"),
            label_create_button=T("Add New Facility"),
            label_delete_button=T("Delete Facility"),
            msg_record_created=T("Facility added"),
            msg_record_modified=T("Facility updated"),
            msg_record_deleted=T("Facility deleted"),
            msg_list_empty=T("No Facilities currently registered"))

        configure(tablename,
                  super_entity="org_site"
                  )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_facility_type_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "org_facility_type":
            table = item.table
            name = item.data.get("name", None)
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def org_facility_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.org_facility_type
        r = db(table.id == id).select(table.name,
                                      limitby=(0, 1)).first()
        try:
            return current.T(r.name)
        except:
            return current.messages.UNKNOWN_OPT

    # -----------------------------------------------------------------------------
    @staticmethod
    def org_facility_type_multirepresent(opt):
        """ Represent a facility type in list views """

        db = current.db
        table = db.org_facility_type
        set = db(table.id > 0).select(table.id,
                                      table.name).as_dict()

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(set.get(o)["name"]) for o in opts]
            multiple = True
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(set.get(opt)["name"])
            multiple = False
        else:
            try:
                opt = int(opt)
            except:
                return current.messages.UNKNOWN_OPT
            else:
                opts = [opt]
                vals = str(set.get(opt)["name"])
                multiple = False

        if multiple:
            if len(opts) > 1:
                vals = ", ".join(vals)
            else:
                vals = len(vals) and vals[0] or ""
        return vals

# -----------------------------------------------------------------------------
def org_facility_rheader(r, tabs=[]):

    T = current.T
    s3db = current.s3db

    # Need to use this format as otherwise /inv/incoming?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3_rheader_resource(r)
    r.record = record
    r.table = s3db[tablename]

    tabs = [(T("Details"), None)]
    try:
        tabs = tabs + s3db.req_tabs(r)
    except:
        pass
    try:
        tabs = tabs + s3db.inv_tabs(r)
    except:
        pass
    rheader_fields = [["name"], ["location_id"]]
    rheader = S3ResourceHeader(rheader_fields, tabs)(r)
    return rheader

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

        # ---------------------------------------------------------------------
        # Rooms (for Sites)
        # @ToDo: Validate to ensure that rooms are unique per facility
        #
        tablename = "org_room"
        table = self.define_table(tablename,
                                  self.org_site_id, # site_id
                                  Field("name", length=128, notnull=True),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_ROOM = T("Add Room")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create=ADD_ROOM,
            title_display=T("Room Details"),
            title_list=T("Rooms"),
            title_update=T("Edit Room"),
            title_search=T("Search Rooms"),
            subtitle_create=T("Add New Room"),
            label_list_button=T("List Rooms"),
            label_create_button=ADD_ROOM,
            label_delete_button=T("Delete Room"),
            msg_record_created=T("Room added"),
            msg_record_modified=T("Room updated"),
            msg_record_deleted=T("Room deleted"),
            msg_list_empty=T("No Rooms currently registered"))

        room_comment = DIV(
                           S3AddResourceLink(c="org",
                                         f="room",
                                         label=ADD_ROOM,
                                         tooltip=T("Select a Room from the list or click 'Add Room'")),
                           # Filters Room based on site
                           SCRIPT(
'''S3FilterFieldChange({
 'FilterField':'site_id',
 'Field':'room_id',
 'FieldPrefix':'org',
 'FieldResource':'room',
})''')
                           )

        # Reusable field for other tables to reference
        room_id = S3ReusableField("room_id", table, sortby="name",
                                  requires=IS_NULL_OR(
                                                IS_ONE_OF(db, "org_room.id",
                                                          self.org_room_represent
                                                          )),
                                  represent=self.org_room_represent,
                                  label=T("Room"),
                                  comment=room_comment,
                                  ondelete="SET NULL"
                                  )

        self.configure(tablename,
                       deduplicate=self.org_room_duplicate,
                       )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    org_room_id=room_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_room_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "org_room":
            table = item.table
            name = item.data.get("name", None)
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -----------------------------------------------------------------------------
    @staticmethod
    def org_room_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.org_room
        r = db(table.id == id).select(table.name,
                                      limitby=(0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

# =============================================================================
class S3OfficeModel(S3Model):

    names = ["org_office",
             "org_office_type",
             "org_office_type_id",
             ]

    def model(self):

        T = current.T
        db = current.db
        messages = current.messages
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Office Types
        #
        tablename = "org_office_type"
        table = define_table(tablename,
                             Field("name", length=128,
                                   notnull=True, unique=True,
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            title_create=T("Add Office Type"),
            title_display=T("Office Type Details"),
            title_list=T("Office Types"),
            title_update=T("Edit Office Type"),
            title_search=T("Search Office Types"),
            subtitle_create=T("Add New Office Type"),
            label_list_button=T("List Office Types"),
            label_create_button=T("Add New Office Type"),
            label_delete_button=T("Delete Office Type"),
            msg_record_created=T("Office Type added"),
            msg_record_modified=T("Office Type updated"),
            msg_record_deleted=T("Office Type deleted"),
            msg_list_empty=T("No Office Types currently registered"))

        office_type_id = S3ReusableField("office_type_id", table,
                                sortby="name",
                                requires=IS_NULL_OR(
                                            IS_ONE_OF(db, "org_office_type.id",
                                                      self.org_office_type_represent,
                                                      sort=True
                                                      )),
                                represent=self.org_office_type_represent,
                                label=T("Office Type"),
                                comment=S3AddResourceLink(c="org",
                                            f="office_type",
                                            label=T("Add Office Type"),
                                            title=T("Office Type"),
                                            tooltip=T("If you don't see the Type in the list, you can add a new one by clicking link 'Add Office Type'.")),
                                ondelete="SET NULL")

        configure(tablename,
                  deduplicate=self.office_type_duplicate,
                  )

        # Tags as component of Office Types
        add_component("org_office_type_tag",
                      org_office_type=dict(joinby="office_type_id",
                                           name="tag"))

        # ---------------------------------------------------------------------
        # Offices
        #
        tablename = "org_office"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             super_link("site_id", "org_site"),
                             super_link("doc_id", "doc_entity"),
                             Field("name", notnull=True,
                                   length=64, # Mayon Compatibility
                                   label=T("Name")),
                             Field("code", length=10, # Mayon compatibility
                                   label=T("Code")
                                   # Deployments that don't wants office codes can hide them
                                   #readable=False,
                                   #writable=False,
                                   # @ToDo: Deployment Setting to add validator to make these unique
                                   ),
                             self.org_organisation_id(
                                 #widget=S3OrganisationAutocompleteWidget(default_from_profile=True),
                                 requires = self.org_organisation_requires(updateable=True,
                                                                           required=True),
                                 ),
                             office_type_id(
                                            #readable = False,
                                            #writable = False,
                                            ),
                             self.gis_location_id(),
                             Field("phone1", label=T("Phone 1"),
                                   requires=IS_NULL_OR(s3_phone_requires)),
                             Field("phone2", label=T("Phone 2"),
                                   requires=IS_NULL_OR(s3_phone_requires)),
                             Field("email", label=T("Email"),
                                   requires=IS_NULL_OR(IS_EMAIL())),
                             Field("fax", label=T("Fax"),
                                   requires=IS_NULL_OR(s3_phone_requires)),
                             # @ToDo: Move to Fixed Assets
                             #Field("number_of_vehicles", "integer",
                             #      label = T("# of Vehicles"),
                             #      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                             #Field("vehicle_types", label = T("Vehicle Types")),
                             #Field("equipment", label = T("Equipment")),
                             Field("obsolete", "boolean",
                                   label=T("Obsolete"),
                                   represent=lambda bool: \
                                    (bool and [T("Obsolete")] or [messages.NONE])[0],
                                   default=False,
                                   readable=False,
                                   writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            title_create=T("Add Office"),
            title_display=T("Office Details"),
            title_list=T("Offices"),
            title_update=T("Edit Office"),
            title_search=T("Search Offices"),
            title_upload=T("Import Offices"),
            title_map=T("Map of Offices"),
            subtitle_create=T("Add New Office"),
            label_list_button=T("List Offices"),
            label_create_button=T("Add New Office"),
            label_delete_button=T("Delete Office"),
            msg_record_created=T("Office added"),
            msg_record_modified=T("Office updated"),
            msg_record_deleted=T("Office deleted"),
            msg_list_empty=T("No Offices currently registered"))

        # Search Method
        office_search = S3Search(
            advanced=(S3SearchSimpleWidget(
                        name="office_search_text",
                        label=T("Search"),
                        comment=T("Search for office by text."),
                        field=["name", "comments", "email"]
                      ),
                      S3SearchOptionsWidget(
                        name="office_search_org",
                        label=messages.ORGANISATION,
                        comment=T("Search for office by organization."),
                        field="organisation_id",
                        represent="%(name)s",
                        cols=3
                      ),
                      S3SearchOptionsWidget(
                        name="office_search_location",
                        field="location_id$L1",
                        location_level="L1",
                        cols=3
                      ),
                      S3SearchLocationWidget(
                        name="office_search_map",
                        label=T("Map"),
                      ),
            ))

        configure(tablename,
                  super_entity=("pr_pentity", "org_site"),
                  onaccept=self.org_office_onaccept,
                  deduplicate=self.org_office_duplicate,
                  search_method=office_search,
                  list_fields=["id",
                               "name",
                               "organisation_id", # Filtered in Component views
                               "type",
                               #(T("Address"), "location_id$addr_street"),
                               (messages.COUNTRY, "location_id$L0"),
                               "location_id$L1",
                               "location_id$L2",
                               "location_id$L3",
                               #"location_id$L4",
                               "phone1",
                               "email"
                               ],
                  realm_components=["contact_emergency",
                                    "config",
                                    "image",
                                    "req",
                                    "send",
                                    "human_resource_site",
                                    "note",
                                    "contact",
                                    "role",
                                    "asset",
                                    "commit",
                                    "inv_item",
                                    "document",
                                    "recv",
                                    "address",
                                    ],
                  update_realm=True,
                 )

        if current.deployment_settings.get_org_summary():
            add_component("org_office_summary",
                          org_office=dict(name="summary",
                                          joinby="office_id"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    org_office_type_id=office_type_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def office_type_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "org_office_type":
            table = item.table
            name = item.data.get("name", None)
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def org_office_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.org_office_type
        r = db(table.id == id).select(table.name,
                                      limitby=(0, 1)).first()
        try:
            return current.T(r.name)
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def org_office_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.org_office
        r = db(table.id == id).select(table.name,
                                      limitby=(0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def org_office_onaccept(form):
        """
            * Update Affiliation and Realms
            * Process injected fields
        """

        auth = current.auth
        s3db = current.s3db
        otable = s3db.org_office
        vars = form.vars

        # Affiliation, record ownership and component ownership
        s3db.pr_update_affiliations(otable, vars)

        if current.deployment_settings.get_org_summary():

            db = current.db
            id = form.vars.id
            table = current.s3db.org_office_summary
            query = (table.office_id == id)
            existing = db(query).select(table.id,
                                        limitby=(0, 1)).first()
            vars = current.request.post_vars
            if "national_staff" in vars:
                national_staff = vars.national_staff
            else:
                national_staff = None
            if "international_staff" in vars:
                international_staff = vars.international_staff
            else:
                international_staff = None

            if existing:
                db(query).update(national_staff=national_staff,
                                 international_staff=international_staff
                                 )
            elif national_staff or international_staff:
                table.insert(office_id=id,
                             national_staff=national_staff,
                             international_staff=international_staff
                             )

    # ---------------------------------------------------------------------
    @staticmethod
    def org_office_duplicate(item):
        """
            Import item deduplication, match by name
                (Adding location_id doesn't seem to be a good idea)

            @param item: the S3ImportItem instance
        """

        if item.tablename == "org_office":
            table = item.table
            name = "name" in item.data and item.data.name
            query = (table.name.lower() == name.lower())
            #location_id = None
            # if "location_id" in item.data:
                # location_id = item.data.location_id
                ## This doesn't find deleted records:
                # query = query & (table.location_id == location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            # if duplicate is None and location_id:
                ## Search for deleted offices with this name
                # query = (table.name.lower() == name.lower()) & \
                        # (table.deleted == True)
                # row = db(query).select(table.id, table.deleted_fk,
                                       # limitby=(0, 1)).first()
                # if row:
                    # fkeys = json.loads(row.deleted_fk)
                    # if "location_id" in fkeys and \
                       # str(fkeys["location_id"]) == str(location_id):
                        # duplicate = row
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3OfficeSummaryModel(S3Model):
    """
        Office Summary fields visible when settings.org.summary = True
    """

    names = ["org_office_summary"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Summary data
        #
        tablename = "org_office_summary"
        table = self.define_table(tablename,
                                  Field("office_id",
                                        requires=IS_ONE_OF(current.db, "org_office.id",
                                                             "%(name)s"),
                                        label=T("Office"),
                                        ondelete="CASCADE"
                                        ),
                                  Field("national_staff", "integer", # national is a reserved word in Postgres
                                        requires=IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                        label=T("# of National Staff")),
                                  Field("international_staff", "integer",
                                        requires=IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                        label=T("# of International Staff")),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

# =============================================================================
class S3OfficeTypeTagModel(S3Model):
    """
        Office Type Tags
    """

    names = ["org_office_type_tag"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Office Type Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems, such as:
        #   * HXL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "org_office_type_tag"
        table = self.define_table(tablename,
                                  self.org_office_type_id(),
                                  # key is a reserved word in MySQL
                                  Field("tag", label=T("Key")),
                                  Field("value", label=T("Value")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

# =============================================================================
def org_organisation_logo(id, type="png"):
    """
        Return a logo of the organisation with the given id, if one exists

        The id can either be the id of the organisation
               or a Row of the organisation

        The type can either be png or bmp and is the format of the saved image
    """

    if not id:
        return None

    s3db = current.s3db
    if isinstance(id, Row):
        # Do not repeat the lookup if already done by IS_ONE_OF or RHeader
        record = id
    else:
        table = s3db.org_organisation
        query = (table.id == id)
        record = current.db(query).select(limitby=(0, 1)).first()

    format = None
    if type == "bmp":
        format = "bmp"
    size = (None, 60)
    image = s3db.pr_image_represent(record.logo, size=size)
    url_small = URL(c="default", f="download", args=image)
    if record and image:
        if record.acronym == None or record.acronym == "":
            alt = "%s logo" % record.name
        else:
            alt = "%s logo" % record.acronym
        logo = IMG(_src=url_small,
                       _alt=alt,
                       _height=60,
                      )
        return logo
    return DIV() # no logo so return an empty div

# =============================================================================
def org_root_organisation(organisation_id=None, pe_id=None):
    """
        Lookup the root organisation of a branch organisation

        @param organisation_id: the organisation's record ID or a record
                                which contains the organisation_id
        @param pe_id: the organisation's pe_id

        @returns: tuple of (id, pe_id) of the root organisation,
                  or (None, None) if no root organisation can be found
    """

    db = current.db
    s3db = current.s3db
    otable = s3db.org_organisation
    btable = s3db.org_organisation.with_alias("org_branch_organisation")
    ltable = s3db.org_organisation_branch

    if isinstance(organisation_id, Row):
        row = organisation_id
        if "organisation_id" in row:
            organisation_id = row.organisation_id
        elif "pe_id" in row:
            organisation_id = None
            pe_id = row.pe_id
        else:
            organisation_id = None
    if not organisation_id and not pe_id:
        return None, None

    if organisation_id is None:
        query = (btable.pe_id == pe_id)
    else:
        query = (btable.id == organisation_id)

    join = (ltable.deleted != True) & \
           (btable.deleted != True) & \
           (otable.deleted != True) & \
           (btable.id == ltable.branch_id) & \
           (otable.id == ltable.organisation_id)
    row = db(query & join).select(btable.id,
                                  btable.pe_id,
                                  otable.id, limitby=(0, 1)).first()

    if row is not None:
        return org_root_organisation(row[otable.id])
    else:
        row = db(query).select(btable.id,
                               btable.pe_id,
                               limitby=(0, 1)).first()
        if row:
            return (row.id, row.pe_id)

    return None, None

# =============================================================================
def org_organisation_requires(updateable=False,
                              required=False):
    """
        Optionally: Filter the list of organisations for a form field to
        just those which the user has update permissions for
    """

    requires = IS_ONE_OF(current.db, "org_organisation.id",
                         org_organisation_represent,
                         updateable = updateable,
                         orderby = "org_organisation.name",
                         sort = True)
    if not required:
        requires = IS_NULL_OR(requires)
    return requires

# =============================================================================
def org_organisation_represent(id, row=None, show_link=False,
                               acronym=True, parent=True):
    """
        Represent an Organisation in option fields or list views

        @param show_link: whether to make the output into a hyperlink
        @param acronym: whether to show any acronym present
        @param parent: whether to show the parent Org for branches
    """

    db = current.db
    table = current.s3db.org_organisation

    if row:
        id = row.id
    elif id:
        row = db(table.id == id).select(table.name,
                                        table.acronym,
                                        limitby=(0, 1)).first()
    else:
        return current.messages.NONE

    try:
        represent = row.name
    except:
        return current.messages.UNKNOWN_OPT

    r = None
    if parent:
        btable = db.org_organisation_branch
        query = (btable.branch_id == id) & \
                (table.id == btable.organisation_id)
        r = db(query).select(table.name,
                             limitby=(0, 1)).first()
        if r:
            represent = "%s > %s" % (r.name, represent)

    if not r and acronym and row.acronym:
        represent = "%s (%s)" % (represent, row.acronym)

    if show_link:
        represent = A(represent,
                      _href=URL(c="org", f="organisation",
                                  args=id))

    return represent

# =============================================================================
def org_site_represent(id, row=None, show_link=True):
    """
        Represent a Facility in option fields or list views

        @param site_id: the org_site record ID or the org_site record
        @param show_link: whether to render the representation as link
    """

    if row:
        db = current.db
        s3db = current.s3db
        table = s3db.org_site
        id = row.site_id
    elif id:
        db = current.db
        s3db = current.s3db
        table = s3db.org_site
        if isinstance(id, Row):
            row = id
            id = row.site_id
        else:
            row = db(table._id == id).select(table.instance_type,
                                             limitby=(0, 1)).first()
    else:
        return current.messages.NONE

    instance_type = row.instance_type
    instance_type_nice = table.instance_type.represent(instance_type)
    tab = None

    try:
        table = s3db[instance_type]
    except:
        return current.messages.UNKNOWN_OPT

    r = db(table.site_id == id).select(table.id,
                                       table.name,
                                       limitby=(0, 1)).first()

    try:
        if r.name:
            represent = "%s (%s)" % (r.name, instance_type_nice)
        else:
            represent = "[site %d] (%s)" % (id, instance_type_nice)
    except:
        return current.messages.UNKNOWN_OPT

    if show_link:
        c, f = instance_type.split("_", 1)
        args = [r.id]
        if tab:
            args.append(tab)
        # extension="" removes the .aaData extension in paginated views
        represent = A(represent,
                      _href=URL(c=c, f=f, args=args, extension=""))

    return represent

# =============================================================================
def org_rheader(r, tabs=[]):
    """ Organisation/Office page headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    s3db = current.s3db

    # Need to use this format as otherwise req_match?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3_rheader_resource(r)
    r.record = record
    r.table = s3db[tablename]

    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    T = current.T
    table = s3db[tablename]
    resourcename = r.name
    settings = current.deployment_settings

    if tablename == "org_organisation":

        # Tabs
        if not tabs:
            tabs = [(T("Basic Details"), None),
                    (T("Branches"), "branch"),
                    (T("Offices"), "office"),
                    (T("Warehouses"), "warehouse"),
                    (T("Facilities"), "facility"),
                    (T("Staff & Volunteers"), "human_resource"),
                    (T("Projects"), "project"),
                    (T("User Roles"), "roles"),
                    #(T("Tasks"), "task"),
                   ]
        rheader_tabs = s3_rheader_tabs(r, tabs)

        if table.multi_sector_id.readable and record.multi_sector_id:
            if settings.get_ui_cluster():
                sector_label = T("Cluster(s)")
            else:
                sector_label = T("Sector(s)")
            sectors = TR(TH("%s: " % sector_label),
                         table.multi_sector_id.represent(record.multi_sector_id))
        else:
            sectors = ""

        if record.website:
            website = TR(TH("%s: " % table.website.label),
                         A(record.website, _href=record.website))
        else:
            website = ""

        rheader = DIV()
        logo = org_organisation_logo(record)
        rData = TABLE(
                        TR(
                            TH("%s: " % table.name.label),
                            record.name,
                          ),
                        website,
                        sectors,
                        )
        if logo:
            rheader.append(TABLE(TR(TD(logo), TD(rData))))
        else:
            rheader.append(rData)
        rheader.append(rheader_tabs)

    elif tablename == "org_office":
        tabs = [(T("Basic Details"), None),
                #(T("Contact Data"), "contact"),
                (T("Staff"), "human_resource"),

               ]
        if current.auth.s3_has_permission("create", "hrm_human_resource"):
            tabs.append((T("Assign Staff"), "human_resource_site"))
        if settings.has_module("inv"):
            tabs = tabs + s3db.inv_tabs(r)
        if settings.has_module("req"):
            tabs = tabs + s3db.req_tabs(r)
        tabs.append((T("Attachments"), "document"))
        tabs.append((T("User Roles"), "roles"))

        rheader_fields = [["name", "organisation_id", "email"],
                          ["office_type_id", "location_id", "phone1"],
                          ]

        rheader_fields, rheader_tabs = S3ResourceHeader(rheader_fields,
                                                        tabs)(r, as_div=True)

        # Inject logo
        logo = org_organisation_logo(record.organisation_id)
        if logo:
            rheader = DIV(TABLE(TR(TD(logo),
                                   TD(rheader_fields))))
        else:
            rheader = DIV(rheader_fields)

        rheader.append(rheader_tabs)

        #if r.component and r.component.name == "req":
            # Inject the helptext script
            #rheader.append(s3.req_helptext_script)

    elif tablename in ("org_organisation_type", "org_office_type"):
        tabs = [(T("Basic Details"), None),
                (T("Tags"), "tag"),
               ]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(
                            TH("%s: " % table.name.label),
                            record.name,
                            )),
                      rheader_tabs)

    return rheader

# =============================================================================
def org_organisation_controller():
    """
        Organisation Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    s3db = current.s3db
    s3 = current.response.s3
    T = current.T

    # Pre-process
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.representation == "json":
            r.table.pe_id.readable = True
            list_fields = s3db.get_config(r.tablename,
                                          "list_fields") or []
            s3db.configure(r.tablename, list_fields=list_fields + ["pe_id"])
        elif r.interactive:
            request = current.request
            r.table.country.default = current.gis.get_default_country("code")

            if not r.component and r.method not in ["read", "update", "delete"]:
                # Filter out branches
                lfilter = current.session.s3.location_filter
                if lfilter:
                    # Include those whose parent is in a different country
                    db = current.db
                    gtable = s3db.gis_location
                    query = (gtable.id == lfilter)
                    row = db(query).select(gtable.id,
                                           gtable.name,
                                           gtable.level,
                                           gtable.path,
                                           limitby=(0, 1)).first()
                    if row and row.level:
                        if row.level != "L0":
                            code = current.gis.get_parent_country(row, key_type="code")
                        else:
                            ttable = s3db.gis_location_tag
                            query = (ttable.tag == "ISO2") & \
                                    (ttable.location_id == row.id)
                            tag = db(query).select(ttable.value,
                                                   limitby=(0, 1)).first()
                            code = tag.value
                        branch_filter = (S3FieldSelector("parent.id") == None) | \
                                        (S3FieldSelector("parent.country") != code) | \
                                        (S3FieldSelector("parent.country") == None)
                    else:
                        branch_filter = (S3FieldSelector("parent.id") == None)
                else:
                    branch_filter = (S3FieldSelector("parent.id") == None)
                r.resource.add_filter(branch_filter)

            elif r.component_name == "human_resource" and r.component_id:
                # Workaround until widget is fixed:
                htable = s3db.hrm_human_resource
                htable.person_id.widget = None
                htable.person_id.writable = False

            elif r.component_name == "branch":
                # Branches default to the same type/sector/country as the parent
                otable = r.table
                record = r.record
                otable.organisation_type_id.default = record.organisation_type_id
                otable.multi_sector_id.default = record.multi_sector_id
                otable.country.default = record.country
                # Represent orgs without the parent prefix as we have that context already
                s3db.org_organisation_branch.branch_id.represent = lambda val: \
                    s3db.org_organisation_represent(val, parent=False)

            elif r.component_name == "task" and \
                 r.method != "update" and r.method != "read":
                # Create or ListCreate
                ttable = r.component.table
                ttable.organisation_id.default = r.id
                ttable.status.writable = False
                ttable.status.readable = False

            elif r.component_name == "project" and r.link:
                # Hide/show host role after project selection in embed-widget
                tn = r.link.tablename
                s3db.configure(tn,
                               post_process='''hide_host_role($('#%s').val())''')
                s3.scripts.append("/%s/static/scripts/S3/s3.hide_host_role.js" % \
                    request.application)

            s3db.configure("project_project", create_next=None)

            # If a filter is being applied to the Organisations, change the CRUD Strings accordingly
            type_filter = request.get_vars["organisation.organisation_type_id$name"]
            if type_filter:
                type_crud_strings = { "Red Cross / Red Crescent" :
                                       # @ToDo: IFRC isn't an NS?
                                       Storage(title_create=T("Add National Society"),
                                                title_display=T("National Society Details"),
                                                title_list=T("Red Cross & Red Crescent National Societies"),
                                                title_update=T("Edit National Society"),
                                                title_search=T("Search Red Cross & Red Crescent National Societies"),
                                                title_upload=T("Import Red Cross & Red Crescent National Societies"),
                                                subtitle_create=T("Add National Society"),
                                                label_list_button=T("List Red Cross & Red Crescent National Societies"),
                                                label_create_button=T("Add National Society"),
                                                label_delete_button=T("Delete National Society"),
                                                msg_record_created=T("National Society added"),
                                                msg_record_modified=T("National Society updated"),
                                                msg_record_deleted=T("National Society deleted"),
                                                msg_list_empty=T("No Red Cross & Red Crescent National Societies currently registered")
                                                ),
                                     "Supplier" :
                                       Storage(title_create=T("Add Supplier"),
                                                title_display=T("Supplier Details"),
                                                title_list=T("Suppliers"),
                                                title_update=T("Edit Supplier"),
                                                title_search=T("Search Suppliers"),
                                                title_upload=T("Import Suppliers"),
                                                subtitle_create=T("Add Supplier"),
                                                label_list_button=T("List Suppliers"),
                                                label_create_button=T("Add Suppliers"),
                                                label_delete_button=T("Delete Supplier"),
                                                msg_record_created=T("Supplier added"),
                                                msg_record_modified=T("Supplier updated"),
                                                msg_record_deleted=T("Supplier deleted"),
                                                msg_list_empty=T("No Suppliers currently registered")
                                                ),
                                     "Bilateral,Government,Intergovernmental,NGO,UN agency" :
                                       Storage(title_create=T("Add Partner Organisation"),
                                                title_display=T("Partner Organisation Details"),
                                                title_list=T("Partner Organisations"),
                                                title_update=T("Edit Partner Organisation"),
                                                title_search=T("Search Partner Organisations"),
                                                title_upload=T("Import Partner Organisations"),
                                                subtitle_create=T("Add Partner Organisation"),
                                                label_list_button=T("List Partner Organisations"),
                                                label_create_button=T("Add Partner Organisations"),
                                                label_delete_button=T("Delete Partner Organisation"),
                                                msg_record_created=T("Partner Organisation added"),
                                                msg_record_modified=T("Partner Organisation updated"),
                                                msg_record_deleted=T("Partner Organisation deleted"),
                                                msg_list_empty=T("No Partner Organisations currently registered")
                                                ),
                                    }
                if type_filter in type_crud_strings:
                    s3.crud_strings.org_organisation = type_crud_strings[type_filter]

                # default the Type
                if not r.method or r.method == "create":
                    type_table = s3db.org_organisation_type
                    query = type_table.name == type_filter
                    row = current.db(query).select(type_table.id,
                                                   limitby=(0, 1)).first()
                    type = row and row.id
                    if type:
                        org_type_field = s3db.org_organisation.organisation_type_id
                        org_type_field.default = type
                        org_type_field.writable = False

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component and \
               current.deployment_settings.get_org_summary():
                # Insert fields to view/record the summary data
                table = s3db.org_organisation_summary
                field1 = table.national_staff
                field2 = table.international_staff
                row = None
                if r.id:
                    query = (table.organisation_id == r.id)
                    row = current.db(query).select(field1,
                                                   field2,
                                                   limitby=(0, 1)).first()
                if r.method == "read" and \
                   "item" in output:
                    for field in [field1, field2]:
                        if row:
                            widget = row[field]
                        else:
                            widget = current.messages.NONE
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        comment = ""
                        rows = s3.crud.formstyle(row_id, label, widget, comment)
                        try:
                            # Insert Label row
                            output["item"][0].insert(-2, rows[0])
                        except:
                            pass
                        try:
                            # Insert Widget row
                            output["item"][0].insert(-2, rows[1])
                        except:
                            # A non-standard formstyle with just a single row
                            pass

                elif r.method not in ("import", "search") and \
                     "form" in output:

                    sep = ": "
                    for field in [field1, field2]:
                        if row:
                            default = row[field]
                        else:
                            default = field.default
                        widget = field.widget or SQLFORM.widgets.integer.widget(field, default)
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, label and sep, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        comment = field.comment or ""
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        rows = s3.crud.formstyle(row_id, label, widget, comment)
                        try:
                            # Insert Label row
                            output["form"][0].insert(-4, rows[0])
                        except:
                            pass
                        try:
                            # Insert Widget row
                            output["form"][0].insert(-4, rows[1])
                        except:
                            # A non-standard formstyle with just a single row
                            pass
        return output
    s3.postp = postp

    output = current.rest_controller("org", "organisation",
                                     native=False, rheader=s3db.org_rheader)
    return output

# =============================================================================
def org_office_controller():
    """
        Office Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    T = current.T
    s3db = current.s3db
    request = current.request
    s3 = current.response.s3
    settings = current.deployment_settings

    # Get default organisation_id
    req_vars = request.vars
    organisation_id = req_vars["organisation_id"]
    if type(organisation_id) is list:
        req_vars["organisation_id"] = organisation_id[0]
    organisation_id = req_vars["organisation_id"] or \
                      current.session.s3.organisation_id or \
                      ""

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        table = r.table
        if organisation_id:
            table.organisation_id.default = organisation_id

        if r.representation == "plain":
            # Map popups want less clutter
            table.obsolete.readable = False

        if r.interactive:
            if r.component:
                cname = r.component.name
                if cname in ("inv_item", "recv", "send"):
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create=False,
                                   listadd=False,
                                   editable=False,
                                   deletable=False,
                                   )

                elif cname == "human_resource":
                    # Filter to just Staff
                    s3.filter = (s3db.hrm_human_resource.type == 1)
                    # Make it clear that this is for adding new staff, not assigning existing
                    s3.crud_strings.hrm_human_resource.label_create_button = T("Add New Staff Member")
                    # Cascade the organisation_id from the office to the staff
                    htable = s3db.hrm_human_resource
                    htable.organisation_id.default = r.record.organisation_id
                    htable.organisation_id.writable = False
                    htable.organisation_id.comment = None
                    # Filter out people which are already staff for this office
                    s3_filter_staff(r)

                elif cname == "req" and r.method not in ("update", "read"):
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    s3db.req_create_form_mods()
            elif r.id:
                table.obsolete.readable = table.obsolete.writable = True

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component and \
               settings.get_org_summary():
                # Insert fields to view/record the summary data
                table = s3db.org_office_summary
                field1 = table.national_staff
                field2 = table.international_staff
                row = None
                if r.id:
                    query = (table.office_id == r.id)
                    row = current.db(query).select(field1,
                                                   field2,
                                                   limitby=(0, 1)).first()
                if r.method == "read" and \
                   "item" in output:
                    for field in [field1, field2]:
                        if row:
                            widget = row[field]
                        else:
                            widget = current.messages.NONE
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        comment = ""
                        rows = s3.crud.formstyle(row_id, label, widget, comment)
                        try:
                            # Insert Label row
                            output["item"][0].insert(-2, rows[0])
                        except:
                            pass
                        try:
                            # Insert Widget row
                            output["item"][0].insert(-2, rows[1])
                        except:
                            # A non-standard formstyle with just a single row
                            pass

                elif r.method not in ("import", "search") and \
                     "form" in output:

                    sep = ": "
                    for field in [field1, field2]:
                        if row:
                            default = row[field]
                        else:
                            default = field.default
                        widget = field.widget or SQLFORM.widgets.integer.widget(field, default)
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, label and sep, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        comment = field.comment or ""
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        rows = s3.crud.formstyle(row_id, label, widget, comment)
                        try:
                            # Insert Label row
                            output["form"][0].insert(-4, rows[0])
                        except:
                            pass
                        try:
                            # Insert Widget row
                            output["form"][0].insert(-4, rows[1])
                        except:
                            # A non-standard formstyle with just a single row
                            pass
            elif r.component_name == "human_resource":
                # Modify action button to open staff instead of human_resource
                read_url = URL(c="hrm", f="staff", args=["[id]"])
                delete_url = URL(c="hrm", f="staff", args=["[id]", "delete"])
                update_url = URL(c="hrm", f="staff", args=["[id]", "update"])
                S3CRUD.action_buttons(r, read_url=read_url,
                                         delete_url=delete_url,
                                         update_url=update_url)
        return output
    s3.postp = postp

    if "inv_item" in request.args:
        rheader = s3db.inv_warehouse_rheader
    else:
        rheader = s3db.org_rheader
    output = current.rest_controller("org", "office", rheader=rheader)
    return output

# END =========================================================================
