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
             "dc_section",
             "dc_question",
             "dc_question_l10n",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        settings = current.deployment_settings

        add_components = self.add_components
        configure = self.configure
        define_table = self.define_table

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

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
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  create_onaccept = self.dc_template_create_onaccept,
                  deduplicate = S3Duplicate(),
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        template_id = S3ReusableField("template_id", "reference %s" % tablename,
                                      label = T("Template"),
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
                       dc_section = "template_id",
                       )

        # =====================================================================
        # Template Sections
        #
        # Currently support Sections, SubSections & SubSubSections only
        #
        # @ToDo: l10n
        #
        hierarchical_sections = True # @ToDo: deployment_setting if need to support non-SCPHIMS contexts

        tablename = "dc_section"
        define_table(tablename,
                     template_id(),
                     Field("parent", "reference dc_section",
                           label = T("SubSection of"),
                           ondelete = "RESTRICT",
                           readable = hierarchical_sections,
                           writable = hierarchical_sections,
                           ),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("posn", "integer",
                           label = T("Position"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Reusable field
        represent = S3Represent(lookup=tablename)
        requires = IS_EMPTY_OR(IS_ONE_OF(db, "dc_section.id",
                                         represent,
                                         ))
        if hierarchical_sections:
            hierarchy = "parent"
            # Can't be defined in-line as otherwise get a circular reference
            parent = db[tablename].parent
            parent.represent = represent
            parent.requires = requires

            widget = S3HierarchyWidget(lookup = tablename,
                                       represent = represent,
                                       multiple = False,
                                       leafonly = True,
                                       )
        else:
            hierarchy = None
            widget = None

        section_id = S3ReusableField("section_id", "reference %s" % tablename,
                                     label = T("Section"),
                                     represent = represent,
                                     requires = requires,
                                     sortby = "name",
                                     widget = widget,
                                     #comment = S3PopupLink(f="template",
                                     #                      args=["[id]", "section"], # @ToDo: Build support for this?
                                     #                      tooltip=T("Add a new section to the template"),
                                     #                      ),
                                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Section"),
            title_display = T("Section Details"),
            title_list = T("Sections"),
            title_update = T("Edit Section"),
            label_list_button = T("List Sections"),
            label_delete_button = T("Delete Section"),
            msg_record_created = T("Section added"),
            msg_record_modified = T("Section updated"),
            msg_record_deleted = T("Section deleted"),
            msg_list_empty = T("No Sections currently registered"))

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("name", "parent", "template_id")),
                  hierarchy = hierarchy,
                  orderby = tablename + ".posn",
                  )

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
                     #: T("Organization"),
                     #: T("Location"),
                     #: T("Person"),
                     }

        tablename = "dc_question"
        define_table(tablename,
                     template_id(),
                     section_id(),
                     Field("posn", "integer",
                           label = T("Position"),
                           ),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("code",
                           label = T("Code"),
                           requires = IS_EMPTY_OR(
                                        # Only really needs to be unique per Template
                                        IS_NOT_IN_DB(db, "dc_question.code")
                                        ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Code"),
                                                           T("Unique code for the field - required if using Auto-Totals, Grids or Show Hidden"),
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
                           represent = lambda opt: \
                                            type_opts.get(opt, UNKNOWN_OPT),
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
                     Field("totals", "json",
                           label = T("Totals"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Totals"),
                                                           T("List of fields (codes) which this one is the Total of"),
                                                           ),
                                         ),
                           ),
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
            label_create = T("Create Question"),
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
                           label = T("Translated Options"),
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
    @staticmethod
    def dc_template_create_onaccept(form):
        """
            On-accept routine for dc_template:
                - Create & link a Dynamic Table to use to store the Questions
        """

        form_vars = form.vars
        try:
            template_id = form_vars.id
        except AttributeError:
            return

        db = current.db
        s3db = current.s3db

        title = form_vars.get("name")
        master = form_vars.get("master")
        if master is None:
            # Load full record
            ttable = s3db.dc_template
            record = db(ttable.id == template_id).select(ttable.master,
                                                         ttable.name,
                                                         limitby = (0, 1),
                                                         ).first()
            title = record.name
            master = record.master

        table_settings = {}
        if master == "dc_response":
            settings = current.deployment_settings
            mobile_form = True # For SCPHIMS at least
            mobile_data = settings.get_dc_mobile_data()
            if not settings.get_dc_mobile_inserts():
                table_settings["insertable"] = False
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
        db.s3_field.insert(table_id = table_id,
                           name = "%s_id" % master.split("_", 1)[1],
                           field_type = "reference %s" % master,
                           require_not_empty = True,
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

    # -------------------------------------------------------------------------
    @staticmethod
    def dc_question_onaccept(form):
        """
            On-accept routine for dc_question:
                - Create & link a Dynamic Field to use to store the Question
        """

        try:
            question_id = form.vars.id
        except AttributeError:
            return

        db = current.db

        # Read the full Question
        qtable = db.dc_question
        question = db(qtable.id == question_id).select(qtable.id,
                                                       qtable.template_id,
                                                       qtable.field_id,
                                                       qtable.name,
                                                       qtable.comments,
                                                       qtable.field_type,
                                                       qtable.options,
                                                       qtable.require_not_empty,
                                                       limitby=(0, 1)
                                                       ).first()

        field_type = question.field_type
        field_settings = {}
        options = None
        if field_type == 1:
            field_type = "string"
        elif field_type == 2:
            field_type = "integer"
        elif field_type == 4:
            field_type = "boolean"
            field_settings["mobile"] = {}
            field_settings["mobile"]["widget"] = "checkbox"
        elif field_type == 5:
            T = current.T
            options = [T("Yes"),
                       T("No"),
                       T("Don't Know"),
                       ]
            field_type = "string"
        elif field_type == 6:
            options = question.options
            field_type = "string"
        elif field_type == 7:
            field_type = "date"
        elif field_type == 8:
            field_type = "datetime"
        elif field_type == 9:
            # Grid: Pseudo-question, no dynamic field
            return
        elif field_type == 10:
            field_type = "text"
            field_settings["widget"] = "comments"
        elif field_type == 11:
            field_type = "text"
            field_settings["widget"] = "richtext"
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
            question.update_record(field_id=field_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def dc_question_l10n_onaccept(form):
        """
            On-accept routine for dc_question_l10n:
                - Update the Translations file with translated Options
        """

        try:
            question_l10n_id = form.vars.id
        except AttributeError:
            return

        db = current.db

        # Read the Question
        qtable = db.dc_question
        ltable = db.dc_question_l10n
        query = (qtable.id == ltable.question_id) & \
                (ltable.id == question_l10n_id)
        question = db(query).select(qtable.field_type,
                                    qtable.options,
                                    ltable.options_l10n,
                                    ltable.language,
                                    limitby=(0, 1)
                                    ).first()

        if question["dc_question.field_type"] != 6:
            # Nothing we need to do
            return

        options = question["dc_question.options"]
        options_l10n = question["dc_question_l10n.options_l10n"]

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
        for i in range(len_options):
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

        status_opts = {1: T("Draft"),
                       2: T("Active"),
                       3: T("Inactive"),
                       }

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
                           default = 1,
                           label = T("Status"),
                           represent = S3Represent(options = status_opts),
                           requires = IS_IN_SET(status_opts),
                           ),
                     s3_date(default = "now"),
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
        label = current.deployment_settings.get_dc_response_label()
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
        """

        T = current.T
        db = current.db

        # Mobile form configuration required for both schema and data export
        #mform = r.method == "mform"
        mform = r.tablename == tablename
        if mform:
            # Going direct to Dynamic Table
            dtable = db.s3_table
            ttable = db.dc_template
            query = (dtable.name == tablename) & \
                    (ttable.table_id == dtable.id)
            template = db(query).select(ttable.id,
                                        limitby = (0, 1),
                                        ).first()
            template_id = template.id
        else:
            # Going via Component
            template_id = r.record.template_id

        # Extract the Sections
        # @ToDo: l10n
        stable = db.dc_section
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
        qtable = db.dc_question
        ttable = db.dc_question_l10n
        ftable = db.s3_field

        language = current.session.s3.language
        if language == current.deployment_settings.get_L10n_default_language():
            translate = False
        else:
            # @ToDo: Translate Section names too (for Subheadings)
            translate = True

        query = (qtable.template_id == template_id) & \
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
                  qtable.show_hidden,
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
        show_hidden = {}
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
                        # @ToDo: Make mandatory in onvalidation
                        raise ValueError("Code required for Grid Questions")
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
                    current.log.warning("Invalid grid data for %s - ignoring" % (code or field_name))
            hides = question["dc_question.show_hidden"]
            if hides:
                show_hidden[field_name] = {"codes": hides,
                                           "fields": [],
                                           }

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
            section = s[list(s.items())[0][0]]
            subsections = [{v["posn"]: v} for k, v in section["subsections"].items()]
            subsections.sort()
            section["subsections"] = subsections
            section["questions"].sort()
            for sub in subsections:
                _sub = sub[list(sub.items())[0][0]]
                subsubsections = [{v["posn"]: v} for k, v in _sub["subsubsections"].items()]
                subsubsections.sort()
                _sub["subsubsections"] = subsubsections
                _sub["questions"].sort()
                for subsub in subsubsections:
                    subsub[list(subsub.items())[0][0]]["questions"].sort()

        # Append questions to the form, with subheadings
        crud_fields = []
        cappend = crud_fields.append

        # 1st add those questions without a section (likely the only questions then)
        for q in root_questions:
            question = q[list(q.items())[0][0]]
            fname = question["name"]
            if fname:
                cappend((question["label"], fname))
            else:
                # Grid Pseudo-Question
                fname = question["code"]
                cappend(S3SQLDummyField(fname))
        # Next add those questions with a section (likely the only questions then)
        subheadings = {}
        for s in sections:
            section = s[list(s.items())[0][0]]
            section_name = section["name"]
            # 1st add those questions without a subsection
            questions = section["questions"]
            first = True
            for question in questions:
                question = list(question.items())[0][1]
                fname = question["name"]
                if fname:
                    cappend((question["label"], fname))
                else:
                    # Grid Pseudo-Question
                    fname = question["code"]
                    cappend(S3SQLDummyField(fname))
                if first:
                    subheadings[fname] = section_name
                    first = False
            # Next add those questions in a subsection
            subsections = section["subsections"]
            for sub in subsections:
                _sub = sub[list(sub.items())[0][0]]
                subsection_name = _sub["name"]
                questions = _sub["questions"]
                ffirst = True
                for question in questions:
                    question = list(question.items())[0][1]
                    fname = question["name"]
                    if fname:
                        cappend((question["label"], fname))
                    else:
                        # Grid Pseudo-Question
                        fname = question["code"]
                        cappend(S3SQLDummyField(fname))
                    if ffirst:
                        if first:
                            subheadings[fname] = [section_name, subsection_name]
                            first = False
                        else:
                            subheadings[fname] = subsection_name
                        ffirst = False
                # Next add those questions in a subsubsection
                subsubsections = _sub["subsubsections"]
                for subsub in subsubsections:
                    _subsub = subsub[list(subsub.items())[0][0]]
                    subsubsection_name = _subsub["name"]
                    questions = _subsub["questions"]
                    fffirst = True
                    for question in questions:
                        question = list(question.items())[0][1]
                        fname = question["name"]
                        if fname:
                            cappend((question["label"], fname))
                        else:
                            # Grid Pseudo-Question
                            fname = question["code"]
                            cappend(S3SQLDummyField(fname))
                        if fffirst:
                            if first:
                                subheadings[fname] = [section_name, subsection_name, subsubsection_name]
                                first = False
                                ffirst = False
                            elif ffirst:
                                subheadings[fname] = [subsection_name, subsubsection_name]
                                ffirst = False
                            else:
                                subheadings[fname] = subsubsection_name
                            fffirst = False

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
                                     qtable.posn,
                                     ftable.name,
                                     orderby = qtable.posn,
                                     )

        # Index Dictionary by Fieldname
        FIELD_NAME = "s3_field.name"
        fields = {row[FIELD_NAME]: [] for row in questions}

        # Lookup the Dynamic Tablename from the Template
        ttable = s3db.dc_template
        dtable = s3db.s3_table
        query = (ttable.id == template_id) & \
                (ttable.table_id == dtable.id)
        template = db(query).select(dtable.name,
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
        atable = s3db.table(template.name)
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

        # List of Questions
        ID = "dc_question.id"
        NAME = "dc_question.name"
        OPTIONS = "dc_question.options"
        for question in questions:
            question.id = question[ID]
            question.name = question[NAME]
            answers = fields[question[FIELD_NAME]]
            options = question[OPTIONS]
            if options:
                options = [s3_str(opt) for opt in options]
                unsorted_options = {opt: 0 for opt in options}
                for answer in answers:
                    unsorted_options[answer] += 1
                question.options = [(opt, unsorted_options[opt]) for opt in options]
            else:
                question.options = None
                question.answers = answers

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
                    (T("Sections"), "section"),
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
