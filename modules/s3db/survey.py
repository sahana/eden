# -*- coding: utf-8 -*-

""" Sahana Eden Survey Tool

    @copyright: 2011-2015 (c) Sahana Software Foundation
    @license: MIT

    ADAT - Assessment Data Analysis Tool

    For more details see the blueprint at:
    http://eden.sahanafoundation.org/wiki/BluePrint/SurveyTool/ADAT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3SurveyTemplateModel",
           "S3SurveyQuestionModel",
           "S3SurveyFormatterModel",
           "S3SurveySeriesModel",
           "S3SurveyCompleteModel",
           "S3SurveyTranslateModel",
           "survey_template_represent",
           "survey_answer_list_represent",
           "survey_template_rheader",
           "survey_series_rheader",
           "survey_getAllSectionsForTemplate",
           "survey_getAllQuestionsForTemplate",
           "survey_buildQuestionnaireFromTemplate",
           "survey_buildQuestionnaireFromSeries",
           "survey_getTemplateFromSeries",
           "survey_getAllWidgetsForTemplate",
           "survey_getWidgetFromQuestion",
           "survey_getAllSectionsForSeries",
           "survey_getAllSectionsForTemplate",
           "survey_getQuestionFromCode",
           "survey_getAllQuestionsForTemplate",
           "survey_getAllQuestionsForSeries",
           "survey_getAllQuestionsForComplete",
           "survey_save_answers_for_series",
           "survey_updateMetaData",
           "survey_getAllAnswersForQuestionInSeries",
           "survey_getQstnLayoutRules",
           "survey_getAllTranslationsForTemplate",
           "survey_getAllTranslationsForSeries",
           "survey_build_template_summary",
           "survey_serieslist_dataTable_post",
           "survey_answerlist_dataTable_pre",
           "survey_answerlist_dataTable_post",
           "survey_json2py",
           "survey_json2list",
           )

try:
    from cStringIO import StringIO    # Faster, where available
except ImportError:
    from StringIO import StringIO

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except ImportError:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3chart import S3Chart
from s3survey import survey_question_type, \
                     survey_analysis_type, \
                     _debug

# =============================================================================
def json2py(jsonstr):
    """
        Utility function to convert a string in json to a python structure
    """

    from xml.sax.saxutils import unescape

    if not isinstance(jsonstr, str):
        return jsonstr
    try:
        jsonstr = unescape(jsonstr, {"u'": '"'})
        jsonstr = unescape(jsonstr, {"'": '"'})
        python_structure = json.loads(jsonstr)
    except ValueError:
        _debug("ERROR: attempting to convert %s using modules/s3db/survey/json2py.py" % (jsonstr))
        return jsonstr
    else:
        return python_structure
survey_json2py = json2py

# =============================================================================
def json2list(jsonstr):
    """
        Used to modify a json string to a python list.
    """

    if jsonstr == "":
        value_list = []
    else:
        if jsonstr[0] == "[":
            value_list = json2py(jsonstr)
        else:
            value_list = jsonstr.split(",")
        if not isinstance(value_list, list):
            value_list = [value_list]
    return value_list

survey_json2list = json2list

# =============================================================================
class S3SurveyTemplateModel(S3Model):
    """
        Template model

        The template model is a container for the question model
    """

    names = ("survey_template",
             "survey_template_id",
             "survey_section",
             "survey_section_id",
             "survey_template_status",
             )

    def model(self):

        T = current.T
        db = current.db

        template_status = {1: T("Pending"),
                           2: T("Active"),
                           3: T("Closed"),
                           4: T("Master")
                           }

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # survey_template
        #
        # The template is the root table and acts as a container for
        # the questions that will be used in a survey.

        tablename = "survey_template"
        define_table(tablename,
                     Field("name", "string", length=120,
                           notnull=True, unique=True,
                           default = "",
                           label = T("Template Name"),
                           ),
                     Field("description", "text", length=500,
                           default = "",
                           label = T("Description"),
                           ),
                     Field("status", "integer",
                           default = 1,
                           label = T("Status"),
                           requires = IS_IN_SET(template_status,
                                                zero=None),
                           represent = lambda index: \
                                       template_status[index],
                           #readable=True,
                           writable = False,
                           ),
                     # Standard questions which may belong to all template
                     # competion_qstn: who completed the assessment
                     Field("competion_qstn", "string", length=200,
                           label = T("Completion Question"),
                           ),
                     # date_qstn: when it was completed (date)
                     Field("date_qstn", "string", length=200,
                           label = T("Date Question"),
                           ),
                     # time_qstn: when it was completed (time)
                     Field("time_qstn", "string", length=200,
                           label = T("Time Question"),
                           ),
                     # location_detail: json of the location question
                     #                  May consist of any of the following:
                     #                  L0, L1, L2, L3, L4, Lat, Lon
                     Field("location_detail", "string", length=200,
                           label = T("Location Detail"),
                           ),
                     # The priority question is the default question used
                     # to determine the priority of each point on the map.
                     # The data is stored as the question code.
                     Field("priority_qstn", "string", length=16,
                           label = T("Default map question"),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Assessment Template"),
            title_display = T("Assessment Template Details"),
            title_list = T("Assessment Templates"),
            title_analysis_summary = T("Template Summary"),
            title_update = T("Edit Assessment Template"),
            title_question_details = T("Details of each question in the Template"),
            subtitle_analysis_summary = T("Summary by Question Type - (The fewer text questions the better the analysis can be)"),
            label_list_button = T("List Assessment Templates"),
            label_delete_button = T("Delete this Assessment Template"),
            msg_record_created = T("Assessment Template added"),
            msg_record_modified = T("Assessment Template updated"),
            msg_record_deleted = T("Assessment Template deleted"),
            msg_list_empty = T("No Assessment Templates"))

        template_id = S3ReusableField("template_id", "reference %s" % tablename,
                                      label = T("Template"),
                                      ondelete = "CASCADE",
                                      requires = IS_ONE_OF(db,
                                                           "survey_template.id",
                                                           self.survey_template_represent,
                                                           ),
                                      represent = self.survey_template_represent,
                                      sortby = "name",
                                      )
        # Components
        add_components(tablename,
                       survey_series = "template_id",
                       survey_translate = "template_id",
                       )

        set_method = self.set_method
        set_method("survey", "template",
                   component_name = "translate",
                   method = "translate_download",
                   action = survey_TranslateDownload,
                   )

        filter_widgets = [
            S3TextFilter("name",
                         label = T("Search")),
            S3OptionsFilter("status",
                         label = T("Status")),
            ]

        configure(tablename,
                  deduplicate = self.survey_template_duplicate,
                  filter_widgets = filter_widgets,
                  onaccept = self.template_onaccept,
                  onvalidation = self.template_onvalidate,
                  )

        # ---------------------------------------------------------------------
        # survey_sections
        #
        # The questions can be grouped into sections this provides
        # the description of the section and
        # the position of the section within the template

        tablename = "survey_section"
        define_table(tablename,
                     Field("name", "string", length=120,
                           notnull = True,
                           default = "",
                           ),
                     Field("description", "text", length=500,
                           default = "",
                           ),
                     Field("posn", "integer"),
                     Field("cloned_section_id", "integer",
                           readable = False,
                           writable = False,
                           ),
                     template_id(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Template Section"),
            title_display = T("Template Section Details"),
            title_list = T("Template Sections"),
            title_update = T("Edit Template Section"),
            label_list_button = T("List Template Sections"),
            label_delete_button = T("Delete this Template Section"),
            msg_record_created = T("Template Section added"),
            msg_record_modified = T("Template Section updated"),
            msg_record_deleted = T("Template Section deleted"),
            msg_list_empty = T("No Template Sections"))

        configure(tablename,
                  deduplicate = self.survey_section_duplicate,
                  orderby = tablename + ".posn",
                  )

        section_id = S3ReusableField("section_id", "reference %s" % tablename,
                                     readable = False,
                                     writable = False,
                                     )

        # Pass names back to global scope (s3.*)
        return dict(survey_template_id = template_id,
                    survey_template_status = template_status,
                    survey_section_id = section_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def template_onvalidate(form):
        """
            It is not valid to re-import a template that already has a
            status of Active or higher
        """

        template_id = form.vars.id
        table = current.s3db.survey_template
        row = current.db(table.id == template_id).select(table.status,
                                                         limitby=(0, 1)
                                                         ).first()
        if row is not None and row.status > 1:
            return False
        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def add_question(template_id, name, code, notes, qtype, posn, metadata={}):
        """
            Adds a question to the template corresponding to template_id
        """

        db = current.db
        s3db = current.s3db

        # Add the question to the database if it's not already there
        qtable = s3db.survey_question
        query = (qtable.name == name) & \
                (qtable.code == code)
        record = db(query).select(qtable.id, limitby=(0, 1)).first()
        if record:
            qstn_id = record.id
        else:
            qstn_id = qtable.insert(name = name,
                                    code = code,
                                    notes = notes,
                                    type = qtype,
                                    )
            qstn_metadata_table = s3db.survey_question_metadata
            for (descriptor, value) in metadata.items():
                qstn_metadata_table.insert(question_id = qstn_id,
                                           descriptor = descriptor,
                                           value = value,
                                           )
        # Add these questions to the section: "Background Information"
        sectable = s3db.survey_section
        section_name = "Background Information"
        query = (sectable.name == section_name) & \
                (sectable.template_id == template_id)
        record = db(query).select(sectable.id, limitby=(0, 1)).first()
        if record:
            section_id = record.id
        else:
            section_id = sectable.insert(name = section_name,
                                         template_id = template_id,
                                         posn = 0 # special section with no position
                                         )
        # Add the question to the list of questions in the template
        qltable = s3db.survey_question_list
        query = (qltable.question_id == qstn_id) & \
                (qltable.template_id == template_id)
        record = db(query).select(qtable.id, limitby=(0, 1)).first()
        if not record:
            qltable.insert(question_id = qstn_id,
                           template_id = template_id,
                           section_id = section_id,
                           posn = posn,
                           )

    # -------------------------------------------------------------------------
    @staticmethod
    def template_onaccept(form):
        """
            All of the standard questions will now be generated
            competion_qstn: who completed the assessment
            date_qstn: when it was completed (date)
            time_qstn: when it was completed (time)
            location_detail: json of the location question
                             May consist of any of the following:
                             L0, L1, L2, L3, L4, Lat, Lon
                             for json entry a question will be generated
            The code for each question will start with "STD-" followed by
            the type of question.
        """

        form_vars = form.vars
        if form_vars.id:
            template_id = form_vars.id
        else:
            return

        add_question = S3SurveyTemplateModel.add_question
        if form_vars.competion_qstn != None:
            name = form_vars.competion_qstn
            code = "STD-WHO"
            notes = "Who completed the assessment"
            qtype = "String"
            posn = -10 # negative used to force these question to appear first
            add_question(template_id, name, code, notes, qtype, posn)
        if form_vars.date_qstn != None:
            name = form_vars.date_qstn
            code = "STD-DATE"
            notes = "Date the assessment was completed"
            qtype = "Date"
            posn += 1
            add_question(template_id, name, code, notes, qtype, posn)
        if form_vars.time_qstn != None:
            name = form_vars.time_qstn
            code = "STD-TIME"
            notes = "Time the assessment was completed"
            qtype = "Time"
            posn += 1
            add_question(template_id, name, code, notes, qtype, posn)
        if form_vars.location_detail != None:
            location_list = json2py(form_vars.location_detail)
            if len(location_list) > 0:
                name = "The location P-code"
                code = "STD-P-Code"
                qtype = "String"
                posn += 1
                add_question(template_id, name, code, None, qtype, posn)
            for loc in location_list:
                if loc == "Lat":
                    name = "Latitude"
                elif loc == "Lon":
                    name = "Longitude"
                else:
                    name = loc
                code = "STD-%s" % loc
                if loc == "Lat" or loc == "Lon":
                    qtype = "Numeric"
                    metadata = {"Format": "nnn.nnnnnn"}
                else:
                    qtype = "Location"
                    metadata = {}
                posn += 1
                add_question(template_id, name, code, "", qtype, posn, metadata)

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_template_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for a record with a similar name, ignoring case
        """

        name = item.data.get("name")
        table = item.table
        query =  table.name.lower().like('%%%s%%' % name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_section_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for a record with the same name
                - the same template
                - and the same position within the template
                - however if their is a record with position of zero then
                  that record should be updated
        """

        data = item.data
        name = data.get("name")
        template = data.get("template_id")
        table = item.table
        query = (table.name == name) & \
                (table.template_id == template)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
def survey_template_represent(template_id, row=None):
    """
        Display the template name rather than the id
    """

    if row:
        return row.name
    elif not template_id:
        return current.messages["NONE"]

    table = current.s3db.survey_template
    query = (table.id == template_id)
    record = current.db(query).select(table.name,
                                      limitby=(0, 1)).first()
    try:
        return record.name
    except AttributeError:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def survey_template_rheader(r, tabs=[]):
    """
        The template rheader
    """

    if r.representation == "html":

        tablename, record = s3_rheader_resource(r)
        if tablename == "survey_template" and record:

            T = current.T
            s3db = current.s3db

            # Tabs
            tabs = [(T("Basic Details"), "read"),
                    (T("Question Details"), "template_read/"),
                    (T("Question Summary"), "template_summary/"),
                    #(T("Sections"), "section"),
                    ]
            if current.auth.s3_has_permission("create", "survey_translate"):
                tabs.append((T("Translate"), "translate"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            stable = s3db.survey_section
            qltable = s3db.survey_question_list
            viewing = current.request.get_vars.get("viewing", None)
            if viewing:
                dummy, template_id = viewing.split(".")
            else:
                template_id = r.id

            query = (qltable.template_id == template_id) & \
                    (qltable.section_id == stable.id)
            rows = current.db(query).select(stable.id,
                                            stable.name,
                                            orderby = qltable.posn)
            tsection = TABLE(_class="survey-section-list")
            label_section = SPAN(T("Sections that are part of this template"),
                                 _style="font-weight:bold;")
            if (rows.__len__() == 0):
                rsection = SPAN(T("As of yet, no sections have been added to this template."))
            else:
                rsection = TR()
                count = 0
                last_section = ""
                for section in rows:
                    if section.name == last_section:
                        continue
                    rsection.append(TD(section.name))
                    # Comment out the following until templates can be built online
                    #rsection.append(TD(A(section.name,
                    #                     _href=URL(c="survey",
                    #                               f="section",
                    #                               args="%s" % section.id))))
                    last_section = section.name
                    count += 1
                    if count % 4 == 0:
                        tsection.append(rsection)
                        rsection = TR()
            tsection.append(rsection)

            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   record.name,
                                   TH("%s: " % T("Status")),
                                   s3db.survey_template_status[record.status],
                                   ),
                                ),
                          label_section,
                          tsection,
                          rheader_tabs,
                          )
            return rheader

# =============================================================================
def survey_getTemplateFromSeries(series_id):
    """
        Return the template data from the series_id passed in
        @ToDo: Remove wrapper
    """

    s3db = current.s3db
    stable = s3db.survey_series
    ttable = s3db.survey_template
    query = (stable.id == series_id) & \
            (ttable.id == stable.template_id)
    row = current.db(query).select(ttable.ALL,
                                   limitby=(0, 1)).first()
    return row

# =============================================================================
def survey_getAllWidgetsForTemplate(template_id):
    """
        Function to return the widgets for each question for the given
        template. The widgets are returned in a dict with the key being
        the question code.
    """

    s3db = current.s3db
    qltable = s3db.survey_question_list
    qtable = s3db.survey_question
    query = (qltable.template_id == template_id) & \
            (qltable.question_id == qtable.id)
    rows = current.db(query).select(qtable.id,
                                    qtable.code,
                                    qtable.type,
                                    qltable.posn,
                                    )
    widgets = {}
    for row in rows:
        sqrow = row.survey_question
        qstn_type = sqrow.type
        qstn_id = sqrow.id
        qstn_code = sqrow.code
        qstn_posn = row.survey_question_list.posn
        widget_obj = survey_question_type[qstn_type](qstn_id)
        widgets[qstn_code] = widget_obj
        widget_obj.question["posn"] = qstn_posn
        question = {}
    return widgets

# =============================================================================
def survey_getAllSectionsForSeries(series_id):
    """
        Function to return the list of sections for the given series
        The sections are returned in the order of their position in the
        template.

        The data on each section is held in a dict and is as follows:
        section_id, name, template_id, and posn

        @ToDo: Remove wrapper
    """

    table = current.s3db.survey_series
    row = current.db(table.id == series_id).select(table.template_id,
                                                   limitby = (0, 1),
                                                   ).first()
    return survey_getAllSectionsForTemplate(row.template_id)

# =============================================================================
def survey_buildQuestionnaireFromTemplate(template_id):
    """
        Build a form displaying all the questions for a given template_id
        @ToDo: Remove wrapper
    """

    questions = survey_getAllQuestionsForTemplate(template_id)
    return buildQuestionsForm(questions, readOnly=True)

# =============================================================================
def survey_getAllSectionsForTemplate(template_id):
    """
        function to return the list of sections for the given template
        The sections are returned in the order of their position in the
        template.

        The data on each section is held in a dict and is as follows:
        section_id, name, template_id, and posn
    """

    sectable = current.s3db.survey_section
    query = (sectable.template_id == template_id)

    rows = current.db(query).select(sectable.id,
                                    sectable.name,
                                    sectable.template_id,
                                    sectable.posn,
                                    orderby = sectable.posn)
    sections = []
    for sec in rows:
        sections.append({"section_id": sec.id,
                         "name" : sec.name,
                         "template_id": sec.template_id,
                         "posn" : sec.posn
                         }
                        )
    return sections

# =============================================================================
def survey_getWidgetFromQuestion(question_id):
    """
        Function that gets the right widget for the question
    """

    qtable = current.s3db.survey_question
    question = current.db(qtable.id == question_id).select(qtable.type,
                                                           limitby=(0, 1)
                                                           ).first()
    question_type = question.type
    widget_obj = survey_question_type[question_type](question_id)
    return widget_obj

# =============================================================================
def buildQuestionsForm(questions, complete_id=None, readOnly=False):
    """
        Create the form, hard-coded table layout :(
    """

    form = FORM()
    table = None
    section_title = ""
    for question in questions:
        if section_title != question["section"]:
            if section_title != "":
                form.append(P())
                form.append(HR(_width="90%"))
                form.append(P())
            div = DIV()
            table = TABLE()
            div.append(table)
            form.append(div)
            table.append(TR(TH(question["section"],
                               _colspan="2"),
                            _class="survey_section"))
            section_title = question["section"]
        widget_obj = survey_getWidgetFromQuestion(question["qstn_id"])
        if readOnly:
            table.append(TR(TD(question["code"]),
                            TD(widget_obj.type_represent()),
                            TD(question["name"])
                            )
                         )
        else:
            if complete_id != None:
                widget_obj.loadAnswer(complete_id, question["qstn_id"])
            widget = widget_obj.display(question_id = question["qstn_id"])
            if widget != None:
                if isinstance(widget, TABLE):
                    table.append(TR(TD(widget, _colspan=2)))
                else:
                    table.append(widget)
    if not readOnly:
        button = INPUT(_type="submit", _name="Save", _value=current.T("Save"),
                       _class="small primary button")
        form.append(button)
    return form

# =============================================================================
def survey_build_template_summary(template_id):
    """
    """

    from s3.s3data import S3DataTable
    T = current.T

    table = TABLE(_id="template_summary",
                  _class="dataTable display")
    table_header = TR(TH(T("Position")), TH(T("Section")))
    question_type_list = {}
    posn = 1
    for (key, qtype) in survey_question_type.items():
        if key == "Grid" or key == "GridChild":
            continue
        table_header.append(TH(qtype().type_represent()))
        question_type_list[key] = posn
        posn += 1
    table_header.append(TH(T("Total")))
    header = THEAD(table_header)

    num_of_question_types = len(survey_question_type) - 1 # exclude the grid questions
    questions = survey_getAllQuestionsForTemplate(template_id)
    section_title = ""
    line = []
    body = TBODY()
    section = 0
    total = ["", T("Total")] + [0] * num_of_question_types
    for question in questions:
        if section_title != question["section"]:
            if line != []:
                temp_row = TR()
                for cell in line:
                    temp_row.append(cell)
                body.append(temp_row)
            section += 1
            section_title = question["section"]
            line = [section, section_title] + [0] * num_of_question_types
        if question["type"] == "Grid":
            continue
        if question["type"] == "GridChild":
            # get the real grid question type
            widget_obj = survey_getWidgetFromQuestion(question["qstn_id"])
            question["type"] = widget_obj.typeDescription
        line[question_type_list[question["type"]]+1] += 1
        line[num_of_question_types+1] += 1
        total[question_type_list[question["type"]]+1] += 1
        total[num_of_question_types+1] += 1
    # Add the trailing row
    empty_row = TR()
    for cell in line:
        empty_row.append(cell)
    body.append(empty_row)
    # Add the footer to the table
    foot = TFOOT()
    footer_row = TR()
    for cell in total:
        footer_row.append(TD(B(cell))) # don't use TH() otherwise dataTables will fail
    foot.append(footer_row)

    table.append(header)
    table.append(body)
    table.append(foot)

    # Turn off server side pagination
    s3 = current.response.s3
    s3.no_sspag = True
    s3.no_formats = True

    s3.dataTableID = None
    attr = S3DataTable.getConfigData()
    form = S3DataTable.htmlConfig(table,
                                  "template_summary",
                                  [[0, 'asc']], # order by
                                  "", # the filter string
                                  None, # the rfields
                                  dt_action_col = -1,
                                  **attr
                                  )
    return form

# =============================================================================
class S3SurveyQuestionModel(S3Model):
    """
        Question Model
    """

    names = ("survey_question",
             "survey_question_id",
             "survey_question_metadata",
             "survey_question_list",
             "survey_qstn_name_represent",
             )

    def model(self):

        T = current.T
        s3 = current.response.s3

        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # survey_question
        # Defines a question that will appear within a section, and thus belong
        # to the template.
        #
        #    This holds the actual question and
        #    A string code (unique within the template) is used to identify the question.
        #
        #    It will have a type from the questionType dictionary.
        #    This type will determine the options that can be associated with it.
        #    A question can belong to many different sections.
        #    The notes are to help the enumerator and will typically appear as a
        #    footnote in the printed form.
        #
        #   @todo: the name, code and type combination should be unique
        #          so that multiple imports don't add the same question a second time
        #          may want a restriction such that:
        #          if name and code exist then the type must match.

        tablename = "survey_question"
        define_table(tablename,
                     Field("name", length=200,
                           notnull = True,
                           represent = self.qstn_name_represent,
                           ),
                     Field("code", length=16,
                           notnull = True,
                           ),
                     Field("notes", length=400
                           ),
                     Field("type", length=40,
                           notnull = True,
                           ),
                     Field("metadata", "text",
                           ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create an Assessment Question"),
            title_display = T("Assessment Question Details"),
            title_list = T("Assessment Questions"),
            title_update = T("Edit Assessment Question"),
            label_list_button = T("List Assessment Questions"),
            label_delete_button = T("Delete this Assessment Question"),
            msg_record_created = T("Assessment Question added"),
            msg_record_modified = T("Assessment Question updated"),
            msg_record_deleted = T("Assessment Question deleted"),
            msg_list_empty = T("No Assessment Questions"))

        configure(tablename,
                  deduplicate = self.survey_question_duplicate,
                  onaccept = self.question_onaccept,
                  onvalidation = self.question_onvalidate,
                  )

        question_id = S3ReusableField("question_id", "reference %s" % tablename,
                                      readable = False,
                                      writable = False,
                                      )

        # ---------------------------------------------------------------------
        # survey_question_metadata
        # referenced by
        #    the survey_question table and is used to manage
        #    the metadata that will be associated with a question type.
        #    For example: if the question type is option, then valid metadata
        #    might be:
        #    count: the number of options that will be presented: 3
        #    1 : the first option                               : Female
        #    2 : the second option                              : Male
        #    3 : the third option                               : Not Specified
        #    So in the above case a question record will be associated with four
        #    question_metadata records.

        tablename = "survey_question_metadata"
        define_table(tablename,
                     question_id(),
                     Field("descriptor", length=20,
                           notnull = True,
                           ),
                     Field("value", "text",
                           notnull = True,
                           ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Question Meta-Data"),
            title_display = T("Question Meta-Data Details"),
            title_list = T("Question Meta-Data"),
            title_update = T("Edit Question Meta-Data"),
            label_list_button = T("List Question Meta-Data"),
            label_delete_button = T("Delete this Question Meta-Data"),
            msg_record_created = T("Question Meta-Data added"),
            msg_record_modified = T("Question Meta-Data updated"),
            msg_record_deleted = T("Question Meta-Data deleted"),
            msg_list_empty = T("No Question Meta-Data"),
            title_upload = T("Upload a Question List import file")
            )

        configure(tablename,
                  deduplicate = self.survey_question_metadata_duplicate,
                  )

        # -------------------------------------------------------------------------
        # The survey_question_list table is a resolver between
        #    the survey_question and the survey_section tables.
        #
        #    Along with ids mapping back to these tables
        #    it will have a code that can be used to reference the question
        #    it will have the position that the question will appear in the template

        tablename = "survey_question_list"
        define_table(tablename,
                     Field("posn", "integer",
                           notnull = True,
                           ),
                     self.survey_template_id(),
                     question_id(),
                     self.survey_section_id(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_upload = T("Upload an Assessment Template import file")
            )

        configure(tablename,
                  deduplicate = self.survey_question_list_duplicate,
                  onaccept = self.question_list_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict(survey_qstn_name_represent = self.qstn_name_represent,
                    survey_question_id = question_id
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def qstn_name_represent(value):
        """
            Return the question name, for locations in the gis hierarchy
            the localised name will be returned
            @todo: add the full name if it is a grid question BUT not displayed
                  as part of a grid,
                  e.g. "Currently known Displaced", rather than just "Displaced"
                  see controller... template_read() for an example not in the grid
        """

        if value == "L0" or value == "L1" or \
           value == "L2" or value == "L3" or value == "L4":
            return current.gis.get_location_hierarchy(value)
        else:
            return value

    # -------------------------------------------------------------------------
    @staticmethod
    def question_onvalidate(form):
        """
            Any text with the metadata that is imported will be held in
            single quotes, rather than double quotes and so these need
            to be escaped to double quotes to make it valid JSON
        """

        from xml.sax.saxutils import unescape

        metadata = form.vars.metadata
        if metadata != None:
            metadata = unescape(metadata, {"'":'"'})
        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def question_onaccept(form):
        """
            All of the question metadata will be stored in the metadata
            field in a JSON format.
            They will then be inserted into the survey_question_metadata
            table pair will be a record on that table.

        """

        form_vars = form.vars
        if form_vars.metadata is None:
            return
        if form_vars.id:
            record = current.s3db.survey_question[form_vars.id]
        else:
            return
        if form_vars.metadata and \
           form_vars.metadata != "":
            survey_updateMetaData(record,
                                  form_vars.type,
                                  form_vars.metadata
                                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_question_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for the question code
        """

        code = item.data.get("code")
        table = item.table
        query = (table.code == code)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_question_metadata_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for the question_id and descriptor
        """

        data = item.data
        question = data.get("question_id")
        descriptor = data.get("descriptor")
        table = item.table
        query = (table.descriptor == descriptor) & \
                (table.question_id == question)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def question_list_onaccept(form):
        """
            If a grid question is added to the the list then all of the
            grid children will need to be added as well
        """

        qstntable = current.s3db.survey_question
        try:
            form_vars = form.vars
            question_id = form_vars.question_id
            template_id = form_vars.template_id
            section_id = form_vars.section_id
            posn = form_vars.posn
        except AttributeError:
            return
        record = qstntable[question_id]
        qtype = record.type

        if qtype == "Grid":
            widget_obj = survey_question_type["Grid"]()
            widget_obj.insertChildrenToList(question_id,
                                            template_id,
                                            section_id,
                                            posn,
                                            )
        if qtype == "Location":
            widget_obj = survey_question_type["Location"]()
            widget_obj.insertChildrenToList(question_id,
                                            template_id,
                                            section_id,
                                            posn,
                                            )

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_question_list_duplicate(item):
        """
            Rules for finding a duplicate:
                - The template_id, question_id and section_id are the same
        """

        data = item.data
        tid = data.get("template_id")
        qid = data.get("question_id")
        sid = data.get("section_id")
        table = item.table
        query = (table.template_id == tid) & \
                (table.question_id == qid) & \
                (table.section_id == sid)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
def survey_getQuestionFromCode(code, series_id=None):
    """
        Function to return the question for the given series
        with the code that matches the one passed in
    """

    s3db = current.s3db
    sertable = s3db.survey_series
    q_ltable = s3db.survey_question_list
    qsntable = s3db.survey_question
    if series_id != None:
        query = (sertable.id == series_id) & \
                (q_ltable.template_id == sertable.template_id) & \
                (q_ltable.question_id == qsntable.id) & \
                (qsntable.code == code)
    else:
        query = (q_ltable.template_id == sertable.template_id) & \
                (q_ltable.question_id == qsntable.id) & \
                (qsntable.code == code)
    record = current.db(query).select(qsntable.id,
                                      qsntable.code,
                                      qsntable.name,
                                      qsntable.type,
                                      q_ltable.posn,
                                      limitby=(0, 1)).first()
    question = {}
    if record != None:
        question_row = record.survey_question
        question["qstn_id"] = question_row.id
        question["code"] = question_row.code
        question["name"] = question_row.name
        question["type"] = question_row.type
        question["posn"] = record.survey_question_list.posn
    return question

# =============================================================================
def survey_getAllQuestionsForTemplate(template_id):
    """
        Function to return the list of questions for the given template
        The questions are returned in the order of their position in the
        template.

        The data on a question that it returns is as follows:
        qstn_id, code, name, type, posn, section
    """

    s3db = current.s3db
    sectable = s3db.survey_section
    q_ltable = s3db.survey_question_list
    qsntable = s3db.survey_question
    query = (q_ltable.template_id == template_id) & \
            (q_ltable.section_id == sectable.id) & \
            (q_ltable.question_id == qsntable.id)
    rows = current.db(query).select(qsntable.id,
                                    qsntable.code,
                                    qsntable.name,
                                    qsntable.type,
                                    sectable.name,
                                    q_ltable.posn,
                                    orderby=(q_ltable.posn))
    questions = []
    for row in rows:
        question = {}
        question_row = row.survey_question
        question["qstn_id"] = question_row.id
        question["code"] = question_row.code
        question["name"] = s3db.survey_qstn_name_represent(question_row.name)
        question["type"] = question_row.type
        question["posn"] = row.survey_question_list.posn
        question["section"] = row.survey_section.name
        questions.append(question)
    return questions

# =============================================================================
def survey_getAllQuestionsForSeries(series_id):
    """
        Function to return the list of questions for the given series
        The questions are returned in to order of their position in the
        template.

        The data on a question that is returns is as follows:
        qstn_id, code, name, type, posn, section
    """

    table = current.s3db.survey_series
    row = current.db(table.id == series_id).select(table.template_id,
                                                   limitby=(0, 1)).first()
    template_id = row.template_id
    questions = survey_getAllQuestionsForTemplate(template_id)
    return questions

# =============================================================================
def survey_getAllQuestionsForComplete(complete_id):
    """
        Function to return a tuple of the list of questions and series_id
        for the given completed_id

        The questions are returned in to order of their position in the
        template.

        The data on a question that is returns is as follows:
        qstn_id, code, name, type, posn, section
    """

    table = current.s3db.survey_complete
    row = current.db(table.id == complete_id).select(table.series_id,
                                                     limitby=(0, 1)).first()
    series_id = row.series_id
    questions = survey_getAllQuestionsForSeries(series_id)
    return (questions, series_id)

# =============================================================================
def survey_get_series_questions_of_type(question_list, qtype):
    """
    """

    if isinstance(qtype, (list, tuple)):
        types = qtype
    else:
        types = (qtype)
    questions = []
    for question in question_list:
        if question["type"] in types:
            questions.append(question)
        elif question["type"] == "Link" or \
             question["type"] == "GridChild":
            widget_obj = survey_getWidgetFromQuestion(question["qstn_id"])
            if widget_obj.getParentType() in types:
                question["name"] = widget_obj.fullName()
                questions.append(question)
    return questions

# =============================================================================
def survey_getQuestionFromName(name, series_id):
    """
        Function to return the question for the given series
        with the name that matches the one passed in
    """

    s3db = current.s3db
    sertable = s3db.survey_series
    q_ltable = s3db.survey_question_list
    qsntable = s3db.survey_question
    query = (sertable.id == series_id) & \
            (q_ltable.template_id == sertable.template_id) & \
            (q_ltable.question_id == qsntable.id) & \
            (qsntable.name == name)
    record = current.db(query).select(qsntable.id,
                                      qsntable.code,
                                      qsntable.name,
                                      qsntable.type,
                                      q_ltable.posn,
                                      limitby=(0, 1)).first()
    if record is None:
        # Unable to get the record from the question name
        # It could be because the question is a location
        # So get the location names and then check
        loc_list = current.gis.get_all_current_levels()
        for row in loc_list.items():
            if row[1] == name:
                return survey_getQuestionFromName(row[0], series_id)

    question = {}
    question_row = record.survey_question
    question["qstn_id"] = question_row.id
    question["code"] = question_row.code
    question["name"] = question_row.name
    question["type"] = question_row.type
    question["posn"] = record.survey_question_list.posn
    return question

# =============================================================================
def survey_updateMetaData(record, qtype, metadata):
    """
    """

    metatable = current.s3db.survey_question_metadata
    question_id = record.id
    # the metadata can either be passed in as a JSON string
    # or as a parsed map. If it is a string load the map.
    if isinstance(metadata, str):
        metadata_list = json2py(metadata)
    else:
        metadata_list = metadata
    for (desc, value) in metadata_list.items():
        desc = desc.strip()
        if not isinstance(value, str):
            # web2py stomps all over a list so convert back to a string
            # before inserting it on the database
            value = json.dumps(value)
        value = value.strip()
        metatable.insert(question_id = question_id,
                         descriptor = desc,
                         value = value,
                         )
    if qtype == "Grid":
        widget_obj = survey_question_type["Grid"]()
        widget_obj.insertChildren(record, metadata_list)

# =============================================================================
class S3SurveyFormatterModel(S3Model):
    """
        The survey_formatter table defines the order in which the questions
        will be laid out when a formatted presentation is used.

        The idea is to be able to present the questions in a format that
        best uses the available space and is familiar to those using the
        tool.

        Examples of formatted presentation are the spreadsheet and the web
        form. This may be extended to PDF documents.

        The rules are held as a JSON record and describe where each question
        within the section should appear in terms of rows and columns. Each
        question is referenced by the question code.

        For example assume a section with the following eight questions:
        QSTN_1, QSTN_2, QSTN_3, QSTN_4, QSTN_5, QSTN_6, QSTN_7, QSTN_8
        Then to display them in three rows:
        [[QSTN_1, QSTN_2, QSTN_3], [QSTN_4, QSTN_5, QSTN_6], [QSTN_7, QSTN_8]]
        would present it as follows:
        QSTN_1, QSTN_2, QSTN_3,
        QSTN_4, QSTN_5, QSTN_6,
        QSTN_7, QSTN_8
        The order of the questions does not need to be preserved, thus:
        [[QSTN_1, QSTN_2], [QSTN_4, QSTN_5, QSTN_3], [QSTN_7, QSTN_8, QSTN_6]]
        would be valid, and give:
        QSTN_1, QSTN_2,
        QSTN_4, QSTN_5, QSTN_3,
        QSTN_7, QSTN_8, QSTN_6,

        ***NOTE***
        When importing this record with a CSV file the question code will be
        single quoted, rather than double quoted which JSON requires.
        This is because the whole rule needs to be double quoted. Code that
        extracts the records from the table will then need to change all
        single quotes to double quotes. This can be done as follows:

        rowList = json2py(rules)
    """

    names = ("survey_formatter",)

    def model(self):

        T = current.T

        survey_formatter_methods = {1: T("Default"),
                                    2: T("Web Form"),
                                    3: T("Spreadsheet"),
                                    4: T("PDF"),
                                    }

        # ---------------------------------------------------------------------
        tablename = "survey_formatter"
        self.define_table(tablename,
                          self.survey_template_id(),
                          self.survey_section_id(),
                          Field("method", "integer",
                                default = 1,
                                represent = lambda index: \
                                    survey_formatter_methods[index],
                                requires = IS_IN_SET(survey_formatter_methods,
                                                     zero=None),
                                writable = False,
                                ),
                          Field("rules", "text", default=""),
                          *s3_meta_fields()
                          )

        self.configure(tablename,
                       deduplicate = self.survey_formatter_duplicate,
                       onaccept = self.formatter_onaccept,
                       )

        # ---------------------------------------------------------------------
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def formatter_onaccept(form):
        """
            If this is the formatter rules for the Background Information
            section then add the standard questions to the layout
        """

        s3db = current.s3db
        section_id = form.vars.section_id
        stable = s3db.survey_section
        section_name = stable[section_id].name
        if section_name == "Background Information":
            col1 = []
            # Add the default layout
            ttable = s3db.survey_template
            template = ttable[form.vars.template_id]
            if template.competion_qstn != "":
                col1.append("STD-WHO")
            if template.date_qstn != "":
                col1.append("STD-DATE")
            if template.time_qstn != "":
                col1.append("STD-TIME")
            if "location_detail" in template:
                col2 = ["STD-P-Code"]
                location_list = json2py(template.location_detail)
                for loc in location_list:
                    col2.append("STD-%s" % loc)
                col = [col1, col2]
                rule = [{"columns":col}]
                rule_list = json2py(form.vars.rules)
                rule_list[:0] = rule
                rules = json.dumps(rule_list)
                db = current.db
                ftable = db.survey_formatter
                db(ftable.id == form.vars.id).update(rules = rules)

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_formatter_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for a record with the same template_id and section_id
        """

        data = item.data
        tid = data.get("template_id")
        sid = data.get("section_id")
        table = item.table
        query = (table.template_id == tid) & \
                (table.section_id == sid)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
def survey_getQstnLayoutRules(template_id,
                              section_id,
                              method = 1
                              ):
    """
        This will return the rules for laying out the questions for
        the given section within the template.
        This is used when generating a formatted layout.

        First it will look for a survey_formatter record that matches
        the method given. Failing that it will look for a default
        survey_formatter record. If no appropriate survey_formatter
        record exists for the section then it will use the posn
        field found in the survey_question_list record.

        The function will return a list of rows. Each row is a list
        of question codes.
    """

    db = current.db
    s3db = current.s3db

    # search for layout rules on the survey_formatter table
    fmttable = s3db.survey_formatter
    query = (fmttable.template_id == template_id) & \
            (fmttable.section_id == section_id)
    rows = db(query).select(fmttable.method,
                            fmttable.rules)
    rules = None
    drules = None # default rules
    for row in rows:
        if row.method == method:
            rules = row.rules
            break
        elif row.method == 1:
            drules = row.rules
    if rules == None and drules != None:
        rules = drules
    row_list = []
    if rules is None or rules == "":
        # get the rules from survey_question_list
        qltable = s3db.survey_question_list
        qtable = s3db.survey_question
        query = (qltable.template_id == template_id) & \
                (qltable.section_id == section_id) & \
                (qltable.question_id == qtable.id)
        rows = db(query).select(qtable.code,
                                qltable.posn,
                                orderby=qltable.posn)
        append = row_list.append
        for question in rows:
            append([question.survey_question.code])
    else:
        # convert the JSON rules to python
        row_list = json2py(rules)
    return row_list

# =============================================================================
class S3SurveySeriesModel(S3Model):
    """
        Series Model
    """

    names = ("survey_series",
             "survey_series_id",
             "survey_series_status",
             )

    def model(self):

        T = current.T

        person_id = self.pr_person_id
        pr_person_comment = self.pr_person_comment
        organisation_id = self.org_organisation_id

        s3_date_represent = S3DateTime.date_represent
        s3_date_format = current.deployment_settings.get_L10n_date_format()

        crud_strings = current.response.s3.crud_strings

        set_method = self.set_method

        if current.deployment_settings.get_org_autocomplete():
            org_widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
        else:
            org_widget = None

        # ---------------------------------------------------------------------
        # The survey_series table is used to hold all uses of a template
        #
        #    When a series is first created the template status will change from
        #    Pending to Active and at the stage no further changes to the
        #    template can be made.
        #
        #    Typically a series will be created for an event, which may be a
        #    response to a natural disaster, an exercise,
        #    or regular data collection activity.
        #
        #    The series is a container for all the responses for the event

        series_status = {1: T("Active"),
                         2: T("Closed"),
                         }

        tablename = "survey_series"
        self.define_table(tablename,
                          Field("name", length=120,
                                default = "",
                                label = T("Name"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("description", "text", length=500,
                                default = "",
                                label = T("Description"),
                                ),
                          Field("status", "integer",
                                default = 1,
                                label = T("Status"),
                                represent = lambda index: series_status[index],
                                requires = IS_IN_SET(series_status,
                                                     zero = None),
                                #readable = True,
                                writable = False,
                                ),
                          self.survey_template_id(empty = False,
                                                  ondelete = "RESTRICT"),
                          person_id(),
                          organisation_id(widget = org_widget),
                          Field("logo", length=512,
                                default = "",
                                label = T("Logo"),
                                ),
                          Field("language", length=8,
                                default = "en",
                                label = T("Language"),
                                ),
                          s3_date("start_date",
                                  label = T("Start Date"),
                                  ),
                          s3_date("end_date",
                                  label = T("End Date"),
                                  start_field = "survey_series_start_date",
                                  default_interval = 1,
                                  ),
                          #self.super_link("source_id", "doc_source_entity"),
                          *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Conduct a Disaster Assessment"),
            title_display = T("Details of Disaster Assessment"),
            title_list = T("Disaster Assessments"),
            title_update = T("Edit this Disaster Assessment"),
            title_analysis_summary = T("Disaster Assessment Summary"),
            title_analysis_chart = T("Disaster Assessment Chart"),
            title_map = T("Disaster Assessment Map"),
            subtitle_analysis_summary = T("Summary of Completed Assessment Forms"),
            help_analysis_summary = T("Click on questions below to select them, then click 'Display Selected Questions' button to view the selected questions for all Completed Assessment Forms"),
            subtitle_analysis_chart = T("Select a label question and at least one numeric question to display the chart."),
            subtitle_map = T("Disaster Assessment Map"),
            label_list_button = T("List Disaster Assessments"),
            label_delete_button = T("Delete this Disaster Assessment"),
            msg_record_created = T("Disaster Assessment added"),
            msg_record_modified = T("Disaster Assessment updated"),
            msg_record_deleted = T("Disaster Assessment deleted"),
            msg_list_empty = T("No Disaster Assessments"))

        filter_widgets = [
            S3TextFilter("name",
                         label = T("Search")),
            S3OptionsFilter("organisation_id",
                         label = T("Organization")),
            S3DateFilter("start_date",
                         label = T("Start Date")),
            ]

        self.configure(tablename,
                       create_next = URL(f="new_assessment",
                                         vars={"viewing":"survey_series.[id]"}),
                       deduplicate = self.survey_series_duplicate,
                       filter_widgets = filter_widgets,
                       onaccept = self.series_onaccept,
                       )

        # Components
        self.add_components(tablename,
                            survey_complete = "series_id",
                            )

        series_id = S3ReusableField("series_id", "reference %s" % tablename,
                                    label = T("Series"),
                                    represent = S3Represent(lookup=tablename),
                                    readable = False,
                                    writable = False,
                                    )

        # Custom Methods
        set_method("survey", "series", method="summary", # NB This conflicts with the global summary method!
                   action = self.seriesSummary)
        set_method("survey", "series", method="graph",
                   action = self.seriesGraph)
        set_method("survey", "series", method="map", # NB This conflicts with the global map method!
                   action = self.seriesMap)
        set_method("survey", "series", method="series_chart_download",
                   action = self.seriesChartDownload)
        set_method("survey", "series", method="export_responses",
                   action = survey_ExportResponses)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict(survey_series_status = series_status,
                    survey_series_id = series_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def series_onaccept(form):
        """
            Ensure that the template status is set to Active
        """

        if form.vars.template_id:
            template_id = form.vars.template_id
        else:
            return
        table = current.s3db.survey_template
        current.db(table.id == template_id).update(status = 2)

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_series_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for a record with a similar name, ignoring case
        """

        name = item.data.get("name")
        table = item.table
        query = table.name.lower().like('%%%s%%' % name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def seriesSummary(r, **attr):
        """
        """

        s3db = current.s3db
        response = current.response
        s3 = response.s3
        posn_offset = 11

        # Retain the rheader
        rheader = attr.get("rheader", None)
        if rheader:
            rheader = rheader(r)
            output = dict(rheader=rheader)
        else:
            output = dict()
        if r.env.request_method == "POST" \
           or "mode" in r.vars:
            # This means that the user has selected the questions and
            # Wants to display the details of the selected questions
            crud_strings = s3.crud_strings["survey_complete"]
            question_ids = []
            rvars = r.vars

            if "mode" in rvars:
                mode = rvars["mode"]
                series_id = r.id
                if "selected" in rvars:
                    selected = rvars["selected"].split(",")
                else:
                    selected = []
                q_ltable = s3db.survey_question_list
                sertable = s3db.survey_series
                query = (sertable.id == series_id) & \
                        (sertable.template_id == q_ltable.template_id)
                questions = current.db(query).select(q_ltable.posn,
                                                     q_ltable.question_id,
                                                     orderby = q_ltable.posn)
                for question in questions:
                    qstn_posn = question.posn + posn_offset
                    if mode == "Inclusive":
                        if str(qstn_posn) in selected:
                            question_ids.append(str(question.question_id))
                    elif mode == "Exclusive":
                        if str(qstn_posn) not in selected:
                            question_ids.append(str(question.question_id))
                items = buildCompletedList(series_id, question_ids)
                if r.representation == "xls":
                    from ..s3.s3codecs.xls import S3XLS
                    exporter = S3XLS()
                    return exporter.encode(items,
                                           title=crud_strings.title_selected,
                                           use_colour=False
                                           )
                if r.representation == "html":
                    table = buildTableFromCompletedList(items)
                    #exporter = S3Exporter()
                    #table = exporter.html(items)
                output["items"] = table
                output["sortby"] = [[0, "asc"]]
                url_pdf = URL(c="survey", f="series",
                              args=[series_id, "summary.pdf"],
                              vars = {"mode": mode,
                                      "selected": rvars["selected"]},
                              )
                url_xls = URL(c="survey", f="series",
                              args=[series_id, "summary.xls"],
                              vars = {"mode": mode,
                                      "selected": rvars["selected"]},
                              )
                s3.formats["pdf"] = url_pdf
                s3.formats["xls"] = url_xls
            else:
                output["items"] = None
            output["title"] = crud_strings.title_selected
            output["subtitle"] = crud_strings.subtitle_selected
            output["help"] = ""
        else:
            crud_strings = s3.crud_strings["survey_series"]
            viewing = r.get_vars.get("viewing", None)
            if viewing:
                dummy, series_id = viewing.split(".")
            else:
                series_id = r.get_vars.get("series", None)
                if not series_id:
                    series_id = r.id
            form = buildSeriesSummary(series_id, posn_offset)
            output["items"] = form
            output["sortby"] = [[0, "asc"]]
            output["title"] = crud_strings.title_analysis_summary
            output["subtitle"] = crud_strings.subtitle_analysis_summary
            output["help"] = crud_strings.help_analysis_summary
            s3.dataTableBulkActionPosn = "top"
            s3.actions = None
        response.view = "survey/series_summary.html"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def getChartName():
        """
            Create a Name for a Chart
        """

        import hashlib
        rvars = current.request.vars
        end_part = "%s_%s" % (rvars.numericQuestion,
                              rvars.labelQuestion)
        h = hashlib.sha256()
        h.update(end_part)
        encoded_part = h.hexdigest()
        chart_name = "survey_series_%s_%s" % (rvars.series, encoded_part)
        return chart_name

    # -------------------------------------------------------------------------
    @staticmethod
    def seriesChartDownload(r, **attr):
        """
        """

        from gluon.contenttype import contenttype

        filename = "%s_chart.png" % r.record.name

        response = current.response
        response.headers["Content-Type"] = contenttype(".png")
        response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename

        chart_file = S3SurveySeriesModel.getChartName()
        cached = S3Chart.getCachedFile(chart_file)
        if cached:
            return cached

        # The cached version doesn't exist so regenerate it
        output = dict()
        get_vars = current.request.get_vars
        if "labelQuestion" in get_vars:
            label_question = get_vars.labelQuestion
        if "numericQuestion" in get_vars:
            numeric_question_list = get_vars.numericQuestion
            if not isinstance(numeric_question_list, (list, tuple)):
                numeric_question_list = [numeric_question_list]
        if (numeric_question_list != None) and (label_question != None):
            S3SurveySeriesModel.drawChart(output, r.id, numeric_question_list,
                                          label_question, outputFormat="png")
        return output["chart"]

    # -------------------------------------------------------------------------
    @staticmethod
    def seriesGraph(r, **attr):
        """

            Allows the user to select one string question and multiple numeric
            questions. The string question is used to group the numeric data,
            with the result displayed as a bar chart.

            For example:
                The string question can be Geographic area, and the numeric
                questions could be people injured and families displaced.
                Then the results will be grouped by each geographical area.
        """

        T = current.T
        response = current.response
        s3 = current.response.s3

        # Draw the chart
        output = dict()
        rvars = r.vars
        if "viewing" in rvars:
            dummy, series_id = rvars.viewing.split(".")
        elif "series" in rvars:
            series_id = rvars.series
        else:
            series_id = r.id
        chart_file = S3SurveySeriesModel.getChartName()
        cache_path = S3Chart.getCachedPath(chart_file)
        if cache_path and r.ajax:
            return IMG(_src=cache_path)
        else:
            numeric_question_list = None
            label_question = None
            post_vars = r.post_vars
            if post_vars is not None:
                if "labelQuestion" in post_vars:
                    label_question = post_vars.labelQuestion
                if "numericQuestion" in post_vars:
                    numeric_question_list = post_vars.numericQuestion
                    if not isinstance(numeric_question_list, (list, tuple)):
                        numeric_question_list = [numeric_question_list]
                if (numeric_question_list != None) and (label_question != None):
                    S3SurveySeriesModel.drawChart(output, series_id, numeric_question_list,
                                                  label_question)
        if r.ajax == True and "chart" in output:
            return output["chart"]

        # retain the rheader
        rheader = attr.get("rheader", None)
        if rheader:
            rheader = rheader(r)
            output["rheader"] = rheader

        # ---------------------------------------------------------------------
        def addQstnChkboxToTR(numeric_question_list, question):
            """
                Build the form
            """

            tr = TR()
            if numeric_question_list != None and \
               question["code"] in numeric_question_list:
                tr.append(INPUT(_type="checkbox",
                                _name="numericQuestion",
                                _value=question["code"],
                                value=True,
                                )
                          )
            else:
                tr.append(INPUT(_type="checkbox",
                                _name="numericQuestion",
                                _value=question["code"],
                                )
                          )
            tr.append(LABEL(question["name"]))
            return tr

        if series_id == None:
            return output

        all_questions = survey_getAllQuestionsForSeries(series_id)
        label_type_list = ("String",
                           "Option",
                           "YesNo",
                           "YesNoDontKnow",
                           "Location",
                           )
        label_questions = survey_get_series_questions_of_type(all_questions,
                                                              label_type_list)
        question_labels = []
        for question in label_questions:
            question_labels.append(question["name"])
        numeric_type_list = ("Numeric")

        form = FORM(_id="mapGraphForm")
        table = TABLE()

        label_question = SELECT(question_labels, _name="labelQuestion", value=label_question)
        table.append(TR(TH("%s:" % T("Select Label Question")),
                        _class="survey_question"))
        table.append(label_question)

        table.append(TR(TH(T("Select Numeric Questions (one or more):")),
                        _class="survey_question"))
        # First add the special questions
        special_questions = [{"code": "Count",
                              "name": T("Number of Completed Assessment Forms"),
                              }]
        inner_table = TABLE()
        for question in special_questions:
            tr = addQstnChkboxToTR(numeric_question_list, question)
            inner_table.append(tr)
        table.append(inner_table)
        # Now add the numeric questions
        numeric_questions = survey_get_series_questions_of_type(all_questions,
                                                                numeric_type_list)
        inner_table = TABLE()
        for question in numeric_questions:
            tr = addQstnChkboxToTR(numeric_question_list, question)
            inner_table.append(tr)
        table.append(inner_table)
        form.append(table)

        series = INPUT(_type="hidden",
                       _id="selectSeriesID",
                       _name="series",
                       _value="%s" % series_id,
                       )
        button = INPUT(_type="button",
                       _id="chart_btn",
                       _name="Chart",
                       _value=T("Display Chart"),
                       _class="small primary button",
                       )
        form.append(series)
        form.append(button)
        # Set up the javascript code for ajax interaction
        jurl = URL(c=r.prefix, f=r.function, args=r.args)
        s3.jquery_ready.append('''
$('#chart_btn').click(function(){
 var data=$('#mapGraphForm').serialize()
 var url='<a class="action-btn" href=series_chart_download?' + data + '>Download Chart</a>'
 $.post('%s',data,function(data){
  $('#survey_chart').empty();
  $('#survey_chart').append(data);
  $('#survey_chart_download').empty();
  $('#survey_chart_download').append(url);
 });
});
''' % jurl)
        output["showForm"] = P(T("Click on the chart to show/hide the form."))
        output["form"] = form
        output["title"] = s3.crud_strings["survey_series"].title_analysis_chart
        response.view = "survey/series_analysis.html"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def drawChart(output,
                  series_id,
                  numeric_question_list,
                  label_question,
                  outputFormat=None):
        """
        """

        T = current.T

        get_answers = survey_getAllAnswersForQuestionInSeries
        gqstn = survey_getQuestionFromName(label_question, series_id)
        gqstn_id = gqstn["qstn_id"]
        ganswers = get_answers(gqstn_id, series_id)
        data_list = []
        legend_labels = []
        for numeric_question in numeric_question_list:
            if numeric_question == "Count":
                # get the count of replies for the label question
                gqstn_type = gqstn["type"]
                analysis_tool = survey_analysis_type[gqstn_type](gqstn_id, ganswers)
                mapdict = analysis_tool.uniqueCount()
                label = mapdict.keys()
                data = mapdict.values()
                legend_labels.append(T("Count of Question"))
            else:
                qstn = survey_getQuestionFromCode(numeric_question, series_id)
                qstn_id = qstn["qstn_id"]
                qstn_type = qstn["type"]
                answers = get_answers(qstn_id, series_id)
                analysis_tool = survey_analysis_type[qstn_type](qstn_id, answers)
                label = analysis_tool.qstnWidget.fullName()
                if len(label) > 20:
                    label = "%s..." % label[0:20]
                legend_labels.append(label)
                grouped = analysis_tool.groupData(ganswers)
                aggregate = "Sum"
                filtered = analysis_tool.filter(aggregate, grouped)
                (label, data) = analysis_tool.splitGroupedData(filtered)
            if data != []:
                data_list.append(data)

        if data_list == []:
            output["chart"] = H4(T("There is insufficient data to draw a chart from the questions selected"))
        else:
            chart_file = S3SurveySeriesModel.getChartName()
            chart = S3Chart(path=chart_file, width=7.2)
            chart.asInt = True
            chart.survey_bar(label_question,
                             data_list,
                             label,
                             legend_labels)
            if outputFormat == None:
                image = chart.draw()
            else:
                image = chart.draw(output=outputFormat)
            output["chart"] = image
            request = current.request
            chart_link = A(T("Download"),
                           _href=URL(c="survey",
                                     f="series",
                                     args=request.args,
                                     vars=request.vars
                                     )
                           )
            output["chartDownload"] = chart_link

    # -------------------------------------------------------------------------
    @staticmethod
    def seriesMap(r, **attr):
        """
        """

        import math
        from s3survey import S3AnalysisPriority

        T = current.T
        response = current.response
        s3 = response.s3
        gis = current.gis

        # retain the rheader
        rheader = attr.get("rheader", None)
        if rheader:
            rheader = rheader(r)
            output = dict(rheader=rheader)
        else:
            output = dict()
        crud_strings = s3.crud_strings["survey_series"]
        viewing = r.get_vars.get("viewing", None)
        if viewing:
            dummy, series_id = viewing.split(".")
        else:
            series_id = r.get_vars.get("series", None)
            if not series_id:
                series_id = r.id
        table = r.table
        if series_id == None:
            records = current.db(table.deleted == False).select(table.id,
                                                                table.name)
            series = {}
            for row in records:
                series[row.id] = row.name
        else:
            series = {r.id: r.record.name}
        pqstn = {}
        pqstn_name = r.post_vars.get("pqstn_name", None)
        if pqstn_name is None:
            pqstn = survey_getPriorityQuestionForSeries(series_id)
            if "name" in pqstn:
                pqstn_name = pqstn["name"]
        feature_queries = []
        bounds = {}

        # Build the drop down list of priority questions
        all_questions = survey_getAllQuestionsForSeries(series_id)
        numeric_type_list = ("Numeric")
        numeric_questions = survey_get_series_questions_of_type(all_questions,
                                                                numeric_type_list)
        num_questions = []
        for question in numeric_questions:
            num_questions.append(question["name"])

        form = FORM(_id="mapQstnForm")
        table = TABLE()

        if pqstn:
            priority_question = SELECT(num_questions, _name="pqstn_name",
                                  value=pqstn_name)
        else:
            priority_question = None

        # Set up the legend
        priority_object = S3AnalysisPriority(range=[-.66, .66],
                                             colour={-1:"#888888", # grey
                                                      0:"#008000", # green
                                                      1:"#FFFF00", # yellow
                                                      2:"#FF0000", # red
                                                      },
                                             # Make Higher-priority show up more clearly
                                             opacity={-1:0.5,
                                                       0:0.6,
                                                       1:0.7,
                                                       2:0.8,
                                                       },
                                             image={-1:"grey",
                                                     0:"green",
                                                     1:"yellow",
                                                     2:"red",
                                                     },
                                             desc={-1:"No Data",
                                                    0:"Low",
                                                    1:"Average",
                                                    2:"High",
                                                    },
                                             zero = True)
        for series_id in series:
            series_name = series[series_id]
            response_locations = getLocationList(series_id)
            if pqstn == {} and pqstn_name:
                for question in numeric_questions:
                    if pqstn_name == question["name"]:
                        pqstn = question
            if pqstn != {}:
                pqstn_id = pqstn["qstn_id"]
                answers = survey_getAllAnswersForQuestionInSeries(pqstn_id,
                                                                  series_id)
                analysis_tool = survey_analysis_type["Numeric"](pqstn_id,
                                                                answers)
                analysis_tool.advancedResults()
            else:
                analysis_tool = None
            if analysis_tool != None and not math.isnan(analysis_tool.mean):
                priority_band = analysis_tool.priorityBand(priority_object)
                legend = TABLE(TR(TH(T("Marker Levels"), _colspan=3),
                               _class= "survey_question"),
                               )
                for key in priority_object.image.keys():
                    tr = TR(TD(priority_object.imageURL(r.application,
                                                    key)),
                            TD(priority_object.desc(key)),
                            TD(priority_object.rangeText(key, priority_band)),
                            )
                    legend.append(tr)
                output["legend"] = legend

            if len(response_locations) > 0:
                for i in range(0, len(response_locations)):
                    location = response_locations[i]
                    complete_id = location.complete_id
                    # Insert how we want this to appear on the map
                    url = URL(c="survey",
                              f="series",
                              args=[series_id,
                                    "complete",
                                    complete_id,
                                    "read"
                                    ]
                              )
                    location.shape = "circle"
                    location.size = 5
                    if analysis_tool is None:
                        priority = -1
                    else:
                        priority = analysis_tool.priority(complete_id,
                                                          priority_object)
                    location.colour = priority_object.colour[priority]
                    location.opacity = priority_object.opacity[priority]
                    location.popup_url = url
                    location.popup_label = response_locations[i].name
                feature_queries.append({ "name": "%s: Assessments" % series_name,
                                         "query": response_locations,
                                         "active": True })
                if bounds == {}:
                    bounds = (gis.get_bounds(features=response_locations))
                else:
                    new_bounds = gis.get_bounds(features=response_locations)
                    # Where is merge_bounds defined!?
                    bounds = merge_bounds([bounds, new_bounds])
        if bounds == {}:
            bounds = gis.get_bounds()
        gismap = gis.show_map(feature_queries = feature_queries,
                              #height = 600,
                              #width = 720,
                              bbox = bounds,
                              #collapsed = True,
                              catalogue_layers = True,
                              )
        series = INPUT(_type="hidden",
                       _id="selectSeriesID",
                       _name="series",
                       _value="%s" % series_id
                       )
        table.append(TR(TH("%s:" % T("Display Question on Map")),
                        _class="survey_question"))
        table.append(priority_question)
        table.append(series)
        form.append(table)

        button = INPUT(_type="submit", _name="Chart",
                       _value=T("Update Map"),
                       _class="small primary button",
                       )
        # REMOVED until we have dynamic loading of maps.
        #button = INPUT(_type="button", _id="map_btn", _name="Map_Btn", _value=T("Select the Question"))
        #jurl = URL(c=r.prefix, f=r.function, args=r.args)
        #s3.jquery_ready.append('''
#$('#map_btn').click(function(){
# $.post('%s',$('#mapQstnForm').serialize(),function(data){
#  obj = jQuery.parseJSON(data);
#  $('#survey_map-legend').empty();
#  $('#survey_map-legend').append(obj.legend);
#  $('#survey_map-container').empty();
#  $('#survey_map-container').append(obj.map);
# });
#});
#''' % jurl)
        form.append(button)

        output["title"] = crud_strings.title_map
        output["subtitle"] = crud_strings.subtitle_map
        output["instructions"] = T("Click on a marker to see the Completed Assessment Form")
        output["form"] = form
        output["map"] = map

        response.view = "survey/series_map.html"
        return output

# =============================================================================
def survey_serieslist_dataTable_post(r):
    """
        Replace the Action Buttons
    """

    #S3CRUD.action_buttons(r)
    current.response.s3.actions = [
                   dict(label=current.messages.UPDATE,
                        _class="action-btn edit",
                        url=URL(c="survey", f="series",
                                args=["[id]", "summary"]
                                )
                        ),
                  ]

# =============================================================================
def survey_series_rheader(r):
    """
        The series rheader
    """

    if r.representation == "html":

        db = current.db
        s3db = current.s3db
        tablename, record = s3_rheader_resource(r)
        if not record:
            series_id = current.request.vars.series
            table = s3db.survey_series
            record = db(table.id == series_id).select(table.id,
                                                      table.template_id,
                                                      table.name,
                                                      table.status,
                                                      limitby=(0, 1)
                                                      ).first()
        if record != None:
            T = current.T

            # Tabs
            tabs = [(T("Details"), None),
                    (T("Completed Assessments"), "complete"),
                    (T("Summary"), "summary"),
                    (T("Chart"), "graph"),
                    (T("Map"), "map"),
                    ]
            if current.auth.s3_has_permission("create", "survey_complete"):
                tabs.insert(1, (T("Enter Completed Assessment"), "new_assessment/"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            ctable = s3db.survey_complete
            qty = db(ctable.series_id == record.id).count()
            tsection = TABLE(_class="survey-complete-list")
            label_section = T("Number of Completed Assessment Forms")
            rsection = TR(TH(label_section), TD(qty))
            tsection.append(rsection)

            urlexport = URL(c="survey", f="series_export_formatted",
                            args=[record.id])
            translate_form = FORM(_action=urlexport)
            translation_list = survey_getAllTranslationsForSeries(record.id)
            if len(translation_list) > 0:
                translation_table = TABLE()
                tr = TR(INPUT(_type='radio',
                              _name='translation_language',
                              _value="Default",
                              _checked=True,
                              ),
                        LABEL("Default"))
                column_count = 1
                for translation in translation_list:
                    # include a maximum of 4 translation languages per row
                    if column_count == 4:
                        translation_table.append(tr)
                        tr = TR()
                        column_count = 0
                    tr.append(INPUT(_type="radio",
                                    _name="translation_language",
                                    _value=translation["code"],
                                   ))
                    tr.append(LABEL(translation["language"]))
                    column_count += 1
                if column_count != 0:
                    translation_table.append(tr)
                translate_form.append(translation_table)
            export_xls_btn = INPUT(_type="submit",
                                   _id="export_xls_btn",
                                   _name="Export_Spreadsheet",
                                   _value=T("Download Assessment Form Spreadsheet"),
                                   _class="action-btn"
                                  )
            translate_form.append(export_xls_btn)
            export_rtf_btn = INPUT(_type="submit",
                                   _id="export_rtf_btn",
                                   _name="Export_Word",
                                   _value=T("Download Assessment Form Document"),
                                   _class="action-btn"
                                   )
            translate_form.append(export_rtf_btn)
            urlimport = URL(c="survey",
                            f="series",
                            args=[record.id, "export_responses"],
                            extension="xls")
            buttons = DIV(A(T("Export all Completed Assessment Data"),
                            _href=urlimport,
                            _id="All_resposnes",
                            _class="action-btn"
                            ),
                          )

            rheader = DIV(TABLE(TR(TH("%s: " % T("Template")),
                                   survey_template_represent(record.template_id),
                                   TH("%s: " % T("Name")),
                                   record.name,
                                   TH("%s: " % T("Status")),
                                   s3db.survey_series_status[record.status],
                                   ),
                                ),
                          tsection,
                          translate_form,
                          buttons,
                          rheader_tabs)
            return rheader
    return None

# =============================================================================
def survey_buildQuestionnaireFromSeries(series_id, complete_id=None):
    """
        Build a form displaying all the questions for a given series_id
        If the complete_id is also provided then the responses to each
        completed question will also be displayed

        @ToDo: Remove wrapper
    """

    questions = survey_getAllQuestionsForSeries(series_id)
    return buildQuestionsForm(questions, complete_id)

# =============================================================================
def survey_save_answers_for_series(series_id, complete_id, rvars):
    """
        function to save the list of answers for a completed series

        @ToDo: Remove wrapper
    """

    questions = survey_getAllQuestionsForSeries(series_id)
    return saveAnswers(questions, series_id, complete_id, rvars)

# =============================================================================
def saveAnswers(questions, series_id, complete_id, rvars):
    """
    """

    text = ""
    table = current.s3db.survey_complete
    for question in questions:
        code = question["code"]
        if (code in rvars) and rvars[code] != "":
            line = '"%s","%s"\n' % (code, rvars[code])
            text += line
    if complete_id == None:
        # Insert into database
        record_id = table.insert(series_id = series_id, answer_list = text)
        S3SurveyCompleteModel.completeOnAccept(record_id)
        return record_id
    else:
        # Update the complete_id record
        current.db(table.id == complete_id).update(answer_list = text)
        S3SurveyCompleteModel.completeOnAccept(complete_id)
        return complete_id

# =============================================================================
def survey_getPriorityQuestionForSeries(series_id):
    """
    """

    template_rec = survey_getTemplateFromSeries(series_id)
    if template_rec != None:
        priority_question_code = template_rec["priority_qstn"]
        question = survey_getQuestionFromCode(priority_question_code,
                                              series_id)
        return question
    else:
        return None

# =============================================================================
def buildSeriesSummary(series_id, posn_offset):
    """
    """

    from s3.s3data import S3DataTable
    T = current.T

    table = TABLE(_id="series_summary",
                  _class="dataTable display")
    hr = TR(TH(""), # Bulk action column
            TH(T("Position")),
            TH(T("Question")),
            TH(T("Type")),
            TH(T("Summary"))
            )
    header = THEAD(hr)

    questions = survey_getAllQuestionsForSeries(series_id)
    line = []
    body = TBODY()
    for question in questions:
        if question["type"] == "Grid":
            continue
        question_id = question["qstn_id"]
        widget_object = survey_getWidgetFromQuestion(question_id)
        br = TR()
        posn = int(question["posn"])+posn_offset
        br.append(TD(INPUT(_id="select%s" % posn,
                           _type="checkbox",
                           _class="bulkcheckbox",
                           )))
        br.append(posn) # add an offset to make all id's +ve
        br.append(widget_object.fullName())
        #br.append(question["name"])
        qtype = widget_object.type_represent()
        answers = survey_getAllAnswersForQuestionInSeries(question_id,
                                                          series_id)
        analysis_tool = survey_analysis_type[question["type"]](question_id,
                                                               answers)
        chart = analysis_tool.chartButton(series_id)
        cell = TD()
        cell.append(qtype)
        if chart:
            cell.append(chart)
        br.append(cell)
        analysis_tool.count()
        br.append(analysis_tool.summary())

        body.append(br)

    table.append(header)
    table.append(body)

    s3 = current.response.s3
    # Turn off server side pagination
    s3.no_sspag = True
    # Turn multi-select on
    s3.dataTableBulkActions = [current.T("Display Selected Questions")]

    attr = S3DataTable.getConfigData()
    form = S3DataTable.htmlConfig(table,
                                  "series_summary",
                                  [[0, 'asc']], # order by
                                  "", # the filter string
                                  None, # the rfields
                                  **attr
                                  )
    series = INPUT(_type="hidden", _id="selectSeriesID", _name="series",
                   _value="%s" % series_id)
    form.append(series)
    return form

# =============================================================================
class S3SurveyCompleteModel(S3Model):
    """
        Completed Surveys Model
    """

    names = ("survey_complete",
             "survey_complete_id",
             "survey_answer",
             )

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        #    The survey_complete table holds all of the answers for a completed
        #    response. It has a link back to the series this response belongs to.
        #
        #    Whilst this table holds all of the answers in a text field during
        #    the onaccept each answer is extracted and then stored in the
        #    survey_answer table. This process of moving the answers to a
        #    separate table makes it easier to analyse the answers
        #    for a given question across all responses.

        tablename = "survey_complete"
        define_table(tablename,
                     self.survey_series_id(),
                     Field("answer_list", "text",
                           represent = survey_answer_list_represent,
                           ),
                     Field("location", "text",
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Enter Completed Assessment Form"),
            title_display = T("Completed Assessment Form Details"),
            title_list = T("Completed Assessment Forms"),
            title_update = T("Edit Completed Assessment Form"),
            title_selected = T("Selected Questions for all Completed Assessment Forms"),
            subtitle_selected = T("Selected Questions for all Completed Assessment Forms"),
            label_list_button = T("List Completed Assessment Forms"),
            label_delete_button = T("Delete this Completed Assessment Form"),
            msg_record_created = T("Completed Assessment Form entered"),
            msg_record_modified = T("Completed Assessment Form updated"),
            msg_record_deleted = T("Completed Assessment Form deleted"),
            msg_list_empty = T("No Completed Assessment Forms"),
            title_upload = T("Upload the Completed Assessment Form")
            )

        configure(tablename,
                  deduplicate = self.survey_complete_duplicate,
                  onaccept = self.complete_onaccept,
                  onvalidation = self.complete_onvalidate,
                  )

        complete_id = S3ReusableField("complete_id", "reference %s" % tablename,
                                      readable = False,
                                      writable = False,
                                      )

        self.add_components(tablename,
                            survey_complete="series_id",
                            )

        # ---------------------------------------------------------------------
        # The survey_answer table holds the answer for a single response
        #    of a given question.

        tablename = "survey_answer"
        define_table(tablename,
                     complete_id(),
                     self.survey_question_id(),
                     Field("value", "text"),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Assessment Answer"),
            title_display = T("Assessment Answer Details"),
            title_list = T("Assessment Answers"),
            title_update = T("Edit Assessment Answer"),
            label_list_button = T("List Assessment Answers"),
            label_delete_button = T("Delete this Assessment Answer"),
            msg_record_created = T("Assessment Answer added"),
            msg_record_modified = T("Assessment Answer updated"),
            msg_record_deleted = T("Assessment Answer deleted"),
            msg_list_empty = T("No Assessment Answers"))

        configure(tablename,
                  deduplicate = self.survey_answer_duplicate,
                  onaccept = self.answer_onaccept,
                  )

        # ---------------------------------------------------------------------
        return dict(survey_complete_id = complete_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def extractAnswerFromAnswerList(answer_list, question_code):
        """
            function to extract the answer for the question code
            passed in from the list of answers. This is in a CSV
            format created by the XSL stylesheet or by the function
            saveAnswers()
        """

        start = answer_list.find(question_code)
        if start == -1:
            return None
        start = start + len(question_code) + 3
        end = answer_list.find('"', start)
        answer = answer_list[start:end]
        return answer

    # -------------------------------------------------------------------------
    @staticmethod
    def complete_onvalidate(form):
        """
        """

        T = current.T
        form_vars = form.vars
        if "series_id" not in form_vars or form_vars.series_id == None:
            form.errors.series_id = T("Series details missing")
            return False
        if "answer_list" not in form_vars or form_vars.answer_list == None:
            form.errors.answer_list = T("The answers are missing")
            return False
        series_id = form_vars.series_id
        answer_list = form_vars.answer_list
        qstn_list = survey_getAllQuestionsForSeries(series_id)
        qstns = []
        for qstn in qstn_list:
            qstns.append(qstn["code"])
        temp_answer_list = answer_list.splitlines(True)
        for answer in temp_answer_list:
            qstn_code = answer[1:answer.find('","')]
            if qstn_code not in qstns:
                msg = "%s: %s" % (T("Unknown question code"), qstn_code)
                if answer_list not in form.errors:
                    form.errors.answer_list = msg
                else:
                    form.errors.answer_list += msg
        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def complete_onaccept(form):
        """
            All of the answers will be stored in the answer_list in the
            format "code","answer"
            They will then be inserted into the survey_answer table
            each item will be a record on that table.

            This will also extract the default location question as
            defined by the template and store this in the location field
        """

        complete_id = form.vars.id
        if complete_id:
            S3SurveyCompleteModel.completeOnAccept(complete_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def completeOnAccept(complete_id):
        """
        """

        # Get the basic data that is needed
        s3db = current.s3db
        rtable = s3db.survey_complete
        atable = s3db.survey_answer
        record = rtable[complete_id]
        series_id = record.series_id
        purge_prefix = "survey_series_%s" % series_id
        S3Chart.purgeCache(purge_prefix)
        if series_id == None:
            return
        # Save all the answers from answer_list in the survey_answer table
        answer_list = record.answer_list
        S3SurveyCompleteModel.importAnswers(complete_id, answer_list)
        # Extract the default template location question and save the
        # answer in the location field
        template_record = survey_getTemplateFromSeries(series_id)
        location_details = template_record["location_detail"]
        if not location_details:
            return
        widget_obj = get_default_location(complete_id)
        if widget_obj:
            current.db(rtable.id == complete_id).update(location = widget_obj.repr())
        locations = get_location_details(complete_id)
        S3SurveyCompleteModel.importLocations(locations)

    # -------------------------------------------------------------------------
    @staticmethod
    def importAnswers(complete_id, question_list):
        """
            Private function used to save the answer_list stored in
            survey_complete into answer records held in survey_answer
        """

        import csv
        import os

        strio = StringIO()
        strio.write(question_list)
        strio.seek(0)
        answer = []
        append = answer.append
        reader = csv.reader(strio)
        for row in reader:
            if row != None:
                row.insert(0, complete_id)
                append(row)

        from tempfile import TemporaryFile
        csvfile = TemporaryFile()
        writer = csv.writer(csvfile)
        writerow = writer.writerow
        writerow(["complete_id", "question_code", "value"])
        for row in answer:
            writerow(row)
        csvfile.seek(0)
        xsl = os.path.join("applications",
                           current.request.application,
                           "static",
                           "formats",
                           "s3csv",
                           "survey",
                           "answer.xsl")
        resource = current.s3db.resource("survey_answer")
        resource.import_xml(csvfile, stylesheet = xsl, format="csv",)

    # -------------------------------------------------------------------------
    @staticmethod
    def importLocations(location_dict):
        """
            private function used to save the locations to gis.location
        """

        import csv
        import os

        last_loc_widget = None
        code_list = ["STD-L0", "STD-L1", "STD-L2", "STD-L3", "STD-L4"]
        heading_list = ["Country",
                        "ADM1_NAME",
                        "ADM2_NAME",
                        "ADM3_NAME",
                        "ADM4_NAME",
                        ]

        answer = []
        headings = []
        aappend = answer.append
        happend = headings.append
        for position, location in enumerate(code_list):
            if location in location_dict:
                aappend(location_dict[location].repr())
                last_loc_widget = location_dict[location]
                happend(heading_list[position])

        # Check that we have at least one location question answered
        if last_loc_widget == None:
            return
        code_list = ["STD-P-Code", "STD-Lat", "STD-Lon"]
        for loc in code_list:
            if loc in location_dict:
                aappend(location_dict[loc].repr())
            else:
                aappend("")

        from tempfile import TemporaryFile
        csvfile = TemporaryFile()
        writer = csv.writer(csvfile)
        headings += ["Code2", "Lat", "Lon"]
        writer.writerow(headings)
        writer.writerow(answer)
        csvfile.seek(0)
        xsl = os.path.join("applications",
                           current.request.application,
                           "static",
                           "formats",
                           "s3csv",
                           "gis",
                           "location.xsl")
        resource = current.s3db.resource("gis_location")
        resource.import_xml(csvfile, stylesheet = xsl, format="csv")

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_complete_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for a record with the same name, answer_list
        """

        answers = item.data.get("answer_list")
        table = item.table
        query = (table.answer_list == answers)
        try:
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        except:
            # if this is part of an import then the select will throw an error
            # if the question code doesn't exist.
            # This can happen during an import if the wrong file is used.
            return

    # -------------------------------------------------------------------------
    @staticmethod
    def answer_onaccept(form):
        """
            Some question types may require additional processing
        """

        form_vars = form.vars
        if form_vars.complete_id and form_vars.question_id:
            atable = current.s3db.survey_answer
            complete_id = form_vars.complete_id
            question_id = form_vars.question_id
            value = form_vars.value
            widget_obj = survey_getWidgetFromQuestion(question_id)
            new_value = widget_obj.onaccept(value)
            if new_value != value:
                query = (atable.question_id == question_id) & \
                        (atable.complete_id == complete_id)
                current.db(query).update(value = new_value)

    # -------------------------------------------------------------------------
    @staticmethod
    def survey_answer_duplicate(item):
        """
            Rules for finding a duplicate:
                - Look for a record with the same complete_id and question_id
        """

        data = item.data
        qid = data.get("question_id")
        rid = data.get("complete_id")
        table = item.table
        query = (table.question_id == qid) & \
                (table.complete_id == rid)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
def survey_answerlist_dataTable_pre():
    """
        The answer list has been removed for the moment. Currently it
        displays all answers for a summary it would be better to
        be able to display just a few select answers
    """

    list_fields = ["created_on", "series_id", "location", "modified_by"]
    current.s3db.configure("survey_complete", list_fields=list_fields)

# =============================================================================
def survey_answerlist_dataTable_post(r):
    """
        Replace Action Buttons
    """

    #S3CRUD.action_buttons(r)
    current.response.s3.actions = [
                    dict(label=current.messages["UPDATE"],
                         _class="action-btn edit",
                         url=URL(c="survey", f="series",
                                 args=[r.id, "complete", "[id]", "update"])
                         ),
                    ]

# =============================================================================
def survey_answer_list_represent(value):
    """
        Display the answer list in a formatted table.
        Displaying the full question (rather than the code)
        and the answer.
    """

    db = current.db
    qtable = current.s3db.survey_question
    answer_text = value
    answer_list = answer_text.splitlines()
    result = TABLE()
    questions = {}
    xml_decode = S3Codec.xml_decode
    for line in answer_list:
        line = xml_decode(line)
        (question, answer) = line.split(",", 1)
        question = question.strip("\" ")
        if question in questions:
            question = questions[question]
        else:
            query = (qtable.code == question)
            qstn = db(query).select(qtable.name,
                                    limitby=(0, 1)).first()
            if not qstn:
                continue
            questions[question] = qstn.name
            question = qstn.name
        answer = answer.strip("\" ")
        result.append(TR(TD(B(question)), TD(answer)))
    return result

# =============================================================================
def get_location_details(complete_id):
    """
        It will return a dict of values for all of the standard location
        questions that have been answered
    """

    db = current.db
    s3db = current.s3db

    locations = {}
    ctable = s3db.survey_complete
    qtable = s3db.survey_question
    atable = s3db.survey_answer
    query = (atable.question_id == qtable.id) & \
            (atable.complete_id == ctable.id)
    code_list = ["STD-P-Code",
                 "STD-L0", "STD-L1", "STD-L2", "STD-L3", "STD-L4",
                 "STD-Lat", "STD-Lon"]
    for location_code in code_list:
        record = db(query & (qtable.code == location_code)).select(qtable.id,
                                                                   limitby=(0, 1)).first()
        if record:
            widget_obj = survey_getWidgetFromQuestion(record.id)
            widget_obj.loadAnswer(complete_id, record.id)
            locations[location_code] = widget_obj
    return locations

# =============================================================================
def get_default_location(complete_id):
    """
        It will check each standard location question in
        the hierarchy until either one is found or none are found
    """

    db = current.db
    s3db = current.s3db

    ctable = s3db.survey_complete
    qtable = s3db.survey_question
    atable = s3db.survey_answer
    query = (atable.question_id == qtable.id) & \
            (atable.complete_id == ctable.id)
    code_list = ["STD-L4", "STD-L3", "STD-L2", "STD-L1", "STD-L0"]
    for location_code in code_list:
        record = db(query & (qtable.code == location_code)).select(qtable.id,
                                                                   limitby=(0, 1)).first()
        if record:
            widget_obj = survey_getWidgetFromQuestion(record.id)
            break
    if record:
        widget_obj.loadAnswer(complete_id, record.id)
        return widget_obj
    else:
        return None

# =============================================================================
def survey_getAllAnswersForQuestionInSeries(question_id, series_id):
    """
        function to return all the answers for a given question
        from with a specified series
    """

    s3db = current.s3db
    ctable = s3db.survey_complete
    atable = s3db.survey_answer
    query = (atable.question_id == question_id) & \
            (atable.complete_id == ctable.id) & \
            (ctable.series_id == series_id)
    rows = current.db(query).select(atable.id,
                                    atable.value,
                                    atable.complete_id)
    answers = []
    for row in rows:
        answer = {}
        answer["answer_id"] = row.id
        answer["value"] = row.value
        answer["complete_id"] = row.complete_id
        answers.append(answer)
    return answers

# =============================================================================
def buildTableFromCompletedList(data_source):
    """
    """

    headers = data_source[0]
    items = data_source[2:]

    table = TABLE(_id="completed_list",
                  _class="dataTable display")
    hr = TR()
    for title in headers:
        hr.append(TH(title))
    header = THEAD(hr)

    body = TBODY()

    for row in items:
        tr = TR()
        for answer in row:
            tr.append(TD(answer))
        body.append(tr)

    table.append(header)
    table.append(body)
    # Turn off server side pagination
    current.response.s3.no_sspag = True

    attr = S3DataTable.getConfigData()
    form = S3DataTable.htmlConfig(table,
                                  "completed_list",
                                  [[0, 'asc']], # order by
                                  "", # the filter string
                                  None, # the rfields
                                  **attr
                                  )
    return form

# =============================================================================
def buildCompletedList(series_id, question_id_list):
    """
        build a list of completed items for the series including
        just the questions in the list passed in

        The list will come in three parts.
        1) The first row is the header (list of field labels)
        2) The seconds row is the type of each column
        3) The remaining rows are the data

        @param series_id: The id of the series
        @param question_id_list: The list of questions to display
    """

    db = current.db
    qtable = current.s3db.survey_question

    headers = []
    happend = headers.append
    types = []
    items = []
    qstn_posn = 0
    row_len = len(question_id_list)
    complete_lookup = {}
    for question_id in question_id_list:
        answers = survey_getAllAnswersForQuestionInSeries(question_id,
                                                          series_id)
        widget_obj = survey_getWidgetFromQuestion(question_id)

        question = db(qtable.id == question_id).select(qtable.name,
                                                       limitby=(0, 1)).first()
        happend(question.name)
        types.append(widget_obj.db_type())

        for answer in answers:
            complete_id = answer["complete_id"]
            if complete_id in complete_lookup:
                row = complete_lookup[complete_id]
            else:
                row = len(complete_lookup)
                complete_lookup[complete_id] = row
                items.append([''] * row_len)
            items[row][qstn_posn] = widget_obj.repr(answer["value"])
        qstn_posn += 1

    return [headers] + [types] + items

# =============================================================================
def getLocationList(series_id):
    """
        Get a list of the LatLons for each Response in a Series
    """

    response_locations = []
    rappend = response_locations.append
    code_list = ["STD-L4", "STD-L3", "STD-L2", "STD-L1", "STD-L0"]

    table = current.s3db.survey_complete
    rows = current.db(table.series_id == series_id).select(table.id,
                                                           table.answer_list)
    for row in rows:
        lat = None
        lon = None
        name = None
        answer_list = row.answer_list.splitlines()
        answer_dict = {}
        for line in answer_list:
            (question, answer) = line.split(",", 1)
            question = question.strip('"')
            if question in code_list:
                # Store to get the name
                answer_dict[question] = answer.strip('"')
            elif question == "STD-Lat":
                try:
                    lat = float(answer.strip('"'))
                except ValueError:
                    pass
                else:
                    if lat < -90.0 or lat > 90.0:
                        lat = None
            elif question == "STD-Lon":
                try:
                    lon = float(answer.strip('"'))
                except ValueError:
                    pass
                else:
                    if lon < -180.0 or lon > 180.0:
                        lon = None
            else:
                # Not relevant here
                continue

        for loc_code in code_list:
            # Retrieve the name of the lowest Lx
            if loc_code in answer_dict:
                name = answer_dict[loc_code]
                break

        if lat and lon:
            from s3dal import Row
            # We have sufficient data to display on the map
            location = Row()
            location.lat = lat
            location.lon = lon
            location.name = name
            location.complete_id = row.id
            rappend(location)
        else:
            # The lat & lon were not added to the assessment so try and get one
            loc_widget = get_default_location(row.id)
            if loc_widget:
                complete_id = loc_widget.question["complete_id"]
                if "answer" not in loc_widget.question:
                    continue
                answer = loc_widget.question["answer"]
                if loc_widget != None:
                    record = loc_widget.getLocationRecord(complete_id, answer)
                    if len(record.records) == 1:
                        location = record.records[0].gis_location
                        location.complete_id = complete_id
                        rappend(location)

    return response_locations

# =============================================================================
class S3SurveyTranslateModel(S3Model):
    """
        Translations Model
    """

    from gluon.languages import read_dict, write_dict

    names = ("survey_translate",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # The survey_translate table holds the details of the language
        #    for which the template has been translated into.

        LANG_HELP = T("This is the full name of the language and will be displayed to the user when selecting the template language.")
        CODE_HELP = T("This is the short code of the language and will be used as the name of the file. This should be the ISO 639 code.")
        tablename = "survey_translate"
        self.define_table(tablename,
                          self.survey_template_id(),
                          Field("language",
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Language"),
                                                                LANG_HELP))
                                ),
                          Field("code",
                                comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Language Code"),
                                                                CODE_HELP))
                                ),
                          Field("file", "upload",
                                autodelete=True),
                          Field("filename",
                                readable = False,
                                writable = False,
                                ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Translation Language"),
        )

        self.configure(tablename,
                       onaccept = self.translate_onaccept,
                       )
        # ---------------------------------------------------------------------
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def translate_onaccept(form):
        """
            If the translation spreadsheet has been uploaded then
            it needs to be processed.

            The translation strings need to be extracted from
            the spreadsheet and inserted into the language file.
        """

        if "file" in form.vars:
            try:
                import xlrd
            except ImportError:
                print >> sys.stderr, "ERROR: xlrd & xlwt modules are needed for importing spreadsheets"
                return None

            from gluon.languages import read_dict, write_dict

            T = current.T
            request =  current.request
            response = current.response

            msg_none = T("No translations exist in spreadsheet")
            upload_file = request.post_vars.file
            upload_file.file.seek(0)
            open_file = upload_file.file.read()
            lang = form.record.language
            code = form.record.code
            try:
                workbook = xlrd.open_workbook(file_contents=open_file)
            except IOError:
                msg = T("Unable to open spreadsheet")
                response.error = msg
                response.flash = None
                return
            try:
                language_sheet = workbook.sheet_by_name(lang)
            except IOError:
                msg = T("Unable to find sheet %(sheet_name)s in uploaded spreadsheet") % \
                    dict(sheet_name=lang)
                response.error = msg
                response.flash = None
                return
            if language_sheet.ncols == 1:
                response.warning = msg_none
                response.flash = None
                return
            count = 0
            lang_filename = "applications/%s/uploads/survey/translations/%s.py" % \
                (request.application, code)
            try:
                strings = read_dict(lang_filename)
            except IOError:
                strings = dict()
            for row in xrange(1, language_sheet.nrows):
                original = language_sheet.cell_value(row, 0)
                translation = language_sheet.cell_value(row, 1)
                if (original not in strings) or translation != "":
                    strings[original] = translation
                    count += 1
            write_dict(lang_filename, strings)
            if count == 0:
                response.warning = msg_none
                response.flash = None
            else:
                response.flash = T("%(count_of)d translations have been imported to the %(language)s language file") % \
                    dict(count_of=count, language=lang)

# =============================================================================
def survey_getAllTranslationsForTemplate(template_id):
    """
        Function to return all the translations for the given template
    """

    table = current.s3db.survey_translate
    row = current.db(table.template_id == template_id).select()
    return row

# =============================================================================
def survey_getAllTranslationsForSeries(series_id):
    """
        Function to return all the translations for the given series
    """

    table = current.s3db.survey_series
    row = current.db(table.id == series_id).select(table.template_id,
                                                   limitby=(0, 1)).first()
    template_id = row.template_id
    return survey_getAllTranslationsForTemplate(template_id)

# =============================================================================
class survey_TranslateDownload(S3Method):
    """
        Download a Translation Template
    """

    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.representation != "xls":
            r.error(501, current.ERROR.BAD_FORMAT)

        template_id = r.id
        template = r.record
        if not template:
            r.error(405, current.ERROR.BAD_METHOD)

        T = current.T
        try:
           import xlwt
        except ImportError:
            r.error(501, T("xlwt not installed, so cannot export as a Spreadsheet"))

        s3db = current.s3db
        db = current.db

        # Get the translate record
        table = s3db.survey_translate
        record = db(table.id == self.record_id).select(table.code,
                                                       table.language,
                                                       limitby=(0, 1)).first()
        if record is None:
            r.error(404, current.ERROR.BAD_RECORD)

        code = record.code
        from s3survey import S3QuestionTypeOptionWidget
        lang_filename = "applications/%s/languages/%s.py" % (r.application,
                                                             code)
        try:
            from gluon.languages import read_dict
            strings = read_dict(lang_filename)
        except IOError:
            strings = dict()

        output = StringIO()

        book = xlwt.Workbook(encoding="utf-8")
        sheet = book.add_sheet(record.language)
        question_list = s3db.survey_getAllQuestionsForTemplate(template_id)
        original = {}
        original[template.name] = True
        if template.description != "":
            original[template.description] = True

        for qstn in question_list:
            original[qstn["name"]] = True
            widget_obj = survey_question_type[qstn["type"]](question_id = qstn["qstn_id"])
            if isinstance(widget_obj, S3QuestionTypeOptionWidget):
                option_list = widget_obj.getList()
                for option in option_list:
                    original[option] = True
        sections = s3db.survey_getAllSectionsForTemplate(template_id)

        for section in sections:
            original[section["name"]] = True
            section_id = section["section_id"]
            layout_rules = s3db.survey_getQstnLayoutRules(template_id, section_id)
            layout_str = str(layout_rules)
            posn = layout_str.find("heading")
            while posn != -1:
                start = posn + 11
                end = layout_str.find("}", start)
                original[layout_str[start:end]] = True
                posn = layout_str.find("heading", end)

        row = 0
        sheet.write(row, 0, u"Original")
        sheet.write(row, 1, u"Translation")
        original_list = original.keys()
        original_list.sort()

        for text in original_list:
            row += 1
            original = s3_unicode(text)
            sheet.write(row, 0, original)
            if (original in strings):
                sheet.write(row, 1, s3_unicode(strings[original]))

        book.save(output)

        from gluon.contenttype import contenttype
        filename = "%s.xls" % code

        headers = current.response.headers
        headers["Content-Type"] = contenttype(".xls")
        headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename

        output.seek(0)
        return output.read()

# =============================================================================
class survey_ExportResponses(S3Method):
    """
        Download all responses in a Spreadsheet
    """

    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.representation != "xls":
            r.error(501, current.error.BAD_FORMAT)

        series_id = self.record_id
        if series_id is None:
            r.error(405, current.error.BAD_METHOD)

        s3db = current.s3db

        T = current.T
        try:
            import xlwt
        except ImportError:
            r.error(501, T("xlwt not installed, so cannot export as a Spreadsheet"))

        section_break = False
        try:
            filename = "%s_All_responses.xls" % r.record.name
        except AttributeError:
            r.error(404, T("Series not found!"))

        output = StringIO()

        book = xlwt.Workbook(encoding="utf-8")
        # Get all questions and write out as a heading
        col = 0
        complete_row = {}
        next_row = 2
        question_list = s3db.survey_getAllQuestionsForSeries(series_id)
        if len(question_list) > 256:
            section_list = s3db.survey_getAllSectionsForSeries(series_id)
            section_break = True
        if section_break:
            sheets = {}
            cols = {}
            for section in section_list:
                sheet_name = section["name"].split(" ")[0]
                if sheet_name not in sheets:
                    sheets[sheet_name] = book.add_sheet(sheet_name)
                    cols[sheet_name] = 0
        else:
            sheet = book.add_sheet(T("Responses", lazy = False))
        for qstn in question_list:
            if section_break:
                sheet_name = qstn["section"].split(" ")[0]
                sheet = sheets[sheet_name]
                col = cols[sheet_name]
            row = 0
            sheet.write(row, col, s3_unicode(qstn["code"]))
            row += 1
            widget_obj = s3db.survey_getWidgetFromQuestion(qstn["qstn_id"])
            sheet.write(row, col, s3_unicode(widget_obj.fullName()))
            # For each question get the response
            all_responses = s3db.survey_getAllAnswersForQuestionInSeries(qstn["qstn_id"],
                                                                         series_id)
            for answer in all_responses:
                value = answer["value"]
                complete_id = answer["complete_id"]
                if complete_id in complete_row:
                    row = complete_row[complete_id]
                else:
                    complete_row[complete_id] = next_row
                    row = next_row
                    next_row += 1
                sheet.write(row, col, s3_unicode(value))
            col += 1
            if section_break:
                cols[sheet_name] += 1
        sheet.panes_frozen = True
        sheet.horz_split_pos = 2

        book.save(output)

        from gluon.contenttype import contenttype

        headers = current.response.headers
        headers["Content-Type"] = contenttype(".xls")
        headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename

        output.seek(0)
        return output.read()

# END =========================================================================
