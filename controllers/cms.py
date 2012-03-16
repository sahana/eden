# -*- coding: utf-8 -*-

"""
    CMS

    Simple Content Management System
"""

module = request.controller
resourcename = request.function

if not (deployment_settings.has_module("inv") or deployment_settings.has_module("asset")):
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def index():
    """
        Application Home page
    """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name

    table = s3db.cms_post
    item = db(table.module == module).select(table.body,
                                             limitby=(0, 1)).first()
    if item:
        item = item.body
    else:
        item = H2(module_name)

    # tbc
    report = ""

    return dict(item=item, report=report)

# -----------------------------------------------------------------------------
def series():
    """ RESTful CRUD controller """

    return s3_rest_controller(rheader=s3db.cms_rheader)

# -----------------------------------------------------------------------------
def post():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if not r.component:
            # Add CKEditor to the Body input
            ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
            response.s3.scripts.append(ckeditor)
            adapter = URL(c="static", f="ckeditor", args=["adapters",
                                                          "jquery.js"])
            response.s3.scripts.append(adapter)

            # Toolbar options: http://docs.cksource.com/CKEditor_3.x/Developers_Guide/Toolbar
            js = "var ck_config = {toolbar:[['Format','Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Image','Table','-','PasteFromWord','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'};"
            response.s3.js_global.append(js)
            js = "$('#cms_text_body').ckeditor(ck_config);"
            response.s3.jquery_ready.append(js)
        return True
    response.s3.prep = prep

    return s3_rest_controller(rheader=s3db.cms_rheader)

# -----------------------------------------------------------------------------
def page():
    """
        RESTful CRUD controller for display of a post as a full-page read-only
    """

    # Pre-process
    def prep(r):
        s3mgr.configure(r.tablename, listadd=False)
        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.record:
            output = {"item": r.record.body}
            response.view = "cms/page.html"
        return output
    response.s3.postp = postp

    output = s3_rest_controller("cms", "post")
    return output

# END =========================================================================
