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

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                cname = r.component_name
                if cname in ("inv_item", "recv", "send"):
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                    # remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create=False,
                                   listadd=False,
                                   editable=False,
                                   deletable=False,
                                   )

                elif cname == "human_resource":
                    # Filter to just Staff
                    s3.filter = (s3db.hrm_human_resource.type == 1)
                    # Make it clear that this is for adding new staff, not assigning existing
                    s3.crud_strings.hrm_human_resource.label_create_button = T("Add New Staff Member")
                    # Cascade the organisation_id from the office to the staff
                    htable = s3db.hrm_human_resource
                    field = htable.organisation_id
                    field.default = r.record.organisation_id
                    field.writable = False
                    field.comment = None
                    # Filter out people which are already staff for this office
                    s3base.s3_filter_staff(r)
                    # Modify list_fields
                    s3db.configure("hrm_human_resource",
                                   list_fields=["person_id",
                                                "phone",
                                                "email",
                                                "organisation_id",
                                                "job_title_id",
                                                "department_id",
                                                "site_contact",
                                                "status",
                                                "comments",
                                                ]
                                   )

                elif cname == "req" and r.method not in ("update", "read"):
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    s3db.req_create_form_mods()

                elif cname == "asset":
                    # Default/Hide the Organisation & Site fields
                    record = r.record
                    atable = s3db.asset_asset
                    field = atable.organisation_id
                    field.default = record.organisation_id
                    field.readable = field.writable = False
                    field = atable.site_id
                    field.default = record.site_id
                    field.readable = field.writable = False
                    # Stay within Facility tab
                    s3db.configure("asset_asset",
                                   create_next = None)

            elif r.id:
                field = r.table.obsolete
                field.readable = field.writable = True

        elif r.representation == "geojson":
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker
        
        return True
    s3.prep = prep

    def postp(r, output):
        if r.representation == "plain" and \
             r.method !="search":
            # Custom Map Popup
            output = TABLE()
            append = output.append
            # Edit button
            append(TR(TD(A(T("Edit"),
                           _target="_blank",
                           _id="edit-btn",
                           _href=URL(args=[r.id, "update"])))))

            # Name
            append(TR(TD(B("%s:" % T("Name"))),
                      TD(r.record.name)))

            # Type(s)
            ttable = db.org_facility_type
            ltable = db.org_site_facility_type
            query = (ltable.site_id == r.record.site_id) & \
                    (ltable.facility_type_id == ttable.id)
            rows = db(query).select(ttable.name)
            if rows:
                append(TR(TD(B("%s:" % ltable.facility_type_id.label)),
                          TD(", ".join([row.name for row in rows]))))

            # Comments
            if r.record.comments:
                append(TR(TD(B("%s:" % r.table.comments.label)),
                          TD(r.record.comments)))

            # Organisation (better with just name rather than Represent)
            # @ToDo: Make this configurable - some users will only see
            #        their staff so this is a meaningless field for them
            table = db.org_organisation
            org = db(table.id == r.record.organisation_id).select(table.name,
                                                                  limitby=(0, 1)
                                                                  ).first()
            if org:
                append(TR(TD(B("%s:" % r.table.organisation_id.label)),
                          TD(org.name)))

            site_id = r.record.site_id

            if settings.has_module("req"):
                # Open/High/Medium priority Requests
                rtable = s3db.req_req
                query = (rtable.site_id == site_id) & \
                        (rtable.fulfil_status != 2) & \
                        (rtable.priority.belongs((2, 3)))
                reqs = db(query).select(rtable.id,
                                        rtable.req_ref,
                                        rtable.type,
                                        )
                if reqs:
                    append(TR(TD(B("%s:" % T("Requests")))))
                    req_types = {1:"req_item",
                                 3:"req_skill",
                                 8:"",
                                 9:"",
                                 }
                    vals = [A(req.req_ref,
                              _href=URL(c="req", f="req",
                                        args=[req.id, req_types[req.type]])) for req in reqs]
                    for val in vals:
                        append(TR(TD(val, _colspan=2)))

            # Street address
            gtable = s3db.gis_location
            stable = s3db.org_site
            query = (gtable.id == stable.location_id) & \
                    (stable.id == site_id)
            location = db(query).select(gtable.addr_street,
                                        limitby=(0, 1)).first()
            if location.addr_street:
                append(TR(TD(B("%s:" % gtable.addr_street.label)),
                          TD(location.addr_street)))

            # Opening Times
            opens = r.record.opening_times
            if opens:
                append(TR(TD(B("%s:" % r.table.opening_times.label)),
                          TD(opens)))

            # Phone number
            contact = r.record.contact
            if contact:
                append(TR(TD(B("%s:" % r.table.contact.label)),
                          TD(contact)))

            # Phone number
            phone1 = r.record.phone1
            if phone1:
                append(TR(TD(B("%s:" % r.table.phone1.label)),
                          TD(phone1)))

            # Email address (as hyperlink)
            email = r.record.email
            if email:
                append(TR(TD(B("%s:" % r.table.email.label)),
                          TD(A(email, _href="mailto:%s" % email))))

            # Website (as hyperlink)
            website = r.record.website
            if website:
                append(TR(TD(B("%s:" % r.table.website.label)),
                          TD(A(website, _href=website))))

        return output
    s3.postp = postp

    if "map" in request.args:
        # S3Map has migrated
        hide_filter = False
    else:
        # Not yet ready otherwise
        hide_filter = True

    output = s3_rest_controller(rheader=s3db.org_rheader,
                                hide_filter=hide_filter,
                                )
    return output

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
