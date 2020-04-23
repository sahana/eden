# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

from s3 import FS

def config(settings):
    """
        Template settings: 'Skeleton' designed to be copied to quickly create
                           custom templates

        All settings which are to configure a specific template are located
        here. Deployers should ideally not need to edit any other files outside
        of their template folder.
    """

    T = current.T

    purpose = {"event": "COVID-19"}
    settings.base.system_name = T("%(event)s Crisis Management") % purpose
    settings.base.system_name_short = T("%(event)s Crisis Management") % purpose

    # PrePopulate data
    settings.base.prepopulate += ("RLP",)
    settings.base.prepopulate_demo.append("RLP/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "RLP"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/<templatename>/img/logo.png" % current.request.application

    # Authentication settings
    # No self-registration
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    #settings.auth.registration_link_user_to = ["staff"]
    #settings.auth.registration_link_user_to_default = ["staff"]

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("DE",)
    gis_levels = ("L1", "L2", "L3")
    # Uncomment to display the Map Legend as a floating DIV, so that it is visible on Summary Map
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("en", "English"),
       ("de", "German"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "de"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.timezone = "Europe/Berlin"
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
    settings.security.policy = 7

    # -------------------------------------------------------------------------
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    # -------------------------------------------------------------------------
    settings.org.projects_tab = False

    # -------------------------------------------------------------------------
    # Custom group types for volunteer pools
    #
    pool_types = {21: T("Open Pool"),
                  22: T("Managed Pool"),
                  }
    pool_type_ids = list(pool_types.keys())

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # TODO is this needed?
        s3db.add_components("org_organisation",
                            pr_group = {"name": "pool",
                                        "link": "org_organisation_team",
                                        "joinby": "organisation_id",
                                        "key": "group_id",
                                        "filterby": {"group_type": pool_type_ids,
                                                     },
                                        "actuate": "replace",
                                        },
                            )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        s3db = current.s3db

        s3db.add_components("org_organisation",
                            pr_group = {"name": "pool",
                                        "link": "org_organisation_team",
                                        "joinby": "organisation_id",
                                        "key": "group_id",
                                        "filterby": {"group_type": pool_type_ids,
                                                     },
                                        "actuate": "replace",
                                        },
                            )

        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "human_resource":
                # Show staff only (not volunteers)
                r.component.add_filter(FS("type") == 1)

                # TODO adjust list_fields to what is necessary
                # TODO use simplified form


            return result
        s3.prep = custom_prep

        # Custom rheader
        attr = dict(attr)
        attr["rheader"] = rlp_org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_pr_group_resource(r, tablename):

        if r.tablename == "org_organisation":

            table = r.component.table

            from gluon import IS_IN_SET
            from s3 import S3Represent

            #table = s3db.pr_group
            field = table.group_type
            field.label = T("Pool Type")
            field.default = 22
            field.requires = IS_IN_SET(pool_types, zero=None)
            field.represent = S3Represent(options = pool_types)

            field = table.name
            field.label = T("Pool Title")

            field = table.description
            field.readable = field.writable = False

            # TODO embed contact information for pool

    settings.customise_pr_group_resource = customise_pr_group_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_membership_resource(r, tablename):

        component = r.component

        if component and component.alias == "pool_membership":

            table = component.table

            # Limit group selector to pools the person is not a member of yet
            field = table.group_id
            from s3 import IS_ONE_OF
            gtable = current.s3db.pr_group
            mtable = current.s3db.pr_group_membership
            query = (gtable.group_type.belongs(pool_type_ids)) & (mtable.id == None)
            left = mtable.on((mtable.group_id == gtable.id) & \
                             (mtable.person_id == r.id) & \
                             (mtable.deleted == False))
            dbset = current.db(query)
            field.requires = IS_ONE_OF(dbset, "pr_group.id", field.represent,
                                       left = left,
                                       )

            # Hide add-form if already member in all pools
            if len(dbset.select(gtable.id, left=left)) == 0:
                component.configure(insertable=False)

            # Custom label, use drop-down not autocomplete, no add-link
            field.label = T("Pool")
            field.widget = None
            field.comment = None

            # Hide group_head box
            field = table.group_head
            field.readable = field.writable = False

            # Hide comments (not needed here)
            field = table.comments
            field.readable = field.writable = False

            # Custom table configuration for pool membership
            component.configure(list_fields = ["group_id",
                                               # TODO show pool type (needs S3Represent)
                                               #"group_id$group_type",
                                               ],
                                editable = False,
                                )

    settings.customise_pr_group_membership_resource = customise_pr_group_membership_resource

    # -------------------------------------------------------------------------
    #def customise_pr_person_resource(r, tablename):
    #    pass
    #
    #settings.customise_pr_person_resource = customise_pr_person_resource
    # -------------------------------------------------------------------------
    def get_pools():

        db = current.db
        s3db = current.s3db

        gtable = s3db.pr_group
        query = (gtable.group_type.belongs(pool_type_ids)) & \
                (gtable.deleted == False)
        rows = db(query).select(gtable.id,
                                gtable.name,
                                cache = s3db.cache,
                                )

        return {row.id: row.name for row in rows}

    # -------------------------------------------------------------------------
    def use_person_custom_components():
        """
            Define custom components of pr_person
            - membership in volunteer pool (group_membership)
            - recruitment request (req_need)
        """

        s3db = current.s3db

        pools = get_pools()
        pool_ids = list(pools.keys())

        s3db.add_components("pr_pentity",
                            pr_address = {"name": "current_address",
                                          "joinby": "pe_id",
                                          "filterby": {"type": 1},
                                          "multiple": False,
                                          },
                            )

        s3db.add_components("pr_person",
                            hrm_human_resource = {"name": "volunteer_record",
                                                  "joinby": "person_id",
                                                  "filterby": {"type": 2},
                                                  "multiple": False,
                                                  },
                            pr_group = {"name": "pool",
                                        "link": "pr_group_membership",
                                        "joinby": "person_id",
                                        "key": "group_id",
                                        "filterby": {"group_type": pool_type_ids},
                                        "multiple": False,
                                        },
                            pr_group_membership = {"name": "pool_membership",
                                                   "joinby": "person_id",
                                                   "filterby": {"group_id": pool_ids},
                                                   "multiple": False,
                                                   },
                            req_need = {"link": "req_need_person",
                                        "joinby": "person_id",
                                        "key": "need_id",
                                        "actuate": "replace",
                                        },
                            )

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        # Enable bigtable features
        settings.base.bigtable = True

        use_person_custom_components()

        standard_prep = s3.prep
        def custom_prep(r):

            result = True

            if r.controller == "vol":

                resource = r.resource
                from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

                # Filter to volunteers only
                resource.add_filter(FS("volunteer_record.id") != None)

                # TODO If not COORDINATOR:
                # - filter to pool-listed volunteers

                # HR type defaults to volunteer (already done in controller)
                #hrtable = s3db.hrm_human_resource
                #hrtable.type.default = 2

                # Custom Form
                crud_fields = ["volunteer_record.organisation_id",
                               S3SQLInlineLink("pool",
                                               field = "group_id",
                                               multiple = False,
                                               header = False,
                                               search = False,
                                               ),
                               # name-fields
                               "date_of_birth",
                               S3SQLInlineComponent(
                                        "address",
                                        label = T("Current Address"),
                                        fields = [("", "location_id")],
                                        filterby = {"field": "type",
                                                    "options": "1",
                                                    },
                                        link = False,
                                        multiple = False,
                                        ),
                               S3SQLInlineComponent(
                                        "contact",
                                        fields = [("", "value")],
                                        filterby = {"field": "contact_method",
                                                    "options": "EMAIL",
                                                    },
                                        label = T("Email"),
                                        multiple = False,
                                        name = "email",
                                        ),
                               S3SQLInlineComponent(
                                        "contact",
                                        fields = [("", "value")],
                                        filterby = {"field": "contact_method",
                                                    "options": "SMS",
                                                    },
                                        label = T("Mobile Phone"),
                                        multiple = False,
                                        name = "phone",
                                        ),
                               S3SQLInlineLink("occupation_type",
                                               field = "occupation_type_id",
                                               ),
                               ]

                list_fields = [# name-fields
                               (T("Age"), "age"),
                               "gender",
                               "occupation_type_person.occupation_type_id",
                               (T("Place of Residence"), "current_address.location_id$L3"),
                               (T("Pool"), "pool_membership.group_id"),
                               ]

                # Insert name fields in name-format order
                NAMES = ("first_name", "middle_name", "last_name")
                from s3 import StringTemplateParser
                keys = StringTemplateParser.keys(settings.get_pr_name_format())
                name_fields = [fn for fn in keys if fn in NAMES]
                crud_fields[2:2] = name_fields
                list_fields[0:0] = name_fields

                # Filters
                from s3 import S3AgeFilter, S3OptionsFilter, S3TextFilter

                filter_widgets = [
                    # TODO Hide text filter unless COORDINATOR
                    S3TextFilter(["first_name",
                                  "middle_name",
                                  "last_name",
                                  ],
                                 label = T("Search"),
                                 ),
                    S3AgeFilter("date_of_birth",
                                label = T("Age"),
                                minimum = 12,
                                maximum = 90,
                                ),
                    S3OptionsFilter("pool_membership.group_id",
                                    label = T("Pool"),
                                    options = get_pools,
                                    hidden = True,
                                    ),
                    # TODO filter by home address
                    # TODO filter by profession
                    # TODO filter by competency
                    ]

                resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                   filter_widgets = filter_widgets,
                                   list_fields = list_fields,
                                   # Extra fields for computation of virtual fields
                                   extra_fields = ["date_of_birth",
                                                   ],
                                   )

                if r.component_name == "delegation":

                    # HRMANAGERs and ADMINs see the list
                    if not current.auth.s3_has_role("HRMANAGER") and \
                       r.interactive and r.method is None and not r.component_id:
                        r.method = "organize"

                # TODO adapt CRUD-strings (=>volunteers)

            elif callable(standard_prep):
                result = standard_prep(r)

            return result
        s3.prep = custom_prep

        # Custom rheader in vol-perspective
        if current.request.controller == "vol":
            attr = dict(attr)
            attr["rheader"] = rlp_vol_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller
    # -------------------------------------------------------------------------
    def delegation_workflow(table, record):
        """
            Enforce workflow in delegation records

            @param table: the Table used in the request (can be aliased)
            @param record: the delegation record
        """

        workflow = {"REQ": ("REQ", "APPR", "DECL", "CANC"),
                    "APPR": ("APPR", "CANC", "IMPL"),
                    "IMPL": ("IMPL", "CANC",),
                    }

        status = record.status
        next_status = workflow.get(status)

        field = table.status
        if not next_status:
            # Final status => can't be changed
            field.writable = False
        else:
            requires = field.requires
            theset = []
            labels = []
            for index, option in enumerate(requires.theset):
                if option in next_status:
                    theset.append(option)
                    labels.append(requires.labels[index])
            requires.theset = theset
            requires.labels = labels
            field.writable = True

        # Can only change dates while not processed yet
        if status != "REQ":
            field = table.date
            field.writable = False
            field = table.end_date
            field.writable = False

        # Can never change person or organisation
        field = table.person_id
        field.writable = False
        field = table.organisation_id
        field.writable = False

    # -------------------------------------------------------------------------
    def customise_hrm_delegation_resource(r, tablename):

        s3db = current.s3db

        # Basic organizer configuration
        organize = {"start": "date",
                    "end": "end_date",
                    "color": "status",
                    "colors": {"REQ":  "#d554a2",
                               "APPR": "#408d40",
                               "DECL": "#303030",
                               "CANC": "#d0d0d0",
                               "IMPL": "#40879c",
                               },
                    }

        if r.method == "organize":
            table = s3db.hrm_delegation

            # Cannot change dates with the organizer
            # - but may be possible in the popup
            field = table.date
            field.writable = False
            field = table.end_date
            field.writable = False

            # Cannot create delegations in the organizer
            s3db.configure("hrm_delegation", insertable = False)

        if r.tablename == "pr_person" and r.component:
            # On tab of volunteer file

            if r.component_id:
                r.component.load()
                record = r.component._rows[0]
                delegation_workflow(r.component.table, record)
                # TODO cannot change organisation
                # TODO can only change dates while status is REQ/INVT/APPL
                pass

            organize["title"] = "organisation_id"
            organize["description"] = ["date",
                                       "end_date",
                                       "status",
                                       ]
        else:
            # Delegation controller or popup
            record = r.record
            if record:
                delegation_workflow(r.resource.table, record)

            # Cannot insert here
            s3db.configure("hrm_delegation",
                           insertable = False,
                           )

            organize["title"] = "person_id"
            organize["description"] = ["organisation_id",
                                       "date",
                                       "end_date",
                                       "status",
                                       ]

        # Reconfigure
        s3db.configure("hrm_delegation",
                       organize = organize,
                       deletable = False,
                       )

    settings.customise_hrm_delegation_resource = customise_hrm_delegation_resource

    # -------------------------------------------------------------------------
    def customise_hrm_delegation_controller(**attr):

        s3 = current.response.s3

        # Must not create or delete delegations from here
        current.s3db.configure("hrm_delegation",
                               insertable = False,
                               )

        #standard_prep = s3.prep
        #def custom_prep(r):
        #
        #    # Call standard prep
        #    result = standard_prep(r) if callable(standard_prep) else True
        #
        #    return result
        #s3.prep = custom_prep

        return attr

    settings.customise_hrm_delegation_controller = customise_hrm_delegation_controller
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
        # HRM is required for access to default realm permissions
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
        #  name_nice = T("Content Management"),
        #  #description = "Content Management System",
        #  restricted = True,
        #  module_type = 10,
        #)),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        #("msg", Storage(
        #    name_nice = T("Messaging"),
        #    #description = "Sends & Receives Alerts via Email & SMS",
        #    restricted = True,
        #    # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        #    module_type = None,
        #)),
        #("supply", Storage(
        #    name_nice = T("Supply Chain Management"),
        #    #description = "Used within Inventory Management, Request Management and Asset Management",
        #    restricted = True,
        #    module_type = None, # Not displayed
        #)),
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = 4
        #)),
        #("asset", Storage(
        #    name_nice = T("Assets"),
        #    #description = "Recording and Assigning Assets",
        #    restricted = True,
        #    module_type = 5,
        #)),
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
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("br", Storage(
        #   name_nice = T("Beneficiary Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

# =============================================================================
def rlp_vol_rheader(r, tabs=None):
    # TODO custom rheader for vol/person

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_fullname, s3_rheader_resource, S3ResourceHeader
    auth = current.auth

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "pr_person":

            # TODO extract pool membership and pool type

            if not tabs:
                tabs = [(T("Personal Data"), None),
                        ]
                # TODO show address and contacts tab if allows by any team
                if auth.s3_has_role("COORDINATOR"):
                    tabs.extend([(T("Addresses"), "address"),
                                 (T("Contact Information"), "contacts"),
                                 (T("Pool"), "pool_membership"),
                                 ])
                tabs.extend([(T("Competencies"), "competency"),
                             (T("Recruitment"), "delegation"),
                             ])

            rheader_fields = [[(T("Name"), s3_fullname),
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# =============================================================================
def rlp_org_rheader(r, tabs=None):
    """ ORG custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "org_organisation":

            if not tabs:
                tabs = [(T("Organisation"), None),
                        (T("Administrative Offices"), "office"),
                        (T("Staff"), "human_resource"),
                        (T("Volunteer Pools"), "pool"),
                        ]

            rheader_fields = [["name",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader


# =============================================================================
def rlp_req_rheader(r, tabs=None):
    """ REQ custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "req_need":

            if not tabs:
                tabs = [(T("Request Details"), None),
                        ]

            # TODO show requesting organisation, date and status instead?
            rheader_fields = [["name",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader


# END =========================================================================
