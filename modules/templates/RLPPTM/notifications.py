# -*- coding: utf-8 -*-

import re

from gluon import current

from s3 import s3_str

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
class CMSNotifications(object):
    """
        Helper class to send CMS-based Notifications
    """

    @classmethod
    def send(cls, email, template, data, cc=None, module="cms", resource="post"):
        """
            Send notification emails

            @param email: the recipient email address (or list|tuple of email addresses)
            @param template: suffix of the CMS posts containing the subject
                             and message templates

            @param data: dict of data to substitute placeholders in the template
            @param cc: list of cc-recipients email addresses

            @param module: module prefix for the CMS posts
            @param resource: resource name for the CMS posts

            @returns: error message (T), or None if sending was successful
        """

        T = current.T
        settings = current.deployment_settings

        if not settings.get_mail_sender() or \
           not settings.get_mail_server():
            return T("mail system not configured")

        send_email = current.msg.send_email
        error = None

        if email:
            message = cls.compose(template, data,
                                  module = module,
                                  resource = resource,
                                  )
            if message:
                if not send_email(to = email,
                                  cc = cc,
                                  subject = message[0],
                                  message = message[1],
                                  ):
                    error = T("failed to send email")

            else:
                error = T("message template not found")
        else:
            error = T("no email address specified")

        return error

    # -------------------------------------------------------------------------
    @classmethod
    def compose(cls, templates, data, module="cms", resource="post"):
        """
            Compose subject/message from templates using data

            @param templates: a tuple of string templates (subject, message),
                              or the name of the template-pair, e.g. "Volunteer"
            @param data: a dict of data to substitute placeholders in the templates
            @param module: the module prefix
            @param resource: the resource name

            @returns: tuple (subject, message), or None if disabled
        """

        # Sanitize data
        if not isinstance(data, dict):
            data = {}
        for key in data:
            if data[key] is None:
                data[key] = "-"
        if "system" not in data:
            data["system"] = current.deployment_settings.get_system_name_short()

        if isinstance(templates, str):
            templates = cls.templates(templates, module=module, resource=resource)
        if not isinstance(templates, (tuple, list)):
            return None

        subject = formatmap(templates[0], data)
        message = formatmap(templates[1], data)

        return subject, message

    # -------------------------------------------------------------------------
    @staticmethod
    def templates(name, module="cms", resource="post"):
        """
            Get message templates

            @param name: the name of the template-pair, e.g. "InviteOrg"
            @param module: the module prefix
            @param resource: the resource name

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
                         (ltable.module == module) & \
                         (ltable.resource == resource) & \
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

# END =========================================================================
