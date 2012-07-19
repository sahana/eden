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
                s3mgr.LABEL["DELETE"] = T("Remove")
            if r.component_name == "site":
                field = db.scenario_site
                field.readable = field.writable = True
        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=scenario_rheader)
    return output

# -----------------------------------------------------------------------------
def scenario_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None

    if r.representation == "html":

        if r.name == "scenario":
            # Scenario Controller
            tabs = [(T("Scenario Details"), None)]
            if deployment_settings.has_module("hrm"):
                tabs.append((T("Human Resources"), "human_resource"))
            if deployment_settings.has_module("asset"):
                tabs.append((T("Assets"), "asset"))
            tabs.append((T("Organizations"), "organisation"))
            tabs.append((T("Facilities"), "site"))
            if deployment_settings.has_module("project"):
                tabs.append((T("Tasks"), "task"))
            tabs.append((T("Map Configuration"), "config"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            if record:
                rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                       record.name),
                                    TR(TH("%s: " % T("Comments")),
                                       record.comments),
                                    ), rheader_tabs)

    return rheader

# -----------------------------------------------------------------------------
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            s3mgr.show_ids = True
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person")

# END =========================================================================
