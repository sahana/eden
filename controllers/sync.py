# -*- coding: utf-8 -*-

"""
    Synchronisation, Controllers

    @author: Dominic König <dominic[at]aidiq[dot]com>
"""

module = request.controller
prefix = "sync" # common table prefix
module_name = T("Synchronization")

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def config():
    """ Synchronization Settings Controller """

    resourcename = "config"

    # Get the record ID of the first and only record
    table = s3db.sync_config
    record = db().select(table.id, limitby=(0, 1)).first()
    if not record:
        record_id = table.insert()
    else:
        record_id = record.id

    # Can't do anything else than update here
    r = s3mgr.parse_request(args=[str(record_id), "update"],
                            extension="html")

    output = r(list_btn=None)
    return output

# -----------------------------------------------------------------------------
def repository():
    """ Repository Management Controller """

    resourcename = "repository"

    tabs = [(T("Configuration"), None),
            (T("Resources"), "task"),
            (T("Schedule"), "job"),
            (T("Log"), "log")
           ]

    s3db.set_method("sync", "repository",
                           method="register",
                           action=s3mgr.sync)

    def prep(r):
        if r.interactive:
            if r.component and r.id:
                if r.component.alias == "job":
                    current.s3task.configure_tasktable_crud(
                        function="sync_synchronize",
                        args = [r.id],
                        vars = dict(user_id = auth.user.id))
                response.s3.cancel = URL(c="sync", f="repository",
                                         args=[str(r.id), r.component.alias])
        return True
    response.s3.prep = prep

    def postp(r, output):
        if r.interactive and r.id:
            if r.component and r.component.alias == "job":
                response.s3.actions = [
                    dict(label=str(T("Reset")),
                         _class="action-btn",
                         url=URL(c="sync", f="repository",
                                 args=[str(r.id), "job", "[id]", "reset"]))
                    ]
        s3_action_buttons(r)
        return output
    response.s3.postp = postp

    rheader = lambda r: s3db.sync_rheader(r, tabs=tabs)
    output = s3_rest_controller(prefix, resourcename, rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def sync():
    """ Synchronization """

    if "resource" in request.get_vars:
        tablename = request.get_vars["resource"]
        if "_" in tablename:

            # URL variables from peer
            _vars = request.get_vars
            get_vars=Storage(include_deleted=True)
            if "repository" in _vars:
                get_vars.update(repository=_vars["repository"])
            if "msince" in _vars:
                get_vars.update(msince=_vars["msince"])

            # Request
            prefix, name = tablename.split("_", 1)
            r = s3mgr.parse_request(prefix=prefix,
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

    resourcename = "log"

    if "return" in request.get_vars:
        there = request.get_vars["return"]
        c, f = there.split(".", 1)
        list_btn = URL(c=c, f=f,
                       args="sync_log")
    else:
        list_btn = URL(c="sync", f="log",
                       vars=request.get_vars)

    list_btn = A(T("List all Entries"), _href=list_btn, _class="action-btn")

    output = s3_rest_controller(prefix, resourcename,
                                subtitle=None,
                                rheader=s3base.S3SyncLog.rheader,
                                list_btn=list_btn)
    return output

# END =========================================================================
