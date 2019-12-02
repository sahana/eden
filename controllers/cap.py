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
def alerting_authority():
    """
        Alerting Authorities: RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def alert_history():
    """
        Alert History: RESTful CRUD controller
    """

    return s3_rest_controller(rheader=s3db.cap_history_rheader)

# -----------------------------------------------------------------------------
def alert_ack():
    """
        Alert Acknowledgements: RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def info_prep(r):
    """
        Preprocessor for CAP Info segments
        - whether accessed via /eden/info or /eden/alert/x/info

        TODO move this into info model
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
            except (AttributeError, KeyError):
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
        # TODO improve docstring
        Filtered version of the Alerts controller
    """

    s3.filter = (FS("scope") == "Public") # TODO do this in the prep of alert()

    return alert()

# -----------------------------------------------------------------------------
def alert():
    """ REST controller for CAP Alerts and Components """

    tablename = "cap_alert"

    def prep(r):
        from s3 import S3OptionsFilter
        resource = r.resource
        table = r.table
        itable = s3db.cap_info

        rows = db(itable.expires < request.utcnow).select(itable.id,
                                                          orderby=itable.id)
        expired_ids = ",".join([str(row.id) for row in rows]) or None

        rows = db(itable.expires >= request.utcnow).select(itable.id,
                                                           orderby=itable.id)
        unexpired_ids = default_filter = ",".join([str(row.id) for row in rows]) or None


        rows = db(table.external == True).select(table.id,
                                                 orderby=table.id)
        external_alerts = ",".join([str(row.id) for row in rows]) or None

        rows = db(table.external != True).select(table.id,
                                                 orderby=table.id)
        internal_alerts = default_alert = ",".join([str(row.id) for row in rows]) or None

        filter_widgets = s3db.get_config(tablename, "filter_widgets")
        filter_widgets_insert = filter_widgets.insert
        filter_widgets_insert(0, S3OptionsFilter("info.id",
                                                 label = T("Expiration"),
                                                 options = OrderedDict(
                                                        [(expired_ids, T("Expired")),
                                                         (unexpired_ids, T("Unexpired")),
                                                         ("*", T("All")),
                                                         ]),
                                                 cols = 3,
                                                 multiple = False,
                                                 default = default_filter,
                                                 ))
        filter_widgets_insert(1, S3OptionsFilter("id",
                                                 label = T("Source"),
                                                 options = OrderedDict(
                                                        [(internal_alerts, T("Internal")),
                                                         (external_alerts, T("External")),
                                                         ("*", T("All")),
                                                         ]),
                                                 cols = 3,
                                                 multiple = False,
                                                 default = default_alert,
                                                 ))
        # No need to put them back - the edit happens in-place
        #s3db.configure(tablename,
        #               filter_widgets = filter_widgets,
        #               )
        representation = r.representation
        if representation in ("html", "aadata"):
            table.msg_type.represent = None

        elif representation == "dl":
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

        elif representation == "json":
            # @ToDo: fix JSON representation's ability to use component list_fields
            list_fields = ["id",
                           "identifier",
                           "msg_type",
                           "sender",
                           "sent",
                           "scope",
                           "status",
                           "template_id",
                           "restriction",
                           "info.description",
                           "info.category",
                           "info.certainty",
                           "info.effective",
                           "info.event_type_id",
                           "info.event_type_id$name",
                           "info.expires",
                           "info.headline",
                           "info.onset",
                           "info.priority",
                           "info.response_type",
                           "info.severity",
                           "info.urgency",
                           "area.name",
                           ]

            s3db.configure(tablename,
                           list_fields = list_fields,
                           )

        elif representation == "rss":
            # filter non-template internal alerts that are approved
            filter = (table.is_template != True) & (table.external != True) & \
                     (table.approved_on != None)
            resource.add_filter(filter)

        record = r.record
        if r.id:

            if record.is_template:
                redirect(URL(c="cap", f="template",
                             args = request.args,
                             vars = request.vars))

            if record.external != True:
                from s3 import S3Represent
                table.addresses.represent = S3Represent(lookup = "pr_group",
                                                        fields = ["name"],
                                                        multiple = True,
                                                        )

            # Don't show event_type_id and template once created
            # If the user used the wrong event type,
            # then they should "Cancel" that alert and start a new one
            table.event_type_id.readable = False
            table.event_type_id.writable = False
            table.template_id.readable = False
            table.template_id.writable = False

            if record.approved_by is not None:
                # Once approved, don't allow to edit
                # Don't allow to delete
                s3db.configure(tablename,
                               deletable = False,
                               editable = False,
                               insertable = False,
                               )
            if record.reference is not None:
                table.msg_type.writable = False

            if settings.get_cap_restrict_fields():
                if record.msg_type in ("Update", "Cancel", "Error"):
                    # Use case for change in msg_type
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
                        table[f].writable = False
        else:
            r.resource.add_filter(table.is_template == False)
            s3.formats["cap"] = r.url() # .have added by JS

        if r.interactive:
            if r.method not in ("import", "import_feed"):
                # Internal Alerts
                table.external.default = False
            if not r.component:
                if r.get_vars["~.approved_by__ne"] == "None":
                    # Filter to internal alerts
                    r.resource.add_filter(table.external != True)
                    s3.crud_strings["cap_alert"].title_list = T("Approved Alerts")

                    # TODO Action buttons should be postp, not prep
                    s3_action_buttons(r, deletable=False, editable=False,
                                      read_url=URL(args="[id]"))
                    profile_button = {"url": URL(args=["[id]", "profile"]),
                                      "_class": "action-btn",
                                      "_target": "_blank",
                                      "label": str(T("View Profile"))
                                      }
                    s3.actions.insert(1, profile_button)
                    list_fields = ["info.event_type_id",
                                   "msg_type",
                                   (T("Sent"), "sent"),
                                   "info.headline",
                                   "info.sender_name",
                                   "approved_by",
                                   ]

                    s3db.configure(tablename,
                                   filter_widgets = None,
                                   insertable = False,
                                   list_fields = list_fields,
                                   )
                elif r.get_vars["~.external"] == "True":
                    # TODO explain this section
                    query = (table.id == itable.alert_id) & \
                            (table.external == True) & \
                            (table.is_template != True) & \
                            (table.deleted != True)
                    rows = db(query).select(itable.sender_name,
                                            groupby=itable.sender_name)
                    sender_options = {}
                    for row in rows:
                        sender_name = row.sender_name
                        sender_options[sender_name] = s3_str(T(sender_name))

                    rows = db(query).select(itable.event_type_id,
                                            groupby=itable.event_type_id)
                    event_type_options = {}
                    for row in rows:
                        event_type_id = row.event_type_id
                        event_type_options[event_type_id] = itable.event_type_id.represent(event_type_id)
                    filter_widgets = [
                        S3OptionsFilter("info.sender_name",
                                        label = T("Sender"),
                                        options = sender_options,
                                        ),
                        S3OptionsFilter("info.event_type_id",
                                        options = event_type_options,
                                        ),
                        S3OptionsFilter("scope",
                                        ),
                        S3OptionsFilter("msg_type",
                                        default = "Alert",
                                        ),
                        ]
                    s3.crud_strings["cap_alert"].title_list = T("Alerts Hub")
                    s3base.S3CRUD.action_buttons(r, deletable=False)
                    profile_button = {"url": URL(args=["[id]", "profile"]),
                                      "_class": "action-btn",
                                      "_target": "_blank",
                                      "label": str(T("View Profile"))
                                      }
                    s3.actions.insert(1, profile_button)

                    s3db.configure(tablename,
                                   deletable = False,
                                   editable = False,
                                   filter_widgets = filter_widgets,
                                   insertable = False,
                                   )

                if r.method == "review":
                    alert_id = r.id
                    if alert_id:
                        artable = s3db.cap_area
                        irow = db(itable.alert_id == alert_id).select(itable.id,
                                                                      itable.urgency,
                                                                      itable.severity,
                                                                      itable.certainty,
                                                                      limitby=(0, 1)).first()
                        arow = db(artable.alert_id == alert_id).select(artable.id,
                                                                       limitby=(0, 1)).first()
                        if not irow or not arow:
                            # This is incomplete alert
                            session.warning = T("This Alert is incomplete! You can complete it now.")
                            redirect(URL(c="cap", f="alert", args=[alert_id]))
                        elif not irow.urgency or not irow.severity or not irow.certainty:
                            # Some required element is missing
                            # This could arise because info segments are copied from templates
                            # and there is no any urgency or severity or certainty in the info template
                            session.warning = T("Urgency or Severity or Certainty is missing in info segment!.")
                            redirect(URL(c="cap", f="alert", args=[alert_id, "info"]))
                    else:
                        if r.get_vars["status"] == "incomplete":
                            # Show incomplete alerts, ie. without info and area segment
                            s3.filter = ((FS("info.id") == None) | (FS("area.id") == None)) & \
                                        (FS("external") != True)
                            s3.crud_strings["cap_alert"].title_list = T("Incomplete Alerts")
                            url = URL(c="cap", f="alert", args=["[id]"])
                            s3base.S3CRUD.action_buttons(r, update_url=url, read_url=url)
                        elif not r.get_vars:
                            # Filter those alerts having at least info and area segment
                            s3.filter = ((FS("info.id") != None) & (FS("area.id") != None)) & \
                                        (FS("external") != True)
                            s3.crud_strings["cap_alert"].title_list = T("Review Alerts")
                        list_fields = ["event_type_id",
                                       "msg_type",
                                       (T("Sent"), "sent"),
                                       "info.headline",
                                       "info.sender_name",
                                       "created_by",
                                       ]
                        s3db.configure(tablename,
                                       list_fields = list_fields,
                                       )
                elif r.method == "profile":
                    # Provide a nice display of the Alert details
                    # TODO move this into a separate function, probably in model

                    # Hide the side menu
                    current.menu.options = None

                    # Header
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
                    # Fields to extract
                    fields = ["info.id",
                              "info.category",
                              "info.event_type_id",
                              "info.response_type",
                              "info.priority",
                              "info.urgency",
                              "info.severity",
                              "info.certainty",
                              "info.audience",
                              "info.effective",
                              "info.onset",
                              "info.expires",
                              "info.sender_name",
                              "info.headline",
                              "info.description",
                              "info.instruction",
                              "info.contact",
                              "info.web",
                              "info_parameter.name",
                              "info_parameter.value",
                              "area.name",
                              "resource.resource_desc",
                              "resource.uri",
                              "resource.image",
                              "resource.doc_id",
                              ]

                    # Extract the data
                    data = resource.select(fields, raw_data=True)
                    info = data["rows"][0]
                    if info:
                        ptable = s3db.cap_info_parameter
                        if isinstance(info["cap_info.id"], list):
                            query = (ptable.info_id.belongs(info["cap_info.id"]))
                        else:
                            query = (ptable.info_id == info["cap_info.id"])
                        parameters = db(query).select(ptable.name,
                                                      ptable.value)

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

                    area_name = info["cap_area.name"]
                    if area_name:
                        label = TAG[""](SPAN("%s :: " % T("Area"),
                                             _class="cap-label upper"
                                             ),
                                        SPAN(", ".join(area_name)
                                             if isinstance(area_name, list)
                                             else area_name,
                                             _class="cap-value"
                                             ),
                                        )
                    else:
                        label = ""
                    map_widget = dict(label = label,
                                      type = "map",
                                      #context = "alert",
                                      icon = "icon-map",
                                      #height = 383,
                                      #width = 568,
                                      bbox = bbox,
                                      )

                    widget = s3db.cap_AlertProfileWidget
                    component = widget.component

                    @widget(None)
                    def alert_widget(r, **attr):
                        return (
                          component("Headline", info["cap_info.headline"],
                                    uppercase = True,
                                    headline = True,
                                    ),
                          component("Description", info["cap_info.description"],
                                    uppercase = True,
                                    ),
                          component("Response Type", info["cap_info.response_type"]
                                    if info["cap_info.response_type"] else None,
                                    uppercase = True,
                                    strong = True,
                                    hide_empty = True,
                                    ),
                          component("Instructions", info["cap_info.instruction"],
                                    uppercase = True,
                                    ),
                        )

                    @widget("Information",
                            label = "Event",
                            value = itable.event_type_id.represent(info["cap_info.event_type_id"]),
                            )
                    def info_widget(r, **attr):

                        if len(parameters):
                            params = ", ".join("%s: %s" % (p.name, p.value)
                                               for p in parameters)
                        else:
                            params = None

                        return (
                            component("Priority",
                                      info["cap_info.priority"],
                                      represent = itable.priority.represent,
                                      hide_empty = True,
                                      ),
                            component("Category",
                                      info["cap_info.category"],
                                      represent = itable.category.represent,
                                      ),
                            component("Urgency",
                                      info["cap_info.urgency"],
                                      represent = itable.urgency.represent,
                                      ),
                            component("Severity",
                                      info["cap_info.severity"],
                                      represent = itable.severity.represent,
                                      ),
                            component("Certainty",
                                      info["cap_info.certainty"],
                                      represent = itable.certainty.represent,
                                      ),
                            component("Audience",
                                      info["cap_info.audience"],
                                      ),
                            component("Effective Date",
                                      info["cap_info.effective"],
                                      represent = itable.effective.represent,
                                      ),
                            component("Onset Date",
                                      info["cap_info.onset"],
                                      represent = itable.onset.represent,
                                      ),
                            component("Expiry Date",
                                      info["cap_info.expires"],
                                      represent = itable.expires.represent,
                                      ),
                            component("Information URL",
                                      info["cap_info.web"],
                                      ),
                            component("Sender",
                                      info["cap_info.sender_name"],
                                      ),
                            component("Contact Info",
                                      info["cap_info.contact"],
                                      ),
                            component("Parameters",
                                      params,
                                      ),
                        )

                    @widget("Alert Qualifiers")
                    def qualifiers_widget(r, **attr):

                        return (
                            component("Sender ID",
                                      record.sender,
                                      ),
                            component("Sent Date/Time",
                                      record.sent,
                                      represent = table.sent.represent,
                                      ),
                            component("Message Status",
                                      record.status,
                                      represent = table.status.represent,
                                      ),
                            component("Message Type",
                                      record.msg_type,
                                      ),
                            component("Handling Code",
                                      record.codes,
                                      represent = table.codes.represent,
                                      ),
                            component("Scope",
                                      record.scope,
                                      ),
                            component("Note",
                                      record.note,
                                      ),
                            component("Reference ID",
                                      record.reference,
                                      ),
                            component("Incident IDs",
                                      record.incidents,
                                      represent = table.incidents.represent,
                                      ),
                        )

                    resource_desc = info["cap_resource.resource_desc"]
                    dtable = s3db.doc_document
                    documents_ = []
                    resource_title = None
                    if resource_desc:
                        resource_title = T("Resources")
                        doc_id = info["cap_resource.doc_id"]
                        resource_image = info["cap_resource.image"]
                        if doc_id:
                            if isinstance(doc_id, list):
                                query = (dtable.doc_id.belongs(doc_id)) & \
                                        (dtable.deleted != True)
                            else:
                                query = (dtable.doc_id == doc_id) & (dtable.deleted != True)
                            drows = db(query).select(dtable.file)
                            for drow in drows:
                                documents_.append(drow.file)

                    @widget(resource_title)
                    def resource_widget(r, **attr):

                        return (
                            component("Resource Description",
                                      resource_desc,
                                      ),
                            component("Resource Link",
                                      info["cap_resource.uri"],
                                      ),
                            component("Attached Image",
                                      info["cap_resource.image"],
                                      represent = s3db.doc_image_represent,
                                      resource_segment = True,
                                      ),
                            component("Attached Document",
                                      documents_,
                                      represent = dtable.file.represent,
                                      resource_segment = True,
                                      ),
                        )

                    s3db.configure(tablename,
                                   profile_header = profile_header,
                                   profile_layers = (layer,),
                                   profile_widgets = ({"type": "custom",
                                                       "fn": alert_widget,
                                                       },
                                                      map_widget,
                                                      {"type": "custom",
                                                       "fn": info_widget,
                                                       },
                                                      {"type": "custom",
                                                       "fn": qualifiers_widget,
                                                       },
                                                      {"type": "custom",
                                                       "fn": resource_widget,
                                                       },
                                                      ),
                                   )

                    s3.stylesheets.append("../themes/default/cap.css")

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
                                              "button small",
                                              ),)

            elif r.component_name == "info":
                # Filter the language options
                itable.language.requires = IS_ISO639_2_LANGUAGE_CODE(\
                                            zero=None,
                                            translate=True,
                                            select=settings.get_cap_languages())
                itable.language.comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Denotes the language of the information"),
                                                                T("Code Values: Natural language identifier per [RFC 3066]. If not present, an implicit default value of 'en-US' will be assumed. Edit settings.cap.languages in 000_config.py to add more languages. See <a href=\"%s\">here</a> for a full list.") % "http://www.i18nguy.com/unicode/language-identifiers.html"))
                # Do not show this as overwritten in onaccept
                itable.web.readable = False
                itable.web.writable = False

                alert_id = request.args(0)

                # Check for prepopulate # TODO DRY this with corresponding section in template/X/info
                if alert_id:
                    irows = db(itable.alert_id == alert_id).select(itable.language)
                    # An alert can contain two info segments, in English and local language
                    if len(irows) < 2:
                        row = db(table.id == alert_id).select(table.scope,
                                                              table.event_type_id,
                                                              limitby=(0, 1)).first()
                        if row.scope == "Public":
                            fn = "public"
                        else:
                            fn = "alert"
                        itable.web.default = settings.get_base_public_url()+\
                                             URL(c="cap", f=fn, args=alert_id)
                        itable.event_type_id.default = row.event_type_id
                    else:
                        s3db.configure("cap_info",
                                       insertable = False,
                                       )
                if record.approved_by is not None:
                    # Once approved, don't allow info segment to edit
                    # Don't allow to delete
                    s3db.configure("cap_info",
                                   deletable = False,
                                   editable = False,
                                   insertable = False,
                                   )
                if settings.get_cap_restrict_fields():
                    if record.msg_type in ("Update", "Cancel", "Error"):
                        # Use case for change in msg_type
                        for f in ("language",
                                  "category",
                                  "event",
                                  "event_type_id",
                                  "audience",
                                  "event_code",
                                  "sender_name",
                                  #"parameter",
                                  ):
                            itable[f].writable = False

            elif r.component_name == "area":
                atable = r.component.table
                list_fields = ["name",
                               "altitude",
                               "ceiling",
                               (T("Polygon"), "location.location_id"),
                               "tag.tag",
                               (T("Geocode Value"), "tag.value"),
                               ]
                s3db.configure("cap_area",
                               list_fields = list_fields,
                               )

                # Do not show for the actual area
                atable.event_type_id.writable = atable.event_type_id.readable = False

                translate = settings.get_L10n_translate_cap_area()
                if translate:
                    if session.s3.language == settings.get_L10n_default_language():
                        translate = False
                    if translate:
                        # Represent each row with local name if available
                        from s3 import S3Represent
                        cap_area_options = cap_AreaRowOptionsBuilder(r.id)
                        atable.name.represent = S3Represent(options=cap_area_options)

                if record.approved_by is not None:
                    # Once approved, don't allow area segment to edit
                    # Don't allow to delete
                    s3db.configure("cap_area",
                                   deletable = False,
                                   editable = False,
                                   insertable = False,
                                   )

            elif r.component_name == "resource":
                if record.approved_by is not None:
                    # Once approved, don't allow resource segment to edit
                    # Don't allow to delete
                    s3db.configure("cap_resource",
                                   deletable = False,
                                   editable = False,
                                   insertable = False,
                                   )

            # TODO: Move inside correct component context (None?)
            post_vars = request.post_vars
            if post_vars.get("edit_info", False):
                tid = post_vars["template_id"]
                if tid:
                    # Read template and copy locked fields to post_vars
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
            itable = s3db.cap_info
            alert = db(table.id == lastid).select(table.template_id,
                                                  limitby=(0, 1)).first()
            iquery = (itable.alert_id == alert.template_id) & \
                     (itable.deleted != True)
            irows = db(iquery).select(itable.id)
            iquery_ = (itable.alert_id == lastid) & \
                      (itable.deleted != True)
            irows_ = db(iquery_).select(itable.template_info_id)

            parameter_table = s3db.cap_info_parameter
            if alert.template_id and not \
               ({irow.id for irow in irows} == {irow_.template_info_id for irow_ in irows_}):

                parameter_query_ = (parameter_table.alert_id == alert.template_id) & \
                                   (parameter_table.deleted != True)

                # Clone all cap_info entries from the alert template
                # If already created dont copy again
                unwanted_fields = {"deleted_rb",
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
                                   }
                fields = [itable[f] for f in itable.fields
                          if f not in unwanted_fields]

                parameter_fields = [parameter_table[f] for f in parameter_table.fields
                                    if f not in unwanted_fields]
                scope_row = db(table.id == lastid).select(table.scope,
                                                          limitby=(0, 1)).first()
                if scope_row and scope_row.scope == "Public":
                    fn = "public"
                else:
                    fn = "alert"
                rows = db(itable.alert_id == alert.template_id).select(*fields)
                for row in rows:
                    row_clone = row.as_dict()
                    audience = row_clone["audience"]
                    if not audience or audience == messages["NONE"]:
                        audience = None
                    del row_clone["id"]
                    row_clone["alert_id"] = lastid
                    row_clone["template_info_id"] = row.id
                    row_clone["is_template"] = False
                    row_clone["effective"] = request.utcnow
                    row_clone["expires"] = s3db.cap_expirydate()
                    row_clone["sender_name"] = s3db.cap_sendername()
                    row_clone["web"] = settings.get_base_public_url() + \
                                        URL(c="cap", f=fn, args=lastid)
                    row_clone["audience"] = audience
                    new_info_id = itable.insert(**row_clone)

                    # Copy info_parameter as well
                    parameter_query = parameter_query_ & \
                                      (parameter_table.info_id == row.id)
                    parameter_rows =db(parameter_query).select(*parameter_fields)
                    for parameter_row in parameter_rows:
                        parameter_row_clone = parameter_row.as_dict()
                        del parameter_row_clone["id"]
                        parameter_row_clone["alert_id"] = lastid
                        parameter_row_clone["info_id"] = new_info_id
                        parameter_table.insert(**parameter_row_clone)

                # Clone all cap_resource entries from the alert template
                # First get the info_id
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
                    rtable.insert(**row_clone)

            rows = db(itable.alert_id == lastid).select(itable.id)
            if len(rows) == 1:
                r.next = URL(c="cap", f="alert", args=[lastid, "info", rows.first().id, "update"])
            elif len(rows) > 1:
                r.next = URL(c="cap", f="alert", args=[lastid, "info"])
            else:
                r.next = URL(c="cap", f="alert", args=[lastid, "info", "create"])

        if r.interactive:
            if not r.component and not r.method:
                s3_action_buttons(r, read_url=URL(args="[id]"))
                profile_button = {"url": URL(args=["[id]", "profile"]),
                                  "_class": "action-btn",
                                  "_target": "_blank",
                                  "label": str(T("View Profile"))
                                  }
                cap_button = {"url": URL(args=["[id].cap"]),
                              "_class": "action-btn",
                              "_target": "_blank",
                              "label": str(T("View CAP File"))
                              }
                s3.actions.insert(1, profile_button)
                s3.actions.insert(2, cap_button)

            if get_vars.get("_next"):
                r.next = get_vars.get("_next")

            if isinstance(output, dict) and "form" in output:
                if not r.component and \
                   r.method not in ("import", "import_feed", "profile"):
                    form = output["form"]
                    form.update(_class="cap_alert_form")
                set_priority_js()

        elif r.representation == "plain":
            # Map Popup: style like the dataList
            # TODO why is this in postp not prep?
            #      - better to bypass CRUD if its output is overwritten anyway
            list_fields = ["info.headline",
                           "area.name",
                           "info.priority",
                           "status",
                           "scope",
                           "msg_type",
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
        CAP info - RESTful CRUD controller

        - shouldn't ever be called TODO if it shouldn't be called, then why does it exist?
    """

    def prep(r):
        if r.representation == "xls":
            table = r.table
            # TODO Explain this (using raw values?)
            table.alert_id.represent = None
            table.language.represent = None
            table.category.represent = None
            table.response_type.represent = None
            list_fields = ["alert_id",
                           "language",
                           "category",
                           (T("Event Type"), "event_type_id$name"),
                           "response_type",
                           "audience",
                           "event_code",
                           (T("Sender Name"), "sender_name"),
                           "headline",
                           "description",
                           "instruction",
                           "contact",
                           ]

            s3db.configure("cap_info",
                           list_fields = list_fields,
                           )

        # TODO Explain info_prep, and why would it ever return anything falsy?
        result = info_prep(r)
        if result:
            # TODO explain this
            if not r.component and r.representation == "html":
                s3.crud.submit_style = "hide"
                s3.crud.custom_submit = (("add_language",
                                          T("Save and add another language..."),
                                          "button small",
                                          ),)

        return result
    s3.prep = prep

    def postp(r, output):
        if r.representation == "html":
            # TODO explain this
            if r.component_name == "area":
                update_url = URL(f="area", args=["[id]"])
                s3_action_buttons(r, update_url=update_url)

            # TODO explain this
            if not r.component and "form" in output:
                set_priority_js()

        return output
    s3.postp = postp

    return s3_rest_controller(rheader=s3db.cap_rheader)

# -----------------------------------------------------------------------------
def info_parameter():
    """
        Info Parameters - RESTful CRUD controller

        - should only be accessed from mobile client # TODO Should? Clients won't read comments!
    """

    def prep(r):
        if r.representation == "json":
            list_fields = ["id",
                           "alert_id",
                           "info_id",
                           "name",
                           "value",
                           "mobile",
                           ]

            s3db.configure("cap_info_parameter",
                           list_fields = list_fields,
                           )
        else:
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def template():
    """ REST controller for CAP templates """

    # TODO what's this? (no real point with it, never called)
    #tablename = "cap_alert"
    #viewing = request.vars["viewing"]
    #if viewing:
    #    table, _id = viewing.strip().split(".")
    #    if table == tablename:
    #        redirect(URL(c="cap", f="template", args=[_id]))

    def prep(r):

        # Alert templates only (mandatory filter)
        r.resource.add_filter(FS("is_template") == True)

        table = r.table
        tablename = "cap_alert"

        if r.representation == "xls":

            table.scope.represent = None
            table.incidents.represent = None

            list_fields = [(T("ID"), "id"),
                           "template_title",
                           "restriction",
                           "note",
                           "incidents",
                           ]

        elif r.representation == "json":
            # TODO why this @ToDo?
            # @ToDo: fix JSON representation's ability to use component list_fields
            list_fields = ["id",
                           "template_title",
                           #"scope",
                           #"sender",
                           "info.category",
                           "info.description",
                           "info.event_type_id",
                           "info.headline",
                           "info.response_type",
                           "info.sender_name",
                           ]

        else:
            list_fields = ["template_title",
                           #"identifier",
                           "event_type_id",
                           "incidents",
                           "info.category",
                           ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       orderby = "cap_alert.event_type_id asc",
                       )

        # Hide irrelevant fields
        for fn in ("identifier",
                   "msg_type",
                   "sender",
                   "source",
                   "scope",
                   "status",
                   "addresses",
                   ):
            field = table[fn]
            field.writable = field.readable = False
            field.requires = None

        # Field configuration specifically for templates
        table.template_title.requires = [IS_NOT_EMPTY(), IS_LENGTH(512)]
        table.external.default = False

        component = r.component
        if component:
            alias = r.component_name
            ctable = component.table

            if alias == "info":
                # Hide irrelevant fields
                for fn in ("event",
                           "urgency",
                           "certainty",
                           "priority",
                           "severity",
                           "effective",
                           "onset",
                           "expires",
                           "web",
                           ):
                    field = ctable[fn]
                    field.writable = field.readable = False
                    field.requires = None

                # Set is_template to true
                ctable.is_template.default = True

                # An alert can contain two info segments, one in English and
                # one in local language
                alert_id = r.id
                if alert_id:
                    rows = db(ctable.alert_id == alert_id).select(ctable.language)
                    if len(rows) < 2:
                        # Inherit event type from alert, set default web address
                        row = db(table.id == alert_id).select(table.scope,
                                                              table.event_type_id,
                                                              limitby = (0, 1),
                                                              ).first()
                        ctable.event_type_id.default = row.event_type_id
                        f = "public" if row.scope == "Public" else "alert"
                        ctable.web.default = settings.get_base_public_url() + \
                                             URL(c="cap", f=f, args=alert_id)
                    else:
                        # All possible info segments already present
                        s3db.configure("cap_info", insertable=False)

            elif alias == "resource":

                # Set is_template to true
                ctable.is_template.default = True

        # Alternative CRUD Strings for Alert Templates
        s3.crud_strings[tablename] = Storage(
            label_create = T("Create Template"),
            title_display = T("Template"),
            title_list = T("Templates"),
            title_update = T("Edit Template"),
            title_upload = T("Import Templates"),
            label_list_button = T("List Templates"),
            label_delete_button = T("Delete Template"),
            msg_record_created = T("Template created"),
            msg_record_modified = T("Template modified"),
            msg_record_deleted = T("Template deleted"),
            msg_list_empty = T("No templates to show"),
            )

        if r.representation == "html":
            # Add global JSON object for old browsers (before ECMA-5) - obsolete?
            #s3.scripts.append("/%s/static/scripts/json2.min.js" % appname)

            # Inject CAP form logic and i18n used by it
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.cap.min.js" % appname)
            s3.js_global.append('''i18n.cap_locked="%s"''' % T("Locked"))

            # Inject module-specific styles
            s3.stylesheets.append("S3/cap.css")

        return True
    s3.prep = prep

    def postp(r, output):

        if isinstance(output, dict):
            form = output.get("form")
            if form:
                form.add_class("cap_template_form")

        if r.interactive:
            if get_vars.get("_next"):
                r.next = get_vars.get("_next")
            else:
                lastid = r.id or r.resource.lastid
                if lastid:
                    itable = s3db.cap_info
                    info = db(itable.alert_id == lastid).select(itable.id,
                                                                limitby = (0, 1),
                                                                ).first()
                    if info:
                        r.next = URL(c="cap", f="template", args=[lastid, "info"])
                    else:
                        r.next = URL(c="cap", f="template", args=[lastid, "info", "create"])

        return output
    s3.postp = postp

    return s3_rest_controller("cap", "alert", rheader=s3db.cap_rheader)

# -----------------------------------------------------------------------------
def area():
    """
        CAP Areas - RESTful CRUD controller

        Should only be accessed for defining area template # TODO Should? => filter?
    """

    def prep(r):
        artable = s3db.cap_area
        artable.alert_id.readable = False
        artable.alert_id.writable = False

        # Area create from this controller is template
        artable.is_template.default = True

        # Context-specific CRUD strings (template areas)
        s3.crud_strings["cap_area"] = Storage(
            label_create = T("Create Predefined Area"),
            title_display = T("Predefined Area"),
            title_list = T("Predefined Areas"),
            title_update = T("Edit Predefined Area"),
            title_upload = T("Import Predefined Areas"),
            label_list_button = T("List Predefined Areas"),
            label_delete_button = T("Delete Predefined Area"),
            msg_record_created = T("Predefined Area created"),
            msg_record_modified = T("Predefined Area modified"),
            msg_record_deleted = T("Predefined Area deleted"),
            msg_list_empty = T("No Predefined Areas to show"))

        list_fields = ["name",
                       "event_type_id",
                       #"priority",
                       ]

        s3db.configure("cap_area",
                       list_fields = list_fields,
                       )

        if r.representation == "json":
            list_fields = ["id",
                           "name",
                           "event_type_id",
                           (T("Event Type"), "event_type_id$name"),
                           #"priority",
                           "altitude",
                           "ceiling",
                           "location.location_id",
                           ]

            # TODO DRY this (alternative not override)
            s3db.configure("cap_area",
                           list_fields = list_fields,
                           )
        elif r.representation == "xls":
            s3db.gis_location.wkt.represent = None
            list_fields = [(T("Area Description"), "name"),
                           (T("Event Type"), "event_type_id$name"),
                           (T("WKT"), "location.location_id$wkt"),
                           "altitude",
                           "ceiling",
                           ]
            # TODO DRY this (alternative not override)
            s3db.configure("cap_area",
                           list_fields = list_fields,
                           )

        return True
    s3.prep = prep

    return s3_rest_controller("cap", "area", rheader=s3db.cap_rheader)

# -----------------------------------------------------------------------------
def warning_priority():
    """
        Warning Priorities: RESTful CRUD controller
    """

    def prep(r):
        if r.representation == "json":
            # For option lookups (priority selector)
            # - currently unused, options are injected in postp as S3.cap_priorities
            list_fields = ["id",
                           "priority_rank",
                           "color_code",
                           "severity",
                           "certainty",
                           "urgency",
                           "event_type_id",
                           "event_code",
                           "name",
                           ]
            s3db.configure("cap_warning_priority",
                           list_fields = list_fields,
                           )
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def notify_approver():
    """
        Send message to the people with role of Alert Approval
    """

    if settings.has_module("msg"):
        # Notify People with the role of Alert Approval via email and SMS
        alert_id = get_vars.get("cap_alert.id")
        atable = s3db.cap_alert
        if not alert_id and not auth.s3_has_permission("update", atable,
                                                       record_id=alert_id):
            auth.permission.fail()
        row = db(atable.id == alert_id).select(atable.created_by,
                                               atable.approved_by,
                                               limitby=(0, 1)).first()
        if not row.approved_by:
            # Get the user ids for the role alert_approver
            agtable = db.auth_group
            group_row = db(agtable.role == "Alert Approver").select(\
                                                        agtable.id,
                                                        limitby=(0, 1)).first()
            if group_row:
                user_pe_id = auth.s3_user_pe_id
                full_name = s3_fullname(pe_id=user_pe_id(row.created_by), truncate=False)
                user_ids = auth.s3_group_members(group_row.id) # List of user_ids
                pe_ids = [] # List of pe_ids
                pe_append = pe_ids.append
                for user_id in user_ids:
                    pe_append(user_pe_id(int(user_id)))
                subject = "%s: Alert Approval Required" % settings.get_system_name_short()
                url = "%s%s" % (settings.get_base_public_url(),
                                URL(c="cap", f="alert", args=[alert_id, "review"]))
                try:
                    from pyshorteners import Shortener
                except ImportError:
                    pass
                else:
                    try:
                        url = s3_str(Shortener('Tinyurl', timeout=3).short(url))
                    except:
                        pass

                message = """
Hello Approver,
%(full_name)s has created the alert message.
Your action is required to approve or reject the message.
Please go to %(url)s to complete the actions.\n
Remember to verify the content before approving by using Edit button.""" % \
                        {"full_name": full_name, "url": url}
                msg.send_by_pe_id(pe_ids,
                                  subject,
                                  message,
                                  alert_id=alert_id,
                                  )
                try:
                    msg.send_by_pe_id(pe_ids,
                                      subject,
                                      message,
                                      contact_method="SMS",
                                      alert_id=alert_id,
                                      )
                except ValueError:
                    current.log.error("No SMS Handler defined!")
                session.confirmation = T("Alert Approval Notified")
        else:
            session.error = T("Alert already approved")

    redirect(URL(c="cap", f="alert"))

# -----------------------------------------------------------------------------
def set_priority_js():
    """ Output json for priority field (TODO explain better) """

    # called from alert and info controllers
    # TODO move this into warning priority model
    #      - can be called from client (=is a controller of its own)
    #      - potentially harmful because it runs a (pointless) request cycle
    #      - pointless because it returns nothing

    wptable = s3db.cap_warning_priority

    # TODO Proper query? (exclude deleted records?)
    rows = db(wptable).select(wptable.name,
                              wptable.urgency,
                              wptable.severity,
                              wptable.certainty,
                              wptable.color_code,
                              orderby = wptable.name,
                              )

    priorities = [(s3_str(T(r.name)), r.urgency, r.severity, r.certainty, r.color_code)\
                  for r in rows]

    from gluon.serializers import json as jsons
    script = s3_str('''S3.cap_priorities=%s''' % jsons(priorities))

    js_global = s3.js_global
    if not script in js_global:
        js_global.append(script)

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
                            s3_str(row_["cap_area_name.name_l10n"] or \
                                   row_["cap_area.name"])

        return cap_area_options

# END =========================================================================
