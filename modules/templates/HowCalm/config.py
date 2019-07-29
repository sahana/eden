# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for HowCalm
    """

    T = current.T

    settings.base.system_name = T("HowCalm")
    settings.base.system_name_short = T("HowCalm")

    # PrePopulate data
    settings.base.prepopulate += ("HowCalm",)
    settings.base.prepopulate_demo += ("HowCalm/Demo",)

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "HowCalm"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_requests_mobile_phone = True
    settings.auth.registration_mobile_phone_mandatory = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    settings.gis.poi_create_resources = []
    settings.gis.location_represent_address_only = True
    # 4500 Facs would be nice but this hits server timeout limits so we have to currently accept the default 2000
    #settings.gis.max_features = 4500
    # Reduce the default a little to have a more responsive site
    settings.gis.max_features = 1500

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    #gis_levels = ("L2", "L3", "L4")

    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("es", "Español"),
    ])

    # Default timezone for users
    settings.L10n.timezone = "US/Eastern"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","

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
    settings.security.policy = 7 # Organisation-ACLs

    # Record Approval
    settings.auth.record_approval = True
    settings.auth.record_approval_required_for = ("org_organisation",
                                                  )

    # Open records in read mode rather then edit by default
    settings.ui.open_read_first = True
    settings.ui.update_label = "Edit"
    settings.ui.export_formats = ("pdf", "xls")

    settings.pr.hide_third_gender = False

    settings.hrm.compose_button = False
    settings.hrm.staff_label = "Contacts"

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
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
    ])

    # -------------------------------------------------------------------------
    def howcalm_rheader(r):
        """
            Just used to hide default rheader
            - all Record Details now done in profile_header
        """

        # Just used to hide default rheader
        return None

        if r.representation != "html":
            # RHeaders only used in interactive views
            return None

        # Need to use this format as otherwise req_match?viewing=org_office.x
        # doesn't have an rheader
        from s3 import s3_rheader_resource
        tablename, record = s3_rheader_resource(r)

        if record is None:
            # List or Create form: rheader makes no sense here
            return None

        T = current.T

        if tablename == "pr_person":
            # Details for Read in profile_header
            # Edit has no need of header
            return None

            #tabs = [(T("Basic Details"), None),
            #        ]

            #from s3 import s3_rheader_tabs
            #rheader_tabs = s3_rheader_tabs(r, tabs)

            from gluon import A, DIV, TABLE, TR, TH, URL

            from s3 import s3_fullname
            record_data = TABLE(TR(TH(s3_fullname(record), _colspan=2)))
            record_data_append = record_data.append

            record_id = record.id

            db = current.db
            s3db = current.s3db

            ptagtable = s3db.pr_person_tag
            query = (ptagtable.person_id == record_id) & \
                    (ptagtable.tag == "religious_title")
            religious_title = db(query).select(ptagtable.value,
                                               limitby = (0, 1)
                                               ).first()
            if religious_title:
                record_data_append(TR(TH("%s: " % T("Religious Title")),
                                      religious_title.value))

            query = (ptagtable.person_id == record_id) & \
                    (ptagtable.tag == "position_title")
            position_title = db(query).select(ptagtable.value,
                                              limitby = (0, 1)
                                              ).first()
            if position_title:
                record_data_append(TR(TH("%s: " % T("Position Title")),
                                      position_title.value))

            hrtable = s3db.hrm_human_resource
            query = (hrtable.person_id == record_id)
            hr = db(query).select(hrtable.organisation_id,
                                  limitby = (0, 1)
                                  ).first()
            if hr:
                organisation_id = hr.organisation_id
                record_data_append(TR(TH("%s: " % T("Organization")),
                                      A(hrtable.organisation_id.represent(organisation_id),
                                        _href = URL(c="org", f="organisation",
                                                    args=[organisation_id, "profile"]),
                                        )
                                      ))

            rheader = DIV(record_data,
                          #rheader_tabs,
                          )

        elif tablename == "org_organisation":
            # Details for Read in profile_header
            # Edit has no need of header
            return None

            tabs = [(T("Basic Details"), None),
                   (T("Contacts"), "person"),
                   (T("Facilities"), "facility"),
                   ]

            from s3 import s3_rheader_tabs
            rheader_tabs = s3_rheader_tabs(r, tabs)

            from gluon import A, DIV, TABLE, TR, TH

            db = current.db
            s3db = current.s3db

            table = s3db.org_organisation

            record_data = TABLE(TR(TH(record.name, _colspan=2)))
            record_data_append = record_data.append

            record_id = record.id

            otagtable = s3db.org_organisation_tag
            query = (otagtable.organisation_id == record_id) & \
                    (otagtable.tag == "org_id")
            org_id = db(query).select(otagtable.value,
                                      limitby = (0, 1)
                                      ).first()
            if org_id:
                record_data_append(TR(TH("%s: " % T("Organization ID")),
                                      org_id.value))

            ltable = s3db.pr_religion_organisation
            query = (ltable.organisation_id == record_id)
            religion = db(query).select(ltable.religion_id,
                                       limitby = (0, 1)
                                       ).first()
            if religion:
                record_data_append(TR(TH("%s: " % T("Religion")),
                                      ltable.religion_id.represent(religion.religion_id)))

            ltable = s3db.org_organisation_organisation_type
            query = (ltable.organisation_id == record_id)
            org_type = db(query).select(ltable.organisation_type_id,
                                        limitby = (0, 1)
                                        ).first()
            if org_type:
                record_data_append(TR(TH("%s: " % ltable.organisation_type_id.label),
                                      ltable.organisation_type_id.represent(org_type.organisation_type_id)))

            website = record.website
            if website:
                record_data_append(TR(TH("%s: " % table.website.label),
                                      A(website, _href=website)))

            ctable = s3db.pr_contact
            query = (table.id == record_id) & \
                    (table.pe_id == ctable.pe_id) & \
                    (ctable.contact_method == "FACEBOOK")
            facebook = db(query).select(ctable.value,
                                        limitby = (0, 1)
                                        ).first()
            if facebook:
                url = facebook.value
                record_data_append(TR(TH("%s: " % T("Facebook")),
                                      A(url, _href=url)))

            oftable = s3db.org_facility
            gtable = s3db.gis_location
            query = (oftable.organisation_id == record_id) & \
                    (oftable.location_id == gtable.id)
            features = db(query).select(gtable.lat,
                                        gtable.lon
                                        )
            map_ = ""
            if len(features) > 0:
                ftable = s3db.gis_layer_feature
                query = (ftable.controller == "org") & \
                        (ftable.function == "facility")
                layer = db(query).select(ftable.layer_id,
                                         limitby=(0, 1)).first()
                if layer:
                    gis = current.gis
                    bbox = gis.get_bounds([f for f in features])
                    map_ = gis.show_map(height = 250,
                                        collapsed = True,
                                        bbox = bbox,
                                        mouse_position = False,
                                        overview = False,
                                        permalink = False,
                                        feature_resources = [{"name": T("Facilities"),
                                                              "id": "rheader_map",
                                                              "active": True,
                                                              "layer_id": layer.layer_id,
                                                              "filter": "~.organisation_id=%s" % record_id,
                                                              }],
                                        )

            rheader = DIV(DIV(record_data,
                              _class = "columns medium-6",
                              ),
                          DIV(map_,
                              _class = "columns medium-6",
                              ),
                          rheader_tabs,
                          )

        elif tablename == "org_facility":
            # Details for Read in profile_header
            # Edit has no need of header
            return None

            #tabs = [(T("Basic Details"), None),
            #        ]

            #from s3 import s3_rheader_tabs
            #rheader_tabs = s3_rheader_tabs(r, tabs)

            from gluon import DIV, TABLE, TR, TH

            db = current.db
            s3db = current.s3db

            table = s3db.org_facility

            record_data = TABLE(TR(TH(record.name, _colspan=2)),
                                TR(TH("%s: " % table.organisation_id.label),
                                      table.organisation_id.represent(record.organisation_id)),
                                )
            record_data_append = record_data.append

            #record_id = record.id
            site_id = record.site_id

            ltable = s3db.org_site_facility_type
            query = (ltable.site_id == site_id)
            fac_type = db(query).select(ltable.facility_type_id,
                                        limitby = (0, 1)
                                        ).first()
            if fac_type:
                record_data_append(TR(TH("%s: " % ltable.facility_type_id.label),
                                      ltable.facility_type_id.represent(fac_type.facility_type_id)))

            location_id = record.location_id
            if location_id:
                record_data_append(TR(TH("%s: " % table.location_id.label),
                                      table.location_id.represent(location_id)))

            stagtable = s3db.org_site_tag
            query = (stagtable.site_id == site_id) & \
                    (stagtable.tag == "congregations")
            congregations = db(query).select(stagtable.value,
                                             limitby = (0, 1)
                                             ).first()
            if congregations:
                record_data_append(TR(TH("%s: " % T("# of Congregations")),
                                      congregations.value))

            query = (stagtable.site_id == site_id) & \
                    (stagtable.tag == "cross_streets")
            cross_streets = db(query).select(stagtable.value,
                                             limitby = (0, 1)
                                             ).first()
            if cross_streets:
                record_data_append(TR(TH("%s: " % T("Cross Streets")),
                                      cross_streets.value))

            stable = s3db.org_site_status
            query = (stable.site_id == site_id)
            status = db(query).select(stable.facility_status,
                                      limitby = (0, 1)
                                      ).first()
            if status:
                record_data_append(TR(TH("%s: " % stable.facility_status.label),
                                      stable.facility_status.represent(status.facility_status)))

            query = (stagtable.site_id == site_id) & \
                    (stagtable.tag == "em_call")
            em_call = db(query).select(stagtable.value,
                                       limitby = (0, 1)
                                       ).first()
            if em_call:
                record_data_append(TR(TH("%s: " % T("Call in Emergency")),
                                      em_call.value))

            query = (stagtable.site_id == site_id) & \
                    (stagtable.tag == "oem_ready")
            oem_ready = db(query).select(stagtable.value,
                                         limitby = (0, 1)
                                         ).first()
            if oem_ready:
                record_data_append(TR(TH("%s: " % T("OEM Ready Receiving Center")),
                                      oem_ready.value))

            query = (stagtable.site_id == site_id) & \
                    (stagtable.tag == "oem_want")
            oem_want = db(query).select(stagtable.value,
                                        limitby = (0, 1)
                                        ).first()
            if oem_want:
                record_data_append(TR(TH("%s: " % T("Want to be an OEM Ready Receiving Center")),
                                      oem_want.value))

            comments = record.comments
            if comments:
                record_data_append(TR(TH("%s: " % table.comments.label),
                                      table.comments.represent(comments)))

            map_ = ""
            if location_id:
                ftable = s3db.gis_layer_feature
                query = (ftable.controller == "org") & \
                        (ftable.function == "facility")
                layer = db(query).select(ftable.layer_id,
                                         limitby=(0, 1)).first()
                if layer:
                    gtable = s3db.gis_location
                    location = db(gtable.id == location_id).select(gtable.lat,
                                                                   gtable.lon,
                                                                   limitby = (0, 1)
                                                                   ).first()
                    map_ = current.gis.show_map(height = 250,
                                                lat = location.lat,
                                                lon = location.lon,
                                                zoom = 15,
                                                collapsed = True,
                                                mouse_position = False,
                                                overview = False,
                                                permalink = False,
                                                feature_resources = [{"name": T("Facility"),
                                                                      "id": "rheader_map",
                                                                      "active": True,
                                                                      "layer_id": layer.layer_id,
                                                                      "filter": "~.id=%s" % record.id,
                                                                      }],
                                                )

            rheader = DIV(DIV(record_data,
                              _class = "columns medium-6"
                              ),
                          DIV(map_,
                              _class = "columns medium-6"
                              ),
                          #rheader_tabs,
                          )

        return rheader

    # -------------------------------------------------------------------------
    def hrm_list_fields(r):
        """
            DRY Helper
        """

        s3db = current.s3db

        if r.representation == "xls":
            # Filtered components
            s3db.add_components("org_organisation",
                                org_organisation_tag = ({"name": "org_id",
                                                         "joinby": "organisation_id",
                                                         "filterby": {"tag": "org_id"},
                                                         "multiple": False,
                                                         },
                                                        ),
                                )

            s3db.add_components("pr_pentity",
                                pr_contact = (# Office Fax:
                                              {"name": "fax",
                                               "joinby": "pe_id",
                                               "filterby": {
                                                    "contact_method": "FAX",
                                                    },
                                               },
                                              # Personal Email:
                                              {"name": "personal_email",
                                               "joinby": "pe_id",
                                               "filterby": {
                                                    "contact_method": "EMAIL",
                                                    "priority": 2,
                                                    },
                                               },
                                              # Work Email:
                                              {"name": "work_email",
                                               "joinby": "pe_id",
                                               "filterby": {
                                                    "contact_method": "EMAIL",
                                                    "priority": 1,
                                                    },
                                               },
                                              )
                                )

            list_fields = [(T("First Name"), "person_id$first_name"),
                           (T("Middle Name"), "person_id$middle_name"),
                           (T("Last Name"), "person_id$last_name"),
                           (T("Organization"), "organisation_id"),
                           (T("Organization ID"), "organisation_id$org_id.value"),
                           (T("Type"), "job_title_id"),
                           (T("Languages Spoken"), "person_id$competency.skill_id"),
                           (T("Other Languages"), "person_id$other_languages.value"),
                           (T("Religious Title"), "person_id$religious_title.value"),
                           (T("Position Title"), "person_id$position_title.value"),
                           (T("Pronouns"), "person_id$gender"),
                           (T("Mailing Address"), "person_id$address.location_id"),
                           (T("Cell Phone"), "person_id$phone.value"),
                           (T("Office Phone"), "person_id$work_phone.value"),
                           (T("Emergency Phone"), "person_id$home_phone.value"),
                           (T("Office Fax"), "person_id$fax.value"),
                           (T("Personal Email"), "person_id$personal_email.value"),
                           (T("Work Email"), "person_id$work_email.value"),
                           #(T("ECDM"), "person_id$em_comms.value"),
                           ]
        else:
            list_fields = [(T("Person Name"), "person_id"),
                           (T("Organization"), "organisation_id"),
                           (T("Type"), "job_title_id"),
                           (T("Languages Spoken"), "person_id$competency.skill_id"),
                           (T("Religious Title"), "person_id$religious_title.value"),
                           (T("Position Title"), "person_id$position_title.value"),
                           #(T("ECDM"), "person_id$em_comms.value"),
                           ]

        s3db.configure("hrm_human_resource",
                       list_fields = list_fields,
                       )

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Contact"),
            title_display = T("Contact Details"),
            title_list = T("Contact Catalog"),
            title_update = T("Edit Contact"),
            label_list_button = T("List Contacts"),
            label_delete_button = T("Delete Contact"),
            msg_record_created = T("Contact added"),
            msg_record_modified = T("Contact updated"),
            msg_record_deleted = T("Contact deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        # Ensure we have the filtered components
        customise_pr_person_resource(r, "pr_person")

        current.s3db.configure("hrm_human_resource",
                               # We use Custom CRUD button to open Person perspective
                               listadd = False,
                               )

        hrm_list_fields(r)

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            mine = r.get_vars.get("mine")
            if mine:
                from s3 import FS
                filter_ = (FS("organisation_id") == current.auth.user.organisation_id)
                r.resource.add_filter(filter_)
                s3.crud_strings["hrm_human_resource"].title_list = T("My Contacts")

            s3db = current.s3db

            hrm_list_fields(r)

            from s3 import S3HierarchyFilter, \
                           S3NotEmptyFilter, \
                           S3OptionsFilter, \
                           S3TextFilter

            s3db.configure("pr_religion",
                           hierarchy_levels = ["Religion",
                                               "Faith Tradition",
                                               "Denomination",
                                               "Judicatory Body",
                                               ],
                           )

            s3db.org_organisation_organisation_type.organisation_type_id.label = T("Religion")

            filter_widgets = [S3TextFilter(["person_id$first_name",
                                            "person_id$middle_name",
                                            "person_id$last_name",
                                            "person_id$email.value",
                                            ],
                                           label = T("Search"),
                                           ),
                              S3HierarchyFilter("organisation_id$religion_organisation.religion_id",
                                                label = False,
                                                #label = T("Religion"),
                                                widget = "cascade",
                                                leafonly = False,
                                                cascade = True,
                                                ),
                              #S3OptionsFilter("organisation_id",
                              #                search = True,
                              #                header = "",
                              #                #hidden = True,
                              #                ),
                              #S3LocationFilter("location_id",
                              #                 label = T("Location"),
                              #                 #hidden = True,
                              #                 ),
                              S3OptionsFilter("job_title_id",
                                              label = T("Type"),
                                              #hidden = True,
                                              ),
                              #S3OptionsFilter("person_id$em_comms.value",
                              #                label = T("ECDM"),
                              #                #hidden = True,
                              #                options = {"Y": T("Yes"),
                              #                           "N": T("No"),
                              #                           },
                              #                #widget = "groupedopts",
                              #                cols = 2,
                              #                ),
                              S3OptionsFilter("person_id$competency.skill_id",
                                              label = T("Languages Spoken"),
                                              #hidden = True,
                                              ),
                              S3OptionsFilter("organisation_id$facility.location_id$L3",
                                              label = T("Location"),
                                              #hidden = True,
                                              ),
                              S3OptionsFilter("organisation_id$facility.location_id$addr_postcode",
                                              label = T("Zipcode"),
                                              #hidden = True,
                                              ),
                              S3NotEmptyFilter("person_id$email.value",
                                               label = T("Has Email"),
                                               # To default to 'on'
                                               #default = [None],
                                               ),
                              S3NotEmptyFilter(["person_id$phone.value",
                                                "person_id$home_phone.value",
                                                "person_id$work_phone.value",
                                                ],
                                               label = T("Has Phone"), # Any of these
                                               # To default to 'on'
                                               #default = [None],
                                               ),
                              ]

            s3db.configure("hrm_human_resource",
                           filter_widgets = filter_widgets,
                           )

            return result
        s3.prep = custom_prep

        standard_postp = s3.postp
        def custom_postp(r, output):
            if r.representation == "plain":
                # Call standard_postp
                if callable(standard_postp):
                    output = standard_postp(r, output)

            elif r.interactive and r.method == "summary":
                # Custom Create Button
                from gluon import A, DIV, URL
                add_btn = DIV(DIV(DIV(A(T("Create Contact"),
                                        _class = "action-btn",
                                        _href = URL(c="pr", f="person", args="create"),
                                        ),
                                      _id = "list-btn-add",
                                      ),
                                  _class = "widget-container with-tabs",
                                  ),
                              _class = "section-container",
                              )
                output["common"][0] = add_btn

                # Action Buttons should launch Person Profile page
                from s3 import S3CRUD

                profile_url = URL(c="pr", f="person",
                                  args = ["profile"],
                                  vars = {"human_resource.id": "[id]"})

                S3CRUD.action_buttons(r,
                                      editable = False,
                                      read_url = profile_url,
                                      )

            return output
        s3.postp = custom_postp

        # Never used: always open individual records in person perspective
        #attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_msg_contact_resource(r, tablename):

        from s3 import S3SQLCustomForm#, S3SQLInlineComponent

        s3db = current.s3db

        # Filtered components
        s3db.add_components("msg_contact",
                            msg_tag = ({"name": "position",
                                        "joinby": "message_id",
                                        "filterby": {"tag": "position"},
                                        "multiple": False,
                                        },
                                       ),
                            )

        crud_fields = [(T("Topic"), "subject"),
                       "name",
                       (T("Position"), "position.value"),
                       "phone",
                       "from_address",
                       "body",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields)

        s3db.configure("msg_contact",
                       crud_form = crud_form,
                       )

    settings.customise_msg_contact_resource = customise_msg_contact_resource

    # -------------------------------------------------------------------------
    def customise_msg_contact_controller(**attr):

        s3 = current.response.s3

        #standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            #if callable(standard_prep):
            #    result = standard_prep(r)
            #else:
            result = True

            if not current.auth.s3_has_role("MANAGER"):
                r.method = "create"

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_msg_contact_controller = customise_msg_contact_controller

    # -------------------------------------------------------------------------
    def org_facility_onaccept(form):
        """
            Geocode Street Addresses blindly
        """

        location_id = form.vars.get("location_id")
        if not location_id:
            return

        db = current.db
        gis = current.gis
        gtable = current.s3db.gis_location
        location = db(gtable.id == location_id).select(gtable.id,
                                                       gtable.addr_street,
                                                       #gtable.addr_postcode,
                                                       #gtable.parent,
                                                       limitby = (0, 1)
                                                       ).first()

        # We want to populate the Postcode field, so cannot use GeoPy but need
        # to call the Google API directly
        #parent = location.parent
        #if parent:
        #    Lx_ids = gis.get_parents(parent, ids_only=True)
        #    if Lx_ids:
        #        Lx_ids.append(parent)
        #    else:
        #        Lx_ids = [parent]
        #else:
        #    query = (gtable.name == "New York City") & \
        #            (gtable.level == "L2")
        #    NYC = db(query).select(gtable.id,
        #                           limitby = (0, 1)
        #                           ).first()
        #    parent = NYC.id
        #    Lx_ids = [parent]

        #results = gis.geocode(location.addr_street,
        #                      location.addr_postcode,
        #                      Lx_ids)
        #if isinstance(results, basestring):
        #    # Error, Warn
        #    current.log.warning("Geocoder: %s" % results)
        #else:
        #    location.update_record(lat = results["lat"],
        #                           lon = results["lon"],
        #                           inherited = False,
        #                           parent = parent,
        #                           )

        query = (gtable.name == "New York City") & \
                (gtable.level == "L2")
        NYC = db(query).select(gtable.id,
                               gtable.lat_min,
                               gtable.lat_max,
                               gtable.lon_min,
                               gtable.lon_max,
                               limitby = (0, 1)
                               ).first()

        bounds = "%s,%s|%s,%s" % (NYC.lat_min, NYC.lon_min, NYC.lat_max, NYC.lon_max)

        NYC = NYC.id

        import requests
        params = {"address": location.addr_street,
                  "key":settings.get_gis_api_google(),
                  "bounds": bounds,
                  }
        r = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
        if r.status_code == requests.codes.ok:
            results = r.json()
            if results["status"] == "OK":
                results = results["results"][0]
                loc = results["geometry"]["location"]
                postcode = None
                parent = None
                for c in results["address_components"]:
                    types = c["types"]
                    if  "postal_code" in types:
                        postcode = c["short_name"]
                    elif "sublocality_level_1" in types:
                        L3 = c["short_name"]
                        if L3 == "Bronx":
                            # Google sometimes returns just 'Bronx'
                            L3 = "The Bronx"
                        query = (gtable.name == L3) & \
                                (gtable.level == "L3")
                        L3 = db(query).select(gtable.id,
                                              limitby = (0, 1)
                                              ).first()
                        if L3:
                            parent = L3.id
                if not parent:
                    parent = NYC
                location.update_record(lat = loc["lat"],
                                       lon = loc["lng"],
                                       addr_postcode = postcode,
                                       inherited = False,
                                       parent = parent,
                                       wkt = None,
                                       )
                gis.update_location_tree({"id": location.id})

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE, URL

        from s3 import IS_INT_AMOUNT, \
                       S3LocationSelector, \
                       S3SQLCustomForm, S3SQLInlineLink#, S3SQLInlineComponent

        s3db = current.s3db

        table = s3db.org_facility
        f = table.location_id
        f.label = T("Physical Address")
        f.represent = s3db.gis_LocationRepresent(show_link = True,
                                                 controller = "org",
                                                 func = "facility",
                                                 )
        f.widget = S3LocationSelector(levels = ["L3"],
                                      show_address = True,
                                      show_postcode = True,
                                      show_map = False,
                                      )

        if r.method in ("profile", "read"):
            profile_url = URL(c="org", f="organisation",
                              args = ["[id]", "profile"],
                              )
            table.organisation_id.represent = s3db.org_OrganisationRepresent(show_link = True,
                                                                             linkto = profile_url)

        # Filtered components
        s3db.add_components("org_facility",
                            org_site_tag = ({"name": "congregations",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "congregations"},
                                             "multiple": False,
                                             },
                                            {"name": "cross_streets",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "cross_streets"},
                                             "multiple": False,
                                             },
                                            {"name": "em_call",
                                             "joinby": "site_id",
                                             "filterby": {"tag": "em_call"},
                                             "multiple": False,
                                             },
                                            #{"name": "oem_ready",
                                            # "joinby": "site_id",
                                            # "filterby": {"tag": "oem_ready"},
                                            # "multiple": False,
                                            # },
                                            #{"name": "oem_want",
                                            # "joinby": "site_id",
                                            # "filterby": {"tag": "oem_want"},
                                            # "multiple": False,
                                            # },
                                            ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        integer_represent = IS_INT_AMOUNT.represent

        congregations = components_get("congregations")
        f = congregations.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        em_call = components_get("em_call")
        f = em_call.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        #oem_ready = components_get("oem_ready")
        #f = oem_ready.table.value
        #f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        #f.represent = lambda v: T("yes") if v == "Y" else T("no")
        ##from s3 import S3TagCheckboxWidget
        #f.widget = S3TagCheckboxWidget(on="Y", off="N")
        #f.default = "N"

        #oem_want = components_get("oem_want")
        #f = oem_want.table.value
        #f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        #f.represent = lambda v: T("yes") if v == "Y" else T("no")
        ##from s3 import S3TagCheckboxWidget
        #f.widget = S3TagCheckboxWidget(on="Y", off="N")
        #f.default = "N"

        crud_fields = ["organisation_id",
                       "name",
                       S3SQLInlineLink("facility_type",
                                       label = T("Facility Type"),
                                       field = "facility_type_id",
                                       multiple = False,
                                       widget = "groupedopts",
                                       cols = 3,
                                       ),
                       "location_id",
                       (T("# of Congregations at this Facility"), "congregations.value"),
                       (T("Cross Streets"), "cross_streets.value"),
                       (T("Building Status"), "status.facility_status"),
                       (T("Call in Emergency"), "em_call.value"),
                       #(T("OEM Ready Receiving Center"), "oem_ready.value"),
                       #(T("Want to be an OEM Ready Receiving Center"), "oem_want.value"),
                       "comments",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields)

        from s3 import S3OptionsFilter, S3TextFilter #, S3HierarchyFilter, S3LocationFilter
        filter_widgets = [
            S3TextFilter(["name"],
                         label = T("Search"),
                         comment = T("Search by facility name. You can use * as wildcard."),
                         _class = "filter-search",
                         ),
            #S3HierarchyFilter("religion_organisation.religion_id",
            #                  label = False, #T("Religion"),
            #                  widget = "cascade",
            #                  leafonly = False,
            #                  cascade = True,
            #                  ),
            S3OptionsFilter("site_facility_type.facility_type_id",
                            label = T("Type"),
                            ),
            S3OptionsFilter("organisation_id",
                            label = T("Organization"),
                            ),
            S3OptionsFilter("location_id$L3",
                            label = T("Location"),
                            ),
            #S3LocationFilter("location_id",
            #                 label = T("Location"),
            #                 levels = gis_levels,
            #                 #hidden = True,
            #                 ),
            #S3OptionsFilter("location_id$addr_postcode",
            #                label = T("Zipcode"),
            #                #hidden = True,
            #                ),
            ]

        if r.representation == "xls":
            # Filtered components
            s3db.add_components("org_organisation",
                                org_organisation_tag = ({"name": "org_id",
                                                         "joinby": "organisation_id",
                                                         "filterby": {"tag": "org_id"},
                                                         "multiple": False,
                                                         },
                                                        ),
                                )
            list_fields = ["organisation_id",
                           (T("Organization ID"), "organisation_id$org_id.value"),
                           "name",
                           (T("Facility Type"), "site_facility_type.facility_type_id"),
                           (T("Borough"), "location_id$L3"),
                           (T("Street Address"), "location_id$addr_street"),
                           (T("Zipcode"), "location_id$addr_postcode"),
                           (T("# of Congregations at this Facility"), "congregations.value"),
                           (T("Cross Streets"), "cross_streets$value"),
                           (T("Building Status"), "status.facility_status"),
                           (T("Call?"), "em_call.value"),
                           #(T("OEM RRC"), "oem_ready.value"),
                           "comments",
                           ]
        else:
            list_fields = [#"organisation_id",
                           #"name",
                           (T("Physical Address"), "location_id$addr_street"),
                           (T("# of Congregations at this Facility"), "congregations.value"),
                           (T("Building Status"), "status.facility_status"),
                           (T("Call?"), "em_call.value"),
                           #(T("OEM RRC"), "oem_ready.value"),
                           ]
            if r.function == "facility":
                list_fields.insert(0, "organisation_id")

        profile_url = URL(c="org", f="facility",
                          args = ["[id]", "profile"])

        s3db.configure("org_facility",
                       create_next = profile_url,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       update_next = profile_url,
                       )

        s3db.add_custom_callback("org_facility", "onaccept",
                                 org_facility_onaccept)

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            mine = r.get_vars.get("mine")
            if mine:
                from s3 import FS
                filter_ = (FS("organisation_id") == current.auth.user.organisation_id)
                r.resource.add_filter(filter_)
                s3.crud_strings["org_facility"].title_list = T("My Facilities")

            elif r.method == "profile":
                # Profile Configuration
                from gluon import DIV, H2, TABLE, TR, TH

                db = current.db
                s3db = current.s3db
                record = r.record

                table = s3db.org_facility

                record_data = TABLE(TR(TH(record.name, _colspan=2)),
                                    TR(TH("%s: " % table.organisation_id.label),
                                          table.organisation_id.represent(record.organisation_id)),
                                    )
                record_data_append = record_data.append

                record_id = record.id
                site_id = record.site_id

                ltable = s3db.org_site_facility_type
                query = (ltable.site_id == site_id)
                fac_type = db(query).select(ltable.facility_type_id,
                                            limitby = (0, 1)
                                            ).first()
                if fac_type:
                    record_data_append(TR(TH("%s: " % ltable.facility_type_id.label),
                                          ltable.facility_type_id.represent(fac_type.facility_type_id)))

                location_id = record.location_id
                if location_id:
                    record_data_append(TR(TH("%s: " % table.location_id.label),
                                          table.location_id.represent(location_id)))

                stagtable = s3db.org_site_tag
                query = (stagtable.site_id == site_id) & \
                        (stagtable.tag == "congregations")
                congregations = db(query).select(stagtable.value,
                                                 limitby = (0, 1)
                                                 ).first()
                if congregations:
                    record_data_append(TR(TH("%s: " % T("# of Congregations")),
                                          congregations.value))

                query = (stagtable.site_id == site_id) & \
                        (stagtable.tag == "cross_streets")
                cross_streets = db(query).select(stagtable.value,
                                                 limitby = (0, 1)
                                                 ).first()
                if cross_streets:
                    record_data_append(TR(TH("%s: " % T("Cross Streets")),
                                          cross_streets.value))

                stable = s3db.org_site_status
                query = (stable.site_id == site_id)
                status = db(query).select(stable.facility_status,
                                          limitby = (0, 1)
                                          ).first()
                if status:
                    record_data_append(TR(TH("%s: " % stable.facility_status.label),
                                          stable.facility_status.represent(status.facility_status)))

                query = (stagtable.site_id == site_id) & \
                        (stagtable.tag == "em_call")
                em_call = db(query).select(stagtable.value,
                                           limitby = (0, 1)
                                           ).first()
                if em_call:
                    record_data_append(TR(TH("%s: " % T("Call in Emergency")),
                                          em_call.value))

                #query = (stagtable.site_id == site_id) & \
                #        (stagtable.tag == "oem_ready")
                #oem_ready = db(query).select(stagtable.value,
                #                             limitby = (0, 1)
                #                             ).first()
                #if oem_ready:
                #    record_data_append(TR(TH("%s: " % T("OEM Ready Receiving Center")),
                #                          oem_ready.value))

                #query = (stagtable.site_id == site_id) & \
                #        (stagtable.tag == "oem_want")
                #oem_want = db(query).select(stagtable.value,
                #                            limitby = (0, 1)
                #                            ).first()
                #if oem_want:
                #    record_data_append(TR(TH("%s: " % T("Want to be an OEM Ready Receiving Center")),
                #                          oem_want.value))

                comments = record.comments
                if comments:
                    record_data_append(TR(TH("%s: " % table.comments.label),
                                          table.comments.represent(comments)))

                map_ = ""
                if location_id:
                    ftable = s3db.gis_layer_feature
                    query = (ftable.controller == "org") & \
                            (ftable.function == "facility")
                    layer = db(query).select(ftable.layer_id,
                                             limitby=(0, 1)).first()
                    if layer:
                        gtable = s3db.gis_location
                        location = db(gtable.id == location_id).select(gtable.lat,
                                                                       gtable.lon,
                                                                       limitby = (0, 1)
                                                                       ).first()
                        map_ = current.gis.show_map(height = 250,
                                                    lat = location.lat,
                                                    lon = location.lon,
                                                    zoom = 15,
                                                    collapsed = True,
                                                    mouse_position = False,
                                                    overview = False,
                                                    permalink = False,
                                                    feature_resources = [{"name": T("Facility"),
                                                                          "id": "rheader_map",
                                                                          "active": True,
                                                                          "layer_id": layer.layer_id,
                                                                          "filter": "~.id=%s" % record_id,
                                                                          }],
                                                    )

                fac_name = record.name
                buttons = r.resource.crud.render_buttons(r,
                                                         ["edit", "delete"],
                                                         record_id = record_id)

                profile_header = DIV(H2(fac_name, _class="profile-header"),
                                     DIV(DIV(record_data,
                                             _class = "columns medium-6",
                                             ),
                                         DIV(map_,
                                             _class = "columns medium-6",
                                             ),
                                         _class = "row",
                                         ),
                                     buttons.get("edit_btn") or "",
                                     buttons.get("delete_btn") or "",
                                     )

                s3db.configure("org_facility",
                               profile_cols = 1,
                               profile_header = profile_header,
                               profile_title = fac_name,
                               profile_widgets = [],
                               )

            return result
        s3.prep = custom_prep

        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard_postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive:
                s3.stylesheets.append("../themes/HowCalm/style.css")
                # Action Buttons should launch Profile page
                from gluon import URL

                from s3 import S3CRUD

                profile_url = URL(c="org", f="facility",
                                  args = ["[id]", "profile"])
                S3CRUD.action_buttons(r,
                                      editable = False,
                                      read_url = profile_url,
                                      )

            return output
        s3.postp = custom_postp

        # Just used to hide default rheader
        attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_org_facility_controller = customise_org_facility_controller

    # -------------------------------------------------------------------------
    def org_organisation_duplicate(item):
        """
            Import item deduplication
            - names are not unique so we use Org ID as the unique key if names match
                (Can't use as completely Unique key as there are multiple Orgs with the same ID at times!)
            - Note that this does allow duplicates in...we could solve most of
              these by checking Street Address, but would then need to merge Org IDs...
        """

        db = current.db

        data = item.data

        # First check for duplicate name
        name = data.get("name")
        if not name:
            # hmm, nothing we can do
            return

        table = item.table
        ttable = current.s3db.org_organisation_tag
        query = (table.name == name)
        left = ttable.on((ttable.organisation_id == table.id) & \
                         (ttable.tag == "org_id"))
        duplicate_names = db(query).select(table.id,
                                           ttable.value,
                                           #limitby = (0, 3),
                                           )
        if not duplicate_names:
            # Assume not a duplicate, so allow creation of a new Org
            return

        if len(duplicate_names) == 1:
            # Only 1 existing Org with this name, so assume this is a duplicate
            item.id = duplicate_names.first()["org_organisation.id"]
            item.method = item.METHOD.UPDATE
            return

        # Multiple Name matches, so check Org ID
        org_id = None
        for citem in item.components:
            data = citem.data
            if data:
                ctablename = citem.tablename
                if ctablename == "org_organisation_tag":
                    tag = data.get("tag")
                    if tag == "org_id":
                        org_id = data.get("value")
                        break

        if not org_id:
            current.log.warning("Multiple existing orgs with this name, but we have no org_id in the source...we have no way of knowing which is the correct match, so creating a duplicate.")
            return

        # See which Org has the same Org ID
        for org in duplicate_names:
            if org["org_organisation_tag.value"] == org_id:
                # We found it!
                item.id = org["org_organisation.id"]
                item.method = item.METHOD.UPDATE
                return

        current.log.warning("Multiple existing orgs with this name, we have an org_id in the source but this doesn't match any of the existing orgs, so creating a duplicate.")
        return

    # Allow custom deduplicator to be used in scripts
    settings.org_organisation_duplicate = org_organisation_duplicate

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3LocationSelector

        s3db = current.s3db

        # Filtered components
        s3db.add_components("org_organisation",
                            org_facility = ({"name": "main_facility",
                                             "joinby": "organisation_id",
                                             "filterby": {"main_facility": True},
                                             "multiple": False,
                                             },
                                             ),
                            org_organisation_tag = ({"name": "org_id",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "org_id"},
                                                     "multiple": False,
                                                     },
                                                    #{"name": "congregants",
                                                    # "joinby": "organisation_id",
                                                    # "filterby": {"tag": "congregants"},
                                                    # "multiple": False,
                                                    # },
                                                    #{"name": "clergy_staff",
                                                    # "joinby": "organisation_id",
                                                    # "filterby": {"tag": "clergy_staff"},
                                                    # "multiple": False,
                                                    # },
                                                    #{"name": "lay_staff",
                                                    # "joinby": "organisation_id",
                                                    # "filterby": {"tag": "lay_staff"},
                                                    # "multiple": False,
                                                    # },
                                                    #{"name": "religious_staff",
                                                    # "joinby": "organisation_id",
                                                    # "filterby": {"tag": "religious_staff"},
                                                    # "multiple": False,
                                                    # },
                                                    #{"name": "volunteers",
                                                    # "joinby": "organisation_id",
                                                    # "filterby": {"tag": "volunteers"},
                                                    # "multiple": False,
                                                    # },
                                                    {"name": "board",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "board"},
                                                     "multiple": False,
                                                     },
                                                    {"name": "internet",
                                                     "joinby": "organisation_id",
                                                     "filterby": {"tag": "internet"},
                                                     "multiple": False,
                                                     },
                                                    ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        main_facility = components_get("main_facility")
        mftable = main_facility.table
        mftable.name.default = "Main" # NOT_NULL field
        mftable.location_id.widget = S3LocationSelector(levels = False,
                                                        show_address = True,
                                                        show_postcode = False,
                                                        show_map = False,
                                                        )


        def postprocess(form):
            # Set Facility Name to Org name
            form_vars_get = form.vars.get
            ftable = s3db.org_facility
            query = (ftable.organisation_id == form_vars_get("id")) & \
                    (ftable.name == "Main")
            current.db(query).update(name = form_vars_get("name"))

        auth = current.auth
        if not auth.s3_logged_in():
            # Simplified Form
            from s3 import S3SQLCustomForm

            f = s3db.gis_location.addr_street
            # Not Working
            #f.default = current.messages["NONE"] # Can't be empty, otherwise widget validator assumes it's an Lx location!
            f.label = T("Address of Organization or House of Worship")

            crud_form = S3SQLCustomForm((T("Formal Name of Organization or House of Worship"), "name"),
                                        ("", "main_facility.location_id"),
                                        postprocess = postprocess
                                        )

            s3db.configure("org_organisation",
                           crud_form = crud_form,
                           )

            return

        from gluon import IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE, URL

        from s3 import IS_INT_AMOUNT, \
                       S3Represent, \
                       S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        f = s3db.gis_location.addr_street
        # Not Working
        #f.default = current.messages["NONE"] # Can't be empty, otherwise widget validator assumes it's an Lx location!
        f.label =  T("Facility Address")

        #integer_represent = IS_INT_AMOUNT.represent

        #congregants = components_get("congregants")
        #f = congregants.table.value
        #f.represent = integer_represent
        #f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        #clergy_staff = components_get("clergy_staff")
        #f = clergy_staff.table.value
        #f.represent = integer_represent
        #f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        #lay_staff = components_get("lay_staff")
        #f = lay_staff.table.value
        #f.represent = integer_represent
        #f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        #religious_staff = components_get("religious_staff")
        #f = religious_staff.table.value
        #f.represent = integer_represent
        #f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        #volunteers = components_get("volunteers")
        #f = volunteers.table.value
        #f.represent = integer_represent
        #f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        #board = components_get("board")
        #f = board.table.value
        #f.represent = integer_represent
        #f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        internet = components_get("internet")
        f = internet.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        religion = components_get("religion")
        religion_hierarchy_levels = ["Religion",
                                     "Faith Tradition",
                                     "Denomination",
                                     "Judicatory Body",
                                     ]
        religion.configure(hierarchy_levels = religion_hierarchy_levels,
                           )

        if r.representation == "xls":
            xls = True
            # Override hyperlink
            NONE = current.messages["NONE"]
            s3db.org_organisation.website.represent = lambda v: v or NONE

            # Expand the religion column into individual columns per hierarchy level
            s3db.configure("org_organisation",
                           xls_expand_hierarchy = {
                               "religion_organisation.religion_id": religion_hierarchy_levels,
                               },
                           )
        else:
            xls = False
            s3db.pr_religion_organisation.religion_id.represent = S3Represent(lookup = "pr_religion",
                                                                              hierarchy = "%s, %s"
                                                                              )

        method = r.method
        if method == "read":
            # Can't use the Hierarchy widget labels
            religion_label = T("Religion")
            # Can't use the address field label
            facility_label = T("Main Facility Address")
        else:
            religion_label = ""
            facility_label = ""

        if auth.s3_has_role("ADMIN"):
            # Want to be able to create new Types inline!
            org_type_widget = "multiselect"
        else:
            org_type_widget = "groupedopts"

        crud_fields = ["name",
                       (T("Organization ID"), "org_id.value"),
                       S3SQLInlineLink("religion",
                                       field = "religion_id",
                                       label = religion_label,
                                       multiple = False,
                                       widget = "cascade",
                                       leafonly = False,
                                       #cascade = True,
                                       represent = S3Represent(lookup = "pr_religion"),
                                       ),
                       S3SQLInlineLink("organisation_type",
                                       field = "organisation_type_id",
                                       label = T("Organization Type"),
                                       multiple = True,
                                       widget = org_type_widget,
                                       cols = 3, # Only used with "groupedopts"
                                       create = {"c": "org", # Only used with "multiselect"
                                                 "f": "organisation_type",
                                                 "label": "Create Organization Type",
                                                 "parent": "organisation_organisation_type",
                                                 },
                                       ),
                       (facility_label, "main_facility.location_id"),
                       "website",
                       # Not a multiple=False component
                       #(T("Facebook"), "facebook.value"),
                       S3SQLInlineComponent(
                            "facebook",
                            name = "facebook",
                            label = T("Facebook"),
                            multiple = False,
                            fields = [("", "value")],
                            #filterby = {"field": "contact_method",
                            #            "options": "FACEBOOK",
                            #            },
                            ),
                       #(T("# Congregants"), "congregants.value"),
                       #(T("# Clergy Staff"), "clergy_staff.value"),
                       #(T("# Lay Staff"), "lay_staff.value"),
                       #(T("# Religious Staff"), "religious_staff.value"),
                       #(T("# Volunteers"), "volunteers.value"),
                       (T("# C. Board"), "board.value"),
                       (T("Internet Access"), "internet.value"),
                       "comments",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields,
                                    postprocess = postprocess
                                    )

        from s3 import S3HierarchyFilter, S3OptionsFilter, S3TextFilter #, S3LocationFilter
        filter_widgets = [
            S3TextFilter(["name", "org_id.value"],
                         label = T("Search"),
                         comment = T("Search by organization name or ID. You can use * as wildcard."),
                         _class = "filter-search",
                         ),
            S3HierarchyFilter("religion_organisation.religion_id",
                              label = False, #T("Religion"),
                              widget = "cascade",
                              leafonly = False,
                              cascade = True,
                              ),
            S3OptionsFilter("organisation_organisation_type.organisation_type_id",
                            label = T("Type"),
                            ),
            S3OptionsFilter("org_facility.location_id$L3",
                            label = T("Location"),
                            ),
            #S3LocationFilter("org_facility.location_id",
            #                 label = T("Location"),
            #                 levels = gis_levels,
            #                 #hidden = True,
            #                 ),
            S3OptionsFilter("org_facility.location_id$addr_postcode",
                            label = T("Zipcode"),
                            #hidden = True,
                            ),
            ]

        if xls:
            list_fields = ["name",
                           (T("ID"), "org_id.value"),
                           # Replace with something like S3Hierarchy.export_xls() ?
                           (T("Religion"), "religion_organisation.religion_id"),
                           (T("Parent Religion"), "religion_organisation.religion_id$parent"),
                           # Not working
                           #(T("Grandparent Religion"), "religion_organisation.religion_id$parent$parent"),
                           #(T("GreatGrandparent Religion"), "religion_organisation.religion_id$parent$parent$parent"),
                           (T("Organization Type"), "organisation_organisation_type.organisation_type_id"),
                           "website",
                           (T("Facebook"), "facebook.value"),
                           (T("# C. Board"), "board.value"),
                           (T("Internet Access"), "internet.value"),
                           "comments",
                           (T("Facility Address"), "main_facility.location_id$addr_street"),
                           (T("Borough"), "main_facility.location_id$L3"),
                           (T("Zipcode"), "main_facility.location_id$addr_postcode"),
                           ]
        elif method == "review":
            from s3 import S3DateTime
            s3db.org_organisation.created_on.represent = \
                lambda dt: S3DateTime.date_represent(dt, utc=True)
            list_fields = [(T("ID"), "org_id.value"),
                           "name",
                           (T("Religion"), "religion_organisation.religion_id"),
                           (T("Facility Address"), "main_facility.location_id"),
                           (T("Date Registered"), "created_on"),
                           ]
        else:
            list_fields = [(T("ID"), "org_id.value"),
                           "name",
                           (T("Religion"), "religion_organisation.religion_id"),
                           (T("Facility Address"), "main_facility.location_id"),
                           ]

        profile_url = URL(c="org", f="organisation",
                          args = ["[id]", "profile"])

        s3db.configure("org_organisation",
                       crud_form = crud_form,
                       create_next = profile_url,
                       deduplicate = org_organisation_duplicate,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       popup_url = profile_url,
                       update_next = profile_url,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if current.auth.s3_logged_in():
                mine = r.get_vars.get("mine")
                if mine:
                    from s3 import FS
                    filter_ = (FS("id") == current.auth.user.organisation_id)
                    r.resource.add_filter(filter_)
                    s3.crud_strings["org_organisation"].title_list = T("My Organizations")

                elif r.method == "profile":
                    # Profile Configuration
                    db = current.db
                    s3db = current.s3db
                    get_config = s3db.get_config
                    def dt_row_actions(component, tablename):
                        def row_actions(r, list_id):
                            #editable = get_config(tablename, "editable")
                            #if editable is None:
                            #    editable = True
                            deletable = get_config(tablename, "deletable")
                            if deletable is None:
                                deletable = True
                            #if editable:
                            #    actions = [{"label": T("Open"),
                            #                "url": r.url(component=component,
                            #                             component_id="[id]",
                            #                             method="update.popup",
                            #                             vars={"refresh": list_id}),
                            #                "_class": "action-btn edit s3_modal",
                            #                },
                            #               ]
                            #else:
                            if tablename == "pr_person":
                                actions = [{"label": T("Open"),
                                            "url": URL(c="pr", f="person",
                                                       args = ["[id]",
                                                               "read.popup",
                                                               ],
                                                       vars = {"refresh": list_id,
                                                               },
                                                       ),
                                            "_class": "action-btn edit s3_modal",
                                            },
                                           ]
                            else:
                                actions = [{"label": T("Open"),
                                            "url": r.url(component=component,
                                                         component_id="[id]",
                                                         method="read.popup",
                                                         vars={"refresh": list_id}),
                                            "_class": "action-btn edit s3_modal",
                                            },
                                           ]
                            if deletable:
                                actions.append({"label": T("Delete"),
                                                "_ajaxurl": r.url(component=component,
                                                                  component_id="[id]",
                                                                  method="delete.json",
                                                                  ),
                                                "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                                                })
                            return actions
                        return row_actions

                    tablename = "pr_person"
                    contacts_widget = {"label": "Contacts",
                                       "label_create": "Add Contact",
                                       "actions": dt_row_actions("person", tablename),
                                       "tablename": tablename,
                                       "type": "datatable",
                                       "context": "organisation",
                                       }

                    tablename = "org_facility"
                    facilities_widget = {#"label": "Facilities",
                                         "label_create": "Add Facility",
                                         "type": "datatable",
                                         "actions": dt_row_actions("facility", tablename),
                                         "tablename": tablename,
                                         "context": "organisation",
                                         "create_controller": "org",
                                         "create_function": "organisation",
                                         "create_component": "facility",
                                         "pagesize": None, # all records
                                         }

                    profile_widgets = [contacts_widget,
                                       facilities_widget,
                                       ]

                    from gluon import A, DIV, H2, TABLE, TR, TH, URL

                    table = s3db.org_organisation
                    record = r.record

                    record_data = TABLE()
                    record_data_append = record_data.append

                    record_id = record.id

                    otagtable = s3db.org_organisation_tag
                    query = (otagtable.organisation_id == record_id) & \
                            (otagtable.tag == "org_id")
                    org_id = db(query).select(otagtable.value,
                                              limitby = (0, 1)
                                              ).first()
                    if org_id:
                        record_data_append(TR(TH("%s: " % T("Organization ID")),
                                              org_id.value))

                    ltable = s3db.pr_religion_organisation
                    query = (ltable.organisation_id == record_id)
                    religion = db(query).select(ltable.religion_id,
                                                limitby = (0, 1)
                                                ).first()
                    if religion:
                        record_data_append(TR(TH("%s: " % T("Religion")),
                                              ltable.religion_id.represent(religion.religion_id)))

                    ltable = s3db.org_organisation_organisation_type
                    query = (ltable.organisation_id == record_id)
                    org_types = db(query).select(ltable.organisation_type_id,
                                                 # Ensure unique types
                                                 groupby = ltable.organisation_type_id)
                    if org_types:
                        org_types = [l.organisation_type_id for l in org_types]
                        record_data_append(TR(TH("%s: " % ltable.organisation_type_id.label),
                                              ltable.organisation_type_id.represent.multiple(org_types)))

                    website = record.website
                    if website:
                        record_data_append(TR(TH("%s: " % table.website.label),
                                              A(website, _href=website)))

                    ctable = s3db.pr_contact
                    query = (table.id == record_id) & \
                            (table.pe_id == ctable.pe_id) & \
                            (ctable.contact_method == "FACEBOOK")
                    facebook = db(query).select(ctable.value,
                                                limitby = (0, 1)
                                                ).first()
                    if facebook:
                        url = facebook.value
                        record_data_append(TR(TH("%s: " % T("Facebook")),
                                              A(url, _href=url)))

                    oftable = s3db.org_facility
                    query = (oftable.organisation_id == record_id) & \
                            (oftable.deleted == False)
                    facility = db(query).select(oftable.location_id,
                                                limitby = (0, 1)
                                                ).first()
                    if facility:
                        record_data_append(TR(TH("%s: " % T("Main Facility Address")),
                                              oftable.location_id.represent(facility.location_id)))

                    query = (otagtable.organisation_id == record_id) & \
                            (otagtable.tag == "board")
                    board = db(query).select(otagtable.value,
                                             limitby = (0, 1)
                                             ).first()
                    if board:
                        record_data_append(TR(TH("%s: " % T("# C. Board")),
                                              board.value))

                    query = (otagtable.organisation_id == record_id) & \
                            (otagtable.tag == "internet")
                    internet = db(query).select(otagtable.value,
                                                limitby = (0, 1)
                                                ).first()
                    if internet:
                        internet = T("yes") if internet == "Y" else T("no")
                        record_data_append(TR(TH("%s: " % T("Internet Access")),
                                              internet))

                    comments = record.comments
                    if comments:
                        record_data_append(TR(TH("%s: " % table.comments.label),
                                              comments))

                    gtable = s3db.gis_location
                    query = (oftable.organisation_id == record_id) & \
                            (oftable.deleted == False) & \
                            (oftable.location_id == gtable.id)
                    features = db(query).select(gtable.lat,
                                                gtable.lon
                                                )
                    map_ = ""
                    if len(features) > 0:
                        ftable = s3db.gis_layer_feature
                        query = (ftable.controller == "org") & \
                                (ftable.function == "facility")
                        layer = db(query).select(ftable.layer_id,
                                                 limitby=(0, 1)).first()
                        if layer:
                            gis = current.gis
                            bbox = gis.get_bounds([f for f in features])
                            map_ = gis.show_map(height = 250,
                                                collapsed = True,
                                                bbox = bbox,
                                                mouse_position = False,
                                                overview = False,
                                                permalink = False,
                                                feature_resources = [{"name": T("Facilities"),
                                                                      "id": "rheader_map",
                                                                      "active": True,
                                                                      "layer_id": layer.layer_id,
                                                                      "filter": "~.organisation_id=%s" % record_id,
                                                                      }],
                                                )

                    org_name = record.name
                    buttons = r.resource.crud.render_buttons(r,
                                                             ["edit", "delete"],
                                                             record_id = record_id)
                    profile_header = DIV(H2(org_name, _class="profile-header"),
                                         DIV(DIV(record_data,
                                                 _class = "columns medium-6",
                                                 ),
                                             DIV(map_,
                                                 _class = "columns medium-6",
                                                 ),
                                             _class = "row",
                                             ),
                                         buttons.get("edit_btn") or "",
                                         buttons.get("delete_btn") or "",
                                         )

                    s3db.configure("org_organisation",
                                   profile_cols = 1,
                                   profile_header = profile_header,
                                   profile_title = org_name,
                                   profile_widgets = profile_widgets,
                                   )

            else:
                r.id = None
                r.method = "create"

            return result
        s3.prep = custom_prep

        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard_postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive:
                s3.stylesheets.append("../themes/HowCalm/style.css")
                # Action Buttons should launch Profile page
                from gluon import URL

                from s3 import S3CRUD

                profile_url = URL(c="org", f="organisation",
                                  args = ["[id]", "profile"])
                S3CRUD.action_buttons(r,
                                      editable = False,
                                      read_url = profile_url,
                                      )

                if r.component_name == "person":
                    # Custom Create Button in unused Tab
                    from gluon import A#, URL
                    add_btn = A(T("Create Contact"),
                                _class = "action-btn",
                                _href = URL(c="pr", f="person", args="create",
                                            vars = {"organisation_id": r.id},
                                            ),
                                )
                    output["buttons"] = {"add_btn": add_btn}

            return output
        s3.postp = custom_postp

        # Just used to hide default rheader
        attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET, URL

        from s3 import S3LocationSelector, S3Represent, IS_PERSON_GENDER
        from s3layouts import S3PopupLink

        s3db = current.s3db

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Contact"),
            title_display = T("Contact Details"),
            title_list = T("Contacts"),
            title_update = T("Edit Contact Details"),
            label_list_button = T("List Contacts"),
            label_delete_button = T("Delete Contact"),
            msg_record_created = T("Contact added"),
            msg_record_modified = T("Contact details updated"),
            msg_record_deleted = T("Contact deleted"),
            msg_list_empty = T("No Contacts currently registered"))

        pr_gender_opts = {1: "",
                          2: T("He, Him, His"),
                          3: T("She, Her, Hers"),
                          4: T("They, Their, Theirs"),
                          }
        f = s3db.pr_person.gender
        f.label = T("Pronouns")
        f.represent = S3Represent(options = pr_gender_opts,
                                  default = current.messages["NONE"],
                                  )
        f.requires = IS_PERSON_GENDER(pr_gender_opts,
                                      sort = True,
                                      zero = None,
                                      )

        # Filtered components
        s3db.add_components("pr_person",
                            pr_person_tag = ({"name": "other_languages",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "other_languages"},
                                              "multiple": False,
                                              },
                                             {"name": "religious_title",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "religious_title"},
                                              "multiple": False,
                                              },
                                             {"name": "position_title",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "position_title"},
                                              "multiple": False,
                                              },
                                             #{"name": "em_comms",
                                             # "joinby": "person_id",
                                             # "filterby": {"tag": "em_comms"},
                                             # "multiple": False,
                                             # },
                                             ),
                            )

        s3db.add_components("pr_pentity",
                            pr_contact = (# Home phone numbers:
                                          {"name": "home_phone",
                                           "joinby": "pe_id",
                                           "filterby": {
                                                "contact_method": "HOME_PHONE",
                                                },
                                           },
                                          # Work phone numbers:
                                          {"name": "work_phone",
                                           "joinby": "pe_id",
                                           "filterby": {
                                                "contact_method": "WORK_PHONE",
                                                },
                                           },
                                          )
                            )

        # Individual settings for specific tag components
        #components_get = s3db.resource(tablename).components.get

        #em_comms = components_get("em_comms")
        #f = em_comms.table.value
        #f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        #f.represent = lambda v: T("yes") if v == "Y" else T("no")
        #from s3 import S3TagCheckboxWidget
        #f.widget = S3TagCheckboxWidget(on="Y", off="N")
        #f.default = "N"

        s3db.hrm_human_resource.job_title_id.comment = S3PopupLink(c = "hrm",
                                                                   f = "job_title",
                                                                   label = T("Create Type"),
                                                                   title = T("Type"),
                                                                   tooltip = T("The contact's type"),
                                                                   )

        s3db.hrm_competency.skill_id.comment = S3PopupLink(c = "hrm",
                                                           f = "skill",
                                                           # no pr/competency controller for options.s3json lookup
                                                           vars = {"prefix": "hrm",
                                                                   },
                                                           label = T("Create Language"),
                                                           )
        #s3db.gis_location.addr_street.label = T("Mailing Address")
        s3db.gis_location.addr_street.label = ""
        s3db.pr_address.location_id.widget = S3LocationSelector(levels = False,
                                                                show_address = True,
                                                                show_postcode = False,
                                                                show_map = False,
                                                                )

        # List view uses hrm/staff
        #from s3 import S3HierarchyFilter, S3OptionsFilter, S3LocationFilter, S3TextFilter
        #filter_widgets = [
        #    S3TextFilter(["first_name", "middle_name", "last_name"],
        #                 label = T("Search"),
        #                 comment = T("Search by person name. You can use * as wildcard."),
        #                 _class = "filter-search",
        #                 ),
        #    S3HierarchyFilter("human_resource.organisation_id$religion_organisation.religion_id",
        #                      label = T("Religion"),
        #                      ),
        #    S3LocationFilter("location_id",
        #                     label = T("Location"),
        #                     levels = gis_levels,
        #                     #hidden = True,
        #                     ),
        #    S3OptionsFilter("competency.skill_id",
        #                    label = T("Languages Spoken"),
        #                    #hidden = True,
        #                    ),
        #    ]

        list_fields = ["first_name",
                       "middle_name",
                       "last_name",
                       (T("Type"), "human_resource.job_title_id"),
                       (T("Languages Spoken"), "competency.skill_id"),
                       (T("Religious Title"), "religious_title.value"),
                       (T("Position Title"), "position_title.value"),
                       #(T("ECDM"), "em_comms.value"),
                       ]

        profile_url = URL(c="pr", f="person",
                          args = ["[id]", "profile"])

        s3db.configure("pr_person",
                       create_next = profile_url,
                       #filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       update_next = profile_url,
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            get_vars_get = r.get_vars.get
            if get_vars_get("personal"):
                from gluon import URL
                from gluon.tools import redirect
                redirect(URL(args=[current.auth.s3_logged_in_person()]))

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            method = r.method
            if method in ("create", "read", "update"):
                # CRUD form called after standard_prep as that clears the crud_form in popups
                # (Read used in Popups even if not in Profile)
                from s3 import S3SQLCustomForm, S3SQLInlineComponent

                s3db = current.s3db

                crud_fields = ("first_name",
                               "middle_name",
                               "last_name",
                               #(T("ID"), "pe_label"),
                               S3SQLInlineComponent(
                                    "human_resource",
                                    name = "human_resource",
                                    label = "",
                                    multiple = False,
                                    fields = ["organisation_id",
                                              (T("Type"), "job_title_id"),
                                              ],
                                    ),
                               S3SQLInlineComponent(
                                    "competency",
                                    #name = "languages_spoken",
                                    label = T("Languages Spoken"),
                                    multiple = True,
                                    fields = [("", "skill_id")],
                                    ),
                               (T("Other Languages"), "other_languages.value"),
                               (T("Religious Title"), "religious_title.value"),
                               (T("Position Title"), "position_title.value"),
                               "gender",
                               S3SQLInlineComponent(
                                    "address",
                                    name = "address",
                                    label = T("Mailing Address"),
                                    #label = "",
                                    multiple = False,
                                    fields = [("", "location_id")],
                                    #filterby = {"field": "type",
                                    #            "options": 1,
                                    #            },
                                    ),
                               # Not a multiple=False component
                               #(T("Cell Phone"), "phone.value"),
                               S3SQLInlineComponent(
                                    "phone",
                                    name = "phone",
                                    label = T("Cell Phone"),
                                    multiple = False,
                                    fields = [("", "value")],
                                    #filterby = {"field": "contact_method",
                                    #            "options": "SMS",
                                    #            },
                                    ),
                               S3SQLInlineComponent(
                                    "contact",
                                    name = "work_phone",
                                    label = T("Office Phone"),
                                    multiple = False,
                                    fields = [("", "value")],
                                    filterby = {"field": "contact_method",
                                                "options": "WORK_PHONE",
                                                },
                                    ),
                               S3SQLInlineComponent(
                                    "contact",
                                    name = "home_phone",
                                    label = T("Emergency Phone"),
                                    multiple = False,
                                    fields = [("", "value")],
                                    filterby = {"field": "contact_method",
                                                "options": "HOME_PHONE",
                                                },
                                    ),
                               S3SQLInlineComponent(
                                    "contact",
                                    name = "fax",
                                    label = T("Office Fax"),
                                    multiple = False,
                                    fields = [("", "value")],
                                    filterby = {"field": "contact_method",
                                                "options": "FAX",
                                                },
                                    ),
                               S3SQLInlineComponent(
                                    "contact",
                                    name = "personal_email",
                                    label = T("Personal Email"),
                                    multiple = False,
                                    fields = [("", "value")],
                                    filterby = ({"field": "contact_method",
                                                 "options": "EMAIL",
                                                 },
                                                {"field": "priority",
                                                 "options": 2,
                                                 },
                                                ),
                                    ),
                               S3SQLInlineComponent(
                                    "contact",
                                    name = "work_email",
                                    label = T("Work Email"),
                                    multiple = False,
                                    fields = [("", "value")],
                                    filterby = ({"field": "contact_method",
                                                 "options": "EMAIL",
                                                 },
                                                {"field": "priority",
                                                 "options": 1,
                                                 },
                                                ),
                                    ),
                               #(T("Emergency Communications Decision-maker"), "em_comms.value"),
                               )

                crud_form = S3SQLCustomForm(*crud_fields)
                s3db.configure("pr_person",
                               crud_form = crud_form,
                               )

                if method == "create":
                    organisation_id = get_vars_get("organisation_id") or get_vars_get("~.(organisation)")
                    if organisation_id:
                        s3db.hrm_human_resource.organisation_id.default = organisation_id

            elif get_vars_get("mine"):
                from s3 import FS
                filter_ = (FS("human_resource.organisation_id") == current.auth.user.organisation_id)
                r.resource.add_filter(filter_)
                s3.crud_strings["pr_person"].title_list = T("My Contacts")

            elif method == "profile":
                # Profile Configuration
                from gluon import A, DIV, H2, TABLE, TR, TH, URL

                from s3 import s3_fullname

                record = r.record

                person_name = s3_fullname(record)

                record_data = TABLE(TR(TH(person_name, _colspan=2)))
                record_data_append = record_data.append

                record_id = record.id

                db = current.db
                s3db = current.s3db

                hrtable = s3db.hrm_human_resource
                query = (hrtable.person_id == record_id)
                hr = db(query).select(hrtable.job_title_id,
                                      hrtable.organisation_id,
                                      limitby = (0, 1)
                                      ).first()
                if hr:
                    job_title_id = hr.job_title_id
                    if job_title_id:
                        record_data_append(TR(TH("%s: " % T("Type")),
                                              hrtable.job_title_id.represent(job_title_id),
                                              ))

                ctable = s3db.hrm_competency
                query = (ctable.person_id == record_id) & \
                        (ctable.deleted == False)
                languages = db(query).select(ctable.skill_id)
                if languages:
                    record_data_append(TR(TH("%s: " % T("Languages Spoken")),
                                          ctable.skill_id.represent.multiple([l.skill_id for l in languages])))

                ptagtable = s3db.pr_person_tag
                query = (ptagtable.person_id == record_id) & \
                        (ptagtable.tag == "other_languages")
                other_languages = db(query).select(ptagtable.value,
                                                   limitby = (0, 1)
                                                   ).first()
                if other_languages:
                    record_data_append(TR(TH("%s: " % T("Other Languages")),
                                          other_languages.value))

                query = (ptagtable.person_id == record_id) & \
                        (ptagtable.tag == "religious_title")
                religious_title = db(query).select(ptagtable.value,
                                                   limitby = (0, 1)
                                                   ).first()
                if religious_title:
                    record_data_append(TR(TH("%s: " % T("Religious Title")),
                                          religious_title.value))

                query = (ptagtable.person_id == record_id) & \
                        (ptagtable.tag == "position_title")
                position_title = db(query).select(ptagtable.value,
                                                  limitby = (0, 1)
                                                  ).first()
                if position_title:
                    record_data_append(TR(TH("%s: " % T("Position Title")),
                                          position_title.value))
                if hr:
                    organisation_id = hr.organisation_id
                    record_data_append(TR(TH("%s: " % T("Organization")),
                                          s3db.org_OrganisationRepresent(show_link = True,
                                                                         linkto = URL(c="org",
                                                                                      f="organisation",
                                                                                      args=["[id]",
                                                                                            "profile",
                                                                                            ]))(organisation_id),
                                          ))
                gender = record.gender
                if gender:
                    ptable = s3db.pr_person
                    record_data_append(TR(TH("%s: " % ptable.gender.label),
                                          ptable.gender.represent(gender)))
                pe_id = record.pe_id
                atable = s3db.pr_address
                query = (atable.pe_id == pe_id) & \
                        (atable.deleted == False)
                address = db(query).select(atable.location_id,
                                           limitby = (0, 1)
                                           ).first()
                if address:
                    record_data_append(TR(TH("%s: " % T("Mailing Address")),
                                          atable.location_id.represent(address.location_id)))
                ctable = s3db.pr_contact
                query = (ctable.pe_id == pe_id) & \
                        (ctable.deleted == False)
                contacts = db(query).select(ctable.contact_method,
                                            ctable.priority,
                                            ctable.value,
                                            )
                if contacts:
                    phone = work_phone = home_phone = fax = personal_email = work_email = None
                    for contact in contacts:
                        contact_method = contact.contact_method
                        if contact_method == "SMS":
                            phone = contact.value
                        elif contact_method == "WORK_PHONE":
                            work_phone = contact.value
                        elif contact_method == "HOME_PHONE":
                            home_phone = contact.value
                        elif contact_method == "FAX":
                            fax = contact.value
                        elif contact_method == "EMAIL":
                            priority = contact.priority
                            if priority == 1:
                                work_email = contact.value
                            elif priority == 2:
                                personal_email = contact.value
                    if phone:
                        record_data_append(TR(TH("%s: " % T("Cell Phone")),
                                              phone))
                    if work_phone:
                        record_data_append(TR(TH("%s: " % T("Office Phone")),
                                              work_phone))
                    if home_phone:
                        record_data_append(TR(TH("%s: " % T("Emergency Phone")),
                                              home_phone))
                    if fax:
                        record_data_append(TR(TH("%s: " % T("Office FAX")),
                                              fax))
                    if personal_email:
                        record_data_append(TR(TH("%s: " % T("Personal Email")),
                                              personal_email))
                    if work_email:
                        record_data_append(TR(TH("%s: " % T("Work Email")),
                                              work_email))

                buttons = r.resource.crud.render_buttons(r,
                                                         ["edit",
                                                           #"delete",
                                                           ],
                                                         record_id = record_id)

                profile_header = DIV(H2(person_name, _class="profile-header"),
                                     DIV(DIV(record_data,
                                             _class = "columns medium-12",
                                             #_class = "columns medium-6",
                                             ),
                                         #DIV(map_,
                                         #    _class = "columns medium-6",
                                         #    ),
                                         _class = "row",
                                         ),
                                     buttons.get("edit_btn") or "",
                                     #buttons.get("delete_btn") or "",
                                     )

                s3db.configure("pr_person",
                               profile_cols = 1,
                               profile_header = profile_header,
                               profile_title = person_name,
                               profile_widgets = [],
                               )

            return result
        s3.prep = custom_prep

        # Just used to hide default rheader
        attr["rheader"] = howcalm_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

# END =========================================================================
