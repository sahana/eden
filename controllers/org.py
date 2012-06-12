# -*- coding: utf-8 -*-

"""
    Organization Registry - Controllers
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

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

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def subsector():
    """ RESTful CRUD controller """

    #tablename = "%s_%s" % (module, resourcename)
    #table = db[tablename]

    return s3_rest_controller()

# =============================================================================
def site():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def site_org_json():

    table = s3db.org_site
    otable = s3db.org_organisation
    response.headers["Content-Type"] = "application/json"
    #db.req_commit.date.represent = lambda dt: dt[:10]
    query = (table.site_id == request.args[0]) & \
            (table.organisation_id == otable.id)
    records = db(query).select(otable.id,
                               otable.name)
    return records.json()

# -----------------------------------------------------------------------------
def facility():
    """ RESTful CRUD controller """

    manager = current.manager
    # remove CRUD generated buttons in the tabs
    manager.configure("inv_inv_item",
                    create=False,
                    listadd=False,
                    editable=False,
                    deletable=False,
                   )
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def facility_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def organisation():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.org_organisation_controller()

# -----------------------------------------------------------------------------
def organisation_list_represent(l):

    organisation_represent = s3db.org_organisation_represent
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
    return s3db.org_office_controller()

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

    return s3_rest_controller()

# =============================================================================
def mailing_list():
    """ RESTful CRUD controller """

    tablename = "pr_group"
    table = s3db[tablename]

    # Only groups with a group_type of 5
    response.s3.filter = (table.group_type == 5)
    table.group_type.writable = False
    table.group_type.readable = False
    table.name.label = T("Mailing List Name")
    s3.crud_strings[tablename] = s3.pr_mailing_list_crud_strings

    # define the list_fields
    list_fields = s3mgr.model.configure(tablename,
                                        list_fields = ["id",
                                                       "name",
                                                       "description",
                                                      ])
    # Components
    _rheader = s3db.pr_rheader
    _tabs = [(T("Organisation"), "organisation/"),
            (T("Mailing List Details"), None),
           ]
    if len(request.args) > 0:
        _tabs.append((T("Members"), "group_membership"))
    if "viewing" in request.vars:
        tablename, record_id = request.vars.viewing.rsplit(".", 1)
        if tablename == "org_organisation":
            table = s3db[tablename]
            _rheader = s3db.org_rheader
            _tabs = []
    s3mgr.model.add_component("pr_group_membership", pr_group="group_id")

    rheader = lambda r: _rheader(r, tabs = _tabs)
    return s3_rest_controller("pr",
                              "group",
                              rheader=rheader)

# =============================================================================
def incoming():
    """ Incoming Shipments """

    return inv_incoming()

# =============================================================================
def match():
    """ Match Requests """

    return s3db.req_match()

# =============================================================================
def donor():
    """ RESTful CRUD controller """

    tablename = "org_donor"
    table = s3db[tablename]

    tablename = "org_donor"
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_DONOR,
        title_display = T("Donor Details"),
        title_list = T("Donors Report"),
        title_update = T("Edit Donor"),
        title_search = T("Search Donors"),
        subtitle_create = T("Add New Donor"),
        label_list_button = T("List Donors"),
        label_create_button = ADD_DONOR,
        label_delete_button = T("Delete Donor"),
        msg_record_created = T("Donor added"),
        msg_record_modified = T("Donor updated"),
        msg_record_deleted = T("Donor deleted"),
        msg_list_empty = T("No Donors currently registered"))

    s3mgr.configure(tablename, listadd=False)
    output = s3_rest_controller()

    return output

# =============================================================================
def req_match():
    """ Match Requests """

    return s3db.req_match()
# END =========================================================================
