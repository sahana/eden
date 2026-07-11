"""
    MRCMS Shelter Management Extensions

    Copyright: 2023 (c) AHSS

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

__all__ = ("CRShelterNoteModel",
           "cr_configure_shelter_note_form",
           )

from collections import OrderedDict

from gluon import current, IS_IN_SET
from gluon.storage import Storage

from s3dal import Field

from core import CommentsField, DataModel, DateTimeField, WorkflowOptions, \
                 DateFilter, OptionsFilter, TextFilter, \
                 S3PriorityRepresent, CustomForm, InlineComponent, \
                 datahash, get_form_record_id, s3_text_represent

# =============================================================================
class CRShelterNoteModel(DataModel):
    """ Model for Shelter Notes """

    names = ("cr_shelter_note",
             )

    def model(self):

        T = current.T

        auth = current.auth
        s3 = current.response.s3

        crud_strings = s3.crud_strings

        logged_in_person = auth.s3_logged_in_person()

        # ---------------------------------------------------------------------
        # Note
        #
        note_types = (("status", T("Status Report")),
                      ("incident", T("Incident Report")),
                      ("advice", T("Advice")),
                      ("other", T("Other")),
                      )
        type_represent = S3PriorityRepresent(dict(note_types),
                                             {"status": "lightblue",
                                              "incident": "blue",
                                              "advice": "amber",
                                              "other": "grey",
                                              }).represent

        NOTE_STATUS = WorkflowOptions(("open", T("In Progress"), "amber"),
                                      ("closed", T("Done##ready"), "green"),
                                      none = "open",
                                      )

        tablename = "cr_shelter_note"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          self.cr_shelter_id(empty=False),
                          self.pr_person_id(label = T("Author"),
                                            default = logged_in_person,
                                            writable = False,
                                            comment = None,
                                            ),
                          DateTimeField(label = T("Date"),
                                        default = "now",
                                        future = 0,
                                        ),
                          Field("type",
                                label = T("Type"),
                                default = "status",
                                requires = IS_IN_SET(note_types,
                                                     sort = False,
                                                     zero = None,
                                                     ),
                                represent = type_represent,
                                ),
                          Field("note", "text",
                                label = T("Details"),
                                represent = s3_text_represent,
                                ),
                          Field("status",
                                label = T("Status"),
                                default = "open",
                                requires = IS_IN_SET(NOTE_STATUS.selectable(),
                                                     zero = None,
                                                     sort = False,
                                                     ),
                                represent = NOTE_STATUS.represent,
                                comment = T('Status "done" marks the note as final and prevents further modifications'),
                                ),
                          Field("vhash",
                                readable = False,
                                writable = False,
                                ),
                          CommentsField(),
                          )

        # List Fields
        list_fields = ["shelter_id",
                       "date",
                       "person_id",
                       "type",
                       "note",
                       "status",
                       ]

        # Filter Widgets
        filter_widgets = [TextFilter(["note",
                                      "person_id$first_name",
                                      "person_id$last_name",
                                      ],
                                     label = T("Search"),
                                     ),
                          OptionsFilter("type",
                                        options = OrderedDict(note_types),
                                        sort = False,
                                        hidden = True,
                                        ),
                          DateFilter("date",
                                     use_time = False,
                                     hidden = True,
                                     ),
                          OptionsFilter("status",
                                        options = OrderedDict(NOTE_STATUS.selectable()),
                                        sort = False,
                                        hidden = True,
                                        ),
                          ]

        # Table Configuration
        self.configure(tablename,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       pdf_format = "list",
                       pdf_fields = list_fields,
                       onaccept = self.shelter_note_onaccept,
                       orderby = "%s.date desc" % tablename,
                       super_entity = "doc_entity",
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Note"),
            title_display = T("Note Details"),
            title_list = T("Notes"),
            title_update = T("Edit Note"),
            label_list_button = T("List Notes"),
            label_delete_button = T("Delete Note"),
            msg_record_created = T("Note added"),
            msg_record_modified = T("Note updated"),
            msg_record_deleted = T("Note deleted"),
            msg_list_empty = T("No Notes found"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        # return None

    # -------------------------------------------------------------------------
    @staticmethod
    def shelter_note_onaccept(form):
        """
            Onaccept of shelter note:
                - produce a data hash when closed
        """

        record_id = get_form_record_id(form)
        if not record_id:
            return

        db = current.db
        s3db = current.s3db

        table = s3db.cr_shelter_note
        query = (table.id == record_id)
        record = db(query).select(table.id,
                                  table.shelter_id,
                                  table.person_id,
                                  table.date,
                                  table.note,
                                  table.status,
                                  table.vhash,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return

        if record.status == "closed" and not record.vhash:
            date = record.date
            if date:
                date = date.replace(microsecond=0).isoformat()
            vhash = datahash(record.shelter_id,
                             record.person_id,
                             date,
                             record.note,
                             )
            record.update_record(vhash = vhash,
                                 modified_by = table.modified_by,
                                 modified_on = table.modified_on,
                                 )

# =============================================================================
def cr_configure_shelter_note_form(r):
    """
        Configures the form for shelter notes depending on record status

        Args:
            r: the CRUDRequest

        Notes:
            - entries can only be modified or deleted by the original author
            - once closed, all fields are read-only and the entry can no longer
              be deleted
            - exception: the comments field can always be edited by all users
    """

    T = current.T
    s3db = current.s3db

    component = r.component
    table = component.table

    readonly = True
    deletable = False

    if r.component_id:

        component.load()
        record = component.records().first()

        if record and \
           record.person_id == current.auth.s3_logged_in_person() and \
           not record.vhash:
            readonly = False
            deletable = True

    elif r.method in (None, "create"):

        field = table.comments
        field.readable = field.writable = False
        readonly = False

    component.configure(deletable = deletable)

    if readonly:
        # Make all fields read-only except comments
        for fn in table.fields:
            if fn != "comments":
                field = table[fn]
                field.writable = False
                field.comment = None
        # Hide status-field
        field = table.status
        field.readable = False

    # Configure inline documents
    documents = InlineComponent("document",
                                name = "file",
                                label = T("Documents"),
                                fields = ["name", "file", "comments"],
                                filterby = {"field": "file",
                                            "options": "",
                                            "invert": True,
                                            },
                                readonly = readonly,
                                )

    # Configure CRUD form
    s3db.configure("cr_shelter_note",
                   crud_form = CustomForm("date",
                                          "person_id",
                                          "type",
                                          #"subject",
                                          "note",
                                          documents,
                                          "status",
                                          "comments",
                                          ),
                   )

# END =========================================================================
