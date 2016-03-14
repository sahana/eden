# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
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

    # Just redirect to the list of Shelters
    s3_redirect_default(URL(f="shelter"))

# =============================================================================
def shelter_type():
    """
        RESTful CRUD controller
        List / add shelter types (e.g. NGO-operated, Government evacuation center,
        School, Hospital -- see Agasti opt_camp_type.)
    """

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def shelter_service():
    """
        RESTful CRUD controller
        List / add shelter services (e.g. medical, housing, food, ...)
    """

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def shelter_unit():
    """
        REST controller to
            retrieve options for shelter unit selection
            show layer on Map
            imports
    """

    # [Geo]JSON & Map Popups or Imports only
    def prep(r):
        if r.representation == "plain":
            # Have the 'Open' button open in the context of the Shelter
            record_id = r.id
            table = s3db.cr_shelter_unit
            row = db(table.id == record_id).select(table.shelter_id,
                                                   limitby=(0, 1)
                                                   ).first()
            shelter_id = row.shelter_id
            s3db.configure("cr_shelter_unit",
                           popup_url = URL(c="cr", f="shelter",
                                           args=[shelter_id, "shelter_unit",
                                                 record_id]),
                        )
            return True
        elif r.representation in ("json", "geojson", "plain") or \
             r.method == "import":
            return True
        return False

    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def shelter_registration():
    """
        RESTful CRUD controller
    """

    s3.crud_strings.cr_shelter_registration = Storage(
        label_create = T("Register Person"),
        title_display = T("Registration Details"),
        title_list = T("Registered People"),
        title_update = T("Edit Registration"),
        label_list_button = T("List Registrations"),
        msg_record_created = T("Registration added"),
        msg_record_modified = T("Registration updated"),
        msg_record_deleted = T("Registration entry deleted"),
        msg_list_empty = T("No people currently registered in this shelter")
        )

    output = s3_rest_controller()
    return output

# =============================================================================
def shelter():
    """
        RESTful CRUD controller
    """

    tablename = "cr_shelter"
    table = s3db.cr_shelter

    # Filter to just Open shelters (status=2)
    s3base.s3_set_default_filter("~.status", [2, None], tablename=tablename)

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        method = r.method
        if method == "create":
            table.population_day.readable = False
            table.population_night.readable = False

        elif method == "import":
            table.organisation_id.default = None

        elif method == "profile":
            shelter_id = r.id
            name = r.record.name
            
            profile_header = settings.get_ui_profile_header(r)

            map_widget = dict(label = T("Housing Units"),
                              type = "map",
                              icon = "icon-map",
                              colspan = 2,
                              height = 500,
                              #bbox = bbox,
                              )
            ftable = s3db.gis_layer_feature
            query = (ftable.controller == "cr") & \
                    (ftable.function == "shelter_unit")
            layer = db(query).select(ftable.layer_id,
                                     limitby=(0, 1)
                                     ).first()
            try:
                layer = dict(active = True,
                             layer_id = layer.layer_id,
                             filter = "~.shelter_id=%s" % shelter_id,
                             name = T("Housing Units"),
                             id = "profile-header-%s-%s" % (tablename, shelter_id),
                             )
            except:
                # No suitable prepop found
                layer = None

            profile_widgets = [map_widget,
                               ]
            s3db.configure(tablename,
                           profile_header = profile_header,
                           profile_layers = (layer,),
                           profile_title = "%s : %s" % (s3_unicode(s3.crud_strings["cr_shelter"].title_display),
                                                        name),
                           profile_widgets = profile_widgets,
                           )

        if r.interactive:
            if r.id:
                table.obsolete.readable = table.obsolete.writable = True
            if r.component:
                if r.component.name == "inv_item" or \
                   r.component.name == "recv" or \
                   r.component.name == "send":
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                elif r.component.name == "human_resource":
                    s3db.org_site_staff_config(r)

                elif r.component.name == "rat":
                    # Hide the Implied fields
                    db.assess_rat.location_id.writable = False
                    db.assess_rat.location_id.default = r.record.location_id
                    db.assess_rat.location_id.comment = ""
                    # Set defaults
                    staff_id = auth.s3_logged_in_human_resource()
                    if staff_id:
                        db.assess_rat.staff_id.default = staff_id.id

                elif r.component.name == "shelter_registration":
                    if settings.get_cr_shelter_housing_unit_management():
                        # Filter housing units to units of this shelter
                        field = s3db.cr_shelter_registration.shelter_unit_id
                        dbset = db(s3db.cr_shelter_unit.shelter_id == r.id)
                        field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "cr_shelter_unit.id",
                                                               field.represent,
                                                               sort=True,
                                                               ))
                    s3.crud_strings.cr_shelter_registration = Storage(
                        label_create = T("Register Person"),
                        title_display = T("Registration Details"),
                        title_list = T("Registered People"),
                        title_update = T("Edit Registration"),
                        label_list_button = T("List Registrations"),
                        msg_record_created = T("Registration added"),
                        msg_record_modified = T("Registration updated"),
                        msg_record_deleted = T("Registration entry deleted"),
                        msg_list_empty = T("No people currently registered in this shelter")
                    )

                elif r.component.name == "shelter_allocation":
                    s3.crud_strings.cr_shelter_allocation = Storage(
                        label_create = T("Allocate Group"),
                        title_display = T("Allocation Details"),
                        title_list = T("Allocated Groups"),
                        title_update = T("Edit Allocation"),
                        label_list_button = T("List Allocations"),
                        msg_record_created = T("Reservation done"),
                        msg_record_modified = T("Reservation updated"),
                        msg_record_deleted = T("Reservation entry deleted"),
                        msg_list_empty = T("No groups currently allocated for this shelter")
                    )

                elif r.component.name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        s3db.req_create_form_mods()

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.cr_shelter_rheader)

# =============================================================================
def incoming():
    """
        Incoming Shipments for Sites

        Used from Requests rheader when looking at Transport Status
    """

    # @ToDo: Create this function!
    return s3db.inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    return s3db.req_match()

# END =========================================================================
