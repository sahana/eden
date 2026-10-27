"""
    Custom rheaders for MRCMS

    License: MIT
"""

from gluon import current, A, DIV, I, URL, SPAN

from core import S3ResourceHeader, s3_fullname, s3_rheader_resource

from .helpers import client_name_age, hr_details, last_seen_represent

# =============================================================================
def act_rheader(r, tabs=None):
    """ Custom resource headers for ACT module """

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

        if tablename == "act_activity":
            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Participants"), "beneficiary"),
                        (T("Documents"), "document"),
                        ]
            rheader_fields = [["type_id", "place"],
                              ["date", "time"],
                              ["end_date"],
                              ]
            rheader_title = "name"

            rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
            rheader = rheader(r, table=resource.table, record=record)

    return rheader

# =============================================================================
def dvr_rheader(r, tabs=None):
    """ Custom resource headers for DVR module """

    auth = current.auth
    has_permission = auth.s3_has_permission
    accessible_url = auth.permission.accessible_url

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
    rheader_title = None

    if record:
        T = current.T

        if tablename == "pr_person":
            # Case file

            # "Case Archived" hint
            hint = lambda record: SPAN(T("Invalid Case"), _class="invalid-case")

            c = r.controller

            if c == "security":

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
                            ]

                    has_roles = current.auth.s3_has_roles
                    if c == "counsel":
                        # Counseling Perspective
                        tabs.append((T("Family Members"), "group_membership/"))
                        if has_roles(("CASE_ADMIN", "CASE_MANAGER")):
                            tabs.extend([(T("Appointments"), "case_appointment"),
                                         (T("Tasks"), "case_task"),
                                         (T("Vulnerabilities"), "vulnerability"),
                                         (T("Needs"), "case_activity"),
                                         (T("Measures"), "response_action"),
                                         ])
                        tabs.extend([(T("Documents"), "document/"),
                                     (T("Notes"), "case_note"),
                                     ])

                    elif c == "supply":
                        # Supply Perspective
                        tabs.extend([(T("Items Received"), "distribution_item"),
                                     ])

                    elif c == "med":
                        # Medical Perspective
                        patient_id = current.s3db.med_get_current_patient_id(record.id)
                        highlight = {"_class": "emphasis"} if patient_id else {}
                        tabs.extend([(T("Background"), "anamnesis"),
                                     (T("Vaccinations"), "vaccination"),
                                     (T("Medication"), "medication"),
                                     (T("Visits"), "patient"),
                                     (T("Vital Signs"), "vitals", highlight),
                                     (T("Status"), "med_status", highlight),
                                     (T("Treatment"), "treatment", highlight),
                                     (T("Appointments"), "case_appointment"),
                                     ])
                        # Add document-tab only if the user is permitted to
                        # access documents through the med/patient controller
                        # (otherwise, the tab would always be empty)
                        if has_permission("read", "doc_document", c="med", f="patient"):
                            tabs.append((T("Documents"), "document/"))

                    else:
                        # Management Perspective
                        tabs.extend([(T("Family Members"), "group_membership/"),
                                     (T("ID"), "identity"),
                                     (T("Service Contacts"), "service_contact"),
                                     (T("Appointments"), "case_appointment"),
                                     ])
                        if has_roles(("CASE_ADMIN",)):
                            tabs.extend([(T("Tasks"), "case_task"),
                                         (T("Events"), "case_event"),
                                         ])
                        if has_roles(("SHELTER_ADMIN", "SHELTER_MANAGER")):
                            tabs.append((T("Presence"), "site_presence_event"))
                        tabs.extend([(T("Photos"), "image"),
                                     (T("Documents"), "document/"),
                                     (T("Notes"), "case_note"),
                                     ])

                case = resource.select(["dvr_case.status_id",
                                        "dvr_case.archived",
                                        "dvr_case.reference",
                                        "dvr_case.household_size",
                                        "dvr_case.last_seen_on",
                                        "first_name",
                                        "last_name",
                                        "person_details.nationality",
                                        "shelter_registration.shelter_id",
                                        "shelter_registration.shelter_unit_id",
                                        ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows

                if case:
                    # Extract case data
                    case = case[0]
                    raw = case["_row"]

                    case_reference = lambda row: case["dvr_case.reference"]
                    nationality_label = case["pr_person_details.nationality"]
                    nationality = lambda row: SPAN(raw["pr_person_details.nationality"],
                                                   _title = nationality_label,
                                                   _style = "cursor:pointer",
                                                   )

                    case_status = lambda row: case["dvr_case.status_id"]
                    household_size = lambda row: case["dvr_case.household_size"]

                    # Represent shelter as link to shelter overview, if permitted
                    shelter_id = raw["cr_shelter_registration.shelter_id"]
                    shelter_url = accessible_url(c="cr", f="shelter", args=[shelter_id, "overview"])
                    shelter_name = case["cr_shelter_registration.shelter_id"]
                    if shelter_url:
                        shelter = lambda row: A(shelter_name, _href=shelter_url)
                    else:
                        shelter = lambda row: shelter_name
                    unit = lambda row: case["cr_shelter_registration.shelter_unit_id"]

                    # Represent last-seen-date as warning, if too long ago
                    last_seen_on = lambda row: \
                                   last_seen_represent(raw["dvr_case.last_seen_on"],
                                                       case["dvr_case.last_seen_on"],
                                                       )
                else:
                    # Target record exists, but doesn't match filters
                    return None

                # TODO hide restricted fields for non-privileged roles
                # TODO include case organisation for users with cross-org permissions

                rheader_fields = [[(T("ID"), "pe_label"),
                                   (T("Principal Ref.No."), case_reference),    # TODO restricted
                                   (T("Shelter"), shelter),
                                   ],
                                  ["date_of_birth",
                                   (T("Case Status"), case_status),
                                   (T("Housing Unit"), unit),
                                   ],
                                  [(T("Nationality"), nationality),
                                   (T("Size of Family"), household_size),       # TODO restricted
                                   (T("Last seen on"), last_seen_on),           # TODO restricted
                                   ],
                                  ]

                if raw["dvr_case.archived"]:
                    rheader_fields.insert(0, [(None, hint)])
                    links = None
                else:
                    # Link to switch case file perspective
                    links = DIV(_class="case-file-perspectives")
                    render_switch = False
                    record_id = record.id
                    perspectives = (("dvr", T("Manage")),
                                    ("counsel", T("Counseling")),
                                    ("supply", T("Supply")),
                                    ("med", T("Medical")),
                                    )
                    icon = "arrow-circle-left"
                    for cntr, label in perspectives:
                        if c == cntr:
                            link = SPAN(I(_class = "fa fa-arrow-circle-down"),
                                        label,
                                        _class="current-perspective",
                                        )
                            icon = "arrow-circle-right"
                        elif has_permission("read", "pr_person", c=cntr, f="person", record_id=record_id):
                            render_switch = True
                            link = A(I(_class = "fa fa-%s" % icon),
                                     label,
                                     _href = URL(c=cntr, f="person", args=[record_id]),
                                     )
                        else:
                            continue
                        links.append(link)
                    if not render_switch:
                        links = None

                rheader_title = client_name_age

                # Generate rheader XML
                rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
                rheader = rheader(r, table=resource.table, record=record)

                # Add profile picture
                from core import s3_avatar_represent
                record_id = record.id
                # TODO this should only be a link in Manage-perspective
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

                # Insert perspective switch
                if links:
                    rheader.insert(0, links)

                return rheader

        elif tablename == "dvr_task":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

            rheader_fields = [[(T("Client"), "person_id"), (T("Staff"), "human_resource_id")],
                              ["status", "due_date"],
                              ]
            rheader_title = "name"

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table=resource.table, record=record)

    return rheader

# =============================================================================
def org_rheader(r, tabs=None):
    """ Custom resource headers for ORG module """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_title = None
    rheader_fields = []

    if record:
        T = current.T
        auth = current.auth

        if tablename == "org_group":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Member Organizations"), "organisation"),
                        (T("Documents"), "document"),
                        ]

            rheader_fields = []
            rheader_title = "name"

        elif tablename == "org_organisation":

            if not tabs:
                # General tabs
                tabs = [(T("Basic Details"), None),
                        #(T("Offices"), "office"),
                        ]

                # Role/permission-dependent tabs
                if auth.s3_has_permission("read", "pr_person", c="hrm", f="person"):
                    tabs.append((T("Staff"), "human_resource"))

                # Documents tabs
                tabs += [(T("Documents"), "document"),
                         #(T("Templates"), "template"),
                         ]

            rheader_fields = []
            rheader_title = "name"

        elif tablename == "org_facility":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

            rheader_fields = [["name", "email"],
                              ["organisation_id", "phone1"],
                              ["location_id", "phone2"],
                              ]
            rheader_title = None

        else:
            return None

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table=resource.table, record=record)

    return rheader

# =============================================================================
def cr_rheader(r, tabs=None):
    """ Custom resource headers for shelter registry """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_title = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "cr_shelter":

            if not tabs:
                tabs = [(T("Basic Details"), None, {}, "read"),
                        (T("Overview"), "overview"),
                        (T("Housing Units"), "shelter_unit"),
                        (T("Commissions"), "shelter_commission"),
                        (T("Journal"), "shelter_note"),
                        (T("Images"), "image"),
                        (T("Documents"), "document"),
                        ]

            rheader_fields = [["organisation_id",
                               ],
                              ["location_id",
                               ],
                              ]
            rheader_title = "name"

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table=resource.table, record=record)

    return rheader

# -----------------------------------------------------------------------------
def hrm_rheader(r, tabs=None):
    """ Custom resource headers for HRM """

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
            # Staff file

            tabs = [(T("Person Details"), None, {}, "read"),
                    (T("Contact Information"), "contacts"),
                    (T("Address"), "address"),
                    (T("ID"), "identity"),
                    (T("Staff Record"), "human_resource"),
                    (T("Photos"), "image"),
                    ]

            details = hr_details(record)
            rheader_fields = [[(T("User Account"), lambda i: details["account"])],
                              ]

            organisation = details["organisation"]
            if organisation:
                rheader_fields[0].insert(0, (T("Organization"), lambda i: organisation))

            rheader_title = s3_fullname

            rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
            rheader = rheader(r, table=resource.table, record=record)

            # Add profile picture
            from core import s3_avatar_represent
            record_id = record.id
            rheader.insert(0, A(s3_avatar_represent(record_id,
                                                    "pr_person",
                                                    _class = "rheader-avatar",
                                                    ),
                                _href=URL(f = "person",
                                          args = [record_id, "image"],
                                          vars = r.get_vars,
                                          ),
                                ))

    return rheader

# -----------------------------------------------------------------------------
def default_rheader(r, tabs=None):
    """ Custom resource header for user profile """

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
            # Personal profile
            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user_profile"),
                    (T("ID"), "identity"),
                    (T("Contact Information"), "contacts"),
                    (T("Address"), "address"),
                    (T("Staff Record"), "human_resource"),
                    ]
            rheader_fields = []
            rheader_title = s3_fullname

            rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
            rheader = rheader(r, table=resource.table, record=record)

    return rheader

# -----------------------------------------------------------------------------
def security_rheader(r, tabs=None):
    """ Custom resource header for SECURITY module """

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

        if tablename == "security_seized_item_depository":
            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Seized Items"), "seized_item"),
                        ]
            rheader_fields = []
            rheader_title = "name"

            rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
            rheader = rheader(r, table=resource.table, record=record)

    return rheader

# END =========================================================================
