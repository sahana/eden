# -*- coding: utf-8 -*-

"""
    Transport
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    return s3db.cms_index(module)

# -----------------------------------------------------------------------------
def airport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                # remove CRUD generated buttons in the tabs
                s3db.configure("inv_inv_item",
                               create=False,
                               listadd=False,
                               editable=False,
                               deletable=False,
                               )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=transport_rheader)

# -----------------------------------------------------------------------------
def heliport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                # remove CRUD generated buttons in the tabs
                s3db.configure("inv_inv_item",
                               create=False,
                               listadd=False,
                               editable=False,
                               deletable=False,
                               )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=transport_rheader)

# -----------------------------------------------------------------------------
def seaport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                # remove CRUD generated buttons in the tabs
                s3db.configure("inv_inv_item",
                               create=False,
                               listadd=False,
                               editable=False,
                               deletable=False,
                               )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=transport_rheader)

# -----------------------------------------------------------------------------
def transport_rheader(r, tabs=[]):

    # Need to use this format as otherwise /inv/incoming?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3base.s3_rheader_resource(r)
    r.record = record
    r.table = s3db[tablename]

    tabs = [(T("Details"), None)]
    try:
        tabs = tabs + s3db.req_tabs(r)
    except:
        pass
    try:
        tabs = tabs + s3db.inv_tabs(r)
    except:
        pass
    rheader_fields = [["name"], ["location_id"]]
    rheader = S3ResourceHeader(rheader_fields, tabs)(r)
    return rheader

# END =========================================================================
