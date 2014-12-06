# -*- coding: utf-8 -*-

""" Sahana Eden Document Library

    @copyright: 2011-2014 (c) Sahana Software Foundation
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

__all__ = ("S3DocumentLibrary",
           "S3DocSitRepModel",
           "doc_image_represent",
           "doc_document_list_layout",
           )

import os

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3DocumentLibrary(S3Model):

    names = ("doc_entity",
             "doc_document",
             "doc_document_id",
             "doc_image",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        person_comment = self.pr_person_comment
        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # Shortcuts
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        folder = current.request.folder
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Document-referencing entities
        #
        entity_types = Storage(asset_asset=T("Asset"),
                               cms_post=T("Post"),
                               cr_shelter=T("Shelter"),
                               deploy_mission=T("Mission"),
                               doc_sitrep=T("Situation Report"),
                               event_incident=T("Incident"),
                               event_incident_report=T("Incident Report"),
                               hms_hospital=T("Hospital"),
                               hrm_human_resource=T("Human Resource"),
                               inv_adj=T("Stock Adjustment"),
                               inv_warehouse=T("Warehouse"),
                               # @ToDo: Deprecate
                               irs_ireport=T("Incident Report"),
                               pr_group=T("Team"),
                               project_project=T("Project"),
                               project_activity=T("Project Activity"),
                               project_framework=T("Project Framework"),
                               project_task=T("Task"),
                               org_office=T("Office"),
                               org_facility=T("Facility"),
                               org_group=T("Organization Group"),
                               # @ToDo: Deprecate
                               stats_people=T("People"),
                               vulnerability_document=T("Vulnerability Document"),
                               vulnerability_risk=T("Risk"),
                               vulnerability_evac_route=T("Evacuation Route"),
                               )

        tablename = "doc_entity"
        self.super_entity(tablename, "doc_id", entity_types)

        # Components
        doc_id = "doc_id"
        self.add_components(tablename,
                            doc_document = doc_id,
                            doc_image = doc_id,
                            )

        # ---------------------------------------------------------------------
        # Documents
        #
        tablename = "doc_document"
        define_table(tablename,
                     # Instance
                     self.stats_source_superlink,
                     # Component not instance
                     super_link(doc_id, "doc_entity"),
                     # @ToDo: Remove since Site Instances are doc entities?
                     super_link("site_id", "org_site"),
                     Field("file", "upload",
                           autodelete = True,
                           represent = self.doc_file_represent,
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "uploads"),
                           ),
                     Field("mime_type",
                           readable = False,
                           writable = False,
                           ),
                     Field("name", length=128,
                           # Allow Name to be added onvalidation
                           requires = IS_EMPTY_OR(IS_LENGTH(128)),
                           label = T("Name")
                           ),
                     Field("url",
                           label = T("URL"),
                           represent = lambda url: \
                            url and A(url, _href=url) or NONE,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("has_been_indexed", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     person_id(
                        # Enable when-required
                        label = T("Author"),
                        readable = False,
                        writable = False,
                        comment = person_comment(T("Author"),
                                                 T("The Author of this Document (optional)"))
                        ),
                     organisation_id(# Enable when-required
                                     readable = False,
                                     writable = False,
                                     ),
                     s3_date(label = T("Date Published"),
                             ),
                     # @ToDo: Move location to link table
                     location_id(# Enable when-required
                                 readable = False,
                                 writable = False,
                                 ),
                     s3_comments(),
                     Field("checksum",
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Reference Document"),
            title_display = T("Document Details"),
            title_list = T("Documents"),
            title_update = T("Edit Document"),
            label_list_button = T("List Documents"),
            label_delete_button = T("Delete Document"),
            msg_record_created = T("Document added"),
            msg_record_modified = T("Document updated"),
            msg_record_deleted = T("Document deleted"),
            msg_list_empty = T("No Documents found")
        )

        # Search Method

        # Resource Configuration
        if current.deployment_settings.get_base_solr_url():
            onaccept = self.document_onaccept
            ondelete = self.document_ondelete
        else:
            onaccept = None
            ondelete = None

        configure(tablename,
                  context = {"organisation": "organisation_id",
                             "person": "person_id",
                             "site": "site_id",
                             },
                  deduplicate = self.document_duplicate,
                  list_layout = doc_document_list_layout,
                  onaccept = onaccept,
                  ondelete = ondelete,
                  onvalidation = self.document_onvalidation,
                  super_entity = "stats_source",
                  )

        # Reusable field
        represent = doc_DocumentRepresent(lookup = tablename,
                                          fields = ["name", "file", "url"],
                                          labels = "%(name)s",
                                          show_link = True)

        document_id = S3ReusableField("document_id", "reference %s" % tablename,
                                      label = T("Document"),
                                      ondelete = "CASCADE",
                                      represent = represent,
                                      requires = IS_ONE_OF(db,
                                                           "doc_document.id",
                                                           represent),
                                      )

        # ---------------------------------------------------------------------
        # Images
        #
        # @ToDo: Field to determine which is the default image to use for
        #        e.g. a Map popup (like the profile picture)
        #        readable/writable=False except in the cases where-needed
        #
        doc_image_type_opts = {1:  T("Photograph"),
                               2:  T("Map"),
                               3:  T("Document Scan"),
                               99: T("other")
                               }

        tablename = "doc_image"
        define_table(tablename,
                     # Component not instance
                     super_link(doc_id, "doc_entity"),
                     super_link("pe_id", "pr_pentity"), # @ToDo: Remove & make Persons doc entities instead?
                     super_link("site_id", "org_site"), # @ToDo: Remove since Site Instances are doc entities?
                     Field("file", "upload", autodelete=True,
                           represent = doc_image_represent,
                           requires = IS_EMPTY_OR(
                                        IS_IMAGE(extensions=(s3.IMAGE_EXTENSIONS)),
                                        # Distingish from prepop
                                        null = "",
                                      ),
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "uploads",
                                                       "images"),
                           widget = S3ImageCropWidget((600, 600)),
                           ),
                     Field("mime_type",
                           readable = False,
                           writable = False,
                           ),
                     Field("name", length=128,
                           label = T("Name"),
                           # Allow Name to be added onvalidation
                           requires = IS_EMPTY_OR(IS_LENGTH(128)),
                           ),
                     Field("url",
                           label = T("URL"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("type", "integer",
                           default = 1,
                           label = T("Image Type"),
                           represent = lambda opt: \
                            doc_image_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(doc_image_type_opts,
                                                zero=None),
                           ),
                     person_id(label = T("Author"),
                               ),
                     organisation_id(),
                     s3_date(label = T("Date Taken"),
                             ),
                     # @ToDo: Move location to link table
                     location_id(),
                     s3_comments(),
                     Field("checksum",
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Photo"),
            title_display = T("Photo Details"),
            title_list = T("Photos"),
            title_update = T("Edit Photo"),
            label_list_button = T("List Photos"),
            label_delete_button = T("Delete Photo"),
            msg_record_created = T("Photo added"),
            msg_record_modified = T("Photo updated"),
            msg_record_deleted = T("Photo deleted"),
            msg_list_empty = T("No Photos found"))

        # Resource Configuration
        configure(tablename,
                  deduplicate = self.document_duplicate,
                  onvalidation = lambda form: \
                            self.document_onvalidation(form, document=False)
                  )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return dict(doc_document_id = document_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """
        
        document_id = S3ReusableField("document_id", "integer",
                                      readable=False, writable=False)

        return dict(doc_document_id = document_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def doc_file_represent(file):
        """ File representation """

        if file:
            try:
                # Read the filename from the file
                filename = current.db.doc_document.file.retrieve(file)[0]
            except IOError:
                return current.T("File not found")
            else:
                return A(filename,
                         _href=URL(c="default", f="download", args=[file]))
        else:
            return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def document_duplicate(item):
        """ Import item de-duplication """

        data = item.data
        query = None
        file = data.get("file")
        if file:
            table = item.table
            query = (table.file == file)
        else:
            url = data.get("url")
            if url:
                table = item.table
                query = (table.url == url)

        if query:
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def document_onvalidation(form, document=True):
        """ Form validation for both, documents and images """

        form_vars = form.vars
        doc = form_vars.file

        if doc is None:
            # If this is a prepop, then file not in form
            # Interactive forms with empty doc has this as "" not None
            return

        if not document:
            encoded_file = form_vars.get("imagecrop-data", None)
            if encoded_file:
                # S3ImageCropWidget
                import base64
                import uuid
                metadata, encoded_file = encoded_file.split(",")
                filename, datatype, enctype = metadata.split(";")
                f = Storage()
                f.filename = uuid.uuid4().hex + filename
                import cStringIO
                f.file = cStringIO.StringIO(base64.decodestring(encoded_file))
                form_vars.file = f
                if not form_vars.name:
                    form_vars.name = filename

        if not hasattr(doc, "file") and not doc and not form_vars.url:
            if document:
                msg = current.T("Either file upload or document URL required.")
            else:
                msg = current.T("Either file upload or image URL required.")
            form.errors.file = msg
            form.errors.url = msg


        if hasattr(doc, "file"):
            name = form_vars.name
            if not name:
                # Use the filename
                form_vars.name = doc.filename
        else:
            id = current.request.post_vars.id
            if id:
                if document:
                    tablename = "doc_document"
                else:
                    tablename = "doc_image"

                db = current.db
                table = db[tablename]
                record = db(table.id == id).select(table.file,
                                                   limitby=(0, 1)).first()
                if record:
                    name = form_vars.name
                    if not name:
                        # Use the filename
                        form_vars.name = table.file.retrieve(record.file)[0]

        # Do a checksum on the file to see if it's a duplicate
        #import cgi
        #if isinstance(doc, cgi.FieldStorage) and doc.filename:
        #    f = doc.file
        #    form_vars.checksum = doc_checksum(f.read())
        #    f.seek(0)
        #    if not form_vars.name:
        #        form_vars.name = doc.filename

        #if form_vars.checksum is not None:
        #    # Duplicate allowed if original version is deleted
        #    query = ((table.checksum == form_vars.checksum) & \
        #             (table.deleted == False))
        #    result = db(query).select(table.name,
        #                              limitby=(0, 1)).first()
        #    if result:
        #        doc_name = result.name
        #        form.errors["file"] = "%s %s" % \
        #                              (T("This file already exists on the server as"), doc_name)

    # -------------------------------------------------------------------------
    @staticmethod
    def document_onaccept(form):
        """
            Build a full-text index
        """
        
        form_vars = form.vars
        doc = form_vars.file
       
        table = current.db.doc_document

        document = json.dumps(dict(filename=doc,
                                   name=table.file.retrieve(doc)[0],
                                   id=form_vars.id,
                                   ))

        current.s3task.async("document_create_index",
                             args = [document])

    # -------------------------------------------------------------------------
    @staticmethod
    def document_ondelete(row):
        """
            Remove the full-text index
        """
        
        db = current.db
        table = db.doc_document
        record = db(table.id == row.id).select(table.file,
                                               limitby=(0, 1)).first()

        document = json.dumps(dict(filename=record.file,
                                   id=row.id,
                                   ))
        
        current.s3task.async("document_delete_index",
                             args = [document])

# =============================================================================
def doc_image_represent(filename):
    """
        Represent an image as a clickable thumbnail

        @param filename: name of the image file
    """

    if not filename:
        return current.messages["NONE"]

    return DIV(A(IMG(_src=URL(c="default", f="download",
                              args=filename),
                     _height=40),
                     _class="zoom",
                     _href=URL(c="default", f="download",
                               args=filename)))

    # @todo: implement/activate the JavaScript for this:
    #import uuid
    #anchor = "zoom-media-image-%s" % uuid.uuid4()
    #return DIV(A(IMG(_src=URL(c="default", f="download",
                              #args=filename),
                     #_height=40),
                     #_class="zoom",
                     #_href="#%s" % anchor),
               #DIV(IMG(_src=URL(c="default", f="download",
                                #args=filename),
                       #_width=600),
                       #_id="%s" % anchor,
                       #_class="hide"))

# =============================================================================
def doc_checksum(docstr):
    """ Calculate a checksum for a file """

    import hashlib

    converted = hashlib.sha1(docstr).hexdigest()
    return converted

# =============================================================================
def doc_document_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Documents, e.g. on the HRM Profile

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["doc_document.id"]
    item_class = "thumbnail"

    raw = record._row
    title = record["doc_document.name"]
    file = raw["doc_document.file"] or ""
    url = raw["doc_document.url"] or ""
    date = record["doc_document.date"]
    comments = raw["doc_document.comments"] or ""

    if file:
        try:
            doc_name = current.s3db.doc_document.file.retrieve(file)[0]
        except (IOError, TypeError):
            doc_name = current.messages["NONE"]
        doc_url = URL(c="default", f="download",
                      args=[file])
        body = P(I(_class="icon-paperclip"),
                 " ",
                 SPAN(A(doc_name,
                        _href=doc_url,
                        )
                      ),
                 " ",
                 _class="card_1_line",
                 )
    elif url:
        body = P(I(_class="icon-globe"),
                 " ",
                 SPAN(A(url,
                        _href=url,
                        )),
                 " ",
                 _class="card_1_line",
                 )
    else:
        # Shouldn't happen!
        body = P(_class="card_1_line")

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.doc_document
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="doc", f="document",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Document"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(I(_class="icon"),
                   SPAN(" %s" % title,
                        _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(body,
                           P(SPAN(comments),
                             " ",
                             _class="card_manylines",
                             ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
class doc_DocumentRepresent(S3Represent):
    """ Representation of Documents """

    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

            @param k: the key (doc_document.id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        if row:
            try:
                filename = row["doc_document.file"]
                url = row["doc_document.url"]
            except AttributeError:
                return v
            else:
                if filename:
                    url = URL(c="default", f="download", args=filename)
                    return A(v, _href=url)
                elif url:
                    return A(v, _href=url)
        return v

# =============================================================================
class S3DocSitRepModel(S3Model):
    """
        Situation Reports
    """

    names = ("doc_sitrep",
             "doc_sitrep_id",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Situation Reports
        # - can be aggregated by OU
        #
        tablename = "doc_sitrep"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          Field("name", length=128,
                               label = T("Name"),
                               ),
                          Field("description", "text",
                                label = T("Description"),
                                represent = lambda body: XML(body),
                                widget = s3_richtext_widget,
                                ),
                          self.org_organisation_id(),
                          self.gis_location_id(
                            widget = S3LocationSelector(show_map = False),
                            ),
                          s3_date(default = "now",
                                  ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Situation Report"),
                title_display = T("Situation Report Details"),
                title_list = T("Situation Reports"),
                title_update = T("Edit Situation Report"),
                title_upload = T("Import Situation Reports"),
                label_list_button = T("List Situation Reports"),
                label_delete_button = T("Delete Situation Report"),
                msg_record_created = T("Situation Report added"),
                msg_record_modified = T("Situation Report updated"),
                msg_record_deleted = T("Situation Report deleted"),
                msg_list_empty = T("No Situation Reports currently registered"))

        crud_form = S3SQLCustomForm("name",
                                    "description",
                                    "organisation_id",
                                    "location_id",
                                    "date",
                                    S3SQLInlineComponent(
                                        "document",
                                        name = "document",
                                        label = T("Attachments"),
                                        fields = [("", "file")],
                                    ),
                                    "comments",
                                    )

        if current.deployment_settings.get_org_branches():
            org_filter = S3HierarchyFilter("organisation_id",
                                           leafonly = False,
                                           )
        else:
            org_filter = S3OptionsFilter("organisation_id",
                                         #filter = True,
                                         #header = "",
                                         )

        filter_widgets = [org_filter,
                          S3LocationFilter(),
                          S3DateFilter("date"),
                          ]

        self.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = ["date",
                                      "event_sitrep.incident_id",
                                      "location_id$L1",
                                      "location_id$L2",
                                      "location_id$L3",
                                      "organisation_id",
                                      "name",
                                      (T("Attachments"), "document.file"),
                                      "comments",
                                      ],
                       super_entity = "doc_entity",
                       )

        # Components
        self.add_components(tablename,
                            event_sitrep = {"name": "event_sitrep",
                                            "joinby": "sitrep_id",
                                            },
                            event_incident = {"link": "event_sitrep",
                                              "joinby": "sitrep_id",
                                              "key": "incident_id",
                                              "actuate": "hide",
                                              "multiple": "False",
                                              #"autocomplete": "name",
                                              "autodelete": False,
                                              },
                            )

        represent = S3Represent(lookup=tablename)

        sitrep_id = S3ReusableField("sitrep_id", "reference %s" % tablename,
                                    label = T("Situation Report"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "doc_sitrep.id",
                                                          represent,
                                                          orderby="doc_sitrep.name",
                                                          sort=True)),
                                    sortby = "name",
                                    )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(doc_sitrep_id = sitrep_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(doc_sitrep_id = lambda **attr: dummy("sitrep_id"),
                    )

# END =========================================================================
