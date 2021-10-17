# -*- coding: utf-8 -*-

import datetime
from os import path

from gluon import *
from gluon.storage import Storage

from s3 import ICON, IS_FLOAT_AMOUNT, s3_str, \
               S3CustomController, S3Report, s3_request, S3Represent

from s3db.inv import SHIP_DOC_PENDING, SHIP_DOC_COMPLETE, \
                     SHIP_STATUS_SENT, SHIP_STATUS_RECEIVED, SHIP_STATUS_RETURNING

from s3db.pr import OU

THEME = "RMS"

# =============================================================================
def auth_formstyle(form, fields, *args, **kwargs):
    """
        Formstyle for the Login box on the homepage
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        if hasattr(widget, "element"):
            submit = widget.element("input",
                                    _type = "submit",
                                    )
            if submit:
                submit.add_class("small primary button")
            elif label:
                widget["_placeholder"] = label[0]

        return DIV(widget,
                   _class = "row",
                   _id = row_id,
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

# -----------------------------------------------------------------------------
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        auth = current.auth

        if auth.is_logged_in():
            response = current.response
            if response.confirmation:
                has_role = auth.s3_has_role
                if has_role("wh_operator", include_admin=False) or \
                   has_role("logs_manager", include_admin=False):
                    # Redirect to WMS Dashboard
                    current.session.confirmation = response.confirmation
                    redirect(URL(c="inv", f="index"))

            login_form = ""
        else:
            auth.settings.label_separator = ""
            formstyle = auth_formstyle
            login_form = auth.login(formstyle = formstyle)

        output = {"login_form": login_form,
                  }

        self._view(THEME, "index.html")
        return output

# =============================================================================
class apps(S3CustomController):
    """ App Switcher """

    def __call__(self):

        T = current.T
        auth = current.auth
        has_roles = auth.s3_has_roles
        ORG_ADMIN = current.session.s3.system_roles.ORG_ADMIN

        # Which apps are available for this user?
        apps = []
        apps_append = apps.append
        _div = self.div

        if has_roles((ORG_ADMIN,
                      "hr_manager",
                      "hr_assistant",
                      "training_coordinator",
                      "training_assistant",
                      "surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("Human Talent"),
                             url = URL(c = "hrm",
                                       f = "index",
                                       ),
                             image = "human_talent.png",
                             _class = "alh",
                             ))

        if has_roles((ORG_ADMIN,
                      "training_coordinator",
                      "training_assistant",
                      "ns_training_manager",
                      "ns_training_assistant",
                      "surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("Training"),
                             url = URL(c = "hrm",
                                       f = "training_event",
                                       ),
                             image = "training.png",
                             ))

        if auth.permission.accessible_url(c = "member",
                                          f = "membership",
                                          ):
            apps_append(_div(label = T("Partners"),
                             url = URL(c = "member",
                                       f = "membership",
                                       ),
                             image = "partners.png",
                             ))

        if has_roles((ORG_ADMIN,
                      "wh_operator",
                      "logs_manager",
                      )):
            wh_url = URL(c = "inv",
                         f = "index",
                         )
        else:
            # Normal users see Warehouses module, but have a different page
            wh_url = URL(c = "inv",
                         f = "req",
                         )
        apps_append(_div(label = T("Warehouses"),
                         url = wh_url,
                         image = "warehouses.png",
                         _class = "alw",
                         ))

        if has_roles(("project_reader",
                      "project_manager",
                      "monitoring_evaluation",
                      )):
            apps_append(_div(label = T("Projects"),
                             url = URL(c = "project",
                                       f = "project",
                                       args = "summary",
                                       ),
                             image = "projects.png",
                             ))

        if has_roles(("surge_capacity_manager",
                      "disaster_manager",
                      )):
            apps_append(_div(label = T("RIT"),
                             url = URL(c = "deploy",
                                       f = "mission",
                                       args = "summary",
                                       vars = {"status__belongs": 2},
                                       ),
                             image = "RIT.png",
                             ))

        # Layout the apps
        len_apps = len(apps)
        if len_apps == 0:
            # No Apps available
            # This generally gets caught earlier & user sees no App Switcher at all
            resize = True
            height = 112
            width = 110
            apps = DIV(_class = "row",
                       )
        elif len_apps == 1:
            # 1x1
            resize = True
            height = 112
            width = 110
            apps[0]["_class"] = "small-12 columns"
            apps = DIV(apps[0],
                       _class = "row",
                       )
        elif len_apps == 2:
            # 1x2
            resize = True
            height = 112
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps = DIV(apps[0],
                       apps[1],
                       _class = "row",
                       )
        elif len_apps == 3:
            # 2x2
            resize = True
            height = 224
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps[2]["_class"] = "small-6 columns"
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               _class = "row",
                               ),
                           DIV(apps[2],
                               _class = "row",
                               ),
                           )
        elif len_apps == 4:
            # 2x2
            resize = True
            height = 224
            width = 220
            apps[0]["_class"] = "small-6 columns"
            apps[1]["_class"] = "small-6 columns"
            apps[2]["_class"] = "small-6 columns"
            apps[3]["_class"] = "small-6 columns"
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               _class = "row",
                               ),
                           DIV(apps[2],
                               apps[3],
                               _class = "row",
                               ),
                           )
        else:
            # 2xX
            resize = False
            row2 = DIV(apps[3],
                       apps[4],
                       _class = "row",
                       )
            if len_apps == 6:
                row2.append(apps[5])
            apps = TAG[""](DIV(apps[0],
                               apps[1],
                               apps[2],
                               _class = "row",
                               ),
                           row2,
                           )

        output = {"apps": apps,
                  }

        if resize:
            # Insert JS to resize the parent iframe
            output["js"] = '''window.parent.$('#apps-frame').parent().height(%s).width(%s)''' % \
                                (height, width)

        self._view(THEME, "apps.html")
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def div(label,
            url,
            image,
            _class = None
            ):

        if _class:
            #Extra class on label's span to fit it in better
            _class = "al %s" % _class
        else:
            _class = "al"

        div = DIV(DIV(A(IMG(_src = URL(c="static", f="themes",
                                       args = [THEME,
                                               "img",
                                               image,
                                               ]),
                            _class = "ai",
                            _height = "64",
                            _width = "64",
                            ),
                        SPAN(label,
                             _class = _class,
                             ),
                        _href = url,
                        _target = "_top",
                        ),
                      _class = "ah",
                      ),
                  _class = "small-4 columns",
                  )

        return div

# =============================================================================
def deploy_index():
    """
        Custom module homepage for deploy (=RIT) to display online
        documentation for the module
    """

    def prep(r):
        default_url = URL(f="mission", args="summary", vars={})
        return current.s3db.cms_documentation(r, "RIT", default_url)
    current.response.s3.prep = prep
    output = current.rest_controller("cms", "post")

    # Custom view
    S3CustomController._view(THEME, "deploy_index.html")
    return output

# =============================================================================
def inv_operators_for_sites(site_ids):
    """
        Determine to whom Alerts should be sent for specific Site(s)

        @ToDo: Use site_contact instead?
            + Much faster/more generic lookup for the Server
            - More to setup for the Users
            Need to allow visibility of HRM
            Need to expose field
            Ideally do this automatically for new users? Hard!
    """

    db = current.db
    s3db = current.s3db

    stable = s3db.org_site
    site_entities = db(stable.site_id.belongs(site_ids)).select(stable.site_id,
                                                                stable.instance_type,
                                                                )
    # Sort by Instance Type
    sites_by_type = {}
    for row in site_entities:
        instance_type = row.instance_type
        if instance_type not in sites_by_type:
            sites_by_type[instance_type] = []
        sites_by_type[instance_type].append(row.site_id)

    # Lookup Names & PE IDs
    sites = {}
    for instance_type in sites_by_type:
        itable = s3db.table(instance_type)
        instances = db(itable.site_id.belongs(sites_by_type[instance_type])).select(itable.name,
                                                                                    itable.pe_id,
                                                                                    itable.site_id,
                                                                                    )
        for row in instances:
            sites[row.site_id] = {"name": row.name,
                                  "pe_id": row.pe_id,
                                  }
    gtable = db.auth_group
    mtable = db.auth_membership
    utable = db.auth_user
    ltable = s3db.pr_person_user

    atable = s3db.pr_affiliation
    rtable = s3db.pr_role

    # Lookup realm for all wh_operator/logs_manager with default realm outside of loop
    # Incorporates a Bulk version of s3db.pr_realm()
    query = (gtable.uuid.belongs(("wh_operator",
                                  "logs_manager",
                                  ))) & \
            (gtable.id == mtable.group_id) & \
            (mtable.pe_id == None) & \
            (mtable.deleted == False) & \
            (mtable.user_id == utable.id) & \
            (utable.id == ltable.user_id) & \
            (atable.pe_id == ltable.pe_id) & \
            (atable.deleted == False) & \
            (atable.role_id == rtable.id) & \
            (rtable.deleted == False) & \
            (rtable.role_type == OU)
    wh_operators_default_realm = db(query).select(ltable.pe_id,
                                                  ltable.user_id,
                                                  utable.language,
                                                  rtable.pe_id,
                                                  )

    use_admin = []

    for site_id in sites:

        site = sites[site_id]
        pe_id = site["pe_id"]

        # Find the relevant wh_operator/logs_manager
        entities = s3db.pr_get_ancestors(pe_id)
        entities.append(pe_id)

        query = (gtable.uuid.belongs(("wh_operator",
                                      "logs_manager",
                                      ))) & \
                (gtable.id == mtable.group_id) & \
                (mtable.pe_id.belongs(entities)) & \
                (mtable.deleted == False) & \
                (mtable.user_id == utable.id) & \
                (utable.id == ltable.user_id)
        operators = db(query).select(ltable.pe_id,
                                     ltable.user_id,
                                     utable.language,
                                     )
        operators = list(operators)
        for row in wh_operators_default_realm:
            if row["pr_role.pe_id"] in entities:
                operators.append(row)

        if operators:
            site["operators"] = operators
        else:
            # Send to ADMIN instead
            use_admin.append(site_id)

    if use_admin:
        query = (gtable.uuid == "ADMIN") & \
                (gtable.id == mtable.group_id) & \
                (mtable.deleted == False) & \
                (mtable.user_id == utable.id) & \
                (utable.id == ltable.user_id)
        operators = db(query).select(ltable.pe_id,
                                     ltable.user_id,
                                     utable.language,
                                     )
        for site_id in use_admin:
            sites[site_id]["operators"] = operators

    return sites

# =============================================================================
class inv_dashboard(S3CustomController):
    """
        Dashboard for Warehouse Management module
        - used as homepage
    """

    def __call__(self):

        T = current.T
        db = current.db
        s3db = current.s3db
        user = current.auth.user
        user_id = user.id

        # Huuricane Season lasts from 1/6 to 30/11
        now = current.request.utcnow
        if 5 < now.month < 12:
            SEASON = T("this Season")
            SEASON_START = datetime.date(now.year, 6, 1)
            SEASON_END = None
        else:
            SEASON = T("last Season")
            last_year = now.year - 1
            SEASON_START = datetime.date(last_year, 6, 1)
            SEASON_END = datetime.date(last_year, 12, 1)

        # Shipments
        stable = s3db.inv_send
        fields = ["id",
                  "send_ref",
                  "date",
                  "site_id",
                  "to_site_id",
                  "transport_type",
                  "status",
                  "filing_status",
                  ]
        sresource = s3db.resource("inv_send",
                                  filter = (stable.date != None), # Don't include Unsent Shipments
                                  )
        srows = sresource.select(fields,
                                 as_rows = True,
                                 limit = 5,
                                 orderby = ~stable.date,
                                 )

        rtable = s3db.inv_recv
        fields = ["id",
                  "recv_ref",
                  "date",
                  "site_id",
                  "from_site_id",
                  "transport_type",
                  "status",
                  "filing_status",
                  ]
        rresource = s3db.resource("inv_recv",
                                  filter = (rtable.date != None), # Don't include Unreceived Shipments
                                  )
        rrows = rresource.select(fields,
                                 as_rows = True,
                                 limit = 5,
                                 orderby = ~rtable.date,
                                 )
        rtotal = len(rrows)

        # Find the most recent 5 from both lists
        shipments = []
        sappend = shipments.append
        rindex = 0
        stotal = 0
        for srow in srows:
            if rindex < rtotal:
                rrow = rrows[rindex]
            else:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            send_date = srow.date
            recv_date = rrow.date
            if send_date > recv_date:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            rrow.type = "recv"
            sappend(rrow)
            if stotal == 4:
                break
            stotal += 1
            rindex += 1
            if rindex < rtotal:
                rrow = rrows[rindex]
            else:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            recv_date = rrow.date
            if send_date > recv_date:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            rrow.type = "recv"
            sappend(rrow)
            if stotal == 4:
                break
            stotal += 1
            rindex += 1
            if rindex < rtotal:
                rrow = rrows[rindex]
            else:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            recv_date = rrow.date
            if send_date > recv_date:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            rrow.type = "recv"
            sappend(rrow)
            if stotal == 4:
                break
            stotal += 1
            rindex += 1
            if rindex < rtotal:
                rrow = rrows[rindex]
            else:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            recv_date = rrow.date
            if send_date > recv_date:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            rrow.type = "recv"
            sappend(rrow)
            if stotal == 4:
                break
            stotal += 1
            rindex += 1
            if rindex < rtotal:
                rrow = rrows[rindex]
            else:
                srow.type = "send"
                sappend(srow)
                if stotal == 4:
                    break
                stotal += 1
                continue
            recv_date = rrow.date
            if send_date > recv_date:
                srow.type = "send"
                sappend(srow)
                stotal += 1
                break
            rrow.type = "recv"
            sappend(rrow)
            stotal += 1
            break

        while stotal < 5:
            if rindex < rtotal:
                rrow = rrows[rindex]
            else:
                break
            rrow.type = "recv"
            sappend(rrow)
            rindex += 1
            stotal += 1

        date_represent = stable.date.represent
        status_represent = stable.status.represent

        site_ids = []
        for row in shipments:
            if row.type == "send":
                site_ids += [row.site_id,
                             row.to_site_id,
                             ]
            else:
                site_ids += [row.site_id,
                             row.from_site_id,
                             ]
        #sites = org_SiteRepresent(show_type = False).bulk(list(set(site_ids)))
        sites = S3Represent(lookup = "org_site").bulk(list(set(site_ids)))
        sites_get = sites.get

        transport_opts = {"Air": ICON("plane"),
                          "Sea": ICON("ship"),
                          "Road": ICON("truck"),
                          "Hand": ICON("hand-grab"),
                          }
        transport_opts_get = transport_opts.get

        filing_opts = {SHIP_DOC_PENDING: ICON("close"),
                       SHIP_DOC_COMPLETE: ICON("check"),
                       }
        filing_opts_get = filing_opts.get

        shipment_rows = [DIV(DIV(T("Date"),
                                 _class = "columns medium-2",
                                 ),
                             DIV(T("in/out"),
                                 _class = "columns medium-1",
                                 ),
                             DIV(T("From"),
                                 _class = "columns medium-1",
                                 ),
                             DIV(T("To"),
                                 _class = "columns medium-1",
                                 ),
                             DIV(T("WB/GRN"),
                                 _class = "columns medium-4",
                                 ),
                             DIV(T("Trans."),
                                 _class = "columns medium-1",
                                 ),
                             DIV(T("Status"),
                                 _class = "columns medium-1",
                                 ),
                             DIV(ICON("briefcase"),
                                 _class = "columns medium-1",
                                 ),
                             _class = "ship-card row",
                             ),
                        ]
        sappend = shipment_rows.append

        for row in shipments:
            if row.type == "send":
                in_out = ICON("arrow-right")
                from_site_id = row.site_id
                to_site_id = row.to_site_id
                shipment_ref = row.send_ref
                url = URL(c="inv", f="send",
                          args = [row["inv_send.id"]],
                          )
            else:
                in_out = ICON("arrow-left")
                from_site_id = row.from_site_id
                to_site_id = row.site_id
                shipment_ref = row.recv_ref
                url = URL(c="inv", f="recv",
                          args = [row.id],
                          )

            sappend(DIV(DIV(date_represent(row.date),
                            _class = "columns medium-2",
                            ),
                        DIV(in_out,
                            _class = "columns medium-1",
                            ),
                        DIV(sites_get(from_site_id),
                            _class = "columns medium-1",
                            ),
                        DIV(sites_get(to_site_id),
                            _class = "columns medium-1",
                            ),
                        DIV(A(shipment_ref,
                              _href = url,
                              ),
                            _class = "columns medium-4",
                            ),
                        DIV(transport_opts_get(row.transport_type),
                            _class = "columns medium-1",
                            ),
                        DIV(status_represent(row.status),
                            _class = "columns medium-1",
                            ),
                        DIV(filing_opts_get(row.filing_status),
                            _class = "columns medium-1",
                            ),
                        _class = "ship-card row",
                        ))

        shipments = DIV(*shipment_rows)

        # Alerts
        table = s3db.auth_user_notification
        query = (table.user_id == user_id) & \
                (table.deleted == False)
        rows = db(query).select(table.name,
                                table.url,
                                orderby = ~table.created_on,
                                )
        alert_rows = []
        for row in rows:
            alert_rows.append(DIV(A(DIV(ICON("bell-o"),
                                        _class = "columns medium-1"
                                        ),
                                    DIV(row.name,
                                        _class = "columns medium-11"
                                        ),
                                    _href = row.url,
                                    _target = "_blank",
                                    ),
                                  _class = "alert-card row",
                                  ))
        alerts = DIV(*alert_rows)

        # Capacity
        # Define the Pivot Table
        r = s3_request("inv", "inv_item")
        r.customise_resource()
        resource = s3db.resource("inv_inv_item")
        report = S3Report()
        report.resource = resource
        capacity = report.widget(r,
                                 widget_id = "capacity",
                                 ajaxurl = URL(c="inv", f="inv_item",
                                               args = "report.json"
                                               ),
                                 )

        # KPI
        # Which Warehouses are we responsible for?
        wtable = s3db.inv_warehouse
        gtable = db.auth_group
        mtable = db.auth_membership
        query = (mtable.user_id == user_id) & \
                (mtable.deleted == False) & \
                (mtable.group_id == gtable.id) & \
                (gtable.uuid.belongs("ORG_ADMIN",
                                     "logs_manager",
                                     "wh_operator",
                                     ))
        realms = db(query).select(mtable.pe_id)
        realms = list(set([row.pe_id for row in realms]))
        if None in realms:
            realms.remove(None)
            # Lookup Default Realm
            from s3db.pr import pr_default_realms
            default_realms = pr_default_realms(user.pe_id)
            realms = realms + default_realms
        from s3db.pr import pr_get_descendants
        child_pe_ids = pr_get_descendants(realms, entity_types=["inv_warehouse"])
        warehouses = db(wtable.pe_id.belongs(realms + child_pe_ids)).select(wtable.site_id,
                                                                            wtable.name,
                                                                            wtable.free_capacity,
                                                                            )
        wh_site_ids = [row.site_id for row in warehouses]

        itable = s3db.inv_inv_item
        fields = ["site_id",
                  "total_weight",
                  "total_volume",
                  "quantity",       # extra_fields
                  "item_pack_id$quantity", # extra_fields
                  "item_id.weight", # extra_fields
                  "item_id.volume", # extra_fields
                  ]
        iresource = s3db.resource("inv_inv_item",
                                  filter = (itable.site_id.belongs(wh_site_ids)),
                                  )
        rows = iresource.select(fields, as_rows=True)
        stockpile_weight = 0
        stockpile_volume = 0
        for row in rows:
            stockpile_weight += row["inv_inv_item.total_weight"]()
            stockpile_volume += row["inv_inv_item.total_volume"]()

        fields = ["id",
                  "track_item.total_weight",
                  "track_item.total_volume",
                  "track_item.quantity",       # extra_fields
                  "track_item.item_pack_id$quantity", # extra_fields
                  "track_item.item_id$weight", # extra_fields
                  "track_item.item_id$volume", # extra_fields
                  ]
        query = (stable.status.belongs([SHIP_STATUS_SENT,
                                        SHIP_STATUS_RECEIVED,
                                        SHIP_STATUS_RETURNING,
                                        ])) & \
                (stable.date > SEASON_START)
        if SEASON_END:
            query &= (stable.date > SEASON_END)
        sresource = s3db.resource("inv_send", filter = query)
        srows = sresource.select(fields, as_rows = True)
        num_shipments = len(set([row["inv_send.id"] for row in srows]))
        shipments_weight = 0
        shipments_volume = 0
        for row in srows:
            weight = row["inv_track_item.total_weight"]()
            try:
                shipments_weight += weight
            except TypeError:
                # NONE returned: ignore
                pass
            volume = row["inv_track_item.total_volume"]()
            try:
                shipments_volume += volume
            except TypeError:
                # NONE returned: ignore
                pass

        float_represent = IS_FLOAT_AMOUNT.represent

        free_capacities = UL()
        for row in warehouses:
            free_capacities.append(LI("%s: %s m3" % (row.name, float_represent(row.free_capacity, precision=1))))

        kpi = UL(LI("%s: %s kg" % (T("Total weight stockpiled"), float_represent(stockpile_weight, precision=1))),
                 LI("%s: %s m3" % (T("Total volume stockpiled"), float_represent(stockpile_volume, precision=1))),
                 LI("%s %s: %s" % (T("Number of Shipments sent"), SEASON, num_shipments)),
                 LI("%s %s: %s kg" % (T("Total weight sent"), SEASON, float_represent(shipments_weight, precision=1))),
                 LI("%s %s: %s m3" % (T("Total volume sent"), SEASON, float_represent(shipments_volume, precision=3))),
                 LI("%s: %s" % (T("Number of warehouses"), len(warehouses))),
                 LI("%s:" % T("Remaining stockpile capacities available"),
                    free_capacities
                    ),
                 )

        # Preparedness Checklist
        #checklist = UL()

        output = {"title": T("Dashboard"),
                  "shipments": shipments,
                  "alerts": alerts,
                  "capacity": capacity,
                  "kpi": kpi,
                  #"checklist": checklist,
                  }

        # Custom view
        self._view(THEME, "inv_dashboard.html")
        return output

# =============================================================================
class org_SiteRepresent(S3Represent):
    """
        Representation of Sites
        - include Organisation for sites outside own NS
        - ensure these are sorted below those within NS
    """

    def __init__(self,
                 show_link = False,
                 show_type = True,
                 ):

        # Need a custom lookup
        self.lookup_rows = self.custom_lookup_rows

        user = current.auth.user
        if user:
            self.organisation_id = org_id = user.organisation_id
            if org_id:
                from s3db.org import org_root_organisation
                self.root_org = current.cache.ram("root_org_%s" % org_id, # Same key as auth.root_org()
                                                  lambda: org_root_organisation(org_id),
                                                  time_expire=120
                                                  )
            else:
                self.root_org = None
        else:
            self.organisation_id = None
            self.root_org = None

        self.org_labels = {}
        self.show_type = show_type

        super(org_SiteRepresent, self).__init__(lookup = "org_site",
                                                fields = ["name"],
                                                show_link = show_link,
                                                )

    # -------------------------------------------------------------------------
    def bulk(self, values, rows=None, list_type=False, show_link=True, include_blank=True):
        """
            Represent multiple values as dict {value: representation}

            @param values: list of values
            @param rows: the referenced rows (if values are foreign keys)
            @param show_link: render each representation as link
            @param include_blank: Also include a blank value

            @return: a dict {value: representation}
        """

        show_link = show_link and self.show_link
        if show_link and not rows:
            # Retrieve the rows
            rows = self.lookup_rows(None, values)

        self._setup()

        # Get the values
        if rows and self.table:
            values = [row["org_site.site_id"] for row in rows]
        else:
            values = [values] if type(values) is not list else values

        # Lookup the representations
        if values:
            labels = self._lookup(values, rows=rows)
            if show_link:
                link = self.link
                rows = self.rows
                labels = {k: link(k, v, rows.get(k)) for k, v in labels.items()}
            for v in values:
                if v not in labels:
                    labels[v] = self.default
        else:
            labels = {}
        if include_blank:
            labels[None] = self.none
        return labels

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for site rows, does a left join with any
            instance_types found.
            Parameters key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the site IDs
        """

        db = current.db
        s3db = current.s3db
        stable = s3db.org_site
        otable = s3db.org_organisation

        show_type = self.show_type
        show_link = self.show_link

        count = len(values)
        if count == 1:
            value = values[0]
            query = (stable.site_id == value) & \
                    (stable.organisation_id == otable.id)
        else:
            query = (stable.site_id.belongs(values)) & \
                    (stable.organisation_id == otable.id)
        limitby = (0, count)

        fields = [stable.name,
                  stable.site_id,
                  otable.id,
                  otable.root_organisation,
                  ]
        if show_type or show_link:
            fields.append(stable.instance_type)

        rows = db(query).select(limitby=limitby, *fields)
        self.queries += 1

        # Lookup represent for all Orgs
        orgs = set(row["org_organisation.id"] for row in rows)
        root_orgs = set(row["org_organisation.root_organisation"] for row in rows if row["org_organisation.root_organisation"] not in orgs)
        from s3db.org import org_OrganisationRepresent
        self.org_labels = org_OrganisationRepresent(parent = False,
                                                    acronym = False,
                                                    ).bulk(list(orgs) + list(root_orgs))

        if show_type or show_link:

            # Collect the site_ids
            site_ids = set(row["org_site.site_id"] for row in rows)

            # Retrieve the facility type links
            ltable = s3db.org_site_facility_type
            query = ltable.site_id.belongs(site_ids)
            links = db(query).select(ltable.site_id,
                                     ltable.facility_type_id,
                                     )

            # Collect all type IDs and type IDs per site_id
            all_types = set()
            facility_types = {}

            for link in links:

                facility_type_id = link.facility_type_id
                all_types.add(facility_type_id)

                site_id = link.site_id
                if site_id in facility_types:
                    facility_types[site_id].append(facility_type_id)
                else:
                    facility_types[site_id] = [facility_type_id]

            # Bulk-represent all type IDs
            # (stores the representations in the S3Represent)
            if show_type:
                ltable.facility_type_id.represent.bulk(list(all_types))

            # Add the list of corresponding type IDs to each row
            for row in rows:
                row.facility_types = facility_types.get(row["org_site.site_id"]) or []

        if show_link:

            # Collect site_ids per instance type
            site_ids = {}
            for row in rows:
                instance_type = row["org_site.instance_type"]
                if instance_type in site_ids:
                    site_ids[instance_type].add(row["org_site.site_id"])
                else:
                    site_ids[instance_type] = {row["org_site.site_id"]}

            # Retrieve site ID / instance ID pairs per instance_type
            instance_ids = {}
            for instance_type in site_ids:
                table = s3db.table(instance_type)
                if not table:
                    continue
                query = table.site_id.belongs(site_ids[instance_type])
                instances = db(query).select(table._id,
                                             table.site_id,
                                             )
                self.queries += 1
                key = table._id.name
                for instance in instances:
                    instance_ids[instance.site_id] = instance[key]

            # Add the instance ID to each row
            for row in rows:
                row.instance_id = instance_ids.get(row["org_site.site_id"])

        return rows

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

            @param k: the key (site_id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        if row:
            try:
                instance_type = row["org_site.instance_type"]
                instance_id = row.instance_id
            except (AttributeError, KeyError):
                return v
            else:
                c, f = instance_type.split("_", 1)
                return A(v, _href=URL(c=c, f=f, args=[instance_id],
                                      # remove the .aaData extension in paginated views
                                      extension=""
                                      ))
        else:
            # We have no way to determine the linkto
            return v

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the org_site Row
        """

        name = row["org_site.name"]

        if not name:
            return self.default

        if self.show_type:
            instance_type = row["org_site.instance_type"]
            facility_types = row.get("facility_types")

            if facility_types:
                represent = current.s3db.org_site_facility_type.facility_type_id.represent
                type_names = represent.multiple(facility_types)
                name = "%s (%s)" % (name, type_names)
            else:
                instance_type = current.auth.org_site_types.get(instance_type, None)
                if instance_type:
                    name = "%s (%s)" % (name, instance_type)

        organisation_id = row.get("org_organisation.id")
        root_org = row.get("org_organisation.root_organisation")
        ns = None
        parent = None
        if root_org == self.root_org:
            if organisation_id != self.organisation_id:
                parent = self.org_labels.get(organisation_id)
        else:
            ns = self.org_labels.get(root_org)
            if root_org != organisation_id:
                parent = self.org_labels.get(organisation_id)
            
        if ns:
            if parent:
                name = "ᛜᛜ%s > %s > %s" % (ns, parent, name)
            else:
                name = "ᛜᛜ%s > %s" % (ns, name)
        elif parent:
            name = "ᛜ%s > %s" % (parent, name)

        return s3_str(name)

# END =========================================================================
