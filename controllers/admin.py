"""
    Admin Controllers
"""

def index():
    """ Module's Home Page """

    module_name = settings.modules["admin"].get("name_nice")
    response.title = module_name

    return {"module_name": module_name,
            }

# =============================================================================
@auth.requires_membership(1)
def setting():
    """
        Custom page to link to those Settings which can be edited through
        the web interface
    """

    return {}

# =============================================================================
# AAA
# =============================================================================
@auth.requires_membership(1)
def role():
    """ Role Manager """

    def prep(r):
        if r.representation not in ("html", "aadata", "csv", "json"):
            return False
        r.custom_action = s3base.S3RoleManager
        return True
    s3.prep = prep

    return crud_controller("auth", "group")

# -----------------------------------------------------------------------------
def user():
    """ RESTful CRUD controller """

    table = auth.settings.table_user
    s3_has_role = auth.s3_has_role

    UNAPPROVED = request.get_vars.get("unapproved")
    DISABLED = ("disabled", "blocked", "failed")

    # Check for ADMIN first since ADMINs have all roles
    ADMIN = False
    if s3_has_role("ADMIN"):
        ADMIN = True
        pe_ids = None

    elif auth.s3_has_roles(("ORG_ADMIN", "ORG_GROUP_ADMIN")):
        pe_ids = auth.permission.permitted_realms("auth_user", "update")
        if pe_ids:
            # Restricted to certain organisations
            otable = s3db.org_organisation
            s3.filter = (otable.pe_id.belongs(pe_ids)) & \
                        (table.organisation_id == otable.id)
        elif pe_ids is not None:
            # Not allowed for any organisations
            auth.permission.fail()
        else:
            # Allowed for all organisations
            pass
    else:
        auth.permission.fail()

    auth.configure_user_fields(pe_ids)

    # Configure list fields for user list
    list_fields = ["first_name",
                   "last_name",
                   "email",
                   ]
    lappend = list_fields.append
    if len(settings.get_L10n_languages()) > 1:
        lappend("language")
    if ADMIN:
        if settings.get_auth_admin_sees_organisation():
            lappend("organisation_id")
    elif settings.get_auth_registration_requests_organisation():
        lappend("organisation_id")
    if settings.get_auth_registration_requests_organisation_group():
        lappend("org_group_id")
    if settings.get_auth_registration_requests_site():
        lappend("site_id")
    link_user_to = settings.get_auth_registration_link_user_to()
    if link_user_to and len(link_user_to) > 1 and settings.get_auth_show_link():
        lappend("link_user_to")
        table.link_user_to.represent = lambda v: ", ".join([s3_str(link_user_to[opt]) for opt in v]) \
                                                 if v else messages["NONE"]
    date_represent = s3base.S3DateTime.date_represent
    table.created_on.represent = date_represent
    if UNAPPROVED:
        lappend((T("Registration"), "created_on"))
    else:
        table.timestmp.represent = date_represent
        list_fields += [(T("Roles"), "membership.group_id"),
                        (T("Registration"), "created_on"),
                        (T("Last Login"), "timestmp"),
                        ]

    s3db.configure("auth_user",
                   create_next = URL(c="admin", f="user",
                                     args = ["[id]", "roles"],
                                     ),
                   create_onaccept = lambda form: \
                                        auth.s3_approve_user(form.vars),
                   list_fields = list_fields,
                   main = "first_name",
                   #update_onaccept = lambda form: auth.s3_link_user(form.vars),
                   )

    # Configure methods for user accounts
    set_method = s3db.set_method
    set_method("auth_user", method="roles", action = s3base.S3RoleManager)
    set_method("auth_user", method="disable", action=s3base.ManageUserAccount)
    set_method("auth_user", method="enable", action=s3base.ManageUserAccount)
    set_method("auth_user", method="approve", action=s3base.ManageUserAccount)
    set_method("auth_user", method="link", action=s3base.ManageUserAccount)

    # CRUD Strings
    title_list = T("Unapproved Users") if UNAPPROVED else T("Users")
    s3.crud_strings["auth_user"] = Storage(
        label_create = T("Create User"),
        title_display = T("User Details"),
        title_list = title_list,
        title_update = T("Edit User"),
        title_upload = T("Import Users"),
        label_list_button = T("List Users"),
        label_delete_button = T("Delete User"),
        msg_record_created = T("User added"),
        msg_record_modified = T("User updated"),
        msg_record_deleted = T("User deleted"),
        msg_list_empty = T("No Users currently registered"),
        )

    def rheader(r):
        if r.representation != "html" or not r.record:
            return None

        rheader = DIV()

        id = r.id
        registration_key = r.record.registration_key
        if not registration_key:
            btn = A(T("Disable"),
                    _class = "action-btn",
                    _title = "Disable User",
                    _href = URL(args = [id, "disable"])
                    )
            rheader.append(btn)
            if settings.get_auth_show_link():
                btn = A(T("Link"),
                        _class = "action-btn",
                        _title = "Link (or refresh link) between User, Person & HR Record",
                        _href = URL(args = [id, "link"])
                        )
                rheader.append(btn)
        #elif registration_key == "pending":
        #    btn = A(T("Approve"),
        #            _class = "action-btn",
        #            _title = "Approve User",
        #            _href = URL(args = [id, "approve"])
        #            )
        #    rheader.append(btn)
        else:
            # Verify & Approve
            btn = A(T("Approve"),
                    _class = "action-btn",
                    _title = "Approve User",
                    _href = URL(args = [id, "approve"])
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

        if UNAPPROVED:
            registration_key = FS("registration_key")
            query = (~(registration_key.belongs(DISABLED))) & \
                    (registration_key != None) & \
                    (registration_key != "")
            r.resource.add_filter(query)
        #else:
        #    # Add some highlighting to the rows
        #    query = (table.registration_key.belongs(["disabled", "pending"]))
        #    rows = db(query).select(table.id,
        #                            table.registration_key,
        #                            )
        #    disabled_rows = [str(row.id) for row in rows if row.registration_key == "disabled"]
        #    pending_rows = [str(row.id) for row in rows if row.registration_key == "pending"]
        #    s3.dataTableStyle = {
        #        "dtdisable": disabled_rows,
        #        "dtalert": pending_rows,
        #        }

        if r.interactive:
            s3db.configure(r.tablename,
                           addbtn = True,
                           # Password confirmation
                           create_onvalidation = user_create_onvalidation,
                           deletable = False,
                           # jquery.validate is clashing with dataTables so don't embed the create form in with the List
                           listadd = False,
                           sortby = [[2, "asc"], [1, "asc"]],
                           )

        elif r.representation in ("xlsx", "xls"):
            lappend((T("Status"), "registration_key"))

        if r.method == "delete" and r.http == "GET":
            if r.id == session.auth.user.id: # we're trying to delete ourself
                get_vars.update({"user.id":str(r.id)})
                r.id = None
                s3db.configure(r.tablename,
                               delete_next = URL(c="default", f="user/logout"),
                               )
                s3.crud.confirm_delete = T("You are attempting to delete your own account - are you sure you want to proceed?")

        if r.http == "GET" and not r.method:
            session.s3.cancel = r.url()

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and isinstance(output, dict) and \
           r.method in (None, "update", "create"):
            actions = [{"label": s3_str(messages.UPDATE),
                        "url": URL(c="admin", f="user",
                                   args = ["[id]", "update"],
                                   ),
                        "_class": "action-btn",
                        },
                       ]


            if UNAPPROVED:
                # Always show the Approve button
                actions.append({"label": str(T("Approve")),
                                "url": URL(c="admin", f="user",
                                           args = ["[id]", "approve"],
                                           ),
                                "_class": "action-btn",
                                })

            else:
                # Add a button to go direct to the Roles tab
                actions.append({"label": s3_str(T("Roles")),
                                "url": URL(c="admin", f="user",
                                           args = ["[id]", "roles"],
                                           ),
                                "_class": "action-btn",
                                })

                # Only show the disable button if the user is not currently disabled
                table = r.table
                query = (table.registration_key.belongs(DISABLED)) & \
                        (table.deleted == False)
                rows = db(query).select(table.id)
                disabled = [str(row.id) for row in rows]

                actions.append({"label": str(T("Re-enable")),
                                "restrict": disabled,
                                "url": URL(c="admin", f="user",
                                           args = ["[id]", "enable"],
                                           ),
                                "_class": "action-btn",
                                })

                actions.append({"label": str(T("Disable")),
                                "exclude": disabled,
                                "url": URL(c="admin", f="user",
                                           args = ["[id]", "disable"],
                                           ),
                                "_class": "action-btn",
                                })

                if settings.get_auth_show_link():
                    actions.insert(1, {"label": s3_str(T("Link")),
                                       "exclude": disabled,
                                       "url": URL(c="admin", f="user",
                                                  args = ["[id]", "link"],
                                                  ),
                                       "_class": "action-btn",
                                       "_title": s3_str(T("Link (or refresh link) between User, Person & HR Record")),
                                       }
                                   )
                # Only show the approve button if the user is currently pending
                query = (~(table.registration_key.belongs(DISABLED))) & \
                        (table.registration_key != None) & \
                        (table.registration_key != "")
                rows = db(query).select(table.id)
                restrict = [str(row.id) for row in rows]
                actions.append({"label": str(T("Approve")),
                                "restrict": restrict,
                                "url": URL(c="admin", f="user",
                                           args = ["[id]", "approve"],
                                           ),
                                "_class": "action-btn",
                                })

            s3.actions = actions

            # @ToDo: Merge these with the code in s3aaa.py and use CustomForm to implement
            form = output.get("form", None)
            if not form:
                crud_button = s3base.BasicCRUD.crud_button
                if UNAPPROVED:
                    switch_view = crud_button(T("View All Users"),
                                              _href = URL(vars = {}),
                                              )
                elif settings.get_auth_registration_requires_approval():
                    switch_view = crud_button(T("View Unapproved Users"),
                                              _href = URL(vars = {"unapproved": 1}),
                                              )
                else:
                    switch_view = ""
                if not s3db.get_config("auth_user", "insertable") == False:
                    output["showadd_btn"] = DIV(crud_button(T("Create User"),
                                                            _href = URL(args = ["create"]),
                                                            ),
                                                crud_button(T("Import Users"),
                                                            _href = URL(args = ["import"]),
                                                            ),
                                                switch_view,
                                                )
                return output

            # Assume formstyle callable
            id = "auth_user_password_two__row"
            label = "%s:" % T("Verify password")
            widget = INPUT(_name = "password_two",
                           _id = "password_two",
                           _type = "password",
                           _disabled = "disabled",
                           )
            comment = ""
            row = s3_formstyle(id, label, widget, comment, hidden=True)
            if isinstance(row, tuple):
                # Formstyle with separate row for label (e.g. default Eden formstyle)
                tuple_rows = True
                form[0].insert(8, row)
            else:
                # Formstyle with just a single row (e.g. Foundation)
                tuple_rows = False
                form[0].insert(4, row)
            # @ToDo: Ensure this reads existing values & creates/updates when saved
            #if settings.get_auth_registration_requests_mobile_phone():
            #    id = "auth_user_mobile__row"
            #    label = LABEL("%s:" % settings.get_ui_label_mobile_phone(),
            #                  _for="mobile",
            #                  )
            #    widget = INPUT(_name="mobile",
            #                   _id="auth_user_mobile",
            #                   _class="string",
            #                   )
            #    comment = ""
            #    row = s3_formstyle(id, label, widget, comment)
            #    if tuple_rows:
            #        form[0].insert(-8, row)
            #    else:
            #        form[0].insert(-4, row)

            # Add client-side validation
            auth.s3_register_validation()

        return output
    s3.postp = postp

    s3.import_prep = auth.s3_import_prep

    return crud_controller("auth", "user",
                           csv_stylesheet = ("auth", "user.xsl"),
                           csv_template = ("auth", "user"),
                           rheader = rheader,
                           )

# =============================================================================
def group():
    """
        RESTful CRUD controller
        - used by role_required autocomplete
    """

    tablename = "auth_group"

    if not auth.s3_has_role("ADMIN"):
        s3db.configure(tablename,
                       deletable = False,
                       editable = False,
                       insertable = False,
                       )

    # CRUD Strings
    ADD_ROLE = T("Create Role")
    s3.crud_strings[tablename] = Storage(
        label_create = ADD_ROLE,
        title_display = T("Role Details"),
        title_list = T("Roles"),
        title_update = T("Edit Role"),
        label_list_button = T("List Roles"),
        msg_record_created = T("Role added"),
        msg_record_modified = T("Role updated"),
        msg_record_deleted = T("Role deleted"),
        msg_list_empty = T("No Roles defined"),
        )

    s3db.configure(tablename, main="role")
    return crud_controller("auth", "group")

# -----------------------------------------------------------------------------
@auth.requires_membership(1)
def organisation():
    """
        RESTful CRUD controller

        @ToDo: Prevent multiple records for the same domain
    """

    tablename = "auth_organisation"
    table = s3db[tablename]

    s3.crud_strings[tablename] = Storage(
        label_create = T("Add Organization Domain"),
        title_display = T("Organization Domain Details"),
        title_list = T("Organization Domains"),
        title_update = T("Edit Organization Domain"),
        label_list_button = T("List Organization Domains"),
        label_delete_button = T("Delete Organization Domain"),
        msg_record_created = T("Organization Domain added"),
        msg_record_modified = T("Organization Domain updated"),
        msg_record_deleted = T("Organization Domain deleted"),
        msg_list_empty = T("No Organization Domains currently registered")
        )

    return crud_controller("auth", "organisation")

# -----------------------------------------------------------------------------
def user_create_onvalidation (form):
    """ Server-side check that Password confirmation field is valid """
    if ("password_two" in form.request_vars and \
        form.request_vars.password != form.request_vars.password_two):
        form.errors.password = T("Password fields don't match")
    return True

# =============================================================================
# Audit
#
@auth.requires_membership(1)
def audit():
    """ Audit Logs: RESTful CRUD Controller """

    # Ensure table is visible
    settings.security.audit_write = True
    from core import S3Audit
    S3Audit().__init__()

    # Represent the user_id column
    db.s3_audit.user_id.represent = s3db.auth_UserRepresent()

    return crud_controller("s3", "audit")

# =============================================================================
@auth.requires_membership(1)
def event():
    """
        CRUD controller for Auth event log
    """

    def prep(r):

        from core import S3DateTime

        table = auth.settings.table_event

        field = table.time_stamp
        field.represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

        field = table.user_id
        field.represent = auth.user_represent

        list_fields = ["time_stamp", "user_id", "description"]

        s3db.configure(table,
                       insertable = False,
                       editable = False,
                       deletable = False,
                       list_fields = list_fields,
                       orderby = ~table.time_stamp,
                       )

        s3.crud_strings[auth.settings.table_event_name] = Storage(
            title_display = T("Logged Event"),
            title_list = T("Logged Events"),
            label_list_button = T("List Events"),
            msg_list_empty = T("No Events currently registered"),
            )

        return True
    s3.prep = prep

    return crud_controller("auth", "event")

# =============================================================================
# Consent Tracking
#
@auth.requires_membership(1)
def processing_type():
    """ Types of Data Processing: RESTful CRUD Controller """

    return crud_controller("auth", "processing_type",
                           csv_template = ("auth", "processing_type"),
                           csv_stylesheet = ("auth", "processing_type.xsl"),
                           )

# -----------------------------------------------------------------------------
@auth.requires_membership(1)
def consent_option():
    """ Consent Options: RESTful CRUD Controller """

    ctable = s3db.auth_consent
    atable = s3db.auth_consent_assertion

    def prep(r):

        resource = r.resource
        table = resource.table

        editable = True
        if r.record:
            # Make hash-fields writable only when not referenced by any
            # consent / consent assertion record
            for t in (ctable, atable):
                query = (t.option_id == r.id) & (t.deleted == False)
                row = db(query).select(t.id, limitby=(0, 1)).first()
                if row:
                    editable = False
                    break
        if editable:
            for fn in s3db.auth_consent_option_hash_fields:
                table[fn].writable = True
        else:
            # Prevent deletion when referenced in a consent
            # or consent assertion record
            resource.configure(deletable=False)

        return True
    s3.prep = prep

    def postp(r, output):

        if not r.record:
            # No delete-button by default
            s3_action_buttons(r, deletable=False)

            # Add delete-button only for options not yet referenced
            # by any consent / consent assertion record:
            table = r.table
            left = [ctable.on((ctable.option_id == table.id) & \
                              (ctable.deleted == False)),
                    atable.on((atable.option_id == table.id) & \
                              (atable.deleted == False)),
                    ]
            ccount = ctable.id.count()
            acount = atable.id.count()
            rows = db(table.deleted == False).select(table.id,
                                                     ccount,
                                                     acount,
                                                     groupby = table.id,
                                                     having = (ccount == 0) & (acount == 0),
                                                     left = left,
                                                     )
            deletable = [str(row.auth_consent_option.id) for row in rows]
            s3.actions.append({"label": s3_str(T("Delete")),
                               "restrict": deletable,
                               "url": URL(args = ["[id]", "delete"]),
                               "_class": "action-btn delete-btn",
                               })
        return output
    s3.postp = postp

    return crud_controller("auth", "consent_option",
                           csv_template = ("auth", "consent_option"),
                           csv_stylesheet = ("auth", "consent_option.xsl"),
                           )

# =============================================================================
@auth.requires_membership(1)
def consent():

    return crud_controller("auth", "consent")

# =============================================================================
# Ticket viewing
# - web2Py ticket viewer functions borrowed from admin application of web2py
#
@auth.requires_membership(1)
def errors():
    """ Error ticket list """

    from gluon.admin import apath
    from gluon.fileutils import listdir

    for item in request.vars:
        if item[:7] == "delete_":
            os.unlink(apath("%s/errors/%s" % (appname, item[7:]), r=request))

    func = lambda p: os.stat(apath("%s/errors/%s" % (appname, p), r=request)).st_mtime
    tickets = sorted(listdir(apath("%s/errors/" % appname, r=request), r"^\w.*"),
                     key=func,
                     reverse=True)

    return {"app": appname,
            "tickets": tickets,
            }

# -----------------------------------------------------------------------------
@auth.requires_membership(1)
def ticket():
    """ Ticket viewer """

    if len(request.args) != 2:
        session.error = T("Invalid ticket")
        redirect(URL(r=request))

    app = request.args[0]
    ticket = request.args[1]

    from gluon.restricted import RestrictedError
    e = RestrictedError()
    e.load(request, app, ticket)

    return {"app": app,
            "ticket": ticket,
            "traceback": s3base.Traceback(e.traceback),
            "code": e.code,
            "layer": e.layer,
            }

# =============================================================================
# Create portable app
# =============================================================================
@auth.requires_membership(1)
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
            os.remove(os.path.join(uploadfolder, sorted_files[i][0]))
        web2py_source = sorted_files[len(sorted_files) - 1][0]
        web2py_source_exists = True
        session.flash = T("Web2py executable zip file found - Upload to replace the existing file")
    else:
        # Lets throw an error message if this the zip file isn't found
        if not web2py_source_exists:
            session.error = T("Web2py executable zip file needs to be uploaded to use this function.")
        else:
            session.flash = T("Web2py executable zip file found - Upload to replace the existing file")

    # Since the 2nd form depends on having uploaded the zip
    # in order to work we only show it if the upload was successfully
    # completed.

    if web2py_source_exists:
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
                session.error = T("Web2py executable zip file needs to be uploaded first to use this function.")
    else:
        generator_form = None

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

    return {"web2py_form": web2py_form,
            "generator_form": generator_form,
            "download_last_form": download_last_form,
            }

# -----------------------------------------------------------------------------
def create_portable_app(web2py_source, copy_database=False, copy_uploads=False):
    """Function to create the portable app based on the parameters"""

    import contenttype
    import os
    import shutil
    import tempfile
    import zipfile

    from gluon.admin import apath

    cachedir = os.path.join(apath("%s" % appname, r=request), "cache")
    tempdir = tempfile.mkdtemp("", "eden-", cachedir)
    workdir = os.path.join(tempdir, "web2py")
    if copy_uploads:
        ignore = shutil.ignore_patterns("*.db", "*.log", "*.table", "errors", "sessions", "compiled", "cache", ".bzr", "*.pyc")
    else:
        ignore = shutil.ignore_patterns("*.db", "*.log", "*.table", "errors", "sessions", "compiled", "uploads", "cache", ".bzr", "*.pyc")

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
@auth.requires_membership(1)
def task():
    """
        Scheduler tasks: RESTful CRUD controller
    """

    s3db.add_components("scheduler_task",
                        scheduler_run = "task_id",
                        )
    def prep(r):

        if r.component_name == "run":

            component = r.component

            ctable = component.table

            field = ctable.traceback
            from core import s3_text_represent
            field.represent = s3_text_represent

            component.configure(insertable = False,
                                editable = False,
                                )

        s3task.configure_tasktable_crud(status_writable=True)
        return True
    s3.prep = prep

    return crud_controller("scheduler", "task",
                           rheader = s3db.s3_scheduler_rheader,
                           )

# =============================================================================
def result():
    """
        Selenium Test Result Reports
    """

    args = request.args
    result_type = args[0] if len(args) else None

    result_types = {"automated": "Automated Tests",
                    "roles": "Roles Test",
                    "smoke": "Smoke Test",
                    }

    if result_type in result_types:

        title = T(result_types[result_type])
        overview = False

        foldername = "test_%s" % result_type
        path = os.path.join(request.folder, "static", foldername)
        try:
            filenames = os.listdir(path)
        except OSError:
            links = UL(LI(T("No test results found"), _class="error"))
        else:
            links = UL()
            for filename in filenames:
                link = LI(A(filename,
                            _href = URL(c = "static",
                                        f = foldername,
                                        args = [filename]
                                        ),
                            _target = "_blank",
                            )
                          )
                links.append(link)
    else:

        title = T("Test Results Overview")
        overview = True

        links = UL()
        for name, label in result_types.items():
            link = LI(A(label,
                        _href = URL(c = "admin",
                                    f = "result",
                                    args = [name]
                                    )
                        )
                      )
            links.append(link)

    output = {"title": title,
              "links": links,
              "overview": overview,
              }

    return output

# =============================================================================
# Configurations
# =============================================================================
def dashboard():
    """
        Dashboard Configurations
    """

    return crud_controller("s3", "dashboard")

# END =========================================================================
