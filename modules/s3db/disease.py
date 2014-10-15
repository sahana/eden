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

        # @todo: CRUD strings
        # @todo: components

        # =====================================================================
        # Status
        #
        tablename = "disease_case_status"
        table = define_table(tablename,
                             # @todo: link to person + case
                             # @todo: add inline-component for symptoms
                             # @todo: add basic status information fields
                             *s3_meta_fields())

        # @todo: CRUD strings

        # Pass names back to global scope (s3.*)
        return dict()

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
        # Contact
        #
        tablename = "disease_contact"
        table = define_table(tablename,
                             person_id("primary_person_id"),
                             person_id("secondary_person_id"),
                             # @todo: elaborate
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
                ]

        rheader_fields = [["person_id"],
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    return rheader

# END =========================================================================
