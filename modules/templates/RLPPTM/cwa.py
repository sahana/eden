# -*- coding: utf-8 -*-

"""
    Infection test result reporting for RLPPTM template

    @license: MIT
"""

import base64
import datetime
import hashlib
import json
import requests
import secrets
import sys
import uuid

from gluon import current, Field, IS_EMPTY_OR, IS_IN_SET, SQLFORM, URL, \
                  BUTTON, DIV, FORM, H5, INPUT, TABLE, TD, TR

from s3 import IS_ONE_OF, S3CustomController, S3Method, \
               s3_date, s3_mark_required, s3_qrcode_represent, \
               JSONERRORS

from .vouchers import RLPCardLayout

CWA = {"system": "RKI / Corona-Warn-App",
       "app": "Corona-Warn-App",
       }
POCID_PREFIX = "lsjvrlp"

# =============================================================================
class TestResultRegistration(S3Method):
    """ REST Method to Register Test Results """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}
        if r.method == "register":
            output = self.register(r, **attr)
        elif r.method == "certify":
            output = self.certify(r, **attr)
        elif r.method == "cwaretry":
            output = self.cwaretry(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def register(self, r, **attr):
        """
            Register a test result

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        if r.http not in ("GET", "POST"):
            r.error(405, current.ERROR.BAD_METHOD)
        if not r.interactive:
            r.error(415, current.ERROR.BAD_FORMAT)

        T = current.T
        db = current.db
        s3db = current.s3db
        auth = current.auth

        request = current.request
        response = current.response
        s3 = response.s3

        settings = current.deployment_settings

        # Page title and intro text
        title = T("Register Test Result")

        # Get intro text from CMS
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "disease") & \
                         (ltable.resource == "case_diagnostics") & \
                         (ltable.deleted == False))

        query = (ctable.name == "TestResultRegistrationIntro") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                                join = join,
                                cache = s3db.cache,
                                limitby = (0, 1),
                                ).first()
        intro = row.body if row else None

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["CWA_ANONYMOUS", "CWA_PERSONAL"])

        table = s3db.disease_case_diagnostics

        # Configure disease_id
        field = table.disease_id
        if field.writable:
            default_disease = None
            offset = 1
        else:
            default_disease = field.default
            field.readable = False
            offset = 0

        # Probe date is mandatory
        field = table.probe_date
        requires = field.requires
        if isinstance(requires, IS_EMPTY_OR):
            field.requires = requires.other

        # Configure device_id
        field = table.device_id
        field.readable = field.writable = True

        dtable = s3db.disease_testing_device
        query = (dtable.device_class == "RAT") & \
                (dtable.approved == True) & \
                (dtable.available == True)
        if default_disease:
            query = (dtable.disease_id == default_disease) & query
        field.requires = IS_ONE_OF(db(query), "disease_testing_device.id",
                                   field.represent,
                                   )

        cwa_options = (("NO", T("Do not report")),
                       ("ANONYMOUS", T("Issue anonymous contact tracing code")),
                       ("PERSONAL", T("Issue personal test certificate")),
                       )
        formfields = [# -- Test Result --
                      table.site_id,
                      table.disease_id,
                      table.probe_date,
                      table.device_id,
                      table.result,

                      # -- Report to CWA --
                      Field("report_to_cwa", "string",
                            requires = IS_IN_SET(cwa_options, sort=False, zero=""),
                            default = "NO",
                            label = T("Report test result to %(system)s") % CWA,
                            ),
                      Field("last_name",
                            label = T("Last Name"),
                            ),
                      Field("first_name",
                            label = T("First Name"),
                            ),
                      s3_date("date_of_birth",
                              label = T("Date of Birth"),
                              month_selector = True,
                              ),
                      Field("dcc_option", "boolean",
                            default = False,
                            label = T("Provide Digital %(title)s Certificate") % {"title": "COVID-19 Test"},
                            ),
                      Field("consent",
                            label = "",
                            widget = consent.widget,
                            ),
                      ]

        # Required fields
        required_fields = []

        # Subheadings
        subheadings = ((0, T("Test Result")),
                       (4 + offset, CWA["system"]),
                       )

        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields,
                                                mark_required = required_fields,
                                                )
        s3.has_required = has_required

        # Form buttons
        REGISTER = T("Submit")
        buttons = [INPUT(_type = "submit",
                         _value = REGISTER,
                         ),
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "test_result",
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = REGISTER,
                               delete_label = auth.messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS & JS Validation
        form.add_class("result-register")

        # Add Subheadings
        if subheadings:
            for pos, heading in subheadings[::-1]:
                form[0].insert(pos, DIV(heading, _class="subheading"))

        # Inject scripts
        script = "/%s/static/themes/RLP/js/testresult.js" % r.application
        if script not in s3.scripts:
            s3.scripts.append(script)
        s3.jquery_ready.append("S3EnableNavigateAwayConfirm()")

        if form.accepts(request.vars,
                        current.session,
                        formname = "register",
                        onvalidation = self.validate,
                        ):

            formvars = form.vars

            # Create disease_case_diagnostics record
            testresult = {"result": formvars.get("result"),
                          }
            if "site_id" in formvars:
                testresult["site_id"] = formvars["site_id"]
            if "disease_id" in formvars:
                testresult["disease_id"] = formvars["disease_id"]
            if "probe_date" in formvars:
                testresult["probe_date"] = formvars["probe_date"]
            if "device_id" in formvars:
                testresult["device_id"] = formvars["device_id"]

            record_id = table.insert(**testresult)
            if not record_id:
                raise RuntimeError("Could not create testresult record")

            testresult["id"] = record_id
            # Set record owner
            auth = current.auth
            auth.s3_set_record_owner(table, record_id)
            auth.s3_make_session_owner(table, record_id)
            # Onaccept
            s3db.onaccept(table, testresult, method="create")
            response.confirmation = T("Test Result registered")

            report_to_cwa = formvars.get("report_to_cwa")
            if report_to_cwa == "NO":
                # Do not report to CWA, just forward to read view
                self.next = r.url(id=record_id, method="read")
            else:
                # Report to CWA and show test certificate
                dcc_option = False
                if report_to_cwa == "ANONYMOUS":
                    processing_type = "CWA_ANONYMOUS"
                    cwa_report = CWAReport(record_id)
                elif report_to_cwa == "PERSONAL":
                    dcc_option = formvars.get("dcc_option")
                    processing_type = "CWA_PERSONAL"
                    cwa_report = CWAReport(record_id,
                                           anonymous = False,
                                           first_name = formvars.get("first_name"),
                                           last_name = formvars.get("last_name"),
                                           dob = formvars.get("date_of_birth"),
                                           dcc = dcc_option,
                                           )
                else:
                    processing_type = cwa_report = None

                if cwa_report:
                    # Register consent
                    if processing_type:
                        cwa_report.register_consent(processing_type,
                                                    formvars.get("consent"),
                                                    )
                    # Send to CWA
                    success = cwa_report.send()
                    if success:
                        response.information = T("Result reported to %(system)s") % CWA
                        retry = False
                    else:
                        response.error = T("Report to %(system)s failed") % CWA
                        retry = True

                    # Store DCC data
                    if dcc_option:
                        cwa_data = cwa_report.data
                        from .dcc import DCC
                        try:
                            hcert = DCC.from_result(cwa_data.get("hash"),
                                                    record_id,
                                                    cwa_data.get("fn"),
                                                    cwa_data.get("ln"),
                                                    cwa_data.get("dob"),
                                                    )
                        except ValueError as e:
                            hcert = None
                            response.warning = str(e)
                        # TODO disable dcc in CWA report if failed?
                        if hcert:
                            hcert.save()

                    S3CustomController._view("RLPPTM", "certificate.html")

                    # Title
                    field = table.disease_id
                    if cwa_report.disease_id and field.represent:
                        disease = field.represent(cwa_report.disease_id)
                        title = "%s %s" % (disease, T("Test Result"))
                    else:
                        title = T("Test Result")

                    return {"title": title,
                            "intro": None, # TODO
                            "form": cwa_report.formatted(retry=retry),
                            }
                else:
                    response.information = T("Result not reported to %(system)s") % CWA
                    self.next = r.url(id=record_id, method="read")


            return None

        elif form.errors:
            current.response.error = T("There are errors in the form, please check your input")

        # Custom View
        S3CustomController._view("RLPPTM", "testresult.html")

        return {"title": title,
                "intro": intro,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def validate(form):
        """
            Validate the test result registration form
            - personal details are required for reporting to CWA by name
            - make sure the required consent option is checked
        """

        T = current.T

        formvars = form.vars

        consent = current.s3db.auth_Consent
        response = consent.parse(formvars.get("consent"))

        cwa = formvars.get("report_to_cwa")
        if cwa == "PERSONAL":
            # Personal data required
            for fn in ("first_name", "last_name", "date_of_birth"):
                if not formvars.get(fn):
                    form.errors[fn] = T("Enter a value")
            # CWA_PERSONAL consent required
            c = response.get("CWA_PERSONAL")
            if not c or not c[1]:
                form.errors.consent = T("Consent required")
        elif cwa == "ANONYMOUS":
            # CWA_ANONYMOUS consent required
            c = response.get("CWA_ANONYMOUS")
            if not c or not c[1]:
                form.errors.consent = T("Consent required")

        # TODO chosen test device must match the chosen disease, if disease_id is in FORM

    # -------------------------------------------------------------------------
    @staticmethod
    def certify(r, **attr):
        """
            Generate a test certificate (PDF) for download

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        if not r.record:
            r.error(400, current.ERROR.BAD_REQUEST)
        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)
        if r.representation != "pdf":
            r.error(415, current.ERROR.BAD_FORMAT)

        post_vars = r.post_vars

        # Extract and check formkey from post data
        formkey = post_vars.get("_formkey")
        keyname = "_formkey[testresult/%s]" % r.id
        if not formkey or formkey not in current.session.get(keyname, []):
            r.error(403, current.ERROR.NOT_PERMITTED)

        # Extract cwadata
        cwadata = post_vars.get("cwadata")
        if not cwadata:
            r.error(400, current.ERROR.BAD_REQUEST)
        try:
            cwadata = json.loads(cwadata)
        except JSONERRORS:
            r.error(400, current.ERROR.BAD_REQUEST)

        # Generate the CWAReport (implicitly validates the hash)
        anonymous = "fn" not in cwadata
        try:
            cwareport = CWAReport(r.id,
                                  anonymous = anonymous,
                                  first_name = cwadata.get("fn"),
                                  last_name = cwadata.get("ln"),
                                  dob = cwadata.get("dob"),
                                  dcc = cwadata.get("dcc", False),
                                  salt = cwadata.get("salt"),
                                  dhash = cwadata.get("hash"),
                                  )
        except ValueError:
            r.error(400, current.ERROR.BAD_RECORD)

        # Generate the data item
        item = {"link": cwareport.get_link(),
                }
        if not anonymous:
            for k in ("ln", "fn", "dob"):
                value = cwadata.get(k)
                if k == "dob":
                    value = CWAReport.to_local_dtfmt(value)
                item[k] = value

        # Test Station, date and result
        table = current.s3db.disease_case_diagnostics
        field = table.site_id
        if field.represent:
            item["site_name"] = field.represent(cwareport.site_id)
        field = table.probe_date
        if field.represent:
            item["test_date"] = field.represent(cwareport.probe_date)
        field = table.result
        if field.represent:
            item["result"] = field.represent(cwareport.result)

        # Title
        T = current.T
        field = table.disease_id
        if cwareport.disease_id and field.represent:
            disease = field.represent(cwareport.disease_id)
            title = "%s %s" % (disease, T("Test Result"))
        else:
            title = T("Test Result")
        item["title"] = pdf_title = title

        from s3.s3export import S3Exporter
        from gluon.contenttype import contenttype

        # Export PDF
        output = S3Exporter().pdfcard([item],
                                      layout = CWACardLayout,
                                      title = pdf_title,
                                      )

        response = current.response
        disposition = "attachment; filename=\"certificate.pdf\""
        response.headers["Content-Type"] = contenttype(".pdf")
        response.headers["Content-disposition"] = disposition

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def cwaretry(r, **attr):
        """
            Retry sending test result to CWA result server

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        if not r.record:
            r.error(400, current.ERROR.BAD_REQUEST)
        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)
        if r.representation != "json":
            r.error(415, current.ERROR.BAD_FORMAT)

        T = current.T

        # Parse JSON body
        s = r.body
        s.seek(0)
        try:
            options = json.load(s)
        except JSONERRORS:
            options = None
        if not isinstance(options, dict):
            r.error(400, "Invalid request options")

        # Verify formkey
        formkey = options.get("formkey")
        keyname = "_formkey[testresult/%s]" % r.id
        if not formkey or formkey not in current.session.get(keyname, []):
            r.error(403, current.ERROR.NOT_PERMITTED)

        # Instantiate CWAReport
        cwadata = options.get("cwadata", {})
        anonymous = "fn" not in cwadata
        try:
            cwareport = CWAReport(r.id,
                                  anonymous = anonymous,
                                  first_name = cwadata.get("fn"),
                                  last_name = cwadata.get("ln"),
                                  dob = cwadata.get("dob"),
                                  dcc = cwadata.get("dgc", False),
                                  salt = cwadata.get("salt"),
                                  dhash = cwadata.get("hash"),
                                  )
        except ValueError:
            r.error(400, current.ERROR.BAD_RECORD)

        success = cwareport.send()
        if success:
            message = T("Result reported to %(system)s") % CWA
            output = current.xml.json_message(message=message)
        else:
            r.error(503, T("Report to %(system)s failed") % CWA)
        return output

# =============================================================================
class CWAReport(object):
    """
        CWA Report Generator
        @see: https://github.com/corona-warn-app/cwa-quicktest-onboarding/wiki/Anbindung-der-Partnersysteme
    """

    def __init__(self,
                 result_id,
                 anonymous=True,
                 first_name=None,
                 last_name=None,
                 dob=None,
                 dcc=False,
                 salt=None,
                 dhash=None,
                 ):
        """
            Constructor

            @param result_id: the disease_case_diagnostics record ID
            @param anonymous: generate anonymous report
            @param first_name: first name
            @param last_name: last name
            @param dob: date of birth (str in isoformat, or datetime.date)
            @param dcc: whether to provide a digital test certificate
            @param salt: previously used salt (for retry)
            @param dhash: previously generated hash (for retry)

            @note: if not anonymous, personal data are required
        """

        db = current.db
        s3db = current.s3db

        # Lookup the result
        if result_id:
            table = s3db.disease_case_diagnostics
            query = (table.id == result_id) & \
                    (table.deleted == False)
            result = db(query).select(table.uuid,
                                      table.modified_on,
                                      table.site_id,
                                      table.disease_id,
                                      table.probe_date,
                                      table.result_date,
                                      table.result,
                                      limitby = (0, 1),
                                      ).first()
            if not result:
                raise ValueError("Test result #%s not found" % result_id)
        else:
            raise ValueError("Test result ID is required")

        # Store the test result
        self.result_id = result_id
        self.site_id = result.site_id
        self.disease_id = result.disease_id
        self.probe_date = result.probe_date
        self.result_date = result.result_date
        self.result = result.result
        self.dcc = False

        # Determine the testid and timestamp
        testid = result.uuid
        timestamp = int(result.probe_date.replace(microsecond=0).timestamp())

        if not anonymous:
            if not all(value for value in (first_name, last_name, dob)):
                raise ValueError("Incomplete person data for personal report")
            data = {"fn": first_name,
                    "ln": last_name,
                    "dob": dob.isoformat() if isinstance(dob, datetime.date) else dob,
                    "timestamp": timestamp,
                    "testid": testid,
                    }
            if dcc:
                # Indicate whether we can issue a DCC (Digital COVID Certificate)
                self.dcc = data["dgc"] = bool(dcc) and self.result in ("POS", "NEG")
        else:
            data = {"timestamp": timestamp,
                    }

        # Add salt and hash
        data["salt"] = salt if salt else self.get_salt()
        if dhash:
            # Verify the hash
            if dhash != self.get_hash(data, anonymous=anonymous):
                raise ValueError("Invalid hash")
            data["hash"] = dhash
        else:
            data["hash"] = self.get_hash(data, anonymous=anonymous)

        self.data = data

        self._poc_id = None

    # -------------------------------------------------------------------------
    @property
    def poc_id(self):
        """
            The Point-of-Care ID for the test station we're reporting on
            - a string consisting of a common prefix and the site UUID

            @returns: the ID as string
        """

        poc_id = self._poc_id
        if poc_id is None:
            s3db = current.s3db
            stable = s3db.org_site
            query = (stable.site_id == self.site_id)
            row = current.db(query).select(stable.uuid,
                                           cache = s3db.cache,
                                           limitby = (0, 1),
                                           ).first()
            if row:
                uid = uuid.UUID(row.uuid).hex
                poc_id = self._poc_id = ("%s%s" % (POCID_PREFIX, uid)).lower()

        return poc_id

    # -------------------------------------------------------------------------
    @staticmethod
    def get_salt():
        """
            Produce a secure 128-bit (=16 bytes) random hex token

            @returns: the token as str
        """
        return secrets.token_hex(16)

    # -------------------------------------------------------------------------
    @staticmethod
    def get_hash(data, anonymous=True):
        """
            Generate a SHA256 hash from report data string
            String formats:
            - personal : [dob]#[fn]#[ln]#[timestamp]#[testid]#[salt]
            - anonymous: [timestamp]#[salt]

            @returns: the hash as str
        """

        hashable = lambda fields: "#".join(str(data[k]) for k in fields)
        if not anonymous:
            dstr = hashable(["dob", "fn", "ln", "timestamp", "testid", "salt"])
        else:
            dstr = hashable(["timestamp", "salt"])

        return hashlib.sha256(dstr.encode("utf-8")).hexdigest().lower()

    # -------------------------------------------------------------------------
    def get_link(self):
        """
            Construct the link for QR code generation

            @returns: the link as str
        """

        # Template for CWA-link
        template = current.deployment_settings.get_custom(key="cwa_link_template")

        # Convert data to JSON
        from s3.s3xml import SEPARATORS
        data_json = json.dumps(self.data, separators=SEPARATORS)

        # Base64-encode the data JSON
        data_str = base64.urlsafe_b64encode(data_json.encode("utf-8")).decode("utf-8")

        # Generate the link
        link = template % {"data": data_str}

        return link

    # -------------------------------------------------------------------------
    @staticmethod
    def to_local_dtfmt(dtstr):
        """
            Helper to convert an ISO-formatted date to local format

            @param dtstr: the ISO-formatted date as string

            @returns: the date in local format as string
        """

        c = current.calendar
        dt = c.parse_date(dtstr)
        return c.format_date(dt, local=True) if dt else dtstr

    # -------------------------------------------------------------------------
    def formatted(self, retry=False):
        """
            Formatted version of this report

            @param retry: add retry-action for sending to CWA

            @returns: a FORM containing
                      - the QR-code
                      - human-readable report details
                      - actions to download PDF, or retry sending to CWA
        """

        T = current.T
        table = current.s3db.disease_case_diagnostics

        # Personal Details
        data_repr = TABLE()
        data = self.data
        if not any(k in data for k in ("fn", "ln", "dob")):
            data_repr.append(TR(TD(T("Person Tested")),
                                TD(T("anonymous"), _class="cwa-data"),
                                ))
        else:
            labels = {"fn": T("First Name"),
                      "ln": T("Last Name"),
                      "dob": T("Date of Birth"),
                      }
            for k in ("ln", "fn", "dob"):
                value = data[k]
                if k == "dob":
                    value = self.to_local_dtfmt(value)
                data_repr.append(TR(TD(labels.get(k)),
                                    TD(value, _class="cwa-data"),
                                    ))

        # Test Station, date and result
        field = table.site_id
        if field.represent:
            data_repr.append(TR(TD(field.label),
                                TD(field.represent(self.site_id),
                                   _class="cwa-data",
                                   ),
                                ))
        field = table.probe_date
        if field.represent:
            data_repr.append(TR(TD(field.label),
                                TD(field.represent(self.probe_date),
                                   _class="cwa-data",
                                   ),
                                ))
        field = table.result
        if field.represent:
            data_repr.append(TR(TD(field.label),
                                TD(field.represent(self.result),
                                   _class="cwa-data",
                                   ),
                                ))

        # Details
        details = DIV(H5(T("Details")),
                      data_repr,
                      _class = "cwa-details",
                      )

        # QR Code
        title = T("Code for %(app)s") % CWA
        qrcode = DIV(s3_qrcode_represent(self.get_link(), show_value=False),
                     DIV(title, _class="cwa-qrcode-title"),
                     _class="cwa-qrcode",
                     )
        if retry:
            qrcode.add_class("hide")

        # Form buttons
        buttons = [
            BUTTON(T("Download PDF"),
                   _class = "tiny primary button cwa-pdf",
                   _type = "button",
                   ),
            ]
        if retry:
            buttons[0].add_class("hide")
            buttons.append(BUTTON(T("Retry sending to %(app)s") % CWA,
                                  _class = "tiny alert button cwa-retry",
                                  _type = "button",
                                  ))

        # Generate form key
        formurl = URL(c = "disease",
                      f = "case_diagnostics",
                      args = [self.result_id],
                      )
        formkey = uuid.uuid4().hex

        # Store form key in session
        session = current.session
        keyname = "_formkey[testresult/%s]" % self.result_id
        session[keyname] = session.get(keyname, [])[-9:] + [formkey]

        form = FORM(DIV(DIV(details,
                            qrcode,
                            _class="small-12 columns",
                            ),
                        _class="row form-row",
                        ),
                    DIV(DIV(buttons,
                            _class="small-12 columns",
                            ),
                        _class="row form-row",
                        ),
                    hidden = {"formurl": formurl,
                              "cwadata": json.dumps(self.data),
                              "_formkey": formkey,
                              },
                    )

        return form

    # -------------------------------------------------------------------------
    def register_consent(self, processing_type, response):
        """
            Register consent assertion using the current hash as reference

            @param processing type: the data processing type for which
                                    consent is required
            @param response: the consent response
        """

        data = self.data

        dhash = data.get("hash")
        if not dhash:
            raise ValueError("Missing context hash")

        consent = current.s3db.auth_Consent
        consent.assert_consent(dhash, processing_type, response)

    # -------------------------------------------------------------------------
    def send(self):
        """
            Send the CWA Report to the server;
            see also: https://github.com/corona-warn-app/cwa-quicktest-onboarding/blob/master/api/quicktest-openapi.json

            @returns: True|False whether successful
        """

        # Encode the result
        results = {"NEG": 6, "POS": 7, "INC": 8}
        result = results.get(self.result)
        if not result:
            current.log.error("CWAReport: invalid test result %s" % self.result)
            return False

        # Build the QuickTestResult JSON structure
        data = self.data
        testresult = {"id": data.get("hash"),
                      "sc": data.get("timestamp"),
                      "result": result,
                      }

        # The CWA server URL
        settings = current.deployment_settings
        server_url = settings.get_custom("cwa_server_url")
        if not server_url:
            raise RuntimeError("No CWA server URL configured")

        # The client credentials to access the server
        folder = current.request.folder
        cert = settings.get_custom("cwa_client_certificate")
        key = settings.get_custom("cwa_certificate_key")
        if not cert or not key:
            raise RuntimeError("No CWA client credentials configured")
        cert = "%s/%s" % (folder, cert)
        key = "%s/%s" % (folder, key)

        # The certificate chain to verify the server identity
        verify = settings.get_custom("cwa_server_ca")
        if verify:
            # Use the specified CA Certificate to verify server identity
            verify = "%s/%s" % (current.request.folder, verify)
        else:
            # Use python-certifi (=> make sure the latest version is installed)
            verify = True

        # Build the result_list
        result_list = {"testResults": [testresult]}
        # Look up the LabID
        if self.dcc:
            poc_id = self.poc_id
            if not poc_id:
                raise RuntimeError("Point-of-Care ID for test station not found")
            else:
                result_list["labId"] = poc_id

        # POST to server
        try:
            sr = requests.post(server_url,
                               # Send the QuickTestResultList
                               json = result_list,
                               cert = (cert, key),
                               verify = verify,
                               )
        except Exception:
            # Local error
            error = sys.exc_info()[1]
            current.log.error("CWAReport: transmission to CWA server failed (local error: %s)" % error)
            return False

        # Check return code (should be 204, but 202/200 would also be good news)
        if sr.status_code not in (204, 202, 200):
            # Remote error
            current.log.error("CWAReport: transmission to CWA server failed, status code %s" % sr.status_code)
            return False

        # Success
        return True

# =============================================================================
class CWACardLayout(RLPCardLayout):
    """
        Layout for printable vouchers
    """

    # -------------------------------------------------------------------------
    def draw(self):
        """
            Draw the card (one side)

            Instance attributes (NB draw-function should not modify them):
            - self.canv...............the canvas (provides the drawing methods)
            - self.resource...........the resource
            - self.item...............the data item (dict)
            - self.labels.............the field labels (dict)
            - self.backside...........this instance should render the backside
                                      of a card
            - self.multiple...........there are multiple cards per page
            - self.width..............the width of the card (in points)
            - self.height.............the height of the card (in points)

            NB Canvas coordinates are relative to the lower left corner of the
               card's frame, drawing must not overshoot self.width/self.height
        """

        T = current.T

        c = self.canv
        #w = self.width
        h = self.height

        item = self.item

        draw_value = self.draw_value

        if not self.backside:

            # CWA QR-Code
            link = item.get("link")
            if link:
                self.draw_qrcode(link,
                                 120,
                                 h - 170,
                                 size = 160,
                                 halign = "center",
                                 valign = "middle",
                                 level = "M",
                                 )
                draw_value(120,
                           h - 255,
                           T("Code for %(app)s") % CWA,
                           width = 160,
                           height = 20,
                           size = 7,
                           bold = False,
                           halign = "center",
                           )

            # Alignments for header items
            HL = 360
            HY = (h - 55, h - 75)

            # Title
            title = item.get("title")
            if title:
                draw_value(HL, HY[0], title, width=280, height=20, size=16)

            # Horizontal alignments for data items
            DL, DR = 270, 400

            # Vertical alignment for data items
            dy = lambda rnr: h - 115 - rnr * 20
            # Person first name, last name, date of birth
            if "fn" in item:
                last_name = item.get("ln")
                if last_name:
                    draw_value(DL, dy(0), "%s:" % T("Last Name"), width=100, height=20, size=9, bold=False)
                    draw_value(DR, dy(0), last_name, width=180, height=20, size=12)

                first_name = item.get("fn")
                if first_name:
                    draw_value(DL, dy(1), "%s:" % T("First Name"), width=100, height=20, size=9, bold=False)
                    draw_value(DR, dy(1), first_name, width=180, height=20, size=12)

                dob = item.get("dob")
                if dob:
                    draw_value(DL, dy(2), "%s:" % T("Date of Birth"), width=100, height=20, size=9, bold=False)
                    draw_value(DR, dy(2), dob, width=180, height=20, size=12)
                offset = 3
            else:
                draw_value(DL, dy(0), "%s:" % T("Person Tested"), width=100, height=20, size=9, bold=False)
                draw_value(DR, dy(0), T("anonymous"), width=180, height=20, size=12)
                offset = 1

            dy = lambda rnr: h - 115 - (rnr + offset) * 20
            # Test Station
            site_name = item.get("site_name")
            if site_name:
                draw_value(DL, dy(1), "%s:" % T("Test Station"), width=100, height=20, size=9, bold=False)
                draw_value(DR, dy(1), site_name, width=180, height=20, size=12)
            # Test Date
            test_date = item.get("test_date")
            if test_date:
                draw_value(DL, dy(2), "%s:" % T("Test Date/Time"), width=100, height=20, size=9, bold=False)
                draw_value(DR, dy(2), test_date, width=180, height=20, size=12)
            # Test Result
            result = item.get("result")
            if result:
                draw_value(DL, dy(3), "%s:" % T("Test Result"), width=100, height=20, size=9, bold=False)
                draw_value(DR, dy(3), result, width=180, height=20, size=12)

            # Add a cutting line with multiple cards per page
            if self.multiple:
                c.setDash(1, 2)
                self.draw_outline()
        else:
            # No backside
            pass

# END =========================================================================
