# -*- coding: utf-8 -*-

import json

from gluon import *
#from gluon import current
#from gluon.storage import Storage
from s3 import s3_str, \
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
        query = (stable.deleted == False) & \
                (stable.event_id == etable.id)
        fields = [etable.name,
                  stable.date,
                  stable.summary,
                  ]
        language = current.session.s3.language
        if language != current.deployment_settings.get_L10n_default_language():
            ntable = s3db.event_event_name
            left = ntable.on((ntable.event_id == etable.id) & \
                             (ntable.language == language))
            fields.append(ntable.name_l10n)
        else:
            left = None
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
                if left:
                    event_name = s["event_event_name.name_l10n"] or s["event_event.name"]
                else:
                    event_name = s["event_event.name"]
                rappend(H3(event_name))
                rappend(P(s["event_sitrep.summary"]))
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

        return output

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
        except:
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

        self.lookup_rows = self.custom_lookup_rows
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
    def custom_lookup_rows(self, key, values, fields=None):
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
    def represent_row(self, row):
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

        self.lookup_rows = self.custom_lookup_rows

        super(req_NeedRepresent,
              self).__init__(lookup = "req_need",
                             fields = ["req_need.name",
                                       "req_need_tag.value",
                                       ],
                             show_link = show_link,
                             multiple = multiple,
                             )

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=None):
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
    def represent_row(self, row):
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
        """

        T = current.T
        db = current.db

        # Extract the data
        table = current.s3db.req_need_line
        status = table.status
        number = table.id.count()
        query = (table.deleted == False)
        rows = db(query).select(status, number, groupby = status)

        # Build data structure for chart renderer
        rows = dict((row[status], row[number]) for row in rows)
        data = []
        for code, label, color in cls.REQ_STATUS:
            value = rows.get(code)
            data.append({"label": s3_str(label),
                         "value": value if value else 0,
                         "color": color,
                         })

        return data

    # -------------------------------------------------------------------------
    @classmethod
    def needs_by_district(cls):
        """
            Count need lines per district and status (top 5 districts)
        """

        T = current.T

        db = current.db
        s3db = current.s3db

        table = s3db.req_need_line
        ntable = s3db.req_need

        left = ntable.on(ntable.id == table.need_id)

        status = table.status
        number = table.id.count()
        location = ntable.location_id

        # Get the top-5 locations by number of need lines
        query = (table.deleted == False) & \
                (location != None)
        rows = db(query).select(location,
                                number,
                                left = left,
                                groupby = location,
                                orderby = ~(number),
                                limitby = (0, 5),
                                )
        locations = [row[location] for row in rows]

        data = []
        if locations:
            # Get labels for locations
            from s3 import S3Represent
            location_represent = S3Represent(lookup="gis_location", fields=["L2"])
            location_labels = location_represent.bulk(locations)

            # Count need lines per status and location
            query = (table.deleted == False) & \
                    (location.belongs(locations))
            rows = db(query).select(location,
                                    status,
                                    number,
                                    left = left,
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
                          }
                values = []
                per_location = per_status.get(code)
                for location_id in locations:
                    if per_location:
                        value = per_location.get(location_id)
                    else:
                        value = None
                    item = {"label": location_labels.get(location_id),
                            "value": value if value else 0,
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
        """

        db = current.db
        s3db = current.s3db

        table = s3db.req_need_line

        query = (table.deleted == False)
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
            values.append({"label": s3_str(represent(row[demographic])),
                           "value": value if value else 0,
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

            NB requires write-permission for static/data/SHARE folder+files
        """

        SEPARATORS = (",", ":")

        import os
        base = os.path.join(current.request.folder, "static", "data", "SHARE")

        path = os.path.join(base, "needs_by_status.json")
        data = cls.needs_by_status()
        with open(path, "wb") as outfile:
            json.dump(data, outfile, separators=SEPARATORS, encoding="utf-8")

        path = os.path.join(base, "needs_by_district.json")
        data = cls.needs_by_district()
        with open(path, "wb") as outfile:
            json.dump(data, outfile, separators=SEPARATORS, encoding="utf-8")

        path = os.path.join(base, "people_affected.json")
        data = cls.people_affected()
        with open(path, "wb") as outfile:
            json.dump(data, outfile, separators=SEPARATORS, encoding="utf-8")

# END =========================================================================
