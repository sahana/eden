# -*- coding: utf-8 -*-

from gluon import current

from s3 import s3_fullname, s3_str

# =============================================================================
class safesub(dict):
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
    def compose(self, subject, message, data):
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
        data = safesub(data)
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
    def data(self):
        """
            Lookup data to pass into template
        """

        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings

        # Lookup delegation
        table = s3db.hrm_delegation
        query = (table.id == self.delegation_id)
        delegation = db(query).select(table.status,
                                      table.organisation_id,
                                      table.person_id,
                                      table.date,
                                      table.end_date,
                                      table.comments,
                                      limitby = (0, 1),
                                      ).first()
        if not delegation: # or delegation.status != "APPR":
            return None

        data = {"start": table.date.represent(delegation.date),
                "end": table.end_date.represent(delegation.end_date),
                "comments": delegation.comments,
                }

        # Lookup volunteer person
        ptable = s3db.pr_person
        query = (ptable.id == delegation.person_id)
        person = db(query).select(ptable.pe_id,
                                  ptable.pe_label,
                                  ptable.first_name,
                                  ptable.middle_name,
                                  ptable.last_name,
                                  limitby = (0, 1),
                                  ).first()
        if not person:
            return None
        data["volunteer_id"] = person.pe_label
        data["volunteer_name"] = s3_fullname(person)
        data["volunteer_first_name"] = person.first_name
        data["volunteer_last_name"] = person.last_name

        # Lookup volunteer email
        ctable = s3db.pr_contact
        query = (ctable.pe_id == person.pe_id) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.deleted == False)
        contact = db(query).select(ctable.value,
                                   limitby = (0, 1),
                                   ).first()
        data["volunteer_email"] = contact.value if contact else None

        # Lookup volunteer mobile phone
        ctable = s3db.pr_contact
        query = (ctable.pe_id == person.pe_id) & \
                (ctable.contact_method == "SMS") & \
                (ctable.deleted == False)
        contact = db(query).select(ctable.value,
                                   limitby = (0, 1),
                                   ).first()
        data["volunteer_phone"] = contact.value if contact else None

        # Lookup volunteer office
        htable = s3db.hrm_human_resource
        stable = s3db.org_office
        left = stable.on((stable.site_id == htable.site_id) & \
                         (stable.deleted == False))
        query = (htable.person_id == delegation.person_id) & \
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
            data["volunteer_office"] = row.name
            data["volunteer_office_email"] = row.email
            data["volunteer_office_phone"] = row.phone1

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
            data["organisation"] = row.org_organisation.name
            data["organisation_email"] = row.org_office.email
            data["organisation_phone"] = row.org_office.phone1

        # Lookup current user (=coordinator)
        user = current.auth.user
        if user:
            data["coordinator"] = s3_fullname(pe_id=user.pe_id)
            ctable = s3db.pr_contact
            query = (ctable.pe_id == user.pe_id) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.deleted == False)
            contact = db(query).select(ctable.value,
                                       limitby = (0, 1),
                                       ).first()
            data["coordinator_email"] = contact.value if contact else None

            # Lookup volunteer mobile phone
            ctable = s3db.pr_contact
            query = (ctable.pe_id == user.pe_id) & \
                    (ctable.contact_method == "SMS") & \
                    (ctable.deleted == False)
            contact = db(query).select(ctable.value,
                                       limitby = (0, 1),
                                       ).first()
            data["coordinator_phone"] = contact.value if contact else None

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
