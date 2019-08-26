# -*- coding: utf-8 -*-

import os

from gluon import *
from gluon.storage import Storage

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
    #url = raw["doc_document.url"] or ""
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
    #elif url:
    #    body = P(ICON("link"),
    #             " ",
    #             SPAN(A(url,
    #                    _href=url,
    #                    )),
    #             " ",
    #             _class="card_1_line",
    #             )
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
    item = DIV(DIV(#ICON(icon),
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
                               args=[target_id, "edit_confirm.popup"],
                               )
                _title = T("Edit survey") # Used in popup as well as popover
                _class = "s3_modal"

            edit_btn = A(ICON("survey-edit"),
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
            delete_btn = A(ICON("survey-delete"),
                           SPAN("delete",
                                _class = "show-for-sr",
                                ),
                           _href=URL(c="dc", f="target",
                                     args=[target_id, "delete_confirm.popup"],
                                     #vars={"refresh": list_id,
                                     #      "record": record_id}
                                     ),
                           #_class="dl-survey-delete",
                           _class="s3_modal",
                           _title=T("Delete survey"), # Visible in both popup & popover
                           )
        else:
            delete_btn = ""
        if permit("create", ttable):
            copy_btn = A(ICON("survey-copy"),
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
            export_btn = ""
            preview_btn = ""
            report_btn = ""
            switch = ""
        else:
            responses = db(rtable.target_id == target_id).count()
            responses = DIV("%s Responses" % responses)
            export_btn = A(ICON("upload"),
                           SPAN("export",
                                _class = "show-for-sr",
                                ),
                           _href=URL(c="dc", f="target",
                                     args=[target_id, "export"],
                                     ),
                           _title=T("Export"),
                           )
            preview_btn = A(ICON("eye"),
                            SPAN("preview",
                                 _class = "show-for-sr",
                                 ),
                            _href=URL(c="dc", f="template",
                                      args=[template_id, "editor"],
                                      ),
                            _title=T("Preview"),
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
                    # Copy button disabled until implemented
                    #DIV(edit_btn, copy_btn, delete_btn),
                    DIV(edit_btn, delete_btn),
                    DIV(preview_btn, export_btn, report_btn),
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
                  # Copy button disabled until implemented
                  #copy_btn,
                  delete_btn,
                  _class="edit-bar fright",
                  )

    item = DIV(DIV(#ICON(icon),
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
                        ),
                   _class="card-footer",
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
                    new_vars = Storage(template_id = template_id,
                                       field_type = field_type,
                                       )
                    question_id = table.insert(**new_vars)
                    new_vars.id = question_id
                    onaccept = current.s3db.get_config("dc_question", "onaccept")
                    onaccept(Storage(vars = new_vars))

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
class dc_QuestionImageDelete(S3Method):
    """
        Delete an Image for a Question
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

                filename = r.record.file
                if filename:
                    # Delete from filesystem
                    os.remove(os.path.join(table.file.uploadfolder, filename))

                    # Update record
                    current.db(table.id == record_id).update(file = None)

                # Results (Empty Message so we don't get it shown to User)
                current.response.headers["Content-Type"] = "application/json"
                output = current.xml.json_message(True, 200, "")
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# =============================================================================
class dc_QuestionImageUpload(S3Method):
    """
        Upload an Image for a Question
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
                field_storage = r.post_vars.get("file")
                if field_storage not in ("", None):

                    # Store in filesystem
                    field = table.file
                    newfilename = field.store(field_storage.file,
                                              field_storage.filename,
                                              field.uploadfolder)

                    # Update record
                    current.db(table.id == record_id).update(file = newfilename)

                    # Results (Empty Message so we don't get it shown to User)
                    current.response.headers["Content-Type"] = "application/json"
                    output = current.xml.json_message(True, 200, "",
                                                      file = newfilename)
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
                    db = current.db
                    mandatory = post_vars_get("mandatory")
                    options = post_vars_get("options")
                    #if options:
                    #    options = json.loads(options)
                    settings = post_vars_get("settings")
                    #if settings:
                    #    settings = json.loads(settings)
                    old_settings = r.record.settings or {}
                    other_id = old_settings.get("other_id")
                    if other_id:
                        # Preserve the reference to the other Field
                        # - Editor JS is unaware of this attribute
                        settings["other_id"] = other_id
                    db(table.id == record_id).update(name = name,
                                                     # Always use isNotEmpty validator now, so only applies if field is visible
                                                     #require_not_empty = mandatory,
                                                     options = options,
                                                     settings = settings,
                                                     )
                    onaccept = current.s3db.get_config("dc_question", "onaccept")
                    onaccept(Storage(vars = Storage(id = record_id)))

                    # Translation
                    name_l10n = post_vars_get("name_l10n")
                    options_l10n = post_vars_get("options_l10n")
                    if name_l10n or options_l10n:
                        s3db = current.s3db
                        ltable = s3db.dc_template_l10n
                        l10n = db(ltable.template_id == r.record.template_id).select(ltable.language,
                                                                                     limitby = (0, 1)
                                                                                     ).first()
                        if l10n:
                            l10n = l10n.language
                            ltable = s3db.dc_question_l10n
                            exists = db(ltable.question_id == record_id).select(ltable.id,
                                                                                limitby = (0, 1)
                                                                                ).first()
                            new_vars = {"name_l10n": name_l10n,
                                        "language": l10n,
                                        }
                            if options_l10n:
                                new_vars["options_l10n"] = options_l10n
                            if exists:
                                exists.update_record(**new_vars)
                            else:
                                new_vars["question_id"] = record_id
                                ltable.insert(**new_vars)

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
                s3 = current.response.s3
                if s3.debug:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.min.js" % r.application)

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
                               _class="button round",
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
                self.update(r)

                # Message
                current.session.confirmation = current.T("Survey Activated")

                # Redirect
                redirect(URL(c="project", f="project", args="datalist"))

            elif r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                self.update(r)

                # Message
                current.response.headers["Content-Type"] = "application/json"
                output = current.xml.json_message(True, 200, current.T("Survey Activated"))

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def update(r):
        """
            DRY Helper to check permissions and update the Data in the Database
        """

        table = r.table
        target_id = r.id
        if not current.auth.s3_has_permission("update", table, record_id=target_id):
            r.unauthorised()

        # Update the Data in the Database
        db = current.db
        s3db = current.s3db

        # Update Status
        db(table.id == target_id).update(status = 2)

        # Lookup the Dynamic Table
        template_id = r.record.template_id
        tetable = s3db.dc_template
        template = db(tetable.id == template_id).select(tetable.table_id,
                                                        tetable.layout,
                                                        limitby = (0, 1)
                                                        ).first()
        if not template:
            current.log.error("Error Activating Target %s: Cannot find Template!" % target_id)
            return

        # Convert dc_template.layout to s3_table.settings["mobile_form"]
        layout = template.layout or []
        mobile_form = []
        mappend = mobile_form.append

        # Read Questions
        qtable = db.dc_question
        ftable = db.s3_field
        query = (qtable.template_id == template_id) & \
                (qtable.deleted == False)
        left = [ftable.on(ftable.id == qtable.field_id),
                ]
        rows = db(query).select(ftable.name,
                                #ftable.label,
                                qtable.id,
                                left = left
                                )
        questions = {}
        for row in rows:
            _row = row["s3_field"]
            questions[row["dc_question.id"]] = {"name": _row.name,
                                                #"label": _row.label,
                                                }

        for posn in range(1, len(layout) + 1):
            item = layout[str(posn)]
            item_type = item["type"]
            if item_type == "question":
                question = questions[item["id"]]
                fname = question["name"]
                if fname:
                    displayLogic = item.get("displayLogic")
                    if displayLogic:
                        # Convert Question ID to fieldname
                        dq = questions.get(displayLogic["id"])
                        if dq:
                            dfname = dq["name"]
                            displayLogic["field"] = fname
                            displayLogic.pop("id")
                            item = {"type": "input",
                                    "field": fname,
                                    "displayLogic": displayLogic,
                                    # Read from model
                                    #"label": question["label"],
                                    }
                    else:
                        item = fname
                    mappend(item)

            elif item_type == "instructions":
                new_item = {"type": "instructions"}
                do = item.get("do")
                say = item.get("say")
                new_item["do"] = do.get("text")
                new_item["say"] = say.get("text")
                # @ToDo: l10n
                displayLogic = item.get("displayLogic")
                if displayLogic:
                    # Convert Question ID to fieldname
                    dq = questions.get(displayLogic["id"])
                    if dq:
                        dfname = dq["name"]
                        displayLogic["field"] = fname
                        displayLogic.pop("id")
                        new_item["displayLogic"] = displayLogic
                        
                mappend(new_item)

            elif item_type == "break":
                mappend({"type": "section-break"})

        # Update Dynamic Table
        db(s3db.s3_table.id == template.table_id).update(settings = {"mobile_form": mobile_form},
                                                         mobile_form = True)

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
            if r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                table = r.table
                target_id = r.id
                if not current.auth.s3_has_permission("update", table, record_id=target_id):
                    r.unauthorised()

                db = current.db
                s3db = current.s3db

                # Update Status
                db(table.id == target_id).update(status = 3)

                # Lookup the Dynamic Table
                tetable = s3db.dc_template
                template = db(tetable.id == r.record.template_id).select(tetable.table_id,
                                                                         limitby = (0, 1)
                                                                         ).first()
                if template:
                    # Update Dynamic Table
                    db(s3db.s3_table.id == template.table_id).update(mobile_form = False)

                # Message
                current.response.headers["Content-Type"] = "application/json"
                output = current.xml.json_message(True, 200, current.T("Survey Deactivated"))

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

# =============================================================================
class dc_TargetEdit(S3Method):
    """
        Edit a Survey
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
                s3 = current.response.s3
                if s3.debug:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.min.js" % r.application)

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
                                         args=[r.id, "edit_confirm"]),
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
                self.update(r)

                # Message
                current.session.confirmation = current.T("Survey Deactivated")

                # Redirect
                redirect(URL(c="dc", f="template", args=[r.record.template_id, "editor"]))

            elif r.http == "POST" and r.representation == "json":
                # AJAX method
                # Action the request
                self.update(r)

                # Message
                current.response.headers["Content-Type"] = "application/json"
                output = current.xml.json_message(True, 200, current.T("Survey Deactivated"))

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(404, current.ERROR.BAD_RESOURCE)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def update(r):
        """
            DRY Helper to check permissions and update the Data in the Database
        """

        table = r.table
        target_id = r.id
        if not current.auth.s3_has_permission("update", table, record_id=target_id):
            r.unauthorised()

        # Update the Data in the Database
        db = current.db
        s3db = current.s3db

        # Delete Responses
        rtable = s3db.dc_response
        resource = s3db.resource("dc_response", filter=(rtable.target_id == target_id))
        resource.delete()

        # Update Status
        db(table.id == target_id).update(status = 1)

        # Lookup the Dynamic Table
        tetable = s3db.dc_template
        template = db(tetable.id == r.record.template_id).select(tetable.table_id,
                                                                 limitby = (0, 1)
                                                                 ).first()
        if template:
            # Update Dynamic Table
            db(s3db.s3_table.id == template.table_id).update(mobile_form = False)

# =============================================================================
class dc_TargetDelete(S3Method):
    """
        Delete a Survey
            - confirmation popup
            - delete linked Template
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
                s3 = current.response.s3
                if s3.debug:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.min.js" % r.application)

                items = [DIV(P(T("Are you sure you want to delete the survey? All data will be deleted as well.")),
                             _class="row",
                             ),
                         DIV(INPUT(_type="checkbox",
                                   _id="checkbox1",
                                   ),
                             LABEL(T("Delete all collected data")),
                             _class="row",
                             ),
                         ]
                cancel_btn = A(T("Cancel"),
                               _href="#",
                               _class="button secondary round",
                               )
                action_btn = A(T("Delete survey"),
                               _href=URL(c="dc", f="target",
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
                target_id = r.id
                if not current.auth.s3_has_permission("delete", table, record_id=target_id):
                    r.unauthorised()
                db = current.db
                s3db = current.s3db

                # Delete Responses
                rtable = s3db.dc_response
                resource = s3db.resource("dc_response", filter=(rtable.target_id == target_id))
                resource.delete()

                # Lookup Template
                query = (table.id == target_id)
                target = db(query).select(table.template_id,
                                          limitby = (0,1)
                                          ).first()
                template_id = target.template_id

                # Delete Target
                resource = s3db.resource("dc_target", filter=(query))
                resource.delete()

                # Delete Template
                tetable = s3db.dc_template
                resource = s3db.resource("dc_template", filter=(tetable.id == template_id))
                resource.delete()

                # Message
                current.session.confirmation = current.T("Survey deleted")
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

                    # Update Target
                    db(table.id == target_id).update(name = name)

                    # Update Template
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
class dc_TargetL10n(S3Method):
    """
        Change the language of a Survey

        NB Currently each Survey is only ever translated into a single language
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
                # Update Language
                l10n = r.post_vars.get("l10n")
                if l10n is not None:
                    db = current.db
                    s3db = current.s3db

                    # Update Target
                    ltable = s3db.dc_target_l10n
                    exists = db(ltable.target_id == target_id).select(ltable.id,
                                                                      ltable.language,
                                                                      limitby = (0, 1)
                                                                      ).first()
                    if exists:
                        if exists.language != l10n:
                            exists.update_record(language = l10n)
                    else:
                        ltable.insert(target_id = target_id,
                                      language = l10n,
                                      )

                    # Update Template
                    template_id = r.record.template_id
                    ltable = s3db.dc_template_l10n
                    exists = db(ltable.template_id == template_id).select(ltable.id,
                                                                          ltable.language,
                                                                          limitby = (0, 1)
                                                                          ).first()
                    if exists:
                        if exists.language != l10n:
                            exists.update_record(language = l10n)
                    else:
                        ltable.insert(template_id = template_id,
                                      language = l10n,
                                      )
                    

                    if l10n:
                        # Update Questions
                        qtable = s3db.dc_question
                        questions = db(qtable.template_id == template_id).select(qtable.id)
                        question_ids = [q.id for q in questions]
                        qltable = s3db.dc_question_l10n
                        db(qltable.question_id.belongs(question_ids)).update(language = l10n)

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
                template_id = record.id

                ttable = s3db.dc_target
                target = db(ttable.template_id == template_id).select(ttable.id,
                                                                      ttable.status,
                                                                      limitby = (0, 1)
                                                                      ).first()
                try:
                    target_id = target.id
                    target_status = target.status
                except AttributeError:
                    target_id = None
                    target_status = None

                read_only = True
                if not target_status:
                    # No Target linked...something odd happening
                    button = ""
                elif target_status == 1:
                    # Draft
                    button = A(T("Activate"),
                               _href=URL(c="dc", f="target",
                                         args=[target_id, "activate.popup"],
                                         ),
                               _class="button round tiny s3_modal",
                               _title=T("Activate Survey"),
                               )
                    read_only = False
                elif target_status in (2, 3):
                    # Active / Deactivated
                    button = A(T("Edit"),
                               _href=URL(c="dc", f="target",
                                         args=[target_id, "edit_confirm.popup"],
                                         ),
                               _class="button round tiny s3_modal",
                               _title=T("Edit Survey"),
                               )
                else:
                    # Unknown Status...something odd happening
                    button = ""

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

                info_instructions = SPAN(ICON("info-circle"),
                                         _class="has-tip",
                                         _title=T("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."),
                                         )
                info_instructions["data-tooltip"] = 1

                ltable = s3db.dc_template_l10n
                l10n = db(ltable.template_id == template_id).select(ltable.language,
                                                                    limitby = (0, 1)
                                                                    ).first()
                if l10n:
                    l10n = l10n.language

                languages_dropdown = SELECT(OPTION(T("Choose language"),
                                                   _value="",
                                                   ),
                                            _id="survey-l10n",
                                            _class="fright",
                                            )
                l10n_options = current.deployment_settings.L10n.get("survey_languages", {})
                for lang in l10n_options:
                    if lang == l10n:
                        languages_dropdown.append(OPTION(l10n_options[lang],
                                                         _selected=True,
                                                         _value=lang,
                                                         ))
                    else:
                        languages_dropdown.append(OPTION(l10n_options[lang],
                                                         _value=lang,
                                                         ))

                toolbar = DIV(DIV(H2(T("Question types")),
                                  _class="row",
                                  ),
                              DIV(DIV(ICON("instructions"),
                                      _class="medium-2 columns",
                                      ),
                                  DIV(T("Data collector instructions"),
                                      _class="medium-9 columns",
                                      ),
                                  DIV(info_instructions,
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
                              DIV(DIV(ICON("section-break"),
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
                              DIV(H2(T("Translation options")),
                                  _class="row",
                                  ),
                              DIV(LABEL("%s:" % T("Translated to"),
                                        _class = "fleft",
                                        ),
                                  languages_dropdown,
                                  _class="row",
                                  ),
                              DIV(A(T("Upload translation"),
                                    _class="button tiny round fright",
                                    ),
                                  _class="row",
                                  ),
                              _id = "question-bar",
                              )
                toolbar["_data-magellan-expedition"] = "fixed"
                toolbar = DIV(toolbar,
                              _class = "magellan-scrollnav",
                              )

                hidden_input = INPUT(_type = "hidden",
                                     _id = "survey-layout",
                                     )
                hidden_input["_data-id"] = template_id

                questions = {}
                qtable = s3db.dc_question
                qrows = db(qtable.template_id == template_id).select(qtable.id,
                                                                     qtable.name,
                                                                     qtable.field_type,
                                                                     #qtable.require_not_empty,
                                                                     qtable.options,
                                                                     qtable.settings,
                                                                     qtable.file,
                                                                     )
                if l10n:
                    l10table = s3db.dc_question_l10n
                    question_ids = [question.id for question in qrows]
                    query = (l10table.question_id.belongs(question_ids)) & \
                            (l10table.language == l10n)
                    trows = db(query).select(l10table.question_id,
                                             l10table.name_l10n,
                                             l10table.options_l10n,
                                             )
                    questions_l10n = trows.as_dict(key="question_id")
                for question in qrows:
                    question_id = question.id
                    this_question = {"name": question.name or '',
                                     "type": question.field_type,
                                     # Always use isNotEmpty validator now, so only applies if field is visible
                                     #"mandatory": question.require_not_empty,
                                     "options": question.options or {},
                                     "settings": question.settings or {},
                                     "file": question.file,
                                     }
                    if l10n:
                        if question_id in questions_l10n:
                            this_question["name_l10n"] = questions_l10n[question_id].get("name_l10n")
                            this_question["options_l10n"] = questions_l10n[question_id].get("options_l10n")
                    questions[question_id] = this_question

                data = {"layout": record.layout or {},
                        "questions": questions,
                        }
                if l10n:
                    data["l10n"] = l10n
                hidden_input["_value"] = json.dumps(data, separators=SEPARATORS)

                layout = DIV(hidden_input)

                # Inject JS
                response = current.response
                s3 = response.s3
                appname = r.application
                scripts_append = s3.scripts.append
                if s3.debug:
                    scripts_append("/%s/static/scripts/load-image.js" % appname)
                    #scripts_append("/%s/static/scripts/load-image-exif.js" % appname)
                    #scripts_append("/%s/static/scripts/load-image-meta.js" % appname)
                    scripts_append("/%s/static/scripts/load-image-scale.js" % appname)
                    scripts_append("/%s/static/scripts/canvas-to-blob.js" % appname)
                    # The Iframe Transport is required for browsers without support for XHR file uploads
                    scripts_append("/%s/static/scripts/jquery.iframe-transport.js" % appname)
                    scripts_append("/%s/static/scripts/jquery.fileupload.js" % appname)
                    scripts_append("/%s/static/scripts/jquery.validate.js" % appname)
                    s3.scripts_modules.append("/%s/static/themes/UCCE/js/s3.ui.template.js" % appname)
                else:
                    scripts_append("/%s/static/scripts/load-image.all.min.js" % appname)
                    scripts_append("/%s/static/scripts/canvas-to-blob.min.js" % appname)
                    # The Iframe Transport is required for browsers without support for XHR file uploads
                    scripts_append("/%s/static/scripts/jquery.iframe-transport.js" % appname)
                    scripts_append("/%s/static/scripts/jquery.fileupload.min.js" % appname)
                    scripts_append("/%s/static/scripts/jquery.validate.min.js" % appname)
                    s3.scripts_modules.append("/%s/static/themes/UCCE/js/s3.ui.template.min.js" % appname)

                # Initialise the Template Editor Widget
                if read_only:
                    script = '''$('#survey-layout').surveyLayout({readOnly: true})'''
                    response.title = title = T("Preview")
                else:
                    script = '''$('#survey-layout').surveyLayout()'''
                    response.title = title = T("Editor")
                s3.jquery_ready.append(script)

                S3CustomController._view(THEME, "template_editor.html")
                output = {"header": header,
                          "layout": layout,
                          "title": title,
                          "toolbar": toolbar,
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
                if layout is not None:
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
                s3 = current.response.s3
                if s3.debug:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/themes/UCCE/js/confirm_popup.min.js" % r.application)

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
