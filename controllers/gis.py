# -*- coding: utf-8 -*-

"""
    GIS Controllers
"""

module = request.controller
resourcename = request.function

# -----------------------------------------------------------------------------
def index():
    """
       Module's Home Page
    """

    module_name = settings.modules[module].name_nice
    response.title = module_name

    # Read user request
    vars = request.get_vars
    height = vars.get("height", None)
    width = vars.get("width", None)
    iframe = vars.get("iframe", False)
    toolbar = vars.get("toolbar", True)
    collapsed = vars.get("collapsed", False)

    if collapsed:
        collapsed = True

    if toolbar == "0":
        toolbar = False
    else:
        toolbar = True

    if iframe:
        response.view = "gis/iframe.html"
    else:
        # Code to go fullscreen
        # IE (even 9) doesn't like the dynamic full-screen, so simply do a page refresh for now
        # Remove components from embedded Map's containers without destroying their contents
        # Add a full-screen window which will inherit these components
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.gis.fullscreen.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.gis.fullscreen.min.js" % appname
        s3.scripts.append(script)

    # Include an embedded Map on the index page
    map = define_map(height=height,
                     width=width,
                     window=False,
                     toolbar=toolbar,
                     collapsed=collapsed,
                     closable=False,
                     maximizable=False)

    return dict(map=map,
                title = T("Map"))

# =============================================================================
def map_viewing_client():
    """
        Map Viewing Client.
        UI for a user to view the overall Maps with associated Features
    """

    map = define_map(window=True,
                     toolbar=True,
                     closable=False,
                     maximizable=False)

    response.title = T("Map Viewing Client")
    return dict(map=map)

# -----------------------------------------------------------------------------
def define_map(height = None,
               width = None,
               window = False,
               toolbar = False,
               closable = True,
               collapsed = False,
               maximizable = True,
               config = None):
    """
        Define the main Situation Map
        This can then be called from both the Index page (embedded)
        & the Map_Viewing_Client (fullscreen)
    """

    if not config:
        config = gis.get_config()

    # @ToDo: Make these configurable
    search = True
    legend = True
    #googleEarth = True
    #googleStreetview = True
    catalogue_layers = True

    if config.wmsbrowser_url:
        wms_browser = {"name" : config.wmsbrowser_name,
                       "url" : config.wmsbrowser_url}
    else:
        wms_browser = None

    # http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
    print_service = settings.get_gis_print_service()
    if print_service:
        print_tool = {"url": print_service}
    else:
        print_tool = {}

    map = gis.show_map(height=height,
                       width=width,
                       window=window,
                       wms_browser = wms_browser,
                       toolbar=toolbar,
                       collapsed=collapsed,
                       closable=closable,
                       maximizable=maximizable,
                       legend=legend,
                       search=search,
                       catalogue_layers=catalogue_layers,
                       print_tool = print_tool,
                       )

    return map

# =============================================================================
def location():
    """ RESTful CRUD controller for Locations """

    tablename = "gis_location"
    table = s3db[tablename]

    # Custom Methods
    set_method = s3db.set_method
    from s3.s3gis import S3ExportPOI
    set_method("gis", "location",
               method="export_poi",
               action=S3ExportPOI())
    from s3.s3gis import S3ImportPOI
    set_method("gis", "location",
               method="import_poi",
               action=S3ImportPOI())
    set_method("gis", "location",
               method="parents",
               action=s3_gis_location_parents)
    
    if "report" in request.args:
        # @ToDo: Migrate to Field.Lazy
        class S3LocationVirtualFields:
            def population(self):
                """
                    Used by the Report
                """
                table = current.s3db.gis_location_tag
                query = (table.location_id == self.gis_location.id) & \
                        (table.tag == "population")
                location = current.db(query).select(table.value,
                                                    limitby=(0, 1)).first()
                if location:
                    return int(location.value)
                else:
                    return None

        table.virtualfields.append(S3LocationVirtualFields())

        s3db.configure(tablename,
                       report_options=Storage(
                                search=gis_location_adv_search,
                                rows=["name"],
                                cols=[],
                                fact=[("population", "sum", T("Total Population"))],
                                defaults=Storage(
                                                rows="name",
                                                cols=None,
                                                fact="sum:population",
                                                totals=True
                                                )
                                ),
                        )

    s3db.configure(tablename,
                   # Don't include Bulky Location Selector in List Views
                   listadd=False,
                   )

    # Pre-processor
    # Allow prep to pass vars back to the controller
    vars = {}
    def prep(r, vars):

        if r.interactive and not r.component:
            location_hierarchy = gis.get_location_hierarchy()
            from s3.s3filter import S3TextFilter, S3OptionsFilter#, S3LocationFilter
            filter_widgets = [
                S3TextFilter(["name",
                              "comments",
                              "L0",
                              "L1",
                              "L2",
                              "L3",
                              "L4",
                              "L5",
                              "tag.value",
                              ],
                             label = T("Search"),
                             comment = T("To search for a location, enter the name. You may use % as wildcard. Press 'Search' without input to list all locations."),
                             _class = "filter-search",
                             ),
                S3OptionsFilter("level",
                                label=T("Level"),
                                cols=3,
                                options=location_hierarchy,
                                hidden=True,
                                ),
                # @ToDo: Hierarchical filter working on id
                #S3LocationFilter("id",
                #                 label=T("Location"),
                #                 levels=["L0", "L1", "L2", "L3", "L4", "L5"],
                #                 widget="multiselect",
                #                 cols=3,
                #                 hidden=True,
                #                 ),
                S3OptionsFilter("L0",
                                label=COUNTRY,
                                #widget="multiselect",
                                cols=5,
                                hidden=True,
                                ),
                S3OptionsFilter("L1",
                                label=location_hierarchy["L1"],
                                #widget="multiselect",
                                cols=5,
                                hidden=True,
                                ),
                S3OptionsFilter("L2",
                                label=location_hierarchy["L2"],
                                #widget="multiselect",
                                cols=5,
                                hidden=True,
                                ),
                S3OptionsFilter("L3",
                                label=location_hierarchy["L3"],
                                #widget="multiselect",
                                cols=5,
                                hidden=True,
                                ),
                ]

            s3db.configure(tablename,
                           filter_widgets=filter_widgets,
                           )

            # Restrict access to Polygons to just MapAdmins
            if settings.get_security_map() and not s3_has_role(MAP_ADMIN):
                table.gis_feature_type.writable = table.gis_feature_type.readable = False
                table.wkt.writable = table.wkt.readable = False
            else:
                table.wkt.comment = DIV(_class="stickytip",
                                        _title="WKT|%s %s%s %s%s" % (T("The"),
                                                                   "<a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>",
                                                                   T("Well-Known Text"),
                                                                   "</a>",
                                                                   T("representation of the Polygon/Line.")))

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
                table.parent.comment = DIV(S3AddResourceLink(c="gis",
                                                             f="location",
                                                             vars=dict(child="parent")),
                                           parent_comment)

            table.inherited.comment = DIV(_class="tooltip",
                                          _title="%s|%s" % (table.inherited.label,
                                                            T("Whether the Latitude & Longitude are inherited from a higher level in the location hierarchy rather than being a separately-entered figure.")))

            table.comments.comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Comments"),
                                                           T("Please use this field to record any additional information, such as Ushahidi instance IDs. Include a history of the record if it is updated.")))

            if r.method in (None, "list") and r.record is None:
                # List
                pass
            elif r.method in ("delete", "search", "profile"):
                pass
            else:
                if r.method == "report":
                    s3.filter = (table.level !=None)
                # Add Map to allow locations to be found this way
                config = gis.get_config()
                lat = config.lat
                lon = config.lon
                zoom = config.zoom
                feature_queries = []

                if r.method == "create":
                    s3.scripts.append("/%s/static/scripts/S3/s3.gis.feature_crud.js" % appname)
                    add_feature = True
                    add_feature_active = True
                    table.inherited.readable = False
                else:
                    if r.method == "update":
                        s3.scripts.append("/%s/static/scripts/S3/s3.gis.feature_crud.js" % appname)
                        add_feature = True
                        add_feature_active = False
                    else:
                        # Read
                        add_feature = False
                        add_feature_active = False

                    record = r.record
                    if record and record.lat is not None and record.lon is not None:
                        lat = record.lat
                        lon = record.lon
                    # Same as a single zoom on a cluster
                    zoom = zoom + 2

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
    s3.prep = lambda r, vars=vars: prep(r, vars)

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
        s3.filter = reduce(__and__, filters)

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

    level = _vars.get("level", None)
    if level:
        # We've been called from the Location Selector widget
        table.addr_street.readable = table.addr_street.writable = False

    country = S3ReusableField("country", "string", length=2,
                              label = COUNTRY,
                              requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                    lambda: gis.get_countries(key_type="code"),
                                    zero = SELECT_LOCATION)),
                              represent = lambda code: \
                                    gis.get_country(code, key_type="code") or UNKNOWN_OPT)

    output = s3_rest_controller(rheader=s3db.gis_rheader,
                                hide_filter = False,
                                # CSV column headers, so no T()
                                csv_extra_fields = [
                                    dict(label="Country",
                                         field=country())
                                ])

    _map = vars.get("_map", None)
    if _map and isinstance(output, dict):
        output["_map"] = _map

    return output

# -----------------------------------------------------------------------------
def ldata():
    """
        Return JSON of location hierarchy suitable for use by S3LocationSelectorWidget2
        '/eden/gis/ldata/' + id

        n = {id : {'n' : name,
                   'l' : level,
                   'f' : parent,
                   'b' : [lon_min, lat_min, lon_max, lat_max]
                   }}
    """

    args = request.args
    args_len = len(args)

    if args_len == 0:
        raise HTTP(400)

    id = args[0]

    table = s3db.gis_location
    query = (table.deleted == False) & \
            ((table.parent == id) | \
             (table.id == id))
    locations = db(query).select(table.id,
                                 table.name,
                                 table.level,
                                 table.parent,
                                 table.lon_min,
                                 table.lat_min,
                                 table.lon_max,
                                 table.lat_max,
                                 )
    try:
        id_level = int(locations.as_dict()[int(id)]["level"][1:])
    except:
        return ""
    output_level = id_level + 1
    search_level = "L%s" % output_level
    location_dict = {}
    for location in locations:
        if location.level == search_level:
            if location.lon_min is not None:
                location_dict[int(location.id)] = dict(n=location.name,
                                                       l=output_level,
                                                       f=int(location.parent),
                                                       b=[location.lon_min,
                                                          location.lat_min,
                                                          location.lon_max,
                                                          location.lat_max
                                                          ],
                                                       )
            else:
                location_dict[int(location.id)] = dict(n=location.name,
                                                       l=output_level,
                                                       f=int(location.parent),
                                                       )

    script = '''n=%s\n''' % json.dumps(location_dict)
    response.headers["Content-Type"] = "application/json"
    return script

# -----------------------------------------------------------------------------
def s3_gis_location_parents(r, **attr):
    """
        Custom S3Method

        Return a list of Parents for a Location
    """

    table = r.resource.table

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
        item = current.xml.json_message(False, 400, "Need to specify a record ID!")
        raise HTTP(400, body=item)

    table = s3db.gis_location
    ttable = s3db.gis_location_tag
    query = (table.id == record_id) & \
            (table.deleted == False) & \
            (table.level == "L0") & \
            (ttable.tag == "ISO2") & \
            (ttable.location_id == table.id)
    record = db(query).select(table.id,
                              table.name,
                              # Code for the Geocoder lookup filter
                              ttable.value,
                              # LatLon for Centering the Map
                              table.lon,
                              table.lat,
                              # Bounds for Zooming the Map
                              table.lon_min,
                              table.lon_max,
                              table.lat_min,
                              table.lat_max,
                              cache = s3db.cache,
                              limitby=(0, 1)).first()
    if not record:
        item = current.xml.json_message(False, 400, "Invalid ID!")
        raise HTTP(400, body=item)

    result = record.as_dict()
    location_part = result["gis_location"]
    for key in location_part:
        result[key] = location_part[key]
    del result["gis_location"]
    result["code"] = result["gis_location_tag"]["value"]
    del result["gis_location_tag"]

    # Provide the Location Hierarchy for this country
    location_hierarchy = gis.get_location_hierarchy(location=record_id)
    for key in location_hierarchy:
        result[key] = location_hierarchy[key]

    output = json.dumps(result)
    response.headers["Content-Type"] = "application/json"
    return output

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
def catalog():
    """ Custom View to link to different Layers """
    return dict()

# -----------------------------------------------------------------------------
def config():
    """ RESTful CRUD controller """

    # Custom Methods to enable/disable layers
    set_method = s3db.set_method
    set_method(module, resourcename,
               component_name="layer_entity",
               method="enable",
               action=enable_layer)
    set_method(module, resourcename,
               component_name="layer_entity",
               method="disable",
               action=disable_layer)

    # Pre-process
    def prep(r):
        if r.interactive:
            if not r.component:
                s3db.gis_config_form_setup()
                if auth.is_logged_in() and not auth.s3_has_role(MAP_ADMIN):
                    # Only Personal Config is accessible
                    # @ToDo: ideal would be to have the SITE_DEFAULT (with any OU configs overlaid) on the left-hand side & then they can see what they wish to override on the right-hand side
                    # - could be easier to put the currently-effective config into the form fields, however then we have to save all this data
                    # - if each field was readable & you clicked on it to make it editable (like RHoK pr_contact), that would solve this
                    pe_id = auth.user.pe_id
                    # For Lists
                    s3.filter = (s3db.gis_config.pe_id == pe_id)
                    # For Create forms
                    field = r.table.pe_id
                    field.default = pe_id
                    field.readable = False
                    field.writable = False
            elif r.component_name == "layer_entity":
                s3.crud_strings["gis_layer_config"] = Storage(
                    title_create = T("Add Layer to this Profile"),
                    title_display = LAYER_DETAILS,
                    title_list = LAYERS,
                    title_update = EDIT_LAYER,
                    subtitle_create = T("Add Layer from Catalog"),
                    label_list_button = T("List Layers in Profile"),
                    label_create_button = T("Add Layer from Catalog"),
                    label_delete_button = T("Remove Layer from Profile"),
                    msg_record_created = LAYER_ADDED,
                    msg_record_modified = LAYER_UPDATED,
                    msg_list_empty = T("No Layers currently configured in this Profile"),
                )
                table =  s3db.gis_layer_entity
                ltable = s3db.gis_layer_config
                if r.method == "update":
                    # Existing records don't need to change the layer pointed to (confusing UI & adds validation overheads)
                    ltable.layer_id.writable = False
                    # Hide irrelevant fields
                    query = (table.layer_id == r.component_id)
                    type = db(query).select(table.instance_type,
                                            limitby=(0, 1)).first().instance_type
                    if type in ("gis_layer_coordinate",
                                "gis_layer_georss",
                                "gis_layer_gpx",
                                "gis_layer_mgrs",
                                "gis_layer_openweathermap",
                                ):
                        ltable.base.readable = ltable.base.writable = False
                    elif type in ("gis_layer_bing",
                                  "gis_layer_google",
                                  "gis_layer_tms",
                                  ):
                        ltable.visible.readable = ltable.visible.writable = False
                    elif type in ("gis_layer_feature"
                                  "gis_layer_geojson",
                                  "gis_layer_kml",
                                  "gis_layer_shapefile",
                                  "gis_layer_theme",
                                  "gis_layer_wfs",
                                  ):
                        ltable.base.readable = ltable.base.writable = False
                        ltable.style.readable = ltable.style.writable = True
                else:
                    # Only show Layers not yet in this config
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (ltable.config_id == r.id)
                    rows = db(query).select(table.layer_id)
                    # Filter them out
                    ltable.layer_id.requires = IS_ONE_OF(db, "gis_layer_entity.layer_id",
                                                         s3db.gis_layer_represent,
                                                         not_filterby="layer_id",
                                                         not_filter_opts=[row.layer_id for row in rows]
                                                         )

        elif r.representation == "url":
            # Save from Map
            if r.method == "create" and \
                 auth.is_logged_in() and \
                 not auth.s3_has_role(MAP_ADMIN):
                pe_id = auth.user.pe_id
                r.table.pe_id.default = pe_id
                r.table.pe_type.default = 1

        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive:
            if r.component_name == "layer_entity":
                s3_action_buttons(r, deletable=False)
                ltable = s3db.gis_layer_config
                query = (ltable.config_id == r.id)
                rows = db(query).select(ltable.layer_id,
                                        ltable.enabled)
                # Show the enable button if the layer is not currently enabled
                restrict = [str(row.layer_id) for row in rows if not row.enabled]
                s3.actions.append(dict(label=str(T("Enable")),
                                                _class="action-btn",
                                                url=URL(args=[r.id, "layer_entity", "[id]", "enable"]),
                                                restrict = restrict
                                                )
                                            )
                # Show the disable button if the layer is not currently disabled
                restrict = [str(row.layer_id) for row in rows if row.enabled]
                s3.actions.append(dict(label=str(T("Disable")),
                                                _class="action-btn",
                                                url=URL(args=[r.id, "layer_entity", "[id]", "disable"]),
                                                restrict = restrict
                                                )
                                            )
        elif r.representation == "url":
            # Save from Map
            result = json.loads(output["item"])
            if result["status"] == "success":
                # Process Layers
                ltable = s3db.gis_layer_config
                id = r.id
                layers = json.loads(request.post_vars.layers)
                form = Storage()
                for layer in layers:
                    if "id" in layer and layer["id"] != "search_results":
                        layer_id = layer["id"]
                        vars = Storage(
                                config_id = id,
                                layer_id = layer_id,
                            )
                        if "base" in layer:
                            vars.base = layer["base"]
                        if "visible" in layer:
                            vars.visible = layer["visible"]
                        else:
                            vars.visible = False
                        if "style" in layer:
                            vars.style = json.dumps(layer["style"])
                        # Update or Insert?
                        query = (ltable.config_id == id) & \
                                (ltable.layer_id == layer_id)
                        record = db(query).select(ltable.id,
                                                  limitby=(0, 1)).first()
                        if record:
                            vars.id = record.id
                        else:
                            vars.id = ltable.insert(**vars)
                        # Ensure that Default Base processing happens properly
                        form.vars = vars
                        s3db.gis_layer_config_onaccept(form)

        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)
    return output

# -----------------------------------------------------------------------------
def enable_layer(r, **attr):
    """
        Enable a Layer
            designed to be a custom method called by an action button
    """

    if r.component_name != "layer_entity":
        session.error = T("Incorrect parameters")
        redirect(URL(args=[r.id, "layer_entity"]))

    ltable = s3db.gis_layer_config
    query = (ltable.config_id == r.id) & \
            (ltable.layer_id == r.component_id)
    db(query).update(enabled = True)
    session.confirmation = T("Layer has been Enabled")
    redirect(URL(args=[r.id, "layer_entity"]))

# -----------------------------------------------------------------------------
def disable_layer(r, **attr):
    """
        Disable a Layer
            designed to be a custom method called by an action button in config/layer_entity
    """

    if r.component_name != "layer_entity":
        session.error = T("Incorrect parameters")
        redirect(URL(args=[r.id, "layer_entity"]))

    ltable = s3db.gis_layer_config
    query = (ltable.config_id == r.id) & \
            (ltable.layer_id == r.component_id)
    db(query).update(enabled = False)
    session.confirmation = T("Layer has been Disabled")
    redirect(URL(args=[r.id, "layer_entity"]))

# -----------------------------------------------------------------------------
def hierarchy():
    """ RESTful CRUD controller """

    s3db.gis_hierarchy_form_setup()

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def menu():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def symbology():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "layer_entity":
                s3.crud_strings["gis_layer_entity"] = Storage(
                    title_create=T("Configure Layer for this Symbology"),
                    title_display=LAYER_DETAILS,
                    title_list=LAYERS,
                    title_update=EDIT_LAYER,
                    subtitle_create=T("Add New Layer to Symbology"),
                    label_list_button=T("List Layers in Symbology"),
                    label_create_button=ADD_LAYER,
                    label_delete_button = T("Remove Layer from Symbology"),
                    msg_record_created=LAYER_ADDED,
                    msg_record_modified=LAYER_UPDATED,
                    msg_record_deleted=T("Layer removed from Symbology"),
                    msg_list_empty=T("No Layers currently defined in this Symbology"))
                if r.method != "update":
                    # Only show Layers not yet in this symbology
                    table =  s3db.gis_layer_entity
                    ltable = s3db.gis_layer_symbology
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (ltable.symbology_id == r.id)
                    rows = db(query).select(table.layer_id)
                    # Filter them out
                    # Restrict Layers to those which have Markers
                    ltable.layer_id.requires = IS_ONE_OF(db, "gis_layer_entity.layer_id",
                                                         s3db.gis_layer_represent,
                                                         filterby="instance_type",
                                                         filter_opts=("gis_layer_feature",
                                                                      "gis_layer_georss",
                                                                      "gis_layer_geojson",
                                                                      "gis_layer_kml",
                                                                      # @ToDo:
                                                                      #"gis_layer_openweathermap",
                                                                      ),
                                                         not_filterby="layer_id",
                                                         not_filter_opts=[row.layer_id for row in rows]
                                                         )

        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=s3db.gis_rheader)
    return output

# -----------------------------------------------------------------------------
def marker():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.method == "create":
                table = r.table
                table.height.readable = False
                table.width.readable = False
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=s3db.gis_rheader)

# -----------------------------------------------------------------------------
def projection():
    """ RESTful CRUD controller """

    if settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    return s3_rest_controller()

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

    return s3_rest_controller()

# =============================================================================
def inject_enable(output):
    """
        Inject an 'Enable in Default Config?' checkbox into the form
    """

    if "form" in output:
        id  = "layer_enable"
        label  = LABEL("%s:" % T("Enable in Default Config?"),
                       _for="enable")
        widget = INPUT(_name="enable",
                       _type="checkbox",
                       _value="on",
                       _id="layer_enable",
                      _class="boolean")
        comment = ""
        if s3_formstyle == "bootstrap":
            _controls = DIV(widget, comment, _class="controls")
            row = DIV(label,
                      _controls,
                      _class="control-group",
                      _id="%s__row" % id
                      )
        elif callable(s3_formstyle):
            row = s3_formstyle(id=id,
                               label=label,
                               widget=widget,
                               comment=comment)
        else:
            # Unsupported
            raise

        output["form"][0][-2].append(row)

# -----------------------------------------------------------------------------
def layer_config():
    """ RESTful CRUD controller """

    if settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    layer = request.get_vars.get("layer", None)
    if layer:
        csv_stylesheet = "layer_%s.xsl" % layer
    else:
        # Cannot import without a specific layer type
        csv_stylesheet = None

    output = s3_rest_controller(csv_stylesheet=csv_stylesheet)
    return output

# -----------------------------------------------------------------------------
def layer_entity():
    """ RESTful CRUD controller """

    if settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="disable",
                    action=disable_layer)

    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                # Hide irrelevant fields
                type = r.record.instance_type
                if type in ("gis_layer_coordinate",
                            "gis_layer_feature",
                            "gis_layer_geojson",
                            "gis_layer_georss",
                            "gis_layer_gpx",
                            "gis_layer_kml",
                            "gis_layer_mgrs",
                            "gis_layer_wfs",
                            ):
                    ltable.base.writable = ltable.base.readable = False
                elif type in ("gis_layer_empty",
                              "gis_layer_bing",
                              "gis_layer_google",
                              "gis_layer_tms",
                              ):
                    ltable.visible.writable = table.visible.readable = False
                if r.method =="update":
                    # Existing records don't need to change the config pointed to (confusing UI & adds validation overheads)
                    ltable.config_id.writable = False
                else:
                    # Only show Symbologies not yet defined for this Layer
                    table =  s3db.gis_config
                    # Find the records which are used
                    query = (ltable.config_id == table.id) & \
                            (ltable.layer_id == r.id)
                    rows = db(query).select(table.id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="id",
                                                          not_filter_opts=[row.id for row in rows]
                                                          )

            elif r.component_name == "symbology":
                ltable = s3db.gis_layer_symbology
                # Hide irrelevant fields
                type = r.record.instance_type
                if type != "gis_layer_feature":
                    ltable.gps_marker.writable = ltable.gps_marker.readable = False
                if r.method =="update":
                    # Existing records don't need to change the symbology pointed to (confusing UI & adds validation overheads)
                    ltable.symbology_id.writable = False
                else:
                    # Only show Symbologies not yet defined for this Layer
                    table =  s3db.gis_symbology
                    # Find the records which are used
                    query = (ltable.symbology_id == table.id) & \
                            (ltable.layer_id == r.id)
                    rows = db(query).select(table.id)
                    # Filter them out
                    ltable.symbology_id.requires = IS_ONE_OF(db, "gis_symbology.id",
                                                             "%(name)s",
                                                             not_filterby="id",
                                                             not_filter_opts=[row.id for row in rows]
                                                             )
        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=s3db.gis_rheader)
    return output

# -----------------------------------------------------------------------------
def layer_feature():
    """ RESTful CRUD controller """

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="disable",
                    action=disable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                ltable.style.readable = ltable.style.writable = True
                # @ToDo: Move style to layer_config
                #ltable.style.writable = ltable.style.readable = True
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
            elif r.component_name == "symbology" and r.method != "update":
                # Only show ones with no definition yet for this Layer
                table = r.table
                ltable = s3db.gis_layer_symbology
                # Find the records which are used
                query = (ltable.layer_id == table.layer_id) & \
                        (table.id == r.id)
                rows = db(query).select(ltable.symbology_id)
                # Filter them out
                ltable.symbology_id.requires = IS_ONE_OF(db, "gis_symbology.id",
                                                         "%(name)s",
                                                         not_filterby="id",
                                                         not_filter_opts=[row.symbology_id for row in rows]
                                                         )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)
    return output

# -----------------------------------------------------------------------------
def layer_openstreetmap():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )

        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_bing():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

    # CRUD Strings
    type = "Bing"
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_update=EDIT_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED)

    s3db.configure(tablename,
                    deletable=False,
                    listadd=False)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.visible.writable = table.visible.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )

        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_empty():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

    # CRUD Strings
    type = "Empty"
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_update=EDIT_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED)

    s3db.configure(tablename,
                    deletable=False,
                    listadd=False)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.visible.writable = table.visible.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )

        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_google():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

    # CRUD Strings
    type = "Google"
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_update=EDIT_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED)

    s3db.configure(tablename,
                    deletable=False,
                    listadd=False)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.visible.writable = table.visible.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_mgrs():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    s3db.configure(tablename, deletable=False, listadd=False)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_arcrest():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

    # CRUD Strings
    type = "ArcGIS REST"
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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="enable",
                    action=enable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_geojson():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                ltable.style.readable = ltable.style.writable = True
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
            elif r.component_name == "symbology":
                ltable = s3db.gis_layer_symbology
                ltable.gps_marker.writable = ltable.gps_marker.readable = False
                if r.method != "update":
                    # Only show ones with no definition yet for this Layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.symbology_id)
                    # Filter them out
                    ltable.symbology_id.requires = IS_ONE_OF(db, "gis_symbology.id",
                                                             "%(name)s",
                                                             not_filterby="id",
                                                             not_filter_opts=[row.symbology_id for row in rows]
                                                             )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_georss():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="enable",
                    action=enable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
            elif r.component_name == "symbology":
                ltable = s3db.gis_layer_symbology
                ltable.gps_marker.writable = ltable.gps_marker.readable = False
                if r.method != "update":
                    # Only show ones with no definition yet for this Layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.symbology_id)
                    # Filter them out
                    ltable.symbology_id.requires = IS_ONE_OF(db, "gis_symbology.id",
                                                             "%(name)s",
                                                             not_filterby="id",
                                                             not_filter_opts=[row.symbology_id for row in rows]
                                                             )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_gpx():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_kml():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    #s3db.set_method(module, resourcename,
    #                method="enable",
    #                action=enable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                ltable.style.readable = ltable.style.writable = True
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
            elif r.component_name == "symbology":
                ltable = s3db.gis_layer_symbology
                #ltable.gps_marker.readable = ltable.gps_marker.writable = False
                if r.method != "update":
                    # Only show ones with no definition yet for this Layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.symbology_id)
                    # Filter them out
                    ltable.symbology_id.requires = IS_ONE_OF(db, "gis_symbology.id",
                                                             "%(name)s",
                                                             not_filterby="id",
                                                             not_filter_opts=[row.symbology_id for row in rows]
                                                             )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_openweathermap():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

    # CRUD Strings
    type = "OpenWeatherMap"
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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="enable",
                    action=enable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
            elif r.component_name == "symbology":
                ltable = s3db.gis_layer_symbology
                ltable.gps_marker.readable = ltable.gps_marker.writable = False
                if r.method != "update":
                    # Only show ones with no definition yet for this Layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.symbology_id)
                    # Filter them out
                    ltable.symbology_id.requires = IS_ONE_OF(db, "gis_symbology.id",
                                                             "%(name)s",
                                                             not_filterby="id",
                                                             not_filter_opts=[row.symbology_id for row in rows]
                                                             )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)
    return output

# -----------------------------------------------------------------------------
def layer_shapefile():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # CRUD Strings
    type = "Shapefile"
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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="enable",
                    action=enable_layer)

    args = request.args
    if len(args) > 1:
        test = args[1]
        if test[:4] == "data":
            # This must be a request for the data held within a layer
            # Define the Table
            id = args[0]
            _tablename = "gis_layer_shapefile_%s" % id
            Fields = [Field("lat", "float"),
                      Field("lon", "float"),
                      Field("wkt", "text"),
                      Field("layer_id", table),
                      ]
            append = Fields.append
            row = db(table.id == id).select(table.data,
                                            limitby=(0, 1)
                                            ).first()
            fields = json.loads(row.data)
            for field in fields:
                # Unicode fieldnames not supported
                append(Field(str(field[0]), field[1]))
            if settings.get_gis_spatialdb():
                # Add a spatial field
                append(Field("the_geom", "geometry()"))
            s3db.define_table(_tablename, *Fields)
            new_arg = _tablename[4:]
            extension = test[4:]
            if extension:
                new_arg = "%s%s" % (new_arg, extension)
            args[1] = new_arg
            s3db.add_component(_tablename,
                               gis_layer_shapefile="layer_id")
            # @ToDo: onaccept to write any modified data back to the attached shapefile
            # If we need to reproject, then we need to write a .prj file out:
            #outSpatialRef.MorphToESRI()
            #file = open(outfilepath + '\\'+ outfileshortname + '.prj', 'w')
            #file.write(outSpatialRef.ExportToWkt())
            #file.close()

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                ltable.style.writable = ltable.style.readable = True
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
            elif r.component_name == "symbology":
                # Markers - just for Points layers
                ltable = s3db.gis_layer_symbology
                #ltable.gps_marker.readable = ltable.gps_marker.writable = False
                if r.method != "update":
                    # Only show ones with no definition yet for this Layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.symbology_id)
                    # Filter them out
                    ltable.symbology_id.requires = IS_ONE_OF(db, "gis_symbology.id",
                                                             "%(name)s",
                                                             not_filterby="id",
                                                             not_filter_opts=[row.symbology_id for row in rows]
                                                             )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)
    return output

# -----------------------------------------------------------------------------
def layer_theme():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                ltable.style.writable = ltable.style.readable = True
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
            else:
                # CRUD Strings
                type = "Theme"
                LAYERS = T(TYPE_LAYERS_FMT % type)
                ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
                EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
                LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
                NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
                s3.crud_strings["gis_layer_theme"] = Storage(
                    title_create=ADD_LAYER,
                    title_display=LAYER_DETAILS,
                    title_list=LAYERS,
                    title_update=EDIT_LAYER,
                    title_search=SEARCH_LAYERS,
                    subtitle_create=ADD_NEW_LAYER,
                    label_list_button=LIST_LAYERS,
                    label_create_button=ADD_LAYER,
                    label_delete_button = DELETE_LAYER,
                    msg_record_created=LAYER_ADDED,
                    msg_record_modified=LAYER_UPDATED,
                    msg_record_deleted=LAYER_DELETED,
                    msg_list_empty=NO_LAYERS)
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
                # Inject Import links
                s3.rfooter = DIV(A(T("Import Layers"),
                                   _href=URL(args="import"),
                                   _class="action-btn"),
                                 A(T("Import Data"),
                                   _href=URL(f="theme_data", args="import"),
                                   _class="action-btn"),
                                 )
        return output
    s3.postp = postp

    if "import" in request.args:
        # Import to 'layer_config' resource instead
        output = s3_rest_controller("gis", "layer_config",
                                    csv_template="layer_theme",
                                    csv_stylesheet="layer_theme.xsl",
                                    )
    else:
        output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def theme_data():
    """ RESTful CRUD controller """

    field = s3db.gis_layer_theme_id()
    field.requires = IS_NULL_OR(field.requires)
    output = s3_rest_controller(csv_extra_fields = [
                                    # CSV column headers, so no T()
                                    dict(label="Layer",
                                         field=field)
                                ])

    return output

# -----------------------------------------------------------------------------
def layer_tms():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="enable",
                    action=enable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.visible.writable = ltable.visible.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_wfs():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.base.writable = ltable.base.readable = False
                ltable.style.readable = ltable.style.writable = True
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_wms():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="enable",
                    action=enable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_xyz():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Custom Method
    s3db.set_method(module, resourcename,
                    method="enable",
                    action=enable_layer)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                ltable.visible.writable = ltable.visible.readable = False
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                s3_action_buttons(r, copyable=True)
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# -----------------------------------------------------------------------------
def layer_js():
    """ RESTful CRUD controller """

    if settings.get_security_map() and not s3_has_role(MAP_ADMIN):
        auth.permission.fail()

    tablename = "%s_%s" % (module, resourcename)
    s3db.table(tablename)

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
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Pre-processor
    def prep(r):
        if r.interactive:
            if r.component_name == "config":
                ltable = s3db.gis_layer_config
                if r.method != "update":
                    # Only show Configs with no definition yet for this layer
                    table = r.table
                    # Find the records which are used
                    query = (ltable.layer_id == table.layer_id) & \
                            (table.id == r.id)
                    rows = db(query).select(ltable.config_id)
                    # Filter them out
                    ltable.config_id.requires = IS_ONE_OF(db, "gis_config.id",
                                                          "%(name)s",
                                                          not_filterby="config_id",
                                                          not_filter_opts=[row.config_id for row in rows]
                                                          )
        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                # Inject checkbox to enable layer in default config
                inject_enable(output)
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.gis_rheader)

    return output

# =============================================================================
def cache_feed():
    """
        RESTful CRUD controller
        - cache GeoRSS/KML feeds &
          make them available to the Map Viewing Client as GeoJSON

        The create.georss/create.kml methods are designed to be called
        asynchronously using S3Task

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
    #s3db.table("gis_cache")

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
    s3.filter = (table.lat != None) & (table.lon != None)

    # Parse the Request
    r = s3_request()

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
        Used by gis_LocationRepresent() to show just this feature on the map.
        Called by the s3_viewMap() JavaScript
    """

    # The Feature
    feature_id = request.args[0]

    table = s3db.gis_location

    # Check user is authorised to access record
    if not s3_has_permission("read", table, feature_id):
        session.error = T("No access to this record!")
        raise HTTP(401, body=current.xml.json_message(False, 401, session.error))

    feature = db(table.id == feature_id).select(table.id,
                                                table.parent,
                                                table.lat,
                                                table.lon,
                                                table.wkt,
                                                limitby=(0, 1)).first()

    if not feature:
        session.error = T("Record not found!")
        raise HTTP(404, body=current.xml.json_message(False, 404, session.error))

    # Centre on Feature
    lat = feature.lat
    lon = feature.lon
    if (lat is None) or (lon is None):
        if feature.parent:
            # Skip the current record if we can
            latlon = gis.get_latlon(feature.parent)
        elif feature.id:
            latlon = gis.get_latlon(feature.id)
        if latlon:
            lat = latlon["lat"]
            lon = latlon["lon"]
        else:
            session.error = T("No location information defined!")
            raise HTTP(404, body=current.xml.json_message(False, 404, session.error))

    # Default zoom +2 (same as a single zoom on a cluster)
    # config = gis.get_config()
    # zoom = config.zoom + 2
    bounds = gis.get_bounds(features=[feature])

    map = gis.show_map(
        features = [feature.wkt],
        lat = lat,
        lon = lon,
        #zoom = zoom,
        bbox = bounds,
        window = False,
        closable = False,
        collapsed = True,
        width=640,
        height=480,
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
        raise HTTP(400, body=current.xml.json_message(False, 400, session.error))

    tablename = "%s_%s" % (res_module, resource)
    s3db.table(tablename)
    table = db[table]
    component, pkey, fkey = s3db.get_component(table, jresource)
    jtable = db[str(component.table)]
    query = (jtable[fkey] == table[pkey]) & (table.id == instance)
    # Filter out deleted
    deleted = (table.deleted == False)
    query = query & deleted
    # Filter out inaccessible
    query2 = (ltable.id == jtable.location_id)
    accessible = auth.s3_accessible_query("read", ltable)
    query2 = query2 & accessible

    features = db(query).select(ltable.wkt,
                                left = [ltable.on(query2)]
                                )

    # Calculate an appropriate BBox
    bounds = gis.get_bounds(features=features)

    map = gis.show_map(
        features = [f.wkt for f in features],
        bbox = bounds,
        window = True,
        closable = False,
        collapsed = True
    )

    return dict(map=map)

# =============================================================================
def geocode():
    """
        Geocode a location
        - designed to be called via AJAX POST

        Looks up Lx in our own database and returns Bounds
        Passes on Street names to 3rd party services and returns a Point

        @param L0: Country (as ID)
        @param L1: State/Province (as ID)
        @param L2: County/District (as ID)
        @param L3: City/Town (as ID)
        @param L4: Village/Neighborhood (as ID)
        @param L5: Village/Census Tract (as ID)
        @param street: Street Address
        @param postcode: Postcode
    """

    # Read the request
    vars = request.post_vars
    street = vars.get("street", None)
    postcode = vars.get("postcode", None)
    L0 = vars.get("L0", None)
    L1 = vars.get("L1", None)
    L2 = vars.get("L2", None)
    L3 = vars.get("L3", None)
    L4 = vars.get("L4", None)
    L5 = vars.get("L5", None)
    # Is this a Street or Lx?
    if street:
        # Send request to external geocoders to get a Point
        from geopy import geocoders
        Lx = ",".join([])
        location = "%s,L3" % (street, Lx)
        # @ToDo: Extend gis_config to see which geocoders to use for which countries
        #if google:
        g = geocoders.GoogleV3()
        place, (lat, lon) = g.geocode(location)
        #elif yahoo
        #    apikey = settings.get_gis_api_yahoo()
        #    y = geocoders.Yahoo(apikey)
        #    place, (lat, lon) = y.geocode(location)
        # @ToDo: Check Results
        results = dict(lat=lat, lon=lon)
        results = json.dumps(results)
    else:
        # Lx: Lookup Bounds in our own database
        # Not needed by S3LocationSelectorWidget2 as it downloads bounds with options
        # @ToDo
        results = "NotImplementedError"

    response.headers["Content-Type"] = "application/json"
    return results

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
    s3.filter = (query & _filter)

    # Hide unnecessary fields
    table.level.readable = table.level.writable = False
    table.gis_feature_type.readable = table.gis_feature_type.writable = False
    table.wkt.readable = table.wkt.writable = False
    table.comments.readable = table.comments.writable = False

    # Customise Labels for specific use-cases
    #table.name.label = T("Building Name") # Building Assessments-specific
    #table.parent.label = T("Suburb") # Christchurch-specific

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
    s3.prep = lambda r, vars=vars: prep(r, vars)

    s3db.configure(table._tablename,
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

    # @ToDo: Optimise to a single query of table
    bing_key = settings.get_gis_api_bing()
    google_key = settings.get_gis_api_google()
    yahoo_key = settings.get_gis_api_yahoo()

    # http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
    print_service = settings.get_gis_print_service()

    geoserver_url = settings.get_gis_geoserver_url()

    response.title = "GeoExplorer"
    return dict(
                #config=gis.get_config(),
                bing_key=bing_key,
                google_key=google_key,
                yahoo_key=yahoo_key,
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
            The models for this are currently not enabled in modules/s3db/gis.py
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
    pe_id = auth.s3_user_pe_id(auth.user.id) if auth.s3_logged_in() else None
    opt = s3db.auth_user_options_get_osm(auth.user.pe_id) if pe_id else None
    if opt:
        osm_oauth_consumer_key, osm_oauth_consumer_secret = opt
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

        site_name = settings.get_system_name_short()

        return dict(lat=lat, lon=lon, zoom=zoom,
                    gpx_url=gpx_url,
                    site_name=site_name,
                    key=osm_oauth_consumer_key,
                    secret=osm_oauth_consumer_secret)

    else:
        session.warning = T("To edit OpenStreetMap, you need to edit the OpenStreetMap settings in your Map Config")
        redirect(URL(c="pr", f="person", args=["config"]))

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

    if auth.is_logged_in():
        # Authenticated users can use our Proxy
        allowedHosts = None
        allowed_content_types = None
    else:
        # @ToDo: Link to map_service_catalogue to prevent Open Proxy abuse
        # (although less-critical since we restrict content type)
        allowedHosts = []
        #append = allowedHosts.append
        #letable = s3db.gis_layer_entity
        #rows = db(letable.deleted == False).select(letable.layer_id, letable.instance_type)
        # @ToDo: Better query (single query by instance_type)
        #for row in rows:
        #   table = db[row.instance_type]
        #   @ToDo: Check url2/url3 for relevant instance_types
        #   r = db(table.layer_id == row.layer_id).select(table.url, limitby=(0, 1)).first()
        #   if r:
        #       append(r.url)

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
            raise HTTP(400, body=current.xml.json_message(False, 400, session.error))

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
                try:
                    y = urllib2.urlopen(r)
                except urllib2.URLError:
                    raise(HTTP(504, "Unable to reach host %s" % r))
            else:
                # GET
                try:
                    y = urllib2.urlopen(url)
                except urllib2.URLError:
                    raise(HTTP(504, "Unable to reach host %s" % url))

            i = y.info()
            if i.has_key("Content-Type"):
                ct = i["Content-Type"]
            else:
                ct = None
            if allowed_content_types:
                # Check for allowed content types
                if not ct:
                    raise(HTTP(406, "Unknown Content"))
                elif not ct.split(";")[0] in allowed_content_types:
                    # @ToDo?: Allow any content type from allowed hosts (any port)
                    #if allowedHosts and not host in allowedHosts:
                    raise(HTTP(403, "Content-Type not permitted"))

            msg = y.read()
            y.close()

            if ct:
                # Maintain the incoming Content-Type
                response.headers["Content-Type"] = ct
            return msg

        else:
            # Bad Request
            raise(HTTP(400))

    except Exception, E:
        raise(HTTP(500, "Some unexpected error occurred. Error text was: %s" % str(E)))

# END =========================================================================
