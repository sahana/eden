# -*- coding: utf-8 -*-

from os import path

from gluon import current
from gluon.html import *
#from gluon.storage import Storage

from s3 import S3CustomController

THEME = "IFRC"

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        response = current.response

        response.title = current.deployment_settings.get_system_name()
        view = path.join(current.request.folder, "modules", "templates",
                         "IFRC", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP(404, "Unable to open Custom View: %s" % view)

        script = '''
$('.marker').mouseover(function(){$(this).children('.marker-window').show()})
$('.marker').mouseout(function(){$(this).children('.marker-window').hide()})
$('#single-col').css('padding', 0)'''
        response.s3.jquery_ready.append(script)

        markers = [
            {"name": "Afghan Red Crescent Society",
             "direction": "right",
             "top": 109,
             "left": 271,
             },
            {"name": "Australian Red Cross",
             "direction": "right",
             "top": 349,
             "left": 478,
             },
            {"name": "Bangladesh Red Crescent Society",
             "direction": "right",
             "top": 142,
             "left": 326,
             },
            {"name": "Bhutan Red Cross Society",
             "direction": "right",
             "top": 136,
             "left": 321,
             },
            {"name": "Brunei Darussalam Red Crescent Society",
             "direction": "right",
             "top": 205,
             "left": 402,
             },
            {"name": "Cambodian Red Cross Society",
             "direction": "right",
             "top": 181,
             "left": 374,
             },
            {"name": "Cook Islands Red Cross",
             "direction": "right",
             "top": 291,
             "left": 652,
             },
            {"name": "Fiji Red Cross Society",
             "direction": "right",
             "top": 278,
             "left": 590,
             },
            {"name": "Hong Kong Red Cross Society",
             "direction": "right",
             "top": 146,
             "left": 398,
             },
            {"name": "Indian Red Cross Society",
             "direction": "right",
             "top": 129,
             "left": 287,
             },
            {"name": "Indonesian Red Cross Society",
             "direction": "right",
             "top": 235,
             "left": 378,
             },
            {"name": "Iraqi Red Crescent Society",
             "direction": "right",
             "top": 110,
             "left": 195,
             },
            {"name": "Japanese Red Cross Society",
             "direction": "right",
             "top": 94,
             "left": 463,
             },
            {"name": "Kiribati Red Cross Society",
             "direction": "left",
             "top": 214,
             "left": 564,
             },
            {"name": "Lao Red Cross Society",
             "direction": "right",
             "top": 159,
             "left": 366,
             },
            {"name": "Malaysian Red Crescent Society",
             "direction": "right",
             "top": 207,
             "left": 367,
             },
            {"name": "Maldivian Red Crescent",
             "direction": "right",
             "top": 205,
             "left": 278,
             },
            {"name": "Marshall Islands Red Cross Society",
             "direction": "left",
             "top": 200,
             "left": 561,
             },
            {"name": "Micronesia Red Cross Society",
             "direction": "left",
             "top": 200,
             "left": 532,
             },
            {"name": "Mongolian Red Cross Society",
             "direction": "right",
             "top": 54,
             "left": 372,
             },
            {"name": "Myanmar Red Cross Society",
             "direction": "right",
             "top": 165,
             "left": 349,
             },
            {"name": "Nepal Red Cross Society",
             "direction": "right",
             "top": 133,
             "left": 308,
             },
            {"name": "New Zealand Red Cross",
             "direction": "right",
             "top": 368,
             "left": 562,
             },
            {"name": "Pakistan Red Crescent Society",
             "direction": "right",
             "top": 115,
             "left": 278,
             },
            {"name": "Palau Red Cross Society",
             "direction": "right",
             "top": 197,
             "left": 463,
             },
            {"name": "Papua New Guinea Red Cross Society",
             "direction": "right",
             "top": 247,
             "left": 504,
             },
            {"name": "Philippine National Red Cross",
             "direction": "right",
             "top": 170,
             "left": 421,
             },
            {"name": "Red Cross of Viet Nam",
             "direction": "right",
             "top": 150,
             "left": 373,
             },
            {"name": "Red Cross Society of China",
             "direction": "right",
             "top": 81,
             "left": 399,
             },
            {"name": "Red Cross Society of the Democratic People's Republic of Korea",
             "direction": "right",
             "top": 82,
             "left": 423,
             },
            {"name": "Republic of Korea National Red Cross",
             "direction": "right",
             "top": 87,
             "left": 426,
             },
            {"name": "Samoa Red Cross Society",
             "direction": "left",
             "top": 261,
             "left": 621,
             },
            {"name": "Singapore Red Cross Society",
             "direction": "right",
             "top": 214,
             "left": 376,
             },
            {"name": "Solomon Islands Red Cross",
             "direction": "right",
             "top": 247,
             "left": 537,
             },
            {"name": "Sri Lanka Red Cross Society",
             "direction": "right",
             "top": 197,
             "left": 303,
             },
            {"name": "Thai Red Cross Society",
             "direction": "right",
             "top": 172,
             "left": 360,
             },
            {"name": "Timor-Leste Red Cross Society",
             "direction": "right",
             "top": 245,
             "left": 435,
             },
            {"name": "Tonga Red Cross Society",
             "direction": "right",
             "top": 291,
             "left": 563,
             },
            {"name": "Tuvalu Red Cross Society",
             "direction": "right",
             "top": 245,
             "left": 591,
             },
            {"name": "Vanuatu Red Cross Society",
             "direction": "right",
             "top": 276,
             "left": 559,
             },
            ]

        map = DIV(A(T("Go to Functional Map"),
                    _href = URL(c="gis", f="index"),
                    _class = "map-click"),
                  _id = "map-home")

        append = map.append
        for marker in markers:
            name = marker["name"]
            append(DIV(A("",
                         _href=URL(c="org", f="organisation",
                                   args = "read",
                                   vars = {"organisation.name": name},
                                   )
                         ),
                       DIV(SPAN(name),
                           SPAN(_class = "marker-plus"),
                           _class = "marker-window %s" % marker["direction"]),
                       _class = "marker",
                       _style = "top:%ipx;left:%ipx;" % (marker["top"],
                                                         marker["left"])))
        append(DIV(SPAN(T("Click anywhere on the map for full functionality")),
                   _class = "map-tip"))

        current.menu.breadcrumbs = None

        return dict(map=map)

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
def deploy_index():
    """
        Custom module homepage for deploy (=RDRT) to display online
        documentation for the module
    """

    response = current.response

    def prep(r):
        default_url = URL(f="mission", args="summary", vars={})
        return current.s3db.cms_documentation(r, "RDRT", default_url)
    response.s3.prep = prep
    output = current.rest_controller("cms", "post")

    # Custom view
    view = path.join(current.request.folder,
                     "modules",
                     "templates",
                     THEME,
                     "views",
                     "deploy",
                     "index.html",
                     )
    try:
        # Pass view as file not str to work in compiled mode
        response.view = open(view, "rb")
    except IOError:
        from gluon.http import HTTP
        raise HTTP(404, "Unable to open Custom View: %s" % view)

    return output

# END =========================================================================
