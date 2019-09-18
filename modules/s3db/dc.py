# -*- coding: utf-8 -*-

""" Sahana Eden Data Collection Models
    - a front-end UI to manage Assessments which uses the Dynamic Tables
      back-end

    @copyright: 2014-2019 (c) Sahana Software Foundation
    @license: MIT

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

__all__ = ("DataCollectionTemplateModel",
           "DataCollectionModel",
           #"dc_TargetReport",
           "dc_rheader",
           )

from gluon import *
from gluon.languages import read_dict, write_dict

from ..s3 import *
from s3compat import xrange
from s3layouts import S3PopupLink

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class DataCollectionTemplateModel(S3Model):
    """
        Templates to use for Assessments / Surveys
        - uses the Dynamic Tables back-end to store Questions
    """

    names = ("dc_template",
             "dc_template_id",
             "dc_template_l10n",
             "dc_question",
             "dc_question_l10n",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        crud_strings = s3.crud_strings
        settings = current.deployment_settings

        add_components = self.add_components
        configure = self.configure
        define_table = self.define_table

        master_opts = {"dc_response": T("Assessments"),
                       "event_sitrep": T("Situation Reports"),
                       #"hrm_training_event": T("Training Events"), # Currently using dc_target
                       }

        # =====================================================================
        # Data Collection Templates
        #
        tablename = "dc_template"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("master", length=32,
                           default = "dc_response",
                           label = T("Used for"),
                           represent = S3Represent(options = master_opts),
                           requires = IS_IN_SET(master_opts),
                           # Either set via Controller or on Import
                           readable = False,
                           writable = False,
                           ),
                     # The Dynamic Table used to store the Questions and Answers
                     # (An alternative design would be to use Tables as reusable
                     #  Sections but this hasn't been adopted at this time for
                     #  simplicity)
                     self.s3_table_id(
                        readable = False,
                        writable = False,
                        ),
                     # Dictionary of Positions and Items within them
                     # e.g.
                     # {1: {'type': 'subheading',
                     #      'text': 'Subheading',
                     #      'l10n': {'fr': 'Sous rubrique',
                     #               }
                     #      },
                     #  2: {'type': 'instructions',
                     #      'do': {'text': 'Make yourself comfortable',
                     #             'l10n': {'fr': "Mettez-vous à l'aise",
                     #                      },
                     #             },
                     #      'say': {'text': 'Make yourself comfortable',
                     #              'l10n': {'fr': "Mettez-vous à l'aise",
                     #                       },
                     #              },
                     #      'displayLogic': {'id': questionID,
                     #                       'eq': option_id (Multichoice, Likert)
                     #                       or
                     #                       'selectedRegion': region_id (Heatmap)
                     #                       },
                     #      },
                     #  3: {'type': 'question',
                     #      'code': 'MyT4',   # Used for prepop
                     #      'id': 4,          # Used live
                     #      'displayLogic': {'id': questionID, (Numeric)
                     #                       'eq': 4,
                     #                       or 1 or both of these:
                     #                       'gt': 6,
                     #                       'lt': 14,
                     #                       },
                     #      },
                     #  4: {'type': 'break',
                     #      },
                     Field("layout", "json",
                           label = T("Layout"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  create_onaccept = self.dc_template_create_onaccept,
                  onaccept = self.dc_template_onaccept,
                  ondelete = self.dc_template_ondelete,
                  deduplicate = S3Duplicate(),
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        template_id = S3ReusableField("template_id", "reference %s" % tablename,
                                      label = T("Template"),
                                      ondelete = "CASCADE",
                                      represent = represent,
                                      requires = IS_ONE_OF(db, "dc_template.id",
                                                           represent,
                                                           ),
                                      sortby = "name",
                                      comment = S3PopupLink(f="template",
                                                            tooltip=T("Add a new data collection template"),
                                                            ),
                                      )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Template"),
            title_display = T("Template Details"),
            title_list = T("Templates"),
            title_update = T("Edit Template"),
            label_list_button = T("List Templates"),
            label_delete_button = T("Delete Template"),
            msg_record_created = T("Template added"),
            msg_record_modified = T("Template updated"),
            msg_record_deleted = T("Template deleted"),
            msg_list_empty = T("No Templates currently registered"))

        # Components
        add_components(tablename,
                       dc_question = "template_id",
                       dc_instruction = "template_id",
                       dc_template_l10n = "template_id",
                       )

        # =====================================================================
        # Template Translations
        #
        tablename = "dc_template_l10n"
        define_table(tablename,
                     template_id(),
                     s3_language(empty = False),
                     *s3_meta_fields())

        # =====================================================================
        # Questions
        #
        type_opts = {1: T("Text"),
                     2: T("Number"),
                     #3: T("Fractional Number"),
                     4: T("Yes/No"),
                     5: T("Yes, No, Don't Know"),
                     6: T("Options"),
                     7: T("Date"),
                     #8: T("Date/Time"),
                     9: T("Grid"), # Pseudo-question
                     10: T("Large Text"),
                     11: T("Rich Text"),
                     12: T("Likert-scale"),
                     13: T("Heatmap"),
                     #: T("Organization"),
                     #: T("Location"),
                     #: T("Person"),
                     }

        # Scale defined in settings["scale"]
        #likert_opts = {1: T("Appropriateness (Very appropriate - Very inappropriate)"),
        #               2: T("Confidence (Extremely confident - Not confident at all)"),
        #               3: T("Frequency (Always - Never)"),
        #               4: T("Safety (Extremely safe - Not safe at all)"),
        #               5: T("Satisfaction (Satisfied - Dissatisfied)"),
        #               6: T("Smiley scale (5 point)"),
        #               7: T("Smiley scale (3 point)"),
        #               }

        tablename = "dc_question"
        define_table(tablename,
                     template_id(),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("code",
                           label = T("Code"),
                           requires = IS_EMPTY_OR(
                                        # @ToDo: Only really needs to be unique per Template
                                        IS_NOT_IN_DB(db, "dc_question.code")
                                        ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Code"),
                                                           T("Unique code for the field - required if using Auto-Totals, Grids or Show Hidden"), # Also needed for Prepop
                                                           ),
                                         ),
                           ),
                     # The Dynamic Field used to store the Question/Answers
                     self.s3_field_id(
                        readable = False,
                        writable = False,
                        ),
                     Field("field_type", "integer", notnull=True,
                           default = 1, # string
                           label = T("Field Type"),
                           represent = S3Represent(options=type_opts),
                           requires = IS_IN_SET(type_opts),
                           ),
                     Field("options", "json",
                           label = T("Options"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           ),
                     # Use List to force order or Dict to alphasort
                     #Field("sort_options", "boolean",
                     #      default = True,
                     #      label = T("Sort Options?"),
                     #      represent = s3_yes_no_represent,
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("Sort Options?"),
                     #                                      T("Whether options should be sorted alphabetically"),
                     #                                      ),
                     #                    ),
                     #      ),
                     # Field used by UCCE:
                     Field("settings", "json",
                           label = T("Settings"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           ),
                     # Field used by SCPHIMS:
                     Field("grid", "json",
                           label = T("Grid"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s%s" % (T("Grid"),
                                                             T("For Grid Pseudo-Question, this is the Row labels & Column labels"),
                                                             T("For Questions within the Grid, this is their position in the Grid, encoded as Grid,Row,Col"), # @ToDo: Widget?
                                                             ),
                                         ),
                           ),
                     # Field used by SCPHIMS:
                     Field("totals", "json",
                           label = T("Totals"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Totals"),
                                                           T("List of fields (codes) which this one is the Total of"),
                                                           ),
                                         ),
                           ),
                     # Field used by SCPHIMS:
                     Field("show_hidden", "json",
                           label = T("Show Hidden"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Show Hidden"),
                                                           T("List of fields (codes) which this one unhides when selected"),
                                                           ),
                                         ),
                           ),
                     Field("require_not_empty", "boolean",
                           default = False,
                           label = T("Required?"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Required?"),
                                                           T("Is the field mandatory? (Cannot be left empty)"),
                                                           ),
                                         ),
                           ),
                     Field("file", "upload",
                           autodelete = True,
                           label = T("Image"),
                           length = current.MAX_FILENAME_LENGTH,
                           represent = self.doc_image_represent,
                           requires = IS_EMPTY_OR(
                                        IS_IMAGE(extensions=(s3.IMAGE_EXTENSIONS)),
                                        # Distinguish from prepop
                                        null = "",
                                      ),
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(current.request.folder,
                                                       "uploads",
                                                       "images"),
                           widget = S3ImageCropWidget((120, 120)),
                           ),
                     s3_comments(label = T("Tooltip"),
                                 represent = s3_text_represent,
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Tooltip"),
                                                                 T("Explanation of the field to be displayed in forms"),
                                                                 ),
                                               ),
                                 ),
                     *s3_meta_fields())

        unique_question_names_per_template = settings.get_dc_unique_question_names_per_template()
        if unique_question_names_per_template:
            # Deduplicate Questions by Name/Template
            # - needed for importing multiple translations
            deduplicate = S3Duplicate(primary=("name", "template_id"))
        else:
            deduplicate = None

        configure(tablename,
                  onaccept = self.dc_question_onaccept,
                  deduplicate = deduplicate,
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        question_id = S3ReusableField("question_id", "reference %s" % tablename,
                                      label = T("Question"),
                                      represent = represent,
                                      requires = IS_ONE_OF(db, "dc_question.id",
                                                           represent,
                                                           ),
                                      sortby = "name",
                                      #comment = S3PopupLink(f="question",
                                      #                      tooltip=T("Add a new question"),
                                      #                      ),
                                      )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Question"),
            title_display = T("Question Details"),
            title_list = T("Questions"),
            title_update = T("Edit Question"),
            title_upload = T("Import Questions"),
            label_list_button = T("List Questions"),
            label_delete_button = T("Delete Question"),
            msg_record_created = T("Question added"),
            msg_record_modified = T("Question updated"),
            msg_record_deleted = T("Question deleted"),
            msg_list_empty = T("No Questions currently registered"))

        # Components
        add_components(tablename,
                       dc_question_l10n = "question_id",
                       )

        # =====================================================================
        # Question Translations
        #
        tablename = "dc_question_l10n"
        define_table(tablename,
                     question_id(),
                     s3_language(empty = False),
                     Field("name_l10n",
                           label = T("Translated Question"),
                           ),
                     Field("options_l10n", "json",
                           label = T("Translated Options"), # Regions for Heatmap Questions
                           represent = lambda opts: ", ".join(json.loads(opts)),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           ),
                     # @ToDo: Implement this when-required
                     Field("tooltip_l10n",
                           label = T("Translated Tooltip"),
                           ),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Translation"),
            title_display = T("Translation Details"),
            title_list = T("Translations"),
            title_update = T("Edit Translation"),
            title_upload = T("Import Translations"),
            label_list_button = T("List Translations"),
            label_delete_button = T("Delete Translation"),
            msg_record_created = T("Translation added"),
            msg_record_modified = T("Translation updated"),
            msg_record_deleted = T("Translation deleted"),
            msg_list_empty = T("No Translations currently registered"))

        configure(tablename,
                  onaccept = self.dc_question_l10n_onaccept,
                  )

        # =====================================================================
        # Pass names back to global scope (s3.*)
        return {"dc_template_id": template_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dc_template_id": lambda **attr: dummy("template_id"),
                }

    # -------------------------------------------------------------------------
    def dc_template_create_onaccept(self, form):
        """
            On-accept routine for dc_template:
             - Create & link a Dynamic Table to use to store the Questions
        """

        form_vars_get = form.vars.get
        template_id = form_vars_get("id")
        if not template_id:
            return

        db = current.db
        s3db = current.s3db

        title = form_vars_get("name")
        master = form_vars_get("master")
        if master is None:
            # Load full record
            ttable = s3db.dc_template
            record = db(ttable.id == template_id).select(ttable.master,
                                                         ttable.name,
                                                         limitby = (0, 1),
                                                         ).first()
            title = record.name
            master = record.master

        settings = current.deployment_settings
        if settings.get_dc_mobile_inserts():
            insertable = True
        else:
            insertable = False

        table_settings = {}
        if master == "dc_response":
            mobile_form = True # For SCPHIMS at least, for UCCE this should happen only based on dc_target.status (currently handled in-template)
            mobile_data = settings.get_dc_mobile_data()
            table_settings["insertable"] = insertable
            # Configure table.response_id.represent
            table_settings["card"] = {"title": "{{record.response_id}}",
                                      }
        elif master == "event_sitrep":
            mobile_form = False # For SCPHIMS at least
            mobile_data = False
        else:
            raise TypeError

        # Create the Dynamic Table
        table_id = s3db.s3_table.insert(title = title,
                                        mobile_form = mobile_form,
                                        mobile_data = mobile_data,
                                        settings = table_settings,
                                        )

        # Add a Field to link Answers together
        if insertable:
            # We calculate the response_id onaccept: UCCE
            #  1 Template = 1 Target so can calculate target_id from table_id
            require_not_empty = False
        else:
            # We provide the response_id to the client: SCPHIMS
            #  1 Template > Targets so cannot calculate target_id from table_id
            require_not_empty = True
        db.s3_field.insert(table_id = table_id,
                           name = "%s_id" % master.split("_", 1)[1],
                           field_type = "reference %s" % master,
                           require_not_empty = require_not_empty,
                           component_key = True,
                           component_alias = "answer",
                           component_tab = True,
                           master = master,
                           settings = {"component_multiple": False},
                           )
        # @ToDo: Call onaccept if this starts doing anything other than just setting 'master'
        # @ToDo: Call set_record_owner() once we start restricting these

        # Link this Table to the Template
        db(db.dc_template.id == template_id).update(table_id=table_id)

        # Call normal onaccept
        self.dc_template_onaccept(form)

    # -------------------------------------------------------------------------
    @staticmethod
    def dc_template_onaccept(form):
        """
            On-accept routine for dc_template:
             - Set the Dynamnic Table to the same Title as the Template
             - Convert Question Codes to IDs in the layout
        """

        template_id = form.vars.get("id")
        if not template_id:
            return

        db = current.db
        s3db = current.s3db

        # Load full record
        ttable = s3db.dc_template
        record = db(ttable.id == template_id).select(ttable.name,
                                                     ttable.layout,
                                                     ttable.table_id,
                                                     limitby = (0, 1),
                                                     ).first()

        # Sync the name of the Template to that of the Dynamic Table
        # (UCCE's mobile app uses s3_table.title for the Survey name...which works since 1 Template == 1 Target, beyond UCCE this won't be possible)
        dtable = s3db.s3_table
        db(dtable.id == record.table_id).update(title = record.name)

        # Convert Question Codes to IDs in the layout
        layout = record.layout
        if layout is not None:

            qtable = s3db.dc_question

            # Not needed for JSON field type:
            #layout = json.loads(layout)
            new_layout = {}
            questions = {}

            for position in layout:
                item = layout[position]
                if item["type"] != "question":
                    new_layout[position] = item
                    continue
                if item.get("id"):
                    new_layout[position] = item
                    continue
                code = item.get("code")
                if not code:
                    current.log.error("Question without ID or Code")
                    continue
                questions[code] = position

            rows = db(qtable.code.belongs(questions)).select(qtable.id,
                                                             qtable.code,
                                                             )
            for row in rows:
                new_layout[questions.get(row.code)] = {"type": "question",
                                                       "id": row.id,
                                                       }

            db(ttable.id == template_id).update(layout = new_layout)

    # -------------------------------------------------------------------------
    @staticmethod
    def dc_template_ondelete(form):
        """
            On-delete routine for dc_template:
             - Delete the associated Dynamic Table
        """

        template_id = form.id
        if not template_id:
            return

        db = current.db
        s3db = current.s3db

        # Load full record
        ttable = s3db.dc_template
        record = db(ttable.id == template_id).select(ttable.deleted_fk,
                                                     limitby = (0, 1),
                                                     ).first()

        deleted_fk = json.loads(record.deleted_fk)
        table_id = deleted_fk.get("table_id")
        if table_id:
            dtable = s3db.s3_table
            resource = s3db.resource("s3_table", filter=(dtable.id == table_id))
            resource.delete()

    # -------------------------------------------------------------------------
    @staticmethod
    def dc_question_onaccept(form):
        """
            On-accept routine for dc_question:
             - Create & link a Dynamic Field to use to store the Question

            Currently assumes only a single Translation available for each Question
        """

        try:
            question_id = form.vars.id
        except AttributeError:
            return

        db = current.db

        # Read the full Question
        qtable = db.dc_question
        ltable = db.dc_question_l10n
        left = ltable.on(ltable.question_id == qtable.id)
        question = db(qtable.id == question_id).select(qtable.id,
                                                       qtable.template_id,
                                                       qtable.field_id,
                                                       qtable.name,
                                                       qtable.comments,
                                                       qtable.field_type,
                                                       qtable.file,
                                                       qtable.options,
                                                       qtable.settings,
                                                       qtable.require_not_empty,
                                                       ltable.language,
                                                       ltable.name_l10n,
                                                       ltable.options_l10n,
                                                       left = left,
                                                       limitby=(0, 1)
                                                       ).first()

        l10n = question["dc_question_l10n"]
        language = l10n.get("language")

        question = question["dc_question"]
        field_type = question.field_type
        question_settings = question.settings or {}

        field_settings = {"mobile": {}}
        mobile_settings = field_settings["mobile"]
        if language:
            name_l10n = l10n.get("name_l10n")
            options_l10n = l10n.get("options_l10n") or []
            l10n = {language: {"label": name_l10n,
                               }
                    }
            if options_l10n:
                l10n[language]["options"] = options_l10n
            mobile_settings["l10n"] = l10n

        ftable = current.s3db.s3_field

        image = question.file
        if image:
            mobile_settings["image"] = {"url": URL(c="default", f="download", args=image),
                                        }
        else:
            pipe_image = question_settings.get("pipeImage")
            if pipe_image:
                region = pipe_image.get("region")
                if region is not None:
                    # Heatmap
                    # Convert Question ID to fieldname
                    query = (qtable.id == pipe_image["id"]) & \
                            (ftable.id == qtable.field_id)
                    from_field = db(query).select(ftable.name,
                                                  limitby = (0, 1)
                                                  ).first()
                    mobile_settings["image"] = {"from": from_field.name,
                                                "region": region,
                                                }
                else:
                    # Nothing special needed client-side
                    piped_question = db(qtable.id == pipe_image["id"]).select(qtable.file,
                                                                              limitby=(0, 1)
                                                                              ).first()
                    if piped_question:
                        mobile_settings["image"] = {"url": URL(c="default", f="download", args=piped_question.file),
                                                    }

        requires = question_settings.get("requires")
        if requires:
            # "isNotEmpty": {}
            # "isIntInRange": {"min": min, "max": max}
            mobile_settings["requires"] = requires

        options = None
        if field_type == 1:
            # Text
            field_type = "string"
        elif field_type == 2:
            # Number
            field_type = "integer"
        elif field_type == 4:
            # Boolean
            field_type = "boolean"
            mobile_settings["widget"] = {"type": "checkbox"}
        elif field_type == 5:
            # Yes/No/Don't Know
            T = current.T
            options = [T("Yes"),
                       T("No"),
                       T("Don't Know"),
                       ]
            field_type = "string"
        elif field_type == 6:
            # Options
            options = question.options
            multiple = question_settings.get("multiple")
            if multiple and multiple > 1:
                field_type = "list:string"
                if requires:
                    mobile_settings["requires"]["selectedOpts"] = {"max": multiple}
                else:
                    mobile_settings["requires"] = {"selectedOpts": {"max": multiple}}
            else:
                field_type = "string"
            other = question_settings.get("other")
            if other:
                options.append("__other__")
                if language:
                    other_l10n = question_settings.get("otherL10n")
                    if other_l10n:
                        other_settings = {"mobile": {"l10n": {language: {"label": other_l10n,
                                                                         },
                                                              },
                                                     },
                                          }
                    else:
                        other_settings = {}
                else:
                    other_settings = {}
                other_id = question_settings.get("other_id")
                if other_id:
                    # Read the Dyanmic Field to get the fieldname for the Mobile client
                    other_field = db(ftable.id == other_id).select(ftable.id,
                                                                   ftable.name,
                                                                   limitby = (0, 1)
                                                                   ).first()
                    mobile_settings["other"] = other_field.name
                    # Update the Dynamic Field with the current label
                    other_field.update_record(label = other,
                                              settings = other_settings,
                                              )
                    # @ToDo: Call onaccept if this starts doing anything other than just setting 'master'
                else:
                    # Create the Dynamic Field
                    # Lookup the table_id
                    ttable = db.dc_template
                    template = db(ttable.id == question.template_id).select(ttable.table_id,
                                                                            limitby=(0, 1)
                                                                            ).first()
                    from uuid import uuid1
                    name = "f%s" % str(uuid1()).replace("-", "_")
                    mobile_settings["other"] = name
                    other_id = ftable.insert(table_id = template.table_id,
                                             label = other,
                                             name = name,
                                             field_type = "string",
                                             settings = other_settings,
                                             )
                    question_settings["other_id"] = other_id
                    question.update_record(settings = question_settings)
                    # @ToDo: Call onaccept if this starts doing anything other than just setting 'master'
                    # @ToDo: Call set_record_owner() once we start restricting these
        elif field_type == 7:
            # "Date"
            field_type = "date"
        elif field_type == 8:
            # Datetime
            field_type = "datetime"
        elif field_type == 9:
            # Grid: Pseudo-question, no dynamic field
            return
        elif field_type == 10:
            # Large Text
            field_type = "text"
            field_settings["widget"] = "comments"
        elif field_type == 11:
            # Rich Text
            field_type = "text"
            field_settings["widget"] = "richtext"
        elif field_type == 12:
            # Likert
            field_type = "integer" # We hardcode options currently & indexes are far less likely to vary than the string representations
            # No need to pass these to mobile as it has it's own lookup based on scale
            #options = question.options
            # NB UCCE uses options_l10n just like for multichoice, but in general, could have l10n done centrally instead
            # Mobile client currently uses names for scales, rather than simple number, so map:
            likert_scale_names = {1: "appropriateness",
                                  2: "confidence",
                                  3: "frequency",
                                  4: "safety",
                                  5: "satisfaction",
                                  6: "smiley-5",
                                  7: "smiley-3",
                                  }
            mobile_settings["widget"] = {"type": "likert",
                                         "scale": likert_scale_names.get(question_settings.get("scale")),
                                         }
        elif field_type == 13:
            # Heatmap
            field_type = "json" # Store list of Lat/Lons
            widget = {"type": "heatmap"}
            regions = question_settings.get("regions")
            if regions:
                widget["regions"] = regions
            mobile_settings["widget"] = widget
            num_clicks = question_settings.get("numClicks")
            if num_clicks:
                if requires:
                    mobile_settings["requires"]["selectedOpts"] = {"max": num_clicks}
                else:
                    mobile_settings["requires"] = {"selectedOpts": {"max": num_clicks}}
        else:
            current.log.debug(field_type)
            raise NotImplementedError

        field_id = question.field_id
        if field_id:
            # Update the Dynamic Field
            db(current.s3db.s3_field.id == field_id).update(label = question.name,
                                                            field_type = field_type,
                                                            options = options,
                                                            settings = field_settings,
                                                            require_not_empty = question.require_not_empty,
                                                            comments = question.comments,
                                                            )
            # @ToDo: Call onaccept if this starts doing anything other than just setting 'master'
        else:
            # Create the Dynamic Field
            # Lookup the table_id
            ttable = db.dc_template
            template = db(ttable.id == question.template_id).select(ttable.table_id,
                                                                    limitby=(0, 1)
                                                                    ).first()
            from uuid import uuid1
            name = "f%s" % str(uuid1()).replace("-", "_")
            field_id = current.s3db.s3_field.insert(table_id = template.table_id,
                                                    label = question.name,
                                                    name = name,
                                                    field_type = field_type,
                                                    options = options,
                                                    settings = field_settings,
                                                    require_not_empty = question.require_not_empty,
                                                    comments = question.comments,
                                                    )
            # @ToDo: Call onaccept if this starts doing anything other than just setting 'master'
            # @ToDo: Call set_record_owner() once we start restricting these

            # Link the Field to the Question
            question.update_record(field_id = field_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def dc_question_l10n_onaccept(form):
        """
            On-accept routine for dc_question_l10n:
                - Update the Translations file with translated Options
        """

        form_vars = form.vars

        try:
            question_l10n_id = form_vars.get("id")
        except AttributeError:
            return

        db = current.db
        qtable = db.dc_question
        settings = current.deployment_settings

        if settings.get_dc_response_mobile():
            # Pass Translations to s3_field.settings
            # Read the current Field Settings
            question_id = form_vars.get("question_id")
            ftable = db.s3_field
            query = (qtable.id == question_id) & \
                    (qtable.field_id == ftable.id)
            field = db(query).select(ftable.id,
                                     ftable.settings,
                                     limitby = (0, 1)
                                     ).first()
            field_settings = field.settings
            if field_settings.get("mobile") is None:
                field_settings["mobile"] = {}
            if field_settings["mobile"].get("l10n") is None:
                field_settings["mobile"]["l10n"] = {}
            # Add the L10n options
            language = form_vars.get("language")
            name_l10n = form_vars.get("name_l10n")
            field_settings["mobile"]["l10n"][language] = {"label": name_l10n,
                                                          }
            options_l10n = form_vars.get("options_l10n")
            if options_l10n:
                field_settings["mobile"]["l10n"][language]["options"] = options_l10n
            field.update_record(settings = field_settings)

        if not settings.get_dc_response_web():
            return

        # Read the Question
        ltable = db.dc_question_l10n
        query = (qtable.id == ltable.question_id) & \
                (ltable.id == question_l10n_id)
        question = db(query).select(qtable.field_type,
                                    qtable.options,
                                    ltable.options_l10n,
                                    ltable.language,
                                    limitby=(0, 1)
                                    ).first()

        if question["dc_question.field_type"] in (6, 12):
            # Nothing we need to do
            return

        options = question["dc_question.options"] or []
        options_l10n = question["dc_question_l10n.options_l10n"] or []

        len_options = len(options)
        if len_options != len(options_l10n):
            current.session.error(T("Number of Translated Options don't match original!"))
            return

        # Read existing translations (if any)
        w2pfilename = os.path.join(current.request.folder, "languages",
                                   "%s.py" % question["dc_question_l10n.language"])

        if os.path.exists(w2pfilename):
            translations = read_dict(w2pfilename)
        else:
            translations = {}

        # Add ours
        for i in xrange(len_options):
            original = s3_str(options[i])
            translated = s3_str(options_l10n[i])
            if original != translated:
                translations[original] = translated

        # Write out new file
        write_dict(w2pfilename, translations)

# =============================================================================
class DataCollectionModel(S3Model):
    """
        Results of Assessments / Surveys
        - uses the Dynamic Tables back-end to store Answers
    """

    names = ("dc_target",
             "dc_target_id",
             "dc_target_l10n",
             "dc_response",
             "dc_response_id",
             "dc_answer_form",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        settings = current.deployment_settings

        location_id = self.gis_location_id
        template_id = self.dc_template_id

        # Status (Optional control of workflow)
        #  Draft
        #    - questions can be modified
        #    - cannot hold data
        #    - not visible to normal users (e.g. in mobile client)
        #  Active
        #    - questions cannot be modified
        #    - can hold data
        #    - visible to normal users (e.g. in mobile client)
        #  Inactive
        #    - questions cannot be modified
        #    - can hold data
        #    - not visible to normal users (e.g. in mobile client)

        target_status = settings.get_dc_target_status()
        status_opts = {1: T("Draft"),
                       2: T("Active"),
                       3: T("Inactive"),
                       }

        if target_status:
            # UCCE
            default_status = 1 # Draft
            default_date = None
            date_label = T("Activation Date")
        else:
            default_status = 2 # Active
            default_date = "now"
            date_label = T("Date")

        # =====================================================================
        # Data Collection Target
        # - planning of Assessments / Surveys
        #   (optional step in the process)
        # - can be used to analyse a group of responses
        #
        tablename = "dc_target"
        define_table(tablename,
                     Field("name"),
                     template_id(),
                     Field("status", "integer",
                           default = default_status,
                           label = T("Status"),
                           represent = S3Represent(options = status_opts),
                           requires = IS_IN_SET(status_opts),
                           readable = target_status,
                           writable = target_status,
                           ),
                     s3_date(default = default_date,
                             label = date_label,
                             ),
                     # Enable in-templates as-required
                     s3_language(readable = False,
                                 writable = False,
                                 ),
                     location_id(widget = S3LocationSelector(show_map = False,
                                                             show_postcode = False,
                                                             )),
                     #self.org_organisation_id(),
                     #self.pr_person_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # Components
        add_components(tablename,

                       dc_response = "target_id",

                       dc_target_l10n = "target_id",

                       event_event = {"link": "event_target",
                                      "joinby": "target_id",
                                      "key": "event_id",
                                      "actuate": "replace",
                                      },

                       hrm_training_event = {"link": "hrm_event_target",
                                             "joinby": "target_id",
                                             "key": "training_event_id",
                                             "multiple": False,
                                             "actuate": "replace",
                                             },
                       # Format for S3InlineComponent
                       hrm_event_target = {"joinby": "target_id",
                                           "multiple": False,
                                           },

                       project_project_target = "target_id",
                       project_project = {"link": "project_project_target",
                                          "joinby": "target_id",
                                          "key": "project_id",
                                          "actuate": "replace",
                                          },

                       )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Data Collection Target"),
            title_display = T("Data Collection Target Details"),
            title_list = T("Data Collection Targets"),
            title_update = T("Edit Data Collection Target"),
            title_upload = T("Import Data Collection Targets"),
            label_list_button = T("List Data Collection Targets"),
            label_delete_button = T("Delete Data Collection Target"),
            msg_record_created = T("Data Collection Target added"),
            msg_record_modified = T("Data Collection Target updated"),
            msg_record_deleted = T("Data Collection Target deleted"),
            msg_list_empty = T("No Data Collection Targets currently registered"))

        self.set_method("dc", "target",
                        method = "results",
                        action = dc_TargetReport())

        target_id = S3ReusableField("target_id", "reference %s" % tablename,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dc_target.id")
                                                ),
                                    readable = False,
                                    writable = False,
                                    )

        # =====================================================================
        # Target Translations
        #
        tablename = "dc_target_l10n"
        define_table(tablename,
                     target_id(),
                     s3_language(empty = False),
                     *s3_meta_fields())


        # =====================================================================
        # Answers / Responses
        # - instances of an Assessment / Survey
        # - each of these is a record in the Template's Dynamic Table
        #
        tablename = "dc_response"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     target_id(),
                     template_id(),
                     s3_datetime(default = "now"),
                     # Enable in-templates as-required
                     s3_language(readable = False,
                                 writable = False,
                                 ),
                     location_id(),
                     self.org_organisation_id(),
                     self.pr_person_id(
                        default = current.auth.s3_logged_in_person(),
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # Configuration
        self.configure(tablename,
                       create_next = URL(f="respnse", args=["[id]", "answer"]),
                       # Question Answers are in a Dynamic Component
                       # - however they all have the same component name so add correct one in controller instead!
                       #dynamic_components = True,
                       super_entity = "doc_entity",
                       orderby = "dc_response.date desc",
                       )

        # CRUD strings
        label = settings.get_dc_response_label()
        if label == "Assessment":
            label = T("Assessment")
            crud_strings[tablename] = Storage(
                label_create = T("Create Assessment"),
                title_display = T("Assessment Details"),
                title_list = T("Assessments"),
                title_update = T("Edit Assessment"),
                title_upload = T("Import Assessments"),
                label_list_button = T("List Assessments"),
                label_delete_button = T("Delete Assessment"),
                msg_record_created = T("Assessment added"),
                msg_record_modified = T("Assessment updated"),
                msg_record_deleted = T("Assessment deleted"),
                msg_list_empty = T("No Assessments currently registered"))
        elif label == "Survey":
            label = T("Survey")
            crud_strings[tablename] = Storage(
                label_create = T("Create Survey"),
                title_display = T("Survey Details"),
                title_list = T("Surveys"),
                title_update = T("Edit Survey"),
                title_upload = T("Import Surveys"),
                label_list_button = T("List Surveys"),
                label_delete_button = T("Delete Survey"),
                msg_record_created = T("Survey added"),
                msg_record_modified = T("Survey updated"),
                msg_record_deleted = T("Survey deleted"),
                msg_list_empty = T("No Surveys currently registered"))
        else:
            label = T("Response")
            crud_strings[tablename] = Storage(
                label_create = T("Create Data Collection"),
                title_display = T("Data Collection Details"),
                title_list = T("Data Collections"),
                title_update = T("Edit Data Collection"),
                title_upload = T("Import Data Collections"),
                label_list_button = T("List Data Collections"),
                label_delete_button = T("Delete Data Collection"),
                msg_record_created = T("Data Collection added"),
                msg_record_modified = T("Data Collection updated"),
                msg_record_deleted = T("Data Collection deleted"),
                msg_list_empty = T("No Data Collections currently registered"))

        # @todo: representation including template name, location and date
        #        (not currently required since always hidden)
        represent = S3Represent(lookup=tablename,
                                fields=["date"],
                                )

        # Reusable field
        response_id = S3ReusableField("response_id", "reference %s" % tablename,
                                      label = label,
                                      represent = represent,
                                      requires = IS_ONE_OF(db, "dc_response.id",
                                                           represent,
                                                           ),
                                      comment = S3PopupLink(f="respnse",
                                                            ),
                                      )

        # Components
        add_components(tablename,
                       event_event = {"link": "event_response",
                                      "joinby": "response_id",
                                      "key": "event_id",
                                      "actuate": "replace",
                                      },
                       )

        # =====================================================================
        # Pass names back to global scope (s3.*)
        return {"dc_response_id": response_id,
                "dc_target_id": target_id,
                "dc_answer_form": self.dc_answer_form,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"dc_response_id": lambda **attr: dummy("response_id"),
                "dc_target_id": lambda **attr: dummy("target_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def dc_answer_form(r, tablename):
        """
            Customise the form for Answers to a Template
            Web UI:
                Create the crud_form, autototals, grids, hides & subheadings
            Mobile Client:
                Create the crud_form
                (autototals, grids, hides & subheadings are in the table.settings)

            SCPHIMS calls this in customise_default_table_controller()
            UCCE doesn't need Web UI Answers, so writes to s3_table.settings["mobile_form"] when survey is activated instead
        """

        T = current.T
        db = current.db
        ttable = db.dc_template

        # Mobile form configuration required for both schema and data export
        #mform = r.method == "mform"
        mform = r.tablename == tablename
        if mform:
            # Going direct to Dynamic Table
            dtable = db.s3_table
            query = (dtable.name == tablename) & \
                    (ttable.table_id == dtable.id)
            template = db(query).select(ttable.id,
                                        ttable.layout,
                                        limitby = (0, 1),
                                        ).first()
            template_id = template.id
        else:
            # Going via Component
            template_id = r.record.template_id
            template = db(ttable.id == template_id).select(ttable.layout,
                                                           limitby = (0, 1),
                                                           ).first()
        layout = template.layout

        # Add the Questions
        # Prep for Auto-Totals
        # Prep for Grids
        qtable = db.dc_question
        ltable = db.dc_question_l10n
        ftable = db.s3_field

        language = current.session.s3.language
        if language == current.deployment_settings.get_L10n_default_language():
            translate = False
        else:
            translate = True

        query = (qtable.template_id == template_id) & \
                (qtable.deleted == False)
        left = [ftable.on(ftable.id == qtable.field_id),
                ]
        fields = [ftable.name,
                  ftable.label,
                  qtable.id,
                  qtable.code,
                  qtable.totals,
                  qtable.grid,
                  qtable.show_hidden,
                  ]
        if translate:
            left.append(ltable.on((ltable.question_id == qtable.id) & \
                                  (ltable.language == language)))
            fields.append(ltable.name_l10n)
        rows = db(query).select(*fields,
                                left = left
                                )

        auto_totals = {}
        codes = {}
        grids = {}
        grid_children = {}
        show_hidden = {}
        questions = {}
        for question in rows:
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
                        # @ToDo: Make mandatory in onvalidation
                        raise ValueError("Code required for Grid Questions")
                    rows = [s3_str(T(v)) for v in grid[0]]
                    cols = [s3_str(T(v)) for v in grid[1]]
                    fields = [[0 for x in xrange(len(rows))] for y in xrange(len(cols))]
                    grids[code] = {"r": rows,
                                   "c": cols,
                                   "f": fields,
                                   }
                elif len_grid == 3:
                    # Child Question
                    grid_children[field_name] = grid
                else:
                    current.log.warning("Invalid grid data for %s - ignoring" % (code or field_name))
            hides = question["dc_question.show_hidden"]
            if hides:
                show_hidden[field_name] = {"codes": hides,
                                           "fields": [],
                                           }

            label = None
            if translate:
                label = question.get("dc_question_l10n.name_l10n")
            if not label:
                label = question.get("s3_field.label")
            questions[question["dc_question.id"]] = {"name": field_name,
                                                     "code": code,
                                                     "label": label,
                                                     }

        # Append questions to the form, with subheadings
        crud_fields = []
        cappend = crud_fields.append
        subheadings = {}
        fname = None

        for posn in layout:
            item = layout[posn]
            item_type = item["type"]
            if item_type == "question":
                question = questions[item["id"]]
                fname = question["name"]
                if fname:
                    cappend((question["label"], fname))
                    # @ToDo: If type is options and 'other' field then add this, with suitable displayLogic
                else:
                    # Grid Pseudo-Question
                    fname = question["code"]
                    cappend(S3SQLDummyField(fname))
            elif item_type == "subheading":
                text = None
                if translate:
                    l10n = item.get("l10n")
                    if l10n:
                        text = l10n.get(language)
                if text is None:
                    text = item["text"]
                subheadings[fname] = text
            elif item_type == "instructions":
                do = None
                say = None
                do_item = item.get("do")
                say_item = item.get("say")
                if translate:
                    do_l10n = do_item.get("l10n")
                    if do_l10n:
                        do = do_l10n.get(language)
                    say_l10n = say_item.get("l10n")
                    if say_l10n:
                        say = say_l10n.get(language)
                if do is None:
                    do = do_item.get("text")
                if say is None:
                    say = say_item.get("text")
                cappend(S3SQLInlineInstruction(do=item["do"], say=item["say"]))
            elif item_type == "break":
                cappend(S3SQLSectionBreak())

        # Auto-Totals
        autototals = {}
        for field in auto_totals:
            f = auto_totals[field]
            append = f["fields"].append
            for code in f["codes"]:
                append(codes.get(code))
            autototals[field] = f["fields"]

        # Grids
        # Place the child fields in the correct places in their grids
        if len(grids):
            for child in grid_children:
                code, row, col = grid_children[child]
                try:
                    grids[code]["f"][col - 1][row - 1] = child
                except:
                    current.log.warning("Invalid grid data for %s - ignoring" % code)

        # Hides
        hides = {}
        for field in show_hidden:
            f = show_hidden[field]
            append = f["fields"].append
            for code in f["codes"]:
                fname = codes.get(code) or code
                append(fname)
            hides[field] = f["fields"]

        if mform:
            # Add response_id to form (but keep invisible) so that it can be used for the dataList represent
            f = r.table.response_id
            f.readable = f.writable = False
            crud_fields.insert(0, "response_id")

            crud_form = S3SQLCustomForm(*crud_fields)

            current.s3db.configure(tablename,
                                   crud_form = crud_form,
                                   autototals = autototals,
                                   grids = grids,
                                   show_hidden = hides,
                                   subheadings = subheadings,
                                   )

        else:
            crud_form = S3SQLCustomForm(*crud_fields)

            current.s3db.configure(tablename,
                                   crud_form = crud_form,
                                   subheadings = subheadings,
                                   )

            s3 = current.response.s3

            # Compact JSON encoding
            SEPARATORS = (",", ":")
            jappend = s3.jquery_ready.append

            # Auto-Totals
            for field in autototals:
                jappend('''S3.autoTotals('%s',%s,'%s')''' % \
                    (field,
                     json.dumps(autototals[field], separators=SEPARATORS),
                     tablename))

            # Grids
            if len(grids):
                jappend('''S3.dc_grids(%s,'%s')''' % \
                    (json.dumps(grids, separators=SEPARATORS),
                     tablename))

            # Show Hidden
            for field in hides:
                jappend('''S3.showHidden('%s',%s,'%s')''' % \
                    (field,
                     json.dumps(hides[field], separators=SEPARATORS),
                     tablename))

            # Add JS
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.dc_answer.js" % r.application)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.dc_answer.min.js" % r.application)

# =============================================================================
class dc_TargetReport(S3Method):
    """
        Display a Summary of the Target (i.e. collection of Responses)

        Results in charts for quantitative questions and
                   full text of the qualitative answers

        Used by IFRC bkk_training_evaluation

        @ToDo: Add support for Grids
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "target":
            representation = r.representation
            label = current.deployment_settings.get_dc_response_label()
            if label == "Assessment":
                title = current.T("Assessment Report")
            elif label == "Survey":
                title = current.T("Survey Report")
            elif label == "Evaluation":
                title = current.T("Evaluation Report")
            elif label == "Event":
                title = current.T("Event Report")
            else:
                title = current.T("Target Report")
            if representation == "html":
                output = self.html(r, title, **attr)
                return output
            #elif representation == "pdf":
            #    output = self.pdf(r, title, **attr)
            #    return output
        r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def _extract(self, r, **attr):
        """
            Extract the Data

            @ToDo: Order by Section
            @ToDo: Translate Question Names/Options
        """

        db = current.db
        s3db = current.s3db

        target_id = r.id
        template_id = r.record.template_id

        # Questions
        qtable = s3db.dc_question
        ftable = s3db.s3_field
        query = (qtable.template_id == template_id) & \
                (qtable.deleted == False) & \
                (ftable.id == qtable.field_id)
        questions = db(query).select(qtable.id,
                                     qtable.name,
                                     #qtable.field_type,
                                     qtable.options,
                                     ftable.name,
                                     )

        # Index Dictionary by Fieldname
        FIELD_NAME = "s3_field.name"
        fields = {row[FIELD_NAME]: [] for row in questions}

        # Lookup the Layout & Dynamic Tablename from the Template
        ttable = s3db.dc_template
        dtable = s3db.s3_table
        query = (ttable.id == template_id) & \
                (ttable.table_id == dtable.id)
        template = db(query).select(ttable.layout,
                                    dtable.name,
                                    limitby=(0, 1),
                                    ).first()

        # Responses (for Stats)
        rtable = s3db.dc_response
        ptable = s3db.pr_person
        query = (rtable.target_id == target_id) & \
                (rtable.deleted == False) & \
                (rtable.person_id == ptable.id)
        responses = db(query).select(ptable.id,
                                     ptable.gender,
                                     )

        # Answers
        atable = s3db.table(template["s3_table.name"])
        answer_fields = [atable[f] for f in fields]
        answer_fields.append(rtable.person_id) # For Stats & Contacts
        query = (rtable.target_id == target_id) & \
                (atable.response_id == rtable.id)
        answers = db(query).select(*answer_fields)

        # Build Data structure
        # Collate Answers & collect people for Stats & Contacts
        replied = []
        rappend = replied.append
        can_contact = []
        cappend = can_contact.append

        for row in answers:
            person_id = row["dc_response.person_id"]
            rappend(person_id)
            answer = row[atable]
            for fieldname in answer:
                value = answer[fieldname]
                fields[fieldname].append(value)
                if value == "yes":
                    # Hardcoded to IFRC bkk_training_evaluation!
                    # - the only Question with Yes/No answers!
                    cappend(person_id)

        # Stats
        total = 0
        total_female = 0
        total_replied = 0
        replied_female = 0
        for row in responses:
            total += 1
            gender = row.gender
            if gender == 2:
                total_female += 1
            if row.id in replied:
                total_replied += 1
                if gender == 2:
                    replied_female += 1
        stats = {"total": total,
                 "total_female": total_female,
                 "total_replied": total_replied,
                 "replied_female": replied_female,
                 }

        # Ordered List of Questions
        questions_dict = questions.as_dict(key="dc_question.id")
        questions = []
        qappend = questions.append
        layout = template["dc_template.layout"]
        for posn in layout:
            item = layout[posn]
            if item["type"] != "question":
                # Ignore
                continue
            question_id = item["id"]
            row = questions_dict[question_id]
            question = Storage()
            q = row["dc_question"]
            question.id = q["id"]
            question.name = q["name"]
            answers = fields[row["s3_field"]["name"]]
            options = q["options"]
            if options:
                options = [s3_str(opt) for opt in options]
                unsorted_options = {opt: 0 for opt in options}
                for answer in answers:
                    unsorted_options[answer] += 1
                question.options = [(opt, unsorted_options[opt]) for opt in options]
            else:
                question.options = None
                question.answers = answers

            qappend(question)

        # Contacts
        ctable = s3db.pr_contact
        query = (ptable.id.belongs(can_contact))
        left = ctable.on((ctable.pe_id == ptable.pe_id) & \
                         (ctable.contact_method.belongs(("EMAIL", "SMS"))) & \
                         (ctable.deleted == False))
        rows = db(query).select(ptable.id,
                                ptable.first_name,
                                ptable.middle_name,
                                ptable.last_name,
                                ctable.contact_method,
                                ctable.priority,
                                ctable.value,
                                left = left,
                                orderby = ctable.priority,
                                )
        contacts = {}
        for row in rows:
            person = row.pr_person
            person_id = person.id
            if person_id not in contacts:
                contacts[person_id] = {"name": s3_fullname(person),
                                       "email": None,
                                       "phone": None,
                                       }
            contact_ = contacts[person_id]
            contact = row.pr_contact
            if not contact_["email"] and contact.contact_method == "EMAIL":
                contact_["email"] = contact.value
            elif not contact_["phone"] and contact.contact_method == "SMS":
                contact_["phone"] = contact.value

        for person_id in contacts:
            contact = contacts[person_id]
            repr_str = contact["name"]
            email = contact["email"]
            if email:
                repr_str = "%s <%s>" % (repr_str,
                                        email,
                                        )
            phone = contact["phone"]
            if phone:
                repr_str = "%s %s" % (repr_str,
                                      s3_phone_represent(phone),
                                      )
            contact["repr_str"] = repr_str

        stats["contacts"] = contacts

        return questions, stats

    # -------------------------------------------------------------------------
    def html(self, r, title, **attr):
        """
            HTML Representation
        """

        T = current.T
        table = r.table
        date_represent = table.date.represent

        response = current.response
        s3 = response.s3
        jqready_append = s3.jquery_ready.append

        #target_title = table.template_id.represent(r.record.template_id)

        questions, stats = self._extract(r, **attr)

        table = TABLE()
        json_dumps = json.dumps
        for question in questions:
            table.append(TR(TH(question.name)))
            if question.options:
                # Graph
                svg_id = "svg_%s" % question.id
                table.append(TR(TD(TAG["SVG"](_id=svg_id))))
                data = []
                data_append = data.append
                for opt in question.options:
                    data_append({"o": opt[0],
                                 "v": opt[1],
                                 })
                script = '''S3.dc_results('%s','%s')''' % \
                    ("#%s" % svg_id, json_dumps(data, separators=SEPARATORS))
                jqready_append(script)
            else:
                # Enumerate Answers
                for answer in question.answers:
                    table.append(TR(TD(answer)))

        contacts = P()
        cappend = contacts.append
        _contacts = stats["contacts"]
        for person_id in _contacts:
            cappend(_contacts[person_id]["repr_str"])
            cappend(BR())

        item = DIV(H1(title),
                   H3("%s: %s" % (T("Up To Date"), date_represent(r.utcnow))),
                   P("%i %s (%i %s)" % (stats["total"], T("Participants"), stats["total_female"], T("Female")),
                     BR(),
                     "%i %s (%i %s)" % (stats["total_replied"], T("Replied"), stats["replied_female"], T("Female")),
                     ),
                   table,
                   contacts,
                   )

        output = {"item": item,
                  "title": title,
                  }

        appname = r.application
        s3.stylesheets.append("S3/dc_results.css")
        scripts_append = s3.scripts.append
        if s3.debug:
            scripts_append("/%s/static/scripts/d3/d3.js" % appname)
            scripts_append("/%s/static/scripts/S3/s3.dc_results.js" % appname)
        else:
            scripts_append("/%s/static/scripts/d3/d3.min.js" % appname)
            scripts_append("/%s/static/scripts/S3/s3.dc_results.min.js" % appname)
        response.view = "simple.html"
        return output

    # -------------------------------------------------------------------------
    def pdf(self, r, title, **attr):
        """
            PDF Representation
            @ToDo: Finish this stub when-required
                   (original is project_SummaryReport)
        """

        from s3.codecs.pdf import EdenDocTemplate, S3RL_PDF

        T = current.T
        table = r.table
        date_represent = table.date.represent

        target_title = table.template_id.represent(r.record.template_id)

        report_title = s3_str(title)
        filename = "%s_%s.pdf" % (report_title, s3_str(target_title))

        # @ToDo
        #questions, stats = self._extract(r, **attr)

        # @ToDo
        header = DIV()

        body = DIV(H1(title),
                   H3("%s: %s" % (T("Up To Date"), date_represent(r.utcnow))),
                   table,
                   )

        footer = DIV("%s: %s" % (title, target_title))

        doc = EdenDocTemplate(title=report_title)
        printable_width = doc.printable_width
        get_html_flowable = S3RL_PDF().get_html_flowable
        header_flowable = get_html_flowable(header, printable_width)
        body_flowable = get_html_flowable(body, printable_width)#, styles)
        footer_flowable = get_html_flowable(footer, printable_width)

        # Build the PDF
        doc.build(header_flowable,
                  body_flowable,
                  footer_flowable,
                  )

        # Return the generated PDF
        response = current.response
        from gluon.contenttype import contenttype
        response.headers["Content-Type"] = contenttype(".pdf")
        disposition = "attachment; filename=\"%s\"" % filename
        response.headers["Content-disposition"] = disposition

        return doc.output.getvalue()

# =============================================================================
def dc_rheader(r, tabs=None):
    """ Resource Headers for Data Collection Tool """

    if r.representation != "html":
        return None

    s3db = current.s3db
    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "dc_template":

            tabs = ((T("Basic Details"), None),
                    (T("Questions"), "question"),
                    )

            rheader_fields = (["name"],
                              )

        elif tablename == "dc_question":

            tabs = ((T("Basic Details"), None),
                    (T("Translations"), "question_l10n"),
                    )

            def options(record):
                if record.options:
                    return ", ".join(record.options)
                else:
                    return current.messages["NONE"]

            rheader_fields = ([(T("Question"), "name")],
                              [(T("Options"), options)],
                              ["comments"],
                              )

        elif tablename == "dc_response":

            tabs = ((T("Basic Details"), None, {"native": 1}),
                    (T("Answers"), "answer"),
                    (T("Attachments"), "document"),
                    )

            rheader_fields = [["template_id"],
                              ["location_id"],
                              ["date"],
                              ["person_id"],
                              ]

            db = current.db

            def contacts(record):
                ptable = s3db.pr_person
                ctable = s3db.pr_contact
                query = (ptable.id == record.person_id) & \
                        (ptable.pe_id == ctable.pe_id) & \
                        (ctable.deleted == False)
                data = db(query).select(ctable.value,
                                        ctable.contact_method,
                                        ctable.priority,
                                        orderby = ~ctable.priority,
                                        )
                if data:
                    # Prioritise Phone then Email
                    email = None
                    other = None
                    for contact in data:
                        if contact.contact_method == "SMS":
                            return contact.value
                        elif contact.contact_method == "Email":
                            if not email:
                                email = contact.value
                        else:
                            if not other:
                                other = contact.value
                    return email or other
                else:
                    # @ToDo: Provide an Edit button
                    return A(T("Add"))

            rheader_fields.append([(T("Contact Details"), contacts)])

            has_module = current.deployment_settings.has_module
            if has_module("stats"):
                # @ToDo: deployment_setting, not just presence of module
                def population(record):
                    ptable = s3db.stats_demographic
                    dtable = s3db.stats_demographic_data
                    date_field = dtable.date
                    value_field = dtable.value
                    query = (ptable.name == "Population") & \
                            (dtable.parameter_id == ptable.parameter_id) & \
                            (dtable.location_id == record.location_id) & \
                            (dtable.deleted == False)
                    data = db(query).select(value_field,
                                            date_field,
                                            limitby=(0, 1),
                                            orderby = ~date_field, # @ToDo: Handle case where system stores future predictions
                                            ).first()
                    if data:
                        return value_field.represent(data.value)
                    else:
                        return ""

                rheader_fields.insert(2, [(T("Total Population"), population)])

            if has_module("event"):
                etable = s3db.event_event
                ltable = s3db.event_response
                event_id = ltable.event_id
                date_field = etable.start_date
                query = (ltable.response_id == record.id) & \
                        (etable.id == event_id)
                event = db(query).select(etable.id,
                                         date_field,
                                         limitby=(0, 1)
                                         ).first()

                def event_name(record):
                    if event:
                        return event_id.represent(event.id)
                    else:
                        return ""

                def event_date(record):
                    if event:
                        return date_field.represent(event.start_date)
                    else:
                        return ""

                def event_days(record):
                    if event:
                        timedelta = record.date - event.start_date
                        return timedelta.days
                    else:
                        return ""

                rheader_fields.insert(0, [(event_id.label, event_name)])
                rheader_fields.insert(1, [(date_field.label, event_date)])
                # @ToDo: deployment_setting
                rheader_fields.insert(2, [(T("Number of Days since Event Occurred"), event_days)])

        elif tablename == "dc_target":

            label = current.deployment_settings.get_dc_response_label()
            if label == "Assessment":
                RESPONSES = T("Assessments")
            elif label == "Survey":
                RESPONSES = T("Surveys")
            else:
                RESPONSES = T("Responses")

            tabs = ((T("Basic Details"), None),
                    (T("Report"), "results/"),
                    (RESPONSES, "response"),
                    )

            rheader_fields = (["template_id"],
                              ["location_id"],
                              ["date"],
                              )

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )

    return rheader

# END =========================================================================
