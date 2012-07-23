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
           "doc_image_represent",
           "S3DocumentSourceModel",
          ]

import os

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3DocumentLibrary(S3Model):

    names = ["doc_entity",
             "doc_document",
             "doc_image",
             ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        person_comment = self.pr_person_comment
        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_key = self.super_key
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Document-referencing entities
        #
        entity_types = Storage(
                               asset_asset=T("Asset"),
                               irs_ireport=T("Incident Report"),
                               project_project=T("Project"),
                               project_activity=T("Project Activity"),
                               project_task=T("Task"),
                               hms_hospital=T("Hospital"),
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
                             # Component not instance
                             super_link("site_id", "org_site"),
                             # Component not instance
                             super_link("doc_id", doc_entity),
                             # Instance
                             super_link("source_id", "doc_source_entity"),
                             Field("file", "upload", autodelete=True),
                             Field("name", length=128,
                                   notnull=True,
                                   # Allow Name to be added onvalidation
                                   requires = IS_NULL_OR(IS_LENGTH(128)),
                                   label=T("Name")),
                             Field("url", label=T("URL"),
                                   requires = IS_NULL_OR(IS_URL()),
                                   represent = lambda url: \
                                               url and A(url,_href=url) or NONE),
                             person_id(label=T("Author"),
                                       comment=person_comment(T("Author"),
                                                              T("The Author of this Document (optional)"))),
                             organisation_id(
                                widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
                                ),
                             s3_date(label = T("Date Published")),
                             location_id(),
                             s3_comments(),
                             #Field("entered", "boolean", label=T("Entered")),
                             Field("checksum", readable=False, writable=False),
                             *s3_meta_fields())

        # Field configuration
        table.file.represent = lambda file, table=table: \
                               self.doc_file_represent(file, table)
        #table.location_id.readable = False
        #table.location_id.writable = False
        #table.entered.comment = DIV(_class="tooltip",
        #                            _title="%s|%s" % (T("Entered"),
        #                                              T("Has data from this Reference Document been entered into Sahana?")))

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

        # Search Method?

        # Resource Configuration
        configure(tablename,
                  super_entity = "doc_source_entity",
                  onvalidation=self.document_onvalidation)

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
                             super_link("site_id", "org_site"),
                             super_link("pe_id", "pr_pentity"),
                             # Component not instance
                             super_link("doc_id", doc_entity),
                             Field("file", "upload", autodelete=True,
                                   requires = IS_NULL_OR(
                                                IS_IMAGE(extensions=(s3.IMAGE_EXTENSIONS)
                                                         )),
                                   # upload folder needs to be visible to the download() function as well as the upload
                                   uploadfolder = os.path.join(current.request.folder,
                                                               "uploads",
                                                               "images")),
                             Field("name", length=128,
                                   notnull=True,
                                   # Allow Name to be added onvalidation
                                   requires = IS_NULL_OR(IS_LENGTH(128)),
                                   label=T("Name")),
                             Field("url", label=T("URL"),
                                   requires = IS_NULL_OR(IS_URL())),
                             Field("type", "integer",
                                   requires = IS_IN_SET(doc_image_type_opts, zero=None),
                                   default = 1,
                                   label = T("Image Type"),
                                   represent = lambda opt: doc_image_type_opts.get(opt, UNKNOWN_OPT)),
                             person_id(label=T("Author")),
                             organisation_id(
                                widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
                                ),
                             location_id(),
                             s3_date(label = T("Date Taken")),
                             s3_comments(),
                             Field("checksum", readable=False, writable=False),
                             *s3_meta_fields())

        # Field configuration
        table.file.represent = doc_image_represent

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
                  onvalidation=lambda form: \
                                self.document_onvalidation(form, document=False))
        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage()

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

        db = current.db
        table = db.doc_document
        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        try:
            return A(record.name,
                     _href = URL(c="doc", f="document", args=[id], extension=""),
                     _target = "blank")
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def document_onvalidation(form, document=True):
        """ Form validation for both, documents and images """

        import cgi

        T = current.T
        db = current.db
        vars = form.vars

        if document:
            tablename = "doc_document"
            msg = T("Either file upload or document URL required.")
        else:
            tablename = "doc_image"
            msg = T("Either file upload or image URL required.")

        table = db[tablename]

        doc = vars.file
        url = vars.url
        if not hasattr(doc, "file"):
            id = current.request.post_vars.id
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
            vars.checksum = doc_checksum(f.read())
            f.seek(0)
            if not vars.name:
                vars.name = doc.filename

        if vars.checksum is not None:
            # Duplicate allowed if original version is deleted
            query = ((table.checksum == vars.checksum) & \
                     (table.deleted == False))
            result = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if result:
                doc_name = result.name
                form.errors["file"] = "%s %s" % \
                                      (T("This file already exists on the server as"), doc_name)
        return

# =============================================================================

class S3DocumentSourceModel(S3Model):

    names = ["doc_source_entity",
             "doc_source_id",
             "doc_source"
             ]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Document-source entities
        #
        source_types = Storage(
                               #pr_pentity = T("Person"),
                               doc_document = T("Document"),
                               #flood_gauge = T("Flood Gauge"),
                               #survey_series = T("Survey")
                               )

        tablename = "doc_source_entity"

        table = self.super_entity(tablename,
                                  "source_id",
                                  source_types
                                  )
        # Reusable Field
        source_id = S3ReusableField("source_id", table,
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(current.db,
                                                          "doc_source_entity.source_id")),
                                    label = T("Source"),
                                    ondelete = "CASCADE")
        # Components
        self.add_component("doc_source", doc_source_entity=self.super_key(table))

        # ---------------------------------------------------------------------
        # Document-source details
        #
        tablename = "doc_source"
        table = self.define_table(tablename,
                                  # This is a component, so needs to be a super_link
                                  # - can't override field name, ondelete or requires
                                  self.super_link("source_id", "doc_source_entity"),
                                  Field("name",
                                        label=T("Name")),
                                  Field("reliability",
                                        label=T("Reliability")),
                                  Field("review",
                                        label=T("Review")),
                                  *s3_meta_fields()
                                  )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                doc_source_id = source_id
            )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """
        source_id = S3ReusableField("source_id", "integer",
                                    readable=False,
                                    writable=False)

        return Storage(
                doc_source_id = source_id
            )

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
