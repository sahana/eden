# -*- coding: utf-8 -*-

"""
    HMS Hospital Status Assessment and Request Management System
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def s3_menu_postp():
    # @todo: rewrite this for new framework
    if len(request.args) > 0 and request.args[0].isdigit():
        newreq = dict(from_record="hms_hospital.%s" % request.args[0],
                      from_fields="hospital_id$id")
        #selreq = {"req.hospital_id":request.args[0]}
    else:
        newreq = dict()
    selreq = {"req.hospital_id__ne":"NONE"}
    menu_selected = []
    hospital_id = s3mgr.get_session("hms", "hospital")
    if hospital_id:
        hospital = s3db.hms_hospital
        query = (hospital.id == hospital_id)
        record = db(query).select(hospital.id,
                                  hospital.name,
                                  limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Hospital"), name), False,
                                 URL(f="hospital",
                                     args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

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
        # Just redirect to the Hospitals Map
        redirect(URL(f="hospital", args=["map"]))

    # tbc
    report = ""

    response.view = "index.html"
    return dict(item=item, report=report)

# -----------------------------------------------------------------------------
def ltc():
    """ Filtered REST Controller """

    s3.filter = (s3db.hms_hospital.facility_type == 31)
    return hospital()

# -----------------------------------------------------------------------------
def marker_fn(record):
    """
        Function to decide which Marker to use for Hospital Map
        @ToDo: Legend
        @ToDo: Move to Templates
        @ToDo: Use Symbology
    """

    stable = db.hms_status
    status = db(stable.hospital_id == record.id).select(stable.facility_status,
                                                        limitby=(0, 1)
                                                        ).first()
    if record.facility_type == 31:
        marker = "special_needs"
    else:
        marker = "hospital"
    if status:
        if status.facility_status == 1:
            # Normal
            marker = "%s_green" % marker
        elif status.facility_status in (3, 4):
            # Evacuating or Closed
            marker = "%s_red" % marker
        elif status.facility_status == 2:
            # Compromised
            marker = "%s_yellow" % marker

    mtable = db.gis_marker
    marker = db(mtable.name == marker).select(mtable.image,
                                              mtable.height,
                                              mtable.width,
                                              cache=s3db.cache,
                                              limitby=(0, 1)).first()
    return marker

# -----------------------------------------------------------------------------
def hospital():
    """ Main REST controller for hospital data """

    table = s3db.hms_hospital

    # Load Models to add tabs
    if settings.has_module("inv"):
        s3db.table("inv_inv_item")
    elif settings.has_module("req"):
        # (gets loaded by Inv if available)
        s3db.table("req_req")

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if r.component:
                if r.component.name == "inv_item" or \
                   r.component.name == "recv" or \
                   r.component.name == "send":
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                elif r.component.name == "human_resource":
                    # Filter out people which are already staff for this hospital
                    s3base.s3_filter_staff(r)
                    # Make it clear that this is for adding new staff, not assigning existing
                    s3.crud_strings.hrm_human_resource.label_create_button = T("Add New Staff Member")
                    # Cascade the organisation_id from the hospital to the staff
                    field = s3db.hrm_human_resource.organisation_id
                    field.default = r.record.organisation_id
                    field.writable = False

                elif r.component.name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        s3db.req_create_form_mods()

                elif r.component.name == "status":
                    table = db.hms_status
                    table.facility_status.comment = DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Facility Status"),
                                                                          T("Status of the facility.")))
                    table.facility_operations.comment = DIV(_class="tooltip",
                                                            _title="%s|%s" % (T("Facility Operations"),
                                                                              T("Overall status of the facility operations.")))
                    table.clinical_status.comment = DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Clinical Status"),
                                                                          T("Status of the clinical departments.")))
                    table.clinical_operations.comment = DIV(_class="tooltip",
                                                            _title="%s|%s" % (T("Clinical Operations"),
                                                                              T("Overall status of the clinical operations.")))
                    table.ems_status.comment = DIV(_class="tooltip",
                                                   _title="%s|%s" % (T("Emergency Medical Services"),
                                                                     T("Status of operations/availability of emergency medical services at this facility.")))
                    table.ems_reason.comment = DIV(_class="tooltip",
                                                   _title="%s|%s" % (T("EMS Status Reasons"),
                                                                     T("Report the contributing factors for the current EMS status.")))
                    table.or_status.comment = DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("OR Status"),
                                                                    T("Status of the operating rooms of this facility.")))
                    table.or_reason.comment = DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("OR Status Reason"),
                                                                    T("Report the contributing factors for the current OR status.")))
                    table.morgue_status.comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Morgue Status"),
                                                                        T("Status of morgue capacity.")))
                    table.morgue_units.comment = DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Morgue Units Available"),
                                                                       T("Number of vacant/available units to which victims can be transported immediately.")))
                    table.security_status.comment = DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Security Status"),
                                                                          T("Status of security procedures/access restrictions for the facility.")))
                    table.staffing.comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Staffing Level"),
                                                                   T("Current staffing level at the facility.")))
                    table.access_status.comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Road Conditions"),
                                                                        T("Describe the condition of the roads from/to the facility.")))

                elif r.component.name == "bed_capacity":
                    table = db.hms_bed_capacity
                    table.bed_type.comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Bed Type"),
                                                                   T("Specify the bed type of this unit.")))
                    table.beds_baseline.comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Baseline Number of Beds"),
                                                                        T("Baseline number of beds of that type in this unit.")))
                    table.beds_available.comment = DIV(_class="tooltip",
                                                       _title="%s|%s" % (T("Available Beds"),
                                                                         T("Number of available/vacant beds of that type in this unit at the time of reporting.")))
                    table.beds_add24.comment = DIV(_class="tooltip",
                                                   _title="%s|%s" % (T("Additional Beds / 24hrs"),
                                                                     T("Number of additional beds of that type expected to become available in this unit within the next 24 hours.")))
                elif r.component.name == "activity":
                    table = db.hms_activity
                    table.date.comment = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Date & Time"),
                                                               T("Date and time this report relates to.")))
                    table.patients.comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Patients"),
                                                                   T("Number of in-patients at the time of reporting.")))
                    table.admissions24.comment = DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Admissions/24hrs"),
                                                                       T("Number of newly admitted patients during the past 24 hours.")))

                    table.discharges24.comment = DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Discharges/24hrs"),
                                                                       T("Number of discharged patients during the past 24 hours.")))
                    table.deaths24.comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Deaths/24hrs"),
                                                                   T("Number of deaths during the past 24 hours.")))

                elif r.component.name == "contact":
                    table = db.hms_contact
                    table.title.comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Title"),
                                                                T("The Role this person plays within this hospital.")))

                elif r.component.name == "image":
                    table = s3db.doc_image
                    table.location_id.readable = table.location_id.writable = False
                    table.organisation_id.readable = table.organisation_id.writable = False
                    table.person_id.readable = table.person_id.writable = False

                elif r.component.name == "ctc":
                    table = db.hms_ctc
                    table.ctc.comment = DIV(_class="tooltip",
                                            _title="%s|%s" % (T("Cholera Treatment Center"),
                                                              T("Does this facility provide a cholera treatment center?")))
                    table.number_of_patients.comment = DIV(_class="tooltip",
                                                           _title="%s|%s" % (T("Current number of patients"),
                                                                             T("How many patients with the disease are currently hospitalized at this facility?")))
                    table.cases_24.comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("New cases in the past 24h"),
                                                                   T("How many new cases have been admitted to this facility in the past 24h?")))
                    table.deaths_24.comment = DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("Deaths in the past 24h"),
                                                                    T("How many of the patients with the disease died in the past 24h at this facility?")))
                    table.icaths_available.comment = DIV(_class="tooltip",
                                                         _title="%s|%s" % (T("Infusion catheters available"),
                                                                           T("Specify the number of available sets")))

                    table.icaths_needed_24.comment = DIV(_class="tooltip",
                                                         _title="%s|%s" % (T("Infusion catheters need per 24h"),
                                                                           T("Specify the number of sets needed per 24h")))

                    table.infusions_available.comment = DIV(_class="tooltip",
                                                            _title="%s|%s" % (T("Infusions available"),
                                                                              T("Specify the number of available units (litres) of Ringer-Lactate or equivalent solutions")))
                    table.infusions_needed_24.comment = DIV(_class="tooltip",
                                                            _title="%s|%s" % (T("Infusions needed per 24h"),
                                                                              T("Specify the number of units (litres) of Ringer-Lactate or equivalent solutions needed per 24h")))
                    table.antibiotics_available.comment = DIV(_class="tooltip",
                                                              _title="%s|%s" % (T("Antibiotics available"),
                                                                                T("Specify the number of available units (adult doses)")))
                    table.antibiotics_needed_24.comment = DIV(_class="tooltip",
                                                              _title="%s|%s" % (T("Antibiotics needed per 24h"),
                                                                                T("Specify the number of units (adult doses) needed per 24h")))
                    table.problem_types.comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Current problems, categories"),
                                                                        T("Select all that apply")))
                    table.problem_details.comment = DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Current problems, details"),
                                                                          T("Please specify any problems and obstacles with the proper handling of the disease, in detail (in numbers, where appropriate). You may also add suggestions the situation could be improved.")))
            else:
                table = r.table
                if r.id:
                    table.obsolete.readable = table.obsolete.writable = True

                elif r.method == "map":
                    # Tell the client to request per-feature markers
                    s3db.configure("hms_hospital", marker_fn=marker_fn)

                s3.formats["have"] = r.url() # .have added by JS
                # Add comments
                table.gov_uuid.comment = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Government UID"),
                                                               T("The Unique Identifier (UUID) as assigned to this facility by the government.")))
                table.total_beds.comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Total Beds"),
                                                                 T("Total number of beds in this facility. Automatically updated from daily reports.")))
                table.available_beds.comment = DIV(_class="tooltip",
                                                   _title="%s|%s" % (T("Available Beds"),
                                                                     T("Number of vacant/available beds in this facility. Automatically updated from daily reports.")))

        elif r.representation == "aadata":
            pass
            # Hide the Implied fields here too to make columns match
            #db.rms_req.shelter_id.readable = False
            #db.rms_req.organisation_id.readable = False

        elif r.representation == "plain":
            # Duplicates info in the other fields
            r.table.location_id.readable = False

        elif r.representation == "geojson":
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker
            stable = s3db.hms_status
            s3db.configure("hms_hospital", marker_fn=marker_fn)

        return True
    s3.prep = prep

    output = s3_rest_controller("hms", "hospital",
                                rheader=s3db.hms_hospital_rheader)
    return output

# -----------------------------------------------------------------------------
def incoming():
    """ Incoming Shipments """

    return inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    return s3db.req_match()

# END =========================================================================

