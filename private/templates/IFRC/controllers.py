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
                         "IFRC", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        script = '''
$('.marker').mouseover(function(){
 $(this).children('.marker-window').show();
})
$('.marker').mouseout(function(){
 $(this).children('.marker-window').hide();
})'''
        response.s3.jquery_ready.append(script)

        markers = [
            Storage(name = "Afghan Red Crescent Society",
                    direction = "right",
                    top = 109,
                    left = 271),
            Storage(name = "Australian Red Cross",
                    direction = "right",
                    top = 349,
                    left = 478),
            Storage(name = "Bangladesh Red Crescent Society",
                    direction = "right",
                    top = 142,
                    left = 326),
            Storage(name = "Brunei Darussalam Red Crescent Society",
                    direction = "right",
                    top = 205,
                    left = 402),
            Storage(name = "Cambodian Red Cross Society",
                    direction = "right",
                    top = 181,
                    left = 374),
            Storage(name = "Cook Islands Red Cross",
                    direction = "right",
                    top = 291,
                    left = 652),
            Storage(name = "Fiji Red Cross Society",
                    direction = "right",
                    top = 278,
                    left = 590),
            Storage(name = "Hong Kong Red Cross Society",
                    direction = "right",
                    top = 146,
                    left = 398),
            Storage(name = "Indian Red Cross Society",
                    direction = "right",
                    top = 129,
                    left = 287),
            Storage(name = "Indonesian Red Cross Society",
                    direction = "right",
                    top = 235,
                    left = 378),
            Storage(name = "Japanese Red Cross Society",
                    direction = "right",
                    top = 94,
                    left = 463),
            Storage(name = "Kiribati Red Cross Society",
                    direction = "left",
                    top = 214,
                    left = 564),
            Storage(name = "Lao Red Cross Society",
                    direction = "right",
                    top = 159,
                    left = 366),
            Storage(name = "Malaysian Red Crescent Society",
                    direction = "right",
                    top = 207,
                    left = 367),
            Storage(name = "Maldivian Red Crescent",
                    direction = "right",
                    top = 205,
                    left = 278),
            Storage(name = "Marshall Islands Red Cross Society",
                    direction = "left",
                    top = 200,
                    left = 561),
            Storage(name = "Micronesia Red Cross Society",
                    direction = "left",
                    top = 200,
                    left = 532),
            Storage(name = "Mongolian Red Cross Society",
                    direction = "right",
                    top = 54,
                    left = 372),
            Storage(name = "Myanmar Red Cross Society",
                    direction = "right",
                    top = 165,
                    left = 349),
            Storage(name = "Nepal Red Cross Society",
                    direction = "right",
                    top = 133,
                    left = 308),
            Storage(name = "New Zealand Red Cross",
                    direction = "right",
                    top = 368,
                    left = 562),
            Storage(name = "Pakistan Red Crescent Society",
                    direction = "right",
                    top = 115,
                    left = 278),
            Storage(name = "Palau Red Cross Society",
                    direction = "right",
                    top = 197,
                    left = 463),
            Storage(name = "Papua New Guinea Red Cross Society",
                    direction = "right",
                    top = 247,
                    left = 504),
            Storage(name = "Philippine National Red Cross",
                    direction = "right",
                    top = 170,
                    left = 421),
            Storage(name = "Red Cross of Viet Nam",
                    direction = "right",
                    top = 150,
                    left = 373),
            Storage(name = "Red Cross Society of China",
                    direction = "right",
                    top = 81,
                    left = 399),
            Storage(name = "Red Cross Society of the Democratic People's Republic of Korea",
                    direction = "right",
                    top = 82,
                    left = 423),
            Storage(name = "Republic of Korea National Red Cross",
                    direction = "right",
                    top = 87,
                    left = 426),
            Storage(name = "Samoa Red Cross Society",
                    direction = "left",
                    top = 261,
                    left = 621),
            Storage(name = "Singapore Red Cross Society",
                    direction = "right",
                    top = 214,
                    left = 376),
            Storage(name = "Solomon Islands Red Cross",
                    direction = "right",
                    top = 247,
                    left = 537),
            Storage(name = "Sri Lanka Red Cross Society",
                    direction = "right",
                    top = 197,
                    left = 303),
            Storage(name = "Thai Red Cross Society",
                    direction = "right",
                    top = 172,
                    left = 360),
            Storage(name = "Timor-Leste Red Cross Society",
                    direction = "right",
                    top = 245,
                    left = 435),
            Storage(name = "Tonga Red Cross Society",
                    direction = "right",
                    top = 291,
                    left = 563),
            Storage(name = "Tuvalu Red Cross Society",
                    direction = "right",
                    top = 245,
                    left = 591),
            Storage(name = "Vanuatu Red Cross Society",
                    direction = "right",
                    top = 276,
                    left = 559),
            ]

        map = DIV(A(T("Go to Functional Map"),
                    _href=URL(c="gis", f="index"),
                    _class="map-click"),
                  _id="map-home")

        append = map.append
        for marker in markers:
            append(DIV(A("",    
                         _href=URL(c="org", f="organisation", args="read",
                                   vars={"organisation.name": marker.name})),
                       DIV(SPAN(marker.name),
                           SPAN(_class="marker-plus"),
                           _class="marker-window %s" % marker.direction),
                       _class="marker",
                       _style="top:%ipx;left:%ipx;" % (marker.top,
                                                       marker.left)))
        append(DIV(SPAN(T("Click anywhere on the map for full functionality")),
                   _class="map-tip"))

        current.menu.breadcrumbs = None
        
        return dict(map=map)

# END =========================================================================
