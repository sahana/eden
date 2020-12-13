# -*- coding: utf-8 -*-

"""
    Custom rheaders for DRKCM template

    @license: MIT
"""

from gluon import current, A, DIV, SPAN, URL

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
def drk_dvr_rheader(r, tabs=None):
    """ DVR custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, \
                   S3ResourceHeader, \
                   s3_fullname
    from .uioptions import get_ui_options

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

            from .helpers import case_read_multiple_orgs
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

                name = lambda person: s3_fullname(person, truncate=False)
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
                from .helpers import get_total_consultations
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
                from .helpers import get_protection_themes
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
    from .uioptions import get_ui_options

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

# END =========================================================================
