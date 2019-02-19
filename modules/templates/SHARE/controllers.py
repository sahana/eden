# -*- coding: utf-8 -*-

import dateutil
import json

from gluon import current, A, DIV, H3, H4, HR, LI, P, SPAN, TAG, TEXTAREA, UL, URL, XML
from s3 import ICON, \
               s3_auth_user_represent, s3_str, \
               S3CustomController, \
               S3FilterForm, S3LocationFilter, S3OptionsFilter, S3TextFilter, \
               S3Represent

THEME = "SHARE"

# =============================================================================
class index(S3CustomController):
    """
        Custom Home Page
    """

    def __call__(self):

        T = current.T
        db = current.db
        s3db = current.s3db

        output = {}

        # Recent Updates
        etable = s3db.event_event
        stable = s3db.event_sitrep
        query = (stable.deleted == False)
        fields = [etable.name,
                  stable.id,
                  stable.date,
                  stable.name,
                  stable.summary,
                  ]

        left = [etable.on(etable.id == stable.event_id)]

        language = current.session.s3.language
        if language != current.deployment_settings.get_L10n_default_language():
            ntable = s3db.event_event_name
            left.append(ntable.on((ntable.event_id == etable.id) & \
                                  (ntable.language == language)))
            fields.append(ntable.name_l10n)
            use_local_event_name = True
        else:
            use_local_event_name = False

        sitreps = db(query).select(left = left,
                                   limitby = (0, 3),
                                   orderby = ~stable.date,
                                   *fields
                                   )
        len_sitreps = len(sitreps)
        if len_sitreps == 0:
            from s3 import S3CRUD
            recent_updates = DIV(S3CRUD.crud_string("event_sitrep",
                                                    "msg_list_empty"),
                                 _class="empty")
        else:
            recent_updates = DIV()
            rappend = recent_updates.append
            count = 0
            for s in sitreps:
                count += 1
                if use_local_event_name:
                    event_name = s["event_event_name.name_l10n"] or s["event_event.name"]
                else:
                    event_name = s["event_event.name"]
                if not event_name:
                    event_name = s["event_sitrep.name"]
                rappend(H3(A(event_name,
                             _href = URL(c = "event",
                                         f = "sitrep",
                                         args = [s["event_sitrep.id"]],
                                         ),
                             )))
                rappend(P(XML(s["event_sitrep.summary"])))
                if count != len_sitreps:
                    rappend(HR())

        output["recent_updates"] = recent_updates

        map_btn = A(T("MAP OF CURRENT NEEDS"),
                    #_href = URL(c="default",
                    #            f="index",
                    #            args="dashboard",
                    #            ),
                    _href = URL(c="req",
                                f="need_line",
                                args="map",
                                ),
                    _class = "small primary button",
                    )

        create_btn = A(T("CREATE A NEED"),
                       _href = URL(c="req",
                                   f="need",
                                   args="create",
                                   ),
                       _class = "small primary button",
                       )

        output["needs_btn"] = DIV(SPAN(map_btn),
                                  SPAN(create_btn),
                                  _class="button-group radius",
                                  )

        output["about_btn"] = A("%s >" % T("Read More"),
                                _href = URL(c="default",
                                            f="about",
                                            ),
                                )

        self._view(THEME, "index.html")

        # Inject D3 scripts
        from s3 import S3Report
        S3Report.inject_d3()

        # Inject charts-script
        appname = current.request.application
        s3 = current.response.s3
        scripts = s3.scripts
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.charts.js" % appname
            if script not in scripts:
                scripts.append(script)
        else:
            script = "/%s/static/scripts/S3/s3.ui.charts.min.js" % appname
            if script not in scripts:
                scripts.append(script)

        # Instantiate charts
        scriptopts = {
            # Standard SHARE theme color set:
            "colors": ['#0C9CD0', # blue
                       '#E03158', # red
                       '#FBA629', # amber
                       '#8ABC3F', # green
                       '#AFB8BF', # grey
                       ],
            }
        script = '''$('.homepage-chart').uiChart(%s)''' % json.dumps(scriptopts)
        s3.jquery_ready.append(script)

        # Add last update time of chart data
        last_update = HomepageStatistics.last_update()
        if last_update:
            output["last_stats_update"] = T("Updated on %(date)s") % {"date": last_update}
        else:
            output["last_stats_update"] = None

        return output

# =============================================================================
def cms_post_list_layout(list_id, item_id, resource, rfields, record):
    """
        dataList item renderer for Posts on the Bulletin Board.

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
    #series_id = raw["cms_post.series_id"]

    # Allow records to be truncated
    # (not yet working for HTML)
    body = DIV(body,
               _class="s3-truncate",
               )

    #if series_id:
    #    series = record["cms_post.series_id"]
    #    translate = settings.get_L10n_translate_cms_series()
    #    if translate:
    #        series_title = T(series)
    #    else:
    #        series_title = series
    #else:
    #    series_title = series = ""

    #status = record["cms_post.status_id"]

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
                     #_title=T("Edit %(type)s") % dict(type=series_title),
                     _title=T("Edit"),
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

    toolbar = UL(#LI(share_btn,
                 #   _class="item",
                 #   ),
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
                                         #LI(series_title,
                                         #   _class="item primary",
                                         #   ),
                                         # post status
                                         #LI(status,
                                         #   _class="item secondary border status",
                                         #   ),
                                         # post visibility
                                         # @ToDo: Read the visibility
                                         #LI(T("Public"),
                                         #   _class="item secondary border visibility",
                                         #   ),
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
class dashboard(S3CustomController):
    """
        Custom Dashboard
        - recent Events
        - set of Filters
        - 2 Tabs: Activities & Needs
            Each tab has DataList & Map
    """

    def __call__(self):

        T = current.T
        output = {}
        s3db = current.s3db
        request = current.request

        #------------------------
        # Map to display needs
        map_id = "default_map"

        ftable = s3db.gis_layer_feature
        query = (ftable.controller == "req") & \
                (ftable.function == "need_line")
        layer = current.db(query).select(ftable.layer_id,
                                         limitby=(0, 1)
                                         ).first()
        try:
            layer_id = layer.layer_id
        except AttributeError:
            current.log.error("Cannot find Layer for Map")
            layer_id = None

        feature_resources = [{"name"      : T("Needs"),
                              "id"        : "search_results",
                              "layer_id"  : layer_id,
                              "active"    : False,
                              }]

        _map = current.gis.show_map(callback = '''S3.search.s3map()''',
                                    catalogue_layers = True,
                                    collapsed = True,
                                    feature_resources = feature_resources,
                                    save = False,
                                    search = True,
                                    toolbar = True,
                                    )
        output["_map"] = _map

        # ---------------------------------------------------------------------
        # Display needs list
        resource = s3db.resource("req_need_line")
        #resource.table.commit_status.represent = None
        #list_id = "req_datalist"
        #list_fields = [#"purpose",
        #               "location_id",
        #               #"priority",
        #               #"req_ref",
        #               #"site_id",
        #               "date",
        #               ]
        # Order with most recent request first
        #orderby = "req_need.date"
        #datalist, numrows = resource.datalist(fields = list_fields,
        #                                      limit = None,
        #                                      list_id = list_id,
        #                                      orderby = orderby,
        #                                      )
        #if numrows == 0:
        #    current.response.s3.crud_strings["req_need"].msg_no_match = T("No needs at present.")

        #ajax_url = URL(c="req", f="need", args="datalist.dl",
        #               vars={"list_id": list_id})
        #@ToDo: Implement pagination properly
        #output[list_id] = datalist.html(ajaxurl = ajax_url,
        #                                pagesize = 0,
        #                                )

        # ----------------------------
        # Filter Form
        # - can we have a single form for both Activities & Needs?
        #
        filter_widgets = [S3TextFilter([#"need_id$req_number.value",
                                        "item_id$name",
                                        # These levels are for SHARE/LK
                                        #"location_id$L1",
                                        "location_id$L2",
                                        #"location_id$L3",
                                        #"location_id$L4",
                                        "need_id$name",
                                        "need_id$comments",
                                        ],
                                       label = T("Search"),
                                       comment = T("Search for a Need by Request Number, Item, Location, Summary or Comments"),
                                       ),
                          S3LocationFilter("location_id",
                                           # These levels are for SHARE/LK
                                           levels = ("L2", "L3", "L4"),
                                           ),
                          S3OptionsFilter("item_id"),
                          S3OptionsFilter("status",
                                          cols = 3,
                                          label = T("Status"),
                                          ),
                          S3OptionsFilter("need_id$event.event_type_id",
                                          hidden = True,
                                          ),
                          # @ToDo: Filter this list dynamically based on Event Type:
                          S3OptionsFilter("need_id$event__link.event_id"),
                          S3OptionsFilter("sector_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("need_id$organisation__link.organisation_id",
                                          hidden = True,
                                          ),
                          S3OptionsFilter("need_id$verified.value",
                                          cols = 2,
                                          label = T("Verified"),
                                          hidden = True,
                                          ),
                          ]
        filter_form = S3FilterForm(filter_widgets,
                                   ajax = True,
                                   submit = True,
                                   #url = ajax_url,
                                   )
        output["req_filter_form"] = filter_form.html(resource,
                                                     request.get_vars,
                                                     #target = "%s %s" % list_id, map_id
                                                     target = map_id
                                                     )

        # View title
        output["title"] = current.deployment_settings.get_system_name()

        self._view(THEME, "dashboard.html")

        # Custom JS
        current.response.s3.scripts.append("/%s/static/themes/SHARE/js/homepage.js" % request.application)

        return output

# =============================================================================
class project_ActivityRepresent(S3Represent):
    """
        Representation of Activities by Organisation
        - unused as we now use req_need_response instead
    """

    def __init__(self,
                 show_link = True,
                 multiple = False,
                 ):

        self.org_represent = current.s3db.org_OrganisationRepresent() # show_link=False

        super(project_ActivityRepresent,
              self).__init__(lookup = "project_activity",
                             fields = ["project_activity.name",
                                       "project_activity_organisation.organisation_id",
                                       ],
                             show_link = show_link,
                             multiple = multiple,
                             )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for activity rows, does a
            left join with the tag. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the activity IDs
        """

        s3db = current.s3db
        atable = s3db.project_activity
        aotable = s3db.project_activity_organisation

        left = aotable.on((aotable.activity_id == atable.id) & \
                          (aotable.role == 1))

        qty = len(values)
        if qty == 1:
            query = (atable.id == values[0])
            limitby = (0, 1)
        else:
            query = (atable.id.belongs(values))
            limitby = (0, qty)

        rows = current.db(query).select(atable.id,
                                        atable.name,
                                        aotable.organisation_id,
                                        left=left,
                                        limitby=limitby)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row, prefix=None):
        """
            Represent a single Row

            @param row: the project_activity Row
        """

        # Custom Row (with the Orgs left-joined)
        organisation_id = row["project_activity_organisation.organisation_id"]
        if organisation_id:
            return self.org_represent(organisation_id)
        else:
            # Fallback to name
            name = row["project_activity.name"]
            if name:
                return s3_str(name)
            else:
                return current.messages["NONE"]

# =============================================================================
class req_NeedRepresent(S3Represent):
    """ Representation of Needs by Req Number """

    def __init__(self,
                 show_link = True,
                 multiple = False,
                 ):

        super(req_NeedRepresent,
              self).__init__(lookup = "req_need",
                             fields = ["req_need.name",
                                       "req_need_tag.value",
                                       ],
                             show_link = show_link,
                             multiple = multiple,
                             )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for need rows, does a
            left join with the tag. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the need IDs
        """

        s3db = current.s3db
        ntable = s3db.req_need
        nttable = s3db.req_need_tag

        left = nttable.on((nttable.need_id == ntable.id) & \
                          (nttable.tag == "req_number"))

        qty = len(values)
        if qty == 1:
            query = (ntable.id == values[0])
            limitby = (0, 1)
        else:
            query = (ntable.id.belongs(values))
            limitby = (0, qty)

        rows = current.db(query).select(ntable.id,
                                        ntable.name,
                                        nttable.value,
                                        left=left,
                                        limitby=limitby)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row, prefix=None):
        """
            Represent a single Row

            @param row: the req_need Row
        """

        # Custom Row (with the tag left-joined)
        req_number = row["req_need_tag.value"]
        if req_number:
            return s3_str(req_number)
        else:
            # Fallback to name
            name = row["req_need.name"]
            if name:
                return s3_str(name)
            else:
                return current.messages["NONE"]

# =============================================================================
class HomepageStatistics(object):
    """
        Data extraction for homepage statistics (charts)
    """

    # Status labels, color and presentation order (bottom=>top)
    REQ_STATUS = ((3, "Complete",            "#6c8c20"), # forrest
                  (2, "Fully Committed",     "#90c147"), # grass
                  (1, "Partially Committed", "#fba629"), # amber
                  (0, "Uncommitted",         "#c42648"), # darkrose
                  )

    # -------------------------------------------------------------------------
    @classmethod
    def needs_by_status(cls):
        """
            Count need lines per status
            - for all open Events
        """

        db = current.db
        s3db = current.s3db

        table = s3db.req_need_line
        etable = s3db.event_event
        ltable = s3db.event_event_need

        # Extract the data
        status = table.status
        number = table.id.count()
        query = (etable.closed == False) & \
                (etable.id == ltable.event_id) & \
                (ltable.need_id == table.need_id) & \
                (table.deleted == False)

        rows = db(query).select(status, number, groupby = status)

        # Build data structure for chart renderer
        rows = dict((row[status], row[number]) for row in rows)
        data = []
        for code, label, color in cls.REQ_STATUS[::-1]: # clockwise
            value = rows.get(code)
            data.append({"label": s3_str(label),
                         "value": value if value else 0,
                         "color": color,
                         "filterKey": code,
                         })

        return data

    # -------------------------------------------------------------------------
    @classmethod
    def needs_by_district(cls):
        """
            Count need lines per district and status (top 5 districts)
            - for all open Events
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        table = s3db.req_need_line
        ntable = s3db.req_need
        etable = s3db.event_event
        ltable = s3db.event_event_need

        status = table.status
        number = table.id.count()
        location = ntable.location_id

        base_query = (etable.closed == False) & \
                     (etable.id == ltable.event_id) & \
                     (ltable.need_id == ntable.id) & \
                     (ntable.id == table.need_id) & \
                     (table.deleted == False)

        # Get the top-5 locations by number of need lines
        query = base_query & (location != None)
        rows = db(query).select(location,
                                number,
                                groupby = location,
                                orderby = ~(number),
                                limitby = (0, 5),
                                )
        locations = [row[location] for row in rows]

        data = []
        if locations:
            # Get labels for locations
            location_represent = S3Represent(lookup="gis_location", fields=["L2"])
            location_labels = location_represent.bulk(locations)

            # Count need lines per status and location
            query = base_query & (location.belongs(locations))
            rows = db(query).select(location,
                                    status,
                                    number,
                                    groupby = (status, location),
                                    )

            # Group results as {status: {location: number}}
            per_status = {}
            for row in rows:
                row_status = row[status]
                if row_status in per_status:
                    per_status[row_status][row[location]] = row[number]
                else:
                    per_status[row_status] = {row[location]: row[number]}

            # Build data structure for chart renderer
            # - every status gives a series
            # - every district gives a series entry
            for code, label, color in cls.REQ_STATUS:
                series = {"key": s3_str(T(label)),
                          "color": color,
                          "filterKey": code,
                          }
                values = []
                per_location = per_status.get(code)
                for location_id in locations:
                    if per_location:
                        value = per_location.get(location_id)
                    else:
                        value = None
                    location_label = location_labels.get(location_id)
                    item = {"label": location_label,
                            "value": value if value else 0,
                            "filterKey": location_label,
                            }
                    values.append(item)
                series["values"] = values
                data.append(series)

        return data

    # -------------------------------------------------------------------------
    @classmethod
    def people_affected(cls):
        """
            Count total number of affected people by demographic type
            - for all open Events
        """

        db = current.db
        s3db = current.s3db

        table = s3db.req_need_line
        etable = s3db.event_event
        ltable = s3db.event_event_need

        query = (etable.closed == False) & \
                (etable.id == ltable.event_id) & \
                (ltable.need_id == table.need_id) & \
                (table.deleted == False)

        demographic = table.parameter_id
        represent = demographic.represent
        total = table.value.sum()

        rows = db(query).select(demographic,
                                total,
                                groupby = demographic,
                                orderby = ~(total),
                                limitby = (0, 5),
                                )
        values = []
        for row in rows:
            value = row[total]
            parameter_id = row[demographic]
            values.append({"label": s3_str(represent(parameter_id)),
                           "value": value if value else 0,
                           "filterKey": parameter_id,
                           })

        return [{"key": s3_str(current.T("People Affected")),
                 "values": values,
                 },
                ]

    # -------------------------------------------------------------------------
    @classmethod
    def update_data(cls):
        """
            Update data files for homepage statistics

            NB requires write-permission for static/themes/SHARE/data folder+files
        """

        SEPARATORS = (",", ":")

        import os
        os_path_join = os.path.join
        json_dump = json.dump

        base = os_path_join(current.request.folder, "static", "themes", "SHARE", "data")

        path = os_path_join(base, "needs_by_status.json")
        data = cls.needs_by_status()
        with open(path, "w") as outfile:
            json_dump(data, outfile, separators=SEPARATORS, encoding="utf-8")

        path = os_path_join(base, "needs_by_district.json")
        data = cls.needs_by_district()
        with open(path, "w") as outfile:
            json_dump(data, outfile, separators=SEPARATORS, encoding="utf-8")

        path = os_path_join(base, "people_affected.json")
        data = cls.people_affected()
        with open(path, "w") as outfile:
            json_dump(data, outfile, separators=SEPARATORS, encoding="utf-8")

    # -------------------------------------------------------------------------
    @classmethod
    def last_update(cls):
        """
            Get last update time of homepage stats

            @returns: a date/time string in local format and timezone
        """

        import datetime, os
        from s3 import S3DateTime

        # Probe file (probing one is good enough since update_data
        # writes them all at the same time)
        filename = os.path.join(current.request.folder,
                                "static", "themes", "SHARE", "data",
                                "people_affected.json",
                                )
        try:
            mtime = os.path.getmtime(filename)
        except OSError:
            last_update = None
        else:
            dt = datetime.datetime.utcfromtimestamp(mtime)
            last_update = S3DateTime.datetime_represent(dt, utc=True)

        return last_update

# END =========================================================================
