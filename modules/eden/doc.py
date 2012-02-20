# -*- coding: utf-8 -*-

""" Sahana Eden Document Library

    @copyright: 2011-2012 (c) Sahana Software Foundation
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
           "doc_image_represent"]

import os

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3DocumentLibrary(S3Model):

    names = ["doc_entity",
             "doc_document",
             "doc_image"]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        person_comment = self.pr_person_comment
        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3_date_format = current.deployment_settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        # Shortcuts
        add_component = self.add_component
        comments = s3.comments
        configure = self.configure
        define_table = self.define_table
        meta_fields = s3.meta_fields
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Document-referencing entities
        #
        entity_types = Storage(asset_asset=T("Asset"),
                               irs_ireport=T("Incident Report"),
                               project_project=T("Project"),
                               project_activity=T("Project Activity"),
                               project_task=T("Task"),
                               hms_hospital=T("Hospital"))

        tablename = "doc_entity"
        doc_entity = self.super_entity(tablename, "doc_id", entity_types)

        # Components
        add_component("doc_document", doc_entity=self.super_key(doc_entity))
        add_component("doc_image", doc_entity=self.super_key(doc_entity))

        # ---------------------------------------------------------------------
        # Documents
        #
        tablename = "doc_document"
        table = define_table(tablename,
                             super_link("site_id", "org_site"),
                             super_link("doc_id", doc_entity),
                             Field("name", length=128,
                                   notnull=True,
                                   label=T("Name")),
                             Field("file", "upload", autodelete=True),
                             Field("url", label=T("URL"),
                                   requires = [IS_NULL_OR(IS_URL()),
                                               IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                                        "%s.url" % tablename))],
                                   represent = lambda url: \
                                               url and A(url,_href=url) or NONE),
                             person_id(label=T("Author"),
                                       comment=person_comment(T("Author"),
                                                              T("The Author of this Document (optional)"))),
                             organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                             Field("date", "date",
                                   label = T("Date Published"),
                                   represent = s3_date_represent,
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                   widget = S3DateWidget()
                                   ),
                             location_id(),
                             comments(),
                             #Field("entered", "boolean", label=T("Entered")),
                             Field("checksum", readable=False, writable=False),
                             *meta_fields())

        # Field configuration
        table.file.represent = lambda file, table=table: \
                               self.doc_file_represent(file, table)
        #table.location_id.readable = False
        #table.location_id.writable = False
        #table.entered.comment = DIV(_class="tooltip",
        #                            _title="%s|%s" % (T("Entered"),
        #                                              T("Has data from this Reference Document been entered into Sahana?")))

        # CRUD Strings
        DOCUMENT = T("Reference Document")
        ADD_DOCUMENT = T("Add Reference Document")
        LIST_DOCUMENTS = T("List Documents")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_DOCUMENT,
            title_display = T("Document Details"),
            title_list = LIST_DOCUMENTS,
            title_update = T("Edit Document"),
            title_search = T("Search Documents"),
            subtitle_create = T("Add New Document"),
            subtitle_list = DOCUMENT,
            label_list_button = LIST_DOCUMENTS,
            label_create_button = ADD_DOCUMENT,
            label_delete_button = T("Delete Document"),
            msg_record_created = T("Document added"),
            msg_record_modified = T("Document updated"),
            msg_record_deleted = T("Document deleted"),
            msg_list_empty = T("No Documents found")
        )

        # Search Method?

        # Resource Configuration
        configure(tablename,
                  #mark_required=["file"],
                  onvalidation=self.document_onvalidation)

        # Reusable Field
        document_comment = DIV(A(ADD_DOCUMENT,
                                 _class="colorbox",
                                 _href=URL(c="doc", f="document",
                                           args="create",
                                           vars=dict(format="popup")),
                                 _target="top",
                                 _title=T("If you need to add a new document then you can click here to attach one.")),
                               DIV(_class="tooltip",
                                   _title="%s|%s" % (DOCUMENT,
                                                     T("A Reference Document such as a file, URL or contact person to verify this data."))))

        document_id = S3ReusableField("document_id", table,
                                      requires = IS_NULL_OR(IS_ONE_OF(db, "doc_document.id",
                                                                      self.document_represent,
                                                                      orderby="doc_document.name")),
                                      represent = self.document_represent,
                                      label = DOCUMENT,
                                      comment = document_comment,
                                      ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Images
        #
        doc_image_type_opts = {
            1:T("Photograph"),
            2:T("Map"),
            3:T("Document Scan"),
            99:T("other")
        }

        tablename = "doc_image"
        table = define_table(tablename,
                             super_link("site_id", "org_site"),
                             super_link("pe_id", "pr_pentity"),
                             super_link("doc_id", doc_entity),
                             Field("name", length=128,
                                   notnull=True,
                                   label=T("Name")),
                             Field("file", "upload", autodelete=True,
                                   requires = IS_NULL_OR(IS_IMAGE(extensions=(s3.IMAGE_EXTENSIONS))),
                                   # upload folder needs to be visible to the download() function as well as the upload
                                   uploadfolder = os.path.join(request.folder,
                                                               "uploads",
                                                               "images")),
                             Field("url", label=T("URL"),
                                   requires = IS_NULL_OR(IS_URL())),
                             Field("type", "integer",
                                   requires = IS_IN_SET(doc_image_type_opts, zero=None),
                                   default = 1,
                                   label = T("Image Type"),
                                   represent = lambda opt: doc_image_type_opts.get(opt, UNKNOWN_OPT)),
                             person_id(label=T("Author")),
                             organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                             location_id(),
                             Field("date", "date",
                                   label = T("Date Taken"),
                                   represent = s3_date_represent,
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                   widget = S3DateWidget()
                                   ),
                             comments(),
                             Field("checksum", readable=False, writable=False),
                             *meta_fields())

        # Field configuration
        table.file.represent = doc_image_represent

       # CRUD Strings
        ADD_IMAGE = T("Add Photo")
        LIST_IMAGES = T("List Photos")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_IMAGE,
            title_display = T("Photo Details"),
            title_list = LIST_IMAGES,
            title_update = T("Edit Photo"),
            title_search = T("Search Photos"),
            subtitle_create = T("Add New Photo"),
            subtitle_list = T("Photo"),
            label_list_button = LIST_IMAGES,
            label_create_button = ADD_IMAGE,
            label_delete_button = T("Delete Photo"),
            msg_record_created = T("Photo added"),
            msg_record_modified = T("Photo updated"),
            msg_record_deleted = T("Photo deleted"),
            msg_list_empty = T("No Photos found"))

        # Search Method

        # Resource Configuration
        configure(tablename,
                  onvalidation=lambda form: \
                                self.document_onvalidation(form, document=False))

        # Reusable field
        #image_id = S3ReusableField("image_id", db.doc_image,
        #                requires = IS_NULL_OR(IS_ONE_OF(db, "doc_image.id", "%(name)s")),
        #                represent = doc_image_represent,
        #                label = T("Image"),
        #                comment = DIV(A(ADD_IMAGE,
        #                                _class="colorbox",
        #                                _href=URL(c="doc", f="image", args="create",
        #                                          vars=dict(format="popup")),
        #                                _target="top",
        #                                _title=ADD_IMAGE),
        #                          DIV( _class="tooltip",
        #                               _title="%s|%s" % (ADD_IMAGE,
        #                                                 T("Upload an image, such as a photo")))),
        #                ondelete = "RESTRICT"
        #                )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                    document_id = document_id
                )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """

        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def doc_file_represent(file, table):
        """ File representation """

        if file:
            return A(table.file.retrieve(file)[0],
                     _href=URL(c="default", f="download", args=[file]))
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def document_represent(id):
        """ Foreign key representation """

        if not id:
            return current.messages.NONE

        represent = s3_get_db_field_value(tablename = "doc_document",
                                          fieldname = "name",
                                          look_up_value = id)
        return A(represent,
                 _href = URL(c="doc", f="document", args=[id], extension=""),
                 _target = "blank")

    # -------------------------------------------------------------------------
    @staticmethod
    def document_onvalidation(form, document=True):
        """ Form validation for both, documents and images """

        import cgi

        T = current.T
        db = current.db
        s3db = current.s3db
        request = current.request

        if document:
            tablename = "doc_document"
            msg = T("Either file upload or document URL required.")
        else:
            tablename = "doc_image"
            msg = T("Either file upload or image URL required.")

        table = s3db[tablename]

        doc = form.vars.file
        url = form.vars.url
        if not hasattr(doc, "file"):
            id = request.post_vars.id
            if id:
                record = db(table.id == id).select(table.file,
                                                   limitby=(0, 1)).first()
                if record:
                    doc = record.file

        if not hasattr(doc, "file") and not doc and not url:
            form.errors.file = msg
            form.errors.url = msg

        # Do a checksum on the file to see if it's a duplicate
        if isinstance(doc, cgi.FieldStorage) and doc.filename:
            f = doc.file
            form.vars.checksum = doc_checksum(f.read())
            f.seek(0)

        if form.vars.checksum is not None:
            # Duplicate allowed if original version is deleted
            query = ((table.checksum == form.vars.checksum) & \
                     (table.deleted == False))
            result = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if result:
                doc_name = result.name
                form.errors["file"] = "%s %s" % \
                                      (T("This file already exists on the server as"), doc_name)
        return

# =============================================================================
def doc_image_represent(filename):
    """
        Represent an image as a clickable thumbnail

        @param filename: name of the image file
    """

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

# END =========================================================================
