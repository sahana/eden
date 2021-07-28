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
    settings.custom.homepage_title = "Fluthilfe-Portal"

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

    settings.cms.hide_index = False

    # Do not send standard welcome emails (using custom function)
    settings.auth.registration_welcome_email = False

    settings.auth.realm_entity_types = ("org_organisation",)
    settings.auth.privileged_roles = {"EVENT_MANAGER": "EVENT_MANAGER",
                                      "CITIZEN": "ADMIN",
                                      "RELIEF_PROVIDER": "RELIEF_PROVIDER",
                                      "MAP_ADMIN": "ADMIN",
                                      }

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
    settings.br.case_global_default_org = False
    settings.br.case_manager = False
    settings.br.household_size = False # True
    settings.br.case_address = True
    settings.br.case_language_details = False

    settings.br.case_activity_status = True
    settings.br.case_activity_manager = False
    settings.br.case_activity_subject = True
    settings.br.case_activity_need_details = True
    settings.br.manage_assistance = False

    settings.br.needs_org_specific = False

    settings.br.case_contacts_tab = True
    settings.br.case_id_tab = False
    settings.br.case_family_tab = False
    settings.br.case_activities = True
    settings.br.manage_assistance = False
    settings.br.assistance_tab = False

    settings.br.service_contacts = False
    settings.br.case_notes_tab = False
    settings.br.case_photos_tab = False
    settings.br.case_documents_tab = False

    # -------------------------------------------------------------------------
    # HRM Settings
    #
    settings.hrm.record_tab = False
    settings.hrm.staff_experience = False
    settings.hrm.teams = False
    settings.hrm.use_address = False
    settings.hrm.use_id = False
    settings.hrm.use_skills = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    # ORG Settings
    #
    settings.org.default_organisation = LSJV

    settings.custom.org_registration = True
    settings.custom.regional = ("Rheinland-Pfalz",
                                "Nordrhein-Westfalen",
                                "Hessen",
                                "Baden-Württemberg",
                                "Saarland",
                                )

    # -------------------------------------------------------------------------
    # Realm Rules
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

        #elif tablename == "br_case":
            # Owned by managing organisation (default)

        elif tablename in ("br_case_activity",
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

        #elif tablename == "br_assistance_offer":
            # Owned by the provider (pe_id, default)

        elif tablename == "br_direct_offer":
            # Direct offer inherits from offer via offer_id
            table = s3db.table(tablename)
            aotable = s3db.br_assistance_offer
            query = (table._id == row.id) & \
                    (aotable.id == table.offer_id)
            offer = db(query).select(aotable.realm_entity,
                                     limitby = (0, 1),
                                     ).first()
            if offer:
                realm_entity = offer.realm_entity

        elif tablename == "pr_group":

            # No realm-entity for case groups
            table = s3db.pr_group
            query = table._id == row.id
            group = db(query).select(table.group_type,
                                     limitby = (0, 1),
                                     ).first()
            if group and group.group_type == 7:
                realm_entity = None

        #elif tablename == "event_event":
            # Owned by the lead organisation (default)

        return realm_entity

    settings.auth.realm_entity = brcms_realm_entity

    # -------------------------------------------------------------------------
    def overview_stats_update():
        """
            Scheduler task to update the data files for the overview page
        """

        from .helpers import OverviewData
        OverviewData.update_data()

    settings.tasks.overview_stats_update = overview_stats_update

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
    def offer_onaccept(form):
        # TODO docstring

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
        table = s3db.br_assistance_offer
        query = (table.id == record_id)
        record = db(query).select(table.id,
                                  table.status,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return
        if record.status == "APR":
            # Look up all pending direct offers
            dotable = s3db.br_direct_offer
            query = (dotable.offer_id == record_id) & \
                    (dotable.notify == True) & \
                    (dotable.notified_on == None)
            pending = db(query).select(dotable.id)
            # TODO do this async?
            from .helpers import notify_direct_offer
            for direct_offer in pending:
                notify_direct_offer(direct_offer.id)

    # -------------------------------------------------------------------------
    def offer_date_dt_orderby(field, direction, orderby, left_joins):
        """
            When sorting offers by date, use created_on to maintain
            consistent order of multiple offers on the same date
        """

        sorting = {"table": field.tablename,
                   "direction": direction,
                   }
        orderby.append("%(table)s.date%(direction)s,%(table)s.created_on%(direction)s" % sorting)

    # -------------------------------------------------------------------------
    def customise_br_assistance_offer_resource(r, tablename):

        s3db = current.s3db

        table = s3db.br_assistance_offer

        # Configure fields
        from .helpers import ProviderRepresent
        from s3 import S3PriorityRepresent

        field = table.pe_id
        field.label = T("Provider")
        field.represent = ProviderRepresent()

        field = table.contact_phone
        field.label = T("Phone #")

        field = table.chargeable
        field.represent = chargeable_warning

        # Color-coded representation of availability/status
        field = table.availability
        availability_opts = s3db.br_assistance_offer_availability
        field.represent = S3PriorityRepresent(dict(availability_opts),
                                              {"AVL": "green",
                                               "OCP": "amber",
                                               "RTD": "black",
                                               }).represent
        field = table.status
        status_opts = s3db.br_assistance_offer_status
        field.represent = S3PriorityRepresent(dict(status_opts),
                                              {"NEW": "lightblue",
                                               "APR": "green",
                                               "BLC": "red",
                                               }).represent

        subheadings = {"need_id": T("Offer"),
                       "location_id": T("Place where help is provided"),
                       "contact_name": T("Contact Information"),
                       "availability": T("Availability and Status"),
                       }

        s3db.configure("br_assistance_offer",
                       # Default sort order: newest first
                       orderby = "br_assistance_offer.date desc, br_assistance_offer.created_on desc",
                       subheadings = subheadings,
                       )

        # Maintain consistent order for multiple assistance offers
        # on the same day (by enforcing created_on as secondary order criterion)
        field = table.date
        field.represent.dt_orderby = offer_date_dt_orderby

        # If the offer is created on direct offer tab, then pre-set the need_id and lock it
        need_id = r.get_vars.get("need_id")
        if need_id and need_id.isdigit():
            field = table.need_id
            field.default = int(need_id)
            if field.default:
                field.writable = False

        # Custom callback to notify pending direct offers upon approval
        s3db.add_custom_callback("br_assistance_offer",
                                 "onaccept",
                                 offer_onaccept,
                                 )

    settings.customise_br_assistance_offer_resource = customise_br_assistance_offer_resource

    # -------------------------------------------------------------------------
    def configure_offer_details(table):
        # TODO docstring/comments

        s3db = current.s3db

        from s3 import s3_fieldmethod
        from .helpers import OfferDetails

        table.place = s3_fieldmethod("place",
                                     OfferDetails.place,
                                     represent = OfferDetails.place_represent,
                                     )
        table.contact = s3_fieldmethod("contact",
                                       OfferDetails.contact,
                                       represent = OfferDetails.contact_represent,
                                       )
        s3db.configure("br_assistance_offer",
                       extra_fields = ["location_id$L3",
                                       "location_id$L2",
                                       "location_id$L1",
                                       "contact_name",
                                       "contact_phone",
                                       "contact_email",
                                       ],
                       )

    # -------------------------------------------------------------------------
    def customise_br_assistance_offer_controller(**attr):

        db = current.db
        auth = current.auth
        s3db = current.s3db

        s3 = current.response.s3

        is_event_manager = auth.s3_has_role("EVENT_MANAGER")
        is_relief_provider = auth.s3_has_role("RELIEF_PROVIDER")
        org_role = is_event_manager or is_relief_provider

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            get_vars = r.get_vars

            resource = r.resource
            table = resource.table

            from .helpers import get_current_events, \
                                 get_managed_orgs

            if is_relief_provider:
                providers = get_managed_orgs("RELIEF_PROVIDER")
            elif auth.user:
                providers = [auth.user.pe_id]
            else:
                providers = []

            # Check perspective
            viewing = r.viewing
            if viewing and viewing[0] == "br_case_activity":
                case_activity_id = viewing[1]
                direct_offers, mine = True, False
                # Must have update-permission for the case activity viewing
                if not auth.s3_has_permission("update", "br_case_activity",
                                              record_id = case_activity_id,
                                              c = "br",
                                              f = "case_activity",
                                              ):
                    r.unauthorised()
                # Filter to the context of the case activity viewing
                query = FS("direct_offer.case_activity_id") == case_activity_id
                resource.add_filter(query)
            else:
                direct_offers = False
                mine = r.function == "assistance_offer"

            if mine:
                # Adjust list title, allow last update info
                title_list = T("Our Relief Offers") if org_role else \
                             T("My Relief Offers")
                s3.hide_last_update = False

                # Filter for offers of current user
                if len(providers) == 1:
                    query = (FS("pe_id") == providers[0])
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
                title_list = T("Direct Offers") if direct_offers else \
                             T("Current Relief Offers")
                s3.hide_last_update = not is_event_manager

                # Restrict data formats
                allowed = ("html", "iframe", "popup", "aadata", "plain", "geojson", "pdf", "xls")
                if r.method in ("report", "filter"):
                    allowed += ("json",)
                settings.ui.export_formats = ("pdf", "xls")
                if r.representation not in allowed:
                    r.error(403, current.ERROR.NOT_PERMITTED)

                # URL pre-filter options
                match = not direct_offers and get_vars.get("match") == "1"
                show_pending = show_blocked = show_all = False
                if is_event_manager and not direct_offers:
                    if get_vars.get("pending") == "1":
                        show_pending = True
                        title_list = T("Pending Approvals")
                    elif get_vars.get("blocked") == "1":
                        show_blocked = True
                        title_list = T("Blocked Entries")
                    elif get_vars.get("all") == "1":
                        show_all = True
                        title_list = T("All Offers")
                elif match:
                    title_list = T("Matching Offers")

                # Make read-only
                writable = is_event_manager and not direct_offers
                resource.configure(insertable = False,
                                   editable = writable,
                                   deletable = writable,
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
                field.readable = not mine or org_role
                if len(providers) == 1:
                    field.default = providers[0]
                    field.writable = False
                elif providers:
                    etable = s3db.pr_pentity
                    dbset = db(etable.pe_id.belongs(providers))
                    field.requires = IS_ONE_OF(dbset, "pr_pentity.pe_id",
                                               field.represent,
                                               )
                    field.writable = mine
                elif is_event_manager:
                    field.writable = False

                # Address mandatory, Lx-only
                field = table.location_id
                requires = field.requires
                if isinstance(requires, IS_EMPTY_OR):
                    field.requires = requires.other
                field.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                                  required_levels = ("L1", "L2", "L3"),
                                                  filter_lx = settings.get_custom("regional"),
                                                  show_address = False,
                                                  show_postcode = False,
                                                  show_map = False,
                                                  )

                # TODO End date mandatory
                # => default to 4 weeks from now

                if not is_event_manager:
                    # Need type is mandatory
                    field = table.need_id
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other

                    # At least phone number is required
                    # - TODO default from user if CITIZEN
                    field = table.contact_phone
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other

                # Status only writable for EVENT_MANAGER
                field = table.status
                field.writable = is_event_manager

                if not r.record:

                    # Filters
                    if direct_offers:
                        filter_widgets = None
                    else:
                        from .helpers import OfferAvailabilityFilter, \
                                             get_offer_filters

                        # Apply availability filter
                        OfferAvailabilityFilter.apply_filter(resource, get_vars)

                        # Filter for matching offers?
                        if not mine and match:
                            filters = get_offer_filters()
                            if filters:
                                resource.add_filter(filters)

                        filter_widgets = [
                            S3TextFilter(["name",
                                          "refno",
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
                            availability_opts = s3db.br_assistance_offer_availability
                            status_opts = s3db.br_assistance_offer_status
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
                        if not mine:
                            # Add availability date range filter for all-offers perspective
                            filter_widgets.append(
                                OfferAvailabilityFilter("date",
                                                        label = T("Available"),
                                                        hidden = True,
                                                        ))

                    # Visibility Filter
                    if mine:
                        # Show all accessible
                        vquery = None
                    else:
                        # Filter out unavailable, unapproved and past offers
                        today = current.request.utcnow.date()
                        vquery = (FS("availability") == "AVL") & \
                                 (FS("status") == "APR") & \
                                 ((FS("end_date") == None) | (FS("end_date") >= today))
                        # Event manager can override this with URL options
                        if is_event_manager and not direct_offers:
                            if show_pending:
                                vquery = (FS("status") == "NEW")
                            elif show_blocked:
                                vquery = (FS("status") == "BLC")
                            elif show_all:
                                vquery = None
                    if vquery:
                        resource.add_filter(vquery)

                    # List fields
                    if not mine:
                        # All or direct offers
                        configure_offer_details(table)
                        list_fields = ["need_id",
                                       "name",
                                       (T("Place"), "place"),
                                       "pe_id",
                                       (T("Contact"), "contact"),
                                       "refno",
                                       "description",
                                       "chargeable",
                                       "availability",
                                       "date",
                                       "end_date",
                                       #"status"
                                       ]
                        if is_event_manager:
                            list_fields.append("status")
                    else:
                        # My/our offers
                        list_fields = ["need_id",
                                       "name",
                                       #"pe_id",
                                       "location_id$L3",
                                       #"location_id$L2",
                                       "location_id$L1",
                                       "refno",
                                       "chargeable",
                                       "availability",
                                       "date",
                                       "end_date",
                                       "status"
                                       ]
                        if org_role:
                            list_fields.insert(2, "pe_id")

                    resource.configure(filter_widgets = filter_widgets,
                                       list_fields = list_fields,
                                       )

                    # Report options
                    if r.method == "report":
                        facts = ((T("Number of Relief Offers"), "count(id)"),
                                 (T("Number of Providers"), "count(pe_id)"),
                                )
                        axes = ["need_id",
                                "location_id$L4",
                                "location_id$L3",
                                "location_id$L2",
                                "location_id$L1",
                                "availability",
                                "chargeable",
                                (T("Provider Type"), "pe_id$instance_type"),
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

            elif r.component_name == "direct_offer":

                # Perspective to manage direct-offer links for an offer

                # List fields
                list_fields = ["case_activity_id",
                               "case_activity_id$date",
                               "case_activity_id$location_id$L3",
                               "case_activity_id$location_id$L1",
                               (T("Need Status"), "case_activity_id$status_id"),
                               (T("Approval"), "offer_id$status"),
                               ]

                r.component.configure(list_fields = list_fields,
                                      # Can only read or delete here
                                      insertable = False,
                                      editable = False,
                                      )

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpcm_br_rheader
        attr["rheader"] = rlpcm_br_rheader

        return attr

    settings.customise_br_assistance_offer_controller = customise_br_assistance_offer_controller

    # -------------------------------------------------------------------------
    def activity_date_dt_orderby(field, direction, orderby, left_joins):
        """
            When sorting activities by date, use created_on to maintain
            consistent order of multiple activities on the same date
        """

        sorting = {"table": field.tablename,
                   "direction": direction,
                   }
        orderby.append("%(table)s.date%(direction)s,%(table)s.created_on%(direction)s" % sorting)

    # -------------------------------------------------------------------------
    def customise_br_case_activity_resource(r, tablename):

        # Case file or self-reporting?
        record = r.record
        case_file = r.tablename == "pr_person" and record
        ours = r.function == "case_activity" and \
                             current.auth.s3_has_roles(("RELIEF_PROVIDER", "CASE_MANAGER"))

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        s3db = current.s3db
        table = s3db.br_case_activity

        # Can't change start date, always today
        field = table.date
        field.writable = False
        # Maintain consistent order for multiple activities
        # on the same day (by enforcing created_on as secondary order criterion)
        field.represent.dt_orderby = activity_date_dt_orderby

        # Need type is mandatory
        field = table.need_id
        requires = field.requires
        if isinstance(requires, IS_EMPTY_OR):
            field.requires = requires.other

        # Subject is mandatory + limit length
        field = table.subject
        field.label = T("Short Description")
        field.requires = [IS_NOT_EMPTY(), IS_LENGTH(128)]

        # Location is visible
        from .helpers import get_current_location
        from s3 import S3LocationSelector

        field = table.location_id
        field.readable = field.writable = True
        field.label = T("Place")
        if case_file:
            # Defaults to beneficiary tracking location
            field.default = get_current_location(record.id)
        else:
            # Default to current user's tracking location
            field.default = get_current_location()
        field.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                          required_levels = ("L1", "L2", "L3"),
                                          filter_lx = settings.get_custom("regional"),
                                          show_address = False,
                                          show_postcode = False,
                                          show_map = False,
                                          )

        if case_file or ours:
            # Custom form to change field order
            from s3 import S3SQLCustomForm
            crud_fields = ["person_id",
                           "priority",
                           "date",
                           "need_id",
                           "subject",
                           "need_details",
                           "location_id",
                           "activity_details",
                           "outcome",
                           "status_id",
                           "comments",
                           ]
            s3db.configure("br_case_activity",
                           crud_form = S3SQLCustomForm(*crud_fields),
                           )
            # Subheadings for CRUD form
            subheadings = {"priority": T("Need Details"),
                           "location_id": T("Need Location"),
                           "activity_details": T("Support provided"),
                           "status_id": T("Status"),
                           }
        else:
            # Default form with mods per settings
            # Subheadings for CRUD form
            subheadings = {"date": T("Need Details"),
                           "location_id": T("Need Location"),
                           "status_id": T("Status"),
                           }
        s3db.configure("br_case_activity",
                       subheadings = subheadings,
                       # Default sort order: newest first
                       orderby = "br_case_activity.date desc, br_case_activity.created_on desc",
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

        db = current.db
        auth = current.auth
        s3db = current.s3db

        s3 = current.response.s3

        is_event_manager = auth.s3_has_role("EVENT_MANAGER")
        is_case_manager = auth.s3_has_roles(("RELIEF_PROVIDER", "CASE_MANAGER"))

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
                if is_case_manager:
                    crud_strings["title_list"] = T("Our Needs")
                else:
                    crud_strings["title_list"] = T("My Needs")
                s3.hide_last_update = False

                # Beneficiary requirements
                field = table.person_id
                field.writable = False
                if is_case_manager:
                    # Must add in case-file
                    field.readable = True
                    insertable = False
                else:
                    # Set default beneficiary + hide it
                    logged_in_person = auth.s3_logged_in_person()
                    field.default = logged_in_person
                    field.readable = False
                    if not r.record:
                        # Filter to own activities
                        query = FS("person_id") == logged_in_person
                        resource.add_filter(query)
                    insertable = True

                # Allow update/delete
                editable = deletable = True
            else:
                # Adjust list title, hide last update info
                crud_strings["title_list"] = T("Current Needs")
                s3.hide_last_update = not is_event_manager

                # Restrict data formats
                allowed = ("html", "iframe", "popup", "aadata", "plain", "geojson", "pdf", "xls")
                if r.method in ("report", "filter"):
                    allowed += ("json",)
                if r.method == "options":
                    allowed += ("s3json",)
                settings.ui.export_formats = ("pdf", "xls")
                if r.representation not in allowed:
                    r.error(403, current.ERROR.NOT_PERMITTED)

                # Limit to active activities
                today = current.request.utcnow.date()
                query = (FS("status_id$is_closed") == False) & \
                        ((FS("end_date") == None) | (FS("end_date") >= today))
                resource.add_filter(query)

                # Deny create, only event manager can update/delete
                insertable = False
                editable = deletable = is_event_manager


            resource.configure(insertable = insertable,
                               editable = editable,
                               deletable = deletable,
                               )

            if not r.component:

                if not mine or not is_case_manager:
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
                    if is_case_manager:
                        list_fields[1:1] = ("priority", "person_id")

                        # Represent person_id as link to case file
                        field = table.person_id
                        field.represent = s3db.pr_PersonRepresent(show_link=True)

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

            elif r.component_name == "direct_offer":

                if r.function != "activities":
                    # This perspective is not supported
                    r.error(403, current.ERROR.NOT_PERMITTED)

                # Perspective to list and add direct offers

                component = r.component

                # Show only approved offers
                query = (FS("offer_id$status") == "APR")
                component.add_filter(query)

                # List fields
                customise_br_assistance_offer_resource(r, "br_assistance_offer")
                list_fields = ["offer_id",
                               "offer_id$pe_id",
                               "offer_id$location_id$L3",
                               "offer_id$location_id$L1",
                               "offer_id$date",
                               "offer_id$end_date",
                               "offer_id$availability",
                               ]
                component.configure(list_fields = list_fields,
                                    )

                record = r.record

                # Configure offer_id selector
                ctable = r.component.table
                field = ctable.offer_id

                # Use must be permitted to manage the offer
                aotable = s3db.br_assistance_offer
                query = auth.s3_accessible_query("update", aotable, c="br", f="assistance_offer")
                # Need type must match
                need_id = record.need_id if record else None
                if need_id:
                    query &= aotable.need_id == need_id
                # Offer must not be blocked, nor past
                today = r.utcnow.date()
                query &= (aotable.status != "BLC") & \
                         ((aotable.end_date == None) | (aotable.end_date >= today))
                dbset = db(query)
                field.requires = IS_ONE_OF(dbset, "br_assistance_offer.id",
                                           field.represent,
                                           )

                # Add popup link as primary route to create new offer as direct offer
                from s3layouts import S3PopupLink
                popup_vars = {# Request the options via this tab to apply above filters
                                "parent": "activities/%s/direct_offer" % record.id,
                                "child": "offer_id",
                                }
                need_id = record.need_id
                if need_id:
                    popup_vars["need_id"] = need_id
                field.comment = S3PopupLink(label = T("Create new Offer"),
                                            c = "br",
                                            f = "assistance_offer",
                                            m = "create",
                                            vars = popup_vars,
                                            )

                # TODO add a CMS intro for selector

                # Cannot create direct offers for my own needs
                insertable = not auth.s3_has_permission("update", "br_case_activity",
                                                        c = "br",
                                                        f = "case_activity",
                                                        record_id = record.id,
                                                        )
                r.component.configure(insertable = insertable,
                                        # Direct offers can not be updated
                                        # => must delete + create new
                                        editable = False,
                                        )

                resource.configure(ignore_master_access = ("direct_offer",),
                                   )

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpcm_br_rheader
        attr["rheader"] = rlpcm_br_rheader

        return attr

    settings.customise_br_case_activity_controller = customise_br_case_activity_controller

    # -------------------------------------------------------------------------
    def direct_offer_create_onaccept(form):
        # TODO docstring

        # Get the record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        # Get the offer
        table = s3db.br_direct_offer
        aotable = s3db.br_assistance_offer
        join = aotable.on(aotable.id == table.offer_id)

        query = (table.id == record_id)
        row = db(query).select(table.id,
                               table.notify,
                               table.notified_on,
                               aotable.id,
                               aotable.status,
                               aotable.end_date,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        record = row.br_direct_offer
        offer = row.br_assistance_offer

        today = current.request.utcnow.date()

        if offer.status == "NEW":
            current.response.warning = T("Your offer is waiting for approval by the administrator")

        elif offer.status == "APR" and \
             (offer.end_date == None or offer.end_date >= today) and \
             record.notify and \
             record.notified_on == None:
            from .helpers import notify_direct_offer
            error = notify_direct_offer(record.id)
            if error:
                current.response.error = T("Notification could not be sent: %(error)s") % {"error": error}
            else:
                current.response.information = T("Notification sent")

    # -------------------------------------------------------------------------
    def customise_br_direct_offer_resource(r, tablename):

        s3db = current.s3db

        table = s3db.br_direct_offer

        field = table.offer_id
        from s3 import S3WithIntro
        from gluon.sqlhtml import OptionsWidget
        field.widget = S3WithIntro(OptionsWidget.widget,
                                   intro = ("br",
                                            "direct_offer",
                                            "DirectOfferSelectorIntro",
                                            ),
                                   )

        # Custom label+represent for case activity
        # - always link to activities-perspective ("Current Needs")
        field = table.case_activity_id
        field.label = T("Need")
        field.represent = s3db.br_CaseActivityRepresent(show_as = "subject",
                                                        show_link = True,
                                                        linkto = URL(c = "br",
                                                                     f = "activities",
                                                                     args = "[id]",
                                                                     extension = "",
                                                                     ),
                                                        )

        # Callback to trigger notification
        s3db.add_custom_callback("br_direct_offer",
                                 "onaccept",
                                 direct_offer_create_onaccept,
                                 method = "create",
                                 )

    settings.customise_br_direct_offer_resource = customise_br_direct_offer_resource

    # -------------------------------------------------------------------------
    # TODO customise event_event

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        # Enable bigtable features
        settings.base.bigtable = True

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            auth = current.auth
            #s3db = current.s3db

            resource = r.resource

            is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")
            mine = False

            if not is_org_group_admin:

                if r.get_vars.get("mine") == "1":
                    mine = True
                    # Filter to those the user can update
                    aquery = current.auth.s3_accessible_query("update", "org_organisation")
                    if aquery:
                        resource.add_filter(aquery)

                # Restrict data formats
                allowed = ("html", "iframe", "popup", "aadata", "plain", "geojson", "pdf", "xls")
                if r.method in ("report", "filter"):
                    allowed += ("json",)
                settings.ui.export_formats = ("pdf", "xls")
                if r.representation not in allowed:
                    r.error(403, current.ERROR.NOT_PERMITTED)

            if not r.component:
                if r.interactive:

                    from s3 import S3SQLCustomForm, \
                                   S3SQLInlineComponent, \
                                   S3SQLInlineLink, \
                                   S3OptionsFilter, \
                                   S3TextFilter, \
                                   s3_get_filter_opts

                    # Custom form
                    if is_org_group_admin:
                        types = S3SQLInlineLink("organisation_type",
                                                field = "organisation_type_id",
                                                search = False,
                                                label = T("Type"),
                                                multiple = settings.get_org_organisation_types_multiple(),
                                                widget = "multiselect",
                                                )
                    else:
                        types = None

                    crud_fields = ["name",
                                   "acronym",
                                   types,
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
                                   "phone",
                                   "website",
                                   "logo",
                                   "comments",
                                   ]

                    # Filters
                    text_fields = ["name",
                                   "acronym",
                                   "website",
                                   "phone",
                                   ]
                    if is_org_group_admin:
                        text_fields.append("email.value")
                    if not mine:
                        text_fields.extend(["office.location_id$L3",
                                            "office.location_id$L1",
                                            ])
                    filter_widgets = [S3TextFilter(text_fields,
                                                   label = T("Search"),
                                                   ),
                                      ]
                    if is_org_group_admin:
                        filter_widgets.extend([
                            S3OptionsFilter(
                                "organisation_type__link.organisation_type_id",
                                label = T("Type"),
                                options = lambda: s3_get_filter_opts("org_organisation_type"),
                                ),
                            ])

                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                       filter_widgets = filter_widgets,
                                       )

                # Custom list fields
                if is_org_group_admin:
                    list_fields = ["name",
                                   "organisation_type__link.organisation_type_id",
                                   (T("Description"), "comments"),
                                   "office.location_id$L3",
                                   "office.location_id$L1",
                                   "website",
                                   "phone",
                                   (T("Email"), "email.value"),
                                   ]
                elif not mine:
                    list_fields = ["name",
                                   "organisation_type__link.organisation_type_id",
                                   (T("Description"), "comments"),
                                   #"office.location_id$L3",
                                   #"office.location_id$L1",
                                   "website",
                                   "phone",
                                   ]
                    if auth.user:
                        list_fields[3:3] = ("office.location_id$L3",
                                            "office.location_id$L1",
                                            )

                else:
                    list_fields = ["name",
                                   (T("Description"), "comments"),
                                   "website",
                                   "phone",
                                   (T("Email"), "email.value"),
                                   ]
                r.resource.configure(list_fields = list_fields,
                                     )

            return result
        s3.prep = prep

        # Custom rheader
        from .rheaders import rlpcm_org_rheader
        attr = dict(attr)
        attr["rheader"] = rlpcm_org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

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

        # Configure components to inherit realm_entity from
        # the person record incl. on realm updates
        s3db.configure("pr_person",
                       realm_components = ("assistance_measure",
                                           "case_activity",
                                           "case_language",
                                           "address",
                                           "contact",
                                           "contact_emergency",
                                           "group_membership",
                                           "image",
                                           "note",
                                           "person_details",
                                           "person_tag",
                                           ),
                       )

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

            controller = r.controller

            # Never show all cases
            if controller == "br" and "closed" not in r.get_vars:
                r.get_vars.closed = "0"

            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            resource = r.resource
            table = resource.table

            from s3 import S3SQLCustomForm, \
                           S3SQLInlineComponent, \
                           StringTemplateParser

            # Determine order of name fields
            NAMES = ("first_name", "middle_name", "last_name")
            keys = StringTemplateParser.keys(settings.get_pr_name_format())
            name_fields = [fn for fn in keys if fn in NAMES]

            if controller == "br":

                ctable = s3db.br_case
                record = r.record

                if not r.component:

                    # Module-specific field and form configuration

                    # Adapt fields to module context
                    multiple_orgs = s3db.br_case_read_orgs()[0]

                    # Configure pe_label (r/o, auto-generated onaccept)
                    field = table.pe_label
                    field.label = T("ID")
                    field.readable = bool(record)
                    field.writable = False

                    # Hide gender
                    field = table.gender
                    field.default = None
                    field.readable = field.writable = False

                    # Address
                    if settings.get_br_case_address():
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
                    else:
                        address = None

                    # If there is a default status for new cases,
                    # hide the status field in create-form
                    field = ctable.status_id
                    if not record and field.default:
                        field.readable = field.writable = False

                    # Configure case.organisation_id
                    field = ctable.organisation_id
                    field.comment = None
                    if not current.auth.s3_has_role("RELIEF_PROVIDER"):
                        ctable = s3db.br_case
                        field.default = settings.get_org_default_organisation()
                        field.readable = field.writable = bool(field.default)
                    else:
                        default_org, selectable = s3db.br_case_default_org()
                        if default_org:
                            field.writable = selectable
                            field.readable = selectable or multiple_orgs
                        field.default = default_org
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other

                    # CRUD form
                    crud_fields = ["case.date",
                                   "case.organisation_id",
                                   "case.human_resource_id",
                                   "case.status_id",
                                   "pe_label",
                                   # +name fields
                                   "case.household_size",
                                   address,
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
                                   "case.comments",
                                   "case.invalid",
                                   ]

                    # Filters
                    from s3 import S3LocationFilter, \
                                   S3OptionsFilter, \
                                   S3TextFilter, \
                                   s3_get_filter_opts
                    filter_widgets = [S3TextFilter(["pe_label",
                                                    "last_name",
                                                    "first_name",
                                                    ],
                                                   label = T("Search"),
                                                   ),
                                      S3LocationFilter("address.location_id",
                                                       levels = ("L2", "L3"),
                                                       ),
                                      ]

                    # List fields
                    list_fields = ["pe_label",
                                   # +name fields
                                   "case.date",
                                   "case.status_id",
                                   ]

                    # Add organisation if user can see cases from multiple orgs
                    if multiple_orgs:
                        filter_widgets.insert(-1,
                            S3OptionsFilter("case.organisation_id",
                                            options = s3_get_filter_opts("org_organisation"),
                                            ))
                        list_fields.insert(-2, "case.organisation_id")

                    # Insert name fields in name-format order
                    NAMES = ("first_name", "middle_name", "last_name")
                    keys = StringTemplateParser.keys(settings.get_pr_name_format())
                    name_fields = [fn for fn in keys if fn in NAMES]
                    crud_fields[5:5] = name_fields
                    list_fields[1:1] = name_fields

                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                       filter_widgets = filter_widgets,
                                       list_fields = list_fields,
                                       )

            elif controller == "default":
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
        c = current.request.controller
        from .rheaders import rlpcm_profile_rheader, rlpcm_br_rheader
        if c == "default":
            attr["rheader"] = rlpcm_profile_rheader
        elif c == "br":
            attr["rheader"] = rlpcm_br_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

# END =========================================================================
