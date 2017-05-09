# -*- coding: utf-8 -*-

import datetime

from collections import OrderedDict

from gluon import current, SPAN
from gluon.storage import Storage

from s3 import FS, IS_ONE_OF, S3DateTime, S3Method, s3_str, s3_unicode

def config(settings):
    """
        DRKCM Template: Case Management, German Red Cross
    """

    T = current.T

    settings.base.system_name = "RefuScope"
    settings.base.system_name_short = "RefuScope"

    # PrePopulate data
    settings.base.prepopulate += ("DRKCM", "default/users", "DRKCM/Demo")

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
       ("de", "Deutsch"),
       ("en", "English"),
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
    settings.security.policy = 7 # Hierarchical Realms

    # Version details on About-page require login
    settings.security.version_info_requires_login = True

    # -------------------------------------------------------------------------
    # CMS Module Settings
    #
    settings.cms.hide_index = True

    # -------------------------------------------------------------------------
    # Human Resource Module Settings
    #
    settings.hrm.teams_orgs = False

    # -------------------------------------------------------------------------
    # Organisations Module Settings
    #
    settings.org.branches = True

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
    settings.project.my_tasks_include_team_tasks = True

    # -------------------------------------------------------------------------
    # DVR Module Settings and Customizations
    #
    # Uncomment this to enable household size in cases, set to "auto" for automatic counting
    settings.dvr.household_size = "auto"
    # Uncomment this to enable features to manage case flags
    #settings.dvr.case_flags = True
    # Case activities use single Needs
    #settings.dvr.case_activity_needs_multiple = True
    # Uncomment this to expose flags to mark appointment types as mandatory
    settings.dvr.mandatory_appointments = True
    # Uncomment this to have appointments with personal presence update last_seen_on
    settings.dvr.appointments_update_last_seen_on = True
    # Uncomment this to have allowance payments update last_seen_on
    settings.dvr.payments_update_last_seen_on = True
    # Uncomment this to automatically update the case status when appointments are completed
    settings.dvr.appointments_update_case_status = True
    # Uncomment this to automatically close appointments when registering certain case events
    settings.dvr.case_events_close_appointments = True
    # Uncomment this to allow cases to belong to multiple case groups ("households")
    #settings.dvr.multiple_case_groups = True
    # Configure a regular expression pattern for ID Codes (QR Codes)
    settings.dvr.id_code_pattern = "(?P<label>[^,]*),(?P<family>[^,]*),(?P<last_name>[^,]*),(?P<first_name>[^,]*),(?P<date_of_birth>[^,]*),.*"
    # Issue a "not checked-in" warning in case event registration
    settings.dvr.event_registration_checkin_warning = True

    # Response types hierarchical ("Interventions")
    #settings.dvr.response_types_hierarchical = True

    # -------------------------------------------------------------------------
    def customise_dvr_home():
        """ Redirect dvr/index to dvr/person?closed=0 """

        from gluon import URL
        from s3 import s3_redirect_default

        s3_redirect_default(URL(f="person", vars={"closed": "0"}))

    settings.customise_dvr_home = customise_dvr_home

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db
        auth = current.auth

        has_permission = auth.s3_has_permission

        # Users who can not register new residents also have
        # only limited write-access to basic details of residents
        if r.controller == "dvr" and not has_permission("create", "pr_person"):

            # Can not write any fields in main person record
            # (fields in components may still be writable, though)
            ptable = s3db.pr_person
            for field in ptable:
                field.writable = False

            # Can not add or edit contact data in person form
            s3db.configure("pr_contact", insertable=False)

            # Can not update shelter registration from person form
            # - check-in/check-out may still be permitted, however
            # - STAFF can update housing unit

            is_staff = auth.s3_has_role("STAFF")

            rtable = s3db.cr_shelter_registration
            for field in rtable:
                if field.name != "shelter_unit_id" or not is_staff:
                    field.writable = False

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def configure_person_tags():
        """
            Configure filtered pr_person_tag components for
            registration numbers:
                - BAMF Registration Number (tag=BAMF)
        """

        current.s3db.add_components("pr_person",
                                    pr_person_tag = ({"name": "bamf",
                                                      "joinby": "person_id",
                                                      "filterby": {
                                                        "tag": "BAMF",
                                                        },
                                                      "multiple": False,
                                                      },
                                                     )
                                    )

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        db = current.db
        s3 = current.response.s3

        auth = current.auth
        s3db = current.s3db

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            archived = r.get_vars.get("archived")
            if archived in ("1", "true", "yes"):
                crud_strings = s3.crud_strings["pr_person"]
                crud_strings["title_list"] = T("Invalid Cases")

            if r.controller == "dvr":

                from gluon import Field, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY

                resource = r.resource
                configure = resource.configure

                table = r.table
                ctable = s3db.dvr_case

                if not r.component:

                    # Can the user see cases from more than one org?
                    realms = auth.permission.permitted_realms("dvr_case", "read")
                    if realms is None or len(realms) > 1:
                        multiple_orgs = True
                    else:
                        multiple_orgs = False

                    configure_person_tags()

                    if r.interactive and r.method != "import":

                        from s3 import S3SQLCustomForm, \
                                       S3SQLInlineComponent, \
                                       S3SQLInlineLink, \
                                       S3TextFilter, \
                                       S3DateFilter, \
                                       S3OptionsFilter, \
                                       IS_PERSON_GENDER

                        # Default organisation
                        ctable = s3db.dvr_case
                        field = ctable.organisation_id
                        user_org = auth.user.organisation_id if auth.user else None
                        if user_org:
                            field.default = user_org

                        # Organisation is required
                        requires = field.requires
                        if isinstance(requires, IS_EMPTY_OR):
                            field.requires = requires.other

                        # Make marital status mandatory, remove "other"
                        dtable = s3db.pr_person_details
                        field = dtable.marital_status
                        options = dict(s3db.pr_marital_status_opts)
                        del options[9] # Remove "other"
                        field.requires = IS_IN_SET(options, zero=None)

                        # Make gender mandatory, remove "unknown"
                        field = table.gender
                        field.default = None
                        options = dict(s3db.pr_gender_opts)
                        del options[1] # Remove "unknown"
                        field.requires = IS_PERSON_GENDER(options, sort = True)

                        # No comment for pe_label
                        field = table.pe_label
                        field.comment = None

                        # Last name is required
                        field = table.last_name
                        field.requires = IS_NOT_EMPTY()

                        # Custom CRUD form
                        crud_form = S3SQLCustomForm(

                            # Case Details ----------------------------
                            "dvr_case.organisation_id",
                            (T("Case Status"), "dvr_case.status_id"),
                            #S3SQLInlineLink("case_flag",
                            #                label = T("Flags"),
                            #                field = "flag_id",
                            #                help_field = "comments",
                            #                cols = 4,
                            #                ),

                            # Person Details --------------------------
                            (T("ID"), "pe_label"),
                            "last_name",
                            "first_name",
                            "person_details.nationality",
                            "date_of_birth",
                            "gender",
                            "person_details.marital_status",

                            # Process Data ----------------------------
                            "dvr_case.site_id",
                            S3SQLInlineComponent(
                                    "address",
                                    label = T("Current Address"),
                                    fields = [("", "location_id"),
                                              ],
                                    filterby = {"field": "type",
                                                "options": "1",
                                                },
                                    link = False,
                                    multiple = False,
                                    ),
                            (T("Date of Arrival"), "dvr_case.date"),
                            S3SQLInlineComponent(
                                    "bamf",
                                    fields = [("", "value"),
                                              ],
                                    filterby = {"field": "tag",
                                                "options": "BAMF",
                                                },
                                    label = T("BAMF Reference Number"),
                                    multiple = False,
                                    name = "bamf",
                                    ),
                            "dvr_case.valid_until",
                            "dvr_case.stay_permit_until",

                            # Other Details ---------------------------
                            "person_details.occupation",
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

                            # Archived-flag ---------------------------
                            (T("Invalid"), "dvr_case.archived"),
                            )

                        # Custom filter widgets

                        # Extract case status options from original filter widget
                        status_opts = None
                        filter_widgets = resource.get_config("filter_widgets")
                        for fw in filter_widgets:
                            if fw.field == "dvr_case.status_id":
                                status_opts = fw.opts.get("options")
                                break
                        if status_opts is None:
                            # Fallback
                            status_opts = s3db.dvr_case_status_filter_opts

                        filter_widgets = [
                            S3TextFilter(["pe_label",
                                          "first_name",
                                          "middle_name",
                                          "last_name",
                                          "dvr_case.comments",
                                          ],
                                          label = T("Search"),
                                          comment = T("You can search by name, ID or comments"),
                                          ),
                            S3DateFilter("date_of_birth",
                                         hidden = True,
                                         ),
                            S3OptionsFilter("dvr_case.status_id",
                                            cols = 3,
                                            #default = None,
                                            #label = T("Case Status"),
                                            options = status_opts,
                                            sort = False,
                                            hidden = True,
                                            ),
                            S3OptionsFilter("person_details.nationality",
                                            hidden = True,
                                            ),
                            S3DateFilter("dvr_case.date",
                                         hidden = True,
                                         ),
                            S3TextFilter(["bamf.value"],
                                         label = T("BAMF Ref.No."),
                                         hidden = True,
                                         ),
                            S3TextFilter(["pe_label"],
                                         label = T("IDs"),
                                         match_any = True,
                                         hidden = True,
                                         comment = T("Search for multiple IDs (separated by blanks)"),
                                         ),
                            ]
                        if multiple_orgs:
                            filter_widgets.insert(1,
                                                  S3OptionsFilter("dvr_case.organisation_id"),
                                                  )

                        configure(crud_form = crud_form,
                                  filter_widgets = filter_widgets,
                                  )

                    # Custom list fields (must be outside of r.interactive)
                    list_fields = [(T("ID"), "pe_label"),
                                   "last_name",
                                   "first_name",
                                   "date_of_birth",
                                   "gender",
                                   "person_details.nationality",
                                   "dvr_case.date",
                                   "dvr_case.status_id",
                                   "dvr_case.site_id",
                                   ]
                    if multiple_orgs:
                        list_fields.insert(-1, "dvr_case.organisation_id")

                    configure(list_fields = list_fields)

            return result
        s3.prep = custom_prep

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
            if r.controller == "dvr":

                if r.interactive:
                    table = resource.table

                    from gluon import IS_EMPTY_OR
                    from s3 import IS_ADD_PERSON_WIDGET2, S3AddPersonWidget2

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

                    # Custom CRUD strings for this perspective
                    s3.crud_strings["pr_group_membership"] = Storage(
                        label_create = T("Add Family Member"),
                        title_display = T("Family Member Details"),
                        title_list = T("Family Members"),
                        title_update = T("Edit Family Member"),
                        label_list_button = T("List Family Members"),
                        label_delete_button = T("Remove Family Member"),
                        msg_record_created = T("Family Member added"),
                        msg_record_modified = T("Family Member updated"),
                        msg_record_deleted = T("Family Member removed"),
                        msg_list_empty = T("No Family Members currently registered")
                        )

                list_fields = [(T("ID"), "person_id$pe_label"),
                               "person_id",
                               "person_id$date_of_birth",
                               "person_id$gender",
                               "group_head",
                               (ROLE, "role_id"),
                               (T("Case Status"), "person_id$dvr_case.status_id"),
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
    def customise_dvr_case_resource(r, tablename):

        s3db = current.s3db
        ctable = s3db.dvr_case

        # Expose expiration dates
        field = ctable.valid_until
        field.label = T("BÜMA valid until")
        field.readable = field.writable = True
        field = ctable.stay_permit_until
        field.readable = field.writable = True

        # Set all fields read-only except comments, unless
        # the user has permission to create cases
        if not current.auth.s3_has_permission("create", "dvr_case"):
            for field in ctable:
                if field.name != "comments":
                    field.writable = False

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

        auth = current.auth

        if not auth.s3_has_role("ADMIN"):

            # Restrict access by note type
            GENERAL = "General"
            MEDICAL = "Medical"
            SECURITY = "Security"

            permitted_note_types = [GENERAL]

            user = auth.user
            if user:
                # Roles permitted to access "Security" type notes
                SECURITY_ROLES = ("ADMIN_HEAD",
                                  "SECURITY_HEAD",
                                  "POLICE",
                                  "MEDICAL",
                                  )

                # Roles permitted to access "Health" type notes
                MEDICAL_ROLES = ("ADMIN_HEAD",
                                 "MEDICAL",
                                 )

                # Get role IDs
                db = current.db
                s3db = current.s3db
                gtable = s3db.auth_group
                roles = db(gtable.deleted != True).select(gtable.uuid,
                                                          gtable.id,
                                                          ).as_dict(key = "uuid")

                realms = user.realms

                security_roles = (roles[uuid]["id"]
                                  for uuid in SECURITY_ROLES if uuid in roles)
                if any(role in realms for role in security_roles):
                    permitted_note_types.append(SECURITY)

                medical_roles = (roles[uuid]["id"]
                                 for uuid in MEDICAL_ROLES if uuid in roles)
                if any(role in realms for role in medical_roles):
                    permitted_note_types.append(MEDICAL)

            # Filter notes to permitted note types
            query = FS("note_type_id$name").belongs(permitted_note_types)
            if r.tablename == "dvr_note":
                r.resource.add_filter(query)
            else:
                r.resource.add_component_filter("case_note", query)

            # Filter note type selector to permitted note types
            ttable = s3db.dvr_note_type
            query = ttable.name.belongs(permitted_note_types)
            rows = db(query).select(ttable.id)
            note_type_ids = [row.id for row in rows]

            table = s3db.dvr_note
            field = table.note_type_id
            field.label = T("Category")

            if len(note_type_ids) == 1:
                field.default = note_type_ids[0]
                field.writable = False

            field.requires = IS_ONE_OF(db(query), "dvr_note_type.id",
                                       field.represent,
                                       )

    settings.customise_dvr_note_resource = customise_dvr_note_resource

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_resource(r, tablename):

        auth = current.auth
        s3db = current.s3db

        if r.interactive or r.representation == "aadata":

            # Can the user see cases from more than one org?
            realms = auth.permission.permitted_realms("dvr_case", "read")
            if realms is None or len(realms) > 1:
                multiple_orgs = True
            else:
                multiple_orgs = False

            from gluon import IS_IN_SET
            from gluon.sqlhtml import OptionsWidget
            from s3 import S3SQLCustomForm, \
                           S3SQLInlineLink, \
                           S3SQLInlineComponent, \
                           S3TextFilter, \
                           S3OptionsFilter, \
                           S3DateFilter, \
                           s3_get_filter_opts

            table = s3db.dvr_case_activity

            # Represent person_id as link
            field = table.person_id
            field.represent = s3db.pr_PersonRepresent(show_link=True)

            # Customise Priority
            field = table.priority
            field.label = T("Priority")
            field.readable = field.writable = True

            # Customise "completed" flag
            # => label as "Status" and use drop-down for open/closed
            CURRENT = T("Current")
            COMPLETED = T("Completed")
            field = table.completed
            field.label = T("Status")
            field.represent = lambda v, row=None: COMPLETED if v else CURRENT
            field.requires = [IS_IN_SET([(False, CURRENT),
                                         (True, COMPLETED),
                                         ],
                                        zero=None,
                                        ),
                              # Form option is a str => convert to boolean
                              lambda v: (str(v) == "True", None),
                              ]
            field.widget = OptionsWidget.widget

            # Show end_date field (read-only)
            field = table.end_date
            field.label = T("Completed on")
            field.readable = True

            crud_form = S3SQLCustomForm(
                            "person_id",

                            (T("Need established on"), "start_date"),

                            "need_id",
                            "need_details",

                            S3SQLInlineLink("response_type",
                                            label = T("Interventions"),
                                            field = "response_type_id",
                                            #widget = "hierarchy",
                                            multiple = True,
                                            #leafonly = True,
                                            ),
                            (T("Intervention Details"), "activity_details"),

                            #"priority",
                            "emergency",

                            "followup",
                            "followup_date",

                            "completed",
                            "end_date",

                            "outcome",

                            S3SQLInlineComponent(
                                "document",
                                name = "file",
                                label = T("Attachments"),
                                fields = ["file", "comments"],
                                filterby = {"field": "file",
                                            "options": "",
                                            "invert": True,
                                            },
                                ),
                            "comments",
                            )

            # Filter widgets
            filter_widgets = [
                S3TextFilter(["person_id$pe_label",
                              "person_id$first_name",
                              "person_id$last_name",
                              "case_id$reference",
                              "need_details",
                              "activity_details",
                              ],
                              label = T("Search"),
                              ),
                S3OptionsFilter("emergency",
                                options = {True: T("Yes"),
                                           False: T("No"),
                                           },
                                cols = 2,
                                ),
                S3OptionsFilter("need_id",
                                options = lambda: s3_get_filter_opts("dvr_need",
                                                                     translate = True,
                                                                     ),
                                ),
                S3OptionsFilter("completed",
                                default = False,
                                options = {True: COMPLETED,
                                           False: CURRENT,
                                           },
                                cols = 2,
                                ),
                S3OptionsFilter("followup",
                                label = T("Follow-up required"),
                                options = {True: T("Yes"),
                                           False: T("No"),
                                           },
                                cols = 2,
                                hidden = True,
                                ),
                S3DateFilter("followup_date",
                             cols = 2,
                             hidden = True,
                             ),
                ]
            if multiple_orgs:
                filter_widgets.insert(1,
                                      S3OptionsFilter("person_id$dvr_case.organisation_id"),
                                      )

            s3db.configure("dvr_case_activity",
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           )

        # Custom list fields for case activity component tab
        if r.tablename != "dvr_case_activity":
            list_fields = ["start_date",
                           "need_id",
                           #"need_details",
                           "emergency",
                           (T("Interventions"),
                            "response_type__link.response_type_id",
                            ),
                           #"activity_details",
                           "followup",
                           "followup_date",
                           "completed",
                           ]

            # Custom list fields
            s3db.configure("dvr_case_activity",
                           list_fields = list_fields,
                           )

    settings.customise_dvr_case_activity_resource = customise_dvr_case_activity_resource

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
                query = (FS("person_id$dvr_case.archived") == False) | \
                        (FS("person_id$dvr_case.archived") == None)
                resource.add_filter(query)

            if not r.component:
                filter_widgets = resource.get_config("filter_widgets")
                if filter_widgets:

                    configure_person_tags()

                # Custom list fields
                list_fields = [(T("ID"), "person_id$pe_label"),
                               (T("Person"), "person_id"),
                               "start_date",
                               "need_id",
                               #"need_details",
                               "emergency",
                               (T("Interventions"),
                                "response_type__link.response_type_id",
                                ),
                               #"activity_details",
                               "followup",
                               "followup_date",
                               "completed",
                               ]

            # Custom list fields
            resource.configure(list_fields = list_fields,
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
                query = (FS("person_id$dvr_case.archived") == False) | \
                        (FS("person_id$dvr_case.archived") == None)
                resource.add_filter(query)

            if not r.component:

                configure_person_tags()

                if r.interactive and not r.id:

                    # Custom filter widgets
                    from s3 import S3TextFilter, S3OptionsFilter, S3DateFilter, s3_get_filter_opts
                    filter_widgets = [
                        S3TextFilter(["person_id$pe_label",
                                      "person_id$first_name",
                                      "person_id$last_name",
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
                now = r.utcnow
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
    def customise_org_facility_resource(r, tablename):

        s3db = current.s3db

        # Hide "code" field (not needed)
        table = s3db.org_facility
        field = table.code
        field.readable = field.writable = False

        # Location selector just needs country + address
        from s3 import S3LocationSelector
        field = table.location_id
        field.widget = S3LocationSelector(levels = ["L0"],
                                          show_address=True,
                                          show_map = False,
                                          )

        field = table.obsolete
        field.label = T("Inactive")
        field.represent = lambda opt: T("Inactive") if opt else current.messages["NONE"]

        # Custom list fields
        list_fields = ["name",
                       "site_facility_type.facility_type_id",
                       "organisation_id",
                       "location_id",
                       "contact",
                       "phone1",
                       "phone2",
                       "email",
                       #"website",
                       "obsolete",
                       "comments",
                       ]

        # Custom filter widgets
        from s3 import S3TextFilter, S3OptionsFilter, s3_get_filter_opts
        filter_widgets = [S3TextFilter(["name",
                                        "organisation_id$name",
                                        "organisation_id$acronym",
                                        "comments",
                                        ],
                                        label = T("Search"),
                                       ),
                          S3OptionsFilter("site_facility_type.facility_type_id",
                                          options = s3_get_filter_opts("org_facility_type",
                                                                       translate = True,
                                                                       ),
                                          ),
                          S3OptionsFilter("organisation_id",
                                          ),
                          S3OptionsFilter("obsolete",
                                          options = {False: T("No"),
                                                     True: T("Yes"),
                                                     },
                                          default = [False],
                                          cols = 2,
                                          )
                          ]

        s3db.configure("org_facility",
                       #deletable = False,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        # Allow selection of all countries
        current.deployment_settings.gis.countries = []

        # Custom rheader+tabs
        if current.request.controller == "org":
            attr = dict(attr)
            attr["rheader"] = drk_org_rheader

        return attr

    settings.customise_org_facility_controller = customise_org_facility_controller

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):
        """
            Restrict list of assignees to just Staff/Volunteers
        """

        db = current.db
        s3db = current.s3db

        # Configure custom form for tasks
        from s3 import S3SQLCustomForm, S3SQLInlineLink
        crud_form = S3SQLCustomForm("name",
                                    "status",
                                    "priority",
                                    "description",
                                    "source",
                                    S3SQLInlineLink("shelter_inspection_flag",
                                                    field="inspection_flag_id",
                                                    label=T("Shelter Inspection"),
                                                    readonly=True,
                                                    render_list=True,
                                                    ),
                                    "pe_id",
                                    "date_due",
                                    )
        s3db.configure("project_task",
                       crud_form = crud_form,
                       )

        # Filter assignees to human resources
        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person
        query = (htable.deleted == False) & \
                (htable.person_id == ptable.id)
        rows = db(query).select(ptable.pe_id)
        pe_ids = set(row.pe_id for row in rows)

        # ...and teams
        gtable = s3db.pr_group
        query = (gtable.group_type == 3) & \
                (gtable.deleted == False)
        rows = db(query).select(gtable.pe_id)
        pe_ids |= set(row.pe_id for row in rows)

        from gluon import IS_EMPTY_OR
        s3db.project_task.pe_id.requires = IS_EMPTY_OR(
            IS_ONE_OF(db, "pr_pentity.pe_id",
                      s3db.pr_PersonEntityRepresent(show_label = False,
                                                    show_type = True,
                                                    ),
                      sort = True,
                      filterby = "pe_id",
                      filter_opts = pe_ids,
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
          name_nice = T("Case Management"),
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
                            (T("Photos"), "image"),
                            (T("Notes"), "case_note"),
                            ]

                case = resource.select(["first_name",
                                        "last_name",
                                        "dvr_case.status_id",
                                        "dvr_case.archived",
                                        "dvr_case.household_size",
                                        "dvr_case.organisation_id",
                                        "dvr_case.site_id",
                                        ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows

                if case:
                    # Extract case data
                    case = case[0]
                    name = lambda row: s3_fullname(row)
                    case_status = lambda row: case["dvr_case.status_id"]
                    archived = case["_row"]["dvr_case.archived"]
                    household_size = lambda row: case["dvr_case.household_size"]
                    organisation = lambda row: case["dvr_case.organisation_id"]
                    facility = lambda row: case["dvr_case.site_id"]
                else:
                    # Target record exists, but doesn't match filters
                    return None

                rheader_fields = [[(T("ID"), "pe_label"),
                                   (T("Case Status"), case_status),
                                   (T("Organisation"), organisation),
                                   ],
                                  [(T("Name"), name),
                                   (T("Size of Family"), household_size),
                                   (T("Facility"), facility),
                                   ],
                                  ["date_of_birth",
                                   ],
                                  ]

                if archived:
                    rheader_fields.insert(0, [(None, hint)])

                # Generate rheader XML
                rheader = S3ResourceHeader(rheader_fields, tabs)(
                                r,
                                table = resource.table,
                                record = record,
                                )

                # Add profile picture
                from gluon import A, URL
                from s3 import s3_avatar_represent
                record_id = record.id
                rheader.insert(0, A(s3_avatar_represent(record_id,
                                                        "pr_person",
                                                        _class = "rheader-avatar",
                                                        ),
                                    _href=URL(f = "person",
                                              args = [record_id, "image"],
                                              vars = r.get_vars,
                                              ),
                                    )
                               )

                return rheader

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

# =============================================================================
def drk_org_rheader(r, tabs=[]):
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

        if tablename == "org_facility":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

            rheader_fields = [["name", "email"],
                              ["organisation_id", "phone1"],
                              ["location_id", "phone2"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# END =========================================================================
