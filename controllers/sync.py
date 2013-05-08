# -*- coding: utf-8 -*-

""" Synchronization Controllers """

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = T("Synchronization")

    response.title = module_name
    return dict(module_name=module_name)

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

    # Can't do anything else than update here
    r = s3_request(args=[str(record_id), "update"], extension="html")

    return r(list_btn=None)

# -----------------------------------------------------------------------------
def repository():
    """ Repository Management Controller """

    tabs = [(T("Configuration"), None),
            (T("Resources"), "task"),
            (T("Schedule"), "job"),
            (T("Log"), "log")
           ]

    s3db.set_method("sync", "repository",
                    method="register", action=current.sync)

    crud_form = s3base.S3SQLCustomForm("resource_name",
                                       "last_pull",
                                       "last_push",
                                       "mode",
                                       "strategy",
                                       "update_method",
                                       "update_policy",
                                       "conflict_policy",
                                       s3base.S3SQLInlineComponent(
                                             "resource_filter",
                                             label = T("Filters"),
                                             fields = ["tablename",
                                                       "filter_string",
                                                      ]
                                       ),
                                      )
    s3db.configure("sync_task", crud_form=crud_form)

    def prep(r):
        if r.interactive:
            if r.component and r.id:
                if r.component.alias == "job":
                    s3task.configure_tasktable_crud(
                        function="sync_synchronize",
                        args = [r.id],
                        vars = dict(user_id = auth.user is not None and auth.user.id or 0),
                        period = 600, # seconds, so 10 mins
                        )
                s3.cancel = URL(c="sync", f="repository",
                                args=[str(r.id), r.component.alias])
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and r.id:
            if r.component and r.component.alias == "job":
                s3.actions = [
                    dict(label=str(T("Reset")),
                         _class="action-btn",
                         url=URL(c="sync", f="repository",
                                 args=[str(r.id), "job", "[id]", "reset"]))
                    ]
        s3_action_buttons(r)
        return output
    s3.postp = postp

    rheader = lambda r: s3db.sync_rheader(r, tabs=tabs)
    return s3_rest_controller("sync", "repository", rheader=rheader)

# -----------------------------------------------------------------------------
def sync():
    """ Synchronization """

    if "resource" in request.get_vars:
        tablename = request.get_vars["resource"]
        if "_" in tablename:

            # URL variables from peer:
            # repository ID, msince and sync filters
            get_vars = Storage(include_deleted=True)
            
            _vars = request.get_vars
            for k, v in _vars.items():
                if k in ("repository", "msince") or \
                   k[0] == "[" and "]" in k:
                    get_vars[k] = v

            # Request
            prefix, name = tablename.split("_", 1)
            r = s3_request(prefix=prefix,
                           name=name,
                           args=["sync"],
                           get_vars=get_vars)

            # Response
            output = r()
            return output

    raise HTTP(400, body=s3mgr.ERROR.BAD_REQUEST)

# -----------------------------------------------------------------------------
def log():
    """ Log Reader """

    if "return" in request.get_vars:
        c, f = request.get_vars["return"].split(".", 1)
        list_btn = URL(c=c, f=f, args="sync_log")
    else:
        list_btn = URL(c="sync", f="log", vars=request.get_vars)

    list_btn = A(T("List all Entries"), _href=list_btn, _class="action-btn")

    output = s3_rest_controller("sync", "log",
                                subtitle=None,
                                rheader=s3base.S3SyncLog.rheader,
                                list_btn=list_btn)
    return output

# END =========================================================================
