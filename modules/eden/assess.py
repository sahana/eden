# -*- coding: utf-8 -*-

""" Sahana Eden Assessments Model

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3AssessBuildingModel"
           ]

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *

T = current.T
assess_property_type_opts = {
    1 : T("Single Family"),
    2 : T("Multi-Family/Apts"),
    3 : T("Residence is Vacation Home"),
    4 : T("Business"),
    }

# =============================================================================
class S3AssessBuildingModel(S3Model):
    """
        Building Damage Assessment form
    """

    names = ["assess_building",
             ]

    def model(self):

        T = current.T
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Building Assessment
        #
        ownership_opts = {1: T("Rent"),
                          2: T("Own"),
                          }
        tablename = "assess_building"
        table = self.define_table(tablename,
                                  s3_datetime(label=T("Intake Date/Time")),
                                  Field("assessor1",
                                        label=T("Assessor 1")),
                                  Field("assessor2",
                                        label=T("Assessor 2")),
                                  Field("name",
                                        label=T("Name")),
                                  Field("address1",
                                        label=T("Address (line 1)")),
                                  Field("address2",
                                        label=T("Address (line 2)")),
                                  Field("homeowner_availability",
                                        label=T("Homeowner Availability")),
                                  Field("type_of_property", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_property_type_opts,
                                                              multiple=True)
                                                ),
                                        represent = self.assess_building_property_type_represent,
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=4, **attr),
                                        label=T("Type of Property")),
                                  Field("inhabitants", "integer",
                                        label=T("# of Inhabitants")),
                                  Field("year_built", "integer",
                                        requires = IS_EMPTY_OR(
                                                    IS_INT_IN_RANGE(1800, 2012)
                                                    ),
                                        label=T("Year Built")),
                                  Field("ownership", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(ownership_opts)
                                                ),
                                        represent = lambda opt:
                                            ownership_opts.get(opt,
                                                               UNKNOWN_OPT),
                                        label=T("Ownership")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_ASSESS = T("Add Assessment")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_ASSESS,
            title_display = T("Assessment Details"),
            title_list = T("Assessments"),
            title_update = T("Edit Assessment"),
            title_search = T("Search Assessments"),
            subtitle_create = T("Add New Assessment"),
            label_list_button = T("List Assessments"),
            label_create_button = ADD_ASSESS,
            label_delete_button = T("Delete Assessment"),
            msg_record_created = T("Assessment added"),
            msg_record_modified = T("Assessment updated"),
            msg_record_deleted = T("Assessment deleted"),
            msg_list_empty = T("No Assessments found")
        )

        #self.configure(tablename,
        #               )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def assess_building_property_type_represent(ids):
        """
            Represent Property Types
        """

        if not ids:
            return current.messages["NONE"]

        ids = [ids] if type(ids) is not list else ids

        strings = [str(assess_property_type_opts.get(id)) for id in ids]

        return ", ".join(strings)

# END =========================================================================
