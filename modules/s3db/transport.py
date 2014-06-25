# -*- coding: utf-8 -*-

""" Sahana Eden Transport Model

    @copyright: 2012-14 (c) Sahana Software Foundation
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

__all__ = ["S3TransportModel",
		   "S3VehicleModel",
           ]

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class S3TransportModel(S3Model):
    """
        http://eden.sahanafoundation.org/wiki/BluePrint/Transport
    """

    names = ["transport_airport",
             "transport_heliport",
             "transport_seaport",
             ]

    def model(self):

        T = current.T
        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Airports
        #
        storage_types = {
            1: T("covered"),
            2: T("uncovered"),
        }
        transport_airport_capacity_opts = {
            1: "",
            2: T("number of planes"),
            3: T("m3")
        }

        tablename = "transport_airport"
        define_table(tablename,
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label=T("Name")),
                     Field("code",
                           length=10,
                           # Deployments that don't wants office codes can hide them
                           #readable=False,
                           #writable=False,
                           # Mayon compatibility
                           # @ToDo: Deployment Setting to add validator to make these unique
                           #notnull=True,
                           #unique=True,
                           label=T("Code")),
                     organisation_id(),
                     location_id(),
                     Field("restrictions", "text",
                           label=T("Restrictions")),
                     Field("ils", "boolean",
                           represent=lambda bool: \
                             (bool and [T("Yes")] or [T("No")])[0],
                           label=T("Instrument Landing System")),
                     Field("lighting", "boolean",
                           represent=lambda bool: \
                             (bool and [T("Yes")] or [T("No")])[0],
                           label=T("Lighting")),
                     Field("immigration_customs_capabilities", "text",
                           label=T("Immigration and Customs Capabilities")),
                     Field("aircraft_max_size", "text",
                           label=T("Aircraft Maximum Size")),
                     Field("security_desc", "text",
                           label=T("Security Description"),
                           comment=DIV(_class="tooltip",
                                       _title="%s|%s" % (T("Security Description"),
                                                         T("Description of perimeter fencing, security guards, security lighting.")))),
                     # @ToDo: put storage type inline
                     Field("storage_capacity", "double",
                           label=T("Storage Capacity (m3)")),
                     Field("storage_type", "integer",
                           requires = IS_EMPTY_OR(IS_IN_SET(storage_types)),
                           label=T("Storage Type")),
                     # @ToDo: put units inline
                     Field("parking_tarmac_space", "double",
                           label=T("Parking/Tarmac Space Capacity")),
                     Field("capacity", "integer",
                           label = T("Parking/Tarmac Space Units"),
                           requires = IS_IN_SET(transport_airport_capacity_opts, zero=None),
                           default = 1,
                           represent = lambda opt: \
                            transport_airport_capacity_opts.get(opt, UNKNOWN_OPT)),
                     Field("helipad_info", "text",
                           label=T("Helipad Information")),
                     self.pr_person_id(label=T("Information Source")),
                     Field("obsolete", "boolean",
                           label=T("Obsolete"),
                           represent=lambda bool: \
                             (bool and [T("Obsolete")] or [current.messages["NONE"]])[0],
                           default=False,
                           readable=False,
                           writable=False),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_AIRPORT = T("Create Airport")
        crud_strings[tablename] = Storage(
            label_create=T("Create Airport"),
            title_display=T("Airport Details"),
            title_list=T("Airports"),
            title_update=T("Edit Airport"),
            title_upload=T("Import Airports"),
            label_list_button=T("List Airports"),
            label_delete_button=T("Delete Airport"),
            msg_record_created=T("Airport added"),
            msg_record_modified=T("Airport updated"),
            msg_record_deleted=T("Airport deleted"),
            msg_list_empty=T("No Airports currently registered"))

        configure(tablename,
                  onaccept = self.transport_airport_onaccept,
                  super_entity = "org_site",
                  )

        # ---------------------------------------------------------------------
        # Heliports
        #
        tablename = "transport_heliport"
        define_table(tablename,
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label=T("Name")),
                     Field("code",
                           length=10,
                           # Deployments that don't wants office codes can hide them
                           #readable=False,
                           #writable=False,
                           # Mayon compatibility
                           # @ToDo: Deployment Setting to add validator to make these unique
                           #notnull=True,
                           #unique=True,
                           label=T("Code")),
                     organisation_id(),
                     location_id(),
                     Field("obsolete", "boolean",
                           label=T("Obsolete"),
                           represent=lambda opt: \
                                     (opt and [T("Obsolete")] or [current.messages["NONE"]])[0],
                           default=False,
                           readable=False,
                           writable=False),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_HELIPORT = T("Create Heliport")
        crud_strings[tablename] = Storage(
            label_create=T("Create Heliport"),
            title_display=T("Heliport Details"),
            title_list=T("Heliports"),
            title_update=T("Edit Heliport"),
            title_upload=T("Import Heliports"),
            label_list_button=T("List Heliports"),
            label_delete_button=T("Delete Heliport"),
            msg_record_created=T("Heliport added"),
            msg_record_modified=T("Heliport updated"),
            msg_record_deleted=T("Heliport deleted"),
            msg_list_empty=T("No Heliports currently registered"))

        configure(tablename,
                  onaccept = self.transport_heliport_onaccept,
                  super_entity = "org_site",
                  )

        # ---------------------------------------------------------------------
        # Seaports
        #
        ownership_opts = {
            1: T("Public"),
            2: T("Private")
        }

        unit_opts = {
            1: T("ft"),
            2: T("m")
        }

        tablename = "transport_seaport"
        define_table(tablename,
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label=T("Name")),
                     Field("code",
                           length=10,
                           # Deployments that don't wants office codes can hide them
                           #readable=False,
                           #writable=False,
                           # Mayon compatibility
                           # @ToDo: Deployment Setting to add validator to make these unique
                           #notnull=True,
                           #unique=True,
                           label=T("Code")),
                     Field("ownership_type", "integer",
                           requires = IS_IN_SET(ownership_opts, zero=None),
                           default = 1,
                           label = T("Ownership"),
                           represent = lambda opt: \
                           ownership_opts.get(opt, UNKNOWN_OPT)),
                     Field("max_height", "double",
                           label=T("Max Height")),
                     Field("max_height_units", "integer",
                           requires = IS_IN_SET(unit_opts, zero=None),
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                           unit_opts.get(opt, UNKNOWN_OPT)),
                     Field("roll_on_off", "boolean",
                           default=False,
                           represent=lambda opt: \
                                     (opt and [T("Yes")] or [T("No")])[0],
                           label=T("Roll On Roll Off Berth")),
                     Field("cargo_pier_depth", "double",
                           label=T("Cargo Pier Depth")),
                     Field("cargo_pier_depth_units", "integer",
                           requires = IS_IN_SET(unit_opts, zero=None),
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT)),
                     Field("oil_terminal_depth", "double",
                           label=T("Oil Terminal Depth")),
                     Field("oil_terminal_depth_units", "integer",
                           requires = IS_IN_SET(unit_opts, zero=None),
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT)),
                     Field("dry_dock", "boolean",
                           default=False,
                           represent=lambda opt: \
                                     (opt and [T("Yes")] or [T("No")])[0],
                           label=T("Dry Dock")),
                     Field("vessel_max_length", "double",
                           label=T("Vessel Max Length")),
                     Field("vessel_max_length_units", "integer",
                           requires = IS_IN_SET(unit_opts, zero=None),
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                           unit_opts.get(opt, UNKNOWN_OPT)),
                     Field("repairs", "text",
                           label=T("Repairs")),
                     Field ("shelter", "text",
                           label=T("Shelter")),
                     Field("warehouse_capacity", "double",
                           label=T("Warehousing Storage Capacity")),
                     Field("secure_storage_capacity", "double",
                           label=T("Secure Storage Capacity")),
                     Field("customs_warehouse_capacity", "double",
                           label=T("Customs Warehousing Storage Capacity")),
                     Field("tugs", "integer",
                           label=T("Number of Tugboats")),
                     Field("tug_capacity", "double",
                           label=T("Tugboat Capacity")),
                     Field("barges", "integer",
                           label=T("Number of Barges")),
                     Field("barge_capacity", "double",
                           label=T("Barge Capacity")),
                     Field("loading_equipment", "text",
                           label=T("Loading Equipment")),
                     Field("customs_capacity", "text",
                           label=T("Customs Capacity")),
                     Field("security", "text",
                           label=T("Security")),
                     Field("high_tide_depth", "double",
                           label=T("High Tide Depth")),
                     Field("high_tide_depth_units", "integer",
                           requires = IS_IN_SET(unit_opts, zero=None),
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT)),
                     Field("low_tide_depth", "double",
                           label=T("Low Tide Depth")),
                     Field("low_tide_depth_units", "integer",
                           requires = IS_IN_SET(unit_opts, zero=None),
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT)),
                     Field("flood_depth", "double",
                           label=T("Flood Depth")),
                     Field("flood_depth_units", "integer",
                           requires = IS_IN_SET(unit_opts, zero=None),
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT)),
                     organisation_id(),
                     location_id(),
                     Field("obsolete", "boolean",
                           label=T("Obsolete"),
                           represent=lambda opt: \
                                     (opt and [T("Closed")] or [T("Operational")])[0],
                           default=False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_SEAPORT = T("Create Seaport")
        crud_strings[tablename] = Storage(
            label_create=T("Create Seaport"),
            title_display=T("Seaport Details"),
            title_list=T("Seaports"),
            title_update=T("Edit Seaport"),
            title_upload=T("Import Seaports"),
            label_list_button=T("List Seaports"),
            label_delete_button=T("Delete Seaport"),
            msg_record_created=T("Seaport added"),
            msg_record_modified=T("Seaport updated"),
            msg_record_deleted=T("Seaport deleted"),
            msg_list_empty=T("No Seaports currently registered"))

        configure(tablename,
                  onaccept = self.transport_seaport_onaccept,
                  super_entity = "org_site",
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_airport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("transport_airport", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_heliport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("transport_heliport", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_seaport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("transport_seaport", form.vars)

# =============================================================================
class S3VehicleModel(S3Model):
    """
        Vehicle Management Functionality

        http://eden.sahanafoundation.org/wiki/BluePrint/Vehicle
    
    """

    names = ["transport_vehicle",
             "transport_vehicle_gps",
             "transport_vehicle_id",
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
        tablename = "transport_vehicle"
        self.define_table(tablename,
                          Field("type",
                                label = T("Type"),
                                represent = lambda opt: \
                                            vehicle_type_opts.get(opt, opt),
                                requires = IS_EMPTY_OR(IS_IN_SET(vehicle_type_opts)),
                                ),
                          Field("name",
                                comment = T("e.g. License Plate"),
                                label = T("ID"),
                                ),
                          asset_id(),
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
                                                              "%s.id" % tablename,
                                                              represent,
                                                              )),
                                     )

        # ---------------------------------------------------------------------
        # GPS records
        # - designed to be pulled in automatically, not entered manually
        #
        # @ToDo: Move these to gis.py - nothing here is vehicle-specific
        #
        tablename = "transport_vehicle_gps"
        self.define_table(tablename,
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
        ADD_GPS = T("Create GPS data")
        crud_strings[tablename] = Storage(
            label_create = ADD_GPS,
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
        return dict(transport_vehicle_id = vehicle_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Return safe defaults for names in case the model is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(transport_vehicle_id = lambda **attr: dummy("vehicle_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_vehicle_gps_onaccept(form):
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
