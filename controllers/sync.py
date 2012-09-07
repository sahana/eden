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

    def prep(r):
        if r.interactive:
            if r.component and r.id:
                if r.component.alias == "job":
                    s3.jquery_ready.append(
'''sync_show_row = function(id) {
    $('#' + id + '__row1').removeClass('hide')
    $('#' + id + '__row').removeClass('hide')
    val = $('#sync_job_repeat_interval').val()
    $('#intvstr').remove()
    if (val == 1) {
        intvstr = '%(minutes)s'
    } else if (val == 2) {
        intvstr = '%(hours)s'
    } else if (val == 3 ) {
        intvstr = '%(days)s'
    } else if (val == 4 ) {
        intvstr = '%(weeks)s'
    } else {
        return
    }
    $('#sync_job_repeat_rate').after('<span id="intvstr">&nbsp;' + intvstr + '</span>')
}
sync_hide_row = function(id) {
    $('#' + id + '__row1').addClass('hide')
    $('#' + id + '__row').addClass('hide')
}
sync_toggle_rows = function() {
    val = $('#sync_job_repeat_interval').val()
    if (val in [1, 2, 3, 4]) {
        // time interval
        sync_show_row('sync_job_repeat_rate')
    } else {
        // once
        sync_hide_row('sync_job_repeat_rate')
    }
}
$('#sync_job_repeat_interval').change(sync_toggle_rows)
sync_toggle_rows()''' % dict (minutes = T("minutes"),
                              hours=T("hours"),
                              days=T("days"),
                              weeks=T("weeks")))
                    s3task.configure_tasktable_crud(
                        function="sync_synchronize",
                        args = [r.id],
                        vars = dict(user_id = auth.user is not None and auth.user.id or 0))
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

            # URL variables from peer
            _vars = request.get_vars
            get_vars=Storage(include_deleted=True)
            if "repository" in _vars:
                get_vars.update(repository=_vars["repository"])
            if "msince" in _vars:
                get_vars.update(msince=_vars["msince"])

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
