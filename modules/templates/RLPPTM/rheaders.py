# -*- coding: utf-8 -*-

"""
    Custom rheaders for RLPPTM template

    @license: MIT
"""

from gluon import current

from s3 import s3_rheader_resource, S3ResourceHeader

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
                # TODO additionally check if record belongs to schools group
                if current.auth.s3_has_role("ORG_GROUP_ADMIN"):
                    invite_tab = (T("Invite"), "invite")
                else:
                    invite_tab = None

                tabs = [(T("Organisation"), None),
                        invite_tab,
                        # TODO Activate for Org-group "COVID-19 Test Stations":
                        #(T("Administrative Offices"), "office"),
                        # TODO Activate for Org-group "Schools":
                        #(T("Facilities"), "facility"),
                        (T("Staff"), "human_resource"),
                        ]


            rheader_title = "name"
            rheader_fields = []

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# END =========================================================================
