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
#def cms_post_list_layout(list_id, item_id, resource, rfields, record):
#    """
#        dataList item renderer for Guides

#        @param list_id: the HTML ID of the list
#        @param item_id: the HTML ID of the item
#        @param resource: the S3Resource to render
#        @param rfields: the S3ResourceFields to render
#        @param record: the record as dict
#    """

#    T = current.T

#    table = current.s3db.cms_post

#    #raw = record._row
#    record_id = record["cms_post.id"]
#    title = record["cms_post.title"]
#    category = record["cms_post.series_id"]

#    # Toolbar
#    permit = current.auth.s3_has_permission
#    if permit("update", table, record_id=record_id):
#        edit_btn = A(ICON("edit"),
#                     SPAN("edit",
#                          _class = "show-for-sr",
#                          ),
#                     _href=URL(c="cms", f="post",
#                               args=[record_id, "update.popup"],
#                               vars={"refresh": list_id,
#                                     "record": record_id}
#                               ),
#                     _class="s3_modal",
#                     #_title=T("Edit %(type)s") % dict(type=series_title),
#                     _title=T("Edit"),
#                     )
#    else:
#        edit_btn = ""
#    if permit("delete", table, record_id=record_id):
#        delete_btn = A(ICON("delete"),
#                       SPAN("delete",
#                           _class = "show-for-sr",
#                           ),
#                      _class="dl-item-delete",
#                      _title=T("Delete"),
#                      )
#    else:
#        delete_btn = ""

#    toolbar = UL(LI(edit_btn,
#                    _class="item",
#                    ),
#                 LI(delete_btn,
#                    _class="item",
#                    ),
#                 _class="controls",
#                 )

#    item = DIV(toolbar,
#               category,
#               title,
#               _class = "card",
#               _id = item_id,
#               )

#    return item

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
    title = record["dc_target.name"]

    item = DIV(title,
               _class = "card",
               _id = item_id,
               )

    return item

# =============================================================================
def doc_document_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Guides

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    T = current.T

    table = current.s3db.doc_document

    raw = record._row
    record_id = record["doc_document.id"]
    title = raw["doc_document.name"]
    filename = raw["doc_document.file"] or ""
    url = raw["doc_document.url"] or ""
    comments = raw["doc_document.comments"] or ""
    #category = record["doc_document.series_id"]

    if filename:
        try:
            # Check whether file exists and extract the original
            # file name from the stored file name
            origname = current.s3db.doc_document.file.retrieve(filename)[0]
        except (IOError, TypeError):
            origname = current.messages["NONE"]
        doc_url = URL(c="default", f="download", args=[filename])
        body = P(ICON("attachment"),
                 " ",
                 SPAN(A(origname,
                        _href=doc_url,
                        )
                      ),
                 " ",
                 _class="card_1_line",
                 )
    elif url:
        body = P(ICON("link"),
                 " ",
                 SPAN(A(url,
                        _href=url,
                        )),
                 " ",
                 _class="card_1_line",
                 )
    else:
        # Shouldn't happen!
        body = P(_class="card_1_line")

    # Toolbar
    permit = current.auth.s3_has_permission
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     SPAN("edit",
                          _class = "show-for-sr",
                          ),
                     _href=URL(c="doc", f="document",
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

    toolbar = DIV(edit_btn,
                  delete_btn,
                  _class="edit-bar fright",
                  )

    # Render the item
    item = DIV(DIV(ICON("icon"),
                   SPAN(" %s" % title,
                        _class="card-title"),
                   toolbar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(body,
                           P(SPAN(comments),
                             " ",
                             _class="card_manylines",
                             ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class="thumbnail",
               _id=item_id,
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
    title = record["project_project.name"]

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
               title,
               _class = "card",
               _id = item_id,
               )

    return item

# END =========================================================================
