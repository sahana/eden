# -*- coding: utf-8 -*-

"""
    Re-routed (custom) controllers
"""

# -----------------------------------------------------------------------------
def rest():
    """
        Vanilla RESTful CRUD controller
    """

    # Restore controller/function
    c, f = request.args[:2]
    request.controller, request.function = c, f

    # Restore arguments List
    from gluon.storage import List
    request.args = List(request.args[2:])

    # Check module is enabled
    if not settings.has_module(c):
        raise HTTP(404, body="Module disabled: %s" % c)

    # Lookup prefix/name for REST
    rest_controllers = settings.get_base_rest_controllers()
    resource = rest_controllers.get((c, f))
    if isinstance(resource, tuple) and len(resource) == 2:
        prefix, name = resource
    else:
        prefix, name = c, f

    # Run REST controller
    return s3_rest_controller(prefix, name)

# END =========================================================================
