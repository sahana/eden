# -*- coding: utf-8 -*-

from os import path

from gluon import current
from gluon.html import *
from gluon.storage import Storage

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        response = current.response

        response.title = current.deployment_settings.get_system_name()
        view = path.join(current.request.folder, "private", "templates",
                         "ARC", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        #script = '''
#$('.marker').mouseover(function(){
# $(this).children('.marker-window').show();
#})
#$('.marker').mouseout(function(){
# $(this).children('.marker-window').hide();
#})'''
        #response.s3.jquery_ready.append(script)

        map = DIV(A(T("Go to Functional Map"),
                    _href=URL(c="gis", f="index"),
                    _class="map-click"),
                  _id="map-home")

        append = map.append
        append(DIV(SPAN(T("Click anywhere on the map for full functionality")),
                   _class="map-tip"))

        current.menu.breadcrumbs = None
        
        return dict(map=map)

# END =========================================================================
