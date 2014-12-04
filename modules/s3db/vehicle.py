# -*- coding: utf-8 -*-

""" Sahana Eden Vehicle Model

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
             "vehicle_gps",
             "vehicle_vehicle_id",
             )

    def model(self):

        T = current.T
        db = current.db

        asset_id = self.asset_asset_id

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Vehicle Types
        #
        tablename = "vehicle_vehicle_type"
        define_table(tablename,
                     Field("code", unique=True, notnull=True, length=64,
                           label = T("Code"),
                           ),
                     Field("name", notnull=True, length=64,
                           label = T("Name"),
                           ),
                     #Field("parent", "reference event_event_type", # This form of hierarchy may not work on all Databases
                     #      label = T("SubType of"),
                     #      ondelete = "RESTRICT",
                     #      readable = hierarchical_vehicle_types,
                     #      writable = hierarchical_vehicle_types,
                     #      ),
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

        vehicle_type_id = S3ReusableField("vehicle_type_id", "reference %s" % tablename,
                                          label = T("Vehicle Type"),
                                          ondelete = "RESTRICT",
                                          represent = type_represent,
                                          requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "event_vehicle_type.id",
                                                                  type_represent,
                                                                  orderby="event_vehicle_type.code",
                                                                  sort=True)),
                                          sortby = "code",
                                          #widget = event_type_widget,
                                          #comment = event_type_comment,
                                          )

        # ---------------------------------------------------------------------
        # Vehicles
        #   a type of Asset
        #
        tablename = "vehicle_vehicle"
        define_table(tablename,
                     asset_id(),
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
                           represent = lambda v, row=None: \
                            IS_INT_AMOUNT.represent(v),
                           ),
                     Field("service_mileage", "integer",
                           comment = T("Mileage"),
                           label = T("Service Due"),
                           represent = lambda v, row=None: \
                            IS_INT_AMOUNT.represent(v),
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

        represent = S3Represent(lookup=tablename)
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

        self.configure(tablename,
                       context = {"location": "asset_id$location_id"
                                  },
                       )

        # ---------------------------------------------------------------------
        # GPS records
        # - designed to be pulled in automatically, not entered manually
        #
        # @ToDo: Move these to gis.py - nothing here is vehicle-specific
        #
        tablename = "vehicle_gps"
        define_table(tablename,
                     asset_id(),
                     Field("lat",
                           label = T("Latitude"),
                           requires = IS_LAT(),
                           ),
                     Field("lon",
                           label = T("Longitude"),
                           requires = IS_LON(),
                           ),
                     Field("direction",
                           label = T("Direction"),
                           ),
                     Field("speed",
                           label = T("Speed"),
                           ),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add GPS data"),
            title_display = T("GPS data"),
            title_list = T("GPS data"),
            title_update = T("Edit GPS data"),
            label_list_button = T("List GPS data"),
            label_delete_button = T("Delete GPS data"),
            msg_record_created = T("GPS data added"),
            msg_record_modified = T("GPS data updated"),
            msg_record_deleted = T("GPS data deleted"),
            msg_list_empty = T("No GPS data currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(vehicle_vehicle_id = vehicle_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Return safe defaults for names in case the model is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(vehicle_vehicle_id = lambda **attr: dummy("vehicle_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def vehicle_gps_onaccept(form):
        """
            Set the current location from the latest GPS record
        """

        form_vars = form.vars
        lat = form_vars.lat
        lon = form_vars.lon
        if lat is not None and lon is not None:
            # Lookup the Asset Code
            db = current.db
            table = db.asset_asset
            vehicle = db(table.id == form_vars.id).select(table.number,
                                                          limitby=(0, 1)
                                                          ).first()
            if vehicle:
                name = vehicle.number
            else:
                name = "vehicle_%i" % form_vars.id
            # Insert a record into the locations table
            ltable = db.gis_location
            location = ltable.insert(name=name, lat=lat, lon=lon)
            # Set the Current Location of the Asset to this Location
            # @ToDo: Currently we set the Base Location as Mapping doesn't support S3Track!
            db(table.id == form_vars.id).update(location_id=location)

# END =========================================================================
