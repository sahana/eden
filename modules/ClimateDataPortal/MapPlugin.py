# -*- coding: utf-8 -*-


from gluon.dal import Expression

from Cache import *
import gluon.contrib.simplejson as JSON
from . import SampleTable, month_number_to_year_month, units_in_out
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
                yearly_values = "Months(" in query_expression
                code = DSL.R_Code_for_values(
                    expression, 
                    ["time_period", "(time_period - (time_period % 12))"][yearly_values],
                    "place_id IN (%s)" % ",".join(map(str, spec["place_ids"]))
                )
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
                    start_year, start_month = month_number_to_year_month(start_month_number)
                    end_month_number = max(data.iterkeys())
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
                        [1,12][yearly_values]
                    ):
                        if not data.has_key(month_number):
                            values.append(None)
                        else:
                            values.append(converter(data[month_number]))
                    
                    if yearly_values:
                        time_serieses.append(
                            R("ts")(
                                self.robjects.FloatVector(values),
                                start = c(start_year, start_month),
                                end = c(end_year, end_month),
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
                "function (xlab, ylab, n, names, ...) {"
                    "par(xpd = T, mar=par()$mar+c(0,0,4,0))\n"
                    "ts.plot(...,"
                        "gpars = list(xlab=xlab, ylab=ylab, bg=c(1:n), pch=c(21:25), type='%(plot_type)s')"
                    ")\n"
                    "legend("
                        "par()$usr[1],"
                        "par()$usr[4]+4,"
                        "names,"
                        "cex=0.8, pt.bg=c(1:n), pch=c(21:25), bty='n'"
                    ")\n"
                "}" % dict(
                    plot_type= "lo"[yearly_values]
                )
            )
            plot_chart(
                "Time",
                display_units,
                len(time_serieses),
                spec_names,
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
