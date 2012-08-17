# -*- coding: utf-8 -*-

""" Sahana Eden Vehicle Model

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

__all__ = ["S3VehicleModel"]

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class S3VehicleModel(S3Model):
    """
        Vehicle Management Functionality

        http://eden.sahanafoundation.org/wiki/BluePrint/Vehicle

        @ToDo: Merge into Transport module
    """

    names = ["vehicle_vehicle",
             "vehicle_gps",
             "vehicle_vehicle_id",
            ]

    def model(self):

        T = current.T
        db = current.db

        asset_id = self.asset_asset_id

        crud_strings = current.response.s3.crud_strings

        # These are Porto-specific Types
        # @ToDo: Move to database table to allow prepop for different deployments
        vehicle_type_opts = {
            "VSAT": T("Rescue Vehicle Tactical Assistance"),
            "VLCI": T("Fire Fighter Light Vehicle"),
            "ABTD": T("Patient Transportation Ambulance"),
            "ABSC": T("Rescue Ambulance"),
            "VUCI": T("Fire Fighter Urban Vehicle"),
            "VTTU": T("Urban Tank Tactical Vehicle"),
            "VCOT": T("Command Tactical Operational Vehicle"),
            "VFCI": T("Fire Fighter Forest Vehicle"),
            "VE30": T("Ladder Vehicle 30"),
            "VTPT": T("Person Transportation Tactical Vehicle"),
            "VTTR": T("Rural Tank Tactical Vehicle"),
            "VTTF": T("Forest Tank Tactical Vehicle"),
            "VECI": T("Fire Fighter Special Vehicle"),
            "VRCI": T("Fire Fighter Rural Vehicle"),
            "MOTA": T("Motorcycle"),
            "VTPG": T("General Person Transportation Vehicle"),
            "VTGC": T("Big Capacity Tank Vehicle"),
            "ABTM": T("Doolie Transportation Ambulance"),
            "VOPE": T("Specific Operations Vehicle"),
            "VETA": T("Technical Support Vehicle"),
            "VPME": T("Special Multirisk Protection Vehicle"),
            "VAME": T("Scubadiving Support Vehicle"),
            "VAPA": T("Alimentary Support Vehicle"),
        }

        # Vehicles are a component of Assets
        tablename = "vehicle_vehicle"
        table = self.define_table(tablename,
                                  Field("type",
                                        requires = IS_NULL_OR(IS_IN_SET(vehicle_type_opts)),
                                        represent = lambda opt: \
                                            vehicle_type_opts.get(opt, opt),
                                        label=T("Type")),
                                  Field("name",
                                        label=T("ID")), # often the License Plate
                                  asset_id(),
                                  Field("gps",
                                        label=T("GPS ID")),
                                  Field("mileage", "integer",
                                        label=T("Current Mileage"),
                                        represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                                  Field("service_mileage", "integer",
                                        label=T("Service Due"),
                                        comment=T("Mileage"),
                                        represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                                  s3_date("service_date",
                                          label=T("Service Due")
                                          ),
                                  s3_date("insurance_date",
                                          label=T("Insurance Renewal Due")
                                          ),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_VEHICLE_DETAILS = T("Add Vehicle Detail")
        crud_strings[tablename] = Storage(
            title_create = ADD_VEHICLE_DETAILS,
            title_display = T("Vehicle Details"),
            title_list = T("Vehicles"),
            title_update = T("Edit Vehicle Details"),
            title_search = T("Search Vehicle Details"),
            subtitle_create = T("Add Vehicle Details"),
            label_list_button = T("List Vehicle Details"),
            label_create_button = ADD_VEHICLE_DETAILS,
            label_delete_button = T("Delete Vehicle Details"),
            msg_record_created = T("Vehicle Details added"),
            msg_record_modified = T("Vehicle Details updated"),
            msg_record_deleted = T("Vehicle Details deleted"),
            msg_list_empty = T("No Vehicle Details currently defined"))

        vehicle_id = S3ReusableField("vehicle_id", table,
                                      requires = IS_NULL_OR(
                                                    IS_ONE_OF(db,
                                                              "vehicle_vehicle.id",
                                                              "%(name)s")),
                                      represent = lambda id: \
                                        (id and [db.vehicle_vehicle[id].name] or [current.messages.NONE])[0],
                                      label = T("Vehicle"),
                                      ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # GPS records
        # - designed to be pulled in automatically, not entered manually
        #
        # @ToDo: Move these to gis.py - nothing here is vehicle-specific
        #
        tablename = "vehicle_gps"
        table = self.define_table(tablename,
                                  asset_id(),
                                  Field("lat",
                                        requires=IS_LAT(),
                                        label=T("Latitude")),
                                  Field("lon",
                                        requires=IS_LON(),
                                        label=T("Longitude")),
                                  Field("direction",
                                        label=T("Direction")),
                                  Field("speed",
                                        label=T("Speed")),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_GPS = T("Add GPS data")
        crud_strings[tablename] = Storage(
            title_create = ADD_GPS,
            title_display = T("GPS data"),
            title_list = T("GPS data"),
            title_update = T("Edit GPS data"),
            title_search = T("Search GPS data"),
            subtitle_create = T("Add GPS data"),
            label_list_button = T("List GPS data"),
            label_create_button = ADD_GPS,
            label_delete_button = T("Delete GPS data"),
            msg_record_created = T("GPS data added"),
            msg_record_modified = T("GPS data updated"),
            msg_record_deleted = T("GPS data deleted"),
            msg_list_empty = T("No GPS data currently registered"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    vehicle_vehicle_id = vehicle_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Return safe defaults for names in case the model is disabled """

        vehicle_id = S3ReusableField("vehicle_id", "integer",
                                     writable=False,
                                     readable=False)
        return Storage(
                    vehicle_vehicle_id = vehicle_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def vehicle_gps_onaccept(form):
        """
            Set the current location from the latest GPS record
        """

        vars = form.vars
        lat = vars.lat
        lon = vars.lon
        if lat is not None and lon is not None:
            # Lookup the Asset Code
            db = current.db
            table = db.asset_asset
            vehicle = db(table.id == vars.id).select(table.number,
                                                     limitby=(0, 1)).first()
            if vehicle:
                name = vehicle.number
            else:
                name = "vehicle_%i" % vars.id
            # Insert a record into the locations table
            ltable = db.gis_location
            location = ltable.insert(name=name, lat=lat, lon=lon)
            # Set the Current Location of the Asset to this Location
            # @ToDo: Currently we set the Base Location as Mapping doesn't support S3Track!
            db(table.id == vars.id).update(location_id=location)

# END =========================================================================
