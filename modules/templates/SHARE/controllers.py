# -*- coding: utf-8 -*-

from gluon import *
#from gluon import current
from gluon.storage import Storage
from s3 import s3_str, \
               S3CustomController, \
               S3FilterForm, S3DateFilter, S3OptionsFilter, \
               S3Represent


THEME = "SHARE"

# =============================================================================
class index(S3CustomController):
    """
        Custom Home Page
        - simple CMS with links to Dashboard, etc
    """

    def __call__(self):

        T = current.T

        output = {}

        output["active_events"] = DIV(H3("Southwest Monsoon May 2018"),
                                      P("Water levels of main rivers are currently showing normal levels in many stations. However , one station is at Alert level in Kalu Ganga & Nilwala river falling slowly."),
                                      HR(),
                                      H3("Southwest Monsoon May 2018"),
                                      P("Water levels of main rivers are currently showing normal levels in many stations. However , one station is at Alert level in Kalu Ganga & Nilwala river falling slowly."),
                                      HR(),
                                      H3("Southwest Monsoon May 2018"),
                                      P("Water levels of main rivers are currently showing normal levels in many stations. However , one station is at Alert level in Kalu Ganga & Nilwala river falling slowly."),
                                      )

        map_btn = A(T("MAP OF CURRENT NEEDS"),
                    _href = URL(c="default",
                                f="index",
                                args="dashboard",
                                ),
                    )

        create_btn = A(T("CREATE A NEED"),
                       _href = URL(c="req",
                                   f="need",
                                   args="create",
                                   ),
                       )
                       
        output["needs_btn"] = DIV(map_btn,
                                  " | ",
                                  create_btn,
                                  _class = "button round",
                                  )

        output["about_btn"] = A("%s >" % T("Read More"),
                                _href = URL(c="default",
                                            f="about",
                                            ),
                                )

        self._view(THEME, "index.html")

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
        ftable = s3db.gis_layer_feature
        query = (ftable.controller == "req") & \
                (ftable.function == "need")
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

        _map = current.gis.show_map(callback='''S3.search.s3map()''',
                                    catalogue_layers=True,
                                    collapsed=True,
                                    feature_resources=feature_resources,
                                    save=False,
                                    search=True,
                                    toolbar=True,
                                    )
        output["_map"] = _map

        # ---------------------------------------------------------------------
        # Display needs list
        resource = s3db.resource("req_need")
        #resource.table.commit_status.represent = None
        list_id = "req_datalist"
        list_fields = [#"purpose",
                       "location_id",
                       "priority",
                       #"req_ref",
                       #"site_id",
                       "date",
                       ]
        # Order with most recent request first
        orderby = "req_need.date"
        datalist, numrows = resource.datalist(fields = list_fields,
                                              limit = None,
                                              list_id = list_id,
                                              orderby = orderby,
                                              )
        if numrows == 0:
            current.response.s3.crud_strings["req_need"].msg_no_match = T("No needs at present.")

        ajax_url = URL(c="req", f="need", args="datalist.dl",
                       vars={"list_id": list_id})
        #@ToDo: Implement pagination properly
        output[list_id] = datalist.html(ajaxurl = ajax_url,
                                        pagesize = 0,
                                        )

        # ----------------------------
        # Filter Form
        # - can we have a single form for both Activities & Needs?
        #
        filter_widgets = [S3OptionsFilter("priority",
                                          label=T("Priority"),
                                          ),
                          S3DateFilter("date",
                                       label = T("Date"),
                                       hide_time=True,
                                       ),
                          ]
        filter_form = S3FilterForm(filter_widgets,
                                   ajax=True,
                                   submit=True,
                                   url=ajax_url,
                                   )
        output["req_filter_form"] = filter_form.html(resource, request.get_vars, list_id)

        # View title
        output["title"] = current.deployment_settings.get_system_name()

        self._view(THEME, "dashboard.html")

        # Custom JS
        current.response.s3.scripts.append("/%s/static/themes/SHARE/js/homepage.js" % request.application)

        return output

# =============================================================================
class project_ActivityRepresent(S3Represent):
    """ Representation of Activities by Organisation """

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

# END =========================================================================
