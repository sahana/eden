# -*- coding: utf-8 -*-

"""
    Common Utilities run most requests
"""

# =============================================================================
if request.is_local:
    # This is a request made from the local server

    search_subscription = request.get_vars.get("search_subscription", None)
    if search_subscription:
        # We're doing a request for a saved search
        table = s3db.pr_saved_search
        search = db(table.auth_token == search_subscription).select(table.pe_id,
                                                                    limitby=(0, 1)
                                                                    ).first()
        if search:
            # Impersonate user
            user_id = auth.s3_get_user_id(pe_id=search.pe_id)

            if user_id:
                # Impersonate the user who is subscribed to this saved search
                auth.s3_impersonate(user_id)
            else:
                # Request is ANONYMOUS
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
from eden.layouts import *
import eden.menus as default_menus

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

# =============================================================================
# CRUD functions
#
def s3_barchart(r, **attr):
    """
        Provide simple barcharts for resource attributes
        SVG representation uses the SaVaGe library
        Need to request a specific value to graph in request.vars

        used as REST method handler for S3Resources

        @todo: replace by a S3MethodHandler
    """

    # Get all the variables and format them if needed
    valKey = r.vars.get("value")

    nameKey = r.vars.get("name")
    if not nameKey and r.table.get("name"):
        # Try defaulting to the most-commonly used:
        nameKey = "name"

    # The parameter value is required; it must be provided
    # The parameter name is optional; it is useful, but we don't need it
    # Here we check to make sure we can find value in the table,
    # and name (if it was provided)
    if not r.table.get(valKey):
        raise HTTP (400, current.xml.json_message(success=False, status_code="400", message="Need a Value for the Y axis"))
    elif nameKey and not r.table.get(nameKey):
        raise HTTP (400, current.xml.json_message(success=False, status_code="400", message=nameKey + " attribute not found in this resource."))

    start = request.vars.get("start")
    if start:
        start = int(start)

    limit = r.vars.get("limit")
    if limit:
        limit = int(limit)

    settings = r.vars.get("settings")
    if settings:
        settings = json.loads(settings)
    else:
        settings = {}

    if r.representation.lower() == "svg":
        r.response.headers["Content-Type"] = "image/svg+xml"

        from savage import graph
        bar = graph.BarGraph(settings=settings)

        title = deployment_settings.modules.get(module).name_nice
        bar.setTitle(title)

        if nameKey:
            xlabel = r.table.get(nameKey).label
            if xlabel:
                bar.setXLabel(str(xlabel))
            else:
                bar.setXLabel(nameKey)

        ylabel = r.table.get(valKey).label
        if ylabel:
            bar.setYLabel(str(ylabel))
        else:
            bar.setYLabel(valKey)

        try:
            records = r.resource.load(start, limit)
            for entry in r.resource:
                val = entry[valKey]

                # Can't graph None type
                if not val is None:
                    if nameKey:
                        name = entry[nameKey]
                    else:
                        name = None
                    bar.addBar(name, val)
            return bar.save()
        # If the field that was provided was not numeric, we have problems
        except ValueError:
            raise HTTP(400, "Bad Request")
    else:
        raise HTTP(501, body=BADFORMAT)

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

    # Parse the request
    r = s3_request(prefix, resourcename)

    # Set method handlers
    method = r.method
    set_handler = r.set_handler
    set_handler("barchart", s3_barchart)
    set_handler("compose", s3base.S3Compose())
    set_handler("copy", lambda r, **attr: redirect(URL(args="create",
                                                       vars={"from_record":r.id})))
    set_handler("import", s3base.S3Importer())
    set_handler("map", lambda r, **attr: s3base.S3Map()(r, **attr))
    set_handler("report", s3base.S3Report())

    if method == "import" and \
       r.representation == "pdf":
        # Don't load S3PDF unless needed (very slow import with Reportlab)
        from s3.s3pdf import S3PDF
        set_handler("import", S3PDF(),
                    http = ["GET", "POST"],
                    representation="pdf")

    # Plugin OrgRoleManager where appropriate
    if r.record and auth.user is not None and \
       r.tablename in s3base.S3OrgRoleManager.ENTITY_TYPES:

        sr = auth.get_system_roles()
        realms = auth.user.realms or Storage()

        if sr.ADMIN in realms or sr.ORG_ADMIN in realms and \
           (realms[sr.ORG_ADMIN] is None or \
            r.record.pe_id in realms[sr.ORG_ADMIN]):
            r.set_handler("roles", s3base.S3OrgRoleManager())

    # Execute the request
    output = r(**attr)

    if isinstance(output, dict) and (not method or method in ("report", "search")):
        if s3.actions is None:

            # Add default action buttons
            prefix, name, table, tablename = r.target()
            authorised = s3_has_permission("update", tablename)

            # If the component has components itself, then use the
            # component's native controller for CRU(D) => make sure
            # you have one, or override by native=False
            if r.component and s3db.has_components(table):
                native = output.get("native", True)
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
                              update_url=open_url)

            # Override Add-button, link to native controller and put
            # the primary key into vars for automatic linking
            if native and not listadd and \
               s3_has_permission("create", tablename):
                label = s3base.S3CRUD.crud_string(tablename,
                                                  "label_create_button")
                hook = r.resource.components[name]
                fkey = "%s.%s" % (name, hook.fkey)
                vars = request.vars.copy()
                vars.update({fkey: r.id})
                url = URL(prefix, name, args=["create"], vars=vars)
                add_btn = A(label, _href=url, _class="action-btn")
                output.update(add_btn=add_btn)

    elif method not in ("import", "review", "approve", "reject"):
        s3.actions = None

    return output

# Enable access to this function from modules
current.rest_controller = s3_rest_controller

# END =========================================================================
