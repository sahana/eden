# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for IFRC's Resource Management System
        - Americas Zone

        http://eden.sahanafoundation.org/wiki/Deployments/IFRC
    """

    T = current.T

    # -----------------------------------------------------------------------------
    # System Name
    #
    settings.base.system_name = T("Resource Management System")
    settings.base.system_name_short = T("RMS")

    # -----------------------------------------------------------------------------
    # Pre-Populate
    #
    settings.base.prepopulate = ("RMSAmericas", "RMSAmericas/Demo")

    # -----------------------------------------------------------------------------
    # Theme (folder to use for views/layout.html)
    #
    settings.base.theme = "RMSAmericas"

    # Uncomment to disable responsive behavior of datatables
    #settings.ui.datatables_responsive = False

    # Uncomment to show a default cancel button in standalone create/update forms
    settings.ui.default_cancel_button = True

    # @todo: configure custom icons
    #settings.ui.custom_icons = {
    #    "male": "icon-male",
    #    "female": "icon-female",
    #    "medical": "icon-plus-sign-alt",
    #}

    # =============================================================================
    # System Settings
    # -----------------------------------------------------------------------------
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
                                               #"member": T("Member")
                                               }

    settings.auth.record_approval = True

    # @ToDo: Should we fallback to organisation_id if site_id is None?
    settings.auth.registration_roles = {"site_id": ["reader",
                                                    ],
                                        }

    # Owner Entity
    settings.auth.person_realm_human_resource_site_then_org = True
    settings.auth.person_realm_member_org = True

    # Activate entity role manager tabs for OrgAdmins
    settings.auth.entity_role_manager = True

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
                         #"member_membership_type",
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
        realm_entity_fks = dict(pr_contact = [("org_organisation", EID),
                                              #("po_household", EID),
                                              ("pr_person", EID),
                                              ],
                                pr_contact_emergency = EID,
                                pr_physical_description = EID,
                                pr_address = [("org_organisation", EID),
                                              ("pr_person", EID),
                                              ],
                                pr_image = EID,
                                pr_identity = PID,
                                pr_education = PID,
                                pr_note = PID,
                                hrm_human_resource = SID,
                                hrm_training = PID,
                                inv_recv = SID,
                                inv_send = SID,
                                inv_track_item = "track_org_id",
                                inv_adj_item = "adj_id",
                                req_req_item = "req_id",
                                #po_household = "area_id",
                                #po_organisation_area = "area_id",
                                )

        # Default Foreign Keys (ordered by priority)
        default_fks = (#"household_id",
                       "catalog_id",
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
        fks = [fk] if not isinstance(fk, list) else list(fk)
        fks.extend(default_fks)
        for default_fk in fks:
            if isinstance(default_fk, tuple):
                instance_type, fk = default_fk
            else:
                instance_type, fk = None, default_fk
            if fk not in table.fields:
                continue

            # Inherit realm_entity from parent record
            if fk == EID:
                if instance_type:
                    ftable = s3db.table(instance_type)
                    if not ftable:
                        continue
                else:
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
        #use_user_root_organisation = False
        # Suppliers & Partners are owned by the user's organisation
        if realm_entity == 0 and tablename == "org_organisation":
            ottable = s3db.org_organisation_type
            ltable = db.org_organisation_organisation_type
            query = (ltable.organisation_id == row.id) & \
                    (ltable.organisation_type_id == ottable.id)
            otype = db(query).select(ottable.name,
                                     limitby=(0, 1)).first()
            if not otype or otype.name != "Red Cross / Red Crescent":
                use_user_organisation = True

        # Facilities & Requisitions are owned by the user's organisation
        elif tablename in ("org_facility", "req_req"):
            use_user_organisation = True

        elif tablename == "hrm_training":
            # Inherit realm entity from the related HR record
            htable = s3db.hrm_human_resource
            query = (table.id == row.id) & \
                    (htable.person_id == table.person_id) & \
                    (htable.deleted != True)
            rows = db(query).select(htable.realm_entity, limitby=(0, 2))
            if len(rows) == 1:
                realm_entity = rows.first().realm_entity
            else:
                # Ambiguous => try course organisation
                ctable = s3db.hrm_course
                otable = s3db.org_organisation
                query = (table.id == row.id) & \
                        (ctable.id == table.course_id) & \
                        (otable.id == ctable.organisation_id)
                row = db(query).select(otable.pe_id,
                                       limitby=(0, 1)).first()
                if row:
                    realm_entity = row.pe_id
                # otherwise: inherit from the person record

        # Groups are owned by the user's organisation
        #elif tablename in ("pr_group",):
        elif tablename == "pr_group":
            use_user_organisation = True

        auth = current.auth
        user = auth.user
        if user:
            if use_user_organisation:
                # @ToDo - this might cause issues if the user's org is different from the realm that gave them permissions to create the Org
                realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                 user.organisation_id)
            #elif use_user_root_organisation:
            #    realm_entity = s3db.pr_get_pe_id("org_organisation",
            #                                     auth.root_org())
        return realm_entity

    settings.auth.realm_entity = ifrc_realm_entity

    # -----------------------------------------------------------------------------
    # L10n (Localization) settings
    #
    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("es", "Español"),
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
    # Unsortable 'pretty' date format (for use in English)
    settings.L10n.date_format = "%d-%b-%Y"
    # Make last name in person/user records mandatory
    #settings.L10n.mandatory_lastname = True
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this for Alternate Location Names
    settings.L10n.name_alt_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True

    # Names of Orgs with specific settings
    HNRC = "Honduran Red Cross"

    # -----------------------------------------------------------------------------
    # Finance settings
    #
    def currencies(default):
        """ RMS- and NS-specific currencies (lazy setting) """

        # Currencies that are common for all NS
        currencies = {"EUR" : T("Euros"),
                      "CHF" : T("Swiss Francs"),
                      "USD" : T("United States Dollars"),
                      }

        # NS-specific currencies
        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            currencies["HNL"] = T("Honduran Lempira")
        return currencies

    settings.fin.currencies = currencies

    def currency_default(default):
        """ NS-specific default currencies (lazy setting) """

        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            default = "HNL"
        #else:
        #    default = "USD"
        return default

    settings.fin.currency_default = currency_default

    # -----------------------------------------------------------------------------
    # Map Settings

    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = True

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

    # GeoNames username
    settings.gis.geonames_username = "rms_dev"

    # -----------------------------------------------------------------------------
    # Use the label 'Camp' instead of 'Shelter'
    #
    settings.ui.camp = True

    # -----------------------------------------------------------------------------
    # Filter Manager
    #
    #settings.search.filter_manager = False

    # -----------------------------------------------------------------------------
    # Default Summary
    #
    settings.ui.summary = ({"common": True,
                            "name": "add",
                            "widgets": [{"method": "create"}],
                            },
                           {"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}],
                            },
                           {"name": "charts",
                            "label": "Report",
                            "widgets": [{"method": "report", "ajax_init": True}],
                            },
                           {"name": "map",
                            "label": "Map",
                            "widgets": [{"method": "map", "ajax_init": True}],
                            },
                           )

    # -----------------------------------------------------------------------------
    # Content Management
    #
    #settings.cms.hide_index = True
    settings.cms.richtext = True

    # -----------------------------------------------------------------------------
    # Messaging
    # Parser
    #settings.msg.parser = "IFRC"

    # =============================================================================
    # Module Settings

    # -----------------------------------------------------------------------------
    # Organisation Management
    #
    # Enable the use of Organisation Branches
    settings.org.branches = True
    # Set the length of the auto-generated org/site code the default is 10
    #settings.org.site_code_len = 3
    # Set the label for Sites
    settings.org.site_label = "Office/Warehouse/Facility"

    # Enable certain fields just for specific Organisations
    #settings.org.dependent_fields = \
    #    {"pr_person.middle_name"                     : (CVTL, VNRC),
    #     "pr_person_details.mother_name"             : (BRCS, ),
    #     "pr_person_details.father_name"             : (ARCS, BRCS),
    #     "pr_person_details.grandfather_name"        : (ARCS, ),
    #     "pr_person_details.affiliations"            : (PRC, ),
    #     "pr_person_details.company"                 : (PRC, ),
    #     "vol_details.availability"                  : (VNRC, ),
    #     "vol_details.card"                          : (ARCS, ),
    #     "vol_volunteer_cluster.vol_cluster_type_id"     : (PRC, ),
    #     "vol_volunteer_cluster.vol_cluster_id"          : (PRC, ),
    #     "vol_volunteer_cluster.vol_cluster_position_id" : (PRC, ),
    #     }

    # -----------------------------------------------------------------------------
    # Human Resource Management
    #
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
    # Uncomment to disable the use of HR Certificates
    settings.hrm.use_certificates = False
    # Uncomment to enable the use of HR Education
    #settings.hrm.use_education = True
    # Custom label for Organisations in HR module
    settings.hrm.organisation_label = "National Society / Branch"
    # Uncomment to consolidate tabs into a single CV
    settings.hrm.cv_tab = True
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    settings.hrm.record_tab = "record"

    # Uncomment to do a search for duplicates in the new AddPersonWidget2
    settings.pr.lookup_duplicates = True

    # -----------------------------------------------------------------------------
    # Projects
    settings.project.assign_staff_tab = False
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    settings.project.mode_drr = True
    # Uncomment this to use Activity Types for Activities & Projects
    settings.project.activity_types = True
    # Uncomment this to use Codes for projects
    settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    #settings.project.community = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
    # Uncomment this to enable Indicators in projects
    # Just HNRC
    #settings.project.indicators = True
    # Uncomment this to use multiple Budgets per project
    settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Ondelete behaviour for ProjectPlanningModel
    settings.project.planning_ondelete = "RESTRICT"
    # Uncomment this to enable Programmes in projects
    settings.project.programmes = True
    # Uncomment this to enable Themes in 3W projects
    settings.project.themes = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Host National Society"),
        2: T("Partner"),
        3: T("Donor"),
        #4: T("Customer"), # T("Beneficiary")?
        #5: T("Supplier"),
        9: T("Partner National Society"),
    }

    # -----------------------------------------------------------------------------
    # Inventory Management

    # Hide Staff Management Tabs for Facilities in Inventory Module
    settings.inv.facility_manage_staff = False

    settings.inv.show_mode_of_transport = True
    settings.inv.send_show_time_in = True
    #settings.inv.collapse_tabs = True
    # Uncomment if you need a simpler (but less accountable) process for managing stock levels
    #settings.inv.direct_stock_edits = True
    #settings.inv.org_dependent_warehouse_types = True
    # Settings for HNRC:
    settings.inv.stock_count = False
    settings.inv.item_status = {#0: current.messages["NONE"], # Not defined yet
                                0: T("Good"),
                                1: T("Damaged"),
                                #1: T("Dump"),
                                #2: T("Sale"),
                                #3: T("Reject"),
                                #4: T("Surplus")
                                }
    settings.inv.recv_types = {#0: current.messages["NONE"], In Shipment Types
                               #11: T("Internal Shipment"), In Shipment Types
                               32: T("Donation"),
                               34: T("Purchase"),
                               36: T("Consignment"), # Borrowed
                               37: T("In Transit"),  # Loaning warehouse space to another agency
                               }


    # -----------------------------------------------------------------------------
    # Request Management
    # Uncomment to disable Inline Forms in Requests module
    settings.req.inline_forms = False
    settings.req.req_type = ["Stock"]
    settings.req.use_commit = False
    # Should Requests ask whether Transportation is required?
    settings.req.ask_transport = True
    settings.req.pack_values = False
    # Disable Request Matching as we don't wwant users making requests to see what stock is available
    settings.req.prompt_match = False
    # Uncomment to disable Recurring Request
    settings.req.recurring = False # HNRC

    # =============================================================================
    # Template Modules
    #
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
                module_type = None,
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
        #("asset", Storage(
        #        name_nice = T("Assets"),
        #        #description = "Recording and Assigning Assets",
        #        restricted = True,
        #        #module_type = 5,
        #    )),
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
        ("budget", Storage(
                name_nice = T("Budgets"),
                #description = "Tracking of Budgets",
                restricted = True,
                #module_type = None
            )),
        #("survey", Storage(
        #        name_nice = T("Assessments"),
        #        #description = "Create, enter, and manage surveys.",
        #        restricted = True,
        #        #module_type = 5,
        #    )),
        #("event", Storage(
        #        name_nice = T("Events"),
        #        #description = "Events",
        #        restricted = True,
        #        #module_type = 10
        #    )),
        #("member", Storage(
        #       name_nice = T("Members"),
        #       #description = "Membership Management System",
        #       restricted = True,
        #       #module_type = 10,
        #   )),
        #("deploy", Storage(
        #       name_nice = T("Regional Disaster Response Teams"),
        #       #description = "Alerting and Deployment of Disaster Response Teams",
        #       restricted = True,
        #       #module_type = 10,
        #   )),
        #("po", Storage(
        #       name_nice = T("Recovery Outreach"),
        #       #description = "Population Outreach",
        #       restricted = True,
        #       #module_type = 10,
        #   )),
        ("stats", Storage(
                name_nice = T("Statistics"),
                #description = "Manages statistics",
                restricted = True,
                #module_type = None,
            )),
        #("vulnerability", Storage(
        #        name_nice = T("Vulnerability"),
        #        #description = "Manages vulnerability indicators",
        #        restricted = True,
        #        #module_type = 10,
        #    )),
    ])

    # -------------------------------------------------------------------------
    # Functions which are local to this Template
    # -------------------------------------------------------------------------
    def ns_only(tablename,
                fieldname = "organisation_id",
                required = True,
                branches = True,
                updateable = True,
                limit_filter_opts = True
                ):
        """
            Function to configure an organisation_id field to be restricted to just
            NS/Branch

            @param required: Field is mandatory
            @param branches: Include Branches
            @param updateable: Limit to Orgs which the user can update
            @param limit_filter_opts: Also limit the Filter options

            NB If limit_filter_opts=True, apply in customise_xx_controller inside prep,
               after standard_prep is run
        """

        # Lookup organisation_type_id for Red Cross
        db = current.db
        s3db = current.s3db
        ttable = s3db.org_organisation_type
        try:
            type_id = db(ttable.name == "Red Cross / Red Crescent").select(ttable.id,
                                                                           limitby=(0, 1),
                                                                           ).first().id
        except:
            # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
            return

        # Load standard model
        f = s3db[tablename][fieldname]

        if limit_filter_opts:
            # Find the relevant filter widget & limit it's options
            filter_widgets = s3db.get_config(tablename, "filter_widgets")
            filter_widget = None
            if filter_widgets:
                from s3 import FS, S3HierarchyFilter
                for w in filter_widgets:
                    if isinstance(w, S3HierarchyFilter) and \
                       w.field == "organisation_id":
                        filter_widget = w
                        break
            if filter_widget is not None:
                selector = FS("organisation_organisation_type.organisation_type_id")
                filter_widget.opts["filter"] = (selector == type_id)

        # Label
        if branches:
            f.label = T("National Society / Branch")
        else:
            f.label = T("National Society")

        # Requires

        # Filter by type
        ltable = db.org_organisation_organisation_type
        rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
        filter_opts = [row.organisation_id for row in rows]

        auth = current.auth
        s3_has_role = auth.s3_has_role
        Admin = s3_has_role("ADMIN")
        if branches:
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

        else:
            # Keep the represent function as simple as possible
            parent = False
            # Exclude branches
            btable = s3db.org_organisation_branch
            rows = db((btable.deleted != True) &
                      (btable.branch_id.belongs(filter_opts))).select(btable.branch_id)
            filter_opts = list(set(filter_opts) - set(row.branch_id for row in rows))

        organisation_represent = s3db.org_OrganisationRepresent
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
            selector = FS("organisation_organisation_type.organisation_type_id")
            f.widget = S3HierarchyWidget(lookup="org_organisation",
                                         filter=(selector == type_id),
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
            from s3layouts import S3AddResourceLink
            from s3 import S3ScriptItem
            add_link = S3AddResourceLink(c="org", f="organisation",
                                         vars={"organisation_type.name":"Red Cross / Red Crescent"},
                                         label=T("Create National Society"),
                                         title=T("National Society"),
                                         )
            comment = f.comment
            if not comment or isinstance(comment, S3AddResourceLink):
                f.comment = add_link
            elif isinstance(comment[1], S3ScriptItem):
                # Don't overwrite scripts
                f.comment[0] = add_link
            else:
                f.comment = add_link
        else:
            # Not allowed to add NS/Branch
            f.comment = ""

    # -----------------------------------------------------------------------------
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

    # -----------------------------------------------------------------------------
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

    # -----------------------------------------------------------------------------
    def customise_auth_user_controller(**attr):
        """
            Customise admin/user() and default/user() controllers
        """

        #if "arg" in attr and attr["arg"] == "register":
        # Organisation needs to be an NS/Branch
        ns_only("auth_user",
                required = True,
                branches = True,
                updateable = False, # Need to see all Orgs in Registration screens
                )

        return attr

    settings.customise_auth_user_controller = customise_auth_user_controller

    # -----------------------------------------------------------------------------
    def customise_hrm_course_controller(**attr):

        tablename = "hrm_course"

        # Organisation needs to be an NS/Branch
        ns_only(tablename,
                required = False,
                branches = False,
                )

        # Load standard model
        s3db = current.s3db
        table = s3db.hrm_course

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

    # -----------------------------------------------------------------------------
    def customise_hrm_department_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("hrm_department",
                required = False,
                branches = False,
                )

        return attr

    settings.customise_hrm_department_controller = customise_hrm_department_controller

    # -----------------------------------------------------------------------------
    def emergency_contact_represent(row):
        """
            Representation of Emergency Contacts (S3Represent label renderer)

            @param row: the row
        """

        items = [row["pr_contact_emergency.name"]]
        relationship = row["pr_contact_emergency.relationship"]
        if relationship:
            items.append(" (%s)" % relationship)
        phone_number = row["pr_contact_emergency.phone"]
        if phone_number:
            items.append(": %s" % phone_number)
        return "".join(items)

    # -----------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        controller = current.request.controller
        if controller != "deploy":
            # Default Filter
            from s3 import s3_set_default_filter
            s3_set_default_filter("~.organisation_id",
                                  user_org_and_children_default_filter,
                                  tablename = "hrm_human_resource")

        s3db = current.s3db
        s3db.org_organisation.root_organisation.label = T("National Society")

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            # Organisation needs to be an NS/Branch
            ns_only("hrm_human_resource",
                    required = True,
                    branches = True,
                    limit_filter_opts = True,
                    )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -----------------------------------------------------------------------------
    def customise_hrm_job_title_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("hrm_job_title",
                required = False,
                branches = False,
                )

        # Don't show RDRT in the list
        from gluon import IS_IN_SET
        current.s3db.hrm_job_title.type.requires = IS_IN_SET({1: T("Staff"),
                                                              2: T("Volunteer"),
                                                              3: T("Both")
                                                              })

        return attr

    settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

    # -----------------------------------------------------------------------------
    def customise_hrm_programme_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("hrm_programme",
                required = False,
                branches = False,
                )

        return attr

    settings.customise_hrm_programme_controller = customise_hrm_programme_controller

    # -----------------------------------------------------------------------------
    def customise_hrm_programme_hours_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.person_id$human_resource.organisation_id",
                              user_org_default_filter,
                              tablename = "hrm_programme_hours")

        return attr

    settings.customise_hrm_programme_hours_controller = customise_hrm_programme_hours_controller

    # -----------------------------------------------------------------------------
    def customise_hrm_training_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.person_id$human_resource.organisation_id",
                              user_org_default_filter,
                              tablename = "hrm_training")

        return attr

    settings.customise_hrm_training_controller = customise_hrm_training_controller

    # -----------------------------------------------------------------------------
    def customise_inv_home():
        """
            Homepage for the Inventory module
        """

        from gluon import URL
        from s3 import s3_redirect_default

        auth = current.auth
        if auth.user and auth.user.site_id and \
           not auth.s3_has_role(current.session.s3.system_roles.ORG_ADMIN):
            # Redirect to this Warehouse
            table = current.s3db.inv_warehouse
            wh = current.db(table.site_id == auth.user.site_id).select(table.id,
                                                                       limitby=(0, 1)
                                                                       ).first()
            if wh:
                s3_redirect_default(URL(c="inv", f="warehouse",
                                        args=[wh.id, "inv_item"]))

        # Redirect to Warehouse Summary Page
        s3_redirect_default(URL(c="inv", f="warehouse", args="summary"))

    settings.customise_inv_home = customise_inv_home

    # -----------------------------------------------------------------------------
    def customise_inv_inv_item_resource(r, tablename):

        current.s3db.configure("inv_inv_item",
                               create = False,
                               deletable = False,
                               editable = False,
                               listadd = False,
                               )

    settings.customise_inv_inv_item_resource = customise_inv_inv_item_resource

    # -----------------------------------------------------------------------------
    def customise_inv_send_resource(r, tablename):

        current.s3db.configure("inv_send",
                               list_fields = ["id",
                                              "send_ref",
                                              "req_ref",
                                              #"sender_id",
                                              "site_id",
                                              "date",
                                              "recipient_id",
                                              "delivery_date",
                                              "to_site_id",
                                              "status",
                                              #"driver_name",
                                              #"driver_phone",
                                              #"vehicle_plate_no",
                                              #"time_out",
                                              "comments",
                                              ],
                               )

    settings.customise_inv_send_resource = customise_inv_send_resource

    # -----------------------------------------------------------------------------
    def customise_inv_warehouse_resource(r, tablename):

        settings.gis.postcode_selector = False # Needs to be done before prep as read during model load
        settings.inv.recv_tab_label = "Received/Incoming Shipments"
        settings.inv.send_tab_label = "Sent Shipments"
        # Only Nepal RC use Warehouse Types
        s3db = current.s3db
        field = s3db.inv_warehouse.warehouse_type_id
        field.readable = field.writable = False
        list_fields = s3db.get_config("inv_warehouse", "list_fields")
        try:
            list_fields.remove("warehouse_type_id")
        except:
            # Already removed
            pass

    settings.customise_inv_warehouse_resource = customise_inv_warehouse_resource

    # -----------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        #root_org = current.auth.root_org_name()
        #if root_org != HNRC:
        #    return
        settings.gis.postcode_selector = False # Needs to be done before prep as read during model load
        # Simplify Form
        s3db = current.s3db
        table = s3db.org_facility
        table.code.readable = table.code.writable = False
        table.opening_times.readable = table.opening_times.writable = False
        table.website.readable = table.website.writable = False
        field = s3db.org_site_facility_type.facility_type_id
        field.readable = field.writable = False
        # Simplify Search Fields
        from s3 import S3TextFilter, S3OptionsFilter, S3LocationFilter
        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()
        text_fields = ["name",
                       #"code",
                       "comments",
                       "organisation_id$name",
                       "organisation_id$acronym",
                       ]
        for level in levels:
            lfield = "location_id$%s" % level
            text_fields.append(lfield)

        s3db.configure("org_facility",
                       filter_widgets = [
                            S3TextFilter(text_fields,
                                         label = T("Search"),
                                         ),
                            S3OptionsFilter("organisation_id"),
                            S3LocationFilter("location_id",
                                             levels = levels,
                                             ),
                            ]
                       )


    settings.customise_org_facility_resource = customise_org_facility_resource

    # -----------------------------------------------------------------------------
    def customise_org_office_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Organisation needs to be an NS/Branch
            ns_only("org_office",
                    required = True,
                    branches = True,
                    limit_filter_opts = True,
                    )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_org_office_controller = customise_org_office_controller

    # -----------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        type_filter = current.request.get_vars.get("organisation_type.name")

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.interactive or r.representation == "aadata":

                if not r.component or r.component_name == "branch":

                    resource = r.resource
                    table = resource.table

                    type_label = T("Type")

                    if r.get_vars.get("caller") == "org_facility_organisation_id":
                        # Simplify
                        from s3 import S3SQLCustomForm
                        crud_form = S3SQLCustomForm("name",
                                                    "acronym",
                                                    "phone",
                                                    "comments",
                                                    )
                        resource.configure(crud_form=crud_form,
                                           )
                    elif r.controller == "po":
                        # Referral Agencies in PO module
                        list_fields = ("name",
                                       "acronym",
                                       "organisation_organisation_type.organisation_type_id",
                                       "website",
                                       )
                        resource.configure(list_fields=list_fields)

                        # Custom CRUD form
                        if r.interactive:
                            from s3 import S3SQLCustomForm, S3SQLInlineLink, S3SQLInlineComponent
                            # Filter inline address for type "office address", also sets default
                            OFFICE = {"field": "type", "options": 3}
                            crud_form = S3SQLCustomForm(
                                            "name",
                                            "acronym",
                                            S3SQLInlineLink("organisation_type",
                                                            field = "organisation_type_id",
                                                            label = type_label,
                                                            multiple = False,
                                                            ),
                                            S3SQLInlineComponent("address",
                                                                 fields = [("", "location_id")],
                                                                 multiple = False,
                                                                 filterby = (OFFICE,),
                                                                 ),
                                            "phone",
                                            "website",
                                            "logo",
                                            "comments",
                                            )
                            # Remove unwanted filters
                            # @todo: add a location filter for office address
                            unwanted_filters = ("sector_organisation.sector_id",
                                                "country",
                                                )
                            filter_widgets = [widget
                                              for widget in resource.get_config("filter_widgets")
                                              if widget.field not in unwanted_filters]
                            resource.configure(crud_form = crud_form,
                                               filter_widgets = filter_widgets,
                                               )
                    else:
                        # Organisations in other modules (org, inv etc.)
                        list_fields = ["name",
                                       "acronym",
                                       "organisation_organisation_type.organisation_type_id",
                                       "country",
                                       "website",
                                       ]
                        if type_filter:
                            type_names = type_filter.split(",")
                            if len(type_names) == 1:
                                # Strip Type from list_fields
                                list_fields.remove("organisation_organisation_type.organisation_type_id")
                                type_label = ""

                            if type_filter == "Red Cross / Red Crescent":
                                # Modify filter_widgets
                                filter_widgets = resource.get_config("filter_widgets")
                                # Remove type (always 'RC')
                                filter_widgets.pop(1)

                                # Modify CRUD Strings
                                s3.crud_strings.org_organisation = Storage(
                                    label_create = T("Create National Society"),
                                    title_display = T("National Society Details"),
                                    title_list = T("Red Cross & Red Crescent National Societies"),
                                    title_update = T("Edit National Society"),
                                    title_upload = T("Import Red Cross & Red Crescent National Societies"),
                                    label_list_button = T("List Red Cross & Red Crescent National Societies"),
                                    label_delete_button = T("Delete National Society"),
                                    msg_record_created = T("National Society added"),
                                    msg_record_modified = T("National Society updated"),
                                    msg_record_deleted = T("National Society deleted"),
                                    msg_list_empty = T("No Red Cross & Red Crescent National Societies currently registered")
                                    )
                                # Add Region to list_fields
                                list_fields.insert(-1, "region_id")
                                # Region is required
                                table.region_id.requires = table.region_id.requires[0].other

                            else:
                                table.region_id.readable = table.region_id.writable = False

                            if type_filter == "Supplier":
                                # Show simple free-text contact field
                                contact_field = table.contact
                                contact_field.readable = True
                                contact_field.writable = True

                                # Include contact information in list_fields
                                list_fields = ["name",
                                               "acronym",
                                               "country",
                                               "contact",
                                               "phone",
                                               "website",
                                               ]

                        resource.configure(list_fields=list_fields)

                        if r.interactive:
                            table.country.label = T("Country")
                            from s3 import S3SQLCustomForm, S3SQLInlineLink
                            crud_form = S3SQLCustomForm(
                                            "name",
                                            "acronym",
                                            S3SQLInlineLink("organisation_type",
                                                            field = "organisation_type_id",
                                                            label = type_label,
                                                            multiple = False,
                                                            #widget = "hierarchy",
                                                            ),
                                            "region_id",
                                            "country",
                                            "contact",
                                            "phone",
                                            "website",
                                            "logo",
                                            "comments",
                                            )
                            resource.configure(crud_form=crud_form)

            return result
        s3.prep = custom_prep

        settings = current.deployment_settings

        # Alter rheader tabs for Suppliers (=hide Offices, Warehouses and Contacts)
        if type_filter == "Supplier":
            tabs = [(T("Basic Details"), None, {"native": 1}),
                    ]
            if settings.get_L10n_translate_org_organisation():
                tabs.append((T("Local Names"), "name"))
            attr["rheader"] = lambda r: current.s3db.org_rheader(r, tabs=tabs)

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -----------------------------------------------------------------------------
    def customise_pr_group_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("org_organisation_team",
                required = False,
                branches = True,
                )

        return attr

    settings.customise_pr_group_controller = customise_pr_group_controller

    # =============================================================================
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
            three_months_prior = (now - datetime.timedelta(days=92))
            end = max(programmes.last().date, three_months_prior.date())
            last_year = end - datetime.timedelta(days=365)
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

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            settings.gis.postcode_selector = False # Needs to be done before prep as read during model load

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
            method = r.method
            if component_name == "appraisal":
                atable = r.component.table
                atable.organisation_id.readable = atable.organisation_id.writable = False
                # Organisation needs to be an NS
                #ns_only("hrm_appraisal",
                #        required = True,
                #        branches = False,
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
            elif component_name == "physical_description":
                from gluon import DIV
                dtable = r.component.table
                dtable.medical_conditions.comment = DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Medical Conditions"),
                                                                          T("Chronic Illness, Disabilities, Mental/Psychological Condition etc.")))

            elif method =="record" or component_name == "human_resource":
                # Organisation needs to be an NS/Branch
                ns_only("hrm_human_resource",
                        required = True,
                        branches = True,
                        )
                if method == "record":
                    # Use default form (legacy)
                    s3db.clear_config("hrm_human_resource", "crud_form")

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -----------------------------------------------------------------------------
    def customise_supply_item_category_resource(r, tablename):

        #root_org = current.auth.root_org_name()
        #if root_org == HNRC:
        # Not using Assets Module
        field = current.s3db.supply_item_category.can_be_asset
        field.readable = field.writable = False

    settings.customise_supply_item_category_resource = customise_supply_item_category_resource

    # -----------------------------------------------------------------------------
    def customise_survey_series_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("survey_series",
                required = False,
                branches = True,
                )

        return attr

    settings.customise_survey_series_controller = customise_survey_series_controller

    # -----------------------------------------------------------------------------
    # Projects
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    settings.project.mode_drr = True
    # Uncomment this to use Activity Types for Activities & Projects
    settings.project.activity_types = True
    # Uncomment this to use Codes for projects
    settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    settings.project.community = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
    # Uncomment this to enable Indicators in projects
    # Just HNRC
    #settings.project.indicators = True
    # Uncomment this to use multiple Budgets per project
    settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Uncomment this to enable Programmes in projects
    settings.project.programmes = True
    # Uncomment this to enable Themes in 3W projects
    settings.project.themes = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Host National Society"),
        2: T("Partner"),
        3: T("Donor"),
        #4: T("Customer"), # T("Beneficiary")?
        #5: T("Supplier"),
        9: T("Partner National Society"),
    }

    # -------------------------------------------------------------------------
    def household_inject_form_script(r, record):
        """
            Inject JS for progressive revelation of household form,
            to be called from prep

            @param r: the S3Request
            @param record: the household record
        """

        if r.interactive:
            s3 = current.response.s3
            script = "/%s/static/themes/IFRC/js/po.js" % current.request.application
            if script not in s3.scripts:
                s3.scripts.append(script)
            if record and record.followup:
                s3.jquery_ready.append('''$.showHouseholdComponents(true)''');
        return

    # -------------------------------------------------------------------------
    def customise_po_household_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            # Do not require international phone number format
            settings = current.deployment_settings
            settings.msg.require_international_phone_numbers = False
            # Inject JS for household form
            household_inject_form_script(r, r.record)
            return result
        s3.prep = custom_prep

        return attr

    settings.customise_po_household_controller = customise_po_household_controller

    # -------------------------------------------------------------------------
    def customise_po_area_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            # Do not require international phone number format
            settings = current.deployment_settings
            settings.msg.require_international_phone_numbers = False
            if r.component_name == "household":
                # Inject JS for household form
                record = None
                if r.component_id:
                    records = r.component.load()
                    if records:
                        record = records[0]
                household_inject_form_script(r, record)
            return result
        s3.prep = custom_prep

        return attr

    settings.customise_po_area_controller = customise_po_area_controller

    # -------------------------------------------------------------------------
    def project_project_postprocess(form):
        """
            When using Project Monitoring (i.e. HNRC) then create the entries
        """

        db = current.db
        s3db = current.s3db
        project_id = form.vars.id
        # Read Budget Entity ID, Start Date and End Date
        ptable = s3db.project_project
        project = db(ptable.id == project_id).select(ptable.budget_entity_id,
                                                     ptable.name,
                                                     ptable.start_date,
                                                     ptable.end_date,
                                                     limitby=(0, 1)
                                                     ).first()
        if not project:
            return

        # Copy Project Name to Budget Name
        budget_entity_id = project.budget_entity_id
        btable = s3db.budget_budget
        query = (btable.budget_entity_id == budget_entity_id)
        budget = db(query).select(btable.id, # Needed for update_record
                                  # If we want to provide smoothed default expected values
                                  #btable.total_budget,
                                  btable.currency,
                                  # Assume Monthly
                                  #btable.monitoring_frequency,
                                  limitby=(0, 1)
                                  ).first()
        if not budget:
            return
        try:
            budget.update_record(name = project.name)
        except:
            # unique=True violation
            budget.update_record(name = "Budget for %s" % project.name)

        mtable = s3db.budget_monitoring
        exists = db(mtable.budget_entity_id == budget_entity_id).select(mtable.id,
                                                                        limitby=(0, 1))
        if not exists:
            # Create Monitoring Data entries
            start_date = project.start_date
            end_date = project.end_date
            if not start_date or not end_date:
                return
            # Assume Monthly
            #monitoring_frequency = budget.monitoring_frequency
            #if not monitoring_frequency:
            #    return
            #total_budget = budget.total_budget
            currency = budget.currency
            # Create entries for the 1st of every month between start_date and end_date
            from dateutil import rrule
            dates = list(rrule.rrule(rrule.MONTHLY, bymonthday=1, dtstart=start_date, until=end_date))
            for d in dates:
                mtable.insert(budget_entity_id = budget_entity_id,
                              # @ToDo: This needs to be modified whenever entries are manually edited
                              # Set/update this in budget_monitoring_onaccept
                              # - also check here that we don't exceed overall budget
                              start_date = start_date,
                              end_date = d,
                              currency = currency,
                              )
                # Start date relates to previous entry
                start_date = d

    # -----------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        tablename = "project_project"

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_default_filter,
                              tablename = "project_project")

        # Load standard model
        s3db = current.s3db
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
        table.organisation_id.label = T("Host National Society")

        # Custom Crud Form
        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            HFA = None
            # @ToDo: Use Inter-American Framework instead (when extending to Zone office)
            # @ToDo: Add 'Business Line' (when extending to Zone office)
            settings.project.details_tab = True
            settings.project.community_volunteers = True
            # Done in a more structured way instead
            objectives = None
            outputs = None
            settings.project.goals = True
            settings.project.indicators = True
            settings.project.outcomes = True
            settings.project.outputs = True
            # Use Budget module instead of ProjectAnnualBudget
            settings.project.multiple_budgets = False
            settings.project.budget_monitoring = True
            # Require start/end dates
            table.start_date.requires = table.start_date.requires.other
            table.end_date.requires = table.end_date.requires.other
            budget = S3SQLInlineComponent(
                "budget",
                label = T("Budget"),
                #link = False,
                multiple = False,
                fields = ["total_budget",
                          "currency",
                          #"monitoring_frequency",
                          ],
            )
            btable = s3db.budget_budget
            # Need to provide a name
            import random, string
            btable.name.default = "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
            btable.monitoring_frequency.default = 3 # Monthly
            postprocess = project_project_postprocess
            list_fields = s3db.get_config("project_project", "list_fields")
            list_fields += [(T("Monthly Status"), "current_status_by_indicators"),
                            (T("Cumulative Status"), "overall_status_by_indicators"),
                            ]
        else:
            HFA = "drr.hfa"
            objectives = "objectives"
            outputs = S3SQLInlineComponent(
                "output",
                label = T("Outputs"),
                fields = ["name", "status"],
            )
            budget = None
            postprocess = None

        if settings.get_project_programmes():
            # Inject inline link for programmes including AddResourceLink
            #from s3layouts import S3AddResourceLink
            comment = s3db.project_programme_id.attr.comment
            comment.vars = {"caller": "link_defaultprogramme",
                            "prefix": "project",
                            "parent": "programme_project",
                            }
            programme = S3SQLInlineLink("programme",
                                        label = T("Program"),
                                        field = "programme_id",
                                        multiple = False,
                                        comment = comment,
                                        )
        else:
            programme = None

        crud_form = S3SQLCustomForm(
            "organisation_id",
            programme,
            "name",
            "code",
            "description",
            "status_id",
            "start_date",
            "end_date",
            budget,
            #S3SQLInlineComponent(
            #    "location",
            #    label = T("Locations"),
            #    fields = ["location_id"],
            #),
            # Outputs
            outputs,
            S3SQLInlineLink(
                "hazard",
                label = T("Hazards"),
                field = "hazard_id",
                help_field = s3db.project_hazard_help_fields,
                cols = 4,
                translate = True,
            ),
            S3SQLInlineLink(
                "sector",
                label = T("Sectors"),
                field = "sector_id",
                cols = 4,
                translate = True,
            ),
            S3SQLInlineLink(
                "theme",
                label = T("Themes"),
                field = "theme_id",
                help_field = s3db.project_theme_help_fields,
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
     'showEmptyField':false,
     'tooltip':'project_theme_help_fields(id,name)'
    })'''
            ),
            HFA,
            objectives,
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
            postprocess = postprocess,
        )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Lead Organisation needs to be an NS (not a branch)
            ns_only(tablename,
                    required = True,
                    branches = False,
                    limit_filter_opts = True,
                    )

            # Set the Host NS filter as Visible so that the default filter works
            filter_widgets = s3db.get_config(tablename, "filter_widgets")
            for widget in filter_widgets:
                if widget.field == "organisation_id":
                    widget.opts.hidden = False
                    break

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # -----------------------------------------------------------------------------
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
                                        "target_value",
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

    # -----------------------------------------------------------------------------
    def customise_project_indicator_resource(r, tablename):

        table = current.s3db.project_indicator
        table.definition.label = T("Indicator Definition")
        table.measures.label = T("Indicator Criteria and Sources of Verification")

    settings.customise_project_indicator_resource = customise_project_indicator_resource

    # -----------------------------------------------------------------------------
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

    # -----------------------------------------------------------------------------
    def customise_req_commit_controller(**attr):

        # Request is mandatory
        field = current.s3db.req_commit.req_id
        field.requires = field.requires.other

        return attr

    settings.customise_req_commit_controller = customise_req_commit_controller

    # -----------------------------------------------------------------------------
    def customise_req_req_resource(r, tablename):

        s3db = current.s3db

        # Request is mandatory
        field = s3db.req_commit.req_id
        field.requires = field.requires.other

        table = s3db.req_req
        table.req_ref.represent = lambda v, show_link=True, pdf=True: \
                s3db.req_ref_represent(v, show_link, pdf)
        table.site_id.label = T("Deliver To")
        # Hide Drivers list_field
        list_fields = s3db.get_config("req_req", "list_fields")
        try:
            list_fields.remove((T("Drivers"), "drivers"))
        except:
            # Already removed
            pass

    settings.customise_req_req_resource = customise_req_req_resource

# END =========================================================================