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
# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ("EVASS", "default/users")

settings.base.system_name = T("EVASS - Sahana Eden for Italy")
settings.base.system_name_short = T("Sahana Eden for Italy")

# Theme (folder to use for views/layout.html)
settings.base.theme = "EVASS"
#settings.ui.formstyle = "foundation"
#settings.ui.filter_formstyle = "foundation_inline"

# -----------------------------------------------------------------------------
# Email settings
settings.mail.default_email_subject = True
settings.mail.auth_user_in_email_subject = True

# -----------------------------------------------------------------------------
# Authentication settings
settings.auth.registration_requests_mobile_phone = True
settings.auth.registration_mobile_phone_mandatory = True
settings.auth.registration_requests_organisation = True
# Uncomment this to have the Organisation selection during registration be mandatory
#settings.auth.registration_organisation_required = True
settings.auth.always_notify_approver = False
settings.security.self_registration = False

# Security Policy
# http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
settings.security.policy = 7

def evass_realm_entity(table, row):
    """
        Assign a Realm Entity to records
    """

    db = current.db
    s3db = current.s3db
    tablename = table._tablename

    realm_entity = None
    # Realm is the organization assigned during the record registration/update
    if tablename in ("event_event",
                     "evr_case",
                     "cr_shelter",
                     "hrm_human_resource",
                     "org_facility",
                     "org_office",
                     ):
        otable = s3db.org_organisation
        organisation_id = row.organisation_id
        if organisation_id:
            org = db(otable.id == organisation_id).select(otable.realm_entity,
                                                          limitby=(0, 1)).first()
            realm_entity = org.realm_entity

    elif tablename == "event_incident":
        # Incident realm is the related event realm
        # (assigned during incident registration/update
        etable = db.event_event
        try:
            incident_id = row.id
            query = (table.id == incident_id) & \
                    (etable.id == table.event_id)
            event = db(query).select(etable.realm_entity,
                                     limitby=(0, 1)).first()
            realm_entity = event.realm_entity
        except:
            return

    elif tablename == "pr_group":
    # Group realm is the user's organisation
        user = current.auth.user
        if user:
            realm_entity = s3db.pr_get_pe_id("org_organisation",
                                             user.organisation_id)
    elif tablename == "org_organisation":
        realm_entity = row.pe_id

    return realm_entity

settings.auth.realm_entity = evass_realm_entity

# -----------------------------------------------------------------------------
# L10n settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("it", "Italiano"),
])
settings.L10n.default_language = "en"
settings.L10n.utc_offset = "UTC +0100"
settings.L10n.date_format = T("%d/%m/%Y")
settings.L10n.decimal_separator = ","
settings.L10n.thousands_separator = "."
settings.L10n.default_country_code = 39
settings.L10n.mandatory_lastname = True
settings.L10n.translate_gis_location = True

# Finance settings
settings.fin.currency_default = "EUR"
settings.fin.currencies = {
    "EUR": T("Euros"),
    "GBP": T("Great British Pounds"),
    "USD": T("United States Dollars"),
}

# -----------------------------------------------------------------------------
# GIS (Map) settings
# GeoNames username
settings.gis.geonames_username = "geoname_username"
settings.gis.countries = ["IT"]
settings.gis.legend = "float"
settings.gis.nav_controls = False

# -----------------------------------------------------------------------------
# Shelters
settings.cr.shelter_population_dynamic = True
settings.cr.shelter_housing_unit_management = True

# -----------------------------------------------------------------------------
# Events
settings.event.types_hierarchical = True

# -----------------------------------------------------------------------------
# Evacuees
settings.evr.physical_description = False
settings.pr.show_emergency_contacts = False
settings.evr.link_to_organisation= True

# -----------------------------------------------------------------------------
# Organisations
settings.org.branches = True
settings.org.branches_tree_view = True
settings.org.facility_types_hierarchical = True

# -----------------------------------------------------------------------------
# Human Resource Management
settings.hrm.email_required = False
settings.hrm.org_required = False
settings.hrm.deletable = True
settings.hrm.multiple_job_titles = True
settings.hrm.staff_experience = False
settings.hrm.vol_active = True
settings.hrm.vol_experience = False
settings.hrm.show_organisation = True
settings.hrm.use_awards = False
settings.hrm.use_certificates = False
settings.hrm.use_skills = True
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
        from s3 import S3LocationSelector
        location_id = table.location_id
        location_id.readable = location_id.writable = True
        location_id.label = T("Place of Birth")
        levels = ("L1","L2","L3",)
        location_id.widget = S3LocationSelector(levels=levels,
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
    from s3 import S3HierarchyWidget
    s3db.cr_shelter.capacity_day.writable = s3db.cr_shelter.capacity_night.writable = False
    s3db.cr_shelter.cr_shelter_environment_id.readable = s3db.cr_shelter.cr_shelter_environment_id.writable = True
    organisation_represent = current.s3db.org_OrganisationRepresent
    node_represent = organisation_represent(parent=False)
    org_widget = S3HierarchyWidget(lookup="org_organisation",
                                   represent=node_represent,
                                   multiple=False,
                                   leafonly=False,
                                   )
    s3db.cr_shelter.organisation_id.widget = org_widget

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

    from s3 import IS_ONE_OF
    db = current.db
    table = r.table
    table.exercise.default = True
    table.event_id.readable = table.event_id.writable = True
    represent = S3Represent(lookup=tablename)
    table.event_id.requires = IS_ONE_OF(db, "event_event.id",
                                        represent,
                                        filterby="closed",
                                        filter_opts=(False,),
                                        orderby="event_event.name",
                                        sort=True)

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