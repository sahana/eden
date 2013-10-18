# -*- coding: utf-8 -*-

"""
    Deployments
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

s3db.hrm_vars()

# =============================================================================
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)
    
# =============================================================================
def deployment():

    def prep(r):
        s3.cancel = r.url(method="summary", id=0)
        created_on = r.table.created_on
        created_on.readable = True
        created_on.label = T("Date Created")
        created_on.represent = lambda d: \
                               s3base.S3DateTime.date_represent(d, utc=True)
        return True
    s3.prep = prep

    # Override standard "List" button
    def postp(r, output):
        s3_action_buttons(r,
                          editable=True,
                          deletable=True,
                          read_url=r.url(method="profile", id="[id]"),
                          update_url=r.url(method="profile", id="[id]"),
                          delete_url=r.url(method="delete", id="[id]"),
                         )
        if isinstance(output, dict) and "buttons" in output:
            buttons = output["buttons"]
            if "list_btn" in buttons and "summary_btn" in buttons:
                buttons["list_btn"] = buttons["summary_btn"]
        return output
    s3.postp = postp

    # @todo: follow global settings:
    settings.ui.filter_auto_submit = 750
    settings.ui.report_auto_submit = 750
    
    return s3_rest_controller(hide_filter=False)
            
# =============================================================================
def human_resource_assignment():

    def prep(r):
        if r.representation == "popup":
            r.resource.configure(insertable=False)
        return True
    s3.prep = prep

    return s3_rest_controller()
    
# =============================================================================
def alert():

    return s3_rest_controller()

# =============================================================================
def human_resource():
    """
        'Members' RESTful CRUD Controller
    """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = True
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    return s3db.hrm_human_resource_controller()
    
# =============================================================================
def person():
    """
        'Members' RESTful CRUD Controller
    """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = "experience"
    settings.hrm.vol_experience = "experience"
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    return s3db.hrm_person_controller()
    
# END =========================================================================
