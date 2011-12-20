# -*- coding: utf-8 -*-

"""
    Flood Alerts Module - Controllers

    @author: Fran Boon
    @see: http://eden.sahanafoundation.org/wiki/Pakistan
"""

module = request.controller

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# Options Menu (available in all Functions' Views)
s3_menu(module)

def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)


def river():

    """ Rivers, RESTful controller """

    resource = request.function

    # Post-processor
    def user_postp(r, output):
        s3_action_buttons(r, deletable=False)
        return output
    response.s3.postp = user_postp

    output = s3_rest_controller(module, resource)
    return output


def freport():

    """ Flood Reports, RESTful controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    resource = request.function

    # Disable legacy fields, unless updating, so the data can be manually transferred to new fields
    #if "update" not in request.args:
    #    table.document.readable = table.document.writable = False

    # Post-processor
    def postp(r, output):
        s3_action_buttons(r, deletable=False)
        return output
    response.s3.postp = postp

    rheader = lambda r: flood_rheader(r, tabs = [(T("Basic Details"), None),
                                                     (T("Locations"), "freport_location")
                                                    ])
    output = s3_rest_controller(module, resource, rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def download():

    """ Download a file """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def flood_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        if r.name == "freport":
            report = r.record
            if report:
                rheader_tabs = s3_rheader_tabs(r, tabs)
                location = report.location_id
                if location:
                    location = gis_location_represent(location)
                rheader = DIV(TABLE(
                                TR(
                                    TH(T("Location") + ": "), location,
                                    TH(T("Date") + ": "), report.datetime
                                  ),
                                ),
                              rheader_tabs)

                return rheader

    return None

