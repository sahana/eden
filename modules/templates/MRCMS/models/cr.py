"""
    MRCMS Shelter Management Extensions

    Copyright: 2023-2026 (c) Sahana Software Foundation

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
           "CRShelterCommissionModel",
           "cr_configure_shelter_note_form",
           )

from collections import OrderedDict

from gluon import current, IS_EMPTY_OR, IS_INT_IN_RANGE, IS_IN_SET, IS_LENGTH, IS_NOT_EMPTY, UL, LI
from gluon.storage import Storage

from s3dal import Field

from core import CommentsField, DataModel, DateField, DateTimeField, WorkflowOptions, \
                 IS_ONE_OF, IS_NOT_ONE_OF, S3Duplicate, \
                 DateFilter, OptionsFilter, TextFilter, \
                 S3Represent, S3PriorityRepresent, CustomForm, InlineComponent, InlineLink, \
                 datahash, get_form_record_id, s3_str, s3_text_represent

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
class CRShelterCommissionModel(DataModel):
    """ Model for Shelter Commission Details """

    names = ("cr_shelter_commission",
             "cr_shelter_commission_demographic",
             "cr_shelter_commission_sector",
             )

    def model(self):

        T = current.T
        db = current.db

        s3 = current.response.s3

        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Target Demographics
        #
        tablename = "cr_shelter_commission_demographic"
        self.define_table(tablename,
                          Field("name",
                                requires = [IS_NOT_EMPTY(),
                                            IS_NOT_ONE_OF(db, "%s.name" % tablename,
                                                          skip_imports = True,
                                                          ),
                                            ],
                                ),
                          CommentsField(),
                          )

        # Table configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       )

        demographic_represent = S3Represent(lookup=tablename)

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Demographic"),
            title_display = T("Demographic Details"),
            title_list = T("Target Demographics"),
            title_update = T("Edit Demographic"),
            label_list_button = T("List Demographics"),
            label_delete_button = T("Delete Demographic"),
            msg_record_created = T("Demographic added"),
            msg_record_modified = T("Demographic updated"),
            msg_record_deleted = T("Demographic deleted"),
            msg_list_empty = T("No Demographics currently defined"),
            )

        # TODO import template and prepop

        # ---------------------------------------------------------------------
        # Commission
        #
        commission_status = WorkflowOptions(("CURRENT", "current", "green"),
                                            ("SUSPENDED", "suspended", "amber"),
                                            ("REVOKED", "revoked", "black"),
                                            ("EXPIRED", "expired", "grey"),
                                            selectable = ("CURRENT", "SUSPENDED", "REVOKED"),
                                            represent = "status",
                                            )
        tablename = "cr_shelter_commission"
        self.define_table(tablename,
                          self.cr_shelter_id(),
                          Field("principal",
                                label = T("Commissioning Organization"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(255, minsize=3),
                                            ],
                                represent = lambda v, row=None: v if v else "-",
                                # TODO comment
                                ),
                          DateField(
                              label = T("Start Date"),
                              default="now",
                              set_min = "#cr_shelter_commission_end_date",
                              ),
                          DateField("end_date",
                              label = T("End Date"),
                              default = None,
                              set_max = "#cr_shelter_commission_date",
                              ),
                          Field("status",
                                label = T("Status"),
                                default = "CURRENT",
                                requires = IS_IN_SET(commission_status.selectable(True),
                                                     zero = None,
                                                     sort = False,
                                                     ),
                                represent = commission_status.represent,
                                ),
                          Field("target_demographic", "reference cr_shelter_commission_demographic",
                                label = T("Target Demographic"),
                                represent = demographic_represent,
                                requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "cr_shelter_commission_demographic.id",
                                                      demographic_represent,
                                                      )),
                                ),
                          Field("capacity", "integer",
                                label = T("Target Capacity"),
                                requires = IS_INT_IN_RANGE(minimum=1),
                                # TODO comment
                                ),
                          CommentsField(),
                          )

        # Components
        self.add_components(tablename,
                            org_sector = {"link": "cr_shelter_commission_sector",
                                          "joinby": "commission_id",
                                          "key": "sector_id",
                                          "actuate": "hide",
                                          },
                            )

        # CRUD form
        crud_form = CustomForm("principal",
                               "date",
                               "end_date",
                               "status",
                               "target_demographic",
                               "capacity",
                               InlineLink("sector",
                                          label = T("Commissioned Services"),
                                          field = "sector_id",
                                          render_list = True,
                                          ),
                               "comments",
                               )

        # List fields
        list_fields = ("principal",
                       "date",
                       "end_date",
                       "status",
                       "target_demographic",
                       "capacity",
                       (T("Commissioned Services"), "sector__link.sector_id"),
                       "comments",
                       )

        # Table configuration
        # TODO onvalidation/onaccept to handle dates+status
        self.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       orderby = "%s.date desc" % tablename,
                       )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Commission"),
            title_display = T("Commission Details"),
            title_list = T("Commissions"),
            title_update = T("Edit Commission"),
            label_list_button = T("List Commissions"),
            label_delete_button = T("Delete Commission"),
            msg_record_created = T("Commission added"),
            msg_record_modified = T("Commission updated"),
            msg_record_deleted = T("Commission deleted"),
            msg_list_empty = T("No Commissions currently registered"),
            )

        # ---------------------------------------------------------------------
        # Commissioned Services (sectors, in this context)
        #
        tablename = "cr_shelter_commission_sector"
        self.define_table(tablename,
                          Field("commission_id", "reference cr_shelter_commission",
                                requires = IS_ONE_OF(db, "cr_shelter_commission.id"),
                                ),
                          self.org_sector_id(empty=False,
                                             represent = SectorListRepresent(lookup="org_sector"),
                                             ),
                          )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        # return None

# =============================================================================
class SectorListRepresent(S3Represent):

    always_list = True

    def render_list(self, value, labels, show_link=True):
        """
            Renders list-type representations from bulk()-results.

            Args:
                value: the list
                labels: the labels as returned from bulk()
                show_link: render references as links, should
                           be the same as used with bulk()
        """

        show_link = show_link and self.show_link

        values = [v for v in value if v is not None]
        if not values:
            return ""

        if show_link:
            labels_ = (labels[v] if v in labels else self.default for v in values)
        else:
            labels_ = sorted(s3_str(labels[v]) if v in labels else self.default for v in values)

        if current.auth.permission.format in ("xlsx", "xls"):
            return ", ".join(labels_)
            #return "\n".join(("- %s" % l) for l in labels_)

        html = UL(_class="service-list")
        for label in labels_:
            html.append(LI(label))

        return html

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
