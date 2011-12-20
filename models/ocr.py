# -*- coding: utf-8 -*-

"""
    OCR Utility Functions

    @author: Shiv Deepak <idlecool@gmail.com>
"""


session.s3.ocr_enabled = deployment_settings.has_module("ocr")
if auth.user:
    session.s3.ocr_user_utc_offset = auth.user.utc_offset
else:
    session.s3.ocr_user_utc_offset = None

def s3_ocr_buttons(r):
    """ Generate 'Print PDF' button in the view """

    if not session.s3.ocr_enabled:
        return ""

    if r.component:
        # if component
        request_args = r.request.get("args",["",""])
        record_id = request_args[0]
        component_name = request_args[1]
        urlprefix = "%s/%s/%s" % (request.function,
                                  record_id,
                                  component_name)

    else:
        # if not a component
        urlprefix = request.function

    output = DIV(\
        A(IMG(_src="/%s/static/img/upload-ocr.png" % \
                  request.application,
              _alt=T("Upload Scanned OCR Form")),
          _id="download-pdf-btn",
          _title=T("Upload Scanned OCR Form"),
          _href=URL(request.controller,
                    "%s/import.pdf" % urlprefix),
          _style="height: 10px; float: right; padding: 3px;"),
        A(IMG(_src="/%s/static/img/download-ocr.png" % \
                  request.application,
              _alt=T("Download OCR-able PDF Form")),
          _id="download-pdf-btn",
          _title=T("Download OCR-able PDF Form"),
          _href=URL(request.controller,
                    "%s/create.pdf" % urlprefix),
          _style="height: 10px; float: right; padding: 3px;"),
        )
    return output


# =============================================================================
if session.s3.ocr_enabled:

    # =========================================================================
    # OCR tables
    #
    def ocr_tables():
        """ Load the OCR Tables when needed """

        # =====================================================================
        # ocr_meta
        #
        tablename = "ocr_meta"
        table = db.define_table(tablename,
                                Field("form_uuid", notnull=True, unique=True),
                                Field("resource_name", notnull=True),
                                Field("s3ocrxml_file",
                                      "upload",
                                      uploadfolder=os.path.join(request.folder,
                                                                "uploads",
                                                                "ocr_meta")),
                                Field("layout_file",
                                      "upload",
                                      uploadfolder=os.path.join(request.folder,
                                                                "uploads",
                                                                "ocr_meta")),
                                Field("revision", unique=True, notnull=True),
                                Field("pages", "integer"),
                                *s3_meta_fields())

        #======================================================================
        # ocr_payload
        #
        tablename = "ocr_payload"
        table = db.define_table(tablename,
                                # a set of images = one complete form
                                Field("image_set_uuid", notnull=True),
                                Field("image_file",
                                      "upload",
                                      uploadfolder=\
                                          os.path.join(request.folder,
                                                       "uploads",
                                                       "ocr_payload"),
                                      notnull=True),
                                Field("page_number", "integer", notnull=True),
                                *s3_meta_fields())

        #======================================================================
        # ocr_form_status
        #
        tablename = "ocr_form_status"
        table = db.define_table(tablename,
                                Field("image_set_uuid",
                                      notnull=True,
                                      unique=True),
                                Field("form_uuid", notnull=True),
                                Field("review_status", "integer",
                                      notnull=True, default=0),
                                Field("job_uuid",
                                      unique=True),
                                Field("job_has_errors", "integer"),
                                *s3_meta_fields())

        #======================================================================
        # ocr_field_crops
        #
        tablename = "ocr_field_crops"
        table = db.define_table(tablename,
                                Field("image_set_uuid",
                                      notnull=True),
                                Field("resource_table", notnull=True),
                                Field("field_name", notnull=True),
                                Field("image_file",
                                      "upload",
                                      uploadfolder=\
                                          os.path.join(request.folder,
                                                       "uploads",
                                                       "ocr_payload"),
                                      notnull=True),
                                Field("value"),
                                Field("sequence", "integer"),
                                *s3_meta_fields())

        #======================================================================
        # ocr_data_xml
        #
        tablename = "ocr_data_xml"
        table = db.define_table(tablename,
                                Field("image_set_uuid",
                                      unique=True,
                                      notnull=True),
                                Field("data_file",
                                      "upload",
                                      uploadfolder=\
                                          os.path.join(request.folder,
                                                       "uploads",
                                                       "ocr_payload"),
                                      notnull=True),
                                Field("form_uuid",
                                      notnull=True,
                                      default=""),
                                *s3_meta_fields())


    # Provide a handle to this load function
    s3mgr.model.loader(ocr_tables,
                       "ocr_meta",
                       "ocr_payload",
                       "ocr_form_status",
                       "ocr_field_crops",
                       "ocr_data_xml")

# END =========================================================================
