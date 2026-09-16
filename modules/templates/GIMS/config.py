"""
    GIMS Refugee Information Management System

    License: MIT
"""

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

from templates.RLPPTM.rlpgeonames import rlp_GeoNames

# Default/lead organisation
MDI = "Ministerium des Innern, für Integration und Verkehr"

# Org Groups
DISTRICTS = "Kreisverwaltung"
COMMUNES = "Kommunale Verwaltung"
AFAS = "AfA"

# =============================================================================
def config(settings):

    T = current.T

    settings.base.system_name = "Geflüchteten-Informations-Management"
    settings.base.system_name_short =  "GIMS"
    settings.custom.homepage_title = "Geflüchteten-Informations-Management"

    # PrePopulate data
    settings.base.prepopulate.append("GIMS")
    settings.base.prepopulate_demo.append("GIMS/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "RLP"
    settings.base.theme_layouts = "GIMS"

    # Custom models/controllers
    settings.base.models = "templates.GIMS.models"
    settings.base.rest_controllers = {
        ("cr", "reception_center_type"): ("cr", "reception_center_type"),
        ("cr", "reception_center"): ("cr", "reception_center"),
        ("cr", "reception_center_status"): ("cr", "reception_center_status"),
        }

    # Authentication settings
    settings.auth.password_min_length = 8
    settings.auth.consent_tracking = True
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
    settings.gis.countries = ("DE",)
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
    # Use custom geocoder
    settings.gis.geocode_service = rlp_GeoNames

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("de", "German"),
       ("en", "English"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "de"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.timezone = "Europe/Berlin"
    # Default date/time formats
    settings.L10n.date_format = "%d.%m.%Y"
    settings.L10n.time_format = "%H:%M"
    # First day of the week
    settings.L10n.firstDOW = 1
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = " "
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Finance settings
    settings.fin.currencies = {
        "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #    "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "EUR"

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
    settings.security.policy = 7 # Hierarchical Realms

    # Version details on About-page require login
    settings.security.version_info_requires_login = True

    # -------------------------------------------------------------------------
    # General UI settings
    #
    settings.ui.menu_logo = URL(c="static", f="themes", args=["RLP", "img", "logo_rlp.png"])

    settings.ui.calendar_clear_icon = True

    #settings.ui.inline_cancel_edit = "submit"

    # Business hours to indicate in organizer (Mo-Fr 08-18)
    settings.ui.organizer_business_hours = {"dow": [1, 2, 3, 4, 5],
                                            "start": "08:00",
                                            "end": "18:00",
                                            }

    # -------------------------------------------------------------------------
    # AUTH Settings
    #
    # Do not send standard welcome emails (using custom function)
    settings.auth.registration_welcome_email = False

    settings.auth.realm_entity_types = ("org_group", "org_organisation")
    settings.auth.privileged_roles = {"MAP_ADMIN": "ADMIN",
                                      "SHELTER_MANAGER": "SHELTER_MANAGER",
                                      "SHELTER_READER": "SHELTER_READER",
                                      "NEWSLETTER_AUTHOR": "NEWSLETTER_AUTHOR",
                                      "AFA_COORDINATOR": "AFA_COORDINATOR",
                                      "AFA_MANAGER": "AFA_MANAGER",
                                      "AFA_READER": "AFA_READER",
                                      }

    from .customise.auth import realm_entity, \
                                assign_role, \
                                remove_role

    settings.auth.realm_entity = realm_entity

    settings.auth.add_role = assign_role
    settings.auth.remove_role = remove_role

    # -------------------------------------------------------------------------
    # CMS Module Settings
    #
    settings.cms.hide_index = {"default": False, "_default": True}
    settings.cms.newsletter_recipient_types = ("org_organisation",)

    from .customise.cms import cms_newsletter_resource, \
                               cms_newsletter_controller, \
                               cms_post_resource, \
                               cms_post_controller

    settings.customise_cms_newsletter_resource = cms_newsletter_resource
    settings.customise_cms_newsletter_controller = cms_newsletter_controller

    settings.customise_cms_post_resource = cms_post_resource
    settings.customise_cms_post_controller = cms_post_controller

    # -------------------------------------------------------------------------
    # CR Settings
    #
    settings.cr.shelter_registration = False
    settings.cr.shelter_units = False
    settings.cr.shelter_population_by_type = True
    settings.cr.shelter_population_by_age_group = True

    from .customise.cr import cr_shelter_resource, \
                              cr_shelter_controller, \
                              cr_shelter_population_resource, \
                              cr_shelter_population_controller, \
                              cr_shelter_status_resource, \
                              cr_reception_center_resource, \
                              cr_reception_center_controller, \
                              cr_reception_center_type_controller

    settings.customise_cr_shelter_resource = cr_shelter_resource
    settings.customise_cr_shelter_controller = cr_shelter_controller
    settings.customise_cr_shelter_population_resource = cr_shelter_population_resource
    settings.customise_cr_shelter_population_controller = cr_shelter_population_controller
    settings.customise_cr_shelter_status_resource = cr_shelter_status_resource

    settings.customise_cr_reception_center_resource = cr_reception_center_resource
    settings.customise_cr_reception_center_controller = cr_reception_center_controller
    settings.customise_cr_reception_center_type_controller = cr_reception_center_type_controller

    # -------------------------------------------------------------------------
    # Document settings
    #
    settings.doc.mailmerge_fields = {}

    from .customise.doc import doc_image_resource

    settings.customise_doc_image_resource = doc_image_resource

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

    settings.hrm.record_tab = False
    settings.hrm.staff_experience = False
    settings.hrm.teams = False
    settings.hrm.use_address = False
    settings.hrm.use_id = False
    settings.hrm.use_skills = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    # ORG Settings
    #
    settings.org.default_organisation = MDI

    settings.org.sector = True
    settings.org.sector_rheader = False

    settings.org.branches = True
    settings.org.offices_tab = False
    settings.org.country = False

    from .customise.org import org_organisation_resource, \
                               org_organisation_controller

    settings.customise_org_organisation_resource = org_organisation_resource
    settings.customise_org_organisation_controller = org_organisation_controller

    # -------------------------------------------------------------------------
    # Persons Module Settings
    #
    settings.pr.hide_third_gender = False

    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    settings.pr.contacts_tabs = {"all": "Contact Info"}

    from .customise.pr import pr_person_resource, \
                              pr_person_controller

    settings.customise_pr_person_resource = pr_person_resource
    settings.customise_pr_person_controller = pr_person_controller

    # -------------------------------------------------------------------------
    # UI Settings
    #
    settings.ui.calendar_clear_icon = True

    settings.ui.custom_icons = {"shelter": "fa-bed",
                                "_base": "fa",
                                }

    # -------------------------------------------------------------------------
    # Defaults for custom settings
    #
    settings.custom.org_registration = True
    settings.custom.regional = ("Rheinland-Pfalz",
                                )

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
        #("vol", Storage(
        #   name_nice = T("Volunteers"),
        #   #description = "Human Resources Management",
        #   restricted = True,
        #   module_type = 2,
        #)),
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
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        ("stats", Storage(
           name_nice = T("Statistics"),
           #description = "Manages statistics",
           restricted = True,
           module_type = None,
        )),
    ])

# END =========================================================================
