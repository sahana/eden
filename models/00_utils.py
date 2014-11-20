# -*- coding: utf-8 -*-

"""
    Common Utilities run most requests
"""

# =============================================================================
if request.is_local:
    # This is a request made from the local server

    f = get_vars.get("format", None)
    auth_token = get_vars.get("subscription", None)
    if auth_token and f == "msg":
        # Subscription lookup request
        rtable = s3db.pr_subscription_resource
        stable = s3db.pr_subscription
        utable = s3db.pr_person_user
        join = [stable.on(stable.id == rtable.subscription_id),
                utable.on(utable.pe_id == stable.pe_id)]

        user = db(rtable.auth_token == auth_token).select(utable.user_id,
                                                          join=join,
                                                          limitby=(0, 1)) \
                                                  .first()
        if user:
            # Impersonate subscriber
            auth.s3_impersonate(user.user_id)
        else:
            # Anonymous request
            auth.s3_impersonate(None)

# =============================================================================
# Check Permissions & fail as early as we can
#
# Set user roles
# - requires access to tables
auth.s3_set_roles()

# Check access to this controller
if not auth.permission.has_permission("read"):
    auth.permission.fail()

# =============================================================================
# Menus
#
from s3layouts import *
import s3menus as default_menus

S3MainMenu = default_menus.S3MainMenu
S3OptionsMenu = default_menus.S3OptionsMenu

current.menu = Storage(options=None, override={})
if auth.permission.format in ("html"):
    menus = None
    theme = settings.get_theme()
    if theme != "default":
        # If there is a custom Theme, then attempot to load a custom menu from it
        menus = "applications.%s.private.templates.%s.menus" % \
                (appname, theme)
    else:
        template = settings.get_template()
        if template != "default":
            # If there is a custom Template, then attempt to load a custom menu from it
            menus = "applications.%s.private.templates.%s.menus" % \
                    (appname, template)
    if menus:
        try:
            exec("import %s as deployment_menus" % menus)
        except ImportError:
            pass
        else:
            if "S3MainMenu" in deployment_menus.__dict__:
                S3MainMenu = deployment_menus.S3MainMenu

            if "S3OptionsMenu" in deployment_menus.__dict__:
                S3OptionsMenu = deployment_menus.S3OptionsMenu

    main = S3MainMenu.menu()
else:
    main = None

menu = current.menu
menu["main"] = main

# Override controller menus
# @todo: replace by current.menu.override
s3_menu_dict = {}

# =============================================================================
def s3_get_utc_offset():
    """ Get the current UTC offset for the client """

    offset = None

    if auth.is_logged_in():
        # 1st choice is the personal preference (useful for GETs if user wishes to see times in their local timezone)
        offset = session.auth.user.utc_offset
        if offset:
            offset = offset.strip()

    if not offset:
        # 2nd choice is what the client provides in the hidden field (for form POSTs)
        offset = request.post_vars.get("_utc_offset", None)
        if offset:
            offset = int(offset)
            utcstr = offset < 0 and "UTC +" or "UTC -"
            hours = abs(int(offset/60))
            minutes = abs(int(offset % 60))
            offset = "%s%02d%02d" % (utcstr, hours, minutes)
            # Make this the preferred value during this session
            if auth.is_logged_in():
                session.auth.user.utc_offset = offset

    if not offset:
        # 3rd choice is the server default (what most clients should see the timezone as)
        offset = deployment_settings.L10n.utc_offset

    return offset

# Store last value in session
session.s3.utc_offset = s3_get_utc_offset()

# -----------------------------------------------------------------------------
def s3_rest_controller(prefix=None, resourcename=None, **attr):
    """
        Helper function to apply the S3Resource REST interface

        @param prefix: the application prefix
        @param resourcename: the resource name (without prefix)
        @param attr: additional keyword parameters

        Any keyword parameters will be copied into the output dict (provided
        that the output is a dict). If a keyword parameter is callable, then
        it will be invoked, and its return value will be added to the output
        dict instead. The callable receives the S3Request as its first and
        only parameter.

        CRUD can be configured per table using:

            s3db.configure(tablename, **attr)

        *** Redirection:

        create_next             URL to redirect to after a record has been created
        update_next             URL to redirect to after a record has been updated
        delete_next             URL to redirect to after a record has been deleted

        *** Form configuration:

        list_fields             list of names of fields to include into list views
        subheadings             Sub-headings (see separate documentation)
        listadd                 Enable/Disable add-form in list views

        *** CRUD configuration:

        editable                Allow/Deny record updates in this table
        deletable               Allow/Deny record deletions in this table
        insertable              Allow/Deny record insertions into this table
        copyable                Allow/Deny record copying within this table

        *** Callbacks:

        create_onvalidation     Function for additional record validation on create
        create_onaccept         Function after successful record insertion

        update_onvalidation     Function for additional record validation on update
        update_onaccept         Function after successful record update

        onvalidation            Fallback for both create_onvalidation and update_onvalidation
        onaccept                Fallback for both create_onaccept and update_onaccept
        ondelete                Function after record deletion
    """

    # Customise Controller from Template
    attr = settings.customise_controller("%s_%s" % (prefix or request.controller,
                                                    resourcename or request.function),
                                         **attr)

    # Parse the request
    r = s3_request(prefix, resourcename)

    # Customize target resource(s) from Template
    r.customise_resource()

    # Configure standard method handlers
    set_handler = r.set_handler
    from s3db.cms import S3CMS
    set_handler("cms", S3CMS)
    set_handler("compose", s3base.S3Compose)
    # @ToDo: Make work in Component Tabs:
    set_handler("copy", lambda r, **attr: \
                               redirect(URL(args="create",
                                            vars={"from_record":r.id})))
    set_handler("deduplicate", s3base.S3Merge)
    set_handler("filter", s3base.S3Filter)
    set_handler("hierarchy", s3base.S3HierarchyCRUD)
    set_handler("import", s3base.S3Importer)
    set_handler("map", s3base.S3Map)
    set_handler("profile", s3base.S3Profile)
    set_handler("report", s3base.S3Report)
    set_handler("report", s3base.S3Report, transform=True)
    set_handler("timeplot", s3base.S3TimePlot) # temporary setting for testing
    set_handler("search_ac", s3base.search_ac)
    set_handler("summary", s3base.S3Summary)

    # Don't load S3PDF unless needed (very slow import with Reportlab)
    method = r.method
    if method == "import" and r.representation == "pdf":
        from s3.s3pdf import S3PDF
        set_handler("import", S3PDF(),
                    http = ["GET", "POST"],
                    representation="pdf")

    # Plugin OrgRoleManager when appropriate
    s3base.S3OrgRoleManager.set_method(r)

    # Execute the request
    output = r(**attr)

    if isinstance(output, dict) and \
       method in (None,
                  "report",
                  "search",
                  "datatable",
                  "datatable_f",
                  "summary"):

        if s3.actions is None:

            # Add default action buttons
            prefix, name, table, tablename = r.target()
            authorised = s3_has_permission("update", tablename)

            # If a component has components itself, then action buttons
            # can be forwarded to the native controller by setting native=True
            if r.component and s3db.has_components(table):
                native = output.get("native", False)
            else:
                native = False

            # Get table config
            get_config = s3db.get_config
            listadd = get_config(tablename, "listadd", True)
            editable = get_config(tablename, "editable", True) and \
                       not auth.permission.ownership_required("update", table)
            deletable = get_config(tablename, "deletable", True)
            copyable = get_config(tablename, "copyable", False)

            # URL to open the resource
            open_url = r.resource.crud._linkto(r,
                                               authorised=authorised,
                                               update=editable,
                                               native=native)("[id]")

            # Add action buttons for Open/Delete/Copy as appropriate
            s3_action_buttons(r,
                              deletable=deletable,
                              copyable=copyable,
                              editable=editable,
                              read_url=open_url,
                              update_url=open_url
                              # To use modals
                              #update_url="%s.popup?refresh=list" % open_url
                              )

            # Override Add-button, link to native controller and put
            # the primary key into get_vars for automatic linking
            if native and not listadd and \
               s3_has_permission("create", tablename):
                label = s3base.S3CRUD.crud_string(tablename,
                                                  "label_create")
                hook = r.resource.components[name]
                fkey = "%s.%s" % (name, hook.fkey)
                get_vars_copy = get_vars.copy()
                get_vars_copy.update({fkey: r.record[hook.fkey]})
                url = URL(prefix, name, args=["create"], vars=get_vars_copy)
                add_btn = A(label, _href=url, _class="action-btn")
                output.update(add_btn=add_btn)

    elif method not in ("import",
                        "review",
                        "approve",
                        "reject",
                        "deduplicate"):
        s3.actions = None

    if get_vars.tour:
        output = s3db.tour_builder(output)

    return output

# Enable access to this function from modules
current.rest_controller = s3_rest_controller

# END =========================================================================
