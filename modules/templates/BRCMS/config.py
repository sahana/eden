# -*- coding: utf-8 -*-

#import datetime

from collections import OrderedDict

from gluon import current #, A, DIV,IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY, SPAN, TAG, URL
from gluon.storage import Storage

#from s3 import FS, IS_ONE_OF
from s3dal import original_tablename

# =============================================================================
def config(settings):
    """
        BRCMS: Sahana Beneficiary Registry and Case Management System
    """

    T = current.T

    settings.base.system_name = "SAHANA Case Management"
    settings.base.system_name_short = "Sahana BRCMS"

    # PrePopulate data
    settings.base.prepopulate += ("BRCMS",)
    settings.base.prepopulate_demo += ("BRCMS/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "BRCMS"

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True

    # Request Organisation during user registration
    settings.auth.registration_requests_organisation = True
    # Suppress popup-link for creating organisations during user registration
    settings.auth.registration_organisation_link_create = False

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               #"volunteer": T("Volunteer"),
                                               }
    # Don't show alternatives, just default
    settings.auth.registration_link_user_to_default = ["staff"]

    # Assign all new users the STAFF role for their default realm
    settings.auth.registration_roles = {None: ("STAFF",)}

    # Disable password-retrieval feature
    settings.auth.password_retrieval = False

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("DE",)
    #gis_levels = ("L1", "L2", "L3")
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Settings suitable for Housing Units
    # - move into customise fn if also supporting other polygons
    settings.gis.precision = 5
    settings.gis.simplify_tolerance = 0
    settings.gis.bbox_min_size = 0.001
    #settings.gis.bbox_offset = 0.007

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("en", "English"),
       ("de", "German"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.timezone = "Europe/Berlin"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # First day of the week
    settings.L10n.firstDOW = 1
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Finance settings
    settings.fin.currencies = {
        "EUR" : "Euros",
        "GBP" : "Great British Pounds",
        "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "USD"

    # Do not require international phone number format
    settings.msg.require_international_phone_numbers = False

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    #
    settings.security.policy = 7 # Hierarchical Realms

    # Version details on About-page require login
    settings.security.version_info_requires_login = True

    # -------------------------------------------------------------------------
    # General UI settings
    #
    settings.ui.calendar_clear_icon = True

    settings.ui.auto_open_update = True
    #settings.ui.inline_cancel_edit = "submit"

    # Business hours to indicate in organizer (Mo-Fr 08-18)
    settings.ui.organizer_business_hours = {"dow": [1, 2, 3, 4, 5],
                                            "start": "08:00",
                                            "end": "18:00",
                                            }

    # -------------------------------------------------------------------------
    # BR Module Settings
    #
    # Terminology to use when referring to cases (Beneficiary|Client|Case)
    #settings.br.case_terminology = "Beneficiary"

    # Terminology to use when referring to measures of assistance (Counseling|Assistance)
    #settings.br.assistance_terminology = "Counseling"

    # -------------------------------------------------------------------------
    # CMS Module Settings
    #
    settings.cms.hide_index = True

    # -------------------------------------------------------------------------
    # Document settings
    #
    settings.doc.mailmerge_fields = {}

    # -------------------------------------------------------------------------
    # Human Resource Module Settings
    #
    settings.hrm.teams_orgs = True
    settings.hrm.staff_departments = False

    settings.hrm.use_id = False
    settings.hrm.use_address = True
    settings.hrm.use_description = False

    settings.hrm.use_trainings = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_awards = False

    settings.hrm.use_skills = False
    settings.hrm.staff_experience = False
    settings.hrm.vol_experience = False

    # -------------------------------------------------------------------------
    # Organisations Module Settings
    #
    settings.org.sector = True
    # But hide it from the rheader
    settings.org.sector_rheader = False
    settings.org.branches = True
    settings.org.offices_tab = False
    settings.org.country = False

    # -------------------------------------------------------------------------
    # Persons Module Settings
    #
    settings.pr.hide_third_gender = False
    #settings.pr.separate_name_fields = 2
    #settings.pr.name_format= "%(last_name)s, %(first_name)s"

    settings.pr.contacts_tabs = {"all": "Contact Info"}

    # -------------------------------------------------------------------------
    # Realm Rules
    #
    def brcms_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        db = current.db
        s3db = current.s3db

        tablename = original_tablename(table)

        realm_entity = 0

        if tablename == "pr_person":

            # Client records are owned by the organisation
            # the case is assigned to
            ctable = s3db.br_case
            query = (ctable.person_id == row.id) & \
                    (ctable.deleted == False)
            case = db(query).select(ctable.organisation_id,
                                    limitby = (0, 1),
                                    ).first()

            if case and case.organisation_id:
                realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                 case.organisation_id,
                                                 )

        elif tablename in ("br_case_activity",
                           "br_assistance_measure",
                           "br_case_language",
                           "pr_group_membership",
                           "pr_person_details",
                           "pr_person_tag",
                           ):

            # Inherit from person via person_id
            table = s3db.table(tablename)
            ptable = s3db.pr_person
            query = (table._id == row.id) & \
                    (ptable.id == table.person_id)
            person = db(query).select(ptable.realm_entity,
                                      limitby = (0, 1),
                                      ).first()
            if person:
                realm_entity = person.realm_entity

        elif tablename in ("pr_address",
                           "pr_contact",
                           "pr_contact_emergency",
                           "pr_image",
                           ):

            # Inherit from person via PE
            table = s3db.table(tablename)
            ptable = s3db.pr_person
            query = (table._id == row.id) & \
                    (ptable.pe_id == table.pe_id)
            person = db(query).select(ptable.realm_entity,
                                      limitby = (0, 1),
                                      ).first()
            if person:
                realm_entity = person.realm_entity

        # TODO
        #elif tablename in ("br_case_activity_need",
        #                   "br_case_activity_update",
        #                   "br_assistance_measure",
        #                   ):
        #
        #    # Inherit from case activity
        #    table = s3db.table(tablename)
        #    atable = s3db.dvr_case_activity
        #    query = (table._id == row.id) & \
        #            (atable.id == table.case_activity_id)
        #    activity = db(query).select(atable.realm_entity,
        #                                limitby = (0, 1),
        #                                ).first()
        #    if activity:
        #        realm_entity = activity.realm_entity

        elif tablename == "pr_group":

            # No realm-entity for case groups
            table = s3db.pr_group
            query = table._id == row.id
            group = db(query).select(table.group_type,
                                     limitby = (0, 1),
                                     ).first()
            if group and group.group_type == 7:
                realm_entity = None

        elif tablename == "project_task":

            # Inherit the realm entity from the assignee
            assignee_pe_id = row.pe_id
            instance_type = s3db.pr_instance_type(assignee_pe_id)
            if instance_type:
                table = s3db.table(instance_type)
                query = table.pe_id == assignee_pe_id
                assignee = db(query).select(table.realm_entity,
                                            limitby = (0, 1),
                                            ).first()
                if assignee and assignee.realm_entity:
                    realm_entity = assignee.realm_entity

            # If there is no assignee, or the assignee has no
            # realm entity, fall back to the user organisation
            if realm_entity == 0:
                auth = current.auth
                user_org_id = auth.user.organisation_id if auth.user else None
                if user_org_id:
                    realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                     user_org_id,
                                                     )
        return realm_entity

    settings.auth.realm_entity = brcms_realm_entity

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        ("hrm", Storage(
           name_nice = T("Staff"),
           #description = "Human Resources Management",
           restricted = True,
           module_type = 2,
        )),
        ("vol", Storage(
           name_nice = T("Volunteers"),
           #description = "Human Resources Management",
           restricted = True,
           module_type = 2,
        )),
        ("cms", Storage(
         name_nice = T("Content Management"),
        #description = "Content Management System",
         restricted = True,
         module_type = 10,
        )),
        ("doc", Storage(
           name_nice = T("Documents"),
           #description = "A library of digital resources, such as photos, documents and reports",
           restricted = True,
           module_type = 10,
        )),
        ("msg", Storage(
          name_nice = T("Messaging"),
          #description = "Sends & Receives Alerts via Email & SMS",
          restricted = True,
          # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
          module_type = None,
        )),
        #("supply", Storage(
        #   name_nice = T("Supply Chain Management"),
        #   #description = "Used within Inventory Management, Request Management and Asset Management",
        #   restricted = True,
        #   module_type = None, # Not displayed
        #)),
        #("inv", Storage(
        #   name_nice = T("Warehouses"),
        #   #description = "Receiving and Sending Items",
        #   restricted = True,
        #   module_type = 4
        #)),
        #("asset", Storage(
        #   name_nice = T("Assets"),
        #   #description = "Recording and Assigning Assets",
        #   restricted = True,
        #   module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("req", Storage(
        #   name_nice = T("Requests"),
        #   #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("project", Storage(
           name_nice = T("Projects"),
           #description = "Tracking of Projects, Activities and Tasks",
           restricted = True,
           module_type = 2
        )),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        ("br", Storage(
            name_nice = T("Beneficiary Registry"),
            #description = "Beneficiary Registry and Case Management",
            restricted = True,
            module_type = 10,
        )),
        #("dvr", Storage(
        #    name_nice = T("Case Management"),
        #    #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("event", Storage(
        #   name_nice = T("Events"),
        #   #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("security", Storage(
        #   name_nice = T("Security"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("stats", Storage(
           name_nice = T("Statistics"),
           #description = "Manages statistics",
           restricted = True,
           module_type = None,
        )),
    ])

# END =========================================================================
