# -*- coding: utf-8 -*-

"""
    Flood Alerts module
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name

    item = None
    if settings.has_module("cms"):
        table = s3db.cms_post
        _item = db(table.module == module).select(table.id,
                                                  table.body,
                                                  limitby=(0, 1)).first()
        if _item:
            if s3_has_role(ADMIN):
                item = DIV(XML(_item.body),
                           BR(),
                           A(T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[_item.id, "update"],
                                       vars={"module":module}),
                             _class="action-btn"))
            else:
                item = XML(_item.body)
        elif s3_has_role(ADMIN):
            item = DIV(H2(module_name),
                       A(T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module":module}),
                         _class="action-btn"))

    if not item:
        item = H2(module_name)

    # tbc
    report = ""

    response.view = "index.html"
    return dict(item=item, report=report)

# -----------------------------------------------------------------------------
def gauge():
    """ Gauges, RESTful controller """

    # Pre-processor
    def prep(r):
        if r.interactive:
            pass
        elif r.representation == "plain" and \
             r.method !="search":
            # Map Popups
            r.table.image_url.readable = False
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive:
            pass
        elif r.representation == "plain" and \
             r.method !="search":
            # Map Popups
            # use the Image URL
            # @ToDo: The default photo not the 1st
            image_url = r.record.image_url
            if image_url:
                output["item"].append(IMG(_src=image_url,
                                          # @ToDo: capture the size on upload & have controller resize where-required on-download
                                          _width=400,
                                          _height=310))
        return output
    s3.postp = postp

    output = s3_rest_controller()

    return output

# -----------------------------------------------------------------------------
def river():
    """ Rivers, RESTful controller """

    return s3_rest_controller()

# END =========================================================================
