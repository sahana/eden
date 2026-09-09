"""
    Emergency Medical Journal

    Copyright: 2024 (c) Sahana Software Foundation

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("MedUnitModel",
           "MedPatientModel",
           "MedVitalsModel",
           "MedTreatmentModel",
           "MedStatusModel",
           "MedParameterModel",
           "MedAnamnesisModel",
           "MedEpicrisisModel",
           "MedMedicationModel",
           "MedVaccinationModel",
           "med_PatientListLayout",
           "med_UnitRepresent",
           "med_DocEntityRepresent",
           "med_get_current_patient_id",
           "med_configure_unit_id",
           "med_rheader",
           )

import datetime
import re

from gluon import *
from gluon.storage import Storage
from gluon.validators import Validator, ValidationError

from ..core import *

BP = r"^\s*([1-3]{1}\d{2}|[2-9]{1}\d)\s*(?:[/]{1}\s*([1]{1}\d{2}|[2-9]{1}\d)){0,1}\s*$"
NV = r"^([+-]?)([0-9]{1,3}(?:(?:([\,\.])[0-9]{3}(?=[\,\.])(?:\3[0-9]{3})*(?!\3))|(?:[0-9]*))?)(?:[\,\.]([0-9]*))?$"

# =============================================================================
class MedUnitModel(DataModel):
    """ Medical Unit & Treatment Areas Model """

    names = ("med_unit",
             "med_unit_id",
             "med_area",
             "med_area_id",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure
        super_link = self.super_link

        # ---------------------------------------------------------------------
        tablename = "med_unit"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     self.org_organisation_id(empty = False),
                     self.org_site_id(),
                     Field("name", length=64,
                           requires = IS_NOT_EMPTY(),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     Field("obsolete", "boolean",
                           label = T("Obsolete"),
                           default = False,
                           represent = BooleanRepresent(labels = False,
                                                        # Reverse icons semantics
                                                        icons = (BooleanRepresent.NEG,
                                                                 BooleanRepresent.POS,
                                                                 ),
                                                        flag = True,
                                                        ),
                           ),
                     )

        # Components
        self.add_components(tablename,
                            med_area = "unit_id",
                            med_patient = {"joinby": "unit_id",
                                           "filterby": {"status": ("ARRIVED", "TREATMENT")},
                                           },
                            )

        # Table configuration
        configure(tablename,
                  onvalidation = self.unit_onvalidation,
                  onaccept = self.unit_onaccept,
                  super_entity = ("pr_pentity",),
                  )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Medical Unit"),
            title_display = T("Medical Unit"),
            title_list = T("Medical Units"),
            title_update = T("Edit Medical Unit"),
            label_list_button = T("List Medical Units"),
            label_delete_button = T("Delete Medical Unit"),
            msg_record_created = T("Medical Unit added"),
            msg_record_modified = T("Medical Unit updated"),
            msg_record_deleted = T("Medical Unit deleted"),
            msg_list_empty = T("No Medical Units currently registered"),
            )

        # Foreign key template
        represent = med_UnitRepresent()
        unit_id = FieldTemplate("unit_id", "reference %s" % tablename,
                                label = T("Unit"),
                                ondelete = "CASCADE",
                                represent = represent,
                                requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          filterby = "obsolete",
                                                          filter_opts = (False,),
                                                          )),
                                )

        # ---------------------------------------------------------------------
        # Area functions
        #
        area_functions = (("A", T("Arrival / Staging")),
                          ("T", T("Examination / Treatment")),
                          ("O", T("Observation")),
                          ("X", T("Transfer")),
                          )

        # ---------------------------------------------------------------------
        # Area status
        #
        area_status = (("O", T("Operational")),
                       ("Q", T("Quarantine")),
                       ("M", T("Maintenance")),
                       ("X", T("Closed")),
                       )

        area_status_represent = S3PriorityRepresent(area_status,
                                                    {"O": "green",
                                                     "Q": "amber",
                                                     "M": "red",
                                                     "X": "black",
                                                     }).represent

        # ---------------------------------------------------------------------
        # Areas (rooms)
        #
        tablename = "med_area"
        define_table(tablename,
                     unit_id(empty=False),
                     Field("name", length=64,
                           requires = IS_NOT_EMPTY(),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     Field("purpose",
                           label = T("Purpose"),
                           default = "T",
                           requires = IS_IN_SET(area_functions,
                                                zero = None,
                                                sort = False,
                                                ),
                           represent = represent_option(dict(area_functions)),
                           ),
                     Field("capacity", "integer",
                           label = T("Capacity"),
                           default = 1,
                           requires = IS_INT_IN_RANGE(minimum=1),
                           ),
                     Field("status",
                           label = T("Status"),
                           default = "O",
                           requires = IS_IN_SET(area_status,
                                                zero = None,
                                                sort = False,
                                                ),
                           represent = area_status_represent,
                           ),
                     CommentsField(),
                     )

        # Table configuration
        configure(tablename,
                  onvalidation = self.area_onvalidation,
                  )

        # CRUD strings
        area_label = settings.get_med_area_label()
        if area_label == "room":
            crud_strings[tablename] = Storage(
                label_create = T("Add Room"),
                title_display = T("Room"),
                title_list = T("Rooms"),
                title_update = T("Edit Room"),
                label_list_button = T("List Rooms"),
                label_delete_button = T("Delete Room"),
                msg_record_created = T("Room added"),
                msg_record_modified = T("Room updated"),
                msg_record_deleted = T("Room deleted"),
                msg_list_empty = T("No Rooms currently registered"),
                )
        else:
            crud_strings[tablename] = Storage(
                label_create = T("Create Treatment Area"),
                title_display = T("Treatment Area"),
                title_list = T("Treatment Areas"),
                title_update = T("Edit Treatment Area"),
                label_list_button = T("List Treatment Areas"),
                label_delete_button = T("Delete Treatment Area"),
                msg_record_created = T("Treatment Area added"),
                msg_record_modified = T("Treatment Area updated"),
                msg_record_deleted = T("Treatment Area deleted"),
                msg_list_empty = T("No Treatment Areas currently registered"),
                )

        # Foreign key template
        represent = S3Represent(lookup=tablename)
        area_id = FieldTemplate("area_id", "reference %s" % tablename,
                                label = T("Place##placement"),
                                ondelete = "SET NULL",
                                represent = represent,
                                requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          not_filterby = "status",
                                                          not_filter_opts = ("M", "X"),
                                                          )),
                                )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"med_unit_id": unit_id,
                "med_area_id": area_id,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        dummy = FieldTemplate.dummy

        return {"med_unit_id": dummy("unit_id"),
                "med_area_id": dummy("area_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def unit_onvalidation(form):
        """
            Form validation for medical units
            - name must be unique within the organisation
        """

        # Get form record id
        record_id = get_form_record_id(form)

        # Get form record data
        table = current.s3db.med_unit
        data = get_form_record_data(form, table, ["organisation_id", "name"])

        name = data.get("name")
        if name:
            # Name must be unique within the organisation
            query = (table.name == name)
            if record_id:
                query &= (table.id != record_id)
            query &= (table.organisation_id == data.get("organisation_id")) & \
                     (table.deleted == False)
            duplicate = current.db(query).select(table.id, limitby=(0, 1)).first()
            if duplicate:
                form.errors.name = current.T("A unit with that name already exists")

    # -------------------------------------------------------------------------
    @staticmethod
    def unit_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("med_unit", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def area_onvalidation(form):
        """
            Form validation for treatment areas
            - name must be unique within the unit
        """

        # Get form record id
        record_id = get_form_record_id(form)

        # Get form record data
        table = current.s3db.med_area
        data = get_form_record_data(form, table, ["unit_id", "name"])

        name = data.get("name")
        if name:
            # Name must be unique within the unit
            query = (table.name == name)
            if record_id:
                query &= (table.id != record_id)
            query &= (table.unit_id == data.get("unit_id")) & \
                     (table.deleted == False)
            duplicate = current.db(query).select(table.id, limitby=(0, 1)).first()
            if duplicate:
                form.errors.name = current.T("An area with that name already exists")

    # -------------------------------------------------------------------------
    @staticmethod
    def area_free_capacity(area_id, patient_id=None):
        """
            Returns the current free capacity for a treatment area

            Args:
                area_id: the area record ID
                patient_id: record ID of a patient to be placed in the
                            area (and hence to be ignored in the occupancy
                            count)
            Returns:
                tuple (area_name, free_capacity)

            Notes:
                - free capacity can be negative if area is occupied over capacity
                - free capacity will always be 1 if there is no capacity limit
                  for the area
        """

        db = current.db
        s3db = current.s3db

        atable = s3db.med_area
        ptable = s3db.med_patient

        area = db(atable.id == area_id).select(atable.name,
                                               atable.capacity,
                                               limitby = (0, 1),
                                               ).first()
        area_name = area.name if area else None

        if not area or not area.capacity:
            # Always at least one more place
            return area_name, 1

        occupancy = ptable.id.count(distinct=True)
        query = (ptable.area_id == area_id)
        if patient_id:
            query &= (ptable.id != patient_id)
        query &= (ptable.status.belongs(("ARRIVED", "TREATMENT"))) & \
                 (ptable.invalid == False) & \
                 (ptable.deleted == False)
        row = db(query).select(occupancy).first()

        return area_name, area.capacity - row[occupancy]

# =============================================================================
class MedPatientModel(DataModel):
    """ Patient (Visit) Data Model """

    names = ("med_patient",
             "med_patient_id",
             )

    def model(self):

        T = current.T
        db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        # configure = self.configure

        # ---------------------------------------------------------------------
        # Patient Status
        #
        patient_status = (("ARRIVED", T("Arrived")),
                          ("TREATMENT", T("In Treatment")),
                          ("DISCHARGED", T("Discharged")),
                          ("TRANSFERRED", T("Transferred")),
                          )

        status_represent = S3PriorityRepresent(patient_status,
                                               {"ARRIVED": "lightblue",
                                                "TREATMENT": "blue",
                                                "DISCHARGED": "grey",
                                                "TRANSFERRED": "grey",
                                                }).represent

        # ---------------------------------------------------------------------
        # Triage Priorities
        #
        triage_priorities = (("A", T("Immediate##triage")),
                             ("B", T("Urgent##triage")),
                             ("C", T("Not Urgent##triage")),
                             ("D", T("Planned##triage")),
                             ("E", T("Deceased/Expectant##triage")),
                             )

        triage_represent = S3PriorityRepresent(triage_priorities,
                                               {"A": "red",
                                                "B": "amber",
                                                "C": "green",
                                                "D": "blue",
                                                "E": "black",
                                                }).represent

        # ---------------------------------------------------------------------
        # Contamination Hazards
        #
        hazards = (("B", T("Infection")),
                   ("R", T("Radiation")),
                   ("C", T("Toxic")),
                   )

        # ---------------------------------------------------------------------
        # Patient
        # - occasion when a person receives medical care (=visit)
        # - there can be multiple (successive) visits for a person,
        #   but only one (active) visit at a time
        #
        tablename = "med_patient"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     self.med_unit_id(
                         empty = False,
                         ondelete = "RESTRICT",
                         ),
                     self.med_area_id(),

                     Field("refno",
                           label = T("Visit #"),
                           writable = False,
                           ),
                     # The patient
                     self.pr_person_id(
                         label = T("Person"),
                         represent = self.pr_PersonRepresent(show_link=True,
                                                             none = T("Unregistered"),
                                                             ),
                         widget = S3PersonAutocompleteWidget(controller="med"),
                         comment = None,
                         ),
                     Field("unregistered", "boolean",
                           label = T("Unregistered Person"),
                           default = False,
                           ),
                     Field("person",
                           label = T("Description"),
                           represent = lambda v, row=None: v if v else "-",
                           comment = T("Specify Name, Gender and Age if known"),
                           ),

                     # Start and end date of the care occasion
                     DateTimeField(
                        label = T("Arrival Time"),
                        default = "now",
                        writable = False,
                        ),
                     DateTimeField("end_date",
                        label = T("End Date"),
                        readable = False,
                        writable = False,
                        ),

                     # Reason for the patient to seek care
                     Field("reason",
                           label = T("Reason for visit"),
                           requires = IS_NOT_EMPTY(),
                           ),

                     # Contamination hazards
                     Field("hazards", "list:string",
                           label = T("Contamination Hazards"),
                           requires = IS_IN_SET(hazards, multiple=True, sort=False, zero=None),
                           represent = self.hazards_represent(hazards),
                           widget = S3GroupedOptionsWidget(multiple = True,
                                                           size = None,
                                                           cols = 1,
                                                           sort = False,
                                                           ),
                           ),
                     Field("hazards_advice",
                           label = T("Hazards Advice"),
                           represent = lambda v, row=None: v if v else "-",
                           ),

                     Field("priority",
                           label = T("Priority"),
                           default = "C",
                           requires = IS_IN_SET(triage_priorities, zero=None, sort=False),
                           represent = triage_represent,
                           ),
                     # TODO inbound route (where did the patient come from?)
                     # TODO outbound route (destination)
                     Field("status",
                           label = T("Status"),
                           default = "ARRIVED",
                           requires = IS_IN_SET(patient_status, zero=None, sort=False),
                           represent = status_represent,
                           ),
                     # Flag to indicate that this is an invalid record
                     # - TODO have an archive-link (separate controller?) to access invalid records
                     Field("invalid", "boolean",
                           label = T("Invalid"),
                           default = False,
                           ),
                     CommentsField(),
                     s3_fieldmethod("patient_link",
                                    self.patient_link,
                                    represent = lambda v, row=None: \
                                                "-" if v is None else v if hasattr(v, "xml") else s3_str(v),
                                    search_field = "reason",
                                    ),
                     )

        # Components
        self.add_components(tablename,
                            med_status = "patient_id",
                            med_treatment = "patient_id",
                            med_vitals = "patient_id",
                            med_sample = "patient_id",
                            med_analysis = "patient_id",
                            med_epicrisis = {"joinby": "patient_id",
                                             "multiple": False,
                                             },
                            )

        # CRUD form
        crud_form = CustomForm(# ------- Unit -----------------------
                               "unit_id",
                               "area_id",
                               # ------- Patient --------------------
                               "person_id",
                               "unregistered",
                               "person",
                               # ------- Current Visit --------------
                               "date",
                               "refno",
                               "reason",
                               "priority",
                               "status",
                               # ------- Hazards --------------------
                               "hazards",
                               "hazards_advice",
                               # ------- Administrative -------------
                               "comments",
                               "invalid",
                               )
        subheadings = {"unit_id": T("Unit"),
                       "person_id": T("Patient"),
                       "date": T("Current Visit"),
                       "hazards": T("Hazards Advice"),
                       "comments": T("Administrative"),
                       }

        # List fields
        # TODO make using areas a deployment setting
        # TODO show unit if user can see multiple
        list_fields = [(T("Place##placement"), "area_id$name"),
                       "refno",
                       "person_id",
                       "priority",
                       "reason",
                       "date",
                       "status",
                       #end_date,       # Only when viewing previous patients
                       (T("Hazards"), "hazards"),
                       "comments",
                       ]

        # Table configuration
        self.configure(tablename,
                       deletable = False,
                       crud_form = crud_form,
                       subheadings = subheadings,
                       list_fields = list_fields,
                       extra_fields = ["reason"],
                       onvalidation = self.patient_onvalidation,
                       onaccept = self.patient_onaccept,
                       # TODO if not using areas, order by priority
                       orderby = "med_area.name",
                       super_entity = ("doc_entity",),
                       )

        # Foreign key template
        represent = med_PatientRepresent(lookup = tablename,
                                         fields = ["refno", "reason", "status"],
                                         show_link = True,
                                         )
        patient_id = FieldTemplate("patient_id", "reference %s" % tablename,
                                   label = T("Patient"),
                                   ondelete = "RESTRICT",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                   )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Visit"),
            title_display = T("Visit"),
            title_list = T("Visits"),
            title_update = T("Edit Visit"),
            label_list_button = T("List Visits"),
            label_delete_button = T("Delete Visit"),
            msg_record_created = T("Visit added"),
            msg_record_modified = T("Visit updated"),
            msg_record_deleted = T("Visit deleted"),
            msg_list_empty = T("No Visits currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"med_patient_id": patient_id,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {"med_patient_id": FieldTemplate.dummy("patient_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def patient_onvalidation(form):
        """
            Patient form validation:
            - there must be only one current visit per person
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings

        # Get form record id
        record_id = get_form_record_id(form)

        # Get form record data
        table = s3db.med_patient
        data = get_form_record_data(form, table, ["person_id",
                                                  "area_id",
                                                  "status",
                                                  ])

        status = data.get("status")
        open_status = ("ARRIVED", "TREATMENT")
        if status in open_status:
            # Verify that there are no other open patient records for the same person
            person_id = data.get("person_id")
            if person_id:
                query = (table.person_id == person_id) & \
                        (table.status.belongs(open_status)) & \
                        (table.invalid == False)
                if record_id:
                    query &= (table.id != record_id)
                query &= (table.deleted == False)
                row = db(query).select(table.id, limitby=(0, 1)).first()
                if row:
                    error = T("There is already an ongoing visit for this patient")
                    for fn in ("person_id", "status", "reason"):
                        if fn in form.vars:
                            form.errors[fn] = error
                            break

            # Area capacity handling
            capacity_handling = settings.get_med_area_over_capacity()
            area_id = data.get("area_id")
            if capacity_handling == "refuse" and area_id:
                area_name, free_capacity = MedUnitModel.area_free_capacity(
                                                            area_id,
                                                            patient_id = record_id,
                                                            )
                if free_capacity < 1:
                    form.errors.area_id = T("%(name)s already fully occupied") % \
                                            {"name": area_name}

    # -------------------------------------------------------------------------
    @staticmethod
    def patient_onaccept(form):
        """
            Onaccept routine for patient records:
            - set reference number
            - update unregistered/person fields
            - update person_id in component records
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        record_id = get_form_record_id(form)
        if not record_id:
            return

        table = s3db.med_patient
        query = (table.id == record_id) & \
                (table.deleted == False)
        record = db(query).select(table.id,
                                  table.refno,
                                  table.date,
                                  table.person_id,
                                  table.area_id,
                                  table.status,
                                  table.end_date,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return
        update = {}

        # Set end date
        open_status = ("ARRIVED", "TREATMENT")
        status = record.status
        if status in open_status:
            if record.end_date:
                update["end_date"] = None
        elif not record.end_date:
            update["end_date"] = current.request.utcnow

        # Set reference number
        if not record.refno:
            update["refno"] = str(record.id)

        # Update unregistered/person fields once person_id is set
        person_id = record.person_id
        if person_id:
            update["unregistered"] = False
            update["person"] = None

        if update:
            record.update_record(**update)

        # Update person_id in component records
        for tn in ("med_status",
                   "med_vitals",
                   "med_treatment",
                   "med_epicrisis",
                   ):
            ctable = s3db.table(tn)
            query = (ctable.patient_id == record_id) & \
                    (ctable.person_id != person_id) & \
                    (ctable.deleted == False)
            db(query).update(person_id = person_id,
                             modified_by = ctable.modified_by,
                             modified_on = ctable.modified_on,
                             )

        # Auto-generate epicrisis
        etable = s3db.med_epicrisis
        row = db(etable.patient_id==record_id).select(etable.id, limitby=(0, 1)).first()
        if not row:
            epicrisis = {"person_id": person_id,
                         "patient_id": record_id,
                         "date": record.date,
                         }
            epicrisis_id = epicrisis["id"] = etable.insert(**epicrisis)
            if epicrisis_id:
                s3db.update_super(etable, epicrisis)
                auth.s3_set_record_owner(etable, epicrisis_id)
                auth.s3_make_session_owner(etable, epicrisis_id)
                s3db.onaccept(etable, epicrisis, method="create")

        # Area capacity warning
        capacity_handling = settings.get_med_area_over_capacity()
        area_id = record.area_id
        if capacity_handling == "warn" and area_id and status in open_status:
            area_name, free_capacity = MedUnitModel.area_free_capacity(area_id)
            if free_capacity < 0:
                current.response.warning = current.T("%(name)s occupied over capacity") % \
                                           {"name": area_name}

    # -------------------------------------------------------------------------
    @staticmethod
    def patient_link(row):
        """
            Field method to represent the reason for visit as link to the
            patient record (med/patient), useful to allow switching between
            person and patient perspectives

            Args:
                row: the med_patient row (must include id and reason)

            Returns:
                a link to the patient record
        """

        if hasattr(row, "med_patient"):
            row = row.med_patient
        label = row.reason if "reason" in row else "?"
        if "id" in row:
            output = A(label, _href=URL(c="med", f="patient", args=[row.id]))
        else:
            output = label
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def hazards_represent(options):
        """
            Returns a function that represents a hazard list as group of icons

            Args:
                options: the hazard options

            Returns:
                representation function
        """

        hazards = dict(options)

        css = {"B": "hazard-bio",
               "R": "hazard-rad",
               "C": "hazard-tox",
               }

        def represent(value, row=None):

            if value is None:
                value = []

            representation = DIV(_class="med-hazards")
            for k, v in hazards.items():
                item = SPAN(_class=css.get(k, "hazard-any"))
                if k in value:
                    item["_title"] = v
                    item.add_class("hazard-pos")
                else:
                    item.add_class("hazard-neg")
                representation.append(item)

            return representation

        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def set_patient(record):
        """
            Link a vitals/status/treatment record to a person or patient

            Args:
                record - the record, must contain:
                            - id
                            - either person_id or patient_id
                            - date
        """

        db = current.db
        s3db = current.s3db

        table = s3db.med_patient

        if record.patient_id:
            query = (table.id == record.patient_id) & \
                    (table.deleted == False)
            patient = db(query).select(table.person_id, limitby=(0, 1)).first()
            if patient:
                record.update_record(person_id=patient.person_id)

        elif record.person_id:
            query = (table.person_id == record.person_id)
            date = record.date if "date" in record else None
            if date:
                # Choose the latest patient record matching this date
                query &= (table.date <= date) & \
                         ((table.end_date == None) | (table.end_date >= date))
            else:
                # Choose the latest open patient record
                open_status = ("ARRIVED", "TREATMENT")
                query &= (table.status.belongs(open_status))
            query &= (table.invalid == False) & \
                     (table.deleted == False)
            patient = db(query).select(table.id,
                                       orderby = ~table.date,
                                       limitby = (0, 1),
                                       ).first()
            if patient:
                record.update_record(patient_id=patient.id)

# =============================================================================
class MedStatusModel(DataModel):
    """ Data Model for medical status """

    names = ("med_status",
             )

    def model(self):

        T = current.T
        # db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        # configure = self.configure

        # ---------------------------------------------------------------------
        # Medical Status Report
        #
        tablename = "med_status"
        define_table(tablename,
                     self.pr_person_id(
                         label = T("Patient"),
                         empty = False,
                         comment = None,
                         readable = False,
                         writable = False,
                         ),
                     self.med_patient_id(
                         readable = False,
                         writable = False,
                         ),
                     DateTimeField(
                        default = "now",
                        future = 0,
                        # past = 24, # hours
                        ),
                     CommentsField("situation",
                                   label = T("Situation"),
                                   represent = s3_text_represent,
                                   requires = IS_NOT_EMPTY(),
                                   comment = None,
                                   ),
                     CommentsField("background",
                                   label = T("Background"),
                                   represent = s3_text_represent,
                                   comment = None,
                                   ),
                     CommentsField("assessment",
                                   label = T("Assessment"),
                                   represent = s3_text_represent,
                                   comment = None,
                                   ),
                     CommentsField("recommendation",
                                   label = T("Recommendation"),
                                   represent = s3_text_represent,
                                   comment = None
                                   ),
                     Field("is_final", "boolean",
                           default = False,
                           label = T("Report is final"),
                           represent = BooleanRepresent(icons = True,
                                                        colors = True,
                                                        ),
                           readable = False,
                           writable = False,
                           ),
                     Field("vhash",
                           readable = False,
                           writable = False,
                           ),
                     )

        # List fields incl. author
        list_fields = ["id",
                       "patient_id",
                       "date",
                       "created_by",
                       "situation",
                       "background",
                       "assessment",
                       "recommendation",
                       ]

        # Table configuration
        self.configure(tablename,
                       list_fields = list_fields,
                       list_type = "datalist",
                       list_layout = med_StatusListLayout(),
                       onaccept = self.status_onaccept,
                       orderby = "%s.date desc" % tablename,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Status Report"),
            title_display = T("Status Report"),
            title_list = T("Status Reports"),
            title_update = T("Edit Status Report"),
            label_list_button = T("List Status Reports"),
            label_delete_button = T("Delete Status Report"),
            msg_record_created = T("Status Report added"),
            msg_record_modified = T("Status Report updated"),
            msg_record_deleted = T("Status Report deleted"),
            msg_list_empty = T("No Status Reports currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        #return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def status_onaccept(form):
        """
            Onaccept-routine for status reports
            - set person_id
            - compute vhash if final
        """

        db = current.db
        s3db = current.s3db

        record_id = get_form_record_id(form)

        table = s3db.med_status
        query = (table.id == record_id) & (table.deleted == False)
        record = db(query).select(table.id,
                                  table.person_id,
                                  table.patient_id,
                                  table.date,
                                  table.is_final,
                                  limitby = (0, 1),
                                  ).first()

        if not record:
            return

        MedPatientModel.set_patient(record)

        if record.is_final:
            record = db(query).select(table.id,
                                      table.person_id,
                                      table.patient_id,
                                      table.date,
                                      table.situation,
                                      table.background,
                                      table.assessment,
                                      table.recommendation,
                                      limitby = (0, 1),
                                      ).first()

            # Compute vhash
            dt = record.date
            if dt:
                dtstr = dt.replace(microsecond=0).isoformat()
            else:
                dtstr = "-"
            values = [record.person_id,
                      record.patient_id,
                      dtstr,
                      ]
            for fn in ("situation", "background", "assessment", "recommendation"):
                value = record[fn]
                if not value:
                    value = "-"
                values.append(value)
            vhash = datahash(values)
            record.update_record(vhash=vhash)

# =============================================================================
class MedParameterModel(DataModel):
    """ Data Model for medical parameters (e.g. lab results) """

    names = ("med_parameter_group",
             "med_sample_type",
             "med_parameter",
             "med_analysis",
             "med_sample",
             "med_analysis_result",
             )

    def model(self):

        T = current.T
        db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        organisation_id = self.org_organisation_id
        person_id = self.pr_person_id
        patient_id = self.med_patient_id

        # ---------------------------------------------------------------------
        # Parameter Group
        # - for grouping of results
        #
        tablename = "med_parameter_group"
        define_table(tablename,
                     organisation_id(),
                     Field("name", notnull=True,
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     CommentsField(),
                     )

        # Table configuration
        configure(tablename,
                  onvalidation = self.parameter_group_onvalidation,
                  )

        # Foreign key template
        represent = S3Represent(lookup=tablename)
        parameter_group_id = FieldTemplate("parameter_group_id", "reference %s" % tablename,
                                           label = T("Parameter Group"),
                                           ondelete = "SET NULL",
                                           represent = represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "%s.id" % tablename,
                                                                  represent,
                                                                  )),
                                           )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Parameter Group"),
            title_display = T("Parameter Group"),
            title_list = T("Parameter Groups"),
            title_update = T("Edit Parameter Group"),
            label_list_button = T("List Parameter Groups"),
            label_delete_button = T("Delete Parameter Group"),
            msg_record_created = T("Parameter Group added"),
            msg_record_modified = T("Parameter Group updated"),
            msg_record_deleted = T("Parameter Group deleted"),
            msg_list_empty = T("No Parameter Groups currently defined"),
            )

        # ---------------------------------------------------------------------
        # Sample Type
        #
        tablename = "med_sample_type"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_ONE_OF(db, "%s.name" % tablename),
                                       IS_LENGTH(128, minsize=2),
                                       ],
                           ),
                     Field("code", length=32, notnull=True, unique=True,
                           label = T("Code"),
                           requires = [IS_NOT_ONE_OF(db, "%s.code" % tablename),
                                       IS_LENGTH(32, minsize=2),
                                       ],
                           ),
                     CommentsField("instructions",
                                   label = T("Instructions"),
                                   comment = None,
                                   ),
                     Field("obsolete", "boolean",
                           label = T("Obsolete"),
                           default = False,
                           represent = BooleanRepresent(labels = False,
                                                        # Reverse icons semantics
                                                        icons = (BooleanRepresent.NEG,
                                                                 BooleanRepresent.POS,
                                                                 ),
                                                        flag = True,
                                                        ),
                           ),
                     CommentsField(),
                     )

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary=("name", "code")),
                  )

        # Foreign key template
        represent = S3Represent(lookup=tablename)
        sample_type_id = FieldTemplate("sample_type_id", "reference %s" % tablename,
                                       label = T("Sample Type"),
                                       ondelete = "RESTRICT",
                                       represent = represent,
                                       requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "%s.id" % tablename,
                                                              represent,
                                                              filterby = "obsolete",
                                                              filter_opts = (False,),
                                                              )),
                                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Sample Type"),
            title_display = T("Sample Type"),
            title_list = T("Sample Types"),
            title_update = T("Edit Sample Type"),
            label_list_button = T("List Sample Types"),
            label_delete_button = T("Delete Sample Type"),
            msg_record_created = T("Sample Type added"),
            msg_record_modified = T("Sample Type updated"),
            msg_record_deleted = T("Sample Type deleted"),
            msg_list_empty = T("No Sample Types currently defined"),
            )

        # ---------------------------------------------------------------------
        # Parameter
        #
        tablename = "med_parameter"
        define_table(tablename,
                     organisation_id(),
                     parameter_group_id(),
                     sample_type_id(),
                     Field("name",
                           label = T("Parameter"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("abrv",
                           label = T("Abbreviation"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("qualitative", "boolean",
                           label = T("Qualitative"),
                           default = False,
                           ),
                     Field("um",
                           label = T("Unit of Measure"),
                           ),
                     Field("precsn", "integer",
                           label = T("Precision"),
                           default = 0,
                           requires = IS_INT_IN_RANGE(minimum=0, maximum=4),
                           ),
                     Field("values_valid", "json",
                           label = T("Valid Values"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = T('Specify like ["value", "value", ...] (options) or [min, max] (range)'),
                           ),
                     Field("values_normal", "json",
                           label = T("Normal Values"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = T('Specify like ["value", "value", ...] (options) or [min, max] (range)'),
                           ),
                     Field("obsolete", "boolean",
                           label = T("Obsolete"),
                           default = False,
                           represent = BooleanRepresent(labels = False,
                                                        # Reverse icons semantics
                                                        icons = (BooleanRepresent.NEG,
                                                                 BooleanRepresent.POS,
                                                                 ),
                                                        flag = True,
                                                        ),
                           ),
                     CommentsField("instructions",
                                   label = T("Instructions"),
                                   comment = None,
                                   ),
                     CommentsField(),
                     )

        # Table configuration
        configure(tablename,
                  onvalidation = self.parameter_onvalidation,
                  )

        # Foreign key template
        represent = S3Represent(lookup=tablename)
        parameter_id = FieldTemplate("parameter_id", "reference %s" % tablename,
                                     label = T("Parameter"),
                                     ondelete = "RESTRICT",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "%s.id" % tablename,
                                                              represent,
                                                              )),
                                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Parameter"),
            title_display = T("Parameter"),
            title_list = T("Parameters"),
            title_update = T("Edit Parameter"),
            label_list_button = T("List Parameters"),
            label_delete_button = T("Delete Parameter"),
            msg_record_created = T("Parameter added"),
            msg_record_modified = T("Parameter updated"),
            msg_record_deleted = T("Parameter deleted"),
            msg_list_empty = T("No Parameters currently defined"),
            )

        # ---------------------------------------------------------------------
        # Analysis
        #
        tablename = "med_analysis"
        define_table(tablename,
                     patient_id(
                         label = T("Visit"),
                         readable = False,
                         writable = False,
                         ),
                     person_id(
                         readable = False,
                         writable = False,
                         comment = None,
                         ),
                     DateTimeField(default="now"),
                     # TODO status (pending, partial, complete, )
                     Field("invalid", "boolean",
                           label = T("Invalid"),
                           default = False,
                           represent = BooleanRepresent(labels = False,
                                                        # Reverse icons semantics
                                                        icons = (BooleanRepresent.NEG,
                                                                 BooleanRepresent.POS,
                                                                 ),
                                                        colors = (BooleanRepresent.RED,
                                                                  BooleanRepresent.GREEN,
                                                                  ),
                                                        flag = True,
                                                        ),
                           ),
                     CommentsField(),
                     )

        # Components
        self.add_components(tablename,
                            med_sample = "analysis_id",
                            med_analysis_result = "analysis_id",
                            )

        # CRUD Form (with embedded results)
        crud_form = CustomForm("date",
                               InlineComponent("analysis_result",
                                               # TODO label
                                               # TODO review fields
                                               fields = ["parameter_id",
                                                         "result",
                                                         "status",
                                                         "status_reason",
                                                         ],
                                               ),
                               "invalid",
                               "comments",
                               )

        # Table Configuration
        configure(tablename,
                  crud_form = crud_form,
                  onaccept = self.analysis_result_onaccept,
                  data_series = AnalysisDataSeries,
                  )

        # Methods
        self.set_method(tablename,
                        method = "results",
                        action = DataSeriesCRUD,
                        )

        # Foreign key template
        represent = S3Represent(lookup=tablename, fields=["date"])
        analysis_id = FieldTemplate("analysis_id", "reference %s" % tablename,
                                    label = T("Analysis"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                    )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Analysis"),
            title_display = T("Analysis"),
            title_list = T("Analyses"),
            title_update = T("Edit Analysis"),
            label_list_button = T("List Analyses"),
            label_delete_button = T("Delete Analysis"),
            msg_record_created = T("Analysis created"),
            msg_record_modified = T("Analysis updated"),
            msg_record_deleted = T("Analysis deleted"),
            msg_list_empty = T("No Analyses currently registered"),
            )

        # ---------------------------------------------------------------------
        # Sample (physical artefact)
        #
        tablename = "med_sample"
        define_table(tablename,
                     patient_id(),
                     person_id(comment=None),
                     sample_type_id(),
                     analysis_id(),
                     # sample number (autogenerate)?
                     DateTimeField(default="now"),
                     # taken_by
                     # TODO status (pending, taken, sent, arrived, analysed, discarded)
                     CommentsField(),
                     )

        # Components
        self.add_components(tablename,
                            med_analysis_result = "sample_id",
                            )

        # Foreign key template
        represent = med_SampleRepresent()
        sample_id = FieldTemplate("sample_id", "reference %s" % tablename,
                                  label = T("Sample"),
                                  ondelete = "SET NULL",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                  )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Sample"),
            title_display = T("Sample"),
            title_list = T("Samples"),
            title_update = T("Edit Sample"),
            label_list_button = T("List Samples"),
            label_delete_button = T("Delete Sample"),
            msg_record_created = T("Sample created"),
            msg_record_modified = T("Sample updated"),
            msg_record_deleted = T("Sample deleted"),
            msg_list_empty = T("No Samples currently registered"),
            )

        # ---------------------------------------------------------------------
        # Measured/observed values (data artefact)
        #
        result_status_opts = WorkflowOptions(("PENDING", "Pending", "blue"),
                                             ("PRELIMINARY", "Preliminary", "amber"),
                                             ("FINAL", "Final", "green"),
                                             ("FAILED", "Failed", "black"),
                                             represent = "status",
                                             none = "PENDING",
                                             )

        tablename = "med_analysis_result"
        define_table(tablename,
                     person_id(
                         label = T("Patient"),
                         empty = False,
                         comment = None,
                         readable = False,
                         writable = False,
                         ),
                     patient_id(
                         empty = False,
                         readable = False,
                         writable = False,
                         ),
                     analysis_id(empty=False),
                     sample_id(),
                     parameter_id(empty=False),

                     # The original result as-entered
                     Field("result",
                           label = T("Result"),
                           ),

                     # Result Status
                     Field("status",
                           label = T("Status"),
                           default = "PENDING",
                           requires = IS_IN_SET(result_status_opts.selectable(), sort=False),
                           represent = result_status_opts.represent,
                           ),
                     # TODO make status reason mandatory for all except preliminary/final
                     Field("status_reason",
                           label = T("Reason"),
                           ),

                     # Numerical result, computed from result onaccept
                     Field("result_numeric", "double",
                           readable = False,
                           writable = False,
                           ),
                     # Marker for abnormal values, TODO compute onaccept
                     # - unless set True manually
                     # - if value is valid and normal range/options defined
                     Field("abnormal", "boolean",
                           default = False,
                           label = T("Outside of normal range"),
                           represent = BooleanRepresent(labels = False,
                                                        # Reverse icons semantics
                                                        icons = ("fa fa-exclamation",
                                                                 BooleanRepresent.POS,
                                                                 ),
                                                        colors = (BooleanRepresent.RED,
                                                                  BooleanRepresent.GREEN,
                                                                  ),
                                                        flag = True,
                                                        ),
                           ),
                     DateTimeField(label = T("Date reported"),
                                   default = "now",
                                   future = 0,
                                   writable = False,
                                   ),
                     # TODO reported_by
                     #DateTimeField("assessed_on"
                     #              label = T("Date assessed"),
                     #              ),
                     # TODO assessed_by
                     #DateTimeField("acknowledged_on",
                     #              label = T("Date acknowledged"),
                     #              ),
                     # TODO acknowledged_by
                     # TODO vhash
                     )

        # Table configuration
        configure(tablename,
                  onvalidation = self.analysis_result_onvalidation,
                  onaccept = self.analysis_result_onaccept,
                  )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Measured Value"),
            title_display = T("Measured Value"),
            title_list = T("Measured Values"),
            title_update = T("Edit Measured Value"),
            label_list_button = T("List Measured Values"),
            label_delete_button = T("Delete Measured Value"),
            msg_record_created = T("Measured Value Added"),
            msg_record_modified = T("Measured Value updated"),
            msg_record_deleted = T("Measured Value deleted"),
            msg_list_empty = T("No Measured Values currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        #return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def parameter_group_onvalidation(form):
        """
            Form validation of parameter groups:
                - name must be unique within organisation
        """

        table = current.s3db.med_parameter_group
        data = get_form_record_data(form, table, ["organisation_id", "name"])

        query = (table.organisation_id == data.get("organisation_id")) & \
                (table.name == data.get("name"))

        record_id = get_form_record_id(form)
        if record_id:
            query &= (table.id != record_id)
        query &= (table.deleted == False)
        row = current.db(query).select(table.id, limitby=(0, 1)).first()
        if row:
            form.errors["name"] = current.T("Parameter Group exists")

    # -------------------------------------------------------------------------
    @staticmethod
    def parameter_onvalidation(form):
        """
            Form validation of parameters:
                - name must be unique within organisation
                - abrv must be unique within organisation
        """

        record_id = get_form_record_id(form)

        table = current.s3db.med_parameter
        data = get_form_record_data(form, table, ["organisation_id", "name", "abrv"])
        name = data.get("name")
        abrv = data.get("abrv")

        query = (table.name == name)
        if abrv:
            query |= (table.abrv == abrv)
        query = (table.organisation_id == data.get("organisation_id")) & query
        if record_id:
            query &= (table.id != record_id)
        query &= (table.deleted == False)
        rows = current.db(query).select(table.id, table.name, table.abrv)

        msg = current.T("Parameter exists")
        for row in rows:
            if row.name == name:
                form.errors["name"] = msg
            if row.abrv == abrv:
                form.errors["abrv"] = msg

    # -------------------------------------------------------------------------
    @staticmethod
    def sample_onaccept(form):
        """
            Onaccept-routine for sample
            - set patient_id/person_id
        """

        # TODO inherit patient_id/person_id from analysis, if linked

        db = current.db
        s3db = current.s3db

        record_id = get_form_record_id(form)

        table = s3db.med_sample
        query = (table.id == record_id) & (table.deleted == False)
        record = db(query).select(table.id,
                                  table.person_id,
                                  table.patient_id,
                                  limitby = (0, 1),
                                  ).first()

        if not record:
            return

        if not record.patient_id or not record.person_id:
            MedPatientModel.set_patient(record)

    # -------------------------------------------------------------------------
    @staticmethod
    def analysis_onaccept(form):
        """
            Onaccept-routine for analysis
            - set patient_id/person_id
        """

        db = current.db
        s3db = current.s3db

        record_id = get_form_record_id(form)

        table = s3db.med_analysis
        query = (table.id == record_id) & (table.deleted == False)
        record = db(query).select(table.id,
                                  table.person_id,
                                  table.patient_id,
                                  limitby = (0, 1),
                                  ).first()

        if not record:
            return

        if not record.patient_id or not record.person_id:
            MedPatientModel.set_patient(record)

    # -------------------------------------------------------------------------
    @staticmethod
    def analysis_result_onvalidation(form):
        """
            Form validation of parameter values:
            - other status than PENDING requires a result
        """

        table = current.s3db.med_analysis_result
        data = get_form_record_data(form, table, ["result", "status"])

        # TODO there must be only one result per parameter per analysis/sample!

        status = data.get("status")
        result = data.get("result")

        if result:
            if status == "PENDING":
                form.errors["status"] = current.T("Result must have qualified status")
        else:
            if status != "PENDING":
                form.errors["result"] = current.T("Result cannot be empty")

    # -------------------------------------------------------------------------
    @staticmethod
    def analysis_result_onaccept(form):
        """
            Onaccept-routine for parameter values
            - set patient_id/person_id
            - generate/link to sample as required
            - compute numerical result for quantitative parameters (if possible)
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth

        record_id = get_form_record_id(form)

        ptable = s3db.med_parameter
        atable = s3db.med_analysis
        stable = s3db.med_sample

        # Reload the record
        table = s3db.med_analysis_result
        query = (table.id == record_id) & (table.deleted == False)
        record = db(query).select(table.id,
                                  table.person_id,
                                  table.patient_id,
                                  table.parameter_id,
                                  table.analysis_id,
                                  table.sample_id,
                                  table.date,
                                  table.result,
                                  table.status,
                                  limitby = (0, 1),
                                  ).first()

        if not record:
            return
        analysis_id = record.analysis_id

        # Inherit person_id/patient_id from analysis
        if not(record.person_id or record.patient_id) and analysis_id:
            # Look up person_id/patient_id from analysis
            query = (atable.id == analysis_id) & (atable.deleted == False)
            row = db(query).select(atable.person_id,
                                   atable.patient_id,
                                   limitby = (0, 1),
                                   ).first()
            if row:
                record.update_record(person_id = row.person_id,
                                     patient_id = row.patient_id,
                                     )
        # Add missing person/patient reference, if required
        if not record.patient_id or not record.person_id:
            MedPatientModel.set_patient(record)

        # Look up parameter details
        query = (ptable.id == record.parameter_id) & \
                (ptable.deleted == False)
        param = db(query).select(ptable.sample_type_id,
                                 ptable.qualitative,
                                 limitby = (0, 1),
                                 ).first()
        sample_type_id = param.sample_type_id if param else None

        # Auto-generate sample record, if required
        if not record.sample_id and sample_type_id:
            if analysis_id:
                # Check for existing sample of that type
                query = (stable.analysis_id == analysis_id) & \
                        (stable.sample_type_id == sample_type_id) & \
                        (stable.deleted == False)
                sample = db(query).select(stable.id, limitby=(0, 1)).first()
            else:
                sample = None

            if sample:
                # Use existing sample
                sample_id = sample.id
            else:
                # Create new sample
                sample = {"person_id": record.person_id,
                          "patient_id": record.patient_id,
                          "analysis_id": analysis_id,
                          "sample_type_id": sample_type_id,
                          "date": record.date,
                          }
                sample_id = sample["id"] = stable.insert(**sample)

                # Postprocess create
                s3db.update_super(stable, sample)
                auth.s3_set_record_owner(stable, sample_id)
                auth.s3_make_session_owner(stable, sample_id)
                s3db.onaccept(stable, sample_id, method="create")

            # Link record to sample
            record.update_record(sample_id=sample_id)

        # Compute numeric value for quantitative parameters
        if param and not param.qualitative:
            result, value = record.result, None
            if result and record.status != "PENDING":
                # The NV-regex handles numerical values with either , or . as
                # decimals-separator, and then the other one for thousands,
                # to allow for safer data entry; e.g. "1,234.56" or "1.234,56"
                # are both understood as 1234.56
                # NOTE: however, a single separator is always interpreted as
                #       decimals-separator, i.e. 1,234 is read as 1.234, not 1234
                # NOTE: input values that do not match the regex will produce
                #       result_numeric=None
                # NOTE: output representation should always use the configured
                #       l10n separators and med_parameter.precsn, regardless how
                #       the value has been entered
                match = re.match(NV, result.replace(" ", ""))
                if match:
                    # Get the integer part
                    v = "%s%s" % (match.group(1), match.group(2))
                    if match.group(3):
                        # Drop the thousands-separator
                        v = v.replace(match.group(3), "")
                    if match.group(4):
                        # Add the decimal part
                        v = "%s.%s" % (v, match.group(4))
                    try:
                        value = float(v)
                    except (ValueError, TypeError):
                        pass
            record.update_record(result_numeric=value)

# =============================================================================
class MedVitalsModel(DataModel):
    """ Data Model for vital signs """

    names = ("med_vitals",
             )


    def model(self):

        T = current.T
        # db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        # configure = self.configure

        # ---------------------------------------------------------------------
        # Vital Signs
        #
        avcpus = (("A", T("Alert##consciousness")),
                  ("V", T("Verbal##consciousness")),
                  ("C", T("Confused##consciousness")),
                  ("P", T("Pain##consciousness")),
                  ("U", T("Unresponsive##consciousness")),
                  ("S", T("Seizure##consciousness")),
                  )

        airway_status = (("N", T("Free##airways")),
                         ("C", T("Compromised##airways")),
                         )

        risk_class = (("C", T("Critical##risk")),
                      ("H", T("High")),
                      ("M", T("Medium")),
                      ("L", T("Low")),
                      )
        risk_class_represent = S3PriorityRepresent(risk_class,
                                                   {"C": "red",
                                                    "H": "lightred",
                                                    "M": "amber",
                                                    "L": "green",
                                                    }).represent

        # TODO age-adjust normal-ranges for representation (=>prep)
        tablename = "med_vitals"
        define_table(tablename,
                     self.pr_person_id(
                         label = T("Patient"),
                         empty = False,
                         comment = None,
                         readable = False,
                         writable = False,
                         ),
                     self.med_patient_id(
                         readable = False,
                         writable = False,
                         ),
                     DateTimeField(
                        default = "now",
                        future = 0,
                        past = 6, # hours
                        ),
                     Field("risk_class",
                           label = T("Risk"),
                           default = "L",
                           requires = IS_IN_SET(risk_class, zero=None, sort=False),
                           represent = risk_class_represent,
                           readable = False,
                           writable = False,
                           ),
                     Field("airways",
                           label = T("Airways##medical"),
                           default = "N",
                           requires = IS_IN_SET(airway_status, zero=None, sort=False),
                           represent = self.represent_discrete(dict(airway_status), normal={"N"}),
                           ),
                     Field("rr", "integer",
                           label = T("Respiratory Rate"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(minimum=2, maximum=80)),
                           represent = represent_normal(12, 20),
                           ),
                     Field("o2sat", "integer",
                           label = T("O2 Sat%"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(minimum=0, maximum=100)),
                           represent = represent_normal(95, 100),
                           ),
                     Field("o2sub", "integer",
                           label = T("O2 L/min"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(minimum=0, maximum=20)),
                           represent = represent_normal(0, 0),
                           ),
                     Field("hypox", "boolean",
                           default = False,
                           label = T("Chronic Hypoxemia"),
                           ),
                     Field("bp",
                           label = T("Blood Pressure"),
                           requires = IS_EMPTY_OR(IS_BLOOD_PRESSURE()),
                           represent = self.represent_bp(110, 220),
                           ),
                     Field("hr", "integer",
                           label = T("Heart Rate"),
                           requires = IS_INT_IN_RANGE(minimum=10, maximum=300),
                           represent = represent_normal(51, 90),
                           ),
                     Field("temp", "double",
                           label = T("Temperature"),
                           requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(minimum=25.0, maximum=44.0)),
                           represent = represent_normal(36.1, 38.0),
                           ),
                     Field("consc",
                           default = "A",
                           label = T("Consciousness"),
                           requires = IS_IN_SET(avcpus, zero=None, sort=False),
                           represent = self.represent_discrete(dict(avcpus), normal={"A"}),
                           ),
                     )

        # List fields
        list_fields = ["date",
                       (T("Occasion"), "patient_id"),
                       "airways",
                       (T("RR##vitals"), "rr"),
                       "o2sat",
                       "o2sub",
                       (T("BP##vitals"), "bp"),
                       (T("HR##vitals"), "hr"),
                       (T("Temp"), "temp"),
                       "consc",
                       "risk_class",
                       ]

        # Table configuration
        self.configure(tablename,
                       list_fields = list_fields,
                       onaccept = self.vitals_onaccept,
                       orderby = "%s.date desc" % tablename,
                       editable = False,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Register Vital Signs"),
            title_display = T("Vital Signs"),
            title_list = T("Vital Signs"),
            title_update = T("Edit Vital Signs"),
            label_list_button = T("List Vital Signs"),
            label_delete_button = T("Delete Vital Signs"),
            msg_record_created = T("Vital Signs added"),
            msg_record_modified = T("Vital Signs updated"),
            msg_record_deleted = T("Vital Signs deleted"),
            msg_list_empty = T("No Vital Signs currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def vitals_onaccept(form):
        """
            Onaccept-routine for vital signs
            - set person/patient ID
            - calculate risk class
        """

        db = current.db
        s3db = current.s3db

        record_id = get_form_record_id(form)

        table = s3db.med_vitals
        query = (table.id == record_id) & (table.deleted == False)
        record = db(query).select(table.id,
                                  table.person_id,
                                  table.patient_id,
                                  table.date,
                                  limitby = (0, 1),
                                  ).first()

        if record:
            MedPatientModel.set_patient(record)
            RiskClass.calculator(record_id).update_risk()

    # -------------------------------------------------------------------------
    @staticmethod
    def represent_bp(minimum=None, maximum=None):
        """
            Renders a representation of blood pressure, highlighting
            abnormal values

            Args:
                minimum: the SBP minimum
                maximum: the SBP maximum
            Returns:
                a representation function
        """

        def represent(value, row=None):

            sbp, _ = med_parse_bp(value)
            if sbp is not None:
                if (minimum is None or minimum < sbp) and \
                   (maximum is None or sbp < maximum):
                    output = SPAN(value)
                else:
                    output = SPAN(value, _class="out-of-range")
            else:
                output = "-"
            return output

        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def represent_discrete(options, *, normal=None):
        """
            Renders a representation of a discrete vital sign value, such
            as airway status or conscience

            Args:
                options: a dict of valid options
                normal: a set|tuple|list of normal options
            Returns:
                a representation function
        """

        def represent(value, row=None):

            if value:
                reprstr = options.get(value, "-")
                if normal is None or value in normal:
                    output = SPAN(reprstr)
                else:
                    output = SPAN(reprstr, _class="out-of-range")
            else:
                output = "-"
            return output

        return represent

# =============================================================================
class MedTreatmentModel(DataModel):
    """ Data Model for treatment documentation """

    names = ("med_treatment",
             "med_treatment_status"
             )

    def model(self):

        T = current.T
        # db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        # configure = self.configure

        # ---------------------------------------------------------------------
        # Treatment
        #
        treatment_status = (("P", T("Pending")),
                            ("S", T("Started / Ongoing")),
                            ("C", T("Completed")),
                            ("R", T("Canceled")),
                            ("O", T("Obsolete")),
                            )
        status_represent = S3PriorityRepresent(treatment_status,
                                               {"P": "lightblue",
                                                "S": "blue",
                                                "C": "green",
                                                "R": "grey",
                                                "O": "grey",
                                                }).represent

        tablename = "med_treatment"
        define_table(tablename,
                     self.pr_person_id(
                         label = T("Patient"),
                         empty = False,
                         comment = None,
                         readable = False,
                         writable = False,
                         ),
                     self.med_patient_id(
                         readable = False,
                         writable = False,
                         ),
                     DateTimeField(
                        default = "now",
                        future = 0,
                        writable = False,
                        ),
                     CommentsField("details",
                                   label = T("Treatment Measure"),
                                   requires = IS_NOT_EMPTY(),
                                   comment = None,
                                   ),
                     Field("status",
                           default = "P",
                           label = T("Status"),
                           requires = IS_IN_SET(treatment_status, zero=None, sort=False),
                           represent = status_represent,
                           ),
                     DateTimeField("start_date",
                                   label = T("Start"),
                                   future = 0,
                                   ),
                     DateTimeField("end_date",
                                   label = T("End"),
                                   future = 0,
                                   ),
                     Field("vhash",
                           readable = False,
                           writable = False,
                           ),
                     CommentsField(),
                     )

        # List fields
        list_fields = ["patient_id",
                       "date",
                       "details",
                       "status",
                       "start_date",
                       "end_date",
                       "comments",
                       ]

        # Table configuration
        self.configure(tablename,
                       list_fields = list_fields,
                       onvalidation = self.treatment_onvalidation,
                       onaccept = self.treatment_onaccept,
                       orderby = "%s.date desc" % tablename,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Treatment Measure"),
            title_display = T("Treatment Measure"),
            title_list = T("Treatment"),
            title_update = T("Edit Treatment Measure"),
            label_list_button = T("List Treatment Measures"),
            label_delete_button = T("Delete Treatment"),
            msg_record_created = T("Treatment Measure added"),
            msg_record_modified = T("Treatment Measures updated"),
            msg_record_deleted = T("Treatment Measure deleted"),
            msg_list_empty = T("No Treatment Measures currently registered"),
            )

        # ---------------------------------------------------------------------
        # Treatment Status History
        #
        tablename = "med_treatment_status"
        define_table(tablename,
                     Field("treatment_id", "reference med_treatment",
                           ondelete = "CASCADE",
                           readable = False,
                           writable = False,
                           ),
                     DateTimeField(),
                     Field("details", "text",
                           label = T("Treatment Measure"),
                           readable = False,
                           writable = False,
                           ),
                     Field("status",
                           label = T("Status"),
                           readable = False,
                           writable = False,
                           ),
                     )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def treatment_update_history(record):
        """
            Tracks changes to a treatment record

            Args:
                record: the treatment record (containing id, details and status)
        """

        s3db = current.s3db
        auth = current.auth

        htable = s3db.med_treatment_status

        # Write new history entry
        entry = {"treatment_id": record.id,
                 "date": current.request.utcnow,
                 "details": record.details,
                 "status": record.status
                 }
        entry["id"] = entry_id = htable.insert(**entry)
        if entry_id:
            s3db.update_super(htable, entry)
            auth.s3_set_record_owner(htable, entry_id)
            auth.s3_make_session_owner(htable, entry_id)
            s3db.onaccept(htable, entry, method="create")

    # -------------------------------------------------------------------------
    @staticmethod
    def treatment_onvalidation(form):
        """
            Treatment form validation
            - end date must be after start date
        """

        # Get form record data
        table = current.s3db.med_treatment
        data = get_form_record_data(form, table, ["start_date", "end_date"])

        start = data.get("start_date")
        end = data.get("end_date")

        if start and end and end < start:
            form.errors.end_date = current.T("End must be at or after start")

    # -------------------------------------------------------------------------
    @classmethod
    def treatment_onaccept(cls, form):
        """
            Onaccept-routine for treatment measures
            - set person_id/patient_id as required
            - set start/end dates as required
            - create history entry if status has changed

            Args:
                form: the FORM
        """

        db = current.db
        s3db = current.s3db

        record_id = get_form_record_id(form)

        table = s3db.med_treatment
        query = (table.id == record_id) & (table.deleted == False)
        record = db(query).select(table.id,
                                  table.person_id,
                                  table.patient_id,
                                  table.date,
                                  table.details,
                                  table.status,
                                  table.vhash,
                                  table.start_date,
                                  table.end_date,
                                  limitby = (0, 1),
                                  ).first()

        if not record:
            return

        MedPatientModel.set_patient(record)

        update = {}

        status = record.status
        date, start, end = record.date, record.start_date, record.end_date
        now = current.request.utcnow

        if status == "P":
            # This status can have neither start nor end date
            if start:
                start = update["start_date"] = None
            if end:
                end = update["end_date"] = None
        if status == "S":
            # This status should have a start date, but no end date
            if not start:
                start = update["start_date"] = now
            if end:
                end = update["end_date"] = None
        if status == "C":
            # This status should have both start and end date
            if not end:
                end = update["end_date"] = now
            if not start:
                start = update["start_date"] = end
        if status in ("R", "O"):
            # These statuses should have an end date if, and only if, they have a start date
            if end and not start:
                end = update["end_date"] = None
            if start and not end:
                end = update["end_date"] = now

        # Compute vhash
        values = [record.person_id,
                  record.patient_id,
                  date.replace(microsecond=0).isoformat() if date else "-",
                  ]
        for fn in ("details", "status"):
            value = record[fn]
            if not value:
                value = "-"
            values.append(value)
        vhash = datahash(values)

        # Update history if hash has changed
        if vhash != record.vhash:
            cls.treatment_update_history(record)
            update["vhash"] = vhash

        # Update record if required
        if update:
            record.update_record(**update)

# =============================================================================
class MedEpicrisisModel(DataModel):
    """ Epicrisis Report Model """

    names = ("med_epicrisis",
             )

    def model(self):

        T = current.T
        # db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        # configure = self.configure

        # ---------------------------------------------------------------------
        # Epicrisis
        #
        tablename = "med_epicrisis"
        define_table(tablename,
                     self.pr_person_id(
                         label = T("Patient"),
                         empty = False,
                         comment = None,
                         readable = False,
                         writable = False,
                         ),
                     self.med_patient_id(
                         readable = False,
                         writable = False,
                         ),
                     DateTimeField(
                        default = "now",
                        future = 0,
                        readable = False,
                        writable = False,
                        ),
                     CommentsField("situation",
                                   label = T("Situation"),
                                   comment = None,
                                   ),
                     CommentsField("diagnoses",
                                   label = T("Relevant Diagnoses"),
                                   comment = None,
                                   ),
                     CommentsField("progress",
                                   label = T("Treatment / Progress"),
                                   comment = None,
                                   ),
                     CommentsField("outcome",
                                   label = T("Outcome"),
                                   comment = None,
                                   ),
                     CommentsField("recommendation",
                                   label = T("Recommendation"),
                                   comment = None,
                                   ),
                     Field("is_final", "boolean",
                           default = False,
                           label = T("Report is final"),
                           represent = BooleanRepresent(icons = True,
                                                        colors = True,
                                                        ),
                           readable = False,
                           writable = False,
                           ),
                     Field("vhash",
                           readable = False,
                           writable = False,
                           ),
                     )

        # Table configuration
        self.configure(tablename,
                       onvalidation = self.epicrisis_onvalidation,
                       onaccept = self.epicrisis_onaccept,
                       orderby = "%s.date desc" % tablename,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Epicrisis"),
            title_display = T("Epicrisis"),
            title_list = T("Epicrises"),
            title_update = T("Edit Epicrisis"),
            label_list_button = T("List Epicrises"),
            label_delete_button = T("Delete Epicrisis"),
            msg_record_created = T("Epicrisis added"),
            msg_record_modified = T("Epicrisis updated"),
            msg_record_deleted = T("Epicrisis deleted"),
            msg_list_empty = T("No Epicrises currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def epicrisis_onvalidation(form):
        """
            Form validation for epicrisis reports
            - situation required when marked as final
        """

        T = current.T

        fields = ["situation", "is_final"]

        table = current.s3db.med_epicrisis
        data = get_form_record_data(form, table, fields)

        # Verify that situation field is filled when marking as final
        if data.get("is_final") and not data.get("situation"):
            error = T("Situation description required to finalize report")
            for fn in ("situation", "is_final"):
                if fn in form.vars:
                    form.errors[fn] = error
                    break

    # -------------------------------------------------------------------------
    @staticmethod
    def epicrisis_onaccept(form):
        """
            Onaccept-routine for epicrisis reports
            - set person_id/patient_id
            - update the date if changed
            - compute vhash if final (or remove it otherwise)
        """

        db = current.db
        s3db = current.s3db

        record_id = get_form_record_id(form)

        table = s3db.med_epicrisis
        query = (table.id == record_id) & (table.deleted == False)
        record = db(query).select(table.id,
                                  table.person_id,
                                  table.patient_id,
                                  table.date,
                                  table.is_final,
                                  table.vhash,
                                  table.situation,
                                  table.diagnoses,
                                  table.progress,
                                  table.outcome,
                                  table.recommendation,
                                  limitby = (0, 1),
                                  ).first()

        if not record:
            return

        MedPatientModel.set_patient(record)

        now = current.request.utcnow.replace(microsecond=0)
        if record.is_final:
            # Reload the person_id/patient_id as they could have changed
            row = db(query).select(table.person_id,
                                   table.patient_id,
                                   limitby = (0, 1),
                                   ).first()

            # Compute verification hash
            dt = record.date
            dtstr = dt.replace(microsecond=0).isoformat() if dt else "-"
            values = [row.person_id, row.patient_id, dtstr]
            for fn in ("situation", "diagnoses", "progress", "outcome", "recommendation"):
                value = record[fn]
                if not value:
                    value = "-"
                values.append(value)
            vhash = datahash(values)

            # Check if the record has changed
            if vhash != record.vhash:
                # Recompute the verification hash with new date, and update both
                values[2] = now.isoformat()
                vhash = datahash(values)
                record.update_record(date=now, vhash=vhash)
        else:
            # Record is not final
            # => Remove the verification hash, set new date
            record.update_record(date=now, vhash=None)

# =============================================================================
class MedAnamnesisModel(DataModel):
    """ Data Model for case anamnesis / background """

    names = ("med_anamnesis",
             )

    def model(self):

        T = current.T
        # db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        UNKNOWN = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Blood types
        #
        blood_types = {"A+": "A RhD pos",
                       "A-": "A RhD neg",
                       "B+": "B RhD pos",
                       "B-": "B RhD neg",
                       "AB+": "AB RhD pos",
                       "AB-": "AB RhD neg",
                       "O+": "O RhD pos",
                       "O-": "O RhD neg",
                       }

        # ---------------------------------------------------------------------
        # Anamnesis
        #
        tablename = "med_anamnesis"
        define_table(tablename,
                     self.pr_person_id(
                         comment = None,
                         ),
                     CommentsField("allergies",
                                   label = T("Allergies"),
                                   comment = None,
                                   ),
                     CommentsField("chronic",
                                   label = T("Chronic Conditions"),
                                   comment = None,
                                   ),
                     CommentsField("disabilities",
                                   label = T("Disabilities"),
                                   comment = None,
                                   ),
                     CommentsField("history",
                                   label = T("Medical History"),
                                   comment = None,
                                   ),
                     Field("height", "integer",
                           label = T("Height (cm)##body"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(30, 280)),
                           represent = lambda v, row=None: str(v) if v else "-",
                           ),
                     Field("weight", "integer",
                           label = T("Weight (kg)##body"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(2, 300)),
                           represent = lambda v, row=None: str(v) if v else "-",
                           ),
                     Field("blood_type",
                           label = T("Blood Type"),
                           requires = IS_EMPTY_OR(IS_IN_SET(blood_types, zero=UNKNOWN)),
                           represent = represent_option(blood_types, default=UNKNOWN),
                           ),
                     CommentsField(),
                     )

        # Table configuration
        configure(tablename,
                  deletable = False,
                  )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Medical Background"),
            title_display = T("Medical Background"),
            title_update = T("Edit Medical Background"),
            label_delete_button = T("Delete Medical Background"),
            msg_record_created = T("Medical Background added"),
            msg_record_modified = T("Medical Background updated"),
            msg_record_deleted = T("Medical Background deleted"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {}

# =============================================================================
class MedMedicationModel(DataModel):
    """ Data Model to record chronic medication """

    names = ("med_substance",
             "med_medication",
             )

    def model(self):

        T = current.T
        db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # Medicine (generic substance)
        #
        tablename = "med_substance"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Active Substance(s)"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128, minsize=1),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.name" % tablename,
                                                     ),
                                       ],
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     CommentsField(),
                     )

        # Table Configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # Field template
        represent = S3Represent(lookup = tablename)
        substance_id = FieldTemplate("substance_id", "reference %s" % tablename,
                                     label = T("Active Substance(s)"),
                                     ondelete = "RESTRICT",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "%s.id" % tablename,
                                                              represent,
                                                              )),
                                                    )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Active Substance"),
            title_display = T("Active Substance"),
            title_list = T("Active Substances"),
            title_update = T("Edit Active Substance"),
            label_list_button = T("List Active Substances"),
            label_delete_button = T("Delete Active Substance"),
            msg_record_created = T("Active Substance added"),
            msg_record_modified = T("Active Substance updated"),
            msg_record_deleted = T("Active Substance deleted"),
            msg_list_empty = T("No Active Substances currently registered"),
            )

        # ---------------------------------------------------------------------
        # Priorities
        #
        priorities = (("A", T("Vital##medication")),
                      ("B", T("Required")),
                      ("C", T("Optional")),
                      )
        priority_represent = S3PriorityRepresent(priorities,
                                                 {"A": "red",
                                                  "B": "green",
                                                  "C": "lightblue",
                                                  }).represent

        # ---------------------------------------------------------------------
        # Pharmaceutical forms
        #
        pforms = {"TBL": T("Tbl##pharma"),  # tablet
                  "CPS": T("Cps##pharma"),  # capsule
                  "INH": T("Inh##pharma"),  # inhalation
                  "INJ": T("Inj##pharma"),  # injection
                  "INF": T("Inf##pharma"),  # infusion
                  "GTTS": T("Gtts##pharma"), # guttae/drops
                  "OINT": T("Oint##pharma"), # ointment/salve
                  "PULV": T("Pulv##pharma"), # pulver/powder
                  "SUPP": T("Supp##pharma"), # suppository
                  "OTH": T("Other"),
                  }

        # ---------------------------------------------------------------------
        # Application forms
        #
        aforms = (("PO", T("p.o.##medical")), # oral
                  ("SC", T("s.c.##medical")), # subcutaneous
                  ("IV", T("i.v.##medical")), # intravenous
                  ("IM", T("i.m.##medical")), # intramuscular
                  ("PR", T("p.r.##medical")), # per rectal
                  ("PA", T("p.a.##medical")), # partibus affectis
                  ("OTH", T("Other")),
                  )

        # ---------------------------------------------------------------------
        # Dosage units
        #
        dunits = (("MG", T("mg")),
                  ("G", T("g")),
                  ("ML", T("ml")),
                  ("L", T("l")),
                  ("DOS", T("Dose##pharma")),
                  ("IU", T("IU##pharma")),
                  ("UNIT", T("Unit##pharma")),
                  )
        # ---------------------------------------------------------------------
        # Medication (prescription)
        #
        tablename = "med_medication"
        define_table(tablename,
                     self.pr_person_id(
                         comment = None,
                         ),
                     Field("priority",
                           label = T("Priority"),
                           default = "B",
                           requires = IS_IN_SET(priorities, zero=None, sort=False),
                           represent = priority_represent,
                           ),
                     Field("pform",
                           label = T("Form##pharma"),
                           default = "TBL",
                           requires = IS_IN_SET(pforms, zero=None),
                           represent = represent_option(pforms),
                           ),
                     Field("product", length=255,
                           label = T("Preparation / Trade Name"),
                           requires = IS_EMPTY_OR(IS_LENGTH(255, minsize=1)),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     substance_id(),
                     Field("aform",
                           label = T("Application##pharma"),
                           default = "PO",
                           requires = IS_IN_SET(aforms, zero=None, sort=False),
                           represent = represent_option(dict(aforms)),
                           ),
                     Field("dosage", "double",
                           label = T("Dosage"),
                           requires = IS_FLOAT_IN_RANGE(minimum=0.01),
                           represent = lambda v, row=None: IS_FLOAT_AMOUNT.represent(v,
                                                                                     precision = 4,
                                                                                     fixed = False,
                                                                                     ),
                           ),
                     Field("dosage_unit",
                           label = T("Unit"),
                           requires = IS_IN_SET(dunits, zero="", sort=False),
                           represent = represent_option(dict(dunits)),
                           ),
                     Field("scheme",
                           label = T("Scheme"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     DateTimeField("updated_on",
                                   label = T("Updated"),
                                   default = datetime.datetime.utcnow,
                                   update = datetime.datetime.utcnow,
                                   writable = False,
                                   ),
                     Field("is_current", "boolean",
                           label = T("Current"),
                           default = True,
                           represent = BooleanRepresent(labels = False,
                                                        icons = True,
                                                        colors = True,
                                                        ),
                           ),
                     CommentsField(),
                     )

        list_fields = ["priority",
                       "is_current",
                       "pform",
                       "product",
                       "substance_id",
                       "dosage",
                       "dosage_unit",
                       "aform",
                       "scheme",
                       "comments",
                       (T("Updated"), "updated_on"),
                       ]

        configure(tablename,
                  list_fields = list_fields,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Medication"),
            title_display = T("Medication"),
            title_list = T("Medications"),
            title_update = T("Edit Medication"),
            label_list_button = T("List Medications"),
            label_delete_button = T("Delete Medication"),
            msg_record_created = T("Medication added"),
            msg_record_modified = T("Medication updated"),
            msg_record_deleted = T("Medication deleted"),
            msg_list_empty = T("No Medications currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {}

# =============================================================================
class MedVaccinationModel(DataModel):
    """ Data Model to document vaccinations """

    names = ("med_vaccination_type",
             "med_vaccination",
             )

    def model(self):

        T = current.T
        db = current.db

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # Vaccination Type
        #
        tablename = "med_vaccination_type"
        define_table(tablename,
                     Field("name",
                           label = T("Designation"),
                           requires = IS_NOT_EMPTY(),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     Field("vaccine_type",
                           label = T("Vaccine type"),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     CommentsField(),
                     )

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary=("name",),
                                            secondary=("vaccine_type",),
                                            ),
                  onvalidation = self.vaccination_type_onvalidation,
                  )

        # Field template
        represent = S3Represent(lookup = tablename,
                                fields = ["name", "vaccine_type"],
                                labels = "%(name)s (%(vaccine_type)s)",
                                )
        vaccination_type_id = FieldTemplate("type_id", "reference %s" % tablename,
                                            label = T("Vaccination Type"),
                                            ondelete = "RESTRICT",
                                            represent = represent,
                                            requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "%s.id" % tablename,
                                                                  represent,
                                                                  )),
                                            )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Vaccination Type"),
            title_display = T("Vaccination Type"),
            title_list = T("Vaccination Types"),
            title_update = T("Edit Vaccination Type"),
            label_list_button = T("List Vaccination Types"),
            label_delete_button = T("Delete Vaccination Type"),
            msg_record_created = T("Vaccination Type added"),
            msg_record_modified = T("Vaccination Type updated"),
            msg_record_deleted = T("Vaccination Type deleted"),
            msg_list_empty = T("No Vaccination Types currently registered"),
            )

        # ---------------------------------------------------------------------
        # TODO m2m link vaccination_type <=> disease
        #
        # ---------------------------------------------------------------------
        # Vaccination
        #
        tablename = "med_vaccination"
        define_table(tablename,
                     self.pr_person_id(
                         comment = None,
                         ),
                     vaccination_type_id(
                         empty = False,
                         ),
                     Field("product", length=255,
                           label = T("Preparation / Trade Name"),
                           represent = lambda v, row=None: v if v else "-",
                           requires = IS_EMPTY_OR(IS_LENGTH(255, minsize=1)),
                           ),
                     Field("lot_no", length=255,
                           label = T("LOT No."),
                           represent = lambda v, row=None: v if v else "-",
                           requires = IS_EMPTY_OR(IS_LENGTH(255, minsize=1)),
                           ),
                     DateField(),
                     CommentsField(),
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Vaccination"),
            title_display = T("Vaccination"),
            title_list = T("Vaccinations"),
            title_update = T("Edit Vaccination"),
            label_list_button = T("List Vaccinations"),
            label_delete_button = T("Delete Vaccination"),
            msg_record_created = T("Vaccination added"),
            msg_record_modified = T("Vaccination updated"),
            msg_record_deleted = T("Vaccination deleted"),
            msg_list_empty = T("No Vaccinations currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        #return {}

    # ---------------------------------------------------------------------
    @staticmethod
    def vaccination_type_onvalidation(form):
        """
            Form validation of vaccination types:
            - prevent duplicates
        """

        # Get form record id
        record_id = get_form_record_id(form)

        # Get form record data
        table = current.s3db.med_vaccination_type
        data = get_form_record_data(form, table, ["name", "vaccine_type"])

        name = data.get("name")
        if name:
            query = (table.name == name)
            vaccine_type = data.get("vaccine_type")
            if vaccine_type:
                query &= (table.vaccine_type == vaccine_type)
            if record_id:
                query &= (table.id != record_id)
            duplicate = current.db(query).select(table.id, limitby=(0, 1)).first()
            if duplicate:
                error = current.T("Vaccination Type already registered")
                if vaccine_type and "vaccine_type" in form.vars:
                    form.errors.vaccine_type = error
                else:
                    form.errors.name = error

# =============================================================================
class RiskClass:
    """
        Risk class calculator
        - calculates a risk stratification indicator (low=>high) for a set
          of reported vital signs, based on NEWS2 National Early Warning Score
    """

    # Vital parameters used for calculation
    indicators = ("airways", "rr", "o2sat", "o2sub", "hypox", "bp", "hr", "temp", "consc")

    def __init__(self, vitals_id):
        """
            Args:
                vitals_id: the med_vitals record ID
        """

        self._vitals_id = vitals_id
        self._vitals = None

        self._patient_id = None
        self._patient = None

    # -------------------------------------------------------------------------
    @property
    def vitals(self):
        """
            Returns the med_vitals record (lazy property)
        """

        vitals = self._vitals
        if not vitals:
            db = current.db
            table = current.s3db.med_vitals
            query = (table.id == self._vitals_id) & (table.deleted == False)

            fields = [table.id, table.date, table.patient_id] + \
                     [table[fn] for fn in self.indicators]
            vitals = self._vitals = db(query).select(*fields,
                                                     limitby = (0, 1),
                                                     ).first()
        return vitals

    # -------------------------------------------------------------------------
    @property
    def patient_id(self):
        """
            Returns the patient record ID (lazy property)
        """

        patient_id = self._patient_id
        if not patient_id:
            patient_id = self._patient_id = self.vitals.patient_id

        return patient_id

    # -------------------------------------------------------------------------
    @property
    def patient(self):
        """
            Returns the patient record (lazy property)
        """

        patient = self._patient
        if not patient:
            db = current.db
            table = current.s3db.med_patient
            query = (table.id == self.patient_id) & (table.deleted == False)
            patient = self._patient = db(query).select(table.id,
                                                       table.person_id,
                                                       limitby = (0, 1),
                                                       ).first()
        return patient

    # -------------------------------------------------------------------------
    @classmethod
    def calculator(cls, vitals_id):
        """
            Factory method that permits overriding the standard
            class with a custom calculator

            Args:
                vitals_id: the med_vitals record ID
            Returns:
                a RiskClass (or custom subclass thereof) instance
        """

        calculator = current.deployment_settings.get_med_risk_class_calculation()
        if calculator is True:
            calculator = cls # default
        if isinstance(calculator, type):
            calculator = calculator(vitals_id)
        return calculator

    # -------------------------------------------------------------------------
    def parameters(self):
        """
            Extracts the relevant parameters for the calculation, re-using
            certain earlier values if no current value available

            Returns:
                a dict of parameters
        """

        indicators = self.indicators

        vitals = self.vitals
        if not vitals:
            return {fn: None for fn in indicators}

        params = {fn: vitals[fn] for fn in indicators}

        # Re-use earlier values for certain parameters
        reusable = ("airways", "bp", "temp")
        reuse = [fn for fn in reusable if params[fn] is None]
        if reuse:
            # Get all records up to 4 hours before the last record
            earliest = vitals.date - datetime.timedelta(hours=4)
            table = current.s3db.med_vitals
            query = (table.patient_id == self.patient_id) & \
                    (table.date >= earliest) & \
                    (table.deleted == False)
            rows = current.db(query).select(*[table[fn] for fn in reuse],
                                            orderby=(~table.date, ~table.id),
                                            )
            for fn in reuse:
                for row in rows:
                    value = row[fn]
                    if value is not None:
                        params[fn] = value
                        break

        return params

    # -------------------------------------------------------------------------
    def calculate(self):
        """
            Calculates a score and from that determiens the risk class
            for the current vitals record

            Returns:
                the risk class
        """
        # TODO adjust for age

        score, risk = 0, None
        params = self.parameters()

        # A - Airways status
        airways = params.get("airways")
        if airways == "C":
            score += 3
            risk = "M"

        # B - Breathing status
        rr = params.get("rr")
        if rr is not None:
            if rr <= 8 or rr >= 25:
                score += 3
                risk = "M"
            elif rr > 20:
                score += 2
            elif rr < 12:
                score += 1

        o2sub = params.get("o2sub") # O2 Substitution
        if o2sub is None:
            o2sub = 0
        if o2sub > 0:
            score += 2

        o2sat = params.get("o2sat") # O2 Saturation
        if o2sat is not None:
            if params.get("hypox"):
                # Special rules for hypoxic ventilation drive (e.g. COPD)
                if o2sat <= 83:
                    score += 3
                    risk = "M"
                elif o2sat < 86:
                    score += 2
                elif o2sat < 88:
                    score += 1
                elif o2sub > 0:
                    if o2sat >= 97:
                        score += 3
                        risk = "M"
                    elif o2sat > 94:
                        score += 2
                    elif o2sat > 92:
                        score += 1
            else:
                if o2sat <= 92:
                    score += 3
                    risk = "M"
                elif o2sat < 94:
                    score += 2
                elif o2sat < 96:
                    score += 1

        # C - Circulation
        sbp, _ = med_parse_bp(params.get("bp"))
        if sbp is not None:
            if sbp <= 90 or sbp >= 220:
                score += 3
                risk = "M"
            elif sbp <= 100:
                score += 2
            elif sbp <= 110:
                score += 1

        hr = params.get("hr")
        if hr is not None:
            if hr <= 40 or hr > 130:
                score += 3
                risk = "M"
            elif hr > 110:
                score += 2
            elif hr <= 50 or hr > 90:
                score += 1

        # D - Disability
        consc = params.get("consc")
        if consc and consc != "A":
            score += 3
            risk = "M"

        # E - Exposure
        temp = params.get("temp")
        if temp is not None:
            if temp <= 35.0:
                score += 3
                risk = "M"
            elif temp > 39.0:
                score += 2
            elif temp <= 36.0 or temp > 38.0:
                score += 1

        if score >= 7:
            risk = "C"
        elif score >= 5:
            risk = "H"
        elif not risk:
            risk = "L"

        return risk

    # -------------------------------------------------------------------------
    def update_risk(self):
        """
            Updates the EWS score for the vitals record
        """

        risk = self.calculate()

        if self.vitals:
            self.vitals.update_record(risk_class=risk)

# =============================================================================
class AnalysisDataSeries(DataSeries):
    """ Data series handler for analysis results """

    # TODO extend with form data lookup
    # TODO extend with form data validation + processing

    # -------------------------------------------------------------------------
    def results(self, start=0, limit=None):
        """
            Extract results from context resource and generate data dict

            Args:
                start: the start index of the page
                limit: the number of records in the page

            Returns:
                a JSON-serializable dict like:
                {d: [[id, iso_date, title], ...],                           // date/time slots
                 g: [[id, title], ...]                                      // series groups
                 s: [[id, group-id, title, full-name, range, unit], ...]    // series
                 v: {slot-id:                                               // values
                      {series-id: [value, status, reason, out-of-range], ...}
                    },
                 }
        """

        resource = self.resource

        # Filter out invalid analyses
        resource.add_filter(FS("invalid") == False)

        # Select all relevant records
        records = resource.select(["id", "date", "invalid"],
                                  start = start,
                                  limit = limit,
                                  orderby = "date desc",
                                  represent = True,
                                  raw_data = True,
                                  ).rows

        # Build date/time slots
        analysis_ids, dates = set(), []
        for record in records:
            raw = record._row
            record_id = raw["med_analysis.id"]
            analysis_ids.add(record_id)
            dates.append((record_id,
                          raw["med_analysis.date"].isoformat(),
                          record["med_analysis.date"],
                          ))

        # Lookup groups, series and values for the slots
        parameters, series, groups = self.get_series(analysis_ids)
        values = self.get_values(analysis_ids, parameters)

        return {"d": dates, "g": groups, "s": series, "v": values}

    # -------------------------------------------------------------------------
    def get_series(self, analysis_ids):
        """
            Look up all series (parameters)

            Args:
                analysis_ids: the analysis record IDs
            Returns:
                tuple (series, groups)

                series = [[parameter-id, group-id, title, full-name, range, unit], ...]
                groups = [[group-id, group-title], ...]
        """

        db = current.db
        s3db = current.s3db

        # Sub-query for all parameters used in analyses
        rtable = s3db.med_analysis_result
        query = (rtable.analysis_id.belongs(analysis_ids)) & \
                (rtable.deleted == False)
        parameter_ids = db(query)._select(rtable.parameter_id)

        # Look up parameter details
        ptable = s3db.med_parameter
        query = (ptable.id.belongs(parameter_ids)) & \
                (ptable.deleted == False)
        rows = db(query).select(ptable.id,
                                ptable.name,
                                ptable.abrv,
                                ptable.parameter_group_id,
                                ptable.qualitative,
                                ptable.values_normal,
                                ptable.precsn,
                                ptable.um,
                                orderby = (ptable.sample_type_id, ptable.name),
                                )
        parameters = {row.id: row for row in rows}

        # Represent as series
        series, group_ids = [], set()
        for row in rows:
            if row.qualitative:
                normal, unit = "", ""
            else:
                normal = self.represent_normal_range(row.values_normal)
                unit = row.um
            series.append([row.id,
                           row.parameter_group_id,
                           row.abrv or row.name,
                           row.name,
                           normal,
                           unit,
                           ])
            group_ids.add(row.parameter_group_id)

        # Look up parameter group details
        gtable = s3db.med_parameter_group
        query = (gtable.id.belongs(group_ids))
        rows = db(query).select(gtable.id, gtable.name, orderby=gtable.name)
        groups = [[row.id, row.name] for row in rows]

        return parameters, series, groups

    # -------------------------------------------------------------------------
    @classmethod
    def get_values(cls, analysis_ids, parameters):
        """
            Get all analysis results

            Args:
                analysis_ids: the med_analysis record IDs
                parameters: details of the parameters used in these analysis,
                            as dict {id: Row}, must contain qualitative-flag
                            and precsn
            Returns:
                a dict {analysis-id:
                         {parameter-id: [value, status, reason, out-of-range],
                          }
                        }
        """

        db = current.db
        s3db = current.s3db

        # Use numeric representations of statuses
        statuses = {"PENDING": 0,
                    "PRELIMINARY": 1,
                    "FINAL": 2,
                    "FAILED": 3,
                    }

        table = s3db.med_analysis_result
        query = (table.analysis_id.belongs(analysis_ids)) & \
                (table.deleted == False)
        rows = db(query).select(table.analysis_id,
                                table.parameter_id,
                                table.result,
                                table.result_numeric,
                                table.status,
                                table.status_reason,
                                table.abnormal,
                                )

        results = {}
        for row in rows:
            analysis_id = row.analysis_id
            if analysis_id in results:
                result = results[analysis_id]
            else:
                result = results[analysis_id] = {}

            parameter_id = row.parameter_id
            parameter = parameters.get(parameter_id)

            status = statuses.get(row.status)
            if status is None:
                continue

            value = str(row.result)

            # Representations of pending, failed and numeric values
            if status == 3:
                value = "***" # Failed
            elif status == 0:
                value = "---" # Pending
            elif parameter and not parameter.qualitative and row.result_numeric is not None:
                # Represent quantitative value as float with fixed precision
                value = IS_FLOAT_AMOUNT.represent(row.result_numeric,
                                                  parameter.precsn or 0,
                                                  True,
                                                  )

            result[parameter_id] = [value,
                                    status,
                                    row.status_reason or "",
                                    int(row.abnormal),
                                    ]

        return results

    # -------------------------------------------------------------------------
    def represent_normal_range(self, vn):
        """
            Represent normal parameter ranges

            Args:
                vn: the normal range, a tuple [min, max] where either can be None

            Returns:
                a string representation of the range
        """

        if isinstance(vn, (list, tuple)) and len(vn) == 2:
            minimum, maximum = vn
        else:
            minimum = maximum = None

        if maximum is not None and minimum is not None:
            repr_str = "%s - %s" % (minimum, maximum)
        elif maximum is not None:
            repr_str = "< %s" % maximum
        elif minimum is not None:
            repr_str = "> %s" % minimum
        else:
            repr_str = ""

        return repr_str

# =============================================================================
class IS_BLOOD_PRESSURE(Validator):

    def validate(self, value, record_id=None):
        """
            Validator for blood pressure expressions

            Args:
                value: the input value
                record_id: the current record ID (unused, for API compatibility)

            Returns:
                the blood pressure expression

            Notes:
                - automatically reverses wrong DIA/SYS order if given two values
        """

        sbp, dbp = med_parse_bp(value)
        if sbp and dbp:
            if sbp - dbp < 10:
                raise ValidationError(current.T("Implausible Value"))
            value = "%s/%s" % (sbp, dbp)
        elif value and sbp is None:
            raise ValidationError(current.T("Enter blood pressure like SYS/DIA, or at least the systolic value"))

        return value

# =============================================================================
class med_UnitRepresent(S3Represent):
    """ Representation of medical units """

    def __init__(self, *, show_org=None, show_link=False):
        """
            Args:
                show_org: include the organisation name (True|False)
                show_link: represent as link to the unit
        """

        super().__init__(lookup = "med_unit",
                         show_link = show_link,
                         )

        self._show_org = show_org

    # -------------------------------------------------------------------------
    @property
    def show_org(self):
        """
            Determines whether to include the organisation name in
            the representation; defaults to True when the user can
            read med_units from more than one organisation; can be
            overridden by explicit True|False constructor parameter
            "show_org"

            Returns:
                boolean
        """

        show_org = self._show_org
        if show_org is None:

            permissions = current.auth.permission
            permitted_realms = permissions.permitted_realms("med_unit", "read")

            if permitted_realms is None:
                show_org = True
            elif permitted_realms:
                orgs = current.s3db.pr_get_entities(permitted_realms,
                                                    types = ["org_organisation"],
                                                    represent = False,
                                                    )
                show_org = len(orgs) != 1
            else:
                show_org = True

            self._show_org = show_org

        return show_org

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            Args:
                key: the key Field
                values: the values
                fields: list of fields to look up (unused)
        """

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        table = self.table
        fields = [table.id, table.name]

        if self.show_org:
            # Left join org?
            otable = current.s3db.org_organisation
            left = otable.on(otable.id == table.organisation_id)
            fields.append(otable.name)
        else:
            left = None

        rows = current.db(query).select(*fields, left=left, limitby=(0, count))
        self.queries += 1

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Generates a string representation from a Row

            Args:
                row: the Row
        """

        if self.show_org and hasattr(row, "org_organisation"):
            org_name = row.org_organisation.name
            row = row.med_unit
        else:
            org_name = None

        reprstr = "%s" % row.name
        if org_name:
            reprstr = "%s (%s)" % (reprstr, org_name)

        return reprstr

# =============================================================================
class med_PatientRepresent(S3Represent):
    """ Representation of treatment occasions """

    def represent_row(self, row):
        """
            Generates a string representation from a Row

            Args:
                row: the Row
        """

        if hasattr(row, "med_patient"):
            row = row.med_patient

        formatted = DIV()

        # Include refno if present in row
        if "refno" in row:
            formatted.append(SPAN(row.refno, _class="med-refno"))

        # Decide CSS class by status, if present in row
        active = "status" in row and row.status in (("ARRIVED", "TREATMENT"))
        css = "med-reason" if active else "med-reason-historical"

        formatted.append(SPAN(s3_truncate(row.reason), _class=css))
        return formatted

# =============================================================================
class med_SampleRepresent(S3Represent):
    """ Representation of samples """

    def __init__(self, show_link=False):
        """
            Args:
                show_link: render as link to the sample
        """

        super().__init__(lookup = "med_sample",
                         show_link = show_link,
                         )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            Args:
                key: the key Field
                values: the values
                fields: list of fields to look up (unused)
        """

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        table = self.table

        fields = [table.id,
                  table.person_id,
                  table.patient_id,
                  table.sample_type_id,
                  table.date,
                  ]

        rows = current.db(query).select(limitby=(0, count), *fields)
        self.queries += 1

        # Bulk-represent human_resource_ids
        type_ids = [row.sample_type_id for row in rows]
        table.sample_type_id.represent.bulk(type_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            Args:
                row: the Row
        """

        table = self.table

        date = table.date.represent(row.date)
        sample_type = table.sample_type_id.represent(row.sample_type_id)

        reprstr = "[%s] %s" % (date, sample_type)

        return reprstr

# =============================================================================
class med_DocEntityRepresent(S3Represent):
    """ Module context-specific representation of doc-entities """

    def __init__(self, *,
                 patient_label = None,
                 show_link = False,
                 ):
        """
            Args:
                patient_label: label for patient records (default: "Visit")
                show_link: show representation as clickable link
        """

        super().__init__(lookup = "doc_entity",
                         show_link = show_link,
                         )

        T = current.T

        if patient_label:
            self.patient_label = patient_label
        else:
            self.patient_label = T("Visit")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            Args:
                key: the key Field
                values: the values
                fields: unused (retained for API compatibility)
        """

        db = current.db
        s3db = current.s3db

        table = self.table

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        rows = db(query).select(table.doc_id,
                                table.instance_type,
                                limitby = (0, count),
                                orderby = table.instance_type,
                                )
        self.queries += 1

        # Sort by instance type
        doc_ids = {}
        for row in rows:
            doc_id = row.doc_id
            instance_type = row.instance_type
            if instance_type not in doc_ids:
                doc_ids[instance_type] = {doc_id: row}
            else:
                doc_ids[instance_type][doc_id] = row

        for instance_type in ("med_patient",):

            doc_entities = doc_ids.get(instance_type)
            if not doc_entities:
                continue

            # The instance table
            itable = s3db[instance_type]

            # Look up person and instance data
            query = itable.doc_id.belongs(set(doc_entities.keys()))
            fields = [itable.id,
                      itable.doc_id,
                      ]
            if instance_type == "med_patient":
                fields.extend((itable.date,
                               itable.reason,
                               ))
            irows = db(query).select(*fields)
            self.queries += 1

            # Add the person+instance data to the entity rows
            for irow in irows:
                entity = doc_entities[irow.doc_id]
                entity[instance_type] = irow

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            Args:
                row: the Row
        """

        instance_type = row.instance_type

        if instance_type == "med_patient":
            patient = row.med_patient
            title = "%s %s" % (current.calendar.format_date(patient.date, local=True),
                               patient.reason,
                               )
            label = self.patient_label
        else:
            title = "%s" % row.doc_id
            label = T("unknown")

        return "%s (%s)" % (s3_str(title), s3_str(label))

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            Args:
                k: the key (doc_entity.doc_id)
                v: the representation of the key
                row: the row with this key
        """

        link = v

        if row:
            if row.instance_type == "med_patient":
                url = URL(c = "med",
                          f = "patient",
                          args = [row.med_patient.id,
                                  ],
                          extension="",
                          )
                link = A(v, _href=url)

        return link

# =============================================================================
class med_StatusListLayout(S3DataListLayout):
    """ List layout for patient status reports (on tab of patient) """

    def __init__(self, profile=None):

        super().__init__(profile=profile)

        self.editable = []
        self.visible = []

        self.patient_id = None
        self.person_id = None

    # -------------------------------------------------------------------------
    def prep(self, resource, records):
        """
            Bulk lookups for cards

            Args:
                resource: the resource
                records: the records as returned from CRUDResource.select
        """

        record_ids = [r["med_status.id"] for r in records]

        user = current.auth.user
        user_id = user.id if user else None

        db = current.db
        table = current.s3db.med_status

        # Visible only if final or created by the current user
        query = table.id.belongs(record_ids) & \
                ((table.is_final==True) | (table.created_by==user_id)) & \
                (table.deleted == False)
        rows = db(query).select(table.id, table.patient_id, table.person_id)
        visible = self.visible = [row.id for row in rows]
        if rows:
            row = rows.first()
            self.patient_id = row.patient_id
            self.person_id = row.person_id

        # Editable only if not final and created by the current user
        query = table.id.belongs(visible) & \
                (table.is_final==False) & \
                (table.created_by==user_id) & \
                (table.deleted == False)
        rows = db(query).select(table.id, table.patient_id)
        self.editable = [row.id for row in rows]

    # -------------------------------------------------------------------------
    def render_header(self, list_id, item_id, resource, rfields, record):
        """
            Render the card header

            Args:
                list_id: the HTML ID of the list
                item_id: the HTML ID of the item
                resource: the CRUDResource to render
                rfields: the S3ResourceFields to render
                record: the record as dict
        """

        record_id = record["_row"]["med_status.id"]
        editable = record_id in self.editable

        header = DIV(_class="med-status-header")
        if editable:
            header.add_class("editable")

        # Include treatment occasion (patient_id), if available
        if "med_status.patient_id" in record:
            header.append(DIV(record["med_status.patient_id"],
                              _class = "meta meta-fix",
                              ))

        # Show date and original author
        for colname in ("med_status.date", "med_status.created_by"):
            if colname not in record:
                continue
            content = DIV(record[colname], _class="meta")
            header.append(content)

        # Render roolbox if editable
        if editable:
            toolbox = self.render_toolbox(list_id, resource, record)
            if toolbox:
                header.append(toolbox)

        return header

    # -------------------------------------------------------------------------
    def render_body(self, list_id, item_id, resource, rfields, record):
        """
            Render the card body

            Args:
                list_id: the HTML ID of the list
                item_id: the HTML ID of the item
                resource: the CRUDResource to render
                rfields: the S3ResourceFields to render
                record: the record as dict
        """

        record_id = record["_row"]["med_status.id"]

        body = DIV(_class="med-status")
        if record_id in self.editable:
            body.add_class("editable")

        if record_id in self.visible:
            for rfield in rfields:
                if rfield.colname in ("med_status.situation",
                                      "med_status.background",
                                      "med_status.assessment",
                                      "med_status.recommendation",
                                      ):
                    content = self.render_column(item_id, rfield, record)
                    if content:
                        body.append(content)
        else:
            T = current.T
            body.append(P(T("Report not yet completed"), _class="pending"))
            body.add_class("pending")

        return body

    # -------------------------------------------------------------------------
    def render_toolbox(self, list_id, resource, record):
        """
            Render the toolbox

            Args:
                list_id: the HTML ID of the list
                resource: the CRUDResource to render
                record: the record as dict
        """

        table = resource.table
        tablename = resource.tablename
        # record_id = record[str(resource._id)]
        record_id = record["_row"]["med_status.id"]

        toolbox = DIV(_class = "edit-bar fright")

        # Look up the patient ID
        f = current.request.function
        if f == "person":
            person_id = self.person_id
            update_url = URL(c = "med",
                             f = "person",
                             args = [person_id, "med_status", record_id, "update.popup"],
                             vars = {"refresh": list_id,
                                     "record": record_id,
                                     "profile": self.profile,
                                     },
                             )
        elif f == "patient":
            patient_id = self.patient_id
            update_url = URL(c = "med",
                             f = "patient",
                             args = [patient_id, "status", record_id, "update.popup"],
                             vars = {"refresh": list_id,
                                     "record": record_id,
                                     "profile": self.profile,
                                     },
                             )
        else:
            return None

        has_permission = current.auth.s3_has_permission

        if has_permission("update", table, record_id=record_id):
            btn = A(ICON("edit"),
                    _href = update_url,
                    _class = "s3_modal",
                    _title = get_crud_string(tablename, "title_update"),
                    )
            toolbox.append(btn)

        if has_permission("delete", table, record_id=record_id):
            btn = A(ICON("delete"),
                    _class = "dl-item-delete",
                    _title = get_crud_string(tablename, "label_delete_button"),
                    )
            toolbox.append(btn)

        return toolbox

    # ---------------------------------------------------------------------
    def render_column(self, item_id, rfield, record):
        """
            Render a data column.

            Args:
                item_id: the HTML element ID of the item
                rfield: the S3ResourceField for the column
                record: the record (from CRUDResource.select)
        """

        colname = rfield.colname
        if colname not in record:
            return None

        raw = record["_row"]
        if rfield.colname in ("med_status.situation",
                              "med_status.background",
                              "med_status.assessment",
                              "med_status.recommendation",
                              ):
            # Use raw data
            value = raw[colname]
            if value:
                value = value.strip()
        else:
            value = record[colname]

        if not value:
            return None

        value_id = "%s-%s" % (item_id, rfield.colname.replace(".", "_"))

        label = LABEL("%s:" % rfield.label,
                      _for = value_id,
                      _class = "dl-field-label")

        value = P(value,
                  _id = value_id,
                  _class = "dl-field-value")

        return TAG[""](label, value)

# =============================================================================
class med_PatientListLayout(S3DataListLayout):
    """ List layout for visits (on tab of person) """

    def __init__(self, profile=None):

        super().__init__(profile=profile)

        T = current.T

        self.list_fields = ["person_id",
                            "unit_id",
                            (T("Reason for visit"), "patient_link"),
                            "refno",
                            "date",
                            "reason",
                            "status",
                            "hazards",
                            "hazards_advice",
                            ]
        if current.auth.permission.has_permission("read", "med_epicrisis"):
            self.list_fields.extend(["epicrisis.id",
                                     "epicrisis.situation",
                                     "epicrisis.diagnoses",
                                     "epicrisis.progress",
                                     "epicrisis.outcome",
                                     "epicrisis.recommendation",
                                     "epicrisis.is_final",
                                     ])

        self.patient_link = current.auth.permission.has_permission("read",
                                                                   c="med",
                                                                   f="patient",
                                                                   t="med_patient",
                                                                   )

    # -------------------------------------------------------------------------
    # def prep(self, resource, records):
    #     """
    #         Bulk lookups for cards
    #
    #         Args:
    #             resource: the resource
    #             records: the records as returned from CRUDResource.select
    #     """
    #
    #     db = current.db
    #     s3db = current.s3db
    #
    #     record_ids = [r["med_patient.id"] for r in records]
    #
    #     # Look up epicrises
    #     etable = s3db.med_epicrisis
    #     query = current.auth.s3_accessible_query("read", "med_epicrisis") & \
    #             (etable.patient_id.belongs(record_ids)) & \
    #             (etable.deleted == False)
    #     rows = db(query).select(etable.id,
    #                             etable.patient_id,
    #                             etable.situation,
    #                             etable.diagnoses,
    #                             etable.progress,
    #                             etable.outcome,
    #                             etable.recommendation,
    #                             etable.is_final,
    #                             )
    #     for row in rows:
    #         self.epicrises[row.patient_id] = row
    #
    # -------------------------------------------------------------------------
    def render_header(self, list_id, item_id, resource, rfields, record):
        """
            Render the card header

            Args:
                list_id: the HTML ID of the list
                item_id: the HTML ID of the item
                resource: the CRUDResource to render
                rfields: the S3ResourceFields to render
                record: the record as dict
        """

        header = DIV(_class="med-status-header")

        # Show ref.no
        if "med_patient.refno" in record:
            header.append(DIV(SPAN(record["med_patient.refno"], _class="med-refno"), _class="meta"))

        # Show date, hazard icons and status
        for colname in ("med_patient.date",
                        "med_patient.unit_id",
                        "med_patient.status",
                        "med_patient.hazards",
                        ):
            if colname not in record:
                continue
            content = DIV(record[colname], _class="meta")
            if colname == "med_patient.unit_id":
                content.add_class("meta-fix")
            header.append(content)

        # Render toolbox
        toolbox = self.render_toolbox(list_id, resource, record)
        if toolbox:
            header.append(toolbox)

        return header

    # -------------------------------------------------------------------------
    def render_body(self, list_id, item_id, resource, rfields, record):
        """
            Render the card body

            Args:
                list_id: the HTML ID of the list
                item_id: the HTML ID of the item
                resource: the CRUDResource to render
                rfields: the S3ResourceFields to render
                record: the record as dict
        """

        body = DIV(_class="med-status")
        if record["_row"]["med_patient.status"] in ("ARRIVED", "TREATMENT"):
            body.add_class("editable")

        cols = {rfield.colname: rfield for rfield in rfields}

        reason = "med_patient.patient_link" if self.patient_link else "med_patient.reason"
        epicrisis = []

        for colname in (reason,
                        "med_patient.hazards_advice",
                        "med_epicrisis.situation",
                        "med_epicrisis.diagnoses",
                        "med_epicrisis.progress",
                        "med_epicrisis.outcome",
                        "med_epicrisis.recommendation",
                        ):
            if colname not in cols:
                continue
            value = record["_row"][colname]
            if isinstance(value, str):
                value = value.strip()
            if not value:
                continue
            rfield = cols[colname]
            content = self.render_column(item_id, cols[colname], record)
            if content:
                if rfield.tname == "med_epicrisis":
                    epicrisis.append(content)
                else:
                    body.append(content)

        if epicrisis:
            # Wrap epicrisis in DIV and add contents-toggle
            T = current.T
            content = DIV(*epicrisis,
                          A(T("Show Details"), _class="action-lnk dl-toggle-contents"),
                          A(T("Hide Details"), _class="action-lnk dl-toggle-contents hide"),
                          _class = "med-epicrisis",
                          )
            body.append(content)

        return body

    # -------------------------------------------------------------------------
    def render_toolbox(self, list_id, resource, record):
        """
            Render the toolbox

            Args:
                list_id: the HTML ID of the list
                resource: the CRUDResource to render
                record: the record as dict
        """

        table = resource.table
        tablename = resource.tablename

        raw = record["_row"]
        record_id = raw["med_patient.id"]
        person_id = raw["med_patient.person_id"]

        toolbox = DIV(_class = "edit-bar fright")

        # Look up the patient ID
        f = current.request.function
        if f == "person" and person_id:
            update_url = URL(c = "med",
                             f = "person",
                             args = [person_id, "patient", record_id, "update.popup"],
                             vars = {"refresh": list_id,
                                     "record": record_id,
                                     "profile": self.profile,
                                     },
                             )
        elif f == "patient":
            update_url = URL(c = "med",
                             f = "patient",
                             args = [record_id, "update.popup"],
                             vars = {"refresh": list_id,
                                     "record": record_id,
                                     "profile": self.profile,
                                     },
                             )
        else:
            return None

        has_permission = current.auth.s3_has_permission

        if has_permission("update", table, record_id=record_id):
            btn = A(ICON("edit"),
                    _href = update_url,
                    _class = "s3_modal",
                    _title = get_crud_string(tablename, "title_update"),
                    )
            toolbox.append(btn)

        if has_permission("delete", table, record_id=record_id):
            btn = A(ICON("delete"),
                    _class = "dl-item-delete",
                    _title = get_crud_string(tablename, "label_delete_button"),
                    )
            toolbox.append(btn)

        return toolbox

    # ---------------------------------------------------------------------
    def render_column(self, item_id, rfield, record):
        """
            Render a data column.

            Args:
                item_id: the HTML element ID of the item
                rfield: the S3ResourceField for the column
                record: the record (from CRUDResource.select)
        """

        colname = rfield.colname
        if colname not in record:
            return None

        raw = record["_row"]

        if colname in ("med_epicrisis.situation",
                       "med_epicrisis.diagnoses",
                       "med_epicrisis.progress",
                       "med_epicrisis.outcome",
                       "med_epicrisis.recommendation",
                       "med_status.situation",
                       ):
            value = raw[colname]
            if value:
                value = value.strip()
        else:
            value = record[colname]

        if not value:
            return None

        value_id = "%s-%s" % (item_id, rfield.colname.replace(".", "_"))

        label = LABEL("%s:" % rfield.label,
                      _for = value_id,
                      _class = "dl-field-label",
                      )

        value = P(value,
                  _id = value_id,
                  _class = "dl-field-value",
                  )

        if rfield.tname == "med_epicrisis":
            # Hide epicrisis details initially
            label.add_class("hide")
            value.add_class("hide")
            # Mark as preliminary if not final yet
            if not raw.get("med_epicrisis.is_final"):
                value.add_class("med-preliminary")
        if colname in ("med_patient.reason", "med_patient.patient_link"):
            value.add_class("med-reason")

        return TAG[""](label, value)

# =============================================================================
def med_parse_bp(bpstr):
    """
        Returns the systolic/diastolic blood pressure values from a BP string

        Args:
            bpstr: the blood pressure as string expression, e.g. "120/80"
        Returns:
            tuple (sbp, dbp)

        Notes:
            - dbp can be None if the string only contains a single value
            - sbp and dbp are both None if the string expression is invalid
    """

    sbp, dbp = None, None

    if bpstr:
        match = re.match(BP, bpstr)
        if match:
            try:
                sbp = int(match.group(1))
            except (ValueError, TypeError):
                pass
            try:
                dbp = int(match.group(2))
            except (ValueError, TypeError):
                pass
            if sbp and dbp and sbp < dbp:
                sbp, dbp = dbp, sbp

    return sbp, dbp

# =============================================================================
def med_configure_unit_id(table, patient=None):
    """
        Configure choices for the unit/area foreign keys in patient form

        Args:
            table: the med_patient table
            patient: the current patient record (Row)
    """

    db = current.db
    s3db = current.s3db

    utable = s3db.med_unit
    unit_id = None

    query = (utable.obsolete == False)

    # Check which units the user has permission to create patients for
    realms = current.auth.permission.permitted_realms("med_patient", "create")
    if realms is not None:
        query &= (utable.pe_id.belongs(realms))
    if patient and patient.unit_id:
        query |= (utable.id == patient.unit_id)
    dbset = db(query)
    units = dbset(utable.deleted == False).select(utable.id,
                                                  limitby = (0, 2),
                                                  )
    single_unit = len(units) == 1
    if single_unit:
        # Only one unit permitted
        unit_id = units.first().id

    field = table.unit_id
    if unit_id:
        # Set default unit_id
        field.default = unit_id
        #field.readable = False # really?
        field.writable = False

        # Limit area_id choices to this unit
        areaset = db(s3db.med_area.unit_id == unit_id)
        area_id = table.area_id
        area_id.requires = IS_EMPTY_OR(IS_ONE_OF(areaset, "med_area.id",
                                                 area_id.represent,
                                                 ))
    else:
        # Configure unit_id choices
        field.requires = IS_ONE_OF(dbset, "med_unit.id", field.represent)

        # Set dynamic options filter for area_id
        script = '''$.filterOptionsS3({
 'trigger':'unit_id',
 'target':'area_id',
 'lookupPrefix':'med',
 'lookupResource':'area',
 'optional':true
})'''
        jquery_ready = current.response.s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    return not single_unit

# =============================================================================
def med_get_current_patient_id(person_id):
    """
        Returns the ID of the latest active patient record for a person

        Args:
            person_id: the person record ID

        Returns:
            patient_id, or None if no active patient record exists
    """

    db = current.db
    s3db = current.s3db

    open_status = ("ARRIVED", "TREATMENT")

    table = s3db.med_patient
    query = (table.person_id == person_id) & \
            (table.status.belongs(open_status)) & \
            (table.invalid == False) & \
            (table.deleted == False)
    patient = db(query).select(table.id, limitby=(0, 1), orderby=~table.date).first()

    return patient.id if patient else None

# =============================================================================
def med_patient_header(record):
    """
        Represents a patient record as name, gender and age of the person;
        for patient file rheader

        Args:
            record: the patient record

        Returns:
            HTML
    """

    T = current.T
    s3db = current.s3db

    # Look up person record
    try:
        person_id = record.person_id
    except AttributeError:
        person_id = None

    # Room/Area
    if record.area_id:
        table = s3db.med_patient
        area = SPAN(table.area_id.represent(record.area_id),
                    _title = T("Place##placement"),
                    _class = "med-area",
                    )
    else:
        area = ""

    # Visit Number
    if record.refno:
        refno = SPAN(record.refno,
                     _title = T("Visit #"),
                     _class = "med-refno",
                     )
    else:
        refno = ""

    # Handle unregistered persons
    if not person_id:
        person = record.person
        label = T("Unregistered Person")
        return TAG[""](area,
                       refno,
                       SPAN(person if person else label,
                            _class = "med-unregistered",
                            _title = label,
                            ),
                       )

    # Look up the person record
    ptable = s3db.pr_person
    person = current.db(ptable.id==person_id).select(ptable.id,
                                                     ptable.first_name,
                                                     ptable.middle_name,
                                                     ptable.last_name,
                                                     ptable.gender,
                                                     ptable.date_of_birth,
                                                     ptable.deceased,
                                                     ptable.date_of_death,
                                                     limitby = (0, 1),
                                                     ).first()
    if not person:
        return "?"

    # Age representation
    pr_age = current.s3db.pr_age
    age = pr_age(person)
    if age is None:
        age = "?"
        unit = T("years")
    elif age == 0:
        age = pr_age(record, months=True)
        unit = T("months") if age != 1 else T("month")
    else:
        unit = T("years") if age != 1 else T("year")
    if person.deceased:
        unit = "%s (%s)" % (unit, T("deceased"))

    # Gender icon
    icons = {2: "fa fa-venus",
             3: "fa fa-mars",
             4: "fa fa-transgender-alt",
             }
    icon = I(_class=icons.get(person.gender, "fa fa-genderless"))

    # Name
    fullname = A(s3_fullname(person, truncate=False),
                 _href = URL(c="med", f="person", args=[person.id]),
                 _class = "med-patient",
                 )

    # Combined representation
    patient = TAG[""](area,
                      refno,
                      fullname,
                      SPAN(icon, "%s %s" % (age, unit), _class="client-gender-age"),
                      )
    return patient

# -----------------------------------------------------------------------------
def med_rheader(r, tabs=None):
    """ MED resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T
        settings = current.deployment_settings

        if tablename == "pr_person":
            if not tabs:
                patient_id = s3db.med_get_current_patient_id(record.id)
                highlight = {"_class": "emphasis"} if patient_id else {}
                has_permission = current.auth.s3_has_permission
                tabs = [(T("Basic Details"), None),
                        (T("Background"), "anamnesis"),
                        (T("Vaccinations"), "vaccination"),
                        (T("Medication"), "medication"),
                        (T("Visits"), "patient"),
                        (T("Vital Signs"), "vitals", highlight),
                        (T("Status"), "med_status", highlight),
                        (T("Treatment"), "treatment", highlight),
                        ]
                # Add document-tab only if the user is permitted to
                # access documents through the med/patient controller
                # (otherwise, the tab would always be empty)
                if has_permission("read", "doc_document", c="med", f="patient"):
                    tabs.append((T("Documents"), "document/"))

            rheader_fields = [["date_of_birth"],
                              ]
            rheader_title = s3_fullname

        elif tablename == "med_patient":

            person_id = record.person_id

            if not tabs:
                tabs = [(T("Overview"), None),
                        # Background [viewing]
                        # Vaccinations [viewing]
                        # Medication [viewing]
                        (T("Vital Signs"), "vitals", {"_class": "emphasis"}),
                        # (T("Parameters"), "analysis", {"_class": "emphasis"}, "results"), # TESTING
                        (T("Status"), "status", {"_class": "emphasis"}),
                        (T("Treatment"), "treatment", {"_class": "emphasis"}),
                        (T("Epicrisis"), "epicrisis"),
                        (T("Documents"), "document"),
                        ]
                if person_id:
                    tabs[1:1] = [(T("Background"), "anamnesis/"),
                                 (T("Medication"), "medication/"),
                                 (T("Vaccinations"), "vaccination/"),
                                 ]

            # Load the person record
            ptable = s3db.pr_person
            dtable = s3db.pr_person_details
            if person_id:
                left = dtable.on((dtable.person_id == ptable.id) & \
                                 (dtable.deleted == False))
                row = db(ptable.id == person_id).select(ptable.pe_label,
                                                        ptable.date_of_birth,
                                                        dtable.nationality,
                                                        left = left,
                                                        limitby = (0, 1),
                                                        ).first()
            else:
                row = None

            if row:
                person, details = row.pr_person, row.pr_person_details
                label = lambda i: person.pe_label
                dob = lambda i: ptable.date_of_birth.represent(person.date_of_birth)
                nationality = lambda i: dtable.nationality.represent(details.nationality)
            else:
                label = dob = nationality = lambda i: "-"

            if settings.get_med_use_pe_label():
                pdata = ((T("ID"), label),
                         (T("Date of Birth"), dob),
                         (T("Nationality"), nationality),
                         )
            else:
                pdata = ((T("Date of Birth"), dob),
                         (T("Nationality"), nationality),
                         ("", None),
                         )

            reason = lambda i: SPAN(i.reason if i.reason else "-", _class="med-reason")

            rheader_fields = [[(T("Reason for visit"), reason, 3)],
                              ["date", pdata[0], "hazards"],
                              ["priority", pdata[1], "hazards_advice"],
                              ["status", pdata[2]],
                              ]
            rheader_title = med_patient_header
            # TODO invalid-hint

        elif tablename == "med_unit":
            if not tabs:
                if settings.get_med_area_label() == "area":
                    areas_label = T("Treatment Areas")
                else:
                    areas_label = T("Rooms")
                tabs = [(T("Basic Details"), None),
                        (areas_label, "area"),
                        (T("Current Visits"), "patient"),
                        ]

            rheader_fields = [["organisation_id"],
                              ["site_id"],
                              ]
            rheader_title = "name"

        else:
            return None

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table=resource.table, record=record)

    return rheader

# END =========================================================================
