"""
    Organization Registry - Controllers
"""

module = request.controller
#resourcename = request.function

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

    # Just redirect to the list of Organisations
    s3_redirect_default(URL(f="organisation"))

# -----------------------------------------------------------------------------
def group_type():
    """ Organisation Group Types: CRUD Controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """

    # Use hrm/group controller for teams rather than pr/group
    s3db.configure("pr_group",
                   linkto = lambda record_id: \
                            URL(c="hrm", f="group", args=[record_id]),
                   )

    return crud_controller(rheader=s3db.org_rheader)

# -----------------------------------------------------------------------------
def group_membership():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return crud_controller()

# -----------------------------------------------------------------------------
def group_membership_status():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def group_person():
    """ REST controller for options.s3json lookups """

    s3.prep = lambda r: r.representation == "s3json" and r.method == "options"

    return crud_controller()

# -----------------------------------------------------------------------------
def group_person_status():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def facility():
    """ RESTful CRUD controller """

    return s3db.org_facility_controller()

# -----------------------------------------------------------------------------
def facility_type():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def office():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.org_office_controller()

# -----------------------------------------------------------------------------
def office_type():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def organisation():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.org_organisation_controller()

# -----------------------------------------------------------------------------
def organisation_type():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def organisation_organisation_type():
    """ REST controller for options.s3json lookups """

    s3.prep = lambda r: r.representation == "s3json" and r.method == "options"

    return crud_controller()

# -----------------------------------------------------------------------------
def org_search():
    """
        Organisation REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    s3.prep = lambda r: r.method == "search_ac"

    return crud_controller(module, "organisation")

# -----------------------------------------------------------------------------
def region():
    """ RESTful CRUD controller """

    def prep(r):
        if r.representation == "popup":

            if settings.get_org_regions_hierarchical():

                table = r.table

                # Zone is required when creating new regions from popup
                field = table.parent
                requires = field.requires
                if isinstance(requires, IS_EMPTY_OR):
                    field.requires = requires.other

        return True
    s3.prep = prep

    return crud_controller()

# -----------------------------------------------------------------------------
def sector():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)
        return True
    s3.prep = prep

    return crud_controller()

# -----------------------------------------------------------------------------
def subsector():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def site():
    """
        RESTful CRUD controller
        - used by S3SiteAutocompleteWidget
          which doesn't yet support filtering to just updateable sites
        - used by site_contact_person()
        - used by OptionsFilter (e.g. Asset Log)
    """

    # Pre-processor
    def prep(r):
        if r.representation != "json" and \
           r.method not in ("search_ac", "search_address_ac", "site_contact_person"):
            return False

        # Location Filter
        s3db.gis_location_filter(r)
        return True
    s3.prep = prep

    return crud_controller()

# -----------------------------------------------------------------------------
def sites_for_org():
    """
        Used to provide the list of Sites for an Organisation
        - used in User Registration & Assets

        Access via the .json representation to avoid work rendering menus, etc
    """

    try:
        org = request.args[0]
    except:
        result = current.xml.json_message(False, 400, "No Org provided!")
    else:
        try:
            org = int(org)
        except:
            result = current.xml.json_message(False, 400, "Invalid Org provided!")
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
def person():
    """ Person controller for PersonSelector """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            current.xml.show_ids = True
        return True
    s3.prep = prep

    return crud_controller("pr", "person")

# -----------------------------------------------------------------------------
def room():
    """ RESTful CRUD controller """

    def prep(r):

        field = r.table.site_id
        field.readable = field.writable = True

        if r.representation == "popup":
            site_id = r.get_vars.get("site_id")
            if site_id:
                # Coming from dynamically filtered PopupLink
                field.default = site_id
                field.writable = False

        return True
    s3.prep = prep

    return crud_controller()

# -----------------------------------------------------------------------------
def mailing_list():
    """ RESTful CRUD controller """

    tablename = "pr_group"
    table = s3db[tablename]

    # Only groups with a group_type of 5
    s3.filter = (table.group_type == 5)
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
    s3db.add_components("pr_group", pr_group_membership="group_id")

    rheader = lambda r: _rheader(r, tabs = _tabs)

    return crud_controller("pr", "group", rheader=rheader)

# -----------------------------------------------------------------------------
def resource():
    """ RESTful CRUD controller """

    def prep(r):
        if r.interactive:
            if r.method in ("create", "update"):
                # Context from a Profile page?"
                table = r.table
                location_id = get_vars.get("(location)", None)
                if location_id:
                    field = table.location_id
                    field.default = location_id
                    field.readable = field.writable = False
                organisation_id = get_vars.get("(organisation)", None)
                if organisation_id:
                    field = table.organisation_id
                    field.default = organisation_id
                    field.readable = field.writable = False

        return True
    s3.prep = prep

    return crud_controller()

# -----------------------------------------------------------------------------
def resource_type():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def service():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def service_location():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def service_mode():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def booking_mode():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def site_location():
    """ RESTful CRUD controller """

    return crud_controller()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests for Sites """

    return s3db.req_match()

# -----------------------------------------------------------------------------
def incoming():
    """
        Incoming Shipments for Sites

        Used from Requests rheader when looking at Transport Status
    """

    # @ToDo: Create this function!
    return s3db.inv_incoming()

# -----------------------------------------------------------------------------
def facility_geojson():
    """
        Create a Static GeoJSON[P] of Facilities for use by a high-traffic website
        - controller just for testing
        - function normally run on a schedule

        Access via the .json representation to avoid work rendering menus, etc
    """

    s3db.org_facility_geojson()

# END =========================================================================
