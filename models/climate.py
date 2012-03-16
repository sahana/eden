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
        row_id = db(climate_station_id.id == id).select(
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
        climate_sample_table_spec = db.climate_sample_table_spec
        row = db(climate_sample_table_spec.id == id).select(
            climate_sample_table_spec.name,
            climate_sample_table_spec.sample_type_code,
            limitby=(0, 1)
        ).first()
        if row:
            return "%s %s" % (
                ClimateDataPortal.sample_table_types_by_code[row.sample_type_code].__name__, 
                row.name
            )
        else:
            return NONE
    
    def parameter_id_represent(id):
        climate_sample_table_spec = db.climate_sample_table_spec
        row = db(climate_sample_table_spec.id == id.parameter_id).select(
            climate_sample_table_spec.name,
            climate_sample_table_spec.sample_type_code,
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
    climate_station_parameter_table_name = "climate_station_parameter"
    climate_station_parameter_table = db.define_table(
        climate_station_parameter_table_name,
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
                            
    def CRUD_strings(
        table_name,
        entity,
        entities = None,
        CREATE = None,
        created = None,
        LIST = None
    ):
        if entities is None:
            entities = entity+"s"
        if CREATE is None:
            CREATE = T("Add new "+entity)
        if created is None:
            created = entity+" added"
        if LIST is None:
            LIST = T("List "+entities)
        s3.crud_strings[table_name] = Storage(
            title_create = CREATE,
            title_display = T(entity+" Details"),
            title_list = LIST,
            title_update = T("Edit "+entity),
            title_search = T("Search "+entities),
            subtitle_create = CREATE,
            subtitle_list = T(entities),
            label_list_button = LIST,
            label_create_button = CREATE,
            label_delete_button = T("Remove "+entity),
            msg_record_created = T(created),
            msg_record_modified = T(entity+" updated"),
            msg_record_deleted = T(entity+" removed"),
            msg_list_empty = T("No "+entities))
                           
    CRUD_strings(
        climate_station_parameter_table_name,
        entity = "Station Parameter"
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
    
    climate_station_parameter_table.virtualfields.append(
        station_parameters_virtualfields()
    )
    
    s3mgr.configure(
        climate_station_parameter_table_name,
        insertable = False,
        list_fields = [
            "station_id",
            "parameter_id",
            (T("Range From"), "range_from"),
            (T("Range To"), "range_to"),
        ]
    )
    
    # Load all stations and parameters
    if not db(climate_station_parameter_table.id > 0).count():
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
                climate_station_parameter_table.insert(
                    station_id = station_row.id,
                    parameter_id = parameter_row.id
                )
            
    
    # =====================================================================
    # Purchase Data
    #
    nationality_opts = {
        1:"Nepali Student",
        2:"Others"
    }
    
    climate_prices_table_name = "climate_prices"
    climate_prices_table = db.define_table(
        climate_prices_table_name,
        Field(
            "category",
            "integer",
            label = T("Category"),
            requires = IS_IN_SET(nationality_opts),
            represent = lambda id: nationality_opts.get(id, NONE),
            notnull = True,
            required = True
        ),
        parameter_id(
            requires = IS_ONE_OF(
                db,
                "climate_sample_table_spec.id",
                sample_table_spec_represent,
                filterby = "sample_type_code",
                filter_opts = ["O"],
                sort=True
            ),
            notnull = True,
            required = True,
            represent = sample_table_spec_represent
        ),
        Field(
            "nrs_per_datum",
            "double",
            label = T("NRs per datum"),
            notnull = True,
            required = True
        )
    )
    
    climate_first_run_sql.append(
    #db.executesql(
        "ALTER TABLE climate_prices"
        "    ADD CONSTRAINT climate_price_unique"
        "    UNIQUE (category, parameter_id);"
    )

    def climate_price_create_onvalidation(form):
        if db(
            (db.climate_prices.category == form.request_vars["category"]) &
            (db.climate_prices.parameter_id == form.request_vars["parameter_id"])
        ).select(
            db.climate_prices.id
        ).first() is not None:
            form.errors["nrs_per_datum"] = [
                "There is a conflicting price for the above category and parameter."
            ]
            return False
        else:
            return True
 
    s3mgr.configure(
        climate_prices_table_name,
        create_onvalidation = climate_price_create_onvalidation,
        list_fields=[
            "category",
            "parameter_id",
            "nrs_per_datum"
        ]
    )
   
    CRUD_strings(
        climate_prices_table_name,
        entity = "Dataset Price"
    )    
        

    climate_purchase_table_name = "climate_purchase"
    climate_purchase_table = db.define_table(
        climate_purchase_table_name,
        #user_id(),
        #Field("sample_type_code",
        #      "string",
        #      requires = IS_IN_SET(sample_type_code_opts),
        #      represent = lambda code: ClimateDataPortal.sample_table_types_by_code[code]
        #),        
        Field(
            "parameter_id", 
            "integer", 
            requires = IS_ONE_OF(
                db,
                "climate_prices.parameter_id",
                parameter_id_represent,
            ),
            represent = sample_table_spec_represent,
            label = "Parameter",
            ondelete = "RESTRICT"
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
              label = T("Category"),
              requires = IS_IN_SET(nationality_opts),
              represent = lambda id: nationality_opts.get(id, NONE),
              required = True
        ),
        Field(
            "notes",
            "text",
            label = T("Receipt number / Student ID / other notes")
        ),
        Field(
            "price", 
            "string",
        ),
        Field(
            "paid",
            "boolean",
            represent = lambda paid: paid and "Yes" or "No",
        ),
        Field(
            "i_agree_to_the_terms_and_conditions",
            "boolean",
            required = True,
            represent = lambda agrees: agrees and "Yes" or "No",
            comment = DIV(
                _class="stickytip",
                _title="%s|%s" % (
                    T("Important"),
                    T(
                        "Check this box when you have read, "
                        "understand and agree to the "
                        "<a href='terms' target='_blank'>"
                            "terms and conditions"
                        "</a>."
                    )
                )
            )
        ),
        *s3_meta_fields()
    )
    climate_purchase_table.owned_by_user.label = T("User")
    
    if not s3_has_role(ADMIN):
        db.climate_purchase.paid.writeable = False
    
    CRUD_strings(
        climate_purchase_table_name,
        entity = "Purchased Data Detail",
        CREATE = T("Purchase New Data"),
        created = T("Data Purchase In Process"),
        LIST = T("All Purchased Data")
    )    

    def climate_purchase_onaccept(form):
        # Calculate Price
        id = form.vars.id
        
        purchase = db(
            db.climate_purchase.id == id
        ).select(
            db.climate_purchase.paid
        ).first()
        
        if (purchase and purchase.paid == True):
            pass
        else:
            parameter_id = form.vars.parameter_id
            parameter_table = db(
                db.climate_sample_table_spec.id == parameter_id
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
            price_row = db(
                (db.climate_prices.category == nationality) &
                (db.climate_prices.parameter_id == parameter_id)
            ).select(
                db.climate_prices.nrs_per_datum
            ).first()

            if price_row is None:
                form.errors["price"] = ["There is no price set for this data"]
            else:
                price = price_row.nrs_per_datum
                
                currency = {
                    1: "%.2f NRs",
                    2: "US$ %.2f"
                }[nationality]
                
                date_mapping = getattr(ClimateDataPortal, date_mapping_name)
                
                start_date_number = date_mapping.date_to_time_period(date_from)
                end_date_number = date_mapping.date_to_time_period(date_to)
                
                place_id = int(form.vars.station_id)
                
                datum_count = db.executesql(
                    "SELECT COUNT(*) "
                    "FROM climate_sample_table_%(parameter_table_id)i "
                    "WHERE place_id = %(place_id)i "
                    "AND time_period >= %(start_date_number)i "
                    "AND time_period <= %(end_date_number)i;" % locals()
                )[0][0]
                db.climate_purchase[id] = {"price": currency % (datum_count * price)}

    s3mgr.configure(
        climate_purchase_table_name,
        onaccept = climate_purchase_onaccept,
        create_next = aURL( args = ["[id]","read"]),
        list_fields=[
            "owned_by_user",
            "parameter_id",
            "station_id",
            "date_from",
            "date_to",
            "nationality",
            #"purpose",
            "price", 
            "paid",
            "i_agree_to_terms_and_conditions"
        ]
    )
    
    # =====================================================================
    # Saved Queries
    #
    climate_save_query_table_name = "climate_save_query"
    climate_save_query_table = db.define_table(
        climate_save_query_table_name,
        #user_id(),
        Field("description", "string"),
        Field("query_definition", "text"),
    )

    CRUD_strings(
        climate_save_query_table_name,
        entity = "Saved Query",
        CREATE = T("Save Query"),
        created = "Query Saved",
        LIST = T("Saved Queries")
    )
    
    s3mgr.configure(
        climate_save_query_table_name,
        listadd = False
    )
    
    # =====================================================================
