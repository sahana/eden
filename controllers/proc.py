# -*- coding: utf-8 -*-

"""
    Procurement

    A module to handle Procurement

    Currently handles
        Suppliers
        Planned Procurements
        Purchase Orders (POs)

    @ToDo: Extend to
        Purchase Requests (PRs)
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(c)

# -----------------------------------------------------------------------------
def order():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.proc_rheader,
                              hide_filter = True,
                              )

# -----------------------------------------------------------------------------
#def order_item():
#    """ RESTful CRUD controller """

#    return s3_rest_controller()

# -----------------------------------------------------------------------------
def plan():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.proc_rheader,
                              hide_filter = True,
                              )

# -----------------------------------------------------------------------------
def supplier():
    """ RESTful CRUD controller """

    return s3_rest_controller("org", "organisation")

# END =========================================================================
