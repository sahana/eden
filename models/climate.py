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

    def station_represent(id):
        row_id = db(climate_station_id.station_id == id).select(
            climate_station_id.station_id,
            limitby=(0,1)
        ).first()
        row_name = db(climate_station_name.id == id).select(
            climate_station_name.name,
            limitby=(0,1)
        ).first()
                                                            
        if row_id and row_id.station_id:
            represent = " (%s)" % row_id.station_id
        else:
            represent = ""
        if row_name and row_name.name:
            represent = "%s%s" % (row_name.name, represent)
        
        return represent or NONE
            
                                                    
    station_id = S3ReusableField(
        "station_id", 
        climate_station_name, 
        sortby="name",
        requires = IS_ONE_OF(
            db,
            "climate_place_station_name.id",
            station_represent,
            orderby="climate_place_station_name.name",
            sort=True
        ),
        represent = station_represent,
        label = "Station",
        ondelete = "RESTRICT"
    )

    # coefficient of variance is meaningless for degrees C but Ok for Kelvin
    # internally all scales must be ratio scales if coefficient 
    # of variations is to be allowed, (which it is)
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
            ),
            Field(
                "grid_size",
                "double",
                default = 0,
                notnull = True,
                required = True
            )
        ),
    )
    
    def sample_table_spec_represent(id):
        table = db.climate_sample_table_spec
        row = db(table.id == id).select(
            table.name,
            table.sample_type_code,
            limitby=(0, 1)
        ).first()
        if row:
            return "%s %s" % (
                ClimateDataPortal.sample_table_types_by_code[row.sample_type_code].__name__, 
                row.name
            )
        else:
            return NONE
    
    parameter_id = S3ReusableField(
        "parameter_id", 
        db.climate_sample_table_spec, 
        sortby="name",
        requires = IS_ONE_OF(
            db,
            "climate_sample_table_spec.id",
            sample_table_spec_represent,
            sort=True
        ),
        represent = sample_table_spec_represent,
        label = "Parameter",
#        script = SCRIPT(
#"""
#S3FilterFieldChange({
#    'FilterField':    'sample_type_code',
#    'Field':        'parameter_id',
#    'FieldResource':'sample_table_spec',
#    'FieldPrefix':    'climate',
#});"""),
        ondelete = "RESTRICT"
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
                # that deals with the monthly aggregated data.
                "aggregation",
                "string",
                notnull=True,
                required=True,
            )
        )
    )

    # =====================================================================
    # Station Parameters
    #
    resourcename = "station_parameter"
    tablename = "climate_station_parameter"
    table = db.define_table(
        tablename,
        station_id(),
        parameter_id(
            requires = IS_ONE_OF(
                db,
                "climate_sample_table_spec.id",
                sample_table_spec_represent,
                sort=True
            ),
            script = None
        ),
    )
    
    # Add virtual fields for range: from - to
                            
                            

    # CRUD strings
    ADD_STATION_PARAMETER = T("Add Station Parameter")
    LIST_STATION_PARAMETER = T("List Station Parameters")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_STATION_PARAMETER,
        title_display = T("Station Parameter Details"),
        title_list = LIST_STATION_PARAMETER,
        title_update = T("Edit Station Parameter"),
        title_search = T("Search Station Parameters"),
        subtitle_create = ADD_STATION_PARAMETER,
        subtitle_list = T("Station Parameters"),
        label_list_button = LIST_STATION_PARAMETER,
        label_create_button = ADD_STATION_PARAMETER,
        label_delete_button = T("Remove Station Parameter"),
        msg_record_created = T("Station Parameter Added"),
        msg_record_modified = T("Station Parameter updated"),
        msg_record_deleted = T("Station Parameter removed"),
        msg_list_empty = T("No Station Parameters currently registered")
    )
    

    # Virtual Field for pack_quantity
    class station_parameters_virtualfields(dict, object):
        def range_from(self):
            query = (
                "SELECT MIN(time_period) "
                "from climate_sample_table_%(parameter_id)i "
                "WHERE place_id = %(station_id)i;"
            ) % dict(
                parameter_id = self.climate_station_parameter.parameter_id,
                station_id = self.climate_station_parameter.station_id,
            )
            date  = db.executesql(query)[0][0]
            if date is not None:
                year,month = ClimateDataPortal.month_number_to_year_month(date)
                return "%s-%s" % (month, year)
            else:
                return NONE
            
            
        
        #"Now station_id=%s parameter_id=%s" % (
        #    self.climate_station_parameter.station_id,
        #    self.climate_station_parameter.parameter_id)
        def range_to(self):
            query = (
                "SELECT MAX(time_period) "
                "from climate_sample_table_%(parameter_id)i "
                "WHERE place_id = %(station_id)i;"
            ) % dict(
                parameter_id = self.climate_station_parameter.parameter_id,
                station_id = self.climate_station_parameter.station_id,
            )
            date  = db.executesql(query)[0][0]
            if date is not None:
                year,month = ClimateDataPortal.month_number_to_year_month(date)
                return "%s-%s" % (month, year)
            else:
                return NONE
    
    table.virtualfields.append(station_parameters_virtualfields())
    
    s3mgr.configure(
        tablename,
        insertable = False,
        list_fields = [
            "station_id",
            "parameter_id",
            (T("Range From"), "range_from"),
            (T("Range To"), "range_to"),
        ]
    )
    
    # Load all stations and parameters
    if not db(table.id > 0).count():
        station_rows = db(
            climate_station_name.id > 0
        ).select(
            climate_station_name.id
        )
        for station_row in station_rows:
            parameter_rows = db(
                climate_sample_table_spec.sample_type_code == "O"
            ).select(climate_sample_table_spec.id)
            for parameter_row in parameter_rows:
                table.insert(
                    station_id = station_row.id,
                    parameter_id = parameter_row.id
                )
            
    
    # =====================================================================
    # Purchase Data
    #
    nationality_opts = {1:"Nepali", 2:"Foreigner"}
    
    resourcename = "purchase"
    tablename = "climate_purchase"
    table = db.define_table(
        tablename,
        #user_id(),
        #Field("sample_type_code",
        #      "string",
        #      requires = IS_IN_SET(sample_type_code_opts),
        #      represent = lambda code: ClimateDataPortal.sample_table_types_by_code[code]
        #),
        parameter_id(
            requires = IS_ONE_OF(
                db,
                "climate_sample_table_spec.id",
                sample_table_spec_represent,
                filterby = "sample_type_code",
                filter_opts = ["O"],
                sort=True
            ),
        ),
        station_id(),
        Field("date_from",
              "date",
              requires = IS_DATE(format = s3_date_format),
              widget = S3DateWidget(),
              default = request.utcnow,
              required = True
        ),
        Field("date_to",
              "date",
              requires = IS_DATE(format = s3_date_format),
              widget = S3DateWidget(),
              default = request.utcnow,
              required = True
        ),
        Field("nationality",
              "integer",
              label = T("Nationality"),
              requires = IS_IN_SET(nationality_opts),
              represent = lambda id: nationality_opts.get(id, NONE),
              required = True
        ),
        Field("purpose",
              "text"
        ),
        Field("price", 
              "string",
        ),
        Field("paid",
              "boolean",
              represent = lambda paid: paid and "Yes" or "No",
        ),
        *s3_meta_fields()
    )
    
    if not s3_has_role(ADMIN):
        db.climate_purchase.paid.writeable = False
    
    # CRUD strings
    ADD_CLIMATE_PURCHASE = T("Purchase New Data")
    LIST_CLIMATE_PURCHASE = T("All Purchased Data")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_CLIMATE_PURCHASE,
        title_display = T("Purchased Data Details"),
        title_list = LIST_CLIMATE_PURCHASE,
        title_update = T("Edit Purchased Data Details"),
        title_search = T("Search Purchased Data"),
        subtitle_create = ADD_CLIMATE_PURCHASE,
        subtitle_list = T("Purchased Data"),
        label_list_button = LIST_CLIMATE_PURCHASE,
        label_create_button = ADD_CLIMATE_PURCHASE,
        label_delete_button = T("Remove Purchased Data"),
        msg_record_created = T("Data Purchase In Process"),
        msg_record_modified = T("Data Purchase Processed"),
        msg_record_deleted = T("Data Purchase removed"),
        msg_list_empty = T("No Data Purchased"))
    
    def climate_purchase_onaccept(form):
        # Calculate Price
        id = form.vars.id
        
        parameter_table = db(
            db.climate_sample_table_spec.id == form.vars.parameter_id
        ).select(
            db.climate_sample_table_spec.id,
            db.climate_sample_table_spec.date_mapping
        ).first()
        parameter_table_id = parameter_table.id
        date_mapping_name = parameter_table.date_mapping
        period = date_mapping_name
        
        date_from = form.vars.date_from
        date_to = form.vars.date_to
        nationality = int(form.vars.nationality)
        if nationality == 1:
            period_dict = dict(
                daily = 60,
                monthly = 40
                          # 3:15,
                          # 4:5
            )
            currency = "NRs"
        else:
            period_dict = dict(
                daily = 2,
                monthly = 1.5
            #               3:0.5,
            #               4:0.25}
            )
            currency = "US$"
        
        date_mapping = getattr(ClimateDataPortal, date_mapping_name)
        
        start_date_number = date_mapping.date_to_time_period(date_from)
        end_date_number = date_mapping.date_to_time_period(date_to)
        
        place_id = int(form.vars.station_id)
        
        duration = db.executesql(
            "SELECT COUNT(*) "
            "FROM climate_sample_table_%(parameter_table_id)i "
            "WHERE time_period >= %(start_date_number)i "
            "AND place_id = %(place_id)i "
            "AND time_period <= %(end_date_number)i;" % locals()
        )[0][0]
        price = "%.2f" % (duration * period_dict[period] / (dict(daily=365.25, monthly=12)[period]))
        db.climate_purchase[id] = {"price": "%s %s" % (price, currency)}

    s3mgr.configure(
        tablename,
        onaccept = climate_purchase_onaccept,
        create_next = aURL( args = ["[id]","read"]),
        #listadd = listadd
    )
    
    # =====================================================================
    # Saved Queries
    #
    resourcename = "save_query"
    tablename = "climate_save_query"
    table = db.define_table(
        tablename,
        #user_id(),
        Field("description", "string"),
        Field("query_definition", "text"),
    )

    # CRUD strings
    ADD_SAVE_QUERY = T("Save Query")
    LIST_SAVE_QUERY = T("Saved Queries")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SAVE_QUERY,
        title_display = T("Saved Query Details"),
        title_list = LIST_SAVE_QUERY,
        title_update = T("Edit Saved Query"),
        title_search = T("Search Saved Queries"),
        subtitle_create = ADD_SAVE_QUERY,
        subtitle_list = T("Saved Queries"),
        label_list_button = LIST_SAVE_QUERY,
        label_create_button = ADD_SAVE_QUERY,
        label_delete_button = T("Remove Saved Query"),
        msg_record_created = T("Query Saved"),
        msg_record_modified = T("Saved Query updated"),
        msg_record_deleted = T("Saved Query removed"),
        msg_list_empty = T("No Queries Saved"))
    
    s3mgr.configure(
        tablename,
        listadd = False
    )
    
    # =====================================================================
