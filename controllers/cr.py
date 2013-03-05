# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# S3 framework functions
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

    # Access Presence from Shelters for Check-In/Check-Out
    s3db.add_component("pr_presence",
                       cr_shelter="shelter_id")

    s3db.configure("cr_shelter",
                   # Go to People check-in for this shelter after creation
                   create_next = URL(c="cr", f="shelter",
                                     args=["[id]", "presence"]))

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.method == "import":
            table.organisation_id.default = None

        if r.component and r.component.name == "presence":
            prtable = db.pr_presence
            r.resource.add_filter(prtable.closed == False)

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
                    # Filter out people which are already staff for this warehouse
                    s3base.s3_filter_staff(r)
                    # Make it clear that this is for adding new staff, not assigning existing
                    s3.crud_strings.hrm_human_resource.label_create_button = T("Add New Staff Member")
                    # Cascade the organisation_id from the hospital to the staff
                    field = s3db.hrm_human_resource.organisation_id
                    field.default = r.record.organisation_id
                    field.writable = False

                elif r.component.name == "rat":
                    # Hide the Implied fields
                    db.assess_rat.location_id.writable = False
                    db.assess_rat.location_id.default = r.record.location_id
                    db.assess_rat.location_id.comment = ""
                    # Set defaults
                    staff_id = auth.s3_logged_in_human_resource()
                    if staff_id:
                        db.assess_rat.staff_id.default = staff_id.id

                elif r.component.name == "presence":
                    field = prtable.shelter_id
                    represent = s3base.S3Represent(lookup="cr_shelter")
                    field.requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter.id",
                                                          represent,
                                                          sort=True))
                    field.represent = represent
                    field.ondelete = "RESTRICT"
                    if settings.get_ui_label_camp():
                        HELP = T("The Camp this person is checking into.")
                    else:
                        HELP = T("The Shelter this person is checking into.")
                    ADD_SHELTER = s3.ADD_SHELTER
                    SHELTER_LABEL = s3.SHELTER_LABEL
                    field.comment = S3AddResourceLink(c="cr",
                                                      f="shelter",
                                                      title=ADD_SHELTER,
                                                      tooltip=HELP)
                    field.label = SHELTER_LABEL
                    field.readable = True
                    field.writable = True

                    if settings.get_ui_label_camp():
                        REGISTER_LABEL = T("Register Person into this Camp")
                        EMPTY_LIST = T("No People currently registered in this camp")
                    else:
                        REGISTER_LABEL = T("Register Person into this Shelter")
                        EMPTY_LIST = T("No People currently registered in this shelter")

                    # Make pr_presence.pe_id visible:
                    pe_id = prtable.pe_id
                    pe_id.readable = pe_id.writable = True

                    # Usually, the pe_id field is an invisible foreign key, therefore it
                    # has no default representation/requirements => need to add this here:
                    pe_id.label = T("Person/Group")
                    pe_represent = s3db.pr_pentity_represent
                    pe_id.represent = pe_represent
                    pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                               pe_represent,
                                               filterby="instance_type",
                                               orderby="instance_type",
                                               filter_opts=("pr_person",
                                                            "pr_group"))
                    pe_id.widget = S3AutocompleteWidget("pr", "pentity")
                    gtable = s3db.pr_group
                    add_group_label = s3base.S3CRUD.crud_string("pr_group", "label_create_button")
                    pe_id.comment = \
                        DIV(s3db.pr_person_comment(T("Add Person"), REGISTER_LABEL, child="pe_id"),
                            S3AddResourceLink(c="pr",
                                              f="group",
                                              title=add_group_label,
                                              tooltip=T("Create a group entry in the registry."))
                        )

                    # Make Persons a component of Presence to add to list_fields
                    s3db.add_component("pr_person",
                                       pr_presence=Storage(joinby="pe_id", pkey="pe_id"))

                    s3db.configure("pr_presence",
                                   # presence not deletable in this view! (need to register a check-out
                                   # for the same person instead):
                                   deletable=False,
                                   list_fields=["id",
                                                "pe_id",
                                                "datetime",
                                                "presence_condition",
                                                #"proc_desc",
                                                "person.age_group",
                                                ])

                    # Hide the Implied fields
                    lfield = prtable.location_id
                    lfield.writable = False
                    lfield.default = r.record.location_id
                    lfield.comment = ""
                    prtable.proc_desc.readable = prtable.proc_desc.writable = False
                    # Set defaults
                    #prtable.datetime.default = request.utcnow
                    #prtable.observer.default = s3_logged_in_person()
                    popts = s3.pr_presence_opts
                    pcnds = s3.pr_presence_conditions
                    cr_shelter_presence_opts = {
                        popts.CHECK_IN: pcnds[popts.CHECK_IN],
                        popts.CHECK_OUT: pcnds[popts.CHECK_OUT]
                    }
                    prtable.presence_condition.requires = IS_IN_SET(
                        cr_shelter_presence_opts, zero=None)
                    prtable.presence_condition.default = popts.CHECK_IN
                    # Change the Labels
                    s3.crud_strings.pr_presence = Storage(
                        title_create = T("Register Person"),
                        title_display = T("Registration Details"),
                        title_list = T("Registered People"),
                        title_update = T("Edit Registration"),
                        title_search = T("Search Registations"),
                        subtitle_create = REGISTER_LABEL,
                        label_list_button = T("List Registrations"),
                        label_create_button = T("Register Person"),
                        msg_record_created = T("Registration added"),
                        msg_record_modified = T("Registration updated"),
                        msg_record_deleted = T("Registration entry deleted"),
                        msg_list_empty = EMPTY_LIST
                    )

                elif r.component.name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        s3db.req_create_form_mods()

        return True
    s3.prep = prep

    rheader = s3db.cr_shelter_rheader
    output = s3_rest_controller(rheader=rheader)

    return output

# =============================================================================
def incoming():
    """ Incoming Shipments """

    return inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    return s3db.req_match()

# END =========================================================================
