# -*- coding: utf-8 -*-


from gluon.dal import Expression

from Cache import *
import gluon.contrib.simplejson as JSON
from . import SampleTable, month_number_to_year_month, units_in_out, start_month_0_indexed
from DSL.Units import MeaninglessUnitsException
from DSL import aggregations

class MapPlugin(object):
    def __init__(
        self,
        env,
        year_min,
        year_max,
        place_table,
    ):
        try:
            import rpy2
            import rpy2.robjects as robjects
        except ImportError:
            import logging
            logging.getLogger().error(
        """R is required by the climate data portal to generate charts

        To install R: refer to:
        http://cran.r-project.org/doc/manuals/R-admin.html


        rpy2 is required to interact with python.

        To install rpy2, refer to:
        http://rpy.sourceforge.net/rpy2/doc-dev/html/overview.html
        """)
            raise

        self.env = env
        self.year_min = year_min 
        self.year_max = year_max
        self.place_table = place_table
        self.robjects = robjects
        R = self.R = robjects.r
        env.DSL.init_R_interpreter(R, env.deployment_settings.database)

    def extend_gis_map(self, add_javascript, add_configuration):
        add_javascript("scripts/S3/s3.gis.climate.js")
        env = self.env
        SCRIPT = env.SCRIPT
        T = env.T
        import json
        application_name = env.request.application
        config_dict = dict(
            year_min = self.year_min,
            year_max = self.year_max,
            overlay_data_URL = "/%s/climate/climate_overlay_data" % application_name,
            chart_URL = "/%s/climate/climate_chart" % application_name,
            places_URL = "/%s/climate/places" % application_name,
            chart_popup_URL = "/%s/climate/chart_popup.html" % application_name,
            buy_data_popup_URL = "/%s/climate/buy_data.html" % application_name,
            data_URL = "/%s/climate/data" % application_name,
            data_type_label = str(T("Data Type")),
            projected_option_type_label = str(
                T("Projection Type")
            ),
            aggregation_names = [
                Aggregation.__name__ for Aggregation in aggregations
            ]
        )
        SampleTable.add_to_client_config_dict(config_dict)
        add_configuration(
            SCRIPT(
                "\n".join((
                    "registerPlugin(",
                    "    new ClimateDataMapPlugin("+
                            json.dumps(
                                config_dict,
                                indent = 4
                            )+
                        ")",
                    ")",
                ))
            )
        )

    def get_places(self, place_ids):
        db = env.db
        place_table = self.place_table

        place_data = db(place_table).select(
            place_table.id,
            place_table.longitude,
            place_table.latitude,
        )
            
    def get_overlay_data(
        self,
        query_expression,
    ):
        env = self.env
        DSL = env.DSL
        expression = DSL.parse(query_expression)
        understood_expression_string = str(expression)        
        units = DSL.units(expression)
        if units is None:
            analysis_strings = []
            def analysis_out(*things):
                analysis_strings.append("".join(map(str, things)))
            DSL.analysis(expression, analysis_out)
            raise MeaninglessUnitsException(
                "\n".join(analysis_strings)
            )                
        
        def generate_map_overlay_data(file_path):
            R = self.R
            code = DSL.R_Code_for_values(expression, "place_id")
            values_by_place_data_frame = R(code)()
            # R willfully removes empty data frame columns 
            # which is ridiculous behaviour
            if isinstance(values_by_place_data_frame, self.robjects.vectors.StrVector):
                raise Exception(str(values_by_place_data_frame))
            elif values_by_place_data_frame.ncol == 0:
                keys = []
                values = []
            else:
                keys = values_by_place_data_frame.rx2("key")
                values = values_by_place_data_frame.rx2("value")
            
            try:
                overlay_data_file = open(file_path, "w")
                write = overlay_data_file.write
                write('{')
                # sent back for acknowledgement:
                write('"understood_expression":"%s",' % understood_expression_string.replace('"','\\"'))
                write('"units":"%s",' % units)
                
                write('"keys":[')
                write(",".join(map(str, keys)))
                write('],')
                
                from math import log10, floor
                def round_to_4_sd(x):
                    if x == 0:
                        return 0.0
                    else:
                        return round(x, -int(floor(log10(abs(x)))-3))
                    
                write('"values":[')
                write(",".
                    join(
                        map(
                            lambda value: str(round_to_4_sd(value)),
                            values
                        )
                    )
                )
                write(']')
                
                write('}')
            except:
                overlay_data_file.close()
                os.unlink(file_path)
                raise
            finally:
                overlay_data_file.close()
            
        import hashlib
        return get_cached_or_generated_file(
            hashlib.md5(understood_expression_string).hexdigest()+".json",
            generate_map_overlay_data
        )
    
    def render_plots(
        self,
        specs,
        width,
        height
    ):
        env = self.env
        DSL = env.DSL
        
        def generate_chart(file_path):
            time_serieses = []
            R = self.R
            c = R("c")
            spec_names = []
            starts = []
            ends = []
            yearly = []
            for spec in specs:
                query_expression = spec["query_expression"]
                expression = DSL.parse(query_expression)
                understood_expression_string = str(expression)
                spec_names.append(understood_expression_string)
                units = DSL.units(expression)
                unit_string = str(units)
                if units is None:
                    analysis_strings = []
                    def analysis_out(*things):
                        analysis_strings.append("".join(map(str, things)))
                    DSL.analysis(expression, analysis_out)
                    raise MeaninglessUnitsException(
                        "\n".join(analysis_strings)
                    )
                is_yearly_values = "Months(" in query_expression
                yearly.append(is_yearly_values)
                code = DSL.R_Code_for_values(
                    expression, 
                    [
                        "time_period",
                        "(time_period - ((time_period + 1000008 + %i) %% 12))" % start_month_0_indexed
                    ][is_yearly_values],
                    "place_id IN (%s)" % ",".join(map(str, spec["place_ids"]))
                )
                #print code
                values_by_time_period_data_frame = R(code)()
                data = {}
                if isinstance(values_by_time_period_data_frame, self.robjects.vectors.StrVector):
                    raise Exception(str(values_by_time_period_data_frame))
                elif values_by_time_period_data_frame.ncol == 0:
                    pass
                else:
                    add = data.__setitem__
                    for key, value in zip(
                        values_by_time_period_data_frame.rx2("key"),
                        values_by_time_period_data_frame.rx2("value")
                    ):
                        add(key, value)
                    # assume monthly values and monthly time_period
                    start_month_number = min(data.iterkeys())
                    starts.append(start_month_number)
                    start_year, start_month = month_number_to_year_month(start_month_number)

                    end_month_number = max(data.iterkeys())
                    ends.append(end_month_number)
                    end_year, end_month = month_number_to_year_month(end_month_number)
                    
                    try:
                        display_units = {
                            "Kelvin": "Celsius",
                        }[unit_string]
                    except KeyError:
                        converter = lambda x:x
                        display_units = unit_string
                    else:
                        converter = units_in_out[display_units]["out"]
                    
                    values = []
                    for month_number in range(
                        start_month_number,
                        end_month_number+1,
                        [1,12][is_yearly_values]
                    ):
                        if not data.has_key(month_number):
                            values.append(None)
                        else:
                            values.append(converter(data[month_number]))
                    
                    #print values
                    
                    if is_yearly_values:
                        time_serieses.append(
                            R("ts")(
                                self.robjects.FloatVector(values),
                                start = c(start_year),
                                end = c(end_year),
                                frequency = 1
                            )
                        )
                    else:
                        time_serieses.append(
                            R("ts")(
                                self.robjects.FloatVector(values),
                                start = c(start_year, start_month),
                                end = c(end_year, end_month),
                                frequency = 12
                            )
                        )
            R((
                "png(filename = '%(file_path)s', "
                    "width = %(width)i, "
                    "height = %(height)i"
                ")"
            ) % dict(
                file_path = file_path,
                width = width,
                height = height
            ))
            plot_chart = R(
                "function (xlab, ylab, n, names, axis_points, axis_labels, axis_orientation, ...) {"
                    "par(xpd = T, mar=par()$mar+c(0,0, length(names)/1.5, 0))\n"
                    "ts.plot(...,"
                        "gpars = list("
                            "xlab = xlab,"
                            "ylab = ylab,"
                            "col = c(1:n),"
                            "pch = c(21:25),"
                            "type = '%(plot_type)s',"
                            "xaxt = 'n'"
                        ")"
                    ")\n"
                    "axis("
                        "1, "
                        "at = axis_points,"
                        "labels = axis_labels,"
                        "las = axis_orientation"
                    ")\n"
                    "legend("
                        "par()$usr[1],"
                        "par()$usr[4] + ((par()$usr[4] - par()$usr[3]) / ((%(height)i - %(total_margin_height)i)/(%(line_height_factor)i * length(names)))) ,"
                        "names,"
                        "cex = 0.8,"
                        "pt.bg = c(1:n),"
                        "pch = c(21:25),"
                        "bty = 'n'"
                    ")\n"
                "}" % dict(
                    plot_type= "lo"[is_yearly_values],
                    width = width,
                    height = height,
                    # R uses Normalised Display coordinates.
                    # these have been found by recursive improvement 
                    # they place the legend legibly. tested up to 8 lines
                    total_margin_height = 150,
                    line_height_factor = 17,
                )
            )
            
            min_start = min(starts)
            max_end = max(ends)
            show_months = any(not is_yearly for is_yearly in yearly)
            if show_months:
                # label_step spaces out the x-axis marks sensibly based on
                # width by not marking all of them.
                ticks = (max_end - min_start) + 1
                # ticks should be made at 1,2,3,4,6,12 month intervals 
                # or 1, 2, 5, 10, 20, 50 year intervals
                # depending on the usable width and the number of ticks
                # ticks should be at least 15 pixels apart
                usable_width = width - 100
                max_ticks = usable_width / 15.0
                Y = 12
                for step in [1,2,3,4,6,12,2*Y, 5*Y, 10*Y, 20*Y, 50*Y]:
                    if ticks/step <= max_ticks:
                        break

                axis_points = []
                axis_labels = []
                month_names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(" ")
                for month_number in range(min_start, max_end+1, step):
                    year, month = month_number_to_year_month(month_number)
                    month -= 1
                    axis_points.append(
                        year + (month / 12.0)
                    )
                    axis_labels.append(
                        "%s %i" % (month_names[month], year)
                    )
            else:
                # show only years
                axis_points = []
                axis_labels = []
                start_year, start_month = month_number_to_year_month(min_start)
                end_year, end_month = month_number_to_year_month(max_end)
                for year in range(start_year, end_year+1):
                    axis_points.append(year)
                    axis_labels.append(year)
            
            if display_units == "Celsius":
                display_units = "\xc2\xb0 Celsius"
            plot_chart(
                "",
                display_units,
                len(time_serieses),
                spec_names,
                axis_points,
                axis_labels,
                axis_orientation = [0,2][show_months],
                *time_serieses
            )
            R("dev.off()")

        import md5
        import gluon.contrib.simplejson as JSON

        import datetime
        def serialiseDate(obj):
            if isinstance(
                obj,
                (
                    datetime.date, 
                    datetime.datetime, 
                    datetime.time
                )
            ): 
                return obj.isoformat()[:19].replace("T"," ") 
            raise TypeError("%r is not JSON serializable" % (obj,)) 
        
        return get_cached_or_generated_file(
            "".join((
                md5.md5(
                    JSON.dumps(
                        [specs, width, height],
                        sort_keys=True,
                        default=serialiseDate,
                    )
                ).hexdigest(),
                ".png"
            )),
            generate_chart
        )

    def place_data(map_plugin):
        def generate_places(file_path):
            "return all place data in JSON format"
            places_strings = []
            append = places_strings.append
            extend = places_strings.extend
            db = map_plugin.env.db
            for place_row in db(
                # only show Nepal
                (db.climate_place.longitude > 79.5) & 
                (db.climate_place.longitude < 88.5) & 
                (db.climate_place.latitude > 26.0) & 
                (db.climate_place.latitude < 30.7)
            ).select(
                db.climate_place.id,
                db.climate_place.longitude,
                db.climate_place.latitude,
                db.climate_place_elevation.elevation_metres,
                db.climate_place_station_id.station_id,
                db.climate_place_station_name.name,
                db.climate_place_region.region_id,
                left = (
                    db.climate_place_region.on(
                        db.climate_place.id == db.climate_place_region.id
                    ),
                    db.climate_place_elevation.on(
                        (db.climate_place.id == db.climate_place_elevation.id)
                    ),
                    db.climate_place_station_id.on(
                        (db.climate_place.id == db.climate_place_station_id.id)
                    ),
                    db.climate_place_station_name.on(
                        (db.climate_place.id == db.climate_place_station_name.id)
                    )
                )
            ):
                append(
                    "".join((
                        "[", str(place_row.climate_place.id), ",{",
                            '"longitude":', str(place_row.climate_place.longitude),
                            ',"latitude":', str(place_row.climate_place.latitude),
                            ',"elevation":', str(place_row.climate_place_elevation.elevation_metres or "null"),
                            ',"station_id":', str(place_row.climate_place_station_id.station_id or "null"),
                            ',"name":"', (
                                place_row.climate_place_station_name.name or "%sN %sE" % (
                                    place_row.climate_place.latitude,
                                    place_row.climate_place.longitude
                                )
                            ).replace('"', '\\"'),'"'
                            ',"region_id":', str(place_row.climate_place_region.region_id or "null"),
                        "}]"
                    ))
                )
            file = open(file_path, "w")
            file.write(
                "[%s]" % ",".join(places_strings)
            )
            file.close()
        
        return get_cached_or_generated_file(
            "places.json",
            generate_places
        )
    
        