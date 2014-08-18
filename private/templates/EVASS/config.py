# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage
from gluon.validators import IS_NOT_EMPTY, IS_EMPTY_OR, IS_IN_SET

from s3 import s3_date, S3Represent

T = current.T
settings = current.deployment_settings

"""
    Settings for the EVASS template:
        http://eden.sahanafoundation.org/wiki/Deployments/Italy/EVASS
"""

# Pre-Populate
settings.base.prepopulate = ["EVASS", "demo/users"]

settings.base.system_name = T("EVASS - Sahana Eden for Italy")
settings.base.system_name_short = T("Sahana Eden for Italy")

# Use system_name_short as default email subject (Appended).
settings.mail.default_email_subject = True
# Append name and surname of logged in user to email subject
settings.mail.auth_user_in_email_subject = True

# Theme (folder to use for views/layout.html)
settings.base.theme = "EVASS"
settings.ui.formstyle = "foundation"
settings.ui.filter_formstyle = "foundation_inline"

# Authentication settings
# Always notify the approver of a new (verified) user, even if the user is automatically approved
settings.auth.always_notify_approver = False

# The name of the teams that users are added to when they opt-in to receive alerts
#settings.auth.opt_in_team_list = ["Updates"]
# Should users be allowed to register themselves?
#settings.security.self_registration = False
# Uncomment this to set the opt in default to True
#settings.auth.opt_in_default = True
# Uncomment this to request the Mobile Phone when a user registers
settings.auth.registration_requests_mobile_phone = True
# Uncomment this to have the Mobile Phone selection during registration be mandatory
settings.auth.registration_mobile_phone_mandatory = True
# Uncomment this to request the Organisation when a user registers
#settings.auth.registration_requests_organisation = True
# Uncomment this to have the Organisation selection during registration be mandatory
#settings.auth.registration_organisation_required = True
# Uncomment this to have the Organisation input hidden unless the user enters a non-whitelisted domain
#settings.auth.registration_organisation_hidden = True
# Uncomment this to default the Organisation during registration
#settings.auth.registration_organisation_default = "My Organisation"
# Uncomment this to request the Organisation Group when a user registers
#settings.auth.registration_requests_organisation_group = True
# Uncomment this to have the Organisation Group selection during registration be mandatory
#settings.auth.registration_organisation_group_required = True
# Uncomment this to request the Site when a user registers
#settings.auth.registration_requests_site = True
# Uncomment this to allow Admin to see Organisations in user Admin even if the Registration doesn't request this
#settings.auth.admin_sees_organisation = True
# Uncomment to set the default role UUIDs assigned to newly-registered users
# This is a dictionary of lists, where the key is the realm that the list of roles applies to
# The key 0 implies not realm restricted
# The keys "organisation_id" and "site_id" can be used to indicate the user's "organisation_id" and "site_id"
#settings.auth.registration_roles = { 0: ["STAFF", "PROJECT_EDIT"]}
# Uncomment this to enable record approval
#settings.auth.record_approval = True
# Uncomment this and specify a list of tablenames for which record approval is required
#settings.auth.record_approval_required_for = ["project_project"]
# Uncomment this to request an image when users register
#settings.auth.registration_requests_image = True
# Uncomment this to direct newly-registered users to their volunteer page to be able to add extra details
# NB This requires Verification/Approval to be Off
# @ToDo: Extend to all optional Profile settings: Homepage, Twitter, Facebook, Mobile Phone, Image
#settings.auth.registration_volunteer = True

# Terms of Service to be able to Register on the system
# uses <template>/views/tos.html
settings.auth.terms_of_service = True

# L10n settings
# Languages used in the deployment (used for Language Toolbar & GIS Locations)
# http://www.loc.gov/standards/iso639-2/php/code_list.php
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("it", "Italiano"),
])
# Default language for Language Toolbar (& GIS Locations in future)
settings.L10n.default_language = "en"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0100"
# Uncomment these to use US-style dates in English (localisations can still convert to local format)
#settings.L10n.time_format = T("%H:%M:%S")
settings.L10n.date_format = T("%d/%m/%Y")
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = ","
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = "."
# Default Country Code for telephone numbers
settings.L10n.default_country_code = +39
# Make last name in person/user records mandatory
settings.L10n.mandatory_lastname = True
# Uncomment this to Translate Layer Names
#settings.L10n.translate_gis_layer = True
# Uncomment this to Translate Location Names
settings.L10n.translate_gis_location = True

# Finance settings
settings.fin.currency_default = "EUR"
settings.fin.currencies = {
    "EUR": T("Euros"),
    "GBP": T("Great British Pounds"),
    "USD": T("United States Dollars"),
}

# GIS (Map) settings
# GeoNames username
settings.gis.geonames_username = "evass"
# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ["IT"]

# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"
# Hide unnecessary Toolbar items
settings.gis.nav_controls = False

# AAA Settings

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
settings.security.policy = 7

# Ownership-rule for records without owner:
# True = not owned by any user (strict ownership, default)
# False = owned by any authenticated user
#settings.security.strict_ownership = False

# -----------------------------------------------------------------------------
# Shelters
# Uncomment to use a dynamic population estimation by calculations based on registrations  
settings.cr.shelter_population_dynamic = True
# Uncomment to activate the housing units management. 
settings.cr.shelter_housing_unit_management = True

# -----------------------------------------------------------------------------

# Events
# Make Event Types Hierarchical
#settings.event.types_hierarchical = True

# -----------------------------------------------------------------------------
# Evacuees
# Group Types
#settings.evr.group_types = {1: T("other"),
#                            2: T("Family"),
#                            3: T("Tourist group"),
#                            4: T("Society"),
#                            5: T("Company"),
#                            6: T("Convent"),
#                            7: T("Hotel"),
#                            8: T("Hospital"),
#                            9: T("Orphanage")
#                            }
# Uncomment to hide evacuees physical description in Evacuees page
settings.evr.physical_description = False
# Uncomment to hide Emergency Contacts in Person Contacts page
settings.pr.show_emergency_contacts = False
# Uncomment to link evacuees to Organisations
settings.evr.link_to_organisation= True
# -----------------------------------------------------------------------------
# Organisations
# Enable the use of Organisation Branches
settings.org.branches = True
# Show branches as tree rather than as table
#settings.org.branches_tree_view = True
# Enable the use of Organisation Groups & what their name is
#settings.org.groups = "Coalition"
# Make Facility Types Hierarchical
settings.org.facility_types_hierarchical = True

# Theme for the S3HierarchyWidget (folder in static/styles/jstree or relative to application)
settings.ui.hierarchy_theme = "default"

# -----------------------------------------------------------------------------
# Human Resource Management
# Uncomment to allow Staff & Volunteers to be registered without an email address
settings.hrm.email_required = False
# Uncomment to allow Staff & Volunteers to be registered without an Organisation
settings.hrm.org_required = False
# Uncomment to allow HR records to be deletable rather than just marking them as obsolete
settings.hrm.deletable = True
# Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
#settings.hrm.filter_certificates = True
# Uncomment to allow HRs to have multiple Job Titles
settings.hrm.multiple_job_titles = True
# Uncomment to have each root Org use a different Job Title Catalog
#settings.hrm.org_dependent_job_titles = True
# Uncomment to hide the Staff resource
#settings.hrm.show_staff = False
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to enable Volunteer 'active' field
# - can also be made a function which is called to calculate the status based on recorded hours
settings.hrm.vol_active = True
# Uncomment to define a Tooltip to show when viewing the Volunteer 'active' field
#settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
# Uncomment to disable Volunteer experience
settings.hrm.vol_experience = False
# Uncomment to show the Organisation name in HR represents
#settings.hrm.show_organisation = True
# Uncomment to disable the use of Volunteer Awards
settings.hrm.use_awards = False
# Uncomment to disable the use of HR Certificates
settings.hrm.use_certificates = False
# Uncomment to enable the use of Staff/Volunteer IDs
#settings.hrm.use_code = True
# Uncomment to disable the use of HR Credentials
#settings.hrm.use_credentials = False
# Uncomment to disable the use of HR Description
#settings.hrm.use_description = False
# Uncomment to disable the use of HR ID
#settings.hrm.use_id = False
# Uncomment to disable the use of HR Skills
settings.hrm.use_skills = False
# Uncomment to disable the use of HR Trainings
settings.hrm.use_trainings = False

#*****************************Frontpage settings*************************
# RSS feeds
settings.frontpage.rss = [
    {"title": "RSS News - Dipartimento della Protezione Civile ",
     "url": "http://www.protezionecivile.gov.it/jcms/do/jprss/Rss/Feed/show.action?id=12170&lang=it#"
    },
    {"title": "RSS Vigilanza Meteo - Dipartimento della Protezione Civile ",
     "url": "http://www.protezionecivile.gov.it/jcms/do/jprss/Rss/Feed/show.action?id=23573&lang=it#"
    },
    {"title": "RSS Previsioni Meteo - Dipartimento della Protezione Civile ",
     "url": "http://www.protezionecivile.gov.it/jcms/do/jprss/Rss/Feed/show.action?id=23575&lang=it#"
    },
    {"title": "RSS Comunicati Stampa - Dipartimento della Protezione Civile ",
     "url": "http://www.protezionecivile.gov.it/jcms/do/jprss/Rss/Feed/show.action?id=23577&lang=it#"
    },
    {"title": "Twitter - Croce Rossa Italia",
     # @crocerossa
     #"url": "https://search.twitter.com/search.rss?q=from%3Acrocerossa" # API v1 deprecated, so doesn't work, need to use 3rd-party service, like:
     "url": "http://www.rssitfor.me/getrss?name=@crocerossa"
     # Hashtag
     #url: "http://search.twitter.com/search.atom?q=%23eqnz" # API v1 deprecated, so doesn't work, need to use 3rd-party service, like:
     #"url": "http://api2.socialmention.com/search?q=protezionecivile&t=all&f=rss"
    },
#    {"title": "Twitter - Dipartimento della Protezione Civile",
#     # @protezionecivile
#     "url": "http://www.rssitfor.me/getrss?name=@protezionecivile"
#     # Hashtag
#     #url: "http://search.twitter.com/search.atom?q=%23eqnz" # API v1 deprecated, so doesn't work, need to use 3rd-party service, like:
#     "url": "http://api2.socialmention.com/search?q=protezionecivile&t=all&f=rss"
#    }
]
# -----------------------------------------------------------------------------
def customise_pr_person_resource(r, tablename):

    s3db = current.s3db
    table = r.resource.table

    # Disallow "unknown" gender and defaults to "male"
    evr_gender_opts = dict((k, v) for k, v in s3db.pr_gender_opts.items()
                                  if k in (2, 3))
    gender = table.gender
    gender.requires = IS_IN_SET(evr_gender_opts, zero=None)
    gender.default = 3

    if r.controller == "evr":
        # Hide evacuees emergency contacts
        settings.pr.show_emergency_contacts = False

        # Last name and date of birth mandatory in EVR module
        table.last_name.requires = IS_NOT_EMPTY(error_message = T("Please enter a last name"))
        
        dob_requires = s3_date("dob",
                               future = 0,
                               past = 1320,
                               empty = False).requires
        dob_requires.error_message = T("Please enter a date of birth")
        table.date_of_birth.requires = dob_requires

            # Enable Location_id
        from gluon import DIV
        from s3.s3widgets import S3LocationSelectorWidget2
        levels = ("L1","L2","L3",)
        location_id = table.location_id
        location_id.readable = location_id.writable = True
        location_id.label = T("Place of Birth")
        location_id.widget = S3LocationSelectorWidget2(levels=levels,
                                                       lines=True,
                                                       )
        location_id.represent = s3db.gis_LocationRepresent(sep=" | ")
            # Enable place of birth
        place_of_birth = s3db.pr_person_details.place_of_birth
        place_of_birth.label = "Specify a Different Place of Birth"
        place_of_birth.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (T("Different Place of Birth"),
                                                      T("Specify a different place of birth (foreign country, village, hamlet)")))
        place_of_birth.readable = place_of_birth.writable = True
            
            # Disable religion selection
        s3db.pr_person_details.religion.readable = False
        s3db.pr_person_details.religion.writable = False
        
    # Disable unneeded physical details
    pdtable = s3db.pr_physical_description
    hide_fields = [
        "race",
        "complexion",
        "height",
        "weight",
        "hair_length",
        "hair_style",
        "hair_baldness",
        "hair_comment",
        "facial_hair_type",
        "facial_hair_length",
        "facial_hair_color",
        "facial_hair_comment",
        "body_hair",
        "skin_marks",
        "medical_conditions"
    ]
    for fname in hide_fields:
        field = pdtable[fname]
        field.readable = field.writable = False

    # This set is suitable for Italy
    ethnicity_opts = ("Italian",
                      "Chinese",
                      "Albanese",
                      "Philippine",
                      "Pakistani",
                      "English",
                      "African",
                      "Other",
                      "Unknown",
                      )
    ethnicity_opts = dict((v, T(v)) for v in ethnicity_opts)

    ethnicity = pdtable.ethnicity
    ethnicity.requires = IS_EMPTY_OR(IS_IN_SET(ethnicity_opts,
                                               sort=True))
    ethnicity.represent = S3Represent(options=ethnicity_opts,
                                      translate=True)

settings.customise_pr_person_resource = customise_pr_person_resource

def customise_cr_shelter_resource(r, tablename):
    
    s3db = current.s3db
    s3db.cr_shelter.capacity_day.writable = s3db.cr_shelter.capacity_night.writable = False 
    s3db.cr_shelter.cr_shelter_environment_id.readable = s3db.cr_shelter.cr_shelter_environment_id.writable = True
    
settings.customise_cr_shelter_resource = customise_cr_shelter_resource

def customise_pr_group_resource(r, tablename):
    
    messages = current.messages
    field = r.table.group_type
    pr_group_types = {1 : T("Family"),
                      2 : T("Tourist Group"),
                      3 : T("Relief Team"),
                      4 : T("other"),
                      5 : T("Mailing Lists"),
                      6 : T("Society"),
                      }
    field.represent = lambda opt: pr_group_types.get(opt, messages.UNKNOWN_OPT)
    field.requires = IS_IN_SET(pr_group_types, zero=None)

settings.customise_pr_group_resource = customise_pr_group_resource

# -----------------------------------------------------------------------------
def customise_event_event_resource(r, tablename):

    table = r.table
    table.exercise.default = True
    table.organisation_id.readable = table.organisation_id.writable = True
        
settings.customise_event_event_resource = customise_event_event_resource

def customise_event_incident_resource(r, tablename):

    table = r.table
    table.exercise.default = True
    table.event_id.readable = table.event_id.writable = True
        
settings.customise_event_incident_resource = customise_event_incident_resource
# -----------------------------------------------------------------------------
def customise_project_location_resource(r, tablename):

    field = current.s3db.project_location.status_id
    field.readable = field.writable = True

settings.customise_project_location_resource = customise_project_location_resource

# -----------------------------------------------------------------------------
# Comment/uncomment modules here to disable/enable them
# @ToDo: Have the system automatically enable migrate if a module is enabled
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
    ("sync", Storage(
        name_nice = T("Synchronization"),
        #description = "Synchronization",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        module_type = None  # This item is handled separately for the menu
    )),
    ("translate", Storage(
        name_nice = T("Translation Functionality"),
        #description = "Selective translation of strings based on module.",
        module_type = None,
    )),
    ("gis", Storage(
        name_nice = T("Map"),
        #description = "Situation Awareness & Geospatial Analysis",
        restricted = True,
        module_type = 1,     # 6th item in the menu
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
        module_type = 10
    )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
        name_nice = T("Staff"),
        #description = "Human Resources Management",
        restricted = True,
        module_type = 10,
    )),
    ("vol", Storage(
        name_nice = T("Volunteers"),
        #description = "Human Resources Management",
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
        module_type = 2,
    )),
    ("cr", Storage(
        name_nice = T("Shelters"),
        #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        restricted = True,
        module_type = 10
    )),
    ("evr", Storage(
         name_nice = T("Evacuees"),
         #description = "Evacuees Registry",
         restricted = True, # use Access Control Lists to see this module
         module_type = 7
    )),
    ("event", Storage(
        name_nice = T("Events"),
        #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        restricted = True,
        module_type = 10,
    )),
])
