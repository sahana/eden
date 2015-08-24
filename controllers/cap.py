# -*- coding: utf-8 -*-

"""
    CAP Module - Controllers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    s3_redirect_default(URL(f="alert"))

# -----------------------------------------------------------------------------
def info_prep(r):
    """
        Preprocessor for CAP Info segments
        - whether accessed via /eden/info or /eden/alert/x/info
    """

    if s3.debug:
        s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % appname)
    else:
        s3.scripts.append("/%s/static/scripts/S3/s3.cap.min.js" % appname)
    s3.stylesheets.append("S3/cap.css")

    table = db.cap_info
    if r.representation == "html":
        if r.component:
            if r.component_name == "info":
                info_fields_comments()
            elif r.component_name == "area":
                area_fields_comments()
            elif r.component_name == "resource":
                resource_fields_comments()
        elif r.tablename == "cap_info":
            info_fields_comments()

        item = r.record
        if item and r.tablename == "cap_info" and \
           s3db.cap_alert_is_template(item.alert_id):
            for f in ("urgency",
                      "certainty",
                      "effective",
                      "onset",
                      "expires",
                      "priority",
                      "severity"
                      ):
                field = table[f]
                field.writable = False
                field.readable = False
                field.required = False
            table.category.required = False

    post_vars = request.post_vars
    template_id = None
    if post_vars.get("language", False):
        if r.tablename == "cap_info":
            # cap/info controller
            try:
                template_id = db(table.id == r.id).select(table.template_info_id,
                                                          limitby=(0, 1)
                                                          ).first().template_info_id
            except AttributeError, KeyError:
                pass
        elif r.component_name == "info":
            # cap/x/info component tab
            try:
                template_id = r.component.get_id()
                # this will error out if component is not yet saved
            except:
                pass

    if template_id:
        # Read template and copy locked fields to post_vars
        template = db(table.id == template_id).select(limitby=(0, 1)).first()
        settings = json.loads(template.template_settings)
        if isinstance(settings.get("locked", False), dict):
            locked_fields = [lf for lf in settings["locked"] if settings["locked"]]
            for lf in locked_fields:
                post_vars[lf] = template[lf]

    return True

# -----------------------------------------------------------------------------
def public():
    """
        Filtered version of the Alerts controller
    """

    s3.filter = (s3base.FS("scope") == "Public")

    return alert()

# -----------------------------------------------------------------------------
def alert():
    """ REST controller for CAP Alerts and Components """

    tablename = "cap_alert"

    def prep(r):
        
        if r.representation == "dl":
            # DataList: match list_layout
            list_fields = ["info.headline",
                           "area.name",
                           "info.priority",
                           "status",
                           "scope",
                           "info.event_type_id",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        #elif r.representation == "cap":
        #    # This is either importing from or exporting to cap format. Set both
        #    # postprocessing hooks so we don't have to enumerate methods.
        #    s3db.configure("gis_location",
        #                   xml_post_parse = s3db.cap_gis_location_xml_post_parse,
        #                   xml_post_render = s3db.cap_gis_location_xml_post_render,
        #                   )

        if r.id:
            if r.record.is_template:
                redirect(URL(c="cap", f="template",
                             args = request.args,
                             vars = request.vars))
        else:
            r.resource.add_filter(r.table.is_template == False)
            s3.formats["cap"] = r.url() # .have added by JS

        if r.interactive:
            alert_fields_comments()

            if not r.component:
                if r.method == "profile":
                    # Provide a nice display of the Alert details

                    # Hide the side menu
                    current.menu.options = None

                    # Header
                    record = r.record
                    profile_header = DIV(SPAN(SPAN("%s :: " % T("Message ID"),
                                                   _class="cap-label upper"
                                                   ),
                                              SPAN(record.identifier,
                                                   _class="cap-strong"
                                                   ),
                                              _class="medium-6 columns",
                                              ),
                                         SPAN(SPAN("%s :: " % T("Source"),
                                                   _class="cap-label upper"
                                                   ),
                                              SPAN(record.source,
                                                   _class="cap-strong"
                                                   ),
                                              _class="medium-6 columns",
                                              ),
                                         _class="row"
                                         )

                    # Read the Components
                    alert_id = record.id

                    # Info
                    # @ToDo: handle multiple languages
                    itable = s3db.cap_info
                    info = db(itable.alert_id == alert_id).select(itable.language,
                                                                  itable.category,
                                                                  itable.event_type_id,
                                                                  itable.response_type,
                                                                  itable.urgency,
                                                                  itable.severity,
                                                                  itable.certainty,
                                                                  itable.audience,
                                                                  itable.effective,
                                                                  itable.onset,
                                                                  itable.expires,
                                                                  itable.sender_name,
                                                                  itable.headline,
                                                                  itable.description,
                                                                  itable.instruction,
                                                                  itable.contact,
                                                                  itable.web,
                                                                  itable.parameter,
                                                                  limitby=(0, 1)
                                                                  ).first()

                    # Area
                    # @ToDo: handle multiple areas
                    atable = s3db.cap_area
                    area = db(atable.alert_id == alert_id).select(atable.name,
                                                                  limitby=(0, 1)).first()

                    # Map
                    ftable = s3db.gis_layer_feature
                    if auth.s3_logged_in():
                        fn = "alert"
                    else:
                        fn = "public"
                    query = (ftable.controller == "cap") & \
                            (ftable.function == fn)
                    layer = db(query).select(ftable.layer_id,
                                             limitby=(0, 1)
                                             ).first()
                    try:
                        layer = dict(active = True,
                                     layer_id = layer.layer_id,
                                     filter = "~.id=%s" % alert_id,
                                     name = record.identifier,
                                     id = "profile-header-%s-%s" % (tablename, alert_id),
                                     )
                    except:
                        # No suitable prepop found
                        layer = None

                    # Location
                    # @ToDo: Support multiple Locations
                    gtable = db.gis_location
                    ltable = db.cap_area_location
                    query = (ltable.alert_id == alert_id) & \
                            (ltable.location_id == gtable.id)
                    location = db(query).select(gtable.lat_max,
                                                gtable.lon_max,
                                                gtable.lat_min,
                                                gtable.lon_min,
                                                limitby=(0, 1)).first()
                    if location:
                        bbox = {"lat_max" : location.lat_max,
                                "lon_max" : location.lon_max,
                                "lat_min" : location.lat_min,
                                "lon_min" : location.lon_min
                                }
                    else:
                        # Default bounds
                        bbox = {}

                    label = TAG[""](SPAN("%s :: " % T("Area"),
                                         _class="cap-label upper"
                                         ),
                                    SPAN(area.name,
                                         _class="cap-value"
                                         ),
                                    )
                    map_widget = dict(label = label,
                                      type = "map",
                                      #context = "alert",
                                      icon = "icon-map",
                                      #height = 383,
                                      #width = 568,
                                      bbox = bbox,
                                      )

                    table = r.table

                    def custom_widget_fn_1(r, **attr):
                        return DIV(DIV(SPAN("%s :: " % T("Headline"),
                                            _class="cap-label upper"
                                            ),
                                       SPAN(info.headline,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(" "),
                                   DIV(SPAN("%s :: " % T("Description"),
                                            _class="cap-label upper"
                                            ),
                                       SPAN(info.description,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Response Type"),
                                            _class="cap-label upper"
                                            ),
                                       SPAN(info.response_type,
                                            _class="cap-strong"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Instructions"),
                                            _class="cap-label upper"
                                            ),
                                       SPAN(info.instruction,
                                            _class="cap-value"
                                            ),
                                       ),
                                   )

                    custom_widget_1 = dict(type = "custom",
                                           fn = custom_widget_fn_1,
                                           )

                    def custom_widget_fn_2(r, **attr):
                        return DIV(DIV(SPAN("%s " % T("Information"),
                                            _class="cap-value upper"
                                            ),
                                       SPAN("%s :: " % T("Event"),
                                            _class="cap-label upper"
                                            ),
                                       SPAN(itable.event_type_id.represent(info.event_type_id),
                                            _class="cap-strong"
                                            ),
                                       ),
                                   DIV(_class="cap-label underline"
                                       ),
                                   DIV(SPAN("%s :: " % T("Language"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.language.represent(info.language),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Category"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.category.represent(info.category),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Urgency"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.urgency.represent(info.urgency),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Severity"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.severity.represent(info.severity),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Certainty"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.certainty.represent(info.certainty),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Audience"),
                                            _class="cap-label"
                                            ),
                                       SPAN(info.audience,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Effective Date"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.effective.represent(info.effective),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Onset Date"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.onset.represent(info.onset),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Expiry Date"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.expires.represent(info.expires),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Sender"),
                                            _class="cap-label"
                                            ),
                                       SPAN(info.sender_name,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Information URL"),
                                            _class="cap-label"
                                            ),
                                       SPAN(info.web,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Contact Info"),
                                            _class="cap-label"
                                            ),
                                       SPAN(info.contact,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Parameters"),
                                            _class="cap-label"
                                            ),
                                       SPAN(itable.parameter.represent(info.parameter),
                                            _class="cap-value"
                                            ),
                                       ),
                                   )

                    custom_widget_2 = dict(type = "custom",
                                           fn = custom_widget_fn_2,
                                           )

                    def custom_widget_fn_3(r, **attr):
                        return DIV(DIV(SPAN(T("Alert Qualifiers"),
                                            _class="cap-value upper"
                                            ),
                                       ),
                                   DIV(_class="underline"
                                       ),
                                   DIV(SPAN("%s :: " % T("Sender ID"),
                                            _class="cap-label"
                                            ),
                                       SPAN(record.sender,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Sent Date/Time"),
                                            _class="cap-label"
                                            ),
                                       SPAN(table.sent.represent(record.sent),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Message Status"),
                                            _class="cap-label"
                                            ),
                                       SPAN(table.status.represent(record.status),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Message Type"),
                                            _class="cap-label"
                                            ),
                                       SPAN(table.msg_type.represent(record.msg_type),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Scope"),
                                            _class="cap-label"
                                            ),
                                       SPAN(table.scope.represent(record.scope),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Handling Code"),
                                            _class="cap-label"
                                            ),
                                       SPAN(table.codes.represent(record.codes),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Note"),
                                            _class="cap-label"
                                            ),
                                       SPAN(record.note,
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Reference ID"),
                                            _class="cap-label"
                                            ),
                                       SPAN(table.reference.represent(record.reference),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(SPAN("%s :: " % T("Incident IDs"),
                                            _class="cap-label"
                                            ),
                                       SPAN(table.incidents.represent(record.incidents),
                                            _class="cap-value"
                                            ),
                                       ),
                                   DIV(_class="underline"
                                       ),
                                   DIV(SPAN(T("Resources"),
                                            _class="cap-value upper"
                                            ),
                                       ),
                                   )

                    custom_widget_3 = dict(type = "custom",
                                           fn = custom_widget_fn_3,
                                           )

                    s3db.configure(tablename,
                                   profile_header = profile_header,
                                   profile_layers = (layer,),
                                   profile_widgets = (custom_widget_1,
                                                      map_widget,
                                                      custom_widget_2,
                                                      custom_widget_3,
                                                      ),
                                   )

                    response.s3.stylesheets.append("../themes/default/cap.css")

                elif r.method != "import":
                    s3.crud.submit_style = "hide"
                    s3.crud.custom_submit = (("edit_info",
                                              T("Save and edit information"),
                                              "",
                                              ),)

            elif r.component_name == "area":
                # Limit to those for this Alert
                r.component.table.info_id.requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "cap_info.id",
                                                                  s3db.cap_info_represent,
                                                                  filterby="alert_id",
                                                                  filter_opts=(r.id,),
                                                                  ))
                for f in ("event_type_id", "priority"):
                    # Do not show for the actual area
                    field = r.component.table[f]
                    field.writable = field.readable = False
                    
            elif r.component_name == "resource":
                # Limit to those for this Alert
                r.component.table.info_id.requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "cap_info.id",
                                                                  s3db.cap_info_represent,
                                                                  filterby="alert_id",
                                                                  filter_opts=(r.id,),
                                                                  ))

            # @ToDo: Move inside correct component context (None?)
            post_vars = request.post_vars
            if post_vars.get("edit_info", False):
                tid = post_vars["template_id"]
                if tid:
                    # Read template and copy locked fields to post_vars
                    table = db.cap_alert
                    template = db(table.id == tid).select(table.template_settings,
                                                          limitby=(0, 1)).first()
                    try:
                        tsettings = json.loads(template.template_settings)
                    except ValueError:
                        tsettings = dict()
                    if isinstance(tsettings.get("locked", False), dict):
                        locked_fields = [lf for lf in tsettings["locked"] if tsettings["locked"]]
                        for lf in locked_fields:
                            post_vars[lf] = template[lf]
        info_prep(r)
        return True
    s3.prep = prep

    def postp(r, output):

        # Check to see if "Save and add information" was pressed
        lastid = r.resource.lastid
        if lastid and request.post_vars.get("edit_info", False):
            table = db.cap_alert
            alert = db(table.id == lastid).select(table.template_id,
                                                  limitby=(0, 1)).first()

            if alert:
                # Clone all cap_info entries from the alert template
                itable = s3db.cap_info
                unwanted_fields = set(("deleted_rb",
                                       "owned_by_user",
                                       "approved_by",
                                       "mci",
                                       "deleted",
                                       "modified_on",
                                       "realm_entity",
                                       "uuid",
                                       "created_on",
                                       "deleted_fk",
                                       # Don't copy this: make an
                                       # Ajax call instead
                                       "template_settings",
                                       ))
                fields = [itable[f] for f in itable.fields
                                    if f not in unwanted_fields]
                rows = db(itable.alert_id == alert.template_id).select(*fields)
                for row in rows:
                    row_clone = row.as_dict()
                    del row_clone["id"]
                    row_clone["alert_id"] = lastid
                    row_clone["template_info_id"] = row.id
                    row_clone["is_template"] = False
                    itable.insert(**row_clone)

            r.next = URL(c="cap", f="alert", args=[lastid, "info"])

        if r.interactive:
            #if r.component_name == "info":
            #    update_url = URL(f="info", args=["[id]"])
            #    s3_action_buttons(r, update_url=update_url)

            #if r.component_name == "area":
            #    update_url = URL(f="area", args=["[id]"])
            #    s3_action_buttons(r, update_url=update_url)

            if isinstance(output, dict) and "form" in output:
                if not r.component and \
                   r.method not in ("import", "import_feed", "profile"):
                    fields = s3db.cap_info_labels()
                    jsobj = []
                    for f in fields:
                        jsobj.append("'%s': '%s'" % (f, fields[f].replace("'", "\\'")))
                    s3.js_global.append('''i18n.cap_info_labels={%s}''' % ", ".join(jsobj))
                    form = output["form"]
                    form.update(_class="cap_alert_form")
                set_priority_js()

        elif r.representation == "plain":
            # Map Popup: style like the dataList
            list_fields = ["info.headline",
                           "area.name",
                           "info.priority",
                           "status",
                           "scope",
                           "info.event_type_id",
                           "info.description",
                           "info.response_type",
                           "info.sender_name",
                           ]

            record = r.resource.select(list_fields,
                                       as_rows=True,
                                       #represent=True,
                                       #show_links=False,
                                       ).first()

            output = s3db.cap_alert_list_layout("map_popup", # list_id
                                                "map_popup", # item_id
                                                None, #r.resource,
                                                None, # rfields
                                                record
                                                )

        return output
    s3.postp = postp

    output = s3_rest_controller("cap", "alert",
                                rheader = s3db.cap_rheader,
                                )
    return output

# -----------------------------------------------------------------------------
def info():
    """
        REST controller for CAP info segments
        - shouldn't ever be called
    """

    def prep(r):
        result = info_prep(r)
        if result:
            if not r.component and r.representation == "html":
                s3.crud.custom_submit = (("add_language",
                                          T("Save and add another language..."),
                                          "",
                                          ),)

        return result
    s3.prep = prep

    def postp(r, output):
        if r.representation == "html":
            if r.component_name == "area":
                update_url = URL(f="area", args=["[id]"])
                s3_action_buttons(r, update_url=update_url)

            if not r.component and "form" in output:
                set_priority_js()

        return output
    s3.postp = postp

    output = s3_rest_controller(rheader = s3db.cap_rheader)
    return output

# -----------------------------------------------------------------------------
def template():
    """ REST controller for CAP templates """

    atable = s3db.cap_alert
    s3.filter = (atable.is_template == True)

    viewing = request.vars["viewing"]
    tablename = "cap_alert"
    
    if viewing:
        table, _id = viewing.strip().split(".")
        if table == tablename:
            redirect(URL(c="cap", f="template", args=[_id]))

    def prep(r):
        list_fields = ["template_title",
                       "info.event_type_id",
                       "scope",
                       "incidents",
                       "info.category",
                       ]
        
        s3db.configure(tablename,
                       list_fields = list_fields,
                       )
        
        for f in ("identifier", "msg_type"):
            field = atable[f]
            field.writable = False
            field.readable = False
            field.requires = None
        atable.template_title.required = True
        atable.status.readable = atable.status.writable = False
        itable = db.cap_info
        for f in ("urgency",
                  "certainty",
                  "priority",
                  "severity",
                  "effective",
                  "onset",
                  "expires",
                  ):
            field = itable[f]
            field.writable = False
            field.readable = False
            field.required = False

        itable.category.required = False

        s3.crud_strings[tablename] = Storage(
            label_create = T("Create Template"),
            title_display = T("Template"),
            title_list = T("Templates"),
            title_update = T("Edit Template"), # If already-published, this should create a new "Update" alert instead of modifying the original
            title_upload = T("Import Templates"),
            label_list_button = T("List Templates"),
            label_delete_button = T("Delete Template"),
            msg_record_created = T("Template created"),
            msg_record_modified = T("Template modified"),
            msg_record_deleted = T("Template deleted"),
            msg_list_empty = T("No templates to show"))

        if r.representation == "html":
            alert_fields_comments()
            s3.scripts.append("/%s/static/scripts/json2.min.js" % appname)
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.cap.min.js" % appname)
            s3.stylesheets.append("S3/cap.css")

        return True
    s3.prep = prep

    def postp(r,output):
        if r.interactive and "form" in output:
            s3.js_global.append('''i18n.cap_locked="%s"''' % T("Locked"))
            tablename = r.tablename
            if tablename == tablename:
                output["form"].add_class("cap_template_form")
            elif tablename == "cap_info":
                output["form"].add_class("cap_info_template_form")
        return output
    s3.postp = postp

    output = s3_rest_controller("cap", "alert",
                                rheader = s3db.cap_rheader)
    return output

# -----------------------------------------------------------------------------
def area():
    """
        REST controller for CAP area
        Should only be accessed for defining area template
    """

    def prep(r):        
        artable = s3db.cap_area
        for f in ("alert_id", "info_id"):
            field = artable[f]
            field.writable = False
            field.readable = False
        
        # Area create from this controller is template
        artable.is_template.default = True
        
        return True
    s3.prep = prep
    
    def postp(r, output):
        if r.interactive and r.component and r.component_name == "area_location":
            # Modify action button to open cap/area_location directly.
            #read_url = URL(c="cap", f="area_location", args=["[id]"])
            update_url = URL(c="cap", f="area_location", args=["[id]", "update"])
            delete_url = URL(c="cap", f="area_location", args=["[id]", "delete"])
            s3_action_buttons(r,
                              update_url=update_url,
                              delete_url=delete_url,
                              )
        return output
    s3.postp = postp

    output = s3_rest_controller("cap", "area",
                                rheader = s3db.cap_rheader)
    return output

# -----------------------------------------------------------------------------
def warning_priority():
    """
        RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def priority_get():
    
    try:
        event_type_id = request.args[0]
    except:
        result = current.xml.json_message(False, 400, "No Event Type provided!")
    else:
        try:
            event_type_id = int(event_type_id)
        except:
            result = current.xml.json_message(False, 400, "Invalid Event Type!")
        else:
            # Get Event Name for Event ID 
            etable = s3db.event_event_type
            item = db(etable.id == event_type_id).select(etable.name,
                                                         limitby=(0, 1)
                                                         ).first()
            try:
                event_type_name = item.name
            except:
                result = current.xml.json_message(False, 400, "Event Type Not Found!")
            else:
                wptable = s3db.cap_warning_priority
                query = (wptable.event_type == event_type_name)
                      
                rows = db(query).select(wptable.id,
                                        wptable.name,
                                        orderby = wptable.id)

                from gluon.serializers import json as jsons
                if rows:
                    row_dict = [{"id": r.id, "name": T(r.name)} for r in rows] + \
                               [{"id": "", "name": T("Undefined")}]
                    result = jsons(row_dict)
                else:
                    rows = db(wptable.event_type == "others").select(wptable.id, 
                                                                     wptable.name,
                                                                     orderby = wptable.id)
            
                    row_dict = [{"id": r.id, "name": T(r.name)} for r in rows] + \
                               [{"id": "", "name": T("Undefined")}]
                    result = jsons(row_dict)
    finally:
        response.headers["Content-Type"] = "application/json"
        return result
    
# -----------------------------------------------------------------------------
def compose():
    """
        Send message to the people with role of Alert Approval
    """
    
    # For SAMBRO, permission is checked by the Authentication Roles but the permission
    # should be checked if CAP module is enabled
    if settings.has_module("msg"):        
        # Notify People with the role of Alert Approval via email and SMS
        pe_ids = get_vars.get("pe_ids")
        alert_id = get_vars.get("cap_alert.id")
        subject = "%s: Alert Approval Required" % settings.get_system_name_short()
        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="cap", f="alert", args=[alert_id, "review"]))
        message = "You are requested to take action on this alert:\n\n%s" % url
        msg.send_by_pe_id(pe_ids, subject, message)
        msg.send_by_pe_id(pe_ids, subject, message, contact_method = "SMS")
        session.confirmation = T("Alert Approval Notified")
        
    redirect(URL(c="cap", f="alert"))

# -----------------------------------------------------------------------------
def alert_fields_comments():
    """
        Add comments to Alert fields
    """

    table = db.cap_alert
    table.identifier.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("A unique identifier of the alert message"),
              T("A number or string uniquely identifying this message, assigned by the sender. Must notnclude spaces, commas or restricted characters (< and &).")))

    table.sender.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The identifier of the sender of the alert message"),
              T("This is guaranteed by assigner to be unique globally; e.g., may be based on an Internet domain name. Must not include spaces, commas or restricted characters (< and &).")))

    table.status.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the appropriate handling of the alert message"),
              T("See options.")))

    table.msg_type.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The nature of the alert message"),
              T("See options.")))

    table.source.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The text identifying the source of the alert message"),
              T("The particular source of this alert; e.g., an operator or a specific device.")))

    table.scope.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the intended distribution of the alert message"),
              T("Who is this alert for?")))

    table.restriction.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The text describing the rule for limiting distribution of the restricted alert message"),
              T("Used when scope is 'Restricted'.")))

    table.addresses.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The group listing of intended recipients of the alert message"),
              T("Required when scope is 'Private', optional when scope is 'Public' or 'Restricted'. Each recipient shall be identified by an identifier or an address.")))

    table.codes.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Codes for special handling of the message"),
              T("Any user-defined flags or special codes used to flag the alert message for special handling.")))

    table.note.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The text describing the purpose or significance of the alert message"),
              T("The message note is primarily intended for use with status 'Exercise' and message type 'Error'")))

    table.reference.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The group listing identifying earlier message(s) referenced by the alert message"),
              T("The extended message identifier(s) (in the form sender,identifier,sent) of an earlier CAP message or messages referenced by this one.")))

    table.incidents.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("A list of incident(s) referenced by the alert message"),
              T("Used to collate multiple messages referring to different aspects of the same incident. If multiple incident identifiers are referenced, they SHALL be separated by whitespace.  Incident names including whitespace SHALL be surrounded by double-quotes.")))

# -----------------------------------------------------------------------------
def area_fields_comments():
    """
        Add comments to Area fields
    """

    table = db.cap_area
    table.name.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The affected area of the alert message"),
              T("A text description of the affected area.")))

    # table.circle.comment = DIV(
          # _class="tooltip",
          # _title="%s|%s" % (
              # T("A point and radius delineating the affected area"),
              # T("The circular area is represented by a central point given as a coordinate pair followed by a radius value in kilometers.")))

    # table.geocode.comment = DIV(
          # _class="tooltip",
          # _title="%s|%s" % (
              # T("The geographic code delineating the affected area"),
              # T("Any geographically-based code to describe a message target area, in the form. The key is a user-assigned string designating the domain of the code, and the content of value is a string (which may represent a number) denoting the value itself (e.g., name='ZIP' and value='54321'). This should be used in concert with an equivalent description in the more universally understood polygon and circle forms whenever possible.")))

    table.altitude.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The specific or minimum altitude of the affected area"),
              T("If used with the ceiling element this value is the lower limit of a range. Otherwise, this value specifies a specific altitude. The altitude measure is in feet above mean sea level.")))

    table.ceiling.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The maximum altitude of the affected area"),
              T("must not be used except in combination with the 'altitude' element. The ceiling measure is in feet above mean sea level.")))

# -----------------------------------------------------------------------------
def info_fields_comments():
    """
        Add comments to Information segment fields
    """

    table = db.cap_info
    table.language.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the language of the information"),
              T("Code Values: Natural language identifier per [RFC 3066]. If not present, an implicit default value of 'en-US' will be assumed. Edit settings.cap.languages in 000_config.py to add more languages. See <a href=\"%s\">here</a> for a full list.") % "http://www.i18nguy.com/unicode/language-identifiers.html"))

    table.category.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the category of the subject event of the alert message"),
              T("You may select multiple categories by holding down control and then selecting the items.")))

    table.event.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The text denoting the type of the subject event of the alert message"),
              T("If not specified, will the same as the Event Type.")))

    table.response_type.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the type of action recommended for the target audience"),
              T("Multiple response types can be selected by holding down control and then selecting the items")))

    table.urgency.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the urgency of the subject event of the alert message"),
              T("The urgency, severity, and certainty of the information collectively distinguish less emphatic from more emphatic messages." +
                "'Immediate' - Responsive action should be taken immediately" +
                "'Expected' - Responsive action should be taken soon (within next hour)" +
                "'Future' - Responsive action should be taken in the near future" +
                "'Past' - Responsive action is no longer required" +
                "'Unknown' - Urgency not known")))

    table.severity.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the severity of the subject event of the alert message"),
              T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
              "'Extreme' - Extraordinary threat to life or property" +
              "'Severe' - Significant threat to life or property" +
              "'Moderate' - Possible threat to life or property" +
              "'Minor' - Minimal to no known threat to life or property" +
              "'Unknown' - Severity unknown")))

    table.certainty.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("Denotes the certainty of the subject event of the alert message"),
              T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
              "'Observed' - Determined to have occurred or to be ongoing" +
              "'Likely' - Likely (p > ~50%)" +
              "'Possible' - Possible but not likely (p <= ~50%)" +
              "'Unlikely' - Not expected to occur (p ~ 0)" +
              "'Unknown' - Certainty unknown")))

    table.audience.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The intended audience of the alert message"),
              T("")))

    table.event_code.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("A system-specific code identifying the event type of the alert message"),
              T("Any system-specific code for events, in the form of key-value pairs. (e.g., SAME, FIPS, ZIP).")))

    table.effective.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The effective time of the information of the alert message"),
              T("If not specified, the effective time shall be assumed to be the same the time the alert was sent.")))

    table.onset.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The expected time of the beginning of the subject event of the alert message"),
              T("")))

    table.expires.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The expiry time of the information of the alert message"),
              T("If this item is not provided, each recipient is free to enforce its own policy as to when the message is no longer in effect.")))

    table.sender_name.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The text naming the originator of the alert message"),
              T("The human-readable name of the agency or authority issuing this alert.")))

    table.headline.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The text headline of the alert message"),
              T("A brief human-readable headline.  Note that some displays (for example, short messaging service devices) may only present this headline; it should be made as direct and actionable as possible while remaining short.  160 characters may be a useful target limit for headline length.")))

    table.description.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The subject event of the alert message"),
              T("An extended human readable description of the hazard or event that occasioned this message.")))

    table.instruction.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The recommended action to be taken by recipients of the alert message"),
              T("An extended human readable instruction to targeted recipients.  If different instructions are intended for different recipients, they should be represented by use of multiple information blocks. You can use a different information block also to specify this information in a different language.")))

    table.web.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("A URL associating additional information with the alert message"),
              T("A full, absolute URI for an HTML page or other text resource with additional or reference information regarding this alert.")))

    table.contact.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The contact for follow-up and confirmation of the alert message"),
              T("")))

    table.parameter.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("A system-specific additional parameter associated with the alert message"),
              T("Any system-specific datum, in the form of key-value pairs.")))

# -----------------------------------------------------------------------------
def resource_fields_comments():
    """
        Add comments to Resource fields
    """

    table = db.cap_resource
    table.resource_desc.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The type and content of the resource file"),
              T("The human-readable text describing the type and content, such as 'map' or 'photo', of the resource file.")))

    table.mime_type.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The identifier of the MIME content type and sub-type describing the resource file"),
              T("MIME content type and sub-type as described in [RFC 2046]. (As of this document, the current IANA registered MIME types are listed at http://www.iana.org/assignments/media-types/)")))

    table.size.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The integer indicating the size of the resource file"),
              T("Approximate size of the resource file in bytes.")))

    # @ToDo: This should be handled under the hood
    table.uri.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The identifier of the hyperlink for the resource file"),
              T("A full absolute URI, typically a Uniform Resource Locator that can be used to retrieve the resource over the Internet.")))

    table.digest.comment = DIV(
          _class="tooltip",
          _title="%s|%s" % (
              T("The code representing the digital digest ('hash') computed from the resource file"),
              T("Calculated using the Secure Hash Algorithm (SHA-1).")))

# -----------------------------------------------------------------------------
def set_priority_js():
    """ Output json for priority field """

    wptable = s3db.cap_warning_priority
    
    rows = db(wptable).select(wptable.name, 
                              wptable.urgency, 
                              wptable.severity,
                              wptable.certainty, 
                              wptable.color_code,
                              orderby = wptable.name,
                              )
    
    from gluon.serializers import json as jsons
    p_settings = [(T(r.name), r.urgency, r.severity, r.certainty, r.color_code)\
                 for r in rows]
    
    priority_conf = '''S3.cap_priorities=%s''' % jsons(p_settings)
    js_global = s3.js_global
    if not priority_conf in js_global:
        js_global.append(priority_conf)

    return

# END =========================================================================
