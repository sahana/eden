# -*- coding: utf-8 -*-

import json
import re
import sys

from gluon import current, Field, SQLFORM, URL, \
                  A, DIV, FIELDSET, H6, INPUT, LABEL, LEGEND, P, TEXTAREA

from s3 import s3_fullname, s3_str, S3Method, JSONERRORS
from s3.s3forms import S3SQLSubForm

PLACEHOLDER = re.compile(r"\{([^{}]+)\}")

# =============================================================================
def formatmap(template, mapping):
    """
        Helper to replace placeholders in template using mapping

        @param: template, a string containing placeholders of the format {name}
        @param: mapping, a dict mapping placeholders to values
    """
    def repl(match):
        key = match.group(1)
        return s3_str(mapping.get(key, match.group(0)))
    return PLACEHOLDER.sub(repl, template)

# =============================================================================
class DeploymentNotifications(object):
    """
        Helper class to send deployment approval notifications
    """

    def __init__(self, delegation_id, sender=None):
        """
            Constructor

            @param delegation_id: the hrm_delegation record ID
            @param sender: the sender type
        """

        self.delegation_id = delegation_id

        if sender == "org":
            # Notifications from the Deploying Organisation
            self.recipients = {"volunteer": ("OrgToVolunteer", False),
                               }
        else:
            # Notifications from the Pool Coordinator
            self.recipients = {"volunteer": ("Volunteer", True),
                               "organisation": ("Organisation", True),
                               "office": ("Office", True),
                               }

    # -------------------------------------------------------------------------
    @classmethod
    def compose(cls, templates, data):
        """
            Compose subject/message from templates using data

            @param templates: a tuple of string templates (subject, message),
                              or the name of the template-pair, e.g. "Volunteer"
            @param data: a dict of data to substitute placeholders in the templates

            @returns: tuple (subject, message), or None if disabled

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
                {volunteer_uri}...................URI of the volunteer record
                {organisation}....................Deploying organisation name
                {organisation_email}..............Deploying organisation email
                {organisation_phone}..............Deploying organisation phone
                {organisation_street}.............Deploying organisation street address
                {organisation_postcode}...........Deploying organisation postcode
                {organisation_place}..............Deploying organisation place name (L4|L3)
                {coordinator}.....................Name of approving coordinator
                {coordinator_email}...............Coordinator email address
                {coordinator_phone}...............Coordinator phone number
                {deployment_uri}..................URI of the deployment
        """

        # Sanitize data
        if not isinstance(data, dict):
            data = {}
        for key in data:
            if data[key] is None:
                data[key] = "-"

        if isinstance(templates, str):
            templates = cls.templates(templates)

        if not isinstance(templates, (tuple, list)):
            return None

        subject = formatmap(templates[0], data)
        message = formatmap(templates[1], data)

        return subject, message

    # -------------------------------------------------------------------------
    @staticmethod
    def templates(name):
        """
            Get message templates

            @param name: the name of the template-pair, e.g. "Volunteer"

            @returns: tuple (subject_template, message_template), or None
        """

        db = current.db
        s3db = current.s3db

        if not name:
            return None

        # Define join
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "hrm") & \
                         (ltable.resource == "delegation") & \
                         (ltable.deleted == False))

        # Get subject template
        subject_name = "Subject %s" % name
        query = (ctable.name == subject_name) & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            subject_template = row.body
        else:
            # Disabled
            return None

        # Get message template
        message_name = "Message %s" % name
        query = (ctable.name == message_name) & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            message_template = row.body
        else:
            message_template = ""

        return subject_template, message_template

    # -------------------------------------------------------------------------
    def data(self):
        """
            Lookup data to pass into template

            @returns: the data as dict
        """

        db = current.db
        s3db = current.s3db

        dtable = s3db.hrm_delegation
        ptable = s3db.pr_person

        delegation_id = self.delegation_id
        if delegation_id:
            # Lookup delegation
            dtable = s3db.hrm_delegation
            ptable = s3db.pr_person
            join = ptable.on(ptable.id == dtable.person_id)
            query = (dtable.id == self.delegation_id)
            row = db(query).select(dtable.organisation_id,
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
            if not row:
                return None
            person = row.pr_person
            person_id = person.id
            if not person_id:
                return None
            delegation = row.hrm_delegation

        else:
            # Use defaults
            person_id = dtable.person_id.default
            if not person_id:
                return None

            query = (ptable.id == person_id)
            person = db(query).select(ptable.id,
                                      ptable.pe_id,
                                      ptable.pe_label,
                                      ptable.first_name,
                                      ptable.middle_name,
                                      ptable.last_name,
                                      limitby = (0, 1),
                                      ).first()
            if not person:
                return None

            fields = ("organisation_id", "date", "end_date", "comments")
            from gluon.storage import Storage
            delegation = Storage({fn: dtable[fn].default for fn in fields})

        lookup_contact = self.lookup_contact

        data = {"system": current.deployment_settings.get_system_name_short(),
                "start": dtable.date.represent(delegation.date),
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
                                     ),
                }
        if delegation_id:
            data["deployment_uri"] = URL(c = "hrm",
                                         f = "delegation",
                                         args = [delegation_id],
                                         host = True,
                                         )

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
        ftable = s3db.org_facility
        organisation_id = delegation.organisation_id

        query = (otable.id == organisation_id)
        organisation = db(query).select(otable.name,
                                        otable.pe_id,
                                        limitby = (0, 1),
                                        ).first()
        if organisation:
            data["organisation"] = organisation.name
            org_email = lookup_contact(organisation.pe_id, "EMAIL")

            site_email = None
            site_phone = None
            location_id = None

            # Lookup facility for address and phone number
            query = (ftable.organisation_id == organisation_id) & \
                    (ftable.obsolete == False) & \
                    (ftable.deleted == False)
            row = db(query).select(ftable.email,
                                   ftable.phone1,
                                   ftable.location_id,
                                   limitby = (0, 1),
                                   orderby = ftable.created_on,
                                   ).first()
            if not row:
                # Fall back to office
                query = (stable.organisation_id == organisation_id) & \
                        (stable.obsolete == False) & \
                        (stable.deleted == False)
                row = db(query).select(stable.email,
                                       stable.phone1,
                                       stable.location_id,
                                       limitby = (0, 1),
                                       orderby = stable.created_on,
                                       ).first()
            if row:
                site_email = row.email
                site_phone = row.phone1
                location_id = row.location_id

            data.update({"organisation_email": org_email if org_email else site_email,
                         "organisation_phone": site_phone,
                         })

            if location_id:
                # Lookup address details
                ltable = s3db.gis_location
                query = (ltable.id == location_id) & \
                        (ltable.deleted == False)
                location = db(query).select(ltable.addr_street,
                                            ltable.addr_postcode,
                                            ltable.L3,
                                            ltable.L4,
                                            limitby = (0, 1),
                                            ).first()
                if location:
                    place = location.L4 or location.L3 # L4 is optional
                    if place:
                        data["organisation_place"] = place
                    if location.addr_postcode:
                        data["organisation_postcode"] = location.addr_postcode
                    if location.addr_street:
                        data["organisation_street"] = location.addr_street

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
    @staticmethod
    def lookup_contact(pe_id, contact_method="EMAIL"):
        """
            Look up contact number/address for a PE

            @param pe_id: the PE_ID
            @param contact_method: the contact method

            @returns: the contact/number address, or None if not found
        """

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
    def send(self):
        """
            Send notification emails (unconditionally, onaccept)

            TODO: unused - deprecate?
        """

        T = current.T

        data = self.data()

        cc = data.get("coordinator_email")

        warnings = []
        send_email = current.msg.send_email

        success = False
        email = data.get("organisation_email")
        if email:
            message = self.compose("Organisation", data)
            if message:
                success = send_email(to = email,
                                     cc = cc,
                                     subject = message[0],
                                     message = message[1],
                                     )
                self.save(email, message[0], message[1],
                          status = "SENT" if success else "FAILED",
                          )
        if not success:
            warnings.append(T("Organization could not be notified"))

        success = False
        email = data.get("volunteer_email")
        if email:
            message = self.compose("Volunteer", data)
            if message:
                success = send_email(to = email,
                                     cc = cc,
                                     subject = message[0],
                                     message = message[1],
                                     )
                self.save(email, message[0], message[1],
                          status = "SENT" if success else "FAILED",
                          )
        if not success:
            warnings.append(T("Volunteer could not be notified"))

        success = False
        email = data.get("volunteer_office_email")
        if email:
            message = self.compose("Office", data)
            if message:
                success = send_email(to = email,
                                     cc = cc,
                                     subject = message[0],
                                     message = message[1],
                                     )
                self.save(email, message[0], message[1],
                          status = "SENT" if success else "FAILED",
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
        if not data:
            return {}

        for key, value in list(data.items()):
            if value is None:
                data[key] = "-"
            else:
                data[key] = s3_str(value)

        output = {"delegationID": self.delegation_id,
                  "data": data,
                  "email": {},
                  "autoSelect": {},
                  "cc": data.get("coordinator_email"),
                  "templates": {},
                  }

        recipients = self.recipients
        for recipient in ("organisation", "volunteer", "office"):

            config = recipients.get(recipient)
            if not config:
                continue
            template_name, auto_select = config

            templates = self.templates(template_name)
            if templates:
                output["templates"][recipient] = {"subject": templates[0],
                                                  "message": templates[1],
                                                  }
            else:
                continue

            if recipient == "office":
                email = data.get("volunteer_office_email")
            else:
                email = data.get("%s_email" % recipient)
            if email:
                output["email"][recipient] = email

            output["autoSelect"][recipient] = auto_select

        return output

    # -------------------------------------------------------------------------
    def save(self, recipient, subject, message, status=None):
        """
            Save a notification in the message journal of the
            delegation.

            @param recipient: the recipient name or email
            @param subject: the message subject
            @param message: the message text
            @param status: the status of the message SENT|FAILED
        """

        s3db = current.s3db

        table = s3db.hrm_delegation_message
        table.insert(delegation_id = self.delegation_id,
                     recipient = recipient,
                     subject = subject,
                     message = message,
                     status = status or "SENT",
                     )

# =============================================================================
class InlineNotificationsData(S3Method):
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

        if not self._permitted("update"):
            # Must be permitted to update delegations
            r.unauthorised()

        if r.http == "GET":
            if r.representation == "json":
                delegation_id = r.record.id if r.record else None
                sender = r.get_vars.get("sender")
                notifications = DeploymentNotifications(delegation_id, sender=sender)
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

        Constructor options:
            label         - the label for the subform
            person_id     - the default person_id for new delegations
            recipients    - the possible recipients for notifications,
                            tuple of strings:

                volunteer......the volunteer themselves
                organisation...the requesting organisation
                office.........the office where the volunteer normally works

            organisations - the names of selectable organisations, a dict
                            {organisation_id: organisation_name}
            reply_to      - where replies to notification emails should go
                            instead of the server's email address:
                            string "coordinator"|"organisation"
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
    def parse(self, value, record_id=None):
        """
            Validator method, converts the JSON returned from the input
            field into a Python object.

            @param value: the JSON from the input field.
            @param record_id: usused (for API compatibility with validators)
            @return: tuple of (value, error), where value is the converted
                      JSON, and error the error message if the decoding
                      fails, otherwise None
        """

        if isinstance(value, str):
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

        # Check current value
        if isinstance(value, str):
            try:
                value = json.loads(value) if value else {}
            except JSONERRORS:
                value = {}
        elif not value:
            value = {}
        delegation_id = value.get("delegationID") if value else None

        # Form name and widget ID
        formname = self._formname()
        widget_id = attributes.get("_id")
        if not widget_id:
            widget_id = str(field).replace(".", "_")

        # Ajax parameters
        if delegation_id:
            ajax_args = [delegation_id, "notifications.json"]
            ajax_vars = {}
        else:
            ajax_args = ["notifications.json"]
            dtable = current.s3db.hrm_delegation
            person_id = dtable.person_id.default
            ajax_vars = {"viewing": "pr_person.%s" % person_id} if person_id else {}

        # Sender and recipient types
        sender = self.options.get("sender")
        if sender:
            ajax_vars["sender"] = sender
        notifications = DeploymentNotifications(delegation_id, sender=sender)
        recipients = list(notifications.recipients.keys())

        # Selectable organisations
        organisations = self.options.get("organisations")

        # Inject script
        options = {"ajaxURL": URL(c = "hrm",
                                  f = "delegation",
                                  args = ajax_args,
                                  vars = ajax_vars,
                                  ),
                   "formName": formname,
                   "recipients": recipients,
                   "organisations": organisations,
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
        for recipient in recipients:
            input_name = "%s_%s" % (formname, recipient)
            formfields = [Field("%s_email" % input_name,
                                label = T("Email"),
                                ),
                          Field("%s_subject" % input_name,
                                label = T("Subject"),
                                widget = self.subject_widget,
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

            toggle_edit = DIV(A(T("Preview"),
                                _class="preview-toggle action-lnk",
                                _style="display:none",
                                ),
                              A(T("Edit"),
                                _class="preview-toggle action-lnk",
                                ),
                              _class="preview-toggles",
                              )
            subform = DIV(FIELDSET(LEGEND(LABEL(INPUT(_type="checkbox",
                                                      _class="notify-toggle",
                                                      value=True,
                                                      _name=toggle_name,
                                                      _id=toggle_name,
                                                      ),
                                                labels.get(recipient, "?"),
                                                ),
                                          ),
                                   form[0],
                                   toggle_edit,
                                   ),
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
        """

        form_vars = form.vars

        status = form_vars.get("status")
        if not master_id or status != "APPR":
            # Do nothing
            return True

        sender = self.options.get("sender")
        notifications = DeploymentNotifications(master_id, sender=sender)

        T = current.T
        formname = self._formname()

        # CC current user (=coordinator)
        user = current.auth.user
        if user and user.pe_id:
            cc = notifications.lookup_contact(user.pe_id)
        else:
            cc = None

        warnings = []
        send_email = current.msg.send_email

        data = notifications.data()

        # Alternative recipient for replies?
        reply_to_type = self.options.get("reply_to")
        if reply_to_type == "org":
            reply_to = data.get("organisation_email")
        elif reply_to_type == "user":
            reply_to = data.get("coordinator_email")
        else:
            reply_to = None

        # Send notification to requesting organisation
        notify_organisation = form_vars.get("%s_notify_organisation" % formname)
        if notify_organisation:
            success = False
            email = form_vars.get("%s_organisation_email" % formname)
            if email:
                # Get the templates
                subject = form_vars.get("%s_organisation_subject" % formname)
                message = form_vars.get("%s_organisation_message" % formname)
                if subject and message:
                    subject, message = notifications.compose((subject, message),
                                                             data,
                                                             )
                    success = send_email(to = email,
                                         cc = cc,
                                         subject = subject,
                                         message = message,
                                         )
                    notifications.save(email, subject, message,
                                       status = "SENT" if success else "FAILED",
                                       )
            if not success:
                warnings.append(T("Organisation could not be notified"))

        # Send notification to volunteer
        notify_volunteer = form_vars.get("%s_notify_volunteer" % formname)
        if notify_volunteer:
            success = False
            email = form_vars.get("%s_volunteer_email" % formname)
            if email:
                subject = form_vars.get("%s_volunteer_subject" % formname)
                message = form_vars.get("%s_volunteer_message" % formname)
                if subject and message:
                    subject, message = notifications.compose((subject, message),
                                                             data,
                                                             )
                    success = send_email(to = email,
                                         cc = cc,
                                         subject = subject,
                                         message = message,
                                         reply_to = reply_to,
                                         )
                    notifications.save(email, subject, message,
                                       status = "SENT" if success else "FAILED",
                                       )
            if not success:
                warnings.append(T("Volunteer could not be notified"))

        # Send notification to managing office
        notify_office = form_vars.get("%s_notify_office" % formname)
        if notify_office:
            success = False
            email = form_vars.get("%s_office_email" % formname)
            if email:
                subject = form_vars.get("%s_office_subject" % formname)
                message = form_vars.get("%s_office_message" % formname)
                if subject and message:
                    subject, message = notifications.compose((subject, message),
                                                             data,
                                                             )
                    success = send_email(to = email,
                                         cc = cc,
                                         subject = subject,
                                         message = message,
                                         reply_to = reply_to,
                                         )
                    notifications.save(email, subject, message,
                                       status = "SENT" if success else "FAILED",
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
    def subject_widget(field, value, **attr):
        """
            Widget to edit and preview a notification subject line

            @param field: the Field
            @param value: the current field value
            @param attr: DOM attributes for the widget
        """

        widget_id = attr.get("_id")
        if not widget_id:
            widget_id = "%s_%s" % (field._tablename, field.name)

        edit = INPUT(_name = attr.get("_name", field.name),
                     _id = widget_id,
                     _type="text",
                     _class = "subject %s" % (field.type),
                     _placeholder = attr.get("_placeholder"),
                     _style = "display:none",
                     value = value,
                     requires = field.requires
                     )

        preview = H6("", _class="preview")

        return DIV(preview, edit, _class = "preview-widget")

    # -------------------------------------------------------------------------
    @staticmethod
    def message_widget(field, value, **attr):
        """
            Widget to edit and preview a notification message body

            @param field: the Field
            @param value: the current field value
            @param attr: DOM attributes for the widget
        """

        widget_id = attr.get("_id")
        if not widget_id:
            widget_id = "%s_%s" % (field._tablename, field.name)

        edit = TEXTAREA(_name = attr.get("_name", field.name),
                        _id = widget_id,
                        _class = "message %s" % (field.type),
                        _placeholder = attr.get("_placeholder"),
                        _rows = 6,
                        _style = "display:none",
                        value = value,
                        requires = field.requires,
                        )

        preview = P("", _class="preview")

        return DIV(preview, edit, _class = "preview-widget")

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
