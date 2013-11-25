# -*- coding: utf-8 -*-

""" Sahana Eden Document Library

    @copyright: 2011-2013 (c) Sahana Software Foundation
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

__all__ = ["S3DocumentLibrary",
           "doc_image_represent",
           "doc_render_documents",
          ]

import os

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3DocumentLibrary(S3Model):

    names = ["doc_entity",
             "doc_document",
             "doc_document_id",
             "doc_image",
             ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        person_comment = self.pr_person_comment
        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        folder = current.request.folder
        super_key = self.super_key
        super_link = self.super_link

        if settings.get_org_autocomplete():
            org_widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
        else:
            org_widget = None

        # ---------------------------------------------------------------------
        # Document-referencing entities
        #
        entity_types = Storage(asset_asset=T("Asset"),
                               cms_post=T("Post"),
                               deploy_mission=T("Mission"),
                               irs_ireport=T("Incident Report"),
                               project_project=T("Project"),
                               project_activity=T("Project Activity"),
                               project_framework=T("Project Framework"),
                               project_task=T("Task"),
                               hms_hospital=T("Hospital"),
                               hrm_human_resource=T("Human Resource"),
                               org_office=T("Office"),
                               org_facility=T("Facility"),
                               cr_shelter=T("Shelter"),
                               inv_adj=T("Stock Adjustment"),
                               inv_warehouse=T("Warehouse"),
                               stats_people=T("People"),
                               vulnerability_document=T("Vulnerability Document"),
                               vulnerability_risk=T("Risk"),
                               vulnerability_evac_route=T("Evacuation Route"),
                               )

        tablename = "doc_entity"
        doc_entity = self.super_entity(tablename, "doc_id", entity_types)

        # Components
        add_component("doc_document", doc_entity=super_key(doc_entity))
        add_component("doc_image", doc_entity=super_key(doc_entity))

        # ---------------------------------------------------------------------
        # Documents
        #
        tablename = "doc_document"
        table = define_table(tablename,
                             # Instance
                             self.stats_source_superlink,
                             # Component not instance
                             super_link("doc_id", doc_entity),
                             # @ToDo: Remove since Site Instances are doc entities?
                             super_link("site_id", "org_site"),
                             Field("file", "upload",
                                   # upload folder needs to be visible to the download() function as well as the upload
                                   uploadfolder = os.path.join(folder,
                                                               "uploads"),
                                   autodelete = True
                                   ),
                             Field("name", length=128,
                                   # Allow Name to be added onvalidation
                                   requires = IS_NULL_OR(IS_LENGTH(128)),
                                   label = T("Name")
                                   ),
                             Field("url",
                                   label = T("URL"),
                                   requires = IS_NULL_OR(IS_URL()),
                                   represent = lambda url: \
                                    url and A(url, _href=url) or NONE
                                   ),
                             Field("has_been_indexed", "boolean", 
                                   default = False,
                                   readable = False,
                                   writable = False,
                                   ),
                             person_id(
                                # Enable when-required
                                readable = False,
                                writable = False,
                                label=T("Author"),
                                comment=person_comment(T("Author"),
                                                       T("The Author of this Document (optional)"))
                                ),
                             organisation_id(
                                # Enable when-required
                                readable = False,
                                writable = False,
                                widget = org_widget,
                                ),
                             s3_date(label = T("Date Published")),
                             # @ToDo: Move location to link table
                             location_id(
                                # Enable when-required
                                readable = False,
                                writable = False,
                                ),
                             s3_comments(),
                             Field("checksum",
                                   readable = False,
                                   writable = False,
                                   ),
                             *s3_meta_fields())

        # Field configuration
        table.file.represent = lambda file, table=table: \
                               self.doc_file_represent(file, table)

        # CRUD Strings
        ADD_DOCUMENT = T("Add Reference Document")
        crud_strings[tablename] = Storage(
            title_create = ADD_DOCUMENT,
            title_display = T("Document Details"),
            title_list = T("Documents"),
            title_update = T("Edit Document"),
            title_search = T("Search Documents"),
            subtitle_create = T("Add New Document"),
            label_list_button = T("List Documents"),
            label_create_button = ADD_DOCUMENT,
            label_delete_button = T("Delete Document"),
            msg_record_created = T("Document added"),
            msg_record_modified = T("Document updated"),
            msg_record_deleted = T("Document deleted"),
            msg_list_empty = T("No Documents found")
        )

        # Search Method

        # Resource Configuration
        if settings.get_base_solr_url():
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
                  list_layout = doc_render_documents,
                  onaccept = onaccept,
                  ondelete = ondelete,
                  onvalidation = self.document_onvalidation,
                  super_entity = "stats_source",
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        document_id = S3ReusableField("document_id", table,
                                      requires = IS_ONE_OF(db,
                                                           "doc_document.id",
                                                           represent),
                                      represent = represent,
                                      label = T("Document"),
                                      ondelete = "CASCADE",
                                     )

        # ---------------------------------------------------------------------
        # Images
        #
        # @ToDo: Field to determine which is the default image to use for
        #        e.g. a Map popup (like the profile picture)
        #        readable/writable=False except in the cases where-needed
        #
        doc_image_type_opts = {
            1:T("Photograph"),
            2:T("Map"),
            3:T("Document Scan"),
            99:T("other")
        }

        tablename = "doc_image"
        table = define_table(tablename,
                             # Component not instance
                             super_link("doc_id", doc_entity),
                             super_link("pe_id", "pr_pentity"), # @ToDo: Remove & make Persons doc entities instead?
                             super_link("site_id", "org_site"), # @ToDo: Remove since Site Instances are doc entities?
                             Field("file", "upload", autodelete=True,
                                   requires = IS_NULL_OR(
                                    IS_IMAGE(extensions=(s3.IMAGE_EXTENSIONS))
                                    ),
                                   represent = doc_image_represent,
                                   # upload folder needs to be visible to the download() function as well as the upload
                                   uploadfolder = os.path.join(folder,
                                                               "uploads",
                                                               "images"),
                                   widget=S3ImageCropWidget((300, 300))),
                             Field("name", length=128,
                                   # Allow Name to be added onvalidation
                                   requires = IS_NULL_OR(IS_LENGTH(128)),
                                   label=T("Name")),
                             Field("url", label=T("URL"),
                                   requires = IS_NULL_OR(IS_URL())),
                             Field("type", "integer",
                                   requires = IS_IN_SET(doc_image_type_opts,
                                                        zero=None),
                                   default = 1,
                                   label = T("Image Type"),
                                   represent = lambda opt: \
                                    doc_image_type_opts.get(opt, UNKNOWN_OPT)),
                             person_id(label=T("Author")),
                             organisation_id(widget = org_widget),
                             s3_date(label = T("Date Taken")),
                             # @ToDo: Move location to link table
                             location_id(),
                             s3_comments(),
                             Field("checksum",
                                   readable = False,
                                   writable = False,
                                   ),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_IMAGE = T("Add Photo")
        crud_strings[tablename] = Storage(
            title_create = ADD_IMAGE,
            title_display = T("Photo Details"),
            title_list = T("Photos"),
            title_update = T("Edit Photo"),
            title_search = T("Search Photos"),
            subtitle_create = T("Add New Photo"),
            label_list_button = T("List Photos"),
            label_create_button = ADD_IMAGE,
            label_delete_button = T("Delete Photo"),
            msg_record_created = T("Photo added"),
            msg_record_modified = T("Photo updated"),
            msg_record_deleted = T("Photo deleted"),
            msg_list_empty = T("No Photos found"))

        # Search Method

        # Resource Configuration
        configure(tablename,
                  deduplicate = self.document_duplicate,
                  onvalidation = lambda form: \
                            self.document_onvalidation(form, document=False)
                  )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(doc_document_id=document_id)

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """
        
        document_id = S3ReusableField("document_id", "integer",
                                      readable=False, writable=False)
        return Storage(doc_document_id=document_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def doc_file_represent(file, table):
        """ File representation """

        if file:
            try:
                # Read the filename from the file
                filename = table.file.retrieve(file)[0]
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

        if item.tablename not in ("doc_document", "doc_image"):
            return

        data = item.data
        query = None
        file = data.get("file", None)
        if file:
            table = item.table
            query = (table.file == file)
        else:
            url = data.get("url", None)
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

        vars = form.vars
        doc = vars.file
        if (not document) and (not doc):
            encoded_file = vars.get("imagecrop-data", None)
            if encoded_file:
                import base64
                import uuid
                metadata, encoded_file = encoded_file.split(",")
                filename, datatype, enctype = metadata.split(";")
                f = Storage()
                f.filename = uuid.uuid4().hex + filename
                import cStringIO
                f.file = cStringIO.StringIO(base64.decodestring(encoded_file))
                form.vars.file = f
        
        if doc is None:
            # This is a prepop, so file not in form
            return

        if document:
            tablename = "doc_document"
        else:
            tablename = "doc_image"

        db = current.db
        table = db[tablename]

        url = vars.url
        if hasattr(doc, "file"):
            name = vars.name
            if not name:
                # Use the filename
                vars.name = doc.filename
        else:
            id = current.request.post_vars.id
            if id:
                record = db(table.id == id).select(table.file,
                                                   limitby=(0, 1)).first()
                if record:
                    doc = record.file
                    name = vars.name
                    if not name:
                        # Use the filename
                        vars.name = table.file.retrieve(doc)[0]

        if not hasattr(doc, "file") and not doc and not url:
            if document:
                msg = current.T("Either file upload or document URL required.")
            else:
                msg = current.T("Either file upload or image URL required.")
            form.errors.file = msg
            form.errors.url = msg

        # Do a checksum on the file to see if it's a duplicate
        #import cgi
        #if isinstance(doc, cgi.FieldStorage) and doc.filename:
        #    f = doc.file
        #    vars.checksum = doc_checksum(f.read())
        #    f.seek(0)
        #    if not vars.name:
        #        vars.name = doc.filename

        #if vars.checksum is not None:
        #    # Duplicate allowed if original version is deleted
        #    query = ((table.checksum == vars.checksum) & \
        #             (table.deleted == False))
        #    result = db(query).select(table.name,
        #                              limitby=(0, 1)).first()
        #    if result:
        #        doc_name = result.name
        #        form.errors["file"] = "%s %s" % \
        #                              (T("This file already exists on the server as"), doc_name)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def document_onaccept(form):        
        
        vars = form.vars
        doc = vars.file
       
        table = current.db.doc_document

        document = json.dumps(dict(filename=doc,
                                  name=table.file.retrieve(doc)[0],
                                  id=vars.id,
                                  ))

        current.s3task.async("document_create_index",
                             args = [document])

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def document_ondelete(row):        
        
        db = current.db
        table = db.doc_document

        record = db(table.id == row.id).select(table.file,
                                               limitby=(0, 1)).first()

        document = json.dumps(dict(filename=record.file,
                                  id=row.id,
                                 ))
        
        current.s3task.async("document_delete_index",
                             args = [document])   

        return

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
def doc_render_documents(listid, resource, rfields, record, 
                         type = None,
                         **attr):
    """
        Custom dataList item renderer for Documents, e.g. on the HRM Profile

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "doc_document.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

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
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Document"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
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

# END =========================================================================
