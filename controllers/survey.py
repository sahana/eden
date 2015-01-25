# -*- coding: utf-8 -*-

"""
    survey - Assessment Data Analysis Tool

    For more details see the blueprint at:
    http://eden.sahanafoundation.org/wiki/BluePrint/SurveyTool/ADAT

    @todo: open template from the dataTables into the section tab not update
    @todo: in the pages that add a link to a template make the combobox display the label not the numbers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from gluon.contenttype import contenttype

from s3survey import S3AnalysisPriority, \
                     survey_question_type, \
                     survey_analysis_type, \
                     getMatrix, \
                     DEBUG, \
                     LayoutBlocks, \
                     DataMatrix, MatrixElement, \
                     S3QuestionTypeOptionWidget, \
                     survey_T

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """
        Enter a new assessment.
        - provides a simpler URL to access from mobile devices...
    """

    redirect(URL(f="newAssessment",
                 vars={"viewing": "survey_series.%s" % request.args[0]}))

# -----------------------------------------------------------------------------
def template():
    """ RESTful CRUD controller """

    # Load Model
    #table = s3db.survey_template

    def prep(r):
        if r.component:
            if r.component_name == "translate":
                table = s3db.survey_translate
                if r.component_id == None:
                    # list existing translations and allow the addition of a new translation
                    table.file.readable = False
                    table.file.writable = False
                else:
                    # edit the selected translation
                    table.language.writable = False
                    table.code.writable = False
                # remove CRUD generated buttons in the tabs
                s3db.configure("survey_translate",
                               deletable=False)
        else:
            table = r.table
            s3_action_buttons(r)
            # Status of Pending
            rows = db(table.status == 1).select(table.id)
            try:
                s3.actions[1]["restrict"].extend(str(row.id) for row in rows)
            except KeyError: # the restrict key doesn't exist
                s3.actions[1]["restrict"] = [str(row.id) for row in rows]
            except IndexError: # the delete buttons doesn't exist
                pass
            # Add some highlighting to the rows
            # Status of Pending
            s3.dataTableStyleAlert = [str(row.id) for row in rows]
            # Status of closed
            rows = db(table.status == 3).select(table.id)
            s3.dataTableStyleDisabled = [str(row.id) for row in rows]
            s3.dataTableStyleWarning = [str(row.id) for row in rows]
            # Status of Master
            rows = db(table.status == 4).select(table.id)
            s3.dataTableStyleWarning.extend(str(row.id) for row in rows)
            s3db.configure("survey_template",
                           orderby = "survey_template.status",
                           create_next = URL(c="survey", f="template"),
                           update_next = URL(c="survey", f="template"),
                           )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.component:
            template_id = r.id
            if r.component_name == "translate":
                s3_action_buttons(r)
                s3.actions.append(dict(label=str(T("Download")),
                                       _class="action-btn",
                                       url=r.url(method = "translate_download",
                                                 component = "translate",
                                                 component_id = "[id]",
                                                 representation = "xls",
                                                 )
                                       ),
                                  )
                s3.actions.append(
                           dict(label=str(T("Upload")),
                                _class="action-btn",
                                url=URL(c=module,
                                        f="template",
                                        args=[template_id, "translate", "[id]"])
                               ),
                          )
            #elif r.component_name == "section":
            #    # Add the section select widget to the form
            #    # undefined
            #    sectionSelect = s3.survey_section_select_widget(template_id)
            #    output.update(form = sectionSelect)

        # Add a button to show what the questionnaire looks like
        #s3_action_buttons(r)
        #s3.actions = s3.actions + [
        #                       dict(label=str(T("Display")),
        #                            _class="action-btn",
        #                            url=URL(c=module,
        #                                    f="templateRead",
        #                                    args=["[id]"])
        #                           ),
        #                      ]

        return output
    s3.postp = postp

    if request.ajax:
        post = request.post_vars
        action = post.get("action")
        template_id = post.get("parent_id")
        section_id = post.get("section_id")
        section_text = post.get("section_text")
        if action == "section" and template_id != None:
            id = db.survey_section.insert(name=section_text,
                                          template_id=template_id,
                                          cloned_section_id=section_id)
            if id is None:
                print "Failed to insert record"
            return

    # Remove CRUD generated buttons in the tabs
    s3db.configure("survey_template",
                   listadd=False,
                   #deletable=False,
                   )

    output = s3_rest_controller(rheader=s3db.survey_template_rheader)
    return output

# -----------------------------------------------------------------------------
def templateRead():
    """
    """

    if len(get_vars) > 0:
        dummy, template_id = get_vars.viewing.split(".")
    else:
        template_id = request.args[0]

    def postp(r, output):
        if r.interactive:
            template_id = r.id
            form = s3db.survey_buildQuestionnaireFromTemplate(template_id)
            output["items"] = None
            output["form"] = None
            output["item"] = form
            output["title"] = s3.crud_strings["survey_template"].title_question_details
            return output
    s3.postp = postp

    # remove CRUD generated buttons in the tabs
    s3db.configure("survey_template",
                   listadd=False,
                   editable=False,
                   deletable=False,
                   )

    r = s3_request("survey", "template", args=[template_id])
    output  = r(method = "read", rheader=s3db.survey_template_rheader)
    return output

# -----------------------------------------------------------------------------
def templateSummary():
    """
    """

    # Load Model
    tablename = "survey_template"
    s3db[tablename]
    s3db.survey_complete
    crud_strings = s3.crud_strings[tablename]

    def postp(r, output):
        if r.interactive:
            if len(get_vars) > 0:
                dummy, template_id = get_vars.viewing.split(".")
            else:
                template_id = r.id
            form = s3db.survey_build_template_summary(template_id)
            output["items"] = form
            output["sortby"] = [[0, "asc"]]
            output["title"] = crud_strings.title_analysis_summary
            output["subtitle"] = crud_strings.subtitle_analysis_summary
        return output
    s3.postp = postp

    # remove CRUD generated buttons in the tabs
    s3db.configure(tablename,
                   listadd=False,
                   deletable=False,
                   )

    output = s3_rest_controller("survey", "template",
                                method = "list",
                                rheader=s3.survey_template_rheader
                                )
    s3.actions = None
    return output

# -----------------------------------------------------------------------------
def series():
    """ RESTful CRUD controller """

    # Load Model
    table = s3db.survey_series
    s3db.survey_answerlist_dataTable_pre()

    def prep(r):
        if r.interactive:
            if r.method == "create":
                ttable = s3db.survey_template
                if not db(ttable.deleted == False).select(ttable.id,
                                                          limitby=(0, 1)
                                                          ):
                    session.warning = T("You need to create a template before you can create a series")
                    redirect(URL(c="survey", f="template", args=[], vars={}))
            if r.id and (r.method == "update"):
                table.template_id.writable = False
        return True
    s3.prep = prep

    def postp(r, output):
        if request.ajax == True and r.method == "read":
            return output["item"]
        if not r.component:
            # Set the minimum end_date to the same as the start_date
            s3.jquery_ready.append(
'''S3.start_end_date('survey_series_start_date','survey_series_end_date')''')
            s3db.survey_serieslist_dataTable_post(r)

        elif r.component_name == "complete":
            if r.method == "update":
                if r.http == "GET":
                    form = s3db.survey_buildQuestionnaireFromSeries(r.id,
                                                                    r.component_id)
                    output["form"] = form
                elif r.http == "POST":
                    if len(request.post_vars) > 0:
                        id = s3db.survey_save_answers_for_series(r.id,
                                                                 r.component_id, # Update
                                                                 request.post_vars)
                        response.confirmation = \
                            s3.crud_strings["survey_complete"].msg_record_modified
            else:
                s3db.survey_answerlist_dataTable_post(r)
        return output
    s3.postp = postp

    # Remove CRUD generated buttons in the tabs
    s3db.configure("survey_series",
                   deletable = False,
                   )
    s3db.configure("survey_complete",
                   listadd = False,
                   deletable = False,
                   )

    output = s3_rest_controller(rheader=s3db.survey_series_rheader)
    return output

# -----------------------------------------------------------------------------
def completed_chart():
    """
        Allows the user to display all the data from the selected question
        in a simple chart. If the data is numeric then a histogram will be
        drawn if it is an option type then a pie chart, although the type of
        chart drawn is managed by the analysis widget.
    """

    series_id = get_vars.get("series_id")
    if not series_id:
        return "Programming Error: Series ID missing"

    question_id = get_vars.get("question_id")
    if not question_id:
        return "Programming Error: Question ID missing"

    q_type = get_vars.get("type")
    if not q_type:
        return "Programming Error: Question Type missing"

    getAnswers = s3db.survey_getAllAnswersForQuestionInSeries
    answers = getAnswers(question_id, series_id)
    analysisTool = survey_analysis_type[q_type](question_id, answers)
    qstnName = analysisTool.qstnWidget.question.name
    image = analysisTool.drawChart(series_id, output="png")
    return image

# -----------------------------------------------------------------------------
def section():
    """
        RESTful CRUD controller
        - unused
    """

    # Load Model
    #table = s3db.survey_section

    def prep(r):
        s3db.configure(r.tablename,
                       deletable = False,
                       orderby = "%s.posn" % r.tablename,
                       )
        return True
    s3.prep = prep

     # Post-processor
    def postp(r, output):
        """ Add the section select widget to the form """
        try:
            template_id = int(request.args[0])
        except:
            template_id = None
        # Undefined?
        sectionSelect = s3.survey_section_select_widget(template_id)
        output["sectionSelect"] = sectionSelect
        return output
    #s3.postp = postp

    output = s3_rest_controller(# Undefined
                                #rheader=s3db.survey_section_rheader
                                )
    return output

# -----------------------------------------------------------------------------
def question():
    """ RESTful CRUD controller """

    def prep(r):
        s3db.configure(r.tablename,
                       orderby = r.tablename + ".posn",
                       )
        return True
    s3.prep = prep

    output = s3_rest_controller(# Undefined
                                #rheader=s3db.survey_section_rheader
                                )
    return output

# -----------------------------------------------------------------------------
def question_list():
    """ RESTful CRUD controller """

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def formatter():
    """ RESTful CRUD controller """

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def question_metadata():
    """ RESTful CRUD controller """

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def newAssessment():
    """
        RESTful CRUD controller to create a new 'complete' survey
        - although the created form is a fully custom one
    """

    # Load Model
    table = s3db.survey_complete
    s3db.table("survey_series")

    def prep(r):
        if r.interactive:
            viewing = get_vars.get("viewing", None)
            if viewing:
                dummy, series_id = viewing.split(".")
            else:
                series_id = get_vars.get("series", None)

            if not series_id:
                series_id = r.id
            if series_id is None:
                # The URL is bad, without a series id we're lost so list all series
                redirect(URL(c="survey", f="series", args=[], vars={}))
            if len(request.post_vars) > 0:
                id = s3db.survey_save_answers_for_series(series_id,
                                                         None, # Insert
                                                         request.post_vars)
                response.confirmation = \
                    s3.crud_strings["survey_complete"].msg_record_created
            r.method = "create"
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            # Not sure why we need to repeat this & can't do it outside the prep/postp
            viewing = get_vars.get("viewing", None)
            if viewing:
                dummy, series_id = viewing.split(".")
            else:
                series_id = get_vars.get("series", None)

            if not series_id:
                series_id = r.id
            if output["form"] is None:
                # The user is not authorised to create so switch to read
                redirect(URL(c="survey", f="series",
                             args=[series_id, "read"],
                             vars={}))
            # This is a bespoke form which confuses CRUD, which displays an
            # error "Invalid form (re-opened in another window?)"
            # So so long as we don't have an error in the form we can
            # delete this error.
            elif response.error and not output["form"]["error"]:
                response.error = None
            s3db.survey_answerlist_dataTable_post(r)
            form = s3db.survey_buildQuestionnaireFromSeries(series_id, None)
            urlimport = URL(c=module, f="complete", args=["import"],
                            vars={"viewing":"%s.%s" % ("survey_series", series_id),
                                  "single_pass":True}
                            )
            buttons = DIV(A(T("Upload Completed Assessment Form"),
                            _href=urlimport,
                            _id="Excel-import",
                            _class="action-btn"
                            ),
                          )
            output["subtitle"] = buttons
            output["form"] = form
        return output
    s3.postp = postp

    output = s3_rest_controller(module, "complete",
                                method = "create",
                                rheader = s3db.survey_series_rheader
                                )
    return output

# -----------------------------------------------------------------------------
def complete():
    """ RESTful CRUD controller """

    # Load Model
    table = s3db.survey_complete
    stable = s3db.survey_series
    s3db.survey_answerlist_dataTable_pre()

    series_id = None
    try:
        viewing = get_vars.get("viewing", None)
        if viewing:
            dummy, series_id = viewing.split(".")
            series = db(stable.id == series_id).select(stable.name,
                                                       limitby=(0, 1)
                                                       ).first()
            if series:
                series_name = series.name
            else:
                series_name = ""
        if series_name != "":
            csv_extra_fields = [dict(label="Series", value=series_name)]
        else:
            csv_extra_fields = []
    except:
        csv_extra_fields = []

    def postp(r, output):
        if r.method == "import":
            pass # don't want the import dataTable to be modified
        else:
            s3db.survey_answerlist_dataTable_post(r)
        return output
    s3.postp = postp

    def import_xls(uploadFile):
        """
            Import Assessment Spreadsheet
        """

        if series_id is None:
            response.error = T("Series details missing")
            return
        openFile = StringIO()
        try:
            import xlrd
            from xlwt.Utils import cell_to_rowcol2
        except ImportError:
            current.log.error("ERROR: xlrd & xlwt modules are needed for importing spreadsheets")
            return None
        workbook = xlrd.open_workbook(file_contents=uploadFile)
        try:
            sheetR = workbook.sheet_by_name("Assessment")
            sheetM = workbook.sheet_by_name("Metadata")
        except:
            session.error = T("You need to use the spreadsheet which you can download from this page")
            redirect(URL(c="survey", f="newAssessment", args=[],
                         vars={"viewing": "survey_series.%s" % series_id}))
        header = ""
        body = ""
        for row in xrange(1, sheetM.nrows):
            header += ',"%s"' % sheetM.cell_value(row, 0)
            code = sheetM.cell_value(row, 0)
            qstn = s3.survey_getQuestionFromCode(code, series_id)
            type = qstn["type"]
            count = sheetM.cell_value(row, 1)
            if count != "":
                count = int(count)
                optionList = sheetM.cell_value(row, 2).split("|#|")
            else:
                count = 1
                optionList = None
            if type == "Location" and optionList != None:
                answerList = {}
            elif type == "MultiOption":
                answerList = []
            else:
                answerList = ""
            for col in range(count):
                cell = sheetM.cell_value(row, 3 + col)
                (rowR, colR) = cell_to_rowcol2(cell)
                try:
                    cellValue = sheetR.cell_value(rowR, colR)
                except IndexError:
                    cellValue = ""
                # BUG: The option list needs to work in different ways
                # depending on the question type. The question type should
                # be added to the spreadsheet to save extra db calls:
                # * Location save all the data as a hierarchy
                # * MultiOption save all selections
                # * Option save the last selection
                if cellValue != "":
                    if optionList != None:
                        if type == "Location":
                            answerList[optionList[col]]=cellValue
                        elif type == "MultiOption":
                            answerList.append(optionList[col])
                        else:
                            answerList = optionList[col]
                    else:
                        if type == "Date":
                            try:
                                (dtYear, dtMonth, dtDay, dtHour, dtMinute, dtSecond) = \
                                         xlrd.xldate_as_tuple(cellValue,
                                                              workbook.datemode)
                                dtValue = datetime.date(dtYear, dtMonth, dtDay)
                                cellValue = dtValue.isoformat()
                            except:
                                pass
                        elif type == "Time":
                            try:
                                time = cellValue
                                hour = int(time * 24)
                                minute = int((time * 24 - hour) * 60)
                                cellValue = "%s:%s" % (hour, minute)
                            except:
                                pass
                        answerList += "%s" % cellValue
            body += ',"%s"' % answerList
        openFile.write(header)
        openFile.write("\n")
        openFile.write(body)
        openFile.seek(0)
        return openFile

    s3db.configure("survey_complete",
                   listadd=False,
                   deletable=False)

    s3.xls_parser = import_xls

    output = s3_rest_controller(csv_extra_fields = csv_extra_fields)
    return output

# -----------------------------------------------------------------------------
def answer():
    """ RESTful CRUD controller """

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def analysis():
    """
        RESTful CRUD controller
        - for Completed Answers
        - not editable (just for analysis)
    """

    s3db.configure("survey_complete",
                   deletable = False,
                   listadd = False,
                   )

    output = s3_rest_controller(module, "complete")
    return output

# -----------------------------------------------------------------------------
def admin():
    """ Custom Page """

    series_id = None
    get_vars_new = Storage()
    try:
        series_id = int(request.args[0])
    except:
        try:
            (dummy, series_id) = get_vars["viewing"].split(".")
            series_id = int(series_id)
        except:
            pass
    if series_id:
        get_vars_new.viewing = "survey_complete.%s" % series_id

    return dict(series_id = series_id,
                vars = get_vars_new)

# END =========================================================================
