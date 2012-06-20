# -*- coding: utf-8 -*-

""" Utilities """

# =============================================================================
# AAA - set user roles and check controller access permission
#
auth.s3_set_roles()

if not auth.permission.has_permission("read"):
    auth.permission.fail()

# =============================================================================
# Global definitions
#
s3_action_buttons = s3base.S3CRUD.action_buttons

# -----------------------------------------------------------------------------
def s3_register_validation():
    """ JavaScript client-side validation """

    # Client-side validation (needed to check for passwords being same)

    if request.cookies.has_key("registered"):
        password_position = "last"
    else:
        password_position = "first"

    if deployment_settings.get_auth_registration_mobile_phone_mandatory():
        mobile = """
mobile: {
    required: true
},
"""
    else:
        mobile = ""

    if deployment_settings.get_auth_registration_organisation_mandatory():
        org1 = """
organisation_id: {
    required: true
},
"""
        org2 = "".join(( """,
organisation_id: '""", str(T("Enter your organization")), """',
""" ))
    else:
        org1 = ""
        org2 = ""

    domains = ""
    if deployment_settings.get_auth_registration_organisation_hidden() and \
       request.controller != "admin":
        table = auth.settings.table_user
        table.organisation_id

        table = s3db.auth_organisation
        query = (table.organisation_id != None) & \
                (table.domain != None)
        whitelists = db(query).select(table.organisation_id,
                                      table.domain)
        if whitelists:
            domains = """$( '#auth_user_organisation_id__row' ).hide();
S3.whitelists = {
"""
            count = 0
            for whitelist in whitelists:
                count += 1
                domains += "'%s': %s" % (whitelist.domain,
                                         whitelist.organisation_id)
                if count < len(whitelists):
                    domains += ",\n"
                else:
                    domains += "\n"
            domains += """};
$( '#regform #auth_user_email' ).blur( function() {
    var email = $( '#regform #auth_user_email' ).val();
    var domain = email.split('@')[1];
    if (undefined != S3.whitelists[domain]) {
        $( '#auth_user_organisation_id' ).val(S3.whitelists[domain]);
    } else {
        $( '#auth_user_organisation_id__row' ).show();
    }
});
"""

    # validate signup form on keyup and submit
    # @ToDo: //remote: 'emailsurl'
    script = "".join(( domains, """
$('#regform').validate({
    errorClass: 'req',
    rules: {
        first_name: {
            required: true
        },""", mobile, """
        email: {
            required: true,
            email: true
        },""", org1, """
        password: {
            required: true
        },
        password_two: {
            required: true,
            equalTo: '.password:""", password_position, """'
        }
    },
    messages: {
        firstname: '""", str(T("Enter your firstname")), """',
        password: {
            required: '""", str(T("Provide a password")), """'
        },
        password_two: {
            required: '""", str(T("Repeat your password")), """',
            equalTo: '""", str(T("Enter the same password as above")), """'
        },
        email: {
            required: '""", str(T("Please enter a valid email address")), """',
            minlength: '""", str(T("Please enter a valid email address")), """'
        }""", org2, """
    },
    errorPlacement: function(error, element) {
        error.appendTo( element.parent().next() );
    },
    submitHandler: function(form) {
        form.submit();
    }
});""" ))
    s3.jquery_ready.append( script )

# -----------------------------------------------------------------------------
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
# Shorteners

# Names - e.g. when used in Dropdowns
# - unused currently?
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name

# -----------------------------------------------------------------------------
# Date/Time representation functions
s3_date_represent = S3DateTime.date_represent
s3_time_represent = S3DateTime.time_represent
s3_datetime_represent = S3DateTime.datetime_represent
s3_utc_represent = lambda dt: s3_datetime_represent(dt, utc=True)
s3_date_represent_utc = lambda date: s3_date_represent(date, utc=True)

# -----------------------------------------------------------------------------
def s3_filename(filename):
    """
        Convert a string into a valid filename on all OS

        http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python/698714#698714
    """
    import string
    import unicodedata

    validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

    filename = unicode(filename)
    cleanedFilename = unicodedata.normalize("NFKD",
                                            filename).encode("ASCII", "ignore")

    return "".join(c for c in cleanedFilename if c in validFilenameChars)

# -----------------------------------------------------------------------------
def s3_include_debug():
    """
        Generates html to include:
            the js scripts listed in /static/scripts/tools/sahana.js.cfg
            the css listed in /private/templates/<template>/css.cfg
    """

    # Disable printing
    class dummyStream:
        """ dummyStream behaves like a stream but does nothing. """
        def __init__(self): pass
        def write(self,data): pass
        def read(self,data): pass
        def flush(self): pass
        def close(self): pass

    save_stdout = sys.stdout
    # Redirect all prints
    sys.stdout = dummyStream()

    folder = request.folder
    appname = request.application
    theme = settings.get_theme()

    # JavaScript
    scripts_dir_path = "%s/static/scripts" % folder
    sys.path.append( "%s/tools" % scripts_dir_path)
    import mergejsmf

    configDictCore = {
        "web2py": scripts_dir_path,
        "T2":     scripts_dir_path,
        "S3":     scripts_dir_path
    }
    configFilename = "%s/tools/sahana.js.cfg"  % scripts_dir_path
    (fs, files) = mergejsmf.getFiles(configDictCore, configFilename)

    # Restore prints
    sys.stdout = save_stdout

    include = ""
    for file in files:
        include = '%s\n<script src="/%s/static/scripts/%s" type="text/javascript"></script>' \
            % (include, appname, file)

    # CSS
    include = "%s\n <!-- CSS Syles -->" % include
    css_cfg = "%s/private/templates/%s/css.cfg" % (folder, theme)
    try:
        f = open(css_cfg, "r")
    except:
        raise HTTP(500, "Theme configuration file missing: private/templates/%s/css.cfg" % theme)
    files = f.readlines()
    files = files[:-1]
    for file in files:
        include = '%s\n<link href="/%s/static/styles/%s" rel="stylesheet" type="text/css" />' \
            % (include, appname, file[:-1])
    f.close()

    return XML(include)

# -----------------------------------------------------------------------------
def s3_table_links(reference):
    """
        Return a dict of tables & their fields which have references to the
        specified table

        @deprecated: to be replaced by db[tablename]._referenced_by
        - used by controllers/gis.py & pr.py
    """

    s3mgr.model.load_all_models()

    tables = {}
    for table in db.tables:
        count = 0
        for field in db[table].fields:
            if str(db[table][field].type) == "reference %s" % reference:
                if count == 0:
                    tables[table] = {}
                tables[table][count] = field
                count += 1

    return tables

# -----------------------------------------------------------------------------
# CRUD functions
# -----------------------------------------------------------------------------
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
        raise HTTP (400, s3mgr.xml.json_message(success=False, status_code="400", message="Need a Value for the Y axis"))
    elif nameKey and not r.table.get(nameKey):
        raise HTTP (400, s3mgr.xml.json_message(success=False, status_code="400", message=nameKey + " attribute not found in this resource."))

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
def s3_copy(r, **attr):
    """
        Copy a record

        used as REST method handler for S3Resources

        @todo: move into S3CRUDHandler
    """

    redirect(URL(args="create", vars={"from_record":r.id}))

# -----------------------------------------------------------------------------
def s3_import_prep(import_data):
    """
        Example for an import pre-processor

        @param import_data: a tuple of (resource, tree)
    """

    resource, tree = import_data

    #print "Import to %s" % resource.tablename
    #print s3mgr.xml.tostring(tree, pretty_print=True)

    # Use this to skip the import:
    #resource.skip_import = True

# Import pre-process
# This can also be a Storage of {tablename = function}*
s3mgr.import_prep = s3_import_prep

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

            s3mgr.configure(tablename, **attr)

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

        create_onvalidation     Function/Lambda for additional record validation on create
        create_onaccept         Function/Lambda after successful record insertion

        update_onvalidation     Function/Lambda for additional record validation on update
        update_onaccept         Function/Lambda after successful record update

        onvalidation            Fallback for both create_onvalidation and update_onvalidation
        onaccept                Fallback for both create_onaccept and update_onaccept
        ondelete                Function/Lambda after record deletion
    """

    # Parse the request
    r = s3mgr.parse_request(prefix, resourcename)

    # Set method handlers
    r.set_handler("barchart", s3_barchart)
    r.set_handler("compose", s3base.S3Compose())
    r.set_handler("copy", s3_copy)
    r.set_handler("report", s3base.S3Cube())
    r.set_handler("import", s3base.S3PDF(),
                  http = ["GET", "POST"],
                  representation="pdf")
    r.set_handler("import", s3base.S3Importer())
    r.set_handler("map", s3base.S3Map())

    # Execute the request
    output = r(**attr)

    if isinstance(output, dict) and (not r.method or r.method in ("report", "search")):
        if s3.actions is None:

            # Add default action buttons
            prefix, name, table, tablename = r.target()
            authorised = s3_has_permission("update", tablename)

            # If the component has components itself, then use the
            # component's native controller for CRU(D) => make sure
            # you have one, or override by native=False
            if r.component and s3mgr.model.has_components(table):
                native = output.get("native", True)
            else:
                native = False

            # Get table config
            model = s3mgr.model
            listadd = model.get_config(tablename, "listadd", True)
            editable = model.get_config(tablename, "editable", True) and \
                       not auth.permission.ownership_required("update", table)
            deletable = model.get_config(tablename, "deletable", True)
            copyable = model.get_config(tablename, "copyable", False)

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

    elif r.method != "import":
        s3.actions = None

    return output

# Enable access to this function from modules
current.rest_controller = s3_rest_controller

# END =========================================================================
