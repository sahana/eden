# -*- coding: utf-8 -*-

"""
    Custom rheaders for RLPPTM template

    @license: MIT
"""

from gluon import current

from s3 import S3ResourceHeader, s3_rheader_resource

# =============================================================================
def rlpptm_org_rheader(r, tabs=None):
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

            if not tabs:

                invite_tab = None
                sites_tab = None

                db = current.db
                s3db = current.s3db
                gtable = s3db.org_group
                mtable = s3db.org_group_membership
                query = (mtable.organisation_id == record.id) & \
                        (mtable.group_id == gtable.id)
                group = db(query).select(gtable.name,
                                         limitby = (0, 1)
                                         ).first()
                if group:
                    if group.name == "COVID-19 Test Stations":
                        sites_tab = (T("Test Stations"), "facility")
                    elif group.name == "Schools":
                        sites_tab = (T("Administrative Offices"), "office")
                        if current.auth.s3_has_role("ORG_GROUP_ADMIN"):
                            invite_tab = (T("Invite"), "invite")

                tabs = [(T("Organisation"), None),
                        invite_tab,
                        sites_tab,
                        (T("Staff"), "human_resource"),
                        ]

            rheader_title = "name"
            rheader_fields = []

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# =============================================================================
def rlpptm_profile_rheader(r, tabs=None):
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

# END =========================================================================
