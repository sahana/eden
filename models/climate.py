# -*- coding: utf-8 -*-

__doc__ = """Climate data portal models

Climate data is stored in dynamically created tables.
These tables can be added from the command line script add_table.py
in modules.ClimateDataPortal.
The table definitions are stored in climate_sample_table_spec.

A data is an observed value over a time quantum at a given place.

e.g. observed temperature in Kathmandu between Feb 2006 - April 2007

Places are currently points, i.e. lat/lon coordinates.
Places may be stations.
Places may have elevation or other optional information.

"""


module = "climate"

if deployment_settings.has_module("climate"):
    climate_first_run_sql = []
    def climate_first_run():
        for sql in climate_first_run_sql:
            db.executesql(sql)
        db.commit()

    def climate_define_table(name, fields, attrs = None):
        if attrs is None:
            attrs = {}
        return db.define_table(
            "climate_"+name,
            *fields,
            **attrs
        )

    # @ToDo: would be great if we had a table that could represent
    # places. gis_location doesn't fit the bill as there are so many
    # other fields that climate doesn't use.
    # elevation is not included as it would just mean a performance hit
    # when we are generating 2D maps without elevation info.
    climate_place = climate_define_table(
        "place",
        (
            # @ToDo: change into GIS point
            Field(
                "longitude",
                "double",
                notnull=True,
                required=True,
            ),
            Field(
                "latitude",
                "double",
                notnull=True,
                required=True,
            )
        )
    )

    def place_attribute_table(
        attribute_table_name,
        fields
    ):
        return climate_define_table(
            "place_"+attribute_table_name,
            fields
        )

    # elevation may not be useful for future projects
    # e.g. where not available, or sea-based stations
    # also, elevation may be supplied for gridded data
    climate_elevation = place_attribute_table(
        "elevation",
        (
            Field(
                "elevation_metres",
                "double",
                notnull=True,
                required=True,
            ),
        )
    )

    # not all places are stations with elevations
    # as in the case of "gridded" data
    # a station can only be in one place
    climate_station_name = place_attribute_table(
        "station_name",
        (
            Field(
                "name",
                "string",
                notnull=True,
                required=True,
            ),
        )
    )

    # station id may not be useful or even meaningful
    # e.g. gridded data has no stations.
    # this is passive data so ok to store separately
    climate_station_id = place_attribute_table(
        "station_id",
        (
            Field(
                "station_id",
                "integer",
                notnull=True,
                required=True,
            ),
        )
    )


    climate_region = place_attribute_table(
        "region",
        (
            Field(
                "region_id",
                "integer",
                notnull=True,
                required=True,
            ),
        )
    )

    # coefficient of variance is meaningless for C but Ok for Kelvin
    # internally all scales must be ratio scales if coefficient of variations is to
    # be used
    # rainfall (mm), temp (K) are ok
    # output units

    climate_sample_table_spec = climate_define_table(
        "sample_table_spec",
        (
            Field(
                "name",
                "string",
                notnull=True,
                required=True,
            ),
            Field(
                "sample_type_code",
                "string",
                length = 1,
                notnull = True,
                # web2py requires a default value for not null fields
                default = "",
                required = True
            ),
            Field(
                "field_type",
                "string",
                notnull=True,
                required=True,
            ),
            Field(
                "units",
                "string",
                notnull=True,
                required=True,
            ),
            Field(
                "date_mapping",
                "string",
                default="",
                notnull=True,
                required=True
            )
        ),
    )
    climate_first_run_sql.append(
        "ALTER TABLE climate_sample_table_spec"
        "    ADD CONSTRAINT climate_sample_table_name_sample_type_unique"
        "    UNIQUE (name, sample_type_code);"
    )


    climate_monthly_aggregation_table_spec = climate_define_table(
        "monthly_aggregation",
        (
            Field(
                "sample_table_id",
                climate_sample_table_spec,
                notnull = True,
                required = True
            ),
            Field(
                # this maps to the name of a python class
                # thats deals with the monthly aggregated data.
                "aggregation",
                "string",
                notnull=True,
                required=True,
            )
        )
    )
