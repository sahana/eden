#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Needs to be run in the web2py environment
# python web2py.py -S eden -M -R applications/eden/static/scripts/tools/compile.py

import os

from gluon.compileapp import compile_application, remove_compiled_application
from gluon.fileutils import up

app = request.application
join = os.path.join

# Pass View Templates to Compiler
s3.views = views = {}
theme = s3.theme
if theme != "default":
    exists = os.path.exists
    folder = request.folder
    for view in ["create.html",
                 #"delete.html",
                 "display.html",
                 "list.html",
                 "list_create.html",
                 "list_filter.html",
                 "map.html",
                 "popup.html",
                 "profile.html",
                 "report.html",
                 "report2.html",
                 #"review.html",
                 "search.html",
                 "summary.html",
                 "update.html",
                 ]:
        if exists(join(folder, "private", "templates", theme, "views", "_%s" % view)):
            views[view] = "../private/templates/%s/views/_%s" % (theme, view)

def apath(path="", r=None):
    """
    Builds a path inside an application folder

    Parameters
    ----------
    path:
        path within the application folder
    r:
        the global request object

    """

    opath = up(r.folder)
    while path[:3] == "../":
        (opath, path) = (up(opath), path[3:])
    return join(opath, path).replace("\\", "/")

folder = apath(app, request)
compile_application(folder)

