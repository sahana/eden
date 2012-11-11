# -*- coding: utf-8 -*-

"""
    Organization Registry - Controllers
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name

    item = None
    if settings.has_module("cms"):
        table = s3db.cms_post
        _item = db(table.module == module).select(table.id,
                                                  table.body,
                                                  limitby=(0, 1)).first()
        if _item:
            if s3_has_role(ADMIN):
                item = DIV(XML(_item.body),
                           BR(),
                           A(T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[_item.id, "update"],
                                       vars={"module":module}),
                             _class="action-btn"))
            else:
                item = XML(_item.body)
        elif s3_has_role(ADMIN):
            item = DIV(H2(module_name),
                       A(T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module":module}),
                         _class="action-btn"))

    if not item:
        #item = H2(module_name)
        # Just redirect to the Facilities Map
        redirect(URL(f="facility", args=["map"]))

    # tbc
    report = ""

    response.view = "index.html"
    return dict(item=item, report=report)

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
        - used by S3SiteAutocompleteWidget(), which doesn't yet support filtering
                                              to just updateable sites
    """

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def site_org_json():
    """
    """

    table = s3db.org_site
    otable = s3db.org_organisation
    response.headers["Content-Type"] = "application/json"
    query = (table.site_id == request.args[0]) & \
            (table.organisation_id == otable.id)
    records = db(query).select(otable.id,
                               otable.name)
    return records.json()

# -----------------------------------------------------------------------------
def facility_marker_fn(record):
    """
        Function to decide which Marker to use for Facilities Map
        @ToDo: Use Symbology
    """

    table = db.org_facility_type
    # @ToDo: Handle case where we use multiple types!
    type = db(table.id == record.facility_type_id).select(table.name,
                                                          limitby=(0, 1)
                                                          ).first().name
    if type == "Hub":
        marker = "warehouse"
    elif type == "Relief Site":
        marker = "asset"
    elif type == "Medical Clinic":
        marker = "hospital"
    elif type == "Food":
        marker = "food"
    elif type == "Residential Building":
        marker = "residence"
    #elif type == "Shelter":
    #    marker = "shelter"
    else:
        # Unknown
        marker = "marker_red"
    # @ToDo: Colour code by open/priority requests
    #if status:
    #    if status.facility_status == 1:
    #        # Normal
    #        marker = "%s_green" % marker
    #    elif status.facility_status in (3, 4):
    #        # Evacuating or Closed
    #        marker = "%s_red" % marker
    #    elif status.facility_status == 2:
    #        # Compromised
    #        marker = "%s_yellow" % marker

    mtable = db.gis_marker
    marker = db(mtable.name == marker).select(mtable.image,
                                              mtable.height,
                                              mtable.width,
                                              cache=s3db.cache,
                                              limitby=(0, 1)).first()
    return marker

# -----------------------------------------------------------------------------
def facility():
    """ RESTful CRUD controller """
    
    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                # remove CRUD generated buttons in the tabs
                s3db.configure("inv_inv_item",
                               create=False,
                               listadd=False,
                               editable=False,
                               deletable=False,
                               )
            elif r.method == "update":
                field = r.table.obsolete
                field.readable = field.writable = True
            elif r.method == "map":
                s3db.configure("org_facility", marker_fn=facility_marker_fn)
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

            # Type
            if r.record.facility_type_id:
                append(TR(TD(B("%s:" % r.table.facility_type_id.label)),
                          TD(r.table.facility_type_id.represent(r.record.facility_type_id))))

            # Comments
            if r.record.comments:
                append(TR(TD(B("%s:" % r.table.comments.label)),
                          TD(r.record.comments)))

            # Organization (better with just name rather than Represent)
            # @ToDo: Make this configurable - some deployments will only see
            #        their staff so this is a meaningless field
            table = s3db.org_organisation
            query = (table.id == r.record.organisation_id)
            org = db(query).select(table.name,
                                    limitby=(0, 1)).first()
            if org:
                append(TR(TD(B("%s:" % r.table.organisation_id.label)),
                          TD(org.name)))

            # Requests link to the Site_ID
            site_id = r.record.site_id

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
                             9:"",
                             }
                vals = [A(req.req_ref, _href=URL(c="req", f="req", args=[req.id, req_types[req.type]])) for req in reqs]
                for val in vals:
                    append(TR(TD(val, _colspan=2)))

            gtable = s3db.gis_location
            stable = s3db.org_site
            query = (gtable.id == stable.location_id) & \
                    (stable.id == site_id)
            location = db(query).select(gtable.addr_street,
                                        limitby=(0, 1)).first()
            # Street address
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

    output = s3_rest_controller(rheader=s3db.org_rheader)
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
        - limited to just search.json for use in Autocompletes
        - allows differential access permissions
    """

    s3.prep = lambda r: r.representation == "json" and \
                        r.method == "search"
    return s3_rest_controller(module, "organisation")

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

# END =========================================================================
