# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

SAVE = "Save the Children"

def config(settings):
    """
        Template settings for Save the Children Philippines
    """

    T = current.T

    settings.base.system_name = T("IMS")
    settings.base.system_name_short = T("IMS")

    # PrePopulate data
    #settings.base.prepopulate = ("skeleton", "default/users")
    settings.base.prepopulate += ("SCPHIMS", "SCPHIMS/Demo", "default/users")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SCPHIMS"
    settings.ui.menu_logo = "/%s/static/themes/SCPHIMS/img/logo.png" % current.request.application

    # Authentication settings
    # Users use their existing SC accounts
    settings.security.self_registration = False

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("PH",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True
    settings.gis.lookup_code = "PSGC"

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
    #    ("ar", "العربية"),
    #    ("bs", "Bosanski"),
        ("en", "English"),
    #    ("fr", "Français"),
    #    ("de", "Deutsch"),
    #    ("el", "ελληνικά"),
    #    ("es", "Español"),
    #    ("it", "Italiano"),
    #    ("ja", "日本語"),
    #    ("km", "ភាសាខ្មែរ"),
    #    ("ko", "한국어"),
    #    ("ne", "नेपाली"),          # Nepali
    #    ("prs", "دری"), # Dari
    #    ("ps", "پښتو"), # Pashto
    #    ("pt", "Português"),
    #    ("pt-br", "Português (Brasil)"),
    #    ("ru", "русский"),
    #    ("tet", "Tetum"),
    #    ("tl", "Tagalog"),
    #    ("tr", "Türkçe"),
    #    ("ur", "اردو"),
    #    ("vi", "Tiếng Việt"),
    #    ("zh-cn", "中文 (简体)"),
    #    ("zh-tw", "中文 (繁體)"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0800"
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
        "PHP" : "Philippine Pesos",
        "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "PHP"

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

    settings.security.policy = 5 # Controller, Function & Table ACLs

    # =========================================================================
    # Login
    #

    settings.auth.password_changes = False
    settings.auth.office365_domains = ["savethechildren.org"]

    #settings.mail.sender = "'IMS' <ims.ph@savethechildren.org>"
    #settings.mail.server = "smtp.office365.com:587"
    #settings.mail.tls = True
    #settings.mail.login = "username:password"

    # =========================================================================
    # Mobile
    #

    settings.mobile.forms = [("Beneficiaries", "pr_person", {"c": "dvr",
                                                             }),
                             # Done via the Answer resource, which is exposed through Dynamic Tables
                             #("Rapid Assessments", "dc_response", {"c": "dc",
                             #                                      "f": "respnse",
                             #                                      }),
                             ]

    # =========================================================================
    # CMS
    #

    settings.cms.richtext = True

    # -------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            if r.method == "calendar":
                # Only show entries related to Activities & Assessments
                from s3 import FS
                r.resource.add_filter(FS("post_module.module").belongs(("project", "dc")))

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller

    # =========================================================================
    # Data Collection
    #

    # Download Assessments - as these have been created through Targetting
    settings.dc.mobile_data = True

    def dc_target_onaccept(form):
        """
            Add/Update entry to calendar
        """

        # Deletion and update have a different format
        try:
            target_id = form.vars.id
            delete = False
        except:
            target_id = form.id
            delete = True

        # Add/Update Calendar entry
        db = current.db
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        query = (ltable.module == "dc") & \
                (ltable.resource == "target") & \
                (ltable.record == target_id)
        link = db(query).select(ltable.post_id,
                                limitby = (0, 1),
                                ).first()
        if delete:
            if link:
                db(table.id == link.post_id).delete()
        else:
            # Retrieve the full record
            ttable = db.dc_target
            record = db(ttable.id == target_id).select(ttable.template_id,
                                                       ttable.location_id,
                                                       ttable.date,
                                                       limitby = (0, 1),
                                                       ).first()
            body = ttable.template_id.represent(record.template_id)
            if link:
                # Update it
                db(table.id == link.post_id).update(body = body,
                                                    location_id = record.location_id,
                                                    date = record.date,
                                                    )
            else:
                # Create it
                post_id = table.insert(body = body,
                                       location_id = record.location_id,
                                       date = record.date,
                                       )
                ltable.insert(post_id = post_id,
                              module = "dc",
                              resource = "target",
                              record = target_id,
                              )

    # -------------------------------------------------------------------------
    def customise_dc_target_resource(r, tablename):

        s3db = current.s3db
        table = s3db.dc_target

        # Always at L3
        from s3 import S3LocationSelector
        table.location_id.widget = S3LocationSelector(levels = ("L1", "L2", "L3"),
                                                      show_map = False,
                                                      )

        has_role = current.auth.s3_has_role
        if has_role("ERT_LEADER") or has_role("HUM_MANAGER"):
            # Default to the Rapid Assessment Form
            s3db = current.s3db
            ttable = s3db.dc_template
            RAPID = current.db(ttable.name == "Rapid Assessment").select(ttable.id,
                                                                         cache = s3db.cache,
                                                                         limitby = (0, 1)
                                                                         ).first()
            try:
                table.template_id.default = RAPID.id
            except:
                # Prepop not done
                current.log.warning("Cannot default Targets to Rapid Assessment form")

        # If we have default ones defined then need to add them in a cascade:
        #onaccept = s3db.get_config("dc_target", "onaccept")
        #ondelete = s3db.get_config("dc_target", "ondelete")
        onaccept = dc_target_onaccept
        
        s3db.configure("dc_target",
                       onaccept = onaccept,
                       ondelete = onaccept,
                       )

    settings.customise_dc_target_resource = customise_dc_target_resource

    # -------------------------------------------------------------------------
    def customise_dc_target_controller(**attr):

        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            if not r.component:
                # When creating Targets from Assessments module, include the Event field
                from s3 import S3SQLCustomForm, S3SQLInlineLink
                crud_form = S3SQLCustomForm(S3SQLInlineLink("event",
                                                            label = T("Disaster"),
                                                            field = "event_id",
                                                            multiple = False,
                                                            ),
                                            "template_id",
                                            "date",
                                            "location_id",
                                            "comments",
                                            )

                current.s3db.configure("dc_target",
                                       crud_form = crud_form,
                                       )
            elif r.component_name == "response":
                # Don't start anseering Assessment when creating them here
                current.s3db.configure("dc_response",
                                       create_next = None,
                                       )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_dc_target_controller = customise_dc_target_controller

    # -------------------------------------------------------------------------
    def customise_dc_response_resource(r, tablename):

        # @ToDo: Filters inc 'Assigned to me'

        db = current.db
        s3db = current.s3db
        table = s3db.dc_response

        f = table.person_id
        f.label = T("Name of team leader")
        # Filter to just Staff
        from gluon import IS_EMPTY_OR
        from s3 import IS_ONE_OF
        ptable = s3db.pr_person
        htable = s3db.hrm_human_resource
        set = db(ptable.id == htable.person_id)
        f.requires = IS_EMPTY_OR(IS_ONE_OF(set, "pr_person.id",
                                           f.represent,
                                           orderby = "pr_person.first_name",
                                           sort = True,
                                           ))
        f.widget = None
        # @ToDo: have this create Staff, not just Person (Allow hrm/person/create with embedded Staff details?)
        from s3layouts import S3PopupLink
        f.comment = S3PopupLink(c = "pr",
                                f = "person",
                                label = T("Create Person"),
                                vars = {"child": "person_id"},
                                )
                                      
        # Always at L4
        from s3 import S3LocationSelector
        table.location_id.widget = S3LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                                      show_map = False,
                                                      )

        # Always SC
        otable = s3db.org_organisation
        org = db(otable.name == SAVE).select(otable.id,
                                             cache = s3db.cache,
                                             limitby = (0, 1)
                                             ).first()
        try:
            SCI = org.id
        except:
            current.log.error("Cannot find org %s - prepop not done?" % SAVE)
        else:
            f = table.organisation_id
            f.default = SCI
            f.readable = f.writable = False 

        has_role = current.auth.s3_has_role
        ttable = s3db.dc_template
        if has_role("ERT_LEADER") or has_role("HUM_MANAGER"):
            # Default to the Rapid Assessment Form
            RAPID = db(ttable.name == "Rapid Assessment").select(ttable.id,
                                                                 cache = s3db.cache,
                                                                 limitby = (0, 1)
                                                                 ).first()
            try:
                table.template_id.default = RAPID.id
            except:
                # Prepop not done
                current.log.warning("Cannot default Targets to Rapid Assessment form")

        def update_onaccept(form):
            form_vars = form.vars
            response_id = form_vars["id"]
            person_id = form_vars.get("person_id")
            if not person_id:
                record = db(table.id == response_id).select(table.person_id,
                                                            limitby = (0, 1)
                                                            ).first()
                person_id = record.person_id
            if person_id:
                # See if there is a user associated with it
                user_id = current.auth.s3_get_user_id(person_id)
                if user_id:
                    # Set correct owned_by_user
                    db(table.id == response_id).update(owned_by_user = user_id)
                    # Also update the Answer
                    dtable = s3db.s3_table
                    ttable = s3db.dc_template
                    query = (table.id == response_id) & \
                            (table.template_id == ttable.id) & \
                            (ttable.table_id == dtable.id)
                    template = db(query).select(dtable.name,
                                                limitby=(0, 1),
                                                ).first()
                    dtablename = template.name
                    db(s3db[dtablename].response_id == response_id).update(owned_by_user = user_id)

        def create_onaccept(form):
            form_vars = form.vars
            response_id = form_vars["id"]
            person_id = form_vars.get("person_id")
            if not person_id:
                record = db(table.id == response_id).select(table.person_id,
                                                            limitby = (0, 1)
                                                            ).first()
                person_id = record.person_id
            if person_id:
                # See if there is a user associated with it
                user_id = current.auth.s3_get_user_id(person_id)
                if user_id:
                    # Set correct owned_by_user
                    db(table.id == response_id).update(owned_by_user = user_id)
            else:
                user_id = None
            # Create the Answer (ERT Members don't have CREATE permissions)
            dtable = s3db.s3_table
            ttable = s3db.dc_template
            query = (table.id == response_id) & \
                    (table.template_id == ttable.id) & \
                    (ttable.table_id == dtable.id)
            template = db(query).select(dtable.name,
                                        limitby=(0, 1),
                                        ).first()
            dtablename = template.name
            s3db[dtablename].insert(response_id = response_id,
                                    owned_by_user = user_id,
                                    )

        s3db.configure("dc_response",
                       create_onaccept = create_onaccept,
                       update_onaccept = update_onaccept,
                       )

    settings.customise_dc_response_resource = customise_dc_response_resource

    # -------------------------------------------------------------------------
    def customise_dc_response_controller(**attr):

        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            # rheader represents should be clickable
            from gluon import URL
            s3db = current.s3db
            s3db.dc_response.person_id.represent = s3db.pr_PersonRepresent(linkto=URL(c="hrm", f="person", args=["[id]"]),
                                                                           show_link = True,
                                                                           )
            if not r.component:
                # When creating Assessments from Assessments module, include the Event field
                from s3 import S3SQLCustomForm, S3SQLInlineLink
                crud_form = S3SQLCustomForm(S3SQLInlineLink("event",
                                                            label = T("Disaster"),
                                                            field = "event_id",
                                                            multiple = False,
                                                            ),
                                            "template_id",
                                            "date",
                                            "location_id",
                                            "person_id",
                                            "comments",
                                            )

                s3db.configure("dc_response",
                               crud_form = crud_form,
                               )

            elif r.component_name == "answer":
                current.s3db.event_event.start_date.label = T("Date the Event Occurred")

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_dc_response_controller = customise_dc_response_controller

    # =========================================================================
    # Documents
    #

    def customise_doc_document_resource(r, tablename):

        from s3 import S3LocationSelector, S3SQLCustomForm#, S3SQLInlineComponent

        s3db = current.s3db
        table = s3db.doc_document
        table.organisation_id.readable = table.organisation_id.writable = True
        f = table.location_id
        f.readable = f.writable = True
        f.widget = S3LocationSelector() # No Street Address

        s3db.add_components("doc_document",
                            event_event = "doc_id",
                            )

        crud_form = S3SQLCustomForm("file",
                                    "name",
                                    "url",
                                    "date",
                                    # @ToDo: Have this as an event_id dropdown
                                    #S3SQLInlineComponent("event"),
                                    "organisation_id",
                                    "location_id",
                                    "comments",
                                    )

        # Custom filters
        from s3 import S3DateFilter, \
                       S3LocationFilter, \
                       S3OptionsFilter, \
                       S3TextFilter

        filter_widgets = [
            S3TextFilter(["name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("Search by disaster name or comments. You can use * as wildcard."),
                         ),
            S3OptionsFilter("event.name",
                            label = T("Disaster"),
                            ),
            S3LocationFilter("location_id"),
            S3OptionsFilter("organisation_id"),
            S3DateFilter("date"),
            ]

        list_fields = ["location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]
        if r.controller == "doc":
            list_fields += ((T("Disaster"), "event.name"),
                           "organisation_id",
                            )
        elif r.controller == "event":
            list_fields.append("organisation_id")
        list_fields += ["date",
                        "name",
                        ]

        s3db.configure("doc_document",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_doc_document_resource = customise_doc_document_resource

    # -------------------------------------------------------------------------
    def customise_doc_image_resource(r, tablename):

        from s3 import S3LocationSelector, S3SQLCustomForm#, S3SQLInlineComponent

        s3db = current.s3db
        table = s3db.doc_image
        table.location_id.widget = S3LocationSelector() # No Street Address

        s3db.add_components("doc_image",
                            event_event = "doc_id",
                            )

        crud_form = S3SQLCustomForm("file",
                                    "name",
                                    "url",
                                    "date",
                                    # @ToDo: Have this as an event_id dropdown...defaulting to currently-open Event
                                    #S3SQLInlineComponent("event"),
                                    "organisation_id",
                                    "location_id",
                                    "comments",
                                    )

        # Custom filters
        from s3 import S3DateFilter, \
                       S3LocationFilter, \
                       S3OptionsFilter, \
                       S3TextFilter

        filter_widgets = [
            S3TextFilter(["name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("Search by disaster name or comments. You can use * as wildcard."),
                         ),
            S3OptionsFilter("event.name",
                            label = T("Disaster"),
                            ),
            S3LocationFilter("location_id"),
            S3OptionsFilter("organisation_id"),
            S3DateFilter("date"),
            ]

        list_fields = ["location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]
        if r.controller != "event":
            list_fields.append((T("Disaster"), "event.name"))
        list_fields += ["organisation_id",
                        "date",
                        "name",
                        ]

        s3db.configure("doc_image",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_doc_image_resource = customise_doc_image_resource

    # -------------------------------------------------------------------------
    def customise_doc_sitrep_resource(r, tablename):
        """
            All SitReps are SAVE
            All SitReps are National in scope
        """

        #if not current.auth.s3_has_role("AUTHENTICATED"):
        #    # @ToDo: Just show the External (Public) parts
        #    pass

        from s3 import S3DateFilter, S3OptionsFilter, S3SQLCustomForm, S3SQLInlineComponent

        db = current.db
        s3db = current.s3db
        table = s3db.doc_sitrep

        # Always SC
        otable = s3db.org_organisation
        org = db(otable.name == SAVE).select(otable.id,
                                             cache = s3db.cache,
                                             limitby = (0, 1)
                                             ).first()
        try:
            SCI = org.id
        except:
            current.log.error("Cannot find org %s - prepop not done?" % SAVE)
        else:
            f = table.organisation_id
            f.default = SCI

        # Always National
        PH = "Philippines"
        gtable = s3db.gis_location
        loc = db((gtable.name == PH) & (gtable.level == "L0")).select(gtable.id,
                                                                      cache = s3db.cache,
                                                                      limitby = (0, 1)
                                                                      ).first()
        try:
            PH = loc.id
        except:
            current.log.error("Cannot find loc %s - prepop not done?" % PH)
        else:
            f = table.location_id
            f.default = PH

        # Default to currently-open Event (if just 1)
        s3db.event_sitrep.event_id.default = current.session.s3.event

        crud_form = S3SQLCustomForm(S3SQLInlineComponent("event_sitrep",
                                                         label = T("Disaster"),
                                                         fields = [("", "event_id")],
                                                         multiple = False,
                                                         required = True,
                                                         ),
                                    "date",
                                    "name",
                                    "description",
                                    "comments",
                                    )

        filter_widgets = [S3OptionsFilter("event_sitrep.event_id"),
                          S3DateFilter("date"),
                          ]

        list_fields = ["event_sitrep.event_id",
                       "date",
                       "name",
                       "comments",
                       ]

        s3db.configure("doc_sitrep",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_doc_sitrep_resource = customise_doc_sitrep_resource

    # -------------------------------------------------------------------------
    def customise_doc_sitrep_controller(**attr):

        # Default Filter: Only open Events
        etable = current.s3db.event_event
        query = (etable.closed == False) & \
                (etable.deleted == False)
        open = current.db(query).select(etable.id,
                                        etable.name,
                                        )
        len_open = len(open)
        if len_open:
            if len_open == 1:
                current.session.s3.event = open.first().id
            else:
                current.session.s3.event = None
            open = {row.id: row.name for row in open}

            from s3 import s3_set_default_filter
            s3_set_default_filter("event_sitrep.event_id",
                                  open,
                                  tablename = "doc_sitrep")

        return attr

    settings.customise_doc_sitrep_controller = customise_doc_sitrep_controller

    # =========================================================================
    # Beneficiaries
    #
    settings.dvr.label = "Beneficiary"
    settings.hrm.email_required = False

    # -------------------------------------------------------------------------
    def customise_dvr_case_resource(r, tablename):

        current.s3db.configure("dvr_case",
                               list_fields = ["person_id",
                                              "reference",
                                              "person_id$location_id",
                                              (T("Phone"), "person_id$phone.value"),
                                              "comments",
                                              ],
                               )

    settings.customise_dvr_case_resource = customise_dvr_case_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        if r.function not in ("activity", "distribution"):
            return

        # Beneficiaries
        if r.tablename == "project_activity":
            activity_id = r.id
        else:
            activity_id = None

        # CRUD Strings
        current.response.s3.crud_strings["pr_person"] = Storage(
            label_create = T("Add Beneficiary"),
            title_display = T("Beneficiary Details"),
            title_list = T("Beneficiaries"),
            title_update = T("Edit Beneficiary"),
            title_report = T("Beneficiary Report"),
            label_list_button = T("List Beneficiaries"),
            msg_record_created = T("Beneficiary Added"),
            msg_record_modified = T("Beneficiary Updated"),
            msg_record_deleted = T("Beneficiary Deleted"),
            msg_list_empty = T("No Beneficiaries Found")
        )

        s3db = current.s3db

        mobile_list_fields = [# No need for Mobile client to know which Activity a Case is linked to
                              #"activity_person.activity_id$name",
                              #"dvr_case.reference", # Will always be empty in download
                              #"dvr_case.date", # We don't need this in the mobile form
                              "first_name",
                              "middle_name",
                              "last_name",
                              "date_of_birth",
                              "gender",
                              "person_details.disabled",
                              "phone.value",
                              #"email.value",
                              # @ToDo: Use just parent in Mobile LocationSelector
                              #"address.location_id$L1",
                              #"address.location_id$L2",
                              #"address.location_id$L3",
                              #"address.location_id$L4",
                              "address.location_id$parent",
                              # @ToDo: Workaround needed to avoid double-join of gis_location (e.g. VF?)
                              #"address.location_id$parent$uuid",
                              "address.location_id$addr_street",
                              "household_member.age",
                              "household_member.gender",
                              "household_member.disabled",
                              "household_member.comments",
                              "dvr_case.comments",
                              ]

        from s3 import S3SQLCustomForm, S3SQLInlineComponent
        crud_fields = [#"dvr_case.reference",
                       #"dvr_case.date",
                       "first_name",
                       "middle_name",
                       "last_name",
                       "date_of_birth",
                       "gender",
                       "person_details.disabled",
                       S3SQLInlineComponent(
                            "phone",
                            fields = [("", "value"),
                                      ],
                            #filterby = {"field": "contact_method",
                            #            "options": "SMS",
                            #            },
                            label = T("Mobile Phone"),
                            multiple = True, # Commonly have up to 3!
                            #name = "phone",
                            ),
                       #S3SQLInlineComponent(
                       #     "email",
                       #     fields = [("", "value"),
                       #               ],
                       #     #filterby = {"field": "contact_method",
                       #     #            "options": "EMAIL",
                       #     #            },
                       #     label = T("Email"),
                       #     multiple = False,
                       #     #name = "email",
                       #     ),
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
                            "household_member",
                            fields = ["age",
                                      "gender",
                                      "disabled",
                                      "comments",
                                      ],
                            label = T("Household Members"),
                            ),
                       "dvr_case.comments",
                       ]

        if r.representation == "mdata":
            # @ToDo: Scan this in from barcode on preprinted card
            crud_fields.insert(0, "dvr_case.reference")
        else:
            db = current.db
            atable = s3db.pr_address
            ctable = s3db.dvr_case
            otable = s3db.org_organisation
            org = db(otable.name == SAVE).select(otable.id,
                                                 cache = s3db.cache,
                                                 limitby = (0, 1),
                                                 ).first()
            try:
                SCI = org.id
            except:
                current.log.error("Cannot find org %s - prepop not done?" % SAVE)
            else:
                ctable.organisation_id.default = SCI

            if activity_id:
                patable = s3db.project_activity
                gtable = s3db.gis_location
                query = (patable.id == activity_id) & \
                        (patable.location_id == gtable.id)
                activity = db(query).select(gtable.parent,
                                            cache = s3db.cache,
                                            limitby = (0, 1),
                                            ).first()
                try:
                    atable.location_id.default = activity.parent
                except AttributeError:
                    current.log.error("Cannot find Activity %s" % activity_id)
            from s3 import S3LocationSelector
            atable.location_id.widget = S3LocationSelector(show_address = True,
                                                           show_map = False,
                                                           )
            ctable.reference.label = T("Barcode")

            #crud_fields.insert(0, "dvr_case.date")
            if r.method in ("read", "update"):
                crud_fields.insert(0, "dvr_case.reference")
                # @ToDo: Add InlineComponents for Distribution Items to be able to mark as received

        s3db.configure("pr_person",
                       crud_form = S3SQLCustomForm(*crud_fields,
                                                   postprocess = lambda form: pr_person_postprocess(form, activity_id)),
                       list_fields = ["first_name",
                                      "middle_name",
                                      "last_name",
                                      "age",
                                      "gender",
                                      (T("Phone"), "phone.value"),
                                      "address.location_id",
                                      "dvr_case.reference",
                                      "dvr_case.comments",
                                      ],
                       mobile_list_fields = mobile_list_fields,
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def pr_person_postprocess(form, activity_id):
        """
            onaccept for the Custom Form:
            - link Beneficiaries to the Distribution
        """

        person_id = form.vars.get("id")
        current.s3db.project_activity_person.insert(activity_id = activity_id,
                                                    person_id = person_id,
                                                    )

    # -------------------------------------------------------------------------
    def dvr_rheader(r, tabs=[]):

        if r.representation != "html":
            # Resource headers only used in interactive views
            return None

        from s3 import s3_rheader_resource, s3_rheader_tabs

        tablename, record = s3_rheader_resource(r)

        if not record:
            return None

        rheader = None

        if tablename == "pr_person":
            T = current.T
            db = current.db
            s3db = current.s3db

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Household Members"), "household_member"),
                        (T("Activities"), "activity_person"),
                        ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            record_id = record.id
            ctable = s3db.dvr_case
            case = db(ctable.person_id == record_id).select(ctable.reference,
                                                            limitby=(0, 1)
                                                            ).first()
            if case:
                reference = case.reference or current.messages["NONE"]
            else:
                reference = None

            from gluon import A, DIV, TABLE, TR, TH, URL
            from s3 import s3_fullname, s3_avatar_represent

            rheader = DIV(
                        A(s3_avatar_represent(record_id,
                                              "pr_person",
                                              _class="rheader-avatar"),
                          _href=URL(f="person", args=[record_id, "image"],
                                    vars = r.get_vars),
                          ),
                        TABLE(
                            TR(TH("%s: " % T("Name")),
                               s3_fullname(record),
                               TH("%s: " % T("Barcode")),
                               reference,
                               ),
                            TR(TH("%s: " % T("Date of Birth")),
                               "%s" % (record.date_of_birth or T("unknown")),
                               TH("%s: " % T("Gender")),
                               "%s" % s3db.pr_gender_opts.get(record.gender,
                                                              T("unknown"))
                               ),
                            ), rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            if r.controller == "dvr":
                # Beneficiaries are added via their Distributions
                # @ToDo: Exception for Mobile?
                r.resource.configure(insertable = False)

            return True
        s3.prep = custom_prep

        if current.request.controller == "dvr":
            # Custom rheader
            attr["rheader"] = dvr_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    # Events
    #
    settings.event.label = "Disaster"

    def response_locations():
        """
            Called onaccept/ondelete from events & activities
            - calculates which L3 locations have SC activities linked to open events & sets their Sectors tag
        """

        db = current.db
        s3db = current.s3db
        gtable = s3db.gis_location
        ttable = s3db.gis_location_tag
        etable = s3db.event_event
        ltable = s3db.event_activity
        atable = s3db.project_activity
        aotable = s3db.project_activity_organisation
        otable = s3db.org_organisation
        stable = s3db.org_sector
        satable = s3db.project_sector_activity

        # Clear all old Data
        db(ttable.tag == "sectors").delete()

        # Find all (L4) Locations with Activities linked to Open Events
        query = (gtable.id == atable.location_id) & \
                (atable.deleted == False) & \
                (atable.id == aotable.activity_id) & \
                (aotable.organisation_id == otable.id) & \
                (otable.name == SAVE) & \
                (atable.id == ltable.activity_id) & \
                (ltable.event_id == etable.id) & \
                (etable.closed == False) & \
                (etable.deleted == False)
        left = stable.on((stable.id == satable.sector_id) & \
                         (satable.activity_id == atable.id))
        L4s = db(query).select(gtable.parent,
                               stable.name,
                               left = left,
                               )

        # Aggregate these to L3
        L3s = {}
        for L4 in L4s:
            sector = L4["org_sector.name"]
            if sector:
                L3 = L4["gis_location.parent"]
                if L3 in L3s:
                    L3s[L3].append(sector)
                else:
                    L3s[L3] = [sector]

        # Store the Sectors in the DB
        for L3 in L3s:
            ttable.insert(location_id = L3,
                          tag = "sectors",
                          value = ", ".join(set(L3s[L3])),
                          )

    # -------------------------------------------------------------------------
    def customise_event_event_controller(**attr):

        # Default Filter: Only open Events
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.closed",
                              False,
                              tablename = "event_event")

        return attr

    settings.customise_event_event_controller = customise_event_event_controller

    # -------------------------------------------------------------------------
    def customise_event_event_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_INT_IN_RANGE
        from s3 import S3LocationSelector, S3SQLCustomForm, S3SQLInlineComponent
        s3db = current.s3db
        s3db.event_event_location.location_id.widget = \
                                    S3LocationSelector(levels=("L1", "L2"))
        # Cat 1: Extra-ordinary
        # Cat 2: Large
        # Cat 3: Medium
        # Cat 4: Small
        s3db.event_event_tag.value.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, 5))
        crud_form = S3SQLCustomForm("name",
                                    "event_type_id",
                                    "start_date",
                                    S3SQLInlineComponent(
                                        "tag",
                                        fields = [("", "value"),
                                                  ],
                                        filterby = {"field": "tag",
                                                    "options": "category",
                                                    },
                                        label = T("Category"),
                                        multiple = False,
                                        ),
                                    "closed",
                                    "comments",
                                    )

        list_fields = ["name",
                       "event_type_id",
                       "start_date",
                       (T("Category"), "tag.value"),
                       "closed",
                       "comments",
                       ]

        # If we have default ones defined then need to add them in a cascade:
        #onaccept = s3db.get_config("event_event", "onaccept")
        #ondelete = s3db.get_config("event_event", "ondelete")
        onaccept = lambda form: response_locations()
        update_onaccept = s3db.get_config("event_event", "update_onaccept")
        update_onaccept = [update_onaccept, onaccept]
        
        s3db.configure("event_event",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       onaccept = onaccept,
                       ondelete = onaccept,
                       update_onaccept = update_onaccept,
                       )

    settings.customise_event_event_resource = customise_event_event_resource

    # =========================================================================
    # Projects
    #
    settings.project.mode_3w = True
    settings.project.mode_drr = True

    settings.project.activities = True
    settings.project.activity_sectors = True
    settings.project.activity_types = True
    settings.project.codes = True
    settings.project.event_activities = True
    settings.project.event_projects = True
    settings.project.hazards = False
    settings.project.hfa = False
    settings.project.programmes = True
    settings.project.programme_budget = True
    settings.project.sectors = False
    settings.project.themes = False

    settings.project.multiple_organisations = True

    # Custom label for project organisation
    settings.project.organisation_roles = {1: T("Implementing Organization"),
                                           2: T("Partner Organization"),
                                           3: T("Donor"),
                                           }

    # -------------------------------------------------------------------------
    def project_activity_onaccept(form):
        """
            Add/Update entry to calendar
            Update response_locations
        """

        # Deletion and update have a different format
        try:
            activity_id = form.vars.id
            delete = False
        except:
            activity_id = form.id
            delete = True

        # Add/Update Calendar entry
        db = current.db
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        query = (ltable.module == "project") & \
                (ltable.resource == "activity") & \
                (ltable.record == activity_id)
        link = db(query).select(ltable.post_id,
                                limitby = (0, 1),
                                ).first()
        if delete:
            if link:
                db(table.id == link.post_id).delete()
        else:
            # Retrieve the full record
            atable = db.project_activity
            record = db(atable.id == activity_id).select(atable.name,
                                                         atable.location_id,
                                                         atable.date,
                                                         limitby = (0, 1),
                                                         ).first()
            if link:
                # Update it
                db(table.id == link.post_id).update(body = record.name,
                                                    location_id = record.location_id,
                                                    date = record.date,
                                                    )
            else:
                # Create it
                post_id = table.insert(body = record.name,
                                       location_id = record.location_id,
                                       date = record.date,
                                       )
                ltable.insert(post_id = post_id,
                              module = "project",
                              resource = "activity",
                              record = activity_id,
                              )

        # Calculate which L3 locations have SC activities linked to open events & set their Sectors tag
        response_locations()

    # -------------------------------------------------------------------------
    def customise_project_activity_resource(r, tablename):

        s3db = current.s3db
        s3db.gis_location.addr_street.label = T("Precise Location")

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_fields = ["name",
                       "date",
                       "status_id",
                       S3SQLInlineComponent("sector_activity",
                                            label = T("Sectors"),
                                            fields = [("", "sector_id")],
                                            ),
                       S3SQLInlineComponent("activity_activity_type",
                                            label = T("Activity Types"),
                                            fields = [("", "activity_type_id")],
                                            ),
                       "location_id",
                       "comments",
                       ]

        if current.auth.s3_logged_in():
            crud_fields.insert(0, "project_id")

        crud_form = S3SQLCustomForm(*crud_fields)

        list_fields = ["name",
                       "date",
                       "status_id",
                       (T("Sectors"), "sector_activity.sector_id"),
                       (T("Activity Types"), "activity_activity_type.activity_type_id"),
                       (T("Items"), "distribution.parameter_id"),
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       #"comments",
                       ]

        # If we have default ones defined then need to add them in a cascade:
        #onaccept = s3db.get_config("project_activity", "onaccept")
        #ondelete = s3db.get_config("project_activity", "ondelete")
        onaccept = project_activity_onaccept
        
        s3db.configure("project_activity",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       onaccept = onaccept,
                       ondelete = onaccept,
                       )

    settings.customise_project_activity_resource = customise_project_activity_resource

    # -------------------------------------------------------------------------
    def customise_project_activity_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive:
                if r.component_name == "case" and "showadd_btn" in output:
                    # Replace add button with one for the Person perspective
                    from gluon import URL
                    from s3 import S3CRUD
                    output["form"] = None
                    output["showadd_btn"] = None
                    url = URL(c="dvr", f="person",
                              args = "create",
                              vars = {"activity_id": r.id}
                              )
                    add_btn = S3CRUD.crud_button(tablename="dvr_case",
                                                 name="label_create",
                                                 icon="add",
                                                 _id="add-btn",
                                                 _href=url,
                                                 )
                    output["buttons"] = {"add_btn": add_btn}
                elif r.component_name == "person" and \
                     r.function != "distribution":
                    # Only Logs should be editing Beneficiaries
                    s3db.configure("pr_person",
                                   insertable = False,
                                   )

            return output
        s3.postp = custom_postp

        return attr

    # No longer required as we switched case_activity to use person_id not case_id
    #settings.customise_project_activity_controller = customise_project_activity_controller

    # -------------------------------------------------------------------------
    def customise_project_programme_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("name",
                                    (T("Project Code"), "code"),
                                    (T("Master Budget"), "budget"),
                                    "currency",
                                    # @ToDo: Link Programmes to Locations
                                    #S3SQLInlineComponent("location",
                                    #                     label = T("Locations"),
                                    #                     fields = ["location_id"],
                                    #                     ),
                                    # @ToDo: Set Metadata on File: Org, Location, Disaster, Date
                                    S3SQLInlineComponent("document",
                                                         label = T("Response Plan"),
                                                         fields = ["file"],
                                                         multiple = False,
                                                         ),
                                    "comments",
                                    )
        
        current.s3db.configure(tablename,
                               crud_form = crud_form,
                               )

    settings.customise_project_programme_resource = customise_project_programme_resource

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        from s3 import S3LocationSelector, S3Represent, S3TextFilter, S3OptionsFilter, S3LocationFilter

        s3db = current.s3db
        table = s3db.project_project

        table.code.label = "SOF"

        s3db.project_location.location_id.widget = S3LocationSelector(levels = ("L1", "L2", "L3"),
                                                                      show_map = False,
                                                                      )

        # Always SC
        otable = s3db.org_organisation
        org = current.db(otable.name == SAVE).select(otable.id,
                                                     cache = s3db.cache,
                                                     limitby = (0, 1)
                                                     ).first()
        try:
            SCI = org.id
        except:
            current.log.error("Cannot find org %s - prepop not done?" % SAVE)
        else:
            f = table.organisation_id
            f.default = SCI

        org_represent = s3db.org_OrganisationRepresent(acronym=False, show_link=True)
        s3db.project_organisation.organisation_id.represent = org_represent
        try:
            s3db.project_donor_organisation.organisation_id.represent = org_represent
        except:
            # Table not present on Activities tab
            pass

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        # @ToDo: Inherit Locations from Disaster?

        crud_form = S3SQLCustomForm(S3SQLInlineLink("programme",
                                                    label = T("Program"),
                                                    field = "programme_id",
                                                    multiple = False,
                                                    ),
                                    "name",
                                    "code",
                                    "status_id",
                                    "start_date",
                                    "end_date",
                                    "budget",
                                    "currency",
                                    S3SQLInlineComponent("location",
                                                         label = T("Locations"),
                                                         fields = ["location_id"],
                                                         ),
                                    S3SQLInlineComponent("organisation",
                                                         name = "donor",
                                                         label = T("Donor(s)"),
                                                         fields = ["organisation_id"],
                                                         ),
                                    # @ToDo: Set Metadata on File: Org, Location, Disaster, Date
                                    S3SQLInlineComponent("document",
                                                         name = "concept_note",
                                                         label = T("Concept Note"),
                                                         fields = ["file"],
                                                         multiple = False,
                                                         ),
                                    # @ToDo: Be able to retrieve the correct document 
                                    #S3SQLInlineComponent("document",
                                    #                     name = "log_frame",
                                    #                     label = T("Log Frame"),
                                    #                     fields = ["file"],
                                    #                     multiple = False,
                                    #                     ),
                                    "comments",
                                    )

        filter_widgets = [
            S3TextFilter(["name",
                          "code",
                          #"description",
                          ],
                         label = T("Search"),
                         comment = T("Search for a Project by name or code"),
                         ),
            S3OptionsFilter("status_id",
                            label = T("Status"),
                            cols = 3,
                            ),
            S3OptionsFilter("donor.organisation_id",
                            label = T("Donor"),
                            hidden = True,
                            ),
            S3LocationFilter("location.location_id",
                             levels = ("L1", "L2", "L3"),
                             hidden = True,
                             ),
            S3OptionsFilter("programme_project.programme_id",
                            label = T("Program"),
                            hidden = True,
                            ),
            #S3OptionsFilter("sector_project.sector_id",
            #                label = T("Sector"),
            #                location_filter = True,
            #                none = True,
            #                hidden = True,
            #                ),
            ]

        list_fields = ["status_id",
                       "code",
                       "name",
                       (T("Donors"), "donor.organisation_id"),
                       (T("Locations"), "location.location_id"),
                       "start_date",
                       "end_date",
                       "budget",
                       "currency",
                       (T("Program"), "programme.name"),
                       ]

        s3db.configure("project_project",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_project_project_resource = customise_project_project_resource

    # -------------------------------------------------------------------------
    def project_rheader(r, ert=False):

        if ert:
            # Simple header, no Tabs
            from s3 import S3ResourceHeader
            rheader_fields = [["name"],
                              ["code"],
                              [(T("Donors"), "donor.organisation_id")],
                              [(T("Locations"), "location.location_id")],
                              ["start_date"],
                              ["end_date"],
                              ]
            rheader = S3ResourceHeader(rheader_fields, tabs=[])(r)
            return rheader
        else:
            # @ToDo: Remove Implementing Org, Add Donors
            return current.s3db.project_rheader(r)

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        # Default Filter: Only open Projects
        # @ToDo: Fix (not activating for some reason)
        stable = current.s3db.project_status
        active = current.db(stable.name.belongs("Active", "Proposed")).select(stable.id,
                                                                              stable.name,
                                                                              )
        active = {row.id: row.name for row in active}

        from s3 import s3_set_default_filter
        s3_set_default_filter("~.status_id",
                              active,
                              tablename = "project_project")

        has_role = current.auth.s3_has_role
        ERT_LEADER = has_role("ERT_LEADER") and not has_role("ADMIN")

        s3 = current.response.s3
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if ERT_LEADER:
                # Don't open Projects: Open Activities
                from gluon import URL
                from s3 import s3_str
                s3.actions = [dict(label=s3_str(T("Open")),
                                   _class="action-btn",
                                   url=URL(args=["[id]", "activity"])),
                              ]

            return output
        s3.postp = custom_postp

        if ERT_LEADER:
            # Simplified RHeader for Operational Requirements
            attr["rheader"] = lambda r: project_rheader(r, ert=True)
        else:
            # Tweaked RHeader
            attr["rheader"] = lambda r: project_rheader(r, ert=False)

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

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
        ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
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
        #("vol", Storage(
        #    name_nice = T("Volunteers"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
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
            name_nice = T("Distributions"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = 10,
        )),
        ("inv", Storage(
            name_nice = T("Warehouses"),
            #description = "Receiving and Sending Items",
            restricted = True,
            module_type = 4
        )),
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
        #("req", Storage(
        #    name_nice = T("Requests"),
        #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("project", Storage(
            name_nice = T("4W"),
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
        ("hms", Storage(
            name_nice = T("Clinics"),
            #description = "Helps to monitor status of hospitals",
            restricted = True,
            module_type = 10
        )),
        ("dc", Storage(
            name_nice = T("Assessments"),
            restricted = True,
            module_type = 10,
        )),
        ("dvr", Storage(
           name_nice = T("Beneficiaries"),
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
        ("edu", Storage(
            name_nice = T("Schools"),
            #description = "Helps to monitor status of schools",
            restricted = True,
            module_type = 10
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

# END =========================================================================