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
             "disease_symptom",
             "disease_disease_id",
             )

    def model(self):
        
        T = current.T
        db = current.db

        define_table = self.define_table
        
        # =====================================================================
        # Basic Disease Information
        #
        tablename = "disease_disease"
        table = define_table(tablename,
                             Field("name"),
                             Field("code"),
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
                                     
        # @todo: CRUD strings

        self.add_components(tablename,
                            disease_symptom = "disease_id",
                            )

        # =====================================================================
        # Symptom Information
        #
        tablename = "disease_symptom"
        table = define_table(tablename,
                             disease_id(),
                             Field("name"),
                             Field("description"),
                             # @todo: add info field for assessment method
                             *s3_meta_fields())

        # @todo: CRUD strings

        # Pass names back to global scope (s3.*)
        return dict(disease_disease_id = disease_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():

        return dict()

# =============================================================================
class CaseTrackingModel(S3Model):

    names = ("disease_case",
             "disease_case_id",
             "disease_case_status",
             )

    def model(self):
        
        T = current.T
        db = current.db

        define_table = self.define_table
        
        person_id = self.pr_person_id

        # =====================================================================
        # Case
        #
        tablename = "disease_case"
        table = define_table(tablename,
                             person_id(),
                             self.disease_disease_id(),
                             *s3_meta_fields())

        represent = S3Represent(lookup=tablename, fields=["person_id"])
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

        self.add_components(tablename,
                            disease_case_status = "case_id",
                            disease_contact = "case_id",
                            )

        # @todo: CRUD strings

        # =====================================================================
        # Status
        #
        tablename = "disease_case_status"
        table = define_table(tablename,
                             case_id(),
                             # @todo: add basic status information fields
                             s3_date(),
                             # @todo: add inline-component for symptoms
                             *s3_meta_fields())

        # @todo: CRUD strings

        # Pass names back to global scope (s3.*)
        return dict(disease_case_id = case_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():

        return dict()

# =============================================================================
class ContactTracingModel(S3Model):

    names = ("disease_contact",
             )

    def model(self):
        
        T = current.T
        db = current.db

        define_table = self.define_table

        person_id = self.pr_person_id

        # =====================================================================
        # Contact: place/time when a people were in contact with a case
        #
        tablename = "disease_contact"
        table = define_table(tablename,
                             self.disease_case_id(),
                             s3_datetime(),
                             self.gis_location_id(),
                             # @todo: elaborate
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

        # @todo: CRUD strings

        # =====================================================================
        # Contact Person: persons who've been involved in a contact
        #
        tablename = "disease_contact_person"
        table = define_table(tablename,
                             contact_id(),
                             person_id(),
                             s3_datetime(),
                             *s3_meta_fields())

        # @todo: CRUD strings

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
                ]
               
        rheader_fields = [["name"],
                          ["code"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)
        
    elif resourcename == "case":

        tabs = [(T("Basic Details"), None),
                (T("Status"), "status"),
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
