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

from s3compat import StringIO

from gluon.contenttype import contenttype
import gluon.contrib.pyrtf as pyrtf

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

    redirect(URL(f="new_assessment.iframe",
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
                s3.actions.extend([dict(label=str(T("Download")),
                                       _class="action-btn",
                                       url=r.url(method = "translate_download",
                                                 component = "translate",
                                                 component_id = "[id]",
                                                 representation = "xls",
                                                 ),
                                       ),
                                   dict(label=str(T("Upload")),
                                        _class="action-btn",
                                        url=URL(c=module,
                                                f="template",
                                                args=[template_id,
                                                      "translate",
                                                      "[id]"]),
                                        ),
                                   ])
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
        #                                    f="template_read",
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
                current.log.error("Failed to insert record")
            return

    # Remove CRUD generated buttons in the tabs
    s3db.configure("survey_template",
                   listadd=False,
                   #deletable=False,
                   )

    output = s3_rest_controller(rheader=s3db.survey_template_rheader)
    return output

# -----------------------------------------------------------------------------
def template_read():
    """
        Show the details of all the questions of a particular template
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
    output = r(method="read", rheader=s3db.survey_template_rheader)
    return output

# -----------------------------------------------------------------------------
def template_summary():
    """
        Show section-wise summary of questions of a template
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
                                rheader=s3db.survey_template_rheader,
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
        method = r.method
        if request.ajax == True and method == "read":
            return output["item"]
        if not r.component and method != "summary":
            # Replace the Action buttons
            s3.actions = [{"label": s3_str(messages.UPDATE),
                           "_class": "action-btn edit",
                           "url": URL(c="survey",
                                      f="series",
                                      args=["[id]",
                                            "summary",
                                            ],
                                      ),
                           },
                          ]

        elif r.component_name == "complete":
            if method == "update":
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
def series_export_formatted():
    """
        Download a Spreadsheet which can be filled-in offline & uploaded
        @ToDo: rewrite as S3Method handler
    """

    try:
        series_id = request.args[0]
    except:
        output = s3_rest_controller(module, "series",
                                    rheader = s3db.survey_series_rheader)
        return output

    # Load Model
    table = s3db.survey_series
    s3db.table("survey_complete")

    vars = request.post_vars
    series = db(table.id == series_id).select(table.name,
                                              table.logo,
                                              limitby = (0, 1)
                                              ).first()
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
                            "%s.%s" % (series.logo, ext)
                            )
        if not os.path.exists(logo) or not os.path.isfile(logo):
            logo = None

    # Get the translation dictionary
    lang_dict = dict()
    lang = request.post_vars.get("translation_language", None)
    if lang:
        if lang == "Default":
            lang_dict = dict()
        else:
            try:
                from gluon.languages import read_dict
                lang_filename = "applications/%s/uploads/survey/translations/%s.py" % \
                                    (appname, lang)
                lang_dict = read_dict(lang_filename)
            except:
                lang_dict = dict()

    if "Export_Spreadsheet" in vars:
        (matrix, matrix_answers) = series_prepare_matrix(series_id,
                                                         series,
                                                         logo,
                                                         lang_dict,
                                                         justified = True
                                                         )
        output = series_export_spreadsheet(matrix,
                                           matrix_answers,
                                           logo,
                                           )
        filename = "%s.xls" % series.name
        content_type = ".xls"

    elif "Export_Word" in vars:
        template = s3db.survey_getTemplateFromSeries(series_id)
        template_id = template.id
        title = "%s (%s)" % (series.name, template.name)
        title = s3db.survey_T(title, lang_dict)
        widget_list = s3db.survey_getAllWidgetsForTemplate(template_id)
        output = series_export_word(widget_list, lang_dict, title, logo)
        filename = "%s.rtf" % series.name
        content_type = ".rtf"

    else:
        output = s3_rest_controller(module, "series",
                                    rheader = s3db.survey_series_rheader)
        return output

    output.seek(0)
    response.headers["Content-Type"] = contenttype(content_type)
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()

# -----------------------------------------------------------------------------
def series_prepare_matrix(series_id, series, logo, lang_dict, justified=False):
    """
        Helper function for series_export_formatted()
    """

    # Get the data
    # ============
    # * The sections within the template
    # * The layout rules for each question
    template = s3db.survey_getTemplateFromSeries(series_id)
    template_id = template.id
    section_list = s3db.survey_getAllSectionsForSeries(series_id)
    survey_T = s3db.survey_T

    title = "%s (%s)" % (series.name, template.name)
    title = survey_T(title, lang_dict)
    layout = []
    survey_getQstnLayoutRules = s3db.survey_getQstnLayoutRules

    for section in section_list:
        section_name = survey_T(section["name"], lang_dict)
        rules = survey_getQstnLayoutRules(template_id,
                                          section["section_id"])
        layout_rules = [section_name, rules]
        layout.append(layout_rules)
    widget_list = s3db.survey_getAllWidgetsForTemplate(template_id)
    layout_blocks = s3db.survey_LayoutBlocks()

    # Store the questions into a matrix based on the layout and the space
    # required for each question - for example an option question might
    # need one row for each possible option, and if this is in a layout
    # then the position needs to be recorded carefully...
    preliminary_matrix = s3db.survey_getMatrix(title,
                                               logo,
                                               layout,
                                               widget_list,
                                               False,
                                               lang_dict,
                                               showSectionLabels = False,
                                               layoutBlocks = layout_blocks,
                                               )
    if not justified:
        return preliminary_matrix

    # Align the questions so that each row takes up the same space.
    # This is done by storing resize and margin instructions with
    # each widget that is being printed
    layout_blocks.align()

    # Now rebuild the matrix with the spacing for each widget set up so
    # that the document will be fully justified
    layout_blocks = s3db.survey_LayoutBlocks()
    (matrix1, matrix2) = s3db.survey_getMatrix(title,
                                               logo,
                                               layout,
                                               widget_list,
                                               True,
                                               lang_dict,
                                               showSectionLabels = False,
                                               )
    return (matrix1, matrix2)

# -----------------------------------------------------------------------------
def series_export_word(widget_list, lang_dict, title, logo):
    """
        Export a Series in RTF Format
        @ToDo: rewrite as S3Method handler
    """

    output  = StringIO()
    doc     = pyrtf.Document(default_language=pyrtf.Languages.EnglishUK)
    section = pyrtf.Section()
    ss      = doc.StyleSheet
    ps = ss.ParagraphStyles.Normal.Copy()
    ps.SetName("NormalGrey")
    ps.SetShadingPropertySet(pyrtf.ShadingPropertySet(pattern=1,
                                                      background=pyrtf.Colour("grey light", 224, 224, 224)))
    ss.ParagraphStyles.append(ps)
    ps = ss.ParagraphStyles.Normal.Copy()
    ps.SetName("NormalCentre")
    ps.SetParagraphPropertySet(pyrtf.ParagraphPropertySet(alignment=3))
    ss.ParagraphStyles.append(ps)

    doc.Sections.append(section)
    heading = pyrtf.Paragraph(ss.ParagraphStyles.Heading1)

    if logo:
        image = pyrtf.Image(logo)
        heading.append(image)
    heading.append(title)
    section.append(heading)

    col = [2800, 6500]
    table = pyrtf.Table(*col)
    AddRow = table.AddRow
    sorted_widget_list = sorted(widget_list.values(),
                              key=lambda widget: widget.question.posn)
    for widget in sorted_widget_list:
        line = widget.writeQuestionToRTF(ss, lang_dict)
        try:
            AddRow(*line)
        except:
            if settings.base.debug:
                raise
            pass

    section.append(table)
    renderer = pyrtf.Renderer()
    renderer.Write(doc, output)
    return output

# -----------------------------------------------------------------------------
def series_export_spreadsheet(matrix, matrix_answers, logo):
    """
        Now take the matrix data type and generate a spreadsheet from it
    """

    try:
        import xlwt
    except ImportError:
        response.error = T("xlwt not installed, so cannot export as a Spreadsheet")
        output = s3_rest_controller(module, "survey_series",
                                    rheader=s3db.survey_series_rheader)
        return output

    import math

    # -------------------------------------------------------------------------
    def wrap_text(sheet, cell, style):
        row = cell.row
        col = cell.col
        try:
            text = s3_unicode(cell.text)
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
                                  style,
                                  )
            except Exception as msg:
                log = current.log
                log.error(msg)
                log.debug("row: %s + vert: %s, col: %s + horiz %s" % \
                          (cell.row, cell.mergeV, cell.col, cell.mergeH))
                posn = "%s,%s" % (cell.row, cell.col)
                if matrix.matrix[posn]:
                    log.debug(matrix.matrix[posn])
            rows = math.ceil((len(text) / characters_in_cell) / (1 + cell.mergeH))
        else:
            sheet.write(cell.row,
                        cell.col,
                        text,
                        style,
                        )
            rows = math.ceil(len(text) / characters_in_cell)
        new_row_height = int(rows * twips_per_row)
        new_col_width = width * COL_WIDTH_MULTIPLIER
        if sheet.row(row).height < new_row_height:
            sheet.row(row).height = new_row_height
        if sheet.col(col).width < new_col_width:
            sheet.col(col).width = new_col_width

    # -------------------------------------------------------------------------
    def merge_styles(list_template, style_list):
        """
            Take a list of styles and return a single style object with
            all the differences from a newly created object added to the
            resultant style.
        """
        if len(style_list) == 0:
            final_style = xlwt.XFStyle()
        elif len(style_list) == 1:
            final_style = list_template[style_list[0]]
        else:
            zero_style = xlwt.XFStyle()
            final_style = xlwt.XFStyle()
            for i in range(0, len(style_list)):
                final_style = merge_object_diff(final_style,
                                                list_template[style_list[i]],
                                                zero_style)
        return final_style

    # -------------------------------------------------------------------------
    def merge_object_diff(base_obj, new_obj, zero_obj):
        """
            Function to copy all the elements in new_obj that are different from
            the zero_obj and place them in the base_obj
        """

        element_list = new_obj.__dict__
        for (element, value) in element_list.items():
            try:
                base_obj.__dict__[element] = merge_object_diff(base_obj.__dict__[element],
                                                               value,
                                                               zero_obj.__dict__[element])
            except:
                if zero_obj.__dict__[element] != value:
                    base_obj.__dict__[element] = value
        return base_obj

    COL_WIDTH_MULTIPLIER = 240
    book = xlwt.Workbook(encoding="utf-8")
    output = StringIO()

    protection = xlwt.Protection()
    protection.cell_locked = 1
    no_protection = xlwt.Protection()
    no_protection.cell_locked = 0

    borders = xlwt.Borders()
    borders.left = xlwt.Borders.DOTTED
    borders.right = xlwt.Borders.DOTTED
    borders.top = xlwt.Borders.DOTTED
    borders.bottom = xlwt.Borders.DOTTED

    border_t1 = xlwt.Borders()
    border_t1.top = xlwt.Borders.THIN
    border_t2 = xlwt.Borders()
    border_t2.top = xlwt.Borders.MEDIUM

    border_l1 = xlwt.Borders()
    border_l1.left = xlwt.Borders.THIN
    border_l2 = xlwt.Borders()
    border_l2.left = xlwt.Borders.MEDIUM

    border_r1 = xlwt.Borders()
    border_r1.right = xlwt.Borders.THIN
    border_r2 = xlwt.Borders()
    border_r2.right = xlwt.Borders.MEDIUM

    border_b1 = xlwt.Borders()
    border_b1.bottom = xlwt.Borders.THIN
    border_b2 = xlwt.Borders()
    border_b2.bottom = xlwt.Borders.MEDIUM

    align_base = xlwt.Alignment()
    align_base.horz = xlwt.Alignment.HORZ_LEFT
    align_base.vert = xlwt.Alignment.VERT_TOP

    align_wrap = xlwt.Alignment()
    align_wrap.horz = xlwt.Alignment.HORZ_LEFT
    align_wrap.vert = xlwt.Alignment.VERT_TOP
    align_wrap.wrap = xlwt.Alignment.WRAP_AT_RIGHT

    shaded_fill = xlwt.Pattern()
    shaded_fill.pattern = xlwt.Pattern.SOLID_PATTERN
    shaded_fill.pattern_fore_colour = 0x16 # 25% Grey
    shaded_fill.pattern_back_colour = 0x08 # Black

    heading_fill = xlwt.Pattern()
    heading_fill.pattern = xlwt.Pattern.SOLID_PATTERN
    heading_fill.pattern_fore_colour = 0x1F # ice_blue
    heading_fill.pattern_back_colour = 0x08 # Black

    style_title =  xlwt.XFStyle()
    style_title.font.height = 0x0140 # 320 twips, 16 points
    style_title.font.bold = True
    style_title.alignment = align_base
    style_header = xlwt.XFStyle()
    style_header.font.height = 0x00F0 # 240 twips, 12 points
    style_header.font.bold = True
    style_header.alignment = align_base
    style_sub_header = xlwt.XFStyle()
    style_sub_header.font.bold = True
    style_sub_header.alignment = align_wrap
    style_section_heading = xlwt.XFStyle()
    style_section_heading.font.bold = True
    style_section_heading.alignment = align_wrap
    style_section_heading.pattern = heading_fill
    style_hint = xlwt.XFStyle()
    style_hint.protection = protection
    style_hint.font.height = 160 # 160 twips, 8 points
    style_hint.font.italic = True
    style_hint.alignment = align_wrap
    style_text = xlwt.XFStyle()
    style_text.protection = protection
    style_text.alignment = align_wrap
    style_instructions = xlwt.XFStyle()
    style_instructions.font.height = 0x00B4 # 180 twips, 9 points
    style_instructions.font.italic = True
    style_instructions.protection = protection
    style_instructions.alignment = align_wrap
    style_box = xlwt.XFStyle()
    style_box.borders = borders
    style_box.protection = no_protection
    style_input = xlwt.XFStyle()
    style_input.borders = borders
    style_input.protection = no_protection
    style_input.pattern = shaded_fill
    box_l1 = xlwt.XFStyle()
    box_l1.borders = border_l1
    box_l2 = xlwt.XFStyle()
    box_l2.borders = border_l2
    box_t1 = xlwt.XFStyle()
    box_t1.borders = border_t1
    box_t2 = xlwt.XFStyle()
    box_t2.borders = border_t2
    box_r1 = xlwt.XFStyle()
    box_r1.borders = border_r1
    box_r2 = xlwt.XFStyle()
    box_r2.borders = border_r2
    box_b1 = xlwt.XFStyle()
    box_b1.borders = border_b1
    box_b2 = xlwt.XFStyle()
    box_b2.borders = border_b2
    style_list = {}
    style_list["styleTitle"] = style_title
    style_list["styleHeader"] = style_header
    style_list["styleSubHeader"] = style_sub_header
    style_list["styleSectionHeading"] = style_section_heading
    style_list["styleHint"] = style_hint
    style_list["styleText"] = style_text
    style_list["styleInstructions"] = style_instructions
    style_list["styleInput"] = style_input
    style_list["boxL1"] = box_l1
    style_list["boxL2"] = box_l2
    style_list["boxT1"] = box_t1
    style_list["boxT2"] = box_t2
    style_list["boxR1"] = box_r1
    style_list["boxR2"] = box_r2
    style_list["boxB1"] = box_b1
    style_list["boxB2"] = box_b2

    sheet1 = book.add_sheet(T("Assessment"))
    sheet2 = book.add_sheet(T("Metadata"))
    max_col = 0
    for cell in matrix.matrix.values():
        if cell.col + cell.mergeH > 255:
            current.log.warning("Cell (%s,%s) - (%s,%s) ignored" % \
                (cell.col, cell.row, cell.col + cell.mergeH, cell.row + cell.mergeV))
            continue
        if cell.col + cell.mergeH > max_col:
            max_col = cell.col + cell.mergeH
        if cell.joined():
            continue
        style = merge_styles(style_list, cell.styleList)
        if (style.alignment.wrap == style.alignment.WRAP_AT_RIGHT):
            # get all the styles from the joined cells
            # and merge these styles in.
            joined_styles = matrix.joinedElementStyles(cell)
            joined_style =  merge_styles(style_list, joined_styles)
            try:
                wrap_text(sheet1, cell, joined_style)
            except:
                pass
        else:
            if cell.merged():
                # get all the styles from the joined cells
                # and merge these styles in.
                joined_styles = matrix.joinedElementStyles(cell)
                joined_style =  merge_styles(style_list, joined_styles)
                try:
                    sheet1.write_merge(cell.row,
                                       cell.row + cell.mergeV,
                                       cell.col,
                                       cell.col + cell.mergeH,
                                       s3_unicode(cell.text),
                                       joined_style,
                                       )
                except Exception as msg:
                    log = current.log
                    log.error(msg)
                    log.debug("row: %s + vert: %s, col: %s + horiz %s" % \
                              (cell.row, cell.mergeV, cell.col, cell.mergeH))
                    posn = "%s,%s" % (cell.row, cell.col)
                    if matrix.matrix[posn]:
                        log.debug(matrix.matrix[posn])
            else:
                sheet1.write(cell.row,
                             cell.col,
                             s3_unicode(cell.text),
                             style,
                             )
    CELL_WIDTH = 480 # approximately 2 characters
    if max_col > 255:
        max_col = 255
    for col in xrange(max_col + 1):
        sheet1.col(col).width = CELL_WIDTH

    sheet2.write(0, 0, "Question Code")
    sheet2.write(0, 1, "Response Count")
    sheet2.write(0, 2, "Values")
    sheet2.write(0, 3, "Cell Address")
    for cell in matrix_answers.matrix.values():
        style = merge_styles(style_list, cell.styleList)
        sheet2.write(cell.row,
                     cell.col,
                     s3_unicode(cell.text),
                     style,
                     )

    if logo != None:
        sheet1.insert_bitmap(logo, 0, 0)

    sheet1.protect = True
    sheet2.protect = True
    for i in range(26):
        sheet2.col(i).width = 0
    sheet2.write(0,
                 26,
                 s3_unicode(T("Please do not remove this sheet")),
                 style_header,
                 )
    sheet2.col(26).width = 12000
    book.save(output)
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
    analysisTool = s3db.survey_analysis_type[q_type](question_id, answers)
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
def new_assessment():
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

            output["form"] = TAG[""](buttons, form)
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
            redirect(URL(c="survey", f="new_assessment", args=[],
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
                   deletable = False,
                   listadd = False,
                   )

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
