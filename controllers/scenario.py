# -*- coding: utf-8 -*-

"""
    Scenario Module - Controllers

    http://eden.sahanafoundation.org/wiki/BluePrintScenario
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
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to scenario/create """
    redirect(URL(f="scenario", args="create"))

# -----------------------------------------------------------------------------
def scenario():
    """ RESTful CRUD controller """

    s3db.configure("scenario_config",
                   deletable=False)

    # Pre-process
    def prep(r):
        if r.interactive and r.component:
            if r.component.name != "config":
                s3.crud.submit_button = T("Assign")
                s3.crud_labels["DELETE"] = T("Remove")
        if r.component_name == "site":
            field = db.scenario_site.site_id
            field.readable = field.writable = True
        return True
    s3.prep = prep

    output = s3_rest_controller(rheader = s3db.scenario_rheader)
    return output

# -----------------------------------------------------------------------------
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            current.xml.show_ids = True
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person")

# END =========================================================================
