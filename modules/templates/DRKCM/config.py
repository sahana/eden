# -*- coding: utf-8 -*-

import datetime

from collections import OrderedDict

from gluon import current, A, DIV, IS_EMPTY_OR, IS_IN_SET, IS_LENGTH, IS_NOT_EMPTY, SPAN, TAG, URL
from gluon.storage import Storage

from s3 import FS, IS_ONE_OF
from s3compat import long
from s3dal import original_tablename

# =============================================================================
# UI options per organisation
#
UI_DEFAULTS = {#"case_arrival_date_label": "Date of Entry",
               "case_collaboration": False,
               "case_document_templates": False,
               "case_header_protection_themes": False,
               "case_hide_default_org": False,
               "case_use_response_tab": True,
               "case_use_photos_tab": False,
               "case_use_bamf": False,
               "case_use_address": True,
               "case_use_appointments": False,
               "case_use_education": False,
               "case_use_flags": False,
               "case_use_notes": False,
               "case_use_occupation": True,
               "case_use_pe_label": False,
               "case_use_place_of_birth": False,
               "case_use_residence_status": True,
               "case_use_referral": True,
               "case_use_service_contacts": False,
               "case_lodging": None, # "site"|"text"|None
               "case_lodging_dates": False,
               "case_nationality_mandatory": False,
               "case_show_total_consultations": True,
               "activity_closure": True,
               "activity_comments": True,
               "activity_use_sector": True,
               "activity_need_details": True,
               "activity_follow_up": False,
               "activity_priority": False,
               "activity_pss_vulnerability": True,
               "activity_use_need": False,
               #"activity_tab_label": "Counseling Reasons",
               "appointments_staff_link": False,
               "appointments_use_organizer": False,
               "response_activity_autolink": False,
               "response_due_date": False,
               "response_effort_required": True,
               "response_planning": False,
               "response_tab_need_filter": False,
               "response_themes_details": False,
               "response_themes_sectors": False,
               "response_themes_needs": False,
               "response_themes_optional": False,
               "response_types": True,
               "response_use_organizer": False,
               "response_use_time": False,
               "response_performance_indicators": None, # default
               }

UI_OPTIONS = {"LEA": {"case_arrival_date_label": "Date of AKN",
                      "case_collaboration": True,
                      "case_document_templates": True,
                      "case_header_protection_themes": True,
                      "case_hide_default_org": True,
                      "case_use_response_tab": True,
                      "case_use_photos_tab": True,
                      "case_use_bamf": True,
                      "case_use_address": False,
                      "case_use_appointments": False,
                      "case_use_education": True,
                      "case_use_flags": False,
                      "case_use_notes": False,
                      "case_use_occupation": False,
                      "case_use_pe_label": True,
                      "case_use_place_of_birth": True,
                      "case_use_residence_status": False,
                      "case_use_referral": False,
                      "case_use_service_contacts": False,
                      "case_lodging": "text",
                      "case_lodging_dates": False,
                      "case_nationality_mandatory": True,
                      "case_show_total_consultations": False,
                      "activity_closure": False,
                      "activity_comments": False,
                      "activity_use_sector": False,
                      "activity_need_details": False,
                      "activity_follow_up": False,
                      "activity_priority": True,
                      "activity_pss_vulnerability": False,
                      "activity_use_need": True,
                      #"activity_tab_label": "Counseling Reasons",
                      "appointments_staff_link": True,
                      "appointments_use_organizer": True,
                      "response_activity_autolink": True,
                      "response_due_date": False,
                      "response_effort_required": True,
                      "response_planning": False,
                      "response_tab_need_filter": True,
                      "response_themes_details": True,
                      "response_themes_sectors": True,
                      "response_themes_needs": True,
                      "response_themes_optional": True,
                      "response_types": False,
                      "response_use_organizer": True,
                      "response_use_time": True,
                      "response_performance_indicators": "lea",
                      },
              }

UI_TYPES = {"LEA Ellwangen": "LEA",
            "Ankunftszentrum Heidelberg": "LEA",
            }

def get_ui_options():
    """ Get the UI options for the current user's root organisation """

    ui_options = dict(UI_DEFAULTS)
    ui_type = UI_TYPES.get(current.auth.root_org_name())
    if ui_type:
        ui_options.update(UI_OPTIONS[ui_type])
    return ui_options

def get_ui_option(key):
    """ Getter for UI options, for lazy deployment settings """

    def getter(default=None):
        return get_ui_options().get(key, default)
    return getter

# =============================================================================
def config(settings):
    """
        DRKCM Template: Case Management, German Red Cross
    """

    T = current.T

    settings.base.system_name = "RefuScope"
    settings.base.system_name_short = "RefuScope"

    # PrePopulate data
    settings.base.prepopulate += ("DRKCM",)
    settings.base.prepopulate_demo += ("DRKCM/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "DRK"

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    # Disable welcome-emails to newly registered users
    settings.auth.registration_welcome_email = False

    # Request Organisation during user registration
    settings.auth.registration_requests_organisation = True
    # Suppress popup-link for creating organisations during user registration
    settings.auth.registration_organisation_link_create = False

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               #"volunteer": T("Volunteer"),
                                               }
    # Don't show alternatives, just default
    settings.auth.registration_link_user_to_default = ["staff"]

    # Assign all new users the STAFF role for their default realm
    settings.auth.registration_roles = {None: ("STAFF",)}

    # Disable password-retrieval feature
    settings.auth.password_retrieval = False

    # Define which entity types to use as realm entities in role manager
    settings.auth.realm_entity_types = ("org_organisation",)

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
    settings.security.policy = 7 # Hierarchical Realms

    # Version details on About-page require login
    settings.security.version_info_requires_login = True

    # -------------------------------------------------------------------------
    # General UI settings
    #
    settings.ui.calendar_clear_icon = True

    #settings.ui.auto_open_update = True
    #settings.ui.inline_cancel_edit = "submit"

    #settings.ui.organizer_snap_duration = "00:10:00"

    # -------------------------------------------------------------------------
    # Document settings
    #
    settings.doc.mailmerge_fields = {"ID": "pe_label",
                                     "Vorname": "first_name",
                                     "Name": "last_name",
                                     "Geburtsdatum": "date_of_birth",
                                     "Geburtsort": "pr_person_details.place_of_birth",
                                     "Land": "pr_person_details.nationality",
                                     "Registrierungsdatum": "case_details.arrival_date",
                                     "AKN-Datum": "case_details.arrival_date",
                                     "Falldatum": "dvr_case.date",
                                     "BAMF-Az": "bamf.value",
                                     "Benutzername": "current_user.name",
                                     }

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
                           "dvr_response_action",
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
    settings.org.sector = True
    # But hide it from the rheader
    settings.org.sector_rheader = False
    settings.org.branches = True
    settings.org.offices_tab = False
    settings.org.country = False

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

    # Enable household size in cases, "auto" for automatic counting
    settings.dvr.household_size = "auto"

    # Group/Case activities per sector
    settings.dvr.activity_sectors = True
    # Case activities use status field
    settings.dvr.case_activity_use_status = True
    # Case activities cover multiple needs
    settings.dvr.case_activity_needs_multiple = True
    # Case activities use follow-up fields
    settings.dvr.case_activity_follow_up = get_ui_option("activity_follow_up")
    # Beneficiary documents-tab includes case activity attachments
    settings.dvr.case_include_activity_docs = True
    # Beneficiary documents-tab includes case group attachments
    settings.dvr.case_include_group_docs = True

    # Manage individual response actions in case activities
    settings.dvr.manage_response_actions = True
    # Planning response actions, or just documenting them?
    settings.dvr.response_planning = get_ui_option("response_planning")
    # Responses use date+time
    settings.dvr.response_use_time = get_ui_option("response_use_time")
    # Response planning uses separate due-date
    settings.dvr.response_due_date = get_ui_option("response_due_date")
    # Use response themes
    settings.dvr.response_themes = True
    # Document response details per theme
    settings.dvr.response_themes_details = get_ui_option("response_themes_details")
    # Response themes are org-specific
    settings.dvr.response_themes_org_specific = True
    # Use response types
    settings.dvr.response_types = get_ui_option("response_types")
    # Response types hierarchical
    settings.dvr.response_types_hierarchical = True
    # Response themes organized by sectors
    settings.dvr.response_themes_sectors = get_ui_option("response_themes_sectors")
    # Response themes linked to needs
    settings.dvr.response_themes_needs = get_ui_option("response_themes_needs")
    # Auto-link responses to case activities
    settings.dvr.response_activity_autolink = get_ui_option("response_activity_autolink")
    # Do not use hierarchical vulnerability types (default)
    #settings.dvr.vulnerability_types_hierarchical = False

    # Expose flags to mark appointment types as mandatory
    settings.dvr.mandatory_appointments = False
    # Appointments with personal presence update last_seen_on
    settings.dvr.appointments_update_last_seen_on = False
    # Automatically update the case status when appointments are completed
    settings.dvr.appointments_update_case_status = True
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

        if r.controller == "dvr" or r.function == "organisation":

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

        s3db = current.s3db
        s3 = current.response.s3

        current.deployment_settings.ui.export_formats = None

        if current.request.controller == "dvr":

            # Use custom rheader for case perspective
            attr["rheader"] = drk_dvr_rheader

            # Set contacts-method to retain the tab
            s3db.set_method("pr", "person",
                            method = "contacts",
                            action = s3db.pr_Contacts,
                            )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            if not result:
                return False

            if r.controller == "dvr" and \
               (r.interactive or r.representation == "aadata"):

                configure_person_tags()

                table = r.table
                field = table.doc_id

                # Representation of doc entity
                ui_opts = get_ui_options()
                if ui_opts.get("activity_use_need"):
                    use_need = True
                    activity_label = T("Counseling Reason")
                else:
                    use_need = False
                    activity_label = None
                field.represent = s3db.dvr_DocEntityRepresent(
                                            show_link = True,
                                            use_need = use_need,
                                            case_group_label = T("Family"),
                                            activity_label = activity_label,
                                            )

                # Also update requires with this represent
                # => retain viewing-filters from standard prep
                requires = field.requires
                if isinstance(requires, IS_EMPTY_OR):
                    requires = requires.other
                if hasattr(requires, "filterby"):
                    filterby = requires.filterby
                    filter_opts = requires.filter_opts
                else:
                    filterby = filter_opts = None
                field.requires = IS_ONE_OF(current.db, "doc_entity.doc_id",
                                           field.represent,
                                           filterby = filterby,
                                           filter_opts = filter_opts,
                                           orderby = "instance_type",
                                           sort = False,
                                           )
            return result
        s3.prep = custom_prep

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
        except AttributeError:
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

        if r.controller == "dvr" and \
           r.name == "person" and not r.component:

            # Configure anonymize-method
            # TODO make standard via setting
            from s3 import S3Anonymize
            s3db.set_method("pr", "person",
                            method = "anonymize",
                            action = S3Anonymize,
                            )

            # Configure anonymize-rules
            s3db.configure("pr_person",
                           anonymize = drk_person_anonymize(),
                           )

            if current.auth.s3_has_role("CASE_MANAGEMENT"):
                # Allow use of Document Templates
                s3db.set_method("pr", "person",
                                method = "templates",
                                action = s3db.pr_Templates(),
                                )
                s3db.set_method("pr", "person",
                                method = "template",
                                action = s3db.pr_Template(),
                                )

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

        s3db.add_custom_callback("dvr_case", "onaccept", dvr_case_onaccept)

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
    def case_default_org():
        """
            Determine the default organisation for new cases
        """

        auth = current.auth
        realms = auth.permission.permitted_realms("dvr_case", "create")

        default_org = None

        if realms is None:
            # User can create cases for any org
            orgs = []
            multiple_orgs = True
        else:
            otable = current.s3db.org_organisation
            query = (otable.pe_id.belongs(realms)) & \
                    (otable.deleted == False)
            rows = current.db(query).select(otable.id)
            orgs = [row.id for row in rows]
            multiple_orgs = len(rows) > 1

        if multiple_orgs:
            # User can create cases for multiple orgs
            user_org = auth.user.organisation_id if auth.user else None
            if user_org and user_org in orgs:
                default_org = user_org
        elif orgs:
            # User can create cases for exactly one org
            default_org = orgs[0]

        return default_org, multiple_orgs

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        auth = current.auth
        s3db = current.s3db

        ui_options = get_ui_options()
        ui_options_get = ui_options.get
        response_tab_need_filter = ui_options_get("response_tab_need_filter")

        settings.base.bigtable = True

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

                resource = r.resource
                configure = resource.configure

                # Set contacts-method for tab
                s3db.set_method("pr", "person",
                                method = "contacts",
                                action = s3db.pr_Contacts,
                                )

                # Add explicit unclear-option for nationality if mandatory,
                # so that cases can be registered even if their nationality
                # is not at hand
                nationality_mandatory = ui_options_get("case_nationality_mandatory")
                settings.pr.nationality_explicit_unclear = nationality_mandatory

                # Autocomplete search-method
                if r.function == "person_search":
                    # Autocomplete-Widget (e.g. response actions)
                    search_fields = ("first_name", "last_name", "pe_label")
                else:
                    # Add-Person-Widget (family members)
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

                configure_person_tags()

                if not r.component:

                    # Can the user see cases from more than one org?
                    multiple_orgs = case_read_multiple_orgs()[0]

                    # Optional: pe_label (ID)
                    if ui_options_get("case_use_pe_label"):
                        pe_label = (T("ID"), "pe_label")
                    else:
                        pe_label = None

                    # Alternatives: site_id or simple text field
                    lodging_opt = ui_options_get("case_lodging")
                    if lodging_opt == "site":
                        lodging = "dvr_case.site_id"
                    elif lodging_opt == "text":
                        lodging = "case_details.lodging"
                    else:
                        lodging = None

                    if r.method == "report":

                        # Custom Report Options
                        facts = ((T("Number of Clients"), "count(id)"),
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
                                       S3TextFilter, \
                                       S3DateFilter, \
                                       S3OptionsFilter, \
                                       s3_get_filter_opts, \
                                       IS_PERSON_GENDER

                        # Default organisation
                        ctable = s3db.dvr_case
                        field = ctable.organisation_id
                        default_org, selectable = case_default_org()
                        if default_org:
                            if ui_options_get("case_hide_default_org"):
                                field.writable = selectable
                                field.readable = selectable or multiple_orgs
                        if field.readable and not field.writable:
                            field.comment = None
                        field.default = default_org

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
                        field.represent = s3db.hrm_HumanResourceRepresent(show_link=False)
                        field.widget = None

                        # Optional: Case Flags
                        if ui_options_get("case_use_flags"):
                            case_flags = S3SQLInlineLink("case_flag",
                                                         label = T("Flags"),
                                                         field = "flag_id",
                                                         help_field = "comments",
                                                         cols = 4,
                                                         )
                        else:
                            case_flags = None

                        # No comment for pe_label
                        field = table.pe_label
                        field.comment = None

                        # Optional: mandatory nationality
                        dtable = s3db.pr_person_details
                        if nationality_mandatory:
                            field = dtable.nationality
                            requires = field.requires
                            if isinstance(requires, IS_EMPTY_OR):
                                field.requires = requires.other

                        # Optional: place of birth
                        if ui_options_get("case_use_place_of_birth"):
                            field = dtable.place_of_birth
                            field.readable = field.writable = True
                            place_of_birth = "person_details.place_of_birth"
                        else:
                            place_of_birth = None

                        # Optional: BAMF No.
                        use_bamf = ui_options_get("case_use_bamf")
                        if use_bamf:
                            bamf = S3SQLInlineComponent(
                                        "bamf",
                                        fields = [("", "value")],
                                        filterby = {"field": "tag",
                                                    "options": "BAMF",
                                                    },
                                        label = T("BAMF Reference Number"),
                                        multiple = False,
                                        name = "bamf",
                                        )
                        else:
                            bamf = None

                        # Optional: referred by/to
                        use_referral = ui_options_get("case_use_referral")
                        if use_referral:
                            referred_by = "case_details.referred_by"
                            referred_to = "case_details.referred_to"
                        else:
                            referred_by = referred_to = None

                        # Make marital status mandatory, remove "other"
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

                        # Last name is required
                        field = table.last_name
                        field.requires = [IS_NOT_EMPTY(), IS_LENGTH(512, minsize=1)]

                        # Optional: site dates
                        if ui_options_get("case_lodging_dates"):
                            on_site_from = (T("Moving-in Date"),
                                            "case_details.on_site_from",
                                            )
                            on_site_until = (T("Moving-out Date"),
                                             "case_details.on_site_until",
                                             )
                        else:
                            on_site_from = None
                            on_site_until = None

                        # Optional: Address
                        if ui_options_get("case_use_address"):
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

                        # Date of Entry (alternative labels)
                        dtable = s3db.dvr_case_details
                        field = dtable.arrival_date
                        label = ui_options_get("case_arrival_date_label")
                        label = T(label) if label else T("Date of Entry")
                        field.label = label
                        field.comment = DIV(_class = "tooltip",
                                            _title = "%s|%s" % (label,
                                                                T("Date of Entry Certificate"),
                                                                ),
                                            )

                        # Optional: Residence Status
                        if ui_options_get("case_use_residence_status"):
                            # Remove Add-links
                            rtable = s3db.dvr_residence_status
                            field = rtable.status_type_id
                            field.comment = None
                            field = rtable.permit_type_id
                            field.comment = None
                            residence_status = S3SQLInlineComponent(
                                                "residence_status",
                                                fields = [#"status_type_id",
                                                          "permit_type_id",
                                                          #"reference",
                                                          #"valid_from",
                                                          "valid_until",
                                                          "comments",
                                                          ],
                                                label = T("Residence Status"),
                                                multiple = False,
                                                )
                        else:
                            residence_status = None

                        # Optional: Occupation/Educational Background
                        if ui_options_get("case_use_occupation"):
                            occupation = "person_details.occupation"
                        else:
                            occupation = None
                        if ui_options_get("case_use_education"):
                            education = "person_details.education"
                        else:
                            education = None

                        # Custom CRUD form
                        crud_form = S3SQLCustomForm(

                            # Case Details ----------------------------
                            "dvr_case.date",
                            "dvr_case.organisation_id",
                            "dvr_case.human_resource_id",
                            (T("Case Status"), "dvr_case.status_id"),
                            case_flags,

                            # Person Details --------------------------
                            pe_label,
                            "last_name",
                            "first_name",
                            "person_details.nationality",
                            "date_of_birth",
                            place_of_birth,
                            bamf,
                            "case_details.arrival_date",
                            "gender",
                            "person_details.marital_status",

                            # Process Data ----------------------------
                            referred_by,
                            referred_to,
                            lodging,
                            on_site_from,
                            on_site_until,
                            address,
                            residence_status,

                            # Other Details ---------------------------
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
                            education,
                            occupation,
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
                            ]

                        # BAMF-Ref.No.-filter if using BAMF
                        if use_bamf:
                            filter_widgets.append(
                                S3TextFilter(["bamf.value"],
                                             label = T("BAMF Ref.No."),
                                             hidden = True,
                                             ))

                        # Multi-ID filter if using ID
                        if pe_label is not None:
                            filter_widgets.append(
                                S3TextFilter(["pe_label"],
                                             label = T("IDs"),
                                             match_any = True,
                                             hidden = True,
                                             comment = T("Search for multiple IDs (separated by blanks)"),
                                             ))

                        # Ref.No.-filter if using service contacts
                        if ui_options_get("case_use_service_contacts"):
                            filter_widgets.append(
                                S3TextFilter(["service_contact.reference"],
                                             label = T("Ref.No."),
                                             hidden = True,
                                             comment = T("Search by service contact reference number"),
                                             ))

                        # Flag-filter if using case flags
                        if case_flags:
                            filter_widgets.insert(2,
                                S3OptionsFilter("case_flag_case.flag_id",
                                                label = T("Flags"),
                                                options = s3_get_filter_opts("dvr_case_flag",
                                                                             translate = True,
                                                                             ),
                                                cols = 3,
                                                hidden = True,
                                                ))
                        # Org-filter if user can see cases from multiple orgs/branches
                        if multiple_orgs:
                            filter_widgets.insert(1,
                                S3OptionsFilter("dvr_case.organisation_id"))

                        configure(crud_form = crud_form,
                                  filter_widgets = filter_widgets,
                                  )

                    # Custom list fields (must be outside of r.interactive)
                    list_fields = [pe_label,
                                   "last_name",
                                   "first_name",
                                   "date_of_birth",
                                   "gender",
                                   "person_details.nationality",
                                   "dvr_case.date",
                                   "dvr_case.status_id",
                                   lodging,
                                   ]
                    if multiple_orgs:
                        list_fields.insert(-1, "dvr_case.organisation_id")

                    configure(list_fields = list_fields)

                elif r.component_name == "case_appointment":

                    if ui_options_get("appointments_use_organizer") and \
                       r.interactive and r.method is None and not r.component_id:
                        r.method = "organize"

                elif r.component_name == "response_action":

                    if response_tab_need_filter:
                        # Configure filter widgets for response tab
                        from s3 import S3DateFilter, S3OptionsFilter, S3TextFilter
                        r.component.configure(
                            filter_widgets = [
                               S3TextFilter(["response_action_theme.theme_id$name",
                                             "response_action_theme.comments",
                                             ],
                                            label = T("Search"),
                                            ),
                               S3OptionsFilter("response_action_theme.theme_id$need_id",
                                               label = T("Counseling Reason"),
                                               hidden = True,
                                               ),
                               S3DateFilter("start_date",
                                            hidden = True,
                                            hide_time = not ui_options_get("response_use_time"),
                                            ),
                               ],
                            )
                        settings.search.filter_manager = False

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

        standard_postp = s3.postp
        def custom_postp(r, output):

            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.controller == "dvr" and \
               not r.component and r.record and \
               r.method in (None, "update", "read") and \
               isinstance(output, dict):

                # Custom CRUD buttons
                if "buttons" not in output:
                    buttons = output["buttons"] = {}
                else:
                    buttons = output["buttons"]

                # Anonymize-button
                from s3 import S3AnonymizeWidget
                anonymize = S3AnonymizeWidget.widget(r,
                                         _class="action-btn anonymize-btn")

                # Doc-From-Template-button
                if ui_options_get("case_document_templates") and \
                   auth.s3_has_role("CASE_MANAGEMENT"):
                    doc_from_template = A(T("Document from Template"),
                                          _class = "action-btn s3_modal",
                                          _title = T("Generate Document from Template"),
                                          _href = URL(args=[r.id, "templates"]),
                                          )
                else:
                    doc_from_template = ""

                # Render in place of the delete-button
                buttons["delete_btn"] = TAG[""](doc_from_template,
                                                anonymize,
                                                )

            return output
        s3.postp = custom_postp

        if current.request.controller == "dvr":
            attr = dict(attr)
            # Custom rheader
            attr["rheader"] = drk_dvr_rheader
            # Activate filters on component tabs
            if response_tab_need_filter:
                attr["hide_filter"] = {"response_action": False}

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

        ui_options = get_ui_options()

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

                configure_person_tags()

                if ui_options.get("case_use_pe_label"):
                    pe_label = (T("ID"), "person_id$pe_label")
                else:
                    pe_label = None
                s3db.pr_person.pe_label.label = T("ID")

                if r.interactive:
                    table = resource.table

                    from s3 import S3AddPersonWidget

                    field = table.person_id
                    field.represent = s3db.pr_PersonRepresent(show_link=True)
                    field.widget = S3AddPersonWidget(controller = "dvr",
                                                     pe_label = bool(pe_label),
                                                     )

                    field = table.role_id
                    field.readable = field.writable = True
                    field.label = ROLE
                    field.comment = DIV(_class="tooltip",
                                        _title="%s|%s" % (T("Role"),
                                                          T("The role of the person within the family"),
                                                          ))
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

                list_fields = [pe_label,
                               "person_id",
                               "person_id$date_of_birth",
                               "person_id$gender",
                               "group_head",
                               (ROLE, "role_id"),
                               (T("Case Status"), "person_id$dvr_case.status_id"),
                               "comments",
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

            # New cases created on family tab inherit organisation_id
            # and human_resource_id from master case:
            viewing = r.get_vars.get("viewing")
            if viewing and viewing[:10] == "pr_person.":
                try:
                    vid = int(viewing[10:])
                except ValueError:
                    pass
                else:
                    ctable = s3db.dvr_case
                    query = (ctable.person_id == vid) & \
                            (ctable.archived == False) & \
                            (ctable.deleted == False)
                    case = current.db(query).select(ctable.organisation_id,
                                                    ctable.human_resource_id,
                                                    limitby = (0, 1),
                                                    ).first()
                    if case:
                        ctable.organisation_id.default = case.organisation_id
                        ctable.human_resource_id.default = case.human_resource_id

        # Custom onaccept to update realm-entity of the
        # beneficiary and case activities of this case
        # (incl. their respective realm components)
        s3db.add_custom_callback("dvr_case", "onaccept", dvr_case_onaccept)

        # Update the realm-entity when the case gets updated
        # (because the assigned organisation/branch can change)
        s3db.configure("dvr_case", update_realm = True)

    settings.customise_dvr_case_resource = customise_dvr_case_resource

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
        table = s3db.dvr_case_activity

        if r.method == "count_due_followups":
            # Just counting due followups => skip customisation
            return

        human_resource_id = auth.s3_logged_in_human_resource()

        ui_options = get_ui_options()
        ui_options_get = ui_options.get

        use_priority = ui_options_get("activity_priority")

        # Optional: closure details
        if ui_options_get("activity_closure"):
            # Activities can be closed
            status_id = "status_id"
            end_date = "end_date"
            outcome = "outcome"
        else:
            # Activities are never closed
            status_id = None
            table.start_date.label = T("Date")
            end_date = None
            outcome = None

        # Activity subject
        if ui_options_get("activity_use_need"):
            # Use need type
            subject_field = "need_id"
            subject_list_field = (T("Counseling Reason"), "need_id")
        else:
            # Use free-text field
            subject_list_field = subject_field = "subject"

        # Using sectors?
        activity_use_sector = ui_options_get("activity_use_sector")

        if r.method == "report":

            # Custom Report Options
            facts = ((T("Number of Activities"), "count(id)"),
                     (T("Number of Clients"), "count(person_id)"),
                     )
            axes = ["person_id$gender",
                    "person_id$person_details.nationality",
                    "person_id$person_details.marital_status",
                    (T("Theme"), "response_action.response_theme_ids"),
                    ]
            if use_priority:
                axes.insert(-1, "priority")

            default_rows = "response_action.response_theme_ids"
            default_cols = "person_id$person_details.nationality"

            # Add the sector_id axis when using sectors
            if activity_use_sector:
                axes.insert(-1, "sector_id")
                default_rows = "sector_id"

            # Add the need_id axis when using needs
            if subject_field == "need_id":
                axes.insert(-1, "need_id")
                default_rows = "need_id"

            # Add status_id axis when using status
            if status_id == "status_id":
                axes.insert(3, status_id)
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
            s3db.configure("dvr_case_activity",
                           report_options = report_options,
                           )
            crud_strings = current.response.s3.crud_strings["dvr_case_activity"]
            crud_strings["title_report"] = T("Activity Statistic")

        if r.interactive or r.representation in ("aadata", "json"):

            from s3 import S3SQLCustomForm, \
                           S3SQLInlineComponent, \
                           S3SQLInlineLink, \
                           S3SQLVerticalSubFormLayout

            # Represent person_id as link
            field = table.person_id
            field.represent = s3db.pr_PersonRepresent(show_link = True)

            # Get person_id, case_activity_id and case activity record
            person_id = case_activity_id = case_activity = None
            if r.tablename == "pr_person":
                # On activities-tab of a case
                person_id = r.record.id if r.record else None
                component = r.component
                if component and component.tablename == "dvr_case_activity":
                    case_activity_id = r.component_id

            elif r.tablename == "dvr_case_activity":
                # Primary case activity controller
                case_activity = r.record
                if case_activity:
                    person_id = case_activity.person_id
                    case_activity_id = r.id

            db = current.db

            # Get the root org of the case
            case_root_org = get_case_root_org(person_id)

            # Configure sector_id
            field = table.sector_id
            field.comment = None
            if ui_options_get("activity_use_sector"):

                # Get the root org for sector selection
                if case_root_org:
                    sector_root_org = case_root_org
                else:
                    sector_root_org = auth.root_org()

                if sector_root_org:
                    # Limit the sector selection
                    ltable = s3db.org_sector_organisation
                    query = (ltable.organisation_id == sector_root_org) & \
                            (ltable.deleted == False)
                    rows = db(query).select(ltable.sector_id)
                    sector_ids = set(row.sector_id for row in rows)

                    # Default sector
                    if len(sector_ids) == 1:
                        default_sector_id = rows.first().sector_id
                    else:
                        default_sector_id = None

                    # Include the sector_id of the current record (if any)
                    record = None
                    component = r.component
                    if not component:
                        if r.tablename == "dvr_case_activity":
                            record = r.record
                    elif component.tablename == "dvr_case_activity" and r.component_id:
                        query = table.id == r.component_id
                        record = db(query).select(table.sector_id,
                                                  limitby = (0, 1),
                                                  ).first()
                    if record and record.sector_id:
                        sector_ids.add(record.sector_id)

                    # Set selectable sectors
                    subset = db(s3db.org_sector.id.belongs(sector_ids))
                    field.requires = IS_EMPTY_OR(IS_ONE_OF(subset, "org_sector.id",
                                                           field.represent,
                                                           ))

                    # Default selection?
                    if len(sector_ids) == 1 and default_sector_id:
                        # Single option => set as default and hide selector
                        field.default = default_sector_id
                        field.readable = field.writable = False
            else:
                field.readable = field.writable = False

            # Configure subject field (alternatives)
            if subject_field == "need_id":

                # Are we looking at a particular case activity?
                if r.tablename != "dvr_case_activity":
                    activity_id = r.component_id
                else:
                    activity_id = r.id

                # Shall we automatically link responses to activities?
                autolink = ui_options_get("response_activity_autolink")

                # Expose need_id
                field = table.need_id
                field.label = T("Counseling Reason")
                field.readable = True
                field.writable = not activity_id or not autolink

                # Limit to org-specific need types
                if case_root_org:
                    needs_root_org = case_root_org
                else:
                    needs_root_org = auth.root_org()
                ntable = s3db.dvr_need
                if needs_root_org:
                    query = (ntable.organisation_id == needs_root_org)
                else:
                    query = None

                # With autolink, prevent multiple activities per need type
                if autolink:
                    joinq = (table.need_id == ntable.id) & \
                            (table.person_id == person_id) & \
                            (table.deleted == False)
                    if activity_id:
                        joinq &= (table.activity_id != activity_id)
                    left = table.on(joinq)
                    q = (table.id == None)
                    query = query & q if query else q
                else:
                    left = None

                if query:
                    field.requires = IS_ONE_OF(db(query), "dvr_need.id",
                                               field.represent,
                                               left = left,
                                               )
            else:
                # Expose simple free-text subject
                field = table.subject
                field.readable = field.writable = True
                field.requires = [IS_NOT_EMPTY(), IS_LENGTH(512, minsize=1)]

            # Show need details (optional)
            field = table.need_details
            field.readable = field.writable = ui_options_get("activity_need_details")

            # Embed vulnerability
            if ui_options_get("activity_pss_vulnerability"):
                vulnerability = S3SQLInlineLink("vulnerability_type",
                                                label = T("Diagnosis / Suspected"),
                                                field = "vulnerability_type_id",
                                                multiple = False,
                                                )
            else:
                vulnerability = None

            # Customise Priority
            field = table.priority
            priority_opts = [(0, T("Emergency")),
                             (1, T("High")),
                             (2, T("Normal")),
                             (3, T("Low")),
                             ]
            field.readable = field.writable = use_priority
            field.label = T("Priority")
            field.default = 2
            field.requires = IS_IN_SET(priority_opts, sort=False, zero=None)
            field.represent = PriorityRepresent(priority_opts,
                                                {0: "red",
                                                 1: "blue",
                                                 2: "lightblue",
                                                 3: "grey",
                                                 }).represent
            priority_field = "priority" if use_priority else None

            # Show human_resource_id
            hr_represent = s3db.hrm_HumanResourceRepresent(show_link=False)
            field = table.human_resource_id
            field.comment = None
            field.default = human_resource_id
            field.label = T("Consultant in charge")
            field.readable = field.writable = True
            field.represent = hr_represent
            field.widget = None

            # Show end_date field (read-only)
            if end_date is not None:
                field = table.end_date
                field.label = T("Completed on")
                field.readable = True

            # Show comments
            field = table.comments
            field.readable = field.writable = ui_options_get("activity_comments")

            # Inline-responses
            rtable = s3db.dvr_response_action
            configure_response_theme_selector(ui_options,
                                              case_root_org = case_root_org,
                                              case_activity = case_activity,
                                              case_activity_id = case_activity_id,
                                              )

            if settings.get_dvr_response_themes_details():
                # Embed response action themes
                inline_responses = S3SQLInlineComponent(
                                        "response_action_theme",
                                        fields = ["action_id",
                                                  "theme_id",
                                                  "comments",
                                                  ],
                                        label = T("Themes"),
                                        orderby = "action_id",
                                        )

                # Filter action_id in inline response_themes to same beneficiary
                ltable = s3db.dvr_response_action_theme
                field = ltable.action_id
                dbset = db(rtable.person_id == person_id) if person_id else db
                field.requires = IS_EMPTY_OR(IS_ONE_OF(
                                                dbset, "dvr_response_action.id",
                                                field.represent,
                                                orderby = ~rtable.start_date,
                                                sort = False,
                                                ))
            else:
                if person_id:
                    # Set the person_id for inline responses (does not not happen
                    # automatically since using case_activity_id as component key)
                    field = rtable.person_id
                    field.default = person_id

                field = rtable.human_resource_id
                field.default = human_resource_id
                field.represent = hr_represent
                field.widget = field.comment = None

                # Require explicit unit in hours-widget above 4 hours
                from s3 import S3HoursWidget
                field = rtable.hours
                field.widget = S3HoursWidget(precision = 2,
                                             explicit_above = 4,
                                             )

                # Embed response actions
                response_action_fields = ["response_theme_ids",
                                          "comments",
                                          "human_resource_id",
                                          "start_date",
                                          "status_id",
                                          "hours",
                                          ]
                if settings.get_dvr_response_due_date():
                    response_action_fields.insert(1, "date_due")
                if settings.get_dvr_response_types():
                    response_action_fields.insert(0, "response_type_id")

                s3db.add_custom_callback("dvr_response_action",
                                         "onvalidation",
                                         response_action_onvalidation,
                                         )

                inline_responses = S3SQLInlineComponent(
                                            "response_action",
                                            label = T("Actions"),
                                            fields = response_action_fields,
                                            layout = S3SQLVerticalSubFormLayout,
                                            explicit_add = T("Add Action"),
                                            )

            # Inline-updates
            utable = current.s3db.dvr_case_activity_update

            field = utable.human_resource_id
            field.default = human_resource_id
            field.represent = hr_represent
            field.widget = field.comment = None

            # Custom CRUD form
            crud_form = S3SQLCustomForm(
                            "person_id",

                            "sector_id",

                            subject_field,
                            vulnerability,
                            (T("Initial Situation Details"), ("need_details")),

                            "start_date",
                            priority_field,
                            "human_resource_id",

                            inline_responses,
                            #S3SQLInlineComponent("response_action",
                            #                     label = T("Actions"),
                            #                     fields = response_action_fields,
                            #                     layout = S3SQLVerticalSubFormLayout,
                            #                     explicit_add = T("Add Action"),
                            #                     ),

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

                            status_id,
                            end_date,

                            outcome,

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
                           orderby = "dvr_case_activity.priority" \
                                     if use_priority else "dvr_case_activity.start_date desc",
                           )

        # Custom list fields for case activity component tab
        if r.tablename != "dvr_case_activity":
            list_fields = ["priority" if use_priority else None,
                           #"sector_id",
                           subject_list_field,
                           #"followup",
                           #"followup_date",
                           "start_date",
                           "human_resource_id",
                           status_id,
                           ]
            if table.sector_id.readable:
                list_fields.insert(1, "sector_id")

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

        s3db = current.s3db

        s3 = current.response.s3

        settings.base.bigtable = True

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

            # Get UI options
            ui_options = get_ui_options()
            ui_options_get = ui_options.get

            use_priority = ui_options.get("activity_priority")

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
                               S3OptionsFilter

                db = current.db

                # Sector filter options
                # (field options are configured in customise_*_resource)
                sector_id = resource.table.sector_id
                sector_options = {k:v for k, v in sector_id.requires.options() if k}

                # Status filter options + defaults, status list field
                if ui_options_get("activity_closure"):
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
                    status_filter = S3OptionsFilter("status_id",
                                                    options = status_filter_options,
                                                    cols = 3,
                                                    default = status_filter_defaults,
                                                    sort = False,
                                                    )
                    status_id = "status_id"
                else:
                    status_filter = None
                    status_id = None

                # Filter widgets
                filter_widgets = [
                    S3TextFilter(["person_id$pe_label",
                                  "person_id$first_name",
                                  "person_id$last_name",
                                  "need_details",
                                  ],
                                  label = T("Search"),
                                  ),
                    S3OptionsFilter("person_id$person_details.nationality",
                                    label = T("Client Nationality"),
                                    hidden = True,
                                    ),
                    ]

                if sector_id.readable:
                    filter_widgets.insert(1, S3OptionsFilter(
                                                "sector_id",
                                                hidden = True,
                                                options = sector_options,
                                                ))
                if status_filter:
                    filter_widgets.insert(1, status_filter)

                # Priority filter (unless pre-filtered to emergencies anyway)
                if use_priority and not emergencies:
                    field = resource.table.priority
                    priority_opts = OrderedDict(field.requires.options())
                    priority_filter = S3OptionsFilter("priority",
                                                      options = priority_opts,
                                                      cols = 4,
                                                      sort = False,
                                                      )
                    filter_widgets.insert(2, priority_filter)

                # Can the user see cases from more than one org?
                multiple_orgs = case_read_multiple_orgs()[0]
                if multiple_orgs:
                    # Add org-filter widget
                    filter_widgets.insert(1,
                                          S3OptionsFilter("person_id$dvr_case.organisation_id"),
                                          )

                # Subject field (alternatives)
                if ui_options_get("activity_use_need"):
                    subject_field = "need_id"
                else:
                    subject_field = "subject"

                # Optional: pe_label (ID)
                if ui_options_get("case_use_pe_label"):
                    pe_label = (T("ID"), "person_id$pe_label")
                else:
                    pe_label = None

                # Custom list fields
                list_fields = ["priority" if use_priority else None,
                               pe_label,
                               (T("Case"), "person_id"),
                               #"sector_id",
                               subject_field,
                               "start_date",
                               #"followup",
                               #"followup_date",
                               status_id,
                               ]
                if sector_id.readable:
                    list_fields.insert(3, "sector_id")

                # Person responsible filter and list_field
                if not r.get_vars.get("mine"):
                    filter_widgets.insert(2, S3OptionsFilter("human_resource_id"))
                    list_fields.insert(5, "human_resource_id")

                # Reconfigure table
                resource.configure(filter_widgets = filter_widgets,
                                   list_fields = list_fields,
                                   )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_dvr_case_activity_controller = customise_dvr_case_activity_controller

    # -------------------------------------------------------------------------
    def customise_dvr_case_appointment_resource(r, tablename):

        s3db = current.s3db

        ui_options = get_ui_options()

        # Organizer popups
        if r.tablename == "pr_person":
            title = "type_id"
            description = ["status",
                           "comments",
                           ]
        elif r.tablename == "dvr_case_appointment":
            title = "person_id"
            description = ["type_id",
                           "status",
                           "comments",
                           ]
            if ui_options.get("case_use_pe_label"):
                description.insert(0, (T("ID"), "person_id$pe_label"))
        else:
            title = description = None

        table = s3db.dvr_case_appointment

        field = table.status
        # Using only a subset of the standard status opts
        appointment_status_opts = {#1: T("Planning"),
                                   2: T("Planned"),
                                   #3: T("In Progress"),
                                   4: T("Completed##appointment"),
                                   5: T("Missed"),
                                   6: T("Cancelled"),
                                   #7: T("Not Required"),
                                   }
        field.default = 2
        field.requires = IS_IN_SET(appointment_status_opts,
                                   zero = None,
                                   )

        if ui_options.get("appointments_staff_link"):
            # Enable staff link and default to logged-in user
            field = table.human_resource_id
            field.default = current.auth.s3_logged_in_human_resource()
            field.readable = field.writable = True
            field.represent = s3db.hrm_HumanResourceRepresent(show_link=False)
            field.widget = None
            # Also show staff link in organizer popup
            if description:
                description.insert(-1, "human_resource_id")

        # Configure Organizer
        if title:
            s3db.configure("dvr_case_appointment",
                           organize = {"start": "date",
                                       "title": title,
                                       "description": description,
                                       },
                           )

    settings.customise_dvr_case_appointment_resource = customise_dvr_case_appointment_resource

    # -------------------------------------------------------------------------
    def customise_dvr_case_appointment_controller(**attr):

        s3 = current.response.s3
        s3db = current.s3db

        ui_options = get_ui_options()

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
                use_pe_label = ui_options.get("case_use_pe_label")

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
                        ]

                    if use_pe_label:
                        filter_widgets.append(
                            S3TextFilter(["person_id$pe_label"],
                                         label = T("IDs"),
                                         match_any = True,
                                         hidden = True,
                                         comment = T("Search for multiple IDs (separated by blanks)"),
                                         ))

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

                # Optional: ID
                if use_pe_label:
                    pe_label = (T("ID"), "person_id$pe_label")
                else:
                    pe_label = None

                # Custom list fields
                list_fields = [pe_label,
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
    def customise_dvr_need_resource(r, tablename):

        table = current.s3db.dvr_need

        # Expose organisation_id (only relevant for ADMINs)
        field = table.organisation_id
        field.readable = field.writable = True

        # Expose protection flag
        field = table.protection
        field.readable = field.writable = True

        # Custom CRUD Strings
        current.response.s3.crud_strings["dvr_need"] = Storage(
            label_create = T("Create Counseling Reason"),
            title_display = T("Counseling Reason Details"),
            title_list = T("Counseling Reason"),
            title_update = T("Edit Counseling Reason"),
            label_list_button = T("List Counseling Reasons"),
            label_delete_button = T("Delete Counseling Reason"),
            msg_record_created = T("Counseling Reason created"),
            msg_record_modified = T("Counseling Reason updated"),
            msg_record_deleted = T("Counseling Reason deleted"),
            msg_list_empty = T("No Counseling Reasons currently defined"),
        )

    settings.customise_dvr_need_resource = customise_dvr_need_resource

    # -------------------------------------------------------------------------
    def get_case_root_org(person_id):
        """
            Get the root organisation managing a case

            @param person_id: the person record ID

            @returns: the root organisation record ID
        """

        db = current.db
        s3db = current.s3db

        if person_id:
            ctable = s3db.dvr_case
            otable = s3db.org_organisation
            left = otable.on(otable.id == ctable.organisation_id)
            query = (ctable.person_id == person_id) & \
                    (ctable.archived == False) & \
                    (ctable.deleted == False)
            row = db(query).select(otable.root_organisation,
                                   left = left,
                                   limitby = (0, 1),
                                   orderby = ~ctable.modified_on,
                                   ).first()
            case_root_org = row.root_organisation if row else None
        else:
            case_root_org = None

        return case_root_org

    # -------------------------------------------------------------------------
    def configure_response_theme_selector(ui_options,
                                          case_root_org = None,
                                          person_id = None,
                                          case_activity = None,
                                          case_activity_id = None,
                                          ):
        """
            Configure response theme selector

            @param ui_options: the UI options for the current org
            @param case_root_org: the case root organisation
            @param person_id: the person record ID (to look up the root org)
            @param case_activity: the case activity record
            @param case_activity_id: the case activity record ID
                                     (to look up the case activity record)
        """

        db = current.db
        s3db = current.s3db

        ttable = s3db.dvr_response_theme
        query = None

        # Limit themes to the themes of the case root organisation
        if not case_root_org:
            case_root_org = get_case_root_org(person_id)
            if not case_root_org:
                case_root_org = current.auth.root_org()
        if case_root_org:
            query = (ttable.organisation_id == case_root_org)

        themes_needs = settings.get_dvr_response_themes_needs()
        if ui_options.get("activity_use_need") and themes_needs:

            # Limit themes to those matching the need of the activity
            if case_activity:
                need_id = case_activity.need_id
            elif case_activity_id:
                # Look up the parent record
                catable = s3db.dvr_case_activity
                case_activity = db(catable.id == case_activity_id).select(catable.need_id,
                                                                          limitby = (0, 1),
                                                                          ).first()
                need_id = case_activity.need_id if case_activity else None
            else:
                need_id = None
            if need_id:
                q = (ttable.need_id == need_id)
                query = query & q if query else q

        dbset = db(query) if query else db

        table = s3db.dvr_response_action
        field = table.response_theme_ids

        if themes_needs:
            # Include the need in the themes-selector
            # - helps to find themes using the selector search field
            represent = s3db.dvr_ResponseThemeRepresent(multiple = True,
                                                        translate = True,
                                                        show_need = True,
                                                        )
        else:
            represent = field.represent

        field.requires = IS_ONE_OF(dbset, "dvr_response_theme.id",
                                   represent,
                                   multiple = True,
                                   )
        if ui_options.get("response_themes_optional"):
            # Allow responses without theme
            field.requires = IS_EMPTY_OR(field.requires)

        table = s3db.dvr_response_action_theme
        field = table.theme_id
        field.requires = IS_ONE_OF(dbset, "dvr_response_theme.id",
                                   represent,
                                   )
        if ui_options.get("response_themes_optional"):
            field.requires = IS_EMPTY_OR(field.requires)

    # -------------------------------------------------------------------------
    def response_action_onvalidation(form):
        """
            Onvalidation for response actions:
                - enforce hours for closed-statuses (org-specific UI option)
        """

        ui_options = get_ui_options()
        if ui_options.get("response_effort_required"):

            db = current.db
            s3db = current.s3db
            form_vars = form.vars

            # Get the new status
            if "status_id" in form_vars:
                status_id = form_vars.status_id
            else:
                status_id = s3db.dvr_response_action.status_id.default

            try:
                hours = form_vars.hours
            except AttributeError:
                # No hours field in form, so no point validating it
                return

            if hours is None:
                # If new status is closed, require hours
                stable = s3db.dvr_response_status
                query = (stable.id == status_id)
                status = db(query).select(stable.is_closed,
                                          limitby = (0, 1),
                                          ).first()
                if status and status.is_closed:
                    form.errors["hours"] = T("Please specify the effort spent")

    # -------------------------------------------------------------------------
    def response_date_dt_orderby(field, direction, orderby, left_joins):
        """
            When sorting response actions by date, use created_on to maintain
            consistent order of multiple response actions on the same date
        """

        sorting = {"table": field.tablename,
                   "direction": direction,
                   }
        orderby.append("%(table)s.start_date%(direction)s,%(table)s.created_on%(direction)s" % sorting)

    # -------------------------------------------------------------------------
    def customise_dvr_response_action_resource(r, tablename):

        #db = current.db
        s3db = current.s3db

        table = s3db.dvr_response_action

        ui_options = get_ui_options()
        ui_options_get = ui_options.get

        # Can the user see cases from more than one org?
        multiple_orgs, org_ids = case_read_multiple_orgs()

        org_context = "person_id$dvr_case.organisation_id"

        # Represent for dvr_response_action_theme.id
        response_themes_details = settings.get_dvr_response_themes_details()
        if response_themes_details:
            ltable = s3db.dvr_response_action_theme
            ltable.id.represent = s3db.dvr_ResponseActionThemeRepresent(
                                            paragraph = True,
                                            details = True,
                                            )

        # Use date+time in responses?
        use_time = settings.get_dvr_response_use_time()

        # Using response types?
        use_response_type = settings.get_dvr_response_types()
        response_type = "response_type_id" if use_response_type else None

        is_report = r.method == "report"
        if is_report:

            # Sector Axis
            if settings.get_dvr_response_themes_sectors():
                sector = "dvr_response_action_theme.theme_id$sector_id"
                default_cols = None
            else:
                sector = "case_activity_id$sector_id"
                default_cols = sector

            # Needs Axis
            if settings.get_dvr_response_themes_needs():
                need = (T("Counseling Reason"),
                        "dvr_response_action_theme.theme_id$need_id",
                        )
            else:
                need = None

            # Vulnerability Axis
            if ui_options_get("activity_pss_vulnerability"):
                diagnosis = (T("Diagnosis / Suspected"),
                             "case_activity_id$vulnerability_type__link.vulnerability_type_id",
                             )
            else:
                diagnosis = None

            # Custom Report Options
            facts = ((T("Number of Actions"), "count(id)"),
                     (T("Number of Clients"), "count(person_id)"),
                     (T("Hours (Total)"), "sum(hours)"),
                     (T("Hours (Average)"), "avg(hours)"),
                     )
            axes = ("person_id$gender",
                    "person_id$person_details.nationality",
                    "person_id$person_details.marital_status",
                    (T("Size of Family"), "person_id$dvr_case.household_size"),
                    diagnosis,
                    response_type,
                    (T("Theme"), "response_theme_ids"),
                    need,
                    sector,
                    "human_resource_id",
                    )
            if multiple_orgs:
                # Add case organisation as report axis
                axes = axes + (org_context,)

            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": facts,
                "defaults": {"rows": "response_theme_ids",
                             "cols": default_cols,
                             "fact": "count(id)",
                             "totals": True,
                             },
                "precision": {"hours": 2, # higher precision is impractical
                              },
                }
            s3db.configure("dvr_response_action",
                           report_options = report_options,
                           )
            crud_strings = current.response.s3.crud_strings["dvr_response_action"]
            crud_strings["title_report"] = T("Action Statistic")

        if r.interactive or r.representation in ("aadata", "xls", "pdf"):

            human_resource_id = current.auth.s3_logged_in_human_resource()

            # Use drop-down for human_resource_id
            field = table.human_resource_id
            field.default = human_resource_id
            field.represent = s3db.hrm_HumanResourceRepresent(show_link=False)
            field.widget = None

            hr_filter_opts = False
            hr_filter_default = None
            mine = r.get_vars.get("mine")
            if mine not in ("a", "r"):
                # Populate hr_filter_opts to enable filter widget
                # - use field options as filter options
                try:
                    hr_filter_opts = field.requires.options()
                except AttributeError:
                    pass
                if mine == "f":
                    hr_filter_default = human_resource_id

            # Require explicit unit in hours-widget above 4 hours
            from s3 import S3HoursWidget
            field = table.hours
            field.widget = S3HoursWidget(precision = 2,
                                         explicit_above = 4,
                                         )

            # Use separate due-date field?
            use_due_date = settings.get_dvr_response_due_date()
            date_due = "date_due" if use_due_date else None

            # Configure theme selector
            if r.tablename == "dvr_response_action":
                is_master = True
                person_id = r.record.person_id if r.record else None
            elif r.tablename == "pr_person" and \
                 r.component and r.component.tablename == "dvr_response_action":
                is_master = False
                person_id = r.record.id if r.record else None

            configure_response_theme_selector(ui_options,
                                              person_id = person_id,
                                              )

            get_vars = r.get_vars
            if not is_master or "viewing" in get_vars:
                # Component tab (or viewing-tab) of case

                # Hide person_id
                field = table.person_id
                field.readable = field.writable = False

                if response_themes_details:
                    list_fields = ["start_date",
                                   (T("Themes"), "dvr_response_action_theme.id"),
                                   "human_resource_id",
                                   "hours",
                                   "status_id",
                                   ]
                    pdf_fields = ["start_date",
                                  #"human_resource_id",
                                  (T("Themes"), "dvr_response_action_theme.id"),
                                  ]
                else:
                    # Show case_activity_id
                    field = table.case_activity_id
                    field.readable = True

                    # Adjust representation to perspective
                    if ui_options_get("activity_use_need"):
                        field.label = T("Counseling Reason")
                        show_as = "need"
                    else:
                        field.label = T("Subject")
                        show_as = "subject"

                    represent = s3db.dvr_CaseActivityRepresent(show_as=show_as,
                                                               show_link=True,
                                                               )
                    field.represent = represent

                    # Make activity selectable if not auto-linking, and
                    # filter options to case
                    if not ui_options_get("response_activity_autolink"):
                        field.writable = True
                        field.requires = IS_ONE_OF(current.db,
                                                   "dvr_case_activity.id",
                                                   represent,
                                                   filterby = "person_id",
                                                   filter_opts = (person_id,),
                                                   )
                    else:
                        field.writable = False

                    # Adapt list-fields to perspective
                    list_fields = ["case_activity_id",
                                   response_type,
                                   "response_theme_ids",
                                   "comments",
                                   "human_resource_id",
                                   date_due,
                                   "start_date",
                                   "hours",
                                   "status_id",
                                   ]
                    pdf_fields = ["start_date",
                                  #"human_resource_id",
                                  "case_activity_id",
                                  response_type,
                                  "response_theme_ids",
                                  "comments",
                                  ]

                s3db.configure("dvr_response_action",
                               filter_widgets = None,
                               list_fields = list_fields,
                               pdf_fields = pdf_fields,
                               )
                if "viewing" in get_vars:
                    s3db.configure("dvr_response_action",
                                   create_next = r.url(id="", method=""),
                                   update_next = r.url(id="", method=""),
                                   )
            else:
                # Primary dvr/response_action controller

                if ui_options_get("case_use_pe_label"):
                    pe_label = (T("ID"), "person_id$pe_label")
                else:
                    pe_label = None

                # Adapt list-fields to perspective
                list_fields = [pe_label,
                               response_type,
                               "human_resource_id",
                               date_due,
                               "start_date",
                               "hours",
                               "status_id",
                               ]

                if response_themes_details:
                    list_fields[2:2] = [(T("Themes"), "dvr_response_action_theme.id")]
                else:
                    list_fields[2:2] = ["response_theme_ids", "comments"]

                if ui_options_get("response_themes_optional"):
                    # Show person_id (read-only)
                    field = table.person_id
                    field.represent =  s3db.pr_PersonRepresent(show_link = True)
                    field.readable = True
                    field.writable = False
                    list_fields.insert(1, (T("Case"), "person_id"))

                    # Hide activity_id
                    field = table.case_activity_id
                    field.readable = field.writable = False
                else:
                    # Hide person_id
                    field = table.person_id
                    field.readable = field.writable = False

                    # Show activity_id (read-only)
                    field = table.case_activity_id
                    field.label = T("Case")
                    field.represent = s3db.dvr_CaseActivityRepresent(
                                                show_as = "beneficiary",
                                                fmt = "%(last_name)s, %(first_name)s",
                                                show_link = True,
                                                )
                    field.readable = True
                    field.writable = False
                    list_fields.insert(1, "case_activity_id")

                s3db.configure("dvr_response_action",
                               list_fields = list_fields,
                               )

                # Custom Filter Options
                if r.interactive:
                    from s3 import S3AgeFilter, \
                                   S3DateFilter, \
                                   S3HierarchyFilter, \
                                   S3OptionsFilter, \
                                   S3TextFilter, \
                                   s3_get_filter_opts

                    filter_widgets = [
                        S3TextFilter(["person_id$pe_label",
                                      "person_id$first_name",
                                      "person_id$middle_name",
                                      "person_id$last_name",
                                      "comments",
                                      ],
                                     label = T("Search"),
                                     ),
                        S3OptionsFilter("status_id",
                                        options = lambda: \
                                                  s3_get_filter_opts("dvr_response_status",
                                                                     orderby = "workflow_position",
                                                                     ),
                                        cols = 3,
                                        orientation = "rows",
                                        sort = False,
                                        size = None,
                                        translate = True,
                                        ),
                        S3DateFilter("start_date",
                                     hidden = not is_report,
                                     hide_time = not use_time,
                                     ),
                        S3OptionsFilter(
                            "response_theme_ids",
                            header = True,
                            hidden = True,
                            options = lambda: \
                                      s3_get_filter_opts("dvr_response_theme",
                                                         org_filter = True,
                                                         ),
                            ),
                        S3OptionsFilter("person_id$person_details.nationality",
                                        label = T("Client Nationality"),
                                        hidden = True,
                                        ),
                        S3AgeFilter("person_id$date_of_birth",
                                    label = T("Client Age"),
                                    hidden = True,
                                    )
                        ]

                    if use_response_type:
                        filter_widgets.insert(3,
                            S3HierarchyFilter("response_type_id",
                                              hidden = True,
                                              ))
                    if use_due_date:
                        filter_widgets.insert(3,
                            S3DateFilter("date_due",
                                         hidden = is_report,
                                         ))
                    if hr_filter_opts:
                        hr_filter_opts = dict(hr_filter_opts)
                        hr_filter_opts.pop('', None)
                        filter_widgets.insert(2,
                            S3OptionsFilter("human_resource_id",
                                            default = hr_filter_default,
                                            header = True,
                                            options = dict(hr_filter_opts),
                                            ))

                    if multiple_orgs:
                        # Add case organisation filter
                        if org_ids:
                            # Provide the permitted organisations as filter options
                            org_filter_opts = s3db.org_organisation_represent.bulk(
                                                                org_ids,
                                                                show_link = False,
                                                                )
                            org_filter_opts.pop(None, None)
                        else:
                            # Look up from records
                            org_filter_opts = None
                        filter_widgets.insert(1, S3OptionsFilter(org_context,
                                                                 options = org_filter_opts,
                                                                 ))

                    s3db.configure("dvr_response_action",
                                   filter_widgets = filter_widgets,
                                   )


        # Organizer and PDF exports
        if response_themes_details:
            description = [(T("Themes"), "response_action_theme.id"),
                           "human_resource_id",
                           "status_id",
                           ]
        else:
            description = ["response_theme_ids",
                           "comments",
                           "human_resource_id",
                           "status_id",
                           ]

        if r.method == "organize":
            table.end_date.writable = True
        s3db.configure("dvr_response_action",
                       organize = {"title": "person_id",
                                   "description": description,
                                   "color": "status_id",
                                   "colors": s3db.dvr_response_status_colors,
                                   "start": "start_date",
                                   "end": "end_date",
                                   "use_time": use_time,
                                   },
                       pdf_format = "list" if response_themes_details else "table",
                       orderby = "dvr_response_action.start_date desc, dvr_response_action.created_on desc",
                       )

        # Maintain consistent order for multiple response actions
        # on the same day (by enforcing created_on as secondary order criterion)
        field = table.start_date
        field.represent.dt_orderby = response_date_dt_orderby

        # Custom onvalidation
        s3db.add_custom_callback("dvr_response_action",
                                 "onvalidation",
                                 response_action_onvalidation,
                                 )

    settings.customise_dvr_response_action_resource = customise_dvr_response_action_resource

    # -------------------------------------------------------------------------
    def customise_dvr_response_action_controller(**attr):

        s3 = current.response.s3
        s3db = current.s3db

        if "viewing" in current.request.get_vars:
            # Set contacts-method to retain the tab
            s3db.set_method("pr", "person",
                            method = "contacts",
                            action = s3db.pr_Contacts,
                            )

        else:
            settings.base.bigtable = True

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            if not r.id:
                from .stats import PerformanceIndicatorExport
                pitype = get_ui_options().get("response_performance_indicators")
                s3db.set_method("dvr", "response_action",
                                method = "indicators",
                                action = PerformanceIndicatorExport(pitype),
                                )
                export_formats = list(settings.get_ui_export_formats())
                export_formats.append(("indicators.xls",
                                       "fa fa-line-chart",
                                       T("Performance Indicators"),
                                       ))
                s3.formats["indicators.xls"] = r.url(method="indicators")
                settings.ui.export_formats = export_formats
            return result
        s3.prep = custom_prep


        # Custom rheader tabs
        if current.request.controller == "dvr":
            attr = dict(attr)
            attr["rheader"] = drk_dvr_rheader

        return attr

    settings.customise_dvr_response_action_controller = customise_dvr_response_action_controller

    # -------------------------------------------------------------------------
    def customise_dvr_response_theme_resource(r, tablename):

        is_admin = current.auth.s3_has_role("ADMIN")


        if r.tablename == "org_organisation" and r.id:

            s3db = current.s3db

            ttable = s3db.dvr_response_theme

            if is_admin or settings.get_dvr_response_themes_sectors():

                # Limit sector selection to the sectors of the organisation
                stable = s3db.org_sector
                ltable = s3db.org_sector_organisation

                dbset = current.db((ltable.sector_id == stable.id) & \
                                   (ltable.organisation_id == r.id) & \
                                   (ltable.deleted == False))
                field = ttable.sector_id
                field.comment = None
                field.readable = field.writable = True
                field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "org_sector.id",
                                                       field.represent,
                                                       ))

            if is_admin or settings.get_dvr_response_themes_needs():

                # Limit needs selection to the needs of the organisation
                ntable = s3db.dvr_need

                dbset = current.db(ntable.organisation_id == r.id)
                field = ttable.need_id
                field.label = T("Counseling Reason")
                field.comment = None
                field.readable = field.writable = True
                field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "dvr_need.id",
                                                       field.represent,
                                                       ))

        # Custom CRUD Strings
        current.response.s3.crud_strings["dvr_response_theme"] = Storage(
            label_create = T("Create Counseling Theme"),
            title_display = T("Counseling Theme Details"),
            title_list = T("Counseling Themes"),
            title_update = T("Edit Counseling Theme"),
            label_list_button = T("List Counseling Themes"),
            label_delete_button = T("Delete Counseling Theme"),
            msg_record_created = T("Counseling Theme created"),
            msg_record_modified = T("Counseling Theme updated"),
            msg_record_deleted = T("Counseling Theme deleted"),
            msg_list_empty = T("No Counseling Themes currently defined"),
        )

    settings.customise_dvr_response_theme_resource = customise_dvr_response_theme_resource

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
    def customise_dvr_vulnerability_type_resource(r, tablename):

        table = current.s3db.dvr_vulnerability_type

        # Adjust labels
        field = table.name
        field.label = T("Diagnosis")

        # Custom CRUD Strings
        current.response.s3.crud_strings["dvr_vulnerability_type"] = Storage(
            label_create = T("Create Diagnosis"),
            title_display = T("Diagnosis Details"),
            title_list = T("Diagnoses"),
            title_update = T("Edit Diagnosis"),
            label_list_button = T("List Diagnoses"),
            label_delete_button = T("Delete Diagnosis"),
            msg_record_created = T("Diagnosis created"),
            msg_record_modified = T("Diagnosis updated"),
            msg_record_deleted = T("Diagnosis deleted"),
            msg_list_empty = T("No Diagnoses currently defined"),
            )

    settings.customise_dvr_vulnerability_type_resource = customise_dvr_vulnerability_type_resource

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
            field.requires = [IS_NOT_EMPTY(), IS_LENGTH(512, minsize=1)]

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

            if r.component_name == "document":
                s3.crud_strings["doc_document"].label_create = T("Add Document Template")
                # Done in customise_doc_document_resource
                #f = current.s3db.doc_document.url
                #f.readable = f.writable = False
                current.s3db.doc_document.is_template.default = True
                r.resource.add_component_filter("document", FS("is_template") == True)

            return result

        s3.prep = custom_prep

        attr = dict(attr)
        attr["rheader"] = drk_org_rheader

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
        from s3 import S3SQLCustomForm
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
def case_read_multiple_orgs():
    """
        Check if the user has read access to cases of more than one org

        @returns: tuple (multiple_orgs, org_ids)
    """

    realms = current.auth.permission.permitted_realms("dvr_case", "read")
    if realms is None:
        multiple_orgs = True
        org_ids = []
    else:
        otable = current.s3db.org_organisation
        query = (otable.pe_id.belongs(realms)) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.id)
        multiple_orgs = len(rows) > 1
        org_ids = [row.id for row in rows]

    return multiple_orgs, org_ids

# =============================================================================
def drk_cr_rheader(r, tabs=None):
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
def get_protection_themes(person):
    """
        Get response themes of a case that are linked to protection needs

        @param person: the beneficiary record (pr_person Row)

        @returns: list-representation of response themes
    """

    db = current.db
    s3db = current.s3db

    # Get all theme_ids that are linked to protection needs
    ntable = s3db.dvr_need
    ttable = s3db.dvr_response_theme

    query = (ntable.protection == True) & \
            (ntable.id == ttable.need_id) & \
            (ttable.deleted == False)
    themes = db(query).select(ttable.id,
                              cache = s3db.cache,
                              )
    theme_ids = set(theme.id for theme in themes)

    # Find out which of these themes are linked to the person
    rtable = s3db.dvr_response_action
    ltable = s3db.dvr_response_action_theme

    query = (ltable.theme_id.belongs(theme_ids)) & \
            (ltable.action_id == rtable.id) & \
            (ltable.deleted == False) & \
            (rtable.person_id == person.id) & \
            (rtable.deleted == False)
    rows = db(query).select(ltable.theme_id,
                            groupby = ltable.theme_id,
                            )
    theme_list = [row.theme_id for row in rows]

    # Return presented as list
    represent = rtable.response_theme_ids.represent
    return represent(theme_list)

# =============================================================================
def get_total_consultations(person):
    """
        Get number of consultations for person

        @param person: the beneficiary record (pr_person Row)

        @returns: number of consultations
    """

    s3db = current.s3db

    rtable = s3db.dvr_response_action

    ui_options = get_ui_options()
    if ui_options.get("response_types"):
        # Filter by response type
        ttable = s3db.dvr_response_type
        join = ttable.on((ttable.id == rtable.response_type_id) & \
                         (ttable.is_consultation == True))
    else:
        # Count all responses as consultations
        join = None

    query = (rtable.person_id == person.id) & \
            (rtable.deleted == False)
    count = rtable.id.count()

    row = current.db(query).select(count, join=join).first()
    return row[count]

# =============================================================================
def drk_dvr_rheader(r, tabs=None):
    """ DVR custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, \
                   S3ResourceHeader, \
                   s3_fullname

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T
        record_id = record.id

        if tablename == "pr_person":

            # UI Options and ability to read cases from multiple orgs
            ui_opts = get_ui_options()
            ui_opts_get = ui_opts.get
            multiple_orgs = case_read_multiple_orgs()[0]

            if not tabs:
                activity_tab_label = ui_opts_get("activity_tab_label")
                if activity_tab_label:
                    ACTIVITIES = T(activity_tab_label)
                else:
                    ACTIVITIES = T("Counseling Reasons")

                # Basic Case Documentation
                tabs = [(T("Basic Details"), None),
                        (T("Contact Info"), "contacts"),
                        (T("Family Members"), "group_membership/"),
                        (ACTIVITIES, "case_activity"),
                        ]

                # Optional Case Documentation
                if ui_opts_get("case_use_response_tab"):
                    tabs.append((T("Actions"), "response_action"))
                if ui_opts_get("case_use_appointments"):
                    tabs.append((T("Appointments"), "case_appointment"))
                if ui_opts_get("case_use_service_contacts"):
                    tabs.append((T("Service Contacts"), "service_contact"))
                if ui_opts_get("case_use_photos_tab"):
                    tabs.append((T("Photos"), "image"))

                # Uploads
                tabs.append((T("Documents"), "document/"))

                # Notes etc.
                if ui_opts_get("case_use_notes"):
                    tabs.append((T("Notes"), "case_note"))

            # Get the record data
            lodging_opt = ui_opts_get("case_lodging")
            if lodging_opt == "site":
                lodging_sel = "dvr_case.site_id"
                lodging_col = "dvr_case.site_id"
            elif lodging_opt == "text":
                lodging_sel = "case_details.lodging"
                lodging_col = "dvr_case_details.lodging"
            else:
                lodging_sel = None
                lodging_col = None

            if ui_opts_get("case_use_flags"):
                flags_sel = "dvr_case_flag_case.flag_id"
            else:
                flags_sel = None

            if ui_opts_get("case_use_place_of_birth"):
                pob_sel = "person_details.place_of_birth"
            else:
                pob_sel = None

            if ui_opts_get("case_use_bamf"):
                bamf_sel = "bamf.value"
            else:
                bamf_sel = None

            case = resource.select(["first_name",
                                    "last_name",
                                    "dvr_case.status_id",
                                    "dvr_case.archived",
                                    "dvr_case.household_size",
                                    "dvr_case.organisation_id",
                                    "case_details.arrival_date",
                                    bamf_sel,
                                    "person_details.nationality",
                                    pob_sel,
                                    lodging_sel,
                                    flags_sel,
                                    ],
                                    represent = True,
                                    raw_data = True,
                                    ).rows

            if case:
                # Extract case data
                case = case[0]

                name = s3_fullname
                raw = case["_row"]

                case_status = lambda row: case["dvr_case.status_id"]
                archived = raw["dvr_case.archived"]
                organisation = lambda row: case["dvr_case.organisation_id"]
                arrival_date = lambda row: case["dvr_case_details.arrival_date"]
                household_size = lambda row: case["dvr_case.household_size"]
                nationality = lambda row: case["pr_person_details.nationality"]

                # Warn if nationality is lacking while mandatory
                if ui_opts_get("case_nationality_mandatory") and \
                   raw["pr_person_details.nationality"] is None:
                    current.response.warning = T("Nationality lacking!")

                bamf = lambda row: case["pr_bamf_person_tag.value"]

                if pob_sel:
                    place_of_birth = lambda row: case["pr_person_details.place_of_birth"]
                else:
                    place_of_birth = None
                if lodging_col:
                    lodging = (T("Lodging"), lambda row: case[lodging_col])
                else:
                    lodging = None
                if flags_sel:
                    flags = lambda row: case["dvr_case_flag_case.flag_id"]
                else:
                    flags = None
            else:
                # Target record exists, but doesn't match filters
                return None

            arrival_date_label = ui_opts_get("case_arrival_date_label")
            arrival_date_label = T(arrival_date_label) \
                                 if arrival_date_label else T("Date of Entry")

            # Adaptive rheader-fields
            rheader_fields = [[None,
                               (T("Nationality"), nationality),
                               (T("Case Status"), case_status)],
                              [None, None, None],
                              [None, None, None],
                              ]

            if ui_opts_get("case_use_pe_label"):
                rheader_fields[0][0] = (T("ID"), "pe_label")
                rheader_fields[1][0] = "date_of_birth"
            else:
                rheader_fields[0][0] = "date_of_birth"

            if pob_sel:
                pob_row = 1 if rheader_fields[1][0] is None else 2
                rheader_fields[pob_row][0] = (T("Place of Birth"), place_of_birth)

            if bamf_sel:
                doe_row = 2
                rheader_fields[1][1] = (T("BAMF-Az"), bamf)
            else:
                doe_row = 1
            rheader_fields[doe_row][1] = (arrival_date_label, arrival_date)

            if lodging:
                rheader_fields[1][2] = lodging

            if ui_opts_get("case_show_total_consultations"):
                total_consultations = (T("Number of Consultations"), get_total_consultations)
                if rheader_fields[1][2] is None:
                    rheader_fields[1][2] = total_consultations
                else:
                    rheader_fields[0].append(total_consultations)

            hhsize = (T("Size of Family"), household_size)
            if rheader_fields[1][0] is None:
                rheader_fields[1][0] = hhsize
            elif rheader_fields[2][0] is None:
                rheader_fields[2][0] = hhsize
            elif rheader_fields[1][2] is None:
                rheader_fields[1][2] = hhsize
            else:
                rheader_fields[2][2] = hhsize

            colspan = 5

            if multiple_orgs:
                # Show organisation if user can see cases from multiple orgs
                rheader_fields.insert(0, [(T("Organisation"), organisation, colspan)])
            if flags_sel:
                rheader_fields.append([(T("Flags"), flags, colspan)])
            if ui_opts_get("case_header_protection_themes"):
                rheader_fields.append([(T("Protection Need"),
                                        get_protection_themes,
                                        colspan,
                                        )])
            if archived:
                # "Case Archived" hint
                hint = lambda record: SPAN(T("Invalid Case"), _class="invalid-case")
                rheader_fields.insert(0, [(None, hint)])

            # Generate rheader XML
            rheader = S3ResourceHeader(rheader_fields, tabs, title=name)(
                            r,
                            table = resource.table,
                            record = record,
                            )

            # Add profile picture
            from s3 import s3_avatar_represent
            rheader.insert(0, A(s3_avatar_represent(record_id,
                                                    "pr_person",
                                                    _class = "rheader-avatar",
                                                    _width = 60,
                                                    _height = 60,
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
def drk_org_rheader(r, tabs=None):
    """ ORG custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, s3_rheader_tabs, S3ResourceHeader

    s3db = current.s3db

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T
        record_id = record.id

        ui_options = get_ui_options()
        is_admin = current.auth.s3_has_role("ADMIN")

        if tablename == "org_organisation":

            table = resource.table

            if record.root_organisation == record_id:
                branch = False
            else:
                branch = True

            # Custom tabs
            tabs = [(T("Basic Details"), None),
                    (T("Branches"), "branch"),
                    (T("Facilities"), "facility"),
                    (T("Staff & Volunteers"), "human_resource"),
                    #(T("Projects"), "project"),
                    (T("Counseling Themes"), "response_theme"),
                    ]

            if is_admin or ui_options.get("response_themes_needs"):
                # Ability to manage org-specific need types
                # as they are used in themes:
                tabs.append((T("Counseling Reasons"), "need"))

            if not branch and \
               (is_admin or \
                ui_options.get("case_document_templates") and \
                current.auth.s3_has_role("ORG_ADMIN")):
                tabs.append((T("Document Templates"), "document"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            # Custom header
            from gluon import TABLE, TR, TH, TD
            rheader = DIV()

            # Name
            record_data = TABLE(TR(TH("%s: " % table.name.label),
                                   record.name,
                                   ),
                                )

            # Parent Organisation
            if branch:
                btable = s3db.org_organisation_branch
                query = (btable.branch_id == record_id) & \
                        (btable.organisation_id == table.id)
                row = current.db(query).select(table.id,
                                               table.name,
                                               limitby = (0, 1),
                                               ).first()
                if row:
                    record_data.append(TR(TH("%s: " % T("Branch of")),
                                          A(row.name, _href=URL(args=[row.id, "read"])),
                                          ))

            # Website as link
            if record.website:
                record_data.append(TR(TH("%s: " % table.website.label),
                                      A(record.website, _href=record.website)))

            logo = s3db.org_organisation_logo(record)
            if logo:
                rheader.append(TABLE(TR(TD(logo),
                                        TD(record_data),
                                        )))
            else:
                rheader.append(record_data)

            rheader.append(rheader_tabs)
            return rheader

        elif tablename == "org_facility":

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
def drk_anonymous_address(record_id, field, value):
    """
        Helper to anonymize a pr_address location; removes street and
        postcode details, but retains Lx ancestry for statistics

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the location_id
    """

    s3db = current.s3db
    db = current.db

    # Get the location
    if value:
        ltable = s3db.gis_location
        row = db(ltable.id == value).select(ltable.id,
                                            ltable.level,
                                            limitby = (0, 1),
                                            ).first()
        if not row.level:
            # Specific location => remove address details
            data = {"addr_street": None,
                    "addr_postcode": None,
                    "gis_feature_type": 0,
                    "lat": None,
                    "lon": None,
                    "wkt": None,
                    }
            # Doesn't work - PyDAL doesn't detect the None value:
            #if "the_geom" in ltable.fields:
            #    data["the_geom"] = None
            row.update_record(**data)
            if "the_geom" in ltable.fields:
                db.executesql("UPDATE gis_location SET the_geom=NULL WHERE id=%s" % row.id)

    return value

# -----------------------------------------------------------------------------
def drk_obscure_dob(record_id, field, value):
    """
        Helper to obscure a date of birth; maps to the first day of
        the quarter, thus retaining the approximate age for statistics

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the new date
    """

    if value:
        month = int((value.month - 1) / 3) * 3 + 1
        value = value.replace(month=month, day=1)

    return value

# -----------------------------------------------------------------------------
def drk_person_anonymize():
    """ Rules to anonymize a case file """

    ANONYMOUS = "-"

    # Helper to produce an anonymous ID (pe_label)
    anonymous_id = lambda record_id, f, v: "NN%06d" % long(record_id)

    # General rule for attachments
    documents = ("doc_document", {"key": "doc_id",
                                  "match": "doc_id",
                                  "fields": {"name": ("set", ANONYMOUS),
                                             "file": "remove",
                                             "comments": "remove",
                                             },
                                  "delete": True,
                                  })

    # Cascade rule for case activities
    activity_details = [("dvr_response_action", {"key": "case_activity_id",
                                                 "match": "id",
                                                 "fields": {"comments": "remove",
                                                            },
                                               }),
                        ("dvr_case_activity_need", {"key": "case_activity_id",
                                                    "match": "id",
                                                    "fields": {"comments": "remove",
                                                               },
                                                  }),
                        ("dvr_case_activity_update", {"key": "case_activity_id",
                                                      "match": "id",
                                                      "fields": {"comments": ("set", ANONYMOUS),
                                                                 },
                                                      }),
                        ]

    rules = [# Remove identity of beneficiary
             {"name": "default",
              "title": "Names, IDs, Reference Numbers, Contact Information, Addresses",
              "fields": {"first_name": ("set", ANONYMOUS),
                         "last_name": ("set", ANONYMOUS),
                         "pe_label": anonymous_id,
                         "date_of_birth": drk_obscure_dob,
                         "comments": "remove",
                         },
              "cascade": [("dvr_case", {"key": "person_id",
                                        "match": "id",
                                        "fields": {"comments": "remove",
                                                   },
                                        }),
                          ("dvr_case_details", {"key": "person_id",
                                                "match": "id",
                                                "fields": {"lodging": "remove",
                                                           },
                                                }),
                          ("pr_contact", {"key": "pe_id",
                                          "match": "pe_id",
                                          "fields": {"contact_description": "remove",
                                                     "value": ("set", ""),
                                                     "comments": "remove",
                                                     },
                                          "delete": True,
                                          }),
                          ("pr_contact_emergency", {"key": "pe_id",
                                                    "match": "pe_id",
                                                    "fields": {"name": ("set", ANONYMOUS),
                                                               "relationship": "remove",
                                                               "phone": "remove",
                                                               "comments": "remove",
                                                               },
                                                    "delete": True,
                                                    }),
                          ("pr_address", {"key": "pe_id",
                                          "match": "pe_id",
                                          "fields": {"location_id": drk_anonymous_address,
                                                     "comments": "remove",
                                                     },
                                          }),
                          ("pr_person_details", {"key": "person_id",
                                                 "match": "id",
                                                 "fields": {"education": "remove",
                                                            "occupation": "remove",
                                                            },
                                                 }),
                          ("pr_person_tag", {"key": "person_id",
                                             "match": "id",
                                             "fields": {"value": ("set", ANONYMOUS),
                                                        },
                                             "delete": True,
                                             }),
                          ("dvr_residence_status", {"key": "person_id",
                                                    "match": "id",
                                                    "fields": {"reference": ("set", ANONYMOUS),
                                                               "comments": "remove",
                                                               },
                                                    }),
                          ("dvr_service_contact", {"key": "person_id",
                                                   "match": "id",
                                                   "fields": {"reference": "remove",
                                                              "contact": "remove",
                                                              "phone": "remove",
                                                              "email": "remove",
                                                              "comments": "remove",
                                                              },
                                                   }),
                          ],
              },

             # Remove activity details, appointments and notes
             {"name": "activities",
              "title": "Activity Details, Appointments, Notes",
              "cascade": [("dvr_case_activity", {"key": "person_id",
                                                 "match": "id",
                                                 "fields": {"subject": ("set", ANONYMOUS),
                                                            "need_details": "remove",
                                                            "outcome": "remove",
                                                            "comments": "remove",
                                                            },
                                                 "cascade": activity_details,
                                                 }),
                          ("dvr_case_appointment", {"key": "person_id",
                                                    "match": "id",
                                                    "fields": {"comments": "remove",
                                                               },
                                                    }),
                          ("dvr_case_language", {"key": "person_id",
                                                 "match": "id",
                                                 "fields": {"comments": "remove",
                                                            },
                                                  }),
                          ("dvr_note", {"key": "person_id",
                                        "match": "id",
                                        "fields": {"note": "remove",
                                                   },
                                        "delete": True,
                                        }),
                          ],
              },

             # Remove photos and attachments
             {"name": "documents",
              "title": "Photos and Documents",
              "cascade": [("dvr_case", {"key": "person_id",
                                        "match": "id",
                                        "cascade": [documents,
                                                    ],
                                        }),
                          ("dvr_case_activity", {"key": "person_id",
                                                 "match": "id",
                                                 "cascade": [documents,
                                                             ],
                                                 }),
                          ("pr_image", {"key": "pe_id",
                                        "match": "pe_id",
                                        "fields": {"image": "remove",
                                                   "url": "remove",
                                                   "description": "remove",
                                                   },
                                        "delete": True,
                                        }),
                          ],
              },

              # TODO family membership

             ]

    return rules

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
