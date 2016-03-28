# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

import datetime

from gluon import current, SPAN
from gluon.storage import Storage

# Limit after which a checked-out resident is reported overdue (days)
ABSENCE_LIMIT = 5

def config(settings):
    """
        DRK ("Village") Template:

        Case Management, Refugee Reception Center, German Red Cross
    """

    T = current.T

    settings.base.system_name = "Village"
    settings.base.system_name_short = "Village"

    # PrePopulate data
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
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               "volunteer": T("Volunteer"),
                                               }
    #settings.auth.registration_link_user_to_default = "staff"

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("DE",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Settings suitable for Housing Units
    # - move into customise fn if also supporting other polygons
    settings.gis.precision = 5
    settings.gis.simplify_tolerance = 0
    settings.gis.bbox_min_size = 0.001
    #settings.gis.bbox_offset = 0.007

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
    settings.security.policy = 5 # Controller, Function & Table ACLs

    # Version details on About-page require login
    settings.security.version_info_requires_login = True

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
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

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

    settings.project.task_time = False

    # -------------------------------------------------------------------------
    # Requests Module Settings
    #
    settings.req.req_type = ("Stock",)
    settings.req.use_commit = False
    settings.req.recurring = False

    # -------------------------------------------------------------------------
    # Shelter Module Settings
    #
    #settings.cr.day_and_night = False
    settings.cr.shelter_population_dynamic = True
    settings.cr.shelter_housing_unit_management = True
    settings.cr.check_out_is_final = False

    # -------------------------------------------------------------------------
    def profile_header(r):
        """
            Profile Header for Shelter Profile page
        """

        from gluon.html import DIV, H2, P, TABLE, TR, TD, A

        db = current.db
        s3db = current.s3db

        rtable = s3db.cr_shelter_registration
        utable = s3db.cr_shelter_unit
        ctable = s3db.dvr_case
        stable = s3db.dvr_case_status

        # Count number of shelter registrations,
        # grouped by transitory-status of the housing unit
        left = utable.on(utable.id == rtable.shelter_unit_id)
        query = (rtable.deleted != True)
        count = rtable.id.count()
        rows = db(query).select(utable.transitory,
                                count,
                                groupby = utable.transitory,
                                left = left,
                                )
        transitory = 0
        regular = 0
        for row in rows:
            if row[utable.transitory]:
                transitory += row[count]
            else:
                regular += row[count]
        total = transitory + regular

        # Transitory housing unit is called "PX" at BFV Mannheim
        # @todo: generalize, lookup transitory unit name(s) from db
        TRANSITORY = TR(TD(T("How many in PX")),
                        TD(transitory),
                        )
        REGULAR = TR(TD(T("How many in BEA (except in PX)")),
                     TD(regular),
                     )
        TOTAL = TR(TD(T("How many in BEA (total)")),
                   TD(total),
                   )

        # Get the IDs of external statuses
        STATUS_EXTERNAL = ("STATUS9", "STATUS9A")
        query = (stable.code.belongs(STATUS_EXTERNAL)) & \
                (stable.deleted != True)
        rows = db(query).select(stable.id, limitby = (0, 2))
        external_status_ids = set(row.id for row in rows)

        # Count valid cases with external status
        count = ctable.id.count()
        query = (ctable.status_id.belongs(external_status_ids)) & \
                ((ctable.archived == False) | (ctable.archived == None)) & \
                (ctable.deleted != True)
        rows = db(query).select(count)
        external = rows.first()[count] if rows else 0

        EXTERNAL = TR(TD(T("How many external (Hospital / Police)")),
                      TD(external),
                      )

        # Get the number of free places in the BEA
        free = r.record.available_capacity_day
        FREE = TR(TD(T("How many free places")),
                  TD(free),
                  )

        # Generate profile header HTML
        output = DIV(H2(r.record.name),
                     P(r.record.comments or ""),
                     # Current population overview
                     TABLE(TOTAL,
                           TRANSITORY,
                           REGULAR,
                           EXTERNAL,
                           FREE
                           ),
                     # Action buttons for check-in/out
                     A("%s / %s" % (T("Check-In"), T("Check-Out")),
                       _href=r.url(method="check-in"),
                       _class="action-btn",
                       ),
                     _class="profile-header",
                     )

        return output

    settings.ui.profile_header = profile_header

    # -------------------------------------------------------------------------
    def site_check_in(site_id, person_id):
        """
            When a person is checked-in to a Shelter then update the Shelter Registration
            (We assume they are checked-in during initial registration)
        """

        from s3 import s3_str

        s3db = current.s3db
        db = current.db

        warnings = []
        wappend = warnings.append

        # Check the case status
        ctable = s3db.dvr_case
        cstable = s3db.dvr_case_status
        query = (ctable.person_id == person_id) & \
                (cstable.id == ctable.status_id)
        status = db(query).select(cstable.is_closed,
                                  limitby = (0, 1),
                                  ).first()

        if status and status.is_closed:
            wappend(T("Not currently a resident"))

        # Find the Registration
        stable = s3db.cr_shelter
        rtable = s3db.cr_shelter_registration

        query = (stable.site_id == site_id) & \
                (stable.id == rtable.shelter_id) & \
                (rtable.person_id == person_id) & \
                (rtable.deleted != True)
        registration = db(query).select(rtable.id,
                                        rtable.registration_status,
                                        limitby=(0, 1),
                                        ).first()
        if not registration:
            error = T("Registration not found")
            return error, ", ".join(s3_str(w) for w in warnings)

        error = None

        if registration.registration_status == 2:
            wappend(T("Client was already checked-in"))

        # Update the Shelter Registration
        registration.update_record(check_in_date = current.request.utcnow,
                                   registration_status = 2,
                                   )

        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)

        return error, ", ".join(s3_str(w) for w in warnings)

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
                (rtable.person_id == person_id) & \
                (rtable.deleted != True)
        registration = current.db(query).select(rtable.id,
                                                rtable.registration_status,
                                                limitby=(0, 1),
                                                ).first()
        if not registration:
            # @ToDo: Check to see if they DISAPPEARED, etc
            error = T("Registration not found")
            warning = None
            return error, warning

        error = None
        if registration.registration_status == 3:
            warning = T("Client was already checked-out")
        else:
            warning = None

        # Update the Shelter Registration
        registration.update_record(check_out_date = current.request.utcnow,
                                   registration_status = 3)

        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)

        return error, warning

    # -------------------------------------------------------------------------
    def org_site_check(site_id):
        """ Custom tasks for scheduled site checks """

        # Update transferability
        from controllers import update_transferability
        result = update_transferability(site_id=site_id)

        # Log the result
        msg = "Update Transferability: " \
              "%s transferable cases found for site %s" % (result, site_id)
        current.log.info(msg)

    settings.org.site_check = org_site_check

    # -------------------------------------------------------------------------
    def customise_auth_user_resource(r, tablename):

        current.db.auth_user.organisation_id.default = settings.get_org_default_organisation()

    settings.customise_auth_user_resource = customise_auth_user_resource

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
                # Configure check-in methods
                current.s3db.configure("cr_shelter",
                                       site_check_in = site_check_in,
                                       site_check_out = site_check_out,
                                       )
            else:
                has_role = current.auth.s3_has_role
                if has_role("SECURITY") and not has_role("ADMIN"):
                    # Security can't do anything else but check-in
                    current.auth.permission.fail()

                if r.method == "profile":
                    # Add PoI layer to the Map
                    s3db = current.s3db
                    ftable = s3db.gis_layer_feature
                    query = (ftable.controller == "gis") & \
                            (ftable.function == "poi")
                    layer = current.db(query).select(ftable.layer_id,
                                                     limitby=(0, 1)
                                                     ).first()
                    try:
                        layer_id = layer.layer_id
                    except:
                        # No suitable prepop found
                        pass
                    else:
                        pois = dict(active = True,
                                    layer_id = layer_id,
                                    name = current.T("Buildings"),
                                    id = "profile-header-%s-%s" % ("gis_poi", r.id),
                                    )
                        profile_layers = s3db.get_config("cr_shelter", "profile_layers")
                        profile_layers += (pois,)
                        s3db.configure("cr_shelter",
                                       profile_layers = profile_layers,
                                       )

            if r.component_name == "shelter_unit":
                # Expose "transitory" flag for housing units
                utable = current.s3db.cr_shelter_unit
                field = utable.transitory
                field.readable = field.writable = True
                list_fields = ["name",
                               "transitory",
                               "capacity_day",
                               "population_day",
                               "available_capacity_day",
                               ]
                r.component.configure(list_fields=list_fields)

            return result
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            # Hide side menu and rheader for check-in
            if r.method == "check-in":
                current.menu.options = None
                output["rheader"] = ""

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_cr_shelter_controller = customise_cr_shelter_controller

    # -------------------------------------------------------------------------
    def customise_cr_shelter_registration_resource(r, tablename):

        table = current.s3db.cr_shelter_registration
        field = table.shelter_unit_id

        # Filter to available housing units
        from gluon import IS_EMPTY_OR
        from s3 import IS_ONE_OF
        field.requires = IS_EMPTY_OR(IS_ONE_OF(current.db, "cr_shelter_unit.id",
                                               field.represent,
                                               filterby = "status",
                                               filter_opts = (1,),
                                               orderby="shelter_id",
                                               ))

    settings.customise_cr_shelter_registration_resource = customise_cr_shelter_registration_resource

    # -------------------------------------------------------------------------
    def customise_cr_shelter_registration_controller(**attr):
        """
            Shelter Registration controller is just used
            by the Quartiermanager role.
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

            if r.method == "assign":
                # Prep runs before split into create/update (Create should never happen in Village)
                table = r.table
                # Only 1 Shelter
                f = table.shelter_id
                f.default = settings.get_org_default_site()
                f.writable = False # f.readable kept as True for cr_shelter_registration_onvalidation
                f.comment = None
                # Only edit for this Person
                f = table.person_id
                f.default = r.get_vars["person_id"]
                f.writable = False
                f.comment = None
                # Registration status hidden
                f = table.registration_status
                f.readable = False
                f.writable = False
                # Check-in dates hidden
                f = table.check_in_date
                f.readable = False
                f.writable = False
                f = table.check_out_date
                f.readable = False
                f.writable = False

                # Go back to the list of residents after assigning
                from gluon import URL
                current.s3db.configure("cr_shelter_registration",
                                       create_next = URL(c="dvr", f="person"),
                                       update_next = URL(c="dvr", f="person"),
                                       )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_cr_shelter_registration_controller = customise_cr_shelter_registration_controller

    # -------------------------------------------------------------------------
    # DVR Module Settings and Customizations
    #
    # Uncomment this to enable features to manage transferability of cases
    settings.dvr.manage_transferability = True
    # Uncomment this to enable household size in cases, set to "auto" for automatic counting
    settings.dvr.household_size = "auto"
    # Uncomment this to expose flags to mark appointment types as mandatory
    settings.dvr.mandatory_appointments = True
    # Uncomment this to allow cases to belong to multiple case groups ("households")
    #settings.dvr.multiple_case_groups = True

    # -------------------------------------------------------------------------
    def customise_dvr_home():
        """ Redirect dvr/index to dvr/person?closed=0 """

        from gluon import URL
        from s3 import s3_redirect_default

        s3_redirect_default(URL(f="person", vars={"closed": "0"}))

    settings.customise_dvr_home = customise_dvr_home

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        has_role = current.auth.s3_has_role
        is_admin = has_role(current.auth.get_system_roles().ADMIN)
        QUARTIERMANAGER = not is_admin and \
                          not any(has_role(role) for role in ("ADMINISTRATION",
                                                              "ADMIN_HEAD",
                                                              )) and \
                          has_role("QUARTIER")

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            if QUARTIERMANAGER:
                # Enforce closed=0
                r.vars["closed"] = r.get_vars["closed"] = "0"

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            archived = r.get_vars.get("archived")
            if archived in ("1", "true", "yes"):
                crud_strings = s3.crud_strings["pr_person"]
                crud_strings["title_list"] = T("Invalid Cases")

            controller = r.controller
            resource = r.resource

            if controller == "security":
                # Restricted view for Security staff
                if r.component:
                    redirect(r.url(method=""))

                # Filter to persons who have a case registered
                from s3 import FS
                resource.add_filter(FS("dvr_case.id") != None)

                current.menu.options = None
                # Only Show Security Notes
                ntable = s3db.dvr_note_type
                note_type = current.db(ntable.name == "Security").select(ntable.id,
                                                                         limitby=(0, 1)
                                                                         ).first()
                try:
                    note_type_id = note_type.id
                except:
                    current.log.error("Prepop not done - deny access to dvr_note component")
                    note_type_id = None
                    atable = s3db.dvr_note
                    atable.date.readable = atable.date.writable = False
                    atable.note.readable = atable.note.writable = False
                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                crud_form = S3SQLCustomForm(
                                (T("ID"), "pe_label"),
                                "last_name",
                                "first_name",
                                "date_of_birth",
                                #"gender",
                                "person_details.nationality",
                                "cr_shelter_registration.shelter_unit_id",
                                S3SQLInlineComponent(
                                        "case_note",
                                        fields = [(T("Date"), "date"),
                                                  "note",
                                                  ],
                                        filterby = {"field": "note_type_id",
                                                    "options": note_type_id,
                                                    },
                                        label = T("Security Notes"),
                                        ),
                                )

                list_fields = [(T("ID"), "pe_label"),
                               "last_name",
                               "first_name",
                               "date_of_birth",
                               #"gender",
                               "person_details.nationality",
                               "shelter_registration.shelter_unit_id",
                               ]


                if r.method == "profile":
                    from gluon.html import DIV, H2, P, TABLE, TR, TD, A
                    from s3 import s3_fullname
                    db = current.db
                    person_id = r.id
                    record = r.record
                    table = r.table
                    dtable = s3db.pr_person_details
                    details = db(dtable.person_id == person_id).select(dtable.nationality,
                                                                       limitby=(0, 1)
                                                                       ).first()
                    try:
                        nationality = details.nationality
                    except:
                        nationality = None
                    rtable = s3db.cr_shelter_registration
                    reg = db(rtable.person_id == person_id).select(rtable.shelter_unit_id,
                                                                   limitby=(0, 1)
                                                                   ).first()
                    try:
                        shelter_unit_id = reg.shelter_unit_id
                    except:
                        shelter_unit_id = None
                    profile_header = DIV(H2(s3_fullname(record)),
                                         TABLE(TR(TD(T("ID")),
                                                  TD(record.pe_label)
                                                  ),
                                               TR(TD(table.last_name.label),
                                                  TD(record.last_name)
                                                  ),
                                               TR(TD(table.first_name.label),
                                                  TD(record.first_name)
                                                  ),
                                               TR(TD(table.date_of_birth.label),
                                                  TD(record.date_of_birth)
                                                  ),
                                               TR(TD(dtable.nationality.label),
                                                  TD(nationality)
                                                  ),
                                               TR(TD(rtable.shelter_unit_id.label),
                                                  TD(shelter_unit_id)
                                                  ),
                                               ),
                                         _class="profile-header",
                                         )
                    notes_widget = dict(label = "Security Notes",
                                        label_create = "Add Note",
                                        type = "datatable",
                                        tablename = "dvr_note",
                                        filter = ((FS("note_type_id$name") == "Security") & \
                                                  (FS("person_id") == person_id)),
                                        #icon = "report",
                                        create_controller = "dvr",
                                        create_function = "note",
                                        )
                    profile_widgets = [notes_widget]
                else:
                    profile_header = None
                    profile_widgets = None

                resource.configure(crud_form = crud_form,
                                   list_fields = list_fields,
                                   profile_header = profile_header,
                                   profile_widgets = profile_widgets,
                                   )

            elif controller == "dvr":

                from gluon import Field, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY

                configure = resource.configure
                table = r.table

                # Used in both list_fields and rheader
                table.absence = Field.Method("absence", drk_absence)

                if r.representation in ("html", "iframe", "aadata"):
                    # Delivers HTML, so restrict to GUI:
                    absence_field = (T("Checked-out"), "absence")
                    configure(extra_fields = ["shelter_registration.registration_status",
                                              "shelter_registration.check_out_date",
                                              ],
                              )
                else:
                    absence_field = None

                # List modes
                check_overdue = False
                show_family_transferable = False

                # Labels
                FAMILY_TRANSFERABLE = T("Family Transferable")

                if not r.record:
                    overdue = r.get_vars.get("overdue")
                    if overdue:
                        # Filter case list for overdue check-in
                        from s3 import FS

                        reg_status = FS("shelter_registration.registration_status")
                        checkout_date = FS("shelter_registration.check_out_date")

                        checked_out = (reg_status == 3)
                        # Must catch None explicitly because it is neither
                        # equal nor unequal with anything according to SQL rules
                        not_checked_out = ((reg_status == None) | (reg_status != 3))

                        # Due date for check-in
                        due_date = current.request.utcnow - \
                                   datetime.timedelta(days=ABSENCE_LIMIT)

                        if overdue == "1":
                            query = checked_out & \
                                    ((checkout_date < due_date) | (checkout_date == None))
                        else:
                            query = not_checked_out | \
                                    checked_out & (checkout_date >= due_date)
                        resource.add_filter(query)
                        check_overdue = True

                    show_family_transferable = r.get_vars.get("show_family_transferable")
                    if show_family_transferable == "1":
                        show_family_transferable = True

                if not r.component:

                    # Additional component "EasyOpt Number"
                    s3db.add_components("pr_person",
                                        pr_person_tag = {"name": "eo_number",
                                                         "joinby": "person_id",
                                                         "filterby": "tag",
                                                         "filterfor": ("EONUMBER",),
                                                         "multiple": False,
                                                         },
                                        )


                    # Case is valid for 5 years
                    ctable = s3db.dvr_case
                    field = ctable.valid_until
                    from dateutil.relativedelta import relativedelta
                    field.default = r.utcnow + relativedelta(years=5)
                    # Not used currently:
                    #field.readable = field.writable = True

                    #default_organisation = current.auth.root_org()
                    default_organisation = settings.get_org_default_organisation()
                    if default_organisation:
                        # Set default for organisation_id and hide the field
                        # (already done in core model)
                        #field = ctable.organisation_id
                        #field.default = default_organisation
                        #field.readable = field.writable = False

                        # Hide organisation_id in list_fields, too
                        # Not needed - using custom list_fields anyway
                        #list_fields = r.resource.get_config("list_fields")
                        #if "dvr_case.organisation_id" in list_fields:
                        #    list_fields.remove("dvr_case.organisation_id")

                        default_site = settings.get_org_default_site()
                        if default_site:
                            # Set default for organisation_id and hide the field
                            # (already done in core model)

                            # Set default shelter_id
                            db = current.db
                            stable = s3db.cr_shelter
                            query = (stable.site_id == default_site)
                            shelter = db(query).select(stable.id,
                                                    limitby=(0, 1),
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
                                                              # Only available units:
                                                              filterby = "status",
                                                              filter_opts = (1,),
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

                    configure = resource.configure
                    if r.interactive and r.method != "import":

                        # Registration status effective dates not manually updateable
                        if r.id:
                            rtable = s3db.cr_shelter_registration
                            field = rtable.check_in_date
                            field.writable = False
                            field.label = T("Last Check-in")
                            field = rtable.check_out_date
                            field.writable = False
                            field.label = T("Last Check-out")

                        # Configure person_details fields
                        ctable = s3db.pr_person_details

                        # Make marital status mandatory, remove "other"
                        field = ctable.marital_status
                        options = dict(s3db.pr_marital_status_opts)
                        del options[9] # Remove "other"
                        field.requires = IS_IN_SET(options, zero=None)

                        # Configure person fields
                        table = resource.table

                        # Make gender mandatory, remove "unknown"
                        field = table.gender
                        field.default = None
                        from s3 import IS_PERSON_GENDER
                        options = dict(s3db.pr_gender_opts)
                        del options[1] # Remove "unknown"
                        field.requires = IS_PERSON_GENDER(options, sort = True)

                        # Last name is required
                        field = table.last_name
                        field.requires = IS_NOT_EMPTY()

                        # Check whether the shelter registration shall be cancelled
                        cancel = False
                        if r.http == "POST":
                            db = current.db
                            post_vars = r.post_vars
                            archived = post_vars.get("sub_dvr_case_archived")
                            status_id = post_vars.get("sub_dvr_case_status_id")
                            if archived:
                                cancel = True
                            if not cancel and status_id:
                                stable = s3db.dvr_case_status
                                status = db(stable.id == status_id).select(stable.is_closed,
                                                                           limitby = (0, 1),
                                                                           ).first()
                                try:
                                    if status.is_closed:
                                        cancel = True
                                except:
                                    pass

                        if cancel:
                            # Ignore registration data in form if the registration
                            # is to be cancelled - otherwise a new registration is
                            # created by the subform-processing right after
                            # dvr_case_onaccept deletes the current one:
                            reg_shelter = None
                            reg_status = None
                            reg_unit_id = None
                            reg_check_in_date = None
                            reg_check_out_date = None
                        else:
                            reg_shelter = "cr_shelter_registration.shelter_id"
                            reg_status = (T("Presence"),
                                          "cr_shelter_registration.registration_status",
                                          )
                            reg_unit_id = "cr_shelter_registration.shelter_unit_id"
                            reg_check_in_date = "cr_shelter_registration.check_in_date"
                            reg_check_out_date = "cr_shelter_registration.check_out_date"

                        # Custom CRUD form
                        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
                        crud_form = S3SQLCustomForm(
                                        #"dvr_case.reference",
                                        # Will always default & be hidden
                                        "dvr_case.organisation_id",
                                        # Will always default & be hidden
                                        "dvr_case.site_id",
                                        (T("BFV Arrival"), "dvr_case.date"),
                                        (T("Case Status"), "dvr_case.status_id"),
                                        # Will always default & be hidden
                                        #"cr_shelter_registration.site_id",
                                        reg_shelter,
                                        # @ ToDo: Automate this from the Case Status?
                                        reg_unit_id,
                                        reg_status,
                                        reg_check_in_date,
                                        reg_check_out_date,
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
                                        "last_name",
                                        "first_name",
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
                                        (T("Invalid"), "dvr_case.archived"),
                                        )
                        configure(crud_form = crud_form,
                                  )

                        # Reconfigure filter widgets
                        filter_widgets = resource.get_config("filter_widgets")
                        if filter_widgets:

                            from s3 import S3DateFilter, \
                                           S3OptionsFilter, \
                                           S3TextFilter
                            extend_text_filter = True
                            for fw in filter_widgets:
                                # No filter default for case status
                                if fw.field == "dvr_case.status_id":
                                    fw.opts.default = None
                                # Text filter includes EasyOpt Number and Case Comments
                                if extend_text_filter and isinstance(fw, S3TextFilter):
                                    fw.field.extend(("eo_number.value",
                                                     "dvr_case.comments",
                                                     ))
                                    fw.opts.comment = T("You can search by name, ID, EasyOpt number and comments")
                                    extend_text_filter = False

                            # Add filter for date of birth
                            dob_filter = S3DateFilter("date_of_birth")
                            #dob_filter.operator = ["eq"]
                            filter_widgets.insert(1, dob_filter)

                            # Add filter for family transferability
                            if show_family_transferable:
                                ft_filter = S3OptionsFilter("dvr_case.household_transferable",
                                                            label = FAMILY_TRANSFERABLE,
                                                            options = {True: T("Yes"),
                                                                       False: T("No"),
                                                                       },
                                                            cols = 2,
                                                            hidden = True,
                                                            )
                                filter_widgets.append(ft_filter)

                            # Add filter for registration date
                            reg_filter = S3DateFilter("dvr_case.date",
                                                      hidden = True,
                                                      )
                            filter_widgets.append(reg_filter)

                            # Add filter for registration status
                            reg_filter = S3OptionsFilter("shelter_registration.registration_status",
                                                         label = T("Presence"),
                                                         options = s3db.cr_shelter_registration_status_opts,
                                                         hidden = True,
                                                         cols = 3,
                                                         )
                            filter_widgets.append(reg_filter)

                            # Add filter for IDs
                            id_filter = S3TextFilter(["pe_label"],
                                                     label = T("IDs"),
                                                     match_any = True,
                                                     hidden = True,
                                                     comment = T("Search for multiple IDs (separated by blanks)"),
                                                     )
                            filter_widgets.append(id_filter)

                    # Custom list fields (must be outside of r.interactive)
                    list_fields = [(T("ID"), "pe_label"),
                                   (T("EasyOpt No."), "eo_number.value"),
                                   "last_name",
                                   "first_name",
                                   "date_of_birth",
                                   "gender",
                                   "person_details.nationality",
                                   "dvr_case.date",
                                   "dvr_case.status_id",
                                   (T("Shelter"), "shelter_registration.shelter_unit_id"),
                                   ]

                    # Add fields for managing transferability
                    if settings.get_dvr_manage_transferability() and not check_overdue:
                        transf_fields = ["dvr_case.transferable",
                                         (T("Size of Family"), "dvr_case.household_size"),
                                         ]
                        if show_family_transferable:
                            transf_fields.append((FAMILY_TRANSFERABLE,
                                                  "dvr_case.household_transferable"))
                        list_fields[-1:-1] = transf_fields

                    # Days of absence (virtual field)
                    if absence_field:
                        list_fields.append(absence_field)

                    if r.representation == "xls":
                        # Extra list_fields for XLS export

                        # Add appointment dates
                        atypes = ["GU",
                                  "X-Ray",
                                  "Reported Transferable",
                                  "Transfer",
                                  "Sent to RP",
                                  ]
                        COMPLETED = 4
                        afields = []
                        attable = s3db.dvr_case_appointment_type
                        query = attable.name.belongs(atypes)
                        rows = db(query).select(attable.id,
                                                attable.name,
                                                )
                        add_components = s3db.add_components
                        for row in rows:
                            type_id = row.id
                            name = "appointment%s" % type_id
                            hook = {"name": name,
                                    "joinby": "person_id",
                                    "filterby": {"type_id": type_id,
                                                 "status": COMPLETED,
                                                 },
                                    }
                            add_components("pr_person",
                                           dvr_case_appointment = hook,
                                           )
                            afields.append((T(row.name), "%s.date" % name))

                        list_fields.extend(afields)

                        # Add family key
                        s3db.add_components("pr_person",
                                            pr_group = {"name": "family",
                                                        "link": "pr_group_membership",
                                                        "joinby": "person_id",
                                                        "key": "group_id",
                                                        "filterby": {"group_type": 7},
                                                        },
                                            )

                        list_fields += [# Current check-in/check-out status
                                        (T("Registration Status"),
                                         "shelter_registration.registration_status",
                                         ),
                                        # Last Check-in date
                                        "shelter_registration.check_in_date",
                                        # Last Check-out date
                                        "shelter_registration.check_out_date",
                                        # Person UUID
                                        ("UUID", "uuid"),
                                        # Family Record ID
                                        (T("Family ID"), "family.id"),
                                        ]
                    configure(list_fields = list_fields)

            return result
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if QUARTIERMANAGER:
                # Add Action Button to assign Housing Unit to the Resident
                from gluon import URL
                #from s3 import S3CRUD, s3_str
                from s3 import s3_str
                #S3CRUD.action_buttons(r)
                s3.actions = [dict(label=s3_str(T("Assign Shelter")),
                                    _class="action-btn",
                                    url=URL(c="cr",
                                            f="shelter_registration",
                                            args=["assign"],
                                            vars={"person_id": "[id]"},
                                            )),
                               ]

            return output
        s3.postp = custom_postp

        # Custom rheader tabs
        if current.request.controller == "dvr":
            attr = dict(attr)
            attr["rheader"] = drk_dvr_rheader

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

            ROLE = T("Role")

            resource = r.resource
            if r.controller == "dvr" and r.interactive:
                table = resource.table

                from gluon import IS_EMPTY_OR
                from s3 import IS_ADD_PERSON_WIDGET2, S3AddPersonWidget2, IS_ONE_OF

                field = table.person_id
                field.represent = s3db.pr_PersonRepresent(show_link=True)
                field.requires = IS_ADD_PERSON_WIDGET2()
                field.widget = S3AddPersonWidget2(controller="dvr")

                field = table.role_id
                field.readable = field.writable = True
                field.label = ROLE
                field.comment = None
                field.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(current.db, "pr_group_member_role.id",
                                              field.represent,
                                              filterby = "group_type",
                                              filter_opts = (7,),
                                              ))

                field = table.group_head
                field.label = T("Head of Family")

            if r.controller == "dvr":
                list_fields = [(T("ID"), "person_id$pe_label"),
                               "person_id",
                               "person_id$date_of_birth",
                               "person_id$gender",
                               (ROLE, "role_id"),
                               (T("Case Status"), "person_id$dvr_case.status_id"),
                               "person_id$dvr_case.transferable",
                               ]
                # Retain group_id in list_fields if added in standard prep
                lfields = resource.get_config("list_fields")
                if "group_id" in lfields:
                    list_fields.insert(0, "group_id")
                resource.configure(filter_widgets = None,
                                   list_fields = list_fields,
                                   )
            return result
        s3.prep = custom_prep

        attr["rheader"] = drk_dvr_rheader

        return attr

    settings.customise_pr_group_membership_controller = customise_pr_group_membership_controller

    # -------------------------------------------------------------------------
    def dvr_case_onaccept(form):
        """
            If case is archived or closed then remove shelter_registration
        """

        cancel = False
        form_vars = form.vars
        archived = form_vars.archived
        if archived:
            cancel = True
            db = current.db
            s3db = current.s3db
        else:
            status_id = form_vars.status_id
            if status_id:
                db = current.db
                s3db = current.s3db
                stable = s3db.dvr_case_status
                status = db(stable.id == status_id).select(stable.is_closed,
                                                           limitby = (0, 1)
                                                           ).first()
                try:
                    if status.is_closed:
                        cancel = True
                except:
                    current.log.error("Status %s not found" % status_id)
                    return

        if cancel:
            rtable = s3db.cr_shelter_registration
            query = (rtable.person_id == form_vars.person_id)
            reg = db(query).select(rtable.id, limitby=(0, 1)).first()
            if reg:
                resource = s3db.resource("cr_shelter_registration",
                                         id = reg.id,
                                         )
                resource.delete()

    # -------------------------------------------------------------------------
    def customise_dvr_case_resource(r, tablename):

        s3db = current.s3db
        default_onaccept = s3db.get_config(tablename, "onaccept")
        if default_onaccept and not isinstance(default_onaccept, list): # Catch running twice
            onaccept = [default_onaccept,
                        dvr_case_onaccept,
                        ]
        else:
            onaccept = dvr_case_onaccept
        s3db.configure(tablename,
                       onaccept = onaccept,
                       )

    settings.customise_dvr_case_resource = customise_dvr_case_resource

    # -------------------------------------------------------------------------
    def dvr_note_onaccept(form):
        """
            Set owned_by_group
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars
        table = s3db.dvr_note_type
        types = db(table.name.belongs(("Medical", "Security"))).select(table.id,
                                                                       table.name).as_dict(key="name")
        try:
            MEDICAL = types["Medical"]["id"]
        except:
            current.log.error("Prepop not completed...cannot assign owned_by_group to dvr_note_type")
            return
        SECURITY = types["Security"]["id"]
        note_type_id = form_vars.note_type_id
        if note_type_id == str(MEDICAL):
            table = s3db.dvr_note
            gtable = db.auth_group
            role = db(gtable.uuid == "MEDICAL").select(gtable.id,
                                                       limitby=(0, 1)
                                                       ).first()
            try:
                group_id = role.id
            except:
                current.log.error("Prepop not completed...cannot assign owned_by_group to dvr_note")
                return
            db(table.id == form_vars.id).update(owned_by_group=group_id)
        elif note_type_id == str(SECURITY):
            table = s3db.dvr_note
            gtable = db.auth_group
            role = db(gtable.uuid == "SECURITY").select(gtable.id,
                                                        limitby=(0, 1)
                                                        ).first()
            try:
                group_id = role.id
            except:
                current.log.error("Prepop not completed...cannot assign owned_by_group to dvr_note")
                return
            db(table.id == form_vars.id).update(owned_by_group=group_id)

    # -------------------------------------------------------------------------
    def customise_dvr_note_resource(r, tablename):

        s3db = current.s3db
        #default_onaccept = s3db.get_config(tablename, "onaccept")
        #if default_onaccept:
        #    onaccept = [default_onaccept,
        #                dvr_case_activity_onaccept,
        #                ]
        #else:
        #    onaccept = dvr_case_activity_onaccept
        #s3db.configure(tablename,
        #               onaccept = onaccept,
        #               )

        has_role = current.auth.s3_has_role
        if has_role("SECURITY") and not has_role("ADMIN"):
            # Just see Security Notes
            table = s3db.dvr_note_type
            security = current.db(table.name == "Security").select(table.id,
                                                                   limitby=(0, 1)
                                                                   ).first()
            try:
                SECURITY = security.id
            except:
                current.log.error("Prepop not completed...cannot filter dvr_note_type")
                raise

            field = s3db[tablename].note_type_id
            field.default = SECURITY
            field.readable = field.writable = False
            from s3 import FS
            if r.tablename  == tablename:
                r.resource.add_filter(FS("note_type_id") == SECURITY)
            else:
                r.resource.add_component_filter("case_note", FS("note_type_id") == SECURITY)
                # Look through components
                #components = r.resource.components
                #for c in components:
                #    if c == tablename:
                #        components[c].add_filter(FS("note_type_id") == SECURITY)
                #        break
        elif not has_role("HEAD_OF_ADMIN"):
            # Remove Medical from list of options
            db = current.db
            table = s3db.dvr_note_type
            medical = db(table.name == "Medical").select(table.id,
                                                         limitby=(0, 1)
                                                         ).first()
            try:
                MEDICAL = medical.id
            except:
                current.log.error("Prepop not completed...cannot filter dvr_note_type")
                raise

            field = s3db[tablename].note_type_id
            from s3 import FS, IS_ONE_OF
            the_set = db(table.id != MEDICAL)
            field.requires = IS_ONE_OF(the_set, "dvr_note_type.id",
                                       field.represent)
            # Cannot see Medical Notes
            if r.tablename == tablename:
                r.resource.add_filter(FS("note_type_id") != MEDICAL)
            else:
                r.resource.add_component_filter("case_note", FS("note_type_id") != MEDICAL)
                # Look through components
                #components = r.resource.components
                #for c in components:
                #    if c == tablename:
                #        components[c].add_filter(FS("note_type_id") != MEDICAL)
                #        break

    settings.customise_dvr_note_resource = customise_dvr_note_resource

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_controller(**attr):

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

            # Filter to active cases
            if not r.record:
                from s3 import FS
                query = (FS("person_id$dvr_case.archived") == False) | \
                        (FS("person_id$dvr_case.archived") == None)
                resource.add_filter(query)

            if not r.component:

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

            resource = r.resource

            # Filter to active cases
            if not r.record:
                from s3 import FS
                query = (FS("person_id$dvr_case.archived") == False) | \
                        (FS("person_id$dvr_case.archived") == None)
                resource.add_filter(query)

            if not r.component:

                if r.interactive and not r.id:
                    # Add EO Number as component so it can be filtered by
                    s3db.add_components("pr_person",
                                        pr_person_tag = {"name": "eo_number",
                                                         "joinby": "person_id",
                                                         "filterby": "tag",
                                                         "filterfor": ("EONUMBER",),
                                                         "multiple": False,
                                                         },
                                        )

                    # Custom filter widgets
                    from s3 import S3TextFilter, S3OptionsFilter, S3DateFilter, s3_get_filter_opts
                    filter_widgets = [
                        S3TextFilter(["person_id$pe_label",
                                      "person_id$first_name",
                                      "person_id$last_name",
                                      "person_id$eo_number.value",
                                      ],
                                      label = T("Search"),
                                      ),
                        S3OptionsFilter("type_id",
                                        options = s3_get_filter_opts("dvr_case_appointment_type",
                                                                     translate = True,
                                                                     ),
                                        cols = 3,
                                        ),
                        S3OptionsFilter("status",
                                        options = s3db.dvr_appointment_status_opts,
                                        default = 2,
                                        ),
                        S3DateFilter("date",
                                     ),
                        S3OptionsFilter("person_id$dvr_case.status_id$is_closed",
                                        cols = 2,
                                        default = False,
                                        #hidden = True,
                                        label = T("Case Closed"),
                                        options = {True: T("Yes"),
                                                   False: T("No"),
                                                   },
                                        ),
                        S3TextFilter(["person_id$pe_label"],
                                     label = T("IDs"),
                                     match_any = True,
                                     hidden = True,
                                     comment = T("Search for multiple IDs (separated by blanks)"),
                                     ),
                        ]

                    resource.configure(filter_widgets = filter_widgets)

                # Default filter today's and tomorrow's appointments
                from s3 import s3_set_default_filter
                now = current.request.utcnow
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                tomorrow = today + datetime.timedelta(days=1)
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

                if r.representation == "xls":
                    # Include Person UUID
                    list_fields.append(("UUID", "person_id$uuid"))

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
    def customise_dvr_allowance_controller(**attr):

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

            resource = r.resource

            # Filter to active cases
            if not r.record:
                from s3 import FS
                query = (FS("person_id$dvr_case.archived") == False) | \
                        (FS("person_id$dvr_case.archived") == None)
                resource.add_filter(query)

            if not r.component:

                if r.interactive and not r.id:
                    # Custom filter widgets
                    from s3 import S3TextFilter, S3OptionsFilter, S3DateFilter, s3_get_filter_opts
                    date_filter = S3DateFilter("date")
                    date_filter.operator = ["eq"]

                    filter_widgets = [
                        S3TextFilter(["person_id$pe_label",
                                      "person_id$first_name",
                                      "person_id$last_name",
                                      ],
                                      label = T("Search"),
                                      ),
                        S3OptionsFilter("status",
                                        default = 2,
                                        cols = 3,
                                        options = s3db.dvr_allowance_status_opts,
                                        ),
                        date_filter,
                        ]
                    resource.configure(filter_widgets = filter_widgets)

                # Field Visibility
                table = resource.table
                field = table.case_id
                field.readable = field.writable = False

                # Custom list fields
                list_fields = [(T("ID"), "person_id$pe_label"),
                               "person_id$first_name",
                               "person_id$last_name",
                               "date",
                               "amount",
                               "currency",
                               "status",
                               "comments",
                               ]

                resource.configure(list_fields = list_fields,
                                   insertable = False,
                                   deletable = False,
                                   updatable = False,
                                   )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_dvr_allowance_controller = customise_dvr_allowance_controller

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):
        """
            Restrict list of assignees to just Staff/Volunteers
        """

        db = current.db
        s3db = current.s3db
        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person
        query = (htable.deleted == False) & \
                (htable.person_id == ptable.id)
        hrs = db(query).select(ptable.pe_id)
        hrs = [hr.pe_id for hr in hrs]

        from gluon import IS_EMPTY_OR
        from s3 import IS_ONE_OF
        s3db.project_task.pe_id.requires = IS_EMPTY_OR(
            IS_ONE_OF(db, "pr_pentity.pe_id",
                      s3db.pr_PersonEntityRepresent(show_label = False,
                                                    show_type = False),
                      sort=True,
                      filterby = "pe_id",
                      filter_opts = hrs,
                      ))

    settings.customise_project_task_resource = customise_project_task_resource

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
          name_nice = T("Residents"),
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

# =============================================================================
def drk_absence(row):
    """
        Field method to display duration of absence in
        dvr/person list view and rheader

        @param row: the Row
    """

    if hasattr(row, "cr_shelter_registration"):
        registration = row.cr_shelter_registration
    else:
        registration = None

    result = current.messages["NONE"]

    if registration is None or \
       not hasattr(registration, "registration_status") or \
       not hasattr(registration, "check_out_date"):
        # must reload
        db = current.db
        s3db = current.s3db

        person = row.pr_person if hasattr(row, "pr_person") else row
        person_id = person.id
        if not person_id:
            return result
        table = s3db.cr_shelter_registration
        query = (table.person_id == person_id) & \
                (table.deleted != True)
        registration = db(query).select(table.registration_status,
                                        table.check_out_date,
                                        limitby = (0, 1),
                                        ).first()

    if registration and \
       registration.registration_status == 3:

        T = current.T

        check_out_date = registration.check_out_date
        if check_out_date:

            delta = (current.request.utcnow - check_out_date).total_seconds()
            if delta < 0:
                delta = 0
            days = int(delta / 86400)

            if days < 1:
                result = "<1 %s" % T("Day")
            elif days == 1:
                result = "1 %s" % T("Day")
            else:
                result = "%s %s" % (days, T("Days"))

            if days >= ABSENCE_LIMIT:
                result = SPAN(result, _class="overdue")

        else:
            result = SPAN(T("Date unknown"), _class="overdue")

    return result

# =============================================================================
def drk_dvr_rheader(r, tabs=[]):
    """ DVR custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, \
                   S3ResourceHeader, \
                   s3_fullname, \
                   s3_yes_no_represent

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

            # "Case Archived" hint
            hint = lambda record: SPAN(T("Invalid Case"),
                                       _class="invalid-case",
                                       )

            if current.request.controller == "security":

                # No rheader except archived-hint
                case = resource.select(["dvr_case.archived"], as_rows=True)
                if case and case[0]["dvr_case.archived"]:
                    rheader_fields = [[(None, hint)]]
                    tabs = None
                else:
                    return None

            else:

                if not tabs:
                    tabs = [(T("Basic Details"), None),
                            (T("Family Members"), "group_membership/"),
                            (T("Activities"), "case_activity"),
                            (T("Appointments"), "case_appointment"),
                            (T("Allowance"), "allowance"),
                            (T("Presence"), "shelter_registration_history"),
                            (T("Notes"), "case_note"),
                            ]

                case = resource.select(["dvr_case.status_id",
                                        "dvr_case.status_id$code",
                                        "dvr_case.archived",
                                        "dvr_case.household_size",
                                        "dvr_case.transferable",
                                        #"dvr_case.household_transferable",
                                        #"case_flag_case.flag_id$name",
                                        "first_name",
                                        "last_name",
                                        ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows

                if case:
                    case = case[0]
                    archived = case["_row"]["dvr_case.archived"]
                    case_status = lambda row: case["dvr_case.status_id"]
                    transferable = lambda row: case["dvr_case.transferable"]
                    household_size = lambda row: case["dvr_case.household_size"]
                    #household_transferable = lambda row: case["dvr_case.household_transferable"]
                    eligible = lambda row: ""
                    name = lambda row: s3_fullname(row)
                else:
                    # Target record exists, but doesn't match filters
                    return None

                rheader_fields = [[(T("ID"), "pe_label"),
                                   (T("Case Status"), case_status),
                                   (T("Transferable"), transferable),
                                   ],
                                  [(T("Name"), name),
                                   (T("Size of Family"), household_size),
                                   #(T("Family Transferable"), household_transferable),
                                   ],
                                  ["date_of_birth",
                                   (T("Checked-out"), "absence"),
                                   ],
                                  ]

                if archived:
                    rheader_fields.insert(0, [(None, hint)])

                if r.component_name == "allowance":
                    # Rule for eligibility:
                    allowance = case["dvr_case_status.code"] in ("STATUS5", "STATUS6")
                    eligible = lambda row, allowance = allowance: \
                                      s3_yes_no_represent(allowance)
                    rheader_fields[-1].append((T("Eligible for Allowance"), eligible))

        elif tablename == "dvr_case":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Activities"), "case_activity"),
                        ]

            rheader_fields = [["reference"],
                              ["status_id"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# END =========================================================================
