# -*- coding: utf-8 -*-

"""
    HTTP Error handler -- implements nicer error pages

    You need to add/replace the following to your routes.py in web2py directory
    routes_onerror = [
        ('eden/400', '!'),
        ('eden/401', '!'),
        ('eden/509', '!'),
        ("eden/*", "/eden/errors/index"),
        ("*/*", "/eden/errors/index"),
    ]

    NOTE: if Eden is installed elsewhere or exists under different name in applications folder,
          just rename it in above list. Comment the last route to disable error
          catching for other apps in the same web2py environment

"""

from gluon.http import defined_status
#s3.stylesheets.append("S3/errorpages.css")

error_messages = {
  "NA":(T("Oops! Something went wrong..."), []),

  400:(T("Sorry, I could not understand your request"),
       [T("Check for errors in the URL, maybe the address was mistyped.")]),

  403:(T("Sorry, that page is forbidden for some reason."),
       [T("Check if the URL is pointing to a directory instead of a webpage."),
        T("Check for errors in the URL, maybe the address was mistyped.")]),

  404:(T("Sorry, we couldn't find that page."),
       [T("Try checking the URL for errors, maybe it was mistyped."),
        T("Try refreshing the page or hitting the back button on your browser.")]),

  500:(T("Oops! something went wrong on our side."),
       [T("Try hitting refresh/reload button or trying the URL from the address bar again."),
        T("Please come back after sometime if that doesn\'t help.")]),

  502:(T("Sorry, something went wrong."),
       [T("The server received an incorrect response from another server that it was accessing to fill the request by the browser."),
        T("Hit the back button on your browser to try again."),
        T("Come back later.")]),

  503:(T("Sorry, that service is temporary unavailable."),
       [T("This might be due to a temporary overloading or maintenance of the server."),
        T("Hit the back button on your browser to try again."),
        T("Come back later.")]),

  504:(T("Sorry, things didn't get done on time."),
       [T("The server did not receive a timely response from another server that it was accessing to fill the request by the browser."),
        T("Hit the back button on your browser to try again."),
        T("Come back later. Everyone visiting this site is probably experiencing the same problem as you.")]),
}

def index():
    """
        Default generic error page
    """

    try:
        code = int(request.vars["code"])
        description = defined_status[code]
    except (ValueError, TypeError, KeyError):
        code = "NA"
        description = "unknown error"

    # Send a JSON message if non-interactive request
    if s3base.s3_get_extension() not in ("html", "iframe", "popup"):
        message = current.xml.json_message(False, code, description)
        headers = {"Content-Type":"application/json"}
        raise HTTP(code, body=message, **headers)

    details = " %s, %s " % (code, description)
    try:
        message, suggestions = error_messages[code]
    except KeyError:
        message, suggestions = error_messages["NA"]

    # Retain the HTTP status code on error pages
    response.status = 400 if code == "NA" else code
    return {"res": request.vars,
            "message": message,
            "details": details,
            "suggestions": suggestions,
            "app": appname,
            }
