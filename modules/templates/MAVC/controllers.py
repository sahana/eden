# -*- coding: utf-8 -*-

from gluon import *
from s3 import ICON, S3CustomController

THEME = "MAVC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T

        response = current.response
        s3 = response.s3

        # Intro
        caption = T("MapPH helps you share neighborhood concerns and connects you to information from NGOs, business and government.")

        # Get-started-button
        get_started = A(T("Get Started"), XML("&nbsp;"), ICON("fa-caret-right", _class="fa"),
                        _class="medium primary button",
                        )

        # Inject custom styles for homepage
        s3.stylesheets.append("../themes/MAVC/homepage.css")

        # Set the custom view
        self._view(THEME, "index.html")

        output = {"caption": caption,
                  "get_started": get_started,
                  }

        return output

# END =========================================================================
