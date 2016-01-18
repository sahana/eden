# -*- coding: utf-8 -*-

""" Sahana Eden Survey Tool

    @copyright: 2011-2016 (c) Sahana Software Foundation
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

    @todo: PEP8
    @todo: naming conventions!
    @todo: remove unnecessary wrappers
    @todo: docstrings
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
           "survey_LayoutBlocks",
           "survey_MatrixElement",
           "survey_DataMatrix",
           "survey_DataMatrixBuilder",
           "survey_getMatrix",
           "survey_S3AnalysisPriority",
           "survey_question_type",
           "survey_analysis_type",
           "survey_T",
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
from gluon.sqlhtml import *

from ..s3 import *
from s3chart import S3Chart

DEBUG = False
if DEBUG:
    import sys
    print >> sys.stderr, "S3Survey: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

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
        query = table.name.lower().like('%%%s%%' % name.lower())
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
        Returns a table of details of a particular template

        @param template_id: ID corresponding to the template for which
                            the summary is to be built
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
                     Field("name", length=400,
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
        Get questions of a particular question type

        @param question_list: List of questions
        @param qtype: Questions of this type to be returned
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
        Function to update the metadata of a question
        corresponding to the record

        @param record: The record for the question to be updated
        @param qtype: Question Type
        @param metadata: The metadata to be updated with
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
        return {}

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
def survey_getQstnLayoutRules(template_id, section_id, method = 1):
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
                                  set_min = "#survey_series_end_date",
                                  ),
                          s3_date("end_date",
                                  label = T("End Date"),
                                  set_max = "#survey_series_start_date",
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
            Build summary of series corresponding to the record in r
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
            output = {}
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
            Helper function to download a Chart
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
        output = {}
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
        output = {}
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
            Helper function to create/draw Chart
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
            Helper function to show a map with markers on the places
            where assessments are carried out
        """

        import math

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
            output = {}
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
        priority_object = survey_S3AnalysisPriority(range=[-.66, .66],
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
                for i in xrange(len(response_locations)):
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

    current.response.s3.actions = [{"label": str(current.messages.UPDATE),
                                    "_class": "action-btn edit",
                                    "url": URL(c="survey",
                                               f="series",
                                               args=["[id]",
                                                     "summary",
                                                     ],
                                               ),
                                    },
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
        Insert/Update a record in survey_complete
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
        Get the Priority Question for series corresponding to series_id
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
        Build series summary with questions and number of replies for
        each question in the template
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
            Helper function for complete_onaccept
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
            Private function used to save the locations to gis.location
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

    current.response.s3.actions = [{"label": str(current.messages.UPDATE),
                                    "_class": "action-btn edit",
                                    "url": URL(c="survey",
                                               f="series",
                                               args=[r.id,
                                                     "complete",
                                                     "[id]",
                                                     "update",
                                                     ],
                                               ),
                                    },
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
        Build a table to display completed list
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
                                autodelete = True,
                                length = current.MAX_FILENAME_LENGTH,
                                ),
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
        return {}

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
            request = current.request
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
                strings = {}
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
            r.error(415, current.ERROR.BAD_FORMAT)

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
        lang_filename = "applications/%s/languages/%s.py" % (r.application,
                                                             code)
        try:
            from gluon.languages import read_dict
            strings = read_dict(lang_filename)
        except IOError:
            strings = {}

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
            r.error(415, current.error.BAD_FORMAT)

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
            sheet = book.add_sheet(s3_unicode(T("Responses")))
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

# =============================================================================
class survey_LayoutBlocks():
    """
        Class that hold details of the layout blocks.

        This is used when resizing the layout to make the final layout uniform.
    """

    def __init__(self):
        """
            Constructor
        """

        self.startPosn = [0, 0]
        self.endPosn = [0, 0]
        self.contains = []
        self.temp = []
        self.widgetList = []
        self.growToWidth = 0
        self.growToHeight = 0

    # -------------------------------------------------------------------------
    class RowBlocks():
        """
            Class the holds blocks that belong on the same row
        """
        def __init__(self, block):
            self.blocks = [block]
            self.startRow = block.startPosn[0]
            self.maxHeight = block.endPosn[0]
            self.maxWidth = block.endPosn[1]
            self.cnt = 1

        def add(self, block):
            self.blocks.append(block)
            if block.endPosn[0] > self.maxHeight:
                self.maxHeight = block.endPosn[0]
            if block.endPosn[1] > self.maxWidth:
                self.maxWidth = block.endPosn[1]
            self.cnt += 1
        # end of class RowBlocks

    # -------------------------------------------------------------------------
    def growTo (self, width=None, height=None):
        """ @todo: docstring """

        if width != None:
            self.growToWidth = width
        if height != None:
            self.growToHeight = height

    # -------------------------------------------------------------------------
    def growBy(self, width=None, height=None):
        """ @todo: docstring """

        if width != None:
            self.growToWidth = self.endPosn[1] + width
        if height != None:
            self.growToHeight = self.endPosn[0] + height

    # -------------------------------------------------------------------------
    def setPosn(self, start, end):
        """ @todo: docstring """

        if self.startPosn[0] == 0 or \
           start[0] < self.startPosn[0]:
            self.startPosn[0] = start[0]

        if self.startPosn[1] == 0 or \
           start[1] > self.startPosn[1]:
            self.startPosn[1] = start[1]

        if end[0] > self.endPosn[0]:
            self.endPosn[0] = end[0]

        if end[1] > self.endPosn[1]:
            self.endPosn[1] = end[1]

        self.growToWidth = self.endPosn[1]
        self.growToHeight = self.endPosn[0]

    # -------------------------------------------------------------------------
    def slideHorizontally(self, colAdjust):
        """ @todo: docstring """

        self.startPosn[1] += colAdjust
        self.endPosn[1] += colAdjust
        for block in self.contains:
            block.slideHorizontally(colAdjust)

    # -------------------------------------------------------------------------
    def setWidgets(self, widgets):
        """ @todo: docstring """

        rowList = {}
        colList = {}
        for widget in widgets:
            startCol = widget.startPosn[1]
            startRow = widget.startPosn[0]
            if startCol in colList:
                colList[startCol] += 1
            else:
                colList[startCol] = 1
            if startRow in rowList:
                rowList[startRow] += 1
            else:
                rowList[startRow] = 1
        if len(colList) > 1:
            self.action = "columns"
        else:
            self.action = "rows"
        self.widgetList = widgets

    # -------------------------------------------------------------------------
    def widthShortfall(self):
        """ @todo: docstring """

        return self.growToWidth - self.endPosn[1]

    # -------------------------------------------------------------------------
    def heightShortfall(self):
        """ @todo: docstring """

        return self.growToHeight - self.endPosn[0]

    # -------------------------------------------------------------------------
    def addBlock(self, start, end, widgets=[]):
        """ @todo: docstring """

        lb = survey_LayoutBlocks()
        lb.setPosn(start, end)
        lb.setWidgets(widgets)
        length = len(self.contains)
        temp = []
        if length > 0 and self.contains[length - 1].startPosn == start:
            lb.contains.append(self.contains.pop())
        for element in self.temp:
            if element.startPosn[0] < start[0] or element.startPosn[1] < start[1]:
                temp.append(element)
            else:
                lb.contains.append(element)
        self.temp = []
        for element in temp:
            self.temp.append(element)
        if self.temp != []:
            self.temp.append(lb)
        else:
            self.contains.append(lb)

    # -------------------------------------------------------------------------
    def addTempBlock(self, start, end, widgets):
        """ @todo: docstring """

        lb = survey_LayoutBlocks()
        lb.setPosn(start, end)
        lb.setWidgets(widgets)
        self.temp.append(lb)

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ @todo: docstring """

        indent = ""
        data = self.display(indent)
        return data

    # -------------------------------------------------------------------------
    def display(self, indent):
        """ @todo: docstring """

        widgets = ""
        for widget in self.widgetList:
            widgets += "%s " % widget.question.code
        data = "%s%s, %s grow to [%s, %s]- %s\n" %(indent,
                                                   self.startPosn,
                                                   self.endPosn,
                                                   self.growToHeight,
                                                   self.growToWidth,
                                                   widgets
                                                   )
        indent = indent + "  "
        for lb in self.contains:
            data += lb.display(indent)
        return data

    # -------------------------------------------------------------------------
    def align(self):
        """
            Method to align the widgets up with each other.

            This means that blocks that are adjacent to each other will be
            spaced to ensure that they have the same height. And blocks on top
            of each other will have the same width.
        """
        formWidth = self.endPosn[1]
        self.realign(formWidth)

    # -------------------------------------------------------------------------
    def realign(self, formWidth):
        """
            Recursive method to ensure all widgets line up

            @todo: parameter description
        """

        rowList = {}
        # Put all of the blocks into rows
        for block in self.contains:
            startRow = block.startPosn[0]
            endRow = block.endPosn[0]
            # Exact match
            if startRow in rowList:
                rowList[startRow].add(block)
                continue
            # look for an overlap
            else:
                overlap = False
                for storedBlock in rowList.values():
                    if (startRow < storedBlock.startRow \
                        and endRow >= storedBlock.startRow) \
                    or (startRow < storedBlock.maxHeight \
                        and endRow >= storedBlock.maxHeight) \
                    or (startRow > storedBlock.startRow) \
                        and (endRow <= storedBlock.maxHeight):
                        storedBlock.add(block)
                        overlap = True
                        break
                if overlap:
                    continue
            # no overlap
            rowList[startRow] = self.RowBlocks(block)
        # Now set up the grow to sizes for each block
        for row in rowList.values():
            # if their is only one row then
            # it just needs to expand to fill the form width
            if row.cnt == 1:
                row.blocks[0].growTo(formWidth)
            # The amount that each block needs to expand to reach the form width
            # needs to be calculated by sharing the shortfall between each block
            # and if any block needs to grow vertically this needs to be added
            # additionally the start position my need adjusting
            else:
                widthShortfall = formWidth - row.maxWidth
                widthShortfallPart = widthShortfall / row.cnt
                colAdjust = 0
                for block in row.blocks:
                    if widthShortfall > 0:
                        widthShortfall -= widthShortfallPart
                        block.slideHorizontally(colAdjust)
                        block.growBy(widthShortfallPart)
                        colAdjust += widthShortfallPart
                    if block.endPosn[0] < row.maxHeight:
                        block.growTo(height = row.maxHeight)
                colAdjust = 0
                for block in row.blocks:
                    if widthShortfall == 0:
                        break
                    block.growBy()
                    widthShortfall -= 1
                    block.slideHorizontally(colAdjust)
                    colAdjust += 1
                rowCnt = len(row.blocks)
                if rowCnt > 1:
                    rowCntList = {}
                    for block in row.blocks:
                        rowCntList[block.startPosn[0]] = True
                    if len(rowCntList) == 1:
                        formWidth = self.growToWidth
        # The growto parameters have been set. Now grow any widgets
        # @todo: add modulo tests for blkCnt to cater for uneven results
        blkCnt = len(self.contains)
        for block in self.contains:
            if block.widgetList == []:
                block.realign(self.growToWidth)
            else:
                self.alignBlock(block, blkCnt)

    # -------------------------------------------------------------------------
    def alignBlock(self, block, blkCnt):
        """ @todo: docstring """

        if block.action == "rows":
            widthShortfall = block.widthShortfall()
            self.alignRow(block, widthShortfall)
        else:
            heightShortfall = block.heightShortfall()
            widthShortfall = block.widthShortfall()
            self.alignCol(block, heightShortfall, widthShortfall)

    # -------------------------------------------------------------------------
    def alignRow(self, block, widthShortfall):
        """
            Method to align the widgets laid out in a single row.

            The horizontal spacing will be fixed. Identify all widgets
            that can grow horizontally and let them do so. If their are
            multiple widgets that can grow then they will all grow by the
            same amount.

            Any space that is left over will be added to a margin between
            the widgets

            @todo: parameter description
        """

        canGrowCount = 0
        for widget in block.widgetList:
            if widget.canGrowHorizontal():
                canGrowCount += 1
        if canGrowCount > 0:
            growBy = widthShortfall / canGrowCount
            if growBy > 0:
                for widget in block.widgetList:
                    if widget.canGrowHorizontal():
                        widget.growHorizontal(growBy)
                        widthShortfall -= growBy
        # Add any unallocated space as margins between the widgets
        if widthShortfall > 0:
            marginGrow = widthShortfall / len(block.widgetList)
            if marginGrow > 0:
                for widget in block.widgetList:
                    widget.addToHorizontalMargin(marginGrow)
                    widthShortfall -= marginGrow
        if widthShortfall > 0:
            for widget in block.widgetList:
                widget.addToHorizontalMargin(1)
                widthShortfall -= 1
                if widthShortfall == 0:
                    break
        # Now sort out any vertical shortfall
        for widget in block.widgetList:
            widgetHeight = block.startPosn[0] + widget.getMatrixSize()[0]
            heightShortfall = block.growToHeight - widgetHeight
            if heightShortfall > 0:
                if widget.canGrowVertical():
                    widget.growVertical(heightShortfall)
                else:
                    widget.addToVerticalMargin(heightShortfall)

    # -------------------------------------------------------------------------
    def alignCol(self, block, heightShortfall, widthShortfall):
        """
            Method to align the widgets laid out different rows

            @todo: parameter description
        """

        # Stretch the columns to fill the maximum width
        for widget in block.widgetList:
            widgetWidth = block.startPosn[1] + widget.getMatrixSize()[1]
            widthShortfall = block.growToWidth - widgetWidth
            # Now grow the columns to align evenly
            if widthShortfall == 0:
                continue
            if widget.canGrowHorizontal():
                widget.growHorizontal(widthShortfall)
            else:
                widget.addToHorizontalMargin(widthShortfall)
        # Now grow the rows to align evenly
        if heightShortfall == 0:
            return
        # See if the widgets can grow
        canGrowCount = 0
        for widget in block.widgetList:
            if widget.canGrowVertical():
                canGrowCount += 1
        if canGrowCount > 0:
            growBy = heightShortfall / canGrowCount
            if growBy > 0:
                for widget in block.widgetList:
                    if widget.canGrowVertical():
                        widget.growVertical(growBy)
                        heightShortfall -= growBy
        # Add any unallocated space as margins between the widgets
        if heightShortfall > 0:
            marginGrow = heightShortfall / len(block.widgetList)
            if marginGrow > 0:
                for widget in block.widgetList:
                    widget.addToVerticalMargin(marginGrow)
                    heightShortfall -= marginGrow
        if heightShortfall > 0:
            for widget in block.widgetList:
                widget.addToVerticalMargin(1)
                heightShortfall -= 1
                if heightShortfall == 0:
                    break

# =============================================================================
class survey_DataMatrix():
    """
        Class that sets the data up ready for export to a specific format,
        such as a spreadsheet or a PDF document.

        It holds the data in a matrix with each element holding details on:
         * A unique position
         * The actual text to be displayed
         * Any style to be applied to the data
    """

    def __init__(self):
        """
            Constructor
        """

        self.matrix = {}
        self.lastRow = 0
        self.lastCol = 0
        self.fixedWidthRepr = False
        self.fixedWidthReprLen = 1

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ @todo: docstring """

        repr = ""
        for row in xrange(self.lastRow+1):
            for col in xrange(self.lastCol+1):
                posn = survey_MatrixElement.getPosn(row, col)
                if posn in self.matrix:
                    cell = self.matrix[posn]
                    data = str(cell)
                else:
                    cell = None
                    data = "-"
                if self.fixedWidthRepr:
                    xposn = 0
                    if cell != None:
                        if cell.joinedWith != None:
                            parentPosn = cell.joinedWith
                            (prow, pcol) = parentPosn.split(",")
                            xposn = col - int(pcol)
                            data = str(self.matrix[parentPosn])
                        if xposn >= len(data):
                            data = "*"
                    if len(data) > self.fixedWidthReprLen:
                        data = data[xposn:xposn+self.fixedWidthReprLen]
                    else:
                        data = data + " " * (self.fixedWidthReprLen - len(data))
                repr += data
            repr += "\n"
        return repr

    # -------------------------------------------------------------------------
    def addCell(self, row, col, data, style, horizontal=0, vertical=0):
        """ @todo: docstring """

        cell = survey_MatrixElement(row, col, data, style)
        if horizontal != 0 or vertical != 0:
            cell.merge(horizontal, vertical)
        try:
            self.addElement(cell)
        except Exception as msg:
            current.log.error(msg)
        return (row + 1 + vertical,
                col + 1 + horizontal)

    # -------------------------------------------------------------------------
    def addElement(self, element):
        """
            Add an element to the matrix, checking that the position is unique.

            @todo: parameter description
        """

        posn = element.posn()
        if posn in self.matrix:
            msg = "Attempting to add data %s at posn %s. This is already taken with data %s" % \
                        (element, posn, self.matrix[posn])
            raise Exception(msg)
        self.matrix[posn] = element
        element.parents.append(self)
        if element.merged():
            self.joinElements(element)
        if element.row + element.mergeV > self.lastRow:
            self.lastRow = element.row + element.mergeV
        if element.col + element.mergeH > self.lastCol:
            self.lastCol = element.col + element.mergeH

    # -------------------------------------------------------------------------
    def joinedElementStyles(self, rootElement):
        """
            Return a list of all the styles used by all the elements joined
            to the root element

            @todo: parameter description
        """

        styleList = []
        row = rootElement.row
        col = rootElement.col
        for v in xrange(rootElement.mergeV + 1):
            for h in xrange(rootElement.mergeH + 1):
                newPosn = "%s,%s" % (row + v, col + h)
                styleList += self.matrix[newPosn].styleList
        return styleList

    # -------------------------------------------------------------------------
    def joinElements(self, rootElement):
        """
            This will set the joinedWith property to the posn of rootElement
            for all the elements that rootElement joins with to make a single
            large merged element.

            @todo: parameter description
        """

        row = rootElement.row
        col = rootElement.col
        posn = rootElement.posn()
        for v in xrange(rootElement.mergeV + 1):
            for h in xrange(rootElement.mergeH + 1):
                newPosn = "%s,%s" % (row + v, col + h)
                if newPosn == posn:
                    continue
                if newPosn in self.matrix:
                    if self.matrix[newPosn].joinedWith == posn:
                        continue
                    msg = "Attempting to merge element at posn %s. The following data will be lost %s" % \
                                (newPosn, self.matrix[newPosn])
                    self.matrix[newPosn].joinedWith = posn
                else:
                    childElement = survey_MatrixElement(row, col, "", [])
                    childElement.joinedWith = posn
                    self.matrix[newPosn] = childElement

    # -------------------------------------------------------------------------
    def boxRange(self, startrow, startcol, endrow, endcol, width=1):
        """
            Function to add a bounding box around the elements contained by
            the elements (startrow, startcol) and (endrow, endcol)

            This uses standard style names:
            boxL, boxB, boxR, boxT
            for Left, Bottom, Right and Top borders respectively

            @todo: parameter description
        """

        for r in xrange(startrow, endrow):
            posn = "%s,%s" % (r, startcol)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxL%s"%width)
            else:
                self.addElement(survey_MatrixElement(r, startcol, "", "boxL%s"%width))
            posn = "%s,%s" % (r, endcol)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxR%s"%width)
            else:
                self.addElement(survey_MatrixElement(r, endcol, "", "boxR%s"%width))

        for c in xrange(startcol, endcol + 1):
            posn = "%s,%s" % (startrow, c)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxT%s"%width)
            else:
                self.addElement(survey_MatrixElement(startrow, c, "", "boxT%s"%width))
            posn = "%s,%s" % (endrow - 1, c)
            if posn in self.matrix:
                self.matrix[posn].styleList.append("boxB%s"%width)
            else:
                self.addElement(survey_MatrixElement(endrow - 1, c, "", "boxB%s"%width))

# =============================================================================
class survey_MatrixElement():
    """
        Class that holds the details of a single element in the matrix

        * posn - row & col
        * text - the actual data that will be displayed at the given position
        * style - a list of styles that will be applied to this location
    """

    def __init__(self, row, col, data, style):
        """
            Constructor

            @todo: parameter description
        """

        self.row = row
        self.col = col
        self.text = data
        self.mergeH = 0
        self.mergeV = 0
        self.joinedWith = None
        self.parents = []
        if isinstance(style, list):
            self.styleList = style
        else:
            self.styleList = [style]

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ @todo: docstring """

        return self.text

    # -------------------------------------------------------------------------
    def merge(self, horizontal=0, vertical=0):
        """ @todo: docstring """

        self.mergeH = horizontal
        self.mergeV = vertical
        for parent in self.parents:
            parent.joinElements(self)

    # -------------------------------------------------------------------------
    @staticmethod
    def getPosn(row, col):
        """
            Standard representation of the position

            @todo: parameter description
        """

        return "%s,%s" % (row, col)

    # -------------------------------------------------------------------------
    def posn(self):
        """
            Standard representation of the position
        """

        return self.getPosn(self.row, self.col)

    # -------------------------------------------------------------------------
    def nextX(self):
        """ @todo: docstring """

        return self.row + self.mergeH + 1

    # -------------------------------------------------------------------------
    def nextY(self):
        """ @todo: docstring """

        return self.col + self.mergeV + 1

    # -------------------------------------------------------------------------
    def merged(self):
        """ @todo: docstring """

        if self.mergeH > 0 or self.mergeV > 0:
            return True
        return False

    # -------------------------------------------------------------------------
    def joined(self):
        """ @todo: docstring """

        if self.joinedWith == None:
            return False
        else:
            return True

# =============================================================================
class survey_DataMatrixBuilder():
    """ @todo: docstring """

    def __init__(self,
                 primaryMatrix,
                 layout=None,
                 widgetList = [],
                 secondaryMatrix=None,
                 langDict = None,
                 addMethod=None):
        """
            Constructor

            @todo: parameter description
        """

        self.matrix = primaryMatrix
        self.layout = layout
        self.widgetList = widgetList
        self.widgetsInList = []
        self.answerMatrix = secondaryMatrix
        self.langDict = langDict
        if addMethod == None:
            self.addMethod = self.addData
        else:
            self.addMethod = addMethod
        self.labelLeft = None
        self.boxOpen = False
        self.postponeLayoutUpdate = False

    # -------------------------------------------------------------------------
    def processRule(self, rules, row, col, matrix):
        """ @todo: docstring """

        startcol = col
        startrow = row
        endcol = col
        endrow = row
        action = "rows"
        self.widgetsInList = []
        for element in rules:
            row = endrow
            col = startcol
            self.nextrow = row
            self.nextcol = col
            if isinstance(element, list):
                (endrow, endcol) = self.processList(element, row, col, matrix, action)
            elif isinstance(element, dict):
                (endrow, endcol) = self.processDict(element, rules, row, col, matrix, action)
            if self.layout != None:
                if self.widgetsInList == []:
                    self.layout.addBlock((row, col), (endrow, endcol))
                else:
                    self.layout.addTempBlock((row, col), (endrow, endcol), self.widgetsInList)
                    self.widgetsInList = []
        return (endrow, endcol)

    # -------------------------------------------------------------------------
    def processList(self, rules, row, col, matrix, action="rows"):
        """ @todo: docstring """

        startcol = col
        startrow = row
        endcol = col
        endrow = row
        for element in rules:
            if action == "rows":
                row = startrow
                col = endcol
            elif action == "columns":
                row = endrow
                col = startcol
            # If the rule is a list then step through each element
            if isinstance(element, list):
                (endrow, endcol) = self.processList(element, row, col, matrix, action)
            elif isinstance(element, dict):
                (endrow, endcol) = self.processDict(element, rules, row, col, matrix, action)
            else:
                (endrow, endcol) = self.addMethod(self, element, row, col)
            if endrow > self.nextrow:
                self.nextrow = endrow
            if endcol > self.nextcol:
                self.nextcol = endcol
        self.addToLayout(startrow, startcol)
        return (self.nextrow, self.nextcol)

    # -------------------------------------------------------------------------
    def processDict(self, rules, parent, row, col, matrix, action="rows"):
        """ @todo: docstring """

        startcol = col
        startrow = row
        endcol = col
        endrow = row
        if "boxOpen" in rules:
            return self.processBox(rules, row, col, matrix, action)
        if "heading" in rules:
            text = rules["heading"]
            if len(parent) == 1:
                width = min(len(text), matrix.lastCol) + 1
                height = 1
                styleName = "styleSectionHeading"
            else:
                width = 11
                height = len(text) / (2 * width) + 1
                styleName = "styleSubHeader"
            cell = survey_MatrixElement(row, col, text, style = styleName)
            cell.merge(horizontal = width - 1, vertical = height - 1)
            try:
                matrix.addElement(cell)
            except Exception as msg:
                current.log.error(msg)
                return (row, col)
            endrow = row + height
            endcol = col + width
            if "hint" in rules:
                text = rules["hint"]
                cell = survey_MatrixElement(endrow, startcol, text,
                                            style="styleHint")
                height = int(((len(text) / (2 * width)) * 0.75) + 0.5) + 1
                cell.merge(horizontal = width - 1, vertical = height - 1)
                try:
                    matrix.addElement(cell)
                except Exception as msg:
                    current.log.error(msg)
                    return (row, col)
                endrow = endrow + height
        if "labelLeft" in rules:
            self.labelLeft = rules["labelLeft"]
        if "columns" in rules:
            value = rules["columns"]
            maxrow = startrow
            for rules in value:
                row = startrow
                self.nextrow = startrow
                col = endcol
                if isinstance(rules, list):
                    (endrow, endcol) = self.processList(rules, row, col, matrix, "columns")
                elif isinstance(rules, dict):
                    (endrow, endcol) = self.processDict(rules, value, row, col, matrix, "columns")
                if endrow > maxrow:
                    maxrow = endrow
                if endcol > self.nextcol:
                    self.nextcol = endcol
            self.nextrow = maxrow
            endrow = self.nextrow
            endcol = self.nextcol
        return (endrow, endcol)

    # -------------------------------------------------------------------------
    def processBox(self, rules, row, col, matrix, action="rows"):
        """ @todo: docstring """

        startcol = col
        startrow = row
        endcol = col
        endrow = row
        headingrow = row
        self.addToLayout(startrow, startcol, andThenPostpone = True)
        if "heading" in rules:
            row += 1
        if "data" in rules:
            self.boxOpen = True
            value = rules["data"]
            (endrow, endcol) = self.processList(value, row, col, matrix, action)
            self.boxOpen = False
        if "heading" in rules:
            value = rules["heading"]
            (row, endcol) = self.addLabel(value, headingrow, col, endcol - col, 1)
        self.matrix.boxRange(startrow, startcol, endrow, endcol - 1)
        self.addToLayout(startrow, startcol, endPostpone = True)
        return (endrow, endcol)

    # -------------------------------------------------------------------------
    def addToLayout(self, startrow, startcol, andThenPostpone = None, endPostpone = None):
        """ @todo: docstring """

        if endPostpone != None:
            self.postponeLayoutUpdate = not endPostpone
        if not self.postponeLayoutUpdate \
        and self.layout != None \
        and (startrow != self.nextrow or startcol != self.nextcol):
            if self.widgetsInList != []:
                self.layout.addTempBlock((startrow, startcol), (self.nextrow, self.nextcol), self.widgetsInList)
                self.widgetsInList = []
        if andThenPostpone != None:
            self.postponeLayoutUpdate = andThenPostpone

    # -------------------------------------------------------------------------
    def addArea(self, element, row, col):
        """ @todo: docstring """

        try:
            widgetObj = self.widgetList[element]
        except:
            _debug("Unable to find element %s in the template" % element)
            return self.matrix.addCell(row, col, "", [])
        widgetObj.startPosn = (col, row)
        if self.labelLeft:
            widgetObj.labelLeft = (self.labelLeft == "True")
            self.labelLeft = None
        self.widgetsInList.append(widgetObj)
        (vert, horiz) = widgetObj.getMatrixSize()
        return self.matrix.addCell(row,
                                   col,
                                   element,
                                   [],
                                   horizontal=horiz - 1,
                                   vertical=vert - 1,
                                  )

    # -------------------------------------------------------------------------
    def addLabel(self, label, row, col, width=11,
                 height=None,
                 style="styleSubHeader"):
        """ @todo: docstring """

        cell = survey_MatrixElement(row, col, label, style=style)
        if height == None:
            height = len(label) / (2 * width) + 1
        cell.merge(horizontal=width - 1, vertical=height - 1)
        try:
            self.matrix.addElement(cell)
        except Exception as msg:
            current.log.error(msg)
            return (row, col)
        endrow = row + height
        endcol = col + width
        return (endrow, endcol)

    # -------------------------------------------------------------------------
    def addData(self, element, row, col):
        """ @todo: docstring """

        try:
            widgetObj = self.widgetList[element]
        except:
            _debug("Unable to find element %s in the template" % element)
            return self.matrix.addCell(row, col, "", [])
        widgetObj.startPosn = (col, row)
        self.widgetsInList.append(widgetObj)
        if self.labelLeft:
            widgetObj.labelLeft = (self.labelLeft == "True")
            self.labelLeft = None
        try:
            (endrow, endcol) = widgetObj.writeToMatrix(self.matrix,
                                                       row,
                                                       col,
                                                       answerMatrix=self.answerMatrix,
                                                       langDict = self.langDict
                                                      )
        except Exception as msg:
            current.log.error(msg)
            return (row, col)
        #if question["type"] == "Grid":
        if self.boxOpen == False:
            self.matrix.boxRange(row, col, endrow, endcol - 1)
        return (endrow, endcol)

# =============================================================================
def survey_getMatrix(title,
                     logo,
                     layout,
                     widgetList,
                     secondaryMatrix,
                     langDict,
                     showSectionLabels=True,
                     layoutBlocks=None):
    """
        @todo: docstring
    """

    matrix = survey_DataMatrix()
    if secondaryMatrix:
        secondaryMatrix = survey_DataMatrix()
    else:
        secondaryMatrix = None
    matrix.fixedWidthRepr = True
    if layoutBlocks == None:
        addMethod = survey_DataMatrixBuilder.addData
    else:
        addMethod = survey_DataMatrixBuilder.addArea
    builder = survey_DataMatrixBuilder(matrix,
                                       layoutBlocks,
                                       widgetList,
                                       secondaryMatrix = secondaryMatrix,
                                       langDict = langDict,
                                       addMethod=addMethod
                                       )
    row = 2
    for (section, rules) in layout:
        col = 0
        if showSectionLabels:
            row += 1
            (row, nextCol) = matrix.addCell(row,
                                            col,
                                            section,
                                            ["styleHeader"],
                                            len(section)
                                            )
        (row, col) = builder.processRule(rules, row, col, matrix)
    row = 0
    col = 0
    logoWidth = 0
    if logo != None:
        logoWidth = 6
        (nextRow, col) = matrix.addCell(row, col, "", [], logoWidth - 1, 1)
    titleWidth = max(len(title), matrix.lastCol - logoWidth)
    (row, col) = matrix.addCell(row, col, title, ["styleTitle"], titleWidth, 1)
    if layoutBlocks != None:
        maxCol = col
        for block in layoutBlocks.contains:
            if block.endPosn[1] > maxCol:
                maxCol = block.endPosn[1]
        layoutBlocks.setPosn((0, 0), (row, maxCol))
    matrix.boxRange(0, 0, matrix.lastRow + 1, matrix.lastCol, 2)
    if secondaryMatrix:
        return (matrix, secondaryMatrix)
    else:
        return matrix

# =============================================================================
# Question Types
# @todo: get rid of the wrapper functions!
#
def survey_stringType(question_id = None):
    return S3QuestionTypeStringWidget(question_id)

def survey_textType(question_id = None):
    return S3QuestionTypeTextWidget(question_id)

def survey_numericType(question_id = None):
    return S3QuestionTypeNumericWidget(question_id)

def survey_dateType(question_id = None):
    return S3QuestionTypeDateWidget(question_id)

def survey_timeType(question_id = None):
    return S3QuestionTypeTimeWidget(question_id)

def survey_optionType(question_id = None):
    return S3QuestionTypeOptionWidget(question_id)

def survey_ynType(question_id = None):
    return S3QuestionTypeOptionYNWidget(question_id)

def survey_yndType(question_id = None):
    return S3QuestionTypeOptionYNDWidget(question_id)

def survey_optionOtherType(question_id = None):
    return S3QuestionTypeOptionOtherWidget(question_id)

def survey_multiOptionType(question_id = None):
    return S3QuestionTypeMultiOptionWidget(question_id)

def survey_locationType(question_id = None):
    return S3QuestionTypeLocationWidget(question_id)

def survey_linkType(question_id = None):
    return S3QuestionTypeLinkWidget(question_id)

def survey_ratingType(question_id = None):
    pass

def survey_gridType(question_id = None):
    return S3QuestionTypeGridWidget(question_id)

def survey_gridChildType(question_id = None):
    return S3QuestionTypeGridChildWidget(question_id)

survey_question_type = {"String": survey_stringType,
                        "Text": survey_textType,
                        "Numeric": survey_numericType,
                        "Date": survey_dateType,
                        "Time": survey_timeType,
                        "Option": survey_optionType,
                        "YesNo": survey_ynType,
                        "YesNoDontKnow": survey_yndType,
                        "OptionOther": survey_optionOtherType,
                        "MultiOption" : survey_multiOptionType,
                        "Location": survey_locationType,
                        "Link" : survey_linkType,
                        #"Rating": survey_ratingType,
                        "Grid" : survey_gridType,
                        "GridChild" : survey_gridChildType,
                        }

# =============================================================================
class S3QuestionTypeAbstractWidget(FormWidget):
    """
        Abstract Question Type widget

        A QuestionTypeWidget can have three basic states:

        The first is as a descriptor for the type of question.
        In this state it will hold the information about what this type of
        question may look like.

        The second state is when it is associated with an actual question
        on the database. Then it will additionally hold information about what
        this actual question looks like.

        The third state is when the widget of an actual question is
        associated with a single answer to that question. If that happens then
        the self.question record from the database is extended to hold
        the actual answer and the complete_id of that answer.

        For example: A numeric question type has a metadata value of "Format"
        this can be used to describe how the data could be formatted to
        represent a number. When this question type is associated with an
        actual numeric question then the metadata might be "Format" : n, which
        would mean that it is an integer value.

        The general instance variables:

        @ivar metalist: A list of all the valid metadata descriptors. This would
                        be used by a UI when designing a question
        @ivar attr: Any HTML/CSS attributes passed in by the call to display
        @ivar webwidget: The web2py widget that should be used to display the
                         question type
        @ivar typeDescription: The description of the type when it is displayed
                               on the screen such as in reports

        The instance variables when the widget is associated with a question:

        @ivar id: The id of the question from the survey_question table
        @ivar question: The question record from the database.
                        Note this variable can be extended to include the
                        answer taken from the complete_id, allowing the
                        question to hold a single answer. This is needed when
                        updating responses.
        @ivar qstn_metadata: The actual metadata for this question taken from
                             the survey_question_metadata table and then
                             stored as a descriptor value pair
        @ivar field: The field object from metadata table, which can be used
                     by the widget to add additional rules (such as a requires)
                     before setting up the UI when inputing data
    """

    def __init__(self,
                 question_id,
                 ):

        self.ANSWER_VALID = 0
        self.ANSWER_MISSING = 1
        self.ANSWER_PARTLY_VALID = 2
        self.ANSWER_INVALID = 3

        T = current.T
        s3db = current.s3db
        # The various database tables that the widget may want access to
        self.qtable = s3db.survey_question
        self.mtable = s3db.survey_question_metadata
        self.qltable = s3db.survey_question_list
        self.ctable = s3db.survey_complete
        self.atable = s3db.survey_answer
        # the general instance variables
        self.metalist = ["Help message"]
        self.attr = {}
        self.webwidget = StringWidget
        self.typeDescription = None
        self.startPosn = (0, 0)
        self.xlsWidgetSize = (6, 0)
        self.xlsMargin = [0, 0]
        self.langDict = {}
        self.label = True
        self.labelLeft = True
        # The instance variables when the widget is associated with a question
        self.id = question_id
        self.question = None
        self.qstn_metadata = {}
        # Initialise the metadata from the question_id
        self._store_metadata()
        self.field = self.mtable.value

        try:
            from xlwt.Utils import rowcol_to_cell
        except:
            current.log.error("WARNING: S3Survey: xlwt module needed for XLS export")
        else:
            self.rowcol_to_cell = rowcol_to_cell

    # -------------------------------------------------------------------------
    def _store_metadata(self, qstn_id=None, update=False):
        """
            This will store the question id in self.id,
            the question data in self.question, and
            the metadata for this specific question in self.qstn_metadata

            It will only get the data from the db if it hasn't already been
            retrieved, or if the update flag is True
        """
        if qstn_id != None:
            if self.id != qstn_id:
                self.id = qstn_id
                # The id has changed so force an update
                update = True
        if self.id == None:
            self.question = None
            self.qstn_metadata = {}
            return
        if self.question == None or update:
            db = current.db
            s3 = current.response.s3
            # Get the question from the database
            query = (self.qtable.id == self.id)
            self.question = db(query).select(limitby=(0, 1)).first()
            if self.question == None:
                raise Exception("no question with id %s in database" % self.id)
            # Get the metadata from the database and store in qstn_metadata
            self.question.name = s3.survey_qstn_name_represent(self.question.name)
            query = (self.mtable.question_id == self.id)
            self.rows = db(query).select()
            for row in self.rows:
                # Remove any double quotes from around the data before storing
                self.qstn_metadata[row.descriptor] = row.value.strip('"')

    # -------------------------------------------------------------------------
    def get(self, value, default=None):
        """
            This will return a single metadata value held by the widget
        """
        if value in self.qstn_metadata:
            return self.qstn_metadata[value]
        else:
            return default

    # -------------------------------------------------------------------------
    def set(self, value, data):
        """
            This will store a single metadata value
        """
        self.qstn_metadata[value] = data


    # -------------------------------------------------------------------------
    def getAnswer(self):
        """
            Return the value of the answer for this question
        """
        if "answer" in self.question:
            answer = self.question.answer
        else:
            answer = ""
        return answer

    # -------------------------------------------------------------------------
    def repr(self, value=None):
        """
            function to format the answer, which can be passed in
        """
        if value == None:
            value = self.getAnswer()
        return value

    # -------------------------------------------------------------------------
    def loadAnswer(self, complete_id, question_id, forceDB=False):
        """
            This will return a value held by the widget
            The value can be held in different locations
            1) In the widget itself:
            2) On the database: table.survey_complete
        """
        value = None
        self._store_metadata(question_id)
        if "answer" in self.question and \
           self.question.complete_id == complete_id and \
           forceDB == False:
            answer = self.question.answer
        else:
            query = (self.atable.complete_id == complete_id) & \
                    (self.atable.question_id == question_id)
            row = current.db(query).select(limitby=(0, 1)).first()
            if row != None:
                value = row.value
                self.question["answer"] = value
            self.question["complete_id"] = complete_id
        return value

    # -------------------------------------------------------------------------
    def initDisplay(self, **attr):
        """
            This method set's up the variables that will be used by all
            display methods of fields for the question type.
            It uses the metadata to define the look of the field
        """
        if "question_id" in attr:
            self.id = attr["question_id"]
        if self.id == None:
            raise Exception("Need to specify the question_id for this QuestionType")
        qstn_id = self.id
        self._store_metadata(qstn_id)
        attr["_name"] = self.question.code
        self.attr = attr

    # -------------------------------------------------------------------------
    def display(self, **attr):
        """
            This displays the widget on a web form. It uses the layout
            function to control how the widget is displayed
        """
        self.initDisplay(**attr)
        value = self.getAnswer()
        input = self.webwidget.widget(self.field, value, **self.attr)
        return self.layout(self.question.name, input, **attr)

    # -------------------------------------------------------------------------
    def fullName(self):
        if "parentCode" in self.question:
            db = current.db
            query = db(self.qtable.code == self.question.parentCode)
            record = query.select(self.qtable.id,
                                  self.qtable.name,
                                  limitby=(0, 1)).first()
            if record != None:
                parentWidget = survey_question_type["Grid"](record.id)
                subHeading = parentWidget.getHeading(self.question.parentNumber)
                return "%s (%s)" % (self.question.name,
                                    subHeading)
        return self.question.name

    # -------------------------------------------------------------------------
    def layout(self, label, widget, **attr):
        """
            This lays the label widget that is passed in on the screen.

            Currently it has a single default layout mechanism but in the
            future it will be possible to add more which will be controlled
            vis the attr passed into display and stored in self.attr
        """
        if "display" in attr:
            display = attr["display"]
        else:
            display = "Default"
        if display == "Default":
            elements = []
            elements.append(TR(TH(label), TD(widget),
                               _class="survey_question"))
            return TAG[""](elements)
        elif display == "Control Only":
            return TD(widget)

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """
        return value

    # -------------------------------------------------------------------------
    def type_represent(self):
        """
            Display the type in a DIV for displaying on the screen
        """
        return DIV(self.typeDescription, _class="surveyWidgetType")

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid
        """
        return "string"

    # -------------------------------------------------------------------------
    def _Tquestion(self, langDict):
        """
            Function to translate the question using the dictionary passed in
        """
        return survey_T(self.question["name"], langDict)

    # -------------------------------------------------------------------------
    def getLabelSize(self, maxWidth = 20):
        """
            Function to return the size of the label, in terms of merged
            MatrixElements
        """
        labelSize = (0, 0)
        if self.label:
            labelWidth = maxWidth/2
            if not self.labelLeft:
                labelWidth = self.xlsWidgetSize[0] + 1
            _TQstn = self._Tquestion(self.langDict)
            labelSize = (labelWidth, len(_TQstn)/(4 * labelWidth / 3) + 1)
        return labelSize

    # -------------------------------------------------------------------------
    def getWidgetSize(self, maxWidth = 20):
        """
            function to return the size of the input control, in terms of merged
            MatrixElements
        """
        return (self.xlsWidgetSize[0] + 1, self.xlsWidgetSize[1] + 1)

    # -------------------------------------------------------------------------
    def getMatrixSize(self):
        """
            function to return the size of the widget
        """
        labelSize = self.getLabelSize()
        widgetSize = self.getWidgetSize()
        if self.labelLeft:
            return (max(labelSize[1], widgetSize[1]) + self.xlsMargin[1],
                    labelSize[0] + widgetSize[0] + self.xlsMargin[0])
        else:
            return (labelSize[1] + widgetSize[1] + self.xlsMargin[1],
                    max(labelSize[0], widgetSize[0]) + self.xlsMargin[0])

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return False

    # -------------------------------------------------------------------------
    def canGrowVertical(self):
        return False

    # -------------------------------------------------------------------------
    def growHorizontal(self, amount):
        if self.canGrowHorizontal():
            self.xlsWidgetSize[0] += amount

    # -------------------------------------------------------------------------
    def growVertical(self, amount):
        if self.canGrowHorizontal():
            self.xlsWidgetSize[1] += amount

    # -------------------------------------------------------------------------
    def addToHorizontalMargin(self, amount):
        self.xlsMargin[0] += amount

    # -------------------------------------------------------------------------
    def addToVerticalMargin(self, amount):
        self.xlsMargin[1] += amount

    # -------------------------------------------------------------------------
    def addPaddingAroundWidget(self, matrix, startrow, startcol,
                               lWidth, lHeight, wWidth, wHeight):

        if self.labelLeft:
            # Add padding below the input boxes
            if lHeight > wHeight:
                cellPadding = survey_MatrixElement(startrow + wHeight,
                                                   startcol + lWidth, "",
                                                   style="styleText")
                cellPadding.merge(wWidth - 1, lHeight - wHeight - 1)
                matrix.addElement(cellPadding)

            # Add padding below the label
            if lHeight < wHeight:
                cellPadding = survey_MatrixElement(startrow + lHeight,
                                                   startcol, "",
                                                   style="styleText")
                cellPadding.merge(lWidth - 1, wHeight - lHeight - 1)
                matrix.addElement(cellPadding)
                height = wHeight + 1
        else:
            # Add padding to make the widget the same width as the label
            if lWidth > wWidth:
                cellPadding = survey_MatrixElement(startrow + lHeight,
                                                   startcol + wWidth, "",
                                                   style="styleText")
                cellPadding.merge(lWidth - wWidth - 1, lHeight - 1)
                matrix.addElement(cellPadding)
            # Add padding to make the label the same width as the widget
            if lWidth < wWidth:
                cellPadding = survey_MatrixElement(startrow,
                                                   startcol + lWidth, "",
                                                   style="styleText")
                cellPadding.merge(wWidth - lWidth - 1, wHeight - 1)
                matrix.addElement(cellPadding)

    # -------------------------------------------------------------------------
    def addPaddingToCell(self,
                         matrix,
                         startrow,
                         startcol,
                         endrow,
                         endcol,
                         ):
        # Add widget padding
        if self.xlsMargin[0] > 0:
            cellPadding = survey_MatrixElement(startrow,
                                               endcol, "",
                                               style="styleText")
            cellPadding.merge(self.xlsMargin[0] - 1,
                              endrow - startrow - 1)
            matrix.addElement(cellPadding)
        if self.xlsMargin[1] > 0:
            cellPadding = survey_MatrixElement(endrow,
                                               startcol, "",
                                               style="styleText")
            cellPadding.merge(endcol - startcol + self.xlsMargin[0] - 1,
                              self.xlsMargin[1] - 1)
            matrix.addElement(cellPadding)

    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict={},
                      answerMatrix=None
                      ):
        """
            Function to write out basic details to the matrix object
        """
        self._store_metadata()
        startrow = row
        startcol = col
        mergeLH = 0
        mergeLV = 0
        height = 0
        width = 0
        if self.label:
            _TQstn = self._Tquestion(langDict)
            cell = survey_MatrixElement(row,
                                        col,
                                        _TQstn,
                                        style="styleSubHeader")
            (width, height) = self.getLabelSize()
            mergeLH = width - 1
            mergeLV = height - 1
            cell.merge(mergeLH, mergeLV)
            matrix.addElement(cell)
            if self.labelLeft:
                col += 1 + mergeLH
            else:
                row += 1 + mergeLV
        cell = survey_MatrixElement(row, col, "", style="styleInput")
        mergeWH = self.xlsWidgetSize[0]
        mergeWV = self.xlsWidgetSize[1]
        cell.merge(mergeWH, mergeWV)
        matrix.addElement(cell)
        if self.labelLeft:
            height = max(height, mergeWV + 1)
            width += mergeWH + 1
        else:
            height += mergeWV + 1
            width = max(width, mergeWH + 1)
        self.addPaddingAroundWidget(matrix, startrow, startcol, mergeLH+1, mergeLV+1, mergeWH+1, mergeWV+1)
        # Add widget padding
        self.addPaddingToCell(matrix, startrow, startcol, startrow + height, startcol + width)
        height += self.xlsMargin[1]
        width += self.xlsMargin[0]
        # Add details to the answerMatrix (if required)
        if answerMatrix != None:
            answerRow = answerMatrix.lastRow+1
            cell = survey_MatrixElement(answerRow, 0, self.question["code"],
                                        style="styleSubHeader")
            answerMatrix.addElement(cell)
            cell = survey_MatrixElement(answerRow, 3,
                                        self.rowcol_to_cell(row, col),
                                        style="styleText")
            answerMatrix.addElement(cell)
        endcol = startcol+width
        endrow = startrow+height
        if DEBUG:
            # Only for debugging purposes
            self.verifyCoords(endrow, endcol)
        return (endrow, endcol)
        #if self.labelLeft:
        #    return (row+self.xlsMargin[1]+height, col+self.xlsMargin[0]+mergeWH)
        #else:
        #    return (row+self.xlsMargin[1]+mergeLV+mergeWV, col+self.xlsMargin[0]+max(mergeLH,mergeWH))

    # -------------------------------------------------------------------------
    @staticmethod
    def _writeToRTF(ss, langDict, full_name, paragraph=None,
                    para_list=[],
                    question_name=""):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.

            @param ss: StyleSheet object
            @param langDict: Dictionary of languages
            @param full_name: Question name(label)
            @param paragraph: Add paragraph from S3QuestionTypeTextWidget
            @param para_list: List of paragraphs from S3QuestionTypeOptionWidget
            @param question_name: Name of question from S3QuestionTypeGridWidget
        """
        from gluon.contrib.pyrtf.Elements import Paragraph, Cell, B
        from gluon.contrib.pyrtf.PropertySets import BorderPS, FramePS

        thin_edge = BorderPS(width=20, style=BorderPS.SINGLE)
        thin_frame = FramePS(thin_edge, thin_edge, thin_edge, thin_edge)
        line = []

        if question_name:
            p = Paragraph(ss.ParagraphStyles.NormalCentre)
            p.append(B(question_name))
            line.append(Cell(p, thin_frame, span = 2))
            return line

        p = Paragraph(ss.ParagraphStyles.Normal)
        p.append(B(str(full_name)))

        if paragraph:
            line.append(Cell(p, paragraph, paragraph, paragraph, thin_frame))
        else:
            line.append(Cell(p, thin_frame))

        if para_list:
            paras = []
            for option in para_list:
                p = Paragraph(ss.ParagraphStyles.Normal)
                p.append(survey_T(option, langDict))
                paras.append(p)
            line.append(Cell(thin_frame, *paras))
        else:
            p = Paragraph(ss.ParagraphStyles.NormalGrey)
            p.append("")
            line.append(Cell(p, thin_frame))

        return line

    # -------------------------------------------------------------------------
    def writeQuestionToRTF(self, ss, langDict):
        """
            Wrapper function for _writeToRTF

            @param ss: StyleSheet object
            @param langDict: Dictionary of languages
        """
        full_name = self.fullName()
        return self._writeToRTF(ss, langDict, full_name)

    # -------------------------------------------------------------------------
    def verifyCoords(self, endrow, endcol):
        (width, height) = self.getMatrixSize()
        calcrow = self.startPosn[1] + width
        calccol = self.startPosn[0] + height
        error = False
        if calcrow != endrow:
            error = True
        if calccol != endcol:
            error = True
        if error:
            w_code = self.question["code"]
            msg = "Coord Verification Error for widget %s, startPosn:(%s, %s), expected:(%s, %s), observed:(%s, %s)" % (w_code, self.startPosn[1], self.startPosn[0], endrow, endcol, calcrow, calccol)
            current.log.error(msg)

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget

            NOTE: Not currently used but will be used when the UI supports the
                  validation of data entered in to the web form
        """
        if len(valueList) == 0:
            return self.ANSWER_MISSING
        data = value(valueList, 0)
        if data == None:
            return self.ANSWER_MISSING
        length = self.get("Length")
        if length != None and length(data) > length:
            return ANSWER_PARTLY_VALID
        return self.ANSWER_VALID

    # -------------------------------------------------------------------------
    def metadata(self, **attr):
        """
            Create the input fields for the metadata for the QuestionType

            NOTE: Not currently used but will be used when the UI supports the
                  creation of the template and specifically the questions in
                  the template
        """
        if "question_id" in attr:
            self._store_metadata(attr["question_id"])
        elements = []
        for fieldname in self.metalist:
            value = self.get(fieldname, "")
            input = StringWidget.widget(self.field, value, **attr)
            elements.append(TR(TD(fieldname), TD(input)))
        return TAG[""](elements)

# =============================================================================
class S3QuestionTypeTextWidget(S3QuestionTypeAbstractWidget):
    """
        Text Question Type widget

        provides a widget for the survey module that will manage plain
        text questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
    """

    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.webwidget = TextWidget
        self.typeDescription = T("Long Text")
        self.xlsWidgetSize = [12, 5]

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return True

    # -------------------------------------------------------------------------
    def canGrowVertical(self):
        return True

    # -------------------------------------------------------------------------
    def writeQuestionToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.

            @param ss: StyleSheet object
            @param langDict: Dictionary of languages
        """
        from gluon.contrib.pyrtf.Elements import Paragraph
        paragraph = Paragraph(ss.ParagraphStyles.Normal)
        full_name = self.fullName()

        return self._writeToRTF(ss, langDict, full_name,
                                paragraph=paragraph)

# =============================================================================
class S3QuestionTypeStringWidget(S3QuestionTypeAbstractWidget):
    """
        String Question Type widget

        provides a widget for the survey module that will manage plain
        string questions (text with a limited length).

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of characters
    """
    def __init__(self,
                 question_id = None
                 ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.metalist.append("Length")
        self.typeDescription = T("Short Text")
        self.xlsWidgetSize = [12, 0]

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return True

    # -------------------------------------------------------------------------
    def display(self, **attr):
        if "length" in self.qstn_metadata:
            length = self.qstn_metadata["length"]
            attr["_size"] = length
            attr["_maxlength"] = length
        return S3QuestionTypeAbstractWidget.display(self, **attr)

# =============================================================================
class S3QuestionTypeNumericWidget(S3QuestionTypeAbstractWidget):
    """
        Numeric Question Type widget

        provides a widget for the survey module that will manage simple
        numerical questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The length if the number, default length of 10 characters
        Format:       Describes the makeup of the number, as follows:
                      n    integer
                      n.   floating point
                      n.n  floating point, the number of decimal places defined
                           by the number of n's that follow the decimal point
    """
    def __init__(self,
                 question_id = None,
                 ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.metalist.append("Length")
        self.metalist.append("Format")
        self.typeDescription = T("Numeric")

    # -------------------------------------------------------------------------
    def display(self, **attr):
        length = self.get("Length", 10)
        attr["_size"] = length
        attr["_maxlength"] = length
        return S3QuestionTypeAbstractWidget.display(self, **attr)

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """
        return str(self.formattedAnswer(value))

    # -------------------------------------------------------------------------
    def formattedAnswer(self, data, format=None):
        if format == None:
            format = self.get("Format", "n")
        parts = format.partition(".")
        try:
            result = float(data)
        except:
            result = 0
        if parts[1] == "": # No decimal point so must be a whole number
            return int(result)
        else:
            if parts[2] == "": # No decimal places specified
                return result
            else:
                return round(result, len(parts[2]))

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid
        """
        format = self.get("Format", "n")
        if format == "n":
            return "integer"
        else:
            return "double"

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("Length", 10)
        format = self.get("Format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

# =============================================================================
class S3QuestionTypeDateWidget(S3QuestionTypeAbstractWidget):
    """
        Date Question Type widget

        provides a widget for the survey module that will manage simple
        date questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Date")

    # -------------------------------------------------------------------------
    def display(self, **attr):
        S3QuestionTypeAbstractWidget.initDisplay(self, **attr)
        from s3.s3widgets import S3DateWidget
        widget = S3DateWidget()
        value = self.getAnswer()
        self.attr["_id"] = self.question.code
        input = widget(self.field, value, **self.attr)
        return self.layout(self.question.name, input, **attr)

    # -------------------------------------------------------------------------
    def formattedAnswer(self, data):
        """
            This will take a string and do it's best to return a Date object
            It will try the following in order
            * Convert using the ISO format:
            * look for a month in words a 4 digit year and a day (1 or 2 digits)
            * a year and month that matches the date now and NOT a future date
            * a year that matches the current date and the previous month
        """
        rawDate = data
        date = None
        try:
            # First convert any non-numeric to a hyphen
            isoDate = ""
            addHyphen = False
            for char in rawDate:
                if char.isdigit:
                    if addHyphen == True and isoDate != "":
                        iscDate += "-"
                    isoDate += char
                    addHyphen = False
                else:
                    addHyphen = True
            # @ToDo: Use deployment_settings.get_L10n_date_format()
            date = datetime.strptime(rawDate, "%Y-%m-%d")
            return date
        except ValueError:
            try:
                for month in monthList:
                    if month in rawDate:
                        search = re, search("\D\d\d\D", rawDate)
                        if search:
                            day = search.group()
                        else:
                            search = re, search("^\d\d\D", rawDate)
                            if search:
                                day = search.group()
                            else:
                                search = re, search("\D\d\d$", rawDate)
                                if search:
                                    day = search.group()
                                else:
                                    search = re, search("\D\d\D", rawDate)
                                    if search:
                                        day = "0" + search.group()
                                    else:
                                        search = re, search("^\d\D", rawDate)
                                        if search:
                                            day = "0" + search.group()
                                        else:
                                            search = re, search("\D\d$", rawDate)
                                            if search:
                                                day = "0" + search.group()
                                            else:
                                                raise ValueError
                        search = re, search("\D\d\d\d\d\D", rawDate)
                        if search:
                            year = search.group()
                        else:
                            search = re, search("^\d\d\d\d\D", rawDate)
                            if search:
                                year = search.group()
                            else:
                                search = re, search("\D\d\d\d\d$", rawDate)
                                if search:
                                    year = search.group()
                                else:
                                    raise ValueError
                    # @ToDo: Use deployment_settings.get_L10n_date_format()
                    testDate = "%s-%s-%s" % (day, month, year)
                    if len(month) == 3:
                        format == "%d-%b-%Y"
                    else:
                        format == "%d-%B-%Y"
                    date = datetime.strptime(format, testDate)
                    return date
            except ValueError:
                return date


    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("length", 10)
        format = self.get("format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

# =============================================================================
class S3QuestionTypeTimeWidget(S3QuestionTypeAbstractWidget):
    """
        Time Question Type widget

        provides a widget for the survey module that will manage simple
        time questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Time")

    # -------------------------------------------------------------------------
    def display(self, **attr):
        S3QuestionTypeAbstractWidget.initDisplay(self, **attr)
        value = self.getAnswer()
        self.attr["_id"] = self.question.code
        input = TimeWidget.widget(self.field, value, **self.attr)
        return self.layout(self.question.name, input, **attr)


# =============================================================================
class S3QuestionTypeOptionWidget(S3QuestionTypeAbstractWidget):
    """
        Option Question Type widget

        provides a widget for the survey module that will manage simple
        option questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of options
        #:            A number one for each option
    """
    def __init__(self,
                 question_id = None,
                 ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.selectionInstructions = "Type x to mark box. Select just one option"
        self.metalist.append("Length")
        self.webwidget = RadioWidget
        self.typeDescription = T("Option")
        self.labelLeft = False
        self.singleRow = False
        self.xlsWidgetSize = [10, 0]

    # -------------------------------------------------------------------------
    def display(self, **attr):
        S3QuestionTypeAbstractWidget.initDisplay(self, **attr)
        self.field.requires = IS_IN_SET(self.getList())
        value = self.getAnswer()
        self.field.name = self.question.code
        input = RadioWidget.widget(self.field, value, **self.attr)
        self.field.name = "value"
        return self.layout(self.question.name, input, **attr)

    # -------------------------------------------------------------------------
    def getList(self):
        list = []
        length = self.get("Length")
        if length == None:
            raise Exception("Need to have the options specified")
        for i in xrange(int(length)):
            list.append(self.get(str(i + 1)))
        return list

    # -------------------------------------------------------------------------
    def getWidgetSize(self, maxWidth = 20):
        """
            function to return the size of the input control
        """
        # calculate the size required for the instructions
        instHeight = 1 + len(self.selectionInstructions)/maxWidth
        if self.singleRow:
            widgetHeight = 1
        else:
            widgetHeight = len(self.getList())
        return (maxWidth/2, instHeight + widgetHeight)

    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict={},
                      answerMatrix=None
                      ):
        """
            Function to write out basic details to the matrix object
        """
        self._store_metadata()
        startrow = row
        startcol = col
        mergeLH = 0
        mergeLV = 0
        maxWidth = 20
        endrow = row
        endcol = col
        lwidth = 10
        lheight = 1
        iwidth = 0
        iheight = 0
        if self.label:
            _TQstn = self._Tquestion(langDict)
            cell = survey_MatrixElement(row,
                                        col,
                                        _TQstn,
                                        style="styleSubHeader"
                                        )
            (lwidth, lheight) = self.getLabelSize()
            mergeLH = lwidth - 1
            mergeLV = lheight - 1
            cell.merge(mergeLH, mergeLV)
            matrix.addElement(cell)
            if self.labelLeft:
                col += lwidth
            else:
                row += lheight
            endrow = startrow + lheight
            endcol = startcol + lwidth
            if self.selectionInstructions != None:
                cell = survey_MatrixElement(row,
                                            col,
                                            survey_T(self.selectionInstructions,
                                                     langDict),
                                            style="styleInstructions")
                iheight = len(self.selectionInstructions) / maxWidth + 1
                mergeIV = iheight - 1
                cell.merge(mergeLH, mergeIV)
                matrix.addElement(cell)
                row += iheight
        list = self.getList()
        if answerMatrix != None:
            answerRow = answerMatrix.lastRow+1
            cell = survey_MatrixElement(answerRow, 0, self.question["code"],
                                        style="styleSubHeader")
            answerMatrix.addElement(cell)
            cell = survey_MatrixElement(answerRow,
                                        1,
                                        len(list),
                                        style="styleSubHeader")
            answerMatrix.addElement(cell)
            cell = survey_MatrixElement(answerRow, 2, "|#|".join(list),
                                        style="styleSubHeader")
            answerMatrix.addElement(cell)
            answerCol = 3
        wwidth = lwidth
        mergeWH = lwidth - 1
        wheight = len(list)
        if self.singleRow:
            wwidthpart = (wwidth - len(list)) / len(list)
            mergeWH = wwidthpart - 1
            wheight = 1
        for option in list:
            _TQstn = survey_T(option, langDict)
            cell = survey_MatrixElement(row,
                                        col,
                                        _TQstn,
                                        style="styleText")
            oheight = len(_TQstn) / maxWidth + 1
            cell.merge(mergeWH - 1, oheight - 1)
            matrix.addElement(cell)
            cell = survey_MatrixElement(row, col + mergeWH, "",
                                        style="styleInput")
            matrix.addElement(cell)
            if answerMatrix != None:
                cell = survey_MatrixElement(answerRow, answerCol,
                                            self.rowcol_to_cell(row, col + mergeWH),
                                            style="styleText")
                answerMatrix.addElement(cell)
                answerCol += 1
            if self.singleRow:
                col += 1 + wwidthpart
            else:
                row += oheight
        if self.singleRow:
            if endrow < row + 1:
                endrow = row + 1
            if endcol < col:
                endcol = col
        else:
            if endrow < row:
                endrow = row
            if endcol < col + 1 + mergeWH:
                endcol = col + 1 + mergeWH
        self.addPaddingAroundWidget(matrix, startrow, startcol, lwidth, lheight, wwidth, iheight+wheight)
        self.addPaddingToCell(matrix, startrow, startcol, endrow, endcol)
        endrow += self.xlsMargin[1]
        endcol += self.xlsMargin[0]
        if DEBUG:
            # Only for debugging purposes
            self.verifyCoords(endrow, endcol)
        return (endrow, endcol)

    # -------------------------------------------------------------------------
    def writeQuestionToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.

            @param ss: StyleSheet object
            @param langDict: Dictionary of languages
        """
        para_list = self.getList()
        full_name = self.fullName()

        return self._writeToRTF(ss, langDict, full_name,
                                para_list=para_list)

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        if len(valueList) == 0:
            return self.ANSWER_MISSING
        data = valueList[0]
        if data == None:
            return self.ANSWER_MISSING
        self._store_metadata(qstn_id)
        if data in self.getList():
            return self.ANSWER_VALID
        else:
            return self.ANSWER_VALID
        return self.ANSWER_INVALID

# =============================================================================
class S3QuestionTypeOptionYNWidget(S3QuestionTypeOptionWidget):
    """
        YN Question Type widget

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.selectionInstructions = "Type x to mark box."
        self.typeDescription = T("Yes, No")
        self.qstn_metadata["Length"] = 2
        self.singleRow = True

    # -------------------------------------------------------------------------
    def getList(self):
        return ["Yes", "No"]

# =============================================================================
class S3QuestionTypeOptionYNDWidget(S3QuestionTypeOptionWidget):
    """
        Yes, No, Don't Know: Question Type widget

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.selectionInstructions = "Type x to mark box."
        self.typeDescription = T("Yes, No, Don't Know")
        self.qstn_metadata["Length"] = 3

    # -------------------------------------------------------------------------
    def getList(self):
        #T = current.T
        #return [T("Yes"), T("No"), T("Don't Know")]
        return ["Yes", "No", "Don't Know"]

# =============================================================================
class S3QuestionTypeOptionOtherWidget(S3QuestionTypeOptionWidget):
    """
        Option Question Type widget with a final other option attached

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of options
        #:            A number one for each option
        Other:        The question type the other option should be
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.typeDescription = T("Option Other")

    # -------------------------------------------------------------------------
    def getList(self):
        list = S3QuestionTypeOptionWidget.getList(self)
        list.append("Other")
        return list


# =============================================================================
class S3QuestionTypeMultiOptionWidget(S3QuestionTypeOptionWidget):
    """
        Multi Option Question Type widget

        provides a widget for the survey module that will manage options
        questions, where more than one answer can be provided.

        Available metadata for this class:
        Help message: A message to help with completing the question
    """
    def __init__(self,
                 question_id = None,
                 ):
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.selectionInstructions = "Type x to mark box. Select all applicable options"
        self.typeDescription = current.T("Multi-Option")

    # -------------------------------------------------------------------------
    def display(self, **attr):
        """ @todo: docstring """

        S3QuestionTypeAbstractWidget.initDisplay(self, **attr)
        self.field.requires = IS_IN_SET(self.getList())
        value = self.getAnswer()
        valueList = json2list(value)

        self.field.name = self.question.code
        input = CheckboxesWidget.widget(self.field, valueList, **self.attr)
        self.field.name = "value"
        return self.layout(self.question.name, input, **attr)

# =============================================================================
class S3QuestionTypeLocationWidget(S3QuestionTypeAbstractWidget):
    """
        ***************************************
        **** MULTIPLE CHANGES HAVE OCCURRED ***
        **** REALLY NEEDS TO BE REWRITTEN  ****
        ***************************************
        Location widget: Question Type widget

        provides a widget for the survey module that will link to the
        gis_location table, and provide the record if a match exists.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Parent:    Indicates which question is used to indicate the parent
                   This is used as a simplified Hierarchy.
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Location")
        self.xlsWidgetSize = [12, 0]

    # -------------------------------------------------------------------------
    def canGrowHorizontal(self):
        return True

    # -------------------------------------------------------------------------
    def display(self, **attr):
        """
            This displays the widget on a web form. It uses the layout
            function to control how the widget is displayed
        """
        return S3QuestionTypeAbstractWidget.display(self, **attr)

    # -------------------------------------------------------------------------
    def getLocationRecord(self, complete_id, location):
        """
            Return the location record from the database
        """
        record = Storage()
        if location != None:
            gtable = current.s3db.gis_location
            query = (gtable.name == location)
            record = current.db(query).select(gtable.name,
                                              gtable.lat,
                                              gtable.lon,
                                             )
            record.complete_id = complete_id
            record.key = location
            if len(record.records) == 0:
                msg = "Unknown Location %s, %s, %s" %(location, query, record.key)
                _debug(msg)
            return record
        else:
            return None

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """

        return value

    # -------------------------------------------------------------------------
    def getAnswerListFromJSON(self, answer):
        """
            If the answer is stored as a JSON value return the data as a map

            If it is not valid JSON then an exception will be raised,
            and must be handled by the calling function
        """

        answerList = json2py(answer)
        return answerList

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("length", 10)
        format = self.get("format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

# =============================================================================
class S3QuestionTypeLinkWidget(S3QuestionTypeAbstractWidget):
    """
        Link widget: Question Type widget

        provides a widget for the survey module that has a link with another
        question.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Parent: The question it links to
        Type: The type of question it really is (another question type)
        Relation: How it relates to the parent question
                  groupby: answers should be grouped by the value of the parent
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.metalist.append("Parent")
        self.metalist.append("Type")
        self.metalist.append("Relation")
        try:
            self._store_metadata()
            type = self.get("Type")
            parent = self.get("Parent")
            if type == None or parent == None:
                self.typeDescription = T("Link")
            else:
                self.typeDescription = T("%s linked to %s") % (type, parent)
        except:
            self.typeDescription = T("Link")

    # -------------------------------------------------------------------------
    def realWidget(self):
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        realWidget.question = self.question
        realWidget.qstn_metadata = self.qstn_metadata
        return realWidget

    # -------------------------------------------------------------------------
    def display(self, **attr):
        return self.realWidget().display(**attr)

    # -------------------------------------------------------------------------
    def onaccept(self, value):
        """
            Method to format the value that has just been put on the database
        """
        type = self.get("Type")
        return self.realWidget().onaccept(value)

    # -------------------------------------------------------------------------
    def getParentType(self):
        self._store_metadata()
        return self.get("Type")

    # -------------------------------------------------------------------------
    def getParentQstnID(self):
        parent = self.get("Parent")
        query = (self.qtable.code == parent)
        row = current.db(query).select(limitby=(0, 1)).first()
        return row.id

    # -------------------------------------------------------------------------
    def fullName(self):
        return self.question.name

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid
        """
        return self.realWidget().db_type()

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        return realWidget.validate(valueList, qstn_id)

# =============================================================================
class S3QuestionTypeGridWidget(S3QuestionTypeAbstractWidget):
    """
        Grid widget: Question Type widget

        provides a widget for the survey module that hold a grid of related
        questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Subtitle: The text for the 1st column and 1st row of the grid
        QuestionNo: The number of the first question, used for the question code
        col-cnt:  The number of data columns in the grid
        row-cnt:  The number of data rows in the grid
        columns:  An array of headings for each data column
        rows:     An array of headings for each data row
        data:     A matrix of widgets for each data cell
    """
    def __init__(self,
                 question_id = None,
                 ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.metalist.append("Subtitle")
        self.metalist.append("QuestionNo")
        self.metalist.append("col-cnt")
        self.metalist.append("row-cnt")
        self.metalist.append("columns")
        self.metalist.append("rows")
        self.metalist.append("data")
        self.typeDescription = current.T("Grid")

    # -------------------------------------------------------------------------
    def getMetaData(self, qstn_id=None):
        self._store_metadata(qstn_id=qstn_id, update=True)
        self.subtitle = self.get("Subtitle")
        self.qstnNo = int(self.get("QuestionNo", 1))
        self.colCnt = self.get("col-cnt")
        self.rowCnt = self.get("row-cnt")
        self.columns = json.loads(self.get("columns"))
        self.rows = json.loads(self.get("rows"))
        self.data = json.loads(self.get("data"))

    # -------------------------------------------------------------------------
    def getHeading(self, number):
        self.getMetaData()
        col = (number - self.qstnNo) % int(self.colCnt)
        return self.columns[col]

    # -------------------------------------------------------------------------
    def display(self, **attr):
        S3QuestionTypeAbstractWidget.display(self, **attr)
        complete_id = None
        if "complete_id" in self.question:
            complete_id = self.question.complete_id
        self.getMetaData()
        table = TABLE()
        if self.data != None:
            tr = TR(_class="survey_question")
            if self.subtitle == None:
                tr.append("")
            else:
                tr.append(TH(self.subtitle))
            for col in self.columns:
                if col == None:
                    tr.append("")
                else:
                    tr.append(TH(col))
            table.append(tr)
            posn = 0
            codeNum = self.qstnNo
            for row in self.data:
                tr = TR(_class="survey_question")
                tr.append(TH(self.rows[posn]))
                for cell in row:
                    if cell == "Blank":
                        tr.append("")
                    else:
                        code = "%s%s" % (self.question["code"], codeNum)
                        codeNum += 1
                        childWidget = self.getChildWidget(code)
                        if complete_id != None:
                            childWidget.loadAnswer(complete_id,
                                                   childWidget.id)
                        tr.append(childWidget.subDisplay())
                table.append(tr)
                posn += 1
        return TABLE(table, _border=3)

    # -------------------------------------------------------------------------
    def getMatrixSize(self, maxWidth = 20):
        self._store_metadata()
        self.getMetaData()
        width = 0
        height = 0
        # Add space for the sub heading
        height = 1
        codeNum = self.qstnNo
        labelWidth = maxWidth/2
        for line in xrange(int(self.rowCnt)):
            label = survey_T(self.rows[line], self.langDict)
            (lwidth, lheight) = (labelWidth, len(label) / (4 * labelWidth / 3) + 1)
            for cell in xrange(int(self.colCnt)):
                code = "%s%s" % (self.question["code"], codeNum)
                codeNum += 1
                childWidget = self.getChildWidget(code)
                type = childWidget.get("Type")
                realWidget = survey_question_type[type](childWidget.id)
                (cwidth, cheight) = realWidget.getWidgetSize(maxWidth)
                lwidth += cwidth
                if cheight > lheight:
                    lheight = cheight
            height += lheight
            if lwidth > width:
                width = lwidth
        _debug("%s (%s,%s)" % (self.question["code"], height, width))
        self.xlsWidgetSize = (width, height)
        return (height, width)

    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict={},
                      answerMatrix=None,
                      ):
        """
            Function to write out basic details to the matrix object
        """
        self._store_metadata()
        self.getMetaData()
        startrow = row
        startcol = col
        endrow = row
        endcol = col
        maxWidth = 20
        labelWidth = maxWidth / 2
        codeNum = self.qstnNo
        row += 1
        needHeading = True
        # Merge the top left cells
        subtitle = survey_T(self.subtitle, self.langDict)
        cell = survey_MatrixElement(startrow,
                                    startcol,
                                    subtitle,
                                    style="styleSubHeader"
                                    )
        cell.merge(labelWidth - 1, 0)
        matrix.addElement(cell)
        for line in xrange(int(self.rowCnt)):
            # Add the label
            label = survey_T(self.rows[line], self.langDict)
            (lwidth, lheight) = (labelWidth, len(label)/(4 * labelWidth / 3) + 1)
            cell = survey_MatrixElement(row,
                                        col,
                                        label,
                                        style="styleSubHeader"
                                        )
            cell.merge(lwidth - 1, lheight - 1)
            matrix.addElement(cell)
            maxrow = row + lheight
            endcol = col + lwidth
            for cell in xrange(int(self.colCnt)):
                code = "%s%s" % (self.question["code"], codeNum)
                codeNum += 1
                childWidget = self.getChildWidget(code)
                type = childWidget.get("Type")
                realWidget = survey_question_type[type](childWidget.id)
                realWidget.label = False
                #realWidget.xlsMargin = (0,0)
                col = endcol
                realWidget.startPosn = (col, row)
                (endrow, endcol) = realWidget.writeToMatrix(matrix,
                                                             row,
                                                             col,
                                                             langDict,
                                                             answerMatrix
                                                            )
                if endrow > maxrow:
                    maxrow = endrow
                if needHeading:
                    # Now add the heading for this column
                    label = survey_T(self.columns[cell], self.langDict)
                    cell = survey_MatrixElement(startrow,
                                                col,
                                                label,
                                                style="styleSubHeader"
                                                )
                    cell.merge(endcol - col - 1, 0)
                    matrix.addElement(cell)
            row = maxrow
            col = startcol
            needHeading = False
        # Add widget padding
        self.addPaddingToCell(matrix, startrow, startcol, row, endcol)
        row += self.xlsMargin[1]
        endcol += self.xlsMargin[0]
        return (row, endcol)

    # -------------------------------------------------------------------------
    def writeQuestionToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            This will just display the grid name, following this will be the
            grid child objects.

            @param ss: StyleSheet object
            @param langDict: Dictionary of languages
        """
        question_name = self.question.name
        full_name = self.fullName()

        return self._writeToRTF(ss, langDict, full_name,
                                question_name=question_name)

    # -------------------------------------------------------------------------
    def insertChildren(self, record, metadata):
        self.id = record.id
        self.question = record
        self.qstn_metadata = metadata
        self.getMetaData()
        if self.data != None:
            posn = 0
            qstnNo = self.qstnNo
            parent_id = self.id
            parent_code = self.question["code"]
            for row in self.data:
                name = self.rows[posn]
                posn += 1
                for cell in row:
                    if cell == "Blank":
                        continue
                    else:
                        type = cell
                        code = "%s%s" % (parent_code, qstnNo)
                        qstnNo += 1
                        childMetadata = self.get(code)
                        if childMetadata == None:
                            childMetadata = {}
                        else:
                            childMetadata = json.loads(childMetadata)
                        childMetadata["Type"] = type
                        # web2py stomps all over a list so convert back to a string
                        # before inserting it on the database
                        metadata = json.dumps(childMetadata)
                        try:
                            id = self.qtable.insert(name = name,
                                                    code = code,
                                                    type = "GridChild",
                                                    metadata = metadata,
                                                   )
                        except:
                            record = self.qtable(code = code)
                            id = record.id
                            record.update_record(name = name,
                                                 code = code,
                                                 type = "GridChild",
                                                 metadata = metadata,
                                                )
                        record = self.qtable(id)
                        current.s3db.survey_updateMetaData(record,
                                                           "GridChild",
                                                           childMetadata)

    # -------------------------------------------------------------------------
    def insertChildrenToList(self, question_id, template_id, section_id,
                             qstn_posn):
        self.getMetaData(question_id)
        if self.data != None:
            posn = 0
            qstnNo = self.qstnNo
            qstnPosn = 1
            parent_id = self.id
            parent_code = self.question["code"]
            for row in self.data:
                name = self.rows[posn]
                posn += 1
                for cell in row:
                    if cell == "Blank":
                        continue
                    else:
                        code = "%s%s" % (parent_code, qstnNo)
                        qstnNo += 1
                        record = self.qtable(code = code)
                        id = record.id
                        try:
                            self.qltable.insert(question_id = id,
                                                template_id = template_id,
                                                section_id = section_id,
                                                posn = qstn_posn+qstnPosn,
                                               )
                            qstnPosn += 1
                        except:
                            pass # already on the database no change required

    # -------------------------------------------------------------------------
    def getChildWidget(self, code):
        # Get the question from the database
        query = (self.qtable.code == code)
        question = current.db(query).select(limitby=(0, 1)).first()
        if question == None:
            raise Exception("no question with code %s in database" % code)
        cellWidget = survey_question_type["GridChild"](question.id)
        return cellWidget

# =============================================================================
class S3QuestionTypeGridChildWidget(S3QuestionTypeAbstractWidget):
    """
        GridChild widget: Question Type widget

        provides a widget for the survey module that is held by a grid question
        type an provides a link to the true question type.

        Available metadata for this class:
        Type:     The type of question it really is (another question type)
    """
    def __init__(self,
                 question_id = None,
                 ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        if self.question != None and "code" in self.question:
            # Expect the parent code to be the same as the child with the number
            # removed. This means that the parent code must end with a hyphen.
            end = self.question.code.rfind("-")+1
            parentCode = self.question.code[0:end]
            parentNumber = self.question.code[end:]
            self.question.parentCode = parentCode
            self.question.parentNumber = int(parentNumber)
        self.metalist.append("Type")
        self.typeDescription = self.qstn_metadata["Type"]
        self.xlsWidgetSize = (0, 0)

    # -------------------------------------------------------------------------
    def display(self, **attr):
        return None

    # -------------------------------------------------------------------------
    def realWidget(self):
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        realWidget.question = self.question
        realWidget.qstn_metadata = self.qstn_metadata
        return realWidget

    # -------------------------------------------------------------------------
    def subDisplay(self, **attr):
        S3QuestionTypeAbstractWidget.display(self, **attr)
        return self.realWidget().display(question_id=self.id, display = "Control Only")

    # -------------------------------------------------------------------------
    def getParentType(self):
        self._store_metadata()
        return self.get("Type")

    # -------------------------------------------------------------------------
    def db_type(self):
        """
            Return the real database table type for this question
            This assumes that the value is valid
        """
        return self.realWidget().db_type()

    # -------------------------------------------------------------------------
    def writeToMatrix(self,
                      matrix,
                      row,
                      col,
                      langDict={},
                      answerMatrix=None,
                      style={}
                     ):
        """
            Dummy function that doesn't write anything to the matrix,
            because it is handled by the Grid question type
        """
        return (row, col)

    # -------------------------------------------------------------------------
    def writeQuestionToRTF(self, ss, langDict):
        """
            Function to write the basic question details to a rtf document.

            The basic details will be written to Cell objects that can be
            added to a row in a table object.

            @param ss: StyleSheet object
            @param langDict: Dictionary of languages
        """
        return self.realWidget().writeQuestionToRTF(ss, langDict)


###############################################################################
###  Classes for analysis
###    will work with a list of answers for the same question
###############################################################################

# *****************************************************************************
# Analysis Types
# @todo: get rid of the wrapper functions!
#
def analysis_stringType(question_id, answerList):
    return S3StringAnalysis("String", question_id, answerList)

def analysis_textType(question_id, answerList):
    return S3TextAnalysis("Text", question_id, answerList)

def analysis_numericType(question_id, answerList):
    return S3NumericAnalysis("Numeric", question_id, answerList)

def analysis_dateType(question_id, answerList):
    return S3DateAnalysis("Date", question_id, answerList)

def analysis_timeType(question_id, answerList):
    return S3TimeAnalysis("Date", question_id, answerList)

def analysis_optionType(question_id, answerList):
    return S3OptionAnalysis("Option", question_id, answerList)

def analysis_ynType(question_id, answerList):
    return S3OptionYNAnalysis("YesNo", question_id, answerList)

def analysis_yndType(question_id, answerList):
    return S3OptionYNDAnalysis("YesNoDontKnow", question_id, answerList)

def analysis_optionOtherType(question_id, answerList):
    return S3OptionOtherAnalysis("OptionOther", question_id, answerList)

def analysis_multiOptionType(question_id, answerList):
    return S3MultiOptionAnalysis("MultiOption", question_id, answerList)

def analysis_locationType(question_id, answerList):
    return S3LocationAnalysis("Location", question_id, answerList)

def analysis_linkType(question_id, answerList):
    return S3LinkAnalysis("Link", question_id, answerList)

def analysis_gridType(question_id, answerList):
    return S3GridAnalysis("Grid", question_id, answerList)

def analysis_gridChildType(question_id, answerList):
    return S3GridChildAnalysis("GridChild", question_id, answerList)

#def analysis_ratingType(answerList):
#    return S3RatingAnalysis(answerList)
#    pass

survey_analysis_type = {"String": analysis_stringType,
                        "Text": analysis_textType,
                        "Numeric": analysis_numericType,
                        "Date": analysis_dateType,
                        "Time": analysis_timeType,
                        "Option": analysis_optionType,
                        "YesNo": analysis_ynType,
                        "YesNoDontKnow": analysis_yndType,
                        "OptionOther": analysis_optionOtherType,
                        "MultiOption" : analysis_multiOptionType,
                        "Location": analysis_locationType,
                        "Link": analysis_linkType,
                        "Grid": analysis_gridType,
                        "GridChild" : analysis_gridChildType,
                        #"Rating": analysis_ratingType,
                        }

# =============================================================================
class survey_S3AnalysisPriority():
    """ @todo: docstring """

    def __init__(self,
                 range=[-1, -0.5, 0, 0.5, 1],
                 colour={-1:"#888888", # grey
                          0:"#000080", # blue
                          1:"#008000", # green
                          2:"#FFFF00", # yellow
                          3:"#FFA500", # orange
                          4:"#FF0000", # red
                          5:"#880088", # purple
                         },
                 # Make Higher-priority show up more clearly
                 opacity={-1:0.5,
                           0:0.6,
                           1:0.6,
                           2:0.7,
                           3:0.7,
                           4:0.8,
                           5:0.8,
                          },
                 image={-1:"grey",
                         0:"blue",
                         1:"green",
                         2:"yellow",
                         3:"orange",
                         4:"red",
                         5:"purple",
                        },
                 desc={-1:"No Data",
                        0:"Very Low",
                        1:"Low",
                        2:"Medium Low",
                        3:"Medium High",
                        4:"High",
                        5:"Very High",
                       },
                 zero = True,
                 ):
        """
            Constructor

            @todo: do not use lists or dicts as parameter defaults!
            @todo: parameter description
        """
        self.range = range
        self.colour = colour
        self.opacity = opacity
        self.image = image
        self.description = desc

    # -------------------------------------------------------------------------
    def imageURL(self, app, key):
        """ @todo: docstring """

        T = current.T
        base_url = "/%s/static/img/survey/" % app
        dot_url = base_url + "%s-dot.png" % self.image[key]
        image = IMG(_src=dot_url,
                    _alt=T(self.image[key]),
                    _height=12,
                    _width=12,
                   )
        return image

    # -------------------------------------------------------------------------
    def desc(self, key):
        """ @todo: docstring """

        T = current.T
        return T(self.description[key])

    # -------------------------------------------------------------------------
    def rangeText(self, key, pBand):
        """ @todo: docstring """

        T = current.T
        if key == -1:
            return ""
        elif key == 0:
            return T("At or below %s") % (pBand[1])
        elif key == len(pBand)-1:
            return T("Above %s") % (pBand[len(pBand)-1])
        else:
            return "%s - %s" % (pBand[key], pBand[key+1])

# -----------------------------------------------------------------------------
class S3AbstractAnalysis():
    """
        Abstract class used to hold all the responses for a single question
        and perform some simple analysis on the data.

        This class holds the main functions for:
         * displaying tables of results
         * displaying charts
         * grouping the data.

        Properties
        ==========
        question_id    - The id from the database
        answerList     - A list of answers, taken from the survey_answer
                         id, complete_id and value
                         See models/survey.py getAllAnswersForQuestionInSeries()
        valueList      - A list of validated & sanitised values
        result         - A list of results before formatting
        type           - The question type
        qstnWidget     - The question Widget for this question
        priorityGroup  - The type of priority group to use in the map
        priorityGroups - The priority data used to colour the markers on the map
    """

    def __init__(self,
                 type,
                 question_id,
                 answerList):
        """
            Constructor

            @todo: parameter description
        """

        self.question_id = question_id
        self.answerList = answerList
        self.valueList = []
        self.result = []
        self.type = type
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.priorityGroup = "zero" # Ensures that it doesn't go negative
        self.priorityGroups = {"default" : [-1, -0.5, 0, 0.5, 1],
                               "standard" : [-2, -1, 0, 1, 2],
                               }
        for answer in self.answerList:
            if self.valid(answer):
                try:
                    cast = self.castRawAnswer(answer["complete_id"],
                                              answer["value"])
                    if cast != None:
                        self.valueList.append(cast)
                except:
                    if DEBUG:
                        raise
                    pass

        self.basicResults()

    # -------------------------------------------------------------------------
    def valid(self, answer):
        """
            Used to validate a single answer

            @todo: parameter description
            @todo: raise exception if abstract and override is mandatory
        """

        # @todo add validation here
        # widget = S3QuestionTypeNumericWidget()
        # widget.validate(answer)
        # if widget.ANSWER_VALID:
        return True

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        """
            Used to modify the answer from its raw text format.
            Where necessary, this will function be overridden.

            @todo: parameter description
            @todo: raise exception if abstract and override is mandatory
        """

        return answer

    # -------------------------------------------------------------------------
    def basicResults(self):
        """
            Perform basic analysis of the answer set.
            Where necessary, this will function be overridden.

            @todo: parameter description
            @todo: raise exception if abstract and override is mandatory
        """

        pass

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        """
            This will display a button which when pressed will display a chart
            When a chart is not appropriate then the subclass will override this
            function with a nul function.

            @todo: parameter description
            @todo: make a class property rather than overriding in subclasses
        """

        if len(self.valueList) == 0:
            return None
        if series_id is None:
            return None
        src = URL(f="completed_chart",
                  vars={"question_id": self.question_id,
                        "series_id" : series_id,
                        "type" : self.type
                        }
                  )
        link = A(current.T("Chart"), _href=src, _target="blank",
                 _class="action-btn")
        return DIV(link, _class="surveyChart%sWidget" % self.type)

    # -------------------------------------------------------------------------
    def getChartName(self, series_id):
        """
            Get chart name for series_id

            @todo: parameter description
        """

        import hashlib
        h = hashlib.sha256()
        h.update(self.qstnWidget.question.code)
        encoded_part = h.hexdigest()
        chartName = "survey_series_%s_%s" % (series_id, encoded_part)

        return chartName

    # -------------------------------------------------------------------------
    def drawChart(self,
                  series_id,
                  output=None,
                  data=None,
                  label=None,
                  xLabel=None,
                  yLabel=None):
        """
            This function will draw the chart using the answer set.

            This function must be overridden by the subclass.

            @todo: parameter description
            @todo: raise NotImplementedException if override is mandatory
        """

        msg = "Programming Error: No chart for %sWidget" % self.type
        output = StringIO()
        output.write(msg)
        current.response.body = output

    # -------------------------------------------------------------------------
    def summary(self):
        """
            Calculate a summary of basic data.

            Where necessary, this will function be overridden.
        """

        self.result = []
        return self.count()

    # -------------------------------------------------------------------------
    def count(self):
        """
            Create a basic count of the data set.

            Where necessary, this will function be overridden.
        """

        self.result.append(([current.T("Replies")], len(self.answerList)))
        return self.format()

    # -------------------------------------------------------------------------
    def format(self):
        """
            This function will take the results and present them in a
            HTML table

            @todo: rename into "formatted"
        """

        table = TABLE()
        for (key, value) in self.result:
            table.append(TR(TD(B(key)), TD(value)))
        return table

    # -------------------------------------------------------------------------
    def uniqueCount(self):
        """
            Calculate the number of occurances of each value

            @todo: do not override Python built-in functions (e.g. "map")
        """

        map = {}
        for answer in self.valueList:
            if answer in map:
                map[answer] += 1
            else:
                map[answer] = 1
        return map

    # -------------------------------------------------------------------------
    def groupData(self, groupAnswer):
        """
            method to group the answers by the categories passed in
            The categories will belong to another question.

            For example the categories might be an option question which has
            responses from High, Medium and Low. So all the responses that
            correspond to the High category will go into one group, the Medium
            into a second group and Low into the final group.

            Later these may go through a filter which could calculate the
            sum, or maybe the mean. Finally the result will be split.

            See controllers/survey.py - series_graph()

            @todo: parameter description
        """

        grouped = {}
        answers = {}
        for answer in self.answerList:
            # hold the raw value (filter() will pass the value through castRawAnswer()
            answers[answer["complete_id"]] = answer["value"]
        # Step through each of the responses on the categories question
        for ganswer in groupAnswer:
            gcode = ganswer["complete_id"]
            greply = ganswer["value"]
            # If response to the group question also has a response to the main question
            # Then store the response in value, otherwise return an empty list for this response
            if gcode in answers:
                value = answers[gcode]
                if greply in grouped:
                    grouped[greply].append(value)
                else:
                    grouped[greply] = [value]
            else:
                if greply not in grouped:
                    grouped[greply] = []
        return grouped

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        """
            Filter the data within the groups by the filter type

            @todo: indicate whether this is meant to be overwritten by
                   subclass (if not: remove it!)
            @todo: parameter description
        """

        return groupedData

    # -------------------------------------------------------------------------
    def splitGroupedData(self, groupedData):
        """
            Split the data set by the groups

            @todo: parameter description
        """

        keys = []
        values = []
        for (key, value) in groupedData.items():
            keys.append(key)
            values.append(value)
        return (keys, values)

# =============================================================================
class S3StringAnalysis(S3AbstractAnalysis):
    """
        @todo: docstring
        @todo: use class property rather than overriding chartButton method
               (=only enable chartButton when needed rather than overriding
                 with return None => lots of unnecessary calls!)
    """

    def chartButton(self, series_id):
        return None

# =============================================================================
class S3TextAnalysis(S3AbstractAnalysis):
    """
        @todo: docstring
        @todo: use class property rather than overriding chartButton method
               (=only enable chartButton when needed rather than overriding
                 with return None => lots of unnecessary calls!)
    """

    def chartButton(self, series_id):
        return None

# =============================================================================
class S3DateAnalysis(S3AbstractAnalysis):
    """
        @todo: docstring
        @todo: use class property rather than overriding chartButton method
               (=only enable chartButton when needed rather than overriding
                 with return None => lots of unnecessary calls!)
    """

    def chartButton(self, series_id):
        return None

# -----------------------------------------------------------------------------
class S3TimeAnalysis(S3AbstractAnalysis):
    """
        @todo: docstring
        @todo: use class property rather than overriding chartButton method
               (=only enable chartButton when needed rather than overriding
                 with return None => lots of unnecessary calls!)
    """

    def chartButton(self, series_id):
        return None

# =============================================================================
class S3NumericAnalysis(S3AbstractAnalysis):
    """
        @todo: docstring
    """

    def __init__(self, type, question_id, answerList):

        S3AbstractAnalysis.__init__(self, type, question_id, answerList)
        self.histCutoff = 10

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        """ @todo: docstring """

        try:
            return float(answer)
        except ValueError:
            return None

    # -------------------------------------------------------------------------
    def summary(self):
        """ @todo: docstring """

        T = current.T
        widget = S3QuestionTypeNumericWidget()
        fmt = widget.formattedAnswer
        if self.sum:
            self.result.append(([T("Total")], fmt(self.sum)))
        if self.average:
            self.result.append(([T("Average")], fmt(self.average)))
        if self.max:
            self.result.append(([T("Maximum")], fmt(self.max)))
        if self.min:
            self.result.append(([T("Minimum")], fmt(self.min)))
        return self.format()

    # -------------------------------------------------------------------------
    def count(self):
        """ @todo: docstring """

        T = current.T
        self.result.append((T("Replies"), len(self.answerList)))
        self.result.append((T("Valid"), self.cnt))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        """ @todo: docstring """

        self.cnt = 0
        if len(self.valueList) == 0:
            self.sum = None
            self.average = None
            self.max = None
            self.min = None
            return
        self.sum = 0
        self.max = self.valueList[0]
        self.min = self.valueList[0]
        for answer in self.valueList:
            self.cnt += 1
            self.sum += answer
            if answer > self.max:
                self.max = answer
            if answer < self.min:
                self.min = answer
        self.average = self.sum / float(self.cnt)

    # -------------------------------------------------------------------------
    def advancedResults(self):
        """ @todo: docstring """

        try:
            from numpy import array
        except:
            current.log.error("ERROR: S3Survey requires numpy library installed.")

        array = array(self.valueList)
        self.std = array.std()
        self.mean = array.mean()
        self.zscore = {}
        for answer in self.answerList:
            complete_id = answer["complete_id"]
            try:
                value = self.castRawAnswer(complete_id, answer["value"])
            except:
                continue
            if value != None:
                self.zscore[complete_id] = (value - self.mean) / self.std

    # -------------------------------------------------------------------------
    def priority(self, complete_id, priorityObj):
        """ @todo: docstring """

        priorityList = priorityObj.range
        priority = 0
        try:
            zscore = self.zscore[complete_id]
            for limit in priorityList:
                if zscore <= limit:
                    return priority
                priority += 1
            return priority
        except:
            return -1

    # -------------------------------------------------------------------------
    def priorityBand(self, priorityObj):
        """ @todo: docstring """

        priorityList = priorityObj.range
        priority = 0
        band = [""]
        cnt = 0
        for limit in priorityList:
            value = int(self.mean + limit * self.std)
            if value < 0:
                value = 0
                priorityList[cnt] = - self.mean / self.std
            band.append(value)
            cnt += 1
        return band

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        """ @todo: docstring """

        # At the moment only draw charts for integers
        if self.qstnWidget.get("Format", "n") != "n":
            return None
        if len(self.valueList) < self.histCutoff:
            return None
        return S3AbstractAnalysis.chartButton(self, series_id)

    # -------------------------------------------------------------------------
    def drawChart(self,
                  series_id,
                  output="xml",
                  data=None,
                  label=None,
                  xLabel=None,
                  yLabel=None):
        """ @todo: docstring """

        chartFile = self.getChartName(series_id)
        cached = S3Chart.getCachedFile(chartFile)
        if cached:
            return cached

        chart = S3Chart(path=chartFile)
        chart.asInt = True
        if data == None:
            chart.survey_hist(self.qstnWidget.question.name,
                              self.valueList,
                              10,
                              0,
                              self.max,
                              xlabel = self.qstnWidget.question.name,
                              ylabel = current.T("Count")
                             )
        else:
            chart.survey_bar(self.qstnWidget.question.name,
                             data,
                             label,
                             []
                            )
        image = chart.draw(output=output)
        return image

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        """ @todo: docstring """

        filteredData = {}
        if filterType == "Sum":
            for (key, valueList) in groupedData.items():
                sum = 0
                for value in valueList:
                    try:
                        sum += self.castRawAnswer(None, value)
                    except:
                        pass
                filteredData[key] = sum
            return filteredData
        return groupedData

# =============================================================================
class S3OptionAnalysis(S3AbstractAnalysis):
    """ @todo: docstring """

    # -------------------------------------------------------------------------
    def summary(self):
        """ @todo: docstring """

        T = current.T
        for (key, value) in self.listp.items():
            self.result.append((T(key), value))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        """ @todo: docstring """

        self.cnt = 0
        self.list = {}
        for answer in self.valueList:
            self.cnt += 1
            if answer in self.list:
                self.list[answer] += 1
            else:
                self.list[answer] = 1
        self.listp = {}
        if self.cnt != 0:
            for (key, value) in self.list.items():
                self.listp[key] = "%3.1f%%" % round((100.0 * value) / self.cnt, 1)

    # -------------------------------------------------------------------------
    def drawChart(self,
                  series_id,
                  output="xml",
                  data=None,
                  label=None,
                  xLabel=None,
                  yLabel=None):
        """ @todo: docstring """

        chartFile = self.getChartName(series_id)
        cached = S3Chart.getCachedFile(chartFile)
        if cached:
            return cached

        chart = S3Chart(path=chartFile)
        data = []
        label = []
        for (key, value) in self.list.items():
            data.append(value)
            label.append(key)
        chart.survey_pie(self.qstnWidget.question.name,
                         data,
                         label)
        image = chart.draw(output=output)
        return image

# =============================================================================
class S3OptionYNAnalysis(S3OptionAnalysis):
    """ @todo: docstring """

    # -------------------------------------------------------------------------
    def summary(self):
        """ @todo: docstring """

        T = current.T
        self.result.append((T("Yes"), self.yesp))
        self.result.append((T("No"), self.nop))
        return self.format()


    # -------------------------------------------------------------------------
    def basicResults(self):
        """ @todo: docstring """

        S3OptionAnalysis.basicResults(self)
        T = current.T
        if "Yes" in self.listp:
            self.yesp = self.listp["Yes"]
        else:
            if self.cnt == 0:
                self.yesp = "" # No replies so can't give a percentage
            else:
                self.list["Yes"] = 0
                self.yesp = T("0%")
        if "No" in self.listp:
            self.nop = self.listp["No"]
        else:
            if self.cnt == 0:
                self.nop = "" # No replies so can't give a percentage
            else:
                self.list["No"] = 0
                self.nop = T("0%")

# =============================================================================
class S3OptionYNDAnalysis(S3OptionAnalysis):
    """ @todo: docstring """

    # -------------------------------------------------------------------------
    def summary(self):
        """ @todo: docstring """

        T = current.T
        self.result.append((T("Yes"), self.yesp))
        self.result.append((T("No"), self.nop))
        self.result.append((T("Don't Know"), self.dkp))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        """ @todo: docstring """

        S3OptionAnalysis.basicResults(self)
        T = current.T
        if "Yes" in self.listp:
            self.yesp = self.listp["Yes"]
        else:
            if self.cnt == 0:
                self.yesp = "" # No replies so can't give a percentage
            else:
                self.list["Yes"] = 0
                self.yesp = T("0%")
        if "No" in self.listp:
            self.nop = self.listp["No"]
        else:
            if self.cnt == 0:
                self.nop = "" # No replies so can't give a percentage
            else:
                self.list["No"] = 0
                self.nop = T("0%")
        if "Don't Know" in self.listp:
            self.dkp = self.listp["Don't Know"]
        else:
            if self.cnt == 0:
                self.dkp = "" # No replies so can't give a percentage
            else:
                self.list["Don't Know"] = 0
                self.dkp = T("0%")

# =============================================================================
class S3OptionOtherAnalysis(S3OptionAnalysis):
    """
        @todo: docstring
        @todo: remove if not needed
    """

    pass

# =============================================================================
class S3MultiOptionAnalysis(S3OptionAnalysis):
    """ @todo: docstring """

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        """
            Used to modify the answer from its raw text format.
            Where necessary, this function will be overridden.
        """

        valueList = json2list(answer)
        return valueList

    # -------------------------------------------------------------------------
    def basicResults(self):
        """ @todo: docstring """

        self.cnt = 0
        self.list = {}
        for answer in self.valueList:
            if isinstance(answer, list):
                answerList = answer
            else:
                answerList = [answer]
            self.cnt += 1
            for answer in answerList:
                if answer in self.list:
                    self.list[answer] += 1
                else:
                    self.list[answer] = 1
        self.listp = {}
        if self.cnt != 0:
            for (key, value) in self.list.items():
                self.listp[key] = "%s%%" %((100 * value) / self.cnt)

    # -------------------------------------------------------------------------
    def drawChart(self,
                  series_id,
                  output="xml",
                  data=None,
                  label=None,
                  xLabel=None,
                  yLabel=None):
        """ @todo: docstring """

        chartFile = self.getChartName(series_id)
        cached = S3Chart.getCachedFile(chartFile)
        if cached:
            return cached

        chart = S3Chart(path=chartFile)
        data = []
        label = []
        for (key, value) in self.list.items():
            data.append(value)
            label.append(key)
        chart.survey_bar(self.qstnWidget.question.name,
                         data,
                         label,
                         None
                         )
        image = chart.draw(output=output)
        return image

# =============================================================================
class S3LocationAnalysis(S3AbstractAnalysis):
    """
        Widget for analysing Location type questions

        The analysis will compare the location values provided with
        data held on the gis_location table.

        The data held can be in its raw form (the actual value imported) or
        in a more refined state, which may include the actual location id
        held on the database or an alternative value which is a string.

        The raw value may be a local name for the place whilst the altervative
        value should be the actual value held on the database.
        The alternative value is useful for matching duplicate responses that
        are using the same local name.
    """

    # -------------------------------------------------------------------------
    def castRawAnswer(self, complete_id, answer):
        """
            Convert the answer for the complete_id into a database record.

            This can have one of three type of return values.
            A single record: The actual location
            Multiple records: The set of location, on of which is the location
            None: No match is found on the database.
        """

        records = self.qstnWidget.getLocationRecord(complete_id, answer)
        return records

    # -------------------------------------------------------------------------
    def summary(self):
        """
            Returns a summary table
        """

        T = current.T
        self.result.append((T("Known Locations"), self.kcnt))
        self.result.append((T("Duplicate Locations"), self.dcnt))
        self.result.append((T("Unknown Locations"), self.ucnt))
        return self.format()

    # -------------------------------------------------------------------------
    def count(self):
        """
            Returns a table of basic results
        """

        T = current.T
        self.result.append((T("Total Locations"), len(self.valueList)))
        self.result.append((T("Unique Locations"), self.cnt))
        return self.format()

    # -------------------------------------------------------------------------
    def basicResults(self):
        """
            Calculate the basic results, which consists of a number of list
            related to the locations

            LISTS (dictionaries)
            ====================
            All maps are keyed on the value used in the database lookup
            locationList - holding the number of times the value exists
            complete_id  - a list of complete_id at this location
            duplicates   - a list of duplicate records
            known        - The record from the database

            Calculated Values
            =================
            cnt  - The number of unique locations
            dcnt - The number of locations with duplicate values
            kcnt - The number of known locations (single match on the database)
            ucnt - The number of unknown locations
            dper - The percentage of locations with duplicate values
            kper - The percentage of known locations
            NOTE: Percentages are calculated from the unique locations
                  and not from the total responses.
        """

        self.locationList = {}
        self.duplicates = {}
        self.known = {}
        self.complete_id = {}
        for answer in self.valueList:
            if answer != None:
                key = answer.key
                if key in self.locationList:
                    self.locationList[key] += 1
                else:
                    self.locationList[key] = 1
                    if key in self.complete_id:
                        self.complete_id[key].append(answer.complete_id)
                    else:
                        self.complete_id[key] = [answer.complete_id]
                    result = answer.records
                    if len(result) > 1:
                        self.duplicates[key] = result
                    if len(result) == 1:
                        self.known[key] = result[0]
        self.cnt = len(self.locationList)
        self.dcnt = len(self.duplicates)
        self.kcnt = len(self.known)
        if self.cnt == 0:
            self.dper = "0%%"
            self.kper = "0%%"
        else:
            self.dper = "%s%%" %((100 * self.dcnt) / self.cnt)
            self.kper = "%s%%" %((100 * self.kcnt) / self.cnt)
        self.ucnt = self.cnt - self.kcnt - self.dcnt

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        """
            Ensures that no button is set up

            @todo: use a class property rather than calling just to get a None
        """

        return None

    # -------------------------------------------------------------------------
    def uniqueCount(self):
        """
            Calculate the number of occurances of each value
        """

        map = {}
        for answer in self.valueList:
            if answer.key in map:
                map[answer.key] += 1
            else:
                map[answer.key] = 1
        return map

# =============================================================================
class S3LinkAnalysis(S3AbstractAnalysis):
    """ @todo: docstring """

    def __init__(self, type, question_id, answerList):
        """ @todo: docstring """

        S3AbstractAnalysis.__init__(self, type, question_id, answerList)
        linkWidget = S3QuestionTypeLinkWidget(question_id)
        parent = linkWidget.get("Parent")
        relation = linkWidget.get("Relation")
        type = linkWidget.get("Type")
        parent_qid = linkWidget.getParentQstnID()
        valueMap = {}
        for answer in self.answerList:
            complete_id = answer["complete_id"]
            parent_answer = linkWidget.loadAnswer(complete_id,
                                                  parent_qid,
                                                  forceDB=True
                                                  )
            if relation == "groupby":
                # @todo: check for different values
                valueMap.update({parent_answer:answer})
        valueList = []
        for answer in valueMap.values():
            valueList.append(answer)
        self.widget = survey_analysis_type[type](question_id, valueList)

    # -------------------------------------------------------------------------
    def summary(self):
        """ @todo: docstring """

        return self.widget.summary()

    # -------------------------------------------------------------------------
    def count(self):
        """ @todo: docstring """

        return self.widget.count()

    # -------------------------------------------------------------------------
    def chartButton(self, series_id):
        """ @todo: docstring """

        return self.widget.chartButton(series_id)

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        """ @todo: docstring """

        return self.widget.filter(filterType, groupedData)

    # -------------------------------------------------------------------------
    def drawChart(self,
                  series_id,
                  output="xml",
                  data=None,
                  label=None,
                  xLabel=None,
                  yLabel=None):
        """ @todo: docstring """

        return self.widget.drawChart(data, series_id, label, xLabel, yLabel)

# =============================================================================
class S3GridAnalysis(S3AbstractAnalysis):
    """
        @todo: docstring
        @todo: remove if not needed
    """

    pass

# =============================================================================
class S3GridChildAnalysis(S3AbstractAnalysis):
    """ @todo: docstring """

    def __init__(self, type, question_id, answerList):
        """ @todo: docstring """

        S3AbstractAnalysis.__init__(self, type, question_id, answerList)
        childWidget = S3QuestionTypeLinkWidget(question_id)
        trueType = childWidget.get("Type")
        for answer in self.answerList:
            if self.valid(answer):
                try:
                    self.valueList.append(trueType.castRawAnswer(answer["complete_id"],
                                                                 answer["value"]))
                except:
                    pass
        self.widget = survey_analysis_type[trueType](question_id, self.answerList)

    # -------------------------------------------------------------------------
    def drawChart(self,
                  series_id,
                  output="xml",
                  data=None,
                  label=None,
                  xLabel=None,
                  yLabel=None):
        """ @todo: docstring """

        return self.widget.drawChart(series_id, output, data, label, xLabel, yLabel)

    # -------------------------------------------------------------------------
    def filter(self, filterType, groupedData):
        """ @todo: docstring """

        return self.widget.filter(filterType, groupedData)

# =============================================================================
# Utilities
#
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

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
def survey_T(phrase, langDict):
    """
        Function to translate a phrase using the dictionary passed in

        @todo: parameter description
    """

    if phrase in langDict and langDict[phrase] != "":
        return langDict[phrase]
    else:
        return phrase

# END =========================================================================
