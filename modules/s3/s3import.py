# -*- coding: utf-8 -*-

""" Resource Import Tools

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

# @todo: remove all interactive error reporting out of the _private methods,
#        and raise exceptions instead.
__all__ = ("S3Importer",
           "S3ImportJob",
           "S3ImportItem",
           "S3Duplicate",
           "S3BulkImporter",
           )

import datetime
import json
import os
import sys
import uuid

from copy import deepcopy
try:
    from lxml import etree
except ImportError:
    sys.stderr.write("ERROR: lxml module needed for XML handling\n")
    raise

from gluon import current, redirect, URL, \
                  A, B, DIV, INPUT, LI, P, TABLE, TBODY, TD, TFOOT, TH, TR, UL, \
                  IS_EMPTY_OR, IS_IN_SET, SQLFORM
from gluon.storage import Storage, Messages
from gluon.tools import callback, fetch

from s3compat import pickle, StringIO, basestring, urllib2, urlopen, HTTPError, URLError
from s3dal import Field
from .s3datetime import s3_utc
from .s3rest import S3Method, S3Request
from .s3resource import S3Resource
from .s3utils import s3_auth_user_represent_name, s3_get_foreign_key, \
                     s3_has_foreign_key, s3_mark_required, s3_str, s3_unicode
from .s3validators import IS_JSONS3

# =============================================================================
class S3Importer(S3Method):
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

            @return: output object to send to the view

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

        #current.log.debug("S3Importer.apply_method(%s)" % r)

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

        # Target table for the data import
        tablename = self.tablename

        # Table for uploads
        self.__define_table()

        # Check authorization
        permitted = current.auth.s3_has_permission
        authorised = permitted("create", self.upload_tablename) and \
                     permitted("create", tablename)
        if not authorised:
            if r.method is not None:
                r.unauthorised()
            else:
                return {"form": None}

        # Target table for the data import
        self.controller_resource = self.resource
        self.controller_table = self.table
        self.controller_tablename = tablename

        self.upload_resource = None
        self.item_resource = None

        # Environment
        self.controller = r.controller
        self.function = r.function

        try:
            self.uploadTitle = current.response.s3.crud_strings[tablename].title_upload or T("Import")
        except (KeyError, AttributeError):
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

        # XSLT Path
        self.xslt_path = os.path.join(r.folder, r.XSLT_PATH)
        self.xslt_extension = r.XSLT_EXTENSION

        # @todo get the data from either get_vars or post_vars appropriately
        #       for post -> commit_items would need to add the uploadID
        get_vars = r.get_vars
        transform = get_vars.get("transform", None)
        source = get_vars.get("filename", None)
        if "job" in r.post_vars:
            upload_id = r.post_vars["job"]
        else:
            upload_id = get_vars.get("job")
        items = self._process_item_list(upload_id, r.vars)
        if "delete" in get_vars:
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
            r.error(405, current.ERROR.BAD_METHOD)

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

        #current.log.debug("S3Importer.upload()")

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

        #current.log.debug("S3Importer.display()")

        response = current.response
        s3 = response.s3

        db = current.db
        table = self.upload_table
        output = None
        if self.ajax:
            sfilename = ofilename = r.post_vars["file"].filename
            upload_id = table.insert(controller = self.controller,
                                     function = self.function,
                                     filename = ofilename,
                                     file = sfilename,
                                     user_id = current.session.auth.user.id
                                     )
        else:
            title = self.uploadTitle
            form = self._upload_form(r, **attr)

            r = self.request
            r.read_body()
            sfilename = form.vars.file
            try:
                ofilename = r.post_vars["file"].filename
            except (KeyError, AttributeError):
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
                db(query).update(controller = self.controller,
                                 function = self.function,
                                 filename = ofilename,
                                 user_id = current.session.auth.user.id)
                row = db(query).select(table.id,
                                       limitby=(0, 1)).first()
                upload_id = row.id

        if not output:
            output = {}
            # Must commit here to separate this transaction from
            # the trial import phase which will be rolled back.
            db.commit()

            extension = ofilename.rsplit(".", 1).pop()
            if extension not in ("csv", "xls", "xlsx", "xlsm"):
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
                    # Survey module currently
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
                    current.session.confirmation = self.messages.file_uploaded
                    # For a single pass retain the vars from the original URL
                    next_URL = URL(r=self.request,
                                   f=self.function,
                                   args=["import"],
                                   vars=current.request.get_vars
                                  )
                    redirect(next_URL)
                s3.dataTable_vars = {"job": upload_id}
                return self.display_job(upload_id)
        return output

    # -------------------------------------------------------------------------
    def display_job(self, upload_id):
        """
            @todo: docstring?
        """

        #current.log.debug("S3Importer.display_job()")

        db = current.db
        request = self.request
        table = self.upload_table
        job_id = self.job_id
        if job_id is None:
            # Redirect to the start page (removes all vars)
            db(table.id == upload_id).update(status = 2) # in error
            current.session.warning = self.messages.no_records_to_import
            redirect(URL(r=request, f=self.function, args=["import"]))

        # Get the status of the upload job
        row = db(table.id == upload_id).select(table.status,
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

        output = self._create_import_item_dataTable(upload_id, job_id)
        if request.representation == "aadata":
            return output

        # Interactive Import
        # Display import items
        response = current.response
        response.view = self._view(request, "list.html")
        if response.s3.error_report:
            error_report = "Errors|" + "|".join(response.s3.error_report)
            error_tip = A("All Errors",
                          _class="errortip",
                          _title=error_report)
        else:
            # @todo: restore the error tree from all items?
            error_tip = ""

        rowcount = len(self._get_all_items(upload_id))
        rheader = DIV(TABLE(TR(TH("%s: " % self.messages.job_total_records),
                               TD(rowcount, _id="totalAvailable"),
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
            Import a source

            @param source: the source
            @param transform: the stylesheet path
        """

        #current.log.debug("S3Importer.commit(%s, %s)" % (source, transform))

        session = current.session
        try:
            user = session.auth.user.id
        except AttributeError:
            user = None

        # @todo: manage different file formats
        # @todo: find file format from request.extension
        extension = source.rsplit(".", 1).pop()
        if extension not in ("csv, ""xls", "xlsx", "xlsm"):
            file_format = "csv"
        else:
            file_format = extension

        # Insert data in the table and get the ID
        try:
            with open(source, "r") as infile:
                upload_id = self.upload_table.insert(controller = self.controller,
                                                     function = self.function,
                                                     filename = source,
                                                     user_id = user,
                                                     status = 1,
                                                     )
                current.db.commit()

                # Create the import job
                result = self._generate_import_job(upload_id,
                                                   infile,
                                                   file_format,
                                                   stylesheet = transform,
                                                   )
        except IOError:
            # Source not found or not readable
            session.error = self.messages.file_open_error % source
            redirect(URL(r=self.request, f=self.function))

        if result is None:
            if self.error != None:
                if session.error is None:
                    session.error = self.error
                else:
                    session.error += self.error
            if self.warning != None:
                if session.warning is None:
                    session.warning = self.warning
                else:
                    session.warning += self.warning
        else:
            items = self._get_all_items(upload_id, True)
            # Commit the import job
            self._commit_import_job(upload_id, items)
            result = self._update_upload_job(upload_id)

            # Get the results and display
            messages = self.messages
            msg = "%s : %s %s %s" % (source,
                                     messages.commit_total_records_imported,
                                     messages.commit_total_errors,
                                     messages.commit_total_records_ignored)
            msg = msg % result

            confirmation = session.confirmation
            if confirmation is None:
                confirmation = msg
            else:
                confirmation += msg

        # @todo: return the upload_id?

    # -------------------------------------------------------------------------
    def commit_items(self, upload_id, items):
        """
            @todo: docstring?
        """

        #current.log.debug("S3Importer.commit_items(%s, %s)" % (upload_id, items))
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

        #current.log.debug("S3Importer.delete_job(%s)" % upload_id)

        db = current.db

        request = self.request
        resource = request.resource # use self.resource?

        # Get the import job ID
        job_id = self.job_id

        # Delete the import job (if any)
        if job_id:
            result = resource.import_xml(None,
                                         id = None,
                                         tree = None,
                                         job_id = job_id,
                                         delete_job = True,
                                         )
        # @todo: check result

        # Delete the upload entry
        count = db(self.upload_table.id == upload_id).delete()
        # @todo: check that the record has been deleted

        # Commit the changes
        db.commit()

        result = count

        # Return to the main import screen
        # @todo: check result properly
        if result == False:
            current.response.warning = self.messages.no_job_to_delete
        else:
            current.response.confirmation = self.messages.job_deleted

        # redirect to the start page (remove all vars)
        self.next = request.url(vars={})

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
        response.view = self._view(request, "list_filter.html")

        if REPLACE_OPTION in attr:
            replace_option = attr[REPLACE_OPTION]
            if replace_option is not None:
                field = table.replace_option
                field.readable = field.writable = True
                field.label = replace_option
                field.comment = DIV(_class="tooltip",
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
            except IOError:
                pass

        if form.accepts(r.post_vars, current.session, formname="upload_form"):

            formvars = form.vars

            # Create the upload entry
            table.insert(file = formvars.file)

            # Process extra fields
            if self.csv_extra_fields:

                # Convert Values to Represents
                extra_data = self.csv_extra_data = Storage()
                for f in self.csv_extra_fields:
                    label = f.get("label")
                    if not label:
                        continue
                    field = f.get("field")
                    value = f.get("value")
                    if field:
                        if field.name in formvars:
                            data = formvars[field.name]
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
                                        break
                                if hasattr(value, "m"):
                                    # Don't translate: XSLT expects English
                                    value = value.m
                    elif value is None:
                        continue
                    extra_data[label] = value

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
        #fields = ["id",
        #          "filename",
        #          "created_on",
        #          "user_id",
        #          "replace_option",
        #          "status",
        #          ]

        self._use_upload_table()

        # Hide the list of prior uploads for now
        #output = self._dataTable(fields, sort_by = [[2,"desc"]])
        output = {}

        self._use_controller_table()

        if request.representation == "aadata":
            return output

        query = (table.status != 3) # Status of Pending or in-Error
        rows = db(query).select(table.id)
        restrictOpen = [str(row.id) for row in rows]
        query = (table.status == 3) # Status of Completed
        rows = db(query).select(table.id)
        restrictView = [str(row.id) for row in rows]

        s3.actions = [{"label": str(self.messages.open_btn),
                       "_class": "action-btn",
                       "url": URL(r=request,
                                  c=controller,
                                  f=function,
                                  args=["import"],
                                  vars={"job":"[id]"}),
                       "restrict": restrictOpen
                       },
                      {"label": str(self.messages.view_btn),
                       "_class": "action-btn",
                       "url": URL(r=request,
                                  c=controller,
                                  f=function,
                                  args=["import"],
                                  vars={"job":"[id]"}),
                       "restrict": restrictView
                       },
                      {"label": str(self.messages.delete_btn),
                       "_class": "delete-btn",
                       "url": URL(r=request,
                                  c=controller,
                                  f=function,
                                  args=["import"],
                                  vars={"job":"[id]",
                                        "delete":"True"
                                       }
                                  )
                       },
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

        represent = {"s3_import_item.element": self._item_element_represent}
        self._use_import_item_table(job_id)
        table = self.table

        # Get a list of the records that have an error of None
        query =  (table.job_id == job_id) & \
                 (table.tablename == self.controller_tablename)
        rows = current.db(query).select(table.id, table.error)
        select_list = []
        error_list = []
        for row in rows:
            if row.error:
                error_list.append(str(row.id))
            else:
                select_list.append("%s" % row.id)

        # Add a filter to the dataTable query
        s3.filter = query

        # Experimental uploading via ajax - added for vulnerability
        if self.ajax:
            resource = self.resource
            resource.add_filter(query)
            rows = resource.select(["id", "element", "error"],
                                   limit=None)["rows"]
            return (upload_id, select_list, rows)

        # Toggle-button for item details
        s3.actions = [{"label": str(self.messages.item_show_details),
                       "_class": "action-btn toggle-item",
                       },
                      ]
        s3.jquery_ready.append('''
$('#import-items').on('click','.toggle-item',function(){$('.importItem.item-'+$(this).attr('db_id')).toggle();})''')

        output = self._dataTable(["id", "element", "error"],
                                 #sort_by = [[1, "asc"]],
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
                             infile,
                             file_format,
                             stylesheet=None,
                             commit_job=False):
        """
            This will take a s3_import_upload record and
            generate the importJob

            @param uploadFilename: The name of the uploaded file

            @todo: complete parameter descriptions
        """

        #current.log.debug("S3Importer._generate_import_job(%s, %s, %s, %s)" % (upload_id,
        #                                                                       infile,
        #                                                                       file_format,
        #                                                                       stylesheet,
        #                                                                       ))

        # ---------------------------------------------------------------------
        # CSV
        if file_format in ("csv", "comma-separated-values"):

            fmt = "csv"
            src = infile

        # ---------------------------------------------------------------------
        # XLS
        elif file_format in ("xls", "xlsx", "xlsm"):

            fmt = "xls"
            src = infile

        # ---------------------------------------------------------------------
        # XML
        # @todo: implement
        #elif file_format == "xml":

        # ---------------------------------------------------------------------
        # S3JSON
        # @todo: implement
        #elif file_format == "s3json":

        # ---------------------------------------------------------------------
        # PDF
        # @todo: implement
        #elif file_format == "pdf":

        # ---------------------------------------------------------------------
        # Unsupported Format
        else:
            msg = self.messages.unsupported_file_type % file_format
            self.error = msg
            current.log.debug(msg)
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
            current.log.debug(msg)
            return None

        return stylesheet

    # -------------------------------------------------------------------------
    def _commit_import_job(self, upload_id, items):
        """
            This will save all of the selected import items

            @todo: parameter descriptions?
        """

        db = current.db
        resource = self.request.resource

        # Load the items from the s3_import_item table
        self.importDetails = {}

        table = self.upload_table
        row = db(table.id == upload_id).select(table.job_id,
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
            for _id in rows:
                if str(_id) not in items:
                    # @todo: replace with a helper method from the API
                    db(itemTable.id == _id).delete()

            #****************************************************************
            # EXPERIMENTAL
            #****************************************************************

            # Set up the table we will import data into
            self.table = self.controller_table
            self.tablename = self.controller_tablename

            self._store_import_details(job_id, "preImportTree")

            # Now commit the remaining items
            resource.import_xml(None,
                                job_id = job_id,
                                ignore_errors = True,
                                )
            return resource.error is None

    # -------------------------------------------------------------------------
    def _store_import_details(self, job_id, key):
        """
            This will store the details from an importJob

            @todo: parameter descriptions?
        """

        #current.log.debug("S3Importer._store_import_details(%s, %s)" % (job_id, key))

        itable = S3ImportJob.define_item_table()

        query = (itable.job_id == job_id)  & \
                (itable.tablename == self.controller_tablename)
        rows = current.db(query).select(itable.data, itable.error)
        items = [{"data": row.data, "error": row.error} for row in rows]

        self.importDetails[key] = items

    # -------------------------------------------------------------------------
    def _update_upload_job(self, upload_id):
        """
            This will record the results from the import, and change the
            status of the upload job

            @todo: parameter descriptions?
            @todo: report errors in referenced records, too
        """

        #current.log.debug("S3Importer._update_upload_job(%s)" % upload_id)

        resource = self.request.resource
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
        db(query).update(summary_added=totalRecords,
                         summary_error=totalErrors,
                         summary_ignored = totalIgnored,
                         status = 3)

        # Commit the changes
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

        messages = self.messages
        msg = "%s - %s - %s" % \
              (messages.commit_total_records_imported,
               messages.commit_total_errors,
               messages.commit_total_records_ignored)
        msg = msg % totals

        if timestmp != None:
            current.session.flash = messages.job_completed % \
                                        (self.date_represent(timestmp), msg)
        elif totals[1] is not 0:
            current.session.error = msg
        elif totals[2] is not 0:
            current.session.warning = msg
        else:
            current.session.flash = msg

    # -------------------------------------------------------------------------
    def _dataTable(self,
                   list_fields,
                   #sort_by = [[1, "asc"]],
                   represent=None,
                   ajax_item_id=None,
                   dt_bulk_select=None,
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
               recordsTotal         Number of records in the filtered data set
               recordsFiltered  Number of records to display
               start                Start point in the ordered data set
               limit                Number of records in the ordered set
               NOTE: limit - recordsFiltered = total cached
        """

        from .s3data import S3DataTable
        request = self.request
        resource = self.resource
        s3 = current.response.s3

        # Controller Filter
        if s3.filter is not None:
            self.resource.add_filter(s3.filter)

        representation = request.representation

        # Datatable Filter
        totalrows = None
        if representation == "aadata":
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               request.get_vars)
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
        else:
            orderby, left = None, None

        # Start/Limit
        if representation == "aadata":
            get_vars = request.get_vars
            start = get_vars.get("displayStart", None)
            limit = get_vars.get("pageLength", None)
            draw = int(get_vars.draw or 0)
        else: # catch all
            start = 0
            limit = s3.ROWSPERPAGE
        if limit is not None:
            try:
                start = int(start)
                limit = int(limit)
            except ValueError:
                start = None
                limit = None # use default
        else:
            start = None # use default

        if not orderby:
            orderby = ~resource.table.error

        data = resource.select(list_fields,
                               start=start,
                               limit=limit,
                               count=True,
                               orderby=orderby,
                               left=left)
        rows = data["rows"]

        displayrows = data["numrows"]
        if totalrows is None:
            totalrows = displayrows

        # Represent the data
        if represent:
            _represent = list(represent.items())
            for row in rows:
                record_id = row["s3_import_item.id"]
                for column, method in _represent:
                    if column in row:
                        row[column] = method(record_id, row[column])

        # Build the datatable
        rfields = resource.resolve_selectors(list_fields)[0]
        dt = S3DataTable(rfields, rows, orderby=orderby)
        datatable_id = "import-items"
        if representation == "aadata":
            # Ajax callback
            output = dt.json(totalrows,
                             displayrows,
                             datatable_id,
                             draw,
                             dt_bulk_actions = [current.T("Import")])
        else:
            # Initial HTML response
            url = "/%s/%s/%s/import.aadata?job=%s" % (request.application,
                                                      request.controller,
                                                      request.function,
                                                      ajax_item_id)
            items =  dt.html(totalrows,
                             displayrows,
                             datatable_id,
                             dt_ajax_url=url,
                             dt_bulk_actions = [current.T("Import")],
                             dt_bulk_selected = dt_bulk_select)
            output = {"items":items}

            current.response.s3.dataTableID = [datatable_id]

        return output

    # -------------------------------------------------------------------------
    def _item_element_represent(self, item_id, value):
        """
            Represent the element in an import item for dataTable display

            @param value: the string containing the element
        """

        try:
            element = etree.fromstring(value)
        except:
            return DIV(value)

        db = current.db
        tablename = element.get("name")
        table = db[tablename]

        output = DIV()
        details = TABLE(_class="importItem item-%s" % item_id)
        header, rows = self._add_item_details(element.findall("data"), table)
        if header is not None:
            output.append(header)
        # Add components, if present
        components = element.findall("resource")
        s3db = current.s3db
        for component in components:
            ctablename = component.get("name")
            ctable = s3db.table(ctablename)
            if not ctable:
                continue
            self._add_item_details(component.findall("data"), ctable,
                                   details=rows, prefix=True)
        if rows:
            details.append(TBODY(rows))
        # Add error messages, if present
        errors = current.xml.collect_errors(element)
        if errors:
            details.append(TFOOT(TR(TH("%s:" % current.T("Errors")),
                                   TD(UL([LI(e) for e in errors])))))
        if rows == [] and components == []:
            # At this stage we don't have anything to display to see if we can
            # find something to show. This could be the case when a table being
            # imported is a resolver for a many to many relationship
            refdetail = TABLE(_class="importItem item-%s" % item_id)
            references = element.findall("reference")
            for reference in references:
                tuid = reference.get("tuid")
                resource = reference.get("resource")
                refdetail.append(TR(TD(resource), TD(tuid)))
            output.append(refdetail)
        else:
            output.append(details)
        return output

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
                value = current.xml.xml_decode(child.text)
            try:
                value = S3Importer._decode_data(field, value)
            except (TypeError, ValueError):
                pass
            if value:
                value = s3_unicode(value)
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

        if field.type == "string" or  \
           field.type == "password" or \
           field.type == "upload" or \
           field.type == "text":
            return value
        elif field.type == "integer" or \
             field.type == "id":
            return int(value)
        elif field.type == "double" or \
             field.type == "decimal":
            return float(value)
        elif field.type == "boolean":
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
    def _process_item_list(self, upload_id, req_vars):
        """
            Get the list of IDs for the selected items from the "mode"
            and "selected" request variables

            @param upload_id: the upload_id
            @param vars: the request variables
        """

        items = None
        if "mode" in req_vars:
            mode = req_vars["mode"]
            selected = req_vars.get("selected", [])
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
        if self.upload_resource is None:
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

        #current.log.debug("S3Importer.__define_table()")

        T = current.T
        request = current.request

        self.upload_tablename = self.UPLOAD_TABLE_NAME

        import_upload_status = {
            1: T("Pending"),
            2: T("In error"),
            3: T("Completed"),
        }

        now = request.utcnow
        table = self.define_upload_table()
        table.file.upload_folder = os.path.join(request.folder,
                                                "uploads",
                                                #"imports"
                                                )
        messages = self.messages
        table.file.comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (messages.import_file,
                                                   messages.import_file_comment))
        table.file.label = messages.import_file
        table.status.requires = IS_IN_SET(import_upload_status, zero=None)
        table.status.represent = lambda opt: \
            import_upload_status.get(opt, current.messages.UNKNOWN_OPT)
        table.user_id.label = messages.user_name
        table.user_id.represent = s3_auth_user_represent_name
        table.created_on.default = now
        table.created_on.represent = self.date_represent
        table.modified_on.default = now
        table.modified_on.update = now
        table.modified_on.represent = self.date_represent

        table.replace_option.label = T("Replace")

        self.upload_table = current.db[self.UPLOAD_TABLE_NAME]

    # -------------------------------------------------------------------------
    @classmethod
    def define_upload_table(cls):
        """ Defines the upload table """


        # @todo: move into s3db/s3.py
        db = current.db
        UPLOAD_TABLE_NAME = cls.UPLOAD_TABLE_NAME
        if UPLOAD_TABLE_NAME not in db:
            db.define_table(UPLOAD_TABLE_NAME,
                            Field("controller",
                                  readable = False,
                                  writable = False),
                            Field("function",
                                  readable = False,
                                  writable = False),
                            Field("file", "upload",
                                  length = current.MAX_FILENAME_LENGTH,
                                  uploadfolder = os.path.join(current.request.folder,
                                                              "uploads", "imports"),
                                  autodelete = True),
                            Field("filename",
                                  readable = False,
                                  writable = False),
                            Field("status", "integer",
                                  default=1,
                                  readable = False,
                                  writable = False),
                            Field("extra_data",
                                  readable = False,
                                  writable = False),
                            Field("replace_option", "boolean",
                                  default=False,
                                  readable = False,
                                  writable = False),
                            Field("job_id", length=128,
                                  readable = False,
                                  writable = False),
                            Field("user_id", "integer",
                                  readable = False,
                                  writable = False),
                            Field("created_on", "datetime",
                                  readable = False,
                                  writable = False),
                            Field("modified_on", "datetime",
                                  readable = False,
                                  writable = False),
                            Field("summary_added", "integer",
                                  readable = False,
                                  writable = False),
                            Field("summary_error", "integer",
                                  readable = False,
                                  writable = False),
                            Field("summary_ignored", "integer",
                                  readable = False,
                                  writable = False),
                            Field("completed_details", "text",
                                  readable = False,
                                  writable = False))

        return db[UPLOAD_TABLE_NAME]

# =============================================================================
class S3ImportItem(object):
    """ Class representing an import item (=a single record) """

    METHOD = Storage(
        CREATE = "create",
        UPDATE = "update",
        DELETE = "delete",
        MERGE = "merge"
    )

    POLICY = Storage(
        THIS   = "THIS",            # keep local instance
        OTHER  = "OTHER",           # update unconditionally
        NEWER  = "NEWER",           # update if import is newer
        MASTER = "MASTER"           # update if import is master
    )

    # -------------------------------------------------------------------------
    def __init__(self, job):
        """
            Constructor

            @param job: the import job this item belongs to
        """

        self.job = job

        # Locking and error handling
        self.lock = False
        self.error = None

        # Identification
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
        self.mtime = datetime.datetime.utcnow()
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

            @return: True if successful, False if not (sets self.error)
        """

        s3db = current.s3db
        xml = current.xml

        ERROR = xml.ATTRIBUTE["error"]

        self.element = element
        if table is None:
            tablename = element.get(xml.ATTRIBUTE["name"])
            table = s3db.table(tablename)
            if table is None:
                self.error = current.ERROR.BAD_RESOURCE
                element.set(ERROR, s3_unicode(self.error))
                return False
        else:
            tablename = table._tablename

        self.table = table
        self.tablename = tablename

        UID = xml.UID

        if original is None:
            original = S3Resource.original(table, element,
                                           mandatory = self._mandatory_fields())
        elif isinstance(original, basestring) and UID in table.fields:
            # Single-component update in add-item => load the original now
            query = (table[UID] == original)
            pkeys = set(fname for fname in table.fields if table[fname].unique)
            fields = S3Resource.import_fields(table, pkeys,
                                              mandatory = self._mandatory_fields())
            original = current.db(query).select(limitby=(0, 1), *fields).first()
        else:
            original = None

        postprocess = s3db.get_config(tablename, "xml_post_parse")
        data = xml.record(table, element,
                          files=files,
                          original=original,
                          postprocess=postprocess)

        if data is None:
            self.error = current.ERROR.VALIDATION_ERROR
            self.accepted = False
            if not element.get(ERROR, False):
                element.set(ERROR, s3_unicode(self.error))
            return False

        self.data = data

        MCI = xml.MCI
        MTIME = xml.MTIME

        self.uid = data.get(UID)
        if original is not None:

            self.original = original
            self.id = original[table._id.name]

            if not current.response.s3.synchronise_uuids and UID in original:
                self.uid = self.data[UID] = original[UID]

        if MTIME in data:
            self.mtime = data[MTIME]
        if MCI in data:
            self.mci = data[MCI]

        #current.log.debug("New item: %s" % self)
        return True

    # -------------------------------------------------------------------------
    def deduplicate(self):
        """
            Detect whether this is an update or a new record
        """

        table = self.table
        if table is None or self.id:
            return

        METHOD = self.METHOD
        CREATE = METHOD["CREATE"]
        UPDATE = METHOD["UPDATE"]
        DELETE = METHOD["DELETE"]
        MERGE = METHOD["MERGE"]

        xml = current.xml
        UID = xml.UID

        data = self.data
        if self.job.second_pass and UID in table.fields:
            uid = data.get(UID)
            if uid and not self.element.get(UID) and not self.original:
                # Previously identified original does no longer exist
                del data[UID]

        mandatory = self._mandatory_fields()

        if self.original is not None:
            original = self.original
        elif self.data:
            original = S3Resource.original(table,
                                           self.data,
                                           mandatory=mandatory,
                                           )
        else:
            original = None

        synchronise_uuids = current.response.s3.synchronise_uuids

        deleted = data[xml.DELETED]
        if deleted:
            if data[xml.REPLACEDBY]:
                self.method = MERGE
            else:
                self.method = DELETE

        self.uid = data.get(UID)

        if original is not None:

            # The original record could be identified by a unique-key-match,
            # so this must be an update
            self.id = original[table._id.name]

            if not deleted:
                self.method = UPDATE

        else:

            if UID in data and not synchronise_uuids:
                # The import item has a UUID but there is no match
                # in the database, so this must be a new record
                self.id = None
                if not deleted:
                    self.method = CREATE
                else:
                    # Nonexistent record to be deleted => skip
                    self.method = DELETE
                    self.skip = True
            else:
                # Use the resource's deduplicator to identify the original
                resolve = current.s3db.get_config(self.tablename, "deduplicate")
                if data and resolve:
                    resolve(self)

            if self.id and self.method in (UPDATE, DELETE, MERGE):
                # Retrieve the original
                fields = S3Resource.import_fields(table,
                                                  data,
                                                  mandatory=mandatory,
                                                  )
                original = current.db(table._id == self.id) \
                                  .select(limitby=(0, 1), *fields).first()

        # Retain the original UUID (except in synchronise_uuids mode)
        if original and not synchronise_uuids and UID in original:
            self.uid = data[UID] = original[UID]

        self.original = original

    # -------------------------------------------------------------------------
    def authorize(self):
        """
            Authorize the import of this item, sets self.permitted
        """

        if not self.table:
            return False

        auth = current.auth
        tablename = self.tablename

        # Check whether self.table is protected
        if not auth.override and tablename.split("_", 1)[0] in auth.PROTECTED:
            return False

        # Determine the method
        METHOD = self.METHOD
        if self.data.deleted is True:
            if self.data.deleted_rb:
                self.method = METHOD["MERGE"]
            else:
                self.method = METHOD["DELETE"]
            self.accepted = True if self.id else False
        elif self.id:
            if not self.original:
                fields = S3Resource.import_fields(self.table, self.data,
                                        mandatory=self._mandatory_fields())
                query = (self.table.id == self.id)
                self.original = current.db(query).select(limitby=(0, 1),
                                                         *fields).first()
            if self.original:
                self.method = METHOD["UPDATE"]
            else:
                self.method = METHOD["CREATE"]
        else:
            self.method = METHOD["CREATE"]

        # Set self.id
        if self.method == METHOD["CREATE"]:
            self.id = 0

        # Authorization
        authorize = current.auth.s3_has_permission
        if authorize:
            self.permitted = authorize(self.method,
                                       tablename,
                                       record_id=self.id)
        else:
            self.permitted = True

        return self.permitted

    # -------------------------------------------------------------------------
    def validate(self):
        """
            Validate this item (=record onvalidation), sets self.accepted
        """

        data = self.data

        if self.accepted is not None:
            return self.accepted
        if data is None or not self.table:
            self.accepted = False
            return False

        xml = current.xml
        ERROR = xml.ATTRIBUTE["error"]

        METHOD = self.METHOD
        DELETE = METHOD.DELETE
        MERGE = METHOD.MERGE

        # Detect update
        if not self.id:
            self.deduplicate()
        if self.accepted is False:
            # Item rejected by deduplicator (e.g. due to ambiguity)
            return False

        # Don't need to validate skipped or deleted records
        if self.skip or self.method in (DELETE, MERGE):
            self.accepted = True if self.id else False
            return True

        # Set dynamic defaults for new records
        if not self.id:
            self._dynamic_defaults(data)

        # Check for mandatory fields
        required_fields = self._mandatory_fields()

        all_fields = list(data.keys())

        failed_references = []
        items = self.job.items
        for reference in self.references:
            resolvable = resolved = True
            entry = reference.entry
            if entry and not entry.id:
                if entry.item_id:
                    item = items[entry.item_id]
                    if item.error:
                        relement = reference.element
                        if relement is not None:
                            # Repeat the errors from the referenced record
                            # in the <reference> element (better reasoning)
                            msg = "; ".join(xml.collect_errors(entry.element))
                            relement.set(ERROR, msg)
                        else:
                            resolvable = False
                        resolved = False
                else:
                    resolvable = resolved = False
            field = reference.field
            if isinstance(field, (tuple, list)):
                field = field[1]
            if resolved:
                all_fields.append(field)
            elif resolvable:
                # Both reference and referenced record are in the XML,
                # => treat foreign key as mandatory, and mark as failed
                if field not in required_fields:
                    required_fields.append(field)
                if field not in failed_references:
                    failed_references.append(field)

        missing = [fname for fname in required_fields
                         if fname not in all_fields]

        original = self.original
        if missing:
            if original:
                missing = [fname for fname in missing
                                 if fname not in original]
            if missing:
                fields = [f for f in missing
                            if f not in failed_references]
                if fields:
                    errors = ["%s: value(s) required" % ", ".join(fields)]
                else:
                    errors = []
                if failed_references:
                    fields = ", ".join(failed_references)
                    errors.append("%s: reference import(s) failed" %
                                  ", ".join(failed_references))
                self.error = "; ".join(errors)
                self.element.set(ERROR, self.error)
                self.accepted = False
                return False

        # Run onvalidation
        form = Storage(method = self.method,
                       vars = data,
                       request_vars = data,
                       # Useless since always incomplete:
                       #record = original,
                       )
        if self.id:
            form.vars.id = self.id

        form.errors = Storage()
        tablename = self.tablename
        key = "%s_onvalidation" % self.method
        get_config = current.s3db.get_config
        onvalidation = get_config(tablename, key,
                       get_config(tablename, "onvalidation"))
        if onvalidation:
            try:
                callback(onvalidation, form, tablename=tablename)
            except:
                from traceback import format_exc
                current.log.error("S3Import %s onvalidation exception:" % tablename)
                current.log.debug(format_exc(10))
        accepted = True
        if form.errors:
            element = self.element
            for k in form.errors:
                e = element.findall("data[@field='%s']" % k)
                if not e:
                    e = element.findall("reference[@field='%s']" % k)
                if not e:
                    e = element
                    form.errors[k] = "[%s] %s" % (k, form.errors[k])
                else:
                    e = e[0]
                e.set(ERROR, s3_unicode(form.errors[k]))
            self.error = current.ERROR.VALIDATION_ERROR
            accepted = False

        self.accepted = accepted
        return accepted

    # -------------------------------------------------------------------------
    def commit(self, ignore_errors=False):
        """
            Commit this item to the database

            @param ignore_errors: skip invalid components
                                  (still reports errors)
        """

        if self.committed:
            # already committed
            return True

        # If the parent item gets skipped, then skip this item as well
        if self.parent is not None and self.parent.skip:
            return True

        # Globals
        db = current.db
        s3db = current.s3db

        xml = current.xml
        ATTRIBUTE = xml.ATTRIBUTE

        # Methods
        METHOD = self.METHOD
        CREATE = METHOD.CREATE
        UPDATE = METHOD.UPDATE
        DELETE = METHOD.DELETE
        MERGE = METHOD.MERGE

        # Policies
        POLICY = self.POLICY
        THIS = POLICY["THIS"]
        NEWER = POLICY["NEWER"]
        MASTER = POLICY["MASTER"]

        # Constants
        UID = xml.UID
        MCI = xml.MCI
        MTIME = xml.MTIME
        VALIDATION_ERROR = current.ERROR.VALIDATION_ERROR

        # Make item mtime TZ-aware
        self.mtime = s3_utc(self.mtime)

        # Resolve references
        self._resolve_references()

        # Deduplicate and validate
        if not self.validate():
            self.skip = True

            # Notify the error in the parent to have reported in the
            # interactive (2-phase) importer
            # Note that the parent item is already written at this point,
            # so this notification can NOT prevent/rollback the import of
            # the parent item if ignore_errors is True (forced commit), or
            # if the user deliberately chose to import it despite error.
            parent = self.parent
            if parent is not None:
                parent.error = VALIDATION_ERROR
                element = parent.element
                if not element.get(ATTRIBUTE.error, False):
                    element.set(ATTRIBUTE.error, s3_unicode(parent.error))

            return ignore_errors

        elif self.method not in (MERGE, DELETE) and self.components:
            for component in self.components:
                if component.accepted is False or \
                   component.data is None:
                    component.skip = True
                    # Skip this item on any component validation errors
                    self.skip = True
                    self.error = VALIDATION_ERROR
                    return ignore_errors

        elif self.method in (MERGE, DELETE) and not self.accepted:
            self.skip = True
            # Deletion of non-existent record: ignore silently
            return True

        # Authorize item
        if not self.authorize():
            self.error = "%s: %s, %s, %s" % (current.ERROR.NOT_PERMITTED,
                                             self.method,
                                             self.tablename,
                                             self.id)
            self.skip = True
            return ignore_errors

        # Update the method
        method = self.method

        # Check if import method is allowed in strategy
        strategy = self.strategy
        if not isinstance(strategy, (list, tuple)):
            strategy = [strategy]
        if method not in strategy:
            self.error = current.ERROR.NOT_PERMITTED
            self.skip = True
            return True

        # Check mtime and mci
        table = self.table
        original = self.original
        original_mtime = None
        original_mci = 0
        if original:
            if hasattr(table, MTIME):
                original_mtime = s3_utc(original[MTIME])
            if hasattr(table, MCI):
                original_mci = original[MCI]
            original_deleted = "deleted" in original and original.deleted
        else:
            original_deleted = False

        # Detect conflicts
        job = self.job
        original_modified = True
        self.modified = True
        self.conflict = False
        last_sync = s3_utc(job.last_sync)
        if last_sync:
            if original_mtime and original_mtime < last_sync:
                original_modified = False
            if self.mtime and self.mtime < last_sync:
                self.modified = False
            if self.modified and original_modified:
                self.conflict = True
        if self.conflict and method in (UPDATE, DELETE, MERGE):
            if job.onconflict:
                job.onconflict(self)

        if self.data is not None:
            data = table._filter_fields(self.data, id=True)
        else:
            data = Storage()

        # Update policy
        if isinstance(self.update_policy, dict):
            def update_policy(f):
                setting = self.update_policy
                p = setting.get(f,
                    setting.get("__default__", THIS))
                if p not in POLICY:
                    return THIS
                return p
        else:
            def update_policy(f):
                p = self.update_policy
                if p not in POLICY:
                    return THIS
                return p

        # Log this item
        if callable(job.log):
            job.log(self)

        tablename = self.tablename
        enforce_realm_update = False

        # Update existing record
        if method == UPDATE:

            if original:
                if original_deleted:
                    policy = update_policy(None)
                    if policy == NEWER and \
                       original_mtime and original_mtime > self.mtime or \
                       policy == MASTER and \
                       (original_mci == 0 or self.mci != 1):
                        self.skip = True
                        return True

                for f in list(data.keys()):
                    if f in original:
                        # Check if unchanged
                        if type(original[f]) is datetime.datetime:
                            if s3_utc(data[f]) == s3_utc(original[f]):
                                del data[f]
                                continue
                        else:
                            if data[f] == original[f]:
                                del data[f]
                                continue
                    remove = False
                    policy = update_policy(f)
                    if policy == THIS:
                        remove = True
                    elif policy == NEWER:
                        if original_mtime and original_mtime > self.mtime:
                            remove = True
                    elif policy == MASTER:
                        if original_mci == 0 or self.mci != 1:
                            remove = True
                    if remove:
                        del data[f]

                if original_deleted:
                    # Undelete re-imported records
                    data["deleted"] = False
                    if hasattr(table, "deleted_fk"):
                        data["deleted_fk"] = ""

                    # Set new author stamp
                    if hasattr(table, "created_by"):
                        data["created_by"] = table.created_by.default
                    if hasattr(table, "modified_by"):
                        data["modified_by"] = table.modified_by.default

                    # Restore defaults for foreign keys
                    for fieldname in table.fields:
                        field = table[fieldname]
                        default = field.default
                        if str(field.type)[:9] == "reference" and \
                           fieldname not in data and \
                           default is not None:
                            data[fieldname] = default

                    # Enforce update of realm entity
                    enforce_realm_update = True

            if not self.skip and not self.conflict and \
               (len(data) or self.components or self.references):
                if self.uid and hasattr(table, UID):
                    data[UID] = self.uid
                if MTIME in table:
                    data[MTIME] = self.mtime
                if MCI in data:
                    # retain local MCI on updates
                    del data[MCI]
                query = (table._id == self.id)
                try:
                    db(query).update(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return ignore_errors
                else:
                    self.committed = True
            else:
                # Nothing to update
                self.committed = True

        # Create new record
        elif method == CREATE:

            # Do not apply field policy to UID and MCI
            if UID in data:
                del data[UID]
            if MCI in data:
                del data[MCI]

            for f in data:
                if update_policy(f) == MASTER and self.mci != 1:
                    del data[f]

            if len(data) or self.components or self.references:

                # Restore UID and MCI
                if self.uid and UID in table.fields:
                    data[UID] = self.uid
                if MCI in table.fields:
                    data[MCI] = self.mci

                # Insert the new record
                try:
                    success = table.insert(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return ignore_errors
                if success:
                    self.id = success
                    self.committed = True

            else:
                # Nothing to create
                self.skip = True
                return True

        # Delete local record
        elif method == DELETE:

            if original:
                if original_deleted:
                    self.skip = True
                policy = update_policy(None)
                if policy == THIS:
                    self.skip = True
                elif policy == NEWER and \
                     (original_mtime and original_mtime > self.mtime):
                    self.skip = True
                elif policy == MASTER and \
                     (original_mci == 0 or self.mci != 1):
                    self.skip = True
            else:
                self.skip = True

            if not self.skip and not self.conflict:

                resource = s3db.resource(tablename, id=self.id)
                # Use cascade=True so that the deletion can be
                # rolled back (e.g. trial phase, subsequent failure)
                success = resource.delete(cascade=True)
                if resource.error:
                    self.error = resource.error
                    self.skip = True
                    return ignore_errors

            return True

        # Merge records
        elif method == MERGE:

            if UID not in table.fields:
                self.skip = True
            elif original:
                if original_deleted:
                    self.skip = True
                policy = update_policy(None)
                if policy == THIS:
                    self.skip = True
                elif policy == NEWER and \
                     (original_mtime and original_mtime > self.mtime):
                    self.skip = True
                elif policy == MASTER and \
                     (original_mci == 0 or self.mci != 1):
                    self.skip = True
            else:
                self.skip = True

            if not self.skip and not self.conflict:

                row = db(table[UID] == data[xml.REPLACEDBY]) \
                                        .select(table._id, limitby=(0, 1)) \
                                        .first()
                if row:
                    original_id = row[table._id]
                    resource = s3db.resource(tablename,
                                             id = [original_id, self.id],
                                             )
                    try:
                        success = resource.merge(original_id, self.id)
                    except:
                        self.error = sys.exc_info()[1]
                        self.skip = True
                        return ignore_errors
                    if success:
                        self.committed = True
                else:
                    self.skip = True

            return True

        else:
            raise RuntimeError("unknown import method: %s" % method)

        # Audit + onaccept on successful commits
        if self.committed:

            # Create a pseudo-form for callbacks
            form = Storage()
            form.method = method
            form.table = table
            form.vars = self.data
            prefix, name = tablename.split("_", 1)
            if self.id:
                form.vars.id = self.id

            # Audit
            current.audit(method, prefix, name,
                          form = form,
                          record = self.id,
                          representation = "xml",
                          )

            # Prevent that record post-processing breaks time-delayed
            # synchronization by implicitly updating "modified_on"
            if MTIME in table.fields:
                modified_on = table[MTIME]
                modified_on_update = modified_on.update
                modified_on.update = None
            else:
                modified_on_update = None

            # Update super entity links
            s3db.update_super(table, form.vars)
            if method == CREATE:
                # Set record owner
                current.auth.s3_set_record_owner(table, self.id)
            elif method == UPDATE:
                # Update realm
                update_realm = enforce_realm_update or \
                               s3db.get_config(table, "update_realm")
                if update_realm:
                    current.auth.set_realm_entity(table, self.id,
                                                  force_update = True,
                                                  )
            # Onaccept
            key = "%s_onaccept" % method
            onaccept = current.deployment_settings.get_import_callback(tablename, key)
            if onaccept:
                callback(onaccept, form, tablename=tablename)

            # Restore modified_on.update
            if modified_on_update is not None:
                modified_on.update = modified_on_update

        # Update referencing items
        if self.update and self.id:
            for u in self.update:

                # The other import item that shall be updated
                item = u.get("item")
                if not item:
                    continue

                # The field in the other item that shall be updated
                field = u.get("field")
                if isinstance(field, (list, tuple)):
                    # The field references something else than the
                    # primary key of this table => look it up
                    pkey, fkey = field
                    query = (table.id == self.id)
                    row = db(query).select(table[pkey], limitby=(0, 1)).first()
                    ref_id = row[pkey]
                else:
                    # The field references the primary key of this table
                    pkey, fkey = None, field
                    ref_id = self.id

                if "refkey" in u:
                    # Target field is a JSON object
                    item._update_objref(fkey, u["refkey"], ref_id)
                else:
                    # Target field is a reference or list:reference
                    item._update_reference(fkey, ref_id)

        return True

    # -------------------------------------------------------------------------
    def _dynamic_defaults(self, data):
        """
            Applies dynamic defaults from any keys in data that start with
            an underscore, used only for new records and only if the respective
            field is not populated yet.

            @param data: the data dict
        """

        for k, v in list(data.items()):
            if k[0] == "_":
                fn = k[1:]
                if fn in self.table.fields and fn not in data:
                    data[fn] = v

    # -------------------------------------------------------------------------
    def _mandatory_fields(self):

        job = self.job

        mandatory = None
        tablename = self.tablename

        mfields = job.mandatory_fields
        if tablename in mfields:
            mandatory = mfields[tablename]

        if mandatory is None:
            mandatory = []
            for field in self.table:
                if field.default is not None:
                    continue
                requires = field.requires
                if requires:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    if isinstance(requires[0], IS_EMPTY_OR):
                        continue
                    error = field.validate("")[1]
                    if error:
                        mandatory.append(field.name)
            mfields[tablename] = mandatory

        return mandatory

    # -------------------------------------------------------------------------
    def _resolve_references(self):
        """
            Resolve the references of this item (=look up all foreign
            keys from other items of the same job). If a foreign key
            is not yet available, it will be scheduled for later update.
        """

        table = self.table
        if not table:
            return

        db = current.db
        items = self.job.items
        for reference in self.references:

            entry = reference.entry
            if not entry:
                continue

            field = reference.field

            # Resolve key tuples
            if isinstance(field, (list, tuple)):
                pkey, fkey = field
            else:
                pkey, fkey = ("id", field)

            f = table[fkey]
            if f.type == "json":
                is_json = True
                objref = reference.objref
                if not objref:
                    objref = S3ObjectReferences(self.data.get(fkey))
                refkey = reference.refkey
                if not refkey:
                    continue
            else:
                is_json = False
                refkey = objref = None
                ktablename, _, multiple = s3_get_foreign_key(f)
                if not ktablename:
                    continue

            # Get the lookup table
            if entry.tablename:
                ktablename = entry.tablename
            try:
                ktable = current.s3db[ktablename]
            except AttributeError:
                continue

            # Resolve the foreign key (value)
            item = None
            fk = entry.id
            if entry.item_id:
                item = items[entry.item_id]
                if item:
                    if item.original and \
                       item.original.get("deleted") and \
                       not item.committed:
                        # Original is deleted and has not been updated
                        fk = None
                    else:
                        fk = item.id
            if fk and pkey != "id":
                row = db(ktable._id == fk).select(ktable[pkey],
                                                  limitby=(0, 1)).first()
                if not row:
                    fk = None
                    continue
                else:
                    fk = row[pkey]

            # Update record data
            if fk:
                if is_json:
                    objref.resolve(refkey[0], refkey[1], refkey[2], fk)
                elif multiple:
                    val = self.data.get(fkey, [])
                    if fk not in val:
                        val.append(fk)
                    self.data[fkey] = val
                else:
                    self.data[fkey] = fk
            else:
                if fkey in self.data and not multiple and not is_json:
                    del self.data[fkey]
                if item:
                    update = {"item": self, "field": fkey}
                    if is_json:
                        update["refkey"] = refkey
                    item.update.append(update)

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

        table = self.table
        record_id = self.id

        if not value or not table or not record_id or not self.permitted:
            return

        db = current.db
        update = None

        fieldtype = str(table[field].type)
        if fieldtype.startswith("list:reference"):
            query = (table._id == record_id)
            record = db(query).select(table[field],
                                      limitby = (0, 1),
                                      ).first()
            if record:
                values = record[field]
                if value not in values:
                    values.append(value)
                    update = {field: values}
        else:
            update = {field: value}

        if update:
            if "modified_on" in table.fields:
                update["modified_on"] = table.modified_on
            if "modified_by" in table.fields:
                update["modified_by"] = table.modified_by
            db(table._id == record_id).update(**update)

    # -------------------------------------------------------------------------
    def _update_objref(self, field, refkey, value):
        """
            Update object references in a JSON field

            @param fieldname: the name of the JSON field
            @param refkey: the reference key, a tuple (tablename, uidtype, uid)
            @param value: the foreign key value
        """


        table = self.table
        record_id = self.id

        if not value or not table or not record_id or not self.permitted:
            return

        db = current.db
        query = (table._id == record_id)
        record = db(query).select(table._id,
                                  table[field],
                                  limitby = (0, 1),
                                  ).first()
        if record:
            obj = record[field]

            tn, uidtype, uid = refkey
            S3ObjectReferences(obj).resolve(tn, uidtype, uid, value)

            update = {field: obj}
            if "modified_on" in table.fields:
                update["modified_on"] = table.modified_on
            if "modified_by" in table.fields:
                update["modified_by"] = table.modified_by
            record.update_record(**update)

    # -------------------------------------------------------------------------
    def store(self, item_table=None):
        """
            Store this item in the DB
        """

        if item_table is None:
            return None

        item_id = self.item_id
        db = current.db
        row = db(item_table.item_id == item_id).select(item_table.id,
                                                       limitby=(0, 1)
                                                       ).first()
        if row:
            record_id = row.id
        else:
            record_id = None

        record = Storage(job_id = self.job.job_id,
                         item_id = item_id,
                         tablename = self.tablename,
                         record_uid = self.uid,
                         error = self.error or "",
                         )

        if self.element is not None:
            element_str = current.xml.tostring(self.element,
                                               xml_declaration=False)
            record.update(element=element_str)

        self_data = self.data
        if self_data is not None:
            table = self.table
            fields = table.fields
            data = Storage()
            for f in self_data.keys():
                if f not in fields:
                    continue
                field = table[f]
                field_type = str(field.type)
                if field_type == "id" or s3_has_foreign_key(field):
                    continue
                data_ = self_data[f]
                if isinstance(data_, Field):
                    # Not picklable
                    # This is likely to be a modified_on to avoid updating this field, which skipping does just fine too
                    continue
                data.update({f: data_})
            record["data"] = pickle.dumps(data)

        ritems = []
        for reference in self.references:
            field = reference.field
            entry = reference.entry
            store_entry = None
            if entry:
                if entry.item_id is not None:
                    store_entry = {"field": field,
                                   "item_id": str(entry.item_id),
                                   }
                elif entry.uid is not None:
                    store_entry = {"field": field,
                                   "tablename": entry.tablename,
                                   "uid": str(entry.uid),
                                   }
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
            self.data = pickle.loads(row.data)
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
        s3db = current.s3db
        try:
            table = s3db[tablename]
        except AttributeError:
            self.error = current.ERROR.BAD_RESOURCE
            return False
        else:
            self.table = table
            self.tablename = tablename
        original = S3Resource.original(table, self.data,
                                       mandatory=self._mandatory_fields())
        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            if not current.response.s3.synchronise_uuids and UID in original:
                self.uid = self.data[UID] = original[UID]
        self.error = row.error
        postprocess = s3db.get_config(self.tablename, "xml_post_parse")
        if postprocess:
            postprocess(self.element, self.data)
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
    def __init__(self, table,
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

        self._uidmap = None

        # Mandatory fields
        self.mandatory_fields = Storage()

        self.elements = Storage()
        self.items = Storage()
        self.references = []

        self.job_table = None
        self.item_table = None

        self.count = 0 # total number of records imported
        self.created = [] # IDs of created records
        self.updated = [] # IDs of updated records
        self.deleted = [] # IDs of deleted records

        self.log = None

        # Import strategy
        if strategy is None:
            METHOD = S3ImportItem.METHOD
            strategy = [METHOD.CREATE,
                        METHOD.UPDATE,
                        METHOD.DELETE,
                        METHOD.MERGE,
                        ]
        if not isinstance(strategy, (tuple, list)):
            strategy = [strategy]
        self.strategy = strategy

        # Update policy (default=always update)
        if update_policy:
            self.update_policy = update_policy
        else:
            self.update_policy = S3ImportItem.POLICY.OTHER
        # Conflict resolution policy (default=always update)
        if conflict_policy:
            self.conflict_policy = conflict_policy
        else:
            self.conflict_policy = S3ImportItem.POLICY.OTHER

        # Synchronization settings
        self.mtime = None
        self.last_sync = last_sync
        self.onconflict = onconflict

        if job_id:
            self.__define_tables()
            jobtable = self.job_table
            if str(job_id).isdigit():
                query = (jobtable.id == job_id)
            else:
                query = (jobtable.job_id == job_id)
            row = current.db(query).select(jobtable.job_id,
                                           jobtable.tablename,
                                           limitby=(0, 1)).first()
            if not row:
                raise SyntaxError("Job record not found")
            self.job_id = row.job_id
            self.second_pass = True
            if not self.table:
                tablename = row.tablename
                try:
                    table = current.s3db[tablename]
                except AttributeError:
                    pass
        else:
            self.job_id = uuid.uuid4() # unique ID for this job
            self.second_pass = False

    # -------------------------------------------------------------------------
    @property
    def uidmap(self):
        """
            Map uuid/tuid => element, for faster reference lookups
        """

        uidmap = self._uidmap
        tree = self.tree

        if uidmap is None and tree is not None:

            root = tree if isinstance(tree, etree._Element) else tree.getroot()

            xml = current.xml
            UUID = xml.UID
            TUID = xml.ATTRIBUTE.tuid

            elements = root.xpath(".//%s" % xml.TAG.resource)
            self._uidmap = uidmap = {UUID: {},
                                     TUID: {},
                                     }
            uuidmap = uidmap[UUID]
            tuidmap = uidmap[TUID]
            for element in elements:
                r_uuid = element.get(UUID)
                if r_uuid and r_uuid not in uuidmap:
                    uuidmap[r_uuid] = element
                r_tuid = element.get(TUID)
                if r_tuid and r_tuid not in tuidmap:
                    tuidmap[r_tuid] = element

        return uidmap

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

            @return: a unique identifier for the new item, or None if there
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

            s3db = current.s3db
            components = s3db.get_components(table, names=components)
            super_keys = s3db.get_super_keys(table)

            cnames = Storage()
            cinfos = Storage()
            for alias in components:

                component = components[alias]

                ctable = component.table
                if ctable._id != "id" and "instance_type" in ctable.fields:
                    # Super-entities cannot be imported to directly => skip
                    continue

                # Determine the keys
                pkey = component.pkey

                if pkey != table._id.name and pkey not in super_keys:
                    # Pseudo-component cannot be imported => skip
                    continue

                if component.linktable:
                    ctable = component.linktable
                    fkey = component.lkey
                else:
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
                                                      first = True,
                                                      )
            add_item = self.add_item
            xml = current.xml
            UID = xml.UID
            for celement in xml.components(element, names=list(cnames.keys())):

                # Get the component tablename
                ctablename = celement.get(xml.ATTRIBUTE.name, None)
                if not ctablename or ctablename not in cnames:
                    continue

                # Get the component alias (for disambiguation)
                calias = celement.get(xml.ATTRIBUTE.alias, None)
                if calias is None:
                    aliases = cnames[ctablename]
                    if len(aliases) == 1:
                        calias = aliases[0]
                    else:
                        calias = ctablename.split("_", 1)[1]
                if (ctablename, calias) not in cinfos:
                    continue
                else:
                    cinfo = cinfos[(ctablename, calias)]

                component = cinfo.component
                ctable = cinfo.ctable

                pkey = cinfo.pkey
                fkey = cinfo.fkey

                original = None

                if not component.multiple:
                    # Single-component: skip all subsequent items after
                    # the first under the same master record
                    if not cinfo.first:
                        continue
                    cinfo.first = False

                    # Single component = the first component record
                    # under the master record is always the original,
                    # only relevant if the master record exists in
                    # the db and hence item.id is not None
                    if item.id:
                        db = current.db
                        query = (table.id == item.id) & \
                                (table[pkey] == ctable[fkey])
                        if UID in ctable.fields:
                            # Load only the UUID now, parse will load any
                            # required data later
                            row = db(query).select(ctable[UID],
                                                   limitby=(0, 1)).first()
                            if row:
                                original = row[UID]
                        else:
                            # Not nice, but a rare edge-case
                            original = db(query).select(ctable.ALL,
                                                        limitby=(0, 1)).first()

                # Recurse
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

            lookahead = self.lookahead
            directory = self.directory

            # Handle references
            table = item.table
            data = item.data
            tree = self.tree

            def schedule(reference):
                """ Schedule a referenced item for implicit import """
                entry = reference.entry
                if entry and entry.element is not None and not entry.item_id:
                    item_id = add_item(element=entry.element)
                    if item_id:
                        entry.item_id = item_id

            # Foreign key fields in table
            if tree is not None:
                fields = [table[f] for f in table.fields]
                rfields = [f for f in fields if s3_has_foreign_key(f)]
                item.references = lookahead(element,
                                            table = table,
                                            fields = rfields,
                                            tree = tree,
                                            directory = directory,
                                            )
                for reference in item.references:
                    schedule(reference)

            references = item.references
            rappend = references.append

            # Parent reference
            if parent is not None:
                entry = Storage(item_id = parent.item_id,
                                element = parent.element,
                                tablename = parent.tablename,
                                )
                rappend(Storage(field = joinby,
                                entry = entry,
                                ))

            # References in JSON field data
            json_references = s3db.get_config(table, "json_references")
            if json_references:
                if json_references is True:
                    # Discover references in any JSON fields
                    fields = table.fields
                else:
                    # Discover references in fields specified by setting
                    fields = json_references
                    if not isinstance(fields, (tuple, list)):
                        fields = [fields]
                for fieldname in fields:
                    value = data.get(fieldname)
                    field = table[fieldname]
                    if value and field.type == "json":
                        objref = S3ObjectReferences(value)
                        for ref in objref.refs:
                            rl = lookahead(None,
                                           tree = tree,
                                           directory = directory,
                                           lookup = ref,
                                           )
                            if rl:
                                reference = rl[0]
                                schedule(reference)
                                rappend(Storage(field = fieldname,
                                                objref = objref,
                                                refkey = ref,
                                                entry = reference.entry,
                                                ))

            # Replacement reference
            deleted = data.get(xml.DELETED, False)
            if deleted:
                fieldname = xml.REPLACEDBY
                replaced_by = data.get(fieldname)
                if replaced_by:
                    rl = lookahead(element,
                                   tree = tree,
                                   directory = directory,
                                   lookup = (table, replaced_by),
                                   )
                    if rl:
                        reference = rl[0]
                        schedule(reference)
                        rappend(Storage(field = fieldname,
                                        entry = reference.entry,
                                        ))

        return item.item_id

    # -------------------------------------------------------------------------
    def lookahead(self,
                  element,
                  table=None,
                  fields=None,
                  tree=None,
                  directory=None,
                  lookup=None):
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
        rlappend = reference_list.append

        root = None
        if tree is not None:
            root = tree if isinstance(tree, etree._Element) else tree.getroot()
        uidmap = self.uidmap

        references = [lookup] if lookup else element.findall("reference")
        for reference in references:
            if lookup:
                field = None
                if element is None:
                    tablename, attr, uid = reference
                    ktable = s3db.table(tablename)
                    if ktable is None:
                        continue
                    uids = [import_uid(uid)] if attr == "uuid" else [uid]
                else:
                    tablename = element.get(ATTRIBUTE.name, None)
                    ktable, uid = reference
                    attr = UID
                    uids = [import_uid(uid)]
            else:
                field = reference.get(ATTRIBUTE.field, None)

                # Ignore references without valid field-attribute
                if not field or field not in fields or field not in table:
                    continue

                # Find the key table
                ktablename, _, multiple = s3_get_foreign_key(table[field])
                if not ktablename:
                    continue
                try:
                    ktable = s3db[ktablename]
                except AttributeError:
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
            id_map = {}
            if attr == UID and uids:
                if len(uids) == 1:
                    uid = import_uid(uids[0])
                    query = (ktable[UID] == uid)
                    record = db(query).select(ktable.id,
                                              cacheable = True,
                                              limitby = (0, 1),
                                              ).first()
                    if record:
                        id_map[uid] = record.id
                else:
                    uids_ = [import_uid(uid) for uid in uids]
                    query = (ktable[UID].belongs(uids_))
                    records = db(query).select(ktable.id,
                                               ktable[UID],
                                               limitby = (0, len(uids_)),
                                               )
                    for r in records:
                        id_map[r[UID]] = r.id

            if not uids:
                # Anonymous reference: <resource> inside the element
                expr = './/%s[@%s="%s"]' % (TAG.resource,
                                            ATTRIBUTE.name,
                                            tablename,
                                            )
                relements = reference.xpath(expr)
                if relements and not multiple:
                    relements = relements[:1]

            elif root is not None:

                for uid in uids:

                    entry = None

                    # Entry already in directory?
                    if directory is not None:
                        entry = directory.get((tablename, attr, uid))

                    if not entry:
                        e = uidmap[attr].get(uid) if uidmap else None
                        if e is not None:
                            # Element in the source => append to relements
                            relements.append(e)
                        else:
                            # No element found, see if original record exists
                            _uid = import_uid(uid)
                            if _uid and _uid in id_map:
                                _id = id_map[_uid]
                                entry = Storage(tablename = tablename,
                                                element = None,
                                                uid = uid,
                                                id = _id,
                                                item_id = None,
                                                )
                                rlappend(Storage(field = field,
                                                 element = reference,
                                                 entry = entry,
                                                 ))
                            else:
                                continue
                    else:
                        rlappend(Storage(field = field,
                                         element = reference,
                                         entry = entry,
                                         ))

            # Create entries for all newly found elements
            for relement in relements:
                uid = relement.get(attr, None)
                if attr == UID:
                    _uid = import_uid(uid)
                    _id = _uid and id_map and id_map.get(_uid, None) or None
                else:
                    _uid = None
                    _id = None
                entry = Storage(tablename = tablename,
                                element = relement,
                                uid = uid,
                                id = _id,
                                item_id = None,
                                )
                # Add entry to directory
                if uid and directory is not None:
                    directory[(tablename, attr, uid)] = entry
                # Append the entry to the reference list
                rlappend(Storage(field = field,
                                 element = reference,
                                 entry = entry,
                                 ))

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
    def commit(self, ignore_errors=False, log_items=None):
        """
            Commit the import job to the DB

            @param ignore_errors: skip any items with errors
                                  (does still report the errors)
            @param log_items: callback function to log import items
                              before committing them
        """

        ATTRIBUTE = current.xml.ATTRIBUTE
        METHOD = S3ImportItem.METHOD

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

        self.log = log_items
        failed = False
        for item_id in import_list:
            item = items[item_id]
            error = None

            if item.accepted is not False:
                logged = False
                success = item.commit(ignore_errors=ignore_errors)
            else:
                # Field validation failed
                logged = True
                success = ignore_errors

            if not success:
                failed = True

            error = item.error
            if error:
                current.log.error(error)
                self.error = error
                element = item.element
                if element is not None:
                    if not element.get(ATTRIBUTE.error, False):
                        element.set(ATTRIBUTE.error, s3_unicode(self.error))
                    if not logged:
                        self.error_tree.append(deepcopy(element))

            elif item.tablename == tablename:
                count += 1
                if mtime is None or item.mtime > mtime:
                    mtime = item.mtime
                if item.id:
                    if item.method == METHOD.CREATE:
                        cappend(item.id)
                    elif item.method == METHOD.UPDATE:
                        updated.append(item.id)
                    elif item.method in (METHOD.MERGE, METHOD.DELETE):
                        deleted.append(item.id)

        if failed:
            return False

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
            db.define_table(cls.JOB_TABLE_NAME,
                            Field("job_id", length=128,
                                  unique=True,
                                  notnull=True),
                            Field("tablename"),
                            Field("timestmp", "datetime",
                                  default=datetime.datetime.utcnow()))

        return db[cls.JOB_TABLE_NAME]

    # -------------------------------------------------------------------------
    @classmethod
    def define_item_table(cls):

        db = current.db
        if cls.ITEM_TABLE_NAME not in db:
            db.define_table(cls.ITEM_TABLE_NAME,
                            Field("item_id", length=128,
                                  unique=True,
                                  notnull=True),
                            Field("job_id", length=128),
                            Field("tablename", length=128),
                            #Field("record_id", "integer"),
                            Field("record_uid"),
                            Field("error", "text"),
                            Field("data", "blob"),
                            Field("element", "text"),
                            Field("ritems", "list:string"),
                            Field("citems", "list:string"),
                            Field("parent", length=128))

        return db[cls.ITEM_TABLE_NAME]

    # -------------------------------------------------------------------------
    def store(self):
        """
            Store this job and all its items in the job table
        """

        db = current.db

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
        except AttributeError:
            pass
        else:
            record.update(tablename=tablename)
        for item in self.items.values():
            item.store(item_table=self.item_table)
        if record_id:
            db(jobtable.id == record_id).update(**record)
        else:
            record_id = jobtable.insert(**record)

        return record_id

    # -------------------------------------------------------------------------
    def get_tree(self):
        """
            Reconstruct the element tree of this job
        """

        if self.tree is not None:
            return self.tree
        else:
            xml = current.xml
            ATTRIBUTE = xml.ATTRIBUTE
            UID = xml.UID
            root = etree.Element(xml.TAG.root)
            for item in self.items.values():
                element = item.element
                if element is not None and not item.parent:
                    if item.tablename == self.table._tablename or \
                       element.get(UID, None) or \
                       element.get(ATTRIBUTE.tuid, None):
                        root.append(deepcopy(element))
            return etree.ElementTree(root)

    # -------------------------------------------------------------------------
    def delete(self):
        """
            Delete this job and all its items from the job table
        """

        db = current.db

        #current.log.debug("Deleting job ID=%s" % self.job_id)

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
                        except AttributeError:
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
                parent = self.items[item.load_parent]
                if parent is None:
                    # Parent has been removed
                    item.skip = True
                else:
                    item.parent = parent
                item.load_parent = None

# =============================================================================
class S3ObjectReferences(object):
    """
        Utility to discover and resolve references in a JSON object;
        handles both uuid- and tuid-based references

        - traverses the object to find dict items of any of these formats:
                "$k_<name>": {"r": <tablename>, "u": <uuid>}
                "$k_<name>": {"@resource": <tablename>, "@uuid": <uuid>}
                "$k_<name>": {"r": <tablename>, "t": <tuid>}
                "$k_<name>": {"@resource": <tablename>, "@tuid": <tuid>}

        - resolve() replaces them with:
                "<name>": <db_id>

        @example:
            # Get a list of all references in obj
            refs = S3ObjectReferences(obj).refs
        @example
            # Resolve a reference in obj
            S3ObjectReferences(obj).resolve("req_req", "uuid", "REQ1", 57)
    """

    TABLENAME_KEYS = ("@resource", "r")
    UUID_KEYS = ("@uuid", "u")
    TUID_KEYS = ("@tuid", "t")

    def __init__(self, obj):
        """
            Constructor

            @param obj: the object to inspect (parsed)
        """

        self.obj = obj

        self._refs = None
        self._objs = None

    # -------------------------------------------------------------------------
    @property
    def refs(self):
        """
            List of references discovered in the object (lazy property)

            @returns: a list of tuples (tablename, uidtype, uid)
        """

        if self._refs is None:
            self._refs = []
            self._objs = {}
            self._traverse(self.obj)
        return self._refs

    # -------------------------------------------------------------------------
    @property
    def objs(self):
        """
            A dict with pointers to the references inside the object

            @returns: a dict {(tablename, uidtype, uid): (obj, key)}
        """

        if self._objs is None:
            self._refs = []
            self._objs = {}
            self._traverse(self.obj)
        return self._objs

    # -------------------------------------------------------------------------
    def _traverse(self, obj):
        """
            Traverse a (possibly nested) object and find all references,
            populates self.refs and self.objs

            @param obj: the object to inspect
        """

        refs = self._refs
        objs = self._objs

        if type(obj) is list:
            for item in obj:
                self._traverse(item)

        elif type(obj) is dict:

            for key, value in obj.items():

                if key[:3] == "$k_" and type(value) is dict:

                    tablename = uid = uid_type = None

                    for k in self.TABLENAME_KEYS:
                        tablename = value.get(k)
                        if tablename:
                            break
                    if tablename:
                        for k in self.UUID_KEYS:
                            uid = value.get(k)
                            if uid:
                                uid_type = "uuid"
                                break
                    if tablename and not uid:
                        for k in self.TUID_KEYS:
                            uid = value.get(k)
                            if uid:
                                uid_type = "tuid"
                                break
                    if not tablename or not uid:
                        self._traverse(value)
                    else:
                        ref = (tablename, uid_type, uid)
                        if ref not in objs:
                            refs.append(ref)
                            objs[ref] = [(obj, key)]
                        else:
                            objs[ref].append((obj, key))
                else:
                    self._traverse(value)

    # -------------------------------------------------------------------------
    def resolve(self, tablename, uidtype, uid, value):
        """
            Resolve a reference in self.obj with the given value; will
            resolve all occurences of the reference

            @param tablename: the referenced table
            @param uidtype: the type of uid (uuid or tuid)
            @param uid: the uuid or tuid
            @param value: the value to resolve the reference
        """

        items = self.objs.get((tablename, uidtype, uid))
        if items:
            for obj, key in items:
                if len(key) > 3:
                    obj[key[3:]] = value
                obj.pop(key, None)

# =============================================================================
class S3Duplicate(object):
    """ Standard deduplicator method """

    def __init__(self,
                 primary=None,
                 secondary=None,
                 ignore_case=True,
                 ignore_deleted=False):
        """
            Constructor

            @param primary: list or tuple of primary fields to find a
                            match, must always match (mandatory, defaults
                            to "name" field)
            @param secondary: list or tuple of secondary fields to
                              find a match, must match if values are
                              present in the import item
            @param ignore_case: ignore case for string/text fields
            @param ignore_deleted: do not match deleted records

            @ToDo: Fuzzy option to do a LIKE search
        """

        if not primary:
            primary = ("name",)
        self.primary = set(primary)

        if not secondary:
            self.secondary = set()
        else:
            self.secondary = set(secondary)

        self.ignore_case = ignore_case
        self.ignore_deleted = ignore_deleted

    # -------------------------------------------------------------------------
    def __call__(self, item):
        """
            Entry point for importer

            @param item: the import item

            @return: the duplicate Row if match found, otherwise None

            @raise SyntaxError: if any of the query fields doesn't exist
                                in the item table
        """

        data = item.data
        table = item.table

        query = None
        error = "Invalid field for duplicate detection: %s (%s)"

        # Primary query (mandatory)
        primary = self.primary
        for fname in primary:

            if fname not in table.fields:
                raise SyntaxError(error % (fname, table))

            field = table[fname]
            value = data.get(fname)

            q = self.match(field, value)
            query = q if query is None else query & q

        # Secondary queries (optional)
        secondary = self.secondary
        for fname in secondary:

            if fname not in table.fields:
                raise SyntaxError(error % (fname, table))

            field = table[fname]
            value = data.get(fname)
            if value:
                query &= self.match(field, value)

        # Ignore deleted records?
        if self.ignore_deleted and "deleted" in table.fields:
            query &= (table.deleted != True)

        # Find a match
        duplicate = current.db(query).select(table._id,
                                             limitby = (0, 1)).first()

        if duplicate:
            # Match found: Update import item
            item.id = duplicate[table._id]
            if not data.deleted:
                item.method = item.METHOD.UPDATE

        # For uses outside of imports:
        return duplicate

    # -------------------------------------------------------------------------
    def match(self, field, value):
        """
            Helper function to generate a match-query

            @param field: the Field
            @param value: the value

            @return: a Query
        """

        ftype = str(field.type)
        ignore_case = self.ignore_case

        if ignore_case and \
           hasattr(value, "lower") and ftype in ("string", "text"):
            # NB Must convert to unicode before lower() in order to correctly
            #    convert certain unicode-characters (e.g. İ=>i, or Ẽ=>ẽ)
            # => PostgreSQL LOWER() on Windows may not convert correctly,
            #    which seems to be a locale issue:
            #    http://stackoverflow.com/questions/18507589/the-lower-function-on-international-characters-in-postgresql
            # => works fine on Debian servers if the locale is a .UTF-8 before
            #    the Postgres cluster is created
            query = (field.lower() == s3_str(s3_unicode(value).lower()))
        else:
            query = (field == value)

        return query

# =============================================================================
class S3BulkImporter(object):
    """
        Import CSV files of data to pre-populate the database.
        Suitable for use in Testing, Demos & Simulations

        http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/PrePopulate
    """

    def __init__(self):
        """ Constructor """

        import csv
        from xml.sax.saxutils import unescape

        self.csv = csv
        self.unescape = unescape
        self.tasks = []
        # Some functions refer to a different resource
        self.alternateTables = {
            "hrm_group_membership": {"tablename": "pr_group_membership",
                                     "prefix": "pr",
                                     "name": "group_membership"},
            "hrm_person": {"tablename": "pr_person",
                           "prefix": "pr",
                           "name": "person"},
            "member_person": {"tablename": "pr_person",
                              "prefix": "pr",
                              "name": "person"},
            }
        # Keep track of which resources have been customised so we don't do this twice
        self.customised = []
        self.errorList = []
        self.resultList = []

    # -------------------------------------------------------------------------
    def load_descriptor(self, path):
        """
            Load the descriptor file and then all the import tasks in that file
            into the task property.
            The descriptor file is the file called tasks.cfg in path.
            The file consists of a comma separated list of:
            module, resource name, csv filename, xsl filename.
        """

        source = open(os.path.join(path, "tasks.cfg"), "r")
        values = self.csv.reader(source)
        for details in values:
            if details == []:
                continue
            prefix = details[0][0].strip('" ')
            if prefix == "#": # comment
                continue
            if prefix == "*": # specialist function
                self.extract_other_import_line(path, details)
            else: # standard CSV importer
                self.extract_csv_import_line(path, details)

    # -------------------------------------------------------------------------
    def extract_csv_import_line(self, path, details):
        """
            Extract the details for a CSV Import Task
        """

        argCnt = len(details)
        if argCnt == 4 or argCnt == 5:
            # Remove any spaces and enclosing double quote
            mod = details[0].strip('" ')
            res = details[1].strip('" ')
            folder = current.request.folder

            csvFileName = details[2].strip('" ')
            if csvFileName[:7] == "http://":
                csv = csvFileName
            else:
                (csvPath, csvFile) = os.path.split(csvFileName)
                if csvPath != "":
                    path = os.path.join(folder,
                                        "modules",
                                        "templates",
                                        csvPath)
                    # @todo: deprecate this block once migration completed
                    if not os.path.exists(path):
                        # Non-standard location (legacy template)?
                        path = os.path.join(folder,
                                            "private",
                                            "templates",
                                            csvPath)
                csv = os.path.join(path, csvFile)

            xslFileName = details[3].strip('" ')
            templateDir = os.path.join(folder,
                                       "static",
                                       "formats",
                                       "s3csv")
            # Try the module directory in the templates directory first
            xsl = os.path.join(templateDir, mod, xslFileName)
            if os.path.exists(xsl) == False:
                # Now try the templates directory
                xsl = os.path.join(templateDir, xslFileName)
                if os.path.exists(xsl) == False:
                    # Use the same directory as the csv file
                    xsl = os.path.join(path, xslFileName)
                    if os.path.exists(xsl) == False:
                        self.errorList.append(
                        "Failed to find a transform file %s, Giving up." % xslFileName)
                        return

            if argCnt == 5:
                extra_data = details[4]
            else:
                extra_data = None
            self.tasks.append([1, mod, res, csv, xsl, extra_data])
        else:
            self.errorList.append(
            "prepopulate error: job not of length 4, ignored: %s" % str(details))

    # -------------------------------------------------------------------------
    def extract_other_import_line(self, path, details):
        """
            Store a single import job into the tasks property
            *,function,filename,*extraArgs
        """

        function = details[1].strip('" ')
        filepath = None
        if len(details) >= 3:
            filename = details[2].strip('" ')
            if filename != "":
                (subfolder, filename) = os.path.split(filename)
                if subfolder != "":
                    path = os.path.join(current.request.folder,
                                        "modules",
                                        "templates",
                                        subfolder)
                    # @todo: deprecate this block once migration completed
                    if not os.path.exists(path):
                        # Non-standard location (legacy template)?
                        path = os.path.join(current.request.folder,
                                            "private",
                                            "templates",
                                            subfolder)
                filepath = os.path.join(path, filename)

        if len(details) >= 4:
            extraArgs = details[3:]
        else:
            extraArgs = None

        self.tasks.append((2, function, filepath, extraArgs))

    # -------------------------------------------------------------------------
    def execute_import_task(self, task):
        """
            Execute each import job, in order
        """

        start = datetime.datetime.now()
        if task[0] == 1:
            s3db = current.s3db
            response = current.response
            error_string = "prepopulate error: file %s missing"
            # Store the view
            view = response.view

            #current.log.debug("Running job %s %s (filename=%s transform=%s)" % (task[1],
            #                                                                    task[2],
            #                                                                    task[3],
            #                                                                    task[4],
            #                                                                    ))

            prefix = task[1]
            name = task[2]
            tablename = "%s_%s" % (prefix, name)
            if tablename in self.alternateTables:
                details = self.alternateTables[tablename]
                if "tablename" in details:
                    tablename = details["tablename"]
                s3db.table(tablename)
                if "loader" in details:
                    loader = details["loader"]
                    if loader is not None:
                        loader()
                if "prefix" in details:
                    prefix = details["prefix"]
                if "name" in details:
                    name = details["name"]

            try:
                resource = s3db.resource(tablename)
            except AttributeError:
                # Table cannot be loaded
                self.errorList.append("WARNING: Unable to find table %s import job skipped" % tablename)
                return

            # Check if the source file is accessible
            filename = task[3]
            if filename[:7] == "http://":
                req = urllib2.Request(url=filename)
                try:
                    f = urlopen(req)
                except HTTPError as e:
                    self.errorList.append("Could not access %s: %s" % (filename, e.read()))
                    return
                except:
                    self.errorList.append(error_string % filename)
                    return
                else:
                    csv = f
            else:
                try:
                    csv = open(filename, "r")
                except IOError:
                    self.errorList.append(error_string % filename)
                    return

            # Check if the stylesheet is accessible
            try:
                S = open(task[4], "r")
            except IOError:
                self.errorList.append(error_string % task[4])
                return
            else:
                S.close()

            if tablename not in self.customised:
                # Customise the resource
                customise = current.deployment_settings.customise_resource(tablename)
                if customise:
                    request = S3Request(prefix, name, current.request)
                    customise(request, tablename)
                    self.customised.append(tablename)

            extra_data = None
            if task[5]:
                try:
                    extradata = self.unescape(task[5], {"'": '"'})
                    extradata = json.loads(extradata)
                    extra_data = extradata
                except:
                    self.errorList.append("WARNING:5th parameter invalid, parameter %s ignored" % task[5])
            auth = current.auth
            auth.rollback = True
            try:
                # @todo: add extra_data and file attachments
                resource.import_xml(csv,
                                    format="csv",
                                    stylesheet=task[4],
                                    extra_data=extra_data,
                                    )
            except SyntaxError as e:
                self.errorList.append("WARNING: import error - %s (file: %s, stylesheet: %s)" %
                                     (e, filename, task[4]))
                auth.rollback = False
                return

            if not resource.error:
                current.db.commit()
            else:
                # Must roll back if there was an error!
                error = resource.error
                self.errorList.append("%s - %s: %s" % (
                                      task[3], resource.tablename, error))
                errors = current.xml.collect_errors(resource)
                if errors:
                    self.errorList.extend(errors)
                current.db.rollback()

            auth.rollback = False

            # Restore the view
            response.view = view
            end = datetime.datetime.now()
            duration = end - start
            csvName = task[3][task[3].rfind("/") + 1:]
            duration = '{:.2f}'.format(duration.total_seconds())
            msg = "%s imported (%s sec)" % (csvName, duration)
            self.resultList.append(msg)
            current.log.debug(msg)

    # -------------------------------------------------------------------------
    def execute_special_task(self, task):
        """
            Execute import tasks which require a custom function,
            such as import_role
        """

        start = datetime.datetime.now()
        s3 = current.response.s3
        if task[0] == 2:
            fun = task[1]
            filepath = task[2]
            extraArgs = task[3]
            if filepath is None:
                if extraArgs is None:
                    error = s3[fun]()
                else:
                    error = s3[fun](*extraArgs)
            elif extraArgs is None:
                error = s3[fun](filepath)
            else:
                error = s3[fun](filepath, *extraArgs)
            if error:
                self.errorList.append(error)
            end = datetime.datetime.now()
            duration = end - start
            duration = '{:.2f}'.format(duration.total_seconds())
            msg = "%s completed (%s sec)" % (fun, duration)
            self.resultList.append(msg)
            current.log.debug(msg)

    # -------------------------------------------------------------------------
    @staticmethod
    def _lookup_pe(entity):
        """
            Convert an Organisation Name to a pe_id
            - helper for import_role
        """

        table = current.s3db.org_organisation
        org = current.db(table.name == entity).select(table.pe_id,
                                                      limitby = (0, 1)
                                                      ).first()
        try:
            pe_id = org.pe_id
        except AttributeError:
            current.log.warning("import_role cannot find pe_id for %s" % entity)
            pe_id = None

        return pe_id

    # -------------------------------------------------------------------------
    def import_role(self, filename):
        """
            Import Roles from CSV
        """

        # Check if the source file is accessible
        try:
            openFile = open(filename, "r")
        except IOError:
            return "Unable to open file %s" % filename

        auth = current.auth
        acl = auth.permission
        create_role = auth.s3_create_role

        def parseACL(_acl):
            permissions = _acl.split("|")
            acl_value = 0
            for permission in permissions:
                if permission == "READ":
                    acl_value |= acl.READ
                if permission == "CREATE":
                    acl_value |= acl.CREATE
                if permission == "UPDATE":
                    acl_value |= acl.UPDATE
                if permission == "DELETE":
                    acl_value |= acl.DELETE
                if permission == "REVIEW":
                    acl_value |= acl.REVIEW
                if permission == "APPROVE":
                    acl_value |= acl.APPROVE
                if permission == "PUBLISH":
                    acl_value |= acl.PUBLISH
                if permission == "ALL":
                    acl_value |= acl.ALL
            return acl_value

        reader = self.csv.DictReader(openFile)
        roles = {}
        acls = {}
        args = {}
        for row in reader:
            if row != None:
                row_get = row.get
                role = row_get("role")
                desc = row_get("description", "")
                rules = {}
                extra_param = {}
                controller = row_get("controller")
                if controller:
                    rules["c"] = controller
                fn = row_get("function")
                if fn:
                    rules["f"] = fn
                table = row_get("table")
                if table:
                    rules["t"] = table
                oacl = row_get("oacl")
                if oacl:
                    rules["oacl"] = parseACL(oacl)
                uacl = row_get("uacl")
                if uacl:
                    rules["uacl"] = parseACL(uacl)
                #org = row_get("org")
                #if org:
                #    rules["organisation"] = org
                #facility = row_get("facility")
                #if facility:
                #    rules["facility"] = facility
                entity = row_get("entity")
                if entity:
                    if entity == "any":
                        # Pass through as-is
                        pass
                    else:
                        try:
                            entity = int(entity)
                        except ValueError:
                            entity = self._lookup_pe(entity)
                    rules["entity"] = entity
                flag = lambda s: bool(s) and s.lower() in ("1", "true", "yes")
                hidden = row_get("hidden")
                if hidden:
                    extra_param["hidden"] = flag(hidden)
                system = row_get("system")
                if system:
                    extra_param["system"] = flag(system)
                protected = row_get("protected")
                if protected:
                    extra_param["protected"] = flag(protected)
                uid = row_get("uid")
                if uid:
                    extra_param["uid"] = uid
            if role in roles:
                acls[role].append(rules)
            else:
                roles[role] = [role, desc]
                acls[role] = [rules]
            if len(extra_param) > 0 and role not in args:
                args[role] = extra_param
        for rulelist in roles.values():
            if rulelist[0] in args:
                create_role(rulelist[0],
                            rulelist[1],
                            *acls[rulelist[0]],
                            **args[rulelist[0]])
            else:
                create_role(rulelist[0],
                            rulelist[1],
                            *acls[rulelist[0]])

    # -------------------------------------------------------------------------
    def import_user(self, filename):
        """
            Import Users from CSV with an import Prep
        """

        current.response.s3.import_prep = current.auth.s3_import_prep

        current.s3db.add_components("auth_user",
                                    auth_masterkey = "user_id",
                                    )

        user_task = [1,
                     "auth",
                     "user",
                     filename,
                     os.path.join(current.request.folder,
                                  "static",
                                  "formats",
                                  "s3csv",
                                  "auth",
                                  "user.xsl"
                                  ),
                     None
                     ]
        self.execute_import_task(user_task)

    # -------------------------------------------------------------------------
    def import_feed(self, filename):
        """
            Import RSS Feeds from CSV with an import Prep
        """

        stylesheet = os.path.join(current.request.folder,
                                  "static",
                                  "formats",
                                  "s3csv",
                                  "msg",
                                  "rss_channel.xsl"
                                  )

        # 1st import any Contacts
        current.response.s3.import_prep = current.s3db.pr_import_prep
        user_task = [1,
                     "pr",
                     "contact",
                     filename,
                     stylesheet,
                     None
                     ]
        self.execute_import_task(user_task)

        # Then import the Channels
        user_task = [1,
                     "msg",
                     "rss_channel",
                     filename,
                     stylesheet,
                     None
                     ]
        self.execute_import_task(user_task)

    # -------------------------------------------------------------------------
    def import_image(self,
                     filename,
                     tablename,
                     idfield,
                     imagefield):
        """
            Import images, such as a logo or person image

            filename     a CSV list of records and filenames
            tablename    the name of the table
            idfield      the field used to identify the record
            imagefield   the field to where the image will be added

            Example:
            bi.import_image ("org_logos.csv", "org_organisation", "name", "logo")
            and the file org_logos.csv may look as follows
            id                            file
            Sahana Software Foundation    sahanalogo.jpg
            American Red Cross            icrc.gif
        """

        # Check if the source file is accessible
        try:
            openFile = open(filename, "r")
        except IOError:
            return "Unable to open file %s" % filename

        prefix, name = tablename.split("_", 1)

        reader = self.csv.DictReader(openFile)

        db = current.db
        s3db = current.s3db
        audit = current.audit
        table = s3db[tablename]
        idfield = table[idfield]
        base_query = (table.deleted != True)
        fieldnames = [table._id.name,
                      imagefield
                      ]
        # https://github.com/web2py/web2py/blob/master/gluon/sqlhtml.py#L1947
        for field in table:
            if field.name not in fieldnames and field.writable is False \
                and field.update is None and field.compute is None:
                fieldnames.append(field.name)
        fields = [table[f] for f in fieldnames]

        # Get callbacks
        get_config = s3db.get_config
        onvalidation = get_config(tablename, "update_onvalidation") or \
                       get_config(tablename, "onvalidation")
        onaccept = get_config(tablename, "update_onaccept") or \
                   get_config(tablename, "onaccept")
        update_realm = get_config(tablename, "update_realm")
        if update_realm:
            set_realm_entity = current.auth.set_realm_entity
        update_super = s3db.update_super

        for row in reader:
            if row != None:
                # Open the file
                image = row["file"]
                try:
                    # Extract the path to the CSV file, image should be in
                    # this directory, or relative to it
                    path = os.path.split(filename)[0]
                    imagepath = os.path.join(path, image)
                    openFile = open(imagepath, "rb")
                except IOError:
                    current.log.error("Unable to open image file %s" % image)
                    continue
                image_source = StringIO(openFile.read())
                # Get the id of the resource
                query = base_query & (idfield == row["id"])
                record = db(query).select(limitby = (0, 1),
                                          *fields).first()
                try:
                    record_id = record.id
                except AttributeError:
                    current.log.error("Unable to get record %s of the resource %s to attach the image file to" % (row["id"], tablename))
                    continue
                # Create and accept the form
                form = SQLFORM(table, record, fields=["id", imagefield])
                form_vars = Storage()
                form_vars._formname = "%s/%s" % (tablename, record_id)
                form_vars.id = record_id
                source = Storage()
                source.filename = imagepath
                source.file = image_source
                form_vars[imagefield] = source
                if form.accepts(form_vars, onvalidation=onvalidation):
                    # Audit
                    audit("update", prefix, name, form=form,
                          record=record_id, representation="csv")

                    # Update super entity links
                    update_super(table, form_vars)

                    # Update realm
                    if update_realm:
                        set_realm_entity(table, form_vars, force_update=True)

                    # Execute onaccept
                    callback(onaccept, form, tablename=tablename)
                else:
                    for (key, error) in form.errors.items():
                        current.log.error("error importing logo %s: %s %s" % (image, key, error))

    # -------------------------------------------------------------------------
    @staticmethod
    def import_font(url):
        """
            Install a Font
        """

        if url == "unifont":
            #url = "http://unifoundry.com/pub/unifont-7.0.06/font-builds/unifont-7.0.06.ttf"
            url = "http://unifoundry.com/pub/unifont-10.0.07/font-builds/unifont-10.0.07.ttf"
            # Rename to make version upgrades be transparent
            filename = "unifont.ttf"
            extension = "ttf"
        else:
            filename = url.split("/")[-1]
            filename, extension = filename.rsplit(".", 1)

            if extension not in ("ttf", "gz", "zip"):
                current.log.warning("Unsupported font extension: %s" % extension)
                return

            filename = "%s.ttf" % filename

        fontPath = os.path.join(current.request.folder, "static", "fonts")
        if os.path.exists(os.path.join(fontPath, filename)):
            current.log.warning("Using cached copy of %s" % filename)
            return

        # Download as we have no cached copy

        # Copy the current working directory to revert back to later
        cwd = os.getcwd()

        # Set the current working directory
        os.chdir(fontPath)
        try:
            _file = fetch(url)
        except URLError as exception:
            current.log.error(exception)
            # Revert back to the working directory as before.
            os.chdir(cwd)
            return

        if extension == "gz":
            import tarfile
            tf = tarfile.open(fileobj=StringIO(_file))
            tf.extractall()

        elif extension == "zip":
            import zipfile
            zf = zipfile.ZipFile(StringIO(_file))
            zf.extractall()

        else:
            f = open(filename, "wb")
            f.write(_file)
            f.close()

        # Revert back to the working directory as before.
        os.chdir(cwd)

    # -------------------------------------------------------------------------
    def import_remote_csv(self, url, prefix, resource, stylesheet):
        """ Import CSV files from remote servers """

        extension = url.split(".")[-1]
        if extension not in ("csv", "zip"):
            current.log.error("error importing remote file %s: invalid extension" % (url))
            return

        # Copy the current working directory to revert back to later
        cwd = os.getcwd()

        # Shortcut
        os_path = os.path
        os_path_exists = os_path.exists
        os_path_join = os_path.join

        # Create the working directory
        TEMP = os_path_join(cwd, "temp")
        if not os_path_exists(TEMP): # use web2py/temp/remote_csv as a cache
            import tempfile
            TEMP = tempfile.gettempdir()
        tempPath = os_path_join(TEMP, "remote_csv")
        if not os_path_exists(tempPath):
            try:
                os.mkdir(tempPath)
            except OSError:
                current.log.error("Unable to create temp folder %s!" % tempPath)
                return

        filename = url.split("/")[-1]
        if extension == "zip":
            filename = filename.replace(".zip", ".csv")
        if os_path_exists(os_path_join(tempPath, filename)):
            current.log.warning("Using cached copy of %s" % filename)
        else:
            # Download if we have no cached copy
            # Set the current working directory
            os.chdir(tempPath)
            try:
                _file = fetch(url)
            except URLError as exception:
                current.log.error(exception)
                # Revert back to the working directory as before.
                os.chdir(cwd)
                return

            if extension == "zip":
                # Need to unzip
                import zipfile
                try:
                    myfile = zipfile.ZipFile(StringIO(_file))
                except zipfile.BadZipfile as exception:
                    # e.g. trying to download through a captive portal
                    current.log.error(exception)
                    # Revert back to the working directory as before.
                    os.chdir(cwd)
                    return
                files = myfile.infolist()
                for f in files:
                    filename = f.filename
                    extension = filename.split(".")[-1]
                    if extension == "csv":
                        _file = myfile.read(filename)
                        _f = open(filename, "w")
                        _f.write(_file)
                        _f.close()
                        break
                myfile.close()
            else:
                f = open(filename, "w")
                f.write(_file)
                f.close()

            # Revert back to the working directory as before.
            os.chdir(cwd)

        task = [1, prefix, resource,
                os_path_join(tempPath, filename),
                os_path_join(current.request.folder,
                             "static",
                             "formats",
                             "s3csv",
                             prefix,
                             stylesheet
                             ),
                None
                ]
        self.execute_import_task(task)

    # -------------------------------------------------------------------------
    @staticmethod
    def import_script(filename):
        """
            Run a custom Import Script

            @ToDo: Report Errors during Script run to console better
        """

        from gluon.cfs import getcfs
        from gluon.compileapp import build_environment
        from gluon.restricted import restricted

        environment = build_environment(current.request, current.response, current.session)
        environment["current"] = current
        environment["auth"] = current.auth
        environment["db"] = current.db
        environment["gis"] = current.gis
        environment["s3db"] = current.s3db
        environment["settings"] = current.deployment_settings

        code = getcfs(filename, filename, None)
        restricted(code, environment, layer=filename)

    # -------------------------------------------------------------------------
    def import_task(self, task_name, args_json=None, vars_json=None):
        """
            Import a Scheduled Task
        """

        # Store current value of Bulk
        bulk = current.response.s3.bulk
        # Set Bulk to true for this parse
        current.response.s3.bulk = True
        validator = IS_JSONS3()
        if args_json:
            task_args, error = validator(args_json)
            if error:
                self.errorList.append(error)
                return
        else:
            task_args = []
        if vars_json:
            all_vars, error = validator(vars_json)
            if error:
                self.errorList.append(error)
                return
        else:
            all_vars = {}
        # Restore bulk setting
        current.response.s3.bulk = bulk

        kwargs = {}
        task_vars = {}
        options = ("function_name",
                   "start_time",
                   "next_run_time",
                   "stop_time",
                   "repeats",
                   "period", # seconds
                   "timeout", # seconds
                   "enabled", # None = Enabled
                   "group_name",
                   "ignore_duplicate",
                   "sync_output",
                   )
        for var in all_vars:
            if var in options:
                kwargs[var] = all_vars[var]
            else:
                task_vars[var] = all_vars[var]

        current.s3task.schedule_task(task_name.split(os.path.sep)[-1], # Strip the path
                                     args = task_args,
                                     vars = task_vars,
                                     **kwargs
                                     )

    # -------------------------------------------------------------------------
    def import_xml(self,
                   filepath,
                   prefix,
                   resourcename,
                   dataformat,
                   source_type=None,
                   ):
        """
            Import XML data using an XSLT: static/formats/<dataformat>/import.xsl
            Setting the source_type is possible
        """

        # Remove any spaces and enclosing double quote
        prefix = prefix.strip('" ')
        resourcename = resourcename.strip('" ')

        try:
            source = open(filepath, "rb")
        except IOError:
            error_string = "prepopulate error: file %s missing"
            self.errorList.append(error_string % filepath)
            return

        stylesheet = os.path.join(current.request.folder,
                                  "static",
                                  "formats",
                                  dataformat,
                                  "import.xsl")
        try:
            xslt_file = open(stylesheet, "r")
        except IOError:
            error_string = "prepopulate error: file %s missing"
            self.errorList.append(error_string % stylesheet)
            return
        else:
            xslt_file.close()

        tablename = "%s_%s" % (prefix, resourcename)
        resource = current.s3db.resource(tablename)

        if tablename not in self.customised:
            # Customise the resource
            customise = current.deployment_settings.customise_resource(tablename)
            if customise:
                request = S3Request(prefix, resourcename, current.request)
                customise(request, tablename)
                self.customised.append(tablename)

        auth = current.auth
        auth.rollback = True
        try:
            resource.import_xml(source,
                                stylesheet = stylesheet,
                                source_type = source_type,
                                )
        except SyntaxError as e:
            self.errorList.append("WARNING: import error - %s (file: %s, stylesheet: %s/import.xsl)" %
                                 (e, filepath, dataformat))
            auth.rollback = False
            return

        if not resource.error:
            current.db.commit()
        else:
            # Must roll back if there was an error!
            error = resource.error
            self.errorList.append("%s - %s: %s" % (
                                  filepath, tablename, error))
            errors = current.xml.collect_errors(resource)
            if errors:
                self.errorList.extend(errors)
            current.db.rollback()

        auth.rollback = False

    # -------------------------------------------------------------------------
    def perform_tasks(self, path):
        """
            Load and then execute the import jobs that are listed in the
            descriptor file (tasks.cfg)
        """

        self.load_descriptor(path)
        for task in self.tasks:
            if task[0] == 1:
                self.execute_import_task(task)
            elif task[0] == 2:
                self.execute_special_task(task)

# END =========================================================================
