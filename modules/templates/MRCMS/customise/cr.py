"""
    CR module customisations for MRCMS

    License: MIT
"""

from collections import OrderedDict

from gluon import current, URL, DIV, H4, P, TAG, IS_EMPTY_OR

from core import BasicCRUD, FS, IS_ONE_OF, \
                 LocationSelector, PresenceRegistration, CustomForm, \
                 DateFilter, OptionsFilter, RangeFilter, TextFilter, get_filter_options, \
                 get_form_record_id, s3_fieldmethod, s3_str, represent_occupancy

# -------------------------------------------------------------------------
def client_site_status(person_id, site_id, site_type, case_status):
    """
        Check whether a person to register at a site is a resident,
        whether they are permitted to enter/leave premises, and whether
        there are advice/instructions to the reception staff

        Args:
            person_id: the person ID
            site_id: the site ID
            site_type: the site type (tablename)
            case_status: the current case status (Row)
        Returns:
            dict, see person_site_status
    """

    T = current.T

    db = current.db
    s3db = current.s3db

    result = {"valid": False,
              "allowed_in": False,
              "allowed_out": False,
              }

    if case_status.is_closed:
        result["error"] = T("Closed case")
        return result

    if site_type == "cr_shelter":
        # Check for a shelter registration
        stable = s3db.cr_shelter
        rtable = s3db.cr_shelter_registration
        query = (stable.site_id == site_id) & \
                (stable.id == rtable.shelter_id) & \
                (rtable.person_id == person_id) & \
                (rtable.deleted != True)
        registration = db(query).select(rtable.id,
                                        rtable.registration_status,
                                        limitby=(0, 1),
                                        ).first()
        if not registration or registration.registration_status == 3:
            # No registration with this site, or checked-out
            return result

    result["valid"] = True

    # Get the current presence status at the site
    from core import SitePresence
    presence = SitePresence.status(person_id, site_id)[0]

    allowed_in = True
    allowed_out = True

    # Check if we have any case flag to deny passage and/or to show instructions
    ftable = s3db.dvr_case_flag
    ltable = s3db.dvr_case_flag_case
    query = (ltable.person_id == person_id) & \
            (ltable.deleted != True) & \
            (ftable.id == ltable.flag_id) & \
            (ftable.deleted != True)
    flags = db(query).select(ftable.name,
                             ftable.deny_check_in,
                             ftable.deny_check_out,
                             ftable.advise_at_check_in,
                             ftable.advise_at_check_out,
                             ftable.advise_at_id_check,
                             ftable.instructions,
                             )
    info = []
    append = info.append
    for flag in flags:
        # Deny IN/OUT?
        if flag.deny_check_in:
            allowed_in = False
        if flag.deny_check_out:
            allowed_out = False

        # Show flag instructions?
        if flag.advise_at_id_check:
            advise = True
        elif presence == "IN":
            advise = flag.advise_at_check_out
        elif presence == "OUT":
            advise = flag.advise_at_check_in
        else:
            advise = flag.advise_at_check_in or flag.advise_at_check_out
        if advise:
            instructions = flag.instructions
            if instructions is not None:
                instructions = instructions.strip()
            if not instructions:
                instructions = current.T("No instructions for this flag")
            append(DIV(H4(T(flag.name)),
                       P(instructions),
                       _class="checkpoint-instructions",
                       ))
    if info:
        result["info"] = DIV(_class="checkpoint-advise", *info)

    result["allowed_in"] = allowed_in
    result["allowed_out"] = allowed_out

    return result

# -------------------------------------------------------------------------
def staff_site_status(person_id, site_id, organisation_ids):
    """
        Check whether a person to register at a site is a staff member

        Args:
            person_id: the person ID
            organisation_ids: IDs of all valid staff organisations for the site
        Returns:
            dict, see person_site_status
    """

    db = current.db
    s3db = current.s3db

    htable = s3db.hrm_human_resource
    query = (htable.person_id == person_id) & \
            (htable.organisation_id.belongs(organisation_ids)) & \
            (htable.status == 1) & \
            (htable.deleted == False)
    staff = db(query).select(htable.id, limitby=(0, 1)).first()

    valid = bool(staff)

    result = {"valid": valid,
              "allowed_in": valid,
              "allowed_out": valid,
              }
    return result

# -------------------------------------------------------------------------
def person_site_status(site_id, person):
    """
        Determine the current status of a person with regard to
        entering/leaving a site

        Args:
            site_id: the site ID
            person: the person record
        Returns:
            dict {"valid": Person can be registered in/out at the site,
                  "error": Error message for the above,
                  "allowed_in": Person is allowed to enter the site,
                  "allowed_out": Person is allowed to leave the site,
                  "info": Instructions for reception staff,
                  }
    """

    T = current.T

    db = current.db
    s3db = current.s3db

    result = {"valid": False,
              "allowed_in": False,
              "allowed_out": False,
              }
    person_id = person.id

    # Get the site type and managing organisation(s)
    otable = s3db.org_organisation
    stable = s3db.org_site
    join = otable.on(otable.id == stable.organisation_id)
    row = db(stable.site_id == site_id).select(stable.instance_type,
                                               otable.id,
                                               otable.root_organisation,
                                               otable.pe_id,
                                               join = join,
                                               limitby = (0, 1),
                                               ).first()
    if not row:
        result["error"] = T("Invalid site")
        return result

    site = row.org_site
    organisation = row.org_organisation

    organisation_ids = [organisation.id]

    root_org = organisation.root_organisation
    if root_org and root_org != organisation.id:
        # Include all parent organisations
        pe_ids = s3db.pr_get_ancestors(organisation.pe_id)
        rows = db((otable.pe_id.belongs(pe_ids))).select(otable.id)
        organisation_ids += [row.id for row in rows]

    # Check for case
    ctable = s3db.dvr_case
    cstable = s3db.dvr_case_status
    query = (ctable.person_id == person_id) & \
            (ctable.organisation_id.belongs(organisation_ids)) & \
            (cstable.id == ctable.status_id)
    case = db(query).select(ctable.id,
                            cstable.is_closed,
                            limitby = (0, 1),
                            ).first()

    if case and case.dvr_case.id:
        # Is a client
        result.update(client_site_status(person_id,
                                         site_id,
                                         site.instance_type,
                                         case.dvr_case_status,
                                         ))
        if not result["valid"] and not result.get("error"):
            result["error"] = T("Not currently a resident")
    else:
        # May be a staff member
        result.update(staff_site_status(person_id,
                                        site_id,
                                        organisation_ids,
                                        ))
        if not result["valid"] and not result.get("error"):
            # Neither resident nor active staff member, so invalid ID
            result["error"] = T("Invalid ID")

    if result["valid"] and not result.get("error"):

        auth = current.auth
        instructions = None

        uperson_id = auth.s3_logged_in_person()
        if uperson_id == person_id:
            if not auth.s3_has_roles(("ORG_ADMIN", "SECURITY")):
                result["allowed_in"] = None
                instructions = T("Self-registration not permitted. Please register with authorized staff at the site.")
        elif not PresenceRegistration.present(site_id):
            result["allowed_in"] = result["allowed_out"] = None
            instructions = T("You must be reported as present at the site yourself in order to register the presence of others.")

        if instructions:
            result["info"] = DIV(DIV(P(instructions),
                                     _class="checkpoint-instructions",
                                     ),
                                 _class="checkpoint-advise",
                                 )
    return result

# -------------------------------------------------------------------------
def on_site_presence_event(site_id, person_id):
    """
        Update last_seen_on in case file when a site presence event
        is registered (if the person has a case file)

        Args:
            site_id: the site_id of the shelter
            person_id: the person_id to check-in
    """

    db = current.db
    s3db = current.s3db

    ctable = s3db.dvr_case
    query = (ctable.person_id == person_id) & \
            (ctable.deleted == False)
    if db(query).select(ctable.id, limitby=(0, 1)).first():
        current.s3db.dvr_update_last_seen(person_id)

# -------------------------------------------------------------------------
def cr_shelter_resource(r, tablename):

    T = current.T
    s3db = current.s3db

    table = s3db.cr_shelter

    # Configure location selector
    field = table.location_id
    field.widget = LocationSelector(levels = ("L1", "L2", "L3", "L4"),
                                    required_levels = ("L1", "L2", "L3"),
                                    show_address = True,
                                    show_postcode = True,
                                    address_required = True,
                                    postcode_required = True,
                                    show_map = False,
                                    )
    field.represent = s3db.gis_LocationRepresent(show_link = False)

    # Custom label for obsolete-flag
    field = table.obsolete
    field.label = T("Defunct")

    # Organisation is required, + cannot be created from here
    field = table.organisation_id
    requires = field.requires
    if isinstance(requires, IS_EMPTY_OR):
        field.requires = requires.other
    field.comment = None

    # Custom form
    crud_fields = ["name",
                   "organisation_id",
                   "shelter_type_id",
                   "status",
                   "location_id",
                   "capacity",
                   "blocked_capacity",
                   "population",
                   "available_capacity",
                   "comments",
                   "obsolete"
                   ]

    subheadings = {"name": T("Shelter"),
                   "location_id": T("Location"),
                   "capacity": T("Capacity"),
                   "comments": T("Other"),
                   }

    # Table configuration
    s3db.configure("cr_shelter",
                   crud_form = CustomForm(*crud_fields),
                   subheadings = subheadings,
                   realm_components = ("shelter_unit",
                                       ),
                   create_next = URL(c ="cr",
                                     f ="shelter",
                                     args = ["[id]", "shelter_unit"],
                                     ),
                   ignore_master_access = ("shelter_note",),
                   )

    # Shelter overview method
    from ..shelter import ShelterOverview
    s3db.set_method("cr_shelter",
                    method = "overview",
                    action = ShelterOverview,
                    )

    from ..presence import PresenceList
    s3db.set_method("cr_shelter",
                    method = "presence_list",
                    action = PresenceList,
                    )

# -------------------------------------------------------------------------
def cr_shelter_controller(**attr):

    T = current.T

    db = current.db
    s3db = current.s3db
    auth = current.auth

    s3 = current.response.s3
    settings = current.deployment_settings

    rtable = s3db.cr_shelter_registration
    htable = s3db.cr_shelter_registration_history
    otable = s3db.org_organisation

    is_admin = auth.s3_has_role("ADMIN")
    is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")
    is_shelter_admin = auth.s3_has_role("SHELTER_ADMIN")

    # Custom components
    s3db.add_components("cr_shelter",
                        cr_shelter_commission = "shelter_id",
                        cr_shelter_note = "shelter_id",
                        )

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        result = standard_prep(r) if callable(standard_prep) else True

        resource = r.resource

        # Restrict organisation selector
        s3db.org_restrict_for_organisations(resource)

        if is_org_group_admin and r.component_name != "shelter_note":
            # Show all records by default
            settings.ui.datatables_pagelength = -1

        if r.method == "presence":
            # Configure presence event callbacks
            resource.configure(site_presence_in = on_site_presence_event,
                               site_presence_out = on_site_presence_event,
                               site_presence_seen = on_site_presence_event,
                               site_presence_status = person_site_status,
                               )

        if not r.component:
            # Custom list fields
            list_fields = ["name",
                           "status",
                           "shelter_type_id",
                           "capacity",
                           "population",
                           "location_id$addr_street",
                           "location_id$L1",
                           "location_id$L2",
                           "location_id$L3",
                           "location_id$L4",
                           ]

            # Custom Filter Widgets
            from s3db.cr import shelter_status_opts
            filter_widgets = [TextFilter(["name",
                                          "location_id$L1",
                                          "location_id$L2",
                                          "location_id$L3",
                                          "location_id$L4",
                                          "location_id$addr_street",
                                          "comments",
                                          ],
                                         label = T("Search"),
                                         ),
                              OptionsFilter("shelter_type_id",
                                            options = get_filter_options("cr_shelter_type"),
                                            hidden = True,
                                            ),
                              OptionsFilter("status",
                                            options = shelter_status_opts,
                                            cols = 2,
                                            hidden = True,
                                            ),
                              RangeFilter("capacity",
                                          hidden = True,
                                          ),
                              RangeFilter("population",
                                          hidden = True,
                                          ),
                              ]

            from ..helpers import permitted_orgs
            organisation_ids = permitted_orgs("read", "cr_shelter")
            if len(organisation_ids) > 1:
                # User can see shelters from more than one organisation
                # => show organisation_id in data table
                list_fields.insert(0, "organisation_id")

                def org_filter_opts():
                    # Lazy options lookup for organisation_filter
                    organisations = db(otable.id.belongs(organisation_ids)).select(otable.id,
                                                                                   otable.name,
                                                                                   )
                    return {o.id: o.name for o in organisations}

                # Add organisation-filter
                filter_widgets.insert(1,
                    OptionsFilter("organisation_id",
                                  options = org_filter_opts,
                                  hidden = True,
                                  ))

            if is_admin or is_org_group_admin:
                # Show date of registration in table and add a filter for it
                registered_on = T("Registered on")
                list_fields.append((registered_on, "created_on"))
                filter_widgets.append(DateFilter("created_on",
                                                 label = registered_on,
                                                 hide_time = True,
                                                 hidden = True,
                                                 ))
            if r.representation == "json":
                # Make sure list_fields include site_id
                # - required by site_id filterOptionsS3 lookup (e.g. act/issue)
                list_fields.append("site_id")

            # Deletability
            if r.record and is_admin:
                shelter_id = r.record.id
                query = (rtable.shelter_id == shelter_id) | \
                        (rtable.last_shelter_id == shelter_id)
                row = db(query).select(rtable.id, limitby=(0, 1)).first()
                if not row:
                    query = (htable.shelter_id == shelter_id)
                    row = db(query).select(htable.id, limitby=(0, 1)).first()
                deletable = not row
            else:
                deletable = is_admin

            resource.configure(filter_widgets = filter_widgets,
                               list_fields = list_fields,
                               # Open shelter basic details in read mode
                               open_read_first = True,
                               deletable = deletable,
                               )

        elif r.component_name != "document":
            # Customise doc_document in any case (for inline-attachments)
            r.customise_resource("doc_document")

        if r.component_name == "shelter_unit":

            if is_shelter_admin:
                r.component.configure(
                    filter_widgets = [
                        TextFilter(["name", "comments"],
                                   label = T("Search"),
                                   ),
                        OptionsFilter("status",
                                      options = OrderedDict((("1", T("Available")),
                                                             ("2", T("Not allocable")),
                                                             ("3", T("Closed"))
                                                             )),
                                      default = [1, 2],
                                      cols = 3,
                                      sort = False,
                                      ),
                        ]
                    )
                settings.search.filter_manager = False
            else:
                r.component.add_filter(FS("status") != 3)

        elif r.component_name == "shelter_note":
            r.component.configure(open_read_first=True)
            current.s3db.cr_configure_shelter_note_form(r)

        elif r.component_name == "document":
            r.component.add_filter(FS("doc_id") == None)

        return result
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        # Hide side menu and rheader for presence registration
        if r.method == "presence":
            current.menu.options = None
            if isinstance(output, dict):
                output["rheader"] = ""
            return output

        # Custom view for shelter inspection
        if r.method == "inspection":
            from core import CustomController
            CustomController._view("MRCMS", "shelter_inspection.html")
            return output

        record = r.record

        if is_admin and not record and not r.component and r.method != "deduplicate":

            # Default action buttons (except delete)
            BasicCRUD.action_buttons(r, deletable =False)

            # Identify shelters which have never been occupied
            table = r.resource.table
            occupied = db(rtable.shelter_id!=None)._select(rtable.shelter_id, distinct=True)
            previous = db(rtable.last_shelter_id!=None)._select(rtable.last_shelter_id, distinct=True)
            historic = db(htable.shelter_id!=None)._select(htable.shelter_id, distinct=True)

            query = (table.id.belongs(occupied)) | \
                    (table.id.belongs(previous)) | \
                    (table.id.belongs(historic))
            rows = db(~query).select(table.id)
            unused = [str(row.id) for row in rows]

            # Delete-button for those
            DELETE = s3_str(T("Delete"))
            enabled = {"label": DELETE,
                       "url": URL(args = ["[id]", "delete"], vars=r.get_vars),
                       "_class": "delete-btn",
                       "restrict": unused,
                       }
            s3.actions.append(enabled)

            # Disabled delete-button for all others,
            # indicating that and why the action is disabled
            disabled = {"label": DELETE,
                        "_class": "action-btn",
                        "_title": s3_str(T("Shelter is or was occupied")),
                        "_disabled": "disabled",
                        "exclude": unused,
                        }
            s3.actions.append(disabled)

        # Add presence registration button, if permitted
        if record and not r.component and \
           PresenceRegistration.permitted("cr_shelter", record=record) and \
           isinstance(output, dict) and "buttons" in output:

            buttons = output["buttons"]

            # Add a "Presence Registration"-button
            presence_url = URL(c="cr", f="shelter", args=[record.id, "presence"])
            presence_btn = BasicCRUD.crud_button(T("Presence Registration"), _href=presence_url)

            delete_btn = buttons.get("delete_btn")
            buttons["delete_btn"] = TAG[""](presence_btn, delete_btn) \
                                    if delete_btn else presence_btn

        return output
    s3.postp = custom_postp

    from ..rheaders import cr_rheader
    attr = dict(attr)
    attr["rheader"] = cr_rheader

    # Activate filters on component tabs
    attr["hide_filter"] = {"shelter_unit": not is_shelter_admin,
                           "shelter_note": False,
                           }

    return attr

# -------------------------------------------------------------------------
def cr_shelter_unit_resource(r, tablename):

    T = current.T
    s3db = current.s3db

    table = s3db.cr_shelter_unit

    field = table.location_id
    field.readable = field.writable = False

    field = table.transitory
    field.label = T("Staging Area")
    field.readable = field.writable = True

    table.occupancy = s3_fieldmethod("occupancy",
                                     shelter_unit_occupancy,
                                     represent = represent_occupancy,
                                     )

    list_fields = [(T("Name"), "name"),
                   "transitory",
                   "status",
                   "capacity",
                   "population",
                   "blocked_capacity",
                   "available_capacity",
                   (T("Occupancy %"), "occupancy"),
                   ]
    s3db.configure("cr_shelter_unit",
                   list_fields = list_fields,
                   extra_fields = ("capacity", "blocked_capacity", "popuplation"),
                   )

# -------------------------------------------------------------------------
def shelter_unit_occupancy(row):
    """
        Returns the occupancy of a housing unit in %, field method

        Args:
            the shelter unit Row (capacity, blocked_capacity, popuplation)

        Returns:
            integer
    """

    if hasattr(row, "cr_shelter_unit"):
        row = row.cr_shelter_unit
    try:
        total_capacity = row.capacity
        blocked_capacity = row.blocked_capacity
        population = row.population
    except AttributeError:
        return None

    if not total_capacity:
        return None
    if blocked_capacity is None:
        blocked_capacity = 0
    if population is None:
        population = 0

    # Blocked capacity cannot exceed total capacity
    blocked_capacity = min(total_capacity, blocked_capacity)

    # Available capacity
    available = total_capacity - blocked_capacity
    if available < population:
        # Population over available capacity:
        # - ignore any blocked capacity that is actually occupied
        available = min(total_capacity, population)

    if not available:
        # A unit with no available capacity is full if, and only if,
        # it is occupied - otherwise it is (in fact) empty
        return 100 if population else 0
    else:
        # Compute occupancy rate, use floor-rounding so the rate is
        # still indicative of even small free capacity (=show 100%
        # only once it is actually reached, not by rounding)
        return (population * 100 // available)

# -------------------------------------------------------------------------
def cr_shelter_unit_controller(**attr):

    db = current.db
    s3db = current.s3db

    s3 = current.response.s3

    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        result = standard_prep(r) if callable(standard_prep) else True

        if not r.record and r.representation == "json":
            # Shelter unit selector => return only available units
            status_query = (FS("status") == 1)

            # Include current unit, if known
            person_id = str(r.get_vars.get("person"))
            if person_id.isdigit():
                rtable = s3db.cr_shelter_registration
                query = (rtable.person_id == person_id) & \
                        (rtable.deleted == False)
                reg = db(query).select(rtable.shelter_unit_id,
                                        limitby = (0, 1),
                                        orderby = ~rtable.id,
                                        ).first()
                current_unit = reg.shelter_unit_id if reg else None
            else:
                current_unit = None

            if current_unit:
                status_query |= (FS("id") == current_unit)

            r.resource.add_filter(status_query)

        return result
    s3.prep = custom_prep

    return attr

# -------------------------------------------------------------------------
def cr_shelter_registration_onaccept(form):
    """
        Onaccept of shelter registration
            - when checked-out, expire all system-generated ID cards
    """

    db = current.db
    s3db = current.s3db

    record_id = get_form_record_id(form)
    if not record_id:
        return

    table = s3db.cr_shelter_registration
    record = db(table.id == record_id).select(table.id,
                                              table.person_id,
                                              table.registration_status,
                                              limitby = (0, 1),
                                              ).first()
    if not record:
        return

    if record.registration_status == 3:
        from ..idcards import IDCard
        IDCard(record.person_id).auto_expire()

# -------------------------------------------------------------------------
def cr_shelter_registration_resource(r, tablename):

    table = current.s3db.cr_shelter_registration
    field = table.shelter_unit_id

    if r.controller == "cr":
        # Filter to available housing units
        field.requires = IS_EMPTY_OR(IS_ONE_OF(current.db, "cr_shelter_unit.id",
                                               field.represent,
                                               filterby = "status",
                                               filter_opts = (1,),
                                               orderby = "shelter_id",
                                               ))

    # Custom-callback to trigger status-dependent actions
    current.s3db.add_custom_callback("cr_shelter_registration",
                                     "onaccept",
                                     cr_shelter_registration_onaccept,
                                     )

# -------------------------------------------------------------------------
def cr_shelter_registration_controller(**attr):
    """
        Shelter Registration controller is just used
        by the Quartiermanager role.
    """

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.method == "assign":

            # TODO replace with default_case_shelter, using viewing
            from ..helpers import get_default_shelter

            # Prep runs before split into create/update (Create should never happen in Village)
            table = r.table
            shelter_id = get_default_shelter()
            if shelter_id:
                # Only 1 Shelter
                f = table.shelter_id
                f.default = shelter_id
                f.writable = False # f.readable kept as True for cr_shelter_registration_onvalidation
                f.comment = None

            # Only edit for this Person
            f = table.person_id
            f.default = r.get_vars["person_id"]
            f.writable = False
            f.comment = None
            # Registration status hidden
            f = table.registration_status
            f.readable = False
            f.writable = False
            # Check-in dates hidden
            f = table.check_in_date
            f.readable = False
            f.writable = False
            f = table.check_out_date
            f.readable = False
            f.writable = False

            # Go back to the list of residents after assigning
            current.s3db.configure("cr_shelter_registration",
                                   create_next = URL(c="dvr", f="person"),
                                   update_next = URL(c="dvr", f="person"),
                                   )

        return result
    s3.prep = custom_prep

    return attr

# -------------------------------------------------------------------------
def cr_shelter_registration_history_resource(r, tablename):

    T = current.T
    s3db = current.s3db

    list_fields = ["date",
                   (T("Status"), "status"),
                   "shelter_id",
                   (T("Registered by"), "created_by"),
                   ]

    s3db.configure(tablename,
                   list_fields = list_fields,
                   # Oldest first, to match rhist.js registrationHistory
                   orderby = "%s.date" % tablename,
                   )

# END =========================================================================
