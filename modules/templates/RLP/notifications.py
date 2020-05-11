# -*- coding: utf-8 -*-

import json
import sys

from gluon import DIV, FIELDSET, Field, INPUT, LABEL, \
                  LEGEND, SQLFORM, TEXTAREA, URL, current

from s3compat import basestring

from s3 import s3_fullname, s3_str, S3Method, JSONERRORS
from s3.s3forms import S3SQLSubForm

# =============================================================================
class SafeSub(dict):
    """
        Helper class for safe string variable substitution
    """
    def __missing__(self, key):
        return "{" + key + "}"

# =============================================================================
class DeploymentNotifications(object):
    """
        Helper class to send deployment approval notifications
    """

    def __init__(self, delegation_id):

        self.delegation_id = delegation_id

    # -------------------------------------------------------------------------
    @staticmethod
    def compose(subject, message, data):
        """
            Lookup a subject/message template from CMS and compose subject
            and message using data

            @param subject: the subject template name
            @param message: the message template name

            @returns: tuple (subject_text, message_text),
                      or None if disabled

            Placeholders that are substituted (if data are available):
                {system}..........................System Name
                {start}...........................Start Date of Deployment
                {end}.............................End Date of Deployment
                {comments}........................Comments in Deployment Record
                {volunteer_id}....................Volunteer ID
                {volunteer_name}..................Volunteer full name
                {volunteer_first_name}............Volunteer first name
                {volunteer_last_name}.............Volunteer last name
                {volunteer_email}.................Volunteer email address
                {volunteer_phone}.................Volunteer (mobile) phone number
                {volunteer_office}................Volunteer managing office name
                {volunteer_office_email}..........Volunteer managing office email
                {volunteer_office_phone}..........Volunteer managing office phone
                {organisation}....................Deploying organisation name
                {organisation_email}..............Deploying organisation email
                {organisation_phone}..............Deploying organisation phone
                {coordinator}.....................Name of approving coordinator
                {coordinator_email}...............Coordinator email address
                {coordinator_phone}...............Coordinator phone number
        """

        db = current.db
        s3db = current.s3db

        # Sanitize data
        data = SafeSub(data)
        data["system"] = current.deployment_settings.get_system_name_short()
        for key in data:
            if data[key] is None:
                data[key] = "-"

        # Define join
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "hrm") & \
                         (ltable.resource == "delegation") & \
                         (ltable.deleted == False))

        # Get subject template + substitute
        query = (ctable.name == subject) & (ctable.deleted == False)
        row = db(query).select(ctable.body,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            subject_out = row.body.format_map(data)
        else:
            # Disabled
            return None

        # Get message template + subsitute
        query = (ctable.name == message) & (ctable.deleted == False)
        row = db(query).select(ctable.body,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            message_out = row.body.format_map(data)
        else:
            message_out = ""

        return subject_out, message_out

    # -------------------------------------------------------------------------
    @staticmethod
    def lookup_contact(pe_id, contact_method="EMAIL"):

        db = current.db
        s3db = current.s3db

        ctable = s3db.pr_contact
        query = (ctable.pe_id == pe_id) & \
                (ctable.contact_method == contact_method) & \
                (ctable.deleted == False)
        contact = db(query).select(ctable.value,
                                   limitby = (0, 1),
                                   ).first()

        return contact.value if contact else None

    # -------------------------------------------------------------------------
    def data(self):
        """
            Lookup data to pass into template
        """

        db = current.db
        s3db = current.s3db

        # Lookup delegation
        dtable = s3db.hrm_delegation
        ptable = s3db.pr_person
        join = ptable.on(ptable.id == dtable.person_id)
        query = (dtable.id == self.delegation_id)
        row = db(query).select(dtable.status,
                               dtable.organisation_id,
                               #dtable.person_id,
                               dtable.date,
                               dtable.end_date,
                               dtable.comments,
                               ptable.id,
                               ptable.pe_id,
                               ptable.pe_label,
                               ptable.first_name,
                               ptable.middle_name,
                               ptable.last_name,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if not row: # or row.status != "APPR":
            return None

        delegation = row.hrm_delegation
        person = row.pr_person
        person_id = person.id
        if not person_id:
            return None

        lookup_contact = self.lookup_contact

        data = {"start": dtable.date.represent(delegation.date),
                "end": dtable.end_date.represent(delegation.end_date),
                "comments": delegation.comments,
                "volunteer_id": person.pe_label,
                "volunteer_name": s3_fullname(person),
                "volunteer_first_name": person.first_name,
                "volunteer_last_name": person.last_name,
                "volunteer_email": lookup_contact(person.pe_id, "EMAIL"),
                "volunteer_phone": lookup_contact(person.pe_id, "SMS"),
                "volunteer_uri": URL(c = "vol",
                                     f = "person",
                                     args = [person_id],
                                     host = True,
                                     )
                }

        # Lookup volunteer office
        htable = s3db.hrm_human_resource
        stable = s3db.org_office
        left = stable.on((stable.site_id == htable.site_id) & \
                         (stable.deleted == False))
        query = (htable.person_id == person_id) & \
                (htable.type == 2) & \
                (htable.deleted == False)
        row = db(query).select(stable.name,
                               stable.email,
                               stable.phone1,
                               left = left,
                               limitby = (0, 1),
                               orderby = ~htable.created_on,
                               ).first()
        if row and row.name:
            data.update({"volunteer_office": row.name,
                         "volunteer_office_email": row.email,
                         "volunteer_office_phone": row.phone1,
                         })

        # Lookup requesting org and office
        otable = s3db.org_organisation
        left = stable.on((stable.organisation_id == otable.id) & \
                         (stable.deleted == False))
        query = (otable.id == delegation.organisation_id)
        row = db(query).select(otable.name,
                               stable.email,
                               stable.phone1,
                               left = left,
                               limitby = (0, 1),
                               orderby = stable.created_on,
                               ).first()
        if row:
            data.update({"organisation": row.org_organisation.name,
                         "organisation_email": row.org_office.email,
                         "organisation_phone": row.org_office.phone1,
                         })

        # Lookup current user (=coordinator)
        user = current.auth.user
        if user and user.pe_id:
            user_pe_id = user.pe_id
            data.update({"coordinator": s3_fullname(pe_id=user_pe_id),
                         "coordinator_email": lookup_contact(user_pe_id, "EMAIL"),
                         "coordinator_phone": lookup_contact(user_pe_id, "SMS"),
                         })

        return data

    # -------------------------------------------------------------------------
    def send(self):
        """
            Send notification emails
        """

        T = current.T

        data = self.data()

        cc = data.get("coordinator_email")

        warnings = []
        send_email = current.msg.send_email

        success = False
        email = data.get("organisation_email")
        if email:
            message = self.compose("Subject Organisation", "Message Organisation", data)
            if message:
                success = send_email(to = email,
                                     cc = cc,
                                     subject = message[0],
                                     message = message[1],
                                     )
        if not success:
            warnings.append(T("Organisation could not be notified"))

        success = False
        email = data.get("volunteer_email")
        if email:
            message = self.compose("Subject Volunteer", "Message Volunteer", data)
            if message:
                success = send_email(to = email,
                                     cc = cc,
                                     subject = message[0],
                                     message = message[1],
                                     )
        if not success:
            warnings.append(T("Volunteer could not be notified"))

        success = False
        email = data.get("volunteer_office_email")
        if email:
            message = self.compose("Subject Office", "Message Office", data)
            if message:
                success = send_email(to = email,
                                     cc = cc,
                                     subject = message[0],
                                     message = message[1],
                                     )
        if not success:
            warnings.append(T("Volunteer Office could not be notified"))

        if warnings:
            current.response.warning = ", ".join(s3_str(w) for w in warnings)
        else:
            current.session.information = T("Notifications sent")

    # -------------------------------------------------------------------------
    def json(self):
        """
            Produce the notification emails as JSON-serializable dict

            @returns: a dict of dicts of the structure:
                         {recipient_type: {email, subject, message}}
        """

        data = self.data()

        output = {"cc": data.get("coordinator_email")}

        email = data.get("organisation_email")
        if email:
            message = self.compose("Subject Organisation", "Message Organisation", data)
            if message:
                output["organisation"] = {"email": email,
                                          "subject": message[0],
                                          "message": message[1],
                                          }

        email = data.get("volunteer_email")
        if email:
            message = self.compose("Subject Volunteer", "Message Volunteer", data)
            if message:
                output["volunteer"] = {"email": email,
                                       "subject": message[0],
                                       "message": message[1],
                                       }

        email = data.get("volunteer_office_email")
        if email:
            message = self.compose("Subject Office", "Message Office", data)
            if message:
                output["office"] = {"email": email,
                                    "subject": message[0],
                                    "message": message[1],
                                    }

        return output

# =============================================================================
class InlineNotificationsCompose(S3Method):
    """
        Ajax-method to compose the notification messages for a delegation
    """

    def apply_method(self, r, **attr):
        """
            Entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        response = current.response
        output = None

        if not r.record:
            # Must have a delegation record
            r.error(404, current.ERROR.BAD_RECORD)
        if not self._permitted("update"):
            # Must be permitted to update the delegation
            r.unauthorised()

        if r.http == "GET":
            if r.representation == "json":
                notifications = DeploymentNotifications(r.record.id)
                response.headers["Content-Type"] = "application/json"
                output = json.dumps(notifications.json())
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

# =============================================================================
class InlineNotifications(S3SQLSubForm):
    """
        Subform to compose and edit notifications for a delegation
    """

    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            @param resource: the resource
            @return: a tuple (self, None, Field instance)
        """

        # Check permission
        permitted = current.auth.s3_has_permission("update", resource.table)
        if not permitted:
            return (None, None, None)

        options = self.options

        if "name" in options:
            self.alias = options["name"]
            label = self.alias
        else:
            self.alias = "inline"
            label = self.selector

        if "label" in options:
            label = options["label"]
        else:
            label = " ".join([s.capitalize() for s in label.split("_")])

        fname = self._formname()
        field = Field(fname, "json",
                      label = label,
                      represent = self.represent,
                      requires = self.parse,
                      widget = self,
                      )

        return (self, None, field)

    # -------------------------------------------------------------------------
    def _formname(self):
        """
            Produce a unique prefix for elements in this subform

            @returns: the prefix as string
        """

        return "%s_%s" % (self.alias, self.selector)

    # -------------------------------------------------------------------------
    def extract(self, resource, record_id):
        """
            Initialize this form element for a particular record. This
            method will be called by the form renderer to populate the
            form for an existing record.

            @param resource: the resource the record belongs to
            @param record_id: the record ID

            @return: the value for the input field that corresponds
                     to the specified record.
        """

        return {"delegationID": record_id} if record_id else {}

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Validator method, converts the JSON returned from the input
            field into a Python object.

            @param value: the JSON from the input field.
            @return: tuple of (value, error), where value is the converted
                      JSON, and error the error message if the decoding
                      fails, otherwise None
        """

        # @todo: catch uploads during validation errors
        if isinstance(value, basestring):
            try:
                value = json.loads(value)
            except JSONERRORS:
                error = sys.exc_info()[1]
                if hasattr(error, "message"):
                    error = error.message
            else:
                error = None
        else:
            value = None
            error = None

        return (value, error)

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field; to be set as widget=self
            for the field returned by the resolve()-method.

            @param field: the input field
            @param value: the value to populate the widget
            @param attributes: attributes for the widget
            @return: the widget for this form element as HTML helper
        """

        T = current.T
        settings = current.deployment_settings

        # Check current value (must have a delegation ID)
        if isinstance(value, str):
            try:
                value = json.loads(value) if value else {}
            except JSONERRORS:
                value = {}
        delegation_id = value.get("delegationID")
        if not delegation_id:
            return "-"

        # Form name and widget ID
        formname = self._formname()
        widget_id = attributes.get("_id")
        if not widget_id:
            widget_id = str(field).replace(".", "_")

        # Inject script
        options = {"ajaxURL": URL(c = "hrm",
                                  f = "delegation",
                                  args = [delegation_id,
                                          "notifications.json",
                                          ],
                                  ),
                   "formName": formname,
                   }
        self.inject_js(widget_id, options)

        # The widget
        widget = DIV(INPUT(_type = "hidden",
                           _name = field.name,
                           _value = json.dumps(value),
                           _class = "notification-data",
                           ),
                     _id = widget_id,
                     )

        # Add field set per recipient type
        labels = {"organisation": T("Requesting Organisation"),
                  "volunteer": T("Volunteer"),
                  "office": T("Office##gov"),
                  }
        formstyle = settings.get_ui_formstyle()
        for recipient in ("organisation", "volunteer", "office"):
            input_name = "%s_%s" % (formname, recipient)
            formfields = [Field("%s_email" % input_name,
                                label = T("Email"),
                                ),
                          Field("%s_subject" % input_name,
                                label = T("Subject"),
                                ),
                          Field("%s_message" % input_name, "text",
                                label = T("Message"),
                                widget = self.message_widget,
                                ),
                          ]
            form = SQLFORM.factory(record = None,
                                   showid = False,
                                   formstyle = formstyle,
                                   buttons = [],
                                   table_name = "sub",
                                   *formfields)
            toggle_name = "%s_notify_%s" % (formname, recipient)
            subform = DIV(FIELDSET(LEGEND(LABEL(INPUT(_type="checkbox",
                                                      _class="notify-toggle",
                                                      value=True,
                                                      _name=toggle_name,
                                                      _id=toggle_name,
                                                      ),
                                                labels.get(recipient, "?"),
                                                ),
                                          ), form[0]),
                          _class = "notification",
                          )
            widget.append(subform)

        return widget

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Read-only representation of this form element.

            @param value: the value as returned from extract()
            @return: the read-only representation of this element as
                     string or HTML helper
        """

        return "-"

    # -------------------------------------------------------------------------
    def accept(self, form, master_id=None, format=None):
        """
            Post-process this form element and perform the related
            transactions. This method will be called after the main
            form has been accepted, where the master record ID will
            be provided.

            @param form: the form
            @param master_id: the master record ID
            @param format: the data format extension
            @return: True on success, False on error

            TODO store the messages in component of delegation record
        """

        form_vars = form.vars

        status = form_vars.get("status")
        if not master_id or status != "APPR":
            # Do nothing
            return True

        T = current.T
        formname = self._formname()

        # CC current user (=coordinator)
        user = current.auth.user
        if user and user.pe_id:
            cc = DeploymentNotifications.lookup_contact(user.pe_id)
        else:
            cc = None

        warnings = []
        send_email = current.msg.send_email

        # Send notification to requesting organisation
        success = False
        notify_organisation = form_vars.get("%s_notify_organisation" % formname)
        if notify_organisation:
            email = form_vars.get("%s_organisation_email" % formname)
            if email:
                subject = form_vars.get("%s_organisation_subject" % formname)
                message = form_vars.get("%s_organisation_message" % formname)
                if subject and message:
                    success = send_email(to = email,
                                         cc = cc,
                                         subject = subject,
                                         message = message,
                                         )
        if not success:
            warnings.append(T("Organisation could not be notified"))

        # Send notification to volunteer
        success = False
        notify_volunteer = form_vars.get("%s_notify_volunteer" % formname)
        if notify_volunteer:
            email = form_vars.get("%s_volunteer_email" % formname)
            if email:
                subject = form_vars.get("%s_volunteer_subject" % formname)
                message = form_vars.get("%s_volunteer_message" % formname)
                if subject and message:
                    success = send_email(to = email,
                                         cc = cc,
                                         subject = subject,
                                         message = message,
                                         )
        if not success:
            warnings.append(T("Volunteer could not be notified"))

        # Send notification to managing office
        success = False
        notify_office = form_vars.get("%s_notify_office" % formname)
        if notify_office:
            email = form_vars.get("%s_office_email" % formname)
            if email:
                subject = form_vars.get("%s_office_subject" % formname)
                message = form_vars.get("%s_office_message" % formname)
                if subject and message:
                    success = send_email(to = email,
                                         cc = cc,
                                         subject = subject,
                                         message = message,
                                         )
        if not success:
            warnings.append(T("Volunteer Office could not be notified"))

        # Screen messages
        if warnings:
            current.response.warning = ", ".join(s3_str(w) for w in warnings)
        else:
            current.session.information = T("Notifications sent")

        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def message_widget(field, value, **attr):
        """
            Smaller than usual textarea for editing message texts

            @param field: the Field
            @param value: the current field value
            @param attr: DOM attributes for the widget
        """

        widget_id = attr.get("_id")
        if not widget_id:
            widget_id = "%s_%s" % (field._tablename, field.name)

        return TEXTAREA(_name = attr.get("_name", field.name),
                        _id = widget_id,
                        _class = "message %s" % (field.type),
                        _placeholder = attr.get("_placeholder"),
                        _rows = 6,
                        value = value,
                        requires = field.requires,
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_js(widget_id, options):
        """
            Helper function to inject static JS and instantiate
            the foodRegistration widget

            @param widget_id: the node ID where to instantiate the widget
            @param options: dict of widget options (JSON-serializable)
        """

        s3 = current.response.s3
        appname = current.request.application

        # Inject script
        # TODO minify?
        scripts = s3.scripts
        script = "/%s/static/themes/RLP/js/notifications.js" % appname
        if script not in scripts:
            scripts.append(script)

        # Instantiate widget
        if not options:
            options = {}
        scripts = s3.jquery_ready
        script = '''$('#%(id)s').rlpNotifications(%(options)s)''' % \
                 {"id": widget_id,
                  "options": json.dumps(options),
                  }
        if script not in scripts:
            scripts.append(script)

# END =========================================================================
