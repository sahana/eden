#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Use this script to update the language files
# e.g. tie into a Bzr pre-commit hook
# python web2py.py -S eden -R applications/eden/static/scripts/tools/languages.py

# Based on web2py/scripts/sync_languages.py

import os

from gluon.languages import update_all_languages
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

    
path = apath(app, request)
update_all_languages(path)
