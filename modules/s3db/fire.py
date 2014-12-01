# -*- coding: utf-8 -*-

""" Sahana Eden Fire Models

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

__all__ = ("S3FireModel",
           "S3FireStationModel",
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3FireModel(S3Model):
    """
        Fire Zones: Burn Perimeter, Burnt zone, Evacuation Zone, etc
    """

    names = ("fire_zone_type",
             "fire_zone",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # -----------------------------------------------------------
        # Fire Zone Types
        tablename = "fire_zone_type"
        define_table(tablename,
                     Field("name",
                           label=T("Name")),
                     # @ToDo: Currently unused - apply in layer_feature for now
                     Field("style", "text",
                           label=T("Style")),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_ZONE_TYPE = T("Create Zone Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_ZONE_TYPE,
            title_display = T("Zone Type Details"),
            title_list = T("Zone Types"),
            title_update = T("Edit Zone Type"),
            title_upload = T("Import Zone Types"),
            label_list_button = T("List Zone Types"),
            label_delete_button = T("Delete Zone Type"),
            msg_record_created = T("Zone Type added"),
            msg_record_modified = T("Zone Type updated"),
            msg_record_deleted = T("Zone Type deleted"),
            msg_list_empty = T("No Zone Types currently registered"))

        zone_type_represent = S3Represent(lookup=tablename)

        self.configure(tablename,
                       deduplicate = self.fire_zone_type_duplicate,
                       )

        # -----------------------------------------------------------
        # Fire Zones
        tablename = "fire_zone"
        define_table(tablename,
                     Field("name",
                           label=T("Name")),
                     Field("zone_type_id", db.fire_zone_type,
                           requires = IS_EMPTY_OR(
                                         IS_ONE_OF(db, "fire_zone_type.id",
                                                   zone_type_represent,
                                                   sort=True)),
                           represent = zone_type_represent,
                           comment = S3AddResourceLink(c="fire",
                                                       f="zone_type",
                                                       label=ADD_ZONE_TYPE,
                                                       tooltip=T("Select a Zone Type from the list or click 'Add Zone Type'")),
                           label=T("Type")),
                     self.gis_location_id(
                       widget = S3LocationSelector(catalog_layers = True,
                                                   points = False,
                                                   polygons = True,
                                                   )
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Zone"),
            title_display = T("Zone Details"),
            title_list = T("Zones"),
            title_update = T("Edit Zone"),
            title_upload = T("Import Zones"),
            label_list_button = T("List Zones"),
            label_delete_button = T("Delete Zone"),
            msg_record_created = T("Zone added"),
            msg_record_modified = T("Zone updated"),
            msg_record_deleted = T("Zone deleted"),
            msg_list_empty = T("No Zones currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def fire_zone_type_duplicate(item):
        """
            Zone Type record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        table = item.table
        query = (table.name == item.data.name)
        row = current.db(query).select(table.id,
                                       limitby=(0, 1)).first()
        if row:
            item.id = row.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3FireStationModel(S3Model):
    """
        A Model to manage Fire Stations:
        http://eden.sahanafoundation.org/wiki/Deployments/Bombeiros
    """

    names = ("fire_station",
             "fire_station_vehicle",
             "fire_water_source",
             "fire_hazard_point",
             "fire_staff_on_duty"
             )

    def model(self):

        T = current.T
        db = current.db
        request = current.request

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        human_resource_id = self.hrm_human_resource_id
        ireport_id = self.irs_ireport_id
        vehicle_id = self.vehicle_vehicle_id

        add_components = self.add_components
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # =====================================================================
        # Fire Station
        #
        fire_station_types = {
            1: T("Fire Station"),
            9: T("Unknown type of facility"),
        }

        tablename = "fire_station"
        define_table(tablename,
                     self.super_link("site_id", "org_site"),
                     Field("name", notnull=True, length=64,
                           label = T("Name")),
                     Field("code", unique=True, length=64,
                           label = T("Code")),
                     Field("facility_type", "integer",
                           label = T("Facility Type"),
                           requires = IS_EMPTY_OR(IS_IN_SET(fire_station_types)),
                           default = 1,
                           represent = lambda opt: \
                                       fire_station_types.get(opt, T("not specified"))
                           ),
                     organisation_id(),
                     location_id(),
                     Field("phone", label = T("Phone"),
                           requires = IS_EMPTY_OR(s3_phone_requires)),
                     Field("website", label=T("Website"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           represent = lambda url: s3_url_represent(url)),
                     Field("email", label = T("Email"),
                           requires = IS_EMPTY_OR(IS_EMAIL())
                           ),
                     Field("fax", label = T("Fax"),
                           requires = IS_EMPTY_OR(s3_phone_requires)),
                     Field("obsolete", "boolean",
                           label = T("Obsolete"),
                           represent = lambda opt: \
                                       (opt and [T("Obsolete")] or [current.messages["NONE"]])[0],
                           default = False,
                           readable = False,
                           writable = False),
                     s3_comments(),
                     *s3_meta_fields())

        self.configure("fire_station",
                       super_entity = "org_site",
                       )

        station_id = S3ReusableField("station_id", "reference %s" % tablename,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "fire_station.id",
                                                              self.fire_station_represent)),
                                     represent = self.fire_station_represent,
                                     label = T("Station"),
                                     ondelete = "CASCADE"
                                     )

        # CRUD strings
        ADD_FIRE_STATION = T("Add Fire Station")
        crud_strings[tablename] = Storage(
            label_create = ADD_FIRE_STATION,
            title_display = T("Fire Station Details"),
            title_list = T("Fire Stations"),
            title_update = T("Edit Station Details"),
            title_upload = T("Upload Fire Stations List"),
            title_map = T("Map of Fire Stations"),
            label_list_button = T("List Fire Stations"),
            label_delete_button = T("Delete Fire Station"),
            msg_record_created = T("Fire Station added"),
            msg_record_modified = T("Fire Station updated"),
            msg_record_deleted = T("Fire Station deleted"),
            msg_no_match = T("No Fire Stations could be found"),
            msg_list_empty = T("No Fire Stations currently registered"))

        # Components
        add_components(tablename,
                       vehicle_vehicle={"link": "fire_station_vehicle",
                                        "joinby": "station_id",
                                        "key": "vehicle_id",
                                        "actuate": "replace",
                                       },
                       fire_shift="station_id",
                       fire_shift_staff="station_id",
                      )

        # =====================================================================
        # Vehicles of Fire stations
        #
        tablename = "fire_station_vehicle"
        define_table(tablename,
                     station_id(),
                     vehicle_id(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_VEHICLE = T("Add Vehicle")
        crud_strings[tablename] = Storage(
            label_create = ADD_VEHICLE,
            title_display = T("Vehicle Details"),
            title_list = T("Vehicles"),
            title_update = T("Edit Vehicle Details"),
            title_upload = T("Upload Vehicles List"),
            label_list_button = T("List Vehicles"),
            label_delete_button = T("Delete Vehicle"),
            msg_record_created = T("Vehicle added"),
            msg_record_modified = T("Vehicle updated"),
            msg_record_deleted = T("Vehicle deleted"),
            msg_no_match = T("No Vehicles could be found"),
            msg_list_empty = T("No Vehicles currently registered"))

        self.set_method("fire", "station",
                        method="vehicle_report",
                        action=self.vehicle_report)

        # =====================================================================
        # Water Sources
        #
        tablename = "fire_water_source"
        define_table(tablename,
                     Field("name", "string"),
                     location_id(),
                     #Field("good_for_human_usage", "boolean"),
                     #Field("fresh", "boolean"),
                     #Field("Salt", "boolean"),
                     #Field("toponymy", "string"),
                     #Field("parish", "string"),
                     #Field("type", "string"),
                     #Field("owner", "string"),
                     #person_id(),
                     #organisation_id(),
                     #Field("shape", "string"),
                     #Field("diameter", "string"),
                     #Field("depth", "string"),
                     #Field("volume", "integer"),
                     #Field("lenght", "integer"),
                     #Field("height", "integer"),
                     #Field("usefull_volume", "integer"),
                     #Field("catchment", "integer"),
                     #Field("area", "integer"),
                     #Field("date", "date"),
                     #Field("access_type", "string"),
                     #Field("previews_usage", "boolean"),
                     #Field("car_access", "string"),
                     #Field("mid_truck_access", "string"),
                     #Field("truck_access", "string"),
                     #Field("distance_from_trees", "integer"),
                     #Field("distance_from_buildings", "integer"),
                     #Field("helicopter_access", "string"),
                     #Field("previews_usage_air", "boolean"),
                     #Field("car_movment_conditions", "string"),
                     #Field("midtruck_movment_conditions", "string"),
                     #Field("truck_movment_conditions", "string"),
                     #Field("powerline_distance", "integer"),
                     #Field("distance_other_risks", "integer"),
                     #Field("anti_seismic_construction", "boolean"),
                     #Field("isolated_from_air", "boolean"),
                     #Field("hermetic", "boolean"),
                     s3_comments(),
                     *s3_meta_fields())

        # =====================================================================
        # Hazards
        # - this is long-term hazards, not incidents
        #
        tablename = "fire_hazard_point"
        define_table(tablename,
                     location_id(),
                     Field("name", "string"),
                     # What are the Org & Person for? Contacts?
                     organisation_id(),
                     person_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # =====================================================================
        # Shifts
        #
        tablename = "fire_shift"
        define_table(tablename,
                     station_id(),
                     Field("name"),
                     s3_datetime("start_time",
                                 empty=False,
                                 default="now"
                                 ),
                     s3_datetime("end_time",
                                 empty=False,
                                 default="now"
                                 ),
                     *s3_meta_fields())

        shift_id = S3ReusableField("shift_id", "reference %s" % tablename,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "fire_shift.id",
                                                          self.fire_shift_represent)),
                                   represent = self.fire_shift_represent,
                                   label = T("Shift"),
                                   ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        tablename = "fire_shift_staff"
        define_table(tablename,
                     station_id(),
                     #shift_id(),
                     human_resource_id(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(# used by IRS
                    fire_staff_on_duty = self.fire_staff_on_duty,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def fire_station_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages["NONE"]

        db = current.db
        table = db.fire_station
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def fire_shift_represent(id, row=None):
        """
            Represent a Shift by Start and End times
        """

        if row:
            pass
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.fire_shift
            row = db(table.id == id).select(table.start_time,
                                            table.end_time,
                                            limitby=(0, 1)).first()
        try:
            return "%s - %s" % (row.start_time, row.end_time)
        except:
            current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def fire_staff_on_duty(station_id=None):
        """
            Return a query for hrm_human_resource filtering
            for entries which are linked to a current shift
        """

        db = current.db
        staff = db.hrm_human_resource
        roster = db.fire_shift_staff

        query = (staff.id == roster.human_resource_id) & \
                (roster.deleted != True)
        if station_id is not None:
            query &= (roster.station_id == station_id)
        return query

    # -------------------------------------------------------------------------
    @staticmethod
    def vehicle_report(r, **attr):
        """
            Custom method to provide a report on Vehicle Deployment Times
            - this is one of the main tools currently used to manage an Incident
        """

        rheader = attr.get("rheader", None)
        if rheader:
            rheader = rheader(r)

        station_id = r.id
        if station_id:

            s3db = current.s3db
            dtable = s3db.irs_ireport_vehicle
            vtable = s3db.vehicle_vehicle
            stable = s3db.fire_station_vehicle

            query = (stable.station_id == station_id) & \
                    (stable.vehicle_id == vtable.id) & \
                    (vtable.asset_id == dtable.asset_id)

            current.response.s3.crud_strings["irs_ireport_vehicle"] = Storage(
                title_report = "Vehicle Deployment Times"
            )

            req = r.factory(prefix="irs",
                            name="ireport_vehicle",
                            args=["report"],
                            vars=Storage(
                              rows = "asset_id",
                              cols = "ireport_id",
                              fact = "minutes",
                              aggregate = "sum")
                           )
            req.set_handler("report", S3Report())
            req.resource.add_filter(query)
            return req(rheader=rheader)

# END =========================================================================
