# -*- coding: utf-8 -*-

"""
    Fire Stations Management, Model

    @author: Dominic König <dominic[at]aidiq[dot]com>
"""

module = "fire"
if deployment_settings.has_module(module):

    s3mgr.model.add_component("vehicle_vehicle",
                              fire_station = Storage(link="fire_station_vehicle",
                                                     joinby="station_id",
                                                     key="vehicle_id",
                                                     actuate="replace"))

    s3mgr.model.add_component("fire_shift",
                              fire_station = "station_id")

    s3mgr.model.add_component("fire_shift_staff",
                              fire_station = "station_id")

    def fire_tables():

        person_id = s3db.pr_person_id
        location_id = s3db.gis_location_id
        organisation_id = s3db.org_organisation_id
        human_resource_id = s3db.hrm_human_resource_id
        ireport_id = s3db.ireport_id

        # =====================================================================
        # Fire Station
        #
        fire_station_types = {
            1: T("Fire Station"),
            9: T("Unknown type of facility"),
        }

        resourcename = "station"
        tablename = "fire_station"
        table = db.define_table(tablename,
                                super_link("site_id", "org_site"),
                                Field("name", notnull=True,
                                      length=64,
                                      label = T("Name")),
                                Field("code", unique=True,
                                      length=64,
                                      label = T("Code")),
                                Field("facility_type", "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(fire_station_types)),
                                default = 1,
                                label = T("Facility Type"),
                                represent = lambda opt: fire_station_types.get(opt, T("not specified"))),
                                organisation_id(),
                                location_id(),
                                Field("phone", label = T("Phone"),
                                      requires = IS_NULL_OR(s3_phone_requires)),
                                Field("website", label=T("Website"),
                                      #requires = IS_NULL_OR(IS_URL()),
                                      represent = lambda url: s3_url_represent(url)),
                                Field("email", label = T("Email"),
                                      #requires = IS_NULL_OR(IS_EMAIL())
                                      ),
                                Field("fax", label = T("Fax"),
                                      requires = IS_NULL_OR(s3_phone_requires)),
                                s3_comments(),
                                *s3_meta_fields())

        s3mgr.configure("fire_station",
                        super_entity="org_site")

        station_id = S3ReusableField("station_id", table,
                                      requires = IS_NULL_OR(IS_ONE_OF(db, "fire_station.id", "%(name)s")),
                                      represent = lambda id: (id and [db.fire_station[id].name] or [NONE])[0],
                                      label = T("Station"),
                                      ondelete = "CASCADE")

        # CRUD strings
        ADD_FIRE_STATION = T("Add Fire Station")
        LIST_FIRE_STATIONS = T("List of Fire Stations")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_FIRE_STATION,
            title_display = T("Fire Station Details"),
            title_list = LIST_FIRE_STATIONS,
            title_update = T("Edit Station Details"),
            title_search = T("Search for Fire Station"),
            title_upload = T("Upload Fire Stations List"),
            subtitle_create = T("Add New Fire Station"),
            subtitle_list = T("Fire Stations"),
            label_list_button = LIST_FIRE_STATIONS,
            label_create_button = ADD_FIRE_STATION,
            label_delete_button = T("Delete Fire Station"),
            msg_record_created = T("Fire Station added"),
            msg_record_modified = T("Fire Station updated"),
            msg_record_deleted = T("Fire Station deleted"),
            msg_no_match = T("No Fire Stations could be found"),
            msg_list_empty = T("No Fire Stations currently registered"))

        # =====================================================================
        # Vehicles of Fire stations
        #
        s3mgr.load("vehicle_vehicle")
        vehicle_id = response.s3.vehicle_id

        tablename = "fire_station_vehicle"
        table = db.define_table(tablename,
                                station_id(),
                                vehicle_id())

        # CRUD strings
        ADD_VEHICLE = T("Add Vehicle")
        LIST_VEHICLES = T("List of Vehicles")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_VEHICLE,
            title_display = T("Vehicle Details"),
            title_list = LIST_VEHICLES,
            title_update = T("Edit Vehicle Details"),
            title_search = T("Search for Vehicles"),
            title_upload = T("Upload Vehicles List"),
            subtitle_create = T("Add New Vehicle"),
            subtitle_list = T("Vehicles"),
            label_list_button = LIST_VEHICLES,
            label_create_button = ADD_VEHICLE,
            label_delete_button = T("Delete Vehicle"),
            msg_record_created = T("Vehicle added"),
            msg_record_modified = T("Vehicle updated"),
            msg_record_deleted = T("Vehicle deleted"),
            msg_no_match = T("No Vehicles could be found"),
            msg_list_empty = T("No Vehicles currently registered"))

        class irs_ireport_vehicle_virtual_fields:

            extra_fields = ["datetime"]

            def minutes(self):
                try:
                    delta = request.utcnow - self.irs_ireport_vehicle.datetime
                    print delta.seconds
                except:
                    return 0
                return int(delta.seconds / 60)

        s3mgr.load("irs_ireport_vehicle")
        db.irs_ireport_vehicle.virtualfields.append(irs_ireport_vehicle_virtual_fields())

        def vehicle_report(r, **attr):

            rheader = attr.get("rheader", None)
            if rheader:
                rheader = rheader(r)

            station_id = r.id
            if station_id:

                dtable = db.irs_ireport_vehicle
                vtable = db.vehicle_vehicle
                stable = db.fire_station_vehicle

                query = (stable.station_id == station_id) & \
                        (stable.vehicle_id == vtable.id) & \
                        (vtable.asset_id == dtable.asset_id)

                s3.crud_strings["irs_ireport_vehicle"] = Storage(
                    title_report = "Vehicles Deployment Times"
                )

                req = s3mgr.parse_request("irs", "ireport_vehicle",
                                          args=["report"],
                                          vars=Storage(
                                            rows = "asset_id",
                                            cols = "ireport_id",
                                            fact = "minutes",
                                            aggregate = "sum"
                                          ))
                req.set_handler("report", s3base.S3Cube())
                req.resource.add_filter(query)
                return req(rheader=rheader)

        s3mgr.model.set_method("fire", "station",
                               method="vehicle_report",
                               action=vehicle_report)

        # =====================================================================
        # Water Sources
        #
        tablename = "fire_water_source"
        table = db.define_table(tablename,
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
        # Water Sources
        #
        tablename = "fire_hazard_point"
        table = db.define_table(tablename,
                                location_id(),
                                Field("name", "string"),
                                organisation_id(),
                                person_id(),
                                s3_comments(),
                                *s3_meta_fields())

        # =====================================================================
        # Shifts
        #
        s3_utc_represent = lambda dt: s3_datetime_represent(dt, utc=True)

        tablename = "fire_shift"
        table = db.define_table(tablename,
                                station_id(),
                                Field("name"),
                                Field("start_time", "datetime",
                                      requires = IS_UTC_DATETIME_IN_RANGE(),
                                      widget = S3DateTimeWidget(),
                                      default = request.utcnow,
                                      represent = s3_utc_represent),
                                Field("end_time","datetime",
                                      requires = IS_UTC_DATETIME_IN_RANGE(),
                                      widget = S3DateTimeWidget(),
                                      default = request.utcnow,
                                      represent = s3_utc_represent),
                                *s3_meta_fields())

        def fire_shift_represent(shift):

            shift_table = db.fire_shift
            if not isinstance(shift, Row):
                shift = db(shift_table.id == shift).select(limitby=(0, 1)).first()
            return "%s - %s" % (shift.start_time, shift.end_time)

        shift_id = S3ReusableField("shift_id", table,
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "fire_shift.id",
                                                                   fire_shift_represent)),
                                   represent = fire_shift_represent,
                                   label = T("Shift"),
                                   ondelete = "CASCADE")

        tablename = "fire_shift_staff"
        table = db.define_table(tablename,
                                station_id(),
                                #shift_id(),
                                human_resource_id(),
                                *s3_meta_fields())

        def fire_staff_on_duty(station_id=None):
            """
                Return a query for hrm_human_resource filtering
                for entries which are linked to a current shift
            """

            staff = db.hrm_human_resource
            roster = db.fire_shift_staff

            query = (staff.id == roster.human_resource_id) & \
                    (roster.deleted != True)
            if station_id is not None:
                query &= (roster.station_id == station_id)
            return query

        # Return variables to the global scope
        return dict(
                station_id = station_id,
                fire_staff_on_duty = fire_staff_on_duty
               )

    # =========================================================================
    # Table loader configuration
    #
    s3mgr.model.loader(fire_tables,
                       "fire_station",
                       "fire_station_vehicle",
                       "fire_water_source",
                       "fire_hazard_point")

else:
    response.s3.fire_staff_on_duty = lambda station_id: (True)
    def station_id(**arguments):
        return Field("station_id", "integer", readable=False, writable=False)
    response.s3.station_id = station_id

# END =========================================================================
