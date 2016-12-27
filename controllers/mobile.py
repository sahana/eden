# -*- coding: utf-8 -*-

"""
    Mobile Forms - Controllers
"""

module = request.controller

# -----------------------------------------------------------------------------
def forms():
    """
        Controller to download a list of available forms
    """

    if request.env.request_method == "GET":

        if auth.permission.format == "json":

            response.headers["Content-Type"] = "application/json"
            return s3base.S3MobileFormList().json()

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
