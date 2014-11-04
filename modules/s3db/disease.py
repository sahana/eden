# -*- coding: utf-8 -*-

__all__ = ("DiseaseDataModel",
           "CaseTrackingModel",
           "ContactTracingModel",
           "disease_rheader",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# Monitoring upgrades {new_level:previous_levels}
MONITORING_UPGRADE = {"OBSERVATION": ("NONE",
                                     "FOLLOW-UP",
                                     ),
                      "DIAGNOSTICS": ("NONE",
                                      "OBSERVATION",
                                      "FOLLOW-UP",
                                      ),
                      "QUARANTINE": ("NONE",
                                     "OBSERVATION",
                                     "DIAGNOSTICS",
                                     "FOLLOW-UP",
                                     ),
                      }

# =============================================================================
class DiseaseDataModel(S3Model):

    names = ("disease_disease",
             "disease_disease_id",
             "disease_symptom",
             "disease_symptom_id",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table

        # =====================================================================
        # Basic Disease Information
        #
        tablename = "disease_disease"
        table = define_table(tablename,
                             self.super_link("doc_id", "doc_entity"),
                             Field("name"),
                             Field("short_name"),
                             Field("acronym"),
                             Field("code",
                                   label = T("ICD-10-CM Code"),
                                   ),
                             Field("description", "text"),
                             Field("trace_period", "integer",
                                   label = T("Trace Period before Symptom Debut (days)"),
                                   ),
                             Field("watch_period", "integer",
                                   label = T("Watch Period after Exposure (days)"),
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        represent = S3Represent(lookup=tablename)
        disease_id = S3ReusableField("disease_id", "reference %s" % tablename,
                                     label = T("Disease"),
                                     represent = represent,
                                     requires = IS_ONE_OF(db, "disease_disease.id",
                                                          represent,
                                                          ),
                                     sortby = "name",
                                     comment = S3AddResourceLink(f="disease",
                                                                 tooltip=T("Add a new disease to the catalog"),
                                                                 ),
                                     )

        self.add_components(tablename,
                            disease_symptom = "disease_id",
                            )

        self.configure(tablename,
                       deduplicate = self.disease_duplicate,
                       super_entity = "doc_entity",
                       )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Disease"),
            title_display = T("Disease Information"),
            title_list = T("Diseases"),
            title_update = T("Edit Disease Information"),
            title_upload = T("Import Disease Information"),
            label_list_button = T("List Diseases"),
            label_delete_button = T("Delete Disease Information"),
            msg_record_created = T("Disease Information added"),
            msg_record_modified = T("Disease Information updated"),
            msg_record_deleted = T("Disease Information deleted"),
            msg_list_empty = T("No Diseases currently registered"))

        # =====================================================================
        # Symptom Information
        #
        tablename = "disease_symptom"
        table = define_table(tablename,
                             disease_id(),
                             Field("name"),
                             Field("description",
                                   label = T("Short Description"),
                                   ),
                             Field("assessment",
                                   label = T("Assessment method"),
                                   ),
                             *s3_meta_fields())

        # @todo: refine to include disease name?
        represent = S3Represent(lookup=tablename)
        symptom_id = S3ReusableField("symptom_id", "reference %s" % tablename,
                                     label = T("Symptom"),
                                     represent = represent,
                                     requires = IS_ONE_OF(db, "disease_symptom.id",
                                                          represent,
                                                          ),
                                     sortby = "name",
                                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Symptom"),
            title_display = T("Symptom Information"),
            title_list = T("Symptoms"),
            title_update = T("Edit Symptom Information"),
            title_upload = T("Import Symptom Information"),
            label_list_button = T("List Symptoms"),
            label_delete_button = T("Delete Symptom Information"),
            msg_record_created = T("Symptom Information added"),
            msg_record_modified = T("Symptom Information updated"),
            msg_record_deleted = T("Symptom Information deleted"),
            msg_list_empty = T("No Symptom Information currently available"))

        # Pass names back to global scope (s3.*)
        return dict(disease_disease_id = disease_id,
                    disease_symptom_id = symptom_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(disease_disease_id = lambda **attr: dummy("disease_id"),
                    disease_symptom_id = lambda **attr: dummy("symptom_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def disease_duplicate(item):
        """
            Disease import update detection

            @param item: the import item
        """

        data = item.data
        code = data.get("code")
        name = data.get("name")

        table = item.table
        queries = []
        if code:
            queries.append((table.code == code))
        if name:
            queries.append((table.name == name))
        if queries:
            query = reduce(lambda x, y: x | y, queries)
        else:
            return

        rows = current.db(query).select(table.id,
                                        table.code,
                                        table.name)
        duplicate = None
        for row in rows:
            if code and row.code == code:
                duplicate = row.id
                break
            if name and row.name == name:
                duplicate = row.id
        if duplicate:
            item.id = duplicate
            item.method = item.METHOD.UPDATE
        return

# =============================================================================
class CaseTrackingModel(S3Model):

    names = ("disease_case",
             "disease_case_id",
             "disease_case_monitoring",
             "disease_case_monitoring_symptom",
             "disease_case_diagnostics",
             )

    def model(self):

        # @todo: add treatment component?

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table
        configure = self.configure
        add_components = self.add_components

        person_id = self.pr_person_id

        # =====================================================================
        # Diagnosis Status
        #
        diagnosis_status = {"UNKNOWN": T("Unknown"),
                            "RISK": T("At Risk"),
                            "PROBABLE": T("Probable"),
                            "CONFIRMED-POS": T("Confirmed Positive"),
                            "CONFIRMED-NEG": T("Confirmed Negative"),
                            }
        diagnosis_status_represent = S3Represent(options = diagnosis_status)

        # =====================================================================
        # Monitoring Levels
        #
        monitoring_levels = {"NONE": T("No Monitoring"),
                             # Clinical observation required:
                             "OBSERVATION": T("Observation"),
                             # Targeted diagnostics required:
                             "DIAGNOSTICS": T("Diagnostics"),
                             # Quarantine required:
                             "QUARANTINE": T("Quarantine"),
                             # Follow-up after recovery:
                             "FOLLOW-UP": T("Post-Recovery Follow-Up"),
                             }
        monitoring_level_represent = S3Represent(options = monitoring_levels)
        # =====================================================================
        # Illness status
        #
        illness_status = {"UNKNOWN": T("Unknown, Not Checked"),
                          "ASYMPTOMATIC": T("Asymptomatic, Clinical Signs Negative"),
                          "SYMPTOMATIC": T("Symptomatic, Clinical Signs Positive"),
                          "SEVERE": T("Severely Ill, Clinical Signs Positive"),
                          "DECEASED": T("Deceased, Clinical Signs Positive"),
                          "RECOVERED": T("Recovered"),
                          }
        illness_status_represent = S3Represent(options = illness_status)

        # =====================================================================
        # Case
        #
        tablename = "disease_case"
        table = define_table(tablename,
                             Field("case_number", length=64,
                                   requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "disease_case.case_number")),
                                   ),
                             person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                             self.disease_disease_id(),
                             #s3_date(), # date registered == created_on?
                             self.gis_location_id(),
                             # @todo: add site ID for registering site?

                             # Current illness status and symptom debut
                             Field("illness_status",
                                   label = T("Current Illness Status"),
                                   represent = illness_status_represent,
                                   requires = IS_IN_SET(illness_status),
                                   default = "UNKNOWN",
                                   ),
                             s3_date("symptom_debut",
                                     label = T("Symptom Debut"),
                                     ),

                             # Current diagnosis status and date of last status update
                             Field("diagnosis_status",
                                   label = T("Diagnosis Status"),
                                   represent = diagnosis_status_represent,
                                   requires = IS_IN_SET(diagnosis_status),
                                   default = "UNKNOWN",
                                   ),
                             s3_date("diagnosis_date",
                                     default = "now",
                                     label = T("Diagnosis Date"),
                                     ),

                             # Current monitoring level and end date
                             Field("monitoring_level",
                                   label = T("Current Monitoring Level"),
                                   represent = monitoring_level_represent,
                                   requires = IS_IN_SET(monitoring_levels),
                                   default = "NONE",
                                   ),
                             s3_date("monitoring_until",
                                     label = T("Monitoring required until"),
                                     ),
                             *s3_meta_fields())

        # Reusable Field
        represent = disease_CaseRepresent()
        case_id = S3ReusableField("case_id", "reference %s" % tablename,
                                  label = T("Case"),
                                  represent = represent,
                                  requires = IS_ONE_OF(db, "disease_case.id",
                                                       represent,
                                                       ),
                                  comment = S3AddResourceLink(f="case",
                                                              tooltip=T("Add a new case"),
                                                              ),
                                  )

        # Components
        add_components(tablename,
                       disease_case_monitoring = "case_id",
                       disease_case_diagnostics = "case_id",
                       disease_tracing = "case_id",
                       disease_exposure = ({"name": "exposure",
                                            "joinby": "person_id",
                                            "pkey": "person_id",
                                            },
                                            {"name": "contact",
                                             "joinby": "case_id",
                                             },
                                            ),
                       )

        report_fields = ["disease_id",
                         "location_id",
                         "illness_status",
                         "monitoring_level",
                         "diagnosis_status",
                         ]
        report_options = {"rows": report_fields,
                          "cols": report_fields,
                          "fact": [(T("Number of Cases"), "count(id)"),
                                   ],
                          "defaults": {"rows": "location_id",
                                       "cols": "diagnosis_status",
                                       "fact": "count(id)",
                                       "totals": True,
                                       },
                          }

        filter_widgets = [S3TextFilter(["case_number",
                                        "person_id$first_name",
                                        "person_id$middle_name",
                                        "person_id$last_name",
                                        ],
                                        label = T("Search"),
                                        comment = T("Enter Case Number or Name"),
                                        ),
                          S3OptionsFilter("monitoring_level",
                                          options = monitoring_levels,
                                          ),
                          S3OptionsFilter("diagnosis_status",
                                          options = diagnosis_status,
                                          ),
                          S3LocationFilter("location_id",
                                           ),
                          ]

        configure(tablename,
                  create_onvalidation = self.case_create_onvalidation,
                  deduplicate = self.case_duplicate,
                  delete_next = URL(f="case", args=["summary"]),
                  filter_widgets = filter_widgets,
                  onaccept = self.case_onaccept,
                  report_options = report_options,
                  )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Case"),
            title_display = T("Case Details"),
            title_list = T("Cases"),
            title_update = T("Edit Cases"),
            title_upload = T("Import Cases"),
            label_list_button = T("List Cases"),
            label_delete_button = T("Delete Case"),
            msg_record_created = T("Case added"),
            msg_record_modified = T("Case updated"),
            msg_record_deleted = T("Case deleted"),
            msg_list_empty = T("No Cases currently registered"))

        # =====================================================================
        # Monitoring
        #
        tablename = "disease_case_monitoring"
        table = define_table(tablename,
                             case_id(),
                             s3_datetime(default="now"),
                             Field("illness_status",
                                   represent = illness_status_represent,
                                   requires = IS_IN_SET(illness_status),
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # Reusable Field
        represent = S3Represent(lookup=tablename, fields=["case_id"])
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Case"),
                                    represent = represent,
                                    requires = IS_ONE_OF(db, "disease_case.id",
                                                         represent,
                                                         ),
                                    comment = S3AddResourceLink(f="case",
                                                                tooltip=T("Add a new case"),
                                                                ),
                                    )

        # Components
        add_components(tablename,
                       disease_symptom = {"link": "disease_case_monitoring_symptom",
                                          "joinby": "status_id",
                                          "key": "symptom_id",
                                          }
                       )

        # Custom CRUD form
        crud_fields = ["case_id",
                       "date",
                       "illness_status",
                       S3SQLInlineLink("symptom",
                                       field = "symptom_id",
                                       label = T("Symptoms"),
                                       multiple = True,
                                       ),
                       "comments",
                       ]

        configure(tablename,
                  crud_form = S3SQLCustomForm(*crud_fields),
                  list_fields = ["date",
                                 "illness_status",
                                 (T("Symptoms"), "symptom.name"),
                                 "comments",
                                 ],
                  onaccept = self.monitoring_onaccept,
                  )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Monitoring Update"),
            title_display = T("Monitoring Update"),
            title_list = T("Monitoring Updates"),
            title_update = T("Edit Monitoring Update"),
            title_upload = T("Import Monitoring Updates"),
            label_list_button = T("List Monitoring Updates"),
            label_delete_button = T("Delete Monitoring Update"),
            msg_record_created = T("Monitoring Update added"),
            msg_record_modified = T("Monitoring Update updated"),
            msg_record_deleted = T("Monitoring Update deleted"),
            msg_list_empty = T("No Monitoring Information currently available"))

        # =====================================================================
        # Monitoring <=> Symptom
        #
        tablename = "disease_case_monitoring_symptom"
        table = define_table(tablename,
                             Field("status_id", "reference disease_case_monitoring",
                                   requires = IS_ONE_OF(db, "disease_case_monitoring.id"),
                                   ),
                             self.disease_symptom_id(),
                             *s3_meta_fields())

        # =====================================================================
        # Diagnostics
        #
        probe_status = {"PENDING": T("Pending"),
                        "PROCESSED": T("Processed"),
                        "VALIDATED": T("Validated"),
                        "INVALID": T("Invalid"),
                        "LOST": T("Lost"),
                        }
        tablename = "disease_case_diagnostics"
        table = define_table(tablename,
                             case_id(),
                             # @todo: make a lookup table in DiseaseDataModel:
                             Field("probe_type"),
                             Field("probe_number", length = 64, unique = True,
                                   ),
                             s3_date("probe_date",
                                     default = "now",
                                     label = T("Probe Date"),
                                     ),
                             Field("probe_status",
                                   represent = S3Represent(options = probe_status),
                                   requires = IS_IN_SET(probe_status),
                                   default = "PENDING",
                                   ),
                             # @todo: make a lookup table in DiseaseDataModel:
                             Field("test_type"),
                             Field("result"),
                             s3_date("result_date",
                                     label = T("Result Date"),
                                     ),
                             Field("conclusion",
                                   represent = diagnosis_status_represent,
                                   requires = IS_EMPTY_OR(
                                                IS_IN_SET(diagnosis_status)),
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Diagnostic Test"),
            title_display = T("Diagnostic Test Details"),
            title_list = T("Diagnostic Tests"),
            title_update = T("Edit Diagnostic Test Details"),
            title_upload = T("Import Diagnostic Test Data"),
            label_list_button = T("List Diagnostic Tests"),
            label_delete_button = T("Delete Diagnostic Test"),
            msg_record_created = T("Diagnostic Test added"),
            msg_record_modified = T("Diagnostic Test updated"),
            msg_record_deleted = T("Diagnostic Test deleted"),
            msg_list_empty = T("No Diagnostic Tests currently registered"))

        # =====================================================================

        # Pass names back to global scope (s3.*)
        return dict(disease_case_id = case_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(disease_case_id = lambda **attr: dummy("case_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def get_case(person_id, disease_id):
        """
            Find the case record for a person for a disease

            @param person_id: the person record ID
            @param disease_id: the disease record ID
        """

        ctable = current.s3db.disease_case
        query = (ctable.person_id == person_id) & \
                (ctable.disease_id == disease_id) & \
                (ctable.deleted != True)
        record = current.db(query).select(ctable.id,
                                          ctable.case_number,
                                          limitby = (0, 1)).first()
        return record

    # -------------------------------------------------------------------------
    @classmethod
    def case_create_onvalidation(cls, form):
        """
            Make sure that there's only one case per person and disease
        """

        formvars = form.vars
        try:
            case_id = formvars.id
            person_id = formvars.person_id
        except AttributeError, e:
            return

        if "disease_id" not in formvars:
            disease_id = current.s3db.disease_case.disease_id.default
        else:
            disease_id = formvars.disease_id

        record = cls.get_case(person_id, disease_id)
        if record and record.id != case_id:
            error = current.T("This case is already registered")
            link = A(record.case_number,
                     _href=URL(f="case", args=[record.id]))
            form.errors.person_id = XML("%s: %s" % (error, link))
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def case_duplicate(item):
        """
            Case import update detection

            @param item: the import item
        """

        data = item.data
        case_number = data.get("case_number")
        person_id = data.get("person_id")

        table = item.table
        if case_number:
            query = (table.case_number == case_number) & \
                    (table.deleted != True)
        else:
            disease_id = data.get("disease_id")
            if person_id and disease_id:
                query = (table.disease_id == disease_id) & \
                        (table.person_id == person_id) & \
                        (table.deleted != True)
            else:
                return

        duplicate = current.db(query).select(table.id,
                                             table.person_id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.data.person_id = duplicate.person_id
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def case_onaccept(form):
        """
            Propagate status updates of the case to high-risk contacts
        """

        formvars = form.vars
        try:
            record_id = formvars.id
        except AttributeError:
            return

        disease_propagate_case_status(record_id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def monitoring_onaccept(form):
        """
            Update the illness status of the case from last monitoring entry
        """

        formvars = form.vars
        try:
            record_id = formvars.id
        except AttributeError:
            return

        db = current.db
        s3db = current.s3db

        ctable = s3db.disease_case
        mtable = s3db.disease_case_monitoring

        # Get the case ID
        case_id = None
        if "case_id" not in formvars:
            query = (mtable.id == record_id)
            row = db(query).select(mtable.case_id, limitby=(0, 1)).first()
            if row:
                case_id = row.case_id
        else:
            case_id = formvars.case_id
        if not case_id:
            return

        query = (mtable.case_id == case_id) & \
                (mtable.illness_status != None)

        row = db(query).select(mtable.illness_status,
                               orderby = "disease_case_monitoring.date desc",
                               limitby = (0, 1)).first()
        if row:
            db(ctable.id == case_id).update(illness_status = row.illness_status)
            # Propagate case status to contacts
            disease_propagate_case_status(case_id)
        return

# =============================================================================
class disease_CaseRepresent(S3Represent):

    def __init__(self):
        """ Constructor """

        super(disease_CaseRepresent, self).__init__(lookup = "disease_case")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=[]):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        s3db = current.s3db

        table = self.table
        ptable = s3db.pr_person
        dtable = s3db.disease_disease

        left = [ptable.on(ptable.id == table.person_id),
                dtable.on(dtable.id == table.disease_id)]
        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(table.id,
                                        table.case_number,
                                        dtable.name,
                                        dtable.short_name,
                                        dtable.acronym,
                                        ptable.first_name,
                                        ptable.last_name,
                                        left = left)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        try:
            case_number = row[self.tablename].case_number
        except AttributeError:
            return row.case_number

        disease_name = None
        try:
            disease = row["disease_disease"]
        except AttributeError:
            pass
        else:
            for field in ("acronym", "short_name", "name"):
                if field in disease:
                    disease_name = disease[field]
                    if disease_name:
                        break

        if disease_name and case_number:
            case = "%s [%s]" % (case_number, disease_name)
        elif disease_name:
            case = "[%s]" % disease_name
        else:
            case = case_number

        try:
            person = row["pr_person"]
        except AttributeError:
            return case

        full_name = s3_fullname(person)
        if case:
            return " ".join((case, full_name))
        else:
            return full_name

# =============================================================================
class ContactTracingModel(S3Model):

    names = ("disease_tracing",
             "disease_exposure",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table

        case_id = self.disease_case_id

        # =====================================================================
        # Tracing Information: when/where did a case pose risk for exposure?
        #

        # Processing Status
        contact_tracing_status = {
            "OPEN": T("Open"),         # not all contacts identified yet
            "COMPLETE": T("Complete"), # all contacts identified, closed
        }

        tablename = "disease_tracing"
        table = define_table(tablename,
                             case_id(),
                             s3_datetime("start_date",
                                         label = T("From"),
                                         widget = S3DateTimeWidget(set_min="disease_end_date",
                                                                   ),
                                         ),
                             s3_datetime("end_date",
                                         label = T("To"),
                                         widget = S3DateTimeWidget(set_max="disease_start_date",
                                                                   ),
                                         ),
                             # @todo: add site_id?
                             self.gis_location_id(),
                             Field("circumstances", "text",
                                   ),
                             Field("status",
                                   default = "OPEN",
                                   label = T("Tracing Status"),
                                   requires = IS_IN_SET(contact_tracing_status, zero=None),
                                   represent = S3Represent(options=contact_tracing_status),
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # @todo: implement specific S3Represent class
        represent = S3Represent(lookup=tablename, fields=["case_id"])
        tracing_id = S3ReusableField("tracing_id", "reference %s" % tablename,
                                     label = T("Tracing Record"),
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "disease_tracing.id",
                                                              represent,
                                                              )),
                                     sortby = "date",
                                     comment = S3AddResourceLink(f="tracing",
                                                                 tooltip=T("Add a new contact tracing information"),
                                                                 ),
                                     )

        self.add_components(tablename,
                            disease_exposure = "tracing_id",
                            )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Tracing Record"),
            title_display = T("Tracing Details"),
            title_list = T("Contact Tracings"),
            title_update = T("Edit Tracing Information"),
            title_upload = T("Import Tracing Information"),
            label_list_button = T("List Tracing Record"),
            label_delete_button = T("Delete Tracing Record"),
            msg_record_created = T("Tracing Record added"),
            msg_record_modified = T("Tracing Record updated"),
            msg_record_deleted = T("Tracing Record deleted"),
            msg_list_empty = T("No Contact Tracings currently registered"))

        # =====================================================================
        # Protection
        #
        protection_level = {"NONE": T("Unknown"),
                            "PARTIAL": T("Partial"),
                            "FULL": T("Full"),
                            }
        protection_level_represent = S3Represent(options = protection_level)

        # =====================================================================
        # Exposure Type
        #
        exposure_type = {"UNKNOWN": T("Unknown"),
                         "DIRECT": T("Direct"),
                         "INDIRECT": T("Indirect"),
                         }
        exposure_type_represent = S3Represent(options = exposure_type)

        # =====================================================================
        # Exposure Risk Level
        #
        exposure_risk = {"UNKNOWN": T("Unknown"),
                         "NONE": T("No known exposure"),
                         "LOW": T("Low risk exposure"),
                         "HIGH": T("High risk exposure"),
                         }
        exposure_risk_represent = S3Represent(options = exposure_risk)

        # =====================================================================
        # Exposure: when and how was a person exposed to the disease?
        #
        tablename = "disease_exposure"
        table = define_table(tablename,
                             case_id(),
                             tracing_id(),
                             self.pr_person_id(requires = IS_ADD_PERSON_WIDGET2(),
                                               widget = S3AddPersonWidget2(controller="pr"),
                                               ),
                             s3_datetime(),
                             #self.gis_location_id(),
                             Field("exposure_type",
                                   default = "UNKNOWN",
                                   represent = exposure_type_represent,
                                   requires = IS_IN_SET(exposure_type, zero=None),
                                   ),
                             Field("protection_level",
                                   default = "NONE",
                                   represent = protection_level_represent,
                                   requires = IS_IN_SET(protection_level, zero=None),
                                   ),
                             Field("exposure_risk",
                                   default = "LOW",
                                   represent = exposure_risk_represent,
                                   requires = IS_IN_SET(exposure_risk, zero=None),
                                   ),
                             Field("circumstances", "text"),
                             *s3_meta_fields())

        self.configure(tablename,
                       onaccept = self.exposure_onaccept,
                       )

        crud_strings[tablename] = Storage(
            label_create = T("Add Exposure Information"),
            title_display = T("Exposure Details"),
            title_list = T("Exposure Information"),
            title_update = T("Edit Exposure Information"),
            title_upload = T("Import Exposure Information"),
            label_list_button = T("List Exposures"),
            label_delete_button = T("Delete Exposure Information"),
            msg_record_created = T("Exposure Information added"),
            msg_record_modified = T("Exposure Information updated"),
            msg_record_deleted = T("Exposure Information deleted"),
            msg_list_empty = T("No Exposure Information currently registered"))

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():

        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def exposure_onaccept(form):
        """
            @todo: docstring
        """

        formvars = form.vars
        try:
            record_id = formvars.id
        except AttributeError:
            return

        db = current.db
        s3db = current.s3db

        # We need case_id, person_id and exposure_risk from the current record
        if "case_id" not in formvars:
            etable = s3db.disease_exposure
            row = db(etable.id == record_id).select(etable.case_id,
                                                    limitby = (0, 1)).first()
            if not row:
                return
            case_id = row.case_id
        else:
            case_id = formvars.case_id

        disease_propagate_case_status(case_id)
        return

# =============================================================================
def disease_propagate_case_status(case_id):
    """
        @todo: docstring
    """

    db = current.db
    s3db = current.s3db

    risk_status = ("SYMPTOMATIC", "SEVERE", "DECEASED", "RECOVERED")

    # Get the case
    ctable = s3db.disease_case
    query = (ctable.id == case_id) & \
            (ctable.deleted != True)
    case = db(query).select(ctable.id,
                            ctable.created_on,
                            ctable.disease_id,
                            ctable.illness_status,
                            ctable.symptom_debut,
                            ctable.diagnosis_status,
                            ctable.diagnosis_date,
                            limitby = (0, 1)).first()
    if case is None:
        return
    disease_id = case.disease_id

    # Try to establish a symptom debut
    symptom_debut = case.symptom_debut
    if not symptom_debut:
        # Get all monitoring entries for this case
        mtable = s3db.disease_case_monitoring
        query = (mtable.case_id == case_id) & \
                (mtable.illness_status.belongs(risk_status)) & \
                (mtable.deleted != True)
        monitoring = db(query).select(mtable.date,
                                      orderby = "disease_case_monitoring.date desc",
                                      limitby = (0, 1)).first()
        if monitoring:
            symptom_debut = monitoring.date
    if not symptom_debut and case.illness_status in risk_status:
        symptom_debut = case.created_on
    if not symptom_debut:
        # Case is not known to ever have shown any symptoms
        return

    if case.diagnosis_status == "CONFIRMED-NEG" and \
       case.diagnosis_date > symptom_debut:
        # Case has been declared CONFIRMED-NEG after symptom debut
        return

    # Establish risk period (=symptom debut minus trace period)
    dtable = s3db.disease_disease
    query = (dtable.id == disease_id) & \
            (dtable.deleted != True)
    disease = db(query).select(dtable.trace_period,
                               dtable.watch_period,
                               limitby = (0, 1)).first()
    if not disease:
        return
    trace_period = disease.trace_period
    if trace_period:
        risk_period_start = symptom_debut - datetime.timedelta(days = disease.trace_period)
    else:
        risk_period_start = symptom_debut

    # Get all high-risk exposures after risk_period_start
    etable = s3db.disease_exposure
    query = (etable.case_id == case_id) & \
            (etable.date >= risk_period_start) & \
            (etable.exposure_risk == "HIGH") & \
            (etable.deleted != True)
    exposures = db(query).select(etable.person_id)
    for exposure in exposures:
        disease_create_case(disease_id,
                            exposure.person_id,
                            monitoring_level = "OBSERVATION",
                            )
    return

# =============================================================================
def disease_create_case(disease_id, person_id, monitoring_level=None):
    """
        @todo: docstring
    """

    ctable = current.s3db.disease_case
    query = (ctable.person_id == person_id) & \
            (ctable.disease_id == disease_id) & \
            (ctable.deleted != True)

    case = current.db(query).select(ctable.id,
                                    ctable.monitoring_level,
                                    limitby = (0, 1)).first()
    if case:
        case_id = case.id
        if monitoring_level is not None:
            disease_upgrade_monitoring(case_id,
                                       monitoring_level,
                                       case=case,
                                       )
    else:
        case_id = ctable.insert(disease_id = disease_id,
                                person_id = person_id,
                                monitoring_level = monitoring_level,
                                )
    return case_id

# =============================================================================
def disease_upgrade_monitoring(case_id, level, case=None):
    """
        @todo: docstring
    """

    if level not in MONITORING_UPGRADE:
        return False
    else:
        previous_levels = MONITORING_UPGRADE[level]

    if case is None or "monitoring_level" not in case:
        ctable = current.s3db.disease_case
        query = (ctable.id == case_id) & \
                (ctable.monitoring_level.belongs(previous_levels)) & \
                (ctable.deleted != True)

        case = current.db(query).select(ctable.id,
                                        limitby = (0, 1)).first()
    elif case.monitoring_level not in previous_levels:
        return
    if case:
        case.update_record(monitoring_level = level)
    return True

# =============================================================================
def disease_rheader(r, tabs=None):
    """
        @todo: docstring
    """

    T = current.T
    if r.representation != "html":
        return None

    resourcename = r.name

    if resourcename == "disease":

        tabs = [(T("Basic Details"), None),
                (T("Symptoms"), "symptom"),
                (T("Documents"), "document"),
                ]

        rheader_fields = [["name"],
                          ["code"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "case":

        tabs = [(T("Basic Details"), None),
                (T("Exposure"), "exposure"),
                (T("Monitoring"), "case_monitoring"),
                (T("Diagnostics"), "case_diagnostics"),
                (T("Contacts"), "contact"),
                (T("Tracing"), "tracing"),
                ]

        rheader_fields = [["person_id"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "tracing":

        tabs = [(T("Basic Details"), None),
                (T("Contact Persons"), "exposure"),
                ]

        rheader_fields = [["case_id"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    return rheader

# END =========================================================================
