# -*- coding: utf-8 -*-

from gluon import *
from s3 import ICON, S3CustomController

THEME = "UCCE"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        self._view(THEME, "index.html")
        return {}

# =============================================================================
def cms_post_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Guides

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    T = current.T

    table = current.s3db.cms_post

    #raw = record._row
    record_id = record["cms_post.id"]
    name = record["cms_post.title"]
    series = record["cms_post.series_id"]

    # Toolbar
    permit = current.auth.s3_has_permission
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     SPAN("edit",
                          _class = "show-for-sr",
                          ),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}
                               ),
                     _class="s3_modal",
                     #_title=T("Edit %(type)s") % dict(type=series_title),
                     _title=T("Edit"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       SPAN("delete",
                           _class = "show-for-sr",
                           ),
                      _class="dl-item-delete",
                      _title=T("Delete"),
                      )
    else:
        delete_btn = ""

    toolbar = UL(LI(edit_btn,
                    _class="item",
                    ),
                 LI(delete_btn,
                    _class="item",
                    ),
                 _class="controls",
                 )

    item = DIV(toolbar,
               series,
               name,
               _class = "card",
               _id = item_id,
               )

    return item

# =============================================================================
def dc_target_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Reports.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    T = current.T

    #raw = record._row
    record_id = record["dc_target.id"]
    survey_name = record["dc_target.name"]

    item = DIV(survey_name,
               _class = "card",
               _id = item_id,
               )

    return item

# =============================================================================
def project_project_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Projects.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    T = current.T

    table = current.s3db.project_project

    #raw = record._row
    record_id = record["project_project.id"]
    name = record["project_project.name"]

    # Toolbar
    permit = current.auth.s3_has_permission
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     SPAN("edit",
                          _class = "show-for-sr",
                          ),
                     _href=URL(c="project", f="project",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}
                               ),
                     _class="s3_modal",
                     #_title=T("Edit %(type)s") % dict(type=series_title),
                     _title=T("Edit"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       SPAN("delete",
                           _class = "show-for-sr",
                           ),
                      _class="dl-item-delete",
                      _title=T("Delete"),
                      )
    else:
        delete_btn = ""

    toolbar = UL(LI(edit_btn,
                    _class="item",
                    ),
                 LI(delete_btn,
                    _class="item",
                    ),
                 _class="controls",
                 )

    item = DIV(toolbar,
               name,
               _class = "card",
               _id = item_id,
               )

    return item

# END =========================================================================
