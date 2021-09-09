# -*- coding: utf-8 -*-

"""
    Mobile Forms - Controllers
"""

# -----------------------------------------------------------------------------
def forms():
    """
        Controller to download a list of available forms
    """

    if request.env.request_method == "GET":

        if auth.permission.format == "json":

            if settings.get_mobile_masterkey_filter():
                # Filter form list by master key

                masterkey_id = 0 # filtering is mandatory

                # Expect the client to send a master key UUID in GET vars
                masterkey_uid = request.get_vars.get("mkuid")
                if masterkey_uid:
                    table = s3db.auth_masterkey
                    query = (table.uuid == masterkey_uid)
                    masterkey = db(query).select(table.id,
                                                 limitby = (0, 1),
                                                 ).first()
                    if masterkey:
                        masterkey_id = masterkey.id

                # Alternatively, allow the client to authenticate with
                # the expected master key
                elif auth.s3_logged_in() and auth.user and auth.user.masterkey_id:
                    masterkey_id = auth.user.masterkey_id

            else:
                # Do not filter the form list by master key
                masterkey_id = None

            response.headers["Content-Type"] = "application/json"
            return s3base.S3MobileFormList(masterkey_id=masterkey_id).json()

        else:
            error(415, "Invalid request format")
    else:
        error(405, "Unsupported request method")

# -----------------------------------------------------------------------------
def error(status, message):
    """
        Raise HTTP error status in non-interactive controllers

        @param status: the HTTP status code
        @param message: the error message
    """

    headers = {"Content-Type":"text/plain"}

    current.log.error(message)
    raise HTTP(status, body=message, web2py_error=message, **headers)

# END =========================================================================
