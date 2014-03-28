# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3utils import S3CustomController

THEME = "OCHAROCCA"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        response = current.response
        response.s3.jquery_ready.append("""
$( ".country" ).hover(
function() { $( ".menus" ).css("background-color","#99CCFF") },
function() { $( ".menus" ).css("background-color","#66B2FF") }
);""")
        output = {}
        self._view(THEME, "index.html")
        return output
