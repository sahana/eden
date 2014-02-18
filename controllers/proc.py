# -*- coding: utf-8 -*-

"""
    Procurement

    A module to handle Procurement

    Currently handles
        Suppliers
        Planned Procurements

    @ToDo: Extend to
        Purchase Requests (PRs)
        Purchase Orders (POs)
"""

module = request.controller
resourcename = request.function

if not settings.has_module("proc"):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module)

# -----------------------------------------------------------------------------
def supplier():
    """ RESTful CRUD controller """

    return s3_rest_controller("org", "organisation")

# -----------------------------------------------------------------------------
def plan():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.proc_rheader,
                              hide_filter = True,
                             )

# END =========================================================================
