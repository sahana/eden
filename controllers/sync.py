# -*- coding: utf-8 -*-

""" Synchronization Controllers """

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = T("Synchronization")

    response.title = module_name
    return {"module_name": module_name,
            }

# -----------------------------------------------------------------------------
def config():
    """ Synchronization Settings Controller """

    # Get the record ID of the first and only record
    table = s3db.sync_config
    record = db().select(table.id, limitby=(0, 1)).first()
    if not record:
        record_id = table.insert()
    else:
        record_id = record.id

    def postp(r, output):
        if isinstance(output, dict) and "buttons" in output:
            output["buttons"].pop("list_btn", None)
        return output
    s3.postp = postp

    # Can't do anything else than update here
    r = s3_request(args=[str(record_id), "update"], extension="html")
    return r()

# -----------------------------------------------------------------------------
def repository():
    """ Repository Management Controller """

    s3db.set_method("sync", "repository",
                    method = "register",
                    action = current.sync,
                    )

    def prep(r):
        if r.interactive:

            if not r.component:

                # Make the UUID field editable in the form
                field = r.table.uuid
                field.label = "UUID"
                field.readable = True
                field.writable = True
                field.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (
                                           T("Repository UUID"),
                                           T("Identifier which the remote site uses to authenticate at this site when sending synchronization requests."),
                                           ),
                                    )

                # Inject script to show/hide relevant fields depending
                # on the API type selected:
                script = "s3.sync.js" if s3.debug else "s3.sync.min.js"
                path = "/%s/static/scripts/S3/%s" % (appname, script)
                if path not in s3.scripts:
                    s3.scripts.append(path)

            elif r.id:

                alias = r.component.alias
                if alias == "task":
                    # Configure custom CRUD form
                    apitype = r.record.apitype
                    if apitype == "eden":
                        components = "components"
                        infile_pattern = None
                        outfile_pattern = None
                        human_readable = None
                        delete_input_files = None
                    elif apitype == "filesync":
                        components = None
                        component_table = r.component.table
                        for fname in ("infile_pattern",
                                      "outfile_pattern",
                                      "human_readable",
                                      "delete_input_files",
                                      ):
                            field = component_table[fname]
                            field.readable = field.writable = True
                        infile_pattern = "infile_pattern"
                        outfile_pattern = "outfile_pattern"
                        human_readable = "human_readable"
                        delete_input_files = "delete_input_files"
                    else:
                        components = None
                        infile_pattern = None
                        outfile_pattern = None
                        human_readable = None
                        delete_input_files = None

                    crud_form = s3base.S3SQLCustomForm(
                                    "resource_name",
                                    components,
                                    infile_pattern,
                                    delete_input_files,
                                    outfile_pattern,
                                    human_readable,
                                    "last_pull",
                                    "last_push",
                                    "mode",
                                    "strategy",
                                    #"update_method",
                                    "update_policy",
                                    "conflict_policy",
                                    s3base.S3SQLInlineComponent(
                                        "resource_filter",
                                        label = T("Filters"),
                                        fields = ["tablename",
                                                  "filter_string",
                                                  ],
                                        ),
                                    )

                    list_fields = ["resource_name",
                                   "mode",
                                   "last_pull",
                                   "last_push",
                                   "strategy",
                                   "update_policy",
                                   "conflict_policy",
                                   ]

                    s3db.configure("sync_task",
                                   crud_form = crud_form,
                                   list_fields = list_fields,
                                   )

                elif alias == "job":
                    # Configure sync-specific defaults for scheduler_task table
                    s3task.configure_tasktable_crud(
                        function="sync_synchronize",
                        args = [r.id],
                        vars = {"user_id": auth.user.id if auth.user else 0},
                        period = 600, # seconds, so 10 mins
                    )

                elif alias == "log" and r.component_id:
                    table = r.component.table
                    table.message.represent = lambda msg: \
                                                DIV(s3base.s3_strip_markup(msg),
                                                    _class="message-body",
                                                    )

                elif alias == "dataset":

                    table = r.component.table
                    tablename = r.component.tablename

                    # Adapt CRUD strings to perspective
                    s3.crud_strings[tablename].update(
                       label_create = T("Add Data Set"),
                       title_list = T("Data Sets"),
                       label_list_button = T("List Data Sets"),
                       msg_record_created = T("Data Set added"),
                       msg_list_empty = T("No Data Sets currently registered"),
                    )

                    # Allow the same data set code only once per repository
                    field = table.code
                    field.requires = s3db.sync_dataset_code_requires + \
                                     [IS_NOT_ONE_OF(db(table.repository_id == r.id),
                                        "sync_dataset.code",
                                        error_message = "Code already registered for this repository",
                                        ),
                                      ]

                s3.cancel = URL(c = "sync",
                                f = "repository",
                                args = [str(r.id), alias],
                                )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and r.id:
            if r.component and r.component.alias == "job":
                s3.actions = [{"label": s3_str(T("Reset")),
                               "url": URL(c = "sync",
                                          f = "repository",
                                          args = [str(r.id),
                                                  "job",
                                                  "[id]",
                                                  "reset",
                                                  ],
                                          ),
                               "_class": "action-btn",
                               }
                              ]
        s3_action_buttons(r)
        return output
    s3.postp = postp

    return s3_rest_controller("sync", "repository", rheader=s3db.sync_rheader)

# -----------------------------------------------------------------------------
def dataset():
    """ Public Data Sets: RESTful CRUD controller """

    def prep(r):

        resource = r.resource

        # Filter to locally hosted data sets
        resource.add_filter(FS("repository_id") == None)

        if not r.component:

            table = resource.table

            if r.interactive:
                # Require code to be unique among exposed data sets
                field = table.code
                field.requires = s3db.sync_dataset_code_requires + \
                                 [IS_NOT_ONE_OF(db(table.repository_id == None),
                                    "sync_dataset.code",
                                    error_message = "Code already in use",
                                    ),
                                  ]

            # Name is required for locally hosted data sets
            field = table.name
            field.requires = IS_NOT_EMPTY()

        if r.record and r.component_name == "task":

            table = r.component.table

            # Default sync mode PULL
            field = table.mode
            field.default = 1

            # TODO adapt tooltips to context

            # Reduced form
            crud_form = s3base.S3SQLCustomForm(
                            "resource_name",
                            "components",
                            s3base.S3SQLInlineComponent(
                                "resource_filter",
                                label = T("Filters"),
                                fields = ["tablename",
                                          "filter_string",
                                          ],
                                ),
                            )

            # Reduced list fields
            list_fields = ["resource_name",
                           ]

            s3db.configure("sync_task",
                           crud_form = crud_form,
                           list_fields = list_fields,
                           )
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.sync_rheader)

# -----------------------------------------------------------------------------
def sync():
    """ Synchronization """

    tablename = get_vars.get("resource")
    if not tablename or tablename == "mixed":
        # Sync adapter to determine/negotiate the resource(s)
        mixed = True
        tablename = "sync_repository"
    else:
        # Resource determined by request
        mixed = False

    if tablename and "_" in tablename:

        get_vars_new = Storage(include_deleted=True)

        # Copy URL variables from peer:
        # repository ID, msince and sync filters
        for k, v in get_vars.items():
            if k in ("repository", "msince") or \
               k[0] == "[" and "]" in k:
                get_vars_new[k] = v

        # Request
        prefix, name = tablename.split("_", 1)
        r = s3_request(prefix = prefix,
                       name = name,
                       args = ["sync"],
                       get_vars = get_vars_new,
                       )

        # Response
        return r(mixed=mixed)

    raise HTTP(400, body=current.ERROR.BAD_REQUEST)

# -----------------------------------------------------------------------------
def log():
    """ Log Reader """

    if "return" in get_vars:
        c, f = get_vars["return"].split(".", 1)
        list_btn = URL(c=c, f=f, args="sync_log")
    else:
        list_btn = URL(c="sync", f="log", vars=get_vars)

    list_btn = A(T("List all Entries"), _href=list_btn, _class="action-btn")

    def prep(r):
        if r.record:
            r.table.message.represent = lambda msg: \
                                            DIV(s3base.s3_strip_markup(msg),
                                                _class="message-body",
                                                )
        return True
    s3.prep = prep

    return s3_rest_controller("sync", "log",
                              subtitle=None,
                              rheader=s3base.S3SyncLog.rheader,
                              list_btn=list_btn,
                              )

# -----------------------------------------------------------------------------
def task():
    """ Sync Tasks: RESTful CRUD controller """

    def prep(r):

        # Only XML and S3JSON formats allowed
        if r.representation not in ("s3json", "xml"):
            r.error(415, current.ERROR.BAD_FORMAT)

        # Limit to local public data sets
        # (=do not expose repositories and corresponding credentials)
        r.resource.add_filter(FS("repository_id") == None)

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def resource_filter():
    """ Sync Resource Filters: RESTful CRUD controller """

    def prep(r):

        # Only XML and S3JSON formats allowed
        if r.representation not in ("s3json", "xml"):
            r.error(415, current.ERROR.BAD_FORMAT)

        # Limit to local public data sets
        # (=do not expose repositories and corresponding credentials)
        r.resource.add_filter(FS("task_id$repository_id") == None)

        return True
    s3.prep = prep

    return s3_rest_controller()

# END =========================================================================
