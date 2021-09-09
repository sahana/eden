# -*- coding: utf-8 -*-

"""
    Data Collection:
    - a front-end UI to manage Assessments which uses the Dynamic Tables back-end
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[c].get("name_nice")
    response.title = module_name
    return {"module_name": module_name,
            }

# -----------------------------------------------------------------------------
def template():
    """ RESTful CRUD controller """

    from s3 import FS
    s3.filter = FS("master") == "dc_response"

    def prep(r):

        if r.record and r.component_name == "question":

            # If the template has responses then we should make the Questions read-only
            # @ToDo: Allow Editing unanswered questions?
            rtable = s3db.dc_response
            query = (rtable.template_id == r.id) & \
                    (rtable.deleted == False)
            if db(query).select(rtable.id,
                                limitby = (0, 1)
                                ):
                s3db.configure("dc_question",
                               deletable = False,
                               editable = False,
                               )

            # Add JS
            scripts_append = s3.scripts.append
            if s3.debug:
                scripts_append("/%s/static/scripts/tag-it.js" % appname)
                scripts_append("/%s/static/scripts/S3/s3.dc_question.js" % appname)
            else:
                scripts_append("/%s/static/scripts/tag-it.min.js" % appname)
                scripts_append("/%s/static/scripts/S3/s3.dc_question.min.js" % appname)
            # Add CSS
            s3.stylesheets.append("plugins/jquery.tagit.css")

            # Open in native controller to access Translations tabs
            s3db.configure("dc_question",
                           linkto = lambda record_id: \
                                        URL(f="question",
                                            args = [record_id, "read"],
                                            ),
                           linkto_update = lambda record_id: \
                                            URL(f="question",
                                                args = [record_id, "update"],
                                                ),
                           )

        return True
    s3.prep = prep

    from s3db.dc import dc_rheader
    return s3_rest_controller(rheader = dc_rheader)

# -----------------------------------------------------------------------------
def question():
    """
        RESTful CRUD controller
        - used for imports & to manage translations
    """

    from s3db.dc import dc_rheader
    return s3_rest_controller(rheader = dc_rheader,
                              )

# -----------------------------------------------------------------------------
def question_l10n():
    """
        RESTful CRUD controller
        - used for imports
    """

    #from s3db.dc import dc_rheader
    return s3_rest_controller(#rheader = s3db.dc_rheader,
                              )

# -----------------------------------------------------------------------------
def target():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "response":
                # Default component values from master record
                record = r.record
                table = s3db.dc_response
                table.language.default = record.language
                table.location_id.default = record.location_id
                f = table.template_id
                f.default = record.template_id
                f.writable = False
                f.comment = None

                # Open in native controller (cannot just set native as can't call this 'response')
                s3db.configure("dc_response",
                               linkto = lambda record_id: \
                                            URL(f="respnse",
                                                args = [record_id, "read"],
                                                ),
                               linkto_update = lambda record_id: \
                                                        URL(f="respnse",
                                                            args = [record_id, "update"],
                                                            ),
                               )
        elif r.id and not r.component and r.representation == "xls":
            # Custom XLS Exporter to include all Responses.
            r.set_handler("read", s3db.dc_TargetXLS(),
                          http = ("GET", "POST"),
                          representation = "xls"
                          )

        return True
    s3.prep = prep

    from s3db.dc import dc_rheader
    return s3_rest_controller(rheader = dc_rheader,
                              )

# -----------------------------------------------------------------------------
def respnse(): # Cannot call this 'response' or it will clobber the global
    """ RESTful CRUD controller """

    # All templates use the same component name for answers so need to add the right component manually
    try:
        response_id = int(request.args(0))
    except:
        # Multiple record method
        pass
    else:
        dtable = s3db.s3_table
        rtable = s3db.dc_response
        ttable = s3db.dc_template
        query = (rtable.id == response_id) & \
                (rtable.template_id == ttable.id) & \
                (ttable.table_id == dtable.id)
        template = db(query).select(dtable.name,
                                    limitby = (0, 1),
                                    ).first()
        try:
            dtablename = template.name
        except:
            # Old URL?
            pass
        else:
            components = {dtablename: {"name": "answer",
                                       "joinby": "response_id",
                                       "multiple": False,
                                       }
                          }
            s3db.add_components("dc_response", **components)

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "answer":
                # CRUD Strings
                tablename = r.component.tablename
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Create Responses"),
                    title_display = T("Response Details"),
                    title_list = T("Responses"),
                    title_update = T("Edit Response"),
                    label_list_button = T("List Responses"),
                    label_delete_button = T("Clear Response"),
                    msg_record_created = T("Response created"),
                    msg_record_modified = T("Response updated"),
                    msg_record_deleted = T("Response deleted"),
                    msg_list_empty = T("No Responses currently defined"),
                )

                # Custom Form with Questions & Subheadings sorted correctly
                from s3db.dc import dc_answer_form
                dc_answer_form(r, tablename)

        return True
    s3.prep = prep

    from s3db.dc import dc_rheader
    return s3_rest_controller("dc", "response",
                              rheader = dc_rheader,
                              )

# END =========================================================================
