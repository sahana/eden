# -*- coding: utf-8 -*-

"""
    Data Collection:
    - a front-end UI to manage Assessments which uses the Dynamic Tables back-end
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def template():
    """ RESTful CRUD controller """

    def prep(r):

        if r.record and r.component_name == "question":

            # If the template has responses then we should make the Questions read-only
            # @ToDo: Allow Editing unanswered questions?
            rtable = s3db.dc_response
            query = (rtable.template_id == r.id) & \
                    (rtable.deleted == False)
            if db(query).select(rtable.id,
                                limitby=(0, 1)
                                ):
                s3db.configure("dc_question",
                               deletable = False,
                               editable = False,
                               )
            else:
                # Sections for this template only
                f = s3db.dc_question.section_id
                f.requires = IS_EMPTY_OR(
                                IS_ONE_OF(db, "dc_section.id",
                                          f.represent,
                                          filterby="template_id",
                                          filter_opts=[r.id],
                                          ))

                # Add JS
                scripts_append = s3.scripts.append
                if s3.debug:
                    scripts_append("/%s/static/scripts/tag-it.js" % appname)
                    scripts_append("/%s/static/scripts/S3/s3.dc.js" % appname)
                else:
                    scripts_append("/%s/static/scripts/tag-it.min.js" % appname)
                    scripts_append("/%s/static/scripts/S3/s3.dc.min.js" % appname)
                # Add CSS
                s3.stylesheets.append("plugins/jquery.tagit.css")

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

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
                table.location_id.default = record.location_id
                f = table.template_id
                f.default = record.template_id
                f.writable = False

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def respnse(): # Cannot call this 'response' or it will clobber the global
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "answer":
                # CRUD Strings
                s3.crud_strings[r.component.tablename] = Storage(
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

                # Create Custom Form with Questions sorted by alpha-sorted Section and then alpha-sorted within them
                from s3 import S3SQLCustomForm
                crud_fields = []
                cappend = crud_fields.append
                subheadings = {}

                qtable = s3db.dc_question
                stable = db.dc_section
                ftable = db.s3_field
                query = (qtable.template_id == r.record.template_id) & \
                        (qtable.deleted == False) & \
                        (qtable.field_id == ftable.id)
                left = stable.on(stable.id == qtable.section_id)
                fields = db(query).select(stable.name,
                                          ftable.label,
                                          ftable.name,
                                          left = left,
                                          orderby = (stable.name, ftable.label),
                                          )
                for f in fields:
                    fname = f["s3_field.name"]
                    section_name = f["dc_section.name"]
                    if section_name in subheadings:
                        subheadings[section_name].append(fname)
                    else:
                        subheadings[section_name] = [fname]
                    cappend(fname)

                crud_form = S3SQLCustomForm(*crud_fields)
                s3db.configure(r.component.tablename,
                               crud_form = crud_form,
                               subheadings = subheadings,
                               )
                
        return True
    s3.prep = prep

    return s3_rest_controller("dc", "response",
                              rheader = s3db.dc_rheader,
                              )

# END =========================================================================
