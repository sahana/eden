# -*- coding: utf-8 -*-

"""
    Document Library
"""

if deployment_settings.has_module("doc"):

    # Documents as Components of Organizations & Incidents
    # @ToDo: Use link tables instead
    joinby = dict(org_organisation="organisation_id")
    if deployment_settings.has_module("asset"):
        joinby["asset_asset"] = "asset_id"
    if deployment_settings.has_module("irs"):
        joinby["irs_ireport"] = "ireport_id"
    if deployment_settings.has_module("project"):
        joinby["project_project"] = "project_id"
        joinby["project_activity"] = "activity_id"
    s3mgr.model.add_component("doc_document", **joinby)

    # Documents as Component of Sites
    s3mgr.model.add_component("doc_document", org_site=super_key(db.org_site))

    # Images as Components of Organizations & Incidents
    # @ToDo: Use link tables instead
    joinby = dict(org_organisation="organisation_id")
    if deployment_settings.has_module("irs"):
        joinby["irs_ireport"] = "ireport_id"
    if deployment_settings.has_module("project"):
       joinby["project_project"] = "project_id"
       joinby["project_activity"] = "activity_id"
    s3mgr.model.add_component("doc_image", **joinby)

    # Images as Component of Sites
    s3mgr.model.add_component("doc_image", org_site=super_key(db.org_site))

    def doc_tables():
        """ Load the Document tables as-needed """

        module = "doc"

        # Load the models we depend on
        if deployment_settings.has_module("asset"):
            s3mgr.load("asset_asset")
        asset_id = response.s3.asset_id
        if deployment_settings.has_module("irs"):
            s3mgr.load("irs_ireport")
        ireport_id = response.s3.ireport_id
        if deployment_settings.has_module("project"):
            s3mgr.load("project_project")
        project_id = response.s3.project_id
        activity_id = response.s3.activity_id

        if "doc_document" in db:
            return

        # =========================================================================
        # Documents
        # =========================================================================
        resourcename = "document"
        tablename = "doc_document"
        table = db.define_table(tablename,
                                super_link(db.org_site),    # site_id
                                Field("name", length=128,
                                      notnull=True, unique=True,
                                      label=T("Name")),
                                Field("file", "upload", autodelete=True),
                                Field("url", label=T("URL"),
                                      requires = [IS_NULL_OR(IS_URL()),
                                                  IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                                           "%s.url" % tablename))],
                                      represent = lambda url: \
                                        url and A(url,_href=url) or NONE),
                                person_id(label=T("Author"),
                                          comment = pr_person_comment(T("Author"), T("The Author of this Document (optional)"))),
                                organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                Field("date", "date"),
                                location_id(),
                                s3_comments(),
                                #Field("entered", "boolean", label=T("Entered")),
                                Field("checksum", readable=False, writable=False),
                                # @ToDo: Use link tables instead
                                asset_id(readable=False, writable=False),      # So that we can add Documents as Components of Assets
                                ireport_id(readable=False, writable=False),    # So that we can add Documents as Components of Incidents
                                project_id(readable=False, writable=False),    # So that we can add Documents as Components of Projects
                                activity_id(readable=False, writable=False),   # So that we can add Documents as Components of Activities
                                *s3_meta_fields())

        def doc_file_represent( file, table):
            if file:
                return A(table.file.retrieve(file)[0],
                         _href=URL(c="default", f="download",
                                   args=[file]))
            else:
                return NONE

        table.file.represent = lambda file, table=table: \
                                        doc_file_represent(file, table)
        #table.location_id.readable = table.location_id.writable = False

        #table.entered.comment = DIV( _class="tooltip",
        #                             _title="%s|%s" % (T("Entered"),
        #                                               T("Has data from this Reference Document been entered into Sahana?")))

        # -------------------------------------------------------------------------
        def document_represent(id):
            if not id:
                return NONE
            represent = s3_get_db_field_value(tablename = "doc_document",
                                              fieldname = "name",
                                              look_up_value = id)
            #File
            #Website
            #Person
            return A ( represent,
                       _href = URL(c="doc", f="document",
                                   args = [id], extension = ""),
                       _target = "blank"
                       )

        DOCUMENT = T("Reference Document")
        ADD_DOCUMENT = T("Add Reference Document")

        document_comment = DIV( A( ADD_DOCUMENT,
                                   _class="colorbox",
                                   _href=URL(c="doc", f="document",
                                             args="create",
                                             vars=dict(format="popup")),
                                   _target="top",
                                   _title=T("If you need to add a new document then you can click here to attach one."),
                                   ),
                                DIV( _class="tooltip",
                                     _title="%s|%s" % (DOCUMENT,
                                        T("A Reference Document such as a file, URL or contact person to verify this data.")),
                                        #T("Add a Reference Document such as a file, URL or contact person to verify this data. If you do not enter a Reference Document, your email will be displayed instead."),
                                     ),
                                #SPAN( I( T("If you do not enter a Reference Document, your email will be displayed to allow this data to be verified.") ),
                                #     _style = "color:red"
                                #     )
                                )

        # CRUD Strings
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
            msg_list_empty = T("No Documents found"))

        # For use in Link Tables
        # - currently used by Requests
        document_id = S3ReusableField("document_id", table,
                                      requires = IS_NULL_OR(IS_ONE_OF(db, "doc_document.id",
                                                                      document_represent,
                                                                      orderby="doc_document.name")),
                                      represent = document_represent,
                                      label = DOCUMENT,
                                      comment = document_comment,
                                      ondelete = "RESTRICT",
                                      # @ToDo
                                      #widget = UploadWidget
                                     )

        # -------------------------------------------------------------------------
        def document_onvalidation(form):

            import cgi

            table = db.doc_document

            doc = form.vars.file
            url = form.vars.url

            if not hasattr(doc, "file"):
                id = request.post_vars.id
                if id:
                    record = db(table.id == id).select(table.file, limitby=(0, 1)).first()
                    if record:
                        doc = record.file

            if not hasattr(doc, "file") and not doc and not url:
                form.errors.file = \
                form.errors.url = T("Either file upload or document URL required.")

            if isinstance(doc, cgi.FieldStorage) and doc.filename:
                f = doc.file
                form.vars.checksum = docChecksum(f.read())
                f.seek(0)
            if form.vars.checksum is not None:
                result = db(table.checksum == form.vars.checksum).select(table.name,
                                                                         limitby=(0, 1)).first()
                if result:
                    doc_name = result.name
                    form.errors["file"] = "%s %s" % (T("This file already exists on the server as"),
                                                     doc_name)
            return

        s3mgr.configure(tablename,
                        mark_required=["file"],
                        onvalidation=document_onvalidation)

        # =========================================================================
        # Images
        # =========================================================================

        doc_image_type_opts = {
            1:T("Photograph"),
            2:T("Map"),
            3:T("Document Scan"),
            99:T("other")
        }

        resourcename = "image"
        tablename = "doc_image"
        table = db.define_table(tablename,
                                super_link(db.org_site),    # site_id
                                super_link(db.pr_pentity),  # pe_id
                                Field("name", length=128,
                                      notnull=True, unique=True,
                                      label=T("Name")),
                                Field("image", "upload", autodelete=True,
                                      requires = IS_IMAGE(extensions=(IMAGE_EXTENSIONS)),
                                      # upload folder needs to be visible to the download() function as well as the upload
                                      uploadfolder = os.path.join(request.folder,
                                                                  "uploads",
                                                                  "images")),
                                # Web2Py r2867+ includes this functionality by default
                                #Field("image", "upload", autodelete=True, widget=S3UploadWidget.widget),
                                Field("type", "integer",
                                      requires = IS_IN_SET(doc_image_type_opts, zero=None),
                                      default = 1,
                                      label = T("Image Type"),
                                      represent = lambda opt: doc_image_type_opts.get(opt, UNKNOWN_OPT)),
                                Field("url", label=T("URL"),
                                      requires = IS_NULL_OR(IS_URL())),
                                person_id(label=T("Author")),
                                organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                location_id(),
                                Field("date", "date"),
                                s3_comments(),
                                Field("checksum", readable=False, writable=False),
                                ireport_id(readable=False, writable=False),    # So that we can add Iamges as Components of Incidents
                                project_id(readable=False, writable=False),    # So that we can add Documents as Components of Projects
                                #activity_id(readable=False, writable=False),    # So that we can add Documents as Components of Activities
                                *s3_meta_fields())

        def s3_image_represent(filename):
            """ Represent an Image as a clickable thumbnail """

            return DIV(A(IMG(_src=URL(c="default", f="download",
                                      args=filename),
                             _height=40),
                             _class="zoom",
                             _href="#zoom-media_image-%s" % id),
                       DIV(IMG(_src=URL(c="default", f="download",
                                        args=filename),
                               _width=600),
                               _id="zoom-media_image-%s" % id,
                               _class="hidden"))

        table.image.represent = s3_image_represent

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

        # Unused - better to have the documents as a tab on the main resource
        #image_id = S3ReusableField("image_id", db.doc_image,
        #                requires = IS_NULL_OR(IS_ONE_OF(db, "doc_image.id", "%(name)s")),
        #                represent = s3_image_represent,
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

        # -------------------------------------------------------------------------
        def image_onvalidation(form):

            import cgi

            table = db.doc_image

            img = form.vars.image

            if not hasattr(img, "file"):
                id = request.post_vars.id
                if id:
                    record = db(table.id == id).select(table.image,
                                                       limitby=(0, 1)).first()
                    if record:
                        img = record.image

            if isinstance(img, cgi.FieldStorage) and img.filename:
                f = img.file
                form.vars.checksum = docChecksum(f.read())
                f.seek(0)
            if form.vars.checksum is not None:
                query = (table.checksum == form.vars.checksum)
                result = db(query).select(table.name,
                                          limitby=(0, 1)).first()
                if result:
                    image_name = result.name
                    form.errors["image"] = "%s %s" % (T("This file already exists on the server as"),
                                                      image_name)
            return

        s3mgr.configure(tablename,
                        create_onvalidation=image_onvalidation,
                        update_onvalidation=image_onvalidation)

        # Pass variables back to global scope (response.s3.*)
        return dict(
            document_id = document_id
            )

    # Provide a handle to this load function
    s3mgr.loader(doc_tables,
                 "doc_document",
                 "doc_image")

# END =========================================================================

