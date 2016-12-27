# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for American Red Cross

        Demo only, not in Production
    """

    T = current.T

    # =========================================================================
    # System Settings
    # -------------------------------------------------------------------------
    # Pre-Populate
    settings.base.prepopulate += ("ARC", "ARC/Demo", "default/users")

    settings.base.system_name = T("Resource Management System")
    settings.base.system_name_short = T("ARC Demo")

    # -------------------------------------------------------------------------
    # Security Policy
    settings.security.policy = 8 # Delegations
    settings.security.map = True

    # Authorization Settings
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requires_verification = True
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_organisation_required = True
    settings.auth.registration_requests_site = True

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               "volunteer": T("Volunteer"),
                                               "member": T("Member")
                                               }

    settings.auth.record_approval = True

    # @ToDo: Should we fallback to organisation_id if site_id is None?
    settings.auth.registration_roles = {"site_id": ["reader",
                                                    ],
                                        }

    # Owner Entity
    settings.auth.person_realm_human_resource_site_then_org = True
    settings.auth.person_realm_member_org = True

    def ifrc_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        tablename = table._tablename

        # Do not apply realms for Master Data
        # @ToDo: Restore Realms and add a role/functionality support for Master Data
        if tablename in ("hrm_certificate",
                         "hrm_department",
                         "hrm_job_title",
                         "hrm_course",
                         "hrm_programme",
                         "member_membership_type",
                         "vol_award",
                         ):
            return None

        db = current.db
        s3db = current.s3db

        # Entity reference fields
        EID = "pe_id"
        #OID = "organisation_id"
        SID = "site_id"
        #GID = "group_id"
        PID = "person_id"

        # Owner Entity Foreign Key
        realm_entity_fks = dict(pr_contact = EID,
                                pr_contact_emergency = EID,
                                pr_physical_description = EID,
                                pr_address = EID,
                                pr_image = EID,
                                pr_identity = PID,
                                pr_education = PID,
                                pr_note = PID,
                                hrm_human_resource = SID,
                                inv_recv = SID,
                                inv_send = SID,
                                inv_track_item = "track_org_id",
                                inv_adj_item = "adj_id",
                                req_req_item = "req_id"
                                )

        # Default Foreign Keys (ordered by priority)
        default_fks = ("catalog_id",
                       "project_id",
                       "project_location_id",
                       )

        # Link Tables
        #realm_entity_link_table = dict(
        #    project_task = Storage(tablename = "project_task_project",
        #                           link_key = "task_id"
        #                           )
        #    )
        #if tablename in realm_entity_link_table:
        #    # Replace row with the record from the link table
        #    link_table = realm_entity_link_table[tablename]
        #    table = s3db[link_table.tablename]
        #    rows = db(table[link_table.link_key] == row.id).select(table.id,
        #                                                           limitby=(0, 1))
        #    if rows:
        #        # Update not Create
        #        row = rows.first()

        # Check if there is a FK to inherit the realm_entity
        realm_entity = 0
        fk = realm_entity_fks.get(tablename, None)
        fks = [fk]
        fks.extend(default_fks)
        for default_fk in fks:
            if default_fk in table.fields:
                fk = default_fk
                # Inherit realm_entity from parent record
                if fk == EID:
                    ftable = s3db.pr_person
                    query = (ftable[EID] == row[EID])
                else:
                    ftablename = table[fk].type[10:] # reference tablename
                    ftable = s3db[ftablename]
                    query = (table.id == row.id) & \
                            (table[fk] == ftable.id)
                record = db(query).select(ftable.realm_entity,
                                          limitby=(0, 1)).first()
                if record:
                    realm_entity = record.realm_entity
                    break
                #else:
                # Continue to loop through the rest of the default_fks
                # Fall back to default get_realm_entity function

        use_user_organisation = False
        # Suppliers & Partners are owned by the user's organisation
        if realm_entity == 0 and tablename == "org_organisation":
            ottable = s3db.org_organisation_type
            ltable = db.org_organisation_organisation_type
            query = (ltable.organisation_id == row.id) & \
                    (ltable.organisation_type_id == ottable.id)
            row = db(query).select(ottable.name,
                                   limitby=(0, 1)
                                   ).first()
            if row and row.name != "Red Cross / Red Crescent":
                use_user_organisation = True

        # Groups are owned by the user's organisation
        #elif tablename in ("pr_group",):
        elif tablename == "pr_group":
            use_user_organisation = True

        user = current.auth.user
        if use_user_organisation and user:
            # @ToDo - this might cause issues if the user's org is different from the realm that gave them permissions to create the Org
            realm_entity = s3db.pr_get_pe_id("org_organisation",
                                             user.organisation_id)

        return realm_entity

    settings.auth.realm_entity = ifrc_realm_entity

    # -------------------------------------------------------------------------
    # Theme (folder to use for views/layout.html)
    settings.base.theme = "ARC"
    settings.base.xtheme = "IFRC/xtheme-ifrc.css"

    # Formstyle
    settings.ui.formstyle = "table"
    settings.ui.filter_formstyle = "table_inline"

    # Icons
    settings.ui.icons = "font-awesome3"

    settings.gis.map_height = 600
    settings.gis.map_width = 869
    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = True
    # GeoNames username
    settings.gis.geonames_username = "rms_dev"
    # Resources which can be directly added to the main map
    settings.gis.poi_create_resources = \
        (dict(c="gis",
              f="poi",
              table="gis_poi",
              type="point",
              label=T("Add PoI"),
              layer="PoIs",
              ),
         dict(c="gis",
              f="poi",
              table="gis_poi",
              type="line",
              label=T("Add Route"),
              layer="Routes",
              ),
         )

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ["US"]

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("es", "Español"),
        #("km", "ភាសាខ្មែរ"),       # Khmer
        #("ne", "नेपाली"),         # Nepali
        #("prs", "دری"),         # Dari
        #("ps", "پښتو"),         # Pashto
        #("vi", "Tiếng Việt"),   # Vietnamese
        #("zh-cn", "中文 (简体)"),
    ])
    # Default Language
    settings.L10n.default_language = "en"
    # Default timezone for users
    settings.L10n.utc_offset = "-0500"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Uncomment these to use US-style dates in English
    settings.L10n.date_format = "%m-%d-%Y"
    # Start week on Sunday
    settings.L10n.firstDOW = 0
    # PDF to Letter
    settings.base.paper_size = T("Letter")
    # Make last name in person/user records mandatory
    settings.L10n.mandatory_lastname = True
    # Uncomment this to Translate CMS Series Names
    #settings.L10n.translate_cms_series = True
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Enable this to change the label for 'Mobile Phone'
    settings.ui.label_mobile_phone = "Cell Phone"
    # Enable this to change the label for 'Postcode'
    settings.ui.label_postcode = "ZIP Code"

    settings.msg.require_international_phone_numbers = False

    # -------------------------------------------------------------------------
    # Finance settings
    settings.fin.currencies = {
        "CAD" : "Canadian Dollars",
        "EUR" : "Euros",
        "GBP" : "Great British Pounds",
        "CHF" : "Swiss Francs",
        "USD" : "United States Dollars",
    }

    # -------------------------------------------------------------------------
    # Enable this for a UN-style deployment
    #settings.ui.cluster = True
    # Enable this to use the label 'Camp' instead of 'Shelter'
    #settings.ui.camp = True

    # -------------------------------------------------------------------------
    # Summary Pages
    settings.ui.summary = [{"common": True,
                            "name": "add",
                            "widgets": [{"method": "create"}],
                            },
                           #{"common": True,
                           # "name": "cms",
                           # "widgets": [{"method": "cms"}]
                           # },
                           {"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}]
                            },
                           {"name": "charts",
                            "label": "Charts",
                            "widgets": [{"method": "report", "ajax_init": True}]
                            },
                           {"name": "map",
                            "label": "Map",
                            "widgets": [{"method": "map", "ajax_init": True}],
                            },
                           ]

    # -------------------------------------------------------------------------
    # Filter Manager
    settings.search.filter_manager = False

    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    settings.msg.parser = "IFRC"

    # =========================================================================
    # Module Settings

    # -------------------------------------------------------------------------
    # CMS
    # Uncomment to use Bookmarks in Newsfeed
    settings.cms.bookmarks = True
    # Uncomment to use have Filter form in Newsfeed be open by default
    settings.cms.filter_open = True
    # Uncomment to adjust filters in Newsfeed when clicking on locations instead of opening the profile page
    #settings.cms.location_click_filters = True
    # Uncomment to use Rich Text editor in Newsfeed
    #settings.cms.richtext = True
    # Uncomment to show Events in Newsfeed
    settings.cms.show_events = True
    # Uncomment to show Links in Newsfeed
    settings.cms.show_links = True
    # Uncomment to show Tags in Newsfeed
    #settings.cms.show_tags = True
    # Uncomment to show post Titles in Newsfeed
    #settings.cms.show_titles = True
    # Uncomment to use organisation_id instead of created_by in Newsfeed
    settings.cms.organisation = "post_organisation.organisation_id"
    # Uncomment to use org_group_id in Newsfeed
    #settings.cms.organisation_group = "created_by$org_group_id"
    #settings.cms.organisation_group = "post_organisation_group.group_id"
    # Uncomment to use person_id instead of created_by in Newsfeed
    settings.cms.person = "person_id"

    # -------------------------------------------------------------------------
    # Shelters
    # Uncomment to use a dynamic population estimation by calculations based on registrations
    #settings.cr.shelter_population_dynamic = True

    # -------------------------------------------------------------------------
    # Events
    # Make Event Types Hierarchical
    #settings.event.types_hierarchical = True
    # Make Incident Types Hierarchical
    #settings.event.incident_types_hierarchical = True

    # -------------------------------------------------------------------------
    # Organisation Management
    # Enable the use of Organisation Branches
    settings.org.branches = True
    # Hierarchical Facility Types
    settings.org.facility_types_hierarchical = True
    # Organisation Location context
    settings.org.organisation_location_context = "organisation_location.location_id"
    # Uncomment to show a Tab for Organisation Resources
    settings.org.resources_tab = True
    # Uncomment to use an Autocomplete for Site lookup fields
    settings.org.site_autocomplete = True
    # Extra fields to search in Autocompletes & display in Representations
    settings.org.site_autocomplete_fields = ("organisation_id$name",
                                             "location_id$addr_street",
                                             )
    # Set the length of the auto-generated org/site code the default is 10
    settings.org.site_code_len = 3
    # Set the label for Sites
    settings.org.site_label = "Office/Shelter/Warehouse/Facility"
    # Uncomment to allow Sites to be staffed by Volunteers
    settings.org.site_volunteers = True

    # -------------------------------------------------------------------------
    # Human Resource Management
    # Uncomment to allow Staff & Volunteers to be registered without an email address
    settings.hrm.email_required = False
    # Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
    settings.hrm.filter_certificates = True
    # Uncomment to show the Organisation name in HR represents
    settings.hrm.show_organisation = True
    # Uncomment to allow HRs to have multiple Job Titles
    settings.hrm.multiple_job_titles = True
    # Uncomment to have each root Org use a different Job Title Catalog
    settings.hrm.org_dependent_job_titles = True
    # Uncomment to disable the use of HR Credentials
    settings.hrm.use_credentials = False
    # Uncomment to enable the use of HR Education
    settings.hrm.use_education = True
    # Custom label for Organisations in HR module
    #settings.hrm.organisation_label = "National Society / Branch"
    # Uncomment to consolidate tabs into a single CV
    settings.hrm.cv_tab = True
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    settings.hrm.record_tab = "record"

    # Uncomment to do a search for duplicates in the new AddPersonWidget2
    settings.pr.lookup_duplicates = True

    # RDRT
    settings.deploy.hr_label = "Member"
    # Enable the use of Organisation Regions
    settings.org.regions = True
    # Make Organisation Regions Hierarchical
    #settings.org.regions_hierarchical = True
    # Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
    settings.hrm.skill_types = True
    # RDRT overrides these within controller:
    # Uncomment to disable Staff experience
    settings.hrm.staff_experience = False
    # Uncomment to disable the use of HR Skills
    settings.hrm.use_skills = False

    # =========================================================================
    # Template Modules
    # Comment/uncomment modules here to disable/enable them
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
                name_nice = "RMS",
                restricted = False, # Use ACLs to control access to this module
                access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
                #module_type = None  # This item is not shown in the menu
            )),
        ("admin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                #module_type = None  # This item is handled separately for the menu
            )),
        ("appadmin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                #module_type = None  # No Menu
            )),
        ("errors", Storage(
                name_nice = T("Ticket Viewer"),
                #description = "Needed for Breadcrumbs",
                restricted = False,
                #module_type = None  # No Menu
            )),
        ("sync", Storage(
                name_nice = T("Synchronization"),
                #description = "Synchronization",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                #module_type = None  # This item is handled separately for the menu
            )),
        ("translate", Storage(
                name_nice = T("Translation Functionality"),
                #description = "Selective translation of strings based on module.",
                #module_type = None,
            )),
        # Uncomment to enable internal support requests
        ("support", Storage(
                name_nice = T("Support"),
                #description = "Support Requests",
                restricted = True,
                #module_type = None  # This item is handled separately for the menu
            )),
        ("gis", Storage(
                name_nice = T("Map"),
                #description = "Situation Awareness & Geospatial Analysis",
                restricted = True,
                #module_type = 6,     # 6th item in the menu
            )),
        ("pr", Storage(
                name_nice = T("Person Registry"),
                #description = "Central point to record details on People",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
                #module_type = 10
            )),
        ("org", Storage(
                name_nice = T("Organizations"),
                #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
                restricted = True,
                #module_type = 1
            )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
                name_nice = T("Staff"),
                #description = "Human Resources Management",
                restricted = True,
                #module_type = 2,
            )),
        ("vol", Storage(
                name_nice = T("Volunteers"),
                #description = "Human Resources Management",
                restricted = True,
                #module_type = 2,
            )),
        ("cms", Storage(
          name_nice = T("Content Management"),
          #description = "Content Management System",
          restricted = True,
          #module_type = 10,
        )),
        ("doc", Storage(
                name_nice = T("Documents"),
                #description = "A library of digital resources, such as photos, documents and reports",
                restricted = True,
                #module_type = 10,
            )),
        ("msg", Storage(
                name_nice = T("Messaging"),
                #description = "Sends & Receives Alerts via Email & SMS",
                restricted = True,
                # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
                #module_type = None,
            )),
        ("supply", Storage(
                name_nice = T("Supply Chain Management"),
                #description = "Used within Inventory Management, Request Management and Asset Management",
                restricted = True,
                #module_type = None, # Not displayed
            )),
        ("inv", Storage(
                name_nice = T("Warehouses"),
                #description = "Receiving and Sending Items",
                restricted = True,
                #module_type = 4
            )),
        ("asset", Storage(
                name_nice = T("Assets"),
                #description = "Recording and Assigning Assets",
                restricted = True,
                #module_type = 5,
            )),
        # Vehicle depends on Assets
        ("vehicle", Storage(
            name_nice = T("Vehicles"),
            #description = "Manage Vehicles",
            restricted = True,
            #module_type = 10,
        )),
        ("req", Storage(
                name_nice = T("Requests"),
                #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
                restricted = True,
                #module_type = 10,
            )),
        ("project", Storage(
                name_nice = T("Projects"),
                #description = "Tracking of Projects, Activities and Tasks",
                restricted = True,
                #module_type = 2
            )),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            #module_type = 10
        )),
        ("assess", Storage(
                name_nice = T("Assessments"),
                #description = "Create, enter, and manage surveys.",
                restricted = True,
                #module_type = 5,
            )),
        ("survey", Storage(
                name_nice = T("Assessments"),
                #description = "Create, enter, and manage surveys.",
                restricted = True,
                #module_type = 5,
            )),
        ("event", Storage(
                name_nice = T("Incidents"),
                #description = "Events",
                restricted = True,
                #module_type = 10
            )),
        ("budget", Storage(
                name_nice = T("Budgeting"),
                #description = "Allows a Budget to be drawn up",
                restricted = True,
                module_type = 10
            )),
        #("member", Storage(
        #       name_nice = T("Members"),
        #       #description = "Membership Management System",
        #       restricted = True,
        #       #module_type = 10,
        #   )),
        ("deploy", Storage(
               name_nice = T("Deployments"),
               #description = "Alerting and Deployment of Disaster Response Teams",
               restricted = True,
               #module_type = 10,
           )),
        ("sit", Storage(
                name_nice = T("Situation Reports"),
                #description = "Manages statistics",
                restricted = True,
                #module_type = None,
            )),
        ("stats", Storage(
                name_nice = T("Statistics"),
                #description = "Manages statistics",
                restricted = True,
                #module_type = None,
            )),
        ("vulnerability", Storage(
                name_nice = T("Vulnerability"),
                #description = "Manages vulnerability indicators",
                restricted = True,
                #module_type = 10,
            )),
    ])

    # -------------------------------------------------------------------------
    # Functions which are local to this Template
    # -------------------------------------------------------------------------
    def ns_only(f, required=True, updateable=True):
        """
            Function to configure an organisation_id field to be restricted to just
            an ARC Branch
        """

        # Label
        f.label = T("ARC Branch")

        # Requires
        db = current.db
        ttable = db.org_organisation_type
        try:
            type_id = db(ttable.name == "Red Cross / Red Crescent").select(ttable.id,
                                                                           limitby=(0, 1)
                                                                           ).first().id
        except:
            # No prepop done - skip (e.g. testing impacts of CSS changes in this theme)
            return

        # Filter by type
        ltable = db.org_organisation_organisation_type
        rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
        filter_opts = [row.organisation_id for row in rows]

        auth = current.auth
        s3_has_role = auth.s3_has_role
        Admin = s3_has_role("ADMIN")
        if Admin:
            parent = True
        else:
            # @ToDo: Set the represent according to whether the user can see resources of just a single NS or multiple
            # @ToDo: Consider porting this into core
            user = auth.user
            if user:
                realms = user.realms
                #delegations = user.delegations
                if realms:
                    parent = True
                else:
                    parent = False
            else:
                parent = True

        organisation_represent = current.s3db.org_OrganisationRepresent
        represent = organisation_represent(parent=parent)
        f.represent = represent

        from s3 import IS_ONE_OF
        requires = IS_ONE_OF(db, "org_organisation.id",
                             represent,
                             filterby = "id",
                             filter_opts = filter_opts,
                             updateable = updateable,
                             orderby = "org_organisation.name",
                             sort = True)
        if not required:
            from gluon import IS_EMPTY_OR
            requires = IS_EMPTY_OR(requires)
        f.requires = requires

        if parent:
            # Use hierarchy-widget
            from s3 import FS, S3HierarchyWidget
            # No need for parent in represent (it's a hierarchy view)
            node_represent = organisation_represent(parent=False)
            # Filter by type
            # (no need to exclude branches - we wouldn't be here if we didn't use branches)
            node_filter = (FS("organisation_organisation_type.organisation_type_id") == type_id)
            f.widget = S3HierarchyWidget(lookup="org_organisation",
                                         filter=node_filter,
                                         represent=node_represent,
                                         multiple=False,
                                         leafonly=False,
                                         )
        else:
            # Dropdown not Autocomplete
            f.widget = None

        # Comment
        if (Admin or s3_has_role("ORG_ADMIN")):
            # Need to do import after setting Theme
            from s3layouts import S3PopupLink
            from s3 import S3ScriptItem
            add_link = S3PopupLink(c = "org",
                                   f = "organisation",
                                   vars = {"organisation_type.name":"Red Cross / Red Crescent"},
                                   label = T("Create ARC Branch"),
                                   title = T("ARC Branch"),
                                   )
            comment = f.comment
            if not comment or isinstance(comment, S3PopupLink):
                f.comment = add_link
            elif isinstance(comment[1], S3ScriptItem):
                # Don't overwrite scripts
                f.comment[0] = add_link
            else:
                f.comment = add_link
        else:
            # Not allowed to add ARC Branch
            f.comment = ""

    # -------------------------------------------------------------------------
    def user_org_default_filter(selector, tablename=None):
        """
            Default filter for organisation_id:
            * Use the user's organisation if logged-in and associated with an
              organisation.
        """

        auth = current.auth
        user_org_id = auth.is_logged_in() and auth.user.organisation_id
        if user_org_id:
            return user_org_id
        else:
            # no default
            return {}

    # -------------------------------------------------------------------------
    def user_org_and_children_default_filter(selector, tablename=None):
        """
            Default filter for organisation_id:
            * Use the user's organisation if logged-in and associated with an
              organisation.
        """

        auth = current.auth
        user_org_id = auth.is_logged_in() and auth.user.organisation_id
        if user_org_id:
            db = current.db
            s3db = current.s3db
            otable = s3db.org_organisation
            org = db(otable.id == user_org_id).select(otable.pe_id,
                                                      limitby=(0, 1)
                                                      ).first()
            if org:
                pe_id = org.pe_id
                pe_ids = s3db.pr_get_descendants((pe_id,),
                                                 entity_types=("org_organisation",))
                rows = db(otable.pe_id.belongs(pe_ids)).select(otable.id)
                ids = [row.id for row in rows]
                ids.append(user_org_id)
                return ids
            else:
                return user_org_id
        else:
            # no default
            return {}

    # -------------------------------------------------------------------------
    def customise_asset_asset_resource(r, tablename):

        s3db = current.s3db
        table = s3db.asset_asset

        # Organisation needs to be an ARC Branch
        ns_only(table.organisation_id,
                required = True,
                )

        # Custom CRUD Form to allow ad-hoc Kits & link to Teams
        from s3 import S3SQLCustomForm, S3SQLInlineComponent
        table.kit.readable = table.kit.writable = True
        crud_form = S3SQLCustomForm("number",
                                    "type",
                                    "item_id",
                                    "organisation_id",
                                    "site_id",
                                    "kit",
                                    # If not ad-hoc Kit
                                    "sn",
                                    "supply_org_id",
                                    "purchase_date",
                                    "purchase_price",
                                    "purchase_currency",
                                    # If ad-hoc Kit
                                    S3SQLInlineComponent(
                                        "item",
                                        label = T("Items"),
                                        fields = ["item_id",
                                                  "quantity",
                                                  "sn",
                                                  # These are too wide for the screen & hence hide the AddResourceLinks
                                                  #"supply_org_id",
                                                  #"purchase_date",
                                                  #"purchase_price",
                                                  #"purchase_currency",
                                                  "comments",
                                                  ],
                                        ),
                                    S3SQLInlineComponent(
                                        "group",
                                        label = T("Team"),
                                        fields = [("", "group_id")],
                                        filterby = dict(field = "group_type",
                                                        options = 3
                                                        ),
                                        multiple = False,
                                        ),
                                    "comments",
                                    )

        from s3 import S3OptionsFilter
        filter_widgets = s3db.get_config(tablename, "filter_widgets")
        filter_widgets.insert(-2, S3OptionsFilter("group.group_id",
                                                  label = T("Team"),
                                                  represent = "%(name)s",
                                                  hidden = True,
                                                  ))

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

        if r.representation == "geojson":
            from s3 import S3Represent
            s3db.vehicle_vehicle.vehicle_type_id.represent = S3Represent(lookup="vehicle_vehicle_type",
                                                                         fields=("code",))

    settings.customise_asset_asset_resource = customise_asset_asset_resource

    # -------------------------------------------------------------------------
    def customise_cms_post_resource(r, tablename):

        s3db = current.s3db
        table = s3db.cms_post
        table.title.comment = None
        s3db.cms_post_organisation.organisation_id.represent = \
                                    s3db.org_OrganisationRepresent(acronym=False)

        if r.function == "newsfeed":
            # Inject Bootstrap JS for the attachments dropdown menu
            s3 = current.response.s3
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/bootstrap.js" % r.application)
            elif s3.cdn:
                s3.scripts.append("http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/js/bootstrap.min.js")
            else:
                s3.scripts.append("/%s/static/scripts/bootstrap.min.js" % r.application)

        elif r.representation == "plain":
            # Map Popups
            table.location_id.represent = s3db.gis_LocationRepresent(sep=" | ")
            from s3 import s3_auth_user_represent_name
            table.created_by.represent = s3_auth_user_represent_name
            # Used by default popups
            series = table.series_id.represent(r.record.series_id)
            current.response.s3.crud_strings["cms_post"].title_display = "%(series)s Details" % dict(series=series)
            s3db.configure("cms_post",
                           popup_url="",
                           )
            table.avatar.readable = False
            table.body.label = ""
            table.expired.readable = False
            table.replies.readable = False
            table.created_by.readable = True
            table.created_by.label = T("Author")
            # Used by cms_post_popup
            #table.created_on.represent = datetime_represent

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -------------------------------------------------------------------------
    def cms_post_popup(r, output):
        """
            Customised Map popup for cms_post resource
            - include Photo if-present

            @ToDo: Much better checking!
        """

        doc_id = r.record.doc_id
        table = current.s3db.doc_document
        query = (table.deleted == False) & \
                (table.doc_id == doc_id)
        row = current.db(query).select(table.file,
                                       limitby=(0, 1)
                                       ).first()
        if row and row.file:
            from gluon import IMG, URL
            image = IMG(_src=URL(c="default", f="download", args=[row.file]))
            output["image"] = image

    # -------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.representation == "plain":
                # Map Popups
                cms_post_popup(r, output)

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller

    # -------------------------------------------------------------------------
    def customise_cr_shelter_controller(**attr):

        # Default Filter
        # Org and all Branches & SubBranches
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_and_children_default_filter,
                              tablename = "cr_shelter")

        s3db = current.s3db
        field = s3db.cr_shelter.shelter_type_id
        field.readable = field.writable = False
        list_fields = s3db.get_config("cr_shelter", "list_fields")
        list_fields.remove("shelter_type_id")

        return attr

    settings.customise_cr_shelter_controller = customise_cr_shelter_controller

    # -------------------------------------------------------------------------
    def customise_deploy_assignment_controller(**attr):

        s3db = current.s3db

        # Labels
        #table = s3db.deploy_assignment
        #table.job_title_id.label = T("RDRT Type")
        #table.start_date.label = T("Deployment Date")
        #table.end_date.label = T("EOM")

        # List fields
        list_fields = [(T("Mission"), "mission_id$name"),
                       (T("Appeal Code"), "mission_id$code"),
                       (T("Country"), "mission_id$location_id"),
                       (T("Incident Type"), "mission_id$event_type_id"),
                       # @todo: replace by date of first alert?
                       (T("Date"), "mission_id$created_on"),
                       "job_title_id",
                       #(T("Member"), "human_resource_id$person_id"),
                       (T("Member"), "human_resource_id$person_id"),
                       (T("Deploying Branch"), "human_resource_id$organisation_id"),
                       "start_date",
                       "end_date",
                       "appraisal.rating",
                       # @todo: Comments of the mission (=>XLS only)
                      ]

        # Report options
        report_fact = [(T("Number of Deployments"), "count(human_resource_id)"),
                       (T("Average Rating"), "avg(appraisal.rating)"),
                       ]
        report_axis = [(T("Appeal Code"), "mission_id$code"),
                       (T("Country"), "mission_id$location_id"),
                       (T("Incident Type"), "mission_id$event_type_id"),
                       "job_title_id",
                       (T("Deploying Branch"), "human_resource_id$organisation_id"),
                      ]
        report_options = Storage(
            rows=report_axis,
            cols=report_axis,
            fact=report_fact,
            defaults=Storage(rows="mission_id$location_id",
                             cols="mission_id$event_type_id",
                             fact="count(human_resource_id)",
                             totals=True
                             )
            )

        s3db.configure("deploy_assignment",
                       list_fields = list_fields,
                       report_options = report_options,
                       )

        return attr

    settings.customise_deploy_assignment_controller = customise_deploy_assignment_controller

    # -------------------------------------------------------------------------
    def customise_deploy_mission_controller(**attr):

        s3db = current.s3db

        table = s3db.deploy_mission
        table.code.label = T("Appeal Code")
        table.event_type_id.label = T("Incident Type")
        table.organisation_id.readable = table.organisation_id.writable = False

        # Report options
        report_fact = [(T("Number of Missions"), "count(id)"),
                       (T("Number of Countries"), "count(location_id)"),
                       (T("Number of Incident Types"), "count(event_type_id)"),
                       (T("Number of Responses"), "sum(response_count)"),
                       (T("Number of Deployments"), "sum(hrquantity)"),
                      ]
        report_axis = ["code",
                       "location_id",
                       "event_type_id",
                       "status",
                       ]
        report_options = Storage(rows = report_axis,
                                 cols = report_axis,
                                 fact = report_fact,
                                 defaults = Storage(rows = "location_id",
                                                    cols = "event_type_id",
                                                    fact = "sum(hrquantity)",
                                                    totals = True,
                                                    ),
                                 )

        s3db.configure("deploy_mission",
                       report_options = report_options,
                       )

        return attr

    settings.customise_deploy_mission_controller = customise_deploy_mission_controller

    # -------------------------------------------------------------------------
    def customise_doc_sitrep_controller(**attr):

        # Default Filter
        # Org and all Branches & SubBranches
        # @ToDo: Only look at current level + 1 level down
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_and_children_default_filter,
                              tablename = "doc_sitrep")

        # @ToDo: Pick this up in request.post_vars along with 'selected'
        dt_bulk_actions = [(T("Consolidate"), "consolidate")]

        attr["dtargs"] = dict(dt_bulk_actions=dt_bulk_actions)
        return attr

    settings.customise_doc_sitrep_controller = customise_doc_sitrep_controller

    # -------------------------------------------------------------------------
    #def customise_event_incident_resource(r, tablename):

    #    # Use Polygons for Location
    #    field = current.s3db.event_incident.location_id

    #settings.customise_event_incident_resource = customise_event_incident_resource

    # -------------------------------------------------------------------------
    def poi_marker_fn(record):
        """
            Function to decide which Marker to use for PoI KML export
            - unused currently
        """

        db = current.db
        table = db.gis_poi_type
        ptype = db(table.id == record.poi_type_id).select(table.name,
                                                          limitby=(0, 1)
                                                          ).first()
        if ptype:
            marker = "ARC/%s.png" % ptype.name.replace(" ", "_")
        else:
            # Fallback
            marker = "marker_red.png"

        return Storage(image = marker)

    # -------------------------------------------------------------------------
    def customise_gis_poi_resource(r, tablename):

        #if r.representation == "kml":
        #    # Custom Marker function
        #    current.s3db.configure("gis_poi",
        #                           marker_fn = poi_marker_fn,
        #                           )
        if current.request.get_vars.get("wkt"):
            # Hide Lat/Lon
            script = """$('#gis_poi_location_id_lat1,#gis_poi_location_id_lat,#gis_poi_location_id_lon1,#gis_poi_location_id_lon').hide()"""
            current.response.s3.jquery_ready.append(script)
            # Type is Feeding Route
            s3db = current.s3db
            table = s3db.gis_poi_type
            poi_type = current.db(table.name == "Feeding Route").select(table.id,
                                                                        limitby=(0, 1)
                                                                        ).first()
            if poi_type:
                field = s3db.gis_poi.poi_type_id
                field.default = poi_type.id
                field.readable = field.writable = False

    settings.customise_gis_poi_resource = customise_gis_poi_resource

    # -------------------------------------------------------------------------
    def customise_hrm_certificate_controller(**attr):

        # Organisation needs to be an ARC Branch
        ns_only(current.s3db.hrm_certificate.organisation_id,
                required = False,
                )

        return attr

    settings.customise_hrm_certificate_controller = customise_hrm_certificate_controller

    # -------------------------------------------------------------------------
    def customise_hrm_course_controller(**attr):

        s3db = current.s3db
        table = s3db.hrm_course
        tablename = "hrm_course"

        # Organisation needs to be an ARC Branch
        ns_only(table.organisation_id,
                required = False,
                )

        list_fields = ["code",
                       "name",
                       "organisation_id",
                       (T("Sectors"), "course_sector.sector_id"),
                       ]

        from s3 import S3SQLCustomForm, S3SQLInlineLink
        crud_form = S3SQLCustomForm("code",
                                    "name",
                                    "organisation_id",
                                    S3SQLInlineLink("sector",
                                                    field = "sector_id",
                                                    label = T("Sectors"),
                                                    ),
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

        return attr

    settings.customise_hrm_course_controller = customise_hrm_course_controller

    # -------------------------------------------------------------------------
    def customise_hrm_credential_controller(**attr):

        # Currently just used by RDRT
        table = current.s3db.hrm_credential
        field = table.job_title_id
        field.comment = None
        field.label = T("Sector")
        from s3 import IS_ONE_OF
        field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                                   field.represent,
                                   filterby = "type",
                                   filter_opts = (4,),
                                   )
        table.organisation_id.readable = table.organisation_id.writable = False
        table.performance_rating.readable = table.performance_rating.writable = False
        table.start_date.readable = table.start_date.writable = False
        table.end_date.readable = table.end_date.writable = False

        return attr

    settings.customise_hrm_credential_controller = customise_hrm_credential_controller

    # -------------------------------------------------------------------------
    def customise_hrm_department_controller(**attr):

        # Organisation needs to be an ARC Branch
        ns_only(current.s3db.hrm_department.organisation_id,
                required = False,
                )

        return attr

    settings.customise_hrm_department_controller = customise_hrm_department_controller

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_and_children_default_filter,
                              tablename = "hrm_human_resource")

        #s3db = current.s3db
        #s3db.org_organisation.root_organisation.label = T("National Society")

        # Organisation needs to be an ARC Branch
        #ns_only(s3db.hrm_human_resource.organisation_id,
        #        required = True,
        #        )

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            from s3 import S3OptionsFilter
            filter_widgets = current.s3db.get_config("hrm_human_resource", "filter_widgets")
            filter_widgets.insert(-1, S3OptionsFilter("training.course_id$course_sector.sector_id",
                                                      label = T("Training Sector"),
                                                      hidden = True,
                                                      ))

            if r.controller == "deploy":

                # Custom profile widgets for hrm_competency ("skills"):
                from s3 import FS
                subsets = (("Computer", "Computer Skills"),
                           ("Language", "Language Skills"),
                           )
                widgets = []
                profile_widgets = r.resource.get_config("profile_widgets")
                while profile_widgets:
                    widget = profile_widgets.pop(0)
                    if widget["tablename"] == "hrm_competency":
                        for skill_type, label in subsets:
                            query = widget["filter"] & \
                                    (FS("skill_id$skill_type_id$name") == skill_type)
                            new_widget = dict(widget)
                            new_widget["label"] = label
                            new_widget["filter"] = query
                            widgets.append(new_widget)
                        break
                    else:
                        widgets.append(widget)
                if profile_widgets:
                    widgets.extend(profile_widgets)

                # Custom list fields for RDRT
                phone_label = settings.get_ui_label_mobile_phone()
                list_fields = ["person_id",
                               "organisation_id",
                               "type",
                               "job_title_id",
                               (T("Email"), "email.value"),
                               (phone_label, "phone.value"),
                               "person_id$gender",
                               (T("Passport Number"), "person_id$passport.value"),
                               (T("Passport Expires"), "person_id$passport.valid_until"),
                               (T("Sectors"), "credential.job_title_id"),
                               (T("Trainings"), "training.course_id"),
                               # @todo: Languages (once implemented)
                               ]
                r.resource.configure(list_fields = list_fields,
                                     profile_widgets = widgets,
                                     )
            return True
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if isinstance(output, dict):
                if r.controller == "deploy" and \
                   "title" in output:
                    output["title"] = T("Damage Assessment Team Members")

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_hrm_job_title_controller(**attr):

        s3 = current.response.s3
        table = current.s3db.hrm_job_title
        controller = current.request.controller
        if controller == "deploy":
            # Filter to just deployables
            s3.filter = (table.type == 4)
        else:
            # Organisation needs to be an ARC Branch
            ns_only(table.organisation_id,
                    required = False,
                    )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if controller == "deploy":
                field = table.type
                field.default = 4
                field.readable = field.writable = False
                table.organisation_id.readable = False
                table.organisation_id.writable = False

                #help = T("If you don't see the Sector in the list, you can add a new one by clicking link 'Create Sector'.")
                s3.crud_strings["hrm_job_title"] = Storage(
                    label_create=T("Create Sector"),
                    title_display=T("Sector Details"),
                    title_list=T("Sectors"),
                    title_update=T("Edit Sector"),
                    label_list_button=T("List Sectors"),
                    label_delete_button=T("Delete Sector"),
                    msg_record_created=T("Sector added"),
                    msg_record_modified=T("Sector updated"),
                    msg_record_deleted=T("Sector deleted"),
                    msg_list_empty=T("No Sectors currently registered"))

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

    # -------------------------------------------------------------------------
    def customise_hrm_programme_controller(**attr):

        # Organisation needs to be an ARC Branch
        ns_only(current.s3db.hrm_programme.organisation_id,
                required = False,
                )

        return attr

    settings.customise_hrm_programme_controller = customise_hrm_programme_controller

    # -------------------------------------------------------------------------
    def customise_hrm_programme_hours_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.person_id$human_resource.organisation_id",
                              user_org_default_filter,
                              tablename = "hrm_programme_hours")

        return attr

    settings.customise_hrm_programme_hours_controller = customise_hrm_programme_hours_controller

    # -------------------------------------------------------------------------
    def customise_hrm_training_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.person_id$human_resource.organisation_id",
                              user_org_default_filter,
                              tablename = "hrm_training")

        return attr

    settings.customise_hrm_training_controller = customise_hrm_training_controller

    # --------------------------------------------------------------------------
    #def customise_member_membership_resource(r, resource):

    #    # Organisation needs to be an ARC Branch
    #    ns_only(current.s3db.member_membership.organisation_id,
    #            required = True,
    #            )

    #settings.customise_member_membership_resource = customise_member_membership_resource

    # -------------------------------------------------------------------------
    #def customise_member_membership_type_resource(r, tablename):

    #    # Organisation needs to be an ARC Branch
    #    ns_only(current.s3db.member_membership_type.organisation_id,
    #            required = False,
    #            )

    #settings.customise_member_membership_type_resource = customise_member_membership_type_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        # Organisation needs to be an ARC Branch
        #ns_only(current.s3db.org_office.organisation_id,
        #        required = True,
        #        )

        if r.representation == "plain":
            # Shorter version fits popup better
            current.s3db.gis_location.addr_street.label = T("Address")

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_office_resource(r, tablename):

        # Organisation needs to be an ARC Branch
        #ns_only(current.s3db.org_office.organisation_id,
        #        required = True,
        #        )
        pass

    #settings.customise_org_office_resource = customise_org_office_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if not r.component or r.component_name == "branch":
                field = r.table.region_id
                field.label = T("State")
                field.comment = None # Don't Add

                if r.interactive or r.representation == "aadata":
                    s3db = current.s3db
                    #s3db.pr_contact.id.represent = s3db.pr_contact_represent
                    list_fields = ["name",
                                   "acronym",
                                   "organisation_organisation_type.organisation_type_id",
                                   #"country",
                                   "website",
                                   #(T("Facebook"), "facebook.id"),
                                   #(T("Twitter"), "twitter.id"),
                                   (T("Facebook"), "facebook.value"),
                                   (T("Twitter"), "twitter.value"),
                                   ]

                    type_filter = r.get_vars.get("organisation_type.name",
                                                 None)
                    type_label = T("Type")
                    if type_filter:
                        type_names = type_filter.split(",")
                        if len(type_names) == 1:
                            # Strip Type from list_fields
                            list_fields.remove("organisation_organisation_type.organisation_type_id")
                            type_label = ""

                    s3db.configure("org_organisation",
                                   list_fields = list_fields,
                                   )

                    if r.interactive:
                        r.table.country.label = T("Country")
                        from s3 import S3SQLCustomForm, S3SQLInlineLink, S3SQLInlineComponent
                        crud_form = S3SQLCustomForm(
                            "name",
                            "acronym",
                            S3SQLInlineLink("organisation_type",
                                            field = "organisation_type_id",
                                            label = type_label,
                                            multiple = False,
                                            #widget = "hierarchy",
                                            ),
                            #"country",
                            "region_id",
                            "phone",
                            "website",
                            S3SQLInlineComponent(
                                "contact",
                                name = "facebook",
                                label = T("Facebook"),
                                multiple = False,
                                fields = [("", "value")],
                                filterby = dict(field = "contact_method",
                                                options = "FACEBOOK"
                                                )
                            ),
                            S3SQLInlineComponent(
                                "contact",
                                name = "twitter",
                                label = T("Twitter"),
                                multiple = False,
                                fields = [("", "value")],
                                filterby = dict(field = "contact_method",
                                                options = "TWITTER"
                                                )
                            ),
                            "logo",
                            "comments",
                            )
                        s3db.configure("org_organisation",
                                       crud_form = crud_form,
                                       )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_pr_group_controller(**attr):

        # Organisation needs to be an ARC Branch
        ns_only(current.s3db.org_organisation_team.organisation_id,
                required = False,
                )

        return attr

    settings.customise_pr_group_controller = customise_pr_group_controller

    # =========================================================================
    def vol_active(person_id):
        """
            Whether a Volunteer counts as 'Active' based on the number of hours
            they've done (both Trainings & Programmes) per month, averaged over
            the last year.
            If nothing recorded for the last 3 months, don't penalise as assume
            that data entry hasn't yet been done.

            @ToDo: This should be based on the HRM record, not Person record
                   - could be active with Org1 but not with Org2
            @ToDo: allow to be calculated differently per-Org
        """

        now = current.request.utcnow

        # Time spent on Programme work
        htable = current.s3db.hrm_programme_hours
        query = (htable.deleted == False) & \
                (htable.person_id == person_id) & \
                (htable.date != None)
        programmes = current.db(query).select(htable.hours,
                                              htable.date,
                                              orderby=htable.date)
        if programmes:
            # Ignore up to 3 months of records
            three_months_prior = (now - timedelta(days=92))
            end = max(programmes.last().date, three_months_prior.date())
            last_year = end - timedelta(days=365)
            # Is this the Volunteer's first year?
            if programmes.first().date > last_year:
                # Only start counting from their first month
                start = programmes.first().date
            else:
                # Start from a year before the latest record
                start = last_year

            # Total hours between start and end
            programme_hours = 0
            for programme in programmes:
                if programme.date >= start and programme.date <= end and programme.hours:
                    programme_hours += programme.hours

            # Average hours per month
            months = max(1, (end - start).days / 30.5)
            average = programme_hours / months

            # Active?
            if average >= 8:
                return True
            else:
                return False
        else:
            return False

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db

        if current.request.controller == "deploy":
            # Replace default title in imports:
            attr["retitle"] = lambda r: {"title": T("Import Members")} \
                                if r.method == "import" else None

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            component_name = r.component_name
            if component_name == "appraisal":
                atable = r.component.table
                atable.organisation_id.readable = atable.organisation_id.writable = False
                # Organisation needs to be an NS
                #ns_only(atable.organisation_id,
                #        required = True,
                #        )
                field = atable.supervisor_id
                field.readable = field.writable = False
                field = atable.job_title_id
                field.comment = None
                field.label = T("Sector") # RDRT-specific
                from s3 import IS_ONE_OF
                field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                                           field.represent,
                                           filterby = "type",
                                           filter_opts = (4,),
                                           )
            elif r.method =="record" or component_name == "human_resource":
                # Organisation needs to be an ARC Branch
                ns_only(s3db.hrm_human_resource.organisation_id,
                        required = True,
                        )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    # Projects
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    #settings.project.mode_3w = True
    # Uncomment this to use settings suitable for detailed Task management
    settings.project.mode_task = True
    # Uncomment this to use Codes for projects
    settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    #settings.project.community = True
    # Uncomment this to enable Hazards in 3W projects
    #settings.project.hazards = True
    # Uncomment this to enable Milestones in projects
    settings.project.milestones = True
    # Uncomment this to use multiple Budgets per project
    #settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Uncomment this to enable Themes in 3W projects
    #settings.project.themes = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Lead Organization"),
        2: T("Partner"),
        3: T("Donor"),
        #4: T("Customer"), # T("Beneficiary")?
        5: T("Supplier"),
        #9: T("Partner National Society"),
    }
    settings.project.task_status_opts = {1: T("Draft"),
                                         2: T("New"),
                                         3: T("Assigned"),
                                         #4: T("Feedback"),
                                         4: T("Accepted"),
                                         5: T("Blocked"),
                                         6: T("On Hold"),
                                         7: T("Canceled"),
                                         8: T("Duplicate"),
                                         9: T("Ready"),
                                        10: T("Verified"),
                                        11: T("Reopened"),
                                        12: T("Completed"),
                                        }

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_default_filter,
                              tablename = "project_project")

        s3db = current.s3db
        tablename = "project_project"
        # Load normal model
        table = s3db[tablename]

        # @ToDo: S3SQLInlineComponent for Project orgs
        # Get IDs for PartnerNS/Partner-Donor
        # db = current.db
        # ttable = db.org_organisation_type
        # rows = db(ttable.deleted != True).select(ttable.id,
        #                                          ttable.name,
        #                                          )
        # rc = []
        # not_rc = []
        # nappend = not_rc.append
        # for row in rows:
            # if row.name == "Red Cross / Red Crescent":
                # rc.append(row.id)
            # elif row.name == "Supplier":
                # pass
            # else:
                # nappend(row.id)

        # Custom Fields
        # Organisation needs to be an NS (not a branch)
        f = table.organisation_id
        ns_only(f,
                required = True,
                )
        f.label = T("Lead Organization")

        # Custom Crud Form
        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
        crud_form = S3SQLCustomForm(
            "organisation_id",
            "name",
            "code",
            "description",
            "status_id",
            "start_date",
            "end_date",
            #S3SQLInlineComponent(
            #    "location",
            #    label = T("Countries"),
            #    fields = ["location_id"],
            #),
            # Outputs
            S3SQLInlineComponent(
                "output",
                label = T("Outputs"),
                #comment = "Bob",
                fields = ["name", "status"],
            ),
            S3SQLInlineLink(
                "hazard",
                label = T("Hazards"),
                field = "hazard_id",
                cols = 4,
                translate = True,
            ),
            S3SQLInlineLink(
                "sector",
                label = T("Sectors"),
                field = "sector_id",
                cols = 4,
                translate = True,
                #widget = "groupedopts",
            ),
            S3SQLInlineLink(
                "theme",
                label = T("Themes"),
                field = "theme_id",
                cols = 4,
                translate = True,
                # Filter Theme by Sector
                filterby = "theme_id:project_theme_sector.sector_id",
                match = "sector_project.sector_id",
                script = '''
    $.filterOptionsS3({
      'trigger':{'alias':'sector','name':'sector_id','inlineType':'link'},
      'target':{'alias':'theme','name':'theme_id','inlineType':'link'},
      'lookupPrefix':'project',
      'lookupResource':'theme',
      'lookupKey':'theme_id:project_theme_sector.sector_id',
      'showEmptyField':false
    })'''
            ),
            #"drr.hfa",
            "objectives",
            "human_resource_id",
            # Disabled since we need organisation_id filtering to either organisation_type_id == RC or NOT
            # & also hiding Branches from RCs
            # & also rewriting for organisation_type_id via link table
            # Partner NS
            # S3SQLInlineComponent(
                # "organisation",
                # name = "partnerns",
                # label = T("Partner National Societies"),
                # fields = ["organisation_id",
                          # "comments",
                          # ],
                # Filter Organisation by Type
                # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                              # "filterfor": rc,
                                              # }],
                # filterby = dict(field = "role",
                                # options = [9])
            # ),
            # Partner Orgs
            # S3SQLInlineComponent(
                # "organisation",
                # name = "partner",
                # label = T("Partner Organizations"),
                # fields = ["organisation_id",
                          # "comments",
                          # ],
                # Filter Organisation by Type
                # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                              # "filterfor": not_rc,
                                              # }],
                # filterby = dict(field = "role",
                                # options = [2])
            # ),
            # Donors
            # S3SQLInlineComponent(
                # "organisation",
                # name = "donor",
                # label = T("Donor(s)"),
                # fields = ["organisation_id",
                          # "amount",
                          # "currency"],
                # Filter Organisation by Type
                # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                              # "filterfor": not_rc,
                                              # }],
                # filterby = dict(field = "role",
                                # options = [3])
            # ),
            #"budget",
            #"currency",
            "comments",
        )

        # Set the Host NS filter as Visible so that the default filter works
        filter_widgets = s3db.get_config(tablename, "filter_widgets")
        for widget in filter_widgets:
            if widget.field == "organisation_id":
                widget.opts.hidden = False
                break

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # -------------------------------------------------------------------------
    def customise_project_beneficiary_resource(r, tablename):
        """
            Link Project Beneficiaries to Activity Type
        """

        if r.interactive and r.component:
            if r.tablename == "project_project":
                # We are a component of the Project
                project_id = r.id
            elif r.tablename == "project_location":
                # We are a component of the Project Location
                project_id = r.record.project_id
            else:
                # Unknown!
                return

            db = current.db
            s3db = current.s3db

            # Filter Activity Type by Sector
            ltable = s3db.project_sector_project
            rows = db(ltable.project_id == project_id).select(ltable.sector_id)
            sectors = [row.sector_id for row in rows]
            ltable = s3db.project_activity_type_sector
            rows = db(ltable.sector_id.belongs(sectors)).select(ltable.activity_type_id)
            filteropts = [row.activity_type_id for row in rows]

            def postprocess(form):
                # Update project_location.activity_type
                beneficiary_id = form.vars.get("id", None)
                table = db.project_beneficiary
                row = db(table.id == beneficiary_id).select(table.project_location_id,
                                                            limitby = (0, 1)
                                                            ).first()
                if not row:
                    return
                project_location_id = row.project_location_id
                if not project_location_id:
                    return
                ltable = db.project_beneficiary_activity_type
                row = db(ltable.beneficiary_id == beneficiary_id).select(ltable.activity_type_id,
                                                                         limitby = (0, 1)
                                                                         ).first()
                if not row:
                    return
                activity_type_id = row.activity_type_id
                ltable = s3db.project_activity_type_location
                query = (ltable.project_location_id == project_location_id) & \
                        (ltable.activity_type_id == activity_type_id)
                exists = db(query).select(ltable.id,
                                          limitby = (0, 1)
                                          ).first()
                if not exists:
                    ltable.insert(project_location_id = project_location_id,
                                  activity_type_id = activity_type_id,
                                  )

            from s3 import S3SQLCustomForm, S3SQLInlineLink
            crud_form = S3SQLCustomForm(#"project_id",
                                        "project_location_id",
                                        S3SQLInlineLink("activity_type",
                                                        field = "activity_type_id",
                                                        filterby = "id",
                                                        options = filteropts,
                                                        label = T("Activity Type"),
                                                        multiple = False,
                                                        ),
                                        "parameter_id",
                                        "value",
                                        "date",
                                        "end_date",
                                        "comments",
                                        postprocess = postprocess,
                                        )

            s3db.configure(tablename,
                           crud_form = crud_form,
                           )

        elif not r.component:
            # Report
            from s3 import S3OptionsFilter
            resource = r.resource
            filter_widgets = resource.get_config("filter_widgets")
            filter_widgets.insert(1,
                S3OptionsFilter("beneficiary_activity_type.activity_type_id",
                                label = T("Activity Type"),
                                ))
            report_options = resource.get_config("report_options")
            report_options.rows.append("beneficiary_activity_type.activity_type_id")
            # Same object so would be added twice
            #report_options.cols.append("beneficiary_activity_type.activity_type_id")

            resource.configure(filter_widgets = filter_widgets,
                               report_options = report_options,
                               )


    settings.customise_project_beneficiary_resource = customise_project_beneficiary_resource

    # -------------------------------------------------------------------------
    def customise_project_location_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponentCheckbox
        crud_form = S3SQLCustomForm(
            "project_id",
            "location_id",
            # @ToDo: Grouped Checkboxes
            S3SQLInlineComponentCheckbox(
                "activity_type",
                label = T("Activity Types"),
                field = "activity_type_id",
                cols = 3,
                # Filter Activity Type by Sector
                filter = {"linktable": "project_activity_type_sector",
                          "lkey": "activity_type_id",
                          "rkey": "sector_id",
                          "lookuptable": "project_project",
                          "lookupkey": "project_id",
                          },
                translate = True,
                ),
            "comments",
            )

        current.s3db.configure(tablename,
                               crud_form = crud_form,
                               )

    settings.customise_project_location_resource = customise_project_location_resource

    # -------------------------------------------------------------------------
    # Inventory Management
    settings.inv.show_mode_of_transport = True
    settings.inv.send_show_time_in = True
    #settings.inv.collapse_tabs = True
    # Uncomment if you need a simpler (but less accountable) process for managing stock levels
    settings.inv.direct_stock_edits = True

    # -------------------------------------------------------------------------
    # Request Management
    # Uncomment to disable Inline Forms in Requests module
    settings.req.inline_forms = False
    #settings.req.prompt_match = False
    settings.req.req_type = ["Stock"]
    settings.req.use_commit = False
    # Should Requests ask whether Transportation is required?
    settings.req.ask_transport = True

    # -------------------------------------------------------------------------
    def customise_req_commit_resource(r, tablename):

        # Request is mandatory
        field = current.s3db.req_commit.req_id
        field.requires = field.requires.other

    settings.customise_req_commit_resource = customise_req_commit_resource

    # -------------------------------------------------------------------------
    def customise_survey_complete_resource(r, tablename):

        if r.representation == "iframe":
            # Use a custom Theme more suited to Mobile
            # Doesn't work with Survey
            #settings.base.theme = "bootstrap"
            # Ensure the form is visible
            script = """$('#popup form').show()"""
            current.response.s3.jquery_ready.append(script)

    settings.customise_survey_complete_resource = customise_survey_complete_resource

# END =========================================================================