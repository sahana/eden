# -*- coding: utf-8 -*-

"""
    Guided Tour, Controllers
"""
module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """
        Application Home page
    """

    module_name = settings.modules[module].get("name_nice")
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def config():
    """ REST Controller """
    tablename = "tour_config"
    s3db.table(tablename)
    table = s3db.tour_config
    return s3_rest_controller("tour", "config",
                              rheader = s3db.tour_rheader)

def details():
    """ REST Controller """
    tablename = "tour_details"
    s3db.table(tablename)
    table = s3db.tour_details
    return s3_rest_controller("tour", "details")

def user():
    """ REST Controller """
    tablename = "tour_user"
    s3db.table(tablename)
    table = s3db.tour_user
    return s3_rest_controller("tour", "user")

# -----------------------------------------------------------------------------
def guided_tour_finished():
    """ Update database when tour completed otherwise redirect to tour/config """
    if request.ajax == True:
        utable = s3db.tour_user
        person_id = auth.s3_logged_in_person()
        query = (utable.person_id == person_id) & \
                (utable.tour_config_id == request.post_vars.tour_id)
        db(query).update(resume = "",
                         completed = True,
                         trip_counter = utable.trip_counter+1)
        return json.dumps({})
    else:
        redirect(URL(f="config"))
