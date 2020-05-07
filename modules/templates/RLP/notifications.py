# -*- coding: utf-8 -*-

from gluon import current

from s3 import s3_fullname, s3_str

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
        if not person.id:
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
                }

        # Lookup volunteer office
        htable = s3db.hrm_human_resource
        stable = s3db.org_office
        left = stable.on((stable.site_id == htable.site_id) & \
                         (stable.deleted == False))
        query = (htable.person_id == person.id) & \
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

# END =========================================================================
