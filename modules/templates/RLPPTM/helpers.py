# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLPPTM template

    @license: MIT
"""

from gluon import current, CRYPT, Field, INPUT, IS_EMAIL, SQLFORM, URL

from s3 import S3Method, s3_mark_required

# =============================================================================
class rlpptm_InviteUserOrg(S3Method):
    """ Custom Method Handler to invite User Organisations """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}

        if r.http in ("GET", "POST"):
            if not r.record:
                r.error(400, current.ERROR.BAD_REQUEST)
            if r.interactive:
                output = self.invite(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def invite(self, r, **attr):
        """
            Prepare and process invitation form

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T

        db = current.db
        s3db = current.s3db

        response = current.response
        request = current.request
        session = current.session

        settings = current.deployment_settings
        auth_settings = current.auth.settings

        output = {"title": T("Invite Organisation"),
                  }

        # Look up existing invite-account
        email = None
        pe_id = r.record.pe_id

        ltable = s3db.pr_person_user
        utable = auth_settings.table_user
        join = utable.on(utable.id == ltable.user_id)
        query = (ltable.pe_id == pe_id) & \
                (ltable.deleted == False)
        account = db(query).select(utable.id,
                                   utable.email,
                                   join = join,
                                   limitby = (0, 1),
                                   ).first()
        if account:
            email = account.email
        else:
            ctable = s3db.pr_contact
            query = (ctable.pe_id == pe_id) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.deleted == False)
            contact = db(query).select(ctable.value,
                                       orderby = ctable.priority,
                                       limitby = (0, 1),
                                       ).first()
            if contact:
                email = contact.value

        # Form Fields
        formfields = [Field("email",
                            default = email,
                            requires = IS_EMAIL(),
                            ),
                      ]

        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields,
                                                )
        response.s3.has_required = has_required

        # Form buttons
        SEND_INVITATION = T("Send New Invitation") if account else T("Send Invitation")
        buttons = [INPUT(_type = "submit",
                         _value = SEND_INVITATION,
                         ),
                   # TODO cancel-button?
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "invite",
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = SEND_INVITATION,
                               #delete_label = auth_messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS & JS Validation
        form.add_class("send_invitation")

        if form.accepts(request.vars,
                        session,
                        formname = "invite",
                        #onvalidation = auth_settings.register_onvalidation,
                        ):

            error = self.invite_account(r.record, form.vars.email, account=account)
            if error:
                response.error = T("Could not send invitation (%(reason)s)") % {"reason": error}
            else:
                response.confirmation = T("Invitation sent")
        else:
            if account:
                response.warning = T("This organisation has been invited before!")

        output["form"] = form

        response.view = self._view(r, "update.html")

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def invite_account(cls, organisation, email, account=None):

        request = current.request

        data = {"first_name": organisation.name,
                "email": email,
                # TODO language => use default language
                "link_user_to": ["staff"],
                "organisation_id": organisation.id,
                }

        # Generate registration key and activation code
        from uuid import uuid4
        key = str(uuid4())
        code = uuid4().hex[-6:].upper()

        # Add hash to data
        data["registration_key"] = cls.keyhash(key, code)

        if account:
            success = account.update_record(**data)
            if not success:
                return "could not update preliminary account"
        else:
            utable = current.auth.settings.table_user
            user_id = utable.insert(**data)
            if user_id:
                ltable = current.s3db.pr_person_user
                ltable.insert(pe_id = organisation.pe_id,
                              user_id = user_id,
                              )
            else:
                return "could not create preliminary account"

        # Compose and send invitation email
        registration_url = URL(c = "default",
                               f = "index",
                               args = ["register_invited", key],
                               scheme = "https" if request.is_https else "http",
                               )

        data = {"url": registration_url,
                "code": code,
                }

        from .notifications import CMSNotifications
        return CMSNotifications.send(email, "InviteOrg", data,
                                     module = "auth",
                                     resource = "user",
                                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def keyhash(key, code):
        """
            Generate a hash of the activation code using
            the registration key

            @param key: the registration key
            @param code: the activation code

            @returns: the hash as string
        """

        crypt = CRYPT(key=key, digest_alg="sha512", salt=None)
        return str(crypt(code.upper())[0])

# END =========================================================================
