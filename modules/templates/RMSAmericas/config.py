# -*- coding: utf-8 -*-

import datetime
from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

from s3 import S3Method

from controllers import deploy_index

RED_CROSS = "Red Cross / Red Crescent"

def config(settings):
    """
        Template settings for IFRC's Resource Management System
        - Americas Zone

        http://eden.sahanafoundation.org/wiki/Deployments/IFRC
    """

    T = current.T

    # -------------------------------------------------------------------------
    # System Name
    #
    settings.base.system_name = T("Resource Management System")
    settings.base.system_name_short = T("RMS")

    # -------------------------------------------------------------------------
    # Pre-Populate
    #
    settings.base.prepopulate += ("RMSAmericas",)
    settings.base.prepopulate_demo += ("RMSAmericas/Demo",)

    # -------------------------------------------------------------------------
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

    # =========================================================================
    # System Settings
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
                                               #"member": T("Member")
                                               }
    # This hides the options from the UI
    #settings.auth.registration_link_user_to_default = ["volunteer"]

    #settings.auth.record_approval = True

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
                                hrm_training_event = OID,
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
            if not otype or otype.name != RED_CROSS:
                use_user_organisation = True

        # Facilities, Forums & Requisitions are owned by the user's organisation
        elif tablename in ("org_facility", "pr_forum", "req_req"):
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

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    #
    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("pt-br", "Portuguese (Brazil)"),
        ("es", "Spanish"),
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
    #settings.L10n.mandatory_lastname = True # mother's surname
    settings.L10n.mandatory_middlename = True # father's surname
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

    # -------------------------------------------------------------------------
    # Finance settings
    #
    def currencies(default):
        """ RMS- and NS-specific currencies (lazy setting) """

        # Currencies that are common for all NS
        currencies = {"EUR" : "Euros",
                      "CHF" : "Swiss Francs",
                      "USD" : "United States Dollars",
                      }

        # NS-specific currencies
        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            currencies["HNL"] = "Honduran Lempira"
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

    def currency_represent(currency):
        """ NS-specific currency represent """

        if currency == "HNL":
            root_org = current.auth.root_org_name()
            if root_org == HNRC:
                return "L"
        return currency

    # -------------------------------------------------------------------------
    # Map Settings

    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = True

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

    # GeoNames username
    settings.gis.geonames_username = "rms_dev"

    # @ToDo: Lazy fn once we have NS to enable this for
    # (off for HN & off by default)
    settings.gis.postcode_selector = False

    # -------------------------------------------------------------------------
    # Use the label 'Camp' instead of 'Shelter'
    #
    settings.ui.camp = True

    # -------------------------------------------------------------------------
    # Filter Manager
    #
    #settings.search.filter_manager = False

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Content Management
    #
    #settings.cms.hide_index = True
    settings.cms.richtext = True

    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    #settings.msg.parser = "IFRC"

    # =========================================================================
    # Module Settings

    # -------------------------------------------------------------------------
    # Members
    #
    settings.member.cv_tab = True

    # -------------------------------------------------------------------------
    # Organisations
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

    # -------------------------------------------------------------------------
    # Human Resource Management
    #
    # Uncomment to allow Staff & Volunteers to be registered without an email address
    settings.hrm.email_required = True
    settings.hrm.mix_staff = True
    # Uncomment to show the Organisation name in HR represents
    settings.hrm.show_organisation = True
    # Uncomment to allow HRs to have multiple Job Titles
    #settings.hrm.multiple_job_titles = True
    # Uncomment to have each root Org use a different Job Title Catalog
    settings.hrm.org_dependent_job_titles = True
    settings.hrm.staff_departments = False
    settings.hrm.teams = False
    # Uncomment to disable the use of HR Credentials
    settings.hrm.use_credentials = False
    # Uncomment to disable the use of HR Certificates
    #settings.hrm.use_certificates = False
    # Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
    #settings.hrm.filter_certificates = True
    # Uncomment to auto-create certificates for courses
    settings.hrm.create_certificates_from_courses = "organisation_id"
    settings.hrm.use_code = True
    settings.hrm.use_description = "Medical Information"
    # Uncomment to enable the use of HR Education
    settings.hrm.use_education = True
    # Uncomment to hide Job Titles
    settings.hrm.use_job_titles = False
    settings.hrm.use_national_id = True
    settings.hrm.use_skills = True
    # Custom label for Organisations in HR module
    settings.hrm.organisation_label = "National Society / Branch"
    # Custom label for Top-level Organisations in HR module
    settings.hrm.root_organisation_label = "National Society"
    # Uncomment to consolidate tabs into a single CV
    settings.hrm.cv_tab = True
    settings.hrm.vol_experience = "programme"
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    settings.hrm.record_tab = "record"
    # Use Locations for Training Events, not Facilities
    settings.hrm.event_site = False
    # Training Instructors are Multiple
    settings.hrm.training_instructors = "multiple"
    # Training Filters are Contains
    settings.hrm.training_filter_and = True
    settings.hrm.record_label = "Information"
    # Pass marks are defined by Course
    settings.hrm.course_pass_marks = True
    # Work History & Missions
    settings.hrm.staff_experience = "both"

    # Uncomment to do a search for duplicates in the new AddPersonWidget2
    settings.pr.lookup_duplicates = True
    settings.pr.separate_name_fields = 3

    #def dob_required(default):
    #    """ NS-specific dob_required (lazy setting) """

    #    if current.auth.override is True:
    #        default = False
    #    else:
    #        root_org = current.auth.root_org_name()
    #        if root_org == HNRC:
    #            default = False
    #        else:
    #            # Human Talent module for zone
    #            default = True
    #    return default

    #settings.pr.dob_required = dob_required

    def hrm_course_grades(default):
        """ Course Grades """

        default = {0: T("No Show"),
                   1: T("Left Early"),
                   #2: T("Attendance"),
                   8: T("Pass"),
                   9: T("Fail"),
                   }

        return default

    settings.hrm.course_grades = hrm_course_grades

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

    def hrm_vol_active(default):
        """ Whether & How to track Volunteers as Active """

        #root_org = current.auth.root_org_name()
        #if root_org in (ARCS, IRCS):
        #    # Simple checkbox
        #    return True
        #elif root_org in (CVTL, PMI, PRC):
        #    # Use formula based on hrm_programme
        #    return vol_programme_active
        #elif root_org in (CRMADA, ):
        #    # Use formula based on vol_activity
        #    return vol_activity_active
        #return False

        # Use formula based on hrm_programme
        return vol_programme_active

    settings.hrm.vol_active = hrm_vol_active
    settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"

    # Roles which are permitted to export ID cards
    ID_CARD_EXPORT_ROLES = ("ORG_ADMIN", "hr_manager", "hr_assistant")

    # -------------------------------------------------------------------------
    # RIT
    settings.deploy.team_label = "RIT"
    settings.customise_deploy_home = deploy_index
    # Alerts get sent to all recipients
    settings.deploy.manual_recipients = False
    settings.deploy.post_to_twitter = True

    # -------------------------------------------------------------------------
    # Projects
    settings.project.assign_staff_tab = False
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    settings.project.mode_drr = True
    # Uncomment this to use Activity Types for Activities & Projects
    #settings.project.activity_types = True
    # Uncomment this to use Codes for projects
    settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    #settings.project.community = True
    # Uncomment this to enable Demographics in 3W projects
    #settings.project.demographics = True
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

    # -------------------------------------------------------------------------
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


    # -------------------------------------------------------------------------
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

    # =========================================================================
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
        # Used by RIT
        ("event", Storage(
                name_nice = T("Events"),
                #description = "Events",
                restricted = True,
                #module_type = 10
            )),
        ("member", Storage(
               name_nice = T("Partners"),
               #description = "Membership Management System",
               restricted = True,
               #module_type = 10,
           )),
        ("deploy", Storage(
               name_nice = T("Regional Intervention Teams"),
               #description = "Alerting and Deployment of Disaster Response Teams",
               restricted = True,
               #module_type = 10,
           )),
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
            type_id = db(ttable.name == RED_CROSS).select(ttable.id,
                                                          limitby=(0, 1),
                                                          cache = s3db.cache,
                                                          ).first().id
        except AttributeError:
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
            from s3layouts import S3PopupLink
            from s3 import S3ScriptItem
            add_link = S3PopupLink(c = "org",
                                   f = "organisation",
                                   vars = {"organisation_type.name": RED_CROSS},
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
    #def user_org_and_children_default_filter(selector, tablename=None):
    #    """
    #        Default filter for organisation_id:
    #        * Use the user's organisation if logged-in and associated with an
    #          organisation.
    #    """

    #    auth = current.auth
    #    user_org_id = auth.is_logged_in() and auth.user.organisation_id
    #    if user_org_id:
    #        db = current.db
    #        s3db = current.s3db
    #        otable = s3db.org_organisation
    #        org = db(otable.id == user_org_id).select(otable.pe_id,
    #                                                  limitby=(0, 1)
    #                                                  ).first()
    #        if org:
    #            pe_id = org.pe_id
    #            pe_ids = s3db.pr_get_descendants((pe_id,),
    #                                             entity_types=("org_organisation",))
    #            rows = db(otable.pe_id.belongs(pe_ids)).select(otable.id)
    #            ids = [row.id for row in rows]
    #            ids.append(user_org_id)
    #            return ids
    #        else:
    #            return user_org_id
    #    else:
    #        # no default
    #        return {}

    # -------------------------------------------------------------------------
    def customise_auth_user_controller(**attr):
        """
            Customise admin/user() and default/user() controllers
        """

        # Organisation needs to be an NS/Branch
        ns_only("auth_user",
                required = True,
                branches = True,
                updateable = False, # Need to see all Orgs in Registration screens
                )

        table = current.db.auth_user
        table.first_name.label = T("Forenames")
        table.last_name.label = T("Father's Surname")

        return attr

    settings.customise_auth_user_controller = customise_auth_user_controller

    # -------------------------------------------------------------------------
    def customise_deploy_alert_resource(r, tablename):

        s3db = current.s3db

        # Only send Alerts via Email
        # @ToDo: Also send via Twitter
        f = s3db[tablename].contact_method
        f.readable = f.writable = False

        #from s3 import S3SQLCustomForm

        #crud_form = S3SQLCustomForm("mission_id",
        #                            "subject",
        #                            "body",
        #                            "modified_on",
        #                            )

        #s3db.configure(tablename,
        #               crud_form = crud_form,
        #               list_fields = ["mission_id",
        #                              "subject",
        #                              "body",
        #                              ],
        #               )

    settings.customise_deploy_alert_resource = customise_deploy_alert_resource

    # -------------------------------------------------------------------------
    def deploy_application_onaccept(form):
        """
            RIT Members should be added to the RIT Role
        """

        db = current.db
        s3db = current.s3db
        htable = db.hrm_human_resource
        ptable = db.pr_person

        # Find the Person
        human_resource_id = form.vars.get("human_resource_id")
        if human_resource_id:
            query = (htable.id == human_resource_id)
        else:
            table = db.deploy_application
            query = (table.id == form.vars.get("id")) & \
                    (table.human_resource_id == htable.id)

        hr = db(query).select(htable.person_id,
                              limitby=(0, 1)
                              ).first()
        person_id = hr.person_id

        # Do they have a User Account?
        ltable = s3db.pr_person_user
        query = (ptable.id == person_id) & \
                (ltable.pe_id == ptable.pe_id)
        link = db(query).select(ltable.user_id,
                                limitby=(0, 1)
                                ).first()
        if link:
            # Add them to the RIT role
            current.auth.s3_assign_role(link.user_id, "RIT_MEMBER")

    # -------------------------------------------------------------------------
    def customise_deploy_application_resource(r, tablename):

        current.s3db.configure(tablename,
                               create_onaccept = deploy_application_onaccept,
                               )

    settings.customise_deploy_application_resource = customise_deploy_application_resource

    # -------------------------------------------------------------------------
    def customise_deploy_mission_resource(r, tablename):

        s3db = current.s3db
        s3db[tablename].event_type_id.label = T("Disaster Type")
        COUNTRY = current.messages.COUNTRY

        from s3 import S3SQLCustomForm

        crud_form = S3SQLCustomForm("name",
                                    "date",
                                    "location_id",
                                    "event_type_id",
                                    )

        #from s3 import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3TextFilter
        #filter_widgets = [S3TextFilter(["name",
        #                                "event_type_id$name",
        #                                "location_id",
        #                                ],
        #                               label=T("Search")
        #                               ),
        #                  S3LocationFilter("location_id",
        #                                   label=COUNTRY,
        #                                   widget="multiselect",
        #                                   levels=["L0"],
        #                                   hidden=True
        #                                   ),
        #                  S3OptionsFilter("event_type_id",
        #                                  widget="multiselect",
        #                                  hidden=True
        #                                  ),
        #                  #S3OptionsFilter("status",
        #                  #                options=s3db.deploy_mission_status_opts,
        #                  #                hidden=True
        #                  #                ),
        #                  S3DateFilter("date",
        #                               hide_time=True,
        #                               hidden=True
        #                               ),
        #                  ]

        list_fields = ["name",
                       "date",
                       "event_type_id",
                       (COUNTRY, "location_id"),
                       (T("Responses"), "response_count"),
                       (T("Members Deployed"), "hrquantity"),
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_deploy_mission_resource = customise_deploy_mission_resource

    # -------------------------------------------------------------------------
    def customise_event_event_type_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Disaster Type"),
            title_display = T("Disaster Type Details"),
            title_list = T("Disaster Types"),
            title_update = T("Edit Disaster Type Details"),
            title_upload = T("Import Disaster Types"),
            label_list_button = T("List Disaster Types"),
            label_delete_button = T("Delete Disaster Type"),
            msg_record_created = T("Disaster Type added"),
            msg_record_modified = T("Disaster Type Details updated"),
            msg_record_deleted = T("Disaster Type deleted"),
            msg_list_empty = T("No Disaster Types currently defined"))

    settings.customise_event_event_type_resource = customise_event_event_type_resource

    # -------------------------------------------------------------------------
    def customise_hrm_certificate_controller(**attr):

        table = current.s3db.hrm_course
        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            # See all Certificates
            pass
        elif auth.s3_has_roles(("training_coordinator",
                                "training_assistant",
                                )):
            # Only show this Center's Certificates
            organisation_id = auth.user.organisation_id
            current.response.s3.filter = (table.organisation_id == organisation_id) | \
                                         (table.organisation_id == None)
            # Default to this Training Center
            table.organisation_id.default = organisation_id
        else:
            # See NS Certificates
            organisation_id = auth.root_org()
            current.response.s3.filter = (table.organisation_id == organisation_id) | \
                                         (table.organisation_id == None)
            # Default to this NS
            table.organisation_id.default = organisation_id
        return attr

    settings.customise_hrm_certificate_controller = customise_hrm_certificate_controller

    # -------------------------------------------------------------------------
    def customise_hrm_course_controller(**attr):

        table = current.s3db.hrm_course
        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            # See all Courses
            pass
        elif auth.s3_has_roles(("training_coordinator",
                                "training_assistant",
                                )):
            # Only show this Center's courses
            current.response.s3.filter = (table.organisation_id == auth.user.organisation_id) | (table.organisation_id == None)
        else:
            # See NS Courses
            current.response.s3.filter = (table.organisation_id == auth.root_org()) | (table.organisation_id == None)

        return attr

    settings.customise_hrm_course_controller = customise_hrm_course_controller

    # -------------------------------------------------------------------------
    def customise_hrm_course_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_NOT_IN_DB
        from s3 import S3SQLCustomForm

        db = current.db
        auth = current.auth
        s3db = current.s3db
        table = s3db[tablename]

        # Code should be Unique
        f = table.code
        f.requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "hrm_course.code"))

        if auth.s3_has_roles(("training_coordinator",
                              "training_assistant",
                              )):
            f = table.organisation_id
            f.label = T("Training Center")
            f.comment = False # Don't create here
            org_represent = s3db.org_OrganisationRepresent(parent=False)
            f.represent = org_represent

        list_fields = ["code",
                       "name",
                       ]

        has_role = auth.s3_has_role
        if has_role("ADMIN"):
            table.organisation_id.label = T("National Society / Training Center")
            list_fields.insert(0, "organisation_id")
            #f.readable = f.writable = True
            #ttable = s3db.org_organisation_type
            #try:
            #    type_id = db(ttable.name == "Training Center").select(ttable.id,
            #                                                          limitby=(0, 1),
            #                                                          ).first().id
            #except:
            #    # No/incorrect prepop done - skip (e.g. testing impacts of CSS changes in this theme)
            #    pass
            #else:
            #    ltable = s3db.org_organisation_organisation_type
            #    rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
            #    filter_opts = [row.organisation_id for row in rows]

            #    f.requires = IS_ONE_OF(db, "org_organisation.id",
            #                           org_represent,
            #                           orderby = "org_organisation.name",
            #                           sort = True,
            #                           filterby = "id",
            #                           filter_opts = filter_opts,
            #                           )

        elif has_role("training_coordinator"):
            f.default = auth.user.organisation_id

        crud_form = S3SQLCustomForm("organisation_id",
                                    "code",
                                    "name",
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       orderby = "hrm_course.code",
                       )

    settings.customise_hrm_course_resource = customise_hrm_course_resource

    # -------------------------------------------------------------------------
    #def customise_hrm_department_controller(**attr):

    #    # Organisation needs to be an NS/Branch
    #    ns_only("hrm_department",
    #            required = False,
    #            branches = False,
    #            )

    #    return attr

    #settings.customise_hrm_department_controller = customise_hrm_department_controller

    # -------------------------------------------------------------------------
    #def emergency_contact_represent(row):
    #    """
    #        Representation of Emergency Contacts (S3Represent label renderer)

    #        @param row: the row
    #    """

    #    items = [row["pr_contact_emergency.name"]]
    #    relationship = row["pr_contact_emergency.relationship"]
    #    if relationship:
    #        items.append(" (%s)" % relationship)
    #    phone_number = row["pr_contact_emergency.phone"]
    #    if phone_number:
    #        items.append(": %s" % phone_number)
    #    return "".join(items)

    # -------------------------------------------------------------------------
    def customise_hrm_home():

        from gluon import URL
        from s3 import s3_redirect_default

        has_role = current.auth.s3_has_role
        len_roles = len(current.session.s3.roles)
        if (len_roles <= 2) or \
           (len_roles == 3 and has_role("RIT_MEMBER") and not has_role("ADMIN")):
            # No specific Roles
            # Go to Personal Profile
            s3_redirect_default(URL(f="person"))
        else:
            # Bypass home page & go direct to searchable list of Staff
            s3_redirect_default(URL(f="human_resource", args="summary"))

    settings.customise_hrm_home = customise_hrm_home

    # -------------------------------------------------------------------------
    def customise_hrm_experience_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Work History"),
            title_display = T("Work History Details"),
            title_list = T("Work History"),
            title_update = T("Edit Work History"),
            label_list_button = T("List Work History"),
            label_delete_button = T("Delete Work History"),
            msg_record_created = T("Work History added"),
            msg_record_modified = T("Work History updated"),
            msg_record_deleted = T("Work History deleted"),
            msg_list_empty = T("No entries currently registered"))

    settings.customise_hrm_experience_resource = customise_hrm_experience_resource

    # -------------------------------------------------------------------------
    def generate_password():
        """
            Generate a Random Password
        """

        import random
        import string
        from gluon import CRYPT
        N = 8
        password = "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(N))
        crypted = CRYPT(key = current.auth.settings.hmac_key,
                        min_length = settings.get_auth_password_min_length(),
                        digest_alg = "sha512",
                        )(password)[0]
        return password, crypted

    # -------------------------------------------------------------------------
    def hrm_human_resource_create_onaccept(form):
        """
            If the Staff/Volunteer is RC then create them a user account with a random password
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars

        # Call normal onaccept
        s3db.hrm_human_resource_onaccept(form)

        # Is the person RC?
        organisation_id = form_vars.get("organisation_id")
        if not organisation_id:
            hr_id = form_vars.get("id")
            if not hr_id:
                # Nothing we can do!
                current.log.warning("Cannot create user for HR as no id in the form")
                return

            htable = s3db.hrm_human_resource
            hr = db(htable.id == hr_id).select(htable.id,
                                               htable.person_id,
                                               htable.type,
                                               htable.organisation_id,
                                               limitby = (0, 1),
                                               ).first()
            try:
                organisation_id = hr.organisation_id
            except AttributeError:
                # Nothing we can do!
                current.log.warning("Cannot create user for HR %s as cannot find HR record" % hr_id)
                return
        else:
            hr = None

        ttable = s3db.org_organisation_type
        ltable = s3db.org_organisation_organisation_type
        query = (ttable.name == RED_CROSS) & \
                (ltable.organisation_type_id == ttable.id) & \
                (ltable.organisation_id == organisation_id)
        RC = db(query).select(ltable.id,
                              limitby=(0, 1),
                              ).first()
        if not RC:
            return

        # Collect the Details needed
        person_id = form_vars.get("person_id")
        if not person_id:
            if not hr:
                hr_id = form_vars.get("id")
                if not hr_id:
                    # Nothing we can do!
                    current.log.warning("Cannot create user for HR as no id in the form")
                    return

                htable = s3db.hrm_human_resource
                hr = db(htable.id == hr_id).select(htable.id,
                                                   htable.person_id,
                                                   htable.type,
                                                   limitby = (0, 1),
                                                   ).first()
            try:
                person_id = hr.person_id
            except AttributeError:
                current.log.warning("Cannot create user for HR %s as cannot find HR record" % hr_id)
                return

        ptable = s3db.pr_person
        person = db(ptable.id == person_id).select(ptable.id,
                                                   ptable.first_name,
                                                   ptable.middle_name, # NB We use middle_name for User in RMS Americas!
                                                   ptable.pe_id,
                                                   limitby = (0, 1),
                                                   ).first()
        try:
            pe_id = person.pe_id
        except AttributeError:
            # Nothing we can do!
            return

        ctable = s3db.pr_contact
        query = (ctable.pe_id == pe_id) & \
                (ctable.contact_method == "EMAIL")
        contact = db(query).select(ctable.value,
                                   limitby = (0, 1),
                                   ).first()
        try:
            email = contact.value
        except AttributeError:
            # Nothing we can do!
            hr_id = form_vars.get("id")
            current.log.warning("Cannot create user for HR %s as cannot find Email" % hr_id)
            return

        hr_type = form_vars.get("type")
        if not hr_type:
            if not hr:
                hr_id = form_vars.get("id")
                if not hr_id:
                    # Nothing we can do!
                    current.log.warning("Cannot create user for HR as no id in the form")
                    return

                htable = s3db.hrm_human_resource
                hr = db(htable.id == hr_id).select(htable.id,
                                                   htable.type,
                                                   limitby = (0, 1),
                                                   ).first()
            try:
                hr_type = str(hr.type)
            except AttributeError:
                # Nothing we can do!
                current.log.warning("Cannot create user for HR %s as cannot find HR record" % hr_id)
                return

        if hr_type == "1":
            link_user_to = "staff"
        else:
            link_user_to = "volunteer"

        # This field has been manually added to the form
        language = current.request.post_vars.get("language")

        auth = current.auth

        # Generate a password
        password, crypted = generate_password()

        # Create User
        user = Storage(organisation_id = organisation_id,
                       language = language,
                       first_name = person.first_name,
                       last_name = person.middle_name, # NB We use middle_name for User in RMS Americas!
                       email = email,
                       link_user_to = link_user_to,
                       password = str(crypted),
                       )

        #user = auth.get_or_create_user(user, login=False)
        user_id = db.auth_user.insert(**user)

        # Set the HR record to be owned by this user
        if hr:
            hr.update_record(owned_by_user=user_id)
        else:
            hr_id = form_vars.get("id")
            db(s3db.hrm_human_resource.id == hr_id).update(owned_by_user=user_id)

        # Set the Person record to be owned by this user
        person.update_record(owned_by_user=user_id)

        # Cascade down to components
        # pr_address
        atable = s3db.pr_address
        db(atable.pe_id == pe_id).update(owned_by_user=user_id)
        # pr_contact
        db(ctable.pe_id == pe_id).update(owned_by_user=user_id)

        # Link to Person so that we find this in the 'Link'
        ltable = s3db.pr_person_user
        ltable.insert(pe_id = pe_id,
                      user_id = user_id,
                      )

        # Approve User, link to Person & send them a Welcome email
        user.update(id = user_id)
        messages = auth.messages
        messages.lock_keys = False
        messages.welcome_email = \
"""Welcome to %(system_name)s
 - You can start using %(system_name)s at: %(url)s
 - Your password is: %(password)s
 - To edit your profile go to: %(url)s%(profile)s
Thank you"""
        messages.lock_keys = True
        auth.s3_approve_user(user, password=password)

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        #controller = current.request.controller
        #if controller != "deploy":
        #    # Default Filter
        #    from s3 import s3_set_default_filter
        #    s3_set_default_filter("~.organisation_id",
        #                          user_org_and_children_default_filter,
        #                          tablename = "hrm_human_resource")

        s3 = current.response.s3
        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        if current.request.function == "trainee":
            EXTERNAL = True
        else:
            EXTERNAL = False

        def add_language(form):
            from gluon import LABEL, OPTION, SELECT
            from s3 import s3_addrow
            formstyle = settings.get_ui_formstyle()
            language_opts = [OPTION(T("Spanish"), _value="es", _selected="selected"),
                             OPTION(T("French"), _value="fr"),
                             OPTION(T("English"), _value="en"),
                             ]
            s3_addrow(form,
                      LABEL("%s:" % T("Language"),
                            _id="auth_user_language__label",
                            _for="auth_user_language",
                            ),
                      SELECT(_id="auth_user_language",
                             _name="language",
                             *language_opts
                             ),
                      "",
                      formstyle,
                      "auth_user_language__row",
                      position = 3,
                      )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            from s3 import FS

            db = current.db
            s3db = current.s3db
            auth = current.auth
            resource = r.resource
            table = r.table

            if EXTERNAL:
                f = table.organisation_id
                f.label = T("Organization")

                # Organisation cannot be an NS/Branch
                # Lookup organisation_type_id for Red Cross
                ttable = s3db.org_organisation_type
                type_ids = db(ttable.name.belongs((RED_CROSS, "Training Center"))).select(ttable.id,
                                                                                          limitby=(0, 2),
                                                                                          cache = s3db.cache,
                                                                                          )
                if type_ids:
                    from s3 import IS_ONE_OF
                    ltable = db.org_organisation_organisation_type
                    rows = db(ltable.organisation_type_id.belongs(type_ids)).select(ltable.organisation_id)
                    not_filter_opts = [row.organisation_id for row in rows]
                    f.requires = IS_ONE_OF(db, "org_organisation.id",
                                           f.represent,
                                           not_filterby = "id",
                                           not_filter_opts = not_filter_opts,
                                           updateable = True,
                                           orderby = "org_organisation.name",
                                           sort = True)

                    resource.add_filter(~FS("organisation_id").belongs(not_filter_opts))

                    # Find the relevant filter widget & limit it's options
                    filter_widgets = s3db.get_config("hrm_human_resource", "filter_widgets")
                    filter_widget = None
                    if filter_widgets:
                        from s3 import S3HierarchyFilter
                        for w in filter_widgets:
                            if isinstance(w, S3HierarchyFilter) and \
                               w.field == "organisation_id":
                                filter_widget = w
                                break
                    if filter_widget is not None:
                        filter_widget.opts["filter"] = (~FS("id").belongs(not_filter_opts))

            else:
                s3db.org_organisation.root_organisation.label = T("National Society")

                # Organisation needs to be an NS/Branch
                ns_only("hrm_human_resource",
                        required = True,
                        branches = True,
                        # default
                        #limit_filter_opts = True,
                        )

                export_formats = list(settings.get_ui_export_formats())

                if not r.id:
                    # Filter to just RC people
                    resource.add_filter(FS("organisation_id$organisation_type.name") == RED_CROSS)
                    resource.configure(create_onaccept = hrm_human_resource_create_onaccept,
                                       form_postp = add_language,
                                       )

                    # Custom list_fields
                    list_fields = [(T("Full Name"), "person_id"),
                                   "organisation_id",
                                   (T("Program"), "person_id$hours.programme_id"),
                                   (T("National ID"), "person_id$national_id.value"),
                                   "code",
                                   (T("Email"), "email.value"),
                                   (settings.get_ui_label_mobile_phone(), "phone.value"),
                                   ]
                    r.resource.configure(list_fields = list_fields)

                    # Bind method for signature list export + add export icon
                    from templates.RMSAmericas.siglist import HRSignatureList
                    s3db.set_method("hrm", "human_resource",
                                    method = "siglist",
                                    action = HRSignatureList,
                                    )
                    export_formats.append(("siglist.pdf", "fa fa-list", T("Export Signature List")))
                    s3.formats["siglist.pdf"] = r.url(method="siglist")

                if auth.s3_has_roles(ID_CARD_EXPORT_ROLES):
                    if r.representation == "card":
                        # Configure ID card layout
                        from templates.RMSAmericas.idcards import IDCardLayout
                        resource.configure(pdf_card_layout = IDCardLayout)

                    if not r.id and not r.component:
                        # Add export-icon for ID cards
                        export_formats.append(("card", "fa fa-id-card", T("Export ID Cards")))
                        s3.formats["card"] = r.url(method="")

                settings.ui.export_formats = export_formats


            if not auth.s3_has_role("ADMIN") and \
                   auth.s3_has_roles(("training_coordinator", "training_assistant")):
                # Filter People to just those trained by this Reference Center
                resource.add_filter(FS("training.training_event_id$organisation_id") == auth.user.organisation_id)

            # Default to Volunteers
            table.type.default = 2

            # Hide Venues from the list of Offices
            from gluon import IS_EMPTY_OR

            ttable = s3db.org_facility_type
            ltable = s3db.org_site_facility_type
            query = (ltable.facility_type_id == ttable.id) & \
                    (ttable.name == "Venue")
            venues = db(query).select(ltable.site_id)
            venues = [f.site_id for f in venues]
            stable = s3db.org_site
            dbset = db(~stable.site_id.belongs(venues))

            f = table.site_id
            new_requires = f.requires.other
            new_requires.dbset = dbset
            f.requires = IS_EMPTY_OR(new_requires)

            table = s3db.pr_person
            table.first_name.label = T("Forenames")
            table.middle_name.label = T("Father's Surname")
            table.last_name.label = T("Mother's Surname")

            # For the filter
            s3db.hrm_competency.skill_id.label = T("Language")

            return True
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if not EXTERNAL and \
               r.method in (None, "create") and \
               isinstance(output, dict):
                form = output.get("form")
                if form:
                    add_language(form)

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_hrm_job_title_resource(r, tablename):

        s3db = current.s3db

        f = s3db.hrm_job_title.type
        f.default = 3 # Both
        #f.readable  = f.writable = False

        label = T("Position")
        label_create = T("Create Position")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = label_create,
            title_display = T("Position Details"),
            title_list = T("Position Catalog"),
            title_update = T("Edit Position"),
            title_upload = T("Import Positions"),
            label_list_button = T("List Positions"),
            label_delete_button = T("Delete Position"),
            msg_record_created = T("Position added"),
            msg_record_modified = T("Position updated"),
            msg_record_deleted = T("Position deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        from s3layouts import S3PopupLink
        f = s3db.hrm_job_title_id.attr
        f.label = label
        f.comment = S3PopupLink(c = "hrm",
                                f = "job_title",
                                label = label_create,
                                title = label,
                                )

    settings.customise_hrm_job_title_resource = customise_hrm_job_title_resource

    # -------------------------------------------------------------------------
    def customise_hrm_job_title_controller(**attr):

        s3 = current.response.s3

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

            if current.auth.s3_has_role("ADMIN"):
                from s3 import S3OptionsFilter, S3TextFilter
                filter_widgets = [S3TextFilter(["name",
                                                ],
                                               label=T("Search")
                                               ),
                                  S3OptionsFilter("organisation_id",
                                                  ),
                                  ]
                current.s3db.configure("hrm_job_title",
                                       filter_widgets = filter_widgets,
                                       )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

    # -------------------------------------------------------------------------
    def customise_hrm_programme_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("hrm_programme",
                required = False,
                branches = False,
                )

        f = current.s3db.hrm_programme.name_long
        f.readable = f.writable = False

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
    def customise_hrm_programme_hours_resource(r, tablename):

        from s3 import S3SQLCustomForm

        s3db = current.s3db
        phtable = s3db.hrm_programme_hours

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Hours of Service"),
            title_display = T("Hours Details"),
            title_list = T("Hours of Service"),
            title_update = T("Edit Hours"),
            label_list_button = T("List Hours"),
            label_delete_button = T("Delete Hours"),
            msg_record_created = T("Hours added"),
            msg_record_modified = T("Hours updated"),
            msg_record_deleted = T("Hours deleted"),
            msg_list_empty = T("Currently no hours recorded"))

        # Show new custom fields
        phtable.event.readable = phtable.event.writable = True
        phtable.place.readable = phtable.place.writable = True
        # Hide old fields so they don't appear in list_fields in hrm_Record
        #phtable.programme_id.readable = phtable.programme_id.writable = False
        phtable.job_title_id.readable = phtable.job_title_id.writable = False

        crud_form = S3SQLCustomForm("date",
                                    "programme_id",
                                    "place",
                                    "event",
                                    "hours",
                                    )

        # Only visible in hrm_Record which controls list_fields itself
        #list_fields = ["date",
        #               "programme_id",
        #               "place",
        #               "event",
        #               "training_id$training_event_id$location_id",
        #               "training_id$training_event_id$course_id",
        #               "hours",
        #               ]

        s3db.configure("hrm_programme_hours",
                       crud_form = crud_form,
                       #list_fields = list_fields,
                       )

    settings.customise_hrm_programme_hours_resource = customise_hrm_programme_hours_resource

    # -------------------------------------------------------------------------
    def customise_hrm_skill_resource(r, tablename):

        #label = T("Language")
        label_create = T("Create Language")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = label_create,
            title_display = T("Language Details"),
            title_list = T("Language Catalog"),
            title_update = T("Edit Language"),
            label_list_button = T("List Languages"),
            label_delete_button = T("Delete Language"),
            msg_record_created = T("Language added"),
            msg_record_modified = T("Language updated"),
            msg_record_deleted = T("Language deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        # No use since cannot be sure this runs before hrm_competency table is loaded
        #from s3layouts import S3PopupLink
        #f = current.s3db.hrm_skill_id.attr
        #f.label = label
        #f.comment = S3PopupLink(c = "hrm",
        #                        f = "skill",
        #                        label = label_create,
        #                        title = label,
        #                        )

    settings.customise_hrm_skill_resource = customise_hrm_skill_resource

    # -------------------------------------------------------------------------
    def customise_hrm_competency_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Language"),
            title_display = T("Language Details"),
            title_list = T("Languages"),
            title_update = T("Edit Language"),
            label_list_button = T("List Languages"),
            label_delete_button = T("Delete Language"),
            msg_record_created = T("Language added"),
            msg_record_modified = T("Language updated"),
            msg_record_deleted = T("Language deleted"),
            msg_list_empty = T("No entries currently registered"))

        label = T("Language")
        from s3layouts import S3PopupLink
        f = current.s3db.hrm_competency.skill_id
        f.label = label
        f.comment = S3PopupLink(c = "hrm",
                                f = "skill",
                                label = T("Create Language"),
                                title = label,
                                )

    settings.customise_hrm_competency_resource = customise_hrm_competency_resource

    # -------------------------------------------------------------------------
    def hrm_training_onaccept(form):
        """
            Add People to the RIT Alert List if they have passed the RIT course
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars

        # Lookup full record
        table = db.hrm_training
        record = db(table.id == form_vars.id).select(table.id,
                                                     table.person_id,
                                                     table.course_id,
                                                     table.grade,
                                                     limitby=(0, 1)).first()
        try:
            course_id = record.course_id
        except AttributeError:
            current.log.error("Cannot find Training record")
            return

        # Lookup the RIT Course ID
        ctable = db.hrm_course
        row = db(ctable.name == "Regional Intervention Teams").select(ctable.id,
                                                                      cache = s3db.cache,
                                                                      limitby=(0, 1)
                                                                      ).first()
        try:
            rit_course_id = row.id
        except AttributeError:
            current.log.error("Cannot find RIT Course: Prepop not done?")
            return

        if course_id != rit_course_id:
            # Nothing to do
            return

        if record.grade != 8:
            # Not passed: Nothing to do
            return

        # Is person already a RIT Member?
        person_id = record.person_id
        htable = s3db.hrm_human_resource
        hr = db(htable.person_id == person_id).select(htable.id,
                                                      limitby=(0, 1)
                                                      ).first()
        try:
            human_resource_id = hr.id
        except AttributeError:
            current.log.error("Cannot find Human Resource record")
            return

        dtable = s3db.deploy_application
        exists = db(dtable.human_resource_id == human_resource_id).select(dtable.id,
                                                                          limitby=(0, 1)
                                                                          ).first()
        if not exists:
            # Add them to the list
            dtable.insert(human_resource_id = human_resource_id)

        # Add them to the RIT role
        ltable = s3db.pr_person_user
        ptable = db.pr_person
        query = (ptable.id == person_id) & \
                (ltable.pe_id == ptable.pe_id)
        link = db(query).select(ltable.user_id,
                                limitby=(0, 1)
                                ).first()
        if link:
            current.auth.s3_assign_role(link.user_id, "RIT_MEMBER")

    # -------------------------------------------------------------------------
    def hrm_training_postimport(import_info):
        """
            Create Users for Persons created
        """

        training_ids = import_info["created"]
        if not training_ids:
            # No new people created
            return

        db = current.db
        s3db = current.s3db

        # Find all the Persons
        ttable = s3db.hrm_training
        ptable = s3db.pr_person
        query = (ttable.id.belongs(training_ids)) & \
                (ttable.person_id == ptable.id)
        trainings = db(query).select(ptable.pe_id)
        person_pe_ids = set([p.pe_id for p in trainings])

        if not person_pe_ids:
            # No people?
            return

        # Remove those with a User Account
        ltable = s3db.pr_person_user
        users = db(ltable.pe_id.belongs(person_pe_ids)).select(ltable.pe_id)
        user_pe_ids = [u.pe_id for u in users]
        discard = person_pe_ids.discard
        for pe_id in user_pe_ids:
            discard(pe_id)

        if not person_pe_ids:
            # Nobody without a User Account already
            return

        # Read Person Details
        ctable = s3db.pr_contact
        dtable = s3db.pr_person_details
        htable = s3db.hrm_human_resource
        left = [ctable.on((ctable.pe_id == ptable.pe_id) & \
                          (ctable.contact_method == "EMAIL")
                          ),
                dtable.on(dtable.person_id == ptable.id),
                htable.on(htable.person_id == ptable.id),
                ]
        persons = db(ptable.pe_id.belongs(person_pe_ids)).select(ptable.id,
                                                                 ptable.first_name,
                                                                 # RMSAmericas uses Apellido Paterno for Last Name
                                                                 ptable.middle_name,
                                                                 #ptable.last_name,
                                                                 ctable.value,
                                                                 dtable.language,
                                                                 htable.type,
                                                                 htable.organisation_id,
                                                                 left=left,
                                                                 )
        utable = db.auth_user
        create_user = utable.insert
        approve_user = current.auth.s3_approve_user
        cert_table = s3db.hrm_certification
        # For each Person
        for p in persons:
            person = p["pr_person"]
            hr = p["hrm_human_resource"]

            if hr.type == 1:
                link_user_to = "staff"
            else:
                link_user_to = "volunteer"

            # Set random password
            password, crypted = generate_password()

            # Create a User Account
            user = Storage(first_name = person.first_name,
                           last_name = person.middle_name,
                           #last_name = person.last_name,
                           email = p["pr_contact.value"],
                           language = p["pr_person_details.language"],
                           password = crypted,
                           organisation_id = hr.organisation_id,
                           link_user_to = link_user_to,
                           )
            user_id = create_user(**user)

            # Standard Approval (inc Link to Person/HR and Send out Welcome Email with password)
            user["id"] = user_id
            approve_user(user, password)

            # Fixup permissions
            person_id = person.id
            db(htable.person_id == person_id).update(owned_by_user = user_id)
            db(ttable.person_id == person_id).update(owned_by_user = user_id)
            db(cert_table.person_id == person_id).update(owned_by_user = user_id)

    # -------------------------------------------------------------------------
    def customise_hrm_training_controller(**attr):

        s3 = current.response.s3

        # Default Filter
        #from s3 import s3_set_default_filter
        #s3_set_default_filter("~.person_id$human_resource.organisation_id",
        #                      user_org_default_filter,
        #                      tablename = "hrm_training")

        auth = current.auth
        if not auth.s3_has_role("ADMIN") and \
               auth.s3_has_roles(("training_coordinator", "training_assistant")):
            TC = True
            # Filter Trainings to just those done by this Reference Center
            from s3 import FS
            query = FS("~.training_event_id$organisation_id") == auth.user.organisation_id
            s3.filter = query
        else:
            TC = False

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            if r.method == "import":
                # HR records may be created via importing them as participants
                s3db = current.s3db
                # Default to Volunteers
                s3db.hrm_human_resource.type.default = 2
                if TC:
                    # Doesn't work as email created after human_resource
                    #s3db.configure("hrm_human_resource",
                    #               create_onaccept = hrm_human_resource_create_onaccept,
                    #               )
                    # Create User Accounts for those Persons without them
                    s3db.configure("hrm_training",
                                   postimport = hrm_training_postimport,
                                   )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_training_controller = customise_hrm_training_controller

    # -------------------------------------------------------------------------
    def customise_hrm_training_resource(r, tablename):

        s3db = current.s3db
        table = s3db.hrm_training
        f = table.grade
        f.readable = f.writable = True
        f = table.qualitative_feedback
        f.readable = f.writable = True

        s3db.hrm_certification.number.label = T("Registration Number")

        from s3 import S3SQLCustomForm, S3TextFilter, S3OptionsFilter, S3DateFilter

        if r.function == "person":
            crud_form = S3SQLCustomForm("course_id",
                                        "end_date",
                                        "grade",
                                        "grade_details",
                                        "qualitative_feedback",
                                        "certification_from_training.number",
                                        )
        else:
            crud_form = S3SQLCustomForm("person_id",
                                        "end_date",
                                        "grade",
                                        "grade_details",
                                        "qualitative_feedback",
                                        "certification_from_training.number",
                                        )

        filter_widgets = [
            S3TextFilter(["person_id$first_name",
                          "person_id$last_name",
                          "course_id$name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("You can search by trainee name, course name or comments. You may use % as wildcard. Press 'Search' without input to list all trainees."),
                         _class="filter-search",
                         ),
            S3OptionsFilter("training_event_id$site_id",
                            label = T("Country"),
                            represent = s3db.org_SiteRepresent(show_type=False),
                            ),
            S3OptionsFilter("person_id$human_resource.organisation_id",
                            label = T("Organization"),
                            ),
            S3OptionsFilter("course_id",
                            ),
            S3OptionsFilter("grade",
                            ),
            S3DateFilter("date",
                         hide_time=True,
                         ),
            ]

        default_onaccept = s3db.get_config(tablename, "onaccept")
        if default_onaccept and not isinstance(default_onaccept, list): # Catch running twice
            onaccept = [default_onaccept,
                        hrm_training_onaccept,
                        ]
        else:
            onaccept = hrm_training_onaccept

        s3db.configure(tablename,
                      crud_form = crud_form,
                      filter_widgets = filter_widgets,
                      onaccept = onaccept,
                      )

    settings.customise_hrm_training_resource = customise_hrm_training_resource

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_resource(r, tablename):

        from s3 import IS_ONE_OF, S3SQLCustomForm, S3SQLInlineComponent

        db = current.db
        auth = current.auth
        s3db = current.s3db
        table = s3db.hrm_training_event

        org_represent = s3db.org_OrganisationRepresent(parent=False)

        f = table.organisation_id
        f.label = T("Training Center")
        f.comment = False # Don't create here
        f.represent = org_represent

        list_fields = ["organisation_id",
                       "course_id",
                       #"site_id",
                       "location_id",
                       "start_date",
                       "training_event_instructor.person_id",
                       "comments",
                       ]

        if auth.s3_has_role("ADMIN"):
            #f.readable = f.writable = True
            ttable = s3db.org_organisation_type
            try:
                type_id = db(ttable.name == "Training Center").select(ttable.id,
                                                                      limitby=(0, 1),
                                                                      ).first().id
            except AttributeError:
                # No/incorrect prepop done - skip (e.g. testing impacts of CSS changes in this theme)
                pass
            else:
                ltable = s3db.org_organisation_organisation_type
                rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
                filter_opts = [row.organisation_id for row in rows]

                f.requires = IS_ONE_OF(db, "org_organisation.id",
                                       org_represent,
                                       orderby = "org_organisation.name",
                                       sort = True,
                                       filterby = "id",
                                       filter_opts = filter_opts,
                                       )

        elif auth.s3_has_roles(("training_coordinator", "training_assistant")):
            organisation_id = auth.user.organisation_id
            f.default = organisation_id
            f.writable = False
            list_fields.pop(0) # organisation_id
            table.course_id.requires.set_filter(filterby = "organisation_id",
                                                filter_opts = [organisation_id],
                                                )

        # Hours are Optional
        from gluon import IS_EMPTY_OR
        table.hours.requires = IS_EMPTY_OR(table.hours)

        #site_represent = S3Represent(lookup = "org_site")

        # Filter list of Venues
        #f = table.site_id
        #f.default = None
        #f.label = T("Country")
        #f.represent = site_represent

        #ftable = s3db.org_facility
        #ltable = s3db.org_site_facility_type
        #ttable = s3db.org_facility_type
        #query = (ftable.deleted == False) & \
        #        (ftable.site_id == ltable.site_id) & \
        #        (ltable.facility_type_id == ttable.id) & \
        #        (ttable.name == "Venue")
        #rows = db(query).select(ftable.site_id)
        #filter_opts = [row.site_id for row in rows]
        #f.requires = IS_ONE_OF(db, "org_site.site_id",
        #                       site_represent,
        #                       filterby="site_id",
        #                       filter_opts=filter_opts,
        #                       )

        # Multiple Instructors
        crud_form = S3SQLCustomForm("organisation_id",
                                    # @ToDo: Filter Courses by Training Center
                                    "course_id",
                                    #"site_id",
                                    "location_id",
                                    "start_date",
                                    "end_date",
                                    S3SQLInlineComponent("training_event_instructor",
                                                         label = T("Instructor"),
                                                         fields = [("", "person_id")],
                                                         # @ToDo: Filter to HRMs (this should be done through AC?)
                                                         #filterby = ({"field": "type",
                                                         #             "options": 3,
                                                         #             },),
                                                         ),
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_hrm_training_event_resource = customise_hrm_training_event_resource

    # -------------------------------------------------------------------------
    def hrm_training_event_report_pdf_export(r, **attr):
        """
            Generate a PDF Export of a training Event Report
        """

        from s3 import s3_fullname, s3_str

        record = r.record

        T = current.T
        db = current.db
        s3db = current.s3db

        current_language = T.accepted_language
        if current_language == "es":
            # Reach different translation
            title = s3_str(T("Training Event Report"))
        else:
            title = s3_str(T("Training Report"))

        if record.course_id:
            course_name = s3db.hrm_training_event.course_id.represent(record.course_id)
            title = "%s: %s" % (title, course_name)

        def callback(r):

            from gluon.html import DIV, TABLE, TD, TH, TR

            rtable = s3db.hrm_training_event_report

            date_represent = rtable.date.represent
            org_represent = s3db.org_OrganisationRepresent(parent = False,
                                                           acronym = False)

            # Logo
            otable = db.org_organisation
            org_id = record.organisation_id
            org = db(otable.id == org_id).select(otable.name,
                                                 otable.acronym, # Present for consistent cache key
                                                 otable.logo,
                                                 limitby=(0, 1),
                                                 ).first()
            #if settings.get_L10n_translate_org_organisation():
            #org_name = org_represent(org_id)
            #else:
            #    org_name = org.name

            logo = org.logo
            if logo:
                logo = s3db.org_organisation_logo(org)
            elif current.deployment_settings.get_org_branches():
                root_org = current.cache.ram(
                    # Common key with auth.root_org
                    "root_org_%s" % org_id,
                    lambda: s3db.org_root_organisation(org_id),
                    time_expire=120
                    )
                logo = s3db.org_organisation_logo(root_org)

            # Read the report
            report = db(rtable.training_event_id == r.id).select(limitby = (0, 1),
                                                                 ).first()

            # Header
            header = TABLE(TR(TH("%s:" % T("Name")),
                              TD(s3_fullname(report.person_id)),
                              TH("%s:" % T("Training Date")),
                              TD(date_represent(record.start_date)),
                              ),
                           TR(TH("%s:" % T("Position")),
                              TD(rtable.job_title_id.represent(report.job_title_id)),
                              TH("%s:" % T("Finance Codes")),
                              TD(report.code),
                              ),
                           TR(TH("%s:" % T("National Society Visited")),
                              TD(org_represent(report.organisation_id)),
                              TH("%s:" % T("Report Date")),
                              TD(date_represent(report.date)),
                              ),
                           TR(TH("%s:" % T("Training Purpose")),
                              TD(report.purpose,
                                 _colspan = 3,
                                 ),
                              ),
                           )

            # Main
            main = TABLE(TR(TH("1. %s" % T("Objectives"))),
                         TR(TD(report.objectives)),
                         TR(TH("2. %s" % T("Methodology"))),
                         TR(TD(report.methodology)),
                         TR(TH("3. %s" % T("Implemented Actions"))),
                         TR(TD(report.actions)),
                         TR(TH("4. %s" % T("About the participants"))),
                         TR(TD(report.participants)),
                         TR(TH("5. %s" % T("Results and Lessons Learned"))),
                         TR(TD(report.results)),
                         TR(TH("6. %s" % T("Follow-up Required"))),
                         TR(TD(report.followup)),
                         TR(TH("7. %s" % T("Additional relevant information"))),
                         TR(TD(report.additional)),
                         TR(TH("8. %s" % T("General Comments"))),
                         TR(TD(report.comments)),
                         )

            output = DIV(TABLE(TR(TD(logo),
                                  #TD(org_name), # This isn't rtl-proof, check vol_service_record for how to handle that if-required
                                  )),
                         TABLE(TR(TD(title))),
                         TABLE(header),
                         TABLE(main),
                         )

            return output

        attr["rheader"] = None

        from s3.s3export import S3Exporter

        exporter = S3Exporter().pdf
        pdf_title = title
        return exporter(r.resource,
                        request = r,
                        method = "list",
                        pdf_title = pdf_title,
                        pdf_table_autogrow = "B",
                        pdf_callback = callback,
                        **attr
                        )

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_controller(**attr):

        T = current.T
        auth = current.auth
        s3db = current.s3db
        s3 = current.response.s3

        if not auth.s3_has_role("ADMIN") and \
               auth.s3_has_roles(("training_coordinator", "training_assistant")):
            # Filter People to just those trained by this Reference Center
            from s3 import FS
            query = FS("~.organisation_id") == auth.user.organisation_id
            s3.filter = query

        s3db.set_method("hrm", "training_event",
                        method = "report_pdf_export",
                        action = hrm_training_event_report_pdf_export,
                        )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "training_event_report" and r.component_id:
                from gluon.html import A, DIV, URL
                from s3 import ICON
                s3.rfooter = DIV(A(ICON("print"),
                                 " ",
                                 T("PDF Report"),
                                   _href=URL(args=[r.id, "report_pdf_export"]),#, extension="pdf"),
                                   _class="action-btn",
                                   ),
                                 )

            return result
        s3.prep = custom_prep

        attr["rheader"] = lambda r: \
            s3db.hrm_rheader(r, tabs=[(T("Training Event Details"), None),
                                      (T("Participants"), "participant"),
                                      (T("Report"), "training_event_report"),
                                      ])
        return attr

    settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_report_resource(r, tablename):

        s3db = current.s3db
        table = s3db.hrm_training_event_report
        table.person_id.default = current.auth.s3_logged_in_person()
        table.person_id.label = T("Name")
        ns_only("hrm_training_event_report",
                required = False,
                branches = False,
                updateable = False,
                )
        table.organisation_id.label = T("National Society Visited")
        table.code.label = T("Finance Codes")

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("person_id",
                                    "job_title_id",
                                    "organisation_id",
                                    "purpose",
                                    "code",
                                    "date",
                                    (("1. %s" % table.objectives.label), "objectives"),
                                    (("2. %s" % table.methodology.label), "methodology"),
                                    (("3. %s" % table.actions.label), "actions"),
                                    (("4. %s" % table.participants.label), "participants"),
                                    (("5. %s" % table.results.label), "results"),
                                    (("6. %s" % table.followup.label), "followup"),
                                    (("7. %s" % table.additional.label), "additional"),
                                    (("8. %s" % table.comments.label), "comments"),
                                    S3SQLInlineComponent("document",
                                                         label = "9. %s" % T("Supporting Documentation"),
                                                         link = False,
                                                         fields = ["file"],
                                                         ),
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_hrm_training_event_report_resource = customise_hrm_training_event_report_resource

    # -------------------------------------------------------------------------
    def customise_member_membership_resource(r, tablename):

        from s3layouts import S3PopupLink

        ADD_MEMBERSHIP_TYPE = T("Create Partner Type")

        s3db = current.s3db
        table = s3db.member_membership
        table.code.label = T("Partner ID")
        table.membership_type_id.comment = S3PopupLink(f = "membership_type",
                                                       label = ADD_MEMBERSHIP_TYPE,
                                                       title = ADD_MEMBERSHIP_TYPE,
                                                       tooltip = T("Add a new partner type to the catalog."),
                                                       )
        list_fields = [(T("Full Name"), "person_id"),
                       "organisation_id",
                       "membership_type_id",
                       "code",
                       (T("National ID"), "person_id$national_id.value"),
                       (T("Email"), "email.value"),
                       (T("Mobile Phone"), "phone.value"),
                       "membership_fee",
                       (T("Paid"), "paid"),
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Partner"),
            title_display = T("Partner Details"),
            title_list = T("Partners"),
            title_update = T("Edit Partner Details"),
            title_upload = T("Import Partners"),
            label_list_button = T("List Partners"),
            label_delete_button = T("Delete Partner"),
            msg_record_created = T("Partner added"),
            msg_record_modified = T("Partner updated"),
            msg_record_deleted = T("Partner deleted"),
            msg_list_empty = T("No Partners currently defined"))

    settings.customise_member_membership_resource = customise_member_membership_resource

    # -------------------------------------------------------------------------
    def customise_member_membership_controller(**attr):

        ns_only("member_membership",
                required = True,
                branches = True,
                updateable = True,
                )

        return attr

    settings.customise_member_membership_controller = customise_member_membership_controller

    # -------------------------------------------------------------------------
    def customise_member_membership_type_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Partner Type"),
            title_display = T("Partner Type Details"),
            title_list = T("Partner Types"),
            title_update = T("Edit Partner Type Details"),
            title_upload = T("Import Partner Types"),
            label_list_button = T("List Partner Types"),
            label_delete_button = T("Delete Partner Type"),
            msg_record_created = T("Partner Type added"),
            msg_record_modified = T("Partner Type updated"),
            msg_record_deleted = T("Partner Type deleted"),
            msg_list_empty = T("No Partner Types currently defined"))

    settings.customise_member_membership_type_resource = customise_member_membership_type_resource

    # -------------------------------------------------------------------------
    def customise_member_membership_type_controller(**attr):

        ns_only("member_membership_type",
                required = False,
                branches = False,
                updateable = True,
                )

        return attr

    settings.customise_member_membership_type_controller = customise_member_membership_type_controller

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def inv_pdf_header(r, title=None):
        """
            PDF header for Stock Reports

            @param r: the S3Request
            @param title: the report title
        """

        # Get organisation name and logo
        from layouts import OM
        name, logo = OM().render()

        from gluon.html import DIV, H2, H4, P, TABLE, TR, TD

        # Report title and subtitle
        title = H2(title) if title else ""
        subtitle = ""

        get_vars = r.get_vars
        report = get_vars.get("report")
        if report == "movements":
            from s3 import S3TypeConverter, S3DateTime
            # Get earliest/latest date from filter
            convert = S3TypeConverter.convert
            dtstr = get_vars.get("_transaction.date__ge")
            earliest = convert(datetime.datetime, dtstr) if dtstr else ""
            dtstr = get_vars.get("_transaction.date__le")
            latest = convert(datetime.datetime, dtstr) if dtstr else ""
            # Convert into local calendar/format
            if earliest:
                earliest = S3DateTime.date_represent(earliest, utc=True)
            if latest:
                latest = S3DateTime.date_represent(latest, utc=True)
            # Add as subtitle
            if earliest or latest:
                subtitle = P(" - ".join((earliest, latest)))

        output = TABLE(TR(TD(DIV(logo, H4(name))),
                          TD(DIV(title, subtitle)),
                          ),
                       )

        return output

    # -------------------------------------------------------------------------
    def customise_inv_inv_item_resource(r, tablename):

        s3db = current.s3db

        resource = r.resource
        if resource.tablename == "inv_inv_item" and r.method == "grouped":
            report = r.get_vars.get("report")
            if report == "weight_and_volume":
                # Add field methods for total weight and volume
                from gluon import Field
                table = s3db.inv_inv_item
                table.total_weight = Field.Method("total_weight",
                                                  s3db.inv_item_total_weight,
                                                  )
                table.total_volume = Field.Method("total_volume",
                                                  s3db.inv_item_total_volume,
                                                  )
                s3db.configure("inv_inv_item",
                               extra_fields = ["item_id$weight",
                                               "item_id$volume",
                                               ],
                               )
            elif report == "movements":
                # Inject a date filter for transactions
                filter_widgets = resource.get_config("filter_widgets")
                from s3 import S3DateFilter
                date_filter = S3DateFilter("transaction_date",
                                           label = T("Date"),
                                           fieldtype = "date",
                                           selector = "_transaction.date",
                                           )
                filter_widgets.insert(1, date_filter)

        # Stock Reports
        stock_reports = {"default": {
                            "title": T("Stock Position Report"),
                            "fields": [(T("Warehouse"), "site_id$name"),
                                       "item_id$item_category_id",
                                       "bin",
                                       "item_id$name",
                                       "quantity",
                                       "pack_value",
                                       "total_value",
                                       ],
                            "groupby": ["site_id",
                                        ],
                            "orderby": ["site_id$name",
                                        "item_id$name",
                                        ],
                            "aggregate": [("sum", "quantity"),
                                          ("sum", "total_value"),
                                          ],
                            "pdf_header": inv_pdf_header,
                            },
                         "weight_and_volume": {
                            "title": T("Weight and Volume Report"),
                            "fields": [(T("Warehouse"), "site_id$name"),
                                       "item_id$item_category_id",
                                       "bin",
                                       "item_id$name",
                                       "quantity",
                                       "item_id$weight",
                                       "item_id$volume",
                                       "total_weight",
                                       "total_volume",
                                       ],
                            "groupby": ["site_id",
                                        ],
                            "orderby": ["site_id$name",
                                        "item_id$name",
                                        ],
                            "aggregate": [("sum", "quantity"),
                                          ("sum", "total_weight"),
                                          ("sum", "total_volume"),
                                          ],
                            "pdf_header": inv_pdf_header,
                            },
                         "movements": {
                            "title": T("Stock Movements Report"),
                            "fields": [(T("Warehouse"), "site_id$name"),
                                       "item_id$item_category_id",
                                       "bin",
                                       "item_id$name",
                                       (T("Origin/Destination"), "sites"),
                                       (T("Documents"), "documents"),
                                       (T("Initial Quantity"), "original_quantity"),
                                       (T("Incoming"), "quantity_in"),
                                       (T("Outgoing"), "quantity_out"),
                                       (T("Final Quantity"), "quantity"),
                                       ],
                            "groupby": ["site_id",
                                        ],
                            "orderby": ["site_id$name",
                                        "item_id$name",
                                        ],
                            "aggregate": [("sum", "original_quantity"),
                                          ("sum", "quantity_in"),
                                          ("sum", "quantity_out"),
                                          ("sum", "quantity"),
                                          ],
                            "extract": s3db.inv_stock_movements,
                            "pdf_header": inv_pdf_header,
                            },
                         }

        current.s3db.configure("inv_inv_item",
                               create = False,
                               deletable = False,
                               editable = False,
                               listadd = False,
                               grouped = stock_reports,
                               )

    settings.customise_inv_inv_item_resource = customise_inv_inv_item_resource

    # -------------------------------------------------------------------------
    def customise_inv_send_resource(r, tablename):

        s3db = current.s3db

        s3db.configure("inv_send",
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

        # Custom Waybill
        s3db.set_method("inv", "send",
                        method = "form",
                        action = PrintableShipmentForm,
                        )

    settings.customise_inv_send_resource = customise_inv_send_resource

    # -------------------------------------------------------------------------
    def customise_inv_recv_resource(r, tablename):

        # Custom GRN
        current.s3db.set_method("inv", "recv",
                                method = "form",
                                action = PrintableShipmentForm,
                                )

    settings.customise_inv_recv_resource = customise_inv_recv_resource

    # -------------------------------------------------------------------------
    def customise_inv_warehouse_resource(r, tablename):

        settings.inv.recv_tab_label = "Received/Incoming Shipments"
        settings.inv.send_tab_label = "Sent Shipments"
        # Only Nepal RC use Warehouse Types
        s3db = current.s3db
        field = s3db.inv_warehouse.warehouse_type_id
        field.readable = field.writable = False
        list_fields = s3db.get_config("inv_warehouse", "list_fields")
        try:
            list_fields.remove("warehouse_type_id")
        except ValueError:
            # Already removed
            pass

    settings.customise_inv_warehouse_resource = customise_inv_warehouse_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        #root_org = current.auth.root_org_name()
        #if root_org != HNRC:
        #    return

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

    # -------------------------------------------------------------------------
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
                    # default
                    #limit_filter_opts = True,
                    )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_org_office_controller = customise_org_office_controller

    # -------------------------------------------------------------------------
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

                    if r.function == "training_center":
                        auth = current.auth
                        if not auth.s3_has_role("ADMIN"):
                            # See NS Training Centers only
                            resource.add_filter(table.root_organisation == auth.root_org())

                            if not auth.s3_has_role("ORG_ADMIN"):
                                resource.configure(insertable = False)

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

                    else:
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
                                try:
                                    list_fields.remove("organisation_organisation_type.organisation_type_id")
                                except ValueError:
                                    # Already removed
                                    pass
                                type_label = ""

                            if type_filter == RED_CROSS:
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

        if type_filter == "Supplier":
            # Suppliers have simpler Tabs (hide Offices, Warehouses and Contacts)
            tabs = [(T("Basic Details"), None, {"native": 1}),
                    ]
            if settings.get_L10n_translate_org_organisation():
                tabs.append((T("Local Names"), "name"))
            attr["rheader"] = lambda r: current.s3db.org_rheader(r, tabs=tabs)

        elif type_filter == "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency":
            # Partners have simpler Tabs (hide Offices, Warehouses and Contacts)
            tabs = [(T("Basic Details"), None, {"native": 1}),
                    (T("Projects"), "project"),
                    ]
            if settings.get_L10n_translate_org_organisation():
                tabs.insert(1, (T("Local Names"), "name"))
            attr["rheader"] = lambda r: current.s3db.org_rheader(r, tabs=tabs)

        else:
            # Enable tab for PDF card configurations
            settings.org.pdf_card_configs = True

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_pr_address_resource(r, tablename):

        #if current.auth.root_org_name() in ("Honduran Red Cross",
        #                                    "Paraguayan Red Cross",
        #                                    ):
            # Location Hierarchy loaded: Leave things as they are since we have the
        #   pass
        #else:
        s3db = current.s3db
        s3db.gis_location.addr_street.label = T("Address")
        s3db.configure("pr_address",
                       list_fields = ["type",
                                      (current.messages.COUNTRY, "location_id$L0"),
                                      (T("Address"), "location_id$addr_street"),
                                      #(settings.get_ui_label_postcode(),
                                      # "location_id$addr_postcode")
                                      ],
                       )

    settings.customise_pr_address_resource = customise_pr_address_resource

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        table = current.s3db[tablename]
        table.comments.readable = table.comments.writable = False
        table.contact_description.readable = table.contact_description.writable = False
        table.priority.readable = table.priority.writable = False

    settings.customise_pr_contact_resource = customise_pr_contact_resource

    # -------------------------------------------------------------------------
    def customise_pr_education_resource(r, tablename):

        s3db = current.s3db
        table = s3db[tablename]
        table.country.readable = table.country.writable = True
        table.grade.readable = table.grade.writable = False
        table.major.readable = table.major.writable = False
        s3db.configure(tablename,
                       list_fields = [# Normally accessed via component
                                      #"person_id",
                                      "year",
                                      "level_id",
                                      "award",
                                      #"major",
                                      #"grade",
                                      "institute",
                                      ],
                       )

    settings.customise_pr_education_resource = customise_pr_education_resource

    # -------------------------------------------------------------------------
    def customise_pr_forum_resource(r, tablename):

        table = current.s3db.pr_forum
        table.forum_type.readable = table.forum_type.writable = False

    settings.customise_pr_forum_resource = customise_pr_forum_resource

    # -------------------------------------------------------------------------
    def customise_pr_forum_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "assign":
                auth = current.auth
                has_role = auth.s3_has_role
                if not has_role("ADMIN") and has_role("training_coordinator"):
                    # Filter people to just those Trained by this Reference Center or Staff of this Reference Center
                    from s3 import FS
                    organisation_id = auth.user.organisation_id
                    query = (FS("training.training_event_id$organisation_id") == organisation_id) | \
                            (FS("user.organisation_id") == organisation_id)
                    s3.filter = query

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_pr_forum_controller = customise_pr_forum_controller

    # -------------------------------------------------------------------------
    #def customise_pr_group_controller(**attr):

    #    # Organisation needs to be an NS/Branch
    #    ns_only("org_organisation_team",
    #            required = False,
    #            branches = True,
    #            )

    #    return attr

    #settings.customise_pr_group_controller = customise_pr_group_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        table = current.s3db[tablename]
        table.first_name.label = T("Forenames")
        table.middle_name.label = T("Father's Surname")
        table.last_name.label = T("Mother's Surname")

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3
        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            auth = current.auth
            has_role = auth.s3_has_role
            EXTERNAL = False
            if "profile" in current.request.get_vars:
                profile = True
            else:
                len_roles = len(current.session.s3.roles)
                if (len_roles <= 2) or \
                   (len_roles == 3 and has_role("RIT_MEMBER") and not has_role("ADMIN")):
                    profile = True
                else:
                    profile = False
                    if r.function == "trainee_person":
                        EXTERNAL = True
                        s3.crud_strings["pr_person"].update(
                            title_display = T("External Trainee Details"),
                            title_update = T("External Trainee Details")
                            )
            if profile:
                # Configure for personal mode
                # People can edit their own HR data
                configure = s3db.configure
                configure("hrm_human_resource",
                          deletable = False,
                          #editable = True,
                          insertable = False,
                          )
                if not has_role("RIT_MEMBER"):
                    #configure("hrm_certification",
                    #          deletable = True,
                    #          editable = True,
                    #          insertable = True,
                    #          )
                    configure("hrm_training",
                              deletable = False,
                              editable = False,
                              insertable = False,
                              )

            component_name = r.component_name
            method = r.method
            if method == "import":
                # HR records may be created via import
                # Default to Volunteers
                s3db.hrm_human_resource.type.default = 2
                # Doesn't work as email created after human_resource
                #s3db.configure("hrm_human_resource",
                #               create_onaccept = hrm_human_resource_create_onaccept,
                #               )

            elif method =="record" or component_name == "human_resource":
                table = s3db.hrm_human_resource
                if EXTERNAL:
                    db = current.db
                    f = table.organisation_id
                    f.label = T("Organization")
                    # Organisation cannot be an NS/Branch
                    # Lookup organisation_type_id for Red Cross
                    ttable = s3db.org_organisation_type
                    type_ids = db(ttable.name.belongs((RED_CROSS, "Training Center"))).select(ttable.id,
                                                                                              limitby=(0, 2),
                                                                                              cache = s3db.cache,
                                                                                              )
                    if type_ids:
                        from s3 import IS_ONE_OF
                        ltable = db.org_organisation_organisation_type
                        rows = db(ltable.organisation_type_id.belongs(type_ids)).select(ltable.organisation_id)
                        not_filter_opts = [row.organisation_id for row in rows]
                        f.requires = IS_ONE_OF(db, "org_organisation.id",
                                               f.represent,
                                               not_filterby = "id",
                                               not_filter_opts = not_filter_opts,
                                               updateable = True,
                                               orderby = "org_organisation.name",
                                               sort = True)
                else:
                    # Organisation needs to be an NS/Branch
                    if auth.s3_has_roles(("surge_capacity_manager",
                                          "ns_training_manager",
                                          "ns_training_assistant",
                                          "training_coordinator",
                                          "training_assistant",
                                          )):
                        updateable = False
                    else:
                        updateable = True
                    ns_only("hrm_human_resource",
                            required = True,
                            branches = True,
                            updateable = updateable,
                            )
                f = table.essential
                f.readable = f.writable = False
                f = table.site_contact
                f.readable = f.writable = False
                if method == "record":
                    if not auth.s3_has_roles(("ORG_ADMIN",
                                              "hr_manager",
                                              "hr_assistant",
                                              )):
                        table.organisation_id.writable = False
                        # Hide the Site field as this data isn't loaded & we want to keep things simple
                        # @ToDo: Re-enable for specific NS as-required
                        f = table.site_id
                        f.readable = f.writable = False
                    # Use default form (legacy)
                    #s3db.clear_config("hrm_human_resource", "crud_form")

            elif not component_name:
                s3db.configure("pr_person",
                               listadd = True,
                               )

                # Basic Details tab
                f = s3db.pr_person.middle_name
                f.readable = f.writable = True
                f = s3db.pr_person_details.nationality2
                f.readable = f.writable = True
                from s3 import S3SQLCustomForm
                crud_form = S3SQLCustomForm("first_name",
                                            "middle_name",
                                            "last_name",
                                            "date_of_birth",
                                            "gender",
                                            "person_details.marital_status",
                                            "person_details.nationality",
                                            "person_details.nationality2",
                                            "comments",
                                            )
                s3db.configure("pr_person",
                               crud_form = crud_form,
                               )

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
                field = atable.job_title_id
                field.comment = None
                field.label = T("Sector") # RDRT-specific
                from s3 import IS_ONE_OF
                field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                                           field.represent,
                                           filterby = "type",
                                           filter_opts = (4,),
                                           )

            elif component_name == "certification":
                ctable = r.component.table
                ctable.organisation_id.readable = False

            elif component_name == "competency":
                ctable = r.component.table
                ctable.skill_id.label = T("Language")
                ctable.organisation_id.readable = False

            elif component_name == "experience":
                # 2 options here: Work Experience & Missions
                # These have very different views
                # Work Experience
                etable = r.component.table
                etable.organisation_id.readable = etable.organisation_id.writable = False
                etable.job_title_id.readable = etable.job_title_id.writable = False
                etable.responsibilities.readable = etable.responsibilities.writable = False
                etable.hours.readable = etable.hours.writable = False
                etable.supervisor_id.readable = etable.supervisor_id.writable = False
                etable.organisation.readable = etable.organisation.writable = True
                etable.job_title.readable = etable.job_title.writable = True
                from s3 import S3LocationSelector
                etable.location_id.label = T("Country")
                etable.location_id.widget = S3LocationSelector(levels=("L0",),
                                                               show_map=False,
                                                               show_postcode=False,
                                                               )

            elif component_name == "identity":
                #itable = r.component.table
                # Default
                #itable.country_code.readable = itable.country_code.writable = False
                #itable.ia_name.readable = itable.ia_name.writable = False
                f = r.component.table.ia_name
                f.readable = f.writable = False
                list_fields = ["type",
                               "value",
                               "valid_until",
                               ]
                s3db.configure("pr_identity",
                               list_fields = list_fields,
                               )

            elif component_name == "physical_description":
                from gluon import DIV
                dtable = r.component.table
                dtable.medical_conditions.comment = DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Medical Conditions"),
                                                                          T("Chronic Illness, Disabilities, Mental/Psychological Condition etc.")))
                dtable.allergic.writable = dtable.allergic.readable = True
                dtable.allergies.writable = dtable.allergies.readable = True
                dtable.ethnicity.writable = dtable.ethnicity.readable = False
                dtable.other_details.writable = dtable.other_details.readable = False
                import json
                SEPARATORS = (",", ":")
                s3.jquery_ready.append('''S3.showHidden('%s',%s,'%s')''' % \
                    ("allergic", json.dumps(["allergies"], separators=SEPARATORS), "pr_physical_description"))

            if not EXTERNAL and \
               auth.s3_has_roles(ID_CARD_EXPORT_ROLES):
                # Show button to export ID card
                settings.hrm.id_cards = True

            return True
        s3.prep = custom_prep

        if current.request.controller in ("hrm", "vol"):
            attr["csv_template"] = ("../../themes/RMSAmericas/formats", "hrm_person")
            # Common rheader for all views
            attr["rheader"] = s3db.hrm_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def customise_supply_item_category_resource(r, tablename):

        #root_org = current.auth.root_org_name()
        #if root_org == HNRC:
        # Not using Assets Module
        field = current.s3db.supply_item_category.can_be_asset
        field.readable = field.writable = False

    settings.customise_supply_item_category_resource = customise_supply_item_category_resource

    # -------------------------------------------------------------------------
    def customise_project_window_resource(r, tablename):

        r.resource.configure(deletable = False,
                             insertable = False,
                             )

    settings.customise_project_window_resource = customise_project_window_resource

    # -------------------------------------------------------------------------
    def customise_project_activity_data_resource(r, tablename):

        if current.auth.s3_has_roles(("monitoring_evaluation", "ORG_ADMIN")):
            # Normal Access
            return

        # Project Manager
        if r.method == "update":

            table = current.s3db.project_activity_data

            if r.tablename == "project_activity_data":
                record_id = r.id
            else:
                record_id = r.component_id
            record = current.db(table.id == record_id).select(table.value,
                                                              limitby=(0, 1)
                                                              ).first()
            if record.value:
                # Redirect to Read-only mode
                from gluon import redirect
                redirect(r.url(method="read"))
            else:
                # Cannot edit anything
                for f in table.fields:
                    table[f].writable = False
                # Except add a Real value
                table.value.writable = True
                # Or Amend the Comments
                table.comments.writable = True
        else:
            s3db = current.s3db
            table = s3db.project_window
            record = current.db(table.deleted == False).select(table.start_date,
                                                               table.end_date,
                                                               limitby = (0, 1)
                                                               ).first()
            if record:
                if record.start_date <= r.utcnow.date() <= record.end_date:
                    # Inside the time window: Project Manager may update Actuals
                    return
            # Outside the time window: Project Manager cannot add the Actual value
            s3db.project_activity_data.value.writable = False
            s3db.configure("project_activity_data",
                           updateable = False,
                           )

    settings.customise_project_activity_data_resource = customise_project_activity_data_resource

    # -------------------------------------------------------------------------
    def customise_project_organisation_resource(r, tablename):

        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            from gluon import IS_IN_SET
            currency_opts = {"EUR" : "EUR",
                             "CHF" : "CHF",
                             "HNL" : "L",
                             "USD" : "USD",
                             }
            f = current.s3db.project_organisation.currency
            f.represent = currency_represent
            f.requires = IS_IN_SET(currency_opts)

    settings.customise_project_organisation_resource = customise_project_organisation_resource

    # -------------------------------------------------------------------------
    def project_project_postprocess(form):
        """
            When using Budget Monitoring (i.e. HNRC) then create the entries
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
                              user_org_default_filter,
                              tablename = "project_project")

        # Load standard model
        s3db = current.s3db
        table = s3db[tablename]

        # Disable Map Tab on Summary View
        # - until we can support multiple Points per Record
        settings.ui.summary = ({"common": True,
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
                                "label": "Report",
                                "widgets": [{"method": "report",
                                             "ajax_init": True}]
                                },
                               #{"name": "map",
                               # "label": "Map",
                               # "widgets": [{"method": "map",
                               #              "ajax_init": True}],
                               # },
                               )

        # @ToDo: S3SQLInlineComponent for Project orgs
        # Get IDs for Partner NS/Partner Donor
        # db = current.db
        # ttable = db.org_organisation_type
        # rows = db(ttable.deleted != True).select(ttable.id,
        #                                          ttable.name,
        #                                          )
        # rc = []
        # not_rc = []
        # nappend = not_rc.append
        # for row in rows:
            # if row.name == RED_CROSS:
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
            # @ToDo: Use Inter-American Framework instead (when extending to Zone office)
            # @ToDo: Add 'Business Line' (when extending to Zone office)
            project_settings = settings.project
            project_settings.details_tab = True
            #project_settings.community_volunteers = True
            # Done in a more structured way instead
            objectives = None
            outputs = None
            project_settings.goals = True
            project_settings.outcomes = True
            project_settings.outputs = True
            project_settings.indicators = True
            project_settings.indicator_criteria = True
            project_settings.status_from_activities = True
            table.human_resource_id.label = T("Coordinator")
            # Use Budget module instead of ProjectAnnualBudget
            project_settings.multiple_budgets = False
            project_settings.budget_monitoring = True
            # Require start/end dates
            table.start_date.requires = table.start_date.requires.other
            table.end_date.requires = table.end_date.requires.other
            budget = S3SQLInlineComponent("budget",
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
            btable.currency.represent = currency_represent
            currency_opts = {"EUR" : "EUR",
                             "CHF" : "CHF",
                             "HNL" : "L",
                             "USD" : "USD",
                             }
            from gluon import IS_IN_SET
            btable.currency.requires = IS_IN_SET(currency_opts)
            s3db.budget_monitoring.currency.represent = currency_represent
            postprocess = project_project_postprocess
            list_fields = s3db.get_config("project_project", "list_fields")
            list_fields += [(T("Actual Progress"), "actual_progress_by_activities"),
                            (T("Planned Progress"), "planned_progress_by_activities"),
                            ]
        else:
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

            if r.method == "grouped":

                grouped = {"default":
                        {"title": T("Global Report of Projects Status"),
                         "fields": [(T("Project"), "name"),
                                    (T("Program"), "programme.name"),
                                    (T("Donor"), "donor.organisation_id"),
                                    (T("Budget"), "budget.total_budget"),
                                    (T("Location"), "location.location_id"),
                                    "start_date",
                                    "end_date",
                                    ],
                         "orderby": ["name",
                                     ],
                         "aggregate": [("sum", "budget.total_budget"),
                                       ],
                         },
                       }

                from s3 import S3DateFilter, S3OptionsFilter

                filter_widgets = [S3DateFilter("date",
                                               label = T("Time Period"),
                                               hide_time = True,
                                               ),
                                  S3OptionsFilter("programme_project.programme_id",
                                                  label = T("Programs"),
                                                  ),
                                  S3OptionsFilter("theme_project.theme_id",
                                                  label = T("Themes"),
                                                  ),
                                  S3OptionsFilter("sector_project.sector_id",
                                                  label = T("Sectors"),
                                                  ),
                                  S3OptionsFilter("beneficiary.parameter_id",
                                                  label = T("Beneficiaries"),
                                                  ),
                                  S3OptionsFilter("hazard_project.hazard_id",
                                                  label = T("Hazards"),
                                                  ),
                                  ]

                s3db.configure(tablename,
                               filter_widgets = filter_widgets,
                               grouped = grouped,
                               )

            elif r.component:
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
                            #ctable.organisation_id.requires = \
                            #    s3db.org_organisation_requires(required = True,
                            #                                   # Only allowed to add Projects for Orgs
                            #                                   # that the user has write access to
                            #                                   updateable = True,
                            #                                   )

            else:
                # Lead Organisation needs to be an NS (not a branch)
                ns_only(tablename,
                        required = True,
                        branches = False,
                        # default
                        #limit_filter_opts = True,
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
    #def customise_project_beneficiary_resource(r, tablename):
    #    """
    #        Link Project Beneficiaries to Activity Type
    #    """

    #    if r.interactive and r.component:
    #        if r.tablename == "project_project":
    #            # We are a component of the Project
    #            project_id = r.id
    #        elif r.tablename == "project_location":
    #            # We are a component of the Project Location
    #            project_id = r.record.project_id
    #        else:
    #            # Unknown!
    #            return

    #        db = current.db
    #        s3db = current.s3db

    #        # Filter Activity Type by Sector
    #        ltable = s3db.project_sector_project
    #        rows = db(ltable.project_id == project_id).select(ltable.sector_id)
    #        sectors = [row.sector_id for row in rows]
    #        ltable = s3db.project_activity_type_sector
    #        rows = db(ltable.sector_id.belongs(sectors)).select(ltable.activity_type_id)
    #        filteropts = [row.activity_type_id for row in rows]

    #        def postprocess(form):
    #            # Update project_location.activity_type
    #            beneficiary_id = form.vars.get("id", None)
    #            table = db.project_beneficiary
    #            row = db(table.id == beneficiary_id).select(table.project_location_id,
    #                                                        limitby = (0, 1)
    #                                                        ).first()
    #            if not row:
    #                return
    #            project_location_id = row.project_location_id
    #            if not project_location_id:
    #                return
    #            ltable = db.project_beneficiary_activity_type
    #            row = db(ltable.beneficiary_id == beneficiary_id).select(ltable.activity_type_id,
    #                                                                     limitby = (0, 1)
    #                                                                     ).first()
    #            if not row:
    #                return
    #            activity_type_id = row.activity_type_id
    #            ltable = s3db.project_activity_type_location
    #            query = (ltable.project_location_id == project_location_id) & \
    #                    (ltable.activity_type_id == activity_type_id)
    #            exists = db(query).select(ltable.id,
    #                                      limitby = (0, 1)
    #                                      ).first()
    #            if not exists:
    #                ltable.insert(project_location_id = project_location_id,
    #                              activity_type_id = activity_type_id,
    #                              )

    #        from s3 import S3SQLCustomForm, S3SQLInlineLink
    #        crud_form = S3SQLCustomForm(#"project_id",
    #                                    "project_location_id",
    #                                    S3SQLInlineLink("activity_type",
    #                                                    field = "activity_type_id",
    #                                                    filterby = "id",
    #                                                    options = filteropts,
    #                                                    label = T("Activity Type"),
    #                                                    multiple = False,
    #                                                    ),
    #                                    "parameter_id",
    #                                    "value",
    #                                    "target_value",
    #                                    "date",
    #                                    "end_date",
    #                                    "comments",
    #                                    postprocess = postprocess,
    #                                    )

    #        s3db.configure(tablename,
    #                       crud_form = crud_form,
    #                       )

    #    elif not r.component:
    #        # Report
    #        from s3 import S3OptionsFilter
    #        resource = r.resource
    #        filter_widgets = resource.get_config("filter_widgets")
    #        filter_widgets.insert(1,
    #            S3OptionsFilter("beneficiary_activity_type.activity_type_id",
    #                            label = T("Activity Type"),
    #                            ))
    #        report_options = resource.get_config("report_options")
    #        report_options.rows.append("beneficiary_activity_type.activity_type_id")
    #        # Same object so would be added twice
    #        #report_options.cols.append("beneficiary_activity_type.activity_type_id")

    #        resource.configure(filter_widgets = filter_widgets,
    #                           report_options = report_options,
    #                           )

    # Only used for activity_types which aren't used by HNRC
    #settings.customise_project_beneficiary_resource = customise_project_beneficiary_resource

    # -------------------------------------------------------------------------
    #def customise_project_indicator_resource(r, tablename):

    #    table = current.s3db.project_indicator
    #    table.definition.label = T("Indicator Definition")
    #    table.measures.label = T("Indicator Criteria")

    #settings.customise_project_indicator_resource = customise_project_indicator_resource

    # -------------------------------------------------------------------------
    def customise_project_indicator_data_resource(r, tablename):

        table = current.s3db.project_indicator_data
        f = table.start_date
        f.readable = f.writable = True
        f.label = T("Start Date")
        table.end_date.label = T("End Date")

        if r.method == "update":
            has_role = current.auth.s3_has_role
            if has_role("monitoring_evaluation") or has_role("ORG_ADMIN"):
                # Normal Access
                return
            # Project Manager
            if r.tablename == "project_indicator_data":
                record_id = r.id
            else:
                record_id = r.component_id
            record = current.db(table.id == record_id).select(table.value,
                                                              limitby=(0, 1)
                                                              ).first()
            if record.value:
                # Redirect to Read-only mode
                # @ToDo: Remove 'Update' button from the read-only page
                from gluon import redirect
                redirect(r.url(method="read"))
            else:
                # Cannot edit anything
                for f in table.fields:
                    table[f].writable = False
                # Except add a Real value
                table.value.writable = True
                # Or Amend the Comments
                table.comments.writable = True

    settings.customise_project_indicator_data_resource = customise_project_indicator_data_resource

    # -------------------------------------------------------------------------
    def customise_project_location_resource(r, tablename):

        s3db = current.s3db
        table = s3db.project_location
        table.name.readable = False
        table.percentage.readable = table.percentage.writable = False
        #ist_fields = s3db.get_config(tablename, "list_fields")
        #try:
        #    list_fields.remove((T("Activity Types"), "activity_type.name"))
        #except:
        #    # Already removed
        #    pass

    settings.customise_project_location_resource = customise_project_location_resource

    # -------------------------------------------------------------------------
    def customise_project_location_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        #standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp (just does same thing but different)
            #if callable(standard_postp):
            #    output = standard_postp(r, output)

            if r.representation == "plain":
                # Map Popup
                from gluon import A, TABLE, TR, TD, B, URL
                s3db = current.s3db
                table = s3db.project_project
                project_id = r.record.project_id
                resource = s3db.resource("project_project", id=project_id)
                list_fields = ("name",
                               "status_id",
                               "start_date",
                               "end_date",
                               "budget.total_budget",
                               "budget.currency",
                               "hazard_project.hazard_id",
                               "sector_project.sector_id",
                               "theme_project.theme_id",
                               # Contact
                               "human_resource_id",
                               "overall_status_by_indicators",
                               )
                data = resource.select(list_fields, represent=True)
                record = data.rows[0]
                item = TABLE(TR(TD(B("%s:" % table.name.label)),
                                          TD(record["project_project.name"]),
                                          ),
                                       TR(TD(B("%s:" % table.status_id.label)),
                                          TD(record["project_project.status_id"]),
                                          ),
                                       TR(TD(B("%s:" % table.start_date.label)),
                                          TD(record["project_project.start_date"]),
                                          ),
                                       TR(TD(B("%s:" % table.end_date.label)),
                                          TD(record["project_project.end_date"]),
                                          ),
                                       TR(TD(B("%s:" % T("Budget"))),
                                          TD("%s %s" % (record["budget_budget.currency"],
                                                        record["budget_budget.total_budget"])),
                                          ),
                                       TR(TD(B("%s:" % s3db.project_hazard_project.hazard_id.label)),
                                          TD(record["project_hazard_project.hazard_id"]),
                                          ),
                                       TR(TD(B("%s:" % s3db.project_sector_project.sector_id.label)),
                                          TD(record["project_sector_project.sector_id"]),
                                          ),
                                       TR(TD(B("%s:" % s3db.project_theme_project.theme_id.label)),
                                          TD(record["project_theme_project.theme_id"]),
                                          ),
                                       TR(TD(B("%s:" % table.human_resource_id.label)),
                                          TD(record["project_project.human_resource_id"]),
                                          ),
                                       TR(TD(B("%s:" % T("Cumulative Status"))),
                                          TD(record["project_project.overall_status_by_indicators"]),
                                          ),
                                       )
                title = s3.crud_strings["project_project"].title_display
                # Assume authorised to see details
                popup_url = URL(f="project", args=[project_id])
                details_btn = A(T("Open"),
                                _href=popup_url,
                                _class="btn",
                                _id="details-btn",
                                _target="_blank")
                output = dict(item = item,
                              title = title,
                              details_btn = details_btn,
                              )

            return output

        s3.postp = custom_postp
        return attr

    settings.customise_project_location_controller = customise_project_location_controller

    # -------------------------------------------------------------------------
    def customise_req_commit_controller(**attr):

        # Request is mandatory
        field = current.s3db.req_commit.req_id
        field.requires = field.requires.other

        return attr

    settings.customise_req_commit_controller = customise_req_commit_controller

    # -------------------------------------------------------------------------
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
        except ValueError:
            # Already removed
            pass

        # Custom Request Form
        s3db.set_method("req", "req",
                       method = "form",
                       action = PrintableShipmentForm,
                       )

    settings.customise_req_req_resource = customise_req_req_resource

# =============================================================================
class PrintableShipmentForm(S3Method):
    """ REST Method Handler for Printable Shipment Forms """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes

            @note: always returns PDF, disregarding the requested format
        """

        output = {}
        if r.http == "GET":
            if r.id:
                tablename = r.tablename
                if tablename == "req_req":
                    output = self.request_form(r, **attr)
                elif tablename == "inv_send":
                    output = self.waybill(r, **attr)
                elif tablename == "inv_recv":
                    output = self.goods_received_note(r, **attr)
                else:
                    # Not supported
                    r.error(405, current.ERROR.BAD_METHOD)
            else:
                # Record ID is required
                r.error(400, current.ERROR.BAD_REQUEST)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def request_form(self, r, **attr):
        """
            Request Form

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T
        s3db = current.s3db

        # Master record (=req_req)
        resource = s3db.resource(r.tablename,
                                 id = r.id,
                                 components = ["req_item"],
                                 )

        # Columns and data for the form header
        header_fields = ["req_ref",
                         "date",
                         "date_required",
                         (T("Deliver to"), "site_id"),
                         (T("Reason for Request"), "purpose"),
                         "requester_id",
                         "site_id$site_id:inv_warehouse.contact",
                         "comments",
                         ]

        header_data = resource.select(header_fields,
                                      start = 0,
                                      limit = 1,
                                      represent = True,
                                      show_links = False,
                                      raw_data = True,
                                      )
        if not header_data:
            r.error(404, current.ERROR.BAD_RECORD)

        # Generate PDF header
        pdf_header = self.request_form_header(header_data)

        # Filename from send_ref
        header_row = header_data.rows[0]
        pdf_filename = header_row["_row"]["req_req.req_ref"]

        # Component (=inv_track_item)
        component = resource.components["req_item"]
        body_fields = ["item_id",
                       "item_pack_id",
                       "quantity",
                       "comments",
                       ]

        # Aggregate methods and column names
        aggregate = [("sum", "req_req_item.quantity"),
                     ]

        # Generate the JSON data dict
        json_data = self._json_data(component,
                                    body_fields,
                                    aggregate = aggregate,
                                    )

        # Generate the grouped items table
        from s3 import S3GroupedItemsTable
        output = S3GroupedItemsTable(component,
                                     data = json_data,
                                     totals_label = T("Total"),
                                     title = T("Logistics Requisition"),
                                     pdf_header = pdf_header,
                                     pdf_footer = self.request_form_footer,
                                     )

        # ...and export it as PDF
        return output.pdf(r, filename=pdf_filename)

    # -------------------------------------------------------------------------
    @classmethod
    def request_form_header(cls, data):
        """
            Header for Request Forms

            @param data: the S3ResourceData for the req_req
        """

        row = data.rows[0]
        labels = dict((rfield.colname, rfield.label) for rfield in data.rfields)
        def row_(left, right):
            return cls._header_row(left, right, row=row, labels=labels)

        from gluon import DIV, H2, H4, TABLE, TD, TH, TR, P

        T = current.T

        # Get organisation name and logo
        from layouts import OM
        name, logo = OM().render()

        # The title
        title = H2(T("Logistics Requisition"))

        # Waybill details
        dtable = TABLE(
                    TR(TD(DIV(logo, H4(name)), _colspan = 2),
                       TD(DIV(title), _colspan = 2),
                       ),
                    row_("req_req.req_ref", None),
                    row_("req_req.date", "req_req.date_required"),
                    row_("req_req.site_id", "req_req.purpose"),
                    row_("req_req.requester_id", "inv_warehouse.contact"),
                 )

        # Waybill comments
        ctable = TABLE(TR(TH(T("Comments"))),
                       TR(TD(row["req_req.comments"])),
                       )

        return DIV(dtable, P("&nbsp;"), ctable)

    # -------------------------------------------------------------------------
    @staticmethod
    def request_form_footer(r):
        """
            Footer for Request Forms

            @param r: the S3Request
        """

        T = current.T
        from gluon import TABLE, TH, TR

        return TABLE(TR(TH("&nbsp;"),
                        TH(T("Name")),
                        TH(T("Signature")),
                        TH(T("Date")),
                        ),
                     TR(TH(T("Requester"))),
                     TR(TH(T("Budget Administrator"))),
                     TR(TH(T("Finance"))),
                     )

    # -------------------------------------------------------------------------
    def waybill(self, r, **attr):
        """
            Waybill

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T
        s3db = current.s3db

        # Component declarations to distinguish between the
        # origin and destination warehouses
        s3db.add_components("inv_send",
                            inv_warehouse = ({"name": "origin",
                                              "joinby": "site_id",
                                              "pkey": "site_id",
                                              "filterby": False,
                                              "multiple": False,
                                              },
                                             {"name": "destination",
                                              "joinby": "site_id",
                                              "pkey": "to_site_id",
                                              "filterby": False,
                                              "multiple": False,
                                              },
                                             ),
                            )

        # Master record (=inv_send)
        resource = s3db.resource(r.tablename,
                                 id = r.id,
                                 components = ["origin",
                                               "destination",
                                               "track_item",
                                               ],
                                 )

        # Columns and data for the form header
        header_fields = ["send_ref",
                         "req_ref",
                         "date",
                         "delivery_date",
                         (T("Origin"), "site_id"),
                         (T("Destination"), "to_site_id"),
                         "sender_id",
                         "origin.contact",
                         "recipient_id",
                         "destination.contact",
                         "transported_by",
                         "transport_ref",
                         (T("Delivery Address"), "destination.location_id"),
                         "comments",
                         ]

        header_data = resource.select(header_fields,
                                      start = 0,
                                      limit = 1,
                                      represent = True,
                                      show_links = False,
                                      raw_data = True,
                                      )
        if not header_data:
            r.error(404, current.ERROR.BAD_RECORD)

        # Generate PDF header
        pdf_header = self.waybill_header(header_data)

        # Filename from send_ref
        header_row = header_data.rows[0]
        pdf_filename = header_row["_row"]["inv_send.send_ref"]

        # Component (=inv_track_item)
        component = resource.components["track_item"]
        body_fields = ["bin",
                       "item_id",
                       "item_pack_id",
                       "quantity",
                       (T("Total Volume (m3)"), "total_volume"),
                       (T("Total Weight (kg)"), "total_weight"),
                       "supply_org_id",
                       "inv_item_status",
                       ]
        # Any extra fields needed for virtual fields
        component.configure(extra_fields = ["item_id$weight",
                                            "item_id$volume",
                                            ],
                            )

        # Aggregate methods and column names
        aggregate = [("sum", "inv_track_item.quantity"),
                     ("sum", "inv_track_item.total_volume"),
                     ("sum", "inv_track_item.total_weight"),
                     ]

        # Generate the JSON data dict
        json_data = self._json_data(component,
                                    body_fields,
                                    aggregate = aggregate,
                                    )

        # Generate the grouped items table
        from s3 import S3GroupedItemsTable
        output = S3GroupedItemsTable(component,
                                     data = json_data,
                                     totals_label = T("Total"),
                                     title = T("Waybill"),
                                     pdf_header = pdf_header,
                                     pdf_footer = self.waybill_footer,
                                     )

        # ...and export it as PDF
        return output.pdf(r, filename=pdf_filename)

    # -------------------------------------------------------------------------
    @classmethod
    def waybill_header(cls, data):
        """
            Header for Waybills

            @param data: the S3ResourceData for the inv_send
        """

        row = data.rows[0]
        labels = dict((rfield.colname, rfield.label) for rfield in data.rfields)
        def row_(left, right):
            return cls._header_row(left, right, row=row, labels=labels)

        from gluon import DIV, H2, H4, TABLE, TD, TH, TR, P

        T = current.T

        # Get organisation name and logo
        from layouts import OM
        name, logo = OM().render()

        # The title
        title = H2(T("Waybill"))

        # Waybill details
        dtable = TABLE(
                    TR(TD(DIV(logo, H4(name)), _colspan = 2),
                       TD(DIV(title), _colspan = 2),
                       ),
                    row_("inv_send.send_ref", "inv_send.req_ref"),
                    row_("inv_send.date", "inv_send.delivery_date"),
                    row_("inv_send.site_id", "inv_send.to_site_id"),
                    row_("inv_send.sender_id", "inv_send.recipient_id"),
                    row_("inv_origin_warehouse.contact",
                         "inv_destination_warehouse.contact",
                         ),
                    row_("inv_send.transported_by", "inv_send.transport_ref"),
                    row_("inv_destination_warehouse.location_id", None),
                 )

        # Waybill comments
        ctable = TABLE(TR(TH(T("Comments"))),
                       TR(TD(row["inv_send.comments"])),
                       )

        return DIV(dtable, P("&nbsp;"), ctable)

    # -------------------------------------------------------------------------
    @staticmethod
    def waybill_footer(r):
        """
            Footer for Waybills

            @param r: the S3Request
        """

        T = current.T
        from gluon import TABLE, TD, TH, TR

        return TABLE(TR(TH(T("Shipment")),
                        TH(T("Date")),
                        TH(T("Function")),
                        TH(T("Name")),
                        TH(T("Signature")),
                        TH(T("Status")),
                        ),
                     TR(TD(T("Sent by"))),
                     TR(TD(T("Transported by"))),
                     TR(TH(T("Received by")),
                        TH(T("Date")),
                        TH(T("Function")),
                        TH(T("Name")),
                        TH(T("Signature")),
                        TH(T("Status")),
                        ),
                     TR(TD("&nbsp;")),
                     )

    # -------------------------------------------------------------------------
    def goods_received_note(self, r, **attr):
        """
            GRN (Goods Received Note)

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T
        s3db = current.s3db

        # Master record (=inv_recv)
        resource = s3db.resource(r.tablename,
                                 id = r.id,
                                 components = ["track_item"],
                                 )

        # Columns and data for the form header
        header_fields = ["eta",
                         "date",
                         (T("Origin"), "from_site_id"),
                         (T("Destination"), "site_id"),
                         "sender_id",
                         "recipient_id",
                         "send_ref",
                         "recv_ref",
                         "comments",
                         ]

        header_data = resource.select(header_fields,
                                      start = 0,
                                      limit = 1,
                                      represent = True,
                                      show_links = False,
                                      raw_data = True,
                                      )
        if not header_data:
            r.error(404, current.ERROR.BAD_RECORD)

        # Generate PDF header
        pdf_header = self.goods_received_note_header(header_data)

        # Filename from send_ref
        header_row = header_data.rows[0]
        pdf_filename = header_row["_row"]["inv_recv.recv_ref"]

        # Component (=inv_track_item)
        component = resource.components["track_item"]
        body_fields = ["recv_bin",
                       "item_id",
                       "item_pack_id",
                       "recv_quantity",
                       (T("Total Volume (m3)"), "total_recv_volume"),
                       (T("Total Weight (kg)"), "total_recv_weight"),
                       "supply_org_id",
                       "inv_item_status",
                       ]
        # Any extra fields needed for virtual fields
        component.configure(extra_fields = ["item_id$weight",
                                            "item_id$volume",
                                            ],
                            )

        # Aggregate methods and column names
        aggregate = [("sum", "inv_track_item.recv_quantity"),
                     ("sum", "inv_track_item.total_recv_volume"),
                     ("sum", "inv_track_item.total_recv_weight"),
                     ]

        # Generate the JSON data dict
        json_data = self._json_data(component,
                                    body_fields,
                                    aggregate = aggregate,
                                    )

        # Generate the grouped items table
        from s3 import S3GroupedItemsTable
        output = S3GroupedItemsTable(component,
                                     data = json_data,
                                     totals_label = T("Total"),
                                     title = T("Goods Received Note"),
                                     pdf_header = pdf_header,
                                     pdf_footer = self.goods_received_note_footer,
                                     )

        # ...and export it as PDF
        return output.pdf(r, filename=pdf_filename)

    # -------------------------------------------------------------------------
    @classmethod
    def goods_received_note_header(cls, data):
        """
            Header for Goods Received Notes

            @param data: the S3ResourceData for the inv_recv
        """

        row = data.rows[0]
        labels = dict((rfield.colname, rfield.label) for rfield in data.rfields)
        def row_(left, right):
            return cls._header_row(left, right, row=row, labels=labels)

        from gluon import DIV, H2, H4, TABLE, TD, TH, TR, P

        T = current.T

        # Get organisation name and logo
        from layouts import OM
        name, logo = OM().render()

        # The title
        title = H2(T("Goods Received Note"))

        # GRN details
        dtable = TABLE(TR(TD(DIV(logo, H4(name)), _colspan = 2),
                          TD(DIV(title), _colspan = 2),
                          ),
                       row_("inv_recv.eta", "inv_recv.date"),
                       row_("inv_recv.from_site_id", "inv_recv.site_id"),
                       row_("inv_recv.sender_id", "inv_recv.recipient_id"),
                       row_("inv_recv.send_ref", "inv_recv.recv_ref"),
                       )

        # GRN comments
        ctable = TABLE(TR(TH(T("Comments"))),
                       TR(TD(row["inv_recv.comments"])),
                       )

        return DIV(dtable, P("&nbsp;"), ctable)

    # -------------------------------------------------------------------------
    @staticmethod
    def goods_received_note_footer(r):
        """
            Footer for Goods Received Notes

            @param r: the S3Request
        """

        T = current.T
        from gluon import TABLE, TD, TH, TR

        return TABLE(TR(TH(T("Delivered by")),
                        TH(T("Date")),
                        TH(T("Function")),
                        TH(T("Name")),
                        TH(T("Signature")),
                        TH(T("Status")),
                        ),
                     TR(TD(T("&nbsp;"))),
                     TR(TH(T("Received by")),
                        TH(T("Date")),
                        TH(T("Function")),
                        TH(T("Name")),
                        TH(T("Signature")),
                        TH(T("Status")),
                        ),
                     TR(TD("&nbsp;")),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def _header_row(left, right, row=None, labels=None):
        """
            Helper function to generate a 2-column table row
            for the PDF header

            @param left: the column name for the left column
            @param right: the column name for the right column,
                          or None for an empty column
            @param row: the S3ResourceData row
            @param labels: dict of labels {colname: label}
        """

        from gluon import TD, TH, TR

        if right:
            header_row = TR(TH(labels[left]),
                            TD(row[left]),
                            TH(labels[right]),
                            TD(row[right]),
                            )
        else:
            header_row = TR(TH(labels[left]),
                            TD(row[left], _colspan = 3),
                            )
        return header_row

    # -------------------------------------------------------------------------
    @staticmethod
    def _json_data(component, list_fields, aggregate=None):
        """
            Extract, group and aggregate the data for the form body

            @param component: the component (S3Resource)
            @param list_fields: the columns for the form body
                                (list of field selectors)
            @param aggregate: aggregation methods and fields,
                              a list of tuples (method, column name)
        """

        # Extract the data
        data = component.select(list_fields,
                                limit = None,
                                raw_data = True,
                                represent = True,
                                show_links = False,
                                )

        # Get the column names and labels
        columns = []
        append_column = columns.append
        labels = {}
        for rfield in data.rfields:
            colname = rfield.colname
            append_column(colname)
            labels[colname] = rfield.label

        # Group and aggregate the items
        from s3 import S3GroupedItems
        gi = S3GroupedItems(data.rows,
                            aggregate = aggregate,
                            )

        # Convert into JSON-serializable dict for S3GroupedItemsTable
        json_data = gi.json(fields = columns,
                            labels = labels,
                            as_dict = True,
                            )

        return json_data

# END =========================================================================
