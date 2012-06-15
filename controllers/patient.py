# -*- coding: utf-8 -*-

"""
    Patient Tracking
"""

module = request.controller

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

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
    response.s3.prep = prep

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def patient():
    """ RESTful CRUD controller """

    resourcename = request.function
    tablename = "patient_patient"

    # Load Models
    s3mgr.load("patient_patient")

    # Search method
    patient_search = s3base.S3Search(
        simple = s3base.S3SearchSimpleWidget(
            name="patient_search_simple",
            label = T("Search"),
            comment=T("To search for a patient, enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all patients."),
            field = [ "person_id$first_name",
                      "person_id$middle_name",
                      "person_id$last_name",
                      "person_id$local_name"]),
        advanced = (s3base.S3SearchSimpleWidget(
                    name="patient_search_simple",
                    label = T("Search"),
                    comment=T("To search for a patient, enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all patients."),
                    field = [ "person_id$first_name",
                              "person_id$middle_name",
                              "person_id$last_name",
                              "person_id$local_name"]),
                    s3base.S3SearchOptionsWidget(
                        name = "patient_search_country",
                        label = T("Country"),
                        field = "country",
                        cols = 2
                    ),
                    s3base.S3SearchOptionsWidget(
                        name = "patient_search_hospital",
                        label = T("Hospital"),
                        field = "hospital_id",
                        cols = 2
                    ),
        )
    )


    s3mgr.configure(tablename,
                    search_method=patient_search,
                    create_next = URL(args=["[id]", "relative"]))
    # Pre-process
    def prep(r):
        if r.id:
            s3mgr.configure("patient_relative",
                            create_next = URL(args=[str(r.id), "home"]))
        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):
        # No Delete-button in list view
        s3_action_buttons(r, deletable=False)
        return output
    response.s3.postp = postp

    tabs = [(T("Basic Details"), None),
            (T("Accompanying Relative"), "relative"),
            (T("Home"), "home")]
    rheader = lambda r: patient_rheader(r, tabs=tabs)
    output = s3_rest_controller(module, resourcename, rheader=rheader)

    return output

# -----------------------------------------------------------------------------
def patient_rheader(r, tabs=[]):
    """ Resource Page Header """

    if r.representation == "html":

        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        table = db.patient_patient

        rheader_tabs = s3_rheader_tabs(r, tabs)

        patient = r.record
        if patient.person_id:
            name = s3_fullname(patient.person_id)
        else:
            name = None

        if patient.country:
            country = table.country.represent(patient.country)
        else:
            country = None

        if patient.hospital_id:
            hospital = table.hospital_id.represent(patient.hospital_id)
        else:
            hospital = None

        rheader = DIV(TABLE(
            TR(
                TH("%s: " % T("Patient")),
                name,
                TH("%s: " % T("Country")),
                country),
            TR(
                TH(),
                TH(),
                TH("%s: " % T("Hospital")),
                hospital,
                )
        ), rheader_tabs)

        return rheader

    return None

# END =========================================================================

