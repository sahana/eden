# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers

    @ToDo Search shelters by type, services, location, available space
    @ToDo Tie in assessments from RAT and requests from RMS.
    @ToDo Associate persons with shelters (via presence loc == shelter loc?)
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# S3 framework functions
# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# =============================================================================
def shelter_type():
    """
        RESTful CRUD controller
        List / add shelter types (e.g. NGO-operated, Government evacuation center,
        School, Hospital -- see Agasti opt_camp_type.)
    """

    output = s3_rest_controller(rheader=s3db.cr_shelter_rheader)
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

    """ RESTful CRUD controller

    >>> resource="shelter"
    >>> from applications.sahana.modules.s3_test import WSGI_Test
    >>> test=WSGI_Test(db)
    >>> "200 OK" in test.getPage("/sahana/%s/%s" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody("List Shelters")
    >>> "200 OK" in test.getPage("/sahana/%s/%s/create" % (module,resource))    #doctest: +SKIP
    True
    >>> test.assertHeader("Content-Type", "text/html")                          #doctest: +SKIP
    >>> test.assertInBody("Add Shelter")                                        #doctest: +SKIP
    >>> "200 OK" in test.getPage("/sahana/%s/%s?format=json" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody("[")
    >>> "200 OK" in test.getPage("/sahana/%s/%s?format=csv" % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/csv")

    """

    tablename = "cr_shelter"
    table = s3db[tablename]

    field = s3db.pr_presence.shelter_id
    field.requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter.id",
                                          "%(name)s",
                                          sort=True))
    field.represent = lambda id: \
        (id and [db.cr_shelter[id].name] or ["None"])[0]
    field.ondelete = "RESTRICT"
    if settings.get_ui_camp():
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

    # Make pr_presence.pe_id visible:
    pe_id = s3db.pr_presence.pe_id
    pe_id.readable = True
    pe_id.writable = True

    # Usually, the pe_id field is an invisible foreign key, therefore it
    # has no default representation/requirements => need to add this here:
    pe_id.label = T("Person/Group")
    pe_id.represent = s3db.pr_pentity_represent
    pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                               s3.pr_pentity_represent,
                               filterby="instance_type",
                               orderby="instance_type",
                               filter_opts=("pr_person",
                                            "pr_group"))

    s3db.configure("pr_presence",
                    # presence not deletable in this view! (need to register a check-out
                    # for the same person instead):
                    deletable=False,
                    list_fields=["id",
                                 "pe_id",
                                 "datetime",
                                 "presence_condition",
                                 "proc_desc"
                                ])

    # Access from Shelters
    s3db.add_component("pr_presence",
                              cr_shelter="shelter_id")

    s3db.configure(tablename,
                    # Go to People check-in for this shelter after creation
                    create_next = URL(c="cr", f="shelter",
                                      args=["[id]", "presence"]))

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.component and r.component.name == "presence":
            r.resource.add_filter(s3db.pr_presence.closed == False)

        if r.interactive:
            if r.id:
                s3db.cr_shelter.obsolete.readable = s3db.cr_shelter.obsolete.writable = True
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
                    if deployment_settings.get_ui_camp():
                        REGISTER_LABEL = T("Register Person into this Camp")
                        EMPTY_LIST = T("No People currently registered in this camp")
                    else:
                        REGISTER_LABEL = T("Register Person into this Shelter")
                        EMPTY_LIST = T("No People currently registered in this shelter")
                    # Hide the Implied fields
                    db.pr_presence.location_id.writable = False
                    db.pr_presence.location_id.default = r.record.location_id
                    db.pr_presence.location_id.comment = ""
                    db.pr_presence.proc_desc.readable = db.pr_presence.proc_desc.writable = False
                    # AT: Add Person
                    s3db.table("pr_group", None)
                    add_group_label = s3base.S3CRUD.crud_string("pr_group", "label_create_button")
                    db.pr_presence.pe_id.comment = \
                        DIV(s3db.pr_person_comment(T("Add Person"), REGISTER_LABEL, child="pe_id"),
                            S3AddResourceLink(c="pr",
                                              f="group",
                                              title=add_group_label,
                                              tooltip=T("Create a group entry in the registry."))
                        )
                    db.pr_presence.pe_id.widget = S3AutocompleteWidget("pr", "pentity")
                    # Set defaults
                    db.pr_presence.datetime.default = request.utcnow
                    db.pr_presence.observer.default = s3_logged_in_person()
                    popts = s3db.pr_presence_opts
                    pcnds = s3db.pr_presence_conditions
                    cr_shelter_presence_opts = {
                        popts.CHECK_IN: pcnds[popts.CHECK_IN],
                        popts.CHECK_OUT: pcnds[popts.CHECK_OUT]
                    }
                    db.pr_presence.presence_condition.requires = IS_IN_SET(
                        cr_shelter_presence_opts, zero=None)
                    db.pr_presence.presence_condition.default = popts.CHECK_IN
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

# =============================================================================
# This code provides urls of the form:
# http://.../eden/cr/call/<service>/rpc/<method>/<id>
# e.g.:
# http://.../eden/cr/call/jsonrpc/rpc/list/2

# It is not currently in use but left in as an example, and because it may
# be used in future for interoperating with or transferring data from Agasti
# which uses xml-rpc. See:
# http://www.web2py.com/examples/default/tools#services
# http://groups.google.com/group/web2py/browse_thread/thread/53086d5f89ac3ae2

#from gluon.tools import Service
#service = Service()

# def call():
    # "Call an XMLRPC, JSONRPC or RSS service"
    # return service()

# @service.jsonrpc
# @service.xmlrpc
# @service.amfrpc
# def rpc(method, id=0):
    # if method == "list":
        # return db().select(db.cr_shelter.ALL).as_list()
    # if method == "read":
        # return db(db.cr_shelter.id == id).select().as_list()
    # if method == "delete":
        # status=db(db.cr_shelter.id == id).delete()
        # if status:
            # return "Success - record %d deleted!" % id
        # else:
            # return "Failed - no record %d!" % id
    # else:
        # return "Method not implemented!"

# @service.xmlrpc
# def create(name):
    ##Need to do validation manually!
    # id = db.cr_shelter.insert(name=name)
    # return id

# @service.xmlrpc
# def update(id, name):
    ##Need to do validation manually!
    # status = db(db.cr_shelter.id == id).update(name=name)
    ##@todo: audit!
    # if status:
        # return "Success - record %d updated!" % id
    # else:
        # return "Failed - no record %d!" % id

# END =========================================================================
