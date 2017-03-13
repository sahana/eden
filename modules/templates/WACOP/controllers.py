# -*- coding: utf-8 -*-

from gluon import current, SQLFORM
from gluon.html import *
from gluon.storage import Storage
from gluon.utils import web2py_uuid
from s3 import s3_str, FS, ICON, S3CRUD, S3CustomController, S3DateFilter, S3DateTime, S3FilterForm, S3OptionsFilter, S3Request, S3TextFilter, S3URLQuery

THEME = "WACOP"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        T = current.T

        custom = custom_WACOP()

        # Alerts Cards
        alerts = custom._alerts_html()

        # Events Cards
        events = custom._events_html()

        # Map of Incidents
        ltable = current.s3db.gis_layer_feature
        layer = current.db(ltable.name == "Incidents").select(ltable.layer_id,
                                                              limitby=(0, 1)
                                                              ).first()
        try:
            layer_id = layer.layer_id
        except:
            # No prepop done?
            layer_id = None
        feature_resources = [{"name"     : T("Incidents"),
                              "id"       : "search_results",
                              "layer_id" : layer_id,
                              },
                             ]
        map = current.gis.show_map(height = 350,
                                   width = 425,
                                   collapsed = True,
                                   callback='''S3.search.s3map()''',
                                   feature_resources = feature_resources,
                                   )

        # Output
        output = {"alerts": alerts,
                  "events": events,
                  "map": map,
                  }

        # Incidents dataTable
        dtargs = {"dt_pagination": False,
                  "dt_pageLength": 10,
                  "dt_pagination": False,
                  "dt_searching": False,
                  #"dt_lengthMenu": None,
                  }
        current.response.s3.no_formats = True

        custom._datatable(r = S3Request("event", "incident"),
                          output = output,
                          dtargs = dtargs,
                          dt_init = None,
                          incident_id = None,
                          updateable = False,
                          start = 0,
                          limit = 10,
                          tablename = "event_incident",
                          list_fields = ["name",
                                         (T("Type"), "incident_type_id"),
                                         # @ToDo: VirtualField
                                         #"status",
                                         "location_id",
                                         (T("Start"), "date"),
                                         ],
                          orderby = "event_incident.name",
                          )

        s3 = current.response.s3
        s3.scripts.append("/%s/static/themes/WACOP/js/bookmarks.js" % current.request.application)
        s3.jquery_ready.append('''wacop_bookmarks()''')
        self._view(THEME, "index.html")
        return output

# =============================================================================
class custom_WACOP(S3CRUD):
    """
        Custom profile page for WACOP
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "incident":
            incident_id = r.id
        else:
            incident_id = None

        if r.http == "POST":
            output = self._post(r, incident_id, **attr)
            if output:
                # Update deleted
                return output

        representation = r.representation

        if representation == "html":
            return self._html(r, **attr)

        elif representation == "aadata":
            return self._aadata(r, incident_id, **attr)

        elif representation == "dl":
            if incident_id:
                # Incident Profile
                # - only show Updates relating to this Incident
                filter = (FS("event_post.incident_id") == incident_id)
                ajaxurl = URL(args = [incident_id, "custom.dl"])
            else:
                # Dashboard
                # - show all Updates
                filter = None
                ajaxurl = URL(args = "dashboard.dl")
            return self._dl(r, filter, ajaxurl, **attr)

        raise HTTP(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def _post(self, r, incident_id, **attr):
        """
            Handle POSTs

            @param r: the S3Request
            @param attr: controller arguments
        """

        delete = r.get_vars.get("delete")
        if delete:
            # Delete the Update
            resource = current.s3db.resource("cms_post", id=delete)
            numrows = resource.delete(format=r.representation)

            if numrows > 1:
                message = "%s %s" % (numrows, current.T("records deleted"))
            elif numrows == 1:
                message = self.crud_string("cms_post",
                                           "msg_record_deleted")
            else:
                r.error(404, resource.error, next=r.url(method=""))

            current.response.headers["Content-Type"] = "application/json"
            data = current.xml.json_message(message=message)
            return data

        else:
            # Process the Updates create form
            db = current.db
            s3db = current.s3db

            ptable = s3db.cms_post

            form = SQLFORM(ptable)
            #onvalidation = 
            post_vars = r.post_vars
            if form.accepts(post_vars,
                            current.session,
                            #onvalidation=onvalidation
                            ):
                pget = post_vars.get
                # Create Post
                post_id = ptable.insert(body = pget("body"),
                                        series_id = pget("series_id"),
                                        )
                record = dict(id=post_id)
                s3db.update_super(ptable, record)
                # @ToDo: onaccept / record ownership / audit if-required
                if incident_id:
                    # Link to Incident
                    s3db.event_post.insert(incident_id = r.id,
                                           post_id = post_id,
                                           )
                # Process Tags
                tags = pget("tags")
                if tags:
                    ttable = s3db.cms_tag
                    tags = tags.split(",")
                    len_tags = len(tags)
                    if len(tags) == 1:
                        query = (ttable.name == tags[0])
                    else:
                        query = (ttable.name.belongs(tags))
                    existing_tags = db(query).select(ttable.id,
                                                     ttable.name,
                                                     limitby=(0, len_tags)
                                                     )
                    existing_tags = {tag.name: tag.id for tag in existing_tags}
                    ltable = s3db.cms_tag_post
                    for tag in tags:
                        if tag in existing_tags:
                            tag_id = existing_tags[tag]
                        else:
                            tag_id = ttable.insert(name=tag)
                        ltable.insert(post_id = post_id,
                                      tag_id = tag_id,
                                      )

                current.response.confirmation = current.T("Update posted")

                if form.errors:
                    # Revert any records created within widgets/validators
                    db.rollback()
                else:
                    # Commit changes & continue to load the page
                    db.commit()

                return None

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        # Implement in sub-classes
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def _datatable(self,
                   r,
                   output,
                   dtargs,
                   dt_init,
                   incident_id,
                   updateable,
                   start,
                   limit,
                   tablename,
                   list_fields,
                   orderby):
        """
            Update output with a dataTable and a create_popup
            Update dt_init for the dataTable

            @param r: the S3Request
            @param attr: controller arguments
        """

        c, f = tablename.split("_", 1)

        resource = current.s3db.resource(tablename)
        if incident_id:
            resource.add_filter(FS("event_%s.incident_id" % f) == incident_id)

        list_id = "custom-list-%s" % tablename

        if dt_init:
            # Move the search boxes into the design
            dt_init.append('''$('#dt-%(tablename)s .dataTables_filter').prependTo($('#dt-search-%(tablename)s'));$('#dt-search-%(tablename)s .dataTables_filter input').attr('placeholder','Enter search term…').attr('name','%(tablename)s-search').prependTo($('#dt-search-%(tablename)s .dataTables_filter'));$('.custom-list-%(tablename)s_length').hide();''' % \
                dict(tablename = tablename))
            current.deployment_settings.ui.datatables_initComplete = "".join(dt_init)

        # Get the data table
        dt, totalrows, ids = resource.datatable(fields=list_fields,
                                                start=start,
                                                limit=limit,
                                                orderby=orderby)
        displayrows = totalrows

        if dt.empty:
            empty_str = self.crud_string(tablename,
                                         "msg_list_empty")
        else:
            empty_str = self.crud_string(tablename,
                                         "msg_no_match")
        empty = DIV(empty_str, _class="empty")

        # @ToDo: Permissions
        messages = current.messages
        if incident_id:
            read_url = URL(c="event", f="incident",
                           args=[incident_id, f, "[id].popup"])
            delete_url = URL(c="event", f="incident",
                             args=[incident_id, f, "[id]", "delete"])
        else:
            read_url = URL(c=c, f=f,
                           args = "[id].popup")
            delete_url = URL(c=c, f=f,
                             args=["[id]", "delete"])
        dtargs["dt_row_actions"] = [{"label": messages.READ,
                                     "url": read_url,
                                     "icon": "fa fa-eye",
                                     "_class": "s3_modal",
                                     },
                                    # @ToDo: AJAX delete
                                    {"label": messages.DELETE,
                                     "url": delete_url,
                                     "icon": "fa fa-trash",
                                     },
                                    ]
        dtargs["dt_action_col"] = len(list_fields)
        dtargs["dt_ajax_url"] = r.url(vars={"update": tablename},
                                      representation="aadata")

        datatable = dt.html(totalrows,
                            displayrows,
                            id=list_id,
                            **dtargs)

        if dt.data:
            empty.update(_style="display:none")
        else:
            datatable.update(_style="display:none")
        contents = DIV(datatable, empty, _class="dt-contents")

        # Link for create-popup
        if updateable and current.auth.s3_has_permission("create", tablename):
            if tablename == "event_human_resource":
                label = current.T("Assign Staff")
                url = URL(c="event", f="incident",
                          args=[incident_id, "assign"],
                          vars={"refresh": list_id},
                          )
            else:
                if incident_id:
                    url = URL(c="event", f="incident",
                              args=[incident_id, f, "create.popup"],
                              vars={"refresh": list_id},
                              )
                else:
                    url = URL(c=c, f=f,
                              args=["create.popup"],
                              vars={"refresh": list_id},
                              )
                if tablename == "event_organisation":
                    label = current.T("Add Organization")
                elif tablename == "project_task":
                    label = current.T("Create Task")
                else:
                    # event_team
                    label = current.T("Add")
            output["create_%s_popup" % tablename] = \
                A(TAG[""](ICON("plus"),
                          label,
                          ),
                  _href = url,
                  _class = "button tiny postfix s3_modal", 
                  _title = label,
                  )
        else:
            output["create_%s_popup" % tablename] = ""

        # Render the widget
        output["%s_datatable" % tablename] = DIV(contents,
                                                 _class="card-holder",
                                                 )

    # -------------------------------------------------------------------------
    @staticmethod
    def _alerts_html():
        """
            Create the HTML for the Alerts section
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        tablename = "cms_post"
        resource = s3db.resource(tablename)
        resource.add_filter(FS("~.series_id$name") == "Public Alert")
        # @ToDo: Just show Open Alerts?

        list_fields = [#"priority",
                       "id",
                       "status_id",
                       "date",
                       "title",
                       "body",
                       "created_by",
                       "location_id$path",
                       "location_id$L3",
                       "location_id$lat",
                       "location_id$lon",
                       ]
        rows = resource.select(fields=list_fields,
                               start=None,
                               limit=4,
                               orderby="date desc",
                               represent=True,
                               raw_data=True,
                               ).rows
        if len(rows) == 0:
            # Section won't be visible at all
            alerts = ""
        else:
            # Render the list
            alerts = DIV(H3("Alerts ",
                            TAG["small"](A(T("See all alerts"),
                                           _href=URL(c="cms", f="post",
                                                     args="summary",
                                                     ),
                                           ),
                                         ),
                            _class="well-title",
                            ),
                         _class="row well blue",
                         )
            gttable = s3db.gis_location_tag
            auth = current.auth
            if auth.is_logged_in():
                logged_in = True
                user_id = auth.user.id
                btable = s3db.cms_post_user
                bquery = (btable.post_id.belongs([row["cms_post.id"] for row in rows])) & \
                         (btable.deleted == False)
                bookmarks = db(bquery).select(btable.post_id)
                bookmarks = [b.post_id for b in bookmarks]
            else:
                logged_in = False
            for row in rows:
                record_id = row["cms_post.id"]
                status = row["cms_post.status_id"]
                post_dt = row._row["cms_post.date"]
                post_date = post_dt.date().strftime("%b %d, %Y")
                post_time = post_dt.time().strftime("%H:%M")
                if logged_in:
                    if record_id in bookmarks:
                        bookmark = LI(ICON("bookmark"),
                                      _title=T("Remove Bookmark"),
                                      _class="item bookmark",
                                      )
                    else:
                        bookmark = LI(ICON("bookmark-empty"),
                                      _title=T("Add Bookmark"),
                                      _class="item bookmark",
                                      )
                    bookmark["_data-c"] = "cms"
                    bookmark["_data-f"] = "post"
                    bookmark["_data-i"] = record_id
                else:
                    bookmark = ""
                path = row._row["gis_location.path"]
                if path:
                    L1 = path.split("/")[1]
                    query = (gttable.location_id == L1) & \
                            (gttable.tag == "state")
                    L1_abrv = db(query).select(gttable.value,
                                               limitby=(0, 1),
                                               ).first().value
                    L3 = row["gis_location.L3"]
                    lat = row["gis_location.lat"]
                    lon = row["gis_location.lon"]
                else:
                    # No location
                    L1_abrv = ""
                    L3 = ""
                    lat = ""
                    lon = ""
                alerts.append(DIV(TAG["aside"](TAG["header"](UL(LI(_class="item icon",
                                                                   ),
                                                                LI(status,
                                                                   _class="item secondary status",
                                                                   ),
                                                                _class="status-bar-left",
                                                                ),
                                                             UL(bookmark,
                                                                _class="controls",
                                                                ),
                                                             # @ToDo: Allow user-visible string to be translated without affecting the style
                                                             _class="status-bar %s" % status,
                                                             ),
                                               DIV(H1(row["cms_post.title"],
                                                      _class="title",
                                                      ),
                                                   P(SPAN("%s @ %s by %s" % (post_date, post_time, row["cms_post.created_by"]),
                                                          _class="meta",
                                                          ),
                                                     BR(),
                                                     SPAN("%s, %s; %s, %s" % (L3, L1_abrv, lat, lon),
                                                          _class="meta-location",
                                                          ),
                                                     ),
                                                   P(row["cms_post.body"],
                                                     _class="desc",
                                                     ),
                                                   _class="body",
                                                   ),
                                               TAG["footer"](P(A(T("Read More"),
                                                                 _href=URL(c="cms", f="post",
                                                                           args=[record_id, "profile"],
                                                                           ),
                                                                 _class="more",
                                                                 ),
                                                               ),
                                                             _class="footer",
                                                             ),
                                               _class="card-alert",
                                               ),
                                  _class="medium-6 large-3 columns",
                                  ))
            while len(alerts) < 4:
                # Fill out empty spaces
                alerts.append(DIV(_class="medium-6 large-3 columns",
                                  ))

        return alerts

    # -------------------------------------------------------------------------
    @staticmethod
    def _events_html():
        """
            Create the HTML for the Events section
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        tablename = "event_event"
        resource = s3db.resource(tablename)
        # Just show Open Events
        resource.add_filter(FS("~.closed") == False)

        list_fields = ["id",
                       "name",
                       "closed",
                       "start_date",
                       "end_date",
                       "exercise",
                       "comments",
                       "event_location.location_id$path",
                       "event_location.location_id$L3",
                       "event_location.location_id$addr_street",
                       "event_location.location_id$addr_postcode",
                       ]
        rows = resource.select(fields=list_fields,
                               start=None,
                               limit=3,
                               orderby="date desc",
                               represent=True,
                               raw_data=True,
                               ).rows
        if len(rows) == 0:
            # Section won't be visible at all
            events = ""
        else:
            # Render the list
            events = DIV(H3("Events ",
                            TAG["small"](A(T("See all events"),
                                           _href=URL(c="event", f="event",
                                                     args="summary",
                                                     ),
                                           ),
                                         ),
                            _class="well-title",
                            ),
                         _class="row well",
                         )
            itable = s3db.event_incident
            iquery = (itable.deleted == False)
            rtable = s3db.event_team
            rquery = (rtable.deleted == False)
            gttable = s3db.gis_location_tag
            auth = current.auth
            if auth.is_logged_in():
                logged_in = True
                user_id = auth.user.id
                etable = s3db.event_event
                has_permission = auth.s3_has_permission
                btable = s3db.event_bookmark
                bquery = (btable.user_id == user_id) & \
                         (btable.event_id.belongs([row["event_event.id"] for row in rows])) & \
                         (btable.deleted == False)
                bookmarks = db(bquery).select(btable.event_id)
                bookmarks = [b.event_id for b in bookmarks]
            else:
                logged_in = False
            for row in rows:
                record_id = row["event_event.id"]
                incidents = db(iquery & (itable.event_id == record_id)).count()
                resources = db(rquery & (rtable.event_id == record_id)).count()
                meta = "%s Incidents %s Resources" % (incidents, resources)
                if row._row["event_event.exercise"]:
                    status = "Testing"
                elif row._row["event_event.end_date"]:
                    status = "Complete"
                else:
                    status = "Active"
                start_dt = row._row["event_event.start_date"]
                start_date = start_dt.date().strftime("%b %d, %Y")
                start_time = start_dt.time().strftime("%H:%M")
                end_dt = row._row["event_event.end_date"]
                if end_dt:
                    end_date = start_dt.date().strftime("%b %d, %Y")
                    end_time = start_dt.time().strftime("%H:%M")
                    end_date = TAG[""](SPAN("Closed at:",
                                            _class="date-label",
                                            ),
                                       SPAN("%s @ %s" % (end_date, end_time),
                                            _class="date",
                                            )
                                       )
                else:
                    end_date = ""
                if logged_in:
                    if record_id in bookmarks:
                        bookmark = LI(ICON("bookmark"),
                                      _title=T("Remove Bookmark"),
                                      _class="item bookmark",
                                      )
                    else:
                        bookmark = LI(ICON("bookmark-empty"),
                                      _title=T("Add Bookmark"),
                                      _class="item bookmark",
                                      )
                    bookmark["_data-c"] = "event"
                    bookmark["_data-f"] = "event"
                    bookmark["_data-i"] = record_id
                    if has_permission("update", etable, record_id):
                        edit = LI(A(ICON("pencil"),
                                    _href=URL(c="event", f="event",
                                              args=["%s.popup" % record_id, "update"]
                                              ),
                                    _title=T("Edit Event"),
                                    _class="s3_modal",
                                    ),
                                  _class="item edit",
                                  )
                    else:
                        edit = ""
                else:
                    bookmark = ""
                    edit = ""
                path = row._row["gis_location.path"]
                if path:
                    L1 = path.split("/")[1]
                    query = (gttable.location_id == L1) & \
                            (gttable.tag == "state")
                    L1_abrv = db(query).select(gttable.value,
                                               limitby=(0, 1),
                                               ).first().value
                    L3 = row["gis_location.L3"]
                    addr_street = row["gis_location.addr_street"]
                    addr_postcode = row["gis_location.addr_postcode"]
                else:
                    # No location
                    L1_abrv = ""
                    L3 = ""
                    addr_street = ""
                    addr_postcode = ""
                events.append(DIV(TAG["aside"](TAG["header"](UL(LI(status,
                                                                   _class="item primary status",
                                                                   ),
                                                                _class="status-bar-left",
                                                                ),
                                                             UL(bookmark,
                                                                edit,
                                                                _class="controls",
                                                                ),
                                                             _class="status-bar highlight",
                                                             ),
                                               DIV(H1(row["event_event.name"],
                                                      _class="title",
                                                      ),
                                                   DIV(DIV(SPAN(addr_street,
                                                                _class="street-address",
                                                                ),
                                                           SPAN(L3,
                                                                _class="locality",
                                                                ),
                                                           SPAN(L1_abrv,
                                                                _class="region",
                                                                ),
                                                           SPAN(addr_postcode,
                                                                _class="postal-code",
                                                                ),
                                                           _class="adr",
                                                           ),
                                                       SPAN("Zero hour:",
                                                            _class="date-label",
                                                            ),
                                                       SPAN("%s @ %s" % (start_date, start_time),
                                                            _class="date",
                                                            ),
                                                       BR(),
                                                       end_date,
                                                       _class="event-date-location",
                                                       ),
                                                   P(meta,
                                                     _class="meta",
                                                     ),
                                                   P(row["event_event.comments"],
                                                     _class="desc",
                                                     ),
                                                   _class="body",
                                                   ),
                                               TAG["footer"](P(A(T("Read More"),
                                                                 _href=URL(c="event", f="event",
                                                                           args=[record_id, "profile"],
                                                                           ),
                                                                 _class="more",
                                                                 ),
                                                               ),
                                                             _class="footer",
                                                             ),
                                               _class="card-event",
                                               ),
                                  _class="medium-4 columns",
                                  ))
            while len(events) < 4:
                # Fill out empty spaces
                events.append(DIV(_class="medium-6 large-3 columns",
                                  ))

        return events

    # -------------------------------------------------------------------------
    @staticmethod
    def _system_wide_html():
        """
            Create the HTML for the System-wide 'Alert' section
        """

        ADMIN = current.auth.s3_has_role("ADMIN")

        table = current.s3db.cms_post
        record = current.db(table.name == "SYSTEM_WIDE").select(table.body,
                                                                limitby=(0, 1)
                                                                ).first()
        if record or ADMIN:
            if ADMIN:
                edit_btn = P(A(current.T("Edit System-wide Alert"),
                               _href = URL(c="cms", f="post",
                                           args = "update",
                                           vars = {"page": "SYSTEM_WIDE"},
                                           ),
                               _class = "button button-info tiny",
                               ),
                             _class = "large-3 small-12 columns text-right",
                             )
            else:
                edit_btn = ""
            system_wide = DIV(DIV(DIV(P(record and record.body or "",
                                        ),
                                      _class="large-9 small-12 columns",
                                      ),
                                  edit_btn,
                                  _role="complementary",
                                 _class="row panel callout",
                                 ),
                              _class="row",
                              )
        else:
            # Don't display the section
            system_wide = ""

        return system_wide

    # -------------------------------------------------------------------------
    def _updates_html(self, r, output, incident_id, updateable, **attr):
        """
            Create the HTML for the Updates section

            @param r: the S3Request
            @param attr: controller arguments
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        tablename = "cms_post"
        resource = s3db.resource(tablename)
        if incident_id:
            resource.add_filter(FS("event_post.incident_id") == incident_id)

        list_fields = ["series_id",
                       "priority",
                       "status_id",
                       "date",
                       "body",
                       "created_by",
                       "tag.name",
                       ]
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                   start=None,
                                                   limit=5,
                                                   list_id="updates_datalist",
                                                   orderby="date desc",
                                                   layout=cms_post_list_layout)
        if numrows == 0:
            # Empty table or just no match?
            ptable = s3db.cms_post
            if "deleted" in ptable:
                available_records = db(ptable.deleted != True)
            else:
                available_records = db(ptable._id > 0)
            if available_records.select(ptable._id,
                                        limitby=(0, 1)).first():
                msg = DIV(self.crud_string(tablename,
                                           "msg_no_match"),
                          _class="empty")
            else:
                msg = DIV(self.crud_string(tablename,
                                           "msg_list_empty"),
                          _class="empty")
            data = msg
        else:
            # Render the list
            if incident_id:
                ajaxurl = URL(args = [incident_id, "custom.dl"])
            else:
                ajaxurl = URL(args = "dashboard.dl")
            data = datalist.html(pagesize = 5,
                                 ajaxurl = ajaxurl,
                                 )

        # Render the widget
        output["updates_datalist"] = data

        # Filter Form
        # @ToDo: This should use date/end_date not just date
        date_filter = S3DateFilter("date",
                                   label = "",
                                   #hide_time = True,
                                   )
        date_filter.input_labels = {"ge": "Start Time/Date", "le": "End Time/Date"}

        filter_widgets = [S3TextFilter(["body",
                                        ],
                                       formstyle = text_filter_formstyle,
                                       label = T("Search"),
                                       _placeholder = T("Enter search term…"),
                                       ),
                          S3OptionsFilter("series_id",
                                          label = "",
                                          noneSelectedText = "Type",
                                          widget = "multiselect",
                                          ),
                          S3OptionsFilter("priority",
                                          label = "",
                                          noneSelectedText = "Priority",
                                          widget = "multiselect",
                                          ),
                          S3OptionsFilter("status_id",
                                          label = "",
                                          noneSelectedText = "Status",
                                          widget = "multiselect",
                                          ),
                          S3OptionsFilter("created_by$organisation_id",
                                          label = "",
                                          noneSelectedText = "Source",
                                          ),
                          S3OptionsFilter("tag_post.tag_id",
                                          label = "",
                                          noneSelectedText = "Tag",
                                          ),
                          date_filter,
                          ]

        auth = current.auth
        user = auth.user
        if user:
            filter_widgets.insert(1, S3OptionsFilter("bookmark.user_id",
                                                     label = "",
                                                     options = {"*": T("All"),
                                                                user.id: T("My Bookmarks"),
                                                                },
                                                     cols = 2,
                                                     multiple = False,
                                                     table = False,
                                                     ))

        filter_form = S3FilterForm(filter_widgets,
                                   formstyle = filter_formstyle_profile,
                                   submit=True,
                                   ajax=True,
                                   url=URL(args=[incident_id, "custom.dl"],
                                           vars={}),
                                   ajaxurl=URL(c="cms", f="post",
                                               args=["filter.options"], vars={}),
                                   )
        output["filter_form"] = filter_form.html(resource, r.get_vars,
                                                 target="updates_datalist",
                                                 alias=None)

        #  Create Form for Updates
        if updateable and auth.s3_has_permission("create", tablename):
            output["create_post_button"] = DIV(A(ICON("add"),
                                                 T("Add Update"),
                                                 _href=URL(c="event", f="incident",
                                                           args = [incident_id, "post", "create.popup"],
                                                           vars={"refresh": "updates_datalist"},
                                                           ),
                                                 _class="s3_modal button wide radius",
                                                 ),
                                               _class="panel",
                                               )
        else:
            output["create_post_button"] = ""

        # Tags for Updates
        s3 = current.response.s3
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/tag-it.js" % current.request.application)
        else:
            s3.scripts.append("/%s/static/scripts/tag-it.min.js" % current.request.application)
        if auth.s3_has_permission("update", s3db.cms_tag_post):
            readonly = '''afterTagAdded:function(event,ui){
if(ui.duringInitialization){return}
var post_id=$(this).attr('data-post_id')
var url=S3.Ap.concat('/cms/post/',post_id,'/add_tag/',ui.tagLabel)
$.getS3(url)
},afterTagRemoved:function(event,ui){
var post_id=$(this).attr('data-post_id')
var url=S3.Ap.concat('/cms/post/',post_id,'/remove_tag/',ui.tagLabel)
$.getS3(url)
},'''
        else:
            readonly = '''readOnly:true'''
        script = \
'''S3.tagit=function(){$('.s3-tags').tagit({autocomplete:{source:'%s'},%s})}
S3.tagit()
S3.redraw_fns.push('tagit')''' % (URL(c="cms", f="tag",
                                      args="search_ac.json"),
                                  readonly)
        s3.jquery_ready.append(script)

    # -------------------------------------------------------------------------
    def _aadata(self, r, filter, **attr):
        """
            Handle DataTable AJAX updates

            @param r: the S3Request
            @param attr: controller arguments
        """

        get_vars = r.get_vars
        tablename = get_vars.get("update")

        if tablename == "event_team":
            list_fields = ["group_id",
                           "status_id",
                           ]
            orderby = "pr_group.name"

        elif tablename == "project_task":
            list_fields = ["status",
                           "name",
                           "created_on",
                           "date_due",
                           ]
            orderby = "project_task.date_due"

        elif tablename == "event_human_resource":
            list_fields = ["human_resource_id",
                           "human_resource_id$job_title_id",
                           "human_resource_id$organisation_id",
                           "human_resource_id$person_id$email.value",
                           "human_resource_id$person_id$phone.value",
                           "status",
                           "comments",
                           ]
            orderby = "event_human_resource.human_resource_id"

        elif tablename == "event_organisation":
            list_fields = ["organisation_id",
                           "status",
                           "comments",
                           ]
            orderby = "event_organisation.organisation_id"

        else:
            raise HTTP(405, current.ERROR.BAD_METHOD)

        resource = current.s3db.resource(tablename)
        if incident_id:
            c, f = tablename.split("_", 1)
            resource.add_filter(FS("event_%s.incident_id" % f) == incident_id)

        list_id = "custom-list-%s" % tablename

        # Parse datatable filter/sort query
        searchq, orderby_not, left = resource.datatable_filter(list_fields,
                                                               get_vars)

        # DataTable filtering
        if searchq is not None:
            totalrows = resource.count()
            resource.add_filter(searchq)
        else:
            totalrows = None

        # Get the data table
        if totalrows != 0:
            start = get_vars.get("displayStart", None)
            limit = get_vars.get("pageLength", 0)
            dt, displayrows, ids = resource.datatable(fields=list_fields,
                                                      start=start,
                                                      limit=limit,
                                                      left=left,
                                                      orderby=orderby,
                                                      getids=False)
        else:
            dt, displayrows, limit = None, 0, 0

        if totalrows is None:
            totalrows = displayrows

        # Echo
        draw = int(get_vars.get("draw") or 0)

        response = current.response
        s3 = response.s3
        
        # How many records per page?
        if s3.dataTable_pageLength:
            display_length = s3.dataTable_pageLength
        else:
            display_length = 10

        # Server-side pagination?
        if not s3.no_sspag:
            dt_pagination = "true"
            if not limit and display_length is not None:
                limit = 2 * display_length
            else:
                limit = None
        else:
            dt_pagination = "false"

        dtargs = attr.get("dtargs", {})
        dtargs["dt_action_col"] = len(list_fields)
        dtargs["dt_pagination"] = dt_pagination
        dtargs["dt_pageLength"] = display_length

        # Representation
        if dt is not None:
            data = dt.json(totalrows,
                           displayrows,
                           list_id,
                           draw,
                           **dtargs)
        else:
            data = '{"recordsTotal":%s,' \
                   '"recordsFiltered":0,' \
                   '"dataTable_id":"%s",' \
                   '"draw":%s,' \
                   '"data":[]}' % (totalrows, list_id, draw)

        response.headers["Content-Type"] = "application/json"
        return data

    # -------------------------------------------------------------------------
    def _dl(self, r, filter, ajaxurl, **attr):
        """
            Handle DataList AJAX updates

            @param r: the S3Request
            @param attr: controller arguments
        """

        tablename = "cms_post"
        resource = current.s3db.resource(tablename)
        if filter:
            resource.add_filter(filter)
        queries = S3URLQuery.parse(resource, r.get_vars)
        for alias in queries:
            for q in queries[alias]:
                resource.add_filter(q)

        list_fields = ["series_id",
                       "date",
                       "body",
                       "created_by",
                       "tag.name",
                       ]
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                   start=None,
                                                   limit=5,
                                                   list_id="updates_datalist",
                                                   orderby="date desc",
                                                   layout=cms_post_list_layout)

        # Render the list
        data = datalist.html(pagesize = 5,
                             ajaxurl = ajaxurl,
                             )

        current.response.view = "plain.html"
        output = {"item": data}
        return output

# =============================================================================
class incident_Profile(custom_WACOP):
    """
        Custom profile page for an Incident
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        incident_id = r.id

        T = current.T
        auth = current.auth
        db = current.db
        s3db = current.s3db
        response = current.response
        s3 = response.s3

        ptable = s3db.cms_post
        gtable = s3db.gis_location
        itable = s3db.event_incident
        #rtable = s3db.pr_group
        ertable = s3db.event_team
        eptable = s3db.event_post
        ttable = s3db.cms_tag
        ittable = s3db.event_tag

        date_represent = lambda dt: S3DateTime.date_represent(dt,
                                                              format = "%b %d %Y %H:%M",
                                                              utc = True,
                                                              #calendar = calendar,
                                                              )

        output = {"incident_id": incident_id,
                  }

        # Incident Details
        record = r.record
        output["name"] = record.name

        output["modified_on"] = date_represent(record.modified_on)

        output["start_date"] = date_represent(record.date)

        end_date = record.end_date
        if end_date:
            output["active"] = False
            output["end_date"] = date_represent(end_date)
        else:
            output["active"] = True
            output["end_date"] = ""
        
        incident_type = record.incident_type_id
        if incident_type:
            output["incident_type"] = itable.incident_type_id.represent(incident_type)
        else:
            output["incident_type"] = None
        output["description"] = record.comments

        location = db(gtable.id == record.location_id).select(gtable.L1,
                                                              gtable.L3,
                                                              gtable.addr_street,
                                                              gtable.addr_postcode,
                                                              gtable.lat,
                                                              gtable.lon,
                                                              limitby = (0, 1),
                                                              ).first()
        if location:
            output["L1"] = location.L1 or ""
            output["L3"] = location.L3 or ""
            output["addr_street"] = location.addr_street or ""
            output["postcode"] = location.addr_postcode or ""
            output["lat"] = location.lat or ""
            output["lon"] = location.lon or ""
            # @ToDo: BBOX should include the resources too
            bbox = current.gis.get_bounds(features=[location])
            output["lat_max"] = bbox["lat_max"]
            output["lat_min"] = bbox["lat_min"]
            output["lon_max"] = bbox["lon_max"]
            output["lon_min"] = bbox["lon_min"]
        else:
            output["L1"] = ""
            output["L3"] = ""
            output["addr_street"] = ""
            output["postcode"] = ""
            output["lat"] = ""
            output["lon"] = ""
            # @ToDo: Defaults for Seattle
            output["lat_max"] = ""
            output["lat_min"] = ""
            output["lon_max"] = ""
            output["lon_min"] = ""

        updateable = auth.s3_has_permission("update", itable, record_id=incident_id, c="event", f="incident")
        output["updateable"] = updateable

        # Tags for Incident
        tag_list = UL(_class="left inline-list",
                      _id="incident-tags",
                      )
        query = (ittable.incident_id == incident_id) & \
                (ittable.deleted == False) & \
                (ittable.tag_id == ttable.id)
        tags = db(query).select(ttable.name)
        tags = [t.name for t in tags]
        for tag in tags:
            tag_list.append(LI(A(tag,
                                 _href="#",
                                 ),
                               ))
        output["incident_tags"] = tag_list
        if updateable:
            script = '''incident_tags(%s)''' % incident_id
        else:
            script = '''incident_tags(false)'''
        s3.jquery_ready.append(script)

        user = auth.user
        if user:
            user_id = user.id
            ltable = s3db.event_bookmark
            query = (ltable.incident_id == incident_id) & \
                    (ltable.user_id == user_id)
            exists = db(query).select(ltable.id,
                                      limitby=(0, 1)
                                      ).first()
            if exists:
                bookmark = A(ICON("bookmark"),
                             _title=T("Remove Bookmark"),
                             _class="item bookmark",
                             )
            else:
                bookmark = A(ICON("bookmark-empty"),
                             _title=T("Add Bookmark"),
                             _class="item bookmark",
                             )
            bookmark["_data-c"] = "event"
            bookmark["_data-f"] = "incident"
            bookmark["_data-i"] = incident_id
            script = '''wacop_bookmarks()'''
            s3.jquery_ready.append(script)
        else:
            bookmark = ""
        output["bookmark_btn"] = bookmark

        # Is this Incident part of an Event?
        event_id = record.event_id
        if event_id:
            # Read Event details
            event = Storage()
            etable = s3db.event_event
            erecord = db(etable.id == event_id).select(etable.name,
                                                       etable.exercise,
                                                       etable.start_date,
                                                       etable.end_date,
                                                       limitby = (0, 1),
                                                       ).first()
            event.name = erecord.name
            event.start_date = date_represent(erecord.start_date)
            end_date = erecord.end_date
            if end_date:
                event.active = False
                event.end_date = date_represent(end_date)
            else:
                event.active = True
                event.end_date = "n/a"

            eltable = s3db.event_event_location
            query = (eltable.event_id == event_id) & \
                    (eltable.deleted == False)
            event_location = db(query).select(eltable.location_id,
                                              limitby = (0, 1),
                                              ).first()
            if event_location:
                event.location = eltable.location_id.represent(event_location.location_id)
            else:
                event.location = ""

            query = (itable.event_id == event_id) & \
                    (itable.deleted == False)
            incidents = db(query).count()
            event.incidents = A("%s %s" % (incidents, T("Incidents")),
                                _href = URL(c="event", f="event",
                                            args = "incident.popup",
                                            ),
                                _class = "s3_modal",
                                _title = T("Incidents"),
                                )

            query = (ertable.event_id == event_id) & \
                    (ertable.deleted == False)
            resources = db(query).count()
            event.resources = A("%s %s" % (resources, T("Resources")),
                                _href = URL(c="event", f="event",
                                            args = "team.popup",
                                            ),
                                _class = "s3_modal",
                                _title = T("Resources"),
                                )

            query = (eptable.event_id == event_id) & \
                    (eptable.deleted == False)
            updates = db(query).count()
            event.updates = A("%s %s" % (updates, T("Updates")),
                                _href = URL(c="event", f="event",
                                            args = "post.popup",
                                            ),
                                _class = "s3_modal",
                                _title = T("Updates"),
                                )

            event.url = URL(c="event", f="event",
                            args = [event_id, "profile"],
                            )

            if erecord.exercise:
                event.status = T("Testing")
            elif not erecord.end_date:
                event.status = T("Open")
            else:
                event.status = T("Closed")

            output["event"] = event
        else:
            output["event"] = None

        # DataTables
        current.deployment_settings.ui.datatables_pagingType = "bootstrap"
        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

        get_vars = r.get_vars
        start = get_vars.get("start", None)
        limit = get_vars.get("limit", 0)
        if limit:
            if limit.lower() == "none":
                limit = None
            else:
                try:
                    start = int(start)
                    limit = int(limit)
                except (ValueError, TypeError):
                    start = None
                    limit = 0 # use default
        else:
            # Use defaults
            start = None

        # How many records per page?
        if s3.dataTable_pageLength:
            display_length = s3.dataTable_pageLength
        else:
            display_length = 10

        # Server-side pagination?
        if not s3.no_sspag:
            dt_pagination = "true"
            if not limit and display_length is not None:
                limit = 2 * display_length
            else:
                limit = None
        else:
            dt_pagination = "false"

        dtargs = attr.get("dtargs", {})
        dtargs["dt_pagination"] = dt_pagination
        dtargs["dt_pageLength"] = display_length
        dtargs["dt_base_url"] = r.url(method="", vars={})

        s3.no_formats = True
        datatable = self._datatable

        # Resources dataTable
        tablename = "event_team"
        list_fields = ["id", #(T("Actions"), "id"), @ToDo: Label
                       "group_id",
                       "status_id",
                       ]
        orderby = "pr_group.name"
        datatable(r,
                  output,
                  dtargs,
                  dt_init,
                  incident_id,
                  updateable,
                  start,
                  limit,
                  tablename,
                  list_fields,
                  orderby)

        # Tasks dataTable
        tablename = "project_task"
        list_fields = ["status",
                       (T("Description"), "name"),
                       (T("Created"), "created_on"),
                       (T("Due"), "date_due"),
                       ]
        orderby = "project_task.date_due"
        datatable(r,
                  output,
                  dtargs,
                  dt_init,
                  incident_id,
                  updateable,
                  start,
                  limit,
                  tablename,
                  list_fields,
                  orderby)

        # Staff dataTable
        tablename = "event_human_resource"
        list_fields = [(T("Name"), "human_resource_id"),
                       (T("Title"), "human_resource_id$job_title_id"),
                       "human_resource_id$organisation_id",
                       (T("Email"), "human_resource_id$person_id$email.value"),
                       (T("Phone"), "human_resource_id$person_id$phone.value"),
                       "status",
                       (T("Notes"), "comments"),
                       ]
        orderby = "event_human_resource.human_resource_id"
        datatable(r,
                  output,
                  dtargs,
                  dt_init,
                  incident_id,
                  updateable,
                  start,
                  limit,
                  tablename,
                  list_fields,
                  orderby)

        # Organisations dataTable
        tablename = "event_organisation"
        list_fields = [(T("Name"), "organisation_id"),
                       "status",
                       "comments",
                       ]
        orderby = "event_organisation.organisation_id"
        datatable(r,
                  output,
                  dtargs,
                  dt_init,
                  incident_id,
                  updateable,
                  start,
                  limit,
                  tablename,
                  list_fields,
                  orderby)

        # Updates DataList
        self._updates_html(r, output, incident_id, updateable, **attr)

        S3CustomController._view(THEME, "incident_profile.html")
        # Done for the whole controller
        #current.menu.options = None
        return output

# =============================================================================
class person_Dashboard(custom_WACOP):
    """
        Custom dashboard page for a person
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        #person_id = r.id

        T = current.T
        s3 = current.response.s3

        output = {}

        # Map of Incidents
        ltable = current.s3db.gis_layer_feature
        layer = current.db(ltable.name == "Incidents").select(ltable.layer_id,
                                                              limitby=(0, 1)
                                                              ).first()
        try:
            layer_id = layer.layer_id
        except:
            # No prepop done?
            layer_id = None
        feature_resources = [{"name"     : T("Incidents"),
                              "id"       : "search_results",
                              "layer_id" : layer_id,
                              },
                             ]
        output["map"] = current.gis.show_map(height = 350,
                                             width = 425,
                                             collapsed = True,
                                             callback='''S3.search.s3map()''',
                                             feature_resources = feature_resources,
                                             )

        # DataTables
        current.deployment_settings.ui.datatables_pagingType = "bootstrap"
        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

        get_vars = r.get_vars
        start = get_vars.get("start", None)
        limit = get_vars.get("limit", 0)
        if limit:
            if limit.lower() == "none":
                limit = None
            else:
                try:
                    start = int(start)
                    limit = int(limit)
                except (ValueError, TypeError):
                    start = None
                    limit = 0 # use default
        else:
            # Use defaults
            start = None

        # How many records per page?
        if s3.dataTable_pageLength:
            display_length = s3.dataTable_pageLength
        else:
            display_length = 10

        # Server-side pagination?
        if not s3.no_sspag:
            dt_pagination = "true"
            if not limit and display_length is not None:
                limit = 2 * display_length
            else:
                limit = None
        else:
            dt_pagination = "false"

        dtargs = attr.get("dtargs", {})
        dtargs["dt_pagination"] = dt_pagination
        dtargs["dt_pageLength"] = display_length
        dtargs["dt_base_url"] = r.url(method="", vars={})

        s3.no_formats = True
        datatable = self._datatable

        # Tasks dataTable
        tablename = "project_task"
        list_fields = ["status",
                       (T("Description"), "name"),
                       (T("Created"), "created_on"),
                       (T("Due"), "date_due"),
                       ]
        orderby = "project_task.date_due"
        datatable(r,
                  output,
                  dtargs,
                  dt_init,
                  None, # incident_id
                  True, # updateable
                  start,
                  limit,
                  tablename,
                  list_fields,
                  orderby)

        # Staff dataTable
        tablename = "hrm_human_resource"
        list_fields = [(T("Name"), "person_id"),
                       (T("Title"), "job_title_id"),
                       "organisation_id",
                       (T("Email"), "person_id$email.value"),
                       (T("Phone"), "person_id$phone.value"),
                       ]
        orderby = "hrm_human_resource.person_id"
        datatable(r,
                  output,
                  dtargs,
                  dt_init,
                  None, # incident_id
                  True, # updateable
                  start,
                  limit,
                  tablename,
                  list_fields,
                  orderby)

        # Organisations dataTable
        tablename = "org_organisation"
        list_fields = ["name",
                       ]
        orderby = "org_organisation.name"
        datatable(r,
                  output,
                  dtargs,
                  dt_init,
                  None, # incident_id
                  True, # updateable
                  start,
                  limit,
                  tablename,
                  list_fields,
                  orderby)

        # Updates DataList (without Create...at least until we can select an Incident to link it to)
        self._updates_html(r, output, None, False, **attr)

        S3CustomController._view(THEME, "dashboard.html")
        # Done for the whole controller
        #current.menu.options = None
        return output

# =============================================================================
def cms_post_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Updates on the Incident Profile page.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["cms_post.id"]
    item_class = "thumbnail"

    T = current.T
    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings
    permit = current.auth.s3_has_permission

    raw = record._row
    date = record["cms_post.date"]
    body = record["cms_post.body"]
    series_id = raw["cms_post.series_id"]

    # Allow records to be truncated
    # (not yet working for HTML)
    body = DIV(body,
               _class="s3-truncate",
               )

    if series_id:
        series = record["cms_post.series_id"]
        translate = settings.get_L10n_translate_cms_series()
        if translate:
            series_title = T(series)
        else:
            series_title = series
    else:
        series_title = series = ""

    status = record["cms_post.status_id"]

    author_id = raw["cms_post.created_by"]
    person = record["cms_post.created_by"]

    # @ToDo: Bulk lookup
    ltable = s3db.pr_person_user
    ptable = db.pr_person
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = db(query).select(ptable.id,
                           limitby=(0, 1)
                           ).first()
    if row:
        person_id = row.id
    else:
        person_id = None

    if person:
        if person_id:
            # @ToDo: deployment_setting for controller to use?
            person_url = URL(c="hrm", f="person", args=[person_id])
        else:
            person_url = "#"
        person = A(person,
                   _href=person_url,
                   )

    table = db.cms_post
    updateable = permit("update", table, record_id=record_id)

    # Toolbar
    if updateable:
        edit_btn = A(ICON("edit"),
                     SPAN("edit",
                          _class = "show-for-sr",
                          ),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}
                               ),
                     _class="s3_modal",
                     _title=T("Edit %(type)s") % dict(type=series_title),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       SPAN("delete",
                           _class = "show-for-sr",
                           ),
                      _class="dl-item-delete",
                      _title=T("Delete"),
                      )
    else:
        delete_btn = ""

    user = current.auth.user
    if user: #and settings.get_cms_bookmarks():
        ltable = s3db.cms_post_user
        query = (ltable.post_id == record_id) & \
                (ltable.user_id == user.id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            bookmark_btn = A(ICON("bookmark"),
                             SPAN("remove bookmark",
                                  _class = "show-for-sr",
                                  ),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "remove_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Remove Bookmark"),
                             )
        else:
            bookmark_btn = A(ICON("bookmark-empty"),
                             SPAN("bookmark",
                                  _class = "show-for-sr",
                                  ),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "add_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Add Bookmark"),
                             )
    else:
        bookmark_btn = ""

    divider = LI("|")
    divider["_aria-hidden"] = "true"

    toolbar = UL(LI(A(ICON("share"),
                      SPAN("share this",
                           _class = "show-for-sr",
                           ),
                      _href="#",
                      _title="Share",
                      ),
                    _class="item",
                    ),
                 LI(A(ICON("flag"), # @ToDo: Use flag-alt if not flagged & flag if already flagged (like for bookmarks)
                      SPAN("flag this",
                           _class = "show-for-sr",
                           ),
                      _href="#",
                      _title=T("Flag"),
                      ),
                    _class="item",
                    ),
                 LI(bookmark_btn,
                    _class="item",
                    ),
                 LI(A(I(_class="fa fa-users",
                        ),
                      SPAN("make public",
                           _class = "show-for-sr",
                           ),
                      _href="#",
                      _title=T("Make Public"),
                      ),
                    _class="item",
                    ),
                 LI(edit_btn,
                    _class="item",
                    ),
                 LI(delete_btn,
                    _class="item",
                    ),
                 _class="controls",
                 )

    #if settings.get_cms_show_tags():
    tag_list = UL(_class="left inline-list s3-tags",
                  )
    tag_list["_data-post_id"] = record_id
    tags = raw["cms_tag.name"]
    if tags:
        if not isinstance(tags, list):
            tags = [tags]
        for tag in tags:
            tag_list.append(LI(A(tag,
                                 _href="#",
                                 ),
                               ))

    item = TAG["ARTICLE"](TAG["HEADER"](UL(# post priority icon
                                           LI(_class="item icon",
                                              ),
                                           # post type title
                                           LI(series_title,
                                              _class="item primary",
                                              ),
                                           # post status
                                           LI(status,
                                              _class="item secondary border status",
                                              ),
                                           # post visibility
                                           # @ToDo: Read the visibility
                                           LI(T("Public"),
                                              _class="item secondary border visibility",
                                              ),
                                           _class="status-bar-left"
                                           ),
                                        toolbar,
                                        _class="status-bar",
                                        ),
                          DIV(P(TAG["TIME"](date),
                                " by ",
                                person,
                                " – ",
                                # @ToDo: Make comments work
                                A("0 Comments",
                                  #_href="#update-1-comments",
                                  ),
                                _class="dl-meta",
                                ),
                              P(body),
                              _class="dl-body",
                              ),
                          TAG["FOOTER"](tag_list,
                                        _class="footer",
                                        ),
                          _class="card-post",
                          _id=item_id,
                          )

    return item

# =============================================================================
def text_filter_formstyle(form, fields, *args, **kwargs):
    """
        Custom formstyle for S3TextFilter
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        controls = DIV(DIV(LABEL("Search:",
                                 _class="prefix",
                                 ),
                           _class="large-4 columns",
                           _for=widget[1].attributes["_name"],
                           ),
                       DIV(widget,
                           _class="large-8 columns",
                           ),
                       _class="row collapse prefix-radius",
                       _id=row_id,
                       )
        return controls

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# =============================================================================
def filter_formstyle_summary(form, fields, *args, **kwargs):
    """
        Custom formstyle for filters on the Incident Summary page
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        controls = FIELDSET(LEGEND(label),
                            widget,
                            )
        return DIV(controls, _id=row_id)

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# =============================================================================
def filter_formstyle_profile(form, fields, *args, **kwargs):
    """
        Custom formstyle for filters on the Incident Profile page
        - slightly tweaked formstyle_foundation_inline
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        if hasattr(widget, "element"):
            submit = widget.element("input", _type="submit")
            if submit:
                submit.add_class("small primary button")

        if isinstance(label, LABEL):
            label.add_class("left inline")

        controls_col = DIV(widget, _class="small-12 columns controls")
        if label:
            label_col = DIV(label, _class="medium-2 columns")
        else:
            label_col = ""
            #controls_col.add_class("medium-offset-2")

        if comment:
            comment = render_tooltip(label,
                                     comment,
                                     _class="inline-tooltip tooltip",
                                     )
            if hasattr(comment, "add_class"):
                comment.add_class("inline-tooltip")
            controls_col.append(comment)

        _class = "form-row row hide" if hidden else "form-row row"
        return DIV(label_col,
                   controls_col,
                   _class=_class, _id=row_id)

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# END =========================================================================
