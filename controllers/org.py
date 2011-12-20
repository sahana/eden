# -*- coding: utf-8 -*-

"""
    Organization Registry - Controllers

    @author: Fran Boon
    @author: Michael Howden
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Options Menu (available in all Functions" Views)
s3_menu(module)

# =============================================================================
def index():
    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# =============================================================================
def sector():
    """ RESTful CRUD controller """

    #tablename = "%s_%s" % (module, resourcename)
    #table = db[tablename]

    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def subsector():
    """ RESTful CRUD controller """

    #tablename = "%s_%s" % (module, resourcename)
    #table = db[tablename]

    return s3_rest_controller(module, resourcename)

# =============================================================================
def site():
    """ RESTful CRUD controller """
    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def site_org_json():

    table = db.org_site
    otable = db.org_organisation
    response.headers["Content-Type"] = "application/json"
    #db.req_commit.date.represent = lambda dt: dt[:10]
    query = (table.site_id == request.args[0]) & \
            (table.organisation_id == otable.id)
    records = db(query).select(otable.id,
                               otable.name)
    return records.json()

# =============================================================================
def organisation():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    #return response.s3.organisation_controller()
    return organisation_controller()

# -----------------------------------------------------------------------------
def organisation_list_represent(l):
    if l:
        max = 4
        if len(l) > max:
            count = 1
            for x in l:
                if count == 1:
                    output = organisation_represent(x)
                elif count > max:
                    return "%s, etc" % output
                else:
                    output = "%s, %s" % (output, organisation_represent(x))
                count += 1
        else:
            return ", ".join([organisation_represent(x) for x in l])
    else:
        return NONE

# =============================================================================
def office():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    #return response.s3.office_controller()
    return office_controller()

# =============================================================================
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            s3mgr.show_ids = True
        return True
    response.s3.prep = prep

    return s3_rest_controller("pr", "person")

# =============================================================================
def room():
    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

# =============================================================================
def incoming():
    """ Incoming Shipments """

    s3mgr.load("inv_inv_item")
    return response.s3.inv_incoming()

# =============================================================================
def req_match():
    """ Match Requests """

    s3mgr.load("req_req")
    return response.s3.req_match()

# =============================================================================
def donor():
    """ RESTful CRUD controller """

    tablename = "org_donor"
    table = db[tablename]

    tablename = "org_donor"
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_DONOR,
        title_display = T("Donor Details"),
        title_list = T("Donors Report"),
        title_update = T("Edit Donor"),
        title_search = T("Search Donors"),
        subtitle_create = T("Add New Donor"),
        subtitle_list = T("Donors"),
        label_list_button = T("List Donors"),
        label_create_button = ADD_DONOR,
        label_delete_button = T("Delete Donor"),
        msg_record_created = T("Donor added"),
        msg_record_modified = T("Donor updated"),
        msg_record_deleted = T("Donor deleted"),
        msg_list_empty = T("No Donors currently registered"))

    s3mgr.configure(tablename, listadd=False)
    output = s3_rest_controller(module, resourcename)

    return output

# END =========================================================================
