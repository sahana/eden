# -*- coding: utf-8 -*-

""" Resource PDF Tools

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{ReportLab}} <http://www.reportlab.com>}

    ######################################################################
    DEPRECATION WARNING

    This class is being replaced by the S3RL_PDF codec

    Initially the reporting features will be replaced, with the OCR
    process being removed at a later stage.
    ######################################################################

    @copyright: 2011-2019 (c) Sahana Software Foundation
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

__all__ = ("S3PDF",)

import json
import math
import os
import re
import sys
import subprocess
import unicodedata

from copy import deepcopy
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
from datetime import datetime, timedelta, date
# Not using soupparser's unescape for now as it adds BeautifulSoup module
# to the dependency list for just one utility
#from lxml.html.soupparser import unescape
from htmlentitydefs import name2codepoint

from gluon import *
from gluon.storage import Storage
from gluon.contenttype import contenttype
from gluon.languages import lazyT

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("ERROR: lxml module needed for XML handling\n")
    raise

from s3datetime import S3DateTime
from s3rest import S3Method
from s3utils import s3_represent_value, s3_validate
import s3codec

try:
    from PIL import Image
    from PIL import ImageOps
    from PIL import ImageStat
    PILImported = True
except(ImportError):
    try:
        import Image
        import ImageOps
        import ImageStat
        PILImported = True
    except(ImportError):
        sys.stderr.write("S3 Debug: S3PDF: Python Image Library not installed\n")
        PILImported = False
try:
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics

    from reportlab.pdfgen import canvas
    from reportlab.lib.fonts import tt2ps
    from reportlab.rl_config import canvas_basefontname as _baseFontName
    from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, PageTemplate
    from reportlab.platypus.frames import Frame
    from reportlab.platypus import Spacer, PageBreak, Paragraph
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.colors import Color
    from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
    from reportlab.platypus.flowables import Flowable
    reportLabImported = True
except ImportError:
    sys.stderr.write("S3 Debug: S3PDF: Reportlab not installed\n")
    reportLabImported = False

# Maximum number of options a field can have
MAX_FORM_OPTIONS_LIMIT = 12

# Will be loaded with values during S3PDF apply_method
ERROR = Storage()

# =============================================================================
def checkDependencies(r):
    T = current.T
    ERROR = Storage(
                    PIL_ERROR=T("PIL (Python Image Library) not installed"),
                    REPORTLAB_ERROR=T("ReportLab not installed"),
                   )
    # Check that the necessary reportLab classes were imported
    if not reportLabImported:
        r.error(501, ERROR.REPORTLAB_ERROR)
    if not PILImported:
        r.error(501, ERROR.PIL_ERROR)
        # redirect() is not available in this scope
        #current.session.error = self.ERROR.REPORTLAB_ERROR
        #redirect(URL(extension=""))


# =============================================================================
if reportLabImported:

    # =========================================================================
    class ChangePageTitle(Flowable):
        def __init__(self, doc, newTitle):
            Flowable.__init__(self)
            self.doc = doc
            self.title = newTitle

        def draw(self):
            self.doc.title = self.title

    # =========================================================================
    class Overlay(Flowable):
        def __init__(self, callback, data):
            Flowable.__init__(self)
            self.function = callback
            self.data = data

        def draw(self):
            self.function(self.canv, self.data)

    # =========================================================================
    class EdenDocTemplate(BaseDocTemplate):
        """
            The standard document template for eden reports
            It allows for the following page templates:
            1) First Page
            2) Even Page
            3) Odd Page
            4) Landscape Page
        """

        # ---------------------------------------------------------------------
        def setPageTemplates(self,
                             first,
                             firstEnd,
                             even = None,
                             odd = None,
                             landscape = None,
                             ):
            """
                Determine which page template to use
            """

            self.onfirst = first
            self.onfirstEnd = firstEnd
            if even:
                self.oneven = even
            else:
                self.oneven = first
            if odd:
                self.onodd = odd
            else:
                self.onodd = first
            if landscape:
                self.onlandscape = landscape
            else:
                self.onlandscape = first
            self.needLandscape = False

        # ---------------------------------------------------------------------
        def handle_pageBegin(self):
            """
                Determine which page template to use
            """

            self._handle_pageBegin()
            if self.needLandscape:
                self._handle_nextPageTemplate("landscape")
            elif self.page %2 == 1:
                self._handle_nextPageTemplate("odd")
            else:
                self._handle_nextPageTemplate("even")

        # ---------------------------------------------------------------------
        def build(self, flowables, canvasmaker=canvas.Canvas):
            """
                Build the document using the flowables.

                Set up the page templates that the document can use

            """

            self._calc()    # in case we changed margins sizes etc
            showBoundary = 0 # for debugging set to 1
            frameT = Frame(self.leftMargin,
                           self.bottomMargin,
                           self.width,
                           self.height,
                           id="body",
                           showBoundary = showBoundary)
            self.addPageTemplates([PageTemplate(id="first",
                                                frames=frameT,
                                                onPage=self.onfirst,
                                                onPageEnd=self.onfirstEnd,
                                                pagesize=self.pagesize),
                                   PageTemplate(id="even",
                                                frames=frameT,
                                                onPage=self.oneven,
                                                onPageEnd=self.onfirstEnd,
                                                pagesize=self.pagesize),
                                   PageTemplate(id="odd",
                                                frames=frameT,
                                                onPage=self.onodd,
                                                onPageEnd=self.onfirstEnd,
                                                pagesize=self.pagesize),
                                   PageTemplate(id="landscape",
                                                frames=frameT,
                                                onPage=self.onlandscape,
                                                pagesize=self.pagesize),
                                   ])
            BaseDocTemplate.build(self, flowables, canvasmaker=canvasmaker)

# =============================================================================
class S3PDF(S3Method):
    """
        Class to help generate PDF documents.

        A typical implementation would be as follows:

            exporter = s3base.S3PDF()
            return exporter(xrequest, **attr)

        Currently this class supports two types of reports:
        A List: Typically called from the icon shown in a search
                For example inv/warehouse
        A Header plus List: Typically called from a button on a form
                For example ???

        Add additional generic forms to the apply_method() function
        For specialist forms a S3PDF() object will need to be created.
        See the apply_method() for ideas on how to create a form,
        but as a minimum the following structure is required:

            pdf = S3PDF()
            pdf.newDocument(pdf.defaultTitle(resource))

            # Add specific pages here

            return pdf.buildDoc()
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply CRUD methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
                        The attributes that it knows about are:
                      * componentname
                      * formname
                      * list_fields
                      * report_groupby
                      * report_hide_comments

            @return: output object to send to the view
        """

        # ---------------------------------------------------------------------
        def getParam(key):
            """
                nested function to get the parameters passed into apply_method

                @todo find out if this has been done better elsewhere! :(

                This will first try and get the argument from the attr parameter,
                if it's not here then try self._config()
            """
            value = attr.get(key)
            if value != None:
                return value
            return self._config(key)

        T = current.T
        self.ERROR = ERROR = Storage(
            NO_RECORDS=T("No records in this resource. Add one more records manually and then retry."),
            TESSERACT_ERROR=T("%(app)s not installed. Ask the Server Administrator to install on Server.") % dict(app="Tesseract 3.01"),
            EMPTY_OCR_FORM=T("Selected OCR Form has no pages. Use another revision of create a new revision by downloading a new Form."),
            INVALID_IMAGE_TYPE=T("Uploaded file(s) are not Image(s). Supported image formats are '.png', '.jpg', '.bmp', '.gif'."),
            OCR_DISABLED=T("OCR module is disabled. Ask the Server Administrator to enable it."),
            IMAGE_MAGICK_ERROR=T("%(app)s not installed. Ask the Server Administrator to install on Server.") % dict(app="ImageMagick"),
            NOT_PDF_FILE=T("Uploaded file is not a PDF file. Provide a Form in valid PDF Format."),
            INVALID_PDF=T("Uploaded PDF file has more/less number of page(s) than required. Check if you have provided appropriate revision for your Form as well as check the Form contains appropriate number of pages."),
            NO_UTC_OFFSET=T("No UTC offset found. Please set UTC offset in your 'User Profile' details. Example: UTC+0530"),
            INVALID_JOBID=T("The provided 'jobuuid' is invalid. The session of Form upload is invalid. You should retry uploading."),
            INVALID_FORMID=T("The provided 'formuuid' is invalid. You have selected a Form revision which does not exist on this server."),
            UNRECOVERABLE_ERROR=T("The uploaded Form is unreadable, please do manual data entry."),
            JOB_COMPLETE=T("This job has already been finished successfully."),
            )

        self.r = r
        checkDependencies(r)
        settings = current.deployment_settings
        request = current.request
        response = current.response
        session = current.session
        db = current.db

        if DEBUG:
            content_disposition = "inline"
        else:
            content_disposition = "attachment"

        if settings.get_pdf_size() == "Letter":
            self.paper_size = LETTER
        else:
            self.paper_size = A4

        try:
            self.logo =  os.path.join(request.folder,
                                      settings.get_pdf_logo())
        except:
            self.logo = None
        self.headerBanner = None

        method = self.method

        callback = getParam("callback")
        if callback != None:
            title = getParam("formname")
            if title == None:
                title = self.defaultTitle(self.resource)
            header = getParam("header")
            if header == None:
                header = self.pageHeader
            footer = getParam("footer")
            if footer == None:
                footer = self.pageFooter
            filename = getParam("filename")
            if filename == None:
                filename = title
            self.newDocument(title,
                             header=header,
                             footer=footer,
                             filename = filename)
            try:
                id = r.component_id
                if id == None:
                    id = r.id
            except:
                try:
                    id = r.id
                except:
                    id = None

            callback(self, id=id)
            # Build the document
            doc = self.buildDoc()
            # Set content type and disposition headers
            if response:
                response.headers["Content-Type"] = contenttype(".pdf")
                response.headers["Content-disposition"] = \
                    "%s; filename=\"%s\"" % (content_disposition,
                                             self.filename)

            # Return the stream
            return doc

        elif r.http == "GET":
            if self.method in ("read", "list"):
                # Normal PDF output
                # Get the configuration parameters
                componentname = getParam("componentname")
                title = getParam("formname")
                list_fields = getParam("list_fields")
                report_groupby = getParam("report_groupby")
                report_hide_comments = getParam("report_hide_comments")
                filename = getParam("filename")
                if filename == None:
                    filename = title

                # Create the document shell
                if title == None:
                    title = self.defaultTitle(self.resource)
                self.newDocument(title,
                                 header=self.pageHeader,
                                 footer=self.pageFooter,
                                 filename = filename)

                if "report_landscape" in attr:
                    self.setLandscape()
                # get the header details, if appropriate
                if "rheader" in attr and attr["rheader"]:
                    self.extractrHeader(attr["rheader"])
                    self.addSpacer(3)
                elif componentname:
                    self.addrHeader(self.resource,
                                    list_fields,
                                    report_hide_comments=report_hide_comments)
                    self.addSpacer(3)
                # Add details to the document
                if componentname == None:
                    # Document that only has a resource list
                    self.addTable(self.resource,
                                  list_fields=list_fields,
                                  report_groupby=report_groupby,
                                  report_hide_comments=report_hide_comments)
                else:
                    # Document that has a resource header and component list
                    # Get the raw data for the component
                    ptable = self.resource.table
                    ctable = db[componentname]
                    raw_data = []
                    linkfield = None
                    for link in ptable._referenced_by:
                        if link[0] == componentname:
                            linkfield = link[1]
                            break
                    if linkfield != None:
                        query = ctable[linkfield] == self.record_id
                        records = db(query).select()
                        find_fields = []
                        for component in self.resource.components.values():
                            find_fields += component.readable_fields()
                        fields = []
                        if list_fields:
                            for lf in list_fields:
                                for field in find_fields:
                                    if field.name == lf:
                                        fields.append(field)
                                        break
                        else:
                            for field in find_fields:
                                if field.type == "id":
                                    continue
                                if report_hide_comments and field.name == "comments":
                                    continue
                                fields.append(field)
                        if not fields:
                            fields = [table.id]
                        label_fields = [f.label for f in fields]

                        for record in records:
                            data = []
                            for field in fields:
                                value = record[field.name]
                                text = s3_represent_value(field,
                                                          value=value,
                                                          strip_markup=True,
                                                          non_xml_output=True,
                                                          extended_comments=True
                                                          )
                                data.append(text)
                            raw_data.append(data)
                        self.addTable(raw_data = raw_data,
                                      list_fields=label_fields)

                if "report_footer" in attr:
                    self.addSpacer(3)
                    self.extractrHeader(attr["report_footer"])
                # Build the document
                doc = self.buildDoc()

                # Set content type and disposition headers
                if response:
                    response.headers["Content-Type"] = contenttype(".pdf")
                    response.headers["Content-disposition"] = \
                        "%s; filename=\"%s\"" % (content_disposition,
                                                 self.filename)

                # Return the stream
                return doc

            elif method == "create":
                if current.deployment_settings.has_module("ocr"):
                    # Create an OCR PDF form
                    import uuid
                    formUUID = uuid.uuid1()
                    self.newOCRForm(formUUID)

                    # Put values
                    self.OCRPDFManager()

                    # Build the document
                    doc = self.buildDoc()
                    numPages = self.doc.numPages
                    layoutXML = self.__getOCRLayout()
                    self.__update_dbmeta(formUUID, layoutXML, numPages)

                    # Set content type and disposition headers
                    if response:
                        response.headers["Content-Type"] = contenttype(".pdf")
                        response.headers["Content-disposition"] = \
                            "%s; filename=\"%s\"" % (content_disposition,
                                                     self.filename)

                    # Return the stream
                    return doc

                else:
                    # @ToDo: Produce a simple form
                    r.error(501, self.ERROR.OCR_DISABLED)

            elif method == "import":
                # Render a review UI
                if not current.deployment_settings.has_module("ocr"):
                    r.error(501, self.ERROR.OCR_DISABLED)

                authorised = self._permitted(method="create")
                if not authorised:
                    r.unauthorised()

                try:
                    if r.component:
                        trigger = r.args[3]
                    else:
                        trigger = r.args[1]
                except(IndexError):
                    trigger = None

                if trigger == "review":
                    try:
                        jobuuid = r.vars["jobuuid"]
                    except(KeyError):
                        r.error(501, current.ERROR.BAD_REQUEST)

                    # Check if operation is valid on the given job_uuid
                    current.s3db.table("ocr_meta")
                    statustable = db.ocr_form_status
                    query = (statustable.job_uuid == jobuuid)
                    row = db(query).select(statustable.review_status,
                                           statustable.job_has_errors,
                                           statustable.image_set_uuid,
                                           statustable.form_uuid,
                                           limitby=(0, 1)).first()
                    if not row:
                        # No such job
                        r.error(501, self.ERROR.INVALID_JOBID)

                    if row.review_status == 1:
                        # Job has already been reviewed
                        r.error(501, self.ERROR.JOB_COMPLETE)

                    # Retrieve meta data
                    if row.job_has_errors == 1:
                        job_has_errors = True
                    else:
                        job_has_errors = False

                    self.setuuid = row.image_set_uuid

                    # Retrieve s3ocrxml
                    formuuid = row.form_uuid
                    metatable = db.ocr_meta
                    row = db(metatable.form_uuid == formuuid).select(metatable.s3ocrxml_file,
                                                                     limitby=(0, 1)).first()
                    if not row:
                        r.error(501, self.ERROR.INVALID_FORMID)

                    s3ocrxml_filename = row.s3ocrxml_file
                    f = open(os.path.join(r.folder,
                                          "uploads",
                                          "ocr_meta",
                                          s3ocrxml_filename),
                             "rb")
                    s3ocrxml = f.read()
                    f.close()

                    s3ocrdict = self.__s3ocrxml2dict(s3ocrxml)

                    # Retrieve the job
                    import_job = self.resource.import_tree(None, None,
                                                           job_id=jobuuid,
                                                           commit_job=False,
                                                           ignore_errors=True)

                    s3import_enabled = True
                    if s3import_enabled:
                        s3ocrdata = self.__importjob2data(import_job)

                    else:
                        # Retrive s3ocr data xml
                        table = db.ocr_data_xml
                        query = (table.image_set_uuid == self.setuuid)
                        row = db(query).select(table.data_file,
                                               limitby=(0, 1)).first()

                        if not row:
                            r.error(501, current.ERROR.BAD_RECORD)

                        s3ocrdataxml_filename = row.data_file
                        f = open(os.path.join(r.folder,
                                              "uploads",
                                              "ocr_payload",
                                              s3ocrdataxml_filename),
                                 "rb")
                        s3ocrdataxml = f.read()
                        f.close()

                        s3ocrdata = self.__temp_ocrdataxml_parser(s3ocrdataxml)

                    reviewform = self.__create_review_form(s3ocrdict, s3ocrdata)

                    return response.render("_ocr_review.html",
                                           dict(reviewform=reviewform)
                                          )

                elif trigger == "image":
                    # Do import job
                    try:
                        setuuid = r.vars["setuuid"]
                        resource_table = r.vars["resource_table"]
                        field_name = r.vars["field_name"]
                    except(KeyError):
                        r.error(501, current.ERROR.BAD_REQUEST)

                    try:
                        value = r.vars["value"]
                    except(KeyError):
                        value = None
                        try:
                            sequence = r.vars["sequence"]
                        except(KeyError):
                            r.error(501, current.ERROR.BAD_REQUEST)

                    # Load ocr tables
                    current.s3db.table("ocr_meta")
                    table = db.ocr_field_crops
                    if value:
                        query = (table.image_set_uuid == setuuid) & \
                                (table.resource_table == resource_table) & \
                                (table.field_name == field_name) & \
                                (table.value == value)
                        row = db(query).select(table.image_file,
                                               limitby=(0, 1)).first()
                    else:
                        query = (table.image_set_uuid == setuuid) & \
                                (table.resource_table == resource_table) & \
                                (table.field_name == field_name) & \
                                (table.sequence == sequence)
                        row = db(query).select(table.image_file,
                                               limitby=(0, 1)).first()
                    if not row:
                        r.error(501, current.ERROR.BAD_RECORD)

                    format = row.image_file[-4:]
                    image_file = open(os.path.join(r.folder,
                                                   "uploads",
                                                   "ocr_payload",
                                                   row.image_file))
                    image_file_content = image_file.read()
                    image_file.close()
                    # Set content type and disposition headers
                    if response:
                        response.headers["Content-Type"] = contenttype(format)
                        response.headers["Content-disposition"] = \
                            "%s; filename=\"%s\"" % ("inline",
                                                     "tempimage%s" % format)

                    # Return the stream
                    return image_file_content

                elif trigger == "import":
                    # Do import job
                    try:
                        setuuid = r.vars["setuuid"]
                    except(KeyError):
                        r.error(501, current.ERROR.BAD_REQUEST)

                    # Check if operation is valid on the given set_uuid
                    statustable = s3db.ocr_form_status
                    query = (statustable.image_set_uuid == setuuid)
                    row = db(query).select(statustable.job_uuid,
                                           limitby=(0, 1)).first()
                    if row:
                        # This set of images has already been imported
                        jobuuid = row.job_uuid

                        if r.component:
                            # If component
                            request_args = request.get("args", ["", ""])
                            record_id = request_args[0]
                            component_name = request_args[1]
                            urlprefix = "%s/%s/%s" % (request.function,
                                                      record_id,
                                                      component_name)
                        else:
                            # Not a component
                            urlprefix = request.function

                        redirect(URL(request.controller,
                                     "%s/upload.pdf" % urlprefix,
                                     args="review",
                                     vars={"jobuuid":jobuuid}))

                    table = db.ocr_data_xml
                    row = db(table.image_set_uuid == setuuid).select(table.data_file,
                                                                     table.form_uuid,
                                                                     limitby=(0, 1)
                                                                     ).first()
                    if not row:
                        r.error(501, current.ERROR.BAD_RECORD)

                    data_file = open(os.path.join(r.folder,
                                                  "uploads",
                                                  "ocr_payload",
                                                  row.data_file))
                    formuuid = row.form_uuid

                    datafile_content = data_file.read()
                    data_file.close()

                    metatable = db.ocr_meta
                    row = db(metatable.form_uuid == formuuid).select(metatable.s3ocrxml_file,
                                                                     limitby=(0, 1)
                                                                     ).first()
                    if not row:
                        r.error(501, self.ERROR.INVALID_FORMID)

                    s3ocrxml_filename = row.s3ocrxml_file
                    f = open(os.path.join(r.folder,
                                          "uploads",
                                          "ocr_meta",
                                          s3ocrxml_filename),
                             "rb")
                    s3ocrxml = f.read()
                    f.close()

                    s3ocrdict = self.__s3ocrxml2dict(s3ocrxml)
                    crosslimit_options = {}
                    for resourcename in s3ocrdict["$resource_seq"]:
                        resource = s3ocrdict[resourcename]
                        for fieldname in resource["$field_seq"]:
                            field = resource[fieldname]
                            if field.has_options:
                                if field.options and \
                                   field.options.count > MAX_FORM_OPTIONS_LIMIT:
                                    if not crosslimit_options.has_key(resourcename):
                                        crosslimit_options[resourcename] = [fieldname]
                                    else:
                                        crosslimit_options[resourcename].append(fieldname)

                    if len(crosslimit_options) != 0:
                        s3xml_root = etree.fromstring(datafile_content)
                        resource_element = s3xml_root.getchildren()[0]
                        resourcename = resource_element.attrib.get("name")
                        for field in resource_element:
                            if field.tag == "data":
                                if crosslimit_options.has_key(resourcename):
                                    fieldname = field.attrib.get("field")
                                    if fieldname in crosslimit_options[resourcename]:
                                        match_status = {}
                                        value = field.text.encode("utf-8").lower()
                                        for option in s3ocrdict[resourcename][fieldname].options.list:
                                            try:
                                                fieldtext = option.label.lower()
                                            except:
                                                fieldtext = ""
                                            match_status[option.value] =\
                                                self.dameraulevenshtein(cast2ascii(fieldtext),
                                                                        cast2ascii(value))

                                        closematch_value = 1000000000
                                        closematch = []

                                        for match in match_status.keys():
                                            if match_status[match] < closematch_value:
                                                closematch = [match]
                                                closematch_value = match_status[match]
                                            elif match_status[match] == closematch_value:
                                                closematch.append(match)

                                        if len(closematch) > 0:
                                            value = closematch[0]
                                        else:
                                            value = ""

                                        field.text = value
                                        field.attrib["value"] = value


                            elif field.tag == "resource":
                                resourcename = field.attrib.get("name")
                                for subfield in field:
                                    if subfield.tag == "data":
                                        fieldname = subfield.attrib.get("field")
                                        if resourcename in crosslimit_options.keys() and\
                                                fieldname in crosslimit_options[resourcename]:
                                            match_status = {}
                                            value = subfield.text.encode("utf-8").lower()
                                            for option in s3ocrdict[resourcename][fieldname].options.list:
                                                try:
                                                    fieldtext = option.label.lower()
                                                except:
                                                    fieldtext = ""
                                                match_status[option.value] =\
                                                    self.dameraulevenshtein(cast2ascii(fieldtext),
                                                                            cast2ascii(value))

                                            closematch_value = 1000000000
                                            closematch = []

                                            for match in match_status.keys():
                                                if match_status[match] < closematch_value:
                                                    closematch = [match]
                                                    closematch_value = match_status[match]
                                                elif match_status[match] == closematch_value:
                                                    closematch.append(match)

                                            if len(closematch) > 0:
                                                value = closematch[0]
                                            else:
                                                value = ""

                                            subfield.text = value
                                            subfield.attrib["value"] = value

                        datafile_content = etree.tostring(s3xml_root)

                    # import_xml routine
                    outputjson = self.resource.import_xml(StringIO(datafile_content),
                                                          commit_job=False,
                                                          ignore_errors=True)

                    # Get metadata for review
                    jobuuid = self.resource.job.job_id
                    json2dict = json.loads(outputjson, strict=False)

                    if json2dict.has_key("message"):
                        jobhaserrors = 1
                    else:
                        jobhaserrors = 0

                    # Check status code
                    if json2dict.get("statuscode") != "200":
                        r.error(501, self.ERROR.UNRECOVERABLE_ERROR)

                    # Store metadata for review
                    db.ocr_form_status.insert(image_set_uuid=setuuid,
                                              form_uuid=formuuid,
                                              job_uuid=jobuuid,
                                              job_has_errors=jobhaserrors)

                    if r.component:
                        request_args = request.get("args", ["", ""])
                        record_id = request_args[0]
                        component_name = request_args[1]
                        urlprefix = "%s/%s/%s" % (request.function,
                                                  record_id,
                                                  component_name)

                    else:
                        # Not a component
                        urlprefix = request.function

                    redirect(URL(request.controller,
                                 "%s/upload.pdf" % urlprefix,
                                 args="review",
                                 vars={"jobuuid":jobuuid}))

                else:
                    # Render upload UI

                    # Check if user has UTC offset in his profile
                    auth = current.auth
                    if auth.user:
                        utc_offset = auth.user.utc_offset
                    else:
                        r.error(501, self.ERROR.NO_UTC_OFFSET)

                    # Load OCR tables
                    current.s3db.ocr_meta

                    # Create an html image upload form for user
                    formuuid = r.vars.get("formuuid", None)
                    uploadformat = r.vars.get("uploadformat", None)
                    requesturl = request.env.path_info
                    createurl = "%s/create.pdf" %\
                        requesturl[0:requesturl.rfind("/")]
                    if not (formuuid and uploadformat):
                        availForms = self.__getResourceForms()
                        return response.render("_ocr_upload.html",
                                               dict(availForms=availForms,
                                                    createurl=createurl))
                    else:
                        try:
                            numpages = self.__getNumPages(formuuid)
                        except:
                            r.error(501, current.ERROR.BAD_RECORD)

                        if not numpages:
                            r.error(501, self.ERROR.EMPTY_OCR_FORM)

                        return response.render("_ocr_page_upload.html",
                                               dict(numpages=numpages,
                                                    posturl=createurl,
                                                    formuuid=formuuid,
                                                    uploadformat=uploadformat))

                    numpages = self.__getNumPages(formuuid)
                    if not numpages:
                        r.error(501, self.ERROR.EMPTY_OCR_FORM)

                    return response.render("_ocr_page_upload.html",
                                           dict(numpages=numpages,
                                                posturl=createurl,
                                                formuuid=formuuid,
                                                uploadformat=uploadformat))

            else:
                r.error(405, current.ERROR.BAD_METHOD)

        elif r.http == "POST":
            if method == "create":
                # Upload scanned OCR images
                if not current.deployment_settings.has_module("ocr"):
                    r.error(501, self.ERROR.OCR_DISABLED)

                # Form meta vars
                formuuid = r.vars.formuuid
                numpages = int(r.vars.numpages)
                uploadformat = r.vars.uploadformat

                # Set id for given form
                import uuid
                setuuid = uuid.uuid1()

                # Load model
                current.s3db.ocr_meta

                # Check for upload format
                if uploadformat == "image":
                    # store each page into db/disk
                    payloadtable = db.ocr_payload
                    for eachpage in xrange(1, numpages + 1):
                        varname = "page%s" % eachpage
                        fileholder = r.vars[varname]
                        pagenumber = eachpage

                        # server side file validation
                        imgfilename = fileholder.filename
                        extension = lambda m: m[m.rfind(".") + 1:]
                        imageformats = ["jpg", "png", "gif", "bmp"]

                        if extension(imgfilename) not in imageformats:
                            r.error(501, self.ERROR.INVALID_IMAGE_TYPE)

                        # store page
                        payloadtable.insert(
                            image_set_uuid=setuuid,
                            image_file=payloadtable["image_file"].store(\
                                fileholder.file,
                                fileholder.filename),
                            page_number=pagenumber)

                elif uploadformat == "pdf":
                    fileholder = r.vars["pdffile"]
                    # server side file validation
                    filename = fileholder.filename
                    extension = lambda m: m[m.rfind(".") + 1:]

                    if extension(filename) != "pdf":
                        r.error(501, self.ERROR.NOT_PDF_FILE)

                    # create temp dir to extract the images
                    uniqueuuid = setuuid # to make it thread safe
                    inputfilename = "%s_%s" % (uniqueuuid, fileholder.filename)
                    outputfilename = "%s_%s.png" % (uniqueuuid,
                                                    fileholder.filename[:-4])

                    ocr_temp_dir = os.path.join(self.r.folder,
                                                "uploads", "ocr_temp")
                    try:
                        os.mkdir(ocr_temp_dir)
                    except(OSError):
                        pass

                    f = open(os.path.join(ocr_temp_dir, inputfilename), "w")
                    f.write(fileholder.file.read())
                    f.close()

                    success = subprocess.call(["convert",
                                               os.path.join(ocr_temp_dir,
                                                            inputfilename),
                                               os.path.join(ocr_temp_dir,
                                                            outputfilename)])
                    if success != 0:
                        self.r.error(501, self.ERROR.IMAGE_MAGICK_ERROR)

                    # Store each page into db/disk
                    payloadtable = db.ocr_payload

                    if numpages == 1:
                        imagefilename = outputfilename
                        imgfilepath = os.path.join(ocr_temp_dir, imagefilename)
                        try:
                            imgfile = open(imgfilepath)
                        except(IOError):
                            self.r.error(501, self.ERROR.INVALID_PDF)
                        pagenumber = 1

                        # Store page
                        payloadtable.insert(
                            image_set_uuid=setuuid,
                            image_file=payloadtable["image_file"].store(\
                                imgfile,
                                imagefilename),
                            page_number=pagenumber)
                        imgfile.close()
                        os.remove(imgfilepath)

                    else:
                        for eachpage in xrange(0, numpages):
                            imagefilename = "%s-%s.png" % (outputfilename[:-4],
                                                     eachpage)
                            imgfilepath = os.path.join(ocr_temp_dir,
                                                       imagefilename)
                            try:
                                imgfile = open(imgfilepath, "r")
                            except(IOError):
                                self.r.error(501, self.ERROR.INVALID_PDF)

                            pagenumber = eachpage + 1

                            # Store page
                            payloadtable.insert(
                                image_set_uuid=setuuid,
                                image_file=payloadtable["image_file"].store(\
                                    imgfile,
                                    imagefilename),
                                page_number=pagenumber)
                            imgfile.close()
                            os.remove(imgfilepath)

                    os.remove(os.path.join(ocr_temp_dir, inputfilename))
                    try:
                        os.rmdir(ocr_temp_dir)
                    except(OSError):
                        import shutil
                        shutil.rmtree(ocr_temp_dir)

                else:
                    r.error(501, self.ERROR.INVALID_IMAGE_TYPE)

                # OCR it
                s3ocrimageparser = S3OCRImageParser(self, r)
                output = s3ocrimageparser.parse(formuuid, setuuid)

                table = db.ocr_data_xml
                table.insert(image_set_uuid=setuuid,
                             data_file=table["data_file"].store(
                                                    StringIO(output),
                                                    "%s-data.xml" % setuuid),
                             form_uuid=formuuid,
                             )

                if r.component:
                    request_args = current.request.get("args", ["", ""])
                    record_id = request_args[0]
                    component_name = request_args[1]
                    urlprefix = "%s/%s/%s" % (request.function,
                                              record_id,
                                              component_name)

                else:
                    # Not a component
                    urlprefix = request.function

                redirect(URL(request.controller,
                             "%s/import.pdf" % urlprefix,
                             args="import",
                             vars={"setuuid":setuuid}))

            elif method == "import":
                if not current.deployment_settings.has_module("ocr"):
                    r.error(501, self.ERROR.OCR_DISABLED)

                authorised = self._permitted(method="create")
                if not authorised:
                    r.unauthorised()

                try:
                    if r.component:
                        trigger = r.args[3]
                    else:
                        trigger = r.args[1]
                except(IndexError):
                    trigger = None

                if trigger == "review":
                    # Review UI post
                    jobuuid = r.vars.pop("jobuuid")

                    # Check if operation is valid on the given job_uuid
                    statustable = current.s3db.ocr_form_status
                    query = (statustable.job_uuid == jobuuid)
                    row = db(query).select(statustable.review_status,
                                           limitby=(0, 1)).first()
                    if not row:
                        r.error(501, self.ERROR.INVALID_JOBID)

                    if row.review_status == 1:
                        # Job has already been reviewed
                        r.error(501, self.ERROR.JOB_COMPLETE)

                    try:
                        r.vars.pop("_utc_offset")
                    except:
                        pass

                    try:
                        ignore_fields = r.vars.pop("ignore-fields-list")
                    except:
                        ignore_fields = None

                    if not ignore_fields:
                        ignore_fields = []
                    else:
                        try:
                            ignore_fields = ignore_fields.split("|")
                        except:
                            ignore_fields = [ignore_fields]

                    datadict = Storage()
                    for field in r.vars.keys():
                        resourcetable, fieldname = field.split("-")
                        if not datadict.has_key(resourcetable):
                            datadict[resourcetable] = Storage()

                        datadict[resourcetable][fieldname] = r.vars[field]

                    for field in ignore_fields:
                        resourcetable, fieldname = field.split("-")
                        datadict[resourcetable].pop(fieldname)
                        if len(datadict[resourcetable]) == 0:
                            datadict.pop(resourcetable)

                    s3xml_etree_dict = Storage()
                    for resource in datadict.keys():
                        s3xml_root = etree.Element("s3xml")
                        resource_element = etree.SubElement(s3xml_root, "resource")
                        resource_element.attrib["name"] = resource

                        for field in datadict[resource].keys():
                            fieldvalue = datadict[resource][field]
                            fieldvalue = str(fieldvalue) if fieldvalue else ""
                            fieldtype = db[resource][field].type
                            if fieldtype.startswith("reference "):
                                reference_resource_name = fieldtype[len("reference "):]
                                # reference element
                                reference_element =\
                                    etree.SubElement(resource_element, "reference")
                                reference_element.attrib["field"] = field
                                reference_element.attrib["resource"] = reference_resource_name
                                # resource element
                                ref_res_element =\
                                    etree.SubElement(reference_element, "resource")
                                ref_res_element.attrib["name"] = reference_resource_name
                                # data element
                                ref_res_data_element =\
                                    etree.SubElement(ref_res_element, "data")
                                ref_res_data_element.attrib["field"] = "name"
                                try:
                                    ref_res_data_element.text = cast2ascii(fieldvalue)
                                except(ValueError):
                                    ref_res_data_element.text = ""
                            else:
                                field_element = etree.SubElement(resource_element, "data")
                                field_element.attrib["field"] = field
                                try:
                                    field_element.attrib["value"] = cast2ascii(fieldvalue)
                                except(ValueError):
                                    field_element.attrib["value"] = ""
                                try:
                                    field_element.text = cast2ascii(fieldvalue)
                                except(ValueError):
                                    field_element.text = ""

                        s3xml_etree_dict[resource] = s3xml_root

                    errordict = {}

                    _record = current.xml.record
                    s3record_dict = Storage()
                    for tablename in s3xml_etree_dict.keys():
                        record = _record(db[tablename],
                                         s3xml_etree_dict[tablename].getchildren()[0])
                        s3record_dict[tablename] = record

                    import_job = r.resource.import_tree(None, None, job_id=jobuuid,
                                                        ignore_errors=False,
                                                        commit_job=False)

                    response.headers["Content-Type"] = contenttype(".json")

                    for tablename in s3record_dict.keys():
                        record = s3record_dict[tablename]
                        possible_items = []
                        our_item = None
                        for eachitem in import_job.items.keys():
                            item = import_job.items[eachitem]
                            if item.table == tablename:
                                if item.data and (len(item.data) > 0):
                                    our_item = item
                                else:
                                    if item.data and (len(item.data) == 0):
                                        possible_items.append(item)

                        if our_item:
                            our_item.update(record)
                        elif len(possible_items) > 0:
                            possible_items[0].update(record)
                        else:
                            import_job.add_item(s3xml_etree_dict[tablename].getchildren()[0])

                        for resourcename in datadict.keys():
                            table = db[resourcename]
                            for field in datadict[resourcename].keys():
                                if not table[field].type.startswith("reference "):
                                    value, error = s3_validate(table,
                                                               field,
                                                               datadict[resourcename][field])
                                    if error:
                                        errordict["%s-%s" % (resourcename, field)] = str(error)

                    if not import_job.error_tree:
                        store_success = import_job.store()
                        if store_success:
                            if import_job.error_tree:
                                errordict = self.__parse_job_error_tree(import_job.error_tree)
                                success = False
                            else:
                                # Revalidate data
                                for resourcename in datadict.keys():
                                    table = db[resourcename]
                                    for field in datadict[resourcename].keys():
                                        if not table[field].type.startswith("reference "):
                                            value, error =\
                                                s3_validate(table,
                                                            field,
                                                            datadict[resourcename][field])
                                            if error:
                                                errordict["%s-%s" % (resourcename, field)] = str(error)

                                if len(errordict) > 0:
                                    success = False
                                else:
                                    success = True
                                    import_job.commit()

                        else:
                            errordict = self.__parse_job_error_tree(import_job.error_tree)
                            success = False
                    else:
                        errordict = self.__parse_job_error_tree(import_job.error_tree)
                        success = False

                    if success:
                        session.confirmation =\
                            T("OCR review data has been stored into the database successfully.")

                        # Perform cleanup
                        statustable = db["ocr_form_status"]
                        query = (statustable.job_uuid == jobuuid)
                        row = db(query).select(statustable.image_set_uuid).first()
                        image_set_uuid = row.image_set_uuid

                        # Set review status = true
                        db(query).update(review_status=1)

                        # Remove cropped images from the database
                        cropstable = db.ocr_field_crops
                        query = (cropstable.image_set_uuid == image_set_uuid)

                        # Delete uploaded files
                        rows = db(query).select(cropstable.image_file)
                        for row in rows:
                            filename = row.image_file
                            filepath = os.path.join(self.r.folder,
                                                    "uploads",
                                                    "ocr_payload",
                                                    filename)
                            os.remove(filepath)

                        # Delete records
                        db(query).delete()

                    return json.dumps({"success": success,
                                       "error": errordict})

            else:
                r.error(405, current.ERROR.BAD_METHOD)

        else:
            r.error(501, current.ERROR.BAD_REQUEST)

    # -------------------------------------------------------------------------
    def __parse_job_error_tree(self, tree):
        """
            create a dictionary of fields with errors

            @param tree: S3ImportJob.error_tree
            @return: errordict
        """

        errordict = {}

        for resource in tree:
            resourcename = resource.attrib.get("name")
            for field in resource:
                fieldname = field.attrib.get("field")
                error = field.attrib.get("error")
                if error:
                    errordict["%s-%s" % (resourcename, fieldname)] = error

        return errordict

    # -------------------------------------------------------------------------
    def dameraulevenshtein(self, seq1, seq2):
        """
            Calculate the Damerau-Levenshtein distance between sequences.

            This distance is the number of additions, deletions, substitutions,
            and transpositions needed to transform the first sequence into the
            second. Although generally used with strings, any sequences of
            comparable objects will work.

            Transpositions are exchanges of *consecutive* characters; all other
            operations are self-explanatory.

            This implementation is O(N*M) time and O(M) space, for N and M the
            lengths of the two sequences.

            >>> dameraulevenshtein('ba', 'abc')
            2
            >>> dameraulevenshtein('fee', 'deed')
            2

            It works with arbitrary sequences too:
            >>> dameraulevenshtein('abcd', ['b', 'a', 'c', 'd', 'e'])
            2
        """

        # codesnippet:D0DE4716-B6E6-4161-9219-2903BF8F547F
        # Conceptually, this is based on a len(seq1) + 1 * len(seq2) + 1 matrix.
        # However, only the current and two previous rows are needed at once,
        # so we only store those.
        oneago = None
        thisrow = range(1, len(seq2) + 1) + [0]
        for x in xrange(len(seq1)):
            # Python lists wrap around for negative indices, so put the
            # leftmost column at the *end* of the list. This matches with
            # the zero-indexed strings and saves extra calculation.
            twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
            for y in xrange(len(seq2)):
                delcost = oneago[y] + 1
                addcost = thisrow[y - 1] + 1
                subcost = oneago[y - 1] + (seq1[x] != seq2[y])
                thisrow[y] = min(delcost, addcost, subcost)
                # This block deals with transpositions
                if (x > 0 and y > 0 and seq1[x] == seq2[y - 1]
                    and seq1[x - 1] == seq2[y] and seq1[x] != seq2[y]):
                    thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
        return thisrow[len(seq2) - 1]

    # -------------------------------------------------------------------------
    def __temp_ocrdataxml_parser(self, s3ocrdataxml):
        """
            convert data generated from ocr parser to a dictionary

            @param s3dataxml: output of S3OCRImageParser

            @return: python dictionary equalant to the input xml
        """

        s3ocrdataxml_etree = etree.fromstring(s3ocrdataxml)
        s3ocrdatadict = Storage()

        s3xml_root = s3ocrdataxml_etree
        resource_element = s3xml_root.getchildren()[0]
        s3ocr_root = etree.Element("s3ocr")

        if self.r.component:     # if it is a component
            s3ocr_root.append(resource_element)

        else:                    # if it is main resource
            componentetrees = []
            # mres is main resource etree
            mres = etree.Element("resource")
            for attr in resource_element.attrib.keys():
                mres.set(attr, resource_element.attrib.get(attr))
            for field_element in resource_element:
                if field_element.tag in ["data", "reference"]:       # main resource fields
                    mres.append(field_element)
                elif field_element.tag == "resource":  # component resource
                    componentetrees.append(field_element)

            serialised_component_etrees = componentetrees

            # create s3ocr tree
            s3ocr_root.append(mres)
            for res in serialised_component_etrees:
                s3ocr_root.append(res)

        for resource in s3ocr_root:
            resourcename = resource.attrib.get("name")
            s3ocrdatadict[resourcename] = Storage()
            for field in resource:
                if field.tag == "reference":
                    fieldname = field.attrib.get("field")
                    ref_res_field = field.getchildren()[0]
                    datafield = ref_res_field.getchildren()[0]
                    value = datafield.text

                else:
                    fieldname = field.attrib.get("field")
                    value = field.attrib.get("value")
                    text = field.text
                    if not value:
                        value = text

                s3ocrdatadict[resourcename][fieldname] = value
        return s3ocrdatadict

    # -------------------------------------------------------------------------
    def __importjob2data(self, importjob):
        """
            convert data from import job into a dictionary

            @param importjob: S3ImportJob instance

            @return: data of S3ImportJob into a dictionary
        """

        s3ocrdata = Storage()

        import_item_dict = importjob.items
        for eachitem in import_item_dict.keys():
            import_item = import_item_dict[eachitem]
            if import_item.data and len(import_item.data) > 0:
                s3ocrdata[str(import_item.table)] = import_item.data

        return s3ocrdata

    # -------------------------------------------------------------------------
    def __create_review_form(self, s3ocrdict, s3ocrdata):
        """
            create a html review form using the available data

            @param s3ocrdict: output of self.__s3ocrxml2dict()
            @param s3ocrdata: output of self.__importjob2data()

            @return: html review form
        """

        ptablecontent = []
        fieldnum = 1
        request = current.request
        T = current.T
        r = self.r
        setuuid = self.setuuid
        if r.component:
            request_args = request.get("args",["",""])
            record_id = request_args[0]
            component_name = request_args[1]
            urlprefix = "%s/%s/%s" % (request.function,
                                      record_id,
                                      component_name)
        else:
            # Not a component
            urlprefix = request.function

        for resourcename in s3ocrdict["$resource_seq"]:
            # Resource title
            resource = s3ocrdict[resourcename]
            ptablecontent.append(TR(TD(DIV(resourcename, _class="resource_name"),
                                       _colspan="4"),
                                    _class="titletr")
                                 )

            ctablecontent = []
            for fieldname in resource["$field_seq"]:
                field = resource[fieldname]
                comment = field.comment if field.comment else ""

                try:
                    ocrdata = s3ocrdata[resourcename][fieldname]
                    if ocrdata:
                        condition = (isinstance(ocrdata, str) or \
                                     isinstance(ocrdata, int))
                        if condition:
                            value = str(ocrdata)
                        elif isinstance(ocrdata, date):
                            value = date.strftime(ocrdata, "%Y-%m-%d")
                        elif isinstance(ocrdata, datetime):
                            value = datetime.strftime(ocrdata, "%Y-%m-%d %H:%M:%S")
                        else:
                            value = unicodedata.normalize("NFKD",
                                                          ocrdata).encode("ascii",
                                                                          "ignore")
                    else:
                        value = ""
                except(KeyError):
                    value=""

                name = "%s-%s" % (resourcename, fieldname)

                if field.has_options:
                    if field.type == "multiselect":
                        if field.options.count <= MAX_FORM_OPTIONS_LIMIT:
                            options = []
                            optct = 1
                            try:
                                value = value.split("|")[1:-1]
                            except:
                                value = [str(value)]
                            chk = lambda m, n: "on" if str(m) in n else None
                            for option in field.options.list:
                                options.append(TD(IMG(_src=URL(request.application,
                                                               r.prefix,
                                                               "%s/upload.pdf" % urlprefix,
                                                               args="image",
                                                               vars={"setuuid": setuuid,
                                                                     "resource_table": resourcename,
                                                                     "field_name": fieldname,
                                                                     "value": option.value
                                                                     }
                                                               ),
                                                      _style="border: solid #333 1px;"),
                                                  _style="text-align:center;"),
                                               TD(INPUT(_id="%s-%s" % (name, optct),
                                                        _value=option.value,
                                                        _type="checkbox",
                                                        _class="field-%s" % fieldnum,
                                                        _name=name,
                                                        value=chk(option.value,
                                                                  value))),
                                               TD(LABEL(option.label,
                                                        _for="%s-%s" % (name, optct))))
                                optct += 1
                            input_area = TABLE(TR(options),
                                               _class="field-%s" % fieldnum)

                        else:
                            for line in xrange(1, 3):
                                ctablecontent.append(TR(TD(IMG(_src=URL(request.application,
                                                                        r.prefix,
                                                                        "%s/upload.pdf" % urlprefix,
                                                                        args="image",
                                                                        vars={"setuuid": setuuid,
                                                                              "resource_table": resourcename,
                                                                              "field_name": fieldname,
                                                                              "sequence": line
                                                                              }
                                                                        ),
                                                               _style="border: solid #333 1px;"),
                                                           _style="text-align:center; padding:5px;",
                                                           _colspan="4")))

                            options = []
                            optct = 1

                            chk = lambda m, n: "on" if str(m) in n else None
                            for option in field.options.list:
                                options.append(TR(TD(INPUT(_id="%s-%s" % (name, optct),
                                                           _value=option.value,
                                                           _type="checkbox",
                                                           _class="field-%s" % fieldnum,
                                                           _name=name,
                                                           value=chk(option.value,
                                                                     value)
                                                           )),
                                                  TD(LABEL(option.label,
                                                           _for="%s-%s" % (name, optct)))))
                                optct += 1
                            input_area = TABLE(options,
                                               _class="field-%s" % fieldnum)

                    elif field.type == "boolean":
                        options = []
                        optct = 1
                        chk = lambda m, n: m if str(m) == str(n) else None
                        for option in [Storage({"value": "yes",
                                                "label": T("Yes")}),
                                       Storage({"value": "no",
                                                "label": T("No")})]:
                            options.append(TD(IMG(_src=URL(request.application,
                                                           r.prefix,
                                                           "%s/upload.pdf" % urlprefix,
                                                           args="image",
                                                           vars={"setuuid": setuuid,
                                                                 "resource_table": resourcename,
                                                                 "field_name": fieldname,
                                                                 "value": option.value
                                                                 }
                                                           ),
                                                  _style="border: solid #333 1px;"),
                                              _style="text-align:center;"),
                                           TD(INPUT(_id="%s-%s" % (name, optct),
                                                    _value=option.value,
                                                    _type="radio",
                                                    _class="field-%s" % fieldnum,
                                                    _name=name,
                                                    value=chk(option.value,
                                                              value))),
                                              TD(LABEL(option.label,
                                                 _for="%s-%s" % (name, optct))))
                            optct += 1
                        input_area = TABLE(TR(options),
                                           _class="field-%s" % fieldnum)

                    else:
                        if field.options.count <= MAX_FORM_OPTIONS_LIMIT:
                            options = []
                            optct = 1
                            chk = lambda m, n: m if str(m) == str(n) else None
                            for option in field.options.list:
                                options.append(TD(IMG(_src=URL(request.application,
                                                               r.prefix,
                                                               "%s/upload.pdf" % urlprefix,
                                                               args="image",
                                                               vars={"setuuid": setuuid,
                                                                     "resource_table": resourcename,
                                                                     "field_name": fieldname,
                                                                     "value": option.value
                                                                     }
                                                               ),
                                                      _style="border: solid #333 1px;"),
                                                  _style="text-align:center;"),
                                               TD(INPUT(_id="%s-%s" % (name, optct),
                                                        _value=option.value,
                                                        _type="radio",
                                                        _class="field-%s" % fieldnum,
                                                        _name=name,
                                                        value=chk(option.value,
                                                                  value))),
                                               TD(LABEL(option.label,
                                                        _for="%s-%s" % (name, optct))))
                                optct += 1
                            input_area = TABLE(TR(options),
                                               _class="field-%s" % fieldnum)

                        else:
                            for line in xrange(1, 3):
                                ctablecontent.append(TR(TD(IMG(_src=URL(request.application,
                                                                        r.prefix,
                                                                        "%s/upload.pdf" % urlprefix,
                                                                        args="image",
                                                                        vars={"setuuid": setuuid,
                                                                              "resource_table": resourcename,
                                                                              "field_name": fieldname,
                                                                              "sequence": line
                                                                              }
                                                                        ),
                                                               _style="border: solid #333 1px;"),
                                                           _style="text-align:center; padding:5px;",
                                                           _colspan="4")))

                            options = []
                            optct = 1
                            chk = lambda m, n: m if str(m) == str(n) else None
                            for option in field.options.list:
                                options.append(TR(TD(INPUT(_id="%s-%s" % (name, optct),
                                                           _value=option.value,
                                                           _type="radio",
                                                           _class="field-%s" % fieldnum,
                                                           _name=name,
                                                           value=chk(option.value,
                                                                     value)
                                                           )),
                                                  TD(LABEL(option.label,
                                                           _for="%s-%s" % (name, optct)))))
                                optct += 1
                            input_area = TABLE(options,
                                               _class="field-%s" % fieldnum)

                else:
                    if field.type in ["string", "integer", "double"]:
                        for line in xrange(1, field.lines + 1):
                            ctablecontent.append(TR(TD(IMG(_src=URL(request.application,
                                                                    r.prefix,
                                                                    "%s/upload.pdf" % urlprefix,
                                                                    args="image",
                                                                    vars={"setuuid": setuuid,
                                                                          "resource_table": resourcename,
                                                                          "field_name": fieldname,
                                                                          "sequence": line
                                                                          }
                                                                    ),
                                                           _style="border: solid #333 1px;"),
                                                       _style="text-align:center; padding:5px;",
                                                       _colspan="4")))
                        input_area = INPUT(_id="%s-id" % name.replace("-", "_"),
                                           _class="field-%s" % fieldnum,
                                           _value=value, _name=name)

                    elif field.type == "date":
                        subsec = {"DD":1,
                                  "MO":2,
                                  "YYYY":3}
                        imglist = []
                        for sec in ["YYYY", "MO", "DD"]:
                            imglist.append(IMG(_src=URL(request.application,
                                                        r.prefix,
                                                        "%s/upload.pdf" % urlprefix,
                                                        args="image",
                                                        vars={"setuuid": setuuid,
                                                              "resource_table": resourcename,
                                                              "field_name": field,
                                                              "sequence": subsec[sec]}
                                                        ),
                                               _style="border: solid #333 1px;"))
                        ctablecontent.append(TR(TD(imglist,
                                                   _style="text-align:center; padding:5px;",
                                                   _colspan="4")))

                        try:
                            value = value.strftime("%Y-%m-%d")
                        except(AttributeError):
                            try:
                                value = datetime.strptime(value, "%Y-%m-%d")
                                value = value.strftime("%Y-%m-%d")
                            except(ValueError):
                                value = ""
                        input_area = INPUT(_id="%s-id" % name.replace("-", "_"),
                                           _class="field-%s date" % fieldnum,
                                           _value=value, _name=name)

                    elif field.type == "datetime":
                        subsec = {"HH":1,
                                  "MM":2,
                                  "DD":3,
                                  "MO":4,
                                  "YYYY":5}
                        imglist = []
                        for eachsec in ["YYYY", "MO", "DD", "HH", "MM"]:
                            imglist.append(IMG(_src=URL(request.application,
                                                        r.prefix,
                                                        "%s/upload.pdf" % urlprefix,
                                                        args="image",
                                                        vars={"setuuid": setuuid,
                                                              "resource_table": resourcename,
                                                              "field_name": fieldname,
                                                              "sequence": subsec[eachsec],
                                                              }
                                                        ),
                                               _style="border: solid #333 1px;"))
                        ctablecontent.append(TR(TD(imglist,
                                                   _style="text-align:center; padding:5px;",
                                                   _colspan="4")))

                        try:
                            value = value.strftime("%Y-%m-%d %H:%M:%S")
                        except(AttributeError):
                            try:
                                value = datetime.strptime(value,"%Y-%m-%d %H:%M:%S")
                                value = value.strftime("%Y-%m-%d %H:%M:%S")
                            except(ValueError):
                                value = ""

                        input_area = INPUT(_id="%s-id" % name.replace("-", "_"),
                                           _class="field-%s datetime" % fieldnum,
                                           _value=value, _name=name)

                    elif field.type == "textbox":
                        for line in xrange(1, field.lines + 1):
                            ctablecontent.append(TR(TD(IMG(_src=URL(request.application,
                                                                    r.prefix,
                                                                    "%s/upload.pdf" % urlprefix,
                                                                    args="image",
                                                                    vars={"setuuid": setuuid,
                                                                          "resource_table": resourcename,
                                                                          "field_name": fieldname,
                                                                          "sequence": line
                                                                          }
                                                                    ),
                                                           _style="border: solid #333 1px;"),
                                                       _style="text-align:center; padding:5px;",
                                                       _colspan="4")))
                        input_area = TEXTAREA(value,
                                              _class="field-%s" % fieldnum,
                                              _name=name)

                    else:
                        input_area = SPAN()

                ctablecontent.append(TR(TD(TABLE(TR(TD(field.label)),
                                                 TR(TD(SPAN(_id="%s-error" % name,
                                                            _style="font-size: 12px; font-weight:bold; color: red;",
                                                            _class="error-span")))),
                                           _class="label", _style="vertical-align: top;"),
                                        TD(input_area, _class="infield"),
                                        TD(comment, _class="comment", _style="vertical-align: top;"),
                                        TD(TAG["BUTTON"](T("clear"),
                                                         _name="button-%s" % fieldnum,
                                                         _class="clrbutton"
                                                         ),
                                           TAG["BUTTON"](T("ignore"),
                                                   _name="ignore-%s" % name,
                                                   _class="ignore-button"),
                                           _class="clear", _style="vertical-align: top;"),
                                        _class="fieldtr"))

                ctablecontent.append(TR(TD(_colspan="4",
                                           _style="border: solid #999 3px;")))
                fieldnum += 1

            ptablecontent.extend(ctablecontent)

        # Submit button
        ptablecontent.append(TR(TD(TAG["button"](T("Submit"),
                                                 _class="submit-button",
                                                 _style="width: 70px; height: 20px;"),
                                                 _colspan="4",
                                                 _style="text-align:center; padding: 5px;")))

        output = FORM(TABLE(ptablecontent, _class="ptable"),
                      _id="ocr-review-form")

        return output

    # -------------------------------------------------------------------------
    def __s3ocrxml2dict(self, s3ocrxml):
        """
            convert s3ocrxml to dictionary so that it can be used in templates

            @param s3ocrxml: content of a s3ocrxml file, in text

            @return: equivalent dictionary for s3ocrxml file
        """

        db = current.db
        s3ocr_etree = etree.fromstring(s3ocrxml)
        s3ocrdict = Storage()
        resource_seq = []

        for resource in s3ocr_etree:
            resourcename = resource.attrib.get("name")
            table = db[resourcename]
            s3ocrdict[resourcename] = Storage()
            resource_seq.append(resourcename)
            field_seq = []
            for field in resource:
                get = field.attrib.get
                fieldname = get("name")

                if get("readable") == "True" and \
                   get("writable") == "True":

                    field_seq.append(fieldname)

                    fieldlabel = get("label")
                    fieldtype = get("type")
                    numlines = get("lines", "1")

                    if get("reference") == "1":
                        fieldreference = True
                    else:
                        fieldreference = False
                    fieldresource = get("resource")
                    if get("has_options") == "True":
                        fieldhasoptions = True
                    else:
                        fieldhasoptions = False

                    # Get html comment
                    fieldcomment = table[fieldname].comment

                    if fieldhasoptions:
                        try:
                            s3ocrselect = field.getchildren()[0]
                            options_found = True
                        except(IndexError):
                            fieldoptions = None
                            options_found = False

                        if options_found:

                            numoptions = len(s3ocrselect.getchildren())
                            optionlist = []

                            for option in s3ocrselect:
                                optionlabel = option.text
                                optionvalue = option.attrib.get("value")
                                optionlist.append(Storage({"label": optionlabel,
                                                           "value": optionvalue}))

                            fieldoptions = Storage({"count": numoptions,
                                                    "list": optionlist})

                        else:
                            fieldoptions = None
                    else:
                        fieldoptions = None

                    s3ocrdict[resourcename][fieldname] = Storage({"label": fieldlabel,
                                                                  "type": fieldtype,
                                                                  "comment": fieldcomment,
                                                                  "reference": fieldreference,
                                                                  "resource": fieldresource,
                                                                  "has_options": fieldhasoptions,
                                                                  "options": fieldoptions,
                                                                  "lines": int(numlines)
                                                                  })
            s3ocrdict[resourcename]["$field_seq"] = field_seq

        s3ocrdict["$resource_seq"] = resource_seq

        return s3ocrdict

    # -------------------------------------------------------------------------
    def newDocument(self,
                    title,
                    header,
                    footer,
                    filename = None,
                    heading=None,
                    ):
        """
            This will create a new empty PDF document.
            Data then needs to be added to this document.

            @param title: The title that will appear at the top of the document
                          and in the filename

            @return: An empty pdf document
        """

        # Get the document variables
        now = self.request.now.isoformat()[:19].replace("T", " ")
        docTitle = "%s %s" % (title, now)
        if filename == None:
            self.filename = "%s_%s.pdf" % (title, now)
        else:
            self.filename = "%s_%s.pdf" % (filename, now)
        self.output = StringIO()
        self.doc = EdenDocTemplate(self.output, title=docTitle)
        self.doc.setPageTemplates(header,footer)
        self.content = []
        if heading == None:
            heading = title
        self.title = heading
        self.prevtitle = heading
        self.setPortrait()
        self.leftMargin = 0.4 * inch
        self.rightMargin = 0.4 * inch
        self.topMargin = 0.4 * inch
        self.bottomMargin = 0.4 * inch
        self.MINIMUM_MARGIN_SIZE = 0.3 * inch
        self.setMargins()

    # -------------------------------------------------------------------------
    def newOCRForm(self,
                   formUUID,
                   pdfname="ocrform.pdf",
                   top=65,
                   left=50,
                   bottom=None,
                   right=None,
                   **args):

        self.content = []
        self.output = StringIO()
        self.layoutEtree = etree.Element("s3ocrlayout")
        try:
            pdfTitle = current.response.s3.crud_strings[self.tablename].label_create.decode("utf-8")
        except:
            pdfTitle = self.resource.tablename

        formResourceName =  self.resource.tablename
        formRevision = self.__book_revision(formUUID, formResourceName)
        self.filename = "%s_rev%s.pdf" % (formResourceName, formRevision)
        self.doc = self.S3PDFOCRForm(self.output,
                                     formUUID=formUUID,
                                     pdfTitle = pdfTitle,
                                     formRevision=formRevision,
                                     formResourceName=formResourceName)

    # -------------------------------------------------------------------------
    def __getResourceForms(self):
        """
            Get all form UUIDs/Revs available for a given resource

            @return: a list of all available forms for the given
                     resource, the list will contain tuples such
                     that the first value is form-uuid and the
                     second value is form-revision
        """

        db = current.db
        table = db.ocr_meta
        query = (table.resource_name == self.resource.tablename)
        rows = db(query).select(table.form_uuid,
                                table.revision,
                                orderby=~table.revision)
        availForms = []
        append = availForms.append
        for row in rows:
            append({"uuid" : row.form_uuid,
                    "revision": row.revision,
                    })
        return availForms

    # -------------------------------------------------------------------------
    def __getNumPages(self, formuuid):
        """
            Gets Number of pages for given form UUID

            @param formuuid: uuid of the form, for which
                             number of pages is required

            @return: number of pages in a form identified
                     by uuid
        """

        db = current.db
        table = db.ocr_meta
        row = db(table.form_uuid == formuuid).select(table.pages,
                                                     limitby=(0, 1)
                                                     ).first()
        return int(row.pages)

    # -------------------------------------------------------------------------
    def __s3OCREtree(self):
        """
            Optimise & Modifiy s3xml etree to and produce s3ocr etree

            @return: s3ocr etree
        """

        r = self.r

        s3xml_etree = self.resource.export_struct(options=True,
                                                  references=True,
                                                  stylesheet=None,
                                                  as_json=False,
                                                  as_tree=True)

        # Additional XML tags
        ITEXT = "label"
        HINT = "comment"
        TYPE = "type"
        HASOPTIONS = "has_options"
        LINES = "lines"
        BOXES = "boxes"
        REFERENCE = "reference"
        RESOURCE = "resource"

        # Components Localised Text added to the etree
        # Convering s3xml to s3ocr_xml (nicer to traverse)
        s3xml_root = s3xml_etree.getroot()
        resource_element = s3xml_root.getchildren()[0]
        s3ocr_root = etree.Element("s3ocr")

        # Store components which have to be excluded
        settings = current.deployment_settings
        self.exclude_component_list =\
                    settings.get_pdf_excluded_fields("%s_%s" % \
                                                     (r.prefix,
                                                      r.resource.name))

        if r.component: # if it is a component
            s3ocr_root.append(resource_element)

        else: # if it is main resource
            componentetrees = []
            # mres is main resource etree
            mres = etree.Element("resource")
            for attr in resource_element.attrib.keys():
                mres.set(attr, resource_element.attrib.get(attr))
            for field_element in resource_element:
                if field_element.tag == "field":       # main resource fields
                    mres.append(field_element)
                elif field_element.tag == "resource":  # component resource
                    componentetrees.append(field_element)

            serialised_component_etrees = componentetrees

            # create s3ocr tree
            s3ocr_root.append(mres)
            for res in serialised_component_etrees:
                s3ocr_root.append(res)

        # Database fieldtype to ocr fieldtype mapping
        self.generic_ocr_field_type = {
            "string": "string",
            "text": "textbox",
            "boolean" : "boolean",
            "double": "double",
            "date": "date",
            "datetime": "datetime",
            "integer": "integer",
            "list:integer": "multiselect",
            "list:string": "multiselect",
            "list:double": "multiselect",
            "list:text": "multiselect",
            }

        # Remove fields which are not required
        # Load user-defined configurations
        FIELD_TYPE_LINES = { # mapping types with number of lines
            "string": 1,
            "textbox": 2,
            "integer": 1,
            "double": 1,
            "date": 1,
            "datetime": 1,
            }
        FIELD_TYPE_BOXES = { # mapping type with numboxes
            "integer": 8,
            "double": 16,
            }
        for resource in s3ocr_root.iterchildren():
            rget = resource.attrib.get
            resourcetablename = rget("name")

            # Exclude components
            if not r.component:
                if rget("name") in self.exclude_component_list:
                    s3ocr_root.remove(resource)
                    continue

            if "alias" in resource.attrib:
                alias = resource.attrib["alias"]
            elif "_" in resourcetablename:
                alias = resourcetablename.split("_", 1)[1]
            else:
                alias = resourcetablename

            if alias == self.resource.alias and \
                resourcetablename == self.resource.tablename:
                fieldresource = self.resource
            elif alias in self.resource.components:
                fieldresource = self.resource.components[alias]
            else:
                continue

            for field in resource.iterchildren():
                get = field.attrib.get
                set = field.set
                fieldname = get("name")
                # Fields which have to be displayed
                fieldtype = get(TYPE)

                if fieldtype.startswith("reference "):
                    set(RESOURCE, fieldtype.split("reference ")[1])
                    set(REFERENCE, "1")
                else:
                    set(REFERENCE, "0")

                # Load OCR-specific fieldtypes
                ocrfieldtype = self.generic_ocr_field_type.get(fieldtype, None)
                if ocrfieldtype != None:
                    set(TYPE, ocrfieldtype)
                    # Refresh fieldtypes after update
                    fieldtype = get(TYPE)

                # Set num boxes and lines
                fieldhasoptions = get(HASOPTIONS)
                if fieldhasoptions == "False":
                    set(LINES, str(FIELD_TYPE_LINES.get(fieldtype, 1)))
                    if fieldtype in FIELD_TYPE_BOXES.keys():
                        set(BOXES, str(FIELD_TYPE_BOXES.get(fieldtype)))

                # If field is readable but not writable set default value
                if get("readable", "False") == "True" and \
                   get("writable", "False") == "False":

                    fieldname = get("name")
                    try:
                        fielddefault = fieldresource.table[fieldname].default
                    except(KeyError):
                        fielddefault = "None"
                    set("default", str(fielddefault))

                # For unknown field types
                if fieldtype not in self.generic_ocr_field_type.values():
                    set(TYPE, "string")
                    set(HASOPTIONS, "False")
                    set(LINES, "2")
                    # Refresh fieldtypes after update
                    fieldtype = get(TYPE)

                # In OCR, boolean fields should be shown as options
                if fieldtype == "boolean":
                    set(HASOPTIONS, "True")

                # Fields removed which need not be displayed
                if get("readable", "False") == "False" and \
                   get("writable", "False") == "False":
                    resource.remove(field)
                    continue

                if get(HASOPTIONS, "False") == "True" and \
                   get(TYPE) != "boolean":
                    s3ocrselect = field.getchildren()[0]
                    for option in s3ocrselect.iterchildren():
                        if option.text == "" or option.text == None:
                            s3ocrselect.remove(option)
                            continue

        return s3ocr_root

    # -------------------------------------------------------------------------
    def OCRPDFManager(self):
        """
            Produces OCR Compatible PDF forms
        """

        T = current.T
        s3ocr_root = self.__s3OCREtree() # get element s3xml
        self.s3ocrxml = etree.tostring(s3ocr_root, pretty_print=DEBUG)
        self.content = []
        s3ocr_layout_etree = self.layoutEtree

        # @ToDo: Define font sizes centrally rather than in flowables
        #titlefontsize = 16
        #sectionfontsize = 14
        #regularfontsize = 12
        #hintfontsize = 10

        ITEXT = "label"
        HINT = "comment"
        TYPE = "type"
        HASOPTIONS = "has_options"
        LINES = "lines"
        BOXES = "boxes"
        REFERENCE = "reference"
        RESOURCE = "resource"

        dtformat = current.deployment_settings.get_L10n_datetime_format()
        if str(dtformat)[:2] == "%m":
            # US-style
            date_hint = T("fill in order: month(2) day(2) year(4)")
            datetime_hint = T("fill in order: hour(2) min(2) month(2) day(2) year(4)")
        else:
            # ISO-style
            date_hint = T("fill in order: day(2) month(2) year(4)")
            datetime_hint = T("fill in order: hour(2) min(2) day(2) month(2) year(4)")
        l10n = {
            "datetime_hint": {
                "date": date_hint,
                "datetime": datetime_hint,
                },
            "boolean": {
                "yes": T("Yes"),
                "no": T("No"),
                },
            "select": {
                "multiselect": T("Select one or more option(s) that apply"),
                "singleselect": T("Select the option that applies"),
                },
            }

        # Print the etree
        append = self.content.append
        SubElement = etree.SubElement
        for resource in s3ocr_root:
            name = resource.attrib.get("name")
            # Create resource element of ocr layout xml
            s3ocr_layout_resource_etree = SubElement(s3ocr_layout_etree,
                                                     "resource",
                                                     name=name)

            styleSheet = getStyleSheet()
            # @ToDo: Check if this is needed by OCR (removed for now as ugly)
            #append(DrawHrLine(0.5))
            #append(Paragraph(html_unescape_and_strip(resource.attrib.get(ITEXT,
            #                                                                 name)),
            #                 styleSheet["Section"]))
            #append(DrawHrLine(0.5))

            for field in resource.iterchildren():
                get = field.attrib.get
                # Create field element of ocr layout xml
                s3ocr_layout_field_etree = SubElement(s3ocr_layout_resource_etree,
                                                      "field",
                                                      name=get("name"),
                                                      type=get("type"))

                if get(REFERENCE) == "1":
                    s3ocr_layout_field_etree.set(REFERENCE, "1")
                    s3ocr_layout_field_etree.set(RESOURCE, get(RESOURCE))

                fieldlabel = get(ITEXT)
                spacing = " " * 5
                fieldhint = self.__trim(get(HINT))

                if fieldhint:
                    append(Paragraph(html_unescape_and_strip("%s%s( %s )" % \
                                                      (fieldlabel,
                                                       spacing,
                                                       fieldhint)),
                                     styleSheet["Question"]))

                else:
                    append(Paragraph(html_unescape_and_strip(fieldlabel),
                                     styleSheet["Question"]))

                if get("readable", "False") == "True" and \
                   get("writable", "False") == "False":
                    append(Paragraph(html_unescape_and_strip(get("default",
                                                                 "No default Value")),
                                     styleSheet["DefaultAnswer"]))

                    # Remove the layout component of empty fields
                    s3ocr_layout_resource_etree.remove(s3ocr_layout_field_etree)

                elif get(HASOPTIONS) == "True":
                    fieldtype = get(TYPE)
                    # The field has to be shown with options
                    if fieldtype == "boolean":
                        bool_text = l10n.get("boolean")
                        append(DrawOptionBoxes(s3ocr_layout_field_etree,
                                               [bool_text.get("yes").decode("utf-8"),
                                                bool_text.get("no").decode("utf-8")],
                                               ["yes", "no"]))

                    else:
                        if fieldtype == "multiselect":
                            option_hint = l10n.get("select").get("multiselect")
                        else:
                            #option_hint = l10n.get("select").get("singleselect")
                            option_hint = None

                        s3ocrselect = field.getchildren()[0]
                        numoptions = len(s3ocrselect.getchildren())

                        if numoptions <= MAX_FORM_OPTIONS_LIMIT:
                            s3ocr_layout_field_etree.attrib["limitcrossed"] = "1"
                            if option_hint:
                                append(DrawHintBox(option_hint.decode("utf-8")))

                            options = s3ocrselect.iterchildren()
                            # Only show 4 options per row
                            opts = []
                            oppend = opts.append
                            range = int(math.ceil(numoptions / 4.0))
                            for row in xrange(range):
                                labels = []
                                lappend = labels.append
                                values = []
                                vappend = values.append
                                i = 1
                                for option in options:
                                    label = option.text
                                    if label in opts:
                                        continue
                                    oppend(label)
                                    lappend(label)
                                    vappend(option.attrib.get("value"))
                                    if i == 4:
                                        break
                                    i += 1
                                append(DrawOptionBoxes(s3ocr_layout_field_etree,
                                                       labels,
                                                       values))
                        else:
                            append(DrawHintBox(T("Enter a value carefully without spelling mistakes, this field needs to match existing data.").decode("utf-8")))
                            for line in xrange(2):
                                append(StringInputBoxes(numBoxes=None,
                                                        etreeElem=s3ocr_layout_field_etree))
                else:
                    # It is a text field
                    fieldtype = get(TYPE)
                    BOXES_TYPES = ["string", "textbox", "integer",
                                   "double", "date", "datetime",]
                    if fieldtype in BOXES_TYPES:
                        if fieldtype in ["string", "textbox"]:
                            #form.linespace(3)
                            num_lines = int(get("lines", 1))
                            for line in xrange(num_lines):
                                append(StringInputBoxes(numBoxes=None,
                                                        etreeElem=s3ocr_layout_field_etree))

                        elif fieldtype in ["integer", "double"]:
                            num_boxes = int(get("boxes", 9))
                            append(StringInputBoxes(numBoxes=num_boxes,
                                                    etreeElem=s3ocr_layout_field_etree))

                        elif fieldtype in ["date", "datetime"]:
                            # Print hint
                            #hinttext = \
                            #    l10n.get("datetime_hint").get(fieldtype).decode("utf-8")
                            #append(DrawHintBox(hinttext))

                            if fieldtype == "datetime":
                                append(DateTimeBoxes(s3ocr_layout_field_etree))
                            elif fieldtype == "date":
                                append(DateBoxes(s3ocr_layout_field_etree))

                    else:
                        self.r.error(501, current.ERROR.PARSE_ERROR)
        return

    # -------------------------------------------------------------------------
    def __getOCRLayout(self):
        """
            return layout file

            @return: layout xml for the generated OCR form
        """

        prettyprint = True if DEBUG else False
        return etree.tostring(self.layoutEtree, pretty_print=prettyprint)

    # -------------------------------------------------------------------------
    @staticmethod
    def __trim(text):
        """
            Helper to trim off any enclosing paranthesis

            @param text: text which need to be trimmed

            @return: text with front and rear paranthesis stripped
        """

        if isinstance(text, str) and \
                text[0] == "(" and \
                text[-1] == ")":
            text = text[1:-1]
        return text

    # -------------------------------------------------------------------------
    def __update_dbmeta(self, formUUID, layoutXML, numPages):
        """
            Store the PDF layout information into the database/disk.

            @param formUUID: uuid of the generated form
            @param layoutXML: layout xml of the generated form
            @param numPages: number of pages in the generated form
        """

        layout_file_stream = StringIO(layoutXML)
        layout_file_name = "%s_xml" % formUUID

        s3ocrxml_file_stream = StringIO(self.s3ocrxml)
        s3ocrxml_file_name = "%s_ocrxml" % formUUID

        db = current.db
        table = db.ocr_meta
        rows = db(table.form_uuid == formUUID).select()
        row = rows[0]
        row.update_record(layout_file=table.layout_file.store(\
                layout_file_stream,
                layout_file_name),
                          s3ocrxml_file=table.s3ocrxml_file.store(\
                s3ocrxml_file_stream,
                s3ocrxml_file_name),
                          pages=numPages)

    # -------------------------------------------------------------------------
    @staticmethod
    def __book_revision(formUUID, formResourceName):
        """
            Books a revision number for current operation in ocr_meta

            @param formUUID: uuid of the generated form
            @param formResourceName: name of the eden resource
        """

        db = current.db
        table = current.s3db.ocr_meta

        # Determine revision
        #selector = table["revision"].max()
        #rows = db(table.resource_name == formResourceName).select(selector)
        #row = rows.first()
        #revision = 0 if (row[selector] == None) else (row[selector] + 1)

        # Make the table migratable
        # Take the timestamp in hex
        import uuid
        revision = uuid.uuid5(formUUID, formResourceName).hex.upper()[:6]

        table.insert(form_uuid=formUUID,
                     resource_name=formResourceName,
                     revision=revision)

        return revision

    # -------------------------------------------------------------------------
    @staticmethod
    def defaultTitle(resource):
        """
            Method to extract a generic title from the resource using the
            crud strings

            @param: resource: a S3Resource object

            @return: the title as a String
        """

        try:
            return current.response.s3.crud_strings.get(resource.table._tablename).get("title_list")
        except:
            # No CRUD Strings for this resource
            return current.T(resource.name.replace("_", " ")).decode("utf-8")

    # -------------------------------------------------------------------------
    def setMargins(self, left=None, right=None, top=None, bottom=None):
        """
            Method to set the margins of the document

            @param left: the size of the left margin, default None
            @param right: the size of the right margin, default None
            @param top: the size of the top margin, default None
            @param bottom: the size of the bottom margin, default None

            The margin is only changed if a value is provided, otherwise the
            last value that was set will be used. The original values are set
            up to be an inch - in newDocument()

            @todo: make this for a page rather than the document
        """

        if left != None:
            self.doc.leftMargin = left
            self.leftMargin = left
        else:
            self.doc.leftMargin = self.leftMargin
        if right != None:
            self.doc.rightMargin = right
            self.rightMargin = right
        else:
            self.doc.rightMargin = self.rightMargin
        if top != None:
            self.doc.topMargin = top
            self.topMargin = top
        else:
            self.doc.topMargin = self.topMargin
        if bottom != None:
            self.doc.bottomMargin = bottom
            self.bottomMargin = bottom
        else:
            self.doc.bottomMargin = self.bottomMargin

    # -------------------------------------------------------------------------
    def setPortrait(self):
        """
            Method to set the orientation of the document to be portrait

            @todo: make this for a page rather than the document
        """

        self.doc.pagesize = portrait(self.paper_size)

    # -------------------------------------------------------------------------
    def setLandscape(self):
        """
            Method to set the orientation of the document to be landscape

            @todo: make this for a page rather than the document
        """

        self.doc.pagesize = landscape(self.paper_size)

    # -------------------------------------------------------------------------
    def addTable(self,
                 resource = None,
                 raw_data = None,
                 list_fields=None,
                 report_groupby=None,
                 report_hide_comments=False
                ):
        """
            Method to create a table that will be inserted into the document

            @param resource: A S3Resource object
            @param list_Fields: A list of field names
            @param report_groupby: A field name that is to be used as a sub-group
                   All the records that share the same report_groupby value will
                   be clustered together
            @param report_hide_comments: Any comment field will be hidden

            This uses the class S3PDFTable to build and properly format the table.
            The table is then built and stored in the document flow ready for
            generating the pdf.

            If the table is too wide for the page then it will automatically
            adjust the margin, font or page orientation. If it is still too
            wide then the table will be split across multiple pages.
        """

        table = S3PDFTable(document=self,
                           resource=resource,
                           raw_data=raw_data,
                           list_fields=list_fields,
                           groupby=report_groupby,
                           hide_comments=report_hide_comments
                           )
        result = table.build()
        if result != None:
            self.content += result

    # -------------------------------------------------------------------------
    def extractrHeader(self,
                       rHeader
                       ):
        """
            Method to convert the HTML generated for a rHeader into PDF
        """

        # let's assume that it's a callable rHeader
        try:
            # switch the representation to html so the rHeader doesn't barf
            repr = self.r.representation
            self.r.representation = "html"
            html = rHeader(self.r)
            self.r.representation = repr
        except:
            # okay so maybe it wasn't ... it could be an HTML object
            html = rHeader
        parser = S3html2pdf(pageWidth = self.doc.width,
                            exclude_class_list=["tabs"])
        result = parser.parse(html)
        if result != None:
            self.content += result

    # -------------------------------------------------------------------------
    def addrHeader(self,
                   resource = None,
                   raw_data = None,
                   list_fields=None,
                   report_hide_comments=False
                  ):
        """
            Method to create a rHeader table that is inserted into the document

            @param resource: A S3Resource object
            @param list_Fields: A list of field names
            @param report_hide_comments: Any comment field will be hidden

            This uses the class S3PDFTable to build and properly format the table.
            The table is then built and stored in the document flow ready for
            generating the pdf.
        """

        rHeader = S3PDFRHeader(self,
                               resource,
                               raw_data,
                               list_fields,
                               report_hide_comments
                               )
        result = rHeader.build()
        if result != None:
            self.content += result

    # -------------------------------------------------------------------------
    def addPlainTable(self, text, style=None, append=True):
        """
        """

        table = Table(text, style=style)
        if append:
            self.content.append(table)
        return table

    # -------------------------------------------------------------------------
    def addParagraph(self, text, style=None, append=True):
        """
            Method to create a paragraph that may be inserted into the document

            @param text: The text for the paragraph
            @param append: If True then the paragraph will be stored in the
            document flow ready for generating the pdf.

            @return The paragraph

            This method can return the paragraph rather than inserting into the
            document. This is useful if the paragraph needs to be first
            inserted in another flowable, before being added to the document.
            An example of when this is useful is when large amounts of text
            (such as a comment) are added to a cell of a table.
        """

        if text != "":
            if style == None:
                styleSheet = getSampleStyleSheet()
                style = styleSheet["Normal"]
            para = Paragraph(text, style)
            if append:
                self.content.append(para)
            return para
        return ""

    # -------------------------------------------------------------------------
    def addSpacer(self, height, append=True):
        """
            Add a spacer to the story
        """

        spacer = Spacer(1, height)
        if append:
            self.content.append(spacer)
        return spacer

    # -------------------------------------------------------------------------
    def addOverlay(self, callback, data):
        """
            Add an overlay to the page
        """

        self.content.append(Overlay(callback, data))

    # -------------------------------------------------------------------------
    def addBoxes(self, cnt, append=True):
        """
            Add square text boxes for text entry to the story
        """

        boxes = StringInputBoxes(cnt, etree.Element("dummy"))
        if append:
            self.content.append(boxes)
        return boxes

    # -------------------------------------------------------------------------
    def throwPageBreak(self):
        """
            Method to force a page break in the report
        """

        self.content.append(PageBreak())

    # -------------------------------------------------------------------------
    def changePageTitle(self, newTitle):
        """
            Method to force a page break in the report
        """

        self.content.append(ChangePageTitle(self, newTitle))

    # -------------------------------------------------------------------------
    def getStyledTable(self, table, colWidths=None, rowHeights = None, style=[]):
        """
            Method to create a simple table
        """

        (list, style) = self.addCellStyling(table, style)
        return Table(list,
                     colWidths=colWidths,
                     rowHeights=rowHeights,
                     style=style,
                     )

    # -------------------------------------------------------------------------
    def getTableMeasurements(self, tempTable):
        """
            Method to calculate the dimensions of the table
        """

        tempDoc = EdenDocTemplate(StringIO())
        tempDoc.setPageTemplates(lambda x, y: None, lambda x, y: None)
        tempDoc.pagesize = portrait(self.paper_size)
        tempDoc.build([tempTable], canvasmaker=canvas.Canvas)
        return (tempTable._colWidths, tempTable._rowHeights)

    # -------------------------------------------------------------------------
    def cellStyle(self, style, cell):
        """
            Add special styles to the text in a cell
        """

        if style == "*GREY":
            return [("TEXTCOLOR", cell, cell, colors.lightgrey)]
        elif style == "*RED":
            return [("TEXTCOLOR", cell, cell, colors.red)]
        return []

    # -------------------------------------------------------------------------
    def addCellStyling(self, table, style):
        """
            Add special styles to the text in a table
        """

        row = 0
        for line in table:
            col = 0
            for cell in line:
                try:
                    if cell.startswith("*"):
                        (instruction,sep,text) = cell.partition(" ")
                        style += self.cellStyle(instruction, (col, row))
                        table[row][col] = text
                except:
                    pass
                col += 1
            row += 1
        return (table, style)

    # -------------------------------------------------------------------------
    def setHeaderBanner (self, image):
        """
            Method to add a banner to a page
            used by pageHeader
        """

        self.headerBanner = os.path.join(current.request.folder,image)

    # -------------------------------------------------------------------------
    def pageHeader(self, canvas, doc):
        """
            Method to generate the basic look of a page.
            It is a callback method and will not be called directly
        """

        canvas.saveState()
        if self.logo and os.path.exists(self.logo):
            im = Image.open(self.logo)
            (iwidth, iheight) = im.size
            height = 1.0 * inch
            width = iwidth * (height/iheight)
            canvas.drawImage(self.logo,
                             inch,
                             doc.pagesize[1] - 1.2 * inch,
                             width = width,
                             height = height)
        if self.headerBanner and os.path.exists(self.headerBanner):
            im = Image.open(self.headerBanner)
            (iwidth, iheight) = im.size
            height = 0.75 * inch
            width = iwidth * (height / iheight)
            canvas.drawImage(self.headerBanner,
                             3 * inch,
                             doc.pagesize[1] - 0.95 * inch,
                             width = width,
                             height = height)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(doc.pagesize[0] / 2.0,
                                 doc.pagesize[1] - 1.3*inch, self.title
                                )
        canvas.setFont("Helvetica-Bold", 8)
        now = S3DateTime.datetime_represent(datetime.utcnow(), utc=True)
        canvas.drawCentredString(doc.pagesize[0] - 1.5 * inch,
                                 doc.pagesize[1] - 1.3 * inch, now
                                )
        canvas.restoreState()

    # -------------------------------------------------------------------------
    def pageFooter(self, canvas, doc):
        """
            Method to generate the basic look of a page.
            It is a callback method and will not be called directly
        """

        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(inch, 0.75 * inch,
                          "Page %d %s" % (doc.page,
                                          self.prevtitle
                                         )
                         )
        self.prevtitle = self.title
        canvas.restoreState()

    # -------------------------------------------------------------------------
    def buildDoc(self):
        """
            Method to build the PDF document.
            The response headers are set up for a pdf document and the document
            is then sent

            @return the document as a stream of characters

            @todo add a proper template class so that the doc.build is more generic
        """

        styleSheet = getSampleStyleSheet()
        self.doc.build(self.content,
                       canvasmaker=canvas.Canvas)
        self.output.seek(0)
        return self.output.read()

    # Nested classes that extend external libraries
    # If the external library failed to be imported then we get a stacktrace
    if reportLabImported:

        # =====================================================================
        class S3PDFOCRForm(BaseDocTemplate):
            """
                Extended class of the BaseDocTemplate to be used with OCR Forms.
                The form has a standard page template that draws handles on the
                page in the four corners, the middle of the side and bottom edges
            """

            _invalidInitArgs = ("pageTemplates",)

            # -----------------------------------------------------------------
            def __init__(self, filename, **attr):

                BaseDocTemplate.__init__(self, filename, **attr)
                self.formUUID = attr.get("formUUID", "")
                self.formResourceName = attr.get("formResourceName", "")
                self.formRevision = attr.get("formRevision", "")
                self.pdfTitle = attr.get("pdfTitle", "OCR Form")
                self.content = []
                self.leftMargin = 20
                self.rightMargin = 20
                self.topMargin = 20
                self.bottomMargin = 20
                settings = current.deployment_settings
                if settings.get_pdf_size() == "Letter":
                    self.paper_size = LETTER
                else:
                    self.paper_size = A4

            # -----------------------------------------------------------------
            def handle_pageBegin(self):
                """
                    Override base method to add a change of page template after
                    the firstpage.
                """

                self._handle_pageBegin()
                self._handle_nextPageTemplate("Later")

            # -----------------------------------------------------------------
            def build(self, content=[], canvasmaker=canvas.Canvas, **attr):
                """
                    Build the document using the flowables.
                """

                T = current.T
                self._calc()    # in case we changed margins sizes etc
                frameT = Frame(self.leftMargin,
                               self.bottomMargin,
                               self.width,
                               self.height,
                               id="normal")
                self.addPageTemplates([PageTemplate(id="First",
                                                    frames=frameT,
                                                    onPage=self.firstPageTemplate,
                                                    pagesize=self.pagesize),
                                       PageTemplate(id="Later",
                                                    frames=frameT,
                                                    onPage=self.laterPageTemplate,
                                                    pagesize=self.pagesize)])

                # Generate PDF header
                ocrInstructions = [
                    T("1. Fill the necessary fields in BLOCK CAPITAL letters.").decode("utf-8"),
                    T("2. Always use one box per letter and leave one box space to separate words.").decode("utf-8"),
                    T("3. Fill in the circles completely.").decode("utf-8"),
                    ]
                # Put pdf title
                styleSheet = getStyleSheet()
                self.content = [Paragraph(html_unescape_and_strip(self.pdfTitle), styleSheet["Title"])]
                # Print input instructions
                append = self.content.append
                for eachInstruction in ocrInstructions:
                    append(Paragraph(html_unescape_and_strip(eachInstruction),
                                     styleSheet["Instructions"]))

                # Add content
                self.content.extend(content)
                # Build OCRable PDF form
                BaseDocTemplate.build(self, self.content,
                                      canvasmaker=canvasmaker)
                self.numPages = self.canv.getPageNumber() - 1

            # -----------------------------------------------------------------
            def firstPageTemplate(self, canvas, doc):
                """
                    Template for first page
                """

                self.laterPageTemplate(canvas, doc)

            # -----------------------------------------------------------------
            def laterPageTemplate(self, canvas, doc):
                """
                    Template for all pages but first
                """

                self.pageDecorate(canvas, doc)
                self.pageMeta(canvas, doc)

            # -----------------------------------------------------------------
            def pageDecorate(self, canvas, doc):
                """
                    Decorate Page with blocks for OCR-ability
                """

                canvas.saveState()
                pagewidth, pageheight = self.paper_size
                canvas.rect(10, 10, 10, 10, fill=1)                       #btlf
                canvas.rect(pagewidth - 20, 10, 10, 10, fill=1)           #btrt
                canvas.rect(10, pageheight - 20, 10, 10, fill=1)          #tplf
                canvas.rect(pagewidth / 2 - 5, 10, 10, 10, fill=1)        #btmd
                canvas.rect(10, pageheight / 2 - 5, 10, 10, fill=1)       #mdlf
                canvas.rect(pagewidth - 20,
                            pageheight - 20, 10, 10, fill=1)              #tprt
                canvas.rect(pagewidth - 20,
                            pageheight / 2 - 5, 10, 10, fill=1)           #mdrt
                canvas.restoreState()

            # -----------------------------------------------------------------
            def pageMeta(self, canvas, doc):
                """
                    Put pagenumber and other meta info on each page
                """

                canvas.saveState()
                canvas.setFont("Helvetica", 7)
                pageNumberText = "Page %s" % self.canv.getPageNumber()
                pagewidth, pageheight = self.paper_size
                metaHeight = 14
                pageNumberWidth = pagewidth - (((len(pageNumberText) + 2) * 5) + 40)
                pageNumberHeight = metaHeight
                canvas.drawString(pageNumberWidth, pageNumberHeight, pageNumberText)

                uuidText = "UUID %s" % self.formUUID
                uuidWidth = 40
                uuidHeight = metaHeight
                canvas.drawString(uuidWidth, uuidHeight, uuidText)
                resourceNameText = self.formResourceName
                revisionText = self.formRevision
                otherMetaText = "Resource %s      Revision %s" % (resourceNameText,
                                                                  revisionText)
                otherMetaWidth = (pagewidth / 2) + 20
                otherMetaHeight = metaHeight
                canvas.drawString(otherMetaWidth, otherMetaHeight, otherMetaText)
                canvas.restoreState()

# =============================================================================
class S3PDFDataSource:
    """
        Class to get the labels and the data from the database
    """

    def __init__(self, obj):
        """
            Method to create the S3PDFDataSource object
        """

        self.resource = obj.resource
        self.list_fields = obj.list_fields
        self.report_groupby = obj.report_groupby
        self.hideComments = obj.hideComments
        self.fields = None
        self.labels = None
        self.records = False

    # -------------------------------------------------------------------------
    def select(self):
        """
            Internally used method to get the data from the database

            If the list of fields is provided then only these will be returned
            otherwise all fields on the table will be returned

            Automatically the id field will be hidden, and if
            hideComments is true then the comments field will also be hidden.

            If a groupby field is provided then this will be used as the sort
            criteria, otherwise it will sort by the first field

            The returned records are stored in the records property.
        """

        resource = self.resource
        list_fields = self.list_fields
        if not list_fields:
            fields = resource.readable_fields()
            for field in fields:
                if field.type == "id":
                    fields.remove(field)
                if self.hideComments and field.name == "comments":
                    fields.remove(field)
            if not fields:
                fields = [table.id]
            list_fields = [f.name for f in fields]
        else:
            indices = s3codec.S3Codec.indices
            list_fields = [f for f in list_fields if f not in indices]

        # Filter and orderby
        filter = current.response.s3.filter
        if filter is not None:
            resource.add_filter(filter)
        orderby = self.report_groupby

        # Retrieve the resource contents
        table = resource.table
        rfields = resource.resolve_selectors(list_fields)[0]
        fields = [f for f in rfields if f.show]
        headers = [f.label for f in rfields if f.show]
        if orderby != None:
            orderby = fields[0].field
        self.records = resource.select(list_fields,
                                       limit=None,
                                       orderby=orderby,
                                       as_rows=True)

        # Pass to getLabels
        self.labels = headers
        # Pass to getData
        self.fields = fields
        # Better to return a PDF, even if it has no records
        #if not self.records:
        #    current.session.warning = current.ERROR.NO_RECORDS
        #    redirect(URL(extension=""))

    # -------------------------------------------------------------------------
    def getLabels(self):
        """
            Internally used method to get the field labels

            Used to remove the report_groupby label (if present)
        """

        # Collect the labels from the select() call
        labels = self.labels
        if self.report_groupby != None:
            for label in labels:
                if label == self.report_groupby.label:
                    labels.remove(label)
        return labels

    # -------------------------------------------------------------------------
    def getData(self):
        """
            Internally used method to format the data from the database

            This will extract the data from the returned records list.

            If there is a groupby then the records will be grouped by this field.
            For each new value the groupby field will be placed in a list of
            its own. This will then be followed by lists of the records that
            share this value

            If there is no groupby then the result is a simple matrix of
            rows by fields
        """

        # Build the data list
        data = []
        currentGroup = None
        subheadingList = []
        rowNumber = 1
        for item in self.records:
            row = []
            if self.report_groupby != None:
                # @ToDo: non-XML output should use Field.represent
                # - this saves the extra parameter
                groupData = s3_represent_value(self.report_groupby,
                                               record=item,
                                               strip_markup=True,
                                               non_xml_output=True
                                               )
                if groupData != currentGroup:
                    currentGroup = groupData
                    data.append([groupData])
                    subheadingList.append(rowNumber)
                    rowNumber += 1

            for field in self.fields:
                if self.report_groupby != None:
                    if field.label == self.report_groupby.label:
                        continue
                if field.field:
                    text = s3_represent_value(field.field,
                                              record=item,
                                              strip_markup=True,
                                              non_xml_output=True,
                                              extended_comments=True
                                              )
                if text == "" or not field.field:
                    # some represents replace the data with an image which will
                    # then be lost by the strip_markup, so get back what we can
                    tname = field.tname
                    fname = field.fname
                    if fname in item:
                        text = item[fname]
                    elif tname in item and fname in item[tname]:
                        text = item[tname][fname]
                    else:
                        text = ""
                row.append(text)
            data.append(row)
            rowNumber += 1
        return (subheadingList, data)

# =============================================================================
class S3PDFRHeader():
    """
        Class to build a simple table that holds the details of one record,
        which can then be placed in a pdf document

        This class doesn't need to be called directly.
        Rather see S3PDF.addrHeader()
    """

    def __init__(self,
                 document,
                 resource=None,
                 raw_data=None,
                 list_fields=None,
                 hide_comments=False
                 ):
        """
            Method to create an rHeader object

            @param document: An S3PDF object
            @param resource: An S3Resource object
            @param list_fields: A list of field names
            @param hide_comments: Any comment field will be hidden
        """

        self.pdf = document
        self.resource = resource
        self.raw_data = raw_data
        self.list_fields = list_fields
        self.hideComments = hide_comments
        self.report_groupby = None
        self.data = []
        self.subheadingList = []
        self.labels = []
        self.fontsize = 10

    # -------------------------------------------------------------------------
    def build(self):
        """
            Method to build the table.

            @return: A list of Table objects. Normally this will be a list with
                     just one table object, but if the table needs to be split
                     across columns then one object per page will be created.
        """

        if self.resource != None:
            ds = S3PDFDataSource(self)
            # Get records
            ds.select()
            self.labels = ds.getLabels()
            self.data.append(self.labels)
            (self.subheadingList, data) = ds.getData()
            self.data + data

        if self.raw_data != None:
            self.data = self.raw_data

        self.rheader = []
        if len(self.data) == 0:
            return None
        else:
            NONE = current.messages["NONE"]
            for index in range(len(self.labels)):
                try:
                    value = data[0][index]
                except:
                    value = NONE
                self.rheader.append([self.labels[index],
                                     value])
        content = []
        style = [("FONTSIZE", (0, 0), (-1, -1), self.fontsize),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                 ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ]
        (self.rheader,style) = self.pdf.addCellStyling(self.rheader, style)
        table = Table(self.rheader,
                      repeatRows=1,
                      style=style,
                      hAlign="LEFT",
                     )
        content.append(table)
        return content

# =============================================================================
# Custom Flowables (used by OCR)
if reportLabImported:

    # =========================================================================
    class DrawHrLine(Flowable):
        """
            Draw a horizontal line
        """

        def __init__(self, lineThickness):
            Flowable.__init__(self)
            self.lineThickness = 1
            if current.deployment_settings.get_pdf_size() == "Letter":
                self.paper_size = LETTER
            else:
                self.paper_size = A4

        # ---------------------------------------------------------------------
        def draw(self):
            canv = self.canv
            pagewidth, pageheight = self.paper_size
            self.canv.line(0, -5, pagewidth - 100, -5)

        # ---------------------------------------------------------------------
        def wrap(self, availWidth, availHeight):
            self._width = availWidth
            self._height = self.lineThickness
            return self._width, self._height

    # =========================================================================
    class StringInputBoxes(Flowable):
        """
            Draw input boxes in a complete line
        """

        def __init__(self, numBoxes=None, etreeElem=None):
            Flowable.__init__(self)
            self.spaceAfter = 2
            self.sideLength = 15
            self.numBoxes = numBoxes
            self.fontsize = 10
            self.etreeElem = etreeElem
            if current.deployment_settings.get_pdf_size() == "Letter":
                self.paper_size = LETTER
            else:
                self.paper_size = A4

        # ---------------------------------------------------------------------
        def draw(self):
            canv = self.canv
            pagewidth, pageheight = self.paper_size
            numBoxes = int((pagewidth - (100 + self.fontsize)) / self.sideLength)
            if self.numBoxes != None and\
                    isinstance(self.numBoxes, int):
                numBoxes = self.numBoxes
            canv.setLineWidth(0.90)
            canv.setStrokeGray(0.9)
            widthPointer = self.fontsize
            # values are set manually
            xpadding = 6 # default
            ypadding = 4
            margin = 50 # as set
            # Reportlab's coordinate system uses bottom left
            # as origin, so we have to take top left marker as
            # origin to provide input for Python Imaging.
            markerOrigin = (29, 29) # top left marker location
            xCoord = pagewidth - \
                     (self.layoutCoords[0] + xpadding + margin) - \
                     markerOrigin[0] + \
                     self.fontsize
            yCoord = pageheight - \
                     (self.layoutCoords[1] + ypadding + margin) - \
                     markerOrigin[1]
            for box in xrange(numBoxes):
                self.canv.rect(widthPointer,
                               0,
                               self.sideLength,
                               self.sideLength)
                widthPointer += self.sideLength
            StringInputBoxEtree = etree.SubElement(self.etreeElem,
                                                   "textbox",
                                                   x="%s" % xCoord,
                                                   y="%s" % yCoord,
                                                   side="%s" % self.sideLength,
                                                   boxes="%s" % numBoxes,
                                                   page="%s" % self.canv.getPageNumber())
            StringInputBoxEtree.text = " "

        # ---------------------------------------------------------------------
        def wrap(self, availWidth, availHeight):
            self.layoutCoords = availWidth, availHeight
            self._width = availWidth
            self._height = self.sideLength + self.spaceAfter
            return self._width, self._height

    # =========================================================================
    class DateBoxes(Flowable):
        """
            Draw date boxes
        """

        def __init__(self, etreeElem):
            Flowable.__init__(self)
            self.spaceAfter = 2
            self.sideLength = 15
            self.fontsize = 10
            self.etreeElem = etreeElem
            if current.deployment_settings.get_pdf_size() == "Letter":
                self.paper_size = LETTER
            else:
                self.paper_size = A4

        # ---------------------------------------------------------------------
        def draw(self):
            canv = self.canv
            pagewidth, pageheight = self.paper_size
            canv.setLineWidth(0.90)
            canv.setStrokeGray(0.9)
            widthPointer = self.fontsize
            # Values are set manually
            xpadding = 6 # default
            ypadding = 4
            margin = 50 # as set
            # Reportlab's coordinate system uses bottom left
            # as origin, so we have to take top left marker as
            # origin to provide input for Python Imaging.
            markerOrigin = (29, 29) # top left marker location
            xCoord = pagewidth - \
                     (self.layoutCoords[0] + xpadding + margin) - \
                     markerOrigin[0] + \
                     self.fontsize
            yCoord = pageheight - \
                     (self.layoutCoords[1] + ypadding + margin) - \
                     markerOrigin[1]

            sideLength = self.sideLength
            rect = self.canv.rect
            for box in xrange(1, 11):
                if box not in (3, 6):
                    rect(widthPointer,
                         0,
                         sideLength,
                         sideLength)
                else:
                    self.canv.drawString(widthPointer + 5,
                                         self.height,
                                         "/")
                widthPointer += 15
            getPageNumber = self.canv.getPageNumber
            dtformat = current.deployment_settings.get_L10n_datetime_format()
            if str(dtformat)[:2] == "%m":
                # US-style
                DateBoxEtree = etree.SubElement(self.etreeElem,
                                                "textbox",
                                                x="%s" % xCoord,
                                                y="%s" % yCoord,
                                                side="%s" % sideLength,
                                                boxes="2",
                                                page="%s" % getPageNumber())
                DateBoxEtree.text = "MO"
                DateBoxEtree = etree.SubElement(self.etreeElem,
                                                "textbox",
                                                x="%s" % (xCoord + (sideLength * 3)),
                                                y="%s" % yCoord,
                                                side="%s" % sideLength,
                                                boxes="2",
                                                page="%s" % getPageNumber())
                DateBoxEtree.text = "DD"
            else:
                # ISO-style
                DateBoxEtree = etree.SubElement(self.etreeElem,
                                                "textbox",
                                                x="%s" % xCoord,
                                                y="%s" % yCoord,
                                                side="%s" % sideLength,
                                                boxes="2",
                                                page="%s" % getPageNumber())
                DateBoxEtree.text = "DD"
                DateBoxEtree = etree.SubElement(self.etreeElem,
                                                "textbox",
                                                x="%s" % (xCoord + (sideLength * 3)),
                                                y="%s" % yCoord,
                                                side="%s" % sideLength,
                                                boxes="2",
                                                page="%s" % getPageNumber())
                DateBoxEtree.text = "MO"
            DateBoxEtree = etree.SubElement(self.etreeElem,
                                            "textbox",
                                            x="%s" % (xCoord + (sideLength * 6)),
                                            y="%s" % yCoord,
                                            side="%s" % sideLength,
                                            boxes="4",
                                            page="%s" % getPageNumber())
            DateBoxEtree.text = "YYYY"

        # ---------------------------------------------------------------------
        def wrap(self, availWidth, availHeight):
            self.layoutCoords = availWidth, availHeight
            self._width = availWidth
            self._height = self.sideLength + self.spaceAfter
            return self._width, self._height

    # =========================================================================
    class DateTimeBoxes(Flowable):
        """
            Draw datetime boxes
        """

        def __init__(self, etreeElem):
            Flowable.__init__(self)
            self.spaceAfter = 2
            self.sideLength = 15
            self.fontsize = 10
            self.etreeElem = etreeElem
            if current.deployment_settings.get_pdf_size() == "Letter":
                self.paper_size = LETTER
            else:
                self.paper_size = A4

        # ---------------------------------------------------------------------
        def draw(self):
            canv = self.canv
            pagewidth, pageheight = self.paper_size
            canv.setLineWidth(0.90)
            canv.setStrokeGray(0.9)
            widthPointer = self.fontsize
            # Values are set manually
            xpadding = 6 # default
            ypadding = 4
            margin = 50 # as set
            # Reportlab's coordinate system uses bottom-left
            # as origin, so we have to take top-left marker as
            # origin to provide input for Python Imaging.
            markerOrigin = (29, 29) # top-left marker location
            xCoord = pagewidth - \
                     (self.layoutCoords[0] + xpadding + margin) - \
                     markerOrigin[0]+\
                     self.fontsize
            yCoord = pageheight - \
                     (self.layoutCoords[1] + ypadding + margin) - \
                     markerOrigin[1]

            for box in xrange(1, 18):
                if box not in (3, 6, 7, 10, 13):
                    self.canv.rect(widthPointer,
                                   0,
                                   self.sideLength,
                                   self.sideLength)
                widthPointer += 15
            DateTimeBoxEtree = etree.SubElement(self.etreeElem,
                                                "textbox",
                                                x="%s" % xCoord,
                                                y="%s" % yCoord,
                                                side="%s" % self.sideLength,
                                                boxes="2",
                                                page="%s" % self.canv.getPageNumber())
            DateTimeBoxEtree.text = "HH"
            DateTimeBoxEtree = etree.SubElement(self.etreeElem,
                                                "textbox",
                                                x="%s" % (xCoord + (self.sideLength * 3)),
                                                y="%s" % yCoord,
                                                side="%s" % self.sideLength,
                                                boxes="2",
                                                page="%s" % self.canv.getPageNumber())
            DateTimeBoxEtree.text = "MM"
            dtformat = current.deployment_settings.get_L10n_datetime_format()
            if str(dtformat)[:2] == "%m":
                # US-style
                DateTimeBoxEtree = etree.SubElement(self.etreeElem,
                                                    "textbox",
                                                    x="%s" % (xCoord + (self.sideLength * 7)),
                                                    y="%s" % yCoord,
                                                    side="%s" % self.sideLength,
                                                    boxes="2",
                                                    page="%s" % self.canv.getPageNumber())
                DateTimeBoxEtree.text = "MO"
                DateTimeBoxEtree = etree.SubElement(self.etreeElem,
                                                    "textbox",
                                                    x="%s" % (xCoord + (self.sideLength * 10)),
                                                    y="%s" % yCoord,
                                                    side="%s" % self.sideLength,
                                                    boxes="2",
                                                    page="%s" % self.canv.getPageNumber())
                DateTimeBoxEtree.text = "DD"
            else:
                # ISO-style
                DateTimeBoxEtree = etree.SubElement(self.etreeElem,
                                                    "textbox",
                                                    x="%s" % (xCoord + (self.sideLength * 7)),
                                                    y="%s" % yCoord,
                                                    side="%s" % self.sideLength,
                                                    boxes="2",
                                                    page="%s" % self.canv.getPageNumber())
                DateTimeBoxEtree.text = "DD"
                DateTimeBoxEtree = etree.SubElement(self.etreeElem,
                                                    "textbox",
                                                    x="%s" % (xCoord + (self.sideLength * 10)),
                                                    y="%s" % yCoord,
                                                    side="%s" % self.sideLength,
                                                    boxes="2",
                                                    page="%s" % self.canv.getPageNumber())
                DateTimeBoxEtree.text = "MO"
            DateTimeBoxEtree = etree.SubElement(self.etreeElem,
                                                "textbox",
                                                x="%s" % (xCoord + (self.sideLength * 13)),
                                                y="%s" % yCoord,
                                                side="%s" % self.sideLength,
                                                boxes="4",
                                                page="%s" % self.canv.getPageNumber())
            DateTimeBoxEtree.text = "YYYY"

        # ---------------------------------------------------------------------
        def wrap(self, availWidth, availHeight):
            self.layoutCoords = availWidth, availHeight
            self._width = availWidth
            self._height = self.sideLength + self.spaceAfter
            return self._width, self._height

    # =========================================================================
    class DrawOptionBoxes(Flowable):
        """
            Draw a set of Option Boxes (for Boolean or Multi-Select)
            - along with Labels
        """

        def __init__(self, etreeElem, labels, values):
            Flowable.__init__(self)
            self.etreeElem = etreeElem
            self.fontsize = 8
            self.spaceAfter = 2
            self.labels = labels
            self.text = labels[0]
            self.values = values
            if current.deployment_settings.get_pdf_size() == "Letter":
                self.paper_size = LETTER
            else:
                self.paper_size = A4

        # ---------------------------------------------------------------------
        def draw(self):
            canv = self.canv
            pagewidth, pageheight = self.paper_size
            canv.setLineWidth(0.90)
            canv.setStrokeGray(0.9)
            fontsize = self.fontsize
            radius = (fontsize / 2) - 1
            # Values are set manually
            xpadding = 6 # default
            ypadding = 8
            margin = 50 # as set
            # Reportlab's coordinate system uses bottom left
            # as origin, so we have to take top-left marker as
            # origin to provide input for Python Imaging.
            markerOrigin = (29, 29) # top-left marker location
            layoutCoords = self.layoutCoords
            pwidth = pagewidth - (layoutCoords[0] + xpadding + margin) - markerOrigin[0]
            pheight = pageheight - (layoutCoords[1] + ypadding + margin) - markerOrigin[1]
            labels = self.labels
            index = 0
            values = self.values
            circle = self.canv.circle
            drawString = self.canv.drawString
            getPageNumber = self.canv.getPageNumber
            etreeElem = self.etreeElem
            height = self.height
            cheight = height + (fontsize / 4) + 1
            width = self.width
            # Width of the circle
            cwidth = width + fontsize
            # Initial X for the elements
            _cwidth = width + fontsize
            _swidth = width + (fontsize * 2)
            for label in labels:
                # Draw circle to fill-in
                circleCenter = (_cwidth, cheight)
                circle(circleCenter[0],
                       circleCenter[1],
                       radius,
                       fill=0)
                # Add label
                drawString(_swidth, height,
                           html_unescape_and_strip(label))
                xCoord = pwidth + circleCenter[0]
                yCoord = pheight + circleCenter[0]
                optionBoxEtree = etree.SubElement(etreeElem,
                                                  "optionbox",
                                                  x="%s" % xCoord,
                                                  y="%s" % yCoord,
                                                  radius="%s" % radius,
                                                  boxes="1",
                                                  page="%s" % getPageNumber())
                optionBoxEtree.set("value", values[index])
                optionBoxEtree.text = label
                xwidth = cwidth + (fontsize * (len(label) + 2)) / 1.4
                _cwidth += xwidth
                _swidth += xwidth
                index += 1

        # ---------------------------------------------------------------------
        def wrap(self, availWidth, availHeight):
            self.layoutCoords = availWidth, availHeight
            width = 0
            for label in self.labels:
                width += (len(label) + 8)
            fontsize = self.fontsize
            self._width = (fontsize * width) / 2
            self._height = fontsize + self.spaceAfter
            return self._width, self._height

    # =========================================================================
    class DrawHintBox(Flowable):
        """
            Draw Help Text to explain how to fill out a question
        """

        def __init__(self, text=""):
            Flowable.__init__(self)
            self.text = text
            self.fontsize = 6
            self.spaceAfter = 2
            if current.deployment_settings.get_pdf_size() == "Letter":
                self.paper_size = LETTER
            else:
                self.paper_size = A4

        # ---------------------------------------------------------------------
        def draw(self):
            canv = self.canv
            canv.setFillGray(0.4)
            self.canv.drawString(self.width + (self.fontsize / 2),
                                 self.height,
                                 html_unescape_and_strip(self.text))

        # ---------------------------------------------------------------------
        def wrap(self, availWidth, availHeight):
            fontsize = self.fontsize
            self._width = (fontsize * (len(self.text) + 4)) / 2
            self._height = fontsize + self.spaceAfter
            return self._width, self._height

    # -------------------------------------------------------------------------
    # Custom styleSheets
    _baseFontNameB = tt2ps(_baseFontName, 1, 0)
    _baseFontNameI = tt2ps(_baseFontName, 0, 1)
    _baseFontNameBI = tt2ps(_baseFontName, 1, 1)

    def getStyleSheet():
        """
        """

        styleSheet = getSampleStyleSheet()
        styleSheet.add(ParagraphStyle(name="Instructions",
                                      parent=styleSheet["Bullet"],
                                      fontName=_baseFontName,
                                      fontSize=12,
                                      firstLineIndent=0,
                                      spaceBefore=3),
                       alias="Inst")
        styleSheet.add(ParagraphStyle(name="Section",
                                      parent=styleSheet["Normal"],
                                      fontName=_baseFontName,
                                      fontSize=13,
                                      spaceBefore=5,
                                      spaceAfter=5,
                                      firstLineIndent=0),
                       alias="Sec")
        styleSheet.add(ParagraphStyle(name="Question",
                                      parent=styleSheet["Normal"],
                                      fontName=_baseFontName,
                                      fontSize=11,
                                      firstLineIndent=0,
                                      spaceAfter=5,
                                      spaceBefore=10),
                       alias="Quest")
        styleSheet.add(ParagraphStyle(name="DefaultAnswer",
                                      parent=styleSheet["Normal"],
                                      fontName=_baseFontName,
                                      fontSize=10,
                                      firstLineIndent=0,
                                      spaceBefore=3),
                       alias="DefAns")
        return styleSheet

# Helper functions (used by OCR)
html_unescape_and_strip = lambda m: html_strip(html_unescape(m))

# =============================================================================
def html_unescape(text):
    """
        Helper function, unscape any html special characters
    """

    return re.sub("&(%s);" % "|".join(name2codepoint),
                  lambda m: unichr(name2codepoint[m.group(1)]),
                  text)

# =============================================================================
def html_strip(text):
    """
        Strips html markup from text
    """

    mark = 0
    markstart = 0
    markend = 0
    index = 0
    occur = 0
    for i in text:
        if i == "<":
            try:
                if text[index+1] != " ":
                    mark = 1
                    markstart = index
            except(IndexError):
                pass
        elif i == ">":
            if mark == 1:
                mark = 0
                markend = index
                text = "%s%s" % (text[:markstart], text[markend+1:])
                occur = 1
                break

        index += 1

    if occur == 1:
        text = html_strip(text)

    return text

# =============================================================================
# Convert unicode to ascii compatible strings
cast2ascii = lambda m: \
    m if isinstance(m, str) else unicodedata.normalize("NFKD",
                                                       m).encode("ascii",
                                                                 "ignore")

# =============================================================================
class S3OCRImageParser(object):
    """
        Image Parsing and OCR Utility
    """

    def __init__(self, s3method, r):
        """
            Intialise class instance with environment variables and functions
        """

        self.r = r
        self.request = current.request
        checkDependencies(r)

    # -------------------------------------------------------------------------
    def parse(self, form_uuid, set_uuid, **kwargs):
        """
            Performs OCR on a given set of pages
        """

        raw_images = {}
        images = {}

        self.set_uuid = set_uuid
        db = current.db
        T = current.T
        request = self.request

        # Get metadata of the form
        metatable = "ocr_meta"
        query = (db[metatable]["form_uuid"] == form_uuid)
        row = db(query).select(limitby=(0, 1)).first()
        revision = row["revision"]
        resourcename = row["resource_name"]
        layoutfilename = row["layout_file"]
        pages = int(row["pages"])
        is_component = True if len(self.r.resource.components) == 1 else False

        # Open each page
        for eachpage in xrange(1, pages+1):
            payloadtable = "ocr_payload"
            row =\
                db((db[payloadtable]["image_set_uuid"]==set_uuid) &\
                       (db[payloadtable]["page_number"]==eachpage)
                   ).select().first()

            pageimagefile = row["image_file"]
            raw_images[eachpage] =\
                Image.open(os.path.join(self.r.folder,
                                        "uploads",
                                        "ocr_payload",
                                        pageimagefile))

        # Transform each image
        for each_img_index in raw_images.keys():
            images[each_img_index] = {}
            images[each_img_index]["image"] =\
                self.__convertImage2binary(raw_images[each_img_index])
            images[each_img_index]["markers"] =\
                self.__getMarkers(images[each_img_index]["image"])
            images[each_img_index]["orientation"] =\
                self.__getOrientation(images[each_img_index]["markers"])
            if images[each_img_index]["orientation"] != 0.0:
                images[each_img_index]["image"] =\
                    images[each_img_index]["image"].rotate(images[each_img_index]["orientation"])
                images[each_img_index]["markers"] =\
                    self.__getMarkers(images[each_img_index]["image"])
                images[each_img_index]["orientation"] =\
                    self.__getOrientation(images[each_img_index]["markers"])

            images[each_img_index]["scalefactor"] =\
                self.__scaleFactor(images[each_img_index]["markers"])

        # Get layout file, convert it to etree
        layout_file = open(os.path.join(self.r.folder,
                                        "uploads",
                                        "ocr_meta",
                                        layoutfilename),
                           "rb")
        layout_xml = layout_file.read()
        layout_file.close()
        layout_etree = etree.fromstring(layout_xml)

        # Data etree
        s3xml_root_etree = etree.Element("s3xml")
        parent_resource_exist = False

        SubElement = etree.SubElement
        for resource in layout_etree:
            # Create data etree
            if not is_component:
                if parent_resource_exist == False:
                    s3xml_parent_resource_etree = SubElement(s3xml_root_etree,
                                                             "resource")
                    s3xml_resource_etree = s3xml_parent_resource_etree
                    parent_resource_exist = True
                else:
                    s3xml_resource_etree = SubElement(s3xml_parent_resource_etree,
                                                      "resource")
            else:
                    s3xml_resource_etree = SubElement(s3xml_root_etree,
                                                      "resource")

            s3xml_resource_etree.set("name",
                                     resource.attrib.get("name", None))

            for field in resource:
                field_name = field.attrib.get("name", None)
                field_type = field.attrib.get("type", None)
                field_reference = field.attrib.get("reference")

                if field_reference == "1":
                    field_is_reference = True
                    field_resource = field.attrib.get("resource")
                else:
                    field_is_reference = False

                # Create data/reference etree
                if field_is_reference:
                    s3xml_reference_etree = SubElement(s3xml_resource_etree,
                                                       "reference")
                    s3xml_reference_etree.set("field", field_name)
                    s3xml_reference_etree.set("resource", field_resource)

                    s3xml_sub_reference_etree = SubElement(s3xml_reference_etree,
                                                           "resource")
                    s3xml_sub_reference_etree.set("name", field_resource)

                    s3xml_field_etree = SubElement(s3xml_sub_reference_etree,
                                                   "data")
                    s3xml_field_etree.set("field", "name")

                else:
                    s3xml_field_etree = SubElement(s3xml_resource_etree,
                                                   "data")
                    s3xml_field_etree.set("field", field_name)
                    #s3xml_field_etree.set("type", field_type)

                components = field.getchildren()
                numcomponents = len(components)
                null_field = False
                if numcomponents == 0:
                    continue
                else:
                    component_type = components[0].tag
                    if component_type in ("optionbox", "textbox"):
                        if component_type == "optionbox":
                            linenum = 0
                            OCRText = []
                            OCRValue = []
                            for component in components:
                                get = component.attrib.get
                                comp_x = float(get("x"))
                                comp_y = float(get("y"))
                                comp_boxes = int(get("boxes"))
                                comp_radius = float(get("radius"))
                                comp_page = int(get("page"))
                                comp_value = str(get("value"))
                                comp_text = str(component.text)
                                try:
                                    page_origin = images[comp_page]["markers"]
                                except(KeyError):
                                     self.r.error(501,
                                                  T("insufficient number of pages provided"))
                                crop_box = (
                                     int(page_origin[0][0]+\
                                             (comp_x*\
                                                  images[comp_page]["scalefactor"]["x"])-\
                                             comp_radius*images[comp_page]["scalefactor"]["x"]),
                                     int(page_origin[0][1]+\
                                             (comp_y*\
                                                  images[comp_page]["scalefactor"]["y"])-\
                                             comp_radius*images[comp_page]["scalefactor"]["y"]),
                                     int(page_origin[0][0]+\
                                             (comp_x*\
                                                  images[comp_page]["scalefactor"]["x"])+\
                                             comp_radius*images[comp_page]["scalefactor"]["x"]),
                                     int(page_origin[0][1]+\
                                             (comp_y*\
                                                  images[comp_page]["scalefactor"]["y"])+\
                                             comp_radius*images[comp_page]["scalefactor"]["y"]),
                                     )
                                temp_image = images[comp_page]["image"].crop(crop_box)
                                cropped_image = images[comp_page]["image"].crop(crop_box)
                                result = self.__ocrIt(cropped_image,
                                                      form_uuid,
                                                      resourcename,
                                                      linenum,
                                                      content_type="optionbox",
                                                      resource_table=resource.attrib.get("name"),
                                                      field_name=field.attrib.get("name"),
                                                      field_value=comp_value)
                                if result:
                                    OCRText.append(unicode.strip(comp_text.decode("utf-8")))
                                    OCRValue.append(unicode.strip(comp_value.decode("utf-8")))

                                linenum += 1

                            # Store values into xml
                            if len(OCRValue) in [0, 1]:
                                uOCRValue = "|".join(OCRValue)
                                uOCRText = "|".join(OCRText)
                            else:
                                uOCRValue = "|%s|" % "|".join(OCRValue)
                                uOCRText = "|%s|" % "|".join(OCRText)

                            s3xml_field_etree.set("value", uOCRValue)
                            s3xml_field_etree.text = uOCRText

                            if len(OCRValue) == 0:
                                null_field = True
                            else:
                                null_field = False

                        elif component_type == "textbox":
                            linenum = 1
                            if field_type in ["date", "datetime"]:
                                # Date(Time) Text Box
                                OCRedValues = {}
                                comp_count = 1
                                for component in components:
                                    get = component.attrib.get
                                    comp_x = float(get("x"))
                                    comp_y = float(get("y"))
                                    comp_boxes = int(get("boxes"))
                                    comp_side = float(get("side"))
                                    comp_page = int(get("page"))
                                    comp_meta = str(component.text)
                                    try:
                                        page_origin = images[comp_page]["markers"]
                                    except(KeyError):
                                        self.r.error(501,
                                                     T("insufficient number of pages provided"))
                                    crop_box = (
                                        int(page_origin[0][0]+\
                                                (comp_x*\
                                                     images[comp_page]["scalefactor"]["x"])),
                                        int(page_origin[0][1]+\
                                                (comp_y*\
                                                     images[comp_page]["scalefactor"]["y"])),
                                        int(page_origin[0][0]+\
                                                (comp_x*\
                                                     images[comp_page]["scalefactor"]["x"])+\
                                                comp_side*comp_boxes*images[comp_page]["scalefactor"]["x"]),
                                        int(page_origin[0][1]+\
                                                (comp_y*\
                                                     images[comp_page]["scalefactor"]["y"])+\
                                                comp_side*images[comp_page]["scalefactor"]["y"]),
                                        )
                                    cropped_image = images[comp_page]["image"].crop(crop_box)
                                    output = self.__ocrIt(cropped_image,
                                                          form_uuid,
                                                          resourcename,
                                                          linenum,
                                                          resource_table=resource.attrib.get("name"),
                                                          field_name=field.attrib.get("name"),
                                                          field_seq=comp_count)
                                    linenum += 1
                                    comp_count += 1

                                    OCRedValues[comp_meta] = unicode.strip(output.decode("utf-8"))

                                # YYYY
                                yyyy = datetime.now().year
                                try:
                                    if int(OCRedValues["YYYY"]) in range(1800, 2300):
                                        yyyy = int(OCRedValues["YYYY"])
                                except:
                                    pass

                                if yyyy % 4 == 0:
                                    leapyear = True
                                else:
                                    leapyear = False

                                # MO
                                try:
                                    if int(OCRedValues["MO"]) in range(1, 13):
                                        mo = int(OCRedValues["MO"])
                                except:
                                    mo = 1

                                # DD
                                try:
                                    if int(OCRedValues["DD"]) in range(1, 32):
                                        dd = int(OCRedValues["DD"])
                                except:
                                    dd = 1

                                if mo in [4, 6, 9, 11]:
                                    if dd == 31:
                                        dd = 1
                                elif mo == 2:
                                    if leapyear:
                                        if dd > 29:
                                            dd = 1
                                    else:
                                        if dd > 28:
                                            dd = 1

                                if field_type == "datetime":
                                    # MM
                                    try:
                                        if int(OCRedValues["MM"]) in range(0, 60):
                                            mm = int(OCRedValues["MM"])
                                    except:
                                        mm = 0

                                    # MM
                                    try:
                                        if int(OCRedValues["HH"]) in range(0, 24):
                                            hh = int(OCRedValues["HH"])
                                    except:
                                        hh = 0

                                if field_type == "date":
                                    s3xml_field_etree.set("value",
                                                          "%s-%s-%s" % (yyyy, mo, dd))
                                    s3xml_field_etree.text =\
                                        "%s-%s-%s" % (yyyy, mo, dd)

                                elif field_type == "datetime":
                                    utctime = self.__convert_utc(yyyy, mo, dd, hh, mm)
                                    utcftime = utctime.strftime("%Y-%m-%dT%H:%M:%SZ")
                                    s3xml_field_etree.set("value", utcftime)
                                    s3xml_field_etree.text = utcftime

                            else:
                                # Normal Text Box
                                ocrText = ""
                                comp_count = 1
                                for component in components:
                                    comp_x = float(component.attrib.get("x"))
                                    comp_y = float(component.attrib.get("y"))
                                    comp_boxes = int(component.attrib.get("boxes"))
                                    comp_side = float(component.attrib.get("side"))
                                    comp_page = int(component.attrib.get("page"))
                                    comp_meta = str(component.text)
                                    try:
                                        page_origin = images[comp_page]["markers"]
                                    except(KeyError):
                                        self.r.error(501,
                                                     T("insufficient number of pages provided"))
                                    crop_box = (
                                        int(page_origin[0][0]+\
                                                (comp_x*\
                                                     images[comp_page]["scalefactor"]["x"])),
                                        int(page_origin[0][1]+\
                                                (comp_y*\
                                                     images[comp_page]["scalefactor"]["y"])),
                                        int(page_origin[0][0]+\
                                                (comp_x*\
                                                     images[comp_page]["scalefactor"]["x"])+\
                                                comp_side*comp_boxes*images[comp_page]["scalefactor"]["x"]),
                                        int(page_origin[0][1]+\
                                                (comp_y*\
                                                     images[comp_page]["scalefactor"]["y"])+\
                                                comp_side*images[comp_page]["scalefactor"]["y"]),
                                        )
                                    cropped_image = images[comp_page]["image"].crop(crop_box)
                                    output = self.__ocrIt(cropped_image,
                                                          form_uuid,
                                                          resourcename,
                                                          linenum,
                                                          resource_table=resource.attrib.get("name"),
                                                          field_name=field.attrib.get("name"),
                                                          field_seq=comp_count)
                                    ocrText += output
                                    linenum += 1
                                    comp_count += 1

                                output = unicode.strip(ocrText.decode("utf-8"))
                                # Store OCRText
                                if field_type in ["double", "integer"]:
                                    try:
                                        output = int(self.__strip_spaces(output))
                                    except:
                                        output = 0
                                    s3xml_field_etree.set("value",
                                                          "%s" % output)
                                    s3xml_field_etree.text =\
                                        "%s" % output
                                else:
                                    s3xml_field_etree.text = output

                                if len("%s" % output) == 0:
                                    null_field = True
                                else:
                                    null_field = False

                    else:
                        continue

                if null_field:
                    if field_is_reference:
                        s3xml_resource_etree.remove(s3xml_reference_etree)

                    else:
                        s3xml_resource_etree.remove(s3xml_field_etree)

        output = etree.tostring(s3xml_root_etree, pretty_print=True)
        return output

    # -------------------------------------------------------------------------
    def __strip_spaces(self, text):
        """
            Remove all spaces from a string
        """

        try:
            text = "".join(text.split())
        except:
            pass

        return text

    # -------------------------------------------------------------------------
    def __convert_utc(self,
                      yyyy,
                      mo,
                      dd,
                      hh,
                      mm):
        """
            Convert local time to UTC
        """

        timetuple = datetime.strptime("%s-%s-%s %s:%s:00" % (yyyy,
                                                             mo,
                                                             dd,
                                                             hh,
                                                             mm),
                                      "%Y-%m-%d %H:%M:%S")
        auth = current.auth
        if auth.user:
            utc_offset = auth.user.utc_offset
        else:
            utc_offset = None
        try:
            t = utc_offset.split()[1]
            if len(t) == 5:
                sign = t[0]
                hours = t[1:3]
                minutes = t[3:5]
            tdelta = timedelta(hours=int(hours), minutes=int(minutes))
            if sign == "+":
                utctime = timetuple - tdelta
            elif sign == "-":
                utctime = timetuple + tdelta
        except:
            utctime = timetuple

        return utctime

    # -------------------------------------------------------------------------
    def __ocrIt(self,
                image,
                form_uuid,
                resourcename,
                linenum,
                content_type="textbox",
                **kwargs):
        """
            Put Tesseract to work, actual OCRing will be done here
        """

        db = current.db
        ocr_field_crops = "ocr_field_crops"
        import uuid
        uniqueuuid = uuid.uuid1() # to make it thread safe

        resource_table = kwargs.get("resource_table")
        field_name = kwargs.get("field_name")

        inputfilename = "%s_%s_%s_%s.tif" % (uniqueuuid,
                                             form_uuid,
                                             resourcename,
                                             linenum)
        outputfilename = "%s_%s_%s_%s_text" % (uniqueuuid,
                                               form_uuid,
                                               resourcename,
                                               linenum)

        ocr_temp_dir = os.path.join(self.r.folder, "uploads", "ocr_temp")

        try:
            os.mkdir(ocr_temp_dir)
        except(OSError):
            pass

        if content_type == "optionbox":
            field_value = kwargs.get("field_value")
            imgfilename = "%s.png" % inputfilename[:-3]
            imgpath = os.path.join(ocr_temp_dir, imgfilename)
            image.save(imgpath)
            imgfile = open(imgpath, "r")
            db[ocr_field_crops].insert(image_set_uuid=self.set_uuid,
                                       resource_table=resource_table,
                                       field_name=field_name,
                                       image_file=db[ocr_field_crops]["image_file"].store(imgfile,
                                                                                          imgfilename),
                                       value=field_value)
            imgfile.close()
            os.remove(imgpath)

            stat = ImageStat.Stat(image)
            if stat.mean[0] < 96 :
                return True
            else:
                return None

        elif content_type == "textbox":
            field_seq = kwargs.get("field_seq")

            inputpath = os.path.join(ocr_temp_dir, inputfilename)
            image.save(inputpath)

            success =\
                subprocess.call(["tesseract", inputpath,
                                 os.path.join(ocr_temp_dir, outputfilename)])
            if success != 0:
                self.r.error(501, ERROR.TESSERACT_ERROR)
            outputpath = os.path.join(ocr_temp_dir, "%s.txt" % outputfilename)
            outputfile = open(outputpath)
            outputtext = outputfile.read()
            outputfile.close()
            output = outputtext.replace("\n", " ")
            os.remove(outputpath)
            imgfilename = "%s.png" % inputfilename[:-3]
            imgpath = os.path.join(ocr_temp_dir, imgfilename)
            image.save(imgpath)
            imgfile = open(imgpath, "r")
            db[ocr_field_crops].insert(image_set_uuid=self.set_uuid,
                                       resource_table=resource_table,
                                       field_name=field_name,
                                       image_file=db[ocr_field_crops]["image_file"].store(imgfile,
                                                                                          imgfilename),
                                       sequence=field_seq)
            imgfile.close()
            os.remove(imgpath)
            os.remove(inputpath)

            try:
                os.rmdir(ocr_temp_dir)
            except(OSError):
                import shutil
                shutil.rmtree(ocr_temp_dir)
            return output

    # -------------------------------------------------------------------------
    def __convertImage2binary(self, image, threshold = 180):
        """
            Converts the image into binary based on a threshold. here it is 180
        """

        image = ImageOps.grayscale(image)
        image.convert("L")

        width, height = image.size

        for x in xrange(width):
            for y in xrange(height):
                if image.getpixel((x,y)) < 180 :
                    image.putpixel((x,y), 0)
                else:
                    image.putpixel((x,y), 255)
        return image

    # -------------------------------------------------------------------------
    def __findRegions(self, im):
        """
            Return the list of regions which are found by the following algorithm.

            -----------------------------------------------------------
            Raster Scanning Algorithm for Connected Component Analysis:
            -----------------------------------------------------------

            On the first pass:
            =================
            1. Iterate through each element of the data by column, then by row (Raster Scanning)
            2. If the element is not the background
                1. Get the neighboring elements of the current element
                2. If there are no neighbors, uniquely label the current element and continue
                3. Otherwise, find the neighbor with the smallest label and assign it to the current element
                4. Store the equivalence between neighboring labels

            On the second pass:
            ===================
            1. Iterate through each element of the data by column, then by row
            2. If the element is not the background
               1. Relabel the element with the lowest equivalent label
            ( source: http://en.wikipedia.org/wiki/Connected_Component_Labeling )
        """

        width, height  = im.size
        ImageOps.grayscale(im)
        im = im.convert("L")

        regions = {}
        pixel_region = [[0 for y in xrange(height)] for x in xrange(width)]
        equivalences = {}
        n_regions = 0

        # First pass: find regions.
        for x in xrange(width):
            for y in xrange(height):
                # Look for a black pixel
                if im.getpixel((x, y)) == 0 : # BLACK
                    # get the region number from north or west or create new region
                    region_n = pixel_region[x-1][y] if x > 0 else 0
                    region_w = pixel_region[x][y-1] if y > 0 else 0
                    #region_nw = pixel_region[x-1][y-1] if x > 0 and y > 0 else 0
                    #region_ne = pixel_region[x-1][y+1] if x > 0 else 0

                    max_region = max(region_n, region_w)

                    if max_region > 0:
                        #a neighbour already has a region, new region is the smallest > 0
                        new_region = min(filter(lambda i: i > 0, (region_n, region_w)))
                        #update equivalences
                        if max_region > new_region:
                            if max_region in equivalences:
                                equivalences[max_region].add(new_region)
                            else:
                                equivalences[max_region] = set((new_region, ))
                    else:
                        n_regions += 1
                        new_region = n_regions

                    pixel_region[x][y] = new_region

        # Scan image again, assigning all equivalent regions the same region value.
        for x in xrange(width):
            for y in xrange(height):
                r = pixel_region[x][y]
                if r > 0:
                    while r in equivalences:
                        r = min(equivalences[r])

                    if r in regions:
                        regions[r].add(x, y)
                    else:
                        regions[r] = self.__Region(x, y)

        return list(regions.itervalues())

    # -------------------------------------------------------------------------
    def __getOrientation(self, markers):
        """
            Returns orientation of the sheet in radians
        """

        x1, y1 = markers[0]
        x2, y2 = markers[2]
        try:
            slope = ((x2 - x1) * 1.0) / ((y2 - y1) * 1.0)
        except(ZeroDivisionError):
            slope = 999999999999999999999999999
        return math.atan(slope) * (180.0 / math.pi) * (-1)

    # -------------------------------------------------------------------------
    def __scaleFactor(self, markers):
        """
            Returns the scale factors lengthwise and breadthwise
        """

        stdWidth = sum((596, -60))
        stdHeight = sum((842, -60))
        li = [markers[0], markers[2]]
        sf_y = self.__distance(li)/stdHeight
        li = [markers[6], markers[2]]
        sf_x = self.__distance(li)/stdWidth
        return {"x": sf_x,
                "y": sf_y
                }

    # -------------------------------------------------------------------------
    def __distance(self, li):
        """
            Returns the euclidean distance if the input is of the form [(x1, y1), (x2, y2)]
        """

        return math.sqrt(math.fsum((math.pow(math.fsum((int(li[1][0]), -int(li[0][0]))), 2), math.pow(math.fsum((int(li[1][1]), -int(li[0][1]))), 2))))

    # -------------------------------------------------------------------------
    def __getMarkers(self, image):
        """
            Gets the markers on the OCR image
        """

        centers = {}
        present = 0

        regions = self.__findRegions(image)

        for r in regions:
            if r.area > 320 and r.aspectratio() < 1.5 and r.aspectratio() > 0.67:
                present += 1
                centers[present] = r.centroid()

        # This is the list of all the markers on the form.
        markers = list(centers.itervalues())
        markers.sort()
        l1 = sorted(markers[0:3], key=lambda y: y[1])
        l2 = markers[3:4]
        l3 = sorted(markers[4:7], key=lambda y: y[1])
        markers = []
        markers.extend(l1)
        markers.extend(l2)
        markers.extend(l3)
        #markers.sort(key=lambda x: (x[0], x[1]))
        return markers

    # =========================================================================
    class __Region():
        """
        """

        def __init__(self, x, y):
            """ Initialize the region """
            self._pixels = [(x, y)]
            self._min_x = x
            self._max_x = x
            self._min_y = y
            self._max_y = y
            self.area = 1

        # ---------------------------------------------------------------------
        def add(self, x, y):
            """ Add a pixel to the region """
            self._pixels.append((x, y))
            self.area += 1
            self._min_x = min(self._min_x, x)
            self._max_x = max(self._max_x, x)
            self._min_y = min(self._min_y, y)
            self._max_y = max(self._max_y, y)

        # ---------------------------------------------------------------------
        def centroid(self):
            """ Returns the centroid of the bounding box """
            return ((self._min_x + self._max_x) / 2,
                    (self._min_y + self._max_y) / 2)

        # ---------------------------------------------------------------------
        def box(self):
            """ Returns the bounding box of the region """
            return [ (self._min_x, self._min_y) , (self._max_x, self._max_y)]

        # ---------------------------------------------------------------------
        def aspectratio(self):
            """ Calculating the aspect ratio of the region """
            width = self._max_x - self._min_x
            length = self._max_y - self._min_y
            return float(width)/float(length)

# END =========================================================================
