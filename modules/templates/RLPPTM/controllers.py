# -*- coding: utf-8 -*-

import json
from uuid import uuid4

from gluon import Field, HTTP, SQLFORM, URL, current, redirect, \
                  CRYPT, IS_EMAIL, IS_EMPTY_OR, IS_EXPR, IS_IN_SET, IS_LENGTH, \
                  IS_LOWER, IS_NOT_EMPTY, IS_NOT_IN_DB, \
                  A, BR, DIV, FORM, H3, H4, I, INPUT, LI, TAG, TABLE, TD, TR, UL, XML

from gluon.storage import Storage

from s3 import FS, IS_PHONE_NUMBER_MULTI, JSONERRORS, S3CRUD, S3CustomController, \
               S3GroupedOptionsWidget, S3LocationSelector, S3Represent, S3Request, \
               S3WithIntro, s3_comments_widget, s3_get_extension, s3_mark_required, \
               s3_str, s3_text_represent, s3_truncate

from .config import TESTSTATIONS
from .notifications import formatmap

TEMPLATE = "RLPPTM"
THEME = "RLP"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        s3 = current.response.s3

        auth = current.auth
        settings = current.deployment_settings


        # Defaults
        login_form = None
        login_div = None
        announcements = None
        announcements_title = None

        roles = current.session.s3.roles
        sr = auth.get_system_roles()
        if sr.AUTHENTICATED in roles:
            # Logged-in user
            # => display announcements

            from s3 import S3DateTime
            dtrepr = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

            filter_roles = roles if sr.ADMIN not in roles else None
            posts = self.get_announcements(roles=filter_roles)

            # Render announcements list
            announcements = UL(_class="announcements")
            if posts:
                announcements_title = T("Announcements")
                priority_classes = {2: "announcement-important",
                                    3: "announcement-critical",
                                    }
                priority_icons = {2: "fa-exclamation-circle",
                                  3: "fa-exclamation-triangle",
                                  }
                for post in posts:
                    # The header
                    header = H4(post.name)

                    # Priority
                    priority = post.priority
                    # Add icon to header?
                    icon_class = priority_icons.get(post.priority)
                    if icon_class:
                        header = TAG[""](I(_class="fa %s announcement-icon" % icon_class),
                                         header,
                                         )
                    # Priority class for the box
                    prio = priority_classes.get(priority, "")

                    row = LI(DIV(DIV(DIV(dtrepr(post.date),
                                        _class = "announcement-date",
                                        ),
                                    _class="fright",
                                    ),
                                 DIV(DIV(header,
                                         _class = "announcement-header",
                                         ),
                                     DIV(XML(post.body),
                                         _class = "announcement-body",
                                         ),
                                     _class="announcement-text",
                                    ),
                                 _class = "announcement-box %s" % prio,
                                 ),
                             )
                    announcements.append(row)
        else:
            # Anonymous user
            # => provide a login box
            login_div = DIV(H3(T("Login")),
                            )
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)

        output = {"login_div": login_div,
                  "login_form": login_form,
                  "announcements": announcements,
                  "announcements_title": announcements_title,
                  }

        # Custom view and homepage styles
        s3.stylesheets.append("../themes/%s/homepage.css" % THEME)
        self._view(settings.get_theme_layouts(), "index.html")

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def get_announcements(roles=None):
        """
            Get current announcements

            @param roles: filter announcement by these roles

            @returns: any announcements (Rows)
        """

        db = current.db
        s3db = current.s3db

        # Look up all announcements
        ptable = s3db.cms_post
        stable = s3db.cms_series
        join = stable.on((stable.id == ptable.series_id) & \
                         (stable.name == "Announcements") & \
                         (stable.deleted == False))
        query = (ptable.date <= current.request.utcnow) & \
                (ptable.expired == False) & \
                (ptable.deleted == False)

        if roles:
            # Filter posts by roles
            ltable = s3db.cms_post_role
            q = (ltable.group_id.belongs(roles)) & \
                (ltable.deleted == False)
            rows = db(q).select(ltable.post_id,
                                cache = s3db.cache,
                                groupby = ltable.post_id,
                                )
            post_ids = {row.post_id for row in rows}
            query = (ptable.id.belongs(post_ids)) & query

        posts = db(query).select(ptable.name,
                                 ptable.body,
                                 ptable.date,
                                 ptable.priority,
                                 join = join,
                                 orderby = (~ptable.priority, ~ptable.date),
                                 limitby = (0, 5),
                                 )

        return posts

# =============================================================================
class privacy(S3CustomController):
    """ Custom Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        ADMIN = current.auth.s3_has_role("ADMIN")

        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module

        module = "default"
        resource = "Privacy"

        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                content = DIV(XML(item.body),
                              BR(),
                              A(current.T("Edit"),
                                _href = URL(c="cms", f="post",
                                            args = [item.id, "update"],
                                            vars = {"module": module,
                                                    "resource": resource,
                                                    },
                                            ),
                                _class="action-btn",
                                ),
                              )
            else:
                content = DIV(XML(item.body))
        elif ADMIN:
            content = A(current.T("Edit"),
                        _href = URL(c="cms", f="post", args="create",
                                    vars = {"module": module,
                                            "resource": resource,
                                            },
                                    ),
                        _class="action-btn cms-edit",
                        )
        else:
            content = ""

        output["item"] = content

        self._view(THEME, "cmspage.html")
        return output

# =============================================================================
class legal(S3CustomController):
    """ Custom Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        ADMIN = current.auth.s3_has_role("ADMIN")

        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module

        module = "default"
        resource = "Legal"

        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby = (0, 1)
                                        ).first()
        if item:
            if ADMIN:
                content = DIV(XML(item.body),
                              BR(),
                              A(current.T("Edit"),
                                _href = URL(c="cms", f="post",
                                            args = [item.id, "update"],
                                            vars = {"module": module,
                                                    "resource": resource,
                                                    },
                                            ),
                                _class="action-btn",
                                ),
                              )
            else:
                content = DIV(XML(item.body))
        elif ADMIN:
            content = A(current.T("Edit"),
                        _href = URL(c="cms", f="post", args="create",
                                    vars = {"module": module,
                                            "resource": resource,
                                            },
                                    ),
                        _class="action-btn cms-edit",
                        )
        else:
            content = ""

        output["item"] = content

        self._view(THEME, "cmspage.html")
        return output

# =============================================================================
class approve(S3CustomController):
    """ Custom Approval Page """

    def __call__(self):

        T = current.T
        auth = current.auth
        db = current.db
        s3db = current.s3db
        session = current.session

        ogtable = s3db.org_group
        org_group = db(ogtable.name == TESTSTATIONS).select(ogtable.id,
                                                            ogtable.pe_id,
                                                            limitby = (0, 1)
                                                            ).first()

        try:
            org_group_pe_id = org_group.pe_id
        except:
            raise RuntimeError("Cannot approve user account as Org Group '%s' is missing " % TESTSTATIONS)

        has_role = auth.s3_has_role
        if has_role("ORG_GROUP_ADMIN",
                    for_pe = org_group_pe_id):
            ORG_ADMIN = False
        elif has_role("ORG_ADMIN"):
            ORG_ADMIN = True
        else:
            session.error = T("Not Permitted!")
            redirect(URL(c = "default",
                         f = "index",
                         args = None,
                         ))

        utable = db.auth_user
        request = current.request
        response = current.response
        org_group_id = org_group.id

        # Single User or List?
        if len(request.args) > 1:
            user_id = request.args[1]
            user = db(utable.id == user_id).select(utable.id,
                                                   utable.first_name,
                                                   utable.last_name,
                                                   utable.email,
                                                   utable.organisation_id,
                                                   utable.org_group_id,
                                                   utable.registration_key,
                                                   utable.link_user_to, # Needed for s3_approve_user
                                                   utable.site_id, # Needed for s3_link_to_human_resource (calledfrom s3_approve_user)
                                                   limitby = (0, 1)
                                                   ).first()

            if not user or user.org_group_id != org_group_id:
                session.error = T("Invalid Account!")
                redirect(URL(c = "default",
                             f = "index",
                             args = ["approve"],
                             ))

            otable = s3db.org_organisation
            organisation_id = user.organisation_id
            if organisation_id:
                org = db(otable.id == organisation_id).select(otable.name,
                                                              otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
            if ORG_ADMIN:
                if not organisation_id or \
                   not has_role("ORG_ADMIN",
                                for_pe = org.pe_id):
                    session.error = T("Account not within your Organisation!")
                    redirect(URL(c = "default",
                                 f = "index",
                                 args = ["approve"],
                                 ))

            person = "%(first_name)s %(last_name)s <%(email)s>" % {"first_name": user.first_name,
                                                                   "last_name": user.last_name,
                                                                   "email": user.email,
                                                                   }

            ttable = s3db.auth_user_temp
            temp = db(ttable.user_id == user_id).select(ttable.custom,
                                                        limitby = (0, 1)
                                                        ).first()

            try:
                custom = json.loads(temp.custom)
            except JSONERRORS:
                custom = {}

            custom_get = custom.get
            organisation = custom_get("organisation")
            if organisation:
                test_station = TR(TD("%s:" % T("Test Station")),
                                  TD(organisation),
                                  )
            else:
                test_station = None
            location = custom_get("location")
            location_get = location.get
            addr_street = location_get("addr_street")
            addr_postcode = location_get("addr_postcode")
            L1 = location_get("L1")
            L2 = location_get("L2")
            L3 = location_get("L3")
            L4 = location_get("L4")
            represent = S3Represent(lookup = "gis_location")
            address = TABLE(TR(addr_street or ""),
                            TR(addr_postcode or ""),
                            TR(represent(L4) if L4 else ""),
                            TR(represent(L3) if L3 else ""),
                            TR(represent(L2) if L2 else ""),
                            TR(represent(L1) if L1 else ""),
                            )

            facility_phone = custom_get("facility_phone") or custom_get("office_phone")
            facility_email = custom_get("facility_email")
            opening_times = custom_get("opening_times")

            # Map selected projects to the projects selectable at time of approval
            selectable_projects = register.selectable_projects()
            projects = []
            selected = custom_get("projects")
            if not isinstance(selected, (tuple, list)):
                selected = [selected]
            for v in selected:
                try:
                    project_id = int(v)
                except (ValueError, TypeError):
                    continue
                else:
                    if project_id in selectable_projects:
                        projects.append(project_id)

            # Add project selector
            field = Field("projects", "list:integer",
                          label = T("Programs"),
                          requires = [IS_IN_SET(selectable_projects,
                                                multiple = True,
                                                zero = None,
                                                ),
                                      IS_NOT_EMPTY(),
                                      ],
                          )
            field.tablename = "approve" # Dummy to make widget work
            projects_selector = S3GroupedOptionsWidget(cols=1)(field, projects)

            comments = custom_get("comments")

            if user.registration_key is None:
                response.warning = T("Registration has previously been Approved")
            elif user.registration_key == "rejected":
                response.warning = T("Registration has previously been Rejected")
            elif user.registration_key != "pending":
                response.warning = T("User hasn't verified their email")

            approve = INPUT(_value = T("Approve"),
                            _type = "submit",
                            _name = "approve-btn",
                            _id = "approve-btn",
                            _class = "small primary button",
                            )

            reject = INPUT(_value = T("Reject"),
                           _type = "submit",
                           _name = "reject-btn",
                           _id = "reject-btn",
                           _class = "small alert button",
                           )

            strrepr = lambda v: v if v else "-"
            form = FORM(TABLE(TR(approve,
                                 reject,
                                 ),
                              TR(TD("%s:" % T("Person")),
                                 TD(person),
                                 ),
                              test_station,
                              TR(TD("%s:" % T("Address")),
                                 TD(address),
                                 ),
                              TR(TD("%s:" % T("Telephone")),
                                 TD(strrepr(facility_phone)),
                                 ),
                              TR(TD("%s:" % T("Email")),
                                 TD(strrepr(facility_email)),
                                 ),
                              TR(TD("%s:" % T("Opening Hours")),
                                 TD(strrepr(opening_times)),
                                 ),
                              TR(TD("%s:" % T("Projects")),
                                 TD(projects_selector),
                                 ),
                              TR(TD("%s:" % T("Comments")),
                                 TD(s3_text_represent(strrepr(comments))),
                                 ),
                              )
                        )

            if form.accepts(request.post_vars, session, formname="approve"):

                form_vars = form.vars

                rejected = bool(form_vars.get("reject-btn"))
                approved = bool(form_vars.get("approve-btn")) and not rejected

                if approved:

                    set_record_owner = auth.s3_set_record_owner
                    s3db_onaccept = s3db.onaccept
                    update_super = s3db.update_super

                    if not organisation_id:
                        # Create Organisation
                        org = {"name": organisation}
                        org["id"] = organisation_id = otable.insert(**org)

                        # Post-process Organisation
                        update_super(otable, org)
                        set_record_owner(otable, org, owned_by_user=user_id)
                        s3db_onaccept(otable, org, method="create")

                        # Link to Org_Group TESTSTATIONS
                        s3db.org_group_membership.insert(group_id = org_group_id,
                                                         organisation_id = organisation_id,
                                                         )

                        # Link Organisation to selected projects
                        selected = form_vars.get("projects")
                        if isinstance(selected, (tuple, list)):
                            ltable = s3db.project_organisation
                            for item in selected:
                                try:
                                    project_id = int(item)
                                except (ValueError, TypeError):
                                    continue
                                link = {"project_id": project_id,
                                        "organisation_id": organisation_id,
                                        "role": 2,
                                        }
                                link["id"] = ltable.insert(**link)
                                set_record_owner(ltable, link)
                                s3db_onaccept(ltable, link, method="create")

                        # Add REQUESTER-tag ("No" by default)
                        ttable = s3db.org_organisation_tag
                        ttable.insert(organisation_id = organisation_id,
                                      tag = "REQUESTER",
                                      value = "N",
                                      )

                        # Update User
                        user.update_record(organisation_id = organisation_id,
                                           registration_key = None,
                                           )

                        # Grant ORG_ADMIN and PROVIDER_ACCOUNTANT
                        auth.s3_assign_role(user_id, "ORG_ADMIN", for_pe=org["pe_id"])
                        auth.s3_assign_role(user_id, "PROVIDER_ACCOUNTANT")
                    else:
                        # Update User
                        user.update_record(registration_key = None)

                    # Grant VOUCHER_PROVIDER
                    auth.s3_assign_role(user_id, "VOUCHER_PROVIDER")

                    location_id = location_get("id")
                    if not location_id:
                        # Create Location
                        ltable = s3db.gis_location
                        del location["wkt"] # Will get created during onaccept & we don't want the 'Source WKT has been cleaned by Shapely" warning
                        location["id"] = location_id = ltable.insert(**location)
                        set_record_owner(ltable, location, owned_by_user=user_id)
                        s3db_onaccept(ltable, location, method="create")

                    # Create Facility
                    ftable = s3db.org_facility
                    facility_name = organisation if organisation else org.name
                    facility = {"name": s3_truncate(facility_name),
                                "organisation_id": organisation_id,
                                "location_id": location_id,
                                "phone1": facility_phone,
                                "email": facility_email,
                                "opening_times": opening_times,
                                "comments": comments,
                                }
                    facility["id"] = ftable.insert(**facility)
                    update_super(ftable, facility)
                    set_record_owner(ftable, facility, owned_by_user=user_id)
                    s3db_onaccept(ftable, facility, method="create")

                    # Link to Facility Type
                    fttable = s3db.org_facility_type
                    facility_type = db(fttable.name == "Infection Test Station").select(fttable.id,
                                                                                        limitby = (0, 1),
                                                                                        ).first()
                    if facility_type:
                        s3db.org_site_facility_type.insert(site_id = facility["site_id"],
                                                           facility_type_id = facility_type.id,
                                                           )

                    # Approve user
                    auth.s3_approve_user(user)

                    # Send welcome email
                    settings = current.deployment_settings
                    from .notifications import CMSNotifications
                    error = CMSNotifications.send(user.email,
                                                  "WelcomeProvider",
                                                  {"name": organisation or org.name,
                                                   "homepage": settings.get_base_public_url(),
                                                   "profile": URL("default", "person", host=True),
                                                   },
                                                  module = "auth",
                                                  resource = "user",
                                                  )
                    if error:
                        session.warning = "%s: %s" % (T("Welcome Email NOT sent"), error)

                    session.confirmation = T("Registration approved")
                    redirect(URL(c = "default",
                                 f = "index",
                                 args = ["approve"],
                                 ))

                elif rejected:

                    user.update_record(registration_key = "rejected")
                    # @ToDo: Delete Org & Fac, if created previously
                    session.confirmation = T("Registration rejected")
                    redirect(URL(c = "default",
                                 f = "index",
                                 args = ["approve"],
                                 ))

            output = {"form": form,
                      "title": T("Approve Test Station"),
                      }

            # Custom View
            self._view("RLPPTM", "approve.html")

        else:
            # List View
            if ORG_ADMIN:
                # Filter to just their users
                gtable = db.auth_group
                mtable = db.auth_membership
                query = (mtable.user_id == auth.user.id) & \
                        (mtable.group_id == gtable.id) & \
                        (gtable.uuid == "ORG_ADMIN")
                memberships = db(query).select(mtable.pe_id)
                pe_id = [m.pe_id for m in memberships]
                otable = s3db.org_organisation
                orgs = db(otable.pe_id.belongs(pe_id)).select(otable.id)
                organisation_id = [org.id for org in orgs]
                accounts_filter = FS("organisation_id").belongs(organisation_id)
            else:
                # Filter to all for the ORG_GROUP
                accounts_filter = FS("org_group_id") == org_group_id
            # Only include pending accounts
            accounts_filter &= FS("registration_key") == "pending"

            resource = s3db.resource("auth_user", filter=accounts_filter)

            list_id = "datatable"

            # List fields
            list_fields = resource.list_fields()

            orderby = None

            s3 = response.s3
            representation = s3_get_extension(request) or \
                             S3Request.DEFAULT_REPRESENTATION

            # Pagination
            get_vars = request.get_vars
            if representation == "aadata":
                start, limit = S3CRUD._limits(get_vars)
            else:
                # Initial page request always uses defaults (otherwise
                # filtering and pagination would have to be relative to
                # the initial limits, but there is no use-case for that)
                start = None
                limit = None if s3.no_sspag else 0

            left = []
            distinct = False
            dtargs = {}

            if representation in S3Request.INTERACTIVE_FORMATS:

                # How many records per page?
                if s3.dataTable_pageLength:
                    display_length = s3.dataTable_pageLength
                else:
                    display_length = 25

                # Server-side pagination?
                if not s3.no_sspag:
                    dt_pagination = "true"
                    if not limit:
                        limit = 2 * display_length
                    session.s3.filter = get_vars
                    if orderby is None:
                        dt_sorting = {"iSortingCols": "1",
                                      "sSortDir_0": "asc"
                                      }

                        if len(list_fields) > 1:
                            dt_sorting["bSortable_0"] = "false"
                            dt_sorting["iSortCol_0"] = "1"
                        else:
                            dt_sorting["bSortable_0"] = "true"
                            dt_sorting["iSortCol_0"] = "0"

                        orderby, left = resource.datatable_filter(list_fields,
                                                                  dt_sorting,
                                                                  )[1:3]
                else:
                    dt_pagination = "false"

                # Disable exports
                s3.no_formats = True

                # Get the data table
                dt, totalrows = resource.datatable(fields = list_fields,
                                                   start = start,
                                                   limit = limit,
                                                   left = left,
                                                   orderby = orderby,
                                                   distinct = distinct,
                                                   )
                displayrows = totalrows

                # Always show table, otherwise it can't be Ajax-filtered
                # @todo: need a better algorithm to determine total_rows
                #        (which excludes URL filters), so that datatables
                #        shows the right empty-message (ZeroRecords instead
                #        of EmptyTable)
                dtargs["dt_pagination"] = dt_pagination
                dtargs["dt_pageLength"] = display_length
                dtargs["dt_base_url"] = URL(c="default", f="index", args="approve")
                dtargs["dt_permalink"] = URL(c="default", f="index", args="approve")
                datatable = dt.html(totalrows,
                                    displayrows,
                                    id = list_id,
                                    **dtargs)

                # Action Buttons
                s3.actions = [{"label": s3_str(T("Review")),
                               "url": URL(args = ["approve", "[id]"],
                                          ),
                               "_class": "action-btn",
                               },
                              ]

                output = {"items": datatable,
                          "title": T("Test Stations to be Approved"),
                          }

                # Custom View
                self._view(TEMPLATE, "approve_list.html")

            elif representation == "aadata":

                # Apply datatable filters
                searchq, orderby, left = resource.datatable_filter(list_fields,
                                                                   get_vars)
                if searchq is not None:
                    totalrows = resource.count()
                    resource.add_filter(searchq)
                else:
                    totalrows = None

                # Get a data table
                if totalrows != 0:
                    dt, displayrows = resource.datatable(fields = list_fields,
                                                         start = start,
                                                         limit = limit,
                                                         left = left,
                                                         orderby = orderby,
                                                         distinct = distinct,
                                                         )
                else:
                    dt, displayrows = None, 0
                if totalrows is None:
                    totalrows = displayrows

                # Echo
                draw = int(get_vars.get("draw", 0))

                # Representation
                if dt is not None:
                    output = dt.json(totalrows,
                                     displayrows,
                                     list_id,
                                     draw,
                                     **dtargs)
                else:
                    output = '{"recordsTotal":%s,' \
                             '"recordsFiltered":0,' \
                             '"dataTable_id":"%s",' \
                             '"draw":%s,' \
                             '"data":[]}' % (totalrows, list_id, draw)
            else:
                S3Request("auth", "user").error(415, current.ERROR.BAD_FORMAT)

        return output

# =============================================================================
class register(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth

        # Redirect if already logged-in
        if auth.s3_logged_in():
            redirect(URL(c="default", f="index"))

        auth_settings = auth.settings
        auth_messages = auth.messages
        self.customise_auth_messages()

        T = current.T
        db = current.db
        s3db = current.s3db

        request = current.request
        response = current.response
        session = current.session
        settings = current.deployment_settings

        utable = auth_settings.table_user

        # Page title and intro text
        title = T("Register Test Station")

        # Get intro text from CMS
        db = current.db
        s3db = current.s3db

        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                        (ltable.module == "auth") & \
                        (ltable.resource == "user") & \
                        (ltable.deleted == False))

        query = (ctable.name == "SelfRegistrationIntro") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                                join = join,
                                cache = s3db.cache,
                                limitby = (0, 1),
                                ).first()
        intro = row.body if row else None

        # Form Fields
        formfields, required_fields, subheadings = self.formfields()

        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields,
                                                mark_required = required_fields,
                                                )
        response.s3.has_required = has_required

        # Form buttons
        REGISTER = T("Register")
        buttons = [INPUT(_type = "submit",
                         _value = REGISTER,
                         ),
                   # TODO cancel-button?
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = utable._tablename,
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = REGISTER,
                               delete_label = auth_messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS & JS Validation
        form.add_class("auth_register")

        # Add Subheadings
        if subheadings:
            for pos, heading in subheadings[::-1]:
                form[0].insert(pos, DIV(heading, _class="subheading"))

        # Inject client-side Validation
        auth.s3_register_validation()

        # Set default registration key, so new users are prevented
        # from logging in until approved
        key = str(uuid4())
        code = uuid4().hex[-6:].upper()
        utable.registration_key.default = self.keyhash(key, code)

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = auth_settings.register_onvalidation,
                        ):

            formvars = form.vars

            organisation = formvars.get("organisation")

            # Check if organisation already exists
            organisation_id = self.lookup_organisation(formvars)
            if organisation_id:
                formvars["organisation_id"] = organisation_id

            # Create the user record
            user_id = utable.insert(**utable._filter_fields(formvars, id=False))
            formvars.id = user_id

            # Set org_group
            ogtable = s3db.org_group
            org_group = db(ogtable.name == TESTSTATIONS).select(ogtable.id,
                                                                limitby = (0, 1)
                                                                ).first()
            try:
                org_group_id = org_group.id
            except:
                raise RuntimeError("Cannot register user account as Org Group '%s' is missing " % TESTSTATIONS)
            db(utable.id == user_id).update(org_group_id = org_group_id)

            # Save temporary user fields in s3db.auth_user_temp
            temptable = s3db.auth_user_temp
            record  = {"user_id": user_id}

            record["consent"] = formvars.consent

            # Store Custom fields
            custom = {"location": formvars.location,
                      "facility_phone": formvars.facility_phone,
                      "facility_email": formvars.facility_email,
                      "opening_times": formvars.opening_times,
                      "projects": formvars.projects,
                      "comments": formvars.comments,
                      }
            if not organisation_id:
                custom["organisation"] = organisation
            record["custom"] = json.dumps(custom)

            temptable.insert(**record)

            # Post-process the new user record
            users = db(utable.id > 0).select(utable.id, limitby=(0, 2))
            if len(users) == 1:
                # 1st user to register doesn't need verification/approval
                auth.s3_approve_user(form.vars)
                session.confirmation = auth_messages.registration_successful

                # 1st user gets Admin rights
                admin_group_id = 1
                auth.add_membership(admin_group_id, users.first().id)

                # Log them in
                if "language" not in form.vars:
                    # Was missing from login form
                    form.vars.language = T.accepted_language
                user = Storage(utable._filter_fields(form.vars, id=True))
                auth.login_user(user)

                # Send welcome email
                auth.s3_send_welcome_email(form.vars)

                # Where to go next?
                register_next = request.vars._next or auth_settings.register_next

            else:
                # Request User Verify their Email
                # System Details for Verification Email
                verify_url = URL(c = "default",
                                 f = "index",
                                 args = ["verify_email", key],
                                 scheme = "https" if request.is_https else "http",
                                 )
                system = {"system_name": settings.get_system_name(),
                          "url": verify_url,
                          #"url": "%s/default/index/verify_email/%s" % (response.s3.base_url, key),
                          "code": code,
                          }

                # Try to send the Verification Email
                if not auth_settings.mailer or \
                   not auth_settings.mailer.settings.server or \
                   not auth_settings.mailer.send(to = form.vars.email,
                                                 subject = auth_messages.verify_email_subject % system,
                                                 message = auth_messages.verify_email % system,
                                                 ):
                    response.error = auth_messages.email_verification_failed

                    # Custom View
                    self._view(THEME, "register.html")

                    return {"title": title,
                            "form": form,
                            }

                # Redirect to Verification Info page
                register_next = URL(c = "default",
                                    f = "message",
                                    args = ["verify_email_sent"],
                                    vars = {"email": form.vars.email},
                                    )

            # Log action
            auth.log_event(auth_messages.register_log, form.vars)

            # Redirect
            redirect(register_next)

        elif form.errors:
            response.error = T("There are errors in the form, please check your input")

        # Custom View
        self._view(THEME, "register.html")

        return {"title": title,
                "intro": intro,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @classmethod
    def formfields(cls):
        """
            Generate the form fields for the registration form

            @returns: a tuple (formfields, required_fields, subheadings)
                      - formfields = list of form fields
                      - required_fields = list of field names of required fields
                      - subheadings = list of tuples (position, heading) to
                                      insert into the form
        """

        T = current.T
        request = current.request

        #db = current.db
        s3db = current.s3db

        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["SHARE", "RULES_PRO"])

        # Last name is required
        utable.last_name.requires = IS_NOT_EMPTY(error_message=T("input required"))

        #ltable = s3db.gis_location

        # Lookup projects with provider self-registration
        projects = cls.selectable_projects()

        # Form fields
        formfields = [utable.first_name,
                      utable.last_name,
                      utable.email,
                      utable[passfield],

                      # Password Verification Field
                      Field("password_two", "password",
                            label = auth_messages.verify_password,
                            requires = IS_EXPR("value==%s" % \
                                               repr(request.vars.get(passfield)),
                                               error_message = auth_messages.mismatched_password,
                                               ),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (auth_messages.verify_password,
                                                              T("Enter the same password again"),
                                                              ),
                                          ),
                            ),
                      # --------------------------------------------
                      Field("organisation",
                            label = T("Name"),
                            requires = [IS_NOT_EMPTY(), IS_LENGTH(60)],
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Test Station Name"),
                                                              T("Specify the name of the test station (max 60 characters)"),
                                                              ),
                                          ),
                            ),
                      Field("location", "json",
                            widget = S3LocationSelector(
                                        levels = ("L1", "L2", "L3", "L4"),
                                        required_levels = ("L1", "L2", "L3"),
                                        show_address = True,
                                        show_postcode = True,
                                        show_map = True,
                                        ),
                            ),
                      #Field("addr_street",
                      #      label = ltable.addr_street.label,
                      #      ),
                      #Field("addr_postcode",
                      #      label = ltable.addr_postcode.label,
                      #      requires = IS_NOT_EMPTY(),
                      #      ),

                      Field("facility_phone",
                            label = T("Telephone"),
                            requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                            ),
                      Field("facility_email",
                            label = T("Email"),
                            requires = IS_EMPTY_OR(IS_EMAIL()),
                            ),
                      Field("opening_times",
                            label = T("Opening Hours"),
                            #requires = IS_NOT_EMPTY(),
                            ),
                      Field("projects", "list:integer",
                            label = T("Programs"),
                            requires = [IS_IN_SET(projects,
                                                  multiple = True,
                                                  zero = None,
                                                  ),
                                        IS_NOT_EMPTY(),
                                        ],
                            widget = S3WithIntro(S3GroupedOptionsWidget(cols=1),
                                                 # Widget intro from CMS
                                                 intro = ("org",
                                                          "organisation",
                                                          "ProjectParticipationIntro",
                                                          ),
                                                 )
                            ),
                      Field("comments", "text",
                            label = T("Comments"),
                            widget = s3_comments_widget,
                            ),

                      # --------------------------------------------
                      Field("consent",
                           label = T("Consent"),
                           widget = consent.widget,
                           ),
                      ]

        # Required fields
        required_fields = ["first_name",
                           "last_name",
                           ]

        # Subheadings
        subheadings = ((0, T("User Account")),
                       (5, T("Test Station")),
                       (12, T("Privacy")),
                       )

        # Geocoder
        current.response.s3.scripts.append("/%s/static/themes/RLP/js/geocoderPlugin.js" % request.application)

        return formfields, required_fields, subheadings

    # -------------------------------------------------------------------------
    @staticmethod
    def keyhash(key, code):
        """
            Generate a hash of the activation code using
            the registration key

            @param key: the registration key
            @param code: the activation code

            @returns: the hash as string
        """

        crypt = CRYPT(key=key, digest_alg="sha512", salt=None)
        return str(crypt(code.upper())[0])

    # -------------------------------------------------------------------------
    @staticmethod
    def customise_auth_messages():
        """
            Customise auth messages:
            - verification email
            - welcome email
        """

        messages = current.auth.messages

        messages.verify_email_subject = "%(system_name)s - Verify Email"
        messages.verify_email = \
"""Click on the link %(url)s to verify your email.

Your Activation Code: %(code)s
"""

        messages.welcome_email_subject = "Welcome to the %(system_name)s Portal"
        messages.welcome_email = \
"""Welcome to the %(system_name)s Portal
 - To edit your profile go to: %(url)s%(profile)s

Thank you
"""

    # -------------------------------------------------------------------------
    @staticmethod
    def lookup_organisation(formvars):
        """
            Identify the organisation the user attempts to register for,
            by name, facility Lx and if necessary facility email address

            @param formvars: the FORM vars
            @returns: organisation_id if found, or None if this is a new
                      organisation
        """

        orgname = formvars.get("organisation")
        if not orgname:
            return None

        db = current.db
        s3db = current.s3db

        otable = s3db.org_organisation
        ftable = s3db.org_facility
        ltable = s3db.gis_location
        gtable = s3db.org_group
        mtable = s3db.org_group_membership

        # Search by name among test stations
        query = (otable.name == orgname) & \
                (otable.deleted == False)
        join = [mtable.on(mtable.organisation_id == otable.id),
                gtable.on((gtable.id == mtable.group_id) & \
                          (gtable.name == TESTSTATIONS)),
                ftable.on(ftable.organisation_id == otable.id),
                ]

        # Do we have a selected location (should have since mandatory)
        location = formvars.get("location")
        if isinstance(location, str):
            try:
                location = json.loads(location)
            except JSONERRORS:
                location = None

        if location:
            # Include the Lx ancestor in the lookup
            ancestor = None
            for level in ("L4", "L3", "L2"):
                ancestor = location.get(level)
                if ancestor:
                    break
            if ancestor:
                join.append(ltable.on(ltable.id == ftable.location_id))
                query &= ((ltable.level == None) & (ltable.parent == ancestor)) | \
                         (ltable.id == ancestor)

        rows = db(query).select(otable.id, join = join)
        organisation_id = None
        if len(rows) > 1:
            # Multiple matches => try using facility email to reduce
            facility_email = formvars.get("facility_email")
            if facility_email:
                candidates = {row.id for row in rows}
                query = (ftable.organisation_id.belongs(candidates)) & \
                        (ftable.email == facility_email) & \
                        (ftable.deleted == False)
                match = db(query).select(ftable.organisation_id,
                                         limitby = (0, 2),
                                         )
                if len(match) == 1:
                    organisation_id = match.first().organisation_id
        elif rows:
            # Single match - this organisation already exists
            organisation_id = rows.first().organisation_id

        return organisation_id

    # -------------------------------------------------------------------------
    @staticmethod
    def selectable_projects():
        """
            Projects the user can select during test station registration
            => all projects that are tagged with APPLY=Y

            @returns: list of project_ids
        """

        db = current.db
        s3db = current.s3db

        # Lookup projects with provider self-registration
        ptable = s3db.project_project
        ttable = s3db.project_project_tag
        join = ttable.on((ttable.project_id == ptable.id) & \
                         (ttable.tag == "APPLY") & \
                         (ttable.value == "Y") & \
                         (ttable.deleted == False))
        query = (ptable.deleted == False)
        rows = db(query).select(ptable.id,
                                ptable.name,
                                join = join,
                                )
        projects = {row.id: row.name for row in rows}
        return projects

# =============================================================================
class verify_email(S3CustomController):
    """ Custom verify_email Page """

    def __call__(self):

        T = current.T

        request = current.request
        response = current.response
        session = current.session

        settings = current.deployment_settings

        # Get the registration key
        if request.env.request_method == "POST":
            key = request.post_vars.registration_key
        elif len(request.args) > 1:
            key = request.args[-1]
        else:
            key = None
        if not key:
            session.error = T("Missing registration key")
            redirect(URL(c="default", f="index"))


        formfields = [Field("activation_code",
                            label = T("Please enter your Activation Code"),
                            requires = IS_NOT_EMPTY(),
                            ),
                      ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "auth_user",
                               record = None,
                               hidden = {"_next": request.vars._next,
                                         "registration_key": key,
                                         },
                               separator = ":",
                               showid = False,
                               submit_button = T("Submit"),
                               formstyle = settings.get_ui_formstyle(),
                               #buttons = buttons,
                               *formfields)

        if form.accepts(request.vars,
                        session,
                        formname = "register_confirm",
                        ):

            db = current.db
            s3db = current.s3db

            auth = current.auth
            auth_settings = auth.settings
            register.customise_auth_messages()

            # Get registration key from URL
            code = form.vars.activation_code

            # Find the pending user account
            utable = auth_settings.table_user
            query = (utable.registration_key == register.keyhash(key, code))
            user = db(query).select(limitby = (0, 1),
                                    ).first()
            if not user:
                session.error = T("Registration not found")
                redirect(auth_settings.verify_email_next)

            user_id = user.id
            db(utable.id == user_id).update(registration_key = "pending")
            auth.log_event(auth.messages.verify_email_log, user)

            # Lookup the Approver(s)
            gtable = db.auth_group
            mtable = db.auth_membership
            pe_id = None

            # Is this an existing Org?
            organisation_id = user.organisation_id
            if organisation_id:
                role_required = "ORG_ADMIN"

                # Get org_name and pe_id from organisation
                otable = s3db.org_organisation
                row = db(otable.id == organisation_id).select(otable.name,
                                                              otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
                if row:
                    org_name = row.name
                    pe_id = row.pe_id

                subject = """%(system_name)s - New User Approval Pending"""
                message = """Your action is required to approve a New User for %(org_name)s:
%(user_name)s
Please go to %(url)s to approve this user."""

            if not pe_id:
                role_required = "ORG_GROUP_ADMIN"

                subject = """%(system_name)s - New Test Station Approval Pending"""
                message = """Your action is required to approve a New Test Station for %(system_name)s:
%(org_name)s
Please go to %(url)s to approve this station."""

                # Get org_name from auth_user_temp
                ttable= s3db.auth_user_temp
                temp = db(ttable.user_id == user_id).select(ttable.custom,
                                                            limitby = (0, 1)
                                                            ).first()
                try:
                    custom = json.loads(temp.custom)
                except JSONERRORS:
                    custom = {}
                org_name = custom.get("organisation")

                # Get pe_id of TESTSTATIONS group
                ogtable = s3db.org_group
                query = (ogtable.name == TESTSTATIONS) & \
                        (ogtable.deleted == False)
                row = db(query).select(ogtable.pe_id, limitby=(0, 1)).first()
                if row:
                    pe_id = row.pe_id

            query = (mtable.pe_id == 0)
            if pe_id:
                query |= (mtable.pe_id == pe_id)
            join = [mtable.on((mtable.user_id == utable.id) & \
                              (mtable.deleted == False)),
                    gtable.on((gtable.id == mtable.group_id) & \
                              (gtable.uuid == role_required)),
                    ]
            approvers = db(query).select(utable.email,
                                         utable.language,
                                         join = join,
                                         )

            # Ensure that we send out the mails in the language that the approver(s) want
            languages = {}
            for approver in approvers:
                language = approver.language
                if language not in languages:
                    languages[language] = [approver.email]
                else:
                    languages[language].append(approver.email)

            subjects = {}
            messages = {}
            system_name = settings.get_system_name()

            base_url = response.s3.base_url
            url = "%s/default/index/approve/%s" % (base_url, user_id)

            for language in languages:
                subjects[language] = s3_str(T(subject, language=language) %
                                            {"system_name": system_name,
                                             })
                messages[language] = s3_str(T(message, language=language) %
                                            {"org_name": org_name,
                                             "system_name": system_name,
                                             "user_name": user.email,
                                             "url": url,
                                             })

            result = None
            mailer = auth_settings.mailer
            if mailer.settings.server:
                send_email = mailer.send
                for approver in approvers:
                    language = approver["language"]
                    result = send_email(to = approver["email"],
                                        subject = subjects[language],
                                        message = messages[language]
                                        )

            session = current.session
            if result:
                session.confirmation = settings.get_auth_registration_pending_approval()
            else:
                # Don't prevent registration just because email not configured
                #db.rollback()
                session.error = auth.messages.email_send_failed

            redirect(URL(c="default", f="index"))

        self._view(THEME, "register.html")

        return {"title": T("Confirm Registration"),
                "form": form,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def send_welcome_email(user):
        """
            Send a welcome email to the new user

            @param user: the auth_user Row
        """

        register.customise_auth_messages()
        auth_messages = current.auth.messages

        try:
            recipient = user["email"]
        except (KeyError, TypeError):
            recipient = None
        if not recipient:
            current.response.error = auth_messages.unable_send_email
            return

        # Look up CMS template for welcome email
        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings

        # Define join
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "auth") & \
                         (ltable.resource == "user") & \
                         (ltable.deleted == False))

        # Get message template
        query = (ctable.name == "WelcomeMessage") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.doc_id,
                               ctable.body,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            message_template = row.body
        else:
            # Disabled
            return

        # Look up attachments
        dtable = s3db.doc_document
        query = (dtable.doc_id == row.doc_id) & \
                (dtable.file != None) & (dtable.file != "") & \
                (dtable.deleted == False)
        rows = db(query).select(dtable.file)
        attachments = []
        for row in rows:
            filename, stream = dtable.file.retrieve(row.file)
            attachments.append(current.mail.Attachment(stream, filename=filename))

        # Default subject from auth.messages
        system_name = s3_str(settings.get_system_name())
        subject = s3_str(auth_messages.welcome_email_subject % \
                         {"system_name": system_name})

        # Custom message body
        data = {"system_name": system_name,
                "url": settings.get_base_public_url(),
                "profile": URL("default", "person", host=True),
                }
        message = formatmap(message_template, data)

        # Send email
        success = current.msg.send_email(to = recipient,
                                         subject = subject,
                                         message = message,
                                         attachments = attachments,
                                         )
        if not success:
            current.response.error = auth_messages.unable_send_email

# =============================================================================
class register_invited(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth

        # Redirect if already logged-in
        if auth.s3_logged_in():
            redirect(URL(c="default", f="index"))

        T = current.T

        settings = current.deployment_settings

        request = current.request
        response = current.response
        session = current.session

        # Get the registration key
        if len(request.args) > 1:
            key = request.args[-1]
            session.s3.invite_key = key
            redirect(URL(c="default", f="index", args = ["register_invited"]))
        else:
            key = session.s3.invite_key
        if not key:
            session.error = T("Missing registration key")
            redirect(URL(c="default", f="index"))

        # Page title and intro text
        title = T("Registration")

        # Get intro text from CMS
        db = current.db
        s3db = current.s3db

        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                        (ltable.module == "auth") & \
                        (ltable.resource == "user") & \
                        (ltable.deleted == False))

        query = (ctable.name == "InvitedRegistrationIntro") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                                join = join,
                                cache = s3db.cache,
                                limitby = (0, 1),
                                ).first()
        intro = row.body if row else None

        # Customise Auth Messages
        auth_settings = auth.settings
        auth_messages = auth.messages
        self.customise_auth_messages()

        # Form Fields
        formfields, required_fields = self.formfields()

        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields,
                                                mark_required = required_fields,
                                                )
        response.s3.has_required = has_required

        # Form buttons
        REGISTER = T("Register")
        buttons = [INPUT(_type = "submit",
                         _value = REGISTER,
                         ),
                   # TODO cancel-button?
                   ]

        # Construct the form
        utable = auth_settings.table_user
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = utable._tablename,
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = REGISTER,
                               delete_label = auth_messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS & JS Validation
        form.add_class("auth_register")

        # Inject client-side Validation
        auth.s3_register_validation()

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = self.validate(key),
                        ):

            form_vars = form.vars

            # Get the account
            account = self.account(key, form_vars.code)
            account.update_record(**utable._filter_fields(form_vars, id=False))

            del session.s3["invite_key"]

            # Post-process the new user record
            s3db.configure("auth_user",
                           register_onaccept = self.register_onaccept,
                           )

            # Store consent response (for approve_user to register it)
            consent = form_vars.consent
            if consent:
                ttable = s3db.auth_user_temp
                record  = {"user_id": account.id,
                           "consent": form_vars.consent
                           }
                ttable.insert(**record)

            # Approve and link user
            auth.s3_approve_user(account)

            # Send welcome email (custom)
            self.send_welcome_email(account)

            # Log them in
            user = Storage(utable._filter_fields(account, id=True))
            auth.login_user(user)

            auth_messages = auth.messages
            auth.log_event(auth_messages.register_log, user)
            session.flash = auth_messages.registration_successful

            # TODO redirect to the org instead?
            redirect(URL(c="default", f="person"))

        elif form.errors:
            response.error = T("There are errors in the form, please check your input")

        # Custom View
        self._view(TEMPLATE, "register_invited.html")

        return {"title": title,
                "intro": intro,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @classmethod
    def validate(cls, key):
        """
            Custom validation of registration form
            - check the registration code
            - check for duplicate email
        """

        T = current.T

        def register_onvalidation(form):

            code = form.vars.get("code")

            account = cls.account(key, code)
            if not account:
                form.errors["code"] = T("Invalid Registration Code")
                return

            email = form.vars.get("email")

            from gluon.validators import ValidationError
            auth = current.auth
            utable = auth.settings.table_user
            dbset = current.db(utable.id != account.id)
            requires = IS_NOT_IN_DB(dbset, "%s.email" % utable._tablename)
            try:
                requires.validate(email)
            except ValidationError:
                form.errors["email"] = auth.messages.duplicate_email
                return

            onvalidation = current.auth.settings.register_onvalidation
            if onvalidation:
                from gluon.tools import callback
                callback(onvalidation, form, tablename="auth_user")

        return register_onvalidation

    # -------------------------------------------------------------------------
    @staticmethod
    def register_onaccept(user_id):
        """
            Process Registration

            @param user_id: the user ID
        """

        auth = current.auth
        assign_role = auth.s3_assign_role

        assign_role(user_id, "ORG_ADMIN")
        assign_role(user_id, "VOUCHER_ISSUER")

    # -------------------------------------------------------------------------
    @classmethod
    def send_welcome_email(cls, user):
        """
            Send a welcome email to the new user

            @param user: the auth_user Row
        """

        cls.customise_auth_messages()
        auth_messages = current.auth.messages

        # Look up CMS template for welcome email
        try:
            recipient = user["email"]
        except (KeyError, TypeError):
            recipient = None
        if not recipient:
            current.response.error = auth_messages.unable_send_email
            return


        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings

        # Define join
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "auth") & \
                         (ltable.resource == "user") & \
                         (ltable.deleted == False))

        # Get message template
        query = (ctable.name == "WelcomeMessageInvited") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.doc_id,
                               ctable.body,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            message_template = row.body
        else:
            # Disabled
            return

        # Look up attachments
        dtable = s3db.doc_document
        query = (dtable.doc_id == row.doc_id) & \
                (dtable.file != None) & (dtable.file != "") & \
                (dtable.deleted == False)
        rows = db(query).select(dtable.file)
        attachments = []
        for row in rows:
            filename, stream = dtable.file.retrieve(row.file)
            attachments.append(current.mail.Attachment(stream, filename=filename))

        # Default subject from auth.messages
        system_name = s3_str(settings.get_system_name())
        subject = s3_str(auth_messages.welcome_email_subject % \
                         {"system_name": system_name})

        # Custom message body
        data = {"system_name": system_name,
                "url": settings.get_base_public_url(),
                "profile": URL("default", "person", host=True),
                }
        message = formatmap(message_template, data)

        # Send email
        success = current.msg.send_email(to = recipient,
                                         subject = subject,
                                         message = message,
                                         attachments = attachments,
                                         )
        if not success:
            current.response.error = auth_messages.unable_send_email

    # -------------------------------------------------------------------------
    @classmethod
    def account(cls, key, code):
        """
            Find the account matching registration key and code

            @param key: the registration key (from URL args)
            @param code: the registration code (from form)
        """

        if key and code:
            utable = current.auth.settings.table_user
            query = (utable.registration_key == cls.keyhash(key, code))
            account = current.db(query).select(utable.ALL, limitby=(0, 1)).first()
        else:
            account = None

        return account

    # -------------------------------------------------------------------------
    @staticmethod
    def formfields():
        """
            Generate the form fields for the registration form

            @returns: a tuple (formfields, required_fields)
                      - formfields = list of form fields
                      - required_fields = list of field names of required fields
        """

        T = current.T
        request = current.request

        s3db = current.s3db
        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Last name is required
        utable.last_name.requires = IS_NOT_EMPTY(error_message=T("input required"))

        # Don't check for duplicate email (will be done in onvalidation)
        # => user might choose to use the current email address of the account
        # => if registration key or code are invalid, we don't want to give away
        #    any existing email addresses
        utable.email.requires = [IS_EMAIL(error_message = auth_messages.invalid_email),
                                 IS_LOWER(),
                                 ]

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["STORE", "RULES_ISS"])

        # Form fields
        formfields = [utable.first_name,
                      utable.last_name,
                      utable.email,
                      utable[passfield],
                      Field("password_two", "password",
                            label = auth_messages.verify_password,
                            requires = IS_EXPR("value==%s" % \
                                               repr(request.vars.get(passfield)),
                                               error_message = auth_messages.mismatched_password,
                                               ),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (auth_messages.verify_password,
                                                              T("Enter the same password again"),
                                                              ),
                                          ),
                            ),
                      Field("code",
                            label = T("Registration Code"),
                            requires = IS_NOT_EMPTY(),
                            ),
                      Field("consent",
                            label = T("Consent"),
                            widget = consent.widget,
                            ),
                      ]


        # Required fields
        required_fields = ["first_name",
                           "last_name",
                           ]

        return formfields, required_fields

    # -------------------------------------------------------------------------
    @staticmethod
    def keyhash(key, code):
        """
            Generate a hash of the activation code using
            the registration key

            @param key: the registration key
            @param code: the activation code

            @returns: the hash as string
        """

        crypt = CRYPT(key=key, digest_alg="sha512", salt=None)
        return str(crypt(code.upper())[0])

    # -------------------------------------------------------------------------
    @staticmethod
    def customise_auth_messages():
        """
            Customise auth messages:
            - welcome email subject
        """

        messages = current.auth.messages

        messages.welcome_email_subject = "Welcome to the %(system_name)s Portal"

# =============================================================================
class geocode(S3CustomController):
    """
        Custom Geocoder
        - looks up Lat/Lon from Postcode &/or Address
        - looks up Lx from Lat/Lon
    """

    def __call__(self):

        vars_get = current.request.post_vars.get

        # Validate the formkey
        formkey = vars_get("k")
        keyname = "_formkey[geocode]"
        if not formkey or formkey not in current.session.get(keyname, []):
            status = 403
            message = current.ERROR.NOT_PERMITTED
            headers = {"Content-Type": "application/json"}
            current.log.error(message)
            raise HTTP(status,
                       body = current.xml.json_message(success = False,
                                                       statuscode = status,
                                                       message = message),
                       web2py_error = message,
                       **headers)

        gis = current.gis

        postcode = vars_get("postcode")
        address = vars_get("address")
        if address:
            full_address = "%s %s" %(postcode, address)
        else:
            full_address = postcode

        latlon = gis.geocode(full_address)
        if not isinstance(latlon, dict):
            output = "{}"
        else:
            lat = latlon["lat"]
            lon = latlon["lon"]
            results = gis.geocode_r(lat, lon)

            results["lat"] = lat
            results["lon"] = lon

            from s3.s3xml import SEPARATORS
            output = json.dumps(results, separators=SEPARATORS)

        current.response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class ocert(S3CustomController):
    """
        Custom controller to certify the eligibility of an organisation
        to perform certain actions in an external application

        Process similar to OAuth:
            - external app presents the user with a link to Sahana
              containing a purpose key and a session token, e.g.
              /default/index/ocert?p=XY&t=0123456789ABCDEF
            - user follows the link, and is asked by Sahana to login
            - once logged-in, Sahana verifies that the user is OrgAdmin
              for an organisation that qualifies for the specified purpose,
              and if it does, redirects the user back to a URL in the
              external app, with a verification hash as URL parameter
            - the external app requests the OrgID from the user, and
              generates a hash of the session token with that ID, and
              if both hashes match, access to the intended function is
              granted
    """

    def __call__(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth

        session = current.session

        # Handle purpose key and token in URL
        get_vars = current.request.get_vars
        purpose = get_vars.get("p")
        token = get_vars.get("t")
        if purpose or token:
            if not purpose or not token:
                self._error("Invalid Request - Missing Parameter")
            session.s3.ocert_key = {"p": purpose, "t": token}
            redirect(URL(args=["ocert"], vars={}))

        # Check that function is configured
        purposes = current.deployment_settings.get_custom(key="ocert")
        if not isinstance(purposes, dict):
            self._error("Function not available")

        # Read key from session, extract purpose and token
        key = session.s3.get("ocert_key")
        try:
            purpose, token = key.get("p"), key.get("t")
        except (TypeError, AttributeError):
            self._error("Invalid Request - Missing Parameter")

        # Verify purpose key
        redirect_uri = purposes.get(purpose)
        if not redirect_uri:
            self._error("Invalid Parameter")

        # Validate token
        # - must be a 64 to 256 bit hex-encoded number
        token_value = None
        if 16 <= len(token) <= 64:
            try:
                token_value = int(token, 16)
            except (TypeError, ValueError):
                pass
        if not token_value:
            self._error("Invalid Parameter")

        # Determine the organisation to check
        organisation_id = None
        if auth.s3_logged_in():

            # Must be ORG_ADMIN
            if not auth.s3_has_role("ORG_ADMIN"):
                self._error("Insufficient Permissions")

            # Must manage at least one organisation
            managed_orgs = None

            user = auth.user
            sr = auth.get_system_roles()
            realms = user.realms[sr.ORG_ADMIN]
            if not realms:
                realms = s3db.pr_realm(user.pe_id)
            if realms:
                # Look up managed organisations
                otable = s3db.org_organisation
                query = (otable.pe_id.belongs(realms)) & \
                        (otable.deleted == False)
                managed_orgs = db(query).select(otable.id,
                                                otable.name,
                                                )
            if not managed_orgs:
                self._error("No Managed Organizations")
            elif len(managed_orgs) == 1:
                # Only one managed org
                organisation_id = managed_orgs.first().id
            else:
                # Let user select the organisation
                form = self._org_select(managed_orgs)
                if form.accepts(current.request.vars,
                                session,
                                formname = "org_select",
                                ):
                    organisation_id = form.vars.organisation_id
                else:
                    self._view(THEME, "register.html")
                    output = {"title": current.T("Select Organization"),
                              "intro": None,
                              "form": form,
                              }
        else:
            # Go to login, then return here
            redirect(URL(c = "default",
                         f = "user",
                         args = ["login"],
                         vars = {"_next": URL(args=["ocert"], vars={})},
                         ))

        if organisation_id:
            # Remove ocert key from session
            del session.s3.ocert_key

            # Generate verification hash
            vhash = self._vhash(organisation_id,
                                purpose = purpose,
                                token = token,
                                )
            if vhash:
                from s3compat import urllib_quote
                url = redirect_uri % {"token": urllib_quote(token),
                                      "vhash": urllib_quote(vhash),
                                      }
                redirect(url)
            else:
                # Organisation is not authorized for the purpose
                self._error("Organization not authorized")

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def _vhash(organisation_id, purpose=None, token=None):
        """
            Verify the qualification of the organisation for the purpose,
            and generate a verification hash (=encrypt the token with the
            organisation's OrgID tag) if successful

            @param organisation_id: the organisation_id
            @param purpose: the purpose key
            @param token: the token

            @returns: the encrypted token
        """

        if not token:
            return None

        db = current.db
        s3db = current.s3db

        # Look up the organisation ID tag
        ttable = s3db.org_organisation_tag
        query = (ttable.organisation_id == organisation_id) & \
                (ttable.tag == "OrgID") & \
                (ttable.deleted == False)
        orgid = db(query).select(ttable.value,
                                 limitby = (0, 1),
                                 ).first()
        if not orgid or not orgid.value:
            return None

        if purpose == "KVREG":

            # Must be a TESTSTATIONS organisation
            gtable = s3db.org_group
            mtable = s3db.org_group_membership
            query = (mtable.organisation_id == organisation_id) & \
                    (mtable.deleted == False) & \
                    (gtable.id == mtable.group_id) & \
                    (gtable.name == TESTSTATIONS)
            row = db(query).select(mtable.id, limitby=(0, 1)).first()
            if not row:
                return None

            # Must be partner in the TESTS-PUBLIC project
            ptable = s3db.project_project
            ltable = s3db.project_organisation
            query = (ltable.organisation_id == organisation_id) & \
                    (ltable.deleted == False) & \
                    (ptable.id == ltable.project_id) & \
                    (ptable.code == "TESTS-PUBLIC")
            row = db(query).select(ltable.id, limitby=(0, 1)).first()
            if not row:
                return None

        # Generate vhash
        crypt = CRYPT(key = orgid.value,
                      digest_alg = "sha512",
                      salt = False,
                      )
        return str(crypt(token)[0])

    # -------------------------------------------------------------------------
    @staticmethod
    def _org_select(organisations):
        """
            Render a form for the user to select one of their managed
            organisations

            @param organisations: the managed organisations, Rows {id, name}

            @returns: a FORM
        """

        T = current.T

        response = current.response
        settings = current.deployment_settings

        options = {row.id: row.name for row in organisations}

        formfields = [Field("organisation_id",
                            label = T("Organization"),
                            requires = IS_IN_SET(options),
                            ),
                      ]

        # Generate labels (and mark required fields in the process)
        labels = s3_mark_required(formfields)[0]
        response.s3.has_required = False

        # Form buttons
        SUBMIT = T("Continue")
        buttons = [INPUT(_type = "submit",
                         _value = SUBMIT,
                         ),
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "organisation",
                               record = None,
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = SUBMIT,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        return form

    # -------------------------------------------------------------------------
    @staticmethod
    def _error(message):
        """
            Redirect to home page with error message

            @param message: the error message
        """

        current.session.error = current.T(message)
        redirect(URL(c="default", f="index"))

# END =========================================================================
