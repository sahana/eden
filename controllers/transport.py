# -*- coding: utf-8 -*-

"""
    Transport
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    from s3db.cms import cms_index
    return s3db.cms_index(c)

# -----------------------------------------------------------------------------
def airport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        if r.interactive:
            if r.component:
                component_name = r.component_name
                if component_name == "human_resource":
                    from s3db.org import org_site_staff_config
                    org_site_staff_config(r)
                elif component_name == "inv_item":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)
                elif component_name == "layout" and \
                     r.method != "hierarchy":
                    from s3db.org import org_site_layout_config
                    org_site_layout_config(r.record.site_id)
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    from s3db.transport import transport_rheader
    return s3_rest_controller(rheader = transport_rheader)

# -----------------------------------------------------------------------------
def border_crossing():
    """ RESTful CRUD controller """

    from s3db.transport import transport_rheader
    return s3_rest_controller(rheader = transport_rheader)

# -----------------------------------------------------------------------------
def border_control_point():
    """ Border Control Points - RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component_name == "human_resource":
                    from s3db.org import org_site_staff_config
                    org_site_staff_config(r)
                elif r.component_name == "inv_item":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)
                elif component_name == "layout" and \
                     r.method != "hierarchy":
                    from s3db.org import org_site_layout_config
                    org_site_layout_config(r.record.site_id)
            #elif r.method == "update":
            #    field = r.table.obsolete
            #    field.readable = field.writable = True
        return True
    s3.prep = prep

    from s3db.transport import transport_rheader
    return s3_rest_controller(rheader = transport_rheader)

# -----------------------------------------------------------------------------
def bridge():
    """ RESTful CRUD controller """

    from s3db.transport import transport_rheader
    return s3_rest_controller(rheader = transport_rheader)

# -----------------------------------------------------------------------------
def heliport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component_name == "human_resource":
                    from s3db.org import org_site_staff_config
                    org_site_staff_config(r)
                elif r.component_name == "inv_item":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)
                elif component_name == "layout" and \
                     r.method != "hierarchy":
                    from s3db.org import org_site_layout_config
                    org_site_layout_config(r.record.site_id)
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    from s3db.transport import transport_rheader
    return s3_rest_controller(rheader = transport_rheader)

# -----------------------------------------------------------------------------
def seaport():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component_name == "human_resource":
                    from s3db.org import org_site_staff_config
                    org_site_staff_config(r)
                elif r.component_name == "inv_item":
                    # Filter out items which are already in this inventory
                    from s3db.inv import inv_prep
                    inv_prep(r)
                elif component_name == "layout" and \
                     r.method != "hierarchy":
                    from s3db.org import org_site_layout_config
                    org_site_layout_config(r.record.site_id)
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
        return True
    s3.prep = prep

    from s3db.transport import transport_rheader
    return s3_rest_controller(rheader = transport_rheader)

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

    from s3db.inv import inv_req_match
    from s3db.transport import transport_rheader
    return inv_req_match(rheader = transport_rheader)

# END =========================================================================
