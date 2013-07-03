# -*- coding: utf-8 -*-

""" Sahana Eden Organisation Model

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

__all__ = ["S3OrganisationModel",
           "S3OrganisationGroupModel",
           "S3OrganisationLocationModel",
           "S3OrganisationResourceModel",
           "S3OrganisationSectorModel",
           "S3OrganisationServiceModel",
           "S3OrganisationSummaryModel",
           "S3OrganisationTypeTagModel",
           "S3SiteModel",
           "S3SiteDetailsModel",
           "S3FacilityModel",
           "org_facility_rheader",
           "S3RoomModel",
           "S3OfficeModel",
           "S3OfficeSummaryModel",
           "S3OfficeTypeTagModel",
           "org_organisation_logo",
           "org_organisation_address",
           "org_root_organisation",
           "org_organisation_requires",
           "org_site_represent",
           "org_rheader",
           "org_organisation_controller",
           "org_office_controller",
           "org_update_affiliations",
           "org_OrganisationRepresent"
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
from s3layouts import S3AddResourceLink

# =============================================================================
class S3OrganisationModel(S3Model):
    """
        Organisations
    """

    names = ["org_organisation_type",
             "org_organisation_type_id",
             "org_organisation",
             "org_organisation_id",
             "org_organisation_branch",
             "org_organisation_user",
             "org_organisation_represent",
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
        NONE = messages["NONE"]
        ORGANISATION = messages.ORGANISATION

        use_branches = settings.get_org_branches()

        # ---------------------------------------------------------------------
        # Organisation Types
        #
        tablename = "org_organisation_type"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True,
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

        represent = S3Represent(lookup=tablename, translate=True)
        organisation_type_id = S3ReusableField("organisation_type_id", table,
                                sortby="name",
                                requires=IS_NULL_OR(
                                            IS_ONE_OF(db, "org_organisation_type.id",
                                                      represent,
                                                      sort=True
                                                      )),
                                represent=represent,
                                label=T("Organization Type"),
                                comment=S3AddResourceLink(c="org",
                                    f="organisation_type",
                                    label=T("Add Organization Type"),
                                    title=T("Organization Type"),
                                    tooltip=T("If you don't see the Type in the list, you can add a new one by clicking link 'Add Organization Type'.")),
                                ondelete="SET NULL")

        configure(tablename,
                  # Not needed since unique=True
                  #deduplicate=self.organisation_type_duplicate,
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
                                   represent=self.gis_country_code_represent,
                                   ),
                             # @ToDo: Deprecate with Contact component
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
                                   requires=IS_NULL_OR(
                                                IS_INT_IN_RANGE(1850, 2100)),
                                   represent=lambda v: v or NONE,
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Year"),
                                                                 T("Year that the organization was founded"))),
                                   ),
                             Field("logo", "upload",
                                   label=T("Logo"),
                                   uploadfolder = os.path.join(
                                    current.request.folder, "uploads"),
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
                             #Field("privacy", "integer", default=0),
                             #Field("archived", "boolean", default=False),
                             * s3_meta_fields())

        # CRUD strings
        ADD_ORGANIZATION = T("Add New Organization")
        crud_strings[tablename] = Storage(
            title_create=T("Add Organization"),
            title_display=T("Organization Details"),
            title_list=T("Organizations"),
            title_update=T("Edit Organization"),
            title_search=T("Search Organizations"),
            title_upload=T("Import Organizations"),
            subtitle_create=ADD_ORGANIZATION,
            label_list_button=T("List Organizations"),
            label_create_button=ADD_ORGANIZATION,
            label_delete_button=T("Delete Organization"),
            msg_record_created=T("Organization added"),
            msg_record_modified=T("Organization updated"),
            msg_record_deleted=T("Organization deleted"),
            msg_list_empty=T("No Organizations currently registered"))

        # @ToDo: Deployment_setting
        organisation_dropdown_not_ac = True
        if organisation_dropdown_not_ac:
            help = T("If you don't see the Organization in the list, you can add a new one by clicking link 'Add Organization'.")
            widget = None
        else:
            help = T("Enter some characters to bring up a list of possible matches")
            widget = S3OrganisationAutocompleteWidget()
        #else:
        #    widget = SQLFORM.widgets.options.widget

        organisation_comment = S3AddResourceLink(c="org",
                                                 f="organisation",
                                                 label=ADD_ORGANIZATION,
                                                 title=ORGANISATION,
                                                 tooltip=help)

        org_organisation_represent = org_OrganisationRepresent()

        from_organisation_comment = S3AddResourceLink(c="org",
                                                      f="organisation",
                                                      vars=dict(child="from_organisation_id"),
                                                      label=ADD_ORGANIZATION,
                                                      title=ORGANISATION,
                                                      tooltip=help)

        auth = current.auth
        organisation_id = S3ReusableField("organisation_id", table,
                                          sortby="name",
                                          default = auth.user.organisation_id if auth.is_logged_in() \
                                                                              else None,
                                          requires=org_organisation_requires(),
                                          represent=org_organisation_represent,
                                          label=ORGANISATION,
                                          comment=organisation_comment,
                                          ondelete="RESTRICT",
                                          widget = widget,
                                          )

        utablename = auth.settings.table_user_name
        configure(tablename,
                  super_entity="pr_pentity",
                  deduplicate=self.organisation_duplicate,
                  onaccept=self.org_organisation_onaccept,
                  ondelete=self.org_organisation_ondelete,
                  referenced_by=[(utablename, "organisation_id")],
                  xml_post_parse=self.org_organisation_xml_post_parse,
                  list_orderby=table.name,
                  list_fields=["id",
                               "name",
                               "acronym",
                               "organisation_type_id",
                               "website"
                               ])

        # Custom Method for S3SiteAddressAutocompleteWidget
        self.set_method("org", "organisation",
                        method="search_ac",
                        action=self.org_search_ac)

        # Components

        # Documents
        add_component("doc_document", org_organisation="organisation_id")
        add_component("doc_image", org_organisation="organisation_id")

        # Groups
        add_component("org_group",
                      org_organisation=dict(link="org_group_membership",
                                            joinby="organisation_id",
                                            key="group_id",
                                            actuate="hide"))
        # Format for filter_widget
        add_component("org_group_membership",
                      org_organisation="organisation_id")

        # Sites
        add_component("org_site",
                      org_organisation="organisation_id")

        # Facilities
        add_component("org_facility",
                      org_organisation="organisation_id")

        # Offices
        add_component("org_office",
                      org_organisation="organisation_id")

        # Warehouses
        add_component("inv_warehouse",
                      org_organisation="organisation_id")

        # Staff/Volunteers
        add_component("hrm_human_resource",
                      org_organisation="organisation_id")

        # Members
        add_component("member_membership",
                      org_organisation="organisation_id")

        # Locations served
        add_component("gis_location",
                      org_organisation=dict(link="org_organisation_location",
                                            joinby="organisation_id",
                                            key="location_id",
                                            actuate="hide"))
        # Format for filter_widget
        add_component("org_organisation_location",
                      org_organisation="organisation_id")

        # Catalogs
        add_component("supply_catalog",
                      org_organisation="organisation_id")

        # Resources
        add_component("org_resource",
                      org_organisation="organisation_id")

        # Sectors
        add_component("org_sector",
                      org_organisation=dict(link="org_sector_organisation",
                                            joinby="organisation_id",
                                            key="sector_id",
                                            actuate="hide"))
        # Format for filter_widget
        add_component("org_sector_organisation",
                      org_organisation="organisation_id")

        # Services
        add_component("org_service",
                      org_organisation=dict(link="org_service_organisation",
                                            joinby="organisation_id",
                                            key="service_id",
                                            actuate="hide"))
        # Format for filter_widget
        add_component("org_service_organisation",
                      org_organisation="organisation_id")

        # Assets
        add_component("asset_asset",
                      org_organisation="organisation_id")

        # Projects
        if settings.get_project_multiple_organisations():
            add_component("project_project",
                          org_organisation=dict(link="project_organisation",
                                                joinby="organisation_id",
                                                key="project_id",
                                                # Embed widget doesn't currently support 2 fields of same name (8 hours)
                                                #actuate="embed",
                                                actuate="hide",
                                                autocomplete="name",
                                                autodelete=False))
            # Format for filter_widget
            add_component("project_organisation",
                          org_organisation=dict(joinby="organisation_id",
                                                name="project_organisation"))
            
        else:
            add_component("project_project",
                          org_organisation="organisation_id")

        # Organisation Summary data
        if settings.get_org_summary():
            add_component("org_organisation_summary",
                          org_organisation=dict(name="summary",
                                                joinby="organisation_id"))

        # Requests
        #add_component("req_req",
        #              org_organisation = "donated_by_id")

        # -----------------------------------------------------------------------------
        # Enable this to allow migration of users between instances
        #add_component(db.auth_user,
        #              org_organisation="organisation_id")

        if use_branches:
            # Branches
            add_component("org_organisation",
                          org_organisation=Storage(
                                        name="branch",
                                        link="org_organisation_branch",
                                        joinby="organisation_id",
                                        key="branch_id",
                                        actuate="embed",
                                        autocomplete="name",
                                        autodelete=True))

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

            # ---------------------------------------------------------------------
            # Organisation Branches
            #
            tablename = "org_organisation_branch"
            table = define_table(tablename,
                                 organisation_id(ondelete="CASCADE"),
                                 organisation_id("branch_id",
                                                 label=T("Branch"),
                                                 default=None,
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
                #title_upload=T("Import Branch Organizations"),
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
        utable = auth.settings.table_user
        tablename = "org_organisation_user"
        table = define_table(tablename,
                             Field("user_id", utable),
                             organisation_id(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage(
                    org_organisation_type_id=organisation_type_id,
                    org_organisation_id=organisation_id,
                    org_organisation_represent=org_organisation_represent
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
            If an Org is deleted then remove Logo
        """

        db = current.db
        table = db.org_organisation
        deleted_row = db(table.id == row.id).select(table.logo,
                                                    limitby=(0, 1)
                                                    ).first()
        if deleted_row and deleted_row.logo:
            current.s3db.pr_image_delete_all(deleted_row.logo)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_xml_post_parse(element, record):
        """
            Check for defaults provided by project/organisation.xsl
        """

        org_type_default = element.xpath('data[@field="_organisation_type_id"]')
        if org_type_default:
            org_type_default = org_type_default[0].text            
            db = current.db
            table = db.org_organisation_type
            cache = current.s3db.cache
            row = None
            # These default mappings can be overridden per-deployment
            if org_type_default == "Donor":
                row = db(table.name == "Bilateral").select(table.id,
                                                           cache=cache,
                                                           limitby=(0, 1)).first()
            elif org_type_default == "Partner":
                row = db(table.name == "NGO").select(table.id,
                                                     cache=cache,
                                                     limitby=(0, 1)).first()
            elif org_type_default in ("Host National Society",
                                      "Partner National Society"):
                row = db(table.name == "Red Cross / Red Crescent").select(table.id,
                                                                          cache=cache,
                                                                          limitby=(0, 1)
                                                                          ).first()
            if row:
                # Note this sets only the default, so won't override existing or explicit values
                record._organisation_type_id = row.id
        return

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
    def org_search_ac(r, **attr):
        """
            JSON search method for S3OrganisationAutocompleteWidget
            - searches name & acronym for both this organisation & the parent
              of branches
            @param r: the S3Request
            @param attr: request attributes
        """

        response = current.response
        resource = r.resource
        table = resource.table
        settings = current.deployment_settings

        use_branches = settings.get_org_branches()

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = current.request.get_vars

        # JQueryUI Autocomplete uses "term"
        # old JQuery Autocomplete uses "q"
        # what uses "value"?
        value = _vars.term or _vars.value or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower().strip()

        filter = _vars.filter

        if filter and value:

            if filter == "~":
                query = (S3FieldSelector("organisation.name").lower().like(value + "%")) | \
                        (S3FieldSelector("organisation.acronym").lower().like(value + "%"))
                if use_branches:
                    query |= (S3FieldSelector("parent.name").lower().like(value + "%")) | \
                             (S3FieldSelector("parent.acronym").lower().like(value + "%"))

            else:
                output = current.xml.json_message(False, 400,
                                "Unsupported filter! Supported filters: ~")
                raise HTTP(400, body=output)

        resource.add_filter(query)

        MAX_SEARCH_RESULTS = settings.get_search_max_results()
        limit = int(_vars.limit or MAX_SEARCH_RESULTS)
        if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
            output = jsons([dict(id="",
                                 name="Search results are over %d. Please input more characters." \
                                 % MAX_SEARCH_RESULTS)])
        else:
            field = table.name
            field2 = table.acronym

            # Fields to return
            fields = [table.id, field, field2]
            if use_branches:
                btable = current.s3db.org_organisation_branch
                field3 = btable.organisation_id
                fields.append(field3)
                db = current.db

            attributes = dict(orderby=field)
            limitby = resource.limitby(start=0, limit=limit)
            if limitby is not None:
                attributes["limitby"] = limitby
            rows = resource._load(*fields, **attributes)
            output = []
            append = output.append
            for row in rows:
                if use_branches:
                    _row = row[table]
                else:
                    _row = row
                name = _row.name
                parent = None
                if "org_organisation_branch" in row:
                    query = (table.id == row[btable].organisation_id)
                    parent = db(query).select(table.name,
                                              limitby = (0, 1)).first()
                    if parent:
                        name = "%s > %s" % (parent.name, name)
                if not parent:
                    acronym = _row.acronym
                    if acronym:
                        name = "%s (%s)" % (name, acronym)
                record = dict(
                    id = _row.id,
                    name = name,
                    )
                append(record)
            output = jsons(output)

        response.headers["Content-Type"] = "application/json"
        return output

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
            error = current.T("Cannot make an Organization a branch of itself!")
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
        s3db = current.s3db

        # Fields a branch organisation inherits from its parent organisation
        inherit = ["organisation_type_id",
                   # @ToDo: Update for Component
                   #"sector",
                   "region",
                   "country",
                   ]

        otable = s3db.org_organisation
        ltable = db.org_organisation_branch
        btable = db.org_organisation.with_alias("org_branch_organisation")

        ifields = [otable[fn] for fn in inherit]  + \
                  [btable[fn] for fn in inherit]

        left = [otable.on(ltable.organisation_id == otable.id),
                btable.on(ltable.branch_id == btable.id)]
        
        record = db(ltable.id == id).select(
                    ltable.branch_id,
                    ltable.organisation_id,
                    ltable.deleted,
                    ltable.deleted_fk,
                    *ifields,
                    left=left,
                    limitby=(0, 1)).first()

        if record:
            try:
                organisation = record["org_organisation"]
                branch = record["org_branch_organisation"]
                link = record["org_organisation_branch"]

                branch_id = link.branch_id
                organisation_id = link.organisation_id
                if branch_id and organisation_id and not link.deleted:

                    # Inherit fields from parent organisation
                    update = dict([(field, organisation[field])
                                for field in inherit
                                if not branch[field] and organisation[field]])
                    if update:
                        db(otable.id == branch_id).update(**update)

                    # Eliminate duplicate affiliations
                    query = (ltable.branch_id == branch_id) & \
                            (ltable.organisation_id == organisation_id) & \
                            (ltable.id != id) & \
                            (ltable.deleted != True)

                    deleted_fk = {"branch_id": branch_id,
                                "organisation_id": organisation_id}
                    db(query).update(deleted=True,
                                    branch_id=None,
                                    organisation_id=None,
                                    deleted_fk=json.dumps(deleted_fk))

                org_update_affiliations("org_organisation_branch", link)
            except:
                pass
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
            org_update_affiliations("org_organisation_branch", record)
        return

# =============================================================================
class S3OrganisationGroupModel(S3Model):
    """
        Organisation Group Model
        - 'Coalitions' or 'Networks'
    """

    names = ["org_group",
             "org_group_membership",
             "org_group_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Organization Groups
        #
        tablename = "org_group"
        table = define_table(tablename,
                             self.super_link("pe_id", "pr_pentity"),
                             Field("name", notnull=True, unique=True,
                                   length=128,
                                   label=T("Name")),
                             #self.gis_location_id(),
                             s3_comments(),
                             *s3_meta_fields()
                             )

        # CRUD Strings not defined to allow each template to define as-required

        configure(tablename,
                  super_entity="pr_pentity",
                  )

        represent = S3Represent(lookup=tablename)
        group_id = S3ReusableField("group_id", table,
                                   sortby="name",
                                   requires=IS_NULL_OR(
                                                IS_ONE_OF(db, "org_group.id",
                                                          represent,
                                                          sort=True,
                                                          )),
                                   represent=represent,
                                   # Always links via Link Tables
                                   ondelete="CASCADE",
                                   )

        # ---------------------------------------------------------------------
        # Group membership
        #
        tablename = "org_group_membership"
        define_table(tablename,
                     group_id(),
                     self.org_organisation_id(),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.group_membership_onaccept,
                  ondelete = self.group_membership_onaccept,
                  )

        # Pass names back to global scope (s3.*)
        return dict(
                org_group_id = group_id,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def group_membership_onaccept(form):
        """
            Remove any duplicate memberships and update affiliations
        """

        if hasattr(form, "vars"):
            _id = form.vars.id
        elif isinstance(form, Row) and "id" in form:
            _id = form.id
        else:
            return

        db = current.db
        mtable = db.org_group_membership

        if _id:
            record = db(mtable.id == _id).select(limitby=(0, 1)).first()
        else:
            return
        if record:
            organisation_id = record.organisation_id
            group_id = record.group_id
            if organisation_id and group_id and not record.deleted:
                query = (mtable.organisation_id == organisation_id) & \
                        (mtable.group_id == group_id) & \
                        (mtable.id != record.id) & \
                        (mtable.deleted != True)
                deleted_fk = {"organisation_id": organisation_id,
                              "group_id": group_id}
                db(query).update(deleted = True,
                                 organisation_id = None,
                                 group_id = None,
                                 deleted_fk = json.dumps(deleted_fk))
            org_update_affiliations("org_group_membership", record)
        return

# =============================================================================
class S3OrganisationLocationModel(S3Model):
    """
        Organisation Location Model
    """

    names = ["org_organisation_location"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Organizations <> Locations Link Table
        #
        tablename = "org_organisation_location"
        self.define_table(tablename,
                          self.org_organisation_id(),
                          self.gis_location_id(
                            requires = IS_LOCATION(),
                            #represent = self.gis_LocationRepresent(sep=", "),
                            widget = S3LocationAutocompleteWidget()
                          ),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("New Location"),
            title_display = T("Location"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_search = T("Search Locations"),
            title_upload = T("Import Location data"),
            subtitle_create = T("Add New Location"),
            label_list_button = T("List Locations"),
            label_create_button = T("Add Location to Organization"),
            msg_record_created = T("Location added to Organization"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location removed from Organization"),
            msg_list_empty = T("No Locations found for this Organization"))

        self.configure(tablename,
                       deduplicate=self.org_organisation_location_deduplicate,
                       )

        # Pass names back to global scope (s3.*)
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_location_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "org_organisation_location":
            return

        data = item.data
        if "organisation_id" in data and \
           "location_id" in data:
            organisation_id = data.organisation_id
            location_id = data.location_id
            table = item.table
            query = (table.organisation_id == organisation_id) & \
                    (table.location_id == location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

        return

# =============================================================================
class S3OrganisationResourceModel(S3Model):
    """
        Organisation Resource Model
        - depends on Stats module
    """

    names = ["org_resource",
             "org_resource_type",
             ]

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            # Organisation Resource Model needs Stats module enabling
            return dict()

        T = current.T
        db = current.db
        auth = current.auth
        settings = current.deployment_settings
        crud_strings = current.response.s3.crud_strings
        super_link = self.super_link
        configure = self.configure

        # ---------------------------------------------------------------------
        # Resource Type data
        #
        tablename = "org_resource_type"
        table = self.define_table(tablename,
                                  super_link("parameter_id", "stats_parameter"),
                                  Field("name",
                                        label=T("Resource Type")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_RESOURCE_TYPE = T("Add New Resource Type")
        crud_strings[tablename] = Storage(
            title_create=T("Add Resource Type"),
            title_display=T("Resource Type Details"),
            title_list=T("Resource Types"),
            title_update=T("Edit Resource Type"),
            title_search=T("Search Resource  Types"),
            title_upload=T("Import Resource Types"),
            subtitle_create=ADD_RESOURCE_TYPE,
            label_list_button=T("Resource Types"),
            label_create_button=ADD_RESOURCE_TYPE,
            label_delete_button=T("Delete Resource Type"),
            msg_record_created=T("Resource Type added"),
            msg_record_modified=T("Resource Type updated"),
            msg_record_deleted=T("Resource Type deleted"),
            msg_list_empty=T("No Resource Types defined"))

        # Resource Configuration
        configure(tablename,
                  super_entity = "stats_parameter",
                  )

        # ---------------------------------------------------------------------
        # Resource data
        #
        tablename = "org_resource"
        table = self.define_table(tablename,
                                  self.org_organisation_id(ondelete="CASCADE"),
                                  # Add this when deprecating S3OfficeSummaryModel
                                  # self.super_link("site_id", "org_site",
                                                  # label=settings.get_org_site_label(),
                                                  # instance_types = auth.org_site_types,
                                                  # orderby = "org_site.name",
                                                  # realms = auth.permission.permitted_realms(tablename,  
                                                                                            # method="create"),
                                                  # not_filterby = "obsolete",
                                                  # not_filter_opts = [True],
                                                  # readable = True,
                                                  # writable = True,
                                                  # represent = self.org_site_represent,
                                                  # ),
                                  self.gis_location_id(),
                                  # Instance
                                  super_link("data_id", "stats_data"),
                                  # This is a component, so needs to be a super_link
                                  # - can't override field name, ondelete or requires
                                  super_link("parameter_id", "stats_parameter",
                                             label = T("Resource Type"),
                                             instance_types = ["org_resource_type"],
                                             represent = S3Represent(lookup="stats_parameter"),
                                             readable = True,
                                             writable = True,
                                             empty = True,
                                             comment = S3AddResourceLink(c="org",
                                                                         f="resource_type",
                                                                         vars = dict(child = "parameter_id"),
                                                                         title=ADD_RESOURCE_TYPE),
                                             ),
                                  Field("value", "integer", 
                                        requires=IS_NULL_OR(
                                                    IS_INT_IN_RANGE(0, 999999)
                                                    ),
                                        label=T("Quantity")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            title_create=T("Add Resource"),
            title_display=T("Resource Details"),
            title_list=T("Resource Inventory"),
            title_update=T("Edit Resource"),
            title_map=T("Map of Resources"),
            title_search=T("Search Resource Inventory"),
            title_upload=T("Import Resources"),
            subtitle_create=T("Add New Resource"),
            label_list_button=T("Resource Inventory"),
            label_create_button=T("Add New Resource"),
            label_delete_button=T("Delete Resource"),
            msg_record_created=T("Resource added"),
            msg_record_modified=T("Resource updated"),
            msg_record_deleted=T("Resource deleted"),
            msg_list_empty=T("No Resources in Inventory"))

        configure(tablename,
                  super_entity = "stats_data",
                  context = {"location": "location_id",
                             "organisation": "organisation_id",
                             },
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage(
                )

# =============================================================================
class S3OrganisationSectorModel(S3Model):
    """
        Organisation Sector Model
    """

    names = ["org_sector",
             "org_sector_id",
             "org_sector_opts",
             #"org_subsector",
             "org_sector_organisation",
             ]

    def model(self):

        T = current.T
        db = current.db

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

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
        if current.deployment_settings.get_ui_label_cluster():
            SECTOR = T("Cluster")
            ADD_SECTOR = T("Add New Cluster")
            help = T("If you don't see the Cluster in the list, you can add a new one by clicking link 'Add New Cluster'.")
            crud_strings[tablename] = Storage(
                title_create=T("Add Cluster"),
                title_display=T("Cluster Details"),
                title_list=T("Clusters"),
                title_update=T("Edit Cluster"),
                title_search=T("Search Clusters"),
                subtitle_create=ADD_SECTOR,
                label_list_button=T("List Clusters"),
                label_create_button=ADD_SECTOR,
                label_delete_button=T("Delete Cluster"),
                msg_record_created=T("Cluster added"),
                msg_record_modified=T("Cluster updated"),
                msg_record_deleted=T("Cluster deleted"),
                msg_list_empty=T("No Clusters currently registered"))
        else:
            SECTOR = T("Sector")
            ADD_SECTOR = T("Add New Sector")
            help = T("If you don't see the Sector in the list, you can add a new one by clicking link 'Add New Sector'.")
            crud_strings[tablename] = Storage(
                title_create=T("Add Sector"),
                title_display=T("Sector Details"),
                title_list=T("Sectors"),
                title_update=T("Edit Sector"),
                title_search=T("Search Sectors"),
                subtitle_create=ADD_SECTOR,
                label_list_button=T("List Sectors"),
                label_create_button=ADD_SECTOR,
                label_delete_button=T("Delete Sector"),
                msg_record_created=T("Sector added"),
                msg_record_modified=T("Sector updated"),
                msg_record_deleted=T("Sector deleted"),
                msg_list_empty=T("No Sectors currently registered"))

        configure("org_sector",
                  deduplicate=self.org_sector_duplicate)

        sector_comment = lambda child: S3AddResourceLink(c="org", f="sector",
                                                         vars={"child": child},
                                                         label=ADD_SECTOR,
                                                         title=SECTOR,
                                                         tooltip=help)

        represent = S3Represent(lookup=tablename, translate=True)
        sector_id = S3ReusableField("sector_id", "reference org_sector",
                                    sortby="abrv",
                                    requires=IS_NULL_OR(
                                                IS_ONE_OF(db, "org_sector.id",
                                                          represent,
                                                          sort=True,
                                                          filterby=filterby,
                                                          filter_opts=filter_opts,
                                                          )),
                                    represent=represent,
                                    comment=sector_comment("sector_id"),
                                    label=SECTOR,
                                    ondelete="SET NULL")

        # Components
        add_component("org_organisation",
                      org_sector=Storage(
                                link="org_sector_organisation",
                                joinby="sector_id",
                                key="organisation_id",
                                actuate="hide"))
        add_component("project_project",
                      org_sector=Storage(
                                link="project_sector_project",
                                joinby="sector_id",
                                key="project_id",
                                actuate="hide"))
        #add_component("project_activity_type",
        #              org_sector=Storage(
        #                        link="project_activity_type_sector",
        #                        joinby="sector_id",
        #                        key="activity_type_id",
        #                        actuate="hide"))
        #add_component("project_theme",
        #              org_sector=Storage(
        #                        link="project_theme_sector",
        #                        joinby="sector_id",
        #                        key="theme_id",
        #                        actuate="hide"))

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
        # if settings.get_ui_label_cluster():
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
        # Organizations <> Sectors Link Table
        #
        tablename = "org_sector_organisation"
        define_table(tablename,
                     sector_id(),
                     self.org_organisation_id(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Sector"),
            title_display = T("Sector"),
            title_list = T("Sectors"),
            title_update = T("Edit Sector"),
            title_search = T("Search Sectors"),
            title_upload = T("Import Sector data"),
            subtitle_create = T("Add New Sector"),
            label_list_button = T("List Sectors"),
            label_create_button = T("Add Sector to Organization"),
            msg_record_created = T("Sector added to Organization"),
            msg_record_modified = T("Sector updated"),
            msg_record_deleted = T("Sector removed from Organization"),
            msg_list_empty = T("No Sectors found for this Organization"))

        configure(tablename,
                  deduplicate=self.org_sector_organisation_deduplicate,
                  )

        # Pass names back to global scope (s3.*)
        return dict(
                org_sector_id=sector_id,
                org_sector_opts=self.org_sector_opts,
            )

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
        od[None] = current.messages["NONE"]
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
            return current.messages["NONE"]

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
    def org_sector_organisation_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "org_sector_organisation":
            return

        data = item.data
        if "organisation_id" in data and \
           "sector_id" in data:
            organisation_id = data.organisation_id
            sector_id = data.sector_id
            table = item.table
            query = (table.organisation_id == organisation_id) & \
                    (table.sector_id == sector_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

        return

# =============================================================================
class S3OrganisationServiceModel(S3Model):
    """
        Organisation Service Model
    """

    names = ["org_service",
             "org_service_organisation",
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Service
        #
        tablename = "org_service"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True,
                                   label=T("Name"),
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_SERVICE = T("Add Service")
        crud_strings[tablename] = Storage(
            title_create = ADD_SERVICE,
            title_display = T("Service Details"),
            title_list = T("Services"),
            title_update = T("Edit Service"),
            title_upload = T("Import Services"),
            subtitle_create = T("Add New Service"),
            label_list_button = T("List Services"),
            label_create_button = ADD_SERVICE,
            label_delete_button = T("Delete Service"),
            msg_record_created = T("Service added"),
            msg_record_modified = T("Service updated"),
            msg_record_deleted = T("Service deleted"),
            msg_list_empty = T("No Services currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        service_id = S3ReusableField("service_id", table,
                                    sortby = "name",
                                    label = T("Services"),
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "org_service.id",
                                                          represent,
                                                          sort=True)),
                                    represent = represent,
                                    ondelete = "CASCADE",
                                    )

        # Field settings for org_organisation.service field in friendly_string_from_field_query function
        # - breaks Action Buttons, so moved to inside the fn which calls them
        #table.id.represent = represent
        #table.id.label = T("Service")

        # ---------------------------------------------------------------------
        # Organizations <> Services Link Table
        #
        tablename = "org_service_organisation"
        define_table(tablename,
                     service_id(),
                     self.org_organisation_id(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Service"),
            title_display = T("Service"),
            title_list = T("Services"),
            title_update = T("Edit Service"),
            title_search = T("Search Services"),
            title_upload = T("Import Service data"),
            subtitle_create = T("Add New Service"),
            label_list_button = T("List Services"),
            label_create_button = T("Add Service to Organization"),
            msg_record_created = T("Service added to Organization"),
            msg_record_modified = T("Service updated"),
            msg_record_deleted = T("Service removed from Organization"),
            msg_list_empty = T("No Services found for this Organization"))

        self.configure(tablename,
                       deduplicate=self.org_service_organisation_deduplicate,
                       )

        # Pass names back to global scope (s3.*)
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_service_organisation_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "org_service_organisation":
            return

        data = item.data
        if "organisation_id" in data and \
           "service_id" in data:
            organisation_id = data.organisation_id
            service_id = data.service_id
            table = item.table
            query = (table.organisation_id == organisation_id) & \
                    (table.service_id == service_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

        return

# =============================================================================
class S3OrganisationSummaryModel(S3Model):
    """
        Organisation Summary fields visible when settings.org.summary = True

        @ToDo: Deprecate in favour of S3OrganisationResourceModel
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
        # Pass names back to global scope (s3.*)
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
        # Pass names back to global scope (s3.*)
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
                                  Field("name", notnull=True,
                                        length=64, # Mayon compatibility
                                        #unique=True,
                                        label=T("Name")),
                                  self.gis_location_id(),
                                  self.org_organisation_id(),
                                  Field("obsolete", "boolean",
                                        label=T("Obsolete"),
                                        represent=lambda bool: \
                                          (bool and [T("Obsolete")] or
                                           [current.messages["NONE"]])[0],
                                        default=False,
                                        readable=False,
                                        writable=False),
                                  *s3_ownerstamp())

        # ---------------------------------------------------------------------
        settings = current.deployment_settings
        org_site_label = settings.get_org_site_label()
        if settings.get_org_site_autocomplete():
            widget=S3SiteAutocompleteWidget(),
            comment=DIV(_class="tooltip",
                        _title="%s|%s" % (org_site_label,
                                          T("Enter some characters to bring up a list of possible matches")))
        else:
            widget = None
            comment = None
        site_id = self.super_link("site_id", "org_site",
                                  #writable = True,
                                  #readable = True,
                                  label=org_site_label,
                                  default=auth.user.site_id if auth.is_logged_in() else None,
                                  represent=org_site_represent,
                                  orderby="org_site.name",
                                  widget=widget,
                                  comment=comment
                                  )

        # Custom Method for S3SiteAddressAutocompleteWidget
        self.set_method("org", "site",
                        method="search_address_ac",
                        action=self.site_search_address_ac)

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
        add_component("req_site_needs",
                      org_site=dict(joinby="site_id",
                                    multiple=False))

        # Details
        add_component("org_site_details",
                      org_site=dict(joinby="site_id",
                                    multiple=False))
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
        # Pass names back to global scope (s3.*)
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
                temp_code = S3SiteModel.returnUniqueCode(code, wildcard_posn,
                                                         code_list)
        if temp_code:
            db(site_table.site_id == form.vars.site_id).update(code=temp_code)

    # -------------------------------------------------------------------------
    @staticmethod
    def getCodeList(code, wildcard_posn=[]):
        """
            Called by org_site_onaccept
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
        # Extract the rows in the database to provide a list of used codes
        codeList = []
        for record in rows:
            codeList.append(record.code)
        return codeList

    # -------------------------------------------------------------------------
    @staticmethod
    def returnUniqueCode(code, wildcard_posn=[], code_list=[]):
        """
            Called by org_site_onaccept
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
            # Set up the next rep_posn
            p = 0
            while (p < len(wildcard_posn)):
                if rep_posn[p] == 35: # the maximum number of replacement characters
                    rep_posn[p] = 0
                    p += 1
                else:
                    rep_posn[p] = rep_posn[p] + 1
                    break
            # If no new permutation of replacement characters has been found
            if p == len(wildcard_posn):
                return None

    # -------------------------------------------------------------------------
    @staticmethod
    def site_search_address_ac(r, **attr):
        """
            JSON search method for S3SiteAddressAutocompleteWidget

            @param r: the S3Request
            @param attr: request attributes
        """

        response = current.response
        resource = r.resource
        table = resource.table

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = current.request.get_vars

        # JQueryUI Autocomplete uses "term"
        # old JQuery Autocomplete uses "q"
        # what uses "value"?
        value = _vars.term or _vars.value or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower().strip()

        filter = _vars.filter

        if filter and value:

            if filter == "~":
                query = (S3FieldSelector("name").lower().like(value + "%")) | \
                        (S3FieldSelector("location_id$address").lower().like(value + "%"))

            else:
                output = current.xml.json_message(False, 400,
                                "Unsupported filter! Supported filters: ~")
                raise HTTP(400, body=output)

        resource.add_filter(query)

        MAX_SEARCH_RESULTS = current.deployment_settings.get_search_max_results()
        limit = int(_vars.limit or MAX_SEARCH_RESULTS)
        if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
            output = jsons([dict(id="",
                                 name="Search results are over %d. Please input more characters." \
                                 % MAX_SEARCH_RESULTS)])
        else:
            s3db = current.s3db
            field = table.name
            field2 = s3db.gis_location.address

            # Fields to return
            fields = [table.id, field, field2]

            attributes = dict(orderby=field)
            limitby = resource.limitby(start=0, limit=limit)
            if limitby is not None:
                attributes["limitby"] = limitby
            rows = resource._load(*fields, **attributes)
            output = []
            append = output.append
            represent = s3db.org_site_represent
            for row in rows:
                name = represent(row[table].name)
                address = row.gis_location.address
                if address:
                        name = "%s, %s" % (name, address)
                record = dict(
                    id = row[table].id,
                    name = name,
                    )
                append(record)
            output = jsons(output)

        response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class S3SiteDetailsModel(S3Model):
    """ Extra optional details for Sites """

    names = ["org_site_details",
             ]

    def model(self):

        T = current.T
        settings = current.deployment_settings

        last_contacted = settings.get_org_site_last_contacted()

        # ---------------------------------------------------------------------
        # Details
        tablename = "org_site_details"
        table = self.define_table(tablename,
                                  # Component not instance
                                  self.super_link("site_id", "org_site"),
                                  s3_date("last_contacted",
                                          readable = last_contacted,
                                          writable = last_contacted,
                                          label = T("Last Contacted")),
                                  *s3_meta_fields())

        # CRUD Strings
        site_label = settings.get_org_site_label()
        ADD_DETAILS = T("Add %(site_label)s Details") % site_label
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_DETAILS,
            title_display = T("%(site_label)s Details") % site_label,
            title_list = T("%(site_label)s Details") % site_label,
            title_update = T("Edit %(site_label)s Details") % site_label,
            title_search = T("Search %(site_label)s Details") % site_label,
            subtitle_create = T("Add New %(site_label)s Details") % site_label,
            label_list_button = T("List %(site_label)s Details") % site_label,
            label_create_button = ADD_DETAILS,
            msg_record_created = T("%(site_label)s Details added") % site_label,
            msg_record_modified = T("%(site_label)s Details updated") % site_label,
            msg_record_deleted = T("%(site_label)s Details deleted") % site_label,
            msg_list_empty = T("There are no details for this %(site_label)s yet. Add %(site_label)s Details.") % site_label
            )

        # Resource configuration
        #self.configure(tablename,
        #               )

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
        #
        return Storage()

# =============================================================================
class S3FacilityModel(S3Model):
    """
        Generic Site
    """

    names = ["org_facility_type",
             "org_facility",
             "org_facility_geojson",
             ]

    def model(self):

        T = current.T
        db = current.db

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        NONE = current.messages["NONE"]

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
                             super_link("doc_id", "doc_entity"),
                             super_link("pe_id", "pr_pentity"),
                             super_link("site_id", "org_site"),
                             Field("name", notnull=True,
                                   length=64, # Mayon Compatibility
                                   label=T("Name")),
                             Field("code", length=10, # Mayon compatibility
                                   # Deployments that don't wants office codes can hide them
                                   #readable=False, writable=False,
                                   # @ToDo: Deployment Setting to add validator to make these unique
                                   #notnull=True, unique=True,
                                   represent = lambda v: v or NONE,
                                   label=T("Code")),
                             Field("facility_type_id", "list:reference org_facility_type",
                                   requires=IS_NULL_OR(
                                                IS_ONE_OF(db, "org_facility_type.id",
                                                          self.org_facility_type_represent,
                                                          sort=True,
                                                          multiple=True)),
                                   represent=self.org_facility_type_multirepresent,
                                   widget = CheckboxesWidgetS3.widget,
                                   comment=S3AddResourceLink(c="org",
                                                             f="facility_type",
                                                             label=ADD_FAC,
                                                             tooltip=T("Select a Facility Type from the list or click 'Add Facility Type'")),
                                   label=T("Type")),
                             self.org_organisation_id(
                                #widget=S3OrganisationAutocompleteWidget(
                                            #default_from_profile=True)
                                ),
                             self.gis_location_id(),
                             Field("opening_times",
                                   represent = lambda v: v or NONE,
                                   label=T("Opening Times")),
                             Field("contact",
                                   represent = lambda v: v or NONE,
                                   label=T("Contact")),
                             Field("phone1",
                                   label=T("Phone 1"),
                                   represent = lambda v: v or NONE,
                                   requires=IS_NULL_OR(s3_phone_requires)),
                             Field("phone2",
                                   label=T("Phone 2"),
                                   represent = lambda v: v or NONE,
                                   requires=IS_NULL_OR(s3_phone_requires)),
                             Field("email",
                                   label=T("Email"),
                                   represent = lambda v: v or NONE,
                                   requires=IS_NULL_OR(IS_EMAIL())),
                             Field("website",
                                   represent = lambda v: v or NONE,
                                   label=T("Website")),
                             Field("obsolete", "boolean",
                                   label=T("Obsolete"),
                                   represent=lambda bool: \
                                     (bool and [T("Obsolete")] or [current.messages["NONE"]])[0],
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
            title_map=T("Map of Facilities"),
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

        # Search method
        def facility_type_opts():
            table = self.org_facility_type
            rows = db(table.deleted == False).select(table.id, table.name)
            opts = {}
            for row in rows:
                name = row.name
                id = row.id
                opts[id] = name
            return opts

        org_facility_search = [
            S3SearchSimpleWidget(
                name="facility_search_advanced",
                label=T("Name, Address, Organization and/or Code"),
                comment=T("To search for a facility, enter the name, address or code of the facility, or the organisation name or acronym, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all facilities."),
                field=["name",
                       "code",
                       "location_id$address",
                       "organisation_id$name",
                       "organisation_id$acronym"
                       ]
            ),
            S3SearchOptionsWidget(
                name="facility_search_type",
                label=T("Type"),
                field="facility_type_id",
                options = facility_type_opts,
                cols=2,
            ),
            S3SearchOptionsWidget(
                name="facility_search_org",
                label=T("Organization"),
                field="organisation_id",
                cols=3,
            ),
            #S3SearchOptionsWidget(
            #  name="facility_search_L1",
            #  field="location_id$L1",
            #  location_level="L1",
            #  cols = 3,
            #),
            #S3SearchOptionsWidget(
            #  name="facility_search_L2",
            #  field="location_id$L2",
            #  location_level="L2",
            #  cols = 3,
            #),
            S3SearchOptionsWidget(
                name="facility_search_L3",
                field="location_id$L3",
                location_level="L3",
                cols = 3,
            ),
            S3SearchOptionsWidget(
                name="facility_search_L4",
                field="location_id$L4",
                location_level="L4",
                cols = 3,
            ),
            ]

        report_fields = ["name",
                         "facility_type_id",
                         "organisation_id",
                         #"location_id$L1",
                         #"location_id$L2",
                         "location_id$L3",
                         "location_id$L4",
                         ]
        settings = current.deployment_settings
        if settings.has_module("req"):
            # "reqs" virtual field: the highest priority of
            # all open requests for this site:
            table.reqs = Field.Lazy(
                            lambda row: \
                            org_site_top_req_priority(row,
                                                      tablename=tablename))
            widget = S3SearchOptionsWidget(
                        name="facility_search_reqs",
                        field="reqs",
                        label = T("Highest Priority Open Requests"),
                        options = self.req_priority_opts,
                        cols = 3,
                      )
            org_facility_search.append(widget)
            # @ToDo: Report should show Closed Requests?
            #report_fields.append((T("High Priority Open Requests"), "reqs"))

        # Custom Form
        crud_form = S3SQLCustomForm("name",
                                    "code",
                                    "facility_type_id",
                                    "organisation_id",
                                    "location_id",
                                    "opening_times",
                                    "contact",
                                    "phone1",
                                    "phone2",
                                    "email",
                                    "website",
                                    "site_details.last_contacted",
                                    "obsolete",
                                    "comments",
                                    )

        filter_widgets = [
            S3TextFilter(["name",
                          "code",
                          "comments",
                          "organisation_id$name",
                          "organisation_id$acronym",
                          "location_id$name",
                          "location_id$L1",
                          "location_id$L2",
                          ],
                         label=T("Name"),
                         _class="filter-search",
                         ),
            S3OptionsFilter("facility_type_id",
                            label=T("Type"),
                            represent="%(name)s",
                            widget="multiselect",
                            ),
            S3OptionsFilter("organisation_id",
                            label=T("Organization"),
                            represent="%(name)s",
                            widget="multiselect",
                            ),
            ]

        configure(tablename,
                  super_entity=("org_site", "doc_entity", "pr_pentity"),
                  context = {"org_group": "organisation_id$group_membership.group_id",
                             },
                  crud_form = crud_form,
                  deduplicate = self.org_facility_duplicate,
                  onaccept = self.org_facility_onaccept,
                  filter_widgets = filter_widgets,
                  search_method=S3Search(simple=(),
                                         advanced=org_facility_search),
                  report_options = Storage(
                    search=org_facility_search,
                    rows=report_fields,
                    cols=report_fields,
                    #facts=report_fields,
                    #methods=["count", "list", "sum"],
                    fact = [("id", "count", T("Number of Facilities")),
                            ("name", "list", T("List of Facilities"))],
                    defaults=Storage(rows="location_id$L4",
                                     cols="facility_type_id",
                                     fact="name",
                                     aggregate="count")
                    ),
                  realm_components = ["contact_emergency",
                                      "physical_description",
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
                  update_realm = True,
                  )

        # Groups
        add_component("org_group",
                      org_facility=Storage(link="org_facility_group",
                                           joinby="facility_id",
                                           key="group_id",
                                           actuate="hide"))
        # Format for filter_widgets
        add_component("org_facility_group",
                      org_facility="facility_id")

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage(
                    org_facility_geojson = self.org_facility_geojson
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_facility_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        org_update_affiliations("org_facility", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_facility_duplicate(item):
        """ Import item de-duplication """

        if item.tablename == "org_facility":
            table = item.table
            data = item.data
            name = data.get("name", None)
            org = data.get("organisation_id", None)
            address = data.get("address", None)

            query = (table.name.lower() == name.lower())
            if org:
                query = query & (table.organisation_id == org)
            if address:
                query = query & (table.address == address)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

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
            return current.messages["NONE"]

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

        if not opt:
            return current.messages["NONE"]

        opts = opt if type(opt) is list else [opt]

        table = current.s3db.org_facility_type
        query = table.id.belongs(opts)
        rows = current.db(query).select(table.id,
                                        table.name,
                                        cacheable=True,
                                        limitby=(0, len(opts)))
        vals = dict([(r.id, r.name) for r in rows])

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        names = [vals[k] if k in vals else UNKNOWN_OPT for k in opts]
        return ", ".join(names)

    # -----------------------------------------------------------------------------
    @staticmethod
    def org_facility_geojson(jsonp=True,
                             decimals=4):
        """
            Produce a static GeoJSON[P] feed of Facility data
            Designed to be run on a schedule to serve a high-volume website
        """

        from shapely.geometry import Point
        from ..geojson import dumps

        db = current.db
        s3db = current.s3db
        stable = s3db.org_facility
        gtable = db.gis_location
        ntable = s3db.req_site_needs

        # Limit the number of decimal places
        formatter = ".%sf" % decimals

        # All Facilities
        query = (stable.deleted != True) & \
                (stable.obsolete != True) & \
                (gtable.id == stable.location_id)
        lquery = (ntable.deleted != True) & \
                 (ntable.site_id == stable.site_id)
        left = ntable.on(lquery)
        facs = db(query).select(stable.id,
                                stable.name,
                                stable.facility_type_id,
                                stable.comments,
                                stable.opening_times,
                                stable.phone1,
                                stable.phone2,
                                stable.email,
                                stable.website,
                                ntable.needs,
                                gtable.addr_street,
                                gtable.L1,
                                gtable.L4,
                                gtable.lat,
                                gtable.lon,
                                left=left,
                                )
        features = []
        append = features.append
        represent = stable.facility_type_id.represent
        for f in facs:
            g = f.gis_location
            x = g.lon
            y = g.lat
            if x is None or y is None:
                continue
            x = float(format(x, formatter))
            y = float(format(y, formatter))
            shape = Point(x, y)
            # Compact Encoding
            geojson = dumps(shape, separators=(",", ":"))
            o = f.org_facility
            properties = {
                    "id": o.id,
                    "name": o.name,
                    }
            if o.facility_type_id:
                properties["type"] = represent(o.facility_type_id)
            if o.opening_times:
                properties["open"] = o.opening_times
            if o.comments:
                properties["comments"] = o.comments
            if g.addr_street:
                properties["addr"] = g.addr_street
            if g.L1:
                # Encode smaller if-possible
                L1 = g.L1
                if L1 == "New York":
                    properties["L1"] = "NY"
                elif L1 == "New Jersey":
                    properties["L1"] = "NJ"
                else:
                    properties["L1"] = L1
            if g.L4:
                properties["L4"] = g.L4
            if o.phone1:
                properties["ph1"] = o.phone1
            if o.phone2:
                properties["ph2"] = o.phone2
            if o.email:
                properties["email"] = o.email
            if o.website:
                properties["web"] = o.website
            n = f.req_site_needs
            if n:
                if n.needs:
                    needs = json.loads(n.needs)
                    if "urgent" in needs:
                        properties["urgent"] = needs["urgent"]
                    if "need" in needs:
                        properties["need"] = needs["need"]
                    if "no" in needs:
                        properties["no"] = needs["no"]
            f = dict(
                type = "Feature",
                properties = properties,
                geometry = json.loads(geojson)
                )
            append(f)
        data = dict(
                    type = "FeatureCollection",
                    features = features
                    )
        output = json.dumps(data)
        if jsonp:
            filename = "facility.geojsonp"
            output = "grid(%s)" % output
        else:
            filename = "facility.geojson"
        path = os.path.join(current.request.folder,
                            "static", "cache",
                            filename)
        File = open(path, "w")
        File.write(output)
        File.close()

# -----------------------------------------------------------------------------
def org_facility_rheader(r, tabs=[]):
    """
        RHeader for facilities when doing a req_match
    """

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
'''S3OptionsFilter({
 'triggerName':'site_id',
 'targetName':'room_id',
 'lookupPrefix':'org',
 'lookupResource':'room',
})''')
                           )

        # Reusable field for other tables to reference
        represent = S3Represent(lookup=tablename)
        room_id = S3ReusableField("room_id", table,
                                  sortby="name",
                                  requires=IS_NULL_OR(
                                            IS_ONE_OF(db, "org_room.id",
                                                      represent
                                                      )),
                                  represent=represent,
                                  label=T("Room"),
                                  comment=room_comment,
                                  ondelete="SET NULL"
                                  )

        self.configure(tablename,
                       deduplicate=self.org_room_duplicate,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
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
        settings = current.deployment_settings
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
        ADD_OFFICE_TYPE = T("Add New Office Type")
        crud_strings[tablename] = Storage(
            title_create=T("Add Office Type"),
            title_display=T("Office Type Details"),
            title_list=T("Office Types"),
            title_update=T("Edit Office Type"),
            title_search=T("Search Office Types"),
            subtitle_create=ADD_OFFICE_TYPE,
            label_list_button=T("List Office Types"),
            label_create_button=ADD_OFFICE_TYPE,
            label_delete_button=T("Delete Office Type"),
            msg_record_created=T("Office Type added"),
            msg_record_modified=T("Office Type updated"),
            msg_record_deleted=T("Office Type deleted"),
            msg_list_empty=T("No Office Types currently registered"))

        represent = S3Represent(lookup=tablename)
        office_type_id = S3ReusableField("office_type_id", table,
                            sortby="name",
                            requires=IS_NULL_OR(
                                        IS_ONE_OF(db, "org_office_type.id",
                                                  represent,
                                                  sort=True
                                                  )),
                            represent=represent,
                            label=T("Office Type"),
                            comment=S3AddResourceLink(c="org",
                                f="office_type",
                                label=ADD_OFFICE_TYPE,
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
                                   label=T("Code"),
                                   # Deployments that don't wants office codes can hide them
                                   #readable=False,
                                   #writable=False,
                                   # @ToDo: Deployment Setting to add validator to make these unique
                                   ),
                             self.org_organisation_id(
                                 #widget=S3OrganisationAutocompleteWidget(default_from_profile=True),
                                 requires = org_organisation_requires(required=True,
                                                                      updateable=True),
                                 ),
                             office_type_id(
                                            #readable = False,
                                            #writable = False,
                                            ),
                             self.gis_location_id(),
                             Field("phone1", label=T("Phone 1"),
                                   requires=IS_NULL_OR(s3_phone_requires),
                                   represent = lambda v: v or "",
                                   ),
                             Field("phone2", label=T("Phone 2"),
                                   requires=IS_NULL_OR(s3_phone_requires),
                                   represent = lambda v: v or "",
                                   ),
                             Field("email", label=T("Email"),
                                   requires=IS_NULL_OR(IS_EMAIL()),
                                   represent = lambda v: v or "",
                                   ),
                             Field("fax", label=T("Fax"),
                                   requires=IS_NULL_OR(s3_phone_requires),
                                   represent = lambda v: v or "",
                                   ),
                             Field("obsolete", "boolean",
                                   label=T("Obsolete"),
                                   represent=lambda bool: \
                                    (bool and [T("Obsolete")] or [messages["NONE"]])[0],
                                   default=False,
                                   readable=False,
                                   writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_OFFICE = T("Add New Office")
        crud_strings[tablename] = Storage(
            title_create=T("Add Office"),
            title_display=T("Office Details"),
            title_list=T("Offices"),
            title_update=T("Edit Office"),
            title_search=T("Search Offices"),
            title_upload=T("Import Offices"),
            title_map=T("Map of Offices"),
            subtitle_create=ADD_OFFICE,
            label_list_button=T("List Offices"),
            label_create_button=ADD_OFFICE,
            label_delete_button=T("Delete Office"),
            msg_record_created=T("Office added"),
            msg_record_modified=T("Office updated"),
            msg_record_deleted=T("Office deleted"),
            msg_list_empty=T("No Offices currently registered"))

        # Search Method
        if settings.get_org_branches():
            ORGANISATION = T("Organization/Branch")
            comment = T("Search for office by organization or branch.")
        else:
            ORGANISATION = T("Organization")
            comment = T("Search for office by organization.")
        search_method = S3Search(
            simple=(),
            advanced=(S3SearchSimpleWidget(
                        name="office_search_text",
                        label=T("Search"),
                        comment=T("Search for office by text."),
                        field=["name", "comments", "email"]
                      ),
                      S3SearchOptionsWidget(
                        name="office_search_org",
                        label=ORGANISATION,  
                        comment=comment,
                        field="organisation_id",
                        represent="%(name)s",
                        cols=3
                      ),
                      S3SearchOptionsWidget(
                        name="office_search_L0",
                        field="location_id$L0",
                        location_level="L0",
                        cols=3
                      ),
                      S3SearchOptionsWidget(
                        name="office_search_L1",
                        field="location_id$L1",
                        location_level="L1",
                        cols=3
                      ),
                      S3SearchOptionsWidget(
                        name="office_search_L2",
                        field="location_id$L2",
                        location_level="L2",
                        cols=3
                      ),
                      # Disabled until fixed (which will be in new S3FilterForm)
                      #S3SearchLocationWidget(
                      #  name="office_search_map",
                      #  label=T("Map"),
                      #),
            ))

        filter_widgets = [
                S3TextFilter(["name",
                              "code",
                              "comments",
                              "organisation_id$name",
                              "organisation_id$acronym",
                              "location_id$name",
                              "location_id$L1",
                              "location_id$L2",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                #S3OptionsFilter("office_type_id",
                #                label=T("Type"),
                #                represent="%(name)s",
                #                widget="multiselect",
                #                cols=3,
                #                #hidden=True,
                #                ),
                S3OptionsFilter("organisation_id",
                                label=messages.ORGANISATION,
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("location_id",
                                 label=T("Location"),
                                 levels=["L0", "L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                ]

        configure(tablename,
                  super_entity=("pr_pentity", "org_site"),
                  onaccept=self.org_office_onaccept,
                  deduplicate=self.org_office_duplicate,
                  filter_widgets=filter_widgets,
                  search_method=search_method,
                  list_fields=["id",
                               "name",
                               "organisation_id", # Filtered in Component views
                               "office_type_id",
                               (messages.COUNTRY, "location_id$L0"),
                               "location_id$L1",
                               "location_id$L2",
                               "location_id$L3",
                               #"location_id$L4",
                               (T("Address"), "location_id$addr_street"),
                               "phone1",
                               "email"
                               ],
                  context = {"location": "location_id",
                             "organisation": "organisation_id",
                             },
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

        if settings.get_org_summary():
            add_component("org_office_summary",
                          org_office=dict(name="summary",
                                          joinby="office_id"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
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

    # ---------------------------------------------------------------------
    @staticmethod
    def org_office_onaccept(form):
        """
            * Update Affiliation and Realms
            * Process injected fields
        """

        vars = form.vars

        # Affiliation, record ownership and component ownership
        org_update_affiliations("org_office", vars)

        if current.deployment_settings.get_org_summary():

            db = current.db
            id = vars.id
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
            Import item deduplication: simple match by name
                (Adding location_id doesn't seem to be a good idea)

            @param item: the S3ImportItem instance
        """

        if item.tablename == "org_office":
            table = item.table
            name = "name" in item.data and item.data.name or None
            if name:
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

        @ToDo: Deprecate in favour of S3OrganisationResourceModel
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
        # Pass names back to global scope (s3.*)
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
        # Pass names back to global scope (s3.*)
        #
        return Storage(
                )

# =============================================================================
def org_organisation_address(row):
    """ The address of the first office """

    if hasattr(row, "org_organisation"):
        row = row.org_organisation
    try:
        organisation_id = row.id
    except:
        # not available
        return current.messages["NONE"]

    db = current.db
    s3db = current.s3db

    otable = s3db.org_office
    gtable = s3db.gis_location
    query = (otable.deleted != True) & \
            (otable.organisation_id == organisation_id) & \
            (otable.location_id == gtable.id)
    row = db(query).select(gtable.addr_street, limitby=(0, 1)).first()

    if row:
        row.addr_street
    else:
        return current.messages["NONE"]

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
        record = current.db(query).select(table.name,
                                          table.acronym,
                                          table.logo,
                                          limitby=(0, 1)).first()

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

        @return: tuple of (id, pe_id) of the root organisation,
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
def org_organisation_requires(required = False,
                              realms = None,
                              updateable = False
                              ):
    """
        @param required: Whether the selection is optional or mandatory
        @param realms: Whether the list should be filtered to just those
                       belonging to a list of realm entities
        @param updateable: Whether the list should be filtered to just those
                           which the user has Write access to
    """

    requires = IS_ONE_OF(current.db, "org_organisation.id",
                         org_OrganisationRepresent(),
                         realms = realms,
                         updateable = updateable,
                         orderby = "org_organisation.name",
                         sort = True)
    if not required:
        requires = IS_NULL_OR(requires)
    return requires

# =============================================================================
class org_OrganisationRepresent(S3Represent):
    """ Representation of Organisations """

    def __init__(self,
                 translate=False,
                 show_link=False,
                 parent=True,
                 acronym=True,
                 multiple=False):

        self.acronym = acronym

        if parent and current.deployment_settings.get_org_branches():
            # Need a custom lookup
            self.parent = True
            self.lookup_rows = self.custom_lookup_rows
            fields = ["org_organisation.name",
                      "org_organisation.acronym",
                      "org_parent_organisation.name",
                      ]
        else:
            # Can use standard lookup of fields
            self.parent = False
            fields = ["name", "acronym"]

        super(org_OrganisationRepresent,
              self).__init__(lookup="org_organisation",
                             fields=fields,
                             show_link=show_link,
                             translate=translate,
                             multiple=multiple)

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=[]):
        """
            Custom lookup method for organisation rows, does a
            left join with the parent organisation. Parameters
            key and fields are not used, but are kept for API
            compatiblity reasons.

            @param values: the organisation IDs
        """

        db = current.db
        otable = current.s3db.org_organisation
        btable = db.org_organisation_branch
        ptable = db.org_organisation.with_alias("org_parent_organisation")

        left = [btable.on(btable.branch_id == otable.id),
                ptable.on(ptable.id == btable.organisation_id)]

        if len(values) == 1:
            query = (otable.id == values[0])
            limitby = (0, 1)
        else:
            query = (otable.id.belongs(values))
            limitby = None
        rows = db(query).select(otable.id,
                                otable.name,
                                otable.acronym,
                                ptable.name,
                                left=left,
                                limitby=limitby)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the org_organisation Row
        """

        if self.parent:
            # Custom Row (with the parent left-joined)
            name = row["org_organisation.name"]
            acronym = row["org_organisation.acronym"]
            parent = row["org_parent_organisation.name"]
        else:
            # Standard row (from fields)
            name = row["name"]
            acronym = row["acronym"]

        if not name:
            return self.default
        if self.acronym and acronym:
            name = "%s (%s)" % (name, acronym)
        if self.parent and parent:
            name = "%s > %s" % (parent, name)
        return s3_unicode(name)
        
# =============================================================================
def org_site_top_req_priority(row, tablename="org_facility"):
    """ Highest priority of open requests for a site """

    try:
        from req import REQ_STATUS_COMPLETE
    except ImportError:
        return None
    
    if hasattr(row, tablename):
        row = row[tablename]
    try:
        id = row.id
    except AttributeError:
        return None

    s3db = current.s3db
    rtable = s3db.req_req
    stable = s3db[tablename]
    
    query = (rtable.deleted != True) & \
            (stable.id == id) & \
            (rtable.site_id == stable.site_id) & \
            (rtable.fulfil_status != REQ_STATUS_COMPLETE) & \
            (rtable.is_template == False)
            
    req = current.db(query).select(rtable.id,
                                   rtable.priority,
                                   orderby=~rtable.priority,
                                   limitby=(0, 1)).first()
                                   
    if req:
        return req.priority
    else:
        return None

# =============================================================================
def org_site_represent(id, row=None, show_link=True):
    """
        Represent a Facility in option fields or list views

        @param id: the site_id
        @param row: the org_site Row
        @param show_link: whether to render the representation as link
    """

    if row:
        db = current.db
        s3db = current.s3db
        stable = s3db.org_site
        id = row.site_id
    elif id:
        db = current.db
        s3db = current.s3db
        stable = s3db.org_site
        try:
            row = db(stable._id == id).select(stable.instance_type,
                                              limitby=(0, 1)).first()
        except:
            # Bad data (e.g. list:reference)
            return current.messages.UNKNOWN_OPT
    else:
        return current.messages["NONE"]

    instance_type = row.instance_type
    instance_type_nice = stable.instance_type.represent(instance_type)

    try:
        table = s3db[instance_type]
    except:
        return current.messages.UNKNOWN_OPT

    if instance_type == "org_facility":
        # Lookup Facility Type
        r = db(table.site_id == id).select(table.id,
                                           table.name,
                                           table.facility_type_id,
                                           limitby=(0, 1)).first()
        try:
            if r.facility_type_id:
                facility_type = r.facility_type_id[0]
                table = s3db.org_facility_type
                type = db(table.id == facility_type).select(table.name,
                                                            limitby=(0, 1),
                                                            ).first().name
                instance_type_nice = current.T(type)
        except:
            return current.messages.UNKNOWN_OPT
    else:
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
        # extension="" removes the .aaData extension in paginated views
        represent = A(represent,
                      _href=URL(c=c, f=f, args=[r.id], extension=""))

    return represent

# =============================================================================
def org_rheader(r, tabs=[]):
    """ Organisation/Office/Facility page headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    # Need to use this format as otherwise req_match?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3_rheader_resource(r)

    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    T = current.T
    s3db = current.s3db
    # These 2 needed for req_match
    r.record = record
    r.table = \
    table = s3db[tablename]
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
                    (T("Assets"), "asset"),
                    (T("Projects"), "project"),
                    (T("User Roles"), "roles"),
                    #(T("Tasks"), "task"),
                    ]
            # If a filter is being applied to the Organisations, amend the tabs accordingly
            type_filter = current.request.get_vars.get("organisation.organisation_type_id$name",
                                                       None)
            if type_filter:
                if type_filter == "Supplier":
                    tabs = [(T("Basic Details"), None),
                            (T("Offices"), "office"),
                            (T("Warehouses"), "warehouse"),
                            (T("Contacts"), "human_resource"),
                            ]
                elif type_filter == "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency":
                    tabs = [(T("Basic Details"), None, {"native": 1}),
                            (T("Branches"), "branch"),
                            (T("Offices"), "office"),
                            (T("Warehouses"), "warehouse"),
                            (T("Contacts"), "human_resource"),
                            (T("Projects"), "project"),
                            ]
        rheader_tabs = s3_rheader_tabs(r, tabs)

        # @ToDo: Update for Component
        # if record.sector_id:
        #    if settings.get_ui_label_cluster():
        #        sector_label = T("Cluster(s)")
        #    else:
        #        sector_label = T("Sector(s)")
        #    sectors = TR(TH("%s: " % sector_label),
        #                 table.sector_id.represent(record.sector_id))
        # else:
        #    sectors = ""

        if record.website:
            website = TR(TH("%s: " % table.website.label),
                         A(record.website, _href=record.website))
        else:
            website = ""

        rheader = DIV()
        logo = org_organisation_logo(record)
        rData = TABLE(TR(TH("%s: " % table.name.label),
                         record.name,
                         ),
                      website,
                      #sectors,
                      )
        if logo:
            rheader.append(TABLE(TR(TD(logo), TD(rData))))
        else:
            rheader.append(rData)
        rheader.append(rheader_tabs)

    elif tablename in ("org_office", "org_facility"):
        STAFF = settings.get_hrm_staff_label()
        tabs = [(T("Basic Details"), None),
                #(T("Contact Data"), "contact"),
                (STAFF, "human_resource"),
                ]
        if current.auth.s3_has_permission("create", "hrm_human_resource"):
            tabs.append((T("Assign %(staff)s") % dict(staff=STAFF), "human_resource_site"))
        if settings.get_req_summary():
            tabs.append((T("Needs"), "site_needs"))
        if settings.has_module("asset"):
            tabs.append((T("Assets"), "asset"))
        if settings.has_module("inv"):
            tabs = tabs + s3db.inv_tabs(r)
        if settings.has_module("req"):
            tabs = tabs + s3db.req_tabs(r)
        tabs.append((T("Attachments"), "document"))
        tabs.append((T("User Roles"), "roles"))

        if tablename == "org_office":
            rheader_fields = [["name", "organisation_id", "email"],
                              ["office_type_id", "location_id", "phone1"],
                              ]
        else:
            rheader_fields = [["name", "organisation_id", "email"],
                              ["facility_type_id", "location_id", "phone1"],
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

        if settings.has_module("inv"):
            # Build footer
            s3db.inv_rfooter(r, record)

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

    T = current.T
    db = current.db
    s3db = current.s3db
    s3 = current.response.s3
    settings = current.deployment_settings

    # Pre-process
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.representation == "json":
            r.table.pe_id.readable = True
            list_fields = s3db.get_config(r.tablename,
                                          "list_fields") or []
            s3db.configure(r.tablename, list_fields=list_fields + ["pe_id"])
        elif r.interactive or r.representation.lower() == "aadata":
            request = current.request
            gis = current.gis
            r.table.country.default = gis.get_default_country("code")

            if not r.component and r.method not in ["read", "update", "delete", "deduplicate"]:
                use_branches = settings.get_org_branches()
                if use_branches:
                    # Filter Branches
                    branch_filter = (S3FieldSelector("parent.id") == None)
                # Filter Locations
                lfilter = current.session.s3.location_filter
                if lfilter:
                    # Include those whose parent is in a different country
                    gtable = s3db.gis_location
                    query = (gtable.id == lfilter)
                    row = db(query).select(gtable.id,
                                           gtable.name,
                                           gtable.level,
                                           gtable.path,
                                           limitby=(0, 1)).first()
                    if row and row.level:
                        if row.level != "L0":
                            code = gis.get_parent_country(row, key_type="code")
                        else:
                            ttable = s3db.gis_location_tag
                            query = (ttable.tag == "ISO2") & \
                                    (ttable.location_id == row.id)
                            tag = db(query).select(ttable.value,
                                                   limitby=(0, 1)).first()
                            code = tag.value
                        # Filter out Branches
                        branch_filter |= (S3FieldSelector("parent.country") != code) | \
                                         (S3FieldSelector("parent.country") == None)
                if use_branches:
                    r.resource.add_filter(branch_filter)
                    search_fields = ["name",
                                     "acronym",
                                     "parent.name",
                                     "parent.acronym",
                                     ]
                else:
                    search_fields = ["name", "acronym"]
                if settings.get_ui_label_cluster():
                    SECTOR = T("Cluster")
                else:
                    SECTOR = T("Sector")
                search_method = S3Search(
                        # simple = (S3SearchSimpleWidget(
                            # name="org_search_text_simple",
                            # label = T("Search"),
                            # comment = T("Search for an Organization by name or acronym."),
                            # field = search_fields
                            # )
                        # ),
                        simple=(),
                        advanced=(
                            S3SearchSimpleWidget(
                                name="org_search_text_advanced",
                                label=T("Search"),
                                comment=T("Search for an Organization by name or acronym"),
                                field=search_fields
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
                                field="sector.name",
                                options=s3db.org_sector_opts,
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
                s3db.configure("org_organisation", search_method=search_method)

            else:
                cname = r.component_name
                if cname == "human_resource" and r.component_id:
                    # Workaround until widget is fixed:
                    htable = s3db.hrm_human_resource
                    htable.person_id.widget = None
                    htable.person_id.writable = False

                elif cname == "branch":
                    # Branches default to the same type/country as the parent
                    otable = r.table
                    record = r.record
                    otable.organisation_type_id.default = record.organisation_type_id
                    otable.region.default = record.region
                    otable.country.default = record.country
                    # @ToDo: Update for components
                    #otable.sector_id.default = record.sector_id
                    # Represent orgs without the parent prefix as we have that context already
                    s3db.org_organisation_branch.branch_id.represent = \
                        org_OrganisationRepresent(parent=False)

                elif cname == "task" and \
                     r.method != "update" and r.method != "read":
                    # Create or ListCreate
                    ttable = r.component.table
                    ttable.organisation_id.default = r.id
                    ttable.status.writable = False
                    ttable.status.readable = False

                elif cname == "asset":
                    # Filter the Site field
                    field = s3db.super_link("site_id", "org_site",
                                            empty = False,
                                            filterby="organisation_id",
                                            filter_opts=(r.id,),
                                            represent = s3db.org_site_represent,
                                            )
                    atable = s3db.asset_asset
                    atable.site_id.requires = field.requires
                    # Stay within Organisation tab
                    s3db.configure("asset_asset",
                                   create_next = None)

                elif cname == "project" and r.link:
                    # Hide/show host role after project selection in embed-widget
                    tn = r.link.tablename
                    s3db.configure(tn,
                                   post_process='''S3.hide_host_role($('#%s').val())''')
                    s3.scripts.append("/%s/static/scripts/S3/s3.hide_host_role.js" % \
                        request.application)

            s3db.configure("project_project", create_next=None)

            # If a filter is being applied to the Organisations, change the CRUD Strings accordingly
            type_filter = request.get_vars.get("organisation.organisation_type_id$name", None)
            if type_filter:
                ADD_NS = T("Add National Society")
                ADD_PARTNER = T("Add Partner Organization")
                ADD_SUPPLIER = T("Add Supplier")
                type_crud_strings = {
                    "Red Cross / Red Crescent" :
                        # @ToDo: IFRC isn't an NS?
                        Storage(
                            title_create=ADD_NS,
                            title_display=T("National Society Details"),
                            title_list=T("Red Cross & Red Crescent National Societies"),
                            title_update=T("Edit National Society"),
                            title_search=T("Search Red Cross & Red Crescent National Societies"),
                            title_upload=T("Import Red Cross & Red Crescent National Societies"),
                            subtitle_create=ADD_NS,
                            label_list_button=T("List Red Cross & Red Crescent National Societies"),
                            label_create_button=ADD_NS,
                            label_delete_button=T("Delete National Society"),
                            msg_record_created=T("National Society added"),
                            msg_record_modified=T("National Society updated"),
                            msg_record_deleted=T("National Society deleted"),
                            msg_list_empty=T("No Red Cross & Red Crescent National Societies currently registered")
                            ),
                    "Supplier" :
                        Storage(
                            title_create=ADD_SUPPLIER,
                            title_display=T("Supplier Details"),
                            title_list=T("Suppliers"),
                            title_update=T("Edit Supplier"),
                            title_search=T("Search Suppliers"),
                            title_upload=T("Import Suppliers"),
                            subtitle_create=ADD_SUPPLIER,
                            label_list_button=T("List Suppliers"),
                            label_create_button=T("Add Suppliers"),
                            label_delete_button=T("Delete Supplier"),
                            msg_record_created=T("Supplier added"),
                            msg_record_modified=T("Supplier updated"),
                            msg_record_deleted=T("Supplier deleted"),
                            msg_list_empty=T("No Suppliers currently registered")
                            ),
                    "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency" :
                        Storage(
                            title_create=ADD_PARTNER,
                            title_display=T("Partner Organization Details"),
                            title_list=T("Partner Organizations"),
                            title_update=T("Edit Partner Organization"),
                            title_search=T("Search Partner Organizations"),
                            title_upload=T("Import Partner Organizations"),
                            subtitle_create=ADD_PARTNER,
                            label_list_button=T("List Partner Organizations"),
                            label_create_button=T("Add Partner Organizations"),
                            label_delete_button=T("Delete Partner Organization"),
                            msg_record_created=T("Partner Organization added"),
                            msg_record_modified=T("Partner Organization updated"),
                            msg_record_deleted=T("Partner Organization deleted"),
                            msg_list_empty=T("No Partner Organizations currently registered")
                            ),
                    }

                # Filter type field
                type_names = [name.lower().strip()
                              for name in type_filter.split(",")]
                type_table = s3db.org_organisation_type
                fquery = (type_table.name.lower().belongs(type_names))
                field = r.table.organisation_type_id
                if len(type_names) == 1:
                    list_fields = s3db.get_config("org_organisation", "list_fields")
                    try:
                        list_fields.remove("organisation_type_id")
                    except:
                        pass
                    else:
                        s3db.configure("org_organisation", list_fields=list_fields)
                    # Default the Type
                    if not r.method or r.method == "create":
                        query = (type_table.name == type_filter)
                        row = db(query).select(type_table.id,
                                               limitby=(0, 1)).first()
                        type = row and row.id
                        if type:
                            field.default = type
                            field.writable = False

                field.requires = IS_ONE_OF(db(fquery),
                                           "org_organisation_type.id",
                                           label=field.represent,
                                           error_message=T("Please choose a type"),
                                           sort=True)
                field.comment = None # AddResourceLink makes no sense here

                if type_filter in type_crud_strings:
                    s3.crud_strings.org_organisation = type_crud_strings[type_filter]

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component and \
               settings.get_org_summary():
                # Insert fields to view/record the summary data
                # @ToDo: Re-implement using http://eden.sahanafoundation.org/wiki/S3SQLForm
                table = s3db.org_organisation_summary
                field1 = table.national_staff
                field2 = table.international_staff
                row = None
                if r.id:
                    query = (table.organisation_id == r.id)
                    row = db(query).select(field1,
                                           field2,
                                           limitby=(0, 1)).first()
                s3_formstyle = settings.get_ui_formstyle()
                if r.method == "read" and \
                   "item" in output:
                    for field in [field1, field2]:
                        if row:
                            widget = row[field]
                        else:
                            widget = current.messages["NONE"]
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        comment = ""
                        rows = s3_formstyle(row_id, label, widget, comment)
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
                        rows = s3_formstyle(row_id, label, widget, comment)
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

            else:
                cname = r.component_name
                if cname == "human_resource":
                    # Modify action button to open staff instead of human_resource
                    # (Delete not overridden to keep errors within Tab)
                    read_url = URL(c="hrm", f="staff", args=["[id]"])
                    update_url = URL(c="hrm", f="staff", args=["[id]", "update"])
                    S3CRUD.action_buttons(r, read_url=read_url,
                                             update_url=update_url)

        return output
    s3.postp = postp

    output = current.rest_controller("org", "organisation",
                                     #hide_filter = {None: False},
                                     # Don't allow components with components (such as document) to breakout from tabs
                                     native=False,
                                     rheader=org_rheader,
                                     # Need to be explicit since can also come from Project controller
                                     csv_template=("org", "organisation"),
                                     csv_stylesheet=("org", "organisation.xsl"),
                                     )
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
                cname = r.component_name
                if cname in ("inv_item", "recv", "send"):
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                    # Remove CRUD generated buttons in the tabs
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
                    field = htable.organisation_id
                    field.default = r.record.organisation_id
                    field.writable = False
                    field.comment = None
                    # Filter out people which are already staff for this office
                    s3_filter_staff(r)

                elif cname == "req" and r.method not in ("update", "read"):
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    s3db.req_create_form_mods()

                elif cname == "asset":
                    # Default/Hide the Organisation & Site fields
                    record = r.record
                    atable = s3db.asset_asset
                    field = atable.organisation_id
                    field.default = record.organisation_id
                    field.readable = field.writable = False
                    field = atable.site_id
                    field.default = record.site_id
                    field.readable = field.writable = False
                    # Stay within Office tab
                    s3db.configure("asset_asset",
                                   create_next = None)

            elif r.method in ("create", "update"):
                if r.method == "update":
                    table.obsolete.readable = table.obsolete.writable = True
                # Context from a Profile page?"
                org_id = request.get_vars.get("(organisation)", None)
                if org_id:
                    field = table.organisation_id
                    field.default = org_id
                    field.readable = field.writable = False
            elif r.id:
                table.obsolete.readable = table.obsolete.writable = True
            elif r.representation == "geojson":
                marker_fn = s3db.get_config("org_office", marker_fn)
                if marker_fn:
                    # Load these models now as they'll be needed when we encode
                    mtable = s3db.gis_marker

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component and \
               settings.get_org_summary():
                # Insert fields to view/record the summary data
                # @ToDo: Re-implement using http://eden.sahanafoundation.org/wiki/S3SQLForm
                table = s3db.org_office_summary
                field1 = table.national_staff
                field2 = table.international_staff
                row = None
                if r.id:
                    query = (table.office_id == r.id)
                    row = current.db(query).select(field1,
                                                   field2,
                                                   limitby=(0, 1)).first()
                s3_formstyle = settings.get_ui_formstyle()
                if r.method == "read" and \
                   "item" in output:
                    for field in [field1, field2]:
                        if row:
                            widget = row[field]
                        else:
                            widget = current.messages["NONE"]
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        comment = ""
                        rows = s3_formstyle(row_id, label, widget, comment)
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

                elif r.method not in ("import", "map", "search") and \
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
                        rows = s3_formstyle(row_id, label, widget, comment)
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

            else:
                cname = r.component_name
                if cname == "human_resource":
                    # Modify action button to open staff instead of human_resource
                    # (Delete not overridden to keep errors within Tab)
                    read_url = URL(c="hrm", f="staff", args=["[id]"])
                    update_url = URL(c="hrm", f="staff", args=["[id]", "update"])
                    S3CRUD.action_buttons(r, read_url=read_url,
                                             update_url=update_url)
        return output
    s3.postp = postp

    if "map" in request.args:
        # S3Map has migrated
        hide_filter = False
    else:
        # Not yet ready otherwise
        hide_filter = True

    output = current.rest_controller("org", "office",
                                     hide_filter=hide_filter,
                                     # Don't allow components with components (such as document) to breakout from tabs
                                     native=False,
                                     rheader=org_rheader)
    return output

# =============================================================================
# Hierarchy Manipulation
# =============================================================================
#
def org_update_affiliations(table, record):
    """
        Update OU affiliations related to this record

        @param table: the table
        @param record: the record
    """

    if hasattr(table, "_tablename"):
        rtype = table._tablename
    else:
        rtype = table

    if rtype == "org_organisation_branch":

        ltable = current.s3db.org_organisation_branch
        if not isinstance(record, Row):
            record = current.db(ltable.id == record).select(ltable.ALL,
                                                            limitby=(0, 1)
                                                            ).first()
        if not record:
            return
        organisation_update_affiliations(record)

    elif rtype == "org_group_membership":

        mtable = current.s3db.org_group_membership
        if not isinstance(record, Row):
            record = current.db(mtable.id == record).select(mtable.ALL,
                                                            limitby=(0, 1)
                                                            ).first()
        if not record:
            return
        org_group_update_affiliations(record)

    elif rtype == "org_site" or rtype in current.auth.org_site_types:

        org_site_update_affiliations(record)

    return

# =============================================================================
def organisation_update_affiliations(record):
    """
        Update affiliations for a branch organisation

        @param record: the org_organisation_branch record
    """

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            branch_id = fk["branch_id"]
        except:
            return
    else:
        branch_id = record.branch_id

    from pr import OU
    BRANCHES = "Branches"

    db = current.db
    s3db = current.s3db
    otable = s3db.org_organisation
    btable = otable.with_alias("branch")
    ltable = db.org_organisation_branch
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

    o = otable._tablename
    b = btable._tablename
    r = rtable._tablename

    # Get current memberships
    query = (ltable.branch_id == branch_id) & \
            (ltable.deleted != True)
    left = [otable.on(ltable.organisation_id == otable.id),
            btable.on(ltable.branch_id == btable.id)]
    rows = db(query).select(otable.pe_id, btable.pe_id, left=left)
    current_memberships = [(row[o].pe_id, row[b].pe_id) for row in rows]

    # Get current affiliations
    query = (rtable.deleted != True) & \
            (rtable.role == BRANCHES) & \
            (rtable.pe_id == etable.pe_id) & \
            (etable.instance_type == o) & \
            (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == btable.pe_id) & \
            (btable.id == branch_id)
    rows = db(query).select(rtable.pe_id, btable.pe_id)
    current_affiliations = [(row[r].pe_id, row[b].pe_id) for row in rows]

    # Remove all affiliations which are not current memberships
    remove_affiliation = s3db.pr_remove_affiliation
    for a in current_affiliations:
        org, branch = a
        if a not in current_memberships:
            remove_affiliation(org, branch, role=BRANCHES)
        else:
            current_memberships.remove(a)

    # Add affiliations for all new memberships
    add_affiliation = s3db.pr_add_affiliation
    for m in current_memberships:
        org, branch = m
        add_affiliation(org, branch, role=BRANCHES, role_type=OU)
    return

# =============================================================================
def org_group_update_affiliations(record):
    """
        Update affiliations for organisation group memberships

        @param record: the org_group_membership record
    """

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            organisation_id = fk["organisation_id"]
        except:
            return
    else:
        organisation_id = record.organisation_id

    MEMBER = 2 # role_type == "Member"
    MEMBERS = "Members"

    db = current.db
    s3db = current.s3db
    mtable = s3db.org_group_membership
    otable = db.org_organisation
    gtable = db.org_group
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

    g = gtable._tablename
    r = rtable._tablename
    o = otable._tablename

    # Get current memberships
    query = (mtable.organisation_id == organisation_id) & \
            (mtable.deleted != True)
    left = [otable.on(mtable.organisation_id == otable.id),
            gtable.on(mtable.group_id == gtable.id)]
    rows = db(query).select(otable.pe_id, gtable.pe_id, left=left)
    current_memberships = [(row[g].pe_id, row[o].pe_id) for row in rows]

    # Get current affiliations
    query = (rtable.deleted != True) & \
            (rtable.role == MEMBERS) & \
            (rtable.pe_id == etable.pe_id) & \
            (etable.instance_type == g) & \
            (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == otable.pe_id) & \
            (otable.id == organisation_id)
    rows = db(query).select(otable.pe_id, rtable.pe_id)
    current_affiliations = [(row[r].pe_id, row[o].pe_id) for row in rows]

    # Remove all affiliations which are not current memberships
    remove_affiliation = s3db.pr_remove_affiliation
    for a in current_affiliations:
        group, org = a
        if a not in current_memberships:
            remove_affiliation(group, org, role=MEMBERS)
        else:
            current_memberships.remove(a)

    # Add affiliations for all new memberships
    add_affiliation = s3db.pr_add_affiliation
    for m in current_memberships:
        group, org = m
        add_affiliation(group, org, role=MEMBERS, role_type=MEMBER)
    return

# =============================================================================
def org_site_update_affiliations(record):
    """
        Update the affiliations of an org_site instance

        @param record: the org_site instance record
    """

    from pr import OU
    SITES = "Sites"

    db = current.db
    s3db = current.s3db
    stable = s3db.org_site
    otable = db.org_organisation
    ptable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

    o_pe_id = None
    s_pe_id = record.pe_id

    organisation_id = record.organisation_id
    if organisation_id:
        org = db(otable.id == organisation_id).select(otable.pe_id,
                                                      limitby=(0, 1)).first()
        if org:
            o_pe_id = org.pe_id
    if s_pe_id:
        query = (atable.deleted != True) & \
                (atable.pe_id == s_pe_id) & \
                (rtable.deleted != True) & \
                (rtable.id == atable.role_id) & \
                (rtable.role == SITES) & \
                (ptable.pe_id == rtable.pe_id) & \
                (ptable.instance_type == str(otable))
        rows = db(query).select(rtable.pe_id)
        seen = False
        
        remove_affiliation = s3db.pr_remove_affiliation
        for row in rows:
            if o_pe_id == None or o_pe_id != row.pe_id:
                remove_affiliation(row.pe_id, s_pe_id, role=SITES)
            elif o_pe_id == row.pe_id:
                seen = True
        if o_pe_id and not seen:
            s3db.pr_add_affiliation(o_pe_id, s_pe_id, role=SITES,
                                    role_type=OU)
    return

# END =========================================================================
