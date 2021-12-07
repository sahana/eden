# -*- coding: utf-8 -*-

""" Sahana Eden Patient Model

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("PatientModel",)

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class PatientModel(S3Model):
    """
        Patients

        @ToDo: Move to Medical module
    """

    names = ("patient_patient",
             "patient_relative",
             "patient_home",
             )

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis

        person_id = self.pr_person_id

        messages = current.messages

        add_components = self.add_components
        crud_strings = current.response.s3.crud_strings

        # ---------------------------------------------------------------------
        # Patients

        tablename = "patient_patient"
        self.define_table(tablename,
                          person_id(empty = False,
                                    comment = None,
                                    label = T("Patient"),
                                    widget = S3AddPersonWidget(),
                                    ),
                          Field("country",
                                label = T("Current Location Country"),
                                represent = lambda code: \
                                            gis.get_country(code, key_type="code") or \
                                            messages.UNKNOWN_OPT,
                                requires = IS_EMPTY_OR(IS_IN_SET_LAZY(
                                           lambda: gis.get_countries(key_type="code"),
                                           zero = messages.SELECT_LOCATION)),
                                ),
                          self.med_hospital_id(empty = False,
                                               label = T("Current Location Treating Hospital")
                                               ),
                          Field("phone", requires=IS_PHONE_NUMBER_MULTI(),
                                label = T("Current Location Phone Number"),
                                ),
                          Field("injuries", "text",
                                label = T("Injuries"),
                                widget = s3_comments_widget,
                                ),
                          s3_date("treatment_date",
                                  label = T("Date of Treatment"),
                                  ),
                          s3_date("return_date",
                                  label = T("Expected Return Home"),
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
            msg_list_empty = T("No Patients currently registered"),
            )

        patient_represent = patient_PatientRepresent(lookup = "patient_patient")

        # Reusable Field for Component Link
        patient_id = S3ReusableField("patient_id", "reference %s" % tablename,
                                     ondelete = "RESTRICT",
                                     represent = patient_represent,
                                     requires = IS_ONE_OF(db,
                                                          "patient_patient.id",
                                                          patient_represent,
                                                          ),
                                     )
        # Search method
        filter_widgets = [
            S3TextFilter(["person_id$first_name",
                          "person_id$middle_name",
                          "person_id$last_name",
                          #"person_id$person_details.local_name",
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
                       patient_relative = {"joinby": "patient_id",
                                           "multiple": False,
                                           },
                       # Homes
                       patient_home = {"joinby": "patient_id",
                                       "multiple": False,
                                       },
                       )

        # ---------------------------------------------------------------------
        # Relatives

        tablename = "patient_relative"
        self.define_table(tablename,
                          patient_id(readable = False,
                                     writable = False),
                          person_id(empty = False,
                                    comment = None,
                                    label = T("Accompanying Relative"),
                                    widget = S3AddPersonWidget(),
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
            msg_list_empty = T("No Relatives currently registered"),
            )

        # ---------------------------------------------------------------------
        # Homes
        #
        # @ToDo: Default the Home Phone Number from the Person, if available
        # @ToDo: Onvalidation to set the Relative's Contact

        tablename = "patient_home"
        self.define_table(tablename,
                          patient_id(readable = False,
                                     writable = False),
                          person_id(comment = None,
                                    label = T("Home Relative"),
                                    widget = S3AddPersonWidget(),
                                    ),
                          #person_id(label = T("Home Relative")),
                          self.gis_location_id(
                              label = T("Home Location"),
                              requires = IS_LOCATION(),
                              widget = S3LocationAutocompleteWidget(),
                              ),
                          Field("phone",
                                label = T("Home Phone Number"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
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
            msg_list_empty = T("No Homes currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

# =============================================================================
class patient_PatientRepresent(S3Represent):
    """
        Representation of Patient names by their full name
    """

    def lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for Patient names

            Args:
                key: Key for patient table
                values: Patient IDs
        """

        table = self.table
        ptable = current.s3db.pr_person

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = (key.belongs(values))

        left = ptable.on(table.person_id == ptable.id)

        db = current.db
        rows = db(query).select(table.id,
                                ptable.first_name,
                                ptable.middle_name,
                                ptable.last_name,
                                left = left,
                                limitby = (0, count),
                                )

        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row for a particular patient

            Args:
                row: patient_patient Row
        """

        try:
            return s3_fullname(row)
        except:
            return current.messages.UNKNOWN_OPT

# END =========================================================================
