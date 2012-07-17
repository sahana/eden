# -*- coding: utf-8 -*-

"""
    Security module
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
def zone():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def zone_type():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def staff():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def staff_type():
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def essential():
    table = s3db.hrm_human_resource
    s3.filter = (table.essential == True)
    return s3_rest_controller("hrm", "human_resource")

# END =========================================================================