# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for HowCalm
    """

    T = current.T

    settings.base.system_name = T("HowCalm")
    settings.base.system_name_short = T("HowCalm")

    # PrePopulate data
    settings.base.prepopulate += ("HowCalm",)
    settings.base.prepopulate_demo += ("HowCalm/Demo",)

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "HowCalm"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("US",)
    gis_levels = ("L2", "L3", "L4")

    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("es", "Español"),
    ])

    # Default timezone for users
    settings.L10n.utc_offset = "+0500"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","

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
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
    ])

    settings.hrm.staff_label = "Contacts"
    settings.org.organisation_types_hierarchical = True
    settings.ui.export_formats = ("pdf", "xls")

    # -------------------------------------------------------------------------
    def howcalm_rheader(r):

        if r.representation != "html":
            # RHeaders only used in interactive views
            return None

        # Need to use this format as otherwise req_match?viewing=org_office.x
        # doesn't have an rheader
        from s3 import s3_rheader_resource
        tablename, record = s3_rheader_resource(r)

        if record is None:
            # List or Create form: rheader makes no sense here
            return None

        T = current.T

        if tablename == "org_organisation":
            tabs = [(T("Basic Details"), None),
                    (T("Contacts"), "human_resource"),
                    (T("Facilities"), "facility"),
                    ]

            from s3 import s3_rheader_tabs
            rheader_tabs = s3_rheader_tabs(r, tabs)

            from gluon import A, DIV, TABLE, TR, TH

            db = current.db
            s3db = current.s3db

            table = s3db.org_organisation

            record_data = TABLE(TR(TH(record.name)))
            record_data_append = record_data.append

            record_id = record.id

            otagtable = s3db.org_organisation_tag
            query = (otagtable.organisation_id == record_id) & \
                    (otagtable.tag == "org_id")
            org_id = db(query).select(otagtable.value,
                                      limitby = (0, 1)
                                      ).first()
            if org_id:
                record_data_append(TR(TH("%s: " % T("Organization ID")),
                                      org_id.value))

            otypetable = s3db.org_organisation_type
            ltable = s3db.org_organisation_organisation_type
            query = (ltable.organisation_id == record_id) & \
                    (ltable.organisation_type_id == otypetable.id)
            religion = db(query).select(otypetable.name,
                                        limitby = (0, 1)
                                        ).first()
            if religion:
                record_data_append(TR(TH("%s: " % T("Religion")),
                                      religion.name))

            website = record.website
            if website:
                record_data_append(TR(TH("%s: " % table.website.label),
                                      A(website, _href=website)))

            ctable = s3db.pr_contact
            query = (table.id == record_id) & \
                    (table.pe_id == ctable.pe_id) & \
                    (ctable.contact_method == "FACEBOOK")
            facebook = db(query).select(ctable.value,
                                        limitby = (0, 1)
                                        ).first()
            if facebook:
                url = facebook.value
                record_data_append(TR(TH("%s: " % T("Facebook")),
                                      A(url, _href=url)))

            rheader = DIV(record_data,
                          rheader_tabs,
                          )

        elif tablename == "org_facility":

            settings = current.deployment_settings
            STAFF = settings.get_hrm_staff_label()
            tabs = [(T("Basic Details"), None),
                    (STAFF, "human_resource"),
                    ]
            permitted = current.auth.s3_has_permission
            if permitted("update", tablename, r.id) and \
               permitted("create", "hrm_human_resource_site"):
                tabs.append((T("Assign %(staff)s") % dict(staff=STAFF), "assign"))

            def facility_type_lookup(record):
                db = current.db
                ltable = db.org_site_facility_type
                ttable = db.org_facility_type
                query = (ltable.site_id == record.site_id) & \
                        (ltable.facility_type_id == ttable.id)
                rows = db(query).select(ttable.name)
                if rows:
                    return ", ".join([row.name for row in rows])
                else:
                    return current.messages["NONE"]
            rheader_fields = [["name",
                               "organisation_id",
                               "email",
                               ],
                              [(T("Facility Type"), facility_type_lookup),
                               "location_id",
                               "phone1",
                               ],
                              ]

            from s3 import S3ResourceHeader
            rheader_fields, rheader_tabs = S3ResourceHeader(rheader_fields,
                                                            tabs)(r, as_div=True)

            rheader = DIV(rheader_fields)
            rheader.append(rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE

        from s3 import IS_INT_AMOUNT, \
                       S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        s3db = current.s3db

        # Filtered components
        s3db.add_components("org_organisation",
                            org_organisation_tag = ({"name": "org_id",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "org_id"},
                                                     },
                                                    {"name": "congregants",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "congregants"},
                                                     },
                                                    {"name": "clergy_staff",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "clergy_staff"},
                                                     },
                                                    {"name": "lay_staff",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "lay_staff"},
                                                     },
                                                    {"name": "religious_staff",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "religious_staff"},
                                                     },
                                                    {"name": "volunteers",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "volunteers"},
                                                     },
                                                    {"name": "board",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "board"},
                                                     },
                                                    {"name": "internet",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "internet"},
                                                     "multiple": False,
                                                     },
                                                    ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        integer_represent = IS_INT_AMOUNT.represent

        congregants = components_get("congregants")
        f = congregants.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        clergy_staff = components_get("clergy_staff")
        f = clergy_staff.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        lay_staff = components_get("lay_staff")
        f = lay_staff.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        religious_staff = components_get("religious_staff")
        f = religious_staff.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        volunteers = components_get("volunteers")
        f = volunteers.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        board = components_get("board")
        f = board.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        internet = components_get("internet")
        f = internet.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        crud_fields = ["name",
                       S3SQLInlineComponent(
                            "org_id",
                            label = T("Organization ID"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "tag",
                            #                options = "org_id",
                            #                ),
                            ),
                       S3SQLInlineLink("organisation_type",
                                       field = "organisation_type_id",
                                       label = T("Religion"),
                                       multiple = False,
                                       widget = "hierarchy",
                                       ),
                       "website",
                       S3SQLInlineComponent(
                            "facebook",
                            name = "facebook",
                            label = T("Facebook"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "contact_method",
                            #                options = "FACEBOOK",
                            #                ),
                            ),
                       S3SQLInlineComponent(
                            "congregants",
                            name = "congregants",
                            label = T("# Congregants"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "tag",
                            #                options = "congregants",
                            #                ),
                            ),
                       S3SQLInlineComponent(
                            "clergy_staff",
                            name = "clergy_staff",
                            label = T("# Clergy Staff"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "tag",
                            #                options = "clergy_staff",
                            #                ),
                            ),
                       S3SQLInlineComponent(
                            "lay_staff",
                            name = "lay_staff",
                            label = T("# Lay Staff"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "tag",
                            #                options = "lay_staff",
                            #                ),
                            ),
                       S3SQLInlineComponent(
                            "religious_staff",
                            name = "religious_staff",
                            label = T("# Religious Staff"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "tag",
                            #                options = "religious_staff",
                            #                ),
                            ),
                       S3SQLInlineComponent(
                            "volunteers",
                            name = "volunteers",
                            label = T("# Volunteers"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "tag",
                            #                options = "volunteers",
                            #                ),
                            ),
                       S3SQLInlineComponent(
                            "board",
                            name = "board",
                            label = T("# C. Board"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = dict(field = "tag",
                            #                options = "board",
                            #                ),
                            ),
                       (T("Internet Access"), "internet.value"),
                       "comments",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields)

        from s3 import S3HierarchyFilter, S3LocationFilter, S3TextFilter#, S3OptionsFilter
        filter_widgets = [
            S3TextFilter(["name", "org_id.value"],
                         label = T("Search"),
                         comment = T("Search by organization name or ID. You can use * as wildcard."),
                         _class = "filter-search",
                         ),
            S3HierarchyFilter("organisation_organisation_type.organisation_type_id",
                              label = T("Religion"),
                              ),
            S3LocationFilter("org_facility.location_id",
                             label = T("Location"),
                             levels = gis_levels,
                             #hidden = True,
                             ),
            ]

        if r.method == "review":
            from s3 import S3DateTime
            s3db.org_organisation.created_on.represent = \
                lambda dt: S3DateTime.date_represent(dt, utc=True)
            list_fields = [(T("ID"), "org_id.value"),
                           "name",
                           (T("Religion"), "organisation_organisation_type.organisation_type_id"),
                           (T("Date Registered"), "created_on"),
                           # @ToDo: Address
                           ]
        else:
            list_fields = [(T("ID"), "org_id.value"),
                           "name",
                           (T("Religion"), "organisation_organisation_type.organisation_type_id"),
                           # @ToDo: Address
                           ]

        s3db.configure("org_organisation",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

# END =========================================================================
