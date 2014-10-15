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

# =============================================================================
class CaseTrackingModel(S3Model):

    names = ("disease_case",
             "disease_case_id",
             "disease_case_monitoring",
             "disease_case_monitoring_symptom",
             )

    def model(self):
        
        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table
        
        person_id = self.pr_person_id

        # =====================================================================
        # Case
        #
        monitoring_levels = {"NONE": T("No Monitoring"),
                             "MONITORING": T("Routine Monitoring"),
                             "DIAGNOSTICS": T("Targeted Diagnostics"),
                             "QUARANTINE": T("Quarantine"),
                             "FOLLOW-UP": T("Post-Quarantine Follow-Up"),
                             }
        diagnosis_status = {"UNKNOWN": T("Unknown"),
                            "PROBABLE": T("Probable"),
                            "CONFIRMED-POS": T("Confirmed Positive"),
                            "CONFIRMED-NEG": T("Confirmed Negative"),
                            }

        tablename = "disease_case"
        table = define_table(tablename,
                             Field("case_number", length=64, unique=True,
                                   ),
                             person_id(),
                             self.disease_disease_id(),
                             s3_date(),
                             Field("monitoring_level",
                                   label = T("Monitoring Level"),
                                   represent = S3Represent(options = monitoring_levels),
                                   requires = IS_IN_SET(monitoring_levels),
                                   ),
                             Field("diagnosis_status",
                                   label = T("Diagnosis Status"),
                                   represent = S3Represent(options = diagnosis_status),
                                   requires = IS_IN_SET(diagnosis_status),
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
        self.add_components(tablename,
                            disease_case_monitoring = "case_id",
                            disease_contact = "case_id",
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
        illness_status = {"UNKNOWN": T("Unknown"),
                          "ASYMPTOMATIC": T("Asymptomatic"),
                          "SYMPTOMATIC": T("Symptomatic"),
                          "SEVERE": T("Severely Ill"),
                          "DECEASED": T("Deceased"),
                          "RECOVERED": T("Recovered"),
                          }

        tablename = "disease_case_monitoring"
        table = define_table(tablename,
                             case_id(),
                             s3_datetime(default="now"),
                             Field("illness_status",
                                   requires = IS_IN_SET(illness_status),
                                   represent = S3Represent(options = illness_status),
                                   ),
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
        self.add_components(tablename,
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
                       ]
                     
        self.configure(tablename,
                       crud_form = S3SQLCustomForm(*crud_fields),
                       list_fields = ["date", 
                                      (T("Symptoms"), "symptom.name"),
                                      ],
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

        # @todo: CRUD strings

        # Pass names back to global scope (s3.*)
        return dict(disease_case_id = case_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():

        return dict()

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

    names = ("disease_contact",
             "disease_contact_person",
             )

    def model(self):
        
        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings

        define_table = self.define_table

        person_id = self.pr_person_id

        # =====================================================================
        # Contact: place/time when a people were in contact with a case
        #
        
        # Status of the tracing
        contact_tracing_status = {
            "OPEN": T("Open"),         # not all contact persons identified yet
            "COMPLETE": T("Complete"), # all contact persons identified
        }
        tablename = "disease_contact"
        table = define_table(tablename,
                             self.disease_case_id(label="Source Case"),
                             s3_datetime("start_date",
                                         label = T("From"),
                                         widget = S3DateTimeWidget(set_min="disease_contact_end_date",
                                                                   ),
                                         ),
                             s3_datetime("end_date",
                                         label = T("To"),
                                         widget = S3DateTimeWidget(set_max="disease_contact_start_date",
                                                                   ),
                                         ),
                             self.gis_location_id(),
                             Field("status",
                                   label = T("Tracing Status"),
                                   requires = IS_IN_SET(contact_tracing_status),
                                   represent = S3Represent(options=contact_tracing_status),
                                   ),
                             *s3_meta_fields())
                             
        represent = S3Represent(lookup=tablename, fields=["person_id", "date"])
        contact_id = S3ReusableField("contact_id", "reference %s" % tablename,
                                     label = T("Contact"),
                                     represent = represent,
                                     requires = IS_ONE_OF(db, "disease_contact.id",
                                                          represent,
                                                          ),
                                     sortby = "date",
                                     comment = S3AddResourceLink(f="contact",
                                                                 tooltip=T("Add a new contact"),
                                                                 ),
                                     )

        self.add_components(tablename,
                            disease_contact_person = "contact_id",
                            )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Register Contact Tracing"),
            title_display = T("Contact Tracing Information"),
            title_list = T("Contact Tracings"),
            title_update = T("Edit Contact Tracing"),
            title_upload = T("Import Contact Tracing"),
            label_list_button = T("List Contact Tracings"),
            label_delete_button = T("Delete Contact Tracing"),
            msg_record_created = T("Contact Tracing registered"),
            msg_record_modified = T("Contact Tracing updated"),
            msg_record_deleted = T("Contact Tracing deleted"),
            msg_list_empty = T("No Contact Tracings currently registered"))

        # =====================================================================
        # Contact Person: persons who've been involved in a contact
        #
        tablename = "disease_contact_person"
        table = define_table(tablename,
                             contact_id(),
                             person_id(),
                             s3_datetime(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Contact Person"),
            title_display = T("Contact Person Details"),
            title_list = T("Contact Persons"),
            title_update = T("Edit Contact Person"),
            title_upload = T("Import Contact Persons"),
            label_list_button = T("List Contact Persons"),
            label_delete_button = T("Delete Contact Person"),
            msg_record_created = T("Contact Person added"),
            msg_record_modified = T("Contact Person Details updated"),
            msg_record_deleted = T("Contact Person deleted"),
            msg_list_empty = T("No Contact Persons currently registered"))

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():

        return dict()

# =============================================================================
def disease_rheader(r, tabs=None):
    
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
                (T("Monitoring"), "case_monitoring"),
                (T("Contacts"), "contact"),
                ]

        rheader_fields = [["person_id"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "contact":

        tabs = [(T("Basic Details"), None),
                (T("Contact Persons"), "contact_person"),
                ]

        rheader_fields = [["case_id"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    return rheader

# END =========================================================================
