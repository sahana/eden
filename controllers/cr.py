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
    redirect(URL(f="shelter"))

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

# =============================================================================
def shelter():

    """
        RESTful CRUD controller
    """

    table = s3db.cr_shelter

    # Filter to just Open shelters (status=2)
    s3base.s3_set_default_filter("~.status", [2, None], tablename="cr_shelter")

    s3db.configure("cr_shelter",
                   # Go to People check-in for this shelter after creation
                   create_next = URL(c="cr", f="shelter",
                                     args=["[id]", "shelter_registration"]))

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.method == "create":
            table.population_day.readable = False
            table.population_night.readable = False

        if r.method == "import":
            table.organisation_id.default = None

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

                    # Show a non blocking warning in case the people in the shelter are more than its capacity
                    if not r.method:
                        record = db(table.id == r.id).select(table.capacity_day,
                                                             table.population_day,
                                                             table.capacity_night,
                                                             table.population_night,
                                                             limitby=(0, 1)
                                                             ).first()
                        cap_day = record.capacity_day
                        pop_day = record.population_day
                        if (cap_day is not None) and (pop_day > cap_day):
                            response.warning = T("Warning: this shelter is full for daytime")

                        cap_night = record.capacity_night
                        pop_night = record.population_night
                        if (cap_night is not None) and (pop_night > cap_night):
                            response.warning = T("Warning: this shelter is full for the night")

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
    """ Incoming Shipments """

    return inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    return s3db.req_match()

# END =========================================================================
