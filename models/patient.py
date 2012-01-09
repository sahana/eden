# -*- coding: utf-8 -*-

"""
    Patient Tracking

    @author: Fran Boon
"""

if deployment_settings.has_module("patient"):

    def patient_tables():

        person_id = s3db.pr_person_id
        location_id = s3db.gis_location_id

        # ---------------------------------------------------------------------
        tablename = "patient_patient"
        table = db.define_table(tablename,
                                person_id(widget=S3AddPersonWidget(),
                                          requires=IS_ADD_PERSON_WIDGET(),
                                          label=T("Patient"),
                                          comment=None),
                                #person_id(empty=False, label = T("Patient")),
                                Field("country",
                                      label = T("Current Location Country"),
                                      requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                        lambda: gis.get_countries(key_type="code"),
                                        zero = SELECT_LOCATION)),
                                      represent = lambda code: \
                                        gis.get_country(code, key_type="code") or \
                                            UNKNOWN_OPT),
                                hospital_id(empty=False,
                                            label = T("Current Location Treating Hospital")),
                                Field("phone", requires=s3_phone_requires,
                                      label=T("Current Location Phone Number")),
                                Field("treatment_date", "date", label=T("Date of Treatment")),
                                Field("return_date", "date", label=T("Expected Return Home")),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_PATIENT = T("New Patient")
        LIST_PATIENTS = T("List Patients")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PATIENT,
            title_display = T("Patient Details"),
            title_list = LIST_PATIENTS,
            title_update = T("Edit Patient"),
            title_search = T("Search Patients"),
            subtitle_create = T("Add New Patient"),
            subtitle_list = T("Patients"),
            label_list_button = LIST_PATIENTS,
            label_create_button = ADD_PATIENT,
            label_delete_button = T("Delete Patient"),
            msg_record_created = T("Patient added"),
            msg_record_modified = T("Patient updated"),
            msg_record_deleted = T("Patient deleted"),
            msg_list_empty = T("No Patients currently registered"))

        def patient_represent(id):
            if isinstance(id, Row):
                # Do not repeat the lookup if already done by IS_ONE_OF or RHeader
                patient = id
            else:
                table = db.patient_patient
                query = (table.id == id)
                patient = db(query).select(table.person_id,
                                           limitby = (0, 1)).first()
            if patient:
                represent = via.fullname(patient.person_id)
            else:
                represent = "-"

            return represent

        # Reusable Field for Component Link
        patient_id = S3ReusableField("patient_id", db.patient_patient,
                                     requires = IS_ONE_OF(db,
                                                          "patient_patient.id",
                                                          patient_represent),
                                     represent = patient_represent,
                                     ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        tablename = "patient_relative"
        table = db.define_table(tablename,
                                patient_id(readable=False, writable=False),
                                #person_id(label = T("Accompanying Relative")),
                                person_id(widget=S3AddPersonWidget(),
                                          requires=IS_ADD_PERSON_WIDGET(),
                                          label=T("Accompanying Relative"),
                                          comment=None),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_RELATIVE = T("New Relative")
        LIST_RELATIVES = T("List Relatives")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_RELATIVE,
            title_display = T("Relative Details"),
            title_list = LIST_RELATIVES,
            title_update = T("Edit Relative"),
            title_search = T("Search Relatives"),
            subtitle_create = T("Add New Relative"),
            subtitle_list = T("Relatives"),
            label_list_button = LIST_RELATIVES,
            label_create_button = ADD_RELATIVE,
            label_delete_button = T("Delete Relative"),
            msg_record_created = T("Relative added"),
            msg_record_modified = T("Relative updated"),
            msg_record_deleted = T("Relative deleted"),
            msg_list_empty = T("No Relatives currently registered"))

        # Home as Component of Patients
        s3mgr.model.add_component(table,
                                  patient_patient=dict(joinby="patient_id",
                                                       multiple=False))

        # ---------------------------------------------------------------------
        # @ToDo: Default the Home Phone Number from the Person, if available
        # @ToDo: Onvalidation to set the Relative's Contact
        tablename = "patient_home"
        table = db.define_table(tablename,
                                patient_id(readable=False, writable=False),
                                person_id(widget=S3AddPersonWidget(),
                                          requires=IS_ADD_PERSON_WIDGET(),
                                          label=T("Home Relative"),
                                          comment=None),
                                #person_id(label = T("Home Relative")),
                                location_id(label=T("Home City"),
                                            widget = S3LocationAutocompleteWidget(level="L2"),
                                            requires = IS_LOCATION(level="L2")),
                                Field("phone",
                                      requires=IS_NULL_OR(s3_phone_requires),
                                      label=T("Home Phone Number")),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_HOME = T("New Home")
        LIST_HOMES = T("List Homes")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_HOME,
            title_display = T("Home Details"),
            title_list = LIST_HOMES,
            title_update = T("Edit Home"),
            title_search = T("Search Homes"),
            subtitle_create = T("Add New Home"),
            subtitle_list = T("Homes"),
            label_list_button = LIST_HOMES,
            label_create_button = ADD_HOME,
            label_delete_button = T("Delete Home"),
            msg_record_created = T("Home added"),
            msg_record_modified = T("Home updated"),
            msg_record_deleted = T("Home deleted"),
            msg_list_empty = T("No Homes currently registered"))

        # Home as Component of Patients
        s3mgr.model.add_component(table,
                                  patient_patient=dict(joinby="patient_id",
                                                       multiple=False))

    # Provide a handle to this load function
    s3mgr.loader(patient_tables,
                 "patient_patient")

# END =========================================================================

