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
def dc_target_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Reports.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    #T = current.T

    #raw = record._row
    #record_id = record["dc_target.id"]
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
    db = current.db
    s3db = current.s3db

    table = s3db.project_project
    ttable = s3db.dc_target

    raw = record._row
    record_id = record["project_project.id"]
    title = record["project_project.name"]
    master_key = raw["project_master_key_project_tag.value"]
    target_ids = raw["project_project_target.target_id"]

    if target_ids:
        targets = db(ttable.id.belongs(target_ids)).select(ttable.id,
                                                           ttable.name,
                                                           ttable.status,
                                                           ttable.template_id,
                                                           )
        rtable = s3db.dc_response
    else:
        targets = []

    permit = current.auth.s3_has_permission

    body = DIV(_class="row")
    bappend = body.append
    for target in targets:
        target_id = target.id
        template_id = target.template_id
        if permit("update", ttable, record_id=target_id):
            edit_btn = A(ICON("edit"),
                         SPAN("edit",
                              _class = "show-for-sr",
                              ),
                         _href=URL(c="dc", f="template",
                                   args=[template_id, "question"],
                                   ),
                         #_title=T("Edit %(type)s") % dict(type=series_title),
                         _title=T("Edit"),
                         )
        else:
            edit_btn = ""
        if permit("delete", ttable, record_id=target_id):
            delete_btn = A(ICON("delete"),
                           SPAN("delete",
                               _class = "show-for-sr",
                               ),
                          _href=URL(c="dc", f="target",
                                   args=[target_id, "delete"],
                                   vars={"refresh": list_id,
                                         "record": record_id}
                                   ),
                           _title=T("Delete"),
                          )
        else:
            delete_btn = ""
        if permit("create", ttable):
            copy_btn = A(ICON("copy"),
                         SPAN("copy",
                              _class = "show-for-sr",
                             ),
                         _href=URL(c="dc", f="target",
                                   args=[target_id, "copy"],
                                   vars={"refresh": list_id}
                                   ),
                         _title=T("Copy"),
                         )
        else:
            copy_btn = ""
        status = target.status
        if status == 1:
            # Draft
            responses = DIV("Draft")
            upload_btn = ""
            report_btn = ""
            switch = ""
        else:
            responses = db(rtable.target_id == target_id).count()
            responses = DIV("%s Responses" % responses)
            upload_btn = A(ICON("upload"),
                           SPAN("upload",
                                _class = "show-for-sr",
                                ),
                           _href=URL(c="dc", f="target",
                                     args=[target_id, "upload"],
                                     ),
                           _title=T("Upload"),
                           )
            report_btn = A(ICON("bar-chart"),
                           SPAN("report",
                                _class = "show-for-sr",
                                ),
                           _href=URL(c="dc", f="target",
                                     args=[target_id, "report"],
                                     ),
                           _title=T("Report"),
                           )
            switch_id = "target_status_%s" % target_id
            if status == 2:
                input = INPUT(_id=switch_id,
                              _type="checkbox",
                              _checked="checked",
                              )
            elif status == 3:
                input = INPUT(_id=switch_id,
                              _type="checkbox",
                              )
            switch = DIV(input,
                         # Inner Labels require Foundation 6
                         # https://foundation.zurb.com/sites/docs/switch.html#inner-labels
                         LABEL(SPAN("ON",
                                    _class="switch-active",
                                    #_aria-hidden="true",
                                    ),
                               SPAN("OFF",
                                    _class="switch-inactive",
                                    #_aria-hidden="true",
                                    ),
                               _for=switch_id,
                               ),
                         _class="switch round large",
                         )

        bappend(DIV(DIV(_class="card-inner-header"),
                    DIV(target.name),
                    responses,
                    DIV(edit_btn, copy_btn, delete_btn),
                    DIV(upload_btn, report_btn),
                    switch,
                    _class="thumbnail medium-2 columns",
                    ))

    if permit("create", ttable):
        # Create Button
        create_btn = A(ICON("plus"),
                     SPAN("Create new survey",
                          ),
                     _href=URL(c="project", f="project",
                               args=[record_id, "target", "create"],
                               ),
                     _title=T("Create new survey"),
                     )
        bappend(DIV(create_btn,
                    _class="thumbnail medium-2 columns end",
                    ))


    # Toolbar
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
    if permit("create", table):
        copy_btn = A(ICON("copy"),
                     SPAN("copy",
                          _class = "show-for-sr",
                         ),
                     _href=URL(c="project", f="project",
                               args=[record_id, "copy"],
                               vars={"refresh": list_id}
                               ),
                     _title=T("Copy"),
                     )
    else:
        copy_btn = ""

    toolbar = DIV(edit_btn,
                  copy_btn,
                  delete_btn,
                  _class="edit-bar fright",
                  )

    item = DIV(DIV(ICON("icon"),
                   SPAN(" %s" % title,
                        _class="card-title"),
                   toolbar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(body,
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               DIV(SPAN("Master key: %s" % master_key,
                        _class="card-title"),
                   _class="card-header",
                   ),
               _class="thumbnail",
               _id=item_id,
               )

    return item

# END =========================================================================
