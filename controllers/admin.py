# -*- coding: utf-8 -*-

"""
    Admin Controllers
"""

module = request.controller
resourcename = request.function

# S3 framework functions
# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# =============================================================================
@auth.s3_requires_membership(1)
def setting():
    """
        Custom page to link to those Settings which can be edited through the web interface
    """

    return dict()

# =============================================================================
# AAA
# =============================================================================
@auth.s3_requires_membership(1)
def role():
    """
        Role Manager
    """

    # ACLs as component of roles
    s3db.add_component(auth.permission.table,
                       auth_group="group_id")

    def prep(r):
        if r.representation != "html":
            return False
        handler = s3base.S3RoleManager()
        modules = settings.modules
        handler.controllers = Storage([(m, modules[m])
                                        for m in modules
                                        if modules[m].restricted])
        # Configure REST methods
        set_handler = r.set_handler
        set_handler("users", handler)
        set_handler("read", handler)
        set_handler("list", handler)
        set_handler("copy", handler)
        set_handler("create", handler)
        set_handler("update", handler)
        set_handler("delete", handler)
        return True
    s3.prep = prep

    s3.stylesheets.append( "S3/role.css" )
    output = s3_rest_controller("auth", "group")
    return output

# -----------------------------------------------------------------------------
def user():
    """ RESTful CRUD controller """

    table = auth.settings.table_user

    if s3_has_role("ADMIN"):
        # Needed as Admin has all roles
        pe_ids = None
    elif s3_has_role("ORG_ADMIN"):
        # Filter users to just those belonging to the Org Admin's Org & Descendants
        otable = s3db.org_organisation
        pe_id = db(otable.id == auth.user.organisation_id).select(otable.pe_id,
                                                                  limitby=(0, 1)
                                                                  ).first().pe_id
        pe_ids = s3db.pr_get_descendants(pe_id, entity_types="org_organisation")
        pe_ids.append(pe_id)
        s3.filter = (otable.pe_id.belongs(pe_ids)) & \
                    (table.organisation_id == otable.id)
    else:
        auth.permission.fail()

    auth.configure_user_fields(pe_ids)

    s3db.add_component("auth_membership", auth_user="user_id")

    list_fields = ["first_name",
                   "last_name",
                   "email",
                   ]
    lappend = list_fields.append
    if len(settings.get_L10n_languages()) > 1:
        lappend("language")
    if settings.get_auth_registration_requests_organisation():
        lappend("organisation_id")
    if settings.get_auth_registration_requests_organisation_group():
        lappend("org_group_id")
    if settings.get_auth_registration_requests_site():
        lappend("site_id")
    if settings.get_auth_registration_link_user_to() and settings.get_auth_show_link():
        lappend("link_user_to")
    lappend((T("Roles"), "membership.group_id"))

    s3db.configure("auth_user",
                   main="first_name",
                   create_next = URL(c="admin", f="user", args=["[id]", "roles"]),
                   create_onaccept = lambda form: auth.s3_approve_user(form.vars),
                   list_fields = list_fields,
                   )

    def disable_user(r, **args):
        if not r.id:
            session.error = T("Can only disable 1 record at a time!")
            redirect(URL(args=[]))

        if r.id == session.auth.user.id: # we're trying to disable ourself
            session.error = T("Cannot disable your own account!")
            redirect(URL(args=[]))

        db(table.id == r.id).update(registration_key = "disabled")
        session.confirmation = T("User Account has been Disabled")
        redirect(URL(args=[]))

    def approve_user(r, **args):
        if not r.id:
            session.error = T("Can only approve 1 record at a time!")
            redirect(URL(args=[]))

        user = db(table.id == r.id).select(limitby=(0, 1)).first()
        auth.s3_approve_user(user)

        session.confirmation = T("User Account has been Approved")
        redirect(URL(args=[r.id, "roles"]))

    def link_user(r, **args):
        if not r.id:
            session.error = T("Can only update 1 record at a time!")
            redirect(URL(args=[]))

        user = db(table.id == r.id).select(limitby=(0, 1)).first()
        auth.s3_link_user(user)

        session.confirmation = T("User has been (re)linked to Person and Human Resource record")
        redirect(URL(args=[]))

    # Custom Methods
    set_method = s3db.set_method
    set_method("auth", "user", method="roles",
               action=s3base.S3RoleManager())

    set_method("auth", "user", method="disable",
               action=disable_user)

    set_method("auth", "user", method="approve",
               action=approve_user)

    set_method("auth", "user", method="link",
               action=link_user)

    # CRUD Strings
    ADD_USER = T("Add User")
    s3.crud_strings["auth_user"] = Storage(
        title_create = ADD_USER,
        title_display = T("User Details"),
        title_list = T("Users"),
        title_update = T("Edit User"),
        title_search = T("Search Users"),
        title_upload = T("Import Users"),
        subtitle_create = T("Add New User"),
        label_list_button = T("List Users"),
        label_create_button = ADD_USER,
        label_delete_button = T("Delete User"),
        msg_record_created = T("User added"),
        msg_record_modified = T("User updated"),
        msg_record_deleted = T("User deleted"),
        msg_list_empty = T("No Users currently registered"))

    def rheader(r):
        if r.representation != "html":
            return None

        rheader = DIV()

        if r.record:
            id = r.id
            registration_key = r.record.registration_key
            if not registration_key:
                btn = A(T("Disable"),
                        _class = "action-btn",
                        _title = "Disable User",
                        _href = URL(args=[id, "disable"])
                        )
                rheader.append(btn)
                if settings.get_auth_show_link():
                    btn = A(T("Link"),
                            _class = "action-btn",
                            _title = "Link (or refresh link) between User, Person & HR Record",
                            _href = URL(args=[id, "link"])
                            )
                    rheader.append(btn)
            #elif registration_key == "pending":
            #    btn = A(T("Approve"),
            #            _class = "action-btn",
            #            _title = "Approve User",
            #            _href = URL(args=[id, "approve"])
            #            )
            #    rheader.append(btn)
            else:
                # Verify & Approve
                btn = A(T("Approve"),
                        _class = "action-btn",
                        _title = "Approve User",
                        _href = URL(args=[id, "approve"])
                        )
                rheader.append(btn)

            tabs = [(T("User Details"), None),
                    (T("Roles"), "roles")
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader.append(rheader_tabs)
        return rheader

    # Pre-processor
    def prep(r):
        if r.interactive:
            s3db.configure(r.tablename,
                           deletable=False,
                           # jquery.validate is clashing with dataTables so don't embed the create form in with the List
                           listadd=False,
                           addbtn=True,
                           sortby = [[2, "asc"], [1, "asc"]],
                           # Password confirmation
                           create_onvalidation = user_create_onvalidation)
        elif r.representation == "xls":
            lappend((T("Status"), "registration_key"))

        if r.method == "delete" and r.http == "GET":
            if r.id == session.auth.user.id: # we're trying to delete ourself
                request.get_vars.update({"user.id":str(r.id)})
                r.id = None
                s3db.configure(r.tablename,
                               delete_next = URL(c="default", f="user/logout"))
                s3.crud.confirm_delete = T("You are attempting to delete your own account - are you sure you want to proceed?")

        if r.http == "GET" and not r.method:
            session.s3.cancel = r.url()
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            # Only show the disable button if the user is not currently disabled
            table = r.table
            query = (table.registration_key == None) | \
                    (table.registration_key == "")
            rows = db(query).select(table.id)
            restrict = [str(row.id) for row in rows]
            s3.actions = [dict(label=str(UPDATE), _class="action-btn",
                               url=URL(c="admin", f="user",
                                       args=["[id]", "update"])),
                          dict(label=str(T("Roles")), _class="action-btn",
                               url=URL(c="admin", f="user",
                                       args=["[id]", "roles"])),
                          dict(label=str(T("Disable")), _class="action-btn",
                               url=URL(c="admin", f="user",
                                       args=["[id]", "disable"]),
                               restrict = restrict)
                          ]
            if settings.get_auth_show_link():
                s3.actions.insert(1, dict(label=str(T("Link")),
                                          _class="action-btn",
                                          _title = str(T("Link (or refresh link) between User, Person & HR Record")),
                                          url=URL(c="admin", f="user",
                                                  args=["[id]", "link"]),
                                          restrict = restrict)
                                  )
            # Only show the approve button if the user is currently pending
            query = (table.registration_key != "disabled") & \
                    (table.registration_key != None) & \
                    (table.registration_key != "")
            rows = db(query).select(table.id)
            restrict = [str(row.id) for row in rows]
            s3.actions.append(
                    dict(label=str(T("Approve")), _class="action-btn",
                         url=URL(c="admin", f="user",
                                 args=["[id]", "approve"]),
                         restrict = restrict)
                )
            # Add some highlighting to the rows
            query = (table.registration_key.belongs(["disabled", "pending"]))
            rows = db(query).select(table.id,
                                    table.registration_key)
            s3.dataTableStyleDisabled = s3.dataTableStyleWarning = [str(row.id) for row in rows if row.registration_key == "disabled"]
            s3.dataTableStyleAlert = [str(row.id) for row in rows if row.registration_key == "pending"]

            # Translate the status values
            values = [dict(col=6, key="", display=str(T("Active"))),
                      dict(col=6, key="None", display=str(T("Active"))),
                      dict(col=6, key="pending", display=str(T("Pending"))),
                      dict(col=6, key="disabled", display=str(T("Disabled")))
                      ]
            s3.dataTableDisplay = values

            # @ToDo: Merge these with the code in s3aaa.py and use S3SQLCustomForm to implement
            form = output.get("form", None)
            if not form:
                create_url = URL(args=["create"])
                output["showadd_btn"] = s3base.S3CRUD.crud_button(T("Add User"),
                                                                  _href=create_url)
                return output
            form.attributes["_id"] = "regform"
            if s3_formstyle == "bootstrap":
                div = DIV(LABEL("%s:" % T("Verify password"),
                                _id="auth_user_password_two__label",
                                _for="password_two",
                                _class="control-label",
                                ),
                          DIV(INPUT(_name="password_two",
                                    _id="password_two",
                                    _type="password",
                                    _disabled="disabled",
                                    _class="password input-xlarge",
                                    ),
                              _class="controls",
                              ),
                          # Somewhere to store Error Messages
                          SPAN(_class="help-block"),
                          _id="auth_user_password_two__row",
                          _class="control-group hide",
                          )
                form[0].insert(4, div)
                # @ToDo:
                #if settings.get_auth_registration_requests_mobile_phone():
            else:
                # Assume callable
                id = "auth_user_password_two__row"
                label = "%s:" % T("Verify password")
                widget = INPUT(_name="password_two",
                               _id="password_two",
                               _type="password",
                               _disabled="disabled",
                               )
                comment = ""
                row = s3_formstyle(id, label, widget, comment, hidden=True)
                if s3.theme == "DRRPP":
                    form[0].insert(4, row)
                else:
                    form[0].insert(8, row)
                if settings.get_auth_registration_requests_mobile_phone():
                    id = "auth_user_mobile__row"
                    label = "%s:" % settings.get_ui_label_mobile_phone()
                    widget = INPUT(_name="mobile",
                                   _id="mobile",
                                   _class="string",
                                   )
                    comment = ""
                    row = s3_formstyle(id, label, widget, comment)
                    # @ToDo:
                    #if s3.theme == "DRRPP":
                    form[0].insert(-8, row)

            # Add client-side validation
            auth.s3_register_validation()

        return output
    s3.postp = postp

    s3mgr.import_prep = auth.s3_import_prep

    output = s3_rest_controller("auth", "user",
                                rheader=rheader,
                                csv_template=("auth", "user"),
                                csv_stylesheet=("auth", "user.xsl")
                                )
    return output

# =============================================================================
def group():
    """
        RESTful CRUD controller
        - used by role_required autocomplete
    """

    tablename = "auth_group"

    if not auth.s3_has_role(ADMIN):
        s3db.configure(tablename,
                       editable=False,
                       insertable=False,
                       deletable=False)

    # CRUD Strings
    ADD_ROLE = T("Add Role")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ROLE,
        title_display = T("Role Details"),
        title_list = T("Roles"),
        title_update = T("Edit Role"),
        title_search = T("Search Roles"),
        subtitle_create = T("Add New Role"),
        label_list_button = T("List Roles"),
        label_create_button = ADD_ROLE,
        msg_record_created = T("Role added"),
        msg_record_modified = T("Role updated"),
        msg_record_deleted = T("Role deleted"),
        msg_list_empty = T("No Roles defined"))

    s3db.configure(tablename, main="role")
    return s3_rest_controller("auth", resourcename)

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def organisation():
    """
        RESTful CRUD controller

        @ToDo: Prevent multiple records for the same domain
    """

    module = "auth"
    tablename = "auth_organisation"
    table = s3db[tablename]

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Organization Domain"),
        title_display = T("Organization Domain Details"),
        title_list = T("Organization Domains"),
        title_update = T("Edit Organization Domain"),
        title_search = T("Search Organization Domains"),
        subtitle_create = T("Add New Organization Domain"),
        label_list_button = T("List Organization Domains"),
        label_create_button = T("Add Organization Domain"),
        label_delete_button = T("Delete Organization Domain"),
        msg_record_created = T("Organization Domain added"),
        msg_record_modified = T("Organization Domain updated"),
        msg_record_deleted = T("Organization Domain deleted"),
        msg_list_empty = T("No Organization Domains currently registered")
    )

    output = s3_rest_controller(module, resourcename)

    return output

# -----------------------------------------------------------------------------
def user_create_onvalidation (form):
    """ Server-side check that Password confirmation field is valid """
    if (form.request_vars.has_key("password_two") and \
        form.request_vars.password != form.request_vars.password_two):
        form.errors.password = T("Password fields don't match")
    return True

# =============================================================================
@auth.s3_requires_membership(1)
def acl():
    """
        Preliminary controller for ACLs
        for testing purposes, not for production use!
    """

    module = "s3"
    name = "permission"

    table = auth.permission.table
    tablename = table._tablename
    table.group_id.requires = IS_ONE_OF(db, "auth_group.id", "%(role)s")
    table.group_id.represent = lambda opt: opt and db.auth_group[opt].role or opt

    table.controller.requires = IS_EMPTY_OR(IS_IN_SET(settings.modules.keys(),
                                                      zero="ANY"))
    table.controller.represent = lambda opt: opt and \
        "%s (%s)" % (opt,
                     auth.permission.modules.get(opt, {}).get("name_nice", opt)) or "ANY"

    table.function.represent = lambda val: val and val or T("ANY")

    table.tablename.requires = IS_EMPTY_OR(IS_IN_SET([t._tablename for t in db],
                                                     zero=T("ANY")))
    table.tablename.represent = lambda val: val and val or T("ANY")

    table.uacl.label = T("All Resources")
    table.uacl.widget = S3ACLWidget.widget
    table.uacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
    table.uacl.represent = lambda val: acl_represent(val,
                                                     auth.permission.PERMISSION_OPTS)

    table.oacl.label = T("Owned Resources")
    table.oacl.widget = S3ACLWidget.widget
    table.oacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
    table.oacl.represent = lambda val: acl_represent(val,
                                                     auth.permission.PERMISSION_OPTS)

    s3db.configure(tablename,
                   create_next = URL(r=request),
                   update_next = URL(r=request))

    if "_next" in request.vars:
        next = request.vars._next
        s3db.configure(tablename, delete_next=next)

    output = s3_rest_controller(module, name)
    return output

# -----------------------------------------------------------------------------
def acl_represent(acl, options):
    """
        Represent ACLs in tables
        for testing purposes, not for production use!
    """

    values = []

    for o in options.keys():
        if o == 0 and acl == 0:
            values.append("%s" % options[o][0])
        elif acl and acl & o == o:
            values.append("%s" % options[o][0])
        else:
            values.append("_")

    return " ".join(values)

# =============================================================================
# Ticket viewing
# =============================================================================
@auth.s3_requires_membership(1)
def ticket():
    """ Ticket handler """

    import traceback
    from gluon.restricted import RestrictedError

    if len(request.args) != 2:
        session.error = T("Invalid ticket")
        redirect(URL(r=request))

    app = request.args[0]
    ticket = request.args[1]
    e = RestrictedError()
    e.load(request, app, ticket)

    return dict(app=app,
                ticket=ticket,
                traceback=s3base.Traceback(e.traceback),
                code=e.code,
                layer=e.layer)

# -----------------------------------------------------------------------------
# Web2Py Ticket Viewer functions Borrowed from admin application of web2py
@auth.s3_requires_membership(1)
def errors():
    """ Error handler """

    from gluon.admin import apath
    from gluon.fileutils import listdir

    for item in request.vars:
        if item[:7] == "delete_":
            os.unlink(apath("%s/errors/%s" % (appname, item[7:]), r=request))

    func = lambda p: os.stat(apath("%s/errors/%s" % (appname, p), r=request)).st_mtime
    tickets = sorted(listdir(apath("%s/errors/" % appname, r=request), "^\w.*"),
                     key=func,
                     reverse=True)

    return dict(app=appname, tickets=tickets)

# =============================================================================
# Management scripts
# =============================================================================
@auth.s3_requires_membership(1)
def clean():
    """
        Run an external script to clean this instance & reset to default values

        visudo
        web2py ALL=(ALL)NOPASSWD:/usr/local/bin/clean
    """

    from subprocess import check_call

    instance = settings.get_instance_name()
    try:
        check_call(["sudo /usr/local/bin/clean %s" % instance], shell=True)
    except:
        import sys
        error = sys.exc_info()[1]
        status = current.xml.json_message(False, 400,
                                          "Script cannot be run: %s" % error)
        raise HTTP(400, body=status)

# =============================================================================
# Create portable app
# =============================================================================
@auth.s3_requires_membership(1)
def portable():
    """ Portable app creator"""

    from gluon.admin import apath
    import os
    from operator import itemgetter, attrgetter

    uploadfolder=os.path.join(apath("%s" % appname, r=request), "cache")
    web2py_source = None
    web2py_source_exists = False
    last_build_exists = False

    for base, dirs, files in os.walk(uploadfolder):
        for filename in files:
            if "web2py_source" in filename:
                web2py_source_exists = True
                web2py_source = filename
                break

    for base, dirs, files in os.walk(uploadfolder):
        for filename in files:
            if "download.zip" in filename:
                last_build_exists = True
                break

    web2py_form = SQLFORM.factory(
            Field("web2py_source",
                  "upload",
                  uploadfolder=uploadfolder,
                  requires=IS_UPLOAD_FILENAME(extension="zip"),
                ),
            table_name="web2py_source",
            )

    if web2py_form.accepts(request.vars, keepvalues=True, session=None):
        # Make sure only one web2py source file exists
        files_to_remove = {}
        for base, dirs, files in os.walk(uploadfolder):
            for filename in files:
                if "web2py_source" in filename:
                    files_to_remove[filename] = os.stat(os.path.join(uploadfolder, filename)).st_mtime
        sorted_files = sorted(files_to_remove.items(), key=itemgetter(1))
        for i in range(0, len(sorted_files) - 1): # 1 indicates leave one file
            os.remove(os.path.join(uploadfolder,sorted_files[i][0]))
        web2py_source = sorted_files[len(sorted_files) - 1][0]
        web2py_source_exists = True
        session.flash = T("Web2py executable zip file found - Upload to replace the existing file")
    else:
        # Lets throw an error message if this the zip file isn't found
        if not web2py_source_exists:
            session.error = T("Web2py executable zip file needs to be uploaded to use this function.")
        else:
            session.flash = T("Web2py executable zip file found - Upload to replace the existing file")

    generator_form = SQLFORM.factory(
            Field("copy_database", "boolean"),
            Field("copy_uploads", "boolean"),
            )

    if generator_form.accepts(request.vars, keepvalues=True, session=None):
        if web2py_source_exists:
            create_portable_app(web2py_source=web2py_source,\
                    copy_database = request.vars.copy_database,\
                    copy_uploads = request.vars.copy_uploads)
        else:
            session.error = T("Web2py executable zip file needs to be uploaded to use this function.")
    if last_build_exists:
        download_last_form = SQLFORM.factory()
        if download_last_form.accepts(request.vars, keepvalues=True, session=None):
            portable_app = os.path.join(cachedir, "download.zip")
            response.headers["Content-Type"] = contenttype.contenttype(portable_app)
            response.headers["Content-Disposition"] = \
                    "attachment; filename=portable-sahana.zip"
            return response.stream(portable_app)

    else:
        download_last_form = None
    return dict(
            web2py_form=web2py_form,
            generator_form=generator_form,
            download_last_form=download_last_form
        )

# -----------------------------------------------------------------------------
def create_portable_app(web2py_source, copy_database=False, copy_uploads=False):
    """Function to create the portable app based on the parameters"""

    from gluon.admin import apath
    import shutil,tempfile,os
    import zipfile
    import contenttype

    cachedir = os.path.join(apath("%s" % appname, r=request), "cache")
    tempdir = tempfile.mkdtemp("", "eden-", cachedir)
    workdir = os.path.join(tempdir, "web2py")
    if copy_uploads:
        ignore = shutil.ignore_patterns("*.db", "*.log", "*.table", "errors", "sessions", "compiled" , "cache", ".bzr", "*.pyc")
    else:
        ignore = shutil.ignore_patterns("*.db", "*.log", "*.table", "errors", "sessions", "compiled" , "uploads", "cache", ".bzr", "*.pyc")

    appdir = os.path.join(workdir, "applications", appname)
    shutil.copytree(apath("%s" % appname, r=request),\
                    appdir, \
                    ignore = ignore)
    os.mkdir(os.path.join(appdir, "errors"))
    os.mkdir(os.path.join(appdir, "sessions"))
    os.mkdir(os.path.join(appdir, "cache"))
    if not copy_uploads:
        os.mkdir(os.path.join(appdir, "uploads"))

    shutil.copy(os.path.join(appdir, "deployment-templates", "cron", "crontab"),\
            os.path.join(appdir, "cron", "crontab"))

    if copy_database:
        # Copy the db for the portable app
        s3db.load_all_models() # Load all modules to copy everything

        portable_db = DAL("sqlite://storage.db", folder=os.path.join(appdir, "databases"))
        for table in db:
            portable_db.define_table(table._tablename, *[field for field in table])

        portable_db.commit()

        temp_csv_file=tempfile.mkstemp()
        db.export_to_csv_file(open(temp_csv_file[1], "wb"))
        portable_db.import_from_csv_file(open(temp_csv_file[1], "rb"))
        os.unlink(temp_csv_file[1])
        portable_db.commit()

    # Replace the following with a more specific config
    config_template = open(os.path.join(appdir, "deployment-templates", "models", "000_config.py"), "r")
    new_config = open(os.path.join(appdir, "models", "000_config.py"), "w")
    # Replace first occurance of False with True
    new_config.write(config_template.read().replace("False", "True", 1))
    new_config.close()

    # Embedded the web2py source with eden for download
    shutil.copy(os.path.join(cachedir, web2py_source), os.path.join(cachedir, "download.zip"))
    portable_app = os.path.join(cachedir, "download.zip")
    zip = zipfile.ZipFile(portable_app, "a", zipfile.ZIP_DEFLATED)
    tozip = os.path.join(tempdir, "web2py")
    rootlen = len(tempdir) + 1

    for base, dirs, files in os.walk(tozip):
        for directory in dirs:
            directory = os.path.join(base, directory)
            zip.write(directory, directory[rootlen:]) # Create empty directories
        for file in files:
            fn = os.path.join(base, file)
            zip.write(fn, fn[rootlen:])

    zip.close()
    shutil.rmtree(tempdir)
    response.headers["Content-Type"] = contenttype.contenttype(portable_app)
    response.headers["Content-Disposition"] = \
                            "attachment; filename=portable-sahana.zip"

    return response.stream(portable_app)

# =============================================================================
# Translation Functionality
# =============================================================================
def translate():
    """
        Translation controller to enable four major workflows :-

        1) Select modules which require translation. The list of strings
           belonging to selected modules can be exported in .xls or .po format

        2) Upload csv file containing strings with their translations which
           are then merged with existing language file

        3) Display the percentage of translation for each module for a given
           language file

        4) Upload a text file containing a list of new-line separated strings
           which are to be considered for translation in the future. These
           strings are termed as "user-supplied" strings and are picked up by
           the first workflow when preparing the spreadsheet for translation

        Note : The above functionalities require a considerable amount of
               main memory to execute successfully.

        @ToDo: Move opts 1, 3 & 4 outside the REST Controller
               - only opt 2 makes use of this so it's unnecessary overhead!
    """

    opt = request.get_vars.get("opt", None)
    if not opt:
        # Show index page
        return dict()

    # For the one which actually uses CRUD (opt 2)
    s3.crud.submit_button = T("Upload")

    def postp(r, output):
        # Create a custom form
        form = FORM()

        # Prevent redirection
        r.next = None

        # Remove the false error from the form
        # error : "Invalid form (re-opened in another window?)"
        if response.error and not output["form"]["error"]:
            response.error = None

        if opt == "1":
            # Select modules for Translation
            from math import ceil
            from s3.s3translate import TranslateAPI, Strings
            if form.accepts(request.vars, session):
                modlist = []
                # If only one module is selected
                if type(form.request_vars.module_list) == str:
                    modlist.append(form.request_vars.module_list)
                # If multiple modules are selected
                else:
                    modlist = form.request_vars.module_list

                # If no module is selected
                if modlist is None:
                    modlist = []

                # If "Select All" option is chosen
                all_template_flag = 0
                if "all" in modlist:
                    all_template_flag = 1
                    A = TranslateAPI()
                    modlist = A.get_modules()
                    if "core" in form.request_vars.module_list:
                        modlist.append("core")

                # Obtaining the language file from the language code
                code = form.request_vars.new_code
                if code == "":
                    code = form.request_vars.code
                code += ".py"

                # Obtaining the type of file to export to
                filetype = form.request_vars.filetype

                # Generate the file to download
                X = Strings()
                output = X.export_file(code, modlist, [], filetype, all_template_flag)
                return output

            # Create a form with checkboxes for list of modules
            A = TranslateAPI()
            # Retrieve list of active modules
            activemodlist = settings.modules.keys()
            modlist = activemodlist
            # Hiding core modules
            hidden_modules = A.core_modules
            for module in hidden_modules:
                if module in modlist:
                    modlist.remove(module)
            modlist.sort()
            modcount = len(modlist)

            langlist = A.get_langcodes()
            langlist.sort()

            table = TABLE(_class="translation_module_table")
            table.append(BR())

            # Set number of columns in the form
            NO_OF_COLUMNS = 3

            # Display "NO_OF_COLUMNS" modules per row so as to utilize the page completely
            num = 0
            max_rows = int(ceil(modcount / float(NO_OF_COLUMNS)))
            modules = settings.modules
            while num < max_rows:
                check = "yes"
                mod_name = modules[modlist[num]].name_nice
                mod_name = "%s (%s)" %(mod_name, modlist[num])
                row = TR(TD(num + 1),
                         TD(INPUT(_type="checkbox", _name="module_list",
                                  _value=modlist[num], _checked = check)),
                         TD(mod_name),
                         )

                for c in range(1, NO_OF_COLUMNS):
                    cmax_rows = num + (c * max_rows)
                    if cmax_rows < modcount:
                        mod_name = modules[modlist[cmax_rows]].name_nice
                        mod_name = "%s (%s)" % (mod_name, modlist[cmax_rows])
                        row.append(TD(cmax_rows + 1))
                        row.append(TD(INPUT(_type="checkbox",
                                            _name="module_list",
                                            _value=modlist[cmax_rows],
                                            _checked = check)))
                        row.append(TD(mod_name))
                num += 1
                table.append(row)

            div = DIV(table,
                      BR(),
                      )
            row = TR(TD(INPUT(_type="checkbox", _name="module_list",
                              _value="core", _checked="yes")),
                     TD(T("Include core files")),
                     )
            div.append(row)
            div.append(BR())
            row = TR(TD(INPUT(_type="checkbox", _name="module_list",
                              _value="all")),
                     TD(T("Select all templates (All modules included)")),
                     )
            div.append(row)
            div.append(BR())

            # Provide option to choose export format
            row = TR(TD("%s:" % T("Export as")),
                     TD(INPUT(_type="radio", _name="filetype",
                            _value="xls", _checked="checked")),
                     TD(".xls (Excel)"),
                     TD(INPUT(_type="radio", _name="filetype", _value="po")),
                     TD(".po (Pootle)"),
                     BR(),
                     BR(),
                     )

            div.append(row)

            # Drop-down for available language codes
            lang_dropdown = SELECT(_name = "code")
            for lang in langlist:
                lang_dropdown.append(lang)

            row = TR(TD("%s:" % T("Select language code")),
                     TD(lang_dropdown),
                     TD("%s:" % T("Or add a new language code")),
                     TD(INPUT(_type="text", _name="new_code")),
                     )
            div.append(row)
            div.append(BR())
            div.append(BR())
            div.append(INPUT(_type="submit", _value=T("Submit")))
            form.append(div)
            # Add the custom form to the output
            output["form"] = form
            output["title"] = T("Select the required modules")

        elif opt == "2":
            # Upload translated files
            form = output["form"]
            div = DIV(BR(),
                      T("Note: Make sure that all the text cells are quoted in the csv file before uploading"),
                      )
            form.append(div)
            output["form"] = form

        elif opt == "3":
            # View Translation Percentage
            if form.accepts(request.vars, session):
                # Retrieve the translation percentage for each module
                from math import ceil
                from s3.s3translate import TranslateReportStatus
                code = form.request_vars.code
                S = TranslateReportStatus()

                if form.request_vars.update_master == "on":
                    S.create_master_file()

                percent_dict = S.get_translation_percentages(code)

                modlist = []
                for mod in sorted(percent_dict.keys()):
                    if mod != "complete_file":
                        modlist.append(mod)
                modcount = len(modlist)

                table = TABLE(_class="translation_module_table")
                table.append(BR())

                # Set number of columns in the table
                NO_OF_COLUMNS = 3

                # Display "NO_OF_COLUMNS" modules per row so as to utilize the page completely
                num = 0
                max_rows = int(ceil(modcount / float(NO_OF_COLUMNS)))

                while num < max_rows:
                    row = TR(TD(modlist[num]), TD(percent_dict[modlist[num]]))
                    for c in range(1, NO_OF_COLUMNS):
                        cmax_rows = num + (c * max_rows)
                        if cmax_rows < modcount:
                            row.append(TD(modlist[cmax_rows]))
                            row.append(TD(percent_dict[modlist[cmax_rows]]))
                    num += 1
                    table.append(row)

                # Add the table to output to display it
                div = DIV(table,
                          BR(),
                          TR(TD("Overall translation percentage of the file: "),
                             TD(percent_dict["complete_file"])),
                          )
                form.append(div)
                output["form"] = form
                output["title"] = T("Module-wise Percentage of Translated Strings")
                s3.has_required = False

            else:
                # Display the form to view translated percentage
                from s3.s3translate import TranslateAPI
                A = TranslateAPI()
                langlist = A.get_langcodes()
                langlist.sort()
                # Drop-down for selecting language codes
                lang_col = TD()
                lang_dropdown = SELECT(_name="code")
                for lang in langlist:
                    lang_dropdown.append(lang)
                lang_col.append(lang_dropdown)

                row = TR(TD("%s:" % T("Language Code")), TD(lang_col))
                div = DIV(row,
                          BR(),
                          )
                row = TR(TD(INPUT(_type="checkbox", _name="update_master")),
                         TD(T("Update Master file")))
                div.append(row)
                div.append(BR())
                div.append(BR())
                div.append(INPUT(_type="submit", _value=T("Submit")))
                form.append(div)
                # Add the custom form to the output
                output["title"] = T("Select the language file")
                output["form"] = form

        elif opt == "4":
            # Add strings manually
            if form.accepts(request.vars, session):
                # Retrieve strings from the uploaded file
                from s3.s3translate import TranslateReadFiles
                f = request.vars.upload.file
                strings = []
                R = TranslateReadFiles()
                for line in f:
                    strings.append(line)
                # Update the file containing user strings
                R.merge_user_strings_file(strings)
                response.confirmation = T("File uploaded")

            div = DIV(T("Upload a text file containing new-line separated strings:"),
                      INPUT(_type="file", _name="upload"),
                      BR(),
                      INPUT(_type="submit", _value=T("Upload")),
                      )
            form.append(div)
            output["form"] = form

        return output
    s3.postp = postp

    output = s3_rest_controller("translate", "language")
    return output

# =============================================================================
# Selenium Test Results
# =============================================================================
def result():
    """
        Selenium Test Result Reports list
    """

    file_list = UL()
    static_path = os.path.join(request.folder, "static", "test")
    for filename in os.listdir(static_path):
        link = A(filename,
                 _href = URL(c = "static",
                             f = "test",
                             args = [filename]
                             )
                 )
        file_list.append(link)
    return dict(file_list=file_list)

# -----------------------------------------------------------------------------
def result_automated():
    """
        Selenium Test Result Reports list
    """
    file_list_automated = UL()
    static_path = os.path.join(request.folder, "static", "test_automated")
    filenames = os.listdir(static_path)
    filenames.reverse()
    for filename in filenames:
        link = A(filename,
                 _href = URL(c = "static",
                             f = "test_automated",
                             args = [filename]
                             )
                 )
        file_list_automated.append(link)
    return dict(file_list_automated=file_list_automated)

# -----------------------------------------------------------------------------
def result_smoke():
    """
        Selenium Test Result Reports list
    """

    file_list_smoke = UL()
    static_path = os.path.join(request.folder, "static", "test_smoke")
    filenames = os.listdir(static_path)
    filenames.reverse()
    for filename in filenames:
        link = A(filename,
                 _href = URL(c = "static",
                             f = "test_smoke",
                             args = [filename]
                             )
                 )
        file_list_smoke.append(link)
    return dict(file_list_smoke=file_list_smoke)

# -----------------------------------------------------------------------------
def result_roles():
    """
        Selenium Test Result Reports list
    """

    file_list_roles = UL()
    static_path = os.path.join(request.folder, "static", "test_roles")
    filenames = os.listdir(static_path)
    filenames.reverse()
    for filename in filenames:
        link = A(filename,
                 _href = URL(c = "static",
                             f = "test_roles",
                             args = [filename]
                             )
                 )
        file_list_roles.append(link)
    return dict(file_list_roles=file_list_roles)

# END =========================================================================
