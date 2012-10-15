# -*- coding: utf-8 -*-

""" Resource Import Tools

    @copyright: 2011-12 (c) Sahana Software Foundation
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

# @todo: remove all interactive error reporting out of the _private methods, and raise exceptions instead.
__all__ = ["S3Importer", "S3ImportJob", "S3ImportItem"]

import os
import sys
import cPickle
import tempfile
from datetime import datetime
from copy import deepcopy
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.serializers import json as jsons
from gluon.storage import Storage, Messages
from gluon.tools import callback

from s3crud import S3CRUD
from s3xml import S3XML
from s3utils import s3_mark_required, s3_has_foreign_key, s3_get_foreign_key
from s3resource import S3Resource

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3IMPORTER: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3Importer(S3CRUD):
    """
        Transformable formats (XML, JSON, CSV) import handler
    """

    UPLOAD_TABLE_NAME = "s3_import_upload"

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply CRUD methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view

            Known means of communicating with this module:

            It expects a URL of the form: /prefix/name/import

            It will interpret the http requests as follows:

            GET     will trigger the upload
            POST    will trigger either commits or display the import details
            DELETE  will trigger deletes

            It will accept one of the following control vars:
            item:   to specify a single item in the import job
            job:    to specify a job
            It should not receive both so job takes precedent over item

            For CSV imports, the calling controller can add extra fields
            to the upload form to add columns to each row in the CSV. To add
            the extra fields, pass a named parameter "csv_extra_fields" to the
            s3_rest_controller call (or the S3Request call, respectively):

            s3_rest_controller(module, resourcename,
                               csv_extra_fields=[
                                    dict(label="ColumnLabelInTheCSV",
                                         field=field_instance)
                               ])

            The Field instance "field" will be added to the upload form, and
            the user input will be added to each row of the CSV under the
            label as specified. If the "field" validator has options, the
            input value will be translated into the option representation,
            otherwise the value will be used as-is.

            Note that the "label" in the dict is the column label in the CSV,
            whereas the field label for the form is to be set in the Field
            instance passed as "field".

            You can add any arbitrary number of csv_extra_fields to the list.

            Additionally, you may want to allow the user to choose whether
            the import shall first remove all existing data in the target
            table. To do so, pass a label for the "replace_option" to the
            request:

            s3_rest_controller(module, resourcename,
                               replace_option=T("Remove existing data before import"))

            This will add the respective checkbox to the upload form.

            You may also want to provide a link to download a CSV template from
            the upload form. To do that, add the resource name to the request
            attributes:

            s3_rest_controller(module, resourcename,
                               csv_template="<resourcename>")

            This will provide a link to:
                - static/formats/s3csv/<controller>/<resourcename>.csv
            at the top of the upload form.

        """

        _debug("S3Importer.apply_method(%s)" % r)

        # Messages
        T = current.T
        messages = self.messages = Messages(T)
        messages.download_template = "Download Template"
        messages.invalid_file_format = "Invalid File Format"
        messages.unsupported_file_type = "Unsupported file type of %s"
        messages.stylesheet_not_found = "No Stylesheet %s could be found to manage the import file."
        messages.no_file = "No file submitted"
        messages.file_open_error = "Unable to open the file %s"
        messages.file_not_found = "The file to upload is missing"
        messages.no_records_to_import = "No records to import"
        messages.no_job_to_delete = "No job to delete, maybe it has already been deleted."
        messages.title_job_read = "Details of the selected import job"
        messages.title_job_list = "List of import items"
        messages.file_uploaded = "Import file uploaded"
        messages.upload_submit_btn = "Upload Data File"
        messages.open_btn = "Open"
        messages.view_btn = "View"
        messages.delete_btn = "Delete"
        messages.item_show_details = "Display Details"
        messages.job_total_records = "Total records in the Import Job"
        messages.job_records_selected = "Records selected"
        messages.job_deleted = "Import job deleted"
        messages.job_completed = "Job run on %s. With result of (%s)"
        messages.import_file = "Import File"
        messages.import_file_comment = "Upload a file formatted according to the Template."
        messages.user_name = "User Name"
        messages.commit_total_records_imported = "%s records imported"
        messages.commit_total_records_ignored = "%s records ignored"
        messages.commit_total_errors = "%s records in error"

        try:
            self.uploadTitle = current.response.s3.crud_strings[self.tablename].title_upload or T("Import")
        except:
            self.uploadTitle = T("Import")

        # @todo: correct to switch this off for the whole session?
        current.session.s3.ocr_enabled = False

        # Reset all errors/warnings
        self.error = None
        self.warning = None

        # CSV upload configuration
        if "csv_stylesheet" in attr:
            self.csv_stylesheet = attr["csv_stylesheet"]
        else:
            self.csv_stylesheet = None
        self.csv_extra_fields = None
        self.csv_extra_data = None

        # Environment
        self.controller = r.controller
        self.function = r.function

        # Target table for the data import
        self.controller_resource = self.resource
        self.controller_table = self.table
        self.controller_tablename = self.tablename

        # Table for uploads
        self.__define_table()
        self.upload_resource = None
        self.item_resource = None

        # XSLT Path
        self.xslt_path = os.path.join(r.folder, r.XSLT_PATH)
        self.xslt_extension = r.XSLT_EXTENSION

        # Check authorization
        permitted = current.auth.s3_has_permission
        authorised = permitted("create", self.upload_tablename) and \
                     permitted("create", self.controller_tablename)
        if not authorised:
            if r.method is not None:
                r.unauthorised()
            else:
                return dict(form=None)

        # @todo: clean this up
        source = None
        open_file = None
        transform = None
        upload_id = None
        items = None
        # @todo get the data from either get_vars or post_vars appropriately
        #       for post -> commit_items would need to add the uploadID
        if "transform" in r.get_vars:
            transform = r.get_vars["transform"]
        if "filename" in r.get_vars:
            source = r.get_vars["filename"]
        if "job" in r.post_vars:
            upload_id = r.post_vars["job"]
        elif "job" in r.get_vars:
            upload_id = r.get_vars["job"]
        items = self._process_item_list(upload_id, r.vars)
        if "delete" in r.get_vars:
            r.http = "DELETE"

        # If we have an upload ID, then get upload and import job
        self.upload_id = upload_id
        query = (self.upload_table.id == upload_id)
        self.upload_job = current.db(query).select(limitby=(0, 1)).first()
        if self.upload_job:
            self.job_id = self.upload_job.job_id
        else:
            self.job_id = None


        # Experimental uploading via ajax - added for vulnerability
        # Part of the problem with this is that it works directly with the
        # opened file. This might pose a security risk, is should be alright
        # if only trusted users are involved but care should be taken with this
        self.ajax = current.request.ajax and r.post_vars.approach == "ajax"

        # Now branch off to the appropriate controller function
        if r.http == "GET":
            if source != None:
                self.commit(source, transform)
                output = self.upload(r, **attr)
            if upload_id != None:
                output = self.display_job(upload_id)
            else:
                output = self.upload(r, **attr)
        elif r.http == "POST":
            if items != None:
                output = self.commit_items(upload_id, items)
            else:
                output = self.generate_job(r, **attr)
        elif r.http == "DELETE":
            if upload_id != None:
                output = self.delete_job(upload_id)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def upload(self, r, **attr):
        """
            This will display the upload form
            It will ask for a file to be uploaded or for a job to be selected.

            If a file is uploaded then it will guess at the file type and
            ask for the transform file to be used. The transform files will
            be in a dataTable with the module specific files shown first and
            after those all other known transform files. Once the transform
            file is selected the import process can be started which will
            generate an importJob, and a "POST" method will occur

            If a job is selected it will have two actions, open and delete.
            Open will mean that a "GET" method will occur, with the job details
            passed in.
            Whilst the delete action will trigger a "DELETE" method.
        """

        _debug("S3Importer.upload()")

        request = self.request

        form = self._upload_form(r, **attr)
        output = self._create_upload_dataTable()
        if request.representation == "aadata":
            return output

        output.update(form=form, title=self.uploadTitle)
        return output

    # -------------------------------------------------------------------------
    def generate_job(self, r, **attr):
        """
            Generate an ImportJob from the submitted upload form
        """

        _debug("S3Importer.display()")

        response = current.response
        s3 = response.s3

        db = current.db
        table = self.upload_table
        output = None
        if self.ajax:
            sfilename = ofilename = r.post_vars["file"].filename
            upload_id = table.insert(controller=self.controller,
                                     function=self.function,
                                     filename=ofilename,
                                     file = sfilename,
                                     user_id=current.session.auth.user.id
                                     )
        else:
            title=self.uploadTitle
            form = self._upload_form(r, **attr)

            r = self.request
            r.read_body()
            sfilename = form.vars.file
            try:
                ofilename = r.post_vars["file"].filename
            except:
                form.errors.file = self.messages.no_file

            if form.errors:
                response.flash = ""
                output = self._create_upload_dataTable()
                output.update(form=form, title=title)

            elif not sfilename or \
                 ofilename not in r.files or r.files[ofilename] is None:
                response.flash = ""
                response.error = self.messages.file_not_found
                output = self._create_upload_dataTable()
                output.update(form=form, title=title)
            else:
                query = (table.file == sfilename)
                db(query).update(controller=self.controller,
                                 function=self.function,
                                 filename=ofilename,
                                 user_id=current.session.auth.user.id)
                row = db(query).select(table.id, limitby=(0, 1)).first()
                upload_id = row.id

        if not output:
            output = dict()
            # must commit here to separate this transaction from
            # the trial import phase which will be rolled back.
            db.commit()

            extension = ofilename.rsplit(".", 1).pop()
            if extension not in ("csv", "xls"):
                if self.ajax:
                    return {"Error": self.messages.invalid_file_format}
                response.flash = None
                response.error = self.messages.invalid_file_format
                return self.upload(r, **attr)

            if self.ajax:
                upload_file = r.post_vars.file.file
            else:
                upload_file = r.files[ofilename]
            if extension == "xls":
                if "xls_parser" in s3:
                    upload_file.seek(0)
                    upload_file = s3.xls_parser(upload_file.read())
                    extension = "csv"

            if upload_file is None:
                response.flash = None
                response.error = self.messages.file_not_found
                return self.upload(r, **attr)
            else:
                upload_file.seek(0)

            if "single_pass" in r.vars:
                single_pass = r.vars["single_pass"]
            else:
                single_pass = None
            self._generate_import_job(upload_id,
                                      upload_file,
                                      extension,
                                      commit_job = single_pass)
            if upload_id is None:
                row = db(query).update(status = 2) # in error
                if self.error != None:
                    response.error = self.error
                if self.warning != None:
                    response.warning = self.warning
                response.flash = ""
                return self.upload(r, **attr)
            else:
                if single_pass:
                    current.session.flash = self.messages.file_uploaded
                    # For a single pass retain the vars from the original URL
                    next_URL = URL(r=self.request,
                                   f=self.function,
                                   args=["import"],
                                   vars=current.request.get_vars
                                  )
                    redirect(next_URL)
                s3.dataTable_vars = {"job" : upload_id}
                return self.display_job(upload_id)
        return output

    # -------------------------------------------------------------------------
    def display_job(self, upload_id):
        """
            @todo: docstring?
        """

        _debug("S3Importer.display_job()")

        request = self.request
        response = current.response

        db = current.db
        table = self.upload_table
        job_id = self.job_id
        output = dict()
        if job_id == None:
            # redirect to the start page (removes all vars)
            query = (table.id == upload_id)
            row = db(query).update(status = 2) # in error
            current.session.warning = self.messages.no_records_to_import
            redirect(URL(r=request, f=self.function, args=["import"]))

        # Get the status of the upload job
        query = (table.id == upload_id)
        row = db(query).select(table.status,
                               table.modified_on,
                               table.summary_added,
                               table.summary_error,
                               table.summary_ignored,
                               limitby=(0, 1)).first()
        status = row.status
        # completed display details
        if status == 3: # Completed
            # @todo currently this is an unnecessary server call,
            #       change for completed records to be a display details
            #       and thus avoid the round trip.
            #       but keep this code to protect against hand-crafted URLs
            #       (and the 'go back' syndrome on the browser)
            result = (row.summary_added,
                      row.summary_error,
                      row.summary_ignored,
                     )
            self._display_completed_job(result, row.modified_on)
            redirect(URL(r=request, f=self.function, args=["import"]))
        # otherwise display import items
        response.view = self._view(request, "list.html")

        output = self._create_import_item_dataTable(upload_id, job_id)
        if request.representation == "aadata":
            return output

        if response.s3.error_report:
            error_report = "Errors|" + "|".join(response.s3.error_report)
            error_tip = A("All Errors",
                          _class="errortip",
                          _title=error_report)
        else:
            # @todo: restore the error tree from all items?
            error_tip = ""

        rowcount = len(self._get_all_items(upload_id))
        rheader = DIV(TABLE(
            TR(
                TH("%s: " % self.messages.job_total_records),
                TD(rowcount, _id="totalAvaliable"),
                TH("%s: " % self.messages.job_records_selected),
                TD(0, _id="totalSelected"),
                TH(error_tip)
              ),
        ))

        output["title"] = self.messages.title_job_read
        output["rheader"] = rheader
        output["subtitle"] = self.messages.title_job_list

        return output

    # -------------------------------------------------------------------------
    def commit(self, source, transform):
        """
            @todo: docstring?
        """

        _debug("S3Importer.commit(%s, %s)" % (source, transform))

        db = current.db
        session = current.session
        request = self.request

        try:
            openFile = open(source, "r")
        except:
            session.error = self.messages.file_open_error % source
            redirect(URL(r=request, f=self.function))

        # @todo: manage different file formats
        # @todo: find file format from request.extension
        fileFormat = "csv"

        # Insert data in the table and get the ID
        try:
            user = session.auth.user.id
        except:
            user = None

        upload_id = self.upload_table.insert(controller=self.controller,
                                             function=self.function,
                                             filename = source,
                                             user_id = user,
                                             status = 1)
        db.commit()

        # Create the import job
        result = self._generate_import_job(upload_id,
                                           openFile,
                                           fileFormat,
                                           stylesheet=transform
                                           )
        if result == None:
            if self.error != None:
                if session.error == None:
                    session.error = self.error
                else:
                    session.error += self.error
            if self.warning != None:
                if session.warning == None:
                    session.warning = self.warning
                else:
                    session.warning += self.warning
        else:
            items = self._get_all_items(upload_id, True)
            # Commit the import job
            self._commit_import_job(upload_id, items)
            result = self._update_upload_job(upload_id)

            # Get the results and display
            msg = "%s : %s %s %s" % (source,
                                     self.messages.commit_total_records_imported,
                                     self.messages.commit_total_errors,
                                     self.messages.commit_total_records_ignored)
            msg = msg % result

            if session.flash == None:
                session.flash = msg
            else:
                session.flash += msg

        # @todo: return the upload_id?

    # -------------------------------------------------------------------------
    def commit_items(self, upload_id, items):
        """
            @todo: docstring?
        """

        _debug("S3Importer.commit_items(%s, %s)" % (upload_id, items))
        # Save the import items
        self._commit_import_job(upload_id, items)
        # Update the upload table
        # change the status to completed
        # record the summary details
        # delete the upload file
        result = self._update_upload_job(upload_id)
        if self.ajax:
            return result
        # redirect to the start page (removes all vars)
        self._display_completed_job(result)
        redirect(URL(r=self.request, f=self.function, args=["import"]))

    # -------------------------------------------------------------------------
    def delete_job(self, upload_id):
        """
            Delete an uploaded file and the corresponding import job

            @param upload_id: the upload ID
        """

        _debug("S3Importer.delete_job(%s)" % (upload_id))

        db = current.db

        request = self.request
        resource = request.resource # use self.resource?
        response = current.response

        # Get the import job ID
        job_id = self.job_id

        # Delete the import job (if any)
        if job_id:
            result = resource.import_xml(None,
                                         id = None,
                                         tree = None,
                                         job_id = job_id,
                                         delete_job = True)
        # @todo: check result

        # now delete the upload entry
        query = (self.upload_table.id == upload_id)
        count = db(query).delete()
        # @todo: check that the record has been deleted

        # Now commit the changes
        db.commit()

        result = count

        # return to the main import screen
        # @todo: check result properly
        if result == False:
            response.warning = self.messages.no_job_to_delete
        else:
            response.flash = self.messages.job_deleted

        # redirect to the start page (remove all vars)
        self.next = self.request.url(vars=dict())
        return

    # ========================================================================
    # Utility methods
    # ========================================================================
    def _upload_form(self, r, **attr):
        """
            Create and process the upload form, including csv_extra_fields
        """

        EXTRA_FIELDS = "csv_extra_fields"
        TEMPLATE = "csv_template"
        REPLACE_OPTION = "replace_option"

        response = current.response
        s3 = response.s3
        request = self.request
        table = self.upload_table

        formstyle = s3.crud.formstyle
        response.view = self._view(request, "list_create.html")

        if REPLACE_OPTION in attr:
            replace_option = attr[REPLACE_OPTION]
            if replace_option is not None:
                table.replace_option.readable = True
                table.replace_option.writable = True
                table.replace_option.label = replace_option
                table.replace_option.comment = DIV(_class="tooltip",
                                                   _title="%s|%s" % \
                    (replace_option,
                     current.T("Delete all data of this type which the user has permission to before upload. This is designed for workflows where the data is maintained in an offline spreadsheet and uploaded just for Reads.")))

        fields = [f for f in table if f.readable or f.writable and not f.compute]
        if EXTRA_FIELDS in attr:
            extra_fields = attr[EXTRA_FIELDS]
            if extra_fields is not None:
                fields.extend([f["field"] for f in extra_fields if "field" in f])
            self.csv_extra_fields = extra_fields
        labels, required = s3_mark_required(fields)
        if required:
            s3.has_required = True

        form = SQLFORM.factory(table_name=self.UPLOAD_TABLE_NAME,
                               labels=labels,
                               formstyle=formstyle,
                               upload = os.path.join(request.folder, "uploads", "imports"),
                               separator = "",
                               message=self.messages.file_uploaded,
                               *fields)

        args = ["s3csv"]
        template = attr.get(TEMPLATE, True)
        if template is True:
            args.extend([self.controller, "%s.csv" % self.function])
        elif isinstance(template, basestring):
            args.extend([self.controller, "%s.csv" % template])
        elif isinstance(template, (tuple, list)):
            args.extend(template[:-1])
            args.append("%s.csv" % template[-1])
        else:
            template = None
        if template is not None:
            url = URL(r=request, c="static", f="formats", args=args)
            try:
                # only add the download link if the template can be opened
                open("%s/../%s" % (r.folder, url))
                form[0][0].insert(0, TR(TD(A(self.messages.download_template,
                                             _href=url)),
                                        _id="template__row"))
            except:
                pass

        if form.accepts(r.post_vars, current.session,
                        formname="upload_form"):
            upload_id = table.insert(**table._filter_fields(form.vars))
            if self.csv_extra_fields:
                self.csv_extra_data = Storage()
                for f in self.csv_extra_fields:
                    label = f.get("label", None)
                    if not label:
                        continue
                    field = f.get("field", None)
                    value = f.get("value", None)
                    if field:
                        if field.name in form.vars:
                            data = form.vars[field.name]
                        else:
                            data = field.default
                        value = data
                        requires = field.requires
                        if not isinstance(requires, (list, tuple)):
                            requires = [requires]
                        if requires:
                            requires = requires[0]
                            if isinstance(requires, IS_EMPTY_OR):
                                requires = requires.other
                            try:
                                options = requires.options()
                            except:
                                pass
                            else:
                                for k, v in options:
                                    if k == str(data):
                                        value = v
                    elif value is None:
                        continue
                    self.csv_extra_data[label] = value
        s3.no_formats = True
        return form

    # -------------------------------------------------------------------------
    def _create_upload_dataTable(self):
        """
            List of previous Import jobs
        """

        db = current.db
        request = self.request
        controller = self.controller
        function = self.function
        s3 = current.response.s3

        table = self.upload_table
        s3.filter = (table.controller == controller) & \
                    (table.function == function)
        fields = ["id",
                  "filename",
                  "created_on",
                  "user_id",
                  "replace_option",
                  "status"]

        self._use_upload_table()

        # Hide the list of prior uploads for now
        #output = self._dataTable(fields, sort_by = [[2,"desc"]])
        output = dict()

        self._use_controller_table()

        if request.representation == "aadata":
            return output

        query = (table.status != 3) # Status of Pending or in-Error
        rows = db(query).select(table.id)
        restrictOpen = [str(row.id) for row in rows]
        query = (table.status == 3) # Status of Completed
        rows = db(query).select(table.id)
        restrictView = [str(row.id) for row in rows]

        s3.actions = [
                    dict(label=str(self.messages.open_btn),
                         _class="action-btn",
                         url=URL(r=request,
                                 c=controller,
                                 f=function,
                                 args=["import"],
                                 vars={"job":"[id]"}),
                         restrict = restrictOpen

                         ),
                    dict(label=str(self.messages.view_btn),
                         _class="action-btn",
                         url=URL(r=request,
                                 c=controller,
                                 f=function,
                                 args=["import"],
                                 vars={"job":"[id]"}),
                         restrict = restrictView
                         ),
                    dict(label=str(self.messages.delete_btn),
                         _class="delete-btn",
                         url=URL(r=request,
                                 c=controller,
                                 f=function,
                                 args=["import"],
                                 vars={"job":"[id]",
                                       "delete":"True"
                                      }
                                )
                         ),
                  ]
        # Display an Error if no job is attached with this record
        query = (table.status == 1) # Pending
        rows = db(query).select(table.id)
        s3.dataTableStyleAlert = [str(row.id) for row in rows]
        query = (table.status == 2) # in error
        rows = db(query).select(table.id)
        s3.dataTableStyleWarning = [str(row.id) for row in rows]

        return output

    # -------------------------------------------------------------------------
    def _create_import_item_dataTable(self, upload_id, job_id):
        """
            @todo: docstring?
        """

        s3 = current.response.s3
        T = current.T

        represent = {"s3_import_item.element" : self._item_element_represent}
        self._use_import_item_table(job_id)

        # Add a filter to the dataTable query
        s3.filter = (self.table.job_id == job_id) & \
                    (self.table.tablename == self.controller_tablename)

        # Get a list of the records that have an error of None
        query =  (self.table.job_id == job_id) & \
                 (self.table.tablename == self.controller_tablename)
        rows = current.db(query).select(self.table.id, self.table.error)
        select_list = []
        error_list = []
        for row in rows:
            if row.error:
                error_list.append(str(row.id))
            else:
                select_list.append("%s" % row.id)

        # Experimental uploading via ajax - added for vulnerability
        if self.ajax:
            resource = self.resource
            resource.add_filter(s3.filter)
            rows = resource.select(["id", "element", "error"],
                                   start=0,
                                   limit=resource.count(),
                                   )
            data = resource.extract(rows,
                                    ["id", "element", "error"],
                                    )
            return (upload_id, select_list, data)

        s3.actions = [
                        dict(label= str(self.messages.item_show_details),
                             _class="action-btn",
                             _jqclick="$('.importItem.'+id).toggle();",
                             ),
                      ]
        output = self._dataTable(["id", "element", "error"],
                                 sort_by = [[1, "asc"]],
                                 represent=represent,
                                 ajax_item_id=upload_id,
                                 dt_bulk_select = select_list)

        self._use_controller_table()

        if self.request.representation == "aadata":
            return output

        # Highlight rows in error in red
        s3.dataTableStyleWarning = error_list

        form = output["items"]
        job = INPUT(_type="hidden", _id="importUploadID", _name="job",
                    _value="%s" % upload_id)
        form.append(job)
        return output

    # -------------------------------------------------------------------------
    def _generate_import_job(self,
                             upload_id,
                             openFile,
                             fileFormat,
                             stylesheet=None,
                             commit_job=False):
        """
            This will take a s3_import_upload record and
            generate the importJob

            @param uploadFilename: The name of the uploaded file

            @todo: complete parameter descriptions
        """

        _debug("S3Importer._generate_import_job(%s, %s, %s, %s)" % (upload_id,
                                                                    openFile,
                                                                    fileFormat,
                                                                    stylesheet
                                                                    )
              )

        # ---------------------------------------------------------------------
        # CSV
        if fileFormat == "csv" or fileFormat == "comma-separated-values":

            fmt = "csv"
            src = openFile

        # ---------------------------------------------------------------------
        # XML
        # @todo: implement
        #elif fileFormat == "xml":

        # ---------------------------------------------------------------------
        # S3JSON
        # @todo: implement
        #elif fileFormat == "s3json":

        # ---------------------------------------------------------------------
        # PDF
        # @todo: implement
        #elif fileFormat == "pdf":

        # ---------------------------------------------------------------------
        # Unsupported Format
        else:
            msg = self.messages.unsupported_file_type % fileFormat
            self.error = msg
            _debug(msg)
            return None

        # Get the stylesheet
        if stylesheet == None:
            stylesheet = self._get_stylesheet()
        if stylesheet == None:
            return None

        request = self.request
        resource = request.resource

        # Before calling import tree ensure the db.table is the controller_table
        self.table = self.controller_table
        self.tablename = self.controller_tablename

        # Pass stylesheet arguments
        args = Storage()
        mode = request.get_vars.get("xsltmode", None)
        if mode is not None:
            args.update(mode=mode)

        # Generate the import job
        resource.import_xml(src,
                            format=fmt,
                            extra_data=self.csv_extra_data,
                            stylesheet=stylesheet,
                            ignore_errors = True,
                            commit_job = commit_job,
                            **args)

        job = resource.job
        if job is None:
            if resource.error:
                # Error
                self.error = resource.error
                return None
            else:
                # Nothing to import
                self.warning = self.messages.no_records_to_import
                return None
        else:
            # Job created
            db = current.db
            job_id = job.job_id
            errors = current.xml.collect_errors(job)
            if errors:
                current.response.s3.error_report = errors
            query = (self.upload_table.id == upload_id)
            result = db(query).update(job_id=job_id)
            # @todo: add check that result == 1, if not we are in error
            # Now commit the changes
            db.commit()

        self.job_id = job_id
        return True

    # -------------------------------------------------------------------------
    def _get_stylesheet(self, file_format="csv"):
        """
            Get the stylesheet for transformation of the import

            @param file_format: the import source file format
        """

        if file_format == "csv":
            xslt_path = os.path.join(self.xslt_path, "s3csv")
        else:
            xslt_path = os.path.join(self.xslt_path, file_format, "import.xsl")
            return xslt_path

        # Use the "csv_stylesheet" parameter to override the CSV stylesheet subpath
        # and filename, e.g.
        #       s3_rest_controller(module, resourcename,
        #                          csv_stylesheet=("inv", "inv_item.xsl"))
        if self.csv_stylesheet:
            if isinstance(self.csv_stylesheet, (tuple, list)):
                stylesheet = os.path.join(xslt_path,
                                          *self.csv_stylesheet)
            else:
                stylesheet = os.path.join(xslt_path,
                                          self.controller,
                                          self.csv_stylesheet)
        else:
            xslt_filename = "%s.%s" % (self.function, self.xslt_extension)
            stylesheet = os.path.join(xslt_path,
                                      self.controller,
                                      xslt_filename)

        if os.path.exists(stylesheet) is False:
            msg = self.messages.stylesheet_not_found % stylesheet
            self.error = msg
            _debug(msg)
            return None

        return stylesheet

    # -------------------------------------------------------------------------
    def _commit_import_job(self, upload_id, items):
        """
            This will save all of the selected import items

            @todo: parameter descriptions?
        """

        _debug("S3Importer._commit_import_job(%s, %s)" % (upload_id, items))

        db = current.db
        resource = self.request.resource

        # Load the items from the s3_import_item table
        self.importDetails = dict()

        table = self.upload_table
        query = (table.id == upload_id)
        row = db(query).select(table.job_id,
                               table.replace_option,
                               limitby=(0, 1)).first()
        if row is None:
            return False
        else:
            job_id = row.job_id
            current.response.s3.import_replace = row.replace_option

        itemTable = S3ImportJob.define_item_table()

        if itemTable != None:
            #****************************************************************
            # EXPERIMENTAL
            # This doesn't delete related items
            # but import_tree will tidy it up later
            #****************************************************************
            # Get all the items selected for import
            rows = self._get_all_items(upload_id, as_string=True)

            # Loop through each row and delete the items not required
            self._store_import_details(job_id, "preDelete")
            for id in rows:
                if str(id) not in items:
                    # @todo: replace with a helper method from the API
                    _debug("Deleting item.id = %s" % id)
                    query = (itemTable.id == id)
                    db(query).delete()

            #****************************************************************
            # EXPERIMENTAL
            #****************************************************************

            # Set up the table we will import data into
            self.table = self.controller_table
            self.tablename = self.controller_tablename

            self._store_import_details(job_id, "preImportTree")

            # Now commit the remaining items
            msg = resource.import_xml(None,
                                      job_id = job_id,
                                      ignore_errors = True)
            return resource.error is None

    # -------------------------------------------------------------------------
    def _store_import_details(self, job_id, key):
        """
            This will store the details from an importJob

            @todo: parameter descriptions?
        """

        _debug("S3Importer._store_import_details(%s, %s)" % (job_id, key))

        itemTable = S3ImportJob.define_item_table()

        query = (itemTable.job_id == job_id)  & \
                (itemTable.tablename == self.controller_tablename)
        rows = current.db(query).select(itemTable.data, itemTable.error)
        items = [dict(data=row.data, error=row.error) for row in rows]

        self.importDetails[key] = items

    # -------------------------------------------------------------------------
    def _update_upload_job(self, upload_id):
        """
            This will record the results from the import, and change the
            status of the upload job

            @todo: parameter descriptions?
            @todo: report errors in referenced records, too
        """

        _debug("S3Importer._update_upload_job(%s)" % (upload_id))

        request = self.request
        resource = request.resource
        db = current.db

        totalPreDelete = len(self.importDetails["preDelete"])
        totalPreImport = len(self.importDetails["preImportTree"])
        totalIgnored = totalPreDelete - totalPreImport

        if resource.error_tree is None:
            totalErrors = 0
        else:
            totalErrors = len(resource.error_tree.findall(
                            "resource[@name='%s']" % resource.tablename))

        totalRecords = totalPreImport - totalErrors
        if totalRecords < 0:
            totalRecords = 0

        query = (self.upload_table.id == upload_id)
        result = db(query).update(summary_added=totalRecords,
                                  summary_error=totalErrors,
                                  summary_ignored = totalIgnored,
                                  status = 3)

        # Now commit the changes
        db.commit()
        return (totalRecords, totalErrors, totalIgnored)

    # -------------------------------------------------------------------------
    def _display_completed_job(self, totals, timestmp=None):
        """
            Generate a summary flash message for a completed import job

            @param totals: the job totals as tuple
                           (total imported, total errors, total ignored)
            @param timestmp: the timestamp of the completion
        """

        session = current.session

        msg = "%s - %s - %s" % \
              (self.messages.commit_total_records_imported,
               self.messages.commit_total_errors,
               self.messages.commit_total_records_ignored)
        msg = msg % totals

        if timestmp != None:
            session.flash = self.messages.job_completed % \
                            (self.date_represent(timestmp), msg)
        elif totals[1] is not 0:
            session.error = msg
        elif totals[2] is not 0:
            session.warning = msg
        else:
            session.flash = msg

    # -------------------------------------------------------------------------
    def _dataTable(self,
                   list_fields,
                   sort_by = [[1, "asc"]],
                   represent={},
                   ajax_item_id=None,
                   dt_bulk_select=[],
                  ):
        """
            Method to get the data for the dataTable
            This can be either a raw html representation or
            and ajax call update
            Additional data will be cached to limit calls back to the server

            @param list_fields: list of field names
            @param sort_by: list of sort by columns
            @param represent: a dict of field callback functions used
                              to change how the data will be displayed
                              keyed on the field identifier

            @return: a dict()
               In html representations this will be a table of the data
               plus the sortby instructions
               In ajax this will be a json response

               In addition the following values will be made available:
               totalRecords         Number of records in the filtered data set
               totalDisplayRecords  Number of records to display
               start                Start point in the ordered data set
               limit                Number of records in the ordered set
               NOTE: limit - totalDisplayRecords = total cached
        """

        from s3.s3utils import S3DataTable
        request = self.request
        resource = self.resource
        s3 = current.response.s3
        # Filter
        if s3.filter is not None:
            self.resource.add_filter(s3.filter)

        representation = self.request.representation
        if representation == "aadata":
            vars = request.get_vars
            start = vars.get("iDisplayStart", None)
            limit = vars.get("iDisplayLength", None)
            sEcho = int(vars.sEcho or 0)
        else: # catch all
            start = 0
            limit = current.manager.ROWSPERPAGE
        if limit is not None:
            try:
                start = int(start)
                limit = int(limit)
            except ValueError:
                start = None
                limit = None # use default
        else:
            start = None # use default
        rows = resource.select(list_fields,
                               start=start,
                               limit=limit,
                               )
        data = resource.extract(rows,
                                list_fields,
                                )

        # put each value through the represent function
        for row in data:
            for (key, value) in row.items():
                if key in represent:
                    row[key] = represent[key](row["s3_import_item.id"], value);
        rfields = resource.resolve_selectors(list_fields)[0]
        dt = S3DataTable(rfields, data)
        id = "s3import_1"
        if representation == "aadata":
            totalrows = self.resource.count()
            return dt.json(totalrows,
                           totalrows,
                           id,
                           sEcho,
                           dt_bulk_actions = [current.T("Import")],
                           )
        else:
            output = dict()
            url = "/%s/%s/%s/import.aadata?job=%s" % (request.application,
                                                      request.controller,
                                                      request.function,
                                                      ajax_item_id
                                                      )
            totalrows = self.resource.count()
            items =  dt.html(totalrows,
                             totalrows,
                             id,
                             dt_ajax_url=url,
                             dt_bulk_actions = [current.T("Import")],
                             dt_bulk_selected = dt_bulk_select,
                             )
            current.response.s3.dataTableID = ["s3import_1"]
            output.update(items=items)
            return output

    # -------------------------------------------------------------------------
    def _item_element_represent(self, id, value):
        """
            Represent the element in an import item for dataTable display

            @param value: the string containing the element
        """

        T = current.T
        db = current.db

        value = S3XML.xml_decode(value)
        try:
            element = etree.fromstring(value)
        except:
            # XMLSyntaxError: return the element as-is
            return DIV(value)

        tablename = element.get("name")
        table = current.db[tablename]

        output = DIV()
        details = TABLE(_class="importItem %s" % id)
        header, rows = self._add_item_details(element.findall("data"), table)
        if header is not None:
            output.append(header)
        # Add components, if present
        components = element.findall("resource")
        for component in components:
            ctablename = component.get("name")
            ctable = db[ctablename]
            self._add_item_details(component.findall("data"), ctable,
                                   details=rows, prefix=True)
        if rows:
            details.append(TBODY(rows))
        # Add error messages, if present
        errors = current.xml.collect_errors(element)
        if errors:
            details.append(TFOOT(TR(TH("%s:" % T("Errors")),
                                   TD(UL([LI(e) for e in errors])))))
        if rows == [] and components == []:
            # At this stage we don't have anything to display to see if we can
            # find something to show. This could be the case when a table being
            # imported is a resolver for a many to many relationship
            refdetail = TABLE(_class="importItem %s" % id)
            references = element.findall("reference")
            for reference in references:
                tuid = reference.get("tuid")
                resource = reference.get("resource")
                refdetail.append(TR(TD(resource), TD(tuid)))
            output.append(refdetail)
        else:
            output.append(details)
        return str(output)

    # -------------------------------------------------------------------------
    @staticmethod
    def _add_item_details(data, table, details=None, prefix=False):
        """
            Add details of the item element

            @param data: the list of data elements in the item element
            @param table: the table for the data
            @param details: the existing details rows list (to append to)
        """

        tablename = table._tablename
        if details is None:
            details = []
        first = None
        firstString = None
        header = None
        for child in data:
            f = child.get("field", None)
            if f not in table.fields:
                continue
            elif f == "wkt":
                # Skip bulky WKT fields
                continue
            field = table[f]
            ftype = str(field.type)
            value = child.get("value", None)
            if not value:
                value = child.text
            try:
                value = S3Importer._decode_data(field, value)
            except:
                pass
            if value:
                value = S3XML.xml_encode(unicode(value))
            else:
                value = ""
            if f != None and value != None:
                headerText = P(B("%s: " % f), value)
                if not first:
                    first = headerText
                if ftype == "string" and not firstString:
                    firstString = headerText
                if f == "name":
                    header = headerText
                if prefix:
                    details.append(TR(TH("%s.%s:" % (tablename, f)), TD(value)))
                else:
                    details.append(TR(TH("%s:" % f), TD(value)))
        if not header:
            if firstString:
                header = firstString
            else:
                header = first
        return (header, details)

    # -------------------------------------------------------------------------
    @staticmethod
    def _decode_data(field, value):
        """
            Try to decode string data into their original type

            @param field: the Field instance
            @param value: the stringified value

            @todo: replace this by ordinary decoder
        """

        if field.type == "string" or \
            field.type == "string" or  \
            field.type == "password" or \
            field.type == "upload" or \
            field.type == "text":
            return value
        elif field.type == "integer" or field.type == "id":
            return int(value)
        elif field.type == "double" or field.type == "decimal":
            return double(value)
        elif  field.type == 'boolean':
            if value and not str(value)[:1].upper() in ["F", "0"]:
                return "T"
            else:
                return "F"
        elif field.type == "date":
            return value # @todo fix this to get a date
        elif field.type == "time":
            return value # @todo fix this to get a time
        elif field.type == "datetime":
            return value # @todo fix this to get a datetime
        else:
            return value

    # -------------------------------------------------------------------------
    @staticmethod
    def date_represent(date_obj):
        """
            Represent a datetime object as string

            @param date_obj: the datetime object

            @todo: replace by S3DateTime method?
        """
        return date_obj.strftime("%d %B %Y, %I:%M%p")

    # -------------------------------------------------------------------------
    def _process_item_list(self, upload_id, vars):
        """
            Get the list of IDs for the selected items from the "mode"
            and "selected" request variables

            @param upload_id: the upload_id
            @param vars: the request variables
        """

        items = None
        if "mode" in vars:
            mode = vars["mode"]
            if "selected" in vars:
                selected = vars["selected"]
            else:
                selected = []
            if mode == "Inclusive":
                items = selected
            elif mode == "Exclusive":
                all_items = self._get_all_items(upload_id, as_string=True)
                items = [i for i in all_items if i not in selected]
        return items

    # -------------------------------------------------------------------------
    def _get_all_items(self, upload_id, as_string=False):
        """
            Get a list of the record IDs of all import items for
            the the given upload ID

            @param upload_id: the upload ID
            @param as_string: represent each ID as string
        """

        item_table = S3ImportJob.define_item_table()
        upload_table = self.upload_table

        query = (upload_table.id == upload_id) & \
                (item_table.job_id == upload_table.job_id) & \
                (item_table.tablename == self.controller_tablename)

        rows = current.db(query).select(item_table.id)
        if as_string:
            items = [str(row.id) for row in rows]
        else:
            items = [row.id for row in rows]

        return items

    # -------------------------------------------------------------------------
    def _use_upload_table(self):
        """
            Set the resource and the table to being s3_import_upload
        """

        self.tablename = self.upload_tablename
        if self.upload_resource == None:
            self.upload_resource = current.s3db.resource(self.tablename)
        self.resource = self.upload_resource
        self.table = self.upload_table

    # -------------------------------------------------------------------------
    def _use_controller_table(self):
        """
            Set the resource and the table to be the imported resource
        """

        self.resource = self.controller_resource
        self.table = self.controller_table
        self.tablename = self.controller_tablename

    # -------------------------------------------------------------------------
    def _use_import_item_table(self, job_id):
        """
            Set the resource and the table to being s3_import_item
        """
        self.table = S3ImportJob.define_item_table()
        self.tablename = S3ImportJob.ITEM_TABLE_NAME
        if self.item_resource == None:
            self.item_resource = current.s3db.resource(self.tablename)
        self.resource = self.item_resource

    # -------------------------------------------------------------------------
    def __define_table(self):
        """ Configures the upload table """

        _debug("S3Importer.__define_table()")

        T = current.T
        db = current.db
        request = current.request

        self.upload_tablename = self.UPLOAD_TABLE_NAME

        import_upload_status = {
            1: T("Pending"),
            2: T("In error"),
            3: T("Completed"),
        }

        def user_name_represent(id):
            # @todo: use s3_represent_user?

            table = db.auth_user
            query = (table.id == id)
            row = db(query).select(table.first_name,
                                   table.last_name,
                                   limitby=(0, 1)).first()
            if row:
                rep_str = "%s %s" % (row.first_name, row.last_name)
            else:
                rep_str = current.messages.NONE

            return rep_str

        def status_represent(index):
            if index == None:
                return "Unknown" # @todo: use messages (internationalize)
            else:
                return import_upload_status[index]

        now = request.utcnow
        table = self.define_upload_table()
        table.file.upload_folder = os.path.join(request.folder,
                                                "uploads",
                                                #"imports"
                                                )
        table.file.comment = DIV(_class="tooltip",
                                 _title="%s|%s" %
                                    (self.messages.import_file,
                                     self.messages.import_file_comment))
        table.file.label = self.messages.import_file
        table.status.requires = IS_IN_SET(import_upload_status, zero=None)
        table.status.represent = status_represent
        table.user_id.label = self.messages.user_name
        table.user_id.represent = user_name_represent
        table.created_on.default = now
        table.created_on.represent = self.date_represent
        table.modified_on.default = now
        table.modified_on.update = now
        table.modified_on.represent = self.date_represent

        table.replace_option.label = T("Replace")

        self.upload_table = db[self.UPLOAD_TABLE_NAME]

    # -------------------------------------------------------------------------
    @classmethod
    def define_upload_table(cls):
        """ Defines the upload table """

        db = current.db
        if cls.UPLOAD_TABLE_NAME not in db:
            upload_table = db.define_table(cls.UPLOAD_TABLE_NAME,
                    Field("controller",
                          readable=False,
                          writable=False),
                    Field("function",
                          readable=False,
                          writable=False),
                    Field("file", "upload",
                          uploadfolder=os.path.join(current.request.folder,
                                                    "uploads", "imports"),
                          autodelete=True),
                    Field("filename",
                          readable=False,
                          writable=False),
                    Field("status", "integer",
                          default=1,
                          readable=False,
                          writable=False),
                    Field("extra_data",
                          readable=False,
                          writable=False),
                    Field("replace_option", "boolean",
                          default=False,
                          readable=False,
                          writable=False),
                    Field("job_id",
                          length=128,
                          readable=False,
                          writable=False),
                    Field("user_id", "integer",
                          readable=False,
                          writable=False),
                    Field("created_on", "datetime",
                          readable=False,
                          writable=False),
                    Field("modified_on", "datetime",
                          readable=False,
                          writable=False),
                    Field("summary_added", "integer",
                          readable=False,
                          writable=False),
                    Field("summary_error", "integer",
                          readable=False,
                          writable=False),
                    Field("summary_ignored", "integer",
                          readable=False,
                          writable=False),
                    Field("completed_details", "text",
                          readable=False,
                          writable=False))
        else:
            upload_table = db[cls.UPLOAD_TABLE_NAME]

        return upload_table

# =============================================================================
class S3ImportItem(object):
    """ Class representing an import item (=a single record) """

    METHOD = Storage(
        CREATE="create",
        UPDATE="update",
        DELETE="delete"
    )

    POLICY = Storage(
        THIS="THIS",                # keep local instance
        OTHER="OTHER",              # update unconditionally
        NEWER="NEWER",              # update if import is newer
        MASTER="MASTER"             # update if import is master
    )

    # -------------------------------------------------------------------------
    def __init__(self, job):
        """
            Constructor

            @param job: the import job this item belongs to
        """

        self.job = job
        self.ERROR = current.manager.ERROR

        # Locking and error handling
        self.lock = False
        self.error = None

        # Identification
        import uuid
        self.item_id = uuid.uuid4() # unique ID for this item
        self.id = None
        self.uid = None

        # Data elements
        self.table = None
        self.tablename = None
        self.element = None
        self.data = None
        self.original = None
        self.components = []
        self.references = []
        self.load_components = []
        self.load_references = []
        self.parent = None
        self.skip = False

        # Conflict handling
        self.mci = 2
        self.mtime = datetime.utcnow()
        self.modified = True
        self.conflict = False

        # Allowed import methods
        self.strategy = job.strategy
        # Update and conflict resolution policies
        self.update_policy = job.update_policy
        self.conflict_policy = job.conflict_policy

        # Actual import method
        self.method = None

        self.onvalidation = None
        self.onaccept = None

        # Item import status flags
        self.accepted = None
        self.permitted = False
        self.committed = False

        # Writeback hook for circular references:
        # Items which need a second write to update references
        self.update = []

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ Helper method for debugging """

        _str = "<S3ImportItem %s {item_id=%s uid=%s id=%s error=%s data=%s}>" % \
               (self.table, self.item_id, self.uid, self.id, self.error, self.data)
        return _str

    # -------------------------------------------------------------------------
    def parse(self,
              element,
              original=None,
              table=None,
              tree=None,
              files=None):
        """
            Read data from a <resource> element

            @param element: the element
            @param table: the DB table
            @param tree: the import tree
            @param files: uploaded files

            @returns: True if successful, False if not (sets self.error)
        """

        db = current.db
        xml = current.xml
        manager = current.manager
        validate = manager.validate
        s3db = current.s3db

        self.element = element
        if table is None:
            tablename = element.get(xml.ATTRIBUTE.name, None)
            try:
                table = s3db[tablename]
            except:
                self.error = self.ERROR.BAD_RESOURCE
                element.set(xml.ATTRIBUTE.error, self.error)
                return False

        self.table = table
        self.tablename = table._tablename

        if original is None:
            original = S3Resource.original(table, element)
        data = xml.record(table, element,
                          files=files,
                          original=original,
                          validate=validate)

        if data is None:
            self.error = self.ERROR.VALIDATION_ERROR
            self.accepted = False
            if not element.get(xml.ATTRIBUTE.error, False):
                element.set(xml.ATTRIBUTE.error, str(self.error))
            return False

        self.data = data

        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            if xml.UID in original:
                self.uid = original[xml.UID]
                self.data.update({xml.UID:self.uid})
        elif xml.UID in data:
            self.uid = data[xml.UID]
        if xml.MTIME in data:
            self.mtime = data[xml.MTIME]
        if xml.MCI in data:
            self.mci = data[xml.MCI]

        _debug("New item: %s" % self)
        return True

    # -------------------------------------------------------------------------
    def deduplicate(self):
        """
            Detect whether this is an update or a new record
        """

        RESOLVER = "deduplicate"

        if self.id:
            return

        table = self.table

        if table is None:
            return
        if self.original is not None:
            original = self.original
        else:
            original = S3Resource.original(table, self.data)

        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            UID = current.xml.UID
            if UID in original:
                self.uid = original[UID]
                self.data.update({UID:self.uid})
            self.method = self.METHOD.UPDATE
        else:
            resolve = current.s3db.get_config(self.tablename, RESOLVER)
            if self.data and resolve:
                resolve(self)

        return

    # -------------------------------------------------------------------------
    def authorize(self):
        """
            Authorize the import of this item, sets self.permitted
        """

        if not self.table:
            return False

        prefix = self.tablename.split("_", 1)[0]
        if prefix in current.manager.PROTECTED:
            return False

        # Determine the method
        self.method = self.METHOD.CREATE
        if self.id:

            if self.data.deleted is True:
                self.method = self.METHOD.DELETE
                self.accepted = True

            else:
                if not self.original:
                    query = (self.table.id == self.id)
                    self.original = current.db(query).select(limitby=(0, 1)).first()
                if self.original:
                    self.method = self.METHOD.UPDATE

        # Set self.id
        if self.method == self.METHOD.CREATE:
            self.id = 0

        # Authorization
        authorize = current.auth.s3_has_permission
        if authorize:
            self.permitted = authorize(self.method,
                                       self.tablename,
                                       record_id=self.id)
        else:
            self.permitted = True

        return self.permitted

    # -------------------------------------------------------------------------
    def validate(self):
        """
            Validate this item (=record onvalidation), sets self.accepted
        """

        if self.accepted is not None:
            return self.accepted
        if self.data is None or not self.table:
            self.accepted = False
            return False

        form = Storage(method = self.method,
                       vars = self.data,
                       request_vars = self.data)

        if self.id:
            form.vars.id = self.id

        form.errors = Storage()
        tablename = self.tablename
        key = "%s_onvalidation" % self.method
        s3db = current.s3db
        onvalidation = s3db.get_config(tablename, key,
                       s3db.get_config(tablename, "onvalidation"))
        if onvalidation:
            try:
                callback(onvalidation, form, tablename=tablename)
            except:
                pass # @todo need a better handler here.
        self.accepted = True
        if form.errors:
            error = current.xml.ATTRIBUTE.error
            for k in form.errors:
                e = self.element.findall("data[@field='%s']" % k)
                if not e:
                    e = self.element.findall("reference[@field='%s']" % k)
                if not e:
                    e = self.element
                    form.errors[k] = "[%s] %s" % (k, form.errors[k])
                else:
                    e = e[0]
                e.set(error,
                      str(form.errors[k]).decode("utf-8"))
            self.error = self.ERROR.VALIDATION_ERROR
            self.accepted = False
        return self.accepted

    # -------------------------------------------------------------------------
    def commit(self, ignore_errors=False):
        """
            Commit this item to the database

            @param ignore_errors: skip invalid components
                                  (still reports errors)
        """

        # Check if already committed
        if self.committed:
            # already committed
            return True

        # If the parent item gets skipped, then skip this item as well
        if self.parent is not None and self.parent.skip:
            return True

        _debug("Committing item %s" % self)

        METHOD = self.METHOD
        POLICY = self.POLICY

        db = current.db
        s3db = current.s3db
        xml = current.xml
        manager = current.manager
        table = self.table

        # Resolve references
        self._resolve_references()

        # Set a flag so that we know this is an import job
        current.response.s3.bulk = True

        # Validate
        if not self.validate():
            _debug("Validation error: %s (%s)" % (self.error, xml.tostring(self.element, pretty_print=True)))
            self.skip = True
            return ignore_errors

        elif self.components:
            for component in self.components:
                if not component.validate():
                    if hasattr(component, "tablename"):
                        tn = component.tablename
                    else:
                        tn = None
                    _debug("Validation error, component=%s" % tn)
                    component.skip = True
                    # Skip this item on any component validation errors
                    # unless ignore_errors is True
                    if ignore_errors:
                        continue
                    else:
                        self.skip = True
                        return False

        # De-duplicate
        self.deduplicate()

        # Log this item
        if manager.log is not None:
            manager.log(self)

        # Authorize item
        if not self.authorize():
            _debug("Not authorized - skip")
            self.error = manager.ERROR.NOT_PERMITTED
            self.skip = True
            return ignore_errors

        method = self.method
        _debug("Method: %s" % method)

        # Check if import method is allowed in strategy
        if not isinstance(self.strategy, (list, tuple)):
            self.strategy = [self.strategy]
        if method not in self.strategy:
            _debug("Method not in strategy - skip")
            self.error = manager.ERROR.NOT_PERMITTED
            self.skip = True
            return True

        this = self.original
        if not this and self.id and \
           method in (METHOD.UPDATE, METHOD.DELETE):
            query = (table.id == self.id)
            this = db(query).select(limitby=(0, 1)).first()
        this_mtime = None
        this_mci = 0
        if this:
            if xml.MTIME in table.fields:
                this_mtime = xml.as_utc(this[xml.MTIME])
            if xml.MCI in table.fields:
                this_mci = this[xml.MCI]
        self.mtime = xml.as_utc(self.mtime)

        # Conflict detection
        this_modified = True
        self.modified = True
        self.conflict = False
        last_sync = xml.as_utc(self.job.last_sync)
        if last_sync:
            if this_mtime and this_mtime < last_sync:
                this_modified = False
            if self.mtime and self.mtime < last_sync:
                self.modified = False
            if self.modified and this_modified:
                self.conflict = True

        if self.conflict and \
           method in (METHOD.UPDATE, METHOD.DELETE):
            _debug("Conflict: %s" % self)
            if self.job.onconflict:
                self.job.onconflict(self)

        if self.data is not None:
            data = Storage(self.data)
        else:
            data = Storage()

        if isinstance(self.update_policy, dict):
            def update_policy(f):
                setting = self.update_policy
                p = setting.get(f,
                    setting.get("__default__", POLICY.THIS))
                if p not in POLICY:
                    return POLICY.THIS
                return p
        else:
            def update_policy(f):
                p = self.update_policy
                if p not in POLICY:
                    return POLICY.THIS
                return p

        # Update existing record
        if method == METHOD.UPDATE:

            if this:
                if "deleted" in this and this.deleted:
                    policy = update_policy(None)
                    if policy == POLICY.NEWER and \
                       this_mtime and this_mtime > self.mtime or \
                       policy == POLICY.MASTER and \
                       (this_mci == 0 or self.mci != 1):
                        self.skip = True
                        return True
                fields = data.keys()
                for f in fields:
                    if f not in this:
                        continue
                    if isinstance(this[f], datetime):
                        if xml.as_utc(data[f]) == xml.as_utc(this[f]):
                            del data[f]
                            continue
                    else:
                        if data[f] == this[f]:
                            del data[f]
                            continue
                    remove = False
                    policy = update_policy(f)
                    if policy == POLICY.THIS:
                        remove = True
                    elif policy == POLICY.NEWER:
                        if this_mtime and this_mtime > self.mtime:
                            remove = True
                    elif policy == POLICY.MASTER:
                        if this_mci == 0 or self.mci != 1:
                            remove = True
                    if remove:
                        del data[f]
                        self.data.update({f:this[f]})
                if "deleted" in this and this.deleted:
                    # Undelete re-imported records:
                    data.update(deleted=False)
                    if "deleted_fk" in table:
                        data.update(deleted_fk="")
                    if "created_by" in table:
                        data.update(created_by=table.created_by.default)
                    if "modified_by" in table:
                        data.update(modified_by=table.modified_by.default)

            if not self.skip and not self.conflict and \
               (len(data) or self.components or self.references):
                if self.uid and xml.UID in table:
                    data.update({xml.UID:self.uid})
                if xml.MTIME in table:
                    data.update({xml.MTIME: self.mtime})
                if xml.MCI in data:
                    # retain local MCI on updates
                    del data[xml.MCI]
                query = (table._id == self.id)
                try:
                    success = db(query).update(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return False
                if success:
                    self.committed = True
            else:
                # Nothing to update
                self.committed = True

        # Create new record
        elif method == METHOD.CREATE:

            # Do not apply field policy to UID and MCI
            UID = xml.UID
            if UID in data:
                del data[UID]
            MCI = xml.MCI
            if MCI in data:
                del data[MCI]

            for f in data:
                policy = update_policy(f)
                if policy == POLICY.MASTER and self.mci != 1:
                    del data[f]

            if len(data) or self.components or self.references:

                # Restore UID and MCI
                if self.uid and UID in table.fields:
                    data.update({UID:self.uid})
                if MCI in table.fields:
                    data.update({MCI:self.mci})

                # Insert the new record
                try:
                    success = table.insert(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return False
                if success:
                    self.id = success
                    self.committed = True

            else:
                # Nothing to create
                self.skip = True
                return True

        # Delete local record
        elif method == METHOD.DELETE:

            if this:
                if this.deleted:
                    self.skip = True
                policy = update_policy(None)
                if policy == POLICY.THIS:
                    self.skip = True
                elif policy == POLICY.NEWER and \
                     (this_mtime and this_mtime > self.mtime):
                    self.skip = True
                elif policy == POLICY.MASTER and \
                     (this_mci == 0 or self.mci != 1):
                    self.skip = True
            else:
                self.skip = True

            if not self.skip and not self.conflict:

                resource = s3db.resource(self.tablename, id=self.id)

                ondelete = s3db.get_config(self.tablename, "ondelete")
                success = resource.delete(ondelete=ondelete,
                                          cascade=True)
                if resource.error:
                    self.error = resource.error
                    self.skip = True
                    return ignore_errors

            _debug("Success: %s, id=%s %sd" % (self.tablename, self.id,
                                               self.skip and "skippe" or \
                                               method))
            return True

        # Audit + onaccept on successful commits
        if self.committed:
            form = Storage()
            form.method = method
            form.vars = self.data
            tablename = self.tablename
            prefix, name = tablename.split("_", 1)
            if self.id:
                form.vars.id = self.id
            if manager.audit is not None:
                manager.audit(method, prefix, name,
                              form=form,
                              record=self.id,
                              representation="xml")
            # Update super entity links
            s3db.update_super(table, form.vars)
            if method == METHOD.CREATE:
                # Set record owner
                current.auth.s3_set_record_owner(table, self.id)
            elif method == METHOD.UPDATE:
                # Update realm
                update_realm = s3db.get_config(table, "update_realm")
                if update_realm:
                    current.auth.set_realm_entity(table, self.id,
                                                  force_update=True)
            # Onaccept
            key = "%s_onaccept" % method
            onaccept = s3db.get_config(tablename, key,
                       s3db.get_config(tablename, "onaccept"))
            if onaccept:
                callback(onaccept, form, tablename=self.tablename)

        # Update referencing items
        if self.update and self.id:
            for u in self.update:
                item = u.get("item", None)
                if not item:
                    continue
                field = u.get("field", None)
                if isinstance(field, (list, tuple)):
                    pkey, fkey = field
                    query = table.id == self.id
                    row = db(query).select(table[pkey],
                                           limitby=(0, 1)).first()
                    if row:
                        item._update_reference(fkey, row[pkey])
                else:
                    item._update_reference(field, self.id)

        _debug("Success: %s, id=%s %sd" % (self.tablename, self.id,
                                           self.skip and "skippe" or \
                                           method))
        return True

    # -------------------------------------------------------------------------
    def _resolve_references(self):
        """
            Resolve the references of this item (=look up all foreign
            keys from other items of the same job). If a foreign key
            is not yet available, it will be scheduled for later update.
        """

        if not self.table:
            return

        items = self.job.items
        for reference in self.references:

            item = None
            field = reference.field
            entry = reference.entry
            if not entry:
                continue

            # Resolve key tuples
            if isinstance(field, (list,tuple)):
                pkey, fkey = field
            else:
                pkey, fkey = ("id", field)

            # Resolve the key table name
            ktablename, key, multiple = s3_get_foreign_key(self.table[fkey])
            if not ktablename:
                if self.tablename == "auth_user" and \
                   fkey == "organisation_id":
                    ktablename = "org_organisation"
                else:
                    continue
            if entry.tablename:
                ktablename = entry.tablename
            try:
                ktable = current.s3db[ktablename]
            except:
                continue

            # Resolve the foreign key (value)
            fk = entry.id
            if entry.item_id:
                item = items[entry.item_id]
                if item:
                    fk = item.id
            if fk and pkey != "id":
                row = current.db(ktable._id == fk).select(ktable[pkey],
                                                          limitby=(0, 1)).first()
                if not row:
                    fk = None
                    continue
                else:
                    fk = row[pkey]

            # Update record data
            if fk:
                if multiple:
                    val = self.data.get(fkey, [])
                    if fk not in val:
                        val.append(fk)
                    self.data[fkey] = val
                else:
                    self.data[fkey] = fk
            else:
                if fkey in self.data and not multiple:
                    del self.data[fkey]
                if item:
                    item.update.append(dict(item=self, field=fkey))

    # -------------------------------------------------------------------------
    def _update_reference(self, field, value):
        """
            Helper method to update a foreign key in an already written
            record. Will be called by the referenced item after (and only
            if) it has been committed. This is only needed if the reference
            could not be resolved before commit due to circular references.

            @param field: the field name of the foreign key
            @param value: the value of the foreign key
        """

        if not value or not self.table:
            return
        db = current.db
        if self.id and self.permitted:
            fieldtype = str(self.table[field].type)
            if fieldtype.startswith("list:reference"):
                query = (self.table.id == self.id)
                record = db(query).select(self.table[field],
                                          limitby=(0,1)).first()
                if record:
                    values = record[field]
                    if value not in values:
                        values.append(value)
                        db(self.table.id == self.id).update(**{field:values})
            else:
                db(self.table.id == self.id).update(**{field:value})

    # -------------------------------------------------------------------------
    def store(self, item_table=None):
        """
            Store this item in the DB
        """

        _debug("Storing item %s" % self)
        if item_table is None:
            return None
        db = current.db
        query = item_table.item_id == self.item_id
        row = db(query).select(item_table.id, limitby=(0, 1)).first()
        if row:
            record_id = row.id
        else:
            record_id = None
        record = Storage(job_id = self.job.job_id,
                         item_id = self.item_id,
                         tablename = self.tablename,
                         record_uid = self.uid,
                         error = self.error)
        if self.element is not None:
            element_str = current.xml.tostring(self.element,
                                               xml_declaration=False)
            record.update(element=element_str)
        if self.data is not None:
            data = Storage()
            for f in self.data.keys():
                table = self.table
                if f not in table.fields:
                    continue
                fieldtype = str(self.table[f].type)
                if fieldtype == "id" or s3_has_foreign_key(self.table[f]):
                    continue
                data.update({f:self.data[f]})
            data_str = cPickle.dumps(data)
            record.update(data=data_str)
        ritems = []
        for reference in self.references:
            field = reference.field
            entry = reference.entry
            store_entry = None
            if entry:
                if entry.item_id is not None:
                    store_entry = dict(field=field,
                                       item_id=str(entry.item_id))
                elif entry.uid is not None:
                    store_entry = dict(field=field,
                                       tablename=entry.tablename,
                                       uid=str(entry.uid))
                if store_entry is not None:
                    ritems.append(json.dumps(store_entry))
        if ritems:
            record.update(ritems=ritems)
        citems = [c.item_id for c in self.components]
        if citems:
            record.update(citems=citems)
        if self.parent:
            record.update(parent=self.parent.item_id)
        if record_id:
            db(item_table.id == record_id).update(**record)
        else:
            record_id = item_table.insert(**record)
        _debug("Record ID=%s" % record_id)
        return record_id

    # -------------------------------------------------------------------------
    def restore(self, row):
        """
            Restore an item from a item table row. This does not restore
            the references (since this can not be done before all items
            are restored), must call job.restore_references() to do that

            @param row: the item table row
        """

        xml = current.xml

        self.item_id = row.item_id
        self.accepted = None
        self.permitted = False
        self.committed = False
        tablename = row.tablename
        self.id = None
        self.uid = row.record_uid
        if row.data is not None:
            self.data = cPickle.loads(row.data)
        else:
            self.data = Storage()
        data = self.data
        if xml.MTIME in data:
            self.mtime = data[xml.MTIME]
        if xml.MCI in data:
            self.mci = data[xml.MCI]
        UID = xml.UID
        if UID in data:
            self.uid = data[UID]
        self.element = etree.fromstring(row.element)
        if row.citems:
            self.load_components = row.citems
        if row.ritems:
            self.load_references = [json.loads(ritem) for ritem in row.ritems]
        self.load_parent = row.parent
        try:
            table = current.s3db[tablename]
        except:
            self.error = self.ERROR.BAD_RESOURCE
            return False
        else:
            self.table = table
            self.tablename = tablename
        original = S3Resource.original(table, self.data)
        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            if UID in original:
                self.uid = original[UID]
                self.data.update({UID:self.uid})
        self.error = row.error
        if self.error and not self.data:
            # Validation error
            return False
        return True

# =============================================================================
class S3ImportJob():
    """
        Class to import an element tree into the database
    """

    JOB_TABLE_NAME = "s3_import_job"
    ITEM_TABLE_NAME = "s3_import_item"

    # -------------------------------------------------------------------------
    def __init__(self, manager, table,
                 tree=None,
                 files=None,
                 job_id=None,
                 strategy=None,
                 update_policy=None,
                 conflict_policy=None,
                 last_sync=None,
                 onconflict=None):
        """
            Constructor

            @param manager: the S3RequestManager instance performing this job
            @param tree: the element tree to import
            @param files: files attached to the import (for upload fields)
            @param job_id: restore job from database (record ID or job_id)
            @param strategy: the import strategy
            @param update_policy: the update policy
            @param conflict_policy: the conflict resolution policy
            @param last_sync: the last synchronization time stamp (datetime)
            @param onconflict: custom conflict resolver function
        """

        self.error = None # the last error
        self.error_tree = etree.Element(current.xml.TAG.root)

        self.table = table
        self.tree = tree
        self.files = files
        self.directory = Storage()

        self.elements = Storage()
        self.items = Storage()
        self.references = []

        self.job_table = None
        self.item_table = None

        self.count = 0 # total number of records imported
        self.created = [] # IDs of created records
        self.updated = [] # IDs of updated records
        self.deleted = [] # IDs of deleted records

        # Import strategy
        self.strategy = strategy
        if self.strategy is None:
            self.strategy = [S3ImportItem.METHOD.CREATE,
                             S3ImportItem.METHOD.UPDATE,
                             S3ImportItem.METHOD.DELETE]
        if not isinstance(self.strategy, (tuple, list)):
            self.strategy = [self.strategy]

        # Update policy (default=always update)
        self.update_policy = update_policy
        if not self.update_policy:
            self.update_policy = S3ImportItem.POLICY.OTHER
        # Conflict resolution policy (default=always update)
        self.conflict_policy = conflict_policy
        if not self.conflict_policy:
            self.conflict_policy = S3ImportItem.POLICY.OTHER

        # Synchronization settings
        self.mtime = None
        self.last_sync = last_sync
        self.onconflict = onconflict

        if job_id:
            self.__define_tables()
            jobtable = self.job_table
            if str(job_id).isdigit():
                query = jobtable.id == job_id
            else:
                query = jobtable.job_id == job_id
            row = current.db(query).select(limitby=(0, 1)).first()
            if not row:
                raise SyntaxError("Job record not found")
            self.job_id = row.job_id
            if not self.table:
                tablename = row.tablename
                try:
                    table = current.s3db[tablename]
                except:
                    pass
        else:
            import uuid
            self.job_id = uuid.uuid4() # unique ID for this job

    # -------------------------------------------------------------------------
    def add_item(self,
                 element=None,
                 original=None,
                 components=None,
                 parent=None,
                 joinby=None):
        """
            Parse and validate an XML element and add it as new item
            to the job.

            @param element: the element
            @param original: the original DB record (if already available,
                             will otherwise be looked-up by this function)
            @param components: a dictionary of components (as in S3Resource)
                               to include in the job (defaults to all
                               defined components)
            @param parent: the parent item (if this is a component)
            @param joinby: the component join key(s) (if this is a component)

            @returns: a unique identifier for the new item, or None if there
                      was an error. self.error contains the last error, and
                      self.error_tree an element tree with all failing elements
                      including error attributes.
        """

        if element in self.elements:
            # element has already been added to this job
            return self.elements[element]

        # Parse the main element
        item = S3ImportItem(self)

        # Update lookup lists
        item_id = item.item_id
        self.items[item_id] = item
        if element is not None:
            self.elements[element] = item_id

        if not item.parse(element,
                          original=original,
                          files=self.files):
            self.error = item.error
            item.accepted = False
            if parent is None:
                self.error_tree.append(deepcopy(item.element))

        else:
            # Now parse the components
            table = item.table
            components = current.s3db.get_components(table, names=components)

            cnames = Storage()
            cinfos = Storage()
            for alias in components:
                component = components[alias]
                pkey = component.pkey
                if component.linktable:
                    ctable = component.linktable
                    fkey = component.lkey
                else:
                    ctable = component.table
                    fkey = component.fkey
                ctablename = ctable._tablename
                if ctablename in cnames:
                    cnames[ctablename].append(alias)
                else:
                    cnames[ctablename] = [alias]
                cinfos[(ctablename, alias)] = Storage(component = component,
                                                      ctable = ctable,
                                                      pkey = pkey,
                                                      fkey = fkey,
                                                      original = None,
                                                      uid = None)
            add_item = self.add_item
            xml = current.xml
            for celement in xml.components(element, names=cnames.keys()):

                # Get the component tablename
                ctablename = celement.get(xml.ATTRIBUTE.name, None)
                if not ctablename:
                    continue

                # Get the component alias (for disambiguation)
                calias = celement.get(xml.ATTRIBUTE.alias, None)
                if calias is None:
                    if ctablename not in cnames:
                        continue
                    aliases = cnames[ctablename]
                    if len(aliases) == 1:
                        calias = aliases[0]
                    else:
                        # ambiguous components *must* use alias
                        continue
                if (ctablename, calias) not in cinfos:
                    continue
                else:
                    cinfo = cinfos[(ctablename, calias)]

                component = cinfo.component
                original = cinfo.original
                ctable = cinfo.ctable
                pkey = cinfo.pkey
                fkey = cinfo.fkey
                if not component.multiple:
                    if cinfo.uid is not None:
                        continue
                    if original is None and item.id:
                        query = (table.id == item.id) & \
                                (table[pkey] == ctable[fkey])
                        original = current.db(query).select(ctable.ALL,
                                                            limitby=(0, 1)).first()
                    if original:
                        cinfo.uid = uid = original.get(xml.UID, None)
                        celement.set(xml.UID, uid)
                    cinfo.original = original

                item_id = add_item(element=celement,
                                   original=original,
                                   parent=item,
                                   joinby=(pkey, fkey))
                if item_id is None:
                    item.error = self.error
                    self.error_tree.append(deepcopy(item.element))
                else:
                    citem = self.items[item_id]
                    citem.parent = item
                    item.components.append(citem)

            # Handle references
            table = item.table
            tree = self.tree
            if tree is not None:
                fields = [table[f] for f in table.fields]
                rfields = filter(s3_has_foreign_key, fields)
                item.references = self.lookahead(element,
                                                 table=table,
                                                 fields=rfields,
                                                 tree=tree,
                                                 directory=self.directory)
                for reference in item.references:
                    entry = reference.entry
                    if entry and entry.element is not None:
                        item_id = add_item(element=entry.element)
                        if item_id:
                            entry.update(item_id=item_id)

            # Parent reference
            if parent is not None:
                entry = Storage(item_id=parent.item_id,
                                element=parent.element,
                                tablename=parent.tablename)
                item.references.append(Storage(field=joinby,
                                               entry=entry))

        return item.item_id

    # -------------------------------------------------------------------------
    def lookahead(self,
                  element,
                  table=None,
                  fields=None,
                  tree=None,
                  directory=None):
        """
            Find referenced elements in the tree

            @param element: the element
            @param table: the DB table
            @param fields: the FK fields in the table
            @param tree: the import tree
            @param directory: a dictionary to lookup elements in the tree
                              (will be filled in by this function)
        """

        db = current.db
        s3db = current.s3db
        xml = current.xml
        import_uid = xml.import_uid
        ATTRIBUTE = xml.ATTRIBUTE
        TAG = xml.TAG
        UID = xml.UID
        reference_list = []

        root = None
        if tree is not None:
            if isinstance(tree, etree._Element):
                root = tree
            else:
                root = tree.getroot()
        references = element.findall("reference")
        for reference in references:
            field = reference.get(ATTRIBUTE.field, None)

            # Ignore references without valid field-attribute
            if not field or field not in fields:
                continue

            # Find the key table
            ktablename, key, multiple = s3_get_foreign_key(table[field])
            if not ktablename:
                if table._tablename == "auth_user" and \
                   field == "organisation_id":
                    ktablename = "org_organisation"
                else:
                    continue
            try:
                ktable = current.s3db[ktablename]
            except:
                continue

            tablename = reference.get(ATTRIBUTE.resource, None)
            # Ignore references to tables without UID field:
            if UID not in ktable.fields:
                continue
            # Fall back to key table name if tablename is not specified:
            if not tablename:
                tablename = ktablename
            # Super-entity references must use the super-key:
            if tablename != ktablename:
                field = (ktable._id.name, field)
            # Ignore direct references to super-entities:
            if tablename == ktablename and ktable._id.name != "id":
                continue
            # Get the foreign key
            uids = reference.get(UID, None)
            attr = UID
            if not uids:
                uids = reference.get(ATTRIBUTE.tuid, None)
                attr = ATTRIBUTE.tuid
            if uids and multiple:
                uids = json.loads(uids)
            elif uids:
                uids = [uids]

            # Find the elements and map to DB records
            relements = []

            # Create a UID<->ID map
            id_map = Storage()
            if attr == UID and uids:
                _uids = map(import_uid, uids)
                query = ktable[UID].belongs(_uids)
                records = db(query).select(ktable.id,
                                           ktable[UID])
                id_map = dict([(r[UID], r.id) for r in records])

            if not uids:
                # Anonymous reference: <resource> inside the element
                expr = './/%s[@%s="%s"]' % (TAG.resource,
                                            ATTRIBUTE.name,
                                            tablename)
                relements = reference.xpath(expr)
                if relements and not multiple:
                    relements = [relements[0]]

            elif root is not None:

                for uid in uids:

                    entry = None
                    # Entry already in directory?
                    if directory is not None:
                        entry = directory.get((tablename, attr, uid), None)
                    if not entry:
                        expr = ".//%s[@%s='%s' and @%s='%s']" % (
                                    TAG.resource,
                                    ATTRIBUTE.name,
                                    tablename,
                                    attr,
                                    uid)
                        e = root.xpath(expr)
                        if e:
                            # Element in the source => append to relements
                            relements.append(e[0])
                        else:
                            # No element found, see if original record exists
                            _uid = import_uid(uid)
                            if _uid and _uid in id_map:
                                _id = id_map[_uid]
                                entry = Storage(tablename=tablename,
                                                element=None,
                                                uid=uid,
                                                id=_id,
                                                item_id=None)
                                reference_list.append(Storage(field=field,
                                                              entry=entry))
                            else:
                                continue
                    else:
                        reference_list.append(Storage(field=field,
                                                      entry=entry))

            # Create entries for all newly found elements
            for relement in relements:
                uid = relement.get(attr, None)
                if attr == UID:
                    _uid = import_uid(uid)
                    id = _uid and id_map and id_map.get(_uid, None) or None
                else:
                    _uid = None
                    id = None
                entry = Storage(tablename=tablename,
                                element=relement,
                                uid=uid,
                                id=id,
                                item_id=None)
                # Add entry to directory
                if uid and directory is not None:
                    directory[(tablename, attr, uid)] = entry
                # Append the entry to the reference list
                reference_list.append(Storage(field=field, entry=entry))

        return reference_list

    # -------------------------------------------------------------------------
    def load_item(self, row):
        """
            Load an item from the item table (counterpart to add_item
            when restoring a job from the database)
        """

        item = S3ImportItem(self)
        if not item.restore(row):
            self.error = item.error
            if item.load_parent is None:
                self.error_tree.append(deepcopy(item.element))
        # Update lookup lists
        item_id = item.item_id
        self.items[item_id] = item
        return item_id

    # -------------------------------------------------------------------------
    def resolve(self, item_id, import_list):
        """
            Resolve the reference list of an item

            @param item_id: the import item UID
            @param import_list: the ordered list of items (UIDs) to import
        """

        item = self.items[item_id]
        if item.lock or item.accepted is False:
            return False
        references = []
        for reference in item.references:
            ritem_id = reference.entry.item_id
            if ritem_id and ritem_id not in import_list:
                references.append(ritem_id)
        for ritem_id in references:
            item.lock = True
            if self.resolve(ritem_id, import_list):
                import_list.append(ritem_id)
            item.lock = False
        return True

    # -------------------------------------------------------------------------
    def commit(self, ignore_errors=False):
        """
            Commit the import job to the DB

            @param ignore_errors: skip any items with errors
                                  (does still report the errors)
        """

        ATTRIBUTE = current.xml.ATTRIBUTE

        # Resolve references
        import_list = []
        for item_id in self.items:
            self.resolve(item_id, import_list)
            if item_id not in import_list:
                import_list.append(item_id)
        # Commit the items
        items = self.items
        count = 0
        mtime = None
        created = []
        cappend = created.append
        updated = []
        deleted = []
        tablename = self.table._tablename
        for item_id in import_list:
            item = items[item_id]
            error = None
            success = item.commit(ignore_errors=ignore_errors)
            error = item.error
            if error:
                self.error = error
                element = item.element
                if element is not None:
                    if not element.get(ATTRIBUTE.error, False):
                        element.set(ATTRIBUTE.error, str(self.error))
                    self.error_tree.append(deepcopy(element))
                if not ignore_errors:
                    return False
            elif item.tablename == tablename:
                count += 1
                if mtime is None or item.mtime > mtime:
                    mtime = item.mtime
                if item.id:
                    if item.method == item.METHOD.CREATE:
                        cappend(item.id)
                    elif item.method == item.METHOD.UPDATE:
                        updated.append(item.id)
                    elif item.method == item.METHOD.DELETE:
                        deleted.append(item.id)
        self.count = count
        self.mtime = mtime
        self.created = created
        self.updated = updated
        self.deleted = deleted
        return True

    # -------------------------------------------------------------------------
    def __define_tables(self):
        """
            Define the database tables for jobs and items
        """

        self.job_table = self.define_job_table()
        self.item_table = self.define_item_table()

    # -------------------------------------------------------------------------
    @classmethod
    def define_job_table(cls):

        db = current.db
        if cls.JOB_TABLE_NAME not in db:
            job_table = db.define_table(cls.JOB_TABLE_NAME,
                                        Field("job_id", length=128,
                                              unique=True,
                                              notnull=True),
                                        Field("tablename"),
                                        Field("timestmp", "datetime",
                                              default=datetime.utcnow()))
        else:
            job_table = db[cls.JOB_TABLE_NAME]
        return job_table

    # -------------------------------------------------------------------------
    @classmethod
    def define_item_table(cls):

        db = current.db
        if cls.ITEM_TABLE_NAME not in db:
            item_table = db.define_table(cls.ITEM_TABLE_NAME,
                                        Field("item_id", length=128,
                                              unique=True,
                                              notnull=True),
                                        Field("job_id", length=128),
                                        Field("tablename", length=128),
                                        #Field("record_id", "integer"),
                                        Field("record_uid"),
                                        Field("error", "text"),
                                        Field("data", "text"),
                                        Field("element", "text"),
                                        Field("ritems", "list:string"),
                                        Field("citems", "list:string"),
                                        Field("parent", length=128))
        else:
            item_table = db[cls.ITEM_TABLE_NAME]
        return item_table

    # -------------------------------------------------------------------------
    def store(self):
        """
            Store this job and all its items in the job table
        """

        db = current.db

        _debug("Storing Job ID=%s" % self.job_id)
        self.__define_tables()
        jobtable = self.job_table
        query = jobtable.job_id == self.job_id
        row = db(query).select(jobtable.id, limitby=(0, 1)).first()
        if row:
            record_id = row.id
        else:
            record_id = None
        record = Storage(job_id=self.job_id)
        try:
            tablename = self.table._tablename
        except:
            pass
        else:
            record.update(tablename=tablename)
        for item in self.items.values():
            item.store(item_table=self.item_table)
        if record_id:
            db(jobtable.id == record_id).update(**record)
        else:
            record_id = jobtable.insert(**record)
        _debug("Job record ID=%s" % record_id)
        return record_id

    # -------------------------------------------------------------------------
    def get_tree(self):
        """
            Reconstruct the element tree of this job
        """

        if self.tree is not None:
            return tree
        else:
            xml = current.xml
            root = etree.Element(xml.TAG.root)
            for item in self.items.values():
                if item.element is not None and not item.parent:
                    if item.tablename == self.table._tablename or \
                       item.element.get(xml.UID, None) or \
                       item.element.get(xml.ATTRIBUTE.tuid, None):
                        root.append(deepcopy(item.element))
            return etree.ElementTree(root)

    # -------------------------------------------------------------------------
    def delete(self):
        """
            Delete this job and all its items from the job table
        """

        db = current.db

        _debug("Deleting job ID=%s" % self.job_id)
        self.__define_tables()
        item_table = self.item_table
        query = item_table.job_id == self.job_id
        db(query).delete()
        job_table = self.job_table
        query = job_table.job_id == self.job_id
        db(query).delete()

    # -------------------------------------------------------------------------
    def restore_references(self):
        """
            Restore the job's reference structure after loading items
            from the item table
        """

        db = current.db
        UID = current.xml.UID

        for item in self.items.values():
            for citem_id in item.load_components:
                if citem_id in self.items:
                    item.components.append(self.items[citem_id])
            item.load_components = []
            for ritem in item.load_references:
                field = ritem["field"]
                if "item_id" in ritem:
                    item_id = ritem["item_id"]
                    if item_id in self.items:
                        _item = self.items[item_id]
                        entry = Storage(tablename=_item.tablename,
                                        element=_item.element,
                                        uid=_item.uid,
                                        id=_item.id,
                                        item_id=item_id)
                        item.references.append(Storage(field=field,
                                                       entry=entry))
                else:
                    _id = None
                    uid = ritem.get("uid", None)
                    tablename = ritem.get("tablename", None)
                    if tablename and uid:
                        try:
                            table = current.s3db[tablename]
                        except:
                            continue
                        if UID not in table.fields:
                            continue
                        query = table[UID] == uid
                        row = db(query).select(table._id,
                                               limitby=(0, 1)).first()
                        if row:
                            _id = row[table._id.name]
                        else:
                            continue
                        entry = Storage(tablename = ritem["tablename"],
                                        element=None,
                                        uid = ritem["uid"],
                                        id = _id,
                                        item_id = None)
                        item.references.append(Storage(field=field,
                                                       entry=entry))
            item.load_references = []
            if item.load_parent is not None:
                item.parent = self.items[item.load_parent]
                item.load_parent = None

# END =========================================================================
