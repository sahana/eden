# -*- coding: utf-8 -*-

""" OCR Utility Functions

    @copyright: 2009-2016 (c) Sahana Software Foundation
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

__all__ = ("OCRDataModel",
           "ocr_buttons",
           )

import os

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class OCRDataModel(S3Model):
    """
    """

    names = ("ocr_meta",
             "ocr_payload",
             "ocr_form_status",
             "ocr_field_crops",
             "ocr_data_xml",
             )

    def model(self):

        #T = current.T

        #messages = current.messages
        #UNKNOWN_OPT = messages.UNKNOWN_OPT
        #NONE = messages["NONE"]

        define_table = self.define_table

        # Upload folders
        folder = current.request.folder
        metadata_folder = os.path.join(folder, "uploads", "ocr_meta")
        payload_folder = os.path.join(folder, "uploads", "ocr_payload")

        # =====================================================================
        # OCR Meta Data
        #
        tablename = "ocr_meta"
        define_table(tablename,
                     Field("form_uuid",
                           notnull=True,
                           length=128,
                           unique=True),
                     Field("resource_name",
                           notnull=True),
                     Field("s3ocrxml_file", "upload",
                           length = current.MAX_FILENAME_LENGTH,
                           uploadfolder = metadata_folder,
                           ),
                     Field("layout_file", "upload",
                           length = current.MAX_FILENAME_LENGTH,
                           uploadfolder = metadata_folder,
                           ),
                     Field("revision",
                           notnull=True,
                           length=128,
                           unique=True),
                     Field("pages", "integer"),
                     *s3_meta_fields())

        #======================================================================
        # OCR Payload
        #
        tablename = "ocr_payload"
        define_table(tablename,
                     # a set of images = one complete form
                     Field("image_set_uuid",
                           notnull=True),
                     Field("image_file", "upload",
                           length = current.MAX_FILENAME_LENGTH,
                           notnull = True,
                           uploadfolder = payload_folder,
                           ),
                     Field("page_number", "integer",
                           notnull=True),
                     *s3_meta_fields())

        #======================================================================
        # OCR Form Status
        #
        tablename = "ocr_form_status"
        define_table(tablename,
                     Field("image_set_uuid",
                           notnull=True,
                           length=128,
                           unique=True),
                     Field("form_uuid",
                           notnull=True),
                     Field("review_status", "integer",
                           notnull=True,
                           default=0),
                     Field("job_uuid",
                           length=128,
                           unique=True),
                     Field("job_has_errors", "integer"),
                     *s3_meta_fields())

        #======================================================================
        # OCR Field Crops
        #
        tablename = "ocr_field_crops"
        define_table(tablename,
                     Field("image_set_uuid",
                           notnull=True),
                     Field("resource_table",
                           notnull=True),
                     Field("field_name",
                           notnull=True),
                     Field("image_file", "upload",
                           length = current.MAX_FILENAME_LENGTH,
                           notnull = True,
                           uploadfolder = payload_folder,
                           ),
                     Field("value"),
                     Field("sequence", "integer"),
                     *s3_meta_fields())

        #======================================================================
        # OCR XML Data
        #
        tablename = "ocr_data_xml"
        define_table(tablename,
                     Field("image_set_uuid",
                           length=128,
                           unique=True,
                           notnull=True),
                     Field("data_file", "upload",
                           length = current.MAX_FILENAME_LENGTH,
                           notnull = True,
                           uploadfolder = payload_folder,
                           ),
                     Field("form_uuid",
                           notnull=True,
                           default=""),
                     *s3_meta_fields())

# =============================================================================
def ocr_buttons(r):
    """ Generate 'Print PDF' button in the view """

    if not current.deployment_settings.has_module("ocr"):
        return ""

    if r.component:
        urlargs = [r.id, r.component_name]

    else:
        urlargs = []

    f = r.function
    c = r.controller
    a = r.application

    T = current.T
    UPLOAD = T("Upload Scanned OCR Form")
    DOWNLOAD = T("Download OCR-able PDF Form")

    _style = "height:10px;float:right;padding:3px;"

    output = DIV(

        A(IMG(_src="/%s/static/img/upload-ocr.png" % a, _alt=UPLOAD),
          _id="upload-pdf-btn",
          _href=URL(c=c, f=f, args=urlargs + ["import.pdf"]),
          _title=UPLOAD,
          _style=_style),

        A(IMG(_src="/%s/static/img/download-ocr.png" % a, _alt=DOWNLOAD),
          _id="download-pdf-btn",
          _href=URL(c=c, f=f, args=urlargs + ["create.pdf"]),
          _title=DOWNLOAD,
          _style=_style),

        )
    return output

# END =========================================================================
