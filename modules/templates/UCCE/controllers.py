# -*- coding: utf-8 -*-

from gluon import *
from s3 import ICON, S3CustomController, S3Method

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
    master_key = raw["auth_masterkey.name"]
    target_ids = raw["project_project_target.target_id"]

    if target_ids:
        if isinstance(target_ids, list):
            query = (ttable.id.belongs(target_ids))
        else:
            query = (ttable.id == target_ids)
        targets = db(query).select(ttable.id,
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
        status = target.status
        if permit("update", ttable, record_id=target_id):
            if status == 1:
                # Draft - can Edit freely
                edit_url = URL(c="dc", f="template",
                               args=[template_id, "question"],
                               )
                _title = T("Edit") # Only used in popover
                _class = ""
            else:
                # Activated/Deactivated - need to change status before can edit
                edit_url = URL(c="dc", f="target",
                               args=[target_id, "deactivate.popup"],
                               )
                _title = T("Edit survey") # Used in popup as well as popover
                _class = "s3_modal"
 
            edit_btn = A(ICON("edit"),
                         SPAN("edit",
                              _class = "show-for-sr",
                              ),
                         _href=edit_url,
                         _title=_title,
                         _class=_class,
                         )
        else:
            edit_btn = ""

        if permit("delete", ttable, record_id=target_id):
            delete_btn = A(ICON("delete"),
                           SPAN("delete",
                                _class = "show-for-sr",
                                ),
                           _class="dl-survey-delete",
                           _id="survey-%s" % target_id,
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
            switch_id = "target_status-%s" % target_id
            if status == 2:
                checkbox = INPUT(_id=switch_id,
                                 _type="checkbox",
                                 _checked="checked",
                                 _class="switch-input",
                                 )
            elif status == 3:
                checkbox = INPUT(_id=switch_id,
                                 _type="checkbox",
                                 _class="switch-input",
                                 )
            switch = DIV(checkbox,
                         # Inner Labels require Foundation 6
                         # https://foundation.zurb.com/sites/docs/switch.html#inner-labels
                         # - have backported the Foundation 6 CSS into style.css instead of using the Foundation 5 SCSS
                         LABEL(SPAN("ON",
                                    _class="switch-active",
                                    #_aria-hidden="true",
                                    ),
                               SPAN("OFF",
                                    _class="switch-inactive",
                                    #_aria-hidden="true",
                                    ),
                               _for = switch_id,
                               _class="switch-paddle rounded",
                               ),
                         _class="switch large",
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

# =============================================================================
class dc_TargetActivate(S3Method):
    """
        Activate a Survey
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "target":
           if r.representation == "popup":
                # Display interactive popup to confirm
                T = current.T
                # Inject JS to handle buttons with AJAX
                current.response.s3.scripts.append("/%s/static/themes/UCCE/js/activate_popup.js" % r.application)

                items = [DIV(P(T("Once the survey is activated, it will be linked to the respective project master key.")),
                             P(T("Survey must be deactivated before making any edits.")),
                             _class="row",
                             ),
                         ]
                cancel_btn = A(T("Cancel"),
                               _href="#",
                               _class="button secondary round",
                               )
                action_btn = A(T("Activate survey"),
                               _href=URL(c="dc", f="target",
                                         args=[r.id, "activate"]),
                               _class="button alert round",
                               _target="_top",
                               )
                output = {"items": items,
                          "cancel_btn": cancel_btn,
                          "action_btn": action_btn,
                          }
                S3CustomController._view(THEME, "activate_popup.html")
                return output
           elif r.interactive:
                # Popup has confirmed the action
                # Action the Request
                table = r.table
                target_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=target_id):
                    r.unauthorised()
                # Update Status
                current.db(table.id == target_id).update(status = 2)
                # Message
                current.session.confirmation = current.T("Survey Activated")
                # Redirect
                redirect(URL(c="project", f="project", args="datalist"))
           elif r.http == "POST" and \
            r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                target_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=target_id):
                    r.unauthorised()
                # Update Status
                current.db(table.id == target_id).update(status = 2)
                # Message
                output = current.xml.json_message(True, 200, current.T("Survey Activated"))
                current.response.headers["Content-Type"] = "application/json"
                return output
        r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class dc_TargetDeactivate(S3Method):
    """
        Deactivate a Survey
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "target":
           if r.representation == "popup":
                # Display interactive popup to confirm
                T = current.T
                # Inject JS to handle buttons with AJAX
                current.response.s3.scripts.append("/%s/static/themes/UCCE/js/activate_popup.js" % r.application)

                items = [DIV(P(T("In order to edit it, the survey will be deactivated and all data collected will be deleted.")),
                             _class="row",
                             ),
                         DIV(INPUT(_type="checkbox",
                                   _id="checkbox1",
                                   ),
                             LABEL(T("Delete all collected data")),
                             _class="row",
                             ),
                         DIV(INPUT(_type="checkbox",
                                   _id="checkbox2",
                                   ),
                             LABEL(T("Deactivate survey")),
                             _class="row",
                             ),
                         ]
                cancel_btn = A(T("Cancel"),
                               _href="#",
                               _class="button secondary round",
                               )
                action_btn = A(T("Edit survey"),
                               _href=URL(c="dc", f="target",
                                         args=[r.id, "deactivate"]),
                               _class="button round disabled",
                               _target="_top",
                               )
                output = {"items": items,
                          "cancel_btn": cancel_btn,
                          "action_btn": action_btn,
                          }
                S3CustomController._view(THEME, "activate_popup.html")
                return output
           elif r.interactive:
                # Popup has confirmed the action
                # Action the Request
                table = r.table
                target_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=target_id):
                    r.unauthorised()
                s3db = current.s3db
                # Delete Responses
                rtable = s3db.dc_response
                resource = s3db.resource("dc_response", filter=(rtable.target_id == target_id))
                resource.delete()
                # Update Status
                current.db(table.id == target_id).update(status = 3)
                # Message
                current.session.confirmation = current.T("Survey Deactivated")
                # Redirect
                redirect(URL(c="dc", f="template", args=[r.record.template_id, "question"]))
           elif r.http == "POST" and \
            r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                target_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=target_id):
                    r.unauthorised()
                s3db = current.s3db
                # Delete Responses
                rtable = s3db.dc_response
                resource = s3db.resource("dc_response", filter=(rtable.target_id == target_id))
                resource.delete()
                # Update Status
                current.db(table.id == target_id).update(status = 3)
                # Message
                output = current.xml.json_message(True, 200, current.T("Survey Deactivated"))
                current.response.headers["Content-Type"] = "application/json"
                return output
        r.error(405, current.ERROR.BAD_METHOD)

# END =========================================================================
