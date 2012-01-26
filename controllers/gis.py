# -*- coding: utf-8 -*-

"""
    GIS Controllers

    @author: Fran Boon <fran@aidiq.com>
"""

module = request.controller
resourcename = request.function

# Options Menu (available in all Functions' Views)
s3_menu(module)

#if not deployment_settings.get_security_map() or s3_has_role(MAP_ADMIN):
#   response.menu_options.append([T("Service Catalogue"), False, URL(f="map_service_catalogue")])
#   # Not yet ready for Production
#   response.menu_options.append([T("De-duplicator"), False, URL(f="location_duplicates")])

# -----------------------------------------------------------------------------
def index():
    """
       Module's Home Page
    """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name

    # Include an embedded Map on the index page

    # Icon toolbar?
    toolbar = True

    map = define_map(window=False,
                     toolbar=toolbar)

    # Don't bother with breadcrumbs as they use up real-estate needlessly
    breadcrumbs = []

    # Provide access to the Personalised config
    pconfig = ""
    config_id = session.s3.gis_config_id
    if auth.is_logged_in():
        if config_id == 1:
            pconfig = T("You are using the site-wide map configuration. To create or use a personal map configuration, click %(here)s") % \
                        dict(here=A(T("here"),
                                    _class="marron",
                                    _style="font-weight:bold;",
                                    _href=URL(c="pr", f="person",
                                              args=["config"],
                                              vars={"person.uid":auth.user.person_uuid})))
        else:
            table = s3db.gis_config
            query = (table.id == config_id)
            config = db(query).select(table.pe_id,
                                      limitby=(0, 1)).first()
            if config and config.pe_id:
                table = s3db.pr_person
                query = (table.uuid == auth.user.person_uuid)
                person = db(query).select(table.pe_id,
                                          limitby=(0, 1)).first()
                if person and person.pe_id == config.pe_id:
                    pconfig = T("You are using a personal map configuration. To edit your personal configuration, click %(here)s") % \
                                dict(here=A(T("here"),
                                            _class="marron",
                                            _style="font-weight:bold;",
                                            _href=URL(c="pr", f="person",
                                                      args=["config"],
                                                      vars={"person.uid":auth.user.person_uuid})))

    return dict(map=map, breadcrumbs=breadcrumbs, pconfig=pconfig)

# =============================================================================
def map_viewing_client():
    """
        Map Viewing Client.
        UI for a user to view the overall Maps with associated Features
    """

    map = define_map(window=True,
                     toolbar=True)

    response.title = T("Map Viewing Client")
    return dict(map=map)

# -----------------------------------------------------------------------------
def define_map(window=False, toolbar=False, config=None):
    """
        Define the main Situation Map
        This can then be called from both the Index page (embedded)
        & the Map_Viewing_Client (fullscreen)
    """

    if not config:
        config = gis.get_config()

    if not deployment_settings.get_security_map() or s3_has_role(MAP_ADMIN):
        catalogue_toolbar = True
    else:
        catalogue_toolbar = False

    # @ToDo: Make these configurable
    search = True
    legend = True
    googleEarth = True
    googleStreetview = True
    catalogue_layers = True

    if config.wmsbrowser_url:
        wms_browser = {"name" : config.wmsbrowser_name,
                       "url" : config.wmsbrowser_url}
    else:
        wms_browser = None

    # 'normal', 'mgrs' or 'off'
    mouse_position = deployment_settings.get_gis_mouse_position()

    # http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
    print_service = deployment_settings.get_gis_print_service()
    if print_service:
        print_tool = {"url": print_service}
    else:
        print_tool = {}

    map = gis.show_map(
                       window=window,
                       catalogue_toolbar=catalogue_toolbar,
                       wms_browser = wms_browser,
                       toolbar=toolbar,
                       legend=legend,
                       search=search,
                       catalogue_layers=catalogue_layers,
                       mouse_position = mouse_position,
                       print_tool = print_tool
                      )

    return map

# =============================================================================
def location():
    """ RESTful CRUD controller for Locations """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # Location Search Method
    gis_location_search = s3base.S3LocationSearch(
        simple = (s3base.S3SearchSimpleWidget(
            name="location_search_text_simple",
            label = T("Search"),
            #comment = T("Search for a Location by name, including local names."),  # How? These aren't fields in this table or in a table that we link to.
            comment = T("To search for a location, enter the name. You may use % as wildcard. Press 'Search' without input to list all locations."),
            field = [ "name" ]
            )
        ),
        advanced = (s3base.S3SearchSimpleWidget(
            name = "location_search_text_advanced",
            label = T("Search"),
            #comment = T("Search for a Location by name, including local names."),
            comment = T("To search for a location, enter the name. You may use % as wildcard. Press 'Search' without input to list all locations."),
            field = [ "name"]
            ),
            s3base.S3SearchOptionsWidget(
                name = "location_search_level",
                label = T("Level"),
                field = ["level"],
                cols = 2
            ),
            # NB This currently only works for locations with the country as direct parent (i.e. mostly L1s)
            #s3base.S3SearchOptionsWidget(
            #    name = "location_search_country",
            #    label = T("Country"),
            #    field = ["parent"],
            #    cols = 2
            #),
        )
    )

    s3mgr.configure(tablename,
                    # Don't include Bulky Location Selector in List Views
                    listadd=False,
                    # Custom Search Method
                    search_method=gis_location_search)

    # Custom Method
    s3mgr.model.set_method("gis", "location", method="parents",
                           action=s3_gis_location_parents)

    # Pre-processor
    # Allow prep to pass vars back to the controller
    vars = {}
    # @ToDo: Clean up what needs to be done only for interactive views,
    # vs. what needs to be done generally. E.g. some tooltips are defined
    # for non-interactive.
    def prep(r, vars):

        def get_location_info():
            table = s3db.gis_location
            query = (table.id == r.id)
            return db(query).select(table.lat,
                                    table.lon,
                                    table.level,
                                    limitby=(0, 1)).first()

        # Restrict access to Polygons to just MapAdmins
        if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
            table.code.writable = False
            if r.method == "create":
                table.code.readable = False
            table.gis_feature_type.writable = table.gis_feature_type.readable = False
            table.wkt.writable = table.wkt.readable = False
        elif r.interactive:
            table.code.comment = DIV(_class="tooltip",
                                     _title="%s|%s" % (T("Code"),
                                                       T("For a country this would be the ISO2 code, for a Town, it would be the Airport Locode.")))
            table.wkt.comment = DIV(_class="stickytip",
                                    _title="WKT|%s %s%s %s%s" % (T("The"),
                                                               "<a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>",
                                                               T("Well-Known Text"),
                                                               "</a>",
                                                               T("representation of the Polygon/Line.")))
            table.members.comment = DIV(_class="tooltip",
                      _title="%s|%s|%s|%s|%s" % (T("Members"),
                                                 T("A location group is a set of locations (often, a set of administrative regions representing a combined area)."),
                                                 T("Location groups may be used to filter what is shown on the map and in search results to only entities covered by locations in the group."),
                                                 T("A location group can be used to define the extent of an affected area, if it does not fall within one administrative region."),
                                                 T("Location groups can be used in the Regions menu.")))



        if r.method == "update" and r.id:
            # We don't allow converting a location group to non-group and
            # vice versa. We also don't allow taking away all the members of
            # a group -- setting "notnull" gets the "required" * displayed.
            # Groups don't have parents. (This is all checked in onvalidation.)
            # NB r.id is None for update.url
            location = get_location_info()
            if location.level == "GR":
                table.level.writable = False
                table.parent.readable = table.parent.writable = False
                table.members.notnull = True
                # Record that this is a group location. Since we're setting
                # level to not writable, it won't be in either form.vars or
                # request.vars. Saving it while we have it avoids another
                # db access.
                response.s3.location_is_group = True
            else:
                table.members.writable = table.members.readable = False
                response.s3.location_is_group = False

        if r.interactive:
            if not "group" in r.vars:
                # Hide the Members List (a big download when many records are entered)
                table.members.writable = table.members.readable = False
            # Don't show street address, postcode for hierarchy on read or update.
            if r.method != "create" and r.id:
                try:
                    location
                except:
                    location = get_location_info()
                if location.level:
                    table.addr_street.writable = table.addr_street.readable = False
                    table.addr_postcode.writable = table.addr_postcode.readable = False

            # Options which are only required in interactive HTML views
            table.level.comment = DIV(_class="tooltip",
                                      _title="%s|%s" % (T("Level"),
                                                        T("If the location is a geographic area, then state at what level here.")))
            parent_comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (T("Parent"),
                                                   T("The Area which this Site is located within.")))
            if r.representation == "popup":
                table.parent.comment = parent_comment
            else:
                # Include 'Add Location' button
                table.parent.comment = DIV(A(ADD_LOCATION,
                                             _class="colorbox",
                                             _href=URL(c="gis", f="location",
                                                       args="create",
                                                       vars=dict(format="popup",
                                                                 child="parent")),
                                             _target="top",
                                             _title=ADD_LOCATION),
                                           parent_comment),
            table.osm_id.comment = DIV(_class="stickytip",
                                       _title="OpenStreetMap ID|%s%s%s" % (T("The"),
                                                                           " <a href='http://openstreetmap.org' target=_blank>OpenStreetMap</a> ID. ",
                                                                           T("If you know what the OSM ID of this location is then you can enter it here.")))
            table.geonames_id.comment = DIV(_class="stickytip",
                                            _title="Geonames ID|%s%s%s" % (T("The"),
                                                                           " <a href='http://geonames.org' target=_blank>Geonames</a> ID. ",
                                                                           T("If you know what the Geonames ID of this location is then you can enter it here.")))
            table.comments.comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Comments"),
                                                           T("Please use this field to record any additional information, such as Ushahidi instance IDs. Include a history of the record if it is updated.")))

            if r.representation == "iframe":
                # De-duplicator needs to be able to access UUID fields
                table.uuid.readable = table.uuid.writable = True
                table.uuid.label = "UUID"
                table.uuid.comment = DIV(_class="stickytip",
                                         _title="UUID|%s%s%s" % (T("The"),
                                                                 " <a href='http://eden.sahanafoundation.org/wiki/UUID#Mapping' target=_blank>Universally Unique ID</a>. ",
                                                                 T("Suggest not changing this field unless you know what you are doing.")))

            if r.method in (None, "list") and r.record is None:
                # List
                pass
            elif r.method in ("delete", "search"):
                pass
            else:
                # Add Map to allow locations to be found this way
                config = gis.get_config()
                lat = config.lat
                lon = config.lon
                zoom = config.zoom
                feature_queries = []

                if r.method == "create":
                    add_feature = True
                    add_feature_active = True
                else:
                    if r.method == "update":
                        add_feature = True
                        add_feature_active = False
                    else:
                        # Read
                        add_feature = False
                        add_feature_active = False

                    try:
                        location
                    except:
                        location = get_location_info()
                    if location and location.lat is not None and location.lon is not None:
                        lat = location.lat
                        lon = location.lon
                    # Same as a single zoom on a cluster
                    zoom = zoom + 2

                # @ToDo: Does map make sense if the user is updating a group?
                # If not, maybe leave it out. OTOH, might be nice to select
                # admin regions to include in the group by clicking on them in
                # the map. Would involve boundaries...
                _map = gis.show_map(lat = lat,
                                    lon = lon,
                                    zoom = zoom,
                                    feature_queries = feature_queries,
                                    add_feature = add_feature,
                                    add_feature_active = add_feature_active,
                                    toolbar = True,
                                    collapsed = True)

                # Pass the map back to the main controller
                vars.update(_map=_map)
        elif r.representation == "json":
            # Path field should be visible
            table.path.readable = True
        return True
    response.s3.prep = lambda r, vars=vars: prep(r, vars)

    # Options
    _vars = request.vars
    filters = []

    parent = _vars.get("parent_", None)
    # Don't use 'parent' as the var name as otherwise it conflicts with the form's var of the same name & hence this will be triggered during form submission
    if parent:
        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        _parent = parent.lower()

        # Can't do this using a JOIN in DAL syntax
        # .belongs() not GAE-compatible!
        query = (table.name.lower().like(_parent))
        filters.append((table.parent.belongs(db(query).select(table.id))))
        # ToDo: Make this recursive - want descendants not just direct children!
        # Use new gis.get_children() function

    if filters:
        from operator import __and__
        response.s3.filter = reduce(__and__, filters)

    caller = _vars.get("caller", None)
    if caller:
        # We've been called as a Popup
        if "gis_location_parent" in caller:
            # Hide unnecessary rows
            table.addr_street.readable = table.addr_street.writable = False
        else:
            parent = _vars.get("parent_", None)
            # Don't use 'parent' as the var name as otherwise it conflicts with the form's var of the same name & hence this will be triggered during form submission
            if parent:
                table.parent.default = parent

            # Hide unnecessary rows
            table.level.readable = table.level.writable = False
            table.geonames_id.readable = table.geonames_id.writable = False
            table.osm_id.readable = table.osm_id.writable = False
            table.source.readable = table.source.writable = False
            table.url.readable = table.url.writable = False

    level = _vars.get("level", None)
    if level:
        # We've been called from the Location Selector widget
        table.addr_street.readable = table.addr_street.writable = False

        
    country = S3ReusableField("country", "string", length=2,
                              label = T("Country"),
                              requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                    lambda: gis.get_countries(key_type="code"),
                                    zero = SELECT_LOCATION)),
                              represent = lambda code: \
                                    gis.get_country(code, key_type="code") or UNKNOWN_OPT)

    output = s3_rest_controller(csv_extra_fields = [
                                    dict(label="Country",
                                         field=country())
                                ])

    _map = vars.get("_map", None)
    if _map and isinstance(output, dict):
        output["_map"] = _map

    return output

# -----------------------------------------------------------------------------
def s3_gis_location_parents(r, **attr):

    """
        Return a list of Parents for a Location
        Custom S3Method
    """

    resource = r.resource
    table = resource.table

    # Check permission
    if not s3_has_permission("read", table):
        r.unauthorised()

    if r.representation == "html":

        # @ToDo
        output = dict()
        #return output
        raise HTTP(501, body=s3mgr.ERROR.BAD_FORMAT)

    elif r.representation == "json":

        if r.id:
            # Get the parents for a Location
            parents = gis.get_parents(r.id)
            if parents:
                _parents = {}
                for parent in parents:
                    _parents[parent.level] = parent.id
                output = json.dumps(_parents)
                return output
            else:
                raise HTTP(404, body=s3mgr.ERROR.NO_MATCH)
        else:
            raise HTTP(404, body=s3mgr.ERROR.BAD_RECORD)

    else:
        raise HTTP(501, body=s3mgr.ERROR.BAD_FORMAT)

# -----------------------------------------------------------------------------
def l0():
    """
        A specialised controller to return details for an L0 location
        - suitable for use with the LocationSelector

        arg: ID of the L0 location
        returns JSON
    """

    try:
        record_id = request.args[0]
    except:
        item = s3mgr.xml.json_message(False, 400, "Need to specify a record ID!")
        raise HTTP(400, body=item)

    table = s3db.gis_location
    query = (table.id == record_id) & \
            (table.deleted == False) & \
            (table.level == "L0")
    record = db(query).select(table.id,
                              table.name,
                              # Code for the Geocoder lookup filter
                              table.code,
                              # LatLon for Centering the Map
                              table.lon,
                              table.lat,
                              # Bounds for Zooming the Map
                              table.lon_min,
                              table.lon_max,
                              table.lat_min,
                              table.lat_max,
                              limitby=(0, 1)).first()
    if not record:
        item = s3mgr.xml.json_message(False, 400, "Invalid ID!")
        raise HTTP(400, body=item)

    result = record.as_dict()

    # Check if we have a Regional config defined for this country
    table = s3db.gis_config
    query = (table.region_location_id == record_id)
    config = db(query).select(table.L1,
                              table.L2,
                              table.L3,
                              table.L4,
                              table.L5,
                              table.geocoder,
                              table.strict_hierarchy,
                              table.location_parent_required,
                              limitby=(0, 1)).first()
    if config:
        config = config.as_dict()
        for key in config:
            result[key] = config[key]
    else:
        # Fallback to current config
        config = gis.get_config()
        for key in ["geocoder", "strict_hierarchy", "location_parent_required"]:
            result[key] = config[key]
        for key in config.location_hierarchy:
            result[key] = config.location_hierarchy[key]

    output = json.dumps(result)
    response.headers["Content-Type"] = "application/json"
    return output

# -----------------------------------------------------------------------------
def location_duplicates():
    """
        Handle De-duplication of Locations by comparing the ones which are closest together

        @ToDo: Extend to being able to check locations for which we have no Lat<>Lon info (i.e. just names & parents)
    """

    # @ToDo: Set this via the UI & pass in as a var
    dupe_distance = 50 # km

    # Shortcut
    locations = s3db.gis_location

    table_header = THEAD(TR(TH(T("Location 1")),
                            TH(T("Location 2")),
                            TH(T("Distance(Kms)")),
                            TH(T("Resolve"))))

    # Calculate max possible combinations of records
    # To handle the AJAX requests by the dataTables jQuery plugin.
    totalLocations = db(locations.id > 0).count()

    item_list = []
    if request.vars.iDisplayStart:
        end = int(request.vars.iDisplayLength) + int(request.vars.iDisplayStart)
        locations = db((locations.id > 0) & \
                       (locations.deleted == False) & \
                       (locations.lat != None) & \
                       (locations.lon != None)).select(locations.id,
                                                       locations.name,
                                                       locations.level,
                                                       locations.lat,
                                                       locations.lon)
        # Calculate the Great Circle distance
        count = 0
        for oneLocation in locations[:len(locations) / 2]:
            for anotherLocation in locations[len(locations) / 2:]:
                if count > end and request.vars.max != "undefined":
                    count = int(request.vars.max)
                    break
                if oneLocation.id == anotherLocation.id:
                    continue
                else:
                    dist = gis.greatCircleDistance(oneLocation.lat,
                                                   oneLocation.lon,
                                                   anotherLocation.lat,
                                                   anotherLocation.lon)
                    if dist < dupe_distance:
                        count = count + 1
                        item_list.append([oneLocation.name,
                                          anotherLocation.name,
                                          dist,
                                          "<a href=\"../gis/location_resolve?locID1=%i&locID2=%i\", class=\"action-btn\">Resolve</a>" % (oneLocation.id, anotherLocation.id)
                                         ])
                    else:
                        continue

        item_list = item_list[int(request.vars.iDisplayStart):end]
        # Convert data to JSON
        result  = []
        result.append({
                    "sEcho" : request.vars.sEcho,
                    "iTotalRecords" : count,
                    "iTotalDisplayRecords" : count,
                    "aaData" : item_list
                    })
        output = json.dumps(result)
        # Remove unwanted brackets
        output = output[1:]
        output = output[:-1]
        return output
    else:
        # Don't load records except via dataTables (saves duplicate loading & less confusing for user)
        items = DIV((TABLE(table_header,
                           TBODY(),
                           _id="list",
                           _class="dataTable display")))
        return(dict(items=items))

# -----------------------------------------------------------------------------
def delete_location():

    """ Delete references to a old record and replacing it with the new one. """

    old = request.vars.old
    new = request.vars.new

    # Find all tables which link to the Locations table
    # @ToDo Replace with db.gis_location._referenced_by
    tables = s3_table_links("gis_location")

    for table in tables:
        for count in range(len(tables[table])):
            field = tables[str(db[table])][count]
            query = db[table][field] == old
            db(query).update(**{field:new})

    # Remove the record
    db(s3db.gis_location.id == old).update(deleted=True)
    return "Record Gracefully Deleted"

# -----------------------------------------------------------------------------
def location_resolve():

    """ Opens a popup screen where the de-duplication process takes place. """

    # @ToDo: Error gracefully if conditions not satisfied
    locID1 = request.vars.locID1
    locID2 = request.vars.locID2

    # Shortcut
    locations = s3db.gis_location

    # Remove the comment and replace it with buttons for each of the fields
    count = 0
    for field in locations:
        id1 = str(count) + "Right"      # Gives a unique number to each of the arrow keys
        id2 = str(count) + "Left"
        count  = count + 1

        # Comment field filled with buttons
        field.comment = DIV(TABLE(TR(TD(INPUT(_type="button", _id=id1, _class="rightArrows", _value="-->")),
                                     TD(INPUT(_type="button", _id=id2, _class="leftArrows", _value="<--")))))
        record = locations[locID1]
    myUrl = URL(c="gis", f="location")
    form1 = SQLFORM(locations, record, _id="form1", _action=("%s/%s" % (myUrl, locID1)))

    # For the second location remove all the comments to save space.
    for field in locations:
        field.comment = None
    record = locations[locID2]
    form2 = SQLFORM(locations, record,_id="form2", _action=("%s/%s" % (myUrl, locID2)))
    return dict(form1=form1, form2=form2, locID1=locID1, locID2=locID2)

# -----------------------------------------------------------------------------
def location_links():
    """
        @arg id - the location record id
        Returns a JSON array of records which link to the specified location

        @ToDo: Deprecated with new de-duplicator?
    """

    try:
        record_id = request.args[0]
    except:
        item = s3mgr.xml.json_message(False, 400, "Need to specify a record ID!")
        raise HTTP(400, body=item)

    try:
        # Shortcut
        locations = s3db.gis_location

        deleted = (locations.deleted == False)
        query = (locations.id == record_id)
        query = deleted & query
        record = db(query).select(locations.id, limitby=(0, 1)).first().id
    except:
        item = s3mgr.xml.json_message(False, 404, "Record not found!")
        raise HTTP(404, body=item)

    # Find all tables which link to the Locations table
    # @ToDo: Replace with db.gis_location._referenced_by
    tables = s3_table_links("gis_location")

    results = []
    for table in tables:
        for count in range(len(tables[table])):
            field = tables[str(db[table])][count]
            query = db[table][field] == record_id
            _results = db(query).select()
            module, resourcename = table.split("_", 1)
            for result in _results:
                id = result.id
                # We currently have no easy way to get the default represent for a table!
                try:
                    # Locations & Persons
                    represent = eval("s3_%s_represent(id)" % table)
                except:
                    try:
                        # Organizations
                        represent = eval("s3_%s_represent(id)" % resourcename)
                    except:
                        try:
                            # Many tables have a Name field
                            represent = (id and [db[table][id].name] or ["None"])[0]
                        except:
                            # Fallback
                            represent = id
                results.append({
                    "module" : module,
                    "resource" : resourcename,
                    "id" : id,
                    "represent" : represent
                    })

    output = json.dumps(results)
    return output

# =============================================================================
def map_service_catalogue():
    """
        Map Service Catalogue.
        Allows selection of which Layers are active.
    """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    subtitle = T("List Layers")
    # Start building the Return with the common items
    output = dict(subtitle=subtitle)

    # Hack: We control all perms from this 1 table
    table = s3db.gis_layer_openstreetmap
    authorised = s3_has_permission("update", table)
    item_list = []
    even = True
    if authorised:
        # List View with checkboxes to Enable/Disable layers
        for type in response.s3.gis.layer_types:
            table = db["gis_layer_%s" % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ""
                label = "%s_%s" % (type, str(row.id))
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value=True, _name=label)
                else:
                    enabled = INPUT(_type="checkbox", _name=label)
                item_list.append(TR(TD(A(row.name,
                                         _href=URL("layer_%s" % type,
                                                   args=row.id))),
                                    TD(description),
                                    TD(enabled),
                                    _class=theclass))
        # Feature Layers
        type = "feature"
        for row in db(s3db.gis_layer_feature.id > 0).select():
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            if row.comments:
                    description = row.comments
            else:
                description = ""
            label = "%s_%s" % (type, str(row.id))
            if row.enabled:
                enabled = INPUT(_type="checkbox", value=True, _name=label)
            else:
                enabled = INPUT(_type="checkbox", _name=label)
            item_list.append(TR(TD(A(row.name,
                                     _href=URL(f="layer_feature",
                                               args=row.id))),
                                TD(description),
                                TD(enabled),
                                _class=theclass))

        table_header = THEAD(TR(TH("Layer"),
                                TH("Description"),
                                TH("Enabled?")))
        table_footer = TFOOT(TR(TD(INPUT(_id="submit_button",
                                         _type="submit",
                                         _value=T("Update")),
                                   _colspan=3)),
                             _align="right")
        items = DIV(FORM(TABLE(table_header,
                               TBODY(item_list),
                               table_footer,
                               _id="table-container"),
                    _name="custom",
                    _method="post",
                    _enctype="multipart/form-data",
                    _action=URL(f="layers_enable")))

    else:
        # Simple List View
        for type in response.s3.gis.layer_types:
            table = s3db["gis_layer_%s" % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ""
                if row.enabled:
                    enabled = INPUT(_type="checkbox",
                                    value="on",
                                    _disabled="disabled")
                else:
                    enabled = INPUT(_type="checkbox",
                                    _disabled="disabled")
                item_list.append(TR(TD(A(row.name,
                                         _href=URL("layer_%s" % type,
                                                   args=row.id))),
                                    TD(description),
                                    TD(enabled),
                                    _class=theclass))
        # Feature Layers
        type = "feature"
        table = s3db["gis_layer_%s" % type]
        query = table.id > 0
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            if row.comments:
                description = row.comments
            else:
                description = ""
            if row.enabled:
                enabled = INPUT(_type="checkbox",
                                value="on",
                                _disabled="disabled")
            else:
                enabled = INPUT(_type="checkbox", _disabled="disabled")
            item_list.append(TR(TD(A(row.name,
                                     _href=URL(f="layer_feature",
                                               args=row.id))),
                                TD(description),
                                TD(enabled),
                                _class=theclass))

        table_header = THEAD(TR(TH("Layer"), TH("Description"), TH("Enabled?")))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

    output.update(dict(items=items))
    return output

# -----------------------------------------------------------------------------
def layers_enable():
    """
        Enable/Disable Layers
    """

    # Hack: We control all perms from this 1 table
    table = s3db.gis_layer_openstreetmap
    authorised = s3_has_permission("update", table)
    if authorised:
        for type in response.s3.gis.layer_types:
            resourcename = "gis_layer_%s" % type
            table = s3db[resourcename]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                query_inner = (table.id == row.id)
                var = "%s_%i" % (type, row.id)
                # Read current state
                if db(query_inner).select(table.enabled,
                                          limitby=(0, 1)).first().enabled:
                    # Old state: Enabled
                    if var in request.vars:
                        # Do nothing
                        pass
                    else:
                        # Disable
                        db(query_inner).update(enabled=False)
                        # Audit
                        s3_audit("update", module, resourcename, record=row.id,
                                 representation="html")
                else:
                    # Old state: Disabled
                    if var in request.vars:
                        # Enable
                        db(query_inner).update(enabled=True)
                        # Audit
                        s3_audit("update", module, resourcename, record=row.id,
                                 representation="html")
                    else:
                        # Do nothing
                        pass
        resourcename = "gis_layer_feature"
        table = s3db[resourcename]
        query = table.id > 0
        sqlrows = db(query).select()
        for row in sqlrows:
            query_inner = (table.id == row.id)
            var = "feature_%i" % (row.id)
            # Read current state
            if db(query_inner).select(table.enabled,
                                      limitby=(0, 1)).first().enabled:
                # Old state: Enabled
                if var in request.vars:
                    # Do nothing
                    pass
                else:
                    # Disable
                    db(query_inner).update(enabled=False)
                    # Audit
                    s3_audit("update", module, resourcename, record=row.id,
                             representation="html")
            else:
                # Old state: Disabled
                if var in request.vars:
                    # Enable
                    db(query_inner).update(enabled=True)
                    # Audit
                    s3_audit("update", module, resourcename, record=row.id,
                             representation="html")
                else:
                    # Do nothing
                    pass

        session.flash = T("Layers updated")

    else:
        session.error = T("Not authorised!")

    redirect(URL(f="map_service_catalogue"))

# -----------------------------------------------------------------------------
def config():

    """ RESTful CRUD controller """

    s3db.gis_config_form_setup()

    # Pre-processor
    def prep(r):
        if deployment_settings.get_security_map() and \
           (r.id == 1 or r.vars.region_location_id) and \
           r.method in ["create", "update"] and not s3_has_role(MAP_ADMIN):
            auth.permission.fail()
        response.s3.gis_config_prep_helper(r, r.id)
        return True

    response.s3.prep = prep

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    if auth.is_logged_in():
        table = s3db.gis_config
        ptable = s3db.pr_person
        query = (ptable.uuid == auth.user.person_uuid) & \
                (table.pe_id == ptable.pe_id)
        personalised = db(query).select(table.id,
                                        limitby=(0, 1)).first()
        if personalised:

            output["rheader"] = P(T("You have a personal map configuration. To change your personal configuration, click "),
                                  A(T("here"),
                                    _href=URL(c="pr", f="person",
                                              args=["config"],
                                              vars={"person.uid":auth.user.person_uuid})))
        else:
            output["rheader"] = P(T("To create a personal map configuration, click "),
                                  A(T("here"),
                                    _href=URL(c="pr", f="person",
                                              args=["config"],
                                              vars={"person.uid":auth.user.person_uuid})))

    return output


# -----------------------------------------------------------------------------
def layer_feature():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # Model options
    table.gps_marker.comment = DIV(_class="tooltip",
                                   _title="%s|%s" % (T("GPS Marker"),
                                                     T("Defines the icon used for display of features on handheld GPS.")))

    
    # Load Models
    s3mgr.model.load_all_models()

    # Pre-processor
    def prep(r):
        # Which tables have GIS Locations
        tables = []
        for table in db.tables:
            if "location_id" in db[table]:
                tables.append(table)
        s3db.gis_layer_feature.resource.requires = IS_IN_SET(tables)

        return True
    response.s3.prep = prep

    # Custom Method
    s3mgr.model.set_method(module, resourcename,
                           method="disable",
                           action=disable_layer)

    # Post-processor
    def postp(r, output):
        s3_action_buttons(r)
        # Only show the disable button if the layer is not currently disabled
        query = (r.table.enabled != False)
        rows = db(query).select(r.table.id)
        restrict = [str(row.id) for row in rows]
        response.s3.actions.append(dict(label=str(T("Disable")),
                                        _class="action-btn",
                                        url=URL(args=["[id]", "disable"]),
                                        restrict = restrict
                                        )
                                    )

        if r.record and r.record.resource:
            # Format for the View
            response.s3.feature_resource = "%s_%s" % (r.record.module, r.record.resource)
        return output
    response.s3.postp = postp

    # CRUD Strings
    ADD_FEATURE_LAYER = T("Add Feature Layer")
    LIST_FEATURE_LAYERS = T("List Feature Layers")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_FEATURE_LAYER,
        title_display = T("Feature Layer Details"),
        title_list = T("Feature Layers"),
        title_update = T("Edit Feature Layer"),
        title_search = T("Search Feature Layers"),
        subtitle_create = T("Add New Feature Layer"),
        subtitle_list = LIST_FEATURE_LAYERS,
        label_list_button = LIST_FEATURE_LAYERS,
        label_create_button = ADD_FEATURE_LAYER,
        label_delete_button = T("Delete Feature Layer"),
        msg_record_created = T("Feature Layer added"),
        msg_record_modified = T("Feature Layer updated"),
        msg_record_deleted = T("Feature Layer deleted"),
        msg_list_empty = T("No Feature Layers currently defined"))

    s3mgr.configure(tablename,
                    create_onvalidation = feature_layer_query,
                    update_onvalidation = feature_layer_query)

    output = s3_rest_controller()

    return output

# -----------------------------------------------------------------------------
def feature_layer_query(form):
    """
        OnValidation callback to strip the module from the resource
        - in future may build the simple Query from helpers
    """

    resource = None
    if "resource" in form.vars:
        resource = form.vars.resource
        # Remove the module from name
        form.vars.resource = resource[len(form.vars.module) + 1:]

    #if "advanced" in form.vars:
    #    # We should use the query field as-is
    #    pass

    #if resource:
    #    # We build query from helpers
    #    if "filter_field" in form.vars and "filter_value" in form.vars:
    #        if "deleted" in db[resource]:
    #            form.vars.query = "(db[%s].deleted == False) & (db[%s][%s] == "%s")" % (resource, resource, filter_field, filter_value)
    #        else:
    #            form.vars.query = "(db[%s][%s] == "%s")" % (resource, filter_field, filter_value)
    #    else:
    #        if "deleted" in db[resource]:
    #            # All undeleted members of the resource
    #            form.vars.query = "(db[%s].deleted == False)" % (resource)
    #        else:
    #            # All members of the resource
    #            form.vars.query = "(db[%s].id > 0)" % (resource)
    if not resource:
        # Resource is mandatory if not in advanced mode
        session.error = T("Need to specify a Resource!")

    return

# -----------------------------------------------------------------------------
def symbology():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    output = s3_rest_controller()

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

# -----------------------------------------------------------------------------
def marker():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    output = s3_rest_controller()

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

# -----------------------------------------------------------------------------
def projection():

    """ RESTful CRUD controller """

    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

# -----------------------------------------------------------------------------
def waypoint():

    """ RESTful CRUD controller for GPS Waypoints """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def waypoint_upload():

    """
        Custom View
        Temporary: Likely to be refactored into the main waypoint controller
    """

    return dict()

# -----------------------------------------------------------------------------
def trackpoint():

    """ RESTful CRUD controller for GPS Track points """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def track():

    """ RESTful CRUD controller for GPS Tracks (uploaded as files) """

    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    return s3_rest_controller()


# =============================================================================
# Common CRUD strings for all layers
ADD_LAYER = T("Add Layer")
LAYER_DETAILS = T("Layer Details")
LAYERS = T("Layers")
EDIT_LAYER = T("Edit Layer")
SEARCH_LAYERS = T("Search Layers")
ADD_NEW_LAYER = T("Add New Layer")
LIST_LAYERS = T("List Layers")
DELETE_LAYER = T("Delete Layer")
LAYER_ADDED = T("Layer added")
LAYER_UPDATED = T("Layer updated")
LAYER_DELETED = T("Layer deleted")
# These may be differentiated per type of layer.
TYPE_LAYERS_FMT = "%s Layers"
ADD_NEW_TYPE_LAYER_FMT = "Add New %s Layer"
EDIT_TYPE_LAYER_FMT = "Edit %s Layer"
LIST_TYPE_LAYERS_FMT = "List %s Layers"
NO_TYPE_LAYERS_FMT = "No %s Layers currently defined"

# -----------------------------------------------------------------------------
def enable_layer(r):
    """
        Enable a Layer
            designed to be a custom method called by an action button
    """
    if not r.id:
        session.error = T("Can only enable 1 record at a time!")
        redirect(URL(args=[]))

    query = (r.table.id == r.id)
    db(query).update(enabled = True)
    session.confirmation = T("Layer has been Enabled")
    redirect(URL(args=[]))

# -----------------------------------------------------------------------------
def disable_layer(r):
    """
        Disable a Layer
            designed to be a custom method called by an action button
    """
    if not r.id:
        session.error = T("Can only disable 1 record at a time!")
        redirect(URL(args=[]))

    query = (r.table.id == r.id)
    db(query).update(enabled = False)
    session.confirmation = T("Layer has been Disabled")
    redirect(URL(args=[]))

# -----------------------------------------------------------------------------
def layer_openstreetmap():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # CRUD Strings
    type = "OpenStreetMap"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_bing():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # This flag is set onvalidation based on the individual layers
    table.enabled.readable = table.enabled.writable = False

    table.name.label = T("Description")
    table.description.readable = table.description.writable = False
    table.apikey.label = T("API Key")
    table.aerial_enabled.label = T("Enabled?")
    table.aerial.label = T("Name")
    table.road_enabled.label = T("Enabled?")
    table.road.label = T("Name")
    table.hybrid_enabled.label = T("Enabled?")
    table.hybrid.label = T("Name")

    # CRUD Strings
    type = "Bing"
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_update=EDIT_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED)

    s3mgr.configure(tablename,
                    deletable=False,
                    listadd=False,
                    subheadings = {
                        T("Satellite Layer"): "aerial_enabled",
                        T("Roads Layer"): "road_enabled",
                        T("Hybrid Layer"): "hybrid_enabled",
                        "": "role_required"
                    })

    # This layer should only ever have a single layer, so display this direct
    record = db(table.id > 0).select(table.id,
                                     limitby=(0, 1),
                                     cache=s3db.cache).first()
    if record:
        args = [str(record.id)]
    else:
        args = ["create"]

    # Parse the Request
    r = s3mgr.parse_request(args=args)

    # Execute the request
    output = r()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_google():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # This flag is set onvalidation based on the individual layers
    table.enabled.readable = table.enabled.writable = False

    table.name.label = T("Description")
    table.description.readable = table.description.writable = False
    table.apikey.label = T("API Key")
    table.satellite_enabled.label = T("Enabled?")
    table.satellite.label = T("Name")
    table.maps_enabled.label = T("Enabled?")
    table.maps.label = T("Name")
    table.hybrid_enabled.label = T("Enabled?")
    table.hybrid.label = T("Name")
    table.mapmaker_enabled.label = T("Enabled?")
    table.mapmaker.label = T("Name")
    table.mapmaker.comment = T("Enabling MapMaker layers disables the StreetView functionality")
    table.mapmakerhybrid_enabled.label = T("Enabled?")
    table.mapmakerhybrid.label = T("Name")
    table.earth_enabled.label = T("Earth Enabled?")
    table.streetview_enabled.label = T("Streetview Enabled?")

    # CRUD Strings
    type = "Google"
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_update=EDIT_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED)

    s3mgr.configure(tablename,
                    deletable=False,
                    listadd=False,
                    subheadings = {
                        T("Satellite Layer"): "satellite_enabled",
                        T("Roads Layer"): "maps_enabled",
                        T("Hybrid Layer"): "hybrid_enabled",
                        T("MapMaker Layer"): "mapmaker_enabled",
                        T("MapMaker Hybrid Layer"): "mapmakerhybrid_enabled",
                        "": "earth_enabled",
                        "": "role_required"
                    })

    # This layer should only ever have a single layer, so display this direct
    record = db(table.id > 0).select(table.id,
                                     limitby=(0, 1),
                                     cache=s3db.cache).first()
    if record:
        args = [str(record.id)]
    else:
        args = ["create"]

    # Parse the Request
    r = s3mgr.parse_request(args=args)

    # Execute the request
    output = r()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_mgrs():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # CRUD Strings
    type = "MGRS"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    s3mgr.configure(tablename, deletable=False, listadd=False)
    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_geojson():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "GeoJSON"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_georss():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "GeoRSS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3mgr.model.set_method(module, resourcename, method="enable",
                           action=enable_layer)

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            s3_action_buttons(r)
            # Only show the enable button if the layer is not currently enabled
            query = (r.table.enabled != True)
            rows = db(query).select(r.table.id)
            restrict = [str(row.id) for row in rows]
            response.s3.actions.append(dict(label=str(T("Enable")),
                                            _class="action-btn",
                                            url=URL(args=["[id]", "enable"]),
                                            restrict = restrict
                                            )
                                        )
        return output
    response.s3.postp = postp

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_gpx():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # Model options
    # Needed in multiple controllers, so defined in Model

    # CRUD Strings
    type = "GPX"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_kml():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "KML"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            s3_action_buttons(r, copyable=True)
        return output
    response.s3.postp = postp

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_tms():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "TMS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3mgr.model.set_method(module, resourcename,
                           method="enable",
                           action=enable_layer)

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            s3_action_buttons(r, copyable=True)
            # Only show the enable button if the layer is not currently enabled
            query = (r.table.enabled != True)
            rows = db(query).select(r.table.id)
            restrict = [str(row.id) for row in rows]
            response.s3.actions.append(dict(label=str(T("Enable")),
                                            _class="action-btn",
                                            url=URL(args=["[id]", "enable"]),
                                            restrict = restrict
                                            )
                                        )
        return output
    response.s3.postp = postp

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_wfs():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "WFS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            s3_action_buttons(r, copyable=True)
        return output
    response.s3.postp = postp

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_wms():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "WMS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3mgr.model.set_method(module, resourcename,
                           method="enable",
                           action=enable_layer)

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            s3_action_buttons(r, copyable=True)
            # Only show the enable button if the layer is not currently enabled
            query = (r.table.enabled != True)
            rows = db(query).select(r.table.id)
            restrict = [str(row.id) for row in rows]
            response.s3.actions.append(dict(label=str(T("Enable")),
                                            _class="action-btn",
                                            url=URL(args=["[id]","enable"]),
                                            restrict = restrict
                                            )
                                        )
        return output
    response.s3.postp = postp

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
@auth.s3_requires_membership("MapAdmin")
def layer_js():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "JS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# -----------------------------------------------------------------------------
def layer_xyz():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3mgr.load(tablename)

    # CRUD Strings
    type = "XYZ"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    output = s3_rest_controller()

    if not "gis" in response.view:
        response.view = "gis/%s" % response.view

    return output

# =============================================================================
def cache_feed():
    """
        RESTful CRUD controller
        - cache GeoRSS/KML feeds &
          make them available to the Map Viewing Client as GeoJSON

        The create.georss/create.kml methods are designed to be called
        asynchronously using Celery: http://celeryproject.org/

        This allows:
        * Feed can be refreshed on a schedule rather than every client request
          - especially useful when unzipping or following network links
        * BBOX strategy can be used to allow clients to only download the
          features in their area of interest
        * Can parse the feed using XSLT to extract whatever information we
          want from the feed
        * Can unify the client-side support for Markers & Popups
        * Slightly smaller OpenLayers.js
        * Remove dependency from filesystem to support scaling
          - EC2, GAE or clustering
        * Possible to Cluster multiple feeds together
          - will require rewriting the way we turn layers on/off if we wish
            to retain the ability to do so independently
        * Can have dynamic Layer Filtering
          - change layer.protocol.url
          - call refresh strategy

        NB This can't be simply called 'cache' as this conflicts with the
        global cache object
    """

    resourcename = "cache"

    # Load Models
    #s3mgr.load("gis_cache")

    #if kml:
        # Unzip & Follow Network Links
        #download_kml.delay(url)

    output = s3_rest_controller(module, resourcename)
    return output

# =============================================================================
def feature_query():
    """
        RESTful CRUD controller
        - cache Feature Queries &
          make them available to the Map Viewing Client as GeoJSON

        This allows:
        * Feed can be refreshed on a schedule rather than every client request
          - especially useful when unzipping or following network links
        * BBOX strategy can be used to allow clients to only download the
          features in their area of interest
        * Can parse the feed using XSLT to extract whatever information we
          want from the feed
        * Can unify the client-side support for Markers & Popups
        * Slightly smaller OpenLayers.js
        * Remove dependency from filesystem to support scaling
          - EC2, GAE or clustering
        * Possible to Cluster multiple feeds together
          - will require rewriting the way we turn layers on/off if we wish
            to retain the ability to do so independently
        * Can have dynamic Layer Filtering
          - change layer.protocol.url
          - call refresh strategy

        The create.georss/create.kml methods are designed to be called
        asynchronously using S3Task
    """

    table = s3db.gis_feature_query

    # Filter out any records without LatLon
    response.s3.filter = (table.lat != None) & (table.lon != None)

    # Parse the Request
    r = s3mgr.parse_request()

    if r.representation != "geojson":
        session.error = BADFORMAT
        redirect(URL(c="default", f="index", args=None, vars=None))

    # Execute the request
    output = r()

    return output

# =============================================================================
def display_feature():
    """
        Cut-down version of the Map Viewing Client.
        Used by gis_location_represent() to show just this feature on the map.
        Called by the s3_viewMap() JavaScript
    """

    # The Feature
    feature_id = request.args[0]

    table = s3db.gis_location

    # Check user is authorised to access record
    if not s3_has_permission("read", table, feature_id):
        session.error = T("No access to this record!")
        raise HTTP(401, body=s3mgr.xml.json_message(False, 401, session.error))

    feature = db(table.id == feature_id).select(limitby=(0, 1)).first()

    config = gis.get_config()

    try:
        # Centre on Feature
        lat = feature.lat
        lon = feature.lon
        if (lat is None) or (lon is None):
            if feature.get("parent"):
                # Skip the current record if we can
                latlon = gis.get_latlon(feature.parent)
            elif feature.get("id"):
                latlon = gis.get_latlon(feature.id)
            else:
                # nothing we can do!
                raise
            if latlon:
                lat = latlon["lat"]
                lon = latlon["lon"]
            else:
                # nothing we can do!
                raise
    except:
        lat = config.lat
        lon = config.lon

    # Default zoom +2 (same as a single zoom on a cluster)
    zoom = config.zoom + 2

    map = gis.show_map(
        features = [{"lat"  : lat,
                     "lon"  : lon}],
        lat = lat,
        lon = lon,
        zoom = zoom,
        window = True,
        closable = False,
        collapsed = True
    )

    return dict(map=map)

# -----------------------------------------------------------------------------
def display_features():
    """
        Cut-down version of the Map Viewing Client.
        Used as a link from the RHeader.
            URL generated server-side
        Shows all locations matching a query.
        @ToDo: Most recent location is marked using a bigger Marker.
        @ToDo: Move to S3Method (will then use AAA etc).
    """

    ltable = s3db.gis_location

    # Parse the URL, check for implicit resources, extract the primary record
    # http://127.0.0.1:8000/eden/gis/display_features&module=pr&resource=person&instance=1&jresource=presence
    ok = 0
    if "module" in request.vars:
        res_module = request.vars.module
        ok +=1
    if "resource" in request.vars:
        resource = request.vars.resource
        ok +=1
    if "instance" in request.vars:
        instance = int(request.vars.instance)
        ok +=1
    if "jresource" in request.vars:
        jresource = request.vars.jresource
        ok +=1
    if ok != 4:
        session.error = T("Insufficient vars: Need module, resource, jresource, instance")
        raise HTTP(400, body=s3mgr.xml.json_message(False, 400, session.error))

    tablename = "%s_%s" % (res_module, resource)
    s3mgr.load(tablename)
    table = db[table]
    component, pkey, fkey = s3mgr.model.get_component(table, jresource)
    jtable = db[str(component.table)]
    query = (jtable[fkey] == table[pkey]) & (table.id == instance)
    # Filter out deleted
    deleted = (table.deleted == False)
    query = query & deleted
    # Filter out inaccessible
    query2 = (ltable.id == jtable.location_id)
    accessible = s3_accessible_query("read", ltable)
    query2 = query2 & accessible

    features = db(query).select(ltable.ALL, left = [ltable.on(query2)])

    # Calculate an appropriate BBox
    bounds = gis.get_bounds(features=features)

    map = gis.show_map(
        features = features,
        bbox = bounds,
        window = True,
        closable = False,
        collapsed = True
    )

    return dict(map=map)

# =============================================================================
def geocode():

    """
        Call a Geocoder service

        @param location: a string to search for
        @param service: the service to call (defaults to Google)
    """

    if "location" in request.vars:
        location = request.vars.location
    else:
        session.error = T("Need to specify a location to search for.")
        redirect(URL(f="index"))

    if "service" in request.vars:
        service = request.vars.service
    else:
        # @ToDo: service=all should be default
        service = "google"

    if service == "google":
        return s3base.GoogleGeocoder(location).get_json()

    if service == "yahoo":
        # @ToDo: Convert this to JSON
        return s3base.YahooGeocoder(location).get_xml()

# -----------------------------------------------------------------------------
def geocode_manual():

    """
        Manually Geocode locations

        @ToDo: make this accessible by Anonymous users?
    """

    table = s3db.gis_location

    # Filter
    query = (table.level == None)
    # @ToDo: make this role-dependent
    # - Normal users do the Lat/Lons
    # - Special users do the Codes
    _filter = (table.lat == None)
    response.s3.filter = (query & _filter)

    # Hide unnecessary fields
    table.code.readable = table.code.writable = False # @ToDo: Role-dependent
    table.level.readable = table.level.writable = False
    table.members.readable = table.members.writable = False
    table.gis_feature_type.readable = table.gis_feature_type.writable = False
    table.wkt.readable = table.wkt.writable = False
    table.url.readable = table.url.writable = False
    table.geonames_id.readable = table.geonames_id.writable = False
    table.osm_id.readable = table.osm_id.writable = False
    table.source.readable = table.source.writable = False
    table.comments.readable = table.comments.writable = False

    # Customise Labels for specific use-cases
    #table.name.label = T("Building Name") # Building Assessments-specific
    #table.parent.label = T("Suburb") # Christchurch-specific

    # For Special users doing codes
    #table.code.label = T("Property reference in the council system") # Christchurch-specific 'prupi'
    #table.code2.label = T("Polygon reference of the rating unit") # Christchurch-specific 'gisratingid'

    # Allow prep to pass vars back to the controller
    vars = {}

    # Pre-processor
    def prep(r, vars):
        def get_location_info():
            table = s3db.gis_location
            return db(table.id == r.id).select(table.lat,
                                               table.lon,
                                               table.level,
                                               limitby=(0, 1)).first()

        if r.method in (None, "list") and r.record is None:
            # List
            pass
        elif r.method in ("delete", "search"):
            pass
        else:
            # Add Map to allow locations to be found this way
            # @ToDo: DRY with one in location()
            config = gis.get_config()
            lat = config.lat
            lon = config.lon
            zoom = config.zoom
            feature_queries = []

            if r.method == "create":
                add_feature = True
                add_feature_active = True
            else:
                if r.method == "update":
                    add_feature = True
                    add_feature_active = False
                else:
                    # Read
                    add_feature = False
                    add_feature_active = False

                try:
                    location
                except:
                    location = get_location_info()
                if location and location.lat is not None and location.lon is not None:
                    lat = location.lat
                    lon = location.lon
                # Same as a single zoom on a cluster
                zoom = zoom + 2

            # @ToDo: Does map make sense if the user is updating a group?
            # If not, maybe leave it out. OTOH, might be nice to select
            # admin regions to include in the group by clicking on them in
            # the map. Would involve boundaries...
            _map = gis.show_map(lat = lat,
                                lon = lon,
                                zoom = zoom,
                                feature_queries = feature_queries,
                                add_feature = add_feature,
                                add_feature_active = add_feature_active,
                                toolbar = True,
                                collapsed = True)

            # Pass the map back to the main controller
            vars.update(_map=_map)
        return True
    response.s3.prep = lambda r, vars=vars: prep(r, vars)

    s3mgr.configure(table._tablename,
                    listadd=False,
                    list_fields=["id",
                                 "name",
                                 "address",
                                 "parent"
                                ])

    output = s3_rest_controller("gis", "location")

    _map = vars.get("_map", None)
    if _map and isinstance(output, dict):
        output.update(_map=_map)

    return output

# =============================================================================
def geoexplorer():

    """
        Embedded GeoExplorer: https://github.com/opengeo/GeoExplorer

        This is used as a demo of GXP components which we want to pull into
        the Map Viewing Client.

        No real attempt to integrate/optimise.

        @ToDo: Get working
        If gxp is loaded in debug mode then it barfs Ext:
            ext-all-debug.js (line 10535)
                types[config.xtype || defaultType] is not a constructor
                [Break On This Error] return config.render ? con...config.xtype || defaultType](config);
        In non-debug mode, the suite breaks, but otherwise the UI loads fine & is operational.
        However no tiles are ever visible!
    """

    #config = gis.get_config()

    # Load Models
    s3mgr.load("gis_wmc_layer")

    # @ToDo: Optimise to a single query of table
    #bing_key = gis.get_api_key("bing")
    #google_key = gis.get_api_key("google")
    #yahoo_key = gis.get_api_key("yahoo")

    # http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
    print_service = deployment_settings.get_gis_print_service()

    geoserver_url = deployment_settings.get_gis_geoserver_url()

    response.title = "GeoExplorer"
    return dict(
                #config=config,
                #bing_key=bing_key,
                #google_key=google_key,
                #yahoo_key=yahoo_key,
                print_service=print_service,
                geoserver_url=geoserver_url
               )

# -----------------------------------------------------------------------------
def about():
    """  Custom View for GeoExplorer """
    return dict()

# -----------------------------------------------------------------------------
def maps():

    """
        Map Save/Publish Handler for GeoExplorer

        NB
            The models for this are currently not enabled in 03_gis.py
            This hasn't been tested at all with the new version of GeoExplorer
    """

    table = s3db.gis_wmc
    ltable = s3db.gis_wmc_layer

    if request.env.request_method == "GET":
        # This is a request to read the config of a saved map

        # Which map are we updating?
        id = request.args[0]
        if not id:
            raise HTTP(501)

        # Read the WMC record
        record = db(table.id == id).select(limitby=(0, 1)).first()
        # & linked records
        #projection = db(db.gis_projection.id == record.projection).select(limitby=(0, 1)).first()

        # Put details into the correct structure
        output = dict()
        output["map"] = dict()
        map = output["map"]
        map["center"] = [record.lat, record.lon]
        map["zoom"] = record.zoom
        # @ToDo: Read Projection (we generally use 900913 & no way to edit this yet)
        map["projection"] = "EPSG:900913"
        map["units"] = "m"
        map["maxResolution"] = 156543.0339
        map["maxExtent"] = [ -20037508.34, -20037508.34, 20037508.34, 20037508.34 ]
        # @ToDo: Read Layers
        map["layers"] = []
        #map["layers"].append(dict(source="google", title="Google Terrain", name="TERRAIN", group="background"))
        #map["layers"].append(dict(source="ol", group="background", fixed=True, type="OpenLayers.Layer", args=[ "None", {"visibility":False} ]))
        for _layer in record.layer_id:
            layer = db(ltable.id == _layer).select(limitby=(0, 1)).first()
            if layer.type_ == "OpenLayers.Layer":
                # Add args
                map["layers"].append(dict(source=layer.source,
                                          title=layer.title,
                                          name=layer.name,
                                          group=layer.group_,
                                          type=layer.type_,
                                          format=layer.img_format,
                                          visibility=layer.visibility,
                                          transparent=layer.transparent,
                                          opacity=layer.opacity,
                                          fixed=layer.fixed,
                                          args=[ "None", {"visibility":False} ]))
            else:
                map["layers"].append(dict(source=layer.source,
                                          title=layer.title,
                                          name=layer.name,
                                          group=layer.group_,
                                          type=layer.type_,
                                          format=layer.img_format,
                                          visibility=layer.visibility,
                                          transparent=layer.transparent,
                                          opacity=layer.opacity,
                                          fixed=layer.fixed))

        # @ToDo: Read Metadata (no way of editing this yet)

        # Encode as JSON
        output = json.dumps(output)

        # Output to browser
        response.headers["Content-Type"] = "application/json"
        return output

    elif request.env.request_method == "POST":
        # This is a request to save/publish a new map

        # Get the data from the POST
        source = request.body.read()
        if isinstance(source, basestring):
            import cStringIO
            source = cStringIO.StringIO(source)

        # Decode JSON
        source = json.load(source)
        # @ToDo: Projection (we generally use 900913 & no way to edit this yet)
        lat = source["map"]["center"][0]
        lon = source["map"]["center"][1]
        zoom = source["map"]["zoom"]
        # Layers
        layers = []
        for layer in source["map"]["layers"]:
            try:
                opacity = layer["opacity"]
            except:
                opacity = None
            try:
                name = layer["name"]
            except:
                name = None
            query = (ltable.source == layer["source"]) & \
                    (ltable.name == name) & \
                    (ltable.visibility == layer["visibility"]) & \
                    (ltable.opacity == opacity)
            _layer = db(query).select(ltable.id,
                                      limitby=(0, 1)).first()
            if _layer:
                # This is an existing layer
                layers.append(_layer.id)
            else:
                # This is a new layer
                try:
                    type_ = layer["type"]
                except:
                    type_ = None
                try:
                    group_ = layer["group"]
                except:
                    group_ = None
                try:
                    fixed = layer["fixed"]
                except:
                    fixed = None
                try:
                    format = layer["format"]
                except:
                    format = None
                try:
                    transparent = layer["transparent"]
                except:
                    transparent = None
                # Add a new record to the gis_wmc_layer table
                _layer = ltable.insert(source=layer["source"],
                                       name=name,
                                       visibility=layer["visibility"],
                                       opacity=opacity,
                                       type_=type_,
                                       title=layer["title"],
                                       group_=group_,
                                       fixed=fixed,
                                       transparent=transparent,
                                       img_format=format)
                layers.append(_layer)

        # @ToDo: Metadata (no way of editing this yet)

        # Save a record in the WMC table
        id = table.insert(lat=lat, lon=lon, zoom=zoom, layer_id=layers)

        # Return the ID of the saved record for the Bookmark
        output = json.dumps(dict(id=id))
        return output

    elif request.env.request_method == "PUT":
        # This is a request to save/publish an existing map

        # Which map are we updating?
        id = request.args[0]
        if not id:
            raise HTTP(501)

        # Get the data from the PUT
        source = request.body.read()
        if isinstance(source, basestring):
            import cStringIO
            source = cStringIO.StringIO(source)

        # Decode JSON
        source = json.load(source)
        # @ToDo: Projection (unlikely to change)
        lat = source["map"]["center"][0]
        lon = source["map"]["center"][1]
        zoom = source["map"]["zoom"]
        # Layers
        layers = []
        for layer in source["map"]["layers"]:
            try:
                opacity = layer["opacity"]
            except:
                opacity = None
            try:
                name = layer["name"]
            except:
                name = None
            query = (ltable.source == layer["source"]) & \
                    (ltable.name == name) & \
                    (ltable.visibility == layer["visibility"]) & \
                    (ltable.opacity == opacity)
            _layer = db(query).select(ltable.id,
                                      limitby=(0, 1)).first()
            if _layer:
                # This is an existing layer
                layers.append(_layer.id)
            else:
                # This is a new layer
                try:
                    type_ = layer["type"]
                except:
                    type_ = None
                try:
                    group_ = layer["group"]
                except:
                    group_ = None
                try:
                    fixed = layer["fixed"]
                except:
                    fixed = None
                try:
                    format = layer["format"]
                except:
                    format = None
                try:
                    transparent = layer["transparent"]
                except:
                    transparent = None
                # Add a new record to the gis_wmc_layer table
                _layer = ltable.insert(source=layer["source"],
                                       name=name,
                                       visibility=layer["visibility"],
                                       opacity=opacity,
                                       type_=type_,
                                       title=layer["title"],
                                       group_=group_,
                                       fixed=fixed,
                                       transparent=transparent,
                                       img_format=format)
                layers.append(_layer)

        # @ToDo: Metadata (no way of editing this yet)

        # Update the record in the WMC table
        db(table.id == id).update(lat=lat, lon=lon, zoom=zoom, layer_id=layers)

        # Return the ID of the saved record for the Bookmark
        output = json.dumps(dict(id=id))
        return output

    # Abort - we shouldn't get here
    raise HTTP(501)

# =============================================================================
def potlatch2():
    """
        Custom View for the Potlatch2 OpenStreetMap editor
        http://wiki.openstreetmap.org/wiki/Potlatch_2
    """

    config = gis.get_config()
    osm_oauth_consumer_key = config.osm_oauth_consumer_key
    osm_oauth_consumer_secret = config.osm_oauth_consumer_secret
    if osm_oauth_consumer_key and osm_oauth_consumer_secret:
        gpx_url = None
        if "gpx_id" in request.vars:
            # Pass in a GPX Track
            # @ToDo: Set the viewport based on the Track, if one is specified
            table = s3db.gis_layer_track
            query = (table.id == request.vars.gpx_id)
            track = db(query).select(table.track,
                                     limitby=(0, 1)).first()
            if track:
                gpx_url = "%s/%s" % (URL(c="default", f="download"),
                                     track.track)

        if "lat" in request.vars:
            lat = request.vars.lat
            lon = request.vars.lon
        else:
            lat = config.lat
            lon = config.lon

        if "zoom" in request.vars:
            zoom = request.vars.zoom
        else:
            # This isn't good as it makes for too large an area to edit
            #zoom = config.zoom
            zoom = 14

        site_name = deployment_settings.get_system_name_short()

        return dict(lat=lat, lon=lon, zoom=zoom,
                    gpx_url=gpx_url,
                    site_name=site_name,
                    key=osm_oauth_consumer_key,
                    secret=osm_oauth_consumer_secret)

    else:
        session.warning = T("To edit OpenStreetMap, you need to edit the OpenStreetMap settings in your Map Config")
        redirect(URL(c="pr", f="person",
                     args=["config"],
                     vars={"person.uid":auth.user.person_uuid}))

# =============================================================================
def proxy():
    """
    Based on http://trac.openlayers.org/browser/trunk/openlayers/examples/proxy.cgi
    This is a blind proxy that we use to get around browser
    restrictions that prevent the Javascript from loading pages not on the
    same server as the Javascript. This has several problems: it's less
    efficient, it might break some sites, and it's a security risk because
    people can use this proxy to browse the web and possibly do bad stuff
    with it. It only loads pages via http and https, but it can load any
    content type. It supports GET and POST requests.
    """

    import socket
    import urllib2
    import cgi

    # @ToDo: Link to map_service_catalogue to prevent Open Proxy abuse
    # (although less-critical since we restrict content type)
    allowedHosts = []
    #allowedHosts = ["www.openlayers.org", "demo.opengeo.org"]

    allowed_content_types = (
        "application/json", "text/json", "text/x-json",
        "application/xml", "text/xml",
        "application/vnd.ogc.se_xml",           # OGC Service Exception
        "application/vnd.ogc.se+xml",           # OGC Service Exception
        "application/vnd.ogc.success+xml",      # OGC Success (SLD Put)
        "application/vnd.ogc.wms_xml",          # WMS Capabilities
        "application/vnd.ogc.context+xml",      # WMC
        "application/vnd.ogc.gml",              # GML
        "application/vnd.ogc.sld+xml",          # SLD
        "application/vnd.google-earth.kml+xml", # KML
    )

    method = request["wsgi"].environ["REQUEST_METHOD"]

    if method == "POST":
        # This can probably use same call as GET in web2py
        qs = request["wsgi"].environ["QUERY_STRING"]

        d = cgi.parse_qs(qs)
        if d.has_key("url"):
            url = d["url"][0]
        else:
            url = "http://www.openlayers.org"
    else:
        # GET
        if "url" in request.vars:
            url = request.vars.url
        else:
            session.error = T("Need a 'url' argument!")
            raise HTTP(400, body=s3mgr.xml.json_message(False, 400, session.error))

    # Debian has no default timeout so connection can get stuck with dodgy servers
    socket.setdefaulttimeout(30)
    try:
        host = url.split("/")[2]
        if allowedHosts and not host in allowedHosts:
            raise(HTTP(403, "Host not permitted: %s" % host))

        elif url.startswith("http://") or url.startswith("https://"):
            if method == "POST":
                length = int(request["wsgi"].environ["CONTENT_LENGTH"])
                headers = {"Content-Type": request["wsgi"].environ["CONTENT_TYPE"]}
                body = request.body.read(length)
                r = urllib2.Request(url, body, headers)
                y = urllib2.urlopen(r)
            else:
                # GET
                y = urllib2.urlopen(url)

            # Check for allowed content types
            i = y.info()
            if i.has_key("Content-Type"):
                ct = i["Content-Type"]
                if not ct.split(";")[0] in allowed_content_types:
                    # @ToDo?: Allow any content type from allowed hosts (any port)
                    #if allowedHosts and not host in allowedHosts:
                    raise(HTTP(403, "Content-Type not permitted"))
            else:
                raise(HTTP(406, "Unknown Content"))

            msg = y.read()
            y.close()

            # Maintain the incoming Content-Type
            response.headers["Content-Type"] = ct
            return msg

        else:
            # Bad Request
            raise(HTTP(400))

    except Exception, E:
        raise(HTTP(500, "Some unexpected error occurred. Error text was: %s" % str(E)))

# END =========================================================================

