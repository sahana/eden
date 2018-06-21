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

        #------------------------------------------------------------
        # Allow editing of page content from browser using CMS module
        if current.deployment_settings.has_module("cms"):
            system_roles = current.auth.get_system_roles()
            ADMIN = system_roles.ADMIN in current.session.s3.roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            custom_info = current.db(query).select(table.body,
                                            table.id,
                                            limitby=(0, 1)).first()
            if custom_info:
                if ADMIN:
                    custom_info = DIV(XML(custom_info.body),
                               BR(),
                               A(current.T("Edit"),
                                 _href=URL(c="cms", f="post",
                                           args=[custom_info.id, "update"]),
                                 _class="action-btn"))
                else:
                    custom_info = DIV(XML(custom_info.body))
            elif ADMIN:
                if current.response.s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                custom_info = A(current.T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module": module,
                                         "resource": resource
                                         }),
                         _class="%s cms-edit" % _class)
            else:
                custom_info = ""
        else:
            custom_info = ""
        output["custom_info"] = custom_info

        #----------------------
        # Button to upload 4W data
        upload_4W_activity_btn = A(T("Upload 4W Activity"),
                         _href = URL(c="project",
                                     f="activity",
                                     args="import",
                                     ),
                         _class = "action-btn button small",
                         )
        output["upload_4W_activity_btn"] = upload_4W_activity_btn

        #----------------------
        # Button to access Dashboard
        dashboard_btn = A(T("Dashboard"),
                          _href = URL(c="default",
                                      f="index",
                                      args="dashboard",
                                      ),
                          _class = "action-btn button small",
                          )
        output["dashboard_btn"] = dashboard_btn

        # View title
        output["title"] = current.deployment_settings.get_system_name()

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
