#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Needs to be run in the web2py environment
# python web2py.py -S eden -M -R applications/eden/static/scripts/tools/compile.py

import os

from gluon.compileapp import compile_application, remove_compiled_application
from gluon.fileutils import up

app = request.application

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
    return os.path.join(opath, path).replace("\\", "/")

folder = apath(app, request)
compile_application(folder)

