"""
    RLPPTM: Template for Rhineland-Palatinate (RLP) COVID-19 Test Stations Portal

    License: MIT
"""

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

from .rlpgeonames import rlp_GeoNames

LSJV = "Landesamt für Soziales, Jugend und Versorgung"
SCHOOLS = "Schulen"
TESTSTATIONS = "COVID-19 Teststellen"
GOVERNMENT = "Regierungsstellen"

# =============================================================================
def config(settings):

    T = current.T

    purpose = {"disease": "COVID-19"}
    settings.base.system_name = T("%(disease)s Test Stations") % purpose
    settings.base.system_name_short = T("%(disease)s Test Stations") % purpose

    # PrePopulate data
    settings.base.prepopulate += ("RLPPTM",)
    settings.base.prepopulate_demo.append("RLPPTM/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "RLP"
    settings.base.theme_layouts = "RLPPTM"

    # Custom XSLT transformation stylesheets
    settings.base.xml_formats = {"wws": "RLPPTM"}

    # Custom models/controllers
    settings.base.models = "templates.RLPPTM.models"
    settings.base.rest_controllers = {("disease", "daycare_testing"): ("disease", "daycare_testing"),
                                      ("audit", "organisation"): ("org", "organisation"),
                                      ("org", "provider"): ("org", "organisation"),
                                      }

    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/<templatename>/img/logo.png" % current.request.application

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
    settings.auth.privileged_roles = {"DISEASE_TEST_READER": "ORG_GROUP_ADMIN",
                                      "PROGRAM_ACCOUNTANT": "PROGRAM_ACCOUNTANT",
                                      "PROGRAM_MANAGER": "ORG_GROUP_ADMIN",
                                      "PROVIDER_ACCOUNTANT": "PROVIDER_ACCOUNTANT",
                                      "SUPPLY_COORDINATOR": "SUPPLY_COORDINATOR",
                                      "VOUCHER_ISSUER": "VOUCHER_ISSUER",
                                      "VOUCHER_PROVIDER": "VOUCHER_PROVIDER",
                                      "TEST_PROVIDER": "TEST_PROVIDER",
                                      "NEWSLETTER_AUTHOR": "NEWSLETTER_AUTHOR",
                                      "AUDITOR": "ADMIN",
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
    settings.cms.newsletter_recipient_types = ("org_organisation", "org_facility")

    # -------------------------------------------------------------------------
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    settings.pr.availability_json_rules = True

    # -------------------------------------------------------------------------
    settings.disease.testing_report_by_demographic = True

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
    settings.org.default_organisation = LSJV

    # -------------------------------------------------------------------------
    settings.project.multiple_organisations = True

    # -------------------------------------------------------------------------
    settings.fin.voucher_personalize = "dob"
    settings.fin.voucher_eligibility_types = True
    settings.fin.voucher_invoice_status_labels = {"VERIFIED": None,
                                                  "APPROVED": None,
                                                  "PAID": "Payment Ordered",
                                                  }
    settings.fin.voucher_claim_paid_label = "Payment Ordered"

    # -------------------------------------------------------------------------
    settings.req.req_type = ("Stock",)
    settings.req.type_inv_label = ("Equipment")

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

    # -------------------------------------------------------------------------
    settings.inv.track_pack_values = False
    settings.inv.send_show_org = False

    # -------------------------------------------------------------------------
    settings.supply.catalog_default = "Material für Teststellen"
    settings.supply.catalog_multi = False

    # -------------------------------------------------------------------------
    # UI Settings
    settings.ui.calendar_clear_icon = True

    # -------------------------------------------------------------------------
    # Custom settings
    settings.custom.test_station_registration = True
    settings.custom.test_station_cleanup = True

    settings.custom.daycare_testing_data = False
    settings.custom.daycare_testing_inquiry = False

    # -------------------------------------------------------------------------
    def poll_dcc():
        """
            Scheduler task to poll for DCC requests
        """

        from .dcc import DCC
        return DCC.poll()

    settings.tasks.poll_dcc = poll_dcc

    # -------------------------------------------------------------------------
    from .customise.auth import rlpptm_realm_entity, \
                                consent_check, \
                                pending_response, \
                                auth_consent_resource, \
                                auth_user_resource

    settings.auth.realm_entity = rlpptm_realm_entity
    settings.auth.consent_check = consent_check
    settings.auth.mandatory_page = pending_response

    settings.customise_auth_consent_resource = auth_consent_resource
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
    from .customise.disease import disease_case_diagnostics_resource, \
                                   disease_case_diagnostics_controller, \
                                   disease_testing_device_resource, \
                                   disease_testing_report_resource, \
                                   disease_testing_report_controller, \
                                   disease_testing_demographic_resource, \
                                   disease_testing_demographic_controller, \
                                   disease_daycare_testing_controller

    settings.customise_disease_case_diagnostics_resource = disease_case_diagnostics_resource
    settings.customise_disease_case_diagnostics_controller = disease_case_diagnostics_controller
    settings.customise_disease_testing_device_resource = disease_testing_device_resource
    settings.customise_disease_testing_report_resource = disease_testing_report_resource
    settings.customise_disease_testing_report_controller = disease_testing_report_controller
    settings.customise_disease_testing_demographic_resource = disease_testing_demographic_resource
    settings.customise_disease_testing_demographic_controller = disease_testing_demographic_controller
    settings.customise_disease_daycare_testing_controller = disease_daycare_testing_controller

    # -------------------------------------------------------------------------
    from .customise.doc import doc_document_resource

    settings.customise_doc_document_resource = doc_document_resource

    # -------------------------------------------------------------------------
    from .customise.fin import fin_voucher_resource, \
                               fin_voucher_controller, \
                               fin_voucher_debit_resource, \
                               fin_voucher_debit_controller, \
                               fin_voucher_program_resource, \
                               fin_voucher_program_controller, \
                               fin_voucher_billing_resource, \
                               fin_voucher_claim_resource, \
                               fin_voucher_claim_controller, \
                               fin_voucher_invoice_resource, \
                               fin_voucher_invoice_controller

    settings.customise_fin_voucher_resource = fin_voucher_resource
    settings.customise_fin_voucher_controller = fin_voucher_controller
    settings.customise_fin_voucher_debit_resource = fin_voucher_debit_resource
    settings.customise_fin_voucher_debit_controller = fin_voucher_debit_controller
    settings.customise_fin_voucher_program_resource = fin_voucher_program_resource
    settings.customise_fin_voucher_program_controller = fin_voucher_program_controller
    settings.customise_fin_voucher_billing_resource = fin_voucher_billing_resource
    settings.customise_fin_voucher_claim_resource = fin_voucher_claim_resource
    settings.customise_fin_voucher_claim_controller = fin_voucher_claim_controller
    settings.customise_fin_voucher_invoice_resource = fin_voucher_invoice_resource
    settings.customise_fin_voucher_invoice_controller = fin_voucher_invoice_controller

    # -------------------------------------------------------------------------
    from .customise.hrm import hrm_human_resource_resource, \
                               hrm_human_resource_controller

    settings.customise_hrm_human_resource_resource = hrm_human_resource_resource
    settings.customise_hrm_human_resource_controller = hrm_human_resource_controller

    # -------------------------------------------------------------------------
    from .customise.inv import inv_recv_resource, \
                               inv_recv_controller, \
                               inv_send_resource, \
                               inv_send_controller, \
                               inv_track_item_resource, \
                               inv_warehouse_resource, \
                               inv_warehouse_controller

    settings.customise_inv_recv_resource = inv_recv_resource
    settings.customise_inv_recv_controller = inv_recv_controller
    settings.customise_inv_send_resource = inv_send_resource
    settings.customise_inv_send_controller = inv_send_controller
    settings.customise_inv_track_item_resource = inv_track_item_resource
    settings.customise_inv_warehouse_resource = inv_warehouse_resource
    settings.customise_inv_warehouse_controller = inv_warehouse_controller

    # -------------------------------------------------------------------------
    from .customise.org import org_organisation_resource, \
                               org_organisation_controller, \
                               org_organisation_type_resource, \
                               org_facility_resource, \
                               org_facility_controller

    settings.customise_org_organisation_resource = org_organisation_resource
    settings.customise_org_organisation_controller = org_organisation_controller
    settings.customise_org_organisation_type_resource = org_organisation_type_resource
    settings.customise_org_facility_resource = org_facility_resource
    settings.customise_org_facility_controller = org_facility_controller

    # -------------------------------------------------------------------------
    from .customise.pr import pr_address_resource, \
                              pr_contact_resource, \
                              pr_person_controller, \
                              pr_person_resource

    settings.customise_pr_address_resource = pr_address_resource
    settings.customise_pr_contact_resource = pr_contact_resource

    settings.customise_pr_person_controller = pr_person_controller
    settings.customise_pr_person_resource = pr_person_resource

    # -------------------------------------------------------------------------
    from .customise.project import project_project_resource, \
                                   project_project_controller

    settings.customise_project_project_resource = project_project_resource
    settings.customise_project_project_controller = project_project_controller

    # -------------------------------------------------------------------------
    from .customise.req import req_req_resource, \
                               req_req_controller, \
                               req_req_item_resource

    settings.customise_req_req_resource = req_req_resource
    settings.customise_req_req_controller = req_req_controller
    settings.customise_req_req_item_resource = req_req_item_resource

    # -------------------------------------------------------------------------
    from .customise.supply import supply_item_resource, \
                                  supply_item_controller, \
                                  shipping_code

    settings.customise_supply_item_resource = supply_item_resource
    settings.customise_supply_item_controller = supply_item_controller
    settings.supply.shipping_code = shipping_code

    settings.L10n.units_of_measure = {"btl": T("Bottle##unit"),
                                      "pkt": T("Packet##unit"),
                                      "pc": T("piece##unit"),
                                      }

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
        ("audit", Storage(
            name_nice = T("Organizations"),
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
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            module_type = None,
        )),
        ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = None,
        )),
        ("fin", Storage(
            name_nice = T("Finance"),
            #description = "Finance Management / Accounting",
            restricted = True,
            module_type = None,
        )),
        ("disease", Storage(
            name_nice = T("Disease Tracking"),
            #description = "Helps to track cases and trace contacts in disease outbreaks",
            restricted = True,
            module_type = None,
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
        ("jnl", Storage(
            name_nice = T("Management Journal"),
            module_type = None,
        )),
    ])

# END =========================================================================
