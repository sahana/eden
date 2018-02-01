# -*- coding: utf-8 -*-

import datetime

from collections import OrderedDict

from gluon import current, A, DIV, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY, SPAN, URL
from gluon.storage import Storage

from s3 import FS, IS_ONE_OF, S3DateTime, S3Method, s3_str, s3_unicode
from s3dal import original_tablename

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
    settings.auth.password_retrieval = False

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("DE",)
    gis_levels = ("L1", "L2", "L3")
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
       ("de", "German"),
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
    settings.security.policy = 7 # Hierarchical Realms

    # Version details on About-page require login
    settings.security.version_info_requires_login = True

    # -------------------------------------------------------------------------
    # General UI settings
    #
    settings.ui.calendar_clear_icon = True

    # -------------------------------------------------------------------------
    # Realm Rules
    #
    def drk_realm_entity(table, row):
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
            ctable = s3db.dvr_case
            query = (ctable.person_id == row.id) & \
                    (ctable.deleted == False)
            case = db(query).select(ctable.organisation_id,
                                    limitby = (0, 1),
                                    ).first()

            if case and case.organisation_id:
                realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                 case.organisation_id,
                                                 )

        elif tablename in ("dvr_case_activity",
                           "dvr_case_details",
                           "dvr_case_flag_case",
                           "dvr_case_language",
                           "dvr_note",
                           "dvr_residence_status",
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

        elif tablename in ("dvr_case_activity_need",
                           "dvr_case_activity_update",
                           "dvr_response_action",
                           ):

            # Inherit from case activity
            table = s3db.table(tablename)
            atable = s3db.dvr_case_activity
            query = (table._id == row.id) & \
                    (atable.id == table.case_activity_id)
            activity = db(query).select(atable.realm_entity,
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

    settings.auth.realm_entity = drk_realm_entity

    # -------------------------------------------------------------------------
    # CMS Module Settings
    #
    settings.cms.hide_index = True

    # -------------------------------------------------------------------------
    # Human Resource Module Settings
    #
    settings.hrm.teams_orgs = True
    settings.hrm.staff_departments = False

    settings.hrm.use_id = False
    settings.hrm.use_address = True
    settings.hrm.use_description = False

    settings.hrm.use_trainings = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_awards = False

    settings.hrm.use_skills = False
    settings.hrm.staff_experience = False
    settings.hrm.vol_experience = False

    # -------------------------------------------------------------------------
    # Organisations Module Settings
    #
    settings.org.branches = True
    settings.org.offices_tab = False

    # -------------------------------------------------------------------------
    # Persons Module Settings
    #
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    settings.pr.contacts_tabs = {"all": "Contact Info"}

    # -------------------------------------------------------------------------
    # DVR Module Settings and Customizations
    #
    # Enable features to manage case flags
    settings.dvr.case_flags = True
    # Allow cases to belong to multiple case groups ("households")
    #settings.dvr.multiple_case_groups = True

    # Enable household size in cases, "auto" for automatic counting
    settings.dvr.household_size = "auto"

    # Group/Case activities per sector
    settings.dvr.activity_sectors = True
    # Case activities use status field
    settings.dvr.case_activity_use_status = True
    # Case activities cover multiple needs
    settings.dvr.case_activity_needs_multiple = True

    # Manage individual response actions in case activities
    settings.dvr.manage_response_actions = True
    # Response types hierarchical
    settings.dvr.response_types_hierarchical = True

    # Expose flags to mark appointment types as mandatory
    settings.dvr.mandatory_appointments = False
    # Appointments with personal presence update last_seen_on
    settings.dvr.appointments_update_last_seen_on = False
    # Automatically update the case status when appointments are completed
    settings.dvr.appointments_update_case_status = False
    # Automatically close appointments when registering certain case events
    settings.dvr.case_events_close_appointments = True

    # Allowance payments update last_seen_on
    #settings.dvr.payments_update_last_seen_on = True

    # Configure a regular expression pattern for ID Codes (QR Codes)
    #settings.dvr.id_code_pattern = "(?P<label>[^,]*),(?P<family>[^,]*),(?P<last_name>[^,]*),(?P<first_name>[^,]*),(?P<date_of_birth>[^,]*),.*"
    # Issue a "not checked-in" warning in case event registration
    #settings.dvr.event_registration_checkin_warning = True

    # -------------------------------------------------------------------------
    def customise_doc_document_resource(r, tablename):

        if r.controller == "dvr":

            s3db = current.s3db
            table = s3db.doc_document

            # Hide URL field
            field = table.url
            field.readable = field.writable = False

            # Custom label for date-field
            field = table.date
            field.label = T("Uploaded on")
            field.default = r.utcnow.date()
            field.writable = False

            # Custom label for name-field
            field = table.name
            field.label = T("Title")

            # List fields
            list_fields = ["name",
                           "file",
                           "date",
                           "comments",
                           ]
            s3db.configure("doc_document",
                           list_fields = list_fields,
                           )

    settings.customise_doc_document_resource = customise_doc_document_resource

    # -------------------------------------------------------------------------
    def customise_doc_document_controller(**attr):

        current.deployment_settings.ui.export_formats = None

        if current.request.controller == "dvr":

            # Use custom rheader for case perspective
            attr["rheader"] = drk_dvr_rheader

            # Set contacts-method to retain the tab
            s3db = current.s3db
            s3db.set_method("pr", "person",
                            method = "contacts",
                            action = s3db.pr_Contacts,
                            )

        return attr

    settings.customise_doc_document_controller = customise_doc_document_controller

    # -------------------------------------------------------------------------
    def customise_dvr_home():
        """ Do not redirect to person-controller """

        return {"module_name": T("Case Consulting"),
                }

    settings.customise_dvr_home = customise_dvr_home

    # -------------------------------------------------------------------------
    def pr_address_onaccept(form):
        """
            Custom onaccept to set the person's Location to the Private Address
            - unless their case is associated with a Site
        """

        try:
            record_id = form.vars.id
        except AttributeError:
            # Nothing we can do
            return

        db = current.db
        s3db = current.s3db

        atable = db.pr_address
        row = db(atable.id == record_id).select(atable.location_id,
                                                atable.pe_id,
                                                limitby=(0, 1),
                                                ).first()
        try:
            location_id = row.location_id
        except:
            # Nothing we can do
            return

        pe_id = row.pe_id

        ctable = s3db.dvr_case
        ptable = s3db.pr_person
        query = (ptable.pe_id == pe_id) & \
                (ptable.id == ctable.person_id)
        case = db(query).select(ctable.site_id,
                                limitby=(0, 1),
                                ).first()

        if case and not case.site_id:
            db(ptable.pe_id == pe_id).update(location_id = location_id,
                                             # Indirect update by system rule,
                                             # do not change modified_* fields:
                                             modified_on = ptable.modified_on,
                                             modified_by = ptable.modified_by,
                                             )

    # -------------------------------------------------------------------------
    def customise_pr_address_resource(r, tablename):

        # Custom onaccept to set the Person's Location to this address
        # - unless their case is associated with a Site
        current.s3db.add_custom_callback("pr_address",
                                         "onaccept",
                                         pr_address_onaccept,
                                         )

    settings.customise_pr_address_resource = customise_pr_address_resource

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        table = current.s3db.pr_contact

        #field = table.contact_description
        #field.readable = field.writable = False

        field = table.value
        field.label = T("Number or Address")

        field = table.contact_method
        all_opts = current.msg.CONTACT_OPTS
        subset = ("SMS",
                  "EMAIL",
                  "HOME_PHONE",
                  "WORK_PHONE",
                  "FACEBOOK",
                  "TWITTER",
                  "SKYPE",
                  "WHATSAPP",
                  "OTHER",
                  )
        contact_methods = [(k, all_opts[k]) for k in subset if k in all_opts]
        field.requires = IS_IN_SET(contact_methods, zero=None)
        field.default = "SMS"

    settings.customise_pr_contact_resource = customise_pr_contact_resource

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

        # Configure components to inherit realm_entity
        # from the person record
        s3db.configure("pr_person",
                       realm_components = ("case_activity",
                                           "case_details",
                                           "dvr_flag",
                                           "case_language",
                                           "case_note",
                                           "residence_status",
                                           "address",
                                           "contact",
                                           "contact_emergency",
                                           "group_membership",
                                           "image",
                                           "person_details",
                                           "person_tag",
                                           ),
                       )

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

            crud_strings = s3.crud_strings["pr_person"]

            archived = r.get_vars.get("archived")
            if archived in ("1", "true", "yes"):
                crud_strings["title_list"] = T("Invalid Cases")

            if r.controller == "dvr":

                from gluon import Field

                resource = r.resource
                configure = resource.configure

                # Set contacts-method for tab
                s3db.set_method("pr", "person",
                                method = "contacts",
                                action = s3db.pr_Contacts,
                                )

                # Autocomplete search-method
                search_fields = ("first_name", "last_name")
                s3db.set_method("pr", "person",
                                method = "search_ac",
                                action = s3db.pr_PersonSearchAutocomplete(search_fields),
                                )

                table = r.table
                ctable = s3db.dvr_case

                # Case-sites must be shelters
                field = ctable.site_id
                field.label = T("Shelter")
                field.represent = s3db.org_SiteRepresent(show_type=False)
                requires = field.requires
                if isinstance(requires, IS_EMPTY_OR):
                    requires = requires.other
                if hasattr(requires, "instance_types"):
                    requires.instance_types = ("cr_shelter",)

                if not r.component:

                    # Can the user see cases from more than one org?
                    realms = auth.permission.permitted_realms("dvr_case", "read")
                    if realms is None or len(realms) > 1:
                        multiple_orgs = True
                    else:
                        multiple_orgs = False

                    configure_person_tags()

                    if r.method == "report":

                        # Custom Report Options
                        facts = ((T("Number of Clients"), "count(pe_label)"),
                                 (T("Number of Actions"), "count(case_activity.response_action.id)"),
                                 )
                        axes = ("gender",
                                "person_details.nationality",
                                "person_details.marital_status",
                                "dvr_case.status_id",
                                "dvr_case.site_id",
                                "residence_status.status_type_id",
                                "residence_status.permit_type_id",
                                )

                        report_options = {
                            "rows": axes,
                            "cols": axes,
                            "fact": facts,
                            "defaults": {"rows": axes[0],
                                         "cols": axes[1],
                                         "fact": facts[0],
                                         "totals": True,
                                         },
                            }
                        configure(report_options = report_options)
                        crud_strings["title_report"] = T("Case Statistic")

                    if r.interactive and r.method != "import":

                        from s3 import S3SQLCustomForm, \
                                       S3SQLInlineComponent, \
                                       S3SQLInlineLink, \
                                       S3SQLVerticalSubFormLayout, \
                                       S3TextFilter, \
                                       S3DateFilter, \
                                       S3OptionsFilter, \
                                       s3_get_filter_opts, \
                                       IS_PERSON_GENDER

                        # Default organisation
                        ctable = s3db.dvr_case
                        field = ctable.organisation_id
                        field.comment = None
                        user_org = auth.user.organisation_id if auth.user else None
                        if user_org:
                            field.default = user_org

                        # Organisation is required
                        requires = field.requires
                        if isinstance(requires, IS_EMPTY_OR):
                            field.requires = requires.other

                        # Expose human_resource_id
                        field = ctable.human_resource_id
                        field.comment = None
                        human_resource_id = auth.s3_logged_in_human_resource()
                        if human_resource_id:
                            field.default = human_resource_id
                        field.readable = field.writable = True
                        field.widget = None

                        # Make marital status mandatory, remove "other"
                        dtable = s3db.pr_person_details
                        field = dtable.marital_status
                        options = dict(s3db.pr_marital_status_opts)
                        del options[9] # Remove "other"
                        field.requires = IS_IN_SET(options, zero=None)

                        # Remove Add-links in residence status
                        rtable = s3db.dvr_residence_status
                        field = rtable.status_type_id
                        field.comment = None
                        field = rtable.permit_type_id
                        field.comment = None

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
                            "dvr_case.date",
                            "dvr_case.organisation_id",
                            "dvr_case.human_resource_id",
                            (T("Case Status"), "dvr_case.status_id"),
                            S3SQLInlineLink("case_flag",
                                           label = T("Flags"),
                                           field = "flag_id",
                                           help_field = "comments",
                                           cols = 4,
                                           ),

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
                            (T("Moving-in Date"), "dvr_case_details.on_site_from"),
                            (T("Moving-out Date"), "dvr_case_details.on_site_until"),
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
                            (T("Date of Entry"), "dvr_case_details.arrival_date"),
                            S3SQLInlineComponent(
                                    "residence_status",
                                    fields = ["status_type_id",
                                              "permit_type_id",
                                              #"reference",
                                              #"valid_from",
                                              "valid_until",
                                              "comments",
                                              ],
                                    label = T("Residence Status"),
                                    multiple = False,
                                    layout = S3SQLVerticalSubFormLayout,
                                    ),

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
                            S3OptionsFilter("case_flag_case.flag_id",
                                            label = T("Flags"),
                                            options = s3_get_filter_opts("dvr_case_flag",
                                                                         translate = True,
                                                                         ),
                                            cols = 3,
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

            elif r.controller == "default":

                # Personal Profile

                if r.component_name == "group_membership":

                    # Team memberships are read-only
                    r.component.configure(insertable = False,
                                          editable = False,
                                          deletable = False,
                                          )

                elif r.component_name == "human_resource":

                    # Staff/Volunteer records are read-only
                    r.component.configure(insertable = False,
                                          editable = False,
                                          deletable = False,
                                          )

            return result
        s3.prep = custom_prep

        # Custom rheader tabs
        if current.request.controller == "dvr":
            attr = dict(attr)
            attr["rheader"] = drk_dvr_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def customise_pr_group_controller(**attr):

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

            if r.controller in ("hrm", "vol"):

                if not r.component:

                    # No inline-adding new organisations
                    ottable = s3db.org_organisation_team
                    field = ottable.organisation_id
                    field.comment = None

                    # Organisation is required
                    from s3 import S3SQLCustomForm, \
                                   S3SQLInlineComponent
                    crud_form = S3SQLCustomForm(
                                    "name",
                                    "description",
                                    S3SQLInlineComponent("organisation_team",
                                                         label = T("Organization"),
                                                         fields = ["organisation_id"],
                                                         multiple = False,
                                                         required = True,
                                                         ),
                                    "comments",
                                    )
                    r.resource.configure(crud_form = crud_form)

                elif r.component_name == "group_membership":

                    from s3 import S3PersonAutocompleteWidget

                    # Make sure only HRs can be added to teams
                    mtable = s3db.pr_group_membership
                    field = mtable.person_id
                    field.widget = S3PersonAutocompleteWidget(
                                        #controller="hrm",
                                        ajax_filter="human_resource.id__ne=None",
                                        )
            return result
        s3.prep = custom_prep

        return attr

    settings.customise_pr_group_controller = customise_pr_group_controller

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

                # Set contacts-method to retain the tab
                s3db.set_method("pr", "person",
                                method = "contacts",
                                action = s3db.pr_Contacts,
                                )

                if r.interactive:
                    table = resource.table

                    #from s3 import IS_ADD_PERSON_WIDGET2, S3AddPersonWidget2
                    from s3 import S3AddPersonWidget

                    field = table.person_id
                    field.represent = s3db.pr_PersonRepresent(show_link=True)
                    #field.requires = IS_ADD_PERSON_WIDGET2()
                    #field.widget = S3AddPersonWidget2(controller="dvr")
                    field.requires = IS_ONE_OF(current.db, "pr_person.id")
                    s3db.pr_person.pe_label.label = T("ID")
                    field.widget = S3AddPersonWidget(controller = "dvr",
                                                     pe_label = True,
                                                     )

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
    def dvr_case_onaccept(form):
        """
            Additional custom-onaccept for dvr_case to:
            * Force-update the realm entity of the person record:
            - the organisation managing the case is the realm-owner,
              but the person record is written first, so we need to
              update it after writing the case
            - the case can be transferred to another organisation/branch,
              and then the person record needs to be transferred to that
              same realm as well
            * Update the Population of all Shelters
            * Update the Location of the person record:
            - if the Case is linked to a Site then use that for the Location of
              the Person
            - otherwise use the Private Address
        """

        try:
            form_vars = form.vars
        except AttributeError:
            return

        record_id = form_vars.id
        if not record_id:
            # Nothing we can do
            return

        db = current.db
        s3db = current.s3db

        # Update the Population of all Shelters
        cr_shelter_population()

        # Get the Person ID & Site ID for this case
        person_id = form_vars.person_id
        if not person_id or "site_id" not in form_vars:
            # Reload the record
            table = s3db.dvr_case
            query = (table.id == record_id)
            row = db(query).select(table.person_id,
                                   table.site_id,
                                   limitby = (0, 1),
                                   ).first()

            if row:
                person_id = row.person_id
                site_id = row.site_id
        else:
            site_id = form_vars.site_id

        if person_id:

            set_realm_entity = current.auth.set_realm_entity

            # Configure components to inherit realm_entity
            # from the person record
            s3db.configure("pr_person",
                           realm_components = ("case_activity",
                                               "case_details",
                                               "dvr_flag",
                                               "case_language",
                                               "case_note",
                                               "residence_status",
                                               "address",
                                               "contact",
                                               "contact_emergency",
                                               "group_membership",
                                               "image",
                                               "person_details",
                                               "person_tag",
                                               ),
                           )

            # Force-update the realm entity for the person
            set_realm_entity("pr_person", person_id, force_update=True)

            # Configure components to inherit realm entity
            # from the case activity record
            s3db.configure("dvr_case_activity",
                           realm_components = ("case_activity_need",
                                               "case_activity_update",
                                               "response_action",
                                               ),
                           )

            # Force-update the realm entity for all case activities
            # linked to the person_id
            atable = s3db.dvr_case_activity
            query = (atable.person_id == person_id)
            set_realm_entity(atable, query, force_update=True)

            # Update the person's location_id
            ptable = s3db.pr_person
            location_id = None

            if site_id:
                # Use the Shelter's Address
                stable = s3db.org_site
                site = db(stable.site_id == site_id).select(stable.location_id,
                                                            limitby = (0, 1),
                                                            ).first()
                if site:
                    location_id = site.location_id
            else:
                # Use the Private Address (no need to filter by address type as only
                # 'Current Address' is exposed)
                # NB If this is a New/Modified Address then this won't be caught here
                # - we use pr_address_onaccept to catch those
                atable = s3db.pr_address
                query = (ptable.id == person_id) & \
                        (ptable.pe_id == atable.pe_id) & \
                        (atable.deleted == False)
                address = db(query).select(atable.location_id,
                                           limitby = (0, 1),
                                           ).first()
                if address:
                    location_id = address.location_id

            db(ptable.id == person_id).update(location_id = location_id,
                                              # Indirect update by system rule,
                                              # do not change modified_* fields:
                                              modified_on = ptable.modified_on,
                                              modified_by = ptable.modified_by,
                                              )

    # -------------------------------------------------------------------------
    def customise_dvr_case_resource(r, tablename):

        s3db = current.s3db
        ctable = s3db.dvr_case

        get_vars = r.get_vars
        if r.function == "group_membership" and "viewing" in get_vars:

            # Creating a case file for a new family member
            # => default to same organisation as primary case
            try:
                vtablename, record_id = get_vars["viewing"].split(".")
            except ValueError:
                vtablename, record_id = None, None

            if vtablename == "pr_person":
                query = (ctable.person_id == record_id)
                row = current.db(query).select(ctable.organisation_id,
                                               limitby = (0, 1),
                                               ).first()
                if row:
                    ctable.organisation_id.default = row.organisation_id

        # Custom onaccept to update realm-entity of the
        # beneficiary and case activities of this case
        # (incl. their respective realm components)
        s3db.add_custom_callback("dvr_case",
                                 "onaccept",
                                 dvr_case_onaccept,
                                 )

        # Update the realm-entity when the case gets updated
        # (because the assigned organisation/branch can change)
        s3db.configure("dvr_case", update_realm = True)

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

        db = current.db
        auth = current.auth
        s3db = current.s3db

        human_resource_id = auth.s3_logged_in_human_resource()

        if r.method == "report":

            # Custom Report Options
            facts = ((T("Number of Activities"), "count(id)"),
                     (T("Number of Clients"), "count(person_id$pe_label)"),
                     )
            axes = ("person_id$gender",
                    "person_id$person_details.nationality",
                    "person_id$person_details.marital_status",
                    "status_id",
                    "priority",
                    "sector_id",
                    "case_activity_need.need_id",
                    "response_action.response_type_id",
                    )
            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": facts,
                "defaults": {"rows": "sector_id",
                             "cols": "person_id$person_details.nationality",
                             "fact": "count(id)",
                             "totals": True,
                             },
                }
            s3db.configure("dvr_case_activity",
                           report_options = report_options,
                           )
            crud_strings = current.response.s3.crud_strings["dvr_case_activity"]
            crud_strings["title_report"] = T("Activity Statistic")

        if r.interactive or r.representation == "aadata":

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
            #fmt = "%(pe_label)s %(last_name)s, %(first_name)s"
            field.represent = s3db.pr_PersonRepresent(#fields = ("pe_label",
                                                      #          "last_name",
                                                      #          "first_name",
                                                      #          ),
                                                      #labels = fmt,
                                                      show_link = True,
                                                      )

            # Customise sector
            field = table.sector_id
            field.comment = None

            # Show subject field
            field = table.subject
            field.readable = field.writable = True
            field.requires = IS_NOT_EMPTY()

            # Customise Priority
            field = table.priority
            priority_opts = [(0, T("Emergency")),
                             (1, T("High")),
                             (2, T("Normal")),
                             (3, T("Low")),
                             ]
            field.readable = field.writable = True
            field.label = T("Priority")
            field.default = 2
            field.requires = IS_IN_SET(priority_opts, sort=False, zero=None)
            field.represent = PriorityRepresent(priority_opts,
                                                {0: "red",
                                                 1: "blue",
                                                 2: "lightblue",
                                                 3: "grey",
                                                 }).represent

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

            # Show human_resource_id
            field = table.human_resource_id
            field.readable = field.writable = True
            field.label = T("Consultant in charge")
            field.default = human_resource_id
            field.widget = None
            field.comment = None

            # Inline-needs
            ntable = current.s3db.dvr_case_activity_need

            field = ntable.human_resource_id
            field.default = human_resource_id
            field.widget = field.comment = None

            field = ntable.need_id
            field.comment = None

            # Inline-responses
            rtable = s3db.dvr_response_action

            field = rtable.human_resource_id
            field.label = T("Assigned to")
            field.default = human_resource_id
            field.widget = field.comment = None

            # Inline-updates
            utable = current.s3db.dvr_case_activity_update

            field = utable.human_resource_id
            field.default = human_resource_id
            field.widget = field.comment = None

            from s3 import S3SQLVerticalSubFormLayout
            crud_form = S3SQLCustomForm(
                            "person_id",

                            "sector_id",

                            "subject",
                            (T("Initial Situation Details"), ("need_details")),

                            "start_date",
                            "priority",
                            "human_resource_id",

                            S3SQLInlineComponent("case_activity_need",
                                                 label = T("Needs Assessment"),
                                                 fields = [
                                                     "date",
                                                     "need_id",
                                                     (T("Details"), "comments"),
                                                     "human_resource_id",
                                                     ],
                                                 layout = S3SQLVerticalSubFormLayout,
                                                 explicit_add = T("Add Need"),
                                                 ),

                            S3SQLInlineComponent("response_action",
                                                 label = T("Actions"),
                                                 fields = [
                                                     "response_type_id",
                                                     "date_due",
                                                     "comments",
                                                     "human_resource_id",
                                                     "status_id",
                                                     "date",
                                                     "hours",
                                                     ],
                                                 layout = S3SQLVerticalSubFormLayout,
                                                 explicit_add = T("Add Action"),
                                                 ),

                            "followup",
                            "followup_date",

                            S3SQLInlineComponent("case_activity_update",
                                                 label = T("Progress"),
                                                 fields = [
                                                     "date",
                                                     (T("Occasion"), "update_type_id"),
                                                     "human_resource_id",
                                                     "comments",
                                                     ],
                                                 layout = S3SQLVerticalSubFormLayout,
                                                 explicit_add = T("Add Entry"),
                                                 ),

                            "status_id",
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

            s3db.configure("dvr_case_activity",
                           crud_form = crud_form,
                           #filter_widgets = filter_widgets,
                           orderby = "dvr_case_activity.priority",
                           )

        # Custom list fields for case activity component tab
        if r.tablename != "dvr_case_activity":
            list_fields = ["priority",
                           "sector_id",
                           "subject",
                           #"followup",
                           #"followup_date",
                           "start_date",
                           "human_resource_id",
                           "status_id",
                           ]

            # Custom list fields
            s3db.configure("dvr_case_activity",
                           list_fields = list_fields,
                           )

        # Configure components to inherit realm entity
        # from the case activity record
        s3db.configure("dvr_case_activity",
                       realm_components = ("case_activity_need",
                                           "case_activity_update",
                                           "response_action",
                                           ),
                       )

    settings.customise_dvr_case_activity_resource = customise_dvr_case_activity_resource

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_controller(**attr):

        auth = current.auth
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

            # Configure person tags
            configure_person_tags()

            # Adapt list title when filtering for priority 0 (Emergency)
            if r.get_vars.get("~.priority") == "0":
                emergencies = True
                s3.crud_strings["dvr_case_activity"]["title_list"] = T("Emergencies")
            else:
                emergencies = False

            # Filter to active cases
            if not r.record:
                query = (FS("person_id$dvr_case.archived") == False) | \
                        (FS("person_id$dvr_case.archived") == None)
                resource.add_filter(query)

            if not r.component and not r.record:

                from s3 import S3TextFilter, \
                               S3OptionsFilter, \
                               S3DateFilter, \
                               s3_get_filter_opts

                db = current.db

                # Status filter options + defaults
                stable = s3db.dvr_case_activity_status
                query = (stable.deleted == False)
                rows = db(query).select(stable.id,
                                        stable.name,
                                        stable.is_closed,
                                        cache = s3db.cache,
                                        orderby = stable.workflow_position,
                                        )
                status_filter_options = OrderedDict((row.id, T(row.name))
                                                    for row in rows)
                status_filter_defaults = [row.id for row in rows
                                                 if not row.is_closed]

                # Filter widgets
                filter_widgets = [
                    S3TextFilter(["person_id$pe_label",
                                  "person_id$first_name",
                                  "person_id$last_name",
                                  "need_details",
                                  ],
                                  label = T("Search"),
                                  ),
                    S3OptionsFilter("status_id",
                                    options = status_filter_options,
                                    cols = 3,
                                    default = status_filter_defaults,
                                    sort = False,
                                    ),
                    S3OptionsFilter("sector_id",
                                    hidden = True,
                                    options = lambda: s3_get_filter_opts("org_sector",
                                                                         translate = True,
                                                                         ),
                                    ),
                    S3OptionsFilter("case_activity_need.need_id",
                                    options = lambda: s3_get_filter_opts("dvr_need",
                                                                         translate = True,
                                                                         ),
                                    hidden = True,
                                    ),
                    S3OptionsFilter("person_id$person_details.nationality",
                                    label = T("Client Nationality"),
                                    hidden = True,
                                    ),
                    ]

                # Priority filter (unless pre-filtered to emergencies anyway)
                if not emergencies:
                    field = resource.table.priority
                    priority_opts = OrderedDict(field.requires.options())
                    priority_filter = S3OptionsFilter("priority",
                                                      options = priority_opts,
                                                      cols = 4,
                                                      sort = False,
                                                      )
                    filter_widgets.insert(2, priority_filter)

                # Can the user see cases from more than one org?
                realms = auth.permission.permitted_realms("dvr_case", "read")
                if realms is None:
                    multiple_orgs = True
                elif len(realms) > 1:
                    otable = s3db.org_organisation
                    query = (otable.pe_id.belongs(realms)) & \
                            (otable.deleted == False)
                    rows = db(query).select(otable.id)
                    multiple_orgs = len(rows) > 1
                else:
                    multiple_orgs = False
                if multiple_orgs:
                    # Add org-filter widget
                    filter_widgets.insert(1,
                                          S3OptionsFilter("person_id$dvr_case.organisation_id"),
                                          )

                # Custom list fields
                list_fields = ["priority",
                               (T("ID"), "person_id$pe_label"),
                               (T("Case"), "person_id"),
                               "sector_id",
                               "subject",
                               "start_date",
                               #"followup",
                               #"followup_date",
                               "status_id",
                               ]

                # Reconfigure table
                resource.configure(filter_widgets = filter_widgets,
                                   list_fields = list_fields,
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
    def customise_dvr_case_flag_resource(r, tablename):

        table = current.s3db.dvr_case_flag

        # Hide unwanted fields
        unused = ("advise_at_check_in",
                  "advise_at_check_out",
                  "advise_at_id_check",
                  "instructions",
                  "deny_check_in",
                  "deny_check_out",
                  "allowance_suspended",
                  "is_not_transferable",
                  "is_external",
                  )

        for fieldname in unused:
            field = table[fieldname]
            field.readable = field.writable = False

    settings.customise_dvr_case_flag_resource = customise_dvr_case_flag_resource

    # -------------------------------------------------------------------------
    def customise_dvr_response_action_resource(r, tablename):

        s3db = current.s3db

        table = s3db.dvr_response_action

        # Custom format for case activity representation
        field = table.case_activity_id
        fmt = "%(pe_label)s %(last_name)s, %(first_name)s"
        field.represent = s3db.dvr_CaseActivityRepresent(fmt = fmt,
                                                         show_link = True,
                                                         )

        is_report = r.method == "report"

        if is_report:

            # Custom Report Options
            facts = ((T("Number of Clients"), "count(case_activity_id$person_id$pe_label)"),
                     (T("Hours (Average)"), "avg(hours)"),
                     (T("Hours (Total)"), "sum(hours)"),
                     (T("Number of Actions"), "count(id)"),
                     )
            axes = ("case_activity_id$person_id$gender",
                    "case_activity_id$person_id$person_details.nationality",
                    "case_activity_id$person_id$person_details.marital_status",
                    "case_activity_id$sector_id",
                    "case_activity_id$case_activity_need.need_id",
                    "response_type_id",
                    )
            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": facts,
                "defaults": {"rows": "response_type_id",
                             "cols": "case_activity_id$case_activity_need.need_id",
                             "fact": "count(id)",
                             "totals": True,
                             },
                }
            s3db.configure("dvr_response_action",
                           report_options = report_options,
                           )
            crud_strings = current.response.s3.crud_strings["dvr_response_action"]
            crud_strings["title_report"] = T("Action Statistic")

        if r.interactive or r.representation == "aadata":

            # Custom Filter Options
            from s3 import S3AgeFilter, \
                           S3DateFilter, \
                           S3HierarchyFilter, \
                           S3OptionsFilter, \
                           S3TextFilter, \
                           s3_get_filter_opts

            filter_widgets = [S3TextFilter(
                                ["case_activity_id$person_id$pe_label",
                                 "case_activity_id$person_id$first_name",
                                 "case_activity_id$person_id$middle_name",
                                 "case_activity_id$person_id$last_name",
                                 "comments",
                                 ],
                                label = T("Search"),
                                ),
                              S3OptionsFilter(
                                "status_id",
                                options = lambda: \
                                          s3_get_filter_opts("dvr_response_status"),
                                          cols = 3,
                                          translate = True,
                                          ),
                              S3DateFilter("date", hidden=not is_report),
                              S3DateFilter("date_due", hidden=is_report),
                              S3HierarchyFilter("response_type_id",
                                                lookup = "dvr_response_type",
                                                hidden = True,
                                                ),
                              S3OptionsFilter("case_activity_id$person_id$person_details.nationality",
                                              label = T("Client Nationality"),
                                              hidden = True,
                                              ),
                              S3AgeFilter("case_activity_id$person_id$date_of_birth",
                                          label = T("Client Age"),
                                          hidden = True,
                                          )
                              #S3DateFilter("case_activity_id$person_id$date_of_birth",
                              #             label = T("Client Date of Birth"),
                              #             hidden = True,
                              #             ),
                              ]
            s3db.configure("dvr_response_action",
                           filter_widgets = filter_widgets,
                           )

    settings.customise_dvr_response_action_resource = customise_dvr_response_action_resource

    # -------------------------------------------------------------------------
    def customise_dvr_service_contact_resource(r, tablename):

        s3db = current.s3db

        table = s3db.dvr_service_contact

        field = table.type_id
        field.label = T("Type")

        field = table.organisation_id
        field.readable = field.writable = False

        field = table.organisation
        field.readable = field.writable = True

    settings.customise_dvr_service_contact_resource = customise_dvr_service_contact_resource

    # -------------------------------------------------------------------------
    # Shelter Registry Settings
    #
    settings.cr.people_registration = False

    # -------------------------------------------------------------------------
    def cr_shelter_onaccept(form):
        """
            Custom onaccept for shelters:
            * Update the Location for all linked Cases
              (in case the Address has been updated)
        """

        db = current.db
        s3db = current.s3db

        try:
            record_id = form.vars.id
        except AttributeError:
            return

        if not record_id:
            # Nothing we can do
            return

        # Reload the record (need site_id which is never in form.vars)
        table = s3db.cr_shelter
        shelter = db(table.id == record_id).select(table.location_id,
                                                   table.site_id,
                                                   limitby = (0, 1),
                                                   ).first()

        # If shelter were None here, then this shouldn't have been called
        # in the first place => let it raise AttributeError
        location_id = shelter.location_id
        site_id = shelter.site_id

        ctable = s3db.dvr_case
        cases = db(ctable.site_id == site_id).select(ctable.person_id)
        if cases:
            person_ids = set(case.person_id for case in cases)
            ptable = s3db.pr_person
            db(ptable.id.belongs(person_ids)).update(
                                            location_id = location_id,
                                            # Indirect update by system rule,
                                            # do not change modified_* fields:
                                            modified_on = ptable.modified_on,
                                            modified_by = ptable.modified_by,
                                            )

    # -------------------------------------------------------------------------
    def cr_shelter_population():
        """
            Update the Population of all Shelters
            * called onaccept from dvr_case
        """

        db = current.db
        s3db = current.s3db

        # Get the number of open cases per site_id
        ctable = s3db.dvr_case
        dtable = s3db.dvr_case_details
        stable = s3db.dvr_case_status
        join = stable.on(stable.id == ctable.status_id)
        left = dtable.on((dtable.person_id == ctable.person_id) & \
                         ((dtable.case_id == None) |
                          (dtable.case_id == ctable.id)) & \
                         (dtable.deleted == False))
        today = current.request.utcnow.date()
        query = (ctable.site_id != None) & \
                (ctable.deleted == False) & \
                (stable.is_closed == False) & \
                ((dtable.on_site_from == None) | (dtable.on_site_from <= today)) & \
                ((dtable.on_site_until == None) | (dtable.on_site_until >= today))

        site_id = ctable.site_id
        count = ctable.id.count()
        rows = db(query).select(site_id,
                                count,
                                groupby = site_id,
                                join = join,
                                left = left,
                                )

        # Update shelter population count
        stable = s3db.cr_shelter
        for row in rows:
            db(stable.site_id == row[site_id]).update(
                population = row[count],
                # Indirect update by system rule,
                # do not change modified_* fields:
                modified_on = stable.modified_on,
                modified_by = stable.modified_by,
                )

    # -------------------------------------------------------------------------
    def customise_cr_shelter_resource(r, tablename):

        auth = current.auth
        s3db = current.s3db

        s3 = current.response.s3

        # Disable name-validation of cr_shelter_type
        import_prep = s3.import_prep
        def custom_import_prep(data):

            # Call standard import_prep
            if import_prep:
                from gluon.tools import callback
                callback(import_prep, data, tablename="cr_shelter")

            # Disable uniqueness validation for shelter type names,
            # otherwise imports will fail before reaching de-duplicate
            ttable = s3db.cr_shelter_type
            field = ttable.name
            field.requires = IS_NOT_EMPTY()

            # Reset to standard (no need to repeat it)
            s3.import_prep = import_prep

        s3.import_prep = custom_import_prep

        from s3 import S3LocationSelector, \
                       S3SQLCustomForm

        # Field configurations
        table = s3db.cr_shelter

        field = table.organisation_id
        user_org = auth.user.organisation_id if auth.user else None
        if user_org:
            field.default = user_org

        field = table.shelter_type_id
        field.comment = None

        # Hide L2 Government District
        field = table.location_id
        field.widget = S3LocationSelector(levels = gis_levels,
                                          show_address = True,
                                          )

        # Custom form
        crud_form = S3SQLCustomForm("name",
                                    "organisation_id",
                                    "shelter_type_id",
                                    "location_id",
                                    "phone",
                                    "status",
                                    "comments",
                                    )


        # Custom list fields
        list_fields = [(T("Name"), "name"),
                       (T("Type"), "shelter_type_id"),
                       "organisation_id",
                       (T("Number of Cases"), "population"),
                       "status",
                       ]

        # Which levels of Hierarchy are we using?
        #levels = current.gis.get_relevant_hierarchy_levels()
        lfields = ["location_id$%s" % level for level in gis_levels]
        list_fields[-1:-1] = lfields

        s3db.configure("cr_shelter",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

        # Add custom onaccept
        s3db.add_custom_callback(tablename,
                                 "onaccept",
                                 cr_shelter_onaccept,
                                 )

    settings.customise_cr_shelter_resource = customise_cr_shelter_resource

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

            if r.interactive:

                resource = r.resource

                # Customise filter widgets
                filter_widgets = resource.get_config("filter_widgets")
                if filter_widgets:

                    from s3 import S3TextFilter

                    custom_filters = []
                    for fw in filter_widgets:
                        if fw.field == "capacity_day":
                            continue
                        elif fw.field == "location_id":
                            fw.opts["levels"] = gis_levels
                        if not isinstance(fw, S3TextFilter) and \
                           fw.field != "shelter_type_id":
                            fw.opts["hidden"] = True
                        custom_filters.append(fw)

                    resource.configure(filter_widgets = custom_filters)

            return result

        s3.prep = custom_prep

        # Custom rheader
        attr = dict(attr)
        attr["rheader"] = drk_cr_rheader

        return attr

    settings.customise_cr_shelter_controller = customise_cr_shelter_controller

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Disable creation of new root orgs unless user is ORG_GROUP_ADMIN
            if r.method != "hierarchy" and \
               (r.representation != "popup" or not r.get_vars.get("hierarchy")):
                auth = current.auth
                sysroles = sysroles = auth.get_system_roles()
                insertable = auth.s3_has_roles((sysroles.ADMIN,
                                                sysroles.ORG_GROUP_ADMIN,
                                                ))
                r.resource.configure(insertable = insertable)

            return result

        s3.prep = custom_prep

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def org_site_check(site_id):
        """ Custom tasks for scheduled site checks """

        # Tasks which are not site-specific
        if site_id == "all":

            # Update all shelter populations
            # NB will be db.committed by org_site_check in models/tasks.py
            current.log.info("Updating all shelter populations")
            cr_shelter_population()

    settings.org.site_check = org_site_check

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
    def customise_org_sector_resource(r, tablename):

        table = current.s3db.org_sector

        field = table.location_id
        field.readable = field.writable = False

    settings.customise_org_sector_resource = customise_org_sector_resource

    # -------------------------------------------------------------------------
    # Project Module Settings
    #
    settings.project.mode_task = True
    settings.project.projects = False
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
    #def customise_project_home():
    #    """ Always go to task list """
    #
    #    from s3 import s3_redirect_default
    #    s3_redirect_default(URL(f="task"))
    #
    #settings.customise_project_home = customise_project_home

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
                                    #"source",
                                    "pe_id",
                                    "date_due",
                                    )
        s3db.configure("project_task",
                       crud_form = crud_form,
                       update_realm = True,
                       )

        accessible_query = current.auth.s3_accessible_query

        # Filter assignees to human resources
        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person
        query = accessible_query("read", htable) & \
                (htable.person_id == ptable.id)
        rows = db(query).select(ptable.pe_id)
        pe_ids = set(row.pe_id for row in rows)

        # ...and teams
        gtable = s3db.pr_group
        query = accessible_query("read", gtable) & \
                (gtable.group_type == 3)
        rows = db(query).select(gtable.pe_id)
        pe_ids |= set(row.pe_id for row in rows)

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
        #("supply", Storage(
        #   name_nice = T("Supply Chain Management"),
        #   #description = "Used within Inventory Management, Request Management and Asset Management",
        #   restricted = True,
        #   module_type = None, # Not displayed
        #)),
        #("inv", Storage(
        #   name_nice = T("Warehouses"),
        #   #description = "Receiving and Sending Items",
        #   restricted = True,
        #   module_type = 4
        #)),
        #("asset", Storage(
        #   name_nice = T("Assets"),
        #   #description = "Recording and Assigning Assets",
        #   restricted = True,
        #   module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("req", Storage(
        #   name_nice = T("Requests"),
        #   #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #   restricted = True,
        #   module_type = 10,
        #)),
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
        #("event", Storage(
        #   name_nice = T("Events"),
        #   #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("security", Storage(
        #   name_nice = T("Security"),
        #   restricted = True,
        #   module_type = 10,
        #)),
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
def drk_cr_rheader(r, tabs=[]):
    """ CR custom resource headers """

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

        if tablename == "cr_shelter":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

            rheader_fields = [["name",
                               ],
                              ["organisation_id",
                               ],
                              ["location_id",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

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
                            (T("Contact Info"), "contacts"),
                            (T("Family Members"), "group_membership/"),
                            (T("Activities"), "case_activity"),
                            (T("Appointments"), "case_appointment"),
                            (T("Service Contacts"), "service_contact"),
                            (T("Photos"), "image"),
                            (T("Documents"), "document/"),
                            (T("Notes"), "case_note"),
                            ]

                case = resource.select(["first_name",
                                        "last_name",
                                        "dvr_case.status_id",
                                        "dvr_case.archived",
                                        "dvr_case.household_size",
                                        "dvr_case.organisation_id",
                                        "dvr_case.site_id",
                                        "dvr_case_flag_case.flag_id",
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
                    flags = lambda row: case["dvr_case_flag_case.flag_id"]
                else:
                    # Target record exists, but doesn't match filters
                    return None

                rheader_fields = [[(T("ID"), "pe_label"),
                                   (T("Case Status"), case_status),
                                   (T("Organisation"), organisation),
                                   ],
                                  [(T("Name"), name),
                                   (T("Size of Family"), household_size),
                                   (T("Shelter"), facility),
                                   ],
                                  ["date_of_birth",
                                   ],
                                  [(T("Flags"), flags),
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

# =============================================================================
class PriorityRepresent(object):
    """
        Color-coded representation of priorities

        @todo: generalize/move to s3utils?
    """

    def __init__(self, options, classes=None):
        """
            Constructor

            @param options: the options (as dict or anything that can be
                            converted into a dict)
            @param classes: a dict mapping keys to CSS class suffixes
        """

        self.options = dict(options)
        self.classes = classes

    def represent(self, value, row=None):
        """
            Representation function

            @param value: the value to represent
        """

        css_class = base_class = "prio"

        classes = self.classes
        if classes:
            suffix = classes.get(value)
            if suffix:
                css_class = "%s %s-%s" % (css_class, base_class, suffix)

        label = self.options.get(value)

        return DIV(label, _class=css_class)

# END =========================================================================
