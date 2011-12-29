# -*- coding: utf-8 -*-

"""
   Volunteer Module
   - A 'My Sahana' view of an individual Volunteer's Data, Tasks, etc
   (Ability for Anonymous users to sign-up as a Volunteer?)
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Options Menu (available in all Functions)
s3_menu(module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    # Default to the Personal profile
    return person()

# -----------------------------------------------------------------------------
# People
# -----------------------------------------------------------------------------
def person():
    """
        Person Controller
        - allows a person to view/update the details held about them
    """

    resourcename = "person"

    # Load Model
    s3mgr.load("pr_address")
    s3mgr.load("hrm_skill")

    s3.crud.submit_button = T("Next")

    s3mgr.model.add_component("hrm_certification",
                              pr_person="person_id")

    s3mgr.model.add_component("hrm_competency",
                              pr_person="person_id")

    s3mgr.model.add_component("hrm_credential",
                              pr_person="person_id")

    s3mgr.model.add_component("hrm_training",
                              pr_person="person_id")

    s3mgr.model.add_component("hrm_experience",
                              pr_person="person_id")

    # Q: Are volunteers assigned to a specific organisation outside of a specific Event?
    # Yes, some are: CERT
    s3mgr.model.add_component("hrm_human_resource",
                              pr_person="person_id")

    # Configure human resource table
    # - for Positions
    tablename = "hrm_human_resource"
    table = db[tablename]
    table.type.readable = True
    table.type.writable = False
    table.location_id.writable = False # Populated from pr_address
    table.location_id.readable = False
    s3mgr.configure(tablename,
                    list_fields=["id",
                                 "organisation_id",
                                 "job_title",
                                 "status"])

    # Configure person table
    # - hide fields
    tablename = "pr_person"
    table = db[tablename]
    table.pe_label.readable = False
    table.pe_label.writable = False
    table.missing.readable = False
    table.missing.writable = False
    table.age_group.readable = False
    table.age_group.writable = False
    s3mgr.configure(tablename,
                    # Wizard: Move to next Tab after Save
                    update_next = URL(args=["[id]", "address"]),
                    deletable=False)

    # Configure for personal mode
    s3.crud_strings[tablename].update(
        title_display = T("Personal Profile"),
        title_update = T("Personal Profile"))
    # People can view their own HR data, but not edit it
    db.hrm_human_resource.organisation_id.readable = True
    s3mgr.configure("hrm_human_resource",
                    insertable = False,
                    editable = False,
                    deletable = False)
    s3mgr.configure("hrm_certification",
                    insertable = True,
                    editable = True,
                    deletable = True)
    s3mgr.configure("hrm_credential",
                    insertable = False,
                    editable = False,
                    deletable = False)
    s3mgr.configure("hrm_competency",
                    insertable = True,  # Can add unconfirmed
                    editable = False,
                    deletable = False)
    s3mgr.configure("hrm_training",    # Can add but not provide grade
                    insertable = True,
                    editable = False,
                    deletable = False)
    s3mgr.configure("hrm_experience",
                    insertable = False,
                    editable = False,
                    deletable = False)
    s3mgr.configure("pr_group_membership",
                    insertable = False,
                    editable = False,
                    deletable = False)
    tabs = [(T("Person Details"), None),
            (T("Addresses"), "address"),
            (T("Certificates"), "certification"),
            (T("Contact Information"), "contact"),
            #(T("Skills"), "competency"),
            #(T("Credentials"), "credential"),
            #(T("Trainings"), "training"),
            #(T("Mission Record"), "experience"),
            #(T("Positions"), "human_resource"),
            #(T("Teams"), "group_membership")
           ]

    # Prepare CRUD
    def prep(r):
        if r.interactive:
            resource = r.resource
            r.resource.build_query(id=s3_logged_in_person())
            if resource.count() == 1:
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
            if r.component:
                if r.component.name == "address":
                    s3mgr.configure("pr_address",
                                    create_next = URL(args=[str(r.id), "certification"]))
                elif r.component.name == "certification":
                    r.component.table.certificate_id.comment = None
                    r.component.table.organisation_id.readable = False
                    s3mgr.configure("hrm_certification",
                                     create_next = URL(args=[str(r.id), "contact"]))
                #elif r.component.name == "contact":
                #    s3mgr.configure("pr_contact",
                #                   create_next = URL(#                                      args=[str(r.id), ""]))

            return True
        else:
            # This controller is only for interactive use
            redirect(URL(f='default', c="index"))
    response.s3.prep = prep

    rheader = lambda r, tabs=tabs: vol_rheader(r, tabs)

    output = s3_rest_controller("pr", resourcename,
                                native=False,
                                rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def vol_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None
    rheader_tabs = s3_rheader_tabs(r, tabs)

    if r.representation == "html":

        if r.name == "person":
            # Person Controller
            person = r.record
            if person:
                rheader = DIV(TABLE(

                    TR(TH("%s: " % T("Name")),
                       s3_fullname(person),
                       TH(""),
                       ""),

                    TR(TH("%s: " % T("Date of Birth")),
                       "%s" % (s3_date_represent(person.date_of_birth) or T("unknown")),
                       TH(""),
                       ""),

                    ), rheader_tabs)

    return rheader

# -----------------------------------------------------------------------------
# Tasks
# -----------------------------------------------------------------------------
def task():

    """ Allow a volunteer to View the details of their own tasks """

    tablename = "project_task"
    s3mgr.load(tablename)
    table = db[tablename]

    my_person_id = s3_logged_in_person()

    if not my_person_id:
        session.error = T("No person record found for current user.")
        redirect(URL(f="index"))

    table.person_id.default = my_person_id

    response.s3.filter = (table.person_id == my_person_id)

    s3.crud_strings[tablename].title_list = T("My Tasks")
    s3.crud_strings[tablename].subtitle_list = T("Task List")
    s3.crud_strings[tablename].msg_list_empty = T("No tasks currently assigned")

    s3mgr.configure(tablename,
                    insertable = False,
                    editable = False,
                    deletable = False)

    return s3_rest_controller("project", "task")

# END =========================================================================

