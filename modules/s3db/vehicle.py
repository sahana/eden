# -*- coding: utf-8 -*-

""" Sahana Eden Vehicle Model

    @copyright: 2009-2020 (c) Sahana Software Foundation
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

__all__ = ("S3VehicleModel",)

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class S3VehicleModel(S3Model):
    """
        Vehicle Management Functionality

        http://eden.sahanafoundation.org/wiki/BluePrint/Vehicle
    """

    names = ("vehicle_vehicle_type",
             "vehicle_vehicle",
             "vehicle_vehicle_id",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        float_represent = IS_FLOAT_AMOUNT.represent
        int_represent = IS_INT_AMOUNT.represent

        # ---------------------------------------------------------------------
        # Vehicle Types
        #
        tablename = "vehicle_vehicle_type"
        define_table(tablename,
                     # @ToDo: deployment_setting for use of Code
                     Field("code", length=64,
                           label = T("Code"),
                           requires = IS_LENGTH(64),
                           ),
                     Field("name", length=128,
                           label = T("Name"),
                           requires = IS_LENGTH(128),
                           ),
                     #Field("parent", "reference event_event_type", # This form of hierarchy may not work on all Databases
                     #      label = T("SubType of"),
                     #      ondelete = "RESTRICT",
                     #      readable = hierarchical_vehicle_types,
                     #      writable = hierarchical_vehicle_types,
                     #      ),
                     Field("vehicle_height", "double",
                           label = T("Vehicle Height (m)"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           ),
                     Field("vehicle_weight", "double",
                           comment = T("Gross Vehicle Weight Rating (GVWR)"),
                           label = T("Vehicle Weight (kg)"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           ),
                     Field("weight", "double",
                           label = T("Payload Weight (kg)"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" %
                                                  (T("Payload Weight"),
                                                   T("Gross Vehicle Weight Rating (GVWR) minus Curb Weight")
                                                   )
                                         ),
                           ),
                     Field("length", "double",
                           label = T("Payload Length (m)"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           ),
                     Field("width", "double",
                           label = T("Payload Width (m)"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           ),
                     Field("height", "double",
                           label = T("Payload Height (m)"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           ),
                     Field("volume", "double",
                           label = T("Payload Volume (m3)"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        type_represent = S3Represent(lookup=tablename,
                                     fields=["code", "name"],
                                     translate=True)

        crud_strings[tablename] = Storage(
            label_create = T("Create Vehicle Type"),
            title_display = T("Vehicle Type Details"),
            title_list = T("Vehicle Types"),
            title_update = T("Edit Vehicle Type"),
            title_upload = T("Import Vehicle Types"),
            label_list_button = T("List Vehicle Types"),
            label_delete_button = T("Delete Vehicle Type"),
            msg_record_created = T("Vehicle Type added"),
            msg_record_modified = T("Vehicle Type updated"),
            msg_record_deleted = T("Vehicle Type removed"),
            msg_list_empty = T("No Vehicle Types currently registered")
            )

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("code",)),
                  )

        vehicle_type_id = S3ReusableField("vehicle_type_id", "reference %s" % tablename,
                                          label = T("Vehicle Type"),
                                          ondelete = "RESTRICT",
                                          represent = type_represent,
                                          requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "vehicle_vehicle_type.id",
                                                                  type_represent,
                                                                  orderby="vehicle_vehicle_type.code",
                                                                  sort=True)),
                                          sortby = "code",
                                          # Allow changing by whether hierarchical or not
                                          #widget = vehicle_type_widget,
                                          #comment = vehicle_type_comment,
                                          )

        # ---------------------------------------------------------------------
        # Vehicles
        #   a type of Asset
        #
        tablename = "vehicle_vehicle"
        define_table(tablename,
                     self.asset_asset_id(),
                     vehicle_type_id(),
                     Field("name",
                           comment = T("e.g. License Plate"),
                           label = T("ID"),
                           ),
                     Field("gps",
                           label = T("GPS ID"),
                           ),
                     Field("mileage", "integer",
                           label = T("Current Mileage"),
                           represent = int_represent,
                           requires = IS_EMPTY_OR(
                                          IS_INT_IN_RANGE(0, None)
                                          ),
                           ),
                     Field("service_mileage", "integer",
                           comment = T("Mileage"),
                           label = T("Service Due"),
                           represent = int_represent,
                           requires = IS_EMPTY_OR(
                                          IS_INT_IN_RANGE(0, None)
                                          ),
                           ),
                     s3_date("service_date",
                             label = T("Service Due"),
                             ),
                     s3_date("insurance_date",
                             label = T("Insurance Renewal Due"),
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Vehicle Details"),
            title_display = T("Vehicle Details"),
            title_list = T("Vehicles"),
            title_update = T("Edit Vehicle Details"),
            label_list_button = T("List Vehicle Details"),
            label_delete_button = T("Delete Vehicle Details"),
            msg_record_created = T("Vehicle Details added"),
            msg_record_modified = T("Vehicle Details updated"),
            msg_record_deleted = T("Vehicle Details deleted"),
            msg_list_empty = T("No Vehicle Details currently defined"))

        represent = S3Represent(lookup = tablename)

        vehicle_id = S3ReusableField("vehicle_id", "reference %s" % tablename,
                                     label = T("Vehicle"),
                                     ondelete = "RESTRICT",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db,
                                                              "vehicle_vehicle.id",
                                                              represent,
                                                              )),
                                     )

        configure(tablename,
                  context = {"location": "asset_id$location_id"
                             },
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"vehicle_vehicle_id": vehicle_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Return safe defaults for names in case the model is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"vehicle_vehicle_id": lambda **attr: dummy("vehicle_id"),
                }

# END =========================================================================
