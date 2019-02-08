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
    settings.auth.registration_requests_mobile_phone = True
    settings.auth.registration_mobile_phone_mandatory = True

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

    # Record Approval
    settings.auth.record_approval = True
    settings.auth.record_approval_required_for = ("org_organisation",
                                                  )

    # Open records in read mode rather then edit by default
    settings.ui.open_read = True

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

        if tablename == "pr_person":
            #tabs = [(T("Basic Details"), None),
            #        ]

            #from s3 import s3_rheader_tabs
            #rheader_tabs = s3_rheader_tabs(r, tabs)

            from gluon import DIV, TABLE, TR, TH

            from s3 import s3_fullname
            record_data = TABLE(TR(TH(s3_fullname(record))))
            record_data_append = record_data.append

            record_id = record.id

            db = current.db
            s3db = current.s3db

            ptagtable = current.s3db.pr_person_tag
            query = (ptagtable.person_id == record_id) & \
                    (ptagtable.tag == "religious_title")
            religious_title = db(query).select(ptagtable.value,
                                               limitby = (0, 1)
                                               ).first()
            if religious_title:
                record_data_append(TR(TH("%s: " % T("Religious Title")),
                                      religious_title.value))

            query = (ptagtable.person_id == record_id) & \
                    (ptagtable.tag == "position_title")
            position_title = db(query).select(ptagtable.value,
                                              limitby = (0, 1)
                                              ).first()
            if position_title:
                record_data_append(TR(TH("%s: " % T("Position Title")),
                                      position_title.value))

            rheader = DIV(record_data,
                          #rheader_tabs,
                          )

        elif tablename == "org_organisation":
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

            ltable = s3db.org_organisation_organisation_type
            query = (ltable.organisation_id == record_id)
            religion = db(query).select(ltable.organisation_type_id,
                                        limitby = (0, 1)
                                        ).first()
            if religion:
                record_data_append(TR(TH("%s: " % T("Religion")),
                                      ltable.organisation_type_id.represent(religion.organisation_type_id)))

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
            #tabs = [(T("Basic Details"), None),
            #        ]

            #from s3 import s3_rheader_tabs
            #rheader_tabs = s3_rheader_tabs(r, tabs)

            from gluon import DIV, TABLE, TR, TH

            record_data = TABLE(TR(TH(record.name)))
            record_data_append = record_data.append

            #record_id = record.id
            site_id = record.site_id

            db = current.db
            s3db = current.s3db

            stagtable = current.s3db.org_site_tag
            query = (stagtable.site_id == site_id) & \
                    (stagtable.tag == "oem_ready")
            oem_ready = db(query).select(stagtable.value,
                                         limitby = (0, 1)
                                         ).first()
            if oem_ready:
                record_data_append(TR(TH("%s: " % T("OEM Ready Receiving Center")),
                                      oem_ready.value))

            rheader = DIV(record_data,
                          #rheader_tabs,
                          )

        return rheader

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Contact"),
            title_display = T("Contact Details"),
            title_list = T("Contact Catalog"),
            title_update = T("Edit Contact"),
            label_list_button = T("List Contacts"),
            label_delete_button = T("Delete Contact"),
            msg_record_created = T("Contact added"),
            msg_record_modified = T("Contact updated"),
            msg_record_deleted = T("Contact deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        # Ensure we have the filtered components
        customise_pr_person_resource(r, "pr_person")

        list_fields = [(T("Person Name"), "person_id"),
                       (T("Type"), "job_title_id"),
                       (T("Languages Spoken"), "person_id$languages_spoken.value"),
                       (T("Religious Title"), "person_id$religious_title.value"),
                       (T("Position Title"), "person_id$position_title.value"),
                       (T("ECDM"), "person_id$em_comms.value"),
                       ]

        current.s3db.configure(tablename,
                               list_fields = list_fields,
                               )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            mine = r.get_vars.get("mine")
            if mine:
                from s3 import FS
                _filter = (FS("organisation_id") == current.auth.user.organisation_id)
                r.resource.add_filter(_filter)
                s3.crud_strings["hrm_human_resource"].title_list = T("My Contacts")

            return result
        s3.prep = custom_prep

        # Never used: always open individual records in person perspective
        #attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_msg_contact_resource(r, tablename):

        from s3 import S3SQLCustomForm#, S3SQLInlineComponent

        s3db = current.s3db

        # Filtered components
        s3db.add_components("msg_contact",
                            msg_tag = ({"name": "position",
                                        "joinby": "message_id",
                                        "filterby": {"tag": "position"},
                                        "multiple": False,
                                        },
                                       ),
                            )

        crud_fields = [(T("Topic"), "subject"),
                       "name",
                       (T("Position"), "position.value"),
                       "phone",
                       "from_address",
                       "body",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields)

        s3db.configure("msg_contact",
                       crud_form = crud_form,
                       )

    settings.customise_msg_contact_resource = customise_msg_contact_resource

    # -------------------------------------------------------------------------
    def customise_msg_contact_controller(**attr):

        s3 = current.response.s3

        #standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            #if callable(standard_prep):
            #    result = standard_prep(r)
            #else:
            result = True

            if not current.auth.s3_has_role("MANAGER"):
                r.method = "create"

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_msg_contact_controller = customise_msg_contact_controller

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE

        from s3 import IS_INT_AMOUNT, \
                       S3LocationSelector, \
                       S3SQLCustomForm#, S3SQLInlineComponent

        s3db = current.s3db

        s3db.org_facility.location_id.widget = S3LocationSelector(levels = gis_levels,
                                                                  show_address = True,
                                                                  )

        # Filtered components
        s3db.add_components("org_facility",
                            org_site_tag = ({"name": "congregations",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "congregations"},
                                             "multiple": False,
                                             },
                                            {"name": "cross_streets",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "cross_streets"},
                                             "multiple": False,
                                             },
                                            {"name": "em_call",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "em_call"},
                                             "multiple": False,
                                             },
                                            {"name": "oem_ready",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "oem_ready"},
                                             "multiple": False,
                                             },
                                            {"name": "oem_want",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "oem_want"},
                                             "multiple": False,
                                             },
                                            ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        integer_represent = IS_INT_AMOUNT.represent

        congregations = components_get("congregations")
        f = congregations.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        em_call = components_get("em_call")
        f = em_call.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        oem_ready = components_get("oem_ready")
        f = oem_ready.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        #from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        oem_want = components_get("oem_want")
        f = oem_want.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        #from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        crud_fields = ["organisation_id",
                       "name",
                       "location_id",
                       (T("# of Congregations"), "congregations.value"),
                       (T("Cross Streets"), "cross_streets.value"),
                       (T("Building Status"), "status.facility_status"),
                       (T("Call in Emergency"), "em_call.value"),
                       (T("OEM Ready Receiving Center"), "oem_ready.value"),
                       (T("Want to be an OEM Ready Receiving Center"), "oem_want.value"),
                       "comments",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields)

        list_fields = [#"organisation_id",
                       #"name",
                       (T("Physical Address"), "location_id$addr_street"),
                       (T("# of Congregations"), "congregations.value"),
                       (T("Building Status"), "status.facility_status"),
                       (T("Call?"), "em_call.value"),
                       (T("OEM RRC"), "oem_ready.value"),
                       ]
        if r.function == "facility":
            list_fields.insert(0, "organisation_id")

        s3db.configure("org_facility",
                       crud_form = crud_form,
                       # Defaults seem OK for now
                       #filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            mine = r.get_vars.get("mine")
            if mine:
                from s3 import FS
                _filter = (FS("organisation_id") == current.auth.user.organisation_id)
                r.resource.add_filter(_filter)
                s3.crud_strings["org_facility"].title_list = T("My Facilities")

            return result
        s3.prep = custom_prep

        attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_org_facility_controller = customise_org_facility_controller

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3LocationSelector

        s3db = current.s3db

        # Filtered components
        s3db.add_components("org_organisation",
                            org_facility = ({"name": "main_facility",
                                             "joinby": "organisation_id",
                                             "filterby": {"main_facility": True},
                                             "multiple": False,
                                             },
                                             ),
                            org_organisation_tag = ({"name": "org_id",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "org_id"},
                                                     "multiple": False,
                                                     },
                                                    {"name": "congregants",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "congregants"},
                                                     "multiple": False,
                                                     },
                                                    {"name": "clergy_staff",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "clergy_staff"},
                                                     "multiple": False,
                                                     },
                                                    {"name": "lay_staff",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "lay_staff"},
                                                     "multiple": False,
                                                     },
                                                    {"name": "religious_staff",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "religious_staff"},
                                                     "multiple": False,
                                                     },
                                                    {"name": "volunteers",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "volunteers"},
                                                     "multiple": False,
                                                     },
                                                    {"name": "board",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "board"},
                                                     "multiple": False,
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

        main_facility = components_get("main_facility")
        mftable = main_facility.table
        mftable.name.default = "Main" # NOT_NULL field
        mftable.location_id.widget = S3LocationSelector(levels = False,
                                                        show_address = True,
                                                        show_postcode = False,
                                                        show_map = False,
                                                        )


        def postprocess(form):
            # Set Facility Name to Org name
            form_vars_get = form.vars.get
            ftable = s3db.org_facility
            query = (ftable.organisation_id == form_vars_get("id")) & \
                    (ftable.name == "Main")
            current.db(query).update(name = form_vars_get("name"))

        if not current.auth.s3_logged_in():
            # Simplified Form
            from s3 import S3SQLCustomForm

            s3db.gis_location.addr_street.label = T("Address of Organization or House of Worship")

            crud_form = S3SQLCustomForm((T("Formal Name of Organization or House of Worship"), "name"),
                                        ("", "main_facility.location_id"),
                                        postprocess = postprocess
                                        )

            s3db.configure("org_organisation",
                           crud_form = crud_form,
                           )

            return

        from gluon import IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE

        from s3 import IS_INT_AMOUNT, \
                       S3Represent, \
                       S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        s3db.gis_location.addr_street.label = T("Facility Address")

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

        orgtype = components_get("organisation_type")
        orgtype.configure(hierarchy_levels = ["Religion",
                                              "Faith Tradition",
                                              "Denomination",
                                              "Judicatory Body",
                                              ],
                          )

        s3db.org_organisation_organisation_type.organisation_type_id.represent = S3Represent(lookup = "org_organisation_type",
                                                                                             hierarchy = "%s, %s"
                                                                                             )

        crud_fields = ["name",
                       (T("Organization ID"), "org_id.value"),
                       S3SQLInlineLink("organisation_type",
                                       field = "organisation_type_id",
                                       label = "", #T("Religion"),
                                       multiple = False,
                                       widget = "cascade",
                                       leafonly = False,
                                       #cascade = True,
                                       represent = S3Represent(lookup = "org_organisation_type"),
                                       ),
                       S3SQLInlineComponent(
                            "facebook",
                            name = "facebook",
                            label = T("Facebook"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = {"field": "contact_method",
                            #            "options": "FACEBOOK",
                            #            },
                            ),
                       ("", "main_facility.location_id"),
                       "website",
                       # Not a multiple=False component
                       #(T("Facebook"), "facebook.value"),
                       S3SQLInlineComponent(
                            "facebook",
                            name = "facebook",
                            label = T("Facebook"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = {"field": "contact_method",
                            #            "options": "FACEBOOK",
                            #            },
                            ),
                       (T("# Congregants"), "congregants.value"),
                       (T("# Clergy Staff"), "clergy_staff.value"),
                       (T("# Lay Staff"), "lay_staff.value"),
                       (T("# Religious Staff"), "religious_staff.value"),
                       (T("# Volunteers"), "volunteers.value"),
                       (T("# C. Board"), "board.value"),
                       (T("Internet Access"), "internet.value"),
                       "comments",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields,
                                    postprocess = postprocess
                                    )

        from s3 import S3HierarchyFilter, S3LocationFilter, S3TextFilter#, S3OptionsFilter
        filter_widgets = [
            S3TextFilter(["name", "org_id.value"],
                         label = T("Search"),
                         comment = T("Search by organization name or ID. You can use * as wildcard."),
                         _class = "filter-search",
                         ),
            S3HierarchyFilter("organisation_organisation_type.organisation_type_id",
                              label = False, #T("Religion"),
                              widget = "cascade",
                              leafonly = False,
                              cascade = True,
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
                           (T("Facility Address"), "main_facility.location_id"),
                           (T("Date Registered"), "created_on"),
                           ]
        else:
            list_fields = [(T("ID"), "org_id.value"),
                           "name",
                           (T("Religion"), "organisation_organisation_type.organisation_type_id"),
                           (T("Facility Address"), "main_facility.location_id"),
                           ]

        s3db.configure("org_organisation",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if current.auth.s3_logged_in():
                mine = r.get_vars.get("mine")
                if mine:
                    from s3 import FS
                    _filter = (FS("id") == current.auth.user.organisation_id)
                    r.resource.add_filter(_filter)
                    s3.crud_strings["org_organisation"].title_list = T("My Organizations")
            else:
                r.method = "create"

            return result
        s3.prep = custom_prep

        attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET

        from s3 import S3LocationSelector, \
                       S3Represent, \
                       S3SQLCustomForm, S3SQLInlineComponent
        from s3layouts import S3PopupLink

        s3db = current.s3db

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Contact"),
            title_display = T("Contact Details"),
            title_list = T("Contacts"),
            title_update = T("Edit Contact Details"),
            label_list_button = T("List Contacts"),
            label_delete_button = T("Delete Contact"),
            msg_record_created = T("Contact added"),
            msg_record_modified = T("Contact details updated"),
            msg_record_deleted = T("Contact deleted"),
            msg_list_empty = T("No Contacts currently registered"))

        # Filtered components
        s3db.add_components("pr_person",
                            pr_person_tag = ({"name": "languages_spoken",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "languages_spoken"},
                                              },
                                             {"name": "other_languages",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "other_languages"},
                                              "multiple": False,
                                              },
                                             {"name": "religious_title",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "religious_title"},
                                              "multiple": False,
                                              },
                                             {"name": "position_title",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "position_title"},
                                              "multiple": False,
                                              },
                                             {"name": "em_comms",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "em_comms"},
                                              "multiple": False,
                                              },
                                             ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        languages_spoken = components_get("languages_spoken")
        f = languages_spoken.table.value
        language_opts = {1: T("English"),
                         2: T("Spanish"),
                         3: T("Chinese"),
                         4: T("Indic Languages (Hindi, Urdu or Gujarati)"),
                         5: T("Russian"),
                         }
        f.requires = IS_EMPTY_OR(IS_IN_SET(language_opts, multiple = True))
        f.represent = S3Represent(options = language_opts, multiple = True)

        em_comms = components_get("em_comms")
        f = em_comms.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        s3db.hrm_human_resource.job_title_id.comment = S3PopupLink(c = "hrm",
                                                                   f = "job_title",
                                                                   # Add this for usecases where this is no special controller for an options lookup
                                                                   #vars = {"prefix": "hrm",
                                                                   #        "parent": "human_resource",
                                                                   #        },
                                                                   label = T("Create Type"),
                                                                   title = T("Type"),
                                                                   tooltip = T("The contact's type"),
                                                                   )

        #s3db.gis_location.addr_street.label = T("Mailing Address")
        s3db.gis_location.addr_street.label = ""
        s3db.pr_address.location_id.widget = S3LocationSelector(levels = False,
                                                                show_address = True,
                                                                show_postcode = False,
                                                                show_map = False,
                                                                )

        crud_fields = ("first_name",
                       "middle_name",
                       "last_name",
                       #(T("ID"), "pe_label"),
                       S3SQLInlineComponent(
                            "human_resource",
                            name = "human_resource",
                            label = "",
                            multiple = False,
                            fields = ["organisation_id",
                                      (T("Type"), "job_title_id"),
                                      ],
                            ),
                       S3SQLInlineComponent(
                            "languages_spoken",
                            name = "languages_spoken",
                            label = T("Languages Spoken"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = {"field": "tag",
                            #            "options": "languages_spoken",
                            #            },
                            ),
                       (T("Other Languages"), "other_languages.value"),
                       (T("Religious Title"), "religious_title.value"),
                       (T("Position Title"), "position_title.value"),
                       S3SQLInlineComponent(
                            "address",
                            name = "address",
                            label = T("Mailing Address"),
                            #label = "",
                            multiple = False,
                            fields = [("", "location_id")],
                            #filterby = {"field": "type",
                            #            "options": 1,
                            #            },
                            ),
                       # Not a multiple=False component
                       #(T("Cell Phone"), "phone.value"),
                       S3SQLInlineComponent(
                            "phone",
                            name = "phone",
                            label = T("Cell Phone"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = {"field": "contact_method",
                            #            "options": "SMS",
                            #            },
                            ),
                       S3SQLInlineComponent(
                            "contact",
                            name = "work_phone",
                            label = T("Office Phone"),
                            multiple = False,
                            fields = [("", "value")],
                            filterby = {"field": "contact_method",
                                        "options": "WORK_PHONE",
                                        },
                            ),
                       S3SQLInlineComponent(
                            "contact",
                            name = "home_phone",
                            label = T("Emergency Phone"),
                            multiple = False,
                            fields = [("", "value")],
                            filterby = {"field": "contact_method",
                                        "options": "HOME_PHONE",
                                        },
                            ),
                       S3SQLInlineComponent(
                            "contact",
                            name = "fax",
                            label = T("Office Fax"),
                            multiple = False,
                            fields = [("", "value")],
                            filterby = {"field": "contact_method",
                                        "options": "FAX",
                                        },
                            ),
                       S3SQLInlineComponent(
                            "contact",
                            name = "personal_email",
                            label = T("Personal Email"),
                            multiple = False,
                            fields = [("", "value")],
                            filterby = ({"field": "contact_method",
                                         "options": "EMAIL",
                                         },
                                        {"field": "priority",
                                         "options": 2,
                                         },
                                        ),
                            ),
                       S3SQLInlineComponent(
                            "contact",
                            name = "work_email",
                            label = T("Work Email"),
                            multiple = False,
                            fields = [("", "value")],
                            filterby = ({"field": "contact_method",
                                         "options": "EMAIL",
                                         },
                                        {"field": "priority",
                                         "options": 1,
                                         },
                                        ),
                            ),
                       (T("Emergency Communications Decision-maker"), "em_comms.value"),
                       )

        crud_form = S3SQLCustomForm(*crud_fields)

        from s3 import S3TextFilter#, S3OptionsFilter, S3HierarchyFilter, S3LocationFilter,
        filter_widgets = [
            S3TextFilter(["first_name", "middle_name", "last_name"],
                         label = T("Search"),
                         comment = T("Search by person name. You can use * as wildcard."),
                         _class = "filter-search",
                         ),
            #S3HierarchyFilter("organisation_organisation_type.organisation_type_id",
            #                  label = T("Religion"),
            #                  ),
            #S3LocationFilter("org_facility.location_id",
            #                 label = T("Location"),
            #                 levels = gis_levels,
            #                 #hidden = True,
            #                 ),
            ]

        list_fields = ["first_name",
                       "middle_name",
                       "last_name",
                       (T("Type"), "human_resource.job_title_id"),
                       (T("Languages Spoken"), "languages_spoken.value"),
                       (T("Religious Title"), "religious_title.value"),
                       (T("Position Title"), "position_title.value"),
                       (T("ECDM"), "em_comms.value"),
                       ]

        s3db.configure("pr_person",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            mine = r.get_vars.get("mine")
            if mine:
                from s3 import FS
                _filter = (FS("human_resource.organisation_id") == current.auth.user.organisation_id)
                r.resource.add_filter(_filter)
                s3.crud_strings["pr_person"].title_list = T("My Contacts")

            elif r.get_vars.get("personal"):
                from gluon import URL
                from gluon.tools import redirect
                redirect(URL(args=[current.auth.s3_logged_in_person()]))

            return result
        s3.prep = custom_prep

        attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

# END =========================================================================
