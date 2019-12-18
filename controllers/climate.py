# -*- coding: utf-8 -*-

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

ClimateDataPortal = local_import("ClimateDataPortal")
SampleTable = ClimateDataPortal.SampleTable
DSL = local_import("ClimateDataPortal.DSL")

def _map_plugin(**client_config):
    return ClimateDataPortal.MapPlugin(
        env = Storage(globals()),
        year_max = 2100,
        year_min = 1940,
        place_table = climate_place,
        client_config = client_config
    )

# -----------------------------------------------------------------------------
def index():
    try:
        module_name = settings.modules[module].name_nice
    except:
        module_name = T("Climate")

    # Include an embedded Overview Map on the index page
    config = gis.get_config()

    if config.wmsbrowser_url:
        wms_browser = {
            "name" : config.wmsbrowser_name,
            "url" : config.wmsbrowser_url
        }
    else:
        wms_browser = None

    print_service = settings.get_gis_print_service()
    if print_service:
        print_tool = {"url": print_service}
    else:
        print_tool = {}

    vars = request.vars
    if vars.get("zoom", None) is not None:
        zoom = int(vars["zoom"])
    else:
        zoom = 7

    if vars.get("coords", None) is not None:
        lon, lat = [float(c) for c in vars["coords"].split(",")]
    else:
        lon = 84.1
        lat = 28.5

    gis_map = gis.show_map(
        lon = lon,
        lat = lat,
        zoom = zoom,
        toolbar = vars.get("display_mode", None) != "print",
        googleEarth = True,
        wms_browser = wms_browser, # dict
        plugins = [
            _map_plugin(
                **vars
            )
        ]
    )

    response.title = module_name
    return dict(
        module_name=module_name,
        map=gis_map
    )

# -----------------------------------------------------------------------------
def climate_overlay_data():
    kwargs = dict(request.vars)

    arguments = {}
    errors = []
    for kwarg_name, converter in dict(
        query_expression = str,
    ).items():
        try:
            value = kwargs.pop(kwarg_name)
        except KeyError:
            errors.append("%s missing" % kwarg_name)
        else:
            try:
                arguments[kwarg_name] = converter(value)
            except TypeError:
                errors.append("%s is wrong type" % kwarg_name)
            except AssertionError as assertion_error:
                errors.append("%s: %s" % (kwarg_name, assertion_error))
    if kwargs:
        errors.append("Unexpected arguments: %s" % list(kwargs.keys()))

    if errors:
        raise HTTP(400, "<br />".join(errors))
    else:
        try:
            data_path = _map_plugin().get_overlay_data(**arguments)
        # only DSL exception types should be raised here
        except DSL.DSLSyntaxError as syntax_error:
            raise HTTP(400, json.dumps({
                "error": "SyntaxError",
                "lineno": syntax_error.lineno,
                "offset": syntax_error.offset,
                "understood_expression": syntax_error.understood_expression
            }))
        except (
            DSL.MeaninglessUnitsException,
            DSL.DimensionError,
            DSL.DSLTypeError
        ) as exception:
            raise HTTP(400, json.dumps({
                "error": exception.__class__.__name__,
                "analysis": str(exception)
            }))
        else:
            return response.stream(
                open(data_path, "rb"),
                chunk_size=4096
            )

# -----------------------------------------------------------------------------
def climate_csv_location_data():
    kwargs = dict(request.vars)

    arguments = {}
    errors = []
    for kwarg_name, converter in dict(
        query_expression = str,
    ).items():
        try:
            value = kwargs.pop(kwarg_name)
        except KeyError:
            errors.append("%s missing" % kwarg_name)
        else:
            try:
                arguments[kwarg_name] = converter(value)
            except TypeError:
                errors.append("%s is wrong type" % kwarg_name)
            except AssertionError as assertion_error:
                errors.append("%s: %s" % (kwarg_name, assertion_error))
    if kwargs:
        errors.append("Unexpected arguments: %s" % list(kwargs.keys()))

    if errors:
        raise HTTP(400, "<br />".join(errors))
    else:
        data_path = _map_plugin().get_csv_location_data(**arguments)
        # only DSL exception types should be raised here
        return response.stream(
            open(data_path, "rb"),
            chunk_size=4096
        )

# -----------------------------------------------------------------------------
def climate_chart():
    import gluon.contenttype
    data_image_file_path = _climate_chart(gluon.contenttype.contenttype(".png"))
    return response.stream(
        open(data_image_file_path, "rb"),
        chunk_size=4096
    )

# -----------------------------------------------------------------------------
def _climate_chart(content_type):
    """
    """

    kwargs = dict(request.vars)
    specs = json.loads(kwargs.pop("spec"))
    def list_of(converter):
        def convert_list(choices):
            return list(map(converter, choices))
        return convert_list
    checked_specs = []
    for label, spec in specs.items():
        arguments = {}
        errors = []
        for name, converter in dict(
            query_expression = str,
            place_ids = list_of(int)
        ).items():
            try:
                value = spec.pop(name)
            except KeyError:
                errors.append("%s missing" % name)
            else:
                try:
                    arguments[name] = converter(value)
                except TypeError:
                    errors.append("%s is wrong type" % name)
                except AssertionError as assertion_error:
                    errors.append("%s: %s" % (name, assertion_error))
        if spec:
            errors.append("Unexpected arguments: %s" % list(spec.keys()))
        checked_specs.append((label, arguments))

    if errors:
        raise HTTP(400, "<br />".join(errors))
    else:
        response.headers["Content-Type"] = content_type
        data_image_file_path = _map_plugin().render_plots(
            specs = checked_specs,
            width = int(kwargs.pop("width")),
            height = int(kwargs.pop("height"))
        )
        return data_image_file_path

# -----------------------------------------------------------------------------
def climate_chart_download():
    data_image_file_path = _climate_chart("application/force-download")
    import os
    response.headers["Content-disposition"] = (
        "attachment; filename=" +
        os.path.basename(data_image_file_path)
    )
    return response.stream(
        open(data_image_file_path, "rb"),
        chunk_size=4096
    )

# -----------------------------------------------------------------------------
def chart_popup():
    """ Custom View """
    return {}

# -----------------------------------------------------------------------------
def buy_data():
    """ Custom View """
    return {}

# -----------------------------------------------------------------------------
def stations():
    """
        Return all station data in JSON format
        - join the 4 tables assuming a common ID to link records
    """

    stations_strings = []
    append = stations_strings.append

    table = s3db.climate_place
    etable = s3db.climate_place_elevation
    itable = s3db.climate_place_station_id
    ntable = s3db.climate_place_station_name
    query = (table.id == etable.id) & \
            (table.id == itable.id) & \
            (table.id == ntable.id)
    rows = db(query).select(table.id,
                            table.longitude,
                            table.latitude,
                            etable.elevation_metres,
                            itable.station_id,
                            ntable.name)
    for place_row in rows:
        append(
            "".join((
                "(", str(place_row.climate_place.id), ",{",
                    '"longitude":', str(place_row.climate_place.longitude),
                    ',"latitude":', str(place_row.climate_place.latitude),
                "}"
            ))
        )
    return "[%s]" % ",".join(stations_strings)

# -----------------------------------------------------------------------------
def places():
    """
    """

    from datetime import datetime, timedelta
    response.headers["Expires"] = (
        datetime.now() + timedelta(days = 7)
    ).strftime("%a, %d %b %Y %H:%M:%S GMT") # not GMT, but can't find a way
    return response.stream(
        open(_map_plugin().place_data(), "rb"),
        chunk_size=4096
    )

# =============================================================================
def sample_table_spec():
    return s3_rest_controller()

# =============================================================================
def station_parameter():
    return s3_rest_controller()

# =============================================================================
def purchase():
    """
    """

    table = s3db.climate_purchase
    if not auth.is_logged_in():
        redirect(URL(c = "default",
                     f = "user",
                     args = ["login"],
                     vars = {"_next":URL(c="climate",
                                         f="purchase")}))

    if auth.s3_has_role("ADMIN"):
        ADMIN = True
    else:
        ADMIN = False
        table.paid.writable = False
        table.price.writable = False
        s3.filter = (table.created_by == auth.user.id)

    def prep(r):
        if not ADMIN and r.record and r.record.paid:
            for f in table.fields:
                table[f].writable = False

        if r.method == "read":
            s3.rfooter = DIV(
                T("Please make your payment in person at the DHM office, or by bank Transfer to:"),
                TABLE(
                    TR("Bank Name", "Nepal Rastra Bank"),
                    TR("Branch Address", "Kathmandu Banking Office"),
                    TR("Branch City", "Kathmandu"),
                    TR("A/c Holder", "Dept. of Hydrology and Meteorology"),
                    TR("Office Code No", "27-61-04"),
                    TR("Office A/c No", "KA 1-1-199"),
                    TR("Revenue Heading No", "1-1-07-70")
                )
            )
        return True

    def rheader(r):
        record = r.record
        if record and record.paid:
            # These are the parameters to download the data export file
            # see models/climate.py for more details
            return A("Download this data",
                     _href=URL(c="download_purchased_data",
                               vars={"purchase_id": record.id}),
                     _style="border:1px solid black; padding:0.5em; background-color:#0F0; color:black; text-decoration:none;"
                    )
        else:
            return None

    s3.prep = prep

    output = s3_rest_controller(rheader = rheader)
    output["addheader"] = T("Please enter the details of the data you wish to purchase")
    return output

# -----------------------------------------------------------------------------
def prices():
    """
    """

    if not auth.is_logged_in():
        redirect(URL(c="default",
                     f="user",
                     args=["login"],
                     vars = {"_next": URL(c="climate",
                                          f="prices")}
                    )
                )
    else:
        if auth.s3_has_role("ADMIN"):
            return s3_rest_controller()


# =============================================================================
def save_query():
    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def request_image():
    """
    """

    from datetime import datetime, timedelta
    response.headers["Expires"] = (
        datetime.now() + timedelta(days = 7)
    ).strftime("%a, %d %b %Y %H:%M:%S GMT") # not GMT, but can't find a way
    response.headers["Content-Type"] = "application/force-download"
    response.headers["Content-disposition"] = (
        "attachment; filename=MapScreenshot.png"
    )
    vars = request.vars
    return response.stream(
        open(
            _map_plugin().printable_map_image_file(
                command = (
                    request.env.applications_parent + "/applications/" +
                    "%s/modules/webkit_url2png.py" % appname
                ),
                url_prefix = (
                    "http://%(http_host)s/%(appname)s/%(controller)s"
                ) % dict(
                    http_host = request.env.http_host, # includes port
                    appname = appname,
                    controller = request.controller,
                ),
                query_string = request.env.query_string,
                width = int(vars["width"]),
                height = int(vars["height"])
            ),
            "rb"
        ),
        chunk_size=4096
    )

# -----------------------------------------------------------------------------
def download_purchased_data():
    """
    """

    purchase_id = request.vars["purchase_id"]
    query = (s3db.climate_purchase.id == purchase_id)
    climate_purchase = db(query).select(limitby=(0, 1)).first()
    if climate_purchase is not None and climate_purchase.paid:
        sample_table = SampleTable.with_id(climate_purchase.parameter_id)
        parameter_name = repr(sample_table)
        # climate_purchase.station_id is currently actually the place_id
        place_id = climate_purchase.station_id
        itable = s3db.climate_place_station_id
        ntable = s3db.climate_place_station_name
        query = (itable.id == place_id) & \
                (ntable.id == place_id)
        station = db(query).select(ntable.name,
                                   itable.station_id,
                                   limitby=(0, 1)).first()

        station_id = station.climate_place_station_id.station_id
        station_name = station.climate_place_station_name.name
        date_from = climate_purchase.date_from
        date_to = climate_purchase.date_to

        csv_data = sample_table.csv_data(
            place_id = place_id,
            date_from = date_from,
            date_to = date_to
        )
        response.headers["Content-Type"] = "application/force-download"
        response.headers["Content-disposition"] = (
            "attachment; filename="
            "%(parameter_name)s"
            "_%(station_id)i"
            "_%(station_name)s"
            "_%(date_from)s"
            "_%(date_to)s.csv" % locals()
        )
        return csv_data
    else:
        return

# -----------------------------------------------------------------------------
def get_years():
    """
    """

    from datetime import datetime, timedelta
    response.headers["Expires"] = (
        datetime.now() + timedelta(days = 7)
    ).strftime("%a, %d %b %Y %H:%M:%S GMT") # not GMT, but can't find a way
    return response.stream(
        open(_map_plugin().get_available_years(request.vars["dataset_name"]), "rb"),
        chunk_size=4096
    )

# END =========================================================================
