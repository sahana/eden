# -*- coding: utf-8 -*-

"""
    survey - Assessment Data Analysis Tool

    For more details see the blueprint at:
    http://eden.sahanafoundation.org/wiki/BluePrint/SurveyTool/ADAT

    @todo: open template from the dataTables into the section tab not update
    @todo: in the pages that add a link to a template make the combobox display the label not the numbers
    @todo: restrict the deletion of a template to only those with status Pending
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
def template():
    """ RESTful CRUD controller """

    # Load Model
    table = s3db.survey_template

    def prep(r):
        if r.component and r.component_name == "translate":
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
            s3db.configure(table,
                            deletable=False)
        else:
            s3_action_buttons(r)
            query = (r.table.status == 1) # Status of Pending
            rows = db(query).select(r.table.id)
            try:
                s3.actions[1]["restrict"].extend(str(row.id) for row in rows)
            except KeyError: # the restrict key doesn't exist
                s3.actions[1]["restrict"] = [str(row.id) for row in rows]
            except IndexError: # the delete buttons doesn't exist
                pass
            # Add some highlighting to the rows
            query = (r.table.status == 3) # Status of closed
            rows = db(query).select(r.table.id)
            s3.dataTableStyleDisabled = [str(row.id) for row in rows]
            s3.dataTableStyleWarning = [str(row.id) for row in rows]
            query = (r.table.status == 1) # Status of Pending
            rows = db(query).select(r.table.id)
            s3.dataTableStyleAlert = [str(row.id) for row in rows]
            query = (r.table.status == 4) # Status of Master
            rows = db(query).select(r.table.id)
            s3.dataTableStyleWarning.extend(str(row.id) for row in rows)
            s3db.configure(r.tablename,
                            orderby = "%s.status" % r.tablename,
                            create_next = URL(c="survey", f="template"),
                            update_next = URL(c="survey", f="template"),
                            )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.component:
            template_id = request.args[0]
            if r.component_name == "section":
                # Add the section select widget to the form
                # Where is this defined?
                sectionSelect = s3.survey_section_select_widget(template_id)
                output.update(form = sectionSelect)
                return output
            elif r.component_name == "translate":
                s3_action_buttons(r)
                s3.actions.append(
                                   dict(label=str(T("Download")),
                                        _class="action-btn",
                                        url=URL(c=module,
                                                f="templateTranslateDownload",
                                                args=["[id]"])
                                       ),
                                  )
                s3.actions.append(
                           dict(label=str(T("Upload")),
                                _class="action-btn",
                                url=URL(c=module,
                                        f="template",
                                        args=[template_id,"translate","[id]"])
                               ),
                          )
                return output


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
            if id == None:
                print "Failed to insert record"
            return

    # remove CRUD generated buttons in the tabs
    s3db.configure("survey_template",
                    listadd=False,
                    deletable=False,
                   )
    output = s3_rest_controller(rheader=s3db.survey_template_rheader)

    return output

# -----------------------------------------------------------------------------
def templateRead():
    """
    """

    if "vars" in request and len(request.vars) > 0:
        dummy, template_id = request.vars.viewing.split(".")
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
    resourcename = "template"
    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)
    s3db.table("survey_complete")
    crud_strings = s3.crud_strings[tablename]

    def postp(r, output):
        if r.interactive:
            if "vars" in request and len(request.vars) > 0:
                dummy, template_id = request.vars.viewing.split(".")
            else:
                template_id = r.id
            form = s3.survey_build_template_summary(template_id)
            output["items"] = form
            output["sortby"] = [[0, "asc"]]
            output["title"] = crud_strings.title_analysis_summary
            output["subtitle"] = crud_strings.subtitle_analysis_summary
            return output

    # remove CRUD generated buttons in the tabs
    s3db.configure(tablename,
                    listadd=False,
                    deletable=False,
                   )

    s3.postp = postp
    output = s3_rest_controller(module,
                                resourcename,
                                method = "list",
                                rheader=s3.survey_template_rheader
                               )
    s3.actions = None
    return output

# -----------------------------------------------------------------------------
def templateTranslateDownload():
    """
    """

    # Load Model
    resourcename = "translate"
    tablename = "%s_%s" % (module, resourcename)
    s3db.table("survey_template")
    s3db.table("survey_translate")
    s3db.table("survey_complete")

    try:
        import xlwt
    except ImportError:
        redirect(URL(c="survey",
                     f="templateTranslation",
                     args=[],
                     vars = {}))
    record = s3.survey_getTranslation(request.args[0])
    if record == None:
        redirect(URL(c="survey",
                     f="templateTranslation",
                     args=[],
                     vars = {}))
    code = record.code
    language = record.language
    lang_fileName = "applications/%s/languages/%s.py" % \
                                    (appname, code)
    try:
        from gluon.languages import read_dict
        strings = read_dict(lang_fileName)
    except:
        strings = dict()
    template_id = record.template_id
    template = s3.survey_getTemplate(template_id)
    book = xlwt.Workbook(encoding="utf-8")
    sheet = book.add_sheet(language)
    output = StringIO()
    qstnList = s3.survey_getAllQuestionsForTemplate(template_id)
    original = {}
    original[template["name"]] = True
    if template["description"] != "":
        original[template["description"]] = True
    for qstn in qstnList:
        original[qstn["name"]] = True
        widgetObj = survey_question_type[qstn["type"]](question_id = qstn["qstn_id"])
        if isinstance(widgetObj, S3QuestionTypeOptionWidget):
            optionList = widgetObj.getList()
            for option in optionList:
                original[option] = True
    sections = s3.survey_getAllSectionsForTemplate(template_id)
    for section in sections:
        original[section["name"]]=True
        section_id = section["section_id"]
        layoutRules = s3.survey_getQstnLayoutRules(template_id, section_id)
        layoutStr = str(layoutRules)
        posn = layoutStr.find("heading")
        while posn != -1:
            start = posn + 11
            end = layoutStr.find("}", start)
            original[layoutStr[start:end]] = True
            posn = layoutStr.find("heading", end)

    row = 0
    sheet.write(row,
                0,
                unicode("Original")
               )
    sheet.write(row,
                1,
                unicode("Translation")
               )
    originalList = original.keys()
    originalList.sort()
    for text in originalList:
        row += 1
        original = unicode(text)
        sheet.write(row,
                    0,
                    original
                   )
        if (original in strings):
            sheet.write(row,
                        1,
                        strings[original]
                       )

    book.save(output)
    output.seek(0)
    response.headers["Content-Type"] = contenttype(".xls")
    filename = "%s.xls" % code
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

# -----------------------------------------------------------------------------
def series():
    """ RESTful CRUD controller """

    # Load Model
    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]
    s3.survey_answerlist_dataTable_pre()

    def prep(r):
        if r.interactive:
            if r.method == "create":
                allTemplates = s3.survey_getAllTemplates()
                if len(allTemplates) == 0:
                    session.warning = T("You need to create a template before you can create a series")
                    redirect(URL(c="survey",
                             f="template",
                             args=[],
                             vars = {}))
            if r.id and (r.method == "update"):
                table.template_id.writable = False
        return True

    def postp(r, output):
        if request.ajax == True and r.method == "read":
            return output["item"]
        if r.component_name == None:
            s3.survey_serieslist_dataTable_post(r)
        elif r.component_name == "complete":
            if r.method == "update":
                if r.http == "GET":
                    form = s3.survey_buildQuestionnaireFromSeries(r.id,
                                                                  r.component_id)
                    output["form"] = form
                elif r.http == "POST":
                    if "post_vars" in request and len(request.post_vars) > 0:
                        id = s3.survey_save_answers_for_series(r.id,
                                                               r.component_id, # Update
                                                               request.post_vars)
                        response.flash = s3.crud_strings["survey_complete"].msg_record_modified
            else:
                s3.survey_answerlist_dataTable_post(r)
        return output

    # Remove CRUD generated buttons in the tabs
    s3db.configure("survey_series",
                    deletable = False,)
    s3db.configure("survey_complete",
                    listadd=False,
                    deletable=False)
    s3.prep = prep
    s3.postp = postp
    output = s3_rest_controller(module,
                                resourcename,
                                rheader=s3.survey_series_rheader)
    return output

# -----------------------------------------------------------------------------
def export_all_responses():
    """
    """

    s3db.table("survey_series")
    s3db.table("survey_section")
    s3db.table("survey_complete")
    # turn off lazy translation
    # otherwise xlwt will crash if it comes across a T string
    T.lazy = False
    try:
        import xlwt
    except ImportError:
        output = s3_rest_controller("survey",
                                    "series",
                                    rheader=s3.survey_series_rheader)
        return output
    series_id = request.args[0]
    seriesName = s3.survey_getSeriesName(series_id)
    sectionBreak = False

    filename = "%s_All_responses.xls" % seriesName
    contentType = ".xls"
    output = StringIO()
    book = xlwt.Workbook(encoding="utf-8")
    # get all questions and write out as a heading
    col = 0
    completeRow = {}
    nextRow = 2
    qstnList = s3.survey_getAllQuestionsForSeries(series_id)
    if len(qstnList) > 256:
        sectionList = s3.survey_getAllSectionsForSeries(series_id)
        sectionBreak = True
    if sectionBreak:
        sheets = {}
        cols = {}
        for section in sectionList:
            sheetName = section["name"].split(" ")[0]
            if sheetName not in sheets:
                sheets[sheetName] = book.add_sheet(sheetName)
                cols[sheetName] = 0
    else:
        sheet = book.add_sheet(T("Responses"))
    for qstn in qstnList:
        if sectionBreak:
            sheetName = qstn["section"].split(" ")[0]
            sheet = sheets[sheetName]
            col = cols[sheetName]
        row = 0
        sheet.write(row,col,qstn["code"])
        row += 1
        widgetObj = s3.survey_getWidgetFromQuestion(qstn["qstn_id"])
        sheet.write(row,col,widgetObj.fullName())
        # for each question get the response
        allResponses = s3.survey_getAllAnswersForQuestionInSeries(qstn["qstn_id"],
                                                                  series_id)
        for answer in allResponses:
            value = answer["value"]
            complete_id = answer["complete_id"]
            if complete_id in completeRow:
                row = completeRow[complete_id]
            else:
                completeRow[complete_id] = nextRow
                row = nextRow
                nextRow += 1
            sheet.write(row,col,value)
        col += 1
        if sectionBreak:
            cols[sheetName] += 1
    sheet.panes_frozen = True
    sheet.horz_split_pos = 2
    book.save(output)

    T.lazy = True
    # turn lazy translation back on
    output.seek(0)
    response.headers["Content-Type"] = contenttype(contentType)
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

# -----------------------------------------------------------------------------
def series_export_formatted():
    """
    """

    s3db.table("survey_series")
    s3db.table("survey_complete")
    # Check that the series_id has been passed in
    if len(request.args) != 1:
        output = s3_rest_controller("survey",
                                    "series",
                                    rheader=s3db.survey_series_rheader)
        return output
    series_id = request.args[0]
    vars = request.post_vars
    seriesName = s3db.survey_getSeriesName(series_id)
    series = s3db.survey_getSeries(series_id)
    if not series.logo:
        logo = None
    else:
        if "Export_Spreadsheet" in vars:
            ext = "bmp"
        else:
            ext = "png"
        logo = os.path.join(request.folder,
                            "uploads",
                            "survey",
                            "logo",
                            "%s.%s" %(series.logo,ext)
                            )
        if not os.path.exists(logo) or not os.path.isfile(logo):
            logo = None
    # Get the translation dictionary
    langDict = dict()
    if "translationLanguage" in request.post_vars:
        lang = request.post_vars.translationLanguage
        if lang == "Default":
            langDict = dict()
        else:
            try:
                from gluon.languages import read_dict
                lang_fileName = "applications/%s/uploads/survey/translations/%s.py" % (appname, lang)
                langDict = read_dict(lang_fileName)
            except:
                langDict = dict()
    if "Export_Spreadsheet" in vars:
        (matrix, matrixAnswers) = series_prepare_matrix(series_id,
                                                        series,
                                                        logo,
                                                        langDict,
                                                        justified = True
                                                       )
        output = series_export_spreadsheet(matrix,
                                           matrixAnswers,
                                           logo,
                                          )
        filename = "%s.xls" % seriesName
        contentType = ".xls"
    elif "Export_Word" in vars:
        template = s3db.survey_getTemplateFromSeries(series_id)
        template_id = template.id
        title = "%s (%s)" % (series.name, template.name)
        title = survey_T(title, langDict)
        widgetList = s3db.survey_getAllWidgetsForTemplate(template_id)
        output = series_export_word(widgetList, langDict, title, logo)
        filename = "%s.rtf" % seriesName
        contentType = ".rtf"
    else:
        output = s3_rest_controller("survey",
                                    "series",
                                    rheader=s3db.survey_series_rheader)
        return output
    output.seek(0)
    response.headers["Content-Type"] = contenttype(contentType)
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

# -----------------------------------------------------------------------------
def series_prepare_matrix(series_id, series, logo, langDict, justified = False):
    """
    """

    ######################################################################
    #
    # Get the data
    # ============
    # * The sections within the template
    # * The layout rules for each question
    ######################################################################
    # Check that the series_id has been passed in
    if len(request.args) != 1:
        output = s3_rest_controller("survey",
                                    "series",
                                    rheader=s3db.survey_series_rheader)
        return output
    series_id = request.args[0]
    template = s3db.survey_getTemplateFromSeries(series_id)
    template_id = template.id
    sectionList = s3db.survey_getAllSectionsForSeries(series_id)
    title = "%s (%s)" % (series.name, template.name)
    title = survey_T(title, langDict)
    layout = []
    survey_getQstnLayoutRules = s3db.survey_getQstnLayoutRules
    for section in sectionList:
        sectionName = survey_T(section["name"], langDict)
        rules = survey_getQstnLayoutRules(template_id,
                                          section["section_id"])
        layoutRules = [sectionName, rules]
        layout.append(layoutRules)
    widgetList = s3db.survey_getAllWidgetsForTemplate(template_id)
    layoutBlocks = LayoutBlocks()

    ######################################################################
    #
    # Store the questions into a matrix based on the layout and the space
    # required for each question - for example an option question might
    # need one row for each possible option, and if this is in a layout
    # then the position needs to be recorded carefully...
    #
    ######################################################################
    preliminaryMatrix = getMatrix(title,
                                  logo,
                                  series,
                                  layout,
                                  widgetList,
                                  False,
                                  langDict,
                                  showSectionLabels = False,
                                  layoutBlocks = layoutBlocks
                                 )
    if not justified:
        return preliminaryMatrix
    ######################################################################
    # Align the questions so that each row takes up the same space.
    # This is done by storing resize and margin instructions with
    # each widget that is being printed
    ######################################################################
    layoutBlocks.align()
    ######################################################################
    # Now rebuild the matrix with the spacing for each widget set up so
    # that the document will be fully justified
    ######################################################################
    layoutBlocks = LayoutBlocks()
    (matrix1, matrix2) = getMatrix(title,
                                   logo,
                                   series,
                                   layout,
                                   widgetList,
                                   True,
                                   langDict,
                                   showSectionLabels = False,
                                  )
    return (matrix1, matrix2)

# -----------------------------------------------------------------------------
def series_export_word(widgetList, langDict, title, logo):
    """
    """

    try:
        from PyRTF import Document, \
                          Languages, \
                          Section, \
                          Image, \
                          Paragraph, \
                          ShadingPropertySet, \
                          ParagraphPropertySet, \
                          StandardColours, \
                          Colour, \
                          Table, \
                          Cell, \
                          Renderer
    except ImportError:
        output = s3_rest_controller(module,
                                    "survey_series",
                                    rheader=s3db.survey_series_rheader)
        return output
    output  = StringIO()
    doc     = Document(default_language=Languages.EnglishUK)
    section = Section()
    ss      = doc.StyleSheet
    ps = ss.ParagraphStyles.Normal.Copy()
    ps.SetName("NormalGrey")
    ps.SetShadingPropertySet(ShadingPropertySet(pattern=1,
                                                background=Colour("grey light", 224, 224, 224)))
    ss.ParagraphStyles.append(ps)
    ps = ss.ParagraphStyles.Normal.Copy()
    ps.SetName("NormalCentre")
    ps.SetParagraphPropertySet(ParagraphPropertySet(alignment=3))
    ss.ParagraphStyles.append(ps)

    doc.Sections.append(section)
    heading = Paragraph(ss.ParagraphStyles.Heading1)

    if logo:
        image = Image(logo)
        heading.append(image)
    heading.append(title)
    section.append(heading)

    col = [2800, 6500]
    table = Table(*col)
    sortedwidgetList = sorted(widgetList.values(), key= lambda widget: widget.question.posn)
    for widget in sortedwidgetList:
        line = widget.writeToRTF(ss, langDict)
        try:
            table.AddRow(*line)
        except:
            if DEBUG:
                raise
            pass
    section.append(table)
    renderer = Renderer()
    renderer.Write(doc, output)
    return output

# -----------------------------------------------------------------------------
def series_export_spreadsheet(matrix, matrixAnswers, logo):
    """
        Now take the matrix data type and generate a spreadsheet from it
    """

    import sys
    import math
    try:
        import xlwt
    except ImportError:
        output = s3_rest_controller(module,
                                    "survey_series",
                                    rheader=s3db.survey_series_rheader)
        return output

    # -------------------------------------------------------------------------
    def wrapText(sheet, cell, style):
        row = cell.row
        col = cell.col
        try:
            text = unicode(cell.text)
        except:
            text = cell.text
        width = 16
        # Wrap text and calculate the row width and height
        characters_in_cell = float(width-2)
        twips_per_row = 255 #default row height for 10 point font
        if cell.merged():
            try:
                sheet.write_merge(cell.row,
                                  cell.row + cell.mergeV,
                                  cell.col,
                                  cell.col + cell.mergeH,
                                  text,
                                  style
                                 )
            except Exception as msg:
                print >> sys.stderr, msg
                print >> sys.stderr, "row: %s + vert: %s, col: %s + horiz %s" % \
                    (cell.row, cell.mergeV, cell.col, cell.mergeH)
                posn = "%s,%s" % (cell.row, cell.col)
                if matrix.matrix[posn]:
                    print >> sys.stderr, matrix.matrix[posn]
            rows = math.ceil((len(text) / characters_in_cell) / (1 + cell.mergeH))
        else:
            sheet.write(cell.row,
                        cell.col,
                        text,
                        style
                       )
            rows = math.ceil(len(text) / characters_in_cell)
        new_row_height = int(rows * twips_per_row)
        new_col_width = width * COL_WIDTH_MULTIPLIER
        if sheet.row(row).height < new_row_height:
            sheet.row(row).height = new_row_height
        if sheet.col(col).width < new_col_width:
            sheet.col(col).width = new_col_width

    # -------------------------------------------------------------------------
    def mergeStyles(listTemplate, styleList):
        """
            Take a list of styles and return a single style object with
            all the differences from a newly created object added to the
            resultant style.
        """
        if len(styleList) == 0:
            finalStyle = xlwt.XFStyle()
        elif len(styleList) == 1:
            finalStyle = listTemplate[styleList[0]]
        else:
            zeroStyle = xlwt.XFStyle()
            finalStyle = xlwt.XFStyle()
            for i in range(0,len(styleList)):
                finalStyle = mergeObjectDiff(finalStyle,
                                             listTemplate[styleList[i]],
                                             zeroStyle)
        return finalStyle

    # -------------------------------------------------------------------------
    def mergeObjectDiff(baseObj, newObj, zeroObj):
        """
            function to copy all the elements in newObj that are different from
            the zeroObj and place them in the baseObj
        """

        elementList = newObj.__dict__
        for (element, value) in elementList.items():
            try:
                baseObj.__dict__[element] = mergeObjectDiff(baseObj.__dict__[element],
                                                            value,
                                                            zeroObj.__dict__[element])
            except:
                if zeroObj.__dict__[element] != value:
                    baseObj.__dict__[element] = value
        return baseObj

    COL_WIDTH_MULTIPLIER = 240
    book = xlwt.Workbook(encoding="utf-8")
    output = StringIO()

    protection = xlwt.Protection()
    protection.cell_locked = 1
    noProtection = xlwt.Protection()
    noProtection.cell_locked = 0

    borders = xlwt.Borders()
    borders.left = xlwt.Borders.DOTTED
    borders.right = xlwt.Borders.DOTTED
    borders.top = xlwt.Borders.DOTTED
    borders.bottom = xlwt.Borders.DOTTED

    borderT1 = xlwt.Borders()
    borderT1.top = xlwt.Borders.THIN
    borderT2 = xlwt.Borders()
    borderT2.top = xlwt.Borders.MEDIUM

    borderL1 = xlwt.Borders()
    borderL1.left = xlwt.Borders.THIN
    borderL2 = xlwt.Borders()
    borderL2.left = xlwt.Borders.MEDIUM

    borderR1 = xlwt.Borders()
    borderR1.right = xlwt.Borders.THIN
    borderR2 = xlwt.Borders()
    borderR2.right = xlwt.Borders.MEDIUM

    borderB1 = xlwt.Borders()
    borderB1.bottom = xlwt.Borders.THIN
    borderB2 = xlwt.Borders()
    borderB2.bottom = xlwt.Borders.MEDIUM

    alignBase = xlwt.Alignment()
    alignBase.horz = xlwt.Alignment.HORZ_LEFT
    alignBase.vert = xlwt.Alignment.VERT_TOP

    alignWrap = xlwt.Alignment()
    alignWrap.horz = xlwt.Alignment.HORZ_LEFT
    alignWrap.vert = xlwt.Alignment.VERT_TOP
    alignWrap.wrap = xlwt.Alignment.WRAP_AT_RIGHT

    shadedFill = xlwt.Pattern()
    shadedFill.pattern = xlwt.Pattern.SOLID_PATTERN
    shadedFill.pattern_fore_colour = 0x16 # 25% Grey
    shadedFill.pattern_back_colour = 0x08 # Black

    headingFill = xlwt.Pattern()
    headingFill.pattern = xlwt.Pattern.SOLID_PATTERN
    headingFill.pattern_fore_colour = 0x1F # ice_blue
    headingFill.pattern_back_colour = 0x08 # Black

    styleTitle =  xlwt.XFStyle()
    styleTitle.font.height = 0x0140 # 320 twips, 16 points
    styleTitle.font.bold = True
    styleTitle.alignment = alignBase
    styleHeader = xlwt.XFStyle()
    styleHeader.font.height = 0x00F0 # 240 twips, 12 points
    styleHeader.font.bold = True
    styleHeader.alignment = alignBase
    styleSubHeader = xlwt.XFStyle()
    styleSubHeader.font.bold = True
    styleSubHeader.alignment = alignWrap
    styleSectionHeading = xlwt.XFStyle()
    styleSectionHeading.font.bold = True
    styleSectionHeading.alignment = alignWrap
    styleSectionHeading.pattern = headingFill
    styleHint = xlwt.XFStyle()
    styleHint.protection = protection
    styleHint.font.height = 160 # 160 twips, 8 points
    styleHint.font.italic = True
    styleHint.alignment = alignWrap
    styleText = xlwt.XFStyle()
    styleText.protection = protection
    styleText.alignment = alignWrap
    styleInstructions = xlwt.XFStyle()
    styleInstructions.font.height = 0x00B4 # 180 twips, 9 points
    styleInstructions.font.italic = True
    styleInstructions.protection = protection
    styleInstructions.alignment = alignWrap
    styleBox = xlwt.XFStyle()
    styleBox.borders = borders
    styleBox.protection = noProtection
    styleInput = xlwt.XFStyle()
    styleInput.borders = borders
    styleInput.protection = noProtection
    styleInput.pattern = shadedFill
    boxL1 = xlwt.XFStyle()
    boxL1.borders = borderL1
    boxL2 = xlwt.XFStyle()
    boxL2.borders = borderL2
    boxT1 = xlwt.XFStyle()
    boxT1.borders = borderT1
    boxT2 = xlwt.XFStyle()
    boxT2.borders = borderT2
    boxR1 = xlwt.XFStyle()
    boxR1.borders = borderR1
    boxR2 = xlwt.XFStyle()
    boxR2.borders = borderR2
    boxB1 = xlwt.XFStyle()
    boxB1.borders = borderB1
    boxB2 = xlwt.XFStyle()
    boxB2.borders = borderB2
    styleList = {}
    styleList["styleTitle"] = styleTitle
    styleList["styleHeader"] = styleHeader
    styleList["styleSubHeader"] = styleSubHeader
    styleList["styleSectionHeading"] = styleSectionHeading
    styleList["styleHint"] = styleHint
    styleList["styleText"] = styleText
    styleList["styleInstructions"] = styleInstructions
    styleList["styleInput"] = styleInput
    styleList["boxL1"] = boxL1
    styleList["boxL2"] = boxL2
    styleList["boxT1"] = boxT1
    styleList["boxT2"] = boxT2
    styleList["boxR1"] = boxR1
    styleList["boxR2"] = boxR2
    styleList["boxB1"] = boxB1
    styleList["boxB2"] = boxB2

    sheet1 = book.add_sheet(T("Assessment"))
    sheetA = book.add_sheet(T("Metadata"))
    maxCol = 0
    for cell in matrix.matrix.values():
        if cell.col + cell.mergeH > 255:
            print >> sys.stderr, "Cell (%s,%s) - (%s,%s) ignored" % \
                (cell.col, cell.row, cell.col + cell.mergeH, cell.row + cell.mergeV)
            continue
        if cell.col + cell.mergeH > maxCol:
            maxCol = cell.col + cell.mergeH
        if cell.joined():
            continue
        style = mergeStyles(styleList, cell.styleList)
        if (style.alignment.wrap == style.alignment.WRAP_AT_RIGHT):
            # get all the styles from the joined cells
            # and merge these styles in.
            joinedStyles = matrix.joinedElementStyles(cell)
            joinedStyle =  mergeStyles(styleList, joinedStyles)
            try:
                wrapText(sheet1, cell, joinedStyle)
            except:
                pass
        else:
            if cell.merged():
                # get all the styles from the joined cells
                # and merge these styles in.
                joinedStyles = matrix.joinedElementStyles(cell)
                joinedStyle =  mergeStyles(styleList, joinedStyles)
                try:
                    sheet1.write_merge(cell.row,
                                       cell.row + cell.mergeV,
                                       cell.col,
                                       cell.col + cell.mergeH,
                                       unicode(cell.text),
                                       joinedStyle
                                       )
                except Exception as msg:
                    print >> sys.stderr, msg
                    print >> sys.stderr, "row: %s + vert: %s, col: %s + horiz %s" % \
                        (cell.row, cell.mergeV, cell.col, cell.mergeH)
                    posn = "%s,%s" % (cell.row, cell.col)
                    if matrix.matrix[posn]:
                        print >> sys.stderr, matrix.matrix[posn]
            else:
                sheet1.write(cell.row,
                             cell.col,
                             unicode(cell.text),
                             style
                             )
    cellWidth = 480 # approximately 2 characters
    if maxCol > 255:
        maxCol = 255
    for col in range(maxCol+1):
        sheet1.col(col).width = cellWidth

    sheetA.write(0, 0, "Question Code")
    sheetA.write(0, 1, "Response Count")
    sheetA.write(0, 2, "Values")
    sheetA.write(0, 3, "Cell Address")
    for cell in matrixAnswers.matrix.values():
        style = mergeStyles(styleList, cell.styleList)
        sheetA.write(cell.row,
                     cell.col,
                     unicode(cell.text),
                     style
                    )

    if logo != None:
        sheet1.insert_bitmap(logo, 0, 0)

    sheet1.protect = True
    sheetA.protect = True
    for i in range(26):
        sheetA.col(i).width = 0
    sheetA.write(0,
                 26,
                 unicode(T("Please do not remove this sheet")),
                 styleHeader
                )
    sheetA.col(26).width = 12000
    book.save(output)
    return output

# -----------------------------------------------------------------------------
def completed_chart():
    """ RESTful CRUD controller

        Allows the user to display all the data from the selected question
        in a simple chart. If the data is numeric then a histogram will be
        drawn if it is an option type then a pie chart, although the type of
        chart drawn is managed by the analysis widget.
    """

    vars = request.vars
    if "series_id" in vars:
        seriesID = vars.series_id
    else:
        return "Programming Error: Series ID missing"
    if "question_id" in vars:
        qstnID = vars.question_id
    else:
        return "Programming Error: Question ID missing"
    if "type" in vars:
        type = vars.type
    else:
        return "Programming Error: Question Type missing"

    getAnswers = s3db.survey_getAllAnswersForQuestionInSeries
    answers = getAnswers(qstnID, seriesID)
    analysisTool = survey_analysis_type[type](qstnID, answers)
    qstnName = analysisTool.qstnWidget.question.name
    image = analysisTool.drawChart(seriesID, output="png")
    return image

# -----------------------------------------------------------------------------
def section():
    """ RESTful CRUD controller """

    # Load Model
    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)
    table = db[tablename]

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
        # Where is this defined?
        sectionSelect = s3.survey_section_select_widget(template_id)
        output["sectionSelect"] = sectionSelect
        return output
    s3.postp = postp

    output = s3_rest_controller(module, resourcename,
                                # Undefined
                                #rheader=s3db.survey_section_rheader
                                )
    return output

# -----------------------------------------------------------------------------
def question():
    """ RESTful CRUD controller """

    def prep(r):
        s3db.configure(r.tablename,
                        orderby = r.tablename+".posn",
                        )
        return True
    s3.prep = prep

    output = s3_rest_controller(module, resourcename,
                                # Undefined
                                #rheader=s3db.survey_section_rheader
                                )
    return output

# -----------------------------------------------------------------------------
def question_list():
    """ RESTful CRUD controller """

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def formatter():
    """ RESTful CRUD controller """

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def question_metadata():
    """ RESTful CRUD controller """

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def newAssessment():
    """ RESTful CRUD controller """

    # Load Model
    resourcename = "complete"
    tablename = "%s_%s" % (module, resourcename)
    s3db.table("survey_complete")
    s3db.table("survey_series")
    table = db[tablename]

    def prep(r):
        if r.interactive:
            if "viewing" in request.vars:
                dummy, series_id = request.vars.viewing.split(".")
            elif "series" in request.vars:
                series_id = request.vars.series
            else:
                series_id = r.id
            if series_id == None:
                # The URL is bad, without a series id we're lost so list all series
                redirect(URL(c="survey",
                             f="series",
                             args=[],
                             vars = {}))
            if "post_vars" in request and len(request.post_vars) > 0:
                id = s3.survey_save_answers_for_series(series_id,
                                                       None, # Insert
                                                       request.post_vars)
                response.confirmation = \
                    s3.crud_strings["survey_complete"].msg_record_created
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if "viewing" in request.vars:
                dummy, series_id = request.vars.viewing.split(".")
            elif "series" in request.vars:
                series_id = request.vars.series
            else:
                series_id = r.id
            if output["form"] == None:
                # The user is not authorised to create so switch to read
                redirect(URL(c="survey",
                             f="series",
                             args=[series_id,"read"],
                             vars = {}))
            # This is a bespoke form which confuses CRUD, which displays an
            # error "Invalid form (re-opened in another window?)"
            # So so long as we don't have an error in the form we can
            # delete this error.
            elif response.error and not output["form"]["error"]:
                response.error = None
            s3.survey_answerlist_dataTable_post(r)
            form = s3.survey_buildQuestionnaireFromSeries(series_id, None)
            urlimport = URL(c=module,
                            f="complete",
                            args=["import"],
                            vars = {"viewing":"%s.%s" % ("survey_series", series_id)
                                   ,"single_pass":True}
                            )
            buttons = DIV (A(T("Upload Completed Assessment Form"),
                             _href=urlimport,
                             _id="Excel-import",
                             _class="action-btn"
                             ),
                          )
            output["subtitle"] = buttons
            output["form"] = form
        return output
    s3.postp = postp

    output = s3_rest_controller(module,
                                resourcename,
                                method = "create",
                                rheader=s3db.survey_series_rheader
                               )
    return output

# -----------------------------------------------------------------------------
def complete():
    """ RESTful CRUD controller """

    # Load Model
    s3db.table("survey_complete")
    s3db.table("survey_series")
    table = db["survey_complete"]
    s3db.survey_answerlist_dataTable_pre()

    def postp(r, output):
        if r.method == "import":
            pass # don't want the import dataTable to be modified
        else:
            s3db.survey_answerlist_dataTable_post(r)
        return output
    s3.postp = postp

    def import_xls(uploadFile):
        if series_id == None:
            response.error = T("Series details missing")
            return
        openFile = StringIO()
        try:
            import xlrd
            from xlwt.Utils import cell_to_rowcol2
        except ImportError:
            s3base.s3_debug("ERROR: xlrd & xlwt modules are needed for importing spreadsheets")
            return None
        workbook = xlrd.open_workbook(file_contents=uploadFile)
        try:
            sheetR = workbook.sheet_by_name("Assessment")
            sheetM = workbook.sheet_by_name("Metadata")
        except:
            session.error = T("You need to use the spreadsheet which you can download from this page")
            redirect(URL(c="survey",
                     f="newAssessment",
                     args=[],
                     vars = {"viewing":"survey_series.%s" % series_id}))
        header = ''
        body = ''
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
                answerList = ''
            for col in range(count):
                cell = sheetM.cell_value(row, 3+col)
                (rowR, colR) = cell_to_rowcol2(cell)
                try:
                    cellValue = sheetR.cell_value(rowR, colR)
                except IndexError:
                    cellValue = ""
                """
                    BUG: The option list needs to work in different ways
                    depending on the question type. The question type should
                    be added to the spreadsheet to save extra db calls:

                    * Location save all the data as a hierarchy
                    * MultiOption save all selections
                    * Option save the last selection
                """
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
                                hour = int(time*24)
                                minute = int((time*24-hour)*60)
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

    series_id = None
    try:
        if "viewing" in request.vars:
            dummy, series_id = request.vars.viewing.split(".")
            series_name = s3.survey_getSeriesName(series_id)
        if series_name != "":
            csv_extra_fields = [dict(label="Series", value=series_name)]
        else:
            csv_extra_fields = []
    except:
        csv_extra_fields = []

    s3db.configure("survey_complete",
                    listadd=False,
                    deletable=False)

    s3.xls_parser = import_xls
    output = s3_rest_controller(module, resourcename,
                                csv_extra_fields=csv_extra_fields)
    return output

# -----------------------------------------------------------------------------
def answer():
    """ RESTful CRUD controller """

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def analysis():
    """ Bespoke controller """

    try:
        template_id = request.args[0]
    except:
        pass
    s3db.configure("survey_complete",
                    listadd=False,
                    deletable=False)
    output = s3_rest_controller(module, "complete")
    return output

# END =========================================================================
