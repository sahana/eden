# -*- coding: utf-8 -*-

__all__ = ("DiseaseDataModel",
           "CaseTrackingModel",
           "ContactTracingModel",
           "DiseaseStatsModel",
           "disease_rheader",
           )

import datetime

try:
    # try stdlib (Python 2.6)
    import json
except ImportError:
    try:
        # try external module
        import simplejson as json
    except:
        # fallback to pure-Python module
        import gluon.contrib.simplejson as json

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
class DiseaseStatsModel(S3Model):
    """
        Disease Statistics:
            Cases:
                Confirmed/Suspected/Probable
            Deaths
    """

    names = ("disease_statistic",
             "disease_stats_data",
             "disease_stats_aggregate",
             "disease_stats_rebuild_all_aggregates",
             "disease_stats_update_aggregates",
             "disease_stats_update_location_aggregates",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        location_id = self.gis_location_id

        stats_parameter_represent = S3Represent(lookup="stats_parameter",
                                                translate=True)

        # ---------------------------------------------------------------------
        # Disease Statistic Parameter
        #
        tablename = "disease_statistic"
        define_table(tablename,
                     # Instance
                     super_link("parameter_id", "stats_parameter"),
                     Field("name",
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                    else NONE,
                           ),
                     s3_comments("description",
                                 label = T("Description"),
                                 ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        ADD_STATISTIC = T("Add Statistic")
        crud_strings[tablename] = Storage(
            label_create = ADD_STATISTIC,
            title_display = T("Statistic Details"),
            title_list = T("Statistics"),
            title_update = T("Edit Statistic"),
            #title_upload = T("Import Statistics"),
            label_list_button = T("List Statistics"),
            msg_record_created = T("Statistic added"),
            msg_record_modified = T("Statistic updated"),
            msg_record_deleted = T("Statistic deleted"),
            msg_list_empty = T("No statistics currently defined"))

        configure(tablename,
                  deduplicate = self.disease_statistic_duplicate,
                  super_entity = "stats_parameter",
                  )

        # ---------------------------------------------------------------------
        # Disease Statistic Data
        #
        tablename = "disease_stats_data"
        define_table(tablename,
                     # Instance
                     super_link("data_id", "stats_data"),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                instance_types = ("disease_statistic",),
                                label = T("Statistic"),
                                represent = stats_parameter_represent,
                                readable = True,
                                writable = True,
                                empty = False,
                                comment = S3AddResourceLink(c="disease",
                                                            f="statistic",
                                                            vars = dict(child = "parameter_id"),
                                                            title=ADD_STATISTIC,
                                                            ),
                                ),
                     location_id(
                         requires = IS_LOCATION(),
                         widget = S3LocationAutocompleteWidget(),
                     ),
                     Field("value", "double",
                           label = T("Value"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_date(empty = False),
                     #Field("end_date", "date",
                     #      # Just used for the year() VF
                     #      readable = False,
                     #      writable = False
                     #      ),
                     # Link to Source
                     self.stats_source_id(),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Disease Data"),
            title_display = T("Disease Data Details"),
            title_list = T("Disease Data"),
            title_update = T("Edit Disease Data"),
            title_upload = T("Import Disease Data"),
            label_list_button = T("List Disease Data"),
            msg_record_created = T("Disease Data added"),
            msg_record_modified = T("Disease Data updated"),
            msg_record_deleted = T("Disease Data deleted"),
            msg_list_empty = T("No disease data currently available"))

        levels = current.gis.get_relevant_hierarchy_levels()

        location_fields = ["location_id$%s" % level for level in levels]

        list_fields = ["parameter_id"]
        list_fields.extend(location_fields)
        list_fields.extend((("value",
                             "date",
                             "source_id",
                             )))

        filter_widgets = [S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          multiple = False,
                                          # Not translateable
                                          #represent = "%(name)s",
                                          ),
                          S3OptionsFilter("location_id$level",
                                          label = T("Level"),
                                          multiple = False,
                                          # Not translateable
                                          #represent = "%(name)s",
                                          ),
                          S3LocationFilter("location_id",
                                           levels = levels,
                                           ),
                          ]

        report_options = Storage(rows = location_fields,
                                 cols = ["parameter_id"],
                                 fact = [(T("Value"), "sum(value)"),
                                         ],
                                 defaults = Storage(rows = location_fields[0], # => L0 for multi-country, L1 for single country
                                                    cols = "parameter_id",
                                                    fact = "sum(value)",
                                                    totals = True,
                                                    chart = "breakdown:rows",
                                                    table = "collapse",
                                                    )
                                 )

        configure(tablename,
                  deduplicate = self.disease_stats_data_duplicate,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  report_options = report_options,
                  # @ToDo: Wrapper function to call this for the record linked
                  # to the relevant place depending on whether approval is
                  # required or not. Disable when auth.override is True.
                  #onaccept = self.disease_stats_update_aggregates,
                  #onapprove = self.disease_stats_update_aggregates,
                  # @ToDo: deployment_setting
                  #requires_approval = True,
                  super_entity = "stats_data",
                  timeplot_options = {"defaults": {"event_start": "date",
                                                   "event_end": "date",
                                                   "fact": "cumulate(value)",
                                                   },
                                      },
                  )

        #----------------------------------------------------------------------
        # Disease Aggregated data
        #

        # The data can be aggregated against:
        # location, all the aggregated values across a number of locations
        #           thus for an L2 it will aggregate all the L3 values
        # time, sum of all the disease_stats_data values up to this time.
        #           allowing us to report on cumulative values

        aggregate_types = {1 : T("Time"),
                           2 : T("Location"),
                           }

        tablename = "disease_stats_aggregate"
        define_table(tablename,
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                empty = False,
                                instance_types = ("disease_statistic",),
                                label = T("Statistic"),
                                represent = S3Represent(lookup="stats_parameter"),
                                readable = True,
                                writable = True,
                                ),
                     location_id(
                        requires = IS_LOCATION(),
                        widget = S3LocationAutocompleteWidget(),
                     ),
                     Field("agg_type", "integer",
                           default = 1,
                           label = T("Aggregation Type"),
                           represent = lambda opt: \
                            aggregate_types.get(opt,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(aggregate_types),
                           ),
                     s3_date("date",
                             label = T("Start Date"),
                             ),
                     Field("sum", "double",
                           label = T("Sum"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                           ),
                     *s3_meta_fields()
                     )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(
            disease_stats_rebuild_all_aggregates = self.disease_stats_rebuild_all_aggregates,
            disease_stats_update_aggregates = self.disease_stats_update_aggregates,
            disease_stats_update_location_aggregates = self.disease_stats_update_location_aggregates,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def disease_statistic_duplicate(item):
        """ Import item de-duplication """

        name = item.data.get("name")
        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def disease_stats_data_duplicate(item):
        """ Import item de-duplication """

        data = item.data
        parameter_id = data.get("parameter_id")
        location_id = data.get("location_id")
        date = data.get("date")
        table = item.table
        query = (table.date == date) & \
                (table.location_id == location_id) & \
                (table.parameter_id == parameter_id)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def disease_stats_rebuild_all_aggregates():
        """
            This will delete all the disease_stats_aggregate records and
            then rebuild them by triggering off a request for each
            disease_stats_data record.

            This function is normally only run during prepop or postpop so we
            don't need to worry about the aggregate data being unavailable for
            any length of time
        """

        # Check to see whether an existing task is running and if it is then kill it
        db = current.db
        ttable = db.scheduler_task
        rtable = db.scheduler_run
        wtable = db.scheduler_worker
        query = (ttable.task_name == "disease_stats_update_aggregates") & \
                (rtable.task_id == ttable.id) & \
                (rtable.status == "RUNNING")
        rows = db(query).select(rtable.id,
                                rtable.task_id,
                                rtable.worker_name)
        now = current.request.utcnow
        for row in rows:
            db(wtable.worker_name == row.worker_name).update(status="KILL")
            db(rtable.id == row.id).update(stop_time=now,
                                           status="STOPPED")
            db(ttable.id == row.task_id).update(stop_time=now,
                                                status="STOPPED")

        # Delete the existing aggregates
        current.s3db.disease_stats_aggregate.truncate()

        # Read all the disease_stats_data records
        dtable = db.disease_stats_data
        query = (dtable.deleted != True)
        # @ToDo: deployment_setting to make this just the approved records
        #query &= (dtable.approved_by != None)
        records = db(query).select(dtable.parameter_id,
                                   dtable.date,
                                   dtable.value,
                                   dtable.location_id,
                                   )

        # Fire off a rebuild task
        current.s3task.async("disease_stats_update_aggregates",
                             vars = dict(records=records.json(), all=True),
                             timeout = 21600 # 6 hours
                             )

    # -------------------------------------------------------------------------
    @staticmethod
    def disease_stats_update_aggregates(records=None, all=False):
        """
            This will calculate the disease_stats_aggregates for the specified
            records. Either all (when rebuild_all is invoked) or for the
            individual parameter(s) at the specified location(s) when run
            onaccept/onapprove.
            @ToDo: onapprove/onaccept wrapper function.

            This will get the raw data from disease_stats_data and generate
            a disease_stats_aggregate record for the given time period.

            The reason for doing this is so that all aggregated data can be
            obtained from a single table. So when displaying data for a
            particular location it will not be necessary to try the aggregate
            table, and if it's not there then try the data table. Rather just
            look at the aggregate table.

            Once this has run then a complete set of aggregate records should
            exists for this parameter_id and location for every time period from
            the first data item until the current time period.

            @ToDo: Add test cases to modules/unit_tests/s3db/disease.py
         """

        if not records:
            return

        # Test to see which date format we have based on how we were called
        if isinstance(records, basestring):
            from_json = True
            from dateutil.parser import parse
            records = json.loads(records)
        elif isinstance(records[0]["date"],
                        (datetime.date, datetime.datetime)):
            from_json = False
        else:
            from_json = True
            from dateutil.parser import parse

        db = current.db
        s3db = current.s3db
        atable = db.disease_stats_aggregate

        if not all:
            # Read the database to get all the relevant records
            # @ToDo: Complete this
            return
            dtable = s3db.disease_stats_data

        # For each location/parameter pair, create a time-aggregate summing all
        # the data so far

        now = current.request.now

        # Assemble raw data
        earliest_period = now.date()
        locations = {}
        parameters = []
        pappend = parameters.append
        for record in records:
            location_id = record["location_id"]
            if location_id not in locations:
                locations[location_id] = {}
            parameter_id = record["parameter_id"]
            if parameter_id not in parameters:
                pappend(parameter_id)
            if parameter_id not in locations[location_id]:
                locations[location_id][parameter_id] = {}
            if from_json:
                date = parse(record["date"]) # produces a datetime
                date = date.date()
            else:
                date = record["date"]
            if date < earliest_period:
                earliest_period = date
            locations[location_id][parameter_id][date] = record["value"]

        # Full range of dates
        # 1 per day from the start of the data to the present day
        from dateutil.rrule import rrule, DAILY
        dates = rrule(DAILY, dtstart=earliest_period, until=now)
        dates = [d.date() for d in dates]

        # Add the sums
        insert = atable.insert
        lfield = atable.location_id
        pfield = atable.parameter_id
        dfield = atable.date
        ifield = atable.id
        _q = (atable.agg_type == 1)
        for location_id in locations:
            location = locations[location_id]
            query = _q & (lfield == location_id)
            for parameter_id in location:
                parameter = location[parameter_id]
                q = query & (pfield == parameter_id)
                for d in dates:
                    values = []
                    vappend = values.append
                    for date in parameter:
                        if date <= d:
                            vappend(parameter[date])
                    values_sum = sum(values)
                    exists = db(q & (dfield == d)).select(ifield,
                                                          limitby=(0, 1))
                    if exists:
                        db(ifield == exists.first().id).update(sum = values_sum)
                    else:
                        insert(agg_type = 1, # Time
                               location_id = location_id,
                               parameter_id = parameter_id,
                               date = d,
                               sum = values_sum,
                               )

        # For each location/parameter pair, build a location-aggregate for all
        # ancestors, by level (immediate parents first).
        # Ensure that we don't duplicate builds
        # Do this for all dates between the changed date and the current date

        # Get all the ancestors
        # Read all the Paths
        # NB Currently we're assuming that all Paths have been built correctly
        gtable = db.gis_location
        ifield = gtable.id
        location_ids = locations.keys()
        paths = db(ifield.belongs(location_ids)).select(gtable.path)
        paths = [p.path.split("/") for p in paths]
        # Convert list of lists to flattened list & remove duplicates
        import itertools
        ancestors = tuple(itertools.chain.from_iterable(paths))
        # Remove locations which we already have data for
        ancestors = [a for a in ancestors if a not in location_ids]

        # Get all the children for each ancestor (immediate children not descendants)
        pfield = gtable.parent
        query = (gtable.deleted == False) & \
                (pfield.belongs(ancestors))
        all_children = db(query).select(ifield,
                                        pfield)

        # Read the levels
        rows = db(ifield.belongs(ancestors)).select(ifield,
                                                    gtable.level)
        L0 = []
        L0_append = L0.append
        L1 = []
        L1_append = L1.append
        L2 = []
        L2_append = L2.append
        L3 = []
        L3_append = L3.append
        L4 = []
        L4_append = L4.append
        for row in rows:
            if row.level == "L0":
                L0_append(row.id)
            elif row.level == "L1":
                L1_append(row.id)
            elif row.level == "L2":
                L2_append(row.id)
            elif row.level == "L3":
                L3_append(row.id)
            elif row.level == "L4":
                L4_append(row.id)

        async = current.s3task.async
        from gluon.serializers import json as jsons
        dates = jsons(dates)
        # Build the lowest level first
        for level in (L4, L3, L2, L1):
            for location_id in level:
                children = [c.id for c in all_children if c.parent == location_id]
                children = json.dumps(children)
                for parameter_id in parameters:
                    async("disease_stats_update_location_aggregates",
                          args = [location_id, children, parameter_id, dates],
                          timeout = 1800 # 30m
                          )

    # -------------------------------------------------------------------------
    @staticmethod
    def disease_stats_update_location_aggregates(location_id,
                                                 children,
                                                 parameter_id,
                                                 dates,
                                                 ):
        """
            Calculates the disease_stats_aggregate for a specific parameter at a
            specific location over the range of dates.

            @param location_id: location to aggregate at
            @param children: locations to aggregate from
            @param parameter_id: arameter to aggregate
            @param dates: dates to aggregate for (as JSON string)
        """

        db = current.db
        atable = current.s3db.disease_stats_aggregate
        ifield = atable.id
        lfield = atable.location_id
        pfield = atable.parameter_id
        dfield = atable.date

        children = json.loads(children)

        # Get the most recent disease_stats_aggregate record for all child locations
        # - doesn't matter whether this is a time or location aggregate
        query = (pfield == parameter_id) & \
                (atable.deleted != True) & \
                (lfield.belongs(children))
        rows = db(query).select(atable.sum,
                                dfield,
                                lfield,
                                orderby=(lfield, ~dfield),
                                # groupby avoids duplicate records for the same
                                # location, but is slightly slower than just
                                # skipping the duplicates in the loop below
                                #groupby=(lfield)
                                )

        if not rows:
            return

        # Lookup which records already exist
        query = (lfield == location_id) & \
                (pfield == parameter_id)
        existing = db(query).select(ifield,
                                    dfield,
                                    )
        exists = {}
        for e in existing:
            exists[e.date] = e.id

        from dateutil.parser import parse
        dates = json.loads(dates)
        insert = atable.insert

        for date in dates:
            # Collect the values, skip duplicate records for the
            # same location => use the most recent one, which is
            # the first row for each location as per the orderby
            # in the query above
            date = parse(date) # produces a datetime
            date = date.date()
            last_location = None
            values = []
            vappend = values.append
            for row in rows:
                if date < row.date:
                    # Skip
                    continue
                new_location_id = row.location_id
                if new_location_id != last_location:
                    last_location = new_location_id
                    vappend(row.sum)

            if values:
                # Aggregate the values
                values_sum = sum(values)
            else:
                values_sum = 0

            # Add or update the aggregated values in the database

            attr = dict(agg_type = 2, # Location
                        sum = values_sum,
                        )

            # Do we already have a record?
            if date in exists:
                db(ifield == exists[date]).update(**attr)
            else:
                # Insert new
                insert(parameter_id = parameter_id,
                       location_id = location_id,
                       date = date,
                       **attr
                       )

# =============================================================================
def disease_rheader(r, tabs=None):
    """
        Resource Header for Disease module
    """

    T = current.T
    if r.representation != "html":
        return None

    resourcename = r.name

    if resourcename == "disease":

        tabs = ((T("Basic Details"), None),
                (T("Symptoms"), "symptom"),
                (T("Documents"), "document"),
                )

        rheader_fields = (["name"],
                          ["code"],
                          )
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "case":

        tabs = ((T("Basic Details"), None),
                (T("Exposure"), "exposure"),
                (T("Monitoring"), "case_monitoring"),
                (T("Diagnostics"), "case_diagnostics"),
                (T("Contacts"), "contact"),
                (T("Tracing"), "tracing"),
                )

        rheader_fields = (["person_id"],
                          )
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "tracing":

        tabs = ((T("Basic Details"), None),
                (T("Contact Persons"), "exposure"),
                )

        rheader_fields = (["case_id"],
                          )
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    return rheader

# END =========================================================================
