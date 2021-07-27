# -*- coding: utf-8 -*-

"""
    Custom rheaders for RLPCM template

    @license: MIT
"""

from gluon import current, URL, A, SPAN

from s3 import S3ResourceHeader, s3_rheader_resource, s3_fullname

# =============================================================================
def rlpcm_br_rheader(r, tabs=None):
    """ BR Resource Headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T
        settings = current.deployment_settings

        record_id = record.id

        if tablename == "pr_person":

            if not tabs:

                # Basic Case Documentation
                tabs = [(T("Basic Details"), None),
                        ]
                append = tabs.append

                if settings.get_br_case_contacts_tab():
                    append((T("Contact Info"), "contacts"))
                if settings.get_br_case_id_tab():
                    append((T("ID"), "identity"))
                if settings.get_br_case_family_tab():
                    append((T("Family Members"), "group_membership/"))

                activities_tab = settings.get_br_case_activities()
                measures_tab = settings.get_br_manage_assistance() and \
                               settings.get_br_assistance_tab()

                activities_label = T("Needs")
                if activities_tab and measures_tab:
                    measures_label = T("Measures")
                else:
                    measures_label = T("Assistance")

                if activities_tab:
                    append((activities_label, "case_activity"))
                if measures_tab:
                    append((measures_label, "assistance_measure"))

                if settings.get_br_service_contacts():
                    append((T("Service Contacts"), "service_contact"))
                if settings.get_br_case_notes_tab():
                    append((T("Notes"), "br_note"))
                if settings.get_br_case_photos_tab():
                    append((T("Photos"), "image"))
                if settings.get_br_case_documents_tab():
                    append((T("Documents"), "document/"))

            case = resource.select(["first_name",
                                    "middle_name",
                                    "last_name",
                                    "case.status_id",
                                    "case.invalid",
                                    "case.household_size",
                                    "case.organisation_id",
                                    ],
                                    represent = True,
                                    raw_data = True,
                                    ).rows

            if not case:
                # Target record exists, but doesn't match filters
                return None

            # Extract case data
            case = case[0]

            name = s3_fullname
            case_status = lambda row: case["br_case.status_id"]
            organisation = lambda row: case["br_case.organisation_id"]

            household = settings.get_br_household_size()
            if household:
                if household == "auto":
                    label = T("Size of Family")
                else:
                    label = T("Household Size")
                household_size = (label,
                                  lambda row: case["br_case.household_size"],
                                  )
            else:
                household_size = None

            rheader_fields = [[(T("ID"), "pe_label"),
                               (T("Case Status"), case_status),
                               (T("Organisation"), organisation),
                               ],
                              [household_size,
                               ],
                              ]

            invalid = case["_row"]["br_case.invalid"]
            if invalid:
                # "Invalid Case" Hint
                hint = lambda record: SPAN(T("Invalid Case"),
                                           _class="invalid-case",
                                           )
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
                                                    ),
                                _href=URL(f = "person",
                                          args = [record_id, "image"],
                                          vars = r.get_vars,
                                          ),
                                )
                           )
        elif tablename == "br_case_activity":

            if not tabs:
                if r.function in ("case_activity", "offers"):
                    tabs = [(T("Basic Details"), None),
                            (T("Direct Offers"), "offers/"),
                            ]
                elif r.function in ("activities"):
                    tabs = [(T("Basic Details"), None, {"native": True}),
                            (T("Direct Offers"), "direct_offer"),
                            ]

            rheader_fields = [["need_id"],
                              ["date"],
                              ]
            rheader = S3ResourceHeader(rheader_fields, tabs, title="subject")(
                            r,
                            table = resource.table,
                            record = record,
                            )
        elif tablename == "br_assistance_offer":

            if not tabs:
                tabs = [(T("Basic Details"), None, {"native": True}),
                        ]
                if r.function == "assistance_offer":
                    tabs.append((T("Direct Offers"), "direct_offer"))
            rheader_fields = [["date"]]
            rheader = S3ResourceHeader(rheader_fields, tabs, title="name")(
                            r,
                            table = resource.table,
                            record = record,
                            )
        else:
            rheader = None

    return rheader

# =============================================================================
def rlpcm_profile_rheader(r, tabs=None):
    """ Custom rheader for default/person """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

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

            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user_profile"),
                    (T("Contact Information"), "contacts"),
                    ]
            rheader_fields = []

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )
    return rheader

# =============================================================================
def rlpcm_org_rheader(r, tabs=None):
    """ ORG custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "org_organisation":

            auth = current.auth
            is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")

            if not tabs:
                tabs = [(T("Organisation"), None),
                        (T("Offices"), "office"),
                        ]
                if auth.s3_has_permission("update", "org_organisation", record_id=record.id):
                    tabs.append((T("Staff"), "human_resource"))

            # Check for active user accounts:
            rheader_fields = []
            if is_org_group_admin:

                from templates.RLPPTM.helpers import get_org_accounts
                active = get_org_accounts(record.id)[0]

                active_accounts = lambda row: len(active)
                rheader_fields.append([(T("Active Accounts"), active_accounts)])

            rheader_title = "name"

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# END =========================================================================
