module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

def index():
    """ Module Home Page """
    module_name = settings.modules[module].name_nice
    response.title = module_name

    return dict(module_name=module_name)
def report():
    """ RESTful CRUD controller """

    return s3_rest_controller()
