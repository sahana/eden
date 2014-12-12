 # -*- coding: utf-8 -*-

"""
    Organization Registry - Controllers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # @ToDo: Move this to the Template (separate deployment_setting or else a customize for non-REST controllers)
    template = settings.get_template()
    if template == "SandyRelief":
        # Just redirect to the Facilities
        redirect(URL(f="facility", args=["search"]))
    else:
        # Just redirect to the list of Organisations
        redirect(URL(f="organisation"))

# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def region():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def sector():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def subsector():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def site():
    """
        RESTful CRUD controller
        - used by S3SiteAutocompleteWidget/S3SiteAddressAutocompleteWidget
          which doesn't yet support filtering to just updateable sites
        - used by S3OptionsFilter (e.g. Asset Log)
    """

    # Pre-processor
    def prep(r):
        if r.representation != "json" and \
           r.method not in ("search_ac", "search_address_ac"):
            return False

        # Location Filter
        s3db.gis_location_filter(r)
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def sites_for_org():
    """
        Used to provide the list of Sites for an Organisation
        - used in User Registration
    """

    try:
        org = request.args[0]
    except:
        result = current.xml.json_message(False, 400, "No Org provided!")
    else:
        stable = s3db.org_site
        if settings.get_org_branches():
            # Find all branches for this Organisation
            btable = s3db.org_organisation_branch
            query = (btable.organisation_id == org) & \
                    (btable.deleted != True)
            rows = db(query).select(btable.branch_id)
            org_ids = [row.branch_id for row in rows] + [org]
            query = (stable.organisation_id.belongs(org_ids)) & \
                    (stable.deleted != True)
        else:
            query = (stable.organisation_id == org) & \
                    (stable.deleted != True)
        rows = db(query).select(stable.site_id,
                                stable.name,
                                orderby=stable.name)
        result = rows.json()
    finally:
        response.headers["Content-Type"] = "application/json"
        return result

# -----------------------------------------------------------------------------
def facility():
    """ RESTful CRUD controller """

    return s3db.org_facility_controller()

# -----------------------------------------------------------------------------
def facility_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def office_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def organisation_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def organisation():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.org_organisation_controller()

# -----------------------------------------------------------------------------
def org_search():
    """
        Organisation REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    s3.prep = lambda r: r.method == "search_ac"
    return s3_rest_controller(module, "organisation")

# -----------------------------------------------------------------------------
def organisation_list_represent(l):

    organisation_represent = s3db.org_organisation_represent
    if l:
        max_length = 4
        if len(l) > max_length:
            return "%s, etc" % \
                   organisation_represent.multiple(l[:max_length])
        else:
            return organisation_represent.multiple(l)
    else:
        return NONE

# -----------------------------------------------------------------------------
def office():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.org_office_controller()

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

# -----------------------------------------------------------------------------
def room():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
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
    list_fields = s3db.configure(tablename,
                                        list_fields = ["id",
                                                       "name",
                                                       "description",
                                                      ])
    # Components
    _rheader = s3db.pr_rheader
    _tabs = [(T("Organization"), "organisation/"),
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
    s3db.add_component("pr_group_membership", pr_group="group_id")

    rheader = lambda r: _rheader(r, tabs = _tabs)
    return s3_rest_controller("pr",
                              "group",
                              rheader=rheader)

# -----------------------------------------------------------------------------
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

    s3db.configure(tablename, listadd=False)
    output = s3_rest_controller()

    return output

# -----------------------------------------------------------------------------
def resource():
    """ RESTful CRUD controller """

    def prep(r):
        if r.interactive:
            if r.method in ("create", "update"):
                # Context from a Profile page?"
                table = r.table
                location_id = request.get_vars.get("(location)", None)
                if location_id:
                    field = table.location_id
                    field.default = location_id
                    field.readable = field.writable = False
                organisation_id = request.get_vars.get("(organisation)", None)
                if organisation_id:
                    field = table.organisation_id
                    field.default = organisation_id
                    field.readable = field.writable = False

        return True
    s3.prep = prep
    
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def resource_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def service():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests for Sites """

    return s3db.req_match()

# -----------------------------------------------------------------------------
def incoming():
    """
        Incoming Shipments for Sites

        @unused
    """

    return inv_incoming()

# -----------------------------------------------------------------------------
def facility_geojson():
    """
        Create GeoJSON[P] of Facilities for use by a high-traffic website
        - controller just for testing
        - function normally run on a schedule
    """

    s3db.org_facility_geojson()

# END =========================================================================
