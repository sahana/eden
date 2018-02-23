# -*- coding: utf-8 -*-

from gluon import *
from s3 import ICON, S3CustomController

THEME = "historic.MAVC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T

        response = current.response
        s3 = response.s3

        # Intro
        caption = T("MapPH helps you share neighborhood needs and connects you to information from NGOs, business and government.")

        # Get-started-button
        get_started = A(T("Get Started"), XML("&nbsp;"), ICON("fa-caret-right", _class="fa"),
                        _class="medium primary button",
                        _href=URL(c="default",
                                  f="index",
                                  args=["docs"],
                                  vars={"name": "GetStarted"},
                                  )
                        )

        # Inject custom styles for homepage
        s3.stylesheets.append("../themes/MAVC/homepage.css")

        # Set the custom view
        self._view(THEME, "index.html")

        output = {"caption": caption,
                  "get_started": get_started,
                  }

        return output

# =============================================================================
class docs(S3CustomController):
    """
        Custom controller to display online documentation, accessible
        for anonymous users (e.g. information how to register/login)
    """

    def __call__(self):

        response = current.response

        def prep(r):
            default_url = URL(f="index", args=[], vars={})
            return current.s3db.cms_documentation(r, "HELP", default_url)
        response.s3.prep = prep
        output = current.rest_controller("cms", "post")

        # Custom view
        self._view(THEME, "docs.html")

        current.menu.dashboard = None

        return output

# =============================================================================
class profile(S3CustomController):
    """
        Custom controller to fill out Organisation Profile
    """

    def __call__(self):

        auth = current.auth
        if not current.auth.is_logged_in():
            current.session.information = current.T("You need to Login to create an Organization Profile")
            redirect(URL(c="default", f="user", args="login", vars={"_next": URL(c="default", f="index", args="profile")}))

        organisation_id = auth.user.organisation_id
        if not organisation_id:
            redirect(URL(c="org", f="organisation", args="create"))

        if auth.s3_has_role("ORG_ADMIN"):
            redirect(URL(c="org", f="organisation", args=[organisation_id, "update"]))

        current.session.warning = current.T("Your Organization Profile is here, changes can only be made by your Organization Administrator")
        redirect(URL(c="org", f="organisation", args=organisation_id))

# END =========================================================================
