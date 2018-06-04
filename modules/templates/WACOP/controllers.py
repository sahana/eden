# -*- coding: utf-8 -*-

import dateutil.parser
import json
from gluon import current#, Field, SQLFORM
from gluon.html import *
from gluon.http import HTTP
from gluon.storage import Storage
from s3 import FS, ICON, s3_auth_user_represent, \
               S3CRUD, S3CustomController, \
               S3DateFilter, S3DateTime, S3FilterForm, S3LocationFilter,\
               S3MapFilter, S3OptionsFilter, S3Request, S3TextFilter

THEME = "WACOP"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        custom = custom_WACOP()

        # Alerts Cards
        alerts = custom._alerts_html()

        # Events Cards
        events = custom._events_html()

        # Map of Incidents
        _map, button = custom._map("Incidents")

        # Output
        output = {"alerts": alerts,
                  "events": events,
                  "map": _map,
                  }

        # Incidents dataTable
        tablename = "event_incident"

        #ajax_vars = {"home": 1}
        customise = current.deployment_settings.customise_resource(tablename)
        if customise:
            r = S3Request(c="event", f="incident")#, vars=ajax_vars)
            customise(r, tablename)

        #current.deployment_settings.ui.datatables_pagingType = "bootstrap"
        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']
        custom._datatable(output = output,
                          tablename = tablename,
                          search = False,
                          updateable = False,
                          #ajax_vars = ajax_vars,
                          dt_init = dt_init,
                          )

        # View
        custom._view(output, "index.html")

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

        if r.representation == "html":
            return self._html(r, **attr)

        r.error(405, current.ERROR.BAD_METHOD)

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
                   output,
                   tablename,
                   search = True,
                   updateable = True,
                   export = False,
                   event_id = None,
                   forum_id = None,
                   incident_id = None,
                   actions = None,
                   ajax_vars = None, # Used to be able to differentiate contexts in customise()
                                     # & for filter_defaults
                   dt_init = None,
                   resource = None,
                   ):
        """
            Update output with a dataTable and a create_popup
            Update dt_init for the dataTable
        """

        T = current.T
        s3db = current.s3db

        c, f = tablename.split("_", 1)

        if ajax_vars is None:
            ajax_vars = {}
        if resource is None:
            resource = s3db.resource(tablename)
        if event_id:
            ltablename = "event_%s" % f
            if tablename == ltablename:
                # Need simplified selector for some reason
                resource.add_filter(FS("event_id") == event_id)
                ajax_vars["~.event_id"] = event_id
            else:
                resource.add_filter(FS("event_%s.event_id" % f) == event_id)
                ajax_vars["event_%s.event_id" % f] = event_id
        elif incident_id:
            ltablename = "event_%s" % f
            if tablename == ltablename:
                # Need simplified selector for some reason
                resource.add_filter(FS("incident_id") == incident_id)
                ajax_vars["~.incident_id"] = incident_id
            else:
                resource.add_filter(FS("event_%s.incident_id" % f) == incident_id)
                ajax_vars["event_%s.incident_id" % f] = incident_id
        elif forum_id:
            if tablename == "pr_forum_membership":
                resource.add_filter(FS("forum_id") == forum_id)
                ajax_vars["~.forum_id"] = forum_id
            elif tablename == "project_task":
                resource.add_filter(FS("task_forum.forum_id") == forum_id)
                ajax_vars["task_forum.forum_id"] = forum_id

        dataTable_id = "custom-list-%s" % tablename

        if dt_init:
            if search:
                # Move the search boxes into the design
                dt_init.append('''$('#dt-%(tablename)s .dataTables_filter').prependTo($('#dt-search-%(tablename)s'));$('#dt-search-%(tablename)s .dataTables_filter input').attr('placeholder','%(placeholder)s').attr('name','%(tablename)s-search').prependTo($('#dt-search-%(tablename)s .dataTables_filter'));$('#dt-search-%(tablename)s .dataTables_filter').removeClass('dataTables_filter');''' % \
                    dict(tablename = tablename,
                         placeholder = T("Search"),
                         ))
            current.deployment_settings.ui.datatables_initComplete = "".join(dt_init)

        # Get the data table
        displayLength = 10
        if export:
            current.response.s3.no_formats = False
        else:
            current.response.s3.no_formats = True
        get_config = s3db.get_config # Customise these inside customise() functions as-required
        list_fields = get_config(tablename, "list_fields")
        orderby = get_config(tablename, "orderby")
        dt, totalrows = resource.datatable(fields = list_fields,
                                           start = 0,
                                           limit = 2 * displayLength,
                                           orderby = orderby,
                                           )
        displayrows = totalrows

        if dt.empty:
            empty_str = self.crud_string(tablename,
                                         "msg_list_empty")
        else:
            empty_str = self.crud_string(tablename,
                                         "msg_no_match")
        empty = DIV(empty_str, _class="empty")

        dtargs = {"dt_pagination": "true",
                  "dt_pageLength": displayLength,
                  #"dt_lengthMenu": None,
                  }
        if not search:
            dtargs["dt_searching"] = False

        # Action Buttons
        # @ToDo: Permissions
        #messages = current.messages
        #if f in ("event", "incident"):
        #    profile = "custom"
        #else:
        #    profile = "profile"
        #if event_id and f != "incident":
        #    read_url = URL(c="event", f="event",
        #                   args=[event_id, f, "[id]", profile])
        #    delete_url = URL(c="event", f="event",
        #                     args=[event_id, f, "[id]", "delete"])
        #elif incident_id:
        #    read_url = URL(c="event", f="incident",
        #                   args=[incident_id, f, "[id]", profile])
        #    delete_url = URL(c="event", f="incident",
        #                     args=[incident_id, f, "[id]", "delete"])
        #else:
        #    read_url = URL(c=c, f=f,
        #                   args = ["[id]", profile])
        #    delete_url = URL(c=c, f=f,
        #                     args=["[id]", "delete"])
        if actions is None:
            # Hide the Action Buttons as we assume that the first column is clickable to open details
            actions = [{#"label": messages.READ,
                        "label": "",
                        #"url": read_url,
                        "url": "",
                        ##"icon": "fa fa-eye",
                        # "icon": "fa fa-caret-right",
                        # #"_class": "s3_modal",
                        },
                        # @ToDo: AJAX delete
                        #{"label": messages.DELETE,
                        # "url": delete_url,
                        # "icon": "fa fa-trash",
                        # },
                       ]
        dtargs["dt_row_actions"] = actions
        # Action Buttons on the right (no longer)
        #dtargs["dt_action_col"] = len(list_fields)

        if tablename == "pr_forum_membership":
            # Use Native controller for AJAX calls
            dtargs["dt_ajax_url"] = URL(c = "pr",
                                        f = "forum",
                                        args = [forum_id, "forum_membership"],
                                        #vars = ajax_vars,
                                        extension = "aadata",
                                        )
        else:
            # Use Native controller for AJAX calls
            dtargs["dt_ajax_url"] = URL(c = c,
                                        f = f,
                                        vars = ajax_vars,
                                        extension = "aadata",
                                        )

        datatable = dt.html(totalrows,
                            displayrows,
                            id = dataTable_id,
                            **dtargs)

        if dt.data:
            empty.update(_style="display:none")
        else:
            datatable.update(_style="display:none")
        contents = DIV(datatable, empty, _class="dt-contents")

        # Link for create-popup
        if updateable and current.auth.s3_has_permission("create", tablename):
            if tablename == "event_human_resource":
                label = T("Assign Staff")
                if event_id:
                    url = URL(c="event", f="event",
                              args=[event_id, "assign.popup"],
                              vars={"refresh": dataTable_id},
                              )
                else:
                    url = URL(c="event", f="incident",
                              args=[incident_id, "assign.popup"],
                              vars={"refresh": dataTable_id},
                              )
            elif tablename == "pr_forum_membership":
                label = T("Add Member")
                url = URL(c="pr", f="forum",
                          args=[forum_id, f, "create.popup"],
                          vars={"refresh": dataTable_id},
                          )
            else:
                if event_id:
                    if f == "team":
                        f = "group"
                    url = URL(c="event", f="event",
                              args=[event_id, f, "create.popup"],
                              vars={"refresh": dataTable_id},
                              )
                elif incident_id:
                    if f == "team":
                        f = "group"
                    url = URL(c="event", f="incident",
                              args=[incident_id, f, "create.popup"],
                              vars={"refresh": dataTable_id},
                              )
                elif forum_id:
                    url = URL(c="pr", f="forum",
                              args=[forum_id, f, "create.popup"],
                              vars={"refresh": dataTable_id},
                              )
                else:
                    url = URL(c=c, f=f,
                              args=["create.popup"],
                              vars={"refresh": dataTable_id},
                              )
                if tablename == "event_organisation":
                    label = T("Add Organization")
                elif tablename == "project_task":
                    label = T("Create Task")
                elif tablename == "pr_forum":
                    label = T("Create Group")
                else:
                    # event_team
                    label = T("Add")
            output["create_%s_popup" % tablename] = \
                DIV(A(TAG[""](ICON("plus"),
                              label,
                              ),
                      _href = url,
                      _class = "button wide radius s3_modal",
                      _title = label,
                      ),
                    _class = "panel"
                    )
        else:
            output["create_%s_popup" % tablename] = ""

        # Render the widget
        output["%s_datatable" % tablename] = contents

    # -------------------------------------------------------------------------
    def _map(self, layer_name, map_id="default_map", filter=None):
        """
            Create the HTML for a Map section

            @param layer_name: the name of the Layer
            @param map_id: the id of the map
            @param filter: True for an S3MapFilter, otherwise optional filter string for the layer
        """

        s3 = current.response.s3
        jqrappend = s3.jquery_ready.append

        if filter is True and current.deployment_settings.get_gis_spatialdb():
            # Using S3MapFilter
            _map = None

            button = A("DRAW A MAP AREA",
                       _class="button wide",
                       _id="map_filter_button",
                       )

            # Move Map into the Design
            jqrappend('''$('#%s').appendTo($('#map-here'))''' % map_id)

            # Apply custom design to the S3MapFilter
            s3.scripts.append("/%s/static/themes/WACOP/js/map_filter.js" % current.request.application)
            jqrappend('''S3.wacop_mapFilter('%s')''' % map_id)

        else:
            # Map without S3MapFilter
            button = None

            ltable = current.s3db.gis_layer_feature
            layer = current.db(ltable.name == layer_name).select(ltable.layer_id,
                                                                 limitby=(0, 1)
                                                                 ).first()
            try:
                layer_id = layer.layer_id
            except:
                # No prepop done?
                layer_id = None
            feature_resources = [{"name"     : current.T(layer_name),
                                  "id"       : "search_results",
                                  "layer_id" : layer_id,
                                  "filter"   : filter,
                                  },
                                 ]
            _map = current.gis.show_map(id = map_id,
                                        height = 350,
                                        width = 425,
                                        collapsed = True,
                                        callback='''S3.search.s3map('%s')''' % map_id,
                                        feature_resources = feature_resources,
                                        #toolbar = True,
                                        #add_polygon = True,
                                        )

        # Resize the map to match the height of the Filter Form
        jqrappend('''S3.wacop_resizeMap('%s')''' % map_id)

        return _map, button

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
                if path and "/" in path:
                    L1 = path.split("/")[1]
                    query = (gttable.location_id == L1) & \
                            (gttable.tag == "state")
                    L1_abrv = db(query).select(gttable.value,
                                               limitby=(0, 1),
                                               ).first().value
                    L3 = row["gis_location.L3"]
                    lat = row["gis_location.lat"]
                    lon = row["gis_location.lon"]
                    location_full = "%s, %s; %s, %s" % (L3, L1_abrv, lat, lon)
                else:
                    # No location or national
                    location_full = T("No Address Given")
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
                                                     SPAN(location_full,
                                                          _class="meta-location",
                                                          ),
                                                     ),
                                                   DIV(row["cms_post.body"],
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
                                                     args="browse",
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
                                              args = ["%s.popup" % record_id, "update"],
                                              vars = {"refresh": 1},
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
                    addr_street = T("No Address Given")
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
                                                   P(meta + " ",
                                                     A(T("Read More"),
                                                       _href=URL(c="event", f="event",
                                                                 args=[record_id, "custom"],
                                                                 ),
                                                       _class="more",
                                                       ),
                                                     _class="meta",
                                                     ),
                                                   DIV(row["event_event.comments"],
                                                       _class="desc",
                                                       ),
                                                   _class="body",
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
        query = (table.name == "SYSTEM_WIDE") & \
                (table.deleted == False)
        record = current.db(query).select(table.body,
                                          limitby=(0, 1)
                                          ).first()
        if record or ADMIN:
            if ADMIN:
                if record:
                    label = current.T("Edit System-wide Alert")
                else:
                    label = current.T("Create System-wide Alert")
                edit_btn = P(A(label,
                               _href = URL(c="cms", f="post",
                                           args = "create",
                                           vars = {"page": "SYSTEM_WIDE"},
                                           ),
                               _class = "button button-info",
                               ),
                             _class = "callout-right text-right",
                             )
            else:
                edit_btn = ""
            content = record and record.body or ""
            if content:
                content = XML(content)
            system_wide = DIV(DIV(DIV(P(content,
                                        ),
                                      _class="callout-left",
                                      ),
                                  edit_btn,
                                  _role="complementary",
                                 _class="callout",
                                 ),
                              _class="row well",
                              )
        else:
            # Don't display the section
            system_wide = ""

        return system_wide

    # -------------------------------------------------------------------------
    def _tasks_html(self,
                    r,
                    output,
                    updateable = True,
                    event_id = None,
                    incident_id = None,
                    forum_id = None,
                    dt_init = None,
                    ):
        """
            Create the HTML for the Tasks section

            @param r: the S3Request
        """

        tablename = "project_task"
        dataTable_id = "custom-list-%s" % tablename
        ajax_vars = {#"list_id": dataTable_id,
                     #"refresh": dataTable_id,
                     }

        s3db = current.s3db
        resource = s3db.resource(tablename)
        if event_id:
            # Done by _datatable
            #resource.add_filter(FS("event_task.event_id") == event_id)
            ajax_vars["event_task.event_id"] = event_id
        elif incident_id:
            # Done by _datatable
            #resource.add_filter(FS("event_task.incident_id") == incident_id)
            ajax_vars["event_task.incident_id"] = incident_id
        elif forum_id:
            # Done by _datatable
            #resource.add_filter(FS("task_forum.forum_id") == forum_id)
            ajax_vars["task_forum.forum_id"] = forum_id
        ajaxurl = URL(c="project", f="task", args="datatable",
                      vars=ajax_vars, extension="aadata")

        customise = current.deployment_settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        default_filters = S3FilterForm.apply_filter_defaults(r, resource)

        self._datatable(output = output,
                        tablename = tablename,
                        search = False,
                        updateable = updateable,
                        event_id = event_id,
                        incident_id = incident_id,
                        forum_id = forum_id,
                        ajax_vars = default_filters,
                        dt_init = dt_init,
                        resource = resource,
                        )

        # Filter Form
        # Widgets defined in customise() to be visible to filter.options
        filter_widgets = s3db.get_config(tablename, "filter_widgets")

        #ajax_vars.pop("list_id")
        #ajax_vars.pop("refresh")
        filter_form = S3FilterForm(filter_widgets,
                                   formstyle = filter_formstyle_profile,
                                   submit = True,
                                   ajax = True,
                                   url = ajaxurl,
                                   # Ensure that Filter options update when
                                   # entries are added/modified
                                   # => done through target-parameter in html() now,
                                   #    but /a/ form ID is still required for other
                                   #    scripts and styles
                                   _id = "%s-filter-form" % dataTable_id,
                                   ajaxurl = URL(c="project", f="task",
                                                 args = ["filter.options"],
                                                 vars = ajax_vars, # manually applied to s3.filter in customise()
                                                 ),
                                   )

        output["project_task_filter_form"] = filter_form.html(resource, r.get_vars,
                                                              target = dataTable_id,
                                                              alias = None,
                                                              )

    # -------------------------------------------------------------------------
    def _updates_html(self, r, output,
                      event_id = None,
                      incident_id = None,
                      forum_id = None,
                      updateable = True,
                      **attr):
        """
            Create the HTML for the Updates section

            @param r: the S3Request
            @param attr: controller arguments
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        list_id = "updates_datalist"
        ajax_vars = {"list_id": list_id,
                     #"refresh": list_id,
                     }

        tablename = "cms_post"
        resource = s3db.resource(tablename)
        if event_id:
            resource.add_filter(FS("event_post.event_id") == event_id)
            ajax_vars["event_post.event_id"] = event_id
        elif incident_id:
            resource.add_filter(FS("event_post.incident_id") == incident_id)
            ajax_vars["event_post.incident_id"] = incident_id
        elif forum_id:
            resource.add_filter(group_filter(forum_id))
            ajax_vars["forum"] = forum_id
        elif r.method == "dashboard":
            resource.add_filter(dashboard_filter())
            ajax_vars["dashboard"] = 1
        ajaxurl = URL(c="cms", f="post", args="datalist",
                      vars=ajax_vars, extension="dl")

        customise = current.deployment_settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        # list_fields defined in customise() to be DRY
        list_fields = s3db.get_config(tablename, "list_fields")

        datalist, numrows = resource.datalist(fields = list_fields,
                                              start = None,
                                              limit = 5,
                                              list_id = list_id,
                                              # This is the default but needs specifying when talking direct to the back-end
                                              orderby = "cms_post.date desc",
                                              layout = cms_post_list_layout,
                                              )

        s3.dl_no_header = True

        #if numrows == 0:
        #    # Empty table or just no match?
        #    ptable = s3db.cms_post
        #    if "deleted" in ptable:
        #        available_records = db(ptable.deleted != True)
        #    else:
        #        available_records = db(ptable._id > 0)
        #    if available_records.select(ptable._id,
        #                                limitby=(0, 1)).first():
        #        msg = DIV(self.crud_string(tablename,
        #                                   "msg_no_match"),
        #                  _class="empty")
        #    else:
        #        msg = DIV(self.crud_string(tablename,
        #                                   "msg_list_empty"),
        #                  _class="empty")
        #    data = msg
        #else:
        # Render the list
        # - do this anyway to ensure 1st-added update refreshes the list
        data = datalist.html(pagesize = 5,
                             ajaxurl = ajaxurl,
                             )

        # Render the widget
        output["updates_datalist"] = data

        # Filter Form
        # Widgets defined in customise() to be visible to filter.options
        filter_widgets = s3db.get_config(tablename, "filter_widgets")

        ajax_vars.pop("list_id")
        #ajax_vars.pop("refresh")
        filter_form = S3FilterForm(filter_widgets,
                                   formstyle = filter_formstyle_profile,
                                   submit = True,
                                   ajax = True,
                                   url = ajaxurl,
                                   # Ensure that Filter options update when
                                   # entries are added/modified
                                   # => done through target-parameter in html() now,
                                   #    but /a/ form ID is still required for other
                                   #    scripts and styles
                                   _id = "%s-filter-form" % list_id,
                                   ajaxurl = URL(c="cms", f="post",
                                                 args = ["filter.options"],
                                                 vars = ajax_vars, # manually applied to s3.filter in customise()
                                                 ),
                                   )

        #get_vars = r.get_vars
        #if forum_id:
        #    get_vars = dict((k, v) for k, v in get_vars.items())
        #    eftable = s3db.event_forum
        #    base_query = (eftable.forum_id == forum_id)
        #    etable = s3db.event_event
        #    query = base_query & (eftable.event_id == etable.id)
        #    events = db(query).select(etable.id)
        #    events = [e.id for e in events]
        #    if events:
        #        get_vars["event_post.event_id__belongs"] = events
        #    itable = s3db.event_incident
        #    query = base_query & (eftable.incident_id == itable.id)
        #    incidents = db(query).select(itable.id)
        #    incidents = [i.id for i in incidents]
        #    if incidents:
        #        get_vars["event_post.incident_id__belongs"] = incidents

        output["filter_form"] = filter_form.html(resource, r.get_vars,
                                                 target = list_id,
                                                 alias = None,
                                                 )

        #  Create Form for Updates
        has_permission = current.auth.s3_has_permission
        if updateable and has_permission("create", tablename):
            if event_id:
                url = URL(c="event", f="event",
                          args = [event_id, "post", "create.popup"],
                          vars={"refresh": list_id},
                          )
            elif incident_id:
                url = URL(c="event", f="incident",
                          args = [incident_id, "post", "create.popup"],
                          vars={"refresh": list_id},
                          )
            elif forum_id:
                url = URL(c="pr", f="forum",
                          args = [forum_id, "post", "create.popup"],
                          vars={"refresh": list_id},
                          )
            elif r.method == "dashboard":
                url = URL(c="cms", f="post",
                          args = ["create.popup"],
                          vars={"dashboard": 1,
                                "refresh": list_id,
                                },
                          )
            else:
                url = URL(c="cms", f="post",
                          args = ["create.popup"],
                          vars={"refresh": list_id},
                          )
            output["create_post_button"] = DIV(A(ICON("add"),
                                                 T("Add Update"),
                                                 _href=url,
                                                 _class="s3_modal button wide radius",
                                                 ),
                                               _class="panel",
                                               )
        else:
            output["create_post_button"] = ""

        appname = r.application

        # Comments for Updates
        s3.scripts.append("/%s/static/themes/WACOP/js/update_comments.js" % appname)
        script = '''S3.wacop_comments()
S3.redraw_fns.push('wacop_comments')'''
        s3.jquery_ready.append(script)

        # Tags for Updates
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/tag-it.js" % appname)
        else:
            s3.scripts.append("/%s/static/scripts/tag-it.min.js" % appname)
        if has_permission("update", s3db.cms_tag_post):
            # @ToDo: Move the ajaxUpdateOptions into callback of getS3?
            readonly = '''afterTagAdded:function(event,ui){
if(ui.duringInitialization){return}
var post_id=$(this).attr('data-post_id')
var url=S3.Ap.concat('/cms/post/',post_id,'/add_tag/',ui.tagLabel)
$.getS3(url)
S3.search.ajaxUpdateOptions('#updates_datalist-filter-form')
},afterTagRemoved:function(event,ui){
var post_id=$(this).attr('data-post_id')
var url=S3.Ap.concat('/cms/post/',post_id,'/remove_tag/',ui.tagLabel)
$.getS3(url)
S3.search.ajaxUpdateOptions('#updates_datalist-filter-form')
},'''
        else:
            readonly = '''readOnly:true'''
        script = \
'''S3.tagit=function(){$('.s3-tags').tagit({placeholderText:'%s',autocomplete:{source:'%s'},%s})}
S3.tagit()
S3.redraw_fns.push('tagit')''' % (T("Add tags here…"),
                                  URL(c="cms", f="tag",
                                      args="tag_list.json"),
                                  readonly)
        s3.jquery_ready.append(script)

        return numrows

    # -------------------------------------------------------------------------
    def _view(self, output, view):
        """
            Apply the View, with all things which have to be on every page

            @param output: the output dict
            @param view: view template
        """

        current.menu.options = None

        appname = current.request.application
        s3 = current.response.s3
        scripts_append = s3.scripts.append
        jqready_append = s3.jquery_ready.append

        scripts_append("/%s/static/themes/WACOP/js/bookmarks.js" % appname)
        jqready_append('''S3.wacop_bookmarks()
S3.redraw_fns.push('wacop_bookmarks')''')

        scripts_append("/%s/static/themes/WACOP/js/shares.js" % appname)
        jqready_append('''S3.wacop_shares()
S3.redraw_fns.push('wacop_shares')''')

        # System-wide Message
        output["system_wide"] = self._system_wide_html()

        S3CustomController._view(THEME, view)

# =============================================================================
class event_Browse(custom_WACOP):
    """
        Custom browse page for Events
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        T = current.T

        # Alerts Cards
        alerts = self._alerts_html()

        # Events Cards
        events = self._events_html()

        # Map of Events
        map_id = "event-gis_location_the_geom-map-filter-map"
        _map, button = self._map("Events", map_id=map_id, filter=True)

        # Output
        output = {"alerts": alerts,
                  "events": events,
                  "_map": _map,
                  }

        tablename = "event_event"
        form_id = "%s-filter-form" % tablename

        # Report
        method = "report"
        report_widget_id = "event_event_report"
        handler = r.get_widget_handler(method)
        content = handler(r,
                          method = method,
                          widget_id = report_widget_id,
                          visible = False,
                          **attr)
        output["event_event_report"] = content
        jqr_append = current.response.s3.jquery_ready.append
        jqr_append('''S3.search.setup_hidden_widget('%s','%s')''' % (form_id, report_widget_id))
        jqr_append('''$(document).foundation({tab:{callback:function(tab){S3.search.unhide_section('%s',tab)}}})''' % form_id)

        # Filter Form
        date_filter = S3DateFilter(["start_date", "end_date"],
                                   label = "",
                                   #hide_time = True,
                                   slider = True,
                                   clear_text = "X",
                                   )
        date_filter.input_labels = {"ge": "Start Time/Date", "le": "End Time/Date"}

        filter_widgets = [S3TextFilter(["name",
                                        "comments",
                                        ],
                                       formstyle = text_filter_formstyle,
                                       label = T("Search"),
                                       _placeholder = T("Enter search term…"),
                                       ),
                          S3LocationFilter("event_location.location_id",
                                           label = "",
                                           #label = T("City"),
                                           widget = "multiselect",
                                           #levels = ("L1", "L2", "L3"),
                                           levels = ("L3",),
                                           ),
                          S3MapFilter("event_location.location_id$the_geom",
                                      label = "",
                                      button = button,
                                      ),
                          S3OptionsFilter("tag.tag_id",
                                          label = "",
                                          noneSelectedText = "Tag",
                                          no_opts = "",
                                          ),
                          S3OptionsFilter("status",
                                          label = "",
                                          noneSelectedText = "Status",
                                          no_opts = "",
                                          ),
                          date_filter,
                          ]

        user = current.auth.user
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
                                   submit = True,
                                   ajax = True,
                                   url = URL(args=["browse.dl"],
                                             vars={}),
                                   ajaxurl = URL(c="event", f="event",
                                                 args=["filter.options"], vars={}),
                                   _id = form_id,
                                   )
        output["filter_form"] = filter_form.html(r.resource, r.get_vars,
                                                 # Map & dataTable
                                                 target = "%s custom-list-event_event" % map_id,
                                                 alias = None
                                                 )

        # Events dataTable

        #ajax_vars = {"browse": 1}
        # Run already by the controller:
        #customise = current.deployment_settings.customise_resource(tablename)
        #if customise:
        #    customise(r, tablename)

        self._datatable(output = output,
                        tablename = tablename,
                        search = False,
                        updateable = False,
                        export = True,
                        #ajax_vars = ajax_vars,
                        )

        output["title"] = T("Events")
        self._view(output, "event_browse.html")

        return output

# =============================================================================
class group_Browse(custom_WACOP):
    """
        Custom browse page for Groups
        - modelled as pr_forum
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        from s3 import s3_str

        T = current.T
        db = current.db
        s3db = current.s3db

        output = {}

        # dataTable (& Create button)
        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']
        tablename = "pr_forum"

        customise = current.deployment_settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        # Lookup person_id of current user
        ptable = s3db.pr_person
        person_id = db(ptable.pe_id == current.auth.user.pe_id).select(ptable.id,
                                                                       limitby = (0, 1)
                                                                       ).first().id

        # Action Buttons
        table = r.table
        mtable = s3db.pr_forum_membership
        # Groups that the User is a Member of
        query = (table.deleted == False) & \
                (table.id == mtable.forum_id) & \
                (mtable.person_id == person_id) & \
                (mtable.deleted == False)
        groups = db(query).select(table.id)
        groups_member_of = [g.id for g in groups]
        restrict_l = [str(g) for g in groups_member_of]
        # Public Groups that the User is not a Member of
        query = (table.forum_type.belongs((1, 2))) & \
                (~table.id.belongs(groups_member_of)) & \
                (table.deleted == False)
        groups = db(query).select(table.id,
                                  table.forum_type)
        restrict_j = [str(g.id) for g in groups if g.forum_type == 1]
        # Private Groups that the User is not a Member of
        restrict_r = [str(g.id) for g in groups if g.forum_type == 2]

        actions = [dict(label = s3_str(T("Join")),
                        url = URL(args=["[id]", "join"]),
                        _class = "action-btn",
                        restrict = restrict_j,
                        ),
                   dict(label = s3_str(T("Leave")),
                        url = URL(args = ["[id]", "leave"]),
                        _class = "action-btn",
                        restrict = restrict_l,
                        ),
                   dict(label = s3_str(T("Request Invite")),
                        url = URL(args = ["[id]", "request"]),
                        _class = "action-btn",
                        restrict = restrict_r,
                        ),
                   ]

        resource = r.resource
        self._datatable(output = output,
                        tablename = tablename,
                        actions = actions,
                        dt_init = dt_init,
                        resource = resource,
                        search = False,
                        )

        # Filter Form
        ajax_vars = {}
        ajaxurl = URL(c="pr", f="forum", args="datatable",
                      vars=ajax_vars, extension="aadata")
        dataTable_id = "custom-list-pr_forum"
        # Widgets defined in customise() to be visible to filter.options
        filter_widgets = current.s3db.get_config(tablename, "filter_widgets")

        #ajax_vars.pop("list_id")
        #ajax_vars.pop("refresh")
        filter_form = S3FilterForm(filter_widgets,
                                   formstyle = filter_formstyle_profile,
                                   submit = True,
                                   ajax = True,
                                   url = ajaxurl,
                                   # Ensure that Filter options update when
                                   # entries are added/modified
                                   # => done through target-parameter in html() now,
                                   #    but /a/ form ID is still required for other
                                   #    scripts and styles
                                   _id = "%s-filter-form" % dataTable_id,
                                   ajaxurl = URL(c="pr", f="forum",
                                                 args = ["filter.options"],
                                                 vars = ajax_vars, # would be manually applied to s3.filter in customise()
                                                 ),
                                   )

        output["filter_form"] = filter_form.html(resource, r.get_vars,
                                                 target = dataTable_id,
                                                 alias = None,
                                                 )

        output["title"] = T("Groups")
        self._view(output, "group_browse.html")

        return output

# =============================================================================
class incident_Browse(custom_WACOP):
    """
        Custom browse page for Incidents
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        T = current.T

        # Alerts Cards
        #alerts = self._alerts_html()

        # Events Cards
        #events = self._events_html()

        # Map of Incidents
        map_id = "incident-gis_location_the_geom-map-filter-map"
        _map, button = self._map("Incidents", map_id=map_id, filter=True)

        # Output
        output = {#"alerts": alerts,
                  #"events": events,
                  "_map": _map,
                  }

        tablename = "event_incident"
        form_id = "%s-filter-form" % tablename

        # Report
        method = "report"
        report_widget_id = "event_incident_report"
        handler = r.get_widget_handler(method)
        content = handler(r,
                          method = method,
                          widget_id = report_widget_id,
                          visible = False,
                          **attr)
        output["event_incident_report"] = content
        jqr_append = current.response.s3.jquery_ready.append
        jqr_append('''S3.search.setup_hidden_widget('%s','%s')''' % (form_id, report_widget_id))
        jqr_append('''$(document).foundation({tab:{callback:function(tab){S3.search.unhide_section('%s',tab)}}})''' % form_id)

        # Filter Form
        date_filter = S3DateFilter(["date", "end_date"],
                                   label = "",
                                   #hide_time = True,
                                   slider = True,
                                   clear_text = "X",
                                   )
        date_filter.input_labels = {"ge": "Start Time/Date", "le": "End Time/Date"}

        filter_widgets = [S3TextFilter(["name",
                                        "comments",
                                        ],
                                       formstyle = text_filter_formstyle,
                                       label = T("Search"),
                                       _placeholder = T("Enter search term…"),
                                       ),
                          S3LocationFilter("location_id",
                                           label = "",
                                           #label = T("City"),
                                           widget = "multiselect",
                                           #levels = ("L1", "L2", "L3"),
                                           levels = ("L3",),
                                           no_opts = "",
                                           ),
                          S3MapFilter("location_id$the_geom",
                                      label = "",
                                      button = button,
                                      ),
                          S3OptionsFilter("tag.tag_id",
                                          label = "",
                                          noneSelectedText = "Tag",
                                          no_opts = "",
                                          ),
                          S3OptionsFilter("source",
                                          label = "",
                                          noneSelectedText = "Source",
                                          no_opts = "",
                                          ),
                          S3OptionsFilter("status",
                                          label = "",
                                          noneSelectedText = "Status",
                                          no_opts = "",
                                          ),
                          S3OptionsFilter("incident_type_id",
                                          label = "",
                                          noneSelectedText = "Incident Type",
                                          no_opts = "",
                                          ),
                          #S3OptionsFilter("organisation_id",
                          #                label = "",
                          #                noneSelectedText = "Agency",
                          #                no_opts = "",
                          #                ),
                          S3OptionsFilter("group.organisation_team.organisation_id",
                                          label = "",
                                          noneSelectedText = "Organization",
                                          no_opts = "",
                                          ),
                          date_filter,
                          ]

        user = current.auth.user
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
                                   submit = True,
                                   ajax = True,
                                   url = URL(args=["browse.dl"],
                                             vars={}),
                                   ajaxurl = URL(c="event", f="incident",
                                                 args=["filter.options"], vars={}),
                                   _id = form_id,
                                   )
        output["filter_form"] = filter_form.html(r.resource, r.get_vars,
                                                 # Map, dataTable & Report
                                                 target = "%s custom-list-event_incident %s" % (map_id, report_widget_id),
                                                 alias = None
                                                 )

        # Incidents dataTable

        ajax_vars = {"browse": 1}
        # Run already by the controller:
        #customise = current.deployment_settings.customise_resource(tablename)
        #if customise:
        #    customise(r, tablename)

        # For debugging Map, replace the dataTable with this:
        #output["event_incident_datatable"] = ""
        self._datatable(output = output,
                        tablename = tablename,
                        search = False,
                        updateable = False,
                        export = True,
                        ajax_vars = ajax_vars,
                        )

        output["title"] = T("Incidents")
        self._view(output, "incident_browse.html")

        return output

# =============================================================================
class resource_Browse(custom_WACOP):
    """
        Custom browse page for Resources
        - modelled as pr_group as they are typically teams
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        T = current.T

        # Alerts Cards
        #alerts = self._alerts_html()

        # Events Cards
        #events = self._events_html()

        # Map of Resources
        map_id = "group-gis_location_the_geom-map-filter-map"
        _map, button = self._map("Resources", map_id=map_id, filter=True)

        # Output
        output = {#"alerts": alerts,
                  #"events": events,
                  "_map": _map,
                  }

        tablename = "pr_group"
        form_id = "%s-filter-form" % tablename

        # Report
        method = "report"
        report_widget_id = "pr_group_report"
        handler = r.get_widget_handler(method)
        content = handler(r,
                          method = method,
                          widget_id = report_widget_id,
                          visible = False,
                          **attr)
        output["pr_group_report"] = content
        jqr_append = current.response.s3.jquery_ready.append
        jqr_append('''S3.search.setup_hidden_widget('%s','%s')''' % (form_id, report_widget_id))
        jqr_append('''$(document).foundation({tab:{callback:function(tab){S3.search.unhide_section('%s',tab)}}})''' % form_id)

        # Filter Form
        filter_widgets = [S3TextFilter(["name",
                                        "comments",
                                        ],
                                       formstyle = text_filter_formstyle,
                                       label = T("Search"),
                                       _placeholder = T("Enter search term…"),
                                       ),
                          S3LocationFilter("location_id",
                                           label = "",
                                           #label = T("City"),
                                           widget = "multiselect",
                                           #levels = ("L1", "L2", "L3"),
                                           levels = ("L3",),
                                           no_opts = "",
                                           ),
                          S3MapFilter("location_id$the_geom",
                                      label = "",
                                      button = button,
                                      ),
                          S3OptionsFilter("organisation_team.organisation_id",
                                          label = "",
                                          noneSelectedText = "Organization",
                                          no_opts = "",
                                          ),
                          S3OptionsFilter("source",
                                          label = "",
                                          noneSelectedText = "Source",
                                          no_opts = "",
                                          ),
                          S3OptionsFilter("status_id",
                                          label = "",
                                          noneSelectedText = "Status",
                                          no_opts = "",
                                          ),
                          ]

        filter_form = S3FilterForm(filter_widgets,
                                   formstyle = filter_formstyle_profile,
                                   submit = True,
                                   ajax = True,
                                   #url = URL(args=["browse.dl"],
                                   #          vars={}),
                                   ajaxurl = URL(c="pr", f="group",
                                                 args=["filter.options"], vars={}),
                                   _id = form_id,
                                   )
        output["filter_form"] = filter_form.html(r.resource, r.get_vars,
                                                 # Map, dataTable & Report
                                                 # We also want to filter the Active Resources datatable, however the selectors don't match for that
                                                 #custom-list-event_team
                                                 target = "%s custom-list-pr_group %s" % (map_id, report_widget_id),
                                                 alias = None
                                                 )

        # DataTables
        datatable = self._datatable
        #current.deployment_settings.ui.datatables_pagingType = "bootstrap"

        # Resources dataTable

        #ajax_vars = {"browse": 1}
        # Run already by the controller:
        #customise = current.deployment_settings.customise_resource(tablename)
        #if customise:
        #    customise(r, tablename)

        # For debugging Map, replace the dataTable with this:
        #output["pr_group_datatable"] = ""
        datatable(output = output,
                  tablename = tablename,
                  search = False,
                  updateable = False,
                  export = True,
                  #ajax_vars = ajax_vars,
                  )

        # Active Resources dataTable
        tablename = "event_team"

        customise = current.deployment_settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

        datatable(output = output,
                  tablename = tablename,
                  search = False,
                  updateable = False,
                  dt_init = dt_init,
                  )

        output["title"] = T("Resources")
        self._view(output, "resource_browse.html")

        return output

# =============================================================================
class event_Profile(custom_WACOP):
    """
        Custom profile page for Events
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        event_id = r.id

        T = current.T
        auth = current.auth
        db = current.db
        s3db = current.s3db
        settings = current.deployment_settings

        etable = s3db.event_event
        itable = s3db.event_incident
        ertable = s3db.event_team
        eptable = s3db.event_post

        date_represent = lambda dt: S3DateTime.date_represent(dt,
                                                              format = "%b %d %Y %H:%M",
                                                              utc = True,
                                                              #calendar = calendar,
                                                              )

        # Map of Incidents
        _map, button = self._map("Incidents", filter="~.event_id=%s" % event_id)

        # Output
        output = {"event_id": event_id,
                  "map": _map,
                  }

        # Event Details
        updateable = auth.s3_has_permission("update", etable, record_id=event_id, c="event", f="event")
        output["updateable"] = updateable

        user = auth.user
        if user:
            user_id = user.id
            ltable = s3db.event_bookmark
            query = (ltable.event_id == event_id) & \
                    (ltable.user_id == user_id)
            exists = db(query).select(ltable.id,
                                      limitby=(0, 1)
                                      ).first()
            if exists:
                bookmark = A(ICON("bookmark"),
                             _title=T("Remove Bookmark"),
                             _class="bookmark",
                             )
            else:
                bookmark = A(ICON("bookmark-empty"),
                             _title=T("Add Bookmark"),
                             _class="bookmark",
                             )
            bookmark["_data-c"] = "event"
            bookmark["_data-f"] = "event"
            bookmark["_data-i"] = event_id
            # Done globally in _view
            #script = '''S3.wacop_bookmarks()'''
            #s3.jquery_ready.append(script)
        else:
            bookmark = ""
        output["bookmark_btn"] = bookmark

        if user:
            ptable = s3db.pr_person
            mtable = s3db.pr_forum_membership
            ftable = s3db.pr_forum
            query = (ptable.pe_id == user.pe_id) & \
                    (ptable.id == mtable.person_id) & \
                    (mtable.forum_id == ftable.id)
            forums = db(query).select(ftable.id,
                                      ftable.name,
                                      cache = s3db.cache)
            if len(forums):
                ADMIN = auth.s3_has_role("ADMIN")
                forum_ids = [f.id for f in forums]
                ltable = s3db.event_forum
                query = (ltable.event_id == event_id) & \
                        (ltable.forum_id.belongs(forum_ids))
                shares = db(query).select(ltable.forum_id,
                                          ltable.created_by,
                                          ).as_dict(key="forum_id")
                share_btn = A(ICON("share"),
                               _href = "#",
                               _class = "",
                               _title = T("Share"),
                               )
                share_btn["_data-dropdown"] = "share_event_dropdown"
                share_btn["_aria-controls"] = "share_event_dropdown"
                share_btn["_aria-expanded"] = "false"

                dropdown = UL(_id = "share_event_dropdown",
                              _class = "f-dropdown share",
                              tabindex = "-1",
                              )
                dropdown["_data-dropdown-content"] = ""
                dropdown["_aria-hidden"] = "true"
                dropdown["_data-c"] = "event"
                dropdown["_data-f"] = "event"
                dropdown["_data-i"] = event_id

                dappend = dropdown.append
                for f in forums:
                    forum_id = f.id
                    checkbox_id = "event_forum_%s" % forum_id
                    if forum_id in shares:
                        if ADMIN or shares[forum_id]["created_by"] == user_id:
                            # Shared by us (or we're ADMIN), so render Checked checkbox which we can deselect
                            checkbox = INPUT(_checked = "checked",
                                             _id = checkbox_id,
                                             _type = "checkbox",
                                             _value = forum_id,
                                             )
                        else:
                            # Shared by someone else, so render Checked checkbox which is disabled
                            checkbox = INPUT(_checked = "checked",
                                             _disabled = "disabled",
                                             _id = checkbox_id,
                                             _type = "checkbox",
                                             _value = forum_id,
                                             )
                    else:
                        # Not Shared so render empty checkbox
                        checkbox = INPUT(_id = checkbox_id,
                                         _type = "checkbox",
                                         _value = forum_id,
                                         )
                    dappend(LI(checkbox,
                               LABEL(f.name,
                                     _for = checkbox_id,
                                     ),
                               ))

                share_btn = TAG[""](share_btn,
                                    dropdown,
                                    )
                # Done globally in _view
                #script = '''S3.wacop_shares()'''
                #s3.jquery_ready.append(script)
            else:
                share_btn = ""
        else:
            share_btn = ""
        output["share_btn"] = share_btn

        event = Storage()
        record = r.record
        event.name = record.name
        event.desc = record.comments
        event.start_date = date_represent(record.start_date)
        end_date = record.end_date
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
                                        vars = {"view": 1},
                                        ),
                            _class = "s3_modal",
                            _title = T("Incidents"),
                            )

        query = (ertable.event_id == event_id) & \
                (ertable.deleted == False)
        resources = db(query).count()
        event.resources = A("%s %s" % (resources, T("Resources")),
                            _href = URL(c="event", f="event",
                                        args = "group.popup",
                                        vars = {"view": 1},
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
                                      vars = {"view": 1},
                                      ),
                          _class = "s3_modal",
                          _title = T("Updates"),
                          )

        if record.exercise:
            event.status = T("Testing")
        elif not record.end_date:
            event.status = T("Open")
        else:
            event.status = T("Closed")

        output["event"] = event

        # DataTables
        datatable = self._datatable
        #settings.ui.datatables_pagingType = "bootstrap"
        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

        # Incidents dataTable
        tablename = "event_incident"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = updateable,
                  event_id = event_id,
                  dt_init = dt_init,
                  )

        # Resources dataTable
        tablename = "event_team"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = updateable,
                  event_id = event_id,
                  dt_init = dt_init,
                  )

        # Tasks dataTable
        self._tasks_html(r, output,
                         updateable = updateable,
                         event_id = event_id,
                         dt_init = dt_init,
                         )

        # Staff dataTable
        tablename = "event_human_resource"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = updateable,
                  event_id = event_id,
                  dt_init = dt_init,
                  # @ToDo: AJAX Delete
                  actions = [{"label": T("Unassign"),
                              "url": URL(c="event", f="event",
                                         args=[event_id, "human_resource", "[id]", "delete"]),
                              "icon": "fa fa-trash",
                              },
                             ],
                  )

        # Organisations dataTable
        tablename = "event_organisation"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = updateable,
                  event_id = event_id,
                  dt_init = dt_init,
                  # @ToDo: AJAX Delete
                  actions = [{"label": T("Remove"),
                              "url": URL(c="event", f="event",
                                         args=[event_id, "event_organisation", "[id]", "delete"]),
                              "icon": "fa fa-trash",
                              },
                             ],
                  )

        # Updates DataList
        self._updates_html(r, output,
                           event_id = event_id,
                           updateable = updateable,
                           **attr)

        self._view(output, "event_profile.html")

        return output

# =============================================================================
class group_Profile(custom_WACOP):
    """
        Custom profile page for Groups
        - modelled as pr_forum
    """

    # -------------------------------------------------------------------------
    def _html(self, r, **attr):
        """
            Handle HTML representation

            @param r: the S3Request
            @param attr: controller arguments
        """

        from s3 import s3_fullname

        db = current.db
        s3db = current.s3db
        auth = current.auth

        table = r.table
        record = r.record
        forum_id = r.id

        updateable = auth.s3_has_permission("update", table,
                                            record_id=forum_id,
                                            c="pr",
                                            f="forum")

        output = {"forum_id": forum_id,
                  "updateable": updateable,
                  }

        mtable = s3db.pr_forum_membership
        query = (mtable.forum_id == forum_id) & \
                (mtable.deleted == False)
        members = db(query).select(mtable.person_id,
                                   mtable.admin)
        admins = [s3_fullname(m.person_id) for m in members if m.admin]

        # Updates DataList
        numrows = self._updates_html(r, output,
                                     forum_id = forum_id,
                                     **attr)

        date_represent = lambda dt: S3DateTime.date_represent(dt,
                                                              format = "%b %d %Y %H:%M",
                                                              utc = True,
                                                              #calendar = calendar,
                                                              )

        output["group"] = Storage(name = record.name,
                                  description = record.comments,
                                  forum_type = table.forum_type.represent(record.forum_type),
                                  created_on = date_represent(record.created_on),
                                  modified_on = date_represent(record.modified_on),
                                  admin = ", ".join(admins),
                                  members = len(members),
                                  updates = numrows,
                                  )

        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

        # Members dataTable
        tablename = "pr_forum_membership"

        customise = current.deployment_settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        self._datatable(output = output,
                        tablename = tablename,
                        dt_init = dt_init,
                        forum_id = forum_id,
                        # @ToDo: AJAX Delete
                        actions = [{"label": current.T("Remove"),
                                    "url": URL(c="pr", f="forum",
                                               args=[forum_id, "forum_membership", "[id]", "delete"]),
                                    "icon": "fa fa-trash",
                                    },
                                   ],
                        )

        # Tasks dataTable
        self._tasks_html(r, output,
                         dt_init = dt_init,
                         forum_id = forum_id,
                         )

        # Notifications
        ftable = s3db.pr_filter
        stable = s3db.pr_subscription

        pe_id = auth.user.pe_id
        filter_string = '[["~.id", %s]]' % forum_id

        query = (ftable.pe_id == pe_id) & \
                (ftable.resource == "pr_forum") & \
                (ftable.query == filter_string) & \
                (ftable.id == stable.filter_id)
        exists = db(query).select(stable.frequency,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            output["notify"] = True
            output["frequency"] = exists.frequency
        else:
            output["notify"] = False
            output["frequency"] = "immediately"

        current.response.s3.scripts.append("/%s/static/themes/WACOP/js/group_profile.js" % r.application)

        self._view(output, "group_profile.html")

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
        s3 = current.response.s3
        settings = current.deployment_settings

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

        # Map of Incident
        # @ToDo: Add Resources
        _map, button = self._map("Incidents", filter="~.id=%s" % incident_id)

        output = {"incident_id": incident_id,
                  "_map": _map,
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
            s3.js_global.append('''incident_bounds=%s''' % json.dumps(bbox))
        else:
            output["L1"] = ""
            output["L3"] = ""
            output["addr_street"] = ""
            output["postcode"] = ""
            output["lat"] = ""
            output["lon"] = ""
            # Defaults for Washington
            bbox = {"lat_max": "45.5437202453613",
                    "lat_min": "49.00244140625",
                    "lon_max": "-116.917427062988",
                    "lon_min": "-124.836097717285",
                    }
            s3.js_global.append('''incident_bounds=%s''' % json.dumps(bbox))

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
            # Done globally in _view
            #script = '''S3.wacop_bookmarks()'''
            #s3.jquery_ready.append(script)
        else:
            bookmark = ""
        output["bookmark_btn"] = bookmark

        if user:
            ptable = s3db.pr_person
            mtable = s3db.pr_forum_membership
            ftable = s3db.pr_forum
            query = (ptable.pe_id == user.pe_id) & \
                    (ptable.id == mtable.person_id) & \
                    (mtable.forum_id == ftable.id)
            forums = db(query).select(ftable.id,
                                      ftable.name,
                                      cache = s3db.cache)
            if len(forums):
                ADMIN = auth.s3_has_role("ADMIN")
                forum_ids = [f.id for f in forums]
                ltable = s3db.event_forum
                query = (ltable.incident_id == incident_id) & \
                        (ltable.forum_id.belongs(forum_ids))
                shares = db(query).select(ltable.forum_id,
                                          ltable.created_by,
                                          ).as_dict(key="forum_id")
                share_btn = A(ICON("share"),
                               _href = "#",
                               _class = "",
                               _title = T("Share"),
                               )
                share_btn["_data-dropdown"] = "share_incident_dropdown"
                share_btn["_aria-controls"] = "share_incident_dropdown"
                share_btn["_aria-expanded"] = "false"

                dropdown = UL(_id = "share_incident_dropdown",
                              _class = "f-dropdown share",
                              tabindex = "-1",
                              )
                dropdown["_data-dropdown-content"] = ""
                dropdown["_aria-hidden"] = "true"
                dropdown["_data-c"] = "event"
                dropdown["_data-f"] = "incident"
                dropdown["_data-i"] = incident_id

                dappend = dropdown.append
                for f in forums:
                    forum_id = f.id
                    checkbox_id = "incident_forum_%s" % forum_id
                    if forum_id in shares:
                        if ADMIN or shares[forum_id]["created_by"] == user_id:
                            # Shared by us (or we're ADMIN), so render Checked checkbox which we can deselect
                            checkbox = INPUT(_checked = "checked",
                                             _id = checkbox_id,
                                             _type = "checkbox",
                                             _value = forum_id,
                                             )
                        else:
                            # Shared by someone else, so render Checked checkbox which is disabled
                            checkbox = INPUT(_checked = "checked",
                                             _disabled = "disabled",
                                             _id = checkbox_id,
                                             _type = "checkbox",
                                             _value = forum_id,
                                             )
                    else:
                        # Not Shared so render empty checkbox
                        checkbox = INPUT(_id = checkbox_id,
                                         _type = "checkbox",
                                         _value = forum_id,
                                         )
                    dappend(LI(checkbox,
                               LABEL(f.name,
                                     _for = checkbox_id,
                                     ),
                               ))

                share_btn = TAG[""](share_btn,
                                    dropdown,
                                    )
                # Done globally in _view
                #script = '''S3.wacop_shares()'''
                #s3.jquery_ready.append(script)
            else:
                share_btn = ""
        else:
            share_btn = ""
        output["share_btn"] = share_btn

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
                                            vars = {"view": 1},
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
                                            vars = {"view": 1},
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
                                            vars = {"view": 1},
                                            ),
                                _class = "s3_modal",
                                _title = T("Updates"),
                                )

            event.url = URL(c="event", f="event",
                            args = [event_id, "custom"],
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
        datatable = self._datatable
        #settings.ui.datatables_pagingType = "bootstrap"
        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

        # Resources dataTable
        tablename = "event_team"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = updateable,
                  incident_id = incident_id,
                  dt_init = dt_init,
                  )

        # Tasks dataTable
        self._tasks_html(r, output,
                         updateable = updateable,
                         incident_id = incident_id,
                         dt_init = dt_init,
                         )

        # Staff dataTable
        tablename = "event_human_resource"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = updateable,
                  incident_id = incident_id,
                  dt_init = dt_init,
                  # @ToDo: AJAX Delete
                  actions = [{"label": T("Unassign"),
                              "url": URL(c="event", f="incident",
                                         args=[incident_id, "human_resource", "[id]", "delete"]),
                              "icon": "fa fa-trash",
                              },
                             ],
                  )

        # Organisations dataTable
        tablename = "event_organisation"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = updateable,
                  incident_id = incident_id,
                  dt_init = dt_init,
                  # @ToDo: AJAX Delete
                  actions = [{"label": T("Remove"),
                              "url": URL(c="event", f="incident",
                                         args=[incident_id, "event_organisation", "[id]", "delete"]),
                              "icon": "fa fa-trash",
                              },
                             ],
                  )

        # Updates DataList
        self._updates_html(r, output,
                           incident_id = incident_id,
                           updateable = updateable,
                           **attr)

        self._view(output, "incident_profile.html")

        return output

# =============================================================================
def group_Notify(r, **attr):
    """
        Manage Notifications for a Group

        S3Method for interactive requests
        - designed to be called via AJAX
    """

    forum_id = r.id
    if not forum_id or r.http != "POST":
        r.error(405, current.ERROR.BAD_METHOD)

    tablename = "pr_forum"
    controller, function = tablename.split("_", 1)
    filter_string = '[["~.id", %s]]' % forum_id

    pe_id = current.auth.user.pe_id

    post_vars_get = r.post_vars.get
    email = post_vars_get("email")
    frequency = post_vars_get("frequency")

    db = current.db
    s3db = current.s3db

    ftable = s3db.pr_filter
    stable = s3db.pr_subscription

    query = (ftable.pe_id == pe_id) & \
            (ftable.query == filter_string) & \
            (ftable.resource == tablename) & \
            (ftable.id == stable.filter_id)
    exists = db(query).select(ftable.id,
                              stable.id,
                              limitby=(0, 1)
                              ).first()
    if exists:
        if email == "1":
            db(stable.id == exists["pr_subscription.id"]).update(frequency = frequency)
        else:
            # Delete the Subscription
            # (cascades to the subscription_resource)
            resource = s3db.resource("pr_subscription", id=exists["pr_subscription.id"])
            resource.delete()
            # Delete the Filter
            resource = s3db.resource("pr_filter", id=exists["pr_filter.id"])
            resource.delete()
    else:
        if email == "1":
            # Create the Filter
            filter_id = ftable.insert(pe_id = pe_id,
                                      # Just used by Saved Filters, not Subscription
                                      #controller = controller,
                                      #function = function,
                                      resource = tablename, # But still useful to distinguish, in case saved filters also used
                                      query = filter_string,
                                      )
            # Create the Subscription
            subscription_id = stable.insert(pe_id = pe_id,
                                            filter_id = filter_id,
                                            notify_on = ["upd"],
                                            frequency = frequency,
                                            # Default:
                                            #method = ["EMAIL"],
                                            )
            # Create the Subscription Resource
            db.pr_subscription_resource.insert(subscription_id = subscription_id,
                                               resource = tablename,
                                               url = "%s/%s" % (controller, function),
                                               )


    output = current.xml.json_message(True, 200, current.T("Notification Settings Updated"))
    current.response.headers["Content-Type"] = "application/json"
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

        settings = current.deployment_settings

        # Map of Incidents
        _map, button = self._map("Incidents")

        output = {"map": _map,
                  }

        # Greeting
        user = current.auth.user
        organisation_id = user.organisation_id
        if organisation_id:
            s3db = current.s3db
            ptable = s3db.pr_person
            ltable = s3db.pr_person_user
            hrtable = s3db.hrm_human_resource
            organisation = hrtable.organisation_id.represent(organisation_id)
            query = (ltable.user_id == user.id) & \
                    (ltable.pe_id == ptable.pe_id) & \
                    (hrtable.person_id == ptable.id)
            hr = current.db(query).select(hrtable.job_title_id,
                                          limitby = (0, 1),
                                          ).first()
            if hr:
                job_title = hrtable.organisation_id.represent(hr.job_title_id)
                staff_role = XML("%s, %s" % (job_title, organisation))

            else:
                staff_role = organisation
        else:
            staff_role = ""
        output["greeting"] = Storage(first_name = user.first_name,
                                     last_name = user.last_name,
                                     staff_role = staff_role,
                                     )

        # DataTables
        datatable = self._datatable
        #settings.ui.datatables_pagingType = "bootstrap"
        dt_init = ['''$('.dataTables_filter label,.dataTables_length,.dataTables_info').hide();''']

        # Tasks dataTable
        self._tasks_html(r, output,
                         updateable = True,
                         dt_init = dt_init,
                         )

        # Staff dataTable
        tablename = "hrm_human_resource"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = True,
                  dt_init = dt_init,
                  )

        # Organisations dataTable
        tablename = "org_organisation"

        customise = settings.customise_resource(tablename)
        if customise:
            customise(r, tablename)

        datatable(output = output,
                  tablename = tablename,
                  updateable = True,
                  dt_init = dt_init,
                  )

        # Updates DataList
        self._updates_html(r, output, **attr)

        self._view(output, "dashboard.html")

        return output

# =============================================================================
def dashboard_filter():
    """
        Filter Updates on the Dashboard
         - Updates we have Bookmarked
         - Updates linked to Incidents we have Bookmarked
         - Updates linked to Events we have Bookmarked
           #(unless that update is also linked to an Incident)
         - Updates linked to Groups which we are a Member of
    """

    db = current.db
    s3db = current.s3db
    user = current.auth.user
    user_id = user.id

    btable = s3db.event_bookmark
    query = (btable.user_id == user_id) & \
            (btable.deleted == False)
    bookmarks = db(query).select(btable.event_id,
                                 btable.incident_id,
                                 )
    incident_ids = []
    iappend = incident_ids.append
    event_ids = []
    eappend = event_ids.append
    for b in bookmarks:
        incident_id = b.incident_id
        if incident_id is not None:
            iappend(incident_id)
        else:
            eappend(b.event_id)

    ptable = s3db.pr_person
    mtable = s3db.pr_forum_membership
    query = (ptable.pe_id == user.pe_id) & \
            (mtable.person_id == ptable.id) & \
            (mtable.deleted == False)
    forums = db(query).select(mtable.forum_id,
                              )
    forum_ids = [f.forum_id for f in forums]

    filter = (FS("bookmark.user_id") == user_id) | \
             (FS("post_forum.forum_id").belongs(forum_ids)) | \
             (FS("incident_post.incident_id").belongs(incident_ids)) | \
             (FS("incident_post.event_id").belongs(event_ids))
             #((FS("incident_post.event_id").belongs(event_ids)) & \
             # (FS("incident_post.incident_id") == None))

    return filter

# =============================================================================
def group_filter(forum_id):
    """
        Filter Updates for a Group
         - Updates shared to this Group
         - Updates linked to Incidents shared to this Group
         - Updates linked to Events shared to this Group
           #(unless that update is also linked to an Incident)
    """

    stable = current.s3db.event_forum
    query = (stable.forum_id == forum_id) & \
            (stable.deleted == False)
    shared = current.db(query).select(stable.event_id,
                                      stable.incident_id,
                                      )
    incident_ids = []
    iappend = incident_ids.append
    event_ids = []
    eappend = event_ids.append
    for s in shared:
        incident_id = s.incident_id
        if incident_id is not None:
            iappend(incident_id)
        else:
            eappend(s.event_id)

    filter = (FS("post_forum.forum_id") == forum_id)
    if incident_ids:
        filter |= (FS("incident_post.incident_id").belongs(incident_ids))
    if event_ids:
        filter |= (FS("event_post.event_id").belongs(event_ids))
                  #((FS("event_post.event_id").belongs(event_ids)) & \
                  # (FS("event_post.incident_id") == None))

    return filter

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
    #item_class = "thumbnail"

    T = current.T
    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings
    permit = current.auth.s3_has_permission

    raw = record._row
    date = record["cms_post.date"]
    title = record["cms_post.title"]
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

    # Toolbar
    if permit("update", table, record_id=record_id):
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

    # Bookmarks
    auth = current.auth
    user = auth.user
    if user: #and settings.get_cms_bookmarks():
        # @ToDo: Bulk lookup (via list_fields?)
        ltable = s3db.cms_post_user
        query = (ltable.post_id == record_id) & \
                (ltable.user_id == user.id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            bookmark = A(ICON("bookmark"),
                         SPAN("remove bookmark",
                              _class = "show-for-sr",
                              ),
                         _class="bookmark",
                         _title=T("Remove Bookmark"),
                         )
        else:
            bookmark = A(ICON("bookmark-empty"),
                         SPAN("bookmark",
                              _class = "show-for-sr",
                              ),
                         _class="bookmark",
                         _title=T("Add Bookmark"),
                         )
        bookmark["_data-c"] = "cms"
        bookmark["_data-f"] = "post"
        bookmark["_data-i"] = record_id
    else:
        bookmark = ""

    # Shares
    if user:
        # @ToDo: Bulk lookup (via list_fields?)
        ptable = s3db.pr_person
        mtable = s3db.pr_forum_membership
        ftable = s3db.pr_forum
        query = (ptable.pe_id == user.pe_id) & \
                (ptable.id == mtable.person_id) & \
                (mtable.forum_id == ftable.id)
        forums = db(query).select(ftable.id,
                                  ftable.name,
                                  cache = s3db.cache)
        if len(forums):
            ADMIN = auth.s3_has_role("ADMIN")
            forum_ids = [f.id for f in forums]
            ltable = s3db.cms_post_forum
            query = (ltable.post_id == record_id) & \
                    (ltable.forum_id.belongs(forum_ids))
            shares = db(query).select(ltable.forum_id,
                                      ltable.created_by,
                                      ).as_dict(key="forum_id")
            share_btn = A(ICON("share"),
                           _href = "#",
                           _class = "",
                           _title = T("Share"),
                           )
            dropdown_id = "share_post_dropdown_%s" % record_id
            share_btn["_data-dropdown"] = dropdown_id
            share_btn["_aria-controls"] = dropdown_id
            share_btn["_aria-expanded"] = "false"

            dropdown = UL(_id = dropdown_id,
                          _class = "f-dropdown share",
                          tabindex = "-1",
                          )
            dropdown["_data-dropdown-content"] = ""
            dropdown["_aria-hidden"] = "true"
            dropdown["_data-c"] = "cms"
            dropdown["_data-f"] = "post"
            dropdown["_data-i"] = record_id

            dappend = dropdown.append
            user_id = user.id
            for f in forums:
                forum_id = f.id
                checkbox_id = "post_%s_forum_%s" % (record_id, forum_id)
                if forum_id in shares:
                    if ADMIN or shares[forum_id]["created_by"] == user_id:
                        # Shared by us (or we're ADMIN), so render Checked checkbox which we can deselect
                        checkbox = INPUT(_checked = "checked",
                                         _id = checkbox_id,
                                         _type = "checkbox",
                                         _value = forum_id,
                                         )
                    else:
                        # Shared by someone else, so render Checked checkbox which is disabled
                        checkbox = INPUT(_checked = "checked",
                                         _disabled = "disabled",
                                         _id = checkbox_id,
                                         _type = "checkbox",
                                         _value = forum_id,
                                         )
                else:
                    # Not Shared so render empty checkbox
                    checkbox = INPUT(_id = checkbox_id,
                                     _type = "checkbox",
                                     _value = forum_id,
                                     )
                dappend(LI(checkbox,
                           LABEL(f.name,
                                 _for = checkbox_id,
                                 ),
                           ))

            share_btn = TAG[""](share_btn,
                                dropdown,
                                )
            # Done globally in _view
            #script = '''S3.wacop_shares()'''
            #s3.jquery_ready.append(script)
        else:
            share_btn = ""
    else:
        share_btn = ""

    # Dropdown of available documents
    documents = raw["doc_document.file"]
    if documents:
        if not isinstance(documents, list):
            documents = (documents,)
        doc_list = UL(_class="dropdown-menu",
                      _role="menu",
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except (IOError, TypeError):
                doc_name = current.messages["NONE"]
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(ICON("file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(ICON("paper-clip"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle",
                     _href="#",
                     **{"_data-toggle": "dropdown"}
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    divider = LI("|")
    divider["_aria-hidden"] = "true"

    toolbar = UL(LI(share_btn,
                    _class="item",
                    ),
                 #LI(A(ICON("flag"), # @ToDo: Use flag-alt if not flagged & flag if already flagged (like for bookmarks)
                 #     SPAN("flag this",
                 #          _class = "show-for-sr",
                 #          ),
                 #     _href="#",
                 #     _title=T("Flag"),
                 #     ),
                 #   _class="item",
                 #   ),
                 LI(bookmark,
                    _class="item",
                    ),
                 #LI(A(I(_class="fa fa-users",
                 #       ),
                 #     SPAN("make public",
                 #          _class = "show-for-sr",
                 #          ),
                 #     _href="#",
                 #     _title=T("Make Public"),
                 #     ),
                 #   _class="item",
                 #   ),
                 LI(edit_btn,
                    _class="item",
                    ),
                 LI(delete_btn,
                    _class="item",
                    ),
                 _class="controls",
                 )

    # Tags
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

    # Comments
    comment_list = UL(_class="card-post-comments")
    cappend = comment_list.append

    #if settings.get_cms_comments():
    # Add existing comments (oldest 1st)
    # - should sort by default by ID which is equivalent to oldest first,
    #   however they seem to come in in a random order (even if orderby set on the component) so need to be sorted manually here
    comments = raw["cms_comment.json_dump"]
    ncomments = 0
    if comments:
        if not isinstance(comments, list):
            comments = [comments]
        comments = [json.loads(comment) for comment in comments]
        comments.sort(key=lambda c: c["created_on"])
        for comment in comments:
            author = s3_auth_user_represent(comment["created_by"])
            cdate = dateutil.parser.parse(comment["created_on"])
            ctime = cdate.time().strftime("%H:%M")
            cdate = cdate.date().strftime("%b %d, %Y")
            comment = LI(TAG["ASIDE"](P(T("Updated %(date)s @ %(time)s by %(author)s") % \
                                                dict(date = cdate,
                                                     time = ctime,
                                                     author = author,
                                                     ),
                                        _class="meta",
                                        ),
                                      DIV(comment["body"],
                                          _class="desc",
                                          ),
                                      # @ToDo: Show this if more than x chars?
                                      #TAG["FOOTER"](P(A(T("More Info"),
                                      #                  _class="more",
                                      #                  )
                                      #                ),
                                      #              _class="footer",
                                      #              ),
                                      _class="card-post-comment",
                                      ))
            cappend(comment)
            ncomments += 1

    if ncomments == 1:
        num_comments = "1 Comment"
    else:
        num_comments = T("%(num)s Comments") % dict(num = ncomments)

    if user:
        add_comment = A(T("Add Comment"),
                        _class="add-comment",
                        )
        add_comment["_data-l"] = list_id
        add_comment["_data-i"] = record_id
        add_comment = P(add_comment)
        comment_input = LI(TAG["ASIDE"](TEXTAREA(_class="desc",
                                                 _placeholder=T("comment here"),
                                                 ),
                                        TAG["FOOTER"](P(A("Submit Comment",
                                                          _class="submit",
                                                          ),
                                                        ),
                                                      ),
                                        _class="card-post-comment",
                                        ),
                          _class="comment-form hide",
                          )
        cappend(comment_input)
    else:
        add_comment = ""

    item = TAG["ASIDE"](TAG["HEADER"](UL(# post priority icon
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
                        DIV(DIV(SPAN("Updated ", # @ToDo: i18n
                                     TAG["TIME"](date),
                                     " by ",
                                     person,
                                     _class="meta-update",
                                     ),
                                SPAN(num_comments,
                                     _class="meta-comments",
                                     ),
                                _class="meta",
                                ),
                            H4(title,
                               _class="title",
                               ),
                            DIV(body,
                                _class="desc",
                                ),
                            _class="body",
                            ),
                        docs,
                        TAG["FOOTER"](DIV(tag_list,
                                        _class="tags clearfix", # @ToDo: remove clearfix and style via CSS
                                        ),
                                      comment_list,
                                      add_comment,
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

        controls = DIV(widget,
                       SPAN(I(_class="fa fa-search"),
                            _class="search-icon",
                            ),
                       _class="search-wrapper",
                       _id=row_id,
                       )
        return DIV(DIV(controls,
                       _class="small-12 column",
                       ),
                   _class="row",
                   )

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

        controls = DIV(widget, _class="controls")

        #if comment:
        #    comment = render_tooltip(label,
        #                             comment,
        #                             _class="inline-tooltip tooltip",
        #                             )
        #    if hasattr(comment, "add_class"):
        #        comment.add_class("inline-tooltip")
        #    controls_col.append(comment)

        _class = "row hide" if hidden else "row"
        return DIV(DIV(label,
                       controls,
                       _class="small-12 columns",
                       ),
                   _class=_class,
                   _id=row_id,
                   )

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
