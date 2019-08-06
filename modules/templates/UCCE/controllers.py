# -*- coding: utf-8 -*-

from gluon import *
from s3 import json, ICON, S3CustomController, S3Method

# Compact JSON encoding
SEPARATORS = (",", ":")

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
                               args=[template_id, "editor"],
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
                       _href=URL(c="project", f="project",
                                 args=[record_id, "delete_confirm.popup"],
                                 #vars={"refresh": list_id,
                                 #      "record": record_id}
                                 ),
                      #_class="dl-item-delete",
                      _class="s3_modal",
                      _title=T("Delete project"), # Visible in both popup & popover
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
class dc_QuestionCreate(S3Method):
    """
        Create a Question
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "question":
            if r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                if not current.auth.s3_has_permission("create", table):
                    r.unauthorised()
                # Create record
                post_vars_get = r.post_vars.get
                field_type = post_vars_get("type")
                template_id = post_vars_get("template_id")
                if field_type and template_id:
                    question_id = table.insert(template_id = template_id,
                                               field_type = field_type,
                                               )
                    # Results (Empty Message so we don't get it shown to User)
                    current.response.headers["Content-Type"] = "application/json"
                    output = current.xml.json_message(True, 200, "",
                                                      question_id = question_id)
                else:
                    r.error(400, current.T("Invalid Parameters"))
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# =============================================================================
class dc_QuestionSave(S3Method):
    """
        Save a Question
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "question":
            if r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                record_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=record_id):
                    r.unauthorised()
                # Update Question
                post_vars_get = r.post_vars.get
                name = post_vars_get("name")
                if name:
                    mandatory = post_vars_get("mandatory")
                    settings = json.loads(post_vars_get("settings"))
                    current.db(table.id == record_id).update(name = name,
                                                             require_not_empty = mandatory,
                                                             settings = settings,
                                                             )
                    # Results (Empty Message so we don't get it shown to User)
                    current.response.headers["Content-Type"] = "application/json"
                    output = current.xml.json_message(True, 200, "")
                else:
                    r.error(400, current.T("Invalid Parameters"))
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

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
                current.response.s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.js" % r.application)

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

                S3CustomController._view(THEME, "confirm_popup.html")
                output = {"items": items,
                          "cancel_btn": cancel_btn,
                          "action_btn": action_btn,
                          }

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

            elif r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                target_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=target_id):
                    r.unauthorised()
                # Update Status
                current.db(table.id == target_id).update(status = 2)

                # Message
                current.response.headers["Content-Type"] = "application/json"
                output = current.xml.json_message(True, 200, current.T("Survey Activated"))

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

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
                current.response.s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.js" % r.application)

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

                S3CustomController._view(THEME, "confirm_popup.html")
                output = {"items": items,
                          "cancel_btn": cancel_btn,
                          "action_btn": action_btn,
                          }

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
                redirect(URL(c="dc", f="template", args=[r.record.template_id, "editor"]))

            elif r.http == "POST" and r.representation == "json":
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
                current.response.headers["Content-Type"] = "application/json"
                output = current.xml.json_message(True, 200, current.T("Survey Deactivated"))

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# =============================================================================
class dc_TargetName(S3Method):
    """
        Rename a Survey
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "target":
            if r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                target_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=target_id):
                    r.unauthorised()
                # Update Name
                name = r.post_vars.get("name")
                if name:
                    db = current.db
                    db(table.id == target_id).update(name = name)
                    ttable = current.s3db.dc_template
                    db(ttable.id == r.record.template_id).update(name = name)
                    # Message
                    current.response.headers["Content-Type"] = "application/json"
                    output = current.xml.json_message(True, 200, current.T("Survey Renamed"))
                else:
                    r.error(400, current.T("Invalid Parameters"))
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# =============================================================================
class dc_TemplateEditor(S3Method):
    """
        Survey Template Editor
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "template":
            if r.record and \
               r.interactive:

                T = current.T
                db = current.db
                s3db = current.s3db

                record = r.record
                record_id = record.id

                ttable = s3db.dc_target
                target = db(ttable.template_id == record_id).select(ttable.id,
                                                                    ttable.status,
                                                                    limitby = (0, 1)
                                                                    ).first()
                try:
                    target_id = target.id
                    target_status = target.status
                except AttributeError:
                    target_id = None
                    target_status = None

                if not target_status:
                    # No Target linked...something odd happening
                    button = ""
                elif target_status == 2:
                    # Active
                    button = A(T("Deactivate"),
                               _href=URL(c="dc", f="target",
                                         args=[target_id, "deactivate.popup"],
                                         ),
                               _class="action-btn s3_modal",
                               _title=T("Deactivate Survey"),
                               )
                else:
                    # Draft / Deactivated
                    button = A(T("Activate"),
                               _href=URL(c="dc", f="target",
                                         args=[target_id, "activate.popup"],
                                         ),
                               _class="action-btn s3_modal",
                               _title=T("Activate Survey"),
                               )

                ptable = s3db.project_project
                ltable = s3db.project_project_target
                query = (ltable.target_id == target_id) & \
                        (ltable.project_id == ptable.id)
                project = db(query).select(ptable.name,
                                           limitby = (0, 1)
                                           ).first()
                try:
                    project_name = project.name
                except AttributeError:
                    project_name = ""

                name_widget = INPUT(_value=record.name,
                                    _type="text",
                                    _id="survey-name",
                                    )
                name_widget["_data-id"] = target_id

                header = DIV(DIV("%s: " % T("Survey name"),
                                 name_widget,
                                 _class="medium-6 columns",
                                 ),
                             DIV("%s: " % T("Project"),
                                 project_name,
                                 _class="medium-3 columns",
                                 ),
                             DIV(button,
                                 _class="medium-3 columns",
                                 ),
                             _class="row"
                             )

                question_types = DIV(DIV(H2(T("Question types")),
                                         _class="row",
                                         ),
                                     DIV(DIV(ICON("edit"),
                                             _class="medium-2 columns",
                                             ),
                                         DIV(T("Data collector instructions"),
                                             _class="medium-9 columns",
                                             ),
                                         DIV(ICON("info-circle"),
                                             _class="medium-1 columns",
                                             ),
                                         _class="row draggable",
                                         _id="instructions",
                                         ),
                                     DIV(DIV(ICON("comment-alt"),
                                             _class="medium-2 columns",
                                             ),
                                         DIV(T("Text box"),
                                             _class="medium-9 columns",
                                             ),
                                         DIV(ICON("info-circle"),
                                             _class="medium-1 columns",
                                             ),
                                         _class="row draggable",
                                         _id="text",
                                         ),
                                     DIV(DIV(ICON("hashtag"),
                                             _class="medium-2 columns",
                                             ),
                                         DIV(T("Number question"),
                                             _class="medium-9 columns",
                                             ),
                                         DIV(ICON("info-circle"),
                                             _class="medium-1 columns",
                                             ),
                                         _class="row draggable",
                                         _id="number",
                                         ),
                                     DIV(DIV(ICON("list"),
                                             _class="medium-2 columns",
                                             ),
                                         DIV(T("Multiple choice question"),
                                             _class="medium-9 columns",
                                             ),
                                         DIV(ICON("info-circle"),
                                             _class="medium-1 columns",
                                             ),
                                         _class="row draggable",
                                         _id="multichoice",
                                         ),
                                     DIV(DIV(ICON("tasks"),
                                             _class="medium-2 columns",
                                             ),
                                         DIV(T("Likert-scale"),
                                             _class="medium-9 columns",
                                             ),
                                         DIV(ICON("info-circle"),
                                             _class="medium-1 columns",
                                             ),
                                         _class="row draggable",
                                         _id="likert",
                                         ),
                                     DIV(DIV(ICON("picture"),
                                             _class="medium-2 columns",
                                             ),
                                         DIV(T("Heatmap"),
                                             _class="medium-9 columns",
                                             ),
                                         DIV(ICON("info-circle"),
                                             _class="medium-1 columns",
                                             ),
                                         _class="row draggable",
                                         _id="heatmap",
                                         ),
                                     DIV(DIV(ICON("minus"),
                                             _class="medium-2 columns",
                                             ),
                                         DIV(T("Section / Page break"),
                                             _class="medium-9 columns",
                                             ),
                                         DIV(ICON("info-circle"),
                                             _class="medium-1 columns",
                                             ),
                                         _class="row draggable",
                                         _id="break",
                                         ),
                                     )

                hidden_input = INPUT(_type = "hidden",
                                     _id = "survey-layout",
                                     )
                hidden_input["_data-id"] = record_id
                if record.layout is not None:
                    hidden_input["_value"] = json.dumps(record.layout, separators=SEPARATORS)
                layout = DIV(hidden_input)

                # Inject JS
                appname = r.application
                scripts_append = current.response.s3.scripts.append
                scripts_append("/%s/static/themes/UCCE/js/s3.ui.template.js" % appname)
                scripts_append("/%s/static/themes/UCCE/js/template_editor.js" % appname)

                S3CustomController._view(THEME, "template_editor.html")
                output = {"question_types": question_types,
                          "header": header,
                          "layout": layout,
                          }

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# =============================================================================
class dc_TemplateSave(S3Method):
    """
        Save a Survey
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "template":
            if r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                record_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=record_id):
                    r.unauthorised()
                # Update Layout
                layout = r.post_vars.get("layout")
                if layout:
                    current.db(table.id == record_id).update(layout = layout)
                    # Results (Empty Message so we don't get it shown to User)
                    current.response.headers["Content-Type"] = "application/json"
                    output = current.xml.json_message(True, 200, "")
                else:
                    r.error(400, current.T("Invalid Parameters"))
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# =============================================================================
class dc_ProjectDelete(S3Method):
    """
        Delete a Project
            - confirmation popup
            - delete all linked Surveys
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "project":
            if r.representation == "popup":
                # Display interactive popup to confirm
                T = current.T
                # Inject JS to handle buttons with AJAX
                current.response.s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.js" % r.application)

                items = [DIV(P(T("Are you sure you want to delete the project? All surveys and data will be deleted as well.")),
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
                             LABEL(T("Delete all surveys within this project")),
                             _class="row",
                             ),
                         ]
                cancel_btn = A(T("Cancel"),
                               _href="#",
                               _class="button secondary round",
                               )
                action_btn = A(T("Delete project"),
                               _href=URL(c="project", f="project",
                                         args=[r.id, "delete_confirm"]),
                               _class="button round disabled",
                               _target="_top",
                               )

                S3CustomController._view(THEME, "confirm_popup.html")
                output = {"items": items,
                          "cancel_btn": cancel_btn,
                          "action_btn": action_btn,
                          }

            elif r.interactive:
                # Popup has confirmed the action
                # Action the request
                table = r.table
                project_id = r.id
                if not current.auth.s3_has_permission("delete", table, record_id=project_id):
                    r.unauthorised()
                db = current.db
                s3db = current.s3db
                # Lookup Targets
                ltable = s3db.project_project_target
                links = db(ltable.project_id == project_id).select(ltable.target_id)
                target_ids = [l.target_id for l in links]
                # Delete Responses
                rtable = s3db.dc_response
                resource = s3db.resource("dc_response", filter=(rtable.target_id.belongs(target_ids)))
                resource.delete()
                # Lookup Templates
                ttable = s3db.dc_target
                query = (ttable.id.belongs(target_ids))
                targets = db(query).select(ttable.template_id)
                template_ids = [t.template_id for t in targets]
                # Delete Targets
                resource = s3db.resource("dc_target", filter=(query))
                resource.delete()
                # Delete Templates
                tetable = s3db.dc_template
                resource = s3db.resource("dc_template", filter=(tetable.id.belongs(template_ids)))
                resource.delete()
                # Delete Project
                resource = s3db.resource("project_project", filter=(table.id == project_id))
                resource.delete()
                # Message
                current.session.confirmation = current.T("Project deleted")
                # Redirect
                # @ToDo: Do this without a full page refresh
                # - self.parent.dl.datalist('reloadAjaxItem', project_id)
                # - message
                # - self.parent.S3.popup_remove();
                redirect(URL(c="project", f="project", args=["datalist"]))

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# END =========================================================================
