# -*- coding: utf-8 -*-

""" Sahana Eden Patient Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
    @license: MIT

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

__all__ = ["S3PatientModel"]

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3PatientModel(S3Model):
    """
    """

    names = ["patient_patient",
             "patient_relative",
             "patient_home",
            ]

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis

        person_id = self.pr_person_id

        messages = current.messages

        s3_date_format = current.deployment_settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        add_components = self.add_components
        crud_strings = current.response.s3.crud_strings

        # ---------------------------------------------------------------------
        # Patients

        tablename = "patient_patient"
        self.define_table(tablename,
                          person_id(comment=None,
                                    label=T("Patient"),
                                    requires=IS_ADD_PERSON_WIDGET2(),
                                    widget=S3AddPersonWidget2(),
                                    ),
                          #person_id(empty=False, label = T("Patient")),
                          Field("country",
                                label = T("Current Location Country"),
                                requires = IS_EMPTY_OR(IS_IN_SET_LAZY(
                                           lambda: gis.get_countries(key_type="code"),
                                           zero = messages.SELECT_LOCATION)),
                                represent = lambda code: \
                                            gis.get_country(code, key_type="code") or \
                                            messages.UNKNOWN_OPT),
                          self.hms_hospital_id(
                                empty=False,
                                label = T("Current Location Treating Hospital")
                          ),
                          Field("phone", requires=s3_phone_requires,
                                label=T("Current Location Phone Number")),
                          Field("treatment_date", "date",
                                label=T("Date of Treatment"),
                                represent = s3_date_represent,
                                requires = IS_EMPTY_OR(IS_DATE(format=s3_date_format)),
                                widget = S3DateWidget()
                                ),
                          Field("return_date", "date",
                                label=T("Expected Return Home"),
                                represent = s3_date_represent,
                                requires = IS_EMPTY_OR(IS_DATE(format=s3_date_format)),
                                widget = S3DateWidget()
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add New Patient"),
            title_display = T("Patient Details"),
            title_list = T("Patients"),
            title_update = T("Edit Patient"),
            label_list_button = T("List Patients"),
            label_delete_button = T("Delete Patient"),
            msg_record_created = T("Patient added"),
            msg_record_modified = T("Patient updated"),
            msg_record_deleted = T("Patient deleted"),
            msg_list_empty = T("No Patients currently registered"))

        # Reusable Field for Component Link
        patient_id = S3ReusableField("patient_id", "reference %s" % tablename,
                                     requires = IS_ONE_OF(db,
                                                          "patient_patient.id",
                                                          self.patient_represent),
                                     represent = self.patient_represent,
                                     ondelete = "RESTRICT")

        # Search method
        filter_widgets = [
            S3TextFilter(["person_id$first_name",
                          "person_id$middle_name",
                          "person_id$last_name",
                          "person_id$local_name",
                         ],
                         label = T("Search"),
                         comment=T("To search for a patient, enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all patients."),
                        ),
            S3OptionsFilter("country",
                            label = messages.COUNTRY,
                            cols = 2,
                            hidden = True,
                           ),
            S3OptionsFilter("hospital_id",
                            label = T("Hospital"),
                            cols = 2,
                            hidden = True,
                           ),
        ]

        # Configuration
        self.configure(tablename,
                       filter_widgets = filter_widgets,
                      )

        # Components
        add_components(tablename,
                       # Relatives
                       patient_relative={"joinby": "patient_id",
                                         "multiple": False,
                                        },
                       # Homes
                       patient_home={"joinby": "patient_id",
                                     "multiple": False,
                                    },
                      )

        # ---------------------------------------------------------------------
        # Relatives

        tablename = "patient_relative"
        self.define_table(tablename,
                          patient_id(readable=False, writable=False),
                          person_id(comment=None,
                                    label=T("Accompanying Relative"),
                                    requires=IS_ADD_PERSON_WIDGET2(),
                                    widget=S3AddPersonWidget2(),
                                    ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        ADD_RELATIVE = T("New Relative")
        crud_strings[tablename] = Storage(
            label_create = ADD_RELATIVE,
            title_display = T("Relative Details"),
            title_list = T("Relatives"),
            title_update = T("Edit Relative"),
            label_list_button = T("List Relatives"),
            label_delete_button = T("Delete Relative"),
            msg_record_created = T("Relative added"),
            msg_record_modified = T("Relative updated"),
            msg_record_deleted = T("Relative deleted"),
            msg_list_empty = T("No Relatives currently registered"))

        # ---------------------------------------------------------------------
        # Homes
        #
        # @ToDo: Default the Home Phone Number from the Person, if available
        # @ToDo: Onvalidation to set the Relative's Contact

        tablename = "patient_home"
        self.define_table(tablename,
                          patient_id(readable=False, writable=False),
                          person_id(comment=None,
                                    label=T("Home Relative"),
                                    requires=IS_ADD_PERSON_WIDGET2(),
                                    widget=S3AddPersonWidget2(),
                                    ),
                          #person_id(label = T("Home Relative")),
                          self.gis_location_id(
                              label=T("Home City"),
                              widget = S3LocationAutocompleteWidget(level="L2"),
                              requires = IS_LOCATION(level="L2")
                          ),
                          Field("phone",
                                requires=IS_EMPTY_OR(s3_phone_requires),
                                label=T("Home Phone Number")),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add New Home"),
            title_display = T("Home Details"),
            title_list = T("Homes"),
            title_update = T("Edit Home"),
            label_list_button = T("List Homes"),
            label_delete_button = T("Delete Home"),
            msg_record_created = T("Home added"),
            msg_record_modified = T("Home updated"),
            msg_record_deleted = T("Home deleted"),
            msg_list_empty = T("No Homes currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def patient_represent(id, row=None):
        """
            Represent a Patient by their full name
        """

        if row:
            pass
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.patient_patient
            row = db(table.id == id).select(table.person_id,
                                            limitby=(0, 1)).first()
        try:
            return s3_fullname(row.person_id)
        except:
            return current.messages.UNKNOWN_OPT

# END =========================================================================
