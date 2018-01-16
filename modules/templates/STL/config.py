# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, DIV, H3, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY, SPAN, URL
from gluon.storage import Storage

from s3 import S3Represent

# Service type names
INDIVIDUAL_SUPPORT = "Individual Support"
MENTAL_HEALTH = "Mental Health"

def config(settings):
    """
        Settings for the SupportToLife deployment in Turkey
    """

    T = current.T

    settings.base.system_name = T("Beneficiary Data Management")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate += ("STL", "default/users", "STL/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "STL"

    # =========================================================================
    # Security/AAA Settings
    #
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    # Uncomment to have Person records owned by the Org they are an HR for
    settings.auth.person_realm_human_resource_site_then_org = True

    settings.auth.admin_sees_organisation = True
    settings.auth.registration_organisation_default = "Support To Life"
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = "staff"

    # Password retrieval disabled
    settings.auth.password_retrieval = False

    # Approval emails get sent to all admins
    #settings.mail.approver = "ADMIN"

    # Security Policy
    settings.security.policy = 7 # Hierarchical realms

    # =========================================================================
    def stl_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        db = current.db
        s3db = current.s3db

        tablename = original_tablename(table)

        realm_entity = 0

        if tablename == "pr_person":

            # Beneficiary records are owned by the organisation
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

        elif tablename in ("pr_person_details",
                           "dvr_case_activity",
                           "dvr_case_details",
                           "dvr_economy",
                           "dvr_evaluation",
                           "dvr_household",
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

        return realm_entity

    settings.auth.realm_entity = stl_realm_entity

    # =========================================================================
    # GIS Settings
    #
    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("TR",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Enable scalability-optimized option lookups in location filters
    settings.gis.location_filter_bigtable_lookups = True

    # =========================================================================
    # L10n Settings
    #
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
        ("ar", "Arabic"),
        ("en", "English"),
        ("tr", "Turkish"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0200"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = ","
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = "."
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True

    # =========================================================================
    # Finance Settings
    #
    settings.fin.currencies = {
        "EUR" : "Euros",
        #"GBP" : "Great British Pounds",
        "TRY" : "Turkish Lira",
        "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "TRY"

    # =========================================================================
    # UI Settings
    #
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["STL", "img", "stl_menu_logo.png"],
                                )

    settings.ui.hierarchy_cascade_option_in_tree = False

    # Increase timeout on AJAX reports (ms)
    settings.ui.report_timeout = 600000 # 10 mins, same as the webserver
    # Disable report auto-submit
    settings.ui.report_auto_submit = 0

    # =========================================================================
    # DVR Case Management
    #
    # Case activities use service types
    settings.dvr.activity_use_service_type = True
    # Case activities use multiple Needs
    settings.dvr.case_activity_needs_multiple = True

    # Needs differentiated by service type, and hierarchical
    settings.dvr.needs_use_service_type = True
    settings.dvr.needs_hierarchical = True

    # Vulnerability types hierarchical ("Protection Assessment")
    settings.dvr.vulnerability_types_hierarchical = True

    # Response types hierarchical ("Interventions Required")
    settings.dvr.response_types_hierarchical = True

    # Set DVR Default Label
    settings.dvr.label = "Beneficiary"

    # Represent project IDs as code
    stl_project_id_represent = S3Represent(lookup = "project_project",
                                           fields = ["code"],
                                           )

    # -------------------------------------------------------------------------
    def customise_dvr_home():
        """ Redirect dvr/index to dvr/person?closed=0 """

        from s3 import s3_redirect_default

        s3_redirect_default(URL(f="person", vars={"closed": "0"}))

    settings.customise_dvr_home = customise_dvr_home

    # -------------------------------------------------------------------------
    def dvr_activity_update_onaccept(form):
        """
            Onaccept of group activity:
                - propagate the service_id to all case activities
                  linked to it
        """

        db = current.db
        s3db = current.s3db

        # Read form data
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        if record_id:

            # Get the service ID
            atable = s3db.dvr_activity
            row = db(atable.id == record_id).select(atable.service_id,
                                                    limitby = (0, 1),
                                                    ).first()
            if row:
                service_id = row.service_id
                if service_id:
                    # Update the service_id of all case activities
                    # linked to this group activity
                    catable = s3db.dvr_case_activity
                    query = (catable.activity_id == record_id) & \
                            (catable.service_id != service_id)
                    db(query).update(service_id = service_id)

        # Also execute standard onaccept, if any
        onaccept = s3db.get_config("dvr_activity", "onaccept")
        if onaccept:
            from gluon.tools import callback
            callback(onaccept, form, tablename="dvr_activity")

    # -------------------------------------------------------------------------
    def customise_dvr_activity_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        T = current.T

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            table = r.table
            crud_strings = s3.crud_strings[r.tablename]

            from s3 import FS, \
                           IS_ONE_OF, \
                           S3DateFilter, \
                           S3HierarchyFilter, \
                           S3HierarchyWidget, \
                           S3OptionsFilter, \
                           S3Represent, \
                           S3SQLCustomForm, \
                           S3SQLInlineComponent, \
                           S3TextFilter, \
                           s3_get_filter_opts

            # Expose organisation_id
            field = table.organisation_id
            field.readable = field.writable = True

            # Organisation is required
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Hierarchical Organisation Selector
            represent = s3db.org_OrganisationRepresent(parent=False)
            field.widget = S3HierarchyWidget(lookup="org_organisation",
                                             represent=represent,
                                             multiple=False,
                                             leafonly=False,
                                             )

            # Context-adapted tool tip
            field.comment = DIV(_class = "tooltip",
                                _title = "%s|%s" % (T("Organisation"),
                                                    T("The organisation/branch managing this activity"),
                                                    ),
                                )

            # Default to user organisation
            user = current.auth.user
            if user:
                field.default = user.organisation_id

            service_type = r.get_vars.get("service_type")
            if service_type == "MH":

                crud_strings["title_list"] = T("MH Group/Family Sessions")

                # Get service type ID
                stable = s3db.org_service
                query = (stable.parent == None) & \
                        (stable.name == MENTAL_HEALTH) & \
                        (stable.deleted != True)
                service = db(query).select(stable.id, limitby=(0, 1)).first()
                root_service_id = service.id if service else None

                # Filter activities
                query = (FS("service_id$root_service") == root_service_id)
                r.resource.add_filter(query)

                # Filter service selector
                field = table.service_id
                field.requires = IS_ONE_OF(db, "org_service.id",
                                           field.represent,
                                           filterby = "root_service",
                                           filter_opts = (root_service_id,),
                                           sort=True,
                                           )
                field.widget = S3HierarchyWidget(multiple = False,
                                                 leafonly = True,
                                                 filter = (FS("root_service") == root_service_id),
                                                 )

                # Adapt label for "facilitator"
                field = table.facilitator
                field.label = T("Counselor")

                # Expose gender type
                field = table.gender
                field.readable = field.writable = True

                # Expose activity focus
                field = table.focus_id
                field.label = T("Focus of Group")
                field.readable = field.writable = True

                # Custom list fields
                list_fields = ["name",
                               "service_id",
                               "start_date",
                               "end_date",
                               (T("Type of Group"), "group_type_id"),
                               "gender",
                               "age_group_id",
                               "site_id",
                               "room_id",
                               "facilitator",
                               ]

                # Custom form
                crud_form = S3SQLCustomForm("name",
                                            "organisation_id",
                                            "service_id",
                                            "start_date",
                                            "end_date",
                                            (T("Type of Group"), "group_type_id"),
                                            "gender",
                                            "age_group_id",
                                            "focus_id",
                                            "site_id",
                                            "room_id",
                                            "facilitator",
                                            "comments",
                                            )

                s3db.configure("dvr_activity",
                               crud_form = crud_form,
                               list_fields = list_fields,
                               )

            elif service_type == "PSS":

                crud_strings["title_list"] = T("Group Activities")

                # Get service root types
                stable = s3db.org_service
                query = (stable.parent == None) & \
                        (stable.name != INDIVIDUAL_SUPPORT) & \
                        (stable.name != MENTAL_HEALTH) & \
                        (stable.deleted != True)
                rows = db(query).select(stable.id)
                root_service_ids = [row.id for row in rows]

                # Filter activities
                query = (FS("service_id$root_service").belongs(root_service_ids))
                if r.representation == "json":

                    import datetime
                    today = r.utcnow.date()
                    fortnight = datetime.timedelta(days=14)

                    # Filter by date
                    start_date = FS("start_date")
                    end_date = FS("end_date")
                    query &= ((start_date == None) | (start_date <= today)) & \
                             ((end_date == None) | (end_date >= today - fortnight))

                    # Allow current value to remain
                    include = r.get_vars.get("include")
                    if include and include.isdigit():
                        query |= (FS("id") == int(include))

                r.resource.add_filter(query)

                # Filter service selector
                field = table.service_id
                field.represent = S3Represent(lookup = "org_service",
                                              hierarchy = True,
                                              translate = True,
                                              )
                field.requires = IS_ONE_OF(db, "org_service.id",
                                           field.represent,
                                           filterby = "root_service",
                                           filter_opts = root_service_ids,
                                           sort=True,
                                           )
                widget_represent = S3Represent(lookup = "org_service",
                                               hierarchy = False,
                                               translate = True)
                field.widget = S3HierarchyWidget(multiple = False,
                                                 leafonly = True,
                                                 filter = (FS("root_service").belongs(root_service_ids)),
                                                 represent = widget_represent,
                                                 )

                # Expose gender type
                field = table.gender
                field.readable = field.writable = True

                # Expose modality (with custom labels for options)
                field = table.modality
                modality_opts = {"E": T("CC/Camp"),
                                 "O": T("Outreach"),
                                 }
                field.requires = IS_IN_SET(modality_opts, zero=None)
                field.represent = S3Represent(options=modality_opts)
                field.readable = field.writable = True

                # Expose outreach area
                field = table.location_id
                field.readable = field.writable = True

                # Expose project code
                field = table.project_id
                field.comment = None
                field.label = T("Project Code")
                field.represent = stl_project_id_represent
                field.requires = IS_ONE_OF(db, "project_project.id",
                                           stl_project_id_represent,
                                           )
                field.readable = field.writable = True

                # Expose certificate fields
                field = table.certificate
                field.readable = field.writable = True

                field = table.certificate_details
                field.readable = field.writable = True

                # Toggle visibility of location fields for individual records
                record = r.record
                if record:
                    if record.modality == "O":
                        table.location_id.readable = True
                        table.site_id.readable = False
                        table.room_id.readable = False
                    else:
                        table.location_id.readable = False
                        table.site_id.readable = True
                        table.room_id.readable = True

                # Customise distributions
                dtable = s3db.supply_distribution

                # Default date today
                field = dtable.date
                field.default = current.request.utcnow.date()

                # Default quantity 1
                field = dtable.value
                field.default = 1

                # Don't allow to create new items from here
                field = dtable.parameter_id
                field.comment = None

                # Custom list fields
                list_fields = ["service_id",
                               "project_id",
                               "start_date",
                               "end_date",
                               "period",
                               "gender",
                               "age_group_id",
                               "modality",
                               #"site_id",
                               #"room_id",
                               #"location_id",
                               "facilitator",
                               ]

                # Custom form
                crud_form = S3SQLCustomForm("organisation_id",
                                            "service_id",
                                            "project_id",
                                            "start_date",
                                            "end_date",
                                            "period",
                                            "gender",
                                            "age_group_id",
                                            "modality",
                                            "site_id",
                                            "room_id",
                                            "location_id",
                                            "facilitator",
                                            S3SQLInlineComponent(
                                                "distribution",
                                                explicit_add = T("Add Item"),
                                                fields = [(T("Date"),"date"),
                                                          "parameter_id",
                                                          "value",
                                                          ],
                                                label = T("Item Distribution"),
                                                # Embed the component rather than the link
                                                link = False,
                                                name = "distribution",
                                                ),
                                            "certificate",
                                            "certificate_details",
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

                # Custom filter widgets
                filter_widgets = [
                    S3TextFilter(["facilitator",
                                  "comments",
                                  ],
                                 label = T("Search"),
                                 ),
                    S3HierarchyFilter("service_id",
                                      lookup = "org_service",
                                      filter = (FS("root_service").belongs(root_service_ids)),
                                      ),
                    S3OptionsFilter("project_id",
                                    options = s3_get_filter_opts("project_project"),
                                    ),
                    S3OptionsFilter("gender",
                                    hidden = True,
                                    ),
                    S3OptionsFilter("age_group_id",
                                    hidden = True,
                                    ),
                    S3DateFilter("start_date",
                                 hidden = True,
                                 ),
                    S3DateFilter("end_date",
                                 hidden = True,
                                 ),
                    ]

                s3db.configure("dvr_activity",
                               crud_form = crud_form,
                               filter_widgets = filter_widgets,
                               list_fields = list_fields,
                               )

                scripts = s3.scripts
                script = "/%s/static/themes/STL/js/activity.js" % r.application
                if script not in scripts:
                    scripts.append(script)

            s3db.configure("dvr_activity",
                           # Custom update-onaccept to propagate
                           # service_id changes to case activities:
                           update_onaccept = dvr_activity_update_onaccept,
                           )

            return result
        s3.prep = custom_prep

        # Make sure action buttons retain the service_type
        s3.crud.keep_vars = ("service_type",)

        return attr

    settings.customise_dvr_activity_controller = customise_dvr_activity_controller

    # -------------------------------------------------------------------------
    def reset_case_status(person_id):
        """
            Reset case status from OPEN to NEW if no case activities
            exist; for all cases related to person_id

            @param person_id: the person record ID
        """

        db = current.db
        s3db = current.s3db

        # Get relevant status IDs
        stable = s3db.dvr_case_status
        query = (stable.code.belongs(("NEW", "OPEN"))) & \
                (stable.deleted == False)
        rows = db(query).select(stable.id,
                                stable.code,
                                limitby = (0, 2),
                                )
        status_ids = dict((row.code, row.id) for row in rows)

        NEW = status_ids.get("NEW")
        OPEN = status_ids.get("OPEN")
        if NEW and OPEN:

            # Count the number of case activities per OPEN case record
            ctable = s3db.dvr_case
            atable = s3db.dvr_case_activity

            left = atable.on((atable.person_id == ctable.person_id) & \
                             ((atable.case_id == None) | \
                              (atable.case_id == ctable.id)) & \
                             (atable.deleted == False))

            query = (ctable.person_id == person_id) & \
                    (ctable.status_id == OPEN) & \
                    (ctable.deleted == False)

            acount = atable.id.count()

            rows = db(query).select(ctable.id,
                                    acount,
                                    groupby = ctable.id,
                                    left = left,
                                    )
            for row in rows:
                case = row.dvr_case
                if row[acount] == 0:
                    # Reset status to NEW
                    case.update_record(status_id = NEW)

    # -------------------------------------------------------------------------
    def dvr_case_onaccept(form):
        """
            Additional custom-onaccept for dvr_case to force-update the
            realm entity of the person record:
            - the organisation managing the case is the realm-owner,
              but the person record is written first, so we need to
              update it after writing the case
            - the case can be transferred to another organisation/branch,
              and then the person record needs to be transferred to that
              same realm as well
            - Reset case status from OPEN to NEW if no case activities exist
        """

        form_vars = form.vars
        record_id = form_vars.id

        s3db = current.s3db

        # Get the person ID for this case
        person_id = form_vars.person_id
        if not person_id:
            table = s3db.dvr_case
            query = (table.id == record_id)
            row = current.db(query).select(table.person_id,
                                           limitby = (0, 1),
                                           ).first()
            if row:
                person_id = row.person_id

        if person_id:

            # Reset case status depending on the existence
            # of any related case activities:
            reset_case_status(person_id)

            # Configure components to inherit realm_entity
            # from the person record
            s3db.configure("pr_person",
                           realm_components = ("case_activity",
                                               "case_details",
                                               "economy",
                                               "evaluation",
                                               "household",
                                               "person_details",
                                               "address",
                                               "contact",
                                               "contact_emergency",
                                               "presence",
                                               ),
                           )

            # Force-update the realm entity for the person
            current.auth.s3_set_record_owner("pr_person",
                                             person_id,
                                             force_update = True,
                                             )

    # -------------------------------------------------------------------------
    def customise_dvr_case_resource(r, tablename):

        s3db = current.s3db

        # Update the realm-entity when the case gets updated
        # (because the assigned organisation/branch can change)
        config = {"update_realm": True,
                  }

        # Extend case-onaccept with custom routine
        get_config = s3db.get_config
        for method in ("create", "update", None):

            setting = "%s_onaccept" % method if method else "onaccept"
            default = get_config(tablename, setting)
            if not default:
                if method is None and len(config) < 2:
                    onaccept = dvr_case_onaccept
                else:
                    continue
            elif not isinstance(default, list):
                onaccept = [default, dvr_case_onaccept]
            else:
                onaccept = default
                if all(cb != dvr_case_onaccept for cb in onaccept):
                    onaccept.append(dvr_case_onaccept)
            config[setting] = onaccept

        s3db.configure(tablename, **config)

    settings.customise_dvr_case_resource = customise_dvr_case_resource

    # -------------------------------------------------------------------------
    def vulnerability_type_validation(form):
        """
            Validate "Protection Assessment" (dvr_vulnerability_type link)
            in case activities: for any required root category, at least one
            child category must be selected
        """

        key = "link_defaultvulnerability_type"

        formvars = form.vars
        try:
            vulnerability_types = formvars[key]
        except (KeyError, AttributeError):
            # No inline link we can validate
            return

        # Single value? => convert to list
        if vulnerability_types and \
           type(vulnerability_types) is not list:
            vulnerability_types = [vulnerability_types]

        # Get all required root categories
        ttable = current.s3db.dvr_vulnerability_type
        query = (ttable.required == True) & \
                (ttable.deleted == False)
        rows = current.db(query).select(ttable.id,
                                        ttable.name,
                                        )
        if not rows:
            return

        # Get the hierarchy
        from s3 import S3Hierarchy
        h = S3Hierarchy("dvr_vulnerability_type")

        for row in rows:

            # Find all child categories
            children = h.findall(row.id)
            if not children:
                continue

            message = T("At least one %(category)s must be selected") % \
                      {"category": row.name}

            # Check that at least one child is selected
            if vulnerability_types:
                if not any(c in children for c in vulnerability_types):
                    form.errors[key] = message
                    break
            else:
                # Nothing selected at all
                form.errors[key] = message
                break

    # -------------------------------------------------------------------------
    def case_activity_validation(form):
        """
            Custom validation for case activities:
                - prevent linking the same beneficiary twice to the
                  same group activity
        """

        db = current.db
        s3db = current.s3db

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        # Get the person_id and the activity_id
        table = s3db.dvr_case_activity
        load = []
        values = {}
        for fieldname in ("person_id", "activity_id"):
            if fieldname in form_vars:
                value = form_vars[fieldname]
            elif record_id:
                load.append(fieldname)
                continue
            else:
                value = table[fieldname].default
            values[fieldname] = value

        # Load missing values from existing record
        if record_id and load:
            fields = [table[fieldname] for fieldname in load]
            query = (table.id == record_id)
            row = db(query).select(limitby = (0, 1), *fields).first()
            for fieldname in load:
                values[fieldname] = row[fieldname]

        person_id = values.get("person_id")
        activity_id = values.get("activity_id")

        # Check whether another link already exists
        if person_id and activity_id:
            query = (table.person_id == person_id) & \
                    (table.activity_id == activity_id) & \
                    (table.deleted == False)
            if record_id:
                query &= (table.id != record_id)
            row = db(query).select(table.id, limitby=(0, 1)).first()
            if row:
                error = T("Beneficiary is already registered for this activity")
                for fieldname in ("person_id", "activity_id"):
                    if fieldname in form_vars:
                        form.errors[fieldname] = error

    # -------------------------------------------------------------------------
    def pss_case_activity_onaccept(form):
        """
            PSS Case Activities inherit the project ID from
            the group activity record (custom onaccept extension)

            @param form: the FORM
        """

        formvars = form.vars
        try:
            record_id = formvars.id
        except AttributeError:
            return

        db = current.db
        s3db = current.s3db

        atable = s3db.dvr_activity
        ctable = s3db.dvr_case_activity
        left = atable.on(atable.id == ctable.activity_id)

        query = (ctable.id == record_id)

        row = db(query).select(atable.project_id,
                               left = left,
                               limitby = (0, 1),
                               ).first()

        project_id = row.project_id if row else None
        db(query).update(project_id = row.project_id)

    # -------------------------------------------------------------------------
    def case_activity_onaccept(form):
        """
            Custom onaccept for case activities to
                - update the case status depending on the total number
                  of open case activities
        """

        formvars = form.vars
        try:
            record_id = formvars.id
        except AttributeError:
            return

        db = current.db
        s3db = current.s3db

        # Get relevant status IDs
        stable = s3db.dvr_case_status
        query = (stable.code.belongs(("NEW", "OPEN"))) & \
                (stable.deleted == False)
        rows = db(query).select(stable.id,
                                stable.code,
                                limitby = (0, 2),
                                )
        status_ids = dict((row.code, row.id) for row in rows)

        NEW = status_ids.get("NEW")
        OPEN = status_ids.get("OPEN")
        if NEW and OPEN:

            # Set all related NEW cases to OPEN
            atable = s3db.dvr_case_activity
            ctable = s3db.dvr_case
            join = ctable.on((ctable.person_id == atable.person_id) & \
                             (ctable.deleted == False) & \
                             ((atable.case_id == None) | \
                              (ctable.id == atable.case_id)))
            query = (atable.id == record_id) & \
                    (ctable.status_id == NEW)
            cases = db(query).select(ctable.id, join=join)
            for case in cases:
                case.update_record(status_id = OPEN)

    # -------------------------------------------------------------------------
    def case_activity_ondelete(row):
        """
            Reset case status when the last case activity gets deleted
        """

        try:
            record_id = row.id
        except AttributeError:
            return

        db = current.db

        # Extract the person ID
        atable = current.s3db.dvr_case_activity
        row = db(atable.id == record_id).select(atable.deleted_fk,
                                                limitby = (0, 1),
                                                ).first()
        if row and row.deleted_fk:

            import json
            data = json.loads(row.deleted_fk)

            person_id = data.get("person_id")
            if person_id:
                reset_case_status(person_id)

    # -------------------------------------------------------------------------
    def expose_project_id(table, mandatory=False):
        """
            Helper function to expose "Project Code"
        """

        from s3 import IS_ONE_OF

        field = table.project_id
        field.label = current.T("Project Code")
        field.comment = None
        field.readable = field.writable = True

        # Represent as code
        field.represent = stl_project_id_represent
        requires = IS_ONE_OF(current.db, "project_project.id",
                             stl_project_id_represent,
                             )

        # Mandatory or not?
        if mandatory:
            field.requires = requires
        else:
            field.requires = IS_EMPTY_OR(requires)

    def expose_human_resource_id(table, mandatory=False):
        """
            Helper function to expose "Person Responsible"
        """

        field = table.human_resource_id
        field.label = current.T("Person Responsible")
        field.widget = None
        field.comment = None
        field.readable = field.writable = True

        # Mandatory or not?
        requires = field.requires
        if isinstance(requires, IS_EMPTY_OR):
            if mandatory:
                field.requires = requires.other
        elif not mandatory:
            field.requires = IS_EMPTY_OR(requires)

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_resource(r, tablename):

        from s3 import FS, \
                       IS_ONE_OF, \
                       S3HierarchyWidget, \
                       S3SQLCustomForm, \
                       S3SQLInlineComponent, \
                       S3SQLInlineLink, \
                       s3_comments_widget

        T = current.T
        db = current.db
        s3db = current.s3db

        s3 = current.response.s3

        args = r.args
        if r.tablename == "dvr_case_activity" and \
           args and args[0] == "count_due_followups":

            # Just counting due follow-ups

            # Get service root type
            stable = s3db.org_service
            query = (stable.parent == None) & \
                    (stable.name == INDIVIDUAL_SUPPORT) & \
                    (stable.deleted != True)
            service = db(query).select(stable.id, limitby=(0, 1)).first()
            root_service_id = service.id if service else None

            # Filter activities by root service
            query = (FS("service_id$root_service") == root_service_id)
            r.resource.add_filter(query)

            return

        # Custom onaccept callback to automatically update
        # the case status depending on the number of open
        # case activities in the case
        s3db.add_custom_callback("dvr_case_activity",
                                 "onaccept",
                                 case_activity_onaccept,
                                 )

        # Custom ondelete callback to automatically reset
        # the case status from OPEN to NEW if the last case
        # activity gets deleted
        s3db.add_custom_callback("dvr_case_activity",
                                 "ondelete",
                                 case_activity_ondelete,
                                 )

        # Different representations of service_id:
        #   - lists use hierarchical
        #   - hierarchy-widgets use non-hierarchical
        service_represent = S3Represent(lookup = "org_service",
                                        hierarchy = False,
                                        translate = True,
                                        )
        service_represent_hierarchical = S3Represent(lookup = "org_service",
                                                     hierarchy = True,
                                                     translate = True,
                                                     )

        # Custom labels
        COMPLAINT_TYPE = T("MH Complaint Type")

        component_name = r.component_name
        if r.tablename == "dvr_activity":

            # "Beneficiaries" tab of PSS or MH group activities

            catable = s3db.dvr_case_activity

            # Expose and configure person_id field
            field = catable.person_id
            field.readable = field.writable = True
            field.represent = s3db.pr_PersonRepresent(show_link=True)
            from s3 import S3PersonAutocompleteWidget
            field.widget = S3PersonAutocompleteWidget(
                               controller = "dvr",
                               function = "person_search",
                               )
            field.comment = T("Enter some characters of the ID or name to start the search, then select from the drop-down")

            # Adapt CRUD strings to perspective
            s3.crud_strings["dvr_case_activity"] = Storage(
                label_create = T("Add Beneficiary"),
                title_display = T("Beneficiary Details"),
                title_list = T("Beneficiaries"),
                title_update = T("Edit Beneficiary"),
                label_list_button = T("List Beneficiaries"),
                label_delete_button = T("Remove Beneficiary"),
                msg_record_created = T("Beneficiary added"),
                msg_record_modified = T("Beneficiary updated"),
                msg_record_deleted = T("Beneficiary removed"),
                msg_list_empty = T("No Beneficiaries currently registered"),
                )

            # Determine root service type of master record
            root_service_id = root_service_name = None
            stable = s3db.org_service

            if r.record:
                rstable = stable.with_alias("root_service")

                left = rstable.on(rstable.id == stable.root_service)
                query = (stable.id == r.record.service_id) & \
                        (stable.deleted == False)
                root_service = db(query).select(rstable.id,
                                                rstable.name,
                                                left=left,
                                                limitby=(0, 1)).first()
                if root_service:
                    root_service_id = root_service.id
                    root_service_name = root_service.name if root_service else None

            insertable = False

            # Service-type specific crud_form/list_fields
            if root_service_name == INDIVIDUAL_SUPPORT:

                # This service type has no group activities
                r.error(400, "Invalid Group Activity")

            elif root_service_name == MENTAL_HEALTH:

                # "Beneficiaries" tab of Mental Health group activities

                expose_project_id(catable)
                expose_human_resource_id(catable)

                # Filter need types
                ntable = s3db.dvr_need
                left = stable.on(stable.id == ntable.service_id)
                query = (stable.root_service == root_service_id) & \
                        (stable.deleted != True)

                FILTER = (FS("service_id$root_service") == root_service_id)

                field = s3db.dvr_case_activity_need.need_id
                field.label = COMPLAINT_TYPE
                field.comment = None
                field.requires = IS_ONE_OF(db(query), "dvr_need.id",
                                           field.represent,
                                           left = left,
                                           )

                # No follow-ups for MH
                catable.followup.default = False
                catable.followup_date.default = None

                # Expose achievement field
                field = catable.achievement
                field.readable = field.writable = True

                # Expose provider type field
                field = catable.provider_type_id
                field.readable = field.writable = True

                # Expose termination type field
                field = catable.termination_type_id
                field.label = T("Type of Exit")
                field.readable = field.writable = True

                # Filter termination types
                tttable = s3db.dvr_termination_type
                query = (tttable.service_id == root_service_id)
                field.requires = IS_EMPTY_OR(IS_ONE_OF(db(query),
                                                       "dvr_termination_type.id",
                                                       field.represent,
                                                       ))

                crud_form = S3SQLCustomForm("person_id",
                                            S3SQLInlineLink("need",
                                                            label = COMPLAINT_TYPE,
                                                            field = "need_id",
                                                            widget = "hierarchy",
                                                            multiple = False,
                                                            leafonly = True,
                                                            filter = FILTER,
                                                            ),
                                            "human_resource_id",
                                            "project_id",
                                            "provider_type_id",
                                            (T("Status of main complaint at last visit"), "achievement"),
                                            "termination_type_id",
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

                # Custom list fields
                list_fields = ["person_id$pe_label",
                               "person_id",
                               "person_id$gender",
                               "person_id$age",
                               (T("Phone Number"), "person_id$phone.value"),
                               "need__link.need_id",
                               "human_resource_id",
                               "project_id",
                               ]
            else:

                # "Beneficiaries" tab of PSS-type group activities

                record = r.record
                if record:

                    # Allow creation of new case activities
                    insertable = True

                    # Inherit + hide service_id
                    field = catable.service_id
                    field.default = record.service_id
                    field.readable = field.writable = False

                    # Inherit + hide project_id
                    field = catable.project_id
                    field.default = record.project_id
                    field.readable = field.writable = False

                # No follow-ups for PSS
                catable.followup.default = False
                catable.followup_date.default = None

                # Custom CRUD form
                crud_form = S3SQLCustomForm("person_id",
                                            S3SQLInlineComponent(
                                                "document",
                                                fields = ["file", "comments"],
                                                filterby = {"field": "file",
                                                            "options": "",
                                                            "invert": True,
                                                            },
                                                label = T("Attachments"),
                                                name = "file",
                                                ),
                                            "comments",
                                            )

                # Custom list fields
                list_fields = ["person_id$pe_label",
                               "person_id",
                               "person_id$gender",
                               "person_id$age",
                               (T("Phone Number"), "person_id$phone.value"),
                               "comments",
                               ]

            s3db.configure("dvr_case_activity",
                           insertable = insertable,
                           extra_fields = "person_id$date_of_birth",
                           )

        elif r.tablename == "dvr_case_activity" or \
             r.component_name == "case_activity" or \
             r.function == "due_followups":

            # "Individual Support" perspectives, incl. due follow-ups

            # Get service root type
            stable = s3db.org_service
            query = (stable.parent == None) & \
                    (stable.name == INDIVIDUAL_SUPPORT) & \
                    (stable.deleted != True)
            service = db(query).select(stable.id, limitby=(0, 1)).first()
            root_service_id = service.id if service else None

            # CRUD Strings use "Protection Response"
            s3.crud_strings["dvr_case_activity"] = Storage(
                label_create = T("Create Protection Response"),
                title_display = T("Protection Response Details"),
                title_list = T("Protection Responses"),
                title_update = T("Edit Protection Response"),
                label_list_button = T("List Protection Responses"),
                label_delete_button = T("Delete Protection Response"),
                msg_record_created = T("Protection Response added"),
                msg_record_modified = T("Protection Response updated"),
                msg_record_deleted = T("Protection Response deleted"),
                msg_list_empty = T("No Protection Responses currently registered"),
                )

            if r.tablename == "dvr_case_activity" or \
               r.function == "due_followups":

                # Master perspective
                table = r.table
                component = r.resource

                # Filter activities by root service
                query = (FS("service_id$root_service") == root_service_id)
                component.add_filter(query)

                # Configure summary
                summary = ({"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}]
                            },
                           {"name": "charts",
                            "label": "Report",
                            "widgets": [{"method": "report",
                                         "ajax_init": True}]
                            },
                           )

                # Configure report options
                report_axes = ["person_id$gender",
                               "person_id$person_details.nationality",
                               "project_id",
                               "organisation_id",
                               "service_id",
                               (T("Interventions Required"),
                                   "response_type__link.response_type_id",
                                   ),
                               "need__link.need_id",
                               # @todo: consider using a filtered "home_address" component
                               "person_id$address.location_id$L2",
                               "completed",
                               "person_id$dvr_case_details.referral_type_id",
                               ]

                report_options = {
                    "rows": report_axes,
                    "cols": report_axes,
                    "fact": [(T("Number of Beneficiaries"), "count(person_id)"),
                             (T("Number of Activities"), "count(id)"),
                             ],
                    #"defaults": {"rows": "person_id$gender",
                    #             "cols": "person_id$person_details.nationality",
                    #             "fact": "count(person_id)",
                    #             "totals": True,
                    #             },
                    }

                component.configure(report_options = report_options,
                                    summary = summary,
                                    )

            else:
                # Component tab
                table = r.component.table
                component = r.component

            # Extend onvalidation with custom validation for
            # mandatory vulnerability type categories
            s3db.add_custom_callback("dvr_case_activity",
                                     "onvalidation",
                                     vulnerability_type_validation,
                                     )

            component.configure(orderby = ~table.start_date,
                                )

            # Expose "Project Code" and "Person responsible" (both mandatory)
            expose_project_id(table, mandatory=True)
            expose_human_resource_id(table, mandatory=True)

            # Adjust validator and widget for service_id
            field = table.service_id
            field.requires = IS_ONE_OF(db, "org_service.id",
                                       field.represent,
                                       filterby = "root_service",
                                       filter_opts = (root_service_id,),
                                       sort=True,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                             leafonly = True,
                                             filter = (FS("root_service") == root_service_id),
                                             )

            # Filter need types
            ntable = s3db.dvr_need
            left = stable.on(stable.id == ntable.service_id)
            query = (stable.root_service == root_service_id) & \
                    (stable.deleted != True)
            SECTOR = T("Protection Response Sector")
            FILTER = (FS("service_id$root_service") == root_service_id)

            #field = table.need_id
            field = s3db.dvr_case_activity_need.need_id
            field.label = SECTOR
            field.comment = None
            field.requires = IS_ONE_OF(db(query), "dvr_need.id",
                                       field.represent,
                                       left = left,
                                       )
            #field.widget = S3HierarchyWidget(multiple = False,
            #                                 leafonly = False,
            #                                 filter = FILTER,
            #                                 )

            # Customise Need Details (+make mandatory)
            field = table.need_details
            field.label = T("Initial Situation Explanation")
            field.readable = field.writable = True
            field.requires = IS_NOT_EMPTY()

            # Customise Activity Details (+make mandatory)
            field = table.activity_details
            field.label = T("Protection Response Details")
            field.readable = field.writable = True
            field.requires = IS_NOT_EMPTY()

            # Customise Outside Support
            field = table.outside_support
            field.label = T("Support provided by others")
            field.readable = field.writable = True

            # Customise Priority
            field = table.priority
            field.label = T("Priority")
            field.readable = field.writable = True

            # Customise start_date field (+make mandatory)
            field = table.start_date
            field.label = T("Opened on")
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Show end_date field (read-only)
            field = table.end_date
            field.label = T("Closed on")
            field.readable = True
            # Allow to manually set closed_on (for historic records, only create)
            if not r.component_id:
                field.writable = True

            # Customise "completed" flag
            # => label as "Status" and use drop-down for open/closed
            field = table.completed
            field.label = T("Status")
            field.represent = lambda v, row=None: T("Closed") if v else T("Open")
            field.requires = [IS_IN_SET([(False, T("Open")),
                                         (True, T("Closed")),
                                         ],
                                        zero=None,
                                        ),
                              # Form option is a str => convert to boolean
                              lambda v: (str(v) == "True", None),
                              ]
            from gluon.sqlhtml import OptionsWidget
            field.widget = OptionsWidget.widget

            # Customise SNF fields
            ftable = s3db.dvr_activity_funding
            field = ftable.funding_required
            field.label = T("Need for SNF")
            field = ftable.reason
            field.label = T("Justification for SNF")
            field.widget = s3_comments_widget
            field = ftable.approved
            field.label = T("SNF Assistance Approved by Committee")

            # Expose termination type field
            field = table.termination_type_id
            field.label = T("Closure Reason")
            field.readable = field.writable = True

            # Filter termination types
            tttable = s3db.dvr_termination_type
            query = (tttable.service_id == root_service_id)
            field.requires = IS_EMPTY_OR(IS_ONE_OF(db(query),
                                                   "dvr_termination_type.id",
                                                   field.represent,
                                                   ))

            # Custom CRUD form
            crud_form = S3SQLCustomForm("person_id",
                                        "human_resource_id",
                                        "project_id",
                                        S3SQLInlineLink("vulnerability_type",
                                                        label = T("Protection Assessment"),
                                                        field = "vulnerability_type_id",
                                                        widget = "hierarchy",
                                                        multiple = True,
                                                        leafonly = True,
                                                        ),
                                        "need_details",
                                        "service_id",
                                        S3SQLInlineLink("need",
                                                        label = SECTOR,
                                                        field = "need_id",
                                                        widget = "hierarchy",
                                                        multiple = False,
                                                        leafonly = True,
                                                        filter = FILTER,
                                                        required = True,
                                                        ),
                                        "priority",
                                        S3SQLInlineLink("response_type",
                                                        label = T("Interventions Required"),
                                                        field = "response_type_id",
                                                        widget = "hierarchy",
                                                        multiple = True,
                                                        leafonly = True,
                                                        ),
                                        "activity_details",
                                        "start_date",
                                        "outside_support",
                                        "activity_funding.funding_required",
                                        "activity_funding.reason",
                                        "activity_funding.approved",
                                        "followup",
                                        "followup_date",
                                        "completed",
                                        "end_date",
                                        (T("Result of Protection Response"), "outcome"),
                                        "termination_type_id",
                                        S3SQLInlineComponent(
                                            "case_effort",
                                            label = T("Efforts"),
                                            fields = ["date",
                                                      (T("Name of Meeting"), "name"),
                                                      #"human_resource_id",
                                                      "hours",
                                                      "comments",
                                                      ]
                                            ),
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

            scripts = s3.scripts
            script = "/%s/static/themes/STL/js/case_activity.js" % r.application
            if script not in scripts:
                scripts.append(script)

            list_fields = ["person_id",
                           "service_id",
                           "human_resource_id",
                           "project_id",
                           "need__link.need_id",
                           "start_date",
                           (T("Interventions Required"),
                                "response_type__link.response_type_id"),
                           "priority",
                           "followup",
                           "followup_date",
                           "completed",
                           "end_date",
                           ]

        elif r.component_name == "pss_activity":

            # "Group Activities" tab of Beneficiary

            table = r.component.table

            field = table.project_id
            field.label = T("Project Code")
            field.writable = False

            # Configure custom onaccept to inherit
            # project ID from group activity
            s3db.add_custom_callback("dvr_case_activity",
                                     "onaccept",
                                     pss_case_activity_onaccept,
                                     )

            # Get service root types
            stable = s3db.org_service
            query = (stable.parent == None) & \
                    (stable.name != INDIVIDUAL_SUPPORT) & \
                    (stable.name != MENTAL_HEALTH) & \
                    (stable.deleted != True)
            rows = db(query).select(stable.id)
            root_service_ids = [row.id for row in rows]

            # Filter service types
            field = table.service_id
            field.represent = service_represent_hierarchical
            field.requires = IS_ONE_OF(db, "org_service.id",
                                       field.represent,
                                       filterby = "root_service",
                                       filter_opts = root_service_ids,
                                       sort=True,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                             leafonly = True,
                                             filter = (FS("root_service").belongs(root_service_ids)),
                                             represent = service_represent,
                                             )

            # Filter activities
            field = table.activity_id
            field.readable = field.writable = True

            import datetime
            today = r.utcnow.date()
            fortnight = datetime.timedelta(days=14)

            atable = s3db.dvr_activity
            stable = s3db.org_service
            left = stable.on(stable.id == atable.service_id)
            query = (stable.root_service.belongs(root_service_ids)) & \
                    ((atable.start_date == None) | (atable.start_date <= today)) & \
                    ((atable.end_date == None) | (atable.end_date >= today - fortnight))

            current_activity_id = None
            if r.component_id:

                # Look up current activity_id
                # => need to pass it to the Ajax-controller for filterOptionsS3,
                #    otherwise it would remove the current value from the update
                #    form when we're past the deadline
                # => need to allow the current value to pass the validator on
                #    update, otherwise update with unchanged value would fail
                #    when we're past the deadline
                component = r.component
                component.load()
                record = component.records().first()

                if record:
                    current_activity_id = record.activity_id
                    if current_activity_id:
                        query |= (atable.id == current_activity_id)

            field.requires = IS_EMPTY_OR(IS_ONE_OF(db(query), "dvr_activity.id",
                                                   field.represent,
                                                   left = left,
                                                   ))

            if r.interactive:
               script = '''$.filterOptionsS3({
'trigger':'service_id',
'target':'activity_id',
'lookupURL': S3.Ap.concat('/dvr/activity.json?service_type=PSS&include=%s&~.service_id='),
'fncRepresent': function(r){return r.service_id+' ('+(r.start_date||'..')+' - '+(r.end_date||'..')+') ('+(r.facilitator||'..')+')'},
'optional': true
})''' % current_activity_id

               s3.jquery_ready.append(script)

            # No follow-ups for PSS
            table.followup.default = False
            table.followup_date.default = None

            # Custom CRUD form
            crud_form = S3SQLCustomForm("person_id",
                                        "service_id",
                                        #"project_id",
                                        "activity_id",
                                        S3SQLInlineComponent(
                                            "document",
                                            fields = ["file", "comments"],
                                            filterby = {"field": "file",
                                                        "options": "",
                                                        "invert": True,
                                                        },
                                            label = T("Attachments"),
                                            name = "file",
                                            ),
                                        "comments",
                                        )
            # Custom list fields
            list_fields = ["person_id",
                           "service_id",
                           "project_id",
                           "activity_id",
                           ]

        elif r.component_name == "mh_activity":

            # "Mental Health" tab of Beneficiary

            table = r.component.table

            expose_project_id(table)
            expose_human_resource_id(table)

            # Get service root type
            stable = s3db.org_service
            query = (stable.parent == None) & \
                    (stable.name == MENTAL_HEALTH) & \
                    (stable.deleted != True)
            service = db(query).select(stable.id, limitby=(0, 1)).first()
            root_service_id = service.id if service else None

            # Filter service types
            field = table.service_id
            field.requires = IS_ONE_OF(db, "org_service.id",
                                       field.represent,
                                       filterby = "root_service",
                                       filter_opts = (root_service_id,),
                                       sort=True,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                             leafonly = True,
                                             filter = (FS("root_service") == root_service_id),
                                             )

            # Filter need types
            ntable = s3db.dvr_need
            left = stable.on(stable.id == ntable.service_id)
            query = (stable.root_service == root_service_id) & \
                    (stable.deleted != True)
            FILTER = (FS("service_id$root_service") == root_service_id)

            #field = table.need_id
            field = s3db.dvr_case_activity_need.need_id
            field.label = COMPLAINT_TYPE
            field.comment = None
            field.requires = IS_ONE_OF(db(query), "dvr_need.id",
                                       field.represent,
                                       left = left,
                                       )
            #field.widget = S3HierarchyWidget(multiple = False,
            #                                 leafonly = False,
            #                                 filter = FILTER,
            #                                 )

            # Filter activities
            field = table.activity_id
            field.readable = field.writable = True
            atable = s3db.dvr_activity
            stable = s3db.org_service
            left = stable.on(stable.id == atable.service_id)
            query = (stable.root_service == root_service_id)
            field.requires = IS_EMPTY_OR(IS_ONE_OF(db(query), "dvr_activity.id",
                                                   field.represent,
                                                   left = left,
                                                   ))

            # Filter options for activity when service type selected
            if r.interactive:
                script = '''$.filterOptionsS3({
'trigger':'service_id',
'target':'activity_id',
'lookupURL': S3.Ap.concat('/dvr/activity.json?service_type=MH&~.service_id='),
'fncRepresent': function(r){return r.name||r.service_id},
'optional': true
})'''
                s3.jquery_ready.append(script)

            # No follow-ups for MH
            table.followup.default = False
            table.followup_date.default = None

            # Expose achievement field
            field = table.achievement
            field.readable = field.writable = True

            # Expose provider type field
            field = table.provider_type_id
            field.readable = field.writable = True

            # Expose termination type field
            field = table.termination_type_id
            field.label = T("Type of Exit")
            field.readable = field.writable = True

            # Filter termination types
            tttable = s3db.dvr_termination_type
            query = (tttable.service_id == root_service_id)
            field.requires = IS_EMPTY_OR(IS_ONE_OF(db(query),
                                                   "dvr_termination_type.id",
                                                   field.represent,
                                                   ))

            # Custom CRUD form
            crud_form = S3SQLCustomForm("person_id",
                                        S3SQLInlineLink("need",
                                                        label = COMPLAINT_TYPE,
                                                        field = "need_id",
                                                        widget = "hierarchy",
                                                        multiple = False,
                                                        leafonly = True,
                                                        filter = FILTER,
                                                        ),
                                        "service_id",
                                        "human_resource_id",
                                        "project_id",
                                        "activity_id",
                                        "provider_type_id",
                                        (T("Status of main complaint at last visit"), "achievement"),
                                        "termination_type_id",
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

            # Custom list fields
            list_fields = ["person_id",
                           "need__link.need_id",
                           "service_id",
                           "human_resource_id",
                           "project_id",
                           "activity_id",
                           ]

        else:
            # Other perspective (currently unused)
            expose_project_id(s3db.dvr_case_activity)
            crud_form = S3SQLCustomForm("person_id",
                                        "project_id",
                                        "service_id",
                                        #"need_id",
                                        "followup",
                                        "followup_date",
                                        "activity_funding.funding_required",
                                        "activity_funding.reason",
                                        "comments",
                                        )
            # Custom list fields
            list_fields = ["person_id",
                           "project_id",
                           "service_id",
                           "followup",
                           "followup_date",
                           ]

        s3db.configure("dvr_case_activity",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       owner_group = stl_case_activity_owner_group,
                       )
        s3db.add_custom_callback("dvr_case_activity",
                                 "onvalidation",
                                 case_activity_validation,
                                 )

    settings.customise_dvr_case_activity_resource = customise_dvr_case_activity_resource

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Show person_id as link to case
            table = r.resource.table
            table.person_id.represent = s3db.pr_PersonRepresent(show_link=True)

            if r.function == "due_followups":

                crud_strings = s3.crud_strings["dvr_case_activity"]
                crud_strings["title_list"] = T("Interventions to follow-up")

                # Custom list fields
                list_fields = [(T("Ref.No."), "person_id$pe_label"),
                               "person_id",
                               (T("Protection Response Sector"), "case_activity_need.need_id"),
                               "service_id",
                               "followup_date",
                               ]

                # Custom filter widgets
                from s3 import S3TextFilter, S3DateFilter
                filter_widgets = [S3TextFilter(["person_id$pe_label",
                                                "person_id$first_name",
                                                "person_id$last_name",
                                                "case_activity_need.need_id$name",
                                                "service_id$name",
                                                ],
                                                label = T("Search"),
                                                ),
                                  S3DateFilter("followup_date",
                                               cols = 2,
                                               hidden = True,
                                               ),
                                  ]
            else:
                # Custom list fields
                list_fields = ["person_id",
                               "service_id",
                               "human_resource_id",
                               "project_id",
                               "need__link.need_id",
                               "start_date",
                               (T("Interventions Required"),
                                    "response_type__link.response_type_id"),
                               "priority",
                               "followup",
                               "followup_date",
                               "completed",
                               "end_date",
                               ]

                # Custom filter widgets
                #Project Code,
                #Person Responsible,
                #Protection Assesment,
                #Service Type,
                #Protection Response Sector,
                #Interventions required

                # Limit HR filter options to selectable HRs
                requires = table.human_resource_id.requires
                if hasattr(requires, "options"):
                    hr_filter_opts = dict(opt for opt in requires.options() if opt[0])
                else:
                    hr_filter_opts = None

                from s3 import S3DateFilter, \
                               S3HierarchyFilter, \
                               S3LocationFilter, \
                               S3OptionsFilter, \
                               S3TextFilter, \
                               s3_get_filter_opts

                filter_widgets = [S3TextFilter(["person_id$pe_label",
                                                "person_id$first_name",
                                                "person_id$last_name",
                                                ],
                                                label = T("Search"),
                                                ),
                                  S3HierarchyFilter("person_id$dvr_case.organisation_id",
                                                    leafonly = False,
                                                    cascade_select = True,
                                                    ),
                                  S3OptionsFilter("human_resource_id",
                                                  options = hr_filter_opts,
                                                  ),
                                  S3OptionsFilter("project_id",
                                                  options = s3_get_filter_opts("project_project"),
                                                  ),
                                  S3HierarchyFilter("service_id",
                                                    hidden = True,
                                                    ),
                                  S3HierarchyFilter("vulnerability_type_case_activity.vulnerability_type_id",
                                                    label = T("Protection Assessment"),
                                                    hidden = True,
                                                    ),
                                  S3HierarchyFilter("case_activity_need.need_id",
                                                    hidden = True,
                                                    ),
                                  S3HierarchyFilter("response_type_case_activity.response_type_id",
                                                    hidden = True,
                                                    ),
                                  S3OptionsFilter("person_id$dvr_case_details.referral_type_id",
                                                  options = s3_get_filter_opts("dvr_referral_type"),
                                                  label = T("Referred to Case Management by"),
                                                  hidden = True,
                                                  ),
                                  # Not scalable
                                  #S3LocationFilter("person_id$address.location_id",
                                  #                hidden = True,
                                  #                ),
                                  S3OptionsFilter("completed",
                                                  hidden = True,
                                                  ),
                                  S3DateFilter("person_id$date_of_birth",
                                               hidden = True,
                                               ),
                                  S3DateFilter("start_date",
                                               hidden = True,
                                               ),
                                  S3DateFilter("end_date",
                                               hidden = True,
                                               ),
                                  ]

            r.resource.configure(filter_widgets = filter_widgets,
                                 list_fields = list_fields,
                                 )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_dvr_case_activity_controller = customise_dvr_case_activity_controller

    # -------------------------------------------------------------------------
    def customise_dvr_activity_funding_resource(r, tablename):

        T = current.T

        table = current.s3db.dvr_activity_funding
        field = table.funding_required
        field.label = T("Need for SNF")
        field = table.reason
        field.label = T("Justification for SNF")

    settings.customise_dvr_activity_funding_resource = customise_dvr_activity_funding_resource

    # -------------------------------------------------------------------------
    def customise_dvr_economy_resource(r, tablename):

        table = current.s3db.dvr_economy
        field = table.monthly_costs

        field.label = current.T("Monthly Rent Expense")

    settings.customise_dvr_economy_resource = customise_dvr_economy_resource

    # -------------------------------------------------------------------------
    def customise_dvr_household_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("hoh_relationship",
                                    "hoh_name",
                                    "hoh_date_of_birth",
                                    "hoh_gender",
                                    S3SQLInlineComponent("beneficiary_data",
                                                         fields = [(T("Age Group"), "beneficiary_type_id"),
                                                                   "female",
                                                                   "male",
                                                                   "other",
                                                                   "out_of_school",
                                                                   (T("Number Working"), "employed"),
                                                                   ],
                                                         label = T("Household Members"),
                                                         explicit_add = T("Add Household Members"),
                                                         ),
                                    "comments",
                                    )

        current.s3db.configure("dvr_household",
                               crud_form = crud_form,
                               )

    settings.customise_dvr_household_resource = customise_dvr_household_resource

    # -------------------------------------------------------------------------
    def customise_dvr_response_type_resource(r, tablename):

        current.response.s3.crud_strings["dvr_response_type"] = Storage(
            label_create = T("Create Intervention Type"),
            title_display = T("Intervention Type Details"),
            title_list = T("Intervention Types"),
            title_update = T("Edit Intervention Type"),
            label_list_button = T("List Intervention Types"),
            label_delete_button = T("Delete Intervention Type"),
            msg_record_created = T("Intervention Type created"),
            msg_record_modified = T("Intervention Type updated"),
            msg_record_deleted = T("Intervention Type deleted"),
            msg_list_empty = T("No Intervention Types currently registered"),
            )

    settings.customise_dvr_response_type_resource = customise_dvr_response_type_resource

    # -------------------------------------------------------------------------
    def customise_dvr_vulnerability_type_resource(r, tablename):

        # Expose required-flag
        table = current.s3db.dvr_vulnerability_type
        field = table.required
        field.readable = field.writable = True

    settings.customise_dvr_vulnerability_type_resource = customise_dvr_vulnerability_type_resource

    # =========================================================================
    # Person Registry
    #
    # Allow third gender
    settings.pr.hide_third_gender = False

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        table = current.s3db.pr_contact

        field = table.contact_description
        field.readable = field.writable = False

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
                  "OTHER",
                  )
        contact_methods = [(k, all_opts[k]) for k in subset if k in all_opts]
        field.requires = IS_IN_SET(contact_methods, zero=None)
        field.default = "SMS"

    settings.customise_pr_contact_resource = customise_pr_contact_resource

    # -------------------------------------------------------------------------
    def customise_pr_education_level_resource(r, tablename):

        table = current.s3db.pr_education_level

        # Hide organisation_id (not used here)
        field = table.organisation_id
        field.readable = field.writable = False

    settings.customise_pr_education_level_resource = customise_pr_education_level_resource

    # -------------------------------------------------------------------------
    def person_tag_onvalidation(form):
        """
            Custom onvalidation callback for person tags
            => INDIVIDUAL_ID must be unique
        """

        formvars = form.vars

        tag = formvars.tag
        value = formvars.value

        if tag != "INDIVIDUAL_ID" or value is None:
            return

        # Is this an update?
        if "id" in formvars:
            record_id = formvars.id
        elif "_id" in formvars:
            # Inline component
            record_id = formvars._id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            # New record
            record_id = None

        # Find a duplicate
        table = current.s3db.pr_person_tag
        query = (table.tag == "INDIVIDUAL_ID") & \
                (table.value == value) & \
                (table.deleted == False)
        if record_id:
            query &= (table.id != record_id)
        duplicate = current.db(query).select(table.id,
                                             limitby = (0, 1),
                                             ).first()

        # Reject if duplicate exists
        if duplicate:
            form.errors["value"] = current.T("ID already in database")

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db

        # Configure components to inherit realm_entity from the person record
        s3db.configure("pr_person",
                       realm_components = ("case_activity",
                                           "case_details",
                                           "economy",
                                           "evaluation",
                                           "household",
                                           "person_details",
                                           "address",
                                           "contact",
                                           "contact_emergency",
                                           "presence",
                                           ),
                       update_realm = True,
                       )

        # Custom components
        s3db.add_components("pr_person",
                            # Govt-assigned IDs: Family ID, Individual ID
                            pr_person_tag = ({"name": "family_id",
                                              "joinby": "person_id",
                                              "filterby": {
                                                  "tag": "FAMILY_ID",
                                                  },
                                              "multiple": False,
                                              },
                                             {"name": "individual_id",
                                              "joinby": "person_id",
                                              "filterby": {
                                                  "tag": "INDIVIDUAL_ID",
                                                  },
                                              "multiple": False,
                                              },
                                             ),
                            # Education level (simplified model)
                            pr_education_level = {"link": "pr_education",
                                                  "joinby": "person_id",
                                                  "key": "level_id",
                                                  },
                            )

        # Add contacts-method
        if r.controller == "dvr":

            # Use pr_Contacts as contacts-method
            s3db.set_method("pr", "person",
                            method = "contacts",
                            action = s3db.pr_Contacts,
                            )

            from s3 import IS_PERSON_GENDER

            table = s3db.pr_person

            # ID label is required, remove tooltip
            field = table.pe_label
            field.comment = DIV(_class = "tooltip",
                                _title = "%s|%s" % (T("Reference Number"),
                                                    T("The STL Individual Reference Number for this Beneficiary"),
                                                    ),
                                )
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Last name is required
            field = table.last_name
            field.requires = IS_NOT_EMPTY()

            # Date of Birth is required
            field = table.date_of_birth
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Gender is required, remove "unknown" option, adjust label
            field = table.gender
            field.label = current.T("Gender")
            field.default = None
            options = dict(s3db.pr_gender_opts)
            del options[1] # Remove "unknown"
            field.requires = IS_PERSON_GENDER(options, sort=True)

            dtable = s3db.pr_person_details

            # Nationality is required, default is Syrian
            field = dtable.nationality
            field.default = "SY"
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Custom validator for person tags
            s3db.add_custom_callback("pr_person_tag",
                                     "onvalidation",
                                     person_tag_onvalidation,
                                     )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def is_turkish_phone_number(value):
        """
            Custom validator for beneficiary mobile phone number:
                - requires 3-digit area code and 7-digit local number
                - rejects all country codes other than 0090 resp. +90
                - fixed output format with leading +90 country code
                - removes all whitespace
        """

        msg = "Enter turkish phone number in international format like +907837549574"

        if isinstance(value, basestring):
            import re
            match = re.match("^(0090|\+90|0){0,1}((\s*[0-9]){10})$", value.strip())
            if match:
                error = None
                value = "+90%s" % "".join(match.groups()[1].split())
            else:
                error = msg
        else:
            error = msg

        return value, error

    # -------------------------------------------------------------------------
    def set_default_pe_label():
        """
            Attempt to auto-generate a beneficiary reference number
            for the logged-in staff member, using the Staff ID (code)
            plus a n-digit number as pattern
        """

        db = current.db
        auth = current.auth
        s3db = current.s3db

        ptable = s3db.pr_person
        htable = s3db.hrm_human_resource

        # Number of trailing digits
        DIGITS = 4

        # Get the staff ID of the logged-in user
        code = None
        if auth.s3_logged_in() and auth.user:
            query = (ptable.pe_id == auth.user.pe_id) & \
                    (htable.person_id == ptable.id) & \
                    (htable.deleted == False)
            row = db(query).select(htable.code,
                                   orderby = ~htable.modified_on,
                                   limitby = (0, 1),
                                   ).first()
            if row:
                code = row.code

        if not code:
            # No staff ID => can not auto-generate reference number
            return

        # Get the highest reference number with that staff code
        query = (ptable.pe_label.like("%s%s" % (code, "_" * DIGITS))) & \
                (ptable.pe_label >= "%s%s1" % (code, "0" * (DIGITS -1))) & \
                (ptable.pe_label <= "%s%s" % (code, "9" * DIGITS)) & \
                (ptable.deleted == False)
        highest = ptable.pe_label.max()
        row = db(query).select(highest).first()

        if not row or not row[highest]:
            # No such reference number yet => start with 1
            next_id = 1
        else:
            try:
                last_id = int(row[highest][-DIGITS:])
            except ValueError:
                next_id = None
            else:
                # Increment it
                next_id = last_id + 1 if last_id < (10 ** DIGITS - 1) else None

        if next_id:
            template = "%%s%%0%sd" % DIGITS
            ptable.pe_label.default = template % (code, next_id)

    # -------------------------------------------------------------------------
    def get_service_ids():

        db = current.db
        s3db = current.s3db

        # Get service IDs
        stable = s3db.org_service
        query = (stable.deleted != True)
        rows = db(query).select(stable.id,
                                stable.name,
                                stable.parent,
                                stable.root_service,
                                cache = s3db.cache,
                                orderby = stable.root_service,
                                )

        # Group service IDs by root service
        mh_ids = []
        is_ids = []
        ps_ids = []
        sids = ps_ids

        group = set()
        root_service = None
        for row in rows:
            # Rows are ordered by root service, so they come in
            # groups each of which contains one root service

            if row.root_service != root_service:
                # Different root service => new group
                if group:
                    # Add previous group to its service_ids array
                    sids.extend(group)
                # Start new group
                group = set()
                root_service = row.root_service

            if row.parent is None:
                # This is the root service of the current group
                # => choose the right service_ids array for the group
                name = row.name
                if name == INDIVIDUAL_SUPPORT:
                    sids = is_ids
                elif name == MENTAL_HEALTH:
                    sids = mh_ids
                else:
                    # Everything else is PSS
                    sids = ps_ids

            group.add(row.id)

        # Add the last group to its service_ids array
        sids.extend(group)

        return {"mh": mh_ids, "is": is_ids, "ps": ps_ids}

    # -------------------------------------------------------------------------
    def configure_case_activity_components(service_ids):

        current.s3db.add_components("pr_person",
                                    dvr_case_activity = (
                                        {"name": "case_activity",
                                            "joinby": "person_id",
                                            "filterby": {
                                                "service_id": service_ids["is"],
                                                },
                                        },
                                        {"name": "mh_activity",
                                            "joinby": "person_id",
                                            "filterby": {
                                                "service_id": service_ids["mh"],
                                                },
                                        },
                                        {"name": "pss_activity",
                                            "joinby": "person_id",
                                            "filterby": {
                                                "service_id": service_ids["ps"],
                                                },
                                        },
                                       ),
                                    )

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        # Split case activity tabs by service type
        # NB this must happen before request parsing, so can neither be prep
        #    nor customise_resource; but should still perform the service_id
        #    look-up only when required, thus checking request args here:
        args = current.request.args
        if args and len(args) > 1 and \
           args[1] in ("case_activity", "mh_activity", "pss_activity"):
            service_ids = s3.stl_service_ids
            if not service_ids:
                s3.stl_service_ids = service_ids = get_service_ids()
            configure_case_activity_components(service_ids)
        else:
            configure_case_activity_components({"is": [], "mh": [], "ps": []})

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            controller = r.controller
            get_vars = r.get_vars

            archived = get_vars.get("archived")
            if archived in ("1", "true", "yes"):
                crud_strings = s3.crud_strings["pr_person"]
                crud_strings["title_list"] = T("Invalid Cases")

            if controller == "dvr":

                if r.method == "search_ac":

                    # Autocomplete using alternative search method
                    search_fields = ("first_name", "last_name", "pe_label")
                    s3db.set_method("pr", "person",
                                    method = "search_ac",
                                    action = s3db.pr_PersonSearchAutocomplete(search_fields),
                                    )

                if not r.component:

                    from s3 import IS_ONE_OF, S3HierarchyWidget

                    if r.interactive and not r.record and \
                       r.method == "create": # or not r.method:
                        set_default_pe_label()

                    ctable = s3db.dvr_case

                    # Remove empty option from case status selector
                    field = ctable.status_id
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires = requires.other
                        requires.zero = None

                    # Hierarchical Organisation Selector
                    field = ctable.organisation_id
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other
                    #field.requires = s3db.org_organisation_requires(required=True,
                    #                                                updateable=True,
                    #                                                )
                    represent = s3db.org_OrganisationRepresent(parent=False)
                    field.widget = S3HierarchyWidget(lookup="org_organisation",
                                                     represent=represent,
                                                     multiple=False,
                                                     leafonly=False,
                                                     )
                    field.comment = DIV(_class = "tooltip",
                                        _title = "%s|%s" % (T("Organisation"),
                                                            T("The organisation/branch this case is assigned to"),
                                                            ),
                                        )
                    user = current.auth.user
                    if user:
                        field.default = user.organisation_id

                    # Individual staff assignment
                    field = ctable.human_resource_id
                    field.label = T("Person Responsible")
                    field.readable = field.writable = True
                    field.widget = None
                    field.comment = None

                    # Filter staff by organisation
                    script = '''$.filterOptionsS3({
'trigger':'sub_dvr_case_organisation_id',
'target':'sub_dvr_case_human_resource_id',
'lookupPrefix':'hrm',
'lookupResource':'human_resource',
'lookupKey':'organisation_id',
'fncRepresent': function(record){return record.person_id},
'optional': true
})'''
                    s3.jquery_ready.append(script)

                    # Visibility and tooltip for consent flag, make mandatory
                    field = ctable.disclosure_consent
                    field.readable = field.writable = True
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other
                    field.comment = DIV(_class="tooltip",
                                        _title="%s|%s" % (T("Consenting to Data Disclosure"),
                                                          T("Is the beneficiary consenting to disclosure of their data towards partner organisations and authorities?"),
                                                          ),
                                        )

                    dtable = s3db.dvr_case_details

                    # Custom label for registered-flag
                    field = dtable.registered
                    field.default = False
                    field.label = T("Registered with Turkish Authorities")
                    field.comment = DIV(_class="tooltip",
                                        _title="%s|%s" % (T("Registered with Turkish Authorities"),
                                                          T("Is the beneficiary officially registered with AFAD/DGMM?"),
                                                          ),
                                        )

                    # Custom label for enrolled_in_school-flag
                    field = dtable.enrolled_in_school
                    field.label = T("Registered at public school")
                    field.comment = DIV(_class="tooltip",
                                        _title="%s|%s" % (T("Registered at Public School"),
                                                          T("If the beneficiary is a child, is (s)he registered at a public school?"),
                                                          ),
                                        )

                    # Custom labels for referral types
                    field = dtable.referral_type_id
                    field.label = T("Referred to Case Management by")

                    field = dtable.activity_referral_type_id
                    field.label = T("Referred to Group Activities by")

                    # Subset of languages for the case-language component
                    ltable = s3db.dvr_case_language
                    field = ltable.language
                    field.requires._select = OrderedDict([
                        ("ar", "Arabic"),
                        ("en", "English"),
                        ("fr", "French"),
                        ("de", "German"),
                        ("el", "Greek"),
                        ("ku", "Kurdish"),
                        ("fa", "Persian"),
                        ("ru", "Russian"),
                        ("sgn", "Sign Languages"),
                        ("tr", "Turkish"),
                        ("ur", "Urdu"),
                    ])

                    # Custom validation for phone number
                    field = s3db.pr_contact.value
                    field.requires = is_turkish_phone_number

                    # Temporarily disable international format requirement
                    # (will be enforced by custom validator anyway)
                    settings.msg.require_international_phone_numbers = False

                    resource = r.resource
                    if r.interactive:

                        from s3 import S3DateFilter, \
                                       S3HierarchyFilter, \
                                       S3LocationFilter, \
                                       S3OptionsFilter, \
                                       S3SQLCustomForm, \
                                       S3SQLInlineComponent, \
                                       S3SQLInlineLink, \
                                       S3TextFilter, \
                                       s3_get_filter_opts

                        # Custom CRUD form
                        crud_form = S3SQLCustomForm(
                                        (T("Reference Number"), "pe_label"),
                                        "dvr_case.status_id",
                                        "dvr_case.date",
                                        "case_details.referral_type_id",
                                        "case_details.activity_referral_type_id",
                                        "dvr_case.organisation_id",
                                        "dvr_case.human_resource_id",
                                        "first_name",
                                        #"middle_name",
                                        "last_name",
                                        "person_details.nationality",
                                        "case_details.arrival_date",
                                        "date_of_birth",
                                        "gender",
                                        "case_details.enrolled_in_school",
                                        "person_details.marital_status",
                                        "case_details.registered",
                                        S3SQLInlineComponent(
                                                "individual_id",
                                                fields = [("", "value"),
                                                          ],
                                                filterby = {"field": "tag",
                                                            "options": "INDIVIDUAL_ID",
                                                            },
                                                label = T("Individual ID Number"),
                                                multiple = False,
                                                name = "individual_id",
                                                #required = True,
                                                ),
                                        S3SQLInlineComponent(
                                                "family_id",
                                                fields = [("", "value"),
                                                          ],
                                                filterby = {"field": "tag",
                                                            "options": "FAMILY_ID",
                                                            },
                                                label = T("Family ID Number"),
                                                multiple = False,
                                                name = "family_id",
                                                #required = True,
                                                ),
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
                                        S3SQLInlineLink("education_level",
                                                        field = "level_id",
                                                        multiple = False,
                                                        ),
                                        S3SQLInlineLink("occupation_type",
                                                        label = T("Current Occupation"),
                                                        field = "occupation_type_id",
                                                        ),
                                        S3SQLInlineComponent(
                                                "case_language",
                                                fields = ["language",
                                                          "quality",
                                                          "comments",
                                                          ],
                                                label = T("Language / Communication Mode"),
                                                explicit_add = T("Add Language"),
                                                ),
                                        "dvr_case.disclosure_consent",
                                        "dvr_case.comments",
                                        (T("Invalid Record"), "dvr_case.archived"),
                                        )

                        opt_yes_no = {True: T("Yes"),
                                      False: T("No"),
                                      }

                        # Retain (+adapt) the status-filter widget
                        status_filter = None
                        filter_widgets = resource.get_config("filter_widgets")
                        if filter_widgets:
                            for widget in filter_widgets:
                                if widget.field == "dvr_case.status_id":
                                    status_filter = widget
                                    status_filter.opts.default = None
                                    status_filter.opts.hidden = "closed" in get_vars
                                    break

                        # Limit HR filter options to selectable HRs
                        requires = ctable.human_resource_id.requires
                        if hasattr(requires, "options"):
                            hr_filter_opts = dict(opt for opt in requires.options() if opt[0])
                        else:
                            hr_filter_opts = None

                        # Limit gender filter options
                        gender_opts = dict(s3db.pr_gender_opts)
                        del gender_opts[1] # Remove "unknown"

                        # Custom filter widgets
                        filter_widgets = [

                            # Standard filters
                            S3TextFilter(["pe_label",
                                          "first_name",
                                          "middle_name",
                                          "last_name",
                                          "individual_id.value",
                                          "family_id.value",
                                          "dvr_case.reference",
                                          "dvr_case.comments",
                                          ],
                                          label = T("Search"),
                                          comment = T("You can search by name, ID or reference number"),
                                          ),
                            S3TextFilter(["phone.value"],
                                         label = T("Phone"),
                                         ),

                            # Extended filters (initially hidden)
                            S3OptionsFilter("dvr_case.organisation_id",
                                            #label = T("Branch"),
                                            options = s3_get_filter_opts("org_organisation"),
                                            hidden = True,
                                            ),
                            S3OptionsFilter("person_details.nationality",
                                            #label = T("Nationality"),
                                            hidden = True,
                                            ),
                            S3OptionsFilter("gender",
                                            options = gender_opts,
                                            hidden = True,
                                            ),
                            # Virtual field filter not scalable
                            #S3OptionsFilter("age_group",
                            #                hidden = True,
                            #                ),
                            S3HierarchyFilter("dvr_case_activity.service_id",
                                              lookup = "org_service",
                                              none = "None",
                                              hidden = True,
                                              ),
                            S3HierarchyFilter("dvr_case_activity.need__link.need_id",
                                              lookup = "dvr_need",
                                              label = T("Protection Response Sector"),
                                              hidden = True,
                                              ),
                            S3HierarchyFilter("dvr_case_activity.vulnerability_type__link.vulnerability_type_id",
                                              lookup = "dvr_vulnerability_type",
                                              label = "Protection Assessment",
                                              hidden = True,
                                              ),
                            S3OptionsFilter("dvr_case_activity.project_id",
                                            options = s3_get_filter_opts("project_project"),
                                            hidden = True,
                                            ),
                            S3OptionsFilter("dvr_case.human_resource_id",
                                            options = hr_filter_opts,
                                            hidden = True,
                                            ),
                            # Not scalable:
                            #S3LocationFilter("address.location_id",
                            #                 hidden = True,
                            #                 ),
                            S3OptionsFilter("person_details.marital_status",
                                            options = s3db.pr_marital_status_opts,
                                            hidden = True,
                                            ),
                            S3OptionsFilter("case_details.registered",
                                            cols = 2,
                                            hidden = True,
                                            options = opt_yes_no,
                                            ),
                            S3OptionsFilter("case_details.enrolled_in_school",
                                            cols = 2,
                                            hidden = True,
                                            options = opt_yes_no,
                                            ),
                            S3DateFilter("date_of_birth",
                                         #label = T("Date of Birth"),
                                         hidden = True,
                                         ),
                            S3DateFilter("dvr_case.date",
                                         #label = T("Registration Date"),
                                         hidden = True,
                                         ),
                            S3DateFilter("dvr_case_activity.activity_id$start_date",
                                         label = T("Activity Start Date"),
                                         hidden = True,
                                         ),
                            S3DateFilter("dvr_case_activity.activity_id$end_date",
                                         label = T("Activity End Date"),
                                         hidden = True,
                                         ),
                            S3DateFilter("dvr_case_activity.start_date",
                                         label = T("Protection Response Opened on"),
                                         hidden = True,
                                         ),
                            ]

                        if status_filter:
                            filter_widgets.insert(2, status_filter)

                        # Update configuration
                        resource.configure(crud_form = crud_form,
                                           filter_widgets = filter_widgets,
                                           )

                    # Custom list fields (must be outside of r.interactive)
                    list_fields = [(T("Ref.No."), "pe_label"),
                                   "first_name",
                                   #"middle_name",
                                   "last_name",
                                   (T("Phone"), "phone.value"),
                                   "date_of_birth",
                                   "gender",
                                   "person_details.nationality",
                                   (T("ID"), "individual_id.value"),
                                   (T("Family ID"), "family_id.value"),
                                   "dvr_case.date",
                                   "dvr_case.status_id",
                                   ]

                    resource.configure(list_fields = list_fields,
                                       listadd = False,
                                       addbtn = True,
                                       )

                    if r.method == "report":

                        # Representation of record IDs in ID aggregations
                        resource.table.id.represent = s3db.pr_PersonRepresent()

                        report_fields = ("gender",
                                         "person_details.nationality",
                                         "dvr_case.status_id",
                                         "dvr_case_activity.service_id",
                                         (T("Protection Response Sector"),"dvr_case_activity.dvr_case_activity_need.need_id"),
                                         (T("Protection Assessment"), "dvr_case_activity.dvr_vulnerability_type_case_activity.vulnerability_type_id"),
                                         "age_group",
                                         "address.location_id$L2",
                                         "dvr_case.date",
                                         )

                        report_facts = [(T("Number of Beneficiaries"), "count(id)"),
                                        ]

                        report_options = {"rows": report_fields,
                                          "cols": report_fields,
                                          "fact": report_facts,
                                          #"defaults": {
                                          #    "rows": "gender",
                                          #    "cols": "person_details.nationality",
                                          #    "fact": report_facts[0],
                                          #    }
                                          }

                        # Drop DoB extra field unless age_group is used as report axis,
                        # NB does not detect age_group as default axis, so this would
                        #    require a manual workaround
                        if "~.age_group" not in (get_vars.get("rows"),
                                                 get_vars.get("cols")):
                            extra_fields = resource.get_config("extra_fields")
                            if extra_fields:
                                extra_fields = [s for s in extra_fields
                                                  if s != "date_of_birth"]
                            resource.configure(extra_fields = extra_fields or None)

                        resource.configure(report_options = report_options,
                                           )

                elif r.component_name == "evaluation":

                    s3.stylesheets.append("../themes/STL/evaluation.css")

            elif controller == "hrm":

                if not r.component:

                    table = s3db.pr_person_details
                    field = table.marital_status
                    field.readable = field.writable = False
                    field = table.religion
                    field.readable = field.writable = False

                elif r.method == "record" or \
                     r.component_name == "human_resource":

                    table = s3db.hrm_human_resource
                    field = table.site_id
                    field.readable = field.writable = False

            return result
        s3.prep = custom_prep

        standard_postp = s3.postp
        def custom_postp(r, output):

            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            # Remove subtitle on case tab
            if r.component_name == "dvr_case" and \
               isinstance(output, dict) and "subtitle" in output:
                output["subtitle"] = None

            return output
        s3.postp = custom_postp

        # Custom rheader tabs
        if current.request.controller == "dvr":
            attr = dict(attr)
            attr["rheader"] = stl_dvr_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    # Staff Module
    #
    settings.hrm.use_code = True
    settings.hrm.use_skills = False
    settings.hrm.use_address = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_id = False
    settings.hrm.use_trainings = False

    settings.hrm.staff_departments = False
    settings.hrm.teams = False
    settings.hrm.staff_experience = False

    def customise_hrm_human_resource_controller(**attr):

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

            if r.controller == "hrm":

                resource = r.resource

                # Hide "Facility" from form (unused)
                table = resource.table
                field = table.site_id
                field.readable = field.writable = False

                # Don't need Location/Facility filters either
                std_filters = resource.get_config("filter_widgets")
                filter_widgets = []
                for filter_widget in std_filters:
                    if filter_widget.field in ("location_id", "site_id"):
                        continue
                    filter_widgets.append(filter_widget)

                # Custom list fields
                list_fields = ["person_id",
                               "code",
                               "job_title_id",
                               "organisation_id",
                               (T("Email"), "email.value"),
                               (settings.get_ui_label_mobile_phone(), "phone.value"),
                               ]

                # Update resource config
                resource.configure(list_fields = list_fields,
                                   filter_widgets = filter_widgets,
                                   )

                # Sort filterOptionsS3 results alphabetically
                if r.representation == "json":
                    resource.configure(orderby = ["pr_person.first_name",
                                                  "pr_person.middle_name",
                                                  "pr_person.last_name",
                                                  ],
                                       )
            return result
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # =========================================================================
    # Organisation Registry
    #
    settings.org.branches = True
    settings.org.services_hierarchical = True

    # Uncomment this to make tree view the default for "Branches" tab
    #settings.org.branches_tree_view = True

    def customise_org_organisation_controller(**attr):

        tabs = [(T("Basic Details"), None),
                (T("Staff & Volunteers"), "human_resource"),
                ]

        if settings.get_org_branches():
            if settings.get_org_branches_tree_view():
                branches = "hierarchy"
            else:
                branches = "branch"
            tabs.insert(1, (T("Branches"), branches))

        org_rheader = lambda r, tabs=tabs: current.s3db.org_rheader(r, tabs=tabs)

        attr = dict(attr)
        attr["rheader"] = org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        s3db = current.s3db

        s3db.add_components("org_facility",
                            org_room = "site_id",
                            )

        # Custom rheader
        attr = dict(attr)
        attr["rheader"] = stl_org_rheader

        return attr

    settings.customise_org_facility_controller = customise_org_facility_controller

    # -------------------------------------------------------------------------
    def customise_org_service_controller(**attr):

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

            # Prevent name/parent change for service categories
            # with dependent functionality:
            record = r.record
            if record and \
               record.name in (INDIVIDUAL_SUPPORT, MENTAL_HEALTH) and \
               not record.parent:

                field = r.table.name
                field.writable = False

                field = r.table.parent
                field.readable = field.writable = False

                # @todo: delete should be prevented too?
                #r.resource.configure(deletable = False)

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_org_service_controller = customise_org_service_controller

    # =========================================================================
    # Project Module
    #
    settings.project.mode_3w = True
    settings.project.codes = True
    settings.project.sectors = False
    settings.project.assign_staff_tab = False

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        s3db = current.s3db

        from s3 import S3SQLCustomForm, \
                       S3TextFilter

        # Simplified form
        crud_form = S3SQLCustomForm("organisation_id",
                                    "code",
                                    "name",
                                    "description",
                                    "comments",
                                    )

        # Custom list fields
        list_fields = ["code",
                       "name",
                       "organisation_id",
                       ]

        # Custom filter widgets
        filter_widgets = [S3TextFilter(["name",
                                        "code",
                                        "description",
                                        "organisation_id$name",
                                        "comments",
                                        ],
                                        label = current.T("Search"),
                                       ),
                          ]

        s3db.configure("project_project",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_project_project_resource = customise_project_project_resource

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        T = current.T
        s3db = current.db
        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Customise fields
            table = s3db.project_project
            field = table.code
            field.label = T("Code")

            return result
        s3.prep = custom_prep


        # Custom rheader
        attr = dict(attr)
        attr["rheader"] = stl_project_rheader

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # =========================================================================
    # Modules
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
        #    name_nice = T("Content Management"),
        #    #description = "Content Management System",
        #    restricted = True,
        #    module_type = 10,
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
        #("req", Storage(
        #    name_nice = T("Requests"),
        #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #   restricted = True,
        #    module_type = 10,
        #)),
        ("project", Storage(
           name_nice = T("Projects"),
           #description = "Tracking of Projects, Activities and Tasks",
           restricted = True,
           module_type = 2
        )),
        #("cr", Storage(
        #    name_nice = T("Camps"),
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
        ("dvr", Storage(
          name_nice = T("Case Management"),
          #description = "Allow affected individuals & households to register to receive compensation and distributions",
          restricted = True,
          module_type = 10,
        )),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("tr", Storage(
        #   name_nice = "Turkish Extensions",
        #   restricted = True,
        #   module_type = None,
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
def stl_dvr_rheader(r, tabs=[]):
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

        if tablename == "pr_person":

            # "Invalid Case" warning
            hint = lambda record: H3(T("Invalid Case"),
                                     _class="alert label",
                                     )

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Contact"), "contacts"),
                        (T("Household"), "household"),
                        (T("Economy"), "economy"),
                        ]

                has_role = current.auth.s3_has_role
                if has_role("CASE_MANAGEMENT"):
                    tabs.append((T("Individual Case Management"), "case_activity"))
                if has_role("GROUP_ACTIVITIES"):
                    tabs.append((T("Group Activities"), "pss_activity"))
                if has_role("MENTAL_HEALTH"):
                    tabs.append((T("Mental Health"), "mh_activity"))

                #tabs.append((T("Evaluation"), "evaluation"))

                case = resource.select(["individual_id.value",
                                        "family_id.value",
                                        "dvr_case.status_id",
                                        "dvr_case.archived",
                                        "dvr_case.organisation_id",
                                        "dvr_case.disclosure_consent",
                                        ],
                                        limit = 1,
                                        represent = True,
                                        raw_data = True,
                                        ).rows

                if not case:
                    return None

                case = case[0]

                case_status = lambda row: case["dvr_case.status_id"]
                archived = case["_row"]["dvr_case.archived"]
                individual_id = lambda row: case["pr_individual_id_person_tag.value"]
                family_id = lambda row: case["pr_family_id_person_tag.value"]
                organisation_id = lambda row: case["dvr_case.organisation_id"]
                name = lambda row: s3_fullname(row)

                raw = case._row

                # Render disclosure consent flag as colored label
                consent = raw["dvr_case.disclosure_consent"]
                labels = {"Y": "success", "N/A": "warning", "N": "alert"}
                def disclosure(row):
                    _class = labels.get(consent, "secondary")
                    return SPAN(case["dvr_case.disclosure_consent"],
                                _class = "%s label" % _class,
                                )

                rheader_fields = [[(T("Ref.No."), "pe_label"),
                                   (T("ID"), individual_id),
                                   (T("Organisation"), organisation_id),
                                   (T("Data Disclosure"), disclosure),
                                   ],
                                  [(T("Name"), name),
                                   (T("Family ID"), family_id),
                                   (T("Case Status"), case_status),
                                   ],
                                  ["date_of_birth",
                                   ],
                                  ]

                if archived:
                    rheader_fields.insert(0, [(None, hint)])

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# =============================================================================
def stl_project_rheader(r, tabs=[]):
    """ PROJECT custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, \
                   S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "project_project":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

                rheader_fields = [[(T("Code"), "code"),
                                   ],
                                  [(T("Name"), "name"),
                                   ],
                                  [(T("Organisation"), "organisation_id"),
                                   ],
                                  ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# =============================================================================
def stl_org_rheader(r, tabs=[]):
    """ ORG custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, \
                   S3ResourceHeader

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
                        (T("Rooms"), "room"),
                        ]

                def facility_type_lookup(record):
                    db = current.db
                    ltable = db.org_site_facility_type
                    ttable = db.org_facility_type
                    query = (ltable.site_id == record.site_id) & \
                            (ltable.facility_type_id == ttable.id)
                    rows = db(query).select(ttable.name)
                    if rows:
                        return ", ".join([row.name for row in rows])
                    else:
                        return current.messages["NONE"]

                rheader_fields = [["name", "organisation_id", "email"],
                                  [(T("Facility Type"), facility_type_lookup),
                                   "location_id", "phone1"],
                                  ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# =============================================================================
def stl_case_activity_owner_group(table, row):
    """
        Determine the owner group (auth_group.id) for dvr_case_activity
        records from the service type

        @param table: the table (dvr_case_activity)
        @param row: the case activity record
    """

    db = current.db
    s3db = current.s3db

    # Get the root service name
    stable = s3db.org_service
    rtable = stable.with_alias("root_service")
    left = [stable.on(stable.id == table.service_id),
            rtable.on(rtable.id == stable.root_service),
            ]
    query = (table.id == row[table._id])
    row = db(query).select(rtable.name,
                           left = left,
                           limitby = (0, 1),
                           ).first()
    if not row:
        return None

    root_service_name = row.name
    if not root_service_name:
        return None

    # Determine the owner group
    if root_service_name == INDIVIDUAL_SUPPORT:
        owner_group_uuid = "CASE_MANAGEMENT"
    elif root_service_name == MENTAL_HEALTH:
        owner_group_uuid = "MENTAL_HEALTH"
    else:
        owner_group_uuid = "GROUP_ACTIVITIES"

    gtable = current.auth.settings.table_group
    query = (gtable.uuid == owner_group_uuid) & \
            (gtable.deleted != True)
    group = db(query).select(gtable.id,
                             limitby = (0, 1),
                             ).first()

    return group.id if group else None

# END =========================================================================
