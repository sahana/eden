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
                scripts_append("/%s/static/scripts/S3/s3.dc_question.js" % appname)
            else:
                scripts_append("/%s/static/scripts/tag-it.min.js" % appname)
                scripts_append("/%s/static/scripts/S3/s3.dc_question.min.js" % appname)
            # Add CSS
            s3.stylesheets.append("plugins/jquery.tagit.css")

            # Open in native controller to access Translations tabs
            s3db.configure("dc_question",
                           linkto = lambda record_id: URL(f="question", args=[record_id, "read"]),
                           linkto_update = lambda record_id: URL(f="question", args=[record_id, "update"]),
                           )

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def question():
    """
        RESTful CRUD controller
        - used for imports & to manage translations
    """

    return s3_rest_controller(rheader = s3db.dc_rheader,
                              )

# -----------------------------------------------------------------------------
def question_l10n():
    """
        RESTful CRUD controller
        - used for imports
    """

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
                               linkto = lambda record_id: URL(f="respnse", args=[record_id, "read"]),
                               linkto_update = lambda record_id: URL(f="respnse", args=[record_id, "update"]),
                               )

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader,
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
                                    limitby=(0, 1),
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
                from s3 import S3SQLCustomForm, S3SQLDummyField
                crud_fields = []
                cappend = crud_fields.append
                template_id = r.record.template_id
                stable = db.dc_section

                # Extract the Sections
                query = (stable.template_id == template_id) & \
                        (stable.deleted == False)
                sections = db(query).select(stable.id,
                                            stable.parent,
                                            stable.name,
                                            stable.posn,
                                            distinct = True,
                                            )

                # Put them into the hierarchy
                root_sections = {}
                subsections = {}
                for section in sections:
                    parent = section.parent
                    if parent:
                        # Store this for next parse
                        if parent in subsections:
                            subsections[parent].append(section)
                        else:
                            subsections[parent] = [section]
                    else:
                        # Root section
                        root_sections[section.id] = {"id": section.id,
                                                     "name": section.name,
                                                     "posn": section.posn,
                                                     "questions": [],
                                                     "subsections": {},
                                                     }

                # Add the subsections
                subsubsections = {}
                for parent in subsections:
                    _subsections = subsections[parent]
                    if parent in root_sections:
                        # SubSections
                        for sub in _subsections:
                            root_sections[parent]["subsections"][sub.id] = {"id": sub.id,
                                                                            "name": sub.name,
                                                                            "posn": sub.posn,
                                                                            "questions": [],
                                                                            "subsubsections": {},
                                                                            }
                    else:
                        # SubSubSections - store for next parse
                        subsubsections[parent] = _subsections

                # Add the subsubsections
                for parent in subsubsections:
                    for root in root_sections:
                        subsections = root_sections[root]["subsections"]
                        if parent in subsections:
                            _subsubsections = subsubsections[parent]
                            for subsub in _subsubsections:
                                subsections[parent]["subsubsections"][subsub.id] = {"id": subsub.id,
                                                                                    "name": subsub.name,
                                                                                    "posn": subsub.posn,
                                                                                    "questions": [],
                                                                                    }

                # Add the Questions
                # Prep for Auto-Totals
                # Prep for Grids
                qtable = s3db.dc_question
                ttable = s3db.dc_question_l10n
                ftable = db.s3_field

                language = session.s3.language
                if language == settings.get_L10n_default_language():
                    translate = False
                else:
                    translate = True

                query = (qtable.template_id == r.record.template_id) & \
                        (qtable.deleted == False)
                left = [stable.on(stable.id == qtable.section_id),
                        ftable.on(ftable.id == qtable.field_id),
                        ]
                fields = [stable.id,
                          ftable.name,
                          ftable.label,
                          qtable.code,
                          qtable.posn,
                          qtable.totals,
                          qtable.grid,
                          ]
                if translate:
                    left.append(ttable.on((ttable.question_id == qtable.id) & \
                                          (ttable.language == language)))
                    fields.append(ttable.name_l10n)
                questions = db(query).select(*fields,
                                             left = left
                                             )
                auto_totals = {}
                codes = {}
                grids = {}
                grid_children = {}
                root_questions = []
                for question in questions:
                    field_name = question.get("s3_field.name")
                    code = question["dc_question.code"]
                    if code:
                        codes[code] = field_name
                    totals = question["dc_question.totals"]
                    if totals:
                        auto_totals[field_name] = {"codes": totals,
                                                   "fields": [],
                                                   }
                    grid = question["dc_question.grid"]
                    if grid:
                        len_grid = len(grid)
                        if len_grid == 2:
                            # Grid Pseudo-Question
                            if not code:
                                s3.error("Code required for Grid Questions") # @ToDo: Make mandatory in onvalidation
                                raise
                            rows = [s3_str(T(v)) for v in grid[0]]
                            cols = [s3_str(T(v)) for v in grid[1]]
                            fields = [[0 for x in range(len(rows))] for y in range(len(cols))] 
                            grids[code] = {"r": rows,
                                           "c": cols,
                                           "f": fields,
                                           }
                        elif len_grid == 3:
                            # Child Question
                            grid_children[field_name] = grid
                        else:
                            s3.warning("Invalid grid data for %s - ignoring" % (code or field_name))
                    
                    section_id = question["dc_section.id"]
                    label = None
                    if translate:
                        label = question.get("dc_question_l10n.name_l10n")
                    if not label:
                        label = question.get("s3_field.label")
                    question = {question["dc_question.posn"]: {"name": field_name,
                                                               "code": code,
                                                               "label": label,
                                                               },
                                }
                    if not section_id:
                        root_questions.append(question)
                        continue
                    if section_id in root_sections:
                        root_sections[section_id]["questions"].append(question)
                        continue
                    for section in root_sections:
                        if section_id in root_sections[section]["subsections"]:
                            root_sections[section]["subsections"][section_id]["questions"].append(question)
                            continue
                        for subsection in root_sections[section]["subsections"]:
                            if section_id in root_sections[section]["subsections"][subsection]["subsubsections"]:
                                root_sections[section]["subsections"][subsection]["subsubsections"][section_id]["questions"].append(question)

                # Sort them by Position
                root_questions.sort()
                sections = [{v["posn"]: v} for k, v in root_sections.items()]
                sections.sort()
                for s in sections:
                    section = s[s.items()[0][0]]
                    subsections = [{v["posn"]: v} for k, v in section["subsections"].items()]
                    subsections.sort()
                    section["subsections"] = subsections
                    section["questions"].sort()
                    for sub in subsections:
                        _sub = sub[sub.items()[0][0]]
                        subsubsections = [{v["posn"]: v} for k, v in _sub["subsubsections"].items()]
                        subsubsections.sort()
                        _sub["subsubsections"] = subsubsections
                        _sub["questions"].sort()
                        for subsub in subsubsections:
                            subsub[subsub.items()[0][0]]["questions"].sort()

                # Append questions to the form, with subheadings
                # 1st add those questions without a section (likely the only questions then)
                for q in root_questions:
                    question = q[q.items()[0][0]]
                    fname = question["name"]
                    if fname:
                        cappend((question["label"], fname))
                    else:
                        # Grid Pseudo-Question
                        fname = question["code"]
                        cappend((question["label"], S3SQLDummyField(fname)))
                # Next add those questions with a section (likely the only questions then)
                subheadings = {}
                for s in sections:
                    section = s[s.items()[0][0]]
                    section_name = section["name"]
                    # 1st add those questions without a subsection
                    _subheadings = {"fields": [],
                                    "subheadings": {},
                                    }
                    subheadings[section_name] = _subheadings
                    questions = section["questions"]
                    for question in questions:
                        question = question.items()[0][1] 
                        fname = question["name"]
                        if fname:
                            cappend((question["label"], fname))
                        else:
                            # Grid Pseudo-Question
                            fname = question["code"]
                            cappend((question["label"], S3SQLDummyField(fname)))
                        _subheadings["fields"].append(fname)
                    # Next add those questions in a subsection
                    subsections = section["subsections"]
                    for sub in subsections:
                        _sub = sub[sub.items()[0][0]]
                        section_name = _sub["name"]
                        __subheadings = {"fields": [],
                                         "subheadings": {},
                                         }
                        _subheadings["subheadings"][section_name] = __subheadings
                        questions = _sub["questions"]
                        for question in questions:
                            question = question.items()[0][1] 
                            fname = question["name"]
                            if fname:
                                cappend((question["label"], fname))
                            else:
                                # Grid Pseudo-Question
                                fname = question["code"]
                                cappend((question["label"], S3SQLDummyField(fname)))
                            __subheadings["fields"].append(fname)
                        # Next add those questions in a subsubsection
                        subsubsections = _sub["subsubsections"]
                        for subsub in subsubsections:
                            _subsub = subsub[subsub.items()[0][0]]
                            section_name = _subsub["name"]
                            ___subheadings = {"fields": [],
                                              "subheadings": {},
                                              }
                            __subheadings["subheadings"][section_name] = ___subheadings
                            questions = _subsub["questions"]
                            for question in questions:
                                question = question.items()[0][1] 
                                fname = question["name"]
                                if fname:
                                    cappend((question["label"], fname))
                                else:
                                    # Grid Pseudo-Question
                                    fname = question["code"]
                                    cappend((question["label"], S3SQLDummyField(fname)))
                                ___subheadings["fields"].append(fname)

                crud_form = S3SQLCustomForm(*crud_fields)
                s3db.configure(tablename,
                               crud_form = crud_form,
                               subheadings = subheadings,
                               )

                # Compact JSON encoding
                SEPARATORS = (",", ":")
                jappend = s3.jquery_ready.append

                # Auto-Totals
                for field in auto_totals:
                    f = auto_totals[field]
                    append = f["fields"].append
                    for code in f["codes"]:
                        append(codes.get(code))
                    jappend('''S3.autoTotals('%s',%s,'%s')''' % (field, json.dumps(f["fields"], separators=SEPARATORS), dtablename))

                # Grids
                # Place the child fields in the correct places in their grids
                if len(grids):
                    for child in grid_children:
                        code, row, col = grid_children[child]
                        grids[code]["f"][col - 1][row - 1] = child
                    jappend('''S3.dc_grids(%s,'%s')''' % (json.dumps(grids, separators=SEPARATORS), dtablename))

                # Add JS
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/S3/s3.dc_answer.js" % appname)
                else:
                    s3.scripts.append("/%s/static/scripts/S3/s3.dc_answer.min.js" % appname)

        return True
    s3.prep = prep

    return s3_rest_controller("dc", "response",
                              rheader = s3db.dc_rheader,
                              )

# END =========================================================================
