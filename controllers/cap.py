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
        from s3 import S3OptionsFilter
        itable = s3db.cap_info
        rows = db(itable.expires < request.utcnow).select(itable.id,
                                                          orderby=itable.id)
        if rows:
            expired_ids = ",".join([str(row.id) for row in rows])
        else:
            expired_ids = "*"
        rows = db(itable.expires >= request.utcnow).select(itable.id,
                                                           orderby=itable.id)
        if rows:
            unexpired_ids = ",".join([str(row.id) for row in rows])
        else:
            unexpired_ids = "*"

        filter_widgets = s3db.get_config(tablename, "filter_widgets")
        filter_widgets.insert(0, S3OptionsFilter("info.id",
                                                 label = T("Expiration"),
                                                 options = OrderedDict(
                                                        [(expired_ids, T("Expired")),
                                                         (unexpired_ids, T("Unexpired")),
                                                         ("*", T("All")),
                                                         ]),
                                                 cols = 3,
                                                 multiple = False,
                                                 ))
        s3db.configure(tablename,
                       filter_widgets = filter_widgets,
                       )

        if r.representation == "dl":
            # DataList: match list_layout
            list_fields = ["msg_type",
                           "info.headline",
                           "area.name",
                           "info.priority",
                           "status",
                           "scope",
                           "info.event_type_id",
                           "info.certainty",
                           "info.severity",
                           "info.urgency",
                           "info.sender_name",
                           "sent",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        elif r.representation == "json":
            # @ToDo: fix JSON representation's ability to use component list_fields
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
            if r.record.approved_by is not None:
                # Once approved, don't allow to edit
                # Don't allow to delete
                s3db.configure(tablename,
                               editable=False,
                               deletable=False,
                               insertable=False,
                               )
            if settings.get_cap_restrict_fields():
                if r.record.msg_type in ("Update", "Cancel", "Error"):
                    # Use case for change in msg_type
                    atable = r.table
                    for f in ("template_id",
                              "sender",
                              "status",
                              "msg_type",
                              "source",
                              "scope",
                              "restriction",
                              "addresses",
                              "codes",
                              "note",
                              "reference",
                              "incidents",
                              ):
                        atable[f].writable = False
        else:
            r.resource.add_filter(r.table.is_template == False)
            s3.formats["cap"] = r.url() # .have added by JS

        if r.interactive:

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
                                       SPAN(record.reference,
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

                elif r.method == "assign":
                    translate = settings.get_L10n_translate_cap_area()
                    if translate:
                        if session.s3.language == settings.get_L10n_default_language():
                            translate = False
                        if translate:
                            # Represent each row with local name if available
                            from s3 import S3Represent
                            atable = s3db.cap_area
                            cap_area_options = cap_AreaRowOptionsBuilder(r.id,
                                                                         caller=r.method)
                            atable.name.represent = S3Represent(options=cap_area_options)

                elif r.method != "import" and not get_vars.get("_next"):
                    s3.crud.submit_style = "hide"
                    s3.crud.custom_submit = (("edit_info",
                                              T("Save and edit information"),
                                              "",
                                              ),)

            elif r.component_name == "info":
                itable = r.component.table
                alert_id = request.args(0)
                # Check for prepopulate
                if alert_id:
                    itable.web.default = settings.get_base_public_url()+\
                                         URL(c="cap", f="alert", args=alert_id)

                if r.record.approved_by is not None:
                    # Once approved, don't allow info segment to edit
                    # Don't allow to delete
                    s3db.configure("cap_info",
                                   editable = False,
                                   deletable = False,
                                   insertable=False,
                                   )
                if settings.get_cap_restrict_fields():
                    if r.record.msg_type in ("Update", "Cancel", "Error"):
                        # Use case for change in msg_type
                        for f in ("language",
                                  "category",
                                  "event",
                                  "event_type_id",
                                  "audience",
                                  "event_code",
                                  "sender_name",
                                  "parameter",
                                  ):
                            itable[f].writable = False

            elif r.component_name == "area":
                atable = r.component.table
                # Limit to those for this Alert
                atable.info_id.requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cap_info.id",
                                                          s3db.cap_info_represent,
                                                          filterby="alert_id",
                                                          filter_opts=(r.id,),
                                                          ))
                for f in ("event_type_id", "priority"):
                    # Do not show for the actual area
                    field = atable[f]
                    field.writable = field.readable = False

                translate = settings.get_L10n_translate_cap_area()
                if translate:
                    if session.s3.language == settings.get_L10n_default_language():
                        translate = False
                    if translate:
                        # Represent each row with local name if available
                        from s3 import S3Represent
                        cap_area_options = cap_AreaRowOptionsBuilder(r.id)
                        atable.name.represent = S3Represent(options=cap_area_options)

                # Auto assign the info_id to area if only one info segment
                itable = s3db.cap_info
                rows = db(itable.alert_id == r.record.id).select(itable.id)
                if len(rows) == 1:
                    field = atable.info_id
                    field.default = rows.first().id
                    field.writable = field.readable = False

                if r.record.approved_by is not None:
                    # Once approved, don't allow area segment to edit
                    # Don't allow to delete
                    s3db.configure("cap_area",
                                   editable = False,
                                   deletable = False,
                                   insertable=False,
                                   )

            elif r.component_name == "resource":
                atable = r.component.table
                # Limit to those for this Alert
                atable.info_id.requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cap_info.id",
                                                          s3db.cap_info_represent,
                                                          filterby="alert_id",
                                                          filter_opts=(r.id,),
                                                          ))

                # Auto assign the info_id to area if only one info segment
                itable = s3db.cap_info
                rows = db(itable.alert_id == r.record.id).select(itable.id)
                if len(rows) == 1:
                    field = atable.info_id
                    field.default = rows.first().id
                    field.writable = field.readable = False

                if r.record.approved_by is not None:
                    # Once approved, don't allow resource segment to edit
                    # Don't allow to delete
                    s3db.configure("cap_resource",
                                   editable = False,
                                   deletable = False,
                                   insertable=False,
                                   )

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

                # Clone all cap_resource entries from the alert template
                # First get the info_id
                itable = s3db.cap_info
                rows = db(itable.alert_id == lastid).select(itable.id)

                rtable = s3db.cap_resource
                r_unwanted_fields = set(s3base.s3_all_meta_field_names())
                rfields = [rtable[f] for f in rtable.fields
                                     if f not in r_unwanted_fields]
                rows_ = db(rtable.alert_id == alert.template_id).select(*rfields)
                for row in rows_:
                    row_clone = row.as_dict()
                    del row_clone["id"]
                    row_clone["alert_id"] = lastid
                    row_clone["is_template"] = False
                    # Use the info_id here
                    if len(rows) == 1:
                        row_clone["info_id"] = rows.first().id
                    else:
                        del row_clone["info_id"]
                    rtable.insert(**row_clone)

            itable = s3db.cap_info
            row = db(itable.alert_id == lastid).select(itable.id,
                                                       limitby=(0, 1)).first()
            if row:
                r.next = URL(c="cap", f="alert", args=[lastid, "info"])
            else:
                r.next = URL(c="cap", f="alert", args=[lastid, "info", "create"])

        if r.interactive:
            if get_vars.get("_next"):
                r.next = get_vars.get("_next")
            #if r.component_name == "info":
            #    update_url = URL(f="info", args=["[id]"])
            #    s3_action_buttons(r, update_url=update_url)

            #if r.component_name == "area":
            #    update_url = URL(f="area", args=["[id]"])
            #    s3_action_buttons(r, update_url=update_url)

            if isinstance(output, dict) and "form" in output:
                if not r.component and \
                   r.method not in ("import", "import_feed", "profile"):
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
        atable.template_title.requires = IS_NOT_EMPTY()
        atable.status.readable = atable.status.writable = False

        if r.component_name == "info":
            itable = db.cap_info
            for f in ("event",
                      "urgency",
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

            alert_id = request.args(0)
            # Check for prepopulate
            if alert_id:
                itable.web.default = settings.get_base_public_url()+\
                                     URL(c="cap", f="alert", args=alert_id)

        elif r.component_name == "resource":
            rtable = r.component.table
            # Limit to those for this Alert
            rtable.info_id.requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "cap_info.id",
                                                      s3db.cap_info_represent,
                                                      filterby="alert_id",
                                                      filter_opts=(r.id,),
                                                      ))

            # Set is_template to true as only accessed by template
            rtable.is_template.default = True

            # Auto assign the info_id to area if only one info segment
            itable = s3db.cap_info
            rows = db(itable.alert_id == r.record.id).select(itable.id)
            if len(rows) == 1:
                field = rtable.info_id
                field.default = rows.first().id
                field.writable = field.readable = False

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
            s3.scripts.append("/%s/static/scripts/json2.min.js" % appname)
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.cap.min.js" % appname)
            s3.stylesheets.append("S3/cap.css")

        return True
    s3.prep = prep

    def postp(r,output):
        lastid = r.resource.lastid
        if lastid:
            itable = s3db.cap_info
            row = db(itable.alert_id == lastid).select(itable.id,
                                                       limitby=(0, 1)).first()
            if row:
                r.next = URL(c="cap", f="template", args=[lastid, "info"])
            else:
                r.next = URL(c="cap", f="template", args=[lastid, "info", "create"])

        if r.interactive and "form" in output:
            if get_vars.get("_next"):
                r.next = get_vars.get("_next")

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
    from s3 import s3_unicode
    p_settings = [(s3_unicode(T(r.name)), r.urgency, r.severity, r.certainty, r.color_code)\
                 for r in rows]

    priority_conf = '''S3.cap_priorities=%s''' % jsons(p_settings)
    js_global = s3.js_global
    if not priority_conf in js_global:
        js_global.append(priority_conf)

    return

# -----------------------------------------------------------------------------
def cap_AreaRowOptionsBuilder(alert_id, caller=None):
    """
        Build the options for the cap_area associated with alert_id
        with the translated name (if available)
        @param caller: currently used by assign method
    """

    atable = s3db.cap_area

    if caller:
        assign = caller == "assign"
    else:
        assign = None
    if assign:
        query = (atable.is_template == True) & (atable.deleted != True)
    else:
        query = (atable.alert_id == alert_id) & (atable.deleted != True)

    rows = db(query).select(atable.id,
                            atable.template_area_id,
                            atable.name,
                            orderby=atable.id)
    values = [row.id for row in rows]
    count = len(values)
    if count:
        if count == 1:
            query_ = (atable.id == values[0])
        else:
            query_ = (atable.id.belongs(values))

        ltable = s3db.cap_area_name
        if assign:
            left = [ltable.on((ltable.area_id == atable.id) & \
                              (ltable.language == session.s3.language)),
                    ]
        else:
            left = [ltable.on((ltable.area_id == atable.template_area_id) & \
                              (ltable.language == session.s3.language)),
                    ]

        fields = [atable.name,
                  ltable.name_l10n,
                  ]
        rows_ = db(query_).select(left=left,
                                  limitby=(0, count),
                                  *fields)

        cap_area_options = {}
        for row_ in rows_:
                cap_area_options[row_["cap_area.name"]] = \
                            s3_unicode(row_["cap_area_name.name_l10n"] or \
                                       row_["cap_area.name"])

        return cap_area_options

# END =========================================================================
