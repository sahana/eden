# -*- coding: utf-8 -*-

""" Authentication, Authorization, Accounting

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2021 Sahana Software Foundation
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

__all__ = ("S3MasterKey",
           )

import base64
import datetime
import json
from uuid import uuid4

from gluon import CRYPT, current

from .s3utils import s3_str

DIGEST_ALG = "pbkdf2(1000,64,sha512)"

# =============================================================================
class S3MasterKey:
    """ Master Key Verification and Authentication """

    # -------------------------------------------------------------------------
    @staticmethod
    def __purge():
        """
            Delete all master key auth tokens that have expired
        """

        db = current.db

        table = current.s3db.auth_masterkey_token
        db(table.expires_on <= datetime.datetime.utcnow()).delete()

        # Commit here so subsequent rollback cannot reinstate tokens
        db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def __check(cls, token_id):
        """
            Check a token ID; deletes the token if found

            Args:
                token_id: the token ID

            Returns:
                The token string if found, otherwise None
        """

        # Drop all expired tokens
        cls.__purge()

        table = current.s3db.auth_masterkey_token
        query = (table.id == token_id)

        db = current.db
        row = db(query).select(table.id, table.token, limitby = (0, 1)).first()
        if not row:
            # Invalid token ID or token expired
            return None

        # Found => delete token
        db(query).delete()

        # Commit here so subsequent rollback cannot reinstate the token
        db.commit()

        return row.token

    # -------------------------------------------------------------------------
    @classmethod
    def __token(cls):
        """
            Generate a new token for master key authentication

            Returns:
                tuple (token_id, token)
        """

        # Drop all expired tokens
        cls.__purge()

        # Generate new token
        token = uuid4().hex
        token_ttl = current.deployment_settings.get_auth_masterkey_token_ttl()
        expires_on = datetime.datetime.utcnow() + datetime.timedelta(seconds=token_ttl)

        # Store in token table
        table = current.s3db.auth_masterkey_token
        token_id = table.insert(token=token, expires_on=expires_on)

        # Commit here so subsequent rollback will not drop the token
        current.db.commit()

        return token_id, token

    # -------------------------------------------------------------------------
    @classmethod
    def challenge(cls, headers=None):
        """
            Add a response header to a HTTP-401 challenge containing
            a master key auth token; this token can be used by the
            client to generate an access key

            The client must indicate its MasterKeyAuth capability by
            adding a HTTP header to the original request:

                - RequestMasterKeyAuth: true

            In case of a 401-response, the server will send a corresponding
            header:

                - MasterKeyAuthToken: <token>

            The value of this header is a base64-encoded combination of
            token ID and token string: "ID:TOKEN".
        """

        if not current.response.s3.masterkey_auth_failed and \
           current.request.env.http_requestmasterkeyauth == "true":

            header = ("%s:%s" % cls.__token()).encode("utf-8")

            if headers is None:
                headers = current.response.headers

            headers["MasterKeyAuthToken"] = s3_str(base64.b64encode(header))

    # -------------------------------------------------------------------------
    @staticmethod
    def get_access_key():
        """
            Extract the access key for master key auth from the Authorization
            header in the current request

            Returns:
                The access key as str, or None if no master key
                authorization header was found
        """

        header = current.request.env.http_authorization

        if not header or header[:10].lower() != "masterkey ":
            return None

        return s3_str(base64.b64decode(header[10:]))

    # -------------------------------------------------------------------------
    @classmethod
    def get_masterkey(cls, keyhash, token):
        """
            Get the master key matching a keyhash

            Args:
                keyhash: the key hash from the Authorization header
                token: the master key auth token

            Returns:
                The master key Row
        """

        # Get all valid master keys
        table = current.s3db.auth_masterkey
        query = (table.deleted == False) & \
                (table.name != None) & \
                (table.name != "") & \
                (table.user_id != None)
        rows = current.db(query).select(table.id,
                                        table.uuid,
                                        table.name,
                                        table.user_id,
                                        )

        # Get the app key
        app_key = current.deployment_settings.get_auth_masterkey_app_key()

        # Format keyhash
        formatted = "%s$%s$%s" % (DIGEST_ALG, token, keyhash)

        # Find match
        masterkey = None
        encrypt = CRYPT(digest_alg=DIGEST_ALG, salt=token)
        for row in rows:
            key = row.name
            if app_key:
                key = "%s:%s" % (key, app_key)
            if encrypt(key)[0] == formatted:
                masterkey = row
                break

        return masterkey

    # -------------------------------------------------------------------------
    @classmethod
    def authenticate(cls, access_key):
        """
            Attempt to authenticate with an access key; logs in the user
            associated with the master key represented by the access key

            Args:
                access_key: the access key, format: "TokenID:KeyHash"

            Returns:
                True|False whether the login was successful
        """

        if not access_key or ":" not in access_key:
            current.log.error("Master key auth: failed [access key syntax error]")
            return False

        token_id, keyhash = access_key.split(":", 1)
        token = cls.__check(token_id)
        if not token:
            current.log.error("Master key auth: failed [invalid token]")
            return False

        masterkey = cls.get_masterkey(keyhash, token)
        if not masterkey:
            current.log.error("Master key auth: failed [invalid access key]")
            return False

        auth = current.auth
        auth.s3_impersonate(masterkey.user_id)
        if auth.user:
            current.log.info("Master key auth: success [%s]" % auth.user.email)

            # Remember the ID of the master key used for login
            auth.user.masterkey_id = masterkey.id

            # Add new token to response if requested by client
            cls.challenge()

        return auth.user is not None

    # -------------------------------------------------------------------------
    @classmethod
    def context(cls):
        """
            Get context for the master key the current user is logged-in
            with (auth.user.masterkey_id)

            Returns:
                JSON (as string); for verification: if the user is
                logged-in with a valid master key, the JSON object
                will always contain a non-null masterkey_uuid attribute
        """

        auth = current.auth
        if auth.user:
            masterkey_id = auth.user.get("masterkey_id")
        else:
            masterkey_id = None

        if not masterkey_id:
            return {}

        # Get the master key UUID
        table = current.s3db.auth_masterkey
        row = current.db(table.id == masterkey_id).select(table.id,
                                                          table.uuid,
                                                          table.name,
                                                          limitby = (0, 1),
                                                          ).first()
        if row:
            context = current.deployment_settings.get_auth_masterkey_context()
            if callable(context):
                try:
                    context = context(row)
                except Exception as e:
                    current.log.error("Master Key Context Getter failed: %s" % e)
                    context = None
            if isinstance(context, dict):
                context["masterkey_uuid"] = row.uuid
            else:
                context = {"masterkey_uuid": row.uuid}
        else:
            context = {}

        response = current.response
        if response:
            response.headers["Content-Type"] = "application/json"

        return json.dumps(context)

# END =========================================================================
