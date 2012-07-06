# -*- coding: utf-8 -*-

""" Sahana Eden Patient Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

        add_component = self.add_component
        crud_strings = current.response.s3.crud_strings

        # ---------------------------------------------------------------------
        # Patients

        tablename = "patient_patient"
        table = self.define_table(tablename,
                                  person_id(widget=S3AddPersonWidget(),
                                            requires=IS_ADD_PERSON_WIDGET(),
                                            label=T("Patient"),
                                            comment=None),
                                  #person_id(empty=False, label = T("Patient")),
                                  Field("country",
                                        label = T("Current Location Country"),
                                        requires = IS_NULL_OR(IS_IN_SET_LAZY(
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
                                        requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                        widget = S3DateWidget()
                                        ),
                                  Field("return_date", "date",
                                        label=T("Expected Return Home"),
                                        represent = s3_date_represent,
                                        requires = IS_NULL_OR(IS_DATE(format=s3_date_format)),
                                        widget = S3DateWidget()
                                       ),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_PATIENT = T("New Patient")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PATIENT,
            title_display = T("Patient Details"),
            title_list = T("Patients"),
            title_update = T("Edit Patient"),
            title_search = T("Search Patients"),
            subtitle_create = T("Add New Patient"),
            label_list_button = T("List Patients"),
            label_create_button = ADD_PATIENT,
            label_delete_button = T("Delete Patient"),
            msg_record_created = T("Patient added"),
            msg_record_modified = T("Patient updated"),
            msg_record_deleted = T("Patient deleted"),
            msg_list_empty = T("No Patients currently registered"))

        # Reusable Field for Component Link
        patient_id = S3ReusableField("patient_id", db.patient_patient,
                                     requires = IS_ONE_OF(db,
                                                          "patient_patient.id",
                                                          self.patient_represent),
                                     represent = self.patient_represent,
                                     ondelete = "RESTRICT")

        # Components
        # Relatives
        add_component("patient_relative",
                      patient_patient=dict(joinby="patient_id",
                                           multiple=False))

        # Homes
        add_component("patient_home",
                      patient_patient=dict(joinby="patient_id",
                                           multiple=False))

        # ---------------------------------------------------------------------
        # Relatives

        tablename = "patient_relative"
        table = self.define_table(tablename,
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
        crud_strings[tablename] = Storage(
            title_create = ADD_RELATIVE,
            title_display = T("Relative Details"),
            title_list = T("Relatives"),
            title_update = T("Edit Relative"),
            title_search = T("Search Relatives"),
            subtitle_create = T("Add New Relative"),
            label_list_button = T("List Relatives"),
            label_create_button = ADD_RELATIVE,
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
        table = self.define_table(tablename,
                                  patient_id(readable=False, writable=False),
                                  person_id(widget=S3AddPersonWidget(),
                                            requires=IS_ADD_PERSON_WIDGET(),
                                            label=T("Home Relative"),
                                            comment=None),
                                  #person_id(label = T("Home Relative")),
                                  self.gis_location_id(
                                    label=T("Home City"),
                                    widget = S3LocationAutocompleteWidget(level="L2"),
                                    requires = IS_LOCATION(level="L2")
                                    ),
                                  Field("phone",
                                        requires=IS_NULL_OR(s3_phone_requires),
                                        label=T("Home Phone Number")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_HOME = T("New Home")
        crud_strings[tablename] = Storage(
            title_create = ADD_HOME,
            title_display = T("Home Details"),
            title_list = T("Homes"),
            title_update = T("Edit Home"),
            title_search = T("Search Homes"),
            subtitle_create = T("Add New Home"),
            label_list_button = T("List Homes"),
            label_create_button = ADD_HOME,
            label_delete_button = T("Delete Home"),
            msg_record_created = T("Home added"),
            msg_record_modified = T("Home updated"),
            msg_record_deleted = T("Home deleted"),
            msg_list_empty = T("No Homes currently registered"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def patient_represent(id):
        """
        """

        if isinstance(id, Row):
            # Do not repeat the lookup if already done by IS_ONE_OF or RHeader
            patient = id
        else:
            db = current.db
            table = db.patient_patient
            patient = db(table.id == id).select(table.person_id,
                                                limitby=(0, 1)).first()
        try:
            represent = s3_fullname(patient.person_id)
        except:
            return current.messages.UNKNOWN_OPT

        return represent

# END =========================================================================
