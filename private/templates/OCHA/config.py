# -*- coding: utf-8 -*-

from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict
settings = current.deployment_settings
T = current.T

"""
    Template settings for OCHA: UN Office for the Coordination of Humanitarian Affairs
"""

# Pre-Populate
settings.base.prepopulate = ["OCHA"]

settings.base.system_name = T("Who What Where")
settings.base.system_name_short = T("3W")

# Theme (folder to use for views/layout.html)
#settings.base.theme = "OCHA"

# Auth settings
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
settings.auth.registration_requires_approval = True
# Uncomment this to request the Organisation when a user registers
settings.auth.registration_requests_organisation = True

#settings.auth.role_modules = OrderedDict([
#        ("transport", "Airports and Seaports"),
#        ("hms", "Hospitals"),
#        ("org", "Organizations, Offices, and Facilities"),
#        ("inv", "Warehouses"),
#        ("staff", "Staff"),
#        ("vol", "Volunteers"),
#        ("project", "Projects"),
#        #("asset", "Assets"),
#        #("vehicle", "Vehicles"),
#    ])

# L10n settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("fr", "French"),
])
# Default timezone for users
settings.L10n.utc_offset = "UTC +0300"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ["KE"]

# Finance settings
settings.fin.currencies = {
    "EUR" : T("Euros"),
    "GBP" : T("Great British Pounds"),
    "KES" : T("Kenyan Shillings"),
    "USD" : T("United States Dollars"),
}

# Security Policy
settings.security.policy = 1 # Simple
settings.security.map = True

# Set this if there will be multiple areas in which work is being done,
# and a menu to select among them is wanted.
#settings.gis.menu = "Country"
# PoIs to export in KML/OSM feeds from Admin locations
#settings.gis.poi_resources = ["cr_shelter", "hms_hospital", "org_office",
#                              "transport_airport", "transport_seaport"
#                              ]

# Enable this for a UN-style deployment
settings.ui.cluster = True

#settings.frontpage.rss = [
#    {"title": "Blog",
#     "url": "http://eurosha-volunteers-blog.org/feed/"
#    }
#]

# Organisation Management
# Uncomment to add summary fields for Organisations/Offices for # National/International staff
settings.org.summary = True

# HRM
# Uncomment to allow HRs to have multiple Job Roles in addition to their Job Title
settings.hrm.job_roles = True
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to disable Volunteer experience
settings.hrm.vol_experience = False
# Uncomment to disable the use of HR Certificates
settings.hrm.use_certificates = False
# Uncomment to disable the use of HR Credentials
settings.hrm.use_credentials = False
# Uncomment to disable the use of HR Description
settings.hrm.use_description = False
# Uncomment to disable the use of HR ID
settings.hrm.use_id = False
# Uncomment to disable the use of HR Skills
settings.hrm.use_skills = False
# Uncomment to disable the use of HR Trainings
settings.hrm.use_trainings = False

# Projects
# Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
settings.project.mode_3w = True
# Uncomment this to use Codes for projects
settings.project.codes = True
# Uncomment this to call project locations 'Communities'
#settings.project.community = True
# Uncomment this to use multiple Budgets per project
settings.project.multiple_budgets = True
settings.project.theme_percentages = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True
# Uncomment this to customise
settings.project.organisation_roles = {
    1: T("Lead Reporter"),
    2: T("Implementing Partner"),
    3: T("Donor"),
    #4: T("Customer"), # T("Beneficiary")?
    5: T("Partner")
}

# -----------------------------------------------------------------------------
def customize_org_office(**attr):
    """
        Customize org_office controller
    """

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive or r.representation.lower() == "aadata":
            s3db = current.s3db
        
        if r.interactive:
            from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter
            filter_widgets = [
                S3TextFilter(["name",
                              "code",
                              "comments",
                              "organisation_id$name",
                              "organisation_id$acronym",
                              "location_id$name",
                              "location_id$L1",
                              "location_id$L2",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                #S3OptionsFilter("office_type_id",
                #                label=T("Type"),
                #                represent="%(name)s",
                #                widget="multiselect",
                #                cols=3,
                #                #hidden=True,
                #                ),
                S3OptionsFilter("organisation_id",
                                label=T("Organization"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("location_id",
                                 label=T("Location"),
                                 levels=["L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                ]
            s3db.configure("org_office",
                           #crud_form=crud_form,
                           filter_widgets = filter_widgets,
                           )
            
        return result
    s3.prep = custom_prep

    attr["hide_filter"] = False
    return attr

settings.ui.customize_org_office = customize_org_office

# -----------------------------------------------------------------------------
def customize_org_organisation(**attr):
    """
        Customize org_organisation controller
    """

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive or r.representation.lower() == "aadata":
            s3db = current.s3db
            list_fields = ["id",
                           "name",
                           "acronym",
                           "organisation_type_id",
                           (T("Clusters"), "sector.name"),
                           "country",
                           "website"
                           ]
            
            s3db.configure("org_organisation", list_fields=list_fields)
        
        if r.interactive:
            from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponentCheckbox
            crud_form = S3SQLCustomForm(
                "name",
                "acronym",
                "organisation_type_id",
                "region",
                "country",
                S3SQLInlineComponentCheckbox(
                    "sector",
                    label = T("Clusters"),
                    field = "sector_id",
                    cols = 3,
                ),
                "phone",
                "website",
                "year",
                "logo",
                "comments",
            )
            from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter
            filter_widgets = [
                S3TextFilter(["name", "acronym"],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("organisation_type_id",
                                label=T("Type"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3OptionsFilter("sector_organisation.sector_id",
                                label=T("Cluster"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3OptionsFilter("project_organisation.project_id$theme_project.theme_id",
                                label=T("Theme"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("project_organisation.project_id$location.location_id",
                                 label=T("Location"),
                                 levels=["L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                ]
            s3db.configure("org_organisation",
                           crud_form=crud_form,
                           filter_widgets = filter_widgets,
                           )
            
        return result
    s3.prep = custom_prep

    attr["hide_filter"] = False
    return attr

settings.ui.customize_org_organisation = customize_org_organisation

# -----------------------------------------------------------------------------
def customize_project_project(**attr):
    """
        Customize project_project controller
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive  or r.representation == "aadata":
            # Configure fields 
            field = r.table.duration
            field.readable = field.writable = True

        if r.interactive:
            from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter, S3DateFilter
            filter_widgets = [
                S3TextFilter(["name",
                              "code",
                              "description",
                              "organisation.name",
                              "organisation.acronym",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("status_id",
                                label=T("Status"),
                                represent="%(name)s",
                                cols=3,
                                ),
                S3OptionsFilter("theme_project.theme_id",
                                label=T("Theme"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("location.location_id",
                                 label=T("Location"),
                                 levels=["L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                # @ToDo: Widget to handle Start & End in 1!
                S3DateFilter("start_date",
                             label=T("Start Date"),
                             hide_time=True,
                             #hidden=True,
                             ),
                S3DateFilter("end_date",
                             label=T("End Date"),
                             hide_time=True,
                             #hidden=True,
                             ),
                ]
            current.s3db.configure("project_project",
                                   filter_widgets = filter_widgets,
                                   )
        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False
    return attr

settings.ui.customize_project_project = customize_project_project

# -----------------------------------------------------------------------------
def customize_project_location(**attr):
    """
        Customize project_location controller
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:
            messages = current.messages
            from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter, S3DateFilter
            filter_widgets = [
                S3TextFilter(["project_id$name",
                              "project_id$code",
                              "project_id$description",
                              "location_id$name",
                              "project_id$organisation.name",
                              "project_id$organisation.acronym",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("project_id$status_id",
                                label=T("Status"),
                                represent="%(name)s",
                                #widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3OptionsFilter("project_id$theme_project.theme_id",
                                label=T("Theme"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("location_id",
                                 label=T("Location"),
                                 levels=["L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                # @ToDo: Widget to handle Start & End in 1!
                S3DateFilter("start_date",
                             label=T("Start Date"),
                             hide_time=True,
                             #hidden=True,
                             ),
                S3DateFilter("end_date",
                             label=T("End Date"),
                             hide_time=True,
                             #hidden=True,
                             ),
                ]
            report_fields = [
                #(messages.COUNTRY, "location_id$L0"),
                "location_id$L1",
                "location_id$L2",
                #"location_id$L3",
                #"location_id$L4",
                (messages.ORGANISATION, "project_id$organisation_id"),
                (T("Project"), "project_id"),
                #(T("Activity Types"), "activity_type.activity_type_id"),
                (T("Themes"), "project_id$theme.name"),
                ]
            report_options = Storage(
                rows=report_fields,
                cols=report_fields,
                fact=report_fields,
                defaults=Storage(rows="location_id$L2",
                                 #cols=(T("Themes"), "project_id$theme.name"),
                                 cols="project_id$theme.name",
                                 # T("Projects")
                                 fact="count(project_id$name)",
                                 totals=True
                                 )
                )
            current.s3db.configure("project_location",
                                   filter_widgets = filter_widgets,
                                   report_options = report_options,
                                   )
        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False
    return attr

settings.ui.customize_project_location = customize_project_location

# -----------------------------------------------------------------------------
def customize_project_organisation(**attr):
    """
        Customize project_organisation controller
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:
            from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter
            filter_widgets = [
                S3TextFilter(["project_id$name",
                              "project_id$code",
                              "project_id$description",
                              "organisation_id$name",
                              "organisation_id$acronym",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("role",
                                label=T("Role"),
                                #represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3OptionsFilter("project_id$theme_project.theme_id",
                                label=T("Theme"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("project_id$location.location_id",
                                 label=T("Location"),
                                 levels=["L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                ]
            report_fields = ["project_id",
                             "organisation_id",
                             "role",
                             "amount",
                             "currency",
                             ]
            report_options = Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=report_fields,
                    defaults=Storage(rows = "organisation_id",
                                     cols = "currency",
                                     fact = "sum(amount)",
                                     totals = False
                                     )
                    )
            current.s3db.configure("project_organisation",
                                   filter_widgets = filter_widgets,
                                   report_options = report_options,
                                   )
        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False
    return attr

settings.ui.customize_project_organisation = customize_project_organisation

# -----------------------------------------------------------------------------
def customize_project_beneficiary(**attr):
    """
        Customize project_beneficiary controller
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:
            from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter
            filter_widgets = [
                S3TextFilter(["project_id$name",
                              "project_id$code",
                              "project_id$description",
                              "project_id$organisation.name",
                              "project_id$organisation.acronym",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("parameter_id",
                                label=T("Beneficiary Type"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3OptionsFilter("project_id$theme_project.theme_id",
                                label=T("Theme"),
                                represent="%(name)s",
                                widget="multiselect",
                                cols=3,
                                #hidden=True,
                                ),
                S3LocationFilter("project_location_id$location_id",
                                 label=T("Location"),
                                 levels=["L1", "L2"],
                                 widget="multiselect",
                                 cols=3,
                                 #hidden=True,
                                 ),
                ]
            report_fields = ["project_location_id",
                             (T("Beneficiary Type"), "parameter_id"),
                             "project_id",
                             (T("Year"), "year"),
                             #"project_id$hazard.name",
                             "project_id$theme.name",
                             #(current.messages.COUNTRY, "location_id$L0"),
                             "location_id$L1",
                             "location_id$L2",
                             "location_id$L3",
                             "location_id$L4",
                             ]
            report_options = Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=report_fields,
                    defaults=Storage(rows="project_id",
                                     cols="parameter_id",
                                     fact="sum(value)",
                                     totals=True
                                     )
                    )
            current.s3db.configure("project_organisation",
                                   filter_widgets = filter_widgets,
                                   report_options = report_options,
                                   )
        return True
    s3.prep = custom_prep

    attr["hide_filter"] = False
    return attr

settings.ui.customize_project_beneficiary = customize_project_beneficiary

# -----------------------------------------------------------------------------
# Comment/uncomment modules here to disable/enable them
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
            module_type = 3,
        )),
    ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = None
        )),
    ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 2
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
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
    ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 1
        )),
    ("stats", Storage(
            name_nice = "Stats",
            #description = "Needed for Project Beneficiaries",
            restricted = True,
            module_type = None
        )),
    #("cr", Storage(
    #        name_nice = T("Shelters"),
    #        #description = "Tracks the location, capacity and breakdown of victims in Shelters",
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("hms", Storage(
    #        name_nice = T("Hospitals"),
    #        #description = "Helps to monitor status of hospitals",
    #        restricted = True,
    #        module_type = 3
    #    )),
    #("transport", Storage(
    #       name_nice = T("Transport"),
    #       restricted = True,
    #       module_type = 10,
    #   )),
])
