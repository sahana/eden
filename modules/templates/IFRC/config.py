# -*- coding: utf-8 -*-

import datetime

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

from s3 import S3Represent

from .controllers import deploy_index

def config(settings):
    """
        Template settings for IFRC's Resource Management System

        http://eden.sahanafoundation.org/wiki/Deployments/IFRC

        This version was developed for the Asia-Pacific Zone and also used in:
            * Madagascar
            * Nairobi (RDRT)
        Currently used in:
            * Iraq
            * Yemen
    """

    T = current.T

    # -------------------------------------------------------------------------
    # System Name
    #
    settings.base.system_name = T("Resource Management System")
    settings.base.system_name_short = T("RMS")

    # -------------------------------------------------------------------------
    # Custom Models
    #
    settings.base.custom_models = {"deploy": "RMS",
                                   "po": "IFRC",
                                   "survey": "IFRC",
                                   }

    # -------------------------------------------------------------------------
    # Pre-Populate
    settings.base.prepopulate += ("IFRC",)
    settings.base.prepopulate_demo += ("IFRC/Train",
                                       #"IFRC/Demo", # Takes a long time to import
                                       )

    # =========================================================================
    # System Settings
    # -------------------------------------------------------------------------
    # Use the Database for storing sessions to avoid session locks on long-running requests
    settings.base.session_db = True

    # Security Policy
    settings.security.policy = 7
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
    # System-generated Surveys need to be Approved/Rejected
    settings.auth.record_approval_required_for = ("dc_target",)

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
        if tablename in ("event_event_type",
                         "hrm_certificate",
                         "hrm_department",
                         "hrm_job_title",
                         "hrm_course",
                         "hrm_programme",
                         "hrm_skill",
                         "member_membership_type",
                         "vol_award",
                         ):
            return None

        db = current.db
        s3db = current.s3db

        # Entity reference fields
        EID = "pe_id"
        OID = "organisation_id"
        SID = "site_id"
        #GID = "group_id"
        PID = "person_id"

        # Owner Entity Foreign Key
        realm_entity_fks = {"hrm_competency": PID,
                            "hrm_credential": PID,
                            "hrm_experience": PID,
                            "hrm_human_resource": SID,
                            "hrm_training": PID, # Also see-below
                            "pr_contact": [("org_organisation", EID),
                                          ("po_household", EID),
                                          ("pr_person", EID),
                                          ],
                            "pr_contact_emergency": EID,
                            "pr_physical_description": EID,
                            "pr_address": [("org_organisation", EID),
                                          ("pr_person", EID),
                                          ],
                            "pr_image": EID,
                            "pr_identity": PID,
                            "pr_education":PID,
                            "pr_group": OID,
                            "pr_note": PID,
                            "inv_recv": SID,
                            "inv_send": SID,
                            "inv_track_item": "track_org_id",
                            "inv_adj_item": "adj_id",
                            "org_capacity_assessment_data": "assessment_id",
                            "po_area": OID,
                            "po_household": "area_id",
                            "po_organisation_area": "area_id",
                            "inv_req_item": "req_id",
                            }

        # Default Foreign Keys (ordered by priority)
        default_fks = ("household_id",
                       "catalog_id",
                       "project_id",
                       "project_location_id",
                       )

        # Link Tables
        #realm_entity_link_table = {
        #    "project_task": Storage(tablename = "project_task_project",
        #                           link_key = "task_id"
        #                           )
        #    }
        #if tablename in realm_entity_link_table:
        #    # Replace row with the record from the link table
        #    link_table = realm_entity_link_table[tablename]
        #    table = s3db[link_table.tablename]
        #    rows = db(table[link_table.link_key] == row.id).select(table.id,
        #                                                           limitby=(0, 1))
        #    if rows:
        #        # Update not Create
        #        row = rows.first()

        realm_entity = 0

        # Check if there is a FK to inherit the realm_entity
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
                query = (table.id == row["id"]) & \
                        (table[fk] == ftable.id)
            record = db(query).select(ftable.realm_entity,
                                      limitby = (0, 1),
                                      ).first()
            if record:
                realm_entity = record.realm_entity
                break
            #else:
            # Continue to loop through the rest of the default_fks
            # Fall back to default get_realm_entity function

        auth = current.auth
        use_user_organisation = False
        #use_user_root_organisation = False

        if tablename in ("org_facility", "inv_req"):
            # Facilities & Requisitions are in the user organisation's realm
            use_user_organisation = True

        elif realm_entity == 0:
            if tablename == "org_organisation":
                if current.request.controller == "po":
                    # Referral Agencies to be in the root_org realm
                    realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                     auth.root_org())
                else:
                    # Suppliers & Partners are in the user organisation's realm
                    # @note: when the organisation record is first written, no
                    #        type-link would exist yet, so this needs to be
                    #        called again every time the type-links for an
                    #        organisation change in order to be effective
                    ottable = s3db.org_organisation_type
                    ltable = db.org_organisation_organisation_type
                    query = (ltable.organisation_id == row["id"]) & \
                            (ottable.id == ltable.organisation_type_id) & \
                            (ottable.name == "Red Cross / Red Crescent")
                    rclink = db(query).select(ltable.id,
                                              limitby = (0, 1),
                                              ).first()
                    if not rclink:
                        use_user_organisation = True

            elif tablename == "hrm_training":
                # Inherit realm entity from the related HR record if none set on the person record
                htable = s3db.hrm_human_resource
                query = (table.id == row["id"]) & \
                        (htable.person_id == table.person_id) & \
                        (htable.deleted != True)
                rows = db(query).select(htable.realm_entity,
                                        limitby = (0, 2),
                                        )
                if len(rows) == 1:
                    realm_entity = rows.first().realm_entity
                else:
                    # Ambiguous => try course organisation
                    ctable = s3db.hrm_course
                    otable = s3db.org_organisation
                    query = (table.id == row["id"]) & \
                            (ctable.id == table.course_id) & \
                            (otable.id == ctable.organisation_id)
                    org = db(query).select(otable.pe_id,
                                           limitby = (0, 1),
                                           ).first()
                    if org:
                        realm_entity = org.pe_id

            elif tablename == "pr_group":
                # Groups are in the user organisation's realm if not linked to an Organisation directly
                use_user_organisation = True

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

    # -------------------------------------------------------------------------
    # Theme (folder to use for views/layout.html)
    settings.base.theme = "IFRC"
    settings.base.xtheme = "IFRC/xtheme-ifrc.css"

    # Formstyle
    settings.ui.formstyle = "table"
    settings.ui.filter_formstyle = "table_inline"
    # Uncomment to disable responsive behavior of datatables
    settings.ui.datatables_responsive = False

    # Icons
    settings.ui.icons = "font-awesome3"
    settings.ui.custom_icons = {
        "male": "icon-male",
        "female": "icon-female",
        "medical": "icon-plus-sign-alt",
    }

    settings.gis.map_height = 600
    settings.gis.map_width = 869
    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = True
    # GeoNames username
    settings.gis.geonames_username = "rms_dev"

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages = OrderedDict([
        ("ar", "Arabic"),
        #("dv", "Divehi"), # Maldives
        #("dz", "Dzongkha"), # Bhutan
        ("en-gb", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
        ("id", "Indonesian"),
        ("km", "Khmer"), # Cambodia
        ("lo", "Lao"),
        ("mg", "Мalagasy"), # Madagascar
        ("mn", "Mongolian"),
        ("ms", "Malaysian"),
        ("my", "Burmese"),
        ("ne", "Nepali"),
        ("prs", "Dari"), # Afghan  Persian
        ("ps", "Pashto"), # Afghanistan, Pakistan
        ("th", "Thai"),
        ("vi", "Vietnamese"),
        ("zh-cn", "Chinese (Simplified)"), # Mainland
    ])
    # Default Language
    settings.L10n.default_language = "en-gb"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Kuala_Lumpur"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Unsortable 'pretty' date format (for use in English)
    # For a potential way to sort, see http://datatables.net/manual/orthogonal-data
    settings.L10n.date_format = "%d-%b-%Y"
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this for Alternate Location Names
    settings.L10n.name_alt_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True

    # Names of Orgs with specific settings
    AP_ZONE = "Asia-Pacific Region"
    ARCS = "Afghan Red Crescent Society"
    AURC = "Australian Red Cross"
    BRCS = "Bangladesh Red Crescent Society"
    CRMADA = "Malagasy Red Cross Society"
    CVTL = "Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste)"
    #IFRC = "International Federation of Red Cross and Red Crescent Societies"
    IRCS = "Iraqi Red Crescent Society"
    NRCS = "Nepal Red Cross Society"
    NZRC = "New Zealand Red Cross"
    PMI = "Indonesian Red Cross Society (Palang Merah Indonesia)"
    PRC = "Philippine Red Cross"
    VNRC = "Viet Nam Red Cross"

    # -------------------------------------------------------------------------
    def airegex(default):
        """ NS-specific settings for accent-insensitive searching """

        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            return True
        else:
            return False

    settings.database.airegex = airegex

    # -------------------------------------------------------------------------
    def l10n_calendar(default):
        """ Which calendar to use """

        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            return "Afghan"
        return default

    settings.L10n.calendar = l10n_calendar

    # -------------------------------------------------------------------------
    # Finance settings
    #
    def currencies(default):
        """ RMS- and NS-specific currencies """

        # Currencies that are common for all NS
        currencies = {"EUR" : "Euros",
                      "CHF" : "Swiss Francs",
                      "USD" : "United States Dollars",
                      }

        # NS-specific currencies
        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            currencies["AFN"] = "Afghani"
        elif root_org == AURC:
            currencies["AUD"] = "Australian Dollars"
        elif root_org == BRCS:
            currencies["BDT"] = "Taka"
        elif root_org == CRMADA:
            currencies["CAD"] = "Canadian Dollars"
            currencies["MGA"] = "Malagasy Ariary"
            currencies["NOK"] = "Norwegian Krone"
        elif root_org == IRCS:
            currencies["IQD"] = "Iraqi Dinar"
        elif root_org == NRCS:
            currencies["NPR"] = "Nepalese Rupee"
        elif root_org == NZRC:
            currencies["NZD"] = "New Zealand Dollars"
        elif root_org == PMI:
            currencies["IDR"] = "Indonesian Rupiah"
        elif root_org == PRC:
            currencies["PHP"] = "Philippine Pesos"
        elif root_org == VNRC:
            currencies["VND"] = "Vietnamese Dong"
        else:
            currencies["GBP"] = "Great British Pounds"
            currencies["CAD"] = "Canadian Dollars"
        return currencies

    settings.fin.currencies = currencies

    def currency_default(default):
        """ NS-specific default currencies """

        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            default = "AFN"
        elif root_org == AURC:
            default = "AUD"
        elif root_org == BRCS:
            default = "BDT"
        elif root_org == CRMADA:
            default = "MGA"
        elif root_org == IRCS:
            default = "IQD"
        elif root_org == NRCS:
            default = "NPR"
        elif root_org == NZRC:
            default = "NZD"
        elif root_org == PMI:
            default = "IDR"
        elif root_org == PRC:
            default = "PHP"
        elif root_org == VNRC:
            default = "VND"
        #else:
            #default = "USD"
        return default

    settings.fin.currency_default = currency_default

    # -------------------------------------------------------------------------
    def pdf_bidi(default):
        """ NS-specific selection of whether to support BiDi in PDF output """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, IRCS):
            default = True
        return default

    settings.L10n.pdf_bidi = pdf_bidi

    # -------------------------------------------------------------------------
    def pdf_export_font(default):
        """ NS-specific selection of which font to use in PDF output """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, IRCS):
            # Use Unifont even in English since there is data stored with non-English characters
            default = ["unifont", "unifont"]
        return default

    settings.L10n.pdf_export_font = pdf_export_font

    # -------------------------------------------------------------------------
    def postcode_selector(default):
        """ NS-specific selection of whether to show Postcode """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, IRCS, VNRC):
            default = False
        return default

    settings.gis.postcode_selector = postcode_selector

    # -------------------------------------------------------------------------
    def label_fullname(default):
        """
            NS-specific selection of label for the AddPersonWidget2's Name field
        """

        if current.session.s3.language == "mg":
            # Allow for better localisation
            default = "Full Name"
        return default

    settings.pr.label_fullname = label_fullname

    # -------------------------------------------------------------------------
    # Enable this for a UN-style deployment
    #settings.ui.cluster = True
    # Enable this to use the label 'Camp' instead of 'Shelter'
    settings.ui.camp = True

    # -------------------------------------------------------------------------
    # Filter Manager
    settings.search.filter_manager = False

    # -------------------------------------------------------------------------
    # Default Summary
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

    # Increase timeout on AJAX reports (ms)
    settings.ui.report_timeout = 600000 # 10 mins, same as the webserver
    # Increase the timeout on Report auto-submission
    settings.ui.report_auto_submit = 1400 # 1.4s

    # -------------------------------------------------------------------------
    # Content Management
    #
    # Uncomment this to hide CMS from module index pages
    settings.cms.hide_index = True
    settings.cms.richtext = True

    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    settings.msg.parser = "IFRC"

    # =========================================================================
    # Module Settings

    # -------------------------------------------------------------------------
    # Data Collection
    settings.dc.response_label = "Survey"
    settings.dc.unique_question_names_per_template = True

    # Fill-out Assessments on Web-only
    settings.dc.response_mobile = False
    #settings.dc.response_web = False

    # -------------------------------------------------------------------------
    # Organisation Management
    # Enable the use of Organisation Branches
    settings.org.branches = True
    # Enable the use of Organisation Regions
    settings.org.regions = True
    # Make Organisation Regions Hierarchical
    settings.org.regions_hierarchical = True
    # Enable the use of Organisation Region Countries
    settings.org.region_countries = True
    # Set the length of the auto-generated org/site code the default is 10
    settings.org.site_code_len = 3
    # Set the label for Sites
    settings.org.site_label = "Office/Warehouse/Facility"
    # Enable certain fields just for specific Organisations
    # @ToDo: Make these Lazy settings
    settings.org.dependent_fields = \
        {"pr_person.middle_name"                     : (CVTL, VNRC),
         "pr_person_details.mother_name"             : (BRCS, ),
         "pr_person_details.father_name"             : (ARCS, BRCS, IRCS),
         "pr_person_details.grandfather_name"        : (ARCS, IRCS),
         "pr_person_details.year_of_birth"           : (ARCS, ),
         "pr_person_details.affiliations"            : (PRC, ),
         "pr_person_details.company"                 : (PRC, ),
         "vol_details.card"                          : (ARCS, ),
         "vol_volunteer_cluster.vol_cluster_type_id"     : (PRC, ),
         "vol_volunteer_cluster.vol_cluster_id"          : (PRC, ),
         "vol_volunteer_cluster.vol_cluster_position_id" : (PRC, ),
         }

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
    settings.hrm.organisation_label = "National Society / Branch"
    # Custom label for Top-level Organisations in HR module
    settings.hrm.root_organisation_label = "National Society"
    # Uncomment to consolidate tabs into a single CV
    settings.hrm.cv_tab = True
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    settings.hrm.record_tab = "record"

    # Uncomment to do a search for duplicates in AddPersonWidget2
    settings.pr.lookup_duplicates = True

    # Surge (RDRT)
    settings.hrm.job_title_deploy = True
    settings.deploy.hr_label = "Member"
    settings.deploy.team_label = "Surge"
    # Responses only come in via Email
    settings.deploy.responses_via_web = False
    settings.customise_deploy_home = deploy_index
    # Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
    settings.hrm.skill_types = True
    # RDRT overrides these within controller:
    # Uncomment to disable Staff experience
    settings.hrm.staff_experience = False
    # Activity types for experience record
    settings.hrm.activity_types = {"rdrt": "RDRT Mission"}

    # -------------------------------------------------------------------------
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
    # Uncomment this to enable Demographics in 3W projects
    settings.project.demographics = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
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
    # Inventory Management
    #settings.inv.collapse_tabs = True
    # Uncomment if you need a simpler (but less accountable) process for managing stock levels
    settings.inv.direct_stock_edits = True
    settings.inv.org_dependent_warehouse_types = True
    # Settings for HNRC:
    #settings.inv.stock_count = False
    #settings.inv.item_status = {#0: current.messages["NONE"], # Not defined yet
    #                            0: T("Good"),
    #                            1: T("Damaged"),
    #                            #1: T("Dump"),
    #                            #2: T("Sale"),
    #                            #3: T("Reject"),
    #                            #4: T("Surplus")
    #                            }
    #settings.inv.recv_types = {#0: current.messages["NONE"], In Shipment Types
    #                           #11: T("Internal Shipment"), In Shipment Types
    #                           32: T("Donation"),
    #                           34: T("Purchase"),
    #                           36: T("Consignment"), # Borrowed
    #                           37: T("In Transit"),  # Loaning warehouse space to another agency
    #                           }

    # -------------------------------------------------------------------------
    # Request Management
    # Uncomment to disable Inline Forms in Requests module
    settings.inv.req_inline_forms = False
    settings.inv.use_commit = False
    # Should Requests ask whether Transportation is required?
    settings.inv.req_ask_transport = True
    settings.inv.req_pack_values = False
    # Disable Request Matching as we don't want users making requests to see what stock is available
    #settings.inv.req_prompt_match = False # HNRC
    # Uncomment to disable Recurring Request
    #settings.inv.req_recurring = False # HNRC

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
        ("setup", Storage(
            name_nice = T("Setup"),
            #description = "WebSetup",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
             module_type = None  # No Menu
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
        ("asset", Storage(
                name_nice = T("Assets"),
                #description = "Recording and Assigning Assets",
                restricted = True,
                #module_type = 5,
            )),
        #("req", Storage(
        #        name_nice = T("Requests"),
        #        #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #        restricted = True,
        #        #module_type = 10,
        #    )),
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
        # Old Surveys module
        ("survey", Storage(
                name_nice = T("Assessments"),
                #description = "Create, enter, and manage surveys.",
                restricted = True,
                #module_type = 5,
            )),
        # New Surveys module (currently just used by Bangkok CCST for Training Monitoring)
        ("dc", Storage(
                name_nice = T("Assessments"),
                #description = "Create, enter, and manage surveys.",
                restricted = True,
                #module_type = 5,
            )),
        ("event", Storage(
                name_nice = T("Events"),
                #description = "Events",
                restricted = True,
                #module_type = 10
            )),
        ("member", Storage(
               name_nice = T("Members"),
               #description = "Membership Management System",
               restricted = True,
               #module_type = 10,
           )),
        ("deploy", Storage(
               name_nice = T("Regional Disaster Response Teams"),
               #description = "Alerting and Deployment of Disaster Response Teams",
               restricted = True,
               #module_type = 10,
           )),
        ("dvr", Storage(
               name_nice = T("Disaster Victim Registry"),
               #description = "Population Outreach",
               restricted = True,
               #module_type = 10,
           )),
        ("po", Storage(
               name_nice = T("Recovery Outreach"),
               #description = "Population Outreach",
               restricted = True,
               #module_type = 10,
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
    def ns_only(tablename,
                fieldname = "organisation_id",
                required = True,
                branches = True,
                updateable = True,
                limit_filter_opts = True,
                hierarchy = True,
                ):
        """
            Function to configure an organisation_id field to be restricted to just
            NS/Branch

            @param required: Field is mandatory
            @param branches: Include Branches
            @param updateable: Limit to Orgs which the user can update
            @param limit_filter_opts: Also limit the Filter options
            @param hierarchy: Use the hierarchy widget (unsuitable for use in Inline Components)

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
                                                                           cache = s3db.cache,
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

        if parent and hierarchy:
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
            from s3layouts import S3PopupLink
            from s3 import S3ScriptItem
            add_link = S3PopupLink(c = "org",
                                   f = "organisation",
                                   vars = {"organisation_type.name":"Red Cross / Red Crescent"},
                                   label = T("Create National Society"),
                                   title = T("National Society"),
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
            # Not allowed to add NS/Branch
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
    def user_org_root_default_filter(selector, tablename=None):
        """
            Default filter for organisation_id:
            * Use the user's root organisation if logged-in and associated with
              an organisation.
        """

        user_root_org_id = current.auth.root_org()
        if user_root_org_id:
            return user_root_org_id
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
                                                      limitby=(0, 1),
                                                      cache = s3db.cache,
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
    def user_region_and_children_default_filter(selector, tablename=None):
        """
            Default filter for organisation_id:
            * Use the user's region if logged-in and associated with an
              organisation.
        """

        auth = current.auth
        user_org_id = auth.is_logged_in() and auth.user.organisation_id
        if user_org_id:
            db = current.db
            s3db = current.s3db
            ortable = s3db.org_organisation_region
            link = db(ortable.organisation_id == user_org_id).select(ortable.region_id,
                                                                     cache = s3db.cache,
                                                                     limitby = (0, 1)
                                                                     ).first()
            if link:
                region_id = link.region_id
                # Find Sub regions (just 1 level needed)
                rtable = s3db.org_region
                query = (rtable.parent == region_id) & \
                        (rtable.deleted == False)
                subregions = db(query).select(rtable.id)
                if subregions:
                    region_ids = [region.id for region in subregions]
                    region_ids.append(region_id)
                else:
                    region_ids = [region_id]
                return region_ids
        else:
            # no default
            return {}

    # -------------------------------------------------------------------------
    # Org-dependent settings
    # => lazy settings because they require user authentication and we want them to
    #    work across multiple controllers (inc menus) without too much code
    #
    def auth_realm_entity_types(default):
        """ Which entity types to use as realm entities in role manager """

        auth = current.auth
        if auth.s3_has_role(auth.get_system_roles().ADMIN) or \
           current.auth.root_org_name() == NZRC:
            return list(default) + ["po_area"]
        return default

    settings.auth.realm_entity_types = auth_realm_entity_types

    #def deploy_alerts(default):
    #    """ Whether the system is used to send Alerts """

    #    if _is_asia_pacific():
    #        return False
    #    return default

    #settings.deploy.alerts = deploy_alerts

    #def deploy_cc_groups(default):
    #    """ Which Groups to cc: on Deployment Alerts """

    #    if _is_asia_pacific():
    #        return ["RDRT Focal Points"]
    #    return default

    #settings.deploy.cc_groups = deploy_cc_groups

    def deploy_member_filters_ap():
        """
            AP RDRT:
            Unified Filter Widgets for 'Summary' & 'Select Recipients'
        """

        from s3 import S3DateFilter, S3HierarchyFilter, S3LocationFilter, S3OptionsFilter, S3TextFilter

        s3db = current.s3db
        stable = s3db.hrm_skill
        sttable = s3db.hrm_skill_type
        query = (stable.deleted == False) & \
                (stable.skill_type_id == sttable.id) & \
                (sttable.name == "RDRT_AP")
        skills = current.db(query).select(stable.id,
                                          stable.name,
                                          )
        aprdrt_skills = {skill.id:skill.name for skill in skills}

        filter_widgets = [S3TextFilter(["person_id$first_name",
                                        "person_id$middle_name",
                                        "person_id$last_name",
                                        "person_id$email.value",
                                        ],
                                       label = T("Search"),
                                       ),
                          S3HierarchyFilter("organisation_id",
                                            leafonly = False,
                                            ),
                          S3LocationFilter("location_id",
                                           label = T("Location"),
                                           hidden = True,
                                           ),
                          S3OptionsFilter("person_id$competency.skill_id",
                                           label = T("Skill"),
                                           options = aprdrt_skills,
                                           hidden = True,
                                           ),
                          S3OptionsFilter("person_id$language.language",
                                           label = T("Language"),
                                           hidden = True,
                                           ),
                          S3OptionsFilter("person_id$gender",
                                           label = T("Gender"),
                                           hidden = True,
                                           ),
                          S3DateFilter("available",
                                       label = T("Available for Deployment"),
                                       # Use custom selector to prevent automatic
                                       # parsing (which would result in an error)
                                       selector = "available",
                                       hide_time = True,
                                       hidden = True,
                                       ),
                          S3DateFilter("human_resource_id:deploy_assignment.start_date",
                                       label = T("Deployed"),
                                       hide_time = True,
                                       hidden = True,
                                       ),
                          ]

        return filter_widgets

    def deploy_member_filters(default):
        """
            Custom set of filter_widgets for members (hrm_human_resource),
            used in custom methods for member selection, e.g. deploy_apply
            or deploy_alert_select_recipients
        """

        if _is_asia_pacific():
            filter_widgets = deploy_member_filters_ap()
            return filter_widgets
        return default

    settings.deploy.member_filters = deploy_member_filters

    def hide_third_gender(default):
        """ Whether to hide the third person gender """

        root_org = current.auth.root_org_name()
        if root_org == NRCS:
            return False
        return True

    settings.pr.hide_third_gender = hide_third_gender

    def location_filter_bulk_select_option(default):
        """ Whether to show a bulk select option in location filters """

        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            return True
        return default

    settings.ui.location_filter_bulk_select_option = location_filter_bulk_select_option

    def mandatory_last_name(default):
        """ Whether the Last Name is Mandatory """

        auth = current.auth
        root_org = auth.root_org_name()
        if root_org in (ARCS, IRCS, CRMADA):
            return False
        elif auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER")):
            return False
        return True

    settings.L10n.mandatory_lastname = mandatory_last_name

    def hrm_course_types(default):
        """ Which course types are used """

        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            return {#1: T("Staff"),
                    2: T("Volunteers"),
                    #3: T("Deployables"),
                    4: T("Members"),
                    }
        else:
            # Not used
            return default

    settings.hrm.course_types = hrm_course_types

    def hrm_event_course_mandatory(default):
        """ Whether (Training) Event Courses are mandatory """

        if current.auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER")):
            return False
        else:
            # True
            return default

    settings.hrm.event_course_mandatory = hrm_event_course_mandatory

    #def hrm_event_programme(default):
    #    """ Whether (Training) Events link to Programmes """

    #    if current.auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
    #        # Link to Programmes
    #        return True
    #    else:
    #        # False
    #        return default

    #settings.hrm.event_programme = hrm_event_programme

    def hrm_event_site(default):
        """ Whether (Training) Events use a Site (or Location) """

        auth = current.auth
        if not auth.s3_has_role("ADMIN") and \
           auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER")):
            # Use a Location (e.g. Country or Country/L1)
            return False
        else:
            # True: Use Site
            return default

    settings.hrm.event_site = hrm_event_site

    def hrm_event_types(default):
        """ Whether (Training) Events have multiple Types to choose from """

        if current.auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
            # Use Event Types
            return True
        else:
            # False: No
            return default

    settings.hrm.event_types = hrm_event_types

    def hrm_use_certificates(default):
        """ Whether to use Certificates """

        root_org = current.auth.root_org_name()
        if root_org == IRCS:
            if current.request.controller == "vol":
                return True
            else:
                return False
        elif root_org == VNRC:
            return False
        return True

    settings.hrm.use_certificates = hrm_use_certificates

    def hrm_use_code(default):
        """ Whether to use Staff-ID/Volunteer-ID """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, IRCS):
            return True # use for both staff and volunteers
        return False

    settings.hrm.use_code = hrm_use_code

    def hrm_use_skills(default):
        """ Whether to use Skills """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, CRMADA, IRCS, PMI, VNRC):
            return True
        return False

    settings.hrm.use_skills = hrm_use_skills

    def hrm_teams(default):
        """ Whether to use Teams """

        if current.request.controller == "vol":
            root_org = current.auth.root_org_name()
            if root_org == IRCS:
                return False
        return default

    settings.hrm.teams = hrm_teams

    def hrm_teams_orgs(default):
        """ Whether Teams should link to 1 or more Orgs """

        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            # Multiple Orgs
            return 2
        # Single Org
        return default

    settings.hrm.teams_orgs = hrm_teams_orgs

    def hrm_trainings_external(default):
        """ Whether Training Courses should be split into Internal & External """

        root_org = current.auth.root_org_name()
        if root_org == CRMADA:
            return True
        return False

    settings.hrm.trainings_external = hrm_trainings_external

    def hrm_vol_active(default):
        """ Whether & How to track Volunteers as Active """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, IRCS):
            # Simple checkbox
            return True
        elif root_org in (CVTL, PMI, PRC):
            # Use formula based on hrm_programme
            return vol_programme_active
        elif root_org in (CRMADA, ):
            # Use formula based on vol_activity
            return vol_activity_active
        return False

    settings.hrm.vol_active = hrm_vol_active

    def pr_person_availability_options(default):

        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            # Doesn't seem used anyway...perhaps a bug in hrm_Record?
            return {1: T("No Restrictions"),
                    2: T("Weekends only"),
                    3: T("School Holidays only"),
                    }
        elif root_org == CRMADA:
            return {1: "%s, %s" % (T("Frequent"), T("1-2 times per week")),
                    2: "%s, %s" % (T("Sometimes"), T("When needed")),
                    3: "%s, %s" % (T("Projects"), T("1-3 times per month")),
                    4: T("Once per month"),
                    5: T("Exceptional Cases"),
                    6: T("Other"),
                    }

        # Default to Off
        return None

    settings.pr.person_availability_options = pr_person_availability_options

    def hrm_vol_availability_tab(default):
        """ Whether to show Volunteer Availability Tab """

        root_org = current.auth.root_org_name()
        if root_org == CRMADA:
            return True
        # Default to Off
        return None

    settings.hrm.vol_availability_tab = hrm_vol_availability_tab

    def hrm_vol_departments(default):
        """ Whether to use Volunteer Departments """

        root_org = current.auth.root_org_name()
        if root_org == IRCS:
            return True
        return False

    settings.hrm.vol_departments = hrm_vol_departments

    def hrm_vol_experience(default):
        """ What type(s) of experience to use for Volunteers """

        root_org = current.auth.root_org_name()
        if root_org in (IRCS, PMI, VNRC):
            return "both"
        elif root_org == CRMADA:
            return "activity"
        return default

    settings.hrm.vol_experience = hrm_vol_experience

    def hrm_vol_roles(default):
        """ Whether to use Volunteer Roles """

        root_org = current.auth.root_org_name()
        if root_org in (IRCS, VNRC):
            return False
        return True

    settings.hrm.vol_roles = hrm_vol_roles

    def pr_name_format(default):
        """ Format to use to expand peoples' names """

        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            return "%(last_name)s %(middle_name)s %(first_name)s"
        #elif root_org == CRMADA:
        #    return "%(last_name)s %(first_name)s %(middle_name)s"
        return default

    settings.pr.name_format = pr_name_format

    def pr_request_father_name(default):
        """ Whether to request Father's Name in AddPersonWidget2 """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, BRCS, IRCS):
            return True
        return False

    settings.pr.request_father_name = pr_request_father_name

    def pr_request_grandfather_name(default):
        """ Whether to request GrandFather's Name in AddPersonWidget2 """

        root_org = current.auth.root_org_name()
        if root_org in (ARCS, BRCS, IRCS):
            return True
        return False

    settings.pr.request_grandfather_name = pr_request_grandfather_name

    def training_instructors(default):
        """ Whether to track internal/external training instructors """

        root_org = current.auth.root_org_name()
        if root_org == NRCS:
            return "both"

        elif current.auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
            # Use Status field
            return None

        # External
        return default

    settings.hrm.training_instructors = training_instructors

    #def ui_autocomplete_delay(default):
    #    """ Delay in milliseconds before autocomplete starts searching """
    #    root_org = current.auth.root_org_name()
    #    if root_org == ARCS:
    #        return 800
    #    return default
    #settings.ui.autocomplete_delay = ui_autocomplete_delay

    def membership_types(default):
        """ Whether to use Membership Types """

        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            return False
        return True

    settings.member.membership_types = membership_types

    # -------------------------------------------------------------------------
    def customise_asset_asset_controller(**attr):

        tablename = "asset_asset"

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_and_children_default_filter,
                              tablename = tablename)

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
            ns_only(tablename,
                    required = True,
                    branches = True,
                    limit_filter_opts = True,
                    )

            # Set the NS filter as Visible so that the default filter works
            filter_widgets = current.s3db.get_config(tablename, "filter_widgets")
            for widget in filter_widgets:
                if widget.field == "organisation_id":
                    widget.opts.hidden = False
                    break

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_asset_asset_controller = customise_asset_asset_controller

    # -------------------------------------------------------------------------
    def customise_asset_asset_resource(r, tablename):

        # Load standard model
        s3db = current.s3db
        table = s3db.asset_asset

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
                                        fields = ("item_id",
                                                  "quantity",
                                                  "sn",
                                                  # These are too wide for the screen & hence hide the S3PopupLinks
                                                  #"supply_org_id",
                                                  #"purchase_date",
                                                  #"purchase_price",
                                                  #"purchase_currency",
                                                  "comments",
                                                  ),
                                        ),
                                    S3SQLInlineComponent(
                                        "group",
                                        label = T("Team"),
                                        fields = [("", "group_id")],
                                        filterby = {"field": "group_type",
                                                    "options": 3,
                                                    },
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

    settings.customise_asset_asset_resource = customise_asset_asset_resource

    # -------------------------------------------------------------------------
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

        # Different settings for different NS
        # Not possible for registration form, so fake with language!
        root_org = current.auth.root_org_name()
        if root_org == VNRC or current.session.s3.language == "vi":
            # Too late to do via settings
            #settings.org.site_label = "Office/Center"
            current.db.auth_user.site_id.label = T("Office/Center")

        return attr

    settings.customise_auth_user_controller = customise_auth_user_controller

    # -------------------------------------------------------------------------
    def dc_rheader(r, tabs=None):
        """
            Custom rheader for Bangkok CCST
        """

        if r.representation != "html":
            return None

        from s3 import S3ResourceHeader, s3_rheader_resource

        s3db = current.s3db
        tablename, record = s3_rheader_resource(r)
        if tablename != r.tablename:
            resource = s3db.resource(tablename, id=record.id)
        else:
            resource = r.resource

        rheader = None
        rheader_fields = []

        if record:

            if tablename == "dc_template":

                tabs = ((T("Basic Details"), None),
                        (T("Sections"), "section"),
                        (T("Questions"), "question"),
                        )

                rheader_fields = (["name"],
                                  )

            elif tablename == "dc_response":

                auth = current.auth
                if not auth.s3_has_role("ADMIN") and \
                       auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
                    # MFP shouldn't see the Individual Answers
                    tabs = []
                else:
                    tabs = (#(T("Basic Details"), None, {"native": 1}),
                            (T("Answers"), "answer"),
                            #(T("Attachments"), "document"),
                            )

                from gluon import A, URL

                db = current.db

                def contacts(record):
                    ptable = s3db.pr_person
                    ctable = s3db.pr_contact
                    query = (ptable.id == record.person_id) & \
                            (ptable.pe_id == ctable.pe_id) & \
                            (ctable.deleted == False)
                    data = db(query).select(ctable.value,
                                            ctable.contact_method,
                                            ctable.priority,
                                            orderby = ~ctable.priority,
                                            )
                    if data:
                        # Prioritise Phone then Email
                        email = None
                        other = None
                        for contact in data:
                            if contact.contact_method == "SMS":
                                return contact.value
                            elif contact.contact_method == "Email":
                                if not email:
                                    email = contact.value
                            else:
                                if not other:
                                    other = contact.value
                        return email or other
                    else:
                        # @ToDo: Provide an Edit button
                        return A(T("Add"))

                etable = s3db.hrm_training_event
                ltable = s3db.dc_target_event
                ttable = s3db.dc_target
                query = (ttable.id == record.target_id) & \
                        (ltable.target_id == ttable.id) & \
                        (ltable.training_event_id == etable.id)
                training_event = db(query).select(ttable.date,
                                                  etable.id,
                                                  etable.name,
                                                  etable.start_date,
                                                  etable.location_id,
                                                  limitby = (0, 1),
                                                  ).first()

                def event_name(record):
                    try:
                        return A(training_event["hrm_training_event"].name,
                                 _href=URL(c="hrm", f="training_event", args=training_event["hrm_training_event"].id),
                                 )
                    except:
                        return current.messages["NONE"]

                def event_location(record):
                    try:
                        location_id = training_event["hrm_training_event"].location_id
                    except:
                        return current.messages["NONE"]
                    return etable.location_id.represent(location_id)

                def event_date(record):
                    try:
                        date = training_event["hrm_training_event"].start_date
                    except:
                        return current.messages["NONE"]
                    return etable.start_date.represent(date)

                def survey_date(record):
                    try:
                        date = training_event["dc_target"].date
                    except:
                        return current.messages["NONE"]
                    return ttable.date.represent(date)

                rheader_fields = [[(T("Event Name"), event_name)],
                                  [(T("Event Location"), event_location)],
                                  [(T("Event Date"), event_date)],
                                  #["template_id"],
                                  #["location_id"],
                                  [(T("Survey Date"), survey_date)],
                                  [(T("Response Date"), "date")],
                                  ]
                if current.auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
                    rheader_fields += [["person_id"],
                                       [(T("Contact Details"), contacts)],
                                       ]

            elif tablename == "dc_target":

                tabs = ((T("Basic Details"), None),
                        (T("Report"), "results"),
                        (T("Responses"), "response"),
                        )

                db = current.db

                etable = s3db.hrm_training_event
                ltable = s3db.dc_target_event
                query = (ltable.target_id == record.id) & \
                        (ltable.training_event_id == etable.id)
                training_event = db(query).select(etable.id,
                                                  etable.name,
                                                  etable.start_date,
                                                  etable.location_id,
                                                  limitby = (0, 1),
                                                  ).first()

                def event_name(record):
                    try:
                        return training_event.name
                    except:
                        return current.messages["NONE"]

                def event_location(record):
                    try:
                        location_id = training_event.location_id
                    except:
                        return current.messages["NONE"]
                    return etable.location_id.represent(location_id)

                def event_date(record):
                    try:
                        date = training_event.start_date
                    except:
                        return current.messages["NONE"]
                    return etable.start_date.represent(date)

                rheader_fields = [[(T("Event Name"), event_name)],
                                  [(T("Event Location"), event_location)],
                                  [(T("Event Date"), event_date)],
                                  #["template_id"],
                                  #["location_id"],
                                  [(T("Survey Date"), "date")],
                                  [(T("Survey Template"), "template_id")],
                                  ]

            rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                             table = resource.table,
                                                             record = record,
                                                             )

            if tablename == "dc_target":
                if r.component_name == "response" and r.method == "create":
                    # Simplified UI
                    return None

                from gluon import A, URL

                try:
                    training_event_id = training_event.id
                except:
                    pass
                else:
                    button = A(T("Notify Participants"),
                               _href = URL(c = "hrm",
                                           f = "training_event",
                                           args = [training_event_id, "notify"]
                                           ),
                               _id = "notify_parts",
                               _class = "action-btn"
                               )
                    script = "S3.confirmClick('#notify_parts', '%s')" % \
                        T("Do you want to notify participants to complete survey?")
                    current.response.s3.jquery_ready.append(script)
                    rheader.insert(-1, button)

            return rheader

    # -------------------------------------------------------------------------
    def dc_answer_onaccept(form):
        """
            Set the Date of the Response when the Answers are added
        """

        #record_id = form.vars.get("id")

        # Retrieve the tablename set in prep
        dtablename = current.response.s3.dc_dtablename
        s3db = current.s3db
        dtable = s3db[dtablename]
        rtable = s3db.dc_response
        query = (rtable.id == dtable.response_id)
        response = current.db(query).select(rtable.id,
                                            limitby = (0, 1)
                                            ).first()

        response.update_record(date = current.request.utcnow)

    # -------------------------------------------------------------------------
    def dc_target_check(target_id):
        """
            Check whether a Survey has been Approved/Rejected & notify OM if not

            @param target_id: Target record_id
        """

        #from gluon import URL
        from s3 import S3DateTime, s3_str

        db = current.db
        s3db = current.s3db

        # Read Survey Record
        ttable = s3db.dc_target
        ltable = s3db.dc_target_event
        etable = s3db.hrm_training_event
        query = (ttable.id == target_id)
        left = etable.on((ttable.id == ltable.target_id) & \
                         (etable.id == ltable.training_event_id))
        survey = db(query).select(ttable.approved_by,
                                  ttable.deleted,
                                  etable.name,
                                  etable.location_id,
                                  etable.start_date,
                                  left = left,
                                  limitby = (0, 1)
                                  ).first()

        if not survey:
            return

        if survey["dc_target"].deleted:
            # Presumably it was Rejected
            return

        if survey["dc_target"].approved_by:
            # Survey was Approved
            return

        # List of recipients, grouped by language
        # Recipients: OM
        languages = {}

        utable = db.auth_user
        gtable = db.auth_group
        mtable = db.auth_membership
        ltable = s3db.pr_person_user
        query = (utable.id == mtable.user_id) & \
                (mtable.group_id == gtable.id) & \
                (gtable.uuid == "EVENT_OFFICE_MANAGER") & \
                (ltable.user_id == utable.id)
        users = db(query).select(ltable.pe_id,
                                 utable.language,
                                 distinct = True,
                                 )
        for user in users:
            language = user["auth_user.language"]
            if language in languages:
                languages[language].append(user["pr_person_user.pe_id"])
            else:
                languages[language] = [user["pr_person_user.pe_id"]]

        # Build Message
        event = survey["hrm_training_event"]
        event_date = event.start_date
        location_id = event.location_id
        #url = "%s%s" % (settings.get_base_public_url(),
        #                URL(c="dc", f="target", args=[target_id, "review"]),
        #                )
        subject_T = T("Post-Event Survey hasn't been Approved/Rejected")
        message = "The post-Event Survey for %(event_name)s on %(date)s in %(location)s has not been Approved or Rejected" % \
                    {"date": "%(date)s", # Localise per-language
                     "event_name": event.name,
                     "location": "%(location)s", # Localise per-language
                     #"url": url,
                     }
        message_T = T(message)

        # Send Localised Mail(s)
        send_email = current.msg.send_by_pe_id
        session_s3 = current.session.s3
        date_represent = S3DateTime.date_represent # We want Dates not datetime which etable.start_date uses
        location_represent = s3db.gis_LocationRepresent()
        for language in languages:
            T.force(language)
            subject = s3_str(subject_T)
            session_s3.language = language # for date_represent
            message = s3_str(message_T) % {"date": date_represent(event_date),
                                           "location": location_represent(location_id),
                                           }
            users = languages[language]
            for pe_id in users:
                send_email(pe_id,
                           subject = subject,
                           message = message,
                           )

        # NB No need to restore UI language as this is run as an async task w/o UI
        return

    settings.tasks.dc_target_check = dc_target_check

    # -------------------------------------------------------------------------
    def dc_target_report(target_id):
        """
            Notify EO & MFP that a Survey Report is ready

            @param target_id: Target record_id
        """

        from gluon import URL
        from s3 import S3DateTime, s3_str

        db = current.db
        s3db = current.s3db

        # Read Survey Record
        ttable = s3db.dc_target
        ltable = s3db.dc_target_event
        etable = s3db.hrm_training_event
        query = (ttable.id == target_id)
        left = etable.on((ttable.id == ltable.target_id) & \
                         (etable.id == ltable.training_event_id))
        survey = db(query).select(ttable.approved_by,
                                  ttable.deleted,
                                  etable.created_by,
                                  etable.name,
                                  etable.location_id,
                                  etable.start_date,
                                  left = left,
                                  limitby = (0, 1)
                                  ).first()

        if not survey:
            return

        if survey["dc_target"].deleted:
            # Presumably it was Rejected
            return

        # List of recipients, grouped by language
        # Recipients: EO, MFP
        languages = {}

        event = survey["hrm_training_event"]

        utable = db.auth_user
        gtable = db.auth_group
        mtable = db.auth_membership
        ltable = s3db.pr_person_user
        query = ((utable.id == event.created_by) | \
                 ((utable.id == mtable.user_id) & \
                  (mtable.group_id == gtable.id) & \
                  (gtable.uuid == "EVENT_MONITOR"))) & \
                (ltable.user_id == utable.id)
        users = db(query).select(ltable.pe_id,
                                 utable.language,
                                 distinct = True,
                                 )
        for user in users:
            language = user["auth_user.language"]
            if language in languages:
                languages[language].append(user["pr_person_user.pe_id"])
            else:
                languages[language] = [user["pr_person_user.pe_id"]]

        # Build Message
        event_date = event.start_date
        location_id = event.location_id
        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="dc", f="target", args=[target_id, "results"]),
                        )
        subject_T = T("Post-Event Survey Report is Ready")
        message = "The Report on the post-Event Survey for %(event_name)s on %(date)s in %(location)s is Ready: %(url)s" % \
                    {"date": "%(date)s", # Localise per-language
                     "event_name": event.name,
                     "location": "%(location)s", # Localise per-language
                     "url": url,
                     }
        message_T = T(message)

        # Send Localised Mail(s)
        send_email = current.msg.send_by_pe_id
        session_s3 = current.session.s3
        date_represent = S3DateTime.date_represent # We want Dates not datetime which etable.start_date uses
        location_represent = s3db.gis_LocationRepresent()
        for language in languages:
            T.force(language)
            subject = s3_str(subject_T)
            session_s3.language = language # for date_represent
            message = s3_str(message_T) % {"date": date_represent(event_date),
                                           "location": location_represent(location_id),
                                           }
            users = languages[language]
            for pe_id in users:
                send_email(pe_id,
                           subject = subject,
                           message = message,
                           )

        # NB No need to restore UI language as this is run as an async task w/o UI
        return

    settings.tasks.dc_target_report = dc_target_report

    # -------------------------------------------------------------------------
    def customise_dc_response_controller(**attr):
        """
            Only used by Bangkok CCST currently
        """

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)

            # Need POST too to set Date properly
            #if r.interactive:
            if not current.auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
                # Simplify Interface
                menu = current.menu
                menu.breadcrumbs = None
                menu.main = ""
                menu.options = None
                s3.crud_strings["dc_response"]["title_display"] = ""
                if r.component_name == "answer":
                    # CRUD Strings
                    tablename = r.component.tablename
                    s3.crud_strings[tablename].msg_record_created = T("Thank you for taking this survey and helping us to increase the quality of our trainings.")
                    current.s3db.configure(tablename,
                                           create_onaccept = dc_answer_onaccept,
                                           )
                    # Store tablename for onaccept
                    s3.dc_dtablename = tablename
                #elif r.method == "create":
                #    target_id = r.get_vars.get("target_id")
                #    if target_id:
                #        s3db = current.s3db
                #        table = s3db.dc_response
                #        table.target_id.default = target_id
                #        ttable = s3db.dc_target
                #        target = current.db(ttable.id == target_id).select(ttable.template_id,
                #                                                           limitby = (0, 1)
                #                                                           ).first()
                #        try:
                #            table.template_id.default = target.template_id
                #        except:
                #            # Template not found?
                #            pass
                #        # Auto-submit form
                #        script = '''$('form').submit()'''
                #        s3.jquery_ready.append(script)
                #    else:
                #        # Block create
                #        current.response.error = T("Survey not specified, please click on original link to take survey")
                #        current.s3db.configure("dc_response",
                #                               insertable = False,
                #                               )
            elif r.interactive:
                # Filter out date is None (unfilled responses)
                from s3 import FS
                r.resource.add_filter(FS("date") != None)

                current.s3db.configure("dc_response",
                                       insertable = False,
                                       list_fields = [(T("Event"), "target_id$training_event__link.training_event_id"),
                                                      "date",
                                                      "person_id",
                                                      ],
                                       )

            return result
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and r.component_name == "answer":
                script = '''$('#component').prepend('<div>%s<br>%s</div>')''' % \
                    (T("The questionnaire is available in all SEA languages, please change the language to your need on the upper-right corner of your screen."),
                     T("Do this before filling in the data."))
                s3.jquery_ready.append(script)

            return output
        s3.postp = custom_postp

        attr["rheader"] = dc_rheader

        return attr

    settings.customise_dc_response_controller = customise_dc_response_controller

    # -------------------------------------------------------------------------
    def customise_dc_response_resource(r, tablename):
        """
            Currently used by
                * Bangkok CCST
                * AP RDRT
        """

        from s3 import S3DateTime

        table = current.s3db.dc_response
        table.location_id.readable = table.location_id.writable = False
        table.organisation_id.readable = table.organisation_id.writable = False
        table.comments.readable = table.comments.writable = False
        table.date.represent = S3DateTime.date_represent # Just Date not datetime
        table.date.writable = False
        table.person_id.writable = False
        table.person_id.comment = None

        current.response.s3.crud_strings["dc_response"] = Storage(
            label_create = T("Take Survey"),
            title_display = T("Response Details"),
            title_list = T("Responses"),
            title_update = T("Edit Response"),
            title_upload = T("Import Responses"),
            label_list_button = T("List Responses"),
            label_delete_button = T("Delete Response"),
            msg_record_created = T("Response created"),
            msg_record_modified = T("Response updated"),
            msg_record_deleted = T("Response deleted"),
            msg_list_empty = T("No Responses currently registered"))

    settings.customise_dc_response_resource = customise_dc_response_resource

    # -------------------------------------------------------------------------
    def customise_dc_target_controller(**attr):
        """
            Only used by Bangkok CCST currently
        """

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)

            if r.interactive and r.component_name == "response":

                current.s3db.configure("dc_response",
                                       insertable = False,
                                       list_fields = ["person_id",
                                                      (T("Date Responded"), "date"),
                                                      ],
                                       )

            return result
        s3.prep = custom_prep

        # MFP should NOT be able to see individual responses
        # Custom postp
        #standard_postp = s3.postp
        #def custom_postp(r, output):
        #    # Call standard postp
        #    if callable(standard_postp):
        #        output = standard_postp(r, output)

        #    if r.interactive and r.component_name == "response":
        #        from gluon import URL
        #        from s3 import S3CRUD
        #        open_url = URL(f="respnse", args = ["[id]", "answer"])
        #        S3CRUD.action_buttons(r, read_url=open_url, update_url=open_url)

        #    return output
        #s3.postp = custom_postp

        attr["rheader"] = dc_rheader

        return attr

    settings.customise_dc_target_controller = customise_dc_target_controller

    # -------------------------------------------------------------------------
    def hrm_notify_participants(training_event_id, redirect=True):
        """
            * Notify Participants to fill out the Survey
            - exclude Observers
            * Update Date of Survey
            * Schedule Task to send Report of results
        """

        import time
        from gluon import URL
        from gluon.utils import web2py_uuid
        from s3 import s3_fullname, s3_str, S3DateTime

        db = current.db
        auth = current.auth
        s3db = current.s3db

        # Read the Event Details
        etable = s3db.hrm_training_event
        event = db(etable.id == training_event_id).select(etable.name,
                                                          etable.start_date,
                                                          etable.location_id,
                                                          limitby = (0, 1),
                                                          ).first()
        event_name = event.name
        event_date = event.start_date
        event_location = event.location_id

        # Find the Target (for URLs & to update Date)
        dtable = s3db.dc_target
        ltable = s3db.dc_target_event
        query = (ltable.training_event_id == training_event_id) & \
                (ltable.target_id == dtable.id)
        target = db(query).select(dtable.id,
                                  dtable.template_id,
                                  dtable.language,
                                  limitby = (0, 1),
                                  ).first()
        target_id = target.id
        template_id = target.template_id
        default_language = target.language

        # Update Survey Date
        now = current.request.utcnow
        target.update_record(date = now)

        # Build list of people to notify
        # - including their language
        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        htable = s3db.hrm_human_resource
        ttable = s3db.hrm_training
        utable = s3db.auth_user
        ltable = s3db.pr_person_user
        query = (ttable.training_event_id == training_event_id) & \
                (ttable.role != 3) & \
                (ttable.person_id == ptable.id) & \
                (ttable.deleted == False)
        left = [ltable.on(ltable.pe_id == ptable.pe_id),
                utable.on(utable.id == ltable.user_id),
                htable.on(htable.person_id == ptable.id),
                ctable.on((ctable.pe_id == ptable.pe_id) & (ctable.contact_method=="EMAIL") & (ctable.deleted == False)),
                ]
        # Exclude participants that we have already notified
        rtable = s3db.dc_response
        nquery = (rtable.target_id == target_id) & \
                 (rtable.template_id == template_id) & \
                 (rtable.deleted == False)
        notified = db(nquery).select(rtable.person_id)
        exclude = [n.person_id for n in notified]
        if exclude:
            query &= (~ptable.id.belongs(exclude))
        persons = db(query).select(ptable.id,
                                   ptable.pe_id,
                                   ptable.first_name,
                                   ptable.middle_name,
                                   ptable.last_name,
                                   ptable.gender,
                                   ctable.value,
                                   htable.organisation_id,
                                   htable.site_id,
                                   utable.id,
                                   utable.language,
                                   left = left,
                                   distinct = True,
                                   )

        # Build localised mail for each language
        session = current.session
        session_s3 = session.s3
        ui_language = session_s3.language
        subject = "Placeholder Subject"
        line1 = "You are receiving this email as a participant of %(event_name)s held in %(location)s on %(date)s."
        line2 = "We have 8 simple questions for you, this should not take more than 15mn of your time."
        line3 = "The information collected through this questionnaire will be treated as confidential."
        click = "Please click this link to complete the survey"
        line4 = "Thank you for your participation."
        translations = {}
        languages = list({p["auth_user.language"] for p in persons})
        if default_language not in languages:
            languages.append(default_language)
        date_represent = S3DateTime.date_represent # We want Dates not datetime which etable.start_date uses
        location_represent = s3db.gis_LocationRepresent()
        for l in languages:
            T.force(l)
            session_s3.language = l # for date_represent
            translations[l] = {"s": s3_str(T(subject)),
                               1: s3_str(T(line1)),
                               2: s3_str(T(line2)),
                               3: s3_str(T(line3)),
                               "c": s3_str(T(click)),
                               4: s3_str(T(line4)),
                               "l": location_represent(event_location),
                               "d": date_represent(event_date),
                               }

        # Send localised email to each person
        # @ToDo: Group by Language?
        #db_type = settings.get_database_type()
        #if db_type == "postgres":
        #    try:
        #        from psycopg2 import IntegrityError
        #    except ImportError
        #        from gluon.contrib.pg8000 import IntegrityError
        #elif db_type == "sqlite":
        #    from sqlite3 import IntegrityError
        #else:
        #    # MySQL
        #    try:
        #        from MySQLdb import IntegrityError
        #    except ImportError:
        #        from gluon.contrib.pymysql import IntegrityError
        errors = {}
        success = 0
        response = current.response
        s3 = response.s3
        s3.bulk = True # Don't send a Welcome Message for new users as we send our own message instead
        send_email = current.msg.send_by_pe_id
        rtable.date.default = None # Set the date when we answer
        rinsert = rtable.insert
        uinsert = utable.insert
        approve_user = auth.s3_approve_user
        public_url = settings.get_base_public_url()
        update_super = s3db.update_super
        for p in persons:
            person = p["pr_person"]
            person_id = person.id
            user_id = p.get("auth_user.id")
            if user_id:
                NEW_USER = False
                lang = p.get("auth_user.language")
                T.force(lang)
            else:
                # No User Account exists, so create one
                NEW_USER = True
                email = p.get("pr_contact.value")
                if not email:
                    # Cannot create User account for this person
                    continue
                first_name = person.first_name
                last_name = person.last_name
                # Check if there is already a User Account with this email
                exists = db(utable.email == email).select(utable.id,
                                                          limitby = (0, 1)
                                                          ).first()
                if exists:
                    # Log error
                    errors[person_id] = {#"error": "Cannot create User as there is already a User Account with this email address",
                                         "first_name": first_name,
                                         "last_name": last_name,
                                         }
                    # Continue to notify the rest of the participants
                    continue

                hr = p.get("hrm_human_resource")
                reset_password_key = str(int(time.time())) + "-" + web2py_uuid() # format from auth.email_reset_password()
                # Fallback language based on Target
                lang = default_language
                user = Storage(first_name = first_name,
                               last_name = last_name,
                               language = lang,
                               email = email,
                               organisation_id = hr.organisation_id,
                               site_id = hr.site_id,
                               reset_password_key = reset_password_key,
                               )
                # Commit, because we may need to revert
                #db.commit()
                #try:
                user_id = uinsert(**user)
                #except IntegrityError, e:
                #    # So far this has always been: IntegrityError: duplicate key value violates unique constraint "auth_user_email_key"
                #    db.rollback()
                #    # Log error
                #    errors.append({person_id: {"error": e,
                #                               "first_name": first_name,
                #                               "last_name": last_name,
                #                               }})
                #    # Continue to notify the rest of the participants
                #    continue
                user.id = user_id
                approve_user(user)

            # Create response (so that User only needs oacl UPDATE not uacl READ|CREATE
            record = {"target_id": target_id,
                      "template_id": template_id,
                      "person_id": person_id,
                      "owned_by_user": user_id,
                      }
            response_id = rinsert(**record)
            record["id"] = response_id
            update_super(rtable, record) # doc_entity

            url = URL(c="dc", f="respnse",
                      args = [response_id, "answer"],
                      )
            if NEW_USER:
                url = "%s%s" % (public_url,
                                URL(c="default", f="user",
                                    args = ["reset_password"],
                                    vars= {"key": reset_password_key,
                                           "_next": url,
                                           },
                                    ),
                                )
            else:
                url = "%s%s" % (public_url,
                                url,
                                )

            if lang == "vi":
                gender = person.gender
                if gender == 3:
                    # Male
                    line1 = s3_str(T("Dear Brother %(person_name)s")) %  {#"person_title" : p.title,
                                                                          "person_name" : s3_fullname(person),
                                                                          }
                elif gender == 2:
                    # Female
                    line1 = s3_str(T("Dear Sister %(person_name)s")) % {#"person_title":  p.title,
                                                                        "person_name" : s3_fullname(person),
                                                                        }
                else:
                    # Unknown, Trans, etc
                    line1 = s3_str(T("Dear %(person_name)s")) % {#"person_title" : p.title,
                                                                 "person_name" : s3_fullname(person),
                                                                 }
            else:
                # @ToDo: Automate title in some cases?
                line1 = s3_str(T("Dear %(person_name)s")) % {#"person_title": p.title,
                                                             "person_name" : s3_fullname(person),
                                                             }
            translation = translations[lang]
            message = "%s\n%s\n%s\n%s\n\n%s\n%s\n\n%s" % (line1,
                                                          translation[1] % dict(event_name = event_name,
                                                                                location = translation["l"],
                                                                                date = translation["d"],
                                                                                ),
                                                          translation[2],
                                                          translation[3],
                                                          "%s:" % translation["c"],
                                                          url,
                                                          translation[4],
                                                          )
            send_email(person.pe_id,
                       subject = translation["s"],
                       message = message,
                       )
            success += 1

        s3.bulk = False

        # Restore language for UI
        session_s3.language = ui_language
        T.force(ui_language)

        # Communicate success / errors
        if errors:
            from gluon import A
            bad = ""
            for e in errors:
                error = errors[e]
                new_error = A("%s %s" % (error["first_name"],
                                         error["last_name"]),
                              _href=URL(c="hrm", f="person", args=e))
                if bad:
                    bad = "%s, %s" % (bad, new_error)
                else:
                    bad = new_error
            warning = "%s: %s" % (s3_str(T("%i Notifications sent, but these participants couldn't be notified as User Accounts already exist with these email addresses")) % success,
                                  bad)
            if redirect:
                session.warning = warning
            else:
                response.warning = warning
        elif success:
            if redirect:
                session.confirmation = s3_str(T("%i Notifications sent!")) % success
            else:
                response.confirmation = s3_str(T("%i Notifications sent!")) % success
        else:
            if redirect:
                session.information = T("No Notifications needed sending!")
            else:
                response.information = T("No Notifications needed sending!")

        if success:
            # Schedule Report
            import json
            from dateutil.relativedelta import relativedelta
            ttable = s3db.scheduler_task
            task_name = "settings_task"

            # 1 month reminder
            start_time = now + relativedelta(months = 1)
            args = ["dc_target_report"]
            vars = {"target_id": target_id}
            query = (ttable.task_name == task_name) & \
                    (ttable.args == json.dumps(args)) & \
                    (ttable.vars == json.dumps(vars))
            exists = db(query).select(ttable.id,
                                      ttable.start_time,
                                      limitby = (0, 1)
                                      ).first()
            if exists:
                if exists.start_time != start_time:
                    exists.update_record(start_time = start_time)
            else:
                current.s3task.schedule_task(task_name,
                                             args = args,
                                             vars = vars,
                                             start_time = start_time,
                                             #period = 300,  # seconds
                                             timeout = 300, # seconds
                                             repeats = 1    # run once
                                             )

    # -------------------------------------------------------------------------
    def hrm_training_event_survey(training_event_id, survey_type):
        """
            Notify Event Organiser (EO) that they should consider sending out a Survey

            @param training_event_id: (Training) Event record_id
            @param survey_type: Survey Type (3 month or 6 month currently)
        """

        try:
            import arrow
        except ImportError:
            current.log.error("Arrow library needed for hrm_training_event_survey")
            return

        from gluon import URL
        from s3 import s3_str

        db = current.db
        s3db = current.s3db

        # Read Event Record
        etable = s3db.hrm_training_event
        event = db(etable.id == training_event_id).select(etable.name,
                                                          etable.start_date,
                                                          etable.end_date,
                                                          etable.location_id,
                                                          etable.created_by,
                                                          limitby = (0, 1)
                                                          ).first()

        event_date = event.end_date or event.start_date # Use end_date where-available, otherwise use start_date
        event_date = arrow.get(event_date)
        location_id = event.location_id
        EO = event.created_by

        # Create Survey (unapproved)
        # Default the template
        ttable = s3db.dc_template
        template = db(ttable.name == "Training Evaluation").select(ttable.id,
                                                                   limitby = (0, 1)
                                                                   ).first()
        try:
            template_id = template.id
        except AttributeError:
            current.log.error("Cannot find 'Training Evaluation' template so cannot run hrm_training_event_survey")
            return

        stable = s3db.dc_target
        ltable = s3db.dc_target_event
        target_id = stable.insert(template_id = template_id,
                                  date = None, # Gets set when notifications sent (onapprove here)
                                  owned_by_user = EO,
                                  )
        ltable.insert(training_event_id = training_event_id,
                      target_id = target_id,
                      survey_type = survey_type,
                      )

        # Create Task to check if Survey has been Approved/Rejected
        start_time = arrow.utcnow()
        start_time = start_time.shift(months = 1)
        current.s3task.schedule_task("settings_task",
                                     args = ["dc_target_check"],
                                     vars = {"target_id": target_id},
                                     start_time = start_time.datetime,
                                     #period = 300,  # seconds
                                     timeout = 300, # seconds
                                     repeats = 1    # run once
                                     )

        # List of recipients, grouped by language
        # Recipients: EO (created_by) & MFP(s)
        languages = {}

        utable = db.auth_user
        gtable = db.auth_group
        mtable = db.auth_membership
        ltable = s3db.pr_person_user
        query = ((utable.id == EO) & \
                 (ltable.user_id == utable.id)) | \
                ((utable.id == mtable.user_id) & \
                 (mtable.group_id == gtable.id) & \
                 (gtable.uuid == "EVENT_MONITOR") & \
                 (ltable.user_id == utable.id))
        users = db(query).select(ltable.pe_id,
                                 utable.language,
                                 distinct = True,
                                 )
        for user in users:
            language = user["auth_user.language"]
            if language in languages:
                languages[language].append(user["pr_person_user.pe_id"])
            else:
                languages[language] = [user["pr_person_user.pe_id"]]

        # Build Message
        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="dc", f="target", args=[target_id, "review"]),
                        )
        subject_T = T("Consider sending a post-Event Survey")
        message = "It is now %(date)s since the event %(event_name)s in %(location)s so you should consider creating a survey by visiting this link: %(url)s" % \
                {"date": "%(date)s", # Localise per-language
                 "event_name": event.name,
                 "location": "%(location)s", # Localise per-language
                 "url": url,
                 }
        message_T = T(message)

        # Send Localised Mail(s)
        send_email = current.msg.send_by_pe_id
        location_represent = s3db.gis_LocationRepresent()
        for language in languages:
            T.force(language)
            subject = s3_str(subject_T)
            humanized_date = event_date.humanize(locale=language.replace("-", "_"))
            message = s3_str(message_T) % {"date": humanized_date,
                                           "location": location_represent(location_id),
                                           }
            users = languages[language]
            for pe_id in users:
                send_email(pe_id,
                           subject = subject,
                           message = message,
                           )

        # NB No need to restore UI language as this is run as an async task w/o UI
        return

    settings.tasks.hrm_training_event_survey = hrm_training_event_survey

    # -------------------------------------------------------------------------
    def hrm_training_dashboard_notify():
        """
            Notify Event Office Managers (OMs) & MFP that they should check
            the Event Dashboard
        """

        from gluon import URL
        from s3 import s3_str

        db = current.db
        s3db = current.s3db

        # List of recipients, grouped by language
        # Recipients: OMs & MFP(s)
        languages = {}

        utable = db.auth_user
        gtable = db.auth_group
        mtable = db.auth_membership
        ltable = s3db.pr_person_user
        query = (utable.id == mtable.user_id) & \
                (mtable.group_id == gtable.id) & \
                (gtable.uuid.belongs(("EVENT_MONITOR", "EVENT_OFFICE_MANAGER"))) & \
                (ltable.user_id == utable.id)
        users = db(query).select(ltable.pe_id,
                                 utable.language,
                                 distinct = True,
                                 )
        for user in users:
            language = user["auth_user.language"]
            if language in languages:
                languages[language].append(user["pr_person_user.pe_id"])
            else:
                languages[language] = [user["pr_person_user.pe_id"]]

        # Build Message
        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="hrm", f="training_event", vars={"dashboard": 1}),
                        )
        subject_T = T("Check the Event Dashboard")
        message_T = T("This is your monthly reminder to check the Event Dashboard by visiting this link")

        # Send Localised Mail(s)
        send_email = current.msg.send_by_pe_id
        for language in languages:
            T.force(language)
            subject = s3_str(subject_T)
            message = "%s: %s" % (message_T, url)
            users = languages[language]
            for pe_id in users:
                send_email(pe_id,
                           subject = subject,
                           message = message,
                           )

        # NB No need to restore UI language as this is run as an async task w/o UI
        return

    settings.tasks.hrm_training_dashboard_notify = hrm_training_dashboard_notify

    # -------------------------------------------------------------------------
    def dc_target_onapprove(row):
        """
            Only used by Bangkok CCST currently

            Send Notifications, inc:
            * Update Survey Date
            * Schedule Report

            @ToDo: Don't do this automatically for auto-approved manual surveys?
        """

        target_id = row.id

        ltable = current.s3db.dc_target_event
        training_event = current.db(ltable.target_id == target_id).select(ltable.training_event_id,
                                                                          limitby = (0, 1),
                                                                          ).first()

        hrm_notify_participants(training_event.training_event_id, redirect=False)

    # -------------------------------------------------------------------------
    def customise_dc_target_resource(r, tablename):
        """
            Only used by Bangkok CCST currently
        """

        s3db = current.s3db
        table = s3db.table(tablename)

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Survey"),
            title_display = T("Survey Details"),
            title_list = T("Surveys"),
            title_update = T("Edit Survey"),
            title_upload = T("Import Surveys"),
            label_list_button = T("List Surveys"),
            label_delete_button = T("Delete Survey"),
            msg_record_created = T("Survey added"),
            msg_record_modified = T("Survey updated"),
            msg_record_deleted = T("Survey deleted"),
            msg_list_empty = T("No Surveys currently registered"))

        table.location_id.readable = table.location_id.writable = False
        #table.comments.readable = table.comments.writable = False

        # Expose the Language Option
        f = table.language
        f.readable = f.writable = True
        f.label = T("Default Language")
        f.requires.other._select = OrderedDict([("en-gb", "English"),
                                                ("my", "Burmese"),
                                                ("id", "Indonesian"),
                                                ("km", "Khmer"),
                                                ("lo", "Lao"),
                                                ("ms", "Malaysian"),
                                                ("th", "Thai"),
                                                ])

        # Default the template
        ttable = s3db.dc_template
        template = current.db(ttable.name == "Training Evaluation").select(ttable.id,
                                                                           limitby = (0, 1)
                                                                           ).first()
        if template:
            f = table.template_id
            f.default = template.id
            #f.readable = f.writable = False

        if r.component:
            crud_form = None
            list_fields = None

        else:
            # Add (Training) Event to form & table
            from s3 import S3SQLCustomForm

            crud_form = S3SQLCustomForm("event_target.training_event_id",
                                        "event_target.survey_type",
                                        "template_id",
                                        "language",
                                        #"date",
                                        "comments",
                                        )

            list_fields = [(T("Event"), "training_event__link.training_event_id"),
                           (T("Type"), "training_event__link.survey_type"),
                           "template_id",
                           "date",
                           "comments",
                           ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       onapprove = dc_target_onapprove,
                       # Done in Global Setting
                       #requires_approval = True,
                       )

    settings.customise_dc_target_resource = customise_dc_target_resource

    # -------------------------------------------------------------------------
    def _is_asia_pacific(region_id = False):
        """
            Helper to determine if the user is in the Asia Pacific region
            - used for RDRT
        """

        user = current.auth.user
        organisation_id = user and user.organisation_id or None
        if organisation_id:

            db = current.db
            s3db = current.s3db

            ortable = s3db.org_organisation_region
            rtable = s3db.org_region
            query = (ortable.organisation_id == organisation_id) & \
                    (ortable.region_id == rtable.id)
            region = db(query).select(rtable.id,
                                      rtable.name,
                                      cache = s3db.cache,
                                      limitby = (0, 1)
                                      ).first()
            if region:
                if region_id:
                    if region.name in ("Asia Pacific", "East Asia", "Pacific", "South Asia", "South East Asia"):
                        if region == "Asia Pacific":
                            region_id = region.id
                        else:
                            region_id = db(rtable.name == "Asia Pacific").select(rtable.id,
                                                                                 limitby = (0, 1)
                                                                                 ).first().id
                        #return (True, region_id)
                        return region_id
                    elif region.name in ("Africa", "Central Africa", "Southern Africa", "Sahel", "East Africa", "West Coast", "Indian Ocean", "Madagascar"):
                        if region == "Africa":
                            region_id = region.id
                        else:
                            region_id = db(rtable.name == "Africa").select(rtable.id,
                                                                           limitby = (0, 1)
                                                                           ).first().id
                        #return (False, region_id)
                        return region_id
                elif region.name in ("Asia Pacific", "East Asia", "Pacific", "South Asia", "South East Asia"):
                    return True

        return False

    # -------------------------------------------------------------------------
    def _countries_for_region():
        """
            Helper to determine the list of countries in a user's root region
        """

        user = current.auth.user
        organisation_id = user and user.organisation_id or None
        if organisation_id:

            db = current.db
            s3db = current.s3db

            ortable = s3db.org_organisation_region
            rtable = s3db.org_region
            query = (ortable.organisation_id == organisation_id) & \
                    (rtable.id == ortable.region_id)
            region = db(query).select(rtable.id,
                                      rtable.parent,
                                      cache = s3db.cache,
                                      limitby = (0, 1)
                                      ).first()
            if region:
                ctable = s3db.org_region_country
                parent = region.parent
                if parent:
                    query = (rtable.parent == parent)
                else:
                    query = (rtable.parent == region.id)
                query &= (rtable.deleted == False)
                children = db(query).select(rtable.id)
                region_ids = [c.id for c in children]
                query = (ctable.region_id.belongs(region_ids)) & \
                        (ctable.deleted == False)
                countries = db(query).select(ctable.location_id)
                countries = [c.location_id for c in countries]
                # Cache countries for use in customise_resource is we lookup 1st in customise_controller
                current.response.s3.countries = countries
                return countries

        return []

    # -------------------------------------------------------------------------
    def _customise_job_title_field(field, r = None):
        """
            Helper to customise the Job Title field for RDRT
        """

        field.comment = None
        field.label = T("Sector")

        from s3 import IS_ONE_OF

        db = current.db
        s3db = current.s3db

        table = s3db.hrm_job_title
        query = (table.type == 4)

        region_id = _is_asia_pacific(region_id = True)
        if region_id:
            query &= (table.region_id == region_id)

        if r and r.method == "update" and r.record.job_title_id:
            # Allow to keep the current value
            query |= (table.id == r.record.job_title_id)

        field.requires = IS_ONE_OF(db(query), "hrm_job_title.id",
                                   field.represent,
                                   )

    # -------------------------------------------------------------------------
    def _customise_assignment_fields():

        MEMBER = T("Member")
        from gluon.html import DIV
        hr_comment =  \
            DIV(_class="tooltip",
                _title="%s|%s" % (MEMBER,
                                  current.messages.AUTOCOMPLETE_HELP))

        s3db = current.s3db
        atable = s3db.deploy_assignment
        atable.human_resource_id.label = MEMBER
        atable.human_resource_id.comment = hr_comment
        _customise_job_title_field(atable.job_title_id)

        # Default activity_type when creating experience records from assignments
        activity_type = s3db.hrm_experience.activity_type
        activity_type.default = activity_type.update = "rdrt"

    # -------------------------------------------------------------------------
    def customise_deploy_alert_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        auth = current.auth
        is_admin = auth.s3_has_role("ADMIN")

        if not is_admin:
            organisation_id = auth.user.organisation_id
            dotable = s3db.deploy_organisation
            deploying_orgs = db(dotable.deleted == False).select(dotable.organisation_id)
            deploying_orgs = [o.organisation_id for o in deploying_orgs]

            if organisation_id in deploying_orgs:
                # Filter Alerts to just those from this region's countries
                mtable = s3db.deploy_mission
                missions = db(mtable.organisation_id == organisation_id).select(mtable.id)
                missions = [m.id for m in missions]
                # Cache missions for use in customise_resource
                s3.missions = missions
                s3.filter = (s3db.deploy_alert.mission_id.belongs(missions))

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "select":
                if _is_asia_pacific():
                    settings.deploy.select_ratings = True

                if not is_admin and organisation_id in deploying_orgs:
                    from s3 import FS
                    s3.member_query = (FS("application.organisation_id") == organisation_id)

            return result

        s3.prep = custom_prep

        return attr

    settings.customise_deploy_alert_controller = customise_deploy_alert_controller

    # -------------------------------------------------------------------------
    def customise_deploy_alert_resource(r, tablename):

        from s3 import S3DateTime, S3SQLCustomForm

        db = current.db
        s3db = current.s3db

        s3db.deploy_alert_recipient.human_resource_id.label = T("Member")

        atable = s3db.deploy_alert
        created_on = atable.modified_on
        created_on.readable = True
        created_on.label = T("Date")
        created_on.represent = lambda d: S3DateTime.date_represent(d, utc=True)

        atable.cc.label = T("cc: Focal Points?")

        crud_form = S3SQLCustomForm("mission_id",
                                    "contact_method",
                                    "cc",
                                    "subject",
                                    "body",
                                    "modified_on",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = ["mission_id",
                                      "contact_method",
                                      "subject",
                                      "body",
                                      "alert_recipient.human_resource_id",
                                      ],
                       )

        auth = current.auth
        is_admin = auth.s3_has_role("ADMIN")

        if not is_admin:
            organisation_id = auth.user.organisation_id
            dotable = s3db.deploy_organisation
            deploying_orgs = db(dotable.deleted == False).select(dotable.organisation_id)
            deploying_orgs = [o.organisation_id for o in deploying_orgs]

            if organisation_id in deploying_orgs:
                # Limit Missions to just those for this deploying_org
                missions = current.response.s3.missions
                if not missions:
                    # Not coming from deploy/alert controller so need to query
                    mtable = s3db.deploy_mission
                    query = (mtable.organisation_id == organisation_id) & \
                            (mtable.deleted == False)
                    missions = db(query).select(mtable.id)
                    missions = [m.id for m in missions]

                from s3 import IS_ONE_OF
                field = atable.mission_id
                field.requires = IS_ONE_OF(db, "deploy_mission.id",
                                           field.represent,
                                           filterby = "id",
                                           filter_opts = missions,
                                           sort=True)

    settings.customise_deploy_alert_resource = customise_deploy_alert_resource

    # -------------------------------------------------------------------------
    def customise_deploy_application_resource(r, tablename):

        current.s3db[tablename].human_resource_id.label = T("Member")

    settings.customise_deploy_application_resource = customise_deploy_application_resource

    # -------------------------------------------------------------------------
    def customise_deploy_assignment_controller(**attr):

        s3db = current.s3db
        table = s3db.deploy_assignment

        # Labels
        table.job_title_id.label = T("RDRT Type")
        table.start_date.label = T("Deployment Date")
        #table.end_date.label = T("EOM")

        # List fields
        list_fields = [(T("Mission"), "mission_id$name"),
                       (T("Appeal Code"), "mission_id$code"),
                       (T("Country"), "mission_id$location_id"),
                       (T("Disaster Type"), "mission_id$event_type_id"),
                       # @todo: replace by date of first alert?
                       (T("Date"), "mission_id$created_on"),
                       "job_title_id",
                       (T("Member"), "human_resource_id$person_id"),
                       (T("Deploying NS"), "human_resource_id$organisation_id"),
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
                       (T("Disaster Type"), "mission_id$event_type_id"),
                       (T("RDRT Type"), "job_title_id"),
                       (T("Deploying NS"), "human_resource_id$organisation_id"),
                      ]
        report_options = Storage(
            rows = report_axis,
            cols = report_axis,
            fact = report_fact,
            defaults = Storage(rows="mission_id$location_id",
                               cols="mission_id$event_type_id",
                               fact="count(human_resource_id)",
                               totals=True
                               )
            )

        s3db.configure("deploy_assignment",
                       list_fields = list_fields,
                       report_options = report_options,
                       )


        # CRUD Strings
        s3 = current.response.s3
        s3.crud_strings["deploy_assignment"] = Storage(
            label_create = T("Add Deployment"),
            title_display = T("Deployment Details"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment Details"),
            title_upload = T("Import Deployments"),
            label_list_button = T("List Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment Details updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))

        _customise_assignment_fields()

        # Restrict Location to just Countries
        field = s3db.deploy_mission.location_id
        field.represent = S3Represent(lookup="gis_location", translate=True)

        has_role = current.auth.s3_has_role
        if has_role("AP_RDRT_ADMIN") and not has_role("ADMIN"):
            from s3 import FS
            s3.filter = FS("~.mission_id$organisation_id$name") == "Asia-Pacific Region"

        return attr

    settings.customise_deploy_assignment_controller = customise_deploy_assignment_controller

    # -------------------------------------------------------------------------
    def customise_deploy_mission_controller(**attr):

        from gluon.html import DIV

        db = current.db
        auth = current.auth
        s3db = current.s3db
        s3 = current.response.s3
        messages = current.messages

        MEMBER = T("Member")
        hr_comment =  \
            DIV(_class="tooltip",
                _title="%s|%s" % (MEMBER,
                                  messages.AUTOCOMPLETE_HELP))

        table = s3db.deploy_mission
        table.code.label = T("Appeal Code")
        table.event_type_id.label = T("Disaster Type")

        dotable = s3db.deploy_organisation
        deploying_orgs = db(dotable.deleted == False).select(dotable.organisation_id)
        deploying_orgs = [o.organisation_id for o in deploying_orgs]

        is_admin = auth.s3_has_role("ADMIN")
        organisation_id = auth.user.organisation_id

        from s3 import IS_ONE_OF
        f = table.organisation_id
        if not is_admin and organisation_id in deploying_orgs:
            f.default = organisation_id
            f.readable = f.writable = False
            s3.filter = (f == organisation_id)
        else:
            f.requires = IS_ONE_OF(db, "org_organisation.id",
                                   f.represent,
                                   filterby = "id",
                                   filter_opts = deploying_orgs,
                                   orderby = "org_organisation.name",
                                   sort = True
                                   )

        # Restrict Location to just Countries
        from s3 import S3MultiSelectWidget
        COUNTRY = messages.COUNTRY
        field = table.location_id
        field.label = COUNTRY
        field.represent = S3Represent(lookup="gis_location", translate=True)
        countries = _countries_for_region()
        if countries:
            # Limit to just this region's countries
            field.requires = IS_ONE_OF(db, "gis_location.id",
                                       field.represent,
                                       filterby = "id",
                                       filter_opts = countries,
                                       sort=True)
            # Filter to just the user's region
            # (we filter on organisation_id now)
            #s3.filter = (field.belongs(countries))
        else:
            # Allow all countries
            field.requires = s3db.gis_country_requires
        field.widget = S3MultiSelectWidget(multiple=False)

        rtable = s3db.deploy_response
        rtable.human_resource_id.label = MEMBER
        rtable.human_resource_id.comment = hr_comment

        _customise_assignment_fields()

        from s3 import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3TextFilter
        filter_widgets = [S3TextFilter(["name",
                                        "code",
                                        "event_type_id$name",
                                        ],
                                       label=T("Search")
                                       ),
                          S3LocationFilter("location_id",
                                           label=COUNTRY,
                                           widget="multiselect",
                                           levels=["L0"],
                                           hidden=True
                                           ),
                          S3OptionsFilter("event_type_id",
                                          widget="multiselect",
                                          hidden=True
                                          ),
                          S3OptionsFilter("status",
                                          options=s3db.deploy_mission_status_opts,
                                          hidden=True
                                          ),
                          S3DateFilter("date",
                                       hide_time=True,
                                       hidden=True
                                       ),
                          ]

        # Report options
        report_fact = [(T("Number of Missions"), "count(id)"),
                       (T("Number of Countries"), "count(location_id)"),
                       (T("Number of Disaster Types"), "count(event_type_id)"),
                       #(T("Number of Responses"), "sum(response_count)"),
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

        list_fields = ["name",
                       "date",
                       "event_type_id",
                       (T("Country"), "location_id"),
                       "code",
                       #(T("Responses"), "response_count"),
                       (T("Members Deployed"), "hrquantity"),
                       "status",
                       ]

        s3db.configure("deploy_mission",
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = report_options,
                       )

        # CRUD Strings
        s3.crud_strings["deploy_assignment"] = Storage(
            label_create = T("New Deployment"),
            title_display = T("Deployment Details"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment Details"),
            title_upload = T("Import Deployments"),
            label_list_button = T("List Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment Details updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.interactive:
                table = r.resource.table
                if not current.auth.s3_has_role("RDRT_ADMIN"):
                    # Limit write-access to these fields to RDRT Admins:
                    fields = ("name",
                              "event_type_id",
                              "location_id",
                              "code",
                              "status",
                              )
                    for f in fields:
                        if f in table:
                            table[f].writable = False

                # Date field is always the same as created_on
                table.date.writable = False
                table.date.label = T("Date Created")

                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                crud_form = S3SQLCustomForm("organisation_id",
                                            "name",
                                            "event_type_id",
                                            "location_id",
                                            "code",
                                            "status",
                                            # Files
                                            S3SQLInlineComponent(
                                                "document",
                                                name = "file",
                                                label = T("Files"),
                                                fields = ("file", "comments"),
                                                filterby = {"field": "file",
                                                            "options": "",
                                                            "invert": True,
                                                            }
                                            ),
                                            # Links
                                            S3SQLInlineComponent(
                                                "document",
                                                name = "url",
                                                label = T("Links"),
                                                fields = ("url", "comments"),
                                                filterby = {"field": "url",
                                                            "options": None,
                                                            "invert": True,
                                                            }
                                            ),
                                            "comments",
                                            "date",
                                            )

                s3db.configure("deploy_mission",
                               crud_form = crud_form,
                               )

            #if not r.component and r.method == "create":
            #    # Org is always IFRC
            #    otable = s3db.org_organisation
            #    query = (otable.name == IFRC)
            #    organisation = db(query).select(otable.id,
            #                                    limitby = (0, 1),
            #                                    ).first()
            #    try:
            #        r.table.organisation_id.default = organisation.id
            #    except:
            #        current.log.error("Cannot find org %s - prepop not done?" % IFRC)

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_deploy_mission_controller = customise_deploy_mission_controller

    # -------------------------------------------------------------------------
    def customise_deploy_response_resource(r, tablename):

        from s3 import S3SQLCustomForm

        crud_form = S3SQLCustomForm("mission_id",
                                    "human_resource_id",
                                    "message_id",
                                    "comments",
                                    # @todo:
                                    #S3SQLInlineComponent("document"),
                                    )

        # Table Configuration
        current.s3db.configure(tablename,
                               crud_form = crud_form,
                               )

    settings.customise_deploy_response_resource = customise_deploy_response_resource

    # -------------------------------------------------------------------------
    def customise_event_incident_report_resource(r, tablename):

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            from s3 import S3LocationSelector

            # Don't go back to Create form after submission
            current.session.s3.rapid_data_entry = False

            # Hide Street Address
            current.s3db.event_incident_report.location_id.widget = S3LocationSelector()

    settings.customise_event_incident_report_resource = customise_event_incident_report_resource

    # -------------------------------------------------------------------------
    def poi_marker_fn(record):
        """
            Function to decide which Marker to use for PoI KML export
        """

        db = current.db
        table = db.gis_poi_type
        ptype = db(table.id == record.poi_type_id).select(table.name,
                                                          limitby=(0, 1)
                                                          ).first()
        if ptype:
            marker = ptype.name.lower().replace(" ", "_")\
                                       .replace("_cccm", "_CCCM")\
                                       .replace("_nfi_", "_NFI_")\
                                       .replace("_ngo_", "_NGO_")\
                                       .replace("_wash", "_WASH")
            marker = "OCHA/%s_40px.png" % marker
        else:
            # Fallback
            marker = "marker_red.png"

        return Storage(image = marker)

    # -------------------------------------------------------------------------
    def customise_gis_poi_resource(r, tablename):

        if r.representation == "kml":
            # Custom Marker function
            current.s3db.configure("gis_poi",
                                   marker_fn = poi_marker_fn,
                                   )

    settings.customise_gis_poi_resource = customise_gis_poi_resource

    # -------------------------------------------------------------------------
    def customise_hrm_certificate_controller(**attr):

        # Organisation needs to be an NS
        ns_only("hrm_certificate",
                required = False,
                branches = False,
                )

        return attr

    settings.customise_hrm_certificate_controller = customise_hrm_certificate_controller

    # -------------------------------------------------------------------------
    def customise_hrm_course_controller(**attr):

        tablename = "hrm_course"

        # Different settings for different NS
        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            # Keep things simple
            return attr

        # Load standard model
        s3db = current.s3db
        table = s3db.hrm_course

        # List fields
        list_fields = ["code",
                       "name",
                       ]

        ADMIN = current.session.s3.system_roles.ADMIN
        if current.auth.s3_has_role(ADMIN):
            list_fields.append("organisation_id")
            # Organisation needs to be an NS
            # NB AP RDRT Courses are linked to a Branch
            ns_only(tablename,
                    required = False,
                    branches = False,
                    )

        if root_org == ARCS:
            f = table.type
            f.readable = f.writable = True
            list_fields.append("type")

        if settings.get_hrm_trainings_external():
            list_fields.append("external")

        list_fields.append((T("Sectors"), "course_sector.sector_id"))

        # CRUD Form
        from s3 import S3SQLCustomForm, S3SQLInlineLink
        crud_form = S3SQLCustomForm("code",
                                    "name",
                                    "external",
                                    "type",
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
        s3db = current.s3db
        table = s3db.hrm_credential

        _customise_job_title_field(table.job_title_id)

        table.organisation_id.readable = table.organisation_id.writable = False
        table.performance_rating.readable = table.performance_rating.writable = False
        table.start_date.readable = table.start_date.writable = False
        table.end_date.readable = table.end_date.writable = False

        return attr

    settings.customise_hrm_credential_controller = customise_hrm_credential_controller

    # -------------------------------------------------------------------------
    def customise_hrm_department_controller(**attr):

        # Organisation needs to be an NS
        ns_only("hrm_department",
                required = False,
                branches = False,
                )

        return attr

    settings.customise_hrm_department_controller = customise_hrm_department_controller

    # -------------------------------------------------------------------------
    def customise_hrm_experience_controller(**attr):

        get_vars_get = current.request.get_vars.get
        if get_vars_get("rdrt_ap_current"):
            from s3 import S3SQLCustomForm
            s3db = current.s3db
            table = s3db.hrm_experience
            f = table.organisation
            f.readable = f.writable = True
            f = table.comments
            f.comment = None
            f = table.job_title
            f.readable = f.writable = True
            crud_form = S3SQLCustomForm("organisation",
                                        (T("From"), "start_date"),
                                        (T("To"), "end_date"),
                                        (T("Total experience"), "comments"),
                                        (T("Designation(s)"), "job_title"),
                                        )
            s3db.configure("hrm_experience",
                           crud_form = crud_form,
                           )
        elif get_vars_get("rdrt_ap_deployment"):
            from gluon import IS_EMPTY_OR
            from s3 import s3_comments_widget, IS_ONE_OF, S3SQLCustomForm#, S3MultiSelectWidget
            db = current.db
            s3db = current.s3db

            # Limit Orgs to RC roots
            ttable = s3db.org_organisation_type
            try:
                type_id = db(ttable.name == "Red Cross / Red Crescent").select(ttable.id,
                                                                               limitby=(0, 1),
                                                                               cache = s3db.cache,
                                                                               ).first().id
            except:
                # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
                return
            ltable = s3db.org_organisation_organisation_type
            rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
            filter_opts = [row.organisation_id for row in rows]
            btable = s3db.org_organisation_branch
            rows = db((btable.deleted != True) &
                      (btable.branch_id.belongs(filter_opts))).select(btable.branch_id)
            filter_opts = list(set(filter_opts) - set(row.branch_id for row in rows))

            table = s3db.hrm_experience
            table.activity_type.default = "rdrt"
            table.organisation_id.requires = IS_ONE_OF(db, "org_organisation.id",
                                                       s3db.org_OrganisationRepresent(acronym = False,
                                                                                      parent = False),
                                                       filterby = "id",
                                                       filter_opts = filter_opts,
                                                       orderby = "org_organisation.name",
                                                       sort = True)
            f = table.comments
            f.comment = None
            country_represent = S3Represent(lookup="gis_location", translate=True)
            f = table.location_id
            f.default = None
            f.represent = country_represent
            f.requires = IS_EMPTY_OR(IS_ONE_OF(db, "gis_location.id",
                                               country_represent,
                                               filterby = "level",
                                               filter_opts = ["L0"],
                                               sort=True))
            f.widget = None
            #f.widget = S3MultiSelectWidget(multiple=False)
            table.responsibilities.widget = s3_comments_widget
            crud_form = S3SQLCustomForm("organisation_id",
                                        (T("From"), "start_date"),
                                        (T("To"), "end_date"),
                                        (T("Disaster situation (flood / earthquake, etc.)"), "comments"),
                                        (T("Country of Deployment"), "location_id"),
                                        (T("Skills Utilized"), "responsibilities"),
                                        )
            s3db.configure("hrm_experience",
                           crud_form = crud_form,
                           )
        else:
            s3 = current.response.s3

            root_org = current.auth.root_org_name()
            vnrc = False
            if root_org == VNRC:
                vnrc = True

            standard_prep = s3.prep
            def custom_prep(r):
                # Call standard prep
                if callable(standard_prep):
                    if not standard_prep(r):
                        return False

                if vnrc:
                    department_id = r.table.department_id
                    department_id.readable = department_id.writable = True

                if r.controller == "deploy":
                    # Popups in RDRT Africa Member Profile

                    table = r.table

                    job_title_id = table.job_title_id
                    _customise_job_title_field(job_title_id, r)
                    job_title_id.label = T("Sector / Area of Expertise")

                    job_title = table.job_title
                    job_title.readable = job_title.writable = True
                return True
            s3.prep = custom_prep

        return attr

    settings.customise_hrm_experience_controller = customise_hrm_experience_controller

    # -------------------------------------------------------------------------
    def rdrt_member_profile_header(r):
        """ Custom profile header to allow update of RDRT roster status """

        record = r.record
        if not record:
            return ""

        person_id = record.person_id
        from s3 import s3_fullname, s3_avatar_represent
        name = s3_fullname(person_id)

        has_permission = current.auth.s3_has_permission
        table = r.table

        from s3 import s3_unicode
        from gluon.html import A, DIV, H2, LABEL, P, SPAN, URL
        SUBMIT = T("Save")
        EDIT = T("Click to edit")

        # Job title, if present
        job_title_id = record.job_title_id
        if job_title_id:
            comments = SPAN(s3_unicode(table.job_title_id.represent(job_title_id)))
        else:
            comments = SPAN()

        # Permissions
        record_id = record.id
        updateable = has_permission("update",
                                    "hrm_human_resource",
                                    record_id=record_id)

        # Organisation
        org_value = record.organisation_id
        ofield = table.organisation_id
        org_represent = ofield.represent(org_value)

        if updateable:
            # Make inline-editable
            script = True
            org_represent = A(org_represent,
                              data = {"organisation_id": org_value},
                              _id = "rdrt-organisation",
                              _title = EDIT,
                              )
            #org_opts = ofield.requires.options()
            #org_opts = {key: value for (key, value) in org_opts}
            org_script = '''$.rdrtOrg('%(url)s','%(submit)s')''' % \
                {"url": URL(c="deploy", f="human_resource",
                            args=[record_id, "update.url"]),
                 "submit": SUBMIT,
                 }
        else:
            # Read-only
            script = False
            org_represent = SPAN(org_represent)
            org_script = None

        # Add Type
        hr_type_value = record.type
        tfield = table.type
        if hr_type_value in (1, 2):
            type_represent = tfield.represent
            hr_type_represent = type_represent(hr_type_value)
        else:
            hr_type_represent = current.messages.UNKNOWN_OPT

        if updateable:
            # Make inline-editable
            script = True
            hr_type_represent = A(hr_type_represent,
                                  data = {"type": hr_type_value},
                                  _id = "rdrt-resource-type",
                                  _title = EDIT,
                                  )
            type_script = '''$.rdrtType('%(url)s','%(staff)s','%(volunteer)s','%(submit)s')''' % \
                {"url": URL(c="deploy", f="human_resource",
                            args=["%s.s3json" % record_id]),
                 "staff": type_represent(1),
                 "volunteer": type_represent(2),
                 "submit": SUBMIT,
                 }
        else:
            # Read-only
            script = False
            hr_type_represent = SPAN(hr_type_represent)
            type_script = None

        # Determine the current roster membership status (active/inactive)
        atable = current.s3db.deploy_application
        status = atable.active
        query = atable.human_resource_id == r.id
        row = current.db(query).select(atable.id,
                                       atable.active,
                                       limitby=(0, 1)).first()
        if row:
            active = 1 if row.active else 0
            status_id = row.id
            status_represent = status.represent
            roster_status = status_represent(row.active)
        else:
            active = None
            status_id = None
            roster_status = current.messages.UNKNOWN_OPT

        if status_id and has_permission("update",
                                        "deploy_application",
                                        record_id=status_id):
            # Make inline-editable
            script = True
            roster_status = A(roster_status,
                              data = {"status": active},
                              _id = "rdrt-roster-status",
                              _title = EDIT,
                              )
            status_script = '''$.rdrtStatus('%(url)s','%(active)s','%(inactive)s','%(submit)s')''' % \
                {"url": URL(c="deploy", f="application",
                            args=["%s.s3json" % status_id]),
                 "active": status_represent(True),
                 "inactive": status_represent(False),
                 "submit": SUBMIT,
                 }
        else:
            # Read-only
            roster_status = SPAN(roster_status)
            status_script = None

        if script:
            s3 = current.response.s3
            script = "/%s/static/themes/IFRC/js/rdrt.js" % r.application
            if script not in s3.scripts:
                s3.scripts.append(script)
            jqrappend = s3.jquery_ready.append
            if org_script:
                jqrappend(org_script)
            if type_script:
                jqrappend(type_script)
            if status_script:
                jqrappend(status_script)

        # Render profile header
        return DIV(A(s3_avatar_represent(person_id,
                                         tablename="pr_person",
                                         _class="media-object",
                                         ),
                     _class="pull-left",
                     ),
                   H2(name),
                   P(comments),
                   DIV(LABEL(ofield.label + ": "), org_represent),
                   DIV(LABEL(tfield.label + ": "), hr_type_represent),
                   DIV(LABEL(status.label + ": "), roster_status),
                   _class="profile-header",
                   )

    # -------------------------------------------------------------------------
    def emergency_contact_represent(row):
        """
            Representation of Emergency Contacts (S3Represent label renderer)

            @param row: the row
        """

        name = row["pr_contact_emergency.name"] or current.messages["NONE"]
        items = [name]
        relationship = row["pr_contact_emergency.relationship"]
        if relationship:
            items.append(" (%s)" % relationship)
        phone_number = row["pr_contact_emergency.phone"]
        if phone_number:
            items.append(": %s" % phone_number)
        return "".join(items)

    # -------------------------------------------------------------------------
    def customise_vol_activity_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("vol_activity",
                required = False,
                branches = True,
                )

        return attr

    settings.customise_vol_activity_controller = customise_vol_activity_controller

    # -------------------------------------------------------------------------
    def customise_vol_volunteer_award_resource(r, tablename):

        root_org = current.auth.root_org_name()
        if root_org == IRCS:
            table = current.s3db.vol_volunteer_award
            table.award_id.label = T("Recommendation Letter Type")
            table.award_id.comment = None
            table.number.readable = table.number.writable = True
            table.file.readable = table.file.writable = True

            current.response.s3.crud_strings["vol_volunteer_award"] = Storage(
                label_create = T("Add Recommendation Letter"),
                title_display = T("Recommendation Letter Details"),
                title_list = T("Recommendation Letters"),
                title_update = T("Edit Recommendation Letter"),
                label_list_button = T("List Recommendation Letters"),
                label_delete_button = T("Delete Recommendation Letter"),
                msg_record_created = T("Recommendation Letter added"),
                msg_record_modified = T("Recommendation Letter updated"),
                msg_record_deleted = T("Recommendation Letter removed"),
                msg_no_match = T("No entries found"),
                msg_list_empty = T("Currently no recommendation letters registered"))

    settings.customise_vol_volunteer_award_resource = customise_vol_volunteer_award_resource

    # -------------------------------------------------------------------------
    def customise_vol_award_resource(r, tablename):

        root_org = current.auth.root_org_name()
        if root_org == IRCS:

            current.response.s3.crud_strings["vol_award"] = Storage(
                label_create = T("Add Recommendation Letter Type"),
                title_display = T("Recommendation Letter Type Details"),
                title_list = T("Recommendation Letter Types"),
                title_update = T("Edit Recommendation Letter Type"),
                label_list_button = T("List Recommendation Letter Types"),
                label_delete_button = T("Delete Recommendation Letter Type"),
                msg_record_created = T("Recommendation Letter Type added"),
                msg_record_modified = T("Recommendation Letter Type updated"),
                msg_record_deleted = T("Recommendation Letter Type removed"),
                msg_no_match = T("No entries found"),
                msg_list_empty = T("Currently no recommendation letter types registered"))

    settings.customise_vol_award_resource = customise_vol_award_resource

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        root_org = current.auth.root_org_name()
        controller = r.controller
        if controller == "vol":
            if root_org == IRCS:
                s3db = current.s3db
                table = s3db.hrm_human_resource
                table.start_date.label = T("Appointment Date")
                def vol_service_record_manager(default):
                    from s3 import s3_fullname
                    return s3_fullname(current.auth.s3_logged_in_person())
                settings.hrm.vol_service_record_manager = vol_service_record_manager
                from s3 import S3AddPersonWidget, S3SQLCustomForm, S3SQLInlineComponent
                table.person_id.widget = S3AddPersonWidget(controller = "vol",
                                                           first_name_only = True,
                                                           )
                table.code.label = T("Appointment Number")
                phtable = s3db.hrm_programme_hours
                phtable.date.label = T("Direct Date")
                phtable.contract.label = T("Direct Number")
                phtable.contract.readable = phtable.contract.writable = True
                crud_form = S3SQLCustomForm("organisation_id",
                                            "person_id",
                                            S3SQLInlineComponent("home_address",
                                                                 label = T("Address"),
                                                                 fields = [("", "location_id")],
                                                                 default = {"type": 1}, # Current Home Address
                                                                 link = False,
                                                                 multiple = False,
                                                                 ),
                                            "department_id",
                                            "start_date",
                                            "code",
                                            S3SQLInlineComponent("programme_hours",
                                                                 label = T("Contract"),
                                                                 fields = ("programme_id",
                                                                           "date",
                                                                           (T("End Date"), "end_date"),
                                                                           "contract",
                                                                           ),
                                                                 link = False,
                                                                 multiple = False,
                                                                 ),
                                            S3SQLInlineComponent("education",
                                                                 label = T("Education"),
                                                                 fields = ((T("Education Level"), "level_id"),
                                                                           "institute",
                                                                           "year",
                                                                           ),
                                                                 link = False,
                                                                 multiple = False,
                                                                 ),
                                            "details.active",
                                            )

                s3db.configure("hrm_human_resource",
                               crud_form = crud_form
                               )

            elif root_org == NRCS:
                # Expose volunteer_type field with these options:
                types = {"PROGRAMME": T("Program Volunteer"),
                         "GOVERNANCE": T("Governance Volunteer"),
                         }
                field = current.s3db.vol_details.volunteer_type
                field.readable = field.writable = True
                from gluon.validators import IS_EMPTY_OR, IS_IN_SET
                field.requires = IS_EMPTY_OR(IS_IN_SET(types))
                field.represent = S3Represent(options=types)

        elif controller == "hrm":
            if root_org == IRCS:
                s3db = current.s3db
                table = s3db.hrm_human_resource
                table.start_date.label = T("Appointment Date")
                # All staff have open-ended contracts
                table.end_date.readable = table.end_date.writable = False
                from s3 import S3AddPersonWidget, S3SQLCustomForm, S3SQLInlineComponent
                table.person_id.widget = S3AddPersonWidget(controller = "hrm",
                                                           first_name_only = True,
                                                           )
                table.code.label = T("Appointment Number")
                hrm_status_opts = s3db.hrm_status_opts
                hrm_status_opts[3] = T("End Service")
                table.status.represent = lambda opt: \
                                         hrm_status_opts.get(opt, current.messages.UNKNOWN_OPT)
                from gluon.validators import IS_IN_SET
                table.status.requires = IS_IN_SET(hrm_status_opts,
                                                  zero=None)
                ctable = s3db.hrm_contract
                ctable.name.label = T("Direct Number")
                ctable.date.label = T("Direct Date")
                crud_fields = ["organisation_id",
                               "site_id",
                               "person_id",
                               "job_title_id",
                               "department_id",
                               "start_date",
                               "code",
                               S3SQLInlineComponent("contract",
                                                    label = T("Contract"),
                                                    fields = ("name",
                                                              "date",
                                                              ),
                                                    multiple=True,
                                                    ),
                               "comments",
                               ]
                method = r.method
                if method and method in ("record" "update"):
                    crud_fields.append("status")

                s3db.configure("hrm_human_resource",
                               crud_form = S3SQLCustomForm(*crud_fields),
                               )


    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
    def deploy_dynamic_list_layout(list_id, item_id, resource, rfields, record):
        """
            dataList item renderer for 'Other Information' on the Surge Member Profile

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        raw = record._row
        tablename = resource.tablename

        # Read the fields
        db = current.db
        s3db = current.s3db
        ftable = s3db.s3_field
        ttable = s3db.s3_table
        query = (ftable.table_id == ttable.id) & \
                (ttable.name == tablename)
        fields = db(query).select(ftable.name,
                                  ftable.label,
                                  # Use the fact that each label starts with a number
                                  orderby = ftable.label,
                                  )

        # Render the item
        from gluon import B, DIV
        contents = DIV(_class="media",
                       )
        cappend = contents.append
        for field in fields:
            if not field.label:
                # response_id
                continue
            cappend(DIV(DIV(B("%s:" % field.label)),
                        DIV(raw["%s.%s" % (tablename, field.name)] or "Not Answered"),
                        )
                    )

        item = DIV(DIV(DIV(contents,
                           _class="media-body",
                           ),
                       _class="media",
                       ),
                   _class="thumbnail",
                   _id=item_id,
                   )

        return item

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        from s3 import FS

        db = current.db
        s3db = current.s3db
        auth = current.auth
        s3 = current.response.s3
        request = current.request
        controller = request.controller
        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        tablename = "hrm_human_resource"

        # Special cases for different NS/roles
        arcs = vnrc = EO = False
        root_org = auth.root_org_name()

        if not auth.s3_has_role("ADMIN") and \
           auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
            # Bangkok CCST
            gtable = db.auth_group
            mtable = db.auth_membership

            EO = request.get_vars.get("eo")
            if EO:
                # Filter People to just EOs/MFP(s)/OM(s)
                ltable = s3db.pr_person_user
                query = (gtable.uuid.belongs(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER"))) & \
                        (mtable.group_id == gtable.id) & \
                        (mtable.deleted == False) & \
                        (mtable.user_id == ltable.user_id)
                rows = db(query).select(ltable.pe_id)
                pe_ids = [row.pe_id for row in rows]
                filter = FS("person_id$pe_id").belongs(set(pe_ids))
            else:
                # Filter People to just those trained by this region
                # @ToDo: Filter by Org too if more EVENT_* teams come onboard
                query = (gtable.uuid.belongs(("EVENT_MONITOR", "EVENT_ORGANISER"))) & \
                        (mtable.group_id == gtable.id) & \
                        (mtable.deleted == False)
                rows = db(query).select(mtable.user_id)
                user_ids = [row.user_id for row in rows]
                filter = FS("training.training_event_id$created_by").belongs(set(user_ids))

                # & those from this region's countries? No!
                #ltable = s3db.org_organisation_organisation
                #root_orgs = db(ltable.parent_id == auth.user.organisation_id).select(ltable.organisation_id)
                #root_orgs = [o.organisation_id for o in root_orgs]
                #filter |= FS("~.organisation_id$root_organisation").belongs(root_orgs)

            s3.filter = filter
        else:
            if controller == "deploy":
                # Default Filter
                from s3 import s3_set_default_filter
                s3_set_default_filter("~.organisation_id$organisation_region.region_id",
                                      user_region_and_children_default_filter,
                                      tablename = tablename)

            elif root_org != CRMADA: # CRMADA have too many branches which causes issues
                # Default Filter
                from s3 import s3_set_default_filter
                s3_set_default_filter("~.organisation_id",
                                      user_org_and_children_default_filter,
                                      tablename = tablename)

            if root_org == VNRC:
                vnrc = True
                # @ToDo: Make this use the same lookup as in ns_only to check if user can see HRs from multiple NS
                settings.org.regions = False
                s3db.hrm_human_resource.site_id.represent = s3db.org_SiteRepresent(show_type = False)
                #settings.org.site_label = "Office/Center"

            elif root_org == ARCS:
                arcs = True

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            table = s3db.hrm_human_resource

            # Organisation needs to be an NS/Branch
            ns_only("hrm_human_resource",
                    required = True,
                    branches = True,
                    limit_filter_opts = True,
                    )
            xls = r.representation == "xls"
            if xls:
                # Restore xls represent
                table.organisation_id.represent = s3db.org_OrganisationRepresent(acronym = False,
                                                                                 parent = False)

            resource = r.resource
            get_config = resource.get_config

            is_admin = auth.s3_has_role("ADMIN")
            if is_admin:
                # Remove Location Filter to improve performance
                # @ToDo: Restore this now that performance issues in widget fixed
                filters = []
                append_widget = filters.append
                filter_widgets = get_config("filter_widgets")
                while filter_widgets:
                    widget = filter_widgets.pop(0)
                    if widget.field not in ("location_id",
                                            ):
                        append_widget(widget)

                resource.configure(filter_widgets = filters)

            if EO:
                from s3 import s3_fieldmethod
                ptable = s3db.pr_person
                ltable = s3db.pr_person_user
                gtable = db.auth_group
                mtable = db.auth_membership
                base_query = (ltable.pe_id == ptable.pe_id) & \
                             (ltable.user_id == mtable.user_id) & \
                             (mtable.group_id == gtable.id) & \
                             (gtable.uuid.belongs(("EVENT_ORGANISER", "EVENT_MONITOR", "EVENT_OFFICE_MANAGER")))
                def roles(row):
                    query = base_query & \
                            (ptable.id == row["hrm_human_resource.person_id"])
                    user = db(query).select(gtable.uuid)
                    names = []
                    for u in user:
                        if u.uuid == "EVENT_ORGANISER":
                            names.append("EO")
                        elif u.uuid == "EVENT_MONITOR":
                            names.append("MFP")
                        elif u.uuid == "EVENT_OFFICE_MANAGER":
                            names.append("OM")
                    names = ", ".join(names)
                    return names
                table.roles = s3_fieldmethod("roles", roles)

                list_fields = ["person_id",
                               (T("Roles"), "roles"),
                               (T("Email"), "email.value"),
                               (settings.get_ui_label_mobile_phone(), "phone.value")
                               ]
                resource.configure(list_fields = list_fields)

            elif arcs:
                # No Sector filter
                pass
            elif vnrc:
                field = table.job_title_id
                field.readable = field.writable = False
            else:
                from s3 import S3OptionsFilter
                filter_widgets = get_config("filter_widgets")
                filter_widgets.insert(-1, S3OptionsFilter("training.course_id$course_sector.sector_id",
                                                          label = T("Training Sector"),
                                                          hidden = True,
                                                          ))

            if controller == "vol":
                if arcs:
                    # ARCS have a custom Volunteer form
                    #from gluon import IS_EMPTY_OR
                    #from s3 import S3AddPersonWidget, IS_ONE_OF, S3LocationSelector, S3SQLCustomForm, S3SQLInlineComponent
                    from s3 import IS_ONE_OF, S3LocationSelector, S3SQLCustomForm, S3SQLInlineComponent

                    # Go back to Create form after submission
                    current.session.s3.rapid_data_entry = True

                    settings.pr.request_mobile_phone = False
                    settings.pr.request_email = False
                    #settings.pr.request_year_of_birth = True
                    settings.pr.separate_name_fields = 2
                    #table.person_id.widget = S3AddPersonWidget(controller = "vol",
                    #                                           first_name_only = True,
                    #                                           )
                    table.code.label = T("Volunteer ID")
                    ptable = s3db.pr_person
                    ptable.first_name.label = T("Name")
                    ptable.gender.label = T("Gender")
                    # Ensure that + appears at the beginning of the number
                    # Done in Model's controller prep
                    #f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
                    #f.represent = s3_phone_represent
                    #f.widget = S3PhoneWidget()
                    s3db.pr_address.location_id.widget = S3LocationSelector(show_address = T("Village"),
                                                                            show_map = False)
                    # NB Need to use alias if using this pre-filtered component
                    #s3db.pr_home_address_address.location_id.widget = S3LocationSelector(show_map = False)
                    # Emergency Contact Name isn't required
                    s3db.pr_contact_emergency.name.requires = None
                    dtable = s3db.pr_person_details
                    dtable.father_name.label = T("Father Name")
                    dtable.grandfather_name.label = T("Grand Father Name")
                    dtable.occupation.label = T("Job")
                    etable = s3db.pr_education
                    etable.level_id.comment = None # Don't Add Education Levels inline
                    organisation_id = auth.root_org()
                    f = etable.level_id
                    f.requires = IS_ONE_OF(db, "pr_education_level.id",
                                           f.represent,
                                           filterby = "organisation_id",
                                           filter_opts = (organisation_id,),
                                           )
                    s3db.pr_image.image.widget = None # ImageCropWidget doesn't work inline
                    #ctable = s3db.hrm_course
                    #query = (ctable.organisation_id == auth.root_org()) & \
                    #        (ctable.type == 2) & \
                    #        (ctable.deleted != True)
                    #courses = db(query).select(ctable.id)
                    #course_ids = [c.id for c in courses]
                    f = s3db.hrm_training.course_id
                    f.requires = IS_ONE_OF(db, "hrm_course.id",
                                           f.represent,
                                           #filterby = "id",
                                           #filter_opts = course_ids,
                                           filterby = "organisation_id",
                                           filter_opts = (organisation_id,),
                                           sort = True,
                                           )

                    # Translate Programmes
                    #represent = S3Represent(lookup="hrm_programme", translate=True)
                    #f = s3db.hrm_programme_hours.programme_id
                    #f.represent = represent
                    #f.requires = IS_EMPTY_OR(
                    #                IS_ONE_OF(db, "hrm_programme.id",
                    #                          represent,
                    #                          filterby="organisation_id",
                    #                          filter_opts=(organisation_id,)
                    #                          ))

                    s3db.add_components(tablename,
                                        #hrm_training = {"name": "vol_training",
                                        #                "joinby": "person_id",
                                        #                "filterby": {"course_id": course_ids,
                                        #                             },
                                        #                },
                                        pr_address = {"name": "perm_address",
                                                      "link": "pr_person",
                                                      "joinby": "id",
                                                      "key": "pe_id",
                                                      "fkey": "pe_id",
                                                      "pkey": "person_id",
                                                      "filterby": {"type": "2",
                                                                   },
                                                      },
                                        pr_education = ({"name": "current_education",
                                                         "link": "pr_person",
                                                         "joinby": "id",
                                                         "key": "id",
                                                         "fkey": "person_id",
                                                         "pkey": "person_id",
                                                         "filterby": {"current": True,
                                                                      },
                                                         "multiple": False,
                                                         },
                                                        {"name": "previous_education",
                                                         "link": "pr_person",
                                                         "joinby": "id",
                                                         "key": "id",
                                                         "fkey": "person_id",
                                                         "pkey": "person_id",
                                                         "filterby": {"current": False,
                                                                      },
                                                         "multiple": False,
                                                         },
                                                        ),
                                        pr_image = {"name": "pr_image",
                                                    "link": "pr_person",
                                                    "joinby": "id",
                                                    "key": "pe_id",
                                                    "fkey": "pe_id",
                                                    "pkey": "person_id",
                                                    "filterby": {"profile": True,
                                                                 },
                                                    "multiple": False,
                                                    },
                                        )

                    crud_form = S3SQLCustomForm("organisation_id",
                                                "code",
                                                S3SQLInlineComponent("programme_hours",
                                                                     label = "",
                                                                     fields = ["programme_id"],
                                                                     link = False,
                                                                     multiple = False,
                                                                     ),
                                                "person_id",
                                                S3SQLInlineComponent("perm_address",
                                                                     label = T("Address"),
                                                                     fields = [("", "location_id")],
                                                                     filterby = {"field": "type",
                                                                                 "options": 2,
                                                                                 },
                                                                     link = False,
                                                                     update_link = False,
                                                                     multiple = False,
                                                                     ),
                                                S3SQLInlineComponent("current_education",
                                                                     label = T("School / University"),
                                                                     fields = [("", "institute")],
                                                                     filterby = {"field": "current",
                                                                                 "options": True,
                                                                                 },
                                                                     link = False,
                                                                     update_link = False,
                                                                     multiple = False,
                                                                     ),
                                                S3SQLInlineComponent("phone",
                                                                     label = T("Phone Number"),
                                                                     fields = [("", "value")],
                                                                     filterby = {"field": "contact_method",
                                                                                 "options": "SMS",
                                                                                 },
                                                                     link = False,
                                                                     update_link = False,
                                                                     multiple = False,
                                                                     ),
                                                S3SQLInlineComponent("contact_emergency",
                                                                     label = T("Emergency Contact Number"),
                                                                     fields = [("", "phone")],
                                                                     link = False,
                                                                     update_link = False,
                                                                     multiple = False,
                                                                     ),
                                                S3SQLInlineComponent("previous_education",
                                                                     label = T("Education Level"),
                                                                     fields = [("", "level_id")],
                                                                     filterby = {"field": "current",
                                                                                 "options": False,
                                                                                 },
                                                                     link = False,
                                                                     update_link = False,
                                                                     multiple = False,
                                                                     ),
                                                (T("Volunteer Start Date"), "start_date"),
                                                S3SQLInlineComponent(#"vol_training",
                                                                     "training",
                                                                     label = T("Trainings"),
                                                                     fields = (("", "course_id"),
                                                                               ("", "date"),
                                                                                ),
                                                                     link = False,
                                                                     update_link = False,
                                                                     ),
                                                "details.active",
                                                (T("Remarks"), "comments"),
                                                S3SQLInlineComponent("pr_image",
                                                                     label = T("Photo"),
                                                                     fields = [("", "image")],
                                                                     filterby = {"field": "profile",
                                                                                 "options": True,
                                                                                 },
                                                                     link = False,
                                                                     update_link = False,
                                                                     multiple = False,
                                                                     ),
                                                )

                    from s3 import S3HierarchyFilter, S3LocationFilter, S3OptionsFilter, S3TextFilter

                    filter_widgets = [S3TextFilter(["person_id$first_name",
                                                    "person_id$middle_name",
                                                    "person_id$last_name",
                                                    #"organisation_id",
                                                    ],
                                                   label = T("Search"),
                                                   ),
                                      S3HierarchyFilter("organisation_id",
                                                        leafonly = False,
                                                        ),
                                      S3LocationFilter("location_id",
                                                       label = T("Location"),
                                                       hidden = True,
                                                       ),
                                      S3OptionsFilter("details.active",
                                                      label = T("Active?"),
                                                      cols = 2, #3,
                                                      options = {True: T("Yes"),
                                                                 False: T("No"),
                                                                 #None: T("Unknown"),
                                                                 },
                                                      hidden = True,
                                                      #none = True,
                                                      ),
                                      S3OptionsFilter(#"vol_training.course_id",
                                                      "training.course_id",
                                                      label = T("Training"),
                                                      hidden = True,
                                                      ),
                                      ]

                    if not xls:
                        list_fields = ["person_id",
                                       "organisation_id",
                                       "details.active",
                                       #(T("Trainings"), "vol_training.course_id"),
                                       (T("Trainings"), "training.course_id"),
                                       (T("Start Date"), "start_date"),
                                       (T("Phone"), "phone.value"),
                                       ]
                        s3db.configure(tablename,
                                       list_fields = list_fields,
                                       )

                    report_fields = ["organisation_id",
                                     "person_id",
                                     "person_id$gender",
                                     #(T("Training"), "vol_training.course_id"),
                                     (T("Training"), "training.course_id"),
                                     "location_id$L1",
                                     "location_id$L2",
                                     (T("Age Group"), "person_id$age_group"),
                                     "person_id$education.level",
                                     ]

                    s3db.configure(tablename,
                                   crud_form = crud_form,
                                   filter_widgets = filter_widgets,
                                   report_options = Storage(
                                        rows = report_fields,
                                        cols = report_fields,
                                        fact = report_fields,
                                        methods = ("count", "list",),
                                        defaults = Storage(
                                            rows = "organisation_id",
                                            #cols = "vol_training.course_id",
                                            cols = "training.course_id",
                                            fact = "count(person_id)",
                                            )
                                        ),
                                   )

                elif root_org == CRMADA:
                    if xls:
                        list_fields = get_config("list_fields")
                        list_fields += [(T("Activity Types"), "person_id$activity_hours.activity_hours_activity_type.activity_type_id"),
                                        (T("Activities"), "person_id$activity_hours.activity_id"),
                                        ]
                    else:
                        # Add Activity Type & Tweak Order
                        list_fields = ["person_id",
                                       "organisation_id",
                                       "job_title_id",
                                       (settings.get_ui_label_mobile_phone(), "phone.value"),
                                       (T("Trainings"), "training.course_id"),
                                       (T("Activity Types"), "person_id$activity_hours.activity_hours_activity_type.activity_type_id"),
                                       (T("Activities"), "person_id$activity_hours.activity_id"),
                                       (T("Certificates"), "person_id$certification.certificate_id"),
                                       (T("Email"), "email.value"),
                                       "location_id",
                                       "details.active",
                                       ]

                        s3db.configure(tablename,
                                       list_fields = list_fields,
                                       )

                elif root_org == IRCS:
                    if xls:
                        list_fields = s3db.get_config(tablename, "list_fields")
                        list_fields += ["programme_hours.contract",
                                        "programme_hours.date",
                                        ]
                    else:
                        list_fields = ["person_id",
                                       "details.active",
                                       "code",
                                       "start_date",
                                       "programme_hours.contract",
                                       "programme_hours.date",
                                       "programme_hours.programme_id",
                                       (T("Training"), "training.course_id"),
                                       ]

                        s3db.configure(tablename,
                                       list_fields = list_fields,
                                       )

                elif root_org == NRCS:
                    pos = 6
                    # Add volunteer type to list_fields
                    list_fields = get_config("list_fields")
                    list_fields.insert(pos, "details.volunteer_type")

                    # Add volunteer type to report options
                    report_options = get_config("report_options")
                    if "details.volunteer_type" not in report_options["rows"]:
                        report_options["rows"].insert(pos, "details.volunteer_type")
                    if "details.volunteer_type" not in report_options["cols"]:
                        report_options["cols"].insert(pos, "details.volunteer_type")

                    # Add filter widget for volunteer type
                    filter_widgets = get_config("filter_widgets")
                    filter_widgets.insert(-1, S3OptionsFilter("details.volunteer_type",
                                                              hidden = True,
                                                              ))

                elif root_org == VNRC:
                    # Add extra list_fields
                    list_fields = get_config("list_fields")
                    list_fields += [(T("ID Number"), "person_id$identity.value"),
                                    (T("Province"), "location_id$L1"),
                                    (T("District"), "location_id$L2"),
                                    (T("Commune"), "location_id$L3"),
                                    ]

            elif controller == "hrm":
                if root_org == IRCS:
                    if xls:
                        list_fields = get_config("list_fields")
                        list_fields += ["contract.name",
                                        "contract.date",
                                        ]
                    else:
                        list_fields = ["person_id",
                                       "code",
                                       "start_date",
                                       "contract.name",
                                       "contract.date",
                                       "job_title_id",
                                       "department_id",
                                       ]

                        s3db.configure(tablename,
                                       list_fields = list_fields,
                                       )

            elif controller == "deploy":
                # Custom settings for RDRT

                if not is_admin:
                    organisation_id = auth.user.organisation_id
                    dotable = s3db.deploy_organisation
                    deploying_orgs = db(dotable.deleted == False).select(dotable.organisation_id)
                    deploying_orgs = [o.organisation_id for o in deploying_orgs]
                    if organisation_id in deploying_orgs:
                        r.resource.add_filter(FS("application.organisation_id") == organisation_id)

                    if auth.s3_has_role("RDRT_ADMIN"):
                        # Allow selection of any Organisation for HRs
                        s3db.hrm_human_resource.organisation_id.requires = s3db.org_organisation_requires(required=True)

                AP = _is_asia_pacific()

                if not AP:
                    # Africa RDRT
                    # Exclude None-values for training course pivot axis
                    s3db.configure(tablename,
                                   report_exclude_empty = ("training.course_id",
                                                           ),
                                   )

                    if r.record:
                        widgets = [{"label": "Personal Details",
                                    "tablename": "pr_person",
                                    "type": "datalist",
                                    "insert": False,
                                    "list_fields": ["first_name",
                                                    # Not in form!?
                                                    "middle_name",
                                                    "last_name",
                                                    "date_of_birth",
                                                    "gender",
                                                    # Not in form!?
                                                    "person_details.nationality",
                                                    # Not in form!?
                                                    "physical_description.blood_type",
                                                    ],
                                    "filter": FS("id") == r.record.person_id,
                                    "icon": "user",
                                    },
                                   ]
                    else:
                        widgets = []

                    append_widget = widgets.append

                    # Custom profile widgets for hrm_competency ("skills"):
                    subsets = (("Computer", "Computer Skills", "Add Computer Skills"),
                               ("Language", "Language Skills", "Add Language Skills"),
                               )
                    profile_widgets = get_config("profile_widgets")
                    contacts_filter = None
                    while profile_widgets:
                        widget = profile_widgets.pop(0)
                        w_tablename = widget["tablename"]
                        if w_tablename == "hrm_competency":
                            for skill_type, label, label_create in subsets:
                                query = widget["filter"] & \
                                        (FS("skill_id$skill_type_id$name") == skill_type)
                                new_widget = dict(widget)
                                new_widget["label"] = label
                                new_widget["label_create"] = label_create
                                new_widget["filter"] = query
                                append_widget(new_widget)
                        elif w_tablename == "hrm_experience":
                            new_widget = dict(widget)
                            new_widget["create_controller"] = "deploy"
                            append_widget(new_widget)
                        #elif w_tablename == "hrm_training" and AP and organisation_id:
                        #    new_widget = dict(widget)
                        #    new_widget["filter"] = widget["filter"] & \
                        #        (FS("~.course_id$organisation_id") == organisation_id)
                        #    append_widget(new_widget)
                        else:
                            append_widget(widget)
                        if widget["tablename"] == "pr_contact":
                            contacts_filter = widget["filter"]

                    # Emergency contacts
                    if contacts_filter is not None:
                        emergency_widget = {"label": "Emergency Contacts",
                                            "label_create": "Add Emergency Contact",
                                            "tablename": "pr_contact_emergency",
                                            "type": "datalist",
                                            "filter": contacts_filter,
                                            "icon": "phone",
                                            }
                        append_widget(emergency_widget)

                    # Remove unnecessary filter widgets
                    filters = []
                    append_filter = filters.append
                    filter_widgets = get_config("filter_widgets")
                    while filter_widgets:
                        widget = filter_widgets.pop(0)
                        if widget.field not in ("location_id",
                                                "site_id",
                                                #"group_membership.group_id",
                                                ):
                            append_filter(widget)

                    from s3 import S3OptionsFilter

                    # Add gender filter
                    gender_opts = dict(s3db.pr_gender_opts)
                    del gender_opts[1]
                    append_filter(S3OptionsFilter("person_id$gender",
                                                  options = gender_opts,
                                                  cols = 3,
                                                  hidden = True,
                                                  ))
                    # Add Roster status filter
                    append_filter(S3OptionsFilter("application.active",
                                                  cols = 2,
                                                  default = True,
                                                  # Don't hide otherwise default
                                                  # doesn't apply:
                                                  #hidden = False,
                                                  label = T("Status"),
                                                  options = {"True": T("active"),
                                                             "False": T("inactive"),
                                                             },
                                                  ))

                    if r.method != "profile":
                        # Representation of emergency contacts (breaks the update_url construction in render_toolbox)
                        field = s3db.pr_contact_emergency.id
                        field.represent = S3Represent(lookup = "pr_contact_emergency",
                                                      fields = ("name", "relationship", "phone"),
                                                      labels = emergency_contact_represent,
                                                      )

                    # Custom list fields for Africa RDRT
                    phone_label = settings.get_ui_label_mobile_phone()
                    s3db.org_organisation.root_organisation.label = T("National Society")
                    list_fields = ["person_id",
                                   (T("Sectors"), "credential.job_title_id"),
                                   # @todo: Languages?
                                   # @todo: Skills?
                                   (T("Trainings"), "training.course_id"),
                                   "organisation_id$root_organisation",
                                   "type",
                                   "job_title_id",
                                   # @todo: Education?
                                   (T("Status"), "application.active"),
                                   (T("Email"), "email.value"),
                                   (phone_label, "phone.value"),
                                   (T("Address"), "person_id$address.location_id"),
                                   "person_id$date_of_birth",
                                   "person_id$gender",
                                   "person_id$person_details.nationality",
                                   #(T("Passport Number"), "person_id$passport.value"),
                                   #(T("Passport Issuer"), "person_id$passport.ia_name"),
                                   #(T("Passport Date"), "person_id$passport.valid_from"),
                                   #(T("Passport Expires"), "person_id$passport.valid_until"),
                                   (T("Emergency Contacts"), "person_id$contact_emergency.id"),
                                   "person_id$physical_description.blood_type",
                                   ]

                    resource.configure(filter_widgets = filters,
                                       list_fields = list_fields,
                                       profile_widgets = widgets,
                                       profile_header = rdrt_member_profile_header,
                                       )
                else:
                    # AP RDRT

                    # Old requirements:
                    #otable = s3db.org_organisation
                    #org = db(otable.name == AP_ZONE).select(otable.id,
                    #                                        limitby=(0, 1),
                    #                                        cache = s3db.cache,
                    #                                        ).first()
                    #try:
                    #    organisation_id = org.id
                    #except:
                    #    current.log.error("Cannot find org %s - prepop not done?" % AP_ZONE)
                    #    organisation_id = None
                    #else:
                    #    # Filter trainings to courses which belong to
                    #    # the AP_ZONE organisation:
                    #    ctable = s3db.hrm_course
                    #    query = (ctable.organisation_id == organisation_id) & \
                    #            (ctable.deleted != True)
                    #    courses = db(query).select(ctable.id)
                    #    course_ids = [c.id for c in courses]
                    #    s3db.add_components(tablename,
                    #                        hrm_training = {"link": "pr_person",
                    #                                        "joinby": "id",
                    #                                        "key": "id",
                    #                                        "fkey": "person_id",
                    #                                        "pkey": "person_id",
                    #                                        "filterby": {"course_id": course_ids,
                    #                                                     },
                    #                                        },
                    #                        )
                    #    # Reset the component (we're past resource initialization)
                    #    r.resource.components.reset(("training",))

                    record = r.record
                    if record:
                        person_id = record.person_id
                        ptable = db.pr_person
                        person = db(ptable.id == person_id).select(#ptable.first_name,
                                                                   #ptable.middle_name,
                                                                   #ptable.last_name,
                                                                   ptable.pe_id,
                                                                   limitby=(0, 1)
                                                                   ).first()
                        #name = s3_fullname(person)
                        pe_id = person.pe_id

                        def dt_row_actions(w_tablename, c, f, get_var=None):
                            def row_actions(r, list_id):
                                editable = get_config(w_tablename, "editable")
                                if editable is None:
                                    editable = True
                                deletable = get_config(w_tablename, "deletable")
                                if deletable is None:
                                    deletable = True
                                if editable:
                                    get_vars = {"refresh": list_id}
                                    if get_var:
                                        get_vars[get_var] = 1
                                    actions = [{"label": T("Open"),
                                                "url": URL(c=c, f=f,
                                                           args=["[id]", "update.popup"],
                                                           vars=get_vars),
                                                "_class": "action-btn edit s3_modal",
                                                },
                                               ]
                                else:
                                    get_vars = {"refresh": list_id}
                                    if get_var:
                                        get_vars[get_var] = 1
                                    actions = [{"label": T("Open"),
                                                "url": URL(c=c, f=f,
                                                           args=["[id]", "read.popup"],
                                                           vars=get_vars),
                                                "_class": "action-btn edit s3_modal",
                                                },
                                               ]
                                if deletable:
                                    actions.append({"label": T("Delete"),
                                                    "_ajaxurl": URL(c=c, f=f,
                                                                    args=["[id]", "delete.json"],
                                                                    ),
                                                    "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                                                    })
                                return actions
                            return row_actions

                        details_widget = {"label": "Personal Details",
                                          "tablename": "pr_person",
                                          "type": "datalist",
                                          "insert": False,
                                          "list_fields": ["first_name",
                                                          "middle_name",
                                                          "last_name",
                                                          "date_of_birth",
                                                          "gender",
                                                          "person_details.nationality",
                                                          "person_details.nationality2",
                                                          "physical_description.blood_type",
                                                          ],
                                          "filter": FS("id") == person_id,
                                          "icon": "user",
                                          }

                        contacts_widget = {"label": "Contacts",
                                           "label_create": "Add Contact",
                                           "tablename": "pr_contact",
                                           "type": "datalist",
                                           "filter": FS("pe_id") == pe_id,
                                           "icon": "phone",
                                           # Default renderer:
                                           #"list_layout": s3db.pr_render_contact,
                                           "orderby": "priority asc",
                                           # Can't do this as this is the HR perspective, not Person perspective
                                           #"create_controller": c,
                                           #"create_function": "person",
                                           #"create_component": "contact",
                                           }

                        emergency_widget = {"label": "Emergency Contacts",
                                            "label_create": "Add Emergency Contact",
                                            "tablename": "pr_contact_emergency",
                                            "type": "datalist",
                                            "filter": FS("pe_id") == pe_id,
                                            "icon": "phone",
                                            }

                        address_widget = {"label": "Address",
                                          "label_create": "Add Address",
                                          "type": "datalist",
                                          "tablename": "pr_address",
                                          "filter": FS("pe_id") == pe_id,
                                          "icon": "home",
                                          # Default renderer:
                                          #"list_layout": s3db.pr_render_address,
                                          # Can't do this as this is the HR perspective, not Person perspective
                                          #"create_controller": c,
                                          #"create_function": "person",
                                          #"create_component": "address",
                                          }

                        education_widget = {"label": "Education",
                                            "label_create": "Add Education",
                                            "type": "datalist",
                                            "tablename": "pr_education",
                                            "filter": FS("person_id") == person_id,
                                            "icon": "book",
                                            "list_fields": [(T("Qualification"), "level"),
                                                            (T("Field of Expertise"), "major"),
                                                            ],
                                            # Can't do this as this is the HR perspective, not Person perspective
                                            #"create_controller": c,
                                            #"create_function": "person",
                                            #"create_component": "education",
                                            "create_var": "rdrt_ap",
                                            }

                        w_tablename = "hrm_experience"
                        job_widget = {"label": "Current Job Role",
                                      "label_create": "Add Job Role",
                                      "type": "datatable",
                                      "actions": dt_row_actions(w_tablename, "deploy", "experience", "rdrt_ap_current"),
                                      "dt_searching": False,
                                      "tablename": w_tablename,
                                      "filter": (FS("person_id") == person_id) & \
                                                (FS("activity_type") == None),
                                      "icon": "wrench",
                                      "list_fields": ["organisation",
                                                      (T("From"), "start_date"),
                                                      (T("To"), "end_date"),
                                                      (T("Total experience"), "comments"),
                                                      (T("Designation(s)"), "job_title"),
                                                      ],
                                      "create_controller": "deploy",
                                      # Can't do this as this is the HR perspective, not Person perspective
                                      #"create_function": "person",
                                      #"create_component": "experience",
                                      "create_var": "rdrt_ap_current",
                                      "pagesize": 1,
                                      }

                        w_tablename = "hrm_experience"
                        experience_widget = {"label": "NDRT / other Deployments",
                                             "label_create": "Add Deployment",
                                             "type": "datatable",
                                             "actions": dt_row_actions(w_tablename, "deploy", "experience", "rdrt_ap_deployment"),
                                             "dt_searching": False,
                                             "tablename": w_tablename,
                                             "filter": (FS("person_id") == person_id) & \
                                                       (FS("activity_type") == "rdrt"),
                                             "icon": "truck",
                                             "list_fields": ["organisation_id",
                                                             (T("From"), "start_date"),
                                                             (T("To"), "end_date"),
                                                             (T("Disaster situation (flood / earthquake, etc.)"), "comments"),
                                                             (T("Country of Deployment"), "location_id"),
                                                             (T("Skills Utilized"), "responsibilities"),
                                                             ],
                                             "create_controller": "deploy",
                                             # Can't do this as this is the HR perspective, not Person perspective
                                             #"create_function": "person",
                                             #"create_component": "experience",
                                             "create_var": "rdrt_ap_deployment",
                                             "pagesize": 2,
                                             }

                        w_tablename = "pr_language"
                        language_widget = {"label": "Languages",
                                           "label_create": "Add Language",
                                           "type": "datatable",
                                           "actions": dt_row_actions(w_tablename, "pr", "language"),
                                           "dt_searching": False,
                                           "tablename": w_tablename,
                                           "filter": (FS("person_id") == person_id),
                                           "icon": "comment-alt",
                                           #"create_controller": "deploy",
                                           # Can't do this as this is the HR perspective, not Person perspective
                                           #"create_function": "person",
                                           #"create_component": "language",
                                           }

                        w_tablename = "hrm_competency"
                        skills_widget = {"label": "Areas of Expertise",
                                         "label_create": "Add Skill",
                                         "type": "datatable",
                                         "actions": dt_row_actions(w_tablename, "deploy", "competency", "rdrt_ap"),
                                         "dt_searching": False,
                                         "tablename": w_tablename,
                                         "filter": FS("person_id") == person_id,
                                         "icon": "wrench",
                                         "list_fields": ["skill_id",
                                                         "comments",
                                                         ],
                                         "create_controller": "deploy",
                                         # Can't do this as this is the HR perspective, not Person perspective
                                         #"create_function": "person",
                                         #"create_component": "competency",
                                         "create_var": "rdrt_ap",
                                         }

                        docs_widget = {"label": "Documents",
                                       "label_create": "Add Document",
                                       "type": "datalist",
                                       "tablename": "doc_document",
                                       "filter": FS("doc_id") == record.doc_id,
                                       "icon": "attachment",
                                       # Default renderer:
                                       #"list_layout": s3db.doc_document_list_layout,
                                       }

                        from gluon import URL
                        availability_widget = {"label": "Unavailability",
                                               "type": "organizer",
                                               "tablename": "deploy_unavailability",
                                               "master": "pr_person/%s" % person_id,
                                               "component": "unavailability",
                                               "icon": "calendar",
                                               "url": URL(c="deploy", f="person",
                                                          args = [person_id, "unavailability"],
                                                          ),
                                               }

                        profile_widgets = [details_widget,
                                           contacts_widget,
                                           emergency_widget,
                                           address_widget,
                                           education_widget,
                                           job_widget,
                                           experience_widget,
                                           language_widget,
                                           skills_widget,
                                           docs_widget,
                                           availability_widget,
                                           ]

                        # All templates use the same component name for answers so need to add the right component manually
                        dtable = s3db.s3_table
                        ttable = s3db.dc_template
                        query = (ttable.name == "Surge Member") & \
                                (ttable.table_id == dtable.id)
                        template = db(query).select(ttable.id,
                                                    dtable.name,
                                                    limitby=(0, 1),
                                                    ).first()
                        if template:
                            template_id = template[ttable.id]
                            dtablename = template[dtable.name]
                            dtable = s3db[dtablename]
                            components = {dtablename: {"name": "answer",
                                                       "joinby": "response_id",
                                                       "multiple": False,
                                                       }
                                          }
                            s3db.add_components("dc_response", **components)

                            rtable = s3db.dc_response
                            query = (rtable.person_id == person_id) & \
                                    (rtable.template_id == template_id)
                            respnse = db(query).select(rtable.id,
                                                       limitby=(0, 1),
                                                       ).first()
                            if respnse:
                                response_id = respnse[rtable.id]
                                answer = db(dtable.response_id == response_id).select(dtable.id,
                                                                                      limitby = (0, 1)
                                                                                      )
                                if answer:
                                    answer_id = answer.first().id
                                else:
                                    answer_id = dtable.insert(response_id = response_id)
                                    putable = s3db.pr_person_user
                                    user = db(putable.pe_id == pe_id).select(putable.user_id,
                                                                             limitby = (0, 1)
                                                                             ).first()
                                    if user:
                                        db(dtable.id == answer_id).update(owned_by_user = user.user_id)
                            else:
                                response_id = rtable.insert(template_id = template_id,
                                                            person_id = person_id,
                                                            )
                                answer_id = dtable.insert(response_id = response_id)
                                putable = s3db.pr_person_user
                                user = db(putable.pe_id == pe_id).select(putable.user_id,
                                                                         limitby = (0, 1)
                                                                         ).first()
                                if user:
                                    user_id = user.user_id
                                    db(rtable.id == response_id).update(owned_by_user = user_id)
                                    db(dtable.id == answer_id).update(owned_by_user = user_id)

                            dynamic_widget = {"label": "Other Information",
                                              "label_create": "Update Information",
                                              "type": "datalist",
                                              "list_layout": deploy_dynamic_list_layout,
                                              #"type": "datatable",
                                              #"actions": dt_row_actions(dtablename, "dc", "respnse"),
                                              #"dt_searching": False,
                                              "tablename": dtablename,
                                              "filter": FS("response_id") == response_id,
                                              "icon": "comment-alt",
                                              #"list_fields": ["question",
                                              #                "answer",
                                              #                ],
                                              "create_controller": "dc",
                                              "create_function": "respnse",
                                              "create_args": [response_id, "answer", answer_id, "update.popup"],
                                              }

                            profile_widgets.insert(-2, dynamic_widget)
                    else:
                        profile_widgets = []

                    phone_label = settings.get_ui_label_mobile_phone()
                    s3db.org_organisation.root_organisation.label = T("National Society")
                    list_fields = ["person_id",
                                   "organisation_id$root_organisation",
                                   (T("Skills"), "person_id$competency.skill_id"),
                                   (T("Languages"), "person_id$language.language"),
                                   #(T("Status"), "application.active"),
                                   (T("Email"), "email.value"),
                                   (phone_label, "phone.value"),
                                   #(T("Address"), "person_id$address.location_id"),
                                   "person_id$gender",
                                   "person_id$date_of_birth",
                                   "person_id$person_details.nationality",
                                   #(T("Passport Number"), "person_id$passport.value"),
                                   #(T("Passport Issuer"), "person_id$passport.ia_name"),
                                   #(T("Passport Date"), "person_id$passport.valid_from"),
                                   #(T("Passport Expires"), "person_id$passport.valid_until"),
                                   #"person_id$physical_description.blood_type",
                                   #(T("Emergency Contacts"), "person_id$contact_emergency.id"),
                                   ]

                    resource.configure(filter_widgets = deploy_member_filters_ap(),
                                       list_fields = list_fields,
                                       profile_widgets = profile_widgets,
                                       profile_header = rdrt_member_profile_header,
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
                if vnrc and r.method != "report" and \
                            "form" in output and \
                            (controller == "vol" or \
                             r.component_name == "human_resource"):
                    # Remove the injected Programme field
                    del output["form"][0].components[4]
                    del output["form"][0].components[4]

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_hrm_job_title_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3
        controller = current.request.controller
        if controller == "deploy":
            deploy = True
            # Filter to just deployables
            table = s3db.hrm_job_title
            s3.filter = (table.type == 4)
        else:
            deploy = False
            # Organisation needs to be an NS
            ns_only("hrm_job_title",
                    required = False,
                    branches = False,
                    )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if deploy:
                field = table.type
                field.default = 4
                field.readable = field.writable = False
                table.organisation_id.readable = False
                table.organisation_id.writable = False
                field = table.region_id
                field.readable = field.writable = True
                from gluon import IS_EMPTY_OR
                from s3 import IS_ONE_OF
                field.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(current.db, "org_region.id",
                                              s3db.org_region_represent,
                                              sort=True,
                                              # Only show the Top-Level Regions (Formerly called Zones)
                                              filterby="parent",
                                              filter_opts=(None,)
                                              ))

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

            elif current.auth.s3_has_role("ADMIN"):
                from s3 import S3OptionsFilter, S3TextFilter
                filter_widgets = [S3TextFilter(["name",
                                                ],
                                               label=T("Search")
                                               ),
                                  S3OptionsFilter("organisation_id",
                                                  ),
                                  ]
                s3db.configure("hrm_job_title",
                               filter_widgets = filter_widgets,
                               )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

    # -------------------------------------------------------------------------
    def customise_hrm_programme_controller(**attr):

        # Organisation needs to be an NS
        ns_only("hrm_programme",
                required = False,
                branches = False,
                )

        # Special cases for different NS/roles
        root_org = current.auth.root_org_name()
        if root_org in (CVTL, PMI, PRC):
            settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
        elif root_org == IRCS:
            table = current.s3db.hrm_programme_hours
            table.date.label = T("Direct Date")
            table.contract.label = T("Direct Number")
            table.contract.readable = table.contract.writable = True
            table.hours.readable = table.hours.writable = False
        #elif root_org == VNRC:
            # @ToDo
            # def vn_age_group(age):
            # settings.pr.age_group = vn_age_group
        else:
            auth = current.auth
            if not auth.s3_has_role("ADMIN") and \
               auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
                # Bangkok CCST
                organisation_id = auth.user.organisation_id
                # Filter Programmes to just those from this Org
                from s3 import FS
                current.response.s3.filter = \
                    FS("~.organisation_id") == organisation_id

                # Default to this Org, not to root_org
                current.s3db.hrm_programme.organisation_id.default = organisation_id

        return attr

    settings.customise_hrm_programme_controller = customise_hrm_programme_controller

    # -------------------------------------------------------------------------
    def customise_hrm_programme_hours_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.person_id$human_resource.organisation_id",
                              user_org_default_filter,
                              tablename = "hrm_programme_hours")

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == IRCS:
            table = current.s3db.hrm_programme_hours
            table.date.label = T("Direct Date")
            table.contract.label = T("Direct Number")
            table.contract.readable = table.contract.writable = True
            table.hours.readable = table.hours.writable = False
        elif root_org == VNRC:
            # Remove link to download Template
            attr["csv_template"] = "hide"

        return attr

    settings.customise_hrm_programme_hours_controller = customise_hrm_programme_hours_controller

    # -------------------------------------------------------------------------
    def customise_hrm_training_controller(**attr):

        db = current.db
        s3db = current.s3db

        tablename = "hrm_training"

        # Special cases for different NS/roles
        auth = current.auth
        if not auth.s3_has_role("ADMIN") and \
           auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
            # Bangkok CCST
            s3db.hrm_training.person_id.represent = s3db.pr_PersonRepresent(show_link=True)
            from s3 import FS
            # Filter People to just those conducted by the region
            # @ToDo: Filter by Org too if more EVENT_* teams come onboard
            gtable = db.auth_group
            mtable = db.auth_membership
            query = (gtable.uuid.belongs(("EVENT_MONITOR", "EVENT_ORGANISER"))) & \
                    (mtable.group_id == gtable.id) & \
                    (mtable.deleted == False)
            rows = db(query).select(mtable.user_id)
            user_ids = [row.user_id for row in rows]
            filter = FS("~.training_event_id$created_by").belongs(set(user_ids))

            # & from this region's countries? No!
            #ltable = s3db.org_organisation_organisation
            #root_orgs = db(ltable.parent_id == auth.user.organisation_id).select(ltable.organisation_id)
            #root_orgs = [o.organisation_id for o in root_orgs]
            #filter |= FS("~.person_id$human_resource.organisation_id$root_organisation").belongs(root_orgs)

            current.response.s3.filter = filter

            # Enable the Status field & label accordingly
            f = s3db.hrm_training.role
            f.readable = f.writable = True
            f.label = T("Status")

            list_fields = ["person_id",
                           (settings.get_hrm_organisation_label(), "person_id$human_resource.organisation_id"),
                           (T("Event"), "training_event_id"),
                           "date",
                           "role",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        else:
            # Default Filter
            from s3 import s3_set_default_filter
            s3_set_default_filter("~.person_id$human_resource.organisation_id",
                                  user_org_default_filter,
                                  tablename = tablename)

            root_org = auth.root_org_name()

            if root_org == VNRC:
                # Remove link to download Template
                attr["csv_template"] = "hide"

            elif current.request.controller == "deploy" and _is_asia_pacific():
                # AP RDRT
                # - only interested in RDRT courses

                ttable = s3db.hrm_training

                otable = s3db.org_organisation
                org = db(otable.name == AP_ZONE).select(otable.id,
                                                        limitby=(0, 1),
                                                        cache = s3db.cache,
                                                        ).first()
                try:
                    organisation_id = org.id
                except:
                    current.log.error("Cannot find org %s - prepop not done?" % AP_ZONE)
                    organisation_id = None
                else:
                    from s3 import FS, IS_ONE_OF
                    current.response.s3.filter = (FS("~.course_id$organisation_id") == organisation_id)
                    ctable = s3db.hrm_course
                    query = (ctable.organisation_id == organisation_id) & \
                            (ctable.deleted == False)
                    courses = db(query).select(ctable.id,
                                               ctable.name,
                                               )
                    field = ttable.course_id
                    field.requires = IS_ONE_OF(db, "hrm_course.id",
                                               field.represent,
                                               filterby="id",
                                               filter_opts=[c.id for c in courses],
                                               )

                # Grades 1-4
                course_grade_opts = {1: "1: %s" % T("Unsatisfactory"),
                                     2: "2: %s" % T("Partially achieved expectations"),
                                     3: "3: %s" % T("Fully achieved expectations"),
                                     4: "4: %s" % T("Exceeded expectations"),
                                     }
                field = ttable.grade
                field.readable = field.writable = True
                field.represent = None
                from gluon import IS_EMPTY_OR, IS_IN_SET
                field.requires = IS_EMPTY_OR(IS_IN_SET(course_grade_opts,
                                                       zero=None))

                # Upload Performance Appraisal
                field = ttable.file
                field.readable = field.writable = True
                field.label = T("Performance Appraisal")

                # Customise Filter Widgets
                filter_widgets = s3db.get_config(tablename, "filter_widgets")
                found = None
                index = 0
                for w in filter_widgets:
                    if w.field == "person_id$location_id":
                        found = index
                    elif w.field == "grade":
                        w.opts.options = dict((g, g) for g in course_grade_opts)
                    elif organisation_id and w.field == "course_id":
                        w.opts.options = dict((c.id, T(c.name)) for c in courses)
                    elif w.field == "training_event_id$site_id":
                        w.opts.label = T("Training Location")
                        w.opts.represent = s3db.org_SiteRepresent(show_type = False)
                    index += 1
                if found is not None:
                    filter_widgets.pop(found)

                # Customise Report Options
                report_fields = [(T("Training Event"), "training_event_id"),
                                 "person_id",
                                 "course_id",
                                 "grade",
                                 (T("National Society"), "person_id$human_resource.organisation_id"),
                                 (T("Region"), "person_id$human_resource.organisation_id$organisation_region.region_id"),
                                 (T("Training Location"), "training_event_id$site_id"),
                                 #(T("Month"), "month"),
                                 (T("Year"), "year"),
                                 ]

                report_options = Storage(rows = report_fields,
                                         cols = report_fields,
                                         fact = report_fields,
                                         methods = ["count", "list"],
                                         defaults = Storage(
                                            rows = "person_id$human_resource.organisation_id$organisation_region.region_id",
                                            cols = "training.course_id",
                                            fact = "count(training.person_id)",
                                            totals = True,
                                            )
                                        )

                s3db.configure(tablename,
                               report_options = report_options,
                               )

        return attr

    settings.customise_hrm_training_controller = customise_hrm_training_controller

    # -------------------------------------------------------------------------
    def deploy_status_update(organisation_id, person_id, membership):
        """
            Update the status of AP RDRT members based on their
            Trainings & Deployments
        """

        db = current.db
        s3db = current.s3db

        # Which RDRT courses has the person taken?
        ctable = s3db.hrm_course
        ttable = s3db.hrm_training
        query = (ttable.person_id == person_id) & \
                (ttable.deleted == False) & \
                (ttable.course_id == ctable.id) & \
                (ctable.organisation_id == organisation_id)
        courses = db(query).select(ttable.grade,
                                   ttable.course_id,
                                   ctable.name,
                                   )

        new_status = 5 # Default Status
        for course in courses:
            grade = course["hrm_training.grade"]
            if course["hrm_course.name"] == "RDRT Induction":
                if grade == 1:
                    # Fail
                    if new_status == 5:
                        new_status = 4
                        # Continue to look for Specialist
                    else:
                        # Ignore
                        pass
                elif grade:
                    # Pass
                    new_status = 2
                    break
            elif grade > 1:
                # Pass
                new_status = 3
                # Continue to look for a passed Induction

        if new_status == 2:
            # Has the person been deployed already?
            astable = s3db.deploy_assignment
            ltable = s3db.deploy_assignment_appraisal
            aptable = s3db.hrm_appraisal
            query = (astable.human_resource_id == membership.human_resource_id) & \
                    (astable.id == ltable.assignment_id) & \
                    (ltable.appraisal_id == aptable.id)
            latest_appraisal = db(query).select(aptable.rating,
                                                aptable.date,
                                                orderby = aptable.date,
                                                limitby = (0, 1)
                                                ).first()

            if latest_appraisal:
                if latest_appraisal.rating > 1:
                    # Pass
                    new_status = 1
                else:
                    # Fail
                    new_status = 4

        if new_status != membership.status:
            # Update the record
            membership.update_record(status = new_status)

    # -------------------------------------------------------------------------
    def hrm_appraisal_onaccept(form):
        """
            If the person is a member of the AP RDRT then update their status
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars

        # Find the Person
        person_id = form_vars.person_id
        if not person_id:
            # Load the record
            table = s3db.hrm_appraisal
            record = db(table.id == form_vars.id).select(table.person_id,
                                                         limitby=(0, 1)
                                                         ).first()
            person_id = record.person_id

        # Lookup the AP_ZONE ID
        otable = s3db.org_organisation
        org = db(otable.name == AP_ZONE).select(otable.id,
                                                limitby=(0, 1),
                                                cache = s3db.cache,
                                                ).first()
        try:
            organisation_id = org.id
        except:
            current.log.error("Cannot find org %s - prepop not done?" % AP_ZONE)
            return

        # Are they a member of the AP RDRT?
        htable = s3db.hrm_human_resource
        atable = s3db.deploy_application
        query = (htable.person_id == person_id) & \
                (atable.human_resource_id == htable.id) & \
                (atable.organisation_id == organisation_id)
        membership = db(query).select(atable.id,
                                      atable.human_resource_id,
                                      atable.status,
                                      limitby = (0, 1)
                                      ).first()
        if membership:
            deploy_status_update(organisation_id, person_id, membership)

    # -------------------------------------------------------------------------
    def customise_hrm_appraisal_resource(r, tablename):

        # Add custom onaccept
        s3db = current.s3db
        default = s3db.get_config(tablename, "onaccept")
        if not default:
            onaccept = hrm_appraisal_onaccept
        elif not isinstance(default, list):
            onaccept = [hrm_appraisal_onaccept, default]
        else:
            onaccept = default
            if all(cb != hrm_appraisal_onaccept for cb in onaccept):
                onaccept.append(hrm_appraisal_onaccept)
        s3db.configure(tablename,
                       onaccept = onaccept,
                       )

    settings.customise_hrm_appraisal_resource = customise_hrm_appraisal_resource

    # -------------------------------------------------------------------------
    def customise_hrm_competency_resource(r, tablename):

        if r.get_vars.get("rdrt_ap"):
            # Simplify for RDRT AP

            from s3 import IS_ONE_OF, S3SQLCustomForm

            db = current.db
            s3db = current.s3db

            sttable = s3db.hrm_skill_type
            RDRT_AP = db(sttable.name == "RDRT_AP").select(sttable.id,
                                                           limitby = (0,1)
                                                           ).first().id

            table = s3db.hrm_competency
            f = table.skill_id
            f.comment = None
            f.requires = IS_ONE_OF(db, "hrm_skill.id",
                                   S3Represent(lookup = "hrm_skill",
                                               translate = True),
                                   filterby = "skill_type_id",
                                   filter_opts = (RDRT_AP,),
                                   sort = True,
                                   )
            table.comments.comment = None
            s3db.configure("hrm_competency",
                           crud_form = S3SQLCustomForm("skill_id",
                                                       "comments",
                                                       ),
                           )

    settings.customise_hrm_competency_resource = customise_hrm_competency_resource

    # -------------------------------------------------------------------------
    def hrm_training_onaccept(form):
        """
            If the person is a member of the AP RDRT then update their status
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars

        # Find the Person
        person_id = form_vars.person_id
        if not person_id:
            # Load the record
            table = s3db.hrm_training
            record = db(table.id == form_vars.id).select(table.person_id,
                                                         limitby=(0, 1)
                                                         ).first()
            person_id = record.person_id

        # Lookup the AP_ZONE ID
        otable = s3db.org_organisation
        org = db(otable.name == AP_ZONE).select(otable.id,
                                                limitby=(0, 1),
                                                cache = s3db.cache,
                                                ).first()
        try:
            organisation_id = org.id
        except:
            current.log.error("Cannot find org %s - prepop not done?" % AP_ZONE)
            return

        # Are they a member of the AP RDRT?
        htable = s3db.hrm_human_resource
        atable = s3db.deploy_application
        query = (htable.person_id == person_id) & \
                (atable.human_resource_id == htable.id) & \
                (atable.organisation_id == organisation_id)
        membership = db(query).select(atable.id,
                                      atable.human_resource_id,
                                      atable.status,
                                      limitby = (0, 1)
                                      ).first()
        if membership:
            deploy_status_update(organisation_id, person_id, membership)

    # -------------------------------------------------------------------------
    def hrm_training_event_notify(r, **attr):
        """
            Notify Participants to fill out the Survey
            - exclude Observers
        """

        from gluon import redirect, URL

        training_event_id = r.id

        hrm_notify_participants(training_event_id, redirect=True)

        # Redirect to main event page
        redirect(URL(args=[training_event_id]))

    # -------------------------------------------------------------------------
    def customise_hrm_training_resource(r, tablename):

        # Add custom onaccept
        s3db = current.s3db
        default = s3db.get_config(tablename, "onaccept")
        if not default:
            onaccept = hrm_training_onaccept
        elif not isinstance(default, list):
            onaccept = [hrm_training_onaccept, default]
        else:
            onaccept = default
            if all(cb != hrm_training_onaccept for cb in onaccept):
                onaccept.append(hrm_training_onaccept)
        s3db.configure(tablename,
                       onaccept = onaccept,
                       )

    settings.customise_hrm_training_resource = customise_hrm_training_resource

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_controller(**attr):

        s3db = current.s3db

        # Special cases for different NS/roles
        EVENTS = False
        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            # Remove link to download Template
            attr["csv_template"] = "hide"
        else:
            auth = current.auth

            set_method = s3db.set_method
            set_method("hrm", "training_event",
                       method = "notify",
                       action = hrm_training_event_notify)

            if not auth.s3_has_role("ADMIN"):
                if auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
                    # Bangkok CCST
                    EVENTS = True

                    from s3 import FS

                    db = current.db

                    organisation_id = auth.user.organisation_id

                    # Filter Events to just those created by the regional staff
                    # @ToDo: Filter by Org too if more EVENT_* teams come onboard
                    gtable = db.auth_group
                    mtable = db.auth_membership
                    query = (gtable.uuid.belongs(("EVENT_MONITOR", "EVENT_ORGANISER"))) & \
                            (mtable.group_id == gtable.id) & \
                            (mtable.deleted == False)
                    rows = db(query).select(mtable.user_id)
                    user_ids = [row.user_id for row in rows]
                    filter = FS("~.created_by").belongs(set(user_ids))

                    # & those from this region's countries? No!
                    #ltable = s3db.org_organisation_organisation
                    #root_orgs = db(ltable.parent_id == auth.user.organisation_id).select(ltable.organisation_id)
                    #root_orgs = [o.organisation_id for o in root_orgs]
                    #filter |= FS("~.organisation_id$root_organisation").belongs(root_orgs)
                    current.response.s3.filter = filter

        # Custom prep
        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if root_org == NRCS and r.component_name == "participant":
                # Don't allow creating of Persons here
                from gluon import DIV
                s3db.hrm_training.person_id.comment = \
                    DIV(_class="tooltip",
                        _title="%s|%s" % (T("Participant"),
                                          T("Type the first few characters of one of the Participant's names.")))

            elif EVENTS:
                if not r.component:
                    if r.get_vars.get("dashboard"):
                        # Dashboard for Office Manager
                        #from dateutil.relativedelta import relativedelta
                        from s3 import S3DateTime, s3_fieldmethod

                        etable = s3db.hrm_training_event
                        etable.created_by.represent = s3db.auth_UserRepresent(show_email = False,
                                                                              show_link = False)
                        # Represent just with Date not Datetime
                        date_represent = S3DateTime.date_represent
                        etable.start_date.represent = date_represent
                        etable.end_date.represent = date_represent

                        # Virtual Fields for Dashboard
                        ttable = s3db.dc_target
                        ltable = s3db.dc_target_event
                        rtable = s3db.dc_response
                        squery = (etable.id == ltable.training_event_id) & \
                                 (ttable.id == ltable.target_id)
                        rquery = squery & (rtable.target_id == ttable.id)

                        def month3(row):
                            query = squery & \
                                    (ltable.survey_type == 3) & \
                                    (etable.id == row["hrm_training_event.id"])
                            target = db(query).select(ttable.deleted,
                                                      ttable.approved_by,
                                                      limitby = (0, 1)
                                                      ).first()
                            if not target:
                                status = T("No Survey")
                            elif target.deleted:
                                status = T("Rejected")
                            elif not target.approved_by:
                                status = T("Ignored")
                            else:
                                status = T("Accepted")
                            return status
                        etable.month3 = s3_fieldmethod("month3", month3)

                        def month12(row):
                            query = squery & \
                                    (ltable.survey_type == 12) & \
                                    (etable.id == row["hrm_training_event.id"])
                            target = db(query).select(ttable.deleted,
                                                      ttable.approved_by,
                                                      limitby = (0, 1)
                                                      ).first()
                            if not target:
                                status = T("No Survey")
                            elif target.deleted:
                                status = T("Rejected")
                            elif not target.approved_by:
                                status = T("Ignored")
                            else:
                                status = T("Accepted")
                            return status
                        etable.month12 = s3_fieldmethod("month12", month12)

                        def month3_resp(row):
                            query = rquery & \
                                    (ltable.survey_type == 3) & \
                                    (etable.id == row["hrm_training_event.id"])
                            responses = db(query).select(rtable.date)
                            total = len(responses)
                            responded = len([resp.date for resp in responses if resp.date is not None])
                            response_rate = "%s / %s" % (responded, total)
                            return response_rate
                        etable.month3_resp = s3_fieldmethod("month3_resp", month3_resp)

                        def month12_resp(row):
                            query = rquery & \
                                    (ltable.survey_type == 12) & \
                                    (etable.id == row["hrm_training_event.id"])
                            responses = db(query).select(rtable.date)
                            total = len(responses)
                            responded = len([resp.date for resp in responses if resp.date is not None])
                            response_rate = "%s / %s" % (responded, total)
                            return response_rate
                        etable.month12_resp = s3_fieldmethod("month12_resp", month12_resp)

                        list_fields = ["name",
                                       ("EO", "created_by"),
                                       "start_date",
                                       "end_date",
                                       (T("3 month survey"), "month3"),
                                       (T("Respondents"), "month3_resp"),
                                       (T("12 month survey"), "month12"),
                                       (T("Respondents"), "month12_resp"),
                                       ]

                        s3db.configure("hrm_training_event",
                                       extra_fields = ["deleted"],
                                       listadd = False,
                                       list_fields = list_fields,
                                       )
                    else:
                        from gluon import IS_EMPTY_OR
                        from s3 import IS_ONE_OF, S3SQLCustomForm, S3SQLInlineLink

                        # Default Programme Org to this Branch, not root (for imports)
                        s3db.hrm_programme.organisation_id.default = organisation_id

                        # Enable the Status field & label accordingly
                        f = s3db.hrm_training.role
                        f.readable = f.writable = True
                        f.label = T("Status")

                        # Filter Programmes to this Org (not root)
                        #f = s3db.project_programme_event.programme_id
                        #f.requires = IS_EMPTY_OR(
                        #                IS_ONE_OF(db, "hrm_programme.id",
                        #                          f.represent,
                        #                          filterby = "organisation_id",
                        #                          filter_opts = (organisation_id,),
                        #                          ))

                        # Customise
                        crud_form = S3SQLCustomForm("name",

                                                    # If these are-required in-future then create link tables for them in Project module
                                                    #S3SQLInlineLink("strategy",
                                                    #                field = "strategy_id",
                                                    #                label = T("AoF/SFI"),
                                                    #                multiple = False,
                                                    #                ),
                                                    #S3SQLInlineLink("programme",
                                                    #                field = "programme_id",
                                                    #                label = T("Programme"),
                                                    #                multiple = False,
                                                    #                ),
                                                    #S3SQLInlineLink("project",
                                                    #                field = "project_id",
                                                    #                label = T("Project"),
                                                    #                multiple = False,
                                                    #                required = True,
                                                    #                ),

                                                    "event_type_id",
                                                    "location_id",
                                                    "organisation_id",
                                                    "start_date",
                                                    "end_date",
                                                    "comments",
                                                    )

                        list_fields = ["name",
                                       #(T("AoF/SFI"), "strategy__link.strategy_id"),
                                       #"programme__link.programme_id",
                                       #"project__link.project_id",
                                       "event_type_id",
                                       "location_id$L0",
                                       "location_id$L1",
                                       "location_id$L2",
                                       "location_id$L3",
                                       "organisation_id",
                                       "start_date",
                                       "end_date",
                                       ]

                        s3db.configure("hrm_training_event",
                                       crud_form = crud_form,
                                       list_fields = list_fields,
                                       )

                elif r.component_name == "participant":
                    s3db.hrm_training.person_id.represent = s3db.pr_PersonRepresent(show_link=True)
                    s3db.configure("hrm_training",
                                   list_fields = ["person_id",
                                                  (T("Job Title"), "job_title"),                    # Field.Method
                                                  (settings.get_hrm_organisation_label(), "organisation"),  # Field.Method
                                                  ],
                                   )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller

    # -------------------------------------------------------------------------
    def hrm_training_event_onaccept(form):
        """
            Create a Scheduled Task to notify EO / MFP to run survey
        """

        form_vars = form.vars

        try:
            training_event_id = form_vars.id
        except:
            # Nothing we can do
            return

        db = current.db
        s3db = current.s3db

        start_date = form_vars.get("start_date")
        end_date = form_vars.get("end_date")
        if not start_date or not end_date:
            # Read the record
            etable = s3db.hrm_training_event
            event = db(etable.id == training_event_id).select(etable.start_date,
                                                              etable.end_date,
                                                              limitby = (0, 1)
                                                              ).first()
            start_date = event.start_date
            end_date = event.end_date

        # Prefer end_date if-available, otherwise use start_date
        end_date = end_date or start_date

        if not end_date:
            # No date defined, so exit
            return

        import json
        json_dumps = json.dumps
        from dateutil.relativedelta import relativedelta
        ttable = s3db.scheduler_task
        schedule_task = current.s3task.schedule_task
        task_name = "settings_task"

        # 3 month reminder
        start_time = end_date + relativedelta(months = 3)
        args = ["hrm_training_event_survey"]
        vars = {"training_event_id": training_event_id,
                "survey_type": 3,
                }
        query = (ttable.task_name == task_name) & \
                (ttable.args == json_dumps(args)) & \
                (ttable.vars == json_dumps(vars))
        exists = db(query).select(ttable.id,
                                  ttable.start_time,
                                  limitby = (0, 1)
                                  ).first()
        if exists:
            if exists.start_time != start_time:
                exists.update_record(start_time = start_time)
        else:
            schedule_task(task_name,
                          args = args,
                          vars = vars,
                          start_time = start_time,
                          #period = 300,  # seconds
                          timeout = 300, # seconds
                          repeats = 1    # run once
                          )

        # 12 month reminder
        start_time = end_date + relativedelta(months = 12)
        vars = {"training_event_id": training_event_id,
                "survey_type": 12,
                }
        query = (ttable.task_name == task_name) & \
                (ttable.args == json_dumps(args)) & \
                (ttable.vars == json_dumps(vars))
        exists = db(query).select(ttable.id,
                                  ttable.start_time,
                                  limitby = (0, 1)
                                  ).first()
        if exists:
            if exists.start_time != start_time:
                exists.update_record(start_time = start_time)
        else:
            schedule_task(task_name,
                          args = args,
                          vars = vars,
                          start_time = start_time,
                          #period = 300,  # seconds
                          timeout = 300, # seconds
                          repeats = 1    # run once
                          )

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_resource(r, tablename):

        # Add custom onaccept
        s3db = current.s3db
        default = s3db.get_config(tablename, "onaccept")
        if not default:
            onaccept = hrm_training_event_onaccept
        elif not isinstance(default, list):
            onaccept = [hrm_training_event_onaccept, default]
        else:
            onaccept = default
            if all(cb != hrm_training_event_onaccept for cb in onaccept):
                onaccept.append(hrm_training_event_onaccept)
        s3db.configure(tablename,
                       onaccept = onaccept,
                       )

    settings.customise_hrm_training_event_resource = customise_hrm_training_event_resource

    # -------------------------------------------------------------------------
    def customise_inv_home():
        """
            Homepage for the Inventory module
        """

        from gluon import URL
        from s3 import s3_redirect_default

        # Redirect to Warehouse Summary Page
        s3_redirect_default(URL(c="inv", f="warehouse", args="summary"))

    settings.customise_inv_home = customise_inv_home

    # -------------------------------------------------------------------------
    def customise_inv_inv_item_resource(r, tablename):

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org in (AURC, CRMADA, IRCS):
            # Proper Logistics workflow
            settings.inv.direct_stock_edits = False
            current.s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )

    settings.customise_inv_inv_item_resource = customise_inv_inv_item_resource

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def customise_inv_warehouse_resource(r, tablename):

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org in (AURC, CRMADA, IRCS):
            # Proper Logistics workflow
            settings.inv.direct_stock_edits = False
        if root_org != NRCS:
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

    # -------------------------------------------------------------------------
    def member_membership_paid(row):
        """
            Simplified variant of the original function in s3db/member.py,
            with just "paid"/"unpaid"/"exempted" as possible values
        """

        if hasattr(row, "member_membership"):
            row = row.member_membership

        try:
            exempted = row.fee_exemption
        except AttributeError:
            exempted = False
        if exempted:
            return T("exempted")

        try:
            start_date = row.start_date
        except AttributeError:
            start_date = None
        try:
            paid_date = row.membership_paid
        except AttributeError:
            paid_date = None
        if start_date:
            now = current.request.utcnow.date()
            if not paid_date:
                due = datetime.date(start_date.year + 1,
                                    start_date.month,
                                    start_date.day)
            else:
                due = datetime.date(paid_date.year,
                                    start_date.month,
                                    start_date.day)
                if due < paid_date:
                    due = datetime.date(paid_date.year + 1, due.month, due.day)
            result = T("paid") if now < due else T("unpaid")
        else:
            result = current.messages["NONE"]
        return result

    # -------------------------------------------------------------------------
    def customise_member_membership_resource(r, tablename):

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            from s3 import IS_ONE_OF, S3LocationSelector, S3SQLCustomForm, S3SQLInlineComponent

            # Go back to Create form after submission
            current.session.s3.rapid_data_entry = True

            #db = current.db
            s3db = current.s3db
            tablename = "member_membership"

            settings.pr.request_email = False
            settings.pr.request_mobile_phone = False
            settings.pr.separate_name_fields = 2
            #settings.pr.request_year_of_birth = True
            mtable = s3db.member_membership
            f = mtable.leaving_reason
            f.readable = f.writable = True
            f = mtable.restart_date
            f.readable = f.writable = True
            f = mtable.election
            f.readable = f.writable = True
            f = mtable.trainings
            f.readable = f.writable = True
            mtable.comments.label = T("Remarks")
            # Ensure that + appears at the beginning of the number
            # Done in controllers/member.py
            #f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
            #f.represent = s3_phone_represent
            #f.widget = S3PhoneWidget()
            s3db.pr_address.location_id.widget = S3LocationSelector(show_address = T("Village"),
                                                                    show_map = False)
            ptable = s3db.pr_person
            ptable.first_name.label = T("Name")
            ptable.gender.label = T("Gender")
            dtable = s3db.pr_person_details
            dtable.father_name.label = T("Father Name")
            dtable.grandfather_name.label = T("Grand Father Name")
            #dtable.company.label = T("Place of Work")
            etable = s3db.pr_education
            etable.level_id.comment = None # Don't Add Education Levels inline
            f = etable.level_id
            f.requires = IS_ONE_OF(current.db, "pr_education_level.id",
                                   f.represent,
                                   filterby = "organisation_id",
                                   filter_opts = (current.auth.root_org(),),
                                   )
            s3db.pr_image.image.widget = None # ImageCropWidget doesn't work inline
            #ctable = s3db.hrm_course
            #query = (ctable.organisation_id == current.auth.root_org()) & \
            #        (ctable.type == 4) & \
            #        (ctable.deleted != True)
            #courses = db(query).select(ctable.id)
            #course_ids = [c.id for c in courses]
            #f = s3db.hrm_training.course_id
            #f.requires = IS_ONE_OF(db, "hrm_course.id",
            #                       f.represent,
            #                       filterby = "id",
            #                       filter_opts = course_ids,
            #                       orderby = "hrm_course.name",
            #                       sort = True
            #                       )

            s3db.add_components(tablename,
                                #hrm_training = {"link": "pr_person",
                                #                "joinby": "id",
                                #                "key": "id",
                                #                "fkey": "person_id",
                                #                "pkey": "person_id",
                                #                "filterby": {"course_id": course_ids,
                                #                             },
                                #                },
                                pr_address = ({"name": "perm_address",
                                               "link": "pr_person",
                                               "joinby": "id",
                                               "key": "pe_id",
                                               "fkey": "pe_id",
                                               "pkey": "person_id",
                                               "filterby": {"type": "2",
                                                            },
                                               },
                                              {"name": "temp_address",
                                               "link": "pr_person",
                                               "joinby": "id",
                                               "key": "pe_id",
                                               "fkey": "pe_id",
                                               "pkey": "person_id",
                                               "filterby": {"type": "1",
                                                            },
                                               },
                                              ),
                                pr_contact = {"link": "pr_person",
                                              "joinby": "id",
                                              "key": "pe_id",
                                              "fkey": "pe_id",
                                              "pkey": "person_id",
                                              "filterby": {"contact_method": "SMS",
                                                           },
                                              },
                                pr_contact_emergency = {"link": "pr_person",
                                                        "joinby": "id",
                                                        "key": "pe_id",
                                                        "fkey": "pe_id",
                                                        "pkey": "person_id",
                                                        },
                                pr_education = {"link": "pr_person",
                                                "joinby": "id",
                                                "key": "id",
                                                "fkey": "person_id",
                                                "pkey": "person_id",
                                                },
                                pr_identity = {"name": "idcard",
                                               "link": "pr_person",
                                               "joinby": "id",
                                               "key": "id",
                                               "fkey": "person_id",
                                               "pkey": "person_id",
                                               "filterby": {"type": 2,
                                                            },
                                               "multiple": False,
                                               },
                                pr_image = {"link": "pr_person",
                                            "joinby": "id",
                                            "key": "pe_id",
                                            "fkey": "pe_id",
                                            "pkey": "person_id",
                                            "filterby": {"profile": True,
                                                         },
                                            "multiple": False,
                                            },
                                pr_person_details = {"link": "pr_person",
                                                     "joinby": "id",
                                                     "key": "id",
                                                     "fkey": "person_id",
                                                     "pkey": "person_id",
                                                     },
                                pr_physical_description = {"link": "pr_person",
                                                           "joinby": "id",
                                                           "key": "pe_id",
                                                           "fkey": "pe_id",
                                                           "pkey": "person_id",
                                                           },
                                )

            crud_form = S3SQLCustomForm("organisation_id",
                                        (T("Code No."), "code"),
                                        "person_id",
                                        S3SQLInlineComponent("perm_address",
                                                             label = T("Permanent Address"),
                                                             fields = [("", "location_id")],
                                                             filterby = {"field": "type",
                                                                         "options": 2,
                                                                         },
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("temp_address",
                                                             label = T("Temporary Address"),
                                                             fields = [("", "location_id")],
                                                             filterby = {"field": "type",
                                                                         "options": 1,
                                                                         },
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("person_details",
                                                             label = T("Place of Work"),
                                                             fields = [("", "company")],
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("education",
                                                             label = T("Education Level"),
                                                             fields = [("", "level_id")],
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("idcard",
                                                             label = T("ID Number"),
                                                             fields = [("", "value")],
                                                             filterby = {"field": "type",
                                                                         "options": 2,
                                                                         },
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("physical_description",
                                                             label = T("Blood Group"),
                                                             fields = [("", "blood_type")],
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("phone",
                                                             label = T("Phone Number"),
                                                             fields = [("", "value")],
                                                             filterby = {"field": "contact_method",
                                                                         "options": "SMS",
                                                                         },
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("contact_emergency",
                                                             label = T("Relatives Contact #"),
                                                             fields = [("", "phone")],
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        (T("Date of Recruitment"), "start_date"),
                                        (T("Date of Dismissal"), "end_date"),
                                        (T("Reason for Dismissal"), "leaving_reason"),
                                        (T("Date of Re-recruitment"), "restart_date"),
                                        (T("Monthly Membership Fee"), "membership_fee"),
                                        (T("Membership Fee Last Paid"), "membership_paid"),
                                        "membership_due",
                                        "election",
                                        "trainings",
                                        #S3SQLInlineComponent("training",
                                        #                     label = T("Trainings"),
                                        #                     fields = (("", "course_id"),
                                        #                               ("", "date"),
                                        #                                ),
                                        #                     link = False,
                                        #                     update_link = False,
                                        #                     ),
                                        "comments",
                                        S3SQLInlineComponent("image",
                                                             label = T("Photo"),
                                                             fields = [("", "image")],
                                                             filterby = {"field": "profile",
                                                                         "options": True,
                                                                         },
                                                             link = False,
                                                             update_link = False,
                                                             multiple = False,
                                                             ),
                                        )

            s3db.configure(tablename,
                           create_next = None,
                           crud_form= crud_form,
                           )

            list_fields = s3db.get_config(tablename, "list_fields")
            try:
                list_fields.remove((T("Email"), "email.value"))
            except:
                # Already removed
                pass

        elif root_org == NRCS:
            current.s3db.member_membership.membership_paid.label = \
                T("Membership Approved")

    settings.customise_member_membership_resource = customise_member_membership_resource

    # -------------------------------------------------------------------------
    def customise_member_membership_controller(**attr):

        s3db = current.s3db
        tablename = "member_membership"

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_and_children_default_filter,
                              tablename = tablename)

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        nrcs = vnrc = False
        if root_org == NRCS:
            nrcs = True
        elif root_org == VNRC:
            vnrc = True
            # Remove link to download Template
            attr["csv_template"] = "hide"

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
            ns_only(tablename,
                    required = True,
                    branches = True,
                    limit_filter_opts = True,
                    )

            # Set the NS filter as Visible so that the default filter works
            filter_widgets = s3db.get_config(tablename, "filter_widgets")
            for widget in filter_widgets:
                if widget.field == "organisation_id":
                    widget.opts.hidden = False
                    break

            if nrcs:
                # Remove the Paid Filter (they use 'Approved' instead)
                filter_widgets = r.resource.get_config("filter_widgets")
                if filter_widgets:
                    found = False
                    index = 0
                    for filter_widget in filter_widgets:
                        if filter_widget.field == "paid":
                            found = True
                            break
                        index += 1
                    if found:
                        filter_widgets.pop(index)

            elif vnrc:
                # Modify the Paid Filter
                table = r.table
                from gluon import Field
                table["paid"] = Field.Method("paid", member_membership_paid)
                filter_options = {T("paid"): T("paid"),
                                  T("unpaid"): T("unpaid"),
                                  T("exempted"): T("exempted"),
                                  }
                filter_widgets = r.resource.get_config("filter_widgets")
                if filter_widgets:
                    for filter_widget in filter_widgets:
                        if filter_widget.field == "paid":
                            filter_widget.opts.options = filter_options
                            break

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_member_membership_controller = customise_member_membership_controller

    # -------------------------------------------------------------------------
    def customise_member_membership_type_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("member_membership_type",
                required = False,
                branches = False,
                )

        return attr

    settings.customise_member_membership_type_controller = customise_member_membership_type_controller

    # -------------------------------------------------------------------------
    def customise_msg_email_controller(**attr):

        if current.request.controller == "deploy":
            organisation_id = current.auth.user.organisation_id
            if organisation_id:
                # Filter InBox by Channel
                #from s3 import FS
                s3db = current.s3db
                table = s3db.msg_email_channel
                current.response.s3.filter &= ((table.organisation_id == organisation_id) & \
                                               (table.channel_id == s3db.msg_email.channel_id))

        return attr

    settings.customise_msg_email_controller = customise_msg_email_controller

    # -------------------------------------------------------------------------
    def customise_org_capacity_assessment_controller(**attr):

        # Organisation needs to be an NS/Branch

        user = current.auth.user
        organisation_id = user.organisation_id if user else None
        if organisation_id:
            from s3 import IS_ONE_OF
            db = current.db
            s3db = current.s3db
            otable = s3db.org_organisation
            rows = db(otable.root_organisation == organisation_id).select(otable.id)
            filter_opts = [row.id for row in rows if row.id != organisation_id]

            f = s3db.org_capacity_assessment.organisation_id
            f.label = T("Branch")
            f.widget = None
            f.requires = IS_ONE_OF(db, "org_organisation.id",
                                   s3db.org_OrganisationRepresent(parent=False, acronym=False),
                                   filterby = "id",
                                   filter_opts = filter_opts,
                                   orderby = "org_organisation.name",
                                   sort = True)
        else:
            ns_only("org_capacity_assessment",
                    required = True,
                    branches = True,
                    )

        return attr

    settings.customise_org_capacity_assessment_controller = customise_org_capacity_assessment_controller

    # -------------------------------------------------------------------------
    def customise_org_office_resource(r, tablename):

        # Organisation needs to be an NS/Branch
        ns_only("org_office",
                required = True,
                branches = True,
                limit_filter_opts = True,
                )

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == IRCS:
            table = current.s3db.org_office
            table.code.readable = table.code.writable = False
            table.office_type_id.readable = table.office_type_id.writable = False
        elif root_org == VNRC:
            # Limit office type dropdown to just the VNRC options, not the global ones as well
            field = current.s3db.org_office.office_type_id
            from gluon import IS_EMPTY_OR
            from s3 import IS_ONE_OF
            field.requires = IS_EMPTY_OR(
                                IS_ONE_OF(current.db, "org_office_type.id",
                                          field.represent,
                                          filterby="organisation_id",
                                          filter_opts=(current.auth.root_org(),)
                                          ))

    settings.customise_org_office_resource = customise_org_office_resource

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

            if r.interactive or r.representation == "aadata":

                if not r.component or r.component_name == "branch":

                    resource = r.resource
                    type_label = T("Type")

                    if r.get_vars.get("caller") == "org_facility_organisation_id":
                        # Simplify
                        from s3 import S3SQLCustomForm
                        crud_form = S3SQLCustomForm("name",
                                                    "acronym",
                                                    "phone",
                                                    "comments",
                                                    )
                        resource.configure(crud_form = crud_form,
                                           )
                    elif r.controller == "po":
                        # Referral Agencies in PO module

                        # Default country
                        root_org = current.auth.root_org_name()
                        if root_org == NZRC:
                            resource.table.country.default = "NZ"

                        # Custom CRUD form
                        if r.interactive:
                            from s3 import S3SQLCustomForm, S3SQLInlineLink, S3SQLInlineComponent
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
                                                                 # Filter inline address for type "office address", also sets default
                                                                 filterby = ({"field": "type",
                                                                              "options": 3,
                                                                              },),
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
                        # Organisations in org module
                        list_fields = ["name",
                                       "acronym",
                                       "organisation_organisation_type.organisation_type_id",
                                       "country",
                                       "website",
                                       ]
                        type_filter = r.get_vars.get("organisation_type.name", None)
                        if type_filter:
                            type_names = type_filter.split(",")
                            if len(type_names) == 1:
                                # Strip Type from list_fields
                                try:
                                    list_fields.remove("organisation_organisation_type.organisation_type_id")
                                except:
                                    # Already removed
                                    pass
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
                                list_fields.insert(-1, "organisation_region.region_id")
                                # Region is required
                                f = current.s3db.org_organisation_region.region_id
                                f.requires = f.requires.other
                            else:
                                f = current.s3db.org_organisation_region.region_id
                                f.readable = f.writable = False
                        resource.configure(list_fields = list_fields)

                        if r.interactive:
                            r.table.country.label = T("Country")
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
                                            "organisation_region.region_id",
                                            "country",
                                            "phone",
                                            "website",
                                            "logo",
                                            "comments",
                                            )
                            resource.configure(crud_form = crud_form)

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == VNRC:
            table = current.s3db.pr_contact
            # Hard to translate in Vietnamese
            table.value.label = ""
            # Restrict options to just those wanted by VNRC
            from gluon import IS_IN_SET
            table.contact_method.requires = IS_IN_SET({"EMAIL":       T("Email"),
                                                       "HOME_PHONE":  T("Home Phone"),
                                                       "SMS":         T("Mobile Phone"),
                                                       "WORK_PHONE":  T("Work phone"),
                                                       },
                                                      zero=None)

    settings.customise_pr_contact_resource = customise_pr_contact_resource

    # -------------------------------------------------------------------------
    def customise_pr_contact_emergency_resource(r, tablename):

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == ARCS:
            # Name isn't required
            current.s3db.pr_contact_emergency.name.requires = None
        elif root_org == VNRC:
            # Enable the Address field
            field = current.s3db.pr_contact_emergency.address
            field.readable = field.writable = True

    settings.customise_pr_contact_emergency_resource = customise_pr_contact_emergency_resource

    # -------------------------------------------------------------------------
    def customise_pr_education_resource(r, tablename):

        if r.get_vars.get("rdrt_ap"):
            # Simplify for RDRT AP
            from s3 import S3SQLCustomForm
            s3db = current.s3db
            # Use legacy field for cleaner options
            f = s3db.pr_education.level
            f.readable = f.writable = True
            from gluon import IS_IN_SET
            f.requires = IS_IN_SET(("High School",
                                    "University / College",
                                    "Post Graduate",
                                    ))
            s3db.configure("pr_education",
                           crud_form = S3SQLCustomForm((T("Qualification"), "level"),
                                                       (T("Field of Expertise"), "major"),
                                                       ),
                           )

    settings.customise_pr_education_resource = customise_pr_education_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_availability_resource(r, tablename):

        s3db = current.s3db

        # Construct slot options
        # NB this relies on prepopulation of date/time formulae with
        #    these names, as well as one pr_slot per combination:
        dow = ("Mondays",
               "Tuesdays",
               "Wednesdays",
               "Thursdays",
               "Fridays",
               "Saturdays",
               "Sundays",
               )
        tod = ("Morning", "Afternoon", "Evening")

        stable = s3db.pr_slot
        dtable = s3db.pr_date_formula
        ttable = s3db.pr_time_formula
        join = [dtable.on((dtable.id == stable.date_formula_id) &
                          (dtable.name.belongs(dow))),
                ttable.on((ttable.id == stable.time_formula_id) &
                          (ttable.name.belongs(tod))),
                ]

        dtname = str(dtable)
        ttname = str(ttable)
        stname = str(stable)

        key = lambda row: "%s %s" % (row[dtname]["name"], row[ttname]["name"])
        query = (stable.deleted != True)
        slots = current.db(query).select(stable.id,
                                         stable.name,
                                         dtable.name,
                                         ttable.name,
                                         join = join
                                         ).as_dict(key=key)

        opts = []
        add_option = opts.append
        for t in tod:
            for d in dow:
                slot = slots.get("%s %s" % (d, t))
                if slot:
                    add_option((slot[stname]["id"],
                                T(slot[stname]["name"]),
                                ))

        # @ToDo: Make prettier
        # - reduce labels to just Rows/Columns
        from s3 import S3SQLCustomForm, S3SQLInlineLink
        from gluon.validators import IS_IN_SET
        crud_form = S3SQLCustomForm(
                        "options",
                        S3SQLInlineLink("slot",
                                        cols = len(tod),
                                        field = "slot_id",
                                        label = T("Available on"),
                                        requires = IS_IN_SET(opts,
                                                             sort = False,
                                                             zero = None,
                                                             ),
                                        sort = False,
                                        ),
                        "comments",
                        )

        s3db.configure("pr_person_availability",
                       crud_form = crud_form,
                       )

    settings.customise_pr_person_availability_resource = customise_pr_person_availability_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("org_organisation_team",
                required = False,
                branches = True,
                hierarchy = False,
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

            if r.component_name == "group_membership":
                # Special cases for different NS
                root_org = current.auth.root_org_name()
                if root_org == VNRC:
                    # Update the represent as already set
                    s3db = current.s3db
                    s3db.pr_group_membership.person_id.represent = s3db.pr_PersonRepresent()

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_pr_group_controller = customise_pr_group_controller

    # -------------------------------------------------------------------------
    def customise_pr_language_controller(**attr):

        # Languages for RDRT AP
        settings.L10n.languages = OrderedDict([
            ("af", "Afrikaans"),
            ("sq", "Albanian"),
            ("am", "Amharic"),
            ("ar", "Arabic"),
            ("hy", "Armenian"),
            ("az", "Azerbaijani"),
            ("eu", "Basque"),
            ("be", "Belarusian"),
            ("bn", "Bengali"),
            ("bs", "Bosnian"),
            ("bg", "Bulgarian"),
            ("ca", "Catalan"),
            ("ceb", "Cebuano"),
            ("ny", "Chichewa"),
            ("zh", "Chinese"),
            ("co", "Corsican"),
            ("hr", "Croatian"),
            ("cs", "Czech"),
            ("da", "Danish"),
            ("nl", "Dutch"),
            ("en", "English"),
            ("eo", "Esperanto"),
            ("et", "Estonian"),
            ("fil", "Filipino"),
            ("fi", "Finnish"),
            ("fr", "French"),
            ("gl", "Galician"),
            ("ka", "Georgian"),
            ("de", "German"),
            ("el", "Greek"), # "Greek, Modern (1453-)"
            ("gu", "Gujarati"),
            ("ht", "Haitian Creole"),
            ("ha", "Hausa"),
            ("haw", "Hawaiian"),
            ("he", "Hebrew"),
            ("hi", "Hindi"),
            ("hmn", "Hmong"),
            ("hu", "Hungarian"),
            ("is", "Icelandic"),
            ("ig", "Igbo"),
            ("id", "Indonesian"),
            ("ga", "Irish"),
            ("it", "Italian"),
            ("ja", "Japanese"),
            ("jv", "Javanese"),
            ("kn", "Kannada"),
            ("kk", "Kazakh"),
            ("km", "Khmer"),
            ("ko", "Korean"),
            ("kos", "Kosraean"),
            ("ku", "Kurdish (Kurmanji)"),
            ("ky", "Kyrgyz"),
            ("lo", "Lao"),
            ("la", "Latin"),
            ("lv", "Latvian"),
            ("lt", "Lithuanian"),
            ("lb", "Luxembourgish"),
            ("mk", "Macedonian"),
            ("mg", "Malagasy"), # Madagascar
            ("ms", "Malay"),
            ("ml", "Malayalam"),
            ("mt", "Maltese"),
            ("mi", "Maori"),
            ("mr", "Marathi"),
            ("mn", "Mongolian"),
            ("my", "Myanmar (Burmese)"),
            ("ne", "Nepali"),
            ("nn", "Norwegian"),
            ("ps", "Pashto"),
            ("fa", "Persian"),
            ("pl", "Polish"),
            ("pt", "Portuguese"),
            ("pa", "Punjabi"),
            ("ro", "Romanian"),
            ("ru", "Russian"),
            ("sm", "Samoan"),
            ("sco", "Scots Gaelic"),
            ("sr", "Serbian"),
            ("st", "Sesotho"),
            ("sn", "Shona"),
            ("sd", "Sindhi"),
            ("si", "Sinhala"),
            ("sk", "Slovak"),
            ("sl", "Slovenian"),
            ("so", "Somali"),
            ("es", "Spanish"),
            ("su", "Sundanese"),
            ("sw", "Swahili"),
            ("sv", "Swedish"),
            ("tg", "Tajik"),
            ("ta", "Tamil"),
            ("te", "Telugu"),
            ("th", "Thai"),
            ("tr", "Turkish"),
            ("uk", "Ukrainian"),
            ("ur", "Urdu"),
            ("uz", "Uzbek"),
            ("vi", "Vietnamese"),
            ("cy", "Welsh"),
            ("xh", "Xhosa"),
            ("yi", "Yiddish"),
            ("yo", "Yoruba"),
            ("zu", "Zulu"),
            ])

        return attr

    settings.customise_pr_language_controller = customise_pr_language_controller

    # =========================================================================
    def vol_programme_active(person_id):
        """
            Whether a Volunteer counts as 'Active' based on the number of hours
            they've done (both Trainings & Programmes) per month, averaged over
            the last year.
            If nothing recorded for the last 3 months, don't penalise as assume
            that data entry hasn't yet been done.

            @ToDo: This should be based on the HRM record, not Person record
                   - could be active with Org1 but not with Org2
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

        return False

    # =========================================================================
    def vol_activity_active(person_id):
        """
            Whether a Volunteer counts as 'Active' based on the number of hours
            they've done on Volunteer Activities (inc Trainings, but not Project Activities)
            in the last month.
        """

        from dateutil.relativedelta import relativedelta
        now = current.request.utcnow

        # Time spent on Volunteer Activities in the last month
        htable = current.s3db.vol_activity_hours
        query = (htable.deleted == False) & \
                (htable.person_id == person_id) & \
                (htable.date >= (now - relativedelta(months=1)))
        activities = current.db(query).select(htable.hours,
                                              )
        if activities:
            # Total hours between start and end
            hours = 0
            for activity in activities:
                if activity.hours:
                    hours += activity.hours

            # Active?
            if hours >= 4:
                return True

        return False

    # -------------------------------------------------------------------------
    def vnrc_cv_form(r):

        from s3 import S3FixedOptionsWidget, S3SQLCustomForm

        ptewidget = S3FixedOptionsWidget(("Primary",
                                          "Intermediate",
                                          "Advanced",
                                          "Bachelor",
                                          ),
                                         translate = True,
                                         sort = False,
                                         )

        smewidget = S3FixedOptionsWidget(("Officer",
                                          "Principal Officer",
                                          "Senior Officer",
                                          ),
                                         translate = True,
                                         sort = False,
                                         )

        crud_form = S3SQLCustomForm((T("Political Theory Education"),
                                     "pte.value",
                                     ptewidget,
                                     ),
                                     (T("State Management Education"),
                                      "sme.value",
                                      smewidget,
                                     )
                                    )

        current.s3db.configure("pr_person",
                               crud_form = crud_form,
                               )

        return {"label": T("Other Education"),
                "type": "form",
                "tablename": "pr_person",
                "context": ("id", "id"),
                }

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        from s3 import FS

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        request = current.request
        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        # Special cases for different NS / Roles
        arcs = crmada = ircs = vnrc = False
        auth = current.auth
        root_org = auth.root_org_name()
        if root_org == ARCS:
            arcs = True
            #settings.member.cv_tab = True
            settings.pr.separate_name_fields = 2
        elif root_org == CRMADA:
            crmada = True
            table = s3db.pr_person
            dtable = s3db.pr_person_details
            dtable.religion.readable = dtable.religion.writable = False
            dtable.nationality.default = "MG"
            # Simplify UI: Just have 1 Address
            s3db.add_components("pr_pentity",
                                pr_address = {"joinby": "pe_id",
                                              "multiple": False,
                                              },
                                )
        elif root_org == IRCS:
            ircs = True
            settings.hrm.activity_types = None
            settings.hrm.use_id = False
            table = s3db.pr_person
        elif root_org == PMI:
            settings.hrm.staff_experience = "experience"
            settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
        elif root_org in (CVTL, PRC):
            settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
            if root_org == CVTL:
                settings.member.cv_tab = True
        elif root_org == VNRC:
            vnrc = True
            # Custom components
            add_components = s3db.add_components
            PTE_TAG = "PoliticalTheoryEducation"
            SME_TAG = "StateManagementEducation"
            add_components("pr_person",
                           pr_identity = {"name": "idcard",
                                          "joinby": "person_id",
                                          "filterby": {"type": 2,
                                                       },
                                          "multiple": False,
                                          },
                           pr_person_tag = ({"name": "pte",
                                             "joinby": "person_id",
                                             "filterby": {"tag": PTE_TAG,
                                                          },
                                             "multiple": False,
                                             "defaults": {"tag": PTE_TAG,
                                                          },
                                             },
                                            {"name": "sme",
                                             "joinby": "person_id",
                                             "filterby": {"tag": SME_TAG,
                                                          },
                                             "multiple": False,
                                             "defaults": {"tag": SME_TAG,
                                                          },
                                             },
                                            ),
                           )
            add_components("hrm_human_resource",
                           hrm_insurance = ({"name": "social_insurance",
                                             "joinby": "human_resource_id",
                                             "filterby": {"type": "SOCIAL",
                                                          },
                                             },
                                            {"name": "health_insurance",
                                             "joinby": "human_resource_id",
                                             "filterby": {"type": "HEALTH",
                                                          },
                                             }),
                           )
            # Remove 'Commune' level for Addresses
            #gis = current.gis
            #gis.get_location_hierarchy()
            #try:
            #    gis.hierarchy_levels.pop("L3")
            #except:
            #    # Must be already removed
            #    pass
            settings.modules.pop("asset", None)
        else:
            if not auth.s3_has_role("ADMIN") and \
               auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
                # Bangkok CCST
                req_args = request.args
                if len(req_args) == 1 and req_args[0] == "search_ac.json":
                    # Unfiltered to allow adding as participants
                    pass
                else:
                    # Filter People to just those trained by this region
                    # @ToDo: Filter by Org too if more EVENT_* teams come onboard
                    gtable = db.auth_group
                    mtable = db.auth_membership
                    query = (gtable.uuid.belongs(("EVENT_MONITOR", "EVENT_ORGANISER"))) & \
                            (mtable.group_id == gtable.id) & \
                            (mtable.deleted == False)
                    rows = db(query).select(mtable.user_id)
                    user_ids = [row.user_id for row in rows]
                    filter = FS("training.training_event_id$created_by").belongs(set(user_ids))

                    # & those from this region's countries? No!
                    #ltable = s3db.org_organisation_organisation
                    #root_orgs = db(ltable.parent_id == auth.user.organisation_id).select(ltable.organisation_id)
                    #root_orgs = [o.organisation_id for o in root_orgs]
                    #filter |= FS("~.organisation_id$root_organisation").belongs(root_orgs)

                    s3.filter = filter

        if request.controller == "deploy":
            # Replace default title in imports:
            attr["retitle"] = lambda r: {"title": T("Import Members")} \
                                if r.method == "import" else None
            # Not working
            #if _is_asia_pacific():
            #    settings.L10n.mandatory_lastname = False

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            controller = r.controller
            component_name = r.component_name
            method = r.method
            if component_name == "address":
                if crmada:
                    ctable = r.component.table
                    ctable.type.readable = ctable.type.writable = False

            elif component_name == "appraisal":
                atable = r.component.table
                atable.organisation_id.readable = atable.organisation_id.writable = False
                # Organisation needs to be an NS
                #ns_only("hrm_appraisal",
                #        required = True,
                #        branches = False,
                #        )
                field = atable.supervisor_id
                field.readable = field.writable = False
                _customise_job_title_field(atable.job_title_id)

            if component_name == "experience":
                if ircs:
                    ctable = r.component.table
                    ctable.hours.readable = ctable.hours.writable = False
                    ctable.job_title_id.readable = ctable.job_title_id.writable = False

            elif component_name == "physical_description" or \
                 method == "import":
                from gluon import DIV
                ctable = s3db.pr_physical_description
                ctable.medical_conditions.comment = DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Medical Conditions"),
                                                                          T("Chronic Illness, Disabilities, Mental/Psychological Condition etc.")))
                # Add the less-specific blood types (as that's all the data currently available in some cases)
                from gluon.validators import IS_EMPTY_OR, IS_IN_SET
                blood_type_opts = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "A", "B", "AB", "O")
                ctable.blood_type.requires = IS_EMPTY_OR(IS_IN_SET(blood_type_opts))

                if crmada or ircs:
                    ctable.ethnicity.readable = ctable.ethnicity.writable = False

            elif component_name == "identity":
                if crmada:
                    table = r.component.table
                    # Set default to National ID Card
                    table.type.default = 2
                    # Relabel
                    table.valid_from.label = T("Date of Delivery")
                    field = table.place
                    field.label = T("Place of Delivery")
                    field.readable = field.writable = True
                    # Hide unneeded fields
                    # @ToDo: Do this dynamically in JS based on Type
                    hide_fields = ("description", "valid_until", "country_code", "ia_name")
                    for fname in hide_fields:
                        field = table[fname]
                        field.readable = field.writable = False
                    list_fields = s3db.get_config("pr_identity", "list_fields")
                    hide_fields = set(hide_fields)
                    list_fields = (fs for fs in list_fields if fs not in hide_fields)
                    s3db.configure("pr_identity", list_fields = list_fields)

            elif method == "cv" or component_name == "education":
                if arcs:
                    # Don't enable Legacy Freetext field
                    # Only Highest-level of Education is captured
                    s3db.pr_education.level_id.label = T("Education Level")
                elif vnrc:
                    etable = s3db.pr_education
                    # Don't enable Legacy Freetext field
                    # Hide the 'Name of Award' field
                    field = etable.award
                    field.readable = field.writable = False
                    # Limit education-level dropdown to the 3 specific options initially uploaded
                    # @ToDo: Make this use the VNRC data in the table instead (shouldn't hardcode dynamic options here)
                    # Although then these are different options which makes cross-Org reporting harder...hmmm..anyway these need an l10n which is hardcoded.
                    field = s3db.pr_education.level_id
                    levels = ("High School",
                              "University / College",
                              "Post Graduate",
                              )
                    from gluon import IS_EMPTY_OR
                    from s3 import IS_ONE_OF
                    field.requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "pr_education_level.id",
                                                  field.represent,
                                                  filterby = "name",
                                                  filter_opts = levels,
                                                  ))
                    # Disallow adding of new education levels
                    field.comment = None
                else:
                    # Enable Legacy Freetext field
                    field = s3db.pr_education.level
                    field.readable = field.writable = True
                    field.label = T("Other Level")
                    field.comment = T("Use main dropdown whenever possible")

            elif method =="record" or component_name == "human_resource":
                # Organisation needs to be an NS/Branch
                ns_only("hrm_human_resource",
                        required = True,
                        branches = True,
                        )
                if method == "record":
                    if controller == "vol" and root_org == NRCS:
                        from s3 import S3SQLCustomForm
                        crud_form = S3SQLCustomForm("organisation_id",
                                                    "details.volunteer_type",
                                                    "job_title_id",
                                                    "start_date",
                                                    "end_date",
                                                    "status",
                                                    "comments",
                                                    )
                        s3db.configure("hrm_human_resource",
                                       crud_form = crud_form,
                                       )
                    else:
                        # Use default form (legacy)
                        s3db.clear_config("hrm_human_resource", "crud_form")


            if controller == "deploy":

                AP = _is_asia_pacific()
                if AP:
                    from s3 import S3SQLCustomForm, S3SQLInlineComponent

                    f = s3db.pr_person.middle_name
                    f.readable = f.writable = True

                    f = s3db.pr_person_details.nationality2
                    f.readable = f.writable = True

                    crud_form = S3SQLCustomForm("first_name",
                                                "middle_name",
                                                "last_name",
                                                "date_of_birth",
                                                "gender",
                                                "person_details.nationality",
                                                "person_details.nationality2",
                                                "physical_description.blood_type",
                                                "comments",
                                                )

                    s3db.configure("pr_person",
                                   crud_form = crud_form,
                                   )
            else:
                if arcs:
                    # Changes common to both Members & Volunteers
                    from gluon import IS_EMPTY_OR
                    from s3 import IS_ONE_OF, S3SQLCustomForm, S3SQLInlineComponent, S3LocationSelector
                    # Ensure that + appears at the beginning of the number
                    # Done in Model's controller prep
                    #f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
                    #f.represent = s3_phone_represent
                    #f.widget = S3PhoneWidget()
                    s3db.pr_address.location_id.widget = S3LocationSelector(show_address = T("Village"),
                                                                            show_map = False)
                    etable = s3db.pr_education
                    etable.level_id.comment = None # Don't Add Education Levels inline
                    organisation_id = current.auth.root_org()
                    f = etable.level_id
                    f.requires = IS_ONE_OF(db, "pr_education_level.id",
                                           f.represent,
                                           filterby = "organisation_id",
                                           filter_opts = (organisation_id,),
                                           )
                    s3db.pr_image.image.widget = None # ImageCropWidget doesn't work inline
                    s3db.add_components("pr_person",
                                        pr_address = {"name": "perm_address",
                                                      "joinby": "pe_id",
                                                      "pkey": "pe_id",
                                                      "filterby": {"type": 2,
                                                                   },
                                                      "multiple": False,
                                                      },
                                        pr_education = {"name": "previous_education",
                                                        "joinby": "person_id",
                                                        "filterby": {"current": False,
                                                                     },
                                                        "multiple": False,
                                                        },
                                        )
                    crud_strings = s3.crud_strings
                    if controller == "vol":
                        crud_strings["pr_person"] = crud_strings["hrm_human_resource"]
                        #ctable = s3db.hrm_course
                        #ctable.type.default = 2
                        #query = (ctable.organisation_id == current.auth.root_org()) & \
                        #        (ctable.type == 2) & \
                        #        (ctable.deleted != True)
                        #courses = db(query).select(ctable.id)
                        #course_ids = [c.id for c in courses]
                        f = s3db.hrm_training.course_id
                        f.requires = IS_ONE_OF(db, "hrm_course.id",
                                               f.represent,
                                               #filterby = "id",
                                               #filter_opts = course_ids,
                                               filterby = "organisation_id",
                                               filter_opts = (organisation_id,),
                                               sort = True,
                                               )
                        s3db.add_components("pr_person",
                                            hrm_human_resource = {"name": "volunteer",
                                                                  "joinby": "person_id",
                                                                  "filterby": {
                                                                      "type": 2,
                                                                      },
                                                                  "multiple": False,
                                                                  },
                                            #hrm_training = {"name": "vol_training",
                                            #                "joinby": "person_id",
                                            #                "filterby": {"course_id": course_ids,
                                            #                             },
                                            #                },
                                            pr_education = {"name": "current_education",
                                                            "joinby": "person_id",
                                                            "filterby": {
                                                                "current": True,
                                                                },
                                                            "multiple": False,
                                                            },
                                            vol_details = {"name": "volunteer_details",
                                                           "link": "hrm_human_resource",
                                                           "joinby": "person_id",
                                                           "key": "id",
                                                           "fkey": "human_resource_id",
                                                           "pkey": "id",
                                                           "multiple": False,
                                                           },
                                            )
                        crud_form = S3SQLCustomForm("volunteer.organisation_id",
                                                    "volunteer.code",
                                                    (T("Name"), "first_name"),
                                                    "last_name",
                                                    (T("Father Name"), "person_details.father_name"),
                                                    (T("Grand Father Name"), "person_details.grandfather_name"),
                                                    "date_of_birth",
                                                    (T("Gender"), "gender"),
                                                    (T("Job"), "person_details.occupation"),
                                                    S3SQLInlineComponent("perm_address",
                                                                         label = T("Address"),
                                                                         fields = [("", "location_id")],
                                                                         filterby = {"field": "type",
                                                                                     "options": 2,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("current_education",
                                                                         label = T("School / University"),
                                                                         fields = [("", "institute")],
                                                                         filterby = {"field": "current",
                                                                                     "options": True,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("phone",
                                                                         label = T("Phone Number"),
                                                                         fields = [("", "value")],
                                                                         filterby = {"field": "contact_method",
                                                                                     "options": "SMS",
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("contact_emergency",
                                                                         label = T("Emergency Contact Number"),
                                                                         fields = [("", "phone")],
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("previous_education",
                                                                         label = T("Education Level"),
                                                                         fields = [("", "level_id")],
                                                                         filterby = {"field": "current",
                                                                                     "options": False,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    (T("Volunteer Start Date"), "volunteer.start_date"),
                                                    S3SQLInlineComponent("training",
                                                                         #"vol_training",
                                                                         label = T("Trainings"),
                                                                         fields = (("", "course_id"),
                                                                                   ("", "date"),
                                                                                    ),
                                                                         ),
                                                    S3SQLInlineComponent("volunteer_details",
                                                                         label = T("Active"),
                                                                         fields = [("", "active")],
                                                                         link = False,
                                                                         update_link = False,
                                                                         multiple = False,
                                                                         ),
                                                    (T("Remarks"), "comments"),
                                                    S3SQLInlineComponent("image",
                                                                         label = T("Photo"),
                                                                         fields = [("", "image")],
                                                                         filterby = {"field": "profile",
                                                                                     "options": True,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    )
                        s3db.configure("pr_person",
                                       crud_form = crud_form,
                                       )

                    elif controller == "member":
                        mtable = s3db.member_membership
                        crud_strings["pr_person"] = crud_strings["member_membership"]
                        f = mtable.leaving_reason
                        f.readable = f.writable = True
                        f = mtable.restart_date
                        f.readable = f.writable = True
                        f = mtable.election
                        f.readable = f.writable = True
                        f = mtable.trainings
                        f.readable = f.writable = True
                        #ctable = s3db.hrm_course
                        #ctable.type.default = 4
                        #query = (ctable.organisation_id == current.auth.root_org()) & \
                        #        (ctable.type == 4) & \
                        #        (ctable.deleted != True)
                        #courses = db(query).select(ctable.id)
                        #course_ids = [c.id for c in courses]
                        #f = s3db.hrm_training.course_id
                        #f.requires = IS_ONE_OF(db, "hrm_course.id",
                        #                       f.represent,
                        #                       filterby = "id",
                        #                       filter_opts = course_ids,
                        #                       sort = True,
                        #                       )
                        f = s3db.pr_person_details.grandfather_name
                        f.readable = f.writable = True

                        s3db.add_components("pr_person",
                                            #hrm_training = {"name": "member_training",
                                            #                "joinby": "person_id",
                                            #                "filterby": {"course_id": course_ids,
                                            #                             },
                                            #                },
                                            pr_address = {"name": "temp_address",
                                                          "joinby": "pe_id",
                                                          "pkey": "pe_id",
                                                          "filterby": {
                                                              "type": 1,
                                                              },
                                                          "multiple": False,
                                                          },
                                            # Make single, so fields can be embedded:
                                            member_membership = {"joinby": "person_id",
                                                                 "multiple": False,
                                                                 },
                                            )
                        # Reset the component (we're past resource initialization)
                        r.resource.components.reset(("membership",))

                        crud_form = S3SQLCustomForm("membership.organisation_id",
                                                    "membership.code",
                                                    (T("Name"), "first_name"),
                                                    "last_name",
                                                    (T("Father Name"), "person_details.father_name"),
                                                    (T("Grand Father Name"), "person_details.grandfather_name"),
                                                    "date_of_birth",
                                                    (T("Gender"), "gender"),
                                                    S3SQLInlineComponent("perm_address",
                                                                         label = T("Permanent Address"),
                                                                         fields = [("", "location_id")],
                                                                         filterby = {"field": "type",
                                                                                     "options": 2,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("temp_address",
                                                                         label = T("Temporary Address"),
                                                                         fields = [("", "location_id")],
                                                                         filterby = {"field": "type",
                                                                                     "options": 1,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    (T("Place of Work"), "person_details.company"),
                                                    S3SQLInlineComponent("previous_education",
                                                                         label = T("Education Level"),
                                                                         fields = [("", "level_id")],
                                                                         filterby = {"field": "current",
                                                                                     "options": False,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("identity",
                                                                         label = T("ID Number"),
                                                                         fields = [("", "value")],
                                                                         filterby = {"field": "type",
                                                                                     "options": 2,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("physical_description",
                                                                         label = T("Blood Group"),
                                                                         fields = [("", "blood_type")],
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("phone",
                                                                         label = T("Phone Number"),
                                                                         fields = [("", "value")],
                                                                         filterby = {"field": "contact_method",
                                                                                     "options": "SMS",
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    S3SQLInlineComponent("contact_emergency",
                                                                         label = T("Relatives Contact #"),
                                                                         fields = [("", "phone")],
                                                                         multiple = False,
                                                                         ),
                                                    (T("Date of Recruitment"), "membership.start_date"),
                                                    (T("Date of Dismissal"), "membership.end_date"),
                                                    (T("Reason for Dismissal"), "membership.leaving_reason"),
                                                    (T("Date of Re-recruitment"), "membership.restart_date"),
                                                    (T("Monthly Membership Fee"), "membership.membership_fee"),
                                                    (T("Membership Fee Last Paid"), "membership.membership_paid"),
                                                    "membership.membership_due",
                                                    "membership.election",
                                                    "membership.trainings",
                                                    #S3SQLInlineComponent("member_training",
                                                    #                     label = T("Trainings"),
                                                    #                     fields = (("", "course_id"),
                                                    #                               ("", "date"),
                                                    #                                ),
                                                    #                     ),
                                                    "membership.comments",
                                                    S3SQLInlineComponent("image",
                                                                         label = T("Photo"),
                                                                         fields = [("", "image")],
                                                                         filterby = {"field": "profile",
                                                                                     "options": True,
                                                                                     },
                                                                         multiple = False,
                                                                         ),
                                                    )
                        s3db.configure("pr_person",
                                       crud_form = crud_form,
                                       )

                elif vnrc:
                    if not r.component:
                        crud_fields = ["first_name",
                                       "middle_name",
                                       "last_name",
                                       "date_of_birth",
                                       "gender",
                                       "person_details.marital_status",
                                       "person_details.nationality",
                                       ]

                        from gluon import IS_EMPTY_OR, IS_IN_SET
                        from s3 import IS_ONE_OF

                        dtable = s3db.pr_person_details

                        # Context-dependent form fields
                        if controller in ("pr", "hrm", "vol"):
                            # Provinces of Viet Nam
                            ltable = s3db.gis_location
                            ptable = ltable.with_alias("gis_parent_location")
                            dbset = db((ltable.level == "L1") & \
                                       (ptable.name == "Viet Nam"))
                            left = ptable.on(ltable.parent == ptable.id)
                            vn_provinces = IS_EMPTY_OR(IS_ONE_OF(dbset, "gis_location.name",
                                                                "%(name)s",
                                                                left=left,
                                                                ))
                            # Place Of Birth
                            field = dtable.place_of_birth
                            field.readable = field.writable = True
                            field.requires = vn_provinces

                            # Home Town
                            field = dtable.hometown
                            field.readable = field.writable = True
                            field.requires = vn_provinces

                            # Use a free-text version of religion field
                            # @todo: make religion a drop-down list of options
                            field = dtable.religion_other
                            field.label = T("Religion")
                            field.readable = field.writable = True

                            crud_fields.extend(["person_details.place_of_birth",
                                                "person_details.hometown",
                                                "person_details.religion_other",
                                                "person_details.mother_name",
                                                "person_details.father_name",
                                                "person_details.affiliations",
                                                ])
                        else:
                            # ID Card Number inline
                            from s3 import S3SQLInlineComponent
                            idcard_number = S3SQLInlineComponent("idcard",
                                                                 label = T("ID Card Number"),
                                                                 fields = [("", "value")],
                                                                 default = {"type": 2,
                                                                            },
                                                                 multiple = False,
                                                                 )
                            # @todo: make ethnicity a drop-down list of options
                            crud_fields.extend(["physical_description.ethnicity",
                                                idcard_number,
                                                ])

                        # Standard option for nationality
                        field = dtable.nationality
                        VN = "VN"
                        field.default = VN
                        vnrc_only = False
                        try:
                            options = dict(field.requires.options())
                        except AttributeError:
                            pass
                        else:
                            opts = [VN]
                            if r.record:
                                # Get the nationality from the current record
                                query = (r.table.id == r.id)
                                left = dtable.on(dtable.person_id == r.id)
                                row = db(query).select(dtable.nationality,
                                                       left = left,
                                                       limitby = (0, 1)).first()
                                if row and row.nationality:
                                    opts.append(row.nationality)
                                # Check wether this person is only VNRC-associated
                                htable = s3db.hrm_human_resource
                                otable = s3db.org_organisation
                                query = (htable.person_id == r.id) & \
                                        (htable.deleted != True) & \
                                        (otable.id == htable.organisation_id) & \
                                        (otable.name != VNRC)
                                row = db(query).select(htable.id, limitby=(0, 1)).first()
                                if not row:
                                    vnrc_only = True
                            opts = dict((k, options[k]) for k in opts if k in options)
                            if vnrc_only:
                                # Person is only associated with VNRC => enforce update,
                                # and limit options to either current value or VN
                                field.requires = IS_IN_SET(opts, zero=None)
                            else:
                                # Person is (also) associated with another org
                                # => can't enforce update, so just limit options
                                field.requires = IS_EMPTY_OR(IS_IN_SET(opts))

                        # Also hide some other fields
                        crud_fields.append("comments")
                        from s3 import S3SQLCustomForm
                        s3db.configure("pr_person",
                                       crud_form = S3SQLCustomForm(*crud_fields),
                                       )

                    if method == "record" or component_name == "human_resource":
                        # Hide unwanted fields in human_resource
                        htable = s3db.hrm_human_resource
                        for fname in ["job_title_id",
                                      "code",
                                      "essential",
                                      "site_contact",
                                      "start_date",
                                      "end_date",
                                      ]:
                            field = htable[fname]
                            field.readable = field.writable = False

                        if method == "record" and controller == "hrm":
                            # Custom config for method handler

                            # RC employment history
                            org_type_name = "organisation_id$organisation_organisation_type.organisation_type_id$name"
                            widget_filter = (FS(org_type_name) == "Red Cross / Red Crescent") & \
                                            (FS("organisation") == None)
                            org_experience = {"label": T("Red Cross Employment History"),
                                              "label_create": T("Add Employment"),
                                              "list_fields": ["start_date",
                                                              "end_date",
                                                              "organisation",
                                                              "department_id",
                                                              "job_title",
                                                              "employment_type",
                                                              ],
                                              "filter": widget_filter,
                                              }

                            # Non-RC employment history
                            widget_filter = FS("organisation") != None
                            other_experience = {"label": T("Other Employments"),
                                                "label_create": T("Add Employment"),
                                                "list_fields": ["start_date",
                                                                "end_date",
                                                                "organisation",
                                                                "job_title",
                                                                ],
                                                "filter": widget_filter,
                                                }

                            s3db.set_method("pr", "person",
                                            method = "record",
                                            action = s3db.hrm_Record(salary=True,
                                                                     awards=True,
                                                                     disciplinary_record=True,
                                                                     org_experience=org_experience,
                                                                     other_experience=other_experience,
                                                                     ))

                            # Custom list_fields for hrm_salary (exclude monthly amount)
                            stable = s3db.hrm_salary
                            stable.salary_grade_id.label = T("Grade Code")
                            s3db.configure("hrm_salary",
                                           list_fields = ["staff_level_id",
                                                          "salary_grade_id",
                                                          "start_date",
                                                          "end_date",
                                                          ],
                                           )
                            # Custom list_fields for hrm_award
                            s3db.configure("hrm_award",
                                           list_fields = ["date",
                                                          "awarding_body",
                                                          "award_type_id",
                                                          ],
                                           orderby = "hrm_award.date desc"
                                           )
                            # Custom list_fields for hrm_disciplinary_action
                            s3db.configure("hrm_disciplinary_action",
                                           list_fields = ["date",
                                                          "disciplinary_body",
                                                          "disciplinary_type_id",
                                                          ],
                                           orderby = "hrm_disciplinary_action.date desc"
                                           )
                            # Custom form for hrm_human_resource
                            from s3 import S3SQLCustomForm, S3SQLInlineComponent
                            crud_fields = ["organisation_id",
                                           "site_id",
                                           "department_id",
                                           "status",
                                           S3SQLInlineComponent("contract",
                                                                label = T("Contract Details"),
                                                                fields = ("term",
                                                                          (T("Hours Model"), "hours"),
                                                                          ),
                                                                multiple = False,
                                                                ),
                                           S3SQLInlineComponent("social_insurance",
                                                                label = T("Social Insurance"),
                                                                name = "social",
                                                                fields = ("insurance_number",
                                                                          "insurer",
                                                                          ),
                                                                default = {"type": "SOCIAL"},
                                                                multiple = False,
                                                                ),
                                           S3SQLInlineComponent("health_insurance",
                                                                label = T("Health Insurance"),
                                                                name = "health",
                                                                fields = ("insurance_number",
                                                                          "provider",
                                                                          ),
                                                                default = {"type": "HEALTH"},
                                                                multiple = False,
                                                                ),
                                           "comments",
                                           ]
                            s3db.configure("hrm_human_resource",
                                           crud_form = S3SQLCustomForm(*crud_fields),
                                           )

                    elif component_name == "address":
                        settings.gis.building_name = False
                        settings.gis.latlon_selector = False
                        settings.gis.map_selector = False

                    elif method == "contacts":
                        table = s3db.pr_contact_emergency
                        table.address.readable = table.address.writable = True

                    elif component_name == "identity":
                        table = r.component.table

                        # Limit options for identity document type
                        pr_id_type_opts = {1: T("Passport"),
                                           2: T("National ID Card"),
                                           }
                        from gluon.validators import IS_IN_SET
                        table.type.requires = IS_IN_SET(pr_id_type_opts, zero=None)

                        if controller == "hrm":
                            # For staff, set default for ID document type and do not
                            # allow selection of other options
                            table.type.default = 2
                            table.type.writable = False
                            hide_fields = ("description", "valid_until", "country_code", "ia_name")
                        else:
                            hide_fields = ("description",)

                        # Hide unneeded fields
                        for fname in hide_fields:
                            field = table[fname]
                            field.readable = field.writable = False
                        list_fields = s3db.get_config("pr_identity", "list_fields")
                        hide_fields = set(hide_fields)
                        list_fields = (fs for fs in list_fields if fs not in hide_fields)
                        s3db.configure("pr_identity", list_fields = list_fields)

                    elif method == "cv" or component_name == "experience":
                        table = s3db.hrm_experience
                        # Use simple free-text variants
                        table.organisation_id.default = None # should not default in this case
                        table.organisation.readable = True
                        table.organisation.writable = True
                        table.job_title.readable = True
                        table.job_title.writable = True
                        table.comments.label = T("Main Duties")
                        from s3 import S3SQLCustomForm
                        crud_form = S3SQLCustomForm("organisation",
                                                    "job_title",
                                                    "comments",
                                                    "start_date",
                                                    "end_date",
                                                    )
                        s3db.configure("hrm_experience",
                                       crud_form = crud_form,
                                       list_fields = ["organisation",
                                                      "job_title",
                                                      "comments",
                                                      "start_date",
                                                      "end_date",
                                                      ],
                                       )
                        if method == "cv":
                            # Customize CV
                            s3db.set_method("pr", "person",
                                            method = "cv",
                                            action = s3db.hrm_CV(form=vnrc_cv_form))

                    elif component_name == "salary":
                        stable = s3db.hrm_salary
                        stable.salary_grade_id.label = T("Grade Code")
                        field = stable.monthly_amount
                        field.readable = field.writable = False

                    elif component_name == "competency":
                        ctable = s3db.hrm_competency
                        # Hide confirming organisation (defaults to VNRC)
                        ctable.organisation_id.readable = False

                    elif component_name == "membership":
                        field = s3db.member_membership.fee_exemption
                        field.readable = field.writable = True
                        PROGRAMMES = T("Programs")
                        from s3 import S3SQLCustomForm, S3SQLInlineLink
                        crud_form = S3SQLCustomForm("organisation_id",
                                                    "code",
                                                    "membership_type_id",
                                                    "start_date",
                                                    "end_date",
                                                    "membership_fee",
                                                    "membership_paid",
                                                    "fee_exemption",
                                                    S3SQLInlineLink("programme",
                                                                    field = "programme_id",
                                                                    label = PROGRAMMES,
                                                                    ),
                                                    )

                        list_fields = ["organisation_id",
                                       "membership_type_id",
                                       "start_date",
                                       (T("Paid"), "paid"),
                                       (T("Email"), "email.value"),
                                       (T("Phone"), "phone.value"),
                                       (PROGRAMMES, "membership_programme.programme_id"),
                                       ]

                        s3db.configure("member_membership",
                                       crud_form = crud_form,
                                       list_fields = list_fields,
                                       )
            return True
        s3.prep = custom_prep

        if arcs:
            # Remove Tabs
            attr["rheader"] = None
        else:
            attr["rheader"] = lambda r, v=vnrc: pr_rheader(r, v)

        if vnrc:
            # Link to customised download Template
            #attr["csv_template"] = ("../../themes/IFRC/formats", "volunteer_vnrc.csv")
            # Remove link to download Template
            attr["csv_template"] = "hide"

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def pr_rheader(r, vnrc):
        """
            Custom rheader for vol/person for vnrc
        """

        controller = current.request.controller
        if vnrc :
            if controller == "vol":
                # Simplify RHeader
                settings.hrm.vol_experience = None

        if controller == "member":
            return current.s3db.member_rheader(r)
        else:
            return current.s3db.hrm_rheader(r)

    # -------------------------------------------------------------------------
    def customise_survey_series_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("survey_series",
                required = False,
                branches = True,
                )

        return attr

    settings.customise_survey_series_controller = customise_survey_series_controller

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
                s3.jquery_ready.append('''$.showHouseholdComponents(true)''')
        return

    # -------------------------------------------------------------------------
    def customise_po_household_resource(r, tablename):

        # Must update realm because inheriting from area (which can change)
        current.s3db.configure("po_household",
                               update_realm = True,
                               )

    settings.customise_po_household_resource = customise_po_household_resource

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
            # Geocode imported household addresses
            if r.method == "import" and "job" in r.post_vars:
                settings.gis.geocode_imported_addresses = True
                settings.gis.ignore_geocode_errors = True
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
            When using Budget Monitoring (i.e. CRMADA) then create the entries
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

        # Build Budget Name from Project Name
        project_name = project.name

        # Check for duplicates
        query = (btable.name == project_name) & \
                (btable.id != budget.id)
        duplicate = db(query).select(btable.id,
                                     limitby=(0, 1)
                                     ).first()

        if not duplicate:
            budget_name = project_name[:128]
        else:
            # Need another Unique name
            import uuid
            budget_name = "%s %s" % (project_name[:91], uuid.uuid4())
        budget.update_record(name = budget_name)

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

    # -------------------------------------------------------------------------
    def customise_project_programme_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("project_programme",
                required = True,
                branches = False,
                updateable = True,
                )

        return attr

    settings.customise_project_programme_controller = customise_project_programme_controller

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        tablename = "project_project"

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_root_default_filter,
                              tablename = tablename)

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

        if settings.get_project_programmes():
            # Inject inline link for programmes including S3PopupLink
            #from s3layouts import S3PopupLink
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

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == CRMADA:
            settings.project.details_tab = True
            #settings.project.community_volunteers = True
            HFA = None
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
            budget = S3SQLInlineComponent("budget",
                                          label = T("Budget"),
                                          #link = False,
                                          multiple = False,
                                          fields = ("total_budget",
                                                    "currency",
                                                    #"monitoring_frequency",
                                                    ),
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
            postprocess = None
            HFA = "drr.hfa"
            budget = None
            objectives = "objectives"
            outputs = S3SQLInlineComponent("output",
                                           label = T("Outputs"),
                                           fields = ("name", "status"),
                                           )

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

            if r.component:
                if r.component_name == "organisation":
                    component_id = r.component_id
                    if component_id:
                        # No r.component.record :/
                        ctable = s3db.project_organisation
                        crecord = current.db(ctable.id == component_id).select(ctable.role,
                                                                               limitby=(0, 1)
                                                                               ).first()
                        if crecord.role == settings.get_project_organisation_lead_role():
                            ns_only("project_organisation",
                                    required = True,
                                    branches = False,
                                    updateable = True,
                                    )
            else:
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

    # -------------------------------------------------------------------------
    def customise_project_location_resource(r, tablename):



        if r.interactive:

            from s3 import S3LocationSelector, S3SQLCustomForm, S3SQLInlineLink

            s3db = current.s3db
            s3db.project_location.location_id.widget = \
                S3LocationSelector(show_postcode = False,
                                   show_latlon = False,
                                   show_map = False,
                                   )

            if r.tablename == "project_project" and r.id:
                # On component tab
                # => limit activity types by project sector
                ltable = s3db.project_sector_project
                query = (ltable.project_id == r.id) & \
                        (ltable.deleted == False)
                rows = current.db(query).select(ltable.sector_id)
                sector_ids = set(row.sector_id for row in rows)
                script = None
            else:
                # Primary form
                # => start empty until project selected
                sector_ids = set()
                # => update selectable activity types by project sector
                script = '''
$.filterOptionsS3({
 'trigger':'project_id',
 'target':{'alias':'activity_type','name':'activity_type_id','inlineType':'link'},
 'lookupPrefix':'project',
 'lookupResource':'activity_type',
 'lookupKey':'activity_type_id:project_activity_type_sector.sector_id$project_sector_project.project_id',
 'showEmptyField':false,
})'''

            crud_form = S3SQLCustomForm(
                "project_id",
                "location_id",
                S3SQLInlineLink(
                    "activity_type",
                    label = T("Activity Types"),
                    field = "activity_type_id",
                    cols = 3,
                    filterby = "activity_type_sector.sector_id",
                    options = sector_ids,
                    script = script,
                    ),
                    "comments",
                )

            s3db.configure(tablename,
                           crud_form = crud_form,
                           )

    settings.customise_project_location_resource = customise_project_location_resource

    # -------------------------------------------------------------------------
    def customise_inv_commit_controller(**attr):

        # Request is mandatory
        field = current.s3db.inv_commit.req_id
        field.requires = field.requires.other

        return attr

    settings.customise_inv_commit_controller = customise_inv_commit_controller

    # -------------------------------------------------------------------------
    def customise_inv_req_resource(r, tablename):

        from s3db.inv import inv_ReqRefRepresent

        s3db = current.s3db

        # Request is mandatory
        field = s3db.inv_commit.req_id
        field.requires = field.requires.other

        table = s3db.inv_req
        table.req_ref.represent = inv_ReqRefRepresent(show_link=True, pdf=True)
        table.site_id.label = T("Deliver To")
        # Hide Drivers list_field
        list_fields = s3db.get_config("inv_req", "list_fields")
        try:
            list_fields.remove((T("Drivers"), "drivers"))
        except:
            # Already removed
            pass

    settings.customise_inv_req_resource = customise_inv_req_resource

    # -------------------------------------------------------------------------
    def customise_vulnerability_data_resource(r, tablename):

        # Date is required: We don't store modelled data
        requires = r.table.date.requires
        if hasattr(requires, "other"):
            r.table.date.requires = requires.other

    settings.customise_vulnerability_data_resource = customise_vulnerability_data_resource

# =============================================================================
class hrm_CourseRepresent(S3Represent):
    """
        Representation of Courses
        - list filtered to just those linked to the specified Organisation
        - used for AP RDRT
    """

    def __init__(self, organisation_id):

        self.organisation_id = organisation_id

        super(hrm_CourseRepresent,
              self).__init__(lookup="hrm_course",
                             #none="",
                             translate=True)

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values.
            (in foreign key representations)

            @param key: the key Field
            @param values: the values
            @param fields: the fields to retrieve
        """

        table = self.table
        organisation_id = self.organisation_id

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(key,
                                        table.name,
                                        table.organisation_id,
                                        )
        new_rows = []
        append = new_rows.append
        for row in rows:
            new_row = {key: row.id,
                       }
            if row.organisation_id == organisation_id:
                new_row["name"] = row.name
            else:
                new_row["name"] = None
            append(new_row)
        self.queries += 1
        return new_rows

# END =========================================================================
