# -*- coding: utf-8 -*-

""" Sahana Eden Data Collection Models
    - a front-end UI to manage Assessments which uses the Dynamic Tables back-end

    @copyright: 2014-2017 (c) Sahana Software Foundation
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
           "dc_rheader",
           )

from gluon import *

from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class DataCollectionTemplateModel(S3Model):
    """
        Templates to use for Assessments / Surveys
        - uses the Dynamic Tables back-end to store Questions
    """

    names = ("dc_template",
             "dc_template_id",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table
        add_components = self.add_components

        # =====================================================================
        # Data Collection Template
        #
        tablename = "dc_template"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
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

        self.configure(tablename,
                       create_onaccept = self.dc_template_create_onaccept,
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
            title_upload = T("Import Templates"),
            label_list_button = T("List Templates"),
            label_delete_button = T("Delete Template"),
            msg_record_created = T("Template added"),
            msg_record_modified = T("Template updated"),
            msg_record_deleted = T("Template deleted"),
            msg_list_empty = T("No Templates currently registered"))

        # Components
        add_components(tablename,
                       s3_field = {"name": "question",
                                   "link": "dc_template_question",
                                   "joinby": "template_id",
                                   "key": "field_id",
                                   "actuate": "replace",
                                   "autodelete": False,
                                   },
                       )

        # =====================================================================
        # Template <=> Question link table
        #
        tablename = "dc_template_question"
        define_table(tablename,
                     template_id(),
                     self.s3_field_id(),
                     *s3_meta_fields())

        # CRUD strings - unused
        #crud_strings[tablename] = Storage(
        #    label_create = T("Create Question"),
        #    title_display = T("Question Details"),
        #    title_list = T("Questions"),
        #    title_update = T("Edit Question"),
        #    title_upload = T("Import Questions"),
        #    label_list_button = T("List Questions"),
        #    label_delete_button = T("Delete Question"),
        #    msg_record_created = T("Question added"),
        #    msg_record_modified = T("Question updated"),
        #    msg_record_deleted = T("Question deleted"),
        #    msg_list_empty = T("No Questions currently registered"))

        # =====================================================================
        # Pass names back to global scope (s3.*)
        return dict(dc_template_id = template_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return dict(dc_template_id = lambda **attr: dummy("template_id"),
                    )

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

        # Create the Dynamic Table
        table_id = current.s3db.s3_table.insert(title = form_vars.get("name"))

        # Add a Field to link Answers to the Collection
        db = current.db
        db.s3_field.insert(table_id = table_id,
                           name = "collection_id",
                           field_type = "reference dc_collection",
                           label = "Collection",
                           require_not_empty = True,
                           component_key = True,
                           component_alias = "answer",
                           component_tab = True,
                           )

        # Link this Table to the Template
        db(db.dc_template.id == template_id).update(table_id=table_id)

# =============================================================================
class DataCollectionModel(S3Model):
    """
        Results of Assessments / Surveys
        - uses the Dynamic Tables back-end to store Answers
    """

    names = ("dc_target",
             "dc_target_id",
             "dc_collection",
             "dc_collection_id",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        location_id = self.gis_location_id
        template_id = self.dc_template_id

        # =====================================================================
        # Data Collection Target
        # - planning of Assessments / Surveys
        # - optional step in the process
        #
        tablename = "dc_target"
        define_table(tablename,
                     template_id(),
                     s3_date(default = "now"),
                     location_id(widget = S3LocationSelector(show_map=False)),
                     #self.org_organisation_id(),
                     #self.pr_person_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # Components
        add_components(tablename,
                       dc_collection = "target_id",
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

        target_id = S3ReusableField("target_id", "reference %s" % tablename,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "dc_target.id")
                                                ),
                                    readable = False,
                                    writable = False,
                                    )

        # =====================================================================
        # Data Collections
        # - instances of an Assessment / Survey
        #
        tablename = "dc_collection"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     target_id(),
                     template_id(),
                     s3_date(default = "now"),
                     location_id(),
                     self.org_organisation_id(),
                     self.pr_person_id(
                        default = current.auth.s3_logged_in_person(),
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # Configuration
        self.configure(tablename,
                       # Answers are in a Dynamic Component
                       dynamic_components = True,
                       super_entity = "doc_entity",
                       orderby = "dc_collection.date desc",
                       )

        # CRUD strings
        label = current.deployment_settings.get_dc_collection_label()
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
            label = T("Data Collection")
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
        collection_id = S3ReusableField("collection_id", "reference %s" % tablename,
                                        label = label,
                                        represent = represent,
                                        requires = IS_ONE_OF(db, "dc_collection.id",
                                                             represent,
                                                             ),
                                        comment = S3PopupLink(f="collection",
                                                              ),
                                        )

        # =====================================================================
        # Pass names back to global scope (s3.*)
        return dict(dc_collection_id = collection_id,
                    dc_target_id = target_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return dict(dc_collection_id = lambda **attr: dummy("collection_id"),
                    dc_target_id = lambda **attr: dummy("target_id"),
                    )

# =============================================================================
def dc_rheader(r, tabs=None):
    """ Resource Headers for Data Collection Tool """

    T = current.T
    if r.representation != "html":
        return None

    resourcename = r.name

    if resourcename == "template":

        tabs = ((T("Basic Details"), None),
                (T("Questions"), "question"),
                )

        rheader_fields = (["name"],
                          )
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "collection":

        tabs = ((T("Basic Details"), None),
                (T("Answers"), "answer"),
                (T("Attachments"), "document"),
                )

        rheader_fields = (["template_id"],
                          ["location_id"],
                          ["date"],
                          )
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "target":

        tabs = ((T("Basic Details"), None),
                (T("Collections"), "collection"),
                )

        rheader_fields = (["template_id"],
                          ["location_id"],
                          ["date"],
                          )
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    else:
        rheader = ""

    return rheader

# END =========================================================================
