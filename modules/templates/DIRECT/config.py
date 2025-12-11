"""
    DIRECT: Disaster Response Coordination Tool

    License: MIT
"""

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

# =============================================================================
def config(settings):

    T = current.T

    settings.base.system_name = "Disaster Response Coordination"
    settings.base.system_name_short = "Sahana DIRECT"

    # PrePopulate data
    settings.base.prepopulate += ("DIRECT",)
    settings.base.prepopulate_demo.append("DIRECT/Demo")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "default"
    settings.base.theme_layouts = "DIRECT"

    # Custom XSLT transformation stylesheets
    # settings.base.xml_formats = {"wws": "RLPPTM"}

    # Custom models/controllers
    settings.base.models = "templates.DIRECT.models"
    settings.base.rest_controllers = {}

    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/<theme>/img/logo.png" % current.request.application

    # Authentication settings
    # No self-registration
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do not send standard welcome emails (using custom function)
    settings.auth.registration_welcome_email = False
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = ["staff"]
    # Disable password-retrieval feature
    settings.auth.password_retrieval = True

    settings.auth.realm_entity_types = ("org_group", "org_organisation")
    settings.auth.privileged_roles = {"NEWSLETTER_AUTHOR": "NEWSLETTER_AUTHOR",
                                      }

    settings.auth.password_min_length = 8
    settings.auth.consent_tracking = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("DE",)
    #gis_levels = ("L1", "L2", "L3")
    # Uncomment to display the Map Legend as a floating DIV, so that it is visible on Summary Map
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Use custom geocoder
    # settings.gis.geocode_service = rlp_GeoNames

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("en", "English"),
       # ("si", "සිංහල"),
       # ("ta", "தமிழ்"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.timezone = "Europe/Berlin"
    # Default date/time formats
    settings.L10n.date_format = "%d.%m.%Y"
    settings.L10n.time_format = "%H:%M"
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
    settings.fin.currency_writable = False

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
    settings.security.policy = 7

    # -------------------------------------------------------------------------
    settings.cms.newsletter_recipient_types = ("org_organisation",)

    # -------------------------------------------------------------------------
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    # -------------------------------------------------------------------------
    settings.hrm.record_tab = True
    settings.hrm.staff_experience = False
    settings.hrm.staff_departments = False
    settings.hrm.teams = False
    settings.hrm.use_address = True
    settings.hrm.use_id = False
    settings.hrm.use_skills = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    settings.org.projects_tab = False

    # -------------------------------------------------------------------------
    settings.req.req_type = ("Stock",)
    settings.req.type_inv_label = ("Supply Items")

    settings.req.copyable = False
    settings.req.recurring = False

    settings.req.req_shortname = "BANF"
    settings.req.requester_label = "Orderer"
    settings.req.date_editable = False
    settings.req.status_writable = False

    settings.req.pack_values = False
    settings.req.inline_forms = True
    settings.req.use_commit = False

    settings.req.items_ask_purpose = False
    settings.req.prompt_match = False

    from .customise.req import req_need_controller, \
                               req_need_service_controller

    settings.customise_req_need_controller = req_need_controller
    settings.customise_req_need_service_controller = req_need_service_controller

    # -------------------------------------------------------------------------
    settings.inv.track_pack_values = False
    settings.inv.send_show_org = False

    # -------------------------------------------------------------------------
    settings.supply.catalog_default = "Default"
    settings.supply.catalog_multi = False

    # -------------------------------------------------------------------------
    # UI Settings
    settings.ui.calendar_clear_icon = True

    # -------------------------------------------------------------------------
    # Defaults for custom settings
    #
    settings.custom.context_org_name = "Sahana Eden"

    settings.custom.org_menu_logo = ("default", "img", "eden_small.png")
    settings.custom.homepage_logo = ("default", "img", "eden_large.png")

    # -------------------------------------------------------------------------
    from .customise.auth import realm_entity, \
                                auth_user_resource

    settings.auth.realm_entity = realm_entity

    settings.customise_auth_user_resource = auth_user_resource

    # -------------------------------------------------------------------------
    from .customise.cms import cms_newsletter_resource, \
                               cms_newsletter_controller, \
                               cms_post_resource, \
                               cms_post_controller

    settings.customise_cms_newsletter_resource = cms_newsletter_resource
    settings.customise_cms_newsletter_controller = cms_newsletter_controller
    settings.customise_cms_post_resource = cms_post_resource
    settings.customise_cms_post_controller = cms_post_controller

    # -------------------------------------------------------------------------
    from .customise.doc import doc_document_resource

    settings.customise_doc_document_resource = doc_document_resource

    # -------------------------------------------------------------------------
    from .customise.hrm import hrm_human_resource_resource, \
                               hrm_human_resource_controller

    settings.customise_hrm_human_resource_resource = hrm_human_resource_resource
    settings.customise_hrm_human_resource_controller = hrm_human_resource_controller

    # -------------------------------------------------------------------------
    from .customise.pr import pr_group_controller, \
                              pr_person_controller, \
                              pr_person_resource

    settings.customise_pr_group_controller = pr_group_controller
    settings.customise_pr_person_controller = pr_person_controller
    settings.customise_pr_person_resource = pr_person_resource

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None, # This item is not shown in the menu
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
            module_type = None, # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None, # No Menu
        )),
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10,
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1,
        )),
        # HRM is required for access to default realm permissions
        ("hrm", Storage(
            name_nice = T("Staff"),
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
        ("asset", Storage(
            name_nice = T("Assets"),
            #description = "Recording and Assigning Assets",
            restricted = True,
            module_type = 5,
        )),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        ("dvr", Storage(
            name_nice = T("Clients"),
            restricted = True,
            module_type = 10,
        )),
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            module_type = 10,
        )),
        ("inv", Storage(
            name_nice = T("Warehouses"),
            #description = "Receiving and Sending Items",
            module_type = 4
        )),
        ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            module_type = None, # Not displayed
        )),
        ("water", Storage(
            name_nice = T("Water Sources Monitoring"),
            #description = "Used to monitor and sanitize drinking water sources",
            module_type = None, # Not displayed
        )),
    ])

# END =========================================================================
