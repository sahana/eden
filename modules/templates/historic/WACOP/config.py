# -*- coding: utf-8 -*-

from collections import OrderedDict
import json

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template for WA-COP + CAD Cloud Integration
    """

    T = current.T

    # =========================================================================
    # System Settings
    #
    settings.base.system_name_short = T("Sahana")

    # Prepop default
    settings.base.prepopulate += ("WACOP",)
    settings.base.prepopulate_demo += ("WACOP/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "WACOP"

    settings.ui.social_buttons = True

    # -------------------------------------------------------------------------
    # Self-Registration and User Profile
    #
    # Users can self-register
    settings.security.self_registration = False
    # Users need to verify their email
    settings.auth.registration_requires_verification = True
    # Users need to be approved
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_organisation_required = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    settings.auth.registration_link_user_to = {"staff": T("Staff")}
    settings.auth.registration_link_user_to_default = ["staff"]
    settings.auth.registration_roles = {"organisation_id": ["USER"],
                                        }

    settings.auth.show_link = False

    # -------------------------------------------------------------------------
    # Security Policy
    #
    settings.security.policy = 7 # Apply Controller, Function and Table ACLs
    settings.security.map = True

    # -------------------------------------------------------------------------
    # Audit
    #
    def audit_write(method, tablename, form, record, representation):
        if tablename in ("event_incident",
                         "pr_group",
                         ):
            # Track the Source Repository for Incidents / Resources
            return True
        else:
            # Don't Audit
            return False

    settings.security.audit_write = audit_write

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    #
    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("es", "Spanish"),
    ])
    # Default Language
    settings.L10n.default_language = "en"
    # Default timezone for users
    settings.L10n.timezone = "US/Pacific"
    # Unsortable 'pretty' date format
    settings.L10n.date_format = "%b %d %Y"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 1
    # Enable this to change the label for 'Mobile Phone'
    settings.ui.label_mobile_phone = "Cell Phone"
    # Enable this to change the label for 'Postcode'
    settings.ui.label_postcode = "ZIP Code"

    settings.msg.require_international_phone_numbers = False
    # PDF default size Letter
    settings.base.pdf_size = "Letter"

    # Uncomment this to Translate CMS Series Names
    # - we want this on when running s3translate but off in normal usage as we use the English names to lookup icons in render_posts
    #settings.L10n.translate_cms_series = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True

    # Has scalability issues, but should be OK with our number of records
    settings.search.dates_auto_range = True

    # -------------------------------------------------------------------------
    # GIS settings
    #
    # Restrict the Location Selector to just certain countries
    settings.gis.countries = ("US",)
    # Levels for the LocationSelector
    #levels = ("L1", "L2", "L3")

    # Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
    #settings.gis.geocode_imported_addresses = "google"

    # Until we add support to S3LocationSelector to set dropdowns from LatLons
    settings.gis.check_within_parent_boundaries = False
    # GeoNames username
    settings.gis.geonames_username = "mcop"
    # Uncomment to hide Layer Properties tool
    #settings.gis.layer_properties = False
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to prevent showing LatLon in Location Represents
    settings.gis.location_represent_address_only = "icon"
    # Resources which can be directly added to the main map
    settings.gis.poi_create_resources = None

    # -------------------------------------------------------------------------
    # UI Settings
    #
    settings.ui.datatables_pagingType = "bootstrap"
    settings.ui.update_label = "Edit"

    # -------------------------------------------------------------------------
    # Modules
    #
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = "Home",
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = "Administration",
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = "Administration",
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        #("errors", Storage(
        #    name_nice = "Ticket Viewer",
        #    #description = "Needed for Breadcrumbs",
        #    restricted = False,
        #    module_type = None  # No Menu
        #)),
        ("sync", Storage(
           name_nice = "Synchronization",
           #description = "Synchronization",
           restricted = True,
           access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
           module_type = None  # This item is handled separately for the menu
        )),
        #("translate", Storage(
        #    name_nice = "Translation Functionality",
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = "Map",
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 1,     # 1st item in the menu
        )),
        ("pr", Storage(
            name_nice = "Persons",
            description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = None
        )),
        ("org", Storage(
            name_nice = "Organizations",
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 10
        )),
        # All modules below here should be possible to disable safely
        ("msg", Storage(
            name_nice = "Messaging",
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("hrm", Storage(
            name_nice = "Contacts",
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
        )),
        ("cms", Storage(
                name_nice = "Content Management",
                restricted = True,
                module_type = 10,
            )),
        ("event", Storage(
                name_nice = "Events",
                restricted = True,
                module_type = 2,
            )),
        ("fire", Storage(
                name_nice = "Fire",
                restricted = True,
                module_type = None,
            )),
        ("police", Storage(
                name_nice = "Police",
                restricted = True,
                module_type = None,
            )),
        ("project", Storage(
                name_nice = "Tasks",
                restricted = True,
                module_type = None,
            )),
        ("doc", Storage(
            name_nice = "Documents",
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = None,
        )),
        ("stats", Storage(
            name_nice = "Statistics",
            restricted = True,
            module_type = None
        )),
    ])

    # -------------------------------------------------------------------------
    # CMS Content Management
    #
    settings.cms.bookmarks = True
    settings.cms.richtext = True
    settings.cms.show_tags = True

    # -------------------------------------------------------------------------
    def cms_post_onaccept(form):
        """
            Handle Tags in Create / Update forms
            Auto-Bookmark Updates created from the Dashboard
            Update the forum modified_on when created from the Forum
        """

        post_id = form.vars.id

        db = current.db
        s3db = current.s3db
        request = current.request

        if request.get_vars.get("dashboard"):
            # Bookmark the post
            s3db.cms_post_user.insert(post_id = post_id,
                                      user_id = current.auth.user.id,
                                      )
        elif request.function == "forum":
            # Update modified_on to ensure that the Update is visible to subscribers
            db(s3db.pr_forum.id == request.args[0]).update(modified_on = request.utcnow)

        # Process Tags
        ttable = s3db.cms_tag
        ltable = s3db.cms_tag_post

        # Delete all existing tags for this post
        db(ltable.post_id == post_id).delete()

        # Add tags found in form
        tags = request.post_vars.get("tags")
        if not tags:
            return

        tags = tags.split(",")
        tag_ids = db(ttable.name.belongs(tags)).select(ttable.id,
                                                       ttable.name).as_dict(key="name")
        for tag in tags:
            row = tag_ids.get("tag")
            if row:
                tag_id = row.get("id")
            else:
                tag_id = ttable.insert(name=tag)
            ltable.insert(post_id = post_id,
                          tag_id = tag_id,
                          )

    # -------------------------------------------------------------------------
    def customise_cms_post_resource(r, tablename):

        db = current.db
        s3db = current.s3db
        table = s3db.cms_post
        table.priority.readable = table.priority.writable = True
        table.series_id.readable = table.series_id.writable = True
        table.status_id.readable = table.status_id.writable = True

        method = r.method
        if method in ("create", "update"):
            if r.get_vars.get("page") == "SYSTEM_WIDE":
                # System-wide Alert
                from s3 import S3SQLCustomForm
                crud_form = S3SQLCustomForm("body",
                                            )
                r.resource.configure(crud_form = crud_form)
                # No sidebar menu
                current.menu.options = None
                return

            # Custom Form
            from s3 import S3SQLCustomForm, S3SQLInlineComponent

            s3db.cms_post_team.group_id.widget = None

            crud_fields = [S3SQLInlineComponent("post_team",
                                                fields = [("", "group_id")],
                                                label = T("Resource"),
                                                multiple = False,
                                                ),
                           (T("Type"), "series_id"),
                           (T("Priority"), "priority"),
                           (T("Status"), "status_id"),
                           (T("Title"), "title"),
                           (T("Text"), "body"),
                           (T("Location"), "location_id"),
                           # Tags are added client-side
                           S3SQLInlineComponent("document",
                                                name = "file",
                                                label = T("Files"),
                                                fields = [("", "file"),
                                                          #"comments",
                                                          ],
                                                ),
                           ]

            if r.tablename != "event_incident":
                if r.tablename == "event_event":
                    from gluon import IS_EMPTY_OR
                    from s3 import IS_ONE_OF
                    itable = s3db.event_incident
                    query = (itable.event_id == r.id) & \
                            (itable.closed == False) & \
                            (itable.deleted == False)
                    the_set = db(query)
                    f = s3db.event_post.incident_id
                    f.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(the_set, "event_incident.id",
                                              f.represent,
                                              orderby="event_incident.name",
                                              sort=True))
                crud_fields.insert(0, S3SQLInlineComponent("incident_post",
                                                           fields = [("", "incident_id")],
                                                           label = T("Incident"),
                                                           multiple = False,
                                                           ))

            crud_form = S3SQLCustomForm(*crud_fields
                                        )

            # Client support for Tags
            appname = r.application
            s3 = current.response.s3
            scripts_append = s3.scripts.append
            if s3.debug:
                scripts_append("/%s/static/scripts/tag-it.js" % appname)
            else:
                scripts_append("/%s/static/scripts/tag-it.min.js" % appname)
            scripts_append("/%s/static/themes/WACOP/js/update_tags.js" % appname)
            if method == "create":
                s3.jquery_ready.append('''wacop_update_tags("")''')
            elif method == "update":
                ttable = s3db.cms_tag
                ltable = s3db.cms_tag_post
                if r.tablename == "cms_post":
                    post_id = r.id
                else:
                    post_id = r.component.id
                query = (ltable.post_id == post_id) & \
                        (ltable.tag_id == ttable.id)
                tags = db(query).select(ttable.name)
                tags = [tag.name for tag in tags]
                tags = ",".join(tags)
                s3.jquery_ready.append('''wacop_update_tags("%s")''' % tags)

            def create_onaccept(form):
                """
                    Update the modified_on of any forums to which the Incident/Event this Post links to is Shared
                """
                post_id = form.vars.id
                pltable = s3db.event_post
                events = db(pltable.post_id == post_id).select(pltable.event_id,
                                                               pltable.incident_id,
                                                               )
                if len(events):
                    event_ids = []
                    eappend = event_ids.append
                    incident_ids = []
                    iappend = incident_ids.append
                    for e in events:
                        incident_id = e.incident_id
                        if incident_id:
                            iappend(incident_id)
                        else:
                            eappend(e.event_id)

                    fltable = s3db.event_forum
                    if len(event_ids):
                        query = (fltable.event_id.belongs(event_ids))
                        if len(incident_ids):
                            query |= (fltable.incident_id.belongs(incident_ids))
                    else:
                        query = (fltable.incident_id.belongs(incident_ids))
                    forums = db(query).select(fltable.forum_id)
                    len_forums = len(forums)
                    if len_forums:
                        ftable = s3db.pr_forum
                        if len_forums == 1:
                            query = (ftable.id == forums.first().forum_id)
                        else:
                            query = (ftable.id.belongs([f.forum_id for f in forums]))
                        db(query).update(modified_on = r.utcnow)

            default = s3db.get_config(tablename, "onaccept")
            if isinstance(default, list):
                onaccept = default
                # Processing Tags/auto-Bookmarks
                onaccept.append(cms_post_onaccept)
                create_onaccept = list(onaccept) + [create_onaccept]
            else:
                # Processing Tags/auto-Bookmarks
                onaccept = [default, cms_post_onaccept]
                create_onaccept = [create_onaccept, default, cms_post_onaccept]

            s3db.configure(tablename,
                           crud_form = crud_form,
                           onaccept = onaccept,
                           create_onaccept = create_onaccept,
                           )

        elif method in ("custom", "dashboard", "datalist", "filter"):
            # dataList configuration
            from s3 import s3_fieldmethod
            from templates.WACOP.controllers import cms_post_list_layout

            s3 = current.response.s3
            s3.dl_no_header = True

            # Virtual Field for Comments
            # - otherwise need to do per-record DB calls inside cms_post_list_layout
            #   as direct list_fields come in unsorted, so can't match up to records
            ctable = s3db.cms_comment

            def comment_as_json(row):
                body = row["cms_comment.body"]
                if not body:
                    return None
                return json.dumps({"body": body,
                                   "created_by": row["cms_comment.created_by"],
                                   "created_on": row["cms_comment.created_on"].isoformat(),
                                   })

            ctable.json_dump = s3_fieldmethod("json_dump",
                                              comment_as_json,
                                              # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                              #represent = lambda v: v,
                                              )

            s3db.configure("cms_comment",
                           extra_fields = ["body",
                                           "created_by",
                                           "created_on",
                                           ],
                           # Doesn't seem to have any impact
                           #orderby = "cms_comment.created_on asc",
                           )

            s3db.configure(tablename,
                           # No create form in the datalist popups on Resource Browse page
                           insertable = False,
                           list_fields = ["series_id",
                                          "priority",
                                          "status_id",
                                          "date",
                                          "title",
                                          "body",
                                          "created_by",
                                          "tag.name",
                                          "document.file",
                                          #"comment.id",
                                          "comment.json_dump",
                                          ],
                           list_layout = cms_post_list_layout,
                           # First is Default, 2nd has no impact
                           #orderby = ("cms_post.date desc",
                           #           "cms_comment.created_on asc",
                           #           )
                           )

            get_vars = r.get_vars
            if method == "datalist":
                if get_vars.get("dashboard"):
                    from templates.WACOP.controllers import dashboard_filter
                    # Too late for s3.filter to take effect
                    #s3.filter = dashboard_filter()
                    r.resource.add_filter(dashboard_filter())
                else:
                    forum_id = get_vars.get("forum")
                    if forum_id:
                        from templates.WACOP.controllers import group_filter
                        # Too late for s3.filter to take effect
                        #s3.filter = group_filter(forum_id)
                        r.resource.add_filter(group_filter(forum_id))

            elif method in ("custom", "dashboard", "filter"):
                # Filter Widgets
                from s3 import S3DateFilter, \
                               S3LocationFilter, \
                               S3OptionsFilter, \
                               S3TextFilter

                if method == "filter":
                    # Apply filter_vars
                    for k, v in get_vars.items():
                        # We only expect a maximum of 1 of these, no need to append
                        if k == "dashboard":
                            from templates.WACOP.controllers import dashboard_filter
                            # Too late for s3.filter to take effect
                            #s3.filter = dashboard_filter()
                            r.resource.add_filter(dashboard_filter())
                        elif k == "forum":
                            from templates.WACOP.controllers import group_filter
                            # Too late for s3.filter to take effect
                            #s3.filter = group_filter(v)
                            r.resource.add_filter(group_filter(v))
                        else:
                            from s3 import FS
                            # Too late for s3.filter to take effect
                            #s3.filter = (FS(k) == v)
                            r.resource.add_filter((FS(k) == v))

                date_filter = S3DateFilter("date",
                                           # If we introduce an end_date on Posts:
                                           #["date", "end_date"],
                                           label = "",
                                           #hide_time = True,
                                           slider = True,
                                           clear_text = "X",
                                           )
                date_filter.input_labels = {"ge": "Start Time/Date", "le": "End Time/Date"}

                from templates.WACOP.controllers import text_filter_formstyle

                filter_widgets = [S3TextFilter(["body",
                                                ],
                                               formstyle = text_filter_formstyle,
                                               label = T("Search"),
                                               _placeholder = T("Enter search term…"),
                                               ),
                                  S3OptionsFilter("series_id",
                                                  label = "",
                                                  noneSelectedText = "Type", # T() added in widget
                                                  no_opts = "",
                                                  ),
                                  S3OptionsFilter("priority",
                                                  label = "",
                                                  noneSelectedText = "Priority", # T() added in widget
                                                  no_opts = "",
                                                  ),
                                  S3OptionsFilter("status_id",
                                                  label = "",
                                                  noneSelectedText = "Status", # T() added in widget
                                                  no_opts = "",
                                                  ),
                                  S3OptionsFilter("created_by$organisation_id",
                                                  label = "",
                                                  noneSelectedText = "Source", # T() added in widget
                                                  no_opts = "",
                                                  ),
                                  S3OptionsFilter("tag_post.tag_id",
                                                  label = "",
                                                  noneSelectedText = "Tag", # T() added in widget
                                                  no_opts = "",
                                                  ),
                                  date_filter,
                                  ]

                if r.tablename == "event_event" or \
                   (method == "filter" and get_vars.get("event_post.event_id")):
                    # Event Profile
                    filter_widgets.insert(1, S3OptionsFilter("incident_post.incident_id",
                                                             label = "",
                                                             noneSelectedText = "Incident", # T() added in widget
                                                             no_opts = "",
                                                             ))

                elif r.tablename == "pr_forum" or \
                   (method == "filter" and get_vars.get("forum")):
                    # Group Profile
                    if r.tablename == "pr_forum":
                        forum_id = r.id
                    else:
                        forum_id = get_vars.get("forum")
                    appname = r.application
                    eftable = s3db.event_forum
                    base_query = (eftable.forum_id == forum_id)
                    etable = s3db.event_event
                    query = base_query & (eftable.event_id == etable.id)
                    events_shared = db(query).select(etable.id,
                                                     etable.name,
                                                     )
                    shared_events = {}
                    for e in events_shared:
                        shared_events[e.id] = e.name
                    event_comment = "<a class='drop' data-options='ignore_repositioning:true;align:right' data-dropdown='event_drop{v}' aria-controls='event_drop{v}' aria-expanded='false'>…</a><ul id='event_drop{v}' class='f-dropdown' data-dropdown-content='' aria-hidden='true' tabindex='-1'><li><a href='/%(app)s/event/event/{v}/custom'>Go to Event</a></li><li><a href='/%(app)s/event/event/{v}/unshare/%(forum_id)s' class='ajax_link'>Stop sharing</a></li><li><a href='#'>Stop notifications</a></li></ul>" % \
                        dict(app = appname,
                             forum_id = forum_id,
                             )
                    filter_widgets.append(S3OptionsFilter("event_post.event_id",
                                                          label = T("Shared Events"),
                                                          cols = 1,
                                                          options = shared_events,
                                                          no_opts = "",
                                                          table = False,
                                                          option_comment = event_comment,
                                                          ))
                    itable = s3db.event_incident
                    query = base_query & (eftable.incident_id == itable.id)
                    incidents_shared = db(query).select(itable.id,
                                                        itable.name,
                                                        )
                    shared_incidents = {}
                    for i in incidents_shared:
                        shared_incidents[i.id] = i.name
                    incident_comment = "<a class='drop' data-options='ignore_repositioning:true;align:right' data-dropdown='incident_drop{v}' aria-controls='incident_drop{v}' aria-expanded='false'>…</a><ul id='incident_drop{v}' class='f-dropdown' data-dropdown-content='' aria-hidden='true' tabindex='-1'><li><a href='/%(app)s/event/incident/{v}/custom'>Go to Incident</a></li><li><a href='/%(app)s/event/incident/{v}/unshare/%(forum_id)s' class='ajax_link'>Stop sharing</a></li><li><a href='#'>Stop notifications</a></li></ul>" % \
                        dict(app = appname,
                             forum_id = forum_id,
                             )
                    filter_widgets.append(S3OptionsFilter("incident_post.incident_id",
                                                          label = T("Shared Incidents"),
                                                          cols = 1,
                                                          options = shared_incidents,
                                                          no_opts = "",
                                                          table = False,
                                                          option_comment = incident_comment,
                                                          ))

                if method != "dashboard":
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

                s3db.configure(tablename,
                               filter_widgets = filter_widgets,
                               )

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -------------------------------------------------------------------------
    # Event/Incident Management
    #
    settings.event.incident_teams_tab = "Units"
    # Uncomment to preserve linked Incidents when an Event is deleted
    settings.event.cascade_delete_incidents = False

    # -------------------------------------------------------------------------
    def customise_event_event_resource(r, tablename):

        from gluon import A, URL
        from s3 import s3_fieldmethod

        db = current.db
        s3db = current.s3db

        # Virtual Fields
        etable = s3db.event_event
        #append = etable._virtual_methods.append

        def event_name(row):
            return A(row["event_event.name"],
                     _href = URL(c="event", f="event",
                                 args=[row["event_event.id"], "custom"],
                                 extension = "", # ensure no .aadata
                                 ),
                     )
        #append(Field.Method("name_click", event_name))
        etable.name_click = s3_fieldmethod("name_click",
                                           event_name,
                                           # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                           represent = lambda v: v,
                                           search_field = "name",
                                           )

        def event_status(row):
            if row["event_event.exercise"]:
                status = T("Testing")
            elif not row["event_event.end_date"]:
                status = T("Open")
            else:
                status = T("Closed")
            return status
        #append(Field.Method("status", event_status))
        etable.status = s3_fieldmethod("status", event_status)

        itable = s3db.event_incident
        def event_incidents(row):
            query = (itable.event_id == row["event_event.id"]) & \
                    (itable.deleted == False)
            incidents = db(query).count()
            return incidents
        #append(Field.Method("incidents", event_incidents))
        etable.incidents = s3_fieldmethod("incidents", event_incidents)

        ertable = s3db.event_team
        def event_resources(row):
            query = (ertable.event_id == row["event_event.id"]) & \
                    (ertable.deleted == False)
            resources = db(query).count()
            return resources
        #append(Field.Method("resources", event_resources))
        etable.resources = s3_fieldmethod("resources", event_resources)

        ettable = s3db.event_tag
        ttable = s3db.cms_tag
        def event_tags(row):
            query = (ettable.event_id == row["event_event.id"]) & \
                    (ettable.deleted == False) & \
                    (ettable.tag_id == ttable.id)
            tags = db(query).select(ttable.name)
            if tags:
                tags = [t.name for t in tags]
                tags = ", ".join(tags)
                return tags
            else:
                return current.messages["NONE"]
        #append(Field.Method("tags", event_tags))
        etable.tags = s3_fieldmethod("tags", event_tags)

        list_fields = [(T("Name"), "name_click"),
                       (T("Status"), "status"),
                       (T("Zero Hour"), "start_date"),
                       (T("Closed"), "end_date"),
                       (T("City"), "location.L3"),
                       (T("State"), "location.L1"),
                       (T("Tags"), "tags"),
                       (T("Incidents"), "incidents"),
                       (T("Resources"), "resources"),
                       ]

        report_fields = ["name",
                         #"event_type_id",
                         "status",
                         (T("City"), "location.L3"),
                         (T("State"), "location.L1"),
                         ]

        s3db.configure(tablename,
                       extra_fields = ("name",
                                       "end_date",
                                       "exercise",
                                       ),
                       list_fields = list_fields,
                       report_options = Storage(
                        rows=report_fields,
                        cols=report_fields,
                        fact=report_fields,
                        defaults=Storage(rows = "status",
                                         #cols = "event_type_id",
                                         cols = "location.L3",
                                         fact = "count(name)",
                                         totals = True)
                        ),
                       orderby = "event_event.name",
                       )

    settings.customise_event_event_resource = customise_event_event_resource

    # -------------------------------------------------------------------------
    def customise_event_event_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Modify Components
        s3db.add_components("event_event",
                            # Events have just a single Location
                            event_event_location = {"joinby": "event_id",
                                                    "multiple": False,
                                                    },
                            # Incidents are linked to Events, not created from them
                            # - not a link table though, so can't change the actuation
                            #event_incident = {"joinby": "event_id",
                            #                  },
                            )

        # Custom Browse
        from templates.WACOP.controllers import event_Browse, event_Profile
        set_method = s3db.set_method
        set_method("event", "event",
                   method = "browse",
                   action = event_Browse)

        # Custom Profile
        set_method("event", "event",
                   method = "custom",
                   action = event_Profile)

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            cname = r.component_name
            if not cname:
                f = s3db.event_event.event_type_id
                f.readable = f.writable = False

            elif r.representation == "popup" and r.get_vars.get("view"):
                # Popups for lists in Parent Event of Incident Screen or Event Profile header
                # No Title since this is on the Popup
                s3.crud_strings["event_event"].title_display = ""
                # No create button & Tweak list_fields
                if cname == "incident":
                    list_fields = ["date",
                                   "name",
                                   "incident_type_id",
                                   ]
                elif cname == "group":
                    list_fields = ["incident_id",
                                   "group_id",
                                   "status_id",
                                   ]

                    if r.component_id:
                        f = s3db.event_team.group_id
                        f.writable = False
                        f.comment = None

                    s3db.configure("event_team",
                                   update_next = r.url(),
                                   )

                elif cname == "post":
                    list_fields = ["date",
                                   "series_id",
                                   "priority",
                                   "status_id",
                                   "body",
                                   ]
                else:
                    # Shouldn't get here but want to avoid crashes
                    list_fields = []
                r.component.configure(insertable = False,
                                      list_fields = list_fields,
                                      )

            return True
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and isinstance(output, dict):
                if r.method == "assign":
                    # No Top Menu
                    current.menu.main = ""
                    # Ensure we don't hide the Bulk Actions column in CSS
                    s3.jquery_ready.append('''$('body').addClass('assign')''')
                    # Custom View to waste less space inside popup
                    import os
                    response.view = os.path.join(r.folder,
                                                 "modules", "templates",
                                                 "WACOP", "views",
                                                 "assign.html")

                elif r.component_name == "group":
                    output["title"] = T("Resource Details")

                #elif r.component_name == "post":
                #    # Add Tags - no, do client-side
                #    output["form"].append()

                #else:
                #    # Summary or Profile pages
                #    # Additional styles
                #    s3.external_stylesheets += ["https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css",
                #                                "https://fonts.googleapis.com/css?family=Merriweather:400,700|Source+Sans+Pro:400,700",
                #                                ]

                    #if r.method == "summary":
                    #    # Open the Custom profile page instead of the normal one
                    #    from gluon import URL
                    #    from s3 import s3_action_buttons
                    #    custom_url = URL(args = ["[id]", "custom"])
                    #    s3_action_buttons(r,
                    #                      read_url=custom_url,
                    #                      update_url=custom_url)

            return output
        s3.postp = custom_postp

        # Custom rheader tabs
        attr = dict(attr)
        attr["rheader"] = wacop_rheader

        # No sidebar menu
        current.menu.options = None

        refresh = current.request.get_vars.get("refresh")
        if refresh:
            # Popup from Resource Browse
            current.menu.main = ""

            #from gluon import A, URL
            #attr["custom_crud_buttons"] = {"list_btn": A(T("Browse Resources"),
            #                                             _class="action-btn",
            #                                             _href=URL(c="pr", f="group", args="browse"),
            #                                             _id="list-btn",
            #                                             )
            #                               }
            attr["custom_crud_buttons"] = {"list_btn": "",
                                           }

            response = current.response
            if response.confirmation:
                script = '''self.parent.$('#%s').dataTable().fnReloadAjax()''' % refresh
                response.s3.jquery_ready.append(script)

        return attr

    settings.customise_event_event_controller = customise_event_event_controller

    # -------------------------------------------------------------------------
    def customise_event_incident_resource(r, tablename):

        from gluon import A, URL
        from s3 import s3_fieldmethod

        s3db = current.s3db

        # Virtual Fields
        itable = s3db.event_incident
        #append = itable._virtual_methods.append

        def incident_name(row):
            return A(row["event_incident.name"],
                     _href = URL(c="event", f="incident",
                                 args=[row["event_incident.id"], "custom"],
                                 extension = "", # ensure no .aadata
                                 ),
                     )
        #append(Field.Method("name_click", incident_name))
        itable.name_click = s3_fieldmethod("name_click",
                                           incident_name,
                                           # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                           represent = lambda v: v,
                                           search_field = "name",
                                           )

        def incident_status(row):
            if row["event_incident.exercise"]:
                status = T("Testing")
            elif not row["event_incident.end_date"]:
                status = T("Open")
            else:
                status = T("Closed")
            return status
        #append(Field.Method("status", incident_status))
        itable.status = s3_fieldmethod("status", incident_status)

        if r.method == "browse" or r.get_vars.get("browse"):
            # Incident Browse
            db = current.db
            ertable = s3db.event_team
            def incident_resources(row):
                query = (ertable.incident_id == row["event_incident.id"]) & \
                        (ertable.deleted == False)
                resources = db(query).count()
                return resources
            #append(Field.Method("resources", incident_resources))
            itable.resources = s3_fieldmethod("resources", incident_resources)

            ettable = s3db.event_tag
            ttable = s3db.cms_tag
            def incident_tags(row):
                query = (ettable.incident_id == row["event_incident.id"]) & \
                        (ettable.deleted == False) & \
                        (ettable.tag_id == ttable.id)
                tags = db(query).select(ttable.name)
                if tags:
                    tags = [t.name for t in tags]
                    tags = ", ".join(tags)
                    return tags
                else:
                    return current.messages["NONE"]
            #append(Field.Method("tags", incident_tags))
            itable.tags = s3_fieldmethod("tags", incident_tags)

            atable = db.s3_audit
            stable = s3db.sync_repository
            def incident_source(row):
                query = (atable.record_id == row["event_incident.id"]) & \
                        (atable.tablename == "event_incident") & \
                        (atable.repository_id == stable.id)
                repo = db(query).select(stable.name,
                                        limitby=(0, 1)
                                        ).first()
                if repo:
                    return repo.name
                else:
                    return T("Internal")
            #append(Field.Method("source", incident_source))
            itable.source = s3_fieldmethod("source", incident_source)

            list_fields = [(T("Name"), "name_click"),
                           (T("Status"), "status"),
                           (T("Type"), "incident_type_id"),
                           (T("Zero Hour"), "date"),
                           (T("Closed"), "end_date"),
                           #(T("City"), "location.location_id.L3"),
                           #(T("State"), "location.location_id.L1"),
                           (T("City"), "location_id$L3"),
                           (T("State"), "location_id$L1"),
                           (T("Tags"), "tags"),
                           (T("Resources"), "resources"),
                           (T("Event"), "event_id"),
                           ]
        else:
            # Homepage or Event Profile
            list_fields = [(T("Name"), "name_click"),
                           (T("Status"), "status"),
                           (T("Type"), "incident_type_id"),
                           "location_id",
                           (T("Start"), "date"),
                           ]

        report_fields = ["name",
                         "incident_type_id",
                         "status",
                         (T("City"), "location_id$L3"),
                         "source",
                         "group.organisation_team.organisation_id",
                         ]

        s3db.configure(tablename,
                       extra_fields = ("name",
                                       "end_date",
                                       "exercise",
                                       ),
                       list_fields = list_fields,
                       report_options = Storage(
                        rows=report_fields,
                        cols=report_fields,
                        fact=report_fields,
                        defaults=Storage(rows = "status",
                                         cols = "incident_type_id",
                                         fact = "count(name)",
                                         totals = True)
                        ),
                       orderby = "event_incident.name",
                       popup_url = URL(c="event", f="incident",
                                       args=["[id]", "custom"],
                                       ),
                       )

    settings.customise_event_incident_resource = customise_event_incident_resource

    # -------------------------------------------------------------------------
    def customise_event_incident_controller(**attr):

        s3db = current.s3db
        response = current.response
        s3 = response.s3

        # Load normal model to be able to override configuration
        table = s3db.event_incident

        table.event_id.readable = table.event_id.writable = True

        # Custom Browse
        from templates.WACOP.controllers import incident_Browse, incident_Profile
        set_method = s3db.set_method
        set_method("event", "incident",
                   method = "browse",
                   action = incident_Browse)

        # Custom Profile
        set_method("event", "incident",
                   method = "custom",
                   action = incident_Profile)

        #s3.crud_strings["event_incident"].title_list =  T("Browse Incidents")

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            if r.component_name == "group":
                if r.component_id:
                    f = s3db.event_team.group_id
                    f.writable = False
                    f.comment = None
                s3db.configure("event_team",
                               update_next = r.url(),
                               )

            elif r.representation == "popup":
                if not r.component:
                    if r.get_vars.get("set_event"):
                        # Popup just used to link to Event
                        #s3.crud_strings["event_incident"].title_update =  T("Add to Event")
                        from s3 import S3SQLCustomForm
                        crud_form = S3SQLCustomForm("event_id",
                                                    )
                        s3db.configure("event_incident",
                                       crud_form = crud_form,
                                       )
                #elif r.component_name == "post":
                #    from s3 import S3SQLCustomForm

                #    crud_form = S3SQLCustomForm("body",
                #                                )

                #    s3db.configure("cms_post",
                #                   crud_form = crud_form,
                #                   )

            return True
        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and isinstance(output, dict):
                if r.method == "assign":
                    # No Top Menu
                    current.menu.main = ""
                    # Ensure we don't hide the Bulk Actions column in CSS
                    s3.jquery_ready.append('''$('body').addClass('assign')''')
                    # Custom View to waste less space inside popup
                    import os
                    response.view = os.path.join(r.folder,
                                                 "modules", "templates",
                                                 "WACOP", "views",
                                                 "assign.html")

                elif r.component_name == "group":
                    output["title"] = T("Resource Details")

                #elif r.component_name == "post":
                #    # Add Tags - no, do client-side
                #    output["form"].append()

                #else:
                #    # Summary or Profile pages
                #    # Additional styles
                #    s3.external_stylesheets += ["https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css",
                #                                "https://fonts.googleapis.com/css?family=Merriweather:400,700|Source+Sans+Pro:400,700",
                #                                ]

                    #if r.method == "summary":
                    #    # Open the Custom profile page instead of the normal one
                    #    from gluon import URL
                    #    from s3 import s3_action_buttons
                    #    custom_url = URL(args = ["[id]", "custom"])
                    #    s3_action_buttons(r,
                    #                      read_url=custom_url,
                    #                      update_url=custom_url)

            return output
        s3.postp = custom_postp

        # Custom rheader tabs
        #attr = dict(attr)
        attr["rheader"] = wacop_rheader

        # No sidebar menu
        current.menu.options = None

        refresh = current.request.get_vars.get("refresh")
        if refresh:
            # Popup from Resource Browse
            current.menu.main = ""

            #from gluon import A, URL
            #attr["custom_crud_buttons"] = {"list_btn": A(T("Browse Resources"),
            #                                             _class="action-btn",
            #                                             _href=URL(c="pr", f="group", args="browse"),
            #                                             _id="list-btn",
            #                                             )
            #                               }
            attr["custom_crud_buttons"] = {"list_btn": "",
                                           }

            response = current.response
            if response.confirmation:
                script = '''self.parent.$('#%s').dataTable().fnReloadAjax()''' % refresh
                response.s3.jquery_ready.append(script)

        return attr

    settings.customise_event_incident_controller = customise_event_incident_controller

    # -------------------------------------------------------------------------
    def customise_event_human_resource_resource(r, tablename):

        from gluon import A, URL
        from s3 import s3_fieldmethod, s3_fullname

        s3db = current.s3db

        # Virtual Fields
        # Always used from either the Event or Incident context
        f = r.function
        record_id = r.id
        ehrtable = s3db.event_human_resource
        def person_name(row):
            person_id = row["event_human_resource.person_id"]
            return A(s3_fullname(person_id),
                     _href = URL(c="event", f=f,
                                 args = [record_id, "person", person_id, "profile"],
                                 extension = "", # ensure no .aadata
                                 ),
                     )
        ehrtable.name_click = s3_fieldmethod("name_click",
                                             person_name,
                                             # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                             # @ToDo: Bulk lookups
                                             represent = lambda v: v,
                                             search_field = "person_id",
                                             )

        s3db.configure(tablename,
                       #crud_form = crud_form,
                       delete_next = URL(c="event", f=f,
                                         args = [record_id, "custom"],
                                         ),
                       extra_fields = ("person_id",
                                       ),
                       list_fields = [(T("Name"), "name_click"),
                                      (T("Title"), "person_id$human_resource_id.job_title_id"),
                                      "person_id$human_resource.organisation_id",
                                      (T("Email"), "person_id$email.value"),
                                      (T("Phone"), "person_id$phone.value"),
                                      #"status",
                                      (T("Notes"), "comments"),
                                      ],
                       orderby = "event_human_resource.person_id",
                       )

    settings.customise_event_human_resource_resource = customise_event_human_resource_resource

    # -------------------------------------------------------------------------
    def customise_event_organisation_resource(r, tablename):

        from gluon import A, URL
        from s3 import s3_fieldmethod

        s3db = current.s3db

        # Virtual Fields
        # Always used from either the Event or Incident context
        f = r.function
        record_id = r.id
        eotable = s3db.event_organisation
        org_represent = eotable.organisation_id.represent
        def org_name(row):
            organisation_id = row["event_organisation.organisation_id"]
            return A(org_represent(organisation_id),
                     _href = URL(c="event", f=f,
                                 args=[record_id, "organisation", organisation_id, "profile"],
                                 ),
                     )
        eotable.name_click = s3_fieldmethod("name_click",
                                            org_name,
                                            # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                            # @ToDo: Bulk lookups
                                            represent = lambda v: v,
                                            search_field = "organisation_id",
                                            )

        s3db.configure(tablename,
                       #crud_form = crud_form,
                       delete_next = URL(c="event", f=f,
                                         args = [record_id, "custom"],
                                         ),
                       extra_fields = ("organisation_id",
                                       ),
                       list_fields = [(T("Name"), "name_click"),
                                      "status",
                                      "comments",
                                      ],
                       orderby = "event_organisation.organisation_id",
                       )

    settings.customise_event_organisation_resource = customise_event_organisation_resource

    # -------------------------------------------------------------------------
    def customise_event_team_resource(r, tablename):

        from gluon import A, URL
        from s3 import s3_fieldmethod, S3SQLCustomForm
        from s3layouts import S3PopupLink

        T = current.T
        s3db = current.s3db
        ertable = s3db.event_team

        ertable.group_id.label = T("Resource")
        ertable.group_id.comment = S3PopupLink(c = "pr",
                                               f = "group",
                                               label = T("Create Resource"),
                                               title = T("Create Resource"),
                                               tooltip = T("Create a new Resource"),
                                               )

        # Form
        # @ToDo: Have both Team & Event_Team in 1 form
        crud_form = S3SQLCustomForm("incident_id",
                                    "group_id",
                                    "status_id",
                                    )

        # Virtual Fields
        # @ToDo: Replace with a link to Popup a dataTable of the List of Updates
        incident_id = r.get_vars.get("~.incident_id")
        if incident_id:
            f = "incident"
            record_id = incident_id
        else:
            event_id = r.get_vars.get("~.event_id")
            if event_id:
                f = "event"
                record_id = event_id
            else:
                f = r.function
                record_id = r.id
        group_represent = ertable.group_id.represent
        if f in ("group", "team"):
            # Resource Browse (inc aadata)
            def team_name(row):
                group_id = row["event_team.group_id"]
                return A(group_represent(group_id),
                         _href = URL(c="event", f="incident",
                                     args = [row["event_team.incident_id"], "group", group_id, "read"],
                                     vars = {"refresh": "custom-list-event_team",
                                             },
                                     extension = "", # ensure no .aadata
                                     ),
                         _class = "s3_modal",
                         )
        else:
            # Event Profile or Incident Profile
            def team_name(row):
                group_id = row["event_team.group_id"]
                return A(group_represent(group_id),
                         _href = URL(c="event", f=f,
                                     args = [record_id, "group", group_id, "read"],
                                     vars = {"refresh": "custom-list-event_team",
                                             },
                                     extension = "", # ensure no .aadata
                                     ),
                         _class = "s3_modal",
                         )
        ertable.name_click = s3_fieldmethod("name_click",
                                            team_name,
                                            # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                            # @ToDo: Bulk lookups
                                            represent = lambda v: v,
                                            search_field = "group_id",
                                            )

        if f in ("group", "team"):
            # Resource Browse (inc aadata)
            list_fields = [(T("Resource"), "name_click"),
                           "incident_id",
                           "status_id",
                           ]
        elif f == "incident":
            # Incident Profile
            list_fields = [(T("Name"), "name_click"),
                           "status_id",
                           ]
        else:
            # Event Profile
            list_fields = [(T("Name"), "name_click"),
                           "incident_id",
                           "status_id",
                           ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       extra_fields = ("group_id",
                                       ),
                       list_fields = list_fields,
                       orderby = "pr_group.name",
                       )

    settings.customise_event_team_resource = customise_event_team_resource

    # -----------------------------------------------------------------------------
    def pr_forum_notify_subject(resource, data, meta_data):
        """
            Custom Method to subject for the email
            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param meta_data: the meta data for the notification
        """

        subject = "[%s] %s %s" % (settings.get_system_name_short(),
                                  data["rows"][0]["pr_forum.name"],
                                  T("Notification"),
                                  )
        # RFC 2822
        #return s3_str(s3_truncate(subject, length=78))
        # Truncate happens in s3notify.py
        return subject

    # -----------------------------------------------------------------------------
    def pr_forum_notify_renderer(resource, data, meta_data, format=None):
        """
            Custom Method to pre-render the contents for the message template

            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param meta_data: the meta data for the notification
            @param format: the contents format ("text" or "html")
        """

        from gluon import DIV, H1, P

        # We should always have just a single row
        row = data["rows"][0]
        notification = DIV(H1(T(row["pr_forum.name"])))
        append = notification.append
        # Updates
        updates = row["cms_post.json_dump"]
        if updates:
            updates = "[%s]" % updates
            updates = json.loads(updates)
            for update in updates:
                #update["date"]
                #update["series_id"]
                #update["priority"]
                #update["status_id"]
                append(P(update["body"]))
        # Events
        events = row["event_event.json_dump"]
        if events:
            events = "[%s]" % events
            events = json.loads(events)
            for event in events:
                #event["date"]
                append(P(event["name"]))
        # Incidents
        incidents = row["event_incident.json_dump"]
        if incidents:
            incidents = "[%s]" % incidents
            incidents = json.loads(incidents)
            for incident in incidents:
                #incident["date"]
                append(P(incident["name"]))
        # Tasks
        tasks = row["project_task.json_dump"]
        if tasks:
            tasks = "[%s]" % tasks
            tasks= json.loads(tasks)
            for task in tasks:
                #task["date"]
                append(P(task["name"]))

        return {"notification": notification}

    # -------------------------------------------------------------------------
    def customise_pr_forum_resource(r, tablename):

        f = current.s3db.pr_forum.comments
        f.label = T("Description")
        f.comment = None

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Group"),
            title_display = T("Group Details"),
            title_list = T("Groups"),
            title_update = T("Edit Group"),
            label_list_button = T("List Groups"),
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently registered"))

    settings.customise_pr_forum_resource = customise_pr_forum_resource

    # -------------------------------------------------------------------------
    def customise_pr_forum_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        # Custom Browse
        from templates.WACOP.controllers import group_Browse, group_Notify, group_Profile, text_filter_formstyle
        set_method = s3db.set_method
        set_method("pr", "forum",
                   method = "browse",
                   action = group_Browse)

        # Custom Profile
        set_method("pr", "forum",
                   method = "custom",
                   action = group_Profile)

        # Custom Notifications
        set_method("pr", "forum",
                   method = "notify_settings",
                   action = group_Notify)

        from s3 import S3OptionsFilter, S3SQLCustomForm, S3SQLInlineComponent, S3TextFilter

        crud_form = S3SQLCustomForm("name",
                                    "forum_type",
                                    "comments",
                                    S3SQLInlineComponent("forum_membership",
                                         fields = [("", "person_id")],
                                         label = T("Admin"),
                                         #multiple = False,
                                         filterby = dict(field = "admin",
                                                         options = True,
                                                         )
                                         ),
                                    )

        filter_widgets = [S3TextFilter(["name",
                                        "description",
                                        ],
                                       formstyle = text_filter_formstyle,
                                       label = T("Search"),
                                       _placeholder = T("Enter search term…"),
                                       _class = "filter-search",
                                       ),
                          S3OptionsFilter("forum_membership.person_id$pe_id",
                                          label = "",
                                          options = {"*": T("All Groups"),
                                                     current.auth.user.pe_id: T("My Groups"),
                                                     },
                                          cols = 2,
                                          multiple = False,
                                          table = False,
                                          ),
                          ]

        # Virtual Fields
        from gluon import A, URL
        from s3 import s3_fieldmethod
        table = s3db.pr_forum

        def forum_name(row):
            return A(row["pr_forum.name"],
                     _href = URL(c="pr", f="forum",
                                 args = [row["pr_forum.id"], "custom"],
                                 #vars = {"refresh": "custom-list-pr_forum",
                                 #        },
                                 extension = "", # ensure no .aadata
                                 ),
                     #_class = "s3_modal",
                     )
        table.name_click = s3_fieldmethod("name_click",
                                          forum_name,
                                          # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                          # @ToDo: Bulk lookups
                                          represent = lambda v: v,
                                          search_field = "name",
                                          )

        mtable = s3db.pr_forum_membership
        ffield = mtable.forum_id
        query = (mtable.deleted == False)
        def forum_members(row):
            forum_id = row["pr_forum.id"]
            count = db(query & (ffield == forum_id)).count()
            return count
        table.members = s3_fieldmethod("members",
                                       forum_members,
                                       )

        pfield = mtable.person_id
        aquery = query & (mtable.admin == True)
        NONE = current.messages["NONE"]
        personRepresent = pfield.represent
        def admin(row):
            forum_id = row["pr_forum.id"]
            admins = db(aquery & (ffield == forum_id)).select(pfield)
            if admins:
                return ", ".join([personRepresent(a.person_id) for a in admins])
            else:
                return NONE
        table.admin = s3_fieldmethod("admin",
                                     admin,
                                     )

        list_fields = [(T("Name"), "name_click"),
                       "comments",
                       (T("Members"), "members"),
                       (T("Updated"), "modified_on"),
                       (T("Admin"), "admin"),
                       ]

        s3db.configure("pr_forum",
                       crud_form = crud_form,
                       extra_fields = ("name",
                                       ),
                       list_fields = list_fields,
                       filter_widgets = filter_widgets,
                       )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            if r.representation == "msg":
                # Notifications

                # Add Virtual Fields for Components
                # - to keep their data together

                ptable = s3db.cms_post
                def cms_post_as_json(row):
                    body = row["cms_post.body"]
                    if not body:
                        return None
                    return json.dumps({"body": body,
                                       "date": row["cms_post.date"].isoformat(),
                                       "series_id": row["cms_post.series_id"],
                                       "priority": row["cms_post.priority"],
                                       "status_id": row["cms_post.status_id"],
                                       })

                ptable.json_dump = s3_fieldmethod("json_dump",
                                                  cms_post_as_json,
                                                  )
                s3db.configure("cms_post",
                               extra_fields = ("date",
                                               "series_id",
                                               "priority",
                                               "status_id",
                                               "body",
                                               ),
                               )

                etable = s3db.event_event
                def event_event_as_json(row):
                    name = row["event_event.name"]
                    if not name:
                        return None
                    return json.dumps({"name": name,
                                       "date": row["event_event.start_date"].isoformat(),
                                       })

                etable.json_dump = s3_fieldmethod("json_dump",
                                                  event_event_as_json,
                                                  )
                s3db.configure("event_event",
                               extra_fields = ("name",
                                               "start_date",
                                               ),
                               )

                itable = s3db.event_incident
                def event_incident_as_json(row):
                    name = row["event_incident.name"]
                    if not name:
                        return None
                    return json.dumps({"name": name,
                                       "date": row["event_incident.date"].isoformat(),
                                       })

                itable.json_dump = s3_fieldmethod("json_dump",
                                                  event_incident_as_json,
                                                  )
                s3db.configure("event_incident",
                               extra_fields = ("name",
                                               "date",
                                               ),
                               )

                ttable = s3db.project_task
                def project_task_as_json(row):
                    name = row["project_task.name"]
                    if not name:
                        return None
                    return json.dumps({"name": name,
                                       "date": row["project_task.date_due"].isoformat(),
                                       })

                ttable.json_dump = s3_fieldmethod("json_dump",
                                                  project_task_as_json,
                                                  )
                s3db.configure("project_task",
                               extra_fields = ("name",
                                               "date_due",
                                               ),
                               )

                notify_fields = ["name",
                                 "post.json_dump",
                                 "event.json_dump",
                                 "incident.json_dump",
                                 "task.json_dump",
                                 ]
                s3db.configure("pr_forum",
                               notify_fields = notify_fields,
                               notify_renderer = pr_forum_notify_renderer,
                               notify_subject = pr_forum_notify_subject,
                               # Keep default name, but it will use the one in the Template folder
                               #notify_template = notify_template,
                               )

            elif r.method is None:
                # Override default redirects from custom methods
                if r.component:
                    if r.representation != "aadata":
                        from gluon.tools import redirect
                        current.session.confirmation = current.response.confirmation
                        redirect(URL(args=[r.id, "custom"],
                                     extension = "", # ensure no .aadata
                                     ))
                elif r.representation != "aadata":
                    r.method = "browse"

            return True
        s3.prep = custom_prep

        #if "forum_membership" in current.request.args:
        #    # No sidebar menu
        #    current.menu.options = None
        #    attr["rheader"] = None
        return attr

    settings.customise_pr_forum_controller = customise_pr_forum_controller

    # -------------------------------------------------------------------------
    def customise_pr_forum_membership_resource(r, tablename):

        s3db = current.s3db
        table = s3db.pr_forum_membership

        f = table.admin
        f.readable = f.writable = True

        # CRUD strings
        function = r.function
        if function == "person":
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Membership"),
                title_display = T("Membership Details"),
                title_list = T("Memberships"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Memberships"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Added to Group"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Removed from Group"),
                msg_list_empty = T("Not yet a Member of any Group"))

        elif function in ("forum", "forum_membership"):
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Member"),
                title_display = T("Membership Details"),
                title_list = T("Group Members"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Members"),
                label_delete_button = T("Remove Person from Group"),
                msg_record_created = T("Person added to Group"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Person removed from Group"),
                msg_list_empty = T("This Group has no Members yet"))

            if function == "forum":
                # Virtual Fields
                from gluon import A, URL
                from s3 import s3_fieldmethod, s3_fullname
                auth = current.auth
                if auth.s3_has_role("ADMIN"):
                    method = "update"
                else:
                    ltable = s3db.pr_person_user
                    ptable = s3db.pr_person
                    query = (table.forum_id == r.id) & \
                            (table.admin == True) & \
                            (table.deleted == False) & \
                            (table.person_id == ptable.id) & \
                            (ptable.pe_id == ltable.pe_id) & \
                            (ltable.user_id == auth.user.id)
                    admin = current.db(query).select(ltable.id,
                                                     limitby = (0, 1)
                                                     ).first()
                    if admin:
                        method = "update"
                    else:
                        method = "read"
                def person_membership(row):
                    return A(s3_fullname(row["pr_forum_membership.person_id"]),
                             _href = URL(c="pr", f="forum",
                                         args = [row["pr_forum_membership.forum_id"], "forum_membership", row["pr_forum_membership.id"], "%s.popup" % method],
                                         vars = {"refresh": "custom-list-pr_forum_membership",
                                                 },
                                         extension = "", # ensure no .aadata
                                         ),
                             _class = "s3_modal",
                             )
                table.name_click = s3_fieldmethod("name_click",
                                                  person_membership,
                                                  # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                                  # @ToDo: Bulk lookups
                                                  represent = lambda v: v,
                                                  search_field = "person_id",
                                                  )

                list_fields = [(T("Person"), "name_click"),
                               #"person_id",
                               "admin",
                               "comments",
                               ]

                s3db.configure(tablename,
                               extra_fields = ("forum_id",
                                               "person_id",
                                               ),
                               list_fields = list_fields,
                               )

    settings.customise_pr_forum_membership_resource = customise_pr_forum_membership_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_resource(r, tablename):

        from gluon import A, URL
        from s3 import s3_fieldmethod, S3SQLCustomForm, S3SQLInlineComponent

        db = current.db
        s3db = current.s3db
        table = s3db.pr_group

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Resource"),
            title_display = T("Resource Details"),
            title_list = T("Resources"),
            title_update = T("Edit Resource"),
            label_list_button = T("List Resources"),
            label_delete_button = T("Delete Resource"),
            msg_record_created = T("Resource added"),
            msg_record_modified = T("Resource updated"),
            msg_record_deleted = T("Resource deleted"),
            msg_list_empty = T("No Resources currently registered"))

        field = table.status_id
        field.readable = field.writable = True

        crud_form = S3SQLCustomForm((T("Name"), "name"),
                                    "status_id",
                                    S3SQLInlineComponent("organisation_team",
                                                         fields = [("", "organisation_id")],
                                                         label = T("Organization"),
                                                         multiple = False,
                                                         ),
                                    "comments",
                                    )

        # Virtual Fields
        def team_name(row):
            return A(row["pr_group.name"],
                     _href = URL(c="pr", f="group",
                                 args = [row["pr_group.id"], "read"],
                                 vars = {"refresh": "custom-list-pr_group",
                                         },
                                 extension = "", # ensure no .aadata
                                 ),
                     _class = "s3_modal",
                     )
        table.name_click = s3_fieldmethod("name_click",
                                          team_name,
                                          # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                          # @ToDo: Bulk lookups
                                          represent = lambda v: v,
                                          search_field = "name",
                                          )

        utable = s3db.cms_post_team
        gfield = utable.group_id
        query = (utable.deleted == False)
        def updates(row):
            group_id = row["pr_group.id"]
            count = db(query & (gfield == group_id)).count()
            if count:
                return A(count,
                         _href = URL(c="cms", f="post",
                                     args = ["datalist.popup"],
                                     vars = {"post_team.group_id": group_id},
                                     ),
                         _class="s3_modal",
                         )
            else:
                return 0
        table.updates = s3_fieldmethod("updates",
                                       updates,
                                       # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                       # @ToDo: Bulk lookups
                                       represent = lambda v: v,
                                       #search_field = "name",
                                       )

        atable = db.s3_audit
        stable = s3db.sync_repository
        def team_source(row):
            query = (atable.record_id == row["pr_group.id"]) & \
                    (atable.tablename == "pr_group") & \
                    (atable.repository_id == stable.id)
            repo = db(query).select(stable.name,
                                    limitby=(0, 1)
                                    ).first()
            if repo:
                return repo.name
            else:
                return T("Internal")
        table.source = s3_fieldmethod("source", team_source)

        list_fields = [(T("Name"), "name_click"),
                       "status_id",
                       (T("Current Incident"), "active_incident__link.incident_id"),
                       (T("Organization"), "organisation_team.organisation_id"),
                       # Replaced with VF
                       #(T("Updates"), "post_team.post_id"),
                       (T("Updates"), "updates"),
                       ]

        report_fields = ["name",
                         "status_id",
                         (T("City"), "location_id$L3"),
                         "source",
                         "organisation_team.organisation_id",
                         ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       extra_fields = ("name",
                                       ),
                       list_fields = list_fields,
                       report_options = Storage(
                        rows=report_fields,
                        cols=report_fields,
                        fact=report_fields,
                        defaults=Storage(rows = "status_id",
                                         cols = "organisation_team.organisation_id",
                                         fact = "count(name)",
                                         totals = True)
                        ),
                       )

    settings.customise_pr_group_resource = customise_pr_group_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_controller(**attr):

        # Custom Browse
        from templates.WACOP.controllers import resource_Browse
        current.s3db.set_method("pr", "group",
                                method = "browse",
                                action = resource_Browse)

        # No sidebar menu
        current.menu.options = None

        refresh = current.request.get_vars.get("refresh")
        if refresh:
            # Popup from Browse
            current.menu.main = ""

            attr["rheader"] = wacop_rheader

            #from gluon import A, URL
            #attr["custom_crud_buttons"] = {"list_btn": A(T("Browse Resources"),
            #                                             _class="action-btn",
            #                                             _href=URL(args="browse"),
            #                                             _id="list-btn",
            #                                             )
            #                               }
            attr["custom_crud_buttons"] = {"list_btn": "",
                                           }

            response = current.response
            if response.confirmation:
                script = '''self.parent.$('#%s').dataTable().fnReloadAjax()''' % refresh
                response.s3.jquery_ready.append(script)

        return attr

    settings.customise_pr_group_controller = customise_pr_group_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        # Custom Profile
        from templates.WACOP.controllers import person_Dashboard
        current.s3db.set_method("pr", "person",
                                method = "dashboard",
                                action = person_Dashboard)

        # No sidebar menu
        current.menu.options = None

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def user_pe_id_default_filter(selector, tablename=None):
        """
            Default filter for pe_id:
            * Use the user's pe_id if logged-in
        """

        auth = current.auth
        if auth.is_logged_in():
            return auth.user.pe_id
        else:
            # no default
            return {}

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):

        from gluon import A, URL, IS_EMPTY_OR
        from s3 import s3_fieldmethod, IS_ONE_OF, S3DateFilter, S3OptionsFilter, S3TextFilter, S3SQLCustomForm, S3SQLInlineComponent

        method = r.method
        if method == "dashboard":
            # Default Filter to 'Tasks Assigned to me'
            from s3 import s3_set_default_filter
            s3_set_default_filter("~.pe_id",
                                  user_pe_id_default_filter,
                                  tablename = tablename)
        elif method == "filter":
            # Apply filter_vars
            for k, v in r.get_vars.items():
                # We only expect a maximum of 1 of these, no need to append
                from s3 import FS
                current.response.s3.filter = (FS(k) == v)

        db = current.db
        s3db = current.s3db
        table = s3db.project_task

        # Virtual Fields
        fn = r.function
        if fn == "forum":
            c = "pr"
        else:
            # Used from either the Event or Incident context
            c = "event"
        record_id = r.id
        def task_name(row):
            return A(row["project_task.name"],
                     _href = URL(c=c, f=fn,
                                 args=[record_id, "task", row["project_task.id"], "profile"],
                                 ),
                     )
        table.name_click = s3_fieldmethod("name_click",
                                          task_name,
                                          # over-ride the default represent of s3_unicode to prevent HTML being rendered too early
                                          represent = lambda v: v,
                                          search_field = "name",
                                          )

        # Assignee must be a System User
        etable = s3db.pr_pentity
        ltable = s3db.pr_person_user
        the_set = db(ltable.pe_id == etable.pe_id)
        f = table.pe_id
        f.requires = IS_EMPTY_OR(
                        IS_ONE_OF(the_set, "pr_pentity.pe_id",
                                  f.represent))

        # Custom Form
        crud_fields = ["name",
                       "description",
                       "source",
                       "priority",
                       "pe_id",
                       "date_due",
                       "status",
                       "comments",
                       S3SQLInlineComponent("document",
                                            name = "file",
                                            label = T("Files"),
                                            fields = [("", "file"),
                                                      #"comments",
                                                      ],
                                            ),
                       ]

        filterby = None
        if r.tablename != "pr_forum":
            auth = current.auth
            if auth.user:
                ADMIN = auth.s3_has_role("ADMIN")
                if not ADMIN:
                    # Can only Share to Groups that the User is a Member of
                    ptable = s3db.pr_person
                    mtable = s3db.pr_forum_membership
                    ftable = s3db.pr_forum
                    query = (ptable.pe_id == auth.user.pe_id) & \
                            (ptable.id == mtable.person_id) & \
                            (mtable.forum_id == ftable.id)
                    forums = db(query).select(ftable.id,
                                              ftable.name)
                    forum_ids = [f.id for f in forums]
                    filterby = dict(field = "forum_id",
                                    options = forum_ids,
                                    )

                crud_fields.insert(-1,
                                   S3SQLInlineComponent("task_forum",
                                                        name = "forum",
                                                        label = T("Share to Group"),
                                                        fields = [("", "forum_id")],
                                                        filterby = filterby,
                                                        ))

            if r.tablename == "event_event":
                # Can only link to Incidents within this Event
                itable = s3db.event_incident
                query = (itable.event_id == r.id) & \
                        (itable.closed == False) & \
                        (itable.deleted == False)
                the_set = db(query)
                f = s3db.event_task.incident_id
                f.requires = IS_EMPTY_OR(
                                IS_ONE_OF(the_set, "event_incident.id",
                                          f.represent,
                                          orderby="event_incident.name",
                                          sort=True))
                filterby = dict(field = "event_id",
                                options = r.id,
                                )
            else:
                filterby = None

        if r.tablename != "event_incident":
            crud_fields.insert(0,
                               S3SQLInlineComponent("incident",
                                                    fields = [("", "incident_id")],
                                                    label = T("Incident"),
                                                    multiple = False,
                                                    filterby = filterby,
                                                    ))

        crud_form = S3SQLCustomForm(*crud_fields)

        # Filters
        project_task_priority_opts = settings.get_project_task_priority_opts()
        project_task_status_opts = settings.get_project_task_status_opts()

        from templates.WACOP.controllers import text_filter_formstyle

        filter_widgets = [S3TextFilter(["name",
                                        "description",
                                        ],
                                       formstyle = text_filter_formstyle,
                                       label = T("Search"),
                                       _placeholder = T("Enter search term…"),
                                       _class = "filter-search",
                                       ),
                          S3OptionsFilter("priority",
                                          options = project_task_priority_opts,
                                          ),
                          S3OptionsFilter("pe_id",
                                          label = T("Assigned To"),
                                          none = T("Unassigned"),
                                          ),
                          S3OptionsFilter("status",
                                          options = project_task_status_opts,
                                          ),
                          S3OptionsFilter("created_by",
                                          label = T("Created By"),
                                          hidden = True,
                                          ),
                          S3DateFilter("created_on",
                                       label = T("Date Created"),
                                       hide_time = True,
                                       hidden = True,
                                       ),
                          S3DateFilter("date_due",
                                       hide_time = True,
                                       hidden = True,
                                       ),
                          S3DateFilter("modified_on",
                                       label = T("Date Modified"),
                                       hide_time = True,
                                       hidden = True,
                                       ),
                          ]

        def onaccept(form):
            """
                Update the modified_on of any forums to which the Task is Shared
            """
            task_id = form.vars.id
            ltable = s3db.project_task_forum
            forums = db(ltable.task_id == task_id).select(ltable.forum_id)
            len_forums = len(forums)
            if len_forums:
                ftable = s3db.pr_forum
                if len_forums == 1:
                    query = (ftable.id == forums.first().forum_id)
                else:
                    query = (ftable.id.belongs([f.forum_id for f in forums]))
                db(query).update(modified_on = r.utcnow)

        update_onaccept = s3db.get_config(tablename, "update_onaccept")
        if update_onaccept:
            update_onaccept = [update_onaccept, onaccept]
        else:
            update_onaccept = onaccept

        s3db.configure(tablename,
                       crud_form = crud_form,
                       extra_fields = ("name",
                                       ),
                       filter_widgets = filter_widgets,
                       list_fields = [(T("Description"), "name_click"),
                                      "status",
                                      "incident.incident_id",
                                      (T("Created"), "created_on"),
                                      (T("Due"), "date_due"),
                                      ],
                       orderby = "project_task.date_due",
                       update_onaccept = update_onaccept,
                       )

    settings.customise_project_task_resource = customise_project_task_resource

    # -------------------------------------------------------------------------
    def customise_project_task_controller(**attr):

        # No sidebar menu
        current.menu.options = None

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard postp
            if callable(standard_prep):
                result = standard_prep(r)

            task_id = r.id
            if task_id:
                # Share Button
                auth = current.auth
                user = auth.user
                if user:
                    db = current.db
                    s3db = current.s3db
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
                        from gluon import A, INPUT, LABEL, LI, TAG, UL
                        from s3 import ICON
                        ADMIN = auth.s3_has_role("ADMIN")
                        forum_ids = [f.id for f in forums]
                        ltable = s3db.project_task_forum
                        query = (ltable.task_id == task_id) & \
                                (ltable.forum_id.belongs(forum_ids))
                        shares = db(query).select(ltable.forum_id,
                                                  ltable.created_by,
                                                  ).as_dict(key="forum_id")
                        share_btn = A(ICON("share"),
                                       _href = "#",
                                       _class = "button radius small",
                                       _title = current.T("Share"),
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
                        dropdown["_data-c"] = "project"
                        dropdown["_data-f"] = "task"
                        dropdown["_data-i"] = task_id

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

                        s3.scripts.append("/%s/static/themes/WACOP/js/shares.js" % current.request.application)
                        script = '''S3.wacop_shares()'''
                        s3.jquery_ready.append(script)
                        s3.rfooter = share_btn

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_project_task_controller = customise_project_task_controller

# =============================================================================
def event_team_rheader(group_id,
                       event_id = None,
                       incident_id = None,
                       updates = False,
                       ):
    """
        RHeader for event_team
    """

    from gluon import A, DIV, SPAN, TABLE, TR, TH, URL

    T = current.T

    table = current.s3db.event_team
    if event_id:
        query = (table.event_id == event_id) & \
                (table.group_id == group_id)
        record = current.db(query).select(table.status_id,
                                          limitby=(0, 1),
                                          ).first()

        rheader_tabs = DIV(SPAN(A(T("Resource Details"),
                                  _href=URL(c="event", f="event",
                                            args = [event_id, "group", group_id],
                                            vars = {"refresh": "custom-list-event_team",
                                                    },
                                            ),
                                  _id="rheader_tab_group",
                                  ),
                                _class="tab_here" if not updates else "tab_other",
                                ),
                           SPAN(A(T("Updates"),
                                  _href=URL(c="pr", f="group",
                                            args = [group_id, "post", "datalist"],
                                            vars = {"event_id": event_id,
                                                    "refresh": "custom-list-event_team",
                                                    }
                                            ),
                                  _id="rheader_tab_post",
                                  ),
                                _class="tab_here" if updates else "tab_last",
                                ),
                           _class="tabs",
                           )
        rheader = DIV(TABLE(TR(TH("%s: " % table.group_id.label),
                               table.group_id.represent(group_id),
                               ),
                            TR(TH("%s: " % table.event_id.label),
                               table.event_id.represent(event_id),
                               ),
                            TR(TH("%s: " % table.status_id.label),
                               table.status_id.represent(record.status_id),
                               ),
                            ),
                      rheader_tabs)
    elif incident_id:
        query = (table.incident_id == incident_id) & \
                (table.group_id == group_id)
        record = current.db(query).select(table.status_id,
                                          limitby=(0, 1),
                                          ).first()

        rheader_tabs = DIV(SPAN(A(T("Resource Details"),
                                  _href=URL(c="event", f="incident",
                                            args = [incident_id, "group", group_id],
                                            vars = {"refresh": "custom-list-event_team",
                                                    },
                                            ),
                                  _id="rheader_tab_group",
                                  ),
                                _class="tab_here" if not updates else "tab_other",
                                ),
                           SPAN(A(T("Updates"),
                                  _href=URL(c="pr", f="group",
                                            args = [group_id, "post", "datalist"],
                                            vars = {"incident_id": incident_id,
                                                    "refresh": "custom-list-event_team",
                                                    }
                                            ),
                                  _id="rheader_tab_post",
                                  ),
                                _class="tab_here" if updates else "tab_last",
                                ),
                           _class="tabs",
                           )
        rheader = DIV(TABLE(TR(TH("%s: " % table.group_id.label),
                               table.group_id.represent(group_id),
                               ),
                            TR(TH("%s: " % table.incident_id.label),
                               table.incident_id.represent(incident_id),
                               ),
                            TR(TH("%s: " % table.status_id.label),
                               table.status_id.represent(record.status_id),
                               ),
                            ),
                      rheader_tabs)
    return rheader

# =============================================================================
def pr_group_rheader(r):
    """
        RHeader for pr_group
    """

    from gluon import A, DIV, SPAN, TABLE, TR, TH, URL

    T = current.T
    s3db = current.s3db
    group_id = r.id
    record = r.record
    table = s3db.pr_group

    updates = r.component

    ltable = s3db.org_organisation_team
    query = (ltable.group_id == group_id) & \
            (ltable.deleted == False)
    org = current.db(query).select(ltable.organisation_id,
                                   limitby=(0, 1)
                                   ).first()
    if org:
        org = TR(TH("%s: " % ltable.organisation_id.label),
                 ltable.organisation_id.represent(org.organisation_id),
                 )
    else:
        org = ""

    rheader_tabs = DIV(SPAN(A(T("Resource Details"),
                              _href=URL(c="pr", f="group",
                                        args = [group_id],
                                        vars = {"refresh": "custom-list-pr_group",
                                                },
                                        ),
                              _id="rheader_tab_group",
                              ),
                            _class="tab_here" if not updates else "tab_other",
                            ),
                       SPAN(A(T("Updates"),
                              _href=URL(c="pr", f="group",
                                        args = [group_id, "post", "datalist"],
                                        vars = {"refresh": "custom-list-pr_group",
                                                },
                                        ),
                              _id="rheader_tab_post",
                              ),
                            _class="tab_here" if updates else "tab_last",
                            ),
                       _class="tabs",
                       )
    rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                           record.name,
                           ),
                        TR(TH("%s: " % table.status_id.label),
                           table.status_id.represent(record.status_id),
                           ),
                        org,
                        TR(TH("%s: " % table.comments.label),
                           record.comments or current.messages["NONE"],
                           ),
                        ),
                  rheader_tabs)
    return rheader

# =============================================================================
def wacop_rheader(r, tabs=[]):
    """ WACOP custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "pr_group":

            if r.component_name == "post":
                incident_id = r.get_vars.get("incident_id")
                if incident_id:
                    # Look like event_team details
                    group_id = r.id
                    rheader = event_team_rheader(group_id, None, incident_id, updates=True)
                    return rheader
                else:
                    event_id = r.get_vars.get("event_id")
                    if event_id:
                        # Look like event_team details
                        group_id = r.id
                        rheader = event_team_rheader(group_id, event_id, None, updates=True)
                        return rheader
            # Normal
            rheader = pr_group_rheader(r)
            return rheader

        elif tablename == "event_incident":
            if r.component_name == "group":
                incident_id = r.id
                group_id = r.component_id
                rheader = event_team_rheader(group_id, None, incident_id, updates=False)
                return rheader
            else:
                # Unused
                return None

                if not tabs:
                    tabs = [(T("Incident Details"), None),
                            (T("Units"), "group"),
                            (T("Tasks"), "task"),
                            (T("Updates"), "post"),
                            ]

                rheader_fields = [["name"],
                                  ["date"],
                                  ["comments"],
                                  ]

        elif tablename == "event_event":
            if r.component_name == "group":
                event_id = r.id
                group_id = r.component_id
                rheader = event_team_rheader(group_id, event_id, None, updates=False)
                return rheader
            else:
                # Unused
                return None

                if not tabs:
                    tabs = [(T("Event Details"), None),
                            (T("Incidents"), "incident"),
                            (T("Units"), "group"),
                            (T("Tasks"), "task"),
                            (T("Updates"), "post"),
                            ]

                rheader_fields = [["name"],
                                  ["start_date"],
                                  ["comments"],
                                  ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# END =========================================================================
