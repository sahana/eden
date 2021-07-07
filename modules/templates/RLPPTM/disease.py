# -*- coding: utf-8 -*-

"""
    Disease reporting customisations for RLPPTM template

    @license: MIT
"""

from gluon import current, \
                  DIV, Field, INPUT, IS_IN_SET, SQLFORM

from s3 import S3CustomController, S3Method, s3_date, s3_mark_required

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
        # TODO translations

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
        # TODO option to skip validation of mandatory options
        consent = s3db.auth_Consent(processing_types=["CWA_ANONYMOUS", "CWA_PERSONAL"])

        # Form Fields
        table = s3db.disease_case_diagnostics
        field = table.disease_id
        if field.writable:
            offset = 1
        else:
            field.readable = False
            offset = 0

        cwa = {"system": "RKI / Corona-Warn-App"}
        cwa_options = (("NO", T("Do not report")),
                       ("ANONYMOUS", T("Issue anonymous contact tracing code")),
                       ("PERSONAL", T("Issue personal test certificate")),
                       )
        formfields = [# -- Test Result --
                      table.site_id,
                      table.disease_id,
                      table.result_date,
                      table.result,

                      # -- Report to CWA --
                      Field("report_to_cwa", "string",
                            requires = IS_IN_SET(cwa_options, sort=False, zero=""),
                            default = "NO",
                            label = T("Report test result to %(system)s") % cwa,
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
                      # TODO Styling
                      # TODO Prepop-options + upgrade-script to deploy
                      Field("consent",
                            label = "",
                            widget = consent.widget,
                            ),
                      ]

        # Required fields
        required_fields = []

        # Subheadings
        subheadings = ((0, T("Test Result")),
                       (3 + offset, cwa["system"]),
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

            #formvars = form.vars

            # Create disease_case_diagnostics record + onaccept

            # if report_to_cwa is NO
            #   confirmation message
            #   redirect to form
            # else
            #   register consent
            #   generate JSON for QR-code
            #   generate HASH
            #   send to corona-app
            #   if successful:
            #       confirmation message
            #   else:
            #       error message
            #   generate certificate view with QR-code

            return "registered" # TESTING

        elif form.errors:
            current.response.error = T("There are errors in the form, please check your input")

        # Custom View
        response.view = "create.html"
        # TODO Implement custom view to include intro
        #S3CustomController._view("RLPPTM", "register.html")

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

    # -------------------------------------------------------------------------
    def certify(self, r, **attr):
        """
            Generate a test certificate (PDF) for download

            @param r: the S3Request instance
            @param attr: controller attributes
        """
        # TODO implement

        if not r.record:
            r.error(400, current.ERROR.BAD_REQUEST)
        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)
        if r.representation != "pdf":
            r.error(415, current.ERROR.BAD_FORMAT)

        return "certify"

    # -------------------------------------------------------------------------
    def cwaretry(self, r, **attr):
        """
            Retry sending test result to CWA result server

            @param r: the S3Request instance
            @param attr: controller attributes
        """
        # TODO implement

        if not r.record:
            r.error(400, current.ERROR.BAD_REQUEST)
        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)
        if r.representation != "json":
            r.error(415, current.ERROR.BAD_FORMAT)

        return "cwaretry"

# END =========================================================================
