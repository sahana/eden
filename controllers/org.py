 # -*- coding: utf-8 -*-

"""
    Organization Registry - Controllers
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    from s3db.cms import cms_index
    return cms_index(c, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Organisations
    s3_redirect_default(URL(f = "organisation"))

# -----------------------------------------------------------------------------
def capacity_assessment():
    """ RESTful CRUD controller """

    from s3 import S3SQLCustomForm, S3SQLInlineComponent

    crud_fields = ["organisation_id",
                   "date",
                   "person_id",
                   ]
    cappend = crud_fields.append

    table = s3db.org_capacity_indicator
    rows = db(table.deleted != True).select(table.id,
                                            table.section,
                                            table.header,
                                            table.number,
                                            table.name,
                                            orderby = table.number,
                                            )

    #subheadings = {}

    section = None
    for row in rows:
        name = "number%s" % row.number
        if row.section != section:
            label = section = row.section
            #subheadings["sub_%sdata" % name] = T(section)
        else:
            label = ""
        cappend(S3SQLInlineComponent("data",
                                     name = name,
                                     label = label,
                                     fields = ((row.header, "indicator_id"),
                                               "rating",
                                               "ranking",
                                               ),
                                     filterby = {"field": "indicator_id",
                                                 "options": row.id
                                                 },
                                     multiple = False,
                                     ),
                )

    crud_form = S3SQLCustomForm(*crud_fields)

    s3db.configure("org_capacity_assessment",
                   crud_form = crud_form,
                   #subheadings = subheadings,
                   )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def capacity_assessment_data():
    """
        RESTful CRUD controller
        - just used for the custom_report method
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def capacity_indicator():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """

    # Use hrm/group controller for teams rather than pr/group
    s3db.configure("pr_group",
                   linkto = lambda record_id: \
                            URL(c="hrm", f="group",
                                args = [record_id],
                                ),
                   )

    from s3db.org import org_rheader
    return s3_rest_controller(rheader = org_rheader)

# -----------------------------------------------------------------------------
def group_membership():
    """
        RESTful CRUD controller
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def group_membership_status():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def group_person():
    """
        RESTful CRUD controller
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def group_person_status():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def facility():
    """ RESTful CRUD controller """

    from s3db.org import org_facility_controller
    return org_facility_controller()

# -----------------------------------------------------------------------------
def facility_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def office():
    """ RESTful CRUD controller """

    from s3db.org import org_office_controller
    return org_office_controller()

# -----------------------------------------------------------------------------
def office_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def organisation():
    """ RESTful CRUD controller """

    # Defined in the Model for use from Multiple Controllers for unified menus
    from s3db.org import org_organisation_controller
    return org_organisation_controller()

# -----------------------------------------------------------------------------
def organisation_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def organisation_organisation_type():
    """
        RESTful CRUD controller
        - just used for options.s3json lookups
    """

    s3.prep = lambda r: \
        r.representation == "s3json" and r.method == "options"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def org_search():
    """
        Organisation REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    s3.prep = lambda r: r.method == "search_ac"

    return s3_rest_controller("org", "organisation")

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
def region():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def sector():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def site():
    """
        RESTful CRUD controller
        - used by S3SiteAutocompleteWidget
          which doesn't yet support filtering to just updateable sites
        - used by site_contact_person()
        - used by S3OptionsFilter (e.g. Asset Log)
        - used by s3.asset_log.js to read the Site Layout Hierarchy
    """

    # Pre-processor
    def prep(r):
        if r.representation != "json" and \
           r.method not in ("search_ac", "search_address_ac", "site_contact_person"):
            if r.id:
                # Redirect to the instance controller
                (prefix, resourcename, id) = s3db.get_instance(db.org_site, r.id)
                # If we have a controller defined in s3db then we can Forward without a Redirect
                # Use Web2Py's Custom Importer rather than importlib.import_module
                parent = __import__("s3db", fromlist=["s3db"])
                module = parent.__dict__[prefix]
                controller = "%s_%s_controller" % (prefix, resourcename)
                names = module.__all__
                if controller in names:
                    s3models = module.__dict__
                    function = s3models[controller]
                    request.controller = prefix
                    request.function = resourcename
                    request.args[0] = str(id)
                    return function()
                else:
                    # Revert to a Redirect
                    args = r.args
                    args[0] = id
                    redirect(URL(c = prefix,
                                 f = resourcename,
                                 args = args,
                                 vars = r.get_vars,
                                 ))

            else:
                # Not supported
                return False

        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        return True
    s3.prep = prep

    return s3_rest_controller()

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
                                    orderby = stable.name,
                                    )
            result = rows.json()
    finally:
        response.headers["Content-Type"] = "application/json"
        return result

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
                                 list_fields = ["name",
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
    s3db.add_components("pr_group",
                        pr_group_membership = "group_id",
                        )

    rheader = lambda r: _rheader(r, tabs = _tabs)

    return s3_rest_controller("pr", "group",
                              rheader = rheader,
                              )

# -----------------------------------------------------------------------------
#def organisation_location():
#    """ RESTful CRUD controller """

#    return s3_rest_controller()

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
def service_location():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def service_mode():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def booking_mode():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def site_location():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests for Sites """

    from s3db.inv import inv_req_match
    return inv_req_match()

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
