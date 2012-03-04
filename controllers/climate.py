# -*- coding: utf-8 -*-

module = "climate"
resourcename = request.function

# @todo: re-write this for new framework:
#response.menu = s3_menu_dict[module]["menu"]
#response.menu.append(s3.menu_help)
#response.menu.append(s3.menu_auth)
#if s3.menu_admin:
    #response.menu.append(s3.menu_admin)

ClimateDataPortal = local_import("ClimateDataPortal")
SampleTable = ClimateDataPortal.SampleTable
DSL = local_import("ClimateDataPortal.DSL")

sample_types = SampleTable._SampleTable__types.values()
variable_names = SampleTable._SampleTable__names.keys()

def map_plugin(**client_config):
    return ClimateDataPortal.MapPlugin(
        env = Storage(globals()),
        year_max = 2100,
        year_min = 1950,
        place_table = climate_place,
        client_config = client_config
    )

def index():
    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Climate")

    # Include an embedded Overview Map on the index page
    config = gis.get_config()

    search = True
    catalogue_layers = False

    if config.wmsbrowser_url:
        wms_browser = {
            "name" : config.wmsbrowser_name,
            "url" : config.wmsbrowser_url
        }
    else:
        wms_browser = None

    print_service = deployment_settings.get_gis_print_service()
    if print_service:
        print_tool = {"url": print_service}
    else:
        print_tool = {}

    map = gis.show_map(
        lat = 28.5,
        lon = 84.1,
        zoom = 7,
        toolbar = False,
        wms_browser = wms_browser, # dict
        plugins = [
            map_plugin(
                **request.vars
            )
        ]
    )

    response.title = module_name
    return dict(
        module_name=module_name,
        map=map
    )

month_names = dict(
    January=1,
    February=2,
    March=3,
    April=4,
    May=5,
    June=6,
    July=7,
    August=8,
    September=9,
    October=10,
    November=11,
    December=12
)

for name, number in month_names.items():
    month_names[name[:3]] = number
for name, number in month_names.items():
    month_names[name.upper()] = number
for name, number in month_names.items():
    month_names[name.lower()] = number

def convert_date(default_month):
    def converter(year_month):
        components = year_month.split("-")
        year = int(components[0])
        assert 1960 <= year, "year must be >= 1960"

        try:
            month_value = components[1]
        except IndexError:
            month = default_month
        else:
            try:
                month = int(month_value)
            except TypeError:
                month = month_names[month_value]

        assert 1 <= month <= 12, "month must be in range 1:12"
        return datetime.date(year, month, 1)
    return converter

def one_of(options):
    def validator(choice):
        assert choice in options, "should be one of %s, not '%s'" % (
            options,
            choice
        )
        return choice
    return validator

aggregation_names = ("Maximum", "Minimum", "Average")

def climate_overlay_data():
    kwargs = dict(request.vars)

    arguments = {}
    errors = []
    for kwarg_name, converter in dict(
        query_expression = str,
    ).iteritems():
        try:
            value = kwargs.pop(kwarg_name)
        except KeyError:
            errors.append("%s missing" % kwarg_name)
        else:
            try:
                arguments[kwarg_name] = converter(value)
            except TypeError:
                errors.append("%s is wrong type" % kwarg_name)
            except AssertionError, assertion_error:
                errors.append("%s: %s" % (kwarg_name, assertion_error))
    if kwargs:
        errors.append("Unexpected arguments: %s" % kwargs.keys())

    if errors:
        raise HTTP(400, "<br />".join(errors))
    else:
        import gluon.contrib.simplejson as JSON
        try:
            data_path = map_plugin().get_overlay_data(**arguments)
        except SyntaxError, syntax_error:
            raise HTTP(400, JSON.dumps({
                "error": "SyntaxError",
                "lineno": syntax_error.lineno,
                "offset": syntax_error.offset,
                "understood_expression": syntax_error.understood_expression
            }))
        except (DSL.MeaninglessUnitsException, TypeError), exception:
            raise HTTP(400, JSON.dumps({
                "error": exception.__class__.__name__,
                "analysis": str(exception)
            }))
        else:
            return response.stream(
                open(data_path,"rb"),
                chunk_size=4096
            )

def list_of(converter):
    def convert_list(choices):
        return map(converter, choices)
    return convert_list

def climate_chart():
    import gluon.contenttype
    data_image_file_path = _climate_chart(gluon.contenttype.contenttype(".png"))
    return response.stream(
        open(data_image_file_path,"rb"),
        chunk_size=4096
    )

def _climate_chart(content_type):
    kwargs = dict(request.vars)
    import gluon.contrib.simplejson as JSON
    specs = JSON.loads(kwargs.pop("spec"))

    checked_specs = []
    for spec in specs:
        arguments = {}
        errors = []
        for name, converter in dict(
            query_expression = str,
            place_ids = list_of(int)
        ).iteritems():
            try:
                value = spec.pop(name)
            except KeyError:
                errors.append("%s missing" % name)
            else:
                try:
                    arguments[name] = converter(value)
                except TypeError:
                    errors.append("%s is wrong type" % name)
                except AssertionError, assertion_error:
                    errors.append("%s: %s" % (name, assertion_error))
        if spec:
            errors.append("Unexpected arguments: %s" % spec.keys())
        checked_specs.append(arguments)

    if errors:
        raise HTTP(400, "<br />".join(errors))
    else:
        response.headers["Content-Type"] = content_type
        data_image_file_path = map_plugin().render_plots(
            specs = checked_specs,
            width = int(kwargs.pop("width")),
            height = int(kwargs.pop("height"))
        )
        return data_image_file_path

def climate_chart_download():
    data_image_file_path = _climate_chart("application/force-download")
    import os
    response.headers["Content-disposition"] = (
        "attachment; filename=" +
        os.path.basename(data_image_file_path)
    )
    return response.stream(
        open(data_image_file_path,"rb"),
        chunk_size=4096
    )

def chart_popup():
    return {}

def buy_data():
    return {}

def stations():
    "return all station data in JSON format"
    stations_strings = []
    append = stations_strings.append
    extend = stations_strings.extend

    for place_row in db(
        (db.climate_place.id == db.climate_place_elevation.id) &
        (db.climate_place.id == db.climate_place_station_id.id) &
        (db.climate_place.id == db.climate_place_station_name.id)
    ).select(
        db.climate_place.id,
        db.climate_place.longitude,
        db.climate_place.latitude,
        db.climate_place_elevation.elevation_metres,
        db.climate_place_station_id.station_id,
        db.climate_place_station_name.name
    ):
        append(
            "".join((
                "(", str(place_row.climate_place.id), ",{",
                    '"longitude":', str(place_row.climate_place.longitude),
                    ',"latitude":', str(place_row.climate_place.latitude),
                "}"
            ))
        )
    return "[%s]" % ",".join(stations_strings)

def places():
    response.headers["Expires"] = "Sat, 25 Dec 2011 20:00:00 GMT"
    return response.stream(
        open(map_plugin().place_data(),"rb"),
        chunk_size=4096
    )

# =============================================================================
def sample_table_spec():
    output = s3_rest_controller()
    return output

# =============================================================================
def station_parameter():
    output = s3_rest_controller()
    return output

# =============================================================================
def purchase():

    def prep(r):
        if r.method == "read":
            response.s3.rfooter = DIV(
                T("Please make your payment in person at the DHM office, or by bank Transfer to:"),
                TABLE(
                    TR("Bank Name","Nepal Rastra Bank"),
                    TR("Branch Address","Kathmandu Banking Office"),
                    TR("Branch City","Kathmandu"),
                    TR("A/c Holder","Dept. of Hydrology and Meteorology"),
                    TR("Office Code No","27-61-04"),
                    TR("Office A/c No","KA 1-1-199"),
                    TR("Revenue Heading No","1-1-07-70")
                )
            )
        return True

    response.s3.prep = prep

    output = s3_rest_controller()
    output["addheader"] = T("Please enter the details of the data you wish to purchase")
    return output

# =============================================================================
def save_query():
    output = s3_rest_controller()
    return output

def request_image():
    vars = request.vars
    import subprocess
    #screenshot_renderer_stdout = StringIO.StringIO()
    url = (
        "http://%(http_host)s/%(application_name)s/%(controller)s"
        "?expression=%(expression)s"
        "&filter=%(filter)s"
        "&display_mode=print"
    ) % dict(
        vars,
        controller = request.controller,
        application_name = request.application,
        http_host = request.env.http_host,
        server_port = request.env.server_port,
    )
    width = int(vars["width"])
    height = int(vars["height"])

    # PyQT4 signals don't like not being run in the main thread
    # run in a subprocess to give it it's own thread
    subprocess_args = (
        request.env.applications_parent+"/applications/"+
        request.application+"/modules/webkit_url2png.py",
        url,
        str(width),
        str(height)
    )
    stdoutdata, stderrdata = subprocess.Popen(
        subprocess_args,
        bufsize = 4096,
        stdout = subprocess.PIPE, # StringIO doesn't work
        stderr = subprocess.PIPE
    ).communicate()
#    if stderrdata:
#        raise Exception(stderrdata)
#    else:
    response.headers["Content-Type"] = "application/force-download"
    response.headers["Content-disposition"] = (
        "attachment; filename=MapScreenshot.png"
    )
    import StringIO
    return response.stream(
        StringIO.StringIO(stdoutdata),
        chunk_size=4096
    )
