# -*- coding: utf-8 -*-

"""
    Custom rheaders for RLP template

    @license: MIT
"""

from gluon import current

from s3 import s3_fullname

from .helpers import rlp_deployed_with_org

# =============================================================================
def rlp_vol_rheader(r, tabs=None):
    """ Custom rheader for vol/person """

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
        db = current.db
        s3db = current.s3db
        auth = current.auth

        coordinator = auth.s3_has_role("COORDINATOR")

        if tablename == "pr_person":

            if coordinator:
                delegation_tab = (T("Recruitment"), "delegation")
            else:
                delegation_tab = (T("Recruitment"), "delegation/")

            if not tabs:
                tabs = [(T("Personal Data"), None),
                        (T("Skills / Resources"), "competency"),
                        delegation_tab,
                        ]

            volunteer = resource.select(["person_details.alias",
                                         "pool_membership.group_id",
                                         "pool_membership.group_id$group_type",
                                         "date_of_birth",
                                         "age",
                                         "occupation_type_person.occupation_type_id",
                                         "volunteer_record.site_id",
                                         ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows
            if volunteer:
                # Extract volunteer details
                volunteer = volunteer[0]
                if coordinator or rlp_deployed_with_org(record.id):
                    name = s3_fullname
                else:
                    name = lambda row: volunteer["pr_person_details.alias"]
                pool = lambda row: volunteer["pr_pool_membership_group_membership.group_id"]
                age = lambda row: volunteer["pr_person.age"]
                occupation_type = lambda row: volunteer["pr_occupation_type_person.occupation_type_id"]
            else:
                # Target record exists, but doesn't match filters
                return None

            rheader_fields = [[(T("ID"), "pe_label"),
                               (T("Pool"), pool),
                               ],
                              [(T("Age"), age),
                               (T("Occupation Type"), occupation_type),
                               ],
                              [("", None),
                               ("", None),
                               ]
                              ]

            if coordinator:
                raw = volunteer["_row"]
                site_id = raw["hrm_volunteer_record_human_resource.site_id"]
                if site_id:
                    # Get site details
                    otable = s3db.org_office
                    query = (otable.site_id == site_id) & \
                            (otable.deleted == False)
                    office = db(query).select(otable.name,
                                              otable.phone1,
                                              otable.email,
                                              limitby = (0, 1),
                                              ).first()
                    if office:
                        rheader_fields[0].append((T("Office##gov"),
                                                  lambda row: office.name,
                                                  ))
                        rheader_fields[1].append((T("Office Phone##gov"),
                                                  lambda row: office.phone1,
                                                  ))
                        rheader_fields[2].append((T("Office Email##gov"),
                                                  lambda row: office.email,
                                                  ))

            open_pool_member = (volunteer["_row"]["pr_group.group_type"] == 21)
            if not coordinator and open_pool_member:
                # Recruitment hint
                from gluon import SPAN
                hint = lambda row: SPAN(T("Please contact the volunteer directly for deployment"),
                                        _class="direct-contact-hint"
                                        )
                rheader_fields.append([(None, hint, 5)])

        rheader = S3ResourceHeader(rheader_fields, tabs, title=name)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )
    return rheader

# =============================================================================
def rlp_profile_rheader(r, tabs=None):
    """ Custom rheader for default/person """

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

        if tablename == "pr_person":

            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user_profile"),
                    (T("Address"), "address"),
                    (T("Contact Information"), "contacts"),
                    (T("Skills"), "competency"),
                    ]

            rheader_fields = [[(T("ID"), "pe_label"),
                               ],
                              [(T("Name"), s3_fullname),
                               ],
                              ["date_of_birth",
                               ]
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )
    return rheader

# =============================================================================
def rlp_org_rheader(r, tabs=None):
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

        if tablename == "org_organisation":

            if not tabs:
                tabs = [(T("Organisation"), None),
                        (T("Administrative Offices"), "office"),
                        (T("Facilities"), "facility"),
                        (T("Staff"), "human_resource"),
                        (T("Volunteer Pools"), "pool"),
                        ]

            rheader_fields = [["name",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# =============================================================================
def rlp_delegation_rheader(r, tabs=None):
    """ hrm_delegation custom resource header """

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

        if tablename == "hrm_delegation":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Notifications"), "delegation_message"),
                        (T("Notes"), "delegation_note"),
                        ]

            rheader_fields = [["organisation_id",
                               "date",
                               "status",
                               ],
                              ["person_id",
                               "end_date",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# END =========================================================================
