# -*- coding: utf-8 -*-

"""
    Transport
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    return s3db.cms_index(c)

# -----------------------------------------------------------------------------
def airport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.transport_rheader)

# -----------------------------------------------------------------------------
def border_crossing():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.transport_rheader)

# -----------------------------------------------------------------------------
def border_control_point():
    """ Border Control Points - RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            #elif r.method == "update":
            #    field = r.table.obsolete
            #    field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.transport_rheader)

# -----------------------------------------------------------------------------
def bridge():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.transport_rheader)

# -----------------------------------------------------------------------------
def heliport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.transport_rheader)

# -----------------------------------------------------------------------------
def seaport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)
                elif r.component.name == "inv_item":
                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.transport_rheader)

# -----------------------------------------------------------------------------
def incoming():
    """
        Incoming Shipments for Sites

        Used from Requests rheader when looking at Transport Status
    """

    # @ToDo: Create this function!
    return s3db.inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    from s3db.req import req_match
    return req_match(rheader = s3db.transport_rheader)

# END =========================================================================
