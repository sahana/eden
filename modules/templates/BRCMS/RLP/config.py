# -*- coding: utf-8 -*-

"""
    Application Template for Rhineland-Palatinate (RLP) Crisis Management
    - used to register beneficiaries and their needs, and broker emergency assistance

    @license MIT
"""

from collections import OrderedDict

from gluon import current, URL, I, SPAN, \
                  IS_EMPTY_OR, IS_LENGTH, IS_NOT_EMPTY

from gluon.storage import Storage

from s3 import FS, IS_ONE_OF
from s3dal import original_tablename

from templates.RLPPTM.rlpgeonames import rlp_GeoNames

LSJV = "Landesamt für Soziales, Jugend und Versorgung"

# =============================================================================
def config(settings):

    T = current.T

    names = {"region": "Rheinland-Pfalz"}
    #settings.base.system_name = T("%(region)s Emergency Relief") % names
    #settings.base.system_name_short = T("%(region)s Emergency Relief") % names
    #settings.custom.homepage_title = T("Emergency Relief")

    settings.base.system_name = "Fluthilfe %(region)s" % names
    settings.base.system_name_short =  "Fluthilfe %(region)s" % names
    settings.custom.homepage_title = "Fluthilfe"

    # PrePopulate data
    settings.base.prepopulate.append("BRCMS/RLP")
    settings.base.prepopulate_demo.append("BRCMS/RLP/Demo")

    # Theme
    settings.base.theme = "RLP"
    settings.base.theme_layouts = "BRCMS/RLP"

    # Auth settings
    settings.auth.password_min_length = 8
    settings.auth.consent_tracking = True

    # Custom Logo
    settings.ui.menu_logo = URL(c="static", f="themes", args=["RLP", "img", "logo_rlp.png"])

    # Restrict the Location Selector to just certain countries
    settings.gis.countries = ("DE",)
    #gis_levels = ("L1", "L2", "L3")

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

    # -------------------------------------------------------------------------
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    # -------------------------------------------------------------------------
    # UI Settings
    settings.ui.calendar_clear_icon = True

    # -------------------------------------------------------------------------
    # BR Settings
    #
    settings.br.case_activity_status = True
    settings.br.case_activity_manager = False
    settings.br.case_activity_subject = True
    settings.br.case_activity_need_details = True
    settings.br.manage_assistance = False

    settings.br.needs_org_specific = False

    # -------------------------------------------------------------------------
    # ORG Settings
    #
    settings.org.default_organisation = LSJV

    # -------------------------------------------------------------------------
    # TODO Realm Rules
    #
    def brcms_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        db = current.db
        s3db = current.s3db

        tablename = original_tablename(table)

        realm_entity = 0

        if tablename == "pr_person":

            # Client records are owned by the organisation
            # the case is assigned to
            ctable = s3db.br_case
            query = (ctable.person_id == row.id) & \
                    (ctable.deleted == False)
            case = db(query).select(ctable.organisation_id,
                                    limitby = (0, 1),
                                    ).first()

            if case and case.organisation_id:
                realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                 case.organisation_id,
                                                 )

        elif tablename in ("pr_address",
                           "pr_contact",
                           "pr_contact_emergency",
                           "pr_image",
                           ):

            # Inherit from person via PE
            table = s3db.table(tablename)
            ptable = s3db.pr_person
            query = (table._id == row.id) & \
                    (ptable.pe_id == table.pe_id)
            person = db(query).select(ptable.realm_entity,
                                      limitby = (0, 1),
                                      ).first()
            if person:
                realm_entity = person.realm_entity

        elif tablename in ("br_appointment",
                           "br_case_activity",
                           "br_case_language",
                           "br_assistance_measure",
                           "br_note",
                           "pr_group_membership",
                           "pr_person_details",
                           "pr_person_tag",
                           ):

            # Inherit from person via person_id
            table = s3db.table(tablename)
            ptable = s3db.pr_person
            query = (table._id == row.id) & \
                    (ptable.id == table.person_id)
            person = db(query).select(ptable.realm_entity,
                                      limitby = (0, 1),
                                      ).first()
            if person:
                realm_entity = person.realm_entity

        elif tablename == "br_case_activity_update":

            # Inherit from case activity
            table = s3db.table(tablename)
            atable = s3db.br_case_activity
            query = (table._id == row.id) & \
                    (atable.id == table.case_activity_id)
            activity = db(query).select(atable.realm_entity,
                                        limitby = (0, 1),
                                        ).first()
            if activity:
                realm_entity = activity.realm_entity

        elif tablename == "br_assistance_measure_theme":

            # Inherit from measure
            table = s3db.table(tablename)
            mtable = s3db.br_assistance_measure
            query = (table._id == row.id) & \
                    (mtable.id == table.measure_id)
            activity = db(query).select(mtable.realm_entity,
                                        limitby = (0, 1),
                                        ).first()
            if activity:
                realm_entity = activity.realm_entity

        elif tablename == "pr_group":

            # No realm-entity for case groups
            table = s3db.pr_group
            query = table._id == row.id
            group = db(query).select(table.group_type,
                                     limitby = (0, 1),
                                     ).first()
            if group and group.group_type == 7:
                realm_entity = None

        elif tablename == "project_task":

            # Inherit the realm entity from the assignee
            assignee_pe_id = row.pe_id
            instance_type = s3db.pr_instance_type(assignee_pe_id)
            if instance_type:
                table = s3db.table(instance_type)
                query = table.pe_id == assignee_pe_id
                assignee = db(query).select(table.realm_entity,
                                            limitby = (0, 1),
                                            ).first()
                if assignee and assignee.realm_entity:
                    realm_entity = assignee.realm_entity

            # If there is no assignee, or the assignee has no
            # realm entity, fall back to the user organisation
            if realm_entity == 0:
                auth = current.auth
                user_org_id = auth.user.organisation_id if auth.user else None
                if user_org_id:
                    realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                     user_org_id,
                                                     )
        return realm_entity

    settings.auth.realm_entity = brcms_realm_entity

    # -------------------------------------------------------------------------
    def customise_cms_post_resource(r, tablename):

        s3db = current.s3db

        table = s3db.cms_post

        from s3 import S3SQLCustomForm, \
                       S3SQLInlineComponent, \
                       S3SQLInlineLink, \
                       s3_text_represent

        field = table.body
        field.represent = lambda v, row=None: \
                          s3_text_represent(v, lines=20, _class = "cms-item-body")

        record = r.record
        if r.tablename == "cms_series" and \
           record and record.name == "Announcements":
            table = s3db.cms_post
            field = table.priority
            field.readable = field.writable = True

            crud_fields = ["name",
                           "body",
                           "priority",
                           "date",
                           "expired",
                           S3SQLInlineLink("roles",
                                           label = T("Roles"),
                                           field = "group_id",
                                           ),
                           ]
            list_fields = ["date",
                           "priority",
                           "name",
                           "body",
                           "post_role.group_id",
                           "expired",
                           ]
            orderby = "cms_post.date desc"
        else:
            crud_fields = ["name",
                           "body",
                           "date",
                           S3SQLInlineComponent("document",
                                                name = "file",
                                                label = T("Attachments"),
                                                fields = ["file", "comments"],
                                                filterby = {"field": "file",
                                                            "options": "",
                                                            "invert": True,
                                                            },
                                                ),
                           "comments",
                           ]
            list_fields = ["post_module.module",
                           "post_module.resource",
                           "name",
                           "date",
                           "comments",
                           ]
            orderby = "cms_post.name"

        s3db.configure("cms_post",
                       crud_form = S3SQLCustomForm(*crud_fields),
                       list_fields = list_fields,
                       orderby = orderby,
                       )

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -----------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            table = r.table
            context = r.get_vars.get("resource")
            if context == "Privacy":
                page = URL(c="default", f="index", args=["privacy"])
                r.resource.configure(create_next = page,
                                     update_next = page,
                                     )
                table.name.default = "Privacy Notice"
            elif context == "Legal":
                page = URL(c="default", f="index", args=["legal"])
                r.resource.configure(create_next = page,
                                     update_next = page,
                                     )
                table.name.default = "Legal Notice"
            return result
        s3.prep = prep

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller

    # -------------------------------------------------------------------------
    def customise_br_home():
        """ Do not redirect to person-controller """

        return {"module_name": T("Current Needs"),
                }

    settings.customise_br_home = customise_br_home

    # -------------------------------------------------------------------------
    def chargeable_warning(v, row=None):
        """ Visually enhanced representation of chargeable-flag """

        if v:
            return SPAN(T("yes"),
                        I(_class = "fa fa-exclamation-triangle"),
                        _class = "charge-warn",
                        )
        else:
            return SPAN(T("no"),
                        _class = "free-hint",
                        )

    # -------------------------------------------------------------------------
    def customise_br_assistance_offer_controller(**attr):

        db = current.db
        auth = current.auth
        s3db = current.s3db

        s3 = current.response.s3

        is_event_manager = auth.s3_has_role("EVENT_MANAGER")
        org_role = is_event_manager or auth.s3_has_roles(("CASE_MANAGER", "RELIEF_PROVIDER"))

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource
            table = resource.table

            # Check perspective
            mine = r.function == "assistance_offer"
            if mine:
                # Adjust list title, allow last update info
                title_list = T("Our Relief Offers") if org_role else T("My Relief Offers")
                s3.hide_last_update = False

                # Filter for offers of current user
                pe_id = auth.user.pe_id if auth.user else None
                if pe_id:
                    query = (FS("pe_id") == pe_id)
                else:
                    query = (FS("pe_id").belongs([]))
                resource.add_filter(query)

                # Make editable
                resource.configure(insertable = True,
                                   editable = True,
                                   deletable = True,
                                   )
            else:
                # Adjust list title, hide last update info
                title_list = T("Current Relief Offers")
                s3.hide_last_update = not is_event_manager

                # Restrict data formats
                allowed = ("html", "iframe", "popup", "aadata", "plain", "geojson", "pdf", "xls")
                settings.ui.export_formats = ("pdf", "xls")
                if r.representation not in allowed:
                    r.error(403, current.ERROR.NOT_PERMITTED)

                # Make read-only
                resource.configure(insertable = False,
                                   editable = is_event_manager,
                                   deletable = is_event_manager,
                                   )

            s3.crud_strings["br_assistance_offer"]["title_list"] = title_list

            from s3 import S3LocationFilter, \
                           S3LocationSelector, \
                           S3OptionsFilter, \
                           S3TextFilter, \
                           s3_get_filter_opts

            if not r.component:

                # Default Event
                field = table.event_id
                from .helpers import get_current_events
                events = get_current_events(r.record)
                if events:
                    dbset = db(s3db.event_event.id.belongs(events))
                    field.requires = IS_ONE_OF(dbset, "event_event.id",
                                               field.represent,
                                               )
                    field.default = events[0]
                    field.writable = len(events) != 1

                # Default Provider
                field = table.pe_id
                if not org_role:
                    pe_id = auth.user.pe_id if auth.user else None
                    if pe_id:
                        field.default = pe_id
                        field.readable = field.writable = False
                elif auth.s3_has_role("RELIEF_PROVIDER"):
                    # TODO Get managed orgs (offers only made by RELIEF_PROVIDER)
                    # if one: set org_pe_id
                    # otherwise: make selectable
                    pass
                elif is_event_manager:
                    field.writable = False

                # Address mandatory, Lx-only
                field = table.location_id
                requires = field.requires
                if isinstance(requires, IS_EMPTY_OR):
                    requires = requires.other
                field.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                                  required_levels = ("L1", "L2", "L3"),
                                                  show_address = False,
                                                  show_postcode = False,
                                                  show_map = False,
                                                  )

                # TODO End date mandatory
                # => default to 4 weeks from now

                # TODO Contact defaults
                # - Contact Email => default from user if CITIZEN
                # - Contact Phone number => default from user if CITIZEN

                field = table.chargeable
                field.represent = chargeable_warning

                from s3 import S3PriorityRepresent

                # Color-coded availability representation
                field = table.availability
                availability_opts = s3db.br_assistance_offer_availability
                field.represent = S3PriorityRepresent(dict(availability_opts),
                                                      {"AVL": "green",
                                                       "OCP": "amber",
                                                       "RTD": "black",
                                                       }).represent

                # Status only writable for EVENT_MANAGER
                # TODO default to NEW? or APPROVED?
                field = table.status
                field.writable = is_event_manager
                # Color-coded status representation
                status_opts = s3db.br_assistance_offer_status
                field.represent = S3PriorityRepresent(dict(status_opts),
                                                      {"NEW": "lightblue",
                                                       "APR": "green",
                                                       "BLC": "red",
                                                       }).represent

                # List configuration
                if not r.record:

                    # Filter for matching offers?
                    match = r.get_vars.get("match") == "1"
                    if not mine and match:
                        from .helpers import get_offer_filters
                        filters = get_offer_filters()
                        if filters:
                            resource.add_filter(filters)

                    # Filters
                    filter_widgets = [
                        S3TextFilter(["name",
                                      "description",
                                      ],
                                     label = T("Search"),
                                     ),
                        S3OptionsFilter("need_id",
                                        options = lambda: \
                                            s3_get_filter_opts("br_need",
                                                               translate = True,
                                                               ),
                                        ),
                        S3OptionsFilter("chargeable",
                                        cols = 2,
                                        hidden = mine,
                                        ),
                        ]

                    if not mine:
                        # Add location filter for all-offers perspective
                        filter_widgets.append(
                            S3LocationFilter("location_id",
                                             levels = ("L2", "L3"),
                                             ))

                    if mine or is_event_manager:
                        # Add filter for availability / status
                        filter_widgets.extend([
                            S3OptionsFilter("availability",
                                            options = OrderedDict(availability_opts),
                                            hidden = True,
                                            sort = False,
                                            cols = 3,
                                            ),
                            S3OptionsFilter("status",
                                            options = OrderedDict(status_opts),
                                            hidden = True,
                                            sort = False,
                                            cols = 3,
                                            ),
                            ])
                    else:
                        # Filter out unavailable or unapproved offers
                        today = current.request.utcnow.date()
                        query = (FS("availability") == "AVL") & \
                                (FS("status") == "APR") & \
                                ((FS("end_date") == None) | (FS("end_date") >= today))
                        resource.add_filter(query)

                    # List fields
                    list_fields = ["need_id",
                                   "name",
                                   "chargeable",
                                   "location_id$L3",
                                   "location_id$L2",
                                   "location_id$L1",
                                   "availability",
                                   "date",
                                   "end_date",
                                   ]
                    if mine or is_event_manager:
                        list_fields.append("status")

                    resource.configure(filter_widgets = filter_widgets,
                                       list_fields = list_fields,
                                       )

                    # Report options
                    if r.method == "report":
                        facts = ((T("Number of Relief Offers"), "count(id)"),
                                )
                        axes = ["need_id",
                                "location_id$L4",
                                "location_id$L3",
                                "location_id$L2",
                                "location_id$L1",
                                "availability",
                                "chargeable",
                                ]
                        default_rows = "need_id"
                        default_cols = "location_id$L3"

                        report_options = {
                            "rows": axes,
                            "cols": axes,
                            "fact": facts,
                            "defaults": {"rows": default_rows,
                                        "cols": default_cols,
                                        "fact": "count(id)",
                                        "totals": True,
                                        },
                            }
                        resource.configure(report_options=report_options)

            return result
        s3.prep = prep

        return attr

    settings.customise_br_assistance_offer_controller = customise_br_assistance_offer_controller

    # -------------------------------------------------------------------------
    def customise_br_case_activity_resource(r, tablename):

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        s3db = current.s3db
        table = s3db.br_case_activity

        # Can't change start date, always today
        field = table.date
        field.writable = False

        # Need type is mandatory
        field = table.need_id
        requires = field.requires
        if isinstance(requires, IS_EMPTY_OR):
            field.requires = requires.other

        # Subject is mandatory + limit length
        field = table.subject
        field.label = T("Short Description")
        field.requires = [IS_NOT_EMPTY(), IS_LENGTH(128)]

        # Location is visible, defaults to logged-in user's tracking location
        from .helpers import get_current_location
        from s3 import S3LocationSelector

        field = table.location_id
        field.readable = field.writable = True
        field.label = T("Place")
        field.default = get_current_location()
        field.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                          required_levels = ("L1", "L2", "L3"),
                                          show_address = False,
                                          show_postcode = False,
                                          show_map = False,
                                          )

        # Subheadings for CRUD form
        subheadings = {"date": T("Need Details"),
                       "location_id": T("Need Location"),
                       "status_id": T("Status"),
                       }
        s3db.configure("br_case_activity",
                       subheadings = subheadings,
                       )

        # CRUD Strings
        crud_strings["br_case_activity"] = Storage(
            label_create = T("Report Need"),
            title_display = T("Need Details"),
            title_list = T("Needs"),
            title_report = T("Needs Statistic"),
            title_update = T("Edit Need"),
            label_list_button = T("List Needs"),
            label_delete_button = T("Delete Need"),
            msg_record_created = T("Need added"),
            msg_record_modified = T("Need updated"),
            msg_record_deleted = T("Need deleted"),
            msg_list_empty = T("No Needs currently registered"),
            )

    settings.customise_br_case_activity_resource = customise_br_case_activity_resource

    # -------------------------------------------------------------------------
    def customise_br_case_activity_controller(**attr):

        auth = current.auth
        #s3db = current.s3db

        s3 = current.response.s3

        is_event_manager = auth.s3_has_role("EVENT_MANAGER")
        #org_role = is_event_manager or auth.s3_has_roles(("CASE_MANAGER", "RELIEF_PROVIDER"))

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource
            table = resource.table

            # Check perspective
            mine = r.function == "case_activity"
            crud_strings = s3.crud_strings["br_case_activity"]
            if mine:
                # Adjust list title, allow last update info
                crud_strings["title_list"] = T("My Needs")
                s3.hide_last_update = False

                logged_in_person = auth.s3_logged_in_person()

                # Limit to own activities
                if not r.record:
                    query = FS("person_id") == logged_in_person
                    resource.add_filter(query)

                # Set default beneficiary + hide it
                field = table.person_id
                field.default = logged_in_person
                field.readable = field.writable = False

                # Allow create/update/delete
                insertable = editable = deletable = True
            else:
                # Adjust list title, hide last update info
                crud_strings["title_list"] = T("Current Needs")
                s3.hide_last_update = not is_event_manager

                # Restrict data formats
                allowed = ("html", "iframe", "popup", "aadata", "plain", "geojson", "pdf", "xls")
                settings.ui.export_formats = ("pdf", "xls")
                if r.representation not in allowed:
                    r.error(403, current.ERROR.NOT_PERMITTED)

                # Limit to active activities
                # TODO filter by end-date too
                query = FS("status_id$is_closed") == False
                resource.add_filter(query)

                # Deny create, only event manager can update/delete
                insertable = False
                editable = deletable = is_event_manager


            resource.configure(insertable = insertable,
                               editable = editable,
                               deletable = deletable,
                               )

            if not r.component:

                # Hide irrelevant fields
                for fn in ("person_id", "activity_details", "outcome", "priority"):
                    field = table[fn]
                    field.readable = field.writable = False

                # List fields
                list_fields = ["date",
                               "need_id",
                               "subject",
                               "location_id$L4",
                               "location_id$L3",
                               "location_id$L2",
                               "location_id$L1",
                               #"status_id",
                               ]
                if mine or is_event_manager:
                    list_fields.append("status_id")

                # Filters
                from s3 import S3DateFilter, S3TextFilter, S3LocationFilter, S3OptionsFilter, s3_get_filter_opts
                filter_widgets = [
                    S3TextFilter(["subject",
                                  "need_details",
                                  ],
                                 label = T("Search"),
                                 ),
                    S3OptionsFilter("need_id",
                                    options = lambda: \
                                        s3_get_filter_opts("br_need",
                                                           translate = True,
                                                           ),
                                    ),
                    S3LocationFilter("location_id",
                                     label = T("Place"),
                                     levels = ("L2", "L3"),
                                     ),
                    S3DateFilter("date",
                                 hidden = True,
                                 ),
                    ]
                if mine or is_event_manager:
                    filter_widgets.append(
                        S3OptionsFilter("status_id",
                                        options = lambda: \
                                            s3_get_filter_opts("br_case_activity_status",
                                                               translate = True,
                                                               ),
                                        hidden = True,
                                        ))

                resource.configure(filter_widgets = filter_widgets,
                                   list_fields = list_fields,
                                   orderby = "br_case_activity.date desc",
                                   )

                # Report options
                if r.method == "report":
                    facts = ((T("Number of Need Reports"), "count(id)"),
                             )
                    axes = ["need_id",
                            "location_id$L4",
                            "location_id$L3",
                            "location_id$L2",
                            "location_id$L1",
                            "status_id",
                            ]
                    default_rows = "need_id"
                    default_cols = "location_id$L3"

                    report_options = {
                        "rows": axes,
                        "cols": axes,
                        "fact": facts,
                        "defaults": {"rows": default_rows,
                                    "cols": default_cols,
                                    "fact": "count(id)",
                                    "totals": True,
                                    },
                        }
                    resource.configure(report_options=report_options)

            return result
        s3.prep = prep

        return attr

    settings.customise_br_case_activity_controller = customise_br_case_activity_controller

    # -------------------------------------------------------------------------
    # TODO customise event_event

    # -------------------------------------------------------------------------
    # TODO customise org_organisation
    # - have offices and staff, nothing else

    # -------------------------------------------------------------------------
    def person_onaccept(form):

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        # Get the record
        table = s3db.pr_person
        query = (table.id == record_id)
        record = db(query).select(table.id,
                                  table.pe_label,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return

        if not record.pe_label:
            record.update_record(pe_label="C-%07d" % record_id)
            s3db.update_super(table, record)

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db

        # Custom callback to assign an ID
        s3db.add_custom_callback("pr_person", "onaccept", person_onaccept)

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            from s3 import S3SQLCustomForm, \
                           S3SQLInlineComponent, \
                           StringTemplateParser

            # Determine order of name fields
            NAMES = ("first_name", "middle_name", "last_name")
            keys = StringTemplateParser.keys(settings.get_pr_name_format())
            name_fields = [fn for fn in keys if fn in NAMES]

            # TODO Customise for br
            if r.controller == "br":

                if not current.auth.s3_has_role("CASE_MANAGER"):
                    ctable = s3db.br_case
                    field = ctable.organisation_id
                    field.default = settings.get_org_default_organisation()

            elif r.controller == "default":
                # Personal profile (default/person)
                if not r.component:

                    # Last name is required
                    table = r.resource.table
                    table.last_name.requires = IS_NOT_EMPTY()

                    # Custom Form
                    crud_fields = name_fields
                    address = S3SQLInlineComponent(
                                    "address",
                                    label = T("Current Address"),
                                    fields = [("", "location_id")],
                                    filterby = {"field": "type",
                                                "options": "1",
                                                },
                                    link = False,
                                    multiple = False,
                                    )
                    crud_fields.append(address)
                    r.resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                         deletable = False,
                                         )
            return result
        s3.prep = prep

        # Custom rheader
        if current.request.controller == "default":
            from .rheaders import rlpcm_profile_rheader
            attr["rheader"] = rlpcm_profile_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller


# END =========================================================================
