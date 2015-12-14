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

    settings.base.system_name = "Village"
    settings.base.system_name_short = "Village"

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
    settings.security.policy = 5 # Controller, Function & Table ACLs

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
        PX = db(utable.name == "PX").select(utable.id,
                                            limitby=(0, 1)
                                            ).first()
        try:
            PX = PX.id
        except:
            current.log.warning("No Shelter Unit called 'PX'")
            PX = None
            NON_PX = None
            total = db(rtable.deleted == False).count()
        else:
            rows = db(rtable.deleted == False).select(rtable.shelter_unit_id)
            px_count = 0
            non_px_count = 0
            for row in rows:
                if row.shelter_unit_id == PX:
                    px_count += 1
                else:
                    non_px_count += 1
            total = px_count + non_px_count
            PX = TR(TD(T("How many in PX")),
                    TD(px_count),
                    )
            NON_PX = TR(TD(T("How many in BEA (except in PX)")),
                        TD(non_px_count),
                        )

        TOTAL = TR(TD(T("How many in BEA (total)")),
                   TD(total),
                   )

        stable = s3db.dvr_case_status
        statuses = db(stable.code.belongs(("STATUS9", "STATUS9A"))).select(stable.code,
                                                                           stable.id,
                                                                           ).as_dict(key="code")
        HOSPITAL = statuses["STATUS9"]["id"]
        POLICE = statuses["STATUS9A"]["id"]
        ctable = s3db.dvr_case
        query = (ctable.deleted == False) & \
                (ctable.archived == False) & \
                (ctable.status_id.belongs((HOSPITAL, POLICE)))
        external = db(query).count()
        EXTERNAL = TR(TD(T("How many external (Hospital / Police)")),
                      TD(external),
                      )

        free = r.record.available_capacity_day
        FREE = TR(TD(T("How many free places")),
                  TD(free),
                  )

        output = DIV(H2(r.record.name),
                        P(r.record.comments or ""),
                        TABLE(TOTAL,
                               PX,
                               NON_PX,
                               EXTERNAL,
                               FREE
                               ),
                        A("%s / %s" % (T("Check-In"), T("Check-Out")),
                          _href=r.url(method="check-in"),
                          _class="action-btn",
                          ),
                        _class="profile-header",
                        )
        return output

    settings.ui.profile_header = profile_header

    # -------------------------------------------------------------------------
    def org_site_check(site_id):
        """
            Hook for tasks["org_site_check"]:
                Check site_id & see which persons have checked-out over 3 days ago
                without checking back in (but are not in Hospital)
        """

        db = current.db
        s3db = current.s3db

        # Read the Statuses
        stable = s3db.dvr_case_status
        statuses = db(stable.code.belongs(("STATUS7", "STATUS8", "STATUS9", "STATUS9A"))).select(stable.code,
                                                                                                 stable.id,
                                                                                                 ).as_dict(key="code")
        DISAPPEARED = statuses["STATUS8"]["id"]
        LEGALLY_DEPARTED = statuses["STATUS7"]["id"]
        HOSPITAL = statuses["STATUS9"]["id"]
        POLICE = statuses["STATUS9A"]["id"]

        THREE_DAYS_AGO = current.request.utcnow - datetime.timedelta(days=3)
        table = s3db.cr_shelter_registration
        stable = s3db.cr_shelter
        ctable = s3db.dvr_case
        query = (stable.site_id == site_id) & \
                (stable.id == table.shelter_id) & \
                (table.check_out_date <= THREE_DAYS_AGO) & \
                (table.person_id == ctable.person_id) & \
                (ctable.status_id != HOSPITAL) & \
                (ctable.status_id != POLICE) & \
                (ctable.status_id != DISAPPEARED) & \
                (ctable.archived != True)
        rows = db(query).select(table.person_id,
                                table.check_in_date,
                                table.check_out_date,
                                )
        if rows:
            missing = []
            mappend = missing.append
            for row in rows:
                check_in_date = row.check_in_date
                if not check_in_date or check_in_date < row.check_out_date:
                    mappend(row.person_id)

            if missing:
                # For these users, set Case Flag to 'Suspended' & Status to 'Disappeared'
                ftable = s3db.dvr_case_flag
                flag = db(ftable.name == "Suspended").select(ftable.id,
                                                             limitby=(0, 1)
                                                             ).first()
                try:
                    SUSPENDED = flag.id
                except:
                    current.log.error("Prepop of Flag Status 'Suspended' not done")
                    return
                ltable = s3db.dvr_case_flag_case

                settings.customise_dvr_case_resource(current.request, "dvr_case")
                from gluon.tools import callback
                case_onaccept = s3db.get_config("dvr_case", "onaccept")
                for person_id in missing:
                    ltable.insert(person_id = person_id,
                                  flag_id = SUSPENDED)
                rform = db(table.person_id == missing[0]).select(table.id,
                                                                 limitby=(0, 1)
                                                                 ).first()
                cases = db(ctable.person_id.belongs(missing)).select(ctable.id,
                                                                     # For onaccept
                                                                     ctable.archived,
                                                                     ctable.person_id,
                                                                     ctable.status_id,
                                                                     )
                for case in cases:
                    case.update_record(status_id = DISAPPEARED)
                    # Clear Shelter Registration
                    form = Storage(vars=case)
                    callback(case_onaccept, form)

                # Update Shelter Capacity
                registration_onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
                registration_onaccept(rform)

                # @ToDo: Send notification of which people have been suspended to ADMIN_HEAD

    settings.org_site_check = org_site_check

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
            # @ToDo: Check to see if they DISAPPEARED, etc
            error = T("Registration not found")
            warning = None
            return error, warning

        error = None
        if registration.registration_status == 2:
            warning = T("Client was already checked-in")
        else:
            warning = None

        # Update the Shelter Registration
        registration.update_record(checked_in_date = current.request.utcnow,
                                   registration_status = 2,
                                   )

        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)

        return error, warning

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
        registration.update_record(checked_out_date = current.request.utcnow,
                                   registration_status = 3)

        onaccept = s3db.get_config("cr_shelter_registration", "onaccept")
        if onaccept:
            onaccept(registration)

        return error, warning

    # -------------------------------------------------------------------------
    def customise_auth_user_resource(r, resource):

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
                current.s3db.configure("cr_shelter",
                                       site_check_in = site_check_in,
                                       site_check_out = site_check_out,
                                       )
            else:
                has_role = current.auth.s3_has_role
                if has_role("SECURITY") and not has_role("ADMIN"):
                   return None
            return result
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
    # DVR Module Settings and Customizations
    #
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

            if r.controller == "security":
                # Restricted view for Security staff
                if r.component:
                    redirect(r.url(method=""))

                # Filter to persons who have a case registered
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

            elif r.controller == "dvr" and not r.component:

                # Additional component "EasyOpt Number"
                s3db.add_components("pr_person",
                                    pr_person_tag = {"name": "eo_number",
                                                     "joinby": "person_id",
                                                     "filterby": "tag",
                                                     "filterfor": ("EONUMBER",),
                                                     "multiple": False,
                                                     },
                                    )

                from gluon import IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY

                #default_organisation = current.auth.root_org()
                default_organisation = settings.get_org_default_organisation()

                ctable = s3db.dvr_case

                # Case is valid for 5 years
                field = ctable.valid_until
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

                    # Configure person_details fields
                    ctable = s3db.pr_person_details

                    field = ctable.marital_status
                    options = dict(s3db.pr_marital_status_opts)
                    del options[9] # Remove "other"
                    field.requires = IS_IN_SET(options, zero=None)

                    # Configure person fields
                    table = resource.table

                    field = table.gender
                    field.default = None
                    from s3 import IS_PERSON_GENDER
                    options = dict(s3db.pr_gender_opts)
                    del options[1] # Remove "unknown"
                    field.requires = IS_PERSON_GENDER(options, sort = True)

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
                                "dvr_case.archived",
                                )
                    resource.configure(crud_form = crud_form,
                                       )

                    # Remove filter default for case status
                    filter_widgets = resource.get_config("filter_widgets")
                    if filter_widgets:

                        from s3 import S3TextFilter, S3DateFilter

                        for fw in filter_widgets:
                            if fw.field == "dvr_case.status_id":
                                fw.opts.default = None
                            if isinstance(fw, S3TextFilter):
                                fw.field.append("eo_number.value")

                        # Filter by date of birth
                        dob_filter = S3DateFilter("date_of_birth")
                        #dob_filter.operator = ["eq"]
                        filter_widgets.insert(1, dob_filter)

                        # Filter for IDs
                        id_filter = S3TextFilter(["pe_label"],
                                                 label = T("IDs"),
                                                 match_any = True,
                                                 hidden = True,
                                                 comment = T("Search for multiple IDs (separated by blanks)"),
                                                 )
                        filter_widgets.append(id_filter)

                        # Filter by registration date
                        reg_filter = S3DateFilter("dvr_case.date",
                                                  hidden = True,
                                                  )
                        filter_widgets.append(reg_filter)

                # Custom list fields (must be outside of r.interactive)
                list_fields = [(T("ID"), "pe_label"),
                               (T("EasyOpt No."), "eo_number.value"),
                               "last_name",
                               "first_name",
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
        if current.request.controller == "security":
            attr["rheader"] = ""
        else:
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
                               ]
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
            If archived or status in (DISAPPEARED, LEGALLY_DEPARTED) then
                remove shelter_registration
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
                status = db(stable.id == status_id).select(stable.code,
                                                           limitby = (0, 1)
                                                           ).first()
                try:
                    if status.code in ("STATUS7", "STATUS8"):
                        cancel = True
                except:
                    current.log.error("Status %s not found" % status_id)
                    return

        if cancel:
            rtable = s3db.cr_shelter_registration
            registration = db(rtable.person_id == form_vars.person_id).select(rtable.id,
                                                                              limitby=(0, 1)
                                                                              ).first()
            try:
                resource = s3db.resource("cr_shelter_registration", id=registration.id)
            except:
                pass
            else:
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
    def dvr_case_flag_case_onaccept(form):
        """
            If flag is SUSPENDED then
                remove shelter_registration
        """

        cancel = False
        form_vars = form.vars
        flag_id = form_vars.flag_id
        if flag_id:
            db = current.db
            s3db = current.s3db
            ftable = s3db.dvr_case_flag
            flag = db(ftable.id == flag_id).select(ftable.name,
                                                   limitby = (0, 1)
                                                   ).first()
            try:
                if flag.name == "Suspended":
                    cancel = True
            except:
                current.log.error("Flag %s not found" % flag_id)
                return

        if cancel:
            resource = s3db.resource("cr_shelter_registration", id=form_vars.person_id)
            resource.delete()

    # -------------------------------------------------------------------------
    def customise_dvr_case_flag_case_resource(r, tablename):

        s3db = current.s3db
        default_onaccept = s3db.get_config(tablename, "onaccept")
        if default_onaccept and not isinstance(default_onaccept, list): # Catch running twice
            onaccept = [default_onaccept,
                        dvr_case_flag_case_onaccept,
                        ]
        else:
            onaccept = dvr_case_flag_case_onaccept
        s3db.configure(tablename,
                       onaccept = onaccept,
                       )

    settings.customise_dvr_case_flag_case_resource = customise_dvr_case_flag_case_resource

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

            # Filter to current cases
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

            # Filter to current cases
            if not r.record:
                from s3 import FS
                query = (FS("person_id$dvr_case.archived") == False) | \
                        (FS("person_id$dvr_case.archived") == None)
                resource.add_filter(query)

            if not r.component:

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

            # Filter to current cases
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
def drk_dvr_rheader(r, tabs=[]):
    """ DVR custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader, s3_fullname, s3_yes_no_represent
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

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Family Members"), "group_membership/"),
                        (T("Activities"), "case_activity"),
                        (T("Appointments"), "case_appointment"),
                        (T("Allowance"), "allowance"),
                        (T("Notes"), "case_note"),
                        ]

            case = resource.select(["dvr_case.status_id",
                                    "dvr_case.status_id$code",
                                    "case_flag_case.flag_id$name",
                                    "first_name",
                                    "last_name",
                                    ],
                                    represent = True,
                                    raw_data = True,
                                    ).rows
            if case:
                case = case[0]
                case_status = lambda row: case["dvr_case.status_id"]
                flags = case._row["dvr_case_flag.name"]
                if flags:
                    if type(flags) is not list:
                        flags = [flags]
                    suspended = "Suspended" in flags
                else:
                    suspended = False
                case_suspended = lambda row: s3_yes_no_represent(suspended)
                eligible = lambda row: ""
                name = lambda row: s3_fullname(row)
            else:
                # Target record exists, but doesn't match filters
                return None

            rheader_fields = [[(T("ID"), "pe_label"), (T("Case Status"), case_status)],
                              [(T("Name"), name), (T("Suspended"), case_suspended)],
                              ["date_of_birth"],
                              ]

            if r.component_name == "allowance":
                # Rule for eligibility:
                allowance = case["dvr_case_status.code"] in ("STATUS5", "STATUS6") and \
                            not suspended
                eligible = lambda row, allowance=allowance: \
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
