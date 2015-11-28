# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

import datetime
    
from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings: 'Skeleton' designed to be copied to quickly create
                           custom templates

        All settings which are to configure a specific template are located
        here. Deployers should ideally not need to edit any other files outside
        of their template folder.
    """

    T = current.T

    settings.base.system_name = T("Refugee Support Database")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    #settings.base.prepopulate = ("skeleton", "default/users")
    settings.base.prepopulate += ("DRK", "default/users", "DRK/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "DRK"

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("en", "English"),
       ("de", "Deutsch"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "de"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.utc_offset = "+0100"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
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
    settings.security.policy = 7 # Organisation-ACLs

    # -------------------------------------------------------------------------
    # Inventory Module Settings
    #
    settings.inv.facility_label = "Facility"
    settings.inv.facility_manage_staff = False

    # -------------------------------------------------------------------------
    # Organisations Module Settings
    #
    settings.org.default_organisation = "Deutsches Rotes Kreuz"
    settings.org.default_site = "BEA Benjamin Franklin Village"

    # -------------------------------------------------------------------------
    # Persons Module Settings
    #
    #settings.pr.separate_name_fields = 2

    # -------------------------------------------------------------------------
    # Project Module Settings
    #
    settings.project.mode_task = True
    settings.project.sectors = False

    # NB should not add or remove options, but just comment/uncomment
    settings.project.task_status_opts = {#1: T("Draft"),
                                         2: T("New"),
                                         3: T("Assigned"),
                                         #4: T("Feedback"),
                                         #5: T("Blocked"),
                                         6: T("On Hold"),
                                         7: T("Canceled"),
                                         #8: T("Duplicate"),
                                         #9: T("Ready"),
                                         #10: T("Verified"),
                                         #11: T("Reopened"),
                                         12: T("Completed"),
                                         }

    # -------------------------------------------------------------------------
    # Requests Module Settings
    #
    settings.req.req_type = ("Stock",)
    settings.req.use_commit = False
    settings.req.recurring = False

    # -------------------------------------------------------------------------
    # Shelter Module Settings
    #
    settings.cr.shelter_population_dynamic = True
    settings.cr.shelter_housing_unit_management = True

    # -------------------------------------------------------------------------
    def site_check_in(site_id, person_id):
        """
            When a person is checked-in to a Shelter then update the Shelter Registration
            (We assume they are checked-in during initial registration)
        """

        s3db = current.s3db

        # Find the Registration
        stable = s3db.cr_shelter
        rtable = s3db.cr_shelter_registration
        query = (stable.site_id == site_id) & \
                (stable.id == rtable.shelter_id) & \
                (rtable.person_id == person_id)
        registration = current.db(query).select(rtable.id,
                                                rtable.registration_status,
                                                limitby=(0, 1),
                                                ).first()
        if not registration:
            error = T("Registration not found")
            warning = None
            return error, warning

        if registration.registration_status == 2:
            error = None
            warning = T("Client was already checked-in")
            return error, warning

        # Update the Shelter Registration
        registration.update_record(registration_status = 2)
        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)
        return None, None

    # -------------------------------------------------------------------------
    def site_check_out(site_id, person_id):
        """
            When a person is checked-out from a Shelter then update the Shelter Registration
        """

        s3db = current.s3db

        # Find the Registration
        stable = s3db.cr_shelter
        rtable = s3db.cr_shelter_registration
        query = (stable.site_id == site_id) & \
                (stable.id == rtable.shelter_id) & \
                (rtable.person_id == person_id)
        registration = current.db(query).select(rtable.id,
                                                rtable.registration_status,
                                                limitby=(0, 1),
                                                ).first()
        if not registration:
            error = T("Registration not found")
            warning = None
            return error, warning

        if registration.registration_status == 3:
            error = None
            warning = T("Client was already checked-out")
            return error, warning

        # Update the Shelter Registration
        registration.update_record(registration_status = 3)
        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)
        return None, None

    # -------------------------------------------------------------------------
    def customise_cr_shelter_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "check-in":
                current.s3db.configure("cr_shelter",
                                       site_check_in = site_check_in,
                                       site_check_out = site_check_out,
                                       )
            return  result
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.method == "check-in":
                current.menu.options = None
                output["rheader"] = ""

            return output

        s3.postp = custom_postp

        return attr

    settings.customise_cr_shelter_controller = customise_cr_shelter_controller

    # -------------------------------------------------------------------------
    # Person Registry Settings
    #
    settings.pr.hide_third_gender = False

    # -------------------------------------------------------------------------
    # DVR Module Settings and Customizations
    #
    dvr_case_tabs = [(T("Basic Details"), ""),
                     (T("Family Members"), "group_membership/"),
                     (T("Activities"), "case_activity"),
                     (T("Appointments"), "case_appointment"),
                     ]

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True


            if r.controller == "dvr" and not r.component:

                s3db.add_components("pr_person",
                                    pr_person_tag = {"name": "eo_number",
                                                     "joinby": "person_id",
                                                     "filterby": "tag",
                                                     "filterfor": ("EONUMBER",),
                                                     "multiple": False,
                                                     },
                                    )

                from gluon import IS_EMPTY_OR, IS_NOT_EMPTY

                ctable = s3db.dvr_case
                #default_organisation = current.auth.root_org()
                default_organisation = settings.get_org_default_organisation()

                field = ctable.valid_until

                # Case is valid for 5 years
                from dateutil.relativedelta import relativedelta
                field.default = r.utcnow + relativedelta(years=5)
                field.readable = field.writable = True

                if default_organisation:
                    # Set default for organisation_id and hide the field
                    # (already done in core model)
                    #field = ctable.organisation_id
                    #field.default = default_organisation
                    #field.readable = field.writable = False

                    # Hide organisation_id in list_fields, too
                    list_fields = r.resource.get_config("list_fields")
                    if "dvr_case.organisation_id" in list_fields:
                        list_fields.remove("dvr_case.organisation_id")

                    default_site = settings.get_org_default_site()
                    if default_site:
                        # Set default for organisation_id and hide the field
                        # (already done in core model)

                        # Set default shelter_id
                        db = current.db
                        stable = s3db.cr_shelter
                        query = (stable.site_id == default_site)
                        shelter = db(query).select(stable.id,
                                                   limitby=(0, 1)
                                                   ).first()
                        if shelter:
                            shelter_id = shelter.id
                            rtable = s3db.cr_shelter_registration
                            field = rtable.shelter_id
                            field.default = shelter_id
                            field.readable = field.writable = False

                            # Filter housing units to units of this shelter
                            field = rtable.shelter_unit_id
                            dbset = db(s3db.cr_shelter_unit.shelter_id == shelter_id)
                            from s3 import IS_ONE_OF
                            field.requires = IS_EMPTY_OR(
                                                IS_ONE_OF(dbset, "cr_shelter_unit.id",
                                                          field.represent,
                                                          sort=True,
                                                          ))
                    else:
                        # Limit sites to default_organisation
                        field = ctable.site_id
                        requires = field.requires
                        if requires:
                            if isinstance(requires, IS_EMPTY_OR):
                                requires = requires.other
                            if hasattr(requires, "dbset"):
                                stable = s3db.org_site
                                query = (stable.organisation_id == default_organisation)
                                requires.dbset = current.db(query)

                resource = r.resource
                if r.interactive and r.method != "import":

                    # Nationality is required
                    ctable = s3db.pr_person_details
                    for fn in ("nationality",
                               "marital_status",
                               ):
                        field = ctable[fn]
                        requires = field.requires
                        if not requires:
                            field.requires = IS_NOT_EMPTY
                        elif isinstance(requires, IS_EMPTY_OR):
                            field.requires = requires.other

                    table = resource.table
                    from s3 import IS_PERSON_GENDER
                    gender_opts = dict(s3db.pr_gender_opts)

                    field = table.gender
                    table.default = None
                    del gender_opts[1] # "unknown" option not allowed
                    field.requires = IS_PERSON_GENDER(gender_opts,
                                                      sort = True,
                                                      zero = None,
                                                      )

                    # Last name is required
                    field = table.last_name
                    field.requires = IS_NOT_EMPTY()

                    # Custom CRUD form
                    from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
                    crud_form = S3SQLCustomForm(
                                #"dvr_case.reference",
                                # Will always default & be hidden
                                "dvr_case.organisation_id",
                                # Will always default & be hidden
                                "dvr_case.site_id",
                                "dvr_case.date",
                                (T("Case Status"), "dvr_case.status_id"),
                                # Will always default & be hidden
                                #"cr_shelter_registration.site_id",
                                "cr_shelter_registration.shelter_id",
                                # @ ToDo: Automate this from the Case Status?
                                (T("Shelter Registration Status"), "cr_shelter_registration.registration_status"),
                                "cr_shelter_registration.shelter_unit_id",
                                "cr_shelter_registration.check_in_date",
                                (T("ID"), "pe_label"),
                                S3SQLInlineComponent(
                                        "eo_number",
                                        fields = [("", "value"),
                                                  ],
                                        filterby = {"field": "tag",
                                                    "options": "EONUMBER",
                                                    },
                                        label = T("EasyOpt Number"),
                                        multiple = False,
                                        name = "eo_number",
                                        ),
                                S3SQLInlineLink("case_flag",
                                                label = T("Flags"),
                                                field = "flag_id",
                                                cols = 3,
                                                ),
                                "first_name",
                                "last_name",
                                "date_of_birth",
                                "gender",
                                "person_details.nationality",
                                "person_details.occupation",
                                "person_details.marital_status",
                                S3SQLInlineComponent(
                                        "contact",
                                        fields = [("", "value"),
                                                  ],
                                        filterby = {"field": "contact_method",
                                                    "options": "SMS",
                                                    },
                                        label = T("Mobile Phone"),
                                        multiple = False,
                                        name = "phone",
                                        ),
                                "person_details.literacy",
                                S3SQLInlineComponent(
                                        "case_language",
                                        fields = ["language",
                                                  "quality",
                                                  "comments",
                                                  ],
                                        label = T("Language / Communication Mode"),
                                        ),
                                "dvr_case.comments",
                                )
                    resource.configure(crud_form = crud_form,
                                       )

                    # Remove filter default for case status
                    filter_widgets = resource.get_config("filter_widgets")
                    if filter_widgets:
                        from s3 import S3TextFilter
                        for fw in filter_widgets:
                            if fw.field == "dvr_case.status_id":
                                fw.opts.default = None
                            if isinstance(fw, S3TextFilter):
                                fw.field.append("eo_number.value")
                        from s3 import S3DateFilter
                        dob_filter = S3DateFilter("date_of_birth")
                        dob_filter.operator = ["eq"]
                        filter_widgets.insert(1, dob_filter)

                # Custom list fields (must be outside of r.interactive)
                list_fields = [#"dvr_case.reference",
                               (T("ID"), "pe_label"),
                               (T("EasyOpt No."), "eo_number.value"),
                               "first_name",
                               "last_name",
                               "date_of_birth",
                               "gender",
                               "person_details.nationality",
                               "dvr_case.date",
                               "dvr_case.valid_until",
                               "dvr_case.status_id",
                               ]
                resource.configure(list_fields = list_fields,
                                   )
            return result
        s3.prep = custom_prep

        # Custom rheader tabs
        attr = dict(attr)
        attr["rheader"] = lambda r: s3db.dvr_rheader(r, tabs=dvr_case_tabs)

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def customise_pr_group_membership_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            resource = r.resource
            if r.controller == "dvr" and r.interactive:
                resource.configure(filter_widgets = None)

                table = resource.table
                field = table.person_id

                from s3 import IS_ADD_PERSON_WIDGET2, S3AddPersonWidget2

                field.represent = s3db.pr_PersonRepresent(show_link=True)
                field.requires = IS_ADD_PERSON_WIDGET2()
                field.widget = S3AddPersonWidget2(controller="dvr")

            return result
        s3.prep = custom_prep

        attr = dict(attr)
        def rheader(r):
            if r.controller == "dvr":
                return s3db.dvr_rheader(r, tabs=dvr_case_tabs)
            else:
                return attr.get("rheader")
        attr["rheader"] = rheader



        return attr

    settings.customise_pr_group_membership_controller = customise_pr_group_membership_controller

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_controller(**attr):

        s3 = current.response.s3
        s3db = current.s3db

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if not r.component:

                resource = r.resource
                filter_widgets = resource.get_config("filter_widgets")
                if filter_widgets:
                    s3db.add_components("pr_person",
                                        pr_person_tag = {"name": "eo_number",
                                                         "joinby": "person_id",
                                                         "filterby": "tag",
                                                         "filterfor": ("EONUMBER",),
                                                         "multiple": False,
                                                         },
                                        )
                    from s3 import S3TextFilter
                    for fw in filter_widgets:
                        if isinstance(fw, S3TextFilter):
                            fw.field.append("person_id$eo_number.value")
                            break

                # Custom list fields
                list_fields = [(T("ID"), "person_id$pe_label"),
                               "person_id$first_name",
                               "person_id$last_name",
                               "need_id",
                               "need_details",
                               "emergency",
                               "referral_details",
                               "followup",
                               "followup_date",
                               "completed",
                               ]

                r.resource.configure(list_fields = list_fields,
                                    )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_dvr_case_activity_controller = customise_dvr_case_activity_controller

    # -------------------------------------------------------------------------
    def customise_dvr_case_appointment_controller(**attr):

        s3 = current.response.s3
        s3db = current.s3db

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if not r.component:

                resource = r.resource

                if r.interactive and not r.id:
                    # Custom filter widgets
                    s3db.add_components("pr_person",
                                        pr_person_tag = {"name": "eo_number",
                                                         "joinby": "person_id",
                                                         "filterby": "tag",
                                                         "filterfor": ("EONUMBER",),
                                                         "multiple": False,
                                                         },
                                        )

                    from s3 import S3TextFilter, S3OptionsFilter, S3DateFilter, get_s3_filter_opts
                    filter_widgets = [
                        S3TextFilter(["person_id$pe_label",
                                      "person_id$first_name",
                                      "person_id$last_name",
                                      "person_id$eo_number.value",
                                      ],
                                      label = T("Search"),
                                      ),
                        S3OptionsFilter("type_id",
                                        options = get_s3_filter_opts("dvr_case_appointment_type"),
                                        cols = 3,
                                        ),
                        S3OptionsFilter("status",
                                        default = 2,
                                        ),
                        S3DateFilter("date",
                                     ),
                        ]
                    resource.configure(filter_widgets = filter_widgets)

                # Default filter today's and tomorrow's appointments
                from s3 import s3_set_default_filter
                now = current.request.utcnow
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                tomorrow = today + datetime.timedelta(days=2)
                s3_set_default_filter("~.date",
                                      {"ge": today, "le": tomorrow},
                                      tablename = "dvr_case_appointment",
                                      )

                # Field Visibility
                table = resource.table
                field = table.case_id
                field.readable = field.writable = False
                    
                # Custom list fields
                list_fields = [(T("ID"), "person_id$pe_label"),
                               "person_id$first_name",
                               "person_id$last_name",
                               "type_id",
                               "date",
                               "status",
                               "comments",
                               ]

                resource.configure(list_fields = list_fields,
                                   insertable = False,
                                   deletable = False,
                                   update_next = r.url(method=""),
                                   )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_dvr_case_appointment_controller = customise_dvr_case_appointment_controller

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
        #("cms", Storage(
        # name_nice = T("Content Management"),
        ##description = "Content Management System",
        # restricted = True,
        # module_type = 10,
        #)),
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
        ("supply", Storage(
           name_nice = T("Supply Chain Management"),
           #description = "Used within Inventory Management, Request Management and Asset Management",
           restricted = True,
           module_type = None, # Not displayed
        )),
        ("inv", Storage(
           name_nice = T("Warehouses"),
           #description = "Receiving and Sending Items",
           restricted = True,
           module_type = 4
        )),
        ("asset", Storage(
           name_nice = T("Assets"),
           #description = "Recording and Assigning Assets",
           restricted = True,
           module_type = 5,
        )),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("req", Storage(
           name_nice = T("Requests"),
           #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
           restricted = True,
           module_type = 10,
        )),
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
        ("dvr", Storage(
          name_nice = T("Refugees"),
          #description = "Allow affected individuals & households to register to receive compensation and distributions",
          restricted = True,
          module_type = 10,
        )),
        ("event", Storage(
           name_nice = T("Events"),
           #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
           restricted = True,
           module_type = 10,
        )),
        ("security", Storage(
           name_nice = T("Security"),
           restricted = True,
           module_type = 10,
        )),
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